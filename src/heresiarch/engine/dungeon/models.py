"""Dungeon-layer models: floors, map entities, step results.

Leaf module — imports nothing from the rest of the engine, so
``models/zone.py`` can embed ``FloorState`` without import cycles.

Coordinates: ``x`` is the column, ``y`` the row, (0, 0) top-left.
Tiles are stored as a list of strings (one per row) — compact in saves
and trivially renderable.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Tile glyphs. Kept as single characters so a floor serializes as text.
TILE_WALL = "#"
TILE_FLOOR = "."
TILE_STAIRS = ">"
TILE_EXIT = "X"  # appears where the boss fell; stepping on it leaves the zone
TILE_ENTRY = "<"  # where you arrived on this floor — the way back out

WALKABLE_TILES: frozenset[str] = frozenset({TILE_FLOOR, TILE_STAIRS, TILE_EXIT, TILE_ENTRY})
# Tiles you may walk out of the zone from (retreat rule). Anywhere else
# needs an escape item.
RETREAT_TILES: frozenset[str] = frozenset({TILE_STAIRS, TILE_EXIT, TILE_ENTRY})


class Direction(str, Enum):
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"

    @property
    def delta(self) -> tuple[int, int]:
        return _DELTAS[self]

    @property
    def is_diagonal(self) -> bool:
        dx, dy = _DELTAS[self]
        return dx != 0 and dy != 0

    @classmethod
    def from_delta(cls, dx: int, dy: int) -> Direction:
        for d, delta in _DELTAS.items():
            if delta == (dx, dy):
                return d
        raise ValueError(f"No direction for delta ({dx}, {dy})")


_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.N: (0, -1),
    Direction.NE: (1, -1),
    Direction.E: (1, 0),
    Direction.SE: (1, 1),
    Direction.S: (0, 1),
    Direction.SW: (-1, 1),
    Direction.W: (-1, 0),
    Direction.NW: (-1, -1),
}


class LayoutParams(BaseModel):
    """Floor-generator knobs for one dungeon theme. Defaults = zone 1's
    shrine path (rectangular rooms on a 3×3 cell grid)."""

    width: int = Field(default=40, ge=16, le=80)
    height: int = Field(default=28, ge=12, le=60)
    grid_cols: int = Field(default=3, ge=2, le=6)
    grid_rows: int = Field(default=3, ge=2, le=6)
    room_min_w: int = Field(default=4, ge=3)
    room_min_h: int = Field(default=3, ge=3)
    room_max_w: int = Field(default=10, ge=3)
    room_max_h: int = Field(default=7, ge=3)
    room_chance: float = Field(default=0.7, ge=0.0, le=1.0)
    min_rooms: int = Field(default=4, ge=2)
    extra_edge_chance: float = Field(default=0.2, ge=0.0, le=1.0)
    # Shape: rect rooms, round clearings, or a per-room mix
    room_shape: Literal["rect", "round", "mixed"] = "rect"
    corridor_width: int = Field(default=1, ge=1, le=2)
    # Organic edges: chance each wall tile touching a room is dug out
    edge_jitter: float = Field(default=0.0, ge=0.0, le=0.6)
    # Interior pillars on an odd lattice (never disconnects a room)
    pillar_density: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _ranges(self) -> LayoutParams:
        if self.room_max_w < self.room_min_w or self.room_max_h < self.room_min_h:
            raise ValueError("room max size must be >= min size")
        if self.min_rooms > self.grid_cols * self.grid_rows:
            raise ValueError("min_rooms exceeds the number of grid cells")
        return self


class DungeonTheme(BaseModel):
    """How a zone's floors look and are shaped (data/region_*/dungeon_themes).

    ``id`` doubles as the art prefix: the client draws ``<id>.<frame>``
    (e.g. ``mossy_path.wall_5``) and falls back to the base frame, so a
    theme can override as much or as little art as it likes.
    """

    id: str
    name: str = ""
    notes: str = ""
    layout: LayoutParams = Field(default_factory=LayoutParams)
    backdrop: str = "shrine_path"     # battle backdrop frame: bg_<backdrop>
    decor: list[str] = Field(default_factory=list)  # frame names scattered on floors
    decor_density: float = Field(default=0.0, ge=0.0, le=0.3)


class Room(BaseModel):
    """Axis-aligned rectangle of floor. Inclusive of x..x+w-1, y..y+h-1."""

    x: int
    y: int
    w: int
    h: int

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)


class EntityKind(str, Enum):
    PACK = "PACK"    # a wandering enemy group (symbol encounter)
    BOSS = "BOSS"    # stationary boss guarding the final floor
    ITEM = "ITEM"    # a pickup lying on the floor


class MapEntity(BaseModel):
    """Something standing on the floor."""

    id: str
    kind: EntityKind
    x: int
    y: int
    # PACK/BOSS: which zone encounter template this pack is (None = endless).
    encounter_index: int | None = None
    # PACK/BOSS: template ids for display/sprites (lead first). For endless
    # packs this IS the composition; for zone packs it mirrors the template.
    enemy_template_ids: list[str] = Field(default_factory=list)
    home_room: int | None = None  # wander tether (the room it currently haunts)
    alerted: bool = False         # has spotted the player and is chasing
    # Roaming: an idle pack occasionally sets off for another room
    roam_x: int | None = None
    roam_y: int | None = None
    # ITEM (an item, or loose gold when gold > 0)
    item_id: str | None = None
    gold: int = 0
    # Set when this pickup fulfils a zone's floor guarantee — claimed on
    # pickup so a guaranteed find appears once per run, not per visit.
    guarantee_key: str | None = None


class FloorState(BaseModel):
    """One generated floor and everything on it."""

    floor_number: int            # 1-based
    total_floors: int = 0        # 0 = unbounded (overstay / endless)
    seed: int
    width: int
    height: int
    tiles: list[str]
    rooms: list[Room] = Field(default_factory=list)
    explored: list[str] = Field(default_factory=list)  # '1' = seen, same shape as tiles
    player_x: int
    player_y: int
    facing: Direction = Direction.S
    entities: list[MapEntity] = Field(default_factory=list)
    turn: int = 0
    is_boss_floor: bool = False
    next_entity_seq: int = 0     # monotonically increasing entity id source
    theme: str = "shrine_path"   # DungeonTheme id the floor was built with

    # --- Tile queries -------------------------------------------------

    def tile(self, x: int, y: int) -> str:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.tiles[y][x]
        return TILE_WALL

    def is_walkable(self, x: int, y: int) -> bool:
        return self.tile(x, y) in WALKABLE_TILES

    def room_index_at(self, x: int, y: int) -> int | None:
        for i, room in enumerate(self.rooms):
            if room.contains(x, y):
                return i
        return None

    def entity_at(self, x: int, y: int) -> MapEntity | None:
        for e in self.entities:
            if e.x == x and e.y == y:
                return e
        return None

    def get_entity(self, entity_id: str) -> MapEntity | None:
        for e in self.entities:
            if e.id == entity_id:
                return e
        return None

    def is_explored(self, x: int, y: int) -> bool:
        if 0 <= y < len(self.explored) and 0 <= x < len(self.explored[y]):
            return self.explored[y][x] == "1"
        return False


# ----------------------------------------------------------------------
# Floor loot (zone YAML): random tables + guaranteed placements
# ----------------------------------------------------------------------

Placement = Literal["far", "near", "any"]


class FloorLootEntry(BaseModel):
    """One weighted row: an item, or loose gold in a [min, max] range."""

    item_id: str | None = None
    gold: tuple[int, int] | None = None
    weight: float = 1.0

    @model_validator(mode="after")
    def _one_payload(self) -> FloorLootEntry:
        if (self.item_id is None) == (self.gold is None):
            raise ValueError("floor loot entry needs exactly one of item_id / gold")
        return self


class FloorLootTable(BaseModel):
    """Random finds per floor: roll ``picks`` (min, max) times; each pick
    actually lands with probability ``chance`` (rarity lever)."""

    picks: tuple[int, int] = (0, 0)
    chance: float = Field(default=1.0, ge=0.0, le=1.0)
    entries: list[FloorLootEntry] = Field(default_factory=list)


class FloorGuarantee(FloorLootEntry):
    """A find that is always there: on floor ``floor`` (and every ``every``
    floors after it, for endless milestones). ``placement`` far = the
    room farthest from where you arrive (worth the detour), near = your
    arrival room, any = anywhere. Claimed once per run on pickup."""

    floor: int
    every: int = 0
    placement: Placement = "far"

    def applies_to(self, floor_number: int) -> bool:
        if floor_number == self.floor:
            return True
        return (
            self.every > 0
            and floor_number > self.floor
            and (floor_number - self.floor) % self.every == 0
        )


class StepOutcome(str, Enum):
    MOVED = "MOVED"
    BLOCKED = "BLOCKED"      # wall / diagonal corner — no turn spent
    WAITED = "WAITED"
    CONTACT = "CONTACT"      # a fight starts (see initiative)
    PICKUP = "PICKUP"        # moved onto an item and picked it up
    STASH_FULL = "STASH_FULL"  # moved onto an item, no room to take it
    ON_STAIRS = "ON_STAIRS"
    ON_EXIT = "ON_EXIT"


class Initiative(str, Enum):
    PLAYER = "PLAYER"   # player walked into the pack: first strike
    ENEMY = "ENEMY"     # the pack walked into the player: ambush


class StepResult(BaseModel):
    """What happened on one map turn — for UI messages and the session."""

    outcome: StepOutcome
    # CONTACT: every pack in the fight (engaged first, then merged joiners)
    engaged_entity_ids: list[str] = Field(default_factory=list)
    initiative: Initiative | None = None
    picked_item_id: str | None = None
    picked_gold: int = 0
    picked_guarantee_key: str | None = None
    messages: list[str] = Field(default_factory=list)
    turn_spent: bool = True
