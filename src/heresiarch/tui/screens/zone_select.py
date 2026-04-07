"""Zone selection screen — pick which zone to enter."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, OptionList, Static
from textual.widgets.option_list import Option


class ZoneSelectScreen(Screen):
    """Choose a zone to enter from the unlocked set."""

    CSS = """
    ZoneSelectScreen {
        align: center middle;
    }
    #zone-select-box {
        width: 80;
        height: auto;
        padding: 1 2;
    }
    #zone-list {
        height: auto;
        max-height: 16;
        margin: 1 0;
    }
    #zone-detail {
        height: auto;
        min-height: 4;
        padding: 0 1;
        border: tall #333355;
    }
    #party-summary {
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._zone_ids: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="zone-select-box"):
            yield Static("[bold]Choose a Zone[/bold]")
            yield Label("")
            yield OptionList(id="zone-list")
            yield Static("", id="zone-detail")
            yield Static("", id="party-summary")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_zones()
        self._render_party()
        zone_list = self.query_one("#zone-list", OptionList)
        zone_list.focus()
        if self._zone_ids:
            zone_list.highlighted = 0

    def _populate_zones(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        zone_list = self.query_one("#zone-list", OptionList)
        zone_list.clear_options()
        self._zone_ids = []

        available = self.app.game_loop.get_available_zones(run)
        completed = set(run.zones_completed)

        for zone in available:
            cleared_tag = " [bold #44aa44][CLEARED][/bold #44aa44]" if zone.id in completed else ""
            final_tag = " [bold #e6c566][FINAL][/bold #e6c566]" if zone.is_final else ""
            label = f"{zone.name} (Lv{zone.zone_level}){cleared_tag}{final_tag}"
            zone_list.add_option(Option(label))
            self._zone_ids.append(zone.id)

    def _render_party(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        lines: list[str] = ["[bold]Party[/bold]"]
        for char_id in run.party.active:
            char = run.party.characters.get(char_id)
            if char is None:
                continue
            job = self.app.game_data.jobs.get(char.job_id)
            job_name = job.name if job else "?"
            max_hp = char.max_hp or 1
            hp_pct = char.current_hp / max(max_hp, 1)
            hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            lines.append(
                f"  {char.name} (Lv{char.level} {job_name}) "
                f"HP: [{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
            )
        if run.party.money > 0:
            lines.append(f"  Money: [bold #e6c566]{run.party.money}G[/bold #e6c566]")
        lines.append(f"  Zones cleared: {len(run.zones_completed)}")

        self.query_one("#party-summary", Static).update("\n".join(lines))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id != "zone-list":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._zone_ids):
            return
        self._show_zone_detail(self._zone_ids[idx])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "zone-list":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._zone_ids):
            return
        self._enter_zone(self._zone_ids[idx])

    def _show_zone_detail(self, zone_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return
        zone = self.app.game_data.zones.get(zone_id)
        if zone is None:
            return

        is_cleared = zone_id in run.zones_completed
        encounters = len(zone.encounters)
        boss_count = sum(1 for e in zone.encounters if e.is_boss)
        shop = "Yes" if zone.shop_item_pool else "No"
        recruit = f"{zone.recruitment_chance:.0%}" if zone.recruitment_chance > 0 else "No"

        lines = [
            f"[bold #e6c566]{zone.name}[/bold #e6c566] — {zone.region}",
            f"  Level: {zone.zone_level}  |  Encounters: {encounters} ({boss_count} boss)",
            f"  Shop: {shop}  |  Recruitment: {recruit}",
        ]
        if is_cleared:
            lines.append("  [dim]Cleared — overstay penalty applies to loot drops[/dim]")

        self.query_one("#zone-detail", Static).update("\n".join(lines))

    def _enter_zone(self, zone_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        # Heal between zones
        run = self.app.game_loop.enter_safe_zone(run)
        run = self.app.game_loop.enter_zone(run, zone_id)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())

    def action_go_back(self) -> None:
        """Return to title."""
        self.app.run_state = None
        from heresiarch.tui.screens.title import TitleScreen

        self.app.switch_screen(TitleScreen())
