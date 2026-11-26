"""Turn rules for the dungeon layer: sight, movement, pack AI.

All functions MUTATE the FloorState they are given — callers pass a
deep copy (the director does). Randomness comes from an injected
``random.Random``; the director seeds it from (floor seed, turn) so map
turns never consume the run's combat RNG and floors replay exactly.
"""

from __future__ import annotations

import random
from collections import deque

from heresiarch.engine.dungeon.models import (
    TILE_ENTRY,
    TILE_EXIT,
    TILE_STAIRS,
    Direction,
    EntityKind,
    FloorState,
    Initiative,
    MapEntity,
    StepOutcome,
    StepResult,
)
from heresiarch.engine.formulas import (
    DUNGEON_LOSE_TRACK_RADIUS,
    DUNGEON_MERGE_RADIUS,
    DUNGEON_ROAM_CHANCE,
    DUNGEON_SIGHT_RADIUS,
    DUNGEON_WANDER_CHANCE,
)

ALL_DIRECTIONS: tuple[Direction, ...] = tuple(Direction)
_ENEMY_KINDS = (EntityKind.PACK, EntityKind.BOSS)


def chebyshev(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))


def can_step(floor: FloorState, x: int, y: int, d: Direction) -> bool:
    """Terrain-only legality: target walkable, no cutting wall corners."""
    dx, dy = d.delta
    nx, ny = x + dx, y + dy
    if not floor.is_walkable(nx, ny):
        return False
    if d.is_diagonal:
        if not floor.is_walkable(x + dx, y) or not floor.is_walkable(x, y + dy):
            return False
    return True


# ----------------------------------------------------------------------
# Sight
# ----------------------------------------------------------------------

def rooms_in_view(floor: FloorState) -> set[int]:
    """Rooms the player is in or standing in the doorway of."""
    px, py = floor.player_x, floor.player_y
    out: set[int] = set()
    for i, r in enumerate(floor.rooms):
        if r.x - 1 <= px <= r.x + r.w and r.y - 1 <= py <= r.y + r.h:
            out.add(i)
    return out


