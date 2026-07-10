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
from typing import TYPE_CHECKING, Callable

from heresiarch.policy.features import FEATURES_VERSION, combat_features

if TYPE_CHECKING:
    from heresiarch.engine.models.combat_state import CombatState

logger = logging.getLogger(__name__)

# (state, mc_job_id, stash_potions, stash_size) -> value in [0, 2].
# Stash context comes from the caller (v2 features): the solver counts
# the branch stash at the leaf; CombatState doesn't know the stash.
CombatValueFn = Callable[["CombatState", str, int, int], float]

# Tracks FEATURES_VERSION because the trainer stamps the version into
# the artifact filename — a hardcoded name silently points at a stale
# model after a version bump (the loader then rejects it and every
# --leaf-eval model run fail-fasts).
DEFAULT_MODEL_PATH = Path(
    f"artifacts/models/combat_value_v{FEATURES_VERSION}.pkl"
)

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

    model = payload["model"]

    def value_fn(
        state: CombatState, mc_job_id: str,
        stash_potions: int = 0, stash_size: int = 0,
    ) -> float:
        x = combat_features(
            state, mc_job_id,
            stash_potions=stash_potions, stash_size=stash_size,
        )
        v = float(model.predict([x])[0])
        if not math.isfinite(v):
            raise ValueError(f"model predicted non-finite value {v!r}")
        return min(2.0, max(0.0, v))

    return value_fn
