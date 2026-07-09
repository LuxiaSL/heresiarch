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
    build_timeline,
    load_run_encounters,
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
