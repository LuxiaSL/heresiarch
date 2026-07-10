"""Golden combat policies for onmyoji, sacrist, and berserker.

Derived from first principles of each kit (data/jobs/*.yaml +
data/abilities/*.yaml), in the golden_einherjar mold: combat is
computable, not heuristic. Primary purpose: **training-data
generators** for the learned-value ratchet — each policy encodes the
designer-known line for its job so tap shards contain competent
in-distribution states, not just corpses.

Onmyoji — the insight banker:
  bolt (10 + 0.7xMAG, ignores DEF) is the payoff; insight (survive /
  non-damage actions grant stacks; each amplified cast consumes one at
  +40%/stack) is the engine. Survive turns also bank AP, so banking is
  doubly-paid: the burst arrives amplified AND wide. Rhythm: bank while
  safe, tempo-kill when one bolt removes an attacker, burst to end.

Sacrist — the wound cultivator:
  communion doubles MAG output as HP drops to 50%; sanguine_rite
  (3 + 1.3xMAG, costs 15% max HP) is both the biggest hit and the
  throttle that descends into the power window. Healing above the
  window is throwing away damage; potions are for lethal danger only.
  crown_of_thorns clears packs while paying the same happy toll.

Berserker — the burst window:
  frenzy multiplies consecutive attacks (x1.15^chain, chain persists
  while damage is dealt every round, resets on passive rounds), so
  damage concentrates super-linearly into wide turns. Attack every
  round to keep the chain alive; spend banked AP in sweeps; reckless
  _blow only above half HP (the self-damage is real).
"""

from __future__ import annotations

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.abilities import Ability
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    PlayerTurnDecision,
)
from heresiarch.policy.predicates import (
    ability_damage,
    ability_ready,
    has_item,
    minimum_ap_to_kill_all_passive,
    passive_multiplier,
    projected_incoming_damage,
    speed_bonus_slots,
)
from heresiarch.policy.rule_engine import Rule, RuleBasedCombatPolicy, RuleContext
from heresiarch.policy.targeting import first_healer, first_mage

POTION_ITEM_ID: str = "minor_potion"
BONUS_ACTION_SUPPLY: int = 4

# Onmyoji rhythm knobs
INSIGHT_BANK_TARGET: int = 3      # bank to this many stacks while safe
SAFE_HP_RATIO: float = 0.6        # "safe" = incoming*2 < hp and hp% above this

# Sacrist communion window
DESCEND_ABOVE_HP_PCT: float = 0.70   # above this, self-damage is pure profit
CROWN_MIN_HP_PCT: float = 0.45       # crown costs 20% max HP — floor for it
CROWN_MIN_PACK: int = 3

# Berserker burst
ZERK_BANK_TARGET: int = 3         # the designer's S,S,S,C3 window
RECKLESS_MIN_HP_PCT: float = 0.5


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _ability(ctx: RuleContext, ability_id: str) -> Ability | None:
    return ctx.game_data.abilities.get(ability_id)


def _dmg_fn(ctx: RuleContext, ability_id: str):
    """(damage_fn, ability) pair for the kill-math predicates."""
    ab = _ability(ctx, ability_id)
    if ab is None:
        return None, None
    return (lambda a, t: ability_damage(a, t, ab)), ab


def _hp_pct(actor: CombatantState) -> float:
    return actor.current_hp / max(1, actor.max_hp)


def _weakest(ctx: RuleContext) -> CombatantState | None:
    enemies = ctx.state.living_enemies
    return min(enemies, key=lambda e: e.current_hp) if enemies else None


def _strongest(ctx: RuleContext) -> CombatantState | None:
    enemies = ctx.state.living_enemies
    return max(enemies, key=lambda e: e.current_hp) if enemies else None


def _priority_target(ctx: RuleContext) -> CombatantState | None:
    """Healer first (they undo progress), then mage (they ignore DEF)."""
    enemies = ctx.state.living_enemies
    if not enemies:
        return None
    for finder in (first_healer, first_mage):
        found = finder(ctx)
        if found is not None:
            for e in enemies:
                if e.id == found:
                    return e
    return None


def _min_ap_to_kill_single_passive(
    ctx: RuleContext, target: CombatantState, ability_id: str,
) -> int | None:
    """Min AP so that (1 + AP + speed bonus) casts kill one target,
    with frenzy/insight/communion multipliers per chain position."""
    fn, ab = _dmg_fn(ctx, ability_id)
    if fn is None:
        return None
    bonus = speed_bonus_slots(ctx)
    for cheat_n in range(0, ctx.actor.action_points + 1):
        attacks = 1 + cheat_n + bonus
        dealt = 0
        for idx in range(attacks):
            base = max(1, fn(ctx.actor, target))
            dealt += int(base * passive_multiplier(
                ctx.actor, idx, ctx.game_data, ability=ab,
            ))
            if dealt >= target.current_hp:
                return cheat_n
    return None


