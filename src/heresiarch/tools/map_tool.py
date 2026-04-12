"""Heresiarch map authoring tool.

Preview, validate, inspect, and interactively place zone anchors on ASCII
region maps.

Usage:
    python -m heresiarch.tools.map_tool preview <map_file> [options]
    python -m heresiarch.tools.map_tool validate <map_file> [--data-dir PATH]
    python -m heresiarch.tools.map_tool inspect <map_file> <row> <col> [options]
    python -m heresiarch.tools.map_tool find <map_file> <char>
    python -m heresiarch.tools.map_tool place <map_file>

Examples:
    # Preview the Shinto slimes map with zone_01 cleared and zone_02 selected
    python -m heresiarch.tools.map_tool preview data/maps/shinto_slimes.yaml \\
        --cleared zone_01 --select zone_02

    # Preview with all zones available and a coordinate ruler
    python -m heresiarch.tools.map_tool preview data/maps/shinto_slimes.yaml --all-available --ruler

    # Validate anchors against zone data
    python -m heresiarch.tools.map_tool validate data/maps/shinto_slimes.yaml

    # Inspect a 15x30 region centered on row 8, col 52 (with ruler)
    python -m heresiarch.tools.map_tool inspect data/maps/shinto_slimes.yaml 8 52

    # Inspect a custom-sized crop
    python -m heresiarch.tools.map_tool inspect data/maps/shinto_slimes.yaml 8 52 --rows 20 --cols 50

    # Find all 'o' characters (zone marker placeholders)
    python -m heresiarch.tools.map_tool find data/maps/shinto_slimes.yaml o

    # Find all '~' characters (water terrain)
    python -m heresiarch.tools.map_tool find data/maps/shinto_slimes.yaml "~"

    # Interactive anchor placement — arrow keys to move, Enter to drop
    python -m heresiarch.tools.map_tool place data/maps/shinto_slimes.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.text import Text

from heresiarch.engine.models.region_map import RegionMap

# Reuse the color constants from the map viewer
_TERRAIN_COLORS: dict[str, str] = {
    "~": "#335588",
    "*": "#886655",
    ".": "#444444",
    "|": "#555555",
    "/": "#555555",
    "\\": "#555555",
    "_": "#555555",
    "-": "#444444",
    "=": "#555555",
    "(": "#555555",
    ")": "#555555",
    "#": "#555555",
}
_LETTER_COLOR = "#666666"
_DEFAULT_COLOR = "#555555"

_STATUS_STYLES: dict[str, tuple[str, str]] = {
    # status -> (marker_char, style)
    "locked": ("?", "#555555"),
    "available": ("o", "bold #e6c566"),
    "cleared": ("*", "bold #44aa44"),
}
_SELECTED_MARKER = "X"
_SELECTED_STYLE = "bold #e6c566"
_FLAG_STYLE = "bold #e6c566"
_CURSOR_STYLE = "bold reverse #e6c566"


def _load_map(path: Path) -> RegionMap:
    """Load an ASCII map from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    # Migrate old field names
    if "region_id" in data and "map_id" not in data:
        data["map_id"] = data.pop("region_id")
    for anchor_data in data.get("anchors", []):
        if "zone_id" in anchor_data and "id" not in anchor_data:
            anchor_data["id"] = anchor_data.pop("zone_id")
    return RegionMap(**data)


def _style_for_char(char: str) -> str:
    """Map a terrain character to its display color."""
    if char in _TERRAIN_COLORS:
        return _TERRAIN_COLORS[char]
    if char.isalpha():
        return _LETTER_COLOR
    if char == " ":
        return ""
    return _DEFAULT_COLOR


# ---------------------------------------------------------------------------
# preview
# ---------------------------------------------------------------------------


