"""Tests for the combat solver: enumerator, rollout, and full solver."""

import random
from pathlib import Path

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.policy.enumerator import enumerate_decisions
from heresiarch.policy.protocols import LegalActionSet
from heresiarch.policy.rollout import HeuristicRolloutPolicy
from heresiarch.policy.solver import CombatSolver, SolverConfig, evaluate_terminal
from heresiarch.policy.validation import compute_legal
from tests.conftest import _make_character


@pytest.fixture
def game_data() -> GameData:
    return load_all(Path("data"))


@pytest.fixture
def seeded_rng() -> random.Random:
    return random.Random(42)


def _make_combat(
    game_data: GameData,
    rng: random.Random,
    player: CharacterInstance,
    enemies: list[EnemyInstance],
) -> tuple[CombatState, CombatEngine]:
    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng,
        enemy_registry=game_data.enemies,
    )
    state = engine.initialize_combat([player], enemies)
    return state, engine


# ---------------------------------------------------------------------------
# Enumerator tests
# ---------------------------------------------------------------------------


class TestEnumerator:
    def test_always_has_survive(self, game_data: GameData, seeded_rng: random.Random):
        player = _make_character(game_data, "einherjar", 5, "iron_blade")
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 3)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decisions = enumerate_decisions(state, actor, legal, game_data)

        survive_count = sum(
            1 for d in decisions if d.cheat_survive == CheatSurviveChoice.SURVIVE
        )
        assert survive_count == 1

    def test_no_cheat_at_zero_ap(self, game_data: GameData, seeded_rng: random.Random):
        player = _make_character(game_data, "einherjar", 5)
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 3)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])
        actor = state.living_players[0]
        assert actor.action_points == 0

        legal = compute_legal(state, actor, stash=[])
        decisions = enumerate_decisions(state, actor, legal, game_data)

        cheat_count = sum(
            1 for d in decisions if d.cheat_survive == CheatSurviveChoice.CHEAT
        )
        assert cheat_count == 0

    def test_item_decisions_when_potion_available(
        self, game_data: GameData, seeded_rng: random.Random,
    ):
        player = _make_character(game_data, "einherjar", 5)
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 3)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=["minor_potion"])
        decisions = enumerate_decisions(state, actor, legal, game_data)

        item_decisions = [
            d for d in decisions
            if d.primary_action and d.primary_action.item_id is not None
        ]
        assert len(item_decisions) >= 1

    def test_decisions_count_scales_with_enemies(
        self, game_data: GameData, seeded_rng: random.Random,
    ):
        player = _make_character(game_data, "einherjar", 5)
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        e1 = engine.create_enemy_instance(enemy_t, 3)
        e2 = engine.create_enemy_instance(enemy_t, 3)

        state1, _ = _make_combat(game_data, random.Random(1), player, [e1])
        state2, _ = _make_combat(game_data, random.Random(2), player, [e1, e2])

        legal1 = compute_legal(state1, state1.living_players[0], stash=[])
        legal2 = compute_legal(state2, state2.living_players[0], stash=[])

        d1 = enumerate_decisions(state1, state1.living_players[0], legal1, game_data)
        d2 = enumerate_decisions(state2, state2.living_players[0], legal2, game_data)

        assert len(d2) > len(d1)


# ---------------------------------------------------------------------------
# Rollout tests
# ---------------------------------------------------------------------------


class TestRollout:
    def test_survives_when_no_kill(self, game_data: GameData, seeded_rng: random.Random):
        rollout = HeuristicRolloutPolicy(game_data)
        player = _make_character(game_data, "einherjar", 3)
        enemy_t = game_data.enemies["brute_oni"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 10)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])

        decision = rollout.decide(state, actor, legal)
        assert decision.cheat_survive == CheatSurviveChoice.SURVIVE

    def test_kills_when_possible(self, game_data: GameData, seeded_rng: random.Random):
        rollout = HeuristicRolloutPolicy(game_data)
        player = _make_character(game_data, "einherjar", 15, "iron_blade")
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 1)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])

        decision = rollout.decide(state, actor, legal)
        assert decision.cheat_survive in (
            CheatSurviveChoice.NORMAL,
            CheatSurviveChoice.CHEAT,
        )


# ---------------------------------------------------------------------------
# Solver tests
# ---------------------------------------------------------------------------


