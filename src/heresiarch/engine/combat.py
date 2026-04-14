"""Combat engine: turn loop, action resolution, Cheat/Survive."""

from __future__ import annotations

import random

from heresiarch.engine.ai import EnemyAI
from heresiarch.engine.effect_pipeline import EffectContext, EffectPipelineMixin
from heresiarch.engine.passive_handlers import PASSIVE_DISPATCH, PassiveContext
from heresiarch.engine.formulas import (
    CHEAT_DEBT_PER_ACTION,
    CHEAT_DEBT_RECOVERY_PER_TURN,
    calculate_speed_bonus,
    calculate_effective_stats,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_max_hp,
    calculate_stats_at_level,
    evaluate_item_scaling,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
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
from heresiarch.engine.models.stats import StatBlock

# Re-export for backwards compatibility (tests import EffectContext from here)
__all__ = ["CombatEngine", "EffectContext"]


class CombatEngine(EffectPipelineMixin):
    """Stateless combat resolver.

    All randomness goes through an injected RNG for reproducible testing.
    """

    def __init__(
        self,
        ability_registry: dict[str, Ability],
        item_registry: dict[str, Item],
        job_registry: dict[str, JobTemplate],
        rng: random.Random | None = None,
        enemy_registry: dict[str, EnemyTemplate] | None = None,
    ):
        self.abilities = ability_registry
        self.items = item_registry
        self.jobs = job_registry
        self.enemy_registry: dict[str, EnemyTemplate] = enemy_registry or {}
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

            # Sum leech percent and DEF reduction bonus from all equipped items
            total_phys_leech = sum(item.phys_leech_percent for item in equipped)
            total_mag_leech = sum(item.mag_leech_percent for item in equipped)
            total_extra_def_reduction = sum(item.extra_def_reduction for item in equipped)

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
                    phys_leech_percent=total_phys_leech,
                    mag_leech_percent=total_mag_leech,
                    extra_def_reduction=total_extra_def_reduction,
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

        1. Increment round, refresh per-round state
        2. Determine turn order
        3. Process each combatant's turn
        4. Tick status durations (end-of-round)
        5. Check win/loss
        """
        state.round_number += 1
        state.consumed_items.clear()
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

            # Tick down invulnerability at turn start
            if combatant.invulnerable_turns > 0:
                combatant.invulnerable_turns -= 1

            # Dispatch ON_TURN_START passives (regen, etc.)
            turn_start_handler = PASSIVE_DISPATCH.get(TriggerCondition.ON_TURN_START)
            if turn_start_handler:
                for passive in self._get_all_passives(combatant, TriggerCondition.ON_TURN_START):
                    pctx = PassiveContext(state=state, owner=combatant)
                    turn_start_handler(passive, pctx)

            # Handle charge-up: if charging, tick down and fire or continue
            if combatant.charge_turns_remaining > 0:
                state = self._process_charge_tick(state, combatant)
            elif combatant.is_player:
                decision = player_decisions.get(combatant_id)
                if decision:
                    state = self._resolve_player_turn(state, combatant_id, decision)
            else:
                template_id = combatant_id.rsplit("_", 1)[0]
                template = enemy_templates.get(template_id)
                if template:
                    state = self._resolve_enemy_turn(state, combatant_id, template)

            state = self._check_combat_end(state)

        if not state.is_finished:
            state = self._end_of_round_status_tick(state)
            state = self._check_combat_end(state)

        return state

    def create_enemy_instance(
        self,
        template: EnemyTemplate,
        enemy_level: int,
        instance_id: str | None = None,
    ) -> EnemyInstance:
        """Create a concrete enemy from a template at a given level.

        Enemy stats come from budget allocation, then get amplified by
        equipment through the same Layer 3 scaling players use.
        """
        base_stats = calculate_enemy_stats(
            enemy_level, template.budget_multiplier, template.stat_distribution
        )

        # Apply equipment scaling (same Layer 3 system as players)
        equipped_items = [
            self.items[eid] for eid in template.equipment if eid in self.items
        ]
        effective_stats = calculate_effective_stats(base_stats, equipped_items, [])

        hp = calculate_enemy_hp(
            enemy_level, template.budget_multiplier, template.base_hp, template.hp_per_budget
        )

        return EnemyInstance(
            template_id=template.id,
            name=instance_id if instance_id else template.name,
            level=enemy_level,
            stats=effective_stats,
            max_hp=hp,
            current_hp=hp,
            abilities=list(template.abilities),
            equipment=list(template.equipment),
            action_table=template.action_table,
            target_preference=template.target_preference,
            budget_multiplier=template.budget_multiplier,
            gold_multiplier=template.gold_multiplier,
            xp_multiplier=template.xp_multiplier,
        )

    # --- In-Combat Item Use ---

    def use_combat_item(
        self,
        state: CombatState,
        actor_id: str,
        target_id: str,
        item: Item,
    ) -> CombatState:
        """Apply a consumable item's healing effect during combat.

        Low-level helper: validates the item, applies healing to the
        target combatant, and emits a HEALING event.  Does NOT emit
        ITEM_USED, track consumed_items, or touch the stash — callers
        handle those concerns.
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

        # Stat tonic: apply combat-duration stat buff
        if item.combat_stat_buff:
            status = StatusEffect(
                id=f"tonic_{item.id}",
                name=f"{item.name} buff",
                stat_modifiers=dict(item.combat_stat_buff),
                rounds_remaining=999,  # lasts entire combat
                source_id=actor_id,
            )
            target.active_statuses.append(status)
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.STATUS_APPLIED,
                    round_number=state.round_number,
                    actor_id=actor_id,
                    target_id=target_id,
                    details={
                        "status_id": status.id,
                        "status_name": status.name,
                        "modifiers": item.combat_stat_buff,
                    },
                )
            )

        return state

    def _resolve_item_action(
        self,
        state: CombatState,
        actor_id: str,
        action: CombatAction,
    ) -> CombatState:
        """Resolve a consumable item use as a proper combat action.

        Called during turn order just like ability resolution.  Emits
        ITEM_USED, applies the item's healing via use_combat_item(),
        and records the item in consumed_items for stash removal.
        """
        actor = state.get_combatant(actor_id)
        if actor is None or not actor.is_alive:
            return state

        item_id = action.item_id
        if item_id is None:
            return state

        item = self.items.get(item_id)
        if item is None or not item.is_consumable:
            return state

        target_id = action.target_ids[0] if action.target_ids else actor_id
        target = state.get_combatant(target_id)
        if target is None or not target.is_alive:
            return state

        # Emit the action declaration event
        state.log.append(
            CombatEvent(
                event_type=CombatEventType.ITEM_USED,
                round_number=state.round_number,
                actor_id=actor_id,
                target_id=target_id,
                details={"item_id": item_id, "item_name": item.name},
            )
        )

        # Apply healing
        state = self.use_combat_item(state, actor_id, target_id, item)

        # Track for stash removal by session
        state.consumed_items.append(item_id)

        return state

    # --- Turn Resolution ---

    def _is_taunt_valid_ability(self, ability_id: str) -> bool:
        """Check if an ability is usable while taunted (deals damage to enemies)."""
        ability = self.abilities.get(ability_id)
        if ability is None:
            return False
        has_damage = any(e.base_damage > 0 for e in ability.effects)
        targets_enemy = ability.target in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES)
        return has_damage and targets_enemy

    def _enforce_taunt_action(
        self,
        action: CombatAction,
        combatant_id: str,
        living_taunters: list[str],
    ) -> CombatAction:
        """Enforce taunt restrictions on a single action. Safety net for TUI/agent."""
        if action.is_windup_push:
            return action
        if action.item_id is not None or not self._is_taunt_valid_ability(action.ability_id):
            return CombatAction(
                actor_id=combatant_id,
                ability_id="basic_attack",
                target_ids=[living_taunters[0]],
            )
        ability = self.abilities.get(action.ability_id)
        if ability and ability.target == TargetType.SINGLE_ENEMY:
            if not any(tid in living_taunters for tid in action.target_ids):
                return action.model_copy(update={"target_ids": [living_taunters[0]]})
        return action

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

        # Taunt enforcement: taunted players must attack a taunter
        if combatant.taunted_by:
            living_taunters = [
                tid for tid in combatant.taunted_by
                if (t := state.get_combatant(tid)) is not None and t.is_alive
            ]
            if living_taunters:
                if decision.cheat_survive == CheatSurviveChoice.SURVIVE:
                    decision = PlayerTurnDecision(
                        combatant_id=combatant_id,
                        cheat_survive=CheatSurviveChoice.NORMAL,
                        primary_action=CombatAction(
                            actor_id=combatant_id,
                            ability_id="basic_attack",
                            target_ids=[living_taunters[0]],
                        ),
                    )
                else:
                    if decision.primary_action:
                        decision.primary_action = self._enforce_taunt_action(
                            decision.primary_action, combatant_id, living_taunters,
                        )
                    decision.cheat_extra_actions = [
                        self._enforce_taunt_action(a, combatant_id, living_taunters)
                        for a in decision.cheat_extra_actions
                    ]
                    decision.bonus_actions = [
                        self._enforce_taunt_action(a, combatant_id, living_taunters)
                        for a in decision.bonus_actions
                    ]

        # Pre-calculate speed bonus before any actions resolve.
        # This ensures cheat kills don't retroactively remove the bonus.
        speed_bonus = 0
        if decision.cheat_survive != CheatSurviveChoice.SURVIVE:
            slowest_enemy_spd = min(
                (e.effective_stats.SPD for e in state.living_enemies),
                default=0,
            )
            speed_bonus = calculate_speed_bonus(
                combatant.effective_stats.SPD, slowest_enemy_spd,
            )

        # Cheat/Survive resolution
        match decision.cheat_survive:
            case CheatSurviveChoice.SURVIVE:
                if combatant.cheat_debt > 0:
                    combatant.cheat_debt = max(
                        0, combatant.cheat_debt - CHEAT_DEBT_RECOVERY_PER_TURN
                    )
                survive_action = CombatAction(
                    actor_id=combatant_id,
                    ability_id="survive",
                    target_ids=[combatant_id],
                )
                state = self._resolve_action(state, combatant_id, survive_action)
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

                # Primary action (windup → start charge, else resolve normally)
                if decision.primary_action:
                    state = self._resolve_player_primary(
                        state, combatant_id, decision.primary_action,
                    )

                # Extra actions from Cheat — use individually chosen actions
                for i in range(actions_to_spend):
                    if state.is_finished:
                        break
                    combatant = state.get_combatant(combatant_id)
                    if combatant is None or not combatant.is_alive:
                        break
                    if i < len(decision.cheat_extra_actions):
                        action = decision.cheat_extra_actions[i]
                        state = self._resolve_extra_action(
                            state, combatant_id, action,
                        )
                    elif decision.primary_action and decision.primary_action.item_id is None:
                        # Fallback: repeat primary if no extra actions specified
                        # (item actions are not repeatable — each use consumes a copy)
                        state = self._resolve_extra_action_fallback(
                            state, combatant_id, decision.primary_action,
                        )

            case CheatSurviveChoice.NORMAL:
                combatant.is_surviving = False
                if combatant.cheat_debt > 0:
                    combatant.cheat_debt = max(
                        0, combatant.cheat_debt - CHEAT_DEBT_RECOVERY_PER_TURN
                    )

                if decision.primary_action:
                    state = self._resolve_player_primary(
                        state, combatant_id, decision.primary_action,
                    )

        # Speed bonus actions (pre-calculated at turn start so cheat kills don't erase it)
        if speed_bonus > 0:
            for i in range(speed_bonus):
                if state.is_finished:
                    break
                combatant = state.get_combatant(combatant_id)
                if combatant is None or not combatant.is_alive:
                    break
                if i < len(decision.bonus_actions):
                    action = decision.bonus_actions[i]
                    state = self._resolve_extra_action(
                        state, combatant_id, action, is_speed_bonus=True,
                    )
                elif decision.primary_action and decision.primary_action.item_id is None:
                    # Fallback: repeat primary with auto-retargeting
                    state = self._resolve_extra_action_fallback(
                        state, combatant_id, decision.primary_action,
                        is_speed_bonus=True,
                    )

        return state

    def _pick_living_targets(
        self, ability_id: str, state: CombatState, actor_id: str,
    ) -> list[str]:
        """Auto-pick targets for speed bonus actions. Respects taunt."""
        ability = self.abilities.get(ability_id)
        actor = state.get_combatant(actor_id)
        if not ability or not actor:
            return []

        if actor.is_player:
            enemies = state.living_enemies
            allies = state.living_players
        else:
            enemies = state.living_players
            allies = state.living_enemies

        if ability.target in (TargetType.SINGLE_ENEMY,):
            # Taunted: force-target a taunter if possible
            if actor.taunted_by:
                taunters = [e for e in enemies if e.id in actor.taunted_by]
                if taunters:
                    return [taunters[0].id]
            return [enemies[0].id] if enemies else []
        elif ability.target == TargetType.ALL_ENEMIES:
            return [e.id for e in enemies]
        elif ability.target == TargetType.SELF:
            return [actor_id]
        elif ability.target == TargetType.SINGLE_ALLY:
            return [allies[0].id] if allies else [actor_id]
        elif ability.target == TargetType.ALL_ALLIES:
            return [a.id for a in allies]
        return [enemies[0].id] if enemies else []

    def _resolve_player_primary(
        self, state: CombatState, combatant_id: str, action: CombatAction,
    ) -> CombatState:
        """Resolve a player's primary action, routing windup abilities to charge."""
        ability = self.abilities.get(action.ability_id)
        if ability and ability.windup_turns > 0:
            combatant = state.get_combatant(combatant_id)
            if combatant is not None:
                state = self._start_charge(
                    state, combatant, action.ability_id,
                    action.target_ids, ability.windup_turns,
                )
                if ability.cooldown > 0:
                    combatant.cooldowns[action.ability_id] = ability.cooldown
        else:
            state = self._resolve_action(state, combatant_id, action)
        return state

    def _resolve_extra_action(
        self, state: CombatState, combatant_id: str, action: CombatAction,
        is_speed_bonus: bool = False,
    ) -> CombatState:
        """Resolve a cheat extra or bonus action, handling windup push."""
        combatant = state.get_combatant(combatant_id)
        if combatant is None or not combatant.is_alive:
            return state

        # Windup push: accelerate an active charge by 1 turn
        if action.is_windup_push and combatant.charge_turns_remaining > 0:
            return self._process_charge_tick(state, combatant)

        # Normal action resolution
        return self._resolve_action(
            state, combatant_id, action, is_speed_bonus=is_speed_bonus,
        )

    def _resolve_extra_action_fallback(
        self, state: CombatState, combatant_id: str, primary: CombatAction,
        is_speed_bonus: bool = False,
    ) -> CombatState:
        """Fallback for extra/bonus actions: push windup if charging, else repeat primary."""
        combatant = state.get_combatant(combatant_id)
        if combatant is None or not combatant.is_alive:
            return state

        # If currently charging, auto-push the windup forward
        if combatant.charge_turns_remaining > 0:
            return self._process_charge_tick(state, combatant)

        # Otherwise repeat primary with auto-retargeting
        retargeted = primary.model_copy(update={
            "target_ids": self._pick_living_targets(
                primary.ability_id, state, combatant_id,
            ),
        })
        return self._resolve_action(
            state, combatant_id, retargeted, is_speed_bonus=is_speed_bonus,
        )

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
            # Skip pre-rolling for enemies that are charging or have a pre-set intent
            if enemy.charge_turns_remaining > 0 or enemy.pending_action is not None:
                continue
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

        # Check if the selected ability has a windup — start charge instead
        ability = self.abilities.get(action.ability_id)
        if ability and ability.windup_turns > 0:
            state = self._start_charge(
                state, combatant, action.ability_id,
                action.target_ids, ability.windup_turns,
            )
            # Set cooldown immediately so it can't be re-selected next turn
            if ability.cooldown > 0:
                combatant.cooldowns[action.ability_id] = ability.cooldown
        else:
            state = self._resolve_action(state, combatant_id, action)

        # Speed bonus actions for enemies
        # Suppress bonus on cooldown abilities (would silently fail) or surviving stance
        suppress_bonus = ability is not None and (
            ability.cooldown > 0
            or any(eff.grants_surviving for eff in ability.effects)
        )
        if not suppress_bonus:
            slowest_player_spd = min(
                (p.effective_stats.SPD for p in state.living_players),
                default=0,
            )
            bonus = calculate_speed_bonus(combatant.effective_stats.SPD, slowest_player_spd)
            if bonus > 0:
                for _ in range(bonus):
                    if state.is_finished:
                        break
                    combatant = state.get_combatant(combatant_id)
                    if combatant is None or not combatant.is_alive:
                        break
                    # If charging (windup primary), push the charge forward
                    if combatant.charge_turns_remaining > 0:
                        state = self._process_charge_tick(state, combatant)
                        continue
                    retargeted = action.model_copy(update={
                        "target_ids": self._pick_living_targets(
                            action.ability_id, state, combatant_id,
                        ),
                    })
                    state = self._resolve_action(
                        state, combatant_id, retargeted, is_speed_bonus=True,
                    )

        # Decrement cooldowns
        for ability_key in list(combatant.cooldowns.keys()):
            if combatant.cooldowns[ability_key] > 0:
                combatant.cooldowns[ability_key] -= 1

        return state

    # --- Mid-Combat Spawning ---

    def _spawn_enemies(
        self,
        state: CombatState,
        template_id: str,
        count: int,
        level: int,
        event_type: CombatEventType = CombatEventType.ENEMY_SPAWNED,
        summoner_id: str = "",
    ) -> list[CombatantState]:
        """Spawn new enemy combatants mid-combat.

        Creates EnemyInstance(s) from the template, converts to CombatantState,
        appends to state.enemy_combatants. Returns the new combatants.
        """
        if template_id not in self.enemy_registry:
            return []

        template = self.enemy_registry[template_id]
        spawned: list[CombatantState] = []

        # Count existing enemies with this template for unique IDs
        existing_count = sum(
            1 for c in state.enemy_combatants if c.id.startswith(f"{template_id}_")
        )

        for i in range(count):
            instance = self.create_enemy_instance(
                template, level, instance_id=f"{template_id}_{existing_count + i}"
            )
            combatant = CombatantState(
                id=instance.name,
                is_player=False,
                level=instance.level,
                current_hp=instance.current_hp,
                max_hp=instance.max_hp,
                base_stats=instance.stats,
                equipment_stats=instance.stats,
                effective_stats=instance.stats,
                ability_ids=list(instance.abilities),
            )
            state.enemy_combatants.append(combatant)
            spawned.append(combatant)

            state.log.append(
                CombatEvent(
                    event_type=event_type,
                    round_number=state.round_number,
                    actor_id=summoner_id,
                    target_id=combatant.id,
                    details={"template_id": template_id, "level": level},
                )
            )

        return spawned

    # --- Charge-Up (Windup) Resolution ---

    def _process_charge_tick(
        self, state: CombatState, combatant: CombatantState
    ) -> CombatState:
        """Handle a charging combatant's turn: tick down, fire when ready."""
        combatant.charge_turns_remaining -= 1

        if combatant.charge_turns_remaining > 0:
            # Still charging — log and skip turn
            state.log.append(
                CombatEvent(
                    event_type=CombatEventType.CHARGE_CONTINUE,
                    round_number=state.round_number,
                    actor_id=combatant.id,
                    ability_id=combatant.charging_ability_id or "",
                    details={"turns_remaining": combatant.charge_turns_remaining},
                )
            )
            return state

        # Charge complete — fire the ability
        ability_id = combatant.charging_ability_id or ""
        target_ids = list(combatant.charging_target_ids)

        # Clear charge state
        combatant.charging_ability_id = None
        combatant.charging_target_ids = []
        combatant.charge_turns_remaining = 0

        state.log.append(
            CombatEvent(
                event_type=CombatEventType.CHARGE_RELEASE,
                round_number=state.round_number,
                actor_id=combatant.id,
                ability_id=ability_id,
            )
        )

        # Taunt redirect: charged attack gets aimed at taunter(s)
        ability = self.abilities.get(ability_id)
        if ability and combatant.taunted_by:
            living_taunters = [
                tid for tid in combatant.taunted_by
                if (t := state.get_combatant(tid)) is not None and t.is_alive
            ]
            if living_taunters and ability.target == TargetType.SINGLE_ENEMY:
                target_ids = [living_taunters[0]]

        # Retarget if original targets are dead
        if ability:
            living_targets = [tid for tid in target_ids if (t := state.get_combatant(tid)) and t.is_alive]
            if not living_targets:
                # Retarget to any living enemy (from charger's perspective)
                if combatant.is_player:
                    living_targets = [e.id for e in state.living_enemies]
                else:
                    living_targets = [p.id for p in state.living_players]

            if living_targets:
                action = CombatAction(
                    actor_id=combatant.id,
                    ability_id=ability_id,
                    target_ids=living_targets,
                )
                state = self._resolve_action(state, combatant.id, action)

        return state

    def _start_charge(
        self, state: CombatState, combatant: CombatantState,
        ability_id: str, target_ids: list[str], windup_turns: int,
    ) -> CombatState:
        """Begin a charge-up: lock in ability and targets, set timer."""
        combatant.charging_ability_id = ability_id
        combatant.charging_target_ids = target_ids
        combatant.charge_turns_remaining = windup_turns

        state.log.append(
            CombatEvent(
                event_type=CombatEventType.CHARGE_START,
                round_number=state.round_number,
                actor_id=combatant.id,
                ability_id=ability_id,
                details={"windup_turns": windup_turns},
            )
        )
        return state

    # _resolve_action through _apply_secondary_effect live in EffectPipelineMixin
    # (effect_pipeline.py). Methods below are helpers used by the mixin via self.

    # --- Status Tick ---

    def _tick_statuses(self, state: CombatState) -> CombatState:
        """Round start: reset per-round flags, derive state from active statuses."""
        living_ids = {c.id for c in state.all_combatants if c.is_alive}

        for combatant in state.all_combatants:
            if not combatant.is_alive:
                continue

            if state.round_number > 1:
                self._evaluate_round_boundary_passives(state, combatant)

            # Reset per-round flags, re-derive from active statuses
            combatant.frenzy_stacks = 0
            combatant.dealt_damage_this_round = False
            combatant.is_surviving = False
            combatant.is_marked = any(
                s.grants_mark for s in combatant.active_statuses
            )

            # Taunted: clean dead sources, derive taunted_by list
            combatant.active_statuses = [
                s for s in combatant.active_statuses
                if not s.grants_taunted or s.source_id in living_ids
            ]
            combatant.taunted_by = [
                s.source_id for s in combatant.active_statuses
                if s.grants_taunted
            ]

            self._evaluate_conditional_passives(state, combatant)
            self._recalculate_combat_stats(combatant)

        return state

    def _end_of_round_status_tick(self, state: CombatState) -> CombatState:
        """End of round: tick DOTs, decrement durations, expire statuses."""
        living_ids = {c.id for c in state.all_combatants if c.is_alive}

        for combatant in state.all_combatants:
            if not combatant.is_alive:
                continue

            self._tick_status_effects(state, combatant)

            # Re-derive flags after potential expiry
            combatant.active_statuses = [
                s for s in combatant.active_statuses
                if not s.grants_taunted or s.source_id in living_ids
            ]
            combatant.taunted_by = [
                s.source_id for s in combatant.active_statuses
                if s.grants_taunted
            ]
            combatant.is_marked = any(
                s.grants_mark for s in combatant.active_statuses
            )

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

