"""Heuristic rollout policy for combat solver forward simulation.

Ultra-lightweight survive-then-kill policy. Used by the combat solver
to evaluate candidate decisions: after the solver applies a candidate
to the current round, the rollout policy plays out remaining rounds
to produce a terminal evaluation.

Job-agnostic: picks the actor's best available offensive ability for
kill checks and damage estimation. Works for STR jobs (basic_attack,
thrust), MAG jobs (bolt, litany), and DEF-scaling jobs (rebuke).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from heresiarch.engine.models.abilities import AbilityCategory, TargetType
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.policy.predicates import (
    ability_damage,
    basic_attack_damage,
    minimum_ap_to_kill_all,
    minimum_ap_to_kill_all_passive,
    projected_incoming_damage,
)
from heresiarch.policy.rule_engine import RuleContext

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.abilities import Ability
    from heresiarch.policy.protocols import LegalActionSet

BONUS_ACTION_SUPPLY: int = 4
BASIC_ATTACK_ID: str = "basic_attack"
POTION_ITEM_ID: str = "minor_potion"


def best_attack_ability(
    actor: CombatantState,
    enemies: list[CombatantState],
    game_data: GameData,
) -> tuple[str, Ability | None]:
    """Find the actor's highest-damage offensive ability (no cooldown, instant).

    Returns (ability_id, ability) for the ability that deals the most
    damage to the weakest enemy. Falls back to basic_attack.
    """
    if not enemies:
        return BASIC_ATTACK_ID, game_data.abilities.get(BASIC_ATTACK_ID)

    weakest = min(enemies, key=lambda e: e.current_hp)
    best_id = BASIC_ATTACK_ID
    best_ability = game_data.abilities.get(BASIC_ATTACK_ID)
    best_dmg = basic_attack_damage(actor, weakest)

    for aid in actor.ability_ids:
        if aid == BASIC_ATTACK_ID:
            continue
        ab = game_data.abilities.get(aid)
        if ab is None:
            continue
        if ab.category != AbilityCategory.OFFENSIVE:
            continue
        if ab.target not in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES):
            continue
        if ab.cooldown > 0 and actor.cooldowns.get(aid, 0) > 0:
            continue
        if ab.windup_turns > 0:
            continue
        dmg = ability_damage(actor, weakest, ab)
        if dmg > best_dmg:
            best_dmg = dmg
            best_id = aid
            best_ability = ab

    return best_id, best_ability


def make_damage_fn(
    actor: CombatantState,
    enemies: list[CombatantState],
    game_data: GameData,
) -> Callable[[CombatantState, CombatantState], int]:
    """Create a damage estimation function using the actor's best ability."""
    _, best_ab = best_attack_ability(actor, enemies, game_data)
    if best_ab is None:
        return basic_attack_damage

    def _damage_fn(attacker: CombatantState, target: CombatantState) -> int:
        return ability_damage(attacker, target, best_ab)

    return _damage_fn


class HeuristicRolloutPolicy:
    """Fast survive-then-kill policy for rollout evaluation.

    Priority:
      1. End battle if can kill all and will survive the round
      2. Heal if projected damage >= HP and potion available
      3. Survive (default)
    """

    name: str = "heuristic_rollout"

    def __init__(self, game_data: GameData):
        self.game_data = game_data

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision:
        ctx = RuleContext(
            state=state,
            actor=actor,
            legal=legal,
            game_data=self.game_data,
        )

        enemies = state.living_enemies
        if not enemies:
            return _survive(actor)

        bonus = _bonus_actions(actor, enemies)
        dmg_fn = make_damage_fn(actor, enemies, self.game_data)
        best_ability_id, _ = best_attack_ability(actor, enemies, self.game_data)

        # Rule 1: end battle if possible and safe (passive-aware)
        incoming = projected_incoming_damage(ctx)
        if incoming < actor.current_hp:
            ap_needed = minimum_ap_to_kill_all_passive(
                ctx, self.game_data, damage_fn=dmg_fn,
            )
            if ap_needed is not None:
                return _build_end_battle(
                    actor, enemies, ap_needed, bonus, best_ability_id, dmg_fn,
                )

        # Rule 2: heal if about to die
        if incoming >= actor.current_hp:
            if POTION_ITEM_ID in legal.available_consumable_ids:
                return _build_heal(actor, bonus)

        # Rule 3: continue frenzy chain — berserker's damage multiplier
        # persists across rounds as long as you keep attacking. Breaking
        # the chain (surviving) resets it. Once attacking, always attack.
        if actor.frenzy_chain > 0:
            ap = actor.action_points
            strongest = max(enemies, key=lambda e: e.current_hp)
            if ap > 0:
                return _build_ap_dump(
                    actor, strongest, enemies, ap,
                    bonus, best_ability_id,
                )
            return PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=actor.id,
                    ability_id=best_ability_id,
                    target_ids=[strongest.id],
                ),
                bonus_actions=bonus,
            )

        # Rule 4: consume insight stacks — onmyoji banked stacks via
        # survive; using them amplifies the next ability by 40% per stack.
        if actor.insight_stacks > 0:
            strongest = max(enemies, key=lambda e: e.current_hp)
            ap = actor.action_points
            if ap > 0:
                return _build_ap_dump(
                    actor, strongest, enemies, ap,
                    bonus, best_ability_id,
                )
            return PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=actor.id,
                    ability_id=best_ability_id,
                    target_ids=[strongest.id],
                ),
                bonus_actions=bonus,
            )

        # Rule 5: survive
        return _survive(actor, bonus)


