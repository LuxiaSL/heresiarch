"""Macro solver: search-based between-combat decisions.

Wraps GoldenMacroPolicy for defaults, overrides key decisions
(retreat-vs-continue) with forward simulation using RunSnapshot
branching and encounter simulation.

The combat solver finds optimal play within a fight; the macro solver
finds optimal play between fights — when to retreat, heal, restock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.formulas import calculate_buy_price
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    PlayerTurnDecision,
)
from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.policy.builtin.golden_macro import (
    GoldenMacroConfig,
    GoldenMacroPolicy,
    POTION_ITEM_ID,
    _count_potions,
    _mean_party_hp_pct,
)
from heresiarch.policy.protocols import ItemUse, ShopAction
from heresiarch.policy.snapshot import RunSnapshot
from heresiarch.policy.solver import CombatSolver, SolverConfig
from heresiarch.policy.validation import ValidationError, compute_legal, resolve_decision

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.combat_state import CombatState
    from heresiarch.engine.models.enemies import EnemyTemplate
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneTemplate
    from heresiarch.engine.recruitment import RecruitCandidate


@dataclass
class MacroSolverConfig:
    """Configuration for the macro solver's search behavior."""

    lookahead_encounters: int = 3
    retreat_search: bool = True
    eval_solver_depth: int = 1
    eval_solver_prune: int = 20
    # Quick-skip: don't bother searching when answer is obvious
    skip_retreat_hp_pct: float = 0.85
    skip_retreat_min_potions: int = 2
    # Scoring weights — encounters survived dominates. HP/potions are
    # tiebreakers, not reasons to retreat on their own.
    encounter_weight: float = 10.0
    hp_weight: float = 1.0
    potion_weight: float = 0.5
    gold_weight: float = 0.001
    # Retreat must beat continue by this margin to fire. Prevents
    # "marginally better retreat" from causing stuck loops.
    retreat_margin: float = 1.0
    max_combat_rounds: int = 200


@dataclass
class MacroSolverStats:
    """Per-run statistics for debugging and performance monitoring."""

    retreat_searches: int = 0
    retreat_chosen: int = 0
    continue_chosen: int = 0
    skipped_healthy: int = 0
    skipped_no_town: int = 0
    encounters_simulated: int = 0


