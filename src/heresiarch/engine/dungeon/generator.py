"""Floor generation: rooms + corridors on a cell grid, PMD-style.

Pure and seeded: ``generate_floor(seed, ...)`` always returns the same
floor for the same inputs. The map is divided into a grid of cells;
each cell holds either a room or a 1-tile junction. Cells are joined by
a random spanning tree (guaranteeing connectivity) plus a few extra
edges for loops, carved as Z-shaped corridors.

Layout geometry lives here. Gameplay tunables (packs per floor, sight)
live in ``formulas.py``.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from heresiarch.engine.dungeon.models import (
    TILE_ENTRY,
    TILE_FLOOR,
    TILE_STAIRS,
    TILE_WALL,
    EntityKind,
    FloorState,
    LayoutParams,
    MapEntity,
    Placement,
    Room,
)
from heresiarch.engine.dungeon.rules import reveal_around_player

# Geometry defaults live on LayoutParams (dungeon/models.py); each zone's
# DungeonTheme can override them. Kept as names for older call sites.
_DEFAULT_LAYOUT = LayoutParams()
FLOOR_WIDTH: int = _DEFAULT_LAYOUT.width
FLOOR_HEIGHT: int = _DEFAULT_LAYOUT.height


@dataclass(frozen=True)
class PackSpec:
    """A pack to place: zone encounter index (None = endless) + display ids."""

    encounter_index: int | None
    enemy_template_ids: tuple[str, ...]


@dataclass(frozen=True)
class FloorItemSpec:
    """A pickup to place: an item or loose gold, where, and its guarantee key."""

    item_id: str | None = None
    gold: int = 0
    placement: Placement = "any"
    guarantee_key: str | None = None


@dataclass
class _Cell:
    col: int
    row: int
    room: Room | None
    anchor: tuple[int, int]
    # Inclusive bounds of the cell's carved footprint (room rect or point)
    left: int
    right: int
    top: int
    bottom: int


def _carve(grid: list[list[str]], x: int, y: int) -> None:
    if 0 < x < len(grid[0]) - 1 and 0 < y < len(grid) - 1:
        if grid[y][x] == TILE_WALL:
            grid[y][x] = TILE_FLOOR


def _carve_h(grid: list[list[str]], x0: int, x1: int, y: int, width: int = 1) -> None:
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for k in range(width):
            _carve(grid, x, y + k)


def _carve_v(grid: list[list[str]], y0: int, y1: int, x: int, width: int = 1) -> None:
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for k in range(width):
            _carve(grid, x + k, y)


def _connect(
    rng: random.Random, grid: list[list[str]], a: _Cell, b: _Cell, width: int = 1,
) -> None:
    """Carve a Z-shaped corridor between two grid-adjacent cells."""
    ax, ay = a.anchor
    bx, by = b.anchor
    if a.row == b.row:
        left, right = (a, b) if a.col < b.col else (b, a)
        lo, hi = left.right + 1, right.left - 1
        mid = rng.randint(lo, hi) if lo <= hi else (ax + bx) // 2
        # leave each footprint on its own row, meet at the mid column
        ly = rng.randint(left.top, left.bottom)
        ry = rng.randint(right.top, right.bottom)
        _carve_h(grid, left.right, mid, ly, width)
        _carve_v(grid, ly, ry, mid, width)
        _carve_h(grid, mid, right.left, ry, width)
    else:
        top, bottom = (a, b) if a.row < b.row else (b, a)
        lo, hi = top.bottom + 1, bottom.top - 1
        mid = rng.randint(lo, hi) if lo <= hi else (ay + by) // 2
        tx = rng.randint(top.left, top.right)
        bx2 = rng.randint(bottom.left, bottom.right)
        _carve_v(grid, top.bottom, mid, tx, width)
        _carve_h(grid, tx, bx2, mid, width)
        _carve_v(grid, mid, bottom.top, bx2, width)


def _in_round(room: Room, x: int, y: int) -> bool:
    """Ellipse inscribed in the room rect (round clearings)."""
    rx, ry = room.w / 2, room.h / 2
    cx, cy = room.x + rx - 0.5, room.y + ry - 0.5
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.08


def _build_layout(
    rng: random.Random, layout: LayoutParams,
) -> tuple[list[list[str]], list[Room]]:
    width, height = layout.width, layout.height
    cols, rows = layout.grid_cols, layout.grid_rows
    grid = [[TILE_WALL] * width for _ in range(height)]
    cw = width // cols
    ch = height // rows
    n_cells = cols * rows

    # Decide which cells get rooms (at least min_rooms)
    order = list(range(n_cells))
    rng.shuffle(order)
    room_cells = {i for i in order if rng.random() < layout.room_chance}
    for i in order:
        if len(room_cells) >= layout.min_rooms:
            break
        room_cells.add(i)

    cells: list[_Cell] = []
    rooms: list[Room] = []
    round_rooms: list[bool] = []
    for idx in range(n_cells):
        col, row = idx % cols, idx // cols
        # 1-tile margin inside the cell, plus the outer map wall
        x0, x1 = col * cw + 2, (col + 1) * cw - 2
        y0, y1 = row * ch + 2, (row + 1) * ch - 2
        if idx in room_cells:
            max_w = max(layout.room_min_w, min(layout.room_max_w, x1 - x0 + 1))
            max_h = max(layout.room_min_h, min(layout.room_max_h, y1 - y0 + 1))
            w = rng.randint(min(layout.room_min_w, max_w), max_w)
            h = rng.randint(min(layout.room_min_h, max_h), max_h)
            rx = rng.randint(x0, max(x0, x1 - w + 1))
            ry = rng.randint(y0, max(y0, y1 - h + 1))
            room = Room(x=rx, y=ry, w=w, h=h)
            rooms.append(room)
            is_round = layout.room_shape == "round" or (
                layout.room_shape == "mixed" and rng.random() < 0.5
            )
            round_rooms.append(is_round)
            for yy in range(ry, ry + h):
                for xx in range(rx, rx + w):
                    if not is_round or _in_round(room, xx, yy):
                        _carve(grid, xx, yy)
            if is_round:
                _carve(grid, *room.center)  # tiny ellipses keep their heart
            cells.append(_Cell(
                col, row, room, room.center,
                rx, rx + w - 1, ry, ry + h - 1,
            ))
        else:
            px, py = rng.randint(x0, x1), rng.randint(y0, y1)
            _carve(grid, px, py)
            cells.append(_Cell(col, row, None, (px, py), px, px, py, py))

    # Spanning tree over the 4-neighbour cell grid (randomized DFS)
    def neighbours(i: int) -> list[int]:
        col, row = i % cols, i // cols
        out = []
        if col > 0:
            out.append(i - 1)
        if col < cols - 1:
            out.append(i + 1)
        if row > 0:
            out.append(i - cols)
        if row < rows - 1:
            out.append(i + cols)
        return out

    edges: set[tuple[int, int]] = set()
    start = rng.randrange(n_cells)
    visited = {start}
    stack = [start]
    while stack:
        cur = stack[-1]
        options = [n for n in neighbours(cur) if n not in visited]
        if not options:
            stack.pop()
            continue
        nxt = rng.choice(options)
        visited.add(nxt)
        edges.add((min(cur, nxt), max(cur, nxt)))
        stack.append(nxt)
    # Extra loops
    for i in range(n_cells):
        for n in neighbours(i):
            if n > i and (i, n) not in edges and rng.random() < layout.extra_edge_chance:
                edges.add((i, n))

    for a, b in sorted(edges):
        _connect(rng, grid, cells[a], cells[b], layout.corridor_width)

    # Round rooms' corridor ends may stop at the rect edge outside the
    # ellipse: the Z corridors start ON the footprint, so dig each round
    # room's row/column spans between its centre and any corridor stub.
    for room, is_round in zip(rooms, round_rooms):
        if is_round:
            _reconnect_round(grid, room)

    if layout.edge_jitter > 0:
        _jitter_edges(rng, grid, rooms, layout.edge_jitter)
    if layout.pillar_density > 0:
        _place_pillars(rng, grid, rooms, layout.pillar_density)
    return grid, rooms


def _reconnect_round(grid: list[list[str]], room: Room) -> None:
    """Dig straight from the room centre to any floor on its rect border
    that sits outside the ellipse (a corridor that arrived at the rect)."""
    cx, cy = room.center
    for x in range(room.x, room.x + room.w):
        for y in (room.y, room.y + room.h - 1):
            if grid[y][x] != TILE_WALL and not _in_round(room, x, y):
                _carve_v(grid, y, cy, x)
                _carve_h(grid, x, cx, cy)
    for y in range(room.y, room.y + room.h):
        for x in (room.x, room.x + room.w - 1):
            if grid[y][x] != TILE_WALL and not _in_round(room, x, y):
                _carve_h(grid, x, cx, y)
                _carve_v(grid, y, cy, cx)


def _jitter_edges(
    rng: random.Random, grid: list[list[str]], rooms: list[Room], p: float,
) -> None:
    """Dig random wall tiles hugging rooms: organic edges. Only ever adds
    floor next to existing floor, so connectivity can't break."""
    h, w = len(grid), len(grid[0])
    dig: list[tuple[int, int]] = []
    for room in rooms:
        for y in range(room.y - 1, room.y + room.h + 1):
            for x in range(room.x - 1, room.x + room.w + 1):
                if not (1 < x < w - 2 and 1 < y < h - 2) or grid[y][x] != TILE_WALL:
                    continue
                if any(grid[y + dy][x + dx] != TILE_WALL
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    if rng.random() < p:
                        dig.append((x, y))
    for x, y in dig:
        grid[y][x] = TILE_FLOOR


def _place_pillars(
    rng: random.Random, grid: list[list[str]], rooms: list[Room], p: float,
) -> None:
    """Pillars on an odd lattice strictly inside rooms, each with all 8
    neighbours floor. Lattice spacing keeps pillars apart, so the floor
    around them stays one connected piece."""
    for room in rooms:
        for y in range(room.y + 1, room.y + room.h - 1, 2):
            for x in range(room.x + 1, room.x + room.w - 1, 2):
                if (x, y) == room.center:
                    continue
                if all(
                    grid[y + dy][x + dx] == TILE_FLOOR
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                ) and rng.random() < p:
                    grid[y][x] = TILE_WALL


def bfs_distances(
    tiles: list[list[str]] | list[str], start: tuple[int, int],
) -> dict[tuple[int, int], int]:
    """4-neighbour BFS over walkable tiles (used for placement only)."""
    h = len(tiles)
    w = len(tiles[0])
    dist = {start: 0}
    q: deque[tuple[int, int]] = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in dist:
                if tiles[ny][nx] != TILE_WALL:
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
    return dist


def _room_tiles(room: Room) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y in range(room.y, room.y + room.h)
        for x in range(room.x, room.x + room.w)
    ]


