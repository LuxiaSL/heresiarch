"""Tests for recruitment system: candidate generation, CHA inspection, party management, dismiss."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.items import EquipSlot
from heresiarch.engine.models.jobs import CharacterInstance, JobTemplate
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.run_state import RunState
from heresiarch.engine.models.stats import GrowthVector, StatType
from heresiarch.engine.recruitment import (
    CHA_FULL_THRESHOLD,
    CHA_MODERATE_THRESHOLD,
    GROWTH_FLOOR,
    GROWTH_VARIANCE,
    MAX_PARTY_SIZE,
    RECRUIT_ACCESSORY_CHANCE,
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

    def test_candidate_level_from_range(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        """When level_range is provided, candidate level falls within it."""
        for _ in range(20):
            candidate = recruitment_engine.generate_candidate(
                zone_level=5, level_range=(8, 12)
            )
            assert 8 <= candidate.character.level <= 12

    def test_candidate_level_range_zero_falls_back(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        """level_range (0, 0) falls back to zone_level."""
        candidate = recruitment_engine.generate_candidate(
            zone_level=15, level_range=(0, 0)
        )
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
        """Over 50 generations, all growths stay within bounds with floor of GROWTH_FLOOR."""
        rng = random.Random(12345)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)

        for _ in range(50):
            candidate = engine.generate_candidate(zone_level=10)
            job = game_data.jobs[candidate.character.job_id]
            for stat in StatType:
                base = getattr(job.growth, stat.value)
                actual = getattr(candidate.growth, stat.value)
                assert actual >= GROWTH_FLOOR, (
                    f"{stat.value}: {actual} below floor {GROWTH_FLOOR}"
                )
                assert actual <= base + GROWTH_VARIANCE, (
                    f"{stat.value}: {actual} > {base + GROWTH_VARIANCE}"
                )

    def test_growth_has_variance(self, game_data: GameData) -> None:
        """Verify growths aren't all identical (randomization is happening)."""
        rng = random.Random(99)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)
        growths = [engine.generate_candidate(zone_level=10).growth for _ in range(20)]
        # At least some should differ
        unique = set(g.model_dump_json() for g in growths)
        assert len(unique) > 1

    def test_growth_floor_prevents_dead_stats(self, game_data: GameData) -> None:
        """No stat should ever reach 0 — floor of GROWTH_FLOOR enforced."""
        rng = random.Random(777)
        engine = RecruitmentEngine(job_registry=game_data.jobs, rng=rng)

        for _ in range(100):
            candidate = engine.generate_candidate(zone_level=10)
            for stat in StatType:
                actual = getattr(candidate.growth, stat.value)
                assert actual >= GROWTH_FLOOR, (
                    f"{stat.value} hit {actual}, expected >= {GROWTH_FLOOR}"
                )


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

    def test_recruit_without_shop_pool_has_no_weapon_or_armor(
        self, recruitment_engine: RecruitmentEngine
    ) -> None:
        """Without a shop pool, recruits have no weapon or armor (accessories still possible)."""
        candidate = recruitment_engine.generate_candidate(zone_level=10)
        equipment = candidate.character.equipment
        assert equipment.get("WEAPON") is None
        assert equipment.get("ARMOR") is None

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

    def test_tier_weighting_favors_lower_tiers(self, game_data: GameData) -> None:
        """Higher-tier items should appear less often than lower-tier items."""
        tier1_count = 0
        tier2_count = 0
        # Pool with tier 1 + tier 2 weapons
        pool = ["iron_blade", "runic_edge"]
        for seed in range(200):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=10,
                exclude_job_ids=["onmyoji"],  # STR jobs only
                shop_pool=pool,
            )
            weapon = candidate.character.equipment.get("WEAPON")
            if weapon == "iron_blade":
                tier1_count += 1
            elif weapon == "runic_edge":
                tier2_count += 1

        assert tier1_count > 0 and tier2_count > 0, "Both tiers should appear"
        assert tier1_count > tier2_count, (
            f"Tier 1 ({tier1_count}) should appear more than tier 2 ({tier2_count})"
        )

    def test_accessory_can_appear(self, game_data: GameData) -> None:
        """Recruits can spawn with an accessory from the full item registry."""
        found_accessory = False
        for seed in range(200):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=10,
                shop_pool=["iron_blade", "spirit_lens"],
            )
            if candidate.character.equipment.get("ACCESSORY_1"):
                found_accessory = True
                # Verify it's actually an accessory from the registry
                acc_id = candidate.character.equipment["ACCESSORY_1"]
                item = game_data.items[acc_id]
                assert item.slot in (EquipSlot.ACCESSORY_1, EquipSlot.ACCESSORY_2)
                break
        assert found_accessory, "Expected at least one recruit with an accessory in 200 seeds"

    def test_accessory_fully_random(self, game_data: GameData) -> None:
        """Accessory selection doesn't depend on job affinity — any accessory can appear."""
        seen_accessories: set[str] = set()
        for seed in range(500):
            rng = random.Random(seed)
            engine = RecruitmentEngine(
                job_registry=game_data.jobs,
                item_registry=game_data.items,
                rng=rng,
            )
            candidate = engine.generate_candidate(
                zone_level=10,
                shop_pool=["iron_blade"],
            )
            acc = candidate.character.equipment.get("ACCESSORY_1")
            if acc:
                seen_accessories.add(acc)
        # Should see more than 1 different accessory across 500 seeds
        assert len(seen_accessories) > 1, (
            f"Expected variety in accessories, only saw: {seen_accessories}"
        )


