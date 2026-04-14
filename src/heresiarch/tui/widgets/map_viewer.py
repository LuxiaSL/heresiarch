"""Map viewer widget — pannable ASCII map with anchor markers and selection."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from heresiarch.engine.models.region_map import AsciiMap, MapAnchor


class AnchorStatus(Enum):
    """Visual state of an anchor marker on the map."""

    LOCKED = "locked"
    AVAILABLE = "available"
    CLEARED = "cleared"


# Backward-compat alias
ZoneStatus = AnchorStatus


# --- Marker characters and colors per anchor type ---

_ZONE_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "?",
    AnchorStatus.AVAILABLE: "o",
    AnchorStatus.CLEARED: "*",
}

_ZONE_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#555555",
    AnchorStatus.AVAILABLE: "bold #e6c566",
    AnchorStatus.CLEARED: "bold #44aa44",
}

# Town anchors use a distinct lavender color to stand out from zones
_TOWN_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "?",
    AnchorStatus.AVAILABLE: "T",
    AnchorStatus.CLEARED: "T",
}

_TOWN_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#555555",
    AnchorStatus.AVAILABLE: "bold #c8a2c8",
    AnchorStatus.CLEARED: "bold #c8a2c8",
}

# Building anchors (inside towns) use warm amber
_BUILDING_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "?",
    AnchorStatus.AVAILABLE: "o",
    AnchorStatus.CLEARED: "o",
}

_BUILDING_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#555555",
    AnchorStatus.AVAILABLE: "bold #e6c566",
    AnchorStatus.CLEARED: "bold #e6c566",
}

# Exit anchors (town gates / leave points) — warm rust, distinct from amber
_EXIT_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "?",
    AnchorStatus.AVAILABLE: "V",
    AnchorStatus.CLEARED: "V",
}

_EXIT_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#555555",
    AnchorStatus.AVAILABLE: "bold #cc8866",
    AnchorStatus.CLEARED: "bold #cc8866",
}

# Encounter anchors — zone path nodes
_ENCOUNTER_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: ".",
    AnchorStatus.AVAILABLE: "o",
    AnchorStatus.CLEARED: "*",
}

_ENCOUNTER_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#333333",
    AnchorStatus.AVAILABLE: "bold #e6c566",
    AnchorStatus.CLEARED: "bold #44aa44",
}

# Boss encounter anchors — red when upcoming
_BOSS_MARKER_CHARS: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: ".",
    AnchorStatus.AVAILABLE: "#",
    AnchorStatus.CLEARED: "*",
}

_BOSS_MARKER_STYLES: dict[AnchorStatus, str] = {
    AnchorStatus.LOCKED: "#333333",
    AnchorStatus.AVAILABLE: "bold #cc4444",
    AnchorStatus.CLEARED: "bold #44aa44",
}

_MARKER_CHARS_BY_TYPE: dict[str, dict[AnchorStatus, str]] = {
    "zone": _ZONE_MARKER_CHARS,
    "town": _TOWN_MARKER_CHARS,
    "building": _BUILDING_MARKER_CHARS,
    "exit": _EXIT_MARKER_CHARS,
    "encounter": _ENCOUNTER_MARKER_CHARS,
    "boss": _BOSS_MARKER_CHARS,
}

_MARKER_STYLES_BY_TYPE: dict[str, dict[AnchorStatus, str]] = {
    "zone": _ZONE_MARKER_STYLES,
    "town": _TOWN_MARKER_STYLES,
    "building": _BUILDING_MARKER_STYLES,
    "exit": _EXIT_MARKER_STYLES,
    "encounter": _ENCOUNTER_MARKER_STYLES,
    "boss": _BOSS_MARKER_STYLES,
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
    """Pannable ASCII map viewer with anchor selection.

    Renders an AsciiMap with colored markers for zones, towns, and other
    anchor types. Handles cycling via up/down keys and emits messages
    when an anchor is highlighted or selected.
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

    # Reactive: index into navigable_ids
    selected_index: reactive[int] = reactive(0)

    class AnchorHighlighted(Message):
        """Fired when the highlighted anchor changes."""

        def __init__(self, anchor_id: str, anchor_type: str) -> None:
            super().__init__()
            self.anchor_id = anchor_id
            self.anchor_type = anchor_type

    class AnchorSelected(Message):
        """Fired when the user presses Enter on an anchor."""

        def __init__(self, anchor_id: str, anchor_type: str) -> None:
            super().__init__()
            self.anchor_id = anchor_id
            self.anchor_type = anchor_type

    # Backward-compat message aliases
    class ZoneHighlighted(Message):
        """Fired when the highlighted zone changes (compat wrapper)."""

        def __init__(self, zone_id: str) -> None:
            super().__init__()
            self.zone_id = zone_id

    class ZoneSelected(Message):
        """Fired when the user presses Enter on a zone (compat wrapper)."""

        def __init__(self, zone_id: str) -> None:
            super().__init__()
            self.zone_id = zone_id

    def __init__(
        self,
        ascii_map: AsciiMap,
        anchor_statuses: dict[str, AnchorStatus],
        navigable_ids: list[str],
        initial_id: str | None = None,
        style_overrides: dict[tuple[int, int], str] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.ascii_map = ascii_map
        self.anchor_statuses = anchor_statuses
        self.navigable_ids = navigable_ids
        self.style_overrides = style_overrides or {}
        self.can_focus = True

        # Build anchor type lookup
        self._anchor_types: dict[str, str] = {
            a.id: a.anchor_type for a in ascii_map.anchors
        }

        if initial_id and initial_id in navigable_ids:
            self.selected_index = navigable_ids.index(initial_id)

    @property
    def selected_anchor_id(self) -> str | None:
        """Currently selected anchor ID, or None if no navigable anchors."""
        if not self.navigable_ids:
            return None
        idx = self.selected_index % len(self.navigable_ids)
        return self.navigable_ids[idx]

    # Backward-compat property
    @property
    def selected_zone_id(self) -> str | None:
        return self.selected_anchor_id

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="map-scroll"):
            yield Static(id="map-canvas")

    def on_mount(self) -> None:
        self._refresh_map()
        self.call_after_refresh(self._pan_to_selected)

    def watch_selected_index(self) -> None:
        self._refresh_map()
        self.call_after_refresh(self._pan_to_selected)
        anchor_id = self.selected_anchor_id
        if anchor_id:
            atype = self._anchor_types.get(anchor_id, "zone")
            self.post_message(self.AnchorHighlighted(anchor_id, atype))
            # Also fire legacy message for existing handlers
            self.post_message(self.ZoneHighlighted(anchor_id))

    # --- Key bindings ---

    def key_up(self) -> None:
        """Cycle to previous anchor."""
        if not self.navigable_ids:
            return
        self.selected_index = (self.selected_index - 1) % len(self.navigable_ids)

    def key_down(self) -> None:
        """Cycle to next anchor."""
        if not self.navigable_ids:
            return
        self.selected_index = (self.selected_index + 1) % len(self.navigable_ids)

    def key_enter(self) -> None:
        """Select the currently highlighted anchor."""
        anchor_id = self.selected_anchor_id
        if anchor_id:
            atype = self._anchor_types.get(anchor_id, "zone")
            self.post_message(self.AnchorSelected(anchor_id, atype))
            # Also fire legacy message
            self.post_message(self.ZoneSelected(anchor_id))

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
        art = self.ascii_map.art
        width = self.ascii_map.width
        selected_id = self.selected_anchor_id

        # Build a mutable grid from the art
        grid: list[list[str]] = []
        for line in art:
            padded = line.ljust(width)
            grid.append(list(padded))

        # Build a parallel style grid (None = use character-based default)
        style_grid: list[list[str | None]] = [
            [None] * width for _ in range(len(grid))
        ]

        # Apply caller-provided style overrides (e.g. path coloring)
        for (r, c), style in self.style_overrides.items():
            if 0 <= r < len(style_grid) and 0 <= c < len(style_grid[r]):
                style_grid[r][c] = style

        # Composite anchor markers
        for anchor in self.ascii_map.anchors:
            status = self.anchor_statuses.get(anchor.id, AnchorStatus.LOCKED)
            is_selected = anchor.id == selected_id
            atype = anchor.anchor_type

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
                chars = _MARKER_CHARS_BY_TYPE.get(atype, _ZONE_MARKER_CHARS)
                styles = _MARKER_STYLES_BY_TYPE.get(atype, _ZONE_MARKER_STYLES)
                grid[r][c] = chars.get(status, "?")
                style_grid[r][c] = styles.get(status, _DEFAULT_COLOR)

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
        """Scroll the map to center on the selected anchor."""
        anchor = self._selected_anchor()
        if anchor is None:
            return

        try:
            scroller = self.query_one("#map-scroll", ScrollableContainer)
        except Exception:
            return

        vw = scroller.size.width
        vh = scroller.size.height

        target_x = max(0, anchor.col - vw // 2)
        target_y = max(0, anchor.row - vh // 2)

        scroller.scroll_to(target_x, target_y, animate=True, duration=0.35)

    def _selected_anchor(self) -> MapAnchor | None:
        """Get the anchor for the currently selected item."""
        anchor_id = self.selected_anchor_id
        if anchor_id is None:
            return None
        return self.ascii_map.anchor_for_id(anchor_id)


def _style_for_char(char: str) -> str:
    """Map a terrain character to its display color."""
    if char in _TERRAIN_COLORS:
        return _TERRAIN_COLORS[char]
    if char.isalpha():
        return _LETTER_COLOR
    if char == " ":
        return ""
    return _DEFAULT_COLOR
