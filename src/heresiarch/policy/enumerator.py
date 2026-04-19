"""Decision enumerator: LegalActionSet -> list[PlayerTurnDecision].

Generates all concrete player decisions for one actor on one turn.
The solver evaluates each via forward simulation; the enumerator's
job is to produce a complete-but-pruned set of candidates.

Decisions are grouped by stance:
  SURVIVE (always 1), NORMAL (ability×target), CHEAT (N×ability×target×extras).
Dominance pruning removes strictly worse options (e.g. basic_attack
when thrust does more damage to the same target).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from heresiarch.engine.models.abilities import AbilityCategory, TargetType
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.policy.predicates import ability_damage, basic_attack_damage

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.policy.protocols import LegalActionSet


BONUS_ACTION_SUPPLY: int = 4
BASIC_ATTACK_ID: str = "basic_attack"
POTION_ITEM_ID: str = "minor_potion"


def enumerate_decisions(
    state: CombatState,
    actor: CombatantState,
    legal: LegalActionSet,
    game_data: GameData,
) -> list[PlayerTurnDecision]:
    """Enumerate all concrete legal decisions for one actor on one turn.

    Returns a list of PlayerTurnDecision objects ready for the engine.
    Applies dominance pruning to remove strictly worse options.
    """
    decisions: list[PlayerTurnDecision] = []

    enemies = state.living_enemies
    if not enemies:
        return [_survive(actor)]

    bonus = _make_bonus_actions(actor, enemies)

    # --- SURVIVE (always available) ---
    decisions.append(_survive(actor, bonus))

    # Resolve taunt constraints: taunted actors can only target taunters
    taunted = bool(legal.taunted_by)
    valid_enemy_ids = (
        [tid for tid in legal.taunted_by if tid in set(legal.living_enemy_ids)]
        if taunted
        else list(legal.living_enemy_ids)
    )
    if not valid_enemy_ids and legal.living_enemy_ids:
        valid_enemy_ids = list(legal.living_enemy_ids)

    # Pick the best offensive ability for extras (highest damage vs weakest)
    extras_ability_id = _best_extras_ability(actor, enemies, legal, game_data)

    # --- NORMAL decisions ---
    for ability_id in legal.available_ability_ids:
        ability = game_data.abilities.get(ability_id)
        if ability is None:
            continue
        for target_ids in _valid_targets(ability.target, actor, valid_enemy_ids, legal):
            decisions.append(PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=actor.id,
                    ability_id=ability_id,
                    target_ids=target_ids,
                ),
                bonus_actions=bonus,
            ))

    # --- NORMAL item use (potions) ---
    consumable_ids = _unique_consumables(legal.available_consumable_ids)
    for item_id in consumable_ids:
        item = game_data.items.get(item_id)
        if item is None or not item.is_consumable:
            continue
        if taunted and not item.heal_amount and not item.heal_percent:
            continue
        for target_id in _item_targets(actor, legal):
            decisions.append(PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=actor.id,
                    ability_id="use_item",
                    item_id=item_id,
                    target_ids=[target_id],
                ),
                bonus_actions=bonus,
            ))

    # --- CHEAT decisions (AP >= 1) ---
    max_ap = legal.action_points
    if max_ap >= 1:
        for cheat_n in range(1, max_ap + 1):
            # CHEAT with ability primary
            for ability_id in legal.available_ability_ids:
                ability = game_data.abilities.get(ability_id)
                if ability is None:
                    continue
                if ability.category not in (
                    AbilityCategory.OFFENSIVE,
                    AbilityCategory.DEFENSIVE,
                ):
                    continue
                for target_ids in _valid_targets(
                    ability.target, actor, valid_enemy_ids, legal
                ):
                    primary_target_id = target_ids[0] if target_ids else None
                    # Sweep strategy
                    sweep_extras = _make_sweep_extras(
                        actor, enemies, cheat_n, extras_ability_id,
                    )
                    decisions.append(PlayerTurnDecision(
                        combatant_id=actor.id,
                        cheat_survive=CheatSurviveChoice.CHEAT,
                        cheat_actions=cheat_n,
                        primary_action=CombatAction(
                            actor_id=actor.id,
                            ability_id=ability_id,
                            target_ids=target_ids,
                        ),
                        cheat_extra_actions=sweep_extras,
                        bonus_actions=bonus,
                    ))
                    # Focus strategy (if there's a specific target)
                    if (
                        primary_target_id is not None
                        and ability.target == TargetType.SINGLE_ENEMY
                    ):
                        focus_extras = _make_focus_extras(
                            actor, primary_target_id, cheat_n, extras_ability_id,
                        )
                        decisions.append(PlayerTurnDecision(
                            combatant_id=actor.id,
                            cheat_survive=CheatSurviveChoice.CHEAT,
                            cheat_actions=cheat_n,
                            primary_action=CombatAction(
                                actor_id=actor.id,
                                ability_id=ability_id,
                                target_ids=target_ids,
                            ),
                            cheat_extra_actions=focus_extras,
                            bonus_actions=bonus,
                        ))

            # CHEAT with item primary + attack extras
            for item_id in consumable_ids:
                item = game_data.items.get(item_id)
                if item is None or not item.is_consumable:
                    continue
                if not item.heal_amount and not item.heal_percent and not item.combat_stat_buff:
                    continue
                for target_id in _item_targets(actor, legal):
                    extras = _make_heal_extras(
                        actor, enemies, cheat_n, extras_ability_id, legal, game_data,
                    )
                    decisions.append(PlayerTurnDecision(
                        combatant_id=actor.id,
                        cheat_survive=CheatSurviveChoice.CHEAT,
                        cheat_actions=cheat_n,
                        primary_action=CombatAction(
                            actor_id=actor.id,
                            ability_id="use_item",
                            item_id=item_id,
                            target_ids=[target_id],
                        ),
                        cheat_extra_actions=extras,
                        bonus_actions=bonus,
                    ))

    return _prune_dominated(decisions, actor, enemies, game_data)


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def _valid_targets(
    target_type: TargetType,
    actor: CombatantState,
    valid_enemy_ids: list[str],
    legal: LegalActionSet,
) -> list[list[str]]:
    """Return a list of target_id lists for an ability's target type."""
    match target_type:
        case TargetType.SINGLE_ENEMY:
            return [[eid] for eid in valid_enemy_ids]
        case TargetType.ALL_ENEMIES:
            return [valid_enemy_ids] if valid_enemy_ids else []
        case TargetType.SELF:
            return [[actor.id]]
        case TargetType.SINGLE_ALLY:
            targets = [[actor.id]]
            for aid in legal.living_ally_ids:
                targets.append([aid])
            return targets
        case TargetType.ALL_ALLIES:
            all_allies = [actor.id] + list(legal.living_ally_ids)
            return [all_allies]
        case _:
            return [[valid_enemy_ids[0]]] if valid_enemy_ids else []


