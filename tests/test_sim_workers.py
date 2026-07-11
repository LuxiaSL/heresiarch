"""Worker plumbing for the multi-seed sim CLI (tools/sim.py).

Covers the per-process GameData cache (pool initializer pattern) and
the typed _SeedTask work unit that replaced the fragile 16-way
positional tuple.
"""

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.tools import sim as sim_mod
from heresiarch.tools.sim import (
    _run_one_seed,
    _SeedTask,
    _worker_game_data,
    _worker_init,
)


@pytest.fixture(autouse=True)
def _clean_worker_cache():
    sim_mod._WORKER_GAME_DATA.clear()
    yield
    sim_mod._WORKER_GAME_DATA.clear()


class TestWorkerGameDataCache:
    def test_worker_init_populates_cache(self):
        _worker_init("data")
        assert "data" in sim_mod._WORKER_GAME_DATA
        assert isinstance(sim_mod._WORKER_GAME_DATA["data"], GameData)

    def test_cache_hit_skips_reload(self, monkeypatch, game_data: GameData):
        """After init, _worker_game_data must not call load_all again."""
        sim_mod._WORKER_GAME_DATA["data"] = game_data

        import heresiarch.engine.data_loader as dl

        def _boom(path):
            raise AssertionError("load_all called despite warm cache")

        monkeypatch.setattr(dl, "load_all", _boom)
        assert _worker_game_data("data") is game_data

    def test_cache_miss_loads_on_demand(self, monkeypatch, game_data: GameData):
        """Direct callers (no pool initializer) still get GameData."""
        import heresiarch.engine.data_loader as dl

        calls: list[str] = []

        def _fake_load(path):
            calls.append(str(path))
            return game_data

        monkeypatch.setattr(dl, "load_all", _fake_load)
        assert _worker_game_data("data") is game_data
        assert calls == ["data"]
        # Second call is served from the cache.
        assert _worker_game_data("data") is game_data
        assert calls == ["data"]


class TestSeedTask:
    def test_trailing_fields_default(self):
        """Deep-analyze builds tasks without tap/model knobs."""
        task = _SeedTask(
            seed=7, job_id="einherjar",
            policy_name="solver", macro_name="golden_macro",
            data_path="data", max_enc=10, db_path="",
            solver_depth=1, solver_prune=5, macro_lookahead=2,
        )
        assert task.macro_params_path == ""
        assert task.adaptive is False
        assert task.record_every == 0
        assert task.tap_dir == ""
        assert task.leaf_eval == "rollout"
        assert task.model_path == ""

    def test_arity_is_checked(self):
        """Too few positional fields fails at construction, not unpack."""
        with pytest.raises(TypeError):
            _SeedTask(1, "einherjar", "solver")  # type: ignore[call-arg]

    def test_run_one_seed_executes_task(self):
        """End-to-end: a cheap floor-policy task produces a run result."""
        task = _SeedTask(
            seed=42, job_id="einherjar",
            policy_name="floor", macro_name="default_macro",
            data_path="data", max_enc=2, db_path="",
            solver_depth=1, solver_prune=5, macro_lookahead=2,
        )
        result = _run_one_seed(task)
        assert result.seed == 42
        assert result.encounters_cleared >= 0
        # The on-demand load populated this process's cache.
        assert "data" in sim_mod._WORKER_GAME_DATA

    def test_run_one_seed_accepts_plain_tuple(self):
        """Raw tuples (legacy callers) are promoted to _SeedTask."""
        raw = (
            43, "einherjar", "floor", "default_macro",
            "data", 1, "", 1, 5, 2,
        )
        result = _run_one_seed(raw)
        assert result.seed == 43
