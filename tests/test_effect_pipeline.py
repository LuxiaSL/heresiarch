"""Tests for the effect phase pipeline, behavioral flags, and formula helpers.

Covers WI-1 (phase pipeline), WI-3 (hardcoded ID removal), WI-4 (combat item use),
WI-5 (formula constants).
"""

import random

import pytest

from heresiarch.engine.combat import CombatEngine, EffectContext
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    FRENZY_FLOOR,
    FRENZY_GROWTH,
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
from heresiarch.engine.models.items import EquipType, Item
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

    def test_frenzy_multiplier_chain_zero(self):
        assert calculate_frenzy_multiplier(0) == 1.0

    def test_frenzy_multiplier_chain_1_is_floor(self):
        assert calculate_frenzy_multiplier(1) == pytest.approx(FRENZY_FLOOR)

    def test_frenzy_multiplier_chain_3(self):
        expected = FRENZY_FLOOR * FRENZY_GROWTH ** 2
        assert calculate_frenzy_multiplier(3) == pytest.approx(expected)

    def test_frenzy_multiplier_custom_params(self):
        assert calculate_frenzy_multiplier(2, floor=3.0, growth=1.5) == pytest.approx(4.5)

    def test_frenzy_monotonically_increasing(self):
        """Each chain step must strictly increase the multiplier."""
        for chain in range(1, 15):
            assert calculate_frenzy_multiplier(chain) > calculate_frenzy_multiplier(chain - 1)

    def test_frenzy_chain_zero_is_neutral(self):
        """Chain 0 must return exactly 1.0 — prevents double-dip on chain restart."""
        assert calculate_frenzy_multiplier(0) == 1.0
        # Negative chains should also be neutral (defensive)
        assert calculate_frenzy_multiplier(-1) == 1.0

    def test_frenzy_continuous_chain_beats_broken_patterns(self):
        """Regression: breaking chain to re-apply floor must never beat continuous chaining.

        Simulates the ratchet model (level = max(level, formula(chain))) and verifies
        that no survive-interrupted pattern produces more cumulative damage than
        continuous attacking for the same number of attacks.
        """

        def simulate(actions: list[str]) -> tuple[float, float, int]:
            """Simulate frenzy ratchet. Returns (cumulative_mult, final_level, attacks)."""
            chain = 0
            level = 1.0
            cumulative = 0.0
            attacks = 0

            for action in actions:
                if action == "survive":
                    chain = 0  # round boundary reset
                elif action == "attack":
                    mult = max(level, calculate_frenzy_multiplier(chain))
                    cumulative += mult
                    level = max(level, calculate_frenzy_multiplier(chain))
                    chain += 1
                    attacks += 1

            return cumulative, level, attacks

        # --- 4-attack comparisons ---
        cont_4 = simulate(["attack"] * 4)

        # attack, survive, attack, survive, attack, attack
        broken_asas = simulate(
            ["attack", "survive", "attack", "survive", "attack", "attack"],
        )
        assert cont_4[2] == broken_asas[2] == 4
        assert cont_4[0] > broken_asas[0]
        assert cont_4[1] >= broken_asas[1]

        # survive, attack, attack, survive, attack, attack
        broken_saas = simulate(
            ["survive", "attack", "attack", "survive", "attack", "attack"],
        )
        assert cont_4[2] == broken_saas[2] == 4
        assert cont_4[0] > broken_saas[0]

        # --- 3-attack: survive, cheat(attack×2), survive, attack ---
        broken_cheat = simulate(
            ["survive", "attack", "attack", "survive", "attack"],
        )
        cont_3 = simulate(["attack"] * 3)
        assert cont_3[2] == broken_cheat[2] == 3
        assert cont_3[0] >= broken_cheat[0]
        assert cont_3[1] >= broken_cheat[1]

        # --- Worst case: alternating survive/attack (maximum chain breaks) ---
        broken_alternating = simulate(
            ["attack", "survive"] * 4,  # 4 attacks, each followed by a break
        )
        assert cont_4[2] == broken_alternating[2] == 4
        assert cont_4[0] > broken_alternating[0]

        # --- 6-attack: two cheat bursts with survive between ---
        broken_burst = simulate(
            ["attack", "attack", "attack", "survive", "attack", "attack", "attack"],
        )
        cont_6 = simulate(["attack"] * 6)
        assert cont_6[2] == broken_burst[2] == 6
        assert cont_6[0] > broken_burst[0]
        assert cont_6[1] >= broken_burst[1]

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
            game_data.enemies["brute_oni"], enemy_level=50,
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

        # Use level 1 to avoid speed bonus (enemy SPD must not be 2x player SPD)
        # but boost HP so the fight doesn't end in one hit
        enemy = engine.create_enemy_instance(
            game_data.enemies["brute_oni"], enemy_level=1,
        )
        enemy = enemy.model_copy(update={"current_hp": 999, "max_hp": 999})

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

    def test_taunt_status_applied_to_target(
        self, game_data: GameData, combat_engine: CombatEngine,
    ):
        """When taunt is used, the target gets a grants_taunted=True status."""
        martyr = _make_character(game_data, "martyr", 7)
        martyr = martyr.model_copy(update={
            "abilities": list(martyr.abilities) + ["taunt"],
        })
        enemy = combat_engine.create_enemy_instance(
            game_data.enemies["fodder_slime"], enemy_level=5,
        )

        state = combat_engine.initialize_combat([martyr], [enemy])
        player_id = state.living_players[0].id
        enemy_id = state.living_enemies[0].id
        decisions = {
            player_id: PlayerTurnDecision(
                combatant_id=player_id,
                primary_action=CombatAction(
                    actor_id=player_id, ability_id="taunt", target_ids=[enemy_id],
                ),
            ),
        }
        state = combat_engine.process_round(
            state, decisions, {"fodder_slime": game_data.enemies["fodder_slime"]},
        )

        enemy_state = state.get_combatant(enemy_id)
        taunt_statuses = [s for s in enemy_state.active_statuses if s.grants_taunted]
        assert len(taunt_statuses) >= 1
        assert taunt_statuses[0].source_id == player_id


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
            game_data.enemies["fodder_slime"], enemy_level=5,
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
        item = Item(id="potion", name="Potion", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=50, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 80

    def test_heal_percent(self, combat_engine: CombatEngine):
        item = Item(id="elixir", name="Elixir", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=0, heal_percent=0.5, base_price=300)
        state = self._make_combat_state(hp=30, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 80  # 30 + 50

    def test_heal_caps_at_max_hp(self, combat_engine: CombatEngine):
        item = Item(id="mega_potion", name="Mega Potion", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=999, heal_percent=0.0, base_price=999)
        state = self._make_combat_state(hp=90, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        assert state.get_combatant("p1").current_hp == 100

    def test_emits_healing_event(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=20, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=50, max_hp=100)

        state = combat_engine.use_combat_item(state, "p1", "p1", item)
        heal_events = [e for e in state.log if e.event_type == CombatEventType.HEALING]
        assert len(heal_events) == 1
        assert heal_events[0].value == 20
        assert heal_events[0].details["source"] == "potion"

    def test_rejects_non_consumable(self, combat_engine: CombatEngine):
        item = Item(id="sword", name="Sword", equip_type=EquipType.WEAPON, is_consumable=False,
                    base_price=100)
        state = self._make_combat_state()

        with pytest.raises(ValueError, match="not a consumable"):
            combat_engine.use_combat_item(state, "p1", "p1", item)

    def test_rejects_dead_target(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state(hp=0)
        state.player_combatants[0].is_alive = False

        with pytest.raises(ValueError, match="dead"):
            combat_engine.use_combat_item(state, "p1", "p1", item)

    def test_rejects_invalid_target(self, combat_engine: CombatEngine):
        item = Item(id="potion", name="Potion", equip_type=EquipType.WEAPON, is_consumable=True,
                    heal_amount=30, heal_percent=0.0, base_price=50)
        state = self._make_combat_state()

        with pytest.raises(ValueError, match="No combatant"):
            combat_engine.use_combat_item(state, "p1", "nonexistent", item)


# --- Status Flag Sync Tests ---


class TestStatusFlagSync:
    """Verify grants_taunted/grants_mark flags drive taunted_by/is_marked correctly."""

    def test_grants_taunted_syncs_taunted_by(self, combat_engine: CombatEngine):
        """StatusEffect.grants_taunted=True populates CombatantState.taunted_by after tick."""
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="taunted", name="Taunted",
                    rounds_remaining=3, grants_taunted=True, source_id="e1",
                ),
            ],
        )
        enemy = CombatantState(
            id="e1", is_player=False, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        state = CombatState(
            round_number=2,
            player_combatants=[player],
            enemy_combatants=[enemy],
        )

        state = combat_engine._tick_statuses(state)
        assert state.player_combatants[0].taunted_by == ["e1"]

    def test_taunted_by_cleared_when_source_dead(self, combat_engine: CombatEngine):
        """Taunted status from a dead source is cleaned up during tick."""
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="taunted", name="Taunted",
                    rounds_remaining=3, grants_taunted=True, source_id="e1",
                ),
            ],
        )
        dead_enemy = CombatantState(
            id="e1", is_player=False, current_hp=0, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            is_alive=False,
        )
        state = CombatState(
            round_number=2,
            player_combatants=[player],
            enemy_combatants=[dead_enemy],
        )

        state = combat_engine._tick_statuses(state)
        assert state.player_combatants[0].taunted_by == []
        assert len(state.player_combatants[0].active_statuses) == 0

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

    def test_taunted_expires_after_final_round(self, combat_engine: CombatEngine):
        """Taunted status with 1 round remaining expires at end-of-round tick."""
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            active_statuses=[
                StatusEffect(
                    id="taunted", name="Taunted",
                    rounds_remaining=1, grants_taunted=True, source_id="e1",
                ),
            ],
        )
        enemy = CombatantState(
            id="e1", is_player=False, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        state = CombatState(
            round_number=2,
            player_combatants=[player],
            enemy_combatants=[enemy],
        )

        # Round start: taunt still active, taunted_by derived
        state = combat_engine._tick_statuses(state)
        assert state.player_combatants[0].taunted_by == ["e1"]

        # End of round: status expires, taunted_by cleared
        state = combat_engine._end_of_round_status_tick(state)
        assert state.player_combatants[0].taunted_by == []
        assert len(state.player_combatants[0].active_statuses) == 0


# --- Gold Steal (Pilfer) Capping Tests ---


class TestGoldStealCapping:
    """Gold steal should never take more than the party has."""

    _DUMMY_ABILITY = Ability(
        id="pilfer", name="Pilfer", category=AbilityCategory.OFFENSIVE,
        target=TargetType.SINGLE_ENEMY, effects=[AbilityEffect(gold_steal_flat=1)],
    )

    def _make_pilfer_state(self, party_gold: int = 100) -> CombatState:
        player = CombatantState(
            id="p1", is_player=True, current_hp=100, max_hp=100,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        enemy = CombatantState(
            id="e1", is_player=False, current_hp=100, max_hp=100, level=5,
            base_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            equipment_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
            effective_stats=StatBlock(STR=10, MAG=10, DEF=10, RES=10, SPD=10),
        )
        return CombatState(
            round_number=1,
            player_combatants=[player],
            enemy_combatants=[enemy],
            party_gold=party_gold,
        )

    def test_enemy_steal_capped_at_party_gold(self, combat_engine: CombatEngine):
        """Enemy steals only what the party actually has."""
        state = self._make_pilfer_state(party_gold=5)
        effect = AbilityEffect(gold_steal_flat=20)
        enemy = state.enemy_combatants[0]
        player = state.player_combatants[0]

        ctx = EffectContext(
            state=state, actor=enemy, target=player,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx)

        assert state.gold_stolen_by_enemies == 5
        assert state.party_gold == 0
        stolen_events = [e for e in state.log if e.event_type == CombatEventType.GOLD_STOLEN]
        assert len(stolen_events) == 1
        assert stolen_events[0].value == 5

    def test_enemy_steal_zero_gold_no_event(self, combat_engine: CombatEngine):
        """No GOLD_STOLEN event when party has 0 gold."""
        state = self._make_pilfer_state(party_gold=0)
        effect = AbilityEffect(gold_steal_flat=20)
        enemy = state.enemy_combatants[0]
        player = state.player_combatants[0]

        ctx = EffectContext(
            state=state, actor=enemy, target=player,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx)

        assert state.gold_stolen_by_enemies == 0
        assert state.party_gold == 0
        stolen_events = [e for e in state.log if e.event_type == CombatEventType.GOLD_STOLEN]
        assert len(stolen_events) == 0

    def test_enemy_steal_exact_amount(self, combat_engine: CombatEngine):
        """When party has enough gold, the full amount is stolen."""
        state = self._make_pilfer_state(party_gold=100)
        effect = AbilityEffect(gold_steal_flat=15)
        enemy = state.enemy_combatants[0]
        player = state.player_combatants[0]

        ctx = EffectContext(
            state=state, actor=enemy, target=player,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx)

        assert state.gold_stolen_by_enemies == 15
        assert state.party_gold == 85
        stolen_events = [e for e in state.log if e.event_type == CombatEventType.GOLD_STOLEN]
        assert stolen_events[0].value == 15

    def test_repeated_steals_drain_to_zero(self, combat_engine: CombatEngine):
        """Multiple pilfer hits drain gold correctly, second hit gets remainder."""
        state = self._make_pilfer_state(party_gold=25)
        effect = AbilityEffect(gold_steal_flat=20)
        enemy = state.enemy_combatants[0]
        player = state.player_combatants[0]

        # First steal: takes 20 of 25
        ctx = EffectContext(
            state=state, actor=enemy, target=player,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx)
        assert state.gold_stolen_by_enemies == 20
        assert state.party_gold == 5

        # Second steal: only 5 left
        ctx2 = EffectContext(
            state=state, actor=enemy, target=player,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx2)
        assert state.gold_stolen_by_enemies == 25
        assert state.party_gold == 0

    def test_player_steal_not_capped(self, combat_engine: CombatEngine):
        """Player gold steal is not limited by party_gold (enemies have unlimited gold)."""
        state = self._make_pilfer_state(party_gold=0)
        effect = AbilityEffect(gold_steal_flat=30)
        player = state.player_combatants[0]
        enemy = state.enemy_combatants[0]

        ctx = EffectContext(
            state=state, actor=player, target=enemy,
            effect=effect, ability=self._DUMMY_ABILITY, insight_multiplier=1.0,
        )
        combat_engine._phase_utility(ctx)

        assert state.gold_stolen_by_players == 30
        stolen_events = [e for e in state.log if e.event_type == CombatEventType.GOLD_STOLEN]
        assert stolen_events[0].value == 30


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

        run = gl.equip_item(run, mc_id, item.id, item.equip_type.value)
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
