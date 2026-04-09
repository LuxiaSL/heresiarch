# Agent Player Interface — Implementation Design

> Extends `agent-player-spec.md` with concrete interface shapes, state formats, and tool definitions. The goal: Claude plays Heresiarch with all the same decisions a human makes, ergonomically, and we collect structured balance data from the runs.

## Architecture

```
┌─────────────────────────────────────────────┐
│              MCP Server (agent/)             │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ GameSession  │  │  StateSummarizer     │  │
│  │  - GameLoop  │  │  - run_overview()    │  │
│  │  - CombatEng │  │  - combat_view()     │  │
│  │  - ShopEng   │  │  - loot_view()       │  │
│  │  - RunState  │  │  - party_view()      │  │
│  │  - CombatSt  │  │  - shop_view()       │  │
│  │  - GameData  │  │  - zone_select_view()│  │
│  └──────┬───────┘  └──────────┬───────────┘  │
│         │                     │              │
│  ┌──────┴─────────────────────┴───────────┐  │
│  │         Tool Handlers (tools.py)        │  │
│  │  Validates phase → calls engine →       │  │
│  │  updates state → returns summary        │  │
│  └─────────────────────────────────────────┘  │
│                                             │
│  ┌─────────────────────────────────────────┐  │
│  │       Analytics Collector               │  │
│  │  Hooks into every state transition,     │  │
│  │  builds RunReport at end of run         │  │
│  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
          ▲                          ▲
          │ MCP protocol             │ Direct Python
          │ (tool calls)             │ (batch runs)
          │                          │
   ┌──────┴──────┐           ┌──────┴──────┐
   │ Claude Agent │           │ Batch Runner│
   │ (playtester) │           │ (policies)  │
   └─────────────┘           └─────────────┘
```

**Key principle:** The MCP server is a thin translation layer. All game logic stays in the engine. The server's jobs are:
1. Track game phase (what actions are legal right now)
2. Translate agent decisions into engine calls
3. Summarize state for the agent (token-efficient text)
4. Collect analytics data

---

## Game Phase State Machine

The agent's experience is governed by a phase system. Each phase defines which tools are available.

```
                    ┌──────────┐
            ┌──────►│  SETUP   │
            │       └────┬─────┘
            │            │ new_run()
            │       ┌────▼─────────┐
        game_over   │ ZONE_SELECT  │◄────────────────┐
            │       └────┬─────────┘                  │
            │            │ enter_zone()               │
            │       ┌────▼─────────┐                  │
            │       │   IN_ZONE    │◄──────┐          │
            │       └────┬─────────┘       │          │
            │            │ fight()         │          │
            │       ┌────▼─────────┐       │          │
            │       │   COMBAT     │───────┘          │
            │       └────┬─────────┘   (defeat but    │
            │            │ combat ends  not dead—      │
            │       ┌────▼─────────┐   back to zone)  │
            │       │ POST_COMBAT  │───────┘          │
            │       └────┬─────────┘   (loot done,    │
            │            │              advance zone)  │
            │            ├─── recruitment? ───┐       │
            │       ┌────▼─────────┐    ┌────▼────┐   │
            │       │   IN_ZONE    │    │RECRUITING│   │
            │       └────┬─────────┘    └────┬────┘   │
            │            │ leave_zone()      │        │
            │            └───────────────────┴────────┘
            │
            │       ┌──────────┐
            └──────►│   DEAD   │
                    └──────────┘
```

### Phase → Available Tools

| Phase | Available Tools |
|-------|----------------|
| **SETUP** | `new_run`, `lookup_*` |
| **ZONE_SELECT** | `list_zones`, `enter_zone`, `party_status`, `equip`, `unequip`, `swap_roster`, `use_scroll`, `use_consumable`, `mc_swap_job`, `get_battle_record`, `lookup_*` |
| **IN_ZONE** | `fight`, `party_status`, `equip`, `unequip`, `swap_roster`, `use_scroll`, `use_consumable`, `shop_browse`, `shop_buy`, `shop_sell`, `leave_zone`, `get_zone_status`, `lookup_*` |
| **COMBAT** | `submit_decisions`, `get_combat_state`, `lookup_*` |
| **POST_COMBAT** | `pick_loot`, `lookup_*` |
| **RECRUITING** | `inspect_candidate`, `recruit`, `lookup_*` |
| **DEAD** | `get_battle_record`, `get_run_summary`, `new_run`, `lookup_*` |

Calling a tool outside its valid phase returns a clear error:
```
Error: Cannot fight — not in a zone. Current phase: ZONE_SELECT.
Available actions: list_zones, enter_zone, party_status, equip, ...
```

---

## State Summarizer

Every tool response includes a state summary appropriate to the current decision. These are token-optimized: compact but complete for making the next decision. IDs are always shown (in `backticks` or alongside display names) so the agent can reference them in tool calls.

### Zone Selection View

Shown after `new_run`, `leave_zone`, or `list_zones`.

