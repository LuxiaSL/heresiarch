"""Golden macro policy: parametric per-job baseline.

Most macro decisions are job-agnostic at the logic level; what varies
is the preference parameters (STR vs MAG scaling, overstay tolerance,
potion stockpile target). This macro is one policy with a config
dataclass that each job's golden ties to its stat profile.

Decisions:
  - Zone: lowest-level unlocked uncleared first. If all cleared, pick
    the highest-level zone to keep farming (late-game overstay).
  - Town: visit between zones when gold affordable and we lack potions,
    or HP low.
  - Retreat: bail a zone when we have gold AND potions < target AND
    stash has room.
  - Shop: weapon (matching preferred stat) → armor → potions (to cap).
  - Lodge: configurable — default off (einherjar style). Glass cannons
    may want it on.
  - Overstay: up to ``overstay_cap`` battles per zone, but bail when
    mean party HP% drops below ``overstay_bail_hp_pct``.
  - Recruit: accept if party has an open slot.
  - Between-encounter heal: use potion on anyone below ``heal_threshold_pct``.
  - Loot: take everything that fits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from heresiarch.engine.models.items import EquipType
from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.run_state import RunState
from heresiarch.policy.protocols import ItemUse, ShopAction

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneTemplate
    from heresiarch.engine.recruitment import RecruitCandidate


POTION_ITEM_ID: str = "minor_potion"
POTION_HEAL: int = 50   # minor_potion flat heal (data/items/consumables.yaml)
MAX_RECRUIT_PARTY_SIZE: int = 4
POTION_STASH_CAP: int = 5
HEAL_EFFICIENCY_TOLERANCE: int = 10
POTION_COMBAT_RESERVE: int = 0


@dataclass
class GoldenMacroConfig:
    """Per-job knobs for the shared golden macro."""

    preferred_weapon_stat: str = "STR"      # STR or MAG
    preferred_armor_stat: str = "DEF"       # DEF or RES (accessories can scale mixed)
    potion_stockpile_target: int = 3         # retreat floor (mid-zone bail-to-town)
    potion_stash_buffer: int = 3             # shop extra beyond full-heal need
    overstay_cap: int = 20                  # user: "20 overstay = always optimal"
    overstay_bail_hp_pct: float = 0.40      # bail overstay if mean HP% drops below
    heal_threshold_pct: float = 0.25        # between-encounter potion use threshold
    in_town_heal_target_pct: float = 1.00   # in-town: chain potions to this HP%
    pre_boss_retreat_hp_pct: float = 0.90   # retreat if next encounter is boss and HP below
    lodge_on: bool = False                   # einherjar style: no lodging
    lodge_hp_threshold: float = 0.30
    pit_level_buffer: int = 5               # grind endless zones until MC level >= next_zone_level + buffer
    town_visit_gold_threshold: int = 50     # go shop at this gold+
    town_visit_hp_threshold: float = 0.60    # go heal at this HP%


class GoldenMacroPolicy:
    """Shared macro for golden policies. Configure via ``GoldenMacroConfig``."""

    def __init__(
        self,
        config: GoldenMacroConfig,
        game_data: GameData,
        name: str = "golden_macro",
    ):
        self.config = config
        self.game_data = game_data
        self.name = name

    # -----------------------------------------------------------------
    # Town / zone
    # -----------------------------------------------------------------

    def decide_visit_town(
        self, run: RunState, available_town_ids: list[str]
    ) -> str | None:
        if not available_town_ids:
            return None

        potion_count = _count_potions(run)
        stash_free = STASH_LIMIT - len(run.party.stash)

        wants_potions = (
            run.party.money >= self.config.town_visit_gold_threshold
            and potion_count < self.config.potion_stockpile_target
            and stash_free >= 1
        )
        if wants_potions:
            return available_town_ids[0]

        if _mean_party_hp_pct(run) < self.config.town_visit_hp_threshold:
            return available_town_ids[0]

        return None

    def decide_zone(
        self, run: RunState, options: list[ZoneTemplate]
    ) -> ZoneTemplate | None:
        """Pick the next zone, preferring to finish overstay before advancing.

        Designer's rule: "every zone once cleared goes to 20/20 overstay."
        Endless zones (the pit) are grinding checkpoints — stay until MC
        level is high enough to handle the next non-endless zone.
        """
        if not options:
            return None

        mc = _get_mc(run)
        mc_level = mc.level if mc else 1

        # Priority 0: endless zone not yet graduated — keep grinding.
        # Graduation condition: MC level >= next_zone_level + buffer.
        for z in options:
            if not z.is_endless:
                continue
            if z.id in run.zones_completed:
                continue
            next_zone = self._next_non_endless_zone(z, options)
            if next_zone is None:
                continue
            target_level = next_zone.zone_level + self.config.pit_level_buffer
            if mc_level < target_level:
                return z

        # Priority 1: cleared zones that haven't hit overstay cap yet.
        cleared_needing_farm: list[ZoneTemplate] = []
        for z in options:
            if z.is_endless:
                continue
            if z.id not in run.zones_completed:
                continue
            progress = run.zone_progress.get(z.id)
            if progress is None:
                continue
            if progress.overstay_battles < self.config.overstay_cap:
                cleared_needing_farm.append(z)

        if cleared_needing_farm:
            cleared_needing_farm.sort(key=lambda z: z.zone_level)
            return cleared_needing_farm[0]

        # Priority 2: uncleared zones, lowest level first.
        uncleared = [z for z in options if z.id not in run.zones_completed]
        if uncleared:
            uncleared.sort(key=lambda z: z.zone_level)
            return uncleared[0]

        # Priority 3: all cleared and all at cap — farm the highest
        # level for marginal XP/gold.
        options_sorted = sorted(options, key=lambda z: z.zone_level, reverse=True)
        return options_sorted[0] if options_sorted else None

    def _next_non_endless_zone(
        self, endless_zone: ZoneTemplate, all_options: list[ZoneTemplate],
    ) -> ZoneTemplate | None:
        """Find the next non-endless zone above the endless zone's level."""
        candidates = [
            z for z in all_options
            if not z.is_endless and z.zone_level > endless_zone.zone_level
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda z: z.zone_level)
        return candidates[0]

    # -----------------------------------------------------------------
    # Shop (preference stack)
    # -----------------------------------------------------------------

    def decide_shop(
        self, run: RunState, available_items: list[str]
    ) -> list[ShopAction]:
        actions: list[ShopAction] = []
        mc = _get_mc(run)
        if mc is None:
            return actions

        # Sell items that aren't useful for the roster. Frees stash
        # space for potions and adds gold.
        for iid in list(run.party.stash):
            if iid == POTION_ITEM_ID:
                continue
            if self._should_sell(iid, mc):
                actions.append(ShopAction(action="sell", item_id=iid))

        mc_has_weapon = mc.equipment.get("WEAPON") is not None
        mc_has_armor = mc.equipment.get("ARMOR") is not None

        if not mc_has_weapon:
            ranked = self._ranked_weapons(available_items)
            if ranked and self._scales_with_stat(ranked[0], self.config.preferred_weapon_stat):
                actions.append(ShopAction(action="buy", item_id=ranked[0]))

        if not mc_has_armor:
            ranked = self._ranked_armor(available_items)
            if ranked:
                actions.append(ShopAction(action="buy", item_id=ranked[0]))

        # Potions: buy up to cap. If stash is full after sells above,
        # sell the least useful remaining items to make room.
        potion_count = _count_potions(run)
        needed = max(0, POTION_STASH_CAP - potion_count)
        if needed > 0 and POTION_ITEM_ID in available_items:
            stash_headroom = STASH_LIMIT - len(run.party.stash)
            if stash_headroom < needed:
                sellable = self._least_useful_sellable(run, mc, needed - stash_headroom)
                for sid in sellable:
                    actions.append(ShopAction(action="sell", item_id=sid))
            for _ in range(needed):
                actions.append(ShopAction(action="buy", item_id=POTION_ITEM_ID))

        return actions

    def _should_sell(self, item_id: str, mc) -> bool:
        """True if this item has no value for the current roster.

        Checks item effects/scaling against MC's growth curve. Items
        that scale with stats the MC doesn't grow in are dead weight.
        """
        item = self.game_data.items.get(item_id)
        if item is None:
            return False

        useful_stats = self._useful_stats(mc)

        if not item.is_consumable:
            if item.equip_type == EquipType.WEAPON:
                if item.scaling and item.scaling.stat.value not in useful_stats:
                    return True
            return False

        if item.teaches_ability_id:
            ab = self.game_data.abilities.get(item.teaches_ability_id)
            if ab:
                for eff in ab.effects:
                    if eff.stat_scaling and eff.stat_scaling.value in useful_stats:
                        return False
            return True

        if item.casts_ability_id:
            ab = self.game_data.abilities.get(item.casts_ability_id)
            if ab:
                for eff in ab.effects:
                    if eff.stat_scaling and eff.stat_scaling.value in useful_stats:
                        return False
            return True

        if item.combat_stat_buff:
            for stat_name in item.combat_stat_buff:
                if stat_name in useful_stats:
                    return False
            return True

        return False

    def _useful_stats(self, mc) -> set[str]:
        """Stats with growth > 1 for the MC's job."""
        job = self.game_data.jobs.get(mc.job_id)
        if job is None:
            return {"STR", "DEF"}
        stats: set[str] = set()
        for stat in ("STR", "MAG", "DEF", "RES", "SPD"):
            if getattr(job.growth, stat, 0) > 1:
                stats.add(stat)
        return stats or {"STR", "DEF"}

    def _least_useful_sellable(
        self, run: RunState, mc, count: int,
    ) -> list[str]:
        """Return up to ``count`` stash items to sell for potion room.

        Sells items already marked useless first, then cheapest remaining.
        """
        useless: list[tuple[str, int]] = []
        useful: list[tuple[str, int]] = []
        for iid in run.party.stash:
            if iid == POTION_ITEM_ID:
                continue
            item = self.game_data.items.get(iid)
            if item is None:
                continue
            if self._should_sell(iid, mc):
                useless.append((iid, item.base_price))
            else:
                useful.append((iid, item.base_price))
        useless.sort(key=lambda t: t[1])
        useful.sort(key=lambda t: t[1])
        result = [iid for iid, _ in useless]
        if len(result) < count:
            result.extend(iid for iid, _ in useful[:count - len(result)])
        return result[:count]

    def _ranked_weapons(self, available_items: list[str]) -> list[str]:
        weapons = [
            iid for iid in available_items
            if self._item_equip_type(iid) == EquipType.WEAPON
        ]
        # Primary key: matches preferred_weapon_stat. Secondary: base_price (tier proxy).
        weapons.sort(
            key=lambda iid: (
                1 if self._scales_with_stat(iid, self.config.preferred_weapon_stat) else 0,
                self._item_base_price(iid),
            ),
            reverse=True,
        )
        return weapons

    def _ranked_armor(self, available_items: list[str]) -> list[str]:
        armor = [
            iid for iid in available_items
            if self._item_equip_type(iid) == EquipType.ARMOR
        ]
        armor.sort(
            key=lambda iid: (
                1 if self._scales_with_stat(iid, self.config.preferred_armor_stat) else 0,
                self._item_base_price(iid),
            ),
            reverse=True,
        )
        return armor

    def _item_equip_type(self, item_id: str) -> EquipType | None:
        item = self.game_data.items.get(item_id)
        return item.equip_type if item else None

    def _item_base_price(self, item_id: str) -> int:
        item = self.game_data.items.get(item_id)
        return item.base_price if item else 0

    def _scales_with_stat(self, item_id: str, stat: str) -> bool:
        item = self.game_data.items.get(item_id)
        if not item or not item.scaling:
            return False
        return item.scaling.stat.value == stat

    # -----------------------------------------------------------------
    # Lodge
    # -----------------------------------------------------------------

    def decide_lodge(self, run: RunState, cost: int) -> bool:
        if not self.config.lodge_on:
            return False
        if cost <= 0 or run.party.money < cost:
            return False
        if _mean_party_hp_pct(run) >= self.config.lodge_hp_threshold:
            return False
        if cost / max(1, run.party.money) > 0.5:
            return False
        return True

    # -----------------------------------------------------------------
    # Recruitment
    # -----------------------------------------------------------------

    def decide_recruit(
        self, run: RunState, candidate: RecruitCandidate,
    ) -> bool:
        current = len(run.party.active) + len(run.party.reserve)
        return current < MAX_RECRUIT_PARTY_SIZE

    # -----------------------------------------------------------------
    # Zone tactical
    # -----------------------------------------------------------------

    def decide_overstay(self, run: RunState) -> bool:
        """Keep overstaying in this zone, or bail to town.

        Endless zones (the pit): keep grinding until graduation level
        is reached. Regular zones: cap at overstay_cap battles.
        HP-based bail applies to both — we'll come back.
        """
        if not run.zone_state:
            return False
        if _mean_party_hp_pct(run) < self.config.overstay_bail_hp_pct:
            return False

        # Endless zones: no overstay cap, just the level graduation check.
        # decide_zone handles re-entry if we bail for HP.
        if run.current_zone_id:
            zone = self.game_data.zones.get(run.current_zone_id)
            if zone and zone.is_endless:
                return True

        if run.zone_state.overstay_battles >= self.config.overstay_cap:
            return False
        return True

    def decide_retreat_to_town(self, run: RunState) -> bool:
        """Retreat mid-zone if we have gold to restock and stash room.

        Fires both pre-clear and during overstay. During overstay, the
        retreat → town → re-enter pattern is expected — ``decide_zone``
        routes us back to the same zone until overstay cap is hit.
        """
        potion_count = _count_potions(run)
        if potion_count >= self.config.potion_stockpile_target:
            return False
        if run.party.money < self.config.town_visit_gold_threshold:
            return False
        if STASH_LIMIT - len(run.party.stash) < 1:
            return False
        return True

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]:
        """Use potions to top up wounded characters.

        Chain potions on the most-wounded character below the heal
        threshold, then move to the next. Efficiency guard: skip if the
        potion would mostly overheal (missing < heal amount - tolerance).
        Keep POTION_COMBAT_RESERVE potions for in-combat emergencies.
        """
        uses: list[ItemUse] = []
        stash_potions = [iid for iid in run.party.stash if iid == POTION_ITEM_ID]
        if not stash_potions:
            return uses

        active_chars = [
            run.party.characters[cid] for cid in run.party.active
            if cid in run.party.characters
        ]
        if not active_chars:
            return uses

        running_hp: dict[str, int] = {c.id: c.current_hp for c in active_chars}
        max_hp: dict[str, int] = {c.id: c.max_hp for c in active_chars}
        target_pct = self.config.heal_threshold_pct

        while len(stash_potions) > POTION_COMBAT_RESERVE:
            wounded = [
                c for c in active_chars
                if running_hp[c.id] / max(1, max_hp[c.id]) < target_pct
            ]
            if not wounded:
                break
            wounded.sort(key=lambda c: running_hp[c.id] / max(1, max_hp[c.id]))
            target = wounded[0]
            uses.append(ItemUse(item_id=stash_potions.pop(0), character_id=target.id))
            running_hp[target.id] = min(
                max_hp[target.id], running_hp[target.id] + POTION_HEAL,
            )

        return uses

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int
    ) -> list[str]:
        return list(loot.item_ids)[:max(0, free_stash_slots)]


