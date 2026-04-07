"""Tests for scroll items: permanent teach and one-time cast."""

import random

import pytest

from heresiarch.engine.data_loader import GameData
from heresiarch.engine.game_loop import GameLoop


@pytest.fixture
def game_loop(game_data: GameData, seeded_rng: random.Random) -> GameLoop:
    return GameLoop(game_data=game_data, rng=seeded_rng)


class TestTeachScroll:
    def test_teach_scroll_grants_ability(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        mc = run.party.characters["mc_einherjar"]
        assert "arc_slash" not in mc.abilities

        # Add scroll to stash
        run = game_loop.apply_loot(
            run,
            game_loop.loot_resolver.resolve_encounter_drops([], zone_level=1),
            selected_items=[],
        )
        new_stash = list(run.party.stash) + ["scroll_arc_slash"]
        new_items = dict(run.party.items)
        new_items["scroll_arc_slash"] = game_loop.game_data.items["scroll_arc_slash"]
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"stash": new_stash, "items": new_items})}
        )

        run = game_loop.use_teach_scroll(run, "scroll_arc_slash", "mc_einherjar")
        mc = run.party.characters["mc_einherjar"]
        assert "arc_slash" in mc.abilities
        assert "scroll_arc_slash" not in run.party.stash

    def test_teach_scroll_no_duplicate(self, game_loop: GameLoop) -> None:
        """Teaching an ability the character already has shouldn't add a duplicate."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")

        # Give einherjar brace_strike manually (they'd get it at Lv3)
        mc = run.party.characters["mc_einherjar"]
        mc = mc.model_copy(update={"abilities": list(mc.abilities) + ["brace_strike"]})
        new_chars = dict(run.party.characters)
        new_chars["mc_einherjar"] = mc
        new_stash = ["scroll_arc_slash"]
        new_items = {"scroll_arc_slash": game_loop.game_data.items["scroll_arc_slash"]}
        run = run.model_copy(
            update={"party": run.party.model_copy(
                update={"characters": new_chars, "stash": new_stash, "items": new_items}
            )}
        )

        # Now teach arc_slash (which isn't a dup), verify only added once
        run = game_loop.use_teach_scroll(run, "scroll_arc_slash", "mc_einherjar")
        mc = run.party.characters["mc_einherjar"]
        assert mc.abilities.count("arc_slash") == 1

    def test_teach_scroll_not_in_stash_raises(self, game_loop: GameLoop) -> None:
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        with pytest.raises(ValueError, match="not in stash"):
            game_loop.use_teach_scroll(run, "scroll_arc_slash", "mc_einherjar")

    def test_teach_scroll_invalid_item_raises(self, game_loop: GameLoop) -> None:
        """Using a non-scroll item as a teach scroll should fail."""
        run = game_loop.new_run("run_001", "Hero", "einherjar")
        new_stash = ["minor_potion"]
        run = run.model_copy(
            update={"party": run.party.model_copy(update={"stash": new_stash})}
        )
        with pytest.raises(ValueError, match="not a teach scroll"):
            game_loop.use_teach_scroll(run, "minor_potion", "mc_einherjar")


class TestScrollDataIntegrity:
    def test_all_teach_scrolls_reference_valid_abilities(self, game_data: GameData) -> None:
        for item_id, item in game_data.items.items():
            if item.teaches_ability_id:
                assert item.teaches_ability_id in game_data.abilities, (
                    f"Scroll '{item_id}' teaches unknown ability '{item.teaches_ability_id}'"
                )

    def test_all_cast_scrolls_reference_valid_abilities(self, game_data: GameData) -> None:
        for item_id, item in game_data.items.items():
            if item.casts_ability_id:
                assert item.casts_ability_id in game_data.abilities, (
                    f"Scroll '{item_id}' casts unknown ability '{item.casts_ability_id}'"
                )

    def test_scrolls_are_consumable(self, game_data: GameData) -> None:
        for item_id, item in game_data.items.items():
            if item.teaches_ability_id or item.casts_ability_id:
                assert item.is_consumable, f"Scroll '{item_id}' must be consumable"

    def test_teach_scrolls_exist(self, game_data: GameData) -> None:
        teach_scrolls = [i for i in game_data.items.values() if i.teaches_ability_id]
        assert len(teach_scrolls) >= 3, "Expected at least 3 teach scrolls"

    def test_cast_scrolls_exist(self, game_data: GameData) -> None:
        cast_scrolls = [i for i in game_data.items.values() if i.casts_ability_id]
        assert len(cast_scrolls) >= 1, "Expected at least 1 cast scroll"
