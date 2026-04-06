"""Tests for encounter generation system."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.encounter import BOSS_BUDGET_MULTIPLIER, EncounterGenerator
from heresiarch.engine.formulas import calculate_enemy_hp
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
    def test_boss_has_boosted_hp(
        self, encounter_gen: EncounterGenerator, game_data: GameData
    ) -> None:
        normal_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=False
        )
        boss_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=True
        )
        normal = encounter_gen.generate_encounter(normal_tmpl, zone_level=15)
        boss = encounter_gen.generate_encounter(boss_tmpl, zone_level=15)
        assert boss[0].max_hp > normal[0].max_hp

    def test_boss_has_boosted_stats(
        self, encounter_gen: EncounterGenerator
    ) -> None:
        normal_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=False
        )
        boss_tmpl = EncounterTemplate(
            enemy_templates=["brute_oni"], enemy_counts=[1], is_boss=True
        )
        normal = encounter_gen.generate_encounter(normal_tmpl, zone_level=15)
        boss = encounter_gen.generate_encounter(boss_tmpl, zone_level=15)
        assert boss[0].stats.STR > normal[0].stats.STR


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
