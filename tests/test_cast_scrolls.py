"""One-time cast scrolls must wire through to real ability resolution.

Bug (designer report, 2026-07-10): cast scrolls resolved via the
heal-item path — casts_ability_id was never consulted, the UI's
ally-default targeting stuck to the player's team, and the scroll
did nothing. A scroll cast must behave exactly as if the ability
itself had been used, with targets forced onto the ability's side.
"""

import random
from pathlib import Path

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    PlayerTurnDecision,
)
from tests.conftest import _make_character


@pytest.fixture
def game_data() -> GameData:
    return load_all(Path("data"))


def _combat(game_data: GameData, n_enemies: int = 2, job: str = "einherjar"):
    engine = CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=random.Random(42),
        enemy_registry=game_data.enemies,
    )
    player = _make_character(game_data, job, 5, "iron_blade")
    tmpl = game_data.enemies["fodder_slime"]
    enemies = [engine.create_enemy_instance(tmpl, 3) for _ in range(n_enemies)]
    state = engine.initialize_combat([player], enemies)
    return engine, state, {"fodder_slime": tmpl}


def _use_item_decision(actor_id: str, item_id: str, target_id: str):
    return PlayerTurnDecision(
        combatant_id=actor_id,
        cheat_survive=CheatSurviveChoice.NORMAL,
        primary_action=CombatAction(
            actor_id=actor_id,
            ability_id="use_item",
            item_id=item_id,
            target_ids=[target_id],
        ),
    )


def test_bolt_scroll_mistargeted_at_ally_hits_enemy(game_data: GameData):
    """THE bug: an ally-targeted bolt scroll must redirect to an enemy,
    deal damage, and leave the ally untouched."""
    engine, state, templates = _combat(game_data)
    actor = state.living_players[0]
    hp_actor_before = actor.current_hp
    enemy_hp_before = {e.id: e.current_hp for e in state.living_enemies}

    # Target SELF — mimicking the UI's ally-default item targeting
    decision = _use_item_decision(actor.id, "cast_bolt", actor.id)
    state = engine.process_round(
        state, {actor.id: decision}, templates,
    )

    damaged = [
        eid for eid, hp in enemy_hp_before.items()
        if (c := state.get_combatant(eid)) and c.current_hp < hp
    ]
    assert damaged, "bolt scroll dealt no enemy damage (the original bug)"
    actor_after = state.get_combatant(actor.id)
    # The actor may have taken enemy-turn damage, but must not have
    # taken the bolt: bolt vs 0-DEF self would far exceed slime chip.
    bolt_events = [
        e for e in state.log
        if e.event_type == CombatEventType.DAMAGE_DEALT
        and e.ability_id == "bolt" and e.target_id == actor.id
    ]
    assert not bolt_events, "bolt scroll damaged the caster's own side"
    assert "cast_bolt" in state.consumed_items


def test_cast_scroll_resolves_as_the_ability(game_data: GameData):
    """The cast must go through real ability resolution: an
    ACTION_DECLARED event for the ability, damage from its formula."""
    engine, state, templates = _combat(game_data, n_enemies=1)
    actor = state.living_players[0]
    target = state.living_enemies[0]

    decision = _use_item_decision(actor.id, "cast_bolt", target.id)
    state = engine.process_round(state, {actor.id: decision}, templates)

    declared = [
        e for e in state.log
        if e.event_type == CombatEventType.ACTION_DECLARED
        and e.ability_id == "bolt" and e.actor_id == actor.id
    ]
    assert declared, "scroll cast did not declare the underlying ability"
    used = [
        e for e in state.log
        if e.event_type == CombatEventType.ITEM_USED
        and e.details.get("casts_ability_id") == "bolt"
    ]
    assert used, "scroll use event missing casts_ability_id detail"


def test_aoe_scroll_hits_all_enemies(game_data: GameData):
    engine, state, templates = _combat(game_data, n_enemies=3)
    actor = state.living_players[0]
    before = {e.id: e.current_hp for e in state.living_enemies}

    decision = _use_item_decision(actor.id, "cast_arc_slash", actor.id)
    state = engine.process_round(state, {actor.id: decision}, templates)

    hit = [
        eid for eid, hp in before.items()
        if (c := state.get_combatant(eid)) and c.current_hp < hp
    ]
    assert len(hit) == 3, f"arc_slash scroll hit {len(hit)}/3 enemies"


def test_self_buff_scroll_lands_on_caster(game_data: GameData):
    """stalwart is SELF-targeted: even if the player targets an enemy,
    the buff must land on the caster."""
    engine, state, templates = _combat(game_data, n_enemies=1)
    actor = state.living_players[0]
    enemy = state.living_enemies[0]
    def_before = actor.effective_stats.DEF

    decision = _use_item_decision(actor.id, "cast_stalwart", enemy.id)
    state = engine.process_round(state, {actor.id: decision}, templates)

    actor_after = state.get_combatant(actor.id)
    assert actor_after.effective_stats.DEF > def_before, (
        "stalwart scroll did not buff the caster"
    )


def test_teach_scroll_in_combat_does_not_cast(game_data: GameData):
    """Teach scrolls are the OTHER scroll type — they must not fire
    their ability through the cast path."""
    engine, state, templates = _combat(game_data, n_enemies=1)
    actor = state.living_players[0]
    before = state.living_enemies[0].current_hp

    decision = _use_item_decision(actor.id, "scroll_bolt", actor.id)
    state = engine.process_round(state, {actor.id: decision}, templates)

    declared = [
        e for e in state.log
        if e.event_type == CombatEventType.ACTION_DECLARED
        and e.ability_id == "bolt"
    ]
    assert not declared, "teach scroll cast its ability in combat"
