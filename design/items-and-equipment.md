# Items & Equipment

## Equipment Slots

**4 slots per character.** Clean, tight, every slot matters.

| Slot | Role | Notes |
|------|------|-------|
| **Weapon** | Offense scaling | Where damage formulas live. STR swords, MAG catalysts, hybrid weapons. |
| **Armor** | Survival broadly | DEF and/or RES contribution, HP. Heavy plate, light robes, etc. |
| **Accessory 1** | Anything | Abstract, untyped. The item defines itself. |
| **Accessory 2** | Anything | Same pool as Accessory 1. |

## No Equipment Restrictions

**The League approach.** Anyone can equip anything. The math does the policing.

- An Onmyoji equipping a STR sword gets garbage damage (99 STR at cap). The scaling curve says "you shouldn't."
- But: Onmyoji + STR->MAG converter accessory + STR sword = the converter feeds MAG through the sword's formula. That's not a mistake, that's a BUILD.
- Off-label use is allowed and sometimes brilliant. Best builds will be ones we didn't intend.
- Natural punishment for bad equips, natural reward for creative ones.

> "some of the most fun league builds are off-label and weird. esp if it definitely wasn't intended at first but happens to fall out of it. [...] there can be items clearly meant for certain classes but you can equip them on anyone and it can just either be Shit on them or good. the league approach." — designer

---

## Accessories

Abstract and untyped. The item defines what it does, not the slot.

> "accessories should be kept abstract. they're the most free-flowing of them all." — designer

They can:

- Grant flat stat boosts (base OR scaling — commits to one)
- Grant abilities (from the shared pool — this is how you get abilities beyond your innate)
- Grant conversions (DEF->MAG, SPD->STR, etc.)
- Grant utility (XP accelerators, loot finders — NOT CHA boosters, CHA is meta-progression only)
- Interact with other equipped items (weapon synergies, armor synergies)
- Grant special/unique stats or effects
- Scale at breakpoints like other items

Early accessories = simple stat bumps. Mid-game = specific synergies. Late-game = hypersynergy glue, the difference between a good build and a god-killing build.

---

## Inventory Math

- 4 slots x 4 party members = 16 equipped items
- Shared party stash (~8-10 slots)
- Backup character holds 4 items of gear that walks away on recruitment (the greed trap)

---

## Stat Computation Stack

Items don't have independent damage calculations — they merge onto stats. All damage, all abilities, all thresholds read from the same effective stats. The stack is:

```
Layer 1: BASE STATS
  From level-ups + growth vectors. Pure character identity.

Layer 2: FLAT MODS (additive to base)
  Items that add flat values directly to stats.
  e.g., Endurance Plate: DEF +10
  These INCREASE the input to Layer 3 scaling.
  Multiple Layer 2 items stack additively.

Layer 3: SCALING MODS (reads Layer 1+2, writes to effective)
  Weapon/item scaling formulas that read (base + flat mods) and compute a bonus.
  e.g., Iron Blade: 20 + 1.0 * augmented_STR → added to effective STR
  Different curves (linear, quadratic, degenerate) live here.
  This is where item identity lives — same stat, wildly different value curves.

Layer 4: EFFECTIVE MODS (reads current effective, writes to effective)
  Converters: read from one effective stat, add to another.
    e.g., Fortress Ring: reads effective DEF, converts to MAG bonus
  Buffs/debuffs: temporary combat modifiers. Most live here.
  Special effects can target specific layers for stronger/weaker interactions.
```

**No feedback loops**: each layer only reads upward. Layer 3 reads (1+2), never 3 or 4. Layer 4 reads (1+2+3), never feeds back.

**What reads from effective stats**: ability damage, retaliate, SPD bonus actions, max HP (via DEF), ability stat requirements, combat resolution. Everything.

**Converters are flexible**: they can theoretically be placed at any layer depending on the design intent. A DEF→MAG converter at Layer 2 would increase weapon scaling inputs. At Layer 4 it adds to final effective. The layer placement IS the balance lever.

**Buffs/debuffs are the same**: most are Layer 4, but special ones could target Layer 2 (stronger — affects weapon scaling downstream) or Layer 3 (modifies the scaling formula itself). This is extendable without changing the core architecture.

> "items should be simple. they shouldn't have their own independent calculations; they should just interact with the stats and boost them directly, that way it carries through to the rest much easier." — designer

---

## Seed Item Set

| Item | Slot | Scaling | Stat | Formula | Fantasy |
|------|------|---------|------|---------|---------|
| **Iron Blade** | Weapon | Linear | STR | 20 + 1.0 * STR | Reliable. Gets you home. |
| **Runic Edge** | Weapon | Superlinear | STR | 15 + 0.3*STR + 0.004*STR^2 | Investment piece. Mid-game spike. |
| **Void Fang** | Weapon | Degenerate | STR | -200 + 0.01*STR^2 | Hurts you early. Kills god late. |
| **Spirit Lens** | Weapon | Linear | MAG | 20 + 1.0 * MAG | Caster equivalent of Iron Blade. |
| **Resonance Orb** | Weapon | Quadratic | MAG | 15 + 0.008*MAG^2 | Deep MAG commitment. Onmyoji dream. |
| **Fortress Ring** | Accessory | Converter | DEF->MAG | mag_bonus = 0.004*DEF^2 | Martyr becomes a caster? Off-label enabler. |
| **Gale Brace** | Accessory | Converter | SPD->STR | str_bonus = 0.3*SPD | Berserker's speed feeds damage. |
| **Leech Fang** | Accessory | Utility | -- | Heals wielder for 15% of damage dealt | Sustain. Enables Retaliate loop. |
| **Endurance Plate** | Armor | Defensive | DEF | HP + 0.5*DEF extra reduction | Tank item. Stacks with natural DEF. |

## Emergent Rarity

From curve shape, not labels:
- **Common**: Linear, frontloaded
- **Uncommon**: Slightly superlinear, mid-game
- **Rare**: Quadratic / inflection-point, build-defining late
- **Degenerate**: Negative at low stats, godlike at high. Go-big-or-go-home.

## Converter Items

Bridge stat axes. The primary mid-run adaptation mechanism.

Same formula structure as regular items but with stat substitution. Enemies can equip converters too (shared pool). A Brute with a DEF->STR converter is a nightmare.
