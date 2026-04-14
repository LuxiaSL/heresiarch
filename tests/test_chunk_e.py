"""Tests for Chunk E: endless zone mechanics + Giga Slime redesign."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.encounter import EncounterGenerator
from heresiarch.engine.formulas import calculate_endless_reward_multiplier
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.combat_state import (
    CombatAction,
    CombatEventType,
    CheatSurviveChoice,
    PlayerTurnDecision,
)
from heresiarch.engine.models.run_state import CombatResult


# ===================================================================
# E1: Endless Zone Reward Tapering
# ===================================================================


class TestEndlessRewardMultiplier:
    def test_full_reward_at_low_level(self) -> None:
        """Player well below cap gets near-full rewards."""
        mult = calculate_endless_reward_multiplier(player_level=5, zone_max_level=28)
        assert mult > 0.95

    def test_floor_at_cap(self) -> None:
        """Player at or above cap gets floor reward."""
        mult = calculate_endless_reward_multiplier(player_level=28, zone_max_level=28)
        assert mult == pytest.approx(0.1)

    def test_floor_above_cap(self) -> None:
        """Player above cap gets floor reward."""
        mult = calculate_endless_reward_multiplier(player_level=35, zone_max_level=28)
        assert mult == pytest.approx(0.1)

    def test_diminishing_mid_range(self) -> None:
        """Player mid-range gets partial reward — not full, not floor."""
        mult = calculate_endless_reward_multiplier(player_level=20, zone_max_level=28)
        assert 0.1 < mult < 1.0

    def test_monotonically_decreasing(self) -> None:
        """Higher player level → lower multiplier."""
        prev = 2.0
        for level in range(1, 35):
            mult = calculate_endless_reward_multiplier(player_level=level, zone_max_level=28)
            assert mult <= prev
            prev = mult

    def test_zero_max_level_returns_full(self) -> None:
        """Edge case: zone_max_level 0 shouldn't crash."""
        mult = calculate_endless_reward_multiplier(player_level=10, zone_max_level=0)
        assert mult == 1.0


# ===================================================================
# E1: Endless Zone Model + Data
# ===================================================================


class TestEndlessZoneData:
    def test_the_pit_exists(self, game_data: GameData) -> None:
        assert "the_pit" in game_data.zones

    def test_the_pit_is_endless(self, game_data: GameData) -> None:
        pit = game_data.zones["the_pit"]
        assert pit.is_endless is True

    def test_the_pit_has_enemy_pool(self, game_data: GameData) -> None:
        pit = game_data.zones["the_pit"]
        assert len(pit.endless_enemy_pool) >= 10
        # All pool entries should be valid enemy templates
        for template_id in pit.endless_enemy_pool:
            assert template_id in game_data.enemies, f"Unknown enemy in pool: {template_id}"

    def test_the_pit_level_range(self, game_data: GameData) -> None:
        pit = game_data.zones["the_pit"]
        assert pit.endless_min_level == 18
        assert pit.endless_max_level == 28

    def test_the_pit_empty_encounters(self, game_data: GameData) -> None:
        """Endless zones have no predefined encounters."""
        pit = game_data.zones["the_pit"]
        assert len(pit.encounters) == 0

    def test_the_pit_unlocks_after_zone_06(self, game_data: GameData) -> None:
        pit = game_data.zones["the_pit"]
        assert any(
            r.type == "zone_clear" and r.zone_id == "zone_06"
            for r in pit.unlock_requires
        )

    def test_regular_zones_not_endless(self, game_data: GameData) -> None:
        """All non-Pit zones should have is_endless=False."""
        for zone_id, zone in game_data.zones.items():
            if zone_id != "the_pit":
                assert zone.is_endless is False, f"{zone_id} is wrongly endless"


# ===================================================================
# E1: Endless Encounter Generation
# ===================================================================


