"""Target selectors for golden policies.

Each selector takes a ``RuleContext`` and returns a list of target IDs
ordered for the action being composed. For a cheat burst that needs
multiple targets (e.g. 4 attacks across 3 enemies), the selector
returns the full attack-order list.
"""

from __future__ import annotations


from heresiarch.engine.models.combat_state import CombatantState

from .predicates import GOLD_STEAL_ABILITY_ID, _is_healer, _is_mage, basic_attack_damage
from .rule_engine import RuleContext


def first_alive_enemy(ctx: RuleContext) -> str | None:
    if ctx.state.living_enemies:
        return ctx.state.living_enemies[0].id
    return None


def first_gold_thief(ctx: RuleContext) -> str | None:
    """First living enemy with a gold-stealing ability (e.g., bandit_slime).

    Designer's rule: kill gold-stealers preemptively — they weaken
    economy faster than they threaten HP.
    """
    for e in ctx.state.living_enemies:
        if GOLD_STEAL_ABILITY_ID in e.ability_ids:
            return e.id
    return None


def first_healer(ctx: RuleContext) -> str | None:
    """First living enemy with a healing ability (heal_percent > 0).

    Healers extend fights by undoing retaliate damage, making
    survive-only loops unwinnable. Burst them down first.
    """
    for e in ctx.state.living_enemies:
        if _is_healer(e, ctx.game_data):
            return e.id
    return None


def first_mage(ctx: RuleContext) -> str | None:
    """First living enemy with MAG-scaling offensive abilities.

    Mages bypass DEF, dealing disproportionate damage to physical
    characters. Share priority tier with healers for burst-down.
    """
    for e in ctx.state.living_enemies:
        if _is_mage(e, ctx.game_data):
            return e.id
    return None


def most_wounded_enemy(ctx: RuleContext) -> str | None:
    """Enemy with the lowest absolute HP — often the quickest finish."""
    if not ctx.state.living_enemies:
        return None
    return min(ctx.state.living_enemies, key=lambda e: e.current_hp).id


def weakest_by_max_hp(ctx: RuleContext) -> str | None:
    """Enemy with the lowest max_hp — the 'squishiest' target."""
    if not ctx.state.living_enemies:
        return None
    return min(ctx.state.living_enemies, key=lambda e: e.max_hp).id


def first_taunter(ctx: RuleContext) -> str | None:
    living_enemy_ids = {e.id for e in ctx.state.living_enemies}
    for tid in ctx.actor.taunted_by:
        if tid in living_enemy_ids:
            return tid
    return None


def self_target(ctx: RuleContext) -> str:
    return ctx.actor.id


# ---------------------------------------------------------------------------
# Multi-attack target sequences (for cheat bursts)
# ---------------------------------------------------------------------------


def sweep_attack_order(
    actor: CombatantState, enemies: list[CombatantState], attacks: int,
    damage_fn=None,
) -> list[str]:
    """Return a list of ``attacks`` target IDs that optimally assigns
    attacks to kill the lowest-HP enemies first.

    Weakest-first minimizes overkill and removes attacker slots fastest.
    If we have extra attacks after clearing all living enemies, we
    dogpile the highest-HP remaining one (benign — engine will ignore
    attacks vs dead targets but the order still front-loads useful work).

    ``damage_fn`` takes (actor, enemy) and returns damage estimate;
    defaults to basic_attack. Useful for thrust-based sweeps where
    the damage-per-attack varies by ability.
    """
    if attacks <= 0 or not enemies:
        return []

    dmg_fn = damage_fn or basic_attack_damage
    dmg_map = {e.id: max(1, dmg_fn(actor, e)) for e in enemies}
    remaining_hp = {e.id: e.current_hp for e in enemies}

    sorted_enemies = sorted(enemies, key=lambda e: e.current_hp)

    targets: list[str] = []
    for e in sorted_enemies:
        while remaining_hp[e.id] > 0 and len(targets) < attacks:
            targets.append(e.id)
            remaining_hp[e.id] -= dmg_map[e.id]

    # Surplus attacks: stack on whoever's tankiest remaining (or just
    # the last enemy if everyone's "dead" in our model).
    while len(targets) < attacks:
        living_by_hp = sorted(
            [e for e in enemies if remaining_hp[e.id] > 0],
            key=lambda e: remaining_hp[e.id],
            reverse=True,
        )
        if living_by_hp:
            targets.append(living_by_hp[0].id)
            remaining_hp[living_by_hp[0].id] -= dmg_map[living_by_hp[0].id]
        else:
            targets.append(sorted_enemies[-1].id)

    return targets[:attacks]