```
=== Kael's Run | Zones Cleared: 3/7 | Gold: 450 ===

PARTY:
  [active] Kael (kael_mc) [Einherjar Lv8] 120/120 HP | STR:40 DEF:40 SPD:18
  [active] Yuki (yuki_02) [Onmyoji Lv7] 65/65 HP | MAG:32 RES:32 SPD:18
  [reserve] Tanaka (tanaka_03) [Berserker Lv6] 80/80 HP

STASH (4/10): minor_potion ×2, iron_blade, spirit_lens

AVAILABLE ZONES:
  ✓ zone_01 — Shrine Entrance (Lv1) — Cleared | XP cap: Lv5
  ✓ zone_02 — Mossy Path (Lv2) — Cleared | XP cap: Lv6
  ✓ zone_03 — Bamboo Thicket (Lv3) — Cleared | XP cap: Lv8
  ★ zone_05 — Spirit Clearing (Lv5) — NEW | 6 encounters | XP cap: Lv10
      Recruit chance: 15% | Shop: iron_blade, spirit_lens, iron_guard, spirit_mantle, minor_potion
```

### Combat View

Shown after `fight` (initial state) and after each `submit_decisions` (round result + new state).

```
=== COMBAT Round 3 | Bamboo Thicket (Lv3) | Encounter 4/6 ===

YOUR PARTY:
  kael_mc [Einherjar Lv6] 45/120 HP (38%) | AP: 1 | STR:30 DEF:43 SPD:15
    Abilities: basic_attack ✓, brace_strike ✓, thrust (cd:1), retaliate [passive]
    Equipment: iron_blade (WEAPON), iron_guard (ARMOR)
    Statuses: [DEF +15 — 1t remaining]
    Bonus actions: 0

  yuki_02 [Onmyoji Lv5] 62/65 HP (95%) | AP: 0 | MAG:25 RES:22 SPD:18
    Abilities: basic_attack ✓, bolt ✓, hex ✓, drain (cd:1), foresight [partial] ✓
    Equipment: spirit_lens (WEAPON), spirit_mantle (ARMOR)
    Bonus actions: 0

ENEMIES:
  alpha_slime_1 [Alpha Slime] 30/90 HP (33%) | STR:21 DEF:15 SPD:18
    Statuses: [DISRUPTED — 2t remaining]
  fodder_slime_1 [Fodder Slime] 20/20 HP (100%) | STR:5 DEF:3 SPD:4

TURN ORDER: yuki_02 → alpha_slime_1 → kael_mc → fodder_slime_1

LAST ROUND:
  Kael used Brace Strike → Alpha Slime for 42 dmg, gained DEF +15 (1t)
  Yuki used Hex → Alpha Slime — DISRUPTED (2t)
  Alpha Slime used Heavy Strike → Kael for 35 dmg
  Fodder Slime used Basic Attack → Yuki for 8 dmg
  Kael's Retaliate triggered → Fodder Slime for 12 dmg
```

**On round 0 (combat start):** "LAST ROUND" section is omitted. A brief enemy intro is shown instead:

```
NEW ENCOUNTER: Alpha Slime ×1, Fodder Slime ×2
  Alpha Slime — BOSS archetype, has Heavy Strike. STR-based.
  Fodder Slime — basic attacker, low HP.
```

### Post-Combat View

Shown after combat ends in victory. Includes loot choices.

```
=== VICTORY in 5 rounds | Bamboo Thicket Encounter 4/6 ===

REWARDS:
  Gold: +45 (total: 495)

LOOT DROPS:
  1. minor_potion — Consumable: heals 50 HP
  2. iron_blade — Weapon (STR LINEAR): 20 + 1.0×STR damage

STASH (4/10) — room for 6 more items:
  minor_potion ×2, iron_blade, spirit_lens

PARTY HP after combat:
  kael_mc: 45/120 (38%) | yuki_02: 62/65 (95%)

→ Use pick_loot with item IDs to keep, or [] to take nothing.
```

### Recruitment View

Shown when a recruitment candidate appears (after advancing in-zone).

```
=== RECRUITMENT CANDIDATE ===

Inspection level: MODERATE (party CHA: 45)

Ren [Martyr]
  Growth: STR +0, DEF +6, RES +3, SPD +1, MAG +0 (randomized from base)
  [Full stats hidden — need CHA ≥70 for complete inspection]

Your party: 2/3 active, 0/1 reserve (room for 1 more)
  → Would join as: active member

→ Use recruit(true) to accept or recruit(false) to decline.
```

With CHA ≥70 (FULL inspection):

```
=== RECRUITMENT CANDIDATE ===

Inspection level: FULL (party CHA: 85)

Ren [Martyr Lv3]
  Growth: STR +0, DEF +6, RES +3, SPD +1, MAG +0
  Current stats: STR:0 DEF:18 RES:9 SPD:3 MAG:0
  HP: 106/106 (base 70, growth 12, DEF scaling)
  Projected Lv20: STR:0 DEF:120 RES:60 SPD:20 MAG:0 | HP: 460
  Equipment: iron_guard (ARMOR)
  Abilities: basic_attack, taunt [innate]

Your party: 2/3 active, 0/1 reserve (room for 1 more)
  → Would join as: active member
```

