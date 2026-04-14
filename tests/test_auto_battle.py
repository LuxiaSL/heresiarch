"""Auto-battle logic tests: decision validation, retargeting, record matching.

Tests the auto-battle replay methods on CombatScreen. Static methods are tested
directly; instance methods that access self.app use a mocked app fixture.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    TargetType,
)
from heresiarch.engine.models.battle_record import (
    BattleRecord,
    EncounterRecord,
    RoundRecord,
)
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatantState,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.run_state import RunState
from heresiarch.engine.models.stats import StatBlock
from heresiarch.tui.screens.combat import CombatScreen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _combatant(
    cid: str,
    *,
    is_player: bool = True,
    hp: int = 100,
    max_hp: int = 100,
    alive: bool = True,
    ap: int = 0,
    spd: int = 10,
    cooldowns: dict[str, int] | None = None,
    taunted_by: list[str] | None = None,
    charge_turns: int = 0,
    ability_ids: list[str] | None = None,
) -> CombatantState:
    stats = StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=spd)
    return CombatantState(
        id=cid,
        is_player=is_player,
        current_hp=hp,
        max_hp=max_hp,
        base_stats=stats,
        equipment_stats=stats,
        effective_stats=stats,
        is_alive=alive,
        action_points=ap,
        cooldowns=cooldowns or {},
        taunted_by=taunted_by or [],
        charge_turns_remaining=charge_turns,
        ability_ids=ability_ids or ["basic_attack", "heavy_strike", "heal", "fireball", "brace", "mass_heal"],
    )


def _combat(
    players: list[CombatantState],
    enemies: list[CombatantState],
) -> CombatState:
    return CombatState(
        player_combatants=players,
        enemy_combatants=enemies,
    )


def _encounter(
    enemy_ids: list[str],
    result: str = "victory",
    rounds: list[RoundRecord] | None = None,
) -> EncounterRecord:
    return EncounterRecord(
        zone_id="zone_01",
        encounter_index=0,
        enemy_template_ids=enemy_ids,
        result=result,
        rounds=rounds or [RoundRecord(round_number=1)],
    )


def _decision(
    cid: str,
    cs: CheatSurviveChoice = CheatSurviveChoice.NORMAL,
    ability: str = "basic_attack",
    targets: list[str] | None = None,
    cheat_actions: int = 0,
    cheat_extras: list[CombatAction] | None = None,
    bonus: list[CombatAction] | None = None,
) -> PlayerTurnDecision:
    primary = CombatAction(
        actor_id=cid,
        ability_id=ability,
        target_ids=targets or [],
    )
    return PlayerTurnDecision(
        combatant_id=cid,
        cheat_survive=cs,
        cheat_actions=cheat_actions,
        primary_action=primary,
        cheat_extra_actions=cheat_extras or [],
        bonus_actions=bonus or [],
    )


# Minimal ability registry for tests.
_ABILITIES: dict[str, Ability] = {
    "basic_attack": Ability(
        id="basic_attack", name="Basic Attack",
        category=AbilityCategory.OFFENSIVE, target=TargetType.SINGLE_ENEMY,
    ),
    "heal": Ability(
        id="heal", name="Heal",
        category=AbilityCategory.SUPPORT, target=TargetType.SINGLE_ALLY,
        effects=[AbilityEffect(heal_percent=0.3)],
    ),
    "fireball": Ability(
        id="fireball", name="Fireball",
        category=AbilityCategory.OFFENSIVE, target=TargetType.ALL_ENEMIES,
        effects=[AbilityEffect(base_damage=20)],
    ),
    "brace": Ability(
        id="brace", name="Brace",
        category=AbilityCategory.DEFENSIVE, target=TargetType.SELF,
        effects=[AbilityEffect(def_buff=5)],
    ),
    "heavy_strike": Ability(
        id="heavy_strike", name="Heavy Strike",
        category=AbilityCategory.OFFENSIVE, target=TargetType.SINGLE_ENEMY,
        effects=[AbilityEffect(base_damage=15)], cooldown=2,
    ),
    "mass_heal": Ability(
        id="mass_heal", name="Mass Heal",
        category=AbilityCategory.SUPPORT, target=TargetType.ALL_ALLIES,
        effects=[AbilityEffect(heal_percent=0.2)],
    ),
}


def _make_screen(
    stash: list[str] | None = None,
    abilities: dict[str, Ability] | None = None,
    encounter_record: EncounterRecord | None = None,
    claimed: list[str] | None = None,
) -> tuple[CombatScreen, SimpleNamespace]:
    """Build a CombatScreen + mock app without a real Textual compositor."""
    screen = CombatScreen.__new__(CombatScreen)
    screen._claimed_items = claimed if claimed is not None else []
    screen._encounter_record = encounter_record
    mock_app = SimpleNamespace(
        run_state=SimpleNamespace(
            party=SimpleNamespace(stash=stash or []),
        ),
        game_data=SimpleNamespace(abilities=abilities or _ABILITIES),
    )
    return screen, mock_app


def _patch_app(screen: CombatScreen, mock_app: SimpleNamespace):
    """Context manager to patch self.app on a CombatScreen."""
    return patch.object(
        type(screen), "app",
        new_callable=PropertyMock,
        return_value=mock_app,
    )


# ---------------------------------------------------------------------------
# _retarget (static)
# ---------------------------------------------------------------------------

class TestRetarget:
    """CombatScreen._retarget: dead-target remapping to living combatants."""

    def test_living_targets_unchanged(self) -> None:
        result = CombatScreen._retarget(["e1", "e2"], ["e1", "e2"])
        assert result == ["e1", "e2"]

    def test_dead_target_falls_back(self) -> None:
        result = CombatScreen._retarget(["e1"], ["e2"])
        assert result == ["e2"]

    def test_all_dead_falls_back_to_first_living(self) -> None:
        result = CombatScreen._retarget(["dead_a", "dead_b"], ["e1", "e2"])
        assert result == ["e1"]

    def test_empty_living_returns_original(self) -> None:
        result = CombatScreen._retarget(["e1"], [])
        assert result == ["e1"]

    def test_partial_overlap(self) -> None:
        result = CombatScreen._retarget(["dead_x", "e2"], ["e1", "e2"])
        assert result == ["e2"]

    def test_empty_original_falls_back_to_first(self) -> None:
        result = CombatScreen._retarget([], ["e1"])
        assert result == ["e1"]


# ---------------------------------------------------------------------------
# _retarget_for_ability (static)
# ---------------------------------------------------------------------------

class TestRetargetForAbility:
    """Ability-aware retargeting: returns target ID lists."""

    def _3v2(self) -> tuple[CombatState, list[str], list[str]]:
        p1, p2, p3 = _combatant("p1"), _combatant("p2"), _combatant("p3")
        e1, e2 = _combatant("e1", is_player=False), _combatant("e2", is_player=False)
        combat = _combat([p1, p2, p3], [e1, e2])
        return combat, ["e1", "e2"], ["p1", "p2", "p3"]

    def test_self_target(self) -> None:
        combat, enemies, allies = self._3v2()
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["brace"], ["e1"], "p1", combat, enemies, allies,
        )
        assert result == ["p1"]

    def test_all_enemies(self) -> None:
        combat, enemies, allies = self._3v2()
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["fireball"], ["e1"], "p1", combat, enemies, allies,
        )
        assert set(result) == {"e1", "e2"}

    def test_all_allies(self) -> None:
        combat, enemies, allies = self._3v2()
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["mass_heal"], ["p1"], "p1", combat, enemies, allies,
        )
        assert set(result) == {"p1", "p2", "p3"}

    def test_single_enemy_alive(self) -> None:
        combat, enemies, allies = self._3v2()
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["basic_attack"], ["e2"], "p1", combat, enemies, allies,
        )
        assert result == ["e2"]

    def test_single_enemy_dead_retargets(self) -> None:
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        combat = _combat([p1], [e1, e2])
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["basic_attack"], ["e1"], "p1", combat, ["e2"], ["p1"],
        )
        assert result == ["e2"]

    def test_single_ally_alive(self) -> None:
        combat, enemies, allies = self._3v2()
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["heal"], ["p2"], "p1", combat, enemies, allies,
        )
        assert result == ["p2"]

    def test_single_ally_dead_retargets(self) -> None:
        p1 = _combatant("p1")
        p2 = _combatant("p2", alive=False)
        p3 = _combatant("p3")
        combat = _combat([p1, p2, p3], [_combatant("e1", is_player=False)])
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["heal"], ["p2"], "p1", combat, ["e1"], ["p1", "p3"],
        )
        assert result == ["p1"]

    def test_all_enemies_with_dead(self) -> None:
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        combat = _combat([p1], [e1, e2])
        result = CombatScreen._retarget_for_ability(
            _ABILITIES["fireball"], ["e1"], "p1", combat, ["e2"], ["p1"],
        )
        assert result == ["e2"]


# ---------------------------------------------------------------------------
# _find_matching_record
# ---------------------------------------------------------------------------

class TestFindMatchingRecord:
    """EncounterRecord lookup: same enemy composition → most recent victory."""

    def _screen_for(self, enemy_ids: list[str]) -> CombatScreen:
        screen = CombatScreen.__new__(CombatScreen)
        screen._encounter_record = EncounterRecord(
            zone_id="zone_01", encounter_index=0,
            enemy_template_ids=enemy_ids,
        )
        return screen

    def _run(self, encounters: list[EncounterRecord]) -> RunState:
        return RunState(
            run_id="test_run",
            battle_record=BattleRecord(encounters=encounters),
            party=Party(),
        )

    def test_exact_match(self) -> None:
        enc = _encounter(["slime", "goblin"])
        screen = self._screen_for(["slime", "goblin"])
        assert screen._find_matching_record(self._run([enc])) is enc

    def test_sorted_comparison(self) -> None:
        enc = _encounter(["goblin", "slime"])
        screen = self._screen_for(["slime", "goblin"])
        assert screen._find_matching_record(self._run([enc])) is enc

    def test_skips_defeats(self) -> None:
        defeat = _encounter(["slime"], "defeat")
        victory = _encounter(["slime"], "victory")
        screen = self._screen_for(["slime"])
        assert screen._find_matching_record(self._run([defeat, victory])) is victory

    def test_no_match_different_enemies(self) -> None:
        enc = _encounter(["slime"])
        screen = self._screen_for(["goblin"])
        assert screen._find_matching_record(self._run([enc])) is None

    def test_empty_history(self) -> None:
        screen = self._screen_for(["slime"])
        assert screen._find_matching_record(self._run([])) is None

    def test_most_recent_returned(self) -> None:
        old = _encounter(["slime"])
        new = _encounter(["slime"])
        screen = self._screen_for(["slime"])
        assert screen._find_matching_record(self._run([old, new])) is new

    def test_defeats_only_returns_none(self) -> None:
        d1 = _encounter(["slime"], "defeat")
        d2 = _encounter(["slime"], "defeat")
        screen = self._screen_for(["slime"])
        assert screen._find_matching_record(self._run([d1, d2])) is None

    def test_duplicate_template_ids(self) -> None:
        enc = _encounter(["slime", "slime"])
        screen = self._screen_for(["slime", "slime"])
        assert screen._find_matching_record(self._run([enc])) is enc

    def test_duplicate_mismatch(self) -> None:
        enc = _encounter(["slime"])
        screen = self._screen_for(["slime", "slime"])
        assert screen._find_matching_record(self._run([enc])) is None

    def test_skips_empty_rounds(self) -> None:
        """A victory with no recorded rounds is not matchable for replay."""
        enc = EncounterRecord(
            zone_id="zone_01", encounter_index=0,
            enemy_template_ids=["slime"], result="victory", rounds=[],
        )
        screen = self._screen_for(["slime"])
        assert screen._find_matching_record(self._run([enc])) is None

    def test_no_encounter_record(self) -> None:
        screen = CombatScreen.__new__(CombatScreen)
        screen._encounter_record = None
        assert screen._find_matching_record(self._run([])) is None


# ---------------------------------------------------------------------------
# _make_fallback_decision
# ---------------------------------------------------------------------------

class TestFallbackDecision:

    def test_normal_basic_attack(self) -> None:
        screen = CombatScreen.__new__(CombatScreen)
        dec = screen._make_fallback_decision("p1", ["e1"])
        assert dec.combatant_id == "p1"
        assert dec.cheat_survive == CheatSurviveChoice.NORMAL
        assert dec.primary_action is not None
        assert dec.primary_action.ability_id == "basic_attack"
        assert dec.primary_action.target_ids == ["e1"]

    def test_no_enemies_targets_self(self) -> None:
        screen = CombatScreen.__new__(CombatScreen)
        dec = screen._make_fallback_decision("p1", [])
        assert dec.primary_action.target_ids == ["p1"]

    def test_picks_first_enemy(self) -> None:
        screen = CombatScreen.__new__(CombatScreen)
        dec = screen._make_fallback_decision("p1", ["e1", "e2"])
        assert dec.primary_action.target_ids == ["e1"]


# ---------------------------------------------------------------------------
# _validate_auto_action (needs mocked app)
# ---------------------------------------------------------------------------

class TestValidateAutoAction:

    def test_none_action_returns_fallback(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                None, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_windup_push_while_charging(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", charge_turns=2)
        action = CombatAction(actor_id="p1", is_windup_push=True)
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.is_windup_push is True

    def test_windup_push_not_charging_returns_fallback(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", charge_turns=0)
        action = CombatAction(actor_id="p1", is_windup_push=True)
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_item_in_stash(self) -> None:
        screen, app = _make_screen(stash=["minor_potion"])
        p1 = _combatant("p1")
        p2 = _combatant("p2")
        action = CombatAction(
            actor_id="p1", ability_id="use_item",
            item_id="minor_potion", target_ids=["p2"],
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1, p2], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1", "p2"],
            )
        assert result.item_id == "minor_potion"
        assert "minor_potion" in screen._claimed_items

    def test_item_not_in_stash_returns_fallback(self) -> None:
        screen, app = _make_screen(stash=[])
        p1 = _combatant("p1")
        action = CombatAction(
            actor_id="p1", ability_id="use_item",
            item_id="minor_potion", target_ids=["p1"],
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_item_already_claimed_returns_fallback(self) -> None:
        screen, app = _make_screen(stash=["minor_potion"], claimed=["minor_potion"])
        p1 = _combatant("p1")
        action = CombatAction(
            actor_id="p1", ability_id="use_item",
            item_id="minor_potion", target_ids=["p1"],
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_ability_on_cooldown_returns_fallback(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", cooldowns={"heavy_strike": 2})
        e1 = _combatant("e1", is_player=False)
        action = CombatAction(actor_id="p1", ability_id="heavy_strike", target_ids=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_ability_not_on_cooldown_kept(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", cooldowns={})
        e1 = _combatant("e1", is_player=False)
        action = CombatAction(actor_id="p1", ability_id="heavy_strike", target_ids=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.ability_id == "heavy_strike"

    def test_dead_enemy_target_retargets(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        action = CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [e1, e2]), ["e2"], ["p1"],
            )
        assert result.target_ids == ["e2"]

    def test_ability_not_known_returns_fallback(self) -> None:
        """Ability the character doesn't know falls back to basic_attack."""
        screen, app = _make_screen()
        p1 = _combatant("p1", ability_ids=["basic_attack"])  # no heavy_strike
        e1 = _combatant("e1", is_player=False)
        action = CombatAction(actor_id="p1", ability_id="heavy_strike", target_ids=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.ability_id == "basic_attack"

    def test_cooldown_zero_not_triggered(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", cooldowns={"heavy_strike": 0})
        e1 = _combatant("e1", is_player=False)
        action = CombatAction(actor_id="p1", ability_id="heavy_strike", target_ids=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.ability_id == "heavy_strike"

    def test_duplicate_item_in_stash(self) -> None:
        """Two copies in stash, one claimed — second still available."""
        screen, app = _make_screen(
            stash=["minor_potion", "minor_potion"],
            claimed=["minor_potion"],
        )
        p1 = _combatant("p1")
        action = CombatAction(
            actor_id="p1", ability_id="use_item",
            item_id="minor_potion", target_ids=["p1"],
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.item_id == "minor_potion"

    def test_item_retargets_dead_ally(self) -> None:
        screen, app = _make_screen(stash=["minor_potion"])
        p1 = _combatant("p1")
        p2 = _combatant("p2", alive=False)
        p3 = _combatant("p3")
        action = CombatAction(
            actor_id="p1", ability_id="use_item",
            item_id="minor_potion", target_ids=["p2"],
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_action(
                action, "p1", p1,
                _combat([p1, p2, p3], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1", "p3"],
            )
        assert result.target_ids == ["p1"]


# ---------------------------------------------------------------------------
# _validate_auto_decision (needs mocked app via _validate_auto_action)
# ---------------------------------------------------------------------------

class TestValidateAutoDecision:

    def test_cheat_with_no_ap_falls_back_to_normal(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", ap=0)
        dec = _decision("p1", cs=CheatSurviveChoice.CHEAT, cheat_actions=2, targets=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.cheat_survive == CheatSurviveChoice.NORMAL
        assert result.cheat_actions == 0

    def test_cheat_ap_capped_to_available(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", ap=1)
        dec = _decision("p1", cs=CheatSurviveChoice.CHEAT, cheat_actions=3, targets=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.cheat_survive == CheatSurviveChoice.CHEAT
        assert result.cheat_actions == 1

    def test_survive_while_taunted_falls_back(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", taunted_by=["e1"])
        dec = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.SURVIVE,
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.cheat_survive == CheatSurviveChoice.NORMAL
        assert result.primary_action is not None

    def test_survive_not_taunted_stays(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        dec = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.SURVIVE,
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.cheat_survive == CheatSurviveChoice.SURVIVE
        assert result.primary_action is None

    def test_cooldown_ability_replaced_in_primary(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", cooldowns={"heavy_strike": 1})
        dec = _decision("p1", ability="heavy_strike", targets=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.primary_action.ability_id == "basic_attack"

    def test_cheat_extras_trimmed_to_available_ap(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", ap=1)
        extras = [
            CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
        ]
        dec = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.CHEAT,
            cheat_actions=3,
            primary_action=CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            cheat_extra_actions=extras,
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [_combatant("e1", is_player=False)]),
                ["e1"], ["p1"],
            )
        assert result.cheat_actions == 1
        assert len(result.cheat_extra_actions) == 1

    def test_bonus_actions_recalculated_from_current_spd(self) -> None:
        screen, app = _make_screen()
        # Very fast player vs very slow enemy → SPD bonus actions
        p1 = _combatant("p1", spd=100)
        e1 = _combatant("e1", is_player=False, spd=1)
        # Recorded decision had no bonus actions
        dec = _decision("p1", targets=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        # Should have padded bonus actions
        assert len(result.bonus_actions) > 0
        for ba in result.bonus_actions:
            assert ba.ability_id == "basic_attack"

    def test_bonus_actions_zeroed_when_speed_insufficient(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", spd=10)
        e1 = _combatant("e1", is_player=False, spd=10)
        bonus = [CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"])]
        dec = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            bonus_actions=bonus,
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.bonus_actions == []

    def test_cheat_with_dead_target_in_extras(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", ap=2)
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        extras = [
            CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
        ]
        dec = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.CHEAT,
            cheat_actions=2,
            primary_action=CombatAction(actor_id="p1", ability_id="basic_attack", target_ids=["e1"]),
            cheat_extra_actions=extras,
        )
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [e1, e2]), ["e2"], ["p1"],
            )
        for extra in result.cheat_extra_actions:
            assert extra.target_ids == ["e2"]


# ---------------------------------------------------------------------------
# _build_auto_decisions (needs mocked app)
# ---------------------------------------------------------------------------

class TestBuildAutoDecisions:

    def test_all_players_in_record(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        p2 = _combatant("p2")
        e1 = _combatant("e1", is_player=False)
        combat = _combat([p1, p2], [e1])
        rnd = RoundRecord(
            round_number=1,
            player_decisions={
                "p1": _decision("p1", targets=["e1"]),
                "p2": _decision("p2", targets=["e1"]),
            },
        )
        with _patch_app(screen, app):
            decisions = screen._build_auto_decisions(rnd, combat)
        assert "p1" in decisions
        assert "p2" in decisions

    def test_missing_player_gets_fallback(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        p2 = _combatant("p2")
        e1 = _combatant("e1", is_player=False)
        combat = _combat([p1, p2], [e1])
        rnd = RoundRecord(
            round_number=1,
            player_decisions={"p1": _decision("p1", targets=["e1"])},
        )
        with _patch_app(screen, app):
            decisions = screen._build_auto_decisions(rnd, combat)
        assert decisions["p2"].cheat_survive == CheatSurviveChoice.NORMAL
        assert decisions["p2"].primary_action.ability_id == "basic_attack"

    def test_no_living_players_empty(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1", alive=False)
        e1 = _combatant("e1", is_player=False)
        combat = _combat([p1], [e1])
        rnd = RoundRecord(round_number=1)
        with _patch_app(screen, app):
            decisions = screen._build_auto_decisions(rnd, combat)
        assert decisions == {}

    def test_dead_enemy_retargets(self) -> None:
        screen, app = _make_screen()
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        combat = _combat([p1], [e1, e2])
        rnd = RoundRecord(
            round_number=1,
            player_decisions={"p1": _decision("p1", targets=["e1"])},
        )
        with _patch_app(screen, app):
            decisions = screen._build_auto_decisions(rnd, combat)
        assert decisions["p1"].primary_action.target_ids == ["e2"]

    def test_item_claim_shared_across_players(self) -> None:
        """Two players can't both claim the same single item from stash."""
        screen, app = _make_screen(stash=["minor_potion"])
        p1 = _combatant("p1")
        p2 = _combatant("p2")
        e1 = _combatant("e1", is_player=False)
        combat = _combat([p1, p2], [e1])

        d1 = PlayerTurnDecision(
            combatant_id="p1", cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=CombatAction(
                actor_id="p1", ability_id="use_item",
                item_id="minor_potion", target_ids=["p1"],
            ),
        )
        d2 = PlayerTurnDecision(
            combatant_id="p2", cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=CombatAction(
                actor_id="p2", ability_id="use_item",
                item_id="minor_potion", target_ids=["p2"],
            ),
        )
        rnd = RoundRecord(
            round_number=1,
            player_decisions={"p1": d1, "p2": d2},
        )
        with _patch_app(screen, app):
            decisions = screen._build_auto_decisions(rnd, combat)

        item_users = [
            pid for pid, d in decisions.items()
            if d.primary_action and d.primary_action.item_id == "minor_potion"
        ]
        basic_users = [
            pid for pid, d in decisions.items()
            if d.primary_action and d.primary_action.ability_id == "basic_attack"
            and d.primary_action.item_id is None
        ]
        assert len(item_users) == 1
        assert len(basic_users) == 1


# ---------------------------------------------------------------------------
# Integration with real game data
# ---------------------------------------------------------------------------

class TestWithRealGameData:

    def test_retarget_basic_attack(self, game_data: GameData) -> None:
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False, alive=False)
        e2 = _combatant("e2", is_player=False)
        combat = _combat([p1], [e1, e2])
        result = CombatScreen._retarget_for_ability(
            game_data.abilities["basic_attack"], ["e1"], "p1",
            combat, ["e2"], ["p1"],
        )
        assert result == ["e2"]

    def test_retarget_self_ability(self, game_data: GameData) -> None:
        self_abilities = [
            (aid, a) for aid, a in game_data.abilities.items()
            if a.target == TargetType.SELF and a.category != AbilityCategory.PASSIVE
        ]
        if not self_abilities:
            pytest.skip("No SELF-targeting active abilities in game data")

        aid, ability = self_abilities[0]
        p1 = _combatant("p1")
        combat = _combat([p1], [_combatant("e1", is_player=False)])
        result = CombatScreen._retarget_for_ability(
            ability, ["e1"], "p1", combat, ["e1"], ["p1"],
        )
        assert result == ["p1"]

    def test_retarget_aoe_ability(self, game_data: GameData) -> None:
        aoe_abilities = [
            (aid, a) for aid, a in game_data.abilities.items()
            if a.target == TargetType.ALL_ENEMIES and a.category != AbilityCategory.PASSIVE
        ]
        if not aoe_abilities:
            pytest.skip("No ALL_ENEMIES active abilities in game data")

        aid, ability = aoe_abilities[0]
        p1 = _combatant("p1")
        e1 = _combatant("e1", is_player=False)
        e2 = _combatant("e2", is_player=False)
        e3 = _combatant("e3", is_player=False, alive=False)
        combat = _combat([p1], [e1, e2, e3])
        result = CombatScreen._retarget_for_ability(
            ability, ["e1"], "p1", combat, ["e1", "e2"], ["p1"],
        )
        assert set(result) == {"e1", "e2"}

    def test_validate_decision_real_abilities(self, game_data: GameData) -> None:
        screen, app = _make_screen(abilities=game_data.abilities)
        p1 = _combatant("p1", cooldowns={"heavy_strike": 1})
        e1 = _combatant("e1", is_player=False)
        dec = _decision("p1", ability="heavy_strike", targets=["e1"])
        with _patch_app(screen, app):
            result = screen._validate_auto_decision(
                dec, p1, _combat([p1], [e1]), ["e1"], ["p1"],
            )
        assert result.primary_action.ability_id == "basic_attack"
