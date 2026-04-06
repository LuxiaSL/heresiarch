# Heresiarch — Game Meta

## Name

**Heresiarch** — the founder of a heresy. You're killing god — you ARE the heresiarch. Works across Norse, Shinto, and Abrahamic themes without belonging to any one.

## Tagline

> Pick a world, pick a job, descend, build synergy, kill god.

## Tone

Grinning at the player while they bleed out. Not winking, not serious — scrappy. Irreverent but mechanically serious. "Spreadsheet optimizer in a mythology blender."

> "we don't have to be Truly Faithful since most games aren't and this isn't trying to take itself seriously in that aspect. think aesthetic sensibilities vs accuracy." — designer

---

## World Themes

Three themed world pools. Mechanically identical — same stat budgets, same behavior archetypes, same scaling curves. Different flavor text, ability names, enemy names, area descriptions.

| Theme | Aesthetic | God | God Mechanic |
|-------|-----------|-----|-------------|
| **Nordic** | Frost, iron, runes, ash, world-tree | Ragnarok entity | Absurd DEF, reflects physical — demands MAG solution |
| **Shinto** | Shrines, spirits, paper, ink, seasons | Kami of the final gate | Extreme tempo, acts 3x/round — demands SPD |
| **Abrahamic** | Stone, light, seraphim, desert, scripture | The Throne | Heals to full every N rounds — demands burst window optimization |

World selection is per-run. Same engine, different paint.

### MVP Focus

Shinto first — slimes are the most natural JRPG onramp, and the aesthetic is the most immediately gamey. Nordic and Abrahamic are reskins of the same mechanical foundation.

---

## The God Fight

- After Final Boss. Marks completion of the "normal" game.
- Perfect information: knows your stats, equipment, cooldowns, abilities.
- Plays optimally.
- **Designed to be unbeatable by normal builds.** Win condition: hypersynergy — a build so degenerate the math breaks in your favor.
- You don't outplay god. You outscale god.
- That moment — fifty hours in, CHA maxed, full job roster, everything clicks — is the payoff.

---

## LLM Integration

**Design decisions (locked):**
- Flavor, not structure. LLM never decides mechanical outcomes.
- CHA modulates text richness. Low CHA: terse. High CHA: richer flavor, better hints.
- Use cases: area descriptions, combat narration, shop/event flavor, recruit descriptions, death recaps.

**Implementation (tabled):**
- Pre-generated vs runtime vs hybrid, model choice, caching strategy — deferred to implementation phase.

---

## Content Pipeline

### Seed -> Expand -> Curate

1. Hand-author seed sets (abilities, enemy archetypes, area templates) per world theme
2. LLM-expand within mechanical constraints
3. Curate: validate against balance, select for interesting decisions, assign to world themes

Three themes x one shared mechanical backbone = 3x content from 1x design work.
