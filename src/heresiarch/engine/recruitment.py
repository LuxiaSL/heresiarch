"""Recruitment system: generate recruitable characters with randomized growth."""

from __future__ import annotations

import random
from enum import Enum
from typing import Any

from pydantic import BaseModel

from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.models.items import EquipType, Item
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.stats import GrowthVector, StatType

# --- CHA Inspection Thresholds ---
CHA_MODERATE_THRESHOLD: int = 30
CHA_FULL_THRESHOLD: int = 70

# --- Growth Variance ---
GROWTH_VARIANCE: int = 1
GROWTH_FLOOR: int = 1  # Minimum growth per stat — no dead stats

# --- Party Limits ---
MAX_ACTIVE_SIZE: int = 3
MAX_PARTY_SIZE: int = 4  # total active + reserve (3 active + 1 reserve)

# --- Recruit Equipment Probabilities ---
RECRUIT_WEAPON_CHANCE: float = 0.8
RECRUIT_ARMOR_CHANCE: float = 0.5
RECRUIT_ACCESSORY_CHANCE: float = 0.15


class InspectionLevel(str, Enum):
    MINIMAL = "MINIMAL"
    MODERATE = "MODERATE"
    FULL = "FULL"


class RecruitCandidate(BaseModel):
    """A potential recruit with randomized growth."""

    character: CharacterInstance
    growth: GrowthVector


