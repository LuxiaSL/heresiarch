"""Dungeon layer: floor generation, map rules, director, session dungeon mode."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from heresiarch.agent.session import AgentError, GameSession, Phase
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.dungeon.director import floor_plan
from heresiarch.engine.dungeon.generator import (
    FloorItemSpec,
    PackSpec,
    bfs_distances,
    generate_floor,
)
from heresiarch.engine.dungeon.models import (
    TILE_ENTRY,
    TILE_EXIT,
    TILE_STAIRS,
    WALKABLE_TILES,
    Direction,
    EntityKind,
    FloorState,
    Initiative,
    MapEntity,
    Room,
    StepOutcome,
)
from heresiarch.engine.dungeon.rules import (
    can_step,
    path_to,
    take_turn,
    visible_entities,
)
from heresiarch.engine.formulas import DUNGEON_FIRST_STRIKE_AP
from heresiarch.engine.models.loot import LootResult

# ----------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------


def _walkable(floor: FloorState) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(floor.height)
        for x in range(floor.width)
        if floor.tiles[y][x] in WALKABLE_TILES
    }


@pytest.mark.parametrize("seed", range(40))
def test_floor_is_fully_connected(seed: int) -> None:
    packs = [PackSpec(i, ("fodder_slime",)) for i in range(3)]
    floor = generate_floor(seed, 1, 2, packs, items=[FloorItemSpec(item_id="minor_potion")])
    reach = set(bfs_distances(floor.tiles, (floor.player_x, floor.player_y)))
    assert _walkable(floor) <= reach
    # Everything placed stands on reachable ground
    for e in floor.entities:
        assert (e.x, e.y) in reach
    assert sum(row.count(TILE_STAIRS) for row in floor.tiles) == 1


def test_generation_is_deterministic() -> None:
    packs = [PackSpec(0, ("slime",)), PackSpec(1, ("swime", "slime"))]
    a = generate_floor(123, 1, 3, packs)
    b = generate_floor(123, 1, 3, packs)
    assert a == b
    c = generate_floor(124, 1, 3, packs)
    assert a.tiles != c.tiles


def test_boss_floor_has_boss_and_no_stairs() -> None:
    floor = generate_floor(
        5, 2, 2, [PackSpec(0, ("fodder_slime",))],
        boss=PackSpec(4, ("alpha_slime",)), has_stairs=False,
    )
    assert floor.is_boss_floor
    assert [e.kind for e in floor.entities].count(EntityKind.BOSS) == 1
    assert not any(TILE_STAIRS in row for row in floor.tiles)


def test_packs_never_spawn_in_player_room() -> None:
    for seed in range(30):
        floor = generate_floor(seed, 1, 1, [PackSpec(i, ("slime",)) for i in range(4)])
        spawn_room = floor.room_index_at(floor.player_x, floor.player_y)
        for e in floor.entities:
            if e.kind == EntityKind.PACK and len(floor.rooms) > 1:
                assert floor.room_index_at(e.x, e.y) != spawn_room


def test_floor_plan_places_every_regular_encounter_once(game_data: GameData) -> None:
    for zone in game_data.zones.values():
        if zone.is_endless:
            continue
        plan = floor_plan(zone)
        flat = [i for f in plan for i in f]
        regular = [i for i, e in enumerate(zone.encounters) if not e.is_boss]
        assert sorted(flat) == regular
        # Order preserved: difficulty ramp survives
        assert flat == sorted(flat)


# ----------------------------------------------------------------------
# Rules
# ----------------------------------------------------------------------


def _tiny_floor(rows: list[str], entities: list[MapEntity] | None = None) -> FloorState:
    """Build a hand-drawn floor; '@' marks the player (becomes floor)."""
    px = py = 0
    clean = []
    for y, row in enumerate(rows):
        if "@" in row:
            px, py = row.index("@"), y
        clean.append(row.replace("@", "."))
    floor = FloorState(
        floor_number=1, total_floors=1, seed=1,
        width=len(clean[0]), height=len(clean), tiles=clean,
        explored=["1" * len(clean[0]) for _ in clean],
        player_x=px, player_y=py, entities=entities or [],
    )
    return floor


def test_diagonal_corner_cutting_is_blocked() -> None:
    floor = _tiny_floor([
        "#####",
        "#@#.#",
        "#...#",
        "#####",
    ])
    assert not can_step(floor, 1, 1, Direction.E)
    assert not can_step(floor, 2, 2, Direction.NE) or floor.is_walkable(2, 1)
    # NE from (2,2) to (3,1): needs (3,2) and (2,1); (2,1) is wall → blocked
    assert not can_step(floor, 2, 2, Direction.NE)


def test_blocked_move_costs_no_turn() -> None:
    floor = _tiny_floor(["###", "#@#", "###"])
    res = take_turn(floor, Direction.N, random.Random(0))
    assert res.outcome == StepOutcome.BLOCKED
    assert not res.turn_spent
    assert floor.turn == 0


def test_walking_into_pack_is_first_strike() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=3, y=1,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor(["#####", "#.@.#", "#####"], [pack])
    res = take_turn(floor, Direction.E, random.Random(0))
    assert res.outcome == StepOutcome.CONTACT
    assert res.initiative == Initiative.PLAYER
    assert res.engaged_entity_ids == ["pack1"]


def test_alerted_adjacent_pack_ambushes() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=3, y=1,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor(["######", "#.@..#", "######"], [pack])
    res = take_turn(floor, None, random.Random(0))  # wait next to it
    assert res.outcome == StepOutcome.CONTACT
    assert res.initiative == Initiative.ENEMY


def test_chasing_pack_closes_distance() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=6, y=1,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor(["#########", "#@......#", "#########"], [pack])
    floor.rooms = [Room(x=1, y=1, w=7, h=1)]  # lit room: it sees you
    take_turn(floor, None, random.Random(0))
    assert pack.alerted
    assert pack.x == 5


def test_adjacent_alerted_packs_merge_into_fight() -> None:
    a = MapEntity(id="pack1", kind=EntityKind.PACK, x=3, y=1, alerted=True,
                  encounter_index=0, enemy_template_ids=["slime"])
    b = MapEntity(id="pack2", kind=EntityKind.PACK, x=4, y=1, alerted=True,
                  encounter_index=1, enemy_template_ids=["swime"])
    floor = _tiny_floor(["#######", "#.@...#", "#######"], [a, b])
    res = take_turn(floor, Direction.E, random.Random(0))
    assert res.outcome == StepOutcome.CONTACT
    assert res.engaged_entity_ids == ["pack1", "pack2"]


def test_bosses_never_merge_or_move() -> None:
    boss = MapEntity(id="boss1", kind=EntityKind.BOSS, x=5, y=1,
                     encounter_index=4, enemy_template_ids=["alpha_slime"])
    floor = _tiny_floor(["########", "#@.....#", "########"], [boss])
    for _ in range(3):
        take_turn(floor, None, random.Random(0))
    assert (boss.x, boss.y) == (5, 1)


def test_corridor_hides_distant_packs() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=10, y=1,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor(["#############", "#@..........#", "#############"], [pack])
    assert visible_entities(floor) == []


def test_path_to_routes_around_visible_packs() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=2, y=1,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor(["#####", "#@..#", "#...#", "#####"], [pack])
    path = path_to(floor, 3, 1)
    assert path is not None
    x, y = floor.player_x, floor.player_y
    for d in path:
        x, y = x + d.delta[0], y + d.delta[1]
        assert (x, y) != (2, 1)
    assert (x, y) == (3, 1)


# ----------------------------------------------------------------------
# Session (dungeon mode) end to end
# ----------------------------------------------------------------------


@pytest.fixture
def dsession(game_data: GameData, tmp_path: Path) -> GameSession:
    s = GameSession(game_data=game_data, notes_path=tmp_path / "notes.json",
                    dungeon_mode=True)
    s._get_saves_dir = lambda: tmp_path  # type: ignore[method-assign]
    s.new_run("Hero", "einherjar", seed=42)
    return s


def _fight_out(s: GameSession) -> None:
    """Basic-attack every round until the fight ends."""
    while s.phase == Phase.COMBAT:
        combat = s.combat_state
        assert combat is not None
        # Test-only invulnerability: these tests check map FLOW, and a
        # lv1 basic-attack bot is a coin flip vs a 3-slime pack even at
        # full HP — the outcome must not depend on combat luck.
        for c in combat.living_players:
            c.current_hp = c.max_hp
        target = combat.living_enemies[0].id
        s.submit_decisions({
            c.id: {"mode": "normal", "action": "basic_attack", "target": target}
            for c in combat.living_players
        })
    if s.phase == Phase.POST_COMBAT:
        s.pick_loot([])
    if s.phase == Phase.RECRUITING:
        s.recruit(False)
    _heal(s)


def _heal(s: GameSession) -> None:
    """Test-only: top everyone up. These tests check map flow, not balance
    (a basic-attack-only bot dies to zone 1 in linear mode too)."""
    run = s.run
    if run is None or run.is_dead:
        return
    chars = {
        cid: c.model_copy(update={"current_hp": c.max_hp})
        for cid, c in run.party.characters.items()
    }
    s.run = run.model_copy(update={"party": run.party.model_copy(update={"characters": chars})})


def _frontier(floor: FloorState) -> list[tuple[int, int]]:
    out = []
    for y in range(floor.height):
        for x in range(floor.width):
            if not floor.is_explored(x, y) or not floor.is_walkable(x, y):
                continue
            if any(
                not floor.is_explored(x + dx, y + dy)
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            ):
                out.append((x, y))
    return out


def _bot_play_zone(s: GameSession, max_actions: int = 800) -> None:
    """Greedy explorer: fight what you see, explore frontier, take stairs."""
    zone_id = s.run.current_zone_id  # type: ignore[union-attr]
    for _ in range(max_actions):
        if s.phase in (Phase.COMBAT, Phase.POST_COMBAT, Phase.RECRUITING):
            _fight_out(s)
            continue
        if s.phase != Phase.IN_ZONE:
            return
        run = s.run
        assert run is not None and run.zone_state is not None
        if zone_id in run.zones_completed:
            return
        floor = run.zone_state.floor
        assert floor is not None
        me = (floor.player_x, floor.player_y)

        def plen(t: tuple[int, int]) -> int:
            p = path_to(floor, *t)
            return len(p) if p is not None else 10**6

        enemies = [e for e in visible_entities(floor) if e.kind != EntityKind.ITEM]
        # The approach dance: an alerted pack two steps out will close to
        # one on its turn — wait, and the bump (first strike) is ours.
        if any(
            e.alerted and e.kind == EntityKind.PACK
            and max(abs(e.x - me[0]), abs(e.y - me[1])) == 2
            for e in enemies
        ):
            s.wait_turn()
            continue
        if enemies:
            tgt = min(enemies, key=lambda e: plen((e.x, e.y)))
            if plen((tgt.x, tgt.y)) < 10**6:
                s.travel(tgt.x, tgt.y)
                continue
        frontier = [t for t in _frontier(floor) if t != me and plen(t) < 10**6]
        if frontier:
            s.travel(*min(frontier, key=plen))
            continue
        if floor.tile(*me) == TILE_STAIRS:
            s.descend()
            continue
        stairs = [
            (x, y) for y in range(floor.height) for x in range(floor.width)
            if floor.tiles[y][x] == TILE_STAIRS and floor.is_explored(x, y)
        ]
        if stairs:
            s.travel(*stairs[0])
            continue
        s.wait_turn()
    raise AssertionError("bot did not finish the zone")


def test_bot_clears_zone_01_in_dungeon_mode(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    floor = s.run.zone_state.floor  # type: ignore[union-attr]
    assert floor is not None and floor.floor_number == 1
    _bot_play_zone(s)
    run = s.run
    assert run is not None
    assert "zone_01" in run.zones_completed
    zs = run.zone_state
    assert zs is not None and zs.is_cleared
    assert zs.floor is not None and zs.floor.is_boss_floor
    assert any(TILE_EXIT in row for row in zs.floor.tiles)
    # Boss fought; regular packs may be skipped (that's the XP-min lever)
    assert 4 in zs.encounters_completed
    assert len(set(zs.encounters_completed)) == len(zs.encounters_completed)
    # The fights are in the battle record like linear mode (merged packs
    # share one record, so <= 5)
    assert 1 <= len(run.battle_record.encounters) <= 5


def test_waiting_bot_mostly_wins_initiative(game_data: GameData, tmp_path: Path) -> None:
    """The approach dance works: patient play earns first strikes."""
    inits: list[Initiative | None] = []
    orig = GameSession._start_combat

    def spy(self, enemies, initiative=None):  # type: ignore[no-untyped-def]
        inits.append(initiative)
        return orig(self, enemies, initiative)

    GameSession._start_combat = spy  # type: ignore[method-assign]
    try:
        for seed in range(4):
            s = GameSession(game_data=game_data, notes_path=tmp_path / "n.json",
                            dungeon_mode=True)
            s._get_saves_dir = lambda: tmp_path  # type: ignore[method-assign]
            s.new_run("Hero", "einherjar", seed=seed)
            s.enter_zone("zone_01")
            _bot_play_zone(s)
    finally:
        GameSession._start_combat = orig  # type: ignore[method-assign]
    firsts = inits.count(Initiative.PLAYER)
    assert firsts > len(inits) // 2, inits


def test_fight_tool_refused_in_dungeon_mode(dsession: GameSession) -> None:
    dsession.enter_zone("zone_01")
    with pytest.raises(AgentError, match="walk into"):
        dsession.fight()


def test_first_strike_banks_ap(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    run = s.run
    assert run is not None and run.zone_state is not None
    floor = run.zone_state.floor
    assert floor is not None
    # Drop a pack right next to the player, then bump it
    pack = next(e for e in floor.entities if e.kind == EntityKind.PACK)
    for d in Direction:
        nx, ny = floor.player_x + d.delta[0], floor.player_y + d.delta[1]
        if can_step(floor, floor.player_x, floor.player_y, d) and floor.entity_at(nx, ny) is None:
            break
    pack.x, pack.y = nx, ny
    s.move(d.value)
    assert s.phase == Phase.COMBAT
    assert s.combat_state is not None
    assert all(
        c.action_points == DUNGEON_FIRST_STRIKE_AP
        for c in s.combat_state.player_combatants
    )


def test_floor_survives_save_and_load(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    before = s.run.zone_state.floor  # type: ignore[union-attr]
    s.save_run("slot1")
    s.load_run("slot1")
    after = s.run.zone_state.floor  # type: ignore[union-attr]
    assert before == after
    assert s.phase == Phase.IN_ZONE


def test_leave_and_reenter_keeps_floor(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    for _ in range(3):
        s.wait_turn()
    floor = s.run.zone_state.floor  # type: ignore[union-attr]
    s.leave_zone()
    s.enter_zone("zone_01")
    assert s.run.zone_state.floor == floor  # type: ignore[union-attr]


def _walk_to(s: GameSession, glyph: str) -> None:
    """Travel onto the first explored tile showing ``glyph``."""
    for _ in range(20):
        floor = s.run.zone_state.floor  # type: ignore[union-attr]
        if floor.tile(floor.player_x, floor.player_y) == glyph:
            return
        spots = [
            (x, y) for y in range(floor.height) for x in range(floor.width)
            if floor.tiles[y][x] == glyph and floor.is_explored(x, y)
        ]
        assert spots, f"no explored {glyph!r} tile"
        s.travel(*spots[0])
        if s.phase != Phase.IN_ZONE:
            _fight_out(s)
    raise AssertionError(f"never reached {glyph!r}")


def test_cleared_zone_reentry_starts_overstay_floor(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    _bot_play_zone(s)
    _walk_to(s, TILE_EXIT)
    s.leave_zone()
    s.enter_zone("zone_01")
    zs = s.run.zone_state  # type: ignore[union-attr]
    assert zs is not None and zs.is_cleared
    assert zs.floor is not None
    assert not zs.floor.is_boss_floor
    assert zs.floor.total_floors == 0  # unbounded
    assert any(TILE_STAIRS in row for row in zs.floor.tiles)


def test_descend_requires_stairs(dsession: GameSession) -> None:
    dsession.enter_zone("zone_01")
    with pytest.raises(AgentError, match="stairs"):
        dsession.descend()


def test_linear_mode_unchanged(game_data: GameData, tmp_path: Path) -> None:
    s = GameSession(game_data=game_data, notes_path=tmp_path / "n.json")
    s._get_saves_dir = lambda: tmp_path  # type: ignore[method-assign]
    s.new_run("Hero", "einherjar", seed=1)
    s.enter_zone("zone_01")
    assert s.run.zone_state.floor is None  # type: ignore[union-attr]
    s.fight()
    assert s.phase == Phase.COMBAT
    with pytest.raises(AgentError):
        s.move("N")


# ----------------------------------------------------------------------
# Wave 2: retreat rule, escape, ambush (Startled), floor finds, roaming
# ----------------------------------------------------------------------


def _floor(s: GameSession) -> FloorState:
    floor = s.run.zone_state.floor  # type: ignore[union-attr]
    assert floor is not None
    return floor


def _give(s: GameSession, item_id: str) -> None:
    run = s.run
    assert run is not None
    s.run = s.game_loop.apply_loot(run, LootResult(), [item_id])  # type: ignore[union-attr]


def _step_off_entry(s: GameSession) -> None:
    floor = _floor(s)
    for d in Direction:
        if can_step(floor, floor.player_x, floor.player_y, d):
            nx, ny = floor.player_x + d.delta[0], floor.player_y + d.delta[1]
            if floor.entity_at(nx, ny) is None and floor.tile(nx, ny) == ".":
                s.move(d.value)
                return
    raise AssertionError("no free floor tile next to the entry")


def test_floor_spawn_is_marked_entry(dsession: GameSession) -> None:
    dsession.enter_zone("zone_01")
    floor = _floor(dsession)
    assert floor.tile(floor.player_x, floor.player_y) == TILE_ENTRY
    assert sum(row.count(TILE_ENTRY) for row in floor.tiles) == 1


def test_retreat_only_from_entry_stairs_or_exit(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    _step_off_entry(s)
    if s.phase != Phase.IN_ZONE:
        pytest.skip("stepped into an ambush")
    with pytest.raises(AgentError, match="walk out"):
        s.leave_zone()
    _walk_to(s, TILE_ENTRY)
    s.leave_zone()
    assert s.phase == Phase.ZONE_SELECT


def test_escape_on_map_consumes_item_and_saves_floor(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    _give(s, "escape_ofuda")
    _step_off_entry(s)
    if s.phase != Phase.IN_ZONE:
        pytest.skip("stepped into an ambush")
    floor = _floor(s)
    s.escape("escape_ofuda")
    assert s.phase == Phase.ZONE_SELECT
    assert "escape_ofuda" not in s.run.party.stash  # type: ignore[union-attr]
    s.enter_zone("zone_01")
    assert _floor(s) == floor  # progress kept, like any retreat


def test_escape_mid_fight_keeps_damage_and_pack(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    _give(s, "escape_ofuda")
    floor = _floor(s)
    pack = next(e for e in floor.entities if e.kind == EntityKind.PACK)
    for d in Direction:
        nx, ny = floor.player_x + d.delta[0], floor.player_y + d.delta[1]
        if can_step(floor, floor.player_x, floor.player_y, d) and floor.entity_at(nx, ny) is None:
            break
    pack.x, pack.y = nx, ny
    s.move(d.value)
    assert s.phase == Phase.COMBAT
    combat = s.combat_state
    assert combat is not None
    mc = combat.player_combatants[0]
    mc.current_hp = max(1, mc.max_hp // 2)
    xp_before = s.run.party.characters[mc.id].xp  # type: ignore[union-attr]
    s.escape("escape_ofuda")
    run = s.run
    assert run is not None
    assert s.phase == Phase.ZONE_SELECT and s.combat_state is None
    assert run.party.characters[mc.id].current_hp == mc.max_hp // 2
    assert run.party.characters[mc.id].xp == xp_before
    assert pack.id in {e.id for e in run.zone_progress["zone_01"].floor.entities}  # type: ignore[union-attr]


def test_escape_items_are_not_combat_heals(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    _give(s, "escape_ofuda")
    mc = next(iter(s.run.party.characters))  # type: ignore[union-attr]
    with pytest.raises(AgentError, match="escape"):
        s.use_consumable("escape_ofuda", mc)


def test_escape_without_item_refused(dsession: GameSession) -> None:
    dsession.enter_zone("zone_01")
    with pytest.raises(AgentError, match="stash"):
        dsession.escape("escape_ofuda")


def test_ambush_startles_party(game_data: GameData) -> None:
    from heresiarch.engine.dungeon.director import STARTLED_STATUS_ID, apply_initiative
    from heresiarch.engine.game_loop import GameLoop

    gl = GameLoop(game_data=game_data, rng=random.Random(3))
    run = gl.new_run("r", "Hero", "einherjar")
    zone = game_data.zones["zone_01"]
    enemies = gl.encounter_generator.generate_encounter(zone.encounters[1], 1)
    chars = [run.party.characters[c] for c in run.party.active]
    combat = gl.combat_engine.initialize_combat(chars, enemies)
    apply_initiative(combat, Initiative.ENEMY)
    p = combat.player_combatants[0]
    assert any(st.id == STARTLED_STATUS_ID for st in p.active_statuses)
    assert p.effective_stats.SPD == 0
    assert p.action_points == 0
    # Round 1: SPD re-derived from the status → enemies first in turn order
    from heresiarch.engine.models.combat_state import CombatAction, PlayerTurnDecision
    decision = PlayerTurnDecision(
        combatant_id=p.id,
        primary_action=CombatAction(
            actor_id=p.id, ability_id="basic_attack",
            target_ids=[combat.enemy_combatants[0].id],
        ),
    )
    templates = {e.id: game_data.enemies[e.id.rsplit("_", 1)[0]] for e in combat.enemy_combatants}
    combat = gl.combat_engine.process_round(combat, {p.id: decision}, templates)
    order = combat.turn_order
    assert order.index(p.id) == len(order) - 1 or not combat.living_enemies
    # Expires after round 1
    assert not any(st.id == STARTLED_STATUS_ID for st in combat.player_combatants[0].active_statuses)


def test_first_floor_guarantee_lies_in_arrival_room(dsession: GameSession) -> None:
    dsession.enter_zone("zone_01")
    floor = _floor(dsession)
    spawn_room = floor.room_index_at(floor.player_x, floor.player_y)
    herbs = [
        e for e in floor.entities
        if e.kind == EntityKind.ITEM and e.guarantee_key == "0@1"
    ]
    assert len(herbs) == 1 and herbs[0].item_id == "medicinal_herb"
    assert floor.room_index_at(herbs[0].x, herbs[0].y) == spawn_room


def test_guarantee_claimed_once_per_run(dsession: GameSession) -> None:
    s = dsession
    s.enter_zone("zone_01")
    herb = next(e for e in _floor(s).entities if e.guarantee_key == "0@1")
    s.travel(herb.x, herb.y)
    if s.phase != Phase.IN_ZONE:
        pytest.skip("interrupted by a fight")
    run = s.run
    assert run is not None
    assert "medicinal_herb" in run.party.stash
    assert run.floor_guarantees_claimed == {"zone_01": ["0@1"]}
    # A regenerated floor 1 (as after a lodge reset) no longer places it
    zs = run.zone_state
    assert zs is not None
    fresh = s.game_loop.dungeon._build_floor(  # type: ignore[union-attr]  # noqa: SLF001
        run, game_data_zone(s, "zone_01"), zs, 1,
    )
    assert not any(e.guarantee_key for e in fresh.entities)


def game_data_zone(s: GameSession, zone_id: str):  # type: ignore[no-untyped-def]
    return s.game_data.zones[zone_id]


def test_milestone_guarantees_repeat() -> None:
    from heresiarch.engine.dungeon.models import FloorGuarantee

    g = FloorGuarantee(item_id="escape_ofuda", floor=5, every=5)
    assert [n for n in range(1, 21) if g.applies_to(n)] == [5, 10, 15, 20]
    once = FloorGuarantee(item_id="escape_ofuda", floor=2)
    assert [n for n in range(1, 10) if once.applies_to(n)] == [2]


def test_floor_loot_entry_needs_one_payload() -> None:
    from pydantic import ValidationError

    from heresiarch.engine.dungeon.models import FloorLootEntry

    with pytest.raises(ValidationError):
        FloorLootEntry(item_id="minor_potion", gold=(1, 2))
    with pytest.raises(ValidationError):
        FloorLootEntry()


def test_gold_pickup_ignores_full_stash() -> None:
    gold = MapEntity(id="item1", kind=EntityKind.ITEM, x=3, y=1, gold=12)
    floor = _tiny_floor(["#####", "#.@.#", "#####"], [gold])
    res = take_turn(floor, Direction.E, random.Random(0), can_pickup=False)
    assert res.outcome == StepOutcome.PICKUP and res.picked_gold == 12


def test_unknown_floor_item_fails_validation(game_data: GameData) -> None:
    from heresiarch.engine.dungeon.models import FloorLootEntry

    zone = game_data.zones["zone_03"]
    bad = zone.model_copy(update={"floor_loot": zone.floor_loot.model_copy(
        update={"entries": [FloorLootEntry(item_id="no_such_item")]},
    )})
    zones = dict(game_data.zones)
    zones["zone_03"] = bad
    gd = game_data.model_copy(update={"zones": zones})
    errors = gd.validate_cross_references()
    assert any("no_such_item" in e for e in errors)


def test_roaming_pack_walks_to_another_room() -> None:
    from heresiarch.engine.dungeon.rules import _roam_step

    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=1, y=1,
                     encounter_index=0, enemy_template_ids=["slime"],
                     roam_x=9, roam_y=1)
    floor = _tiny_floor(["###########", "#.........#", "#####@#####", "#####.#####"], [pack])
    for _ in range(10):
        if pack.roam_x is None:
            break
        _roam_step(floor, pack)
    assert pack.roam_x is None  # arrived (within 1)
    assert pack.x >= 8


def test_walls_block_corridor_sight() -> None:
    pack = MapEntity(id="pack1", kind=EntityKind.PACK, x=3, y=3,
                     encounter_index=0, enemy_template_ids=["slime"])
    floor = _tiny_floor([
        "#####",
        "#@..#",
        "#####",
        "#..##",
        "#####",
    ], [pack])
    floor.explored = ["0" * 5 for _ in range(5)]
    assert visible_entities(floor) == []
