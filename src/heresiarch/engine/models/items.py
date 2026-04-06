"""Item models: equipment, scaling curves, converters."""

from enum import Enum

from pydantic import BaseModel, Field

from .stats import StatType


class EquipSlot(str, Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    ACCESSORY_1 = "ACCESSORY_1"
    ACCESSORY_2 = "ACCESSORY_2"


class ScalingType(str, Enum):
    LINEAR = "LINEAR"
    SUPERLINEAR = "SUPERLINEAR"
    QUADRATIC = "QUADRATIC"
    DEGENERATE = "DEGENERATE"
    FLAT = "FLAT"


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


class Item(BaseModel):
    id: str
    name: str
    slot: EquipSlot
    scaling: ItemScaling | None = None
    conversion: ConversionEffect | None = None
    granted_ability_id: str | None = None
    flat_stat_bonus: dict[str, int] = Field(default_factory=dict)
    hp_bonus: int = 0
    extra_def_reduction: float = 0.0
    leech_percent: float = 0.0
    base_price: int = 0
    is_consumable: bool = False
    heal_amount: int = 0
    heal_percent: float = 0.0
    description: str = ""
