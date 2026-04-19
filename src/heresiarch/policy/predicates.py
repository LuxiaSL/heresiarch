"""Predicate helpers for golden policies.

Functions here read ``RuleContext`` and return bool (for rule predicates)
or numeric estimates (for threshold checks). Kept independent of any
specific job so they're reusable across all goldens.

Damage estimation uses the same formulas the engine uses, so estimates
match actual outcomes to within rounding. Effective stats already
include equipment contributions, so no extra item_scaling_bonus math
is needed here.
"""

from __future__ import annotations

import math

from heresiarch.engine.formulas import (
    DEF_REDUCTION_RATIO,
    calculate_communion_multiplier,
    calculate_frenzy_multiplier,
    calculate_insight_multiplier,
    calculate_magical_damage,
    calculate_physical_damage,
    calculate_speed_bonus,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    DamageQuality,
    TriggerCondition,
)
from heresiarch.engine.models.combat_state import CombatantState
from heresiarch.engine.models.stats import StatType

from .rule_engine import RuleContext


# Boss heuristic: a "boss" encounter is a single living enemy whose
# max_hp exceeds this threshold. Matches zone_02 omega_slime (284 max_hp),
# zone_01 alpha_slime (90), and zone_03 kodama_elder (327). Single-target
# zone_03 elites like speeder_tengu may also cross this bar, which is
# fine for policy purposes — they warrant the same opener treatment.
BOSS_MAX_HP_THRESHOLD: int = 90

# Gold-thief archetype marker. Any living enemy with ``pilfer`` in its
# ability list is treated as a gold-stealer (currently only bandit_slime,
# but open to future archetypes that share the behavior).
GOLD_STEAL_ABILITY_ID: str = "pilfer"


# ---------------------------------------------------------------------------
# State-based predicates
# ---------------------------------------------------------------------------


def hp_pct_below(ctx: RuleContext, threshold: float) -> bool:
    """True when actor HP fraction is strictly below threshold."""
    return ctx.actor.current_hp / max(1, ctx.actor.max_hp) < threshold


def ap_at_least(ctx: RuleContext, n: int) -> bool:
    return ctx.actor.action_points >= n


def am_taunted(ctx: RuleContext) -> bool:
    """True when at least one living enemy has taunted us."""
    if not ctx.actor.taunted_by:
        return False
    living_enemy_ids = {e.id for e in ctx.state.living_enemies}
    return any(tid in living_enemy_ids for tid in ctx.actor.taunted_by)


def ability_ready(ctx: RuleContext, ability_id: str) -> bool:
    """True when actor knows the ability and it's off cooldown."""
    if ability_id not in ctx.actor.ability_ids:
        return False
    return ctx.actor.cooldowns.get(ability_id, 0) == 0


def has_item(ctx: RuleContext, item_id: str) -> bool:
    return item_id in ctx.legal.available_consumable_ids


def enemy_count(ctx: RuleContext) -> int:
    return len(ctx.state.living_enemies)


# ---------------------------------------------------------------------------
# Damage / threat estimation
# ---------------------------------------------------------------------------


def estimate_damage(
    attacker: CombatantState,
    target: CombatantState,
    ability_base: int = 5,
    ability_coefficient: float = 0.5,
    stat: str = "STR",
    pierce_percent: float = 0.0,
) -> int:
    """Estimate damage of a hypothetical ability invocation.

    Defaults to basic_attack parameters (5 + 0.5 × STR). Override for
    other abilities. Uses the same formulas the engine uses, so the
    estimate matches the actual damage to within rounding.
    """
    if stat == "STR" or stat == "DEF":
        attacker_stat = (
            attacker.effective_stats.STR if stat == "STR"
            else attacker.effective_stats.DEF
        )
        return calculate_physical_damage(
            ability_base=ability_base,
            ability_coefficient=ability_coefficient,
            attacker_str=attacker_stat,
            target_def=target.effective_stats.DEF,
            pierce_percent=pierce_percent,
            def_reduction_ratio=DEF_REDUCTION_RATIO + target.extra_def_reduction,
        )
    # MAG/RES
    attacker_stat = (
        attacker.effective_stats.MAG if stat == "MAG"
        else attacker.effective_stats.RES
    )
    return calculate_magical_damage(
        ability_base=ability_base,
        ability_coefficient=ability_coefficient,
        attacker_mag=attacker_stat,
        target_res=target.effective_stats.RES,
        pierce_percent=pierce_percent,
    )


