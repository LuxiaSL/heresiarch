"""Policy parameter optimizer: CEM search over macro + rollout knobs.

The golden macro configs and the solver's rollout thresholds were
hand-tuned from designer intuition. This tool replaces that treadmill
with a cross-entropy method (CEM) search: sample a population of
parameter vectors, evaluate each across N full-run simulations
(common random numbers per generation), refit the sampling
distribution to the elite fraction, repeat.

Usage:
    uv run python -m heresiarch.tools.policy_opt --job einherjar \
        --pop 12 --seeds 8 --gens 6 --workers 14 --solver-depth 1

Outputs (under --out, default artifacts/policy_opt/<job>_<tag>/):
    generations.jsonl  — every candidate evaluation (params + per-seed results)
    best.json          — best-so-far config, updated per generation
    final_eval.json    — holdout comparison best-vs-preset at --final-depth

Design notes:
    - The search space is defined by PARAM_SPECS. The CEM operates in
      normalized [0, 1] space; ints are rounded and bools thresholded
      at build time.
    - Fitness rewards clearing zones and *finishing the region*, not
      farming: an alive-at-encounter-cap run that ground every zone to
      20/20 overstay is a censored run, not a win.
    - The designer preset is injected into generation 0 (and the
      best-so-far into every later generation) so the search can never
      regress below the hand-tuned baseline on the same seeds.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Parameter space
# ---------------------------------------------------------------------------

ParamKind = Literal["float", "int", "bool"]
ParamGroup = Literal["macro", "rollout"]


@dataclass(frozen=True)
class ParamSpec:
    """One tunable dimension of the policy search space."""

    name: str
    kind: ParamKind
    lo: float
    hi: float
    group: ParamGroup

    def denormalize(self, x: float) -> float | int | bool:
        """Map a normalized [0, 1] sample to a typed parameter value."""
        x = min(1.0, max(0.0, x))
        raw = self.lo + x * (self.hi - self.lo)
        if self.kind == "int":
            return int(round(raw))
        if self.kind == "bool":
            return x >= 0.5
        return round(raw, 4)

    def normalize(self, value: float | int | bool) -> float:
        """Map a typed parameter value back to [0, 1]."""
        if self.kind == "bool":
            return 1.0 if value else 0.0
        if self.hi == self.lo:
            return 0.5
        return min(1.0, max(0.0, (float(value) - self.lo) / (self.hi - self.lo)))


PARAM_SPECS: tuple[ParamSpec, ...] = (
    # --- GoldenMacroConfig knobs (live ones only) ---
    ParamSpec("potion_stockpile_target", "int", 0, 5, "macro"),
    ParamSpec("potion_stash_cap", "int", 1, 8, "macro"),
    ParamSpec("overstay_cap", "int", 0, 25, "macro"),
    ParamSpec("overstay_bail_hp_pct", "float", 0.05, 0.80, "macro"),
    ParamSpec("heal_threshold_pct", "float", 0.10, 0.95, "macro"),
    ParamSpec("in_town_heal_target_pct", "float", 0.50, 1.00, "macro"),
    ParamSpec("pre_boss_retreat_hp_pct", "float", 0.30, 1.00, "macro"),
    ParamSpec("lodge_on", "bool", 0, 1, "macro"),
    ParamSpec("lodge_hp_threshold", "float", 0.10, 0.60, "macro"),
    ParamSpec("pit_level_buffer", "int", 0, 10, "macro"),
    ParamSpec("town_visit_gold_threshold", "int", 0, 150, "macro"),
    ParamSpec("town_visit_hp_threshold", "float", 0.20, 0.90, "macro"),
    # --- RolloutConfig knobs ---
    ParamSpec("insight_dump_threshold", "int", 2, 10, "rollout"),
    ParamSpec("kill_safety", "float", 0.80, 2.00, "rollout"),
    ParamSpec("heal_safety", "float", 0.80, 2.00, "rollout"),
)


def params_to_configs(params: dict[str, float | int | bool], job_id: str):
    """Build (GoldenMacroConfig, RolloutConfig) from a parameter dict.

    Non-searched fields (stat preferences) come from the job's preset —
    they encode job identity, not tunable strategy.
    """
    from heresiarch.policy.builtin.golden_macro import (
        EINHERJAR_GOLDEN_CONFIG,
        GOLDEN_CONFIGS,
    )
    from heresiarch.policy.rollout import RolloutConfig

    base = GOLDEN_CONFIGS.get(job_id, EINHERJAR_GOLDEN_CONFIG)
    macro_fields = {f.name for f in fields(base)}
    macro_kwargs = {
        k: v for k, v in params.items()
        if k in macro_fields and _spec_group(k) == "macro"
    }
    macro = replace(base, **macro_kwargs)

    rollout_kwargs = {
        k: v for k, v in params.items() if _spec_group(k) == "rollout"
    }
    rollout = RolloutConfig(**rollout_kwargs)
    return macro, rollout


def preset_params(job_id: str) -> dict[str, float | int | bool]:
    """The designer's hand-tuned preset expressed as a parameter dict."""
    from heresiarch.policy.builtin.golden_macro import (
        EINHERJAR_GOLDEN_CONFIG,
        GOLDEN_CONFIGS,
    )
    from heresiarch.policy.rollout import RolloutConfig

    base = GOLDEN_CONFIGS.get(job_id, EINHERJAR_GOLDEN_CONFIG)
    rollout = RolloutConfig()
    out: dict[str, float | int | bool] = {}
    for spec in PARAM_SPECS:
        source = base if spec.group == "macro" else rollout
        out[spec.name] = getattr(source, spec.name)
    return out


