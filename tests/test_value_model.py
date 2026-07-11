"""Learned value functions: loader fallbacks, solver model leaves, trainer."""

import gzip
import json
import pickle
import random
from pathlib import Path

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.combat_state import CombatState
from heresiarch.policy.features import (
    FEATURES_VERSION,
    combat_feature_names,
    macro_feature_names,
)
from heresiarch.policy.solver import CombatSolver, SolverConfig
from heresiarch.policy.validation import compute_legal
from heresiarch.policy.value_model import (
    _CACHE,
    ModelValueFn,
    load_combat_value_fn,
)
from tests.conftest import _make_character


@pytest.fixture(autouse=True)
def _clear_model_cache():
    _CACHE.clear()
    yield
    _CACHE.clear()


def _make_combat(game_data: GameData, rng: random.Random):
    player = _make_character(game_data, "einherjar", 5, "iron_blade")
    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng,
        enemy_registry=game_data.enemies,
    )
    enemy_t = game_data.enemies["fodder_slime"]
    enemies = [engine.create_enemy_instance(enemy_t, 3) for _ in range(2)]
    state = engine.initialize_combat([player], enemies)
    templates = {"fodder_slime": enemy_t}
    return state, templates


# ---------------------------------------------------------------------------
# Loader fallbacks
# ---------------------------------------------------------------------------


class TestLoader:
    def test_missing_file_returns_none(self, tmp_path: Path):
        assert load_combat_value_fn(tmp_path / "nope.pkl") is None

    def test_corrupt_file_returns_none(self, tmp_path: Path):
        p = tmp_path / "junk.pkl"
        p.write_bytes(b"this is not a pickle")
        assert load_combat_value_fn(p) is None

    def test_wrong_kind_returns_none(self, tmp_path: Path):
        p = tmp_path / "macro.pkl"
        with p.open("wb") as fh:
            pickle.dump({
                "model": object(),
                "kind": "macro",
                "features_version": FEATURES_VERSION,
            }, fh)
        assert load_combat_value_fn(p) is None

    def test_version_mismatch_returns_none(self, tmp_path: Path):
        p = tmp_path / "old.pkl"
        with p.open("wb") as fh:
            pickle.dump({
                "model": object(),
                "kind": "combat",
                "features_version": FEATURES_VERSION + 999,
            }, fh)
        assert load_combat_value_fn(p) is None

    def test_result_is_cached(self, tmp_path: Path):
        p = tmp_path / "nope.pkl"
        assert load_combat_value_fn(p) is None
        assert str(p) in _CACHE


# ---------------------------------------------------------------------------
# Solver model leaves
# ---------------------------------------------------------------------------


class TestModelLeaves:
    def test_model_leaf_is_used(self, game_data: GameData):
        """With leaf_eval=model, leaves call value_fn instead of rollout."""
        calls: list[str] = []

        def stub_value(state: CombatState, mc_job_id: str,
                       stash_potions: int = 0, stash_size: int = 0) -> float:
            calls.append(mc_job_id)
            return 1.5

        solver = CombatSolver(
            game_data,
            config=SolverConfig(
                search_depth=1, enable_short_circuit=False,
                leaf_eval="model",
            ),
            value_fn=stub_value,
        )
        state, templates = _make_combat(game_data, random.Random(42))
        solver.set_context(
            stash=[], enemy_templates=templates, mc_job_id="einherjar",
        )
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)

        assert decision is not None
        assert calls, "value_fn was never consulted at leaves"
        assert all(j == "einherjar" for j in calls)
        assert solver.stats.model_leaf_evals == len(calls)
        # Model leaves skip rollout entirely
        assert solver.stats.rollout_rounds_total == 0

    def test_rollout_default_ignores_value_fn(self, game_data: GameData):
        """leaf_eval=rollout (default) never touches a provided value_fn."""
        def exploding_value(state: CombatState, mc_job_id: str,
                            stash_potions: int = 0,
                            stash_size: int = 0) -> float:
            raise AssertionError("must not be called")

        solver = CombatSolver(
            game_data,
            config=SolverConfig(search_depth=1, enable_short_circuit=False),
            value_fn=exploding_value,
        )
        state, templates = _make_combat(game_data, random.Random(42))
        solver.set_context(stash=[], enemy_templates=templates,
                           mc_job_id="einherjar")
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)
        assert decision is not None
        assert solver.stats.model_leaf_evals == 0

    def test_broken_model_falls_back_to_rollout(self, game_data: GameData):
        """A value_fn that raises downgrades to rollout, never crashes."""
        def broken_value(state: CombatState, mc_job_id: str,
                         stash_potions: int = 0,
                         stash_size: int = 0) -> float:
            raise RuntimeError("model on fire")

        solver = CombatSolver(
            game_data,
            config=SolverConfig(
                search_depth=1, enable_short_circuit=False,
                leaf_eval="model",
            ),
            value_fn=broken_value,
        )
        state, templates = _make_combat(game_data, random.Random(42))
        solver.set_context(stash=[], enemy_templates=templates,
                           mc_job_id="einherjar")
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)

        assert decision is not None
        assert solver._model_failed
        # Fallback actually rolled out
        assert solver.stats.rollout_rounds_total > 0

    def test_missing_value_fn_with_model_config_warns_and_rolls_out(
        self, game_data: GameData,
    ):
        solver = CombatSolver(
            game_data,
            config=SolverConfig(
                search_depth=1, enable_short_circuit=False,
                leaf_eval="model",
            ),
        )
        state, templates = _make_combat(game_data, random.Random(42))
        solver.set_context(stash=[], enemy_templates=templates,
                           mc_job_id="einherjar")
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)
        assert decision is not None
        assert solver.stats.rollout_rounds_total > 0


