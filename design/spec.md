# Standalone Roguelike JRPG — Spec v0.1

> A text-based roguelike JRPG. Pick a world, pick a job, descend, build synergy, kill god.

---

## Core Loop

1. Pick a world theme (determines enemy reskins, ability flavor, area descriptions, god identity)
2. Pick a starting job from the unlocked set
3. Descend through zones — fight, recruit, equip, adapt
4. Beat the Final Boss
5. Face god. Die, or break the math and win.
6. Meta-progression banked. Go again.

---

## World Themes

Three themed world pools. Mechanically identical — same stat budgets, same behavior archetypes, same scaling curves. Different flavor text, ability names, enemy names, area descriptions.

| Theme | Aesthetic | Example Enemy Reskin | Example Ability Reskin | God |
|-------|-----------|---------------------|----------------------|-----|
| **Nordic** | Frost, iron, runes, ash, world-tree | Draugr (Brute archetype) | Frostbite (DOT) | Ragnarök entity |
| **Shinto** | Shrines, spirits, paper, ink, seasons | Oni (Brute archetype) | Spirit Burn (DOT) | Kami of the final gate |
| **Abrahamic** | Stone, light, seraphim, desert, scripture | Nephilim (Brute archetype) | Brimstone (DOT) | The Throne |

World selection is per-run. Same engine, different paint. Cheap to produce — the content pipeline generates themed variants from the same mechanical templates.

---

## Stats

Five combat stats, one meta stat. Clean, conventional, legible.

### Combat Stats

| Stat | Role | Design |
|------|------|--------|
| **STR** | Physical offense | Reliable, linear. The consistent stat. Gets you home on bad runs. |
| **MAG** | Magical offense | Conditional, multiplicative. Weak at baseline, explosive with setup. Different risk profile from STR — setup-dependent and back-loaded. |
| **DEF** | Physical defense | Flat reduction against STR-type damage. Predictable. |
| **RES** | Magical defense | Threshold system — if RES exceeds incoming MAG by a ratio, secondary effects (DOT, debuffs) are fully resisted. Below threshold, they go through entirely. Pass/fail gate, not a soak. |
| **SPD** | Action density | Everyone acts every round. SPD thresholds grant bonus partial actions (free item use, defensive check, follow-up at reduced power). Always nice, never mandatory. |

Every stat should feel overpowered when specialized. Multiple optimization paths that all feel strong in different ways.

### Meta Stat

| Stat | Role | Design |
|------|------|--------|
| **CHA** | Non-combat, cross-run | Persists across runs. Affects: recruit inspection depth, shop prices, event outcomes. At low CHA, you're playing blind. At high CHA, you see full recruit scaling curves, better shop options. Never competes with combat stats within a run. |

CHA provides the career arc: early = chaotic, information-poor. Late = full information, pure optimization.

---

## Jobs

Growth rate vectors + equipment access profiles. No ability grants.

A job is:
- A five-element growth rate vector (STR/MAG/DEF/RES/SPD per level)
- An equipment access mask

### Starter Set (illustrative)

- **Knight**: High STR/DEF, equips heavy weapons and armor
- **Seer**: High MAG/SPD, equips catalysts and light armor
- **Warden**: High DEF/RES, equips shields and medium armor
- **Striker**: High STR/SPD, equips light weapons and mobility gear

### Principles

- Jobs are the lens for evaluating items and abilities. Same superlinear STR sword has completely different value for a Knight vs. a Seer.
- Start with 2-3 unlocked. More unlock permanently through run milestones.
- More jobs = more build paths ≠ more power. The game gets wider, not easier.

---

## Abilities

Found as drops, not learned through leveling. Each themed to the current world but mechanically identical across themes.

Each ability:
- **Stat requirements** (continuous — never hard-locked, but underperforms if you barely meet the threshold)
- **Scaling coefficients** (which stats, how)
- **Damage quality** (mechanical effect type)
- **Cooldown** (rounds, not mana)
- **Target profile** (single, AOE, chain, self, etc.)

### Damage Qualities

