# Heresiarch — Agent Player Guide

> Everything an AI agent needs to play Heresiarch through the MCP server.

## Quick Start

The MCP server exposes Heresiarch as tool calls. You play by calling tools to start runs, enter zones, fight encounters, manage your party, and make combat decisions.

```json
// .mcp.json (in your project root)
{
  "mcpServers": {
    "heresiarch": {
      "command": "/path/to/heresiarch/.venv/bin/python",
      "args": ["-m", "heresiarch.agent"],
      "cwd": "/path/to/heresiarch"
    }
  }
}
```

On startup, the server auto-loads the last autosave if one exists.

## The Game

Heresiarch is a roguelike JRPG. You pick a job, enter zones, fight encounters, collect loot, and push deeper. Death is permanent — you lose the run. Zones get harder. Bosses are skill checks that test your resource management and combat tactics.

**Goal:** Clear all 7 zones. Each zone has 5-7 encounters with a boss at the end.

**Jobs:** einherjar (STR/DEF tank), berserker (STR/SPD glass cannon), martyr (DEF/RES wall), onmyoji (MAG caster).

## Game Flow

```
new_run → enter_zone → fight → submit_decisions (repeat) → pick_loot
                     → fight → ... → boss → pick_loot → leave_zone
                     → enter_zone (next zone) → ...
```

### Phases

The game tracks your current phase. Each phase allows specific tools:

| Phase | What's Happening | Key Tools |
|-------|-----------------|-----------|
| SETUP | No run started | `new_run`, `load_run`, lookups |
| ZONE_SELECT | Between zones | `enter_zone`, `list_zones`, party management, shop |
| IN_ZONE | Inside a zone | `fight`, `shop_browse/buy/sell`, `leave_zone` |
| COMBAT | Mid-fight | `submit_decisions`, `get_combat_state` |
| POST_COMBAT | After winning | `pick_loot` |
| RECRUITING | Candidate appeared | `recruit`, `inspect_candidate` |
| DEAD | Party wiped | `get_run_summary`, `new_run` |

Calling a tool outside its valid phase returns a clear error with available alternatives.

## Combat System

### The Triad: Survive / Normal / Cheat

Every round, each character chooses one mode:

**Survive** — No action. Bank 1 AP (max 3). Take 50% less damage. Passive abilities (like retaliate) still trigger.

**Normal** — Take one action: use an ability, basic attack, or use an item from stash.

**Cheat** — Take one action PLUS extra actions from banked AP (1 AP = 1 extra action). Each extra can be an ability or item use. Incurs cheat debt — enemies deal bonus damage while you're in debt. Debt recovers 1 per turn.

### The Rhythm

The core skill loop:

1. **Survive** to bank AP and reduce incoming damage
2. **Normal** to deal damage
3. **Survive** to bank more AP
4. When you need to heal: **Cheat** with potion as primary action + attack as extra (heal AND damage in one turn)
5. **Survive** next round to absorb the debt-boosted hit at half damage
6. Repeat

Against fodder: Survive until enemies are in kill range, then Cheat to wipe them all on your turn (saves the last round of chip damage).

Against bosses: Interleave Survive and Normal. Use Cheat for potion+attack combos when HP gets low. Never raw-Cheat a boss for pure burst — the debt makes their next hit lethal.

### Decision Format

```json
{
  "character_id": {
    "mode": "normal",          // "normal", "survive", or "cheat"
    "action": "basic_attack",  // ability_id or "use_item"
    "target": "enemy_id",      // combatant ID

    // Only for mode: "cheat"
    "ap_spend": 1,
    "cheat_extras": [
      {"ability": "basic_attack", "target": "enemy_id"}
    ],

    // Only for action: "use_item"
    "item_id": "minor_potion",
    "target": "character_id"   // who to heal
  }
}
```

**Survive needs no fields beyond mode:**
```json
{"mc_einherjar": {"mode": "survive"}}
```

**Normal attack:**
```json
{"mc_einherjar": {"mode": "normal", "action": "basic_attack", "target": "fodder_slime_0"}}
```

**Cheat with potion + attack (the boss combo):**
```json
{"mc_einherjar": {
  "mode": "cheat", "ap_spend": 1,
  "action": "use_item", "item_id": "potion", "target": "mc_einherjar",
  "cheat_extras": [{"ability": "thrust", "target": "brute_oni_0"}]
}}
```

**Multi-character decisions:**
```json
{
  "mc_einherjar": {"mode": "normal", "action": "thrust", "target": "caster_kitsune_0"},
  "recruit_martyr_1274": {"mode": "normal", "action": "taunt", "target": "recruit_martyr_1274"}
}
```

All living characters must have a decision each round.

## Key Mechanics

### Damage
- **Physical:** `ability_base + coefficient * STR + weapon_bonus - target_DEF * 0.5`
- **Magical:** `ability_base + coefficient * MAG + weapon_bonus` (NO reduction from any stat)
- **DEF** halves physical damage. Pierce abilities ignore a percentage of DEF.
- **RES** does NOT reduce magic damage. It only gates secondary effects (debuffs).

### HP
- `max_hp = base_hp + hp_growth * level + effective_DEF * 1.5`
- DEF contributes significantly to total HP pool.
- No free healing between zones. HP persists. Potions are the only way to heal.

