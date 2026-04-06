# Stats & Formulas

## Combat Stats

Five combat stats, one meta stat.

| Stat | Role | Design |
|------|------|--------|
| **STR** | Physical offense | Reliable, linear. The consistent stat. Gets you home on bad runs. |
| **MAG** | Magical offense | Conditional, multiplicative. Weak at baseline, explosive with setup. Setup-dependent and back-loaded. |
| **DEF** | Physical defense + HP | Flat reduction against STR-type damage. Also sole stat contributor to HP — DEF = physical durability, full stop. |
| **RES** | Magical defense | Threshold system — pass/fail gate. If RES exceeds incoming MAG by a ratio, secondary effects fully resisted. Below threshold, they go through entirely. |
| **SPD** | Action density | Everyone acts every round. SPD thresholds grant bonus partial actions. Always nice, never mandatory. |
| **CHA** | Non-combat, cross-run | Persists across runs. Affects: recruit inspection depth, shop prices, event outcomes, information visibility. Meta-progression only — NOT boostable by items/accessories. |

Every stat should feel overpowered when specialized.

---

## HP System

HP is derived, not standalone:

```
HP = job_base_hp + (job_hp_growth * level) + (DEF * hp_coefficient)
```

- `hp_coefficient` ~ 1.5-2.0 (tunable)
- DEF double-dips (reduces damage AND adds HP) — intentional, tanks should feel tanky
- RES does NOT contribute to HP — stays pure as magic pass/fail gate
- This gives DEF relevance on every build. Even a caster wants some DEF or their HP pool is paper-thin.

### Job HP Curves (First Pass)

| Job | base_hp | hp_growth | Notes |
|-----|---------|-----------|-------|
| Einherjar | 50 | 8 | Solid. Not the wall, but durable. |
| Onmyoji | 30 | 5 | Fragile. Relies on RES gate, not HP pool. |
| Martyr | 70 | 12 | The deepest pool. This is the taunt target. |
| Berserker | 25 | 4 | Paper. Lives or dies by not getting hit. |

### HP at Level 15

| Job | Base + Growth | + DEF contribution (DEF x 1.5) | Total HP |
|-----|-------------|-------------------------------|----------|
| Einherjar | 50 + 120 = 170 | 75 x 1.5 = 112 | **282** |
| Onmyoji | 30 + 75 = 105 | 15 x 1.5 = 22 | **127** |
| Martyr | 70 + 180 = 250 | 90 x 1.5 = 135 | **385** |
| Berserker | 25 + 60 = 85 | 15 x 1.5 = 22 | **107** |

Martyr has 3.6x the HP of a Berserker at level 15. The wall is a wall, the glass cannon is glass.

---

## Damage Formulas

### Physical Damage

```
raw_damage = ability_base + (ability_coefficient * STR) [+ item_scaling(STR)]
damage_taken = max(1, raw_damage - DEF_reduction)
DEF_reduction = target_DEF * 0.5
```

- DEF as flat reduction at 50% efficiency. High-DEF targets are tough but never invincible.
- `max(1)` — chip damage always gets through. No full immunity.
- Item scaling stacks additively with ability damage before DEF reduction.

### Magical Damage

```
raw_damage = ability_base + (ability_coefficient * MAG) [+ item_scaling(MAG)]
damage_taken = raw_damage  (no flat reduction from RES)
```

- MAG damage is NOT reduced by RES. RES is a pass/fail gate for secondary effects only.
- MAG damage is consistent but lower-coefficient than STR to compensate — paying for reliability.

### RES Threshold (Pass/Fail Gate)

```
if target_RES >= incoming_MAG * threshold_ratio:
    secondary effects (DOT, debuffs) are FULLY RESISTED
else:
    secondary effects apply at full strength
```

- `threshold_ratio` ~ 0.6-0.7 (tunable). At 0.7: need 70% of caster's MAG as RES to resist.
- Binary. No partial resist. Either gate it or eat it.
- Makes RES a build-around stat: either invest enough to hit the gate, or don't bother.