No elemental type chart. Mechanical effect properties, contextually good or bad based on enemy stat profiles.

| Quality | Effect | Strong Against |
|---------|--------|----------------|
| **DOT** | Damage over N rounds, bypasses DEF | High-DEF, low-HP |
| **Shatter** | Reduces DEF for N rounds | DEF-stacked, enables STR allies |
| **Chain** | Hits multiple at reduced power | Mob-heavy encounters |
| **Pierce** | Ignores % of DEF | Armored enemies |
| **Disrupt** | Shifts enemy action weights / delays | Tempo-heavy, dangerous boss phases |
| **Leech** | Heals for % of damage dealt | Attrition, sustain fights |
| **Surge** | Scales with consecutive uses | Extended boss fights |

Qualities combine (DOT + Pierce). World themes reskin the flavor (Frostbite vs. Spirit Burn vs. Brimstone) without changing the math.

---

## Items & Scaling

### Continuous Scaling (No Thresholds)

Every item has a continuous scaling function. No level gates.

```
Iron Sword:        damage = base + 1.0 * STR           (linear, reliable)
Runic Blade:       damage = base + 0.3*STR + 0.02*STR² (worse early, monstrous late)
Void Edge:         damage = -5 + 0.04*STR²              (harmful early, astronomical late)
```

### Emergent Rarity

From curve shape, not labels:
- **Common**: Linear, frontloaded
- **Uncommon**: Slightly superlinear, mid-game
- **Rare**: Quadratic / inflection-point, build-defining late
- **Degenerate**: Negative at low stats, godlike at high. Go-big-or-go-home.

### Converter Items

Bridge stat axes. A shield that converts DEF into MAG scaling. A weapon that feeds SPD into STR. The primary mid-run adaptation mechanism — rescue a mismatched run, enable off-label builds.

### Inventory

- 3-4 equip slots per character
- Small shared party stash (~8-10 slots)
- Every speculative hold has real opportunity cost
- Backup equip slots as overflow = greed trap (see Recruitment)

---

## Party

- **3 active** in combat
- **1 backup** that rotates in

One backup is deliberate: rotation is a decision, not bench management. The backup is a specialization target and an inventory temptation.

---

## Recruitment

### One-Shot Encounters

Roughly once per major zone. Pool is mostly randomized — rolling window prevents same-job repeats, but no bias toward "filling gaps."

### Recruits