### Party Status View

Shown on `party_status`. Full detail for equipment/build decisions.

```
=== PARTY STATUS | In Zone: Bamboo Thicket | Gold: 495 ===

ACTIVE:
  kael_mc [Einherjar Lv6] — 45/120 HP (38%) | XP: 280/360 (78% to Lv7)
    Base:  STR:30 MAG:0  DEF:28 RES:0  SPD:15
    Eff:   STR:30 MAG:0  DEF:76 RES:0  SPD:15
    Weapon: iron_blade — STR LINEAR (20 + 1.0×STR) → +50 phys dmg at current stats
    Armor:  iron_guard — DEF LINEAR (20 + 1.0×DEF) → +48 effective DEF at current stats
    Acc1:   (empty)
    Acc2:   (empty)
    Abilities:
      basic_attack — 5 + 0.5×STR → ~20 raw dmg | SINGLE_ENEMY
      brace_strike — 8 + 0.4×STR → ~20 raw dmg + DEF +15 self (1t) | SINGLE_ENEMY
      retaliate [passive] — triggers ON_HIT_RECEIVED: 5 + 0.3×STR → ~14 dmg
    Next unlock: thrust at Lv8 (PIERCE 40%)

  yuki_02 [Onmyoji Lv5] — 62/65 HP (95%) | XP: 180/250 (72% to Lv6)
    Base:  STR:0  MAG:25 DEF:0  RES:22 SPD:18
    Eff:   STR:0  MAG:25 DEF:0  RES:54 SPD:18
    Weapon: spirit_lens — MAG LINEAR (15 + 0.8×MAG) → +35 mag dmg at current stats
    Armor:  spirit_mantle — RES LINEAR (15 + 1.0×RES) → +37 effective RES at current stats
    Acc1:   (empty)
    Acc2:   (empty)
    Abilities:
      basic_attack — 5 + 0.5×STR → ~5 raw dmg | SINGLE_ENEMY
      bolt — 10 + 0.7×MAG → ~27.5 raw dmg (no DEF reduction) | SINGLE_ENEMY
      hex — 3 + 0.4×MAG → ~13 dmg + DISRUPT (2t) | SINGLE_ENEMY | cd:2
      drain — 6 + 0.5×MAG → ~18.5 dmg + 30% leech | SINGLE_ENEMY | cd:0
      foresight [partial] — reveals enemy action weights | ALL_ENEMIES
    Next unlock: ward at Lv11 (RES +30 buff)

RESERVE:
  tanaka_03 [Berserker Lv4] — 50/50 HP | XP: 90/160 (56% to Lv5)
    STR:20 SPD:24 | No equipment
    Abilities: basic_attack, quick_strike, frenzy [passive]

STASH (4/10):
  minor_potion ×2 — Consumable: heals 50 HP | sell: 12g
  iron_blade — Weapon STR LINEAR (20 + 1.0×STR) | sell: 40g
  spirit_lens — Weapon MAG LINEAR (15 + 0.8×MAG) | sell: 28g
```

### Shop View

Shown on `shop_browse`.

```
=== SHOP | Spirit Clearing (Lv5) | Gold: 495 | CHA: 45 (11% discount) ===

FOR SALE:
  iron_blade — Weapon STR LINEAR (20 + 1.0×STR) | 89g (base 100)
  spirit_lens — Weapon MAG LINEAR (15 + 0.8×MAG) | 67g (base 75)
  iron_guard — Armor DEF LINEAR (20 + 1.0×DEF) | 89g (base 100)
  spirit_mantle — Armor RES LINEAR (15 + 1.0×RES) | 67g (base 75)
  minor_potion — Consumable: heals 50 HP | 13g (base 15)

YOUR STASH (4/10) — sellable:
  minor_potion ×2 | sell: 6g each
  iron_blade | sell: 40g
  spirit_lens | sell: 30g

→ Use shop_buy(item_id) or shop_sell(item_id).
```

### Zone Status View

Shown on `get_zone_status` (while in a zone).

```
=== ZONE: Bamboo Thicket (Lv3) | XP cap: Lv8 ===

Progress: 4/6 encounters completed
  1. ✓ Fodder Slime ×2 — victory (2 rounds)
  2. ✓ Fodder Slime ×3 — victory (3 rounds)
  3. ✓ Fodder Slime ×2, Bandit Slime ×1 — victory (4 rounds)
  4. ✓ Alpha Slime ×1, Fodder Slime ×1 — victory (5 rounds)
  5. → NEXT
  6. (boss encounter)

Party HP: kael_mc 45/120 (38%) | yuki_02 62/65 (95%)
Gold: 495

Actions: fight, party_status, shop_browse, leave_zone
```

### Run Summary View

Shown on `get_run_summary` (after death or completion). Also returned as final tool response.

