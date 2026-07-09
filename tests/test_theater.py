"""Theater mode: timeline building, playback state, and rendering."""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from heresiarch.analytics.record_db import RecordDB
from heresiarch.engine.data_loader import GameData
from heresiarch.policy.builtin.floor import FloorCombatPolicy
from heresiarch.policy.builtin.floor_plus import FloorPlusMacroPolicy
from heresiarch.tools.run_driver import simulate_run
from heresiarch.tools.theater import (
    PanelPlayer,
    _enemy_display_names,
    _macro_line,
    _row_sig,
    build_timeline,
    load_run_encounters,
    refresh_follow,
    render_panel,
    render_wall,
    select_runs,
)


def _seed_db(tmp_path: Path, game_data: GameData, seeds: tuple[int, ...]) -> RecordDB:
    db = RecordDB(tmp_path / "theater.db")
    for seed in seeds:
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=FloorCombatPolicy(),
            macro_policy=FloorPlusMacroPolicy(),
            seed=seed,
            max_encounters=30,
            game_data=game_data,
            record_db=db,
        )
    return db


def _select_all(db: RecordDB, limit: int = 10) -> list[dict]:
    args = argparse.Namespace(run_ids=None, job=None, source=None, limit=limit)
    return select_runs(db, args)


def _play_to_end(pp: PanelPlayer) -> None:
    ticks = 0
    while not pp.done and ticks < 100_000:
        pp.advance(60_000)
        ticks += 1
    assert pp.done, "playback did not terminate"


def test_timeline_plays_to_final_state(tmp_path: Path, game_data: GameData):
    db = _seed_db(tmp_path, game_data, seeds=(1, 2))
    rows = _select_all(db)
    assert len(rows) == 2

    for row in rows:
        encounters = load_run_encounters(db, row["run_id"])
        macro = db.macro_events_for_run(row["run_id"])
        steps = build_timeline(row, encounters, macro, game_data)
        assert steps, "timeline should not be empty"
        # Every step's delay is non-negative and the run terminates.
        assert all(s.delay_ms >= 0 for s in steps)

        pp = PanelPlayer(title=row["run_id"], steps=steps)
        _play_to_end(pp)

        # Floor policy dies early — the tombstone must land.
        assert row["outcome"] == "dead"
        assert pp.final == "dead"
        assert "☠" in pp.status
        assert pp.players, "party should be populated after playback"
    db.close()


def test_final_hp_matches_last_snapshot(tmp_path: Path, game_data: GameData):
    """After full playback, tracked HP equals the last round snapshot."""
    db = _seed_db(tmp_path, game_data, seeds=(3,))
    row = _select_all(db)[0]
    encounters = load_run_encounters(db, row["run_id"])
    macro = db.macro_events_for_run(row["run_id"])
    pp = PanelPlayer(
        title="t", steps=build_timeline(row, encounters, macro, game_data),
    )
    _play_to_end(pp)

    last_round = encounters[-1].rounds[-1]
    for pid, snap_hp in last_round.player_hp.items():
        assert pid in pp.players
        _, hp, max_hp = pp.players[pid]
        assert hp == snap_hp
        assert max_hp >= hp
    db.close()


def test_enemy_display_names_letter_suffixes(game_data: GameData):
    solo = _enemy_display_names(["fodder_slime_0"], game_data)
    assert "A" not in solo["fodder_slime_0"].split()[-1] or len(solo) == 1

    trio = _enemy_display_names(
        ["fodder_slime_0", "fodder_slime_1", "alpha_slime_2"], game_data,
    )
    assert len(set(trio.values())) == 3, "names must be distinct"
    assert trio["fodder_slime_0"].endswith(" A")
    assert trio["fodder_slime_1"].endswith(" B")
    assert trio["alpha_slime_2"].endswith(" C")


def test_macro_line_defensive_on_garbage(game_data: GameData):
    """Malformed macro payloads degrade to a line or None, never raise."""
    cases = [
        {"event_type": "shop_buy", "payload": {}},
        {"event_type": "pick_loot", "payload": {"selected": [123, {"x": 1}]}},
        {"event_type": "use_consumable", "payload": {"item_id": None}},
        {"event_type": "totally_unknown_event", "payload": None},
        {"event_type": "enter_zone"},
    ]
    for evt in cases:
        line = _macro_line(evt, game_data)
        assert line is None or isinstance(line, str)


