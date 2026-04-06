# Jobs

## Naming Philosophy

Jobs pull their name from whichever mythology owns that archetype hardest. Aesthetic sensibility over historical accuracy — playful, not faithful. A Shinto-named class in the Norse world is just style.

> "we should *specialize* from each. whichever type of job feels like it fits best for a given mythology; and optimizing within their [...] whichever one is more ubiquitous/specific for its own mythology would be good." — designer

## Job Definition

A job is:
- Growth vector (STR/MAG/DEF/RES/SPD rates)
- HP curve (base_hp + hp_growth)
- Innate ability
- That's it. No equipment masks — the math does the policing (see items-and-equipment.md).

---

## Starter Jobs

| Job | Origin | Stats | Fantasy |
|-----|--------|-------|---------|
| **Einherjar** | Norse | STR/DEF | The chosen dead. Hits hard, takes hits, doesn't care about speed. Reliable. |
| **Onmyoji** | Shinto | MAG/RES | Spiritual diviner. Setup-dependent magic, strong ward against magical effects. |
| **Martyr** | Abrahamic | DEF/RES | The wall. Absorbs suffering for the party. Taunt/AOE-absorption fantasy. |
| **Berserker** | Norse | STR/SPD | Fast physical striker. Glass cannon, lives in Cheat windows. Rage = reckless offense. |

---

## Growth Vector Design

### Budget Philosophy

- **Equal budget across all starter jobs.** No job gets more total stats — just different shapes.
- **Universal base floor**: every character gets 1/level in each stat regardless of job. No stat is ever truly dead.
- **Budget points** stack on top of the base floor. This is where job identity lives.
- **Starter budget: 10 points** (+ 5 base = 15 total growth/level)
- Later unlockable jobs may have **different budgets** — tighter with sharper spikes (specialist), or weirder distributions that only work with specific items.

### Starter Growth Vectors (First Pass)

Budget distribution (the +X on top of base 1):

| Job | +STR | +MAG | +DEF | +RES | +SPD | Budget |
|-----|------|------|------|------|------|--------|
| **Einherjar** | +4 | +0 | +4 | +0 | +2 | 10 |
| **Onmyoji** | +0 | +4 | +0 | +4 | +2 | 10 |
| **Martyr** | +0 | +0 | +5 | +4 | +1 | 10 |
| **Berserker** | +4 | +0 | +0 | +0 | +6 | 10 |

Effective total growth per level (base + budget):

| Job | STR | MAG | DEF | RES | SPD | Total |
|-----|-----|-----|-----|-----|-----|-------|
| **Einherjar** | 5 | 1 | 5 | 1 | 3 | 15 |
| **Onmyoji** | 1 | 5 | 1 | 5 | 3 | 15 |
| **Martyr** | 1 | 1 | 6 | 5 | 2 | 15 |
| **Berserker** | 5 | 1 | 1 | 1 | 7 | 15 |

### Stat Snapshots at Key Levels

**Level 15 (early run failure):**

| Job | STR | MAG | DEF | RES | SPD |
|-----|-----|-----|-----|-----|-----|
| Einherjar | 75 | 15 | 75 | 15 | 45 |
| Onmyoji | 15 | 75 | 15 | 75 | 45 |
| Martyr | 15 | 15 | 90 | 75 | 30 |
| Berserker | 75 | 15 | 15 | 15 | 105 |

**Level 50 (mid-game):**

| Job | STR | MAG | DEF | RES | SPD |
|-----|-----|-----|-----|-----|-----|
| Einherjar | 250 | 50 | 250 | 50 | 150 |
| Onmyoji | 50 | 250 | 50 | 250 | 150 |
| Martyr | 50 | 50 | 300 | 250 | 100 |
| Berserker | 250 | 50 | 50 | 50 | 350 |

**Level 99 (cap):**

| Job | STR | MAG | DEF | RES | SPD |
|-----|-----|-----|-----|-----|-----|
| Einherjar | 495 | 99 | 495 | 99 | 297 |
| Onmyoji | 99 | 495 | 99 | 495 | 297 |
| Martyr | 99 | 99 | 594 | 495 | 198 |
| Berserker | 495 | 99 | 99 | 99 | 693 |

### Observations

