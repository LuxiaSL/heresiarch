"""Loot system: resolves drops after combat encounters."""

from __future__ import annotations

import random

from heresiarch.engine.formulas import calculate_money_drop
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.loot import DropTable, GuaranteedDropPool, LootResult

# CHA bonus to drop chances
CHA_COMMON_BONUS_PER_POINT: float = 0.002
CHA_RARE_BONUS_PER_POINT: float = 0.001

# Overstay penalty: flat reduction per battle past zone clear
OVERSTAY_PENALTY_PER_BATTLE: float = 0.05


class LootResolver:
    """Resolves drops after combat. Injected RNG, injected registries."""

    def __init__(
        self,
        item_registry: dict[str, Item],
        drop_tables: dict[str, DropTable],
        rng: random.Random | None = None,
    ):
        self.item_registry = item_registry
        self.drop_tables = drop_tables
        self.rng = rng or random.Random()

    def resolve_encounter_drops(
        self,
        defeated_enemies: list[EnemyInstance],
        party_cha: int = 0,
        overstay_battles: int = 0,
        zone_level: int = 0,  # deprecated fallback — use enemy.level instead
    ) -> LootResult:
        """Roll drops for all defeated enemies in an encounter.

        Money drops now scale with each enemy's individual level rather than
        a flat zone_level. The zone_level parameter is kept for backward
        compatibility but is only used when enemy.level is 0.

        ``overstay_battles`` applies a flat -5% penalty per battle to
        item drop chances, money, and XP (via the returned LootResult).
        """
        total_money = 0
        dropped_items: list[str] = []
        seen_items: set[str] = set()

        overstay_reduction = OVERSTAY_PENALTY_PER_BATTLE * overstay_battles
        overstay_multiplier = max(0.0, 1.0 - overstay_reduction)

        for enemy in defeated_enemies:
            dt = self.drop_tables.get(enemy.template_id)

            # Use per-enemy level for money, fall back to zone_level
            money_level = enemy.level if enemy.level > 0 else zone_level

            # Money: scaled by overstay penalty + per-enemy money_multiplier
            if dt is None or dt.guaranteed_money:
                money = calculate_money_drop(money_level, self.rng)
                money = int(money * (dt.money_multiplier if dt else 1.0))
                # Apply per-enemy gold multiplier override if set
                if enemy.gold_multiplier is not None:
                    money = int(money * enemy.gold_multiplier / enemy.budget_multiplier) if enemy.budget_multiplier > 0 else money
                total_money += int(money * overstay_multiplier)

            if dt is None:
                continue

            # Guaranteed pools — always drop, ignoring overstay
            for pool in dt.guaranteed_pools:
                for item_id in self._pick_from_pool(pool):
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

            # Common drop
            if dt.common_item_ids:
                chance = dt.common_drop_chance + (CHA_COMMON_BONUS_PER_POINT * party_cha)
                chance = max(0.0, chance - overstay_reduction)
                if self.rng.random() < chance:
                    item_id = self.rng.choice(dt.common_item_ids)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

            # Rare drop
            if dt.rare_item_ids:
                chance = dt.rare_drop_chance + (CHA_RARE_BONUS_PER_POINT * party_cha)
                chance = max(0.0, chance - overstay_reduction)
                if self.rng.random() < chance:
                    item_id = self.rng.choice(dt.rare_item_ids)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

            # Equipment drop
            if enemy.equipment and dt.equipment_drop_chance > 0:
                chance = max(0.0, dt.equipment_drop_chance - overstay_reduction)
                if self.rng.random() < chance:
                    item_id = self.rng.choice(enemy.equipment)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

        return LootResult(
            money=total_money,
            item_ids=dropped_items,
            overstay_xp_multiplier=overstay_multiplier,
        )

    def _pick_from_pool(self, pool: GuaranteedDropPool) -> list[str]:
        """Weighted random selection of ``pool.count`` items from a pool."""
        if not pool.items:
            return []
        ids = [entry.item_id for entry in pool.items]
        weights = [entry.weight for entry in pool.items]
        picked: list[str] = []
        for _ in range(pool.count):
            choices = self.rng.choices(ids, weights=weights, k=1)
            if choices:
                picked.append(choices[0])
        return picked
