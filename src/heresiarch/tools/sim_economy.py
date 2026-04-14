"""Economy and progression analysis: zone economy, XP curves, shop pricing, lodge tuning.

Extracted from sim.py. Functions focused on progression, economy, and zone analysis.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import (
    calculate_buy_price,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_levels_gained,
    calculate_max_hp,
    calculate_stats_at_level,
    calculate_xp_reward,
    evaluate_item_scaling,
    xp_for_level,
)
from heresiarch.engine.models.items import ItemScaling
from heresiarch.engine.models.stats import StatType
from heresiarch.tools.sim import _fmt_table, _load_game_data

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.enemies import EnemyTemplate
    from heresiarch.engine.models.zone import ZoneTemplate


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

def _effective_xp_mult(tmpl: "EnemyTemplate") -> float:
    """Return the XP multiplier for an enemy: xp_multiplier if set, else budget_multiplier."""
    if tmpl.xp_multiplier is not None and tmpl.xp_multiplier > 0:
        return tmpl.xp_multiplier
    return tmpl.budget_multiplier

def _resolve_encounter_enemy_level(
    zone: "ZoneTemplate",
    enc: "EncounterTemplate",
    encounter_index: int | None = None,
    total_encounters: int | None = None,
) -> int:
    """Resolve the enemy level for an encounter, matching encounter.py priority.

    1. Boss enemy_level_override
    2. Per-encounter enemy_level_range (average)
    3. Auto-interpolation from zone range based on encounter position
    4. Flat zone enemy_level_range (average)
    5. zone_level fallback
    """
    # 1. Boss override
    if enc.enemy_level_override is not None:
        return enc.enemy_level_override

    # 2. Per-encounter range
    if enc.enemy_level_range is not None:
        enc_min, enc_max = enc.enemy_level_range
        if enc_min > 0 and enc_max >= enc_min:
            return (enc_min + enc_max) // 2

    # 3-4. Zone range (interpolated if position known, flat otherwise)
    zone_min, zone_max = zone.enemy_level_range
    if zone_min > 0 and zone_max >= zone_min:
        if (
            encounter_index is not None
            and total_encounters is not None
            and total_encounters > 1
        ):
            t = encounter_index / (total_encounters - 1)
            center = zone_min + t * (zone_max - zone_min)
            interp_min = max(zone_min, round(center - 1))
            interp_max = min(zone_max, round(center + 1))
            return (interp_min + interp_max) // 2
        return (zone_min + zone_max) // 2

    # 5. zone_level fallback
    return zone.zone_level

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

def _compute_zone_economy(game_data: GameData) -> list[ZoneEconSnapshot]:
    """Build per-zone gold snapshots using avg money-drop formula.

    Uses per-enemy levels (enemy_level_range average or boss override)
    instead of flat zone_level. Returns zones sorted by zone_level ascending.
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
        zone_gold = 0.0
        zone_enemies = 0
        non_boss_golds: list[float] = []

        total_enc = len(zone.encounters)
        for enc_idx, enc in enumerate(zone.encounters):
            enemy_level = _resolve_encounter_enemy_level(zone, enc, enc_idx, total_enc)
            enc_gold = 0.0
            enc_enemies = 0
            for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                mult = money_mults.get(tmpl_id, 1.0)
                enc_gold += enemy_level * money_avg * mult * cnt
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
        def _overstay_gold(n_battles: int, _avg=avg_enc_gold) -> float:
            total = 0.0
            for b in range(1, n_battles + 1):
                mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                total += _avg * mult
            return total

        cumulative_rush += zone_gold
        cumulative_moderate += zone_gold + _overstay_gold(_OVERSTAY_MODERATE)
        cumulative_grind += zone_gold + _overstay_gold(_OVERSTAY_GRIND)

        snapshots.append(ZoneEconSnapshot(
            zone_id=zone.id,
            zone_name=zone.name,
            zone_level=zone.zone_level,
            enemies_total=zone_enemies,
            encounters_total=len(zone.encounters),
            zone_gold=zone_gold,
            overstay_max_gold=overstay_max_gold,
            cumulative_gold_rush=cumulative_rush,
            cumulative_gold_moderate=cumulative_moderate,
            cumulative_gold_grind=cumulative_grind,
            avg_encounter_gold=avg_enc_gold,
            shop_items=_resolve_town_shop_items(game_data, zone.region),
        ))

    return snapshots

