"""Core stat types: StatBlock, GrowthVector, StatType enum."""

from enum import Enum

from pydantic import BaseModel


class StatType(str, Enum):
    STR = "STR"
    MAG = "MAG"
    DEF = "DEF"
    RES = "RES"
    SPD = "SPD"


class StatBlock(BaseModel):
    """Concrete stat values for a character or enemy at a point in time."""

    STR: int = 0
    MAG: int = 0
    DEF: int = 0
    RES: int = 0
    SPD: int = 0

    def get(self, stat: StatType) -> int:
        return getattr(self, stat.value)

    def with_modifier(self, stat: StatType, amount: int) -> "StatBlock":
        """Return a new StatBlock with one stat modified."""
        data = self.model_dump()
        data[stat.value] += amount
        return StatBlock(**data)


class GrowthVector(BaseModel):
    """Per-level stat growth. Values are the BONUS on top of universal base floor (1/level)."""

    STR: int = 0
    MAG: int = 0
    DEF: int = 0
    RES: int = 0
    SPD: int = 0

    @property
    def budget(self) -> int:
        return self.STR + self.MAG + self.DEF + self.RES + self.SPD

    def effective_growth(self, stat: StatType) -> int:
        """Total per-level growth including the universal base floor of 1."""
        return getattr(self, stat.value) + 1
