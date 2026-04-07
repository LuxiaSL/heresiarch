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
