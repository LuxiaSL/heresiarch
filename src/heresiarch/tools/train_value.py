"""Train learned value models from data-tap shards.

Rung 1 of the learned-evaluation ladder (design/learned-value-spec.md):
a gradient-boosted regressor maps combat feature vectors (130 dims,
policy/features.py) onto the terminal value each state actually became,
on ``evaluate_terminal``'s [0, 2] scale. The artifact plugs into solver
leaves via ``--leaf-eval model`` (policy/value_model.py).

Also trains the rung-2 macro head (17 dims → zones_ahead) from the same
shards; it costs nothing extra and is the input to macro lookahead.

Usage:
    uv run python -m heresiarch.tools.train_value --data artifacts/tapdata
    uv run python -m heresiarch.tools.train_value --data DIR --kind combat

Requires the ``ml`` dependency group: ``uv sync --group ml``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from heresiarch.policy.features import (
    FEATURES_VERSION,
    combat_feature_names,
    macro_feature_names,
)

# Seeds with (seed % HOLDOUT_MOD == 0) are held out — splitting by seed,
# not by row, keeps all rounds of one fight (and all encounters of one
# run) on the same side, so the test metric measures generalization to
# new runs rather than interpolation within a seen fight.
HOLDOUT_MOD = 5

TARGETS = {"combat": "value", "macro": "zones_ahead"}
FEATURE_NAMES = {
    "combat": combat_feature_names,
    "macro": macro_feature_names,
}


@dataclass
class Dataset:
    """Rows of one kind, split by seed into train/test."""

    x_train: list[list[float]] = field(default_factory=list)
    y_train: list[float] = field(default_factory=list)
    x_test: list[list[float]] = field(default_factory=list)
    y_test: list[float] = field(default_factory=list)
    won_test: list[bool] = field(default_factory=list)
    job_test: list[str] = field(default_factory=list)
    jobs: Counter = field(default_factory=Counter)
    skipped: int = 0


def load_shards(data_dir: Path, kind: str) -> Dataset:
    """Stream every tap_*.jsonl.gz shard into a seed-split dataset.

    Torn lines (concurrent writers) and version-mismatched rows are
    skipped, never fatal.
    """
    target_key = TARGETS[kind]
    n_features = len(FEATURE_NAMES[kind]())
    ds = Dataset()

    shards = sorted(data_dir.glob("tap_*.jsonl.gz"))
    if not shards:
        raise SystemExit(f"No tap_*.jsonl.gz shards found in {data_dir}")

    for shard in shards:
        try:
            with gzip.open(shard, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        ds.skipped += 1
                        continue
                    if (
                        row.get("kind") != kind
                        or row.get("v") != FEATURES_VERSION
                    ):
                        continue
                    x = row.get("x")
                    y = row.get("y", {}).get(target_key)
                    if (
                        not isinstance(x, list)
                        or len(x) != n_features
                        or y is None
                    ):
                        ds.skipped += 1
                        continue
                    seed = int(row.get("seed", 0))
                    job = str(row.get("job", "?"))
                    ds.jobs[job] += 1
                    if seed % HOLDOUT_MOD == 0:
                        ds.x_test.append(x)
                        ds.y_test.append(float(y))
                        ds.won_test.append(bool(row["y"].get("won", False)))
                        ds.job_test.append(job)
                    else:
                        ds.x_train.append(x)
                        ds.y_train.append(float(y))
        except (OSError, EOFError) as exc:
            # A shard truncated mid-write (fleet still running) is data
            # we simply don't get to use today.
            print(f"  [warn] unreadable shard {shard.name}: {exc}")

    return ds


def build_model(model_kind: str, max_iter: int):
    """Regressor backends.

    hist_gbt: best tabular accuracy, but single-row predict pays ~3ms
    of per-tree Python dispatch — fine for training-time metrics, slow
    inside the solver's leaf loop. mlp: a couple of matmuls per predict
    (~40x faster single-row), features are already normalized to [0,1]
    so no scaler is needed.
    """
    if model_kind == "mlp":
        from sklearn.neural_network import MLPRegressor
        return MLPRegressor(
            hidden_layer_sizes=(128, 64),
            early_stopping=True,
            n_iter_no_change=5,
            max_iter=max(50, max_iter),
            random_state=42,
        )
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(
        max_iter=max_iter, early_stopping=True, random_state=42,
    )


def train_kind(
    kind: str,
    data_dir: Path,
    out_dir: Path,
    *,
    max_iter: int,
    importance_rows: int,
    model_kind: str = "hist_gbt",
) -> dict | None:
    """Train one head; returns its sidecar metadata (None if no data)."""
    from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score

    t0 = time.time()
    print(f"\n=== {kind} head (target: {TARGETS[kind]}, "
          f"model: {model_kind}) ===")
    ds = load_shards(data_dir, kind)
    print(
        f"  rows: {len(ds.x_train)} train / {len(ds.x_test)} test "
        f"(seed % {HOLDOUT_MOD} == 0 held out), {ds.skipped} skipped"
    )
    print(f"  jobs: {dict(sorted(ds.jobs.items()))}")
    if not ds.x_train or not ds.x_test:
        print(f"  [warn] not enough data for a {kind} model — skipping")
        return None

    model = build_model(model_kind, max_iter)
    model.fit(ds.x_train, ds.y_train)
    pred = model.predict(ds.x_test)

    metrics: dict[str, object] = {
        "r2": round(float(r2_score(ds.y_test, pred)), 4),
        "mae": round(float(mean_absolute_error(ds.y_test, pred)), 4),
        "n_train": len(ds.x_train),
        "n_test": len(ds.x_test),
        "rows_skipped": ds.skipped,
    }
    if kind == "combat" and len(set(ds.won_test)) == 2:
        # Predicted value as a win score — sanity metric, not the target.
        metrics["auc_won"] = round(
            float(roc_auc_score(ds.won_test, pred)), 4,
        )

    per_job: dict[str, dict[str, object]] = {}
    for job in sorted(set(ds.job_test)):
        idx = [i for i, j in enumerate(ds.job_test) if j == job]
        yj = [ds.y_test[i] for i in idx]
        pj = [float(pred[i]) for i in idx]
        entry: dict[str, object] = {
            "n_test": len(idx),
            "mae": round(float(mean_absolute_error(yj, pj)), 4),
        }
        if len(set(yj)) > 1:
            entry["r2"] = round(float(r2_score(yj, pj)), 4)
        wj = [ds.won_test[i] for i in idx]
        if kind == "combat" and len(set(wj)) == 2:
            entry["auc_won"] = round(float(roc_auc_score(wj, pj)), 4)
        per_job[job] = entry
    metrics["per_job"] = per_job

    importances = _top_importances(
        model, ds, FEATURE_NAMES[kind](), importance_rows,
    )

    print(f"  overall: {metrics['r2']=} {metrics['mae']=} "
          f"auc_won={metrics.get('auc_won', 'n/a')}")
    for job, m in per_job.items():
        print(f"    {job:<12} {m}")
    print("  top features:")
    for name, imp in importances[:10]:
        print(f"    {imp:8.4f}  {name}")

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{kind}_value_v{FEATURES_VERSION}"
    payload = {
        "model": model,
        "kind": kind,
        "model_kind": model_kind,
        "features_version": FEATURES_VERSION,
        "feature_names": FEATURE_NAMES[kind](),
        "target": TARGETS[kind],
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "metrics": metrics,
    }
    model_path = out_dir / f"{stem}.pkl"
    with model_path.open("wb") as fh:
        pickle.dump(payload, fh)

    sidecar = {k: v for k, v in payload.items() if k != "model"}
    sidecar["top_importances"] = [
        {"feature": n, "importance": round(i, 5)} for n, i in importances
    ]
    (out_dir / f"{stem}.json").write_text(json.dumps(sidecar, indent=2))
    print(f"  saved {model_path} (+ .json sidecar) "
          f"[{time.time() - t0:.0f}s]")
    return sidecar


def _top_importances(
    model,
    ds: Dataset,
    names: list[str],
    max_rows: int,
) -> list[tuple[str, float]]:
    """Permutation importance on a test subsample, top 20.

    HistGBT has no native feature_importances_; permutation importance
    is model-agnostic and directly answers the designer question
    "what is the model actually looking at?".
    """
    from sklearn.inspection import permutation_importance

    step = max(1, len(ds.x_test) // max_rows)
    xs = ds.x_test[::step]
    ys = ds.y_test[::step]
    try:
        result = permutation_importance(
            model, xs, ys, n_repeats=3, random_state=42,
        )
    except Exception as exc:  # noqa: BLE001 — importances are a nicety
        print(f"  [warn] permutation importance failed: {exc}")
        return []
    pairs = sorted(
        zip(names, (float(v) for v in result.importances_mean)),
        key=lambda p: p[1],
        reverse=True,
    )
    return pairs[:20]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default="artifacts/tapdata",
                    help="Directory of tap_*.jsonl.gz shards")
    ap.add_argument("--out", default="artifacts/models",
                    help="Output directory for model artifacts")
    ap.add_argument("--kind", choices=("combat", "macro", "both"),
                    default="both")
    ap.add_argument("--model", choices=("hist_gbt", "mlp"),
                    default="mlp", dest="model_kind",
                    help="Regressor backend. mlp (default): ~0.2ms "
                         "single-row predict, right for solver leaves. "
                         "hist_gbt: same accuracy, ~4.8ms/row (300 "
                         "per-tree Python calls) — analysis only.")
    ap.add_argument("--max-iter", type=int, default=300,
                    help="Boosting iterations / MLP epochs "
                         "(early stopping on)")
    ap.add_argument("--importance-rows", type=int, default=20_000,
                    help="Test-row cap for permutation importance")
    args = ap.parse_args()

    try:
        import sklearn  # noqa: F401
    except ImportError:
        raise SystemExit(
            "scikit-learn is not installed. Run: uv sync --group ml"
        ) from None

    kinds = ("combat", "macro") if args.kind == "both" else (args.kind,)
    for kind in kinds:
        train_kind(
            kind, Path(args.data), Path(args.out),
            max_iter=args.max_iter,
            importance_rows=args.importance_rows,
            model_kind=args.model_kind,
        )


if __name__ == "__main__":
    main()
