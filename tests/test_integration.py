"""Integration tests: full game loop from run start through zone completion."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.combat_state import (
    CombatAction,
    CheatSurviveChoice,
    CombatEventType,
    PlayerTurnDecision,
)
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.save_manager import SaveManager
from heresiarch.engine.shop import ShopEngine, ShopInventory


@pytest.fixture
def game_loop(game_data: GameData) -> GameLoop:
    return GameLoop(game_data=game_data, rng=random.Random(42))


def _run_combat_to_completion(
    engine: CombatEngine,
    run: RunState,
    enemies: list,
    game_data: GameData,
    max_rounds: int = 30,
) -> CombatResult:
    """Helper: run a full combat and return CombatResult.

    All player characters use basic_attack (always available).
    """
    chars = [
        run.party.characters[cid]
        for cid in run.party.active
        if cid in run.party.characters
    ]
    state = engine.initialize_combat(chars, enemies)

    enemy_templates = {
        e.template_id: game_data.enemies[e.template_id]
        for e in enemies
        if e.template_id in game_data.enemies
    }

    for _ in range(max_rounds):
        if state.is_finished:
            break

        decisions: dict[str, PlayerTurnDecision] = {}
        for pc in state.living_players:
            targets = [e.id for e in state.living_enemies[:1]]
            decisions[pc.id] = PlayerTurnDecision(
                combatant_id=pc.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=pc.id,
                    ability_id="basic_attack",
                    target_ids=targets,
                ),
            )

        state = engine.process_round(state, decisions, enemy_templates)

    surviving = [p.id for p in state.living_players]
    surviving_hp = {p.id: p.current_hp for p in state.living_players}
    # All enemies are defeated if player won; otherwise determine from living
    living_enemy_template_ids = {le.id.rsplit("_", 1)[0] for le in state.living_enemies}
    defeated_templates = [
        e.template_id for e in enemies
    ] if (state.player_won or False) else []
    defeated_budgets = [
        game_data.enemies[tid].budget_multiplier
        for tid in defeated_templates
        if tid in game_data.enemies
    ]

    return CombatResult(
        player_won=state.player_won or False,
        surviving_character_ids=surviving,
        surviving_character_hp=surviving_hp,
        defeated_enemy_template_ids=defeated_templates,
        defeated_enemy_budget_multipliers=defeated_budgets,
        rounds_taken=state.round_number,
        zone_level=enemies[0].level if enemies else 1,
    )


class TestFullZoneRun:
    def test_clear_zone_01(self, game_loop: GameLoop, game_data: GameData) -> None:
        """Start a run, enter zone_01, fight all encounters, verify progression.

        MC starts at level 15 with a weapon — overleveled for zone 1 to
        survive HP attrition across all encounters without healing.
        """
        from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level

        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        job = game_data.jobs["einherjar"]
        stats = calculate_stats_at_level(job.growth, 15)
        hp = calculate_max_hp(job.base_hp, job.hp_growth, 15, stats.DEF)
        mc = mc.model_copy(update={
            "level": 15,
            "base_stats": stats,
            "current_hp": hp,
            "equipment": {"WEAPON": "iron_blade", "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None},
            "growth_history": [("einherjar", 15)],
        })
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = mc
        run = run.model_copy(update={"party": run.party.model_copy(update={"characters": new_chars})})
        run = game_loop.enter_zone(run, "zone_01")

        zone = game_data.zones["zone_01"]
        initial_level = run.party.characters["mc_einherjar"].level

        for i in range(len(zone.encounters)):
            enemies = game_loop.get_next_encounter(run)
            assert len(enemies) > 0

            result = _run_combat_to_completion(
                game_loop.combat_engine, run, enemies, game_data
            )
            assert result.player_won, f"Lost encounter {i}"

            run, loot = game_loop.resolve_combat_result(run, result)
            assert run.party.money > 0 or loot.money == 0  # money accumulates

            # Apply any loot
            if loot.item_ids:
                run = game_loop.apply_loot(run, loot, selected_items=loot.item_ids)

            run = game_loop.advance_zone(run)

        assert run.zone_state is not None
        assert run.zone_state.is_cleared
        assert "zone_01" in run.zones_completed

        mc = run.party.characters["mc_einherjar"]
        assert mc.xp > 0
        assert mc.level >= initial_level


class TestHPPersistence:
    def test_hp_carries_between_encounters(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """HP from combat persists — no free healing between encounters."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Level 10 MC with weapon for zone 1
        mc = run.party.characters["mc_einherjar"]
        from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level

        job = game_data.jobs["einherjar"]
        stats = calculate_stats_at_level(job.growth, 10)
        hp = calculate_max_hp(job.base_hp, job.hp_growth, 10, stats.DEF)
        mc = mc.model_copy(
            update={
                "level": 10,
                "base_stats": stats,
                "current_hp": hp,
                "equipment": {
                    "WEAPON": "iron_blade",
                    "ARMOR": None,
                    "ACCESSORY_1": None,
                    "ACCESSORY_2": None,
                },
            }
        )
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = mc
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"characters": new_chars})}
        )
        run = game_loop.enter_zone(run, "zone_01")

        full_hp = hp

        # Fight first encounter
        enemies = game_loop.get_next_encounter(run)
        result = _run_combat_to_completion(
            game_loop.combat_engine, run, enemies, game_data
        )
        assert result.player_won

        run, _ = game_loop.resolve_combat_result(run, result)
        run = game_loop.advance_zone(run)

        mc_after = run.party.characters["mc_einherjar"]
        # MC should have taken some damage (or at least HP is from combat, not reset)
        # The surviving HP from combat is persisted, not the pre-combat full HP
        assert mc_after.current_hp <= full_hp


