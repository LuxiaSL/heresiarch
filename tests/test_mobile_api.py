"""Mobile sniff-test API: the phone UI's HTTP surface over GameSession.

Drives a seeded run through the full loop (new run → zone → combat →
loot) via TestClient and checks the structured StatePayload the UI
renders from. See design/mobile-spike.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from heresiarch.mobile.app import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    # Linear zones (the classic Fight flow) — still supported via --linear;
    # dungeon mode has its own tests below.
    app = create_app(notes_path=tmp_path / "notes.json", dungeon_mode=False)
    return TestClient(app)


@pytest.fixture
def dclient(tmp_path: Path) -> TestClient:
    return TestClient(create_app(notes_path=tmp_path / "notes.json"))


def _act(client: TestClient, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    res = client.post("/api/action", json={"tool": tool, "args": args or {}})
    assert res.status_code == 200, res.text
    return res.json()


def test_index_serves_html(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "HERESIARCH" in res.text


def test_pwa_shell_assets_served(client: TestClient) -> None:
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    data = manifest.json()
    assert data["display"] == "fullscreen"
    icon_srcs = [i["src"] for i in data["icons"]]
    # Relative so the bundle also works under a subpath (GitHub Pages)
    assert "icons/icon-512.png" in icon_srcs
    assert not any(src.startswith("/") for src in icon_srcs)
    assert data["start_url"] == "./"

    sw = client.get("/sw.js")
    assert sw.status_code == 200
    assert "no-store" in sw.headers["cache-control"]

    for src in icon_srcs:
        res = client.get("/" + src)
        assert res.status_code == 200, src
        assert res.headers["content-type"] == "image/png"
        assert res.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_icon_route_rejects_traversal_and_unknown(client: TestClient) -> None:
    assert client.get("/icons/nope.png").status_code == 404
    assert client.get("/icons/..%2Findex.html").status_code in (400, 404)


def test_index_links_pwa_shell(client: TestClient) -> None:
    html = client.get("/").text
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html


def test_initial_state_lists_jobs(client: TestClient) -> None:
    res = client.get("/api/state")
    assert res.status_code == 200
    payload = res.json()
    assert payload["phase"] == "SETUP"
    job_ids = {j["id"] for j in payload["jobs"]}
    assert "einherjar" in job_ids
    assert payload["error"] is None


def test_unknown_tool_rejected(client: TestClient) -> None:
    payload = _act(client, "os_system", {"cmd": "rm -rf /"})
    assert payload["error"] is not None
    assert "Unknown tool" in payload["error"]
    assert payload["phase"] == "SETUP"


def test_wrong_phase_surfaces_agent_error(client: TestClient) -> None:
    payload = _act(client, "fight")
    assert payload["error"] is not None
    assert "Cannot use" in payload["error"]
    assert payload["phase"] == "SETUP"


def test_bad_arguments_surface_as_error(client: TestClient) -> None:
    payload = _act(client, "new_run", {"nonsense": True})
    assert payload["error"] is not None
    assert "Bad arguments" in payload["error"]


def _default_decision(player: dict[str, Any], enemies: list[dict[str, Any]]) -> dict[str, Any]:
    """Mirror the UI's default: first ready offensive ability at the first living enemy."""
    ready = [a for a in player["abilities"] if a["cooldown_remaining"] == 0]
    ability = next(
        (a for a in ready if a["category"] == "OFFENSIVE"), ready[0] if ready else None,
    )
    assert ability is not None, f"{player['id']} has no usable ability"
    decision: dict[str, Any] = {"mode": "normal", "action": ability["id"]}
    if ability["target"] == "SINGLE_ENEMY":
        living = [e for e in enemies if e["is_alive"]]
        assert living, "no living enemies to target"
        decision["target"] = living[0]["id"]
    return decision


