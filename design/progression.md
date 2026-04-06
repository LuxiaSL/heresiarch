# Progression

## Level Cap: 99

Psychological hook: staring at "13/99" on early failed runs. "Breaking the limit" feeling as you push deeper. Potential for post-99 bonus levels unlocked through abilities/items/jobs.

## Expected Run Arcs

| Phase | Level Range | Notes |
|-------|------------|-------|
| Early (most starter runs die here) | ~1-15 | Learning the game, builds haven't come together |
| Mid | ~15-60 | Long grind, build identity solidifies |
| Late / endgame | ~60-99 | Degenerate scaling kicks in, god prep |

## Time Targets

- **Regions**: 10-15 mins to clear, up to 30-60 mins if grinding. Region caps on growth/loot to prevent infinite farming.
- **Failed runs**: A few hours.
- **Full runs**: Most of a day. Long but not painful — JRPG length meets roguelike structure.

> "if runs take a few hours each, that's fine; if it's a day per good/long run, pain." — designer

> "we should only ever expect a player to like be in a grindy region for <30~60 mins maybe? and most to take ~10-15 mins to clear, with grinding on top of that 10~15." — designer

---

## Acceleration System

Core philosophy: **don't enforce sunk cost.** Let players enjoy a build or reroll quickly.

> "we don't want to enforce sunk cost too much. surrendering could still incur the accel bonus." — designer

> "a forgiving 'okay, you nuked your run, but at least it won't take as long to get back to where you are' and then a tilt aspect that gets added when you lose a good run, then die in a silly way early, that gets rid of your early bonus." — designer

- **Milestone accelerators**: Reaching certain dungeons/levels/phases unlocks XP boosts / skip-to for future runs. "You died, but getting back won't take as long."
- **Tilt penalty**: Lose a good run -> die early on the next one -> lose early-phase acceleration bonus. Psychological punishment for tilting, not mechanical.
- **Surrender benefits**: Quitting a dead run still grants the acceleration bonus. Respects player time (Dignified Exit).
- **Permanent acceleration**: Meta-milestone perma-boosts, pairs naturally with achievement system and CHA accumulation.
- **Loot-based accelerators**: Straight XP/progress boosting items as drops.
- **Intentional late-loss meta**: Could be strategic value in losing late (banking something?), needs tradeoff so it's not dominant. Future design problem.

---

## Save System

**Permissive saves, permanent death.** The roguelike contract: saves respect your time, not your life.

- **No saving in combat.** Decisions in combat are committed.
- **Autosave option.** On zone transitions, shop exits, recruitment decisions, etc.
- **Save slots within a run.** Multiple save points you can load back to during a living run.
- **Run slots.** Multiple concurrent runs in parallel.
- **Death nukes all saves for that run.** The core roguelike tint. You can save-scum past a bad shop decision. You cannot save-scum past death. Timeline is gone.

> "once you die in a run, that run's saves get nuked. you cannot just load a save back. you risk the timeline if you die in a branched run. this is the roguelike tint." — designer

---

## Information Visibility (Progressive Reveal)

Earned, not given. Avoids info overload early while rewarding continued play.

> "at least very early on, shouldn't be *clear* what things are doing what outside of values. [...] think showing at *first* just the values raw post all calcs. then getting to see base calc vs scaled calc. then, getting a breakdown on where the scaling is coming from. that would feel clean and rewards continued play without overwhelming at first." — designer

| Stage | What You See | When |
|-------|-------------|------|
| **Raw** | Post-calc values only. "65 damage." No formula, no breakdown. | First runs (0-5) |
| **Basic scaling** | Base calc vs scaled calc. You can see THAT an item scales, and roughly how much. | ~5-10 runs |
| **Full breakdown** | Where scaling comes from — stat contributions, item coefficients, ability interactions. The spreadsheet view. | ~20+ runs |

- Players can still OBSERVE scaling by watching stat diffs and equip effects. Not invisible, just not surfaced.
- Ties to CHA and meta-progression — more runs = more information = better optimization.
- At high CHA: can inspect dungeon loot tables and unique drops.

---

## Death / Failed Run Feel

**Dark Souls energy.** Losses should hit so victories land.

> "something like YOU DIED or equivalent. i don't mind the dark souls vibe. like, if runs are taking a bit each time, we want the losses to hit so that once the player gets to that sweet, sweet victory, they can get there." — designer

- YOU DIED equivalent. The game doesn't soften it.
- **Run recap**: LLM generates 2-3 sentence flavor text themed to the world. Surfaces a highlight and the vibe.
- Future: recap could reference past runs, patterns, career arc.
- MVP: basic themed flavor text. Expand later.

---

## Loot Pacing

Hybrid: frequent small, rare meaningful.

- **Money drops**: every encounter, varied value. Feeds shop economy.
- **Common drops**: consumables, basic items. Frequent enough to always be evaluating.
- **Rare/unique drops**: one-time from Key Enemies. Build-defining moments.
- **CHA integration**: high CHA lets you inspect dungeon loot tables / unique drops.

> "there should be somewhat frequent small drops, always money drops of varied value, and rare/one-time item drops for like. Key Enemies. like, think about reaching the end of a dungeon and beating something with the item you've been looking for and getting it. or at high enough cha, you can inspect the dungeon for loot tables/unique drops." — designer
- Inventory tension — limited stash means every pickup is a keep/drop decision.

---

## Difficulty Philosophy

**Toothy from the start.** The game demands engagement, not mastery.

- Players SHOULD die before level 15 on early runs if they play poorly.
- All mechanics must be used to survive early: equip items, shop, Cheat/Survive, read enemy patterns.
- **First battle**: "are you paying attention?" gate. Not unfair, but punishes button-mashing.

> "we want players dying before they reach level 15 on some early runs if they just play poorly or don't somewhat optimize. we want players to use items they get, have to get something from a shop, they should be using all the mechanics of the game in some way early even if they don't optimize it [...] especially the first battle; it's like a proper test to make sure 'are you paying attention?'" — designer
- Teaches through death. Slime curriculum + toothy encounters = lessons learned through failure.
- Curve: toothy early -> builds come together mid -> optimization late -> degeneracy for god.
- Regular Final Boss is reachable with good play. God is the impossible wall requiring broken math.

---

## Meta-Progression

### Jobs
- Start with 2-3. Unlock more through run milestones.
- Wider, not easier.

### CHA
- Accumulates across runs. More information, harder optimization.
- Career arc: blind -> informed -> omniscient optimizer.
- NOT boostable by items — meta-progression only.

### Dignified Exit
- End dead runs early, bank partial progress.
- Respects player time without softening difficulty.
