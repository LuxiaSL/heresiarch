# Heresiarch — Agent Guide

## What This Is

Roguelike JRPG engine + TUI + MCP agent player + balance dashboard. Text-based, terminal-rendered, degenerate-builds-win design philosophy. Three mythology-themed worlds (Nordic, Shinto, Abrahamic), mechanically identical with different flavor.

## Running

```bash
uv run heresiarch           # TUI
uv run pytest tests/ -v     # Tests (~450, deterministic, seeded RNG)
uv run python -m heresiarch.tools.sim <subcommand>  # Balance sim tool
uv run python -m heresiarch.agent    # MCP agent player server
uv run python -m heresiarch.dashboard  # FastAPI balance dashboard
```

## Architecture: Where Logic Lives

**The engine has zero I/O.** All state passed in/out. All randomness via injected `random.Random`. This is the most important invariant.

```
src/heresiarch/
  engine/              # PURE LOGIC — no I/O, no UI, no network
    models/            # Pydantic models (state + data). Source of truth for types.
    formulas.py        # ALL game math as pure functions + named constants
    scaling.py         # Level-scaling helpers (stat curves, enemy scaling)
    combat.py          # CombatEngine: phased effect pipeline, turn loop
    passive_handlers.py # Data-driven passive dispatch table (ON_HIT_RECEIVED, etc.)
    game_loop.py       # GameLoop: stateless orchestrator (combat→XP→loot→zones)
    ai.py              # Enemy AI: weighted action tables + conditions
    data_loader.py     # YAML → pydantic models, cross-ref validation
    encounter.py       # Zone template → concrete enemy groups
    loot.py            # Drop resolution (CHA bonuses, overstay penalty)
    shop.py            # Buy/sell with CHA pricing
    recruitment.py     # Candidate generation, CHA-gated inspection
    save_manager.py    # JSON save/load, permadeath deletion

  tui/                 # Textual TUI — renders engine state, collects player input
    app.py             # App shell: holds RunState, GameLoop, screen routing
    screens/           # 16 screens (title through death)
    event_renderer.py  # CombatEvent → display text (verbose/summary)
    widgets/           # Map viewer

  agent/               # MCP server for LLM-as-player
    server.py          # 39 MCP tools, pure pass-through to session
    session.py         # Game session state management, phase gating
    summarizer.py      # Engine state → text for LLM consumption

  tools/               # CLI balance tools
    sim.py             # Sweep, DPR, economy, progression sims + CLI entry
    combat_sim.py      # General-purpose combat simulator (drives real CombatEngine)
    shared.py          # Shared damage computation helpers (sim + dashboard)
    map_tool.py        # Map authoring/visualization
    map_preview.py     # Map preview rendering

  dashboard/           # FastAPI balance dashboard
    app.py             # FastAPI app shell
    core/sim_service.py  # Structured sim functions (returns pydantic models)
    core/config_manager.py  # Runtime formula overrides for balance testing
    core/config_model.py    # Config pydantic models
    core/response_models.py # API response models
    api/               # HTTP endpoints (sim_routes, config_routes, data_routes)

data/                  # YAML game data (shared + per-region)
  jobs/                # 4 starter jobs
  abilities/           # Offensive, defensive, support, passive, innate
  items/               # Weapons, armor, accessories, consumables, scrolls
  enemies/             # Archetypes with action tables
  loot/                # Drop tables
  region_shinto/       # Shinto region content
    zones/             # Zone templates with encounters
    maps/              # ASCII maps (region map, town interior, per-zone)
    towns/             # Town templates (shop tiers, lodge cost params)
```

## Key Invariants

1. **Engine is zero-I/O.** No prints, no file reads, no network calls. GameLoop, CombatEngine, all formulas — pure functions and state transforms.

2. **RunState carries all mutable state.** GameLoop methods take RunState, return new RunState. TUI/agent hold the reference.

3. **CombatState is mutated in-place during combat** but the engine returns it. CombatEngine.process_round() is the only thing that advances combat.

4. **All formulas live in `formulas.py`.** Named constants at module level. Balance passes should only need to edit this file + YAML data. If you find a magic number in combat.py, it should be moved here.

5. **Abilities are data-driven.** AbilityEffect is a flat model with zero-default fields. New effects = new fields, not new subclasses. Passive triggers dispatch through `passive_handlers.py` based on AbilityEffect fields, not ability IDs.

6. **Never check ability IDs in game logic.** Use behavioral flags on AbilityEffect (`survive_lethal`, `applies_taunt`, `applies_mark`, `ap_refund`, `ap_gain`, `grants_surviving`, `grants_invulnerable`, `split_into_templates`, `summon_template_id`) and on StatusEffect (`grants_taunted`, `grants_mark`). The YAML data sets these flags.

7. **Ability sources are tracked.** `CharacterInstance.ability_sources` maps source names (core/innate/breakpoints/equipment/learned) to ability ID lists. When modifying abilities, update the relevant source — don't reconstruct from scratch.

## How To: Add a New Passive Ability

1. Add YAML entry in `data/abilities/` with the right `trigger:` and `category: PASSIVE`
2. If it uses existing effect fields (`stat_buff`, `reflect_percent`, `base_damage`, `ap_refund`, `ap_gain`, `survive_lethal`, `applies_taunt`, `applies_mark`, `grants_surviving`, `grants_invulnerable`, `regen_missing_hp_percent`, `split_into_templates`, `summon_template_id`): **done, zero code changes**
3. If it needs a new behavior: add a field to `AbilityEffect` (in `models/abilities.py`), add handling in the relevant handler function in `passive_handlers.py`
4. If it needs a new trigger condition: add to `TriggerCondition` enum, write a handler function, add to `PASSIVE_DISPATCH` table

