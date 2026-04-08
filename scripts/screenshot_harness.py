#!/usr/bin/env python3
"""Screenshot harness for TUI iteration.

Captures SVG screenshots of every screen state for visual review.
Runs headlessly via Textual's Pilot API — no terminal needed.

Usage:
    uv run python scripts/screenshot_harness.py
    uv run python scripts/screenshot_harness.py --size 80x24
    uv run python scripts/screenshot_harness.py --only combat
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from pathlib import Path

# Ensure the project src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from heresiarch.engine.data_loader import load_all
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.battle_record import BattleRecord, EncounterRecord
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult
from heresiarch.tui.app import HeresiarchApp

DATA = Path("data")
OUT = Path("screenshots/harness")

# Reusable state setup
_game_data = None
_seed = 42


def get_game_data():
    global _game_data
    if _game_data is None:
        _game_data = load_all(DATA)
    return _game_data


def make_run(name: str = "Heresiarch", job: str = "einherjar"):
    """Create a run state with the MC in the first zone."""
    gd = get_game_data()
    rng = random.Random(_seed)
    gl = GameLoop(game_data=gd, rng=rng)
    run = gl.new_run("ss_run", name, job)
    zones = sorted(gd.zones.keys())
    run = gl.enter_zone(run, zones[0])
    return run, gl


def make_app(**kwargs) -> HeresiarchApp:
    return HeresiarchApp(
        game_data=get_game_data(),
        rng=random.Random(_seed),
        **kwargs,
    )


async def save(app: HeresiarchApp, pilot, name: str) -> Path:
    """Wait for idle and save a screenshot."""
    await pilot.pause()
    svg = app.export_screenshot()
    path = OUT / name
    path.write_text(svg)
    print(f"  saved {name}")
    return path


# ---- Screen Captures ----


async def capture_title(size: tuple[int, int]):
    print("\n--- Title Screen ---")
    app = make_app()
    async with app.run_test(size=size) as pilot:
        await save(app, pilot, "01_title.svg")


async def capture_job_select(size: tuple[int, int]):
    print("\n--- Job Select ---")
    app = make_app()
    async with app.run_test(size=size) as pilot:
        # Title → Job Select via hotkey
        await pilot.press("n")
        await save(app, pilot, "02_job_select.svg")

        # Navigate to show detail
        await pilot.press("down")
        await pilot.pause()
        await save(app, pilot, "03_job_select_detail.svg")

        # Select job → name input
        await pilot.press("enter")
        await pilot.pause()
        await save(app, pilot, "04_job_name_input.svg")


async def capture_zone(size: tuple[int, int]):
    print("\n--- Zone Hub ---")
    run, _ = make_run()
    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.zone import ZoneScreen

        app.switch_screen(ZoneScreen())
        await save(app, pilot, "05_zone.svg")


async def capture_combat(size: tuple[int, int]):
    print("\n--- Combat ---")
    run, _ = make_run()
    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.combat import CombatScreen

        app.switch_screen(CombatScreen())
        await save(app, pilot, "06_combat_cheat_survive.svg")

        # Select "Normal"
        await pilot.press("enter")
        await pilot.pause()
        await save(app, pilot, "07_combat_ability.svg")

        # Select first ability (basic_attack)
        await pilot.press("enter")
        await pilot.pause()
        await save(app, pilot, "08_combat_target.svg")

        # Select first target
        await pilot.press("enter")
        await pilot.pause()
        await save(app, pilot, "09_combat_after_target.svg")


async def capture_party(size: tuple[int, int]):
    print("\n--- Party ---")
    run, _ = make_run()
    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.party import PartyScreen

        app.switch_screen(PartyScreen())
        await save(app, pilot, "10_party.svg")

        # Select MC to show detail + actions
        await pilot.press("enter")
        await pilot.pause()
        await save(app, pilot, "11_party_actions.svg")


async def capture_inventory(size: tuple[int, int]):
    print("\n--- Inventory ---")
    run, _ = make_run()
    # Add some items to stash so it's not empty
    stash = list(run.party.stash) + ["iron_blade", "minor_potion"]
    items = dict(run.party.items)
    for item_id in ["iron_blade", "minor_potion"]:
        item = get_game_data().items.get(item_id)
        if item:
            items[item_id] = item
    party = run.party.model_copy(update={"stash": stash, "items": items})
    run = run.model_copy(update={"party": party})

    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.inventory import InventoryScreen

        app.switch_screen(InventoryScreen())
        await save(app, pilot, "12_inventory.svg")


async def capture_shop(size: tuple[int, int]):
    print("\n--- Shop ---")
    run, _ = make_run()
    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.shop import ShopScreen

        app.switch_screen(ShopScreen())
        await save(app, pilot, "13_shop_buy.svg")

        # Switch to sell tab
        await pilot.press("s")
        await pilot.pause()
        await save(app, pilot, "14_shop_sell.svg")


async def capture_recruitment(size: tuple[int, int]):
    print("\n--- Recruitment ---")
    run, gl = make_run()
    candidate = gl.recruitment_engine.generate_candidate(zone_level=1)

    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.recruitment import RecruitmentScreen

        app.switch_screen(RecruitmentScreen(candidate))
        await save(app, pilot, "15_recruitment.svg")


async def capture_post_combat(size: tuple[int, int]):
    print("\n--- Post-Combat ---")
    run, _ = make_run()
    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        result = CombatResult(
            player_won=True,
            surviving_character_ids=list(run.party.active),
            surviving_character_hp={cid: 50 for cid in run.party.active},
            rounds_taken=3,
            zone_level=1,
        )
        loot = LootResult(money=25, item_ids=["iron_blade"])

        from heresiarch.tui.screens.post_combat import PostCombatScreen

        app.switch_screen(PostCombatScreen(combat_result=result, loot=loot))
        await save(app, pilot, "16_post_combat.svg")


async def capture_death(size: tuple[int, int]):
    print("\n--- Death ---")
    run, _ = make_run()
    # Populate battle record for the recap
    encounter = EncounterRecord(
        zone_id="zone_01",
        encounter_index=0,
        enemy_template_ids=["fodder_slime"],
        result="defeat",
        rounds_taken=5,
        total_damage_dealt=240,
        total_damage_taken=185,
        total_healing=30,
        character_deaths=list(run.party.active),
    )
    run = run.model_copy(
        update={"battle_record": BattleRecord(encounters=[encounter])}
    )

    app = make_app()
    async with app.run_test(size=size) as pilot:
        app.run_state = run
        from heresiarch.tui.screens.death import DeathScreen

        app.switch_screen(DeathScreen())
        await save(app, pilot, "17_death.svg")


# ---- Main ----

ALL_CAPTURES = {
    "title": capture_title,
    "job_select": capture_job_select,
    "zone": capture_zone,
    "combat": capture_combat,
    "party": capture_party,
    "inventory": capture_inventory,
    "shop": capture_shop,
    "recruitment": capture_recruitment,
    "post_combat": capture_post_combat,
    "death": capture_death,
}


async def main(size: tuple[int, int], only: str | None = None):
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Saving screenshots to {OUT}/ (size: {size[0]}x{size[1]})")

    captures = ALL_CAPTURES
    if only:
        captures = {k: v for k, v in ALL_CAPTURES.items() if only in k}
        if not captures:
            print(f"No captures match '{only}'. Available: {list(ALL_CAPTURES.keys())}")
            return

    for name, fn in captures.items():
        try:
            await fn(size)
        except Exception as e:
            print(f"  ERROR in {name}: {e}")
            import traceback

            traceback.print_exc()

    count = len(list(OUT.glob("*.svg")))
    print(f"\nDone! {count} screenshots in {OUT}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TUI screenshot harness")
    parser.add_argument(
        "--size",
        default="120x40",
        help="Terminal size as WxH (default: 120x40)",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Only capture screens matching this substring",
    )
    args = parser.parse_args()

    w, h = args.size.split("x")
    asyncio.run(main(size=(int(w), int(h)), only=args.only))
