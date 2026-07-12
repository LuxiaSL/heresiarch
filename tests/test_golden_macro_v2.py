"""Golden Macro v2: the designer's doctrine as computable rules.

Doctrine source: memory project_macro_doctrine.md (dictated 2026-07-10).
These tests pin each rule: zero-waste heal timing, the expected-death
exception and retreat rule, boss top-up, overstay-to-debuff-cap, and
upgrade-aware shopping.
"""

from __future__ import annotations

import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.battle_record import BattleRecord, EncounterRecord
from heresiarch.engine.models.run_state import RunState
from heresiarch.policy.builtin.golden_macro import (
    OVERSTAY_DEBUFF_CAP,
    OVERSTAY_FREE_HP_PCT,
    POTION_HEAL,
    POTION_ITEM_ID,
    GoldenMacroConfig,
    GoldenMacroPolicy,
    make_golden_macro_for_job,
)


@pytest.fixture(scope="module")
def game_data() -> GameData:
    return load_all(Path("data"))


def _new_run(game_data: GameData, job: str = "einherjar") -> tuple[GameLoop, RunState]:
    gl = GameLoop(game_data, random.Random(42))
    return gl, gl.new_run("test", "T", job)


def _set_mc_hp(run: RunState, hp: int, max_hp: int | None = None) -> RunState:
    chars = dict(run.party.characters)
    for cid, c in chars.items():
        if c.is_mc:
            update: dict = {"current_hp": hp}
            if max_hp is not None:
                update["max_hp"] = max_hp
            chars[cid] = c.model_copy(update=update)
    party = run.party.model_copy(update={"characters": chars})
    return run.model_copy(update={"party": party})


def _with_stash(run: RunState, items: list[str]) -> RunState:
    party = run.party.model_copy(update={"stash": items})
    return run.model_copy(update={"party": party})


def _with_gold(run: RunState, gold: int) -> RunState:
    party = run.party.model_copy(update={"money": gold})
    return run.model_copy(update={"party": party})


def _with_last_fight_damage(run: RunState, taken: int, zone_id: str = "zone_01") -> RunState:
    rec = EncounterRecord(
        zone_id=zone_id, encounter_index=0, result="victory",
        rounds_taken=3, total_damage_taken=taken,
    )
    return run.model_copy(
        update={"battle_record": BattleRecord(encounters=[rec])},
    )


def _macro(game_data: GameData, **cfg) -> GoldenMacroPolicy:
    return GoldenMacroPolicy(GoldenMacroConfig(**cfg), game_data)


