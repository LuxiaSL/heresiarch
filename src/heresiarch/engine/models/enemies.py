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


class ActionWeight(BaseModel):
    ability_id: str
    weight: float


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
    """Static enemy definition. Scaled at runtime to zone level."""

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


class EnemyInstance(BaseModel):
    """A concrete enemy in combat, scaled to a zone level."""

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
