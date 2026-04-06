"""Tests for XP/leveling formulas and MC Mimic stat calculation."""

import pytest

from heresiarch.engine.formulas import (
    XP_MINIMUM_RATIO,
    XP_THRESHOLD_BASE,
    calculate_levels_gained,
    calculate_stats_from_history,
    calculate_xp_reward,
    xp_for_level,
)
from heresiarch.engine.models.stats import GrowthVector, StatType


class TestXPReward:
    """XP reward = zone_level * budget_multiplier."""

    def test_fodder_zone5(self) -> None:
        xp = calculate_xp_reward(zone_level=5, budget_multiplier=8.0, character_level=5)
        assert xp == 40

    def test_brute_zone15(self) -> None:
        xp = calculate_xp_reward(zone_level=15, budget_multiplier=14.0, character_level=15)
        assert xp == 210

    def test_caster_zone10(self) -> None:
        xp = calculate_xp_reward(zone_level=10, budget_multiplier=12.0, character_level=10)
        assert xp == 120

    def test_support_zone8(self) -> None:
        xp = calculate_xp_reward(zone_level=8, budget_multiplier=10.0, character_level=8)
        assert xp == 80


class TestXPOverlevelPenalty:
    """Diminishing XP when character level exceeds zone cap."""

    def test_at_cap_full_xp(self) -> None:
        xp = calculate_xp_reward(
            zone_level=10, budget_multiplier=14.0, character_level=15, xp_cap_level=15
        )
        assert xp == 140

    def test_one_over_cap(self) -> None:
        base = calculate_xp_reward(zone_level=10, budget_multiplier=14.0, character_level=15)
        penalized = calculate_xp_reward(
            zone_level=10, budget_multiplier=14.0, character_level=16, xp_cap_level=15
        )
        assert penalized < base
        assert penalized == int(base * 0.5)

    def test_two_over_cap(self) -> None:
        base = 140  # zone 10, brute budget
        penalized = calculate_xp_reward(
            zone_level=10, budget_multiplier=14.0, character_level=17, xp_cap_level=15
        )
        assert penalized == int(base * 0.25)

    def test_many_over_cap_floors_at_minimum(self) -> None:
        penalized = calculate_xp_reward(
            zone_level=10, budget_multiplier=14.0, character_level=30, xp_cap_level=15
        )
        assert penalized == max(1, int(140 * XP_MINIMUM_RATIO))

    def test_no_cap_no_penalty(self) -> None:
        """xp_cap_level=0 means no cap applied."""
        xp = calculate_xp_reward(
            zone_level=10, budget_multiplier=14.0, character_level=50, xp_cap_level=0
        )
        assert xp == 140


class TestLevelThresholds:
    """Cumulative XP needed: level^2 * XP_THRESHOLD_BASE."""

    def test_level_1_is_zero(self) -> None:
        assert xp_for_level(1) == 0

    def test_level_2(self) -> None:
        assert xp_for_level(2) == 4 * XP_THRESHOLD_BASE  # 2^2 * 10 = 40

    def test_level_10(self) -> None:
        assert xp_for_level(10) == 100 * XP_THRESHOLD_BASE  # 10^2 * 10 = 1000

    def test_level_50(self) -> None:
        assert xp_for_level(50) == 2500 * XP_THRESHOLD_BASE  # 25000

    def test_level_99(self) -> None:
        assert xp_for_level(99) == 9801 * XP_THRESHOLD_BASE  # 98010

    def test_monotonically_increasing(self) -> None:
        for level in range(2, 100):
            assert xp_for_level(level) < xp_for_level(level + 1)


class TestLevelsGained:
    """Given current XP and level, how many levels to gain."""

    def test_no_gain(self) -> None:
        # At level 1, need 40 XP for level 2. With 30, no gain.
        assert calculate_levels_gained(30, 1) == 0

    def test_one_level(self) -> None:
        # At level 1, need 40 XP for level 2. With 40, gain 1.
        assert calculate_levels_gained(40, 1) == 1

    def test_two_levels(self) -> None:
        # Level 2 needs 40, level 3 needs 90. With 90 XP at level 1, gain 2.
        assert calculate_levels_gained(90, 1) == 2

    def test_exact_threshold(self) -> None:
        # At level 5, need xp_for_level(6) = 360 to gain 1.
        assert calculate_levels_gained(360, 5) == 1

    def test_just_below_threshold(self) -> None:
        assert calculate_levels_gained(359, 5) == 0

    def test_cap_at_99(self) -> None:
        # Even with infinite XP, can't go above 99.
        assert calculate_levels_gained(999999999, 98) == 1


class TestMCMimicStats:
    """Composite stats from multi-job growth history."""

    def test_single_job_history(self, game_data) -> None:  # type: ignore[no-untyped-def]
        """10 levels as Einherjar should match calculate_stats_at_level."""
        from heresiarch.engine.formulas import calculate_stats_at_level

        job = game_data.jobs["einherjar"]
        history = [("einherjar", 10)]
        result = calculate_stats_from_history(history, game_data.jobs)
        expected = calculate_stats_at_level(job.growth, 10)
        assert result == expected

    def test_two_job_history(self, game_data) -> None:  # type: ignore[no-untyped-def]
        """10 levels Einherjar + 5 levels Berserker."""
        history = [("einherjar", 10), ("berserker", 5)]
        result = calculate_stats_from_history(history, game_data.jobs)

        ein = game_data.jobs["einherjar"]
        ber = game_data.jobs["berserker"]

        # STR: ein(4+1)*10 + ber(5+1)*5 = 50+30 = 80
        assert result.STR == ein.growth.effective_growth(StatType.STR) * 10 + ber.growth.effective_growth(StatType.STR) * 5

    def test_empty_history(self, game_data) -> None:  # type: ignore[no-untyped-def]
        result = calculate_stats_from_history([], game_data.jobs)
        assert result.STR == 0
        assert result.MAG == 0
