"""Combat solver: 1-ply exhaustive search with rollout evaluation.

Implements CombatPolicy. For each turn, enumerates all legal decisions,
simulates each forward to combat end via heuristic rollout, and returns
the decision that maximizes terminal evaluation (win × HP preservation).

Job-agnostic: works for all 5 jobs without modification. The search
operates over the real game engine, so passive mechanics (frenzy,
insight, thorns, retaliate, communion) are all automatically accounted
for in the forward simulation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.policy.enumerator import enumerate_decisions
from heresiarch.policy.predicates import (
    minimum_ap_to_kill_all_passive,
    projected_incoming_damage,
)
from heresiarch.policy.rollout import HeuristicRolloutPolicy, RolloutConfig
from heresiarch.policy.rule_engine import RuleContext
from heresiarch.policy.snapshot import CombatSnapshot
from heresiarch.policy.validation import compute_legal

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.enemies import EnemyTemplate
    from heresiarch.policy.protocols import LegalActionSet
    from heresiarch.policy.value_model import CombatValueFn


logger = logging.getLogger(__name__)

DEFAULT_MAX_ROLLOUT_ROUNDS: int = 100


@dataclass
class SolverConfig:
    max_candidates: int = 50
    enable_short_circuit: bool = True
    max_rollout_rounds: int = DEFAULT_MAX_ROLLOUT_ROUNDS
    search_depth: int = 3
    prune_after_ply: int = 20
    # Adaptive depth: full search_depth only when the fight is dangerous
    # (meaningful incoming damage or a long boss-like fight); depth 1
    # otherwise. Profiling shows trash fights at depth 3 evaluate 600+
    # candidates per decision for the same move depth 1 picks.
    adaptive_depth: bool = False
    danger_hp_ratio: float = 0.25       # incoming/current_hp at or above → dangerous
    danger_fight_rounds: float = 6.0    # est. rounds to clear at or above → dangerous
    # Runaway guards. Stall fights (nobody can kill anybody) make every
    # leaf rollout burn max_rollout_rounds and every ply multiply it —
    # observed 2h+ on a single seed. Guard at the right layer:
    # rollouts break after N rounds with no HP movement anywhere
    # (productive long fights — einherjar survive/retaliate — always
    # move HP, so they are never clipped). The wall-clock budget is a
    # last-resort backstop only; aggressive values measurably degrade
    # play (holdout: 3s budget + 25-round depth decay cost the preset
    # 1.85 mean zones). stall_rounds_shallow is off by default for the
    # same reason. 0 disables any guard.
    decide_time_budget_s: float = 15.0
    stall_rounds_shallow: int = 0
    rollout_no_progress_rounds: int = 8
    # Leaf evaluation: "rollout" plays out remaining rounds with the
    # heuristic policy; "model" asks a trained value function (rung 1,
    # design/learned-value-spec.md). Model leaves require a value_fn on
    # the solver — without one the solver warns and falls back. Known
    # v1 gap: model leaves don't reason about stash items (search plies
    # still do).
    leaf_eval: str = "rollout"


@dataclass
class SolverStats:
    """Per-combat statistics for performance monitoring."""
    total_decide_calls: int = 0
    short_circuited: int = 0
    candidates_evaluated: int = 0
    rollout_rounds_total: int = 0
    shallow_decides: int = 0   # adaptive depth dropped to 1-ply
    budget_exhausted: int = 0  # decides cut short by the time budget
    model_leaf_evals: int = 0  # leaves scored by the value model
    model_batch_calls: int = 0  # batched predict calls issued


# ---------------------------------------------------------------------------
# Deferred leaf scoring
#
# With leaf_eval="model", single-row model.predict per leaf dominates
# solver time (~0.21ms/row serial vs ~0.01ms/row batched). The search
# therefore returns a score *expression* instead of eagerly predicting:
# floats for terminal/rollout leaves, _DeferredLeaf for model leaves,
# _MaxOf for inner nodes. decide() collects every deferred leaf across
# all candidates, issues ONE batched predict, then resolves the trees.
# Tree shape never depends on leaf values (pruning is heuristic; the
# wall-clock budget gates on candidate *count*, see decide), so
# deferral cannot change which nodes get expanded.
# ---------------------------------------------------------------------------


@dataclass
class _DeferredLeaf:
    """A leaf state awaiting a (batched) model prediction.

    ``state``/``engine``/``stash`` are retained so a model failure at
    scoring time can still fall back to heuristic rollout — the model
    must never kill a sim.
    """

    state: CombatState
    engine: CombatEngine
    stash: list[str]
    value: float | None = None


@dataclass
class _MaxOf:
    """Inner search node: score = max(children)."""

    children: list["_ScoreNode"] = field(default_factory=list)


_ScoreNode = Union[float, _DeferredLeaf, _MaxOf]


class CombatSolver:
    """1-ply search with full rollout evaluation.

    Implements the CombatPolicy protocol so it plugs directly into
    the existing run driver.
    """

    name: str = "solver"

    def __init__(
        self,
        game_data: GameData,
        config: SolverConfig | None = None,
        rollout_config: RolloutConfig | None = None,
        value_fn: CombatValueFn | None = None,
    ):
        self.game_data = game_data
        self.config = config or SolverConfig()
        self.rollout = HeuristicRolloutPolicy(game_data, config=rollout_config)
        self.value_fn = value_fn
        self._stats = SolverStats()
        self._stash: list[str] = []
        self._enemy_templates: dict[str, EnemyTemplate] = {}
        self._mc_job_id: str = ""
        self._deadline: float | None = None
        self._model_failed = False
        if self.config.leaf_eval == "model" and value_fn is None:
            logger.warning(
                "SolverConfig.leaf_eval='model' but no value_fn was "
                "provided — falling back to heuristic rollout leaves.",
            )

    @property
    def stats(self) -> SolverStats:
        return self._stats

    def set_context(
        self,
        stash: list[str],
        enemy_templates: dict[str, EnemyTemplate],
        mc_job_id: str = "",
    ) -> None:
        """Set per-encounter context the solver needs for simulation.

        Called by the driver before each encounter. The stash tracks
        available consumables; enemy_templates are needed by
        process_round(); mc_job_id feeds the learned value function
        (model leaves only — rollout leaves ignore it).
        """
        self._stash = list(stash)
        self._enemy_templates = dict(enemy_templates)
        if mc_job_id:
            self._mc_job_id = mc_job_id

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision:
        self._stats.total_decide_calls += 1

        enemies = state.living_enemies
        if not enemies:
            return _survive(actor)

        # --- Short-circuit: provably optimal decisions ---
        if self.config.enable_short_circuit:
            result = self._try_short_circuit(state, actor, legal)
            if result is not None:
                self._stats.short_circuited += 1
                return result

        # --- Enumerate candidates ---
        candidates = enumerate_decisions(state, actor, legal, self.game_data)
        if not candidates:
            return _survive(actor)
        if len(candidates) == 1:
            return candidates[0]

        # Cap candidates to avoid runaway enumeration
        if len(candidates) > self.config.max_candidates:
            candidates = candidates[: self.config.max_candidates]

        # --- Arm the per-decision wall-clock budget ---
        if self.config.decide_time_budget_s > 0:
            self._deadline = time.monotonic() + self.config.decide_time_budget_s
        else:
            self._deadline = None

        # --- Adaptive depth: spend plies only on dangerous fights ---
        effective_depth = self.config.search_depth
        if self.config.adaptive_depth and effective_depth > 1:
            if not self._is_dangerous(state, actor, legal):
                effective_depth = 1
                self._stats.shallow_decides += 1

        # --- Stall decay: long fights are forced-move territory ---
        stall = self.config.stall_rounds_shallow
        if stall > 0 and state.round_number >= stall and effective_depth > 1:
            effective_depth = 1
            self._stats.shallow_decides += 1

        # --- Evaluate each candidate (leaf scoring may be deferred) ---
        # Snapshot once; restore per-branch
        # We need a RNG for the snapshot. The solver doesn't own the combat
        # RNG directly — it's on the CombatEngine. We create a temporary
        # one seeded from the state to make branches deterministic.
        import random

        rng_seed = hash((state.round_number, actor.id, actor.current_hp))
        base_rng = random.Random(rng_seed)

        snap = CombatSnapshot.take(state, base_rng)

        scored: list[tuple[PlayerTurnDecision, _ScoreNode]] = []
        for candidate in candidates:
            if self._over_budget() and scored:
                self._stats.budget_exhausted += 1
                break
            branch_state, branch_rng = snap.restore()
            node = self._evaluate_candidate(
                branch_state, branch_rng, actor.id, candidate,
                search_depth=effective_depth,
            )
            scored.append((candidate, node))
            self._stats.candidates_evaluated += 1

        # --- Score all deferred model leaves in one batched predict ---
        leaves: list[_DeferredLeaf] = []
        for _, node in scored:
            _collect_leaves(node, leaves)
        if leaves:
            self._score_deferred_leaves(leaves)

        # --- Pick the best candidate (same tie-break as before) ---
        best_score = -1.0
        best_decision = candidates[0]
        best_ap_spend = 999
        for candidate, node in scored:
            score = _resolve_score(node)
            ap_spend = candidate.cheat_actions
            if score > best_score or (
                score == best_score and ap_spend < best_ap_spend
            ):
                best_score = score
                best_decision = candidate
                best_ap_spend = ap_spend

        return best_decision

    def _try_short_circuit(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision | None:
        """Return a decision if the optimal play is provably clear."""
        from heresiarch.policy.rollout import best_attack_ability, make_damage_fn

        ctx = RuleContext(
            state=state,
            actor=actor,
            legal=legal,
            game_data=self.game_data,
        )

        enemies = state.living_enemies
        dmg_fn = make_damage_fn(actor, enemies, self.game_data)
        incoming = projected_incoming_damage(ctx)

        # Can kill all enemies and will survive (passive-aware)
        if incoming < actor.current_hp:
            ap_needed = minimum_ap_to_kill_all_passive(
                ctx, self.game_data, damage_fn=dmg_fn,
            )
            if ap_needed is not None:
                from heresiarch.policy.enumerator import (
                    _make_bonus_actions,
                    _make_sweep_extras,
                )

                bonus = _make_bonus_actions(actor, enemies)
                best_ability_id, _ = best_attack_ability(
                    actor, enemies, self.game_data,
                )
                target = max(enemies, key=lambda e: e.current_hp)

                if ap_needed == 0:
                    return PlayerTurnDecision(
                        combatant_id=actor.id,
                        cheat_survive=CheatSurviveChoice.NORMAL,
                        primary_action=CombatAction(
                            actor_id=actor.id,
                            ability_id=best_ability_id,
                            target_ids=[target.id],
                        ),
                        bonus_actions=bonus,
                    )

                sweep_extras = _make_sweep_extras(
                    actor, enemies, ap_needed, best_ability_id,
                )
                return PlayerTurnDecision(
                    combatant_id=actor.id,
                    cheat_survive=CheatSurviveChoice.CHEAT,
                    cheat_actions=ap_needed,
                    primary_action=CombatAction(
                        actor_id=actor.id,
                        ability_id=best_ability_id,
                        target_ids=[target.id],
                    ),
                    cheat_extra_actions=sweep_extras,
                    bonus_actions=bonus,
                )

        # HP very safe, can't kill anyone, and no AP banked — survive is
        # provably optimal. But if we have AP, the full search should
        # evaluate whether spending it is better (frenzy ramp, insight
        # burst, etc.) — damage multiplier passives make flat estimates
        # unreliable.
        if incoming * 2 < actor.current_hp and actor.action_points == 0:
            ap_needed = minimum_ap_to_kill_all_passive(
                ctx, self.game_data, damage_fn=dmg_fn,
            )
            if ap_needed is None:
                return _survive(actor)

        return None

    def _over_budget(self) -> bool:
        return self._deadline is not None and time.monotonic() > self._deadline

    def _is_dangerous(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> bool:
        """Cheap danger check gating full-depth search.

        Dangerous when this round's projected incoming damage is a real
        fraction of current HP, or the fight is long enough (boss-like
        HP pool relative to our damage) that multi-round planning pays.
        """
        from heresiarch.policy.rollout import make_damage_fn

        enemies = state.living_enemies
        if not enemies:
            return False

        ctx = RuleContext(
            state=state, actor=actor, legal=legal, game_data=self.game_data,
        )
        incoming = projected_incoming_damage(ctx)
        if incoming >= actor.current_hp * self.config.danger_hp_ratio:
            return True

        dmg_fn = make_damage_fn(actor, enemies, self.game_data)
        weakest = min(enemies, key=lambda e: e.current_hp)
        per_hit = max(1, dmg_fn(actor, weakest))
        total_enemy_hp = sum(e.current_hp for e in enemies)
        return total_enemy_hp / per_hit >= self.config.danger_fight_rounds

    def _evaluate_candidate(
        self,
        state: CombatState,
        rng,
        actor_id: str,
        candidate: PlayerTurnDecision,
        search_depth: int | None = None,
    ) -> _ScoreNode:
        """Simulate the candidate decision then search deeper or rollout."""
        depth = search_depth if search_depth is not None else self.config.search_depth
        return self._search_ply(
            state, rng, actor_id, candidate,
            depth_remaining=depth - 1,
            stash=list(self._stash),
        )

    def _search_ply(
        self,
        state: CombatState,
        rng,
        actor_id: str,
        candidate: PlayerTurnDecision,
        depth_remaining: int,
        stash: list[str],
    ) -> _ScoreNode:
        """Execute one ply: apply candidate, then recurse or rollout.

        At depth_remaining > 0: simulate this round, enumerate next
        round's candidates for the actor, evaluate each recursively.
        At depth_remaining == 0: simulate this round then rollout.
        """
        state.log = []

        engine = CombatEngine(
            ability_registry=self.game_data.abilities,
            item_registry=self.game_data.items,
            job_registry=self.game_data.jobs,
            rng=rng,
            enemy_registry=self.game_data.enemies,
        )

        remaining_stash = list(stash)
        round_decisions: dict[str, PlayerTurnDecision] = {actor_id: candidate}
        _claim_items(candidate, remaining_stash)

        for player in state.living_players:
            if player.id == actor_id:
                continue
            other_legal = compute_legal(state, player, stash=remaining_stash)
            other_decision = self.rollout.decide(state, player, other_legal)
            round_decisions[player.id] = other_decision
            _claim_items(other_decision, remaining_stash)

        state = engine.process_round(state, round_decisions, self._enemy_templates)

        for item_id in state.consumed_items:
            try:
                remaining_stash.remove(item_id)
            except ValueError:
                pass
        state.consumed_items = []

        if state.is_finished:
            return evaluate_terminal(state)

        # If deeper plies remain, search the next round's candidates
        if depth_remaining > 0:
            actor = state.get_combatant(actor_id)
            if actor is not None and actor.is_alive:
                return self._search_next_ply(
                    state, engine.rng, actor_id, actor,
                    depth_remaining, remaining_stash,
                )

        # Rollout to terminal state
        return self._rollout_to_end(state, engine, remaining_stash)

    def _search_next_ply(
        self,
        state: CombatState,
        rng,
        actor_id: str,
        actor: CombatantState,
        depth_remaining: int,
        stash: list[str],
    ) -> _ScoreNode:
        """Enumerate candidates for the next round and search recursively."""
        legal = compute_legal(state, actor, stash=stash)

        # Try short-circuit at deeper plies too
        if self.config.enable_short_circuit:
            ctx = RuleContext(
                state=state, actor=actor, legal=legal,
                game_data=self.game_data,
            )
            from heresiarch.policy.rollout import make_damage_fn
            dmg_fn = make_damage_fn(actor, state.living_enemies, self.game_data)
            incoming = projected_incoming_damage(ctx)

            if incoming < actor.current_hp:
                ap_needed = minimum_ap_to_kill_all_passive(
                    ctx, self.game_data, damage_fn=dmg_fn,
                )
                if ap_needed is not None:
                    # Can kill — just rollout from here, kill is guaranteed
                    engine = CombatEngine(
                        ability_registry=self.game_data.abilities,
                        item_registry=self.game_data.items,
                        job_registry=self.game_data.jobs,
                        rng=rng,
                        enemy_registry=self.game_data.enemies,
                    )
                    return self._rollout_to_end(state, engine, stash)

        candidates = enumerate_decisions(state, actor, legal, self.game_data)
        if not candidates:
            engine = CombatEngine(
                ability_registry=self.game_data.abilities,
                item_registry=self.game_data.items,
                job_registry=self.game_data.jobs,
                rng=rng,
                enemy_registry=self.game_data.enemies,
            )
            return self._rollout_to_end(state, engine, stash)

        snap = CombatSnapshot.take(state, rng)

        # Prune by heuristic: prefer candidates that deal damage
        # (attacking options generally more interesting than survive
        # duplicates). Keep SURVIVE + all unique action types, cap total.
        prune_to = self.config.prune_after_ply
        if len(candidates) > prune_to:
            candidates = _heuristic_prune(candidates, prune_to)

        children: list[_ScoreNode] = []
        for cand in candidates:
            if self._over_budget() and children:
                break
            branch_state, branch_rng = snap.restore()
            children.append(self._search_ply(
                branch_state, branch_rng, actor_id, cand,
                depth_remaining=depth_remaining - 1,
                stash=stash,
            ))
            self._stats.candidates_evaluated += 1

        if not children:
            return -1.0
        if all(isinstance(c, float) for c in children):
            return max(children)  # type: ignore[type-var, arg-type]
        return _MaxOf(children)

    def _use_model_leaves(self) -> bool:
        return (
            self.value_fn is not None
            and self.config.leaf_eval == "model"
            and not self._model_failed
        )

    def _rollout_to_end(
        self,
        state: CombatState,
        engine: CombatEngine,
        stash: list[str],
    ) -> _ScoreNode:
        """Score a leaf state: learned value model or heuristic rollout.

        With ``leaf_eval == "model"`` and a value_fn, scoring is
        deferred — decide() batches every leaf of the decision into one
        model predict on the same [0, 2] scale ``evaluate_terminal``
        uses. Any model failure downgrades to rollout for the rest of
        the process (warn once, never crash).
        """
        if self._use_model_leaves():
            if state.is_finished:
                return evaluate_terminal(state)
            return _DeferredLeaf(state=state, engine=engine, stash=list(stash))

        return self._heuristic_rollout(state, engine, stash)

    def _score_deferred_leaves(self, leaves: list[_DeferredLeaf]) -> None:
        """Assign values to deferred leaves; model first, rollout fallback.

        A ``ModelValueFn`` scores every leaf with one batched predict.
        A plain callable value_fn (tests, custom hooks) is called once
        per leaf. Any failure marks the model dead for this process and
        rolls out the still-unscored leaves — never crashes the sim.
        """
        if self._use_model_leaves():
            value_fn = self.value_fn
            batch = getattr(value_fn, "value_batch", None)
            try:
                if callable(batch):
                    values = batch(
                        [leaf.state for leaf in leaves], self._mc_job_id,
                    )
                    for leaf, value in zip(leaves, values):
                        leaf.value = float(value)
                    self._stats.model_leaf_evals += len(leaves)
                    self._stats.model_batch_calls += 1
                    return
                assert value_fn is not None  # _use_model_leaves guarantees
                for leaf in leaves:
                    leaf.value = float(value_fn(leaf.state, self._mc_job_id))
                    self._stats.model_leaf_evals += 1
                return
            except Exception as exc:  # noqa: BLE001 — model must never kill a sim
                self._model_failed = True
                logger.warning(
                    "Combat value model failed (%s: %s) — falling back "
                    "to heuristic rollout leaves.", type(exc).__name__, exc,
                )

        for leaf in leaves:
            if leaf.value is None:
                leaf.value = self._heuristic_rollout(
                    leaf.state, leaf.engine, leaf.stash,
                )

    def _heuristic_rollout(
        self,
        state: CombatState,
        engine: CombatEngine,
        stash: list[str],
    ) -> float:
        """Play out remaining rounds with the heuristic rollout policy."""
        remaining_stash = list(stash)
        rounds = 0
        max_rounds = self.config.max_rollout_rounds
        no_progress_cap = self.config.rollout_no_progress_rounds
        no_progress = 0
        prev_hp = _hp_signature(state)

        while not state.is_finished and rounds < max_rounds:
            # Backstop only — see SolverConfig notes on quality cost.
            if self._over_budget():
                break
            state.log = []

            rollout_decisions: dict[str, PlayerTurnDecision] = {}
            for player in state.living_players:
                legal = compute_legal(state, player, stash=remaining_stash)
                decision = self.rollout.decide(state, player, legal)
                rollout_decisions[player.id] = decision
                _claim_items(decision, remaining_stash)

            state = engine.process_round(
                state, rollout_decisions, self._enemy_templates,
            )
            rounds += 1

            if no_progress_cap > 0:
                hp_now = _hp_signature(state)
                no_progress = no_progress + 1 if hp_now == prev_hp else 0
                prev_hp = hp_now
                if no_progress >= no_progress_cap:
                    break

            for item_id in state.consumed_items:
                try:
                    remaining_stash.remove(item_id)
                except ValueError:
                    pass
            state.consumed_items = []

        self._stats.rollout_rounds_total += rounds
        return evaluate_terminal(state)


def evaluate_terminal(state: CombatState) -> float:
    """Score a completed (or timed-out) combat state.

    Won:  1.0 + mean(hp_remaining / max_hp)  → range [1.0, 2.0]
    Lost: 0.0
    Timed out (not finished): 0.5 × mean(hp_remaining / max_hp)
    """
    if state.is_finished:
        if state.player_won:
            players = state.player_combatants
            if not players:
                return 1.0
            hp_ratio = sum(
                max(0, p.current_hp) / max(1, p.max_hp) for p in players
            ) / len(players)
            return 1.0 + hp_ratio
        return 0.0

    # Timed out — partial credit based on HP state
    players = state.living_players
    if not players:
        return 0.0
    hp_ratio = sum(
        p.current_hp / max(1, p.max_hp) for p in players
    ) / len(players)
    return 0.5 * hp_ratio


def _collect_leaves(node: _ScoreNode, out: list[_DeferredLeaf]) -> None:
    """Gather deferred leaves depth-first (stable evaluation order)."""
    if isinstance(node, _DeferredLeaf):
        out.append(node)
    elif isinstance(node, _MaxOf):
        for child in node.children:
            _collect_leaves(child, out)


def _resolve_score(node: _ScoreNode) -> float:
    """Collapse a score expression once every leaf has a value."""
    if isinstance(node, _DeferredLeaf):
        if node.value is None:  # defensive: scoring must precede resolve
            raise RuntimeError("deferred leaf resolved before scoring")
        return node.value
    if isinstance(node, _MaxOf):
        if not node.children:  # defensive: built non-empty in search
            return -1.0
        return max(_resolve_score(child) for child in node.children)
    return node


def _hp_signature(state: CombatState) -> tuple[int, ...]:
    """Cheap fingerprint of combat progress: every combatant's HP."""
    return tuple(c.current_hp for c in state.all_combatants)


