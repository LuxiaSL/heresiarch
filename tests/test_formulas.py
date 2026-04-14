"""Unit tests for all game formulas against design-doc numbers."""

from heresiarch.engine.formulas import (
    apply_survive_reduction,
    calculate_speed_bonus,
    calculate_enemy_hp,
    calculate_enemy_stats,
    calculate_magical_damage,
    calculate_max_hp,
    calculate_physical_damage,
    calculate_stats_at_level,
    check_res_gate,
)
from heresiarch.engine.models.stats import GrowthVector


# ------------------------------------------------------------------ HP tests


class TestCalculateMaxHP:
    def test_hp_calculation_einherjar_lv15(self) -> None:
        # base=50, hp_growth=8, lv=15, DEF=75
        # 50 + 8*15 + int(75*1.5) = 50 + 120 + 112 = 282
        assert calculate_max_hp(base_hp=50, hp_growth=8, level=15, effective_def=75) == 282

    def test_hp_calculation_onmyoji_lv15(self) -> None:
        # base=30, hp_growth=5, lv=15, DEF=15
        # 30 + 5*15 + int(15*1.5) = 30 + 75 + 22 = 127
        assert calculate_max_hp(base_hp=30, hp_growth=5, level=15, effective_def=15) == 127

    def test_hp_calculation_martyr_lv15(self) -> None:
        # base=70, hp_growth=12, lv=15, DEF=90
        # 70 + 12*15 + int(90*1.5) = 70 + 180 + 135 = 385
        assert calculate_max_hp(base_hp=70, hp_growth=12, level=15, effective_def=90) == 385

    def test_hp_calculation_berserker_lv15(self) -> None:
        # base=25, hp_growth=4, lv=15, DEF=15
        # 25 + 4*15 + int(15*1.5) = 25 + 60 + 22 = 107
        assert calculate_max_hp(base_hp=25, hp_growth=4, level=15, effective_def=15) == 107


# --------------------------------------------------------- Stats at Level


class TestStatsAtLevel:
    def test_stats_at_level_einherjar_lv15(self) -> None:
        # Growth(STR=4,MAG=0,DEF=4,RES=0,SPD=2) -> effective = (5,1,5,1,3)
        # At lv15: STR=75, MAG=15, DEF=75, RES=15, SPD=45
        growth = GrowthVector(STR=4, MAG=0, DEF=4, RES=0, SPD=2)
        stats = calculate_stats_at_level(growth, level=15)
        assert stats.STR == 75
        assert stats.MAG == 15
        assert stats.DEF == 75
        assert stats.RES == 15
        assert stats.SPD == 45

    def test_stats_at_level_berserker_lv99(self) -> None:
        # Growth(STR=4,MAG=0,DEF=0,RES=0,SPD=6) -> effective = (5,1,1,1,7)
        # At lv99: STR=495, MAG=99, DEF=99, RES=99, SPD=693
        growth = GrowthVector(STR=4, MAG=0, DEF=0, RES=0, SPD=6)
        stats = calculate_stats_at_level(growth, level=99)
        assert stats.STR == 495
        assert stats.MAG == 99
        assert stats.DEF == 99
        assert stats.RES == 99
        assert stats.SPD == 693

    def test_stats_at_level_martyr_lv50(self) -> None:
        # Growth(STR=0,MAG=0,DEF=5,RES=4,SPD=1) -> effective = (1,1,6,5,2)
        # At lv50: STR=50, MAG=50, DEF=300, RES=250, SPD=100
        growth = GrowthVector(STR=0, MAG=0, DEF=5, RES=4, SPD=1)
        stats = calculate_stats_at_level(growth, level=50)
        assert stats.STR == 50
        assert stats.MAG == 50
        assert stats.DEF == 300
        assert stats.RES == 250
        assert stats.SPD == 100


# ------------------------------------------------------- Physical Damage


class TestPhysicalDamage:
    def test_physical_damage_basic(self) -> None:
        # ability_base=20, coeff=1.0, STR=75, DEF=60
        # raw = 20 + 1.0*75 = 95, reduction = 60*0.5 = 30, result = 65
        result = calculate_physical_damage(
            ability_base=20,
            ability_coefficient=1.0,
            attacker_str=75,
            target_def=60,
        )
        assert result == 65

    def test_physical_damage_chip(self) -> None:
        # High DEF ensures raw < reduction, should clamp to min 1
        result = calculate_physical_damage(
            ability_base=5,
            ability_coefficient=1.0,
            attacker_str=10,
            target_def=500,
        )
        assert result == 1

    def test_physical_damage_with_pierce(self) -> None:
        # pierce_percent=0.5 halves effective DEF
        # raw = 20 + 1.0*75 = 95
        # effective_def = 60 * 0.5 * (1 - 0.5) = 15, result = 80
        result = calculate_physical_damage(
            ability_base=20,
            ability_coefficient=1.0,
            attacker_str=75,
            target_def=60,
            pierce_percent=0.5,
        )
        assert result == 80


# ------------------------------------------------------- Magical Damage


