"""Heresiarch balance simulation tool.

CLI entry point and shared utilities. Analysis and economy subcommands
live in sim_analysis.py and sim_economy.py respectively.

Usage:
    python -m heresiarch.tools.sim <subcommand> [options]

Subcommands:
    sweep, crossover, build        — Weapon/build analysis (sim_analysis)
    ability-dpr, ability-compare   — Ability damage analysis (sim_analysis)
    job-curve                      — Job progression curves (sim_analysis)
    converter, sigmoid             — Utility analysis (this file)
    economy, xp-curve, enemy-stats — Zone/economy analysis (sim_economy)
    shop-pricing, progression      — Progression analysis (sim_economy)
    lodge-tuning                   — Lodge cost analysis (sim_economy)
    combat                         — Full combat simulation (combat_sim)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from heresiarch.engine.data_loader import load_all
from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
    evaluate_conversion,
    evaluate_item_scaling,
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

from heresiarch.engine.models.items import (
    ConversionEffect,
    EquipType,
    Item,
    ItemScaling,
    ScalingType,
)
from heresiarch.engine.models.stats import StatType

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData


# ---------------------------------------------------------------------------
# Table formatting (shared by sim_analysis, sim_economy)
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
# Shared utilities (imported by sim_analysis, sim_economy)
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


# ---------------------------------------------------------------------------
# Converter / sigmoid analysis (small utilities, kept in main module)
# ---------------------------------------------------------------------------

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
# CLI commands (converter, sigmoid, combat — small enough to stay here)
# ---------------------------------------------------------------------------

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
                id="test_conv", name=conv_name, equip_type=EquipType.ACCESSORY,
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


def cmd_combat(args: argparse.Namespace) -> None:
    """General-purpose combat sim using the real CombatEngine."""
    from heresiarch.tools.combat_sim import (
        CombatSimulator,
        EncounterConfig,
        Scenario,
        format_sim_result,
        parse_between,
        parse_cycle,
    )

    gd = _load_game_data()
    if args.job not in gd.jobs:
        print(f"Unknown job: {args.job}. Available: {', '.join(gd.jobs.keys())}")
        return

    cycle = parse_cycle(args.cycle)
    between = parse_between(args.between or "")

    # Parse equipment
    equipment: dict[str, str | None] = {
        "WEAPON": None, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None,
    }
    if args.equipment:
        for token in args.equipment.split(","):
            token = token.strip()
            if "=" in token:
                slot, item_id = token.split("=", 1)
                equipment[slot.upper()] = item_id
            else:
                equipment["WEAPON"] = token

    # Build encounters
    encounters: list[EncounterConfig] = []
    if not args.zone and args.enemy:
        encounters = [EncounterConfig(
            enemy_id=args.enemy,
            enemy_level=args.enemy_level,
            enemy_count=args.enemy_count,
        )]

    scenario = Scenario(
        job_id=args.job,
        level=args.level,
        equipment=equipment,
        cycle=cycle,
        zone_id=args.zone,
        encounters=encounters,
        between_encounters=between,
        seed=args.seed,
    )

    sim = CombatSimulator(gd, seed=args.seed)
    result = sim.run(scenario)
    print(format_sim_result(result, verbose=not args.quiet))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Deferred imports to avoid circular dependency
    from heresiarch.tools.sim_analysis import (
        _DEFAULT_ENEMY_DEF,
        _DEFAULT_ENEMY_RES,
        cmd_ability_compare,
        cmd_ability_dpr,
        cmd_build,
        cmd_crossover,
        cmd_job_curve,
        cmd_sweep,
    )
    from heresiarch.tools.sim_economy import (
        cmd_economy,
        cmd_enemy_stats,
        cmd_lodge_tuning,
        cmd_progression,
        cmd_shop_pricing,
        cmd_xp_curve,
    )

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
    p.add_argument("--res", dest="res_value", type=int, default=_DEFAULT_ENEMY_RES, help="Enemy RES for magical calcs")
    p.set_defaults(func=cmd_ability_dpr)

    # ability-compare
    p = sub.add_parser("ability-compare", help="Side-by-side ability comparison with crossover analysis")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--abilities", nargs="+", required=True, help="2-3 ability IDs to compare")
    p.add_argument("--def", dest="def_value", type=int, default=_DEFAULT_ENEMY_DEF, help="Enemy DEF for physical calcs")
    p.add_argument("--res", dest="res_value", type=int, default=_DEFAULT_ENEMY_RES, help="Enemy RES for magical calcs")
    p.set_defaults(func=cmd_ability_compare)

    # job-curve
    p = sub.add_parser("job-curve", help="Full ability progression curve for a job")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--def", dest="def_value", type=int, default=_DEFAULT_ENEMY_DEF, help="Enemy DEF for physical calcs")
    p.add_argument("--res", dest="res_value", type=int, default=_DEFAULT_ENEMY_RES, help="Enemy RES for magical calcs")
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

    # lodge-tuning
    p = sub.add_parser("lodge-tuning", help="Lodge cost analysis with dynamic HP-based pricing model")
    p.add_argument("--job", default="einherjar", help="Job ID")
    p.add_argument("--party-size", type=int, default=1, help="Party size for total HP calc (default: 1)")
    p.set_defaults(func=cmd_lodge_tuning)

    # combat — general-purpose combat simulator
    p = sub.add_parser("combat", help="Simulate combat with scripted action cycles against encounters")
    p.add_argument("--job", default="berserker", help="Job ID")
    p.add_argument("--level", type=int, default=1, help="Player level")
    p.add_argument("--cycle", default="S,S,S,C3", help="Action cycle DSL: S=survive, A=attack, A:id=ability, C3=cheat 3AP, I:id=item")
    p.add_argument("--zone", default=None, help="Zone ID — simulates all encounters in order")
    p.add_argument("--enemy", default=None, help="Enemy template ID (for single encounter)")
    p.add_argument("--enemy-level", type=int, default=1, help="Enemy level")
    p.add_argument("--enemy-count", type=int, default=1, help="Number of enemies")
    p.add_argument("--equipment", default=None, help="Equipment: WEAPON=id,ARMOR=id or bare item_id for weapon")
    p.add_argument("--between", default=None, help="Between-encounter items: 1:minor_potion,2:minor_potion")
    p.add_argument("--seed", type=int, default=42, help="RNG seed")
    p.add_argument("--quiet", action="store_true", help="Summary only, no per-round output")
    p.set_defaults(func=cmd_combat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
