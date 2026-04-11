"""All game formulas. Pure functions, no side effects.

Every function takes explicit arguments — no hidden state.
Constants are module-level for easy tuning.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from heresiarch.engine.models.combat_state import StatusEffect
from heresiarch.engine.models.items import (
    ConversionEffect,
    Item,
    ItemScaling,
    ScalingType,
)
from heresiarch.engine.models.stats import GrowthVector, StatBlock, StatType

if TYPE_CHECKING:
    from heresiarch.engine.models.jobs import JobTemplate

# --- Tunable Constants ---

HP_COEFFICIENT: float = 1.5
DEF_REDUCTION_RATIO: float = 0.5
RES_THRESHOLD_RATIO: float = 0.7
SPD_THRESHOLD: int = 100
SURVIVE_DAMAGE_REDUCTION: float = 0.5
PARTIAL_ACTION_DAMAGE_RATIO: float = 0.5
MAX_ACTION_POINT_BANK: int = 3
CHEAT_DEBT_PER_ACTION: int = 1
CHEAT_DEBT_RECOVERY_PER_TURN: int = 1

# Combat modifier constants
FRENZY_BASE: float = 1.5  # exponential base for chain multiplier
INSIGHT_MULTIPLIER_PER_STACK: float = 0.4
THORNS_SCALING_PER_TIER: float = 0.2
THORNS_TIER_LEVELS: int = 10
MARK_DAMAGE_BONUS: float = 1.25
VENGEANCE_DEFAULT_DURATION: int = 4


# --- HP ---


def calculate_max_hp(
    base_hp: int,
    hp_growth: int,
    level: int,
    effective_def: int,
    hp_coefficient: float = HP_COEFFICIENT,
) -> int:
    """HP = base_hp + (hp_growth * level) + (DEF * hp_coefficient)"""
    return base_hp + (hp_growth * level) + int(effective_def * hp_coefficient)


# --- Stats at Level ---


def calculate_stats_at_level(growth: GrowthVector, level: int) -> StatBlock:
    """Compute raw stats from job growth at a given level.

    Each stat = (growth_bonus + 1) * level  (the +1 is the universal base floor)
    """
    return StatBlock(
        STR=growth.effective_growth(StatType.STR) * level,
        MAG=growth.effective_growth(StatType.MAG) * level,
        DEF=growth.effective_growth(StatType.DEF) * level,
        RES=growth.effective_growth(StatType.RES) * level,
        SPD=growth.effective_growth(StatType.SPD) * level,
    )


# --- Physical Damage ---


def calculate_physical_damage(
    ability_base: int,
    ability_coefficient: float,
    attacker_str: int,
    target_def: int,
    item_scaling_bonus: float = 0.0,
    pierce_percent: float = 0.0,
    def_reduction_ratio: float = DEF_REDUCTION_RATIO,
) -> int:
    """Calculate physical damage after DEF reduction.

    raw = ability_base + (coefficient * STR) + item_scaling_bonus
    reduction = target_DEF * def_reduction_ratio * (1 - pierce_percent)
    damage = max(1, raw - reduction)
    """
    raw = ability_base + (ability_coefficient * attacker_str) + item_scaling_bonus
    effective_def = target_def * def_reduction_ratio * (1.0 - pierce_percent)
    return max(1, int(raw - effective_def))


# --- Magical Damage ---


def calculate_magical_damage(
    ability_base: int,
    ability_coefficient: float,
    attacker_mag: int,
    item_scaling_bonus: float = 0.0,
) -> int:
    """Calculate magical damage. No flat reduction from RES.

    raw = ability_base + (coefficient * MAG) + item_scaling_bonus
    """
    return max(1, int(ability_base + (ability_coefficient * attacker_mag) + item_scaling_bonus))


# --- RES Threshold Gate ---


def check_res_gate(
    target_res: int,
    caster_mag: int,
    threshold_ratio: float = RES_THRESHOLD_RATIO,
) -> bool:
    """Check if secondary effects are RESISTED (blocked).

    Returns True if effects are resisted.
    Gate passes when target_RES >= caster_MAG * threshold_ratio.
    """
    return target_res >= caster_mag * threshold_ratio


# --- SPD Bonus Actions ---


def calculate_bonus_actions(
    effective_spd: int,
    spd_threshold: int = SPD_THRESHOLD,
) -> int:
    """bonus_actions = floor(SPD / threshold)"""
    return effective_spd // spd_threshold


# --- Item Scaling ---


def evaluate_item_scaling(scaling: ItemScaling, stat_value: int) -> float:
    """Evaluate an item's scaling formula given the relevant stat value.

    LINEAR:       base + linear_coeff * STAT
    SUPERLINEAR:  base + linear_coeff * STAT + quadratic_coeff * STAT^2
    QUADRATIC:    base + quadratic_coeff * STAT^2
    DEGENERATE:   constant_offset + quadratic_coeff * STAT^2
    FLAT:         base (no scaling)
    """
    match scaling.scaling_type:
        case ScalingType.LINEAR:
            return scaling.base + scaling.linear_coeff * stat_value
        case ScalingType.SUPERLINEAR:
            return (
                scaling.base
                + scaling.linear_coeff * stat_value
                + scaling.quadratic_coeff * stat_value**2
            )
        case ScalingType.QUADRATIC:
            return scaling.base + scaling.quadratic_coeff * stat_value**2
        case ScalingType.DEGENERATE:
            return scaling.constant_offset + scaling.quadratic_coeff * stat_value**2
        case ScalingType.FLAT:
            return scaling.base
        case _:
            return 0.0


def evaluate_conversion(conversion: ConversionEffect, source_stat_value: int) -> int:
    """Evaluate a converter item's bonus to the target stat."""
    match conversion.scaling_type:
        case ScalingType.LINEAR:
            return int(conversion.linear_coeff * source_stat_value)
        case ScalingType.SUPERLINEAR:
            return int(
                conversion.linear_coeff * source_stat_value
                + conversion.quadratic_coeff * source_stat_value**2
            )
        case ScalingType.QUADRATIC:
            return int(conversion.quadratic_coeff * source_stat_value**2)
        case ScalingType.SIGMOID:
            return _sigmoid(
                source_stat_value,
                conversion.sigmoid_max,
                conversion.sigmoid_mid,
                conversion.sigmoid_rate,
            )
        case _:
            return 0


