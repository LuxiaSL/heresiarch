"""Loot models: drop tables and drop results."""

from pydantic import BaseModel, Field


class GuaranteedDropEntry(BaseModel):
    """One item in a guaranteed drop pool, with a relative weight."""

    item_id: str
    weight: float = 1.0


class GuaranteedDropPool(BaseModel):
    """A pool that always drops ``count`` items via weighted random selection."""

    items: list[GuaranteedDropEntry] = Field(default_factory=list)
    count: int = 1


class DropTable(BaseModel):
    """Per-enemy-template drop configuration."""

    enemy_template_id: str
    guaranteed_money: bool = True
    money_multiplier: float = 1.0
    common_item_ids: list[str] = Field(default_factory=list)
    common_drop_chance: float = 0.3
    rare_item_ids: list[str] = Field(default_factory=list)
    rare_drop_chance: float = 0.05
    equipment_drop_chance: float = 0.1
    guaranteed_pools: list[GuaranteedDropPool] = Field(default_factory=list)


class LootResult(BaseModel):
    """Output of a loot roll for an encounter."""

    money: int = 0
    item_ids: list[str] = Field(default_factory=list)
    overstay_xp_multiplier: float = 1.0
