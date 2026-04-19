"""Effect pipeline: action resolution and 11-phase effect application.

Extracted from CombatEngine as a mixin. Must be mixed into a class that provides:
- abilities, items, rng attributes (registries)
- _get_passive, _get_all_passives, _find_survive_lethal_passive (passive lookups)
- _resolve_item_action, _spawn_enemies (action routing)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import (
    DEF_REDUCTION_RATIO,
    INSIGHT_MULTIPLIER_PER_STACK,
    MARK_DAMAGE_BONUS,
    MAX_ACTION_POINT_BANK,
    apply_survive_reduction,
    calculate_communion_multiplier,
    calculate_frenzy_multiplier,
    calculate_insight_multiplier,
    calculate_magical_damage,
    calculate_physical_damage,
    check_res_gate,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    DamageQuality,
    TargetType,
    TriggerCondition,
)
from heresiarch.engine.models.combat_state import (
    CombatAction,
    CombatantState,
    CombatEvent,
    CombatEventType,
    CombatState,
    StatusEffect,
)
from heresiarch.engine.models.stats import StatType
from heresiarch.engine.passive_handlers import PASSIVE_DISPATCH, PassiveContext

if TYPE_CHECKING:
    pass


@dataclass
class EffectContext:
    """Mutable context threaded through effect resolution phases.

    Internal to CombatEngine — not serialized, not part of game state.
    Lives only for the duration of a single _apply_effect call.
    """

    state: CombatState
    actor: CombatantState
    target: CombatantState
    effect: AbilityEffect
    ability: Ability
    insight_multiplier: float
    damage: int = 0
    pre_def_damage: int = 0  # damage before target DEF reduction (for thorns)


class EffectPipelineMixin:
    """Mixin providing action resolution and the 11-phase effect pipeline."""

    # --- Action Resolution ---

    def _resolve_action(
        self,
        state: CombatState,
        actor_id: str,
        action: CombatAction,
        is_speed_bonus: bool = False,
    ) -> CombatState:
        """Core action resolution. Routes to damage calc, applies effects."""
        # Item use is a distinct action type — route to dedicated handler
        if action.item_id is not None:
            return self._resolve_item_action(state, actor_id, action)

        actor = state.get_combatant(actor_id)
        if actor is None or not actor.is_alive:
            return state

        ability = self.abilities.get(action.ability_id)
        if ability is None:
            return state

        # Check cooldown
        if actor.cooldowns.get(action.ability_id, 0) > 0:
            return state

        # Set cooldown
        if ability.cooldown > 0:
            actor.cooldowns[action.ability_id] = ability.cooldown

        # Track legacy frenzy stacks (used by Surge abilities for stack counting)
        if actor.is_player:
            actor.frenzy_stacks += 1

        # Resolve effective targets BEFORE logging so the declaration reflects
        # the actual landing targets (e.g. a heal on a dead ally redirects to
        # a living one).
        effective_target_ids = list(action.target_ids)

        # Determine if this is an ally-targeting or enemy-targeting ability
        targets_allies = ability.target in (TargetType.SINGLE_ALLY, TargetType.ALL_ALLIES)

        # For ALL_ENEMIES, fill target list with all living enemies
        if ability.target == TargetType.ALL_ENEMIES and not effective_target_ids:
            if actor.is_player:
                effective_target_ids = [e.id for e in state.living_enemies]
            else:
                effective_target_ids = [p.id for p in state.living_players]

        # For ALL_ALLIES, fill target list with all living allies
        if ability.target == TargetType.ALL_ALLIES and not effective_target_ids:
            if actor.is_player:
                effective_target_ids = [p.id for p in state.living_players]
            else:
                effective_target_ids = [e.id for e in state.living_enemies]

        # Auto-retarget dead targets to next living combatant on the correct side
        if ability.target != TargetType.SELF:
            retargeted: list[str] = []
            for tid in effective_target_ids:
                target = state.get_combatant(tid)
                if target is not None and target.is_alive:
                    retargeted.append(tid)
                else:
                    # Find a replacement from the correct side
                    if targets_allies:
                        # Ally-targeting: same side as actor
                        if actor.is_player:
                            replacements = [p.id for p in state.living_players if p.id not in retargeted]
                        else:
                            replacements = [e.id for e in state.living_enemies if e.id not in retargeted]
                    else:
                        # Enemy-targeting: opposite side from actor
                        if actor.is_player:
                            replacements = [e.id for e in state.living_enemies if e.id not in retargeted]
                        else:
                            replacements = [p.id for p in state.living_players if p.id not in retargeted]
                    if replacements:
                        retargeted.append(replacements[0])
            effective_target_ids = retargeted

        # Log with resolved targets. SELF abilities log an empty list so the
        # TUI renders "Actor uses Ability" without an "on X" suffix.
        logged_targets = [] if ability.target == TargetType.SELF else list(effective_target_ids)
        state.log.append(
            CombatEvent(
                event_type=CombatEventType.BONUS_ACTION if is_speed_bonus else CombatEventType.ACTION_DECLARED,
                round_number=state.round_number,
                actor_id=actor_id,
                ability_id=action.ability_id,
                details={"targets": logged_targets, "speed_bonus": is_speed_bonus},
            )
        )

        # SELF default applied after logging so display stays "Actor uses Ability"
        if ability.target == TargetType.SELF and not effective_target_ids:
            effective_target_ids = [actor_id]

        # Insight: amplified abilities consume stacks, others grant stacks
        insight_multiplier = 1.0
        insight_passive = self._get_passive(actor, TriggerCondition.ON_NON_DAMAGE_ACTION, state)
        if insight_passive:
            if ability.insight_amplified and actor.insight_stacks > 0:
                insight_multiplier = calculate_insight_multiplier(actor.insight_stacks)
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.INSIGHT_CONSUMED,
                        round_number=state.round_number,
                        actor_id=actor.id,
                        value=actor.insight_stacks,
                        details={"multiplier": round(insight_multiplier, 2)},
                    )
                )
                actor.insight_stacks -= 1

        for effect in ability.effects:
            if state.is_finished:
                break

            # applies_to_self: redirect this effect to the actor
            if effect.applies_to_self:
                if actor.is_alive:
                    state = self._apply_effect(
                        state, actor, actor, effect, ability,
                        insight_multiplier=insight_multiplier,
                    )
                continue

            for target_id in effective_target_ids:
                if state.is_finished:
                    break

                target = state.get_combatant(target_id)
                if target is None or not target.is_alive:
                    continue

                state = self._apply_effect(
                    state, actor, target, effect, ability,
                    insight_multiplier=insight_multiplier,
                )

        # Self-damage effects
        for effect in ability.effects:
            if effect.self_damage_ratio > 0 and actor.is_alive:
                self_damage = int(actor.max_hp * effect.self_damage_ratio)
                actor.current_hp = max(0, actor.current_hp - self_damage)
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.DAMAGE_DEALT,
                        round_number=state.round_number,
                        actor_id=actor_id,
                        target_id=actor_id,
                        ability_id=action.ability_id,
                        value=self_damage,
                        details={"self_damage": True},
                    )
                )
                if actor.current_hp <= 0:
                    actor.is_alive = False
                    state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.DEATH,
                            round_number=state.round_number,
                            target_id=actor_id,
                        )
                    )

        # Post-action insight: non-amplified abilities grant stacks
        if actor.is_alive and insight_passive and not ability.insight_amplified:
            self._evaluate_post_action_passives(state, actor)

        return state

    def _evaluate_post_action_passives(
        self, state: CombatState, combatant: CombatantState,
    ) -> None:
        """Dispatch post-action passives (insight) via handler table."""
        trigger = TriggerCondition.ON_NON_DAMAGE_ACTION
        handler = PASSIVE_DISPATCH.get(trigger)
        if handler is None:
            return
        for passive in self._get_all_passives(combatant, trigger):
            pctx = PassiveContext(state=state, owner=combatant)
            handler(passive, pctx)

    # --- 11-Phase Effect Pipeline ---

    def _apply_effect(
        self,
        state: CombatState,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
        ability: Ability,
        insight_multiplier: float = 1.0,
    ) -> CombatState:
        """Apply a single ability effect to a target via phased pipeline."""
        ctx = EffectContext(
            state=state,
            actor=actor,
            target=target,
            effect=effect,
            ability=ability,
            insight_multiplier=insight_multiplier,
        )

        self._phase_damage_calc(ctx)
        self._phase_damage_modify(ctx)
        self._phase_damage_redirect(ctx)
        self._phase_damage_reduce(ctx)
        self._phase_damage_apply(ctx)
        self._phase_split_check(ctx)
        self._phase_post_damage(ctx)
        self._phase_death_check(ctx)
        self._phase_secondary(ctx)
        self._phase_buff_apply(ctx)
        self._phase_utility(ctx)

        return ctx.state

    # --- Effect Pipeline Phases ---

    def _phase_damage_calc(self, ctx: EffectContext) -> None:
        """Phase 1: Calculate raw damage from ability effect."""
        if ctx.effect.base_damage > 0 or ctx.effect.scaling_coefficient > 0:
            ctx.damage = self._calculate_damage(
                ctx.actor, ctx.target, ctx.effect,
            )
            ctx.pre_def_damage = self._calculate_pre_def_damage(
                ctx.actor, ctx.effect,
            )

    def _phase_damage_modify(self, ctx: EffectContext) -> None:
        """Phase 2: Apply damage multipliers (insight, frenzy, surge, chain, mark).

        Attacker-side multipliers are mirrored to pre_def_damage so thorns
        can reflect the full pre-defense hit strength.
        """
        if ctx.damage <= 0:
            return

        # Insight damage amplification
        if ctx.insight_multiplier > 1.0:
            ctx.damage = int(ctx.damage * ctx.insight_multiplier)
            ctx.pre_def_damage = int(ctx.pre_def_damage * ctx.insight_multiplier)

        # Communion: missing-HP scaled amplification for magical abilities (Sacrist innate)
        communion_passive = self._get_passive(
            ctx.actor, TriggerCondition.ON_DAMAGE_MODIFY, ctx.state,
        )
        if communion_passive:
            for pe in communion_passive.effects:
                if pe.missing_hp_damage_bonus <= 0.0:
                    continue
                # Stat filter: if the passive effect specifies stat_scaling, only
                # amplify ability effects with matching stat_scaling.
                if pe.stat_scaling is not None and ctx.effect.stat_scaling != pe.stat_scaling:
                    continue
                multiplier = calculate_communion_multiplier(
                    ctx.actor.current_hp, ctx.actor.max_hp, max_bonus=pe.missing_hp_damage_bonus,
                )
                if multiplier > 1.0:
                    ctx.damage = int(ctx.damage * multiplier)
                    ctx.pre_def_damage = int(ctx.pre_def_damage * multiplier)

        # Frenzy damage amplification (ratchet: max of level vs chain exponential)
        frenzy_ability = self._get_passive(
            ctx.actor, TriggerCondition.ON_CONSECUTIVE_ATTACK, ctx.state,
        )
        if frenzy_ability:
            multiplier = max(ctx.actor.frenzy_level, calculate_frenzy_multiplier(ctx.actor.frenzy_chain))
            if multiplier > 1.0:
                ctx.damage = round(ctx.damage * multiplier)
                ctx.pre_def_damage = round(ctx.pre_def_damage * multiplier)

        # Surge stacking (Crescendo etc.)
        if ctx.effect.quality == DamageQuality.SURGE and ctx.effect.surge_stack_bonus > 0:
            stacks = ctx.actor.surge_stacks.get(ctx.ability.id, 0)
            multiplier = 1.0 + ctx.effect.surge_stack_bonus * stacks
            ctx.damage = int(ctx.damage * multiplier)
            ctx.pre_def_damage = int(ctx.pre_def_damage * multiplier)
            ctx.actor.surge_stacks[ctx.ability.id] = stacks + 1

        # Chain damage reduction
        if ctx.effect.quality == DamageQuality.CHAIN:
            ctx.damage = int(ctx.damage * ctx.effect.chain_damage_ratio)
            ctx.pre_def_damage = int(ctx.pre_def_damage * ctx.effect.chain_damage_ratio)

        # Mark bonus damage against marked targets
        if ctx.target.is_marked:
            ctx.damage = int(ctx.damage * MARK_DAMAGE_BONUS)
            ctx.pre_def_damage = int(ctx.pre_def_damage * MARK_DAMAGE_BONUS)

    def _phase_damage_redirect(self, ctx: EffectContext) -> None:
        """Phase 3: Redirect effects (reserved for future use)."""

    def _phase_damage_reduce(self, ctx: EffectContext) -> None:
        """Phase 4: Survive damage reduction + invulnerability."""
        if ctx.damage <= 0:
            return
        # Invulnerability: all damage reduced to 0
        if ctx.target.invulnerable_turns > 0:
            ctx.damage = 0
            return
        ctx.damage = apply_survive_reduction(ctx.damage, ctx.target.is_surviving)

    def _phase_damage_apply(self, ctx: EffectContext) -> None:
        """Phase 5: Apply HP loss, emit DAMAGE_DEALT event, leech healing."""
        if ctx.damage <= 0:
            return

        ctx.actor.dealt_damage_this_round = True
        ctx.target.current_hp = max(0, ctx.target.current_hp - ctx.damage)
        ctx.state.log.append(
            CombatEvent(
                event_type=CombatEventType.DAMAGE_DEALT,
                round_number=ctx.state.round_number,
                actor_id=ctx.actor.id,
                target_id=ctx.target.id,
                ability_id=ctx.ability.id,
                value=ctx.damage,
            )
        )

        # Frenzy: ratchet level up and advance chain after damage lands
        frenzy_ability = self._get_passive(
            ctx.actor, TriggerCondition.ON_CONSECUTIVE_ATTACK, ctx.state,
        )
        if frenzy_ability:
            chain_mult = calculate_frenzy_multiplier(ctx.actor.frenzy_chain)
            ctx.actor.frenzy_level = max(ctx.actor.frenzy_level, chain_mult)
            ctx.actor.frenzy_chain += 1
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.FRENZY_STACK,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    value=ctx.actor.frenzy_chain,
                    details={
                        "level": round(ctx.actor.frenzy_level, 3),
                        "chain": ctx.actor.frenzy_chain,
                    },
                )
            )

        # Leech healing — ability leech applies universally, item leech is type-split
        item_leech = self._get_item_leech_for_effect(ctx.actor, ctx.effect)
        total_leech = ctx.effect.leech_percent + item_leech
        if total_leech > 0:
            heal = max(1, int(ctx.damage * total_leech))
            ctx.actor.current_hp = min(ctx.actor.max_hp, ctx.actor.current_hp + heal)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.HEALING,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    target_id=ctx.actor.id,
                    value=heal,
                    details={"source": "leech"},
                )
            )

    def _phase_split_check(self, ctx: EffectContext) -> None:
        """Phase 5.5: Split passive — lethal damage triggers mitosis instead of death.

        When an enemy with a split passive (e.g. mitosis) takes lethal damage,
        spawn replacement enemies and remove the original. Zeroes ctx.damage so
        Phase 7 (death_check) is skipped entirely — no DEATH event, no ON_KILL.
        """
        if ctx.damage <= 0 or ctx.target.current_hp > 0 or ctx.target.is_player:
            return

        split_ability = self._find_split_passive(ctx.target)
        if split_ability is None:
            return

        # Find the effect carrying the split template list
        split_templates: list[str] = []
        for effect in split_ability.effects:
            if effect.split_into_templates:
                split_templates = effect.split_into_templates
                break

        if not split_templates:
            return

        # Spawn each template entry (duplicates in the list spawn multiple copies)
        for template_id in split_templates:
            self._spawn_enemies(
                ctx.state,
                template_id=template_id,
                count=1,
                level=ctx.target.level,
                event_type=CombatEventType.ENEMY_SPAWNED,
                summoner_id=ctx.target.id,
            )

        # Remove original from combat
        ctx.target.is_alive = False
        ctx.state.log.append(
            CombatEvent(
                event_type=CombatEventType.PASSIVE_TRIGGERED,
                round_number=ctx.state.round_number,
                actor_id=ctx.target.id,
                target_id=ctx.target.id,
                ability_id=split_ability.id,
                details={"split_into": split_templates},
            )
        )

        # Zero damage so Phase 7 death pipeline is skipped entirely
        ctx.damage = 0

    def _phase_post_damage(self, ctx: EffectContext) -> None:
        """Phase 6: Post-damage reactive passives via dispatch table."""
        if ctx.damage <= 0 or not ctx.target.is_alive:
            return

        handler = PASSIVE_DISPATCH.get(TriggerCondition.ON_HIT_RECEIVED)
        if handler is None:
            return

        for hit_passive in self._get_all_passives(ctx.target, TriggerCondition.ON_HIT_RECEIVED):
            passive_ctx = PassiveContext(
                state=ctx.state,
                owner=ctx.target,
                trigger_source=ctx.actor,
                damage_dealt=ctx.damage,
                pre_def_damage=ctx.pre_def_damage,
                item_phys_leech_percent=ctx.target.phys_leech_percent,
                item_mag_leech_percent=ctx.target.mag_leech_percent,
            )
            handler(hit_passive, passive_ctx)

    def _phase_death_check(self, ctx: EffectContext) -> None:
        """Phase 7: Endure, death, on-kill/on-ally-KO triggers."""
        if ctx.damage <= 0:
            return
        if ctx.target.current_hp > 0:
            return

        # Check for survive_lethal passive (e.g., Endure: survive at 1 HP, once per fight)
        if not ctx.target.has_endured:
            endure_ability = self._find_survive_lethal_passive(ctx.target)
            if endure_ability is not None:
                ctx.target.current_hp = 1
                ctx.target.has_endured = True
                ctx.state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.PASSIVE_TRIGGERED,
                        round_number=ctx.state.round_number,
                        actor_id=ctx.target.id,
                        target_id=ctx.target.id,
                        ability_id=endure_ability.id,
                        details={"survived_at": 1},
                    )
                )
                return

        ctx.target.is_alive = False
        ctx.state.log.append(
            CombatEvent(
                event_type=CombatEventType.DEATH,
                round_number=ctx.state.round_number,
                target_id=ctx.target.id,
            )
        )

        # ON_KILL passives (momentum AP refund, etc.)
        if ctx.actor.is_alive:
            on_kill_handler = PASSIVE_DISPATCH.get(TriggerCondition.ON_KILL)
            if on_kill_handler:
                for kill_passive in self._get_all_passives(ctx.actor, TriggerCondition.ON_KILL):
                    kill_ctx = PassiveContext(
                        state=ctx.state,
                        owner=ctx.actor,
                        trigger_source=ctx.target,
                    )
                    on_kill_handler(kill_passive, kill_ctx)

        # ON_ALLY_KO passives (vengeance buffs, etc.)
        if ctx.target.is_player:
            on_ally_ko_handler = PASSIVE_DISPATCH.get(TriggerCondition.ON_ALLY_KO)
            if on_ally_ko_handler:
                for ally in ctx.state.living_players:
                    if ally.id == ctx.target.id:
                        continue
                    for ally_passive in self._get_all_passives(ally, TriggerCondition.ON_ALLY_KO):
                        ally_ctx = PassiveContext(
                            state=ctx.state,
                            owner=ally,
                            trigger_source=ctx.target,
                        )
                        on_ally_ko_handler(ally_passive, ally_ctx)

    def _phase_secondary(self, ctx: EffectContext) -> None:
        """Phase 8: DOT/shatter/disrupt (RES-gated secondary effects)."""
        if ctx.effect.quality in (DamageQuality.DOT, DamageQuality.SHATTER, DamageQuality.DISRUPT):
            if ctx.effect.duration_rounds > 0 and ctx.target.is_alive:
                ctx.state = self._apply_secondary_effect(
                    ctx.state, ctx.actor, ctx.target, ctx.effect, ctx.ability,
                )

    def _phase_buff_apply(self, ctx: EffectContext) -> None:
        """Phase 9: DEF buff and general stat buff application."""
        # DEF buff (Brace Strike, Barrier)
        if ctx.effect.def_buff != 0 and ctx.target.is_alive:
            status = StatusEffect(
                id=f"{ctx.ability.id}_def_buff",
                name=f"{ctx.ability.name} DEF buff",
                stat_modifiers={"DEF": ctx.effect.def_buff},
                rounds_remaining=ctx.effect.duration_rounds if ctx.effect.duration_rounds > 0 else 1,
                source_id=ctx.actor.id,
            )
            ctx.target.active_statuses.append(status)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_APPLIED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    target_id=ctx.target.id,
                    details={"status": status.name},
                )
            )

        # General stat buff (Haste, Ward, Infuse, Vengeance, etc.)
        if ctx.effect.stat_buff and ctx.target.is_alive:
            # Insight amplification: boost magnitude of stat buffs
            buffed_modifiers = dict(ctx.effect.stat_buff)
            if ctx.insight_multiplier > 1.0:
                buffed_modifiers = {
                    k: int(v * ctx.insight_multiplier) for k, v in buffed_modifiers.items()
                }
            # Insight duration bonus: for duration-only effects, add rounds
            bonus_rounds = 0
            has_magnitude = bool(ctx.effect.base_damage or ctx.effect.stat_buff)
            if ctx.insight_multiplier > 1.0 and not has_magnitude:
                bonus_rounds = round((ctx.insight_multiplier - 1.0) / INSIGHT_MULTIPLIER_PER_STACK)
            status = StatusEffect(
                id=f"{ctx.ability.id}_stat_buff",
                name=f"{ctx.ability.name} buff",
                stat_modifiers=buffed_modifiers,
                rounds_remaining=(ctx.effect.duration_rounds + 1 if ctx.effect.duration_rounds > 0 else 2) + bonus_rounds,
                source_id=ctx.actor.id,
            )
            ctx.target.active_statuses.append(status)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_APPLIED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    target_id=ctx.target.id,
                    details={"status": status.name, "buffs": ctx.effect.stat_buff},
                )
            )

    def _phase_utility(self, ctx: EffectContext) -> None:
        """Phase 10: Gold steal, heal, mark, taunt, AP gain, surviving stance."""
        # AP gain (Survive etc.)
        if ctx.effect.ap_gain > 0:
            ctx.actor.action_points = min(
                ctx.actor.action_points + ctx.effect.ap_gain, MAX_ACTION_POINT_BANK
            )

        # Surviving stance (halves incoming damage for the round)
        if ctx.effect.grants_surviving:
            ctx.actor.is_surviving = True

        # Gold steal (Pilfer etc.)
        if (ctx.effect.gold_steal_flat > 0 or ctx.effect.gold_steal_per_level > 0) and ctx.target.is_alive:
            steal_amount = ctx.effect.gold_steal_flat + int(ctx.effect.gold_steal_per_level * ctx.actor.level)
            if steal_amount > 0:
                if ctx.actor.is_player:
                    ctx.state.gold_stolen_by_players += steal_amount
                else:
                    # Cap at remaining party gold so we never steal more than exists
                    steal_amount = min(steal_amount, ctx.state.party_gold)
                    ctx.state.gold_stolen_by_enemies += steal_amount
                    ctx.state.party_gold -= steal_amount
                if steal_amount > 0:
                    ctx.state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.GOLD_STOLEN,
                            round_number=ctx.state.round_number,
                            actor_id=ctx.actor.id,
                            target_id=ctx.target.id,
                            value=steal_amount,
                        )
                    )

        # Heal effect (Sacrifice, enemy heal, etc.) — heals the TARGET
        if ctx.effect.heal_percent > 0 and ctx.target.is_alive:
            heal = max(1, int(ctx.actor.max_hp * ctx.effect.heal_percent))
            ctx.target.current_hp = min(ctx.target.max_hp, ctx.target.current_hp + heal)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.HEALING,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    target_id=ctx.target.id,
                    value=heal,
                    details={"source": ctx.ability.id},
                )
            )

        # Invulnerability: grant turns of damage immunity (shell retreat etc.)
        if ctx.effect.grants_invulnerable > 0:
            ctx.actor.invulnerable_turns = ctx.effect.grants_invulnerable

        # Summon: spawn enemies mid-combat (boss summon abilities)
        if ctx.effect.summon_template_id and ctx.effect.summon_count > 0:
            summon_level = max(1, ctx.actor.level + ctx.effect.summon_level_offset)
            self._spawn_enemies(
                ctx.state,
                template_id=ctx.effect.summon_template_id,
                count=ctx.effect.summon_count,
                level=summon_level,
                event_type=CombatEventType.ENEMY_SUMMONED,
                summoner_id=ctx.actor.id,
            )

        # Mark — apply status that flags target for bonus damage
        if ctx.effect.applies_mark and ctx.target.is_alive:
            ctx.target.is_marked = True
            mark_duration = ctx.effect.duration_rounds if ctx.effect.duration_rounds > 0 else 3
            mark_status = StatusEffect(
                id="mark_active",
                name="Marked",
                rounds_remaining=mark_duration + 1,
                source_id=ctx.actor.id,
                grants_mark=True,
            )
            ctx.target.active_statuses = [
                s for s in ctx.target.active_statuses if not s.grants_mark
            ]
            ctx.target.active_statuses.append(mark_status)

        # Taunt — apply taunted status to target, forcing them to attack actor
        if ctx.effect.applies_taunt and ctx.actor.is_alive and ctx.target.is_alive:
            taunt_duration = ctx.effect.duration_rounds if ctx.effect.duration_rounds > 0 else 1
            taunt_status = StatusEffect(
                id="taunted",
                name="Taunted",
                rounds_remaining=taunt_duration + 1,  # +1: tick at round start
                source_id=ctx.actor.id,
                grants_taunted=True,
            )
            # Refresh from same source, keep others (stacking from different sources)
            ctx.target.active_statuses = [
                s for s in ctx.target.active_statuses
                if not (s.grants_taunted and s.source_id == ctx.actor.id)
            ]
            ctx.target.active_statuses.append(taunt_status)
            # Immediately update taunted_by so TUI sees correct state
            # between rounds (the full derivation in _tick_statuses only
            # runs at round start, which is too late for display).
            if ctx.actor.id not in ctx.target.taunted_by:
                ctx.target.taunted_by.append(ctx.actor.id)
            ctx.state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_APPLIED,
                    round_number=ctx.state.round_number,
                    actor_id=ctx.actor.id,
                    target_id=ctx.target.id,
                    details={"status": "Taunted"},
                )
            )

    # --- Damage Calculation ---

    def _calculate_damage(
        self,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
    ) -> int:
        """Calculate raw damage for an effect."""
        if effect.stat_scaling == StatType.STR or effect.stat_scaling is None:
            damage = calculate_physical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_str=actor.effective_stats.STR,
                target_def=target.effective_stats.DEF,
                pierce_percent=effect.pierce_percent,
                def_reduction_ratio=DEF_REDUCTION_RATIO + target.extra_def_reduction,
            )
        elif effect.stat_scaling == StatType.MAG:
            damage = calculate_magical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_mag=actor.effective_stats.MAG,
                target_res=target.effective_stats.RES,
                pierce_percent=effect.pierce_percent,
            )
        elif effect.stat_scaling == StatType.DEF:
            damage = calculate_physical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_str=actor.effective_stats.DEF,
                target_def=target.effective_stats.DEF,
                pierce_percent=effect.pierce_percent,
                def_reduction_ratio=DEF_REDUCTION_RATIO + target.extra_def_reduction,
            )
        elif effect.stat_scaling == StatType.RES:
            damage = calculate_magical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_mag=actor.effective_stats.RES,
                target_res=target.effective_stats.RES,
                pierce_percent=effect.pierce_percent,
            )
        else:
            damage = max(1, effect.base_damage)

        return damage

    def _calculate_pre_def_damage(
        self,
        actor: CombatantState,
        effect: AbilityEffect,
    ) -> int:
        """Calculate damage ignoring target DEF/RES (for thorns reflection)."""
        if effect.stat_scaling == StatType.STR or effect.stat_scaling is None:
            damage = calculate_physical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_str=actor.effective_stats.STR,
                target_def=0,
            )
        elif effect.stat_scaling == StatType.MAG:
            damage = calculate_magical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_mag=actor.effective_stats.MAG,
                target_res=0,
            )
        elif effect.stat_scaling == StatType.DEF:
            damage = calculate_physical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_str=actor.effective_stats.DEF,
                target_def=0,
            )
        elif effect.stat_scaling == StatType.RES:
            damage = calculate_magical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_mag=actor.effective_stats.RES,
                target_res=0,
            )
        else:
            damage = max(1, effect.base_damage)

        return damage

    # --- Secondary Effects ---

    def _apply_secondary_effect(
        self,
        state: CombatState,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
        ability: Ability,
    ) -> CombatState:
        """Apply secondary effects (DOT, Shatter, Disrupt) after RES gate check."""
        if effect.stat_scaling == StatType.MAG:
            resisted = check_res_gate(target.effective_stats.RES, actor.effective_stats.MAG)
            if resisted:
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.STATUS_RESISTED,
                        round_number=state.round_number,
                        actor_id=actor.id,
                        target_id=target.id,
                        ability_id=ability.id,
                        details={"quality": effect.quality.value},
                    )
                )
                # RES_GATE_PASSED passives (counter-hex, etc.)
                res_handler = PASSIVE_DISPATCH.get(TriggerCondition.RES_GATE_PASSED)
                if res_handler:
                    for res_passive in self._get_all_passives(target, TriggerCondition.RES_GATE_PASSED):
                        if actor.is_alive:
                            res_ctx = PassiveContext(
                                state=state,
                                owner=target,
                                trigger_source=actor,
                            )
                            res_handler(res_passive, res_ctx)
                return state

        match effect.quality:
            case DamageQuality.DOT:
                stat_value = (
                    getattr(actor.effective_stats, effect.stat_scaling.value, 0)
                    if effect.stat_scaling
                    else 0
                )
                scaled_total = effect.base_damage + (effect.scaling_coefficient * stat_value)
                duration = max(1, effect.duration_rounds)
                dot_damage = max(1, int(scaled_total / duration))
                status = StatusEffect(
                    id=f"{ability.id}_dot_{id(effect)}",
                    name=f"{ability.name} DOT",
                    damage_per_round=dot_damage,
                    rounds_remaining=effect.duration_rounds,
                    source_id=actor.id,
                )
                target.active_statuses.append(status)

            case DamageQuality.SHATTER:
                def_reduction = int(target.effective_stats.DEF * effect.shatter_amount)
                status = StatusEffect(
                    id=f"{ability.id}_shatter_{id(effect)}",
                    name=f"{ability.name} Shatter",
                    stat_modifiers={"DEF": -def_reduction},
                    rounds_remaining=effect.duration_rounds,
                    source_id=actor.id,
                )
                target.active_statuses.append(status)

            case DamageQuality.DISRUPT:
                status = StatusEffect(
                    id=f"{ability.id}_disrupt_{id(effect)}",
                    name=f"{ability.name} Disrupt",
                    rounds_remaining=effect.duration_rounds,
                    source_id=actor.id,
                )
                target.active_statuses.append(status)

        state.log.append(
            CombatEvent(
                event_type=CombatEventType.STATUS_APPLIED,
                round_number=state.round_number,
                actor_id=actor.id,
                target_id=target.id,
                ability_id=ability.id,
                details={"quality": effect.quality.value},
            )
        )

        return state

    # --- Pipeline Helpers ---

    def _find_split_passive(self, combatant: CombatantState) -> Ability | None:
        """Find a passive with split_into_templates effect on the combatant."""
        for ability_id in combatant.ability_ids:
            ability = self.abilities.get(ability_id)
            if ability is None:
                continue
            for effect in ability.effects:
                if effect.split_into_templates:
                    return ability
        return None

    def _get_item_leech_for_effect(
        self, combatant: CombatantState, effect: AbilityEffect,
    ) -> float:
        """Get item leech percent matching the effect's damage type."""
        if effect.stat_scaling == StatType.MAG:
            return combatant.mag_leech_percent
        # STR-scaling, None, or any other stat → physical leech
        return combatant.phys_leech_percent
