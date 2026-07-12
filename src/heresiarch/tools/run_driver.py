"""Run driver: simulate one full Heresiarch run end-to-end.

Mirrors the control flow of heresiarch.agent.session.GameSession but
strips out phase gating, LLM summarization, and persistence. Takes
CombatPolicy + MacroPolicy objects, runs a full run, and returns a
RunResult with the structured outcome.

This is the Phase 1 deliverable from design/policy-sim-spec.md.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.formulas import calculate_buy_price
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.battle_record import (
    BattleRecord,
    EncounterRecord,
    RoundRecord,
)
from heresiarch.engine.models.combat_state import (
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.policy.protocols import (
    CombatPolicy,
    MacroPolicy,
    RunResult,
)
from heresiarch.policy.validation import (
    ValidationError,
    compute_legal,
    resolve_decision,
)
from heresiarch.logutil import RateLimitedLogger
from heresiarch.tools.progress import ProgressEmitter

if TYPE_CHECKING:
    from heresiarch.analytics.record_db import RecordDB, RunRecordMetadata
    from heresiarch.engine.models.enemies import EnemyInstance, EnemyTemplate

logger = logging.getLogger(__name__)
_rate_limited = RateLimitedLogger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_ENCOUNTERS: int = 400
DEFAULT_MAX_COMBAT_ROUNDS: int = 200  # circuit-breaker against infinite loops
DEFAULT_MAX_SHOP_PURCHASES: int = 16   # circuit-breaker per town visit
# (16, not 10: party-wide gearing adds up to 2 recruit-gear buys per
# recruit after sells + MC gear + potions; 10 starved them.)
DEFAULT_MAX_STUCK_ITERS: int = 8       # outer-loop iters without encounter progress


# ---------------------------------------------------------------------------
# Internal bookkeeping
# ---------------------------------------------------------------------------


@dataclass
class _DriverMetrics:
    rounds_total: int = 0
    gold_earned_combat: int = 0
    gold_spent_shop: int = 0
    gold_spent_lodge: int = 0
    lodge_rests: int = 0
    shop_purchases: int = 0
    recruits_accepted: int = 0
    recruits_declined: int = 0
    encounters_cleared: int = 0
    # Death tracking (only set on defeat)
    killed_at_zone: str = ""
    killed_at_encounter: int = 0
    killed_by: str = ""
    # Termination
    termination_reason: str = "clean_exit"


@dataclass
class _RunContext:
    game_data: GameData
    game_loop: GameLoop
    rng: random.Random
    combat_policy: CombatPolicy
    macro_policy: MacroPolicy
    metrics: _DriverMetrics = field(default_factory=_DriverMetrics)
    max_encounters: int = DEFAULT_MAX_ENCOUNTERS
    max_combat_rounds: int = DEFAULT_MAX_COMBAT_ROUNDS
    seed: int = 0
    emitter: ProgressEmitter = field(
        default_factory=ProgressEmitter.from_env,
    )
    # Live recording: upsert the run to record_db every N cleared
    # encounters (0 = final-only). Lets viewers (theater --follow)
    # tail a run while it is still being simulated.
    record_db: RecordDB | None = None
    record_meta: RunRecordMetadata | None = None
    record_every: int = 0
    encounters_since_record: int = 0
    # Optional training-data tap (tools/data_tap.py). Hooks are
    # failure-proof on the tap side; a None tap costs nothing.
    data_tap: Any = None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def simulate_run(
    mc_job_id: str,
    combat_policy: CombatPolicy,
    macro_policy: MacroPolicy,
    seed: int,
    *,
    game_data: GameData | None = None,
    max_encounters: int = DEFAULT_MAX_ENCOUNTERS,
    max_combat_rounds: int = DEFAULT_MAX_COMBAT_ROUNDS,
    data_path: Path | None = None,
    record_db: RecordDB | None = None,
    record_run_id: str | None = None,
    record_every: int = 0,
    data_tap: Any = None,
) -> RunResult:
    """Simulate one full run and return structured results.

    ``game_data`` can be passed for speed when running many seeds in
    sequence (avoids re-parsing YAML). Otherwise loaded from
    ``data_path`` (default: ``./data``).

    ``record_db`` — if provided, the final RunState (including
    battle_record) is upserted to the DB under ``record_run_id`` (or a
    derived ``sim_{job}_{seed}_{policy}`` tag).

    ``record_every`` — if > 0 (and ``record_db`` is set), also upsert
    mid-run every N cleared encounters so the run can be watched live
    (``theater --follow``). Upserts are idempotent; the final write
    remains authoritative.
    """
    if game_data is None:
        game_data = load_all(data_path or Path("data"))

    if mc_job_id not in game_data.jobs:
        raise ValueError(
            f"Unknown job: {mc_job_id!r}. "
            f"Available: {sorted(game_data.jobs.keys())}"
        )

    rng = random.Random(seed)
    gl = GameLoop(game_data=game_data, rng=rng)

    # Give macro policy access to the game loop if it needs it
    # (MacroSolver uses it for RNG snapshots during branch simulation).
    if hasattr(macro_policy, "set_game_loop"):
        macro_policy.set_game_loop(gl)

    run_id = record_run_id or (
        f"sim_{mc_job_id}_{combat_policy.name}_{macro_policy.name}_{seed}"
    )
    run = gl.new_run(run_id=run_id, mc_name="sim_mc", mc_job_id=mc_job_id)
    run = run.record_macro(
        "run_start",
        {"mc_name": "sim_mc", "mc_job_id": mc_job_id, "seed": seed},
    )

    record_meta = None
    if record_db is not None:
        from heresiarch.analytics.record_db import RunRecordMetadata
        record_meta = RunRecordMetadata(
            source="sim",
            combat_policy=combat_policy.name,
            macro_policy=macro_policy.name,
            seed=seed,
        )

    ctx = _RunContext(
        game_data=game_data,
        game_loop=gl,
        rng=rng,
        combat_policy=combat_policy,
        macro_policy=macro_policy,
        max_encounters=max_encounters,
        max_combat_rounds=max_combat_rounds,
        seed=seed,
        record_db=record_db,
        record_meta=record_meta,
        record_every=max(0, record_every),
        data_tap=data_tap,
    )
    ctx.emitter.emit("run_start", seed=seed, job=mc_job_id)

    run = _drive(run, ctx)

    if data_tap is not None:
        won_region = any(
            (z in game_data.zones and game_data.zones[z].is_final)
            for z in run.zones_completed
        )
        data_tap.on_run_end(run, won_region)

    ctx.emitter.emit(
        "run_end",
        seed=seed,
        zones=len(run.zones_completed),
        enc=ctx.metrics.encounters_cleared,
        dead=run.is_dead,
        reason=ctx.metrics.termination_reason,
    )

    if record_db is not None and record_meta is not None:
        try:
            record_db.record_run(
                run,
                record_meta,
                outcome="dead" if run.is_dead else "clean_exit",
            )
        except Exception:
            # Never break a sim run because the DB write failed.
            pass

    return _build_result(run, ctx, seed, mc_job_id, combat_policy, macro_policy)


# ---------------------------------------------------------------------------
# Top-level control flow
# ---------------------------------------------------------------------------


def _drive(run: RunState, ctx: _RunContext) -> RunState:
    """Outer run loop: town/zone selection until dead, stuck, or capped."""
    gl = ctx.game_loop
    m = ctx.metrics
    stuck_iters = 0

    while not run.is_dead and m.encounters_cleared < ctx.max_encounters:
        prev_encounters = m.encounters_cleared

        # Between-zone: optionally visit a town for shopping/resting.
        run = _maybe_visit_town(run, ctx)

        # Pick a zone.
        available_zones = gl.get_available_zones(run)
        choice = ctx.macro_policy.decide_zone(run, available_zones)
        if choice is None:
            m.termination_reason = "no_available_zones"
            break

        run = gl.enter_zone(run, choice.id)
        run = run.record_macro(
            "enter_zone",
            {
                "zone_id": choice.id,
                "already_cleared": choice.id in run.zones_completed,
                "via": "sim_decide_zone",
            },
        )
        run = _drive_zone(run, ctx)

        # If we died mid-zone, loop exits naturally.
        if run.is_dead:
            m.termination_reason = "dead"
            break

        # Leave the zone cleanly to free the town path.
        if run.current_zone_id:
            zone_id = run.current_zone_id
            zs = run.zone_state
            leave_payload = {
                "zone_id": zone_id,
                "zone_cleared": bool(zs and zs.is_cleared),
                "overstay_battles": zs.overstay_battles if zs else 0,
                "current_encounter_index": zs.current_encounter_index if zs else 0,
                "reason": "sim_post_zone",
            }
            run = gl.leave_zone(run)
            run = run.record_macro("leave_zone", leave_payload)

        # Stuck-loop guard: a misbehaving macro policy can retreat in
        # and out of town without ever advancing encounters. Bail out
        # rather than spin.
        if m.encounters_cleared == prev_encounters:
            stuck_iters += 1
            if stuck_iters >= DEFAULT_MAX_STUCK_ITERS:
                m.termination_reason = "stuck"
                break
        else:
            stuck_iters = 0

    if not run.is_dead and m.encounters_cleared >= ctx.max_encounters:
        m.termination_reason = "max_encounters"

    return run


def _maybe_visit_town(run: RunState, ctx: _RunContext) -> RunState:
    """Enter town if macro says so, process shop + lodge, leave."""
    gl = ctx.game_loop

    # Available town IDs in the current region.
    region = gl.get_region_for_run(run)
    if region is None:
        return run

    available_towns = [
        town.id
        for town in ctx.game_data.towns.values()
        if town.region == region and gl.is_town_unlocked(run, town.id)
    ]
    if not available_towns:
        return run

    choice = ctx.macro_policy.decide_visit_town(run, available_towns)
    if not choice:
        return run

    try:
        run = gl.enter_town(run, choice)
    except ValueError:
        # Can't enter (e.g. still in a zone) — skip.
        return run
    run = run.record_macro("enter_town", {"town_id": choice})

    # Lodge first (heals before we spend gold shopping).
    cost = gl.get_lodge_cost(run) or 0
    if ctx.macro_policy.decide_lodge(run, cost):
        try:
            prev_gold = run.party.money
            run = gl.rest_at_lodge(run)
            spent = prev_gold - run.party.money
            ctx.metrics.gold_spent_lodge += spent
            ctx.metrics.lodge_rests += 1
            run = run.record_macro(
                "lodge_rest",
                {"cost": spent, "gold_before": prev_gold, "gold_after": run.party.money},
            )
        except ValueError:
            pass  # insufficient funds, etc.

    # Shop. `rest_at_lodge` can clear the current town flag — re-check
    # before browsing.
    if run.current_town_id:
        available_items = gl.resolve_town_shop(run)
        purchases = ctx.macro_policy.decide_shop(run, available_items)
        run = _apply_shop_actions(run, ctx, purchases, available_items)

    # In-town heal: buy potion, use it, repeat until topped off.
    if run.current_town_id:
        run = _in_town_heal_loop(run, ctx)

    # Leave town (only if rest_at_lodge didn't already drop us out).
    if run.current_town_id:
        town_id = run.current_town_id
        run = gl.leave_town(run)
        run = run.record_macro("leave_town", {"town_id": town_id})
    return run


def _apply_shop_actions(
    run: RunState,
    ctx: _RunContext,
    actions: list,
    available_items: list[str] | None = None,
) -> RunState:
    """Execute shop actions in order, skipping unaffordable/invalid ones."""
    gl = ctx.game_loop
    count = 0

    # Capture the offered menu for macro event recording. TUI records
    # per-purchase so the shopping loop shows up as N events with the
    # same offered list — we mirror that.
    offered: list[dict[str, int | str]] = []
    if available_items:
        for iid in available_items:
            item = ctx.game_data.items.get(iid)
            if item is None:
                continue
            offered.append(
                {"item_id": iid, "price": calculate_buy_price(item.base_price, run.party.cha)}
            )

    for act in actions:
        if count >= DEFAULT_MAX_SHOP_PURCHASES:
            break
        if act.action == "sell":
            if act.item_id not in run.party.stash:
                continue
            try:
                new_party = gl.shop_engine.sell_item(run.party, act.item_id)
            except ValueError:
                continue
            run = run.model_copy(update={"party": new_party})
            run = run.record_macro(
                "shop_sell",
                {"item_id": act.item_id},
            )
            count += 1
            continue
        if act.action != "buy":
            continue

        item = ctx.game_data.items.get(act.item_id)
        if item is None:
            continue
        price = calculate_buy_price(item.base_price, run.party.cha)

        if run.party.money < price:
            continue
        if len(run.party.stash) >= STASH_LIMIT:
            break

        try:
            new_party = gl.shop_engine.buy_item(run.party, act.item_id, price)
        except ValueError:
            continue

        run = run.model_copy(update={"party": new_party})
        run = run.record_macro(
            "shop_buy",
            {"item_id": act.item_id, "price": price, "offered": list(offered)},
        )
        ctx.metrics.gold_spent_shop += price
        ctx.metrics.shop_purchases += 1
        count += 1

    # Auto-equip best stash gear onto the whole active roster.
    run = _auto_equip_party(run, ctx)
    return run


def _auto_equip_party(run: RunState, ctx: _RunContext) -> RunState:
    """Equip the best WEAPON and ARMOR from stash onto every active member.

    Upgrade-aware (macro doctrine): a stash item strictly better than
    the equipped one — by (tier, base_price) — gets equipped, and the
    engine returns the displaced item to the stash where the next shop
    pass sells it. MC picks first (doctrine priority), recruits follow
    in roster order — their join-time gear is otherwise frozen for the
    whole run. Weapon UPGRADES require a scaling stat the character's
    job grows (mirrors the macro's shop gating); an EMPTY slot takes
    anything — flat damage beats none. Accessories stay out of scope.
    """
    from heresiarch.engine.models.items import EquipType
    from heresiarch.policy.builtin.golden_macro import useful_growth_stats

    gl = ctx.game_loop
    member_ids = [
        cid for cid in run.party.active if cid in run.party.characters
    ]
    # MC first; stable sort keeps roster order for the rest.
    member_ids.sort(key=lambda cid: not run.party.characters[cid].is_mc)
    if not member_ids:
        return run

    slot_types: list[tuple[str, EquipType]] = [
        ("WEAPON", EquipType.WEAPON),
        ("ARMOR", EquipType.ARMOR),
    ]

    def _rank(item) -> tuple[int, int]:
        return (item.tier, item.base_price) if item else (0, 0)

    for char_id in member_ids:
        for slot, equip_type in slot_types:
            char = run.party.characters.get(char_id)
            if char is None:
                break
            equipped_id = char.equipment.get(slot)
            equipped = None
            if equipped_id:
                equipped = ctx.game_data.items.get(equipped_id) or run.party.items.get(equipped_id)
            current_rank = _rank(equipped)
            upgrading = current_rank > (0, 0)
            growable = useful_growth_stats(char.job_id, ctx.game_data)

            best_iid = None
            best_rank = current_rank
            for iid in list(run.party.stash):
                item = ctx.game_data.items.get(iid) or run.party.items.get(iid)
                if item is None or item.is_consumable:
                    continue
                if item.equip_type != equip_type:
                    continue
                if (
                    upgrading
                    and equip_type == EquipType.WEAPON
                    and item.scaling
                    and item.scaling.stat.value not in growable
                ):
                    continue
                if _rank(item) > best_rank:
                    best_iid = iid
                    best_rank = _rank(item)

            if best_iid is None:
                continue
            try:
                run = gl.equip_item(run, char_id, best_iid, slot)
            except ValueError:
                continue
            run = run.record_macro(
                "equip",
                {
                    "character_id": char_id,
                    "slot": slot,
                    "item_id": best_iid,
                    "displaced_item_id": equipped_id,
                },
            )

    return run


def _in_town_heal_loop(run: RunState, ctx: _RunContext) -> RunState:
    """Buy-use-buy-use healing loop while in town.

    Interleaves buying one potion and using it on the most-wounded
    character until all active characters are above the in-town heal
    target (default 100%). Stops when gold runs out, stash is full,
    or potions aren't available in the shop.
    """
    gl = ctx.game_loop
    config = getattr(ctx.macro_policy, 'config', None)
    target_pct = getattr(config, 'in_town_heal_target_pct', 1.0) if config else 1.0

    available_items = gl.resolve_town_shop(run)
    potion_id = "minor_potion"
    if potion_id not in available_items:
        return run

    max_iterations = 20
    for _ in range(max_iterations):
        active = [
            run.party.characters[cid]
            for cid in run.party.active
            if cid in run.party.characters
        ]
        wounded = [
            c for c in active
            if c.current_hp / max(1, c.max_hp) < target_pct
            and (c.max_hp - c.current_hp) >= 10
        ]
        if not wounded:
            break

        potion_in_stash = potion_id in run.party.stash
        if not potion_in_stash:
            item = ctx.game_data.items.get(potion_id)
            if item is None:
                break
            price = calculate_buy_price(item.base_price, run.party.cha)
            if run.party.money < price or len(run.party.stash) >= STASH_LIMIT:
                break
            try:
                new_party = gl.shop_engine.buy_item(run.party, potion_id, price)
            except ValueError:
                break
            run = run.model_copy(update={"party": new_party})
            run = run.record_macro(
                "shop_buy",
                {"item_id": potion_id, "price": price, "offered": []},
            )
            ctx.metrics.gold_spent_shop += price
            ctx.metrics.shop_purchases += 1

        target_char = min(wounded, key=lambda c: c.current_hp / max(1, c.max_hp))
        hp_before = target_char.current_hp
        try:
            run = gl.use_consumable(run, potion_id, target_char.id)
        except ValueError:
            break
        target_after = run.party.characters.get(target_char.id)
        hp_after = target_after.current_hp if target_after else hp_before
        run = run.record_macro(
            "use_consumable",
            {
                "item_id": potion_id,
                "target_character_id": target_char.id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "max_hp": target_char.max_hp,
                "in_combat": False,
            },
        )

    return run


# ---------------------------------------------------------------------------
# Per-zone driving
# ---------------------------------------------------------------------------


def _drive_zone(run: RunState, ctx: _RunContext) -> RunState:
    """Run encounters in the current zone until cleared, dead, or macro stops."""
    gl = ctx.game_loop
    m = ctx.metrics

    while (
        not run.is_dead
        and run.current_zone_id
        and m.encounters_cleared < ctx.max_encounters
    ):
        # Use healing items between encounters if macro says so.
        run = _apply_between_encounter_items(run, ctx)

        # Macro can ask to bail out of the zone mid-way (to shop, heal,
        # etc). Progress is preserved in zone_progress.
        if ctx.macro_policy.decide_retreat_to_town(run):
            break

        # Get next encounter.
        try:
            enemies = gl.get_next_encounter(run)
        except ValueError:
            # No more encounters available in this zone.
            break

        run, victorious, final_state = _run_encounter(run, ctx, enemies)
        _emit_encounter(run, ctx)
        _maybe_record_live(run, ctx)
        if run.is_dead:
            # Defeat metrics already set inside _run_encounter.
            return run
        if not victorious:
            # Defensive: shouldn't hit since defeat sets is_dead.
            break

        # Cleared zone? Decide whether to overstay.
        if run.zone_state and run.zone_state.is_cleared:
            if not ctx.macro_policy.decide_overstay(run):
                break

    return run


def _maybe_record_live(run: RunState, ctx: _RunContext) -> None:
    """Mid-run DB upsert every ``record_every`` encounters (live viewing)."""
    if (
        ctx.record_db is None
        or ctx.record_meta is None
        or ctx.record_every <= 0
    ):
        return
    ctx.encounters_since_record += 1
    if ctx.encounters_since_record < ctx.record_every:
        return
    ctx.encounters_since_record = 0
    try:
        # Outcome inferred: 'dead' or 'in_progress' — the final
        # authoritative write in simulate_run() overrides it.
        # Incremental: only rows newer than the last upsert are written
        # (full replace here is O(n²) over a long run).
        ctx.record_db.record_run(run, ctx.record_meta, incremental=True)
    except Exception as exc:  # noqa: BLE001 — live recording must never break the sim
        _rate_limited.warning(
            logger, "live_record",
            "Live run recording failed (%s: %s) — sim continues; the "
            "theater view of run %s may go stale until the final write.",
            type(exc).__name__, exc, run.run_id,
        )


def _emit_encounter(run: RunState, ctx: _RunContext) -> None:
    """Heartbeat one line per finished encounter to the progress stream."""
    if not ctx.emitter.enabled:
        return
    mc_level = 0
    hp_total = 0
    hp_max = 0
    for cid in run.party.active:
        char = run.party.characters.get(cid)
        if char is None:
            continue
        hp_total += max(0, char.current_hp)
        hp_max += max(1, char.max_hp)
        if char.is_mc:
            mc_level = char.level
    ctx.emitter.emit(
        "encounter",
        seed=ctx.seed,
        zone=run.current_zone_id or "",
        enc=ctx.metrics.encounters_cleared,
        level=mc_level,
        hp_pct=round(hp_total / max(1, hp_max), 3),
        gold=run.party.money,
    )


def _apply_between_encounter_items(
    run: RunState, ctx: _RunContext
) -> RunState:
    gl = ctx.game_loop
    uses = ctx.macro_policy.decide_between_encounter_items(run)
    for use in uses:
        if use.item_id not in run.party.stash:
            continue
        target_char = run.party.characters.get(use.character_id)
        hp_before = target_char.current_hp if target_char else 0
        max_hp = target_char.max_hp if target_char else 0
        try:
            run = gl.use_consumable(run, use.item_id, use.character_id)
        except ValueError:
            continue
        target_after = run.party.characters.get(use.character_id)
        hp_after = target_after.current_hp if target_after else hp_before
        run = run.record_macro(
            "use_consumable",
            {
                "item_id": use.item_id,
                "target_character_id": use.character_id,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "max_hp": max_hp,
                "in_combat": False,
            },
        )
    return run


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def _run_encounter(
    run: RunState,
    ctx: _RunContext,
    enemies: list[EnemyInstance],
) -> tuple[RunState, bool, CombatState]:
    """Run one encounter end-to-end. Returns (new_run, victorious, final_state)."""
    gl = ctx.game_loop
    m = ctx.metrics

    characters = [
        run.party.characters[cid]
        for cid in run.party.active
        if cid in run.party.characters
    ]

    state = gl.combat_engine.initialize_combat(
        characters, enemies, party_gold=run.party.money,
    )

    enemy_combatant_templates: dict[str, str] = {}
    for i, c in enumerate(state.enemy_combatants):
        if i < len(enemies):
            enemy_combatant_templates[c.id] = enemies[i].template_id

    enemy_templates: dict[str, EnemyTemplate] = {}
    for enemy in enemies:
        tmpl = ctx.game_data.enemies.get(enemy.template_id)
        if tmpl:
            enemy_templates[enemy.template_id] = tmpl

    # Give the combat policy per-encounter context if it supports it
    # (CombatSolver needs stash + enemy_templates for forward simulation).
    if hasattr(ctx.combat_policy, "set_context"):
        ctx.combat_policy.set_context(
            stash=list(run.party.stash),
            enemy_templates=enemy_templates,
            mc_job_id=run.mc_job_id,
        )

    # Track round-by-round records for BattleRecord persistence.
    encounter_rounds: list[RoundRecord] = []

    if ctx.data_tap is not None:
        ctx.data_tap.on_encounter_start(run, state)

    # Combat loop
    while not state.is_finished and state.round_number < ctx.max_combat_rounds:
        if ctx.data_tap is not None:
            ctx.data_tap.on_combat_round(state)
        decisions = _collect_decisions(state, ctx, run)
        pre_event_count = len(state.log)
        state = gl.combat_engine.process_round(state, decisions, enemy_templates)

        # Capture round events + HPs for the battle record.
        round_events = state.log[pre_event_count:]
        encounter_rounds.append(
            RoundRecord(
                round_number=state.round_number,
                player_decisions=decisions,
                events=round_events,
                player_hp={c.id: c.current_hp for c in state.player_combatants},
                enemy_hp={c.id: c.current_hp for c in state.enemy_combatants},
            )
        )

        # Remove consumed items from stash
        if state.consumed_items:
            run = _remove_consumed_items(run, state.consumed_items)
            state.consumed_items = []

    m.rounds_total += state.round_number

    victorious = bool(state.player_won)

    if ctx.data_tap is not None:
        ctx.data_tap.on_encounter_end(state, victorious)

    # Append the encounter to the run's BattleRecord regardless of outcome,
    # then proceed with victory/defeat handling.
    run = _append_encounter_record(
        run, state, encounter_rounds, victorious,
        enemy_combatant_templates,
    )

    if not victorious:
        # Record defeat metrics.
        m.killed_at_zone = run.current_zone_id or ""
        if run.zone_state:
            m.killed_at_encounter = run.zone_state.current_encounter_index
        # Pick a living enemy at defeat time as "killer" — heuristic.
        living_enemies = [c for c in state.enemy_combatants if c.is_alive]
        if living_enemies:
            m.killed_by = enemy_combatant_templates.get(
                living_enemies[0].id, living_enemies[0].id,
            )
        run = gl.handle_death(run)
        return run, False, state

    # Victory post-processing.
    combat_result = _build_combat_result(state, run, enemy_combatant_templates, ctx)

    # Track gold change through combat (loot + pilfer − theft).
    prev_gold = run.party.money
    run, loot = gl.resolve_combat_result(run, combat_result)
    m.gold_earned_combat += max(0, run.party.money - prev_gold)

    # Pick loot.
    free_slots = STASH_LIMIT - len(run.party.stash)
    offered_loot = list(loot.item_ids)
    keep = ctx.macro_policy.decide_loot_pick(run, loot, free_slots)
    skipped = [iid for iid in offered_loot if iid not in keep]
    run = gl.apply_loot(run, loot, keep)

    # Advance zone (increment counter or mark cleared).
    run = gl.advance_zone(run)
    m.encounters_cleared += 1
    run = run.record_macro(
        "pick_loot",
        {
            "offered": offered_loot,
            "selected": list(keep),
            "skipped": skipped,
            "discarded_from_stash": [],
            "money_gained": loot.money,
        },
    )

    # Offer recruitment if applicable.
    run, candidate = gl.try_recruitment(run)
    if candidate is not None:
        if ctx.macro_policy.decide_recruit(run, candidate):
            try:
                new_party = gl.recruitment_engine.recruit(run.party, candidate)
                run = run.model_copy(update={
                    "party": new_party,
                    "last_recruit_job_id": candidate.character.job_id,
                })
                m.recruits_accepted += 1
                run = run.record_macro(
                    "recruit_accept",
                    {
                        "candidate_id": candidate.character.id,
                        "job_id": candidate.character.job_id,
                        "level": candidate.character.level,
                        "name": candidate.character.name,
                    },
                )
            except ValueError:
                m.recruits_declined += 1
        else:
            m.recruits_declined += 1
            run = run.record_macro(
                "recruit_pass",
                {
                    "candidate_id": candidate.character.id,
                    "job_id": candidate.character.job_id,
                    "level": candidate.character.level,
                    "name": candidate.character.name,
                },
            )

    return run, True, state


def _collect_decisions(
    state: CombatState, ctx: _RunContext, run: RunState,
) -> dict[str, PlayerTurnDecision]:
    """Run the combat policy against every living player, resolve through validation.

    Claims consumables from the stash as policies request them so two
    actors can't double-spend the same potion in one round.
    """
    decisions: dict[str, PlayerTurnDecision] = {}
    abilities = ctx.game_data.abilities
    remaining_stash = list(run.party.stash)

    for actor in state.living_players:
        legal = compute_legal(state, actor, stash=remaining_stash)
        raw = ctx.combat_policy.decide(state, actor, legal)
        try:
            resolved, _issues = resolve_decision(
                raw, state, actor, abilities, legal,
            )
        except ValidationError:
            # Policy asked for an unknown ability. Fall back to basic_attack
            # on the first living enemy. In Phase 2 we'd fail loud; for
            # Phase 1 infrastructure we prefer to keep the run alive and
            # surface the bug via the rule trace later.
            from heresiarch.engine.models.combat_state import (
                CheatSurviveChoice, CombatAction,
            )
            target = (
                [state.living_enemies[0].id] if state.living_enemies else []
            )
            resolved = PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.NORMAL,
                primary_action=CombatAction(
                    actor_id=actor.id,
                    ability_id="basic_attack",
                    target_ids=target,
                ),
            )

        # Claim consumables the resolved decision will use.
        claimed_items: list[str] = []
        if resolved.primary_action and resolved.primary_action.item_id:
            claimed_items.append(resolved.primary_action.item_id)
        for extra in resolved.cheat_extra_actions:
            if extra.item_id:
                claimed_items.append(extra.item_id)
        for ba in resolved.bonus_actions:
            if ba.item_id:
                claimed_items.append(ba.item_id)
        for iid in claimed_items:
            try:
                remaining_stash.remove(iid)
            except ValueError:
                pass  # policy asked for an item not in stash; engine will handle

        decisions[actor.id] = resolved
    return decisions


def _append_encounter_record(
    run: RunState,
    state: CombatState,
    rounds: list[RoundRecord],
    victorious: bool,
    enemy_combatant_templates: dict[str, str],
) -> RunState:
    """Mirror of agent.session._record_encounter for the sim driver."""
    player_ids = {c.id for c in state.player_combatants}

    total_dealt = 0
    total_taken = 0
    total_healing = 0
    deaths: list[str] = []

    for event in state.log:
        match event.event_type:
            case CombatEventType.DAMAGE_DEALT:
                if event.actor_id in player_ids and not event.details.get("self_damage"):
                    total_dealt += event.value
                elif event.target_id in player_ids:
                    total_taken += event.value
            case CombatEventType.HEALING:
                if event.target_id in player_ids:
                    total_healing += event.value
            case CombatEventType.DEATH:
                if event.target_id in player_ids:
                    deaths.append(event.target_id)
            case CombatEventType.DOT_TICK:
                if event.target_id in player_ids:
                    total_taken += event.value
                elif event.actor_id in player_ids:
                    total_dealt += event.value

    zone_id = run.current_zone_id or ""
    encounter_idx = (
        run.zone_state.current_encounter_index if run.zone_state else 0
    )

    record = EncounterRecord(
        zone_id=zone_id,
        encounter_index=encounter_idx,
        enemy_template_ids=list(enemy_combatant_templates.values()),
        rounds=rounds,
        result="victory" if victorious else "defeat",
        rounds_taken=state.round_number,
        total_damage_dealt=total_dealt,
        total_damage_taken=total_taken,
        total_healing=total_healing,
        character_deaths=deaths,
    )

    new_encounters = list(run.battle_record.encounters) + [record]
    return run.model_copy(
        update={"battle_record": BattleRecord(encounters=new_encounters)}
    )


def _remove_consumed_items(run: RunState, consumed: list[str]) -> RunState:
    new_stash = list(run.party.stash)
    for iid in consumed:
        try:
            new_stash.remove(iid)
        except ValueError:
            pass
    new_party = run.party.model_copy(update={"stash": new_stash})
    return run.model_copy(update={"party": new_party})


def _build_combat_result(
    state: CombatState,
    run: RunState,
    enemy_templates: dict[str, str],
    ctx: _RunContext,
) -> CombatResult:
    """Mirror agent.session._build_combat_result."""
    surviving_ids = [c.id for c in state.player_combatants if c.is_alive]
    surviving_hp = {c.id: c.current_hp for c in state.player_combatants if c.is_alive}

    defeated_templates: list[str] = []
    defeated_budgets: list[float] = []
    defeated_levels: list[int] = []
    defeated_xp_mults: list[float] = []
    defeated_gold_mults: list[float] = []

    for c in state.enemy_combatants:
        if c.is_alive:
            continue
        tmpl_id = enemy_templates.get(c.id, "")
        if not tmpl_id:
            # Split-spawned enemies use rsplit convention.
            tmpl_id = c.id.rsplit("_", 1)[0]
        defeated_templates.append(tmpl_id)
        defeated_levels.append(c.level)
        tmpl = ctx.game_data.enemies.get(tmpl_id)
        if tmpl is not None:
            defeated_budgets.append(tmpl.budget_multiplier)
            defeated_xp_mults.append(tmpl.xp_multiplier or 0.0)
            defeated_gold_mults.append(tmpl.gold_multiplier or 0.0)
        else:
            defeated_budgets.append(0.0)
            defeated_xp_mults.append(0.0)
            defeated_gold_mults.append(0.0)

    zone_level = 0
    if run.current_zone_id:
        zone = ctx.game_data.zones.get(run.current_zone_id)
        if zone:
            zone_level = zone.zone_level

    return CombatResult(
        player_won=state.player_won or False,
        surviving_character_ids=surviving_ids,
        surviving_character_hp=surviving_hp,
        defeated_enemy_template_ids=defeated_templates,
        defeated_enemy_budget_multipliers=defeated_budgets,
        defeated_enemy_levels=defeated_levels,
        defeated_enemy_xp_multipliers=defeated_xp_mults,
        defeated_enemy_gold_multipliers=defeated_gold_mults,
        rounds_taken=state.round_number,
        zone_level=zone_level,
        gold_stolen_by_enemies=state.gold_stolen_by_enemies,
        gold_stolen_by_players=state.gold_stolen_by_players,
    )


# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------


def _build_result(
    run: RunState,
    ctx: _RunContext,
    seed: int,
    mc_job_id: str,
    combat_policy: CombatPolicy,
    macro_policy: MacroPolicy,
) -> RunResult:
    gd = ctx.game_data
    m = ctx.metrics

    # Farthest zone: max zone_level among completed zones; or current zone
    # if we died partway through a zone that wasn't completed.
    zone_levels: list[tuple[str, int]] = []
    for zid in run.zones_completed:
        z = gd.zones.get(zid)
        if z:
            zone_levels.append((zid, z.zone_level))
    if run.current_zone_id:
        z = gd.zones.get(run.current_zone_id)
        if z:
            zone_levels.append((run.current_zone_id, z.zone_level))

    if zone_levels:
        zone_levels.sort(key=lambda t: t[1], reverse=True)
        farthest_zone_id, farthest_level = zone_levels[0]
    else:
        farthest_zone_id, farthest_level = "", 0

    # Final party HP pct
    active = [
        run.party.characters[cid] for cid in run.party.active
        if cid in run.party.characters
    ]
    if active:
        final_hp_pct = sum(
            c.current_hp / max(1, c.max_hp) for c in active
        ) / len(active)
    else:
        final_hp_pct = 0.0

    # MC level
    mc_level = 0
    for char in run.party.characters.values():
        if char.is_mc:
            mc_level = char.level
            break

    return RunResult(
        seed=seed,
        mc_job_id=mc_job_id,
        combat_policy_name=combat_policy.name,
        macro_policy_name=macro_policy.name,
        is_dead=run.is_dead,
        zones_cleared=list(run.zones_completed),
        farthest_zone=farthest_zone_id,
        farthest_zone_level=farthest_level,
        encounters_cleared=m.encounters_cleared,
        final_party_hp_pct=final_hp_pct,
        final_mc_level=mc_level,
        final_gold=run.party.money,
        killed_at_zone=m.killed_at_zone,
        killed_at_encounter=m.killed_at_encounter,
        killed_by=m.killed_by,
        rounds_taken_total=m.rounds_total,
        gold_earned_combat=m.gold_earned_combat,
        gold_spent_shop=m.gold_spent_shop,
        gold_spent_lodge=m.gold_spent_lodge,
        lodge_rests=m.lodge_rests,
        shop_purchases=m.shop_purchases,
        recruits_accepted=m.recruits_accepted,
        recruits_declined=m.recruits_declined,
        termination_reason=m.termination_reason,
    )
