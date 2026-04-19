"""Validation layer: illegal decisions get coerced into legal ones."""

import random

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    PlayerTurnDecision,
)
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.policy.validation import (
    ValidationError,
    compute_legal,
    resolve_decision,
)


def _init_combat(game_data: GameData, seeded_rng: random.Random):
    job = game_data.jobs["einherjar"]
    stats = calculate_stats_at_level(job.growth, 5)
    effective = calculate_effective_stats(stats, [], [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, 5, effective.DEF)
    char = CharacterInstance(
        id="einherjar_t",
        name=job.name,
        job_id="einherjar",
        level=5,
        base_stats=stats,
        effective_stats=effective,
        max_hp=max_hp,
        current_hp=max_hp,
        abilities=["basic_attack", job.innate_ability_id],
    )
    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=seeded_rng,
        enemy_registry=game_data.enemies,
    )
    enemy = engine.create_enemy_instance(game_data.enemies["fodder_slime"], 5)
    state = engine.initialize_combat([char], [enemy])
    return state, engine, char


def test_unknown_ability_raises(game_data: GameData, seeded_rng: random.Random):
    state, engine, char = _init_combat(game_data, seeded_rng)
    actor = state.player_combatants[0]
    decision = PlayerTurnDecision(
        combatant_id=actor.id,
        primary_action=CombatAction(
            actor_id=actor.id,
            ability_id="does_not_exist",
            target_ids=[state.living_enemies[0].id],
        ),
    )
    with pytest.raises(ValidationError):
        resolve_decision(decision, state, actor, game_data.abilities)


def test_dead_target_retargets(game_data: GameData, seeded_rng: random.Random):
    state, engine, _char = _init_combat(game_data, seeded_rng)
    actor = state.player_combatants[0]
    # Kill the enemy off-graph — simulate a target-gone scenario.
    enemy = state.enemy_combatants[0]
    enemy.current_hp = 0
    enemy.is_alive = False
    # Add a second live enemy so retargeting has something to aim at.
    new_enemy = engine.create_enemy_instance(game_data.enemies["fodder_slime"], 5)
    state.enemy_combatants.append(
        state.enemy_combatants[0].model_copy(update={
            "id": "fodder_slime_backup",
            "current_hp": new_enemy.max_hp,
            "max_hp": new_enemy.max_hp,
            "is_alive": True,
        })
    )
    decision = PlayerTurnDecision(
        combatant_id=actor.id,
        primary_action=CombatAction(
            actor_id=actor.id,
            ability_id="basic_attack",
            target_ids=[enemy.id],  # dead target
        ),
    )
    fixed, issues = resolve_decision(decision, state, actor, game_data.abilities)
    assert fixed.primary_action is not None
    assert fixed.primary_action.target_ids == ["fodder_slime_backup"]
    assert any(i.kind == "dead_target_retarget" for i in issues)


def test_ap_downgrade_on_over_spend(game_data: GameData, seeded_rng: random.Random):
    state, _engine, _char = _init_combat(game_data, seeded_rng)
    actor = state.player_combatants[0]
    actor.action_points = 1
    decision = PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.CHEAT,
        cheat_actions=5,
        primary_action=CombatAction(
            actor_id=actor.id,
            ability_id="basic_attack",
            target_ids=[state.living_enemies[0].id],
        ),
        cheat_extra_actions=[
            CombatAction(
                actor_id=actor.id,
                ability_id="basic_attack",
                target_ids=[state.living_enemies[0].id],
            )
            for _ in range(5)
        ],
    )
    fixed, issues = resolve_decision(decision, state, actor, game_data.abilities)
    assert fixed.cheat_actions == 1
    assert len(fixed.cheat_extra_actions) == 1
    assert any(i.kind == "ap_downgrade" for i in issues)


def test_survive_passes_through_unchanged(
    game_data: GameData, seeded_rng: random.Random,
):
    state, _engine, _char = _init_combat(game_data, seeded_rng)
    actor = state.player_combatants[0]
    decision = PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
    )
    fixed, issues = resolve_decision(decision, state, actor, game_data.abilities)
    assert fixed.cheat_survive == CheatSurviveChoice.SURVIVE
    assert issues == []


def test_compute_legal_reports_cooldowns(
    game_data: GameData, seeded_rng: random.Random,
):
    state, _engine, _char = _init_combat(game_data, seeded_rng)
    actor = state.player_combatants[0]
    actor.cooldowns = {"basic_attack": 2}
    legal = compute_legal(state, actor)
    assert "basic_attack" not in legal.available_ability_ids
    assert legal.cooldowns == {"basic_attack": 2}