def _sweep_order(
    ctx: RuleContext, attacks: int, ability_id: str,
    primary_target: CombatantState,
) -> list[str]:
    """Primary on primary_target, extras weakest-first, passive-aware."""
    fn, ab = _dmg_fn(ctx, ability_id)
    if fn is None or attacks <= 0:
        return []
    remaining = {e.id: e.current_hp for e in ctx.state.living_enemies}
    by_id = {e.id: e for e in ctx.state.living_enemies}
    order: list[str] = []

    def hit(target_id: str, idx: int) -> None:
        order.append(target_id)
        base = max(1, fn(ctx.actor, by_id[target_id]))
        mult = passive_multiplier(ctx.actor, idx, ctx.game_data, ability=ab)
        remaining[target_id] = max(0, remaining[target_id] - int(base * mult))

    hit(primary_target.id, 0)
    for idx in range(1, attacks):
        alive = [eid for eid, hp in remaining.items() if hp > 0]
        if not alive:
            order.append(order[-1])
            continue
        hit(min(alive, key=lambda eid: remaining[eid]), idx)
    return order


def _bonus_actions(
    ctx: RuleContext, ability_id: str, target_id: str | None = None,
) -> list[CombatAction]:
    enemies = ctx.state.living_enemies
    if not enemies:
        return []
    if target_id is None:
        target_id = min(enemies, key=lambda e: e.current_hp).id
    return [
        CombatAction(
            actor_id=ctx.actor.id,
            ability_id=ability_id,
            target_ids=[target_id],
        )
        for _ in range(BONUS_ACTION_SUPPLY)
    ]


def _survive(ctx: RuleContext, bonus_ability: str) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
        bonus_actions=_bonus_actions(ctx, bonus_ability),
    )


def _cast(
    ctx: RuleContext, ability_id: str, target: CombatantState,
    bonus_ability: str | None = None,
) -> PlayerTurnDecision:
    """Plain NORMAL turn: one cast at target."""
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=CombatAction(
            actor_id=ctx.actor.id,
            ability_id=ability_id,
            target_ids=[target.id],
        ),
        bonus_actions=_bonus_actions(
            ctx, bonus_ability or ability_id, target_id=target.id,
        ),
    )


def _burst(
    ctx: RuleContext, ability_id: str, cheat_n: int,
    primary_target: CombatantState, *, focused: bool = False,
) -> PlayerTurnDecision:
    """CHEAT/NORMAL burst of (1 + cheat_n) casts."""
    if focused:
        targets = [primary_target.id] * (1 + cheat_n)
    else:
        targets = _sweep_order(ctx, 1 + cheat_n, ability_id, primary_target)
        if not targets:
            return _survive(ctx, ability_id)
    primary = CombatAction(
        actor_id=ctx.actor.id,
        ability_id=ability_id,
        target_ids=[targets[0]],
    )
    extras = [
        CombatAction(
            actor_id=ctx.actor.id,
            ability_id=ability_id,
            target_ids=[tid],
        )
        for tid in targets[1:]
    ]
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=(
            CheatSurviveChoice.CHEAT if cheat_n > 0
            else CheatSurviveChoice.NORMAL
        ),
        cheat_actions=cheat_n,
        primary_action=primary,
        cheat_extra_actions=extras,
        bonus_actions=_bonus_actions(ctx, ability_id, target_id=targets[-1]),
    )


def _use_potion(ctx: RuleContext, bonus_ability: str) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=ctx.actor.id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=CombatAction(
            actor_id=ctx.actor.id,
            ability_id="use_item",
            item_id=POTION_ITEM_ID,
            target_ids=[ctx.actor.id],
        ),
        bonus_actions=_bonus_actions(ctx, bonus_ability),
    )


