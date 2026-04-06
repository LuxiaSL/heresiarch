"""Combat engine: turn loop, action resolution, Cheat/Survive."""

from __future__ import annotations

import random
from typing import Any

from heresiarch.engine.ai import EnemyAI
from heresiarch.engine.formulas import (
    MAX_ACTION_POINT_BANK,
    CHEAT_DEBT_PER_ACTION,
    CHEAT_DEBT_RECOVERY_PER_TURN,
    apply_partial_action_modifier,
    apply_survive_reduction,
    calculate_bonus_actions,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
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

            player_combatants.append(
                CombatantState(
                    id=char.id,
                    is_player=True,
                    current_hp=min(current_hp, max_hp),
                    max_hp=max_hp,
                    base_stats=char.base_stats,
                    effective_stats=effective,
                )
            )

        enemy_combatants = []
        for enemy in enemies:
            enemy_combatants.append(
                CombatantState(
                    id=enemy.template_id + f"_{id(enemy)}",
                    is_player=False,
                    current_hp=enemy.current_hp,
                    max_hp=enemy.max_hp,
                    base_stats=enemy.stats,
                    effective_stats=enemy.stats,
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

        state.turn_order = self._determine_turn_order(state)

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
        """Create a concrete enemy from a template at a zone level."""
        stats = calculate_enemy_stats(
            zone_level, template.budget_multiplier, template.stat_distribution
        )
        hp = calculate_enemy_hp(
            zone_level, template.budget_multiplier, template.base_hp, template.hp_per_budget
        )

        return EnemyInstance(
            template_id=template.id,
            name=template.name,
            level=zone_level,
            stats=stats,
            max_hp=hp,
            current_hp=hp,
            abilities=list(template.abilities),
            equipment=list(template.equipment),
            action_table=template.action_table,
            target_preference=template.target_preference,
        )

    def create_character_combatant(
        self,
        char: CharacterInstance,
        job: JobTemplate,
    ) -> CharacterInstance:
        """Level up a character: compute stats from job growth."""
        stats = calculate_stats_at_level(job.growth, char.level)
        equipped = self._get_equipped_items(char)
        effective = calculate_effective_stats(stats, equipped, [])
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, char.level, effective.DEF)

        return char.model_copy(
            update={
                "base_stats": stats,
                "current_hp": max_hp,
                "abilities": [job.innate_ability_id] + [
                    item.granted_ability_id
                    for item in equipped
                    if item.granted_ability_id
                ],
            }
        )

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
                combatant.action_points = min(
                    combatant.action_points + 1, MAX_ACTION_POINT_BANK
                )
                combatant.is_surviving = True
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.CHEAT_SURVIVE_DECISION,
                        round_number=state.round_number,
                        actor_id=combatant_id,
                        details={"choice": "SURVIVE", "ap": combatant.action_points},
                    )
                )
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

                # Extra actions from Cheat
                for i in range(actions_to_spend):
                    if state.is_finished:
                        break
                    if decision.primary_action:
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

    def _resolve_enemy_turn(
        self,
        state: CombatState,
        combatant_id: str,
        template: EnemyTemplate,
    ) -> CombatState:
        """Process an enemy's turn via AI."""
        combatant = state.get_combatant(combatant_id)
        if combatant is None:
            return state

        # Recover cheat debt (enemies can theoretically Cheat too via shared pool)
        if combatant.cheat_debt > 0:
            combatant.cheat_debt = max(
                0, combatant.cheat_debt - CHEAT_DEBT_RECOVERY_PER_TURN
            )

        ability_id, target_ids = self.ai.select_action(
            combatant, template, state, self.abilities
        )

        action = CombatAction(
            actor_id=combatant_id,
            ability_id=ability_id,
            target_ids=target_ids,
        )

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

        # Track Frenzy stacks for consecutive attacks
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
        effective_target_ids = action.target_ids
        if ability.target == TargetType.SELF and not effective_target_ids:
            effective_target_ids = [actor_id]

        for effect in ability.effects:
            if state.is_finished:
                break

            for target_id in effective_target_ids:
                if state.is_finished:
                    break

                target = state.get_combatant(target_id)
                if target is None or not target.is_alive:
                    continue

                state = self._apply_effect(
                    state, actor, target, effect, ability, is_partial
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

        return state

    def _apply_effect(
        self,
        state: CombatState,
        actor: CombatantState,
        target: CombatantState,
        effect: AbilityEffect,
        ability: Ability,
        is_partial: bool,
    ) -> CombatState:
        """Apply a single ability effect to a target."""
        damage = 0

        if effect.base_damage > 0 or effect.scaling_coefficient > 0:
            damage = self._calculate_damage(actor, target, effect, is_partial)

            # Frenzy bonus (consecutive attack stacking)
            frenzy_ability = self._get_passive(actor, TriggerCondition.ON_CONSECUTIVE_ATTACK, state)
            if frenzy_ability and actor.frenzy_stacks > 1:
                for frenzy_effect in frenzy_ability.effects:
                    if frenzy_effect.surge_stack_bonus > 0:
                        multiplier = 1.0 + frenzy_effect.surge_stack_bonus * (actor.frenzy_stacks - 1)
                        damage = int(damage * multiplier)
                        if actor.frenzy_stacks > 1:
                            state.log.append(
                                CombatEvent(
                                    event_type=CombatEventType.FRENZY_STACK,
                                    round_number=state.round_number,
                                    actor_id=actor.id,
                                    value=actor.frenzy_stacks,
                                    details={"multiplier": multiplier},
                                )
                            )

            # Surge stacking (Crescendo etc.)
            if effect.quality == DamageQuality.SURGE and effect.surge_stack_bonus > 0:
                stacks = actor.surge_stacks.get(ability.id, 0)
                multiplier = 1.0 + effect.surge_stack_bonus * stacks
                damage = int(damage * multiplier)
                actor.surge_stacks[ability.id] = stacks + 1

            # Chain damage reduction
            if effect.quality == DamageQuality.CHAIN:
                damage = int(damage * effect.chain_damage_ratio)

            # Taunt redirect for enemies attacking players
            if not actor.is_player and target.is_player:
                taunting = [p for p in state.living_players if p.is_taunting and p.id != target.id]
                if taunting:
                    original_target_id = target.id
                    target = taunting[0]
                    state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.TAUNT_REDIRECT,
                            round_number=state.round_number,
                            actor_id=actor.id,
                            target_id=target.id,
                            details={"original_target": original_target_id},
                        )
                    )

            # Survive reduction
            damage = apply_survive_reduction(damage, target.is_surviving)

            # Apply damage
            if damage > 0:
                target.current_hp = max(0, target.current_hp - damage)
                state.log.append(
                    CombatEvent(
                        event_type=CombatEventType.DAMAGE_DEALT,
                        round_number=state.round_number,
                        actor_id=actor.id,
                        target_id=target.id,
                        ability_id=ability.id,
                        value=damage,
                    )
                )

                # Leech healing
                total_leech = effect.leech_percent + self._get_item_leech(actor, state)
                if total_leech > 0:
                    heal = max(1, int(damage * total_leech))
                    actor.current_hp = min(actor.max_hp, actor.current_hp + heal)
                    state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.HEALING,
                            round_number=state.round_number,
                            actor_id=actor.id,
                            target_id=actor.id,
                            value=heal,
                            details={"source": "leech"},
                        )
                    )

                # Retaliate trigger
                if target.is_alive and target.is_player:
                    retaliate = self._get_passive(
                        target, TriggerCondition.ON_HIT_RECEIVED, state
                    )
                    if retaliate:
                        ret_damage = self._calculate_retaliate_damage(target, retaliate)
                        if ret_damage > 0:
                            actor.current_hp = max(0, actor.current_hp - ret_damage)
                            state.log.append(
                                CombatEvent(
                                    event_type=CombatEventType.RETALIATE_TRIGGERED,
                                    round_number=state.round_number,
                                    actor_id=target.id,
                                    target_id=actor.id,
                                    value=ret_damage,
                                )
                            )
                            if actor.current_hp <= 0:
                                actor.is_alive = False
                                state.log.append(
                                    CombatEvent(
                                        event_type=CombatEventType.DEATH,
                                        round_number=state.round_number,
                                        target_id=actor.id,
                                    )
                                )

                # Death check
                if target.current_hp <= 0:
                    target.is_alive = False
                    state.log.append(
                        CombatEvent(
                            event_type=CombatEventType.DEATH,
                            round_number=state.round_number,
                            target_id=target.id,
                        )
                    )

        # Secondary effects (DOT, debuffs) — check RES gate
        if effect.quality in (DamageQuality.DOT, DamageQuality.SHATTER, DamageQuality.DISRUPT):
            if effect.duration_rounds > 0 and target.is_alive:
                state = self._apply_secondary_effect(state, actor, target, effect, ability)

        # DEF buff (Brace Strike, Barrier)
        if effect.def_buff != 0 and target.is_alive:
            status = StatusEffect(
                id=f"{ability.id}_def_buff",
                name=f"{ability.name} DEF buff",
                stat_modifiers={"DEF": effect.def_buff},
                rounds_remaining=effect.duration_rounds if effect.duration_rounds > 0 else 1,
                source_id=actor.id,
            )
            target.active_statuses.append(status)
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_APPLIED,
                    round_number=state.round_number,
                    actor_id=actor.id,
                    target_id=target.id,
                    details={"status": status.name},
                )
            )

        # Taunt effect — add a status so it persists through the round
        if ability.id == "taunt" and actor.is_alive:
            actor.is_taunting = True
            taunt_duration = 1
            for eff in ability.effects:
                if eff.duration_rounds > 0:
                    taunt_duration = eff.duration_rounds
            taunt_status = StatusEffect(
                id="taunt_active",
                name="Taunt",
                rounds_remaining=taunt_duration + 1,  # +1 because tick decrements at round start
                source_id=actor.id,
            )
            # Remove existing taunt status if any
            actor.active_statuses = [
                s for s in actor.active_statuses if s.id != "taunt_active"
            ]
            actor.active_statuses.append(taunt_status)

        return state

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

    def _calculate_retaliate_damage(
        self,
        retaliator: CombatantState,
        retaliate_ability: Ability,
    ) -> int:
        """Calculate Retaliate counter-attack damage."""
        for effect in retaliate_ability.effects:
            if effect.stat_scaling == StatType.STR:
                return max(
                    1,
                    int(effect.base_damage + effect.scaling_coefficient * retaliator.effective_stats.STR),
                )
        return 0

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

            # Reset per-round flags
            # is_taunting persists from prior round until tick clears it
            # (taunt lasts 1 full round after activation)
            combatant.is_taunting = False
            combatant.is_surviving = False
            combatant.frenzy_stacks = 0

            # Re-apply taunt if there's an active taunt status
            for status in combatant.active_statuses:
                if "taunt" in status.id.lower():
                    combatant.is_taunting = True

            expired: list[StatusEffect] = []
            for status in combatant.active_statuses:
                # DOT tick
                if status.damage_per_round > 0:
                    combatant.current_hp = max(
                        0, combatant.current_hp - status.damage_per_round
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

            # Recalculate effective stats after status changes
            effective_data = combatant.base_stats.model_dump()
            for status in combatant.active_statuses:
                for stat_name, mod in status.stat_modifiers.items():
                    if stat_name in effective_data:
                        effective_data[stat_name] += mod
            combatant.effective_stats = StatBlock(
                **{k: max(0, v) for k, v in effective_data.items()}
            )

        return state

    # --- Helpers ---

    def _determine_turn_order(self, state: CombatState) -> list[str]:
        """Order combatants by effective SPD descending. Players win ties."""
        alive = [c for c in state.all_combatants if c.is_alive]
        alive.sort(
            key=lambda c: (c.effective_stats.SPD, 1 if c.is_player else 0),
            reverse=True,
        )
        return [c.id for c in alive]

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
        """Find a passive ability with the given trigger on a combatant.

        Checks based on whether combatant is player or enemy.
        """
        # For players, we need to find their character to get ability list
        # For now, check all passive abilities in registry that match
        for ability_id, ability in self.abilities.items():
            if (
                ability.category == AbilityCategory.PASSIVE
                and ability.trigger == trigger
                and ability.is_innate
            ):
                # Check if this combatant would have this ability
                # Simplified: check if any job has this as innate
                for job in self.jobs.values():
                    if job.innate_ability_id == ability_id:
                        # Check if the combatant's stats suggest this job
                        # This is a simplification — proper implementation would
                        # track abilities on CombatantState
                        if combatant.is_player:
                            return ability
        return None

    def _get_item_leech(self, combatant: CombatantState, state: CombatState) -> float:
        """Get total leech percent from equipped items."""
        # Simplified: would need to look up character's equipped items
        # For now return 0 — leech from items needs CharacterInstance lookup
        return 0.0
