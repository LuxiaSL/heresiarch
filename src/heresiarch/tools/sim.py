"""Heresiarch balance simulation tool.

A spreadsheet-style engine for testing weapon scaling, converter interactions,
build comparisons, ability balance analysis, and full run progression against
the actual game formulas.

Usage:
    python -m heresiarch.tools.sim sweep [options]
    python -m heresiarch.tools.sim crossover [options]
    python -m heresiarch.tools.sim build [options]
    python -m heresiarch.tools.sim converter [options]
    python -m heresiarch.tools.sim ability-dpr [options]
    python -m heresiarch.tools.sim ability-compare [options]
    python -m heresiarch.tools.sim job-curve [options]
    python -m heresiarch.tools.sim economy [options]
    python -m heresiarch.tools.sim xp-curve [options]
    python -m heresiarch.tools.sim enemy-stats [options]
    python -m heresiarch.tools.sim shop-pricing [options]
    python -m heresiarch.tools.sim progression [options]

Examples:
    # Sweep STR weapons across all levels for Einherjar
    python -m heresiarch.tools.sim sweep --job einherjar --stat STR

    # Find weapon crossover levels
    python -m heresiarch.tools.sim crossover --job einherjar --stat STR

    # Compare builds at a specific level
    python -m heresiarch.tools.sim build --job berserker --level 50

    # Test converter with different scaling types
    python -m heresiarch.tools.sim converter --job martyr --converter fortress_ring

    # Test hypothetical weapon coefficients
    python -m heresiarch.tools.sim sweep --job einherjar --stat STR \\
        --hypo "TestBlade:SUPERLINEAR:base=10,linear=0.4,quad=0.006"

    # DPR analysis for all offensive abilities available to Einherjar
    python -m heresiarch.tools.sim ability-dpr --job einherjar

    # Side-by-side ability comparison
    python -m heresiarch.tools.sim ability-compare --abilities heavy_strike thrust reckless_blow --job einherjar

    # Full ability progression curve for a job
    python -m heresiarch.tools.sim job-curve --job berserker

    # XP progression across zones for a job
    python -m heresiarch.tools.sim xp-curve --job einherjar

    # Enemy stat tables at each zone level
    python -m heresiarch.tools.sim enemy-stats
    python -m heresiarch.tools.sim enemy-stats --enemies brute_oni caster_kitsune

    # Shop affordability analysis
    python -m heresiarch.tools.sim shop-pricing
    python -m heresiarch.tools.sim shop-pricing --potions-only

    # Full run progression simulation
    python -m heresiarch.tools.sim progression --job einherjar
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from heresiarch.engine.data_loader import load_all
from heresiarch.engine.formulas import (
    calculate_bonus_actions,
    calculate_buy_price,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_levels_gained,
    calculate_max_hp,
    calculate_physical_damage,
    calculate_magical_damage,
    calculate_stats_at_level,
    calculate_xp_reward,
    evaluate_conversion,
    evaluate_item_scaling,
    xp_for_level,
)

# _sigmoid may not exist in all versions of formulas.py
try:
    from heresiarch.engine.formulas import _sigmoid
except ImportError:
    import math as _math

    def _sigmoid(stat_value: int, max_output: float, midpoint: float, rate: float) -> int:
        """Fallback sigmoid: max_output / (1 + exp(-rate * (stat - midpoint)))."""
        try:
            exponent = -rate * (stat_value - midpoint)
            exponent = max(-500.0, min(500.0, exponent))
            return int(max_output / (1.0 + _math.exp(exponent)))
        except OverflowError:
            return 0 if stat_value < midpoint else int(max_output)

from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    DamageQuality,
)
from heresiarch.engine.models.items import (
    ConversionEffect,
    EquipSlot,
    Item,
    ItemScaling,
    ScalingType,
)
from heresiarch.engine.models.jobs import JobTemplate

# AbilityUnlock may not exist in all versions
try:
    from heresiarch.engine.models.jobs import AbilityUnlock
except ImportError:
    from pydantic import BaseModel as _BaseModel

    class AbilityUnlock(_BaseModel):  # type: ignore[no-redef]
        """Fallback: an ability unlocked at a specific level for a job."""
        level: int
        ability_id: str
from heresiarch.engine.models.stats import GrowthVector, StatBlock, StatType

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData


# ---------------------------------------------------------------------------
# Table formatting
# ---------------------------------------------------------------------------

def _fmt_table(headers: list[str], rows: list[list[str]], col_align: list[str] | None = None) -> str:
    """Format a list of rows as a fixed-width table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    if col_align is None:
        col_align = ["r"] * len(headers)

    def _pad(val: str, w: int, align: str) -> str:
        return val.rjust(w) if align == "r" else val.ljust(w)

    sep = " | "
    header_line = sep.join(_pad(h, widths[i], col_align[i]) for i, h in enumerate(headers))
    divider = "-+-".join("-" * widths[i] for i in range(len(headers)))
    lines = [header_line, divider]
    for row in rows:
        line = sep.join(_pad(row[i] if i < len(row) else "", widths[i], col_align[i]) for i in range(len(headers)))
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core simulation functions (importable for REPL use)
# ---------------------------------------------------------------------------

def weapon_sweep(
    growth_rate: int,
    weapons: dict[str, ItemScaling],
    levels: list[int] | None = None,
) -> str:
    """Show weapon output across levels for a given growth rate.

    Returns a formatted table.
    """
    if levels is None:
        levels = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 99]

    weapon_names = list(weapons.keys())
    headers = ["Lv", "STR", *weapon_names, "Best", "|", *[f"{n}_eff" for n in weapon_names]]
    rows: list[list[str]] = []

    for lv in levels:
        stat = growth_rate * lv
        outputs = {}
        for name, scaling in weapons.items():
            outputs[name] = evaluate_item_scaling(scaling, stat)

        best_name = max(outputs, key=lambda n: outputs[n])
        best_tag = best_name

        row = [str(lv), str(stat)]
        for name in weapon_names:
            row.append(f"{outputs[name]:.0f}")
        row.append(best_tag)
        row.append("|")
        for name in weapon_names:
            eff = stat + max(0, int(outputs[name]))
            row.append(str(eff))
        rows.append(row)

    return _fmt_table(headers, rows)


def find_crossovers(
    growth_rate: int,
    weapons: dict[str, ItemScaling],
    max_level: int = 99,
) -> str:
    """Find exact crossover levels between all weapon pairs."""
    names = list(weapons.keys())
    results: list[str] = []

    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            found = False
            a_was_better = None
            for lv in range(1, max_level + 1):
                stat = growth_rate * lv
                val_a = evaluate_item_scaling(weapons[name_a], stat)
                val_b = evaluate_item_scaling(weapons[name_b], stat)
                a_better = val_a >= val_b
                if a_was_better is not None and a_better != a_was_better:
                    winner = name_a if a_better else name_b
                    results.append(
                        f"  {winner} overtakes {name_b if a_better else name_a} "
                        f"at Lv{lv} (stat={stat}, "
                        f"{name_a}={val_a:.0f}, {name_b}={val_b:.0f})"
                    )
                    found = True
                a_was_better = a_better
            if not found:
                final_stat = growth_rate * max_level
                va = evaluate_item_scaling(weapons[name_a], final_stat)
                vb = evaluate_item_scaling(weapons[name_b], final_stat)
                leader = name_a if va >= vb else name_b
                results.append(f"  {leader} leads {name_b if va >= vb else name_a} at all levels (no crossover)")

    # Also find breakeven points for degenerate weapons
    for name, scaling in weapons.items():
        if scaling.scaling_type == ScalingType.DEGENERATE:
            for lv in range(1, max_level + 1):
                stat = growth_rate * lv
                val = evaluate_item_scaling(scaling, stat)
                if val >= 0:
                    results.append(f"  {name} breaks even at Lv{lv} (stat={stat}, output={val:.1f})")
                    break
            else:
                results.append(f"  {name} NEVER breaks even within Lv{max_level}")

    return "\n".join(results)


