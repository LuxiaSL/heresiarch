"""Zone overview screen — the hub between combat encounters."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from heresiarch.engine.formulas import calculate_max_hp


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
    .zone-btn-row {
        height: auto;
        margin-top: 1;
    }
    .zone-btn {
        margin: 0 1 0 0;
    }
    """

    BINDINGS = [
        ("f", "fight", "Fight"),
        ("p", "party", "Party"),
        ("i", "inventory", "Inventory"),
        ("s", "shop", "Shop"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="zone-box"):
            yield Static("", id="zone-header")
            yield Label("", id="zone-progress")
            yield Label("", id="zone-level")
            yield Static("", id="party-summary")
            with Horizontal(classes="zone-btn-row"):
                yield Button("[f] Fight", variant="primary", id="btn-fight", classes="zone-btn")
                yield Button("[p] Party", id="btn-party", classes="zone-btn")
                yield Button("[i] Inventory", id="btn-inventory", classes="zone-btn")
                yield Button("[s] Shop", id="btn-shop", classes="zone-btn", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_display()
        self.query_one("#btn-fight", Button).focus()

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
        if cleared:
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
            max_hp = calculate_max_hp(
                job.base_hp, job.hp_growth, char.level, char.base_stats.DEF
            )
            hp_pct = char.current_hp / max(max_hp, 1)
            hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            lines.append(
                f"  {char.name} (Lv{char.level} {job.name}) "
                f"HP: [{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
            )
        if party.money > 0:
            lines.append(f"  Money: [bold #e6c566]{party.money}G[/bold #e6c566]")
        self.query_one("#party-summary", Static).update("\n".join(lines))

        # Button states
        self.query_one("#btn-fight", Button).disabled = cleared
        self.query_one("#btn-shop", Button).disabled = len(zone.shop_item_pool) == 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-fight":
                self.action_fight()
            case "btn-party":
                self.action_party()
            case "btn-inventory":
                self.action_inventory()
            case "btn-shop":
                self.action_shop()

    def action_fight(self) -> None:
        from heresiarch.tui.screens.combat import CombatScreen

        self.app.push_screen(CombatScreen())

    def action_party(self) -> None:
        from heresiarch.tui.screens.party import PartyScreen

        self.app.push_screen(PartyScreen())

    def action_inventory(self) -> None:
        from heresiarch.tui.screens.inventory import InventoryScreen

        self.app.push_screen(InventoryScreen())

    def action_shop(self) -> None:
        from heresiarch.tui.screens.shop import ShopScreen

        self.app.push_screen(ShopScreen())
