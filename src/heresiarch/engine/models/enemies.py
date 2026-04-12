"""Enemy models: archetypes, action tables, instances."""

from enum import Enum

from pydantic import BaseModel, Field

from .stats import StatBlock


class EnemyArchetype(str, Enum):
    FODDER = "FODDER"
    BRUTE = "BRUTE"
    CASTER = "CASTER"
    SPEEDER = "SPEEDER"
    SUPPORT = "SUPPORT"
    BOSS = "BOSS"


class RepeatMode(str, Enum):
    CONSECUTIVE = "consecutive"  # count only unbroken streak from most recent
    TOTAL = "total"  # count all uses in entire fight


class ActionWeight(BaseModel):
    ability_id: str
    weight: float
    repeat_penalty: float = 0.0  # 0.0 = no penalty, 0.9 = weight * 0.1 per use
    repeat_mode: RepeatMode = RepeatMode.CONSECUTIVE
    recency_bonus: float = 0.0  # weight * (1 + bonus)^rounds_since_last_use


class ActionCondition(BaseModel):
    """A conditional modifier to action weights.

    When the condition is met, weight_overrides replace the base weights.
    Conditions are evaluated in order; last matching condition wins.
    """

    condition_type: str
    threshold: float = 0.0
    ally_archetype: str | None = None
    weight_overrides: list[ActionWeight] = Field(default_factory=list)


class ActionTable(BaseModel):
    """AI behavior definition for an enemy."""

    base_weights: list[ActionWeight]
    conditions: list[ActionCondition] = Field(default_factory=list)


class EnemyTemplate(BaseModel):
    """Static enemy definition. Scaled at runtime to enemy level."""

    id: str
    name: str
    archetype: EnemyArchetype
    budget_multiplier: float
    stat_distribution: dict[str, float]
    base_hp: int
    hp_per_budget: float
    action_table: ActionTable
    abilities: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    target_preference: str = "random"
    description: str = ""
    gold_multiplier: float | None = None  # override budget_multiplier for gold calc
    xp_multiplier: float | None = None    # override budget_multiplier for XP calc
    death_spawn_template_id: str = ""     # on death, spawn N copies of this template
    death_spawn_count: int = 0            # how many to spawn on death
    death_spawn_templates: list[str] = Field(default_factory=list)  # on death, spawn one of each


class EnemyInstance(BaseModel):
    """A concrete enemy in combat, scaled to an enemy level."""

    template_id: str
    name: str
    level: int
    stats: StatBlock
    max_hp: int
    current_hp: int
    abilities: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    action_table: ActionTable
    target_preference: str = "random"
    budget_multiplier: float = 0.0       # preserved for XP/gold calc
    gold_multiplier: float | None = None  # override for gold calc
    xp_multiplier: float | None = None    # override for XP calc
