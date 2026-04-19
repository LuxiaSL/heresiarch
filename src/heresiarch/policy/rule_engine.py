"""Rule engine: priority-ordered (predicate, action) rules for combat policies.

Phase 1 golden policies live as hardcoded Python tables. Each policy is a
``RuleBasedCombatPolicy`` holding a list of ``Rule``s that are checked
in order; first match wins. The structure matches what a future YAML
rule DSL will execute, so the eventual DSL refactor is mechanical.

Designer-written logic lives in each golden's rule list; the engine
just iterates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData

    from heresiarch.policy.protocols import LegalActionSet


@dataclass
class RuleContext:
    """All the state a predicate or action closure needs to fire.

    Closures are free to pull additional info off the game_data
    (abilities, items, enemies). Kept loose on purpose so Phase 2
    rule authors aren't box-bound.
    """

    state: CombatState
    actor: CombatantState
    legal: LegalActionSet
    game_data: GameData


@dataclass
class Rule:
    """One rule in a priority table.

    ``predicate`` takes a ``RuleContext`` and returns True if this rule
    should fire. ``action`` takes the same context and returns a fully-
    formed ``PlayerTurnDecision``. First matching rule wins.

    ``name`` is the tag carried into the rule-fire trace for debugging.
    """

    name: str
    predicate: Callable[[RuleContext], bool]
    action: Callable[[RuleContext], PlayerTurnDecision]


class RuleBasedCombatPolicy:
    """Priority-list combat policy. First matching rule wins."""

    def __init__(
        self,
        name: str,
        rules: list[Rule],
        game_data: GameData,
    ):
        self.name = name
        self.rules = rules
        self.game_data = game_data

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision:
        ctx = RuleContext(
            state=state,
            actor=actor,
            legal=legal,
            game_data=self.game_data,
        )
        for rule in self.rules:
            if rule.predicate(ctx):
                return rule.action(ctx)
        # Every rule table should end with an always-true fallback, but
        # be defensive if the author forgot — default to SURVIVE.
        return PlayerTurnDecision(
            combatant_id=actor.id,
            cheat_survive=CheatSurviveChoice.SURVIVE,
        )
