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
    """The zero-waste point, small-frame adjusted.

    A frame with max_hp < 2×potion can never reach missing == heal —
    the v2.0 gate starved 40-HP onmyoji to death against fodder (25/48
    deaths to fodder_slime on the first eval). For frames smaller than
    two potions, "efficient enough" is half the bar — the designer's
    observed glass-frame behavior.
    """
    return min(POTION_HEAL, max(1, max_hp // 2))


@dataclass
class GoldenMacroConfig:
    """Per-job knobs: stat preferences + risk appetite. The doctrine
    (heal timing, retreat rule, overstay cap, shop priorities) is code."""

    preferred_weapon_stat: str = "STR"      # STR or MAG
    preferred_armor_stat: str = "DEF"       # DEF or RES (accessories can scale mixed)
    potion_stockpile_target: int = 3         # carried potions = expected need + spare
    potion_stash_cap: int = 5                # shop: buy potions up to this count
    pre_boss_retreat_hp_pct: float = 0.90   # heal/retreat target when next encounter is a boss
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

        potion_count = _count_potions(run)
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
            if iid == POTION_ITEM_ID:
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

        # Potions: buy up to cap. If stash is full after sells above,
        # sell the least useful remaining items to make room.
        potion_count = _count_potions(run)
        needed = max(0, self.config.potion_stash_cap - potion_count)
        if needed > 0 and POTION_ITEM_ID in available_items:
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
                actions.append(ShopAction(action="buy", item_id=POTION_ITEM_ID))

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
        mc,
        available_items: list[str],
        equip_type: EquipType,
        slot: str,
    ) -> str | None:
        """Best shop item strictly better than the equipped one, honoring
        stat preference for weapons (a MAG frame never buys a STR sword).

        UPGRADES additionally require the weapon's scaling stat to be one
        the job actually grows: martyr (0 STR growth) fills its empty slot
        with a cheap starter for the flat damage, but must never sink
        thousands into higher-tier STR weapons it can't scale — the first
        v2 eval showed exactly that (final gold 1370→1011, deaths 8→15).
        """
        current_rank = self._gear_rank(self._equipped_item(run, mc, slot))
        upgrading = current_rank > (0, 0)
        useful = self._useful_stats(mc) if upgrading else None
        ranked = (
            self._ranked_weapons(available_items)
            if equip_type == EquipType.WEAPON
            else self._ranked_armor(available_items)
        )
        for iid in ranked:
            item = self.game_data.items.get(iid)
            if item is None:
                continue
            if equip_type == EquipType.WEAPON and item.scaling and not (
                self._scales_with_stat(iid, self.config.preferred_weapon_stat)
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
            if iid != POTION_ITEM_ID and self._should_sell(iid, mc, run)
        )
        useful = self._useful_stats(mc)
        for equip_type, slot, stat in (
            (EquipType.WEAPON, "WEAPON", self.config.preferred_weapon_stat),
            (EquipType.ARMOR, "ARMOR", None),
        ):
            current_rank = self._gear_rank(self._equipped_item(run, mc, slot))
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

        Checks item effects/scaling against MC's growth curve. Items
        that scale with stats the MC doesn't grow in are dead weight,
        and so is gear strictly worse than what the MC already wears
        (displaced by an upgrade — sell it, the designer does).
        """
        item = self.game_data.items.get(item_id)
        if item is None:
            return False

        useful_stats = self._useful_stats(mc)

        if not item.is_consumable:
            if item.equip_type == EquipType.WEAPON:
                if item.scaling and item.scaling.stat.value not in useful_stats:
                    return True
            if run is not None and item.equip_type in (
                EquipType.WEAPON, EquipType.ARMOR,
            ):
                slot = item.equip_type.value
                equipped = self._equipped_item(run, mc, slot)
                if equipped is not None and (
                    self._gear_rank(item) < self._gear_rank(equipped)
                ):
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
            if iid == POTION_ITEM_ID or iid in exclude:
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
        potion_count = _count_potions(run)
        can_heal_in_town = potion_count > 0 or run.party.money >= price

        if self._next_encounter_is_boss(run):
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
        item = self.game_data.items.get(POTION_ITEM_ID)
        base = item.base_price if item else 25
        return calculate_buy_price(base, run.party.cha)

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
        """Enemy count of the upcoming encounter (1 if unknowable)."""
        if not run.current_zone_id or not run.zone_state:
            return 1
        zone = self.game_data.zones.get(run.current_zone_id)
        if zone is None:
            return 1
        idx = run.zone_state.current_encounter_index
        if run.zone_state.is_cleared or idx >= len(zone.encounters):
            # Overstay / endless: assume a typical pack for this zone.
            counts = [sum(e.enemy_counts) for e in zone.encounters if not e.is_boss]
            return max(1, round(sum(counts) / len(counts))) if counts else 1
        return max(1, sum(zone.encounters[idx].enemy_counts))

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
        stash_potions = [iid for iid in run.party.stash if iid == POTION_ITEM_ID]
        if not stash_potions:
            return uses

        active_chars = _active_chars(run)
        if not active_chars:
            return uses

        running_hp: dict[str, int] = {c.id: c.current_hp for c in active_chars}
        max_hp: dict[str, int] = {c.id: c.max_hp for c in active_chars}
        share = self._expected_damage_share(run)
        boss_next = self._next_encounter_is_boss(run)
        boss_target = self.config.pre_boss_retreat_hp_pct

        def drink(char_id: str) -> None:
            uses.append(ItemUse(item_id=stash_potions.pop(0), character_id=char_id))
            running_hp[char_id] = min(max_hp[char_id], running_hp[char_id] + POTION_HEAL)

        while len(stash_potions) > POTION_COMBAT_RESERVE:
            hurt = [c for c in active_chars if running_hp[c.id] < max_hp[c.id]]
            if not hurt:
                break
            hurt.sort(key=lambda c: running_hp[c.id] / max(1, max_hp[c.id]))

            dying = [c for c in hurt if running_hp[c.id] <= share]
            if dying:
                drink(dying[0].id)
                continue

            zero_waste = [
                c for c in hurt
                if max_hp[c.id] - running_hp[c.id] >= _efficient_heal_gate(max_hp[c.id])
            ]
            if zero_waste:
                drink(zero_waste[0].id)
                continue

            if boss_next:
                below_boss_target = [
                    c for c in hurt
                    if running_hp[c.id] / max(1, max_hp[c.id]) < boss_target
                ]
                if below_boss_target:
                    drink(below_boss_target[0].id)
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
    lodge_on=False,
)

SACRIST_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="MAG",
    preferred_armor_stat="DEF",  # sacrist has DEF=1 growth, 0 RES
    potion_stockpile_target=3,
    potion_stash_cap=6,
    pre_boss_retreat_hp_pct=0.90,
    lodge_on=False,
)

MARTYR_GOLDEN_CONFIG = GoldenMacroConfig(
    preferred_weapon_stat="STR",  # martyr has 0 STR but thorns/retaliate don't need weapon scaling
    preferred_armor_stat="DEF",
    potion_stockpile_target=1,
    potion_stash_cap=5,
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


def _active_chars(run: RunState) -> list:
    return [
        run.party.characters[cid] for cid in run.party.active
        if cid in run.party.characters
    ]


def _mean_party_hp_pct(run: RunState) -> float:
    active = _active_chars(run)
    if not active:
        return 1.0
    return sum(c.current_hp / max(1, c.max_hp) for c in active) / len(active)


def _count_potions(run: RunState) -> int:
    return sum(1 for iid in run.party.stash if iid == POTION_ITEM_ID)
