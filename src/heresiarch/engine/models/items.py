"""Item models: equipment, scaling curves, converters."""

from enum import Enum

from pydantic import BaseModel, Field

from .stats import StatType


class EquipType(str, Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    ACCESSORY = "ACCESSORY"


class ScalingType(str, Enum):
    LINEAR = "LINEAR"
    SUPERLINEAR = "SUPERLINEAR"
    QUADRATIC = "QUADRATIC"
    DEGENERATE = "DEGENERATE"
    FLAT = "FLAT"
    SIGMOID = "SIGMOID"


class ItemScaling(BaseModel):
    """Defines how an item's primary effect scales with a stat."""

    scaling_type: ScalingType
    stat: StatType
    base: float = 0.0
    linear_coeff: float = 0.0
    quadratic_coeff: float = 0.0
    constant_offset: float = 0.0


class ConversionEffect(BaseModel):
    """For converter items: source stat -> target stat bonus."""

    source_stat: StatType
    target_stat: StatType
    scaling_type: ScalingType
    linear_coeff: float = 0.0
    quadratic_coeff: float = 0.0
    # Sigmoid parameters: output = sigmoid_max / (1 + exp(-sigmoid_rate * (stat - sigmoid_mid)))
    sigmoid_max: float = 0.0
    sigmoid_mid: float = 0.0
    sigmoid_rate: float = 0.0


class Item(BaseModel):
    id: str
    name: str
    equip_type: EquipType | None = None  # None = not equippable (consumable)
    loot_category: str = ""  # grouping tag for loot pools
    tier: int = 1  # Power tier for rarity weighting (1=common, 2=mid, 3=endgame)
    scaling: ItemScaling | None = None
    conversion: ConversionEffect | None = None
    granted_ability_id: str | None = None
    flat_stat_bonus: dict[str, int] = Field(default_factory=dict)
    hp_bonus: int = 0
    extra_def_reduction: float = 0.0
    phys_leech_percent: float = 0.0
    mag_leech_percent: float = 0.0
    base_price: int = 0
    is_consumable: bool = False
    heal_amount: int = 0
    heal_percent: float = 0.0
    # Scroll fields
    teaches_ability_id: str | None = None  # Permanent teach scroll: consumed, grants ability forever
    casts_ability_id: str | None = None  # One-time cast scroll: consumed, performs ability once
    # Stat tonic: grants a combat-duration stat buff when consumed
    combat_stat_buff: dict[str, int] = Field(default_factory=dict)
    description: str = ""

    @property
    def display_type(self) -> str:
        """Human-readable type for TUI/agent display."""
        if self.equip_type:
            return self.equip_type.value.title()
        _display = {
            "potion": "Potion",
            "tonic": "Tonic",
            "teach_scroll": "Scroll (Teach)",
            "cast_scroll": "Scroll (Cast)",
        }
        return _display.get(self.loot_category, "Consumable")
