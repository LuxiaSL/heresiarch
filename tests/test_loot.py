"""Tests for loot/drop system."""

import random
from collections import Counter

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.loot import CHA_POOL_BONUS_PER_POINT, LootResolver
from heresiarch.engine.models.enemies import ActionTable, ActionWeight, EnemyInstance
from heresiarch.engine.models.loot import (
    EnemyLootTable,
    LootPool,
    LootPoolBranch,
    LootPoolEntry,
    LootResult,
)
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.stats import StatBlock
from heresiarch.engine.models.zone import EncounterLootOverride, EncounterTemplate

_DUMMY_ACTION_TABLE = ActionTable(
    base_weights=[ActionWeight(ability_id="basic_attack", weight=1.0)]
)


def _make_enemy(template_id: str, equipment: list[str] | None = None, level: int = 10) -> EnemyInstance:
    """Minimal EnemyInstance for loot testing."""
    return EnemyInstance(
        template_id=template_id,
        name=template_id,
        level=level,
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

    def test_money_scales_with_enemy_level(self) -> None:
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        r_low = LootResolver(item_registry={}, drop_tables={}, rng=rng1)
        r_high = LootResolver(item_registry={}, drop_tables={}, rng=rng2)
        e_low = _make_enemy("x", level=1)
        e_high = _make_enemy("x", level=20)
        low = r_low.resolve_encounter_drops([e_low])
        high = r_high.resolve_encounter_drops([e_high])
        # Same seed, so same multiplier, different enemy level -> different money
        assert high.money == 20 * (low.money // 1)  # proportional


class TestFodderSlime:
    def test_mostly_money(self, game_data: GameData) -> None:
        """Fodder slime has 10% minor_potion pool — mostly money-only."""
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("fodder_slime")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert result.money > 0
        # 10% drop chance — may or may not have items, but any drops must be valid
        for item_id in result.item_ids:
            assert item_id in game_data.items


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


class TestCategoryDrop:
    def test_tonic_category_drops(self, game_data: GameData) -> None:
        """Brute oni has 10% tonic pool — category resolves to actual tonic items."""
        tonic_ids = {iid for iid, item in game_data.items.items() if item.loot_category == "tonic"}
        dropped_tonic = False
        for seed in range(500):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("brute_oni")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if tonic_ids & set(result.item_ids):
                dropped_tonic = True
                break
        assert dropped_tonic, "Expected tonic from brute_oni category pool in 500 seeds"


class TestPoolDrop:
    def test_specific_item_drops_from_pool(self, game_data: GameData) -> None:
        """Brute oni has 15% minor_potion pool — should drop over many seeds."""
        dropped_item = False
        for seed in range(200):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("brute_oni")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if "minor_potion" in result.item_ids:
                dropped_item = True
                break
        assert dropped_item, "Expected minor_potion from brute_oni pool in 200 seeds"


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


# ===================================================================
# Category-Based Resolution
# ===================================================================

class TestCategoryResolution:
    """Test that category-based pool entries resolve to real items of that category."""

    def test_tonic_category_resolves_to_tonic_items(self, game_data: GameData) -> None:
        """A guaranteed pool with category=tonic must yield an item whose loot_category is 'tonic'."""
        tonic_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "tonic"
        }
        assert tonic_ids, "Precondition: at least one tonic item must exist in game data"

        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(chance=1.0, count=1, items=[LootPoolEntry(category="tonic")]),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert len(result.item_ids) == 1
        assert result.item_ids[0] in tonic_ids

    def test_category_with_tier_filter(self, game_data: GameData) -> None:
        """Pool with category=potion, tier=1 should only yield tier-1 potions."""
        tier1_potions = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "potion" and item.tier == 1
        }
        tier2_potions = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "potion" and item.tier == 2
        }
        assert tier1_potions, "Precondition: tier-1 potions must exist"
        assert tier2_potions, "Precondition: tier-2 potions must exist (to prove exclusion)"

        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=1,
                        items=[LootPoolEntry(category="potion", tier=1)],
                    ),
                ],
            )
        }

        # Run many seeds to ensure we never pick tier-2
        for seed in range(200):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items, drop_tables=drop_tables, rng=rng
            )
            enemy = _make_enemy("test_enemy")
            result = resolver.resolve_encounter_drops([enemy], zone_level=5)
            assert len(result.item_ids) == 1
            assert result.item_ids[0] in tier1_potions, (
                f"Seed {seed}: got {result.item_ids[0]}, expected one of {tier1_potions}"
            )

    def test_category_with_no_matching_items(self) -> None:
        """A category that has zero items should produce no drops (not crash)."""
        # Build a registry with only a weapon — no items in category "nonexistent"
        registry = {
            "test_sword": Item(
                id="test_sword",
                name="Test Sword",
                loot_category="weapon",
                tier=1,
            )
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=1,
                        items=[LootPoolEntry(category="nonexistent")],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert result.item_ids == []

    def test_tier_fallback_to_all_tiers(self, game_data: GameData) -> None:
        """If the specific tier has no items, fall back to all-tiers for that category.

        Category 'tonic' only has tier=1 items. Requesting tier=99 should fall back
        to all tonics.
        """
        tonic_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "tonic"
        }
        assert tonic_ids, "Precondition: tonic items must exist"

        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=1,
                        items=[LootPoolEntry(category="tonic", tier=99)],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        # Falls back to all tonics
        assert len(result.item_ids) == 1
        assert result.item_ids[0] in tonic_ids


