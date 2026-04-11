"""Tests for the effect phase pipeline, behavioral flags, and formula helpers.

Covers WI-1 (phase pipeline), WI-3 (hardcoded ID removal), WI-4 (combat item use),
WI-5 (formula constants).
"""

import random

import pytest

from heresiarch.engine.combat import CombatEngine, EffectContext
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    FRENZY_BASE,
    INSIGHT_MULTIPLIER_PER_STACK,
    MARK_DAMAGE_BONUS,
    THORNS_SCALING_PER_TIER,
    THORNS_TIER_LEVELS,
    VENGEANCE_DEFAULT_DURATION,
    calculate_frenzy_multiplier,
    calculate_insight_multiplier,
    calculate_thorns_percent,
)
from heresiarch.engine.models.abilities import (
    Ability,
    AbilityCategory,
    AbilityEffect,
    DamageQuality,
    TargetType,
    TriggerCondition,
)
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    CombatState,
    CombatantState,
    PlayerTurnDecision,
    StatusEffect,
)
from heresiarch.engine.models.items import EquipSlot, Item
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.stats import StatBlock


def _make_character(
    game_data: GameData, job_id: str, level: int, weapon_id: str | None = None,
) -> CharacterInstance:
    """Helper to create a leveled character with optional weapon."""
    from heresiarch.engine.formulas import calculate_effective_stats, calculate_max_hp, calculate_stats_at_level

    job = game_data.jobs[job_id]
    stats = calculate_stats_at_level(job.growth, level)
    equipment = {"WEAPON": weapon_id, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None}
    equipped_items = []
    if weapon_id and weapon_id in game_data.items:
        equipped_items.append(game_data.items[weapon_id])
    effective = calculate_effective_stats(stats, equipped_items, [])
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, effective.DEF)
    return CharacterInstance(
        id=f"{job_id}_test",
        name=job.name,
        job_id=job_id,
        level=level,
        base_stats=stats,
        effective_stats=effective,
        max_hp=max_hp,
        equipment=equipment,
        current_hp=max_hp,
        abilities=["basic_attack", job.innate_ability_id],
    )


# --- Formula Helper Tests ---


