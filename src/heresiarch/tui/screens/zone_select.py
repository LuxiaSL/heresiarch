"""Zone/town selection screen — ASCII map viewer with anchor markers and panning."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from heresiarch.engine.models.region_map import AsciiMap
from heresiarch.tui.widgets.map_viewer import AnchorStatus, MapViewer


class ZoneSelectScreen(Screen):
    """Choose a zone or town to enter from a pannable ASCII map."""

    CSS = """
    ZoneSelectScreen {
        layout: vertical;
    }
    #map-area {
        height: 1fr;
        border: tall #333355;
    }
    #info-panel {
        height: auto;
        min-height: 5;
        max-height: 8;
        padding: 0 2;
        border: tall #333355;
    }
    #zone-detail {
        width: 1fr;
        height: auto;
    }
    #party-summary {
        width: auto;
        min-width: 32;
        height: auto;
        padding-left: 2;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._navigable_ids: list[str] = []

    def compose(self) -> ComposeResult:
        yield Vertical(id="map-area")
        with Horizontal(id="info-panel"):
            yield Static("", id="zone-detail")
            yield Static("", id="party-summary")
        yield Footer()

    def on_mount(self) -> None:
        self._build_map()
        self._render_party()

    def _build_map(self) -> None:
        """Build the map viewer from run state and mount it into #map-area."""
        run = self.app.run_state
        if run is None:
            return

        ascii_map = self._get_region_map()
        if ascii_map is None:
            self._fallback_list()
            return

        # Build anchor statuses and navigable list
        available = self.app.game_loop.get_available_zones(run)
        available_ids = {z.id for z in available}
        completed = set(run.zones_completed)

        anchor_statuses: dict[str, AnchorStatus] = {}
        navigable: list[str] = []

        for anchor in ascii_map.anchors:
            aid = anchor.id

            if anchor.anchor_type == "town":
                # Town anchor — check town unlock
                if self.app.game_loop.is_town_unlocked(run, aid):
                    anchor_statuses[aid] = AnchorStatus.AVAILABLE
                    navigable.append(aid)
                else:
                    anchor_statuses[aid] = AnchorStatus.LOCKED
            else:
                # Zone anchor
                if aid in completed:
                    anchor_statuses[aid] = AnchorStatus.CLEARED
                    navigable.append(aid)
                elif aid in available_ids:
                    anchor_statuses[aid] = AnchorStatus.AVAILABLE
                    navigable.append(aid)
                else:
                    anchor_statuses[aid] = AnchorStatus.LOCKED

        self._navigable_ids = navigable

        # Find a good initial anchor: first non-cleared available, or first navigable
        initial = None
        for aid in navigable:
            if anchor_statuses.get(aid) == AnchorStatus.AVAILABLE:
                initial = aid
                break
        if initial is None and navigable:
            initial = navigable[0]

        # Mount the map viewer
        container = self.query_one("#map-area", Vertical)
        viewer = MapViewer(
            ascii_map=ascii_map,
            anchor_statuses=anchor_statuses,
            navigable_ids=navigable,
            initial_id=initial,
        )
        container.mount(viewer)
        viewer.focus()

        if initial:
            self._show_anchor_detail(initial)

    def _get_region_map(self) -> AsciiMap | None:
        """Look up the region map for the current run's zones."""
        maps = getattr(self.app, "game_data", None)
        if maps is None:
            return None
        region_maps = maps.maps
        run = self.app.run_state
        if run is not None:
            for zone in self.app.game_data.zones.values():
                if zone.region in region_maps:
                    return region_maps[zone.region]
        if region_maps:
            return next(iter(region_maps.values()))
        return None

    def _fallback_list(self) -> None:
        """Simple text fallback if no map data is available."""
        container = self.query_one("#map-area", Vertical)
        container.mount(Static("[dim]No region map data found.[/dim]"))

    # --- Event handlers from MapViewer ---

    def on_map_viewer_anchor_highlighted(
        self, event: MapViewer.AnchorHighlighted
    ) -> None:
        self._show_anchor_detail(event.anchor_id, event.anchor_type)

    def on_map_viewer_anchor_selected(
        self, event: MapViewer.AnchorSelected
    ) -> None:
        if event.anchor_type == "town":
            self._enter_town(event.anchor_id)
        else:
            self._enter_zone(event.anchor_id)

    # --- Detail panel ---

    def _show_anchor_detail(
        self, anchor_id: str, anchor_type: str = "zone"
    ) -> None:
        # Check if it's a town
        town = self.app.game_data.towns.get(anchor_id)
        if town is not None:
            self._show_town_detail(anchor_id)
            return

        # Otherwise show zone detail
        self._show_zone_detail(anchor_id)

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
        recruit = (
            f"{zone.recruitment_chance:.0%}" if zone.recruitment_chance > 0 else "No"
        )

        status_tag = ""
        if is_cleared:
            status_tag = " [bold #44aa44][CLEARED][/bold #44aa44]"

        lines = [
            f"[bold #e6c566]{zone.name}[/bold #e6c566] (Lv.{zone.zone_level}){status_tag}",
            f"  Encounters: {encounters} ({boss_count} boss)  |  Recruit: {recruit}",
        ]
        if is_cleared:
            lines.append("  [dim]Overstay penalty applies to loot drops[/dim]")
        lines.append(
            "  [dim][Enter] embark  [Up/Down] cycle zones  [Esc] back[/dim]"
        )

        try:
            self.query_one("#zone-detail", Static).update("\n".join(lines))
        except Exception:
            pass

    def _show_town_detail(self, town_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return
        town = self.app.game_data.towns.get(town_id)
        if town is None:
            return

        lodge_cost = self.app.game_loop.get_lodge_cost(run) or "?"
        shop_items = len(self.app.game_loop.resolve_town_shop(run))

        lines = [
            f"[bold #c8a2c8]{town.name}[/bold #c8a2c8]",
            f"  Lodge rest: {lodge_cost}G  |  Shop: {shop_items} items available",
            "  [dim][Enter] visit  [Up/Down] cycle  [Esc] back[/dim]",
        ]

        try:
            self.query_one("#zone-detail", Static).update("\n".join(lines))
        except Exception:
            pass

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
        lines.append(f"  Zones cleared: {len(run.zones_completed)}")

        try:
            self.query_one("#party-summary", Static).update("\n".join(lines))
        except Exception:
            pass

    def _enter_zone(self, zone_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        run = self.app.game_loop.enter_zone(run, zone_id)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())

    def _enter_town(self, town_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        run = self.app.game_loop.enter_town(run, town_id)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.town import TownScreen

        self.app.switch_screen(TownScreen())

    def action_go_back(self) -> None:
        """Return to title."""
        self.app.run_state = None
        from heresiarch.tui.screens.title import TitleScreen

        self.app.switch_screen(TitleScreen())
