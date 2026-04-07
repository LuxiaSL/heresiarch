"""Tests for recruitment system: candidate generation, CHA inspection, party management."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.stats import GrowthVector, StatType
from heresiarch.engine.recruitment import (
    CHA_FULL_THRESHOLD,
    CHA_MODERATE_THRESHOLD,
    GROWTH_VARIANCE,
    MAX_PARTY_SIZE,
    InspectionLevel,
    RecruitCandidate,
    RecruitmentEngine,
)


@pytest.fixture
def recruitment_engine(game_data: GameData, seeded_rng: random.Random) -> RecruitmentEngine:
    return RecruitmentEngine(
        job_registry=game_data.jobs,
        item_registry=game_data.items,
        rng=seeded_rng,
    )


class TestCandidateGeneration:
    def test_candidate_has_valid_job(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        assert candidate.character.job_id in game_data.jobs

    def test_candidate_level_matches_zone(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=15)
        assert candidate.character.level == 15

    def test_candidate_has_innate_ability(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        job = game_data.jobs[candidate.character.job_id]
        assert job.innate_ability_id in candidate.character.abilities

    def test_candidate_has_hp(self, recruitment_engine: RecruitmentEngine) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        assert candidate.character.current_hp > 0

    def test_candidate_has_unique_id(self, recruitment_engine: RecruitmentEngine) -> None:
        c1 = recruitment_engine.generate_candidate(zone_level=10)
        c2 = recruitment_engine.generate_candidate(zone_level=10)
        assert c1.character.id != c2.character.id


class TestGrowthVariance:
    def test_growth_within_bounds(
        self, game_data: GameData
    ) -> None:
        """Over 50 generations, all growths stay within +/- GROWTH_VARIANCE of template."""
        rng = random.Random(12345)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)

        for _ in range(50):
            candidate = engine.generate_candidate(zone_level=10)
            job = game_data.jobs[candidate.character.job_id]
            for stat in StatType:
                base = getattr(job.growth, stat.value)
                actual = getattr(candidate.growth, stat.value)
                assert actual >= 0, f"{stat.value} went negative"
                assert actual <= base + GROWTH_VARIANCE, (
                    f"{stat.value}: {actual} > {base + GROWTH_VARIANCE}"
                )
                assert actual >= base - GROWTH_VARIANCE or actual == 0, (
                    f"{stat.value}: {actual} below {base - GROWTH_VARIANCE} (not clamped to 0)"
                )

    def test_growth_has_variance(self, game_data: GameData) -> None:
        """Verify growths aren't all identical (randomization is happening)."""
        rng = random.Random(99)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)
        growths = [engine.generate_candidate(zone_level=10).growth for _ in range(20)]
        # At least some should differ
        unique = set(g.model_dump_json() for g in growths)
        assert len(unique) > 1


class TestExcludeJobs:
    def test_exclude_prevents_job(self, game_data: GameData) -> None:
        """Excluding all but one job forces that job."""
        rng = random.Random(42)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)
        all_jobs = list(game_data.jobs.keys())
        target_job = all_jobs[0]
        exclude = all_jobs[1:]

        for _ in range(10):
            candidate = engine.generate_candidate(zone_level=10, exclude_job_ids=exclude)
            assert candidate.character.job_id == target_job

    def test_exclude_all_falls_back(self, game_data: GameData) -> None:
        """Excluding all jobs still produces a candidate (fallback to full pool)."""
        rng = random.Random(42)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)
        candidate = engine.generate_candidate(
            zone_level=10, exclude_job_ids=list(game_data.jobs.keys())
        )
        assert candidate.character.job_id in game_data.jobs


