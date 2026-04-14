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
    ON_NON_DAMAGE_ACTION = "ON_NON_DAMAGE_ACTION"
    ON_TURN_START = "ON_TURN_START"  # fires at start of combatant's turn (regen, etc.)


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

    # Gold steal (Pilfer etc.) — amount = gold_steal_flat + gold_steal_per_level * user level
    gold_steal_flat: int = 0
    gold_steal_per_level: float = 0.0

    # Thorns: reflect this percentage of damage taken back to attacker
    reflect_percent: float = 0.0

    # When True, this effect applies to the actor instead of the target.
    # Used for "attack + self-buff" abilities like Brace Strike.
    applies_to_self: bool = False

    # Behavioral flags — replace hardcoded ability ID checks in combat.py
    survive_lethal: bool = False   # Survive one lethal hit at 1 HP (once per fight)
    applies_taunt: bool = False    # Forces target to attack this combatant next round
    applies_mark: bool = False     # Marks target for bonus damage from all sources
    ap_refund: int = 0             # Refund this many AP on trigger (e.g., momentum)
    ap_gain: int = 0               # Grant this many AP to the actor (capped at bank max)
    grants_surviving: bool = False  # Set actor's surviving stance (halves incoming damage)

    # Regen: heal this % of missing HP per trigger (ON_TURN_START)
    regen_missing_hp_percent: float = 0.0

    # Summon: spawn enemies mid-combat (boss summon abilities)
    summon_template_id: str = ""     # enemy template to summon
    summon_count: int = 0            # how many to summon
    summon_level_offset: int = 0     # level relative to summoner (0 = same level)

    # Invulnerability: reduce all incoming damage to 0 for N turns
    grants_invulnerable: int = 0     # number of turns of invulnerability to grant

    # Split (mitosis): on lethal damage, spawn these enemies instead of dying.
    # Each entry is a template_id; duplicates spawn multiple copies.
    split_into_templates: list[str] = Field(default_factory=list)


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
    insight_amplified: bool = False
    priority: bool = False
    description: str = ""
    windup_turns: int = 0  # 0 = instant. N = telegraph for N turns, fire on turn N+1