```
=== RUN COMPLETE — VICTORY ===

Final party:
  Kael [Einherjar Lv18] | Yuki [Onmyoji Lv17] | Ren [Martyr Lv15]
  Reserve: Tanaka [Berserker Lv14]

Zones cleared: 7/7
Total encounters: 47 (42 victories, 5 losses retreated)
Total rounds: 189
Total gold earned: 3,450 | Spent: 2,800 | Final: 650

Damage dealt: 12,450 (Kael: 5,200, Yuki: 4,100, Ren: 3,150)
Damage taken: 8,900
Healing done: 3,200

Most used abilities:
  bolt (89 uses), basic_attack (76), brace_strike (54), hex (41)

Never used: crescendo, void_bolt, sacrifice

Deaths: Tanaka (zone_08 encounter 5), Yuki (zone_12 encounter 3, revived via zone exit)

Close calls (sub-10% HP): 12 instances
  kael_mc: 8 times | yuki_02: 3 times | tanaka_03: 1 time

Overstay decisions: stayed 3 extra battles in zone_05 (total -15% loot penalty)
```

---

## MCP Tool Definitions

### Run Management

#### `new_run`
Start a new playthrough.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | MC's name |
| `job_id` | string | yes | Starting job: `einherjar`, `berserker`, `martyr`, `onmyoji` |
| `seed` | int | no | RNG seed for deterministic runs. Random if omitted. |

**Returns:** Zone selection view.
**Phase transition:** SETUP → ZONE_SELECT.

#### `get_state`
Get current state summary. Adapts output to current phase.

**Returns:** The appropriate view for the current phase (zone select, in-zone, combat, etc.)

---

### Zone Navigation

#### `list_zones`
Show available zones with details.

**Returns:** Zone selection view (same as after `new_run`).
**Valid phases:** ZONE_SELECT.

#### `enter_zone`
Enter a zone to begin fighting encounters.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `zone_id` | string | yes | Zone to enter |

**Returns:** Zone status view.
**Phase transition:** ZONE_SELECT → IN_ZONE.
**Errors:** Zone not unlocked, zone doesn't exist.

**Note:** Entering a zone triggers `enter_safe_zone` first — full party heal.

#### `leave_zone`
Exit current zone. Progress is saved for re-entry.

**Returns:** Zone selection view.
**Phase transition:** IN_ZONE → ZONE_SELECT.

#### `get_zone_status`
Show current zone progress, encounter history, party HP.

**Returns:** Zone status view.
**Valid phases:** IN_ZONE.

---

### Combat

#### `fight`
Start the next encounter in the current zone.