def test_full_loop_new_run_to_loot(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Spike", "job_id": "einherjar", "seed": 42})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "ZONE_SELECT"
    assert payload["party"] is not None
    assert len(payload["party"]["characters"]) == 1
    assert payload["zone_select"] is not None
    zone_ids = [z["id"] for z in payload["zone_select"]["zones"]]
    assert zone_ids, "no zones offered at run start"

    payload = _act(client, "enter_zone", {"zone_id": zone_ids[0]})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "IN_ZONE"
    assert payload["zone"] is not None
    assert payload["zone"]["total_encounters"] > 0

    payload = _act(client, "fight")
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "COMBAT"
    combat = payload["combat"]
    assert combat is not None
    assert combat["players"] and combat["enemies"]
    assert combat["players"][0]["abilities"], "player has no ability chips to render"

    for _ in range(60):
        if payload["phase"] != "COMBAT":
            break
        combat = payload["combat"]
        assert combat is not None
        decisions = {
            p["id"]: _default_decision(p, combat["enemies"])
            for p in combat["players"]
            if p["is_alive"]
        }
        payload = _act(client, "submit_decisions", {"decisions": decisions})
        assert payload["error"] is None, payload["error"]
    else:
        pytest.fail("combat did not finish within 60 rounds")

    assert payload["phase"] in ("POST_COMBAT", "DEAD")
    if payload["phase"] == "POST_COMBAT":
        assert payload["loot"] is not None
        assert payload["combat"] is None
        payload = _act(client, "pick_loot", {"item_ids": []})
        assert payload["error"] is None, payload["error"]
        assert payload["phase"] in ("IN_ZONE", "RECRUITING")


def test_combat_view_renders_log_lines(client: TestClient) -> None:
    _act(client, "new_run", {"name": "Spike", "job_id": "berserker", "seed": 7})
    payload = _act(client, "enter_zone", {"zone_id": "zone_01"})
    assert payload["error"] is None, payload["error"]
    payload = _act(client, "fight")
    combat = payload["combat"]
    assert combat is not None
    decisions = {
        p["id"]: _default_decision(p, combat["enemies"])
        for p in combat["players"]
        if p["is_alive"]
    }
    payload = _act(client, "submit_decisions", {"decisions": decisions})
    assert payload["error"] is None, payload["error"]
    if payload["phase"] == "COMBAT":
        assert payload["combat"]["log_lines"], "round produced no rendered log lines"


def test_cheat_queue_with_mixed_slots(client: TestClient) -> None:
    """The action-queue UI sends cheat extras with independent targets
    plus wait slots and bonus actions — the session must accept them."""
    _act(client, "new_run", {"name": "Queue", "job_id": "berserker", "seed": 11})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    combat = payload["combat"]
    assert combat is not None
    mc = combat["players"][0]

    # Round 1: survive to bank AP
    payload = _act(client, "submit_decisions", {"decisions": {mc["id"]: {"mode": "survive"}}})
    assert payload["error"] is None, payload["error"]
    if payload["phase"] != "COMBAT":
        pytest.skip("fight ended during the survive round on this seed")
    combat = payload["combat"]
    mc = combat["players"][0]
    assert mc["ap"] >= 1, "survive did not bank AP"

    enemies = [e for e in combat["enemies"] if e["is_alive"]]
    ability = _default_decision(mc, combat["enemies"])["action"]
    decision = {
        "mode": "cheat",
        "action": ability,
        "target": enemies[0]["id"],
        "ap_spend": 1,
        "cheat_extras": [
            {"ability": ability, "target": enemies[-1]["id"]},
        ],
    }
    payload = _act(client, "submit_decisions", {"decisions": {mc["id"]: decision}})
    assert payload["error"] is None, payload["error"]

    # A wait extra must also parse (windup push)
    if payload["phase"] == "COMBAT":
        combat = payload["combat"]
        mc = combat["players"][0]
        if mc["is_alive"] and mc["ap"] >= 1:
            decision = {
                "mode": "cheat",
                "action": ability,
                "target": next(e["id"] for e in combat["enemies"] if e["is_alive"]),
                "ap_spend": 1,
                "cheat_extras": [{"action": "wait"}],
            }
            payload = _act(client, "submit_decisions", {"decisions": {mc["id"]: decision}})
            assert payload["error"] is None, payload["error"]


def test_wait_primary_action_while_charging(client: TestClient) -> None:
    """TUI parity: a mid-windup character can submit Wait as their primary
    action instead of a throwaway attack the engine would discard."""
    _act(client, "new_run", {"name": "Windy", "job_id": "einherjar", "seed": 42})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    assert payload["phase"] == "COMBAT"

    session = client.app.state.session
    combat = session.combat_state
    assert combat is not None
    mc = combat.player_combatants[0]
    mc.ability_ids.append("charge_slam")  # 2-turn windup

    target = next(e.id for e in combat.enemy_combatants if e.is_alive)
    payload = _act(client, "submit_decisions", {"decisions": {
        mc.id: {"mode": "normal", "action": "charge_slam", "target": target},
    }})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "COMBAT", "windup rounds deal no damage"
    player = payload["combat"]["players"][0]
    assert player["charging"], "windup did not surface on the combat view"

    # The mobile client submits Wait as the primary while charging
    payload = _act(client, "submit_decisions", {"decisions": {
        mc.id: {"mode": "normal", "action": "wait"},
    }})
    assert payload["error"] is None, payload["error"]
    if payload["phase"] == "COMBAT":
        # Charge ticked down by exactly one turn
        assert payload["combat"]["players"][0]["charging"], (
            "charge should still be active after one wait round"
        )


def test_wait_primary_accepted_when_not_charging(client: TestClient) -> None:
    """A wait primary is a harmless pass even without an active windup —
    the session must not reject it (the engine treats it as a no-op)."""
    _act(client, "new_run", {"name": "Idler", "job_id": "einherjar", "seed": 42})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    mc_id = payload["combat"]["players"][0]["id"]
    payload = _act(client, "submit_decisions", {"decisions": {
        mc_id: {"mode": "normal", "action": "wait"},
    }})
    assert payload["error"] is None, payload["error"]


def test_taunt_constraint_flows_to_combat_view(client: TestClient) -> None:
    """The taunt lock the client applies to EVERY target picker (primary,
    cheat-extra, bonus slots) is driven by CombatantView.taunted_by — the
    payload must name living taunters so all pickers filter identically."""
    _act(client, "new_run", {"name": "Locked", "job_id": "einherjar", "seed": 42})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    assert payload["phase"] == "COMBAT"

    session = client.app.state.session
    combat = session.combat_state
    assert combat is not None
    mc = combat.player_combatants[0]
    enemy = next(e for e in combat.enemy_combatants if e.is_alive)
    mc.taunted_by.append(enemy.id)

    payload = client.get("/api/state").json()
    view = payload["combat"]["players"][0]
    assert view["taunted_by"] == [enemy.id]
    # The taunter is present (and alive) in the enemy views, so the
    # client can resolve the lock against real target chips
    enemy_views = {e["id"]: e for e in payload["combat"]["enemies"]}
    assert enemy.id in enemy_views and enemy_views[enemy.id]["is_alive"]


def test_loot_view_reports_xp_awards(client: TestClient) -> None:
    """Victory loot payload carries per-character XP gains (TUI parity)."""
    _act(client, "new_run", {"name": "Leveler", "job_id": "einherjar", "seed": 42})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    for _ in range(60):
        if payload["phase"] != "COMBAT":
            break
        combat = payload["combat"]
        decisions = {
            p["id"]: _default_decision(p, combat["enemies"])
            for p in combat["players"]
            if p["is_alive"]
        }
        payload = _act(client, "submit_decisions", {"decisions": decisions})
        assert payload["error"] is None, payload["error"]
    if payload["phase"] != "POST_COMBAT":
        pytest.skip("seed lost the first encounter; no loot screen to check")

    awards = payload["loot"]["xp_awards"]
    assert awards, "victory must report XP for surviving characters"
    mc = awards[0]
    assert mc["name"] == "Leveler"
    assert mc["xp_gained"] > 0, "first zone-1 kill must award XP"
    assert mc["levels_gained"] >= 0
    assert mc["xp_next"] > mc["xp"] - mc["xp_gained"]
    assert mc["level"] >= 1 and mc["job_name"]

    # Awards are one-shot: cleared once the loot is picked
    payload = _act(client, "pick_loot", {"item_ids": []})
    assert payload["error"] is None, payload["error"]
    assert payload["loot"] is None


def test_character_view_has_stats_and_xp(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Stats", "job_id": "einherjar", "seed": 5})
    char = payload["party"]["characters"][0]
    assert set(char["base_stats"]) == {"STR", "MAG", "DEF", "RES", "SPD"}
    assert set(char["effective_stats"]) == {"STR", "MAG", "DEF", "RES", "SPD"}
    assert char["xp_next"] > char["xp"]
    # Stat sheet lists display names, not raw ability ids
    assert "Basic Attack" in char["abilities"]
    assert "basic_attack" not in char["abilities"]


def test_equip_preview_endpoint(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Prev", "job_id": "einherjar", "seed": 5})
    mc = payload["party"]["characters"][0]
    res = client.post("/api/preview_equip", json={
        "character_id": mc["id"], "item_id": "iron_blade",
    })
    assert res.status_code == 200
    preview = res.json()
    assert preview["ok"], preview["error"]
    assert preview["slot"] == "WEAPON"
    assert set(preview["preview"]) == {"STR", "MAG", "DEF", "RES", "SPD"}
    # A weapon must move at least one stat relative to bare hands
    assert preview["preview"] != preview["current"]

    bad = client.post("/api/preview_equip", json={
        "character_id": mc["id"], "item_id": "minor_potion",
    }).json()
    assert not bad["ok"] and "not equippable" in bad["error"]


def test_drop_item_frees_stash_slot(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Drop", "job_id": "einherjar", "seed": 5})
    session = client.app.state.session
    run = session.run
    new_party = run.party.model_copy(update={"stash": ["minor_potion"]})
    session.run = run.model_copy(update={"party": new_party})

    payload = _act(client, "drop_item", {"item_id": "minor_potion"})
    assert payload["error"] is None, payload["error"]
    assert payload["party"]["stash"] == []

    payload = _act(client, "drop_item", {"item_id": "minor_potion"})
    assert payload["error"] is not None  # already gone


def test_final_zone_clear_reaches_victory(client: TestClient) -> None:
    """Clearing the final zone must flip the session to VICTORY with a recap
    — previously agent/mobile runs could beat the final boss and never win."""
    from heresiarch.engine.models.loot import LootResult
    from heresiarch.engine.models.zone import ZoneState

    _act(client, "new_run", {"name": "Winner", "job_id": "einherjar", "seed": 5})
    session = client.app.state.session

    final_zone = next(z for z in session.game_data.zones.values() if z.is_final)
    session.run = session.run.model_copy(update={
        "current_zone_id": final_zone.id,
        "zone_state": ZoneState(
            template_id=final_zone.id,
            current_encounter_index=len(final_zone.encounters),
            is_cleared=True,
        ),
        "zones_completed": list(session.run.zones_completed) + [final_zone.id],
    })
    from heresiarch.agent.session import Phase
    session.phase = Phase.POST_COMBAT
    session._last_loot = LootResult(money=0, item_ids=[])

    payload = _act(client, "pick_loot", {"item_ids": []})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "VICTORY"
    assert payload["recap"] is not None
    assert payload["recap"]["won"] is True
    assert "VICTORY" in payload["text"]


def test_zone_select_payload_has_region_map(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Cartographer", "job_id": "einherjar", "seed": 5})
    m = payload["map"]
    assert m is not None
    assert m["kind"] == "region"
    assert m["art"] and m["width"] > 0
    assert m["navigable_ids"], "region map must have navigable anchors"
    assert m["initial_id"] in m["navigable_ids"]
    by_id = {a["id"]: a for a in m["anchors"]}
    initial = by_id[m["initial_id"]]
    assert initial["status"] == "available"
    assert initial["tap_action"] in ("enter_zone", "enter_town")
    # At least one zone must be embarkable from the map
    assert any(a["tap_action"] == "enter_zone" for a in m["anchors"])
    # Locked zones are visible but not navigable and not tappable
    locked = [a for a in m["anchors"] if a["status"] == "locked"]
    for a in locked:
        assert a["id"] not in m["navigable_ids"]
        assert a["tap_action"] is None


def test_zone_map_has_frontier_and_path(client: TestClient) -> None:
    _act(client, "new_run", {"name": "Pathfinder", "job_id": "einherjar", "seed": 5})
    payload = _act(client, "enter_zone", {"zone_id": "zone_01"})
    m = payload["map"]
    assert m is not None
    assert m["kind"] == "zone"
    by_id = {a["id"]: a for a in m["anchors"]}
    assert by_id["exit"]["tap_action"] == "leave_zone"
    assert by_id["enc_0"]["status"] == "available"
    assert by_id["enc_0"]["tap_action"] == "fight"
    assert m["initial_id"] == "enc_0"
    assert m["path_cells"], "zone map must carry path coloring"
    # Frontier: no traversed path cell lies beyond the available encounter
    frontier = by_id["enc_0"]["col"]
    assert all(c["col"] <= frontier for c in m["path_cells"] if c["traversed"])


def test_town_payload_has_interior_map(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Visitor", "job_id": "onmyoji", "seed": 3})
    towns = payload["zone_select"]["towns"]
    if not towns:
        pytest.skip("no town unlocked at run start in current data")
    payload = _act(client, "enter_town", {"town_id": towns[0]["id"]})
    m = payload["map"]
    if m is None:
        pytest.skip("current town has no interior map")
    assert m["kind"] == "town"
    assert all(a["status"] == "available" for a in m["anchors"])
    actions = {a["id"]: a["tap_action"] for a in m["anchors"]}
    assert actions.get("exit") == "leave_town"


def test_recruit_view_is_cha_gated(client: TestClient) -> None:
    _act(client, "new_run", {"name": "Recruiter", "job_id": "einherjar", "seed": 5})
    session = client.app.state.session
    from heresiarch.agent.session import Phase

    candidate = session.game_loop.recruitment_engine.generate_candidate(
        zone_level=2, exclude_job_ids=[], shop_pool=[],
    )
    session._current_candidate = candidate
    session.phase = Phase.RECRUITING

    res = client.get("/api/state")
    payload = res.json()
    recruit = payload["recruit"]
    assert recruit is not None
    assert recruit["name"] == candidate.character.name
    assert recruit["inspection"] in ("MINIMAL", "MODERATE", "FULL")
    if recruit["inspection"] == "MINIMAL":
        assert recruit["growth"] is None and recruit["stats"] is None
    assert recruit["party_full"] is False


def test_round_events_are_structured_and_paced(client: TestClient) -> None:
    _act(client, "new_run", {"name": "Pacer", "job_id": "berserker", "seed": 7})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    combat = payload["combat"]
    assert payload["events"] == [], "no events before the first round resolves"
    assert payload["hp_start"], "hp_start snapshots at fight start"

    decisions = {
        p["id"]: _default_decision(p, combat["enemies"])
        for p in combat["players"]
        if p["is_alive"]
    }
    payload = _act(client, "submit_decisions", {"decisions": decisions})
    assert payload["error"] is None, payload["error"]

    events = payload["events"]
    assert events, "resolved round must produce structured events"
    for e in events:
        assert e["type"] and e["text"]
        assert e["delay_ms"] > 0
        assert e["color"] in ("damage", "heal", "buff", "debuff", "death", "neutral")
    assert any(e["type"] == "DAMAGE_DEALT" for e in events)
    # Names in event text are display names, not combatant ids
    dmg = next(e for e in events if e["type"] == "DAMAGE_DEALT")
    assert "mc_berserker" not in dmg["text"]

    summary = payload["events_summary"]
    assert summary, "summary collapse must be present"
    assert len(summary) <= len(events)

    # hp_start covers every combatant that started the round
    hp_start = payload["hp_start"]
    if payload["phase"] == "COMBAT":
        for c in payload["combat"]["players"] + payload["combat"]["enemies"]:
            assert c["id"] in hp_start


def test_final_round_events_survive_combat_end(client: TestClient) -> None:
    """The killing round's events must reach the post-combat screen."""
    _act(client, "new_run", {"name": "Closer", "job_id": "einherjar", "seed": 42})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    for _ in range(60):
        if payload["phase"] != "COMBAT":
            break
        combat = payload["combat"]
        decisions = {
            p["id"]: _default_decision(p, combat["enemies"])
            for p in combat["players"]
            if p["is_alive"]
        }
        payload = _act(client, "submit_decisions", {"decisions": decisions})
        assert payload["error"] is None, payload["error"]
    assert payload["phase"] in ("POST_COMBAT", "DEAD")
    assert payload["events"], "final round events missing after combat end"
    assert any(
        e["type"] in ("DEATH", "COMBAT_END") for e in payload["events"]
    )


def test_auto_battle_requires_matching_record(client: TestClient) -> None:
    _act(client, "new_run", {"name": "NoAuto", "job_id": "einherjar", "seed": 5})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")
    assert payload["combat"]["auto_available"] is False
    payload = _act(client, "auto_battle_round")
    assert payload["error"] is not None
    assert "No recorded victory" in payload["error"]


def test_auto_battle_replays_matching_record(client: TestClient) -> None:
    """With a matching victory on record, auto_battle_round runs a round."""
    _act(client, "new_run", {"name": "Auto", "job_id": "berserker", "seed": 7})
    _act(client, "enter_zone", {"zone_id": "zone_01"})
    payload = _act(client, "fight")

    # Win the first encounter manually so a record exists
    for _ in range(60):
        if payload["phase"] != "COMBAT":
            break
        combat = payload["combat"]
        decisions = {
            p["id"]: _default_decision(p, combat["enemies"])
            for p in combat["players"]
            if p["is_alive"]
        }
        payload = _act(client, "submit_decisions", {"decisions": decisions})
        assert payload["error"] is None, payload["error"]
    if payload["phase"] != "POST_COMBAT":
        pytest.skip("seed lost the first encounter; can't record a victory")
    payload = _act(client, "pick_loot", {"item_ids": []})
    if payload["phase"] == "RECRUITING":
        payload = _act(client, "recruit", {"accept": False})

    # Start the next encounter, then graft the recorded rounds onto a
    # record matching THIS encounter's enemy group (different group ids).
    payload = _act(client, "fight")
    assert payload["phase"] == "COMBAT"
    session = client.app.state.session
    won = session.run.battle_record.encounters[-1]
    assert won.result == "victory" and won.rounds
    grafted = won.model_copy(update={
        "enemy_template_ids": list(session._enemy_combatant_templates.values()),
    })
    from heresiarch.engine.models.battle_record import BattleRecord
    session.run = session.run.model_copy(update={
        "battle_record": BattleRecord(
            encounters=list(session.run.battle_record.encounters) + [grafted],
        ),
    })

    payload = client.get("/api/state").json()
    assert payload["combat"]["auto_available"] is True

    round_before = payload["combat"]["round_number"]
    payload = _act(client, "auto_battle_round")
    assert payload["error"] is None, payload["error"]
    assert payload["events"], "auto round must produce events"
    if payload["phase"] == "COMBAT":
        assert payload["combat"]["round_number"] == round_before + 1


def _finish_current_combat(client: TestClient) -> dict[str, Any]:
    """Drive the current COMBAT phase to its end with default decisions."""
    payload = client.get("/api/state").json()
    for _ in range(60):
        if payload["phase"] != "COMBAT":
            break
        combat = payload["combat"]
        decisions = {
            p["id"]: _default_decision(p, combat["enemies"])
            for p in combat["players"]
            if p["is_alive"]
        }
        payload = _act(client, "submit_decisions", {"decisions": decisions})
        assert payload["error"] is None, payload["error"]
    return payload


def test_battle_record_survives_pwa_relaunch(tmp_path: Path) -> None:
    """Auto-battle after app restart: battle records (incl. per-round
    decisions) must survive the save -> fresh-session -> load path the
    wasm PWA uses, and the replay lookup must still match."""
    from heresiarch.engine.replay import find_matching_record

    notes = tmp_path / "notes.json"
    first = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    _act(first, "new_run", {"name": "Grinder", "job_id": "einherjar", "seed": 42})
    _act(first, "enter_zone", {"zone_id": "zone_01"})
    _act(first, "fight")
    payload = _finish_current_combat(first)
    if payload["phase"] != "POST_COMBAT":
        pytest.skip("seed lost the first encounter; nothing to record")
    payload = _act(first, "pick_loot", {"item_ids": []})  # autosaves

    won = first.app.state.session.run.battle_record.encounters[-1]
    assert won.result == "victory" and won.rounds, "pre-save record malformed"

    # App relaunch: fresh session over the same storage
    second = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    payload = _act(second, "load_run", {"slot": "autosave"})
    assert payload["error"] is None, payload["error"]

    loaded = second.app.state.session.run.battle_record.encounters
    assert loaded, "battle record lost across save/load"
    restored = loaded[-1]
    assert restored.result == "victory"
    assert restored.enemy_template_ids == won.enemy_template_ids
    assert len(restored.rounds) == len(won.rounds), "round records lost"
    assert restored.rounds[0].player_decisions, "recorded decisions lost"
    assert find_matching_record(loaded, won.enemy_template_ids) is not None


def test_auto_start_offered_after_reload_at_low_hp(tmp_path: Path) -> None:
    """Regression: 'auto-battle unavailable after restarting the game'.

    Root cause: the CLIENT hid the Auto start button whenever auto_halt
    (party HP <= 50%) was set — and HP persists in saves, so a worn-down
    party could never start auto again, restart or not. The TUI never
    HP-gates STARTING auto; the halt rule only stops a running loop.
    Contract: auto_available is independent of HP, auto_halt is advisory
    for the running loop, and auto_battle_round works at low HP.
    """
    from heresiarch.engine.models.battle_record import BattleRecord

    notes = tmp_path / "notes.json"
    first = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    _act(first, "new_run", {"name": "Worn", "job_id": "einherjar", "seed": 42})
    _act(first, "enter_zone", {"zone_id": "zone_01"})
    _act(first, "fight")
    payload = _finish_current_combat(first)
    if payload["phase"] != "POST_COMBAT":
        pytest.skip("seed lost the first encounter; can't record a victory")
    _act(first, "pick_loot", {"item_ids": []})

    # Grinding wore the party below half HP — then the app was closed
    session = first.app.state.session
    run = session.run
    chars = {
        cid: char.model_copy(update={"current_hp": max(1, char.max_hp // 3)})
        for cid, char in run.party.characters.items()
    }
    session.run = run.model_copy(
        update={"party": run.party.model_copy(update={"characters": chars})},
    )
    payload = _act(first, "save_run", {"slot": "autosave"})
    assert payload["error"] is None, payload["error"]

    # Relaunch + load + fight; graft the won record onto this encounter's
    # enemy group (same pattern as the auto-battle replay test above)
    second = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    payload = _act(second, "load_run", {"slot": "autosave"})
    assert payload["error"] is None, payload["error"]
    payload = _act(second, "fight")
    assert payload["phase"] == "COMBAT"

    s2 = second.app.state.session
    won = s2.run.battle_record.encounters[-1]
    grafted = won.model_copy(update={
        "enemy_template_ids": list(s2._enemy_combatant_templates.values()),
    })
    s2.run = s2.run.model_copy(update={
        "battle_record": BattleRecord(
            encounters=list(s2.run.battle_record.encounters) + [grafted],
        ),
    })

    combat = second.get("/api/state").json()["combat"]
    assert combat["auto_available"] is True, (
        "auto start must be offered regardless of party HP"
    )
    assert combat["auto_halt"], "halt rule should still be advertised"

    payload = _act(second, "auto_battle_round")
    assert payload["error"] is None, payload["error"]


def test_town_view_has_priced_shop(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Spike", "job_id": "onmyoji", "seed": 3})
    towns = payload["zone_select"]["towns"]
    if not towns:
        pytest.skip("no town unlocked at run start in current data")
    payload = _act(client, "enter_town", {"town_id": towns[0]["id"]})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "IN_TOWN"
    town = payload["town"]
    assert town is not None
    assert town["shop_items"], "town shop is empty"
    assert all(it["price"] is not None for it in town["shop_items"])


def test_title_saves_list_and_load(tmp_path: Path) -> None:
    """Autosaves show up in the title-screen browser and load from it."""
    notes = tmp_path / "notes.json"
    first = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    payload = _act(first, "new_run", {"name": "Keeper", "job_id": "einherjar", "seed": 9})
    assert payload["phase"] == "ZONE_SELECT"  # new_run autosaved

    # Fresh session over the same storage = app relaunch
    second = TestClient(create_app(notes_path=notes, dungeon_mode=False))
    payload = second.get("/api/state").json()
    assert payload["phase"] == "SETUP"
    slots = {s["slot"]: s for s in payload["saves"]}
    assert "autosave" in slots
    assert slots["autosave"]["mc_name"] == "Keeper"
    assert slots["autosave"]["level"] >= 1

    payload = _act(second, "load_run", {"slot": "autosave"})
    assert payload["error"] is None, payload["error"]
    assert payload["phase"] == "ZONE_SELECT"
    names = [c["name"] for c in payload["party"]["characters"]]
    assert "Keeper" in names


def test_missing_save_reports_in_text(client: TestClient) -> None:
    payload = _act(client, "load_run", {"slot": "autosave"})
    assert payload["phase"] == "SETUP"
    assert "not found" in payload["text"].lower()


def test_export_import_round_trip(tmp_path: Path) -> None:
    """Export from one device, import on another, keep playing."""
    src = TestClient(create_app(notes_path=tmp_path / "src" / "notes.json", dungeon_mode=False))
    _act(src, "new_run", {"name": "Traveler", "job_id": "berserker", "seed": 11})
    res = src.post("/api/export_save", json={"slot": "autosave"})
    assert res.status_code == 200
    exported = res.json()
    assert exported["ok"], exported
    assert exported["data"]["run"]

    dst = TestClient(create_app(notes_path=tmp_path / "dst" / "notes.json", dungeon_mode=False))
    res = dst.post(
        "/api/import_save", json={"slot": "autosave", "data": exported["data"]},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["error"] is None, payload["error"]
    assert any(s["slot"] == "autosave" for s in payload["saves"])

    payload = _act(dst, "load_run", {"slot": "autosave"})
    assert payload["phase"] == "ZONE_SELECT"
    assert "Traveler" in [c["name"] for c in payload["party"]["characters"]]


def test_import_rejects_garbage(client: TestClient) -> None:
    res = client.post("/api/import_save", json={"slot": "evil", "data": {"nope": 1}})
    payload = res.json()
    assert payload["error"] is not None

    res = client.post(
        "/api/import_save",
        json={"slot": "../../etc/passwd", "data": {"run": {"bad": True}}},
    )
    payload = res.json()
    assert payload["error"] is not None  # fails validation before any write

    res = client.post("/api/export_save", json={"slot": "../secrets"})
    exported = res.json()
    assert exported["ok"] is False


# ----------------------------------------------------------------------
# Dungeon mode (the default)
# ----------------------------------------------------------------------


def test_dungeon_floor_payload_and_walk(dclient: TestClient) -> None:
    p = _act(dclient, "new_run", {"name": "D", "job_id": "einherjar", "seed": 9})
    p = _act(dclient, "enter_zone", {"zone_id": "zone_01"})
    assert p["error"] is None, p["error"]
    d = p["dungeon"]
    assert d is not None and p["map"] is None  # floor replaces the path map
    assert d["floor_number"] == 1 and d["total_floors"] >= 1
    assert len(d["tiles"]) == d["height"] and len(d["tiles"][0]) == d["width"]
    # Unexplored tiles are masked, the hero's own tile is not
    assert d["tiles"][d["player_y"]][d["player_x"]] in ".>"
    assert any(" " in row for row in d["tiles"])

    turn = d["turn"]
    p = _act(dclient, "wait_turn")
    assert p["error"] is None
    if p["phase"] == "IN_ZONE":
        assert p["dungeon"]["turn"] == turn + 1

    p = _act(dclient, "move", {"direction": "sideways"})
    assert p["error"] and "direction" in p["error"]


def test_dungeon_fight_tool_points_at_walking(dclient: TestClient) -> None:
    _act(dclient, "new_run", {"name": "D", "job_id": "einherjar", "seed": 9})
    _act(dclient, "enter_zone", {"zone_id": "zone_01"})
    p = _act(dclient, "fight")
    assert p["error"] and "walk into" in p["error"]


def test_dungeon_contact_opens_combat_with_opening(dclient: TestClient) -> None:
    """Travel at the first pack seen; the fight must say how it opened."""
    _act(dclient, "new_run", {"name": "D", "job_id": "einherjar", "seed": 9})
    p = _act(dclient, "enter_zone", {"zone_id": "zone_01"})
    for _ in range(200):
        if p["phase"] != "IN_ZONE":
            break
        d = p["dungeon"]
        foes = [e for e in d["entities"] if e["kind"] != "ITEM"]
        if foes:
            p = _act(dclient, "travel", {"x": foes[0]["x"], "y": foes[0]["y"]})
            continue
        # walk to the nearest frontier tile
        best = None
        for y, row in enumerate(d["tiles"]):
            for x, ch in enumerate(row):
                if ch not in ".>":
                    continue
                near_unknown = any(
                    0 <= y + dy < d["height"] and 0 <= x + dx < d["width"]
                    and d["tiles"][y + dy][x + dx] == " "
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                dist = abs(x - d["player_x"]) + abs(y - d["player_y"])
                if near_unknown and dist and (best is None or dist < best[0]):
                    best = (dist, x, y)
        assert best is not None, "explored everything without meeting a pack"
        p = _act(dclient, "travel", {"x": best[1], "y": best[2]})
    assert p["phase"] == "COMBAT", p.get("error")
    combat = p["combat"]
    assert combat["opening"] in ("first_strike", "ambush")
    assert combat["opening_text"]
    assert all(e["sprite"] for e in combat["enemies"])


def test_sprites_route_guards_traversal(dclient: TestClient) -> None:
    assert dclient.get("/sprites/..%2Fapp.py").status_code == 404
    assert dclient.get("/sprites/nope.png").status_code == 404