def basic_attack_damage(actor: CombatantState, target: CombatantState) -> int:
    """Estimated basic_attack damage against a specific target."""
    return estimate_damage(
        actor, target,
        ability_base=5, ability_coefficient=0.5, stat="STR",
    )


def thrust_damage(actor: CombatantState, target: CombatantState) -> int:
    """Estimated thrust damage against a specific target.

    Thrust: 8 + 0.5×STR, pierces 40% of target DEF. Typically beats
    basic_attack against high-DEF targets (chunky_slime, brute_oni).
    """
    return estimate_damage(
        actor, target,
        ability_base=8, ability_coefficient=0.5, stat="STR",
        pierce_percent=0.4,
    )


def heavy_strike_damage(actor: CombatantState, target: CombatantState) -> int:
    """Estimated heavy_strike damage. 15 + 0.8×STR, no pierce."""
    return estimate_damage(
        actor, target,
        ability_base=15, ability_coefficient=0.8, stat="STR",
    )


def brace_strike_damage(actor: CombatantState, target: CombatantState) -> int:
    """Estimated brace_strike damage. 8 + 0.4×STR (also grants +15 DEF)."""
    return estimate_damage(
        actor, target,
        ability_base=8, ability_coefficient=0.4, stat="STR",
    )


def can_cheat_sweep_all(ctx: RuleContext, attacks_available: int = 4) -> bool:
    """True if ``attacks_available`` basic_attacks can kill every living enemy.

    Targets weakest-first (minimizes wasted overkill), then stacks
    remaining hits on the strongest. If total hits needed ≤ budget,
    we can sweep.

    Retained for backwards compatibility with the v3 rule table; new
    rules should prefer :func:`can_kill_all_with_attacks` which accepts
    a caller-supplied damage function to model non-basic primaries.
    """
    return can_kill_all_with_attacks(ctx, attacks_available)


def can_kill_all_with_attacks(
    ctx: RuleContext,
    attacks_available: int,
    damage_fn=None,
) -> bool:
    """True if ``attacks_available`` attacks can kill every living enemy.

    ``damage_fn`` takes (actor, enemy) and returns estimated damage.
    Defaults to basic_attack_damage. Targets weakest-first.
    """
    if attacks_available <= 0:
        return False
    enemies = ctx.state.living_enemies
    if not enemies:
        return False

    dmg_fn = damage_fn or basic_attack_damage
    total_hits = 0
    for enemy in sorted(enemies, key=lambda e: e.current_hp):
        dmg = max(1, dmg_fn(ctx.actor, enemy))
        total_hits += math.ceil(enemy.current_hp / dmg)
        if total_hits > attacks_available:
            return False
    return total_hits <= attacks_available


def speed_bonus_slots(ctx: RuleContext) -> int:
    """Number of speed-bonus action slots the MC gets this turn.

    Matches the engine's calculation in :func:`combat.process_round`:
    uses the slowest living enemy's SPD as the denominator. Only applies
    to CHEAT or NORMAL turns — the engine zeroes it on SURVIVE.
    """
    enemies = ctx.state.living_enemies
    if not enemies:
        return 0
    slowest_enemy_spd = min(e.effective_stats.SPD for e in enemies)
    return calculate_speed_bonus(
        ctx.actor.effective_stats.SPD, slowest_enemy_spd,
    )


