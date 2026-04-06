"""Loot models: drop tables and drop results."""

from pydantic import BaseModel, Field


class DropTable(BaseModel):
    """Per-enemy-template drop configuration."""

    enemy_template_id: str
    guaranteed_money: bool = True
    common_item_ids: list[str] = Field(default_factory=list)
    common_drop_chance: float = 0.3
    rare_item_ids: list[str] = Field(default_factory=list)
    rare_drop_chance: float = 0.05
    equipment_drop_chance: float = 0.1


class LootResult(BaseModel):
    """Output of a loot roll for an encounter."""

    money: int = 0
    item_ids: list[str] = Field(default_factory=list)