def _survive(actor: CombatantState) -> PlayerTurnDecision:
    return PlayerTurnDecision(
        combatant_id=actor.id,
        cheat_survive=CheatSurviveChoice.SURVIVE,
    )


def _claim_items(
    decision: PlayerTurnDecision,
    stash: list[str],
) -> None:
    """Remove consumed items from the running stash."""
    if decision.primary_action and decision.primary_action.item_id:
        try:
            stash.remove(decision.primary_action.item_id)
        except ValueError:
            pass
    for extra in decision.cheat_extra_actions:
        if extra.item_id:
            try:
                stash.remove(extra.item_id)
            except ValueError:
                pass


def _heuristic_prune(
    candidates: list[PlayerTurnDecision],
    keep: int,
) -> list[PlayerTurnDecision]:
    """Keep a diverse subset of candidates for deeper search.

    Ensures representation from each stance (SURVIVE, NORMAL, CHEAT)
    and target diversity. The 3-ply search needs to explore both
    "attack now" (NORMAL) and "burst later" (CHEAT) strategies.
    """
    survive: list[PlayerTurnDecision] = []
    items: list[PlayerTurnDecision] = []
    normals: list[PlayerTurnDecision] = []
    cheats: list[PlayerTurnDecision] = []

    for d in candidates:
        if d.cheat_survive == CheatSurviveChoice.SURVIVE:
            survive.append(d)
        elif d.primary_action and d.primary_action.item_id:
            items.append(d)
        elif d.cheat_survive == CheatSurviveChoice.NORMAL:
            normals.append(d)
        else:
            cheats.append(d)

    result = list(survive) + list(items)
    budget = keep - len(result)
    if budget <= 0:
        return result[:keep]

    # Split budget: half for NORMALs, half for CHEATs (minimum 2 each)
    normal_budget = max(2, budget // 2)
    cheat_budget = max(2, budget - normal_budget)

    # Deduplicate by target for each group
    seen_targets: set[str] = set()
    for d in normals[:normal_budget]:
        t = _target_key(d)
        if t not in seen_targets or len(result) < keep:
            result.append(d)
            seen_targets.add(t)

    seen_targets.clear()
    for d in cheats[:cheat_budget]:
        if len(result) >= keep:
            break
        result.append(d)

    return result[:keep]


def _target_key(d: PlayerTurnDecision) -> str:
    if d.primary_action and d.primary_action.target_ids:
        return d.primary_action.target_ids[0]
    return ""


def make_solver(
    game_data: GameData,
    config: SolverConfig | None = None,
    rollout_config: RolloutConfig | None = None,
    value_fn: CombatValueFn | None = None,
) -> CombatSolver:
    """Factory for CLI registration."""
    return CombatSolver(
        game_data=game_data, config=config, rollout_config=rollout_config,
        value_fn=value_fn,
    )
