"""SQLite-backed persistent store for run + encounter records.

Every run (sim or TUI) can be upserted via :meth:`RecordDB.record_run`.
The schema keeps two tables:

  ``runs``       — one row per run_id with summary fields and a full
                   RunState JSON blob for later forensics.
  ``encounters`` — one row per encounter in that run's BattleRecord,
                   with the full EncounterRecord JSON for round-level
                   mining.

Upserts are idempotent on ``run_id``: calling ``record_run`` repeatedly
during a run (e.g., on every autosave) always reflects the latest
state. Encounter rows are replaced wholesale on each upsert so the
latest view is authoritative.

Designed to never block the game path — callers should wrap writes
with their own try/except if mid-game writes must be best-effort.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from heresiarch.engine.models.run_state import RunState


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id                TEXT PRIMARY KEY,
    source                TEXT NOT NULL,
    mc_job_id             TEXT NOT NULL,
    mc_name               TEXT NOT NULL,
    combat_policy         TEXT,
    macro_policy          TEXT,
    seed                  INTEGER,
    started_at            TEXT NOT NULL,
    recorded_at           TEXT NOT NULL,
    outcome               TEXT NOT NULL,
    zones_cleared         TEXT NOT NULL,
    encounters_cleared    INTEGER NOT NULL,
    final_mc_level        INTEGER NOT NULL,
    final_mc_hp           INTEGER NOT NULL,
    final_mc_max_hp       INTEGER NOT NULL,
    final_gold            INTEGER NOT NULL,
    killed_by             TEXT,
    killed_at_zone        TEXT,
    rounds_total          INTEGER NOT NULL,
    run_state_json        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_job      ON runs(mc_job_id);
CREATE INDEX IF NOT EXISTS idx_runs_source   ON runs(source);
CREATE INDEX IF NOT EXISTS idx_runs_outcome  ON runs(outcome);

CREATE TABLE IF NOT EXISTS encounters (
    run_id                TEXT NOT NULL,
    encounter_seq         INTEGER NOT NULL,
    zone_id               TEXT NOT NULL,
    encounter_index       INTEGER NOT NULL,
    enemy_template_ids    TEXT NOT NULL,
    result                TEXT NOT NULL,
    rounds_taken          INTEGER NOT NULL,
    total_damage_dealt    INTEGER NOT NULL,
    total_damage_taken    INTEGER NOT NULL,
    total_healing         INTEGER NOT NULL,
    character_deaths      TEXT NOT NULL,
    encounter_json        TEXT NOT NULL,
    PRIMARY KEY (run_id, encounter_seq),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_enc_zone   ON encounters(zone_id);
CREATE INDEX IF NOT EXISTS idx_enc_result ON encounters(result);

CREATE TABLE IF NOT EXISTS macro_events (
    run_id                  TEXT NOT NULL,
    seq                     INTEGER NOT NULL,
    event_type              TEXT NOT NULL,
    zone_id                 TEXT,
    town_id                 TEXT,
    in_town                 INTEGER NOT NULL DEFAULT 0,
    encounter_seq_at_time   INTEGER NOT NULL DEFAULT 0,
    timestamp               TEXT NOT NULL,
    mc_level                INTEGER NOT NULL DEFAULT 1,
    mc_hp_pct               REAL NOT NULL DEFAULT 1.0,
    party_gold              INTEGER NOT NULL DEFAULT 0,
    stash_used              INTEGER NOT NULL DEFAULT 0,
    stash_free              INTEGER NOT NULL DEFAULT 0,
    payload_json            TEXT NOT NULL,
    PRIMARY KEY (run_id, seq),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_macro_type ON macro_events(event_type);
CREATE INDEX IF NOT EXISTS idx_macro_zone ON macro_events(zone_id);
CREATE INDEX IF NOT EXISTS idx_macro_run  ON macro_events(run_id);
"""


@dataclass
class RunRecordMetadata:
    """Auxiliary fields for a record_run() call.

    ``source`` distinguishes 'sim' (driven by the policy sim CLI) from
    'tui' (a human-driven play). ``started_at`` tracks when the run
    began — on the first ``record_run`` we persist whatever's passed.
    """

    source: str  # 'sim' | 'tui'
    combat_policy: str | None = None
    macro_policy: str | None = None
    seed: int | None = None
    started_at: str | None = None  # ISO 8601; falls back to now on first write


