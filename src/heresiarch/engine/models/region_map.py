"""ASCII map models: generic maps with anchor positions for the map viewer.

Used for region maps, town interiors, and eventually world maps.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field


class MapAnchor(BaseModel):
    """A named position on an ASCII map.

    Anchors mark interactive locations — zones, towns, buildings, etc.
    The ``anchor_type`` field determines how the map viewer renders and
    dispatches selection events for this anchor.
    """

    id: str
    row: int
    col: int
    anchor_type: Literal["zone", "town", "building", "exit"] = "zone"


class AsciiMap(BaseModel):
    """ASCII art map with interactive anchor positions.

    Generic map model reused for region overviews, town interiors,
    and other navigable map contexts.
    """

    map_id: str
    name: str
    art: list[str] = Field(default_factory=list)
    anchors: list[MapAnchor] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def width(self) -> int:
        """Width of the widest line in the art."""
        return max((len(line) for line in self.art), default=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def height(self) -> int:
        """Number of lines in the art."""
        return len(self.art)

    def anchor_for_id(self, anchor_id: str) -> MapAnchor | None:
        """Look up an anchor by its ID."""
        for anchor in self.anchors:
            if anchor.id == anchor_id:
                return anchor
        return None


# Backward-compat aliases for existing imports
ZoneAnchor = MapAnchor
RegionMap = AsciiMap
