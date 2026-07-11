"""Tests for the policy optimizer and the knobs it searches over.

Covers:
  - boss-aware pre-boss retreat / heal targets in GoldenMacroPolicy
  - RolloutConfig thresholds actually changing rollout behavior
  - ParamSpec normalize/denormalize round-trips
  - params_to_configs / preset_params mapping
  - CEM refit moving toward elites
  - score_result censoring semantics (alive-at-cap is not a win)
"""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import GameLoop
from heresiarch.policy.builtin.golden_macro import (
    GOLDEN_CONFIGS,
    GoldenMacroConfig,
    GoldenMacroPolicy,
)
from heresiarch.policy.rollout import HeuristicRolloutPolicy, RolloutConfig
from heresiarch.tools.policy_opt import (
    PARAM_SPECS,
    CEMState,
    FitnessWeights,
    params_to_configs,
    preset_params,
    score_result,
)

ZONE_01_BOSS_INDEX = 4  # alpha_slime encounter in zone_01


def _run_at_boss(game_data: GameData, hp_pct: float, *, gold: int = 100):
    """Build a RunState inside zone_01 with the boss up next."""
    gl = GameLoop(game_data, random.Random(42))
    run = gl.new_run("test", "mc", "einherjar")
    run = gl.enter_zone(run, "zone_01")
    zs = run.zone_state.model_copy(
        update={"current_encounter_index": ZONE_01_BOSS_INDEX},
    )
    run = run.model_copy(update={"zone_state": zs})

    mc = next(c for c in run.party.characters.values() if c.is_mc)
    wounded = mc.model_copy(
        update={"current_hp": max(1, int(mc.max_hp * hp_pct))},
    )
    party = run.party.model_copy(
        update={
            "characters": {**run.party.characters, wounded.id: wounded},
            "money": gold,
        },
    )
    return run.model_copy(update={"party": party})


class TestPreBossRetreat:
    def test_retreats_when_wounded_before_boss(self, game_data: GameData):
        run = _run_at_boss(game_data, hp_pct=0.5)
        macro = GoldenMacroPolicy(
            GoldenMacroConfig(pre_boss_retreat_hp_pct=0.90,
                              potion_stockpile_target=0),
            game_data,
        )
        assert macro.decide_retreat_to_town(run) is True

    def test_no_retreat_when_healthy_before_boss(self, game_data: GameData):
        run = _run_at_boss(game_data, hp_pct=1.0)
        macro = GoldenMacroPolicy(
            GoldenMacroConfig(pre_boss_retreat_hp_pct=0.90,
                              potion_stockpile_target=0),
            game_data,
        )
        assert macro.decide_retreat_to_town(run) is False

    def test_no_retreat_when_broke_and_potionless(self, game_data: GameData):
        """A party that can't heal in town shouldn't loop the door."""
        run = _run_at_boss(game_data, hp_pct=0.5, gold=0)
        macro = GoldenMacroPolicy(
            GoldenMacroConfig(pre_boss_retreat_hp_pct=0.90,
                              potion_stockpile_target=0),
            game_data,
        )
        assert macro.decide_retreat_to_town(run) is False

    def test_non_boss_encounter_uses_normal_rules(self, game_data: GameData):
        gl = GameLoop(game_data, random.Random(42))
        run = gl.new_run("test", "mc", "einherjar")
        run = gl.enter_zone(run, "zone_01")  # encounter 0: fodder, not boss
        macro = GoldenMacroPolicy(
            GoldenMacroConfig(pre_boss_retreat_hp_pct=0.90,
                              potion_stockpile_target=0),
            game_data,
        )
        # Full HP, no potion need → no retreat.
        assert macro.decide_retreat_to_town(run) is False

    def test_boss_raises_between_encounter_heal_target(
        self, game_data: GameData,
    ):
        run = _run_at_boss(game_data, hp_pct=0.5)
        # Stash a potion so the healer has something to work with.
        party = run.party.model_copy(
            update={"stash": ["minor_potion", "minor_potion"]},
        )
        run = run.model_copy(update={"party": party})

        low_threshold = GoldenMacroPolicy(
            GoldenMacroConfig(pre_boss_retreat_hp_pct=0.90),
            game_data,
        )
        uses = low_threshold.decide_between_encounter_items(run)
        # At 50% HP with an ordinary threshold of 25%, only the boss
        # check justifies healing.
        assert len(uses) >= 1