### SPD -> Bonus Actions

```
bonus_actions = floor(SPD / spd_threshold)
```

- `spd_threshold` ~ 100 (tunable)
- At SPD 105 (Berserker level 15): 1 bonus action
- At SPD 693 (Berserker level 99): 6 bonus actions
- Partial actions are weaker than full actions — maybe 50% damage, or restricted to specific ability types
- SPD always valuable but never mandatory. 0 bonus actions is fine.

---

## Item Scaling Curves

Tuned to stat range (~500 at cap).

### Crossover Design Intent

- **Linear** is best early game (levels 1-30ish). Reliable, no conditions.
- **Superlinear** overtakes linear mid-game (~level 35, primary stat ~175). Build starts paying off.
- **Quadratic** overtakes superlinear late-game (~level 60+). Deep commitment required.
- **Degenerate** is NEGATIVE until late mid-game (~level 40-50, primary stat ~200+). Actively hurts you until it doesn't. Then it's the best thing in the game.

### Scaling Formulas (First Pass)

```
Linear:       damage = base + 1.0 * STAT
Superlinear:  damage = base + 0.3 * STAT + 0.004 * STAT^2
Quadratic:    damage = base + 0.008 * STAT^2
Degenerate:   damage = -200 + 0.01 * STAT^2
```

### Crossover Table

| STR | Linear (base=20) | Superlinear (base=20) | Quadratic (base=20) | Degenerate |
|-----|------|------|------|------|
| 15 (dump, lv15) | 35 | 21 | 22 | -198 |
| 75 (primary, lv15) | 95 | 65 | 65 | -144 |
| 150 (primary, lv30) | 170 | 155 | 200 | 25 |
| 175 (crossover) | 195 | 195 | 265 | 106 |
| 250 (primary, lv50) | 270 | 345 | 520 | 425 |
| 400 (primary, lv80) | 420 | 780 | 1300 | 1400 |
| 495 (primary, lv99) | 515 | 1130 | 1980 | 2250 |

- Linear leads until STR ~175
- Superlinear overtakes at ~175, stays strong through mid-game
- Degenerate crosses zero around STR ~141 (level ~28 for primary stat)
- At level 99: Degenerate is 4.4x Linear — the "break the math" moment

### Converter Item Formulas

Same formula structure but with stat substitution:

```
DEF->MAG Shield:    mag_bonus = 0.004 * DEF^2    (superlinear, converts tank stat to offense)
SPD->STR Gauntlet:  str_bonus = 0.3 * SPD        (linear, safe conversion)
```

Enemies can equip converters too (shared pool). A Brute with a DEF->STR converter is a nightmare.

### Enemy Stat Budgets Per Zone

```
enemy_budget = zone_level * budget_multiplier
```

| Archetype | budget_multiplier | Distribution Shape |
|-----------|------------------|-------------------|
| Fodder | 8 | Flat, slightly STR-heavy |
| Brute | 14 | STR/DEF spike, low SPD |
| Caster | 12 | MAG spike, low DEF/HP |
| Speeder | 11 | SPD/STR, very low DEF |
| Support | 10 | Balanced, slightly MAG/RES |
| Boss | 20+ | Varies by boss, multi-stat |

### Sanity Check: Level-15 Einherjar vs Zone-15 Brute

Brute budget = 15 x 14 = 210: STR 70, MAG 10, DEF 60, RES 10, SPD 15, HP ~250

- Einherjar with Iron Blade: raw = 20 + 75 = 95, after DEF (60 x 0.5 = 30): **65 damage**
- Brute needs ~4 hits to kill (250 / 65)
- Brute Heavy Strike hits Einherjar for ~65 after DEF
- Einherjar survives ~4 hits (282 HP)
- **Even fight with slight player advantage** (player has abilities, items, party). Feels right.
