"""Job and character instance models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .stats import GrowthVector, StatBlock


class AbilityUnlock(BaseModel):
    """An ability unlocked at a specific level for a job."""

    level: int
    ability_id: str


class JobTemplate(BaseModel):
    """Static job definition loaded from YAML."""

    id: str
    name: str
    origin: str
    growth: GrowthVector
    base_hp: int
    hp_growth: int
    innate_ability_id: str
    ability_unlocks: list[AbilityUnlock] = Field(default_factory=list)
    description: str = ""


class CharacterInstance(BaseModel):
    """A living character in a run: a job template instantiated with state."""

    id: str
    name: str
    job_id: str
    level: int = 1
    xp: int = 0
    base_stats: StatBlock = Field(default_factory=StatBlock)
    equipment: dict[str, str | None] = Field(
        default_factory=lambda: {
            "WEAPON": None,
            "ARMOR": None,
            "ACCESSORY_1": None,
            "ACCESSORY_2": None,
        }
    )
    current_hp: int = 0
    max_hp: int = 0
    effective_stats: StatBlock = Field(default_factory=StatBlock)
    abilities: list[str] = Field(default_factory=list)
    is_mc: bool = False
    growth_history: list[tuple[str, int]] = Field(default_factory=list)
    # Source-tracked abilities: each key is a source name, value is list of ability IDs.
    # When populated, abilities should be derived via get_all_abilities().
    ability_sources: dict[str, list[str]] = Field(default_factory=dict)

    def get_all_abilities(self) -> list[str]:
        """Derive flat ability list from sources, preserving order, deduped.

        Falls back to self.abilities if sources are empty (backwards compat).
        """
        if not self.ability_sources:
            return list(self.abilities)
        seen: set[str] = set()
        result: list[str] = []
        # Ordered by source priority: core, innate, breakpoints, equipment, learned
        for source_key in ("core", "innate", "breakpoints", "equipment", "learned"):
            for aid in self.ability_sources.get(source_key, []):
                if aid not in seen:
                    result.append(aid)
                    seen.add(aid)
        # Any other sources not in the canonical order
        for key, aids in self.ability_sources.items():
            if key not in ("core", "innate", "breakpoints", "equipment", "learned"):
                for aid in aids:
                    if aid not in seen:
                        result.append(aid)
                        seen.add(aid)
        return result
