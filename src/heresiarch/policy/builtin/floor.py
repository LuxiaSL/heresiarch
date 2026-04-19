"""Floor combat policy: the resilience floor.

Always basic_attack the first living enemy. Never cheat, never survive.
This answers the question: "can this job carry itself with zero thought?"

The gap between floor performance and golden-policy performance is the
headroom the job has to reward engaged play. A job that floors to zone
5 has a lot less policy surface than one that floors to zone 1.
"""

from __future__ import annotations

from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.policy.protocols import LegalActionSet


class FloorCombatPolicy:
    """Always basic_attack the first living enemy."""

    name: str = "floor"

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision:
        target_ids: list[str] = []
        if legal.living_enemy_ids:
            target_ids = [legal.living_enemy_ids[0]]

        primary = CombatAction(
            actor_id=actor.id,
            ability_id="basic_attack",
            target_ids=target_ids,
        )

        return PlayerTurnDecision(
            combatant_id=actor.id,
            cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=primary,
        )
