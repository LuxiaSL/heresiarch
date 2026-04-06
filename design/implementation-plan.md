# Implementation Plan

## Current State (Phase 1 Complete)

The engine core is built and tested. 52 passing tests validate all game math against design doc numbers.

### What Exists

```
heresiarch/
    src/heresiarch/engine/
        models/          # 7 pydantic model files — all game entities
        formulas.py      # All pure math (damage, DEF, RES gate, HP, SPD, scaling)
        combat.py        # Full combat engine (Cheat/Survive, turns, damage, statuses)
        ai.py            # Enemy AI (weighted action tables, conditions, targeting)
        scaling.py       # Item scaling evaluation
        data_loader.py   # YAML -> pydantic with cross-reference validation
    data/                # 4 jobs, 18 abilities, 9 items, 5 enemy archetypes
    tests/               # 52 tests — formulas, scaling crossovers, combat simulations
```

### Verified Behaviors
- HP calculations match design doc snapshots
- Item scaling crossovers at correct stat values
- Taunt redirects, Retaliate counters, Frenzy stacks, DOT bypasses DEF
- Survive halves damage, Cheat creates action debt
- SPD bonus actions at threshold
- Enemy AI conditional weight shifts
- Party vs fodder is a stomp, 1v1 Einherjar vs Brute is ~4 rounds

---

## Phase 2: TUI (Textual)

Put a playable face on the engine.

### Screens Needed
- **Title screen** — new run, continue run, meta-progression view
- **World/job select** — pick theme, pick starting job
- **Zone map** — current zone, encounters ahead, shop/event markers
- **Combat screen** — party HP/stats, enemy group, Cheat/Survive prompts, action selection, combat log
- **Party management** — view characters, equip items, swap active/reserve
- **Inventory** — stash management, equip/drop decisions
- **Recruitment** — one-shot recruit encounter, character preview (CHA-gated info)
- **Shop** — buy/sell, CHA affects prices
- **Death screen** — YOU DIED, run recap, meta-progression banked

### Architecture
- `api/game.py` — facade over the engine. Methods: `start_run()`, `choose_job()`, `enter_zone()`, `start_combat()`, `submit_turn()`, `equip_item()`, `recruit()`, `shop_buy()`
- `ui/tui/app.py` — Textual app, screen management
- `ui/tui/screens/` — one module per screen
- TUI consumes `CombatEvent` objects from the log and renders as text

---

## Phase 3: Full Game Loop

This is the big one that makes it a *game*.

### Systems to Build
- **Zone/area system** — zone level, encounter tables, boss at zone end, region caps on grinding
- **Encounter generation** — enemy group composition from archetype pool, themed per world
- **Recruitment system** — one-shot encounters, randomized recruit stats/scaling, CHA-gated inspection
- **Shop system** — item pool, CHA-modulated prices, per-zone inventory
- **Loot system** — drop tables on enemies (shared pool), money drops, rare/unique from key enemies
- **Run state** — ties zones, party, progression together into a coherent run
- **Save/load** — JSON serialization of run state. Autosave on zone transitions. Death nukes all saves for that run.
- **XP/leveling** — how characters gain levels within a run
- **MC Mimic system** — job swapping, growth rate changes forward, stat history preserved

### Key Files
- `engine/zone.py` — zone generation, encounter tables
- `engine/recruitment.py` — recruit generation, CHA inspection
- `engine/shop.py` — shop economy
- `engine/loot.py` — drop table resolution
- `engine/run.py` — run state management, save/load
- `engine/mimic.py` — MC job swapping

---

## Phase 4: Meta-Progression

### Systems
- **CHA accumulation** — persists across runs, gates information visibility
- **Job unlock system** — milestone-based permanent unlocks
- **Acceleration system** — milestone accelerators, tilt penalty, surrender benefits, perma-boosts
- **Information visibility tiers** — Raw (runs 0-5), Basic scaling (5-10), Full breakdown (20+)
- **Dignified Exit** — end dead runs early, bank partial progress
- **Achievement system** — pairs with permanent acceleration

---

## Phase 5: LLM Integration

### Scope
- Area descriptions on zone entry
- Combat narration (mechanical events -> one-line flavor)
- Shop/event/recruit flavor text
- Death recap (2-3 sentence themed summary)
- CHA modulates prompt parameters (terse at low CHA, rich at high)

### Architecture
- `engine/llm_interface.py` — abstract interface
- Caching strategy TBD (pre-generated vs runtime vs hybrid)
- Model choice TBD

---

## Tech Stack
- Python 3.13+ with pydantic
- PyYAML for data files
- pytest for testing
- uv for package management
- Textual for TUI (Phase 2)
- LLM provider TBD (Phase 5)