class TestEndlessEncounterGeneration:
    def test_generates_valid_enemies(self, game_data: GameData) -> None:
        """Endless encounter generates enemies from the pool."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        gen = EncounterGenerator(
            enemy_registry=game_data.enemies,
            combat_engine=engine,
            rng=rng,
        )
        pit = game_data.zones["the_pit"]
        enemies = gen.generate_endless_encounter(
            enemy_pool=pit.endless_enemy_pool,
            player_level=20,
            min_level=pit.endless_min_level,
            max_level=pit.endless_max_level,
        )
        assert 2 <= len(enemies) <= 4
        for enemy in enemies:
            assert enemy.template_id in pit.endless_enemy_pool

    def test_enemy_levels_clamp_to_range(self, game_data: GameData) -> None:
        """Enemy levels should stay within the zone's level range."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        gen = EncounterGenerator(
            enemy_registry=game_data.enemies,
            combat_engine=engine,
            rng=rng,
        )
        pit = game_data.zones["the_pit"]
        # Player well above max — should clamp
        enemies = gen.generate_endless_encounter(
            enemy_pool=pit.endless_enemy_pool,
            player_level=50,
            min_level=pit.endless_min_level,
            max_level=pit.endless_max_level,
        )
        for enemy in enemies:
            assert pit.endless_min_level <= enemy.level <= pit.endless_max_level

    def test_enemy_levels_clamp_low(self, game_data: GameData) -> None:
        """Player below min_level — enemies at min_level."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        gen = EncounterGenerator(
            enemy_registry=game_data.enemies,
            combat_engine=engine,
            rng=rng,
        )
        pit = game_data.zones["the_pit"]
        enemies = gen.generate_endless_encounter(
            enemy_pool=pit.endless_enemy_pool,
            player_level=5,
            min_level=pit.endless_min_level,
            max_level=pit.endless_max_level,
        )
        for enemy in enemies:
            assert enemy.level >= pit.endless_min_level

    def test_empty_pool_raises(self, game_data: GameData) -> None:
        """Empty or invalid pool should raise."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        gen = EncounterGenerator(
            enemy_registry=game_data.enemies,
            combat_engine=engine,
            rng=rng,
        )
        with pytest.raises(ValueError, match="No valid enemies"):
            gen.generate_endless_encounter(
                enemy_pool=["nonexistent_enemy"],
                player_level=20,
                min_level=18,
                max_level=28,
            )


# ===================================================================
# E1: Game Loop — Endless Zone Behavior
# ===================================================================


