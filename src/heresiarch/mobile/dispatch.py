"""Framework-free action dispatch over GameSession.

This is the whole behavior of the mobile frontend, minus HTTP: a
whitelist of session methods, error-to-payload conversion, and the
StatePayload build. The FastAPI LAN server (app.py) and the Pyodide
engine-in-wasm page (wasm/) both drive these exact functions,
so the two transports cannot drift.
"""

from __future__ import annotations

import traceback
from typing import Any

import json
import re

from heresiarch.agent.session import AgentError, GameSession
from heresiarch.engine.models.run_state import RunState
from heresiarch.mobile.views import (
    EquipPreview,
    SaveTransfer,
    StatePayload,
    build_equip_preview,
    build_state_payload,
)

# Session methods the phone may call. Anything else is rejected.
ALLOWED_TOOLS: frozenset[str] = frozenset({
    "new_run", "get_state",
    "list_zones", "enter_zone", "leave_zone", "get_zone_status",
    "enter_town", "leave_town", "rest_at_lodge",
    "shop_browse", "shop_buy", "shop_sell",
    "fight", "submit_decisions",
    "move", "travel", "wait_turn", "descend", "get_map", "escape", "auto_battle_round", "get_combat_state",
    "pick_loot",
    "inspect_candidate", "recruit",
    "party_status", "equip", "unequip", "swap_roster", "dismiss",
    "use_scroll", "use_consumable", "mc_swap_job", "drop_item",
    "get_battle_record", "get_run_summary",
    "save_run", "load_run", "list_saves",
})


def current_state(session: GameSession) -> StatePayload:
    """The full state payload, independent of any action."""
    text = ""
    if session.run is not None:
        try:
            text = session.get_state()
        except AgentError:
            text = ""
    return build_state_payload(session, text=text)


def dispatch_action(
    session: GameSession, tool: str, args: dict[str, Any] | None = None,
) -> StatePayload:
    """Run one whitelisted session method; errors become payload.error."""
    args = args or {}
    if tool not in ALLOWED_TOOLS:
        return build_state_payload(session, error=f"Unknown tool: {tool!r}")
    method = getattr(session, tool, None)
    if method is None:
        return build_state_payload(session, error=f"Tool not available: {tool!r}")
    try:
        text = method(**args)
    except AgentError as e:
        return build_state_payload(session, error=str(e))
    except TypeError as e:
        # Bad/missing kwargs from the client
        return build_state_payload(session, error=f"Bad arguments: {e}")
    except Exception as e:  # noqa: BLE001 — report, don't crash the frontend
        traceback.print_exc()
        return build_state_payload(
            session, error=f"Internal error: {type(e).__name__}: {e}",
        )
    return build_state_payload(session, text=text)


def _clean_slot(slot: str) -> str:
    """Slot names become filenames — keep them boring."""
    return re.sub(r"[^a-z0-9_-]", "", slot.lower())[:32]


def export_save(session: GameSession, slot: str) -> SaveTransfer:
    """Hand the raw save JSON to the client (download / device transfer)."""
    slot = _clean_slot(slot)
    if not slot:
        return SaveTransfer(ok=False, error="Empty slot name")
    path = session._get_saves_dir() / f"{slot}.json"  # noqa: SLF001
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return SaveTransfer(ok=False, error=f"No save in slot '{slot}'")
    except (OSError, ValueError) as e:
        return SaveTransfer(ok=False, error=f"Could not read save: {e}")
    return SaveTransfer(ok=True, slot=slot, data=data)


def import_save(
    session: GameSession, slot: str, data: dict,
) -> StatePayload:
    """Validate an uploaded save and write it into the saves dir.

    The run is fully validated before anything touches disk, so a bad
    file can't leave a corrupt slot behind.
    """
    slot = _clean_slot(slot) or "imported"
    if not isinstance(data, dict) or "run" not in data:
        return build_state_payload(
            session, error="Not a Heresiarch save (missing 'run')",
        )
    try:
        RunState.model_validate(data["run"])
    except Exception as e:  # noqa: BLE001 — pydantic error variety
        return build_state_payload(
            session, error=f"Save failed validation: {str(e)[:200]}",
        )
    path = session._get_saves_dir() / f"{slot}.json"  # noqa: SLF001
    try:
        path.write_text(json.dumps(data, indent=2, default=str))
    except OSError as e:
        return build_state_payload(session, error=f"Could not write save: {e}")
    return build_state_payload(
        session, text=f"Imported save into slot '{slot}'.",
    )


def dispatch_preview(
    session: GameSession,
    character_id: str,
    item_id: str,
    slot: str | None = None,
) -> EquipPreview:
    """Equip stat-diff preview; errors become preview.error."""
    try:
        return build_equip_preview(session, character_id, item_id, slot)
    except Exception as e:  # noqa: BLE001 — report, don't crash the frontend
        traceback.print_exc()
        return EquipPreview(
            ok=False, error=f"Internal error: {type(e).__name__}: {e}",
        )
