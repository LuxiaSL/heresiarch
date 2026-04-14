"""Tests for the GameLoop orchestrator."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import STASH_LIMIT, GameLoop
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult, RunState


@pytest.fixture
def game_loop(game_data: GameData, seeded_rng: random.Random) -> GameLoop:
    return GameLoop(game_data=game_data, rng=seeded_rng)


class TestNewRun:
    def test_creates_run_with_mc(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        assert run.run_id == "run_001"
        mc = run.party.characters["mc_einherjar"]
        assert mc.name == "Hero"
        assert mc.job_id == "einherjar"
        assert mc.level == 1
        assert mc.is_mc is True
        assert mc.current_hp > 0
        assert "mc_einherjar" in run.party.active

    def test_mc_has_growth_history(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        assert mc.growth_history == [("einherjar", 1)]

    def test_invalid_job_raises(self, game_loop: GameLoop) -> None:
        with pytest.raises(KeyError):
            game_loop.new_run("run_001", "Hero", "nonexistent_job")


class TestEnterZone:
    def test_enter_valid_zone(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        assert run.current_zone_id == "zone_01"
        assert run.zone_state is not None
        assert run.zone_state.current_encounter_index == 0

    def test_enter_invalid_zone(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="Unknown zone"):
            game_loop.enter_zone(run, "nonexistent_zone")


class TestGetNextEncounter:
    def test_generates_enemies(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        enemies = game_loop.get_next_encounter(run)
        assert len(enemies) > 0
        assert all(e.max_hp > 0 for e in enemies)

    def test_not_in_zone_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="Not in a zone"):
            game_loop.get_next_encounter(run)


class TestCombatXPDistribution:
    def test_xp_gained_after_combat(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")

        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            defeated_enemy_template_ids=["fodder_slime", "fodder_slime"],
            defeated_enemy_budget_multipliers=[8.0, 8.0],
            rounds_taken=3,
            zone_level=1,
        )

        new_run, loot = game_loop.resolve_combat_result(run, result)
        mc = new_run.party.characters["mc_einherjar"]
        assert mc.xp > 0  # gained XP

    def test_level_up_from_combat(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_05")

        # Big fight: lots of XP
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            defeated_enemy_template_ids=["brute_oni"] * 5,
            defeated_enemy_budget_multipliers=[14.0] * 5,
            rounds_taken=10,
            zone_level=5,
        )

        new_run, loot = game_loop.resolve_combat_result(run, result)
        mc = new_run.party.characters["mc_einherjar"]
        assert mc.level > 1  # should have leveled up
        assert mc.base_stats.STR > 0

    def test_death_marks_run(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")

        result = CombatResult(
            player_won=False,
            surviving_character_ids=[],
            defeated_enemy_template_ids=[],
            defeated_enemy_budget_multipliers=[],
            rounds_taken=5,
            zone_level=1,
        )

        new_run, loot = game_loop.resolve_combat_result(run, result)
        assert new_run.is_dead is True


class TestLootApplication:
    def test_money_added(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")

        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            defeated_enemy_template_ids=["fodder_slime"],
            defeated_enemy_budget_multipliers=[8.0],
            rounds_taken=2,
            zone_level=1,
        )

        new_run, loot = game_loop.resolve_combat_result(run, result)
        assert new_run.party.money > 0

    def test_items_added_to_stash(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        loot = LootResult(money=0, item_ids=["iron_blade"])
        new_run = game_loop.apply_loot(run, loot, selected_items=["iron_blade"])
        assert "iron_blade" in new_run.party.stash
        assert "iron_blade" in new_run.party.items

    def test_stash_limit_enforced(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Fill stash
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"stash": ["x"] * STASH_LIMIT})}
        )
        loot = LootResult(money=0, item_ids=["iron_blade"])
        new_run = game_loop.apply_loot(run, loot, selected_items=["iron_blade"])
        assert len(new_run.party.stash) == STASH_LIMIT  # didn't add more

    def test_discard_frees_space_for_loot(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Fill stash with iron_blades
        run = run.model_copy(
            update={
                "party": run.party.model_copy(
                    update={"stash": ["iron_blade"] * STASH_LIMIT}
                )
            }
        )
        loot = LootResult(money=0, item_ids=["minor_potion"])
        new_run = game_loop.apply_loot(
            run, loot, selected_items=["minor_potion"], discard_items=["iron_blade"]
        )
        assert len(new_run.party.stash) == STASH_LIMIT  # net size unchanged
        assert "minor_potion" in new_run.party.stash
        # One iron_blade was removed
        assert new_run.party.stash.count("iron_blade") == STASH_LIMIT - 1

    def test_discard_multiple_then_pick_multiple(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = run.model_copy(
            update={
                "party": run.party.model_copy(
                    update={"stash": ["iron_blade"] * STASH_LIMIT}
                )
            }
        )
        loot = LootResult(money=0, item_ids=["minor_potion", "minor_potion"])
        new_run = game_loop.apply_loot(
            run,
            loot,
            selected_items=["minor_potion", "minor_potion"],
            discard_items=["iron_blade", "iron_blade"],
        )
        assert len(new_run.party.stash) == STASH_LIMIT
        assert new_run.party.stash.count("minor_potion") == 2
        assert new_run.party.stash.count("iron_blade") == STASH_LIMIT - 2

    def test_discard_nonexistent_item_is_safe(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        loot = LootResult(money=0, item_ids=["iron_blade"])
        # Discarding something not in stash should not error
        new_run = game_loop.apply_loot(
            run, loot, selected_items=["iron_blade"], discard_items=["nonexistent"]
        )
        assert "iron_blade" in new_run.party.stash


class TestZoneProgression:
    def test_advance_increments_index(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state is not None
        assert run.zone_state.current_encounter_index == 0

        run = game_loop.advance_zone(run)
        assert run.zone_state is not None
        assert run.zone_state.current_encounter_index == 1

    def test_zone_cleared(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        zone = game_data.zones["zone_01"]

        for _ in range(len(zone.encounters)):
            run = game_loop.advance_zone(run)

        assert run.zone_state is not None
        assert run.zone_state.is_cleared is True
        assert "zone_01" in run.zones_completed


class TestAbilityBreakpoints:
    def test_onmyoji_starts_with_bolt(self, game_loop: GameLoop) -> None:
        """Onmyoji has bolt as a Lv1 breakpoint — should have it from the start."""
        run = game_loop.new_run("run_001", "Hero", "onmyoji")
        mc = run.party.characters["mc_onmyoji"]
        assert "bolt" in mc.abilities

    def test_einherjar_no_early_unlocks(self, game_loop: GameLoop) -> None:
        """Einherjar's first breakpoint is Lv3 — nothing extra at Lv1."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        assert mc.abilities == ["basic_attack", "retaliate"]

    def test_level_up_grants_ability(self, game_loop: GameLoop) -> None:
        """Leveling past a breakpoint should grant the ability."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_05")

        # Big XP to level up past 3
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            surviving_character_hp={"mc_einherjar": 100},
            defeated_enemy_template_ids=["brute_oni"] * 5,
            defeated_enemy_budget_multipliers=[14.0] * 5,
            rounds_taken=10,
            zone_level=5,
        )
        new_run, loot = game_loop.resolve_combat_result(run, result)
        mc = new_run.party.characters["mc_einherjar"]
        if mc.level >= 3:
            assert "brace_strike" in mc.abilities

    def test_multiple_unlocks_in_one_levelup(self, game_loop: GameLoop) -> None:
        """Gaining multiple levels should grant all intermediate breakpoints."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]

        # Simulate: check_ability_unlocks from Lv1 to Lv10
        updated = game_loop._check_ability_unlocks(mc, 1, 10)
        # Einherjar gets brace_strike at 3 and thrust at 8
        assert "brace_strike" in updated.abilities
        assert "thrust" in updated.abilities

    def test_no_duplicate_abilities(self, game_loop: GameLoop) -> None:
        """Checking unlocks twice shouldn't add duplicates."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        updated = game_loop._check_ability_unlocks(mc, 1, 5)
        updated = game_loop._check_ability_unlocks(updated, 1, 5)
        assert updated.abilities.count("brace_strike") == 1


class TestMCJobSwap:
    def _add_ally(self, run: RunState, game_loop: GameLoop, job_id: str) -> RunState:
        """Add an ally with the given job to the party for mimic tests."""
        from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level

        job = game_loop.game_data.jobs[job_id]
        stats = calculate_stats_at_level(job.growth, 1)
        ally = CharacterInstance(
            id=f"ally_{job_id}",
            name=f"Ally {job_id}",
            job_id=job_id,
            level=1,
            base_stats=stats,
            current_hp=calculate_max_hp(job.base_hp, job.hp_growth, 1, stats.DEF),
            max_hp=calculate_max_hp(job.base_hp, job.hp_growth, 1, stats.DEF),
            abilities=["basic_attack"],
        )
        new_chars = dict(run.party.characters)
        new_chars[ally.id] = ally
        new_active = list(run.party.active) + [ally.id]
        new_party = run.party.model_copy(
            update={"characters": new_chars, "active": new_active}
        )
        return run.model_copy(update={"party": new_party})

    def test_swap_updates_job(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]
        assert mc.job_id == "berserker"

    def test_swap_updates_growth_history(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]
        assert len(mc.growth_history) == 2
        assert mc.growth_history[-1][0] == "berserker"

    def test_swap_updates_abilities(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "onmyoji")
        run = game_loop.mc_swap_job(run, "onmyoji")
        mc = run.party.characters["mc_einherjar"]
        # Should have onmyoji's innate
        onmyoji = game_loop.game_data.jobs["onmyoji"]
        assert onmyoji.innate_ability_id in mc.abilities

    def test_swap_invalid_job(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="Unknown job"):
            game_loop.mc_swap_job(run, "nonexistent")

    def test_swap_to_current_job_raises(self, game_loop: GameLoop) -> None:
        """MC cannot swap to the job they already have."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "einherjar")
        with pytest.raises(ValueError, match="already has job"):
            game_loop.mc_swap_job(run, "einherjar")

    def test_swap_max_hp_changes(self, game_loop: GameLoop) -> None:
        """Swapping to a job with lower base_hp/hp_growth reduces max_hp.

        Einherjar: base_hp=50, hp_growth=8
        Berserker: base_hp=28, hp_growth=4
        """
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        mc_before = run.party.characters["mc_einherjar"]
        hp_before = mc_before.max_hp

        run = game_loop.mc_swap_job(run, "berserker")
        mc_after = run.party.characters["mc_einherjar"]

        assert mc_after.max_hp < hp_before, (
            f"Expected max_hp to drop: {mc_after.max_hp} should be < {hp_before}"
        )

    def test_swap_caps_current_hp_to_new_max(self, game_loop: GameLoop) -> None:
        """If current_hp exceeds new max_hp, it's capped down."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        mc_before = run.party.characters["mc_einherjar"]
        # MC starts at full HP
        assert mc_before.current_hp == mc_before.max_hp

        run = game_loop.mc_swap_job(run, "berserker")
        mc_after = run.party.characters["mc_einherjar"]

        assert mc_after.current_hp == mc_after.max_hp, (
            f"HP should be capped to new max: {mc_after.current_hp} != {mc_after.max_hp}"
        )
        assert mc_after.current_hp < mc_before.current_hp

    def test_swap_preserves_hp_when_lower(self, game_loop: GameLoop) -> None:
        """If current_hp is already below new max, it's preserved as-is."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "martyr")
        # Martyr has base_hp=70, hp_growth=12 — much higher than einherjar
        mc = run.party.characters["mc_einherjar"]

        # Manually reduce HP to 10
        damaged_mc = mc.model_copy(update={"current_hp": 10})
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = damaged_mc
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"characters": new_chars})}
        )

        run = game_loop.mc_swap_job(run, "martyr")
        mc_after = run.party.characters["mc_einherjar"]
        # HP should stay at 10 since martyr has higher max_hp
        assert mc_after.current_hp == 10

    def test_swap_stats_recalculated_from_history(self, game_loop: GameLoop) -> None:
        """After swap, base_stats reflect the full growth history."""
        from heresiarch.engine.formulas import calculate_stats_from_history

        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]

        # Stats should match what calculate_stats_from_history produces
        expected = calculate_stats_from_history(
            mc.growth_history, game_loop.game_data.jobs
        )
        assert mc.base_stats == expected

    def test_swap_strips_old_innate(self, game_loop: GameLoop) -> None:
        """Old job's innate ability should be removed after swap."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")
        old_innate = game_loop.game_data.jobs["einherjar"].innate_ability_id
        new_innate = game_loop.game_data.jobs["berserker"].innate_ability_id

        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]

        assert new_innate in mc.abilities
        assert old_innate not in mc.abilities

    def test_swap_preserves_scroll_taught_ability(self, game_loop: GameLoop) -> None:
        """Scroll-taught abilities survive job swaps."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "berserker")

        # Add scroll to stash and teach it
        new_stash = list(run.party.stash) + ["scroll_arc_slash"]
        new_party = run.party.model_copy(update={"stash": new_stash})
        run = run.model_copy(update={"party": new_party})
        run = game_loop.use_teach_scroll(run, "scroll_arc_slash", "mc_einherjar")

        mc_before = run.party.characters["mc_einherjar"]
        assert "arc_slash" in mc_before.abilities

        # Swap job — arc_slash should survive
        run = game_loop.mc_swap_job(run, "berserker")
        mc_after = run.party.characters["mc_einherjar"]
        assert "arc_slash" in mc_after.abilities, (
            f"Scroll-taught ability lost after swap. Abilities: {mc_after.abilities}"
        )

    def test_level_up_after_swap_uses_new_growth(self, game_loop: GameLoop) -> None:
        """Leveling up after a job swap applies the new job's growth rates."""
        from heresiarch.engine.formulas import calculate_stats_from_history

        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = self._add_ally(run, game_loop, "onmyoji")
        run = game_loop.mc_swap_job(run, "onmyoji")

        mc_pre_level = run.party.characters["mc_einherjar"]
        assert mc_pre_level.growth_history[-1] == ("onmyoji", 0)

        # Level up via combat result (give enough XP for at least 1 level)
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar", "ally_onmyoji"],
            defeated_enemy_template_ids=["brute_oni"] * 5,
            defeated_enemy_budget_multipliers=[14.0] * 5,
            rounds_taken=5,
            zone_level=5,
        )
        run = game_loop.enter_zone(run, "zone_03")
        run, _ = game_loop.resolve_combat_result(run, result)

        mc_after = run.party.characters["mc_einherjar"]
        # Last history entry should have accumulated levels
        last_job, last_levels = mc_after.growth_history[-1]
        assert last_job == "onmyoji"
        assert last_levels > 0, "Should have gained levels in onmyoji segment"

        # Stats should match full history recalculation
        expected = calculate_stats_from_history(
            mc_after.growth_history, game_loop.game_data.jobs
        )
        assert mc_after.base_stats == expected
