"""Tests for mid-combat spawning: summon abilities and death-spawn mechanics."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    PlayerTurnDecision,
)


def _make_character(game_data: GameData, job_id: str, level: int, weapon_id: str | None = None):
    """Create a test character at given level."""
    from heresiarch.engine.formulas import calculate_effective_stats, calculate_max_hp, calculate_stats_at_level
    from heresiarch.engine.models.jobs import CharacterInstance

    job = game_data.jobs[job_id]
    stats = calculate_stats_at_level(job.growth, level)
    equipped = []
    equipment = {"WEAPON": None, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None}
    if weapon_id and weapon_id in game_data.items:
        equipment["WEAPON"] = weapon_id
        equipped.append(game_data.items[weapon_id])
    effective = calculate_effective_stats(stats, equipped, [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, effective.DEF)
    abilities = ["basic_attack", job.innate_ability_id]
    for unlock in job.ability_unlocks:
        if unlock.level <= level and unlock.ability_id not in abilities:
            abilities.append(unlock.ability_id)
    return CharacterInstance(
        id=f"mc_{job_id}",
        name="Test",
        job_id=job_id,
        level=level,
        xp=0,
        base_stats=stats,
        effective_stats=effective,
        current_hp=max_hp,
        max_hp=max_hp,
        abilities=abilities,
        equipment=equipment,
        is_mc=True,
    )


class TestSummonAbility:
    def test_summon_kodama_spawns_enemies(self, game_data: GameData) -> None:
        """Kodama Elder's summon_kodama should add 2 kodama to enemy combatants."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )

        template = game_data.enemies["kodama_elder"]
        boss = engine.create_enemy_instance(template, enemy_level=8, instance_id="kodama_elder_0")
        player = _make_character(game_data, "einherjar", 10, "iron_blade")

        state = engine.initialize_combat([player], [boss])
        initial_enemy_count = len(state.enemy_combatants)

        # Force the boss to use summon_kodama
        boss_combatant = state.get_combatant("kodama_elder_0")
        assert boss_combatant is not None
        boss_combatant.pending_action = CombatAction(
            actor_id="kodama_elder_0",
            ability_id="summon_kodama",
            target_ids=["kodama_elder_0"],  # SELF target
        )

        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # Should have 2 more enemies (kodama)
        assert len(state.enemy_combatants) == initial_enemy_count + 2

        # Check for ENEMY_SUMMONED events
        summon_events = [e for e in state.log if e.event_type == CombatEventType.ENEMY_SUMMONED]
        assert len(summon_events) == 2
        for event in summon_events:
            assert event.details["template_id"] == "kodama"

    def test_summoned_enemies_have_correct_level(self, game_data: GameData) -> None:
        """Summoned kodama should be at the summoner's level."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )

        template = game_data.enemies["kodama_elder"]
        boss = engine.create_enemy_instance(template, enemy_level=8, instance_id="kodama_elder_0")
        player = _make_character(game_data, "einherjar", 10, "iron_blade")

        state = engine.initialize_combat([player], [boss])

        boss_combatant = state.get_combatant("kodama_elder_0")
        assert boss_combatant is not None
        boss_combatant.pending_action = CombatAction(
            actor_id="kodama_elder_0",
            ability_id="summon_kodama",
            target_ids=["kodama_elder_0"],
        )

        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # Find the spawned kodama (not kodama_elder)
        kodama_combatants = [
            c for c in state.enemy_combatants
            if c.id.startswith("kodama_") and not c.id.startswith("kodama_elder")
        ]
        assert len(kodama_combatants) == 2
        for kodama in kodama_combatants:
            assert kodama.level == 8  # same as summoner
            assert kodama.is_alive

    def test_summon_respects_cooldown(self, game_data: GameData) -> None:
        """summon_kodama has cooldown 5 — shouldn't be selectable again immediately."""
        ability = game_data.abilities["summon_kodama"]
        assert ability.cooldown == 5


class TestMitosisPassive:
    def test_split_into_templates_field_exists(self, game_data: GameData) -> None:
        """Verify split_into_templates field exists on AbilityEffect."""
        ability = game_data.abilities["mitosis"]
        assert ability.effects[0].split_into_templates == ["mini_slime", "mini_slime"]

    def test_non_splitter_has_no_split_passive(self, game_data: GameData) -> None:
        """Regular enemies should not have split passives."""
        template = game_data.enemies["fodder_slime"]
        assert "mitosis" not in template.abilities
        assert "giga_mitosis" not in template.abilities

    def test_kodama_elder_data_valid(self, game_data: GameData) -> None:
        """Kodama Elder should load with all expected abilities."""
        template = game_data.enemies["kodama_elder"]
        assert "summon_kodama" in template.abilities
        assert "regen" in template.abilities
        assert "heal_ally" in template.abilities
        assert "rally" in template.abilities

    def test_kodama_data_valid(self, game_data: GameData) -> None:
        """Kodama should load as a lightweight support enemy."""
        template = game_data.enemies["kodama"]
        assert "bolt" in template.abilities
        assert template.budget_multiplier == 6.0
