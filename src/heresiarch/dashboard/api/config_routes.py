"""Config endpoints: get/set/save/reset formula constants."""

from __future__ import annotations

from fastapi import APIRouter, Request

from heresiarch.dashboard.core.config_manager import save_config
from heresiarch.dashboard.core.config_model import FormulaConfig

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/formulas")
def get_formulas(request: Request) -> FormulaConfig:
    return request.app.state.formula_config


@router.put("/formulas")
def update_formulas(request: Request, cfg: FormulaConfig) -> FormulaConfig:
    request.app.state.formula_config = cfg
    return cfg


@router.post("/formulas/save")
def save_formulas(request: Request) -> dict[str, str]:
    cfg = request.app.state.formula_config
    save_config(cfg, request.app.state.overrides_path)
    return {"status": "saved", "path": str(request.app.state.overrides_path)}


@router.post("/formulas/reset")
def reset_formulas(request: Request) -> FormulaConfig:
    cfg = FormulaConfig()
    request.app.state.formula_config = cfg
    # Delete the overrides file if it exists
    path = request.app.state.overrides_path
    if path.exists():
        path.unlink()
    return cfg
