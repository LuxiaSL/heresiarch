"""Tests for zone navigation: unlock, selection, overstay, victory."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE, LootResolver
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.zone import ZoneState, ZoneUnlockRequirement


@pytest.fixture
def game_loop(game_data: GameData, seeded_rng: random.Random) -> GameLoop:
    return GameLoop(game_data=game_data, rng=seeded_rng)


def _clear_zone(game_loop: GameLoop, run: RunState, zone_id: str, game_data: GameData) -> RunState:
    """Helper: enter and fully clear a zone (advance through all encounters)."""
    run = game_loop.enter_zone(run, zone_id)
    zone = game_data.zones[zone_id]
    for _ in range(len(zone.encounters)):
        run = game_loop.advance_zone(run)
    return run


class TestZoneUnlock:
    def test_zone_01_always_unlocked(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        assert game_loop.is_zone_unlocked(run, "zone_01")

    def test_zone_02_locked_at_start(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        assert not game_loop.is_zone_unlocked(run, "zone_02")

    def test_zone_02_unlocked_after_zone_01_clear(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        assert game_loop.is_zone_unlocked(run, "zone_02")

    def test_available_zones_at_start(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        available = game_loop.get_available_zones(run)
        assert len(available) == 1
        assert available[0].id == "zone_01"

    def test_available_zones_grow_with_progress(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        available = game_loop.get_available_zones(run)
        zone_ids = [z.id for z in available]
        assert "zone_01" in zone_ids
        assert "zone_02" in zone_ids
        assert len(available) == 2

    def test_linear_unlock_chain(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """Clearing each zone unlocks exactly the next one."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        zone_order = ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05", "zone_06", "zone_07"]

        for i, zone_id in enumerate(zone_order):
            assert game_loop.is_zone_unlocked(run, zone_id), f"{zone_id} should be unlocked"
            if i + 1 < len(zone_order):
                assert not game_loop.is_zone_unlocked(run, zone_order[i + 1])
            run = _clear_zone(game_loop, run, zone_id, game_data)

    def test_unknown_zone_not_unlocked(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        assert not game_loop.is_zone_unlocked(run, "nonexistent_zone")

    def test_available_zones_sorted_by_level(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Clear first 3 zones
        for zid in ["zone_01", "zone_02", "zone_03"]:
            run = _clear_zone(game_loop, run, zid, game_data)
        available = game_loop.get_available_zones(run)
        levels = [z.zone_level for z in available]
        assert levels == sorted(levels)


class TestEnterClearedZone:
    def test_re_entering_cleared_zone_starts_in_overstay(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        # Now re-enter zone_01
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state is not None
        assert run.zone_state.is_cleared is True
        assert run.zone_state.overstay_battles == 0

    def test_entering_fresh_zone_not_in_overstay(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state is not None
        assert run.zone_state.is_cleared is False
        assert run.zone_state.overstay_battles == 0


class TestOverstayEncounters:
    def test_overstay_generates_encounters(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """In overstay mode, get_next_encounter should still return enemies."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        run = game_loop.enter_zone(run, "zone_01")
        enemies = game_loop.get_next_encounter(run)
        assert len(enemies) > 0

    def test_overstay_advance_increments_counter(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        run = game_loop.enter_zone(run, "zone_01")

        assert run.zone_state.overstay_battles == 0
        run = game_loop.advance_zone(run)
        assert run.zone_state.overstay_battles == 1
        run = game_loop.advance_zone(run)
        assert run.zone_state.overstay_battles == 2

    def test_overstay_does_not_re_add_to_zones_completed(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        assert run.zones_completed.count("zone_01") == 1
        # Re-enter and advance (overstay)
        run = game_loop.enter_zone(run, "zone_01")
        run = game_loop.advance_zone(run)
        assert run.zones_completed.count("zone_01") == 1


class TestOverstayLootPenalty:
    def test_zero_overstay_no_penalty(self, game_data: GameData) -> None:
        rng = random.Random(42)
        resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        # Brute oni has 20% common drop — run many seeds
        drops_normal = 0
        for seed in range(200):
            rng = random.Random(seed)
            r = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            from heresiarch.engine.models.enemies import ActionTable, ActionWeight, EnemyInstance
            from heresiarch.engine.models.stats import StatBlock

            enemy = EnemyInstance(
                template_id="brute_oni",
                name="brute_oni",
                level=10,
                stats=StatBlock(STR=10, MAG=5, DEF=10, RES=5, SPD=10),
                max_hp=50,
                current_hp=0,
                abilities=["basic_attack"],
                equipment=[],
                action_table=ActionTable(
                    base_weights=[ActionWeight(ability_id="basic_attack", weight=1.0)]
                ),
            )
            result = r.resolve_encounter_drops([enemy], zone_level=10, overstay_battles=0)
            drops_normal += len(result.item_ids)
        assert drops_normal > 0  # sanity check

    def test_high_overstay_reduces_drops(self, game_data: GameData) -> None:
        """After 20 overstay battles = 100% penalty, no items should drop."""
        from heresiarch.engine.models.enemies import ActionTable, ActionWeight, EnemyInstance
        from heresiarch.engine.models.stats import StatBlock

        drops = 0
        for seed in range(200):
            rng = random.Random(seed)
            r = LootResolver(
                item_registry=game_data.items,
                drop_tables=game_data.drop_tables,
                rng=rng,
            )
            enemy = EnemyInstance(
                template_id="brute_oni",
                name="brute_oni",
                level=10,
                stats=StatBlock(STR=10, MAG=5, DEF=10, RES=5, SPD=10),
                max_hp=50,
                current_hp=0,
                abilities=["basic_attack"],
                equipment=[],
                action_table=ActionTable(
                    base_weights=[ActionWeight(ability_id="basic_attack", weight=1.0)]
                ),
            )
            result = r.resolve_encounter_drops([enemy], zone_level=10, overstay_battles=20)
            drops += len(result.item_ids)
        # At 20 * 5% = 100% penalty, all drop chances should be 0
        assert drops == 0

    def test_money_penalized_by_overstay(self, game_data: GameData) -> None:
        """Money should degrade to zero at high overstay — no farming."""
        from heresiarch.engine.models.enemies import ActionTable, ActionWeight, EnemyInstance
        from heresiarch.engine.models.stats import StatBlock

        rng = random.Random(42)
        r = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=rng,
        )
        enemy = EnemyInstance(
            template_id="fodder_slime",
            name="fodder_slime",
            level=10,
            stats=StatBlock(STR=10, MAG=5, DEF=10, RES=5, SPD=10),
            max_hp=50,
            current_hp=0,
            abilities=["basic_attack"],
            equipment=[],
            action_table=ActionTable(
                base_weights=[ActionWeight(ability_id="basic_attack", weight=1.0)]
            ),
        )
        # At 20 overstay battles (20 * 5% = 100%), money should be 0
        result = r.resolve_encounter_drops([enemy], zone_level=10, overstay_battles=20)
        assert result.money == 0

    def test_overstay_penalty_constant(self) -> None:
        assert OVERSTAY_PENALTY_PER_BATTLE == 0.05


class TestLeaveZone:
    def test_leave_clears_zone_state(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        assert run.current_zone_id is not None

        run = game_loop.leave_zone(run)
        assert run.current_zone_id is None
        assert run.zone_state is None

    def test_leave_preserves_hp(self, game_loop: GameLoop) -> None:
        """Leaving a zone does NOT heal — HP persists until a town."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")

        # Damage the MC
        mc = run.party.characters["mc_einherjar"]
        damaged_mc = mc.model_copy(update={"current_hp": 1})
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = damaged_mc
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"characters": new_chars})}
        )

        run = game_loop.leave_zone(run)
        mc = run.party.characters["mc_einherjar"]
        assert mc.current_hp == 1

    def test_leave_mid_zone_saves_progress(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """Leaving a zone and re-entering should restore encounter progress."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        run = game_loop.advance_zone(run)
        run = game_loop.advance_zone(run)
        assert run.zone_state.current_encounter_index == 2

        run = game_loop.leave_zone(run)
        assert "zone_01" in run.zone_progress
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state.current_encounter_index == 2

    def test_leave_saves_overstay_counter(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """Overstay battle count should persist across leave/re-enter."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        run = game_loop.enter_zone(run, "zone_01")
        for _ in range(3):
            run = game_loop.advance_zone(run)
        assert run.zone_state.overstay_battles == 3

        run = game_loop.leave_zone(run)
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state.overstay_battles == 3


class TestFinalZone:
    def test_zone_07_is_final(self, game_data: GameData) -> None:
        assert game_data.zones["zone_07"].is_final is True

    def test_non_final_zones(self, game_data: GameData) -> None:
        for zone_id, zone in game_data.zones.items():
            if zone_id != "zone_07":
                assert zone.is_final is False, f"{zone_id} should not be final"

    def test_all_zones_have_unlock_requirements(self, game_data: GameData) -> None:
        """All zones except zone_01 should have at least one unlock requirement."""
        for zone_id, zone in game_data.zones.items():
            if zone_id == "zone_01":
                assert len(zone.unlock_requires) == 0
            else:
                assert len(zone.unlock_requires) > 0, f"{zone_id} missing unlock_requires"


class TestOverstayIntegration:
    def test_combat_result_uses_overstay(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        """resolve_combat_result should pass overstay_battles to loot resolver."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        run = game_loop.enter_zone(run, "zone_01")

        # Advance overstay counter a few times
        for _ in range(5):
            run = game_loop.advance_zone(run)
        assert run.zone_state.overstay_battles == 5

        # Now do combat — loot should have reduced drops
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            surviving_character_hp={"mc_einherjar": 50},
            defeated_enemy_template_ids=["fodder_slime"],
            defeated_enemy_budget_multipliers=[8.0],
            rounds_taken=2,
            zone_level=1,
        )
        new_run, loot = game_loop.resolve_combat_result(run, result)
        # Money should still exist
        assert loot.money > 0


class TestTownNavigation:
    def test_town_loads(self, game_data: GameData) -> None:
        assert "shinto_town" in game_data.towns
        town = game_data.towns["shinto_town"]
        assert town.name == "Kitsune Crossing"
        assert town.region == "shinto_slimes"

    def test_town_always_unlocked_region_1(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        assert game_loop.is_town_unlocked(run, "shinto_town")

    def test_enter_leave_town(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_town(run, "shinto_town")
        assert run.current_town_id == "shinto_town"
        assert run.current_zone_id is None
        run = game_loop.leave_town(run)
        assert run.current_town_id is None

    def test_cannot_enter_town_while_in_zone(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = game_loop.enter_zone(run, "zone_01")
        with pytest.raises(ValueError, match="Cannot enter town while in a zone"):
            game_loop.enter_town(run, "shinto_town")

    def test_resolve_town_shop_before_clears(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        items = game_loop.resolve_town_shop(run)
        assert "minor_potion" in items
        assert "iron_blade" not in items

    def test_resolve_town_shop_after_zone_01(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = _clear_zone(game_loop, run, "zone_01", game_data)
        items = game_loop.resolve_town_shop(run)
        assert "minor_potion" in items
        assert "iron_blade" in items
        assert "spirit_lens" in items
        assert "potion" not in items  # requires zone_03

    def test_resolve_town_shop_after_zone_03(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        for z in ["zone_01", "zone_02", "zone_03"]:
            run = _clear_zone(game_loop, run, z, game_data)
        items = game_loop.resolve_town_shop(run)
        assert "potion" in items
        assert "runic_edge" not in items  # requires zone_05


class TestLodgeRewardSuppression:
    def test_lodge_resets_zone_and_suppresses_xp(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Progress through 3 encounters in zone 01
        run = game_loop.enter_zone(run, "zone_01")
        for _ in range(3):
            run = game_loop.advance_zone(run)
        run = game_loop.leave_zone(run)

        # Rest at lodge
        party = run.party.model_copy(update={"money": 5000})
        run = run.model_copy(update={"party": party, "current_town_id": "shinto_town"})
        run = game_loop.rest_at_lodge(run)

        assert run.lodge_reset_zones.get("zone_01") == 3
        assert "zone_01" not in run.zone_progress

        # Re-enter zone — progress resets to encounter 0
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state.current_encounter_index == 0

        # Encounter 0 (below lodge cap of 3) should give 0 XP
        result = CombatResult(
            player_won=True,
            surviving_character_ids=["mc_einherjar"],
            surviving_character_hp={"mc_einherjar": 50},
            defeated_enemy_template_ids=["fodder_slime"],
            defeated_enemy_budget_multipliers=[1.0],
            defeated_enemy_levels=[1],
            defeated_enemy_xp_multipliers=[1.0],
            defeated_enemy_gold_multipliers=[1.0],
            rounds_taken=2,
            zone_level=1,
        )
        mc_xp_before = run.party.characters["mc_einherjar"].xp
        new_run, loot = game_loop.resolve_combat_result(run, result)
        mc_xp_after = new_run.party.characters["mc_einherjar"].xp
        assert mc_xp_after == mc_xp_before  # zero XP
        assert loot.money == 0  # zero gold
        assert loot.item_ids == []  # zero loot

    def test_lodge_suppression_clears_past_cap(
        self, game_loop: GameLoop, game_data: GameData
    ) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Progress 2 encounters then lodge reset
        run = game_loop.enter_zone(run, "zone_01")
        run = game_loop.advance_zone(run)
        run = game_loop.advance_zone(run)
        run = game_loop.leave_zone(run)

        party = run.party.model_copy(update={"money": 5000})
        run = run.model_copy(update={"party": party, "current_town_id": "shinto_town"})
        run = game_loop.rest_at_lodge(run)
        assert run.lodge_reset_zones.get("zone_01") == 2

        # Re-enter and advance past the cap
        run = game_loop.enter_zone(run, "zone_01")
        run = game_loop.advance_zone(run)  # idx 0 -> 1 (still < 2, suppressed)
        run = game_loop.advance_zone(run)  # idx 1 -> 2 (reaches cap, clears)
        assert "zone_01" not in run.lodge_reset_zones