def _survive(
    actor: CombatantState,
    bonus: list[CombatAction] | None = None,
) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
        bonus_actions=bonus or [],
    )


def _bonus_actions(
    actor: CombatantState,
    enemies: list[CombatantState],
) -> list[CombatAction]:
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


def _build_end_battle(
    actor: CombatantState,
    enemies: list[CombatantState],
    cheat_n: int,
    bonus: list[CombatAction],
    ability_id: str,
    dmg_fn: Callable[[CombatantState, CombatantState], int],
) -> PlayerTurnDecision:
    """Build a kill-all decision using the best ability with sweep targeting."""
    target = max(enemies, key=lambda e: e.current_hp)

    remaining_hp = {e.id: e.current_hp for e in enemies}
    total_attacks = 1 + cheat_n
    targets: list[str] = [target.id]
    dmg = max(1, dmg_fn(actor, target))
    remaining_hp[target.id] -= dmg

    for _ in range(total_attacks - 1):
        alive = [e for e in enemies if remaining_hp.get(e.id, 0) > 0]
        if not alive:
            targets.append(enemies[0].id)
            continue
        weakest = min(alive, key=lambda e: remaining_hp[e.id])
        targets.append(weakest.id)
        d = max(1, dmg_fn(actor, weakest))
        remaining_hp[weakest.id] -= d

    primary = CombatAction(
        actor_id=actor.id,
        ability_id=ability_id,
        target_ids=[targets[0]],
    )
    extras = [
        CombatAction(
            actor_id=actor.id,
            ability_id=ability_id,
            target_ids=[targets[i]],
        )
        for i in range(1, len(targets))
    ]

    cs = CheatSurviveChoice.CHEAT if cheat_n > 0 else CheatSurviveChoice.NORMAL
    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=cs,
        cheat_actions=cheat_n,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=bonus,
    )


def _build_ap_dump(
    actor: CombatantState,
    primary_target: CombatantState,
    enemies: list[CombatantState],
    ap: int,
    bonus: list[CombatAction],
    ability_id: str,
) -> PlayerTurnDecision:
    """CHEAT with all AP on strongest enemy. Sweep extras weakest-first."""
    primary = CombatAction(
        actor_id=actor.id,
        ability_id=ability_id,
        target_ids=[primary_target.id],
    )
    remaining_hp = {e.id: e.current_hp for e in enemies}
    extras: list[CombatAction] = []
    for _ in range(ap):
        alive = [e for e in enemies if remaining_hp.get(e.id, 0) > 0]
        if not alive:
            target = primary_target
        else:
            target = min(alive, key=lambda e: remaining_hp[e.id])
        extras.append(CombatAction(
            actor_id=actor.id,
            ability_id=ability_id,
            target_ids=[target.id],
        ))
        remaining_hp[target.id] = remaining_hp.get(target.id, 0) - 1

    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.CHEAT,
        cheat_actions=ap,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=bonus,
    )


def _build_heal(
    actor: CombatantState,
    bonus: list[CombatAction],
) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=CombatAction(
            actor_id=actor.id,
            ability_id="use_item",
            item_id=POTION_ITEM_ID,
            target_ids=[actor.id],
        ),
        bonus_actions=bonus,
    )