def build_compare(
    game_data: GameData,
    job_id: str,
    level: int,
    builds: dict[str, list[str]],
    enemy_id: str | None = None,
    zone_level: int | None = None,
) -> str:
    """Compare full builds at a specific level.

    builds: {name: [item_id, item_id, ...]}
    """
    job = game_data.jobs[job_id]
    base_stats = calculate_stats_at_level(job.growth, level)

    headers = ["Build", "STR", "MAG", "DEF", "RES", "SPD", "HP", "Bonus Acts"]
    if enemy_id:
        headers.extend(["Heavy", "Bolt", "DPT"])

    rows: list[list[str]] = []

    # Create enemy if specified
    enemy_stats = None
    enemy_hp = 0
    if enemy_id and zone_level:
        from heresiarch.engine.combat import CombatEngine
        import random as _rand

        engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=_rand.Random(42),
        )
        template = game_data.enemies[enemy_id]
        enemy_inst = engine.create_enemy_instance(template, zone_level=zone_level)
        enemy_stats = enemy_inst.stats
        enemy_hp = enemy_inst.max_hp

    for build_name, item_ids in builds.items():
        items = [game_data.items[iid] for iid in item_ids if iid in game_data.items]
        eff = calculate_effective_stats(base_stats, items, [])
        hp = calculate_max_hp(job.base_hp, job.hp_growth, level, eff.DEF)
        bonus = calculate_bonus_actions(eff.SPD)

        row = [
            build_name,
            str(eff.STR), str(eff.MAG), str(eff.DEF), str(eff.RES), str(eff.SPD),
            str(hp), str(bonus),
        ]

        if enemy_stats:
            heavy = calculate_physical_damage(15, 0.8, eff.STR, enemy_stats.DEF)
            bolt = calculate_magical_damage(10, 0.7, eff.MAG)
            partial = max(1, int(calculate_physical_damage(5, 0.5, eff.STR, enemy_stats.DEF) * 0.5))
            dpt = heavy + bonus * partial
            row.extend([str(heavy), str(bolt), str(dpt)])

        rows.append(row)

    result = _fmt_table(headers, rows, col_align=["l"] + ["r"] * (len(headers) - 1))
    if enemy_stats:
        result += f"\n\nEnemy: {enemy_id} Zone {zone_level} — HP={enemy_hp} DEF={enemy_stats.DEF} RES={enemy_stats.RES}"
    return result


def converter_compare(
    growth_rate_source: int,
    converters: dict[str, ConversionEffect],
    levels: list[int] | None = None,
) -> str:
    """Compare converter outputs across levels."""
    if levels is None:
        levels = [10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 99]

    conv_names = list(converters.keys())
    headers = ["Lv", "Src Stat", *conv_names]
    rows: list[list[str]] = []

    for lv in levels:
        stat = growth_rate_source * lv
        row = [str(lv), str(stat)]
        for name in conv_names:
            bonus = evaluate_conversion(converters[name], stat)
            row.append(str(bonus))
        rows.append(row)

    return _fmt_table(headers, rows)


def growth_sensitivity(
    weapon_name: str,
    scaling: ItemScaling,
    growth_rates: list[int],
    levels: list[int] | None = None,
) -> str:
    """Show how growth rate affects weapon output."""
    if levels is None:
        levels = [15, 30, 50, 70, 99]

    headers = ["Growth/Lv", *[f"Lv{lv}" for lv in levels]]
    rows: list[list[str]] = []

    for rate in growth_rates:
        row = [str(rate)]
        for lv in levels:
            stat = rate * lv
            val = evaluate_item_scaling(scaling, stat)
            eff = stat + max(0, int(val))
            row.append(f"{val:.0f} ({eff})")
        rows.append(row)

    return f"--- {weapon_name} ---\n" + _fmt_table(headers, rows)


def sigmoid_explorer(
    max_output: float,
    midpoint: float,
    rate: float,
    stat_values: list[int] | None = None,
) -> str:
    """Show sigmoid curve at specific stat values."""
    if stat_values is None:
        stat_values = list(range(0, 700, 25))

    headers = ["Stat", "Output", "% of Max"]
    rows: list[list[str]] = []

    for stat in stat_values:
        out = _sigmoid(stat, max_output, midpoint, rate)
        pct = (out / max_output * 100) if max_output > 0 else 0
        rows.append([str(stat), str(out), f"{pct:.1f}%"])

    return (
        f"Sigmoid: max={max_output}, midpoint={midpoint}, rate={rate}\n"
        + _fmt_table(headers, rows)
    )


# ---------------------------------------------------------------------------
# Ability balance analysis (importable for REPL use)
# ---------------------------------------------------------------------------

# Default enemy DEF for DPR comparisons (moderate armor target)
_DEFAULT_ENEMY_DEF: int = 50


@dataclass
class AbilityDamageResult:
    """Computed damage output for a single ability at a single level."""

    ability_name: str
    ability_id: str
    level: int
    raw_damage: int
    quality: DamageQuality
    stat_scaling: StatType | None
    scaling_coefficient: float
    base_damage: int
    notes: str = ""

    # Quality-adjusted variants
    chain_damage: int | None = None
    surge_damages: dict[int, int] | None = None  # stacks -> damage
    dot_total: int | None = None  # total DOT over duration
    pierce_damage: int | None = None  # damage vs armored target with pierce


from heresiarch.tools.shared import compute_ability_total_damage as _compute_ability_total_damage  # noqa: E402
from heresiarch.tools.shared import compute_effect_damage as _compute_effect_damage  # noqa: E402


