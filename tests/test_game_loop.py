"""Tests for the GameLoop orchestrator."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import STASH_LIMIT, GameLoop
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
        assert mc.growth_history == [("einherjar", 0)]

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


class TestMCJobSwap:
    def test_swap_updates_job(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]
        assert mc.job_id == "berserker"

    def test_swap_updates_growth_history(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.mc_swap_job(run, "berserker")
        mc = run.party.characters["mc_einherjar"]
        assert len(mc.growth_history) == 2
        assert mc.growth_history[-1][0] == "berserker"

    def test_swap_updates_abilities(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.mc_swap_job(run, "onmyoji")
        mc = run.party.characters["mc_einherjar"]
        # Should have onmyoji's innate
        onmyoji = game_loop.game_data.jobs["onmyoji"]
        assert onmyoji.innate_ability_id in mc.abilities

    def test_swap_invalid_job(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="Unknown job"):
            game_loop.mc_swap_job(run, "nonexistent")
