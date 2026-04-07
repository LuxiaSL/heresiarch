"""Enemy AI: action table evaluation, condition checking, target selection."""

from __future__ import annotations

import random

from heresiarch.engine.models.abilities import Ability, TargetType
from heresiarch.engine.models.combat_state import CombatantState, CombatState
from heresiarch.engine.models.enemies import ActionCondition, ActionWeight, EnemyTemplate


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
        table = enemy_template.action_table

        active_weights = list(table.base_weights)

        for condition in table.conditions:
            if self.evaluate_condition(condition, enemy, combat_state):
                active_weights = list(condition.weight_overrides)

        active_weights = self._filter_cooldowns(active_weights, enemy)

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
                for player in combat_state.living_players:
                    if player.is_taunting:
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

            case _:
                return False

    def select_target(
        self,
        enemy_template: EnemyTemplate,
        combat_state: CombatState,
        ability: Ability | None,
    ) -> list[str]:
        """Select target(s) based on ability type and enemy preference.

        Taunt overrides single-target attacks.
        """
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

        taunting = [p for p in living_players if p.is_taunting]
        if taunting:
            return [taunting[0].id]

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
