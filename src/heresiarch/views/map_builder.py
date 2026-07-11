"""Map view builders: anchor statuses, path frontier, initial selection.

Extracted from the TUI screens (zone_select / zone / town) so the TUI
map viewer and the mobile map renderer agree on which anchors are
locked/available/cleared, where the path frontier sits, and where the
cursor should land. Frontends only translate these view models into
pixels (Rich styles or HTML spans) — no game logic on their side.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.game_loop import GameLoop
    from heresiarch.engine.models.region_map import AsciiMap
    from heresiarch.engine.models.run_state import RunState
    from heresiarch.engine.models.zone import ZoneState, ZoneTemplate


class AnchorState(str, Enum):
    """Semantic state of a map anchor. Frontends map these to colors."""

    LOCKED = "locked"
    AVAILABLE = "available"
    CLEARED = "cleared"


class MapAnchorVM(BaseModel):
    """One interactive position on a map, with resolved display state."""

    id: str
    row: int
    col: int
    anchor_type: str  # zone / town / building / exit / encounter / boss
    status: AnchorState = AnchorState.LOCKED
    label: str = ""
    detail: str = ""
    # Zone maps: boss node that acts as a travel tile to the next zone
    travel_to: str | None = None


class PathCellVM(BaseModel):
    """A colorable cell on a zone map's path row."""

    row: int
    col: int
    traversed: bool


class MapVM(BaseModel):
    """Display-ready map: art + resolved anchors + navigation hints."""

    map_key: str  # key into game_data.maps
    name: str
    kind: str  # region / zone / town
    art: list[str] = Field(default_factory=list)
    width: int = 0
    height: int = 0
    anchors: list[MapAnchorVM] = Field(default_factory=list)
    navigable_ids: list[str] = Field(default_factory=list)
    initial_id: str | None = None
    path_cells: list[PathCellVM] = Field(default_factory=list)

    def anchor_for_id(self, anchor_id: str) -> MapAnchorVM | None:
        for anchor in self.anchors:
            if anchor.id == anchor_id:
                return anchor
        return None


# ---------------------------------------------------------------------------
# Region map (zone select)
# ---------------------------------------------------------------------------


def pick_region_map_key(
    run: RunState, game_data: GameData, game_loop: GameLoop,
) -> str | None:
    """Pick the region map for the player's current frontier.

    Prefers the region with available-but-uncleared zones; falls back to
    the most recently completed zone's region, then any mapped region.
    """
    region_maps = game_data.maps
    available = game_loop.get_available_zones(run)
    completed = set(run.zones_completed)

    for zone in available:
        if zone.id not in completed and zone.region in region_maps:
            return zone.region

    for zone_id in reversed(run.zones_completed):
        zone = game_data.zones.get(zone_id)
        if zone and zone.region in region_maps:
            return zone.region

    for zone in game_data.zones.values():
        if zone.region in region_maps:
            return zone.region
    return None


def build_region_map_vm(
    run: RunState,
    game_data: GameData,
    game_loop: GameLoop,
    requested_anchor_id: str | None = None,
) -> MapVM | None:
    """Region overview: zones + town, statuses from run progress."""
    map_key = pick_region_map_key(run, game_data, game_loop)
    if map_key is None:
        return None
    ascii_map = game_data.maps.get(map_key)
    if ascii_map is None:
        return None

    available_ids = {z.id for z in game_loop.get_available_zones(run)}
    completed = set(run.zones_completed)

    anchors: list[MapAnchorVM] = []
    navigable: list[str] = []

    for anchor in ascii_map.anchors:
        aid = anchor.id
        label = aid
        detail = ""

        if anchor.anchor_type == "town":
            town = game_data.towns.get(aid)
            if town is not None:
                label = town.name
            if game_loop.is_town_unlocked(run, aid):
                status = AnchorState.AVAILABLE
                navigable.append(aid)
                lodge_cost = game_loop.get_lodge_cost(run)
                shop_count = len(game_loop.resolve_town_shop(run))
                detail = f"Lodge rest {lodge_cost}g · shop {shop_count} items"
            else:
                status = AnchorState.LOCKED
        else:
            zone = game_data.zones.get(aid)
            if zone is not None:
                label = zone.name
                boss_count = sum(1 for e in zone.encounters if e.is_boss)
                recruit = (
                    f" · recruit {zone.recruitment_chance:.0%}"
                    if zone.recruitment_chance > 0
                    else ""
                )
                detail = (
                    f"Lv.{zone.zone_level} · {len(zone.encounters)} fights"
                    f" ({boss_count} boss){recruit}"
                )
            if aid in completed:
                status = AnchorState.CLEARED
                navigable.append(aid)
                detail += " · overstay loot penalty"
            elif aid in available_ids:
                status = AnchorState.AVAILABLE
                navigable.append(aid)
            else:
                status = AnchorState.LOCKED

        anchors.append(MapAnchorVM(
            id=aid, row=anchor.row, col=anchor.col,
            anchor_type=anchor.anchor_type, status=status,
            label=label, detail=detail,
        ))

    status_by_id = {a.id: a.status for a in anchors}
    initial: str | None = None
    if requested_anchor_id and requested_anchor_id in navigable:
        initial = requested_anchor_id
    else:
        for aid in navigable:
            if status_by_id.get(aid) == AnchorState.AVAILABLE:
                initial = aid
                break
    if initial is None and navigable:
        initial = navigable[0]

    return MapVM(
        map_key=map_key,
        name=ascii_map.name,
        kind="region",
        art=list(ascii_map.art),
        width=ascii_map.width,
        height=ascii_map.height,
        anchors=anchors,
        navigable_ids=navigable,
        initial_id=initial,
    )


