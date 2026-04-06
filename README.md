# Heresiarch

> Pick a world, pick a job, descend, build synergy, kill god.

A text-based roguelike JRPG. Three mythology-themed worlds (Nordic, Shinto, Abrahamic) — mechanically identical, different paint. Continuous scaling curves where the math does the policing. Degenerate builds are the win condition.

## Core Loop

1. Pick a world theme
2. Pick a starting job (Einherjar, Onmyoji, Martyr, Berserker)
3. Descend through zones — fight, recruit, equip, adapt
4. Beat the Final Boss
5. Face god. Die, or break the math and win.
6. Meta-progression banked. Go again.

## Project Structure

```
heresiarch/
  design/         # Game design docs with designer quotes anchoring intent
  data/           # YAML: jobs, abilities, items, enemies, zones, loot tables
  src/heresiarch/
    engine/       # Pure game logic — zero I/O, event-driven, injected RNG
      models/     # Pydantic models for all game entities
      formulas.py # All math as pure functions
      combat.py   # Combat engine (Cheat/Survive, turns, damage, statuses)
      ai.py       # Enemy AI (weighted action tables, conditions, targeting)
      ...
  tests/          # pytest — deterministic combat simulations, formula verification
```

## Tech Stack

- Python 3.13+ with pydantic
- PyYAML for static game data
- pytest for testing
- uv for package management

## Running Tests

```bash
uv run pytest tests/ -v
```

## Status

- **Phase 1** (complete): Engine core — formulas, combat, AI, models, data loader. 52 tests.
- **Phase 3** (in progress): Game loop — zones, encounters, loot, XP, shops, recruitment, saves.
- **Phase 2** (planned): TUI via Textual.
- **Phase 4** (planned): Meta-progression (CHA, job unlocks, acceleration).
- **Phase 5** (planned): LLM integration (flavor text, combat narration, death recaps).