def cmd_preview(args: argparse.Namespace) -> None:
    """Render the map to the terminal with colored markers."""
    console = Console()
    region_map = _load_map(Path(args.map_file))

    cleared = set(args.cleared) if args.cleared else set()
    available = set(args.available) if args.available else set()
    selected = args.select

    if args.all_available:
        available = {a.id for a in region_map.anchors}

    # Auto-determine statuses if nothing specified
    if not cleared and not available and not args.all_available:
        # Default: first zone available, rest locked
        if region_map.anchors:
            available.add(region_map.anchors[0].id)

    # Ensure selected zone is in available or cleared
    if selected and selected not in available and selected not in cleared:
        available.add(selected)

    # If no selection specified, select the first available
    if not selected:
        for a in region_map.anchors:
            if a.id in available:
                selected = a.id
                break

    # Build grid
    width = region_map.width
    grid = [list(line.ljust(width)) for line in region_map.art]

    # Composite markers
    for anchor in region_map.anchors:
        r, c = anchor.row, anchor.col
        if r < 0 or r >= len(grid) or c < 0 or c >= width:
            continue

        zid = anchor.id
        is_selected = zid == selected

        if is_selected:
            grid[r][c] = _SELECTED_MARKER
            if r >= 1 and c + 1 < width:
                grid[r - 1][c] = "|"
                grid[r - 1][c + 1] = ">"
        elif zid in cleared:
            grid[r][c] = "*"
        elif zid in available:
            grid[r][c] = "o"
        else:
            grid[r][c] = "?"

    # Render with Rich
    text = _render_grid(grid, region_map, selected, cleared, available)

    console.print()
    console.print(f"  [bold #c8a2c8]{region_map.name}[/bold #c8a2c8]  ({width}x{region_map.height})")
    console.print()

    if args.ruler:
        _print_with_ruler(console, grid, width)
    else:
        console.print(text)

    console.print()

    # Legend
    console.print(
        "  [bold #e6c566]X[/bold #e6c566] selected  "
        "[bold #e6c566]o[/bold #e6c566] available  "
        "[bold #44aa44]*[/bold #44aa44] cleared  "
        "[#555555]?[/#555555] locked"
    )
    console.print()


def _render_grid(
    grid: list[list[str]],
    region_map: RegionMap,
    selected: str | None,
    cleared: set[str],
    available: set[str],
) -> Text:
    """Convert a character grid to styled Rich Text."""
    width = region_map.width

    # Build quick lookup for anchor positions -> (zone_id, is_selected)
    anchor_positions: dict[tuple[int, int], tuple[str, bool]] = {}
    for anchor in region_map.anchors:
        anchor_positions[(anchor.row, anchor.col)] = (
            anchor.id,
            anchor.id == selected,
        )
        # Flag position
        if anchor.id == selected and anchor.row >= 1:
            anchor_positions[(anchor.row - 1, anchor.col)] = (anchor.id, True)
            if anchor.col + 1 < width:
                anchor_positions[(anchor.row - 1, anchor.col + 1)] = (
                    anchor.id,
                    True,
                )

    text = Text()
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            key = (r, c)
            if key in anchor_positions:
                zid, is_sel = anchor_positions[key]
                if is_sel:
                    text.append(char, style=_SELECTED_STYLE if char in (_SELECTED_MARKER, "|", ">") else _FLAG_STYLE)
                elif zid in cleared:
                    text.append(char, style="bold #44aa44")
                elif zid in available:
                    text.append(char, style="bold #e6c566")
                else:
                    text.append(char, style="#555555")
            else:
                text.append(char, style=_style_for_char(char))
        if r < len(grid) - 1:
            text.append("\n")

    return text


# ---------------------------------------------------------------------------
# ruler helpers
# ---------------------------------------------------------------------------