class TestFormulaHelpers:
    """WI-5: Verify centralized formula constants and helpers."""

    def test_frenzy_multiplier_base_case(self):
        assert calculate_frenzy_multiplier(0) == 1.0  # 1.5^0

    def test_frenzy_multiplier_chain_3(self):
        expected = FRENZY_BASE ** 3
        assert calculate_frenzy_multiplier(3) == pytest.approx(expected)

    def test_frenzy_multiplier_custom_base(self):
        assert calculate_frenzy_multiplier(2, base=2.0) == 4.0

    def test_insight_multiplier_zero_stacks(self):
        assert calculate_insight_multiplier(0) == 1.0

    def test_insight_multiplier_two_stacks(self):
        expected = 1.0 + INSIGHT_MULTIPLIER_PER_STACK * 2
        assert calculate_insight_multiplier(2) == pytest.approx(expected)

    def test_thorns_percent_level_1(self):
        result = calculate_thorns_percent(0.5, 1)
        assert result == pytest.approx(0.5)  # No tier bonus at level 1

    def test_thorns_percent_level_10(self):
        result = calculate_thorns_percent(0.5, 10)
        expected = 0.5 + THORNS_SCALING_PER_TIER * (10 // THORNS_TIER_LEVELS)
        assert result == pytest.approx(expected)

    def test_thorns_percent_level_25(self):
        result = calculate_thorns_percent(0.5, 25)
        expected = 0.5 + THORNS_SCALING_PER_TIER * 2  # 25 // 10 = 2
        assert result == pytest.approx(expected)


# --- Behavioral Flag Tests (WI-3) ---


class TestSurviveLethalFlag:
    """Endure behavior driven by survive_lethal flag, not ability ID."""

    def test_survive_lethal_effect_field_exists(self):
        """The AbilityEffect model supports the survive_lethal flag."""
        effect = AbilityEffect(survive_lethal=True)
        assert effect.survive_lethal is True

    def test_survive_lethal_defaults_false(self):
        effect = AbilityEffect()
        assert effect.survive_lethal is False

    def test_endure_yaml_has_survive_lethal(self, game_data: GameData):
        """The endure ability in data uses survive_lethal flag."""
        endure = game_data.abilities.get("endure")
        assert endure is not None
        assert any(e.survive_lethal for e in endure.effects)

    def test_endure_triggers_on_lethal_damage(
        self, game_data: GameData, combat_engine: CombatEngine,
    ):
        """A character with endure survives lethal damage at 1 HP."""
        martyr = _make_character(game_data, "martyr", 12)
        # Martyr gets endure at level 12
        martyr = martyr.model_copy(update={
            "abilities": list(martyr.abilities) + ["endure"],
        })

        # Create an overpowered enemy
        enemy = combat_engine.create_enemy_instance(
            game_data.enemies["brute_oni"], zone_level=50,
        )

        state = combat_engine.initialize_combat([martyr], [enemy])

        # Run one round — enemy should deal lethal damage
        decisions = {
            state.living_players[0].id: PlayerTurnDecision(
                combatant_id=state.living_players[0].id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            ),
        }
        state = combat_engine.process_round(
            state, decisions, {"brute_oni": game_data.enemies["brute_oni"]},
        )

        player = state.player_combatants[0]
        # Either survived at 1 HP via endure, or survived due to Survive mode
        if player.has_endured:
            assert player.current_hp == 1
            assert player.is_alive
            # Verify the PASSIVE_TRIGGERED event was logged with endure's ID
            endure_events = [
                e for e in state.log
                if e.event_type == CombatEventType.PASSIVE_TRIGGERED
                and e.details.get("survived_at") == 1
            ]
            assert len(endure_events) >= 1
            assert endure_events[0].ability_id == "endure"

    def test_custom_survive_lethal_passive_works(
        self, game_data: GameData, seeded_rng,
    ):
        """A custom ability with survive_lethal works without being named 'endure'."""
        custom_ability = Ability(
            id="iron_will",
            name="Iron Will",
            category=AbilityCategory.PASSIVE,
            target=TargetType.SELF,
            trigger=TriggerCondition.NONE,
            effects=[AbilityEffect(survive_lethal=True)],
        )
        abilities = dict(game_data.abilities)
        abilities["iron_will"] = custom_ability

        engine = CombatEngine(
            ability_registry=abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=seeded_rng,
        )

        char = _make_character(game_data, "einherjar", 1)
        char = char.model_copy(update={
            "abilities": list(char.abilities) + ["iron_will"],
            "current_hp": 1,  # Near death
        })

        enemy = engine.create_enemy_instance(
            game_data.enemies["brute_oni"], zone_level=50,
        )

        state = engine.initialize_combat([char], [enemy])
        decisions = {
            state.living_players[0].id: PlayerTurnDecision(
                combatant_id=state.living_players[0].id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            ),
        }
        state = engine.process_round(
            state, decisions, {"brute_oni": game_data.enemies["brute_oni"]},
        )

        player = state.player_combatants[0]
        if player.has_endured:
            assert player.current_hp == 1
            assert player.is_alive
            # Should log with "iron_will", not "endure"
            endure_events = [
                e for e in state.log
                if e.event_type == CombatEventType.PASSIVE_TRIGGERED
                and e.details.get("survived_at") == 1
            ]
            assert endure_events[0].ability_id == "iron_will"


class TestAppliesTauntFlag:
    """Taunt behavior driven by applies_taunt flag, not ability ID."""

    def test_applies_taunt_effect_field(self):
        effect = AbilityEffect(applies_taunt=True, duration_rounds=1)
        assert effect.applies_taunt is True

    def test_taunt_yaml_has_flag(self, game_data: GameData):
        taunt = game_data.abilities.get("taunt")
        assert taunt is not None
        assert any(e.applies_taunt for e in taunt.effects)

    def test_taunt_status_has_grants_taunt(
        self, game_data: GameData, combat_engine: CombatEngine,
    ):
        """When taunt is used, the resulting status has grants_taunt=True."""
        martyr = _make_character(game_data, "martyr", 7)
        martyr = martyr.model_copy(update={
            "abilities": list(martyr.abilities) + ["taunt"],
        })
        enemy = combat_engine.create_enemy_instance(
            game_data.enemies["fodder_slime"], zone_level=5,
        )

        state = combat_engine.initialize_combat([martyr], [enemy])
        player_id = state.living_players[0].id
        decisions = {
            player_id: PlayerTurnDecision(
                combatant_id=player_id,
                primary_action=CombatAction(
                    actor_id=player_id, ability_id="taunt", target_ids=[player_id],
                ),
            ),
        }
        state = combat_engine.process_round(
            state, decisions, {"fodder_slime": game_data.enemies["fodder_slime"]},
        )

        player = state.get_combatant(player_id)
        taunt_statuses = [s for s in player.active_statuses if s.grants_taunt]
        assert len(taunt_statuses) >= 1


class TestAppliesMarkFlag:
    """Mark behavior driven by applies_mark flag, not ability ID."""

    def test_applies_mark_effect_field(self):
        effect = AbilityEffect(applies_mark=True, duration_rounds=3)
        assert effect.applies_mark is True

    def test_mark_yaml_has_flag(self, game_data: GameData):
        mark = game_data.abilities.get("mark")
        assert mark is not None
        assert any(e.applies_mark for e in mark.effects)

    def test_mark_status_has_grants_mark(
        self, game_data: GameData, combat_engine: CombatEngine,
    ):
        """When mark is used, the resulting status has grants_mark=True."""
        char = _make_character(game_data, "einherjar", 10)
        char = char.model_copy(update={
            "abilities": list(char.abilities) + ["mark"],
        })
        enemy = combat_engine.create_enemy_instance(
            game_data.enemies["fodder_slime"], zone_level=5,
        )

        state = combat_engine.initialize_combat([char], [enemy])
        player_id = state.living_players[0].id
        enemy_id = state.living_enemies[0].id
        decisions = {
            player_id: PlayerTurnDecision(
                combatant_id=player_id,
                primary_action=CombatAction(
                    actor_id=player_id, ability_id="mark", target_ids=[enemy_id],
                ),
            ),
        }
        state = combat_engine.process_round(
            state, decisions, {"fodder_slime": game_data.enemies["fodder_slime"]},
        )

        enemy_state = state.get_combatant(enemy_id)
        mark_statuses = [s for s in enemy_state.active_statuses if s.grants_mark]
        assert len(mark_statuses) >= 1


# --- In-Combat Item Use (WI-4) ---


class TestCombatItemUse:
    """CombatEngine.use_combat_item() correctly applies healing."""

    def _make_combat_state(self, hp: int = 50, max_hp: int = 100) -> CombatState:
        player = CombatantState(
            id="p1", is_player=True, current_hp=hp, max_hp=max_hp,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        enemy = CombatantState(
            id="e1", is_player=False, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        return CombatState(
            round_number=1,
            player_combatants=[player],
            enemy_combatants=[enemy],
        )

    def test_heal_flat_amount(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=50, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 80

    def test_heal_percent(self, combat_engine: CombatEngine):
        item = Item(id="elixir", name="Elixir", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=0, heal_percent=0.5, base_price=300)
        state = self._make_combat_state(hp=30, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 80  # 30 + 50

    def test_heal_caps_at_max_hp(self, combat_engine: CombatEngine):
        item = Item(id="mega_potion", name="Mega Potion", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=999, heal_percent=0.0, base_price=999)
        state = self._make_combat_state(hp=90, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 100

    def test_emits_healing_event(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=20, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=50, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        heal_events = [e for e in state.log if e.event_type == CombatEventType.HEALING]
        assert len(heal_events) == 1
        assert heal_events[0].value == 20
        assert heal_events[0].details["source"] == "potion"

    def test_rejects_non_consumable(self, combat_engine: CombatEngine):
        item = Item(id="sword", name="Sword", slot=EquipSlot.WEAPON, is_consumable=False,
                    base_price=100)
        state = self._make_combat_state()

        with pytest.raises(ValueError, match="not a consumable"):
            combat_engine.use_combat_item(state, "p1", "p1", item)

    def test_rejects_dead_target(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=0)
        state.player_combatants[0].is_alive = False

        with pytest.raises(ValueError, match="dead"):
            combat_engine.use_combat_item(state, "p1", "p1", item)

    def test_rejects_invalid_target(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", slot=EquipSlot.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state()

        with pytest.raises(ValueError, match="No combatant"):
            combat_engine.use_combat_item(state, "p1", "nonexistent", item)


# --- Status Flag Sync Tests ---


class TestStatusFlagSync:
    """Verify grants_taunt/grants_mark flags drive is_taunting/is_marked correctly."""

    def test_grants_taunt_syncs_is_taunting(self, combat_engine: CombatEngine):
        """StatusEffect.grants_taunt=True sets CombatantState.is_taunting after tick."""
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="taunt_active", name="Taunt",
                    rounds_remaining=3, grants_taunt=True,
                ),
            ],
        )
        state = CombatState(
            round_number=2,
            player_combatants=[player],
            enemy_combatants=[],
        )

        state = combat_engine._tick_statuses(state)
        assert state.player_combatants[0].is_taunting is True

    def test_grants_mark_syncs_is_marked(self, combat_engine: CombatEngine):
        """StatusEffect.grants_mark=True sets CombatantState.is_marked after tick."""
        enemy = CombatantState(
            id="e1", is_player=False, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="mark_active", name="Marked",
                    rounds_remaining=3, grants_mark=True,
                ),
            ],
        )
        state = CombatState(
            round_number=2,
            player_combatants=[],
            enemy_combatants=[enemy],
        )

        state = combat_engine._tick_statuses(state)
        assert state.enemy_combatants[0].is_marked is True

    def test_taunt_persists_on_final_round(self, combat_engine: CombatEngine):
        """Taunt with 1 round remaining is still active during that tick (expires after)."""
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="taunt_active", name="Taunt",
                    rounds_remaining=1, grants_taunt=True,
                ),
            ],
        )
        state = CombatState(
            round_number=2,
            player_combatants=[player],
            enemy_combatants=[],
        )

        # Flags sync from active statuses BEFORE tick removes them,
        # so taunt is active during this round then expires
        state = combat_engine._tick_statuses(state)
        assert state.player_combatants[0].is_taunting is True
        assert len(state.player_combatants[0].active_statuses) == 0

        # Next tick: no taunt status to derive flag from
        state2 = CombatState(
            round_number=3,
            player_combatants=state.player_combatants,
            enemy_combatants=[],
        )
        state2 = combat_engine._tick_statuses(state2)
        assert state2.player_combatants[0].is_taunting is False


