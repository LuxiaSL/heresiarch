"""FastAPI application for the Heresiarch Balance Dashboard."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from heresiarch.engine.data_loader import load_all
from heresiarch.dashboard.core.config_manager import load_saved_config
from heresiarch.dashboard.api.data_routes import router as data_router
from heresiarch.dashboard.api.config_routes import router as config_router
from heresiarch.dashboard.api.sim_routes import router as sim_router


def _find_data_dir() -> Path:
    """Locate the game data directory."""
    candidates = [
        Path("data"),
        Path(__file__).resolve().parents[4] / "data",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    raise FileNotFoundError(f"Cannot find data/ directory. Tried: {candidates}")


def _find_static_dir() -> Path | None:
    """Locate built frontend static files, if they exist."""
    candidates = [
        Path(__file__).resolve().parents[4] / "frontend" / "dist",
        Path("frontend") / "dist",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load game data and config on startup."""
    data_dir = _find_data_dir()
    app.state.game_data = load_all(data_dir)
    app.state.data_dir = data_dir

    overrides_path = data_dir / "_overrides" / "formulas.json"
    app.state.overrides_path = overrides_path
    app.state.formula_config = load_saved_config(overrides_path)

    print(f"Loaded game data from {data_dir}")
    print(f"  Jobs: {len(app.state.game_data.jobs)}")
    print(f"  Items: {len(app.state.game_data.items)}")
    print(f"  Abilities: {len(app.state.game_data.abilities)}")
    print(f"  Enemies: {len(app.state.game_data.enemies)}")
    print(f"  Zones: {len(app.state.game_data.zones)}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Heresiarch Balance Dashboard",
        description="Interactive balance simulation and tuning tool",
        lifespan=lifespan,
    )

    # CORS for dev mode (Vite dev server on :5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(data_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(sim_router, prefix="/api")

    # Serve built frontend (if available)
    static_dir = _find_static_dir()
    if static_dir:
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")

    return app


app = create_app()