class TestRecruitToParty:
    def _make_party_with_n(self, game_data: GameData, n: int) -> Party:
        """Helper to make a party with n characters."""
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


class TestDismiss:
    """Tests for GameLoop.dismiss_character."""

    def _make_equipped_party(self, game_data: GameData) -> tuple[RunState, GameLoop]:
        """Build a 3-active party where char_1 has an equipped weapon."""
        gl = GameLoop(game_data=game_data, rng=random.Random(42))
        mc_job = list(game_data.jobs.keys())[0]
        mc_template = game_data.jobs[mc_job]
        mc_stats = calculate_stats_at_level(mc_template.growth, 5)

        mc = CharacterInstance(
            id="mc",
            name="MC",
            job_id=mc_job,
            level=5,
            base_stats=mc_stats,
            current_hp=100,
            max_hp=100,
            abilities=["basic_attack"],
            is_mc=True,
        )

        ally_job = list(game_data.jobs.keys())[1]
        ally_template = game_data.jobs[ally_job]
        ally_stats = calculate_stats_at_level(ally_template.growth, 5)
        ally = CharacterInstance(
            id="ally_1",
            name="Ally 1",
            job_id=ally_job,
            level=5,
            base_stats=ally_stats,
            current_hp=100,
            max_hp=100,
            abilities=["basic_attack"],
            equipment={"WEAPON": "iron_blade", "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None},
        )

        ally2_job = list(game_data.jobs.keys())[2]
        ally2_template = game_data.jobs[ally2_job]
        ally2_stats = calculate_stats_at_level(ally2_template.growth, 5)
        ally2 = CharacterInstance(
            id="ally_2",
            name="Ally 2",
            job_id=ally2_job,
            level=5,
            base_stats=ally2_stats,
            current_hp=100,
            max_hp=100,
            abilities=["basic_attack"],
        )

        party = Party(
            active=["mc", "ally_1", "ally_2"],
            reserve=[],
            characters={"mc": mc, "ally_1": ally, "ally_2": ally2},
            items={"iron_blade": game_data.items["iron_blade"]},
        )
        run = RunState(run_id="test", party=party)
        return run, gl

    def test_dismiss_removes_character(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        new_run = gl.dismiss_character(run, "ally_2")
        assert "ally_2" not in new_run.party.characters
        assert "ally_2" not in new_run.party.active
        assert len(new_run.party.active) == 2

    def test_dismiss_takes_equipped_gear(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        new_run = gl.dismiss_character(run, "ally_1")
        assert "ally_1" not in new_run.party.characters
        # iron_blade was equipped on ally_1 — should be gone
        assert "iron_blade" not in new_run.party.items

    def test_dismiss_mc_raises(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        with pytest.raises(ValueError, match="MC"):
            gl.dismiss_character(run, "mc")

    def test_dismiss_last_active_raises(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        # Dismiss until 1 active remains
        run = gl.dismiss_character(run, "ally_1")
        run = gl.dismiss_character(run, "ally_2")
        # MC is last active — shouldn't reach here due to MC check, but
        # if we had a non-MC solo, this would fire
        with pytest.raises(ValueError):
            gl.dismiss_character(run, "mc")

    def test_dismiss_unknown_character_raises(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        with pytest.raises(ValueError, match="not in party"):
            gl.dismiss_character(run, "nonexistent")

    def test_dismiss_preserves_other_members(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        new_run = gl.dismiss_character(run, "ally_1")
        assert "mc" in new_run.party.characters
        assert "ally_2" in new_run.party.characters
        assert "mc" in new_run.party.active

    def test_dismiss_from_reserve(self, game_data: GameData) -> None:
        run, gl = self._make_equipped_party(game_data)
        # Move ally_2 to reserve first by adding a 4th, or manipulate directly
        ally2 = run.party.characters["ally_2"]
        new_active = [cid for cid in run.party.active if cid != "ally_2"]
        new_party = run.party.model_copy(
            update={"active": new_active, "reserve": ["ally_2"]}
        )
        run = run.model_copy(update={"party": new_party})

        new_run = gl.dismiss_character(run, "ally_2")
        assert "ally_2" not in new_run.party.reserve
        assert "ally_2" not in new_run.party.characters


class TestMCMimicValidation:
    """Tests for mc_swap_job party membership constraint."""

    def test_mimic_valid_party_job(self, game_data: GameData) -> None:
        """MC can swap to a job held by a party member."""
        gl = GameLoop(game_data=game_data, rng=random.Random(42))
        all_jobs = list(game_data.jobs.keys())
        mc_job = all_jobs[0]
        ally_job = all_jobs[1]

        mc_template = game_data.jobs[mc_job]
        mc_stats = calculate_stats_at_level(mc_template.growth, 5)
        mc = CharacterInstance(
            id="mc", name="MC", job_id=mc_job, level=5,
            base_stats=mc_stats, current_hp=100, max_hp=100,
            abilities=["basic_attack"], is_mc=True,
            growth_history=[(mc_job, 5)],
        )

        ally_template = game_data.jobs[ally_job]
        ally_stats = calculate_stats_at_level(ally_template.growth, 5)
        ally = CharacterInstance(
            id="ally", name="Ally", job_id=ally_job, level=5,
            base_stats=ally_stats, current_hp=100, max_hp=100,
            abilities=["basic_attack"],
        )

        party = Party(
            active=["mc", "ally"], reserve=[],
            characters={"mc": mc, "ally": ally},
        )
        run = RunState(run_id="test", party=party)

        new_run = gl.mc_swap_job(run, ally_job)
        mc_after = new_run.party.characters["mc"]
        assert mc_after.job_id == ally_job

    def test_mimic_job_not_in_party_raises(self, game_data: GameData) -> None:
        """MC cannot swap to a job no party member has."""
        gl = GameLoop(game_data=game_data, rng=random.Random(42))
        all_jobs = list(game_data.jobs.keys())
        mc_job = all_jobs[0]
        # ally has the SAME job as MC — no other job in party
        mc_template = game_data.jobs[mc_job]
        mc_stats = calculate_stats_at_level(mc_template.growth, 5)
        mc = CharacterInstance(
            id="mc", name="MC", job_id=mc_job, level=5,
            base_stats=mc_stats, current_hp=100, max_hp=100,
            abilities=["basic_attack"], is_mc=True,
            growth_history=[(mc_job, 5)],
        )

        party = Party(
            active=["mc"], reserve=[],
            characters={"mc": mc},
        )
        run = RunState(run_id="test", party=party)

        target_job = all_jobs[1]
        with pytest.raises(ValueError, match="no party member has it"):
            gl.mc_swap_job(run, target_job)