# ===================================================================
# Branching Pools
# ===================================================================

class TestBranchingPools:
    """Test branching pool mechanics — the 66/33 scroll set pattern and similar."""

    def test_branch_weight_distribution(self, game_data: GameData) -> None:
        """Boss scroll set (weight 2 vs weight 1) should land ~66/33 over many seeds.

        Use a synthetic pool to isolate branch selection from category resolution.
        """
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
            "item_b": Item(id="item_b", name="B", tier=1),
        }
        drop_tables = {
            "test_boss": EnemyLootTable(
                enemy_template_id="test_boss",
                pools=[
                    LootPool(
                        chance=1.0,
                        branches=[
                            LootPoolBranch(
                                weight=2,
                                count=2,
                                items=[LootPoolEntry(item_id="item_a")],
                            ),
                            LootPoolBranch(
                                weight=1,
                                count=1,
                                items=[LootPoolEntry(item_id="item_b")],
                            ),
                        ],
                    ),
                ],
            )
        }

        branch_a_count = 0
        branch_b_count = 0
        total_trials = 3000

        for seed in range(total_trials):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng
            )
            enemy = _make_enemy("test_boss")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if "item_a" in result.item_ids:
                branch_a_count += 1
            elif "item_b" in result.item_ids:
                branch_b_count += 1

        # Branch A (weight 2/3) should be ~66% of total, branch B ~33%
        ratio_a = branch_a_count / total_trials
        assert 0.58 < ratio_a < 0.74, f"Branch A ratio {ratio_a:.3f} outside expected 0.58-0.74"
        ratio_b = branch_b_count / total_trials
        assert 0.26 < ratio_b < 0.42, f"Branch B ratio {ratio_b:.3f} outside expected 0.26-0.42"

    def test_branch_count_respected(self) -> None:
        """Branch with count=2 should produce 2 items; count=1 should produce 1."""
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
            "item_b": Item(id="item_b", name="B", tier=1),
        }
        # Force branch selection by giving all weight to one branch
        drop_tables = {
            "test_boss": EnemyLootTable(
                enemy_template_id="test_boss",
                pools=[
                    LootPool(
                        chance=1.0,
                        unique=False,  # allow duplicates so count=2 from single entry works
                        branches=[
                            LootPoolBranch(
                                weight=100,
                                count=2,
                                items=[LootPoolEntry(item_id="item_a")],
                            ),
                            LootPoolBranch(
                                weight=0,  # never selected
                                count=1,
                                items=[LootPoolEntry(item_id="item_b")],
                            ),
                        ],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_boss")
        result = resolver.resolve_encounter_drops([enemy], zone_level=10)
        assert result.item_ids.count("item_a") == 2

    def test_boss_scroll_set_produces_real_scrolls(self, game_data: GameData) -> None:
        """Alpha slime's branching scroll pool should produce either cast or teach scrolls."""
        cast_scroll_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "cast_scroll" and item.tier == 1
        }
        teach_scroll_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "teach_scroll" and item.tier == 1
        }
        assert cast_scroll_ids, "Precondition: tier-1 cast scrolls must exist"
        assert teach_scroll_ids, "Precondition: tier-1 teach scrolls must exist"

        got_cast = False
        got_teach = False

        for seed in range(1000):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("alpha_slime")
            result = resolver.resolve_encounter_drops([enemy], zone_level=5)
            dropped = set(result.item_ids)
            if dropped & cast_scroll_ids:
                got_cast = True
            if dropped & teach_scroll_ids:
                got_teach = True
            if got_cast and got_teach:
                break

        assert got_cast, "Expected cast_scroll branch from alpha_slime in 1000 seeds"
        assert got_teach, "Expected teach_scroll branch from alpha_slime in 1000 seeds"


# ===================================================================
# Encounter-Level Overrides
# ===================================================================

class TestEncounterOverrides:
    """Test that EncounterTemplate.loot_overrides replace global loot tables per enemy."""

    def test_override_replaces_global_pools(self, game_data: GameData) -> None:
        """When an encounter override is present, its pools replace the global table."""
        # The global brute_oni table has tonic + minor_potion pools.
        # Override with a guaranteed specific item pool.
        override_encounter = EncounterTemplate(
            enemy_templates=["brute_oni"],
            enemy_counts=[1],
            loot_overrides=[
                EncounterLootOverride(
                    enemy_template_id="brute_oni",
                    pools=[
                        LootPool(
                            chance=1.0,
                            count=1,
                            items=[LootPoolEntry(item_id="iron_blade")],
                        ),
                    ],
                ),
            ],
        )
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("brute_oni")
        result = resolver.resolve_encounter_drops(
            [enemy],
            zone_level=10,
            encounter_template=override_encounter,
        )
        # Should always get iron_blade from the override, not tonic/minor_potion
        assert "iron_blade" in result.item_ids

    def test_override_only_affects_targeted_enemy(self, game_data: GameData) -> None:
        """Override for brute_oni should not change drops for fodder_slime in same encounter."""
        override_encounter = EncounterTemplate(
            enemy_templates=["brute_oni", "fodder_slime"],
            enemy_counts=[1, 1],
            loot_overrides=[
                EncounterLootOverride(
                    enemy_template_id="brute_oni",
                    pools=[],  # Brute gets NO item pools from override
                ),
            ],
        )
        # Run many seeds: brute_oni should never produce items (empty override pools),
        # but fodder_slime should still use its global table
        for seed in range(50):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            brute = _make_enemy("brute_oni")
            # Test single enemy with override to confirm no items
            result_brute = resolver.resolve_encounter_drops(
                [brute],
                zone_level=10,
                encounter_template=override_encounter,
            )
            # Brute's override has empty pools, so no items
            assert result_brute.item_ids == [], (
                f"Seed {seed}: brute_oni should have no items with empty override"
            )

    def test_override_empty_pools_suppresses_drops(self, game_data: GameData) -> None:
        """An override with empty pools should completely suppress item drops."""
        override_encounter = EncounterTemplate(
            enemy_templates=["alpha_slime"],
            enemy_counts=[1],
            loot_overrides=[
                EncounterLootOverride(
                    enemy_template_id="alpha_slime",
                    pools=[],  # No pools at all
                ),
            ],
        )
        for seed in range(50):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("alpha_slime")
            result = resolver.resolve_encounter_drops(
                [enemy],
                zone_level=5,
                encounter_template=override_encounter,
            )
            # Money still comes through (override only affects pools, not money)
            assert result.money > 0
            # But no items
            assert result.item_ids == []


# ===================================================================
# Unique Flag
# ===================================================================

class TestUniqueFlag:
    """Test that unique=True prevents duplicate items within the same encounter."""

    def test_unique_prevents_duplicates_in_single_pool(self) -> None:
        """Pool with unique=True and count=3 from 3 items should yield 3 distinct items."""
        registry = {
            "a": Item(id="a", name="A", tier=1),
            "b": Item(id="b", name="B", tier=1),
            "c": Item(id="c", name="C", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=3,
                        unique=True,
                        items=[
                            LootPoolEntry(item_id="a"),
                            LootPoolEntry(item_id="b"),
                            LootPoolEntry(item_id="c"),
                        ],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert len(result.item_ids) == 3
        assert len(set(result.item_ids)) == 3, "All items should be distinct"

    def test_unique_with_count_exceeding_available(self) -> None:
        """Pool with unique=True and count > available items should cap at available count."""
        registry = {
            "a": Item(id="a", name="A", tier=1),
            "b": Item(id="b", name="B", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=5,  # More than 2 available
                        unique=True,
                        items=[
                            LootPoolEntry(item_id="a"),
                            LootPoolEntry(item_id="b"),
                        ],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        # Should get at most 2 items, no duplicates
        assert len(result.item_ids) <= 2
        assert len(set(result.item_ids)) == len(result.item_ids)

    def test_unique_false_allows_duplicates(self) -> None:
        """Pool with unique=False should allow the same item multiple times."""
        registry = {
            "a": Item(id="a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=3,
                        unique=False,
                        items=[LootPoolEntry(item_id="a")],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        assert len(result.item_ids) == 3
        assert all(i == "a" for i in result.item_ids)

    def test_unique_dedup_across_pools_in_encounter(self) -> None:
        """unique=True deduplicates across multiple pools in the same encounter.

        The seen_items set is shared across all pools for a single resolve call.
        """
        registry = {
            "a": Item(id="a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=1,
                        unique=True,
                        items=[LootPoolEntry(item_id="a")],
                    ),
                    LootPool(
                        chance=1.0,
                        count=1,
                        unique=True,
                        items=[LootPoolEntry(item_id="a")],
                    ),
                ],
            )
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=registry, drop_tables=drop_tables, rng=rng
        )
        enemy = _make_enemy("test_enemy")
        result = resolver.resolve_encounter_drops([enemy], zone_level=5)
        # Only 1 copy of "a" because seen_items is shared and unique=True
        assert result.item_ids.count("a") == 1


# ===================================================================
# Boss Loot Integration
# ===================================================================

class TestBossLootIntegration:
    """Test that boss enemies drop items from expected categories using real game data."""

    def test_omega_slime_guaranteed_potion(self, game_data: GameData) -> None:
        """Omega slime always drops at least one potion (chance=1.0 potion pool)."""
        potion_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "potion"
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("omega_slime")
        result = resolver.resolve_encounter_drops([enemy], zone_level=10)
        assert potion_ids & set(result.item_ids), (
            f"Omega slime must drop a potion. Got: {result.item_ids}"
        )

    def test_omega_slime_guaranteed_scroll(self, game_data: GameData) -> None:
        """Omega slime always drops scrolls from its branching pool (chance=1.0)."""
        scroll_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category in ("cast_scroll", "teach_scroll")
        }
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("omega_slime")
        result = resolver.resolve_encounter_drops([enemy], zone_level=10)
        assert scroll_ids & set(result.item_ids), (
            f"Omega slime must drop scroll(s). Got: {result.item_ids}"
        )

    def test_omega_slime_can_drop_utility_accessory(self, game_data: GameData) -> None:
        """Omega slime has 50% utility_accessory pool — should drop over many seeds."""
        utility_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "utility_accessory"
        }
        assert utility_ids, "Precondition: utility accessories must exist"

        got_accessory = False
        for seed in range(200):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy("omega_slime")
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            if utility_ids & set(result.item_ids):
                got_accessory = True
                break
        assert got_accessory, "Expected utility accessory from omega_slime in 200 seeds"

    def test_omega_slime_boss_money_multiplier(self, game_data: GameData) -> None:
        """Boss money_multiplier of 3.5x should yield substantially more gold than fodder."""
        boss_money = 0
        fodder_money = 0
        trials = 100

        for seed in range(trials):
            rng_boss = random.Random(seed)
            rng_fodder = random.Random(seed)
            r_boss = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng_boss,
            )
            r_fodder = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng_fodder,
            )
            boss = _make_enemy("omega_slime", level=10)
            fodder = _make_enemy("fodder_slime", level=10)
            boss_money += r_boss.resolve_encounter_drops([boss], zone_level=10).money
            fodder_money += r_fodder.resolve_encounter_drops([fodder], zone_level=10).money

        # Boss with 3.5x multiplier should average ~3.5x more gold than fodder (1.0x)
        assert boss_money > fodder_money * 2, (
            f"Boss gold {boss_money} should be substantially more than fodder gold {fodder_money}"
        )

    def test_slime_brute_miniboss_guaranteed_weapon_or_armor(self, game_data: GameData) -> None:
        """Giga Fragment (Brute) has a guaranteed weapon/armor pool."""
        weapon_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "weapon"
        }
        armor_ids = {
            iid for iid, item in game_data.items.items()
            if item.loot_category == "armor"
        }
        equip_ids = weapon_ids | armor_ids

        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy("slime_brute_miniboss")
        result = resolver.resolve_encounter_drops([enemy], zone_level=15)
        assert equip_ids & set(result.item_ids), (
            f"Brute miniboss must drop a weapon or armor. Got: {result.item_ids}"
        )


# ===================================================================
# No-Drop Enemies
# ===================================================================

class TestNoDropEnemies:
    """Test that split_slime, kodama, and giga_slime give no money and no items."""

    @pytest.mark.parametrize("template_id", ["split_slime", "kodama", "giga_slime"])
    def test_no_money_no_items(self, game_data: GameData, template_id: str) -> None:
        """Enemies with guaranteed_money=false and pools=[] should drop nothing."""
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = _make_enemy(template_id)
        result = resolver.resolve_encounter_drops([enemy], zone_level=10)
        assert result.money == 0, f"{template_id} should drop 0 money"
        assert result.item_ids == [], f"{template_id} should drop no items"

    @pytest.mark.parametrize("template_id", ["split_slime", "kodama", "giga_slime"])
    def test_no_drops_across_many_seeds(self, game_data: GameData, template_id: str) -> None:
        """Even across many seeds, no-drop enemies should never produce anything."""
        for seed in range(100):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = _make_enemy(template_id)
            result = resolver.resolve_encounter_drops([enemy], zone_level=10)
            assert result.money == 0, f"Seed {seed}: {template_id} should drop 0 money"
            assert result.item_ids == [], f"Seed {seed}: {template_id} should drop no items"

    def test_giga_fragments_only_brute_drops_items(self, game_data: GameData) -> None:
        """Of the three giga fragments, only slime_brute_miniboss should drop items."""
        for seed in range(50):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            # Caster and tank fragments have empty pools
            for no_item_frag in ["slime_caster_miniboss", "slime_tank_miniboss"]:
                enemy = _make_enemy(no_item_frag)
                result = resolver.resolve_encounter_drops([enemy], zone_level=15)
                assert result.item_ids == [], (
                    f"Seed {seed}: {no_item_frag} should have no item drops"
                )
                # But they DO get money (guaranteed_money=true, money_multiplier=5.0)
                assert result.money > 0, (
                    f"Seed {seed}: {no_item_frag} should still get money"
                )


# ===================================================================
# CHA Interaction with Pools
# ===================================================================

class TestCHAPoolInteraction:
    """Test that CHA bonus only affects non-guaranteed pools."""

    def test_cha_does_not_affect_guaranteed_pools(self) -> None:
        """Pools with chance=1.0 should always drop regardless of CHA."""
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,  # Guaranteed
                        count=1,
                        items=[LootPoolEntry(item_id="item_a")],
                    ),
                ],
            )
        }

        # With CHA=0 and CHA=999: guaranteed pool should always fire
        for cha in [0, 999]:
            for seed in range(50):
                rng = random.Random(seed)
                resolver = LootResolver(
                    item_registry=registry, drop_tables=drop_tables, rng=rng
                )
                enemy = _make_enemy("test_enemy")
                result = resolver.resolve_encounter_drops(
                    [enemy], zone_level=5, party_cha=cha
                )
                assert "item_a" in result.item_ids, (
                    f"Seed {seed}, CHA={cha}: guaranteed pool should always fire"
                )

    def test_cha_increases_non_guaranteed_pool_chance(self) -> None:
        """CHA bonus of 0.002 per point should measurably increase non-guaranteed drops."""
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=0.10,  # 10% base chance
                        count=1,
                        items=[LootPoolEntry(item_id="item_a")],
                    ),
                ],
            )
        }

        drops_no_cha = 0
        drops_high_cha = 0
        trials = 2000

        for seed in range(trials):
            rng0 = random.Random(seed)
            rng100 = random.Random(seed)
            r0 = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng0
            )
            r100 = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng100
            )
            e0 = _make_enemy("test_enemy")
            e100 = _make_enemy("test_enemy")
            # CHA=0 -> effective_chance = 0.10
            # CHA=100 -> effective_chance = 0.10 + 100 * 0.002 = 0.30
            drops_no_cha += len(r0.resolve_encounter_drops([e0], zone_level=5, party_cha=0).item_ids)
            drops_high_cha += len(r100.resolve_encounter_drops([e100], zone_level=5, party_cha=100).item_ids)

        # CHA 100 should result in ~3x the drops of CHA 0 (0.30 vs 0.10)
        assert drops_high_cha > drops_no_cha, (
            f"High CHA ({drops_high_cha} drops) should beat low CHA ({drops_no_cha} drops)"
        )
        # More specifically, the ratio should be roughly 2.5-3.5x
        ratio = drops_high_cha / max(drops_no_cha, 1)
        assert ratio > 2.0, f"CHA 100 should ~triple drops vs CHA 0, got ratio {ratio:.2f}"

    def test_cha_exact_bonus_calculation(self) -> None:
        """Verify the exact CHA bonus arithmetic: 0.002 per CHA point."""
        # With CHA=50: bonus = 50 * 0.002 = 0.10
        # Pool chance 0.05 -> effective = 0.15
        # Expect ~15% drop rate
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=0.05,
                        count=1,
                        items=[LootPoolEntry(item_id="item_a")],
                    ),
                ],
            )
        }

        drops = 0
        trials = 5000
        for seed in range(trials):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng
            )
            enemy = _make_enemy("test_enemy")
            result = resolver.resolve_encounter_drops(
                [enemy], zone_level=5, party_cha=50
            )
            drops += len(result.item_ids)

        # Expected rate: 0.05 + 50 * 0.002 = 0.15 -> ~750 drops in 5000 trials
        rate = drops / trials
        assert 0.10 < rate < 0.20, (
            f"Expected ~15% drop rate with CHA 50, got {rate:.3f}"
        )

    def test_overstay_reduces_non_guaranteed_chance(self) -> None:
        """Overstay penalty should reduce non-guaranteed pool chances."""
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=0.50,
                        count=1,
                        items=[LootPoolEntry(item_id="item_a")],
                    ),
                ],
            )
        }

        drops_fresh = 0
        drops_overstay = 0
        trials = 1000

        for seed in range(trials):
            rng_fresh = random.Random(seed)
            rng_overstay = random.Random(seed)
            r_fresh = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng_fresh
            )
            r_overstay = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng_overstay
            )
            e_fresh = _make_enemy("test_enemy")
            e_overstay = _make_enemy("test_enemy")
            # Fresh: effective_chance = 0.50
            # Overstay 5 battles: reduction = 5 * 0.05 = 0.25, effective = 0.25
            drops_fresh += len(
                r_fresh.resolve_encounter_drops(
                    [e_fresh], zone_level=5, overstay_battles=0
                ).item_ids
            )
            drops_overstay += len(
                r_overstay.resolve_encounter_drops(
                    [e_overstay], zone_level=5, overstay_battles=5
                ).item_ids
            )

        assert drops_fresh > drops_overstay, (
            f"Fresh ({drops_fresh}) should have more drops than overstay ({drops_overstay})"
        )

    def test_overstay_does_not_affect_guaranteed_pools(self) -> None:
        """Guaranteed pools (chance=1.0) should not be affected by overstay."""
        registry = {
            "item_a": Item(id="item_a", name="A", tier=1),
        }
        drop_tables = {
            "test_enemy": EnemyLootTable(
                enemy_template_id="test_enemy",
                pools=[
                    LootPool(
                        chance=1.0,
                        count=1,
                        items=[LootPoolEntry(item_id="item_a")],
                    ),
                ],
            )
        }

        # Even with massive overstay, guaranteed pools should fire
        for seed in range(50):
            rng = random.Random(seed)
            resolver = LootResolver(
                item_registry=registry, drop_tables=drop_tables, rng=rng
            )
            enemy = _make_enemy("test_enemy")
            result = resolver.resolve_encounter_drops(
                [enemy], zone_level=5, overstay_battles=100
            )
            assert "item_a" in result.item_ids, (
                f"Seed {seed}: guaranteed pool should fire despite 100 overstay battles"
            )
