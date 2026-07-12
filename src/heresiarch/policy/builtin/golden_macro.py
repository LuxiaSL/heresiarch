"""Golden macro policy v2: the designer's doctrine as computable rules.

v1 was parametric thresholds tuned per job (and then by CEM, which
tied with the presets four times — the knobs were exhausted). v2
replaces most thresholds with the designer's dictated macro doctrine
(2026-07-10, memory `project_macro_doctrine.md`):

  - Zero-waste healing: drink the moment missing_hp >= potion heal
    ("no waste"), or sooner when death is expected next encounter.
  - Expected-death retreat: go back to town when the projected next
    fight would kill someone and potions can't cover it — not a flat
    HP%. Projection = worst damage taken over the last few fights in
    this zone.
  - Potions ARE the early town heal (buy-1-drink-1 beats the lodge);
    always carry a spare "in case I slip up mid fight".
  - Equipment before the next zone: after zone 1, at LEAST a weapon,
    then class-suited armor — and UPGRADE when the shop has strictly
    better gear, selling dead-weight consumables to afford it.
  - Overstay to the 100% debuff cap (derived from the loot formula,
    not a knob) while fights are ~free; "bail the moment chip resumes".

What remains per-job config: stat preferences (which weapon/armor),
and risk appetite (potion carry target, pre-boss heal target). The
designer: "the macro tends to apply widely … the micro play is what
really changes per job."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from heresiarch.engine.formulas import calculate_buy_price, calculate_sell_price
from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE
from heresiarch.engine.models.items import EquipType, Item
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
POTION_COMBAT_RESERVE: int = 0

# --- Doctrine constants (rules, not knobs — CEM must not touch these) ---
# Overstay rewards decay 5%/battle; at 100% decay farming is "meaningless
# and you must move on". Derived, so a loot-formula change retunes the macro.
OVERSTAY_DEBUFF_CAP: int = max(1, round(1.0 / OVERSTAY_PENALTY_PER_BATTLE))
# "Strictly better if you have patience" holds while fights are ~free.
# Below this mean HP%, chip has resumed and the farm is paying real HP.
OVERSTAY_FREE_HP_PCT: float = 0.90
# Endless zones (the pit) are leveling checkpoints — chip is expected
# there, so only a genuine safety floor bails the grind.
ENDLESS_BAIL_HP_PCT: float = 0.40
# In town the designer heals to full (the last potion's partial waste is
# accepted; zone-1 boss "is harder in terms of potion management").
IN_TOWN_HEAL_TARGET_PCT: float = 1.00
# Expected next-fight damage = worst of the last N fights in this zone.
EXPECTED_DAMAGE_WINDOW: int = 3


def _efficient_heal_gate(max_hp: int) -> int:
    """Town-trip heal gate, small-frame adjusted.

    A frame with max_hp < 2×potion can never reach missing == heal,
    so the TOWN-visit heal leg uses half the bar for them. (Between
    fights this is handled by the per-job between_fight_heal_target
    instead — a flat half-bar gate there crashed berserker, whose
    survive-cycle wants its potions saved for the projected-death
    moment.)
    """
    return min(POTION_HEAL, max(1, max_hp // 2))


def useful_growth_stats(job_id: str, game_data: GameData) -> set[str]:
    """Stats a job actually grows (growth > 1).

    Module-level because the run driver's auto-equip shares it: policy
    shopping and driver equipping must agree on what gear a character
    can scale, or the shop buys upgrades the driver refuses to wear.
    """
    job = game_data.jobs.get(job_id)
    if job is None:
        return {"STR", "DEF"}
    stats: set[str] = set()
    for stat in ("STR", "MAG", "DEF", "RES", "SPD"):
        if getattr(job.growth, stat, 0) > 1:
            stats.add(stat)
    return stats or {"STR", "DEF"}


@dataclass
class GoldenMacroConfig:
    """Per-job knobs: stat preferences + risk appetite. The doctrine
    (heal timing, retreat rule, overstay cap, shop priorities) is code."""

    preferred_weapon_stat: str = "STR"      # STR or MAG
    preferred_armor_stat: str = "DEF"       # DEF or RES (accessories can scale mixed)
    potion_stockpile_target: int = 3         # carried potions = expected need + spare
    potion_stash_cap: int = 5                # shop: buy potions up to this count
    pre_boss_retreat_hp_pct: float = 0.90   # heal/retreat target when next encounter is a boss
    # THE per-job risk threshold (doctrine: "what shifts per job is …
    # your risk threshold internally"). 0.0 = off: drink only at
    # zero-waste or projected death — measured best for survive-cycle
    # frames (berserker v2.0 median 26 enc; the v2.1 half-bar gate
    # crashed it to 4 by sipping the pack budget on ordinary chip).
    # Glass casters want ~0.75: enter every fight topped, waste be
    # damned (old-threshold onmyoji outran every v2 variant).
    between_fight_heal_target: float = 0.0
    lodge_on: bool = False                   # potions are the efficient early heal
    lodge_hp_threshold: float = 0.30
    pit_level_buffer: int = 5               # grind endless zones until MC level >= next_zone_level + buffer


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

        # Potion needs (restock or efficient heal) — the SAME predicate
        # the retreat rule uses, so a retreat-to-town always results in
        # an actual town visit (mismatched conditions deadlocked v2.0
        # into the stuck detector at the zone door).
        if self._town_trip_worthwhile(run):
            return available_town_ids[0]

        # Equipment before the next zone: once shop tiers unlock (a zone
        # is cleared), an affordable strictly-better weapon/armor is the
        # top gold priority.
        if run.zones_completed and self._affordable_upgrade_exists(run):
            return available_town_ids[0]

        return None

    def _town_trip_worthwhile(self, run: RunState) -> bool:
        """Would going to town right now buy us something we need?

        Doctrine: "go back, buy potion, heal" — one affordable potion
        that we'd actually use justifies the trip. Buying the full
        stockpile in one visit is NOT required (early gold rarely
        covers it); partial restocks make progress.
        """
        price = self._potion_price(run)
        if run.party.money < price:
            return False

        potion_count = self._count_potions(run)
        stash_free = STASH_LIMIT - len(run.party.stash)
        if potion_count < self.config.potion_stockpile_target and stash_free >= 1:
            return True

        # Efficient heal: someone is an efficient-heal's worth down —
        # potions are the zero-waste town heal (buy-1-drink-1). Gate is
        # small-frame adjusted (half bar for frames under two potions).
        return any(
            c.max_hp - c.current_hp >= _efficient_heal_gate(c.max_hp)
            for c in _active_chars(run)
        )

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
            if progress.overstay_battles < OVERSTAY_DEBUFF_CAP:
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
        """Doctrine order: sell dead weight → weapon (buy OR upgrade) →
        armor (buy or upgrade) → potions to cap.

        "At LEAST a weapon, so you start doing serious damage, and then
        the armor most suited for the class" — and upgrades count: v1
        only filled EMPTY slots, which the designer's own play (sold a
        tonic to afford warding_mail) proved wrong. If gold falls short
        of a weapon upgrade, sell least-useful stash items to cover it.
        """
        actions: list[ShopAction] = []
        mc = _get_mc(run)
        if mc is None:
            return actions

        # Sell items that aren't useful for the roster (including gear
        # strictly worse than what the MC already wears — displaced
        # upgrades land in the stash). Frees space and funds upgrades.
        sold: set[str] = set()
        projected_gold = run.party.money
        for iid in list(run.party.stash):
            if self._is_heal_potion(iid):
                continue
            if self._should_sell(iid, mc, run):
                actions.append(ShopAction(action="sell", item_id=iid))
                sold.add(iid)
                projected_gold += self._item_sell_price(iid)

        # Weapon first: best available upgrade over what's equipped.
        upgrade = self._best_upgrade(
            run, mc, available_items, EquipType.WEAPON, "WEAPON",
        )
        if upgrade is not None:
            price = calculate_buy_price(
                self._item_base_price(upgrade), run.party.cha,
            )
            if projected_gold < price:
                for sid in self._least_useful_sellable(
                    run, mc, count=len(run.party.stash), exclude=sold,
                ):
                    if projected_gold >= price:
                        break
                    actions.append(ShopAction(action="sell", item_id=sid))
                    sold.add(sid)
                    projected_gold += self._item_sell_price(sid)
            if projected_gold >= price:
                actions.append(ShopAction(action="buy", item_id=upgrade))
                projected_gold -= price

        # Then class-suited armor.
        upgrade = self._best_upgrade(
            run, mc, available_items, EquipType.ARMOR, "ARMOR",
        )
        if upgrade is not None:
            price = calculate_buy_price(
                self._item_base_price(upgrade), run.party.cha,
            )
            if projected_gold >= price:
                actions.append(ShopAction(action="buy", item_id=upgrade))
                projected_gold -= price

        # Potions: buy up to cap — climbing the LADDER, not just minors.
        # Per unit: the biggest flat-heal potion the MC's frame can
        # drink at zero waste (heal <= max_hp) that's also affordable
        # right now. A 400-HP pit frame buys 150s (same HP/gold, a
        # third of the slots and drinks); a Lv1 frame sticks to minors.
        # Degrading by affordability keeps the shop in agreement with
        # the trip predicate ("one affordable potion justifies the
        # trip" — v2.0's deadlock lesson).
        potion_count = self._count_potions(run)
        needed = max(0, self.config.potion_stash_cap - potion_count)
        ladder = self._potion_ladder(available_items)
        if needed > 0 and ladder:
            stash_headroom = (
                STASH_LIMIT - len(run.party.stash) + len(sold)
            )
            if stash_headroom < needed:
                for sid in self._least_useful_sellable(
                    run, mc, count=needed - stash_headroom, exclude=sold,
                ):
                    actions.append(ShopAction(action="sell", item_id=sid))
                    sold.add(sid)
            for _ in range(needed):
                pick: tuple[str, int] | None = None
                for item in ladder:  # biggest heal first
                    price = calculate_buy_price(item.base_price, run.party.cha)
                    if item.heal_amount <= mc.max_hp and price <= projected_gold:
                        pick = (item.id, price)
                        break
                if pick is None:
                    # Nothing zero-waste-sized is affordable: take the
                    # cheapest rung we CAN pay for rather than nothing.
                    for item in reversed(ladder):
                        price = calculate_buy_price(item.base_price, run.party.cha)
                        if price <= projected_gold:
                            pick = (item.id, price)
                            break
                if pick is None:
                    break
                actions.append(ShopAction(action="buy", item_id=pick[0]))
                projected_gold -= pick[1]

        # Recruits last: gear the whole party once the lifeline is
        # secured. Join-time gear is otherwise frozen for the entire run
        # (the pit autopsy: Lv20+ recruits swinging zone-3 tier gear,
        # some slots empty since recruitment). Doctrine: "keeping
        # recruits up" — leftover gold only; MC and potions come first.
        for char in _active_chars(run):
            if char.is_mc:
                continue
            for equip_type, slot in (
                (EquipType.WEAPON, "WEAPON"),
                (EquipType.ARMOR, "ARMOR"),
            ):
                upgrade = self._best_upgrade(
                    run, char, available_items, equip_type, slot,
                )
                if upgrade is None:
                    continue
                price = calculate_buy_price(
                    self._item_base_price(upgrade), run.party.cha,
                )
                if projected_gold < price:
                    continue
                actions.append(ShopAction(action="buy", item_id=upgrade))
                projected_gold -= price

        return actions

    def _equipped_item(self, run: RunState, mc, slot: str) -> Item | None:
        iid = mc.equipment.get(slot)
        if not iid:
            return None
        return self.game_data.items.get(iid) or run.party.items.get(iid)

    def _gear_rank(self, item: Item | None) -> tuple[int, int]:
        """Comparable power proxy for equipment: (tier, base_price)."""
        if item is None:
            return (0, 0)
        return (item.tier, item.base_price)

    def _best_upgrade(
        self,
        run: RunState,
        char,
        available_items: list[str],
        equip_type: EquipType,
        slot: str,
    ) -> str | None:
        """Best shop item strictly better than the equipped one, honoring
        the character's stat preference for weapons (a MAG frame never
        buys a STR sword). Works for MC and recruits alike.

        UPGRADES additionally require the weapon's scaling stat to be one
        the job actually grows: martyr (0 STR growth) fills its empty slot
        with a cheap starter for the flat damage, but must never sink
        thousands into higher-tier STR weapons it can't scale — the first
        v2 eval showed exactly that (final gold 1370→1011, deaths 8→15).
        """
        current_rank = self._gear_rank(self._equipped_item(run, char, slot))
        upgrading = current_rank > (0, 0)
        useful = self._useful_stats(char) if upgrading else None
        preferred_stat = self._preferred_weapon_stat(char)
        ranked = (
            self._ranked_weapons(available_items, preferred_stat)
            if equip_type == EquipType.WEAPON
            else self._ranked_armor(available_items)
        )
        for iid in ranked:
            item = self.game_data.items.get(iid)
            if item is None:
                continue
            if equip_type == EquipType.WEAPON and item.scaling and not (
                self._scales_with_stat(iid, preferred_stat)
            ):
                continue
            if (
                upgrading
                and equip_type == EquipType.WEAPON
                and item.scaling
                and useful is not None
                and item.scaling.stat.value not in useful
            ):
                continue
            if self._gear_rank(item) > current_rank:
                return iid
        return None

    def _affordable_upgrade_exists(self, run: RunState) -> bool:
        """Registry-wide approximation of "the shop has something better
        we could afford" (the policy can't resolve the town shop from
        outside town; decide_shop no-ops if the stock disagrees)."""
        mc = _get_mc(run)
        if mc is None:
            return False
        budget = run.party.money + sum(
            self._item_sell_price(iid)
            for iid in run.party.stash
            if not self._is_heal_potion(iid) and self._should_sell(iid, mc, run)
        )
        members = _active_chars(run) or [mc]
        for member in members:
            useful = self._useful_stats(member)
            for equip_type, slot, stat in (
                (EquipType.WEAPON, "WEAPON", self._preferred_weapon_stat(member)),
                (EquipType.ARMOR, "ARMOR", None),
            ):
                current_rank = self._gear_rank(
                    self._equipped_item(run, member, slot),
                )
                upgrading = current_rank > (0, 0)
                for item in self.game_data.items.values():
                    if item.equip_type != equip_type:
                        continue
                    if stat and item.scaling and item.scaling.stat.value != stat:
                        continue
                    if (
                        upgrading
                        and equip_type == EquipType.WEAPON
                        and item.scaling
                        and item.scaling.stat.value not in useful
                    ):
                        continue
                    if self._gear_rank(item) <= current_rank:
                        continue
                    if calculate_buy_price(item.base_price, run.party.cha) <= budget:
                        return True
        return False

    def _item_sell_price(self, item_id: str) -> int:
        item = self.game_data.items.get(item_id)
        return calculate_sell_price(item.base_price) if item else 0

    def _should_sell(self, item_id: str, mc, run: RunState | None = None) -> bool:
        """True if this item has no value for the current roster.

        Roster-aware: an item is dead weight only when NO active member
        can use it — a MAG staff is kept while an onmyoji recruit is on
        the roster even if the MC swings STR. Gear strictly worse than
        what EVERY member already wears (an empty slot counts as
        upgradeable) is sellable — displaced upgrades land in the stash
        and the designer sells them.
        """
        item = self.game_data.items.get(item_id)
        if item is None:
            return False

        members = _active_chars(run) if run is not None else []
        if not members:
            members = [mc]
        useful_stats: set[str] = set()
        for member in members:
            useful_stats |= self._useful_stats(member)

        if not item.is_consumable:
            if item.equip_type == EquipType.WEAPON:
                if item.scaling and item.scaling.stat.value not in useful_stats:
                    return True
            if run is not None and item.equip_type in (
                EquipType.WEAPON, EquipType.ARMOR,
            ):
                slot = item.equip_type.value
                for member in members:
                    equipped = self._equipped_item(run, member, slot)
                    if equipped is None or (
                        self._gear_rank(item) >= self._gear_rank(equipped)
                    ):
                        return False  # someone could still wear it
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

    def _useful_stats(self, char) -> set[str]:
        """Stats with growth > 1 for this character's job."""
        return useful_growth_stats(char.job_id, self.game_data)

    def _preferred_weapon_stat(self, char) -> str:
        """Weapon-stat preference per character.

        The MC uses the config preference (the designer's pick); recruits
        derive theirs from job growth — a mage recruit shops MAG staves
        regardless of what the MC swings.
        """
        if char.is_mc:
            return self.config.preferred_weapon_stat
        job = self.game_data.jobs.get(char.job_id)
        if job is None:
            return "STR"
        if getattr(job.growth, "MAG", 0) > getattr(job.growth, "STR", 0):
            return "MAG"
        return "STR"

    def _least_useful_sellable(
        self, run: RunState, mc, count: int, exclude: set[str] | None = None,
    ) -> list[str]:
        """Return up to ``count`` stash items to sell (for potion room or
        to fund an upgrade). Useless items first, then cheapest useful
        consumables — the designer sells tonics for armor, but never
        equipped-quality gear."""
        exclude = exclude or set()
        useless: list[tuple[str, int]] = []
        useful: list[tuple[str, int]] = []
        for iid in run.party.stash:
            if self._is_heal_potion(iid) or iid in exclude:
                continue
            item = self.game_data.items.get(iid)
            if item is None:
                continue
            if self._should_sell(iid, mc, run):
                useless.append((iid, item.base_price))
            elif item.is_consumable:
                useful.append((iid, item.base_price))
        useless.sort(key=lambda t: t[1])
        useful.sort(key=lambda t: t[1])
        result = [iid for iid, _ in useless]
        if len(result) < count:
            result.extend(iid for iid, _ in useful[:count - len(result)])
        return result[:count]

    def _ranked_weapons(
        self, available_items: list[str], preferred_stat: str,
    ) -> list[str]:
        weapons = [
            iid for iid in available_items
            if self._item_equip_type(iid) == EquipType.WEAPON
        ]
        # Primary key: matches the character's preferred weapon stat.
        # Secondary: base_price (tier proxy).
        weapons.sort(
            key=lambda iid: (
                1 if self._scales_with_stat(iid, preferred_stat) else 0,
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
        """Overstay is "strictly better if you have patience" — until the
        100% reward-decay cap, or until fights stop being free.

        Endless zones (the pit): leveling checkpoints, chip expected —
        only a real safety floor bails. Regular zones: farm to the
        derived debuff cap while mean HP stays ~flat ("bail the moment
        chip resumed"); the zero-waste heal rule keeps us topped when
        sustain covers the chip.
        """
        if not run.zone_state:
            return False

        # Endless zones: no overstay cap, just the level graduation check.
        # decide_zone handles re-entry if we bail for HP.
        if run.current_zone_id:
            zone = self.game_data.zones.get(run.current_zone_id)
            if zone and zone.is_endless:
                return _mean_party_hp_pct(run) >= ENDLESS_BAIL_HP_PCT

        if run.zone_state.overstay_battles >= OVERSTAY_DEBUFF_CAP:
            return False
        if _mean_party_hp_pct(run) < OVERSTAY_FREE_HP_PCT:
            return False
        return True

    def decide_retreat_to_town(self, run: RunState) -> bool:
        """The designer's retreat rule: "go back when I expect that I
        would die on the next encounter" — expected next-fight cost vs
        current HP, not a flat HP%.

        Called AFTER between-encounter potions (driver order), so what's
        left standing here is what enters the next fight.

        1. Pre-boss: never walk into a boss wounded (designer's own TUI
           pattern) — retreat below the pre-boss target if town can heal.
        2. Expected death: projected damage share would drop someone and
           there are no potions left to fix it → go back, buy, heal.
        3. Restock: carried potions below the target (+spare) and gold
           covers the refill — "buy an extra in case I slip up mid fight".
        """
        price = self._potion_price(run)
        potion_count = self._count_potions(run)
        can_heal_in_town = potion_count > 0 or run.party.money >= price

        # Pre-boss rule — and endless zones are perpetual pre-boss:
        # fight a few, cycle to town, heal to full, return. The pit's
        # sizable gold funds the rhythm.
        if self._next_encounter_is_boss(run) or self._in_endless_zone(run):
            if _mean_party_hp_pct(run) < self.config.pre_boss_retreat_hp_pct:
                if can_heal_in_town:
                    return True

        # Expected-death rule. Potions are exhausted (the heal step ran
        # first) — if the projected per-character share of the next
        # fight's damage still covers someone's remaining HP, retreat.
        if potion_count == 0 and run.party.money >= price:
            share = self._expected_damage_share(run)
            if share > 0 and any(
                c.current_hp <= share for c in _active_chars(run)
            ):
                return True

        # Restock trip — same predicate as decide_visit_town, so the
        # retreat always lands somewhere productive.
        return self._town_trip_worthwhile(run)

    def _potion_price(self, run: RunState) -> int:
        """Price of the BASELINE potion (the cheapest rung).

        Trip predicates gate on this so 'one affordable potion justifies
        the trip' stays true even when the shop stocks bigger rungs the
        party can't afford yet.
        """
        item = self.game_data.items.get(POTION_ITEM_ID)
        base = item.base_price if item else 25
        return calculate_buy_price(base, run.party.cha)

    # -----------------------------------------------------------------
    # Potion ladder (minor 50 → potion 150 → major 400; elixir is %-heal)
    # -----------------------------------------------------------------

    def _is_heal_potion(self, item_id: str) -> bool:
        item = self.game_data.items.get(item_id)
        return bool(
            item
            and item.is_consumable
            and (item.heal_amount > 0 or item.heal_percent > 0)
        )

    def _heal_value(self, item_id: str, max_hp: int) -> int:
        item = self.game_data.items.get(item_id)
        if item is None:
            return 0
        if item.heal_amount > 0:
            return item.heal_amount
        if item.heal_percent > 0:
            return int(max_hp * item.heal_percent)
        return 0

    def _count_potions(self, run: RunState) -> int:
        """Heal potions of ANY rung in the stash."""
        return _count_potions(run, self.game_data)

    def _potion_ladder(self, available_items: list[str]) -> list[Item]:
        """Flat-heal potions in the offer, biggest heal first.

        Percent-heal items (elixir) are excluded: zero waste is
        unreachable by construction (missing == full bar means dead),
        so they never belong in the routine restock.
        """
        seen: set[str] = set()
        rungs: list[Item] = []
        for iid in available_items:
            if iid in seen:
                continue
            seen.add(iid)
            item = self.game_data.items.get(iid)
            if item is None or not item.is_consumable:
                continue
            if item.heal_amount > 0:
                rungs.append(item)
        rungs.sort(key=lambda it: it.heal_amount, reverse=True)
        return rungs

    def _expected_next_fight_damage(self, run: RunState) -> int:
        """Projected party-wide damage for the UPCOMING fight.

        Worst per-enemy damage over the recent window in this zone,
        scaled by the next encounter's pack size (the zone template is
        open information — the designer walks into the zone-1 triple
        pack knowing it hits three times harder than the fodder before
        it, and the estimator must too).
        """
        encounters = run.battle_record.encounters
        if run.current_zone_id:
            zone_encs = [
                e for e in encounters if e.zone_id == run.current_zone_id
            ]
        else:
            zone_encs = []
        window = (zone_encs or list(encounters))[-EXPECTED_DAMAGE_WINDOW:]
        if not window:
            return 0
        per_enemy = max(
            e.total_damage_taken / max(1, len(e.enemy_template_ids))
            for e in window
        )
        next_count = self._next_encounter_enemy_count(run)
        return int(-(-(per_enemy * next_count) // 1))  # ceil

    def _next_encounter_enemy_count(self, run: RunState) -> int:
        """Enemy count of the upcoming encounter.

        Scripted zones read the template. Endless zones spawn
        dynamically (`encounters: []`) — v2.1 fell back to 1 there,
        so the pit projected one-enemy fights and 33/48 einherjar
        runs died inside it. Fallback is now the observed pack size
        from recent fights in this zone (floor 2 for endless).
        """
        if not run.current_zone_id or not run.zone_state:
            return 1
        zone = self.game_data.zones.get(run.current_zone_id)
        if zone is None:
            return 1
        idx = run.zone_state.current_encounter_index
        if not run.zone_state.is_cleared and idx < len(zone.encounters):
            return max(1, sum(zone.encounters[idx].enemy_counts))
        # Overstay / endless: typical scripted pack, else observed packs.
        counts = [sum(e.enemy_counts) for e in zone.encounters if not e.is_boss]
        if counts:
            return max(1, round(sum(counts) / len(counts)))
        observed = [
            len(e.enemy_template_ids)
            for e in run.battle_record.encounters
            if e.zone_id == run.current_zone_id
        ][-EXPECTED_DAMAGE_WINDOW:]
        floor = 2 if zone.is_endless else 1
        if not observed:
            return floor
        mean = sum(observed) / len(observed)
        return max(floor, int(-(-mean // 1)))  # ceil

    def _in_endless_zone(self, run: RunState) -> bool:
        if not run.current_zone_id:
            return False
        zone = self.game_data.zones.get(run.current_zone_id)
        return bool(zone and zone.is_endless)

    def _expected_damage_share(self, run: RunState) -> int:
        """Per-character share of the projected next-fight damage."""
        active = _active_chars(run)
        if not active:
            return 0
        expected = self._expected_next_fight_damage(run)
        return -(-expected // len(active))  # ceil division

    def _next_encounter_is_boss(self, run: RunState) -> bool:
        """True when the upcoming encounter in the current zone is a boss."""
        if not run.current_zone_id or not run.zone_state:
            return False
        zone = self.game_data.zones.get(run.current_zone_id)
        if zone is None:
            return False
        idx = run.zone_state.current_encounter_index
        if run.zone_state.is_cleared or idx >= len(zone.encounters):
            return False
        return zone.encounters[idx].is_boss

    def decide_between_encounter_items(self, run: RunState) -> list[ItemUse]:
        """The zero-waste heal rule, with two doctrine exceptions.

        Drink priority per potion:
        1. Survival: someone's remaining HP is inside the projected
           next-fight damage share — drink even at partial waste
           ("sooner, when I expect that I would die").
        2. Zero waste: missing_hp >= potion heal — "the second that the
           missing health is == the amount gained back, there's no waste".
        3. Pre-boss: below the pre-boss target with a boss up next —
           top up accepting waste (bosses are the potion-management test).
        Otherwise: save the potion. That's the whole rule; no threshold.
        """
        uses: list[ItemUse] = []
        held = [iid for iid in run.party.stash if self._is_heal_potion(iid)]
        if not held:
            return uses

        active_chars = _active_chars(run)
        if not active_chars:
            return uses

        running_hp: dict[str, int] = {c.id: c.current_hp for c in active_chars}
        max_hp: dict[str, int] = {c.id: c.max_hp for c in active_chars}
        share = self._expected_damage_share(run)
        # Endless zones are perpetual pre-boss (designer-confirmed):
        # spawn levels swing wildly (the pit: 18-28), so every fight is
        # entered near the pre-boss target — gold is moot by then.
        boss_next = self._next_encounter_is_boss(run) or self._in_endless_zone(run)
        boss_target = self.config.pre_boss_retreat_hp_pct

        def heal_of(iid: str, char_id: str) -> int:
            return self._heal_value(iid, max_hp[char_id])

        def drink(char_id: str, iid: str) -> None:
            held.remove(iid)
            uses.append(ItemUse(item_id=iid, character_id=char_id))
            running_hp[char_id] = min(
                max_hp[char_id], running_hp[char_id] + heal_of(iid, char_id),
            )

        def largest_zero_waste(char_id: str) -> str | None:
            """Biggest held potion fully absorbed by this char's missing HP."""
            missing = max_hp[char_id] - running_hp[char_id]
            fits = [iid for iid in held if 0 < heal_of(iid, char_id) <= missing]
            if not fits:
                return None
            return max(fits, key=lambda iid: heal_of(iid, char_id))

        while len(held) > POTION_COMBAT_RESERVE:
            hurt = [c for c in active_chars if running_hp[c.id] < max_hp[c.id]]
            if not hurt:
                break
            hurt.sort(key=lambda c: running_hp[c.id] / max(1, max_hp[c.id]))

            # Survival: largest heal held — mitigation over efficiency.
            dying = [c for c in hurt if running_hp[c.id] <= share]
            if dying:
                cid = dying[0].id
                drink(cid, max(held, key=lambda iid: heal_of(iid, cid)))
                continue

            # Zero waste, ladder-aware: drink the biggest potion the
            # frame's missing HP fully absorbs.
            zero_waste = [c for c in hurt if largest_zero_waste(c.id)]
            if zero_waste:
                cid = zero_waste[0].id
                pick = largest_zero_waste(cid)
                assert pick is not None
                drink(cid, pick)
                continue

            # Per-job risk threshold: pre-boss/endless target dominates;
            # otherwise the config's between-fight target (0.0 = off).
            # Waste is accepted here, so the SMALLEST held rung tops up.
            target = boss_target if boss_next else self.config.between_fight_heal_target
            if target > 0:
                below_target = [
                    c for c in hurt
                    if running_hp[c.id] / max(1, max_hp[c.id]) < target
                ]
                if below_target:
                    cid = below_target[0].id
                    drink(cid, min(held, key=lambda iid: heal_of(iid, cid)))
                    continue

            break

        return uses

    def decide_loot_pick(
        self, run: RunState, loot: LootResult, free_stash_slots: int
    ) -> list[str]:
        return list(loot.item_ids)[:max(0, free_stash_slots)]


# ---------------------------------------------------------------------------
# Per-job presets
# ---------------------------------------------------------------------------


# v2 presets: only stat preferences + risk appetite remain — the healing,
# retreat, overstay, and shop rules are doctrine (code), not knobs. The
# v1 glass-preset findings still hold where they map: glass frames carry
# more potions (stockpile 3 vs 1) because their expected-death margin is
# thinner. Sacrist note preserved: enter fights healthy and descend via
# sanguine_rite on purpose — communion is the combat layer's job.

EINHERJAR_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",
    preferred_armor_stat="DEF",
    potion_stockpile_target=1,
    potion_stash_cap=5,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
)

BERSERKER_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",
    preferred_armor_stat="DEF",
    potion_stockpile_target=3,
    potion_stash_cap=6,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
)

ONMYOJI_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="MAG",
    preferred_armor_stat="RES",
    potion_stockpile_target=3,
    potion_stash_cap=6,
    pre_boss_retreat_hp_pct=0.90,
    between_fight_heal_target=0.75,  # glass: enter everything topped
    lodge_on=False,
)

SACRIST_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="MAG",
    preferred_armor_stat="DEF",  # sacrist has DEF=1 growth, 0 RES
    potion_stockpile_target=3,
    potion_stash_cap=6,
    pre_boss_retreat_hp_pct=0.90,
    between_fight_heal_target=0.75,
    lodge_on=False,
)

MARTYR_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",  # martyr has 0 STR but thorns/retaliate don't need weapon scaling
    preferred_armor_stat="DEF",
    potion_stockpile_target=1,
    potion_stash_cap=5,
    pre_boss_retreat_hp_pct=0.90,
    between_fight_heal_target=0.55,  # its old 83%-survival regime
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


def _active_chars(run: RunState) -> list:
    return [
        run.party.characters[cid] for cid in run.party.active
        if cid in run.party.characters
    ]


def _count_potions(run: RunState, game_data: GameData | None = None) -> int:
    """Heal potions in the stash — ladder-aware when game_data is given,
    minor-only otherwise (legacy callers)."""
    if game_data is None:
        return sum(1 for iid in run.party.stash if iid == POTION_ITEM_ID)
    count = 0
    for iid in run.party.stash:
        item = game_data.items.get(iid)
        if item and item.is_consumable and (
            item.heal_amount > 0 or item.heal_percent > 0
        ):
            count += 1
    return count


def _mean_party_hp_pct(run: RunState) -> float:
    active = _active_chars(run)
    if not active:
        return 1.0
    return sum(c.current_hp / max(1, c.max_hp) for c in active) / len(active)

