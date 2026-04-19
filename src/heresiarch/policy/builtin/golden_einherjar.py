"""Golden einherjar combat policy (v6).

Computed-optimal rule set derived from run_d9f92b01 analysis + designer
intent clarifications. Key shift from v5: combat is computable, not
heuristic. The objective is **minimize HP loss while guaranteeing the win.**

Combat model (einherjar):
  - L1: basic_attack + retaliate (passive, damage when hit)
  - L3: brace_strike (8 + 0.4×STR, self +15 DEF 1 turn)
  - L8: thrust (8 + 0.5×STR, pierce 40% DEF)
  - L15: fracture (5 + 0.3×STR + shatter)
  - heavy_strike (scroll-only; 15 + 0.8×STR)

Priority (first match wins):
  1. taunt_cheat          — taunted + AP≥1 → CHEAT with brace_strike
                            primary. Can't survive under taunt; DEF buff
                            mitigates forced hit.
  2. immediate_kill_thief — bandit_slime alive → NORMAL basic_attack
                            on the bandit. Economy protection: gold lost
                            is HP lost via potions.
  3. end_battle           — can kill ALL living enemies this turn →
                            CHEAT/NORMAL with minimum AP spend. Primary
                            on strongest, extras sweep weakest-first.
  4. burst_priority_target— healer/mage alive + can burst-kill them →
                            CHEAT to focus-fire the priority target.
                            Healers extend fights (undo retaliate damage);
                            mages bypass DEF.
  5. heal_emergency       — projected incoming damage ≥ current HP,
                            have potion, can't end battle → NORMAL
                            use_item(potion). Always NORMAL (save AP
                            for next turn's burst).
  6. fallback_survive     — default → SURVIVE, retaliate carries.

Target priority (for primary action):
  - first_taunter (if taunted)
  - first_gold_thief (bandit_slime — preempt to preserve gold)
  - strongest remaining enemy

Design principle: combat decisions are computed from game state, not
approximated with HP% heuristics. The engine exposes all data needed.
"""

from __future__ import annotations

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    PlayerTurnDecision,
)
from heresiarch.policy.predicates import (
    ability_ready,
    am_taunted,
    ap_at_least,
    basic_attack_damage,
    has_healer_enemy,
    has_item,
    has_mage_enemy,
    minimum_ap_to_kill_all,
    minimum_ap_to_kill_single,
    projected_incoming_damage,
    thrust_damage,
)
from heresiarch.policy.rule_engine import Rule, RuleBasedCombatPolicy, RuleContext
from heresiarch.policy.targeting import (
    first_gold_thief,
    first_healer,
    first_mage,
    first_taunter,
)


BASIC_ATTACK_ID: str = "basic_attack"
BRACE_STRIKE_ID: str = "brace_strike"
THRUST_ID: str = "thrust"
POTION_ITEM_ID: str = "minor_potion"

BONUS_ACTION_SUPPLY: int = 4


# ---------------------------------------------------------------------------
# Rule predicates
# ---------------------------------------------------------------------------


def _should_taunt_cheat(ctx: RuleContext) -> bool:
    return am_taunted(ctx) and ap_at_least(ctx, 1)


def _should_immediate_kill_thief(ctx: RuleContext) -> bool:
    return first_gold_thief(ctx) is not None


def _should_end_battle(ctx: RuleContext) -> bool:
    """True when available actions can kill every living enemy this turn
    AND the MC will survive the enemy's attacks without survive halving.

    On a CHEAT/NORMAL turn, survive damage reduction is off. If the
    enemy acts first (faster SPD), they hit at full damage. The policy
    must only commit to ending the battle if it can tank that hit.
    """
    target = _primary_target(ctx)
    if target is None:
        return False
    if projected_incoming_damage(ctx) >= ctx.actor.current_hp:
        return False
    primary_fn = _damage_fn_for(_choose_cheat_primary(ctx))
    extras_fn = _damage_fn_for(_choose_cheat_extras_ability(ctx))
    return minimum_ap_to_kill_all(
        ctx,
        primary_damage_fn=primary_fn,
        extras_damage_fn=extras_fn,
        primary_target_id=target.id,
    ) is not None


def _should_burst_priority_target(ctx: RuleContext) -> bool:
    """True when a healer or mage is alive, we can burst-kill them,
    and we'll survive the round without survive halving."""
    target = _find_priority_target(ctx)
    if target is None:
        return False
    if projected_incoming_damage(ctx) >= ctx.actor.current_hp:
        return False
    primary_fn = _damage_fn_for(_choose_cheat_primary(ctx))
    extras_fn = _damage_fn_for(_choose_cheat_extras_ability(ctx))
    return minimum_ap_to_kill_single(
        ctx, target,
        primary_damage_fn=primary_fn,
        extras_damage_fn=extras_fn,
    ) is not None


