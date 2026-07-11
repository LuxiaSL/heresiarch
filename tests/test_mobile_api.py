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
    app = create_app(notes_path=tmp_path / "notes.json")
    return TestClient(app)


def _act(client: TestClient, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    res = client.post("/api/action", json={"tool": tool, "args": args or {}})
    assert res.status_code == 200, res.text
    return res.json()


def test_index_serves_html(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "HERESIARCH" in res.text


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


def test_character_view_has_stats_and_xp(client: TestClient) -> None:
    payload = _act(client, "new_run", {"name": "Stats", "job_id": "einherjar", "seed": 5})
    char = payload["party"]["characters"][0]
    assert set(char["base_stats"]) == {"STR", "MAG", "DEF", "RES", "SPD"}
    assert set(char["effective_stats"]) == {"STR", "MAG", "DEF", "RES", "SPD"}
    assert char["xp_next"] > char["xp"]


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
