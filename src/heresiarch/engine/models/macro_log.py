"""Macro event log: non-combat decisions recorded during a run.

Combat decisions live in :class:`BattleRecord`. Everything else — shop
purchases, equipment swaps, loot picks, recruitment accept/reject,
lodge rests, zone/town transitions, consumable use — lands here.

Each event carries the decision plus enough context to reconstruct
"what was on the menu at the time." That context is what lets the
golden-macro design workflow distill preference rules from actual
play: we need to know what was skipped, not just what was chosen.

Populated by the TUI (and sim driver / agent session, when wired) at
the decision site. The engine never writes to this log on its own —
callers know the full decision context (alternatives, offers) that the
engine methods don't.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MacroEvent(BaseModel):
    """A single non-combat decision recorded during a run.

    ``payload`` is event-type-specific; the top-level fields are the
    quick-view snapshot so DB queries can filter/sort without parsing
    JSON for every row.
    """

    seq: int
    event_type: str
    zone_id: str | None = None
    town_id: str | None = None
    in_town: bool = False
    encounter_seq_at_time: int = 0
    timestamp: str = ""
    mc_level: int = 1
    mc_hp_pct: float = 1.0
    party_gold: int = 0
    stash_used: int = 0
    stash_free: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
