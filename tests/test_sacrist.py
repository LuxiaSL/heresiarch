"""Tests for the Sacrist job and its Communion innate.

Covers:
- Job loads from YAML with expected stats/innate/unlocks
- Communion multiplier formula (edges and midpoints)
- Self-damage abilities apply self-damage
- Communion amplifies magical damage proportional to missing HP
- Communion does NOT amplify physical damage
- Chained self-damage casts compound via Communion
"""

from __future__ import annotations

import random

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    COMMUNION_MAX_BONUS,
    COMMUNION_RAMP_KNEE,
    calculate_communion_multiplier,
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.models.abilities import TriggerCondition
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    PlayerTurnDecision,
)
from heresiarch.engine.models.jobs import CharacterInstance


def _make_sacrist(
    game_data: GameData, level: int, abilities: list[str] | None = None,
    weapon_id: str | None = "spirit_lens",
) -> CharacterInstance:
    """Build a leveled Sacrist with an explicit ability list (includes innate by default)."""
    job = game_data.jobs["sacrist"]
    stats = calculate_stats_at_level(job.growth, level)
    equipment = {"WEAPON": weapon_id, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None}
    equipped_items = []
    if weapon_id and weapon_id in game_data.items:
        equipped_items.append(game_data.items[weapon_id])
    effective = calculate_effective_stats(stats, equipped_items, [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, effective.DEF)
    ability_ids = abilities if abilities is not None else ["basic_attack", job.innate_ability_id]
    return CharacterInstance(
        id="sacrist_test",
        name=job.name,
        job_id="sacrist",
        level=level,
        base_stats=stats,
        effective_stats=effective,
        max_hp=max_hp,
        equipment=equipment,
        current_hp=max_hp,
        abilities=ability_ids,
    )


# --- YAML / Data Loading ---


class TestSacristData:
    def test_job_loads(self, game_data: GameData):
        job = game_data.jobs["sacrist"]
        assert job.name == "Sacrist"
        assert job.origin == "Abrahamic"
        assert job.innate_ability_id == "communion"
        # Stat budget is 10 like other jobs
        total = job.growth.STR + job.growth.MAG + job.growth.DEF + job.growth.RES + job.growth.SPD
        assert total == 10
        # MAG/SPD heavy
        assert job.growth.MAG >= 4
        assert job.growth.SPD >= 4

    def test_communion_ability_loads(self, game_data: GameData):
        communion = game_data.abilities["communion"]
        assert communion.is_innate is True
        assert communion.trigger == TriggerCondition.ON_DAMAGE_MODIFY
        assert len(communion.effects) == 1
        assert communion.effects[0].missing_hp_damage_bonus == 1.0

    def test_sacrist_abilities_exist(self, game_data: GameData):
        for aid in ("litany", "sanguine_rite", "crown_of_thorns", "passion"):
            assert aid in game_data.abilities, f"missing ability: {aid}"

    def test_unlocks_at_expected_levels(self, game_data: GameData):
        unlocks = {u.level: u.ability_id for u in game_data.jobs["sacrist"].ability_unlocks}
        assert unlocks[1] == "litany"
        assert unlocks[4] == "sanguine_rite"
        assert unlocks[8] == "crown_of_thorns"
        assert unlocks[13] == "passion"


# --- Formula ---


class TestCommunionFormula:
    def test_full_hp_no_bonus(self):
        assert calculate_communion_multiplier(100, 100) == 1.0

    def test_knee_hp_reaches_max_bonus(self):
        # 50% missing HP (the default knee) should hit max bonus exactly.
        knee_hp = int(100 * (1.0 - COMMUNION_RAMP_KNEE))
        mult = calculate_communion_multiplier(knee_hp, 100)
        assert abs(mult - (1.0 + COMMUNION_MAX_BONUS)) < 1e-9

    def test_below_knee_clamped_to_max(self):
        # 1 HP is well past the knee — should still be capped at max_bonus.
        mult = calculate_communion_multiplier(1, 100)
        assert abs(mult - (1.0 + COMMUNION_MAX_BONUS)) < 1e-9

    def test_quarter_missing_gives_half_of_max_bonus(self):
        # 25% missing = halfway through a 50% knee = half of max_bonus
        mult = calculate_communion_multiplier(75, 100)
        expected = 1.0 + 0.5 * COMMUNION_MAX_BONUS
        assert abs(mult - expected) < 1e-9

    def test_ramp_is_steeper_pre_knee_than_default_linear(self):
        # Front-loaded: at 10% missing we get 20% of max_bonus (knee=0.5),
        # which is double the old linear ramp's 10% of max_bonus.
        mult = calculate_communion_multiplier(90, 100)
        expected = 1.0 + (0.1 / COMMUNION_RAMP_KNEE) * COMMUNION_MAX_BONUS
        assert abs(mult - expected) < 1e-9

    def test_downed_clamped_to_full_bonus(self):
        # Negative HP (shouldn't happen in practice) clamps to max bonus.
        mult = calculate_communion_multiplier(-5, 100)
        assert mult == 1.0 + COMMUNION_MAX_BONUS

    def test_overheal_clamped_to_no_bonus(self):
        mult = calculate_communion_multiplier(150, 100)
        assert mult == 1.0

    def test_zero_max_hp_safe(self):
        assert calculate_communion_multiplier(0, 0) == 1.0


# --- Combat Behavior ---


class TestCommunionInCombat:
    def test_self_damage_applies(
        self, combat_engine: CombatEngine, game_data: GameData,
    ):
        """Sanguine Rite should emit a self-damage event of ~15% max HP."""
        sacrist = _make_sacrist(game_data, level=8, abilities=["basic_attack", "communion", "sanguine_rite"])
        template = game_data.enemies["fodder_slime"]
        enemy = combat_engine.create_enemy_instance(template, enemy_level=5)

        state = combat_engine.initialize_combat([sacrist], [enemy])
        max_hp = state.player_combatants[0].max_hp
        expected_self_damage = int(max_hp * 0.15)

        decisions = {
            sacrist.id: PlayerTurnDecision(
                combatant_id=sacrist.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist.id,
                    ability_id="sanguine_rite",
                    target_ids=[state.enemy_combatants[0].id],
                ),
            )
        }
        state = combat_engine.process_round(state, decisions, game_data.enemies)

        # Isolate self-damage events (Sacrist may act twice in one round via speed bonus)
        self_damage_events = [
            e for e in state.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist.id
            and e.target_id == sacrist.id
            and e.details.get("self_damage")
        ]
        assert len(self_damage_events) >= 1
        # Each self-damage event should be 15% of max HP
        for ev in self_damage_events:
            assert ev.value == expected_self_damage

    def test_communion_amplifies_magical_at_low_hp(
        self, combat_engine: CombatEngine, game_data: GameData,
    ):
        """Litany should deal more damage at 50% HP than at full HP."""
        # Use a high-HP dummy target so we can see the full damage roll
        template = game_data.enemies["brute_oni"]

        # Run A: full HP
        sacrist_full = _make_sacrist(game_data, level=10, abilities=["basic_attack", "communion", "litany"])
        enemy_a = combat_engine.create_enemy_instance(template, enemy_level=10)
        state_a = combat_engine.initialize_combat([sacrist_full], [enemy_a])
        decisions_a = {
            sacrist_full.id: PlayerTurnDecision(
                combatant_id=sacrist_full.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist_full.id,
                    ability_id="litany",
                    target_ids=[state_a.enemy_combatants[0].id],
                ),
            )
        }
        state_a = combat_engine.process_round(state_a, decisions_a, game_data.enemies)
        dmg_events_a = [
            e for e in state_a.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist_full.id
            and not e.details.get("self_damage")
        ]
        damage_full_hp = dmg_events_a[0].value

        # Run B: half HP
        sacrist_half = _make_sacrist(game_data, level=10, abilities=["basic_attack", "communion", "litany"])
        sacrist_half.current_hp = sacrist_half.max_hp // 2
        enemy_b = combat_engine.create_enemy_instance(template, enemy_level=10)
        state_b = combat_engine.initialize_combat([sacrist_half], [enemy_b])
        decisions_b = {
            sacrist_half.id: PlayerTurnDecision(
                combatant_id=sacrist_half.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist_half.id,
                    ability_id="litany",
                    target_ids=[state_b.enemy_combatants[0].id],
                ),
            )
        }
        state_b = combat_engine.process_round(state_b, decisions_b, game_data.enemies)
        dmg_events_b = [
            e for e in state_b.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist_half.id
            and not e.details.get("self_damage")
        ]
        damage_half_hp = dmg_events_b[0].value

        # With knee at 50% missing HP, being at 50% HP = 50% missing = full max_bonus.
        # Expected multiplier = 1.0 + COMMUNION_MAX_BONUS = 2.0.
        expected = int(damage_full_hp * (1.0 + COMMUNION_MAX_BONUS))
        # Allow ±3 damage for int rounding jitter through the damage pipeline
        assert abs(damage_half_hp - expected) <= 3, (
            f"damage_full_hp={damage_full_hp}, damage_half_hp={damage_half_hp}, expected~{expected}"
        )

    def test_communion_does_not_amplify_physical(
        self, combat_engine: CombatEngine, game_data: GameData,
    ):
        """Basic attack (STR-scaling) should NOT be amplified by Communion."""
        template = game_data.enemies["fodder_slime"]

        # Run A: full HP with Communion, physical ability
        sacrist_full = _make_sacrist(game_data, level=10, abilities=["basic_attack", "communion"])
        enemy_a = combat_engine.create_enemy_instance(template, enemy_level=10)
        state_a = combat_engine.initialize_combat([sacrist_full], [enemy_a])
        decisions_a = {
            sacrist_full.id: PlayerTurnDecision(
                combatant_id=sacrist_full.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist_full.id,
                    ability_id="basic_attack",
                    target_ids=[state_a.enemy_combatants[0].id],
                ),
            )
        }
        state_a = combat_engine.process_round(state_a, decisions_a, game_data.enemies)
        dmg_a = [
            e for e in state_a.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist_full.id
        ][0].value

        # Run B: 1 HP (maximum Communion bonus), same physical ability
        sacrist_low = _make_sacrist(game_data, level=10, abilities=["basic_attack", "communion"])
        sacrist_low.current_hp = 1
        enemy_b = combat_engine.create_enemy_instance(template, enemy_level=10)
        state_b = combat_engine.initialize_combat([sacrist_low], [enemy_b])
        decisions_b = {
            sacrist_low.id: PlayerTurnDecision(
                combatant_id=sacrist_low.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist_low.id,
                    ability_id="basic_attack",
                    target_ids=[state_b.enemy_combatants[0].id],
                ),
            )
        }
        state_b = combat_engine.process_round(state_b, decisions_b, game_data.enemies)
        dmg_b = [
            e for e in state_b.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist_low.id
        ][0].value

        # Physical damage should be identical regardless of HP
        assert dmg_a == dmg_b

    def test_passion_chain_compounds_via_communion(
        self, combat_engine: CombatEngine, game_data: GameData,
    ):
        """Passion cast twice: second cast should be stronger than first, because
        the first self-damage raised Communion's missing-HP bonus for the second.
        """
        template = game_data.enemies["brute_oni"]
        sacrist = _make_sacrist(
            game_data, level=13,
            abilities=["basic_attack", "communion", "passion"],
        )
        # Boost HP so the Sacrist survives two Passion casts (2 * 35% = 70%)
        enemy = combat_engine.create_enemy_instance(template, enemy_level=13)
        state = combat_engine.initialize_combat([sacrist], [enemy])

        # Cast 1
        state = combat_engine.process_round(
            state,
            {sacrist.id: PlayerTurnDecision(
                combatant_id=sacrist.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist.id,
                    ability_id="passion",
                    target_ids=[state.enemy_combatants[0].id],
                ),
            )},
            game_data.enemies,
        )
        passion_events = [
            e for e in state.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist.id
            and not e.details.get("self_damage")
            and e.ability_id == "passion"
        ]
        first_cast = passion_events[0].value

        # Re-heal the enemy to a huge HP pool so it survives and we can land cast 2
        state.enemy_combatants[0].current_hp = 10_000
        state.enemy_combatants[0].max_hp = 10_000

        # Cast 2 (now at ~65% HP)
        state = combat_engine.process_round(
            state,
            {sacrist.id: PlayerTurnDecision(
                combatant_id=sacrist.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=sacrist.id,
                    ability_id="passion",
                    target_ids=[state.enemy_combatants[0].id],
                ),
            )},
            game_data.enemies,
        )
        passion_events_2 = [
            e for e in state.log
            if e.event_type == CombatEventType.DAMAGE_DEALT
            and e.actor_id == sacrist.id
            and not e.details.get("self_damage")
            and e.ability_id == "passion"
        ]
        second_cast = passion_events_2[-1].value

        assert second_cast > first_cast, (
            f"Communion should amplify the second cast (missing HP higher). "
            f"first={first_cast}, second={second_cast}"
        )