def _shared_rules(attack_ability_of) -> list[Rule]:
    """The kill-math head every job shares: end the fight, kill the
    priority target, heal when the next round is lethal. Job-specific
    rhythm rules slot in after these."""

    def should_end_battle(ctx: RuleContext) -> bool:
        aid = attack_ability_of(ctx)
        fn, ab = _dmg_fn(ctx, aid)
        if fn is None:
            return False
        if projected_incoming_damage(ctx) >= ctx.actor.current_hp:
            return False
        return minimum_ap_to_kill_all_passive(
            ctx, ctx.game_data, damage_fn=fn, ability=ab,
        ) is not None

    def end_battle(ctx: RuleContext) -> PlayerTurnDecision:
        aid = attack_ability_of(ctx)
        fn, ab = _dmg_fn(ctx, aid)
        target = _strongest(ctx)
        if fn is None or target is None:
            return _survive(ctx, aid)
        cheat_n = minimum_ap_to_kill_all_passive(
            ctx, ctx.game_data, damage_fn=fn, ability=ab,
        )
        if cheat_n is None:
            return _survive(ctx, aid)
        return _burst(ctx, aid, cheat_n, target)

    def should_burst_priority(ctx: RuleContext) -> bool:
        target = _priority_target(ctx)
        if target is None:
            return False
        if projected_incoming_damage(ctx) >= ctx.actor.current_hp:
            return False
        aid = attack_ability_of(ctx)
        return _min_ap_to_kill_single_passive(ctx, target, aid) is not None

    def burst_priority(ctx: RuleContext) -> PlayerTurnDecision:
        aid = attack_ability_of(ctx)
        target = _priority_target(ctx)
        if target is None:
            return _survive(ctx, aid)
        cheat_n = _min_ap_to_kill_single_passive(ctx, target, aid)
        if cheat_n is None:
            return _survive(ctx, aid)
        return _burst(ctx, aid, cheat_n, target, focused=True)

    def should_heal(ctx: RuleContext) -> bool:
        if not has_item(ctx, POTION_ITEM_ID):
            return False
        if not ctx.state.living_enemies:
            return False
        if should_end_battle(ctx):
            return False
        return projected_incoming_damage(ctx) >= ctx.actor.current_hp

    def heal(ctx: RuleContext) -> PlayerTurnDecision:
        return _use_potion(ctx, attack_ability_of(ctx))

    return [
        Rule(name="end_battle", predicate=should_end_battle, action=end_battle),
        Rule(name="burst_priority", predicate=should_burst_priority,
             action=burst_priority),
        Rule(name="heal_emergency", predicate=should_heal, action=heal),
    ]


# ---------------------------------------------------------------------------
# Onmyoji
# ---------------------------------------------------------------------------

BOLT_ID = "bolt"
DRAIN_ID = "drain"


def _onmyoji_attack(ctx: RuleContext) -> str:
    return BOLT_ID


def _one_bolt_kills_weakest(ctx: RuleContext) -> bool:
    target = _weakest(ctx)
    fn, ab = _dmg_fn(ctx, BOLT_ID)
    if target is None or fn is None:
        return False
    dmg = int(max(1, fn(ctx.actor, target)) * passive_multiplier(
        ctx.actor, 0, ctx.game_data, ability=ab,
    ))
    return dmg >= target.current_hp


def _tempo_bolt(ctx: RuleContext) -> PlayerTurnDecision:
    target = _weakest(ctx)
    if target is None:
        return _survive(ctx, BOLT_ID)
    return _cast(ctx, BOLT_ID, target)


def _should_bank_insight(ctx: RuleContext) -> bool:
    """Bank while survive-halved chip leaves ≥2 rounds of margin.

    Survive halves incoming AND banks 1 AP AND grants 1 insight stack —
    triple-paid turns. The v1 mistake was comparing full incoming to HP
    (never banked, bolted into the wall at full chip, died at the
    3-slime pack every seed). The right comparison is against the
    halved chip we actually take while assembling the burst.
    """
    actor = ctx.actor
    if (
        actor.insight_stacks >= INSIGHT_BANK_TARGET
        and actor.action_points >= INSIGHT_BANK_TARGET
    ):
        return False  # burst is assembled — dump rules take over
    halved = projected_incoming_damage(ctx) // 2
    return actor.current_hp > 2 * halved


def _should_dump_stacks(ctx: RuleContext) -> bool:
    """Burst assembled but end_battle didn't fire (kill not provable):
    spend it anyway. An amplified sweep that clears half the pack beats
    another banked round — chip accumulates, stacks don't help dead
    onmyoji."""
    return (
        ctx.actor.insight_stacks >= INSIGHT_BANK_TARGET
        and ctx.actor.action_points >= 2
        and projected_incoming_damage(ctx) < ctx.actor.current_hp
    )


def _dump_stacks(ctx: RuleContext) -> PlayerTurnDecision:
    target = _weakest(ctx)
    if target is None:
        return _survive(ctx, BOLT_ID)
    return _burst(ctx, BOLT_ID, ctx.actor.action_points, target)


def _should_drain(ctx: RuleContext) -> bool:
    return _hp_pct(ctx.actor) < 0.55 and ability_ready(ctx, DRAIN_ID)