def _item_targets(
    actor: CombatantState,
    legal: LegalActionSet,
) -> list[str]:
    """Valid targets for consumable use (self + allies)."""
    return [actor.id]


def _unique_consumables(available: list[str]) -> list[str]:
    """Deduplicate consumables — one decision per unique item type."""
    seen: set[str] = set()
    result: list[str] = []
    for iid in available:
        if iid not in seen:
            seen.add(iid)
            result.append(iid)
    return result


# ---------------------------------------------------------------------------
# Extras generation
# ---------------------------------------------------------------------------


def _best_extras_ability(
    actor: CombatantState,
    enemies: list[CombatantState],
    legal: LegalActionSet,
    game_data: GameData,
) -> str:
    """Pick the best offensive ability for cheat extras.

    Evaluates against the weakest enemy (most common extras target).
    Only considers abilities that are off-cooldown and target enemies.
    """
    weakest = min(enemies, key=lambda e: e.current_hp) if enemies else None
    if weakest is None:
        return BASIC_ATTACK_ID

    best_id = BASIC_ATTACK_ID
    best_dmg = basic_attack_damage(actor, weakest)

    for aid in legal.available_ability_ids:
        if aid == BASIC_ATTACK_ID:
            continue
        ability = game_data.abilities.get(aid)
        if ability is None:
            continue
        if ability.category != AbilityCategory.OFFENSIVE:
            continue
        if ability.target not in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES):
            continue
        if ability.cooldown > 0:
            continue
        dmg = ability_damage(actor, weakest, ability)
        if dmg > best_dmg:
            best_dmg = dmg
            best_id = aid

    return best_id


def _make_sweep_extras(
    actor: CombatantState,
    enemies: list[CombatantState],
    count: int,
    ability_id: str,
) -> list[CombatAction]:
    """Sweep extras: distribute attacks weakest-first."""
    remaining_hp = {e.id: e.current_hp for e in enemies}
    extras: list[CombatAction] = []

    for _ in range(count):
        alive = [e for e in enemies if remaining_hp.get(e.id, 0) > 0]
        if not alive:
            target = enemies[0] if enemies else None
        else:
            target = min(alive, key=lambda e: remaining_hp[e.id])
        if target is None:
            break
        extras.append(CombatAction(
            actor_id=actor.id,
            ability_id=ability_id,
            target_ids=[target.id],
        ))
        dmg = max(1, basic_attack_damage(actor, target))
        remaining_hp[target.id] = remaining_hp.get(target.id, 0) - dmg

    return extras


def _make_focus_extras(
    actor: CombatantState,
    target_id: str,
    count: int,
    ability_id: str,
) -> list[CombatAction]:
    """Focus extras: all attacks on one target."""
    return [
        CombatAction(
            actor_id=actor.id,
            ability_id=ability_id,
            target_ids=[target_id],
        )
        for _ in range(count)
    ]


