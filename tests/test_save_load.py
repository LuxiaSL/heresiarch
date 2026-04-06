"""Tests for save/load system: round-trips, autosave, permadeath."""

from pathlib import Path

import pytest

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
