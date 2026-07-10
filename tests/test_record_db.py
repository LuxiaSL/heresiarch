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


# ---------------------------------------------------------------------------
# Incremental live recording (record_run(..., incremental=True))
# ---------------------------------------------------------------------------


def _final_run_state(db: RecordDB, game_data: GameData):
    """Run one sim, return the authoritative final RunState from the DB."""
    from heresiarch.engine.models.run_state import RunState

    simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=FloorPlusMacroPolicy(),
        seed=11,
        max_encounters=25,
        game_data=game_data,
        record_db=db,
    )
    row = db.conn.execute(
        "SELECT run_id, run_state_json FROM runs",
    ).fetchone()
    return RunState.model_validate_json(row[1])


def _partial(run, n_encounters: int, n_macro: int):
    """A mid-run snapshot: the first N encounters / macro events."""
    return run.model_copy(update={
        "battle_record": run.battle_record.model_copy(
            update={"encounters": run.battle_record.encounters[:n_encounters]},
        ),
        "macro_log": run.macro_log[:n_macro],
    })


def _table_rows(db: RecordDB, table: str, order: str) -> list[tuple]:
    return db.conn.execute(
        f"SELECT * FROM {table} ORDER BY {order}",
    ).fetchall()


def test_incremental_steps_match_full_replace(
    tmp_path: Path, game_data: GameData,
):
    """Growing a run via incremental writes == one full-replace write."""
    from heresiarch.analytics.record_db import RunRecordMetadata

    db_full = RecordDB(tmp_path / "full.db")
    run = _final_run_state(db_full, game_data)
    n_enc = len(run.battle_record.encounters)
    n_macro = len(run.macro_log)
    assert n_enc >= 3 and n_macro >= 3, "need a run with some history"

    db_inc = RecordDB(tmp_path / "inc.db")
    meta = RunRecordMetadata(source="sim", combat_policy="floor",
                             macro_policy="floor_plus_macro", seed=11)
    for enc_k, macro_k in [
        (n_enc // 3, n_macro // 3),
        (2 * n_enc // 3, 2 * n_macro // 3),
        (n_enc, n_macro),
    ]:
        db_inc.record_run(_partial(run, enc_k, macro_k), meta,
                          incremental=True)
    # Final authoritative write, exactly like simulate_run does.
    db_inc.record_run(run, meta, outcome="clean_exit")

    assert (
        _table_rows(db_inc, "encounters", "encounter_seq")
        == _table_rows(db_full, "encounters", "encounter_seq")
    )
    assert (
        _table_rows(db_inc, "macro_events", "seq")
        == _table_rows(db_full, "macro_events", "seq")
    )
    db_full.close()
    db_inc.close()


def test_incremental_is_idempotent_and_append_only(
    tmp_path: Path, game_data: GameData,
):
    db = RecordDB(tmp_path / "idem.db")
    run = _final_run_state(db, game_data)
    from heresiarch.analytics.record_db import RunRecordMetadata

    meta = RunRecordMetadata(source="sim", seed=11)
    before_enc = _table_rows(db, "encounters", "encounter_seq")
    before_macro = _table_rows(db, "macro_events", "seq")

    # Re-recording the same state incrementally inserts nothing new.
    db.record_run(run, meta, incremental=True)
    db.record_run(run, meta, incremental=True)
    assert _table_rows(db, "encounters", "encounter_seq") == before_enc
    assert _table_rows(db, "macro_events", "seq") == before_macro
    db.close()


def test_incremental_falls_back_when_db_is_ahead(
    tmp_path: Path, game_data: GameData,
):
    """A shrunk record (reused run_id) triggers a full resync."""
    db = RecordDB(tmp_path / "ahead.db")
    run = _final_run_state(db, game_data)
    from heresiarch.analytics.record_db import RunRecordMetadata

    meta = RunRecordMetadata(source="sim", seed=11)
    smaller = _partial(run, 2, 2)
    db.record_run(smaller, meta, incremental=True)

    enc_rows = _table_rows(db, "encounters", "encounter_seq")
    macro_rows = _table_rows(db, "macro_events", "seq")
    assert len(enc_rows) == 2
    assert len(macro_rows) == 2
    db.close()