def test_select_runs_filters(tmp_path: Path, game_data: GameData):
    db = _seed_db(tmp_path, game_data, seeds=(4, 5))
    args = argparse.Namespace(
        run_ids=None, job="einherjar", source="sim", limit=10,
    )
    assert len(select_runs(db, args)) == 2
    args_none = argparse.Namespace(
        run_ids=None, job="onmyoji", source=None, limit=10,
    )
    assert select_runs(db, args_none) == []
    one_id = select_runs(db, args)[0]["run_id"]
    args_ids = argparse.Namespace(
        run_ids=[one_id], job=None, source=None, limit=10,
    )
    assert [r["run_id"] for r in select_runs(db, args_ids)] == [one_id]
    db.close()


def test_live_timeline_is_strict_prefix(tmp_path: Path, game_data: GameData):
    """Follow mode's cursor-safety contract: a live timeline built from
    k encounters is a strict prefix of the timeline built from k+m
    encounters (and of the final non-live build)."""
    db = _seed_db(tmp_path, game_data, seeds=(7,))
    row = _select_all(db)[0]
    encounters = load_run_encounters(db, row["run_id"])
    macro = db.macro_events_for_run(row["run_id"])
    assert len(encounters) >= 2, "need a multi-encounter run for this test"

    full = build_timeline(row, encounters, macro, game_data, live=False)
    prev_len = -1
    for k in range(1, len(encounters) + 1):
        partial = build_timeline(
            row, encounters[:k], macro, game_data, live=True,
        )
        assert len(partial) > prev_len
        prev_len = len(partial)
        assert full[: len(partial)] == partial, f"prefix broken at k={k}"

    # The live build of ALL encounters is also a prefix of the final
    # build (which appends trailing macros + the outcome banner).
    live_all = build_timeline(row, encounters, macro, game_data, live=True)
    assert len(full) > len(live_all)
    assert full[: len(live_all)] == live_all
    db.close()


class _CountingDB(RecordDB):
    """RecordDB that counts record_run calls (mid-run + final)."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.write_count = 0

    def record_run(self, *args, **kwargs):  # type: ignore[override]
        self.write_count += 1
        return super().record_run(*args, **kwargs)


def test_record_every_upserts_mid_run(tmp_path: Path, game_data: GameData):
    """record_every triggers incremental upserts, final write still wins."""
    db = _CountingDB(tmp_path / "live.db")
    result = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=FloorPlusMacroPolicy(),
        seed=8,
        max_encounters=30,
        game_data=game_data,
        record_db=db,
        record_every=1,
    )
    # One write per encounter + the final authoritative write.
    assert db.write_count >= 2
    assert db.count_runs() == 1
    row = _select_all(db)[0]
    assert row["outcome"] == ("dead" if result.is_dead else "clean_exit")
    db.close()


def test_refresh_follow_attaches_and_extends(
    tmp_path: Path, game_data: GameData,
):
    """Follow polling: attaches new runs, extends on signature change,
    and preserves the playback cursor across a rebuild."""
    db = _seed_db(tmp_path, game_data, seeds=(9,))
    args = argparse.Namespace(
        run_ids=None, job=None, source=None, limit=4, stale_after=1e9,
    )
    panels = refresh_follow(db, args, game_data, [])
    assert len(panels) == 1
    pp = panels[0]
    assert pp.run_id and pp.sig == _row_sig(_select_all(db)[0])

    # Play a bit, then force a "the run grew" rebuild by clearing sig.
    pp.advance(30_000)
    cursor_before = pp.cursor
    assert cursor_before > 0
    pp.sig = ()
    panels = refresh_follow(db, args, game_data, panels)
    assert panels[0] is pp
    assert pp.cursor == cursor_before, "rebuild must not move the cursor"

    # A second recorded run gets attached on the next poll.
    simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=FloorPlusMacroPolicy(),
        seed=10,
        max_encounters=30,
        game_data=game_data,
        record_db=db,
    )
    panels = refresh_follow(db, args, game_data, panels)
    assert len(panels) == 2
    assert {p.run_id for p in panels} == {
        r["run_id"] for r in _select_all(db)
    }
    db.close()


def test_render_wall_smoke(tmp_path: Path, game_data: GameData):
    """A mid-playback frame renders without touching a real terminal."""
    db = _seed_db(tmp_path, game_data, seeds=(6,))
    row = _select_all(db)[0]
    encounters = load_run_encounters(db, row["run_id"])
    macro = db.macro_events_for_run(row["run_id"])
    pp = PanelPlayer(
        title="smoke", steps=build_timeline(row, encounters, macro, game_data),
    )
    pp.advance(45_000)  # mid-flight, mid-combat

    panel = render_panel(pp, width=60)
    assert isinstance(panel, Panel)

    console = Console(record=True, width=130)
    console.print(render_wall([pp, pp], console, cols=2, speed=1.0, paused=False))
    out = console.export_text()
    assert "THEATER" in out
    assert "smoke" in out
    db.close()
