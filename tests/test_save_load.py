"""Tests for save/load system: round-trips, autosave, permadeath, rehydration."""

import json
from pathlib import Path

import pytest

from heresiarch.engine.data_loader import load_all
from heresiarch.engine.formulas import calculate_effective_stats, calculate_max_hp, calculate_stats_at_level
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.run_state import RunState
from heresiarch.engine.models.stats import StatBlock
from heresiarch.engine.save_manager import SaveManager, SaveSlot


def _make_test_run(run_id: str = "test_run_001") -> RunState:
    """Create a minimal RunState for testing."""
    mc = CharacterInstance(
        id="mc_einherjar",
        name="Test Hero",
        job_id="einherjar",
        level=5,
        xp=250,
        base_stats=StatBlock(STR=25, MAG=5, DEF=25, RES=5, SPD=15),
        current_hp=100,
        abilities=["retaliate"],
        is_mc=True,
    )
    party = Party(
        active=["mc_einherjar"],
        characters={"mc_einherjar": mc},
        money=500,
    )
    return RunState(
        run_id=run_id,
        party=party,
        current_zone_id="zone_01",
        created_at="2026-04-06T00:00:00Z",
    )


class TestSaveRoundTrip:
    def test_save_and_load(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.save_run(run, "slot_1")
        loaded = manager.load_run(run.run_id, "slot_1")
        assert loaded.run_id == run.run_id
        assert loaded.party.money == run.party.money
        assert loaded.party.characters["mc_einherjar"].level == 5
        assert loaded.current_zone_id == "zone_01"

    def test_round_trip_preserves_all_fields(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.save_run(run, "slot_1")
        loaded = manager.load_run(run.run_id, "slot_1")
        assert run.model_dump() == loaded.model_dump()

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        with pytest.raises(FileNotFoundError, match="No save found"):
            manager.load_run("nonexistent", "slot_1")


class TestAutosave:
    def test_autosave_creates_file(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        slot = manager.autosave(run)
        assert slot.slot_id == "autosave"
        assert (tmp_path / run.run_id / "autosave.json").exists()

    def test_autosave_overwrites(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.autosave(run)

        # Modify and autosave again
        mc = run.party.characters["mc_einherjar"]
        new_mc = mc.model_copy(update={"level": 10})
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = new_mc
        new_party = run.party.model_copy(update={"characters": new_chars})
        run2 = run.model_copy(update={"party": new_party})
        manager.autosave(run2)

        loaded = manager.load_run(run.run_id, "autosave")
        assert loaded.party.characters["mc_einherjar"].level == 10


class TestMultipleSlots:
    def test_save_two_slots(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.save_run(run, "slot_1")
        manager.save_run(run, "slot_2")

        loaded1 = manager.load_run(run.run_id, "slot_1")
        loaded2 = manager.load_run(run.run_id, "slot_2")
        assert loaded1.model_dump() == loaded2.model_dump()

    def test_list_slots(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.save_run(run, "slot_1")
        manager.save_run(run, "slot_2")
        manager.autosave(run)

        slots = manager.list_slots(run.run_id)
        slot_ids = [s.slot_id for s in slots]
        assert "slot_1" in slot_ids
        assert "slot_2" in slot_ids
        assert "autosave" in slot_ids


class TestDeleteRunSaves:
    def test_delete_removes_all(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        manager.save_run(run, "slot_1")
        manager.autosave(run)

        manager.delete_run_saves(run.run_id)

        with pytest.raises(FileNotFoundError):
            manager.load_run(run.run_id, "slot_1")
        assert not (tmp_path / run.run_id).exists()

    def test_delete_nonexistent_is_noop(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        manager.delete_run_saves("nonexistent")  # Should not raise


class TestListRuns:
    def test_list_multiple_runs(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run1 = _make_test_run("run_001")
        run2 = _make_test_run("run_002")
        manager.save_run(run1, "slot_1")
        manager.save_run(run2, "slot_1")

        runs = manager.list_runs()
        assert "run_001" in runs
        assert "run_002" in runs

    def test_list_empty(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        assert manager.list_runs() == []


class TestSlotMetadata:
    def test_slot_has_correct_fields(self, tmp_path: Path) -> None:
        manager = SaveManager(tmp_path)
        run = _make_test_run()
        slot = manager.save_run(run, "slot_1")
        assert slot.run_id == run.run_id
        assert slot.zone_id == "zone_01"
        assert slot.saved_at != ""
        assert "Test Hero" in slot.party_level_summary


class TestRehydration:
    """Verify that derived fields are correctly recomputed after load."""

    @pytest.fixture
    def game_loop(self, game_data: "GameData") -> GameLoop:
        import random

        return GameLoop(game_data=game_data, rng=random.Random(42))

    def test_rehydrate_fixes_zero_max_hp(self, game_loop: GameLoop, tmp_path: Path) -> None:
        """A save with max_hp=0 (old format) gets correct max_hp after rehydration."""
        manager = SaveManager(tmp_path)
        run = _make_test_run()

        # Verify the problem: max_hp defaults to 0
        mc = run.party.characters["mc_einherjar"]
        assert mc.max_hp == 0

        manager.save_run(run, "slot_1")
        loaded = manager.load_run(run.run_id, "slot_1")
        assert loaded.party.characters["mc_einherjar"].max_hp == 0  # Still broken

        # Rehydrate fixes it
        rehydrated = game_loop.rehydrate_run(loaded)
        mc_fixed = rehydrated.party.characters["mc_einherjar"]
        assert mc_fixed.max_hp > 0
        assert mc_fixed.effective_stats.STR > 0

    def test_rehydrate_computes_correct_values(self, game_loop: GameLoop) -> None:
        """Rehydrated stats match what new_run would produce."""
        fresh = game_loop.new_run("test", "Hero", "einherjar")
        fresh_mc = fresh.party.characters["mc_einherjar"]

        # Create a "loaded" run with same base data but zeroed derived fields
        stale_mc = fresh_mc.model_copy(update={
            "max_hp": 0,
            "effective_stats": StatBlock(),
        })
        stale_run = fresh.model_copy(update={
            "party": fresh.party.model_copy(update={
                "characters": {"mc_einherjar": stale_mc},
            }),
        })

        rehydrated = game_loop.rehydrate_run(stale_run)
        mc = rehydrated.party.characters["mc_einherjar"]
        assert mc.max_hp == fresh_mc.max_hp
        assert mc.effective_stats == fresh_mc.effective_stats

    def test_rehydrate_with_equipment(self, game_loop: GameLoop) -> None:
        """Equipment scaling is included in rehydrated effective stats."""
        run = game_loop.new_run("test", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]

        # Equip iron_blade
        equipped_mc = mc.model_copy(update={
            "equipment": {**mc.equipment, "WEAPON": "iron_blade"},
        })
        stale_run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": {"mc_einherjar": equipped_mc},
            }),
        })

        rehydrated = game_loop.rehydrate_run(stale_run)
        mc_r = rehydrated.party.characters["mc_einherjar"]

        # Iron Blade adds 20 + 1.0*STR to effective STR
        assert mc_r.effective_stats.STR > mc_r.base_stats.STR

    def test_rehydrate_caps_current_hp(self, game_loop: GameLoop) -> None:
        """If current_hp exceeds recomputed max_hp, it gets capped."""
        run = game_loop.new_run("test", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]

        # Set current_hp absurdly high (as if max_hp formula changed)
        inflated = mc.model_copy(update={"current_hp": 999999})
        stale_run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": {"mc_einherjar": inflated},
            }),
        })

        rehydrated = game_loop.rehydrate_run(stale_run)
        mc_r = rehydrated.party.characters["mc_einherjar"]
        assert mc_r.current_hp == mc_r.max_hp

    def test_rehydrate_preserves_current_hp_when_valid(self, game_loop: GameLoop) -> None:
        """current_hp below max_hp is preserved (don't heal on load)."""
        run = game_loop.new_run("test", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]

        damaged = mc.model_copy(update={"current_hp": 10})
        stale_run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": {"mc_einherjar": damaged},
            }),
        })

        rehydrated = game_loop.rehydrate_run(stale_run)
        assert rehydrated.party.characters["mc_einherjar"].current_hp == 10

    def test_full_save_load_rehydrate_pipeline(self, game_loop: GameLoop, tmp_path: Path) -> None:
        """End-to-end: new_run → save → load → rehydrate produces playable state."""
        manager = SaveManager(tmp_path)
        run = game_loop.new_run("pipeline_test", "Lux", "berserker")
        mc = run.party.characters["mc_berserker"]
        original_max_hp = mc.max_hp
        original_str = mc.effective_stats.STR
        assert original_max_hp > 0

        # Save and load
        manager.autosave(run)
        loaded = manager.load_run("pipeline_test", "autosave")

        # Loaded state has the correct values since they were in the JSON
        # But rehydrate should produce identical results
        rehydrated = game_loop.rehydrate_run(loaded)
        mc_r = rehydrated.party.characters["mc_berserker"]
        assert mc_r.max_hp == original_max_hp
        assert mc_r.effective_stats.STR == original_str
        assert mc_r.current_hp == original_max_hp

    def test_rehydrate_multiple_characters(self, game_loop: GameLoop) -> None:
        """All party members get rehydrated, not just the first."""
        run = game_loop.new_run("test", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]

        # Add a second character with zeroed derived fields
        recruit = CharacterInstance(
            id="recruit_onmyoji",
            name="Sage",
            job_id="onmyoji",
            level=5,
            base_stats=calculate_stats_at_level(
                game_loop.game_data.jobs["onmyoji"].growth, 5
            ),
            current_hp=50,
            abilities=["basic_attack", "foresight"],
        )
        new_chars = dict(run.party.characters)
        new_chars["recruit_onmyoji"] = recruit
        multi_run = run.model_copy(update={
            "party": run.party.model_copy(update={
                "characters": new_chars,
                "active": ["mc_einherjar", "recruit_onmyoji"],
            }),
        })

        rehydrated = game_loop.rehydrate_run(multi_run)
        mc_r = rehydrated.party.characters["mc_einherjar"]
        recruit_r = rehydrated.party.characters["recruit_onmyoji"]
        assert mc_r.max_hp > 0
        assert recruit_r.max_hp > 0
        assert recruit_r.effective_stats.MAG > 0
