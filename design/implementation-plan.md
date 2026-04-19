# Implementation Plan

## Current State

Engine, game loop, TUI, agent player, balance dashboard, and sim tools are all functional. ~300 deterministic tests. Code health refactor completed (phased effect pipeline, passive dispatch, ability source tracking).

### What Exists

```
heresiarch/
    src/heresiarch/engine/
        models/              # 12 pydantic model files — all game entities
            stats.py         # StatBlock, GrowthVector, StatType
            abilities.py     # Ability, AbilityEffect, DamageQuality, triggers, behavioral flags
            items.py         # Item (equipment + consumables), scaling, converters
            jobs.py          # JobTemplate, CharacterInstance (with ability_sources)
            enemies.py       # EnemyTemplate, EnemyInstance, ActionTable
            combat_state.py  # CombatState, CombatantState, CombatEvent, StatusEffect
            party.py         # Party, STASH_LIMIT
            loot.py          # DropTable, LootResult
            zone.py          # ZoneTemplate, EncounterTemplate, ZoneState
            run_state.py     # RunState, CombatResult
            battle_record.py # BattleRecord, EncounterRecord, RoundRecord
            region_map.py    # RegionMap, ZoneAnchor
        formulas.py          # All pure math + named constants (damage, HP, XP, frenzy, insight, thorns, mark, etc.)
        combat.py            # CombatEngine — phased effect pipeline, EffectContext
        passive_handlers.py  # PassiveContext + dispatch table for all TriggerConditions
        ai.py                # EnemyAI — weighted action tables, conditions, targeting
        scaling.py           # Item scaling evaluation wrappers
        encounter.py         # EncounterGenerator — zone templates → enemy groups
        loot.py              # LootResolver — drop tables, CHA bonus, overstay penalty
        shop.py              # ShopEngine — buy/sell with CHA pricing
        recruitment.py       # RecruitmentEngine — randomized growth, CHA inspection
        game_loop.py         # GameLoop — orchestrator + try_recruitment, ability source tracking
        save_manager.py      # SaveManager — JSON save/load, permadeath, autosave
        data_loader.py       # YAML → pydantic, cross-reference validation
    tui/
        app.py               # Textual app, state holder, screen routing
        screens/             # 14 screens (title, job_select, zone_select, zone, combat,
                             #   post_combat, party, inventory, shop, recruitment,
                             #   death, victory, load)
        event_renderer.py    # CombatEvent → RenderedEvent (verbose/summary, colors, delays)
        widgets/map_viewer.py # Interactive zone map
    agent/
        server.py            # 30 MCP tools (zero game logic, pure pass-through)
        session.py           # GameSession: phase-gated state management
        summarizer.py        # Engine state → formatted text for LLM consumption
    tools/
        sim.py               # CLI sim: sweep, DPR, economy, xp-curve, progression, etc.
        shared.py            # Shared damage computation helpers (sim + dashboard)
        map_tool.py          # Map authoring + visualization
    dashboard/
        app.py               # FastAPI app factory
        core/sim_service.py  # Structured sim functions (pydantic response models)
        core/config_manager.py # Runtime formula overrides for balance testing
        api/                 # HTTP route handlers
    data/
        jobs/                # 4 starter jobs (einherjar, onmyoji, martyr, berserker)
        abilities/           # 36 abilities across 5 YAML files
        items/               # 26 items (weapons, armor, accessories, consumables, scrolls)
        enemies/             # 7 archetypes with action tables
        loot/                # Drop tables per archetype
        zones/               # 7 zone templates (shinto slime curriculum, zones 1-15)
    tests/                   # ~300 tests across 13 test files
    design/                  # 11 design docs + this plan
```

---

## Completed Phases

### Phase 1: Engine Core
Combat, formulas, AI, models, data loader. Deterministic, fully tested.

### Phase 3: Game Loop
Zones, encounters, loot, XP, shops, recruitment, saves, equipment, consumables, MC job swap, HP persistence, permadeath.

### Phase 2: TUI
14 Textual screens. Sequential JRPG-style combat input, line-by-line event rendering, battle history tracking, autosave, permadeath. Map viewer widget.

### Agent Player
MCP server with 30 tools. Phase-gated session management. Summarizer formats engine state for LLM consumption.

### Balance Dashboard
FastAPI app with runtime formula overrides. Mirrors sim.py functionality with structured JSON responses.

### Code Health Refactor (Session 4)
- Phased effect pipeline (10 phases via EffectContext)
- Passive handler dispatch table (7 trigger conditions, data-driven)
- Behavioral flags replace hardcoded ability IDs
- Formula constants consolidated
- Ability source tracking
- In-combat item use centralized in engine
- Recruitment logic extracted from TUI to engine

---

## Phase 4: Meta-Progression (Next)

### Systems
- **CHA accumulation** — persists across runs, gates information visibility
- **Job unlock system** — milestone-based permanent unlocks
- **Acceleration system** — milestone accelerators, tilt penalty, surrender benefits, perma-boosts
- **Information visibility tiers** — Raw (runs 0-5), Basic scaling (5-10), Full breakdown (20+)
- **Dignified Exit** — end dead runs early, bank partial progress
- **Achievement system** — pairs with permanent acceleration

### Architecture Implications
- New `MetaState` model persisted separately from RunState
- MetaState survives permadeath
- CHA modifies existing systems (shop pricing, recruit inspection) — already wired
- Acceleration modifiers feed into formulas.py constants

---

## Phase 5: LLM Integration

### Scope
- Area descriptions on zone entry
- Combat narration (mechanical events → one-line flavor)
- Shop/event/recruit flavor text
- Death recap (2-3 sentence themed summary)
- CHA modulates prompt parameters (terse at low CHA, rich at high)

### Architecture
- `engine/llm_interface.py` — abstract interface
- Caching strategy TBD (pre-generated vs runtime vs hybrid)
- Model choice TBD

---

## Post-Run Report (planned)

`BattleRecord` is populated by the TUI during every run but barely consumed — death and victory screens don't show structured run analytics. A dedicated Run Report would close that feedback loop and also provide structured input for the Phase 5 LLM death recap.

### Scope
- TUI "Run Report" screen surfaced from death.py and victory.py
- `sim report <save-file>` CLI for post-hoc analysis of a run
- Stats: peak DPR, Cheat:Survive:Normal ratio, biggest single hit, most-used ability, HP low-water mark, gold by source (drops / pilfer / shop-sale), rounds per zone, per-encounter result, character deaths timeline
- Structured data ready to feed Phase 5 death-recap prompt

### Architecture
- `engine/run_report.py` — pure function: RunState + BattleRecord → RunReportSummary (pydantic)
- TUI screen renders summary; CLI dumps JSON + pretty-printed table
- Lives in engine (zero-I/O) so sim/dashboard can use it the same way

---

## Remaining Polish / Balance

- **CHA system** — mechanically wired but invisible to player. Needs meta-progression.
- **Town/healing system** — HP persists between zones, no healing mechanism yet.
- **Frenzy formula variants** — test 2*x and 2^x alongside current 1.5^x
- **Martyr thorns playtest** — implemented but needs balance verification
- **Berserker survivability** — 30 base HP too low for multi-enemy encounters
- **Potion economy** — glass cannon builds need more accessible healing
