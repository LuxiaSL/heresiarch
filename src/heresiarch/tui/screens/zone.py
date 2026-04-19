"""Zone screen — ASCII path map showing encounter progression."""

from __future__ import annotations

import random

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from heresiarch.engine.models.region_map import AsciiMap
from heresiarch.tui.widgets.map_viewer import AnchorStatus, MapViewer


class ZoneScreen(Screen):
    """Zone hub: path map with navigable encounter nodes."""

    CSS = """
    ZoneScreen {
        layout: vertical;
    }
    #zone-map-area {
        height: 1fr;
        border: tall #333355;
    }
    #zone-info-panel {
        height: auto;
        min-height: 5;
        max-height: 8;
        padding: 0 2;
        border: tall #333355;
    }
    #encounter-detail {
        width: 1fr;
        height: auto;
    }
    #zone-party-summary {
        width: auto;
        min-width: 32;
        height: auto;
        padding-left: 2;
    }
    """

    BINDINGS = [
        ("f", "fight", "Fight"),
        ("p", "party", "Party"),
        ("i", "inventory", "Inventory"),
        ("l", "leave", "Leave Zone"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(id="zone-map-area")
        with Horizontal(id="zone-info-panel"):
            yield Static("", id="encounter-detail")
            yield Static("", id="zone-party-summary")
        yield Footer()

    def on_mount(self) -> None:
        self._build_map()
        self._render_party()

    def on_screen_resume(self) -> None:
        self._render_party()
        # Re-render the detail for the currently highlighted anchor
        try:
            viewer = self.query_one(MapViewer)
            anchor_id = viewer.selected_anchor_id
            if anchor_id:
                atype = viewer._anchor_types.get(anchor_id, "encounter")
                self._show_encounter_detail(anchor_id, atype)
        except Exception:
            pass

    # --- Map construction ---

    def _build_map(self) -> None:
        """Build the zone path map from run state and mount it."""
        run = self.app.run_state
        if run is None or run.current_zone_id is None or run.zone_state is None:
            return

        zone_id = run.current_zone_id
        zone = self.app.game_data.zones.get(zone_id)
        zs = run.zone_state
        if zone is None:
            return

        ascii_map = self.app.game_data.maps.get(zone_id)
        if ascii_map is None:
            self._fallback_display()
            return

        is_overstay = zs.is_cleared or zone.is_endless

        # Build anchor statuses and navigable list
        statuses: dict[str, AnchorStatus] = {}
        navigable: list[str] = ["exit"]
        statuses["exit"] = AnchorStatus.AVAILABLE

        if zone.is_endless:
            # Endless zones: all encounter anchors on the map are always
            # available — there are no fixed encounters to track.
            for anchor in ascii_map.anchors:
                if anchor.anchor_type in ("encounter", "boss"):
                    statuses[anchor.id] = AnchorStatus.AVAILABLE
                    navigable.append(anchor.id)
        elif is_overstay:
            # Cleared zone re-entered: all encounters reachable
            for i in range(len(zone.encounters)):
                anchor_id = f"enc_{i}"
                statuses[anchor_id] = AnchorStatus.CLEARED
                navigable.append(anchor_id)
        else:
            for i in range(len(zone.encounters)):
                anchor_id = f"enc_{i}"
                if i in zs.encounters_completed:
                    statuses[anchor_id] = AnchorStatus.CLEARED
                    navigable.append(anchor_id)
                elif i == zs.current_encounter_index:
                    statuses[anchor_id] = AnchorStatus.AVAILABLE
                    navigable.append(anchor_id)
                    break  # can't navigate past the frontier
                else:
                    statuses[anchor_id] = AnchorStatus.LOCKED

            # Set statuses for any remaining locked encounters
            for i in range(len(zone.encounters)):
                anchor_id = f"enc_{i}"
                if anchor_id not in statuses:
                    statuses[anchor_id] = AnchorStatus.LOCKED

        # Compute path coloring
        style_overrides = self._compute_path_coloring(ascii_map, statuses)

        # Determine initial cursor position
        initial: str | None = None
        if zone.is_endless:
            # Endless zones: always start on the encounter node
            enc_anchors = [
                a.id for a in ascii_map.anchors
                if a.anchor_type in ("encounter", "boss")
            ]
            initial = enc_anchors[0] if enc_anchors else "exit"
        elif is_overstay:
            # Random position among encounter nodes for scouring flavor.
            # Exclude boss nodes that act as travel tiles (next_zone) and
            # the exit — player shouldn't land on navigation-only nodes.
            excluded: set[int] = set()
            if zone.next_zone:
                for i, enc in enumerate(zone.encounters):
                    if enc.is_boss:
                        excluded.add(i)
            enc_ids = [
                f"enc_{i}"
                for i in range(len(zone.encounters))
                if i not in excluded
            ]
            if enc_ids:
                rng = random.Random(zs.overstay_battles)
                initial = rng.choice(enc_ids)
        else:
            # Start on the next uncleared encounter
            for i in range(len(zone.encounters)):
                anchor_id = f"enc_{i}"
                if statuses.get(anchor_id) == AnchorStatus.AVAILABLE:
                    initial = anchor_id
                    break
        if initial is None and navigable:
            initial = navigable[-1]

        # Mount the map viewer
        container = self.query_one("#zone-map-area", Vertical)
        viewer = MapViewer(
            ascii_map=ascii_map,
            anchor_statuses=statuses,
            navigable_ids=navigable,
            initial_id=initial,
            style_overrides=style_overrides,
        )
        container.mount(viewer)
        viewer.focus()

        if initial:
            atype = "exit"
            anchor = ascii_map.anchor_for_id(initial)
            if anchor:
                atype = anchor.anchor_type
            self._show_encounter_detail(initial, atype)

    def _compute_path_coloring(
        self,
        ascii_map: AsciiMap,
        statuses: dict[str, AnchorStatus],
    ) -> dict[tuple[int, int], str]:
        """Color path characters green (cleared) or gray (locked) by column."""
        overrides: dict[tuple[int, int], str] = {}

        # Find all encounter/boss anchors on the map
        enc_anchors = [
            a for a in ascii_map.anchors
            if a.anchor_type in ("encounter", "boss")
        ]
        if not enc_anchors:
            return overrides

        # All encounter anchors should share the same row (linear path)
        path_row = enc_anchors[0].row

        # Find the frontier column — column of the current/available encounter.
        # Everything up to this column is "traversed" (green).
        # If all cleared, frontier is the rightmost encounter.
        frontier_col = 0
        exit_anchor = ascii_map.anchor_for_id("exit")
        if exit_anchor:
            frontier_col = exit_anchor.col

        for anchor in sorted(enc_anchors, key=lambda a: a.col):
            status = statuses.get(anchor.id, AnchorStatus.LOCKED)
            if status == AnchorStatus.CLEARED:
                frontier_col = anchor.col
            elif status == AnchorStatus.AVAILABLE:
                frontier_col = anchor.col
                break
            else:
                break

        # Color the path row
        cleared_style = "#44aa44"
        locked_style = "#333333"

        art = ascii_map.art
        if path_row < 0 or path_row >= len(art):
            return overrides

        line = art[path_row]
        for c, char in enumerate(line):
            if char == " ":
                continue  # skip empty space
            # Don't override anchor positions — markers handle those
            is_anchor = any(
                a.row == path_row and a.col == c for a in ascii_map.anchors
            )
            if is_anchor:
                continue
            if c <= frontier_col:
                overrides[(path_row, c)] = cleared_style
            else:
                overrides[(path_row, c)] = locked_style

        return overrides

    def _fallback_display(self) -> None:
        """Simple text fallback if no map data is available."""
        run = self.app.run_state
        if run is None or run.current_zone_id is None or run.zone_state is None:
            return

        zone = self.app.game_data.zones.get(run.current_zone_id)
        zs = run.zone_state
        if zone is None:
            return

        total = len(zone.encounters)
        current = zs.current_encounter_index

        lines = [
            f"[bold]{zone.name}[/bold] — {zone.region}",
            f"Encounters: {current}/{total}" if not zs.is_cleared else "[bold #44aa44]Zone Cleared![/bold #44aa44]",
            f"Zone Level: {zone.zone_level}",
            "",
            "[dim]No zone path map data found.[/dim]",
        ]
        container = self.query_one("#zone-map-area", Vertical)
        container.mount(Static("\n".join(lines)))

    # --- Event handlers ---

    def on_map_viewer_anchor_highlighted(
        self, event: MapViewer.AnchorHighlighted
    ) -> None:
        self._show_encounter_detail(event.anchor_id, event.anchor_type)

    def on_map_viewer_anchor_selected(
        self, event: MapViewer.AnchorSelected
    ) -> None:
        if event.anchor_type == "exit":
            self._leave_zone()
        elif event.anchor_type in ("encounter", "boss"):
            if self._is_travel_tile(event.anchor_id):
                self._travel_to_next_zone()
            else:
                self._try_fight(event.anchor_id)

    # --- Detail panel ---

    def _show_encounter_detail(self, anchor_id: str, anchor_type: str) -> None:
        run = self.app.run_state
        if run is None or run.current_zone_id is None or run.zone_state is None:
            return

        zone = self.app.game_data.zones.get(run.current_zone_id)
        zs = run.zone_state
        if zone is None:
            return

        total = len(zone.encounters)
        is_overstay = zs.is_cleared or zone.is_endless

        if anchor_type == "exit":
            lines = [
                f"[bold #e6c566]{zone.name}[/bold #e6c566] (Lv.{zone.zone_level})",
                "  Return to zone select.",
                "  [dim][Enter] leave zone[/dim]",
            ]
        elif anchor_type in ("encounter", "boss"):
            enc_idx = self._anchor_to_index(anchor_id)

            # Endless zones have no encounter templates — show zone info directly
            if zone.is_endless:
                lines = [
                    f"[bold #e6c566]{zone.name}[/bold #e6c566]  "
                    f"[dim]Endless Zone[/dim]",
                    f"  Battles fought: {zs.overstay_battles}",
                    "  [dim][Enter] fight[/dim]",
                ]
            elif enc_idx is not None and 0 <= enc_idx < total:
                enc = zone.encounters[enc_idx]
                is_boss = enc.is_boss
                label = "Boss" if is_boss else f"Encounter {enc_idx + 1}/{total}"
                is_cleared = enc_idx in zs.encounters_completed

                if self._is_travel_tile(anchor_id):
                    next_name = self._get_next_zone_name()
                    lines = [
                        f"[bold #e6c566]{zone.name}[/bold #e6c566]  "
                        f"[bold #44aa44]Zone Cleared![/bold #44aa44]",
                        f"  Travel to [bold #c8a2c8]{next_name}[/bold #c8a2c8]",
                        "  [dim][Enter] travel[/dim]",
                    ]
                elif is_overstay:
                    penalty_pct = min(zs.overstay_battles * 5, 100)
                    if zs.overstay_battles > 0:
                        lines = [
                            f"[bold #e6c566]{zone.name}[/bold #e6c566]  "
                            f"[bold #44aa44]Zone Cleared![/bold #44aa44]",
                            f"  Overstay: {zs.overstay_battles} battles "
                            f"(-{penalty_pct}% loot)",
                            "  [dim][Enter] fight (overstay)[/dim]",
                        ]
                    else:
                        lines = [
                            f"[bold #e6c566]{zone.name}[/bold #e6c566]  "
                            f"[bold #44aa44]Zone Cleared![/bold #44aa44]",
                            "  [dim][Enter] fight (overstay)[/dim]",
                        ]
                elif is_cleared:
                    lines = [
                        f"[bold #e6c566]{zone.name}[/bold #e6c566] (Lv.{zone.zone_level})",
                        f"  {label}  [bold #44aa44][CLEARED][/bold #44aa44]",
                    ]
                else:
                    lines = [
                        f"[bold #e6c566]{zone.name}[/bold #e6c566] (Lv.{zone.zone_level})",
                        f"  {label}  —  Encounters: "
                        f"{len(zs.encounters_completed)}/{total}",
                        "  [dim][Enter] fight[/dim]",
                    ]
            else:
                lines = [f"[dim]{anchor_id}[/dim]"]
        else:
            lines = [f"[dim]{anchor_id}[/dim]"]

        try:
            self.query_one("#encounter-detail", Static).update("\n".join(lines))
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

        try:
            self.query_one("#zone-party-summary", Static).update(
                "\n".join(lines)
            )
        except Exception:
            pass

    # --- Actions ---

    def _try_fight(self, anchor_id: str) -> None:
        """Start combat if the encounter is fightable."""
        run = self.app.run_state
        if run is None or run.zone_state is None:
            return

        zs = run.zone_state
        zone = self.app.game_data.zones.get(run.current_zone_id or "")
        if zone is None:
            return

        # Endless zones: always fightable
        if zone.is_endless:
            self._start_combat()
            return

        # Overstay (cleared zone): any node triggers overstay fight
        if zs.is_cleared:
            self._start_combat()
            return

        enc_idx = self._anchor_to_index(anchor_id)
        if enc_idx is None:
            return

        # Only fight uncleared encounters
        if enc_idx in zs.encounters_completed:
            return

        if enc_idx == zs.current_encounter_index:
            self._start_combat()

    def _start_combat(self) -> None:
        from heresiarch.tui.screens.combat import CombatScreen

        self.app.push_screen(CombatScreen())

    def _leave_zone(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        anchor_id = run.current_zone_id
        zs = run.zone_state
        payload = {
            "zone_id": run.current_zone_id,
            "zone_cleared": zs.is_cleared if zs else False,
            "overstay_battles": zs.overstay_battles if zs else 0,
            "current_encounter_index": zs.current_encounter_index if zs else 0,
            "reason": "voluntary_leave",
        }
        run = self.app.game_loop.leave_zone(run)
        run = run.record_macro("leave_zone", payload)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone_select import ZoneSelectScreen

        self.app.switch_screen(ZoneSelectScreen(initial_anchor_id=anchor_id))

    def action_fight(self) -> None:
        """Shortcut: jump to next encounter and fight."""
        run = self.app.run_state
        if run is None or run.zone_state is None or run.current_zone_id is None:
            return

        zone = self.app.game_data.zones.get(run.current_zone_id)
        zs = run.zone_state
        if zone is None:
            return

        is_overstay = zs.is_cleared or zone.is_endless
        if is_overstay:
            self._start_combat()
            return

        if zs.current_encounter_index < len(zone.encounters):
            self._start_combat()

    def action_party(self) -> None:
        from heresiarch.tui.screens.party import PartyScreen

        self.app.push_screen(PartyScreen())

    def action_inventory(self) -> None:
        from heresiarch.tui.screens.inventory import InventoryScreen

        self.app.push_screen(InventoryScreen())

    def action_leave(self) -> None:
        """Shortcut: leave zone immediately."""
        self._leave_zone()

    # --- Helpers ---

    def _is_travel_tile(self, anchor_id: str) -> bool:
        """Check if a boss anchor should act as a travel tile to the next zone."""
        run = self.app.run_state
        if run is None or run.zone_state is None or run.current_zone_id is None:
            return False
        zone = self.app.game_data.zones.get(run.current_zone_id)
        if zone is None or not zone.next_zone:
            return False
        if not run.zone_state.is_cleared:
            return False
        # Only the boss anchor becomes a travel tile
        enc_idx = self._anchor_to_index(anchor_id)
        if enc_idx is None:
            return False
        return enc_idx < len(zone.encounters) and zone.encounters[enc_idx].is_boss

    def _get_next_zone_name(self) -> str:
        """Get the display name of the next_zone, if set."""
        run = self.app.run_state
        if run is None or run.current_zone_id is None:
            return "???"
        zone = self.app.game_data.zones.get(run.current_zone_id)
        if zone is None or not zone.next_zone:
            return "???"
        next_z = self.app.game_data.zones.get(zone.next_zone)
        return next_z.name if next_z else zone.next_zone

    def _travel_to_next_zone(self) -> None:
        """Leave current zone and enter the next zone's region."""
        run = self.app.run_state
        if run is None or run.current_zone_id is None:
            return
        zone = self.app.game_data.zones.get(run.current_zone_id)
        if zone is None or not zone.next_zone:
            return

        zs = run.zone_state
        leave_payload = {
            "zone_id": run.current_zone_id,
            "zone_cleared": zs.is_cleared if zs else False,
            "overstay_battles": zs.overstay_battles if zs else 0,
            "current_encounter_index": zs.current_encounter_index if zs else 0,
            "reason": "travel_next_zone",
            "next_zone_id": zone.next_zone,
        }
        run = self.app.game_loop.leave_zone(run)
        run = run.record_macro("leave_zone", leave_payload)
        self.app.run_state = run

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        # Determine if the next zone is in a different region
        next_z = self.app.game_data.zones.get(zone.next_zone)
        if next_z and next_z.region != zone.region:
            # Cross-region travel — go to zone select for the new region
            from heresiarch.tui.screens.zone_select import ZoneSelectScreen

            self.app.switch_screen(
                ZoneSelectScreen(initial_anchor_id=zone.next_zone)
            )
        else:
            # Same region — enter the zone directly
            run = self.app.game_loop.enter_zone(run, zone.next_zone)
            run = run.record_macro(
                "enter_zone",
                {"zone_id": zone.next_zone, "via": "travel_next_zone"},
            )
            self.app.run_state = run
            try:
                self.app.save_manager.autosave(run)
            except Exception:
                pass
            self.app.switch_screen(ZoneScreen())

    @staticmethod
    def _anchor_to_index(anchor_id: str) -> int | None:
        """Parse encounter anchor ID to encounter index. 'enc_3' -> 3."""
        if anchor_id.startswith("enc_"):
            try:
                return int(anchor_id[4:])
            except ValueError:
                return None
        return None
