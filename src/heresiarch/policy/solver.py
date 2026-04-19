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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
from heresiarch.policy.rollout import HeuristicRolloutPolicy
from heresiarch.policy.rule_engine import RuleContext
from heresiarch.policy.snapshot import CombatSnapshot
from heresiarch.policy.validation import compute_legal

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.enemies import EnemyTemplate
    from heresiarch.policy.protocols import LegalActionSet


DEFAULT_MAX_ROLLOUT_ROUNDS: int = 100


@dataclass
class SolverConfig:
    max_candidates: int = 50
    enable_short_circuit: bool = True
    max_rollout_rounds: int = DEFAULT_MAX_ROLLOUT_ROUNDS
    search_depth: int = 3
    prune_after_ply: int = 20


@dataclass
class SolverStats:
    """Per-combat statistics for performance monitoring."""
    total_decide_calls: int = 0
    short_circuited: int = 0
    candidates_evaluated: int = 0
    rollout_rounds_total: int = 0


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
    ):
        self.game_data = game_data
        self.config = config or SolverConfig()
        self.rollout = HeuristicRolloutPolicy(game_data)
        self._stats = SolverStats()
        self._stash: list[str] = []
        self._enemy_templates: dict[str, EnemyTemplate] = {}

    @property
    def stats(self) -> SolverStats:
        return self._stats

    def set_context(
        self,
        stash: list[str],
        enemy_templates: dict[str, EnemyTemplate],
    ) -> None:
        """Set per-encounter context the solver needs for simulation.

        Called by the driver before each encounter. The stash tracks
        available consumables; enemy_templates are needed by
        process_round().
        """
        self._stash = list(stash)
        self._enemy_templates = dict(enemy_templates)

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

        # --- Evaluate each via rollout ---
        best_score = -1.0
        best_decision = candidates[0]
        best_ap_spend = 999

        # Snapshot once; restore per-branch
        # We need a RNG for the snapshot. The solver doesn't own the combat
        # RNG directly — it's on the CombatEngine. We create a temporary
        # one seeded from the state to make branches deterministic.
        import random

        rng_seed = hash((state.round_number, actor.id, actor.current_hp))
        base_rng = random.Random(rng_seed)

        snap = CombatSnapshot.take(state, base_rng)

        for candidate in candidates:
            branch_state, branch_rng = snap.restore()
            score = self._evaluate_candidate(
                branch_state, branch_rng, actor.id, candidate,
            )
            ap_spend = candidate.cheat_actions

            if score > best_score or (
                score == best_score and ap_spend < best_ap_spend
            ):
                best_score = score
                best_decision = candidate
                best_ap_spend = ap_spend

            self._stats.candidates_evaluated += 1

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

    def _evaluate_candidate(
        self,
        state: CombatState,
        rng,
        actor_id: str,
        candidate: PlayerTurnDecision,
    ) -> float:
        """Simulate the candidate decision then search deeper or rollout."""
        return self._search_ply(
            state, rng, actor_id, candidate,
            depth_remaining=self.config.search_depth - 1,
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
    ) -> float:
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
    ) -> float:
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

        best_score = -1.0
        for cand in candidates:
            branch_state, branch_rng = snap.restore()
            score = self._search_ply(
                branch_state, branch_rng, actor_id, cand,
                depth_remaining=depth_remaining - 1,
                stash=stash,
            )
            if score > best_score:
                best_score = score
            self._stats.candidates_evaluated += 1

        return best_score

    def _rollout_to_end(
        self,
        state: CombatState,
        engine: CombatEngine,
        stash: list[str],
    ) -> float:
        """Play out remaining rounds with the heuristic rollout policy."""
        remaining_stash = list(stash)
        rounds = 0
        max_rounds = self.config.max_rollout_rounds

        while not state.is_finished and rounds < max_rounds:
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
) -> CombatSolver:
    """Factory for CLI registration."""
    return CombatSolver(game_data=game_data, config=config)
