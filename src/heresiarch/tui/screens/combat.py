"""Combat screen — the big one.

Turn planning (sequential character cycling) + round execution with event playback.
State machine: PLANNING → EXECUTING → PLANNING (next round) or COMBAT_OVER.
"""

from __future__ import annotations

from enum import Enum, auto

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, OptionList, RichLog, Static
from textual.widgets.option_list import Option

from heresiarch.engine.formulas import MAX_ACTION_POINT_BANK, calculate_speed_bonus
from heresiarch.engine.models.abilities import AbilityCategory, TargetType
from heresiarch.engine.models.battle_record import EncounterRecord, RoundRecord
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.run_state import CombatResult
from heresiarch.tui.event_renderer import (
    get_event_delay,
    render_event,
    render_events_summary,
)


class CombatPhase(Enum):
    PLANNING_CHEAT_SURVIVE = auto()
    PLANNING_CHEAT_AP = auto()      # Choose how many AP to spend
    PLANNING_ACTION_MENU = auto()   # Basic Attack / Abilities / Items
    PLANNING_ABILITY = auto()
    PLANNING_TARGET = auto()
    PLANNING_ITEM = auto()          # Choose a consumable from stash
    PLANNING_ITEM_TARGET = auto()   # Choose who to use the item on
    PLANNING_CHEAT_ACTION = auto()  # Choose extra actions from Cheat
    PLANNING_CHEAT_TARGET = auto()  # Target for cheat extra action
    PLANNING_PARTIAL = auto()
    PLANNING_CONFIRM = auto()
    EXECUTING = auto()
    COMBAT_OVER = auto()


