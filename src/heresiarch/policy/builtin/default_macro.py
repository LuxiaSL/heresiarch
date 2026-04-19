"""Default macro policy: conservative between-combat baseline.

Decisions:
  - Visit town after leaving a zone only if average party HP is below a
    threshold AND we have a town available. Towns exist primarily to
    heal and gear up; visiting wastes a turn otherwise.
  - Pick the highest-level unlocked and uncleared zone. When everything
    is cleared, return None (run ends cleanly).
  - Shop: if MC has no weapon, buy the cheapest affordable equippable
    weapon. Otherwise, stockpile one minor potion per 50g affordable
    (rough heuristic).
  - Lodge when mean HP% < LODGE_HP_THRESHOLD and cost is affordable
    (cost < LODGE_COST_FRACTION * gold).
  - Accept recruits if party has an open slot (active+reserve < 4).
  - Never overstay cleared zones.
  - Use a minor potion on any living party member at <30% HP between
    encounters, if we have one in stash.
  - Loot: take everything that fits.

These are the conservative baselines. Future macro policies will be
rule-table driven (spec Phase 3), just like combat policies will be.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from heresiarch.engine.models.run_state import RunState
from heresiarch.policy.protocols import ItemUse, ShopAction

if TYPE_CHECKING:
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneTemplate
    from heresiarch.engine.recruitment import RecruitCandidate


# Thresholds
TOWN_VISIT_HP_THRESHOLD: float = 0.70  # visit town if mean HP% below this
LODGE_HP_THRESHOLD: float = 0.40       # rest if mean HP% below this
LODGE_COST_FRACTION: float = 0.50      # ...and lodge cost < this fraction of gold
INTER_ENCOUNTER_HEAL_THRESHOLD: float = 0.30  # use potion below this HP%
MAX_RECRUIT_PARTY_SIZE: int = 4         # active + reserve cap


class DefaultMacroPolicy:
    """Conservative defaults for all macro decisions."""

    name: str = "default_macro"

    # -----------------------------------------------------------------
    # Town / zone
    # -----------------------------------------------------------------

    def decide_visit_town(
        self, run: RunState, available_town_ids: list[str]
    ) -> str | None:
        if not available_town_ids:
            return None
        mean_hp_pct = _mean_party_hp_pct(run)
        if mean_hp_pct < TOWN_VISIT_HP_THRESHOLD:
            return available_town_ids[0]
        return None

    def decide_zone(
        self, run: RunState, options: list[ZoneTemplate]
    ) -> ZoneTemplate | None:
        uncleared = [z for z in options if z.id not in run.zones_completed]
        if not uncleared:
            return None
        # Highest zone_level first — aggressive advancement
        uncleared.sort(key=lambda z: z.zone_level, reverse=True)
        # But cap at "probably winnable" — lowest unlocked-uncleared zone
        # (advancing too aggressively is a common floor-policy death trap)
        uncleared.sort(key=lambda z: z.zone_level)
        return uncleared[0]

    # -----------------------------------------------------------------
    # Shop
    # -----------------------------------------------------------------

    def decide_shop(
        self, run: RunState, available_items: list[str]
    ) -> list[ShopAction]:
        # We don't have item details here — the driver resolves prices
        # and calls shop_engine directly. To keep the protocol clean,
        # emit ShopActions as "try to buy these in order; driver skips
        # unaffordable ones and stops when stash fills".
        mc = _get_mc(run)
        mc_has_weapon = mc is not None and mc.equipment.get("WEAPON") is not None

        actions: list[ShopAction] = []
        if not mc_has_weapon:
            # Try each shop item in order — driver will buy the first
            # affordable weapon that the MC can equip.
            for item_id in available_items:
                actions.append(ShopAction(action="buy", item_id=item_id))

        # Also stockpile a minor potion if available.
        if "minor_potion" in available_items:
            actions.append(ShopAction(action="buy", item_id="minor_potion"))

        return actions

    def decide_lodge(self, run: RunState, cost: int) -> bool:
        if cost <= 0:
            return False
        mean_hp_pct = _mean_party_hp_pct(run)
        if mean_hp_pct >= LODGE_HP_THRESHOLD:
            return False
        if run.party.money < cost:
            return False
        if cost / max(1, run.party.money) > LODGE_COST_FRACTION:
            return False
        return True

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
        # Default: never retreat mid-zone. Commit to each zone we enter.
        return False

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]:
        uses: list[ItemUse] = []
        potions_in_stash = [
            iid for iid in run.party.stash if iid == "minor_potion"
        ]
        if not potions_in_stash:
            return uses
        # Heal most-wounded character first (greedy); one potion max per
        # turn to avoid over-healing.
        active_chars = [
            run.party.characters[cid] for cid in run.party.active
            if cid in run.party.characters
        ]
        wounded = [
            c for c in active_chars
            if c.current_hp / max(1, c.max_hp) < INTER_ENCOUNTER_HEAL_THRESHOLD
        ]
        wounded.sort(key=lambda c: c.current_hp / max(1, c.max_hp))
        for c in wounded:
            if not potions_in_stash:
                break
            uses.append(ItemUse(item_id=potions_in_stash.pop(0), character_id=c.id))
        return uses

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int
    ) -> list[str]:
        return list(loot.item_ids)[:max(0, free_stash_slots)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_mc(run: RunState):
    for char in run.party.characters.values():
        if char.is_mc:
            return char
    return None


def _mean_party_hp_pct(run: RunState) -> float:
    active = [
        run.party.characters[cid] for cid in run.party.active
        if cid in run.party.characters
    ]
    if not active:
        return 1.0
    total = sum(c.current_hp / max(1, c.max_hp) for c in active)
    return total / len(active)
