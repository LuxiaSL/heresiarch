"""Tests for regen passive and charge-up (windup) mechanics."""

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
    """Create a test character at given level with optional weapon."""
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


class TestRegenPassive:
    def test_regen_heals_missing_hp(self, game_data: GameData) -> None:
        """Regen (weak) should heal 2.5% of missing HP at turn start."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
        )

        # Create Omega Slime (has regen passive)
        template = game_data.enemies["omega_slime"]
        enemy = engine.create_enemy_instance(template, enemy_level=5, instance_id="omega_slime_0")

        # Create player
        player = _make_character(game_data, "einherjar", 5, "iron_blade")

        state = engine.initialize_combat([player], [enemy])

        # Damage the omega slime to 50% HP
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        original_max = omega.max_hp
        omega.current_hp = original_max // 2
        missing_before = original_max - omega.current_hp

        # Process a round — regen should fire at turn start
        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=player.id,
                    ability_id="basic_attack",
                    target_ids=["omega_slime_0"],
                ),
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # Check for healing event from regen_weak
        heal_events = [
            e for e in state.log
            if e.event_type == CombatEventType.HEALING
            and e.ability_id == "regen_weak"
        ]
        assert len(heal_events) > 0, "Regen (weak) should have triggered"
        expected_heal = int(missing_before * 0.025)
        assert heal_events[0].value == expected_heal

    def test_regen_does_nothing_at_full_hp(self, game_data: GameData) -> None:
        """Regen should not heal when already at full HP."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
        )

        template = game_data.enemies["omega_slime"]
        enemy = engine.create_enemy_instance(template, enemy_level=5, instance_id="omega_slime_0")
        player = _make_character(game_data, "einherjar", 5, "iron_blade")

        state = engine.initialize_combat([player], [enemy])

        # Omega Slime at full HP
        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # No regen healing events (0 missing HP → 0 heal → skipped)
        regen_heals = [
            e for e in state.log
            if e.event_type == CombatEventType.HEALING
            and e.ability_id == "regen_weak"
        ]
        assert len(regen_heals) == 0


class TestChargeUp:
    def test_charge_start_logged(self, game_data: GameData) -> None:
        """When enemy selects a windup ability, CHARGE_START should be logged."""
        # Use a fixed seed where the omega slime selects charge_slam
        rng = random.Random(99)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
        )

        template = game_data.enemies["omega_slime"]
        enemy = engine.create_enemy_instance(template, enemy_level=5, instance_id="omega_slime_0")
        player = _make_character(game_data, "einherjar", 5, "iron_blade")

        state = engine.initialize_combat([player], [enemy])

        # Force the omega slime to select charge_slam by setting pending_action
        from heresiarch.engine.models.combat_state import CombatAction
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        omega.pending_action = CombatAction(
            actor_id="omega_slime_0",
            ability_id="charge_slam",
            target_ids=[player.id],
        )

        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        charge_starts = [e for e in state.log if e.event_type == CombatEventType.CHARGE_START]
        assert len(charge_starts) == 1
        assert charge_starts[0].ability_id == "charge_slam"
        assert charge_starts[0].details["windup_turns"] == 2

        # Omega should be in charging state with 2 turns remaining
        # (charge fires after 2 more turn ticks)
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        assert omega.charging_ability_id == "charge_slam"
        assert omega.charge_turns_remaining == 2

    def test_charge_fires_after_windup(self, game_data: GameData) -> None:
        """A 2-turn windup fires on the 3rd round (start + 2 charge rounds)."""
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
        )

        template = game_data.enemies["omega_slime"]
        enemy = engine.create_enemy_instance(template, enemy_level=5, instance_id="omega_slime_0")
        player = _make_character(game_data, "einherjar", 10, "iron_blade")  # high level to survive
        state = engine.initialize_combat([player], [enemy])

        # Round 1: force charge_slam selection
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        omega.pending_action = CombatAction(
            actor_id="omega_slime_0",
            ability_id="charge_slam",
            target_ids=[player.id],
        )
        decisions = {
            player.id: PlayerTurnDecision(
                combatant_id=player.id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )
        }
        state = engine.process_round(state, decisions, game_data.enemies)

        # After round 1: charge started, 2 turns remaining
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        assert omega.charge_turns_remaining == 2

        # Round 2: charge tick (2 → 1), log CHARGE_CONTINUE
        state = engine.process_round(state, decisions, game_data.enemies)
        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        assert omega.charge_turns_remaining == 1

        charge_continues = [e for e in state.log if e.event_type == CombatEventType.CHARGE_CONTINUE]
        assert len(charge_continues) >= 1

        # Round 3: charge tick (1 → 0), fire! Log CHARGE_RELEASE + DAMAGE_DEALT
        state = engine.process_round(state, decisions, game_data.enemies)

        omega = state.get_combatant("omega_slime_0")
        assert omega is not None
        assert omega.charge_turns_remaining == 0
        assert omega.charging_ability_id is None  # cleared after release

        charge_releases = [e for e in state.log if e.event_type == CombatEventType.CHARGE_RELEASE]
        assert len(charge_releases) >= 1
        assert charge_releases[-1].ability_id == "charge_slam"

        # Player should have taken damage from the charge release
        damage_events = [
            e for e in state.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == "omega_slime_0"
            and e.ability_id == "charge_slam"
        ]
        assert len(damage_events) >= 1, "Charge slam should deal damage when released"

    def test_charge_slam_fast_has_1_turn_windup(self, game_data: GameData) -> None:
        """charge_slam_fast should fire after just 1 windup turn."""
        ability = game_data.abilities["charge_slam_fast"]
        assert ability.windup_turns == 1

        ability_slow = game_data.abilities["charge_slam"]
        assert ability_slow.windup_turns == 2