## How To: Add a New Active Ability Effect

1. Add field to `AbilityEffect` (zero-default so existing YAML is unaffected)
2. Add handling in the relevant phase method in `combat.py`:
   - Damage modifiers → `_phase_damage_modify`
   - Post-damage reactions → `_phase_post_damage`
   - Buffs/debuffs → `_phase_buff_apply`
   - Utility (heal, gold, status application) → `_phase_utility`

## Combat Effect Pipeline

`_apply_effect()` runs 11 phases in order. Each is a focused 20-50 line method:

```
_phase_damage_calc      → Raw damage from formula
_phase_damage_modify    → Insight, frenzy, surge, chain, mark bonus
_phase_damage_redirect  → Taunt redirect
_phase_damage_reduce    → Survive reduction
_phase_damage_apply     → HP loss, DAMAGE_DEALT event, leech
_phase_split_check      → Mitosis/split on lethal (spawns new enemies)
_phase_post_damage      → ON_HIT_RECEIVED dispatch (retaliate, siphon, thorns)
_phase_death_check      → survive_lethal, death, ON_KILL/ON_ALLY_KO dispatch
_phase_secondary        → DOT/shatter/disrupt (RES-gated)
_phase_buff_apply       → DEF buff, stat buff (+insight amplification)
_phase_utility          → Gold steal, heal, mark, taunt
```

`EffectContext` dataclass threads mutable state (damage, redirected target) through phases.

## Testing

- Tests are in `tests/` — deterministic via seeded `random.Random(42)`
- `conftest.py` provides fixtures: `game_data`, `seeded_rng`, `combat_engine`, premade characters
- `_make_character(game_data, job_id, level, weapon_id)` helper for test characters
- Run combat tests fast: `uv run pytest tests/test_combat.py tests/test_effect_pipeline.py -v`
- All tests must pass before committing. No skipping hooks.

## Balance Sim Tool

The sim tool (`uv run python -m heresiarch.tools.sim <subcommand>`) has multiple analysis modes. The most powerful is `combat`, which drives the **real CombatEngine** with scripted player decisions.

### `combat` — Full combat simulator

Simulates encounters using the actual engine (all passives, frenzy, thorns, insight, enemy AI fire correctly).

```bash
# Berserker survive→cheat cycle through zone 1
uv run python -m heresiarch.tools.sim combat --job berserker --zone zone_01 --cycle "S,S,S,C3"

# Onmyoji insight→bolt cycle against specific enemies
uv run python -m heresiarch.tools.sim combat --job onmyoji --level 5 --enemy fodder_slime --enemy-level 3 --cycle "S,S,A:bolt"

# With potion between encounters 1 and 2
uv run python -m heresiarch.tools.sim combat --job berserker --zone zone_01 --cycle "S,S,S,C3" --between "2:minor_potion"

# With equipment
uv run python -m heresiarch.tools.sim combat --job einherjar --level 10 --zone zone_03 --cycle "A:heavy_strike" --equipment "WEAPON=iron_blade"
```

**Cycle DSL tokens** (comma-separated, case-insensitive):
- `S` — Survive (halve damage, bank 1 AP)
- `A` or `A:ability_id` — Normal turn with ability (default: basic_attack)
- `C{N}` or `C{N}:ability_id` — Cheat spending N AP (1 primary + N extra attacks)
- `I:item_id` — Use consumable mid-combat

**Output shows per-round**: player HP, AP banked, cheat debt, insight stacks, enemy HP, damage events (frenzy chains, thorns, retaliate, healing).

### Other sim subcommands

- `sweep` — Parameter sweep across level/stat ranges
- `crossover` — Find crossover points between two ability curves
- `build` — Full build analysis (job + equipment + abilities)
- `converter` — Unit conversion helpers for balance math
- `sigmoid` — Sigmoid curve visualization for scaling tuning
- `xp-curve` — XP/level at each zone exit (rush/moderate/grind)
- `progression` — Full run: level, gold, weapons, abilities per zone
- `ability-dpr` — DPR tables for offensive abilities across levels
- `ability-compare` — Side-by-side ability comparison with crossover
- `job-curve` — Per-job stat progression curves
- `economy` — Gold drops, overstay decay, pilfer analysis
- `enemy-stats` — Enemy stat tables at each zone level
- `shop-pricing` — Shop affordability check
- `lodge-tuning` — Lodge rest cost analysis

### Architecture note

`combat` lives in `tools/combat_sim.py` (CombatSimulator class). It builds real `CharacterInstance` + `EnemyInstance` objects and calls `CombatEngine.initialize_combat()` / `process_round()` directly. This means any engine change (new passive, formula tweak, new mechanic) is automatically reflected in sim output — no reimplementation needed.

## Common Pitfalls

- **Don't put game logic in TUI or agent.** If you're computing damage, checking ability conditions, or modifying RunState outside the engine, stop. Add an engine method.
- **Don't hardcode ability IDs.** Use behavioral flags on AbilityEffect/StatusEffect. The dispatch table in passive_handlers.py handles the rest.
- **Don't reconstruct ability lists from scratch.** Use `ability_sources` and update only the relevant source key.
- **`STASH_LIMIT` lives in `models/party.py`.** Don't redefine it.
- **Status flags (`taunted_by`, `is_marked`) are derived from StatusEffect fields** (`grants_taunted`, `grants_mark`) during `_tick_statuses`. Don't string-match status IDs.
- **Retaliate uses its own effect data** (`base_damage: 5, scaling_coefficient: 0.5`), not a basic_attack lookup.

## Design Docs

`design/` contains the game designer's intent documents with designer quotes anchoring decisions. These are the "why" — the code is the "what". When design intent and implementation diverge, flag it rather than silently changing either.
