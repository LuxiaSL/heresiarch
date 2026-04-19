"""Floor+ combat policy: survive→cheat-3→potion-at-low-HP priority stack."""


from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.combat_state import CheatSurviveChoice
from heresiarch.policy.builtin.floor_plus import (
    FloorPlusCombatPolicy,
    FloorPlusMacroPolicy,
)
from heresiarch.policy.protocols import LegalActionSet
from heresiarch.policy.validation import compute_legal
from heresiarch.tools.run_driver import simulate_run


def _make_legal(actor_id: str, enemies: list[str], stash: list[str]) -> LegalActionSet:
    return LegalActionSet(
        actor_id=actor_id,
        living_enemy_ids=enemies,
        available_consumable_ids=stash,
    )


def test_floor_plus_survives_when_ap_below_threshold(game_data: GameData, einherjar_lv15):
    state_actor, combat_engine_state = _make_state(game_data, einherjar_lv15)
    actor = combat_engine_state.player_combatants[0]
    actor.action_points = 0
    actor.current_hp = actor.max_hp  # healthy
    policy = FloorPlusCombatPolicy()
    legal = compute_legal(combat_engine_state, actor, stash=[])
    decision = policy.decide(combat_engine_state, actor, legal)
    assert decision.cheat_survive == CheatSurviveChoice.SURVIVE
    assert decision.primary_action is None


def test_floor_plus_cheats_when_ap_at_threshold(game_data: GameData, einherjar_lv15):
    state_actor, combat_engine_state = _make_state(game_data, einherjar_lv15)
    actor = combat_engine_state.player_combatants[0]
    actor.action_points = 3
    actor.current_hp = actor.max_hp
    policy = FloorPlusCombatPolicy()
    legal = compute_legal(combat_engine_state, actor, stash=[])
    decision = policy.decide(combat_engine_state, actor, legal)
    assert decision.cheat_survive == CheatSurviveChoice.CHEAT
    assert decision.cheat_actions == 3
    assert decision.primary_action is not None
    assert decision.primary_action.ability_id == "basic_attack"
    assert len(decision.cheat_extra_actions) == 3


def test_floor_plus_potion_overrides_cheat_when_hp_low(
    game_data: GameData, einherjar_lv15,
):
    state_actor, combat_engine_state = _make_state(game_data, einherjar_lv15)
    actor = combat_engine_state.player_combatants[0]
    actor.action_points = 3  # enough for cheat
    actor.current_hp = int(actor.max_hp * 0.3)  # below 50%
    policy = FloorPlusCombatPolicy()
    legal = compute_legal(
        combat_engine_state, actor, stash=["minor_potion"],
    )
    decision = policy.decide(combat_engine_state, actor, legal)
    assert decision.cheat_survive == CheatSurviveChoice.NORMAL
    assert decision.primary_action is not None
    assert decision.primary_action.ability_id == "use_item"
    assert decision.primary_action.item_id == "minor_potion"
    assert decision.primary_action.target_ids == [actor.id]


def test_floor_plus_no_potion_falls_back_to_cheat(
    game_data: GameData, einherjar_lv15,
):
    """HP low but stash empty — policy can't potion, falls through to cheat."""
    state_actor, combat_engine_state = _make_state(game_data, einherjar_lv15)
    actor = combat_engine_state.player_combatants[0]
    actor.action_points = 3
    actor.current_hp = int(actor.max_hp * 0.3)
    policy = FloorPlusCombatPolicy()
    legal = compute_legal(combat_engine_state, actor, stash=[])  # no potions
    decision = policy.decide(combat_engine_state, actor, legal)
    # Falls through to cheat (no potion to use).
    assert decision.cheat_survive == CheatSurviveChoice.CHEAT


def test_floor_plus_end_to_end_vs_floor(game_data: GameData):
    """Floor+ should consistently do at least as well as floor on the same seeds.

    Gate on aggregate behavior — floor+ should have mean encounters_cleared
    strictly greater than floor for at least some jobs at n=20.
    """
    from heresiarch.policy.builtin.default_macro import DefaultMacroPolicy
    from heresiarch.policy.builtin.floor import FloorCombatPolicy

    floor_combat = FloorCombatPolicy()
    floor_macro = DefaultMacroPolicy()
    fp_combat = FloorPlusCombatPolicy()
    fp_macro = FloorPlusMacroPolicy()

    floor_encs: list[int] = []
    fp_encs: list[int] = []

    for seed in range(20):
        floor_encs.append(
            simulate_run(
                mc_job_id="einherjar",
                combat_policy=floor_combat,
                macro_policy=floor_macro,
                seed=seed,
                max_encounters=50,
                game_data=game_data,
            ).encounters_cleared
        )
        fp_encs.append(
            simulate_run(
                mc_job_id="einherjar",
                combat_policy=fp_combat,
                macro_policy=fp_macro,
                seed=seed,
                max_encounters=50,
                game_data=game_data,
            ).encounters_cleared
        )

    # Floor+ should average strictly more encounters than floor on einherjar.
    assert sum(fp_encs) > sum(floor_encs), (
        f"floor+ mean {sum(fp_encs)/20:.2f} vs floor {sum(floor_encs)/20:.2f}"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(game_data: GameData, char):
    """Build a minimal combat state with one enemy for policy decision tests."""
    import random
    from heresiarch.engine.combat import CombatEngine

    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=random.Random(42),
        enemy_registry=game_data.enemies,
    )
    enemy = engine.create_enemy_instance(game_data.enemies["fodder_slime"], 5)
    state = engine.initialize_combat([char], [enemy])
    return engine, state
