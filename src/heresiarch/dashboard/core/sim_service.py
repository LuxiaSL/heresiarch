"""Structured-data simulation functions.

Each function mirrors a sim.py CLI command but returns Pydantic models
instead of formatted text. The engine formulas are called directly.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import (
    _sigmoid,
    calculate_speed_bonus,
    calculate_buy_price,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_levels_gained,
    calculate_magical_damage,
    calculate_max_hp,
    calculate_physical_damage,
    calculate_stats_at_level,
    calculate_xp_reward,
    evaluate_conversion,
    evaluate_item_scaling,
    xp_for_level,
)
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
from heresiarch.engine.models.stats import StatType

from heresiarch.dashboard.core.response_models import (
    AbilityComparePoint,
    AbilityCompareResult,
    AbilityDprResult,
    AbilityDprRow,
    BreakevenEvent,
    BuildCompareResult,
    BuildSnapshot,
    ChainBreakdown,
    ConverterCompareResult,
    ConverterPoint,
    CrossoverEvent,
    CrossoverResult,
    DotBreakdown,
    EconomyResult,
    EnemyStatsEntry,
    EnemyStatsResult,
    EnemyZoneStats,
    JobCurveResult,
    JobCurveUnlock,
    PierceBreakdown,
    PilferImpact,
    ProgressionResult,
    ProgressionZone,
    ShopItem,
    ShopPricingResult,
    ShopZone,
    PotionCheck,
    SigmoidPoint,
    SigmoidResult,
    SurgeBreakdown,
    WeaponSweepPoint,
    WeaponSweepResult,
    XpCurveResult,
    XpMilestone,
    ZoneEconomySnapshot,
    ZoneXpSnapshot,
)

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.jobs import JobTemplate

_DEFAULT_LEVELS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 99]
_DEFAULT_ENEMY_DEF = 50
_OVERSTAY_MODERATE = 5
_OVERSTAY_GRIND = 20


# ---------------------------------------------------------------------------
# Helpers (shared with sim.py)
# ---------------------------------------------------------------------------

from heresiarch.tools.shared import compute_ability_total_damage as _compute_ability_total_damage
from heresiarch.tools.shared import compute_effect_damage as _compute_effect_damage


# ---------------------------------------------------------------------------
# 1. Weapon sweep
# ---------------------------------------------------------------------------

def weapon_sweep_data(
    job_id: str,
    stat: str,
    growth_rate: int,
    weapons: dict[str, ItemScaling],
    levels: list[int] | None = None,
) -> WeaponSweepResult:
    if levels is None:
        levels = _DEFAULT_LEVELS

    points: list[WeaponSweepPoint] = []
    weapon_names = list(weapons.keys())

    for lv in levels:
        stat_val = growth_rate * lv
        outputs: dict[str, float] = {}
        effective: dict[str, int] = {}
        for name, scaling in weapons.items():
            out = evaluate_item_scaling(scaling, stat_val)
            outputs[name] = round(out, 1)
            effective[name] = stat_val + max(0, int(out))

        best = max(outputs, key=lambda n: outputs[n])
        points.append(WeaponSweepPoint(
            level=lv, stat_value=stat_val,
            outputs=outputs, effective=effective, best=best,
        ))

    return WeaponSweepResult(
        job_id=job_id, stat=stat, growth_rate=growth_rate,
        weapon_names=weapon_names, points=points,
    )


# ---------------------------------------------------------------------------
# 2. Crossovers
# ---------------------------------------------------------------------------

def find_crossovers_data(
    job_id: str,
    stat: str,
    growth_rate: int,
    weapons: dict[str, ItemScaling],
    max_level: int = 99,
) -> CrossoverResult:
    names = list(weapons.keys())
    crossovers: list[CrossoverEvent] = []
    breakevens: list[BreakevenEvent] = []

    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            a_was_better: bool | None = None
            for lv in range(1, max_level + 1):
                stat_val = growth_rate * lv
                val_a = evaluate_item_scaling(weapons[name_a], stat_val)
                val_b = evaluate_item_scaling(weapons[name_b], stat_val)
                a_better = val_a >= val_b
                if a_was_better is not None and a_better != a_was_better:
                    winner = name_a if a_better else name_b
                    loser = name_b if a_better else name_a
                    crossovers.append(CrossoverEvent(
                        winner=winner, loser=loser, level=lv,
                        winner_value=val_a if a_better else val_b,
                        loser_value=val_b if a_better else val_a,
                    ))
                a_was_better = a_better

    for name, scaling in weapons.items():
        if scaling.scaling_type == ScalingType.DEGENERATE:
            for lv in range(1, max_level + 1):
                stat_val = growth_rate * lv
                val = evaluate_item_scaling(scaling, stat_val)
                if val >= 0:
                    breakevens.append(BreakevenEvent(
                        weapon=name, level=lv, stat_value=stat_val, output=round(val, 1),
                    ))
                    break

    return CrossoverResult(
        job_id=job_id, stat=stat, growth_rate=growth_rate,
        crossovers=crossovers, breakevens=breakevens,
    )


# ---------------------------------------------------------------------------
# 3. Build compare
# ---------------------------------------------------------------------------

def build_compare_data(
    game_data: GameData,
    job_id: str,
    level: int,
    builds: dict[str, list[str]] | None = None,
    enemy_id: str | None = None,
    zone_level: int | None = None,
) -> BuildCompareResult:
    job = game_data.jobs[job_id]
    base_stats = calculate_stats_at_level(job.growth, level)

    # Auto-generate builds if none provided
    if builds is None:
        builds = _auto_builds(game_data, job)

    # Optionally create enemy for damage calcs
    enemy_stats = None
    enemy_hp = 0
    enemy_info = None
    if enemy_id and zone_level:
        import random as _rand
        from heresiarch.engine.combat import CombatEngine
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
        enemy_info = f"{enemy_id} Zone {zone_level} — HP={enemy_hp} DEF={enemy_stats.DEF} RES={enemy_stats.RES}"

    snapshots: list[BuildSnapshot] = []
    for build_name, item_ids in builds.items():
        items = [game_data.items[iid] for iid in item_ids if iid in game_data.items]
        eff = calculate_effective_stats(base_stats, items, [])
        hp = calculate_max_hp(job.base_hp, job.hp_growth, level, eff.DEF)
        # Speed bonus depends on enemy SPD; use 0 as placeholder for build comparisons
        bonus = calculate_speed_bonus(eff.SPD, 0)

        snap = BuildSnapshot(
            name=build_name,
            items=item_ids,
            stats=eff.model_dump(),
            hp=hp,
            bonus_actions=bonus,
        )
        if enemy_stats:
            heavy = calculate_physical_damage(15, 0.8, eff.STR, enemy_stats.DEF)
            bolt = calculate_magical_damage(10, 0.7, eff.MAG)
            partial = max(1, int(calculate_physical_damage(5, 0.5, eff.STR, enemy_stats.DEF) * 0.5))
            snap.heavy_damage = heavy
            snap.bolt_damage = bolt
            snap.dpt = heavy + bonus * partial
        snapshots.append(snap)

    return BuildCompareResult(
        job_id=job_id, level=level, builds=snapshots, enemy_info=enemy_info,
    )


def _auto_builds(game_data: GameData, job: JobTemplate) -> dict[str, list[str]]:
    """Auto-generate builds from all weapons matching the job's primary stat."""
    primary = max(
        [StatType.STR, StatType.MAG],
        key=lambda s: job.growth.effective_growth(s),
    )
    builds: dict[str, list[str]] = {}
    for item in game_data.items.values():
        if item.scaling and item.scaling.stat == primary:
            builds[item.name] = [item.id]
            for acc in game_data.items.values():
                if acc.conversion and acc.slot in (EquipSlot.ACCESSORY_1, EquipSlot.ACCESSORY_2):
                    builds[f"{item.name} + {acc.name}"] = [item.id, acc.id]
    return builds


