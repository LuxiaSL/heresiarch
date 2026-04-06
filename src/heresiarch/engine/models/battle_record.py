"""Battle record: per-run combat history for replay, analytics, and future auto-battle."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .combat_state import CombatEvent, PlayerTurnDecision


class RoundRecord(BaseModel):
    """One round of combat from a battle encounter."""

    round_number: int
    player_decisions: dict[str, PlayerTurnDecision] = Field(default_factory=dict)
    events: list[CombatEvent] = Field(default_factory=list)
    player_hp: dict[str, int] = Field(default_factory=dict)
    enemy_hp: dict[str, int] = Field(default_factory=dict)


class EncounterRecord(BaseModel):
    """Full record of one combat encounter."""

    zone_id: str
    encounter_index: int
    enemy_template_ids: list[str] = Field(default_factory=list)
    rounds: list[RoundRecord] = Field(default_factory=list)
    result: Literal["victory", "defeat"] = "defeat"
    rounds_taken: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    total_healing: int = 0
    character_deaths: list[str] = Field(default_factory=list)

    @property
    def was_victory(self) -> bool:
        return self.result == "victory"


class BattleRecord(BaseModel):
    """Per-run combat history. Lives on RunState, dies with permadeath.

    Populated by the TUI during combat — the engine doesn't touch it.
    Serializes with saves, nuked when the run dies.
    """

    encounters: list[EncounterRecord] = Field(default_factory=list)

    @property
    def total_encounters(self) -> int:
        return len(self.encounters)

    @property
    def total_rounds(self) -> int:
        return sum(e.rounds_taken for e in self.encounters)

    @property
    def victories(self) -> int:
        return sum(1 for e in self.encounters if e.was_victory)

    @property
    def defeats(self) -> int:
        return sum(1 for e in self.encounters if not e.was_victory)

    @property
    def total_damage_dealt(self) -> int:
        return sum(e.total_damage_dealt for e in self.encounters)

    @property
    def total_damage_taken(self) -> int:
        return sum(e.total_damage_taken for e in self.encounters)

    @property
    def total_healing(self) -> int:
        return sum(e.total_healing for e in self.encounters)

    @property
    def farthest_zone(self) -> str | None:
        """The last zone fought in."""
        if not self.encounters:
            return None
        return self.encounters[-1].zone_id

    def damage_dealt_by_character(self) -> dict[str, int]:
        """Aggregate damage dealt across all encounters, keyed by combatant ID."""
        totals: dict[str, int] = {}
        for encounter in self.encounters:
            for rnd in encounter.rounds:
                for event in rnd.events:
                    if event.event_type == "DAMAGE_DEALT" and event.actor_id:
                        totals[event.actor_id] = totals.get(event.actor_id, 0) + event.value
        return totals

    def most_used_abilities(self) -> dict[str, int]:
        """Count ability uses across all encounters."""
        counts: dict[str, int] = {}
        for encounter in self.encounters:
            for rnd in encounter.rounds:
                for event in rnd.events:
                    if event.event_type in ("ACTION_DECLARED", "BONUS_ACTION") and event.ability_id:
                        counts[event.ability_id] = counts.get(event.ability_id, 0) + 1
        return counts