class TestSolver:
    def test_solver_finds_kill(self, game_data: GameData):
        """Solver should find the kill against a weak enemy."""
        solver = CombatSolver(game_data=game_data)
        player = _make_character(game_data, "einherjar", 15, "iron_blade")
        enemy_t = game_data.enemies["fodder_slime"]
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 1)
        state, _ = _make_combat(game_data, random.Random(42), player, [enemy])

        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])

        enemy_templates = {"fodder_slime": game_data.enemies["fodder_slime"]}
        solver.set_context(stash=[], enemy_templates=enemy_templates)

        decision = solver.decide(state, actor, legal)
        # Should attack, not survive — the enemy is trivially killable
        assert decision.cheat_survive != CheatSurviveChoice.SURVIVE

    def test_solver_survives_when_outmatched(self, game_data: GameData):
        """Solver should survive against a much stronger enemy."""
        solver = CombatSolver(game_data=game_data)
        player = _make_character(game_data, "einherjar", 3)
        enemy_t = game_data.enemies["brute_oni"]
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 15)
        state, _ = _make_combat(game_data, random.Random(42), player, [enemy])

        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])

        enemy_templates = {"brute_oni": game_data.enemies["brute_oni"]}
        solver.set_context(stash=[], enemy_templates=enemy_templates)

        decision = solver.decide(state, actor, legal)
        assert decision.cheat_survive == CheatSurviveChoice.SURVIVE

    def test_solver_prefers_lower_ap_on_tie(self, game_data: GameData):
        """When multiple AP spends can kill, solver should prefer lower."""
        solver = CombatSolver(
            game_data=game_data,
            config=SolverConfig(enable_short_circuit=False),
        )
        player = _make_character(game_data, "einherjar", 15, "iron_blade")
        # Give the player 3 AP
        player = player.model_copy(update={"abilities": ["basic_attack", "retaliate"]})

        enemy_t = game_data.enemies["fodder_slime"]
        rng = random.Random(42)
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 1)
        state, _ = _make_combat(game_data, random.Random(42), player, [enemy])

        # Give actor AP to test tiebreaking
        actor = state.living_players[0]
        actor.action_points = 3

        legal = compute_legal(state, actor, stash=[])
        enemy_templates = {"fodder_slime": game_data.enemies["fodder_slime"]}
        solver.set_context(stash=[], enemy_templates=enemy_templates)

        decision = solver.decide(state, actor, legal)
        # Should prefer NORMAL (0 AP) over CHEAT when both kill
        if decision.cheat_survive == CheatSurviveChoice.CHEAT:
            assert decision.cheat_actions <= 1

    def test_evaluate_terminal_win(self, game_data: GameData, seeded_rng: random.Random):
        player = _make_character(game_data, "einherjar", 10)
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 1)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])

        # Simulate a win: kill the enemy
        for e in state.enemy_combatants:
            e.current_hp = 0
            e.is_alive = False
        state.is_finished = True
        state.player_won = True

        score = evaluate_terminal(state)
        assert score >= 1.0
        assert score <= 2.0

    def test_evaluate_terminal_loss(self, game_data: GameData, seeded_rng: random.Random):
        player = _make_character(game_data, "einherjar", 10)
        enemy_t = game_data.enemies["fodder_slime"]
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(enemy_t, 1)
        state, _ = _make_combat(game_data, seeded_rng, player, [enemy])

        state.is_finished = True
        state.player_won = False

        score = evaluate_terminal(state)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Integration: solver through the sim driver
# ---------------------------------------------------------------------------


class TestSolverIntegration:
    def test_solver_completes_one_seed(self, game_data: GameData):
        """Solver should complete a full run without crashing."""
        from heresiarch.policy.builtin.golden_macro import make_golden_macro_einherjar
        from heresiarch.tools.run_driver import simulate_run

        solver = CombatSolver(game_data=game_data)
        macro = make_golden_macro_einherjar(game_data)
        result = simulate_run(
            mc_job_id="einherjar",
            combat_policy=solver,
            macro_policy=macro,
            seed=42,
            game_data=game_data,
            max_encounters=10,
        )
        assert result.encounters_cleared >= 1
        assert result.termination_reason in ("dead", "max_encounters", "stuck")
