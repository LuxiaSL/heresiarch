"""Recruitment system: generate recruitable characters with randomized growth."""

from __future__ import annotations

import random
from enum import Enum
from typing import Any

from pydantic import BaseModel

from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.stats import GrowthVector, StatType

# --- CHA Inspection Thresholds ---
CHA_MODERATE_THRESHOLD: int = 30
CHA_FULL_THRESHOLD: int = 70

# --- Growth Variance ---
GROWTH_VARIANCE: int = 2

# --- Party Limits ---
MAX_PARTY_SIZE: int = 4


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
        rng: random.Random | None = None,
    ):
        self.job_registry = job_registry
        self.rng = rng or random.Random()

    def generate_candidate(
        self,
        zone_level: int,
        exclude_job_ids: list[str] | None = None,
    ) -> RecruitCandidate:
        """Create a random recruit at zone-appropriate level with randomized growth.

        Growth variance: each stat = job_template_growth +/- randint(-2, 2),
        clamped to [0, job_template_growth + GROWTH_VARIANCE].
        Character level = zone_level.
        """
        exclude = set(exclude_job_ids or [])
        available_jobs = [
            jid for jid in self.job_registry if jid not in exclude
        ]
        if not available_jobs:
            available_jobs = list(self.job_registry.keys())

        job_id = self.rng.choice(available_jobs)
        job = self.job_registry[job_id]

        randomized_growth = self._randomize_growth(job.growth)
        stats = calculate_stats_at_level(randomized_growth, zone_level)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, zone_level, stats.DEF)

        char_id = f"recruit_{job_id}_{self.rng.randint(1000, 9999)}"
        character = CharacterInstance(
            id=char_id,
            name=f"{job.name} Recruit",
            job_id=job_id,
            level=zone_level,
            base_stats=stats,
            current_hp=max_hp,
            abilities=["basic_attack", job.innate_ability_id],
        )

        return RecruitCandidate(character=character, growth=randomized_growth)

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
            info["growth"] = candidate.growth.model_dump()

        if level == InspectionLevel.FULL:
            info["level"] = candidate.character.level
            info["current_stats"] = candidate.character.base_stats.model_dump()
            info["current_hp"] = candidate.character.current_hp
            projected_stats = calculate_stats_at_level(candidate.growth, 99)
            info["projected_stats_99"] = projected_stats.model_dump()

        return info

    def recruit(
        self,
        party: Party,
        candidate: RecruitCandidate,
    ) -> Party:
        """Add candidate to party reserve.

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
        new_reserve = list(party.reserve) + [candidate.character.id]

        return party.model_copy(
            update={"characters": new_characters, "reserve": new_reserve}
        )

    def _randomize_growth(self, base_growth: GrowthVector) -> GrowthVector:
        """Apply +/- GROWTH_VARIANCE to each stat, clamped to [0, base + GROWTH_VARIANCE]."""
        data: dict[str, int] = {}
        for stat in StatType:
            base_val = getattr(base_growth, stat.value)
            delta = self.rng.randint(-GROWTH_VARIANCE, GROWTH_VARIANCE)
            new_val = max(0, min(base_val + GROWTH_VARIANCE, base_val + delta))
            data[stat.value] = new_val
        return GrowthVector(**data)