def minimum_ap_to_kill_all(
    ctx: RuleContext,
    primary_damage_fn=None,
    extras_damage_fn=None,
    primary_target_id: str | None = None,
) -> int | None:
    """Minimum AP to spend so (1 primary + N cheat extras + bonus slots)
    kills every living enemy this round.

    Returns None if no number of attacks (within the AP+bonus cap) can
    finish, or 0 if a single primary + bonus slots already finishes.

    Caller provides damage functions for the primary and extras so the
    estimate accounts for mixed ability use (e.g., thrust primary +
    basic_attack extras).

    ``primary_target_id``: when set, the primary attack goes on this
    specific target and extras sweep the rest weakest-first. This aligns
    the predicate's model with the action builder's actual execution
    order. When None, the primary goes on the weakest enemy (legacy
    behavior).

    The engine caps ``cheat_actions`` at the combatant's current AP and
    at ``MAX_ACTION_POINT_BANK``; we respect the current_ap ceiling here.
    """
    primary_fn = primary_damage_fn or basic_attack_damage
    extras_fn = extras_damage_fn or basic_attack_damage
    max_ap = ctx.actor.action_points
    bonus = speed_bonus_slots(ctx)

    for cheat_n in range(0, max_ap + 1):
        total_attacks = 1 + cheat_n + bonus
        if _can_kill_with_mixed(
            ctx, total_attacks, primary_fn, extras_fn,
            primary_target_id=primary_target_id,
        ):
            return cheat_n
    return None


def minimum_ap_to_kill_single(
    ctx: RuleContext,
    target: CombatantState,
    primary_damage_fn=None,
    extras_damage_fn=None,
) -> int | None:
    """Minimum AP to kill one specific target with available actions.

    All attacks (primary + extras + bonus) focus on the single target.
    Returns the AP spend needed, or None if impossible within current AP.
    """
    primary_fn = primary_damage_fn or basic_attack_damage
    extras_fn = extras_damage_fn or basic_attack_damage
    max_ap = ctx.actor.action_points
    bonus = speed_bonus_slots(ctx)

    primary_dmg = max(1, primary_fn(ctx.actor, target))
    extras_dmg = max(1, extras_fn(ctx.actor, target))

    for cheat_n in range(0, max_ap + 1):
        total_attacks = 1 + cheat_n + bonus
        total_dmg = primary_dmg + (total_attacks - 1) * extras_dmg
        if total_dmg >= target.current_hp:
            return cheat_n
    return None


def _can_kill_with_mixed(
    ctx: RuleContext,
    attacks_available: int,
    primary_fn,
    extras_fn,
    primary_target_id: str | None = None,
) -> bool:
    """Mixed-damage sweep check: one primary_fn attack + (N-1) extras_fn.

    When ``primary_target_id`` is set, the primary goes on that specific
    target and extras sweep the remaining enemies weakest-first. This
    matches the action builder's actual execution order. When None, the
    primary goes on the weakest enemy (legacy behavior).
    """
    if attacks_available <= 0:
        return False
    enemies = ctx.state.living_enemies
    if not enemies:
        return False

    remaining_hp = {e.id: e.current_hp for e in enemies}
    attacks_left = attacks_available

    if primary_target_id is not None:
        primary_target = next(
            (e for e in enemies if e.id == primary_target_id), None,
        )
        if primary_target is not None:
            dmg = max(1, primary_fn(ctx.actor, primary_target))
            remaining_hp[primary_target.id] -= dmg
            attacks_left -= 1

        for e in sorted(enemies, key=lambda e: remaining_hp[e.id]):
            while remaining_hp[e.id] > 0 and attacks_left > 0:
                dmg = max(1, extras_fn(ctx.actor, e))
                remaining_hp[e.id] -= dmg
                attacks_left -= 1
            if remaining_hp[e.id] > 0:
                return False
        return True

    sorted_enemies = sorted(enemies, key=lambda e: e.current_hp)
    primary_used = False

    for e in sorted_enemies:
        while remaining_hp[e.id] > 0 and attacks_left > 0:
            if not primary_used:
                dmg = max(1, primary_fn(ctx.actor, e))
                primary_used = True
            else:
                dmg = max(1, extras_fn(ctx.actor, e))
            remaining_hp[e.id] -= dmg
            attacks_left -= 1
        if remaining_hp[e.id] > 0:
            return False
    return True