def _drain_sustain(ctx: RuleContext) -> PlayerTurnDecision:
    target = _weakest(ctx)
    if target is None:
        return _survive(ctx, BOLT_ID)
    return _cast(ctx, DRAIN_ID, target, bonus_ability=BOLT_ID)


def _pressure_bolt(ctx: RuleContext) -> PlayerTurnDecision:
    """Default: make progress. Turtling into the grave is the failure
    mode this policy exists to not demonstrate."""
    target = _weakest(ctx)
    if target is None:
        return _survive(ctx, BOLT_ID)
    return _cast(ctx, BOLT_ID, target)


def build_golden_onmyoji_rules() -> list[Rule]:
    return _shared_rules(_onmyoji_attack) + [
        Rule(name="tempo_bolt", predicate=_one_bolt_kills_weakest,
             action=_tempo_bolt),
        Rule(name="dump_stacks", predicate=_should_dump_stacks,
             action=_dump_stacks),
        Rule(name="bank_insight", predicate=_should_bank_insight,
             action=lambda ctx: _survive(ctx, BOLT_ID)),
        Rule(name="drain_sustain", predicate=_should_drain,
             action=_drain_sustain),
        Rule(name="pressure_bolt", predicate=lambda ctx: True,
             action=_pressure_bolt),
    ]


# ---------------------------------------------------------------------------
# Sacrist
# ---------------------------------------------------------------------------

LITANY_ID = "litany"
SANGUINE_ID = "sanguine_rite"
CROWN_ID = "crown_of_thorns"


def _sacrist_attack(ctx: RuleContext) -> str:
    # Kill-math head uses litany: free, DEF-ignoring, communion-scaled.
    return LITANY_ID


def _should_survive_lethal(ctx: RuleContext) -> bool:
    """Lethal incoming and no potion — halve it and pray."""
    if has_item(ctx, POTION_ITEM_ID):
        return False
    if not ctx.state.living_enemies:
        return False
    return projected_incoming_damage(ctx) >= ctx.actor.current_hp


def _should_crown(ctx: RuleContext) -> bool:
    return (
        len(ctx.state.living_enemies) >= CROWN_MIN_PACK
        and ability_ready(ctx, CROWN_ID)
        and _hp_pct(ctx.actor) > CROWN_MIN_HP_PCT
    )


def _crown_pack(ctx: RuleContext) -> PlayerTurnDecision:
    target = _strongest(ctx)
    if target is None:
        return _survive(ctx, LITANY_ID)
    return _cast(ctx, CROWN_ID, target, bonus_ability=LITANY_ID)


def _should_descend(ctx: RuleContext) -> bool:
    """Above the communion window, sanguine_rite's self-damage is pure
    profit: biggest hit in the kit AND a step toward double output."""
    return (
        _hp_pct(ctx.actor) > DESCEND_ABOVE_HP_PCT
        and ability_ready(ctx, SANGUINE_ID)
    )


def _descend(ctx: RuleContext) -> PlayerTurnDecision:
    target = _strongest(ctx)
    if target is None:
        return _survive(ctx, LITANY_ID)
    return _cast(ctx, SANGUINE_ID, target, bonus_ability=LITANY_ID)


def _litany_default(ctx: RuleContext) -> PlayerTurnDecision:
    """Litany the weakest if it kills (tempo), else the strongest."""
    weakest = _weakest(ctx)
    if weakest is None:
        return _survive(ctx, LITANY_ID)
    fn, ab = _dmg_fn(ctx, LITANY_ID)
    if fn is not None:
        dmg = int(max(1, fn(ctx.actor, weakest)) * passive_multiplier(
            ctx.actor, 0, ctx.game_data, ability=ab,
        ))
        if dmg >= weakest.current_hp:
            return _cast(ctx, LITANY_ID, weakest)
    target = _strongest(ctx) or weakest
    return _cast(ctx, LITANY_ID, target)


def build_golden_sacrist_rules() -> list[Rule]:
    return _shared_rules(_sacrist_attack) + [
        Rule(name="survive_lethal", predicate=_should_survive_lethal,
             action=lambda ctx: _survive(ctx, LITANY_ID)),
        Rule(name="crown_pack", predicate=_should_crown, action=_crown_pack),
        Rule(name="descend", predicate=_should_descend, action=_descend),
        Rule(name="litany_default", predicate=lambda ctx: True,
             action=_litany_default),
    ]


# ---------------------------------------------------------------------------
# Berserker
# ---------------------------------------------------------------------------

