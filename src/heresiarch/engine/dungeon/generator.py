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
    TILE_FLOOR,
    TILE_STAIRS,
    TILE_WALL,
    EntityKind,
    FloorState,
    MapEntity,
    Room,
)
from heresiarch.engine.dungeon.rules import reveal_around_player

FLOOR_WIDTH: int = 40
FLOOR_HEIGHT: int = 28
GRID_COLS: int = 3
GRID_ROWS: int = 3
ROOM_MIN_W: int = 4
ROOM_MIN_H: int = 3
ROOM_MAX_W: int = 10
ROOM_MAX_H: int = 7
ROOM_CHANCE: float = 0.7
MIN_ROOMS: int = 4
EXTRA_EDGE_CHANCE: float = 0.2


@dataclass(frozen=True)
class PackSpec:
    """A pack to place: zone encounter index (None = endless) + display ids."""

    encounter_index: int | None
    enemy_template_ids: tuple[str, ...]


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


def _carve_h(grid: list[list[str]], x0: int, x1: int, y: int) -> None:
    for x in range(min(x0, x1), max(x0, x1) + 1):
        _carve(grid, x, y)


def _carve_v(grid: list[list[str]], y0: int, y1: int, x: int) -> None:
    for y in range(min(y0, y1), max(y0, y1) + 1):
        _carve(grid, x, y)


def _connect(rng: random.Random, grid: list[list[str]], a: _Cell, b: _Cell) -> None:
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
        _carve_h(grid, left.right, mid, ly)
        _carve_v(grid, ly, ry, mid)
        _carve_h(grid, mid, right.left, ry)
    else:
        top, bottom = (a, b) if a.row < b.row else (b, a)
        lo, hi = top.bottom + 1, bottom.top - 1
        mid = rng.randint(lo, hi) if lo <= hi else (ay + by) // 2
        tx = rng.randint(top.left, top.right)
        bx2 = rng.randint(bottom.left, bottom.right)
        _carve_v(grid, top.bottom, mid, tx)
        _carve_h(grid, tx, bx2, mid)
        _carve_v(grid, mid, bottom.top, bx2)


def _build_layout(
    rng: random.Random, width: int, height: int,
) -> tuple[list[list[str]], list[Room]]:
    grid = [[TILE_WALL] * width for _ in range(height)]
    cw = width // GRID_COLS
    ch = height // GRID_ROWS
    n_cells = GRID_COLS * GRID_ROWS

    # Decide which cells get rooms (at least MIN_ROOMS)
    order = list(range(n_cells))
    rng.shuffle(order)
    room_cells = {i for i in order if rng.random() < ROOM_CHANCE}
    for i in order:
        if len(room_cells) >= MIN_ROOMS:
            break
        room_cells.add(i)

    cells: list[_Cell] = []
    rooms: list[Room] = []
    for idx in range(n_cells):
        col, row = idx % GRID_COLS, idx // GRID_COLS
        # 1-tile margin inside the cell, plus the outer map wall
        x0, x1 = col * cw + 2, (col + 1) * cw - 2
        y0, y1 = row * ch + 2, (row + 1) * ch - 2
        if idx in room_cells:
            max_w = max(ROOM_MIN_W, min(ROOM_MAX_W, x1 - x0 + 1))
            max_h = max(ROOM_MIN_H, min(ROOM_MAX_H, y1 - y0 + 1))
            w = rng.randint(ROOM_MIN_W, max_w)
            h = rng.randint(ROOM_MIN_H, max_h)
            rx = rng.randint(x0, max(x0, x1 - w + 1))
            ry = rng.randint(y0, max(y0, y1 - h + 1))
            room = Room(x=rx, y=ry, w=w, h=h)
            rooms.append(room)
            for yy in range(ry, ry + h):
                for xx in range(rx, rx + w):
                    _carve(grid, xx, yy)
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
        col, row = i % GRID_COLS, i // GRID_COLS
        out = []
        if col > 0:
            out.append(i - 1)
        if col < GRID_COLS - 1:
            out.append(i + 1)
        if row > 0:
            out.append(i - GRID_COLS)
        if row < GRID_ROWS - 1:
            out.append(i + GRID_COLS)
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
            if n > i and (i, n) not in edges and rng.random() < EXTRA_EDGE_CHANCE:
                edges.add((i, n))

    for a, b in sorted(edges):
        _connect(rng, grid, cells[a], cells[b])

    return grid, rooms


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
    item_ids: list[str] | None = None,
    has_stairs: bool = True,
    width: int = FLOOR_WIDTH,
    height: int = FLOOR_HEIGHT,
) -> FloorState:
    """Generate one floor. Deterministic for a given argument set."""
    rng = random.Random(seed)
    grid, rooms = _build_layout(rng, width, height)

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

    # Player spawn
    spawn_room_idx = rng.randrange(len(rooms))
    spawn = free_tile_in(rooms[spawn_room_idx]) or rooms[spawn_room_idx].center
    occupied.add(spawn)

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

    # Items: anywhere in a room, including the spawn room
    for item_id in item_ids or []:
        room_idx = rng.randrange(len(rooms))
        pos = free_tile_in(rooms[room_idx], spacing=0)
        if pos is None:
            continue
        occupied.add(pos)
        entities.append(MapEntity(
            id=next_id("item"), kind=EntityKind.ITEM, x=pos[0], y=pos[1],
            item_id=item_id,
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
    )
    reveal_around_player(floor)
    return floor
