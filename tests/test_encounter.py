"""Tests for encounter generation system."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.encounter import EncounterGenerator
from heresiarch.engine.models.zone import EncounterTemplate


@pytest.fixture
def encounter_gen(
    game_data: GameData, combat_engine: CombatEngine, seeded_rng: random.Random
) -> EncounterGenerator:
    return EncounterGenerator(
        enemy_registry=game_data.enemies,
        combat_engine=combat_engine,
        rng=seeded_rng,
    )


class TestSingleEnemy:
    def test_one_fodder(
        self, encounter_gen: EncounterGenerator, game_data: GameData
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[1]
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=5)
        assert len(enemies) == 1
        assert enemies[0].template_id == "fodder_slime"
        assert enemies[0].level == 5


class TestGroupEncounter:
    def test_three_fodder(self, encounter_gen: EncounterGenerator) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[3]
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=5)
        assert len(enemies) == 3

    def test_unique_ids(self, encounter_gen: EncounterGenerator) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[3]
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=5)
        names = [e.name for e in enemies]
        assert len(set(names)) == 3
        # Names should be like fodder_slime_0, fodder_slime_1, fodder_slime_2
        for i, name in enumerate(names):
            assert name == f"fodder_slime_{i}"


class TestMixedEncounter:
    def test_mixed_group(self, encounter_gen: EncounterGenerator) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime", "brute_oni"], enemy_counts=[2, 1]
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=10)
        assert len(enemies) == 3
        template_ids = [e.template_id for e in enemies]
        assert template_ids.count("fodder_slime") == 2
        assert template_ids.count("brute_oni") == 1


class TestBossEncounter:
    def test_boss_no_budget_multiplier_boost(
        self, encounter_gen: EncounterGenerator, game_data: GameData
    ) -> None:
        """Boss encounters use the template's own budget_multiplier, no automatic boost."""
        normal_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=False
        )
        boss_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=True
        )
        normal = encounter_gen.generate_encounter(normal_tmpl, zone_level=15)
        boss = encounter_gen.generate_encounter(boss_tmpl, zone_level=15)
        assert boss[0].max_hp == normal[0].max_hp
        assert boss[0].stats.STR == normal[0].stats.STR


class TestPerEncounterLevelRange:
    """Per-encounter enemy_level_range overrides the zone-wide range."""

    def test_encounter_range_overrides_zone_range(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"],
            enemy_counts=[1],
            enemy_level_range=(10, 10),
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(1, 3),
        )
        assert enemies[0].level == 10

    def test_encounter_range_equal_pins_level(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"],
            enemy_counts=[3],
            enemy_level_range=(7, 7),
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(1, 20),
        )
        assert all(e.level == 7 for e in enemies)

    def test_boss_override_beats_encounter_range(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"],
            enemy_counts=[1],
            is_boss=True,
            enemy_level_override=20,
            enemy_level_range=(5, 5),
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=1)
        assert enemies[0].level == 20

    def test_encounter_range_within_bounds(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"],
            enemy_counts=[20],
            enemy_level_range=(3, 6),
        )
        enemies = encounter_gen.generate_encounter(template, zone_level=1)
        for e in enemies:
            assert 3 <= e.level <= 6


class TestAutoInterpolation:
    """Zone-wide range is interpolated based on encounter position."""

    def test_first_encounter_skews_low(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[30],
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
            encounter_index=0, total_encounters=6,
        )
        levels = [e.level for e in enemies]
        # First encounter: center=5, range=[5, 6] — all should be 5 or 6
        assert all(5 <= lv <= 6 for lv in levels)

    def test_last_encounter_skews_high(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[30],
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
            encounter_index=5, total_encounters=6,
        )
        levels = [e.level for e in enemies]
        # Last encounter: center=15, range=[14, 15] — all should be 14 or 15
        assert all(14 <= lv <= 15 for lv in levels)

    def test_mid_encounter_is_between(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[30],
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
            encounter_index=3, total_encounters=6,
        )
        levels = [e.level for e in enemies]
        # Mid encounter: center=11, range=[10, 12]
        assert all(5 <= lv <= 15 for lv in levels)
        avg = sum(levels) / len(levels)
        # Average should be roughly in the middle, not at the extremes
        assert 8 < avg < 14

    def test_single_encounter_no_interpolation(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        """With only 1 encounter, fall through to flat zone range."""
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[20],
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
            encounter_index=0, total_encounters=1,
        )
        levels = [e.level for e in enemies]
        # Should use flat range [5, 15] — expect some spread
        assert all(5 <= lv <= 15 for lv in levels)

    def test_overstay_no_interpolation(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        """Overstay (no index passed) uses flat zone range."""
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[20],
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
        )
        levels = [e.level for e in enemies]
        assert all(5 <= lv <= 15 for lv in levels)

    def test_encounter_range_overrides_interpolation(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        """Per-encounter range takes priority over auto-interpolation."""
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"],
            enemy_counts=[10],
            enemy_level_range=(20, 20),
        )
        enemies = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(5, 15),
            encounter_index=0, total_encounters=6,
        )
        assert all(e.level == 20 for e in enemies)

    def test_interpolation_clamped_to_zone_bounds(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        """Interpolated range never exceeds zone min/max."""
        template = EncounterTemplate(
            enemy_templates=["fodder_slime"], enemy_counts=[30],
        )
        # First encounter
        early = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(3, 5),
            encounter_index=0, total_encounters=6,
        )
        # Last encounter
        late = encounter_gen.generate_encounter(
            template, zone_level=1, enemy_level_range=(3, 5),
            encounter_index=5, total_encounters=6,
        )
        for e in early:
            assert 3 <= e.level <= 5
        for e in late:
            assert 3 <= e.level <= 5


class TestZoneEncounterSequence:
    def test_zone_01_encounters(
        self, encounter_gen: EncounterGenerator, game_data: GameData
    ) -> None:
        zone = game_data.zones["zone_01"]
        for enc_template in zone.encounters:
            enemies = encounter_gen.generate_encounter(enc_template, zone.zone_level)
            assert len(enemies) > 0
            for enemy in enemies:
                assert enemy.max_hp > 0
                assert enemy.stats.STR >= 0
