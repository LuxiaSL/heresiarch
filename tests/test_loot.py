"""Tests for loot/drop system."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.loot import CHA_COMMON_BONUS_PER_POINT, LootResolver
from heresiarch.engine.models.enemies import ActionTable, ActionWeight, EnemyInstance
from heresiarch.engine.models.loot import DropTable, LootResult
from heresiarch.engine.models.stats import StatBlock

_DUMMY_ACTION_TABLE = ActionTable(
    base_weights=[ActionWeight(ability_id="basic_attack", weight=1.0)]
)


def _make_enemy(template_id: str, equipment: list[str] | None = None) -> EnemyInstance:
    """Minimal EnemyInstance for loot testing."""
    return EnemyInstance(
        template_id=template_id,
        name=template_id,
        level=10,
        stats=StatBlock(STR=10, MAG=5, DEF=10, RES=5, SPD=10),
        max_hp=50,
        current_hp=0,
        abilities=["basic_attack"],
        equipment=equipment or [],
        action_table=_DUMMY_ACTION_TABLE,
    )


class TestMoneyDrops:
    def test_money_in_range(self) -> None:
        """Zone 10 money: 10 * randint(5,15) = [50, 150]."""
        rng = random.Random(42)
        resolver = LootResolver(item_registry={}, drop_tables={}, rng=rng)
        enemy = _make_enemy("unknown_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=10)
        assert 50 <= result.money <= 150

    def test_money_scales_with_zone(self) -> None:
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        r_low = LootResolver(item_registry={}, drop_tables={}, rng=rng1)
        r_high = LootResolver(item_registry={}, drop_tables={}, rng=rng2)
        e = _make_enemy("x")
        low = r_low.resolve_encounter_drops([e], zone_level=1)
        high = r_high.resolve_encounter_drops([e], zone_level=20)
        # Same seed, so same multiplier, different zone -> different money
        assert high.money == 20 * (low.money // 1)  # proportional


class TestFodderSlime:
    def test_money_only(self, game_data: GameData) -> None:
        """Fodder slime has no common/rare items — only money."""
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("fodder_slime")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert result.money > 0
        assert result.item_ids == []


class TestCommonDrop:
    def test_brute_can_drop_common(self, game_data: GameData) -> None:
        """Brute oni has 20% common drop chance — run many times to verify."""
        dropped_any = False
        for seed in range(100):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("brute_oni")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if result.item_ids:
                dropped_any = True
                # Common items for brute: iron_blade, endurance_plate
                for item_id in result.item_ids:
                    assert item_id in game_data.items
                break
        assert dropped_any, "Expected at least one drop in 100 seeds"


class TestRareDrop:
    def test_rare_drop_possible(self, game_data: GameData) -> None:
        """Brute oni has 5% rare drop (leech_fang etc.) — scan seeds."""
        rare_items = {"endurance_plate", "leech_fang", "void_fang"}
        dropped_rare = False
        for seed in range(500):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("brute_oni")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if rare_items & set(result.item_ids):
                dropped_rare = True
                break
        assert dropped_rare, "Expected rare drop from brute_oni in 500 seeds"


class TestEquipmentDrop:
    def test_enemy_equipment_drops(self, game_data: GameData) -> None:
        """Enemy with equipment can drop its gear."""
        dropped_equip = False
        for seed in range(200):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            # Give the enemy some equipment
            enemy = _make_enemy("brute_oni", equipment=["iron_blade"])
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if "iron_blade" in result.item_ids:
                dropped_equip = True
                break
        assert dropped_equip, "Expected equipment drop in 200 seeds"


class TestCHAModifier:
    def test_high_cha_increases_drops(self, game_data: GameData) -> None:
        """Higher CHA should result in more drops over many trials."""
        drops_low_cha = 0
        drops_high_cha = 0

        for seed in range(200):
            rng_low = random.Random(seed)
            rng_high = random.Random(seed)
            r_low = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng_low,
            )
            r_high = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng_high,
            )
            enemy_low = _make_enemy("brute_oni")
            enemy_high = _make_enemy("brute_oni")
            result_low = r_low.resolve_encounter_drops([enemy_low], zone_level=10, party_cha=0)
            result_high = r_high.resolve_encounter_drops([enemy_high], zone_level=10, party_cha=100)
            drops_low_cha += len(result_low.item_ids)
            drops_high_cha += len(result_high.item_ids)

        assert drops_high_cha >= drops_low_cha


class TestMultipleEnemies:
    def test_aggregate_money_and_items(self, game_data: GameData) -> None:
        """Multiple enemies aggregate money."""
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemies = [_make_enemy("fodder_slime") for _ in range(3)]
        result = resolver.resolve_encounter_drops(enemies, zone_level=10)
        # 3 enemies * money each
        assert result.money >= 150  # at minimum 3 * 10 * 5


class TestNoDropTable:
    def test_unknown_enemy_still_gets_money(self) -> None:
        rng = random.Random(42)
        resolver = LootResolver(item_registry={}, drop_tables={}, rng=rng)
        enemy = _make_enemy("totally_unknown")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert result.money > 0
        assert result.item_ids == []