def _compute_xp_progression(game_data: GameData, job_id: str) -> list[ZoneXPSnapshot]:
    """Simulate XP/level at each zone exit under rush/moderate/grind scenarios.

    Assumes a single character of the given job, starting at level 1 with 0 XP,
    clearing zones in order.  Rush = clear only; moderate = +5 overstay battles;
    grind = +20 overstay battles per zone.

    Uses per-enemy levels (enemy_level_range average or boss override) instead
    of flat zone_level.  Endless zones model dynamic encounters with reward tapering.
    """
    from heresiarch.engine.formulas import calculate_endless_reward_multiplier
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
        xp_cap = zone.xp_cap_level

        # --- Endless zones: model dynamic encounters with reward tapering ---
        if zone.is_endless:
            def _endless_xp(n_battles: int, char_level: int) -> int:
                """Estimate XP from N endless encounters at current player level."""
                # Average XP multiplier from pool
                total_budget = 0.0
                pool_count = 0
                for tid in zone.endless_enemy_pool:
                    tmpl = game_data.enemies.get(tid)
                    if tmpl:
                        total_budget += _effective_xp_mult(tmpl)
                        pool_count += 1
                avg_budget = total_budget / pool_count if pool_count > 0 else 1.0
                avg_enemies_per_enc = 3.0  # (2+4)/2

                total_xp = 0
                lvl = char_level
                for _b in range(n_battles):
                    # Enemy level rubber-bands to player, clamped
                    enemy_level = max(zone.endless_min_level, min(lvl, zone.endless_max_level))
                    base_xp = calculate_xp_reward(enemy_level, avg_budget, lvl, xp_cap)
                    endless_mult = calculate_endless_reward_multiplier(lvl, zone.endless_max_level)
                    enc_xp = int(base_xp * avg_enemies_per_enc * endless_mult)
                    total_xp += enc_xp
                    # Re-check level after each encounter (level-ups reduce future XP)
                    gained = calculate_levels_gained(total_xp + xp_rush, lvl)
                    lvl = char_level + gained
                return total_xp

            # Rush: skip endless entirely
            # Moderate: 10 battles in pit
            xp_moderate += _endless_xp(10, level_moderate)
            gained = calculate_levels_gained(xp_moderate, level_moderate)
            level_moderate += gained

            # Grind: 40 battles in pit
            xp_grind += _endless_xp(_ENDLESS_GRIND_BATTLES, level_grind)
            gained = calculate_levels_gained(xp_grind, level_grind)
            level_grind += gained

            snapshots.append(ZoneXPSnapshot(
                zone_id=zone.id,
                zone_level=zone.zone_level,
                level_at_exit_rush=level_rush,
                level_at_exit_moderate=level_moderate,
                level_at_exit_grind=level_grind,
                cumulative_xp_rush=xp_rush,
                cumulative_xp_moderate=xp_moderate,
                cumulative_xp_grind=xp_grind,
            ))
            continue

        # --- Regular zones ---
        def _zone_clear_xp(char_level: int, _zone=zone) -> int:
            total = 0
            total_enc = len(_zone.encounters)
            for enc_idx, enc in enumerate(_zone.encounters):
                enemy_level = _resolve_encounter_enemy_level(_zone, enc, enc_idx, total_enc)
                for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                    tmpl = game_data.enemies.get(tmpl_id)
                    if tmpl is None:
                        continue
                    xp_per_kill = calculate_xp_reward(
                        enemy_level, _effective_xp_mult(tmpl), char_level, xp_cap,
                    )
                    total += xp_per_kill * cnt
            return total

        def _overstay_xp(n_battles: int, char_level: int, _zone=zone) -> int:
            if not _zone.encounters:
                return 0
            non_boss = [e for e in _zone.encounters if not e.is_boss]
            if not non_boss:
                non_boss = _zone.encounters
            # Average enemy level for overstay (non-boss encounters)
            avg_enemy_level = _resolve_encounter_enemy_level(_zone, non_boss[0])
            total_budget = 0.0
            total_enemies = 0
            for enc in non_boss:
                for tmpl_id, cnt in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
                    tmpl = game_data.enemies.get(tmpl_id)
                    if tmpl is not None:
                        total_budget += _effective_xp_mult(tmpl) * cnt
                        total_enemies += cnt
            avg_budget = total_budget / total_enemies if total_enemies > 0 else 1.0
            avg_count = sum(sum(e.enemy_counts) for e in non_boss) / len(non_boss) if non_boss else 1

            total_xp = 0
            for b in range(1, n_battles + 1):
                overstay_mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * b)
                base_xp = calculate_xp_reward(avg_enemy_level, avg_budget, char_level, xp_cap)
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
            zone_level=zone.zone_level,
            level_at_exit_rush=level_rush,
            level_at_exit_moderate=level_moderate,
            level_at_exit_grind=level_grind,
            cumulative_xp_rush=xp_rush,
            cumulative_xp_moderate=xp_moderate,
            cumulative_xp_grind=xp_grind,
        ))

    return snapshots

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

    # --- Endless zone analysis ---
    endless_zones = [z for z in gd.zones.values() if z.is_endless]
    if endless_zones:
        from heresiarch.engine.formulas import (
            MONEY_DROP_MAX_MULTIPLIER,
            MONEY_DROP_MIN_MULTIPLIER,
            calculate_endless_reward_multiplier,
        )

        money_avg = (MONEY_DROP_MIN_MULTIPLIER + MONEY_DROP_MAX_MULTIPLIER) / 2.0

        for zone in endless_zones:
            # Average XP and gold per enemy in the pool
            pool_xp_mults: list[float] = []
            pool_gold_budgets: list[float] = []
            for tid in zone.endless_enemy_pool:
                tmpl = gd.enemies.get(tid)
                if tmpl:
                    pool_xp_mults.append(_effective_xp_mult(tmpl))
                    pool_gold_budgets.append(tmpl.budget_multiplier)
            avg_xp_mult = sum(pool_xp_mults) / len(pool_xp_mults) if pool_xp_mults else 1.0
            avg_gold_budget = sum(pool_gold_budgets) / len(pool_gold_budgets) if pool_gold_budgets else 1.0
            avg_enemies = 3.0  # (2+4)/2

            print(f"\n{'=' * 90}")
            print(f"ENDLESS ZONE: {zone.name} (Lv{zone.endless_min_level}-{zone.endless_max_level})")
            print(f"  Pool: {len(zone.endless_enemy_pool)} templates, avg xp_mult={avg_xp_mult:.1f}, avg gold_budget={avg_gold_budget:.1f}")
            print(f"  Avg ~{avg_enemies:.0f} enemies/enc, XP cap at Lv{zone.xp_cap_level}")
            print(f"{'=' * 90}")

            print(f"\n  {'Entry Lv':>8} | {'Enc XP':>7} | {'Enc Gold':>8} | {'Reward%':>7} | {'XP→Lv+1':>8} | {'Enc to Lv+1':>11} | {'10 Enc →Lv':>10} | {'30 Enc →Lv':>10}")
            print(f"  {'-'*8}-+-{'-'*7}-+-{'-'*8}-+-{'-'*7}-+-{'-'*8}-+-{'-'*11}-+-{'-'*10}-+-{'-'*10}")

            for entry_lv in range(zone.endless_min_level, zone.endless_max_level + 3):
                enemy_level = max(zone.endless_min_level, min(entry_lv, zone.endless_max_level))
                reward_mult = calculate_endless_reward_multiplier(entry_lv, zone.endless_max_level)

                enc_xp_raw = int(enemy_level * avg_xp_mult * avg_enemies)
                enc_xp = int(enc_xp_raw * reward_mult)
                # Apply XP cap penalty if over cap
                if zone.xp_cap_level > 0 and entry_lv > zone.xp_cap_level:
                    levels_over = entry_lv - zone.xp_cap_level
                    cap_ratio = max(0.1, 0.5 ** levels_over)
                    enc_xp = int(enc_xp * cap_ratio)

                enc_gold_raw = int(enemy_level * money_avg * avg_enemies)
                enc_gold = int(enc_gold_raw * reward_mult)

                # XP needed for next level
                xp_next = xp_for_level(entry_lv + 1) - xp_for_level(entry_lv)
                enc_to_next = xp_next / enc_xp if enc_xp > 0 else float('inf')

                # Simulate 10 and 30 encounters (level changes mid-grind)
                def _sim_encounters(n: int, start_lv: int) -> int:
                    lv = start_lv
                    total_xp = xp_for_level(start_lv)
                    for _ in range(n):
                        elv = max(zone.endless_min_level, min(lv, zone.endless_max_level))
                        rm = calculate_endless_reward_multiplier(lv, zone.endless_max_level)
                        raw = int(elv * avg_xp_mult * avg_enemies * rm)
                        if zone.xp_cap_level > 0 and lv > zone.xp_cap_level:
                            lo = lv - zone.xp_cap_level
                            raw = int(raw * max(0.1, 0.5 ** lo))
                        total_xp += raw
                        gained = calculate_levels_gained(total_xp, lv)
                        lv += gained
                    return lv

                lv_10 = _sim_encounters(10, entry_lv)
                lv_30 = _sim_encounters(30, entry_lv)

                print(f"  Lv{entry_lv:>5} | {enc_xp:>5}xp | {enc_gold:>6}G | {reward_mult:>5.0%} | {xp_next:>6}xp | {enc_to_next:>9.1f} | Lv{lv_10:>7} | Lv{lv_30:>7}")

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

