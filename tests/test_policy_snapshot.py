"""Snapshot/restore roundtrip equivalence tests."""

import random


from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    PlayerTurnDecision,
)
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.policy.snapshot import CombatSnapshot, RunSnapshot


def _make_char(gd: GameData, job_id: str = "einherjar", level: int = 5) -> CharacterInstance:
    job = gd.jobs[job_id]
    stats = calculate_stats_at_level(job.growth, level)
    effective = calculate_effective_stats(stats, [], [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, effective.DEF)
    return CharacterInstance(
        id=f"{job_id}_test",
        name=job.name,
        job_id=job_id,
        level=level,
        base_stats=stats,
        effective_stats=effective,
        max_hp=max_hp,
        current_hp=max_hp,
        abilities=["basic_attack", job.innate_ability_id],
    )


def _run_rounds(engine: CombatEngine, state, n: int, char_id: str, gd: GameData):
    for _ in range(n):
        if state.is_finished:
            break
        targets = [e.id for e in state.living_enemies][:1]
        decision = PlayerTurnDecision(
            combatant_id=char_id,
            cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=CombatAction(
                actor_id=char_id, ability_id="basic_attack", target_ids=targets,
            ),
        )
        state = engine.process_round(state, {char_id: decision}, gd.enemies)
    return state


def _state_signature(state) -> tuple:
    """Observable state reduced to something comparable across roundtrips."""
    return (
        state.round_number,
        state.is_finished,
        state.player_won,
        len(state.log),
        tuple((c.id, c.current_hp, c.is_alive) for c in state.all_combatants),
    )


def test_combat_state_roundtrip_equivalence(game_data: GameData):
    """3 rounds + snapshot + 3 rounds == 6 rounds unbroken."""
    # Unbroken path
    rng_a = random.Random(42)
    eng_a = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng_a,
        enemy_registry=game_data.enemies,
    )
    char_a = _make_char(game_data)
    enemies_a = [
        eng_a.create_enemy_instance(game_data.enemies["fodder_slime"], 5),
        eng_a.create_enemy_instance(game_data.enemies["fodder_slime"], 5),
    ]
    state_a = eng_a.initialize_combat([char_a], enemies_a)
    char_id = state_a.player_combatants[0].id
    state_a = _run_rounds(eng_a, state_a, 6, char_id, game_data)

    # Snapshot path
    rng_b = random.Random(42)
    eng_b = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng_b,
        enemy_registry=game_data.enemies,
    )
    char_b = _make_char(game_data)
    enemies_b = [
        eng_b.create_enemy_instance(game_data.enemies["fodder_slime"], 5),
        eng_b.create_enemy_instance(game_data.enemies["fodder_slime"], 5),
    ]
    state_b = eng_b.initialize_combat([char_b], enemies_b)
    state_b = _run_rounds(eng_b, state_b, 3, char_id, game_data)

    snap = CombatSnapshot.take(state_b, rng_b)
    state_b, rng_b_restored = snap.restore()

    eng_b_restored = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng_b_restored,
        enemy_registry=game_data.enemies,
    )
    state_b = _run_rounds(eng_b_restored, state_b, 3, char_id, game_data)

    assert _state_signature(state_a) == _state_signature(state_b)


def test_run_state_roundtrip_equivalence(game_data: GameData):
    """RunSnapshot take/restore yields an engine-equivalent run."""
    rng = random.Random(7)
    gl = GameLoop(game_data=game_data, rng=rng)
    run = gl.new_run("test_roundtrip", "mc", "einherjar")
    run = gl.enter_zone(run, "zone_01")

    snap = RunSnapshot.take(run, rng)
    restored_run, restored_rng = snap.restore(game_loop=gl)

    # Core invariants
    assert restored_run.run_id == run.run_id
    assert restored_run.current_zone_id == run.current_zone_id
    assert restored_run.is_dead == run.is_dead
    assert restored_run.party.money == run.party.money
    assert list(restored_run.party.active) == list(run.party.active)

    # MC identity preserved
    mc_orig = next(c for c in run.party.characters.values() if c.is_mc)
    mc_restored = next(
        c for c in restored_run.party.characters.values() if c.is_mc
    )
    assert mc_orig.job_id == mc_restored.job_id
    assert mc_orig.level == mc_restored.level
    assert mc_orig.current_hp == mc_restored.current_hp
    assert mc_orig.max_hp == mc_restored.max_hp
    assert mc_orig.abilities == mc_restored.abilities

    # RNG roundtrip — same sequence of draws after restore.
    post_snapshot_draws = [rng.random() for _ in range(5)]
    post_restore_draws = [restored_rng.random() for _ in range(5)]
    assert post_snapshot_draws == post_restore_draws


def test_run_snapshot_is_independent_of_original(game_data: GameData):
    """Mutating the original run shouldn't change the snapshot."""
    rng = random.Random(1)
    gl = GameLoop(game_data=game_data, rng=rng)
    run = gl.new_run("test_indep", "mc", "berserker")

    snap = RunSnapshot.take(run, rng)

    # Mutate run state
    run = gl.enter_zone(run, "zone_01")

    restored, _ = snap.restore(game_loop=gl)
    assert restored.current_zone_id is None
    assert run.current_zone_id == "zone_01"
