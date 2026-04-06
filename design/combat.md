# Combat

## Structure

- **Flat 3vX** — all 3 active party members are targetable. Reserve is safe.
- No positioning grid. No front/back row.
- Taunt and damage-split matter because enemies can hit anyone.

---

## Action Economy: Cheat / Survive

Replaces Brave/Default. Same mechanic — bank turns for defense, spend them for burst — renamed to fit the game's tone.

- **Cheat**: Spend banked action points for multiple actions. Vulnerable afterward until debt repaid. The word works at every layer — cheating the action economy, cheating scaling curves with degenerate builds, cheating god.
- **Survive**: Bank a turn, reduce incoming damage, store an action point. Honest and desperate. That's what defaulting actually is — scraping by until your moment comes.

The pair sets the game's voice: grinning at the player while they bleed out. Not winking, not serious — scrappy.

> "cheat/survive. i want the vibe of the latter, the way you put it. the favorit thing i can come up with are greed traps. and respect falls a tiny bit flat compared to greed. but cheat/survive both hit strong tones." — designer

### Interactions

- SPD partial actions fill the post-Cheat vulnerability gap
- Cheating fires cooldowns sooner -> potential dead zones
- Enemies punish post-Cheat vulnerability (aggression spikes)
- Roguelike tension: Cheat to nuke trash and risk being empty for a miniboss?

### Rejected Alternatives

- **Greed / Respect** — Respect falls flat next to Greed. Greed carries, Respect doesn't match.
- **Bloom / Prune** — too soft, obscures the risk.
- **Ruin / Endure** — too close to Brave/Default.
- **Rage / Weather** — Norse-specific, better as themed flavor text.
- **Leverage / Hedge** — on-tone but too clever for a core mechanic.

---

## Tank Role

- Starter set includes one wall option (Martyr, DEF/RES).
- Taunt is a **job innate** on Martyr — not a general ability drop.
- Soft role requirement: necessary for ~most runs, skippable on god rolls.
- AOE absorption / damage split is a separate droppable ability or unique item (not baked into Taunt).
- Fits the roguelike "work with what you find" ethos.

> "taunt mechanisms and aoe-absorption are interesting mechanics to work around. shouldn't be *fully* necessary, but should be for ~most runs unless you're hitting a god roll." — designer

> (on damage split being separate from taunt): "we want taunt to be specialized/not overpowered [...] that shows like, the direction that abilities want to head." — designer

---

## Turn Order

- Everyone acts every round (players and enemies).
- SPD determines bonus partial actions via threshold (see stats-and-formulas.md).
- Cheat/Survive decisions happen at the start of a character's turn.
- Enemies respond to post-Cheat vulnerability states via conditional action table modifiers.