**Returns:** Combat view (round 0 — initial state with enemy intro).
**Phase transition:** IN_ZONE → COMBAT.
**Errors:** No encounters remaining (zone cleared and not overstaying... actually overstay always works, this shouldn't error).

#### `submit_decisions`
Submit one round of combat decisions for all player characters.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `decisions` | object | yes | Keyed by combatant_id. See Decision Format below. |

**Returns:**
- If combat continues: Round result events + updated combat view.
- If player wins: Round result events + post-combat view. Phase → POST_COMBAT.
- If player loses: Round result events + death summary (if party wipe) or back to zone (if retreat mechanic exists).

**Phase transition:** COMBAT → COMBAT (ongoing), COMBAT → POST_COMBAT (victory), COMBAT → IN_ZONE or DEAD (defeat).

**Decision format per character:**
```json
{
  "kael_mc": {
    "mode": "normal",
    "action": "brace_strike",
    "target": "alpha_slime_1"
  },
  "yuki_02": {
    "mode": "cheat",
    "ap_spend": 1,
    "action": "bolt",
    "target": "alpha_slime_1",
    "cheat_extras": [
      {"ability": "hex", "target": "fodder_slime_1"}
    ],
    "partial_actions": [
      {"ability": "basic_attack", "target": "fodder_slime_1"}
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | string | yes | `"normal"`, `"cheat"`, or `"survive"` |
| `ap_spend` | int | if cheat | AP to spend (1-3). Requires banked AP. |
| `action` | string | yes | Ability ID for primary action |
| `target` | string | yes | Target combatant ID (or self ID for SELF-target abilities) |
| `cheat_extras` | list | if cheat | Additional actions from spent AP. Each: `{ability, target}` |
| `partial_actions` | list | if any | Bonus actions from SPD. Each: `{ability, target}` |

**Validation:**
- All living player characters must have a decision
- Ability must be off cooldown and in character's ability list
- Target must be valid for the ability's target type
- Cheat AP can't exceed banked AP
- Partial action count can't exceed `SPD // 100`
- Clear error messages on validation failure: `"Error: kael_mc — thrust is on cooldown (1 round remaining)"`

#### `get_combat_state`
Re-fetch current combat state without advancing.

**Returns:** Combat view (current round state).
**Valid phases:** COMBAT.

---

### Post-Combat

#### `pick_loot`
Select which dropped items to keep.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `item_ids` | list[string] | yes | IDs of items to keep. Empty list `[]` to take nothing. |

**Returns:**
- If no recruitment pending: Zone status view. Phase → IN_ZONE.
- If recruitment candidate generated: Recruitment view. Phase → RECRUITING.

**Errors:** Item not in loot drops, stash full (over 10).
**Phase transition:** POST_COMBAT → IN_ZONE or POST_COMBAT → RECRUITING.

#### `inspect_candidate`
Get detailed info about the recruitment candidate. CHA-gated detail level.

**Returns:** Recruitment view (with detail level matching party CHA).
**Valid phases:** RECRUITING.

#### `recruit`
Accept or decline the recruitment candidate.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `accept` | bool | yes | true to recruit, false to decline |

**Returns:** Zone status view (updated with new party member if accepted).
**Phase transition:** RECRUITING → IN_ZONE.
**Errors:** Party full (4 members max).

---

### Party Management

All valid in ZONE_SELECT and IN_ZONE phases.

#### `party_status`
Full party detail view.

**Returns:** Party status view.

#### `equip`
Equip an item from stash onto a character.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `character_id` | string | yes | Character to equip |
| `item_id` | string | yes | Item from stash |
| `slot` | string | yes | `"WEAPON"`, `"ARMOR"`, `"ACCESSORY_1"`, `"ACCESSORY_2"` |

**Returns:** Updated character summary with new effective stats.
**Behavior:** If slot is occupied, the existing item returns to stash automatically.
**Errors:** Item not in stash, character not in party, wrong slot for item type.

#### `unequip`
Remove equipment from a slot back to stash.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `character_id` | string | yes | Character to unequip from |
| `slot` | string | yes | Slot to clear |

**Returns:** Updated character summary.
**Errors:** Slot already empty, stash full.

#### `swap_roster`
Swap a character between active and reserve.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `active_id` | string | no | Active member to bench |
| `reserve_id` | string | no | Reserve member to promote |

At least one must be provided. If both: swap positions. If only one: bench or promote (respecting active size limits of 1-3).

**Returns:** Updated party overview.
**Errors:** Can't bench last active member, reserve full.

#### `use_scroll`
Use a teach scroll to permanently teach an ability.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | yes | Scroll item from stash |
| `character_id` | string | yes | Character to teach |

**Returns:** Updated character abilities list + confirmation.
**Errors:** Not a scroll, character already knows the ability.

#### `use_consumable`
Use a consumable item (potion, etc.) on a character.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | yes | Consumable from stash |
| `character_id` | string | yes | Target character |

**Returns:** Updated character HP + confirmation.
**Errors:** Not a consumable, character at full HP (warn but allow).

#### `mc_swap_job`
Change the MC's job (mimic a recruited party member's job).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | yes | Job to swap to |

**Returns:** Updated MC summary with new stats, abilities, growth.
**Valid:** Only if a party member with that job has been recruited (current or past).
**Errors:** Job not available for mimic.

---

### Shopping

Valid in IN_ZONE phase.

#### `shop_browse`
View zone shop inventory with CHA-adjusted prices.

**Returns:** Shop view.

#### `shop_buy`
Purchase an item from the shop.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | yes | Item to buy |

**Returns:** Confirmation + updated gold + stash.
**Errors:** Can't afford, item not in shop, stash full.

#### `shop_sell`
Sell an item from stash.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | yes | Item to sell from stash |

**Returns:** Confirmation + updated gold + stash.
**Errors:** Item not in stash, item is equipped (must unequip first).

---

### Game Knowledge

Available in ALL phases. These let the agent query the game's rulebook without dumping the entire GameData.

#### `lookup_job`
| Param | Type | Required |
|-------|------|----------|
| `job_id` | string | yes |

**Returns:**
```
=== Einherjar ===
Origin: Norse — "The chosen dead, warrior spirits selected by valkyries"

Growth per level: STR +5, DEF +5, SPD +3, MAG +1, RES +1
  (base +1 all stats per level + job bonus)
Base HP: 50 | HP growth: +8/level | HP from DEF: 1.5×DEF

Innate: retaliate — ON_HIT_RECEIVED: 5 + 0.3×STR counter-damage
Ability unlocks:
  Lv3: brace_strike — 8 + 0.4×STR + self DEF +15 (1t)
  Lv8: thrust — PIERCE 40%: 8 + 0.5×STR, ignores 40% of target DEF
  Lv15: fracture — SHATTER: 5 + 0.3×STR, reduces target DEF 25% (2t)

Role: Durable physical striker. Retaliate punishes enemies for hitting you.
Scales STR for damage and DEF for survivability. Mid-speed.
```

#### `lookup_ability`
| Param | Type | Required |
|-------|------|----------|
| `ability_id` | string | yes |