class TestRolloutConfig:
    def test_default_matches_legacy_thresholds(self):
        cfg = RolloutConfig()
        assert cfg.insight_dump_threshold == 6
        assert cfg.kill_safety == 1.0
        assert cfg.heal_safety == 1.0

    def test_insight_dump_threshold_honored(self, game_data: GameData):
        """Stacks below the threshold keep banking; at threshold, dump."""
        from heresiarch.engine.combat import CombatEngine
        from heresiarch.engine.models.combat_state import CheatSurviveChoice
        from heresiarch.policy.validation import compute_legal
        from tests.conftest import _make_character

        player = _make_character(game_data, "onmyoji", 5, "spirit_lens")
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=random.Random(42),
            enemy_registry=game_data.enemies,
        )
        # Beefy enemy: no kill-all available, so rules 1/2 don't fire.
        enemy_t = game_data.enemies["alpha_slime"]
        enemy = engine.create_enemy_instance(enemy_t, 10)
        state = engine.initialize_combat([player], [enemy])
        actor = state.living_players[0]
        actor.insight_stacks = 4
        legal = compute_legal(state, actor, stash=[])

        patient = HeuristicRolloutPolicy(
            game_data, config=RolloutConfig(insight_dump_threshold=6),
        )
        eager = HeuristicRolloutPolicy(
            game_data, config=RolloutConfig(insight_dump_threshold=4),
        )

        assert patient.decide(state, actor, legal).cheat_survive == (
            CheatSurviveChoice.SURVIVE
        )
        assert eager.decide(state, actor, legal).cheat_survive != (
            CheatSurviveChoice.SURVIVE
        )


class TestParamSpace:
    def test_denormalize_bounds_and_types(self):
        for spec in PARAM_SPECS:
            lo_val = spec.denormalize(0.0)
            hi_val = spec.denormalize(1.0)
            if spec.kind == "bool":
                assert lo_val is False and hi_val is True
            elif spec.kind == "int":
                assert lo_val == int(spec.lo) and hi_val == int(spec.hi)
            else:
                assert lo_val == pytest.approx(spec.lo)
                assert hi_val == pytest.approx(spec.hi)
            # Out-of-range samples clip instead of exploding.
            assert spec.denormalize(-3.0) == lo_val
            assert spec.denormalize(9.0) == hi_val

    def test_normalize_roundtrip(self):
        for spec in PARAM_SPECS:
            for x in (0.0, 0.25, 0.75, 1.0):
                value = spec.denormalize(x)
                back = spec.denormalize(spec.normalize(value))
                assert back == value

    def test_preset_params_cover_every_spec(self):
        for job_id in GOLDEN_CONFIGS:
            params = preset_params(job_id)
            assert set(params) == {s.name for s in PARAM_SPECS}

    def test_params_to_configs_applies_both_groups(self):
        params = preset_params("einherjar")
        params["potion_stockpile_target"] = 4
        params["insight_dump_threshold"] = 3
        macro, rollout = params_to_configs(params, "einherjar")
        assert macro.potion_stockpile_target == 4
        assert rollout.insight_dump_threshold == 3
        # Job identity fields untouched by the search.
        assert macro.preferred_weapon_stat == (
            GOLDEN_CONFIGS["einherjar"].preferred_weapon_stat
        )


class TestCEM:
    def test_refit_moves_mean_toward_elites(self):
        base = preset_params("einherjar")
        cem = CEMState.from_params(base, init_std=0.2)
        idx = next(
            i for i, s in enumerate(PARAM_SPECS) if s.name == "potion_stockpile_target"
        )
        before = cem.mean[idx]

        elite = dict(base)
        elite["potion_stockpile_target"] = 0  # elites all say: carry nothing
        cem.refit([elite, dict(elite)], smoothing=0.7, std_floor=0.05)

        assert cem.mean[idx] < before
        assert all(s >= 0.05 for s in cem.std)

    def test_sample_respects_types(self):
        cem = CEMState.from_params(preset_params("einherjar"), init_std=0.3)
        rng = random.Random(0)
        sample = cem.sample(rng)
        for spec in PARAM_SPECS:
            value = sample[spec.name]
            if spec.kind == "bool":
                assert isinstance(value, bool)
            elif spec.kind == "int":
                assert isinstance(value, int)
                assert spec.lo <= value <= spec.hi