def _should_heal_emergency(ctx: RuleContext) -> bool:
    """Heal when enemies would kill us before we can act again.

    Only fires when we can't end the fight (ending it is always better
    than healing). Uses projected_incoming_damage which accounts for
    speed: faster enemies hit twice before our next action.
    """
    if not has_item(ctx, POTION_ITEM_ID):
        return False
    if not ctx.state.living_enemies:
        return False
    if _should_end_battle(ctx):
        return False
    return projected_incoming_damage(ctx) >= ctx.actor.current_hp


# ---------------------------------------------------------------------------
# Ability selection
# ---------------------------------------------------------------------------


def _choose_cheat_primary(ctx: RuleContext) -> str:
    """Pick the cheat primary ability.

      - Taunted + brace_strike ready → brace_strike (DEF soak)
      - Thrust known and thrust_damage(target) > basic_damage(target)
        → thrust
      - Else → basic_attack
    """
    if am_taunted(ctx) and ability_ready(ctx, BRACE_STRIKE_ID):
        return BRACE_STRIKE_ID

    target = _primary_target(ctx)
    if target is not None and ability_ready(ctx, THRUST_ID):
        if thrust_damage(ctx.actor, target) > basic_attack_damage(
            ctx.actor, target
        ):
            return THRUST_ID

    return BASIC_ATTACK_ID


def _choose_cheat_extras_ability(ctx: RuleContext) -> str:
    """Per-extra-attack ability choice. Evaluate against weakest enemy."""
    weakest = _weakest_enemy(ctx)
    if (
        weakest is not None
        and ability_ready(ctx, THRUST_ID)
        and thrust_damage(ctx.actor, weakest) > basic_attack_damage(
            ctx.actor, weakest
        )
    ):
        return THRUST_ID
    return BASIC_ATTACK_ID


def _damage_fn_for(ability_id: str):
    if ability_id == THRUST_ID:
        return thrust_damage
    return basic_attack_damage


# ---------------------------------------------------------------------------
# Target selection
# ---------------------------------------------------------------------------


def _primary_target(ctx: RuleContext) -> CombatantState | None:
    """Where the primary attack goes for end_battle sweeps.

    Priority: taunter → gold_thief → strongest remaining enemy.
    Healer/mage targeting is handled explicitly by burst_priority_target.
    """
    enemies = ctx.state.living_enemies
    if not enemies:
        return None

    taunt_id = first_taunter(ctx)
    if taunt_id is not None:
        for e in enemies:
            if e.id == taunt_id:
                return e

    thief_id = first_gold_thief(ctx)
    if thief_id is not None:
        for e in enemies:
            if e.id == thief_id:
                return e

    return max(enemies, key=lambda e: e.current_hp)


def _find_priority_target(ctx: RuleContext) -> CombatantState | None:
    """Find the healer or mage that should be burst-killed.

    Healers take priority over mages: they extend fights by undoing
    retaliate damage, which is a worse attrition problem than mages'
    raw DPS.
    """
    enemies = ctx.state.living_enemies
    if not enemies:
        return None

    healer_id = first_healer(ctx)
    if healer_id is not None:
        for e in enemies:
            if e.id == healer_id:
                return e

    mage_id = first_mage(ctx)
    if mage_id is not None:
        for e in enemies:
            if e.id == mage_id:
                return e

    return None


def _weakest_enemy(ctx: RuleContext) -> CombatantState | None:
    enemies = ctx.state.living_enemies
    if not enemies:
        return None
    return min(enemies, key=lambda e: e.current_hp)


