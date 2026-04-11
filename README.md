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
      formulas.py   # All math as pure functions + named constants
      combat.py     # Combat engine: phased effect pipeline, Cheat/Survive turns
      passive_handlers.py  # Data-driven passive ability dispatch table
      ai.py         # Enemy AI (weighted action tables, conditions, targeting)
      game_loop.py  # Stateless orchestrator: combat -> XP -> loot -> zones
      save_manager.py # JSON save/load, permadeath deletion
      ...
    tui/            # Textual TUI — renders engine state, collects decisions
      app.py        # App shell, state owner, screen routing
      screens/      # 14 screens: title through death
      event_renderer.py  # CombatEvent -> display text (verbose/summary modes)
    agent/          # MCP server for LLM-as-player
      server.py     # 30 MCP tools (pure pass-through)
      session.py    # Game session state + phase gating
      summarizer.py # Engine state -> text for LLM consumption
    tools/          # CLI balance simulation tools
      sim.py        # Sweep, DPR, economy, progression sims
      shared.py     # Shared damage computation helpers
    dashboard/      # FastAPI balance dashboard with runtime formula overrides
  tests/            # ~300 pytest tests — deterministic, seeded RNG
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

- **Phase 1** (complete): Engine core — formulas, combat, AI, models, data loader.
- **Phase 3** (complete): Game loop — zones, encounters, loot, XP, shops, recruitment, saves.
- **Phase 2** (playable): TUI — full game loop from title screen through combat to death. 14 screens, line-by-line combat log, battle history, autosave, permadeath.
- **Agent player** (functional): MCP server for LLM-driven play. 30 tools, phase-gated session management.
- **Dashboard** (functional): FastAPI balance dashboard with runtime formula overrides.
- **Phase 4** (planned): Meta-progression (CHA accumulation, job unlocks, acceleration system).
- **Phase 5** (planned): LLM integration (flavor text, combat narration, death recaps).
