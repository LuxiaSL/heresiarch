"""Auto-battle replay: validate recorded decisions against live combat.

Pure functions extracted from the TUI's AutoBattleMixin so both the TUI
and GameSession.auto_battle_round() share one implementation. A recorded
round is replayed with best-effort fidelity: dead targets are remapped,
unavailable abilities/items fall back to basic_attack, cheat AP is
capped to what the combatant actually has, and SPD bonus actions are
recomputed for the current fight.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from heresiarch.engine.formulas import calculate_speed_bonus
from heresiarch.engine.models.abilities import TargetType
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    PlayerTurnDecision,
)

if TYPE_CHECKING:
    from heresiarch.engine.models.abilities import Ability
    from heresiarch.engine.models.battle_record import (
        EncounterRecord,
        RoundRecord,
    )
    from heresiarch.engine.models.combat_state import CombatantState, CombatState


def find_matching_record(
    encounters: list[EncounterRecord],
    enemy_template_ids: list[str],
) -> EncounterRecord | None:
    """Find the most recent recorded victory against the same enemy group."""
    wanted = sorted(enemy_template_ids)
    for encounter in reversed(encounters):
        if (
            encounter.was_victory
            and sorted(encounter.enemy_template_ids) == wanted
            and encounter.rounds
        ):
            return encounter
    return None


def make_fallback_decision(
    combatant_id: str, living_enemy_ids: list[str],
) -> PlayerTurnDecision:
    """Create a safe default: NORMAL + basic_attack on first living enemy."""
    target = living_enemy_ids[0] if living_enemy_ids else combatant_id
    return PlayerTurnDecision(
        combatant_id=combatant_id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=CombatAction(
            actor_id=combatant_id,
            ability_id="basic_attack",
            target_ids=[target],
        ),
    )


def build_replay_decisions(
    round_record: RoundRecord,
    combat: CombatState,
    abilities: dict[str, Ability],
    stash: list[str],
    claimed_items: list[str] | None = None,
) -> dict[str, PlayerTurnDecision]:
    """Build validated decisions for every living player from a recorded round.

    ``claimed_items`` tracks item copies already spoken for this round and
    is appended to as items are claimed (pass a shared list to coordinate
    with other claim sources; omit for a fresh round).
    """
    if claimed_items is None:
        claimed_items = []
    decisions: dict[str, PlayerTurnDecision] = {}
    living_enemy_ids = [e.id for e in combat.living_enemies]
    living_player_ids = [p.id for p in combat.living_players]

    for player in combat.living_players:
        recorded = round_record.player_decisions.get(player.id)
        if recorded is None:
            decisions[player.id] = make_fallback_decision(
                player.id, living_enemy_ids,
            )
            continue
        decisions[player.id] = validate_replay_decision(
            recorded, player, combat, living_enemy_ids, living_player_ids,
            abilities, stash, claimed_items,
        )

    return decisions


def validate_replay_decision(
    recorded: PlayerTurnDecision,
    player: CombatantState,
    combat: CombatState,
    living_enemy_ids: list[str],
    living_player_ids: list[str],
    abilities: dict[str, Ability],
    stash: list[str],
    claimed_items: list[str],
) -> PlayerTurnDecision:
    """Validate a recorded decision against current combat state."""
    cid = player.id

    cs = recorded.cheat_survive
    cheat_actions = recorded.cheat_actions

    if cs == CheatSurviveChoice.CHEAT:
        if player.action_points < 1:
            cs = CheatSurviveChoice.NORMAL
            cheat_actions = 0
        else:
            cheat_actions = min(cheat_actions, player.action_points)

    if cs == CheatSurviveChoice.SURVIVE and player.taunted_by:
        cs = CheatSurviveChoice.NORMAL

    if cs == CheatSurviveChoice.SURVIVE:
        return PlayerTurnDecision(
            combatant_id=cid,
            cheat_survive=CheatSurviveChoice.SURVIVE,
        )

    # Validate primary action
    primary = validate_replay_action(
        recorded.primary_action, cid, player, combat,
        living_enemy_ids, living_player_ids, abilities, stash, claimed_items,
    )

    # Validate cheat extra actions
    cheat_extras: list[CombatAction] = []
    if cs == CheatSurviveChoice.CHEAT and cheat_actions > 0:
        for action in recorded.cheat_extra_actions[:cheat_actions]:
            cheat_extras.append(validate_replay_action(
                action, cid, player, combat,
                living_enemy_ids, living_player_ids,
                abilities, stash, claimed_items,
            ))
        fallback_target = living_enemy_ids[0] if living_enemy_ids else cid
        while len(cheat_extras) < cheat_actions:
            cheat_extras.append(CombatAction(
                actor_id=cid, ability_id="basic_attack",
                target_ids=[fallback_target],
            ))

    # Validate bonus actions — recalculate SPD bonus for current combat
    bonus: list[CombatAction] = []
    slowest_enemy_spd = min(
        (e.effective_stats.SPD for e in combat.living_enemies), default=0,
    )
    spd_bonus = calculate_speed_bonus(
        player.effective_stats.SPD, slowest_enemy_spd,
    )
    if spd_bonus > 0:
        for action in recorded.bonus_actions[:spd_bonus]:
            bonus.append(validate_replay_action(
                action, cid, player, combat,
                living_enemy_ids, living_player_ids,
                abilities, stash, claimed_items,
            ))
        fallback_target = living_enemy_ids[0] if living_enemy_ids else cid
        while len(bonus) < spd_bonus:
            bonus.append(CombatAction(
                actor_id=cid, ability_id="basic_attack",
                target_ids=[fallback_target],
            ))

    return PlayerTurnDecision(
        combatant_id=cid,
        cheat_survive=cs,
        cheat_actions=cheat_actions,
        primary_action=primary,
        cheat_extra_actions=cheat_extras,
        bonus_actions=bonus,
    )


def validate_replay_action(
    recorded_action: CombatAction | None,
    cid: str,
    player: CombatantState,
    combat: CombatState,
    living_enemy_ids: list[str],
    living_player_ids: list[str],
    abilities: dict[str, Ability],
    stash: list[str],
    claimed_items: list[str],
) -> CombatAction:
    """Validate a single combat action, falling back to basic_attack if needed."""
    fallback_target = living_enemy_ids[0] if living_enemy_ids else cid
    fallback = CombatAction(
        actor_id=cid, ability_id="basic_attack", target_ids=[fallback_target],
    )

    if recorded_action is None:
        return fallback

    if recorded_action.is_windup_push:
        if player.charge_turns_remaining > 0:
            return CombatAction(actor_id=cid, is_windup_push=True)
        return fallback

    if recorded_action.item_id:
        available = list(stash)
        for claimed in claimed_items:
            try:
                available.remove(claimed)
            except ValueError:
                pass
        if recorded_action.item_id in available:
            claimed_items.append(recorded_action.item_id)
            targets = retarget(
                recorded_action.target_ids, living_player_ids,
            )
            return CombatAction(
                actor_id=cid, ability_id="use_item",
                item_id=recorded_action.item_id, target_ids=targets,
            )
        return fallback

    ability_id = recorded_action.ability_id
    ability = abilities.get(ability_id)
    if ability is None:
        return fallback

    if ability_id not in player.ability_ids:
        return fallback

    if player.cooldowns.get(ability_id, 0) > 0:
        return fallback

    targets = retarget_for_ability(
        ability, recorded_action.target_ids, cid,
        living_enemy_ids, living_player_ids,
    )
    return CombatAction(actor_id=cid, ability_id=ability_id, target_ids=targets)


def retarget(
    recorded_targets: list[str], living_ids: list[str],
) -> list[str]:
    """Remap recorded target IDs to living combatants."""
    if not living_ids:
        return list(recorded_targets)
    valid = [tid for tid in recorded_targets if tid in living_ids]
    return valid if valid else [living_ids[0]]


def retarget_for_ability(
    ability: Ability,
    recorded_targets: list[str],
    cid: str,
    living_enemy_ids: list[str],
    living_player_ids: list[str],
) -> list[str]:
    """Retarget based on ability's target type."""
    match ability.target:
        case TargetType.SELF:
            return [cid]
        case TargetType.ALL_ENEMIES:
            return list(living_enemy_ids)
        case TargetType.ALL_ALLIES:
            return list(living_player_ids)
        case TargetType.SINGLE_ALLY:
            valid = [t for t in recorded_targets if t in living_player_ids]
            return valid if valid else (
                [living_player_ids[0]] if living_player_ids else [cid]
            )
        case _:  # SINGLE_ENEMY and anything enemy-shaped
            valid = [t for t in recorded_targets if t in living_enemy_ids]
            return valid if valid else (
                [living_enemy_ids[0]] if living_enemy_ids else [cid]
            )
