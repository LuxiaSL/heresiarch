"""Snapshot/restore primitives for RunState and CombatState.

Both snapshots capture the pydantic state plus the RNG state at the
moment of capture. Restore reconstructs an engine-equivalent tuple of
(state, rng) that can resume execution indistinguishably from the
original.

RunSnapshot is the coarse snapshot used for between-encounter rollbacks
and full-run forks. CombatSnapshot is the fine-grained snapshot used for
mid-combat lookahead (MCTS will use this in Phase 4).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from heresiarch.engine.models.combat_state import CombatState
from heresiarch.engine.models.run_state import RunState

if TYPE_CHECKING:
    from heresiarch.engine.game_loop import GameLoop


@dataclass(frozen=True)
class RunSnapshot:
    """Immutable snapshot of a run + its RNG state."""

    run_state_dump: dict[str, Any]
    rng_state: tuple[Any, ...]

    @classmethod
    def take(cls, run: RunState, rng: random.Random) -> RunSnapshot:
        return cls(
            run_state_dump=run.model_dump(mode="python"),
            rng_state=rng.getstate(),
        )

    def restore(
        self, game_loop: GameLoop | None = None
    ) -> tuple[RunState, random.Random]:
        """Reconstruct (run_state, rng) from the snapshot.

        If ``game_loop`` is provided, the restored run is passed through
        ``rehydrate_run`` so derived fields (effective_stats, max_hp) are
        recomputed against the current game data. Pass None only when
        you know the snapshot was taken with matching game data and you
        don't need rehydration.
        """
        rng = random.Random()
        rng.setstate(self.rng_state)
        run = RunState.model_validate(self.run_state_dump)
        if game_loop is not None:
            run = game_loop.rehydrate_run(run)
        return run, rng


@dataclass(frozen=True)
class CombatSnapshot:
    """Immutable snapshot of a CombatState + its RNG state.

    Combat state is fully self-contained (no derived fields depend on
    game data), so restore is a straight model_validate + RNG restore.
    """

    combat_state_dump: dict[str, Any]
    rng_state: tuple[Any, ...]

    @classmethod
    def take(cls, state: CombatState, rng: random.Random) -> CombatSnapshot:
        return cls(
            combat_state_dump=state.model_dump(mode="python"),
            rng_state=rng.getstate(),
        )

    def restore(self) -> tuple[CombatState, random.Random]:
        rng = random.Random()
        rng.setstate(self.rng_state)
        state = CombatState.model_validate(self.combat_state_dump)
        return state, rng