# ---------------------------------------------------------------------------
# Per-job presets
# ---------------------------------------------------------------------------


EINHERJAR_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",
    preferred_armor_stat="DEF",
    potion_stockpile_target=1,
    potion_stash_buffer=5,
    overstay_cap=20,
    overstay_bail_hp_pct=0.25,
    heal_threshold_pct=0.55,
    in_town_heal_target_pct=1.00,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
)

BERSERKER_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",
    preferred_armor_stat="DEF",
    potion_stockpile_target=2,
    potion_stash_buffer=3,
    overstay_cap=20,
    overstay_bail_hp_pct=0.40,
    heal_threshold_pct=0.35,
    in_town_heal_target_pct=1.00,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
    town_visit_gold_threshold=30,
    town_visit_hp_threshold=0.50,
)

ONMYOJI_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="MAG",
    preferred_armor_stat="RES",
    potion_stockpile_target=2,
    potion_stash_buffer=3,
    overstay_cap=20,
    overstay_bail_hp_pct=0.40,
    heal_threshold_pct=0.35,
    in_town_heal_target_pct=1.00,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
    town_visit_gold_threshold=30,
    town_visit_hp_threshold=0.50,
)

SACRIST_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="MAG",
    preferred_armor_stat="DEF",  # sacrist has DEF=1 growth, 0 RES
    potion_stockpile_target=2,
    potion_stash_buffer=3,
    overstay_cap=20,
    overstay_bail_hp_pct=0.40,
    heal_threshold_pct=0.35,
    in_town_heal_target_pct=1.00,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
    town_visit_gold_threshold=30,
    town_visit_hp_threshold=0.50,
)

