"""Shared map view builders: anchor statuses, path frontier, initial cursor.

The map logic that used to live inside the TUI screens now lives in
heresiarch.views.map_builder so the TUI and the mobile UI agree on it.
These tests drive the builders with real game data + a real GameLoop.
"""

from __future__ import annotations

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.run_state import RunState
from heresiarch.views.map_builder import (
    AnchorState,
    build_region_map_vm,
    build_town_map_vm,
    build_zone_map_vm,
)


@pytest.fixture
def game_loop(game_data: GameData) -> GameLoop:
    return GameLoop(game_data=game_data, rng=random.Random(42))


@pytest.fixture
def run(game_loop: GameLoop) -> RunState:
    return game_loop.new_run("test_run", "Mapper", "einherjar")


# ---------------------------------------------------------------------------
# Region map
# ---------------------------------------------------------------------------


class TestRegionMap:
    def test_fresh_run_builds_frontier_region(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        vm = build_region_map_vm(run, game_data, game_loop)
        assert vm is not None
        assert vm.kind == "region"
        assert vm.art and vm.width > 0 and vm.height == len(vm.art)
        assert vm.navigable_ids, "fresh run must have at least one navigable zone"
        # Initial cursor lands on an AVAILABLE anchor
        initial = vm.anchor_for_id(vm.initial_id or "")
        assert initial is not None
        assert initial.status == AnchorState.AVAILABLE

    def test_statuses_partition(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        vm = build_region_map_vm(run, game_data, game_loop)
        assert vm is not None
        available_ids = {z.id for z in game_loop.get_available_zones(run)}
        for anchor in vm.anchors:
            if anchor.anchor_type == "town":
                continue
            if anchor.id in available_ids:
                assert anchor.status == AnchorState.AVAILABLE
                assert anchor.id in vm.navigable_ids
            else:
                assert anchor.status == AnchorState.LOCKED
                assert anchor.id not in vm.navigable_ids

    def test_cleared_zone_marked(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        first = game_loop.get_available_zones(run)[0]
        run = run.model_copy(update={"zones_completed": [first.id]})
        vm = build_region_map_vm(run, game_data, game_loop)
        assert vm is not None
        anchor = vm.anchor_for_id(first.id)
        assert anchor is not None
        assert anchor.status == AnchorState.CLEARED
        assert anchor.id in vm.navigable_ids

    def test_requested_anchor_wins(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        vm = build_region_map_vm(run, game_data, game_loop)
        assert vm is not None and vm.navigable_ids
        wanted = vm.navigable_ids[-1]
        vm2 = build_region_map_vm(
            run, game_data, game_loop, requested_anchor_id=wanted,
        )
        assert vm2 is not None
        assert vm2.initial_id == wanted

    def test_zone_anchors_carry_labels(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        vm = build_region_map_vm(run, game_data, game_loop)
        assert vm is not None
        for anchor in vm.anchors:
            zone = game_data.zones.get(anchor.id)
            if zone is not None:
                assert anchor.label == zone.name


# ---------------------------------------------------------------------------
# Zone path map
# ---------------------------------------------------------------------------


class TestZoneMap:
    @pytest.fixture
    def in_zone(self, run: RunState, game_loop: GameLoop) -> RunState:
        first = game_loop.get_available_zones(run)[0]
        return game_loop.enter_zone(run, first.id)

    def test_fresh_zone_frontier(
        self, in_zone: RunState, game_data: GameData,
    ) -> None:
        vm = build_zone_map_vm(in_zone, game_data)
        assert vm is not None
        assert vm.kind == "zone"
        enc0 = vm.anchor_for_id("enc_0")
        assert enc0 is not None
        assert enc0.status == AnchorState.AVAILABLE
        assert vm.initial_id == "enc_0"
        # Later encounters are locked and not navigable
        enc1 = vm.anchor_for_id("enc_1")
        if enc1 is not None:
            assert enc1.status == AnchorState.LOCKED
            assert "enc_1" not in vm.navigable_ids
        # Exit is always navigable
        assert "exit" in vm.navigable_ids

    def test_progress_advances_frontier(
        self, in_zone: RunState, game_data: GameData,
    ) -> None:
        zs = in_zone.zone_state
        assert zs is not None
        run = in_zone.model_copy(update={
            "zone_state": zs.model_copy(update={
                "current_encounter_index": 1,
                "encounters_completed": [0],
            }),
        })
        vm = build_zone_map_vm(run, game_data)
        assert vm is not None
        assert vm.anchor_for_id("enc_0").status == AnchorState.CLEARED
        assert vm.anchor_for_id("enc_1").status == AnchorState.AVAILABLE
        assert vm.initial_id == "enc_1"

        # Path frontier: traversed cells stop at enc_1's column
        enc1 = vm.anchor_for_id("enc_1")
        traversed_cols = [c.col for c in vm.path_cells if c.traversed]
        locked_cols = [c.col for c in vm.path_cells if not c.traversed]
        assert traversed_cols and max(traversed_cols) <= enc1.col
        if locked_cols:
            assert min(locked_cols) > enc1.col

    def test_path_cells_skip_anchors_and_spaces(
        self, in_zone: RunState, game_data: GameData,
    ) -> None:
        vm = build_zone_map_vm(in_zone, game_data)
        assert vm is not None
        assert vm.path_cells, "zone map should have a colorable path row"
        anchor_cells = {(a.row, a.col) for a in vm.anchors}
        for cell in vm.path_cells:
            assert (cell.row, cell.col) not in anchor_cells
            assert vm.art[cell.row][cell.col] != " "

    def test_cleared_zone_overstay(
        self, in_zone: RunState, game_data: GameData,
    ) -> None:
        zone = game_data.zones[in_zone.current_zone_id]
        zs = in_zone.zone_state
        run = in_zone.model_copy(update={
            "zone_state": zs.model_copy(update={
                "current_encounter_index": len(zone.encounters),
                "encounters_completed": list(range(len(zone.encounters))),
                "is_cleared": True,
                "overstay_battles": 2,
            }),
            "zones_completed": [in_zone.current_zone_id],
        })
        vm = build_zone_map_vm(run, game_data)
        assert vm is not None
        for i in range(len(zone.encounters)):
            anchor = vm.anchor_for_id(f"enc_{i}")
            assert anchor is not None
            assert anchor.status == AnchorState.CLEARED
            assert f"enc_{i}" in vm.navigable_ids
        # Boss node becomes a travel tile when the zone routes onward
        if zone.next_zone:
            boss_idx = next(
                i for i, e in enumerate(zone.encounters) if e.is_boss
            )
            boss = vm.anchor_for_id(f"enc_{boss_idx}")
            assert boss is not None
            assert boss.travel_to == zone.next_zone
            # Initial cursor never lands on the travel tile
            assert vm.initial_id != f"enc_{boss_idx}"


# ---------------------------------------------------------------------------
# Town interior map
# ---------------------------------------------------------------------------


class TestTownMap:
    def test_town_map_all_available(
        self, run: RunState, game_data: GameData, game_loop: GameLoop,
    ) -> None:
        town = next(iter(game_data.towns.values()), None)
        if town is None or game_data.maps.get(town.id) is None:
            pytest.skip("no town map in current data")
        run = run.model_copy(update={"current_town_id": town.id})
        vm = build_town_map_vm(run, game_data)
        assert vm is not None
        assert vm.kind == "town"
        assert vm.anchors and vm.navigable_ids
        for anchor in vm.anchors:
            assert anchor.status == AnchorState.AVAILABLE
        assert vm.initial_id == vm.navigable_ids[0]

    def test_no_town_returns_none(
        self, run: RunState, game_data: GameData,
    ) -> None:
        assert build_town_map_vm(run, game_data) is None
