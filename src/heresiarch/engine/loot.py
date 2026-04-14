"""Loot system: pool-based drop resolution after combat encounters."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import calculate_money_drop
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.loot import (
    EnemyLootTable,
    LootPool,
    LootPoolBranch,
    LootPoolEntry,
    LootResult,
)

if TYPE_CHECKING:
    from heresiarch.engine.models.zone import EncounterTemplate

# CHA bonus to non-guaranteed pool chances
CHA_POOL_BONUS_PER_POINT: float = 0.002

# Overstay penalty: flat reduction per battle past zone clear
OVERSTAY_PENALTY_PER_BATTLE: float = 0.05


class LootResolver:
    """Resolves drops after combat. Injected RNG, injected registries."""

    def __init__(
        self,
        item_registry: dict[str, Item],
        drop_tables: dict[str, EnemyLootTable],
        rng: random.Random | None = None,
    ):
        self.item_registry = item_registry
        self.drop_tables = drop_tables
        self.rng = rng or random.Random()
        # Build category index: (category, tier|None) -> [item_id, ...]
        self._category_index: dict[tuple[str, int | None], list[str]] = {}
        self._build_category_index()

    def _build_category_index(self) -> None:
        """Index all items by (loot_category, tier) and (loot_category, None)."""
        by_cat: dict[str, list[str]] = {}
        by_cat_tier: dict[tuple[str, int], list[str]] = {}
        for item_id, item in self.item_registry.items():
            if item.loot_category:
                by_cat.setdefault(item.loot_category, []).append(item_id)
                by_cat_tier.setdefault(
                    (item.loot_category, item.tier), []
                ).append(item_id)
        for cat, ids in by_cat.items():
            self._category_index[(cat, None)] = ids
        for (cat, tier), ids in by_cat_tier.items():
            self._category_index[(cat, tier)] = ids

    def resolve_encounter_drops(
        self,
        defeated_enemies: list[EnemyInstance],
        party_cha: int = 0,
        overstay_battles: int = 0,
        zone_level: int = 0,
        encounter_template: EncounterTemplate | None = None,
    ) -> LootResult:
        """Roll drops for all defeated enemies in an encounter.

        For each enemy:
        1. Check encounter_template.loot_overrides for a matching enemy_template_id
        2. If found: use override's pools
        3. If not found: use the base EnemyLootTable from global drop tables

        CHA adds to non-guaranteed pool chances.
        Overstay subtracts from non-guaranteed pool chances.
        """
        total_money = 0
        dropped_items: list[str] = []
        seen_items: set[str] = set()

        overstay_reduction = OVERSTAY_PENALTY_PER_BATTLE * overstay_battles
        overstay_multiplier = max(0.0, 1.0 - overstay_reduction)
        cha_bonus = CHA_POOL_BONUS_PER_POINT * party_cha

        # Build override lookup from encounter template
        overrides: dict[str, list[LootPool]] = {}
        if encounter_template:
            for ov in encounter_template.loot_overrides:
                overrides[ov.enemy_template_id] = ov.pools

        for enemy in defeated_enemies:
            dt = self.drop_tables.get(enemy.template_id)

            # Use per-enemy level for money, fall back to zone_level
            money_level = enemy.level if enemy.level > 0 else zone_level

            # Money: scaled by overstay penalty + per-enemy money_multiplier
            guaranteed_money = dt.guaranteed_money if dt else True
            money_mult = dt.money_multiplier if dt else 1.0
            if guaranteed_money:
                money = calculate_money_drop(money_level, self.rng)
                money = int(money * money_mult)
                if enemy.gold_multiplier is not None:
                    money = (
                        int(money * enemy.gold_multiplier / enemy.budget_multiplier)
                        if enemy.budget_multiplier > 0
                        else money
                    )
                total_money += int(money * overstay_multiplier)

            # Resolve pools: encounter override > global loot table
            if enemy.template_id in overrides:
                pools = overrides[enemy.template_id]
            elif dt is not None:
                pools = dt.pools
            else:
                pools = []

            for pool in pools:
                self._resolve_pool(
                    pool, cha_bonus, overstay_reduction, dropped_items, seen_items
                )

        return LootResult(
            money=total_money,
            item_ids=dropped_items,
            overstay_xp_multiplier=overstay_multiplier,
        )

    def _resolve_pool(
        self,
        pool: LootPool,
        cha_bonus: float,
        overstay_reduction: float,
        dropped_items: list[str],
        seen_items: set[str],
    ) -> None:
        """Resolve a single loot pool."""
        # Adjust chance: guaranteed pools (1.0) are not modified
        effective_chance = pool.chance
        if pool.chance < 1.0:
            effective_chance = max(0.0, pool.chance + cha_bonus - overstay_reduction)

        if self.rng.random() >= effective_chance:
            return

        # Determine items list and count (branching vs flat)
        if pool.branches:
            branch = self._pick_branch(pool.branches)
            items = branch.items
            count = branch.count
        else:
            items = pool.items
            count = pool.count

        if not items:
            return

        # Pick `count` items from the pool
        for _ in range(count):
            item_id = self._pick_entry(items, seen_items if pool.unique else None)
            if item_id and item_id in self.item_registry:
                if not pool.unique or item_id not in seen_items:
                    dropped_items.append(item_id)
                    seen_items.add(item_id)

    def _pick_branch(self, branches: list[LootPoolBranch]) -> LootPoolBranch:
        """Weighted random pick of one branch."""
        weights = [b.weight for b in branches]
        if sum(weights) <= 0:
            return branches[0]  # fallback to first branch if all weights zero
        return self.rng.choices(branches, weights=weights, k=1)[0]

    def _pick_entry(
        self,
        entries: list[LootPoolEntry],
        seen: set[str] | None,
    ) -> str | None:
        """Weighted random pick from entries, resolving category-based entries."""
        # Expand entries: category entries become all matching items
        expanded_ids: list[str] = []
        expanded_weights: list[int] = []

        for entry in entries:
            if entry.item_id:
                if seen is None or entry.item_id not in seen:
                    expanded_ids.append(entry.item_id)
                    expanded_weights.append(entry.weight)
            elif entry.category:
                candidates = self._category_index.get(
                    (entry.category, entry.tier), []
                )
                if not candidates and entry.tier is not None:
                    # Fall back to all tiers if specific tier has no items
                    candidates = self._category_index.get(
                        (entry.category, None), []
                    )
                for cid in candidates:
                    if seen is None or cid not in seen:
                        expanded_ids.append(cid)
                        expanded_weights.append(entry.weight)

        if not expanded_ids:
            return None

        return self.rng.choices(expanded_ids, weights=expanded_weights, k=1)[0]