# ---------------------------------------------------------------------------
# 4. Converter compare
# ---------------------------------------------------------------------------

def converter_compare_data(
    game_data: GameData,
    job_id: str,
    converter_id: str,
    levels: list[int] | None = None,
) -> ConverterCompareResult:
    if levels is None:
        levels = [10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 99]

    item = game_data.items[converter_id]
    conv = item.conversion
    if conv is None:
        raise ValueError(f"Item '{converter_id}' has no conversion effect")

    job = game_data.jobs[job_id]
    rate = job.growth.effective_growth(conv.source_stat)

    converters: dict[str, ConversionEffect] = {f"{item.name} (current)": conv}

    points: list[ConverterPoint] = []
    for lv in levels:
        stat_val = rate * lv
        outputs: dict[str, int] = {}
        for name, c in converters.items():
            outputs[name] = evaluate_conversion(c, stat_val)
        points.append(ConverterPoint(level=lv, source_stat=stat_val, outputs=outputs))

    return ConverterCompareResult(
        job_id=job_id, converter_id=converter_id,
        source_stat=conv.source_stat.value, target_stat=conv.target_stat.value,
        growth_rate=rate, points=points,
    )


# ---------------------------------------------------------------------------
# 5. Sigmoid explorer
# ---------------------------------------------------------------------------