**Returns:**
```
=== Hex (hex) ===
Category: OFFENSIVE | Target: SINGLE_ENEMY | Cooldown: 2 rounds
Quality: DISRUPT — shifts enemy action weights, adds delay

Damage: 3 + 0.4×MAG (magical, no DEF reduction, RES-gated effects)
Duration: 2 rounds

Effect: Deals magic damage. If target RES < caster MAG × 0.7, applies
DISRUPT status for 2 turns (alters enemy action table toward weaker moves).

Stat requirement: MAG-based. Need MAG > target RES / 0.7 for effects to land.
```

#### `lookup_item`
| Param | Type | Required |
|-------|------|----------|
| `item_id` | string | yes |

**Returns:**
```
=== Runic Edge (runic_edge) ===
Slot: WEAPON | Base price: 3500g

Scaling: SUPERLINEAR on STR
  Formula: 15 + 0.3×STR + 0.005×STR²
  At STR 30: 15 + 9 + 4.5 = 28.5 bonus damage
  At STR 60: 15 + 18 + 18 = 51 bonus damage
  At STR 100: 15 + 30 + 50 = 95 bonus damage

Crossover: Overtakes Iron Blade (~50 STR).
Best for: Mid-to-late game STR builds.
```

For converter items:
```
=== Fortress Ring (fortress_ring) ===
Slot: ACCESSORY_1 | Base price: 5000g

Conversion: DEF → MAG (SIGMOID)
  Formula: 800 / (1 + e^(-0.015 × (DEF - 300)))
  At DEF 100: ~57 MAG bonus
  At DEF 200: ~172 MAG bonus
  At DEF 300: ~400 MAG bonus (midpoint)
  At DEF 500: ~745 MAG bonus

Best for: High-DEF characters (Martyr) who want magic damage.
```

#### `lookup_enemy`
| Param | Type | Required |
|-------|------|----------|
| `enemy_id` | string | yes |

**Returns:**
```
=== Brute Oni (brute_oni) ===
Archetype: BRUTE | Budget: 14.0× zone level

Stat distribution: STR 33%, DEF 29%, SPD 7%, RES 5%, MAG 5%
HP: 40 base + 3.0 per budget point
Equipment: iron_blade (WEAPON), iron_guard (ARMOR)

At zone 5:  STR:23 DEF:20 SPD:5  HP:250 | Weapon bonus: +43
At zone 8:  STR:37 DEF:32 SPD:8  HP:376 | Weapon bonus: +57
At zone 12: STR:55 DEF:48 SPD:12 HP:544 | Weapon bonus: +75

Action weights:
  heavy_strike: 80% | arc_slash: 15% | basic_attack: 5%
  Conditional: targets <30% HP → heavy_strike 95%
  Conditional: post-Cheat player → heavy_strike 95%

Behavior: Slow but devastating. Finishes low-HP targets. Punishes Cheat with
focused burst. Kill before it acts, or Survive through its turns.

Drops: common (potion, iron_blade, iron_guard) 20% | rare (endurance_plate,
leech_fang, void_fang) 5% | equipment 10%
```

#### `lookup_zone`
| Param | Type | Required |
|-------|------|----------|
| `zone_id` | string | yes |

**Returns:**
```
=== Torii Descent (zone_08) ===
Level: 8 | Region: shinto_slimes | Loot tier: 2 | XP cap: Lv14
Unlock requires: zone_05 cleared

Encounters (7):
  1. Fodder Slime ×3
  2. Brute Oni ×1, Fodder Slime ×1
  3. Caster Kitsune ×1, Fodder Slime ×2
  4. Speeder Tengu ×2
  5. Brute Oni ×1, Caster Kitsune ×1
  6. Support Tanuki ×1, Speeder Tengu ×1, Fodder Slime ×1
  7. [BOSS] Brute Oni ×1, Caster Kitsune ×1, Support Tanuki ×1

Random spawns: bandit_slime (10% per encounter)

Shop: iron_blade, spirit_lens, iron_guard, spirit_mantle, runic_edge,
      resonance_orb, potion, minor_potion

Difficulty: Mixed archetypes. Support Tanuki heals allies — must be focused
down first. Brute Oni punishes Cheat. Boss is a 3-archetype combo fight.
```

#### `lookup_formula`
Query a specific game formula. Useful for the agent to understand damage math, XP curves, etc.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | yes | One of: `damage`, `defense`, `magic`, `hp`, `xp`, `leveling`, `bonus_actions`, `res_gate`, `shop_pricing`, `overstay`, `scaling_types` |

**Returns:** The relevant formula with examples. For `damage`:
```
=== Physical Damage Formula ===
raw = ability_base + (coefficient × STR) + item_scaling_bonus
reduction = target_DEF × 0.5 × (1 - pierce_percent)
damage = max(1, raw - reduction)

DEF is 50% effective. Pierce ignores a percentage of that.

Example: STR 50, basic_attack (5 + 0.5×STR), iron_blade (+70), vs DEF 40
  raw = 5 + 25 + 70 = 100
  reduction = 40 × 0.5 = 20
  damage = 80

=== Magical Damage Formula ===
damage = max(1, ability_base + (coefficient × MAG) + item_scaling_bonus)
No DEF reduction. RES only gates secondary effects (status/debuff).

Magic is NOT reduced by any stat. RES only prevents secondary effects
from landing when target RES >= caster MAG × 0.7.
```