def _attack_order(
    ctx: RuleContext, attacks: int, primary_target_id: str,
) -> list[str]:
    """Ordered target list for (primary + extras).

    Primary lands on primary_target_id. Extras sweep weakest-first
    among remaining enemies, simulating damage to model kill progression.
    """
    if attacks <= 0 or not ctx.state.living_enemies:
        return []

    primary_dmg_fn = _damage_fn_for(_choose_cheat_primary(ctx))
    extras_dmg_fn = _damage_fn_for(_choose_cheat_extras_ability(ctx))

    remaining_hp = {e.id: e.current_hp for e in ctx.state.living_enemies}
    order: list[str] = [primary_target_id]
    if primary_target_id in remaining_hp:
        dmg = max(1, primary_dmg_fn(
            ctx.actor,
            next(
                e for e in ctx.state.living_enemies if e.id == primary_target_id
            ),
        ))
        remaining_hp[primary_target_id] = max(
            0, remaining_hp[primary_target_id] - dmg
        )

    extras_budget = attacks - 1
    if extras_budget <= 0:
        return order

    for _ in range(extras_budget):
        alive = [
            e for e in ctx.state.living_enemies
            if remaining_hp.get(e.id, 0) > 0
        ]
        if not alive:
            order.append(ctx.state.living_enemies[0].id)
            continue
        weakest = min(alive, key=lambda e: remaining_hp[e.id])
        order.append(weakest.id)
        dmg = max(1, extras_dmg_fn(ctx.actor, weakest))
        remaining_hp[weakest.id] = max(0, remaining_hp[weakest.id] - dmg)

    return order


# ---------------------------------------------------------------------------
# Bonus actions
# ---------------------------------------------------------------------------


def _bonus_actions(ctx: RuleContext, target_id: str | None = None) -> list[CombatAction]:
    """Free attacks for speed-bonus slots.

    Supply BONUS_ACTION_SUPPLY basic_attacks. When ``target_id`` is
    given, focus them on that target; otherwise target weakest enemy.
    """
    enemies = ctx.state.living_enemies
    if not enemies:
        return []
    if target_id is None:
        target_id = min(enemies, key=lambda e: e.current_hp).id
    return [
        CombatAction(
            actor_id=ctx.actor.id,
            ability_id=BASIC_ATTACK_ID,
            target_ids=[target_id],
        )
        for _ in range(BONUS_ACTION_SUPPLY)
    ]


# ---------------------------------------------------------------------------
# Action builders
# ---------------------------------------------------------------------------


def _build_cheat_or_normal_decision(
    ctx: RuleContext, cheat_actions: int,
    primary_target_id: str | None = None,
) -> PlayerTurnDecision:
    """Construct a decision spending exactly ``cheat_actions`` AP.

    cheat_actions=0 → NORMAL turn. cheat_actions>0 → CHEAT turn.
    """
    primary_ability = _choose_cheat_primary(ctx)
    extras_ability = _choose_cheat_extras_ability(ctx)

    if primary_target_id is not None:
        target = next(
            (e for e in ctx.state.living_enemies if e.id == primary_target_id),
            None,
        )
    else:
        target = _primary_target(ctx)

    if target is None:
        return _survive(ctx)

    total_attacks = 1 + cheat_actions
    targets = _attack_order(ctx, total_attacks, target.id)

    primary = CombatAction(
        actor_id=ctx.actor.id,
        ability_id=primary_ability,
        target_ids=[targets[0]],
    )
    extras = [
        CombatAction(
            actor_id=ctx.actor.id,
            ability_id=extras_ability,
            target_ids=[targets[i]],
        )
        for i in range(1, len(targets))
    ]

    cs = CheatSurviveChoice.CHEAT if cheat_actions > 0 else CheatSurviveChoice.NORMAL

    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=cs,
        cheat_actions=cheat_actions,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=_bonus_actions(ctx),
    )


def _build_focused_burst(
    ctx: RuleContext, target: CombatantState, cheat_actions: int,
) -> PlayerTurnDecision:
    """All attacks focused on a single target (for priority kills)."""
    primary_ability = _choose_cheat_primary(ctx)
    extras_ability = _choose_cheat_extras_ability(ctx)

    primary = CombatAction(
        actor_id=ctx.actor.id,
        ability_id=primary_ability,
        target_ids=[target.id],
    )
    extras = [
        CombatAction(
            actor_id=ctx.actor.id,
            ability_id=extras_ability,
            target_ids=[target.id],
        )
        for _ in range(cheat_actions)
    ]

    cs = CheatSurviveChoice.CHEAT if cheat_actions > 0 else CheatSurviveChoice.NORMAL

    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=cs,
        cheat_actions=cheat_actions,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=_bonus_actions(ctx, target_id=target.id),
    )


# ---------------------------------------------------------------------------
# Rule actions
# ---------------------------------------------------------------------------


def _taunt_cheat(ctx: RuleContext) -> PlayerTurnDecision:
    return _build_cheat_or_normal_decision(ctx, ctx.actor.action_points)


def _immediate_kill_thief(ctx: RuleContext) -> PlayerTurnDecision:
    """NORMAL basic_attack on the gold thief. No AP spend."""
    thief_id = first_gold_thief(ctx)
    if thief_id is None:
        return _survive(ctx)

    primary = CombatAction(
        actor_id=ctx.actor.id,
        ability_id=BASIC_ATTACK_ID,
        target_ids=[thief_id],
    )
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=primary,
        bonus_actions=_bonus_actions(ctx, target_id=thief_id),
    )


