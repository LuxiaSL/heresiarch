"""Live map preview tool — Textual app for inspecting ASCII maps.

Reuses the actual MapViewer widget from the TUI, so rendering is
pixel-perfect to what the game shows. Watches the YAML file for
changes and reloads automatically.

Usage:
    uv run python -m heresiarch.tools.map_preview
    uv run heresiarch-preview
    uv run heresiarch-preview data/region_shinto/maps/zone_03.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.models.region_map import AsciiMap
from heresiarch.tui.widgets.map_viewer import AnchorStatus, MapViewer

# How often to check for file changes (seconds)
_POLL_INTERVAL = 0.5

# Default data directory (relative to cwd)
_DATA_DIR = Path("data")


def _load_map(path: Path) -> AsciiMap:
    """Load an ASCII map from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty YAML file: {path}")
    if "region_id" in data and "map_id" not in data:
        data["map_id"] = data.pop("region_id")
    for anchor_data in data.get("anchors", []):
        if "zone_id" in anchor_data and "id" not in anchor_data:
            anchor_data["id"] = anchor_data.pop("zone_id")
    return AsciiMap(**data)


def _discover_maps(data_dir: Path) -> dict[str, list[Path]]:
    """Find all map YAML files, grouped by category."""
    groups: dict[str, list[Path]] = {
        "Region Maps": [],
        "Town Maps": [],
        "Zone Path Maps": [],
    }

    for region_dir in sorted(data_dir.glob("region_*")):
        maps_dir = region_dir / "maps"
        if not maps_dir.is_dir():
            continue
        for path in sorted(maps_dir.glob("*.yaml")):
            try:
                m = _load_map(path)
            except Exception:
                continue

            has_encounters = any(
                a.anchor_type in ("encounter", "boss") for a in m.anchors
            )
            has_buildings = any(
                a.anchor_type == "building" for a in m.anchors
            )

            if has_encounters:
                groups["Zone Path Maps"].append(path)
            elif has_buildings:
                groups["Town Maps"].append(path)
            else:
                groups["Region Maps"].append(path)

    return groups


# ---------------------------------------------------------------------------
# File picker screen
# ---------------------------------------------------------------------------


class FilePickerScreen(Screen):
    """Select a map YAML file to preview."""

    CSS = """
    FilePickerScreen {
        align: center middle;
    }
    #picker-box {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: tall #333355;
    }
    #picker-title {
        text-align: center;
        margin-bottom: 1;
    }
    #file-list {
        height: auto;
        max-height: 30;
    }
    """

    BINDINGS = [
        ("q", "quit_app", "Quit"),
    ]

    def __init__(self, data_dir: Path) -> None:
        super().__init__()
        self._data_dir = data_dir
        self._file_paths: list[Path] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-box"):
            yield Static(
                "[bold #e6c566]Map Preview[/bold #e6c566]  "
                "[dim]Select a map file[/dim]",
                id="picker-title",
            )
            yield OptionList(id="file-list")
        yield Footer()

    def on_mount(self) -> None:
        groups = _discover_maps(self._data_dir)
        option_list = self.query_one("#file-list", OptionList)
        self._file_paths = []

        first_group = True
        for group_name, paths in groups.items():
            if not paths:
                continue
            if not first_group:
                option_list.add_option(Option("", disabled=True))
            first_group = False
            option_list.add_option(
                Option(f"[bold dim]── {group_name} ──[/bold dim]", disabled=True)
            )
            for path in paths:
                idx = len(self._file_paths)
                try:
                    rel = path.relative_to(Path.cwd())
                except ValueError:
                    rel = path
                option_list.add_option(Option(f"  {rel}", id=str(idx)))
                self._file_paths.append(path)

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is None:
            return
        try:
            idx = int(event.option.id)
        except (ValueError, TypeError):
            return
        if 0 <= idx < len(self._file_paths):
            self.app.push_screen(MapPreviewScreen(self._file_paths[idx]))

    def action_quit_app(self) -> None:
        self.app.exit()


# ---------------------------------------------------------------------------
# Map preview screen
# ---------------------------------------------------------------------------


