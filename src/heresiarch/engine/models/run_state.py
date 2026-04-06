"""Run state: complete state of a single roguelike run."""

from pydantic import BaseModel, Field

from .party import Party
from .zone import ZoneState


class CombatResult(BaseModel):
    """Summary of a completed combat encounter, for post-combat processing."""

    player_won: bool
    surviving_character_ids: list[str] = Field(default_factory=list)
    surviving_character_hp: dict[str, int] = Field(default_factory=dict)
    defeated_enemy_template_ids: list[str] = Field(default_factory=list)
    defeated_enemy_budget_multipliers: list[float] = Field(default_factory=list)
    rounds_taken: int = 0
    zone_level: int = 0


class RunState(BaseModel):
    """Complete state of a single roguelike run."""

    run_id: str
    party: Party = Field(default_factory=Party)
    current_zone_id: str | None = None
    zone_state: ZoneState | None = None
    zones_completed: list[str] = Field(default_factory=list)
    is_dead: bool = False
    created_at: str = ""
