"""State summarizer: compact, decision-relevant text views of game state.

Pure functions. No side effects. Takes engine state, returns strings.
All output is plain text (no Rich markup) optimized for LLM token budgets.
"""

from __future__ import annotations

import re
from collections import Counter

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    calculate_speed_bonus,
    calculate_buy_price,
    calculate_sell_price,
    evaluate_item_scaling,
    xp_for_level,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    DamageQuality,
    TargetType,
    TriggerCondition,
)
from heresiarch.engine.models.combat_state import (
    CombatEvent,
    CombatEventType,
    CombatState,
    CombatantState,
)
from heresiarch.engine.models.items import Item, ScalingType
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.stats import StatType
from heresiarch.engine.models.zone import ZoneTemplate
from heresiarch.engine.recruitment import InspectionLevel, RecruitCandidate
from heresiarch.engine.shop import ShopInventory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RICH_TAG_RE = re.compile(r"\[/?[^\]]*\]")


def _strip_rich(text: str) -> str:
    """Remove Rich markup tags from text."""
    return _RICH_TAG_RE.sub("", text)


def _pct(current: int, maximum: int) -> str:
    if maximum <= 0:
        return "0%"
    return f"{current * 100 // maximum}%"


def _stat_line(char: CharacterInstance) -> str:
    s = char.effective_stats
    return f"STR:{s.STR} MAG:{s.MAG} DEF:{s.DEF} RES:{s.RES} SPD:{s.SPD}"


def _base_stat_line(char: CharacterInstance) -> str:
    s = char.base_stats
    return f"STR:{s.STR} MAG:{s.MAG} DEF:{s.DEF} RES:{s.RES} SPD:{s.SPD}"


def _item_scaling_desc(item: Item) -> str:
    """Short scaling description like 'STR LINEAR (20 + 1.0xSTR)'."""
    if not item.scaling:
        return "no scaling"
    s = item.scaling
    st = s.scaling_type.value
    stat = s.stat.value
    match s.scaling_type:
        case ScalingType.LINEAR:
            return f"{stat} {st} ({s.base:.0f} + {s.linear_coeff}x{stat})"
        case ScalingType.SUPERLINEAR:
            return f"{stat} {st} ({s.base:.0f} + {s.linear_coeff}x{stat} + {s.quadratic_coeff}x{stat}^2)"
        case ScalingType.QUADRATIC:
            return f"{stat} {st} ({s.base:.0f} + {s.quadratic_coeff}x{stat}^2)"
        case ScalingType.DEGENERATE:
            return f"{stat} {st} ({s.constant_offset:.1f} + {s.quadratic_coeff}x{stat}^2)"
        case ScalingType.FLAT:
            return f"FLAT ({s.base:.0f})"
        case _:
            return st


def _item_bonus_at_stat(item: Item, stat_value: int) -> str:
    """Calculate and show current bonus from item scaling."""
    if not item.scaling:
        return ""
    bonus = evaluate_item_scaling(item.scaling, stat_value)
    kind = "phys" if item.scaling.stat == StatType.STR else "mag" if item.scaling.stat == StatType.MAG else "def" if item.scaling.stat == StatType.DEF else "res"
    return f"+{bonus:.0f} {kind}"


def _ability_status(ability_id: str, combatant: CombatantState, game_data: GameData) -> str:
    """Ability availability string for combat view."""
    ability = game_data.abilities.get(ability_id)
    if ability is None:
        return ability_id

    name = ability_id
    if ability.trigger != TriggerCondition.NONE:
        return f"{name} [passive]"
    cd = combatant.cooldowns.get(ability_id, 0)
    if cd > 0:
        return f"{name} (cd:{cd})"
    return f"{name} ready"