class TestFitness:
    class _FakeResult:
        def __init__(self, **kw):
            self.seed = kw.get("seed", 0)
            self.zones_cleared = kw.get("zones_cleared", [])
            self.encounters_cleared = kw.get("encounters_cleared", 0)
            self.farthest_zone_level = kw.get("farthest_zone_level", 0)
            self.is_dead = kw.get("is_dead", False)
            self.termination_reason = kw.get("termination_reason", "clean_exit")
            self.final_mc_level = kw.get("final_mc_level", 1)

    def test_alive_at_cap_is_not_a_win(self):
        weights = FitnessWeights()
        censored = score_result(
            self._FakeResult(
                zones_cleared=["zone_01", "zone_02", "zone_03"],
                encounters_cleared=200,
                termination_reason="max_encounters",
            ),
            final_zone_ids={"zone_07"},
            max_encounters=200,
            weights=weights,
        )
        assert censored.won_region is False
        assert censored.fitness == pytest.approx(
            3 * weights.per_zone + weights.alive,
        )

    def test_finishing_early_beats_grinding(self):
        weights = FitnessWeights()
        fast = score_result(
            self._FakeResult(
                zones_cleared=["zone_%02d" % i for i in range(1, 8)],
                encounters_cleared=120,
                termination_reason="clean_exit",
            ),
            final_zone_ids={"zone_07"},
            max_encounters=200,
            weights=weights,
        )
        slow = score_result(
            self._FakeResult(
                zones_cleared=["zone_%02d" % i for i in range(1, 8)],
                encounters_cleared=200,
                termination_reason="max_encounters",
            ),
            final_zone_ids={"zone_07"},
            max_encounters=200,
            weights=weights,
        )
        assert fast.won_region and slow.won_region
        assert fast.fitness > slow.fitness


class TestAdaptiveDepth:
    def test_trash_fight_goes_shallow(self, game_data: GameData):
        """A lone low-level fodder slime against a strong player is not
        dangerous — adaptive depth should drop to 1-ply."""
        from heresiarch.engine.combat import CombatEngine
        from heresiarch.policy.solver import SolverConfig, make_solver
        from heresiarch.policy.validation import compute_legal
        from tests.conftest import _make_character

        player = _make_character(game_data, "einherjar", 15, "iron_blade")
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=random.Random(11),
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(
            game_data.enemies["fodder_slime"], 2,
        )
        state = engine.initialize_combat([player], [enemy])
        actor = state.living_players[0]

        solver = make_solver(
            game_data,
            config=SolverConfig(search_depth=3, adaptive_depth=True),
        )
        solver.set_context(
            stash=[], enemy_templates={"fodder_slime": game_data.enemies["fodder_slime"]},
        )
        legal = compute_legal(state, actor, stash=[])
        assert solver._is_dangerous(state, actor, legal) is False

    def test_boss_fight_stays_deep(self, game_data: GameData):
        """A high-level alpha slime against a weak player is dangerous."""
        from heresiarch.engine.combat import CombatEngine
        from heresiarch.policy.solver import SolverConfig, make_solver
        from heresiarch.policy.validation import compute_legal
        from tests.conftest import _make_character

        player = _make_character(game_data, "einherjar", 5, "iron_blade")
        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=random.Random(11),
            enemy_registry=game_data.enemies,
        )
        enemy = engine.create_enemy_instance(
            game_data.enemies["alpha_slime"], 8,
        )
        state = engine.initialize_combat([player], [enemy])
        actor = state.living_players[0]

        solver = make_solver(
            game_data,
            config=SolverConfig(search_depth=3, adaptive_depth=True),
        )
        solver.set_context(
            stash=[], enemy_templates={"alpha_slime": game_data.enemies["alpha_slime"]},
        )
        legal = compute_legal(state, actor, stash=[])
        assert solver._is_dangerous(state, actor, legal) is True