- **Einherjar/Onmyoji are clean mirrors** — physical vs magical, same shape.
- **Martyr has the fattest DEF (594)** -> biggest HP pool (DEF feeds HP). The wall fantasy works.
- **Berserker trades ALL defense for speed** — shares STR primary with Einherjar but is made of glass.
- **Dump stats at 99 are still 99** — converter items always have something to feed on.
- **Martyr does no damage on their own** (STR 99, MAG 99) — damage comes from enabling allies.

---

## Innate Job Abilities

Jobs now grant one innate ability. Drops still provide the bulk of abilities, but the innate gives each job a playable identity from floor 1.

### Martyr — Taunt

- **Cooldown**: 3-4 turns (or 3-4 Cheat cost)
- **Duration**: 1 turn. Forces prediction/timing.
- **Scaling**: Weak at first, strengthens at level cutoffs through the run curve.
- Experienced players time taunt to intercept spikes. Pairs with Foresight and CHA information.

### Onmyoji — Foresight

- Reveals enemy action weights for the next turn. At base, shows top-weighted action only. Scales to show full probability spread at higher levels.
- Turns combat from "guess and react" to "read and plan."
- Synergy with Martyr: see the spike coming, taunt to intercept.
- CHA modulates this too — double-scaling path (level + CHA).

### Einherjar — Retaliate

- Passive counter-attack when hit. Scales with STR.
- The "just does good" ability. Reliable, always-on value. Carries early.
- Teaches that target selection matters.
- **Late-game potential**: on-hit trigger items turn Retaliate into a whole build axis.

### Berserker — Frenzy

- Each consecutive attack in the same turn (via Cheat) deals increasing damage.
- THE Cheat synergy class. Stacking consecutive hits is their whole identity.
- Teaches Cheat timing and burst windows from the first fight.
- Frenzy scaling x STR scaling x Cheat depth = god-killing burst.

### Design Implications

- Innate abilities create **party synergies from draft alone**: Onmyoji reads, Martyr intercepts, Einherjar retaliates, Berserker explodes.
- Each innate teaches a core mechanic: Taunt -> enemy patterns, Foresight -> action tables, Retaliate -> target selection, Frenzy -> Cheat timing.

---

## Specialization Sharpness

Starters are moderate — two strong stats, functional everywhere thanks to base floor. Future unlockable jobs get sharper:

> "we could legit just have some classes be specialized and some well rounded but in lightly lopsided ways so that you have ones that are more hit/miss that unlock later but ones that are stable for early game while learnin the ropes. enhances the god run feel." — designer
- Tighter budgets (8-9 instead of 10) with extreme spikes
- Weird distributions that only shine with specific items/converters
- "Go big or go home" jobs that are bad on average but enable degenerate builds
- Enhances the god-run feel: stable starters for learning, scalpel specialists for mastery

---

## Endgame Capstone: God Job (Name TBD)

Super-late meta-unlock (beat god?). **Player allocates their own budget.** Equip anything. The ultimate "you've mastered the system, now break it" reward. Custom growth vector = consistent god kills without needing perfect RNG. Could use a larger budget than standard jobs.

---

## Future Unlockable Job Ideas

| Job | Origin | Stats | Source |
|-----|--------|-------|--------|
| **Zealot** | Abrahamic | MAG/SPD | Fast magical aggression. Different risk profile from Onmyoji. |
| **Revenant** | TBD | STR or MAG / SPD (tight budget) | Graduates from Blood Rush ability pattern. Strongest at death's door. |
| **Miko** | Shinto | MAG/DEF or MAG/SPD | Graduates from support casting pattern. The enabler. |
| **Mirror/Vessel** | TBD | RES/MAG | Graduates from Siphon + counter-magic. Anti-mage. |
| **Reaper/Ronin** | Shinto | STR/SPD (extreme) | Graduates from Momentum + Chain. Kill chain specialist. |
| **Oracle** | TBD | MAG/RES (CHA-scaling?) | Graduates from Mark + Hex + information control. Pure control. |

### Rejected Alternatives for STR/SPD Starter

- Samurai (Shinto) — exact fit but overused.
- Zealot (Abrahamic) — better as MAG/SPD, potential future unlockable.
- Ninja — overused, doesn't fit.
