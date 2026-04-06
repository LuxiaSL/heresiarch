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
