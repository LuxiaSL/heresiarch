"""Auto-battle mixin for CombatScreen.

Replays decisions from a matching historical encounter record.
Validates and retargets actions against the current combat state.
"""

from __future__ import annotations

from heresiarch.engine.formulas import calculate_speed_bonus
from heresiarch.engine.models.abilities import TargetType
from heresiarch.engine.models.battle_record import EncounterRecord, RoundRecord
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatState,
    PlayerTurnDecision,
)


class AutoBattleMixin:
    """Mixin providing auto-battle replay for CombatScreen.

    Expects the host class to provide:
    - _auto_record, _auto_active, _auto_round_index, _pre_auto_verbose (state)
    - _verbose, _phase, _claimed_items, _decisions (screen state)
    - _encounter_record (recording state)
    - app (Textual app with combat_state, run_state, game_data)
    - _execute_round(), _start_planning(), query_one() (screen methods)
    """

    def _find_matching_record(self, run) -> EncounterRecord | None:
        """Find the most recent victory against the same enemy group."""
        if self._encounter_record is None:
            return None
        current_templates = sorted(self._encounter_record.enemy_template_ids)
        for encounter in reversed(run.battle_record.encounters):
            if (
                encounter.was_victory
                and sorted(encounter.enemy_template_ids) == current_templates
                and encounter.rounds
            ):
                return encounter
        return None

    def action_auto_battle(self) -> None:
        """Toggle auto-battle mode."""
        from heresiarch.tui.screens.combat import CombatPhase

        if self._auto_active:
            self._disable_auto("Auto-battle disabled")
            return

        if self._auto_record is None:
            return

        planning_phases = (
            CombatPhase.PLANNING_CHEAT_SURVIVE,
            CombatPhase.PLANNING_CHEAT_AP,
            CombatPhase.PLANNING_ACTION_MENU,
            CombatPhase.PLANNING_ABILITY,
            CombatPhase.PLANNING_TARGET,
            CombatPhase.PLANNING_ITEM,
            CombatPhase.PLANNING_ITEM_TARGET,
            CombatPhase.PLANNING_CHEAT_ACTION,
            CombatPhase.PLANNING_CHEAT_TARGET,
            CombatPhase.PLANNING_PARTIAL,
            CombatPhase.PLANNING_CONFIRM,
        )
        if self._phase not in planning_phases:
            return

        combat = self.app.combat_state
        if combat is None:
            return

        self._auto_active = True
        self._auto_round_index = combat.round_number
        self._pre_auto_verbose = self._verbose
        self._verbose = False

        from textual.widgets import RichLog

        log = self.query_one("#combat-log", RichLog)
        log.write("[bold #88ccbb]Auto-battle enabled[/bold #88ccbb]")

        self._auto_execute_next_round()

    def _disable_auto(self, reason: str) -> None:
        """Turn off auto-battle and restore previous settings."""
        from textual.widgets import RichLog

        self._auto_active = False
        self._verbose = self._pre_auto_verbose
        log = self.query_one("#combat-log", RichLog)
        log.write(f"[dim]{reason}[/dim]")

    def _auto_execute_next_round(self) -> None:
        """Build decisions from the recorded round and execute."""
        combat = self.app.combat_state
        if combat is None or self._auto_record is None:
            self._disable_auto("Auto-battle disabled — no combat state")
            self._start_planning()
            return

        if self._auto_round_index >= len(self._auto_record.rounds):
            self._disable_auto("Auto-battle disabled — strategy exhausted")
            self._start_planning()
            return

        round_record = self._auto_record.rounds[self._auto_round_index]
        self._auto_round_index += 1

        self._claimed_items = []
        self._decisions = self._build_auto_decisions(round_record, combat)

        self._execute_round()

    def _build_auto_decisions(
        self, round_record: RoundRecord, combat: CombatState,
    ) -> dict[str, PlayerTurnDecision]:
        """Build validated decisions from a recorded round."""
        decisions: dict[str, PlayerTurnDecision] = {}
        living_enemy_ids = [e.id for e in combat.living_enemies]
        living_player_ids = [p.id for p in combat.living_players]

        for player in combat.living_players:
            recorded = round_record.player_decisions.get(player.id)
            if recorded is None:
                decisions[player.id] = self._make_fallback_decision(
                    player.id, living_enemy_ids,
                )
                continue
            decisions[player.id] = self._validate_auto_decision(
                recorded, player, combat, living_enemy_ids, living_player_ids,
            )

        return decisions

    @staticmethod
    def _make_fallback_decision(
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

    def _validate_auto_decision(
        self, recorded: PlayerTurnDecision, player, combat: CombatState,
        living_enemy_ids: list[str], living_player_ids: list[str],
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
        primary = self._validate_auto_action(
            recorded.primary_action, cid, player, combat,
            living_enemy_ids, living_player_ids,
        )

        # Validate cheat extra actions
        cheat_extras: list[CombatAction] = []
        if cs == CheatSurviveChoice.CHEAT and cheat_actions > 0:
            for action in recorded.cheat_extra_actions[:cheat_actions]:
                cheat_extras.append(self._validate_auto_action(
                    action, cid, player, combat,
                    living_enemy_ids, living_player_ids,
                ))
            fallback_target = living_enemy_ids[0] if living_enemy_ids else cid
            while len(cheat_extras) < cheat_actions:
                cheat_extras.append(CombatAction(
                    actor_id=cid, ability_id="basic_attack",
                    target_ids=[fallback_target],
                ))

        # Validate bonus actions — recalculate SPD bonus for current combat
        bonus: list[CombatAction] = []
        if cs != CheatSurviveChoice.SURVIVE:
            slowest_enemy_spd = min(
                (e.effective_stats.SPD for e in combat.living_enemies), default=0,
            )
            spd_bonus = calculate_speed_bonus(
                player.effective_stats.SPD, slowest_enemy_spd,
            )
            if spd_bonus > 0:
                for action in recorded.bonus_actions[:spd_bonus]:
                    bonus.append(self._validate_auto_action(
                        action, cid, player, combat,
                        living_enemy_ids, living_player_ids,
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

    def _validate_auto_action(
        self, recorded_action: CombatAction | None, cid: str, player,
        combat: CombatState, living_enemy_ids: list[str],
        living_player_ids: list[str],
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
            run = self.app.run_state
            available = list(run.party.stash) if run else []
            for claimed in self._claimed_items:
                try:
                    available.remove(claimed)
                except ValueError:
                    pass
            if recorded_action.item_id in available:
                self._claimed_items.append(recorded_action.item_id)
                targets = self._retarget(
                    recorded_action.target_ids, living_player_ids,
                )
                return CombatAction(
                    actor_id=cid, ability_id="use_item",
                    item_id=recorded_action.item_id, target_ids=targets,
                )
            return fallback

        ability_id = recorded_action.ability_id
        ability = self.app.game_data.abilities.get(ability_id)
        if ability is None:
            return fallback

        if ability_id not in player.ability_ids:
            return fallback

        cd = player.cooldowns.get(ability_id, 0)
        if cd > 0:
            return fallback

        targets = self._retarget_for_ability(
            ability, recorded_action.target_ids, cid, combat,
            living_enemy_ids, living_player_ids,
        )
        return CombatAction(actor_id=cid, ability_id=ability_id, target_ids=targets)

    @staticmethod
    def _retarget(
        recorded_targets: list[str], living_ids: list[str],
    ) -> list[str]:
        """Remap recorded target IDs to living combatants."""
        if not living_ids:
            return list(recorded_targets)
        valid = [tid for tid in recorded_targets if tid in living_ids]
        return valid if valid else [living_ids[0]]

    @staticmethod
    def _retarget_for_ability(
        ability, recorded_targets: list[str], cid: str,
        combat: CombatState, living_enemy_ids: list[str],
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
            case TargetType.SINGLE_ENEMY:
                valid = [t for t in recorded_targets if t in living_enemy_ids]
                return valid if valid else ([living_enemy_ids[0]] if living_enemy_ids else [cid])
            case TargetType.SINGLE_ALLY:
                valid = [t for t in recorded_targets if t in living_player_ids]
                return valid if valid else ([living_player_ids[0]] if living_player_ids else [cid])
            case _:
                valid = [t for t in recorded_targets if t in living_enemy_ids]
                return valid if valid else ([living_enemy_ids[0]] if living_enemy_ids else [cid])
