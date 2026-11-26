"""DungeonDirector: maps zone templates onto floors, packs onto fights.

The linear zone API on GameLoop (``get_next_encounter`` /
``advance_zone``) is untouched and still drives the sims, the TUI and
the policy solver. This is a second top level over the same zone data:

  zone encounter templates  →  packs spread across N floors (in order,
                               so early encounters stay on early floors)
  boss encounter            →  stationary boss in the last floor's far room
  overstay (cleared zone)   →  endless regenerated floors of random packs
  endless zone              →  endless floors of pool-rolled packs

Packs keep their encounter index, so level interpolation, loot
overrides and lodge reward suppression all behave as in linear mode.
Pure: RunState in, RunState out, randomness from the run RNG (floor
seeds) and per-turn derived RNGs (pack movement).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from heresiarch.engine.dungeon.generator import FloorItemSpec, PackSpec, generate_floor
from heresiarch.engine.dungeon.models import (
    RETREAT_TILES,
    DungeonTheme,
    TILE_ENTRY,
    TILE_EXIT,
    Direction,
    EntityKind,
    FloorState,
    StepOutcome,
    StepResult,
)
from heresiarch.engine.dungeon.rules import (
    path_to,
    take_turn,
    turn_rng,
    visible_entities,
)
from heresiarch.engine.formulas import (
    DUNGEON_ENDLESS_PACKS_PER_FLOOR,
    DUNGEON_OVERSTAY_PACKS_PER_FLOOR,
    calculate_dungeon_floor_count,
)
from heresiarch.engine.encounter import ENDLESS_MAX_ENEMIES, ENDLESS_MIN_ENEMIES
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.run_state import RunState
from heresiarch.engine.models.zone import ZoneState, ZoneTemplate

if TYPE_CHECKING:
    from heresiarch.engine.dungeon.models import Initiative
    from heresiarch.engine.game_loop import GameLoop

from heresiarch.engine.models.combat_state import CombatState, StatusEffect


TRAVEL_MAX_STEPS: int = 60


class DungeonError(ValueError):
    """Invalid dungeon action (not in a zone, not on stairs, ...)."""


def _template_ids(zone: ZoneTemplate, idx: int) -> tuple[str, ...]:
    enc = zone.encounters[idx]
    out: list[str] = []
    for tid, count in zip(enc.enemy_templates, enc.enemy_counts, strict=True):
        out.extend([tid] * count)
    return tuple(out)


def floor_plan(zone: ZoneTemplate) -> list[list[int]]:
    """Regular encounter indices per floor (boss goes on the last floor).

    Encounters are split in order into near-equal chunks, so a zone's
    difficulty ramp survives the move from a list to a map.
    """
    regular = [i for i, e in enumerate(zone.encounters) if not e.is_boss]
    n = calculate_dungeon_floor_count(len(regular), zone.dungeon_floors)
    plan: list[list[int]] = [[] for _ in range(n)]
    for k, idx in enumerate(regular):
        plan[min(n - 1, k * n // max(1, len(regular)))].append(idx)
    return plan


class DungeonDirector:
    """Dungeon-mode operations. Owned by GameLoop (``gl.dungeon``)."""

    def __init__(self, game_loop: GameLoop):
        self.gl = game_loop

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _zone(self, run: RunState) -> ZoneTemplate:
        if run.current_zone_id is None or run.zone_state is None:
            raise DungeonError("Not in a zone")
        return self.gl.game_data.zones[run.current_zone_id]

    def _with_zone_state(self, run: RunState, zs: ZoneState) -> RunState:
        progress = dict(run.zone_progress)
        if run.current_zone_id:
            progress[run.current_zone_id] = zs
        return run.model_copy(update={"zone_state": zs, "zone_progress": progress})

    def _roll_items(
        self, run: RunState, zone: ZoneTemplate, zs: ZoneState, floor_number: int,
    ) -> list[FloorItemSpec]:
        """Floor finds: the zone's random table + any guarantees due here.

        Guarantees only fire while a zone is still being cleared (or in
        endless zones) and only until picked up once in this run.
        """
        items = self.gl.game_data.items
        rng = self.gl.rng
        out: list[FloorItemSpec] = []

        table = zone.floor_loot
        valid = [
            e for e in table.entries
            if e.weight > 0 and (e.gold is not None or e.item_id in items)
        ]
        lo, hi = table.picks
        if valid and hi > 0:
            for _ in range(rng.randint(max(0, lo), max(lo, hi))):
                if rng.random() >= table.chance:
                    continue
                e = rng.choices(valid, weights=[v.weight for v in valid])[0]
                if e.gold is not None:
                    out.append(FloorItemSpec(gold=rng.randint(*e.gold)))
                else:
                    out.append(FloorItemSpec(item_id=e.item_id))

        if zone.is_endless or not zs.is_cleared:
            claimed = set(run.floor_guarantees_claimed.get(zone.id, []))
            for i, g in enumerate(zone.floor_guarantees):
                key = f"{i}@{floor_number}"
                if not g.applies_to(floor_number) or key in claimed:
                    continue
                if g.item_id is not None and g.item_id not in items:
                    continue
                out.append(FloorItemSpec(
                    item_id=g.item_id,
                    gold=rng.randint(*g.gold) if g.gold else 0,
                    placement=g.placement,
                    guarantee_key=key,
                ))
        return out

    def _endless_pack(self, zone: ZoneTemplate) -> PackSpec:
        pool = [t for t in zone.endless_enemy_pool if t in self.gl.game_data.enemies]
        if not pool:
            raise DungeonError(f"Endless zone {zone.id} has no valid enemy pool")
        n = self.gl.rng.randint(ENDLESS_MIN_ENEMIES, ENDLESS_MAX_ENEMIES)
        return PackSpec(None, tuple(self.gl.rng.choice(pool) for _ in range(n)))

    def _theme(self, zone: ZoneTemplate) -> DungeonTheme:
        """The zone's theme; unknown/missing ids fall back to defaults."""
        theme = self.gl.game_data.dungeon_themes.get(zone.dungeon_theme)
        return theme or DungeonTheme(id=zone.dungeon_theme or "shrine_path")

    def _build_floor(
        self, run: RunState, zone: ZoneTemplate, zs: ZoneState, floor_number: int,
    ) -> FloorState:
        seed = self.gl.rng.getrandbits(31)
        items = self._roll_items(run, zone, zs, floor_number)
        theme = self._theme(zone)
        look = {"layout": theme.layout, "theme": theme.id}

        if zone.is_endless:
            packs = [self._endless_pack(zone) for _ in range(DUNGEON_ENDLESS_PACKS_PER_FLOOR)]
            return generate_floor(seed, floor_number, 0, packs, items=items, **look)

        if zs.is_cleared:
            non_boss = [i for i, e in enumerate(zone.encounters) if not e.is_boss]
            non_boss = non_boss or list(range(len(zone.encounters)))
            packs = [
                PackSpec(i, _template_ids(zone, i))
                for i in (
                    self.gl.rng.choice(non_boss)
                    for _ in range(DUNGEON_OVERSTAY_PACKS_PER_FLOOR)
                )
            ]
            return generate_floor(seed, floor_number, 0, packs, items=items, **look)

        plan = floor_plan(zone)
        total = len(plan)
        floor_idx = min(floor_number, total) - 1
        done = set(zs.encounters_completed)
        packs = [
            PackSpec(i, _template_ids(zone, i))
            for i in plan[floor_idx] if i not in done
        ]
        boss: PackSpec | None = None
        is_last = floor_number >= total
        if is_last:
            bosses = [
                i for i, e in enumerate(zone.encounters)
                if e.is_boss and i not in done
            ]
            if bosses:
                boss = PackSpec(bosses[0], _template_ids(zone, bosses[0]))
                # Extra bosses (rare) become regular packs on the boss floor
                packs.extend(PackSpec(i, _template_ids(zone, i)) for i in bosses[1:])
        return generate_floor(
            seed, floor_number, total, packs,
            boss=boss, items=items, has_stairs=not is_last, **look,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_floor(self, run: RunState) -> RunState:
        """Make sure the current zone has a live floor (call on zone entry)."""
        zone = self._zone(run)
        zs = run.zone_state
        assert zs is not None
        if zs.floor is not None and zs.is_cleared and zs.floor.is_boss_floor:
            # Back in a cleared zone: the boss room is done — overstay
            # floors start fresh from the top.
            zs = zs.model_copy(update={"floor": None, "floor_number": 0})
        if zs.floor is not None:
            return run
        number = max(1, zs.floor_number)
        floor = self._build_floor(run, zone, zs, number)
        return self._with_zone_state(
            run, zs.model_copy(update={"floor": floor, "floor_number": number}),
        )

    def floor(self, run: RunState) -> FloorState:
        zs = run.zone_state
        if zs is None or zs.floor is None:
            raise DungeonError("No active floor — enter a zone first")
        return zs.floor

    def step(self, run: RunState, direction: Direction | None) -> tuple[RunState, StepResult]:
        """One map turn: move (or wait with None), then packs act."""
        current = self.floor(run)
        floor = current.model_copy(deep=True)
        stash_room = len(run.party.stash) < STASH_LIMIT
        result = take_turn(floor, direction, turn_rng(current), can_pickup=stash_room)
        if not result.turn_spent:
            # Facing still changes on a bump — keep it, nothing else moved
            floor = current.model_copy(update={"facing": floor.facing})

        zs = run.zone_state
        assert zs is not None
        run = self._with_zone_state(run, zs.model_copy(update={"floor": floor}))

        if result.outcome == StepOutcome.PICKUP:
            if result.picked_item_id:
                run = self.gl.apply_loot(run, _empty_loot(), [result.picked_item_id])
                name = self.gl.game_data.items[result.picked_item_id].name
                result.messages.append(f"Picked up {name}.")
            if result.picked_gold > 0:
                run = run.model_copy(update={"party": run.party.model_copy(
                    update={"money": run.party.money + result.picked_gold},
                )})
                result.messages.append(f"Picked up {result.picked_gold} gold.")
            if result.picked_guarantee_key and run.current_zone_id:
                claimed = dict(run.floor_guarantees_claimed)
                zone_claims = list(claimed.get(run.current_zone_id, []))
                if result.picked_guarantee_key not in zone_claims:
                    zone_claims.append(result.picked_guarantee_key)
                claimed[run.current_zone_id] = zone_claims
                run = run.model_copy(update={"floor_guarantees_claimed": claimed})
        return run, result

    # ------------------------------------------------------------------
    # Leaving: the retreat rule and escape items
    # ------------------------------------------------------------------

    def can_retreat(self, run: RunState) -> bool:
        """Walking out is only possible from the entry, stairs or exit.

        Floors saved before entry tiles existed (no '<' anywhere) keep the
        old free retreat rather than stranding the player.
        """
        floor = self.floor(run)
        if not any(TILE_ENTRY in row for row in floor.tiles):
            return True
        return floor.tile(floor.player_x, floor.player_y) in RETREAT_TILES

    def _take_escape_item(self, run: RunState, item_id: str) -> RunState:
        item = self.gl.game_data.items.get(item_id) or run.party.items.get(item_id)
        if item_id not in run.party.stash:
            raise DungeonError(f"'{item_id}' is not in your stash")
        if item is None or not item.escape_zone:
            raise DungeonError(f"'{item_id}' can't get you out of here")
        stash = list(run.party.stash)
        stash.remove(item_id)
        return run.model_copy(update={"party": run.party.model_copy(update={"stash": stash})})

    def escape(self, run: RunState, item_id: str) -> RunState:
        """Use an escape item on the map: out of the zone from anywhere.

        The caller then leaves the zone (``GameLoop.leave_zone``), which
        saves floor progress exactly like a normal retreat.
        """
        self.floor(run)  # must be on a floor
        return self._take_escape_item(run, item_id)

    def escape_combat(
        self, run: RunState, combat: CombatState, item_id: str,
    ) -> RunState:
        """Use an escape item mid-fight: the fight is abandoned.

        Damage taken so far sticks (HP is written back from the fight);
        no XP, no loot, and the pack is still on the floor next time.
        Fallen party members stay at 1 HP — escaping is a rescue, not a
        revive, but it never kills anyone the fight didn't.
        """
        run = self._take_escape_item(run, item_id)
        chars = dict(run.party.characters)
        for c in combat.player_combatants:
            ch = chars.get(c.id)
            if ch is None:
                continue
            hp = c.current_hp if c.is_alive else 1
            chars[c.id] = ch.model_copy(update={"current_hp": max(1, min(hp, ch.max_hp))})
        return run.model_copy(update={"party": run.party.model_copy(update={"characters": chars})})

    def travel(
        self, run: RunState, tx: int, ty: int, max_steps: int = TRAVEL_MAX_STEPS,
    ) -> tuple[RunState, list[StepResult], list[tuple[int, int]]]:
        """Walk toward (tx, ty) one turn at a time, PMD 'run' style.

        Stops on arrival, contact, pickup, stairs/exit, a newly sighted
        enemy, or a path blocked by a moving pack. Returns every step's
        result plus the player's position after each step (for animation).
        """
        results: list[StepResult] = []
        trail: list[tuple[int, int]] = []
        for _ in range(max_steps):
            floor = self.floor(run)
            if (floor.player_x, floor.player_y) == (tx, ty):
                break
            path = path_to(floor, tx, ty)
            if not path:
                if not results:
                    if path_to(floor, tx, ty, avoid_enemies=False):
                        raise DungeonError("A pack is in the way.")
                    raise DungeonError("You haven't found a way there yet.")
                break
            seen_before = {
                e.id for e in visible_entities(floor)
                if e.kind != EntityKind.ITEM
            }
            run, res = self.step(run, path[0])
            results.append(res)
            if not res.turn_spent:
                break
            floor = self.floor(run)
            trail.append((floor.player_x, floor.player_y))
            if res.outcome not in (StepOutcome.MOVED, StepOutcome.WAITED):
                break
            seen_now = {
                e.id for e in visible_entities(floor)
                if e.kind != EntityKind.ITEM
            }
            if seen_now - seen_before:
                res.messages.append("Something comes into view.")
                break
        return run, results, trail

    def descend(self, run: RunState) -> RunState:
        """Take the stairs: generate the next floor."""
        zone = self._zone(run)
        floor = self.floor(run)
        if floor.tile(floor.player_x, floor.player_y) != ">":
            raise DungeonError("You're not standing on the stairs")
        zs = run.zone_state
        assert zs is not None
        number = floor.floor_number + 1
        new_floor = self._build_floor(run, zone, zs, number)
        return self._with_zone_state(
            run, zs.model_copy(update={"floor": new_floor, "floor_number": number}),
        )

    def build_engagement(
        self, run: RunState, entity_ids: list[str],
    ) -> tuple[RunState, list[EnemyInstance]]:
        """Concrete enemies for the packs in a fight.

        In a zone being cleared, points ``current_encounter_index`` at the
        lead pack's encounter so loot overrides and lodge suppression
        resolve against the right template.
        """
        zone = self._zone(run)
        floor = self.floor(run)
        zs = run.zone_state
        assert zs is not None
        gen = self.gl.encounter_generator
        spawns = zone.random_spawns or None
        enemies: list[EnemyInstance] = []
        lead_index: int | None = None

        for eid in entity_ids:
            ent = floor.get_entity(eid)
            if ent is None or ent.kind not in (EntityKind.PACK, EntityKind.BOSS):
                raise DungeonError(f"No enemy pack '{eid}' on this floor")
            if ent.encounter_index is None:
                # Endless pack: rubber-band levels like the linear endless zone
                mc = self.gl._get_mc(run)  # noqa: SLF001 — same-engine helper
                level = mc.level if mc else zone.endless_min_level
                enemies.extend(gen.generate_endless_group(
                    ent.enemy_template_ids, level,
                    zone.endless_min_level, zone.endless_max_level,
                ))
                continue
            template = zone.encounters[ent.encounter_index]
            if zs.is_cleared:
                group = gen.generate_encounter(
                    template, zone.zone_level,
                    random_spawns=spawns, enemy_level_range=zone.enemy_level_range,
                )
            else:
                group = gen.generate_encounter(
                    template, zone.zone_level,
                    random_spawns=spawns, enemy_level_range=zone.enemy_level_range,
                    encounter_index=ent.encounter_index,
                    total_encounters=len(zone.encounters),
                )
                if lead_index is None:
                    lead_index = ent.encounter_index
            enemies.extend(group)

        if lead_index is not None:
            run = self._with_zone_state(
                run, zs.model_copy(update={"current_encounter_index": lead_index}),
            )
        return run, enemies

    def resolve_engagement(self, run: RunState, entity_ids: list[str]) -> RunState:
        """After a won fight: remove the packs, advance zone progress.

        Dungeon-mode replacement for ``GameLoop.advance_zone``. Defeating
        the boss clears the zone and opens an exit where it stood.
        """
        zone = self._zone(run)
        floor = self.floor(run).model_copy(deep=True)
        zs = run.zone_state
        assert zs is not None

        beaten = [e for e in floor.entities if e.id in set(entity_ids)]
        floor.entities = [e for e in floor.entities if e.id not in set(entity_ids)]
        updates: dict = {}

        if zone.is_endless or zs.is_cleared:
            updates["overstay_battles"] = zs.overstay_battles + 1
        else:
            completed = list(zs.encounters_completed)
            for e in beaten:
                if e.encounter_index is not None and e.encounter_index not in completed:
                    completed.append(e.encounter_index)
            updates["encounters_completed"] = completed
            updates["current_encounter_index"] = max(completed) + 1 if completed else 0
            boss_beaten = [e for e in beaten if e.kind == EntityKind.BOSS]
            if boss_beaten:
                b = boss_beaten[0]
                rows = [list(r) for r in floor.tiles]
                rows[b.y][b.x] = TILE_EXIT
                floor.tiles = ["".join(r) for r in rows]
                updates["is_cleared"] = True

        updates["floor"] = floor
        new_zs = zs.model_copy(update=updates)
        run = self._with_zone_state(run, new_zs)
        if updates.get("is_cleared") and run.current_zone_id not in run.zones_completed:
            run = run.model_copy(update={
                "zones_completed": [*run.zones_completed, run.current_zone_id],
            })
        return run


def _empty_loot():  # local import keeps the module graph shallow
    from heresiarch.engine.models.loot import LootResult
    return LootResult()


STARTLED_STATUS_ID = "startled"


def apply_initiative(combat: CombatState, initiative: Initiative | None) -> None:
    """How the map opened the fight (mutates combat; the engine is unchanged).

    Initiative is one symmetric AP number. First strike: every party
    member banks DUNGEON_FIRST_STRIKE_AP (burst comes a turn early).
    Ambush: every party member starts at DUNGEON_AMBUSH_AP, i.e. owing a
    turn — the first Survive only climbs back to 0 and Cheat stays
    locked until AP is positive (burst comes a turn late).

    Optional second ambush knob, off by default: Startled, SPD 0 for
    DUNGEON_AMBUSH_STARTLE_ROUNDS (every enemy acts first; Survive still
    resolves at priority).
    """
    from heresiarch.engine.dungeon.models import Initiative
    from heresiarch.engine.formulas import (
        DUNGEON_AMBUSH_AP,
        DUNGEON_AMBUSH_STARTLE_ROUNDS,
        DUNGEON_FIRST_STRIKE_AP,
        MAX_ACTION_POINT_BANK,
    )

    if initiative == Initiative.PLAYER and DUNGEON_FIRST_STRIKE_AP > 0:
        for c in combat.player_combatants:
            c.action_points = min(
                c.action_points + DUNGEON_FIRST_STRIKE_AP, MAX_ACTION_POINT_BANK,
            )
        return
    if initiative != Initiative.ENEMY:
        return
    if DUNGEON_AMBUSH_AP:
        for c in combat.player_combatants:
            c.action_points = max(
                -MAX_ACTION_POINT_BANK,
                min(c.action_points + DUNGEON_AMBUSH_AP, MAX_ACTION_POINT_BANK),
            )
    if DUNGEON_AMBUSH_STARTLE_ROUNDS > 0:
        for c in combat.player_combatants:
            # Show it immediately; the engine re-derives at round start
            c.effective_stats = c.effective_stats.model_copy(update={"SPD": 0})
            c.active_statuses.append(StatusEffect(
                id=STARTLED_STATUS_ID,
                name="Startled",
                stat_modifiers={"SPD": -c.equipment_stats.SPD},
                rounds_remaining=DUNGEON_AMBUSH_STARTLE_ROUNDS,
            ))