def _spec_group(name: str) -> ParamGroup | None:
    for spec in PARAM_SPECS:
        if spec.name == name:
            return spec.group
    return None


def load_params(path: Path) -> dict[str, float | int | bool]:
    """Load a parameter dict from a policy_opt artifact.

    Accepts either a ``best.json`` (params under the "params" key) or a
    raw params dict. Unknown keys are dropped so old artifacts survive
    spec changes.
    """
    payload = json.loads(path.read_text())
    params = payload.get("params", payload)
    known = {s.name for s in PARAM_SPECS}
    return {k: v for k, v in params.items() if k in known}


# ---------------------------------------------------------------------------
# Fitness
# ---------------------------------------------------------------------------


class SeedOutcome(BaseModel):
    """One (candidate, seed) evaluation result."""

    seed: int
    fitness: float
    zones_cleared: int
    encounters_cleared: int
    farthest_zone_level: int
    is_dead: bool
    won_region: bool
    termination_reason: str
    final_mc_level: int
    error: str = ""


class CandidateRecord(BaseModel):
    """One candidate's full evaluation, persisted to generations.jsonl."""

    generation: int
    candidate_index: int
    params: dict[str, float | int | bool]
    outcomes: list[SeedOutcome] = Field(default_factory=list)
    mean_fitness: float = 0.0
    win_rate: float = 0.0
    mean_zones: float = 0.0


class FitnessWeights(BaseModel):
    """Weights for the run-level fitness function."""

    per_zone: float = 100.0
    win_region: float = 300.0
    alive: float = 50.0
    per_encounter_left_on_win: float = 0.5


def score_result(
    result,
    final_zone_ids: set[str],
    max_encounters: int,
    weights: FitnessWeights,
) -> SeedOutcome:
    """Score a RunResult. Rewards clearing zones and finishing the region.

    ``per_encounter_left_on_win`` rewards finishing with encounter
    budget to spare — this is what lets the optimizer discover that
    grinding every zone to the overstay cap is a censored loss, not
    safety.
    """
    won = bool(final_zone_ids & set(result.zones_cleared))
    fitness = weights.per_zone * len(result.zones_cleared)
    if won:
        fitness += weights.win_region
        fitness += weights.per_encounter_left_on_win * max(
            0, max_encounters - result.encounters_cleared,
        )
    if not result.is_dead:
        fitness += weights.alive
    return SeedOutcome(
        seed=result.seed,
        fitness=fitness,
        zones_cleared=len(result.zones_cleared),
        encounters_cleared=result.encounters_cleared,
        farthest_zone_level=result.farthest_zone_level,
        is_dead=result.is_dead,
        won_region=won,
        termination_reason=result.termination_reason,
        final_mc_level=result.final_mc_level,
    )


# ---------------------------------------------------------------------------
# Worker (multiprocessing)
# ---------------------------------------------------------------------------