# ---------------------------------------------------------------------------
# Zone path map
# ---------------------------------------------------------------------------


def build_zone_map_vm(run: RunState, game_data: GameData) -> MapVM | None:
    """Zone path: encounter nodes with frontier progression and exit."""
    if run.current_zone_id is None or run.zone_state is None:
        return None
    zone = game_data.zones.get(run.current_zone_id)
    ascii_map = game_data.maps.get(run.current_zone_id)
    if zone is None or ascii_map is None:
        return None

    zs = run.zone_state
    total = len(zone.encounters)
    is_overstay = zs.is_cleared or zone.is_endless

    statuses: dict[str, AnchorState] = {}
    navigable: list[str] = ["exit"]
    statuses["exit"] = AnchorState.AVAILABLE

    if zone.is_endless:
        # Endless zones: all encounter anchors on the map are always
        # available — there are no fixed encounters to track.
        for anchor in ascii_map.anchors:
            if anchor.anchor_type in ("encounter", "boss"):
                statuses[anchor.id] = AnchorState.AVAILABLE
                navigable.append(anchor.id)
    elif is_overstay:
        # Cleared zone re-entered: all encounters reachable
        for i in range(total):
            anchor_id = f"enc_{i}"
            statuses[anchor_id] = AnchorState.CLEARED
            navigable.append(anchor_id)
    else:
        for i in range(total):
            anchor_id = f"enc_{i}"
            if i in zs.encounters_completed:
                statuses[anchor_id] = AnchorState.CLEARED
                navigable.append(anchor_id)
            elif i == zs.current_encounter_index:
                statuses[anchor_id] = AnchorState.AVAILABLE
                navigable.append(anchor_id)
                break  # can't navigate past the frontier
            else:
                statuses[anchor_id] = AnchorState.LOCKED
        for i in range(total):
            anchor_id = f"enc_{i}"
            statuses.setdefault(anchor_id, AnchorState.LOCKED)

    # Travel tile: once the zone is cleared, its boss node routes onward
    travel_targets: dict[str, str] = {}
    if zone.next_zone and zs.is_cleared:
        for i, enc in enumerate(zone.encounters):
            if enc.is_boss:
                travel_targets[f"enc_{i}"] = zone.next_zone

    anchors: list[MapAnchorVM] = []
    for anchor in ascii_map.anchors:
        aid = anchor.id
        status = statuses.get(aid, AnchorState.LOCKED)
        label, detail = _zone_anchor_text(
            aid, anchor.anchor_type, zone, zs, total, game_data,
            is_travel=aid in travel_targets,
        )
        anchors.append(MapAnchorVM(
            id=aid, row=anchor.row, col=anchor.col,
            anchor_type=anchor.anchor_type, status=status,
            label=label, detail=detail,
            travel_to=travel_targets.get(aid),
        ))

    initial = _zone_initial_anchor(
        zone, zs, ascii_map, statuses, navigable, is_overstay,
    )

    return MapVM(
        map_key=run.current_zone_id,
        name=ascii_map.name,
        kind="zone",
        art=list(ascii_map.art),
        width=ascii_map.width,
        height=ascii_map.height,
        anchors=anchors,
        navigable_ids=navigable,
        initial_id=initial,
        path_cells=compute_path_cells(ascii_map, statuses),
    )


def _zone_anchor_text(
    anchor_id: str,
    anchor_type: str,
    zone: ZoneTemplate,
    zs: ZoneState,
    total: int,
    game_data: GameData,
    *,
    is_travel: bool,
) -> tuple[str, str]:
    """Label + one-line detail for a zone map anchor."""
    if anchor_type == "exit":
        return "Exit", "Return to zone select"
    if anchor_type not in ("encounter", "boss"):
        return anchor_id, ""

    if zone.is_endless:
        return "Endless battle", f"Battles fought: {zs.overstay_battles}"

    enc_idx = _anchor_to_index(anchor_id)
    if enc_idx is None or not (0 <= enc_idx < total):
        return anchor_id, ""

    enc = zone.encounters[enc_idx]
    label = "Boss" if enc.is_boss else f"Encounter {enc_idx + 1}/{total}"

    if is_travel:
        next_z = game_data.zones.get(zone.next_zone or "")
        next_name = next_z.name if next_z else (zone.next_zone or "?")
        return label, f"Travel to {next_name}"
    if zs.is_cleared:
        penalty = min(zs.overstay_battles * 5, 100)
        detail = "Zone cleared — overstay fight"
        if zs.overstay_battles > 0:
            detail += f" (-{penalty}% loot)"
        return label, detail
    if enc_idx in zs.encounters_completed:
        return label, "Cleared"
    return label, ""


