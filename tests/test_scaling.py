"""Verify item scaling crossover table and converter formulas."""

import pytest

from heresiarch.engine.formulas import evaluate_conversion, evaluate_item_scaling
from heresiarch.engine.models.items import ConversionEffect, ItemScaling, ScalingType
from heresiarch.engine.models.stats import StatType


class TestLinearScaling:
    """LINEAR: base + linear_coeff * STAT"""

    def test_linear_at_str_15(self) -> None:
        scaling = ItemScaling(
            scaling_type=ScalingType.LINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=1.0,
        )
        assert evaluate_item_scaling(scaling, stat_value=15) == pytest.approx(35.0)

    def test_linear_at_str_75(self) -> None:
        scaling = ItemScaling(
            scaling_type=ScalingType.LINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=1.0,
        )
        assert evaluate_item_scaling(scaling, stat_value=75) == pytest.approx(95.0)

    def test_linear_at_str_175(self) -> None:
        scaling = ItemScaling(
            scaling_type=ScalingType.LINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=1.0,
        )
        assert evaluate_item_scaling(scaling, stat_value=175) == pytest.approx(195.0)

    def test_linear_at_str_495(self) -> None:
        scaling = ItemScaling(
            scaling_type=ScalingType.LINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=1.0,
        )
        assert evaluate_item_scaling(scaling, stat_value=495) == pytest.approx(515.0)


class TestSuperlinearScaling:
    """SUPERLINEAR: base + linear_coeff * STAT + quadratic_coeff * STAT^2

    Crossover with LINEAR (base=20, coeff=1.0) happens around STR ~175.
    """

    def _make_scaling(self) -> ItemScaling:
        return ItemScaling(
            scaling_type=ScalingType.SUPERLINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=0.3,
            quadratic_coeff=0.004,
        )

    def test_superlinear_at_str_15(self) -> None:
        # 20 + 0.3*15 + 0.004*225 = 20 + 4.5 + 0.9 = 25.4
        result = evaluate_item_scaling(self._make_scaling(), stat_value=15)
        assert result == pytest.approx(25.4)

    def test_superlinear_at_str_75(self) -> None:
        # 20 + 0.3*75 + 0.004*5625 = 20 + 22.5 + 22.5 = 65.0
        result = evaluate_item_scaling(self._make_scaling(), stat_value=75)
        assert result == pytest.approx(65.0)

    def test_superlinear_at_str_175(self) -> None:
        # 20 + 0.3*175 + 0.004*30625 = 20 + 52.5 + 122.5 = 195.0
        # Matches LINEAR's 195 at this crossover point
        result = evaluate_item_scaling(self._make_scaling(), stat_value=175)
        assert result == pytest.approx(195.0)

    def test_superlinear_at_str_495(self) -> None:
        # 20 + 0.3*495 + 0.004*245025 = 20 + 148.5 + 980.1 = 1148.6
        result = evaluate_item_scaling(self._make_scaling(), stat_value=495)
        assert result == pytest.approx(1148.6)

    def test_crossover_with_linear(self) -> None:
        """At STR=175, superlinear matches linear (both produce 195)."""
        linear = ItemScaling(
            scaling_type=ScalingType.LINEAR,
            stat=StatType.STR,
            base=20.0,
            linear_coeff=1.0,
        )
        superlinear = self._make_scaling()
        linear_val = evaluate_item_scaling(linear, stat_value=175)
        super_val = evaluate_item_scaling(superlinear, stat_value=175)
        assert linear_val == pytest.approx(super_val)


class TestQuadraticScaling:
    """QUADRATIC: base + quadratic_coeff * STAT^2"""

    def _make_scaling(self) -> ItemScaling:
        return ItemScaling(
            scaling_type=ScalingType.QUADRATIC,
            stat=StatType.STR,
            base=20.0,
            quadratic_coeff=0.008,
        )

    def test_quadratic_at_str_75(self) -> None:
        # 20 + 0.008*5625 = 20 + 45 = 65.0
        result = evaluate_item_scaling(self._make_scaling(), stat_value=75)
        assert result == pytest.approx(65.0)

    def test_quadratic_at_str_250(self) -> None:
        # 20 + 0.008*62500 = 20 + 500 = 520.0
        result = evaluate_item_scaling(self._make_scaling(), stat_value=250)
        assert result == pytest.approx(520.0)

    def test_quadratic_at_str_495(self) -> None:
        # 20 + 0.008*245025 = 20 + 1960.2 = 1980.2
        result = evaluate_item_scaling(self._make_scaling(), stat_value=495)
        assert result == pytest.approx(1980.2)


class TestDegenerateScaling:
    """DEGENERATE: constant_offset + quadratic_coeff * STAT^2"""

    def _make_scaling(self) -> ItemScaling:
        return ItemScaling(
            scaling_type=ScalingType.DEGENERATE,
            stat=StatType.STR,
            constant_offset=-200.0,
            quadratic_coeff=0.01,
        )

    def test_degenerate_at_str_15(self) -> None:
        # -200 + 0.01*225 = -200 + 2.25 = -197.75
        result = evaluate_item_scaling(self._make_scaling(), stat_value=15)
        assert result == pytest.approx(-197.75)

    def test_degenerate_at_str_75(self) -> None:
        # -200 + 0.01*5625 = -200 + 56.25 = -143.75
        result = evaluate_item_scaling(self._make_scaling(), stat_value=75)
        assert result == pytest.approx(-143.75)

    def test_degenerate_at_str_150(self) -> None:
        # -200 + 0.01*22500 = -200 + 225 = 25.0
        result = evaluate_item_scaling(self._make_scaling(), stat_value=150)
        assert result == pytest.approx(25.0)

    def test_degenerate_at_str_495(self) -> None:
        # -200 + 0.01*245025 = -200 + 2450.25 = 2250.25
        result = evaluate_item_scaling(self._make_scaling(), stat_value=495)
        assert result == pytest.approx(2250.25)


class TestConversion:
    """evaluate_conversion: converter item bonuses."""

    def test_quadratic_conversion_def_90(self) -> None:
        # quadratic_coeff=0.004, source DEF=90 -> int(0.004 * 8100) = int(32.4) = 32
        conv = ConversionEffect(
            source_stat=StatType.DEF,
            target_stat=StatType.STR,
            scaling_type=ScalingType.QUADRATIC,
            quadratic_coeff=0.004,
        )
        assert evaluate_conversion(conv, source_stat_value=90) == 32

    def test_linear_conversion_spd_105(self) -> None:
        # linear_coeff=0.3, source SPD=105 -> int(0.3 * 105) = int(31.5) = 31
        conv = ConversionEffect(
            source_stat=StatType.SPD,
            target_stat=StatType.STR,
            scaling_type=ScalingType.LINEAR,
            linear_coeff=0.3,
        )
        assert evaluate_conversion(conv, source_stat_value=105) == 31