---

### Analytics

#### `get_battle_record`
Get run statistics. Available in all phases.

**Returns:** Run summary view (see State Summarizer section).

#### `get_run_summary`
Comprehensive end-of-run report. Available in DEAD phase or after clearing all zones.

**Returns:** Full run summary with analytics. This is the main data output for balance testing.

---

## Analytics Collector

The analytics layer hooks into every state transition to build a structured `RunReport` at the end of each run.

### RunReport Schema

```python
class RunReport(BaseModel):
    """Complete analytics for one playthrough."""
    # Run metadata
    run_id: str
    seed: int
    mc_job_id: str
    mc_name: str
    outcome: Literal["victory", "defeat"]
    death_zone: str | None = None       # Zone where party wiped (if defeat)
    death_encounter: int | None = None  # Encounter index at death
    zones_cleared: int
    total_zones: int

    # Timing
    total_encounters: int
    total_rounds: int
    encounters_per_zone: dict[str, int]
    rounds_per_encounter: list[int]     # Distribution

    # Party
    final_party: list[CharacterSnapshot]  # Lv, job, stats, equipment, abilities
    recruitment_decisions: list[RecruitEvent]  # Offered, accepted/declined, job, zone
    mc_job_swaps: list[JobSwapEvent]

    # Economy
    total_gold_earned: int
    total_gold_spent: int
    gold_curve: list[GoldSnapshot]      # Gold at each zone transition
    shop_purchases: list[ShopEvent]
    shop_sales: list[ShopEvent]
    gold_stolen_by_enemies: int
    gold_stolen_by_players: int

    # Combat
    damage_dealt_by_character: dict[str, int]
    damage_dealt_by_ability: dict[str, int]
    damage_taken_by_character: dict[str, int]
    healing_by_character: dict[str, int]
    ability_usage: dict[str, int]       # Ability ID → total uses
    abilities_never_used: list[str]     # Available but never picked
    cheat_survive_usage: dict[str, dict[str, int]]  # Char → {cheat: N, survive: N, normal: N}
    close_calls: list[CloseCallEvent]   # Character dropped below 10% HP
    character_deaths: list[DeathEvent]  # Who died, where, when

    # Loot
    items_found: list[str]              # All item IDs that dropped
    items_kept: list[str]               # Items agent chose to keep
    items_discarded: list[str]          # Items agent passed on
    overstay_decisions: list[OverstayEvent]  # Zone, battles stayed, penalty

    # Progression
    level_curve: dict[str, list[LevelSnapshot]]  # Char → [level at each zone]
    xp_by_zone: dict[str, int]         # Zone → total XP earned

    # Build
    equipment_timeline: list[EquipEvent]  # Every equip/unequip action
    final_equipment: dict[str, dict[str, str]]  # Char → {slot: item_id}
    scroll_usage: list[ScrollEvent]     # Which scrolls taught to whom
```

### What This Enables

With RunReports from 100+ seeded runs:

