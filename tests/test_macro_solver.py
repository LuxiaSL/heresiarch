"""Tests for the macro solver: delegation, retreat search, integration."""

import random
from pathlib import Path

import pytest

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.game_loop import GameLoop
from heresiarch.policy.builtin.golden_macro import (
    GoldenMacroPolicy,
    _count_potions,
    _mean_party_hp_pct,
    make_golden_macro_einherjar,
)
from heresiarch.policy.macro_solver import (
    MacroSolver,
    MacroSolverConfig,
    make_macro_solver,
)
from heresiarch.policy.solver import CombatSolver, SolverConfig, make_solver


@pytest.fixture
def game_data() -> GameData:
    return load_all(Path("data"))


def _make_macro_solver(
    gd: GameData,
    config: MacroSolverConfig | None = None,
) -> MacroSolver:
    """Helper: build a macro solver with lightweight eval config."""
    solver = make_solver(gd, config=SolverConfig(search_depth=1, prune_after_ply=10))
    base = make_golden_macro_einherjar(gd)
    return MacroSolver(
        game_data=gd,
        combat_policy=solver,
        base_macro=base,
        config=config or MacroSolverConfig(
            eval_solver_depth=1,
            eval_solver_prune=10,
            lookahead_encounters=2,
        ),
    )


# ---------------------------------------------------------------------------
# Delegation tests
# ---------------------------------------------------------------------------


class TestDelegation:
    """Non-searched methods should pass through to the base macro."""

    def test_decide_zone_delegates(self, game_data: GameData):
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        run = gl.new_run("test", "mc", "einherjar")

        zones = gl.get_available_zones(run)
        ms_choice = ms.decide_zone(run, zones)
        base_choice = ms.base_macro.decide_zone(run, zones)
        assert ms_choice == base_choice

    def test_decide_shop_delegates(self, game_data: GameData):
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        run = gl.new_run("test", "mc", "einherjar")

        shop_items = gl.resolve_town_shop(run)
        ms_actions = ms.decide_shop(run, shop_items)
        base_actions = ms.base_macro.decide_shop(run, shop_items)
        assert ms_actions == base_actions

    def test_config_property_exposes_base_config(self, game_data: GameData):
        ms = _make_macro_solver(game_data)
        assert ms.config is ms.base_macro.config
        assert ms.config.heal_threshold_pct == ms.base_macro.config.heal_threshold_pct


# ---------------------------------------------------------------------------
# Retreat search tests
# ---------------------------------------------------------------------------


class TestRetreatSearch:
    def test_skip_when_healthy(self, game_data: GameData):
        """Full-HP party with potions should skip search entirely."""
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        ms.set_game_loop(gl)

        run = gl.new_run("test", "mc", "einherjar")
        # Enter zone so retreat makes sense
        run = gl.enter_zone(run, "zone_01")
        # Give potions
        new_stash = list(run.party.stash) + ["minor_potion", "minor_potion"]
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"stash": new_stash})}
        )

        result = ms.decide_retreat_to_town(run)
        assert result is False
        assert ms.stats.skipped_healthy >= 1

    def test_retreat_when_low_hp_no_potions(self, game_data: GameData):
        """Low-HP party with no potions and gold should trigger search."""
        from heresiarch.engine.models.zone import ZoneState

        ms = _make_macro_solver(game_data, config=MacroSolverConfig(
            eval_solver_depth=1,
            eval_solver_prune=10,
            lookahead_encounters=2,
            skip_retreat_hp_pct=0.99,
            skip_retreat_min_potions=99,
        ))
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        ms.set_game_loop(gl)

        run = gl.new_run("test", "mc", "berserker")
        run = gl.enter_zone(run, "zone_01")

        # Simulate having cleared 1 encounter (anti-loop guard requires it)
        run = run.model_copy(update={
            "zone_state": run.zone_state.model_copy(update={
                "encounters_completed": [0],
                "current_encounter_index": 1,
            }),
        })

        # Damage MC to 20% HP and give gold for potions
        mc_id = run.party.active[0]
        mc = run.party.characters[mc_id]
        low_hp = max(1, mc.max_hp // 5)
        new_mc = mc.model_copy(update={"current_hp": low_hp})
        new_chars = dict(run.party.characters)
        new_chars[mc_id] = new_mc
        run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": new_chars,
                "money": 200,
            }),
        })

        result = ms.decide_retreat_to_town(run)
        assert ms.stats.retreat_searches >= 1

    def test_fallback_when_no_game_loop(self, game_data: GameData):
        """Without set_game_loop, should fall back to base macro."""
        ms = _make_macro_solver(game_data, config=MacroSolverConfig(
            skip_retreat_hp_pct=0.99,
            skip_retreat_min_potions=99,
        ))
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        # Deliberately do NOT call ms.set_game_loop(gl)

        run = gl.new_run("test", "mc", "einherjar")
        run = gl.enter_zone(run, "zone_01")

        # Should not crash — falls back to base macro
        result = ms.decide_retreat_to_town(run)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Branch simulation tests
