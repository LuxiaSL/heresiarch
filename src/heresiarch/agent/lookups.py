"""Data lookup views: detailed reference text for jobs, abilities, items, enemies, zones, formulas.

Pure functions. No side effects. Takes GameData, returns strings.
All output is plain text (no Rich markup) optimized for LLM token budgets.
"""

from __future__ import annotations

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import evaluate_item_scaling
from heresiarch.engine.models.abilities import DamageQuality, TriggerCondition
from heresiarch.engine.models.stats import StatType

# Shared formatting helpers — defined in summarizer, reused here.
from heresiarch.agent.summarizer import _ability_summary, _item_scaling_desc


def lookup_job_view(job_id: str, game_data: GameData) -> str:
    """Detailed job reference."""
    job = game_data.jobs.get(job_id)
    if not job:
        return f"Unknown job: {job_id}"

    lines: list[str] = []
    lines.append(f"=== {job.name} ({job_id}) ===")
    if job.description:
        lines.append(f'Origin: {job.origin} -- "{job.description}"')
    lines.append("")

    g = job.growth
    lines.append(
        f"Growth per level: STR +{g.effective_growth(StatType.STR)}, "
        f"MAG +{g.effective_growth(StatType.MAG)}, "
        f"DEF +{g.effective_growth(StatType.DEF)}, "
        f"RES +{g.effective_growth(StatType.RES)}, "
        f"SPD +{g.effective_growth(StatType.SPD)}"
    )
    lines.append(f"  (base +1 all stats per level + job bonus of {g.budget} total)")
    lines.append(f"Base HP: {job.base_hp} | HP growth: +{job.hp_growth}/level | HP from DEF: 1.5xDEF")
    lines.append("")

    # Innate
    innate = game_data.abilities.get(job.innate_ability_id)
    if innate:
        lines.append(f"Innate: {job.innate_ability_id} -- {_ability_summary(innate)}")

    # Unlocks
    lines.append("Ability unlocks:")
    for unlock in sorted(job.ability_unlocks, key=lambda u: u.level):
        ability = game_data.abilities.get(unlock.ability_id)
        if ability:
            lines.append(f"  Lv{unlock.level}: {unlock.ability_id} -- {_ability_summary(ability)}")

    return "\n".join(lines)


def lookup_ability_view(ability_id: str, game_data: GameData) -> str:
    """Detailed ability reference."""
    ability = game_data.abilities.get(ability_id)
    if not ability:
        return f"Unknown ability: {ability_id}"

    lines: list[str] = []
    lines.append(f"=== {ability.name} ({ability_id}) ===")
    lines.append(
        f"Category: {ability.category.value} | Target: {ability.target.value} | "
        f"Cooldown: {ability.cooldown} rounds"
    )

    if ability.trigger != TriggerCondition.NONE:
        lines.append(f"Trigger: {ability.trigger.value} (threshold: {ability.trigger_threshold})")
    lines.append("")

    for i, effect in enumerate(ability.effects):
        quality_str = f" [{effect.quality.value}]" if effect.quality != DamageQuality.NONE else ""
        scaling_str = ""
        if effect.stat_scaling:
            scaling_str = f" + {effect.scaling_coefficient}x{effect.stat_scaling.value}"
        dmg_str = f"{effect.base_damage}{scaling_str}" if effect.base_damage or scaling_str else ""

        parts: list[str] = []
        if dmg_str:
            parts.append(f"Damage: {dmg_str}")
        if effect.duration_rounds > 0:
            parts.append(f"Duration: {effect.duration_rounds}t")
        if effect.heal_percent > 0:
            parts.append(f"Heal: {effect.heal_percent:.0%}")
        if effect.stat_buff:
            buff_parts = [f"{k} +{v}" for k, v in effect.stat_buff.items() if v != 0]
            if buff_parts:
                parts.append(f"Buff: {', '.join(buff_parts)}")
        if effect.def_buff > 0:
            parts.append(f"Self DEF +{effect.def_buff}")
        if effect.self_damage_ratio > 0:
            parts.append(f"Self-damage: {effect.self_damage_ratio:.0%}")
        if effect.leech_percent > 0:
            parts.append(f"Leech: {effect.leech_percent:.0%}")
        if effect.pierce_percent > 0:
            parts.append(f"Pierce: {effect.pierce_percent:.0%}")
        if effect.gold_steal_flat > 0:
            parts.append(f"Gold steal: {effect.gold_steal_flat}")

        lines.append(f"  Effect{quality_str}: {' | '.join(parts)}")

    if ability.description:
        lines.append("")
        lines.append(ability.description)

    return "\n".join(lines)


