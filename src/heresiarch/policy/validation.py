"""Validation layer between policy and engine.

Sits between CombatPolicy.decide() and CombatEngine.process_round().
Takes the policy's PlayerTurnDecision and coerces it into a legal one
before the engine sees it. This keeps policies simple (they can pick
whatever feels right) while never letting an illegal action reach the
engine.

Decisions (encoded here, aligned with D6 in the spec):
  - Taunt: coerce-and-log. Engine already does this, but doing it here
    means the policy trace sees the corrected target.
  - Cooldown: fall through to basic_attack. If the policy wanted to
    cast X and X is on cooldown, we silently fall back rather than
    wasting a round.
  - Ability availability: fail-loud. A policy asking for an ability
    the actor doesn't know is a bug in the policy table.
  - AP insufficient for cheat: downgrade cheat_actions to what's
    available; if zero, convert to normal.
  - Dead target (or no target at all for a SINGLE_ENEMY): re-resolve
    to first living enemy. If no enemies alive, combat should already
    be over — but defensively, leave the decision unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from heresiarch.engine.models.abilities import Ability, TargetType
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)

from .protocols import LegalActionSet


@dataclass
class ValidationIssue:
    """One violation the validator corrected."""

    kind: str  # "taunt_redirect", "cooldown_fallback", "ap_downgrade",
               # "dead_target_retarget", "missing_target"
    detail: str


class ValidationError(Exception):
    """Raised for fail-loud violations (e.g. unknown ability)."""


def compute_legal(
    state: CombatState,
    actor: CombatantState,
    stash: list[str] | None = None,
) -> LegalActionSet:
    """Enumerate the legal-action surface for one actor on one turn.

    ``stash`` is the party stash as of this turn (after any claims made
    earlier in the same round). Policies that emit use_item actions
    must pick from this list; the driver claims each used item before
    computing legal for the next actor, so no double-spending.
    """
    return LegalActionSet(
        actor_id=actor.id,
        available_ability_ids=[
            aid for aid in actor.ability_ids
            if actor.cooldowns.get(aid, 0) == 0
        ],
        living_enemy_ids=[e.id for e in state.living_enemies],
        living_ally_ids=[p.id for p in state.living_players if p.id != actor.id],
        taunted_by=list(actor.taunted_by),
        action_points=actor.action_points,
        cheat_debt=actor.cheat_debt,
        cooldowns=dict(actor.cooldowns),
        available_consumable_ids=list(stash) if stash else [],
    )


def resolve_decision(
    decision: PlayerTurnDecision,
    state: CombatState,
    actor: CombatantState,
    abilities: dict[str, Ability],
    legal: LegalActionSet | None = None,
) -> tuple[PlayerTurnDecision, list[ValidationIssue]]:
    """Return a legal PlayerTurnDecision + list of corrections made.

    Raises ValidationError for fail-loud violations (unknown ability on
    the actor's sheet).
    """
    issues: list[ValidationIssue] = []
    legal = legal or compute_legal(state, actor)

    # Survive is always legal; nothing to validate.
    if decision.cheat_survive == CheatSurviveChoice.SURVIVE:
        return decision, issues

    primary = decision.primary_action
    if primary is not None:
        primary, primary_issues = _resolve_action(
            primary, state, actor, abilities, legal, is_primary=True,
        )
        issues.extend(primary_issues)

    # Cheat AP downgrade
    cheat_mode = decision.cheat_survive
    cheat_ap = decision.cheat_actions
    cheat_extras = list(decision.cheat_extra_actions)

    if cheat_mode == CheatSurviveChoice.CHEAT:
        if cheat_ap > actor.action_points:
            issues.append(ValidationIssue(
                kind="ap_downgrade",
                detail=(
                    f"{actor.id}: wanted {cheat_ap} AP, only {actor.action_points} "
                    f"available — downgrading"
                ),
            ))
            cheat_ap = actor.action_points
            cheat_extras = cheat_extras[:cheat_ap]
        if cheat_ap == 0:
            # No AP left — fall through to normal.
            cheat_mode = CheatSurviveChoice.NORMAL
            cheat_extras = []

    # Resolve each cheat extra
    resolved_extras: list[CombatAction] = []
    for extra in cheat_extras:
        if extra.is_windup_push:
            resolved_extras.append(extra)
            continue
        fixed, extra_issues = _resolve_action(
            extra, state, actor, abilities, legal, is_primary=False,
        )
        if fixed is not None:
            resolved_extras.append(fixed)
        issues.extend(extra_issues)

    # Bonus actions (speed-bonus freebies) — same resolution as extras
    resolved_bonus: list[CombatAction] = []
    for ba in decision.bonus_actions:
        if ba.is_windup_push:
            resolved_bonus.append(ba)
            continue
        fixed, ba_issues = _resolve_action(
            ba, state, actor, abilities, legal, is_primary=False,
        )
        if fixed is not None:
            resolved_bonus.append(fixed)
        issues.extend(ba_issues)

    return (
        PlayerTurnDecision(
            combatant_id=decision.combatant_id,
            cheat_survive=cheat_mode,
            cheat_actions=cheat_ap,
            primary_action=primary,
            cheat_extra_actions=resolved_extras,
            bonus_actions=resolved_bonus,
        ),
        issues,
    )


def _resolve_action(
    action: CombatAction,
    state: CombatState,
    actor: CombatantState,
    abilities: dict[str, Ability],
    legal: LegalActionSet,
    *,
    is_primary: bool,
) -> tuple[CombatAction | None, list[ValidationIssue]]:
    """Fix up one CombatAction. Return (possibly-None replacement, issues)."""
    issues: list[ValidationIssue] = []

    # Item-use action — validation is handled by the engine's item path.
    if action.item_id is not None:
        return action, issues

    ability_id = action.ability_id
    if not ability_id:
        # Empty action — treat as basic_attack on first enemy.
        ability_id = "basic_attack"

    # fail-loud: actor doesn't know this ability
    if ability_id not in actor.ability_ids:
        raise ValidationError(
            f"{actor.id} does not know ability '{ability_id}'. "
            f"Available: {sorted(actor.ability_ids)}"
        )

    # cooldown: fall back to basic_attack
    cd = actor.cooldowns.get(ability_id, 0)
    if cd > 0:
        issues.append(ValidationIssue(
            kind="cooldown_fallback",
            detail=f"{actor.id}: {ability_id} on cooldown ({cd}) — using basic_attack",
        ))
        ability_id = "basic_attack"
        if ability_id not in actor.ability_ids:
            # No basic_attack (extreme edge case) — drop the action entirely.
            return None, issues

    # Taunt coercion: if this action targets an enemy and actor is taunted,
    # the engine will redirect, but surfacing it in the trace matters for
    # debugging. Only redirect when the ability actually targets an enemy.
    ability = abilities.get(ability_id)
    target_ids = list(action.target_ids)

    if ability is not None and ability.target in (
        TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES,
    ):
        living_taunters = [
            tid for tid in actor.taunted_by
            if any(e.id == tid and e.is_alive for e in state.enemy_combatants)
        ]
        if living_taunters and ability.target == TargetType.SINGLE_ENEMY:
            if not target_ids or target_ids[0] not in living_taunters:
                issues.append(ValidationIssue(
                    kind="taunt_redirect",
                    detail=f"{actor.id} taunted — redirecting to {living_taunters[0]}",
                ))
                target_ids = [living_taunters[0]]

    # Dead/missing target re-resolve for SINGLE_ENEMY
    if ability is not None and ability.target == TargetType.SINGLE_ENEMY:
        living_enemy_ids = {e.id for e in state.living_enemies}
        if not target_ids or target_ids[0] not in living_enemy_ids:
            if state.living_enemies:
                issues.append(ValidationIssue(
                    kind="dead_target_retarget",
                    detail=(
                        f"{actor.id}: target gone — retargeting "
                        f"{state.living_enemies[0].id}"
                    ),
                ))
                target_ids = [state.living_enemies[0].id]

    # SINGLE_ALLY: default to self if no target specified or target dead
    if ability is not None and ability.target == TargetType.SINGLE_ALLY:
        living_ally_ids = {p.id for p in state.living_players}
        if not target_ids or target_ids[0] not in living_ally_ids:
            target_ids = [actor.id]

    # ALL_ENEMIES: fill with all living enemies if missing
    if ability is not None and ability.target == TargetType.ALL_ENEMIES:
        target_ids = [e.id for e in state.living_enemies]

    # ALL_ALLIES: fill with all living players
    if ability is not None and ability.target == TargetType.ALL_ALLIES:
        target_ids = [p.id for p in state.living_players]

    # SELF: target self
    if ability is not None and ability.target == TargetType.SELF:
        target_ids = [actor.id]

    return (
        CombatAction(
            actor_id=actor.id,
            ability_id=ability_id,
            target_ids=target_ids,
            item_id=None,
            is_windup_push=action.is_windup_push,
        ),
        issues,
    )