class RecruitmentEngine:
    """Generates recruitment encounters."""

    def __init__(
        self,
        job_registry: dict[str, JobTemplate],
        item_registry: dict[str, Item] | None = None,
        rng: random.Random | None = None,
    ):
        self.job_registry = job_registry
        self.item_registry = item_registry or {}
        self.rng = rng or random.Random()

    def generate_candidate(
        self,
        zone_level: int,
        exclude_job_ids: list[str] | None = None,
        shop_pool: list[str] | None = None,
        level_range: tuple[int, int] | None = None,
    ) -> RecruitCandidate:
        """Create a random recruit at zone-appropriate level with randomized growth.

        Growth variance: each stat = job_template_growth +/- GROWTH_VARIANCE,
        clamped to [GROWTH_FLOOR, base + GROWTH_VARIANCE].

        If ``level_range`` is provided and non-zero, the recruit's level is
        randomly chosen from that range.  Otherwise falls back to ``zone_level``.

        If ``shop_pool`` is provided, equips the recruit with job-appropriate
        items (weapon 80%, armor 50%, accessory 15%).  Higher-tier items are
        weighted to appear less frequently (weight = 1/tier).

        If ``exclude_job_ids`` is provided, those jobs are excluded from the
        candidate pool (rolling-window duplicate prevention).
        """
        exclude = set(exclude_job_ids or [])
        available_jobs = [
            jid for jid in self.job_registry if jid not in exclude
        ]
        if not available_jobs:
            available_jobs = list(self.job_registry.keys())

        job_id = self.rng.choice(available_jobs)
        job = self.job_registry[job_id]

        # Resolve candidate level from zone range or flat zone_level
        candidate_level = self._resolve_candidate_level(zone_level, level_range)

        randomized_growth = self._randomize_growth(job.growth)
        stats = calculate_stats_at_level(randomized_growth, candidate_level)

        # Select equipment based on job affinity and zone shop pool
        equipment = self._select_recruit_equipment(job, shop_pool or [])

        # Compute effective stats with equipment
        equipped_items: list[Item] = []
        for slot, item_id in equipment.items():
            if item_id and item_id in self.item_registry:
                equipped_items.append(self.item_registry[item_id])
        effective = calculate_effective_stats(stats, equipped_items, [])

        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, candidate_level, effective.DEF)

        # Build ability list from job innate + breakpoints + equipment-granted
        abilities = ["basic_attack", job.innate_ability_id]
        for unlock in job.ability_unlocks:
            if unlock.level <= candidate_level and unlock.ability_id not in abilities:
                abilities.append(unlock.ability_id)
        for item in equipped_items:
            if item.granted_ability_id and item.granted_ability_id not in abilities:
                abilities.append(item.granted_ability_id)

        char_id = f"recruit_{job_id}_{self.rng.randint(1000, 9999)}"
        character = CharacterInstance(
            id=char_id,
            name=f"{job.name} Recruit",
            job_id=job_id,
            level=candidate_level,
            base_stats=stats,
            effective_stats=effective,
            current_hp=max_hp,
            max_hp=max_hp,
            abilities=abilities,
            equipment=equipment,
        )

        return RecruitCandidate(character=character, growth=randomized_growth)

    def _resolve_candidate_level(
        self,
        zone_level: int,
        level_range: tuple[int, int] | None,
    ) -> int:
        """Pick a recruit level from the zone's enemy level range.

        Falls back to ``zone_level`` if range is None or (0, 0).
        """
        if level_range and level_range != (0, 0):
            lo, hi = level_range
            return self.rng.randint(lo, hi)
        return zone_level

    def _select_recruit_equipment(
        self,
        job: JobTemplate,
        shop_pool: list[str],
    ) -> dict[str, str | None]:
        """Select random equipment for a recruit from the zone's shop pool.

        Uses job growth to determine weapon/armor affinity.
        Higher-tier items are rarer (weighted by 1/tier).
        Accessories have a small chance and are fully random (no affinity).
        """
        equipment: dict[str, str | None] = {
            "WEAPON": None,
            "ARMOR": None,
            "ACCESSORY_1": None,
            "ACCESSORY_2": None,
        }

        if not self.item_registry:
            return equipment

        prefers_str = job.growth.STR >= job.growth.MAG
        prefers_def = job.growth.DEF >= job.growth.RES

        weapons: list[str] = []
        armors: list[str] = []

        # Weapons and armor are filtered from the shop pool (affinity-based)
        for item_id in shop_pool:
            item = self.item_registry.get(item_id)
            if item is None or item.is_consumable:
                continue
            if item.equip_type == EquipType.WEAPON and item.scaling:
                if prefers_str and item.scaling.stat == StatType.STR:
                    weapons.append(item_id)
                elif not prefers_str and item.scaling.stat == StatType.MAG:
                    weapons.append(item_id)
            elif item.equip_type == EquipType.ARMOR and item.scaling:
                if prefers_def and item.scaling.stat == StatType.DEF:
                    armors.append(item_id)
                elif not prefers_def and item.scaling.stat == StatType.RES:
                    armors.append(item_id)
            # Flat-stat armor (e.g. warding_mail) matches either affinity
            elif item.equip_type == EquipType.ARMOR and item.flat_stat_bonus:
                armors.append(item_id)

        if weapons and self.rng.random() < RECRUIT_WEAPON_CHANCE:
            equipment["WEAPON"] = self._tier_weighted_choice(weapons)

        if armors and self.rng.random() < RECRUIT_ARMOR_CHANCE:
            equipment["ARMOR"] = self._tier_weighted_choice(armors)

        # Accessories: small chance, fully random from all accessories in registry
        accessories = [
            iid for iid, item in self.item_registry.items()
            if item.equip_type == EquipType.ACCESSORY
            and not item.is_consumable
        ]
        if accessories and self.rng.random() < RECRUIT_ACCESSORY_CHANCE:
            equipment["ACCESSORY_1"] = self.rng.choice(accessories)

        return equipment

    def _tier_weighted_choice(self, item_ids: list[str]) -> str:
        """Pick an item weighted inversely by tier (higher tier = rarer).

        Weight = 1 / tier.  Tier 1 = weight 1.0, tier 2 = 0.5, tier 3 = 0.33.
        Falls back to uniform choice if items have no registry entries.
        """
        weights: list[float] = []
        for item_id in item_ids:
            item = self.item_registry.get(item_id)
            tier = item.tier if item else 1
            weights.append(1.0 / tier)
        return self.rng.choices(item_ids, weights=weights, k=1)[0]

    def get_inspection_level(self, cha: int) -> InspectionLevel:
        """CHA < 30: MINIMAL. CHA 30-69: MODERATE. CHA >= 70: FULL."""
        if cha >= CHA_FULL_THRESHOLD:
            return InspectionLevel.FULL
        if cha >= CHA_MODERATE_THRESHOLD:
            return InspectionLevel.MODERATE
        return InspectionLevel.MINIMAL

    def inspect_candidate(
        self,
        candidate: RecruitCandidate,
        cha: int,
    ) -> dict[str, Any]:
        """Returns visible information based on CHA level.

        MINIMAL: name, job_id only.
        MODERATE: + growth rates.
        FULL: + current stats, level, HP, full stat projection at 99.
        """
        level = self.get_inspection_level(cha)
        info: dict[str, Any] = {
            "name": candidate.character.name,
            "job_id": candidate.character.job_id,
        }

        if level in (InspectionLevel.MODERATE, InspectionLevel.FULL):
            info["growth"] = candidate.growth

        if level == InspectionLevel.FULL:
            info["level"] = candidate.character.level
            info["stats"] = candidate.character.base_stats
            info["hp"] = candidate.character.current_hp
            projected_stats = calculate_stats_at_level(candidate.growth, 99)
            info["projected_stats_99"] = projected_stats

        return info

    def recruit(
        self,
        party: Party,
        candidate: RecruitCandidate,
    ) -> Party:
        """Add candidate to active party if there's room, otherwise reserve.

        Raises ValueError if party already has MAX_PARTY_SIZE characters.
        """
        total = len(party.active) + len(party.reserve)
        if total >= MAX_PARTY_SIZE:
            raise ValueError(
                f"Party is full ({total}/{MAX_PARTY_SIZE}). "
                "Cannot recruit another character."
            )

        new_characters = dict(party.characters)
        new_characters[candidate.character.id] = candidate.character

        # Add equipped items to party inventory so they resolve during combat
        new_items = dict(party.items)
        for slot, item_id in candidate.character.equipment.items():
            if item_id and item_id in self.item_registry:
                new_items[item_id] = self.item_registry[item_id]

        if len(party.active) < MAX_ACTIVE_SIZE:
            new_active = list(party.active) + [candidate.character.id]
            return party.model_copy(
                update={
                    "characters": new_characters,
                    "active": new_active,
                    "items": new_items,
                }
            )

        new_reserve = list(party.reserve) + [candidate.character.id]
        return party.model_copy(
            update={
                "characters": new_characters,
                "reserve": new_reserve,
                "items": new_items,
            }
        )

    def _randomize_growth(self, base_growth: GrowthVector) -> GrowthVector:
        """Apply +/- GROWTH_VARIANCE to each stat, clamped to [GROWTH_FLOOR, base + GROWTH_VARIANCE]."""
        data: dict[str, int] = {}
        for stat in StatType:
            base_val = getattr(base_growth, stat.value)
            delta = self.rng.randint(-GROWTH_VARIANCE, GROWTH_VARIANCE)
            new_val = max(GROWTH_FLOOR, min(base_val + GROWTH_VARIANCE, base_val + delta))
            data[stat.value] = new_val
        return GrowthVector(**data)
