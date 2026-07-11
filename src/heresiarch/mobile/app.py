"""FastAPI app for the mobile sniff test.

One GameSession, one player (the designer's phone on the LAN).
POST /api/action dispatches {tool, args} through a whitelist to
GameSession methods; every response is a full StatePayload so the
client is a dumb renderer. AgentError surfaces as payload.error,
never a 500.
"""

from __future__ import annotations

import threading
import traceback
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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

_STATIC_DIR = Path(__file__).parent / "static"


class ActionRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


class PreviewRequest(BaseModel):
    character_id: str
    item_id: str
    slot: str | None = None


def create_app(
    data_path: Path | None = None, notes_path: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Heresiarch Mobile", docs_url=None, redoc_url=None)

    if notes_path is None:
        # Own namespace: the MCP agent server uses the repo-root
        # agent_notes.json / agent_saves/ — mobile play must not
        # share (or clobber) those slots.
        notes_path = Path("artifacts/mobile/agent_notes.json")
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    session = GameSession(data_path=data_path, notes_path=notes_path)
    # One session, threadpool endpoints: serialize dispatch so a double-tap
    # can't interleave two half-applied actions.
    lock = threading.Lock()

    app.state.session = session

    @app.get("/api/state", response_model=StatePayload)
    def get_current_state() -> StatePayload:
        with lock:
            text = ""
            if session.run is not None:
                try:
                    text = session.get_state()
                except AgentError:
                    text = ""
            return build_state_payload(session, text=text)

    @app.post("/api/action", response_model=StatePayload)
    def post_action(req: ActionRequest) -> StatePayload:
        with lock:
            if req.tool not in ALLOWED_TOOLS:
                return build_state_payload(
                    session, error=f"Unknown tool: {req.tool!r}",
                )
            method = getattr(session, req.tool, None)
            if method is None:
                return build_state_payload(
                    session, error=f"Tool not available: {req.tool!r}",
                )
            try:
                text = method(**req.args)
            except AgentError as e:
                return build_state_payload(session, error=str(e))
            except TypeError as e:
                # Bad/missing kwargs from the client
                return build_state_payload(session, error=f"Bad arguments: {e}")
            except Exception as e:  # noqa: BLE001 — spike: report, don't 500
                traceback.print_exc()
                return build_state_payload(
                    session, error=f"Internal error: {type(e).__name__}: {e}",
                )
            return build_state_payload(session, text=text)

    @app.post("/api/preview_equip", response_model=EquipPreview)
    def preview_equip(req: PreviewRequest) -> EquipPreview:
        with lock:
            try:
                return build_equip_preview(
                    session, req.character_id, req.item_id, req.slot,
                )
            except Exception as e:  # noqa: BLE001 — spike: report, don't 500
                traceback.print_exc()
                return EquipPreview(
                    ok=False, error=f"Internal error: {type(e).__name__}: {e}",
                )

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(
            _STATIC_DIR / "index.html",
            headers={"Cache-Control": "no-store"},
        )

    return app