class MapPreviewScreen(Screen):
    """Preview a single map with live reload on file changes."""

    CSS = """
    MapPreviewScreen {
        layout: vertical;
    }
    #preview-map-area {
        height: 1fr;
        border: tall #333355;
    }
    #preview-info {
        height: auto;
        min-height: 4;
        max-height: 8;
        padding: 0 2;
        border: tall #333355;
    }
    #anchor-detail {
        width: 1fr;
        height: auto;
    }
    #map-meta {
        width: auto;
        min-width: 36;
        height: auto;
        padding-left: 2;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "quit_app", "Quit"),
        ("1", "set_progress(0)", "0 cleared"),
        ("2", "set_progress(1)", "1 cleared"),
        ("3", "set_progress(2)", "2 cleared"),
        ("4", "set_progress(3)", "3 cleared"),
        ("5", "set_progress(4)", "4 cleared"),
        ("6", "set_progress(5)", "5 cleared"),
        ("7", "set_progress(6)", "6 cleared"),
        ("8", "set_progress(7)", "All cleared"),
        ("0", "all_available", "All available"),
    ]

    def __init__(self, file_path: Path) -> None:
        super().__init__()
        self._file_path = file_path
        self._last_mtime: float = 0.0
        self._ascii_map: AsciiMap | None = None
        self._progress: int = -1  # -1 = all available, 0+ = N encounters cleared
        self._poll_timer = None

    def compose(self) -> ComposeResult:
        yield Vertical(id="preview-map-area")
        with Horizontal(id="preview-info"):
            yield Static("", id="anchor-detail")
            yield Static("", id="map-meta")
        yield Footer()

    def on_mount(self) -> None:
        self._load_and_render()
        self._poll_timer = self.set_interval(_POLL_INTERVAL, self._check_reload)

    def on_screen_resume(self) -> None:
        self._load_and_render()

    def _check_reload(self) -> None:
        """Poll file mtime and reload if changed."""
        try:
            mtime = self._file_path.stat().st_mtime
        except OSError:
            return
        if mtime != self._last_mtime:
            self._load_and_render()

    def _load_and_render(self) -> None:
        """Load the map YAML and mount a fresh MapViewer."""
        try:
            self._ascii_map = _load_map(self._file_path)
            self._last_mtime = self._file_path.stat().st_mtime
        except Exception as e:
            container = self.query_one("#preview-map-area", Vertical)
            # Clear existing children
            for child in list(container.children):
                child.remove()
            container.mount(Static(f"[bold red]Error loading map:[/bold red]\n{e}"))
            return

        self._mount_viewer()
        self._render_meta()

    def _mount_viewer(self) -> None:
        """Build and mount a MapViewer with current settings."""
        if self._ascii_map is None:
            return

        container = self.query_one("#preview-map-area", Vertical)
        # Clear existing children
        for child in list(container.children):
            child.remove()

        ascii_map = self._ascii_map
        statuses, navigable, style_overrides = self._compute_display(ascii_map)

        initial = navigable[0] if navigable else None

        viewer = MapViewer(
            ascii_map=ascii_map,
            anchor_statuses=statuses,
            navigable_ids=navigable,
            initial_id=initial,
            style_overrides=style_overrides,
        )
        container.mount(viewer)
        viewer.focus()

    def _compute_display(
        self, ascii_map: AsciiMap
    ) -> tuple[
        dict[str, AnchorStatus],
        list[str],
        dict[tuple[int, int], str],
    ]:
        """Compute anchor statuses, navigable list, and path coloring."""
        statuses: dict[str, AnchorStatus] = {}
        navigable: list[str] = []

        enc_anchors = [
            a for a in ascii_map.anchors
            if a.anchor_type in ("encounter", "boss")
        ]
        enc_anchors_sorted = sorted(enc_anchors, key=lambda a: a.col)
        is_zone_path = len(enc_anchors) > 0

        if is_zone_path and self._progress >= 0:
            # Simulate encounter progress: N encounters cleared
            for anchor in ascii_map.anchors:
                if anchor.anchor_type == "exit":
                    statuses[anchor.id] = AnchorStatus.AVAILABLE
                    navigable.append(anchor.id)
                elif anchor.anchor_type in ("encounter", "boss"):
                    # Find this anchor's position in sorted order
                    idx = next(
                        (i for i, a in enumerate(enc_anchors_sorted) if a.id == anchor.id),
                        -1,
                    )
                    if idx < self._progress:
                        statuses[anchor.id] = AnchorStatus.CLEARED
                        navigable.append(anchor.id)
                    elif idx == self._progress:
                        statuses[anchor.id] = AnchorStatus.AVAILABLE
                        navigable.append(anchor.id)
                    else:
                        statuses[anchor.id] = AnchorStatus.LOCKED
                else:
                    statuses[anchor.id] = AnchorStatus.AVAILABLE
                    navigable.append(anchor.id)
        else:
            # Default: all available
            for anchor in ascii_map.anchors:
                statuses[anchor.id] = AnchorStatus.AVAILABLE
                navigable.append(anchor.id)

        # Path coloring for zone path maps
        style_overrides: dict[tuple[int, int], str] = {}
        if is_zone_path and self._progress >= 0:
            style_overrides = self._compute_path_coloring(
                ascii_map, enc_anchors_sorted, statuses
            )

        return statuses, navigable, style_overrides

    def _compute_path_coloring(
        self,
        ascii_map: AsciiMap,
        enc_anchors_sorted: list,
        statuses: dict[str, AnchorStatus],
    ) -> dict[tuple[int, int], str]:
        """Color path row green/gray based on simulated progress."""
        overrides: dict[tuple[int, int], str] = {}
        if not enc_anchors_sorted:
            return overrides

        path_row = enc_anchors_sorted[0].row

        # Find frontier column
        frontier_col = 0
        exit_anchor = ascii_map.anchor_for_id("exit")
        if exit_anchor:
            frontier_col = exit_anchor.col

        for anchor in enc_anchors_sorted:
            status = statuses.get(anchor.id, AnchorStatus.LOCKED)
            if status in (AnchorStatus.CLEARED, AnchorStatus.AVAILABLE):
                frontier_col = anchor.col
                if status == AnchorStatus.AVAILABLE:
                    break
            else:
                break

        art = ascii_map.art
        if path_row < 0 or path_row >= len(art):
            return overrides

        line = art[path_row]
        for c, char in enumerate(line):
            if char == " ":
                continue
            is_anchor = any(
                a.row == path_row and a.col == c for a in ascii_map.anchors
            )
            if is_anchor:
                continue
            if c <= frontier_col:
                overrides[(path_row, c)] = "#44aa44"
            else:
                overrides[(path_row, c)] = "#333333"

        return overrides

    def _render_meta(self) -> None:
        """Show map metadata in the info panel."""
        if self._ascii_map is None:
            return

        m = self._ascii_map
        try:
            rel = self._file_path.relative_to(Path.cwd())
        except ValueError:
            rel = self._file_path

        enc_count = sum(1 for a in m.anchors if a.anchor_type == "encounter")
        boss_count = sum(1 for a in m.anchors if a.anchor_type == "boss")
        other_count = len(m.anchors) - enc_count - boss_count

        lines = [
            f"[bold #e6c566]{m.name}[/bold #e6c566]  [dim]{m.map_id}[/dim]",
            f"  {m.width}x{m.height}  |  {len(m.anchors)} anchors",
        ]
        if enc_count > 0 or boss_count > 0:
            lines.append(
                f"  {enc_count} encounter + {boss_count} boss"
                + (f" + {other_count} other" if other_count else "")
            )
            if self._progress >= 0:
                lines.append(
                    f"  [dim]Progress: {self._progress} cleared  "
                    f"(1-8 cycle, 0 all available)[/dim]"
                )
            else:
                lines.append(
                    "  [dim]1-8 simulate progress, 0 all available[/dim]"
                )
        lines.append(f"  [dim]{rel}[/dim]")

        try:
            self.query_one("#map-meta", Static).update("\n".join(lines))
        except Exception:
            pass

    # --- Event handlers ---

    def on_map_viewer_anchor_highlighted(
        self, event: MapViewer.AnchorHighlighted
    ) -> None:
        anchor = self._ascii_map.anchor_for_id(event.anchor_id) if self._ascii_map else None
        if anchor is None:
            return

        status = "?"
        if self._ascii_map:
            statuses, _, _ = self._compute_display(self._ascii_map)
            s = statuses.get(event.anchor_id)
            status = s.value if s else "?"

        lines = [
            f"[bold]{event.anchor_id}[/bold]  ({event.anchor_type})",
            f"  row={anchor.row}  col={anchor.col}  status={status}",
        ]
        try:
            self.query_one("#anchor-detail", Static).update("\n".join(lines))
        except Exception:
            pass

    # --- Actions ---

    def action_set_progress(self, n: int) -> None:
        """Set simulated encounter progress."""
        if self._ascii_map is None:
            return
        enc_count = sum(
            1 for a in self._ascii_map.anchors
            if a.anchor_type in ("encounter", "boss")
        )
        # Clamp: 7 = "all cleared" means progress == enc_count
        self._progress = min(n, enc_count)
        self._mount_viewer()
        self._render_meta()

    def action_all_available(self) -> None:
        """Reset to all-available mode."""
        self._progress = -1
        self._mount_viewer()
        self._render_meta()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.exit()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class MapPreviewApp(App):
    """Standalone map preview tool."""

    TITLE = "Heresiarch Map Preview"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, initial_file: Path | None = None, data_dir: Path = _DATA_DIR) -> None:
        super().__init__()
        self._initial_file = initial_file
        self._data_dir = data_dir

    def on_mount(self) -> None:
        if self._initial_file:
            self.push_screen(MapPreviewScreen(self._initial_file))
        else:
            self.push_screen(FilePickerScreen(self._data_dir))


def main() -> None:
    """CLI entry point."""
    initial_file: Path | None = None
    data_dir = _DATA_DIR

    args = sys.argv[1:]
    for arg in args:
        p = Path(arg)
        if p.suffix == ".yaml" and p.exists():
            initial_file = p
        elif p.is_dir():
            data_dir = p

    app = MapPreviewApp(initial_file=initial_file, data_dir=data_dir)
    app.run()


if __name__ == "__main__":
    main()
