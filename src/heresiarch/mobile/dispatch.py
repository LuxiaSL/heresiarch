"""Framework-free action dispatch over GameSession.

This is the whole behavior of the mobile frontend, minus HTTP: a
whitelist of session methods, error-to-payload conversion, and the
StatePayload build. The FastAPI LAN server (app.py) and the Pyodide
engine-in-wasm page (spikes/pyodide) both drive these exact functions,
so the two transports cannot drift.
"""

from __future__ import annotations

import traceback
from typing import Any

from heresiarch.agent.session import AgentError, GameSession
from heresiarch.mobile.views import (
    EquipPreview,
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
    "fight", "submit_decisions", "auto_battle_round", "get_combat_state",
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
