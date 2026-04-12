"""Game models — pydantic types for all game entities."""

from .abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    DamageQuality,
    TargetType,
    TriggerCondition,
)
from .combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatEvent,
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
    StatusEffect,
)
from .enemies import (
    ActionCondition,
    ActionTable,
    ActionWeight,
    EnemyArchetype,
    EnemyInstance,
    EnemyTemplate,
)
from .items import ConversionEffect, EquipSlot, Item, ItemScaling, ScalingType
from .jobs import CharacterInstance, JobTemplate
from .loot import DropTable, LootResult
from .party import Party
from .battle_record import BattleRecord, EncounterRecord, RoundRecord
from .region_map import AsciiMap, MapAnchor, RegionMap, ZoneAnchor
from .run_state import CombatResult, RunState
from .stats import GrowthVector, StatBlock, StatType
from .zone import EncounterTemplate, ZoneState, ZoneTemplate

__all__ = [
    "Ability",
    "BattleRecord",
    "AbilityCategory",
    "AbilityEffect",
    "ActionCondition",
    "ActionTable",
    "ActionWeight",
    "CharacterInstance",
    "CheatSurviveChoice",
    "CombatAction",
    "CombatResult",
    "CombatantState",
    "CombatEvent",
    "CombatEventType",
    "CombatState",
    "ConversionEffect",
    "DamageQuality",
    "DropTable",
    "EncounterRecord",
    "EncounterTemplate",
    "EnemyArchetype",
    "EnemyInstance",
    "EnemyTemplate",
    "EquipSlot",
    "GrowthVector",
    "Item",
    "ItemScaling",
    "JobTemplate",
    "LootResult",
    "Party",
    "PlayerTurnDecision",
    "AsciiMap",
    "MapAnchor",
    "RegionMap",
    "RoundRecord",
    "RunState",
    "ScalingType",
    "StatBlock",
    "StatType",
    "StatusEffect",
    "TargetType",
    "TriggerCondition",
    "ZoneAnchor",
    "ZoneState",
    "ZoneTemplate",
]