def _line_clear(floor: FloorState, x0: int, y0: int, x1: int, y1: int) -> bool:
    """Bresenham line of sight: every tile strictly between is walkable."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    x, y = x0, y0
    while True:
        if (x, y) == (x1, y1):
            return True
        if (x, y) != (x0, y0) and not floor.is_walkable(x, y):
            return False
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def in_close_sight(floor: FloorState, x: int, y: int) -> bool:
    """Within corridor sight radius AND not behind a wall."""
    px, py = floor.player_x, floor.player_y
    if chebyshev(x, y, px, py) > DUNGEON_SIGHT_RADIUS:
        return False
    return _line_clear(floor, px, py, x, y)


def is_visible(floor: FloorState, x: int, y: int) -> bool:
    """Can the player see this tile right now? (lit room or close by)"""
    if in_close_sight(floor, x, y):
        return True
    for i in rooms_in_view(floor):
        r = floor.rooms[i]
        if r.x - 1 <= x <= r.x + r.w and r.y - 1 <= y <= r.y + r.h:
            return True
    return False


def reveal_around_player(floor: FloorState) -> None:
    """Mark the lit room (with its walls) and the 1-tile ring as explored."""
    rows = [list(r) for r in floor.explored]
    px, py = floor.player_x, floor.player_y

    def mark(x: int, y: int) -> None:
        if 0 <= y < floor.height and 0 <= x < floor.width:
            rows[y][x] = "1"

    r = DUNGEON_SIGHT_RADIUS
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if in_close_sight(floor, px + dx, py + dy):
                mark(px + dx, py + dy)
    for i in rooms_in_view(floor):
        r = floor.rooms[i]
        for y in range(r.y - 1, r.y + r.h + 1):
            for x in range(r.x - 1, r.x + r.w + 1):
                mark(x, y)
    floor.explored = ["".join(r) for r in rows]


def visible_entities(floor: FloorState) -> list[MapEntity]:
    """Entities the player can currently see (items stay once explored)."""
    out = []
    for e in floor.entities:
        if e.kind == EntityKind.ITEM:
            if floor.is_explored(e.x, e.y):
                out.append(e)
        elif is_visible(floor, e.x, e.y):
            out.append(e)
    return out


# ----------------------------------------------------------------------
# Pack AI
# ----------------------------------------------------------------------

def _distance_field(floor: FloorState) -> dict[tuple[int, int], int]:
    """8-neighbour BFS distance from the player, respecting corner rules."""
    start = (floor.player_x, floor.player_y)
    dist = {start: 0}
    q: deque[tuple[int, int]] = deque([start])
    while q:
        x, y = q.popleft()
        if dist[(x, y)] >= DUNGEON_LOSE_TRACK_RADIUS * 2:
            continue
        for d in ALL_DIRECTIONS:
            if not can_step(floor, x, y, d):
                continue
            dx, dy = d.delta
            n = (x + dx, y + dy)
            if n not in dist:
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def _blocked_for_pack(floor: FloorState, x: int, y: int, mover: MapEntity) -> bool:
    if (x, y) == (floor.player_x, floor.player_y):
        return True
    for e in floor.entities:
        if e is not mover and e.x == x and e.y == y:
            return True
    # Packs don't loiter on stairs/exit/entry (keeps the ways out readable)
    return floor.tile(x, y) in (TILE_STAIRS, TILE_EXIT, TILE_ENTRY)


def merge_joiners(floor: FloorState, engaged: MapEntity) -> list[str]:
    """Alerted packs adjacent to the fight pile in. Bosses fight alone."""
    if engaged.kind == EntityKind.BOSS:
        return []
    out = []
    for e in sorted(floor.entities, key=lambda e: e.id):
        if e is engaged or e.kind != EntityKind.PACK or not e.alerted:
            continue
        near_pack = chebyshev(e.x, e.y, engaged.x, engaged.y) <= DUNGEON_MERGE_RADIUS
        near_player = chebyshev(
            e.x, e.y, floor.player_x, floor.player_y,
        ) <= DUNGEON_MERGE_RADIUS
        if near_pack or near_player:
            out.append(e.id)
    return out


def _enemy_phase(floor: FloorState, rng: random.Random) -> StepResult | None:
    """Every pack acts once. Returns a CONTACT result if one ambushes."""
    field: dict[tuple[int, int], int] | None = None
    px, py = floor.player_x, floor.player_y

    for e in sorted(floor.entities, key=lambda e: e.id):
        if e.kind not in _ENEMY_KINDS:
            continue
        sees = is_visible(floor, e.x, e.y)
        dist = chebyshev(e.x, e.y, px, py)
        if sees:
            e.alerted = True
        elif e.alerted and dist > DUNGEON_LOSE_TRACK_RADIUS:
            e.alerted = False

        if e.kind == EntityKind.BOSS:
            continue  # bosses hold their room

        if e.alerted:
            # Adjacent → it walks into you: ambush
            if dist == 1:
                d = Direction.from_delta(px - e.x, py - e.y)
                if can_step(floor, e.x, e.y, d):
                    return StepResult(
                        outcome=StepOutcome.CONTACT,
                        engaged_entity_ids=[e.id, *merge_joiners(floor, e)],
                        initiative=Initiative.ENEMY,
                        messages=[f"{_pack_label(e)} ambushes you!"],
                    )
            if field is None:
                field = _distance_field(floor)
            here = field.get((e.x, e.y), 10**6)
            best: tuple[int, int] | None = None
            best_d = here
            for d in ALL_DIRECTIONS:
                if not can_step(floor, e.x, e.y, d):
                    continue
                nx, ny = e.x + d.delta[0], e.y + d.delta[1]
                if _blocked_for_pack(floor, nx, ny, e):
                    continue
                nd = field.get((nx, ny), 10**6)
                if nd < best_d:
                    best, best_d = (nx, ny), nd
            if best is not None:
                e.x, e.y = best
        elif e.roam_x is not None and e.roam_y is not None:
            # Roaming to another room: walk the corridors, then settle there
            _roam_step(floor, e)
        elif rng.random() < DUNGEON_ROAM_CHANCE and len(floor.rooms) > 1:
            target_room = rng.choice(
                [i for i in range(len(floor.rooms)) if i != e.home_room]
            )
            e.roam_x, e.roam_y = floor.rooms[target_room].center
            e.home_room = target_room
        elif rng.random() < DUNGEON_WANDER_CHANCE:
            options = []
            for d in ALL_DIRECTIONS:
                if not can_step(floor, e.x, e.y, d):
                    continue
                nx, ny = e.x + d.delta[0], e.y + d.delta[1]
                if _blocked_for_pack(floor, nx, ny, e):
                    continue
                # Tethered: wander inside the home room
                if e.home_room is not None and e.home_room < len(floor.rooms):
                    if not floor.rooms[e.home_room].contains(nx, ny):
                        continue
                options.append((nx, ny))
            if options:
                e.x, e.y = rng.choice(options)
    return None


def _roam_step(floor: FloorState, e: MapEntity) -> None:
    """One step along a BFS path toward the roam target (packs don't
    path through other entities; a blocked roamer just waits)."""
    assert e.roam_x is not None and e.roam_y is not None
    goal = (e.roam_x, e.roam_y)
    if (e.x, e.y) == goal or chebyshev(e.x, e.y, *goal) <= 1:
        e.roam_x = e.roam_y = None
        return
    start = (e.x, e.y)
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    seen = {start}
    q: deque[tuple[int, int]] = deque([start])
    found = False
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            found = True
            break
        for d in ALL_DIRECTIONS:
            if not can_step(floor, x, y, d):
                continue
            n = (x + d.delta[0], y + d.delta[1])
            if n in seen:
                continue
            seen.add(n)
            prev[n] = (x, y)
            q.append(n)
    if not found:
        e.roam_x = e.roam_y = None
        return
    step = goal
    while prev[step] != start:
        step = prev[step]
    if not _blocked_for_pack(floor, step[0], step[1], e):
        e.x, e.y = step


def _pack_label(e: MapEntity) -> str:
    if not e.enemy_template_ids:
        return "Something"
    lead = e.enemy_template_ids[0].replace("_", " ").title()
    extra = len(e.enemy_template_ids) - 1
    return f"{lead} +{extra}" if extra else lead


def pack_label(e: MapEntity) -> str:
    """Public display label for a pack (lead name + count)."""
    return _pack_label(e)


# ----------------------------------------------------------------------
# One player turn
# ----------------------------------------------------------------------

def take_turn(
    floor: FloorState,
    direction: Direction | None,
    rng: random.Random,
    can_pickup: bool = True,
) -> StepResult:
    """Advance one map turn. ``direction=None`` waits in place.

    Order: player acts → (contact? stop) → pickup → reveal → packs act →
    turn counter. Blocked moves cost no turn (just turn to face).
    """
    if direction is not None:
        floor.facing = direction
        dx, dy = direction.delta
        tx, ty = floor.player_x + dx, floor.player_y + dy
        if not can_step(floor, floor.player_x, floor.player_y, direction):
            return StepResult(outcome=StepOutcome.BLOCKED, turn_spent=False)

        target = floor.entity_at(tx, ty)
        if target is not None and target.kind in _ENEMY_KINDS:
            target.alerted = True
            floor.turn += 1
            return StepResult(
                outcome=StepOutcome.CONTACT,
                engaged_entity_ids=[target.id, *merge_joiners(floor, target)],
                initiative=Initiative.PLAYER,
                messages=[f"You strike {_pack_label(target)} first!"],
            )

        floor.player_x, floor.player_y = tx, ty

    result = StepResult(
        outcome=StepOutcome.MOVED if direction is not None else StepOutcome.WAITED,
    )

    item = floor.entity_at(floor.player_x, floor.player_y)
    if item is not None and item.kind == EntityKind.ITEM and direction is not None:
        if item.gold > 0 or can_pickup:  # gold needs no stash room
            floor.entities = [e for e in floor.entities if e.id != item.id]
            result.outcome = StepOutcome.PICKUP
            result.picked_item_id = item.item_id
            result.picked_gold = item.gold
            result.picked_guarantee_key = item.guarantee_key
        else:
            result.outcome = StepOutcome.STASH_FULL
            result.messages.append("Your stash is full — you leave it lying there.")

    reveal_around_player(floor)

    contact = _enemy_phase(floor, rng)
    floor.turn += 1
    if contact is not None:
        return contact

    tile = floor.tile(floor.player_x, floor.player_y)
    if result.outcome in (StepOutcome.MOVED, StepOutcome.WAITED):
        if tile == TILE_STAIRS:
            result.outcome = StepOutcome.ON_STAIRS
        elif tile == TILE_EXIT:
            result.outcome = StepOutcome.ON_EXIT
    return result


def turn_rng(floor: FloorState) -> random.Random:
    """Per-turn RNG derived from (floor seed, turn): replayable, isolated."""
    return random.Random(floor.seed * 1_000_003 + floor.turn)


# ----------------------------------------------------------------------
# Pathing (tap-to-travel)
# ----------------------------------------------------------------------

def path_to(floor: FloorState, tx: int, ty: int) -> list[Direction] | None:
    """Shortest 8-dir path over EXPLORED walkable tiles to (tx, ty).

    Visible enemies block the path, except the target tile itself (walking
    into it is an attack). None if unreachable through known ground.
    """
    start = (floor.player_x, floor.player_y)
    goal = (tx, ty)
    if start == goal:
        return []
    blocked = {
        (e.x, e.y) for e in visible_entities(floor)
        if e.kind in _ENEMY_KINDS and (e.x, e.y) != goal
    }
    prev: dict[tuple[int, int], tuple[tuple[int, int], Direction]] = {}
    seen = {start}
    q: deque[tuple[int, int]] = deque([start])
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            break
        # Orthogonal first: straighter-looking paths on ties
        for d in sorted(ALL_DIRECTIONS, key=lambda d: d.is_diagonal):
            if not can_step(floor, x, y, d):
                continue
            n = (x + d.delta[0], y + d.delta[1])
            if n in seen or n in blocked or not floor.is_explored(*n):
                continue
            seen.add(n)
            prev[n] = ((x, y), d)
            q.append(n)
    if goal not in prev:
        return None
    out: list[Direction] = []
    cur = goal
    while cur != start:
        p, d = prev[cur]
        out.append(d)
        cur = p
    out.reverse()
    return out
