"""Tests for equip/unequip, party swap, consumables, lodge rest."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level
from heresiarch.engine.game_loop import STASH_LIMIT, GameLoop
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.run_state import RunState


@pytest.fixture
def game_loop(game_data: GameData) -> GameLoop:
    return GameLoop(game_data=game_data, rng=random.Random(42))


def _run_with_weapon_in_stash(game_loop: GameLoop, game_data: GameData) -> RunState:
    """Create a run with iron_blade in stash."""
    run = game_loop.new_run("run_001", "Hero", "einherjar")
    party = run.party.model_copy(
        update={
            "stash": ["iron_blade"],
            "items": {"iron_blade": game_data.items["iron_blade"]},
        }
    )
    return run.model_copy(update={"party": party})


class TestEquipItem:
    def test_equip_from_stash(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        run = game_loop.equip_item(run, "mc_einherjar", "iron_blade", "WEAPON")
        mc = run.party.characters["mc_einherjar"]
        assert mc.equipment["WEAPON"] == "iron_blade"
        assert "iron_blade" not in run.party.stash

    def test_equip_swaps_old_item_to_stash(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        run = game_loop.equip_item(run, "mc_einherjar", "iron_blade", "WEAPON")
        party = run.party.model_copy(
            update={
                "stash": list(run.party.stash) + ["spirit_lens"],
                "items": {**run.party.items, "spirit_lens": game_data.items["spirit_lens"]},
            }
        )
        run = run.model_copy(update={"party": party})
        run = game_loop.equip_item(run, "mc_einherjar", "spirit_lens", "WEAPON")
        mc = run.party.characters["mc_einherjar"]
        assert mc.equipment["WEAPON"] == "spirit_lens"
        assert "iron_blade" in run.party.stash

    def test_equip_not_in_stash_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="not in stash"):
            game_loop.equip_item(run, "mc_einherjar", "iron_blade", "WEAPON")

    def test_equip_invalid_slot_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        with pytest.raises(ValueError, match="Invalid slot"):
            game_loop.equip_item(run, "mc_einherjar", "iron_blade", "PANTS")

    def test_equip_consumable_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        party = run.party.model_copy(
            update={
                "stash": ["minor_potion"],
                "items": {"minor_potion": game_data.items["minor_potion"]},
            }
        )
        run = run.model_copy(update={"party": party})
        with pytest.raises(ValueError, match="consumable"):
            game_loop.equip_item(run, "mc_einherjar", "minor_potion", "ACCESSORY_1")


class TestUnequipItem:
    def test_unequip_to_stash(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        run = game_loop.equip_item(run, "mc_einherjar", "iron_blade", "WEAPON")
        run = game_loop.unequip_item(run, "mc_einherjar", "WEAPON")
        mc = run.party.characters["mc_einherjar"]
        assert mc.equipment["WEAPON"] is None
        assert "iron_blade" in run.party.stash

    def test_unequip_empty_slot_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="empty"):
            game_loop.unequip_item(run, "mc_einherjar", "WEAPON")

    def test_unequip_stash_full_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        run = game_loop.equip_item(run, "mc_einherjar", "iron_blade", "WEAPON")
        party = run.party.model_copy(update={"stash": ["x"] * STASH_LIMIT})
        run = run.model_copy(update={"party": party})
        with pytest.raises(ValueError, match="full"):
            game_loop.unequip_item(run, "mc_einherjar", "WEAPON")


class TestSwapPartyMember:
    def _run_with_reserve(self, game_loop: GameLoop, game_data: GameData) -> tuple[RunState, str]:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        from heresiarch.engine.recruitment import RecruitmentEngine
        re = RecruitmentEngine(game_data.jobs, rng=random.Random(99))
        candidate = re.generate_candidate(zone_level=5)
        party = run.party.model_copy(
            update={
                "reserve": [candidate.character.id],
                "characters": {**run.party.characters, candidate.character.id: candidate.character},
            }
        )
        return run.model_copy(update={"party": party}), candidate.character.id

    def test_swap_active_and_reserve(self, game_loop: GameLoop, game_data: GameData) -> None:
        run, reserve_id = self._run_with_reserve(game_loop, game_data)
        run = game_loop.swap_party_member(run, "mc_einherjar", reserve_id)
        assert reserve_id in run.party.active
        assert "mc_einherjar" in run.party.reserve

    def test_swap_invalid_active_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run, reserve_id = self._run_with_reserve(game_loop, game_data)
        with pytest.raises(ValueError, match="not in active"):
            game_loop.swap_party_member(run, "nonexistent", reserve_id)

    def test_swap_invalid_reserve_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run, _ = self._run_with_reserve(game_loop, game_data)
        with pytest.raises(ValueError, match="not in reserve"):
            game_loop.swap_party_member(run, "mc_einherjar", "nonexistent")


class TestUseConsumable:
    def test_potion_heals(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        mc = mc.model_copy(update={"current_hp": 10})
        party = run.party.model_copy(
            update={
                "characters": {**run.party.characters, "mc_einherjar": mc},
                "stash": ["minor_potion"],
                "items": {"minor_potion": game_data.items["minor_potion"]},
            }
        )
        run = run.model_copy(update={"party": party})
        run = game_loop.use_consumable(run, "minor_potion", "mc_einherjar")
        assert run.party.characters["mc_einherjar"].current_hp == 60
        assert "minor_potion" not in run.party.stash

    def test_elixir_heals_to_full(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        mc = mc.model_copy(update={"current_hp": 1})
        job = game_data.jobs["einherjar"]
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, mc.level, mc.base_stats.DEF)
        party = run.party.model_copy(
            update={
                "characters": {**run.party.characters, "mc_einherjar": mc},
                "stash": ["elixir"],
                "items": {"elixir": game_data.items["elixir"]},
            }
        )
        run = run.model_copy(update={"party": party})
        run = game_loop.use_consumable(run, "elixir", "mc_einherjar")
        assert run.party.characters["mc_einherjar"].current_hp == max_hp

    def test_heal_capped_at_max(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        job = game_data.jobs["einherjar"]
        mc = run.party.characters["mc_einherjar"]
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, mc.level, mc.base_stats.DEF)
        party = run.party.model_copy(
            update={"stash": ["minor_potion"], "items": {"minor_potion": game_data.items["minor_potion"]}}
        )
        run = run.model_copy(update={"party": party})
        run = game_loop.use_consumable(run, "minor_potion", "mc_einherjar")
        assert run.party.characters["mc_einherjar"].current_hp == max_hp

    def test_use_non_consumable_raises(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = _run_with_weapon_in_stash(game_loop, game_data)
        with pytest.raises(ValueError, match="not a consumable"):
            game_loop.use_consumable(run, "iron_blade", "mc_einherjar")

    def test_use_not_in_stash_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="not in stash"):
            game_loop.use_consumable(run, "minor_potion", "mc_einherjar")


class TestLodgeRest:
    def test_heals_all_to_full(self, game_loop: GameLoop, game_data: GameData) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Damage the MC
        mc = run.party.characters["mc_einherjar"]
        mc = mc.model_copy(update={"current_hp": 1})
        party = run.party.model_copy(
            update={
                "characters": {**run.party.characters, "mc_einherjar": mc},
                "money": 5000,
            }
        )
        run = run.model_copy(update={"party": party, "current_town_id": "shinto_town"})
        run = game_loop.rest_at_lodge(run)
        job = game_data.jobs["einherjar"]
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, mc.level, mc.base_stats.DEF)
        assert run.party.characters["mc_einherjar"].current_hp == max_hp

    def test_costs_gold(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        party = run.party.model_copy(update={"money": 5000})
        run = run.model_copy(update={"party": party, "current_town_id": "shinto_town"})
        gold_before = run.party.money
        run = game_loop.rest_at_lodge(run)
        assert run.party.money < gold_before

    def test_insufficient_gold_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        run = run.model_copy(update={"current_town_id": "shinto_town"})
        # Default gold is 0
        with pytest.raises(ValueError, match="Insufficient funds"):
            game_loop.rest_at_lodge(run)

    def test_resets_zone_progress(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        # Enter and partially progress through zone 1
        run = game_loop.enter_zone(run, "zone_01")
        assert run.zone_state is not None
        run = run.model_copy(
            update={
                "zone_state": run.zone_state.model_copy(
                    update={"current_encounter_index": 3}
                )
            }
        )
        run = game_loop.leave_zone(run)
        assert "zone_01" in run.zone_progress

        # Rest at lodge
        party = run.party.model_copy(update={"money": 5000})
        run = run.model_copy(update={"party": party, "current_town_id": "shinto_town"})
        run = game_loop.rest_at_lodge(run)

        # Zone progress reset, lodge_reset_zones tracks high-water mark
        assert "zone_01" not in run.zone_progress
        assert run.lodge_reset_zones.get("zone_01") == 3

    def test_not_in_town_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        party = run.party.model_copy(update={"money": 5000})
        run = run.model_copy(update={"party": party})
        with pytest.raises(ValueError, match="Must be in a town"):
            game_loop.rest_at_lodge(run)
