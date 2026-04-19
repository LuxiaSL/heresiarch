"""Policy-driven full-run simulator.

Provides:
  - Snapshot/restore primitives for RunState and CombatState.
  - CombatPolicy / MacroPolicy protocols (strategy for per-turn and macro
    decisions).
  - Validation layer that coerces illegal policy outputs into legal ones.
  - Built-in floor (trivial) and default-macro policies.

The run driver lives in heresiarch.tools.run_driver — this package is the
engine-adjacent logic, deliberately separated from CLI and I/O.
"""