def _zone_initial_anchor(
    zone: ZoneTemplate,
    zs: ZoneState,
    ascii_map: AsciiMap,
    statuses: dict[str, AnchorState],
    navigable: list[str],
    is_overstay: bool,
) -> str | None:
    """Where the cursor lands when the zone map opens."""
    if zone.is_endless:
        enc_anchors = [
            a.id for a in ascii_map.anchors
            if a.anchor_type in ("encounter", "boss")
        ]
        return enc_anchors[0] if enc_anchors else "exit"

    if is_overstay:
        # Random position among encounter nodes for scouring flavor.
        # Exclude boss nodes that act as travel tiles and the exit.
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
            return rng.choice(enc_ids)
    else:
        for i in range(len(zone.encounters)):
            anchor_id = f"enc_{i}"
            if statuses.get(anchor_id) == AnchorState.AVAILABLE:
                return anchor_id

    return navigable[-1] if navigable else None


def compute_path_cells(
    ascii_map: AsciiMap, statuses: dict[str, AnchorState],
) -> list[PathCellVM]:
    """Mark path-row cells as traversed (up to the frontier) or not.

    The frontier column is the current/available encounter's column;
    everything at or before it counts as traversed. Anchor cells are
    skipped — markers render over them.
    """
    enc_anchors = [
        a for a in ascii_map.anchors
        if a.anchor_type in ("encounter", "boss")
    ]
    if not enc_anchors:
        return []

    # All encounter anchors share the path row (linear path)
    path_row = enc_anchors[0].row

    frontier_col = 0
    exit_anchor = ascii_map.anchor_for_id("exit")
    if exit_anchor:
        frontier_col = exit_anchor.col

    for anchor in sorted(enc_anchors, key=lambda a: a.col):
        status = statuses.get(anchor.id, AnchorState.LOCKED)
        if status == AnchorState.CLEARED:
            frontier_col = anchor.col
        elif status == AnchorState.AVAILABLE:
            frontier_col = anchor.col
            break
        else:
            break

    art = ascii_map.art
    if path_row < 0 or path_row >= len(art):
        return []

    anchor_cells = {(a.row, a.col) for a in ascii_map.anchors}
    cells: list[PathCellVM] = []
    for c, char in enumerate(art[path_row]):
        if char == " ":
            continue
        if (path_row, c) in anchor_cells:
            continue  # markers handle anchor positions
        cells.append(PathCellVM(row=path_row, col=c, traversed=c <= frontier_col))
    return cells


def _anchor_to_index(anchor_id: str) -> int | None:
    """Parse encounter anchor ID to encounter index. 'enc_3' -> 3."""
    if anchor_id.startswith("enc_"):
        try:
            return int(anchor_id[4:])
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Town interior map
# ---------------------------------------------------------------------------

_BUILDING_TEXT: dict[str, tuple[str, str]] = {
    "shop": ("Shop", "Browse wares"),
    "lodge": ("Lodge", "Full party heal · resets uncleared zone progress"),
    "tavern": ("Tavern", "The tavern is quiet for now"),
    "exit": ("Exit", "Leave town"),
}


def build_town_map_vm(run: RunState, game_data: GameData) -> MapVM | None:
    """Town interior: all buildings always available."""
    if run.current_town_id is None:
        return None
    ascii_map = game_data.maps.get(run.current_town_id)
    if ascii_map is None:
        return None

    anchors: list[MapAnchorVM] = []
    navigable: list[str] = []
    for anchor in ascii_map.anchors:
        label, detail = _BUILDING_TEXT.get(anchor.id, (anchor.id, ""))
        anchors.append(MapAnchorVM(
            id=anchor.id, row=anchor.row, col=anchor.col,
            anchor_type=anchor.anchor_type, status=AnchorState.AVAILABLE,
            label=label, detail=detail,
        ))
        navigable.append(anchor.id)

    return MapVM(
        map_key=run.current_town_id,
        name=ascii_map.name,
        kind="town",
        art=list(ascii_map.art),
        width=ascii_map.width,
        height=ascii_map.height,
        anchors=anchors,
        navigable_ids=navigable,
        initial_id=navigable[0] if navigable else None,
    )