def generate_floor(
    seed: int,
    floor_number: int,
    total_floors: int,
    packs: list[PackSpec],
    boss: PackSpec | None = None,
    items: list[FloorItemSpec] | None = None,
    has_stairs: bool = True,
    layout: LayoutParams | None = None,
    theme: str = "shrine_path",
) -> FloorState:
    """Generate one floor. Deterministic for a given argument set."""
    layout = layout or _DEFAULT_LAYOUT
    width, height = layout.width, layout.height
    rng = random.Random(seed)
    grid, rooms = _build_layout(rng, layout)

    occupied: set[tuple[int, int]] = set()

    def free_tile_in(room: Room, spacing: int = 1) -> tuple[int, int] | None:
        candidates = [
            t for t in _room_tiles(room)
            if grid[t[1]][t[0]] == TILE_FLOOR
            and all(
                max(abs(t[0] - o[0]), abs(t[1] - o[1])) > spacing
                for o in occupied
            )
        ]
        if not candidates:
            candidates = [
                t for t in _room_tiles(room)
                if grid[t[1]][t[0]] == TILE_FLOOR and t not in occupied
            ]
        return rng.choice(candidates) if candidates else None

    # Player spawn — marked as the entry ('<'), the way back out
    spawn_room_idx = rng.randrange(len(rooms))
    spawn = free_tile_in(rooms[spawn_room_idx]) or rooms[spawn_room_idx].center
    occupied.add(spawn)
    grid[spawn[1]][spawn[0]] = TILE_ENTRY

    dist = bfs_distances(grid, spawn)

    def room_distance(i: int) -> int:
        return dist.get(rooms[i].center, 0)

    far_rooms = sorted(
        (i for i in range(len(rooms)) if i != spawn_room_idx),
        key=room_distance,
        reverse=True,
    ) or [spawn_room_idx]

    entities: list[MapEntity] = []
    seq = 0

    def next_id(prefix: str) -> str:
        nonlocal seq
        seq += 1
        return f"{prefix}{seq}"

    # Boss guards the farthest room; stairs go to the farthest otherwise
    if boss is not None:
        bx, by = rooms[far_rooms[0]].center
        if (bx, by) in occupied:
            bx, by = free_tile_in(rooms[far_rooms[0]]) or (bx, by)
        occupied.add((bx, by))
        entities.append(MapEntity(
            id=next_id("boss"), kind=EntityKind.BOSS, x=bx, y=by,
            encounter_index=boss.encounter_index,
            enemy_template_ids=list(boss.enemy_template_ids),
            home_room=far_rooms[0],
        ))
    if has_stairs:
        stairs_room = far_rooms[0] if boss is None else (
            far_rooms[1] if len(far_rooms) > 1 else far_rooms[0]
        )
        st = free_tile_in(rooms[stairs_room], spacing=0)
        if st is not None:
            grid[st[1]][st[0]] = TILE_STAIRS
            occupied.add(st)

    # Packs: avoid the spawn room so the first turn is never an ambush
    pack_rooms = [i for i in range(len(rooms)) if i != spawn_room_idx] or [spawn_room_idx]
    rng.shuffle(pack_rooms)
    for n, spec in enumerate(packs):
        room_idx = pack_rooms[n % len(pack_rooms)]
        pos = free_tile_in(rooms[room_idx])
        if pos is None:
            continue
        occupied.add(pos)
        entities.append(MapEntity(
            id=next_id("pack"), kind=EntityKind.PACK, x=pos[0], y=pos[1],
            encounter_index=spec.encounter_index,
            enemy_template_ids=list(spec.enemy_template_ids),
            home_room=room_idx,
        ))

    # Pickups: "far" = the farthest room from the entry (worth the
    # detour), "near" = the arrival room, "any" = anywhere
    for spec in items or []:
        if spec.placement == "far":
            room_idx = far_rooms[0]
        elif spec.placement == "near":
            room_idx = spawn_room_idx
        else:
            room_idx = rng.randrange(len(rooms))
        pos = free_tile_in(rooms[room_idx], spacing=0)
        if pos is None:
            continue
        occupied.add(pos)
        entities.append(MapEntity(
            id=next_id("item"), kind=EntityKind.ITEM, x=pos[0], y=pos[1],
            item_id=spec.item_id, gold=spec.gold,
            guarantee_key=spec.guarantee_key,
        ))

    floor = FloorState(
        floor_number=floor_number,
        total_floors=total_floors,
        seed=seed,
        width=width,
        height=height,
        tiles=["".join(row) for row in grid],
        rooms=rooms,
        explored=["0" * width for _ in range(height)],
        player_x=spawn[0],
        player_y=spawn[1],
        entities=entities,
        is_boss_floor=boss is not None,
        next_entity_seq=seq,
        theme=theme,
    )
    reveal_around_player(floor)
    return floor