class MacroSolver:
    """Search-based macro policy.

    Delegates most decisions to a base GoldenMacroPolicy. Overrides
    ``decide_retreat_to_town`` with forward simulation: snapshots the
    run state, simulates "continue fighting" vs "retreat to town and
    come back," picks the branch with the higher score.
    """

    name: str = "macro_solver"

    def __init__(
        self,
        game_data: GameData,
        combat_policy: CombatSolver,
        base_macro: GoldenMacroPolicy,
        config: MacroSolverConfig | None = None,
    ):
        self.game_data = game_data
        self.combat_policy = combat_policy
        self.base_macro = base_macro
        self.solver_config = config or MacroSolverConfig()
        self._game_loop: GameLoop | None = None
        self._stats = MacroSolverStats()
        # Cooldown: after retreating, must fight at least 1 encounter
        # before considering retreat again. Prevents stuck loops.
        self._retreat_cooldown: bool = False

        self._eval_solver = CombatSolver(
            game_data=game_data,
            config=SolverConfig(
                search_depth=self.solver_config.eval_solver_depth,
                prune_after_ply=self.solver_config.eval_solver_prune,
            ),
        )

    @property
    def config(self) -> GoldenMacroConfig:
        """Expose base macro config for the run driver's heal loop."""
        return self.base_macro.config

    @property
    def stats(self) -> MacroSolverStats:
        return self._stats

    def set_game_loop(self, gl: GameLoop) -> None:
        """Bind to the driver's GameLoop for RNG access during branching."""
        self._game_loop = gl

    # ------------------------------------------------------------------
    # Delegated methods (pass-through to base macro)
    # ------------------------------------------------------------------

    def decide_visit_town(
        self, run: RunState, available_town_ids: list[str],
    ) -> str | None:
        return self.base_macro.decide_visit_town(run, available_town_ids)

    def decide_zone(
        self, run: RunState, options: list[ZoneTemplate],
    ) -> ZoneTemplate | None:
        return self.base_macro.decide_zone(run, options)

    def decide_shop(
        self, run: RunState, available_items: list[str],
    ) -> list[ShopAction]:
        return self.base_macro.decide_shop(run, available_items)

    def decide_lodge(self, run: RunState, cost: int) -> bool:
        return self.base_macro.decide_lodge(run, cost)

    def decide_recruit(
        self, run: RunState, candidate: RecruitCandidate,
    ) -> bool:
        return self.base_macro.decide_recruit(run, candidate)

    def decide_overstay(self, run: RunState) -> bool:
        return self.base_macro.decide_overstay(run)

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int,
    ) -> list[str]:
        return self.base_macro.decide_loot_pick(run, loot, free_stash_slots)

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]:
        return self.base_macro.decide_between_encounter_items(run)

    # ------------------------------------------------------------------
    # Searched: retreat vs continue
    # ------------------------------------------------------------------

    def decide_retreat_to_town(self, run: RunState) -> bool:
        """Search-based retreat decision.

        Compares "continue fighting" vs "retreat to town, heal, come
        back" by simulating the next N encounters in each branch and
        scoring the outcomes.
        """
        if not self.solver_config.retreat_search:
            return self.base_macro.decide_retreat_to_town(run)

        if self._game_loop is None:
            return self.base_macro.decide_retreat_to_town(run)

        # Cooldown: after a retreat, must fight at least 1 encounter
        # before considering retreat again. Reset the flag and continue.
        if self._retreat_cooldown:
            self._retreat_cooldown = False
            return False

        # Quick-skip: healthy party doesn't need to search
        hp_pct = _mean_party_hp_pct(run)
        potions = _count_potions(run)
        if (
            hp_pct >= self.solver_config.skip_retreat_hp_pct
            and potions >= self.solver_config.skip_retreat_min_potions
        ):
            self._stats.skipped_healthy += 1
            return False

        # Can we even get to a town?
        if not self._can_retreat_to_town(run):
            self._stats.skipped_no_town += 1
            return False

        self._stats.retreat_searches += 1
        gl = self._game_loop

        # Snapshot current state + RNG
        snap = RunSnapshot.take(run, gl.rng)
        n = self.solver_config.lookahead_encounters

        # Branch 1: continue fighting from here
        continue_run, continue_rng = snap.restore(gl)
        continue_gl = GameLoop(self.game_data, continue_rng)
        continue_run, continue_survived = self._simulate_encounters(
            continue_run, continue_gl, n,
        )
        continue_score = self._score_branch(continue_run, continue_survived)

        # Branch 2: retreat → town → heal/shop → re-enter zone → fight
        retreat_run, retreat_rng = snap.restore(gl)
        retreat_gl = GameLoop(self.game_data, retreat_rng)
        retreat_run = self._simulate_retreat(retreat_run, retreat_gl)
        if retreat_run is not None and not retreat_run.is_dead:
            retreat_run, retreat_survived = self._simulate_encounters(
                retreat_run, retreat_gl, n,
            )
            retreat_score = self._score_branch(retreat_run, retreat_survived)
        else:
            retreat_score = -1.0

        if retreat_score > continue_score + self.solver_config.retreat_margin:
            self._stats.retreat_chosen += 1
            self._retreat_cooldown = True
            return True
        else:
            self._stats.continue_chosen += 1
            return False

    # ------------------------------------------------------------------
    # Branch simulation helpers
    # ------------------------------------------------------------------

    def _can_retreat_to_town(self, run: RunState) -> bool:
        """Check if retreating to a town is possible and useful."""
        gl = self._game_loop
        if gl is None:
            return False
        region = gl.get_region_for_run(run)
        if region is None:
            return False
        has_town = False
        for town in self.game_data.towns.values():
            if town.region == region and gl.is_town_unlocked(run, town.id):
                has_town = True
                break
        if not has_town:
            return False

        # Don't retreat if we can't actually do anything useful in town:
        # need gold (or sellable loot) to buy potions, or already have
        # potions to use in the heal loop.
        potion = self.game_data.items.get(POTION_ITEM_ID)
        if potion is not None:
            price = calculate_buy_price(potion.base_price, run.party.cha)
            has_gold = run.party.money >= price
            has_sellable = any(
                iid != POTION_ITEM_ID for iid in run.party.stash
            )
            has_potions = _count_potions(run) > 0
            if not has_gold and not has_sellable and not has_potions:
                return False

        return True

    def _simulate_retreat(
        self, run: RunState, gl: GameLoop,
    ) -> RunState | None:
        """Simulate: leave zone -> visit town -> heal/shop -> re-enter zone."""
        zone_id = run.current_zone_id
        if not zone_id:
            return None

        # Leave zone (saves progress so we resume at same encounter)
        run = gl.leave_zone(run)

        # Find an available town
        region = gl.get_region_for_run(run)
        if not region:
            return None
        town_id: str | None = None
        for town in self.game_data.towns.values():
            if town.region == region and gl.is_town_unlocked(run, town.id):
                town_id = town.id
                break
        if not town_id:
            return None

        # Enter town
        try:
            run = gl.enter_town(run, town_id)
        except ValueError:
            return None

        # Shop using base macro decisions
        available_items = gl.resolve_town_shop(run)
        actions = self.base_macro.decide_shop(run, available_items)
        run = self._apply_shop_actions_branch(run, gl, actions)

        # Heal loop (buy potion → use → repeat)
        run = self._heal_loop_branch(run, gl)

        # Leave town
        if run.current_town_id:
            run = gl.leave_town(run)

        # Re-enter zone at saved progress
        try:
            run = gl.enter_zone(run, zone_id)
        except ValueError:
            return None

        return run

    def _simulate_encounters(
        self,
        run: RunState,
        gl: GameLoop,
        n: int,
    ) -> tuple[RunState, int]:
        """Simulate up to *n* encounters forward, return (final_state, survived)."""
        survived = 0
        solver = self._eval_solver

        for _ in range(n):
            if run.is_dead or not run.current_zone_id:
                break

            # Between-encounter healing (delegate to base macro)
            uses = self.base_macro.decide_between_encounter_items(run)
            for use in uses:
                if use.item_id in run.party.stash:
                    try:
                        run = gl.use_consumable(run, use.item_id, use.character_id)
                    except ValueError:
                        pass

            # Generate encounter
            try:
                enemies = gl.get_next_encounter(run)
            except ValueError:
                break

            # Set up combat
            characters = [
                run.party.characters[cid]
                for cid in run.party.active
                if cid in run.party.characters
            ]
            if not characters:
                break

            state = gl.combat_engine.initialize_combat(
                characters, enemies, party_gold=run.party.money,
            )

            # Build enemy template maps
            enemy_templates: dict[str, EnemyTemplate] = {}
            enemy_combatant_templates: dict[str, str] = {}
            for i, c in enumerate(state.enemy_combatants):
                if i < len(enemies):
                    tmpl_id = enemies[i].template_id
                    enemy_combatant_templates[c.id] = tmpl_id
                    tmpl = self.game_data.enemies.get(tmpl_id)
                    if tmpl:
                        enemy_templates[tmpl_id] = tmpl

            solver.set_context(
                stash=list(run.party.stash),
                enemy_templates=enemy_templates,
            )

            # Run combat loop
            rounds = 0
            while (
                not state.is_finished
                and rounds < self.solver_config.max_combat_rounds
            ):
                state.log = []
                decisions = self._collect_branch_decisions(
                    state, solver, list(run.party.stash),
                )
                state = gl.combat_engine.process_round(
                    state, decisions, enemy_templates,
                )
                rounds += 1

                # Sync consumed items to run stash
                if state.consumed_items:
                    new_stash = list(run.party.stash)
                    for iid in state.consumed_items:
                        try:
                            new_stash.remove(iid)
                        except ValueError:
                            pass
                    run = run.model_copy(
                        update={"party": run.party.model_copy(update={"stash": new_stash})}
                    )
                    state.consumed_items = []

            self._stats.encounters_simulated += 1

            if not (state.is_finished and state.player_won):
                run = gl.handle_death(run)
                break

            # Post-combat: XP, loot, zone advance
            combat_result = self._build_combat_result_branch(
                state, run, enemy_combatant_templates,
            )
            run, loot = gl.resolve_combat_result(run, combat_result)

            free_slots = STASH_LIMIT - len(run.party.stash)
            keep = list(loot.item_ids)[: max(0, free_slots)]
            run = gl.apply_loot(run, loot, keep)

            try:
                run = gl.advance_zone(run)
            except ValueError:
                break

            survived += 1

            # Respect overstay decisions
            if run.zone_state and run.zone_state.is_cleared:
                if not self.base_macro.decide_overstay(run):
                    break

        return run, survived

    def _collect_branch_decisions(
        self,
        state: CombatState,
        solver: CombatSolver,
        stash: list[str],
    ) -> dict[str, PlayerTurnDecision]:
        """Lightweight decision collection for branch simulation."""
        decisions: dict[str, PlayerTurnDecision] = {}
        remaining_stash = list(stash)

        for actor in state.living_players:
            legal = compute_legal(state, actor, stash=remaining_stash)
            raw = solver.decide(state, actor, legal)
            try:
                resolved, _ = resolve_decision(
                    raw, state, actor,
                    self.game_data.abilities, legal,
                )
            except (ValidationError, Exception):
                target = (
                    [state.living_enemies[0].id]
                    if state.living_enemies
                    else []
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

            # Claim consumables from running stash
            if resolved.primary_action and resolved.primary_action.item_id:
                try:
                    remaining_stash.remove(resolved.primary_action.item_id)
                except ValueError:
                    pass
            for extra in resolved.cheat_extra_actions:
                if extra.item_id:
                    try:
                        remaining_stash.remove(extra.item_id)
                    except ValueError:
                        pass

            decisions[actor.id] = resolved

        return decisions

    def _build_combat_result_branch(
        self,
        state: CombatState,
        run: RunState,
        enemy_combatant_templates: dict[str, str],
    ) -> CombatResult:
        """Lightweight CombatResult builder for branch simulation."""
        surviving_ids = [c.id for c in state.player_combatants if c.is_alive]
        surviving_hp = {
            c.id: c.current_hp
            for c in state.player_combatants
            if c.is_alive
        }

        defeated_templates: list[str] = []
        defeated_budgets: list[float] = []
        defeated_levels: list[int] = []
        defeated_xp_mults: list[float] = []
        defeated_gold_mults: list[float] = []

        for c in state.enemy_combatants:
            if c.is_alive:
                continue
            tmpl_id = enemy_combatant_templates.get(
                c.id, c.id.rsplit("_", 1)[0],
            )
            defeated_templates.append(tmpl_id)
            defeated_levels.append(c.level)
            tmpl = self.game_data.enemies.get(tmpl_id)
            if tmpl:
                defeated_budgets.append(tmpl.budget_multiplier)
                defeated_xp_mults.append(tmpl.xp_multiplier or 0.0)
                defeated_gold_mults.append(tmpl.gold_multiplier or 0.0)
            else:
                defeated_budgets.append(0.0)
                defeated_xp_mults.append(0.0)
                defeated_gold_mults.append(0.0)

        zone_level = 0
        if run.current_zone_id:
            zone = self.game_data.zones.get(run.current_zone_id)
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

    def _apply_shop_actions_branch(
        self,
        run: RunState,
        gl: GameLoop,
        actions: list[ShopAction],
    ) -> RunState:
        """Apply shop buy/sell actions in a branch simulation."""
        for act in actions:
            if act.action == "sell":
                if act.item_id not in run.party.stash:
                    continue
                try:
                    new_party = gl.shop_engine.sell_item(run.party, act.item_id)
                except ValueError:
                    continue
                run = run.model_copy(update={"party": new_party})

            elif act.action == "buy":
                item = self.game_data.items.get(act.item_id)
                if item is None:
                    continue
                price = calculate_buy_price(item.base_price, run.party.cha)
                if run.party.money < price or len(run.party.stash) >= STASH_LIMIT:
                    continue
                try:
                    new_party = gl.shop_engine.buy_item(
                        run.party, act.item_id, price,
                    )
                except ValueError:
                    continue
                run = run.model_copy(update={"party": new_party})

        # Auto-equip weapon/armor on MC
        run = self._auto_equip_branch(run, gl)
        return run

    def _auto_equip_branch(self, run: RunState, gl: GameLoop) -> RunState:
        """Auto-equip weapon/armor on MC in branch simulation."""
        from heresiarch.engine.models.items import EquipType

        mc = None
        for char in run.party.characters.values():
            if char.is_mc:
                mc = char
                break
        if mc is None:
            return run

        for slot, equip_type in [
            ("WEAPON", EquipType.WEAPON),
            ("ARMOR", EquipType.ARMOR),
        ]:
            if mc.equipment.get(slot) is not None:
                continue
            for iid in list(run.party.stash):
                item = self.game_data.items.get(iid)
                if item is None or item.is_consumable:
                    continue
                if item.equip_type != equip_type:
                    continue
                try:
                    run = gl.equip_item(run, mc.id, iid, slot)
                except ValueError:
                    continue
                mc = run.party.characters.get(mc.id)
                if mc is None:
                    return run
                break

        return run

    def _heal_loop_branch(self, run: RunState, gl: GameLoop) -> RunState:
        """Buy-use-buy-use healing loop in branch simulation."""
        target_pct = self.base_macro.config.in_town_heal_target_pct
        available_items = gl.resolve_town_shop(run)
        if POTION_ITEM_ID not in available_items:
            return run

        for _ in range(20):
            active = [
                run.party.characters[cid]
                for cid in run.party.active
                if cid in run.party.characters
            ]
            wounded = [
                c
                for c in active
                if c.current_hp / max(1, c.max_hp) < target_pct
                and (c.max_hp - c.current_hp) >= 10
            ]
            if not wounded:
                break

            # Buy a potion if we don't have one
            if POTION_ITEM_ID not in run.party.stash:
                item = self.game_data.items.get(POTION_ITEM_ID)
                if item is None:
                    break
                price = calculate_buy_price(item.base_price, run.party.cha)
                if run.party.money < price or len(run.party.stash) >= STASH_LIMIT:
                    break
                try:
                    new_party = gl.shop_engine.buy_item(
                        run.party, POTION_ITEM_ID, price,
                    )
                except ValueError:
                    break
                run = run.model_copy(update={"party": new_party})

            target = min(
                wounded, key=lambda c: c.current_hp / max(1, c.max_hp),
            )
            try:
                run = gl.use_consumable(run, POTION_ITEM_ID, target.id)
            except ValueError:
                break

        return run

    def _score_branch(
        self, run: RunState, encounters_survived: int,
    ) -> float:
        """Score a macro branch outcome.

        Primary: encounters survived (more = better).
        Secondary: mean party HP% (higher = more runway).
        Tertiary: gold + potions (resources for future fights).

        Dead runs get zero HP/resource credit — healing before dying
        shouldn't score higher than dying immediately.
        """
        cfg = self.solver_config
        if run.is_dead:
            return encounters_survived * cfg.encounter_weight
        hp_pct = _mean_party_hp_pct(run)
        potions = _count_potions(run)
        return (
            encounters_survived * cfg.encounter_weight
            + hp_pct * cfg.hp_weight
            + potions * cfg.potion_weight
            + run.party.money * cfg.gold_weight
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def make_macro_solver(
    game_data: GameData,
    combat_policy: CombatSolver,
    base_macro: GoldenMacroPolicy | None = None,
    config: MacroSolverConfig | None = None,
    job_id: str | None = None,
) -> MacroSolver:
    """Factory for CLI registration.

    If ``base_macro`` is not provided, auto-selects per-job config
    from ``job_id``. Falls back to einherjar if job_id is unknown.
    ``game_loop`` is set later by the run driver via ``set_game_loop``.
    """
    if base_macro is None:
        from heresiarch.policy.builtin.golden_macro import make_golden_macro_for_job

        base_macro = make_golden_macro_for_job(game_data, job_id or "einherjar")
    return MacroSolver(
        game_data=game_data,
        combat_policy=combat_policy,
        base_macro=base_macro,
        config=config,
    )