def is_boss_encounter(ctx: RuleContext) -> bool:
    """True for single high-HP-target encounters — boss fights.

    Heuristic: exactly one living enemy with max_hp at or above the
    boss threshold. Multi-enemy encounters (including boss+minion
    compositions after minions die down to one tough target) naturally
    transition into this state late-fight, which is when the tonic
    opener and cheat-heal rules become relevant anyway.
    """
    enemies = ctx.state.living_enemies
    if len(enemies) != 1:
        return False
    return enemies[0].max_hp >= BOSS_MAX_HP_THRESHOLD


def ability_damage(
    attacker: CombatantState,
    target: CombatantState,
    ability: Ability,
) -> int:
    """Total damage of one ability application against target.

    Sums all damage-dealing effects on the ability. Uses the engine's
    exact damage formulas (calculate_physical_damage /
    calculate_magical_damage) — no approximations.

    Handles:
      - Single-effect abilities (basic_attack, heavy_strike, etc.)
      - Multi-effect abilities (double_hit's two hits)
      - PIERCE quality (pierce_percent of target DEF ignored)
      - CHAIN quality (chain_damage_ratio applied to base)

    Ignores non-damage effects (pure buffs/debuffs/heals).
    """
    total = 0
    for effect in ability.effects:
        # Non-damage effect (pure buff / debuff / heal / status)
        if effect.base_damage == 0 and effect.scaling_coefficient == 0:
            continue
        if effect.stat_scaling is None:
            continue

        stat = effect.stat_scaling.value
        dmg = estimate_damage(
            attacker, target,
            ability_base=effect.base_damage,
            ability_coefficient=effect.scaling_coefficient,
            stat=stat,
            pierce_percent=effect.pierce_percent,
        )
        if effect.quality == DamageQuality.CHAIN:
            dmg = int(dmg * effect.chain_damage_ratio)
        total += max(0, dmg)
    return total


# ---------------------------------------------------------------------------
# Passive-aware damage estimation
# ---------------------------------------------------------------------------


def _has_trigger_passive(
    actor: CombatantState,
    trigger: TriggerCondition,
    game_data,
) -> bool:
    """True if the actor has a passive with the given trigger."""
    for aid in actor.ability_ids:
        ab = game_data.abilities.get(aid)
        if ab is None:
            continue
        if ab.category == AbilityCategory.PASSIVE and ab.trigger == trigger:
            return True
    return False


def passive_multiplier(
    actor: CombatantState,
    attack_index: int,
    game_data,
    *,
    ability: Ability | None = None,
) -> float:
    """Combined passive damage multiplier for the Nth attack in a sequence.

    Accounts for:
      - Frenzy (ON_CONSECUTIVE_ATTACK): exponential scaling per chain position
      - Insight (ON_NON_DAMAGE_ACTION): first attack amplified by stacks
      - Communion (ON_DAMAGE_MODIFY): MAG abilities amplified by missing HP
    """
    mult = 1.0

    # Frenzy: chain grows with each consecutive attack
    if _has_trigger_passive(actor, TriggerCondition.ON_CONSECUTIVE_ATTACK, game_data):
        chain = actor.frenzy_chain + attack_index + 1
        mult *= calculate_frenzy_multiplier(chain)

    # Insight: only the first attack in the sequence gets amplified
    if (
        attack_index == 0
        and actor.insight_stacks > 0
        and _has_trigger_passive(actor, TriggerCondition.ON_NON_DAMAGE_ACTION, game_data)
    ):
        mult *= calculate_insight_multiplier(actor.insight_stacks)

    # Communion: MAG abilities amplified by missing HP fraction
    if _has_trigger_passive(actor, TriggerCondition.ON_DAMAGE_MODIFY, game_data):
        if ability is not None:
            is_mag = any(
                e.stat_scaling == StatType.MAG
                for e in ability.effects
                if e.base_damage > 0 or e.scaling_coefficient > 0
            )
            if is_mag:
                mult *= calculate_communion_multiplier(
                    actor.current_hp, actor.max_hp,
                )

    return mult