_WORKER_GAME_DATA = None


def _worker_init(data_path: str) -> None:
    """Pool initializer: load GameData once per worker process."""
    global _WORKER_GAME_DATA
    from heresiarch.engine.data_loader import load_all

    _WORKER_GAME_DATA = load_all(Path(data_path))


def _evaluate_one(task: tuple) -> tuple[int, SeedOutcome]:
    """Run one (candidate, seed) simulation. Never raises."""
    (
        cand_idx, seed, job_id, params,
        solver_depth, solver_prune, max_encounters, weights_dump,
        adaptive,
    ) = task
    weights = FitnessWeights(**weights_dump)
    try:
        from heresiarch.policy.builtin.golden_macro import GoldenMacroPolicy
        from heresiarch.policy.solver import SolverConfig, make_solver
        from heresiarch.tools.run_driver import simulate_run

        gd = _WORKER_GAME_DATA
        if gd is None:
            from heresiarch.engine.data_loader import load_all
            gd = load_all(Path("data"))

        macro_cfg, rollout_cfg = params_to_configs(params, job_id)
        solver = make_solver(
            gd,
            config=SolverConfig(
                search_depth=solver_depth, prune_after_ply=solver_prune,
                adaptive_depth=adaptive,
            ),
            rollout_config=rollout_cfg,
        )
        macro = GoldenMacroPolicy(
            config=macro_cfg, game_data=gd, name="opt_macro",
        )
        result = simulate_run(
            mc_job_id=job_id,
            combat_policy=solver,
            macro_policy=macro,
            seed=seed,
            game_data=gd,
            max_encounters=max_encounters,
        )
        final_zone_ids = {
            zid for zid, z in gd.zones.items() if z.is_final
        }
        return cand_idx, score_result(
            result, final_zone_ids, max_encounters, weights,
        )
    except Exception as exc:  # noqa: BLE001 — worker must never crash the pool
        return cand_idx, SeedOutcome(
            seed=seed,
            fitness=0.0,
            zones_cleared=0,
            encounters_cleared=0,
            farthest_zone_level=0,
            is_dead=True,
            won_region=False,
            termination_reason="worker_error",
            final_mc_level=0,
            error=f"{type(exc).__name__}: {exc}",
        )


# ---------------------------------------------------------------------------
# CEM core
# ---------------------------------------------------------------------------


@dataclass
class CEMState:
    """Sampling distribution over the normalized parameter space."""

    mean: list[float]
    std: list[float]

    @classmethod
    def from_params(
        cls, params: dict[str, float | int | bool], init_std: float,
    ) -> CEMState:
        mean = [spec.normalize(params[spec.name]) for spec in PARAM_SPECS]
        return cls(mean=mean, std=[init_std] * len(PARAM_SPECS))

    def sample(self, rng: random.Random) -> dict[str, float | int | bool]:
        return {
            spec.name: spec.denormalize(
                rng.gauss(self.mean[i], self.std[i]),
            )
            for i, spec in enumerate(PARAM_SPECS)
        }

    def refit(
        self,
        elites: list[dict[str, float | int | bool]],
        smoothing: float,
        std_floor: float,
    ) -> None:
        """Move the distribution toward the elite set."""
        n = len(PARAM_SPECS)
        elite_norm = [
            [spec.normalize(e[spec.name]) for spec in PARAM_SPECS]
            for e in elites
        ]
        for i in range(n):
            col = [row[i] for row in elite_norm]
            e_mean = sum(col) / len(col)
            e_var = sum((x - e_mean) ** 2 for x in col) / max(1, len(col) - 1)
            e_std = math.sqrt(e_var)
            self.mean[i] = smoothing * e_mean + (1 - smoothing) * self.mean[i]
            self.std[i] = max(
                std_floor,
                smoothing * e_std + (1 - smoothing) * self.std[i],
            )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def evaluate_population(
    population: list[dict[str, float | int | bool]],
    seeds: list[int],
    *,
    job_id: str,
    generation: int,
    solver_depth: int,
    solver_prune: int,
    max_encounters: int,
    weights: FitnessWeights,
    workers: int,
    data_path: str,
    adaptive: bool = False,
) -> list[CandidateRecord]:
    """Evaluate every candidate on every seed, in parallel."""
    import multiprocessing

    tasks = [
        (
            idx, seed, job_id, params,
            solver_depth, solver_prune, max_encounters,
            weights.model_dump(), adaptive,
        )
        for idx, params in enumerate(population)
        for seed in seeds
    ]
    records = [
        CandidateRecord(
            generation=generation, candidate_index=idx, params=params,
        )
        for idx, params in enumerate(population)
    ]

    n_workers = min(workers, len(tasks))
    if n_workers > 1:
        with multiprocessing.Pool(
            n_workers, initializer=_worker_init, initargs=(data_path,),
        ) as pool:
            for cand_idx, outcome in pool.imap_unordered(_evaluate_one, tasks):
                records[cand_idx].outcomes.append(outcome)
    else:
        _worker_init(data_path)
        for task in tasks:
            cand_idx, outcome = _evaluate_one(task)
            records[cand_idx].outcomes.append(outcome)

    for rec in records:
        n = max(1, len(rec.outcomes))
        rec.mean_fitness = sum(o.fitness for o in rec.outcomes) / n
        rec.win_rate = sum(1 for o in rec.outcomes if o.won_region) / n
        rec.mean_zones = sum(o.zones_cleared for o in rec.outcomes) / n
        errors = [o.error for o in rec.outcomes if o.error]
        if errors:
            print(f"    [warn] candidate {rec.candidate_index}: "
                  f"{len(errors)} seed(s) errored, e.g. {errors[0]}")
    return records