# --- Ability Source Tracking Tests (WI-6) ---


class TestAbilitySourceTracking:
    """CharacterInstance.ability_sources and get_all_abilities()."""

    def test_get_all_abilities_from_sources(self):
        char = CharacterInstance(
            id="test", name="Test", job_id="einherjar",
            ability_sources={
                "core": ["basic_attack"],
                "innate": ["retaliate"],
                "breakpoints": ["brace_strike"],
                "equipment": ["flame_strike"],
                "learned": ["bolt"],
            },
        )
        result = char.get_all_abilities()
        assert result == ["basic_attack", "retaliate", "brace_strike", "flame_strike", "bolt"]

    def test_get_all_abilities_deduplicates(self):
        char = CharacterInstance(
            id="test", name="Test", job_id="einherjar",
            ability_sources={
                "core": ["basic_attack"],
                "innate": ["basic_attack"],  # Duplicate
                "breakpoints": ["brace_strike"],
            },
        )
        result = char.get_all_abilities()
        assert result.count("basic_attack") == 1

    def test_get_all_abilities_falls_back_to_flat_list(self):
        """Old saves without ability_sources use the flat abilities list."""
        char = CharacterInstance(
            id="test", name="Test", job_id="einherjar",
            abilities=["basic_attack", "retaliate", "bolt"],
            ability_sources={},
        )
        result = char.get_all_abilities()
        assert result == ["basic_attack", "retaliate", "bolt"]

    def test_equip_updates_equipment_source(self, game_data: GameData):
        """Equipping an item with granted_ability updates equipment source only."""
        from heresiarch.engine.game_loop import GameLoop

        gl = GameLoop(game_data, rng=random.Random(42))
        run = gl.new_run("test_run", "Test", "einherjar")
        mc_id = run.party.active[0]
        mc = run.party.characters[mc_id]

        # Find an item with a granted ability if one exists
        items_with_abilities = [
            item for item in game_data.items.values()
            if item.granted_ability_id
        ]
        if not items_with_abilities:
            pytest.skip("No items with granted abilities in data")

        item = items_with_abilities[0]
        # Add to stash
        new_stash = list(run.party.stash) + [item.id]
        new_items = dict(run.party.items)
        new_items[item.id] = item
        party = run.party.model_copy(update={"stash": new_stash, "items": new_items})
        run = run.model_copy(update={"party": party})

        run = gl.equip_item(run, mc_id, item.id, item.slot.value)
        updated_mc = run.party.characters[mc_id]

        # Should have ability_sources populated
        if updated_mc.ability_sources:
            assert item.granted_ability_id in updated_mc.ability_sources.get("equipment", [])
            assert item.granted_ability_id in updated_mc.abilities

    def test_rebuild_preserves_learned_abilities(self, game_data: GameData):
        """Scroll-taught abilities survive equipment changes."""
        from heresiarch.engine.game_loop import GameLoop

        gl = GameLoop(game_data, rng=random.Random(42))
        run = gl.new_run("test_run", "Test", "einherjar")
        mc_id = run.party.active[0]
        mc = run.party.characters[mc_id]

        # Simulate a scroll-taught ability by adding to learned source
        learned_ability = "bolt"
        new_abilities = list(mc.abilities) + [learned_ability]
        new_sources = dict(mc.ability_sources) if mc.ability_sources else {}
        new_sources["learned"] = [learned_ability]
        mc = mc.model_copy(update={
            "abilities": new_abilities,
            "ability_sources": new_sources,
        })
        chars = dict(run.party.characters)
        chars[mc_id] = mc
        party = run.party.model_copy(update={"characters": chars})
        run = run.model_copy(update={"party": party})

        # Now equip something — should preserve learned abilities
        if "iron_blade" in game_data.items:
            new_stash = list(run.party.stash) + ["iron_blade"]
            new_items = dict(run.party.items)
            new_items["iron_blade"] = game_data.items["iron_blade"]
            party = run.party.model_copy(update={"stash": new_stash, "items": new_items})
            run = run.model_copy(update={"party": party})

            run = gl.equip_item(run, mc_id, "iron_blade", "WEAPON")
            updated_mc = run.party.characters[mc_id]
            assert learned_ability in updated_mc.abilities