class TestEndlessGameLoop:
    def test_endless_zone_never_clears(self, game_data: GameData) -> None:
        """Advancing in an endless zone should never set is_cleared."""
        game_loop = GameLoop(game_data, rng=random.Random(42))
        run = game_loop.new_run("test", "Hero", "einherjar")
        # Cheat: unlock the pit
        run = run.model_copy(update={
            "zones_completed": ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05", "zone_06"],
        })
        run = game_loop.enter_zone(run, "the_pit")
        # Advance several times — should never clear
        for _ in range(10):
            run = game_loop.advance_zone(run)
            assert run.zone_state is not None
            assert not run.zone_state.is_cleared

    def test_endless_zone_tracks_battles(self, game_data: GameData) -> None:
        """Overstay counter increments each advance in endless zones."""
        game_loop = GameLoop(game_data, rng=random.Random(42))
        run = game_loop.new_run("test", "Hero", "einherjar")
        run = run.model_copy(update={
            "zones_completed": ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05", "zone_06"],
        })
        run = game_loop.enter_zone(run, "the_pit")
        for i in range(5):
            run = game_loop.advance_zone(run)
            assert run.zone_state is not None
            assert run.zone_state.overstay_battles == i + 1

    def test_endless_encounter_generation_from_game_loop(self, game_data: GameData) -> None:
        """get_next_encounter should work for endless zones."""
        game_loop = GameLoop(game_data, rng=random.Random(42))
        run = game_loop.new_run("test", "Hero", "einherjar")
        run = run.model_copy(update={
            "zones_completed": ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05", "zone_06"],
        })
        run = game_loop.enter_zone(run, "the_pit")
        enemies = game_loop.get_next_encounter(run)
        assert 2 <= len(enemies) <= 4
        for enemy in enemies:
            pit = game_data.zones["the_pit"]
            assert enemy.template_id in pit.endless_enemy_pool

    def test_endless_xp_tapering(self, game_data: GameData) -> None:
        """Endless zone XP should be reduced at higher player levels."""
        game_loop = GameLoop(game_data, rng=random.Random(42))

        # Create two runs: one low level, one high level
        run_low = game_loop.new_run("low", "Hero", "einherjar")
        run_high = game_loop.new_run("high", "Hero", "einherjar")

        mc_low = game_loop._get_mc(run_low)
        mc_high_old = game_loop._get_mc(run_high)
        assert mc_low is not None and mc_high_old is not None

        # Manually set high-level character
        chars_high = dict(run_high.party.characters)
        chars_high[mc_high_old.id] = mc_high_old.model_copy(update={"level": 27, "xp": 99999})
        run_high = run_high.model_copy(update={
            "party": run_high.party.model_copy(update={"characters": chars_high}),
        })
        # Re-fetch mc_high from updated run so baseline XP is correct
        mc_high = game_loop._get_mc(run_high)
        assert mc_high is not None

        completed = ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05", "zone_06"]
        run_low = run_low.model_copy(update={"zones_completed": completed})
        run_high = run_high.model_copy(update={"zones_completed": completed})
        run_low = game_loop.enter_zone(run_low, "the_pit")
        run_high = game_loop.enter_zone(run_high, "the_pit")

        # Same combat result — identical enemies killed
        result_low = CombatResult(
            player_won=True,
            zone_level=20,
            defeated_enemy_template_ids=["slime"],
            defeated_enemy_budget_multipliers=[9.0],
            defeated_enemy_levels=[20],
            defeated_enemy_xp_multipliers=[0.0],
            defeated_enemy_gold_multipliers=[0.0],
            surviving_character_ids=[mc_low.id],
            surviving_character_hp={mc_low.id: mc_low.max_hp},
        )
        result_high = CombatResult(
            player_won=True,
            zone_level=20,
            defeated_enemy_template_ids=["slime"],
            defeated_enemy_budget_multipliers=[9.0],
            defeated_enemy_levels=[20],
            defeated_enemy_xp_multipliers=[0.0],
            defeated_enemy_gold_multipliers=[0.0],
            surviving_character_ids=[mc_high.id],
            surviving_character_hp={mc_high.id: mc_high.max_hp},
        )

        run_low_after, _ = game_loop.resolve_combat_result(run_low, result_low)
        run_high_after, _ = game_loop.resolve_combat_result(run_high, result_high)

        mc_low_after = game_loop._get_mc(run_low_after)
        mc_high_after = game_loop._get_mc(run_high_after)
        assert mc_low_after is not None and mc_high_after is not None
        xp_gain_low = mc_low_after.xp - mc_low.xp
        xp_gain_high = mc_high_after.xp - mc_high.xp
        assert xp_gain_low > xp_gain_high


# ===================================================================
# E2: Giga Slime Data
# ===================================================================


