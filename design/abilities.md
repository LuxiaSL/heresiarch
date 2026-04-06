# Abilities

## Design Principles

- Abilities are **nodes in an interaction graph**. Value comes from combinations, not individual power.
- Any ability interesting enough to build around could graduate into a job spec.
- Borrowed liberally from BD, FE, D&D, League — the interesting part is how they combine in THIS stat system.
- Jobs grant one innate ability (can't be swapped). Additional abilities come via accessory items.
- Enemies use the same ability pool (shared pool principle).

> "think of like typical archetypes, how they combine, especially with regard to our stat sets. there is a lot of solid moves that could be done here if we borrow from ideas in other games (like BD, fire emblem, DnD, league, etc.) that make things degenerate and open up synergy across all gates" — designer

> "an ability could turn into a job spec later if it's interesting enough to stand on its own in a build and be spec'd around" — designer

> (on the interaction graph): "imagining a networked graph of these things showing possible interactions is so cool... [...] a support/caster type that applies these abilities/effects to characters and creates weird synergies that otherwise would be inaccessible/require a specific drop" — designer

---

## Damage Qualities

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

Qualities combine (DOT + Pierce). World themes reskin flavor without changing math.

---

## Offensive Abilities (Droppable)

| Ability | Quality | Stat Scaling | Effect | Notes |
|---------|---------|-------------|--------|-------|
| **Searing Edge** | DOT | STR | Burn over N rounds, bypasses DEF | Bread and butter vs high-DEF |
| **Fracture** | Shatter | STR | Reduces target DEF for N rounds | Enabler for STR allies |
| **Arc Slash** | Chain | STR | Hits all enemies at reduced power | Mob clear |
| **Thrust** | Pierce | STR | Ignores % of DEF | Direct, good vs armor |
| **Hex** | Disrupt | MAG | Shifts enemy action weights / delays | Tempo control, pairs with Foresight |
| **Drain** | Leech | MAG | Heals for % of damage dealt | Sustain, enables low-DEF builds |
| **Crescendo** | Surge | MAG | Scaling damage with consecutive uses | Extended boss fight ability |
| **Reckless Blow** | -- | STR | Big damage + self-damage | Risk/reward, pairs with Leech |
| **Void Bolt** | -- | MAG | Degenerate scaling: weak early, monstrous late | "Trust the curve" |

---

## Defensive / Utility Abilities (Droppable)

| Ability | Stat Scaling | Effect | Notes |
|---------|-------------|--------|-------|
| **Damage Split** | DEF | Absorbs % of ally damage, redirected to self. Effects still hit original target. | Rare/unique. THE Martyr upgrade path. |
| **Brace Strike** | STR/DEF | Attack + minor DEF buff for 1 turn | Never a wasted action |
| **Anchor** | DEF | Reduces Disrupt-quality effects | Niche counter-pick |
| **Endure** | DEF/RES | Survive one lethal hit at 1 HP, once per fight | Clutch save. Enormous on tanks, interesting on glass cannons. |
| **Ward** | RES | Grants RES threshold buff to self or ally for N rounds | Push someone over the pass/fail gate temporarily |

---

## Support / Targeted Abilities (Droppable)

Abilities that apply effects TO allies — creating combos that would otherwise require specific drops on specific characters.

| Ability | Stat Scaling | Effect | Notes |
|---------|-------------|--------|-------|
| **Bestow Split** | MAG | Cast Damage Split on an ally | THE support enabler. Split on Einherjar -> Retaliate + Leech loop. |
| **Haste** | MAG/SPD | Grant ally bonus SPD for N rounds | Action economy gift. On a Berserker = obscene Cheat windows. |
| **Infuse** | MAG | Grant ally bonus MAG scaling on next attack | Lets STR characters briefly hit with MAG. Converter in ability form. |
| **Mark** | MAG | Mark enemy — all attacks gain bonus damage | Focus fire enabler. Scales with party size. |
| **Sacrifice** | DEF | Transfer own HP to ally | Martyr fantasy, literal. |

---

## Passive / Triggered Abilities (Droppable)

| Ability | Trigger | Effect | Notes |
|---------|---------|--------|-------|
| **Blood Rush** | Below X% HP | Bonus SPD | Edge-riding. Berserker + Blood Rush = terrifying when low. |
| **Vengeance** | Ally KO'd | Massive STR/MAG buff for N rounds | Comeback mechanic. Losing a party member isn't the end. |
| **Momentum** | Kill an enemy | Refund 1 action point | Snowball. Chain kills in mob fights. |
| **Counter-Hex** | RES threshold passed | Reflect debuff back to caster | Punishes magical enemies targeting high-RES. |
| **Siphon** | Survive being attacked | Gain small stacking MAG buff | Slow burn. Onmyoji equivalent of Retaliate. |

---

## Synergy Loops (The Good Stuff)

Examples of the degenerate combinations the game is designed to produce:

### The Immortal Wall (2-character)
> Einherjar w/ Retaliate (innate) + Leech item + Bestow Split from Onmyoji
> -> Allies get hit -> damage redirects to Einherjar -> retaliates -> Leech heals -> self-sustaining loop

### The Burst Window (3-character)
> Onmyoji Foresight -> sees boss Heavy Strike -> Martyr Taunts -> Berserker Cheats 3 actions -> Frenzy stacking x Fracture debuff -> boss phase deleted

### The Edge Rider (1-character, degenerate)
> Berserker w/ Blood Rush + Reckless Blow + Frenzy (innate)
> -> Reckless Blow self-damages into Blood Rush range -> SPD skyrockets -> more actions -> Frenzy stacks harder -> die or delete everything

### The Information Engine (2-character, meta)
> High-CHA Onmyoji w/ Foresight + Hex + Mark
> -> See enemy weights -> Disrupt dangerous ones -> Mark priority target -> party plays with near-perfect information

### The Converter Abomination (late-game, degenerate)
> Any character w/ DEF->MAG converter + Siphon + Crescendo
> -> Tank stats feeding magic -> getting hit makes you stronger -> Crescendo stacks -> "supposed" wall is now primary DPS

---

## Ability -> Job Graduation Candidates

| Ability Pattern | Potential Job | Fantasy |
|----------------|---------------|---------|
| Blood Rush + edge-riding | **Revenant** | The undying. Strongest at death's door. |
| Bestow Split + Haste + support casting | **Miko** | The enabler. Makes everyone else fight better. |
| Siphon + counter-magic + reflection | **Mirror/Vessel** | Absorbs magic, turns it into offense. |
| Momentum + Chain + mob clear | **Reaper/Ronin** | Kill chain specialist. |
| Mark + Hex + information control | **Oracle** | Pure control. "I decide who dies." |