### Items in Combat
- Using an item costs your primary action for the round (no attack).
- Using an item as a Cheat extra costs one AP but lets you attack AND heal.
- Minor Potion heals 50 HP (30g). Potion heals 150 HP (80g).

### XP & Leveling
- XP per kill = zone_level * enemy_budget_multiplier
- Each zone has an XP cap level — beyond it, XP diminishes rapidly
- Level N requires N^2 * 10 cumulative XP

### Retaliate (Einherjar Passive)
- Triggers on every hit received, even during Survive
- Scales with STR and weapon
- Hits the attacker for counter-damage
- With Leech Fang equipped, also heals per trigger
- Scales with enemy count — more attackers = more retaliates = more DPS

## Tool Reference

### Run Management
| Tool | Description |
|------|-------------|
| `new_run(name, job_id, seed?)` | Start new run. Jobs: einherjar, berserker, martyr, onmyoji |
| `get_state()` | Current state summary (adapts to phase) |
| `save_run(slot?)` | Save to disk. Default slot: "autosave" |
| `load_run(slot?)` | Load from disk |
| `list_saves()` | Show available saves |

### Zone Navigation
| Tool | Description |
|------|-------------|
| `list_zones()` | Show available zones |
| `enter_zone(zone_id)` | Enter a zone |
| `leave_zone()` | Exit zone (progress saved) |
| `get_zone_status()` | Zone progress and encounter list |

### Combat
| Tool | Description |
|------|-------------|
| `fight()` | Start next encounter |
| `submit_decisions(decisions)` | Submit one round of combat decisions |
| `get_combat_state()` | Re-fetch current combat state |

### Post-Combat
| Tool | Description |
|------|-------------|
| `pick_loot(item_ids)` | Keep items from drops. `[]` for nothing |
| `recruit(accept)` | Accept/decline recruitment candidate |
| `inspect_candidate()` | View candidate details (CHA-gated) |

### Party Management
| Tool | Description |
|------|-------------|
| `party_status()` | Full party details |
| `equip(character_id, item_id, slot)` | Equip from stash. Slots: WEAPON, ARMOR, ACCESSORY_1, ACCESSORY_2 |
| `unequip(character_id, slot)` | Unequip to stash |
| `swap_roster(active_id?, reserve_id?)` | Swap active/reserve |
| `use_scroll(item_id, character_id)` | Teach permanent ability |
| `use_consumable(item_id, character_id)` | Use potion etc. (out of combat) |
| `mc_swap_job(job_id)` | Change MC's job |

### Shopping
| Tool | Description |
|------|-------------|
| `shop_browse()` | View shop with CHA-adjusted prices |
| `shop_buy(item_id)` | Buy item |
| `shop_sell(item_id)` | Sell from stash |

### Game Knowledge
| Tool | Description |
|------|-------------|
| `lookup_job(job_id)` | Job growth, abilities, role |
| `lookup_ability(ability_id)` | Ability effects and scaling |
| `lookup_item(item_id)` | Item scaling and properties |
| `lookup_enemy(enemy_id)` | Enemy stats, action table, drops |
| `lookup_zone(zone_id)` | Zone encounters, shop, requirements |
| `lookup_formula(topic)` | Game formulas. Topics: damage, res_gate, hp, xp, bonus_actions, shop_pricing, overstay, cheat_survive, scaling_types |

### Notes & Analytics
| Tool | Description |
|------|-------------|
| `save_note(key, content)` | Persist knowledge across runs |
| `read_notes()` | Read all saved notes |
| `get_battle_record()` | Combat statistics |
| `get_run_summary()` | Full end-of-run report |

## Strategy Primer

### Zone 1 (the tutorial wall)

- You WILL die. Multiple times. This is intended.
- Gold buys potions (30g each), not weapons (100g+). Potions are the skill check.
- Survive through all fodder to conserve HP. Cheat-finish when enemies are low.
- Boss (Alpha Slime): heavy_strike hits for ~35 at Lv2. Interleave Survive and Normal. Potion when HP drops below 40. Use the Cheat+potion combo to heal and attack in one turn.
- Save ALL gold for boss potions. Target: 2-3 potions minimum.

### Target Priority

1. **Caster Kitsune** — magic damage ignores DEF. Kill immediately.
2. **Support Tanuki** — heals allies. Kill before it undoes your damage.
3. **Brute Oni** — high DEF, use thrust (PIERCE). Slow, hits hard but your DEF handles it.
4. **Speeder Tengu** — fast but fragile, dies to retaliate.
5. **Fodder Slime** — retaliate handles them passively.

### Resource Management

- HP does NOT heal between zones. Every point of chip damage from fodder is HP you don't have for the boss.
- Potions used before the boss are potions you don't have FOR the boss.
- Buy armor (Iron Guard, 120g) as soon as you can afford it. DEF scaling is multiplicative with HP.
- Leech Fang (accessory, 15% life steal) makes Einherjar nearly unkillable against physical enemies.

### Using Notes

Save what you learn. Every death should produce a note:

```
save_note("alpha_slime", "heavy_strike = 35 dmg. 80% usage. Need 2+ potions. Survive/Normal rhythm.")
save_note("zone_01_economy", "~70g before boss. 2 potions = 60g. Don't waste on fodder.")
```

Read notes at the start of each run:
```
read_notes()
```

This is your meta-progression. Knowledge carries forward even when runs don't.