def _end_battle(ctx: RuleContext) -> PlayerTurnDecision:
    """Spend minimum AP to kill every living enemy this turn."""
    target = _primary_target(ctx)
    if target is None:
        return _survive(ctx)
    primary_fn = _damage_fn_for(_choose_cheat_primary(ctx))
    extras_fn = _damage_fn_for(_choose_cheat_extras_ability(ctx))
    cheat_n = minimum_ap_to_kill_all(
        ctx,
        primary_damage_fn=primary_fn,
        extras_damage_fn=extras_fn,
        primary_target_id=target.id,
    )
    if cheat_n is None:
        return _survive(ctx)
    return _build_cheat_or_normal_decision(ctx, cheat_n)


def _burst_priority_target(ctx: RuleContext) -> PlayerTurnDecision:
    """Focus-fire the healer or mage with minimum AP to kill them."""
    target = _find_priority_target(ctx)
    if target is None:
        return _survive(ctx)
    primary_fn = _damage_fn_for(_choose_cheat_primary(ctx))
    extras_fn = _damage_fn_for(_choose_cheat_extras_ability(ctx))
    cheat_n = minimum_ap_to_kill_single(
        ctx, target,
        primary_damage_fn=primary_fn,
        extras_damage_fn=extras_fn,
    )
    if cheat_n is None:
        return _survive(ctx)
    return _build_focused_burst(ctx, target, cheat_n)


def _heal_emergency(ctx: RuleContext) -> PlayerTurnDecision:
    """Heal with potion. CHEAT if AP available to combine healing with
    brace_strike (DEF soak) and damage extras on the strongest enemy.

    Designer's pattern vs omega_slime: survive to AP 3, then CHEAT
    potion + brace_strike + damage dumps. The brace DEF buff mitigates
    the next hit; the extras chip the boss down faster than pure
    retaliate.
    """
    primary = CombatAction(
        actor_id=ctx.actor.id,
        ability_id="use_item",
        item_id=POTION_ITEM_ID,
        target_ids=[ctx.actor.id],
    )
    ap = ctx.actor.action_points
    strongest = _primary_target(ctx)

    if ap == 0 or strongest is None:
        return PlayerTurnDecision(
            combatant_id=ctx.actor.id,
            cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=primary,
            bonus_actions=_bonus_actions(ctx),
        )

    extras_ability = _choose_cheat_extras_ability(ctx)
    extras: list[CombatAction] = []

    if ability_ready(ctx, BRACE_STRIKE_ID):
        extras.append(CombatAction(
            actor_id=ctx.actor.id,
            ability_id=BRACE_STRIKE_ID,
            target_ids=[strongest.id],
        ))
        for _ in range(ap - 1):
            extras.append(CombatAction(
                actor_id=ctx.actor.id,
                ability_id=extras_ability,
                target_ids=[strongest.id],
            ))
    else:
        for _ in range(ap):
            extras.append(CombatAction(
                actor_id=ctx.actor.id,
                ability_id=extras_ability,
                target_ids=[strongest.id],
            ))

    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.CHEAT,
        cheat_actions=ap,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=_bonus_actions(ctx, target_id=strongest.id),
    )


def _survive(ctx: RuleContext) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
        bonus_actions=_bonus_actions(ctx),
    )


# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------


def build_golden_einherjar_rules() -> list[Rule]:
    return [
        Rule(
            name="taunt_cheat",
            predicate=_should_taunt_cheat,
            action=_taunt_cheat,
        ),
        Rule(
            name="immediate_kill_thief",
            predicate=_should_immediate_kill_thief,
            action=_immediate_kill_thief,
        ),
        Rule(
            name="end_battle",
            predicate=_should_end_battle,
            action=_end_battle,
        ),
        Rule(
            name="burst_priority_target",
            predicate=_should_burst_priority_target,
            action=_burst_priority_target,
        ),
        Rule(
            name="heal_emergency",
            predicate=_should_heal_emergency,
            action=_heal_emergency,
        ),
        Rule(
            name="fallback_survive",
            predicate=lambda ctx: True,
            action=_survive,
        ),
    ]


def make_golden_einherjar(game_data: GameData) -> RuleBasedCombatPolicy:
    return RuleBasedCombatPolicy(
        name="golden_einherjar",
        rules=build_golden_einherjar_rules(),
        game_data=game_data,
    )
