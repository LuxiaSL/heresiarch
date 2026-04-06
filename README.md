# Heresiarch

> Pick a world, pick a job, descend, build synergy, kill god.

A text-based roguelike JRPG. Three mythology-themed worlds (Nordic, Shinto, Abrahamic) — mechanically identical, different paint. Continuous scaling curves where the math does the policing. Degenerate builds are the win condition.

## Playing

```bash
uv run heresiarch
```

Arrow keys to navigate, Enter to select, Escape to go back. `Ctrl+S` saves a screenshot (SVG).

## Core Loop

1. Pick a starting job (Einherjar, Onmyoji, Martyr, Berserker)
2. Descend through zones — fight, recruit, equip, adapt
3. Cheat/Survive combat: bank turns for defense, spend them for burst
4. Beat the Final Boss
5. Face god. Die, or break the math and win.
6. Meta-progression banked. Go again.

## Project Structure

```
heresiarch/
  design/           # Game design docs with designer quotes anchoring intent
  data/             # YAML: jobs, abilities, items, enemies, zones, loot tables
  src/heresiarch/
    engine/         # Pure game logic — zero I/O, event-driven, injected RNG
      models/       # Pydantic models for all game entities
      formulas.py   # All math as pure functions
      combat.py     # Combat engine (Cheat/Survive, turns, damage, statuses)
      ai.py         # Enemy AI (weighted action tables, conditions, targeting)
      game_loop.py  # Stateless orchestrator: combat → XP → loot → zones
      save_manager.py # JSON save/load, permadeath deletion
      ...
    tui/            # Textual TUI — renders engine state, collects decisions
      app.py        # App shell, state owner, screen routing
      screens/      # Title, job select, zone, combat, post-combat, party,
                    # inventory, shop, recruitment, death
      event_renderer.py  # CombatEvent → display text (verbose/summary modes)
      styles/       # TCSS theme
  tests/            # 180 pytest tests — deterministic, seeded RNG
```

## Tech Stack

- Python 3.13+ with pydantic
- Textual for TUI
- PyYAML for static game data
- pytest for testing
- uv for package management

## Running Tests

```bash
uv run pytest tests/ -v
```

## Status

- **Phase 1** (complete): Engine core — formulas, combat, AI, models, data loader. 52 tests.
- **Phase 3** (complete): Game loop — zones, encounters, loot, XP, shops, recruitment, saves. 180 tests.
- **Phase 2** (playable): TUI via Textual — full game loop from title screen through combat to death. Sequential JRPG-style turn planning, line-by-line combat log, battle history tracking, per-run autosave, permadeath.
- **Phase 4** (planned): Meta-progression (CHA accumulation, job unlocks, acceleration system).
- **Phase 5** (planned): LLM integration (flavor text, combat narration, death recaps).
