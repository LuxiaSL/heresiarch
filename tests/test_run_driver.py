"""Smoke tests for the policy run driver."""

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.policy.builtin.default_macro import DefaultMacroPolicy
from heresiarch.policy.builtin.floor import FloorCombatPolicy
from heresiarch.policy.protocols import RunResult
from heresiarch.tools.run_driver import simulate_run
from heresiarch.tools.run_report import summarize


@pytest.mark.parametrize("job_id", ["einherjar", "onmyoji", "martyr", "berserker", "sacrist"])
def test_floor_policy_runs_without_crashing(game_data: GameData, job_id: str):
    """Every starter job should complete a floor-policy run without raising."""
    result = simulate_run(
        mc_job_id=job_id,
        combat_policy=FloorCombatPolicy(),
        macro_policy=DefaultMacroPolicy(),
        seed=0,
        max_encounters=50,
        game_data=game_data,
    )
    assert isinstance(result, RunResult)
    assert result.mc_job_id == job_id
    assert result.combat_policy_name == "floor"
    assert result.macro_policy_name == "default_macro"
    assert result.termination_reason in {
        "dead", "max_encounters", "no_available_zones", "clean_exit",
    }
    # Sanity: metrics aren't wildly negative / inconsistent
    assert result.encounters_cleared >= 0
    assert result.rounds_taken_total >= 0
    assert result.final_gold >= 0


def test_floor_policy_is_deterministic(game_data: GameData):
    """Same seed + policies must produce identical results."""
    r1 = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=DefaultMacroPolicy(),
        seed=123,
        max_encounters=30,
        game_data=game_data,
    )
    r2 = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=DefaultMacroPolicy(),
        seed=123,
        max_encounters=30,
        game_data=game_data,
    )
    # Compare every observable field except embedded rule_trace (empty for floor)
    assert r1.is_dead == r2.is_dead
    assert r1.zones_cleared == r2.zones_cleared
    assert r1.farthest_zone == r2.farthest_zone
    assert r1.encounters_cleared == r2.encounters_cleared
    assert r1.rounds_taken_total == r2.rounds_taken_total
    assert r1.final_mc_level == r2.final_mc_level
    assert r1.final_gold == r2.final_gold
    assert r1.killed_by == r2.killed_by
    assert r1.killed_at_zone == r2.killed_at_zone


def test_different_seeds_diverge(game_data: GameData):
    """Different seeds should almost always produce different outcomes."""
    results = [
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=FloorCombatPolicy(),
            macro_policy=DefaultMacroPolicy(),
            seed=seed,
            max_encounters=30,
            game_data=game_data,
        )
        for seed in range(10)
    ]
    # At least some distinct round totals across 10 seeds.
    distinct_rounds = {r.rounds_taken_total for r in results}
    assert len(distinct_rounds) > 1


def test_summary_aggregates_correctly(game_data: GameData):
    results = [
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=FloorCombatPolicy(),
            macro_policy=DefaultMacroPolicy(),
            seed=seed,
            max_encounters=30,
            game_data=game_data,
        )
        for seed in range(10)
    ]
    s = summarize(results)
    assert s.n_runs == 10
    assert s.n_wins + s.n_deaths == 10
    assert 0.0 <= s.win_rate <= 1.0
    assert s.mc_job_id == "einherjar"
    assert s.combat_policy_name == "floor"


def test_unknown_job_raises(game_data: GameData):
    with pytest.raises(ValueError, match="Unknown job"):
        simulate_run(
            mc_job_id="not_a_job",
            combat_policy=FloorCombatPolicy(),
            macro_policy=DefaultMacroPolicy(),
            seed=0,
            game_data=game_data,
        )


def test_max_encounters_bounds_run(game_data: GameData):
    """If we cap encounters low, alive runs should terminate via max_encounters."""
    # Use a job with some resilience so we survive to the cap.
    result = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=DefaultMacroPolicy(),
        seed=42,
        max_encounters=2,
        game_data=game_data,
    )
    assert result.encounters_cleared <= 2
    # Either died or hit the cap — nothing else is possible this early.
    assert result.termination_reason in {"dead", "max_encounters", "no_available_zones"}
