"""TUI play tap: human runs become labeled training shards."""

import gzip
import json
from pathlib import Path

import pytest

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.tui.app import HeresiarchApp


@pytest.fixture
def game_data() -> GameData:
    return load_all(Path("data").resolve())


def _app_with_run(tmp_path: Path, game_data: GameData) -> HeresiarchApp:
    app = HeresiarchApp(game_data=game_data, save_path=tmp_path / "saves")
    run = app.game_loop.new_run("run_test123", "Tester", "einherjar")
    app.run_state = run
    return app


def test_play_tap_lifecycle(
    tmp_path: Path, monkeypatch, game_data: GameData,
):
    """The exact hook sequence the TUI screens perform writes a
    labeled human shard, and run end closes the tap."""
    monkeypatch.chdir(tmp_path)
    app = _app_with_run(tmp_path, game_data)
    run = app.run_state
    app.start_play_tap(run)
    assert app.data_tap is not None

    # One encounter, as the combat screen drives it
    engine = app.game_loop.combat_engine
    enemies = [engine.create_enemy_instance(
        game_data.enemies["fodder_slime"], 3,
    )]
    chars = [run.party.characters[c] for c in run.party.active]
    combat = engine.initialize_combat(
        chars, enemies, party_gold=run.party.money,
    )
    app.data_tap.on_encounter_start(run, combat)
    app.data_tap.on_combat_round(combat)
    for e in combat.enemy_combatants:
        e.current_hp = 0
        e.is_alive = False
    combat.is_finished = True
    combat.player_won = True
    app.data_tap.on_encounter_end(combat, True)
    app.data_tap.flush()

    shard = (
        tmp_path / "artifacts" / "tapdata_play"
        / "tap_einherjar_human_run_test123.jsonl.gz"
    )
    assert shard.exists()
    rows = [json.loads(line) for line in
            gzip.open(shard, "rt", encoding="utf-8")]
    combat_rows = [r for r in rows if r["kind"] == "combat"]
    assert combat_rows
    for r in combat_rows:
        assert r["policy"] == "human"
        assert r["y"]["won"] is True

    app.end_play_tap(won_region=False)
    assert app.data_tap is None
    # Macro row got its run-end labels
    rows = [json.loads(line) for line in
            gzip.open(shard, "rt", encoding="utf-8")]
    macro_rows = [r for r in rows if r["kind"] == "macro"]
    assert macro_rows and macro_rows[0]["y"]["survived"] in (True, False)

    # The analytics DB got a final outcome (not 'in_progress').
    import sqlite3
    con = sqlite3.connect(tmp_path / "artifacts" / "run_records.db")
    outcome = con.execute(
        "select outcome from runs where run_id='run_test123'",
    ).fetchone()[0]
    assert outcome == "clean_exit"


def test_play_tap_env_optout(
    tmp_path: Path, monkeypatch, game_data: GameData,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HERESIARCH_NO_PLAY_TAP", "1")
    app = _app_with_run(tmp_path, game_data)
    app.start_play_tap(app.run_state)
    assert app.data_tap is None
    app.end_play_tap(won_region=False)  # must be a safe no-op
