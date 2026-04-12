"""Tests for the agent player interface: GameSession + StateSummarizer."""

import random
from pathlib import Path

import pytest

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.agent.session import AgentError, GameSession, Phase


@pytest.fixture
def game_data() -> GameData:
    return load_all(Path("data"))


@pytest.fixture
def session(game_data: GameData) -> GameSession:
    return GameSession(game_data=game_data)


# ---------------------------------------------------------------------------
# Run setup
# ---------------------------------------------------------------------------


class TestNewRun:
    def test_starts_in_zone_select(self, session: GameSession) -> None:
        result = session.new_run("Kael", "einherjar", seed=42)
        assert session.phase == Phase.ZONE_SELECT
        assert "Kael" in result
        assert "Seed: 42" in result
        assert "AVAILABLE ZONES" in result

    def test_invalid_job_raises(self, session: GameSession) -> None:
        with pytest.raises(AgentError, match="Unknown job"):
            session.new_run("Kael", "invalid_job")

    def test_mc_created_correctly(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        run = session.run
        assert run is not None
        mc = run.party.characters[run.party.active[0]]
        assert mc.name == "Kael"
        assert mc.job_id == "einherjar"
        assert mc.level == 1
        assert mc.is_mc is True
        assert mc.current_hp == mc.max_hp  # Full heal

    def test_each_job_starts(self, game_data: GameData) -> None:
        for job_id in game_data.jobs:
            s = GameSession(game_data=game_data)
            result = s.new_run("Test", job_id, seed=1)
            assert s.phase == Phase.ZONE_SELECT
            assert "AVAILABLE ZONES" in result


# ---------------------------------------------------------------------------
# Phase enforcement
# ---------------------------------------------------------------------------


class TestPhaseEnforcement:
    def test_cannot_fight_before_entering_zone(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        with pytest.raises(AgentError, match="Cannot use 'fight'"):
            session.fight()

    def test_cannot_enter_zone_in_setup(self, session: GameSession) -> None:
        with pytest.raises(AgentError, match="Cannot use 'enter_zone'"):
            session.enter_zone("zone_01")

    def test_lookups_always_available(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        # Should work in ZONE_SELECT
        result = session.lookup_job("einherjar")
        assert "Einherjar" in result

    def test_lookup_in_setup(self, session: GameSession) -> None:
        # lookups work before starting a run
        result = session.lookup_formula("damage")
        assert "Physical Damage" in result


# ---------------------------------------------------------------------------
# Zone navigation
# ---------------------------------------------------------------------------


class TestZoneNavigation:
    def test_enter_and_leave_zone(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        result = session.enter_zone("zone_01")
        assert session.phase == Phase.IN_ZONE
        assert "Shrine Entrance" in result

        result = session.leave_zone()
        assert session.phase == Phase.ZONE_SELECT
        assert "AVAILABLE ZONES" in result

    def test_enter_invalid_zone(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        with pytest.raises(AgentError, match="Unknown zone"):
            session.enter_zone("nonexistent")

    def test_zone_status(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        session.enter_zone("zone_01")
        result = session.get_zone_status()
        assert "Shrine Entrance" in result
        assert "encounters" in result.lower()


# ---------------------------------------------------------------------------
# Combat flow
# ---------------------------------------------------------------------------


class TestCombatFlow:
    def _start_combat(self, session: GameSession) -> str:
        session.new_run("Kael", "einherjar", seed=42)
        session.enter_zone("zone_01")
        return session.fight()

    def test_fight_starts_combat(self, session: GameSession) -> None:
        result = self._start_combat(session)
        assert session.phase == Phase.COMBAT
        assert "COMBAT" in result
        assert "YOUR PARTY" in result
        assert "ENEMIES" in result
        assert "TURN ORDER" in result

    def test_submit_basic_decisions(self, session: GameSession) -> None:
        self._start_combat(session)

        # Get the MC's combatant ID
        assert session._combat_state is not None
        player = session._combat_state.player_combatants[0]
        enemy = session._combat_state.enemy_combatants[0]

        decisions = {
            player.id: {
                "mode": "normal",
                "action": "basic_attack",
                "target": enemy.id,
            }
        }
        result = session.submit_decisions(decisions)
        # Should either continue combat or end it
        assert "COMBAT" in result or "VICTORY" in result or "DEFEAT" in result

    def test_invalid_ability_rejected(self, session: GameSession) -> None:
        self._start_combat(session)
        player = session._combat_state.player_combatants[0]
        enemy = session._combat_state.enemy_combatants[0]

        decisions = {
            player.id: {
                "mode": "normal",
                "action": "nonexistent_ability",
                "target": enemy.id,
            }
        }
        with pytest.raises(AgentError, match="doesn't know ability"):
            session.submit_decisions(decisions)

    def test_missing_decision_rejected(self, session: GameSession) -> None:
        self._start_combat(session)
        # Submit empty decisions
        with pytest.raises(AgentError, match="Missing decisions"):
            session.submit_decisions({})

    def test_full_combat_to_victory(self, session: GameSession) -> None:
        """Play through a full combat encounter with basic attacks."""
        self._start_combat(session)

        # Fight until combat ends (max 50 rounds as safety)
        for _ in range(50):
            if session.phase != Phase.COMBAT:
                break

            combat = session._combat_state
            assert combat is not None
            living_players = [c for c in combat.player_combatants if c.is_alive]
            living_enemies = [c for c in combat.enemy_combatants if c.is_alive]

            if not living_enemies:
                break

            decisions = {}
            for player in living_players:
                decisions[player.id] = {
                    "mode": "normal",
                    "action": "basic_attack",
                    "target": living_enemies[0].id,
                }
            session.submit_decisions(decisions)

        # Should be post-combat or dead
        assert session.phase in (Phase.POST_COMBAT, Phase.DEAD)


# ---------------------------------------------------------------------------
# Loot flow
# ---------------------------------------------------------------------------


class TestLootFlow:
    def _win_first_fight(self, session: GameSession) -> None:
        """Helper: win zone_01 encounter 1."""
        session.new_run("Kael", "einherjar", seed=42)
        session.enter_zone("zone_01")
        session.fight()

        for _ in range(50):
            if session.phase != Phase.COMBAT:
                break
            combat = session._combat_state
            assert combat is not None
            living_players = [c for c in combat.player_combatants if c.is_alive]
            living_enemies = [c for c in combat.enemy_combatants if c.is_alive]
            if not living_enemies:
                break
            decisions = {}
            for p in living_players:
                decisions[p.id] = {
                    "mode": "normal",
                    "action": "basic_attack",
                    "target": living_enemies[0].id,
                }
            session.submit_decisions(decisions)

    def test_pick_loot_advances_to_zone(self, session: GameSession) -> None:
        self._win_first_fight(session)
        if session.phase == Phase.POST_COMBAT:
            result = session.pick_loot([])  # Take nothing
            # Should go to IN_ZONE or RECRUITING
            assert session.phase in (Phase.IN_ZONE, Phase.RECRUITING)

    def test_pick_invalid_loot(self, session: GameSession) -> None:
        self._win_first_fight(session)
        if session.phase == Phase.POST_COMBAT:
            with pytest.raises(AgentError, match="not in the loot drops"):
                session.pick_loot(["nonexistent_item"])


# ---------------------------------------------------------------------------
# Party management
# ---------------------------------------------------------------------------


class TestPartyManagement:
    def test_party_status(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        result = session.party_status()
        assert "Kael" in result
        assert "Einherjar" in result
        assert "STR:" in result

    def test_equip_unequip(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)

        # Give gold and mark zone_01 cleared so town shop has gear
        run = session.run
        assert run is not None
        zones_done = list(run.zones_completed)
        if "zone_01" not in zones_done:
            zones_done.append("zone_01")
        new_party = run.party.model_copy(update={"money": 1000})
        session.run = run.model_copy(
            update={"party": new_party, "zones_completed": zones_done}
        )

        # Buy from town shop
        session.enter_town("shinto_town")
        session.shop_buy("iron_blade")
        session.leave_town()

        # Equip it (in zone select phase)
        mc_id = session.run.party.active[0]
        result = session.equip(mc_id, "iron_blade", "WEAPON")
        assert "Equipped" in result
        assert "iron_blade" in result

        # Unequip it
        result = session.unequip(mc_id, "WEAPON")
        assert "Unequipped" in result

    def test_equip_invalid_item(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        mc_id = session.run.party.active[0]
        with pytest.raises(AgentError, match="not in stash"):
            session.equip(mc_id, "nonexistent", "WEAPON")


# ---------------------------------------------------------------------------
# Shopping
# ---------------------------------------------------------------------------


class TestShopping:
    @staticmethod
    def _mark_zone_cleared(session: GameSession, zone_id: str = "zone_01") -> None:
        """Mark a zone as cleared so the town shop unlocks its tier."""
        run = session.run
        assert run is not None
        zones_done = list(run.zones_completed)
        if zone_id not in zones_done:
            zones_done.append(zone_id)
        session.run = run.model_copy(update={"zones_completed": zones_done})

    def test_shop_browse(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        self._mark_zone_cleared(session)
        session.enter_town("shinto_town")
        result = session.shop_browse()
        assert "SHOP" in result
        assert "FOR SALE" in result

    def test_shop_buy_insufficient_funds(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        self._mark_zone_cleared(session)
        session.enter_town("shinto_town")
        with pytest.raises(AgentError, match="Insufficient funds"):
            session.shop_buy("iron_blade")

    def test_shop_buy_sell(self, session: GameSession) -> None:
        session.new_run("Kael", "einherjar", seed=42)
        self._mark_zone_cleared(session)
        session.enter_town("shinto_town")

        # Give gold
        run = session.run
        assert run is not None
        new_party = run.party.model_copy(update={"money": 1000})
        session.run = run.model_copy(update={"party": new_party})

        result = session.shop_buy("iron_blade")
        assert "Bought" in result

        result = session.shop_sell("iron_blade")
        assert "Sold" in result


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


class TestLookups:
    def test_lookup_all_jobs(self, session: GameSession, game_data: GameData) -> None:
        session.new_run("Test", "einherjar", seed=1)
        for job_id in game_data.jobs:
            result = session.lookup_job(job_id)
            assert "===" in result

    def test_lookup_ability(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        result = session.lookup_ability("basic_attack")
        assert "basic_attack" in result

    def test_lookup_item(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        result = session.lookup_item("iron_blade")
        assert "Iron Blade" in result

    def test_lookup_enemy(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        result = session.lookup_enemy("fodder_slime")
        assert "Fodder Slime" in result

    def test_lookup_zone(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        result = session.lookup_zone("zone_01")
        assert "Shrine Entrance" in result

    def test_lookup_unknown(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        result = session.lookup_job("nonexistent")
        assert "Unknown job" in result

    def test_lookup_formula_topics(self, session: GameSession) -> None:
        session.new_run("Test", "einherjar", seed=1)
        for topic in ("damage", "hp", "xp", "bonus_actions", "shop_pricing", "overstay", "cheat_survive", "scaling_types", "res_gate"):
            result = session.lookup_formula(topic)
            assert "===" in result or "Unknown" not in result


# ---------------------------------------------------------------------------
# Full integration: play through zone_01
# ---------------------------------------------------------------------------


class TestFullZonePlaythrough:
    def test_clear_zone_01(self, session: GameSession) -> None:
        """Play through all encounters in zone_01."""
        session.new_run("Kael", "einherjar", seed=42)
        session.enter_zone("zone_01")

        encounters_won = 0
        max_encounters = 10  # Safety limit

        while encounters_won < max_encounters:
            if session.phase != Phase.IN_ZONE:
                break

            # Check if zone is cleared
            run = session.run
            assert run is not None
            if run.zone_state and run.zone_state.is_cleared:
                break

            # Start fight
            session.fight()

            # Play through combat
            for _ in range(50):
                if session.phase != Phase.COMBAT:
                    break
                combat = session._combat_state
                assert combat is not None

                living_players = [c for c in combat.player_combatants if c.is_alive]
                living_enemies = [c for c in combat.enemy_combatants if c.is_alive]
                if not living_enemies:
                    break

                decisions = {}
                for p in living_players:
                    decisions[p.id] = {
                        "mode": "normal",
                        "action": "basic_attack",
                        "target": living_enemies[0].id,
                    }
                session.submit_decisions(decisions)

            if session.phase == Phase.DEAD:
                break

            # Handle post-combat
            if session.phase == Phase.POST_COMBAT:
                session.pick_loot([])  # Take nothing

            # Handle recruitment
            if session.phase == Phase.RECRUITING:
                session.recruit(False)  # Decline

            encounters_won += 1

        # Should have cleared or died
        if session.phase != Phase.DEAD:
            assert session.run is not None
            assert session.run.zone_state is not None
            assert session.run.zone_state.is_cleared or session.phase == Phase.DEAD

    def test_battle_record_populated(self, session: GameSession) -> None:
        """Battle record should have data after combat."""
        session.new_run("Kael", "einherjar", seed=42)
        session.enter_zone("zone_01")
        session.fight()

        # Win one fight
        for _ in range(50):
            if session.phase != Phase.COMBAT:
                break
            combat = session._combat_state
            assert combat is not None
            living_players = [c for c in combat.player_combatants if c.is_alive]
            living_enemies = [c for c in combat.enemy_combatants if c.is_alive]
            if not living_enemies:
                break
            decisions = {}
            for p in living_players:
                decisions[p.id] = {
                    "mode": "normal",
                    "action": "basic_attack",
                    "target": living_enemies[0].id,
                }
            session.submit_decisions(decisions)

        if session.phase in (Phase.POST_COMBAT, Phase.IN_ZONE, Phase.RECRUITING):
            run = session.run
            assert run is not None
            assert run.battle_record.total_encounters >= 1
