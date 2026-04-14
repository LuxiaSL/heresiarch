"""Town models: town templates with progressive shop unlocks and lodge rest."""

from __future__ import annotations

from pydantic import BaseModel, Field

from heresiarch.engine.models.zone import ZoneUnlockRequirement


class TownShopTier(BaseModel):
    """Items unlocked when a zone is cleared.

    ``zone_clear=None`` means items are available from the start
    (before clearing any zone).
    """

    zone_clear: str | None = None
    items: list[str] = Field(default_factory=list)


class TownTemplate(BaseModel):
    """Static definition of a region's town."""

    id: str
    name: str
    region: str
    unlock_requires: list[ZoneUnlockRequirement] = Field(default_factory=list)
    shop_tiers: list[TownShopTier] = Field(default_factory=list)
    lodge_gold_per_hp: float = 0.7
    lodge_floor_base: int = 100
    lodge_floor_per_level: int = 5
