"""Combat engine: turn loop, action resolution, Cheat/Survive."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from heresiarch.engine.ai import EnemyAI
from heresiarch.engine.passive_handlers import PASSIVE_DISPATCH, PassiveContext
from heresiarch.engine.formulas import (
    INSIGHT_MULTIPLIER_PER_STACK,
    MARK_DAMAGE_BONUS,
    MAX_ACTION_POINT_BANK,
    CHEAT_DEBT_PER_ACTION,
    CHEAT_DEBT_RECOVERY_PER_TURN,
    apply_partial_action_modifier,
    apply_survive_reduction,
    calculate_bonus_actions,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_frenzy_multiplier,
    calculate_insight_multiplier,
    calculate_max_hp,
    calculate_magical_damage,
    calculate_physical_damage,
    calculate_stats_at_level,
    check_res_gate,
    evaluate_item_scaling,
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
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatEvent,
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
    StatusEffect,
)
from heresiarch.engine.models.enemies import EnemyInstance, EnemyTemplate
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.stats import StatBlock, StatType


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
    is_partial: bool
    insight_multiplier: float
    damage: int = 0


class CombatEngine:
    """Stateless combat resolver.

    All randomness goes through an injected RNG for reproducible testing.
    """

    def __init__(
        self,
        ability_registry: dict[str, Ability],
        item_registry: dict[str, Item],
        job_registry: dict[str, JobTemplate],
        rng: random.Random | None = None,
    ):
        self.abilities = ability_registry
        self.items = item_registry
        self.jobs = job_registry
        self.rng = rng or random.Random()
        self.ai = EnemyAI(rng=self.rng)

    def initialize_combat(
        self,
        player_characters: list[CharacterInstance],
        enemies: list[EnemyInstance],
    ) -> CombatState:
        """Set up initial CombatState from party and enemy group."""
        player_combatants = []
        for char in player_characters:
            job = self.jobs[char.job_id]
            equipped = self._get_equipped_items(char)
            effective = calculate_effective_stats(char.base_stats, equipped, [])
            max_hp = calculate_max_hp(
                job.base_hp, job.hp_growth, char.level, effective.DEF
            )
            current_hp = char.current_hp if char.current_hp > 0 else max_hp

            # Sum leech percent from all equipped items
            total_leech = sum(item.leech_percent for item in equipped)

            player_combatants.append(
                CombatantState(
                    id=char.id,
                    is_player=True,
                    level=char.level,
                    current_hp=min(current_hp, max_hp),
                    max_hp=max_hp,
                    base_stats=char.base_stats,
                    equipment_stats=effective,  # Baseline for status tick rebuilds
                    effective_stats=effective,
                    ability_ids=list(char.abilities),
                    leech_percent=total_leech,
                )
            )

        enemy_combatants = []
        _eid_counts: dict[str, int] = {}
        for enemy in enemies:
            count = _eid_counts.get(enemy.template_id, 0)
            _eid_counts[enemy.template_id] = count + 1
            enemy_combatants.append(
                CombatantState(
                    id=f"{enemy.template_id}_{count}",
                    is_player=False,
                    level=enemy.level,
                    current_hp=enemy.current_hp,
                    max_hp=enemy.max_hp,
                    base_stats=enemy.stats,
                    equipment_stats=enemy.stats,  # Enemies have no equipment layer
                    effective_stats=enemy.stats,
                    ability_ids=list(enemy.abilities),
                )
            )

        state = CombatState(
            player_combatants=player_combatants,
            enemy_combatants=enemy_combatants,
        )

        state.turn_order = self._determine_turn_order(state)
        return state

    def process_round(
        self,
        state: CombatState,
        player_decisions: dict[str, PlayerTurnDecision],
        enemy_templates: dict[str, EnemyTemplate],
    ) -> CombatState:
        """Execute one full round of combat.

        1. Increment round, tick statuses
        2. Determine turn order
        3. Process each combatant's turn
        4. Check win/loss
        """
        state.round_number += 1
        state.log.append(
            CombatEvent(
                event_type=CombatEventType.ROUND_START,
                round_number=state.round_number,
            )
        )

        state = self._tick_statuses(state)

        state.turn_order = self._determine_turn_order(state, player_decisions)

        self._pre_roll_enemy_intents(state, enemy_templates)

        for combatant_id in state.turn_order:
            if state.is_finished:
                break

            combatant = state.get_combatant(combatant_id)
            if combatant is None or not combatant.is_alive:
                continue

            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.TURN_START,
                    round_number=state.round_number,
                    actor_id=combatant_id,
                )
            )

            if combatant.is_player:
                decision = player_decisions.get(combatant_id)
                if decision:
                    state = self._resolve_player_turn(state, combatant_id, decision)
            else:
                template_id = combatant_id.rsplit("_", 1)[0]
                template = enemy_templates.get(template_id)
                if template:
                    state = self._resolve_enemy_turn(state, combatant_id, template)

            state = self._check_combat_end(state)

        return state

    def create_enemy_instance(
        self,
        template: EnemyTemplate,
        zone_level: int,
        instance_id: str | None = None,
    ) -> EnemyInstance:
        """Create a concrete enemy from a template at a zone level.

        Enemy stats come from budget allocation, then get amplified by
        equipment through the same Layer 3 scaling players use.
        """
        base_stats = calculate_enemy_stats(
            zone_level, template.budget_multiplier, template.stat_distribution
        )

        # Apply equipment scaling (same Layer 3 system as players)
        equipped_items = [
            self.items[eid] for eid in template.equipment if eid in self.items
        ]
        effective_stats = calculate_effective_stats(base_stats, equipped_items, [])

        hp = calculate_enemy_hp(
            zone_level, template.budget_multiplier, template.base_hp, template.hp_per_budget
        )

        return EnemyInstance(
            template_id=template.id,
            name=instance_id if instance_id else template.name,
            level=zone_level,
            stats=effective_stats,
            max_hp=hp,
            current_hp=hp,
            abilities=list(template.abilities),
            equipment=list(template.equipment),
            action_table=template.action_table,
            target_preference=template.target_preference,
        )

    # --- In-Combat Item Use ---

    def use_combat_item(
        self,
        state: CombatState,
        actor_id: str,
        target_id: str,
        item: Item,
    ) -> CombatState:
        """Apply a consumable item during combat.

        Validates the item, applies healing to the target combatant,
        and emits appropriate combat events. Does NOT handle stash
        removal (caller's responsibility on RunState).
        """
        if not item.is_consumable:
            raise ValueError(f"Item '{item.id}' is not a consumable")

        target = state.get_combatant(target_id)
        if target is None:
            raise ValueError(f"No combatant with id '{target_id}'")
        if not target.is_alive:
            raise ValueError(f"Combatant '{target_id}' is dead")

        heal = item.heal_amount + int(target.max_hp * item.heal_percent)
        if heal > 0:
            old_hp = target.current_hp
            target.current_hp = min(target.max_hp, target.current_hp + heal)
            actual_heal = target.current_hp - old_hp
            if actual_heal > 0:
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.HEALING,
                        round_number=state.round_number,
                        actor_id=actor_id,
                        target_id=target_id,
                        value=actual_heal,
                        details={"source": item.id},
                    )
                )

        return state

    # --- Turn Resolution ---

    def _resolve_player_turn(
        self,
        state: CombatState,
        combatant_id: str,
        decision: PlayerTurnDecision,
    ) -> CombatState:
        """Process a player's turn with Cheat/Survive decision."""
        combatant = state.get_combatant(combatant_id)
        if combatant is None:
            return state

        # Cheat/Survive resolution
        match decision.cheat_survive:
            case CheatSurviveChoice.SURVIVE:
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.CHEAT_SURVIVE_DECISION,
                        round_number=state.round_number,
                        actor_id=combatant_id,
                        details={"choice": "SURVIVE"},
                    )
                )
                survive_action = CombatAction(
                    actor_id=combatant_id,
                    ability_id="survive",
                    target_ids=[combatant_id],
                )
                state = self._resolve_action(state, combatant_id, survive_action)
                return state

            case CheatSurviveChoice.CHEAT:
                combatant.is_surviving = False
                actions_to_spend = min(decision.cheat_actions, combatant.action_points)
                combatant.action_points -= actions_to_spend
                combatant.cheat_debt += actions_to_spend * CHEAT_DEBT_PER_ACTION
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.CHEAT_SURVIVE_DECISION,
                        round_number=state.round_number,
                        actor_id=combatant_id,
                        details={
                            "choice": "CHEAT",
                            "actions_spent": actions_to_spend,
                            "debt": combatant.cheat_debt,
                        },
                    )
                )

                # Primary action
                if decision.primary_action:
                    state = self._resolve_action(
                        state, combatant_id, decision.primary_action
                    )

                # Extra actions from Cheat — use individually chosen actions
                for i in range(actions_to_spend):
                    if state.is_finished:
                        break
                    if i < len(decision.cheat_extra_actions):
                        state = self._resolve_action(
                            state, combatant_id, decision.cheat_extra_actions[i]
                        )
                    elif decision.primary_action:
                        # Fallback: repeat primary if no extra actions specified
                        state = self._resolve_action(
                            state, combatant_id, decision.primary_action
                        )

            case CheatSurviveChoice.NORMAL:
                combatant.is_surviving = False
                if combatant.cheat_debt > 0:
                    combatant.cheat_debt = max(
                        0, combatant.cheat_debt - CHEAT_DEBT_RECOVERY_PER_TURN
                    )

                if decision.primary_action:
                    state = self._resolve_action(
                        state, combatant_id, decision.primary_action
                    )

        # Bonus partial actions from SPD
        bonus = calculate_bonus_actions(combatant.effective_stats.SPD)
        for partial in decision.partial_actions[:bonus]:
            if state.is_finished:
                break
            state = self._resolve_action(state, combatant_id, partial, is_partial=True)

        return state

    def _pre_roll_enemy_intents(
        self,
        state: CombatState,
        enemy_templates: dict[str, EnemyTemplate],
    ) -> None:
        """Pre-roll actions for all living enemies at round start.

        Intents are stored on CombatantState.pending_action and consumed
        during the turn loop. This allows future preview mechanics to
        reveal enemy plans before player decisions matter.
        """
        for enemy in state.living_enemies:
            template_id = enemy.id.rsplit("_", 1)[0]
            template = enemy_templates.get(template_id)
            if template is None:
                continue
            ability_id, target_ids = self.ai.select_action(
                enemy, template, state, self.abilities
            )
            enemy.pending_action = CombatAction(
                actor_id=enemy.id,
                ability_id=ability_id,
                target_ids=target_ids,
            )

    def _resolve_enemy_turn(
        self,
        state: CombatState,
        combatant_id: str,
        template: EnemyTemplate,
    ) -> CombatState:
        """Process an enemy's turn using pre-rolled intent."""
        combatant = state.get_combatant(combatant_id)
        if combatant is None:
            return state

        # Recover cheat debt (enemies can theoretically Cheat too via shared pool)
        if combatant.cheat_debt > 0:
            combatant.cheat_debt = max(
                0, combatant.cheat_debt - CHEAT_DEBT_RECOVERY_PER_TURN
            )

        # Consume pre-rolled intent, fallback to live AI if missing
        action = combatant.pending_action
        if action is None:
            ability_id, target_ids = self.ai.select_action(
                combatant, template, state, self.abilities
            )
            action = CombatAction(
                actor_id=combatant_id,
                ability_id=ability_id,
                target_ids=target_ids,
            )
        combatant.pending_action = None

        state = self._resolve_action(state, combatant_id, action)

        # Decrement cooldowns
        for ability_key in list(combatant.cooldowns.keys()):
            if combatant.cooldowns[ability_key] > 0:
                combatant.cooldowns[ability_key] -= 1

        return state

    # --- Action Resolution ---

    def _resolve_action(
        self,
        state: CombatState,
        actor_id: str,
        action: CombatAction,
        is_partial: bool = False,
    ) -> CombatState:
        """Core action resolution. Routes to damage calc, applies effects."""
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

        state.log.append(
            CombatEvent(
                event_type=CombatEventType.BONUS_ACTION if is_partial else CombatEventType.ACTION_DECLARED,
                round_number=state.round_number,
                actor_id=actor_id,
                ability_id=action.ability_id,
                details={"targets": action.target_ids, "is_partial": is_partial},
            )
        )

        # For SELF-targeting abilities (like Taunt), use actor as target
        effective_target_ids = list(action.target_ids)
        if ability.target == TargetType.SELF and not effective_target_ids:
            effective_target_ids = [actor_id]

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
                        state, actor, actor, effect, ability, is_partial,
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
                    state, actor, target, effect, ability, is_partial,
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

    def _apply_effect(
        self,
        state: CombatState,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
        ability: Ability,
        is_partial: bool,
        insight_multiplier: float = 1.0,
    ) -> CombatState:
        """Apply a single ability effect to a target via phased pipeline."""
        ctx = EffectContext(
            state=state,
            actor=actor,
            target=target,
            effect=effect,
            ability=ability,
            is_partial=is_partial,
            insight_multiplier=insight_multiplier,
        )

        self._phase_damage_calc(ctx)
        self._phase_damage_modify(ctx)
        self._phase_damage_redirect(ctx)
        self._phase_damage_reduce(ctx)
        self._phase_damage_apply(ctx)
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
                ctx.actor, ctx.target, ctx.effect, ctx.is_partial,
            )

    def _phase_damage_modify(self, ctx: EffectContext) -> None:
        """Phase 2: Apply damage multipliers (insight, frenzy, surge, chain, mark)."""
        if ctx.damage <= 0:
            return

        # Insight damage amplification
        if ctx.insight_multiplier > 1.0:
            ctx.damage = int(ctx.damage * ctx.insight_multiplier)

        # Frenzy damage amplification (ratchet: max of level vs chain exponential)
        frenzy_ability = self._get_passive(
            ctx.actor, TriggerCondition.ON_CONSECUTIVE_ATTACK, ctx.state,
        )
        if frenzy_ability:
            multiplier = max(ctx.actor.frenzy_level, calculate_frenzy_multiplier(ctx.actor.frenzy_chain))
            if multiplier > 1.0:
                ctx.damage = int(ctx.damage * multiplier)

        # Surge stacking (Crescendo etc.)
        if ctx.effect.quality == DamageQuality.SURGE and ctx.effect.surge_stack_bonus > 0:
            stacks = ctx.actor.surge_stacks.get(ctx.ability.id, 0)
            multiplier = 1.0 + ctx.effect.surge_stack_bonus * stacks
            ctx.damage = int(ctx.damage * multiplier)
            ctx.actor.surge_stacks[ctx.ability.id] = stacks + 1

        # Chain damage reduction
        if ctx.effect.quality == DamageQuality.CHAIN:
            ctx.damage = int(ctx.damage * ctx.effect.chain_damage_ratio)

        # Mark bonus damage against marked targets
        if ctx.target.is_marked:
            ctx.damage = int(ctx.damage * MARK_DAMAGE_BONUS)

    def _phase_damage_redirect(self, ctx: EffectContext) -> None:
        """Phase 3: Taunt redirect for enemies attacking players."""
        if ctx.damage <= 0:
            return
        if not ctx.actor.is_player and ctx.target.is_player:
            taunting = [
                p for p in ctx.state.living_players
                if p.is_taunting and p.id != ctx.target.id
            ]
            if taunting:
                original_target_id = ctx.target.id
                ctx.target = taunting[0]
                ctx.state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.TAUNT_REDIRECT,
                        round_number=ctx.state.round_number,
                        actor_id=ctx.actor.id,
                        target_id=ctx.target.id,
                        details={"original_target": original_target_id},
                    )
                )

    def _phase_damage_reduce(self, ctx: EffectContext) -> None:
        """Phase 4: Survive damage reduction."""
        if ctx.damage <= 0:
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

        # Leech healing
        total_leech = ctx.effect.leech_percent + self._get_item_leech(ctx.actor, ctx.state)
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
                item_leech_percent=self._get_item_leech(ctx.target, ctx.state),
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
                    ctx.state.gold_stolen_by_enemies += steal_amount
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

        # Taunt effect — add a status so it persists through the round
        if ctx.effect.applies_taunt and ctx.actor.is_alive:
            ctx.actor.is_taunting = True
            taunt_duration = ctx.effect.duration_rounds if ctx.effect.duration_rounds > 0 else 1
            taunt_status = StatusEffect(
                id="taunt_active",
                name="Taunt",
                rounds_remaining=taunt_duration + 1,
                source_id=ctx.actor.id,
                grants_taunt=True,
            )
            ctx.actor.active_statuses = [
                s for s in ctx.actor.active_statuses if not s.grants_taunt
            ]
            ctx.actor.active_statuses.append(taunt_status)

    def _calculate_damage(
        self,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
        is_partial: bool,
    ) -> int:
        """Calculate raw damage for an effect."""
        if effect.stat_scaling == StatType.STR or effect.stat_scaling is None:
            damage = calculate_physical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_str=actor.effective_stats.STR,
                target_def=target.effective_stats.DEF,
                pierce_percent=effect.pierce_percent,
            )
        elif effect.stat_scaling == StatType.MAG:
            damage = calculate_magical_damage(
                ability_base=effect.base_damage,
                ability_coefficient=effect.scaling_coefficient,
                attacker_mag=actor.effective_stats.MAG,
            )
        else:
            damage = max(1, effect.base_damage)

        if is_partial:
            damage = apply_partial_action_modifier(damage, True)

        return damage


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
                dot_damage = max(1, int(effect.base_damage * 0.5))
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

    # --- Status Tick ---

    def _tick_statuses(self, state: CombatState) -> CombatState:
        """Round start: tick DOTs, decrement durations, expire statuses."""
        for combatant in state.all_combatants:
            if not combatant.is_alive:
                continue

            if state.round_number > 1:
                self._evaluate_round_boundary_passives(state, combatant)

            # Reset per-round flags, re-derive from active statuses
            combatant.frenzy_stacks = 0
            combatant.dealt_damage_this_round = False
            combatant.is_surviving = False
            combatant.is_taunting = any(
                s.grants_taunt for s in combatant.active_statuses
            )
            combatant.is_marked = any(
                s.grants_mark for s in combatant.active_statuses
            )

            self._tick_status_effects(state, combatant)
            self._evaluate_conditional_passives(state, combatant)
            self._recalculate_combat_stats(combatant)

        return state

    def _evaluate_round_boundary_passives(
        self, state: CombatState, combatant: CombatantState,
    ) -> None:
        """Dispatch round-boundary passives (frenzy) via handler table."""
        for trigger in (TriggerCondition.ON_CONSECUTIVE_ATTACK,):
            handler = PASSIVE_DISPATCH.get(trigger)
            if handler is None:
                continue
            for passive in self._get_all_passives(combatant, trigger):
                pctx = PassiveContext(state=state, owner=combatant)
                handler(passive, pctx)

    def _tick_status_effects(
        self, state: CombatState, combatant: CombatantState,
    ) -> None:
        """Tick DOTs, decrement durations, expire statuses."""
        expired: list[StatusEffect] = []
        for status in combatant.active_statuses:
            # DOT tick
            if status.damage_per_round > 0:
                combatant.current_hp = max(
                    0, combatant.current_hp - status.damage_per_round,
                )
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.DOT_TICK,
                        round_number=state.round_number,
                        target_id=combatant.id,
                        value=status.damage_per_round,
                        details={"status": status.name},
                    )
                )
                if combatant.current_hp <= 0:
                    combatant.is_alive = False
                    state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.DEATH,
                            round_number=state.round_number,
                            target_id=combatant.id,
                        )
                    )

            status.rounds_remaining -= 1
            if status.rounds_remaining <= 0:
                expired.append(status)

        for status in expired:
            combatant.active_statuses.remove(status)
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_EXPIRED,
                    round_number=state.round_number,
                    target_id=combatant.id,
                    details={"status": status.name},
                )
            )

    def _evaluate_conditional_passives(
        self, state: CombatState, combatant: CombatantState,
    ) -> None:
        """Dispatch conditional passives (HP threshold, etc.) via handler table."""
        handler = PASSIVE_DISPATCH.get(TriggerCondition.HP_BELOW_THRESHOLD)
        if handler is None:
            return
        for passive in self._get_all_passives(combatant, TriggerCondition.HP_BELOW_THRESHOLD):
            pctx = PassiveContext(state=state, owner=combatant)
            handler(passive, pctx)

    def _recalculate_combat_stats(self, combatant: CombatantState) -> None:
        """Recalculate effective stats: equipment baseline + active combat buffs."""
        effective_data = combatant.equipment_stats.model_dump()
        for status in combatant.active_statuses:
            for stat_name, mod in status.stat_modifiers.items():
                if stat_name in effective_data:
                    effective_data[stat_name] += mod
        combatant.effective_stats = StatBlock(
            **{k: max(0, v) for k, v in effective_data.items()}
        )

    # --- Helpers ---

    def _determine_turn_order(
        self,
        state: CombatState,
        player_decisions: dict[str, PlayerTurnDecision] | None = None,
    ) -> list[str]:
        """Order combatants by priority → SPD → player tiebreak (all descending).

        Priority abilities (e.g. Survive) resolve before non-priority.
        Multiple priority users tiebreak by SPD as usual.
        """
        alive = [c for c in state.all_combatants if c.is_alive]

        priority_ids: set[str] = set()
        for c in alive:
            ability = self._get_intended_ability(c, player_decisions)
            if ability is not None and ability.priority:
                priority_ids.add(c.id)

        alive.sort(
            key=lambda c: (
                1 if c.id in priority_ids else 0,
                c.effective_stats.SPD,
                1 if c.is_player else 0,
            ),
            reverse=True,
        )
        return [c.id for c in alive]

    def _get_intended_ability(
        self,
        combatant: CombatantState,
        player_decisions: dict[str, PlayerTurnDecision] | None,
    ) -> Ability | None:
        """Look up the ability a combatant intends to use this round."""
        if combatant.is_player and player_decisions:
            decision = player_decisions.get(combatant.id)
            if decision is None:
                return None
            if decision.cheat_survive == CheatSurviveChoice.SURVIVE:
                return self.abilities.get("survive")
            if decision.primary_action:
                return self.abilities.get(decision.primary_action.ability_id)
        elif not combatant.is_player and combatant.pending_action:
            return self.abilities.get(combatant.pending_action.ability_id)
        return None

    def _check_combat_end(self, state: CombatState) -> CombatState:
        """Set is_finished and player_won if one side is eliminated."""
        if not state.living_players:
            state.is_finished = True
            state.player_won = False
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.COMBAT_END,
                    round_number=state.round_number,
                    details={"result": "player_defeat"},
                )
            )
        elif not state.living_enemies:
            state.is_finished = True
            state.player_won = True
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.COMBAT_END,
                    round_number=state.round_number,
                    details={"result": "player_victory"},
                )
            )
        return state

    def _get_equipped_items(self, char: CharacterInstance) -> list[Item]:
        """Get actual Item objects for a character's equipment."""
        items: list[Item] = []
        for slot, item_id in char.equipment.items():
            if item_id and item_id in self.items:
                items.append(self.items[item_id])
        return items

    def _get_passive(
        self,
        combatant: CombatantState,
        trigger: TriggerCondition,
        state: CombatState,
    ) -> Ability | None:
        """Find the first passive ability with the given trigger on a combatant."""
        for ability_id in combatant.ability_ids:
            ability = self.abilities.get(ability_id)
            if ability is None:
                continue
            if (
                ability.category == AbilityCategory.PASSIVE
                and ability.trigger == trigger
            ):
                return ability
        return None

    def _get_all_passives(
        self,
        combatant: CombatantState,
        trigger: TriggerCondition,
    ) -> list[Ability]:
        """Find all passive abilities with the given trigger on a combatant."""
        result: list[Ability] = []
        for ability_id in combatant.ability_ids:
            ability = self.abilities.get(ability_id)
            if ability is None:
                continue
            if (
                ability.category == AbilityCategory.PASSIVE
                and ability.trigger == trigger
            ):
                result.append(ability)
        return result

    def _find_survive_lethal_passive(self, combatant: CombatantState) -> Ability | None:
        """Find a passive with survive_lethal effect on the combatant."""
        for ability_id in combatant.ability_ids:
            ability = self.abilities.get(ability_id)
            if ability is None:
                continue
            for effect in ability.effects:
                if effect.survive_lethal:
                    return ability
        return None

    def _get_item_leech(self, combatant: CombatantState, state: CombatState) -> float:
        """Get total leech percent from equipped items."""
        return combatant.leech_percent
