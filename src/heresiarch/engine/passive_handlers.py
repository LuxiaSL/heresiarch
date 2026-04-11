"""Passive trigger resolution: data-driven dispatch for triggered abilities.

Each handler processes passives of a given TriggerCondition using only the
fields on AbilityEffect. No ability-ID checks. New passives that use existing
effect fields need ZERO code changes.

Handlers are pure functions that mutate CombatState/CombatantState in place
and append to the event log. They receive a PassiveContext with everything
they need.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from heresiarch.engine.formulas import (
    MAX_ACTION_POINT_BANK,
    VENGEANCE_DEFAULT_DURATION,
    calculate_physical_damage,
    calculate_magical_damage,
    calculate_thorns_percent,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityEffect,
    DamageQuality,
    TriggerCondition,
)
from heresiarch.engine.models.combat_state import (
    CombatantState,
    CombatEvent,
    CombatEventType,
    CombatState,
    StatusEffect,
)
from heresiarch.engine.models.stats import StatType

if TYPE_CHECKING:
    pass


@dataclass
class PassiveContext:
    """Context for passive trigger resolution.

    Built by CombatEngine before dispatching. Not serialized.
    """

    state: CombatState
    owner: CombatantState
    trigger_source: CombatantState | None = None
    damage_dealt: int = 0
    item_leech_percent: float = 0.0  # owner's total item leech


PassiveHandler = Callable[[Ability, PassiveContext], None]


# ---------------------------------------------------------------------------
# ON_HIT_RECEIVED: counter-attack, siphon, thorns
# ---------------------------------------------------------------------------


def handle_on_hit_received(passive: Ability, ctx: PassiveContext) -> None:
    """Resolve ON_HIT_RECEIVED effects generically by AbilityEffect fields.

    - base_damage/scaling → counter-attack damage to trigger_source
    - stat_buff → stacking buff on owner (siphon-like)
    - reflect_percent → thorns damage to trigger_source
    """
    if ctx.trigger_source is None:
        return

    for effect in passive.effects:
        # Counter-attack: any ON_HIT_RECEIVED passive with damage fields
        if (effect.base_damage > 0 or effect.scaling_coefficient > 0) and ctx.trigger_source.is_alive:
            if effect.stat_scaling == StatType.STR or effect.stat_scaling is None:
                ret_damage = calculate_physical_damage(
                    ability_base=effect.base_damage,
                    ability_coefficient=effect.scaling_coefficient,
                    attacker_str=ctx.owner.effective_stats.STR,
                    target_def=ctx.trigger_source.effective_stats.DEF,
                )
            elif effect.stat_scaling == StatType.MAG:
                ret_damage = calculate_magical_damage(
                    ability_base=effect.base_damage,
                    ability_coefficient=effect.scaling_coefficient,
                    attacker_mag=ctx.owner.effective_stats.MAG,
                )
            else:
                ret_damage = max(1, effect.base_damage)

            if ret_damage > 0:
                ctx.trigger_source.current_hp = max(0, ctx.trigger_source.current_hp - ret_damage)
                ctx.state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.RETALIATE_TRIGGERED,
                        round_number=ctx.state.round_number,
                        actor_id=ctx.owner.id,
                        target_id=ctx.trigger_source.id,
                        ability_id=passive.id,
                        value=ret_damage,
                    )
                )
                # Leech on counter-attack
                if ctx.item_leech_percent > 0:
                    heal = max(1, int(ret_damage * ctx.item_leech_percent))
                    ctx.owner.current_hp = min(ctx.owner.max_hp, ctx.owner.current_hp + heal)
                    ctx.state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.HEALING,
                            round_number=ctx.state.round_number,
                            actor_id=ctx.owner.id,
                            target_id=ctx.owner.id,
                            value=heal,
                            details={"source": "leech"},
                        )
                    )
                if ctx.trigger_source.current_hp <= 0:
                    ctx.trigger_source.is_alive = False
                    ctx.state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.DEATH,
                            round_number=ctx.state.round_number,
                            target_id=ctx.trigger_source.id,
                        )
                    )

        # Stacking buff: any ON_HIT_RECEIVED passive with stat_buff
        if effect.stat_buff:
            siphon_status = StatusEffect(
                id=f"{passive.id}_stack_{ctx.state.round_number}_{id(effect)}",
                name=passive.name,
                stat_modifiers=dict(effect.stat_buff),
                rounds_remaining=999,  # Permanent for the fight
                source_id=ctx.owner.id,
            )
            ctx.owner.active_statuses.append(siphon_status)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.PASSIVE_TRIGGERED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.owner.id,
                    target_id=ctx.owner.id,
                    ability_id=passive.id,
                    details={"buffs": effect.stat_buff},
                )
            )

        # Thorns: reflect % of damage taken back to attacker
        if effect.reflect_percent > 0 and ctx.trigger_source.is_alive:
            effective_pct = calculate_thorns_percent(effect.reflect_percent, ctx.owner.level)
            reflected = max(1, int(ctx.damage_dealt * effective_pct))
            ctx.trigger_source.current_hp = max(0, ctx.trigger_source.current_hp - reflected)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.THORNS_TRIGGERED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.owner.id,
                    target_id=ctx.trigger_source.id,
                    value=reflected,
                    details={"reflect_percent": round(effective_pct, 2)},
                )
            )
            if ctx.trigger_source.current_hp <= 0:
                ctx.trigger_source.is_alive = False
                ctx.state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.DEATH,
                        round_number=ctx.state.round_number,
                        target_id=ctx.trigger_source.id,
                    )
                )


# ---------------------------------------------------------------------------
# ON_KILL: AP refund, stat buffs
# ---------------------------------------------------------------------------


def handle_on_kill(passive: Ability, ctx: PassiveContext) -> None:
    """Resolve ON_KILL effects: AP refund, stat buffs."""
    for effect in passive.effects:
        if effect.ap_refund > 0:
            ctx.owner.action_points = min(
                ctx.owner.action_points + effect.ap_refund,
                MAX_ACTION_POINT_BANK,
            )
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.PASSIVE_TRIGGERED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.owner.id,
                    target_id=ctx.trigger_source.id if ctx.trigger_source else "",
                    ability_id=passive.id,
                    details={"ap_refunded": effect.ap_refund},
                )
            )

        if effect.stat_buff:
            status = StatusEffect(
                id=f"{passive.id}_{ctx.owner.id}_{ctx.state.round_number}",
                name=passive.name,
                stat_modifiers=dict(effect.stat_buff),
                rounds_remaining=effect.duration_rounds + 1 if effect.duration_rounds > 0 else VENGEANCE_DEFAULT_DURATION,
                source_id=ctx.owner.id,
            )
            ctx.owner.active_statuses.append(status)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.PASSIVE_TRIGGERED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.owner.id,
                    target_id=ctx.trigger_source.id if ctx.trigger_source else "",
                    ability_id=passive.id,
                    details={"buffs": effect.stat_buff},
                )
            )


# ---------------------------------------------------------------------------
# ON_ALLY_KO: buff surviving allies
# ---------------------------------------------------------------------------


def handle_on_ally_ko(passive: Ability, ctx: PassiveContext) -> None:
    """Resolve ON_ALLY_KO effects: stat buffs on the owner."""
    for effect in passive.effects:
        if effect.stat_buff:
            status = StatusEffect(
                id=f"{passive.id}_{ctx.owner.id}_{ctx.state.round_number}",
                name=passive.name,
                stat_modifiers=dict(effect.stat_buff),
                rounds_remaining=effect.duration_rounds + 1 if effect.duration_rounds > 0 else VENGEANCE_DEFAULT_DURATION,
                source_id=ctx.owner.id,
            )
            ctx.owner.active_statuses.append(status)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.PASSIVE_TRIGGERED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.owner.id,
                    target_id=ctx.trigger_source.id if ctx.trigger_source else "",
                    ability_id=passive.id,
                    details={"buffs": effect.stat_buff},
                )
            )


# ---------------------------------------------------------------------------
# RES_GATE_PASSED: reflect debuff back to caster
# ---------------------------------------------------------------------------


def handle_res_gate_passed(passive: Ability, ctx: PassiveContext) -> None:
    """Resolve RES_GATE_PASSED: create a disrupt status on the caster."""
    if ctx.trigger_source is None or not ctx.trigger_source.is_alive:
        return

    for effect in passive.effects:
        duration = effect.duration_rounds if effect.duration_rounds > 0 else 2
        disrupt_status = StatusEffect(
            id=f"{passive.id}_disrupt_{ctx.state.round_number}",
            name=f"{passive.name} Disrupt",
            rounds_remaining=duration,
            source_id=ctx.owner.id,
        )
        ctx.trigger_source.active_statuses.append(disrupt_status)
        ctx.state.log.append(
            CombatEvent(
                event_type=CombatEventType.PASSIVE_TRIGGERED,
                round_number=ctx.state.round_number,
                actor_id=ctx.owner.id,
                target_id=ctx.trigger_source.id,
                ability_id=passive.id,
                details={"reflected": effect.quality.value if effect.quality else "DISRUPT"},
            )
        )


# ---------------------------------------------------------------------------
# ON_CONSECUTIVE_ATTACK: frenzy floor preservation (round boundary)
# ---------------------------------------------------------------------------


def handle_consecutive_attack_boundary(passive: Ability, ctx: PassiveContext) -> None:
    """Round boundary: reset frenzy chain on non-damage rounds (level is preserved)."""
    if not ctx.owner.dealt_damage_this_round and ctx.owner.frenzy_chain > 0:
        ctx.owner.frenzy_chain = 0


# ---------------------------------------------------------------------------
# ON_NON_DAMAGE_ROUND: insight stack generation (round boundary)
# ---------------------------------------------------------------------------


def handle_non_damage_round_boundary(passive: Ability, ctx: PassiveContext) -> None:
    """Round boundary: gain an insight stack on non-damage rounds."""
    if not ctx.owner.dealt_damage_this_round:
        ctx.owner.insight_stacks += 1
        ctx.state.log.append(
            CombatEvent(
                event_type=CombatEventType.PASSIVE_TRIGGERED,
                round_number=ctx.state.round_number,
                actor_id=ctx.owner.id,
                target_id=ctx.owner.id,
                ability_id=passive.id,
                details={"insight_stacks": ctx.owner.insight_stacks},
            )
        )


# ---------------------------------------------------------------------------
# HP_BELOW_THRESHOLD: toggle stat buffs
# ---------------------------------------------------------------------------


def handle_hp_threshold(passive: Ability, ctx: PassiveContext) -> None:
    """Toggle conditional stat buffs based on HP threshold."""
    threshold = passive.trigger_threshold or 0.3
    hp_ratio = ctx.owner.current_hp / max(ctx.owner.max_hp, 1)
    status_id = f"passive_{passive.id}"
    has_buff = any(s.id == status_id for s in ctx.owner.active_statuses)

    if hp_ratio < threshold and not has_buff:
        for effect in passive.effects:
            if effect.stat_buff:
                status = StatusEffect(
                    id=status_id,
                    name=passive.name,
                    stat_modifiers=dict(effect.stat_buff),
                    rounds_remaining=999,
                    source_id=ctx.owner.id,
                )
                ctx.owner.active_statuses.append(status)
                ctx.state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.PASSIVE_TRIGGERED,
                        round_number=ctx.state.round_number,
                        actor_id=ctx.owner.id,
                        target_id=ctx.owner.id,
                        ability_id=passive.id,
                    )
                )
    elif hp_ratio >= threshold and has_buff:
        ctx.owner.active_statuses = [
            s for s in ctx.owner.active_statuses if s.id != status_id
        ]


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

PASSIVE_DISPATCH: dict[TriggerCondition, PassiveHandler] = {
    TriggerCondition.ON_HIT_RECEIVED: handle_on_hit_received,
    TriggerCondition.ON_KILL: handle_on_kill,
    TriggerCondition.ON_ALLY_KO: handle_on_ally_ko,
    TriggerCondition.RES_GATE_PASSED: handle_res_gate_passed,
    TriggerCondition.ON_CONSECUTIVE_ATTACK: handle_consecutive_attack_boundary,
    TriggerCondition.ON_NON_DAMAGE_ROUND: handle_non_damage_round_boundary,
    TriggerCondition.HP_BELOW_THRESHOLD: handle_hp_threshold,
}
