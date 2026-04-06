# Implementation Plan

## Current State (Phases 1 + 3 Complete)

The engine core and full game loop are built and tested. **180 passing tests** validate combat, formulas, scaling, XP, loot, shops, recruitment, saves, equipment, consumables, and end-to-end zone progression.

### What Exists

```
heresiarch/
    src/heresiarch/engine/
        models/              # 10 pydantic model files — all game entities
            stats.py         # StatBlock, GrowthVector, StatType
            abilities.py     # Ability, AbilityEffect, DamageQuality, triggers
            items.py         # Item (equipment + consumables), scaling, converters
            jobs.py          # JobTemplate, CharacterInstance (with growth_history)
            enemies.py       # EnemyTemplate, EnemyInstance, ActionTable
            combat_state.py  # CombatState, CombatantState, CombatEvent, Cheat/Survive
            party.py         # Party (active/reserve/stash/money/cha)
            loot.py          # DropTable, LootResult
            zone.py          # ZoneTemplate, EncounterTemplate, ZoneState
            run_state.py     # RunState, CombatResult (with surviving HP)
        formulas.py          # All pure math — damage, HP, XP, shop pricing, money drops
        combat.py            # CombatEngine — turns, Cheat/Survive, statuses, events
        ai.py                # EnemyAI — weighted action tables, conditions, targeting
        scaling.py           # Item scaling evaluation
        encounter.py         # EncounterGenerator — zone templates → enemy groups
        loot.py              # LootResolver — drop tables, CHA bonus, shared pool
        shop.py              # ShopEngine — buy/sell with CHA pricing
        recruitment.py       # RecruitmentEngine — randomized growth, CHA inspection
        game_loop.py         # GameLoop — the orchestrator (combat→XP→loot→equip→save)
        save_manager.py      # SaveManager — JSON save/load, permadeath, autosave
        data_loader.py       # YAML → pydantic, cross-reference validation
    data/
        jobs/                # 4 starter jobs
        abilities/           # 33 abilities (innate, offensive, defensive, support, passive)
        items/               # 13 items (weapons, armor, accessories, consumables)
        enemies/             # 5 enemy archetypes with action tables
        loot/                # Drop tables per archetype
        zones/               # 7 zone templates (slime curriculum zones 1-15)
    tests/                   # 180 tests across 12 test files
    design/                  # 9 design docs + this plan
```

### Verified Behaviors (Phase 1)
- HP calculations match design doc snapshots
- Item scaling crossovers at correct stat values
- Taunt redirects, Retaliate counters, Frenzy stacks, DOT bypasses DEF
- Survive halves damage, Cheat creates action debt
- SPD bonus actions at threshold
- Enemy AI conditional weight shifts
- Party vs fodder is a stomp, 1v1 Einherjar vs Brute is ~4 rounds

### Verified Behaviors (Phase 3)
- XP rewards scale with zone level × enemy budget, overlevel penalty at 50%/level
- Level thresholds follow quadratic curve (level² × 10)
- Loot drops respect seeded RNG, CHA modifies drop chances
- Zone encounter generation produces correct enemy groups per slime curriculum
- Boss encounters have 1.5× budget multiplier
- Shop buy/sell with CHA pricing (half price at CHA 100)
- Recruitment generates valid candidates with ±2 growth variance
- CHA-gated inspection: MINIMAL (<30), MODERATE (30-69), FULL (≥70)
- Equip/unequip swaps items between stash and character slots
- Party swap between active and reserve roster
- Consumables: potions heal flat HP, elixir heals to full, single-use
- Safe zone healing: full HP restore between zones
- HP persistence: surviving HP carries between encounters within a zone
- MC Mimic job swap: growth history preserved, stats accumulate across segments
- Save/load round-trips via pydantic JSON serialization
- Death nukes all saves for the run (permadeath contract)
- Full zone clear: start run → fight encounters → gain XP → collect loot → clear zone

---

## Phase 2: TUI (Textual) — NEXT UP

Put a playable face on the engine. The game loop is fully functional; this phase renders it.

### Architecture

The engine is already structured for this. `GameLoop` is the stateless orchestrator — the TUI just needs to call its methods and render the results.

```
src/heresiarch/
    tui/
        app.py              # Textual App subclass, screen routing
        screens/
            title.py        # New run / continue / quit
            job_select.py   # Pick starting job (+ world theme placeholder)
            zone.py         # Zone overview: encounters remaining, shop/recruit available
            combat.py       # THE big screen: party stats, enemies, Cheat/Survive, actions, log
            party.py        # View characters, equip/unequip, swap active/reserve
            inventory.py    # Stash management, use consumables
            shop.py         # Buy/sell with CHA-adjusted prices
            recruitment.py  # Inspect candidate (CHA-gated), recruit or pass
            death.py        # YOU DIED + run recap
        widgets/
            stat_bar.py     # HP bar, stat display
            combat_log.py   # Scrolling event log from CombatEvent stream
            item_card.py    # Item display with scaling info
```

### Key Patterns
- **GameLoop is the single source of truth.** TUI calls GameLoop methods, receives updated RunState, renders it. No game logic in the UI layer.
- **CombatEvent stream → combat log.** The combat engine already emits typed events. The TUI just formats them as text lines.
- **Textual's screen stack** maps naturally to game flow: title → job select → zone → combat → zone → ... → death.
- **RunState is serializable.** Save/load already works. The TUI just needs save/load buttons that call SaveManager.

### Suggested Build Order
1. **App shell + title screen** — Textual app with screen routing, new run / quit
2. **Job select** — pick a job, start a run, see the RunState created
3. **Zone screen** — show zone name, encounters remaining, buttons: fight next / shop / manage party
4. **Combat screen** — this is the big one. Render party + enemies, Cheat/Survive prompt, action selection, combat log. Wire to CombatEngine.
5. **Post-combat** — XP summary, loot drops, item selection
6. **Party/inventory screens** — equip/unequip, swap roster, use consumables
7. **Shop screen** — buy/sell menu with CHA-adjusted prices
8. **Recruitment screen** — candidate preview, CHA-gated info reveal, recruit or pass
9. **Death screen** — YOU DIED, run recap, back to title

### What's Needed from Textual
- `pip install textual` (add to pyproject.toml)
- Textual's `App`, `Screen`, `Widget`, `Static`, `Button`, `DataTable`, `Header`, `Footer`
- CSS-like styling via `.tcss` files or inline styles
- Key bindings for common actions

### Open Questions for Phase 2
- **Combat turn input UX**: how to prompt Cheat/Survive + action + target selection cleanly in a terminal? Could be sequential prompts, could be a modal, could be hotkeys.
- **Combat log verbosity**: show every CombatEvent, or summarize? Probably configurable.
- **Auto-battle for trivial encounters?** Skip animation for fodder stomps? Design question.

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
- Combat narration (mechanical events → one-line flavor)
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
