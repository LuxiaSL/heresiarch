"""Shared helpers for simulation tools and dashboard.

Contains damage computation helpers used by both tools/sim.py and
dashboard/core/sim_service.py. These call engine formulas but don't
depend on combat state.
"""

from heresiarch.engine.formulas import (
    calculate_magical_damage,
    calculate_physical_damage,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityEffect,
    DamageQuality,
)
from heresiarch.engine.models.stats import StatType


def compute_effect_damage(
    effect: AbilityEffect,
    attacker_str: int,
    attacker_mag: int,
    enemy_def: int,
) -> int:
    """Compute raw damage for a single effect using game formulas.

    Mirrors CombatEngine._calculate_damage but without combat state deps.
    """
    if effect.base_damage == 0 and effect.scaling_coefficient == 0:
        return 0

    if effect.stat_scaling == StatType.MAG:
        return calculate_magical_damage(
            ability_base=effect.base_damage,
            ability_coefficient=effect.scaling_coefficient,
            attacker_mag=attacker_mag,
        )
    else:
        # STR scaling (also the default for None stat_scaling)
        return calculate_physical_damage(
            ability_base=effect.base_damage,
            ability_coefficient=effect.scaling_coefficient,
            attacker_str=attacker_str,
            target_def=enemy_def,
            pierce_percent=effect.pierce_percent,
        )


def compute_ability_total_damage(
    ability: Ability,
    attacker_str: int,
    attacker_mag: int,
    enemy_def: int,
) -> int:
    """Compute total raw damage for all effects of an ability (single use, no stacks)."""
    total = 0
    for effect in ability.effects:
        dmg = compute_effect_damage(effect, attacker_str, attacker_mag, enemy_def)
        # Apply chain damage ratio inline (CHAIN reduces per-hit)
        if effect.quality == DamageQuality.CHAIN and dmg > 0:
            dmg = max(1, int(dmg * effect.chain_damage_ratio))
        total += dmg
    return total
