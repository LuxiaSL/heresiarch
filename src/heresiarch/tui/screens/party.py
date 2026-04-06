"""Party management screen — view characters, equip/unequip, swap, MC Mimic."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.formulas import calculate_max_hp


class PartyScreen(Screen):
    """View and manage party members, equipment, and MC job swap."""

    CSS = """
    PartyScreen {
        layout: horizontal;
    }
    #char-list-panel {
        width: 30;
        height: 100%;
        padding: 1;
    }
    #char-detail-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    #char-option-list {
        height: auto;
        max-height: 12;
    }
    #action-option-list {
        height: auto;
        max-height: 12;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._char_ids: list[str] = []
        self._action_keys: list[str] = []  # maps action option index → action key

    def compose(self) -> ComposeResult:
        with Vertical(id="char-list-panel"):
            yield Static("[bold]Party[/bold]")
            yield OptionList(id="char-option-list")
            yield Label("")
            yield Button("Back", id="btn-back")

        with Vertical(id="char-detail-panel"):
            yield Static("", id="char-detail")
            yield Label("", id="action-prompt")
            yield OptionList(id="action-option-list")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_char_list()
        self.query_one("#char-option-list", OptionList).focus()

    def on_screen_resume(self) -> None:
        self._populate_char_list()

    def _populate_char_list(self) -> None:
        """Fill the character OptionList."""
        run = self.app.run_state
        if run is None:
            return

        char_list = self.query_one("#char-option-list", OptionList)
        char_list.clear_options()
        self._char_ids = []

        for char_id in run.party.active:
            char = run.party.characters.get(char_id)
            if char:
                mc = " [MC]" if char.is_mc else ""
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                char_list.add_option(Option(f"{char.name} (Lv{char.level} {job_name}){mc}"))
                self._char_ids.append(char_id)

        for char_id in run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                char_list.add_option(Option(f"{char.name} (Lv{char.level} {job_name}) [reserve]"))
                self._char_ids.append(char_id)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "char-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._char_ids):
                self._show_char_detail(self._char_ids[idx])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "char-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._char_ids):
                self._show_char_actions(self._char_ids[idx])

        elif event.option_list.id == "action-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._action_keys):
                self._handle_action(self._action_keys[idx])

    def _show_char_detail(self, char_id: str) -> None:
        """Render character stats in the detail panel."""
        run = self.app.run_state
        if run is None:
            return

        char = run.party.characters.get(char_id)
        if char is None:
            return

        job = self.app.game_data.jobs.get(char.job_id)
        job_name = job.name if job else "?"
        max_hp = calculate_max_hp(
            job.base_hp, job.hp_growth, char.level, char.base_stats.DEF
        ) if job else 0

        stats = char.base_stats
        lines: list[str] = [
            f"[bold]{char.name}[/bold] — Lv{char.level} {job_name}",
            f"  HP: {char.current_hp}/{max_hp}  XP: {char.xp}",
            "",
            "[bold]Stats[/bold]",
            f"  STR [bold]{stats.STR:>3}[/bold]  MAG [bold]{stats.MAG:>3}[/bold]  "
            f"DEF [bold]{stats.DEF:>3}[/bold]  RES [bold]{stats.RES:>3}[/bold]  "
            f"SPD [bold]{stats.SPD:>3}[/bold]",
            "",
            "[bold]Equipment[/bold]",
        ]

        for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            item_id = char.equipment.get(slot)
            if item_id:
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                lines.append(f"  {slot}: {name}")
            else:
                lines.append(f"  {slot}: [dim]empty[/dim]")

        lines.append("")
        lines.append("[bold]Abilities[/bold]")
        for aid in char.abilities:
            ability = self.app.game_data.abilities.get(aid)
            name = ability.name if ability else aid
            innate = " (innate)" if ability and ability.is_innate else ""
            lines.append(f"  {name}{innate}")

        if char.is_mc and char.growth_history:
            lines.append("")
            lines.append("[bold]Growth History[/bold]")
            for jid, levels in char.growth_history:
                j = self.app.game_data.jobs.get(jid)
                jname = j.name if j else jid
                lines.append(f"  {jname}: {levels} levels")

        self.query_one("#char-detail", Static).update("\n".join(lines))

    def _show_char_actions(self, char_id: str) -> None:
        """Populate the action OptionList for a selected character."""
        run = self.app.run_state
        if run is None:
            return

        char = run.party.characters.get(char_id)
        if char is None:
            return

        action_list = self.query_one("#action-option-list", OptionList)
        action_list.clear_options()
        self._action_keys = []

        prompt = self.query_one("#action-prompt", Label)
        prompt.update(f"[bold]{char.name}[/bold] — select action:")

        # Equip/Unequip
        for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            item_id = char.equipment.get(slot)
            if item_id:
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                action_list.add_option(Option(f"Unequip {slot}: {name}"))
                self._action_keys.append(f"unequip:{char_id}:{slot}")

        # Equip from stash
        for item_id in run.party.stash:
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            if item and not item.is_consumable:
                slot = item.slot.value if hasattr(item.slot, "value") else str(item.slot)
                action_list.add_option(Option(f"Equip {item.name} → {slot}"))
                self._action_keys.append(f"equip:{char_id}:{item_id}:{slot}")

        # Swap
        if char_id in run.party.active:
            for rid in run.party.reserve:
                rc = run.party.characters.get(rid)
                if rc:
                    action_list.add_option(Option(f"Swap with {rc.name} (reserve)"))
                    self._action_keys.append(f"swap:{char_id}:{rid}")
        elif char_id in run.party.reserve:
            for aid in run.party.active:
                ac = run.party.characters.get(aid)
                if ac:
                    action_list.add_option(Option(f"Swap with {ac.name} (active)"))
                    self._action_keys.append(f"swap:{aid}:{char_id}")

        # MC Mimic
        if char.is_mc:
            for cid, c in run.party.characters.items():
                if c.job_id != char.job_id:
                    job = self.app.game_data.jobs.get(c.job_id)
                    jname = job.name if job else c.job_id
                    action_list.add_option(Option(f"Mimic → {jname}"))
                    self._action_keys.append(f"mimic:{c.job_id}")

        action_list.add_option(Option("Cancel"))
        self._action_keys.append("cancel")

        action_list.focus()

    def _handle_action(self, key: str) -> None:
        """Execute an action from the action list."""
        run = self.app.run_state
        if run is None:
            return

        parts = key.split(":")

        try:
            match parts[0]:
                case "unequip":
                    _, char_id, slot = parts
                    self.app.run_state = self.app.game_loop.unequip_item(run, char_id, slot)
                case "equip":
                    _, char_id, item_id, slot = parts
                    self.app.run_state = self.app.game_loop.equip_item(run, char_id, item_id, slot)
                case "swap":
                    _, active_id, reserve_id = parts
                    self.app.run_state = self.app.game_loop.swap_party_member(run, active_id, reserve_id)
                case "mimic":
                    _, job_id = parts
                    self.app.run_state = self.app.game_loop.mc_swap_job(run, job_id)
                case "cancel":
                    pass
        except ValueError:
            pass

        # Refresh after action
        self._populate_char_list()
        self.query_one("#action-option-list", OptionList).clear_options()
        self._action_keys = []
        self.query_one("#action-prompt", Label).update("")
        self.query_one("#char-option-list", OptionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
