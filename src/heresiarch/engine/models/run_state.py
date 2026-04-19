"""Run state: complete state of a single roguelike run."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .battle_record import BattleRecord
from .macro_log import MacroEvent
from .party import STASH_LIMIT, Party
from .zone import ZoneState


class CombatResult(BaseModel):
    """Summary of a completed combat encounter, for post-combat processing."""

    player_won: bool
    surviving_character_ids: list[str] = Field(default_factory=list)
    surviving_character_hp: dict[str, int] = Field(default_factory=dict)
    defeated_enemy_template_ids: list[str] = Field(default_factory=list)
    defeated_enemy_budget_multipliers: list[float] = Field(default_factory=list)
    defeated_enemy_levels: list[int] = Field(default_factory=list)  # per-enemy level for XP/gold
    defeated_enemy_xp_multipliers: list[float] = Field(default_factory=list)  # per-enemy XP override
    defeated_enemy_gold_multipliers: list[float] = Field(default_factory=list)  # per-enemy gold override
    rounds_taken: int = 0
    zone_level: int = 0  # kept for backward compat (shop pricing, display, etc.)
    gold_stolen_by_enemies: int = 0
    gold_stolen_by_players: int = 0


class RunState(BaseModel):
    """Complete state of a single roguelike run."""

    run_id: str
    party: Party = Field(default_factory=Party)
    current_zone_id: str | None = None
    current_town_id: str | None = None
    zone_state: ZoneState | None = None
    zones_completed: list[str] = Field(default_factory=list)
    zone_progress: dict[str, ZoneState] = Field(default_factory=dict)
    lodge_reset_zones: dict[str, int] = Field(default_factory=dict)
    battle_record: BattleRecord = Field(default_factory=BattleRecord)
    macro_log: list[MacroEvent] = Field(default_factory=list)
    is_dead: bool = False
    created_at: str = ""
    last_recruit_job_id: str | None = None

    def record_macro(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> RunState:
        """Append a macro event with auto-snapshotted context.

        Returns a new RunState with the event appended. Callers should
        assign the result back (``run = run.record_macro(...)``). The
        snapshot captures zone/town/gold/HP at *current* state (post-
        decision if called after the engine mutation has been applied,
        which is the expected usage).
        """
        mc = self._find_mc()
        hp_pct = 1.0
        level = 1
        if mc is not None:
            hp_pct = mc.current_hp / max(1, mc.max_hp)
            level = mc.level
        event = MacroEvent(
            seq=len(self.macro_log),
            event_type=event_type,
            zone_id=self.current_zone_id,
            town_id=self.current_town_id,
            in_town=self.current_town_id is not None,
            encounter_seq_at_time=len(self.battle_record.encounters),
            timestamp=datetime.now(timezone.utc).isoformat(),
            mc_level=level,
            mc_hp_pct=hp_pct,
            party_gold=self.party.money,
            stash_used=len(self.party.stash),
            stash_free=max(0, STASH_LIMIT - len(self.party.stash)),
            payload=payload or {},
        )
        return self.model_copy(update={"macro_log": list(self.macro_log) + [event]})

    def _find_mc(self):
        for char in self.party.characters.values():
            if getattr(char, "is_mc", False):
                return char
        return None