def estimated_sequence_damage(
    actor: CombatantState,
    targets: list[CombatantState],
    n_attacks: int,
    game_data,
    *,
    damage_fn=None,
    ability: Ability | None = None,
) -> int:
    """Total damage for N sequential attacks accounting for passives.

    Distributes attacks across targets (cycling if fewer targets than
    attacks) and applies frenzy/insight/communion multipliers at each
    attack position. Returns total estimated damage.
    """
    if n_attacks <= 0 or not targets:
        return 0

    dmg_fn = damage_fn or basic_attack_damage
    total = 0
    for i in range(n_attacks):
        target = targets[i % len(targets)]
        base = max(1, dmg_fn(actor, target))
        mult = passive_multiplier(actor, i, game_data, ability=ability)
        total += int(base * mult)
    return total


def passive_aware_kill_check(
    ctx: RuleContext,
    n_attacks: int,
    game_data,
    *,
    damage_fn=None,
    ability: Ability | None = None,
) -> bool:
    """True if N passive-scaled attacks can kill all living enemies.

    Allocates attacks weakest-first with frenzy/insight/communion
    multipliers applied at each chain position.
    """
    if n_attacks <= 0:
        return False
    enemies = ctx.state.living_enemies
    if not enemies:
        return False

    dmg_fn = damage_fn or basic_attack_damage
    remaining_hp = {e.id: e.current_hp for e in enemies}
    sorted_enemies = sorted(enemies, key=lambda e: e.current_hp)
    attack_idx = 0

    for e in sorted_enemies:
        while remaining_hp[e.id] > 0 and attack_idx < n_attacks:
            base = max(1, dmg_fn(ctx.actor, e))
            mult = passive_multiplier(
                ctx.actor, attack_idx, game_data, ability=ability,
            )
            remaining_hp[e.id] -= int(base * mult)
            attack_idx += 1
        if remaining_hp[e.id] > 0:
            return False
    return True


def minimum_ap_to_kill_all_passive(
    ctx: RuleContext,
    game_data,
    *,
    damage_fn=None,
    ability: Ability | None = None,
) -> int | None:
    """Passive-aware version of minimum_ap_to_kill_all.

    Accounts for frenzy chain scaling, insight amplification, and
    communion damage bonus when estimating whether N attacks can
    kill all enemies.
    """
    max_ap = ctx.actor.action_points
    bonus = speed_bonus_slots(ctx)

    for cheat_n in range(0, max_ap + 1):
        total_attacks = 1 + cheat_n + bonus
        if passive_aware_kill_check(
            ctx, total_attacks, game_data,
            damage_fn=damage_fn, ability=ability,
        ):
            return cheat_n
    return None


def max_damage_per_turn(
    enemy: CombatantState,
    target: CombatantState,
    game_data,
) -> int:
    """Max damage enemy could deal to target on their next immediate turn.

    Worst-case analysis: max over all offensive abilities the enemy
    knows. Used for the designer's heal rule — "if their max damage
    kills you this turn, heal now."

    Charging/windup handling:
      - Enemy mid-charge (charge_turns_remaining > 0): no damage this
        turn; the release fires later.
      - Enemy releasing a charge (charging_ability_id set, turns=0):
        damage = that charged ability's damage.
      - Enemy not charging: max over all non-windup abilities.
    """
    # Mid-charge: no immediate damage.
    if enemy.charge_turns_remaining > 0:
        return 0

    # Releasing a charged ability this turn: exact damage is that ability.
    if enemy.charging_ability_id:
        ability = game_data.abilities.get(enemy.charging_ability_id)
        if ability is not None:
            return ability_damage(enemy, target, ability)
        return 0

    # Normal turn: worst case over instant (non-windup) abilities.
    max_dmg = 0
    for aid in enemy.ability_ids:
        ability = game_data.abilities.get(aid)
        if ability is None:
            continue
        if ability.category != AbilityCategory.OFFENSIVE:
            continue
        if ability.windup_turns > 0:
            # Starting a windup this turn deals no damage immediately.
            continue
        dmg = ability_damage(enemy, target, ability)
        if dmg > max_dmg:
            max_dmg = dmg
    return max_dmg