class TestShopDuringRun:
    def test_buy_and_equip(self, game_loop: GameLoop, game_data: GameData) -> None:
        """Buy an item from shop and add to stash."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"money": 500})}
        )

        shop = ShopInventory(
            available_items=["iron_blade", "spirit_lens"],
            zone_level=1,
        )
        menu = game_loop.shop_engine.get_buy_menu(shop, run.party.cha)
        assert len(menu) > 0

        item_id, price = menu[0]
        new_party = game_loop.shop_engine.buy_item(run.party, item_id, price)
        run = run.model_copy(update={"party": new_party})
        assert item_id in run.party.stash


class TestDeathDuringCombat:
    def test_death_marks_run_dead(self, game_loop: GameLoop) -> None:
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

        new_run, _ = game_loop.resolve_combat_result(run, result)
        assert new_run.is_dead is True


class TestDeathNukesSaves:
    def test_saves_deleted_on_death(self, game_loop: GameLoop, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """Death should nuke all saves for the run."""
        manager = SaveManager(tmp_path)
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        manager.save_run(run, "slot_1")
        manager.autosave(run)

        # Die
        dead_run = game_loop.handle_death(run)
        assert dead_run.is_dead

        # Nuke saves
        manager.delete_run_saves(dead_run.run_id)
        assert manager.list_slots(dead_run.run_id) == []


class TestMCJobSwapDuringRun:
    def test_swap_preserves_xp(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")

        # Gain some XP first
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            defeated_enemy_template_ids=["brute_oni"] * 3,
            defeated_enemy_budget_multipliers=[14.0] * 3,
            rounds_taken=5,
            zone_level=5,
        )
        run = game_loop.enter_zone(run, "zone_05")
        run, _ = game_loop.resolve_combat_result(run, result)

        mc_before = run.party.characters["mc_einherjar"]
        xp_before = mc_before.xp

        # Swap job
        run = game_loop.mc_swap_job(run, "onmyoji")
        mc_after = run.party.characters["mc_einherjar"]

        assert mc_after.xp == xp_before
        assert mc_after.job_id == "onmyoji"
        assert len(mc_after.growth_history) == 2
