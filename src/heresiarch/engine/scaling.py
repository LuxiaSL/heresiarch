"""Item scaling evaluation — wraps formulas for convenience."""

from __future__ import annotations

from heresiarch.engine.formulas import evaluate_conversion, evaluate_item_scaling
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.stats import StatBlock, StatType


def evaluate_weapon_damage(item: Item, wielder_stats: StatBlock) -> float:
    """Evaluate a weapon's damage contribution given the wielder's stats.

    Returns the bonus damage from the item's scaling formula.
    Returns 0 if the item has no scaling.
    """
    if item.scaling is None:
        return 0.0

    stat_value = wielder_stats.get(StatType(item.scaling.stat.value))
    return evaluate_item_scaling(item.scaling, stat_value)


def evaluate_converter_bonus(item: Item, wielder_stats: StatBlock) -> dict[str, int]:
    """Evaluate a converter item's stat bonuses.

    Returns a dict of {stat_name: bonus_value} for the target stat.
    Returns empty dict if item has no conversion.
    """
    if item.conversion is None:
        return {}

    source_value = wielder_stats.get(StatType(item.conversion.source_stat.value))
    bonus = evaluate_conversion(item.conversion, source_value)

    return {item.conversion.target_stat.value: bonus}
