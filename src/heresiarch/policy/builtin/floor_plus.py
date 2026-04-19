"""Floor+ policies: the cheapest-possible "play defense" baseline.

Combat policy (``FloorPlusCombatPolicy``):
  1. If HP < 50% and a minor_potion is in the party stash → use_item on self.
  2. If 3+ AP banked → CHEAT spending 3 AP (4 basic_attacks on first enemy).
  3. Otherwise → SURVIVE (bank 1 AP, halve incoming damage).

Macro policy (``FloorPlusMacroPolicy``):
  - Visit town when gold ≥ 50 and fewer than 3 potions in stash
    (stockpile-to-threshold), OR when mean HP < 70%.
  - At shop: buy only potions (no weapon/armor tuning). Driver stops
    when unaffordable or stash full.
  - No lodge (keep it dumb — heal via potions only).
  - Accept recruits if party has an open slot. Same zone/overstay/loot
    behavior as the default macro.
  - Between-encounter heal threshold: HP < 50% (vs 30% in default).

This is the "one step above strict floor" baseline. It measures what the
engine's core defensive loop (survive→cheat with potion-patching) lets
you accomplish without any targeting, ability, or timing intuition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.run_state import RunState
from heresiarch.policy.protocols import ItemUse, LegalActionSet, ShopAction

if TYPE_CHECKING:
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneTemplate
    from heresiarch.engine.recruitment import RecruitCandidate


# Thresholds
COMBAT_POTION_HP_THRESHOLD: float = 0.50
CHEAT_AP_THRESHOLD: int = 3
CHEAT_AP_SPEND: int = 3

TOWN_VISIT_HP_THRESHOLD: float = 0.70
TOWN_VISIT_GOLD_THRESHOLD: int = 50
POTION_STOCKPILE_TARGET: int = 3
BETWEEN_HEAL_HP_THRESHOLD: float = 0.50
MAX_RECRUIT_PARTY_SIZE: int = 4

POTION_ITEM_ID: str = "minor_potion"


class FloorPlusCombatPolicy:
    """Minimum viable defense: potion → cheat-3 → survive."""

    name: str = "floor_plus"

    def decide(
        self,
        state: CombatState,
        actor: CombatantState,
        legal: LegalActionSet,
    ) -> PlayerTurnDecision:
        # Priority 1: emergency potion on self.
        hp_pct = actor.current_hp / max(1, actor.max_hp)
        if hp_pct < COMBAT_POTION_HP_THRESHOLD:
            potions = [
                iid for iid in legal.available_consumable_ids
                if iid == POTION_ITEM_ID
            ]
            if potions:
                return PlayerTurnDecision(
                    combatant_id=actor.id,
                    cheat_survive=CheatSurviveChoice.NORMAL,
                    primary_action=CombatAction(
                        actor_id=actor.id,
                        ability_id="use_item",
                        item_id=potions[0],
                        target_ids=[actor.id],
                    ),
                )

        # Priority 2: cheat-spend when enough AP is banked.
        if actor.action_points >= CHEAT_AP_THRESHOLD:
            target = (
                [legal.living_enemy_ids[0]] if legal.living_enemy_ids else []
            )
            primary = CombatAction(
                actor_id=actor.id,
                ability_id="basic_attack",
                target_ids=target,
            )
            extras = [
                CombatAction(
                    actor_id=actor.id,
                    ability_id="basic_attack",
                    target_ids=target,
                )
                for _ in range(CHEAT_AP_SPEND)
            ]
            return PlayerTurnDecision(
                combatant_id=actor.id,
                cheat_survive=CheatSurviveChoice.CHEAT,
                cheat_actions=CHEAT_AP_SPEND,
                primary_action=primary,
                cheat_extra_actions=extras,
            )

        # Priority 3: survive to bank AP.
        return PlayerTurnDecision(
            combatant_id=actor.id,
            cheat_survive=CheatSurviveChoice.SURVIVE,
        )


class FloorPlusMacroPolicy:
    """Conservative macro with aggressive potion stockpiling."""

    name: str = "floor_plus_macro"

    # -----------------------------------------------------------------
    # Town / zone
    # -----------------------------------------------------------------

    def decide_visit_town(
        self, run: RunState, available_town_ids: list[str]
    ) -> str | None:
        if not available_town_ids:
            return None

        potion_count = sum(
            1 for iid in run.party.stash if iid == POTION_ITEM_ID
        )
        stash_free = STASH_LIMIT - len(run.party.stash)
        wants_potions = (
            run.party.money >= TOWN_VISIT_GOLD_THRESHOLD
            and potion_count < POTION_STOCKPILE_TARGET
            and stash_free >= 1  # don't visit if we can't actually store a potion
        )
        if wants_potions:
            return available_town_ids[0]

        if _mean_party_hp_pct(run) < TOWN_VISIT_HP_THRESHOLD:
            return available_town_ids[0]

        return None

    def decide_zone(
        self, run: RunState, options: list[ZoneTemplate]
    ) -> ZoneTemplate | None:
        uncleared = [z for z in options if z.id not in run.zones_completed]
        if not uncleared:
            return None
        # Lowest-level-first advancement (same as default_macro).
        uncleared.sort(key=lambda z: z.zone_level)
        return uncleared[0]

    # -----------------------------------------------------------------
    # Shop
    # -----------------------------------------------------------------

    def decide_shop(
        self, run: RunState, available_items: list[str]
    ) -> list[ShopAction]:
        # Floor+ is dumb: buy potions only. No weapon shopping.
        actions: list[ShopAction] = []
        if POTION_ITEM_ID not in available_items:
            return actions

        # Emit enough buy actions to fill to the stockpile target. The
        # driver will skip unaffordable purchases and stop when stash is
        # full.
        potion_count = sum(
            1 for iid in run.party.stash if iid == POTION_ITEM_ID
        )
        needed = max(0, POTION_STOCKPILE_TARGET - potion_count)
        for _ in range(needed):
            actions.append(ShopAction(action="buy", item_id=POTION_ITEM_ID))
        return actions

    def decide_lodge(self, run: RunState, cost: int) -> bool:
        # Floor+ does not lodge — healing is strictly via potions.
        return False

    # -----------------------------------------------------------------
    # Recruitment
    # -----------------------------------------------------------------

    def decide_recruit(
        self, run: RunState, candidate: RecruitCandidate
    ) -> bool:
        current = len(run.party.active) + len(run.party.reserve)
        return current < MAX_RECRUIT_PARTY_SIZE

    # -----------------------------------------------------------------
    # Zone tactical
    # -----------------------------------------------------------------

    def decide_overstay(self, run: RunState) -> bool:
        return False

    def decide_retreat_to_town(self, run: RunState) -> bool:
        """Retreat mid-zone to restock potions when affordable and low.

        Floor+ only retreats when we could actually restock: gold
        threshold AND stockpile below target AND stash has room for at
        least one potion. Without the stash-room check, a stash full of
        loot would cause an infinite retreat→shop-nothing→retreat loop.
        """
        potion_count = sum(
            1 for iid in run.party.stash if iid == POTION_ITEM_ID
        )
        if potion_count >= POTION_STOCKPILE_TARGET:
            return False
        if run.party.money < TOWN_VISIT_GOLD_THRESHOLD:
            return False
        if STASH_LIMIT - len(run.party.stash) < 1:
            return False
        return True

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]:
        uses: list[ItemUse] = []
        potions = [iid for iid in run.party.stash if iid == POTION_ITEM_ID]
        if not potions:
            return uses
        active_chars = [
            run.party.characters[cid] for cid in run.party.active
            if cid in run.party.characters
        ]
        wounded = [
            c for c in active_chars
            if c.current_hp / max(1, c.max_hp) < BETWEEN_HEAL_HP_THRESHOLD
        ]
        wounded.sort(key=lambda c: c.current_hp / max(1, c.max_hp))
        for c in wounded:
            if not potions:
                break
            uses.append(ItemUse(item_id=potions.pop(0), character_id=c.id))
        return uses

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int
    ) -> list[str]:
        return list(loot.item_ids)[:max(0, free_stash_slots)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mean_party_hp_pct(run: RunState) -> float:
    active = [
        run.party.characters[cid] for cid in run.party.active
        if cid in run.party.characters
    ]
    if not active:
        return 1.0
    total = sum(c.current_hp / max(1, c.max_hp) for c in active)
    return total / len(active)
