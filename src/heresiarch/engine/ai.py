"""Enemy AI: action table evaluation, condition checking, target selection."""

from __future__ import annotations

import random

from heresiarch.engine.models.abilities import Ability, AbilityCategory, TargetType
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatEventType,
    CombatantState,
    CombatState,
)
from heresiarch.engine.models.enemies import ActionCondition, ActionWeight, EnemyTemplate, RepeatMode
from heresiarch.engine.models.stats import StatType


class EnemyAI:
    """Resolves enemy action selection from action tables + game state conditions."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def select_action(
        self,
        enemy: CombatantState,
        enemy_template: EnemyTemplate,
        combat_state: CombatState,
        ability_registry: dict[str, Ability],
    ) -> tuple[str, list[str]]:
        """Select an action and targets for an enemy.

        Returns (ability_id, target_ids).

        1. Start with base weights from action table
        2. Evaluate each condition against combat state
        3. Last matching condition overrides weights
        4. Filter out abilities on cooldown
        5. Normalize weights, weighted random select
        6. Select targets based on ability + preference
        """
        # Taunted: must use a damaging ability targeting a taunter
        if enemy.taunted_by:
            living_taunters = [
                tid for tid in enemy.taunted_by
                if (t := combat_state.get_combatant(tid)) is not None and t.is_alive
            ]
            if living_taunters:
                damage_abilities = [
                    aid for aid in enemy.ability_ids
                    if aid in ability_registry
                    and any(e.base_damage > 0 for e in ability_registry[aid].effects)
                    and ability_registry[aid].target in (
                        TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES,
                    )
                    and enemy.cooldowns.get(aid, 0) == 0
                ]
                ability_id = self.rng.choice(damage_abilities) if damage_abilities else "basic_attack"
                ability = ability_registry.get(ability_id)
                if ability and ability.target == TargetType.ALL_ENEMIES:
                    return ability_id, [p.id for p in combat_state.living_players]
                return ability_id, [self.rng.choice(living_taunters)]

        table = enemy_template.action_table

        active_weights = list(table.base_weights)

        for condition in table.conditions:
            if self.evaluate_condition(condition, enemy, combat_state):
                active_weights = list(condition.weight_overrides)

        active_weights = self._filter_cooldowns(active_weights, enemy)
        active_weights = self._apply_history_modifiers(active_weights, enemy, combat_state)

        if not active_weights:
            return "basic_attack", self.select_target(
                enemy_template, combat_state, None
            )

        ability_id = self._weighted_select(active_weights)

        ability = ability_registry.get(ability_id)
        targets = self.select_target(enemy_template, combat_state, ability)

        return ability_id, targets

    def evaluate_condition(
        self,
        condition: ActionCondition,
        enemy: CombatantState,
        combat_state: CombatState,
    ) -> bool:
        """Check if a single condition is met."""
        match condition.condition_type:
            case "player_hp_below":
                for player in combat_state.living_players:
                    if player.max_hp > 0:
                        ratio = player.current_hp / player.max_hp
                        if ratio < condition.threshold:
                            return True
                return False

            case "self_hp_below":
                if enemy.max_hp > 0:
                    ratio = enemy.current_hp / enemy.max_hp
                    return ratio < condition.threshold
                return False

            case "player_post_cheat":
                for player in combat_state.living_players:
                    if player.cheat_debt > 0:
                        return True
                return False

            case "no_taunt_active":
                for e in combat_state.living_enemies:
                    if e.taunted_by:
                        return False
                return True

            case "party_low_res":
                for player in combat_state.living_players:
                    if player.effective_stats.RES < condition.threshold * 100:
                        return True
                return False

            case "ally_present":
                for other_enemy in combat_state.living_enemies:
                    if other_enemy.id != enemy.id:
                        return True
                return False

            case "ally_hp_below":
                for other_enemy in combat_state.living_enemies:
                    if other_enemy.id != enemy.id and other_enemy.max_hp > 0:
                        if other_enemy.current_hp / other_enemy.max_hp < condition.threshold:
                            return True
                return False

            case "no_damaged_allies":
                for other_enemy in combat_state.living_enemies:
                    if other_enemy.id != enemy.id:
                        if other_enemy.current_hp < other_enemy.max_hp:
                            return False
                return True

            case "last_standing":
                return len(combat_state.living_enemies) == 1

            # Mimic conditions: check what the player did last round
            case "player_last_used_physical":
                return self._player_last_action_was_physical(combat_state)

            case "player_last_used_magical":
                return self._player_last_action_was_magical(combat_state)

            case "player_last_used_survive":
                return self._player_last_action_was_survive(combat_state)

            case _:
                return False

    def select_target(
        self,
        enemy_template: EnemyTemplate,
        combat_state: CombatState,
        ability: Ability | None,
    ) -> list[str]:
        """Select target(s) based on ability type and enemy preference."""
        living_players = combat_state.living_players
        if not living_players:
            return []

        if ability and ability.target == TargetType.ALL_ENEMIES:
            return [p.id for p in living_players]

        if ability and ability.target == TargetType.SELF:
            return []

        if ability and ability.target in (TargetType.SINGLE_ALLY, TargetType.ALL_ALLIES):
            living_enemies = combat_state.living_enemies
            if ability.target == TargetType.ALL_ALLIES:
                return [e.id for e in living_enemies]
            if living_enemies:
                # For heals, prefer the most damaged ally
                if ability.category.value == "SUPPORT":
                    allies_excl_self = [e for e in living_enemies if e.id != enemy_template.id]
                    if allies_excl_self:
                        target = min(allies_excl_self, key=lambda e: e.current_hp / max(e.max_hp, 1))
                        return [target.id]
                return [self.rng.choice(living_enemies).id]
            return []

        match enemy_template.target_preference:
            case "lowest_def":
                target = min(living_players, key=lambda p: p.effective_stats.DEF)
                return [target.id]

            case "lowest_hp":
                target = min(living_players, key=lambda p: p.current_hp)
                return [target.id]

            case "post_cheat":
                in_debt = [p for p in living_players if p.cheat_debt > 0]
                if in_debt:
                    return [self.rng.choice(in_debt).id]
                return [self.rng.choice(living_players).id]

            case _:
                return [self.rng.choice(living_players).id]

    # --- Mimic condition helpers ---

    def _get_last_player_action(
        self, combat_state: CombatState, ability_registry: dict[str, Ability] | None = None,
    ) -> tuple[str, str | None]:
        """Find the most recent player action. Returns (ability_id, cheat_survive_choice).

        Scans log backwards for the last player ACTION_DECLARED event.
        Also checks for CHEAT_SURVIVE_DECISION to detect Survive.
        """
        last_ability_id = ""
        last_cs_choice: str | None = None
        player_ids = {p.id for p in combat_state.player_combatants}

        for event in reversed(combat_state.log):
            if event.actor_id not in player_ids:
                continue
            if event.event_type == CombatEventType.CHEAT_SURVIVE_DECISION and last_cs_choice is None:
                last_cs_choice = event.details.get("choice", "")
            if event.event_type == CombatEventType.ACTION_DECLARED and not last_ability_id:
                last_ability_id = event.ability_id
            if last_ability_id and last_cs_choice is not None:
                break

        return last_ability_id, last_cs_choice

    def _player_last_action_was_physical(self, combat_state: CombatState) -> bool:
        """True if the last player action used STR scaling (physical attack)."""
        ability_id, _ = self._get_last_player_action(combat_state)
        if not ability_id:
            return False
        # Check log for DAMAGE_DEALT events from this ability — scan for STR-scaled abilities
        # Simple heuristic: check if the ability is in offensive category with STR scaling
        # We don't have ability_registry here, so check the damage events
        for event in reversed(combat_state.log):
            if event.event_type == CombatEventType.DAMAGE_DEALT and event.ability_id == ability_id:
                return True  # any damage means it was an attack
            if event.event_type == CombatEventType.ACTION_DECLARED and event.ability_id == ability_id:
                break
        return False

    def _player_last_action_was_magical(self, combat_state: CombatState) -> bool:
        """True if the last player action was a non-damaging support/defensive ability."""
        ability_id, _ = self._get_last_player_action(combat_state)
        if not ability_id:
            return False
        # If the action didn't produce damage, it was support/magical/utility
        for event in reversed(combat_state.log):
            if event.event_type == CombatEventType.DAMAGE_DEALT and event.ability_id == ability_id:
                return False  # it dealt damage, so it's physical
            if event.event_type == CombatEventType.ACTION_DECLARED and event.ability_id == ability_id:
                return True  # found the action, no damage before it → non-damage action
        return False

    def _player_last_action_was_survive(self, combat_state: CombatState) -> bool:
        """True if the last player chose Survive as their cheat/survive decision."""
        _, cs_choice = self._get_last_player_action(combat_state)
        return cs_choice == "SURVIVE"

    def _count_prior_uses(
        self,
        ability_id: str,
        actor_id: str,
        combat_state: CombatState,
        mode: RepeatMode,
    ) -> int:
        """Count how many times an actor used an ability, per repeat mode.

        TOTAL: all uses across the entire fight.
        CONSECUTIVE: unbroken streak from the most recent action backwards.
        """
        count = 0
        for event in reversed(combat_state.log):
            if event.actor_id != actor_id:
                continue
            if event.event_type not in (CombatEventType.ACTION_DECLARED, CombatEventType.BONUS_ACTION):
                continue
            if event.ability_id == ability_id:
                count += 1
                if mode == RepeatMode.CONSECUTIVE:
                    continue  # keep counting the streak
            else:
                if mode == RepeatMode.CONSECUTIVE:
                    break  # streak broken
        return count

    def _rounds_since_last_use(
        self,
        ability_id: str,
        actor_id: str,
        combat_state: CombatState,
    ) -> int:
        """Count rounds since the actor last used this ability. -1 if never used."""
        for event in reversed(combat_state.log):
            if event.actor_id != actor_id:
                continue
            if event.event_type not in (CombatEventType.ACTION_DECLARED, CombatEventType.BONUS_ACTION):
                continue
            if event.ability_id == ability_id:
                return max(0, combat_state.round_number - event.round_number)
        return -1

    def _apply_history_modifiers(
        self,
        weights: list[ActionWeight],
        enemy: CombatantState,
        combat_state: CombatState,
    ) -> list[ActionWeight]:
        """Apply repeat_penalty decay and recency_bonus growth to weights."""
        adjusted: list[ActionWeight] = []
        for w in weights:
            effective_weight = w.weight

            # Repeat penalty: decay weight based on prior uses
            if w.repeat_penalty > 0:
                uses = self._count_prior_uses(w.ability_id, enemy.id, combat_state, w.repeat_mode)
                if uses > 0:
                    effective_weight *= (1.0 - w.repeat_penalty) ** uses

            # Recency bonus: grow weight based on rounds since last use
            if w.recency_bonus > 0:
                rounds_ago = self._rounds_since_last_use(w.ability_id, enemy.id, combat_state)
                if rounds_ago > 0:  # -1 (never used) doesn't boost
                    effective_weight *= (1.0 + w.recency_bonus) ** rounds_ago

            if effective_weight > 1e-6:
                adjusted.append(ActionWeight(
                    ability_id=w.ability_id,
                    weight=effective_weight,
                    repeat_penalty=w.repeat_penalty,
                    repeat_mode=w.repeat_mode,
                    recency_bonus=w.recency_bonus,
                ))
        return adjusted

    def _filter_cooldowns(
        self,
        weights: list[ActionWeight],
        enemy: CombatantState,
    ) -> list[ActionWeight]:
        """Remove abilities that are on cooldown."""
        return [
            w
            for w in weights
            if w.weight > 0 and enemy.cooldowns.get(w.ability_id, 0) <= 0
        ]

    def _weighted_select(self, weights: list[ActionWeight]) -> str:
        """Weighted random selection from action weights."""
        total = sum(w.weight for w in weights)
        if total <= 0:
            return weights[0].ability_id if weights else "basic_attack"

        roll = self.rng.random() * total
        cumulative = 0.0
        for w in weights:
            cumulative += w.weight
            if roll <= cumulative:
                return w.ability_id

        return weights[-1].ability_id
