"""Auto-battle mixin for CombatScreen.

Replays decisions from a matching historical encounter record. The
validation/retargeting logic lives in engine/replay.py (shared with
GameSession.auto_battle_round); this mixin only wires it into the
screen's planning/execution flow.
"""

from __future__ import annotations

from heresiarch.engine import replay
from heresiarch.engine.models.battle_record import EncounterRecord, RoundRecord
from heresiarch.engine.models.combat_state import (
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
        return replay.find_matching_record(
            run.battle_record.encounters,
            self._encounter_record.enemy_template_ids,
        )

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
        run = self.app.run_state
        stash = list(run.party.stash) if run else []
        return replay.build_replay_decisions(
            round_record, combat, self.app.game_data.abilities,
            stash, self._claimed_items,
        )

    @staticmethod
    def _make_fallback_decision(
        combatant_id: str, living_enemy_ids: list[str],
    ) -> PlayerTurnDecision:
        """Create a safe default: NORMAL + basic_attack on first living enemy."""
        return replay.make_fallback_decision(combatant_id, living_enemy_ids)

    def _validate_auto_decision(
        self, recorded: PlayerTurnDecision, player, combat: CombatState,
        living_enemy_ids: list[str], living_player_ids: list[str],
    ) -> PlayerTurnDecision:
        """Validate a recorded decision against current combat state."""
        run = self.app.run_state
        stash = list(run.party.stash) if run else []
        return replay.validate_replay_decision(
            recorded, player, combat, living_enemy_ids, living_player_ids,
            self.app.game_data.abilities, stash, self._claimed_items,
        )

    def _validate_auto_action(
        self, recorded_action: CombatAction | None, cid: str, player,
        combat: CombatState, living_enemy_ids: list[str],
        living_player_ids: list[str],
    ) -> CombatAction:
        """Validate a single combat action, falling back to basic_attack if needed."""
        run = self.app.run_state
        stash = list(run.party.stash) if run else []
        return replay.validate_replay_action(
            recorded_action, cid, player, combat,
            living_enemy_ids, living_player_ids,
            self.app.game_data.abilities, stash, self._claimed_items,
        )

    @staticmethod
    def _retarget(
        recorded_targets: list[str], living_ids: list[str],
    ) -> list[str]:
        """Remap recorded target IDs to living combatants."""
        return replay.retarget(recorded_targets, living_ids)

    @staticmethod
    def _retarget_for_ability(
        ability, recorded_targets: list[str], cid: str,
        combat: CombatState, living_enemy_ids: list[str],
        living_player_ids: list[str],
    ) -> list[str]:
        """Retarget based on ability's target type."""
        return replay.retarget_for_ability(
            ability, recorded_targets, cid,
            living_enemy_ids, living_player_ids,
        )