def _with_recruit(
    game_data: GameData,
    run: RunState,
    job_id: str = "onmyoji",
    level: int = 5,
    equipment: dict[str, str | None] | None = None,
) -> tuple[RunState, str]:
    """Add an active recruit with explicit (default: empty) equipment."""
    from heresiarch.engine.formulas import (
        calculate_effective_stats,
        calculate_max_hp,
        calculate_stats_at_level,
    )
    from heresiarch.engine.models.jobs import CharacterInstance

    job = game_data.jobs[job_id]
    stats = calculate_stats_at_level(job.growth, level)
    slots: dict[str, str | None] = {
        "WEAPON": None, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None,
    }
    slots.update(equipment or {})
    equipped_items = [
        game_data.items[iid] for iid in slots.values()
        if iid and iid in game_data.items
    ]
    effective = calculate_effective_stats(stats, equipped_items, [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, effective.DEF)
    char = CharacterInstance(
        id=f"recruit_{job_id}",
        name=f"{job.name} Recruit",
        job_id=job_id,
        level=level,
        base_stats=stats,
        effective_stats=effective,
        current_hp=max_hp,
        max_hp=max_hp,
        abilities=["basic_attack", job.innate_ability_id],
        equipment=slots,
    )
    chars = dict(run.party.characters)
    chars[char.id] = char
    party = run.party.model_copy(update={
        "characters": chars,
        "active": list(run.party.active) + [char.id],
    })
    return run.model_copy(update={"party": party}), char.id


# ---------------------------------------------------------------------------
# Zero-waste heal rule
# ---------------------------------------------------------------------------


class TestZeroWasteHeal:
    def test_no_drink_one_hp_short_of_efficiency(self, game_data: GameData):
        """missing = POTION_HEAL - 1 → wasteful, save the potion."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 120 - (POTION_HEAL - 1), max_hp=120)
        run = _with_stash(run, [POTION_ITEM_ID])
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_between_encounter_items(run) == []

    def test_drinks_the_moment_missing_equals_heal(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 120 - POTION_HEAL, max_hp=120)
        run = _with_stash(run, [POTION_ITEM_ID])
        macro = make_golden_macro_for_job(game_data, "einherjar")
        uses = macro.decide_between_encounter_items(run)
        assert len(uses) == 1
        assert uses[0].item_id == POTION_ITEM_ID

    def test_expected_death_overrides_waste(self, game_data: GameData):
        """hp 30, last fight took 40 — drink even though missing < heal."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 30, max_hp=65)
        run = _with_stash(run, [POTION_ITEM_ID])
        run = _with_last_fight_damage(run, taken=40)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        uses = macro.decide_between_encounter_items(run)
        assert len(uses) >= 1

    def test_safe_and_inefficient_saves_the_potion(self, game_data: GameData):
        """Missing 30 with no danger signal and no boss → no drink."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 90, max_hp=120)
        run = _with_stash(run, [POTION_ITEM_ID])
        run = _with_last_fight_damage(run, taken=10)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_between_encounter_items(run) == []

    def test_per_job_risk_threshold(self, game_data: GameData):
        """The doctrine's one per-job delta. Glass (onmyoji, target 0.75)
        enters every fight topped; survive-cycle frames (berserker,
        target off) bank potions for the projected-death moment — the
        v2.1 flat half-bar gate crashed berserker's median 26 → 4 by
        sipping the pack budget on ordinary chip."""
        gl, run = _new_run(game_data, job="onmyoji")
        run = gl.enter_zone(run, "zone_01")
        run = _with_stash(run, [POTION_ITEM_ID])
        onmyoji = make_golden_macro_for_job(game_data, "onmyoji")

        low = _set_mc_hp(run, 20, max_hp=40)   # 50% < 0.75 → drink
        assert len(onmyoji.decide_between_encounter_items(low)) == 1
        high = _set_mc_hp(run, 31, max_hp=40)  # 77.5% ≥ 0.75, waste → save
        assert onmyoji.decide_between_encounter_items(high) == []

        glb, runb = _new_run(game_data, job="berserker")
        runb = glb.enter_zone(runb, "zone_01")
        runb = _with_stash(runb, [POTION_ITEM_ID])
        berserker = make_golden_macro_for_job(game_data, "berserker")
        lowb = _set_mc_hp(runb, 15, max_hp=30)  # 50%, no danger signal
        assert berserker.decide_between_encounter_items(lowb) == []

    def test_boss_topup_accepts_waste(self, game_data: GameData):
        """Below the pre-boss target with the boss up next → top up."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        zone = game_data.zones["zone_01"]
        boss_idx = next(i for i, e in enumerate(zone.encounters) if e.is_boss)
        zs = run.zone_state.model_copy(update={"current_encounter_index": boss_idx})
        run = run.model_copy(update={"zone_state": zs})
        run = _set_mc_hp(run, 100, max_hp=120)  # 83% < 0.90, missing 20 < heal
        run = _with_stash(run, [POTION_ITEM_ID])
        macro = make_golden_macro_for_job(game_data, "einherjar")
        uses = macro.decide_between_encounter_items(run)
        assert len(uses) >= 1


# ---------------------------------------------------------------------------
# Expected-death retreat
# ---------------------------------------------------------------------------


class TestExpectedDeathRetreat:
    def test_retreats_when_next_fight_projects_lethal(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 25, max_hp=65)
        run = _with_gold(run, 100)
        run = _with_stash(run, [])  # potions already drunk
        run = _with_last_fight_damage(run, taken=40)
        macro = _macro(game_data, potion_stockpile_target=0)
        assert macro.decide_retreat_to_town(run) is True

    def test_stays_when_projection_is_survivable(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 60, max_hp=65)
        run = _with_gold(run, 100)
        run = _with_stash(run, [])
        run = _with_last_fight_damage(run, taken=20)
        macro = _macro(game_data, potion_stockpile_target=0)
        assert macro.decide_retreat_to_town(run) is False

    def test_broke_party_does_not_loop_the_door(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 10, max_hp=65)
        run = _with_gold(run, 0)
        run = _with_stash(run, [])
        run = _with_last_fight_damage(run, taken=40)
        macro = _macro(game_data, potion_stockpile_target=0)
        assert macro.decide_retreat_to_town(run) is False

    def test_restock_trip_needs_one_affordable_potion(self, game_data: GameData):
        """One affordable, needed potion justifies the trip ("go back,
        buy potion, heal") — waiting for full-refill gold deadlocked
        early runs at the zone door."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _with_stash(run, [])
        macro = _macro(game_data, potion_stockpile_target=2)
        price = macro._potion_price(run)
        assert macro.decide_retreat_to_town(_with_gold(run, price)) is True
        assert macro.decide_retreat_to_town(_with_gold(run, price - 1)) is False


# ---------------------------------------------------------------------------
# Overstay: farm while free, to the debuff cap
# ---------------------------------------------------------------------------


class TestOverstay:
    def _cleared_run(self, game_data: GameData, battles: int) -> RunState:
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        zs = run.zone_state.model_copy(
            update={"is_cleared": True, "overstay_battles": battles},
        )
        return run.model_copy(update={"zone_state": zs})

    def test_cap_is_derived_from_loot_formula(self):
        assert OVERSTAY_DEBUFF_CAP == 20  # 5%/battle → 100% at 20

    def test_farms_while_hp_flat(self, game_data: GameData):
        run = self._cleared_run(game_data, battles=5)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_overstay(run) is True

    def test_bails_when_chip_resumes(self, game_data: GameData):
        run = self._cleared_run(game_data, battles=5)
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        hurt = int(mc.max_hp * (OVERSTAY_FREE_HP_PCT - 0.05))
        run = _set_mc_hp(run, hurt)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_overstay(run) is False

    def test_stops_at_debuff_cap(self, game_data: GameData):
        run = self._cleared_run(game_data, battles=OVERSTAY_DEBUFF_CAP)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_overstay(run) is False


# ---------------------------------------------------------------------------
# Endless zones: perpetual pre-boss (v2.2 — 33/48 einherjar died in the pit)
# ---------------------------------------------------------------------------


class TestEndlessZones:
    def _pit_run(self, game_data: GameData) -> RunState:
        from heresiarch.engine.models.zone import ZoneState

        gl, run = _new_run(game_data)
        return run.model_copy(update={
            "current_zone_id": "the_pit",
            "zone_state": ZoneState(template_id="the_pit", is_cleared=True),
        })

    def test_pack_size_uses_observed_fights_not_one(self, game_data: GameData):
        """`encounters: []` made v2.1 project ONE-enemy pit fights."""
        run = self._pit_run(game_data)
        rec = EncounterRecord(
            zone_id="the_pit", encounter_index=0, result="victory",
            enemy_template_ids=["brute_oni", "slime", "slime"],
            total_damage_taken=60,
        )
        run = run.model_copy(
            update={"battle_record": BattleRecord(encounters=[rec])},
        )
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro._next_encounter_enemy_count(run) >= 3

    def test_pack_size_floor_two_with_no_history(self, game_data: GameData):
        run = self._pit_run(game_data)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro._next_encounter_enemy_count(run) >= 2

    def test_pit_fights_entered_near_full(self, game_data: GameData):
        """Every endless fight gets the pre-boss top-up (waste accepted)."""
        run = self._pit_run(game_data)
        run = _set_mc_hp(run, 96, max_hp=120)  # 80% < 0.90, missing 24 < gate
        run = _with_stash(run, [POTION_ITEM_ID])
        macro = make_golden_macro_for_job(game_data, "einherjar")
        uses = macro.decide_between_encounter_items(run)
        assert len(uses) == 1

    def test_pit_retreats_below_preboss_target(self, game_data: GameData):
        run = self._pit_run(game_data)
        run = _set_mc_hp(run, 96, max_hp=120)  # 80%
        run = _with_stash(run, [])
        run = _with_gold(run, 1000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_retreat_to_town(run) is True

    def test_pit_no_retreat_when_healthy(self, game_data: GameData):
        run = self._pit_run(game_data)
        run = _set_mc_hp(run, 118, max_hp=120)
        run = _with_stash(run, [POTION_ITEM_ID])
        run = _with_gold(run, 1000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_retreat_to_town(run) is False


# ---------------------------------------------------------------------------
# Upgrade-aware shopping
# ---------------------------------------------------------------------------


class TestUpgradeShopping:
    def test_buys_weapon_into_empty_slot(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = _with_gold(run, 500)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["iron_blade", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "iron_blade" in buys

    def test_buys_strict_upgrade_over_equipped(self, game_data: GameData):
        """v1 only filled empty slots — v2 upgrades (the designer does)."""
        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        run = _with_gold(run, 50_000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["runic_edge", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "runic_edge" in buys

    def test_does_not_rebuy_same_tier(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        run = _with_gold(run, 50_000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["iron_blade", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "iron_blade" not in buys

    def test_sells_displaced_worse_gear(self, game_data: GameData):
        """After an upgrade the old weapon sits in the stash — sell it."""
        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade", "runic_edge"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "runic_edge", "WEAPON")
        run = _with_gold(run, 100)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, [POTION_ITEM_ID])
        sells = [a.item_id for a in actions if a.action == "sell"]
        assert "iron_blade" in sells

    def test_wrong_stat_weapon_never_bought(self, game_data: GameData):
        """A MAG frame doesn't buy STR swords no matter the tier."""
        gl, run = _new_run(game_data, job="onmyoji")
        run = _with_gold(run, 50_000)
        macro = make_golden_macro_for_job(game_data, "onmyoji")
        actions = macro.decide_shop(run, ["runic_edge", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "runic_edge" not in buys

    def test_no_growth_job_skips_expensive_weapon_upgrades(
        self, game_data: GameData,
    ):
        """Martyr (0 STR growth) fills its empty slot with a cheap starter
        but must not sink thousands into STR weapons it can't scale —
        v2.0 did, and paid 1370→1011 gold / 8→15 deaths for it."""
        gl, run = _new_run(game_data, job="martyr")
        run = _with_gold(run, 50_000)
        macro = make_golden_macro_for_job(game_data, "martyr")

        # Empty slot: the cheap starter is still worth its flat damage.
        actions = macro.decide_shop(run, ["iron_blade", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "iron_blade" in buys

        # Equipped: the tier-2 STR sword is a museum piece for martyr.
        run = _with_stash(run, ["iron_blade"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        actions = macro.decide_shop(run, ["runic_edge", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "runic_edge" not in buys
        # And it doesn't burn town trips chasing one either (top armor
        # equipped so the armor slot can't justify the visit instead).
        run = _with_stash(run, ["void_bastion"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "void_bastion", "ARMOR")
        run = run.model_copy(update={"zones_completed": ["zone_01"]})
        assert macro._affordable_upgrade_exists(run) is False


# ---------------------------------------------------------------------------
# Driver: upgrade-aware auto-equip
# ---------------------------------------------------------------------------


class TestAutoEquipUpgrade:
    def test_equips_better_weapon_and_displaces_old(self, game_data: GameData):
        from heresiarch.tools.run_driver import _auto_equip_party

        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        run = _with_stash(run, ["runic_edge"])

        ctx = SimpleNamespace(game_loop=gl, game_data=game_data)
        run = _auto_equip_party(run, ctx)

        mc = run.party.characters[mc.id]
        assert mc.equipment["WEAPON"] == "runic_edge"
        assert "iron_blade" in run.party.stash

    def test_leaves_better_equipped_gear_alone(self, game_data: GameData):
        from heresiarch.tools.run_driver import _auto_equip_party

        gl, run = _new_run(game_data)
        run = _with_stash(run, ["runic_edge"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "runic_edge", "WEAPON")
        run = _with_stash(run, ["iron_blade"])

        ctx = SimpleNamespace(game_loop=gl, game_data=game_data)
        run = _auto_equip_party(run, ctx)

        mc = run.party.characters[mc.id]
        assert mc.equipment["WEAPON"] == "runic_edge"


# ---------------------------------------------------------------------------
# Potion ladder (pit lever 2: a 400-HP frame heals in gulps, not sips)
# ---------------------------------------------------------------------------


class TestPotionLadder:
    def test_big_frame_buys_the_bigger_rung(self, game_data: GameData):
        """Post-zone-3 shop stocks 'potion' (150): a pit-sized frame
        restocks with those, not 50-HP minors."""
        gl, run = _new_run(game_data)
        run = _set_mc_hp(run, 400, max_hp=400)
        run = _with_gold(run, 5000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["minor_potion", "potion"])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "potion" in buys
        assert "minor_potion" not in buys

    def test_small_frame_sticks_to_minors(self, game_data: GameData):
        """A Lv1 frame (65 HP) can never zero-waste a 150 heal."""
        gl, run = _new_run(game_data)
        run = _with_gold(run, 5000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["minor_potion", "potion"])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "minor_potion" in buys
        assert "potion" not in buys

    def test_ladder_degrades_by_affordability(self, game_data: GameData):
        """Big frame, small purse: an affordable minor beats no potion —
        the shop must agree with the 'one affordable potion justifies
        the trip' predicate."""
        gl, run = _new_run(game_data)
        run = _set_mc_hp(run, 400, max_hp=400)
        run = _with_gold(run, 40)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["minor_potion", "potion"])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert buys == ["minor_potion"]

    def test_zero_waste_picks_the_fitting_rung(self, game_data: GameData):
        """Missing 160 absorbs the 150; missing 60 only absorbs the 50."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _with_stash(run, ["minor_potion", "potion"])
        macro = make_golden_macro_for_job(game_data, "einherjar")

        deep = _set_mc_hp(run, 240, max_hp=400)  # missing 160
        uses = macro.decide_between_encounter_items(deep)
        assert [u.item_id for u in uses][:1] == ["potion"]

        shallow = _set_mc_hp(run, 340, max_hp=400)  # missing 60
        uses = macro.decide_between_encounter_items(shallow)
        assert [u.item_id for u in uses] == ["minor_potion"]

    def test_projected_death_drinks_the_largest(self, game_data: GameData):
        """Survival beats efficiency: the biggest held heal goes down."""
        gl, run = _new_run(game_data)
        run = gl.enter_zone(run, "zone_01")
        run = _set_mc_hp(run, 30, max_hp=400)
        run = _with_stash(run, ["minor_potion", "potion"])
        run = _with_last_fight_damage(run, taken=40)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        uses = macro.decide_between_encounter_items(run)
        assert uses and uses[0].item_id == "potion"

    def test_stockpile_counts_every_rung(self, game_data: GameData):
        """Three 150s satisfy a stockpile target of 3 — no restock trip."""
        gl, run = _new_run(game_data)
        run = _with_stash(run, ["potion", "potion", "potion"])
        run = _with_gold(run, 1000)
        macro = _macro(game_data, potion_stockpile_target=3)
        assert macro._town_trip_worthwhile(run) is False


# ---------------------------------------------------------------------------
# Party-wide gearing (pit lever 1: join-time recruit gear must not freeze)
# ---------------------------------------------------------------------------


class TestPartyGearing:
    def test_shop_buys_recruit_weapon_with_leftover_gold(
        self, game_data: GameData,
    ):
        """MAG recruit on an einherjar roster: the shop buys it a staff
        once potions are covered."""
        gl, run = _new_run(game_data)
        run, _rid = _with_recruit(game_data, run, "onmyoji")
        run = _with_gold(run, 5000)
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["spirit_lens", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "spirit_lens" in buys
        # Potions (the lifeline) are queued before recruit gear.
        assert buys.index(POTION_ITEM_ID) < buys.index("spirit_lens")

    def test_potions_beat_recruit_gear_when_gold_tight(
        self, game_data: GameData,
    ):
        gl, run = _new_run(game_data)
        run, _rid = _with_recruit(game_data, run, "onmyoji")
        run = _with_gold(run, 30)  # one potion, nothing more
        macro = make_golden_macro_for_job(game_data, "einherjar")
        actions = macro.decide_shop(run, ["spirit_lens", POTION_ITEM_ID])
        buys = [a.item_id for a in actions if a.action == "buy"]
        assert "spirit_lens" not in buys
        assert POTION_ITEM_ID in buys

    def test_keeps_stash_gear_a_recruit_can_use(self, game_data: GameData):
        """A MAG staff is dead weight for a solo einherjar but must NOT
        be sold while an onmyoji recruit could wear it."""
        gl, run = _new_run(game_data)
        run = _with_stash(run, ["spirit_lens"])
        macro = make_golden_macro_for_job(game_data, "einherjar")
        solo_actions = macro.decide_shop(run, [POTION_ITEM_ID])
        assert any(
            a.action == "sell" and a.item_id == "spirit_lens"
            for a in solo_actions
        )
        run, _rid = _with_recruit(game_data, run, "onmyoji")
        roster_actions = macro.decide_shop(run, [POTION_ITEM_ID])
        assert not any(
            a.action == "sell" and a.item_id == "spirit_lens"
            for a in roster_actions
        )

    def test_auto_equip_gears_recruit_from_stash(self, game_data: GameData):
        from heresiarch.tools.run_driver import _auto_equip_party

        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade", "warding_mail"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        run = gl.equip_item(run, mc.id, "warding_mail", "ARMOR")
        run, rid = _with_recruit(game_data, run, "onmyoji")
        run = _with_stash(run, ["spirit_lens", "iron_guard"])

        ctx = SimpleNamespace(game_loop=gl, game_data=game_data)
        run = _auto_equip_party(run, ctx)

        recruit = run.party.characters[rid]
        assert recruit.equipment["WEAPON"] == "spirit_lens"
        assert recruit.equipment["ARMOR"] == "iron_guard"
        # MC kept its equal-rank blade — no pointless swap.
        assert run.party.characters[mc.id].equipment["WEAPON"] == "iron_blade"

    def test_auto_equip_mc_gets_first_pick(self, game_data: GameData):
        """One upgrade both could wear: doctrine gives it to the MC."""
        from heresiarch.tools.run_driver import _auto_equip_party

        gl, run = _new_run(game_data)
        run = _with_stash(run, ["iron_blade"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "iron_blade", "WEAPON")
        run, rid = _with_recruit(
            game_data, run, "berserker", equipment={"WEAPON": "iron_blade"},
        )
        run = _with_stash(run, ["runic_edge"])

        ctx = SimpleNamespace(game_loop=gl, game_data=game_data)
        run = _auto_equip_party(run, ctx)

        assert run.party.characters[mc.id].equipment["WEAPON"] == "runic_edge"
        assert run.party.characters[rid].equipment["WEAPON"] == "iron_blade"

    def test_auto_equip_growth_gates_recruit_upgrades(
        self, game_data: GameData,
    ):
        """A 0-STR-growth recruit never upgrades INTO expensive STR gear
        (empty slots still take anything — flat damage beats none)."""
        from heresiarch.tools.run_driver import _auto_equip_party

        gl, run = _new_run(game_data)
        run = _with_stash(run, ["runic_edge"])
        mc = next(c for c in run.party.characters.values() if c.is_mc)
        run = gl.equip_item(run, mc.id, "runic_edge", "WEAPON")
        run, rid = _with_recruit(
            game_data, run, "martyr", equipment={"WEAPON": "iron_blade"},
        )
        run = _with_stash(run, ["runic_edge"])

        ctx = SimpleNamespace(game_loop=gl, game_data=game_data)
        run = _auto_equip_party(run, ctx)

        # MC already wears equal-rank runic_edge; martyr must not take
        # the stash one as an "upgrade" it can't scale.
        assert run.party.characters[rid].equipment["WEAPON"] == "iron_blade"
        assert "runic_edge" in run.party.stash


# ---------------------------------------------------------------------------
# Town visits
# ---------------------------------------------------------------------------


class TestTownVisit:
    def test_visits_for_efficient_heal(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = _set_mc_hp(run, 120 - POTION_HEAL, max_hp=120)
        run = _with_gold(run, 100)
        macro = _macro(game_data, potion_stockpile_target=0)
        assert macro.decide_visit_town(run, ["town_shinto"]) is not None

    def test_skips_town_when_topped_and_stocked(self, game_data: GameData):
        gl, run = _new_run(game_data)
        run = _with_stash(run, [POTION_ITEM_ID])
        run = _with_gold(run, 20)
        macro = _macro(game_data, potion_stockpile_target=1)
        assert macro.decide_visit_town(run, ["town_shinto"]) is None

    def test_visits_for_affordable_upgrade_after_zone_clear(
        self, game_data: GameData,
    ):
        gl, run = _new_run(game_data)
        run = _with_stash(run, [POTION_ITEM_ID])
        run = run.model_copy(update={"zones_completed": ["zone_01"]})
        run = _with_gold(run, 50_000)  # can afford any weapon in the registry
        macro = make_golden_macro_for_job(game_data, "einherjar")
        assert macro.decide_visit_town(run, ["town_shinto"]) is not None
