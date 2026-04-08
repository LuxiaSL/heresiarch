"""Region map models: ASCII art maps with zone anchor positions."""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field


class ZoneAnchor(BaseModel):
    """Position of a zone marker on the region map."""

    zone_id: str
    row: int
    col: int


class RegionMap(BaseModel):
    """ASCII art map of a region with zone positions for the map viewer."""

    region_id: str
    name: str
    art: list[str] = Field(default_factory=list)
    anchors: list[ZoneAnchor] = Field(default_factory=list)

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

    def anchor_for_zone(self, zone_id: str) -> ZoneAnchor | None:
        """Look up the anchor for a zone by ID."""
        for anchor in self.anchors:
            if anchor.zone_id == zone_id:
                return anchor
        return None
