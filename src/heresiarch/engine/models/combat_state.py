"""Combat state models: the complete state of a fight, events, statuses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .stats import StatBlock


class CheatSurviveChoice(str, Enum):
    CHEAT = "CHEAT"
    SURVIVE = "SURVIVE"
    NORMAL = "NORMAL"


class StatusEffect(BaseModel):
    id: str
    name: str
    stat_modifiers: dict[str, int] = Field(default_factory=dict)
    damage_per_round: int = 0
    def_reduction: float = 0.0
    rounds_remaining: int = 0
    source_id: str = ""
    grants_taunted: bool = False
    grants_mark: bool = False


class CombatAction(BaseModel):
    """A resolved action in combat."""

    actor_id: str
    ability_id: str = ""
    target_ids: list[str] = Field(default_factory=list)
    item_id: str | None = None  # when set, this is an item use (not an ability)
    is_windup_push: bool = False  # when True, pushes a charging ability forward 1 turn


class PlayerTurnDecision(BaseModel):
    """What a player (or test harness) chooses for one character's turn."""

    combatant_id: str
    cheat_survive: CheatSurviveChoice = CheatSurviveChoice.NORMAL
    cheat_actions: int = 0
    primary_action: CombatAction | None = None
    cheat_extra_actions: list[CombatAction] = Field(default_factory=list)
    bonus_actions: list[CombatAction] = Field(default_factory=list)


class CombatEventType(str, Enum):
    ROUND_START = "ROUND_START"
    TURN_START = "TURN_START"
    CHEAT_SURVIVE_DECISION = "CHEAT_SURVIVE_DECISION"
    ACTION_DECLARED = "ACTION_DECLARED"
    DAMAGE_DEALT = "DAMAGE_DEALT"
    HEALING = "HEALING"
    STATUS_APPLIED = "STATUS_APPLIED"
    STATUS_EXPIRED = "STATUS_EXPIRED"
    STATUS_RESISTED = "STATUS_RESISTED"
    DOT_TICK = "DOT_TICK"
    DEATH = "DEATH"
    BONUS_ACTION = "BONUS_ACTION"
    RETALIATE_TRIGGERED = "RETALIATE_TRIGGERED"
    PASSIVE_TRIGGERED = "PASSIVE_TRIGGERED"
    TAUNT_REDIRECT = "TAUNT_REDIRECT"
    FRENZY_STACK = "FRENZY_STACK"
    INSIGHT_CONSUMED = "INSIGHT_CONSUMED"
    THORNS_TRIGGERED = "THORNS_TRIGGERED"
    GOLD_STOLEN = "GOLD_STOLEN"
    COMBAT_END = "COMBAT_END"
    CHARGE_START = "CHARGE_START"        # "X is winding up!"
    CHARGE_CONTINUE = "CHARGE_CONTINUE"  # "X is still charging..."
    CHARGE_RELEASE = "CHARGE_RELEASE"    # "X unleashes [ability]!"
    ENEMY_SUMMONED = "ENEMY_SUMMONED"    # boss summons adds via ability
    ENEMY_SPAWNED = "ENEMY_SPAWNED"      # split-on-death or similar spawn
    ITEM_USED = "ITEM_USED"              # consumable item used in combat


class CombatEvent(BaseModel):
    event_type: CombatEventType
    round_number: int = 0
    actor_id: str = ""
    target_id: str = ""
    ability_id: str = ""
    value: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class CombatantState(BaseModel):
    """Per-combatant state within a fight."""

    id: str
    is_player: bool
    current_hp: int
    max_hp: int
    base_stats: StatBlock
    equipment_stats: StatBlock  # base + equipment (Layer 1-4, no combat buffs)
    effective_stats: StatBlock  # equipment_stats + combat buffs
    ability_ids: list[str] = Field(default_factory=list)
    action_points: int = 0
    cheat_debt: int = 0
    active_statuses: list[StatusEffect] = Field(default_factory=list)
    taunted_by: list[str] = Field(default_factory=list)
    is_alive: bool = True
    cooldowns: dict[str, int] = Field(default_factory=dict)
    frenzy_stacks: int = 0  # per-round attack count (used by surge, reset each round)
    frenzy_level: float = 1.0  # persistent frenzy multiplier (ratchet: never decreases)
    frenzy_chain: int = 0  # consecutive hit count, resets on non-damage round
    surge_stacks: dict[str, int] = Field(default_factory=dict)
    is_surviving: bool = False
    insight_stacks: int = 0  # onmyoji: empowers next ability cast per stack
    dealt_damage_this_round: bool = False  # tracks whether combatant dealt damage
    phys_leech_percent: float = 0.0
    mag_leech_percent: float = 0.0
    extra_def_reduction: float = 0.0  # bonus DEF reduction ratio from equipment
    level: int = 1
    has_endured: bool = False  # True once Endure has been consumed this fight
    is_marked: bool = False  # Mark: bonus damage from all attackers
    pending_action: CombatAction | None = None  # pre-rolled enemy intent
    charging_ability_id: str | None = None     # ability being charged (windup)
    charging_target_ids: list[str] = Field(default_factory=list)  # pre-selected targets
    charge_turns_remaining: int = 0            # turns left before firing
    invulnerable_turns: int = 0                # while > 0, all damage reduced to 0


class CombatState(BaseModel):
    """The complete state of an ongoing combat encounter."""

    round_number: int = 0
    player_combatants: list[CombatantState] = Field(default_factory=list)
    enemy_combatants: list[CombatantState] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)
    current_turn_index: int = 0
    log: list[CombatEvent] = Field(default_factory=list)
    is_finished: bool = False
    player_won: bool | None = None
    consumed_items: list[str] = Field(default_factory=list)  # item IDs used this round
    foresight_revealed: list[str] = Field(default_factory=list)
    gold_stolen_by_enemies: int = 0
    gold_stolen_by_players: int = 0

    def get_combatant(self, combatant_id: str) -> CombatantState | None:
        for c in self.player_combatants + self.enemy_combatants:
            if c.id == combatant_id:
                return c
        return None

    @property
    def all_combatants(self) -> list[CombatantState]:
        return self.player_combatants + self.enemy_combatants

    @property
    def living_players(self) -> list[CombatantState]:
        return [c for c in self.player_combatants if c.is_alive]

    @property
    def living_enemies(self) -> list[CombatantState]:
        return [c for c in self.enemy_combatants if c.is_alive]