def _xp_progress(char: CharacterInstance) -> str:
    """XP progress string like 'XP: 280/360 (78% to Lv7)'."""
    next_level = char.level + 1
    xp_needed = xp_for_level(next_level)
    if xp_needed <= 0:
        return "XP: MAX"
    pct = min(99, char.xp * 100 // xp_needed) if xp_needed > 0 else 100
    return f"XP: {char.xp}/{xp_needed} ({pct}% to Lv{next_level})"


def _stash_summary(run: RunState, game_data: GameData) -> str:
    """Compact stash listing."""
    if not run.party.stash:
        return "STASH (0/10): empty"

    counts: Counter[str] = Counter(run.party.stash)
    parts: list[str] = []
    for item_id, count in counts.items():
        item = game_data.items.get(item_id) or run.party.items.get(item_id)
        name = item.name if item else item_id
        if count > 1:
            parts.append(f"{name} x{count}")
        else:
            parts.append(name)

    return f"STASH ({len(run.party.stash)}/10): {', '.join(parts)}"


# ---------------------------------------------------------------------------
# Zone Selection View
# ---------------------------------------------------------------------------


def summarize_zone_select(
    run: RunState,
    available_zones: list[ZoneTemplate],
    game_data: GameData,
) -> str:
    """View for choosing which zone to enter. Shown after new_run, leave_zone."""
    lines: list[str] = []

    total_zones = len(game_data.zones)
    lines.append(
        f"=== {_mc_name(run)}'s Run | Zones Cleared: {len(run.zones_completed)}/{total_zones} | Gold: {run.party.money} ==="
    )
    lines.append("")

    # Party summary
    lines.append("PARTY:")
    for char_id in run.party.active:
        char = run.party.characters[char_id]
        role = "[active]"
        lines.append(
            f"  {role} {char.name} ({char_id}) [{_job_name(char.job_id, game_data)} Lv{char.level}] "
            f"{char.current_hp}/{char.max_hp} HP | {_stat_line(char)}"
        )
    for char_id in run.party.reserve:
        char = run.party.characters[char_id]
        lines.append(
            f"  [reserve] {char.name} ({char_id}) [{_job_name(char.job_id, game_data)} Lv{char.level}] "
            f"{char.current_hp}/{char.max_hp} HP"
        )
    lines.append("")

    lines.append(_stash_summary(run, game_data))
    lines.append("")

    # Available zones
    lines.append("AVAILABLE ZONES:")
    for zone in available_zones:
        cleared = zone.id in run.zones_completed
        marker = "done" if cleared else "NEW"

        saved = run.zone_progress.get(zone.id)
        if saved and not saved.is_cleared:
            enc_done = len(saved.encounters_completed)
            marker = f"IN PROGRESS ({enc_done}/{len(zone.encounters)})"

        line = f"  {'*' if not cleared else '-'} {zone.id} -- {zone.name} (Lv{zone.zone_level}) -- {marker} | XP cap: Lv{zone.xp_cap_level}"
        lines.append(line)

        if not cleared:
            details: list[str] = [f"{len(zone.encounters)} encounters"]
            if zone.recruitment_chance > 0:
                details.append(f"Recruit: {zone.recruitment_chance:.0%}")
            lines.append(f"      {' | '.join(details)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Combat View
# ---------------------------------------------------------------------------


def summarize_combat(
    combat: CombatState,
    run: RunState,
    game_data: GameData,
    last_round_events: list[CombatEvent] | None = None,
    enemy_templates: dict[str, str] | None = None,
) -> str:
    """View for making combat decisions. Shown during COMBAT phase."""
    lines: list[str] = []

    zone_name = ""
    encounter_str = ""
    if run.current_zone_id:
        zone = game_data.zones.get(run.current_zone_id)
        if zone:
            zone_name = f"{zone.name} (Lv{zone.zone_level})"
            if run.zone_state:
                total = len(zone.encounters)
                idx = run.zone_state.current_encounter_index + 1
                if run.zone_state.is_cleared:
                    encounter_str = f"Overstay #{run.zone_state.overstay_battles + 1}"
                else:
                    encounter_str = f"Encounter {idx}/{total}"

    lines.append(
        f"=== COMBAT Round {combat.round_number} | {zone_name} | {encounter_str} ==="
    )
    lines.append("")

    # Player party
    lines.append("YOUR PARTY:")
    for c in combat.player_combatants:
        if not c.is_alive:
            lines.append(f"  {c.id} -- DEAD")
            continue

        # Speed bonus: compare to slowest enemy
        slowest_enemy_spd = min(
            (e.effective_stats.SPD for e in combat.living_enemies),
            default=0,
        )
        speed_bonus = calculate_speed_bonus(c.effective_stats.SPD, slowest_enemy_spd)
        # Build passive state indicators
        passive_tags = []
        if c.insight_stacks > 0:
            passive_tags.append(f"I:{c.insight_stacks}")
        if c.frenzy_level > 1.0 or c.frenzy_chain > 0:
            passive_tags.append(f"F:{c.frenzy_level:.2f}x(chain:{c.frenzy_chain})")
        passive_str = f" | {' '.join(passive_tags)}" if passive_tags else ""
        lines.append(
            f"  {c.id} [{_job_name_from_combatant(c, run, game_data)} Lv{c.level}] "
            f"{c.current_hp}/{c.max_hp} HP ({_pct(c.current_hp, c.max_hp)}) | "
            f"AP: {c.action_points}{passive_str} | "
            f"STR:{c.effective_stats.STR} MAG:{c.effective_stats.MAG} "
            f"DEF:{c.effective_stats.DEF} RES:{c.effective_stats.RES} SPD:{c.effective_stats.SPD}"
        )
        # Abilities with cooldown status
        ability_parts = [_ability_status(aid, c, game_data) for aid in c.ability_ids]
        lines.append(f"    Abilities: {', '.join(ability_parts)}")

        # Equipment from RunState
        char = run.party.characters.get(c.id)
        if char:
            equip_parts: list[str] = []
            for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
                item_id = char.equipment.get(slot)
                if item_id:
                    equip_parts.append(f"{slot}: {item_id}")
            if equip_parts:
                lines.append(f"    Equipment: {', '.join(equip_parts)}")

        # Statuses
        if c.active_statuses:
            status_parts = [
                f"{s.name} ({s.rounds_remaining}t)" for s in c.active_statuses
            ]
            lines.append(f"    Statuses: {', '.join(status_parts)}")

        if speed_bonus > 0:
            lines.append(f"    Speed bonus: +{speed_bonus} action(s) (BA:{speed_bonus})")

    # Stash (consumables available mid-combat)
    if run.party.stash:
        counts: Counter[str] = Counter(run.party.stash)
        stash_parts: list[str] = []
        for item_id, count in counts.items():
            item = game_data.items.get(item_id) or run.party.items.get(item_id)
            name = item.name if item else item_id
            stash_parts.append(f"{name} x{count}" if count > 1 else name)
        lines.append(f"  STASH: {', '.join(stash_parts)}")

    lines.append("")

    # Enemies
    lines.append("ENEMIES:")
    for c in combat.enemy_combatants:
        if not c.is_alive:
            lines.append(f"  {c.id} -- DEAD")
            continue
        lines.append(
            f"  {c.id} {c.current_hp}/{c.max_hp} HP ({_pct(c.current_hp, c.max_hp)}) | "
            f"STR:{c.effective_stats.STR} MAG:{c.effective_stats.MAG} "
            f"DEF:{c.effective_stats.DEF} RES:{c.effective_stats.RES} SPD:{c.effective_stats.SPD}"
        )
        if c.active_statuses:
            status_parts = [
                f"{s.name} ({s.rounds_remaining}t)" for s in c.active_statuses
            ]
            lines.append(f"    Statuses: {', '.join(status_parts)}")

    lines.append("")

    # Turn order
    living_order = [
        cid for cid in combat.turn_order
        if any(
            (c.id == cid and c.is_alive)
            for c in combat.player_combatants + combat.enemy_combatants
        )
    ]
    lines.append(f"TURN ORDER: {' -> '.join(living_order)}")

    # Last round events
    if last_round_events:
        lines.append("")
        lines.append("LAST ROUND:")
        for event in last_round_events:
            rendered = _render_combat_event(event, combat, game_data)
            if rendered:
                lines.append(f"  {rendered}")
    elif combat.round_number == 0:
        # Initial encounter — describe enemies
        lines.append("")
        lines.append("NEW ENCOUNTER:")
        seen_templates: set[str] = set()
        for c in combat.enemy_combatants:
            tmpl_id = c.id.rsplit("_", 1)[0] if "_" in c.id else c.id
            if tmpl_id in seen_templates:
                continue
            seen_templates.add(tmpl_id)
            template = game_data.enemies.get(tmpl_id)
            if template:
                lines.append(
                    f"  {template.name} -- {template.archetype.value} archetype, "
                    f"abilities: {', '.join(template.abilities)}"
                )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post-Combat View
# ---------------------------------------------------------------------------


def summarize_post_combat(
    run: RunState,
    loot: LootResult,
    combat_result: CombatResult,
    game_data: GameData,
) -> str:
    """View after combat victory with loot choices."""
    lines: list[str] = []

    zone_name = ""
    encounter_str = ""
    if run.current_zone_id:
        zone = game_data.zones.get(run.current_zone_id)
        if zone:
            zone_name = zone.name
            if run.zone_state:
                total = len(zone.encounters)
                idx = run.zone_state.current_encounter_index
                if run.zone_state.is_cleared:
                    encounter_str = f"Overstay #{run.zone_state.overstay_battles}"
                else:
                    encounter_str = f"Encounter {idx}/{total}"

    lines.append(
        f"=== VICTORY in {combat_result.rounds_taken} rounds | {zone_name} {encounter_str} ==="
    )
    lines.append("")

    # Rewards
    lines.append("REWARDS:")
    lines.append(f"  Gold: +{loot.money} (total: {run.party.money})")
    if combat_result.gold_stolen_by_enemies > 0:
        lines.append(f"  Gold stolen by enemies: -{combat_result.gold_stolen_by_enemies}")
    if combat_result.gold_stolen_by_players > 0:
        lines.append(f"  Gold stolen from enemies: +{combat_result.gold_stolen_by_players}")
    lines.append("")

    # Loot drops
    if loot.item_ids:
        lines.append("LOOT DROPS:")
        for i, item_id in enumerate(loot.item_ids, 1):
            item = game_data.items.get(item_id)
            if item:
                desc = _short_item_desc(item)
                lines.append(f"  {i}. {item_id} -- {item.name} -- {desc}")
            else:
                lines.append(f"  {i}. {item_id}")
        lines.append("")
    else:
        lines.append("LOOT DROPS: none")
        lines.append("")

    # Stash
    stash_room = 10 - len(run.party.stash)
    lines.append(f"{_stash_summary(run, game_data)} -- room for {stash_room} more")
    lines.append("")

    # Party HP
    lines.append("PARTY HP after combat:")
    for char_id in run.party.active:
        char = run.party.characters[char_id]
        lines.append(
            f"  {char_id}: {char.current_hp}/{char.max_hp} ({_pct(char.current_hp, char.max_hp)})"
        )

    lines.append("")
    lines.append("-> Use pick_loot with item IDs to keep, or [] to take nothing.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Recruitment View
# ---------------------------------------------------------------------------


def summarize_recruitment(
    candidate: RecruitCandidate,
    inspection_level: InspectionLevel,
    party_cha: int,
    run: RunState,
    game_data: GameData,
) -> str:
    """View for recruitment decision."""
    lines: list[str] = []
    lines.append("=== RECRUITMENT CANDIDATE ===")
    lines.append("")
    lines.append(f"Inspection level: {inspection_level.value} (party CHA: {party_cha})")
    lines.append("")

    char = candidate.character
    job_name = _job_name(char.job_id, game_data)

    if inspection_level == InspectionLevel.MINIMAL:
        lines.append(f"{char.name} [{job_name}]")
        lines.append("  [Growth and stats hidden -- need CHA >=30 for growth, >=70 for full stats]")

    elif inspection_level == InspectionLevel.MODERATE:
        lines.append(f"{char.name} [{job_name}]")
        g = candidate.growth
        lines.append(
            f"  Growth: STR +{g.STR}, MAG +{g.MAG}, DEF +{g.DEF}, RES +{g.RES}, SPD +{g.SPD}"
        )
        lines.append("  [Full stats hidden -- need CHA >=70 for complete inspection]")

    else:  # FULL
        lines.append(f"{char.name} [{job_name} Lv{char.level}]")
        g = candidate.growth
        lines.append(
            f"  Growth: STR +{g.STR}, MAG +{g.MAG}, DEF +{g.DEF}, RES +{g.RES}, SPD +{g.SPD}"
        )
        lines.append(f"  Stats: {_stat_line(char)}")
        lines.append(f"  HP: {char.current_hp}/{char.max_hp}")
        # Equipment
        equip_parts: list[str] = []
        for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            item_id = char.equipment.get(slot)
            if item_id:
                item = game_data.items.get(item_id)
                equip_parts.append(f"{slot}: {item.name if item else item_id}")
        if equip_parts:
            lines.append(f"  Equipment: {', '.join(equip_parts)}")
        # Abilities
        abilities = [a for a in char.abilities if a != "basic_attack"]
        if abilities:
            lines.append(f"  Abilities: basic_attack, {', '.join(abilities)}")

    lines.append("")
    active_count = len(run.party.active)
    reserve_count = len(run.party.reserve)
    total = active_count + reserve_count
    lines.append(f"Your party: {active_count}/3 active, {reserve_count}/1 reserve ({total}/4 total)")
    if active_count < 3:
        lines.append("  -> Would join as: active member")
    elif total < 4:
        lines.append("  -> Would join as: reserve member")
    else:
        lines.append("  -> Party is FULL. Cannot recruit.")

    lines.append("")
    lines.append("-> Use recruit(true) to accept or recruit(false) to decline.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Party Status View
# ---------------------------------------------------------------------------


def summarize_party(run: RunState, game_data: GameData) -> str:
    """Full party detail view for equipment/build decisions."""
    lines: list[str] = []

    zone_str = ""
    if run.current_zone_id:
        zone = game_data.zones.get(run.current_zone_id)
        zone_str = f" | In Zone: {zone.name if zone else run.current_zone_id}"

    lines.append(f"=== PARTY STATUS{zone_str} | Gold: {run.party.money} ===")
    lines.append("")

    # Active members
    lines.append("ACTIVE:")
    for char_id in run.party.active:
        char = run.party.characters[char_id]
        _append_full_character(lines, char, run, game_data)
        lines.append("")

    # Reserve
    if run.party.reserve:
        lines.append("RESERVE:")
        for char_id in run.party.reserve:
            char = run.party.characters[char_id]
            job_name = _job_name(char.job_id, game_data)
            lines.append(
                f"  {char.name} ({char_id}) [{job_name} Lv{char.level}] "
                f"{char.current_hp}/{char.max_hp} HP | {_xp_progress(char)}"
            )
            lines.append(f"    {_stat_line(char)}")
            abilities = [a for a in char.abilities if a != "basic_attack"]
            lines.append(f"    Abilities: basic_attack, {', '.join(abilities)}")
        lines.append("")

    # Stash with sell prices
    lines.append(_stash_detail(run, game_data))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shop View
# ---------------------------------------------------------------------------


def summarize_shop(
    shop: ShopInventory,
    run: RunState,
    game_data: GameData,
) -> str:
    """View for shopping."""
    lines: list[str] = []

    cha = run.party.cha
    # Derive discount % from actual engine formula: buy_price = base * ratio
    # ratio = clamp(1.0 - 0.005 * CHA, 0.5, 1.5), so discount = (1.0 - ratio) * 100
    sample_ratio = calculate_buy_price(1000, cha) / 1000.0
    discount_pct = int((1.0 - sample_ratio) * 100)
    zone_name = ""
    if run.current_zone_id:
        zone = game_data.zones.get(run.current_zone_id)
        zone_name = f"{zone.name} (Lv{zone.zone_level})" if zone else run.current_zone_id

    lines.append(
        f"=== SHOP | {zone_name} | Gold: {run.party.money} | CHA: {cha} ({discount_pct}% discount) ==="
    )
    lines.append("")

    lines.append("FOR SALE:")
    for item_id in shop.available_items:
        item = game_data.items.get(item_id)
        if item and item.base_price > 0:
            price = calculate_buy_price(item.base_price, cha)
            desc = _short_item_desc(item)
            lines.append(f"  {item_id} -- {item.name} -- {desc} | {price}g (base {item.base_price})")

    lines.append("")

    # Sellable stash items
    if run.party.stash:
        lines.append("YOUR STASH -- sellable:")
        counts: Counter[str] = Counter(run.party.stash)
        for item_id, count in counts.items():
            item = game_data.items.get(item_id) or run.party.items.get(item_id)
            if item:
                sell = calculate_sell_price(item.base_price)
                qty = f" x{count}" if count > 1 else ""
                lines.append(f"  {item_id}{qty} | sell: {sell}g each")
    else:
        lines.append("YOUR STASH: empty")

    lines.append("")
    lines.append("-> Use shop_buy(item_id) or shop_sell(item_id).")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Zone Status View
# ---------------------------------------------------------------------------


def summarize_zone_status(run: RunState, game_data: GameData) -> str:
    """View of current zone progress."""
    lines: list[str] = []

    if not run.current_zone_id or not run.zone_state:
        return "Not currently in a zone."

    zone = game_data.zones.get(run.current_zone_id)
    if not zone:
        return f"Unknown zone: {run.current_zone_id}"

    lines.append(
        f"=== ZONE: {zone.name} (Lv{zone.zone_level}) | XP cap: Lv{zone.xp_cap_level} ==="
    )
    lines.append("")

    zs = run.zone_state
    total = len(zone.encounters)

    if zs.is_cleared:
        lines.append(f"Status: CLEARED")
        if zs.overstay_battles > 0:
            penalty = min(90, zs.overstay_battles * 5)
            lines.append(f"Overstay: {zs.overstay_battles} battles (-{penalty}% rewards)")
        lines.append("")
        lines.append("Zone is cleared. You can fight for diminishing returns or leave.")
    else:
        lines.append(f"Progress: {len(zs.encounters_completed)}/{total} encounters completed")
        lines.append("")
        for i, enc in enumerate(zone.encounters):
            status = "done" if i in zs.encounters_completed else ("-> NEXT" if i == zs.current_encounter_index else "   ")
            enemies_desc = ", ".join(
                f"{game_data.enemies[eid].name if eid in game_data.enemies else eid} x{cnt}"
                for eid, cnt in zip(enc.enemy_templates, enc.enemy_counts)
            )
            boss_tag = " [BOSS]" if enc.is_boss else ""
            lines.append(f"  {i + 1}. {status} {enemies_desc}{boss_tag}")

    lines.append("")

    # Party HP
    lines.append("Party HP:")
    for char_id in run.party.active:
        char = run.party.characters[char_id]
        lines.append(
            f"  {char_id}: {char.current_hp}/{char.max_hp} ({_pct(char.current_hp, char.max_hp)})"
        )
    lines.append(f"Gold: {run.party.money}")
    lines.append("")
    lines.append("Actions: fight, party_status, shop_browse, leave_zone")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Death View
# ---------------------------------------------------------------------------


def summarize_death(run: RunState, game_data: GameData) -> str:
    """View after party wipe."""
    lines: list[str] = []
    lines.append("=== DEFEAT -- YOUR PARTY HAS FALLEN ===")
    lines.append("")

    zone_name = "unknown"
    if run.current_zone_id:
        zone = game_data.zones.get(run.current_zone_id)
        zone_name = zone.name if zone else run.current_zone_id

    lines.append(f"Fell in: {zone_name}")
    lines.append(f"Zones cleared: {len(run.zones_completed)}/{len(game_data.zones)}")
    lines.append("")

    lines.append("Final party:")
    for char_id in run.party.active + run.party.reserve:
        char = run.party.characters.get(char_id)
        if char:
            job_name = _job_name(char.job_id, game_data)
            lines.append(f"  {char.name} [{job_name} Lv{char.level}]")

    lines.append("")
    lines.append("-> Use get_run_summary for full analytics, or new_run to try again.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Run Summary View
# ---------------------------------------------------------------------------


def summarize_run_report(run: RunState, game_data: GameData) -> str:
    """Comprehensive end-of-run report."""
    lines: list[str] = []
    br = run.battle_record

    outcome = "VICTORY" if not run.is_dead else "DEFEAT"
    lines.append(f"=== RUN COMPLETE -- {outcome} ===")
    lines.append("")

    # Final party
    lines.append("Final party:")
    for char_id in run.party.active:
        char = run.party.characters[char_id]
        job_name = _job_name(char.job_id, game_data)
        lines.append(f"  {char.name} [{job_name} Lv{char.level}]")
    for char_id in run.party.reserve:
        char = run.party.characters[char_id]
        job_name = _job_name(char.job_id, game_data)
        lines.append(f"  (reserve) {char.name} [{job_name} Lv{char.level}]")
    lines.append("")

    lines.append(f"Zones cleared: {len(run.zones_completed)}/{len(game_data.zones)}")
    lines.append(f"Total encounters: {br.total_encounters} ({br.victories}W / {br.defeats}L)")
    lines.append(f"Total rounds: {br.total_rounds}")
    lines.append(f"Gold: {run.party.money}")
    lines.append("")

    # Combat stats
    lines.append(f"Damage dealt: {br.total_damage_dealt}")
    by_char = br.damage_dealt_by_character()
    if by_char:
        parts = [f"{cid}: {dmg}" for cid, dmg in sorted(by_char.items(), key=lambda x: -x[1])]
        lines.append(f"  By character: {', '.join(parts)}")

    lines.append(f"Damage taken: {br.total_damage_taken}")
    lines.append(f"Healing done: {br.total_healing}")
    lines.append("")

    # Ability usage
    usage = br.most_used_abilities(actor_filter=set(run.party.characters))
    if usage:
        top = sorted(usage.items(), key=lambda x: -x[1])[:10]
        parts = [f"{aid} ({count})" for aid, count in top]
        lines.append(f"Most used abilities: {', '.join(parts)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _mc_name(run: RunState) -> str:
    for char in run.party.characters.values():
        if char.is_mc:
            return char.name
    return "Unknown"


def _job_name(job_id: str, game_data: GameData) -> str:
    job = game_data.jobs.get(job_id)
    return job.name if job else job_id


def _job_name_from_combatant(
    combatant: CombatantState, run: RunState, game_data: GameData
) -> str:
    char = run.party.characters.get(combatant.id)
    if char:
        return _job_name(char.job_id, game_data)
    return ""


def _short_item_desc(item: Item) -> str:
    """One-line item description."""
    parts: list[str] = []
    if item.is_consumable:
        if item.teaches_ability_id:
            parts.append(f"Scroll: teaches {item.teaches_ability_id}")
        elif item.casts_ability_id:
            parts.append(f"Scroll: casts {item.casts_ability_id}")
        elif item.heal_amount:
            parts.append(f"Consumable: heals {item.heal_amount} HP")
        elif item.heal_percent > 0:
            parts.append(f"Consumable: heals {item.heal_percent:.0%} HP")
        else:
            parts.append("Consumable")
    else:
        parts.append(f"{item.display_type}")
        if item.scaling:
            parts.append(_item_scaling_desc(item))
    return " | ".join(parts) if parts else item.name


def _ability_summary(ability: Ability) -> str:
    """One-line ability summary."""
    parts: list[str] = []

    if ability.trigger != TriggerCondition.NONE:
        parts.append(f"[passive, {ability.trigger.value}]")

    for effect in ability.effects:
        if effect.base_damage or effect.scaling_coefficient:
            scaling = f" + {effect.scaling_coefficient}x{effect.stat_scaling.value}" if effect.stat_scaling else ""
            parts.append(f"{effect.base_damage}{scaling} dmg")
        if effect.quality != DamageQuality.NONE:
            parts.append(effect.quality.value)
        if effect.heal_percent > 0:
            parts.append(f"{effect.heal_percent:.0%} heal")
        if effect.def_buff > 0:
            parts.append(f"self DEF +{effect.def_buff}")
        if effect.stat_buff:
            buff_parts = [f"{k}+{v}" for k, v in effect.stat_buff.items() if v != 0]
            if buff_parts:
                parts.append(f"buff {', '.join(buff_parts)}")
        if effect.duration_rounds > 0:
            parts.append(f"{effect.duration_rounds}t")

    parts.append(f"target: {ability.target.value}")
    if ability.cooldown > 0:
        parts.append(f"cd:{ability.cooldown}")

    return " | ".join(parts)


def _append_full_character(
    lines: list[str],
    char: CharacterInstance,
    run: RunState,
    game_data: GameData,
) -> None:
    """Append detailed character lines for party_status view."""
    job_name = _job_name(char.job_id, game_data)
    lines.append(
        f"  {char.name} ({char.id}) [{job_name} Lv{char.level}] "
        f"{char.current_hp}/{char.max_hp} HP ({_pct(char.current_hp, char.max_hp)}) | "
        f"{_xp_progress(char)}"
    )
    lines.append(f"    Base:  {_base_stat_line(char)}")
    lines.append(f"    Eff:   {_stat_line(char)}")

    # Equipment with current bonus
    for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
        item_id = char.equipment.get(slot)
        if item_id:
            item = game_data.items.get(item_id) or run.party.items.get(item_id)
            if item:
                bonus_str = ""
                if item.scaling:
                    stat_val = char.base_stats.get(item.scaling.stat)
                    bonus_str = f" -> {_item_bonus_at_stat(item, stat_val)} at current stats"
                lines.append(
                    f"    {slot}: {item.name} ({item_id}) -- {_item_scaling_desc(item)}{bonus_str}"
                )
            else:
                lines.append(f"    {slot}: {item_id}")
        else:
            lines.append(f"    {slot}: (empty)")

    # Abilities with damage estimates
    lines.append("    Abilities:")
    for aid in char.abilities:
        ability = game_data.abilities.get(aid)
        if ability:
            lines.append(f"      {aid} -- {_ability_summary(ability)}")

    # Growth history (MC only — shows job lineage for mimic decisions)
    if char.is_mc and char.growth_history:
        history_parts = [
            f"{_job_name(jid, game_data)}({lvls})"
            for jid, lvls in char.growth_history
        ]
        lines.append(f"    Job history: {' -> '.join(history_parts)}")

    # Next unlock
    job = game_data.jobs.get(char.job_id)
    if job:
        next_unlock = None
        for unlock in sorted(job.ability_unlocks, key=lambda u: u.level):
            if unlock.level > char.level:
                next_unlock = unlock
                break
        if next_unlock:
            lines.append(f"    Next unlock: {next_unlock.ability_id} at Lv{next_unlock.level}")


def _stash_detail(run: RunState, game_data: GameData) -> str:
    """Detailed stash listing with sell prices."""
    lines: list[str] = [f"STASH ({len(run.party.stash)}/10):"]

    if not run.party.stash:
        lines.append("  empty")
        return "\n".join(lines)

    counts: Counter[str] = Counter(run.party.stash)
    for item_id, count in counts.items():
        item = game_data.items.get(item_id) or run.party.items.get(item_id)
        if item:
            sell = calculate_sell_price(item.base_price)
            qty = f" x{count}" if count > 1 else ""
            desc = _short_item_desc(item)
            lines.append(f"  {item_id}{qty} -- {item.name} -- {desc} | sell: {sell}g")
        else:
            lines.append(f"  {item_id}")

    return "\n".join(lines)


def _render_combat_event(
    event: CombatEvent,
    combat: CombatState,
    game_data: GameData,
) -> str | None:
    """Render a single combat event as plain text. Returns None for non-significant events."""
    # Build name lookups
    names: dict[str, str] = {}
    for c in combat.player_combatants + combat.enemy_combatants:
        names[c.id] = c.id  # Use IDs as names for agent clarity

    def _n(cid: str) -> str:
        return names.get(cid, cid)

    match event.event_type:
        case CombatEventType.ROUND_START:
            return None  # Handled by header
        case CombatEventType.TURN_START:
            return None  # Noise
        case CombatEventType.CHEAT_SURVIVE_DECISION:
            choice = event.details.get("choice", "NORMAL")
            if choice == "CHEAT":
                actions = event.details.get("actions_spent", 0)
                return f"{_n(event.actor_id)} CHEATS ({actions} extra actions)"
            elif choice == "SURVIVE":
                ap = event.details.get("ap", 0)
                return f"{_n(event.actor_id)} SURVIVES (AP now: {ap})"
            return None
        case CombatEventType.ACTION_DECLARED:
            targets = event.details.get("targets", [])
            target_str = ", ".join(_n(t) for t in targets)
            ability = event.ability_id
            if target_str:
                return f"{_n(event.actor_id)} uses {ability} -> {target_str}"
            return f"{_n(event.actor_id)} uses {ability}"
        case CombatEventType.DAMAGE_DEALT:
            if event.details.get("self_damage"):
                return f"{_n(event.actor_id)} takes {event.value} recoil"
            return f"  {_n(event.target_id)} takes {event.value} dmg from {_n(event.actor_id)}"
        case CombatEventType.ITEM_USED:
            item_name = event.details.get("item_name", event.details.get("item_id", "item"))
            if event.actor_id == event.target_id:
                return f"{_n(event.actor_id)} uses {item_name}"
            return f"{_n(event.actor_id)} uses {item_name} on {_n(event.target_id)}"
        case CombatEventType.HEALING:
            source = event.details.get("source", "")
            src_str = f" ({source})" if source else ""
            return f"  {_n(event.target_id)} heals {event.value} HP{src_str}"
        case CombatEventType.STATUS_APPLIED:
            status = event.details.get("status", event.details.get("quality", "effect"))
            return f"  {_n(event.actor_id)} applies {status} to {_n(event.target_id)}"
        case CombatEventType.STATUS_EXPIRED:
            status = event.details.get("status", "effect")
            return f"  {status} wears off {_n(event.target_id)}"
        case CombatEventType.STATUS_RESISTED:
            quality = event.details.get("quality", "effect")
            return f"  {_n(event.target_id)} RESISTS {quality}!"
        case CombatEventType.DOT_TICK:
            status = event.details.get("status", "DOT")
            return f"  {_n(event.target_id)} takes {event.value} from {status}"
        case CombatEventType.DEATH:
            return f"  {_n(event.target_id)} FALLS!"
        case CombatEventType.RETALIATE_TRIGGERED:
            return f"  {_n(event.actor_id)} retaliates -> {_n(event.target_id)} for {event.value} dmg"
        case CombatEventType.THORNS_TRIGGERED:
            return f"  {_n(event.actor_id)} Thorns reflects {event.value} dmg to {_n(event.target_id)}"
        case CombatEventType.PASSIVE_TRIGGERED:
            return f"  {_n(event.actor_id)}'s {event.ability_id} triggers!"
        case CombatEventType.TAUNT_REDIRECT:
            original = event.details.get("original_target", "")
            return f"  {_n(event.target_id)} draws the attack! (redirected from {_n(original)})"
        case CombatEventType.FRENZY_STACK:
            level = event.details.get("level", 1.0)
            return f"  {_n(event.actor_id)} Frenzy {level:.2f}x (chain {event.value})"
        case CombatEventType.GOLD_STOLEN:
            return f"  {_n(event.actor_id)} steals {event.value}G from {_n(event.target_id)}"
        case CombatEventType.COMBAT_END:
            result = event.details.get("result", "")
            return f"--- {'VICTORY' if result == 'player_victory' else 'DEFEAT'} ---"
        case _:
            return None