- Fixed job (Persona model — can't change it)
- Randomized base stats within job range
- Randomized scaling profile (high base/low scaling vs. low base/high scaling)
- Their own equipment — transfers to you if recruited

### The Decision

- One-time, permanent. Recruit or pass.
- Full party → must release someone to make room
- **Cannot unequip gear during recruitment.** Released member leaves with everything they're wearing. Inventory management happens between stages, never in the moment.
- CHA determines how much you can see (base stats only → full scaling curves + equipment)

### The Greed Trap

Backup holding overflow items + perfect recruit shows up = agonizing choice. Recruit and lose the gear, or pass on the synergy. Entirely the player's fault. Best kind of roguelike pain.

---

## MC & Mimic System

### Starting Job

MC picks from unlocked set at run start. Small innate bonus for starting job (primarily cumulative — they've been in this job from floor 1).

### Mimic

MC can swap to any job currently in the party. Growth rates change forward, stats don't respec. A Knight who swaps to Seer on floor 15 has Knight stats growing Seer-ward. Geological record of every job held.

Implications:
- Every recruit is also a potential build path for the MC
- Multi-job pathing builds unusual stat combos for specific item synergies
- Late swaps = less runway, only worth it for targeted synergies
- Always a pivot, never a free respec

---

## Combat: Brave/Default

- **Default**: Bank a turn, reduce incoming damage. Store an action point.
- **Brave**: Spend banked points for multiple actions. Then vulnerable until debt repaid.

Interactions:
- SPD partial actions fill the post-Brave vulnerability gap
- Braving fires cooldowns sooner → potential dead zones
- Enemies punish post-Brave vulnerability (aggression spikes)
- Roguelike tension: Brave to nuke trash and risk being empty for a miniboss?

---

## Enemy Behavior

### Weighted Tables

3-5 actions per archetype with base probability weights. Conditional modifiers shift weights based on game state.

**Example — Brute:**
- Heavy Strike 80% / Sweeping Blow 15% / Enrage 5%
- Player below 30% HP → 95/5/0 (aggression)
- Brute below 25% HP → 40/10/50 (panic buffing)
- Player post-Brave → aggression spike

Players learn enemy *personalities* across runs. Readable but not fully predictable.

### Bosses

Phase transitions at HP thresholds. Phase 1 → Phase 2 (new actions, weight shifts) → Phase 3 (desperation). Learnable landmarks.

### Variants

Same archetype, different stat budgets and damage qualities. Themed per world — a Nordic draugr brute and a Shinto oni brute fight identically but threaten different damage qualities. Cheap to produce.

---

## The God Fight

### Structure

Final Boss marks run completion. God begins after.

### Design

- Different god per world theme
- Perfect information: knows your stats, equipment, cooldowns, abilities
- Plays optimally — could be LLM-powered or hand-scripted decision trees
- Each god embodies a mechanical philosophy:
  - *Nordic god*: Absurd DEF, reflects physical — demands MAG solution
  - *Shinto god*: Extreme tempo, acts 3x/round — demands SPD
  - *Abrahamic god*: Heals to full every N rounds — demands burst window optimization

### The Core Promise

**Designed to be unbeatable by normal builds.** The only way to win is hypersynergy — a build so degenerate the math breaks in your favor even against perfect counterplay. You don't outplay god. You outscale god.

That moment — fifty hours in, CHA maxed, full job roster, everything clicks — is the payoff. The crack of the whole game.

---

## Meta-Progression

### Jobs
- Start with 2-3. Unlock more through run milestones.
- Wider, not easier.

### CHA
- Accumulates across runs. More information, harder optimization.
- Career arc: blind → informed → omniscient optimizer.

### Dignified Exit
- End dead runs early, bank partial progress.
- Respects player time without softening difficulty.

---

## Text & LLM Integration

### Light Touch

The game is primarily text-based with structured mechanical output. LLM integration is **flavor, not structure**:

- Area descriptions on zone entry (short, atmospheric, themed to world)
- Combat narration: mechanical events → one-line flavor text ("The draugr's axe shatters your ward — DEF down for 2 rounds")
- Shop/event flavor text
- Recruit encounter descriptions

The LLM never decides mechanical outcomes. It dresses up what the engine already determined. Keep it cheap — short generations, cacheable per enemy/ability/area type. Most text can be pre-generated and stored rather than generated at runtime.

### CHA Integration

CHA modulates text richness. Low CHA: terse descriptions, sparse information. High CHA: richer flavor, better hints woven into prose. Simple prompt-level parameter.

---

## Content Pipeline

### Seed → Expand → Curate

1. Hand-author or brainstorm seed sets (base abilities, enemy archetypes, area templates) per world theme
2. LLM-expand within mechanical constraints (stat requirements, scaling ranges, cooldown bounds, quality assignments)
3. Curate: validate against balance, select for interesting decisions, assign to world themes

Three themes × one shared mechanical backbone = 3x content from 1x design work. A Nordic DOT ability and a Shinto DOT ability are the same ability with different names and flavor text.

---

## Open Questions

- [ ] Game name
- [ ] Exact equip slot types
- [ ] Party stash size
- [ ] Recruit frequency tuning
- [ ] MC starting job bonus specifics
- [ ] God selection — one god per world, or pool within each world?
- [ ] Specific job roster with growth vectors
- [ ] Scaling formulas (stats → damage/mitigation/action thresholds)
- [ ] Brave/Default exact mechanics (max bank, debt rate, defensive bonus)
- [ ] Save system
- [ ] How much LLM vs. pre-generated text (cost/latency tradeoff)
- [ ] World unlock order — all three available from start, or progression?

---

*v0.1 — standalone text roguelike spec, April 2026*
