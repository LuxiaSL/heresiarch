"""Zone models: zone templates, encounter blueprints, zone state."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EncounterTemplate(BaseModel):
    """Blueprint for one encounter within a zone."""

    enemy_templates: list[str]
    enemy_counts: list[int]
    is_boss: bool = False


class ZoneUnlockRequirement(BaseModel):
    """Single requirement to unlock a zone.

    Extensible via ``type`` field:
      - ``zone_clear``: requires ``zone_id`` to be in zones_completed
      - ``item``: requires ``item_id`` in party stash (future)
      - ``level``: requires MC level >= ``level`` (future)
    """

    type: str
    zone_id: str | None = None
    item_id: str | None = None
    level: int | None = None


class RandomSpawn(BaseModel):
    """A random enemy that may be injected into any encounter in a zone."""

    enemy_template_id: str
    chance: float = 0.1


class ZoneTemplate(BaseModel):
    """Static definition of a zone."""

    id: str
    name: str
    zone_level: int
    region: str
    encounters: list[EncounterTemplate]
    shop_item_pool: list[str] = Field(default_factory=list)
    recruitment_chance: float = 0.0
    xp_cap_level: int = 0
    loot_tier: int = 1
    unlock_requires: list[ZoneUnlockRequirement] = Field(default_factory=list)
    is_final: bool = False
    random_spawns: list[RandomSpawn] = Field(default_factory=list)


class ZoneState(BaseModel):
    """Runtime state of a zone being played through."""

    template_id: str
    current_encounter_index: int = 0
    encounters_completed: list[int] = Field(default_factory=list)
    is_cleared: bool = False
    overstay_battles: int = 0
    recruitment_offered: bool = False
