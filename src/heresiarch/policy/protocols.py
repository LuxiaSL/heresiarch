"""Policy protocols and the structured RunResult the driver emits.

CombatPolicy chooses one decision per player combatant per round.
MacroPolicy makes all between-combat choices: zone selection, shop
purchases, recruit accept/reject, lodge rest, overstay stop-condition,
and between-encounter item use.

RuleFireRecord / RunResult are the structured outputs of a run. They
are intentionally pydantic-serializable so a batch of N runs can be
dumped to JSON and analyzed downstream without re-running.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from heresiarch.engine.models.combat_state import (
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.run_state import RunState

if TYPE_CHECKING:
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneTemplate
    from heresiarch.engine.recruitment import RecruitCandidate


class LegalActionSet(BaseModel):
    """The set of legal actions for one combatant on one turn.

    Lightweight for Phase 1 — the floor policy does not consume this,
    but validation and future MCTS/golden policies will. Kept on the
    protocol surface so we don't have to re-plumb later.
    """

    actor_id: str
    available_ability_ids: list[str] = Field(default_factory=list)
    living_enemy_ids: list[str] = Field(default_factory=list)
    living_ally_ids: list[str] = Field(default_factory=list)
    taunted_by: list[str] = Field(default_factory=list)
    action_points: int = 0
    cheat_debt: int = 0
    cooldowns: dict[str, int] = Field(default_factory=dict)
    # Party stash snapshot (consumables). Updated per-actor within a round
    # so two actors can't double-claim the same potion.
    available_consumable_ids: list[str] = Field(default_factory=list)


class ItemUse(BaseModel):
    """A between-encounter item use chosen by the macro policy."""

    item_id: str
    character_id: str


class ShopAction(BaseModel):
    """A shop action (buy/sell) chosen by the macro policy.

    ``action`` is 'buy' or 'sell'. For Phase 1 we only emit 'buy'.
    """

    action: str
    item_id: str


@runtime_checkable
class CombatPolicy(Protocol):
    """Chooses one action for one combatant on one round."""

    name: str

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision: ...


@runtime_checkable
class MacroPolicy(Protocol):
    """Decides between-combat actions."""

    name: str

    def decide_visit_town(
        self, run: RunState, available_town_ids: list[str]
    ) -> str | None: ...

    def decide_zone(
        self, run: RunState, options: list[ZoneTemplate]
    ) -> ZoneTemplate | None: ...

    def decide_shop(
        self, run: RunState, available_items: list[str]
    ) -> list[ShopAction]: ...

    def decide_lodge(self, run: RunState, cost: int) -> bool: ...

    def decide_recruit(
        self, run: RunState, candidate: RecruitCandidate
    ) -> bool: ...

    def decide_overstay(self, run: RunState) -> bool: ...

    def decide_retreat_to_town(self, run: RunState) -> bool: ...

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]: ...

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int
    ) -> list[str]: ...


# ---------------------------------------------------------------------------
# Structured outputs
# ---------------------------------------------------------------------------


class RuleFireRecord(BaseModel):
    """One fire of a named rule — for policy tracing.

    Phase 1 policies are hardcoded Python so this stays mostly empty.
    Phase 2 rule-table policies will populate it heavily.
    """

    rule_name: str
    zone_id: str = ""
    encounter_index: int = 0
    round_number: int = 0
    actor_id: str = ""
    decision_summary: str = ""


class RunResult(BaseModel):
    """Structured result of one full-run simulation.

    The full BattleRecord is intentionally kept off this model — it lives
    on the final RunState and can be pulled out per-run if needed, but
    dropping it from aggregate dumps keeps batch JSON a sane size.
    """

    seed: int
    mc_job_id: str
    combat_policy_name: str
    macro_policy_name: str

    # --- Outcome ---
    is_dead: bool
    zones_cleared: list[str] = Field(default_factory=list)
    farthest_zone: str = ""
    farthest_zone_level: int = 0
    encounters_cleared: int = 0

    # --- Final state (when alive) ---
    final_party_hp_pct: float = 0.0  # mean across active party
    final_mc_level: int = 0
    final_gold: int = 0

    # --- Death (when dead) ---
    killed_at_zone: str = ""
    killed_at_encounter: int = 0
    killed_by: str = ""  # enemy template id or empty

    # --- Economy / flow metrics ---
    rounds_taken_total: int = 0
    gold_earned_combat: int = 0  # net gold from loot drops (after enemy theft)
    gold_spent_shop: int = 0
    gold_spent_lodge: int = 0
    lodge_rests: int = 0
    shop_purchases: int = 0
    recruits_accepted: int = 0
    recruits_declined: int = 0

    # --- Termination cause ---
    # "dead", "max_encounters", "no_available_zones", "clean_exit"
    termination_reason: str = "clean_exit"

    # --- Trace (capped to keep JSON small; toggle full trace via driver hook) ---
    rule_trace: list[RuleFireRecord] = Field(default_factory=list)
