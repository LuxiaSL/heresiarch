"""Loot system: resolves drops after combat encounters."""

from __future__ import annotations

import random

from heresiarch.engine.formulas import calculate_money_drop
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.loot import DropTable, LootResult

# CHA bonus to drop chances
CHA_COMMON_BONUS_PER_POINT: float = 0.002
CHA_RARE_BONUS_PER_POINT: float = 0.001


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
        zone_level: int,
        party_cha: int = 0,
    ) -> LootResult:
        """Roll drops for all defeated enemies in an encounter."""
        total_money = 0
        dropped_items: list[str] = []
        seen_items: set[str] = set()

        for enemy in defeated_enemies:
            dt = self.drop_tables.get(enemy.template_id)

            # Money: always roll if guaranteed (or no drop table)
            if dt is None or dt.guaranteed_money:
                total_money += calculate_money_drop(zone_level, self.rng)

            if dt is None:
                continue

            # Common drop
            if dt.common_item_ids:
                chance = dt.common_drop_chance + (CHA_COMMON_BONUS_PER_POINT * party_cha)
                if self.rng.random() < chance:
                    item_id = self.rng.choice(dt.common_item_ids)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

            # Rare drop
            if dt.rare_item_ids:
                chance = dt.rare_drop_chance + (CHA_RARE_BONUS_PER_POINT * party_cha)
                if self.rng.random() < chance:
                    item_id = self.rng.choice(dt.rare_item_ids)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

            # Equipment drop
            if enemy.equipment and dt.equipment_drop_chance > 0:
                if self.rng.random() < dt.equipment_drop_chance:
                    item_id = self.rng.choice(enemy.equipment)
                    if item_id not in seen_items and item_id in self.item_registry:
                        dropped_items.append(item_id)
                        seen_items.add(item_id)

        return LootResult(money=total_money, item_ids=dropped_items)