# ---------------------------------------------------------------------------


class TestBranchSimulation:
    def test_simulate_encounters_returns_count(self, game_data: GameData):
        """Encounter simulation should return a non-negative count."""
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        ms.set_game_loop(gl)

        run = gl.new_run("test", "mc", "einherjar")
        run = gl.enter_zone(run, "zone_01")

        branch_gl = GameLoop(game_data, random.Random(42))
        final_run, survived = ms._simulate_encounters(run, branch_gl, 2)
        assert survived >= 0
        assert final_run is not None

    def test_simulate_retreat_heals(self, game_data: GameData):
        """After simulating a retreat, HP should be higher."""
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        ms.set_game_loop(gl)

        run = gl.new_run("test", "mc", "einherjar")
        run = gl.enter_zone(run, "zone_01")

        mc_id = run.party.active[0]
        mc = run.party.characters[mc_id]
        low_hp = max(1, mc.max_hp // 3)
        new_mc = mc.model_copy(update={"current_hp": low_hp})
        new_chars = dict(run.party.characters)
        new_chars[mc_id] = new_mc
        run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": new_chars,
                "money": 200,
            }),
        })

        branch_gl = GameLoop(game_data, random.Random(99))
        result = ms._simulate_retreat(run, branch_gl)
        assert result is not None
        mc_after = result.party.characters[mc_id]
        assert mc_after.current_hp >= low_hp

    def test_score_branch_rewards_survival(self, game_data: GameData):
        """More survived encounters should give a higher score."""
        ms = _make_macro_solver(game_data)
        rng = random.Random(42)
        gl = GameLoop(game_data, rng)
        run = gl.new_run("test", "mc", "einherjar")

        score_0 = ms._score_branch(run, 0)
        score_3 = ms._score_branch(run, 3)
        assert score_3 > score_0


# ---------------------------------------------------------------------------
# Integration: macro solver through the sim driver
# ---------------------------------------------------------------------------


class TestMacroSolverIntegration:
    def test_completes_run_without_crashing(self, game_data: GameData):
        """Macro solver should complete a full run end-to-end."""
        from heresiarch.tools.run_driver import simulate_run

        solver = make_solver(
            game_data,
            config=SolverConfig(search_depth=1, prune_after_ply=10),
        )
        ms = make_macro_solver(
            game_data, solver,
            config=MacroSolverConfig(
                eval_solver_depth=1,
                eval_solver_prune=10,
                lookahead_encounters=2,
            ),
        )
        result = simulate_run(
            mc_job_id="einherjar",
            combat_policy=solver,
            macro_policy=ms,
            seed=42,
            game_data=game_data,
            max_encounters=10,
        )
        assert result.encounters_cleared >= 1
        assert result.termination_reason in ("dead", "max_encounters", "stuck")

    def test_berserker_completes_run(self, game_data: GameData):
        """Berserker (the motivating case) should complete without crashing."""
        from heresiarch.tools.run_driver import simulate_run

        solver = make_solver(
            game_data,
            config=SolverConfig(search_depth=1, prune_after_ply=10),
        )
        ms = make_macro_solver(
            game_data, solver,
            config=MacroSolverConfig(
                eval_solver_depth=1,
                eval_solver_prune=10,
                lookahead_encounters=2,
            ),
        )
        result = simulate_run(
            mc_job_id="berserker",
            combat_policy=solver,
            macro_policy=ms,
            seed=42,
            game_data=game_data,
            max_encounters=10,
        )
        assert result.termination_reason in ("dead", "max_encounters", "stuck")