def _make_heal_extras(
    actor: CombatantState,
    enemies: list[CombatantState],
    count: int,
    extras_ability_id: str,
    legal: LegalActionSet,
    game_data: GameData,
) -> list[CombatAction]:
    """Extras for a heal/tonic primary: brace_strike (if ready) + damage."""
    extras: list[CombatAction] = []
    strongest = max(enemies, key=lambda e: e.current_hp) if enemies else None
    if strongest is None:
        return extras

    brace_id = "brace_strike"
    used_brace = False

    for _ in range(count):
        if (
            not used_brace
            and brace_id in legal.available_ability_ids
            and actor.cooldowns.get(brace_id, 0) == 0
        ):
            extras.append(CombatAction(
                actor_id=actor.id,
                ability_id=brace_id,
                target_ids=[strongest.id],
            ))
            used_brace = True
        else:
            extras.append(CombatAction(
                actor_id=actor.id,
                ability_id=extras_ability_id,
                target_ids=[strongest.id],
            ))

    return extras


# ---------------------------------------------------------------------------
# Bonus actions
# ---------------------------------------------------------------------------


def _make_bonus_actions(
    actor: CombatantState,
    enemies: list[CombatantState],
) -> list[CombatAction]:
    """Speed-bonus slot filler: basic_attack on weakest enemy."""
    if not enemies:
        return []
    weakest_id = min(enemies, key=lambda e: e.current_hp).id
    return [
        CombatAction(
            actor_id=actor.id,
            ability_id=BASIC_ATTACK_ID,
            target_ids=[weakest_id],
        )
        for _ in range(BONUS_ACTION_SUPPLY)
    ]


def _survive(
    actor: CombatantState,
    bonus: list[CombatAction] | None = None,
) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
        bonus_actions=bonus or [],
    )


# ---------------------------------------------------------------------------
# Dominance pruning
# ---------------------------------------------------------------------------


def _prune_dominated(
    decisions: list[PlayerTurnDecision],
    actor: CombatantState,
    enemies: list[CombatantState],
    game_data: GameData,
) -> list[PlayerTurnDecision]:
    """Remove strictly dominated decisions.

    A NORMAL(ability_A, target_T) is dominated by NORMAL(ability_B, target_T)
    if ability_B deals strictly more damage to T. Same logic for CHEAT
    primaries at the same AP level.
    """
    if not enemies:
        return decisions

    enemy_map = {e.id: e for e in enemies}

    # Build damage lookup: (ability_id, target_id) -> damage
    damage_cache: dict[tuple[str, str], int] = {}
    for d in decisions:
        if d.primary_action is None:
            continue
        if d.primary_action.item_id is not None:
            continue
        aid = d.primary_action.ability_id
        for tid in d.primary_action.target_ids:
            key = (aid, tid)
            if key not in damage_cache:
                target = enemy_map.get(tid)
                if target is not None:
                    ability = game_data.abilities.get(aid)
                    if ability is not None:
                        damage_cache[key] = ability_damage(actor, target, ability)
                    else:
                        damage_cache[key] = 0
                else:
                    damage_cache[key] = 0

    # For each (stance, AP, target), find the best primary ability
    best_for_group: dict[tuple[str, int, str, str], int] = {}
    # key = (stance, cheat_n, target_id, extras_sig) -> max damage

    kept: list[PlayerTurnDecision] = []
    for d in decisions:
        if d.cheat_survive == CheatSurviveChoice.SURVIVE:
            kept.append(d)
            continue

        if d.primary_action is None or d.primary_action.item_id is not None:
            kept.append(d)
            continue

        aid = d.primary_action.ability_id
        target_id = d.primary_action.target_ids[0] if d.primary_action.target_ids else ""
        extras_sig = _extras_signature(d.cheat_extra_actions)
        group_key = (
            d.cheat_survive.value,
            d.cheat_actions,
            target_id,
            extras_sig,
        )

        dmg = damage_cache.get((aid, target_id), 0)
        existing = best_for_group.get(group_key, -1)
        if dmg >= existing:
            if dmg > existing:
                # Remove previously kept decisions in this group
                kept = [
                    k for k in kept
                    if _group_key_of(k) != group_key
                ]
            best_for_group[group_key] = dmg
            kept.append(d)

    return kept


def _extras_signature(extras: list[CombatAction]) -> str:
    """Fingerprint the extras pattern for grouping."""
    if not extras:
        return ""
    target_ids = tuple(
        a.target_ids[0] if a.target_ids else "" for a in extras
    )
    return str(target_ids)


def _group_key_of(d: PlayerTurnDecision) -> tuple[str, int, str, str] | None:
    if d.cheat_survive == CheatSurviveChoice.SURVIVE:
        return None
    if d.primary_action is None or d.primary_action.item_id is not None:
        return None
    target_id = d.primary_action.target_ids[0] if d.primary_action.target_ids else ""
    return (
        d.cheat_survive.value,
        d.cheat_actions,
        target_id,
        _extras_signature(d.cheat_extra_actions),
    )
