"""Zone models: zone templates, encounter blueprints, zone state."""

from pydantic import BaseModel, Field


class EncounterTemplate(BaseModel):
    """Blueprint for one encounter within a zone."""

    enemy_templates: list[str]
    enemy_counts: list[int]
    is_boss: bool = False


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


class ZoneState(BaseModel):
    """Runtime state of a zone being played through."""

    template_id: str
    current_encounter_index: int = 0
    encounters_completed: list[int] = Field(default_factory=list)
    is_cleared: bool = False