**Balance questions we can answer:**
- Win rate per starting job (is any job dominant or unplayable?)
- Death zone distribution (where's the difficulty cliff?)
- Gold curve per zone (do agents hoard or starve?)
- Ability usage heatmap (which abilities are traps? which are mandatory?)
- Item pick rates (which drops are always kept? always discarded?)
- Overstay behavior (is overstaying ever optimal? are the penalties right?)
- Recruitment impact (does recruiting improve win rate? which jobs as recruits?)
- Cheat/Survive distribution (does one mode dominate? is the tradeoff meaningful?)
- Build diversity (do all agents converge on one build? or explore different paths?)
- Close call frequency (is the game too swingy? not swingy enough?)

---

## Batch Simulation Layer

For mass runs without LLM calls. Separate from MCP but shares the same engine.

### Policy Interface

```python
class AgentPolicy(Protocol):
    """Interface for non-LLM agent strategies."""

    def choose_job(self) -> str: ...

    def choose_zone(
        self, run: RunState, available: list[ZoneTemplate]
    ) -> str: ...

    def combat_round(
        self, combat: CombatState, run: RunState
    ) -> dict[str, PlayerTurnDecision]: ...

    def choose_loot(
        self, loot: LootResult, run: RunState
    ) -> list[str]: ...

    def should_recruit(
        self, candidate: RecruitCandidate, run: RunState
    ) -> bool: ...

    def manage_party(
        self, run: RunState, phase: Literal["pre_zone", "in_zone"]
    ) -> list[PartyAction]: ...

    def should_overstay(
        self, run: RunState
    ) -> bool: ...

    def shop_decisions(
        self, shop: ShopInventory, run: RunState
    ) -> tuple[list[str], list[str]]: ...
        # Returns (buy_ids, sell_ids)
```

### Built-in Policies

**Aggressive** — always pick highest-damage ability, target lowest-HP enemy, Cheat whenever AP > 0, never Survive. Pick highest-ATK weapons. Enter highest-level zone available.

**Defensive** — prioritize healing and Survive, Cheat only if winning. Pick highest-DEF armor. Always buy potions. Pick safest (lowest-level uncompleted) zone.

**Economy** — maximize gold: overstay until penalty is steep, buy cheap/sell dear, hoard consumables. Uses Pilfer if available.

**Random** — uniformly random valid decisions. Baseline for comparison.

**Balanced** — heuristic that tries to play well: focus highest-threat enemy, Cheat when advantageous, manage equipment for stat optimization, enter zones at appropriate level. This is the "does the game work for a decent player?" baseline.

### Batch Runner

```python
def run_batch(
    policy: AgentPolicy,
    n_runs: int,
    seed_start: int = 0,
    jobs: list[str] | None = None,  # None = all jobs
) -> list[RunReport]:
    """Run N games with the given policy and sequential seeds."""
```

```python
def aggregate_reports(reports: list[RunReport]) -> BalanceReport:
    """Aggregate across runs for statistical analysis."""
```

### BalanceReport Schema

```python
class BalanceReport(BaseModel):
    """Aggregate statistics across multiple runs."""
    n_runs: int
    win_rate: float
    win_rate_by_job: dict[str, float]
    avg_zones_cleared: float
    death_zone_distribution: dict[str, int]  # Zone → death count
    avg_gold_final: float
    gold_curve_percentiles: dict[str, list[float]]  # p25/p50/p75 per zone
    ability_usage_rates: dict[str, float]    # Uses per encounter
    ability_never_used_rate: dict[str, float]  # % of runs where never used
    item_pick_rate: dict[str, float]         # % of times kept when dropped
    avg_encounters_total: float
    avg_rounds_per_encounter: float
    cheat_rate: float                         # % of turns using Cheat
    survive_rate: float                       # % of turns using Survive
    recruitment_accept_rate: float
    overstay_rate: float                      # % of cleared zones where agent overstayed
    avg_overstay_battles: float
    build_diversity_index: float              # Shannon entropy of final equipment sets
    close_call_rate: float                    # Close calls per encounter
```

---

## Implementation Sequence

### Phase 1: State Summarizer
- `StateSummarizer` class with one method per view
- Pure functions: `(RunState, CombatState, GameData) → str`
- Write tests against snapshot outputs (known state → expected text)
- This is the foundation everything else builds on

### Phase 2: Game Session
- `GameSession` class wrapping engine + state + phase tracking
- Phase validation (what tools are legal when)
- Decision translation (agent JSON → `PlayerTurnDecision`)
- Error handling with clear messages

### Phase 3: MCP Server
- Register tools with MCP protocol
- Wire tool handlers to GameSession methods
- Add `lookup_*` tools backed by GameData queries

### Phase 4: Analytics Collector
- Hook into GameSession state transitions
- Build `RunReport` incrementally during play
- `RunReport` serialization (JSON for storage, text for display)

### Phase 5: Batch Layer
- `AgentPolicy` protocol + built-in policies
- `BatchRunner` driving GameLoop directly (no MCP overhead)
- `aggregate_reports` for balance analysis

### Phase 6: Polish
- System prompt / game guide for Claude (one-shot reference for how to play)
- Multi-run orchestration scripts
- Balance dashboard (tabular/chart output from BalanceReports)

---

## Design Decisions Log

**Why structured text instead of JSON for state views?**
Token efficiency. A combat state in JSON is 2-3× the tokens of the same info in structured text. Claude reasons equally well over both, and the text format makes the views human-readable for debugging.

**Why one tool call per combat round (not per character)?**
Minimizes round trips. A 5-round fight is 5 tool calls instead of 10-20. The agent can still make per-character decisions — they're just bundled. This is the single biggest token saver.

**Why separate MCP and batch layers?**
Different tradeoffs. MCP gives full LLM reasoning per decision (qualitative, strategic, few runs). Batch gives statistical power (quantitative, heuristic, thousands of runs). You want both: Claude to find interesting strategies and report "zone 8 feels unfair", and batch to confirm "zone 8 has 23% death rate vs 8% everywhere else."

**Why `lookup_*` tools instead of dumping GameData in the system prompt?**
GameData is huge. Dumping all items, abilities, enemies, and zones would be 10K+ tokens of rules that the agent only needs fragments of. On-demand lookup keeps the context clean and lets the agent pull exactly what it needs.

**Why seed control?**
Deterministic runs enable A/B testing. "Does Einherjar with Void Fang beat the same zone 12 encounter that killed it with Iron Blade?" Same seed, different choice, compare outcomes. Essential for build testing.

**Why not expose raw pydantic models via MCP?**
The agent doesn't need `growth_history`, `zone_progress` internal bookkeeping, or `model_config`. It needs decision-relevant information. The summarizer is a deliberate information filter that shows what matters and hides implementation details.