def lookup_item_view(item_id: str, game_data: GameData) -> str:
    """Detailed item reference."""
    item = game_data.items.get(item_id)
    if not item:
        return f"Unknown item: {item_id}"

    lines: list[str] = []
    lines.append(f"=== {item.name} ({item_id}) ===")
    lines.append(f"Type: {item.display_type} | Base price: {item.base_price}g")
    lines.append("")

    if item.scaling:
        lines.append(f"Scaling: {_item_scaling_desc(item)}")
        # Show bonus at a few stat values
        stat = item.scaling.stat.value
        for val in (20, 50, 100):
            bonus = evaluate_item_scaling(item.scaling, val)
            lines.append(f"  At {stat} {val}: {bonus:.1f} bonus")
        lines.append("")

    if item.conversion:
        c = item.conversion
        lines.append(
            f"Conversion: {c.source_stat.value} -> {c.target_stat.value} ({c.scaling_type.value})"
        )
        lines.append("")

    extras: list[str] = []
    if item.flat_stat_bonus:
        for stat, val in item.flat_stat_bonus.items():
            if val != 0:
                extras.append(f"{stat} +{val}")
    if item.hp_bonus:
        extras.append(f"HP +{item.hp_bonus}")
    if item.phys_leech_percent > 0:
        extras.append(f"Phys Leech {item.phys_leech_percent:.0%}")
    if item.mag_leech_percent > 0:
        extras.append(f"Mag Leech {item.mag_leech_percent:.0%}")
    if item.extra_def_reduction > 0:
        extras.append(f"DEF reduction +{item.extra_def_reduction}")
    if item.granted_ability_id:
        extras.append(f"Grants: {item.granted_ability_id}")
    if item.teaches_ability_id:
        extras.append(f"Teaches: {item.teaches_ability_id} (permanent)")
    if item.is_consumable:
        if item.heal_amount:
            extras.append(f"Heals {item.heal_amount} HP")
        if item.heal_percent > 0:
            extras.append(f"Heals {item.heal_percent:.0%} HP")
        if item.casts_ability_id:
            extras.append(f"Casts: {item.casts_ability_id}")
    if extras:
        lines.append(f"Properties: {', '.join(extras)}")

    return "\n".join(lines)


