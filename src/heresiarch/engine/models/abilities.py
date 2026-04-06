"""Ability models: effects, damage qualities, triggers."""

from enum import Enum

from pydantic import BaseModel, Field

from .stats import StatType


class DamageQuality(str, Enum):
    NONE = "NONE"
    DOT = "DOT"
    SHATTER = "SHATTER"
    CHAIN = "CHAIN"
    PIERCE = "PIERCE"
    DISRUPT = "DISRUPT"
    LEECH = "LEECH"
    SURGE = "SURGE"


class TargetType(str, Enum):
    SINGLE_ENEMY = "SINGLE_ENEMY"
    ALL_ENEMIES = "ALL_ENEMIES"
    SELF = "SELF"
    SINGLE_ALLY = "SINGLE_ALLY"
    ALL_ALLIES = "ALL_ALLIES"


class AbilityCategory(str, Enum):
    OFFENSIVE = "OFFENSIVE"
    DEFENSIVE = "DEFENSIVE"
    SUPPORT = "SUPPORT"
    PASSIVE = "PASSIVE"


class TriggerCondition(str, Enum):
    """For passive abilities: when do they fire?"""

    NONE = "NONE"
    ON_HIT_RECEIVED = "ON_HIT_RECEIVED"
    ON_KILL = "ON_KILL"
    ON_ALLY_KO = "ON_ALLY_KO"
    HP_BELOW_THRESHOLD = "HP_BELOW_THRESHOLD"
    RES_GATE_PASSED = "RES_GATE_PASSED"
    ON_CONSECUTIVE_ATTACK = "ON_CONSECUTIVE_ATTACK"


class AbilityEffect(BaseModel):
    """Describes one mechanical effect of an ability.

    Uses a flat model with zero-default optional fields rather than polymorphic
    hierarchy. Practical for YAML serialization and multi-effect abilities.
    """

    quality: DamageQuality = DamageQuality.NONE
    base_damage: int = 0
    stat_scaling: StatType | None = None
    scaling_coefficient: float = 0.0
    duration_rounds: int = 0

    # Quality-specific parameters
    pierce_percent: float = 0.0
    chain_damage_ratio: float = 1.0
    leech_percent: float = 0.0
    shatter_amount: float = 0.0
    disrupt_weight_shift: dict[str, float] = Field(default_factory=dict)
    surge_stack_bonus: float = 0.0

    # Misc effect parameters
    self_damage_ratio: float = 0.0
    def_buff: int = 0
    heal_percent: float = 0.0
    stat_buff: dict[str, int] = Field(default_factory=dict)


class Ability(BaseModel):
    id: str
    name: str
    category: AbilityCategory
    target: TargetType
    effects: list[AbilityEffect] = Field(default_factory=list)
    cooldown: int = 0
    trigger: TriggerCondition = TriggerCondition.NONE
    trigger_threshold: float = 0.0
    is_innate: bool = False
    is_partial_action: bool = False
    description: str = ""
