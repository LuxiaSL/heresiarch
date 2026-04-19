"""Smoke tests for the SQLite record DB: upsert, query, round-trip."""

from pathlib import Path

from heresiarch.analytics.record_db import RecordDB
from heresiarch.engine.data_loader import GameData
from heresiarch.policy.builtin.floor import FloorCombatPolicy
from heresiarch.policy.builtin.floor_plus import FloorPlusMacroPolicy
from heresiarch.tools.run_driver import simulate_run


def test_record_db_roundtrip(tmp_path: Path, game_data: GameData):
    db_path = tmp_path / "records.db"
    db = RecordDB(db_path)

    # Seed the DB with a couple of sim runs so we have real BattleRecords.
    floor = FloorCombatPolicy()
    macro = FloorPlusMacroPolicy()

    for seed in range(3):
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=floor,
            macro_policy=macro,
            seed=seed,
            max_encounters=30,
            game_data=game_data,
            record_db=db,
        )

    assert db.count_runs() == 3

    runs = db.runs_by_job("einherjar")
    assert len(runs) == 3
    for row in runs:
        assert row["outcome"] in {"dead", "clean_exit"}
        assert row["encounters_cleared"] >= 0

    # Encounters for zone_01 should exist from the floor policy runs.
    zone1_encs = db.encounters_by_zone("zone_01")
    assert len(zone1_encs) > 0
    # Every row has a zone_id match.
    assert all(e["zone_id"] == "zone_01" for e in zone1_encs)

    # Round-level JSON is recoverable.
    first = zone1_encs[0]
    loaded = db.load_encounter_json(first["run_id"], first["encounter_seq"])
    assert loaded is not None
    assert "rounds" in loaded
    assert isinstance(loaded["rounds"], list)

    db.close()


def test_record_db_upsert_is_idempotent(tmp_path: Path, game_data: GameData):
    """Recording the same run_id twice should update, not duplicate."""
    db = RecordDB(tmp_path / "idempotent.db")
    floor = FloorCombatPolicy()
    macro = FloorPlusMacroPolicy()

    # Two runs with the same job/policy/seed → same derived run_id.
    for _ in range(2):
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=floor,
            macro_policy=macro,
            seed=42,
            max_encounters=30,
            game_data=game_data,
            record_db=db,
        )

    assert db.count_runs() == 1
    db.close()


def test_record_db_encounter_filter_by_result(
    tmp_path: Path, game_data: GameData,
):
    db = RecordDB(tmp_path / "filter.db")
    floor = FloorCombatPolicy()
    macro = FloorPlusMacroPolicy()

    for seed in range(5):
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=floor,
            macro_policy=macro,
            seed=seed,
            max_encounters=30,
            game_data=game_data,
            record_db=db,
        )

    wins = db.encounters_by_zone("zone_01", "victory")
    losses = db.encounters_by_zone("zone_01", "defeat")
    all_zone1 = db.encounters_by_zone("zone_01")

    assert all(e["result"] == "victory" for e in wins)
    assert all(e["result"] == "defeat" for e in losses)
    assert len(all_zone1) == len(wins) + len(losses)

    db.close()