def lookup_enemy_view(enemy_id: str, game_data: GameData) -> str:
    """Detailed enemy reference."""
    template = game_data.enemies.get(enemy_id)
    if not template:
        return f"Unknown enemy: {enemy_id}"

    lines: list[str] = []
    lines.append(f"=== {template.name} ({enemy_id}) ===")
    lines.append(f"Archetype: {template.archetype.value} | Budget: {template.budget_multiplier}x zone level")
    lines.append("")

    dist = template.stat_distribution
    lines.append(
        f"Stat distribution: "
        + " ".join(f"{k} {v:.0%}" for k, v in dist.items() if v > 0)
    )
    lines.append(f"HP: {template.base_hp} base + {template.hp_per_budget} per budget point")
    lines.append("")

    # Stats at a few zone levels
    lines.append("Scaling by zone level:")
    for zl in (1, 5, 8, 12, 15):
        budget = int(zl * template.budget_multiplier)
        stats = {k: int(budget * v) for k, v in dist.items()}
        hp = template.base_hp + int(budget * template.hp_per_budget)
        stat_str = " ".join(f"{k}:{v}" for k, v in stats.items() if v > 0)
        lines.append(f"  Zone {zl:2d}: {stat_str} | HP: {hp}")
    lines.append("")

    # Action table
    lines.append("Action weights:")
    for aw in template.action_table.base_weights:
        lines.append(f"  {aw.ability_id}: {aw.weight:.0%}")
    if template.action_table.conditions:
        for cond in template.action_table.conditions:
            lines.append(f"  Condition: {cond.condition_type} -> {', '.join(f'{aw.ability_id}: {aw.weight:.0%}' for aw in cond.weight_overrides)}")
    lines.append("")

    # Abilities and equipment
    lines.append(f"Abilities: {', '.join(template.abilities)}")
    if template.equipment:
        lines.append(f"Equipment: {', '.join(template.equipment)}")

    # Drop table
    dt = game_data.drop_tables.get(enemy_id)
    if dt and dt.pools:
        lines.append("")
        lines.append("Drops:")
        for i, pool in enumerate(dt.pools):
            chance_str = f"{pool.chance:.0%}" if pool.chance < 1.0 else "guaranteed"
            entry_descs: list[str] = []
            for entry in pool.items:
                if entry.item_id:
                    item = game_data.items.get(entry.item_id)
                    entry_descs.append(item.name if item else entry.item_id)
                elif entry.category:
                    tier_str = f" T{entry.tier}" if entry.tier else ""
                    entry_descs.append(f"[{entry.category}{tier_str}]")
            for branch in pool.branches:
                b_entries: list[str] = []
                for entry in branch.items:
                    if entry.item_id:
                        item = game_data.items.get(entry.item_id)
                        b_entries.append(item.name if item else entry.item_id)
                    elif entry.category:
                        tier_str = f" T{entry.tier}" if entry.tier else ""
                        b_entries.append(f"[{entry.category}{tier_str}]")
                entry_descs.append(f"{branch.count}x({'/'.join(b_entries)})")
            items_str = ", ".join(entry_descs) if entry_descs else "?"
            lines.append(f"  Pool {i+1} ({chance_str}, {pool.count}x): {items_str}")

    return "\n".join(lines)


def lookup_zone_view(zone_id: str, game_data: GameData) -> str:
    """Detailed zone reference."""
    zone = game_data.zones.get(zone_id)
    if not zone:
        return f"Unknown zone: {zone_id}"

    lines: list[str] = []
    lines.append(f"=== {zone.name} ({zone_id}) ===")
    lines.append(
        f"Level: {zone.zone_level} | Region: {zone.region} | "
        f"Loot tier: {zone.loot_tier} | XP cap: Lv{zone.xp_cap_level}"
    )

    if zone.unlock_requires:
        reqs = [
            f"{r.type}: {r.zone_id or r.item_id or f'Lv{r.level}'}"
            for r in zone.unlock_requires
        ]
        lines.append(f"Unlock requires: {', '.join(reqs)}")
    lines.append("")

    lines.append(f"Encounters ({len(zone.encounters)}):")
    for i, enc in enumerate(zone.encounters):
        enemies_desc = ", ".join(
            f"{game_data.enemies[eid].name if eid in game_data.enemies else eid} x{cnt}"
            for eid, cnt in zip(enc.enemy_templates, enc.enemy_counts)
        )
        boss_tag = " [BOSS]" if enc.is_boss else ""
        lines.append(f"  {i + 1}. {enemies_desc}{boss_tag}")

    if zone.random_spawns:
        lines.append("")
        for spawn in zone.random_spawns:
            name = game_data.enemies[spawn.enemy_template_id].name if spawn.enemy_template_id in game_data.enemies else spawn.enemy_template_id
            lines.append(f"Random spawn: {name} ({spawn.chance:.0%} per encounter)")

    if zone.recruitment_chance > 0:
        lines.append(f"Recruitment chance: {zone.recruitment_chance:.0%}")

    return "\n".join(lines)