class TestGigaSlimeData:
    def test_giga_slime_exists(self, game_data: GameData) -> None:
        assert "giga_slime" in game_data.enemies

    def test_giga_slime_has_mitosis_passive(self, game_data: GameData) -> None:
        giga = game_data.enemies["giga_slime"]
        assert "giga_mitosis" in giga.abilities
        ability = game_data.abilities["giga_mitosis"]
        assert set(ability.effects[0].split_into_templates) == {
            "slime_brute_miniboss", "slime_caster_miniboss", "slime_tank_miniboss",
        }

    def test_giga_slime_has_regen_enhanced(self, game_data: GameData) -> None:
        giga = game_data.enemies["giga_slime"]
        assert "regen_enhanced" in giga.abilities

    def test_giga_slime_has_summon(self, game_data: GameData) -> None:
        giga = game_data.enemies["giga_slime"]
        assert "summon_slimes" in giga.abilities

    def test_giga_slime_phase_shift(self, game_data: GameData) -> None:
        giga = game_data.enemies["giga_slime"]
        conditions = giga.action_table.conditions
        hp_below = [c for c in conditions if c.condition_type == "self_hp_below"]
        assert len(hp_below) == 1
        assert hp_below[0].threshold == 0.50

    def test_all_mini_bosses_exist(self, game_data: GameData) -> None:
        for boss_id in ["slime_brute_miniboss", "slime_caster_miniboss", "slime_tank_miniboss"]:
            assert boss_id in game_data.enemies, f"Missing mini-boss: {boss_id}"

    def test_mini_boss_budget_multipliers(self, game_data: GameData) -> None:
        for boss_id in ["slime_brute_miniboss", "slime_caster_miniboss", "slime_tank_miniboss"]:
            boss = game_data.enemies[boss_id]
            assert boss.budget_multiplier == 12.0

    def test_summon_slimes_ability_exists(self, game_data: GameData) -> None:
        ability = game_data.abilities["summon_slimes"]
        assert ability.cooldown == 5
        effect = ability.effects[0]
        assert effect.summon_template_id == "slime"
        assert effect.summon_count == 2
        assert effect.summon_level_offset == -2

    def test_zone_07_uses_giga_slime(self, game_data: GameData) -> None:
        zone = game_data.zones["zone_07"]
        boss_encounters = [e for e in zone.encounters if e.is_boss]
        assert len(boss_encounters) == 1
        assert "giga_slime" in boss_encounters[0].enemy_templates

    def test_giga_slime_splits_on_lethal(self, game_data: GameData) -> None:
        """Killing Giga Slime should trigger giga_mitosis, spawning 3 mini-bosses."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )

        from heresiarch.engine.formulas import calculate_effective_stats, calculate_max_hp, calculate_stats_at_level
        from heresiarch.engine.models.jobs import CharacterInstance

        job = game_data.jobs["einherjar"]
        stats = calculate_stats_at_level(job.growth, 33)
        equipped = [game_data.items["iron_blade"]] if "iron_blade" in game_data.items else []
        effective = calculate_effective_stats(stats, equipped, [])
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, 33, effective.DEF)
        player = CharacterInstance(
            id="mc_einherjar", name="Test", job_id="einherjar", level=33, xp=0,
            base_stats=stats, effective_stats=effective,
            current_hp=max_hp, max_hp=max_hp,
            abilities=["basic_attack", job.innate_ability_id],
            equipment={"WEAPON": "iron_blade", "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None},
            is_mc=True,
        )

        template = game_data.enemies["giga_slime"]
        enemy = engine.create_enemy_instance(template, enemy_level=33, instance_id="giga_slime_0")
        # Set HP to 1 and max_hp to 1 so regen_enhanced doesn't heal (0 missing HP)
        enemy = enemy.model_copy(update={"current_hp": 1, "max_hp": 1})

        state = engine.initialize_combat([player], [enemy])

        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=player.id,
                    ability_id="basic_attack",
                    target_ids=["giga_slime_0"],
                ),
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # Giga should be dead (removed by mitosis)
        giga = state.get_combatant("giga_slime_0")
        assert giga is not None
        assert not giga.is_alive

        # Mitosis passive should have fired, not a DEATH event
        passive_events = [
            e for e in state.log
            if e.event_type == CombatEventType.PASSIVE_TRIGGERED
            and e.ability_id == "giga_mitosis"
        ]
        assert len(passive_events) == 1

        death_events = [
            e for e in state.log
            if e.event_type == CombatEventType.DEATH
            and e.target_id == "giga_slime_0"
        ]
        assert len(death_events) == 0

        # 3 mini-bosses should have spawned (one of each template)
        spawn_events = [e for e in state.log if e.event_type == CombatEventType.ENEMY_SPAWNED]
        assert len(spawn_events) == 3
        spawned_templates = {e.details["template_id"] for e in spawn_events}
        assert spawned_templates == {"slime_brute_miniboss", "slime_caster_miniboss", "slime_tank_miniboss"}

        # Mini-bosses should be alive in combatant list
        alive_minis = [
            c for c in state.enemy_combatants
            if c.is_alive and c.id.startswith("slime_") and "miniboss" in c.id
        ]
        assert len(alive_minis) == 3
