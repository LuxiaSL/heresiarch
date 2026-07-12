"""FastAPI app for the mobile frontend (LAN transport).

One GameSession, one player (the designer's phone on the LAN).
All behavior lives in dispatch.py — this file only adds HTTP, a
lock, and static-asset routes. The Pyodide wasm page drives the same
dispatch functions with no server at all.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from heresiarch.agent.session import GameSession
from heresiarch.mobile.dispatch import (
    current_state,
    dispatch_action,
    dispatch_preview,
)
from heresiarch.mobile.views import EquipPreview, StatePayload

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
            return current_state(session)

    @app.post("/api/action", response_model=StatePayload)
    def post_action(req: ActionRequest) -> StatePayload:
        with lock:
            return dispatch_action(session, req.tool, req.args)

    @app.post("/api/preview_equip", response_model=EquipPreview)
    def preview_equip(req: PreviewRequest) -> EquipPreview:
        with lock:
            return dispatch_preview(
                session, req.character_id, req.item_id, req.slot,
            )

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(
            _STATIC_DIR / "index.html",
            headers={"Cache-Control": "no-store"},
        )

    # --- PWA shell (manifest / service worker / icons) ---

    @app.get("/manifest.webmanifest")
    def manifest() -> FileResponse:
        return FileResponse(
            _STATIC_DIR / "manifest.webmanifest",
            media_type="application/manifest+json",
        )

    @app.get("/sw.js")
    def service_worker() -> FileResponse:
        # no-store so a new SW version is picked up on next launch
        return FileResponse(
            _STATIC_DIR / "sw.js",
            media_type="text/javascript",
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/icons/{name}")
    def icon(name: str) -> FileResponse:
        path = _STATIC_DIR / "icons" / name
        # resolve() guards traversal; icons dir only holds PNGs
        if (
            not path.resolve().is_relative_to((_STATIC_DIR / "icons").resolve())
            or path.suffix != ".png"
            or not path.is_file()
        ):
            raise HTTPException(status_code=404)
        return FileResponse(path, media_type="image/png")

    return app