class TestMagicalDamage:
    def test_magical_damage_no_res(self) -> None:
        # ability_base=20, coeff=1.0, MAG=75, RES=0 -> 20 + 75 = 95
        result = calculate_magical_damage(
            ability_base=20,
            ability_coefficient=1.0,
            attacker_mag=75,
        )
        assert result == 95

    def test_magical_damage_with_res_reduction(self) -> None:
        # raw = 20 + 75 = 95, reduction = 40 * 0.5 = 20, result = 75
        result = calculate_magical_damage(
            ability_base=20,
            ability_coefficient=1.0,
            attacker_mag=75,
            target_res=40,
        )
        assert result == 75

    def test_magical_damage_with_pierce(self) -> None:
        # raw = 20 + 75 = 95, effective_res = 40 * 0.5 * (1 - 0.5) = 10, result = 85
        result = calculate_magical_damage(
            ability_base=20,
            ability_coefficient=1.0,
            attacker_mag=75,
            target_res=40,
            pierce_percent=0.5,
        )
        assert result == 85

    def test_magical_damage_floors_at_one(self) -> None:
        # raw = 5 + 5 = 10, reduction = 100 * 0.5 = 50, result = max(1, -40) = 1
        result = calculate_magical_damage(
            ability_base=5,
            ability_coefficient=1.0,
            attacker_mag=5,
            target_res=100,
        )
        assert result == 1


# ----------------------------------------------------------- RES Gate


class TestResGate:
    def test_res_gate_passes(self) -> None:
        # target RES=75, caster MAG=100, threshold 0.7
        # 75 >= 100*0.7 = 70 -> True (resisted)
        assert check_res_gate(target_res=75, caster_mag=100) is True

    def test_res_gate_fails(self) -> None:
        # target RES=15, caster MAG=75, threshold 0.7
        # 15 < 75*0.7 = 52.5 -> False (not resisted)
        assert check_res_gate(target_res=15, caster_mag=75) is False


# ------------------------------------------------------ SPD Bonus Actions


class TestSpeedBonus:
    """Speed differential bonus actions: 2x → +1, 8x → +2, 32x → +3 (odd-power exponential)."""

    def test_no_bonus_below_threshold(self) -> None:
        assert calculate_speed_bonus(combatant_spd=7, slowest_opponent_spd=5) == 0

    def test_bonus_at_2x(self) -> None:
        assert calculate_speed_bonus(combatant_spd=10, slowest_opponent_spd=5) == 1

    def test_still_1_at_4x(self) -> None:
        # 4x no longer grants +2 under new scaling
        assert calculate_speed_bonus(combatant_spd=20, slowest_opponent_spd=5) == 1

    def test_bonus_at_8x(self) -> None:
        assert calculate_speed_bonus(combatant_spd=40, slowest_opponent_spd=5) == 2

    def test_bonus_at_32x(self) -> None:
        assert calculate_speed_bonus(combatant_spd=160, slowest_opponent_spd=5) == 3

    def test_berserker_vs_slime(self) -> None:
        # Berserker lv1 SPD 7 vs slime SPD 2: ratio 3.5x → +1
        assert calculate_speed_bonus(combatant_spd=7, slowest_opponent_spd=2) == 1

    def test_einherjar_vs_slime(self) -> None:
        # Einherjar lv1 SPD 3 vs slime SPD 2: ratio 1.5x → 0
        assert calculate_speed_bonus(combatant_spd=3, slowest_opponent_spd=2) == 0

    def test_zero_opponent_spd(self) -> None:
        assert calculate_speed_bonus(combatant_spd=10, slowest_opponent_spd=0) == 0


# ------------------------------------------------- Damage Modifiers


class TestDamageModifiers:
    def test_survive_damage_reduction(self) -> None:
        # 100 damage -> 50 when surviving (50% reduction)
        assert apply_survive_reduction(damage=100, is_surviving=True) == 50

    def test_survive_no_reduction_when_not_surviving(self) -> None:
        assert apply_survive_reduction(damage=100, is_surviving=False) == 100


# ---------------------------------------------------- Enemy Stats


class TestEnemyStats:
    def test_enemy_stats_brute_zone15(self) -> None:
        # budget_multiplier=14.0, zone=15 -> total_budget = int(15*14.0) = 210
        # stat_dist: STR=0.33, MAG=0.05, DEF=0.29, RES=0.05, SPD=0.07
        # STR = int(210*0.33) = 69, MAG = int(210*0.05) = 10,
        # DEF = int(210*0.29) = 60, RES = int(210*0.05) = 10,
        # SPD = int(210*0.07) = 14
        stat_dist = {"STR": 0.33, "MAG": 0.05, "DEF": 0.29, "RES": 0.05, "SPD": 0.07}
        stats = calculate_enemy_stats(
            enemy_level=15,
            budget_multiplier=14.0,
            stat_distribution=stat_dist,
        )
        assert stats.STR == 69
        assert stats.MAG == 10
        assert stats.DEF == 60
        assert stats.RES == 10
        assert stats.SPD == 14

    def test_enemy_hp(self) -> None:
        # zone=15, multiplier=14.0, base_hp=40, hp_per_budget=3.0
        # total_budget = int(15*14.0) = 210
        # hp = 40 + int(210*3.0) = 40 + 630 = 670
        hp = calculate_enemy_hp(
            enemy_level=15,
            budget_multiplier=14.0,
            base_hp=40,
            hp_per_budget=3.0,
        )
        assert hp == 670