def _col_ruler(start: int, end: int, gutter: int) -> tuple[str, str, str]:
    """Build a 3-line column ruler header (tens, ones, ticks).

    Returns (tens_line, ones_line, tick_line) with leading gutter space.
    """
    pad = " " * gutter
    tens = []
    ones = []
    ticks = []
    for c in range(start, end):
        tens.append(str((c // 10) % 10) if c % 10 == 0 else " ")
        ones.append(str(c % 10))
        ticks.append("|" if c % 10 == 0 else ("." if c % 5 == 0 else " "))
    return (
        pad + "".join(tens),
        pad + "".join(ones),
        pad + "".join(ticks),
    )


def _print_with_ruler(
    console: Console,
    grid: list[list[str]],
    width: int,
    *,
    row_start: int = 0,
    col_start: int = 0,
    col_end: int | None = None,
) -> None:
    """Print a character grid with row numbers and column ruler."""
    col_end = col_end or width
    gutter = 5  # width of row number gutter

    # Column ruler
    tens, ones, ticks = _col_ruler(col_start, col_end, gutter)
    console.print(f"[dim]{tens}[/dim]")
    console.print(f"[dim]{ones}[/dim]")
    console.print(f"[dim]{ticks}[/dim]")

    # Rows with line numbers
    for r, row in enumerate(grid):
        row_num = row_start + r
        prefix = f"[dim]{row_num:4d}[/dim] "
        line = "".join(row[col_start:col_end])
        console.print(prefix + line)


# ---------------------------------------------------------------------------
# inspect — crop a region with ruler for precise coordinate reading
# ---------------------------------------------------------------------------


def cmd_inspect(args: argparse.Namespace) -> None:
    """Show a cropped region of the map with coordinate rulers."""
    console = Console()
    region_map = _load_map(Path(args.map_file))

    center_row = args.row
    center_col = args.col
    half_rows = args.rows // 2
    half_cols = args.cols // 2

    row_start = max(0, center_row - half_rows)
    row_end = min(region_map.height, center_row + half_rows + 1)
    col_start = max(0, center_col - half_cols)
    col_end = min(region_map.width, center_col + half_cols + 1)

    # Build cropped grid
    width = region_map.width
    grid: list[list[str]] = []
    for r in range(row_start, row_end):
        line = region_map.art[r] if r < len(region_map.art) else ""
        padded = list(line.ljust(width))
        grid.append(padded)

    console.print()
    console.print(
        f"  [bold #c8a2c8]{region_map.name}[/bold #c8a2c8]  "
        f"inspecting rows {row_start}-{row_end - 1}, cols {col_start}-{col_end - 1}  "
        f"(center: {center_row},{center_col})"
    )
    console.print()

    _print_with_ruler(
        console,
        grid,
        width,
        row_start=row_start,
        col_start=col_start,
        col_end=col_end,
    )

    # Show anchors within the visible region
    visible_anchors = [
        a
        for a in region_map.anchors
        if row_start <= a.row < row_end and col_start <= a.col < col_end
    ]
    if visible_anchors:
        console.print()
        console.print("  [bold]Anchors in view:[/bold]")
        for a in visible_anchors:
            console.print(f"    {a.id:<12} ({a.row:3d},{a.col:3d})")

    # Show character at center
    char_at = " "
    if 0 <= center_row < region_map.height:
        line = region_map.art[center_row]
        if 0 <= center_col < len(line):
            char_at = line[center_col]
    console.print()
    console.print(f"  [bold]Center ({center_row},{center_col}):[/bold] char='{char_at}'")
    console.print()


# ---------------------------------------------------------------------------
# find — locate all instances of a character with positions
# ---------------------------------------------------------------------------


def cmd_find(args: argparse.Namespace) -> None:
    """Find all occurrences of a character in the map art."""
    console = Console()
    region_map = _load_map(Path(args.map_file))

    target = args.char
    if len(target) != 1:
        console.print(f"[red]Error: expected a single character, got '{target}'[/red]")
        sys.exit(1)

    hits: list[tuple[int, int, str]] = []
    for r, line in enumerate(region_map.art):
        for c, ch in enumerate(line):
            if ch == target:
                # Grab surrounding context
                ctx_start = max(0, c - 10)
                ctx_end = min(len(line), c + 11)
                context = line[ctx_start:ctx_end]
                hits.append((r, c, context))

    console.print()
    console.print(
        f"  [bold #c8a2c8]{region_map.name}[/bold #c8a2c8]  "
        f"finding '{target}'  ({len(hits)} hit{'s' if len(hits) != 1 else ''})"
    )
    console.print()

    if not hits:
        console.print("  [dim]No matches found.[/dim]")
        console.print()
        return

    # Check which positions are anchor locations
    anchor_positions = {(a.row, a.col): a.id for a in region_map.anchors}

    for r, c, context in hits:
        anchor_note = ""
        if (r, c) in anchor_positions:
            anchor_note = f"  [bold #e6c566]<- {anchor_positions[(r, c)]}[/bold #e6c566]"
        console.print(f"    ({r:3d},{c:3d})  [dim]...{context}...[/dim]{anchor_note}")

    console.print()


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate map anchors against zone data."""
    console = Console()
    region_map = _load_map(Path(args.map_file))

    errors: list[str] = []
    warnings: list[str] = []

    # Try to load zone data for cross-reference checks
    zones: dict[str, object] = {}
    try:
        from heresiarch.engine.data_loader import load_all

        data_dir = Path(args.data_dir) if args.data_dir else Path("data")
        game_data = load_all(data_dir)
        zones = game_data.zones
    except Exception as e:
        warnings.append(f"Could not load game data for cross-reference: {e}")

    console.print(f"\n  [bold]Validating:[/bold] {args.map_file}")
    console.print(f"  Region: {region_map.map_id}  |  Size: {region_map.width}x{region_map.height}  |  Anchors: {len(region_map.anchors)}")
    console.print()

    # Check bounds
    for anchor in region_map.anchors:
        if anchor.row < 0 or anchor.row >= region_map.height:
            errors.append(f"{anchor.id}: row {anchor.row} out of bounds (0-{region_map.height - 1})")
        elif anchor.col < 0 or anchor.col >= len(region_map.art[anchor.row]):
            errors.append(f"{anchor.id}: col {anchor.col} out of bounds for row {anchor.row}")
        else:
            char = region_map.art[anchor.row][anchor.col]
            if char != "o" and char != " ":
                warnings.append(
                    f"{anchor.id}: char at ({anchor.row},{anchor.col}) is '{char}', expected 'o' or space"
                )

    # Check for duplicate positions
    seen_positions: dict[tuple[int, int], str] = {}
    for anchor in region_map.anchors:
        pos = (anchor.row, anchor.col)
        if pos in seen_positions:
            errors.append(
                f"{anchor.id}: overlaps with {seen_positions[pos]} at ({anchor.row},{anchor.col})"
            )
        seen_positions[pos] = anchor.id

    # Check for duplicate zone_ids
    seen_ids: dict[str, int] = {}
    for anchor in region_map.anchors:
        seen_ids[anchor.id] = seen_ids.get(anchor.id, 0) + 1
    for zid, count in seen_ids.items():
        if count > 1:
            errors.append(f"{zid}: appears {count} times in anchors")

    # Cross-reference with zone data
    if zones:
        anchor_ids = {a.id for a in region_map.anchors}
        towns = game_data.towns if hasattr(game_data, "towns") else {}

        # Anchors referencing nonexistent zones or towns
        for aid in anchor_ids:
            if aid not in zones and aid not in towns:
                errors.append(f"{aid}: anchor references unknown zone/town in game data")

        # Zones in this region that lack anchors
        for zid, zone in zones.items():
            if zone.region == region_map.map_id and zid not in anchor_ids:
                warnings.append(f"{zid} ({zone.name}): zone exists in region but has no anchor on map")

    # Flag clearance check (is there room for the |> flag above each anchor?)
    for anchor in region_map.anchors:
        if anchor.row == 0:
            warnings.append(f"{anchor.id}: anchor at row 0, no room for selection flag above")
        elif anchor.col + 1 >= region_map.width:
            warnings.append(f"{anchor.id}: anchor at rightmost col, flag '>' would be clipped")

    # Report
    if errors:
        for e in errors:
            console.print(f"  [bold red]ERROR[/bold red]  {e}")
    if warnings:
        for w in warnings:
            console.print(f"  [bold yellow]WARN [/bold yellow]  {w}")
    if not errors and not warnings:
        console.print("  [bold green]All checks passed.[/bold green]")

    # Summary table of anchors
    console.print()
    console.print("  [bold]Anchor Summary:[/bold]")
    for anchor in region_map.anchors:
        char = "?"
        if 0 <= anchor.row < region_map.height:
            line = region_map.art[anchor.row]
            if 0 <= anchor.col < len(line):
                char = line[anchor.col]
        zone_name = ""
        if zones and anchor.id in zones:
            zone_name = f"  ({zones[anchor.id].name})"
        status = "[green]OK[/green]" if char in ("o", " ") else f"[yellow]'{char}'[/yellow]"
        console.print(f"    {anchor.id:<12} ({anchor.row:3d},{anchor.col:3d})  {status}{zone_name}")

    console.print()

    if errors:
        sys.exit(1)


# ---------------------------------------------------------------------------
# place — interactive anchor placement via Textual
# ---------------------------------------------------------------------------


def cmd_place(args: argparse.Namespace) -> None:
    """Launch interactive cursor for placing zone anchors."""
    region_map = _load_map(Path(args.map_file))
    _run_placer_app(region_map)


def _run_placer_app(region_map: RegionMap) -> None:
    """Run the Textual-based anchor placement app."""
    from textual.app import App, ComposeResult
    from textual.containers import ScrollableContainer
    from textual.reactive import reactive
    from textual.widgets import Footer, Static

    class AnchorPlacerApp(App):
        """Interactive cursor for dropping zone anchors on an ASCII map."""

        TITLE = "Map Anchor Placer"
        CSS = """
        Screen {
            background: #0a0a0a;
            color: #d4d4d4;
        }
        #placer-scroll {
            height: 1fr;
            border: tall #333355;
        }
        #placer-canvas {
            width: auto;
            height: auto;
        }
        #status-bar {
            height: 3;
            padding: 0 2;
            border: tall #333355;
            background: #111111;
        }
        Footer {
            background: #1a1a2e;
            color: #6b6b6b;
        }
        """

        BINDINGS = [
            ("q", "quit_app", "Quit & Print"),
            ("escape", "quit_app", "Quit & Print"),
            ("up", "move(-1, 0)", "Up"),
            ("down", "move(1, 0)", "Down"),
            ("left", "move(0, -1)", "Left"),
            ("right", "move(0, 1)", "Right"),
            ("shift+up", "move(-5, 0)", "Jump Up"),
            ("shift+down", "move(5, 0)", "Jump Down"),
            ("shift+left", "move(0, -10)", "Jump Left"),
            ("shift+right", "move(0, 10)", "Jump Right"),
            ("enter", "drop_anchor", "Drop Anchor"),
            ("backspace", "undo_anchor", "Undo Last"),
        ]

        cursor_row: reactive[int] = reactive(0)
        cursor_col: reactive[int] = reactive(0)

        def __init__(self, rmap: RegionMap) -> None:
            super().__init__()
            self.rmap = rmap
            self.dropped: list[tuple[int, int, str]] = []
            # Pre-populate with existing anchors
            for a in rmap.anchors:
                self.dropped.append((a.row, a.col, a.id))

        def compose(self) -> ComposeResult:
            with ScrollableContainer(id="placer-scroll"):
                yield Static(id="placer-canvas")
            yield Static(id="status-bar")
            yield Footer()

        def on_mount(self) -> None:
            self._refresh()
            canvas = self.query_one("#placer-canvas", Static)
            canvas.focus()

        def watch_cursor_row(self) -> None:
            self._refresh()

        def watch_cursor_col(self) -> None:
            self._refresh()

        def _refresh(self) -> None:
            """Re-render the map with cursor and dropped anchors."""
            width = self.rmap.width
            grid = [list(line.ljust(width)) for line in self.rmap.art]

            # Build position lookup for dropped anchors
            dropped_pos: dict[tuple[int, int], str] = {}
            for r, c, zid in self.dropped:
                dropped_pos[(r, c)] = zid

            text = Text()
            cr, cc = self.cursor_row, self.cursor_col
            for r, row in enumerate(grid):
                for c, char in enumerate(row):
                    if r == cr and c == cc:
                        # Cursor position — show with reverse highlight
                        text.append(char if char.strip() else "+", style=_CURSOR_STYLE)
                    elif (r, c) in dropped_pos:
                        text.append("@", style="bold #44aa44")
                    else:
                        text.append(char, style=_style_for_char(char))
                if r < len(grid) - 1:
                    text.append("\n")

            try:
                self.query_one("#placer-canvas", Static).update(text)
            except Exception:
                pass

            # Update status bar
            char_under = " "
            if 0 <= cr < self.rmap.height:
                line = self.rmap.art[cr]
                if 0 <= cc < len(line):
                    char_under = line[cc]

            n_dropped = len(self.dropped)
            status_lines = [
                f"[bold #e6c566]Cursor:[/bold #e6c566] row={cr}  col={cc}  "
                f"char='{char_under}'  |  "
                f"[bold #44aa44]Anchors dropped: {n_dropped}[/bold #44aa44]",
                "[dim]Arrow keys: move  |  Shift+Arrow: jump  |  "
                "Enter: drop anchor  |  Backspace: undo  |  Q: quit & print[/dim]",
            ]
            try:
                self.query_one("#status-bar", Static).update("\n".join(status_lines))
            except Exception:
                pass

            # Pan to keep cursor visible
            self.call_after_refresh(self._pan_to_cursor)

        def _pan_to_cursor(self) -> None:
            try:
                scroller = self.query_one("#placer-scroll", ScrollableContainer)
                vw = scroller.size.width
                vh = scroller.size.height
                target_x = max(0, self.cursor_col - vw // 2)
                target_y = max(0, self.cursor_row - vh // 2)
                scroller.scroll_to(target_x, target_y, animate=True, duration=0.15)
            except Exception:
                pass

        def action_move(self, dr: int, dc: int) -> None:
            new_r = max(0, min(self.rmap.height - 1, self.cursor_row + dr))
            new_c = max(0, min(self.rmap.width - 1, self.cursor_col + dc))
            self.cursor_row = new_r
            self.cursor_col = new_c

        def action_drop_anchor(self) -> None:
            r, c = self.cursor_row, self.cursor_col
            # Check for existing anchor at this position
            for i, (er, ec, _) in enumerate(self.dropped):
                if er == r and ec == c:
                    self.notify(f"Anchor already exists at ({r},{c})", severity="warning")
                    return

            zone_id = f"zone_{len(self.dropped) + 1:02d}"
            self.dropped.append((r, c, zone_id))
            self.notify(f"Dropped: {zone_id} at ({r},{c})", severity="information")
            self._refresh()

        def action_undo_anchor(self) -> None:
            if self.dropped:
                removed = self.dropped.pop()
                self.notify(f"Removed: {removed[2]} at ({removed[0]},{removed[1]})", severity="information")
                self._refresh()

        def action_quit_app(self) -> None:
            self.exit()

    app = AnchorPlacerApp(region_map)
    app.run()

    # After exit, print the YAML anchor block
    console = Console()
    if app.dropped:
        console.print("\n[bold #c8a2c8]Anchor positions:[/bold #c8a2c8]\n")
        console.print("[dim]anchors:[/dim]")
        for r, c, zid in app.dropped:
            console.print(f"  [dim]- zone_id:[/dim] [bold]{zid}[/bold]")
            console.print(f"    [dim]row:[/dim] {r}")
            console.print(f"    [dim]col:[/dim] {c}")
        console.print()
    else:
        console.print("\n[dim]No anchors placed.[/dim]\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="heresiarch-map",
        description="Map authoring tool — preview, validate, and place anchors on ASCII region maps.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # preview
    p_preview = subparsers.add_parser("preview", help="Render a map with colored zone markers")
    p_preview.add_argument("map_file", help="Path to the map YAML file")
    p_preview.add_argument("--select", help="Zone ID to show as selected")
    p_preview.add_argument("--cleared", nargs="*", default=[], help="Zone IDs to show as cleared")
    p_preview.add_argument("--available", nargs="*", default=[], help="Zone IDs to show as available")
    p_preview.add_argument("--all-available", action="store_true", help="Show all zones as available")
    p_preview.add_argument("--ruler", action="store_true", help="Show row/col coordinate rulers")
    p_preview.set_defaults(func=cmd_preview)

    # inspect
    p_inspect = subparsers.add_parser(
        "inspect",
        help="Crop and display a map region with coordinate rulers",
    )
    p_inspect.add_argument("map_file", help="Path to the map YAML file")
    p_inspect.add_argument("row", type=int, help="Center row")
    p_inspect.add_argument("col", type=int, help="Center col")
    p_inspect.add_argument("--rows", type=int, default=15, help="Height of crop (default: 15)")
    p_inspect.add_argument("--cols", type=int, default=40, help="Width of crop (default: 40)")
    p_inspect.set_defaults(func=cmd_inspect)

    # find
    p_find = subparsers.add_parser("find", help="Find all instances of a character with positions")
    p_find.add_argument("map_file", help="Path to the map YAML file")
    p_find.add_argument("char", help="Single character to search for")
    p_find.set_defaults(func=cmd_find)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate map anchors against zone data")
    p_validate.add_argument("map_file", help="Path to the map YAML file")
    p_validate.add_argument("--data-dir", help="Path to data directory (default: data/)")
    p_validate.set_defaults(func=cmd_validate)

    # place
    p_place = subparsers.add_parser("place", help="Interactive anchor placement with cursor")
    p_place.add_argument("map_file", help="Path to the map YAML file")
    p_place.set_defaults(func=cmd_place)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