def _sigmoid(stat_value: int, max_output: float, midpoint: float, rate: float) -> int:
    """Bounded S-curve: output = max_output / (1 + exp(-rate * (stat - midpoint))).

    Grows roughly linearly around the midpoint, flattens toward 0 and max_output.
    """
    try:
        exponent = -rate * (stat_value - midpoint)
        # Clamp exponent to avoid overflow in exp()
        exponent = max(-500.0, min(500.0, exponent))
        return int(max_output / (1.0 + math.exp(exponent)))
    except OverflowError:
        return 0 if stat_value < midpoint else int(max_output)


# --- Survive Damage Reduction ---


def calculate_frenzy_multiplier(
    chain: int,
    base: float = FRENZY_BASE,
) -> float:
    """Frenzy chain multiplier: base^chain (e.g., 1.5^3 = 3.375)."""
    return base ** chain


def calculate_insight_multiplier(
    stacks: int,
    per_stack: float = INSIGHT_MULTIPLIER_PER_STACK,
) -> float:
    """Insight damage/buff amplification: 1.0 + per_stack * stacks."""
    return 1.0 + per_stack * stacks


def calculate_thorns_percent(
    base_percent: float,
    level: int,
    scaling_per_tier: float = THORNS_SCALING_PER_TIER,
    tier_levels: int = THORNS_TIER_LEVELS,
) -> float:
    """Thorns reflect percent, scaling with level tiers."""
    return base_percent + scaling_per_tier * (level // tier_levels)


def apply_survive_reduction(
    damage: int,
    is_surviving: bool,
    reduction: float = SURVIVE_DAMAGE_REDUCTION,
) -> int:
    """Survive halves incoming damage."""
    if is_surviving:
        return max(1, int(damage * (1.0 - reduction)))
    return damage


# --- Partial Action Damage ---


def apply_partial_action_modifier(
    damage: int,
    is_partial: bool,
    ratio: float = PARTIAL_ACTION_DAMAGE_RATIO,
) -> int:
    """SPD bonus actions deal reduced damage."""
    if is_partial:
        return max(1, int(damage * ratio))
    return damage


# --- Enemy Stat Budget ---


def calculate_enemy_stats(
    zone_level: int,
    budget_multiplier: float,
    stat_distribution: dict[str, float],
) -> StatBlock:
    """Calculate enemy stats from zone level and archetype template.

    Total budget = zone_level * budget_multiplier.
    Distribute across stats by ratios.
    """
    total_budget = int(zone_level * budget_multiplier)
    return StatBlock(
        STR=int(total_budget * stat_distribution.get("STR", 0.0)),
        MAG=int(total_budget * stat_distribution.get("MAG", 0.0)),
        DEF=int(total_budget * stat_distribution.get("DEF", 0.0)),
        RES=int(total_budget * stat_distribution.get("RES", 0.0)),
        SPD=int(total_budget * stat_distribution.get("SPD", 0.0)),
    )


def calculate_enemy_hp(
    zone_level: int,
    budget_multiplier: float,
    base_hp: int,
    hp_per_budget: float,
) -> int:
    """Calculate enemy HP from zone level and template."""
    total_budget = int(zone_level * budget_multiplier)
    return base_hp + int(total_budget * hp_per_budget)


# --- Effective Stats (with equipment and buffs) ---


def calculate_effective_stats(
    base_stats: StatBlock,
    equipped_items: list[Item],
    active_buffs: list[StatusEffect],
) -> StatBlock:
    """Compute effective stats by layering:

    Layer 1: Base stats (from level-ups)
    Layer 2: + flat item bonuses → "augmented base" (feeds into Layer 3 scaling)
    Layer 3: + weapon/item scaling (reads augmented base, adds to effective)
    Layer 4: + converters (reads current effective, adds to effective)
             + buff/debuff modifiers

    No feedback loops: each layer only reads from layers above it.
    """
    data = base_stats.model_dump()

    # --- Layer 2: Flat bonuses (e.g., Endurance Plate: DEF +10) ---
    # These increase the "augmented base" that weapon scaling reads from.
    for item in equipped_items:
        for stat_name, bonus in item.flat_stat_bonus.items():
            if stat_name in data:
                data[stat_name] += bonus

    # Snapshot augmented base for scaling input
    augmented_base = StatBlock(**{k: max(0, v) for k, v in data.items()})

    # --- Layer 3: Weapon/item scaling → stat boost ---
    # Reads from augmented base (Layer 1+2), output added to effective stat.
    # e.g., Iron Blade (LINEAR STR, base=20, coeff=1.0) at augmented STR 10 → +30 STR
    for item in equipped_items:
        if item.scaling:
            stat_key = item.scaling.stat.value
            if stat_key in data:
                stat_value = augmented_base.get(StatType(stat_key))
                scaling_bonus = int(evaluate_item_scaling(item.scaling, stat_value))
                data[stat_key] += scaling_bonus

    # --- Layer 4: Converters + buffs/debuffs ---
    # Converters read from current effective (Layer 1+2+3), add to effective.
    effective_snapshot = StatBlock(**{k: max(0, v) for k, v in data.items()})
    for item in equipped_items:
        if item.conversion:
            source_val = effective_snapshot.get(StatType(item.conversion.source_stat.value))
            bonus = evaluate_conversion(item.conversion, source_val)
            target_key = item.conversion.target_stat.value
            if target_key in data:
                data[target_key] += bonus

    # Buffs/debuffs (Layer 4 — temporary combat modifiers)
    for buff in active_buffs:
        for stat_name, mod in buff.stat_modifiers.items():
            if stat_name in data:
                data[stat_name] += mod

    return StatBlock(**{k: max(0, v) for k, v in data.items()})


# --- XP / Leveling ---

XP_THRESHOLD_BASE: int = 10
XP_THRESHOLD_EXPONENT: float = 2.0
XP_OVERLEVEL_PENALTY_PER_LEVEL: float = 0.5
XP_MINIMUM_RATIO: float = 0.1


def calculate_xp_reward(
    zone_level: int,
    budget_multiplier: float,
    character_level: int,
    xp_cap_level: int = 0,
) -> int:
    """XP from one enemy kill.

    base_xp = zone_level * budget_multiplier.
    If character_level > xp_cap_level (and cap > 0), apply diminishing returns:
    50% reduction per level over, floored at 10% of base.
    """
    base_xp = int(zone_level * budget_multiplier)
    if xp_cap_level > 0 and character_level > xp_cap_level:
        levels_over = character_level - xp_cap_level
        ratio = max(
            XP_MINIMUM_RATIO,
            (1.0 - XP_OVERLEVEL_PENALTY_PER_LEVEL) ** levels_over,
        )
        return max(1, int(base_xp * ratio))
    return base_xp


def xp_for_level(level: int) -> int:
    """Cumulative XP needed to reach a given level.

    Level 1 = 0 XP (starting level).
    xp = level^2 * XP_THRESHOLD_BASE for level >= 2.
    """
    if level <= 1:
        return 0
    return int(level**XP_THRESHOLD_EXPONENT * XP_THRESHOLD_BASE)


def calculate_levels_gained(current_xp: int, current_level: int) -> int:
    """Given current total XP and level, return how many levels to gain."""
    levels = 0
    check_level = current_level + 1
    while check_level <= 99 and current_xp >= xp_for_level(check_level):
        levels += 1
        check_level += 1
    return levels


def calculate_stats_from_history(
    growth_history: list[tuple[str, int]],
    job_registry: dict[str, JobTemplate],
) -> StatBlock:
    """Compute stats from a sequence of job growth segments.

    Each segment = (job_id, levels_spent). Stats accumulate across segments
    using each job's growth vector for its levels.
    """
    totals: dict[str, int] = {"STR": 0, "MAG": 0, "DEF": 0, "RES": 0, "SPD": 0}
    for job_id, levels_spent in growth_history:
        job = job_registry[job_id]
        for stat in StatType:
            totals[stat.value] += job.growth.effective_growth(stat) * levels_spent
    return StatBlock(**totals)


# --- Shop Pricing ---

CHA_PRICE_MODIFIER_PER_POINT: float = 0.005
CHA_PRICE_MIN_RATIO: float = 0.5
CHA_PRICE_MAX_RATIO: float = 1.5
SELL_RATIO: float = 0.4


def calculate_buy_price(base_price: int, cha: int) -> int:
    """Buy price = base_price * clamp(1.0 - 0.005 * CHA, 0.5, 1.5)."""
    ratio = max(
        CHA_PRICE_MIN_RATIO,
        min(CHA_PRICE_MAX_RATIO, 1.0 - CHA_PRICE_MODIFIER_PER_POINT * cha),
    )
    return max(1, int(base_price * ratio))


def calculate_sell_price(base_price: int) -> int:
    """Sell price = base_price * SELL_RATIO."""
    return max(1, int(base_price * SELL_RATIO))


# --- Money Drops ---

MONEY_DROP_MIN_MULTIPLIER: int = 5
MONEY_DROP_MAX_MULTIPLIER: int = 15


def calculate_money_drop(zone_level: int, rng: random.Random) -> int:
    """money = zone_level * rng.randint(5, 15)."""
    return zone_level * rng.randint(MONEY_DROP_MIN_MULTIPLIER, MONEY_DROP_MAX_MULTIPLIER)