class TestInspectionCHA:
    def test_low_cha_minimal(self, recruitment_engine: RecruitmentEngine) -> None:
        assert recruitment_engine.get_inspection_level(0) == InspectionLevel.MINIMAL
        assert recruitment_engine.get_inspection_level(29) == InspectionLevel.MINIMAL

    def test_moderate_cha(self, recruitment_engine: RecruitmentEngine) -> None:
        assert recruitment_engine.get_inspection_level(30) == InspectionLevel.MODERATE
        assert recruitment_engine.get_inspection_level(69) == InspectionLevel.MODERATE

    def test_high_cha_full(self, recruitment_engine: RecruitmentEngine) -> None:
        assert recruitment_engine.get_inspection_level(70) == InspectionLevel.FULL
        assert recruitment_engine.get_inspection_level(100) == InspectionLevel.FULL

    def test_minimal_shows_name_job_only(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        info = recruitment_engine.inspect_candidate(candidate, cha=10)
        assert "name" in info
        assert "job_id" in info
        assert "growth" not in info
        assert "stats" not in info

    def test_moderate_shows_growth(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        info = recruitment_engine.inspect_candidate(candidate, cha=50)
        assert "growth" in info
        assert "stats" not in info

    def test_full_shows_everything(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        info = recruitment_engine.inspect_candidate(candidate, cha=80)
        assert "growth" in info
        assert "stats" in info
        assert "projected_stats_99" in info
        assert "level" in info
        assert "hp" in info


class TestRecruitEquipment:
    def test_recruit_with_shop_pool_can_have_weapon(
        self, game_data: GameData
    ) -> None:
        """With a shop pool, recruits can spawn with weapons."""
        equipped_any = False
        for seed in range(50):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=5,
                shop_pool=["iron_blade", "spirit_lens", "iron_guard", "spirit_mantle"],
            )
            if candidate.character.equipment.get("WEAPON"):
                equipped_any = True
                break
        assert equipped_any, "Expected at least one recruit with a weapon in 50 seeds"

    def test_recruit_without_shop_pool_has_no_equipment(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        """Without a shop pool, recruits spawn unarmed."""
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        equipment = candidate.character.equipment
        assert all(v is None for v in equipment.values())

    def test_str_job_gets_str_weapon(self, game_data: GameData) -> None:
        """STR jobs should get STR-scaling weapons from the pool."""
        for seed in range(50):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=5,
                exclude_job_ids=["onmyoji"],  # only STR jobs
                shop_pool=["iron_blade", "spirit_lens"],
            )
            weapon = candidate.character.equipment.get("WEAPON")
            if weapon:
                item = game_data.items[weapon]
                assert item.scaling.stat.value == "STR"

    def test_mag_job_gets_mag_weapon(self, game_data: GameData) -> None:
        """MAG jobs should get MAG-scaling weapons from the pool."""
        for seed in range(50):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=5,
                exclude_job_ids=["einherjar", "berserker", "martyr"],
                shop_pool=["iron_blade", "spirit_lens"],
            )
            weapon = candidate.character.equipment.get("WEAPON")
            if weapon:
                item = game_data.items[weapon]
                assert item.scaling.stat.value == "MAG"

    def test_recruit_effective_stats_include_equipment(
        self, game_data: GameData
    ) -> None:
        """Recruit effective_stats should account for equipped items."""
        # Force a recruit with a weapon
        for seed in range(100):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=10,
                shop_pool=["iron_blade", "spirit_lens", "iron_guard", "spirit_mantle"],
            )
            if candidate.character.equipment.get("WEAPON"):
                # effective_stats should differ from base_stats
                assert candidate.character.effective_stats != candidate.character.base_stats
                break

    def test_recruit_items_added_to_party_on_recruit(
        self, game_data: GameData
    ) -> None:
        """When recruited, the recruit's equipped items should be in party.items."""
        for seed in range(100):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=5,
                shop_pool=["iron_blade", "spirit_lens"],
            )
            if candidate.character.equipment.get("WEAPON"):
                party = Party(active=[], characters={})
                new_party = engine.recruit(party, candidate)
                weapon_id = candidate.character.equipment["WEAPON"]
                assert weapon_id in new_party.items
                break


class TestRecruitToParty:
    def _make_party_with_n(self, game_data: GameData, n: int) -> Party:
        """Helper to make a party with n characters."""
        from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level

        chars: dict[str, CharacterInstance] = {}
        active: list[str] = []
        reserve: list[str] = []
        for i in range(n):
            job_id = list(game_data.jobs.keys())[i % len(game_data.jobs)]
            job = game_data.jobs[job_id]
            stats = calculate_stats_at_level(job.growth, 5)
            char = CharacterInstance(
                id=f"char_{i}",
                name=f"Char {i}",
                job_id=job_id,
                level=5,
                base_stats=stats,
                current_hp=calculate_max_hp(job.base_hp, job.hp_growth, 5, stats.DEF),
                abilities=[job.innate_ability_id],
            )
            chars[char.id] = char
            if i < 3:
                active.append(char.id)
            else:
                reserve.append(char.id)
        return Party(active=active, reserve=reserve, characters=chars)

    def test_recruit_adds_to_active_if_room(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        party = self._make_party_with_n(game_data, 2)
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        new_party = recruitment_engine.recruit(party, candidate)
        assert candidate.character.id in new_party.active
        assert candidate.character.id in new_party.characters

    def test_recruit_adds_to_reserve_when_active_full(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        party = self._make_party_with_n(game_data, 3)
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        new_party = recruitment_engine.recruit(party, candidate)
        assert candidate.character.id in new_party.reserve
        assert candidate.character.id in new_party.characters

    def test_recruit_party_full_raises(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        party = self._make_party_with_n(game_data, MAX_PARTY_SIZE)
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        with pytest.raises(ValueError, match="full"):
            recruitment_engine.recruit(party, candidate)

    def test_recruit_preserves_existing(
        self, recruitment_engine: RecruitmentEngine, game_data: GameData
    ) -> None:
        party = self._make_party_with_n(game_data, 2)
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        new_party = recruitment_engine.recruit(party, candidate)
        # Original characters still present
        for char_id in party.characters:
            assert char_id in new_party.characters
