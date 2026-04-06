# Enemies

## Philosophy

- **Dead simple within-variant.** Predictable stats, predictable action tables. Players learn patterns, not guess RNG bounds.
- Complexity comes from action table weights, conditions, and phases — not from stat randomization.
- Faithful to JRPG archetypes. They're good templates for a reason.
- Enemies scale with zone level via predictable bounds. A zone-15 Brute and zone-25 Brute are quantitatively different but structurally identical.

> "keeping within-variant specs dead simple is good both for design and for player use. it lets them learn something rather than have to predict the bounds of an rng thing. they already have to work against the weighted action table/conditions/phases/etc." — designer

## Shared Pool Principle

**Enemies use the same ability and item pool as players.** Core design constraint.

> "enemies should use the *same* ability/item pool. this both reduces complexity on our side, showcases combinations to users when we craft them (with weaknesses they can learn from and find ways to work around by purposeful suboptimal hole crafting), and so forth. that's key." — designer

- Enemies are built like NPC party members: archetype (= job) + stats + abilities from the shared pool + items from the shared pool
- Action tables are just AI policy — which shared-pool abilities they use and when
- **Teaching**: players see ability combos used against them, learn what's possible. "That Kitsune just used Hex + Crescendo... I could do that."
- **Intentional holes**: enemy builds have exploitable weaknesses. A Brute with no RES and no anti-DOT teaches "use DOT against high-DEF enemies."
- **Loot source**: defeating enemies can drop their equipped items/abilities. What they use, you can get.
- **One pool to balance**: if an ability is broken on enemies, it's broken on players, and that's a feature.

---

## Scaling Model

- Each archetype has a **base stat template** (ratios between STR/MAG/DEF/RES/SPD/HP).
- Templates **scaled to zone level** — simple multiplier or linear function. No RNG on enemy stats.
- `enemy_budget = zone_level * budget_multiplier`
- Predictable = strategizable. "My build handles Brutes at zone 20 but not 30 — I need more Pierce."

---

## The 5 Archetypes

| Archetype | Stats | Role | What It Tests |
|-----------|-------|------|---------------|
| **Fodder** | Low everything, comes in numbers | Tutorial enemy, mob filler, chain-kill fuel | Basic combat, AOE/Chain value, action economy |
| **Brute** | High STR/DEF, low SPD | Slow heavy hitter, punishes post-Cheat vulnerability | DEF stacking, sustained damage, Survive timing |
| **Caster** | High MAG, low DEF/HP | Applies DOTs/debuffs, tests RES gate | RES threshold management, "kill it fast or suffer" |
| **Speeder** | High SPD, moderate STR, low DEF | Targets squishy party members, acts early/often | Taunt usage, protection, burst before bursted |
| **Support** | Moderate stats, heals/buffs allies | Heals other enemies, buffs them, extends fights | Target priority, DPS racing, "kill this first" |

---

## Action Table Sketches

### Fodder
- Basic Attack 90% / Flee 10%
- In groups: Basic Attack 70% / Swarm (weak AOE) 30%
- Below 25% HP: Flee 60% / Basic Attack 40%

### Brute
- Heavy Strike 80% / Sweeping Blow 15% / Enrage 5%
- Player below 30% HP: 95/5/0 (smells blood)
- Brute below 25% HP: 40/10/50 (panic buffing)
- Player post-Cheat: aggression spike -> Heavy Strike 95%

### Caster
- Bolt (MAG damage) 50% / Hex (debuff) 30% / Barrier (self DEF buff) 20%
- Party has low RES: Hex 60% / Bolt 30% / Barrier 10% (punishes no RES)
- Caster below 40% HP: Bolt 70% / Hex 10% / Barrier 20% (panic damage)
- Ally Brute present: Barrier on Brute 30% (shifts to support role)

### Speeder
- Quick Strike 60% / Double Hit 25% / Evade Stance 15%
- Targets lowest-DEF party member by default
- No taunt active: Quick Strike 80% / Double Hit 20% / Evade 0% (all-in on squishies)
- Post-Cheat party member: priority target shift to vulnerable character

### Support
- Heal Ally 50% / Buff Ally 30% / Weak Attack 20%
- Ally below 40% HP: Heal 80% / Buff 10% / Attack 10%
- Last enemy standing: Weak Attack 40% / Self-Heal 40% / Desperate Buff 20%
- No damaged allies: Buff 60% / Weak Attack 30% / Heal 10%

---

## The Slime Curriculum

Slimes are **the tutorial disguised as enemies**. Each variant is a simplified preview of a real archetype.

> "i almost love the slime archetype. slime variants early. that's a classic for a reason. we can go slime heavy for the early game. and introduce variants past that. [...] slime world. slime reality. slime singularity." — designer

> (on Support archetype timing): "maybe it's like a post level 10/end-of-early-game thing, or maybe even like a boss introduction where you have giga slime with support slimes." — designer

### Slime Progression (Early Zones ~1-15)

| Zone | Encounter | What It Teaches |
|------|-----------|-----------------|
| 1-3 | Single slime, pairs of slimes | Basic combat, Cheat/Survive rhythm |
| 3-5 | Slime groups (3-4 weak slimes) | AOE/Chain value, action economy management |
| 5-8 | Variant slimes: Gel Slime (tanky), Spark Slime (casts), Quick Slime (fast) | Archetype differences — "this one takes hits, that one hurts, the fast one targets your Onmyoji" |
| 8-12 | Mixed variant groups, rare Support Slime toward end of range | First taste of "why won't this group die?" |
| 12-15 | **Giga Slime** (mini-boss) + Support Slime adds | Boss introduces Support archetype properly. "Kill the healers or Giga Slime never goes down." |

After Giga Slime, Support enemies appear in normal encounters. The boss taught the lesson; now it's applied.

After slimes, the "real" archetypes appear with full action tables and themed reskins. Player already knows the language.

### MVP Focus: Shinto (Slime World)

Slimes are the MVP early-game spec. Nordic/Abrahamic get equivalent fodder progressions (baby draugr, locust swarms) — reskins of the same curriculum. Design once, paint three times.

---

## Boss Design

- Phase transitions at HP thresholds.
- Each boss is a **harder version of an archetype combination** — Brute/Caster hybrid that switches phases.
- Bosses teach "you need answers for multiple archetypes simultaneously."
- Zone bosses scale with zone level. Final Boss is fixed power level (the gear/level check). God is the beyond.

---

## Themed Reskins (Per World)

Same archetype, different name and flavor, identical mechanics:

| Archetype | Nordic | Shinto | Abrahamic |
|-----------|--------|--------|-----------|
| Fodder | Draugr Husk | Slime / Kodama | Locust Swarm |
| Brute | Draugr / Troll | Oni | Nephilim |
| Caster | Volva | Kitsune | Seraph |
| Speeder | Fenris Pup | Tengu | Malakh |
| Support | Norn Fragment | Tanuki | Cherub |
