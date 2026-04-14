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

## Combat: Cheat/Survive

Every round, each character picks one of three stances:

- **Survive**: Halves all incoming damage and banks 1 Action Point. Resolves first (priority).
- **Cheat**: Spend banked AP to take multiple attacks in a single round. Generates debt that recovers over subsequent turns.
- **Normal**: One action, recover 1 debt.

This creates the core tension: tank now to stockpile AP, then unleash burst windows. Timing matters more than raw stats. Bosses have readable patterns — learning when to Survive and when to Cheat is the game.

## Jobs

Each job has an innate passive that shapes its Cheat/Survive rhythm:

| Job | Innate | Playstyle |
|-----|--------|-----------|
| **Einherjar** | **Retaliate** — counter-attacks when hit | Tank hits, deal damage passively. Survive turns are productive. |
| **Berserker** | **Frenzy** — consecutive attacks stack +15% damage | Glass cannon. Chain attacks in Cheat windows for exponential burst. |
| **Onmyoji** | **Insight** — non-damage actions build stacks consumed for +40% power | Setup-payoff. Survive builds stacks, Cheat spends them. |
| **Martyr** | **Thorns** — reflects 70% of damage taken back to attacker | The wall. Survive + thorns = passive DPS while tanking for the party. |

## Zones & Bosses

Seven zones with escalating enemies and a unique boss each. Every boss teaches a mechanic through its action table — no special engine code, all data-driven:

- **Alpha Slime** — tutorial, punishes passivity
- **Omega Slime** — regenerates, charges devastating attacks when wounded
- **Kodama Elder** — summons adds, heals, buffs — teaches add priority
- **Kappa** — shell invulnerability cycle — teaches pattern recognition
- **Tanuki Trickster** — mimics your last action type — punishes repetition
- **Nue** — multi-phase chimera, shifts damage types by HP threshold
- **Giga Slime** — regen, armor, then splits into 3 mini-bosses on death

Plus **The Pit**: an endless scaling zone for grinding or testing builds.

## Towns

Towns sit between zones. Three buildings:

- **Lodge**: Full party heal. Costs gold scaled to how hurt you are. Resets incomplete zone progress — commit to your runs or pay for the retreat.
- **Shop**: Progressive unlocks as zones are cleared. CHA stat improves prices.
- **Tavern**: NPC hints (planned).

No free heals between zones. Potions vs lodge rest vs pushing forward is the core economy tension.

## Party & Recruitment

Recruit after encounters. Party caps at 3 active + 1 reserve. Each recruit has randomized stat growth (plus/minus per stat), so no two are identical. CHA gates how much you can inspect before committing — low CHA means recruiting blind.

## Equipment

Weapons, armor, and accessories use different scaling curves:

- **Linear**: Reliable, steady returns
- **Superlinear**: Strong at high levels, modest early
- **Degenerate**: Weak early, breaks the game late

Accessories convert stats (STR to MAG, STR to DEF, etc.), enabling cross-class builds. Scrolls teach abilities permanently or cast them once. The item system is designed so that the "optimal" build is always the most creatively degenerate one.

## LLM Agent Player

The entire game is exposed as an MCP server — an LLM can play autonomously from character creation through the final boss.

```bash
uv run python -m heresiarch.agent    # Start MCP server
```

39 tools covering the full game loop. Phase-gated so the agent can't take illegal actions. Engine state is automatically summarized to natural language. The agent can save notes to persist strategy discoveries across runs.

## Balance Tools

### Combat Simulator

Drives the real engine with scripted decisions. Every passive, frenzy chain, and enemy AI action fires exactly as it would in a real game.

```bash
# Berserker survive-survive-survive-cheat cycle through zone 1
uv run python -m heresiarch.tools.sim combat --job berserker --zone zone_01 --cycle "S,S,S,C3"

# Onmyoji insight stacking against specific enemies
uv run python -m heresiarch.tools.sim combat --job onmyoji --level 5 --enemy fodder_slime --cycle "S,S,A:bolt"
```

### Other Analysis

`uv run python -m heresiarch.tools.sim <subcommand>`:

`ability-dpr`, `ability-compare`, `job-curve`, `xp-curve`, `economy`, `enemy-stats`, `shop-pricing`, `lodge-tuning`, `progression`, `sweep`, `crossover`, `build`, `combat`

### Dashboard

```bash
uv run python -m heresiarch.dashboard   # FastAPI on localhost:8000
```

Web-based balance dashboard with runtime formula overrides — tweak constants and see the impact without restarting.

## Architecture

The engine has **zero I/O**. All state passed in/out, all randomness via injected `random.Random`. This makes the game deterministic (same seed = same game), fast to simulate, trivially testable, and clean to integrate with agents.

Game data is entirely YAML-driven — abilities, enemies, items, zones, loot tables, shop tiers, maps. Balance passes rarely need code changes.

See [CLAUDE.md](CLAUDE.md) for the full architecture guide, invariants, and how-to recipes.

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
      screens/      # 16 screens: title through death
      event_renderer.py  # CombatEvent -> display text (verbose/summary modes)
    agent/          # MCP server for LLM-as-player
      server.py     # 39 MCP tools (pure pass-through)
      session.py    # Game session state + phase gating
      summarizer.py # Engine state -> text for LLM consumption
    tools/          # CLI balance simulation tools
      sim.py        # Sweep, DPR, economy, progression sims
      combat_sim.py # Full combat simulator (drives real CombatEngine)
      shared.py     # Shared damage computation helpers
      map_tool.py   # Map authoring/visualization
    dashboard/      # FastAPI balance dashboard with runtime formula overrides
  tests/            # ~450 pytest tests — deterministic, seeded RNG
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
- **Phase 2** (playable): TUI — full game loop from title screen through combat to death. 16 screens, line-by-line combat log, battle history, autosave, permadeath.
- **Agent player** (functional): MCP server for LLM-driven play. 39 tools, phase-gated session management.
- **Dashboard** (functional): FastAPI balance dashboard with runtime formula overrides.
- **Phase 4** (planned): Meta-progression (CHA accumulation, job unlocks, acceleration system).
- **Phase 5** (planned): LLM integration (flavor text, combat narration, death recaps).
