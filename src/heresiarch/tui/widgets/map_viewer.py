"""Map viewer widget — pannable ASCII map with zone markers and selection."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from heresiarch.engine.models.region_map import RegionMap, ZoneAnchor


class ZoneStatus(Enum):
    """Visual state of a zone marker on the map."""

    LOCKED = "locked"
    AVAILABLE = "available"
    CLEARED = "cleared"


# --- Marker characters and colors ---

_MARKER_CHARS: dict[ZoneStatus, str] = {
    ZoneStatus.LOCKED: "?",
    ZoneStatus.AVAILABLE: "o",
    ZoneStatus.CLEARED: "*",
}

_MARKER_STYLES: dict[ZoneStatus, str] = {
    ZoneStatus.LOCKED: "#555555",
    ZoneStatus.AVAILABLE: "bold #e6c566",
    ZoneStatus.CLEARED: "bold #44aa44",
}

_SELECTED_MARKER = "X"
_SELECTED_STYLE = "bold #e6c566"
_FLAG_STYLE = "bold #e6c566"

# Terrain character -> color for atmospheric coloring
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
    "[": "#555555",
    "]": "#555555",
    "{": "#555555",
    "}": "#555555",
    "#": "#555555",
    "+": "#555555",
}

_LETTER_COLOR = "#666666"
_DEFAULT_COLOR = "#555555"


class MapViewer(Widget):
    """Pannable ASCII map viewer with zone selection.

    Renders a RegionMap with colored zone markers. Handles zone cycling
    via up/down keys and emits messages when a zone is selected.
    """

    DEFAULT_CSS = """
    MapViewer {
        height: 1fr;
        width: 1fr;
    }
    MapViewer > ScrollableContainer {
        height: 1fr;
        width: 1fr;
        overflow-y: scroll;
        overflow-x: scroll;
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 1;
    }
    MapViewer > ScrollableContainer > #map-canvas {
        width: auto;
        height: auto;
    }
    """

    # Reactive: index into navigable_zone_ids
    selected_index: reactive[int] = reactive(0)

    class ZoneHighlighted(Message):
        """Fired when the highlighted zone changes."""

        def __init__(self, zone_id: str) -> None:
            super().__init__()
            self.zone_id = zone_id

    class ZoneSelected(Message):
        """Fired when the user presses Enter on a zone."""

        def __init__(self, zone_id: str) -> None:
            super().__init__()
            self.zone_id = zone_id

    def __init__(
        self,
        region_map: RegionMap,
        zone_statuses: dict[str, ZoneStatus],
        navigable_zone_ids: list[str],
        initial_zone_id: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.region_map = region_map
        self.zone_statuses = zone_statuses
        self.navigable_zone_ids = navigable_zone_ids
        self.can_focus = True

        if initial_zone_id and initial_zone_id in navigable_zone_ids:
            self.selected_index = navigable_zone_ids.index(initial_zone_id)

    @property
    def selected_zone_id(self) -> str | None:
        """Currently selected zone ID, or None if no navigable zones."""
        if not self.navigable_zone_ids:
            return None
        idx = self.selected_index % len(self.navigable_zone_ids)
        return self.navigable_zone_ids[idx]

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="map-scroll"):
            yield Static(id="map-canvas")

    def on_mount(self) -> None:
        self._refresh_map()
        # Initial pan to selected zone
        self.call_after_refresh(self._pan_to_selected)

    def watch_selected_index(self) -> None:
        self._refresh_map()
        self.call_after_refresh(self._pan_to_selected)
        zone_id = self.selected_zone_id
        if zone_id:
            self.post_message(self.ZoneHighlighted(zone_id))

    # --- Key bindings ---

    def key_up(self) -> None:
        """Cycle to previous zone."""
        if not self.navigable_zone_ids:
            return
        self.selected_index = (self.selected_index - 1) % len(self.navigable_zone_ids)

    def key_down(self) -> None:
        """Cycle to next zone."""
        if not self.navigable_zone_ids:
            return
        self.selected_index = (self.selected_index + 1) % len(self.navigable_zone_ids)

    def key_enter(self) -> None:
        """Select the currently highlighted zone."""
        zone_id = self.selected_zone_id
        if zone_id:
            self.post_message(self.ZoneSelected(zone_id))

    # --- Rendering ---

    def _refresh_map(self) -> None:
        """Re-render the map canvas with current state."""
        try:
            canvas = self.query_one("#map-canvas", Static)
        except Exception:
            return
        canvas.update(self._render_map())

    def _render_map(self) -> Text:
        """Build the full map as a Rich Text object with styling."""
        art = self.region_map.art
        width = self.region_map.width
        selected_id = self.selected_zone_id

        # Build a mutable grid from the art
        grid: list[list[str]] = []
        for line in art:
            # Pad to full width so all rows are the same length
            padded = line.ljust(width)
            grid.append(list(padded))

        # Build a parallel style grid (None = use character-based default)
        style_grid: list[list[str | None]] = [
            [None] * width for _ in range(len(grid))
        ]

        # Composite zone markers
        for anchor in self.region_map.anchors:
            status = self.zone_statuses.get(anchor.zone_id, ZoneStatus.LOCKED)
            is_selected = anchor.zone_id == selected_id

            r, c = anchor.row, anchor.col
            if r < 0 or r >= len(grid) or c < 0 or c >= width:
                continue

            if is_selected:
                grid[r][c] = _SELECTED_MARKER
                style_grid[r][c] = _SELECTED_STYLE
                # Draw flag above: |> on the row above the marker
                if r >= 1 and c + 1 < width:
                    grid[r - 1][c] = "|"
                    grid[r - 1][c + 1] = ">"
                    style_grid[r - 1][c] = _FLAG_STYLE
                    style_grid[r - 1][c + 1] = _FLAG_STYLE
            else:
                grid[r][c] = _MARKER_CHARS.get(status, "?")
                style_grid[r][c] = _MARKER_STYLES.get(status, _DEFAULT_COLOR)

        # Build Rich Text line by line
        text = Text()
        for r, row in enumerate(grid):
            for c, char in enumerate(row):
                override = style_grid[r][c]
                if override:
                    text.append(char, style=override)
                else:
                    text.append(char, style=_style_for_char(char))
            if r < len(grid) - 1:
                text.append("\n")

        return text

    def _pan_to_selected(self) -> None:
        """Scroll the map to center on the selected zone."""
        anchor = self._selected_anchor()
        if anchor is None:
            return

        try:
            scroller = self.query_one("#map-scroll", ScrollableContainer)
        except Exception:
            return

        # Calculate target scroll position to center the anchor in the viewport.
        # Each character ≈ 1 cell wide, each line ≈ 1 cell tall.
        vw = scroller.size.width
        vh = scroller.size.height

        target_x = max(0, anchor.col - vw // 2)
        target_y = max(0, anchor.row - vh // 2)

        scroller.scroll_to(target_x, target_y, animate=True, duration=0.35)

    def _selected_anchor(self) -> ZoneAnchor | None:
        """Get the anchor for the currently selected zone."""
        zone_id = self.selected_zone_id
        if zone_id is None:
            return None
        return self.region_map.anchor_for_zone(zone_id)


def _style_for_char(char: str) -> str:
    """Map a terrain character to its display color."""
    if char in _TERRAIN_COLORS:
        return _TERRAIN_COLORS[char]
    if char.isalpha():
        return _LETTER_COLOR
    if char == " ":
        return ""
    return _DEFAULT_COLOR
