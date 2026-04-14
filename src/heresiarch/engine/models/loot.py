"""Loot models: pool-based drop configuration and results."""

from pydantic import BaseModel, Field


class LootPoolEntry(BaseModel):
    """One possible item selection within a pool."""

    item_id: str | None = None  # explicit item
    category: str | None = None  # OR pick random from loot_category
    tier: int | None = None  # optional tier filter (with category)
    weight: int = 1  # selection weight


class LootPoolBranch(BaseModel):
    """A branch within a branching pool — one of these is chosen."""

    weight: int = 1
    count: int = 1
    items: list[LootPoolEntry] = Field(default_factory=list)


class LootPool(BaseModel):
    """One independent loot roll. Terraria-style: each pool rolls separately."""

    chance: float = 1.0  # 1.0 = guaranteed, 0.1 = 10% chance
    count: int = 1  # how many items to pick (if not branching)
    items: list[LootPoolEntry] = Field(default_factory=list)
    branches: list[LootPoolBranch] = Field(default_factory=list)
    unique: bool = True  # if True, no duplicate items across picks


class EnemyLootTable(BaseModel):
    """Complete drop configuration for an enemy template."""

    enemy_template_id: str
    guaranteed_money: bool = True
    money_multiplier: float = 1.0
    pools: list[LootPool] = Field(default_factory=list)


class LootResult(BaseModel):
    """Output of a loot roll for an encounter."""

    money: int = 0
    item_ids: list[str] = Field(default_factory=list)
    overstay_xp_multiplier: float = 1.0