def lookup_formula_view(topic: str) -> str:
    """Game formula reference."""
    formulas: dict[str, str] = {
        "damage": (
            "=== Physical Damage ===\n"
            "raw = ability_base + (coefficient x STR) + item_scaling_bonus\n"
            "reduction = target_DEF x 0.5 x (1 - pierce_percent)\n"
            "damage = max(1, raw - reduction)\n"
            "\n"
            "DEF is 50% effective at reducing physical damage.\n"
            "Pierce ignores a percentage of that reduction.\n"
            "\n"
            "=== Magical Damage ===\n"
            "damage = max(1, ability_base + (coefficient x MAG) + item_scaling_bonus)\n"
            "Magic has NO flat reduction from any stat.\n"
            "RES only gates secondary effects (see 'res_gate')."
        ),
        "res_gate": (
            "=== RES Threshold Gate ===\n"
            "Secondary effects (status/debuff) are RESISTED when:\n"
            "  target_RES >= caster_MAG x 0.7\n"
            "\n"
            "This means the caster needs MAG > target_RES / 0.7\n"
            "for debuffs to land. Does NOT affect direct damage."
        ),
        "hp": (
            "=== HP Formula ===\n"
            "max_hp = base_hp + (hp_growth x level) + (effective_DEF x 1.5)\n"
            "\n"
            "DEF contributes significantly to total HP pool."
        ),
        "xp": (
            "=== XP and Leveling ===\n"
            "XP to reach level N: N^2 x 10 (for N >= 2, level 1 = 0 XP)\n"
            "  Lv2: 40, Lv5: 250, Lv10: 1000, Lv15: 2250, Lv20: 4000\n"
            "\n"
            "XP per enemy kill: zone_level x budget_multiplier\n"
            "If char_level > zone_xp_cap:\n"
            "  penalty = 50% per level over cap, floored at 10% of base\n"
            "\n"
            "Overstay penalty: -5% XP per extra battle, floored at 10%"
        ),
        "bonus_actions": (
            "=== Speed Bonus Actions ===\n"
            "Compare your SPD to the slowest enemy's SPD.\n"
            "Bonus actions at exponential thresholds: +1 at 2x, +2 at 4x, +3 at 8x.\n"
            "Bonus actions work like extra AP: you choose ability + target for each.\n"
            "Pass 'bonus_actions' in your decision (same format as cheat_extras).\n"
            "If omitted, the engine auto-repeats your primary action.\n"
            "Speed bonus actions are full-power, trigger all passives (frenzy, thorns, etc.).\n"
            "Survive suppresses speed bonus (hunkering down = no extra actions).\n"
            "Enemies get the same bonus against slow players."
        ),
        "shop_pricing": (
            "=== Shop Pricing ===\n"
            "buy_price = base_price x clamp(1.0 - 0.005 x CHA, 0.5, 1.5)\n"
            "sell_price = base_price x 0.4\n"
            "\n"
            "At CHA 0: full price. At CHA 100: 50% off (minimum).\n"
            "CHA can go negative for penalty pricing."
        ),
        "overstay": (
            "=== Overstay Mechanics ===\n"
            "After clearing a zone, you can keep fighting.\n"
            "Each extra battle: -5% to money, item drops, and XP.\n"
            "Floor: 10% rewards at 18+ extra battles.\n"
            "Guaranteed drops are unaffected."
        ),
        "cheat_survive": (
            "=== Cheat/Survive/Normal ===\n"
            "NORMAL: Standard turn. No AP change.\n"
            "SURVIVE: Bank 1 AP. Take 50% less damage this round.\n"
            "CHEAT: Spend banked AP for extra actions this turn.\n"
            "  1 AP = 1 extra action, max 3 AP banked.\n"
            "  Cheat debt: +1 per action spent, recovers 1/turn.\n"
            "  While in debt: enemies deal bonus damage."
        ),
        "scaling_types": (
            "=== Item Scaling Types ===\n"
            "LINEAR:      base + coeff x STAT (steady growth)\n"
            "SUPERLINEAR: base + linear x STAT + quad x STAT^2 (accelerating)\n"
            "QUADRATIC:   base + quad x STAT^2 (late-game monster)\n"
            "DEGENERATE:  offset + quad x STAT^2 (negative early, explosive late)\n"
            "FLAT:        base (constant, no scaling)\n"
            "SIGMOID:     bounded S-curve (used by converters)"
        ),
    }

    result = formulas.get(topic)
    if result:
        return result

    available = ", ".join(sorted(formulas.keys()))
    return f"Unknown formula topic: '{topic}'. Available: {available}"
