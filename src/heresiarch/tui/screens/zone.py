"""Zone overview screen — the hub between combat encounters."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, OptionList, Static
from textual.widgets.option_list import Option



class ZoneScreen(Screen):
    """Zone hub: shows progress, routes to combat, shop, party management."""

    CSS = """
    ZoneScreen {
        align: center middle;
    }
    #zone-box {
        width: 70;
        height: auto;
        padding: 1 2;
    }
    #party-summary {
        margin: 1 0;
    }
    #zone-actions {
        height: auto;
        max-height: 10;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("f", "fight", "Fight"),
        ("p", "party", "Party"),
        ("i", "inventory", "Inventory"),
        ("l", "leave", "Leave Zone"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._action_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="zone-box"):
            yield Static("", id="zone-header")
            yield Label("", id="zone-progress")
            yield Label("", id="zone-level")
            yield Static("", id="party-summary")
            yield OptionList(id="zone-actions")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_display()
        self.query_one("#zone-actions", OptionList).focus()

    def on_screen_resume(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        run = self.app.run_state
        if run is None or run.current_zone_id is None or run.zone_state is None:
            return

        zone = self.app.game_data.zones[run.current_zone_id]
        zs = run.zone_state
        total = len(zone.encounters)
        current = zs.current_encounter_index
        cleared = zs.is_cleared

        self.query_one("#zone-header", Static).update(
            f"[bold]{zone.name}[/bold] — {zone.region}"
        )

        progress = self.query_one("#zone-progress", Label)
        if cleared and zs.overstay_battles > 0:
            penalty_pct = min(zs.overstay_battles * 5, 100)
            progress.update(
                f"[bold #44aa44]Zone Cleared![/bold #44aa44]  "
                f"[dim]Overstay: {zs.overstay_battles} battles "
                f"(-{penalty_pct}% loot)[/dim]"
            )
        elif cleared:
            progress.update("[bold #44aa44]Zone Cleared![/bold #44aa44]")
        else:
            progress.update(f"Encounters: {current}/{total}")

        self.query_one("#zone-level", Label).update(f"Zone Level: {zone.zone_level}")

        # Party summary
        party = run.party
        lines: list[str] = []
        for char_id in party.active:
            char = party.characters.get(char_id)
            if char is None:
                continue
            job = self.app.game_data.jobs.get(char.job_id)
            if job is None:
                continue
            max_hp = char.max_hp or 1
            hp_pct = char.current_hp / max(max_hp, 1)
            hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            lines.append(
                f"  {char.name} (Lv{char.level} {job.name}) "
                f"HP: [{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
            )
        if party.money > 0:
            lines.append(f"  Money: [bold #e6c566]{party.money}G[/bold #e6c566]")
        self.query_one("#party-summary", Static).update("\n".join(lines))

        # Action list
        action_list = self.query_one("#zone-actions", OptionList)
        action_list.clear_options()
        self._action_keys = []

        if cleared:
            action_list.add_option(Option("[f] Keep Fighting (overstay)"))
            self._action_keys.append("fight")
        else:
            action_list.add_option(Option("[f] Fight"))
            self._action_keys.append("fight")

        action_list.add_option(Option("[p] Party"))
        self._action_keys.append("party")

        action_list.add_option(Option("[i] Inventory"))
        self._action_keys.append("inventory")

        action_list.add_option(Option("[l] Leave Zone"))
        self._action_keys.append("leave")

        action_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "zone-actions":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._action_keys):
            return

        action = self._action_keys[idx]
        match action:
            case "fight":
                self.action_fight()
            case "party":
                self.action_party()
            case "inventory":
                self.action_inventory()
            case "leave":
                self.action_leave()

    def action_fight(self) -> None:
        from heresiarch.tui.screens.combat import CombatScreen

        self.app.push_screen(CombatScreen())

    def action_party(self) -> None:
        from heresiarch.tui.screens.party import PartyScreen

        self.app.push_screen(PartyScreen())

    def action_inventory(self) -> None:
        from heresiarch.tui.screens.inventory import InventoryScreen

        self.app.push_screen(InventoryScreen())

    def action_leave(self) -> None:
        """Exit the current zone, heal, return to zone selection."""
        run = self.app.run_state
        if run is None:
            return

        run = self.app.game_loop.leave_zone(run)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone_select import ZoneSelectScreen

        self.app.switch_screen(ZoneSelectScreen())