def sigmoid_explorer_data(
    max_output: float,
    midpoint: float,
    rate: float,
    stat_values: list[int] | None = None,
) -> SigmoidResult:
    if stat_values is None:
        stat_values = list(range(0, 700, 25))

    points: list[SigmoidPoint] = []
    for stat in stat_values:
        out = _sigmoid(stat, max_output, midpoint, rate)
        pct = (out / max_output * 100) if max_output > 0 else 0.0
        points.append(SigmoidPoint(stat=stat, output=out, pct_of_max=round(pct, 1)))

    return SigmoidResult(max_output=max_output, midpoint=midpoint, rate=rate, points=points)


# ---------------------------------------------------------------------------
# 6. Ability DPR
# ---------------------------------------------------------------------------

def ability_dpr_data(
    game_data: GameData,
    job_id: str,
    ability_ids: list[str] | None = None,
    levels: list[int] | None = None,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> AbilityDprResult:
    if levels is None:
        levels = [1, 5, 10, 15, 20, 50, 99]

    job = game_data.jobs[job_id]

    # Build unlock lookup
    unlock_map: dict[str, int] = {job.innate_ability_id: 1}
    for unlock in job.ability_unlocks:
        unlock_map[unlock.ability_id] = unlock.level

    # Collect abilities
    if ability_ids is not None:
        abilities = [game_data.abilities[aid] for aid in ability_ids if aid in game_data.abilities]
    else:
        abilities = [a for a in game_data.abilities.values() if a.category == AbilityCategory.OFFENSIVE]

    basic_attack = game_data.abilities.get("basic_attack")
    if basic_attack and basic_attack not in abilities:
        abilities.insert(0, basic_attack)

    # Pre-compute basic_attack damage at each level
    ba_damages: dict[int, int] = {}
    if basic_attack:
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            ba_damages[lv] = _compute_ability_total_damage(basic_attack, stats.STR, stats.MAG, enemy_def)

    rows: list[AbilityDprRow] = []
    for ability in abilities:
        quality_str = "---"
        scaling_str = "STR"
        coeff_val = 0.0
        for eff in ability.effects:
            if eff.base_damage != 0 or eff.scaling_coefficient > 0:
                quality_str = eff.quality.value if eff.quality != DamageQuality.NONE else "---"
                scaling_str = eff.stat_scaling.value if eff.stat_scaling else "STR"
                coeff_val = eff.scaling_coefficient
                break

        damage_by_level: dict[int, int] = {}
        ratio_by_level: dict[int, float] = {}
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            damage_by_level[lv] = dmg
            ba_dmg = ba_damages.get(lv, 0)
            if ba_dmg > 0 and ability.id != "basic_attack":
                ratio_by_level[lv] = round(dmg / ba_dmg, 2)
            else:
                ratio_by_level[lv] = 1.0

        rows.append(AbilityDprRow(
            ability_id=ability.id,
            ability_name=ability.name,
            quality=quality_str,
            scaling_stat=scaling_str,
            coefficient=coeff_val,
            unlock_level=unlock_map.get(ability.id, "---"),
            damage_by_level=damage_by_level,
            ratio_by_level=ratio_by_level,
        ))

    # Quality breakdowns
    surge_breakdowns = _surge_breakdowns(job, abilities, levels, enemy_def)
    dot_breakdowns = _dot_breakdowns(job, abilities, levels, enemy_def)
    pierce_breakdowns = _pierce_breakdowns(job, abilities, levels, enemy_def)
    chain_breakdowns = _chain_breakdowns(job, abilities, levels, enemy_def)

    return AbilityDprResult(
        job_id=job_id, job_name=job.name, enemy_def=enemy_def, levels=levels,
        rows=rows,
        surge_breakdowns=surge_breakdowns,
        dot_breakdowns=dot_breakdowns,
        pierce_breakdowns=pierce_breakdowns,
        chain_breakdowns=chain_breakdowns,
    )


def _surge_breakdowns(job: JobTemplate, abilities: list[Ability], levels: list[int], enemy_def: int) -> list[SurgeBreakdown]:
    result: list[SurgeBreakdown] = []
    for ability in abilities:
        surge_eff = next((e for e in ability.effects if e.quality == DamageQuality.SURGE), None)
        if not surge_eff:
            continue
        bonus = surge_eff.surge_stack_bonus
        data: list[dict[str, int | float]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            base_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            row: dict[str, int | float] = {"level": lv, "base": base_dmg}
            for stacks in [1, 2, 3, 4, 5]:
                row[f"x{stacks}"] = int(base_dmg * (1.0 + bonus * stacks))
            data.append(row)
        result.append(SurgeBreakdown(ability_name=ability.name, stack_bonus=bonus, data=data))
    return result


def _dot_breakdowns(job: JobTemplate, abilities: list[Ability], levels: list[int], enemy_def: int) -> list[DotBreakdown]:
    result: list[DotBreakdown] = []
    for ability in abilities:
        dot_eff = next((e for e in ability.effects if e.quality == DamageQuality.DOT), None)
        if not dot_eff:
            continue
        duration = dot_eff.duration_rounds
        tick_base = max(1, int(dot_eff.base_damage * 0.5))
        data: list[dict[str, int]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            hit_dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            total = hit_dmg + tick_base * duration
            data.append({"level": lv, "hit_dmg": hit_dmg, "tick": tick_base, "total": total})
        result.append(DotBreakdown(ability_name=ability.name, duration=duration, tick_base=tick_base, data=data))
    return result


def _pierce_breakdowns(job: JobTemplate, abilities: list[Ability], levels: list[int], enemy_def: int) -> list[PierceBreakdown]:
    result: list[PierceBreakdown] = []
    def_values = [25, 50, 100, 150, 200]
    for ability in abilities:
        pierce_eff = next((e for e in ability.effects if e.pierce_percent > 0), None)
        if not pierce_eff:
            continue
        pct = pierce_eff.pierce_percent
        data: list[dict[str, int | float]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            row: dict[str, int | float] = {"level": lv}
            for d in def_values:
                with_pierce = calculate_physical_damage(
                    pierce_eff.base_damage, pierce_eff.scaling_coefficient,
                    stats.STR, d, pierce_percent=pct,
                )
                without_pierce = calculate_physical_damage(
                    pierce_eff.base_damage, pierce_eff.scaling_coefficient,
                    stats.STR, d, pierce_percent=0.0,
                )
                row[f"pierce_def_{d}"] = with_pierce
                row[f"normal_def_{d}"] = without_pierce
            data.append(row)
        result.append(PierceBreakdown(ability_name=ability.name, pierce_pct=pct, data=data))
    return result


def _chain_breakdowns(job: JobTemplate, abilities: list[Ability], levels: list[int], enemy_def: int) -> list[ChainBreakdown]:
    result: list[ChainBreakdown] = []
    for ability in abilities:
        chain_eff = next((e for e in ability.effects if e.quality == DamageQuality.CHAIN), None)
        if not chain_eff:
            continue
        ratio = chain_eff.chain_damage_ratio
        data: list[dict[str, int]] = []
        for lv in levels:
            stats = calculate_stats_at_level(job.growth, lv)
            per_hit = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
            row: dict[str, int] = {"level": lv, "per_hit": per_hit}
            for n in [1, 2, 3, 4]:
                row[f"{n}T"] = per_hit * n
            data.append(row)
        result.append(ChainBreakdown(ability_name=ability.name, chain_ratio=ratio, data=data))
    return result


# ---------------------------------------------------------------------------
# 7. Ability compare
# ---------------------------------------------------------------------------

def ability_compare_data(
    game_data: GameData,
    job_id: str,
    ability_ids: list[str],
    levels: list[int] | None = None,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> AbilityCompareResult:
    if levels is None:
        levels = list(range(1, 100))

    job = game_data.jobs[job_id]
    abilities = [game_data.abilities[aid] for aid in ability_ids]
    names = [a.name for a in abilities]

    display_levels = [lv for lv in [1, 5, 10, 15, 20, 30, 50, 70, 99] if lv in levels]

    points: list[AbilityComparePoint] = []
    for lv in display_levels:
        stats = calculate_stats_at_level(job.growth, lv)
        damages: dict[str, int] = {}
        for ability in abilities:
            damages[ability.name] = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
        best = max(damages, key=lambda n: damages[n])
        points.append(AbilityComparePoint(
            level=lv, str_val=stats.STR, mag_val=stats.MAG, damages=damages, best=best,
        ))

    # Find crossovers across full level range
    crossovers: list[CrossoverEvent] = []
    for i, ability_a in enumerate(abilities):
        for ability_b in abilities[i + 1:]:
            a_was_better: bool | None = None
            for lv in range(1, 100):
                stats = calculate_stats_at_level(job.growth, lv)
                dmg_a = _compute_ability_total_damage(ability_a, stats.STR, stats.MAG, enemy_def)
                dmg_b = _compute_ability_total_damage(ability_b, stats.STR, stats.MAG, enemy_def)
                a_better = dmg_a >= dmg_b
                if a_was_better is not None and a_better != a_was_better:
                    winner = ability_a.name if a_better else ability_b.name
                    loser = ability_b.name if a_better else ability_a.name
                    crossovers.append(CrossoverEvent(
                        winner=winner, loser=loser, level=lv,
                        winner_value=float(dmg_a if a_better else dmg_b),
                        loser_value=float(dmg_b if a_better else dmg_a),
                    ))
                a_was_better = a_better

    return AbilityCompareResult(
        job_id=job_id, enemy_def=enemy_def, ability_names=names,
        points=points, crossovers=crossovers,
    )


# ---------------------------------------------------------------------------
# 8. Job ability curve
# ---------------------------------------------------------------------------

def job_ability_curve_data(
    game_data: GameData,
    job_id: str,
    enemy_def: int = _DEFAULT_ENEMY_DEF,
) -> JobCurveResult:
    job = game_data.jobs[job_id]
    unlocks: list[JobCurveUnlock] = []
    ba = game_data.abilities.get("basic_attack")

    def _make_unlock(ability: Ability, lv: int) -> JobCurveUnlock:
        stats = calculate_stats_at_level(job.growth, lv)
        dmg = _compute_ability_total_damage(ability, stats.STR, stats.MAG, enemy_def)
        ba_dmg = _compute_ability_total_damage(ba, stats.STR, stats.MAG, enemy_def) if ba else 0
        quality = "---"
        scaling = "---"
        for eff in ability.effects:
            if eff.base_damage != 0 or eff.scaling_coefficient > 0:
                quality = eff.quality.value if eff.quality != DamageQuality.NONE else "---"
                scaling = eff.stat_scaling.value if eff.stat_scaling else "STR"
                break
        return JobCurveUnlock(
            unlock_level=lv, ability_id=ability.id, ability_name=ability.name,
            category=ability.category.value, quality=quality, scaling_stat=scaling,
            damage_at_unlock=dmg, basic_attack_at_unlock=ba_dmg,
            ratio_vs_basic=round(dmg / ba_dmg, 2) if ba_dmg > 0 else 0.0,
        )

    innate = game_data.abilities.get(job.innate_ability_id)
    if innate:
        unlocks.append(_make_unlock(innate, 1))

    for unlock in sorted(job.ability_unlocks, key=lambda u: u.level):
        ability = game_data.abilities.get(unlock.ability_id)
        if ability:
            unlocks.append(_make_unlock(ability, unlock.level))

    strongest = None
    first_spike = None
    offensive = [u for u in unlocks if u.damage_at_unlock > 0]
    if offensive:
        best = max(offensive, key=lambda u: u.ratio_vs_basic)
        strongest = f"{best.ability_name} at Lv{best.unlock_level} ({best.ratio_vs_basic:.2f}x)"
        spike = next((u for u in offensive if u.ratio_vs_basic > 1.5), None)
        if spike:
            first_spike = f"{spike.ability_name} at Lv{spike.unlock_level}"

    return JobCurveResult(
        job_id=job_id, job_name=job.name, enemy_def=enemy_def,
        unlocks=unlocks, strongest_unlock=strongest, first_power_spike=first_spike,
    )


# ---------------------------------------------------------------------------
# 9. Economy
# ---------------------------------------------------------------------------

def _resolve_town_shop_items(game_data: GameData, region: str) -> list[str]:
    """Resolve shop items from the town matching *region*.

    For simulation purposes we assume all zones are cleared, so every
    shop tier is unlocked.  Returns an empty list when no town exists
    for the region.
    """
    for town in game_data.towns.values():
        if town.region == region:
            items: list[str] = []
            for tier in town.shop_tiers:
                items.extend(tier.items)
            return items
    return []


def economy_data(game_data: GameData) -> EconomyResult:
    from heresiarch.engine.formulas import MONEY_DROP_MIN_MULTIPLIER, MONEY_DROP_MAX_MULTIPLIER
    from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE

    money_avg = (MONEY_DROP_MIN_MULTIPLIER + MONEY_DROP_MAX_MULTIPLIER) / 2.0
    money_mults: dict[str, float] = {dt.enemy_template_id: dt.money_multiplier for dt in game_data.drop_tables.values()}

    zones: list[ZoneEconomySnapshot] = []
    cum_rush = cum_mod = cum_grind = 0.0

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

        overstay_max_gold = 0.0
        for b in range(1, 100):
            mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
            if mult <= 0:
                break
            overstay_max_gold += avg_enc_gold * mult

        def _overstay_gold(n: int) -> float:
            total = 0.0
            for b in range(1, n + 1):
                m = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                total += avg_enc_gold * m
            return total

        cum_rush += zone_gold
        cum_mod += zone_gold + _overstay_gold(_OVERSTAY_MODERATE)
        cum_grind += zone_gold + _overstay_gold(_OVERSTAY_GRIND)

        zones.append(ZoneEconomySnapshot(
            zone_id=zone.id, zone_name=zone.name, zone_level=zlvl,
            enemies_total=zone_enemies, encounters_total=len(zone.encounters),
            zone_gold=round(zone_gold, 1), overstay_max_gold=round(overstay_max_gold, 1),
            avg_encounter_gold=round(avg_enc_gold, 1),
            cumulative_gold_rush=round(cum_rush, 1),
            cumulative_gold_moderate=round(cum_mod, 1),
            cumulative_gold_grind=round(cum_grind, 1),
            shop_items=_resolve_town_shop_items(game_data, zone.region),
        ))

    # Pilfer impact
    pilfer_flat = 0
    pilfer_per_level = 0.0
    pilfer_impacts: list[PilferImpact] = []
    pilfer = game_data.abilities.get("pilfer")
    if pilfer and pilfer.effects:
        eff = pilfer.effects[0]
        pilfer_flat = eff.gold_steal_flat
        pilfer_per_level = eff.gold_steal_per_level
        for snap in zones:
            p = pilfer_flat + int(pilfer_per_level * snap.zone_level)
            two = p * 2
            equiv = two / snap.avg_encounter_gold if snap.avg_encounter_gold > 0 else 0.0
            pilfer_impacts.append(PilferImpact(
                zone_id=snap.zone_id, zone_gold=snap.zone_gold,
                cumulative_gold=snap.cumulative_gold_rush,
                pilfer_per_hit=p, two_hits=two, encounter_equivalent=round(equiv, 2),
            ))

    return EconomyResult(
        zones=zones, pilfer_flat=pilfer_flat, pilfer_per_level=pilfer_per_level,
        pilfer_impacts=pilfer_impacts,
    )


# ---------------------------------------------------------------------------
# 10. XP curve
# ---------------------------------------------------------------------------

def xp_curve_data(game_data: GameData, job_id: str) -> XpCurveResult:
    from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE

    job = game_data.jobs[job_id]
    xp_rush = xp_mod = xp_grind = 0
    lv_rush = lv_mod = lv_grind = 1

    zones_out: list[ZoneXpSnapshot] = []

    for zone in sorted(game_data.zones.values(), key=lambda z: z.zone_level):
        zlvl = zone.zone_level
        xp_cap = zone.xp_cap_level

        def _zone_clear_xp(char_level: int) -> int:
            total = 0
            for enc in zone.encounters:
                for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                    tmpl = game_data.enemies.get(tmpl_id)
                    if tmpl is None:
                        continue
                    total += calculate_xp_reward(zlvl, tmpl.budget_multiplier, char_level, xp_cap) * cnt
            return total

        def _overstay_xp(n_battles: int, char_level: int) -> int:
            if not zone.encounters:
                return 0
            non_boss = [e for e in zone.encounters if not e.is_boss] or zone.encounters
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

        xp_rush += _zone_clear_xp(lv_rush)
        lv_rush += calculate_levels_gained(xp_rush, lv_rush)

        xp_mod += _zone_clear_xp(lv_mod) + _overstay_xp(_OVERSTAY_MODERATE, lv_mod)
        lv_mod += calculate_levels_gained(xp_mod, lv_mod)

        xp_grind += _zone_clear_xp(lv_grind) + _overstay_xp(_OVERSTAY_GRIND, lv_grind)
        lv_grind += calculate_levels_gained(xp_grind, lv_grind)

        zones_out.append(ZoneXpSnapshot(
            zone_id=zone.id, zone_level=zlvl,
            level_at_exit_rush=lv_rush, level_at_exit_moderate=lv_mod, level_at_exit_grind=lv_grind,
            cumulative_xp_rush=xp_rush, cumulative_xp_moderate=xp_mod, cumulative_xp_grind=xp_grind,
        ))

    # Milestones
    milestones: list[XpMilestone] = []
    for target_lv in [5, 10, 15, 20, 25, 30]:
        rush_z = mod_z = grind_z = "---"
        for snap in zones_out:
            if rush_z == "---" and snap.level_at_exit_rush >= target_lv:
                rush_z = snap.zone_id
            if mod_z == "---" and snap.level_at_exit_moderate >= target_lv:
                mod_z = snap.zone_id
            if grind_z == "---" and snap.level_at_exit_grind >= target_lv:
                grind_z = snap.zone_id
        milestones.append(XpMilestone(
            target_level=target_lv, rush_zone=rush_z, moderate_zone=mod_z, grind_zone=grind_z,
        ))

    return XpCurveResult(job_id=job_id, job_name=job.name, zones=zones_out, milestones=milestones)


# ---------------------------------------------------------------------------
# 11. Enemy stats
# ---------------------------------------------------------------------------

def enemy_stats_data(game_data: GameData, enemy_ids: list[str] | None = None) -> EnemyStatsResult:
    if enemy_ids is None:
        enemy_ids = list(game_data.enemies.keys())

    zone_levels = sorted({z.zone_level for z in game_data.zones.values()})
    if not zone_levels:
        zone_levels = list(range(1, 100, 5))

    entries: list[EnemyStatsEntry] = []
    for eid in enemy_ids:
        if eid not in game_data.enemies:
            continue
        tmpl = game_data.enemies[eid]
        equip_items = [game_data.items[iid] for iid in tmpl.equipment if iid in game_data.items]

        zone_stats: list[EnemyZoneStats] = []
        for zlvl in zone_levels:
            base_stats = calculate_enemy_stats(zlvl, tmpl.budget_multiplier, tmpl.stat_distribution)
            hp = calculate_enemy_hp(zlvl, tmpl.budget_multiplier, tmpl.base_hp, tmpl.hp_per_budget)

            eff_stats = None
            if equip_items:
                eff = calculate_effective_stats(base_stats, equip_items, [])
                eff_stats = eff.model_dump()

            zone_stats.append(EnemyZoneStats(
                zone_level=zlvl, hp=hp, base_stats=base_stats.model_dump(),
                effective_stats=eff_stats,
            ))

        entries.append(EnemyStatsEntry(
            enemy_id=eid, enemy_name=tmpl.name, archetype=tmpl.archetype.value,
            budget_multiplier=tmpl.budget_multiplier,
            stat_distribution=tmpl.stat_distribution,
            equipment=tmpl.equipment, zone_stats=zone_stats,
        ))

    return EnemyStatsResult(enemies=entries)


# ---------------------------------------------------------------------------
# 12. Shop pricing
# ---------------------------------------------------------------------------

def shop_pricing_data(game_data: GameData, potions_only: bool = False) -> ShopPricingResult:
    econ = economy_data(game_data)
    zones_out: list[ShopZone] = []

    if not potions_only:
        for snap in econ.zones:
            if not snap.shop_items:
                continue
            items: list[ShopItem] = []
            for item_id in snap.shop_items:
                item = game_data.items.get(item_id)
                if item is None or item.base_price <= 0:
                    continue
                price = calculate_buy_price(item.base_price, cha=0)
                pct_r = (price / snap.cumulative_gold_rush * 100) if snap.cumulative_gold_rush > 0 else None
                pct_m = (price / snap.cumulative_gold_moderate * 100) if snap.cumulative_gold_moderate > 0 else None
                pct_g = (price / snap.cumulative_gold_grind * 100) if snap.cumulative_gold_grind > 0 else None

                if pct_r is not None and pct_r <= 100:
                    afford = "YES (rush)"
                elif pct_m is not None and pct_m <= 100:
                    afford = "YES (mod)"
                elif pct_g is not None and pct_g <= 100:
                    afford = "YES (grind)"
                else:
                    afford = "NO"

                items.append(ShopItem(
                    item_name=item.name, item_id=item.id,
                    base_price=item.base_price, buy_price=price,
                    pct_rush=round(pct_r, 1) if pct_r is not None else None,
                    pct_moderate=round(pct_m, 1) if pct_m is not None else None,
                    pct_grind=round(pct_g, 1) if pct_g is not None else None,
                    affordable=afford,
                ))
            zones_out.append(ShopZone(
                zone_name=snap.zone_name, zone_level=snap.zone_level,
                cumulative_gold_rush=snap.cumulative_gold_rush,
                cumulative_gold_moderate=snap.cumulative_gold_moderate,
                cumulative_gold_grind=snap.cumulative_gold_grind,
                items=items,
            ))

    # Potion check
    potion_ids: set[str] = set()
    for item in game_data.items.values():
        if item.base_price > 0 and any(kw in item.id.lower() for kw in ("potion", "elixir")):
            potion_ids.add(item.id)

    potion_intro: dict[str, ZoneEconomySnapshot] = {}
    for snap in econ.zones:
        for pid in potion_ids:
            if pid in snap.shop_items and pid not in potion_intro:
                potion_intro[pid] = snap

    potions: list[PotionCheck] = []
    for pid in sorted(potion_ids):
        item = game_data.items[pid]
        buy_price = calculate_buy_price(item.base_price, cha=0)
        snap = potion_intro.get(pid)
        if snap is None:
            potions.append(PotionCheck(
                potion_name=item.name, potion_id=pid,
                base_price=item.base_price, buy_price=buy_price, status="NOT IN SHOP",
            ))
            continue
        avg_gold = snap.avg_encounter_gold
        ratio = buy_price / avg_gold if avg_gold > 0 else 0.0
        if abs(ratio - 1.5) <= 0.5:
            status = "OK"
        elif ratio < 1.0:
            status = "CHEAP"
        else:
            status = "EXPENSIVE"
        potions.append(PotionCheck(
            potion_name=item.name, potion_id=pid,
            base_price=item.base_price, buy_price=buy_price,
            intro_zone=f"{snap.zone_name} (Lv{snap.zone_level})",
            avg_encounter_gold=round(avg_gold, 1),
            ratio=round(ratio, 2), status=status,
        ))

    return ShopPricingResult(zones=zones_out, potions=potions)


# ---------------------------------------------------------------------------
# 13. Progression
# ---------------------------------------------------------------------------

def progression_data(game_data: GameData, job_id: str) -> ProgressionResult:
    job = game_data.jobs[job_id]
    econ = economy_data(game_data)
    xp = xp_curve_data(game_data, job_id)

    # Ability unlock map
    unlock_map: dict[int, list[str]] = {}
    innate = game_data.abilities.get(job.innate_ability_id)
    if innate:
        unlock_map.setdefault(1, []).append(innate.name)
    for unlock in job.ability_unlocks:
        ability = game_data.abilities.get(unlock.ability_id)
        if ability:
            unlock_map.setdefault(unlock.level, []).append(ability.name)

    # Primary stat + weapons
    primary_stat = max([StatType.STR, StatType.MAG], key=lambda s: job.growth.effective_growth(s))
    growth_rate = job.growth.effective_growth(primary_stat)
    weapons: dict[str, ItemScaling] = {}
    for item in game_data.items.values():
        if item.scaling and item.scaling.stat == primary_stat:
            weapons[item.name] = item.scaling

    xp_by_zone = {s.zone_id: s for s in xp.zones}
    zones_out: list[ProgressionZone] = []

    for snap in econ.zones:
        xp_snap = xp_by_zone.get(snap.zone_id)
        if xp_snap is None:
            continue

        exit_lv = xp_snap.level_at_exit_moderate

        # Affordable items
        affordable: list[str] = []
        for item_id in snap.shop_items:
            item = game_data.items.get(item_id)
            if item is None or item.base_price <= 0:
                continue
            buy = calculate_buy_price(item.base_price, cha=0)
            if buy <= snap.cumulative_gold_moderate:
                affordable.append(item.name)

        # Unlocked abilities
        unlocked: list[str] = []
        for lv, names in sorted(unlock_map.items()):
            if lv <= exit_lv:
                for n in names:
                    unlocked.append(f"{n} (Lv{lv})")

        # Best weapon
        best_weapon = None
        weapon_outputs: dict[str, float] = {}
        if weapons:
            stat_val = growth_rate * exit_lv
            for wname, wscaling in weapons.items():
                weapon_outputs[wname] = round(evaluate_item_scaling(wscaling, stat_val), 1)
            best_weapon = max(weapon_outputs, key=lambda n: weapon_outputs[n])

        zones_out.append(ProgressionZone(
            zone_id=snap.zone_id, zone_name=snap.zone_name, zone_level=snap.zone_level,
            exit_level_rush=xp_snap.level_at_exit_rush,
            exit_level_moderate=xp_snap.level_at_exit_moderate,
            exit_level_grind=xp_snap.level_at_exit_grind,
            cumulative_gold_rush=snap.cumulative_gold_rush,
            cumulative_gold_moderate=snap.cumulative_gold_moderate,
            cumulative_gold_grind=snap.cumulative_gold_grind,
            affordable_items=affordable, unlocked_abilities=unlocked,
            best_weapon=best_weapon, weapon_outputs=weapon_outputs,
        ))

    return ProgressionResult(
        job_id=job_id, job_name=job.name,
        primary_stat=primary_stat.value, growth_rate=growth_rate,
        zones=zones_out,
    )