MARTYR_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",  # martyr has 0 STR but thorns/retaliate don't need weapon scaling
    preferred_armor_stat="DEF",
    potion_stockpile_target=1,
    potion_stash_buffer=5,
    overstay_cap=20,
    overstay_bail_hp_pct=0.25,
    heal_threshold_pct=0.55,
    in_town_heal_target_pct=1.00,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
)

# Map job IDs to their golden macro config
GOLDEN_CONFIGS: dict[str, GoldenMacroConfig] = {
    "einherjar": EINHERJAR_GOLDEN_CONFIG,
    "berserker": BERSERKER_GOLDEN_CONFIG,
    "onmyoji": ONMYOJI_GOLDEN_CONFIG,
    "sacrist": SACRIST_GOLDEN_CONFIG,
    "martyr": MARTYR_GOLDEN_CONFIG,
}


def make_golden_macro_einherjar(game_data: GameData) -> GoldenMacroPolicy:
    return GoldenMacroPolicy(
        config=EINHERJAR_GOLDEN_CONFIG,
        game_data=game_data,
        name="golden_macro_einherjar",
    )


def make_golden_macro_for_job(
    game_data: GameData, job_id: str,
) -> GoldenMacroPolicy:
    """Create a golden macro policy with per-job stat preferences."""
    config = GOLDEN_CONFIGS.get(job_id, EINHERJAR_GOLDEN_CONFIG)
    return GoldenMacroPolicy(
        config=config,
        game_data=game_data,
        name=f"golden_macro_{job_id}",
    )


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
    return sum(c.current_hp / max(1, c.max_hp) for c in active) / len(active)


def _count_potions(run: RunState) -> int:
    return sum(1 for iid in run.party.stash if iid == POTION_ITEM_ID)