def ability_dpr(
    game_data: GameData,
    job_id: str,
    ability_ids: list[str] | None = None,
    levels: list[int] | None = None,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> str:
    """Calculate Damage Per Round for offensive abilities at various levels.

    If ability_ids is None, uses all offensive abilities in the registry.
    Returns formatted table with damage at each level and ratio vs basic_attack.
    """
    if levels is None:
        levels = [1, 5, 10, 15, 20, 50, 99]

    job = game_data.jobs[job_id]

    # Build unlock-level lookup: ability_id -> unlock level
    unlock_map: dict[str, int] = {}
    ability_unlocks: list[AbilityUnlock] = getattr(job, "ability_unlocks", [])
    for unlock in ability_unlocks:
        unlock_map[unlock.ability_id] = unlock.level
    # Innate is available at level 1
    unlock_map[job.innate_ability_id] = 1

    # Collect abilities to analyze
    if ability_ids is not None:
        abilities = []
        for aid in ability_ids:
            if aid in game_data.abilities:
                abilities.append(game_data.abilities[aid])
    else:
        abilities = [
            a for a in game_data.abilities.values()
            if a.category == AbilityCategory.OFFENSIVE
        ]

    if not abilities:
        return "No offensive abilities found."

    # Ensure basic_attack is present as baseline
    basic_attack = game_data.abilities.get("basic_attack")
    if basic_attack and basic_attack not in abilities:
        abilities.insert(0, basic_attack)

    # Build header
    level_cols = [f"Lv{lv}" for lv in levels]
    ratio_cols = [f"x{lv}" for lv in levels]
    headers = ["Ability", "Quality", "Scaling", "Coeff", "Unlock", *level_cols, "|", *ratio_cols]

    # Pre-compute basic_attack damage at each level for ratio
    ba_damages: dict[int, int] = {}
    if basic_attack:
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            ba_damages[lv] = _compute_ability_total_damage(
                basic_attack, stats.STR, stats.MAG, enemy_def,
            )

    rows: list[list[str]] = []
    for ability in abilities:
        # Summarize quality/scaling from first offensive effect
        quality_str = "---"
        scaling_str = "---"
        coeff_str = "---"
        for eff in ability.effects:
            if eff.base_damage != 0 or eff.scaling_coefficient > 0:
                quality_str = eff.quality.value if eff.quality != DamageQuality.NONE else "---"
                scaling_str = eff.stat_scaling.value if eff.stat_scaling else "STR"
                coeff_str = f"{eff.scaling_coefficient:.2f}"
                break

        unlock_lv = unlock_map.get(ability.id, "---")
        unlock_str = str(unlock_lv) if isinstance(unlock_lv, int) else unlock_lv

        # Compute damage at each level
        dmg_values: list[str] = []
        ratio_values: list[str] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            dmg_values.append(str(dmg))

            ba_dmg = ba_damages.get(lv, 0)
            if ba_dmg > 0 and ability.id != "basic_attack":
                ratio = dmg / ba_dmg
                ratio_values.append(f"{ratio:.2f}")
            else:
                ratio_values.append("1.00" if ability.id == "basic_attack" else "---")

        rows.append([
            ability.name, quality_str, scaling_str, coeff_str, unlock_str,
            *dmg_values, "|", *ratio_values,
        ])

    result = _fmt_table(headers, rows, col_align=["l", "l", "l", "r", "r"] + ["r"] * len(levels) + ["l"] + ["r"] * len(levels))

    # Quality detail sections
    detail_sections: list[str] = []

    # SURGE stacking details
    surge_abilities = [
        a for a in abilities
        if any(e.quality == DamageQuality.SURGE for e in a.effects)
    ]
    if surge_abilities:
        detail_sections.append(_format_surge_details(
            game_data, job, surge_abilities, levels, enemy_def,
        ))

    # DOT total-damage details
    dot_abilities = [
        a for a in abilities
        if any(e.quality == DamageQuality.DOT for e in a.effects)
    ]
    if dot_abilities:
        detail_sections.append(_format_dot_details(
            game_data, job, dot_abilities, levels, enemy_def,
        ))

    # PIERCE comparison (with/without armor)
    pierce_abilities = [
        a for a in abilities
        if any(e.pierce_percent > 0 for e in a.effects)
    ]
    if pierce_abilities:
        detail_sections.append(_format_pierce_details(
            game_data, job, pierce_abilities, levels, enemy_def,
        ))

    # CHAIN AoE efficiency
    chain_abilities = [
        a for a in abilities
        if any(e.quality == DamageQuality.CHAIN for e in a.effects)
    ]
    if chain_abilities:
        detail_sections.append(_format_chain_details(
            game_data, job, chain_abilities, levels, enemy_def,
        ))

    if detail_sections:
        result += "\n\n" + "\n\n".join(detail_sections)

    return result


def _format_surge_details(
    game_data: GameData,
    job: JobTemplate,
    abilities: list[Ability],
    levels: list[int],
    enemy_def: int,
) -> str:
    """Format SURGE stacking breakdown: damage at stacks 1-5."""
    lines = ["--- SURGE Stacking ---"]
    stacks_range = [1, 2, 3, 4, 5]
    for ability in abilities:
        lines.append(f"\n  {ability.name}:")
        surge_effect = next(
            (e for e in ability.effects if e.quality == DamageQuality.SURGE), None,
        )
        if not surge_effect:
            continue
        bonus = surge_effect.surge_stack_bonus
        lines.append(f"  stack_bonus: +{bonus:.0%}/stack")

        headers = ["Lv", "Base", *[f"x{s}" for s in stacks_range]]
        rows: list[list[str]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            base_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            row = [str(lv), str(base_dmg)]
            for stacks in stacks_range:
                multiplier = 1.0 + bonus * stacks
                row.append(str(int(base_dmg * multiplier)))
            rows.append(row)
        lines.append(_fmt_table(headers, rows))

    return "\n".join(lines)


def _format_dot_details(
    game_data: GameData,
    job: JobTemplate,
    abilities: list[Ability],
    levels: list[int],
    enemy_def: int,
) -> str:
    """Format DOT total-damage breakdown: initial + ticks."""
    lines = ["--- DOT Total Damage ---"]
    for ability in abilities:
        dot_effect = next(
            (e for e in ability.effects if e.quality == DamageQuality.DOT), None,
        )
        if not dot_effect:
            continue
        duration = dot_effect.duration_rounds
        # DOT tick = base_damage * 0.5 per round (from combat engine)
        tick_base = max(1, int(dot_effect.base_damage * 0.5))
        lines.append(f"\n  {ability.name}: {duration} rounds, tick={tick_base}/round (base)")

        headers = ["Lv", "Hit Dmg", "Tick/Rd", f"Total ({duration}rd)"]
        rows: list[list[str]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            hit_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            # DOT bypasses DEF (from combat engine logic), tick = base_damage * 0.5
            total_dot = tick_base * duration
            total = hit_dmg + total_dot
            rows.append([str(lv), str(hit_dmg), str(tick_base), str(total)])
        lines.append(_fmt_table(headers, rows))

    return "\n".join(lines)


def _format_pierce_details(
    game_data: GameData,
    job: JobTemplate,
    abilities: list[Ability],
    levels: list[int],
    enemy_def: int,
) -> str:
    """Format PIERCE comparison: damage with and without pierce vs varying DEF."""
    lines = ["--- PIERCE vs Armor ---"]
    def_values = [25, 50, 100, 150, 200]
    for ability in abilities:
        pierce_effect = next(
            (e for e in ability.effects if e.pierce_percent > 0), None,
        )
        if not pierce_effect:
            continue
        pct = pierce_effect.pierce_percent
        lines.append(f"\n  {ability.name}: pierce={pct:.0%}")

        headers = ["Lv", *[f"DEF={d}" for d in def_values], "|", *[f"noPierce@{d}" for d in def_values]]
        rows: list[list[str]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            row = [str(lv)]
            pierce_vals: list[str] = []
            no_pierce_vals: list[str] = []
            for d in def_values:
                with_pierce = calculate_physical_damage(
                    pierce_effect.base_damage, pierce_effect.scaling_coefficient,
                    stats.STR, d, pierce_percent=pct,
                )
                without_pierce = calculate_physical_damage(
                    pierce_effect.base_damage, pierce_effect.scaling_coefficient,
                    stats.STR, d, pierce_percent=0.0,
                )
                pierce_vals.append(str(with_pierce))
                no_pierce_vals.append(str(without_pierce))
            row.extend(pierce_vals)
            row.append("|")
            row.extend(no_pierce_vals)
            rows.append(row)
        lines.append(_fmt_table(headers, rows))

    return "\n".join(lines)


def _format_chain_details(
    game_data: GameData,
    job: JobTemplate,
    abilities: list[Ability],
    levels: list[int],
    enemy_def: int,
) -> str:
    """Format CHAIN AoE efficiency: per-target vs total for N targets."""
    lines = ["--- CHAIN AoE Efficiency ---"]
    target_counts = [1, 2, 3, 4]
    for ability in abilities:
        chain_effect = next(
            (e for e in ability.effects if e.quality == DamageQuality.CHAIN), None,
        )
        if not chain_effect:
            continue
        ratio = chain_effect.chain_damage_ratio
        lines.append(f"\n  {ability.name}: chain_ratio={ratio:.0%}")

        headers = ["Lv", "Per-Hit", *[f"{n}T total" for n in target_counts]]
        rows: list[list[str]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            # Per-hit already includes chain_damage_ratio via _compute_ability_total_damage
            per_hit = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            row = [str(lv), str(per_hit)]
            for n in target_counts:
                row.append(str(per_hit * n))
            rows.append(row)
        lines.append(_fmt_table(headers, rows))

    return "\n".join(lines)


def ability_compare(
    game_data: GameData,
    job_id: str,
    ability_ids: list[str],
    levels: list[int] | None = None,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> str:
    """Side-by-side comparison of 2-3 abilities with crossover analysis.

    Returns formatted table plus crossover point annotations.
    """
    if levels is None:
        levels = list(range(1, 100))

    job = game_data.jobs[job_id]
    abilities: list[Ability] = []
    for aid in ability_ids:
        if aid not in game_data.abilities:
            return f"Error: ability '{aid}' not found in registry."
        abilities.append(game_data.abilities[aid])

    if len(abilities) < 2:
        return "Error: need at least 2 abilities for comparison."

    names = [a.name for a in abilities]

    # Display levels (subset for the table)
    display_levels = [1, 5, 10, 15, 20, 30, 50, 70, 99]
    display_levels = [lv for lv in display_levels if lv in levels]

    headers = ["Lv", "STR", "MAG", *names, "Best"]
    rows: list[list[str]] = []

    for lv in display_levels:
        stats = calculate_stats_at_level(job.growth, lv)
        damages = {}
        for ability in abilities:
            damages[ability.name] = _compute_ability_total_damage(
                ability, stats.STR, stats.MAG, enemy_def,
            )

        best = max(damages, key=lambda n: damages[n])
        row = [str(lv), str(stats.STR), str(stats.MAG)]
        for name in names:
            row.append(str(damages[name]))
        row.append(best)
        rows.append(row)

    result = _fmt_table(headers, rows, col_align=["r", "r", "r"] + ["r"] * len(names) + ["l"])

    # Find crossover points (scan full level range)
    crossovers: list[str] = []
    for i, ability_a in enumerate(abilities):
        for ability_b in abilities[i + 1:]:
            a_was_better: bool | None = None
            for lv in range(1, 100):
                stats = calculate_stats_at_level(job.growth, lv)
                dmg_a = _compute_ability_total_damage(
                    ability_a, stats.STR, stats.MAG, enemy_def,
                )
                dmg_b = _compute_ability_total_damage(
                    ability_b, stats.STR, stats.MAG, enemy_def,
                )
                a_better = dmg_a >= dmg_b
                if a_was_better is not None and a_better != a_was_better:
                    winner = ability_a.name if a_better else ability_b.name
                    loser = ability_b.name if a_better else ability_a.name
                    crossovers.append(
                        f"  {winner} overtakes {loser} at Lv{lv} "
                        f"({ability_a.name}={dmg_a}, {ability_b.name}={dmg_b})"
                    )
                a_was_better = a_better

            if a_was_better is not None and not any(
                ability_a.name in c and ability_b.name in c for c in crossovers
            ):
                final_stats = calculate_stats_at_level(job.growth, 99)
                dmg_a = _compute_ability_total_damage(
                    ability_a, final_stats.STR, final_stats.MAG, enemy_def,
                )
                dmg_b = _compute_ability_total_damage(
                    ability_b, final_stats.STR, final_stats.MAG, enemy_def,
                )
                leader = ability_a.name if dmg_a >= dmg_b else ability_b.name
                trailer = ability_b.name if dmg_a >= dmg_b else ability_a.name
                crossovers.append(f"  {leader} leads {trailer} at all levels (no crossover)")

    if crossovers:
        result += "\n\nCrossover Analysis:\n" + "\n".join(crossovers)

    return result


@dataclass
class AbilityUnlockInfo:
    """Info about an ability's unlock point and power at that level."""

    ability_id: str
    ability_name: str
    unlock_level: int
    category: str
    damage_at_unlock: int
    basic_attack_at_unlock: int
    ratio_vs_basic: float
    quality: str
    scaling_stat: str


def job_ability_curve(
    game_data: GameData,
    job_id: str,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> str:
    """Show the full ability progression for a job.

    Displays: unlock level, ability name, category, DPR at unlock, ratio vs basic_attack.
    """
    job = game_data.jobs[job_id]

    # Build the progression list
    unlocks: list[AbilityUnlockInfo] = []

    # Innate ability (always level 1)
    innate = game_data.abilities.get(job.innate_ability_id)
    if innate:
        stats = calculate_stats_at_level(job.growth, 1)
        innate_dmg = _compute_ability_total_damage(innate, stats.STR, stats.MAG, enemy_def)
        ba = game_data.abilities.get("basic_attack")
        ba_dmg = _compute_ability_total_damage(ba, stats.STR, stats.MAG, enemy_def) if ba else 0
        quality = "---"
        scaling = "---"
        for eff in innate.effects:
            if eff.base_damage != 0 or eff.scaling_coefficient > 0:
                quality = eff.quality.value if eff.quality != DamageQuality.NONE else "---"
                scaling = eff.stat_scaling.value if eff.stat_scaling else "STR"
                break
        unlocks.append(AbilityUnlockInfo(
            ability_id=innate.id,
            ability_name=innate.name,
            unlock_level=1,
            category=innate.category.value,
            damage_at_unlock=innate_dmg,
            basic_attack_at_unlock=ba_dmg,
            ratio_vs_basic=innate_dmg / ba_dmg if ba_dmg > 0 else 0.0,
            quality=quality,
            scaling_stat=scaling,
        ))

    # Ability unlocks from job progression
    ability_unlocks: list[AbilityUnlock] = getattr(job, "ability_unlocks", [])
    for unlock in sorted(ability_unlocks, key=lambda u: u.level):
        ability = game_data.abilities.get(unlock.ability_id)
        if not ability:
            continue

        lv = unlock.level
        stats = calculate_stats_at_level(job.growth, lv)
        dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
        ba = game_data.abilities.get("basic_attack")
        ba_dmg = _compute_ability_total_damage(ba, stats.STR, stats.MAG, enemy_def) if ba else 0

        quality = "---"
        scaling = "---"
        for eff in ability.effects:
            if eff.base_damage != 0 or eff.scaling_coefficient > 0:
                quality = eff.quality.value if eff.quality != DamageQuality.NONE else "---"
                scaling = eff.stat_scaling.value if eff.stat_scaling else "STR"
                break

        unlocks.append(AbilityUnlockInfo(
            ability_id=ability.id,
            ability_name=ability.name,
            unlock_level=lv,
            category=ability.category.value,
            damage_at_unlock=dmg,
            basic_attack_at_unlock=ba_dmg,
            ratio_vs_basic=dmg / ba_dmg if ba_dmg > 0 else 0.0,
            quality=quality,
            scaling_stat=scaling,
        ))

    if not unlocks:
        return f"No ability progression defined for {job.name}."

    # Format as table
    headers = ["Lv", "Ability", "Category", "Quality", "Scaling", "Dmg@Unlock", "BA@Unlock", "Ratio"]
    rows: list[list[str]] = []

    for info in unlocks:
        rows.append([
            str(info.unlock_level),
            info.ability_name,
            info.category,
            info.quality,
            info.scaling_stat,
            str(info.damage_at_unlock),
            str(info.basic_attack_at_unlock),
            f"{info.ratio_vs_basic:.2f}x",
        ])

    result = f"Job: {job.name} — Ability Progression (vs DEF={enemy_def})\n"
    result += _fmt_table(
        headers, rows,
        col_align=["r", "l", "l", "l", "l", "r", "r", "r"],
    )

    # Summary: power curve milestones
    if len(unlocks) > 1:
        result += "\n\nProgression Notes:"
        offensive_unlocks = [u for u in unlocks if u.damage_at_unlock > 0]
        if offensive_unlocks:
            best = max(offensive_unlocks, key=lambda u: u.ratio_vs_basic)
            result += f"\n  Strongest unlock: {best.ability_name} at Lv{best.unlock_level} ({best.ratio_vs_basic:.2f}x basic_attack)"
            first_major = next(
                (u for u in offensive_unlocks if u.ratio_vs_basic > 1.5), None,
            )
            if first_major:
                result += f"\n  First major power spike (>1.5x BA): {first_major.ability_name} at Lv{first_major.unlock_level}"

    return result


# ---------------------------------------------------------------------------
# Hypothetical item parsing
# ---------------------------------------------------------------------------

def parse_hypo_weapon(spec: str) -> tuple[str, ItemScaling]:
    """Parse a hypothetical weapon spec string.

    Format: "Name:TYPE:param=val,param=val,..."
    Params: base, linear, quad, offset
    Example: "TestBlade:SUPERLINEAR:base=10,linear=0.4,quad=0.006"
    """
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(f"Bad hypo spec: {spec}. Need Name:TYPE[:params]")

    name = parts[0]
    stype = ScalingType(parts[1])
    params: dict[str, float] = {}
    if len(parts) > 2:
        for kv in parts[2].split(","):
            k, v = kv.split("=")
            params[k.strip()] = float(v.strip())

    scaling = ItemScaling(
        scaling_type=stype,
        stat=StatType.STR,
        base=params.get("base", 0.0),
        linear_coeff=params.get("linear", 0.0),
        quadratic_coeff=params.get("quad", 0.0),
        constant_offset=params.get("offset", 0.0),
    )
    return name, scaling


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_game_data() -> GameData:
    """Load game data, trying common project root locations."""
    candidates = [
        Path("data"),
        Path(__file__).resolve().parents[4] / "data",
    ]
    for p in candidates:
        if p.is_dir():
            return load_all(p)
    raise FileNotFoundError(f"Cannot find data/ directory. Tried: {candidates}")


def _get_weapons_for_stat(game_data: GameData, stat: str) -> dict[str, ItemScaling]:
    """Get all weapons that scale off a given stat."""
    target = StatType(stat.upper())
    weapons = {}
    for item in game_data.items.values():
        if item.scaling and item.scaling.stat == target:
            weapons[item.name] = item.scaling
    return weapons


def _get_job_growth_rate(game_data: GameData, job_id: str, stat: str) -> int:
    """Get effective growth rate for a job + stat combo."""
    job = game_data.jobs[job_id]
    return job.growth.effective_growth(StatType(stat.upper()))


def cmd_sweep(args: argparse.Namespace) -> None:
    gd = _load_game_data()
    stat = args.stat.upper()
    rate = _get_job_growth_rate(gd, args.job, stat)
    weapons = _get_weapons_for_stat(gd, stat)

    # Add hypothetical weapons
    for spec in args.hypo or []:
        name, scaling = parse_hypo_weapon(spec)
        weapons[name] = scaling

    print(f"Job: {args.job} ({stat} growth: +{rate}/lv)\n")
    print(weapon_sweep(rate, weapons))


def cmd_crossover(args: argparse.Namespace) -> None:
    gd = _load_game_data()
    stat = args.stat.upper()
    rate = _get_job_growth_rate(gd, args.job, stat)
    weapons = _get_weapons_for_stat(gd, stat)

    for spec in args.hypo or []:
        name, scaling = parse_hypo_weapon(spec)
        weapons[name] = scaling

    print(f"Job: {args.job} ({stat} growth: +{rate}/lv)")
    print(f"Crossover analysis:\n")
    print(find_crossovers(rate, weapons))

    # Also show off-label crossover sensitivity
    print(f"\nGrowth sensitivity for breakeven/crossover points:")
    for growth in [1, 2, 3, 4, 5, 6, 7]:
        print(f"\n  Growth {growth}/lv:")
        print(find_crossovers(growth, weapons))


def cmd_build(args: argparse.Namespace) -> None:
    gd = _load_game_data()

    # Build loadouts from all weapons for the job's primary stat
    job = gd.jobs[args.job]
    # Determine primary offensive stat
    primary = max(
        [StatType.STR, StatType.MAG],
        key=lambda s: job.growth.effective_growth(s),
    )

    builds: dict[str, list[str]] = {}
    for item in gd.items.values():
        if item.scaling and item.scaling.stat == primary:
            build_items = [item.id]
            # Add all accessories
            for acc in gd.items.values():
                if acc.conversion and acc.slot in (EquipSlot.ACCESSORY_1, EquipSlot.ACCESSORY_2):
                    builds[f"{item.name} + {acc.name}"] = [item.id, acc.id]
            builds[item.name] = build_items

    print(f"Job: {args.job} Lv{args.level} (primary: {primary.value})\n")
    print(build_compare(
        gd, args.job, args.level, builds,
        enemy_id=args.enemy, zone_level=args.zone,
    ))


def cmd_converter(args: argparse.Namespace) -> None:
    gd = _load_game_data()

    item = gd.items.get(args.converter)
    if not item or not item.conversion:
        print(f"Error: {args.converter} not found or has no conversion")
        return

    conv = item.conversion
    source_stat = conv.source_stat
    job = gd.jobs[args.job]
    rate = job.growth.effective_growth(source_stat)

    # Compare current quadratic vs hypothetical sigmoid
    converters: dict[str, ConversionEffect] = {
        f"{item.name} (current)": conv,
    }

    # Add sigmoid variant for comparison (requires SIGMOID in ScalingType)
    if args.sigmoid_max:
        try:
            sig = ConversionEffect(
                source_stat=conv.source_stat,
                target_stat=conv.target_stat,
                scaling_type=ScalingType("SIGMOID"),
                sigmoid_max=args.sigmoid_max,
                sigmoid_mid=args.sigmoid_mid,
                sigmoid_rate=args.sigmoid_rate,
            )
            converters[f"{item.name} (sigmoid max={args.sigmoid_max})"] = sig
        except ValueError:
            print("Warning: SIGMOID scaling type not available in this version")

    print(f"Job: {args.job} ({source_stat.value} growth: +{rate}/lv)")
    print(f"Converter: {item.name} ({conv.source_stat.value} -> {conv.target_stat.value})\n")
    print(converter_compare(rate, converters))

    # Show full build impact if a weapon is specified
    if args.weapon:
        print(f"\n--- Full build impact with {args.weapon} ---")
        weapon = gd.items[args.weapon]
        for conv_name, conv_effect in converters.items():
            test_item = Item(
                id="test_conv", name=conv_name, slot=EquipSlot.ACCESSORY_1,
                conversion=conv_effect,
            )
            levels = [15, 30, 50, 70, 99]
            print(f"\n  {conv_name}:")
            for lv in levels:
                base = calculate_stats_at_level(job.growth, lv)
                eff = calculate_effective_stats(base, [weapon, test_item], [])
                hp = calculate_max_hp(job.base_hp, job.hp_growth, lv, eff.DEF)
                target_stat = conv.target_stat.value
                print(f"    Lv{lv:>2}: eff_{target_stat}={getattr(eff, target_stat):>5}  HP={hp:>5}")


def cmd_sigmoid(args: argparse.Namespace) -> None:
    """Explore sigmoid curves interactively."""
    print(sigmoid_explorer(args.max, args.mid, args.rate))


def cmd_ability_dpr(args: argparse.Namespace) -> None:
    """DPR analysis for offensive abilities."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    ability_ids = args.abilities if args.abilities else None
    # Validate ability IDs if specified
    if ability_ids:
        for aid in ability_ids:
            if aid not in gd.abilities:
                print(f"Error: ability '{aid}' not found. Available offensive abilities:")
                for a in gd.abilities.values():
                    if a.category == AbilityCategory.OFFENSIVE:
                        print(f"  {a.id}: {a.name}")
                return

    print(f"Job: {gd.jobs[job_id].name} (enemy DEF={args.def_value})\n")
    print(ability_dpr(gd, job_id, ability_ids=ability_ids, enemy_def=args.def_value))


def cmd_ability_compare(args: argparse.Namespace) -> None:
    """Side-by-side ability comparison."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    if not args.abilities or len(args.abilities) < 2:
        print("Error: --abilities requires at least 2 ability IDs.")
        return

    print(f"Job: {gd.jobs[job_id].name} (enemy DEF={args.def_value})\n")
    print(ability_compare(gd, job_id, args.abilities, enemy_def=args.def_value))


def cmd_job_curve(args: argparse.Namespace) -> None:
    """Full ability progression curve for a job."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    print(job_ability_curve(gd, job_id, enemy_def=args.def_value))


# ---------------------------------------------------------------------------
# Shared economy / XP helpers (Step 1)
# ---------------------------------------------------------------------------

_OVERSTAY_MODERATE: int = 5
_OVERSTAY_GRIND: int = 20


@dataclass
class ZoneEconSnapshot:
    """Economy snapshot for a single zone."""

    zone_id: str
    zone_name: str
    zone_level: int
    enemies_total: int
    encounters_total: int
    zone_gold: float
    overstay_max_gold: float
    cumulative_gold_rush: float
    cumulative_gold_moderate: float
    cumulative_gold_grind: float
    avg_encounter_gold: float
    shop_items: list[str]


@dataclass
class ZoneXPSnapshot:
    """XP / level snapshot for a single zone under different play styles."""

    zone_id: str
    zone_level: int
    level_at_exit_rush: int
    level_at_exit_moderate: int
    level_at_exit_grind: int
    cumulative_xp_rush: int
    cumulative_xp_moderate: int
    cumulative_xp_grind: int


def _compute_zone_economy(game_data: GameData) -> list[ZoneEconSnapshot]:
    """Build per-zone gold snapshots using avg money-drop formula.

    Returns zones sorted by zone_level ascending.
    """
    from heresiarch.engine.formulas import MONEY_DROP_MIN_MULTIPLIER, MONEY_DROP_MAX_MULTIPLIER
    from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE

    money_avg = (MONEY_DROP_MIN_MULTIPLIER + MONEY_DROP_MAX_MULTIPLIER) / 2.0

    money_mults: dict[str, float] = {}
    for dt in game_data.drop_tables.values():
        money_mults[dt.enemy_template_id] = dt.money_multiplier

    snapshots: list[ZoneEconSnapshot] = []
    cumulative_rush = 0.0
    cumulative_moderate = 0.0
    cumulative_grind = 0.0

    for zone in sorted(game_data.zones.values(), key=lambda z: z.zone_level):
        zlvl = zone.zone_level
        zone_gold = 0.0
        zone_enemies = 0
        non_boss_golds: list[float] = []

        for enc in zone.encounters:
            enc_gold = 0.0
            enc_enemies = 0
            for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                mult = money_mults.get(tmpl_id, 1.0)
                enc_gold += zlvl * money_avg * mult * cnt
                enc_enemies += cnt
            zone_gold += enc_gold
            zone_enemies += enc_enemies
            if not enc.is_boss:
                non_boss_golds.append(enc_gold)

        avg_enc_gold = sum(non_boss_golds) / len(non_boss_golds) if non_boss_golds else 0.0

        # Overstay gold: sum avg_enc_gold * decaying multiplier per extra battle
        overstay_max_gold = 0.0
        for b in range(1, 100):
            mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
            if mult <= 0:
                break
            overstay_max_gold += avg_enc_gold * mult

        # Gold for N overstay battles
        def _overstay_gold(n_battles: int) -> float:
            total = 0.0
            for b in range(1, n_battles + 1):
                mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                total += avg_enc_gold * mult
            return total

        cumulative_rush += zone_gold
        cumulative_moderate += zone_gold + _overstay_gold(_OVERSTAY_MODERATE)
        cumulative_grind += zone_gold + _overstay_gold(_OVERSTAY_GRIND)

        snapshots.append(ZoneEconSnapshot(
            zone_id=zone.id,
            zone_name=zone.name,
            zone_level=zlvl,
            enemies_total=zone_enemies,
            encounters_total=len(zone.encounters),
            zone_gold=zone_gold,
            overstay_max_gold=overstay_max_gold,
            cumulative_gold_rush=cumulative_rush,
            cumulative_gold_moderate=cumulative_moderate,
            cumulative_gold_grind=cumulative_grind,
            avg_encounter_gold=avg_enc_gold,
            shop_items=list(zone.shop_item_pool),
        ))

    return snapshots


def _compute_xp_progression(game_data: GameData, job_id: str) -> list[ZoneXPSnapshot]:
    """Simulate XP/level at each zone exit under rush/moderate/grind scenarios.

    Assumes a single character of the given job, starting at level 1 with 0 XP,
    clearing zones in order.  Rush = clear only; moderate = +5 overstay battles;
    grind = +20 overstay battles per zone.
    """
    from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE

    job = game_data.jobs[job_id]

    # Track state for each play style independently
    xp_rush = 0
    xp_moderate = 0
    xp_grind = 0
    level_rush = 1
    level_moderate = 1
    level_grind = 1

    snapshots: list[ZoneXPSnapshot] = []

    for zone in sorted(game_data.zones.values(), key=lambda z: z.zone_level):
        zlvl = zone.zone_level
        xp_cap = zone.xp_cap_level

        # XP from clearing all encounters in the zone
        def _zone_clear_xp(char_level: int) -> int:
            total = 0
            for enc in zone.encounters:
                for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                    tmpl = game_data.enemies.get(tmpl_id)
                    if tmpl is None:
                        continue
                    xp_per_kill = calculate_xp_reward(
                        zlvl, tmpl.budget_multiplier, char_level, xp_cap,
                    )
                    total += xp_per_kill * cnt
            return total

        # Overstay XP: re-fight avg encounter, XP penalized by both overstay
        # multiplier and level-cap diminishing returns
        def _overstay_xp(n_battles: int, char_level: int) -> int:
            if not zone.encounters:
                return 0
            # Use avg enemy budget from non-boss encounters
            non_boss = [e for e in zone.encounters if not e.is_boss]
            if not non_boss:
                non_boss = zone.encounters
            total_budget = 0.0
            total_enemies = 0
            for enc in non_boss:
                for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                    tmpl = game_data.enemies.get(tmpl_id)
                    if tmpl is not None:
                        total_budget += tmpl.budget_multiplier * cnt
                        total_enemies += cnt
            avg_budget = total_budget / total_enemies if total_enemies > 0 else 1.0
            avg_count = sum(sum(e.enemy_counts) for e in non_boss) / len(non_boss) if non_boss else 1

            total_xp = 0
            for b in range(1, n_battles + 1):
                overstay_mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                base_xp = calculate_xp_reward(zlvl, avg_budget, char_level, xp_cap)
                total_xp += int(base_xp * overstay_mult * avg_count)
            return total_xp

        # Rush: clear only
        xp_rush += _zone_clear_xp(level_rush)
        gained = calculate_levels_gained(xp_rush, level_rush)
        level_rush += gained

        # Moderate: clear + 5 overstay
        xp_moderate += _zone_clear_xp(level_moderate)
        xp_moderate += _overstay_xp(_OVERSTAY_MODERATE, level_moderate)
        gained = calculate_levels_gained(xp_moderate, level_moderate)
        level_moderate += gained

        # Grind: clear + 20 overstay
        xp_grind += _zone_clear_xp(level_grind)
        xp_grind += _overstay_xp(_OVERSTAY_GRIND, level_grind)
        gained = calculate_levels_gained(xp_grind, level_grind)
        level_grind += gained

        snapshots.append(ZoneXPSnapshot(
            zone_id=zone.id,
            zone_level=zlvl,
            level_at_exit_rush=level_rush,
            level_at_exit_moderate=level_moderate,
            level_at_exit_grind=level_grind,
            cumulative_xp_rush=xp_rush,
            cumulative_xp_moderate=xp_moderate,
            cumulative_xp_grind=xp_grind,
        ))

    return snapshots


# ---------------------------------------------------------------------------
# cmd_economy (refactored to use _compute_zone_economy)
# ---------------------------------------------------------------------------

def cmd_economy(args: argparse.Namespace) -> None:
    """Full zone economy analysis: gold per zone, overstay curves, pilfer impact."""
    from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE

    game_data = _load_game_data()
    snapshots = _compute_zone_economy(game_data)

    print("=" * 90)
    print("ZONE ECONOMY ANALYSIS")
    print("=" * 90)

    for snap in snapshots:
        print(f"\n{snap.zone_name} (Lv{snap.zone_level}) — {snap.encounters_total} encounters, {snap.enemies_total} enemies")
        print(f"  Zone gold: {snap.zone_gold:.0f}G  |  Avg encounter: {snap.avg_encounter_gold:.0f}G  |  Overstay max: {snap.overstay_max_gold:.0f}G")
        print(f"  Zone + overstay: {snap.zone_gold + snap.overstay_max_gold:.0f}G  |  Cumulative run: {snap.cumulative_gold_rush:.0f}G")

        if args.overstay:
            print("  Overstay decay:")
            oc = 0.0
            for b in range(1, 25):
                mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                gold = snap.avg_encounter_gold * mult
                oc += gold
                if b <= 5 or b % 5 == 0 or mult <= 0:
                    print(f"    Battle {b:>2}: {mult:>4.0%} -> {gold:>6.0f}G  (cum: {oc:>6.0f}G)")
                if mult <= 0:
                    break

    # Pilfer impact
    print(f"\n{'=' * 90}")
    print("PILFER IMPACT vs ZONE VALUE")
    print(f"{'=' * 90}")

    pilfer = game_data.abilities.get("pilfer")
    if pilfer and pilfer.effects:
        eff = pilfer.effects[0]
        flat = eff.gold_steal_flat
        per_lvl = eff.gold_steal_per_level
        print(f"  Pilfer: {flat}G flat + {per_lvl}G/level")
        print()
        print(f"  {'Zone':>8} | {'Zone Gold':>10} | {'Cum Gold':>10} | {'Pilfer/Hit':>10} | {'2 Hits':>8} | {'~ Encounters':>12}")
        print(f"  {'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*12}")
        for snap in snapshots:
            p = flat + int(per_lvl * snap.zone_level)
            two = p * 2
            equiv = two / snap.avg_encounter_gold if snap.avg_encounter_gold > 0 else 0
            print(f"  {snap.zone_id:>8} | {snap.zone_gold:>8.0f}G | {snap.cumulative_gold_rush:>8.0f}G | {p:>8}G | {two:>6}G | {equiv:>10.2f}")
    else:
        print("  (pilfer ability not found)")

    # Shop reference
    print("\n  Shop prices: ", end="")
    prices = [(item.name, item.base_price) for item in game_data.items.values() if item.base_price > 0]
    prices.sort(key=lambda x: x[1])
    print(", ".join(f"{name}: {price}G" for name, price in prices[:8]))


# ---------------------------------------------------------------------------
# cmd_xp_curve (Step 2)
# ---------------------------------------------------------------------------

def cmd_xp_curve(args: argparse.Namespace) -> None:
    """Show player level at each zone exit under rush/moderate/grind scenarios."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    job = gd.jobs[job_id]
    snapshots = _compute_xp_progression(gd, job_id)

    if not snapshots:
        print("No zones found.")
        return

    print(f"XP Progression: {job.name}")
    print(f"  Rush = clear only  |  Moderate = +{_OVERSTAY_MODERATE} overstay  |  Grind = +{_OVERSTAY_GRIND} overstay")
    print()

    # Main table
    headers = [
        "Zone", "ZoneLv", "Lv Rush", "XP Rush",
        "Lv Mod", "XP Mod", "Lv Grind", "XP Grind",
    ]
    rows: list[list[str]] = []
    for snap in snapshots:
        rows.append([
            snap.zone_id,
            str(snap.zone_level),
            str(snap.level_at_exit_rush),
            str(snap.cumulative_xp_rush),
            str(snap.level_at_exit_moderate),
            str(snap.cumulative_xp_moderate),
            str(snap.level_at_exit_grind),
            str(snap.cumulative_xp_grind),
        ])
    print(_fmt_table(headers, rows, col_align=["l", "r", "r", "r", "r", "r", "r", "r"]))

    # XP thresholds for milestone levels
    milestone_levels = [5, 10, 15, 20, 25, 30]
    print("\nXP Thresholds:")
    for lv in milestone_levels:
        print(f"  Level {lv:>2}: {xp_for_level(lv):>6} XP")

    # Which zone each milestone is reached in (for each play style)
    print("\nMilestone Zones:")
    print(f"  {'Level':>6} | {'Rush':>10} | {'Moderate':>10} | {'Grind':>10}")
    print(f"  {'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
    for target_lv in milestone_levels:
        rush_zone = "---"
        mod_zone = "---"
        grind_zone = "---"
        for snap in snapshots:
            if rush_zone == "---" and snap.level_at_exit_rush >= target_lv:
                rush_zone = snap.zone_id
            if mod_zone == "---" and snap.level_at_exit_moderate >= target_lv:
                mod_zone = snap.zone_id
            if grind_zone == "---" and snap.level_at_exit_grind >= target_lv:
                grind_zone = snap.zone_id
        print(f"  Lv{target_lv:>3} | {rush_zone:>10} | {mod_zone:>10} | {grind_zone:>10}")


# ---------------------------------------------------------------------------
# cmd_enemy_stats (Step 3)
# ---------------------------------------------------------------------------

def cmd_enemy_stats(args: argparse.Namespace) -> None:
    """Show enemy stats (HP, STR, MAG, DEF, RES, SPD) at each zone level."""
    gd = _load_game_data()

    # Determine which enemies to show
    if args.enemies:
        enemy_ids = args.enemies
        for eid in enemy_ids:
            if eid not in gd.enemies:
                print(f"Error: enemy '{eid}' not found. Available: {', '.join(gd.enemies.keys())}")
                return
    else:
        enemy_ids = list(gd.enemies.keys())

    zones = sorted(gd.zones.values(), key=lambda z: z.zone_level)
    zone_levels = sorted({z.zone_level for z in zones})

    if not zone_levels:
        print("No zones found.")
        return

    for eid in enemy_ids:
        tmpl = gd.enemies[eid]
        equip_items = [gd.items[iid] for iid in tmpl.equipment if iid in gd.items]

        print(f"\n{'=' * 80}")
        print(f"{tmpl.name} ({eid})  |  budget_mult={tmpl.budget_multiplier}  |  equip: {', '.join(tmpl.equipment) or 'none'}")
        print(f"  stat_dist: " + ", ".join(f"{k}={v:.0%}" for k, v in tmpl.stat_distribution.items()))
        print(f"{'=' * 80}")

        headers = ["ZoneLv", "HP", "STR", "MAG", "DEF", "RES", "SPD"]
        if equip_items:
            headers.extend(["eSTR", "eMAG", "eDEF", "eRES", "eSPD"])
        rows: list[list[str]] = []

        for zlvl in zone_levels:
            base_stats = calculate_enemy_stats(
                zlvl, tmpl.budget_multiplier, tmpl.stat_distribution,
            )
            hp = calculate_enemy_hp(
                zlvl, tmpl.budget_multiplier, tmpl.base_hp, tmpl.hp_per_budget,
            )

            row = [
                str(zlvl), str(hp),
                str(base_stats.STR), str(base_stats.MAG),
                str(base_stats.DEF), str(base_stats.RES), str(base_stats.SPD),
            ]

            if equip_items:
                eff = calculate_effective_stats(base_stats, equip_items, [])
                row.extend([
                    str(eff.STR), str(eff.MAG),
                    str(eff.DEF), str(eff.RES), str(eff.SPD),
                ])

            rows.append(row)

        print(_fmt_table(headers, rows))


# ---------------------------------------------------------------------------
# cmd_shop_pricing (Step 4)
# ---------------------------------------------------------------------------

def cmd_shop_pricing(args: argparse.Namespace) -> None:
    """Shop affordability analysis and potion price validation."""
    gd = _load_game_data()
    snapshots = _compute_zone_economy(gd)

    if not snapshots:
        print("No zones found.")
        return

    potions_only: bool = args.potions_only

    if potions_only:
        _print_potion_check(gd, snapshots)
    else:
        _print_shop_affordability(gd, snapshots)
        print()
        _print_potion_check(gd, snapshots)


def _print_shop_affordability(game_data: GameData, snapshots: list[ZoneEconSnapshot]) -> None:
    """For each zone's shop, show item price as % of cumulative gold (rush/mod/grind)."""
    print("=" * 100)
    print("SHOP AFFORDABILITY (item price as % of cumulative gold at zone)")
    print("=" * 100)

    for snap in snapshots:
        if not snap.shop_items:
            continue

        print(f"\n{snap.zone_name} (Lv{snap.zone_level})  —  Cum gold: rush={snap.cumulative_gold_rush:.0f}G  mod={snap.cumulative_gold_moderate:.0f}G  grind={snap.cumulative_gold_grind:.0f}G")

        headers = ["Item", "Base Price", "% Rush", "% Moderate", "% Grind", "Affordable?"]
        rows: list[list[str]] = []

        for item_id in snap.shop_items:
            item = game_data.items.get(item_id)
            if item is None or item.base_price <= 0:
                continue

            price = calculate_buy_price(item.base_price, cha=0)
            pct_rush = (price / snap.cumulative_gold_rush * 100) if snap.cumulative_gold_rush > 0 else float("inf")
            pct_mod = (price / snap.cumulative_gold_moderate * 100) if snap.cumulative_gold_moderate > 0 else float("inf")
            pct_grind = (price / snap.cumulative_gold_grind * 100) if snap.cumulative_gold_grind > 0 else float("inf")

            # Affordable if <= 100% of cumulative gold for at least one style
            if pct_rush <= 100:
                afford = "YES (rush)"
            elif pct_mod <= 100:
                afford = "YES (mod)"
            elif pct_grind <= 100:
                afford = "YES (grind)"
            else:
                afford = "NO"

            rows.append([
                item.name,
                f"{price}G",
                f"{pct_rush:.1f}%" if pct_rush < 10000 else "---",
                f"{pct_mod:.1f}%" if pct_mod < 10000 else "---",
                f"{pct_grind:.1f}%" if pct_grind < 10000 else "---",
                afford,
            ])

        print(_fmt_table(headers, rows, col_align=["l", "r", "r", "r", "r", "l"]))


def _print_potion_check(game_data: GameData, snapshots: list[ZoneEconSnapshot]) -> None:
    """Validate potions cost ~1.5x avg enemy gold in their intro zone."""
    print("=" * 100)
    print("POTION PRICE CHECK (target: ~1.5x avg encounter gold in intro zone)")
    print("=" * 100)

    # Identify potion items (consumables with base_price > 0 and "potion" or "elixir" in name/id)
    potion_ids: set[str] = set()
    for item in game_data.items.values():
        if item.base_price > 0 and any(
            kw in item.id.lower() for kw in ("potion", "elixir")
        ):
            potion_ids.add(item.id)

    if not potion_ids:
        print("  No potions found in item registry.")
        return

    # Find intro zone for each potion (first zone where it appears in shop)
    potion_intro: dict[str, ZoneEconSnapshot] = {}
    for snap in snapshots:
        for pid in potion_ids:
            if pid in snap.shop_items and pid not in potion_intro:
                potion_intro[pid] = snap

    headers = ["Potion", "Base Price", "Buy (0 CHA)", "Intro Zone", "Avg Enc Gold", "Ratio", "Status"]
    rows: list[list[str]] = []

    target_ratio = 1.5
    tolerance = 0.5  # acceptable range: 1.0x to 2.0x

    for pid in sorted(potion_ids):
        item = game_data.items[pid]
        buy_price = calculate_buy_price(item.base_price, cha=0)
        snap = potion_intro.get(pid)

        if snap is None:
            rows.append([item.name, f"{item.base_price}G", f"{buy_price}G", "---", "---", "---", "NOT IN SHOP"])
            continue

        avg_gold = snap.avg_encounter_gold
        ratio = buy_price / avg_gold if avg_gold > 0 else 0.0

        if abs(ratio - target_ratio) <= tolerance:
            status = "OK"
        elif ratio < target_ratio - tolerance:
            status = "CHEAP"
        else:
            status = "EXPENSIVE"

        rows.append([
            item.name,
            f"{item.base_price}G",
            f"{buy_price}G",
            f"{snap.zone_name} (Lv{snap.zone_level})",
            f"{avg_gold:.0f}G",
            f"{ratio:.2f}x",
            status,
        ])

    print(_fmt_table(headers, rows, col_align=["l", "r", "r", "l", "r", "r", "l"]))


# ---------------------------------------------------------------------------
# cmd_progression (Step 5)
# ---------------------------------------------------------------------------

def cmd_progression(args: argparse.Namespace) -> None:
    """Full run simulation: level, gold, shop, abilities, weapon crossover at each zone."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    job = gd.jobs[job_id]

    econ_snaps = _compute_zone_economy(gd)
    xp_snaps = _compute_xp_progression(gd, job_id)

    if not econ_snaps or not xp_snaps:
        print("No zones found.")
        return

    # Build ability unlock lookup: level -> list of ability names
    unlock_map: dict[int, list[str]] = {}
    innate = gd.abilities.get(job.innate_ability_id)
    if innate:
        unlock_map.setdefault(1, []).append(innate.name)
    for unlock in getattr(job, "ability_unlocks", []):
        ability = gd.abilities.get(unlock.ability_id)
        if ability:
            unlock_map.setdefault(unlock.level, []).append(ability.name)

    # Determine primary offensive stat for crossover analysis
    primary_stat = max(
        [StatType.STR, StatType.MAG],
        key=lambda s: job.growth.effective_growth(s),
    )
    growth_rate = job.growth.effective_growth(primary_stat)

    # Gather weapons that scale off the primary stat
    weapons: dict[str, ItemScaling] = {}
    for item in gd.items.values():
        if item.scaling and item.scaling.stat == primary_stat:
            weapons[item.name] = item.scaling

    print("=" * 100)
    print(f"FULL RUN PROGRESSION: {job.name}")
    print(f"  Primary stat: {primary_stat.value} (growth +{growth_rate}/lv)")
    print("=" * 100)

    # Pair econ and xp snapshots by zone_id
    xp_by_zone: dict[str, ZoneXPSnapshot] = {s.zone_id: s for s in xp_snaps}

    for econ in econ_snaps:
        xp = xp_by_zone.get(econ.zone_id)
        if xp is None:
            continue

        print(f"\n--- {econ.zone_name} (Lv{econ.zone_level}) ---")

        # Level + XP
        print(f"  Level at exit:  rush={xp.level_at_exit_rush}  moderate={xp.level_at_exit_moderate}  grind={xp.level_at_exit_grind}")

        # Gold
        print(f"  Cumulative gold: rush={econ.cumulative_gold_rush:.0f}G  moderate={econ.cumulative_gold_moderate:.0f}G  grind={econ.cumulative_gold_grind:.0f}G")

        # Newly affordable items (rush scenario: can we afford it now?)
        newly_affordable: list[str] = []
        for item_id in econ.shop_items:
            item = gd.items.get(item_id)
            if item is None or item.base_price <= 0:
                continue
            buy = calculate_buy_price(item.base_price, cha=0)
            if buy <= econ.cumulative_gold_moderate:
                newly_affordable.append(f"{item.name} ({buy}G)")
        if newly_affordable:
            print(f"  Affordable (mod): {', '.join(newly_affordable)}")

        # Ability unlocks reached by this zone's exit level (moderate)
        exit_level = xp.level_at_exit_moderate
        unlocked_here: list[str] = []
        for lv, names in sorted(unlock_map.items()):
            if lv <= exit_level:
                for n in names:
                    unlocked_here.append(f"{n} (Lv{lv})")
        if unlocked_here:
            print(f"  Abilities unlocked: {', '.join(unlocked_here)}")

        # Weapon crossover status at this level (moderate exit level)
        if weapons:
            stat_val = growth_rate * exit_level
            weapon_outputs: dict[str, float] = {}
            for wname, wscaling in weapons.items():
                weapon_outputs[wname] = evaluate_item_scaling(wscaling, stat_val)
            best_weapon = max(weapon_outputs, key=lambda n: weapon_outputs[n])
            weapon_report = "  |  ".join(
                f"{n}={v:.0f}{'*' if n == best_weapon else ''}"
                for n, v in weapon_outputs.items()
            )
            print(f"  Best weapon @Lv{exit_level}: {best_weapon}  ({weapon_report})")

    # Summary table
    print(f"\n{'=' * 100}")
    print("SUMMARY TABLE (moderate play style)")
    print(f"{'=' * 100}")

    headers = ["Zone", "ZoneLv", "ExitLv", "Gold", "Best Weapon", "New Abilities"]
    rows: list[list[str]] = []

    prev_level = 0
    for econ in econ_snaps:
        xp = xp_by_zone.get(econ.zone_id)
        if xp is None:
            continue
        exit_lv = xp.level_at_exit_moderate

        # Best weapon at this level
        stat_val = growth_rate * exit_lv
        best = "---"
        if weapons:
            best = max(weapons, key=lambda n: evaluate_item_scaling(weapons[n], stat_val))

        # New abilities since last zone
        new_abs: list[str] = []
        for lv, names in sorted(unlock_map.items()):
            if prev_level < lv <= exit_lv:
                new_abs.extend(names)
        prev_level = exit_lv

        rows.append([
            econ.zone_id,
            str(econ.zone_level),
            str(exit_lv),
            f"{econ.cumulative_gold_moderate:.0f}G",
            best,
            ", ".join(new_abs) if new_abs else "---",
        ])

    print(_fmt_table(headers, rows, col_align=["l", "r", "r", "r", "l", "l"]))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="heresiarch-sim",
        description="Balance simulation tool for Heresiarch",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # sweep
    p = sub.add_parser("sweep", help="Weapon scaling sweep across levels")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--stat", default="STR", help="Stat to sweep (STR, MAG, etc.)")
    p.add_argument("--hypo", nargs="*", help="Hypothetical weapons: Name:TYPE:param=val,...")
    p.set_defaults(func=cmd_sweep)

    # crossover
    p = sub.add_parser("crossover", help="Find weapon crossover points")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--stat", default="STR", help="Stat to analyze")
    p.add_argument("--hypo", nargs="*", help="Hypothetical weapons")
    p.set_defaults(func=cmd_crossover)

    # build
    p = sub.add_parser("build", help="Compare builds at a specific level")
    p.add_argument("--job", default="berserker", help="Job ID")
    p.add_argument("--level", type=int, default=50, help="Character level")
    p.add_argument("--enemy", default=None, help="Enemy ID for damage calc")
    p.add_argument("--zone", type=int, default=None, help="Enemy zone level")
    p.set_defaults(func=cmd_build)

    # converter
    p = sub.add_parser("converter", help="Analyze converter items")
    p.add_argument("--job", default="martyr", help="Job ID")
    p.add_argument("--converter", default="fortress_ring", help="Converter item ID")
    p.add_argument("--weapon", default=None, help="Weapon to pair with converter")
    p.add_argument("--sigmoid-max", type=float, default=0, help="Sigmoid max output")
    p.add_argument("--sigmoid-mid", type=float, default=300, help="Sigmoid midpoint")
    p.add_argument("--sigmoid-rate", type=float, default=0.015, help="Sigmoid growth rate")
    p.set_defaults(func=cmd_converter)

    # sigmoid explorer
    p = sub.add_parser("sigmoid", help="Explore sigmoid curve shapes")
    p.add_argument("--max", type=float, required=True, help="Max output")
    p.add_argument("--mid", type=float, required=True, help="Midpoint")
    p.add_argument("--rate", type=float, required=True, help="Growth rate")
    p.set_defaults(func=cmd_sigmoid)

    # ability-dpr
    p = sub.add_parser("ability-dpr", help="DPR analysis for offensive abilities")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--abilities", nargs="*", default=None, help="Specific ability IDs (default: all offensive)")
    p.add_argument("--def", dest="def_value", type=int, default=_DEFAULT_ENEMY_DEF, help="Enemy DEF for physical calcs")
    p.set_defaults(func=cmd_ability_dpr)

    # ability-compare
    p = sub.add_parser("ability-compare", help="Side-by-side ability comparison with crossover analysis")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--abilities", nargs="+", required=True, help="2-3 ability IDs to compare")
    p.add_argument("--def", dest="def_value", type=int, default=_DEFAULT_ENEMY_DEF, help="Enemy DEF for physical calcs")
    p.set_defaults(func=cmd_ability_compare)

    # job-curve
    p = sub.add_parser("job-curve", help="Full ability progression curve for a job")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--def", dest="def_value", type=int, default=_DEFAULT_ENEMY_DEF, help="Enemy DEF for physical calcs")
    p.set_defaults(func=cmd_job_curve)

    # economy
    p = sub.add_parser("economy", help="Zone economy analysis: gold, overstay, pilfer impact")
    p.add_argument("--overstay", action="store_true", help="Show per-battle overstay decay")
    p.set_defaults(func=cmd_economy)

    # xp-curve
    p = sub.add_parser("xp-curve", help="XP progression across zones (rush/moderate/grind)")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.set_defaults(func=cmd_xp_curve)

    # enemy-stats
    p = sub.add_parser("enemy-stats", help="Enemy stat tables at each zone level")
    p.add_argument("--enemies", nargs="*", default=None, help="Specific enemy IDs (default: all)")
    p.set_defaults(func=cmd_enemy_stats)

    # shop-pricing
    p = sub.add_parser("shop-pricing", help="Shop affordability and potion price validation")
    p.add_argument("--potions-only", action="store_true", help="Only show potion price check")
    p.set_defaults(func=cmd_shop_pricing)

    # progression
    p = sub.add_parser("progression", help="Full run progression: level, gold, abilities, weapons per zone")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.set_defaults(func=cmd_progression)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
