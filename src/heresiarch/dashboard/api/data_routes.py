"""Data endpoints: reference data for dropdowns/pickers."""

from __future__ import annotations

from fastapi import APIRouter, Request

from heresiarch.dashboard.core.response_models import (
    AbilitySummary,
    EnemySummary,
    ItemSummary,
    JobSummary,
    ZoneSummary,
)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/jobs")
def list_jobs(request: Request) -> dict[str, JobSummary]:
    gd = request.app.state.game_data
    return {
        jid: JobSummary(
            id=j.id, name=j.name, origin=j.origin,
            growth=j.growth.model_dump(),
            base_hp=j.base_hp, hp_growth=j.hp_growth,
            innate_ability_id=j.innate_ability_id,
            description=j.description,
        )
        for jid, j in gd.jobs.items()
    }


@router.get("/items")
def list_items(request: Request) -> dict[str, ItemSummary]:
    gd = request.app.state.game_data
    return {
        iid: ItemSummary(
            id=i.id, name=i.name, slot=i.display_type,
            scaling_type=i.scaling.scaling_type.value if i.scaling else None,
            scaling_stat=i.scaling.stat.value if i.scaling else None,
            has_conversion=i.conversion is not None,
            base_price=i.base_price,
            description=i.description,
        )
        for iid, i in gd.items.items()
    }


@router.get("/abilities")
def list_abilities(request: Request) -> dict[str, AbilitySummary]:
    gd = request.app.state.game_data
    result: dict[str, AbilitySummary] = {}
    for aid, a in gd.abilities.items():
        quality = None
        for eff in a.effects:
            if eff.quality.value != "NONE":
                quality = eff.quality.value
                break
        result[aid] = AbilitySummary(
            id=a.id, name=a.name, category=a.category.value,
            target=a.target.value, quality=quality, description=a.description,
        )
    return result


@router.get("/enemies")
def list_enemies(request: Request) -> dict[str, EnemySummary]:
    gd = request.app.state.game_data
    return {
        eid: EnemySummary(
            id=e.id, name=e.name, archetype=e.archetype.value,
            budget_multiplier=e.budget_multiplier, description=e.description,
        )
        for eid, e in gd.enemies.items()
    }


@router.get("/zones")
def list_zones(request: Request) -> dict[str, ZoneSummary]:
    gd = request.app.state.game_data
    return {
        zid: ZoneSummary(
            id=z.id, name=z.name, zone_level=z.zone_level, region=z.region,
            encounter_count=len(z.encounters),
            shop_item_count=0,  # shops are now per-town, not per-zone
        )
        for zid, z in gd.zones.items()
    }
