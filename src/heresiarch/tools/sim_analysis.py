"""Balance analysis: weapon sweeps, ability DPR, build comparisons, job curves.

Extracted from sim.py. Analysis functions focused on damage and ability mechanics.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_magical_damage,
    calculate_max_hp,
    calculate_physical_damage,
    calculate_speed_bonus,
    calculate_stats_at_level,
    evaluate_conversion,
    evaluate_item_scaling,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    DamageQuality,
)
from heresiarch.engine.models.items import (
    ConversionEffect,
    EquipType,
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
        level: int
        ability_id: str

from heresiarch.engine.models.stats import StatType
from heresiarch.tools.sim import (
    _fmt_table,
    _get_job_growth_rate,
    _get_weapons_for_stat,
    _load_game_data,
    parse_hypo_weapon,
)

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData

# Default enemy stats for DPR analysis
_DEFAULT_ENEMY_DEF: int = 50
_DEFAULT_ENEMY_RES: int = 50


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
        bonus = calculate_speed_bonus(eff.SPD, 0)  # no enemy context in build compare

        row = [
            build_name,
            str(eff.STR), str(eff.MAG), str(eff.DEF), str(eff.RES), str(eff.SPD),
            str(hp), str(bonus),
        ]

        if enemy_stats:
            heavy = calculate_physical_damage(15, 0.8, eff.STR, enemy_stats.DEF)
            bolt = calculate_magical_damage(10, 0.7, eff.MAG, target_res=enemy_stats.RES)
            partial = max(1, int(calculate_physical_damage(5, 0.5, eff.STR, enemy_stats.DEF) * 0.5))
            dpt = heavy + bonus * partial
            row.extend([str(heavy), str(bolt), str(dpt)])

        rows.append(row)

    result = _fmt_table(headers, rows, col_align=["l"] + ["r"] * (len(headers) - 1))
    if enemy_stats:
        result += f"\n\nEnemy: {enemy_id} Zone {zone_level} — HP={enemy_hp} DEF={enemy_stats.DEF} RES={enemy_stats.RES}"
    return result

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

def ability_dpr(
    game_data: GameData,
    job_id: str,
    ability_ids: list[str] | None = None,
    levels: list[int] | None = None,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
    enemy_res: int = _DEFAULT_ENEMY_RES,
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
                basic_attack, stats.STR, stats.MAG, enemy_def, enemy_res,
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
            dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def, enemy_res)
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
            game_data, job, surge_abilities, levels, enemy_def, enemy_res,
        ))

    # DOT total-damage details
    dot_abilities = [
        a for a in abilities
        if any(e.quality == DamageQuality.DOT for e in a.effects)
    ]
    if dot_abilities:
        detail_sections.append(_format_dot_details(
            game_data, job, dot_abilities, levels, enemy_def, enemy_res,
        ))

    # PIERCE comparison (with/without armor)
    pierce_abilities = [
        a for a in abilities
        if any(e.pierce_percent > 0 for e in a.effects)
    ]
    if pierce_abilities:
        detail_sections.append(_format_pierce_details(
            game_data, job, pierce_abilities, levels, enemy_def, enemy_res,
        ))

    # CHAIN AoE efficiency
    chain_abilities = [
        a for a in abilities
        if any(e.quality == DamageQuality.CHAIN for e in a.effects)
    ]
    if chain_abilities:
        detail_sections.append(_format_chain_details(
            game_data, job, chain_abilities, levels, enemy_def, enemy_res,
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
    enemy_res: int,
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
            base_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def, enemy_res)
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
    enemy_res: int,
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
            hit_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def, enemy_res)
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
    enemy_res: int,
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
    enemy_res: int,
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
            per_hit = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def, enemy_res)
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
    enemy_res: int = _DEFAULT_ENEMY_RES,
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
                ability, stats.STR, stats.MAG, enemy_def, enemy_res,
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
                    ability_a, stats.STR, stats.MAG, enemy_def, enemy_res,
                )
                dmg_b = _compute_ability_total_damage(
                    ability_b, stats.STR, stats.MAG, enemy_def, enemy_res,
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
                    ability_a, final_stats.STR, final_stats.MAG, enemy_def, enemy_res,
                )
                dmg_b = _compute_ability_total_damage(
                    ability_b, final_stats.STR, final_stats.MAG, enemy_def, enemy_res,
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
    enemy_res: int = _DEFAULT_ENEMY_RES,
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
        innate_dmg = _compute_ability_total_damage(innate, stats.STR, stats.MAG, enemy_def, enemy_res)
        ba = game_data.abilities.get("basic_attack")
        ba_dmg = _compute_ability_total_damage(ba, stats.STR, stats.MAG, enemy_def, enemy_res) if ba else 0
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
        dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def, enemy_res)
        ba = game_data.abilities.get("basic_attack")
        ba_dmg = _compute_ability_total_damage(ba, stats.STR, stats.MAG, enemy_def, enemy_res) if ba else 0

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

    result = f"Job: {job.name} — Ability Progression (vs DEF={enemy_def} RES={enemy_res})\n"
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
                if acc.conversion and acc.equip_type == EquipType.ACCESSORY:
                    builds[f"{item.name} + {acc.name}"] = [item.id, acc.id]
            builds[item.name] = build_items

    print(f"Job: {args.job} Lv{args.level} (primary: {primary.value})\n")
    print(build_compare(
        gd, args.job, args.level, builds,
        enemy_id=args.enemy, zone_level=args.zone,
    ))

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

    print(f"Job: {gd.jobs[job_id].name} (enemy DEF={args.def_value} RES={args.res_value})\n")
    print(ability_dpr(gd, job_id, ability_ids=ability_ids, enemy_def=args.def_value, enemy_res=args.res_value))

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

    print(f"Job: {gd.jobs[job_id].name} (enemy DEF={args.def_value} RES={args.res_value})\n")
    print(ability_compare(gd, job_id, args.abilities, enemy_def=args.def_value, enemy_res=args.res_value))

def cmd_job_curve(args: argparse.Namespace) -> None:
    """Full ability progression curve for a job."""
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    print(job_ability_curve(gd, job_id, enemy_def=args.def_value, enemy_res=args.res_value))