# ---------------------------------------------------------------------------
# Batched leaf evaluation
# ---------------------------------------------------------------------------


class _StubModel:
    """sklearn-shaped stub: deterministic affine function of features.

    Records call sizes and every returned value so tests can assert
    batching behavior and value parity.
    """

    def __init__(self) -> None:
        self.call_sizes: list[int] = []
        self.returned: list[float] = []

    def predict(self, xs: list[list[float]]) -> list[float]:
        self.call_sizes.append(len(xs))
        out = [0.3 + 0.017 * sum(x) for x in xs]
        self.returned.extend(out)
        return out


def _make_states(game_data: GameData) -> list[CombatState]:
    """A small, diverse fixed set of mid-combat states."""
    states: list[CombatState] = []
    for seed, enemy_level, n_enemies in [(1, 2, 1), (2, 3, 2), (3, 5, 2)]:
        state, _ = _make_combat(game_data, random.Random(seed))
        # Vary enemy count/level and wound the player for diversity.
        for i, enemy in enumerate(state.living_enemies):
            if i >= n_enemies:
                enemy.current_hp = 0
            else:
                enemy.current_hp = max(1, enemy.current_hp - enemy_level)
        player = state.living_players[0]
        player.current_hp = max(1, player.current_hp - 3 * seed)
        states.append(state)
    return states


class TestBatchedValueFn:
    def test_batch_matches_serial(self, game_data: GameData):
        """Batched and serial evaluation give identical values."""
        fn = ModelValueFn(_StubModel())
        states = _make_states(game_data)
        serial = [fn(s, "einherjar") for s in states]
        batched = fn.value_batch(states, "einherjar")
        assert batched == pytest.approx(serial)

    def test_values_clamped_to_terminal_scale(self, game_data: GameData):
        class _Wild:
            def predict(self, xs):
                return [5.0, -3.0][: len(xs)]

        fn = ModelValueFn(_Wild())
        states = _make_states(game_data)[:2]
        assert fn.value_batch(states, "einherjar") == [2.0, 0.0]

    def test_non_finite_prediction_raises(self, game_data: GameData):
        class _NaN:
            def predict(self, xs):
                return [float("nan")] * len(xs)

        fn = ModelValueFn(_NaN())
        state = _make_states(game_data)[0]
        with pytest.raises(ValueError):
            fn(state, "einherjar")
        with pytest.raises(ValueError):
            fn.value_batch([state], "einherjar")

    def test_wrong_prediction_count_raises(self, game_data: GameData):
        class _Short:
            def predict(self, xs):
                return [1.0]

        fn = ModelValueFn(_Short())
        states = _make_states(game_data)[:2]
        with pytest.raises(ValueError):
            fn.value_batch(states, "einherjar")


