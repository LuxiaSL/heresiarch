"""Game session: manages a single run's lifecycle with phase tracking.

Wraps the engine (GameLoop, CombatEngine, ShopEngine) and returns
summarized text views via the StateSummarizer. Validates that actions
are legal for the current game phase.
"""

from __future__ import annotations

import json
import random
from enum import Enum
from pathlib import Path
from typing import Any

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.formulas import (
    calculate_bonus_actions,
    calculate_buy_price,
    calculate_sell_price,
)
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.battle_record import EncounterRecord, RoundRecord
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEvent,
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.zone import ZoneTemplate
from heresiarch.engine.recruitment import (
    MAX_PARTY_SIZE,
    RecruitCandidate,
    RecruitmentEngine,
)
from heresiarch.engine.shop import ShopInventory

from . import summarizer as S


class Phase(str, Enum):
    SETUP = "SETUP"
    ZONE_SELECT = "ZONE_SELECT"
    IN_ZONE = "IN_ZONE"
    COMBAT = "COMBAT"
    POST_COMBAT = "POST_COMBAT"
    RECRUITING = "RECRUITING"
    DEAD = "DEAD"


class AgentError(Exception):
    """Raised for invalid agent actions (wrong phase, bad input, etc.)."""


# Phase -> which tools are allowed
_PHASE_TOOLS: dict[Phase, set[str]] = {
    Phase.SETUP: {
        "new_run", "lookup_job", "lookup_ability", "lookup_item",
        "lookup_enemy", "lookup_zone", "lookup_formula",
        "save_note", "read_notes", "save_run", "load_run", "list_saves", "save_run", "load_run", "list_saves",
    },
    Phase.ZONE_SELECT: {
        "new_run", "list_zones", "enter_zone", "party_status", "equip", "unequip",
        "swap_roster", "use_scroll", "use_consumable", "mc_swap_job",
        "get_battle_record", "get_run_summary",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
    Phase.IN_ZONE: {
        "new_run", "fight", "party_status", "equip", "unequip", "swap_roster",
        "use_scroll", "use_consumable", "shop_browse", "shop_buy",
        "shop_sell", "leave_zone", "get_zone_status", "get_battle_record",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
    Phase.COMBAT: {
        "submit_decisions", "get_combat_state",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
    Phase.POST_COMBAT: {
        "pick_loot",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
    Phase.RECRUITING: {
        "inspect_candidate", "recruit",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
    Phase.DEAD: {
        "get_battle_record", "get_run_summary", "new_run",
        "lookup_job", "lookup_ability", "lookup_item", "lookup_enemy",
        "lookup_zone", "lookup_formula", "get_state",
        "save_note", "read_notes", "save_run", "load_run", "list_saves",
    },
}


class GameSession:
    """Manages one run's lifecycle. All public methods return summary strings."""

    def __init__(
        self,
        game_data: GameData | None = None,
        data_path: Path | None = None,
        notes_path: Path | None = None,
    ):
        if game_data is not None:
            self.game_data = game_data
        elif data_path is not None:
            self.game_data = load_all(data_path)
        else:
            self.game_data = load_all(Path("data"))

        # Notes persistence
        self._notes_path = notes_path or (data_path or Path("data")).parent / "agent_notes.json"
        self._notes: dict[str, str] = self._load_notes()

        self.phase = Phase.SETUP
        self.run: RunState | None = None
        self.game_loop: GameLoop | None = None
        self.seed: int | None = None

        # Combat state
        self._combat_state: CombatState | None = None
        self._current_enemies: list[EnemyInstance] = []
        self._enemy_combatant_templates: dict[str, str] = {}  # combatant_id -> template_id
        self._round_events: list[CombatEvent] = []
        self._encounter_rounds: list[RoundRecord] = []
        self._encounter_decisions: dict[str, PlayerTurnDecision] = {}

        # Post-combat
        self._last_loot: LootResult | None = None
        self._last_combat_result: CombatResult | None = None

        # Recruitment
        self._current_candidate: RecruitCandidate | None = None

    def _require_phase(self, tool_name: str) -> None:
        """Raise AgentError if the tool isn't valid for the current phase."""
        allowed = _PHASE_TOOLS.get(self.phase, set())
        if tool_name not in allowed:
            available = sorted(allowed)
            raise AgentError(
                f"Cannot use '{tool_name}' during {self.phase.value} phase. "
                f"Available: {', '.join(available)}"
            )

    def _require_run(self) -> RunState:
        if self.run is None:
            raise AgentError("No active run. Use new_run first.")
        return self.run

    def _require_game_loop(self) -> GameLoop:
        if self.game_loop is None:
            raise AgentError("No active run. Use new_run first.")
        return self.game_loop

    def _autosave(self) -> None:
        """Auto-save after key state transitions. Best-effort, never raises."""
        if self.run is None:
            return
        try:
            self.save_run("autosave")
        except (AgentError, OSError):
            pass

    # ------------------------------------------------------------------
    # Run Management
    # ------------------------------------------------------------------

    def new_run(self, name: str, job_id: str, seed: int | None = None) -> str:
        """Start a new playthrough."""
        self._require_phase("new_run")

        if job_id not in self.game_data.jobs:
            available = ", ".join(sorted(self.game_data.jobs.keys()))
            raise AgentError(f"Unknown job: '{job_id}'. Available: {available}")

        self.seed = seed if seed is not None else random.randint(0, 2**31)
        rng = random.Random(self.seed)

        self.game_loop = GameLoop(game_data=self.game_data, rng=rng)
        run_id = f"agent_{self.seed}"
        self.run = self.game_loop.new_run(run_id, name, job_id)

        self.phase = Phase.ZONE_SELECT

        # Reset combat state
        self._combat_state = None
        self._current_enemies = []
        self._round_events = []

        self._autosave()
        available_zones = self.game_loop.get_available_zones(self.run)
        return (
            f"Run started! Seed: {self.seed}\n\n"
            + S.summarize_zone_select(self.run, available_zones, self.game_data)
        )

    def get_state(self) -> str:
        """Get current state summary, adapted to current phase."""
        run = self._require_run()

        match self.phase:
            case Phase.ZONE_SELECT:
                gl = self._require_game_loop()
                zones = gl.get_available_zones(run)
                return S.summarize_zone_select(run, zones, self.game_data)
            case Phase.IN_ZONE:
                return S.summarize_zone_status(run, self.game_data)
            case Phase.COMBAT:
                if self._combat_state:
                    return S.summarize_combat(
                        self._combat_state, run, self.game_data,
                        last_round_events=self._round_events,
                    )
                return "In combat but no combat state available."
            case Phase.POST_COMBAT:
                if self._last_loot and self._last_combat_result:
                    return S.summarize_post_combat(
                        run, self._last_loot, self._last_combat_result, self.game_data,
                    )
                return "Post-combat state."
            case Phase.RECRUITING:
                if self._current_candidate:
                    gl = self._require_game_loop()
                    level = gl.recruitment_engine.get_inspection_level(run.party.cha)
                    return S.summarize_recruitment(
                        self._current_candidate, level, run.party.cha,
                        run, self.game_data,
                    )
                return "Recruiting."
            case Phase.DEAD:
                return S.summarize_death(run, self.game_data)
            case _:
                return f"Phase: {self.phase.value}"

    # ------------------------------------------------------------------
    # Zone Navigation
    # ------------------------------------------------------------------

    def list_zones(self) -> str:
        """Show available zones."""
        self._require_phase("list_zones")
        run = self._require_run()
        gl = self._require_game_loop()
        zones = gl.get_available_zones(run)
        return S.summarize_zone_select(run, zones, self.game_data)

    def enter_zone(self, zone_id: str) -> str:
        """Enter a zone."""
        self._require_phase("enter_zone")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            self.run = gl.enter_zone(run, zone_id)
        except ValueError as e:
            raise AgentError(str(e)) from e

        self.phase = Phase.IN_ZONE
        self._autosave()
        return S.summarize_zone_status(self.run, self.game_data)

    def leave_zone(self) -> str:
        """Exit current zone."""
        self._require_phase("leave_zone")
        run = self._require_run()
        gl = self._require_game_loop()

        self.run = gl.leave_zone(run)
        self.phase = Phase.ZONE_SELECT
        self._autosave()

        zones = gl.get_available_zones(self.run)
        return S.summarize_zone_select(self.run, zones, self.game_data)

    def get_zone_status(self) -> str:
        """Show current zone progress."""
        self._require_phase("get_zone_status")
        run = self._require_run()
        return S.summarize_zone_status(run, self.game_data)

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def fight(self) -> str:
        """Start the next encounter."""
        self._require_phase("fight")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            enemies = gl.get_next_encounter(run)
        except ValueError as e:
            raise AgentError(str(e)) from e

        self._current_enemies = enemies

        # Get active party characters for combat
        characters = [
            run.party.characters[cid]
            for cid in run.party.active
            if cid in run.party.characters
        ]

        self._combat_state = gl.combat_engine.initialize_combat(characters, enemies)

        # Map combatant IDs to template IDs (enemies are created in same order)
        self._enemy_combatant_templates = {}
        for i, c in enumerate(self._combat_state.enemy_combatants):
            if i < len(enemies):
                self._enemy_combatant_templates[c.id] = enemies[i].template_id

        self._round_events = []
        self._encounter_rounds = []
        self.phase = Phase.COMBAT

        return S.summarize_combat(
            self._combat_state, run, self.game_data,
        )

    def submit_decisions(self, decisions: dict[str, Any]) -> str:
        """Submit one round of combat decisions for all player characters."""
        self._require_phase("submit_decisions")
        run = self._require_run()
        gl = self._require_game_loop()
        combat = self._combat_state
        if combat is None:
            raise AgentError("No active combat.")

        # Translate agent decisions into PlayerTurnDecision objects
        # NOTE: _parse_decisions may mutate self._combat_state via item use
        try:
            player_decisions = self._parse_decisions(decisions, combat)
        except (ValueError, KeyError) as e:
            raise AgentError(f"Invalid decisions: {e}") from e

        # Re-read combat state — item use during parsing may have changed HP
        combat = self._combat_state
        if combat is None:
            raise AgentError("Combat state lost during decision parsing.")

        # Build enemy template lookup for AI
        enemy_templates = {}
        for enemy in self._current_enemies:
            if enemy.template_id in self.game_data.enemies:
                enemy_templates[enemy.template_id] = self.game_data.enemies[enemy.template_id]

        # Snapshot pre-round events count to extract this round's events
        pre_event_count = len(combat.log)

        # Process the round
        new_combat = gl.combat_engine.process_round(
            combat, player_decisions, enemy_templates,
        )
        self._combat_state = new_combat

        # Extract this round's events
        self._round_events = new_combat.log[pre_event_count:]

        # Record round for battle history
        player_hp = {
            c.id: c.current_hp
            for c in new_combat.player_combatants
        }
        enemy_hp = {
            c.id: c.current_hp
            for c in new_combat.enemy_combatants
        }
        round_record = RoundRecord(
            round_number=new_combat.round_number,
            player_decisions=player_decisions,
            events=self._round_events,
            player_hp=player_hp,
            enemy_hp=enemy_hp,
        )
        self._encounter_rounds.append(round_record)

        # Check if combat is over
        if new_combat.is_finished:
            return self._resolve_combat(new_combat, run, gl)

        # Combat continues
        return S.summarize_combat(
            new_combat, run, self.game_data,
            last_round_events=self._round_events,
        )

    def get_combat_state(self) -> str:
        """Re-fetch current combat state."""
        self._require_phase("get_combat_state")
        run = self._require_run()
        if self._combat_state is None:
            raise AgentError("No active combat.")
        return S.summarize_combat(
            self._combat_state, run, self.game_data,
            last_round_events=self._round_events,
        )

    def _resolve_combat(
        self, combat: CombatState, run: RunState, gl: GameLoop,
    ) -> str:
        """Handle combat end: build result, resolve XP/loot, update phase."""
        # Build CombatResult from final combat state
        combat_result = self._build_combat_result(combat, run)
        self._last_combat_result = combat_result

        if not combat_result.player_won:
            # Defeat — format events BEFORE clearing combat state
            final_events = self._format_round_events()
            self._record_encounter(combat, combat_result, run)
            self.run = gl.handle_death(self.run or run)
            self._combat_state = None
            self.phase = Phase.DEAD
            self._autosave()
            return (
                final_events
                + "\n\n"
                + S.summarize_death(self.run, self.game_data)
            )

        # Victory: format events BEFORE clearing combat state
        final_events = self._format_round_events()

        new_run, loot = gl.resolve_combat_result(run, combat_result)
        self._last_loot = loot

        # Advance zone (increment encounter or overstay counter)
        new_run = gl.advance_zone(new_run)
        self.run = new_run

        # Record encounter AFTER run state is updated
        self._record_encounter(combat, combat_result, self.run)

        self._combat_state = None
        self.phase = Phase.POST_COMBAT
        self._autosave()

        return (
            final_events
            + "\n\n"
            + S.summarize_post_combat(self.run, loot, combat_result, self.game_data)
        )

    def _build_combat_result(
        self, combat: CombatState, run: RunState,
    ) -> CombatResult:
        """Build CombatResult from final CombatState."""
        surviving_ids = [c.id for c in combat.player_combatants if c.is_alive]
        surviving_hp = {c.id: c.current_hp for c in combat.player_combatants if c.is_alive}

        defeated_templates: list[str] = []
        defeated_budgets: list[float] = []
        for c in combat.enemy_combatants:
            if not c.is_alive:
                tmpl_id = self._enemy_combatant_templates.get(c.id, "")
                if tmpl_id:
                    defeated_templates.append(tmpl_id)
                    template = self.game_data.enemies.get(tmpl_id)
                    if template:
                        defeated_budgets.append(template.budget_multiplier)

        zone_level = 0
        if run.current_zone_id:
            zone = self.game_data.zones.get(run.current_zone_id)
            if zone:
                zone_level = zone.zone_level

        return CombatResult(
            player_won=combat.player_won or False,
            surviving_character_ids=surviving_ids,
            surviving_character_hp=surviving_hp,
            defeated_enemy_template_ids=defeated_templates,
            defeated_enemy_budget_multipliers=defeated_budgets,
            rounds_taken=combat.round_number,
            zone_level=zone_level,
            gold_stolen_by_enemies=combat.gold_stolen_by_enemies,
            gold_stolen_by_players=combat.gold_stolen_by_players,
        )

    def _record_encounter(
        self, combat: CombatState, result: CombatResult, run: RunState,
    ) -> None:
        """Record completed encounter in battle history."""
        zone_id = run.current_zone_id or ""
        encounter_idx = 0
        if run.zone_state:
            encounter_idx = run.zone_state.current_encounter_index

        # Compute damage totals from events
        total_dealt = 0
        total_taken = 0
        total_healing = 0
        deaths: list[str] = []
        player_ids = {c.id for c in combat.player_combatants}

        for event in combat.log:
            match event.event_type:
                case CombatEventType.DAMAGE_DEALT:
                    if event.actor_id in player_ids and not event.details.get("self_damage"):
                        total_dealt += event.value
                    elif event.target_id in player_ids:
                        total_taken += event.value
                case CombatEventType.HEALING:
                    if event.target_id in player_ids:
                        total_healing += event.value
                case CombatEventType.DEATH:
                    if event.target_id in player_ids:
                        deaths.append(event.target_id)
                case CombatEventType.DOT_TICK:
                    if event.target_id in player_ids:
                        total_taken += event.value
                    elif event.actor_id in player_ids:
                        total_dealt += event.value

        enemy_tmpl_ids = list(self._enemy_combatant_templates.values())
        record = EncounterRecord(
            zone_id=zone_id,
            encounter_index=encounter_idx,
            enemy_template_ids=enemy_tmpl_ids,
            rounds=self._encounter_rounds,
            result="victory" if result.player_won else "defeat",
            rounds_taken=result.rounds_taken,
            total_damage_dealt=total_dealt,
            total_damage_taken=total_taken,
            total_healing=total_healing,
            character_deaths=deaths,
        )

        # Add to run's battle record
        run_br = self.run or run
        new_encounters = list(run_br.battle_record.encounters) + [record]
        from heresiarch.engine.models.battle_record import BattleRecord
        new_br = BattleRecord(encounters=new_encounters)
        if self.run:
            self.run = self.run.model_copy(update={"battle_record": new_br})

    def _format_round_events(self) -> str:
        """Format the last round's events as text."""
        if not self._round_events or not self._combat_state:
            return ""
        lines: list[str] = []
        for event in self._round_events:
            rendered = S._render_combat_event(event, self._combat_state, self.game_data)
            if rendered:
                lines.append(rendered)
        return "\n".join(lines) if lines else ""

    def _parse_decisions(
        self,
        raw: dict[str, Any],
        combat: CombatState,
    ) -> dict[str, PlayerTurnDecision]:
        """Translate agent JSON decisions into PlayerTurnDecision objects.

        Supports "action": "use_item" with "item_id" and "target" fields.
        Using an item costs the character's primary action for the round.
        The item heal is applied to combat state and removed from stash
        before the round processes.
        """
        decisions: dict[str, PlayerTurnDecision] = {}

        # Validate all living players have decisions
        living_players = [c for c in combat.player_combatants if c.is_alive]
        living_ids = {c.id for c in living_players}

        for cid in raw:
            if cid not in living_ids:
                raise ValueError(
                    f"'{cid}' is not a living player combatant. "
                    f"Living: {', '.join(sorted(living_ids))}"
                )

        missing = living_ids - set(raw.keys())
        if missing:
            raise ValueError(
                f"Missing decisions for: {', '.join(sorted(missing))}. "
                f"All living characters need decisions."
            )

        for cid, dec in raw.items():
            combatant = combat.get_combatant(cid)
            if combatant is None:
                raise ValueError(f"Unknown combatant: {cid}")

            mode_str = dec.get("mode", "normal").upper()
            try:
                mode = CheatSurviveChoice(mode_str)
            except ValueError:
                raise ValueError(
                    f"{cid}: invalid mode '{mode_str}'. Use 'normal', 'cheat', or 'survive'."
                )

            # --- Survive: no action, just bank AP + reduce damage ---
            if mode == CheatSurviveChoice.SURVIVE:
                decisions[cid] = PlayerTurnDecision(
                    combatant_id=cid,
                    cheat_survive=CheatSurviveChoice.SURVIVE,
                )
                continue

            # --- Primary action: ability or item use ---
            action_id = dec.get("action")
            target_id = dec.get("target")
            primary_action = None

            if action_id == "use_item":
                # Item use costs the primary action
                self._apply_combat_item_use(cid, dec, combat)
            elif action_id:
                # Ability use
                if action_id not in combatant.ability_ids:
                    raise ValueError(
                        f"{cid}: doesn't know ability '{action_id}'. "
                        f"Available: {', '.join(combatant.ability_ids)}"
                    )
                cd = combatant.cooldowns.get(action_id, 0)
                if cd > 0:
                    raise ValueError(
                        f"{cid}: {action_id} is on cooldown ({cd} rounds remaining)"
                    )
                targets = [target_id] if target_id else []
                primary_action = CombatAction(
                    actor_id=cid,
                    ability_id=action_id,
                    target_ids=targets,
                )

            # --- Cheat extra actions: each can be ability or item ---
            cheat_extras: list[CombatAction] = []
            ap_spend = dec.get("ap_spend", 0)
            if mode == CheatSurviveChoice.CHEAT:
                if ap_spend > combatant.action_points:
                    raise ValueError(
                        f"{cid}: wants to spend {ap_spend} AP but only has {combatant.action_points}"
                    )
                for extra in dec.get("cheat_extras", []):
                    if extra.get("action") == "use_item" or extra.get("ability") == "use_item":
                        # Item use as a cheat extra action
                        self._apply_combat_item_use(cid, extra, combat)
                    else:
                        ability = extra.get("ability", extra.get("action", ""))
                        cheat_extras.append(CombatAction(
                            actor_id=cid,
                            ability_id=ability,
                            target_ids=[extra["target"]] if extra.get("target") else [],
                        ))

            # --- Partial actions (SPD bonus): abilities only ---
            partial_actions: list[CombatAction] = []
            max_partials = calculate_bonus_actions(combatant.effective_stats.SPD)
            for partial in dec.get("partial_actions", []):
                if len(partial_actions) >= max_partials:
                    raise ValueError(
                        f"{cid}: too many partial actions. Max: {max_partials} "
                        f"(SPD {combatant.effective_stats.SPD})"
                    )
                partial_actions.append(CombatAction(
                    actor_id=cid,
                    ability_id=partial["ability"],
                    target_ids=[partial["target"]] if partial.get("target") else [],
                    is_partial=True,
                ))

            decisions[cid] = PlayerTurnDecision(
                combatant_id=cid,
                cheat_survive=mode,
                cheat_actions=ap_spend,
                primary_action=primary_action,
                cheat_extra_actions=cheat_extras,
                partial_actions=partial_actions,
            )

        return decisions

    def _apply_combat_item_use(
        self, cid: str, dec: dict[str, Any], combat: CombatState,
    ) -> None:
        """Apply a combat item use: heal combatant, remove from stash.

        Mutates self._combat_state and self.run in place. Called from
        _parse_decisions when action is "use_item".
        """
        run = self._require_run()
        item_id = dec.get("item_id")
        target_id = dec.get("target", cid)  # Default to self

        if not item_id:
            raise ValueError(f"{cid}: use_item requires 'item_id'.")

        if item_id not in run.party.stash:
            raise ValueError(
                f"{cid}: '{item_id}' not in stash. "
                f"Stash: {', '.join(run.party.stash) or 'empty'}"
            )

        item = self.game_data.items.get(item_id) or run.party.items.get(item_id)
        if item is None or not item.is_consumable:
            raise ValueError(f"{cid}: '{item_id}' is not a consumable.")

        target = combat.get_combatant(target_id)
        if target is None or not target.is_player:
            raise ValueError(f"{cid}: '{target_id}' is not a player combatant.")
        if not target.is_alive:
            raise ValueError(f"{cid}: '{target_id}' is dead.")

        # Apply heal
        heal = item.heal_amount + int(target.max_hp * item.heal_percent)
        new_hp = min(target.current_hp + heal, target.max_hp)

        new_player_combatants = []
        for c in combat.player_combatants:
            if c.id == target_id:
                new_player_combatants.append(c.model_copy(update={"current_hp": new_hp}))
            else:
                new_player_combatants.append(c)
        self._combat_state = combat.model_copy(
            update={"player_combatants": new_player_combatants}
        )

        # Remove item from stash
        new_stash = list(run.party.stash)
        new_stash.remove(item_id)
        new_party = run.party.model_copy(update={"stash": new_stash})
        self.run = run.model_copy(update={"party": new_party})

    # ------------------------------------------------------------------
    # Post-Combat
    # ------------------------------------------------------------------

    def pick_loot(self, item_ids: list[str]) -> str:
        """Select which dropped items to keep."""
        self._require_phase("pick_loot")
        run = self._require_run()
        gl = self._require_game_loop()
        loot = self._last_loot

        if loot is None:
            raise AgentError("No loot to pick from.")

        # Validate item IDs
        available = set(loot.item_ids)
        for iid in item_ids:
            if iid not in available:
                raise AgentError(
                    f"'{iid}' is not in the loot drops. "
                    f"Available: {', '.join(sorted(available))}"
                )

        try:
            self.run = gl.apply_loot(run, loot, item_ids)
        except ValueError as e:
            raise AgentError(str(e)) from e

        self._last_loot = None

        # Check for recruitment
        if self._should_offer_recruitment():
            self._generate_recruitment()
            return S.summarize_recruitment(
                self._current_candidate,  # type: ignore[arg-type]
                gl.recruitment_engine.get_inspection_level(self.run.party.cha),
                self.run.party.cha,
                self.run,
                self.game_data,
            )

        self.phase = Phase.IN_ZONE
        return S.summarize_zone_status(self.run, self.game_data)

    def _should_offer_recruitment(self) -> bool:
        """Check if a recruitment event should trigger."""
        run = self._require_run()
        gl = self._require_game_loop()

        if run.zone_state is None or run.current_zone_id is None:
            return False

        # Only offer during normal zone progression, not after clearing
        if run.zone_state.is_cleared:
            return False

        # Already offered this zone visit
        if run.zone_state.recruitment_offered:
            return False

        zone = self.game_data.zones.get(run.current_zone_id)
        if zone is None or zone.recruitment_chance <= 0:
            return False

        # Party full
        total = len(run.party.active) + len(run.party.reserve)
        if total >= MAX_PARTY_SIZE:
            return False

        # Roll recruitment chance
        if gl.rng.random() >= zone.recruitment_chance:
            return False

        return True

    def _generate_recruitment(self) -> None:
        """Generate a recruitment candidate and set phase."""
        run = self._require_run()
        gl = self._require_game_loop()

        zone = self.game_data.zones.get(run.current_zone_id or "")
        zone_level = zone.zone_level if zone else 1
        shop_pool = zone.shop_item_pool if zone else []

        exclude: list[str] = []
        if run.last_recruit_job_id:
            exclude.append(run.last_recruit_job_id)

        self._current_candidate = gl.recruitment_engine.generate_candidate(
            zone_level=zone_level,
            exclude_job_ids=exclude,
            shop_pool=shop_pool,
        )

        # Mark recruitment as offered in zone state
        if run.zone_state:
            new_zs = run.zone_state.model_copy(update={"recruitment_offered": True})
            self.run = run.model_copy(update={"zone_state": new_zs})

        self.phase = Phase.RECRUITING

    # ------------------------------------------------------------------
    # Recruitment
    # ------------------------------------------------------------------

    def inspect_candidate(self) -> str:
        """Get detailed info about the recruitment candidate."""
        self._require_phase("inspect_candidate")
        run = self._require_run()
        gl = self._require_game_loop()

        if self._current_candidate is None:
            raise AgentError("No recruitment candidate.")

        level = gl.recruitment_engine.get_inspection_level(run.party.cha)
        return S.summarize_recruitment(
            self._current_candidate, level, run.party.cha,
            run, self.game_data,
        )

    def recruit(self, accept: bool) -> str:
        """Accept or decline the recruitment candidate."""
        self._require_phase("recruit")
        run = self._require_run()
        gl = self._require_game_loop()

        if self._current_candidate is None:
            raise AgentError("No recruitment candidate.")

        if accept:
            try:
                new_party = gl.recruitment_engine.recruit(
                    run.party, self._current_candidate,
                )
                self.run = run.model_copy(update={
                    "party": new_party,
                    "last_recruit_job_id": self._current_candidate.character.job_id,
                })
                result = f"Recruited {self._current_candidate.character.name}!\n\n"
            except ValueError as e:
                raise AgentError(str(e)) from e
        else:
            result = f"Declined {self._current_candidate.character.name}.\n\n"

        self._current_candidate = None
        self.phase = Phase.IN_ZONE
        return result + S.summarize_zone_status(self.run, self.game_data)

    # ------------------------------------------------------------------
    # Party Management
    # ------------------------------------------------------------------

    def party_status(self) -> str:
        """Full party detail view."""
        self._require_phase("party_status")
        run = self._require_run()
        return S.summarize_party(run, self.game_data)

    def equip(self, character_id: str, item_id: str, slot: str) -> str:
        """Equip an item from stash."""
        self._require_phase("equip")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            self.run = gl.equip_item(run, character_id, item_id, slot)
        except ValueError as e:
            raise AgentError(str(e)) from e

        char = self.run.party.characters[character_id]
        job_name = S._job_name(char.job_id, self.game_data)
        return (
            f"Equipped {item_id} on {char.name} ({slot}).\n\n"
            f"Updated stats: {S._stat_line(char)}\n"
            f"HP: {char.current_hp}/{char.max_hp}"
        )

    def unequip(self, character_id: str, slot: str) -> str:
        """Unequip from a slot."""
        self._require_phase("unequip")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            self.run = gl.unequip_item(run, character_id, slot)
        except ValueError as e:
            raise AgentError(str(e)) from e

        char = self.run.party.characters[character_id]
        return (
            f"Unequipped {slot} from {char.name}.\n\n"
            f"Updated stats: {S._stat_line(char)}\n"
            f"HP: {char.current_hp}/{char.max_hp}"
        )

    def swap_roster(
        self, active_id: str | None = None, reserve_id: str | None = None,
    ) -> str:
        """Swap active/reserve party members."""
        self._require_phase("swap_roster")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            if active_id and reserve_id:
                self.run = gl.swap_party_member(run, active_id, reserve_id)
            elif reserve_id:
                self.run = gl.promote_to_active(run, reserve_id)
            elif active_id:
                self.run = gl.bench_to_reserve(run, active_id)
            else:
                raise AgentError("Provide active_id, reserve_id, or both.")
        except ValueError as e:
            raise AgentError(str(e)) from e

        active_names = [
            self.run.party.characters[cid].name
            for cid in self.run.party.active
        ]
        reserve_names = [
            self.run.party.characters[cid].name
            for cid in self.run.party.reserve
        ]

        return (
            f"Roster updated.\n"
            f"Active: {', '.join(active_names)}\n"
            f"Reserve: {', '.join(reserve_names) or 'none'}"
        )

    def use_scroll(self, item_id: str, character_id: str) -> str:
        """Use a teach scroll."""
        self._require_phase("use_scroll")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            self.run = gl.use_teach_scroll(run, item_id, character_id)
        except ValueError as e:
            raise AgentError(str(e)) from e

        char = self.run.party.characters[character_id]
        return (
            f"Used {item_id} on {char.name}.\n"
            f"Abilities: {', '.join(char.abilities)}"
        )

    def use_consumable(self, item_id: str, character_id: str) -> str:
        """Use a consumable."""
        self._require_phase("use_consumable")
        run = self._require_run()
        gl = self._require_game_loop()

        old_hp = run.party.characters[character_id].current_hp

        try:
            self.run = gl.use_consumable(run, item_id, character_id)
        except ValueError as e:
            raise AgentError(str(e)) from e

        char = self.run.party.characters[character_id]
        healed = char.current_hp - old_hp
        return (
            f"Used {item_id} on {char.name}. Healed {healed} HP.\n"
            f"HP: {char.current_hp}/{char.max_hp}"
        )

    def mc_swap_job(self, job_id: str) -> str:
        """Change MC's job."""
        self._require_phase("mc_swap_job")
        run = self._require_run()
        gl = self._require_game_loop()

        try:
            self.run = gl.mc_swap_job(run, job_id)
        except ValueError as e:
            raise AgentError(str(e)) from e

        mc = None
        for char in self.run.party.characters.values():
            if char.is_mc:
                mc = char
                break

        if mc:
            return (
                f"Job swapped to {S._job_name(job_id, self.game_data)}!\n"
                f"Stats: {S._stat_line(mc)}\n"
                f"Abilities: {', '.join(mc.abilities)}\n"
                f"HP: {mc.current_hp}/{mc.max_hp}"
            )
        return f"Job swapped to {job_id}."

    # ------------------------------------------------------------------
    # Shopping
    # ------------------------------------------------------------------

    def shop_browse(self) -> str:
        """View zone shop."""
        self._require_phase("shop_browse")
        run = self._require_run()

        if not run.current_zone_id:
            raise AgentError("Not in a zone.")

        zone = self.game_data.zones.get(run.current_zone_id)
        if not zone:
            raise AgentError(f"Unknown zone: {run.current_zone_id}")

        shop = ShopInventory(
            available_items=zone.shop_item_pool,
            zone_level=zone.zone_level,
        )
        return S.summarize_shop(shop, run, self.game_data)

    def shop_buy(self, item_id: str) -> str:
        """Buy an item."""
        self._require_phase("shop_buy")
        run = self._require_run()
        gl = self._require_game_loop()

        if not run.current_zone_id:
            raise AgentError("Not in a zone.")

        zone = self.game_data.zones.get(run.current_zone_id)
        if not zone:
            raise AgentError(f"Unknown zone: {run.current_zone_id}")

        if item_id not in zone.shop_item_pool:
            raise AgentError(
                f"'{item_id}' not in this shop. "
                f"Available: {', '.join(zone.shop_item_pool)}"
            )

        item = self.game_data.items.get(item_id)
        if not item:
            raise AgentError(f"Unknown item: {item_id}")

        price = calculate_buy_price(item.base_price, run.party.cha)

        try:
            new_party = gl.shop_engine.buy_item(run.party, item_id, price)
            self.run = run.model_copy(update={"party": new_party})
        except ValueError as e:
            raise AgentError(str(e)) from e

        return (
            f"Bought {item.name} for {price}g.\n"
            f"Gold: {self.run.party.money} | "
            f"Stash: {len(self.run.party.stash)}/10"
        )

    def shop_sell(self, item_id: str) -> str:
        """Sell an item from stash."""
        self._require_phase("shop_sell")
        run = self._require_run()
        gl = self._require_game_loop()

        # Check item isn't equipped
        for char in run.party.characters.values():
            for slot, eid in char.equipment.items():
                if eid == item_id:
                    raise AgentError(
                        f"'{item_id}' is equipped on {char.name} ({slot}). Unequip first."
                    )

        try:
            new_party = gl.shop_engine.sell_item(run.party, item_id)
            self.run = run.model_copy(update={"party": new_party})
        except ValueError as e:
            raise AgentError(str(e)) from e

        item = self.game_data.items.get(item_id)
        sell_price = calculate_sell_price(item.base_price) if item else 0

        return (
            f"Sold {item.name if item else item_id} for {sell_price}g.\n"
            f"Gold: {self.run.party.money} | "
            f"Stash: {len(self.run.party.stash)}/10"
        )

    # ------------------------------------------------------------------
    # Lookup (available in all phases)
    # ------------------------------------------------------------------

    def lookup_job(self, job_id: str) -> str:
        self._require_phase("lookup_job")
        return S.lookup_job_view(job_id, self.game_data)

    def lookup_ability(self, ability_id: str) -> str:
        self._require_phase("lookup_ability")
        return S.lookup_ability_view(ability_id, self.game_data)

    def lookup_item(self, item_id: str) -> str:
        self._require_phase("lookup_item")
        return S.lookup_item_view(item_id, self.game_data)

    def lookup_enemy(self, enemy_id: str) -> str:
        self._require_phase("lookup_enemy")
        return S.lookup_enemy_view(enemy_id, self.game_data)

    def lookup_zone(self, zone_id: str) -> str:
        self._require_phase("lookup_zone")
        return S.lookup_zone_view(zone_id, self.game_data)

    def lookup_formula(self, topic: str) -> str:
        self._require_phase("lookup_formula")
        return S.lookup_formula_view(topic)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_battle_record(self) -> str:
        self._require_phase("get_battle_record")
        run = self._require_run()
        return S.summarize_run_report(run, self.game_data)

    def get_run_summary(self) -> str:
        self._require_phase("get_run_summary")
        run = self._require_run()
        return S.summarize_run_report(run, self.game_data)

    # ------------------------------------------------------------------
    # Notes (persist across runs)
    # ------------------------------------------------------------------

    def _load_notes(self) -> dict[str, str]:
        """Load notes from disk."""
        try:
            if self._notes_path.exists():
                return json.loads(self._notes_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _save_notes_to_disk(self) -> None:
        """Persist notes to disk."""
        try:
            self._notes_path.write_text(json.dumps(self._notes, indent=2))
        except OSError:
            pass  # Best-effort persistence

    def save_note(self, key: str, content: str) -> str:
        """Save a named note. Persists across runs."""
        self._require_phase("save_note")
        self._notes[key] = content
        self._save_notes_to_disk()
        return f"Saved note '{key}'."

    def read_notes(self) -> str:
        """Read all saved notes."""
        self._require_phase("read_notes")
        if not self._notes:
            return "No notes saved yet."
        lines = ["=== AGENT NOTES ===", ""]
        for key, content in self._notes.items():
            lines.append(f"[{key}]")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Save / Load (persist runs across restarts)
    # ------------------------------------------------------------------

    def _get_saves_dir(self) -> Path:
        """Get the saves directory, creating it if needed."""
        saves_dir = self._notes_path.parent / "agent_saves"
        saves_dir.mkdir(exist_ok=True)
        return saves_dir

    def save_run(self, slot: str = "autosave") -> str:
        """Save current run state to disk. Survives server restarts."""
        run = self._require_run()
        saves_dir = self._get_saves_dir()

        save_data = {
            "phase": self.phase.value,
            "seed": self.seed,
            "run": run.model_dump(),
        }

        save_path = saves_dir / f"{slot}.json"
        try:
            save_path.write_text(json.dumps(save_data, indent=2, default=str))
        except OSError as e:
            raise AgentError(f"Failed to save: {e}") from e

        mc_name = ""
        for char in run.party.characters.values():
            if char.is_mc:
                mc_name = char.name
                break

        return (
            f"Saved to slot '{slot}'. "
            f"{mc_name} Lv{next((c.level for c in run.party.characters.values() if c.is_mc), '?')} | "
            f"Phase: {self.phase.value} | "
            f"Zones: {len(run.zones_completed)}/{len(self.game_data.zones)}"
        )

    def load_run(self, slot: str = "autosave") -> str:
        """Load a saved run from disk."""
        saves_dir = self._get_saves_dir()
        save_path = saves_dir / f"{slot}.json"

        if not save_path.exists():
            # List available saves
            available = [
                f.stem for f in saves_dir.glob("*.json")
            ]
            if available:
                return f"Save '{slot}' not found. Available: {', '.join(sorted(available))}"
            return f"Save '{slot}' not found. No saves exist."

        try:
            save_data = json.loads(save_path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise AgentError(f"Failed to load save: {e}") from e

        # Reconstruct session state
        self.seed = save_data.get("seed")
        rng = random.Random(self.seed)
        self.game_loop = GameLoop(game_data=self.game_data, rng=rng)

        # Restore RunState from serialized data
        self.run = RunState.model_validate(save_data["run"])

        # Rehydrate derived fields (effective_stats, max_hp)
        self.run = self.game_loop.rehydrate_run(self.run)

        # Restore phase (default to zone_select if not in combat)
        phase_str = save_data.get("phase", "ZONE_SELECT")
        try:
            self.phase = Phase(phase_str)
        except ValueError:
            self.phase = Phase.ZONE_SELECT

        # Can't restore mid-combat state — drop to zone/select
        if self.phase == Phase.COMBAT:
            self.phase = Phase.IN_ZONE if self.run.current_zone_id else Phase.ZONE_SELECT
        if self.phase == Phase.POST_COMBAT:
            self.phase = Phase.IN_ZONE if self.run.current_zone_id else Phase.ZONE_SELECT
        if self.phase == Phase.RECRUITING:
            self.phase = Phase.IN_ZONE if self.run.current_zone_id else Phase.ZONE_SELECT

        # Clear combat state
        self._combat_state = None
        self._current_enemies = []
        self._round_events = []

        mc_name = ""
        mc_level = 0
        for char in self.run.party.characters.values():
            if char.is_mc:
                mc_name = char.name
                mc_level = char.level
                break

        return (
            f"Loaded '{slot}'. {mc_name} Lv{mc_level} | "
            f"Phase: {self.phase.value} | "
            f"Zones: {len(self.run.zones_completed)}/{len(self.game_data.zones)}\n\n"
            + self.get_state()
        )

    def list_saves(self) -> str:
        """List available save files."""
        saves_dir = self._get_saves_dir()
        saves = sorted(saves_dir.glob("*.json"))
        if not saves:
            return "No saves found."
        lines = ["=== SAVED RUNS ===", ""]
        for save_path in saves:
            try:
                data = json.loads(save_path.read_text())
                run_data = data.get("run", {})
                party = run_data.get("party", {})
                chars = party.get("characters", {})
                mc = next((c for c in chars.values() if c.get("is_mc")), {})
                name = mc.get("name", "?")
                level = mc.get("level", "?")
                zones = len(run_data.get("zones_completed", []))
                phase = data.get("phase", "?")
                lines.append(f"  {save_path.stem} -- {name} Lv{level} | {phase} | Zones: {zones}/7")
            except (json.JSONDecodeError, OSError):
                lines.append(f"  {save_path.stem} -- (corrupted)")
        return "\n".join(lines)
