"""Learned combat value function: model artifact loading + inference.

Rung 1 of the learned-evaluation ladder (design/learned-value-spec.md).
A trained regressor (tools/train_value.py) predicts the terminal value
of a mid-combat state on ``evaluate_terminal``'s [0, 2] scale, replacing
heuristic rollout at solver leaves when ``SolverConfig.leaf_eval ==
"model"``.

This module must stay importable without sklearn installed: the model
is unpickled lazily and every failure path returns None so callers can
fall back to rollout. A missing model must never break a sim.
"""

from __future__ import annotations

import logging
import math
import pickle
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence

from heresiarch.policy.features import FEATURES_VERSION, combat_features

if TYPE_CHECKING:
    from heresiarch.engine.models.combat_state import CombatState

logger = logging.getLogger(__name__)

# (state, mc_job_id) -> predicted terminal value in [0, 2]
CombatValueFn = Callable[["CombatState", str], float]


class ModelValueFn:
    """Trained-model CombatValueFn with a batched variant.

    ``__call__`` keeps the original one-state contract. ``value_batch``
    scores N states with a single ``model.predict`` call — sklearn's
    per-call overhead dominates single-row prediction (~0.21ms/row
    serial vs ~0.01ms/row batched), so the solver collects leaves and
    predicts once per decision (see solver._score_deferred_leaves).

    Both paths clamp to evaluate_terminal's [0, 2] scale and raise
    ``ValueError`` on non-finite predictions so callers can trip their
    rollback-to-rollout handling.
    """

    def __init__(self, model: Any) -> None:
        self._model = model

    def __call__(self, state: CombatState, mc_job_id: str) -> float:
        return self.value_batch([state], mc_job_id)[0]

    def value_batch(
        self, states: Sequence[CombatState], mc_job_id: str,
    ) -> list[float]:
        if not states:
            return []
        xs = [combat_features(s, mc_job_id) for s in states]
        preds = self._model.predict(xs)
        out: list[float] = []
        for v in preds:
            fv = float(v)
            if not math.isfinite(fv):
                raise ValueError(f"model predicted non-finite value {fv!r}")
            out.append(min(2.0, max(0.0, fv)))
        if len(out) != len(states):
            raise ValueError(
                f"model returned {len(out)} predictions for "
                f"{len(states)} states"
            )
        return out

DEFAULT_MODEL_PATH = Path("artifacts/models/combat_value_v1.pkl")

# Per-process cache: multiprocessing workers each load the artifact
# once instead of per (candidate, seed) task. None results are cached
# too so a broken artifact warns once, not once per eval.
_CACHE: dict[str, CombatValueFn | None] = {}


def load_combat_value_fn(
    path: str | Path = DEFAULT_MODEL_PATH,
) -> CombatValueFn | None:
    """Load a trained combat value model; None on any failure.

    Failure modes handled: file missing, sklearn not installed (the
    pickle references sklearn classes), wrong artifact kind, feature
    version mismatch. Each logs one warning and returns None so the
    solver falls back to heuristic rollout.
    """
    key = str(path)
    if key in _CACHE:
        return _CACHE[key]
    fn = _load_uncached(Path(path))
    _CACHE[key] = fn
    return fn


def _load_uncached(path: Path) -> CombatValueFn | None:
    if not path.exists():
        logger.warning(
            "Combat value model not found at %s — solver will use "
            "heuristic rollout leaves.", path,
        )
        return None
    try:
        with path.open("rb") as fh:
            payload = pickle.load(fh)
    except (ImportError, ModuleNotFoundError) as exc:
        logger.warning(
            "Combat value model at %s needs missing ML deps (%s). "
            "Install the 'ml' dependency group: uv sync --group ml",
            path, exc,
        )
        return None
    except Exception as exc:  # noqa: BLE001 — corrupt artifact must not crash
        logger.warning("Failed to load combat value model %s: %s", path, exc)
        return None

    if not isinstance(payload, dict) or "model" not in payload:
        logger.warning(
            "Artifact %s is not a value-model payload (expected dict "
            "with 'model' key).", path,
        )
        return None
    if payload.get("kind") != "combat":
        logger.warning(
            "Artifact %s has kind=%r, expected 'combat'.",
            path, payload.get("kind"),
        )
        return None
    version = payload.get("features_version")
    if version != FEATURES_VERSION:
        logger.warning(
            "Artifact %s was trained on features v%s but this code is "
            "v%s — retrain with tools/train_value.py.",
            path, version, FEATURES_VERSION,
        )
        return None

    return ModelValueFn(payload["model"])