def optimize(args: argparse.Namespace) -> None:
    out_dir = Path(args.out) if args.out else (
        Path("artifacts/policy_opt")
        / f"{args.job}_{time.strftime('%Y%m%d_%H%M%S')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_path = out_dir / "generations.jsonl"
    best_path = out_dir / "best.json"

    # Per-encounter heartbeats from every worker; watch live with
    # `python -m heresiarch.tools.watch <out_dir>/progress.jsonl`.
    import os

    from heresiarch.tools.progress import ENV_VAR, ProgressEmitter
    progress_path = out_dir / "progress.jsonl"
    os.environ[ENV_VAR] = str(progress_path)
    emitter = ProgressEmitter(progress_path)
    print(f"Live view: uv run python -m heresiarch.tools.watch {progress_path}")

    weights = FitnessWeights()
    rng = random.Random(args.cem_seed)

    baseline = preset_params(args.job)
    cem = CEMState.from_params(baseline, init_std=args.init_std)

    best_params: dict[str, float | int | bool] = dict(baseline)
    best_fitness = -1.0

    print(f"Policy optimizer — job={args.job} pop={args.pop} "
          f"seeds/candidate={args.seeds} gens={args.gens} "
          f"depth={args.solver_depth} workers={args.workers}")
    print(f"Artifacts → {out_dir}")

    for gen in range(args.gens):
        t0 = time.time()
        # Rotate the seed block each generation (unless pinned) so the
        # search can't overfit one set of drop/AI rolls. Common random
        # numbers WITHIN a generation keep comparisons fair.
        block = 0 if args.fixed_seeds else gen
        seeds = [args.seed_base + block * args.seeds + i for i in range(args.seeds)]

        population = [cem.sample(rng) for _ in range(args.pop)]
        # Elitism: designer preset in gen 0, best-so-far afterwards.
        population[0] = dict(baseline) if gen == 0 else dict(best_params)

        records = evaluate_population(
            population, seeds,
            job_id=args.job,
            generation=gen,
            solver_depth=args.solver_depth,
            solver_prune=args.solver_prune,
            max_encounters=args.max_encounters,
            weights=weights,
            workers=args.workers,
            data_path=args.data,
            adaptive=args.adaptive,
        )

        with gen_path.open("a") as fh:
            for rec in records:
                fh.write(rec.model_dump_json() + "\n")

        ranked = sorted(records, key=lambda r: r.mean_fitness, reverse=True)
        gen_best = ranked[0]
        if gen_best.mean_fitness > best_fitness:
            best_fitness = gen_best.mean_fitness
            best_params = dict(gen_best.params)
            best_path.write_text(json.dumps({
                "job": args.job,
                "generation": gen,
                "mean_fitness": best_fitness,
                "win_rate": gen_best.win_rate,
                "mean_zones": gen_best.mean_zones,
                "params": best_params,
                "baseline_params": baseline,
            }, indent=2))

        n_elite = max(2, int(args.pop * args.elite_frac))
        cem.refit(
            [r.params for r in ranked[:n_elite]],
            smoothing=args.smoothing,
            std_floor=args.std_floor,
        )

        dt = time.time() - t0
        mean_fit = sum(r.mean_fitness for r in records) / len(records)
        emitter.emit(
            "generation",
            gen=gen,
            best=round(gen_best.mean_fitness, 1),
            pop_mean=round(mean_fit, 1),
            best_ever=round(best_fitness, 1),
            win_rate=round(gen_best.win_rate, 3),
        )
        print(
            f"  gen {gen}: best={gen_best.mean_fitness:7.1f} "
            f"(win={gen_best.win_rate:.0%} zones={gen_best.mean_zones:.1f}) "
            f"pop_mean={mean_fit:7.1f} "
            f"best_ever={best_fitness:7.1f} [{dt/60:.1f} min]",
            flush=True,
        )

    # ------------------------------------------------------------------
    # Final holdout: best vs preset on fresh seeds at verification depth.
    # ------------------------------------------------------------------
    if args.final_seeds > 0:
        print(f"\nFinal holdout: {args.final_seeds} fresh seeds "
              f"at depth {args.final_depth} — best vs preset...")
        emitter.emit("phase", label="holdout")
        holdout = [
            args.seed_base + 100_000 + i for i in range(args.final_seeds)
        ]
        final_records = evaluate_population(
            [dict(baseline), dict(best_params)], holdout,
            job_id=args.job,
            generation=-1,
            solver_depth=args.final_depth,
            solver_prune=args.solver_prune,
            max_encounters=args.max_encounters,
            weights=weights,
            workers=args.workers,
            data_path=args.data,
            adaptive=args.adaptive,
        )
        preset_rec, best_rec = final_records[0], final_records[1]
        payload = {
            "job": args.job,
            "holdout_seeds": holdout,
            "solver_depth": args.final_depth,
            "preset": preset_rec.model_dump(),
            "optimized": best_rec.model_dump(),
        }
        (out_dir / "final_eval.json").write_text(json.dumps(payload, indent=2))
        print(f"  preset:    fitness={preset_rec.mean_fitness:7.1f} "
              f"win={preset_rec.win_rate:.0%} zones={preset_rec.mean_zones:.1f}")
        print(f"  optimized: fitness={best_rec.mean_fitness:7.1f} "
              f"win={best_rec.win_rate:.0%} zones={best_rec.mean_zones:.1f}")

    print("\nBest parameters vs preset (changed only):")
    for spec in PARAM_SPECS:
        b, p = best_params[spec.name], baseline[spec.name]
        if b != p:
            print(f"  {spec.name:28s} {p!r:>8} → {b!r}")
    print(f"\nDone. Artifacts in {out_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CEM optimizer over golden-macro + rollout policy knobs",
    )
    ap.add_argument("--job", required=True)
    ap.add_argument("--pop", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=8,
                    help="Seeds per candidate per generation (CRN within a gen)")
    ap.add_argument("--gens", type=int, default=6)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--solver-depth", type=int, default=1,
                    help="Combat solver depth during optimization (cheap)")
    ap.add_argument("--adaptive", action="store_true",
                    help="Adaptive solver depth: full depth on dangerous fights only")
    ap.add_argument("--solver-prune", type=int, default=20)
    ap.add_argument("--max-encounters", type=int, default=200)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--fixed-seeds", action="store_true",
                    help="Use the same seed block every generation")
    ap.add_argument("--cem-seed", type=int, default=7)
    ap.add_argument("--init-std", type=float, default=0.20)
    ap.add_argument("--elite-frac", type=float, default=0.25)
    ap.add_argument("--smoothing", type=float, default=0.7)
    ap.add_argument("--std-floor", type=float, default=0.05)
    ap.add_argument("--final-seeds", type=int, default=24,
                    help="Holdout seeds for the closing best-vs-preset eval")
    ap.add_argument("--final-depth", type=int, default=3,
                    help="Solver depth for the holdout eval")
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="")
    optimize(ap.parse_args())


if __name__ == "__main__":
    main()
