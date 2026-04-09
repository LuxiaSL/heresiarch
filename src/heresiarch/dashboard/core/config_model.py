"""FormulaConfig: single Pydantic model capturing every tunable engine constant."""

from __future__ import annotations

from pydantic import BaseModel


class FormulaConfig(BaseModel):
    """All tunable formula constants across the engine.

    Defaults match the current engine values. The dashboard can override
    any subset and apply them before running simulations.
    """

    # --- formulas.py ---
    HP_COEFFICIENT: float = 1.5
    DEF_REDUCTION_RATIO: float = 0.5
    RES_THRESHOLD_RATIO: float = 0.7
    SPD_THRESHOLD: int = 100
    SURVIVE_DAMAGE_REDUCTION: float = 0.5
    PARTIAL_ACTION_DAMAGE_RATIO: float = 0.5
    MAX_ACTION_POINT_BANK: int = 3
    CHEAT_DEBT_PER_ACTION: int = 1
    CHEAT_DEBT_RECOVERY_PER_TURN: int = 1

    # XP / Leveling
    XP_THRESHOLD_BASE: int = 10
    XP_THRESHOLD_EXPONENT: float = 2.0
    XP_OVERLEVEL_PENALTY_PER_LEVEL: float = 0.5
    XP_MINIMUM_RATIO: float = 0.1

    # Shop pricing
    CHA_PRICE_MODIFIER_PER_POINT: float = 0.005
    CHA_PRICE_MIN_RATIO: float = 0.5
    CHA_PRICE_MAX_RATIO: float = 1.5
    SELL_RATIO: float = 0.4

    # Money drops
    MONEY_DROP_MIN_MULTIPLIER: int = 5
    MONEY_DROP_MAX_MULTIPLIER: int = 15

    # --- loot.py ---
    OVERSTAY_PENALTY_PER_BATTLE: float = 0.05
