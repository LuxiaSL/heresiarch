"""Progress heartbeat for long-running sims.

Workers append one JSON line per event to a shared file (atomic small
appends); a viewer (``heresiarch.tools.watch``) tails it. Enabled via
the ``HERESIARCH_PROGRESS_FILE`` env var so it crosses multiprocessing
worker boundaries without threading a parameter through every call.

Event kinds:
    run_start   {seed, job}
    encounter   {seed, zone, enc, level, hp_pct, gold}
    run_end     {seed, zones, enc, dead, reason}
    generation  {gen, best, pop_mean, best_ever}   (policy_opt)
    phase       {label}                            (policy_opt)

The emitter is deliberately failure-proof: a broken path or full disk
must never take down a simulation.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

ENV_VAR = "HERESIARCH_PROGRESS_FILE"


class ProgressEmitter:
    """Appends JSON-line events to the progress file, or no-ops."""

    def __init__(self, path: str | Path | None):
        self.path: Path | None = Path(path) if path else None

    @classmethod
    def from_env(cls) -> ProgressEmitter:
        return cls(os.environ.get(ENV_VAR, ""))

    @property
    def enabled(self) -> bool:
        return self.path is not None

    def emit(self, kind: str, **fields: object) -> None:
        if self.path is None:
            return
        record = {"ts": round(time.time(), 2), "kind": kind, "pid": os.getpid()}
        record.update(fields)
        try:
            with self.path.open("a") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError:
            # Never let telemetry break a sim.
            pass


def read_events(path: Path, offset: int = 0) -> tuple[list[dict], int]:
    """Read events from ``offset`` bytes onward. Returns (events, new_offset).

    Tolerates torn trailing lines (a writer mid-append): the incomplete
    tail is left for the next read.
    """
    events: list[dict] = []
    try:
        with path.open("rb") as fh:
            fh.seek(offset)
            data = fh.read()
    except OSError:
        return events, offset

    if not data:
        return events, offset

    complete, sep, _tail = data.rpartition(b"\n")
    if not sep:
        return events, offset
    for line in complete.split(b"\n"):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return events, offset + len(complete) + 1