class TestProgressStream:
    def test_emitter_and_reader_roundtrip(self, tmp_path):
        from heresiarch.tools.progress import ProgressEmitter, read_events

        path = tmp_path / "progress.jsonl"
        em = ProgressEmitter(path)
        em.emit("run_start", seed=7, job="einherjar")
        em.emit("encounter", seed=7, zone="zone_01", enc=1,
                level=2, hp_pct=0.85, gold=30)
        em.emit("run_end", seed=7, zones=1, enc=5, dead=True, reason="dead")

        events, offset = read_events(path, 0)
        assert [e["kind"] for e in events] == ["run_start", "encounter", "run_end"]
        # Incremental read from offset returns nothing new.
        more, offset2 = read_events(path, offset)
        assert more == [] and offset2 == offset

    def test_disabled_emitter_is_noop(self):
        from heresiarch.tools.progress import ProgressEmitter

        em = ProgressEmitter(None)
        em.emit("run_start", seed=1)  # must not raise
        assert em.enabled is False

    def test_reader_tolerates_torn_tail(self, tmp_path):
        from heresiarch.tools.progress import ProgressEmitter, read_events

        path = tmp_path / "progress.jsonl"
        ProgressEmitter(path).emit("run_start", seed=1, job="x")
        with path.open("a") as fh:
            fh.write('{"kind": "encounter", "seed"')  # torn mid-write
        events, _ = read_events(path, 0)
        assert [e["kind"] for e in events] == ["run_start"]

    def test_run_driver_emits_heartbeats(self, tmp_path, monkeypatch, game_data):
        from heresiarch.policy.builtin.default_macro import DefaultMacroPolicy
        from heresiarch.policy.builtin.floor import FloorCombatPolicy
        from heresiarch.tools.progress import ENV_VAR, read_events
        from heresiarch.tools.run_driver import simulate_run

        path = tmp_path / "progress.jsonl"
        monkeypatch.setenv(ENV_VAR, str(path))
        simulate_run(
            mc_job_id="einherjar",
            combat_policy=FloorCombatPolicy(),
            macro_policy=DefaultMacroPolicy(),
            seed=0,
            game_data=game_data,
            max_encounters=3,
        )
        events, _ = read_events(path, 0)
        kinds = [e["kind"] for e in events]
        assert kinds[0] == "run_start"
        assert kinds[-1] == "run_end"
        assert "encounter" in kinds

    def test_watch_state_applies_events(self):
        from heresiarch.tools.watch import WatchState

        st = WatchState()
        st.apply({"kind": "run_start", "seed": 3, "job": "x", "ts": 1.0})
        st.apply({"kind": "encounter", "seed": 3, "zone": "zone_01",
                  "enc": 2, "level": 4, "hp_pct": 0.5, "gold": 10, "ts": 2.0})
        assert st.seeds[3].zone == "zone_01"
        assert st.seeds[3].dead is None
        st.apply({"kind": "run_end", "seed": 3, "zones": 1, "enc": 9,
                  "dead": True, "reason": "dead", "ts": 3.0})
        assert st.seeds[3].dead is True
        st.apply({"kind": "generation", "gen": 0, "best": 500.0,
                  "pop_mean": 300.0, "best_ever": 500.0, "win_rate": 0.1})
        assert len(st.gen_lines) == 1


class TestStagedEvaluation:
    """Successive halving inside evaluate_population."""

    @staticmethod
    def _fake_eval_factory(calls: list):
        """Deterministic fitness = candidate index; logs every task."""
        from heresiarch.tools.policy_opt import SeedOutcome

        def fake_eval(task: tuple):
            cand_idx, seed = task[0], task[1]
            calls.append((cand_idx, seed))
            return cand_idx, SeedOutcome(
                seed=seed,
                fitness=float(cand_idx * 100),
                zones_cleared=cand_idx,
                encounters_cleared=cand_idx,
                farthest_zone_level=1,
                is_dead=False,
                won_region=False,
                termination_reason="clean_exit",
                final_mc_level=1,
            )

        return fake_eval

    def _run(self, monkeypatch, *, stage_seeds: int, stage_keep: int):
        import heresiarch.tools.policy_opt as po

        calls: list = []
        monkeypatch.setattr(po, "_evaluate_one", self._fake_eval_factory(calls))
        monkeypatch.setattr(po, "_worker_init", lambda _: None)
        population = [{"dummy": float(i)} for i in range(4)]
        records = po.evaluate_population(
            population, seeds=[10, 11, 12],
            job_id="einherjar", generation=0,
            solver_depth=1, solver_prune=20, max_encounters=5,
            weights=po.FitnessWeights(), workers=1, data_path="data",
            stage_seeds=stage_seeds, stage_keep=stage_keep,
        )
        return records, calls

    def test_staging_off_runs_every_pair(self, monkeypatch):
        records, calls = self._run(monkeypatch, stage_seeds=0, stage_keep=0)
        assert len(calls) == 4 * 3
        assert all(len(r.outcomes) == 3 for r in records)

    def test_staging_culls_bottom_but_keeps_elitism_slot(self, monkeypatch):
        # Fitness rises with candidate index, so candidate 0 is the
        # WORST — it must still advance (elitism slot).
        records, calls = self._run(monkeypatch, stage_seeds=1, stage_keep=2)
        # Stage 1: all 4 candidates on seed 10.
        assert [c for c in calls if c[1] == 10] == [(i, 10) for i in range(4)]
        # Survivors: top-2 (3, 2) plus forced candidate 0. Candidate 1 culled.
        full = {r.candidate_index for r in records if len(r.outcomes) == 3}
        assert full == {0, 2, 3}
        culled = [r for r in records if r.candidate_index == 1]
        assert len(culled[0].outcomes) == 1  # partial fitness retained
        # Mean fitness still computed for everyone.
        assert all(r.mean_fitness == r.candidate_index * 100 for r in records)
