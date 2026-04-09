"""Pydantic response models for all simulation endpoints."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Weapon sweep / crossover
# ---------------------------------------------------------------------------

class WeaponSweepPoint(BaseModel):
    level: int
    stat_value: int
    outputs: dict[str, float]
    effective: dict[str, int]
    best: str


class WeaponSweepResult(BaseModel):
    job_id: str
    stat: str
    growth_rate: int
    weapon_names: list[str]
    points: list[WeaponSweepPoint]


class CrossoverEvent(BaseModel):
    winner: str
    loser: str
    level: int
    winner_value: float
    loser_value: float


class BreakevenEvent(BaseModel):
    weapon: str
    level: int
    stat_value: int
    output: float


class CrossoverResult(BaseModel):
    job_id: str
    stat: str
    growth_rate: int
    crossovers: list[CrossoverEvent]
    breakevens: list[BreakevenEvent]


# ---------------------------------------------------------------------------
# Build compare
# ---------------------------------------------------------------------------

class BuildSnapshot(BaseModel):
    name: str
    items: list[str]
    stats: dict[str, int]
    hp: int
    bonus_actions: int
    heavy_damage: int | None = None
    bolt_damage: int | None = None
    dpt: int | None = None


class BuildCompareResult(BaseModel):
    job_id: str
    level: int
    builds: list[BuildSnapshot]
    enemy_info: str | None = None


# ---------------------------------------------------------------------------
# Converter compare
# ---------------------------------------------------------------------------

class ConverterPoint(BaseModel):
    level: int
    source_stat: int
    outputs: dict[str, int]


class ConverterCompareResult(BaseModel):
    job_id: str
    converter_id: str
    source_stat: str
    target_stat: str
    growth_rate: int
    points: list[ConverterPoint]


# ---------------------------------------------------------------------------
# Sigmoid explorer
# ---------------------------------------------------------------------------

class SigmoidPoint(BaseModel):
    stat: int
    output: int
    pct_of_max: float


class SigmoidResult(BaseModel):
    max_output: float
    midpoint: float
    rate: float
    points: list[SigmoidPoint]


# ---------------------------------------------------------------------------
# Ability DPR
# ---------------------------------------------------------------------------

class AbilityDprRow(BaseModel):
    ability_id: str
    ability_name: str
    quality: str
    scaling_stat: str
    coefficient: float
    unlock_level: int | str
    damage_by_level: dict[int, int]
    ratio_by_level: dict[int, float]


class SurgeBreakdown(BaseModel):
    ability_name: str
    stack_bonus: float
    data: list[dict[str, int | float]]  # [{level, base, x1, x2, ...}]


class DotBreakdown(BaseModel):
    ability_name: str
    duration: int
    tick_base: int
    data: list[dict[str, int]]  # [{level, hit_dmg, tick, total}]


class PierceBreakdown(BaseModel):
    ability_name: str
    pierce_pct: float
    data: list[dict[str, int | float]]  # [{level, def_25, def_50, ...}]


class ChainBreakdown(BaseModel):
    ability_name: str
    chain_ratio: float
    data: list[dict[str, int]]  # [{level, per_hit, 1T, 2T, 3T, 4T}]


class AbilityDprResult(BaseModel):
    job_id: str
    job_name: str
    enemy_def: int
    levels: list[int]
    rows: list[AbilityDprRow]
    surge_breakdowns: list[SurgeBreakdown] = []
    dot_breakdowns: list[DotBreakdown] = []
    pierce_breakdowns: list[PierceBreakdown] = []
    chain_breakdowns: list[ChainBreakdown] = []


# ---------------------------------------------------------------------------
# Ability compare
# ---------------------------------------------------------------------------

class AbilityComparePoint(BaseModel):
    level: int
    str_val: int
    mag_val: int
    damages: dict[str, int]
    best: str


class AbilityCompareResult(BaseModel):
    job_id: str
    enemy_def: int
    ability_names: list[str]
    points: list[AbilityComparePoint]
    crossovers: list[CrossoverEvent]


# ---------------------------------------------------------------------------
# Job ability curve
# ---------------------------------------------------------------------------

class JobCurveUnlock(BaseModel):
    unlock_level: int
    ability_id: str
    ability_name: str
    category: str
    quality: str
    scaling_stat: str
    damage_at_unlock: int
    basic_attack_at_unlock: int
    ratio_vs_basic: float


class JobCurveResult(BaseModel):
    job_id: str
    job_name: str
    enemy_def: int
    unlocks: list[JobCurveUnlock]
    strongest_unlock: str | None = None
    first_power_spike: str | None = None


# ---------------------------------------------------------------------------
# Economy
# ---------------------------------------------------------------------------

class ZoneEconomySnapshot(BaseModel):
    zone_id: str
    zone_name: str
    zone_level: int
    enemies_total: int
    encounters_total: int
    zone_gold: float
    overstay_max_gold: float
    avg_encounter_gold: float
    cumulative_gold_rush: float
    cumulative_gold_moderate: float
    cumulative_gold_grind: float
    shop_items: list[str]


class PilferImpact(BaseModel):
    zone_id: str
    zone_gold: float
    cumulative_gold: float
    pilfer_per_hit: int
    two_hits: int
    encounter_equivalent: float


class EconomyResult(BaseModel):
    zones: list[ZoneEconomySnapshot]
    pilfer_flat: int = 0
    pilfer_per_level: float = 0.0
    pilfer_impacts: list[PilferImpact] = []


# ---------------------------------------------------------------------------
# XP curve
# ---------------------------------------------------------------------------

class ZoneXpSnapshot(BaseModel):
    zone_id: str
    zone_level: int
    level_at_exit_rush: int
    level_at_exit_moderate: int
    level_at_exit_grind: int
    cumulative_xp_rush: int
    cumulative_xp_moderate: int
    cumulative_xp_grind: int


class XpMilestone(BaseModel):
    target_level: int
    rush_zone: str
    moderate_zone: str
    grind_zone: str


class XpCurveResult(BaseModel):
    job_id: str
    job_name: str
    zones: list[ZoneXpSnapshot]
    milestones: list[XpMilestone]


# ---------------------------------------------------------------------------
# Enemy stats
# ---------------------------------------------------------------------------

class EnemyZoneStats(BaseModel):
    zone_level: int
    hp: int
    base_stats: dict[str, int]
    effective_stats: dict[str, int] | None = None


class EnemyStatsEntry(BaseModel):
    enemy_id: str
    enemy_name: str
    archetype: str
    budget_multiplier: float
    stat_distribution: dict[str, float]
    equipment: list[str]
    zone_stats: list[EnemyZoneStats]


class EnemyStatsResult(BaseModel):
    enemies: list[EnemyStatsEntry]


# ---------------------------------------------------------------------------
# Shop pricing
# ---------------------------------------------------------------------------

class ShopItem(BaseModel):
    item_name: str
    item_id: str
    base_price: int
    buy_price: int
    pct_rush: float | None = None
    pct_moderate: float | None = None
    pct_grind: float | None = None
    affordable: str


class ShopZone(BaseModel):
    zone_name: str
    zone_level: int
    cumulative_gold_rush: float
    cumulative_gold_moderate: float
    cumulative_gold_grind: float
    items: list[ShopItem]


class PotionCheck(BaseModel):
    potion_name: str
    potion_id: str
    base_price: int
    buy_price: int
    intro_zone: str | None = None
    avg_encounter_gold: float | None = None
    ratio: float | None = None
    status: str


class ShopPricingResult(BaseModel):
    zones: list[ShopZone]
    potions: list[PotionCheck]


# ---------------------------------------------------------------------------
# Progression
# ---------------------------------------------------------------------------

class ProgressionZone(BaseModel):
    zone_id: str
    zone_name: str
    zone_level: int
    exit_level_rush: int
    exit_level_moderate: int
    exit_level_grind: int
    cumulative_gold_rush: float
    cumulative_gold_moderate: float
    cumulative_gold_grind: float
    affordable_items: list[str]
    unlocked_abilities: list[str]
    best_weapon: str | None = None
    weapon_outputs: dict[str, float] = {}


class ProgressionResult(BaseModel):
    job_id: str
    job_name: str
    primary_stat: str
    growth_rate: int
    zones: list[ProgressionZone]


# ---------------------------------------------------------------------------
# Data summaries (for dropdowns/pickers)
# ---------------------------------------------------------------------------

class JobSummary(BaseModel):
    id: str
    name: str
    origin: str
    growth: dict[str, int]
    base_hp: int
    hp_growth: int
    innate_ability_id: str
    description: str = ""


class ItemSummary(BaseModel):
    id: str
    name: str
    slot: str
    scaling_type: str | None = None
    scaling_stat: str | None = None
    has_conversion: bool = False
    base_price: int = 0
    description: str = ""


class AbilitySummary(BaseModel):
    id: str
    name: str
    category: str
    target: str
    quality: str | None = None
    description: str = ""


class EnemySummary(BaseModel):
    id: str
    name: str
    archetype: str
    budget_multiplier: float
    description: str = ""


class ZoneSummary(BaseModel):
    id: str
    name: str
    zone_level: int
    region: str
    encounter_count: int
    shop_item_count: int
