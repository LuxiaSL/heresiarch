"""Save/load system: JSON serialization of RunState, save slots, permadeath.

This is the ONE module that does file I/O. Every other engine module is pure.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from heresiarch.engine.models.run_state import RunState

if TYPE_CHECKING:
    from heresiarch.analytics.record_db import RecordDB


class SaveSlot(BaseModel):
    """Metadata for a save slot."""

    slot_id: str
    run_id: str
    zone_id: str | None = None
    party_level_summary: str = ""
    saved_at: str = ""


class SaveManager:
    """Manages save/load operations via pydantic JSON serialization.

    Directory structure:
        saves/{run_id}/autosave.json
        saves/{run_id}/slot_1.json
        saves/{run_id}/metadata.json  (list of SaveSlot)
    """

    def __init__(
        self,
        save_dir: Path,
        record_db: RecordDB | None = None,
    ):
        self.save_dir = save_dir
        self.record_db = record_db

    def save_run(self, run: RunState, slot_id: str) -> SaveSlot:
        """Serialize RunState to JSON file. Returns slot metadata."""
        run_dir = self.save_dir / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        save_path = run_dir / f"{slot_id}.json"
        save_path.write_text(run.model_dump_json(indent=2))

        slot = SaveSlot(
            slot_id=slot_id,
            run_id=run.run_id,
            zone_id=run.current_zone_id,
            party_level_summary=self._build_level_summary(run),
            saved_at=datetime.now(timezone.utc).isoformat(),
        )

        self._update_metadata(run.run_id, slot)
        return slot

    def load_run(self, run_id: str, slot_id: str) -> RunState:
        """Deserialize RunState from JSON file."""
        save_path = self.save_dir / run_id / f"{slot_id}.json"
        if not save_path.exists():
            raise FileNotFoundError(
                f"No save found: run={run_id}, slot={slot_id}"
            )
        return RunState.model_validate_json(save_path.read_text())

    def list_runs(self) -> list[str]:
        """List all run IDs with saves, most recently modified last."""
        if not self.save_dir.exists():
            return []
        run_dirs = [
            d for d in self.save_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]
        run_dirs.sort(key=lambda d: d.stat().st_mtime)
        return [d.name for d in run_dirs]

    def list_slots(self, run_id: str) -> list[SaveSlot]:
        """List all save slots for a run."""
        metadata_path = self.save_dir / run_id / "metadata.json"
        if not metadata_path.exists():
            return []
        data = json.loads(metadata_path.read_text())
        return [SaveSlot(**s) for s in data]

    def delete_run_saves(self, run_id: str) -> None:
        """Delete ALL saves for a run (called on death)."""
        run_dir = self.save_dir / run_id
        if not run_dir.exists():
            return
        for f in run_dir.iterdir():
            f.unlink()
        run_dir.rmdir()

    def delete_slot(self, run_id: str, slot_id: str) -> None:
        """Delete a single save slot. Removes the run dir if no slots remain."""
        run_dir = self.save_dir / run_id
        save_path = run_dir / f"{slot_id}.json"
        if save_path.exists():
            save_path.unlink()

        # Update metadata to remove the slot
        metadata_path = run_dir / "metadata.json"
        if metadata_path.exists():
            slots = json.loads(metadata_path.read_text())
            slots = [s for s in slots if s.get("slot_id") != slot_id]
            if slots:
                metadata_path.write_text(json.dumps(slots, indent=2))
            else:
                # No slots left — clean up the whole run directory
                self.delete_run_saves(run_id)

    def autosave(self, run: RunState) -> SaveSlot:
        """Save to the 'autosave' slot for this run.

        Also upserts to the attached RecordDB (if any) so every
        played run accumulates in the analytics store. DB failures
        are swallowed — never block a save on analytics.
        """
        slot = self.save_run(run, "autosave")
        if self.record_db is not None:
            from heresiarch.analytics.record_db import RunRecordMetadata
            try:
                self.record_db.record_run(
                    run,
                    RunRecordMetadata(source="tui"),
                )
            except Exception:
                pass
        return slot

    def _build_level_summary(self, run: RunState) -> str:
        """Build a brief summary of party levels."""
        parts = []
        for char_id in run.party.active + run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                parts.append(f"{char.name} Lv{char.level}")
        return ", ".join(parts) if parts else "Empty party"

    def _update_metadata(self, run_id: str, slot: SaveSlot) -> None:
        """Update the metadata file with new/updated slot info."""
        metadata_path = self.save_dir / run_id / "metadata.json"
        slots: list[dict] = []
        if metadata_path.exists():
            slots = json.loads(metadata_path.read_text())

        # Replace existing slot or append new one
        updated = False
        for i, s in enumerate(slots):
            if s.get("slot_id") == slot.slot_id:
                slots[i] = slot.model_dump()
                updated = True
                break
        if not updated:
            slots.append(slot.model_dump())

        metadata_path.write_text(json.dumps(slots, indent=2))