def cmd_lodge_tuning(args: argparse.Namespace) -> None:
    """Lodge cost analysis with dynamic HP-based pricing model.

    Models: cost = floor + (missing_hp_total * gold_per_hp)
    where floor = base + per_level * mc_level.

    Simulates across multiple gold_per_hp values and injury levels
    to find the sweet spot.
    """
    gd = _load_game_data()
    job_id = args.job

    if job_id not in gd.jobs:
        print(f"Error: job '{job_id}' not found. Available: {', '.join(gd.jobs.keys())}")
        return

    job = gd.jobs[job_id]

    econ_snaps = _compute_zone_economy(gd)
    xp_snaps = _compute_xp_progression(gd, job_id)
    xp_by_zone = {s.zone_id: s for s in xp_snaps}

    # Potion data (for comparison)
    best_potion: tuple[str, int, int] = ("---", 1, 1)
    for item in gd.items.values():
        if item.is_consumable and item.heal_amount > 0:
            buy = calculate_buy_price(item.base_price, cha=0)
            if item.heal_amount > best_potion[1]:
                best_potion = (item.name, item.heal_amount, buy)
    potion_gph = best_potion[2] / best_potion[1]  # gold per HP for best potion

    # MC max HP at level (solo — party of 1 for simplicity, scale by party_size)
    def _mc_max_hp(level: int) -> int:
        effective_def = (job.growth.DEF + 1) * level
        return calculate_max_hp(job.base_hp, job.hp_growth, level, effective_def)

    # Estimate Pit avg encounter gold
    from heresiarch.engine.formulas import MONEY_DROP_MIN_MULTIPLIER, MONEY_DROP_MAX_MULTIPLIER
    money_avg = (MONEY_DROP_MIN_MULTIPLIER + MONEY_DROP_MAX_MULTIPLIER) / 2.0
    money_mults: dict[str, float] = {}
    for dt in gd.drop_tables.values():
        money_mults[dt.enemy_template_id] = dt.money_multiplier

    pit_avg_gold = 0.0
    for zone in gd.zones.values():
        if zone.is_endless and zone.endless_enemy_pool:
            avg_level = (zone.endless_min_level + zone.endless_max_level) / 2.0
            pool_mults = [money_mults.get(eid, 1.0) for eid in zone.endless_enemy_pool]
            avg_mult = sum(pool_mults) / len(pool_mults) if pool_mults else 1.0
            pit_avg_gold = avg_level * money_avg * avg_mult * 3.0
            break

    # --- Parameters to sweep ---
    gold_per_hp_values = [0.5, 1.0, 1.5, 2.0, 3.0]
    injury_levels = [0.25, 0.50, 0.75, 1.00]  # % HP missing
    floor_base = 50   # minimum cost floor base
    floor_per_lv = 5  # minimum cost floor per level

    party_size = int(args.party_size) if hasattr(args, "party_size") else 1

    print("=" * 120)
    print(f"LODGE COST TUNING — Dynamic HP-based pricing")
    print(f"  Job: {job.name}  |  Party size: {party_size}")
    print(f"  Formula: max(floor, missing_hp_total * gold_per_hp)")
    print(f"  Floor: {floor_base} + {floor_per_lv} * mc_level")
    print(f"  Best potion: {best_potion[0]} ({best_potion[1]}HP, {best_potion[2]}G) = {potion_gph:.2f} G/HP")
    if pit_avg_gold > 0:
        print(f"  Pit avg encounter gold: {pit_avg_gold:.0f}G")
    print(f"  Gold_per_hp values tested: {gold_per_hp_values}")
    print(f"  Injury levels tested: {[f'{i:.0%}' for i in injury_levels]}")
    print("=" * 120)

    # For each gold_per_hp value, show the full table
    for gph in gold_per_hp_values:
        print(f"\n{'─' * 120}")
        print(f"  gold_per_hp = {gph}  (potion = {potion_gph:.2f} G/HP, premium = {gph/potion_gph:.1f}x)")
        print(f"{'─' * 120}")

        rows: list[list[str]] = []
        for econ in econ_snaps:
            xp = xp_by_zone.get(econ.zone_id)
            if xp is None:
                continue

            level = xp.level_at_exit_moderate
            gold = econ.cumulative_gold_moderate
            mc_hp = _mc_max_hp(level)
            total_max_hp = mc_hp * party_size
            floor = floor_base + floor_per_lv * level

            cells: list[str] = [
                econ.zone_id,
                str(level),
                str(total_max_hp),
                f"{gold:.0f}G",
            ]

            for injury in injury_levels:
                missing = int(total_max_hp * injury)
                cost = max(floor, int(missing * gph))
                pct = (cost / gold * 100) if gold > 0 else 999.0
                pit_enc = cost / pit_avg_gold if pit_avg_gold > 0 else 0
                cells.append(f"{cost}G ({pct:.0f}%) [{pit_enc:.1f}p]")

            rows.append(cells)

        headers = ["Zone", "Lv", "PartyHP", "Gold"] + [
            f"{int(inj*100)}% hurt" for inj in injury_levels
        ]
        print(_fmt_table(
            headers, rows,
            col_align=["l", "r", "r", "r"] + ["r"] * len(injury_levels),
        ))

    # Summary: which gold_per_hp gives 20-40% at 75% injury across the run?
    print(f"\n{'=' * 120}")
    print("SUMMARY: %gold at 75% injury (target: 20-40% = 'painful')")
    print(f"{'=' * 120}\n")

    summary_headers = ["Zone", "Lv", "Gold"] + [f"gph={g}" for g in gold_per_hp_values]
    summary_rows: list[list[str]] = []

    for econ in econ_snaps:
        xp = xp_by_zone.get(econ.zone_id)
        if xp is None:
            continue
        level = xp.level_at_exit_moderate
        gold = econ.cumulative_gold_moderate
        mc_hp = _mc_max_hp(level)
        total_max_hp = mc_hp * party_size
        missing_75 = int(total_max_hp * 0.75)
        floor = floor_base + floor_per_lv * level

        cells = [econ.zone_id, str(level), f"{gold:.0f}G"]
        for gph in gold_per_hp_values:
            cost = max(floor, int(missing_75 * gph))
            pct = (cost / gold * 100) if gold > 0 else 999.0
            verdict = (
                "FREE" if pct < 5
                else "cheap" if pct < 15
                else "fair" if pct < 30
                else "painful" if pct < 50
                else "brutal" if pct < 75
                else "NOPE"
            )
            cells.append(f"{pct:>5.1f}% {verdict}")
        summary_rows.append(cells)

    print(_fmt_table(
        summary_headers, summary_rows,
        col_align=["l", "r", "r"] + ["r"] * len(gold_per_hp_values),
    ))

    print()
    print("TUNING GUIDANCE:")
    print("  Target: 20-40% at 75% injury = 'painful but possible'")
    print("  Lodge should cost MORE per HP than potions (convenience premium)")
    print(f"  Potion baseline: {potion_gph:.2f} G/HP — lodge gold_per_hp should be >{potion_gph:.1f}")
    print("  Pit earn-back at 75% injury should be 3-5 encounters")
    print("  Early zones (1-2) being 'brutal' is OK — you shouldn't rest early")

