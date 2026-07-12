"""In-wasm bootstrap: one GameSession + the HTTP-shaped handle.

Executed by boot.js after the engine wheel and data are unpacked.
hx_handle(path, body_json) mirrors the FastAPI routes exactly — the
client cannot tell the transports apart. Runs identically under the
Node verifier (spikes/pyodide/verify_node.mjs).
"""

import json
from pathlib import Path

from heresiarch.agent.session import GameSession
from heresiarch.mobile import dispatch as _D

_session = GameSession(
    data_path=Path("/data"),
    notes_path=Path("/persist/agent_notes.json"),
)


def hx_handle(path: str, body_json: str) -> str:
    body = json.loads(body_json) if body_json else {}
    if path == "/api/state":
        return _D.current_state(_session).model_dump_json()
    if path == "/api/action":
        return _D.dispatch_action(
            _session, body.get("tool", ""), body.get("args") or {},
        ).model_dump_json()
    if path == "/api/preview_equip":
        return _D.dispatch_preview(
            _session,
            body.get("character_id", ""),
            body.get("item_id", ""),
            body.get("slot"),
        ).model_dump_json()
    # Unknown path → the dispatcher's own "Unknown tool" error payload
    return _D.dispatch_action(_session, "", {}).model_dump_json()