RECKLESS_ID = "reckless_blow"
_BERSERKER_ATTACKS = ("reckless_blow", "double_hit", "basic_attack",
                      "quick_strike")


def _berserker_attack(ctx: RuleContext) -> str:
    """Highest-damage known attack vs the strongest enemy; reckless
    only above half HP (self-damage is 25% of a big number)."""
    target = _strongest(ctx)
    if target is None:
        return "basic_attack"
    best_id, best_dmg = "basic_attack", -1
    for aid in _BERSERKER_ATTACKS:
        if aid == RECKLESS_ID and _hp_pct(ctx.actor) < RECKLESS_MIN_HP_PCT:
            continue
        if not ability_ready(ctx, aid):
            continue
        ab = _ability(ctx, aid)
        if ab is None:
            continue
        dmg = ability_damage(ctx.actor, target, ab)
        if dmg > best_dmg:
            best_id, best_dmg = aid, dmg
    return best_id


def _should_dump(ctx: RuleContext) -> bool:
    """Burst window assembled: spend everything. Frenzy rebuilds its
    chain within the wide turn (attack k at x1.15^k), so concentrated
    turns out-damage the same attacks spread across rounds."""
    return (
        ctx.actor.action_points >= ZERK_BANK_TARGET
        and projected_incoming_damage(ctx) < ctx.actor.current_hp
    )


def _dump_burst(ctx: RuleContext) -> PlayerTurnDecision:
    target = _strongest(ctx)
    if target is None:
        return _survive(ctx, "basic_attack")
    return _burst(
        ctx, _berserker_attack(ctx), ctx.actor.action_points, target,
    )


def _should_bank_zerk(ctx: RuleContext) -> bool:
    """The designer's S,S,S,C3 cycle: survive halves the chip while AP
    accumulates. v1 attacked every round at full incoming on 28-base-HP
    and died at median encounter 2 — glass cannons don't trade rounds,
    they bank them. Bank while halved chip leaves 2 rounds of margin."""
    if ctx.actor.action_points >= ZERK_BANK_TARGET:
        return False
    halved = projected_incoming_damage(ctx) // 2
    return ctx.actor.current_hp > 2 * halved


def _attack_default(ctx: RuleContext) -> PlayerTurnDecision:
    """Banking unsafe and burst not ready: make the best of a bad
    round. Weakest first if that kills (removes an attacker), else
    spend whatever AP exists on a sweep."""
    aid = _berserker_attack(ctx)
    weakest = _weakest(ctx)
    if weakest is None:
        return _survive(ctx, "basic_attack")
    fn, ab = _dmg_fn(ctx, aid)
    if fn is not None:
        dmg = int(max(1, fn(ctx.actor, weakest)) * passive_multiplier(
            ctx.actor, 0, ctx.game_data, ability=ab,
        ))
        if dmg >= weakest.current_hp:
            return _cast(ctx, aid, weakest)
    if ctx.actor.action_points > 0:
        target = _strongest(ctx) or weakest
        return _burst(ctx, aid, ctx.actor.action_points, target)
    return _cast(ctx, aid, _strongest(ctx) or weakest)


def build_golden_berserker_rules() -> list[Rule]:
    return _shared_rules(_berserker_attack) + [
        Rule(name="dump_burst", predicate=_should_dump, action=_dump_burst),
        Rule(name="bank_ap", predicate=_should_bank_zerk,
             action=lambda ctx: _survive(ctx, "basic_attack")),
        Rule(name="attack_default", predicate=lambda ctx: True,
             action=_attack_default),
    ]


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_golden_onmyoji(game_data: GameData) -> RuleBasedCombatPolicy:
    return RuleBasedCombatPolicy(
        name="golden_onmyoji",
        rules=build_golden_onmyoji_rules(),
        game_data=game_data,
    )


def make_golden_sacrist(game_data: GameData) -> RuleBasedCombatPolicy:
    return RuleBasedCombatPolicy(
        name="golden_sacrist",
        rules=build_golden_sacrist_rules(),
        game_data=game_data,
    )


def make_golden_berserker(game_data: GameData) -> RuleBasedCombatPolicy:
    return RuleBasedCombatPolicy(
        name="golden_berserker",
        rules=build_golden_berserker_rules(),
        game_data=game_data,
    )


def make_golden_for_job(game_data: GameData, job_id: str):
    """Job-appropriate golden combat policy; None when no golden line
    has been authored (martyr's baseline plays well via the solver)."""
    factories = {
        "onmyoji": make_golden_onmyoji,
        "sacrist": make_golden_sacrist,
        "berserker": make_golden_berserker,
    }
    factory = factories.get(job_id)
    return factory(game_data) if factory else None