def _make_tough_combat(game_data: GameData, rng: random.Random):
    """A fight that cannot finish within the search horizon."""
    player = _make_character(game_data, "einherjar", 5, "iron_blade")
    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=rng,
        enemy_registry=game_data.enemies,
    )
    enemy_t = game_data.enemies["alpha_slime"]
    enemies = [engine.create_enemy_instance(enemy_t, 10)]
    state = engine.initialize_combat([player], enemies)
    templates = {"alpha_slime": enemy_t}
    return state, templates


class TestBatchedSolverLeaves:
    def _solver(self, game_data: GameData, value_fn) -> CombatSolver:
        return CombatSolver(
            game_data,
            config=SolverConfig(
                search_depth=2, enable_short_circuit=False,
                leaf_eval="model", decide_time_budget_s=0,
            ),
            value_fn=value_fn,
        )

    def test_one_batched_predict_per_decision(self, game_data: GameData):
        """All leaves across all candidates go through ONE predict call."""
        stub = _StubModel()
        solver = self._solver(game_data, ModelValueFn(stub))
        state, templates = _make_tough_combat(game_data, random.Random(42))
        solver.set_context(stash=[], enemy_templates=templates,
                           mc_job_id="einherjar")
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)

        assert decision is not None
        assert stub.call_sizes, "model was never consulted"
        assert len(stub.call_sizes) == 1
        assert solver.stats.model_batch_calls == 1
        assert solver.stats.model_leaf_evals == stub.call_sizes[0] > 1
        # Model leaves skip rollout entirely
        assert solver.stats.rollout_rounds_total == 0

    def test_batched_and_serial_pick_identical_decision(
        self, game_data: GameData,
    ):
        """Deferred+batched leaves change nothing about the search result."""
        stub_batched = _StubModel()
        stub_serial = _StubModel()
        serial_model = ModelValueFn(stub_serial)

        def serial_fn(
            state: CombatState, mc_job_id: str,
            stash_potions: int = 0, stash_size: int = 0,
        ) -> float:
            # Plain callable: no value_batch attribute → per-leaf path.
            # v2 CombatValueFn contract: stash context args.
            return serial_model(state, mc_job_id, stash_potions, stash_size)

        solver_b = self._solver(game_data, ModelValueFn(stub_batched))
        solver_s = self._solver(game_data, serial_fn)

        state_b, templates = _make_tough_combat(game_data, random.Random(42))
        state_s, _ = _make_tough_combat(game_data, random.Random(42))
        solver_b.set_context(stash=[], enemy_templates=templates,
                             mc_job_id="einherjar")
        solver_s.set_context(stash=[], enemy_templates=templates,
                             mc_job_id="einherjar")

        actor_b = state_b.living_players[0]
        actor_s = state_s.living_players[0]
        decision_b = solver_b.decide(
            state_b, actor_b, compute_legal(state_b, actor_b, stash=[]),
        )
        decision_s = solver_s.decide(
            state_s, actor_s, compute_legal(state_s, actor_s, stash=[]),
        )

        # Same leaf values in the same order, same decision out.
        assert stub_batched.returned == pytest.approx(stub_serial.returned)
        assert solver_b.stats.model_leaf_evals == solver_s.stats.model_leaf_evals
        assert decision_b.model_dump() == decision_s.model_dump()

    def test_batch_failure_falls_back_to_rollout(self, game_data: GameData):
        """A batched model that explodes downgrades to rollout leaves."""
        class _Boom:
            def predict(self, xs):
                raise RuntimeError("batch on fire")

        solver = self._solver(game_data, ModelValueFn(_Boom()))
        state, templates = _make_tough_combat(game_data, random.Random(42))
        solver.set_context(stash=[], enemy_templates=templates,
                           mc_job_id="einherjar")
        actor = state.living_players[0]
        legal = compute_legal(state, actor, stash=[])
        decision = solver.decide(state, actor, legal)

        assert decision is not None
        assert solver._model_failed
        assert solver.stats.model_leaf_evals == 0
        assert solver.stats.rollout_rounds_total > 0


# ---------------------------------------------------------------------------
# Trainer end-to-end (needs sklearn — ml dependency group)
# ---------------------------------------------------------------------------