class CombatScreen(Screen):
    """Full combat encounter: planning + execution."""

    CSS = """
    #combat-layout {
        height: 100%;
    }
    #status-bar {
        height: auto;
    }
    #party-panel {
        width: 1fr;
        height: auto;
        border: round #4488cc;
        border-title-color: #4488cc;
        border-title-align: left;
        padding: 0 1;
    }
    #enemy-panel {
        width: 1fr;
        height: auto;
        border: round #cc4444;
        border-title-color: #cc4444;
        border-title-align: left;
        padding: 0 1;
    }
    #action-area {
        height: auto;
        padding: 0 1;
        border-bottom: tall #333355;
    }
    #action-choices {
        height: auto;
        max-height: 6;
    }
    #combat-log {
        height: 1fr;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("v", "toggle_verbose", "Toggle Log"),
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._phase: CombatPhase = CombatPhase.PLANNING_CHEAT_SURVIVE
        self._prev_phase: CombatPhase | None = None  # for back navigation
        self._decisions: dict[str, PlayerTurnDecision] = {}
        self._current_char_index: int = 0
        self._current_decision: PlayerTurnDecision | None = None
        self._selected_ability_id: str | None = None
        self._partial_actions_remaining: int = 0
        self._partial_actions: list[CombatAction] = []
        self._cheat_extra_actions: list[CombatAction] = []
        self._cheat_actions_remaining: int = 0
        self._verbose: bool = True
        self._playback_queue: list = []
        self._raw_event_queue: list = []
        self._event_delays: list[int] = []
        # Progressive display state — used during event playback
        self._display_hp: dict[str, int] = {}
        self._display_alive: dict[str, bool] = {}
        self._display_max_hp: dict[str, int] = {}
        # Target cursor — shows arrow in status panels during target selection
        self._highlighted_target_id: str | None = None
        # Item use in combat
        self._selected_item_id: str | None = None
        self._claimed_items: list[str] = []  # items queued this round (prevents double-use)
        self._combatant_names: dict[str, str] = {}
        self._ability_names: dict[str, str] = {}
        self._encounter_record: EncounterRecord | None = None
        self._round_events_start: int = 0
        self._choice_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="combat-layout"):
            with Horizontal(id="status-bar"):
                with Vertical(id="party-panel"):
                    yield Static("", id="party-display")
                with Vertical(id="enemy-panel"):
                    yield Static("", id="enemy-display")

            with Vertical(id="action-area"):
                yield Label("", id="round-indicator")
                yield Label("", id="phase-prompt")
                yield OptionList(id="action-choices")

            yield RichLog(id="combat-log", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self._initialize_combat()
        self._update_display()

    def _initialize_combat(self) -> None:
        """Set up the combat encounter from current run state."""
        app = self.app
        run = app.run_state
        if run is None:
            return

        enemies = app.game_loop.get_next_encounter(run)
        app.current_enemies = enemies

        characters = [
            run.party.characters[cid]
            for cid in run.party.active
            if cid in run.party.characters
        ]

        combat = app.game_loop.combat_engine.initialize_combat(characters, enemies)
        app.combat_state = combat

        # Build name mappings
        self._combatant_names = {}
        for c in combat.player_combatants:
            char = run.party.characters.get(c.id)
            self._combatant_names[c.id] = char.name if char else c.id
        for i, c in enumerate(combat.enemy_combatants):
            template_id = c.id.rsplit("_", 1)[0] if "_" in c.id else c.id
            template = app.game_data.enemies.get(template_id)
            name = template.name if template else template_id
            self._combatant_names[c.id] = f"{name} {chr(65 + i)}" if len(combat.enemy_combatants) > 1 else name

        self._ability_names = {
            aid: ability.name for aid, ability in app.game_data.abilities.items()
        }

        zone_id = run.current_zone_id or ""
        encounter_idx = run.zone_state.current_encounter_index if run.zone_state else 0
        self._encounter_record = EncounterRecord(
            zone_id=zone_id,
            encounter_index=encounter_idx,
            enemy_template_ids=[e.template_id for e in enemies],
        )

        self._round_events_start = 0

        # Set panel titles
        self.query_one("#party-panel").border_title = "Party"
        self.query_one("#enemy-panel").border_title = "Enemies"

        self._start_planning()

    # --- Planning State Machine ---

    def _start_planning(self) -> None:
        self._current_char_index = 0
        self._decisions = {}
        self._claimed_items = []
        combat = self.app.combat_state
        if combat is None:
            return

        living = combat.living_players
        if not living:
            self._phase = CombatPhase.COMBAT_OVER
            return

        self._phase = CombatPhase.PLANNING_CHEAT_SURVIVE
        self._current_decision = PlayerTurnDecision(combatant_id=living[0].id)
        self._populate_choices()
        self._update_display()

    def _current_combatant_id(self) -> str | None:
        combat = self.app.combat_state
        if combat is None:
            return None
        living = combat.living_players
        if self._current_char_index >= len(living):
            return None
        return living[self._current_char_index].id

    def _populate_choices(self) -> None:
        """Fill the OptionList based on current phase."""
        choices = self.query_one("#action-choices", OptionList)
        choices.clear_options()
        self._choice_keys = []
        self._highlighted_target_id = None

        match self._phase:
            case CombatPhase.PLANNING_CHEAT_SURVIVE:
                combatant = None
                if self._current_decision and self.app.combat_state:
                    combatant = self.app.combat_state.get_combatant(self._current_decision.combatant_id)
                ap = combatant.action_points if combatant else 0
                is_taunted = bool(combatant and combatant.taunted_by)

                choices.add_option(Option("Normal — take your turn"))
                self._choice_keys.append("cs:normal")

                if ap > 0:
                    choices.add_option(Option(f"Cheat — spend AP for extra actions ({ap} AP banked)"))
                    self._choice_keys.append("cs:cheat")

                if is_taunted:
                    choices.add_option(Option("[strike dim]Survive[/strike dim] [bold #cc4444]TAUNTED[/bold #cc4444]"))
                    self._choice_keys.append("disabled")
                else:
                    next_ap = min(ap + 1, MAX_ACTION_POINT_BANK)
                    cap_note = " MAX" if next_ap == ap else ""
                    choices.add_option(Option(f"Survive — bank AP, reduce damage (AP: {next_ap}{cap_note})"))
                    self._choice_keys.append("cs:survive")

            case CombatPhase.PLANNING_CHEAT_AP:
                combatant = None
                if self._current_decision and self.app.combat_state:
                    combatant = self.app.combat_state.get_combatant(self._current_decision.combatant_id)
                ap = combatant.action_points if combatant else 0

                for n in range(1, ap + 1):
                    choices.add_option(Option(f"Spend {n} AP ({n} extra action{'s' if n > 1 else ''})"))
                    self._choice_keys.append(f"cheat_ap:{n}")

            case CombatPhase.PLANNING_ACTION_MENU:
                self._populate_action_menu(choices)

            case CombatPhase.PLANNING_ABILITY | CombatPhase.PLANNING_PARTIAL | CombatPhase.PLANNING_CHEAT_ACTION:
                self._populate_ability_options(choices)

            case CombatPhase.PLANNING_TARGET | CombatPhase.PLANNING_CHEAT_TARGET:
                self._populate_target_options(choices)

            case CombatPhase.PLANNING_ITEM:
                self._populate_item_options(choices)

            case CombatPhase.PLANNING_ITEM_TARGET:
                self._populate_item_target_options(choices)

            case CombatPhase.PLANNING_CONFIRM:
                choices.add_option(Option("[bold]Execute Round[/bold]"))
                self._choice_keys.append("execute")

            case CombatPhase.EXECUTING | CombatPhase.COMBAT_OVER:
                return

        # Rebuild options with number hotkey prefixes
        if self._choice_keys:
            old_prompts = [choices.get_option_at_index(i).prompt for i in range(len(self._choice_keys))]
            choices.clear_options()
            for i, prompt in enumerate(old_prompts):
                prefix = f"[bold #888888]{i + 1}.[/bold #888888] " if i < 9 else "   "
                choices.add_option(Option(f"{prefix}{prompt}"))

        # Focus and highlight first option for all planning phases
        if self._choice_keys:
            choices.focus()
            choices.highlighted = 0

    def _populate_action_menu(self, choices: OptionList) -> None:
        """Show top-level action categories: Basic Attack, Abilities, Items."""
        if self._current_decision is None:
            return
        run = self.app.run_state
        combat = self.app.combat_state
        if run is None or combat is None:
            return

        char = run.party.characters.get(self._current_decision.combatant_id)
        if char is None:
            return

        combatant = combat.get_combatant(self._current_decision.combatant_id)
        is_taunted = bool(combatant and combatant.taunted_by)

        # Windup push — when charging, offer "Wait" to accelerate the charge
        if combatant and combatant.charge_turns_remaining > 0:
            turns = combatant.charge_turns_remaining
            ability_name = combatant.charging_ability_id or "ability"
            choices.add_option(Option(
                f"[bold #e6c566]Wait[/bold #e6c566] (push {ability_name}, {turns} turn{'s' if turns != 1 else ''} left)"
            ))
            self._choice_keys.append("action:windup_push")

        # Basic Attack — always available (no sub-menu)
        choices.add_option(Option("Basic Attack"))
        self._choice_keys.append("action:basic_attack")

        # Abilities — enabled only if character has non-basic_attack, non-passive abilities
        # When taunted, only count abilities that deal damage to enemies
        has_extra_abilities = False
        for ability_id in char.abilities:
            if ability_id == "basic_attack":
                continue
            ability = self.app.game_data.abilities.get(ability_id)
            if ability is None or ability.category == AbilityCategory.PASSIVE:
                continue
            if is_taunted:
                has_damage = any(e.base_damage > 0 for e in ability.effects)
                targets_enemy = ability.target in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES)
                if not (has_damage and targets_enemy):
                    continue
            has_extra_abilities = True
            break

        if has_extra_abilities:
            choices.add_option(Option("Abilities"))
            self._choice_keys.append("action:abilities")
        else:
            choices.add_option(Option("[dim]Abilities (none available)[/dim]"))
            self._choice_keys.append("disabled")

        # Items — disabled when taunted or during bonus actions
        if is_taunted:
            choices.add_option(Option("[strike dim]Items[/strike dim] [bold #cc4444]TAUNTED[/bold #cc4444]"))
            self._choice_keys.append("disabled")
        elif self._partial_actions_remaining > 0:
            choices.add_option(Option("[dim]Items (not for bonus actions)[/dim]"))
            self._choice_keys.append("disabled")
        else:
            has_consumables = any(
                (item := (run.party.items.get(iid) or self.app.game_data.items.get(iid)))
                and item.is_consumable
                for iid in run.party.stash
            )
            if has_consumables:
                choices.add_option(Option("[#44aa44]Items[/#44aa44]"))
                self._choice_keys.append("action:items")
            else:
                choices.add_option(Option("[dim]Items (none)[/dim]"))
                self._choice_keys.append("disabled")

    def _populate_ability_options(self, choices: OptionList) -> None:
        """Shared ability list population for primary, cheat, and partial phases."""
        if self._current_decision is None:
            return
        run = self.app.run_state
        combat = self.app.combat_state
        if run is None or combat is None:
            return

        char = run.party.characters.get(self._current_decision.combatant_id)
        if char is None:
            return

        combatant = combat.get_combatant(self._current_decision.combatant_id)
        is_taunted = bool(combatant and combatant.taunted_by)

        for ability_id in char.abilities:
            if ability_id == "basic_attack":
                continue  # basic_attack is handled by the action menu
            ability = self.app.game_data.abilities.get(ability_id)
            if ability is None or ability.category == AbilityCategory.PASSIVE:
                continue

            cd = combatant.cooldowns.get(ability_id, 0) if combatant else 0

            # Check taunt restriction: only damaging enemy-targeting abilities allowed
            taunt_blocked = False
            if is_taunted:
                has_damage = any(e.base_damage > 0 for e in ability.effects)
                targets_enemy = ability.target in (TargetType.SINGLE_ENEMY, TargetType.ALL_ENEMIES)
                taunt_blocked = not (has_damage and targets_enemy)

            label = ability.name
            if ability.description:
                label += f" — {ability.description}"

            if taunt_blocked:
                label = f"[strike dim]{ability.name}[/strike dim] [bold #cc4444]TAUNTED[/bold #cc4444]"
                choices.add_option(Option(label))
                self._choice_keys.append("disabled")
            elif cd > 0:
                label += f" [dim][CD: {cd}][/dim]"
                choices.add_option(Option(label))
                self._choice_keys.append("cooldown")
            else:
                choices.add_option(Option(label))
                self._choice_keys.append(f"ability:{ability_id}")

    def _populate_item_options(self, choices: OptionList) -> None:
        """List consumable items from party stash, excluding already-claimed items."""
        run = self.app.run_state
        if run is None:
            return

        # Build available stash minus items already queued this round
        available = list(run.party.stash)
        for claimed in self._claimed_items:
            try:
                available.remove(claimed)
            except ValueError:
                pass

        seen: set[str] = set()
        for item_id in available:
            if item_id in seen:
                continue
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            if item is None or not item.is_consumable:
                continue
            seen.add(item_id)
            count = available.count(item_id)
            label = item.name
            if item.heal_amount > 0:
                label += f" (heals {item.heal_amount} HP)"
            elif item.heal_percent > 0:
                label += f" (heals {int(item.heal_percent * 100)}% HP)"
            if count > 1:
                label += f" x{count}"
            choices.add_option(Option(label))
            self._choice_keys.append(f"item:{item_id}")

    def _populate_item_target_options(self, choices: OptionList) -> None:
        """List party members to use an item on."""
        combat = self.app.combat_state
        if combat is None:
            return

        for p in combat.living_players:
            name = self._combatant_names.get(p.id, p.id)
            hp_pct = p.current_hp / max(p.max_hp, 1)
            hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            choices.add_option(Option(f"{name} [{hp_color}]{p.current_hp}/{p.max_hp}[/{hp_color}]"))
            self._choice_keys.append(f"item_target:{p.id}")

    def _populate_target_options(self, choices: OptionList) -> None:
        """Shared target list population."""
        combat = self.app.combat_state
        if combat is None or self._selected_ability_id is None:
            return

        ability = self.app.game_data.abilities.get(self._selected_ability_id)
        if ability is None:
            return

        targets: list[tuple[str, str]] = []
        combatant = combat.get_combatant(self._current_decision.combatant_id) if self._current_decision else None
        taunted_by = set(combatant.taunted_by) if combatant else set()

        match ability.target:
            case TargetType.SINGLE_ENEMY:
                if taunted_by:
                    # Taunted: can only target the taunter(s)
                    targets = [
                        (e.id, self._combatant_names.get(e.id, e.id))
                        for e in combat.living_enemies if e.id in taunted_by
                    ]
                else:
                    targets = [(e.id, self._combatant_names.get(e.id, e.id)) for e in combat.living_enemies]
            case TargetType.SINGLE_ALLY:
                targets = [(p.id, self._combatant_names.get(p.id, p.id)) for p in combat.living_players]

        for tid, name in targets:
            choices.add_option(Option(name))
            self._choice_keys.append(f"target:{tid}")

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Update target cursor in status panels as player browses targets."""
        if event.option_list.id != "action-choices":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._choice_keys):
            return

        key = self._choice_keys[idx]
        old_target = self._highlighted_target_id

        if key.startswith("target:"):
            self._highlighted_target_id = key.split(":", 1)[1]
        else:
            self._highlighted_target_id = None

        # Re-render panels if cursor moved
        if self._highlighted_target_id != old_target:
            combat = self.app.combat_state
            if combat:
                self._render_party_panel(combat)
                self._render_enemy_panel(combat)

    def on_key(self, event: events.Key) -> None:
        """Map 1-9 keys to option selection for quick combat input."""
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(self._choice_keys):
                choices = self.query_one("#action-choices", OptionList)
                choices.highlighted = idx
                choices.action_select()
                event.prevent_default()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "action-choices":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._choice_keys):
            return

        key = self._choice_keys[idx]
        if key in ("cooldown", "disabled"):
            return

        if key == "execute":
            self._execute_round()
            return

        parts = key.split(":", 1)
        match parts[0]:
            case "cs":
                self._handle_cs(parts[1])
            case "cheat_ap":
                self._handle_cheat_ap(int(parts[1]))
            case "action":
                self._handle_action_menu(parts[1])
            case "ability":
                self._handle_ability(parts[1])
            case "target":
                self._handle_target(parts[1])
            case "item":
                self._selected_item_id = parts[1]
                self._phase = CombatPhase.PLANNING_ITEM_TARGET
                self._populate_choices()
                self._update_display()
            case "item_target":
                self._handle_item_use(parts[1])

    def _handle_item_use(self, target_id: str) -> None:
        """Queue a consumable item use as a proper combat action."""
        run = self.app.run_state
        combat = self.app.combat_state
        if run is None or combat is None or self._selected_item_id is None:
            return

        if self._current_decision is None:
            return

        item_id = self._selected_item_id
        self._selected_item_id = None

        # Claim item so it can't be double-queued this round
        self._claimed_items.append(item_id)

        # Build item action — resolved during turn order by the engine
        item_action = CombatAction(
            actor_id=self._current_decision.combatant_id,
            ability_id="use_item",
            item_id=item_id,
            target_ids=[target_id],
        )

        # Cheat extra action (primary already set, cheat slots remaining)
        if self._cheat_actions_remaining > 0 and self._current_decision.primary_action is not None:
            self._cheat_extra_actions.append(item_action)
            self._cheat_actions_remaining -= 1
            if self._cheat_actions_remaining > 0:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
                return
            self._current_decision.cheat_extra_actions = self._cheat_extra_actions
            self._check_partial_actions()
            return

        # Primary action slot — item consumes it
        # (Items cannot be used as partial/SPD-bonus actions — abilities only)
        self._current_decision.primary_action = item_action

        # Still need cheat extra actions?
        if self._cheat_actions_remaining > 0:
            self._phase = CombatPhase.PLANNING_ACTION_MENU
            self._selected_ability_id = None
            self._populate_choices()
            self._update_display()
            return

        self._check_partial_actions()

    def _handle_action_menu(self, choice: str) -> None:
        """Handle selection from the action menu (Basic Attack / Abilities / Items)."""
        match choice:
            case "windup_push":
                self._handle_windup_push()
                return
            case "basic_attack":
                # Route through the same ability handler for consistent targeting
                self._handle_ability("basic_attack")
            case "abilities":
                self._phase = CombatPhase.PLANNING_ABILITY
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
            case "items":
                self._phase = CombatPhase.PLANNING_ITEM
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()

    def _handle_windup_push(self) -> None:
        """Handle the player choosing to push their active windup forward."""
        if self._current_decision is None:
            return

        push_action = CombatAction(
            actor_id=self._current_decision.combatant_id,
            is_windup_push=True,
        )

        # Cheat extra action slot
        if self._cheat_actions_remaining > 0 and self._current_decision.primary_action is not None:
            self._cheat_extra_actions.append(push_action)
            self._cheat_actions_remaining -= 1
            if self._cheat_actions_remaining > 0:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
                return
            self._current_decision.cheat_extra_actions = self._cheat_extra_actions
            self._check_partial_actions()
            return

        # Bonus action slot
        if self._partial_actions_remaining > 0 and self._current_decision.primary_action is not None:
            self._partial_actions.append(push_action)
            self._partial_actions_remaining -= 1
            if self._partial_actions_remaining > 0:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
                return
            self._current_decision.bonus_actions = self._partial_actions
            self._finalize_character()
            return

    def _handle_cs(self, choice: str) -> None:
        if self._current_decision is None:
            return

        match choice:
            case "cheat":
                self._current_decision.cheat_survive = CheatSurviveChoice.CHEAT
                # Go to AP selection
                self._prev_phase = CombatPhase.PLANNING_CHEAT_SURVIVE
                self._phase = CombatPhase.PLANNING_CHEAT_AP
                self._populate_choices()
                self._update_display()
                return
            case "survive":
                self._current_decision.cheat_survive = CheatSurviveChoice.SURVIVE
                self._finalize_character()
                return
            case "normal":
                self._current_decision.cheat_survive = CheatSurviveChoice.NORMAL

        self._phase = CombatPhase.PLANNING_ACTION_MENU
        self._selected_ability_id = None
        self._partial_actions = []
        self._partial_actions_remaining = 0
        self._cheat_extra_actions = []
        self._cheat_actions_remaining = 0
        self._populate_choices()
        self._update_display()

    def _handle_cheat_ap(self, ap_count: int) -> None:
        """Player chose how many AP to spend."""
        if self._current_decision is None:
            return
        self._current_decision.cheat_actions = ap_count
        self._cheat_actions_remaining = ap_count
        self._cheat_extra_actions = []

        # Now choose primary action
        self._phase = CombatPhase.PLANNING_ACTION_MENU
        self._selected_ability_id = None
        self._populate_choices()
        self._update_display()

    def _handle_ability(self, ability_id: str) -> None:
        self._selected_ability_id = ability_id
        ability = self.app.game_data.abilities.get(ability_id)
        if ability is None:
            return

        # Auto-target for non-single target types
        match ability.target:
            case TargetType.SELF:
                targets = [self._current_decision.combatant_id] if self._current_decision else []
                self._apply_action(ability_id, targets)
            case TargetType.ALL_ENEMIES:
                combat = self.app.combat_state
                if combat:
                    self._apply_action(ability_id, [e.id for e in combat.living_enemies])
            case TargetType.ALL_ALLIES:
                combat = self.app.combat_state
                if combat:
                    self._apply_action(ability_id, [p.id for p in combat.living_players])
            case _:
                self._phase = CombatPhase.PLANNING_TARGET
                self._populate_choices()
                self._update_display()

    def _handle_target(self, target_id: str) -> None:
        if self._selected_ability_id is None:
            return
        self._apply_action(self._selected_ability_id, [target_id])

    def _apply_action(self, ability_id: str, target_ids: list[str]) -> None:
        if self._current_decision is None:
            return

        action = CombatAction(
            actor_id=self._current_decision.combatant_id,
            ability_id=ability_id,
            target_ids=target_ids,
        )

        # Cheat extra action (primary already set, cheat slots remaining)
        if self._cheat_actions_remaining > 0 and self._current_decision.primary_action is not None:
            self._cheat_extra_actions.append(action)
            self._cheat_actions_remaining -= 1
            if self._cheat_actions_remaining > 0:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
                return
            # All cheat actions chosen
            self._current_decision.cheat_extra_actions = self._cheat_extra_actions
            self._check_partial_actions()
            return

        # Partial (SPD bonus) action (primary already set, partial slots remaining)
        if self._partial_actions_remaining > 0 and self._current_decision.primary_action is not None:
            self._partial_actions.append(action)
            self._partial_actions_remaining -= 1
            if self._partial_actions_remaining > 0:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._selected_ability_id = None
                self._populate_choices()
                self._update_display()
                return
            self._current_decision.bonus_actions = self._partial_actions
            self._finalize_character()
            return

        # Primary action
        self._current_decision.primary_action = action

        # If cheating, now choose extra actions
        if self._cheat_actions_remaining > 0:
            self._phase = CombatPhase.PLANNING_ACTION_MENU
            self._selected_ability_id = None
            self._populate_choices()
            self._update_display()
            return

        self._check_partial_actions()

    def _check_partial_actions(self) -> None:
        """If the player has speed bonus actions, let them choose abilities/targets."""
        combat = self.app.combat_state
        if combat is None or self._current_decision is None:
            self._finalize_character()
            return

        # Survive suppresses speed bonus
        if self._current_decision.cheat_survive == CheatSurviveChoice.SURVIVE:
            self._finalize_character()
            return

        # Item primary suppresses speed bonus (no free item repeats)
        if (
            self._current_decision.primary_action
            and self._current_decision.primary_action.item_id is not None
        ):
            self._finalize_character()
            return

        cid = self._current_decision.combatant_id
        combatant = combat.get_combatant(cid)
        if combatant is None:
            self._finalize_character()
            return

        slowest_enemy_spd = min(
            (e.effective_stats.SPD for e in combat.living_enemies), default=0,
        )
        bonus = calculate_speed_bonus(combatant.effective_stats.SPD, slowest_enemy_spd)
        if bonus > 0:
            self._partial_actions_remaining = bonus
            self._partial_actions = []
            self._phase = CombatPhase.PLANNING_ACTION_MENU
            self._selected_ability_id = None
            self._populate_choices()
            self._update_display()
            return

        self._finalize_character()

    def action_go_back(self) -> None:
        """Navigate back one step in the planning flow."""
        match self._phase:
            case CombatPhase.PLANNING_CHEAT_SURVIVE:
                # Go back to previous character, or do nothing if first
                if self._current_char_index > 0:
                    self._current_char_index -= 1
                    combat = self.app.combat_state
                    if combat:
                        living = combat.living_players
                        if self._current_char_index < len(living):
                            cid = living[self._current_char_index].id
                            self._decisions.pop(cid, None)
                            self._current_decision = PlayerTurnDecision(combatant_id=cid)
                    self._populate_choices()
                    self._update_display()
            case CombatPhase.PLANNING_CHEAT_AP:
                self._phase = CombatPhase.PLANNING_CHEAT_SURVIVE
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_ACTION_MENU:
                self._phase = CombatPhase.PLANNING_CHEAT_SURVIVE
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_ABILITY:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_TARGET:
                # If targeting for basic_attack (from action menu), go back to action menu
                if self._selected_ability_id == "basic_attack":
                    self._phase = CombatPhase.PLANNING_ACTION_MENU
                else:
                    self._phase = CombatPhase.PLANNING_ABILITY
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_ITEM:
                self._selected_item_id = None
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_ITEM_TARGET:
                self._phase = CombatPhase.PLANNING_ITEM
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_CHEAT_ACTION:
                if self._cheat_extra_actions:
                    self._cheat_extra_actions.pop()
                    self._cheat_actions_remaining += 1
                else:
                    self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_CHEAT_TARGET:
                self._phase = CombatPhase.PLANNING_ACTION_MENU
                self._populate_choices()
                self._update_display()
            case CombatPhase.PLANNING_CONFIRM:
                # Go back to last character
                combat = self.app.combat_state
                if combat:
                    living = combat.living_players
                    self._current_char_index = len(living) - 1
                    if living:
                        cid = living[self._current_char_index].id
                        self._decisions.pop(cid, None)
                        self._current_decision = PlayerTurnDecision(combatant_id=cid)
                        self._phase = CombatPhase.PLANNING_CHEAT_SURVIVE
                        self._populate_choices()
                        self._update_display()

    def _finalize_character(self) -> None:
        if self._current_decision is None:
            return
        self._decisions[self._current_decision.combatant_id] = self._current_decision

        combat = self.app.combat_state
        if combat is None:
            return

        living = combat.living_players
        self._current_char_index += 1

        if self._current_char_index < len(living):
            self._phase = CombatPhase.PLANNING_CHEAT_SURVIVE
            self._current_decision = PlayerTurnDecision(combatant_id=living[self._current_char_index].id)
            self._populate_choices()
            self._update_display()
        else:
            self._phase = CombatPhase.PLANNING_CONFIRM
            self._populate_choices()
            self._update_display()

    # --- Display ---

    def _update_display(self) -> None:
        combat = self.app.combat_state
        run = self.app.run_state
        if combat is None or run is None:
            return

        self.query_one("#round-indicator", Label).update(f"[bold]Round {combat.round_number + 1}[/bold]")

        # Phase prompt
        prompt = self.query_one("#phase-prompt", Label)
        cid = self._current_combatant_id()
        name = self._combatant_names.get(cid, "") if cid else ""

        match self._phase:
            case CombatPhase.PLANNING_CHEAT_SURVIVE:
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Cheat, Survive, or Normal?")
            case CombatPhase.PLANNING_CHEAT_AP:
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — How many AP to spend?")
            case CombatPhase.PLANNING_ACTION_MENU:
                # Context-aware prompt for action menu
                if self._cheat_actions_remaining > 0 and self._current_decision and self._current_decision.primary_action is not None:
                    n = len(self._cheat_extra_actions) + 1
                    total = self._current_decision.cheat_actions if self._current_decision else 0
                    prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Cheat action {n}/{total}")
                elif self._partial_actions_remaining > 0 and self._current_decision and self._current_decision.primary_action is not None:
                    prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Bonus action ({self._partial_actions_remaining} remaining)")
                else:
                    prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Choose action")
            case CombatPhase.PLANNING_ABILITY:
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Choose ability")
            case CombatPhase.PLANNING_TARGET:
                aname = self._ability_names.get(self._selected_ability_id or "", "")
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — {aname} → Select target")
            case CombatPhase.PLANNING_ITEM:
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Choose item to use")
            case CombatPhase.PLANNING_ITEM_TARGET:
                item = self.app.game_data.items.get(self._selected_item_id or "")
                iname = item.name if item else "Item"
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — {iname} → Use on who?")
            case CombatPhase.PLANNING_CHEAT_ACTION:
                n = len(self._cheat_extra_actions) + 1
                total = self._current_decision.cheat_actions if self._current_decision else 0
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Cheat action {n}/{total}")
            case CombatPhase.PLANNING_CHEAT_TARGET:
                aname = self._ability_names.get(self._selected_ability_id or "", "")
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — {aname} → Select target (Cheat)")
            case CombatPhase.PLANNING_PARTIAL:
                prompt.update(f"[bold #e6c566]{name}[/bold #e6c566] — Bonus action ({self._partial_actions_remaining} remaining)")
            case CombatPhase.PLANNING_CONFIRM:
                prompt.update("[bold]All characters ready. Execute round?[/bold]")
            case CombatPhase.EXECUTING:
                prompt.update("[dim]Executing...[/dim]")
            case CombatPhase.COMBAT_OVER:
                prompt.update("")

        self._render_party_panel(combat)
        self._render_enemy_panel(combat)

    def _render_party_panel(self, combat: CombatState) -> None:
        lines: list[str] = []
        for p in combat.player_combatants:
            char = self.app.run_state.party.characters.get(p.id) if self.app.run_state else None
            name = self._combatant_names.get(p.id, p.id)
            job_name = ""
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else ""

            # Use progressive display state if available (during playback)
            hp = self._display_hp.get(p.id, p.current_hp)
            max_hp = self._display_max_hp.get(p.id, p.max_hp)
            alive = self._display_alive.get(p.id, p.is_alive)

            if not alive:
                lines.append(f"[#880000]{name} ({job_name} Lv{char.level if char else '?'}) DEAD[/#880000]")
                continue

            # Markers: ◄ for active turn, ► for target cursor
            is_active = self._current_combatant_id() == p.id and self._phase not in (CombatPhase.EXECUTING, CombatPhase.COMBAT_OVER)
            is_targeted = self._highlighted_target_id == p.id

            if is_targeted:
                marker = "[bold #e6c566]►[/bold #e6c566] "
            elif is_active:
                marker = "[bold #e6c566]◄[/bold #e6c566] "
            else:
                marker = "  "

            ap_str = f"  AP:{p.action_points}" if p.action_points > 0 else ""
            debt_str = f" D:{p.cheat_debt}" if p.cheat_debt > 0 else ""
            # Speed bonus: compare to slowest living enemy
            slowest_e = min((e.effective_stats.SPD for e in combat.living_enemies), default=0)
            spd_bonus = calculate_speed_bonus(p.effective_stats.SPD, slowest_e)
            ba_str = f" BA:{spd_bonus}" if spd_bonus > 0 else ""
            insight_str = f" I:{p.insight_stacks}" if p.insight_stacks > 0 else ""
            frenzy_str = f" F:{p.frenzy_level:.2f}x" if p.frenzy_level > 1.0 else ""

            hp_pct = hp / max(max_hp, 1)
            hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            bar_w = 12
            filled = int(hp_pct * bar_w)
            bar = f"[{hp_color}]{'█' * filled}[/{hp_color}][#333333]{'░' * (bar_w - filled)}[/#333333]"

            lines.append(f"{marker}[bold]{name}[/bold] ({job_name} Lv{char.level if char else '?'})")
            taunt_str = f" [bold #cc4444]TAUNTED[/bold #cc4444]" if p.taunted_by else ""
            lines.append(f"  {bar} {hp}/{max_hp}{ap_str}{ba_str}{debt_str}{insight_str}{frenzy_str}{taunt_str}")

        self.query_one("#party-display", Static).update("\n".join(lines))

    def _render_enemy_panel(self, combat: CombatState) -> None:
        lines: list[str] = []
        for e in combat.enemy_combatants:
            name = self._combatant_names.get(e.id, e.id)

            # Use progressive display state if available (during playback)
            hp = self._display_hp.get(e.id, e.current_hp)
            max_hp = self._display_max_hp.get(e.id, e.max_hp)
            alive = self._display_alive.get(e.id, e.is_alive)

            if not alive:
                lines.append(f"[#880000]{name} DEAD[/#880000]")
                continue

            is_targeted = self._highlighted_target_id == e.id
            marker = "[bold #e6c566]►[/bold #e6c566] " if is_targeted else "  "

            hp_pct = hp / max(max_hp, 1)
            hp_color = "#cc4444" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#44aa44"
            bar_w = 12
            filled = int(hp_pct * bar_w)
            bar = f"[{hp_color}]{'█' * filled}[/{hp_color}][#333333]{'░' * (bar_w - filled)}[/#333333]"

            taunt_str = f" [bold #cc4444]TAUNTED[/bold #cc4444]" if e.taunted_by else ""
            lines.append(f"{marker}[bold]{name}[/bold]")
            lines.append(f"  {bar} {hp}/{max_hp}{taunt_str}")

        self.query_one("#enemy-display", Static).update("\n".join(lines))

    # --- Round Execution ---

    def _execute_round(self) -> None:
        self._phase = CombatPhase.EXECUTING
        self._populate_choices()
        self._update_display()

        combat = self.app.combat_state
        if combat is None:
            return

        # Snapshot HP before processing — playback will apply changes progressively
        self._display_hp = {}
        self._display_alive = {}
        self._display_max_hp = {}
        for c in combat.player_combatants + combat.enemy_combatants:
            self._display_hp[c.id] = c.current_hp
            self._display_alive[c.id] = c.is_alive
            self._display_max_hp[c.id] = c.max_hp

        self._round_events_start = len(combat.log)

        enemy_templates = {}
        for e in combat.enemy_combatants:
            template_id = e.id.rsplit("_", 1)[0] if "_" in e.id else e.id
            if template_id in self.app.game_data.enemies:
                enemy_templates[template_id] = self.app.game_data.enemies[template_id]

        combat = self.app.game_loop.combat_engine.process_round(
            combat, self._decisions, enemy_templates
        )
        self.app.combat_state = combat

        # Remove consumed items from stash
        if combat.consumed_items and self.app.run_state is not None:
            run = self.app.run_state
            new_stash = list(run.party.stash)
            for item_id in combat.consumed_items:
                try:
                    new_stash.remove(item_id)
                except ValueError:
                    pass
            party = run.party.model_copy(update={"stash": new_stash})
            self.app.run_state = run.model_copy(update={"party": party})

        new_events = combat.log[self._round_events_start:]

        # Record round in battle history
        if self._encounter_record is not None:
            round_record = RoundRecord(
                round_number=combat.round_number,
                player_decisions=dict(self._decisions),
                events=list(new_events),
                player_hp={p.id: p.current_hp for p in combat.player_combatants},
                enemy_hp={e.id: e.current_hp for e in combat.enemy_combatants},
            )
            self._encounter_record.rounds.append(round_record)

            for ev in new_events:
                if ev.event_type == CombatEventType.DAMAGE_DEALT:
                    is_player = any(p.id == ev.actor_id for p in combat.player_combatants)
                    if is_player and not ev.details.get("self_damage"):
                        self._encounter_record.total_damage_dealt += ev.value
                    elif not is_player:
                        self._encounter_record.total_damage_taken += ev.value
                elif ev.event_type == CombatEventType.HEALING:
                    self._encounter_record.total_healing += ev.value
                elif ev.event_type == CombatEventType.DEATH:
                    if any(p.id == ev.target_id for p in combat.player_combatants):
                        self._encounter_record.character_deaths.append(ev.target_id)

        self._play_events(new_events)

    def _play_events(self, events: list) -> None:
        if self._verbose:
            self._playback_queue = [
                render_event(e, self._combatant_names, self._ability_names, verbose=True)
                for e in events
            ]
            self._raw_event_queue = list(events)
            self._event_delays = [get_event_delay(e) for e in events]
        else:
            self._playback_queue = render_events_summary(
                events, self._combatant_names, self._ability_names
            )
            self._raw_event_queue = []
            self._event_delays = [300] * len(self._playback_queue)
            # Summary mode: apply all changes up front (can't sync per-line)
            for e in events:
                self._apply_display_event(e)

        self._play_next_event()

    def _apply_display_event(self, event) -> None:
        """Apply a combat event to the progressive display state."""
        match event.event_type:
            case CombatEventType.DAMAGE_DEALT:
                tid = event.actor_id if event.details.get("self_damage") else event.target_id
                if tid in self._display_hp:
                    self._display_hp[tid] = max(0, self._display_hp[tid] - event.value)
            case CombatEventType.DOT_TICK:
                if event.target_id in self._display_hp:
                    self._display_hp[event.target_id] = max(0, self._display_hp[event.target_id] - event.value)
            case CombatEventType.HEALING:
                if event.target_id in self._display_hp:
                    cap = self._display_max_hp.get(event.target_id, 9999)
                    self._display_hp[event.target_id] = min(cap, self._display_hp[event.target_id] + event.value)
            case CombatEventType.DEATH:
                if event.target_id in self._display_alive:
                    self._display_alive[event.target_id] = False
                    self._display_hp[event.target_id] = 0
            case CombatEventType.RETALIATE_TRIGGERED:
                if event.target_id in self._display_hp:
                    self._display_hp[event.target_id] = max(0, self._display_hp[event.target_id] - event.value)

    def _play_next_event(self) -> None:
        if not self._playback_queue:
            self._on_playback_complete()
            return

        rendered = self._playback_queue.pop(0)
        delay = self._event_delays.pop(0) if self._event_delays else 250

        # Apply raw event to display state (verbose mode — 1:1 with rendered)
        if self._raw_event_queue:
            raw = self._raw_event_queue.pop(0)
            self._apply_display_event(raw)

        log = self.query_one("#combat-log", RichLog)
        log.write(rendered.text)

        # Re-render panels with progressive display state
        combat = self.app.combat_state
        if combat:
            self._render_party_panel(combat)
            self._render_enemy_panel(combat)

        self.set_timer(delay / 1000.0, self._play_next_event)

    def _on_playback_complete(self) -> None:
        # Clear progressive display — panels now read from actual combat state
        self._display_hp.clear()
        self._display_alive.clear()
        self._display_max_hp.clear()

        combat = self.app.combat_state
        if combat is None:
            return

        if combat.is_finished:
            self._phase = CombatPhase.COMBAT_OVER

            if self._encounter_record is not None:
                self._encounter_record.result = "victory" if combat.player_won else "defeat"
                self._encounter_record.rounds_taken = combat.round_number

                run = self.app.run_state
                if run is not None:
                    record = run.battle_record
                    encounters = list(record.encounters) + [self._encounter_record]
                    new_record = record.model_copy(update={"encounters": encounters})
                    self.app.run_state = run.model_copy(update={"battle_record": new_record})

            if combat.player_won:
                self._handle_victory()
            else:
                self._handle_defeat()
        else:
            self._start_planning()

    def _handle_victory(self) -> None:
        combat = self.app.combat_state
        run = self.app.run_state
        if combat is None or run is None:
            return

        defeated_enemies_data = [
            (e.id.rsplit("_", 1)[0] if "_" in e.id else e.id, e.level)
            for e in combat.enemy_combatants if not e.is_alive
        ]
        defeated_templates = [tmpl_id for tmpl_id, _lv in defeated_enemies_data]
        defeated_levels = [lv for _tmpl_id, lv in defeated_enemies_data]
        defeated_budgets: list[float] = []
        defeated_xp_mults: list[float] = []
        defeated_gold_mults: list[float] = []
        for tmpl_id, _lv in defeated_enemies_data:
            template = self.app.game_data.enemies.get(tmpl_id)
            if template:
                defeated_budgets.append(template.budget_multiplier)
                defeated_xp_mults.append(template.xp_multiplier or 0.0)
                defeated_gold_mults.append(template.gold_multiplier or 0.0)

        result = CombatResult(
            player_won=True,
            surviving_character_ids=[p.id for p in combat.living_players],
            surviving_character_hp={p.id: p.current_hp for p in combat.living_players},
            defeated_enemy_template_ids=defeated_templates,
            defeated_enemy_budget_multipliers=defeated_budgets,
            defeated_enemy_levels=defeated_levels,
            defeated_enemy_xp_multipliers=defeated_xp_mults,
            defeated_enemy_gold_multipliers=defeated_gold_mults,
            rounds_taken=combat.round_number,
            zone_level=self.app.game_data.zones[run.current_zone_id].zone_level if run.current_zone_id else 0,
            gold_stolen_by_enemies=combat.gold_stolen_by_enemies,
            gold_stolen_by_players=combat.gold_stolen_by_players,
        )

        new_run, loot = self.app.game_loop.resolve_combat_result(run, result)
        self.app.run_state = new_run

        from heresiarch.tui.screens.post_combat import PostCombatScreen

        self.app.switch_screen(PostCombatScreen(combat_result=result, loot=loot))

    def _handle_defeat(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        combat = self.app.combat_state
        result = CombatResult(
            player_won=False,
            rounds_taken=combat.round_number if combat else 0,
            zone_level=self.app.game_data.zones[run.current_zone_id].zone_level if run.current_zone_id else 0,
        )
        new_run, _ = self.app.game_loop.resolve_combat_result(run, result)
        self.app.run_state = new_run

        from heresiarch.tui.screens.death import DeathScreen

        self.app.switch_screen(DeathScreen())

    def action_toggle_verbose(self) -> None:
        self._verbose = not self._verbose
        mode = "verbose" if self._verbose else "summary"
        log = self.query_one("#combat-log", RichLog)
        log.write(f"[dim]Log mode: {mode}[/dim]")
