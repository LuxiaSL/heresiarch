# Agent Player Interface — Design Spec

> Scaffold for designing an MCP server or tool-use interface that lets AI agents play Heresiarch for automated balance testing, QA, and build discovery.

## Goal

Let AI agents play full runs of Heresiarch autonomously — making all the same decisions a human player would — then collect data on:
- Which builds/strategies emerge as dominant
- Where runs consistently die (difficulty spikes)
- Gold economy health (do agents hoard? overspend? starve?)
- Ability usage patterns (which abilities are never picked?)
- Zone progression pacing (how long do runs take, where do they stall?)
- Edge cases and bugs (states that shouldn't be reachable)

## Architecture Context

Heresiarch's engine is **pure functions with no I/O**:

```
GameLoop.new_run(run_id, name, job_id) → RunState
GameLoop.enter_zone(run, zone_id) → RunState
GameLoop.get_next_encounter(run) → list[EnemyInstance]
CombatEngine.initialize_combat(characters, enemies) → CombatState
CombatEngine.process_round(state, decisions, templates) → CombatState
GameLoop.resolve_combat_result(run, result) → (RunState, LootResult)
GameLoop.apply_loot(run, loot, selected_items) → RunState
GameLoop.advance_zone(run) → RunState
GameLoop.equip_item(run, char_id, item_id, slot) → RunState
GameLoop.use_teach_scroll(run, item_id, char_id) → RunState
GameLoop.use_consumable(run, item_id, char_id) → RunState
ShopEngine.buy_item(run, item_id) → RunState
ShopEngine.sell_item(run, item_id) → RunState
GameLoop.leave_zone(run) → RunState
GameLoop.mc_swap_job(run, job_id) → RunState
```

All state lives in `RunState` (pydantic, JSON-serializable). All randomness through injected `random.Random`. The TUI is just a renderer — no game logic lives there.

## Decision Points

An agent playing a full run must make these decisions:

### 1. Run Setup
- **Pick starting job**: einherjar, berserker, martyr, onmyoji
- Strategy: each has different growth curves and innate abilities

### 2. Zone Selection (between zones)
- **Which zone to enter**: from unlocked set
- **Whether to overstay**: keep fighting in a cleared zone (diminishing returns)
- **When to leave**: cut losses on a bad zone vs push for the boss

### 3. Combat (per round, per character)
- **Cheat/Survive/Normal**: bank AP for defense, spend AP for burst, or just act
- **If Cheat**: how many AP to spend (1-3)
- **Primary action**: which ability to use
- **Target selection**: which enemy (or ally for support abilities)
- **Item use**: use a consumable instead of attacking
- **Partial actions** (SPD bonus): additional weaker actions

### 4. Post-Combat
- **Loot selection**: which dropped items to keep (stash limit = 10)
- **Recruitment**: recruit candidate or pass (when offered)

### 5. Party Management (between encounters)
- **Equipment**: equip/unequip items across 4 slots per character
- **Scrolls**: use teach scrolls on which character
- **Party composition**: swap active/reserve members
- **Shopping**: buy/sell at zone shops
- **MC job swap**: mimic a recruited party member's job

## Information Available to Agent

At any decision point, the agent can observe:

**RunState**: party (characters with stats, abilities, equipment, HP), stash, money, current zone, zones completed, zone progress

**CombatState**: all combatant HP/stats/statuses, action points, cooldowns, turn order, combat log (full event history)

**GameData** (static): all jobs, abilities, items, enemies, zones, drop tables — the complete rulebook

## Proposed Interface Shapes

### Option A: MCP Server (tool-use)
Expose game actions as MCP tools. Agent calls tools, receives state back.

```
Tools:
  new_run(job_id) → RunState summary
  get_state() → current RunState summary
  get_available_zones() → list of unlocked zones with details
  enter_zone(zone_id) → zone info
  fight() → CombatState summary (enemies, party HP)
  combat_decision(decisions: dict) → round result events
  pick_loot(item_ids: list) → updated stash
  equip(char_id, item_id, slot) → updated character
  shop_buy(item_id) / shop_sell(item_id)
  use_scroll(item_id, char_id)
  leave_zone()
```

Pro: Natural for Claude/tool-use agents. Each tool call is one decision.
Con: Many round-trips per combat. Token-heavy for long runs.

### Option B: Batch/Script Interface
Agent produces a full run strategy as a script, engine executes it.

```python
strategy = RunStrategy(
    job="einherjar",
    zone_order=["zone_01", "zone_02", ...],
    combat_policy=AggressiveCombatPolicy(),  # or custom per-zone
    loot_policy=KeepUpgradesPolicy(),
    shop_policy=BuyWeaponFirstPolicy(),
)
results = simulate_run(strategy, seed=42)
```

Pro: Fast, no round-trips. Can batch thousands of runs.
Con: Less flexible. Agent can't react to mid-run surprises.

### Option C: Hybrid — Reactive Loop
Agent provides a policy function that's called at each decision point.

```python
class AgentPlayer:
    def choose_zone(self, run: RunState, available: list[ZoneTemplate]) -> str: ...
    def combat_round(self, combat: CombatState, run: RunState) -> dict[str, PlayerTurnDecision]: ...
    def pick_loot(self, loot: LootResult, run: RunState) -> list[str]: ...
    def manage_party(self, run: RunState) -> list[Action]: ...
```

Pro: Full reactivity, clean interface, fast (no serialization overhead).
Con: Requires Python agent implementation, not directly usable from Claude tool-use.

### Option D: Hybrid MCP + Batch
MCP for exploration/learning. Batch for mass simulation once strategy is learned.

## Key Design Questions

1. **Observation granularity**: Should the agent see raw numbers (STR=75, DEF=60) or derived analysis ("this weapon does 95 damage against this enemy")? Raw is more flexible but requires the agent to do math.

2. **Combat pacing**: One tool call per round? Per character? Per action? Fewer calls = fewer tokens but less granular control.

3. **State representation**: Full JSON RunState? Summarized natural language? Structured but compressed? Token budget matters for long runs.

4. **Multi-agent**: Could different agents play different builds in parallel? Tournament-style balance testing?

5. **Metrics collection**: What data do we want out? Win rate per job? Gold curve? Death zone distribution? Ability usage heatmap? Build diversity index?

6. **Seed control**: Deterministic runs (same seed = same enemy encounters, same drops) for A/B testing builds against identical scenarios.

## Existing Infrastructure to Leverage

- `RunState` is already JSON-serializable (pydantic `model_dump_json`)
- `CombatState` has full event log with typed `CombatEvent` objects
- `BattleRecord` tracks per-run combat history (damage, healing, ability usage)
- `SaveManager` can snapshot any point in a run
- Sim tool (`python -m heresiarch.tools.sim`) already does economy/progression modeling
- All randomness is injectable (`random.Random` with seed)
- `event_renderer.py` already translates combat events to readable text

## Success Criteria

A good agent player interface should:
1. Let an agent play a full run (zone 1 → zone 15 or death) without human input
2. Collect structured data on every decision and outcome
3. Support running hundreds of seeded runs for statistical balance analysis
4. Be simple enough that a fresh agent can learn the interface in one conversation
5. Produce actionable balance insights (not just "agent won/lost")
