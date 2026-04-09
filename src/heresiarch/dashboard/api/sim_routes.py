"""Simulation endpoints: one POST per sim type, returns JSON."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from heresiarch.engine.models.items import ItemScaling, ScalingType
from heresiarch.engine.models.stats import StatType

from heresiarch.dashboard.core.config_manager import apply_formula_config
from heresiarch.dashboard.core.config_model import FormulaConfig
from heresiarch.dashboard.core import sim_service
from heresiarch.dashboard.core.response_models import (
    AbilityCompareResult,
    AbilityDprResult,
    BuildCompareResult,
    ConverterCompareResult,
    CrossoverResult,
    EconomyResult,
    EnemyStatsResult,
    JobCurveResult,
    ProgressionResult,
    ShopPricingResult,
    SigmoidResult,
    WeaponSweepResult,
    XpCurveResult,
)

router = APIRouter(prefix="/sim", tags=["sim"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class HypoWeapon(BaseModel):
    name: str
    scaling_type: str
    stat: str = "STR"
    base: float = 0.0
    linear_coeff: float = 0.0
    quadratic_coeff: float = 0.0
    constant_offset: float = 0.0


class WeaponSweepRequest(BaseModel):
    job_id: str = "einherjar"
    stat: str = "STR"
    levels: list[int] | None = None
    hypo_weapons: list[HypoWeapon] | None = None
    formula_overrides: FormulaConfig | None = None


class CrossoverRequest(BaseModel):
    job_id: str = "einherjar"
    stat: str = "STR"
    hypo_weapons: list[HypoWeapon] | None = None
    formula_overrides: FormulaConfig | None = None


class BuildCompareRequest(BaseModel):
    job_id: str = "berserker"
    level: int = 50
    builds: dict[str, list[str]] | None = None
    enemy_id: str | None = None
    zone_level: int | None = None
    formula_overrides: FormulaConfig | None = None


class ConverterRequest(BaseModel):
    job_id: str = "martyr"
    converter_id: str = "fortress_ring"
    levels: list[int] | None = None
    formula_overrides: FormulaConfig | None = None


class SigmoidRequest(BaseModel):
    max_output: float
    midpoint: float
    rate: float
    stat_values: list[int] | None = None
    formula_overrides: FormulaConfig | None = None


class AbilityDprRequest(BaseModel):
    job_id: str = "einherjar"
    ability_ids: list[str] | None = None
    levels: list[int] | None = None
    enemy_def: int = 50
    formula_overrides: FormulaConfig | None = None


class AbilityCompareRequest(BaseModel):
    job_id: str = "einherjar"
    ability_ids: list[str]
    levels: list[int] | None = None
    enemy_def: int = 50
    formula_overrides: FormulaConfig | None = None


class JobCurveRequest(BaseModel):
    job_id: str = "einherjar"
    enemy_def: int = 50
    formula_overrides: FormulaConfig | None = None


class EconomyRequest(BaseModel):
    formula_overrides: FormulaConfig | None = None


class XpCurveRequest(BaseModel):
    job_id: str = "einherjar"
    formula_overrides: FormulaConfig | None = None


class EnemyStatsRequest(BaseModel):
    enemy_ids: list[str] | None = None
    formula_overrides: FormulaConfig | None = None


class ShopPricingRequest(BaseModel):
    potions_only: bool = False
    formula_overrides: FormulaConfig | None = None


class ProgressionRequest(BaseModel):
    job_id: str = "einherjar"
    formula_overrides: FormulaConfig | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_config(request: Request, overrides: FormulaConfig | None) -> FormulaConfig:
    """Merge session config with per-request overrides."""
    base: FormulaConfig = request.app.state.formula_config
    if overrides is None:
        return base
    # Per-request overrides replace session values
    return overrides


def _get_weapons(request: Request, stat: str, hypos: list[HypoWeapon] | None) -> dict[str, ItemScaling]:
    gd = request.app.state.game_data
    target = StatType(stat.upper())
    weapons: dict[str, ItemScaling] = {}
    for item in gd.items.values():
        if item.scaling and item.scaling.stat == target:
            weapons[item.name] = item.scaling
    if hypos:
        for h in hypos:
            weapons[h.name] = ItemScaling(
                scaling_type=ScalingType(h.scaling_type),
                stat=StatType(h.stat),
                base=h.base,
                linear_coeff=h.linear_coeff,
                quadratic_coeff=h.quadratic_coeff,
                constant_offset=h.constant_offset,
            )
    return weapons


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/weapon-sweep")
def weapon_sweep(request: Request, body: WeaponSweepRequest) -> WeaponSweepResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    job = gd.jobs[body.job_id]
    stat = body.stat.upper()
    rate = job.growth.effective_growth(StatType(stat))
    weapons = _get_weapons(request, stat, body.hypo_weapons)
    with apply_formula_config(cfg):
        return sim_service.weapon_sweep_data(body.job_id, stat, rate, weapons, body.levels)


@router.post("/crossovers")
def crossovers(request: Request, body: CrossoverRequest) -> CrossoverResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    job = gd.jobs[body.job_id]
    stat = body.stat.upper()
    rate = job.growth.effective_growth(StatType(stat))
    weapons = _get_weapons(request, stat, body.hypo_weapons)
    with apply_formula_config(cfg):
        return sim_service.find_crossovers_data(body.job_id, stat, rate, weapons)


@router.post("/build-compare")
def build_compare(request: Request, body: BuildCompareRequest) -> BuildCompareResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.build_compare_data(
            gd, body.job_id, body.level, body.builds,
            body.enemy_id, body.zone_level,
        )


@router.post("/converter")
def converter(request: Request, body: ConverterRequest) -> ConverterCompareResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.converter_compare_data(gd, body.job_id, body.converter_id, body.levels)


@router.post("/sigmoid")
def sigmoid(request: Request, body: SigmoidRequest) -> SigmoidResult:
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.sigmoid_explorer_data(body.max_output, body.midpoint, body.rate, body.stat_values)


@router.post("/ability-dpr")
def ability_dpr(request: Request, body: AbilityDprRequest) -> AbilityDprResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.ability_dpr_data(gd, body.job_id, body.ability_ids, body.levels, body.enemy_def)


@router.post("/ability-compare")
def ability_compare(request: Request, body: AbilityCompareRequest) -> AbilityCompareResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.ability_compare_data(gd, body.job_id, body.ability_ids, body.levels, body.enemy_def)


@router.post("/job-curve")
def job_curve(request: Request, body: JobCurveRequest) -> JobCurveResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.job_ability_curve_data(gd, body.job_id, body.enemy_def)


@router.post("/economy")
def economy(request: Request, body: EconomyRequest) -> EconomyResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.economy_data(gd)


@router.post("/xp-curve")
def xp_curve(request: Request, body: XpCurveRequest) -> XpCurveResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.xp_curve_data(gd, body.job_id)


@router.post("/enemy-stats")
def enemy_stats(request: Request, body: EnemyStatsRequest) -> EnemyStatsResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.enemy_stats_data(gd, body.enemy_ids)


@router.post("/shop-pricing")
def shop_pricing(request: Request, body: ShopPricingRequest) -> ShopPricingResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.shop_pricing_data(gd, body.potions_only)


@router.post("/progression")
def progression(request: Request, body: ProgressionRequest) -> ProgressionResult:
    gd = request.app.state.game_data
    cfg = _get_config(request, body.formula_overrides)
    with apply_formula_config(cfg):
        return sim_service.progression_data(gd, body.job_id)