class RecordDB:
    """Persistent store for run + encounter records."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> RecordDB:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record_run(
        self,
        run: RunState,
        metadata: RunRecordMetadata,
        *,
        outcome: str | None = None,
    ) -> None:
        """Upsert a run + its encounters.

        ``outcome`` overrides the inferred status. Inference:
          - ``run.is_dead`` → 'dead'
          - else → 'in_progress'
        """
        now = datetime.now(timezone.utc).isoformat()
        mc = _find_mc(run)
        mc_job = mc.job_id if mc else "unknown"
        mc_name = mc.name if mc else ""
        mc_level = mc.level if mc else 0
        mc_hp = mc.current_hp if mc else 0
        mc_max_hp = mc.max_hp if mc else 0

        derived_outcome = outcome or ("dead" if run.is_dead else "in_progress")
        rounds_total = sum(e.rounds_taken for e in run.battle_record.encounters)
        encounters_cleared = sum(
            1 for e in run.battle_record.encounters if e.result == "victory"
        )

        # Killed_by inference: last encounter whose result was 'defeat'.
        killed_by = ""
        killed_at_zone = ""
        for enc in reversed(run.battle_record.encounters):
            if enc.result == "defeat":
                killed_by = ",".join(enc.enemy_template_ids)
                killed_at_zone = enc.zone_id
                break

        # Keep the original started_at if the row already exists.
        existing_started = self._existing_started_at(run.run_id)
        started_at = (
            existing_started
            or metadata.started_at
            or run.created_at
            or now
        )

        self.conn.execute(
            """
            INSERT INTO runs (
                run_id, source, mc_job_id, mc_name,
                combat_policy, macro_policy, seed,
                started_at, recorded_at, outcome,
                zones_cleared, encounters_cleared,
                final_mc_level, final_mc_hp, final_mc_max_hp, final_gold,
                killed_by, killed_at_zone, rounds_total,
                run_state_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                recorded_at          = excluded.recorded_at,
                outcome              = excluded.outcome,
                zones_cleared        = excluded.zones_cleared,
                encounters_cleared   = excluded.encounters_cleared,
                final_mc_level       = excluded.final_mc_level,
                final_mc_hp          = excluded.final_mc_hp,
                final_mc_max_hp      = excluded.final_mc_max_hp,
                final_gold           = excluded.final_gold,
                killed_by            = excluded.killed_by,
                killed_at_zone       = excluded.killed_at_zone,
                rounds_total         = excluded.rounds_total,
                run_state_json       = excluded.run_state_json
            """,
            (
                run.run_id, metadata.source, mc_job, mc_name,
                metadata.combat_policy, metadata.macro_policy, metadata.seed,
                started_at, now, derived_outcome,
                json.dumps(run.zones_completed), encounters_cleared,
                mc_level, mc_hp, mc_max_hp, run.party.money,
                killed_by, killed_at_zone, rounds_total,
                run.model_dump_json(),
            ),
        )

        # Replace all encounter rows for this run — simpler than diffing
        # and safe since we have the full authoritative record in memory.
        self.conn.execute(
            "DELETE FROM encounters WHERE run_id = ?", (run.run_id,),
        )
        for seq, enc in enumerate(run.battle_record.encounters):
            self.conn.execute(
                """
                INSERT INTO encounters (
                    run_id, encounter_seq, zone_id, encounter_index,
                    enemy_template_ids, result, rounds_taken,
                    total_damage_dealt, total_damage_taken, total_healing,
                    character_deaths, encounter_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id, seq, enc.zone_id, enc.encounter_index,
                    json.dumps(enc.enemy_template_ids),
                    enc.result, enc.rounds_taken,
                    enc.total_damage_dealt, enc.total_damage_taken,
                    enc.total_healing, json.dumps(enc.character_deaths),
                    enc.model_dump_json(),
                ),
            )

        # Replace macro events in the same pattern.
        self.conn.execute(
            "DELETE FROM macro_events WHERE run_id = ?", (run.run_id,),
        )
        for evt in run.macro_log:
            # payload_json stores ONLY the event-specific payload; the flat
            # columns carry the snapshot context (zone, HP, gold, etc.) so
            # queries don't have to parse JSON for quick filters.
            self.conn.execute(
                """
                INSERT INTO macro_events (
                    run_id, seq, event_type, zone_id, town_id, in_town,
                    encounter_seq_at_time, timestamp,
                    mc_level, mc_hp_pct, party_gold,
                    stash_used, stash_free, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id, evt.seq, evt.event_type,
                    evt.zone_id, evt.town_id, 1 if evt.in_town else 0,
                    evt.encounter_seq_at_time, evt.timestamp,
                    evt.mc_level, evt.mc_hp_pct, evt.party_gold,
                    evt.stash_used, evt.stash_free,
                    json.dumps(evt.payload),
                ),
            )
        self.conn.commit()

    def _existing_started_at(self, run_id: str) -> str | None:
        cur = self.conn.execute(
            "SELECT started_at FROM runs WHERE run_id = ?", (run_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Read / query helpers
    # ------------------------------------------------------------------

    def count_runs(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM runs")
        return int(cur.fetchone()[0])

    def runs_by_job(self, mc_job_id: str) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT run_id, source, outcome, zones_cleared, encounters_cleared,
                   final_mc_level, final_gold, killed_by, started_at
            FROM runs WHERE mc_job_id = ? ORDER BY started_at
            """,
            (mc_job_id,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def encounters_by_zone(
        self, zone_id: str, result: str | None = None,
    ) -> list[dict[str, Any]]:
        """All encounters in a zone, optionally filtered by 'victory'/'defeat'."""
        sql = """
            SELECT run_id, encounter_seq, zone_id, encounter_index,
                   enemy_template_ids, result, rounds_taken,
                   total_damage_dealt, total_damage_taken, total_healing
            FROM encounters WHERE zone_id = ?
        """
        params: tuple[Any, ...] = (zone_id,)
        if result is not None:
            sql += " AND result = ?"
            params = (zone_id, result)
        sql += " ORDER BY run_id, encounter_seq"
        cur = self.conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def load_encounter_json(
        self, run_id: str, encounter_seq: int,
    ) -> dict[str, Any] | None:
        cur = self.conn.execute(
            "SELECT encounter_json FROM encounters WHERE run_id = ? AND encounter_seq = ?",
            (run_id, encounter_seq),
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def macro_events_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """All macro events for a run, ordered by seq."""
        cur = self.conn.execute(
            """
            SELECT seq, event_type, zone_id, town_id, in_town,
                   encounter_seq_at_time, timestamp,
                   mc_level, mc_hp_pct, party_gold,
                   stash_used, stash_free, payload_json
            FROM macro_events WHERE run_id = ? ORDER BY seq
            """,
            (run_id,),
        )
        cols = [d[0] for d in cur.description]
        out: list[dict[str, Any]] = []
        for row in cur.fetchall():
            rec = dict(zip(cols, row))
            rec["in_town"] = bool(rec["in_town"])
            rec["payload"] = json.loads(rec.pop("payload_json"))
            out.append(rec)
        return out

    def macro_events_by_type(
        self,
        event_type: str,
        *,
        mc_job_id: str | None = None,
        zone_id: str | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """All macro events of a given type, joined to run meta for filtering."""
        sql = """
            SELECT m.run_id, m.seq, m.event_type, m.zone_id, m.town_id,
                   m.in_town, m.encounter_seq_at_time, m.timestamp,
                   m.mc_level, m.mc_hp_pct, m.party_gold,
                   m.stash_used, m.stash_free, m.payload_json,
                   r.mc_job_id, r.source
            FROM macro_events m
            JOIN runs r ON r.run_id = m.run_id
            WHERE m.event_type = ?
        """
        params: list[Any] = [event_type]
        if mc_job_id is not None:
            sql += " AND r.mc_job_id = ?"
            params.append(mc_job_id)
        if zone_id is not None:
            sql += " AND m.zone_id = ?"
            params.append(zone_id)
        if source is not None:
            sql += " AND r.source = ?"
            params.append(source)
        sql += " ORDER BY m.run_id, m.seq"
        cur = self.conn.execute(sql, tuple(params))
        cols = [d[0] for d in cur.description]
        out: list[dict[str, Any]] = []
        for row in cur.fetchall():
            rec = dict(zip(cols, row))
            rec["in_town"] = bool(rec["in_town"])
            rec["payload"] = json.loads(rec.pop("payload_json"))
            out.append(rec)
        return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_mc(run: RunState):
    for char in run.party.characters.values():
        if char.is_mc:
            return char
    return None
