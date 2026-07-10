"""Training-data tap: streams labeled (state, outcome) rows from sims.

Hooks into run_driver at three points:
  - every combat round  → a "combat" row (features now, labels when the
    encounter resolves: won / final party HP / rounds remaining)
  - every encounter start → a "macro" row (features now, labels when the
    run ends: zones gained from here, survival, region win)
  - run end → flush everything to a gzip JSONL shard

Labels for combat rows deliberately mirror the solver's
``evaluate_terminal`` scale so a trained value model is a drop-in
replacement for rollout leaf evaluation (see policy/solver.py).

Failure-proof by contract: every hook swallows exceptions. A broken tap
must never break a sim — but it also must not fail silently: every
swallow emits a rate-limited warning, because a quiet tap failure is
lost training data.
"""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import Any

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.combat_state import CombatState
from heresiarch.engine.models.run_state import RunState
from heresiarch.logutil import RateLimitedLogger
from heresiarch.policy.features import (
    FEATURES_VERSION,
    combat_features,
    macro_features,
)

logger = logging.getLogger(__name__)
_rate_limited = RateLimitedLogger()


def _healing_item_ids(game_data: GameData) -> frozenset[str]:
    """Item ids with any healing effect — behavioral, not name-matched."""
    out = set()
    for item_id, item in game_data.items.items():
        effect = getattr(item, "consumable_effect", None) or getattr(item, "effect", None)
        for attr in ("heal_amount", "heal_percent", "heal_flat"):
            if getattr(effect, attr, 0):
                out.add(item_id)
                break
    return frozenset(out)


class DataTap:
    """Buffers feature rows during a run, labels them, writes one shard."""

    def __init__(
        self,
        out_path: Path,
        mc_job_id: str,
        seed: int,
        game_data: GameData,
        *,
        policy_name: str = "",
    ):
        self.out_path = Path(out_path)
        self.mc_job_id = mc_job_id
        self.seed = seed
        self.policy_name = policy_name
        self.game_data = game_data
        self.healing_ids = _healing_item_ids(game_data)
        self._pending_combat: list[dict[str, Any]] = []
        self._macro_rows: list[dict[str, Any]] = []
        self._done_rows: list[dict[str, Any]] = []
        self._zones_at: list[int] = []  # zones_completed per macro row

    # -- hooks (all failure-proof) --------------------------------------

    def on_encounter_start(self, run: RunState, state: CombatState) -> None:
        try:
            zone_level = 0
            if run.current_zone_id:
                zone = self.game_data.zones.get(run.current_zone_id)
                zone_level = zone.zone_level if zone else 0
            self._macro_rows.append({
                "kind": "macro",
                "v": FEATURES_VERSION,
                "job": self.mc_job_id,
                "seed": self.seed,
                "policy": self.policy_name,
                "x": macro_features(
                    run, self.mc_job_id, zone_level, self.healing_ids,
                ),
                "y": {},  # labeled at run end
            })
            self._zones_at.append(len(run.zones_completed))
        except Exception as exc:  # noqa: BLE001 — tap must never break a sim
            _rate_limited.warning(
                logger, "tap_encounter_start",
                "DataTap.on_encounter_start failed (%s: %s) — a macro "
                "training row was lost (seed=%s).",
                type(exc).__name__, exc, self.seed,
            )

    def on_combat_round(self, state: CombatState) -> None:
        try:
            self._pending_combat.append({
                "kind": "combat",
                "v": FEATURES_VERSION,
                "job": self.mc_job_id,
                "seed": self.seed,
                "policy": self.policy_name,
                "round": state.round_number,
                "x": combat_features(state, self.mc_job_id),
                "y": {},
            })
        except Exception as exc:  # noqa: BLE001 — tap must never break a sim
            _rate_limited.warning(
                logger, "tap_combat_round",
                "DataTap.on_combat_round failed (%s: %s) — a combat "
                "training row was lost (seed=%s).",
                type(exc).__name__, exc, self.seed,
            )

    def on_encounter_end(self, state: CombatState, victorious: bool) -> None:
        try:
            players = state.player_combatants
            hp_frac = (
                sum(max(0, p.current_hp) / max(1, p.max_hp) for p in players)
                / len(players)
            ) if players else 0.0
            end_round = state.round_number
            finished = state.is_finished
            for row in self._pending_combat:
                row["y"] = {
                    "won": bool(victorious),
                    "finished": bool(finished),
                    "end_hp_frac": round(hp_frac, 4),
                    "rounds_left": end_round - row.pop("round", 0),
                    # evaluate_terminal-compatible target in [0, 2]
                    "value": round(
                        (1.0 + hp_frac) if victorious
                        else (0.5 * hp_frac if not finished else 0.0),
                        4,
                    ),
                }
                self._done_rows.append(row)
            self._pending_combat = []
        except Exception as exc:  # noqa: BLE001 — tap must never break a sim
            n_lost = len(self._pending_combat)
            self._pending_combat = []
            _rate_limited.warning(
                logger, "tap_encounter_end",
                "DataTap.on_encounter_end failed (%s: %s) — %d pending "
                "combat training row(s) dropped unlabeled (seed=%s).",
                type(exc).__name__, exc, n_lost, self.seed,
            )

    def on_run_end(self, run: RunState, won_region: bool) -> None:
        try:
            zones_final = len(run.zones_completed)
            for row, zones_then in zip(self._macro_rows, self._zones_at):
                row["y"] = {
                    "zones_ahead": zones_final - zones_then,
                    "survived": not run.is_dead,
                    "won_region": bool(won_region),
                }
                self._done_rows.append(row)
            self._macro_rows = []
            self._flush()
        except Exception as exc:  # noqa: BLE001 — tap must never break a sim
            # Worst swallow of the four: the whole shard may be lost.
            _rate_limited.warning(
                logger, "tap_run_end",
                "DataTap.on_run_end failed (%s: %s) — the training-data "
                "shard %s may be incomplete or missing entirely "
                "(seed=%s).",
                type(exc).__name__, exc, self.out_path, self.seed,
            )

    # -- output ----------------------------------------------------------

    def _flush(self) -> None:
        if not self._done_rows:
            return
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(self.out_path, "at", encoding="utf-8") as fh:
            for row in self._done_rows:
                fh.write(json.dumps(row) + "\n")
        self._done_rows = []