def _write_synthetic_shard(path: Path, seeds: range) -> None:
    """Shards whose value is a learnable function of two features."""
    rng = random.Random(1234)
    n_combat = len(combat_feature_names())
    n_macro = len(macro_feature_names())
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for seed in seeds:
            for _ in range(30):
                x = [round(rng.random(), 3) for _ in range(n_combat)]
                value = max(0.0, min(2.0, 1.2 * x[0] + 0.8 * x[1]))
                fh.write(json.dumps({
                    "kind": "combat", "v": FEATURES_VERSION,
                    "job": "einherjar", "seed": seed, "policy": "synthetic",
                    "x": x,
                    "y": {"won": value > 1.0, "finished": True,
                          "end_hp_frac": 0.5, "rounds_left": 0,
                          "value": value},
                }) + "\n")
            for _ in range(5):
                xm = [round(rng.random(), 3) for _ in range(n_macro)]
                fh.write(json.dumps({
                    "kind": "macro", "v": FEATURES_VERSION,
                    "job": "einherjar", "seed": seed, "policy": "synthetic",
                    "x": xm,
                    "y": {"zones_ahead": round(3 * xm[0], 2),
                          "survived": True, "won_region": False},
                }) + "\n")
        # A torn line — concurrent-writer reality; must be skipped.
        fh.write('{"kind": "combat", "v": 1, "x": [0.1')


class TestTrainer:
    def test_train_and_load_roundtrip(self, tmp_path: Path):
        pytest.importorskip("sklearn")
        from heresiarch.tools.train_value import train_kind

        data_dir = tmp_path / "tapdata"
        data_dir.mkdir()
        _write_synthetic_shard(data_dir / "tap_einherjar_synth_0.jsonl.gz",
                               seeds=range(100, 140))
        out_dir = tmp_path / "models"

        sidecar = train_kind(
            "combat", data_dir, out_dir,
            max_iter=50, importance_rows=500,
        )
        assert sidecar is not None
        assert sidecar["metrics"]["r2"] > 0.5, (
            "model failed to learn a trivially learnable function"
        )
        assert sidecar["features_version"] == FEATURES_VERSION

        model_path = out_dir / f"combat_value_v{FEATURES_VERSION}.pkl"
        assert model_path.exists()
        assert (out_dir / f"combat_value_v{FEATURES_VERSION}.json").exists()

        fn = load_combat_value_fn(model_path)
        assert fn is not None

    def test_macro_head_trains(self, tmp_path: Path):
        pytest.importorskip("sklearn")
        from heresiarch.tools.train_value import train_kind

        data_dir = tmp_path / "tapdata"
        data_dir.mkdir()
        _write_synthetic_shard(data_dir / "tap_einherjar_synth_0.jsonl.gz",
                               seeds=range(100, 140))
        sidecar = train_kind(
            "macro", data_dir, tmp_path / "models",
            max_iter=50, importance_rows=500,
        )
        assert sidecar is not None
        assert sidecar["target"] == "zones_ahead"

    def test_trained_model_scores_real_combat_state(
        self, tmp_path: Path, game_data: GameData,
    ):
        """The full plumbing: synthetic model → loader → real CombatState."""
        pytest.importorskip("sklearn")
        from heresiarch.tools.train_value import train_kind

        data_dir = tmp_path / "tapdata"
        data_dir.mkdir()
        _write_synthetic_shard(data_dir / "tap_einherjar_synth_0.jsonl.gz",
                               seeds=range(100, 140))
        out_dir = tmp_path / "models"
        train_kind("combat", data_dir, out_dir,
                   max_iter=50, importance_rows=500)

        fn = load_combat_value_fn(
            out_dir / f"combat_value_v{FEATURES_VERSION}.pkl",
        )
        assert fn is not None

        state, _ = _make_tough_combat(game_data, random.Random(42))
        value = fn(state, "einherjar")
        assert 0.0 <= value <= 2.0


def test_job_leaf_defaults_table():
    from heresiarch.policy.value_model import job_leaf_defaults
    assert job_leaf_defaults("berserker") == ("model", 0)
    assert job_leaf_defaults("onmyoji") == ("model", 2)
    assert job_leaf_defaults("sacrist") == ("rollout", 0)
    assert job_leaf_defaults("unknown_job") == ("rollout", 0)