def projected_incoming_damage(ctx: RuleContext) -> int:
    """Sum of each living enemy's max-per-turn damage against the actor.

    Per the designer: if the enemy is faster than the actor, they get
    to hit twice before the actor can act again (once this turn before
    the actor's heal lands, once next turn before the actor's next
    action). So their contribution is doubled.

    "Faster" = strictly greater effective_stats.SPD.

    Used to implement the heal rule: "if i am going to die to the next
    hit, or die before i can heal, then i need to heal now."
    """
    total = 0
    actor_spd = ctx.actor.effective_stats.SPD
    for enemy in ctx.state.living_enemies:
        max_dmg = max_damage_per_turn(enemy, ctx.actor, ctx.game_data)
        multiplier = 2 if enemy.effective_stats.SPD > actor_spd else 1
        total += max_dmg * multiplier
    return total


def has_gold_thief_enemy(ctx: RuleContext) -> bool:
    """True when any living enemy can steal gold (has pilfer ability).

    Designer's rule: "nuke bandit_slime right off the bat because it
    steals ~a minor potion's worth of gold." Generalized to any gold
    stealer so future archetypes inherit the priority.
    """
    return any(
        GOLD_STEAL_ABILITY_ID in e.ability_ids
        for e in ctx.state.living_enemies
    )


def expected_incoming_damage(ctx: RuleContext) -> int:
    """Sum of each living enemy's basic_attack damage vs the actor.

    Rough proxy for "next round's incoming damage" — enemies may actually
    use abilities, but basic_attack is usually on their fallback branch
    and serves as a lower-bound estimate.
    """
    total = 0
    for enemy in ctx.state.living_enemies:
        total += estimate_damage(enemy, ctx.actor)
    return total


def two_hits_would_kill(
    ctx: RuleContext, hp_pct_floor: float = 0.40,
) -> bool:
    """True if two rounds of incoming damage would drop actor to ≤0 HP.

    Matches the einherjar playstyle rule: "when 2 enemy attacks would
    kill you, you heal."

    ``expected_incoming_damage`` only models basic_attack; enemies with
    heavy ability branches (heavy_strike, charged abilities) hit
    considerably harder. To guard against under-estimate, we also
    heal unconditionally below ``hp_pct_floor`` — a conservative backstop
    that fires whenever HP drops past a quarter-ish of max, which is
    the "2 heavy_strikes from a boss would kill me" zone.
    """
    if ctx.actor.current_hp <= int(hp_pct_floor * ctx.actor.max_hp):
        return True
    incoming = expected_incoming_damage(ctx)
    if incoming <= 0:
        return False
    return ctx.actor.current_hp <= 2 * incoming


# ---------------------------------------------------------------------------
# Enemy archetype detection
# ---------------------------------------------------------------------------


def has_healer_enemy(ctx: RuleContext) -> bool:
    """True when any living enemy has a healing ability.

    Detects support abilities with ``heal_percent > 0`` (e.g.,
    support_tanuki's heal_ally). Healers extend fights via attrition —
    they undo retaliate damage, making survive-only loops unwinnable.
    """
    for e in ctx.state.living_enemies:
        if _is_healer(e, ctx.game_data):
            return True
    return False


def has_mage_enemy(ctx: RuleContext) -> bool:
    """True when any living enemy has MAG-scaling offensive abilities.

    Mages bypass DEF, dealing disproportionate damage to STR-scaling
    characters. They share priority with healers for burst-down.
    """
    for e in ctx.state.living_enemies:
        if _is_mage(e, ctx.game_data):
            return True
    return False


def _is_healer(enemy: CombatantState, game_data) -> bool:
    for aid in enemy.ability_ids:
        ability = game_data.abilities.get(aid)
        if ability is None or ability.category != AbilityCategory.SUPPORT:
            continue
        for effect in ability.effects:
            if effect.heal_percent > 0:
                return True
    return False


def _is_mage(enemy: CombatantState, game_data) -> bool:
    for aid in enemy.ability_ids:
        ability = game_data.abilities.get(aid)
        if ability is None or ability.category != AbilityCategory.OFFENSIVE:
            continue
        for effect in ability.effects:
            if effect.stat_scaling == StatType.MAG and (
                effect.base_damage > 0 or effect.scaling_coefficient > 0
            ):
                return True
    return False
