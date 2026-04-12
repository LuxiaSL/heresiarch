"""Town screen — hub with ASCII map, routes to Lodge, Shop, Tavern."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from heresiarch.engine.models.region_map import AsciiMap
from heresiarch.tui.widgets.map_viewer import AnchorStatus, MapViewer


class TownScreen(Screen):
    """Town interior: shows ASCII map with Lodge/Shop/Tavern, routes to each."""

    CSS = """
    TownScreen {
        layout: vertical;
    }
    #town-map-area {
        height: 1fr;
        border: tall #333355;
    }
    #town-info-panel {
        height: auto;
        min-height: 5;
        max-height: 8;
        padding: 0 2;
        border: tall #333355;
    }
    #building-detail {
        width: 1fr;
        height: auto;
    }
    #town-party-summary {
        width: auto;
        min-width: 32;
        height: auto;
        padding-left: 2;
    }
    """

    BINDINGS = [
        ("escape", "leave_town", "Leave Town"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(id="town-map-area")
        with Horizontal(id="town-info-panel"):
            yield Static("", id="building-detail")
            yield Static("", id="town-party-summary")
        yield Footer()

    def on_mount(self) -> None:
        self._build_map()
        self._render_party()

    def on_screen_resume(self) -> None:
        self._render_party()

    def _build_map(self) -> None:
        """Load the town interior map and mount the viewer."""
        run = self.app.run_state
        if run is None or run.current_town_id is None:
            return

        town_map = self._get_town_map(run.current_town_id)
        if town_map is None:
            container = self.query_one("#town-map-area", Vertical)
            container.mount(Static("[dim]No town map data found.[/dim]"))
            return

        # All buildings are always available in town
        statuses: dict[str, AnchorStatus] = {}
        navigable: list[str] = []
        for anchor in town_map.anchors:
            statuses[anchor.id] = AnchorStatus.AVAILABLE
            navigable.append(anchor.id)

        initial = navigable[0] if navigable else None

        container = self.query_one("#town-map-area", Vertical)
        viewer = MapViewer(
            ascii_map=town_map,
            anchor_statuses=statuses,
            navigable_ids=navigable,
            initial_id=initial,
        )
        container.mount(viewer)
        viewer.focus()

        if initial:
            self._show_building_detail(initial)

    def _get_town_map(self, town_id: str) -> AsciiMap | None:
        """Look up the interior map for the current town."""
        return self.app.game_data.maps.get(town_id)

    # --- Event handlers ---

    def on_map_viewer_anchor_highlighted(
        self, event: MapViewer.AnchorHighlighted
    ) -> None:
        self._show_building_detail(event.anchor_id)

    def on_map_viewer_anchor_selected(
        self, event: MapViewer.AnchorSelected
    ) -> None:
        match event.anchor_id:
            case "shop":
                self._open_shop()
            case "lodge":
                self._open_lodge()
            case "tavern":
                self._open_tavern()
            case "exit":
                self.action_leave_town()

    # --- Building detail ---

    def _show_building_detail(self, building_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        match building_id:
            case "shop":
                shop_items = self.app.game_loop.resolve_town_shop(run)
                lines = [
                    "[bold #e6c566]Shop[/bold #e6c566]",
                    f"  {len(shop_items)} items available  |  Gold: {run.party.money}G",
                    "  [dim][Enter] browse wares[/dim]",
                ]
            case "lodge":
                cost = self.app.game_loop.get_lodge_cost(run)
                lines = [
                    "[bold #c8a2c8]Lodge[/bold #c8a2c8]",
                    f"  Rest cost: {cost}G  |  Gold: {run.party.money}G",
                    "  Full party heal. Resets incomplete zone progress.",
                    "  [dim][Enter] rest[/dim]",
                ]
            case "tavern":
                lines = [
                    "[bold #e6c566]Tavern[/bold #e6c566]",
                    "  The tavern is quiet for now.",
                    "  [dim]NPCs and hints coming soon.[/dim]",
                ]
            case "exit":
                lines = [
                    "[bold #e6c566]Exit[/bold #e6c566]",
                    "  Leave town and return to the region map.",
                    "  [dim][Enter] leave town[/dim]",
                ]
            case _:
                lines = [f"[dim]{building_id}[/dim]"]

        try:
            self.query_one("#building-detail", Static).update("\n".join(lines))
        except Exception:
            pass

    def _render_party(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        town = self.app.game_data.towns.get(run.current_town_id or "")
        town_name = town.name if town else "Town"

        lines: list[str] = [f"[bold #c8a2c8]{town_name}[/bold #c8a2c8]"]
        for char_id in run.party.active:
            char = run.party.characters.get(char_id)
            if char is None:
                continue
            job = self.app.game_data.jobs.get(char.job_id)
            job_name = job.name if job else "?"
            max_hp = char.max_hp or 1
            hp_pct = char.current_hp / max(max_hp, 1)
            hp_color = (
                "#44aa44"
                if hp_pct > 0.5
                else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            )
            lines.append(
                f"  {char.name} (Lv{char.level} {job_name}) "
                f"HP: [{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
            )
        if run.party.money > 0:
            lines.append(
                f"  Gold: [bold #e6c566]{run.party.money}G[/bold #e6c566]"
            )

        try:
            self.query_one("#town-party-summary", Static).update(
                "\n".join(lines)
            )
        except Exception:
            pass

    # --- Navigation ---

    def _open_shop(self) -> None:
        from heresiarch.tui.screens.shop import ShopScreen

        self.app.push_screen(ShopScreen())

    def _open_lodge(self) -> None:
        from heresiarch.tui.screens.lodge import LodgeScreen

        self.app.push_screen(LodgeScreen())

    def _open_tavern(self) -> None:
        from heresiarch.tui.screens.tavern import TavernScreen

        self.app.push_screen(TavernScreen())

    def action_leave_town(self) -> None:
        """Leave town, return to zone select."""
        run = self.app.run_state
        if run is None:
            return

        run = self.app.game_loop.leave_town(run)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone_select import ZoneSelectScreen

        self.app.switch_screen(ZoneSelectScreen())
