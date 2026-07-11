# Run Trace: run_d9f92b01 (einherjar 'luxerjar' L10)

**Final state**: L10 · HP 269/310 · 2130g · zones cleared: ['zone_01', 'zone_02', 'zone_03']
**Encounters**: 61
**Macro events**: 178

## Legend

- Round line: `rN hp H→H' ap A st=<statuses> | DECISION primary→target +extras×N +bonus×N | dealt X · took Y · retal Z · KILL foo | end [enemy hp]`
- `hp H→H'` is pre→post-round MC HP. `ap A` is PRE-decision AP (what the policy saw). `st=` is active statuses at round start (taunted, marked, etc.) — inferred from events.
- SURVIVE banks +1 AP (capped at 3). CHEAT(+NAP) spends N AP. NORMAL is a regular turn, no AP change.
- Macro event header: `[seq=N event_type zone]` with L#/HP%/gold context.

---

### [seq=0 run_start]
_L1 · HP 100% · 0g · stash 0/10 · enc_at_time=0_
- start: luxerjar (einherjar)

### [seq=1 enter_zone] zone_01
_L1 · HP 100% · 0g · stash 0/10 · enc_at_time=0_
- enter zone_01 (already_cleared=False, via=zone_select)

### ENC 0 [zone_01 idx=0] vs fodder_slime → **VICTORY** (5 rounds)
_dealt 18, took 3, healed 0_

- **r1** hp ?→65 ap 0 st=— | **SURVIVE** | (no events) | end [fodder_slime=36]
- **r2** hp 65→64 ap 1 st=— | **SURVIVE** | took 1 | end [fodder_slime=30]
- **r3** hp 64→63 ap 2 st=— | **SURVIVE** | took 1 | end [fodder_slime=24]
- **r4** hp 63→62 ap 3 st=— | **SURVIVE** | took 1 | end [fodder_slime=18]
- **r5** hp 62→62 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 | dealt 18 · KILL fodder_slime | end [fodder_slime=0]

### [seq=2 pick_loot] zone_01
_L1 · HP 95% · 15g · stash 0/10 · enc_at_time=1_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 1 [zone_01 idx=1] vs fodder_slime, fodder_slime → **VICTORY** (7 rounds)
_dealt 18, took 9, healed 0_

- **r1** hp ?→62 ap 0 st=— | **SURVIVE** | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 62→60 ap 1 st=— | **SURVIVE** | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r3** hp 60→59 ap 2 st=— | **SURVIVE** | took 1 | end [fodder_slime=30, fodder_slime=24]
- **r4** hp 59→57 ap 3 st=— | **SURVIVE** | took 2 | end [fodder_slime=24, fodder_slime=18]
- **r5** hp 57→55 ap 3 st=— | **SURVIVE** | took 2 | end [fodder_slime=18, fodder_slime=12]
- **r6** hp 55→53 ap 3 st=— | **SURVIVE** | took 2 | end [fodder_slime=12, fodder_slime=6]
- **r7** hp 53→53 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 | dealt 18 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=3 pick_loot] zone_01
_L1 · HP 82% · 37g · stash 1/10 · enc_at_time=2_
- money +22g, offered=['crusader_tonic'], **selected**=['crusader_tonic'], skipped=[], discarded_stash=[]

### ENC 2 [zone_01 idx=2] vs fodder_slime, fodder_slime → **VICTORY** (6 rounds)
_dealt 24, took 8, healed 0_

- **r1** hp ?→52 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=36, fodder_slime=30]
- **r2** hp 52→50 ap 1 st=— | **SURVIVE** | took 2 | end [fodder_slime=30, fodder_slime=24]
- **r3** hp 50→48 ap 2 st=— | **SURVIVE** | took 2 | end [fodder_slime=24, fodder_slime=18]
- **r4** hp 48→47 ap 3 st=— | **SURVIVE** | took 1 | end [fodder_slime=18, fodder_slime=18]
- **r5** hp 47→45 ap 3 st=— | **SURVIVE** | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r6** hp 45→45 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 | dealt 24 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=4 pick_loot] zone_01
_L2 · HP 56% · 60g · stash 1/10 · enc_at_time=3_
- money +23g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 3 [zone_01 idx=3] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (5 rounds)
_dealt 0, took 12, healed 0_

- **r1** hp ?→44 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=36, fodder_slime=36, fodder_slime=27]
- **r2** hp 44→41 ap 1 st=— | **SURVIVE** | took 3 | end [fodder_slime=27, fodder_slime=27, fodder_slime=18]
- **r3** hp 41→38 ap 2 st=— | **SURVIVE** | took 3 | end [fodder_slime=18, fodder_slime=18, fodder_slime=9]
- **r4** hp 38→35 ap 3 st=— | **SURVIVE** | took 3 · KILL fodder_slime | end [fodder_slime=9, fodder_slime=9, fodder_slime=0]
- **r5** hp 35→33 ap 3 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=5 pick_loot] zone_01
_L2 · HP 41% · 90g · stash 1/10 · enc_at_time=4_
- money +30g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=6 leave_zone]
_L2 · HP 41% · 90g · stash 1/10 · enc_at_time=4_
- leave zone_01: reason=voluntary_leave, enc_idx=4, overstay=0, cleared=False

### [seq=7 enter_town] (in shinto_town)
_L2 · HP 41% · 90g · stash 1/10 · enc_at_time=4_
- enter town shinto_town

### [seq=8 shop_buy] (in shinto_town)
_L2 · HP 41% · 60g · stash 2/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=9 shop_buy] (in shinto_town)
_L2 · HP 41% · 30g · stash 3/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=10 leave_town]
_L2 · HP 41% · 30g · stash 3/10 · enc_at_time=4_
- leave town shinto_town

### [seq=11 use_consumable]
_L2 · HP 100% · 30g · stash 2/10 · enc_at_time=4_
- use minor_potion on mc_einherjar (HP 33→81/81)

### [seq=12 enter_zone] zone_01
_L2 · HP 100% · 30g · stash 2/10 · enc_at_time=4_
- enter zone_01 (already_cleared=False, via=zone_select)

### ENC 4 [zone_01 idx=4] vs alpha_slime → **VICTORY** (11 rounds)
_dealt 14, took 60, healed 0_

- **r1** hp ?→73 ap 0 st=— | **SURVIVE** | took 8 | end [alpha_slime=83]
- **r2** hp 73→65 ap 1 st=— | **SURVIVE** | took 8 | end [alpha_slime=76]
- **r3** hp 65→63 ap 2 st=— | **SURVIVE** | took 2 | end [alpha_slime=69]
- **r4** hp 63→61 ap 3 st=— | **SURVIVE** | took 2 | end [alpha_slime=62]
- **r5** hp 61→53 ap 3 st=— | **SURVIVE** | took 8 | end [alpha_slime=55]
- **r6** hp 53→51 ap 3 st=— | **SURVIVE** | took 2 | end [alpha_slime=48]
- **r7** hp 51→43 ap 3 st=— | **SURVIVE** | took 8 | end [alpha_slime=41]
- **r8** hp 43→41 ap 3 st=— | **SURVIVE** | took 2 | end [alpha_slime=34]
- **r9** hp 41→33 ap 3 st=— | **SURVIVE** | took 8 | end [alpha_slime=27]
- **r10** hp 33→25 ap 3 st=— | **SURVIVE** | took 8 | end [alpha_slime=20]
- **r11** hp 25→21 ap 3 st=— | **CHEAT(+3AP)** basic_attack→alpha_slime +cheat_extras×3 | dealt 7 · took 4 · retal 7 · KILL alpha_slime | end [alpha_slime=0]

### [seq=13 pick_loot] zone_01
_L2 · HP 26% · 93g · stash 6/10 · enc_at_time=5_
- money +63g, offered=['minor_potion', 'spirit_lens', 'cast_quick_strike', 'cast_bolt'], **selected**=['minor_potion', 'spirit_lens', 'cast_quick_strike', 'cast_bolt'], skipped=[], discarded_stash=[]

### [seq=14 use_consumable] zone_01
_L2 · HP 88% · 93g · stash 5/10 · enc_at_time=5_
- use minor_potion on mc_einherjar (HP 21→71/81)

### ENC 5 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 27, took 1, healed 0_

- **r1** hp ?→70 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=27]
- **r2** hp 70→70 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 27 · KILL fodder_slime | end [fodder_slime=0]

### [seq=15 pick_loot] zone_01
_L2 · HP 86% · 103g · stash 5/10 · enc_at_time=6_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=16 leave_zone]
_L2 · HP 86% · 103g · stash 5/10 · enc_at_time=6_
- leave zone_01: reason=voluntary_leave, enc_idx=5, overstay=1, cleared=True

### [seq=17 enter_town] (in shinto_town)
_L2 · HP 86% · 103g · stash 5/10 · enc_at_time=6_
- enter town shinto_town

### [seq=18 shop_buy] (in shinto_town)
_L2 · HP 86% · 3g · stash 6/10 · enc_at_time=6_
- **BOUGHT** iron_blade @ 100g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=19 equip] (in shinto_town)
_L2 · HP 86% · 3g · stash 5/10 · enc_at_time=6_
- equip iron_blade → mc_einherjar:WEAPON (displaced=None)

### [seq=20 leave_town]
_L2 · HP 86% · 3g · stash 5/10 · enc_at_time=6_
- leave town shinto_town

### [seq=21 enter_zone] zone_02
_L2 · HP 86% · 3g · stash 5/10 · enc_at_time=6_
- enter zone_02 (already_cleared=False, via=zone_select)

### [seq=22 leave_zone]
_L2 · HP 86% · 3g · stash 5/10 · enc_at_time=6_
- leave zone_02: reason=voluntary_leave, enc_idx=0, overstay=0, cleared=False

### [seq=23 enter_zone] zone_01
_L2 · HP 86% · 3g · stash 5/10 · enc_at_time=6_
- enter zone_01 (already_cleared=True, via=zone_select)

### ENC 6 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 48, took 0, healed 0_

- **r1** hp ?→70 ap 0 st=— | **SURVIVE** | (no events) | end [fodder_slime=36]
- **r2** hp 70→70 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 48 · KILL fodder_slime | end [fodder_slime=0]

### [seq=24 pick_loot] zone_01
_L2 · HP 86% · 13g · stash 5/10 · enc_at_time=7_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 7 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (4 rounds)
_dealt 0, took 9, healed 0_

- **r1** hp ?→68 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=29, fodder_slime=29, fodder_slime=52]
- **r2** hp 68→65 ap 1 st=— | **SURVIVE** | took 3 | end [fodder_slime=6, fodder_slime=6, fodder_slime=29]
- **r3** hp 65→63 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime | end [fodder_slime=6, fodder_slime=0, fodder_slime=6]
- **r4** hp 63→61 ap 3 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=25 pick_loot] zone_01
_L3 · HP 64% · 65g · stash 5/10 · enc_at_time=8_
- money +52g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 8 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→59 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=7, fodder_slime=7]
- **r2** hp 59→58 ap 1 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=7, fodder_slime=0]
- **r3** hp 58→57 ap 2 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=26 pick_loot] zone_01
_L3 · HP 59% · 86g · stash 5/10 · enc_at_time=9_
- money +21g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 9 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 29, took 1, healed 0_

- **r1** hp ?→56 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=7]
- **r2** hp 56→56 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 29 · KILL fodder_slime | end [fodder_slime=0]

### [seq=27 pick_loot] zone_01
_L3 · HP 58% · 98g · stash 5/10 · enc_at_time=10_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 10 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→54 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=7, fodder_slime=7]
- **r2** hp 54→53 ap 1 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=7]
- **r3** hp 53→52 ap 2 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=28 pick_loot] zone_01
_L3 · HP 54% · 112g · stash 5/10 · enc_at_time=11_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 11 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→51 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=7, fodder_slime=36]
- **r2** hp 51→49 ap 1 st=— | **SURVIVE** | took 2 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=7]
- **r3** hp 49→48 ap 2 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=29 pick_loot] zone_01
_L3 · HP 50% · 127g · stash 5/10 · enc_at_time=12_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 12 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→47 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=7, fodder_slime=36]
- **r2** hp 47→46 ap 1 st=— | **SURVIVE** | took 1 | end [fodder_slime=7, fodder_slime=7]
- **r3** hp 46→44 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=30 pick_loot] zone_01
_L4 · HP 39% · 142g · stash 5/10 · enc_at_time=13_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=31 use_consumable] zone_01
_L4 · HP 84% · 142g · stash 4/10 · enc_at_time=13_
- use minor_potion on mc_einherjar (HP 44→94/112)

### ENC 13 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→92 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 92→90 ap 1 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=32 pick_loot] zone_01
_L4 · HP 80% · 156g · stash 4/10 · enc_at_time=14_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 14 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→89 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=52, fodder_slime=19, fodder_slime=36]
- **r2** hp 89→86 ap 1 st=— | **SURVIVE** | took 3 · KILL fodder_slime | end [fodder_slime=19, fodder_slime=0, fodder_slime=2]
- **r3** hp 86→84 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=33 pick_loot] zone_01
_L4 · HP 75% · 185g · stash 4/10 · enc_at_time=15_
- money +29g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 15 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→84 ap 0 st=— | **SURVIVE** | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 84→82 ap 1 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r3** hp 82→80 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=34 pick_loot] zone_01
_L4 · HP 71% · 197g · stash 4/10 · enc_at_time=16_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 16 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→78 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 78→76 ap 1 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=35 pick_loot] zone_01
_L4 · HP 68% · 206g · stash 4/10 · enc_at_time=17_
- money +9g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 17 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 34, took 1, healed 0_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=2]
- **r2** hp 75→75 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 34 · KILL fodder_slime | end [fodder_slime=0]

### [seq=36 pick_loot] zone_01
_L4 · HP 67% · 211g · stash 4/10 · enc_at_time=18_
- money +5g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 18 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** | (no events) | end [fodder_slime=36]
- **r2** hp 75→75 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=37 pick_loot] zone_01
_L4 · HP 67% · 214g · stash 4/10 · enc_at_time=19_
- money +3g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 19 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 34, took 1, healed 0_

- **r1** hp ?→74 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=2]
- **r2** hp 74→74 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 34 · KILL fodder_slime | end [fodder_slime=0]

### [seq=38 pick_loot] zone_01
_L4 · HP 66% · 217g · stash 4/10 · enc_at_time=20_
- money +3g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 20 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→72 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=52, fodder_slime=19]
- **r2** hp 72→70 ap 1 st=— | **SURVIVE** | took 2 · KILL fodder_slime | end [fodder_slime=2, fodder_slime=19, fodder_slime=0]
- **r3** hp 70→68 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=39 pick_loot] zone_01
_L4 · HP 61% · 231g · stash 4/10 · enc_at_time=21_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 21 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 34, took 1, healed 0_

- **r1** hp ?→67 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=2]
- **r2** hp 67→67 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×1 | dealt 34 · KILL fodder_slime | end [fodder_slime=0]

### [seq=40 pick_loot] zone_01
_L4 · HP 60% · 232g · stash 4/10 · enc_at_time=22_
- money +1g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 22 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→65 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 65→65 ap 1 st=— | **SURVIVE** | (no events) | end [fodder_slime=2, fodder_slime=2]
- **r3** hp 65→63 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=41 pick_loot] zone_01
_L4 · HP 56% · 234g · stash 4/10 · enc_at_time=23_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 23 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→61 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=36, fodder_slime=19, fodder_slime=19]
- **r2** hp 61→59 ap 1 st=— | **SURVIVE** | took 2 · KILL fodder_slime | end [fodder_slime=2, fodder_slime=19, fodder_slime=0]
- **r3** hp 59→57 ap 2 st=— | **SURVIVE** | took 2 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=42 pick_loot] zone_01
_L4 · HP 51% · 236g · stash 4/10 · enc_at_time=24_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 24 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 4, healed 0_

- **r1** hp ?→55 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 55→54 ap 1 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=2, fodder_slime=0]
- **r3** hp 54→53 ap 2 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=43 pick_loot] zone_01
_L4 · HP 47% · 236g · stash 4/10 · enc_at_time=25_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=44 leave_zone]
_L4 · HP 47% · 236g · stash 4/10 · enc_at_time=25_
- leave zone_01: reason=voluntary_leave, enc_idx=5, overstay=20, cleared=True

### [seq=45 enter_town] (in shinto_town)
_L4 · HP 47% · 236g · stash 4/10 · enc_at_time=25_
- enter town shinto_town

### [seq=46 shop_buy] (in shinto_town)
_L4 · HP 47% · 206g · stash 5/10 · enc_at_time=25_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=47 shop_buy] (in shinto_town)
_L4 · HP 47% · 86g · stash 6/10 · enc_at_time=25_
- **BOUGHT** iron_guard @ 120g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=48 leave_town]
_L4 · HP 47% · 86g · stash 6/10 · enc_at_time=25_
- leave town shinto_town

### [seq=49 enter_zone] zone_01
_L4 · HP 47% · 86g · stash 6/10 · enc_at_time=25_
- enter zone_01 (already_cleared=True, via=zone_select)

### [seq=50 use_consumable] zone_01
_L4 · HP 92% · 86g · stash 5/10 · enc_at_time=25_
- use minor_potion on mc_einherjar (HP 53→103/112)

### [seq=51 equip] zone_01
_L4 · HP 60% · 86g · stash 4/10 · enc_at_time=25_
- equip iron_guard → mc_einherjar:ARMOR (displaced=None)

### ENC 25 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 0, took 2, healed 0_

- **r1** hp ?→102 ap 0 st=— | **SURVIVE** | took 1 | end [fodder_slime=2]
- **r2** hp 102→101 ap 1 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0]

### [seq=52 pick_loot] zone_01
_L4 · HP 59% · 86g · stash 4/10 · enc_at_time=26_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 26 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→99 ap 0 st=— | **SURVIVE** | took 2 | end [fodder_slime=2, fodder_slime=52, fodder_slime=19]
- **r2** hp 99→96 ap 1 st=— | **SURVIVE** | took 3 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=19, fodder_slime=0]
- **r3** hp 96→95 ap 2 st=— | **SURVIVE** | took 1 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=53 pick_loot] zone_01
_L4 · HP 55% · 86g · stash 4/10 · enc_at_time=27_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=54 leave_zone]
_L4 · HP 55% · 86g · stash 4/10 · enc_at_time=27_
- leave zone_01: reason=voluntary_leave, enc_idx=5, overstay=22, cleared=True

### [seq=55 enter_town] (in shinto_town)
_L4 · HP 55% · 86g · stash 4/10 · enc_at_time=27_
- enter town shinto_town

### [seq=56 shop_buy] (in shinto_town)
_L4 · HP 55% · 56g · stash 5/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=57 shop_buy] (in shinto_town)
_L4 · HP 55% · 26g · stash 6/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=58 leave_town]
_L4 · HP 55% · 26g · stash 6/10 · enc_at_time=27_
- leave town shinto_town

### [seq=59 use_consumable]
_L4 · HP 84% · 26g · stash 5/10 · enc_at_time=27_
- use minor_potion on mc_einherjar (HP 95→145/172)

### [seq=60 enter_zone] zone_02
_L4 · HP 84% · 26g · stash 5/10 · enc_at_time=27_
- enter zone_02 (already_cleared=False, via=zone_select)

### ENC 27 [zone_02 idx=0] vs slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→143 ap 0 st=— | **SURVIVE** | took 2 | end [slime=48, slime=48]
- **r2** hp 143→141 ap 1 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [slime=17, slime=17]
- **r3** hp 141→139 ap 2 st=— | **SURVIVE** | took 2 · KILL slime,slime | end [slime=0, slime=0]

### [seq=61 pick_loot] zone_02
_L4 · HP 81% · 92g · stash 6/10 · enc_at_time=28_
- money +66g, offered=['paladin_tonic'], **selected**=['paladin_tonic'], skipped=[], discarded_stash=[]

### ENC 28 [zone_02 idx=1] vs swime, slime → **VICTORY** (3 rounds)
_dealt 92, took 17, healed 0_

- **r1** hp ?→125 ap 0 st=— | **SURVIVE** | took 14 · enemy_status(Brace Strike DEF buff→slime) | end [swime=71, slime=67]
- **r2** hp 125→123 ap 1 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [swime=40, slime=37]
- **r3** hp 123→122 ap 2 st=— | **CHEAT(+2AP)** basic_attack→swime +cheat_extras×2 | dealt 92 · took 1 · KILL swime,slime | end [swime=0, slime=0]

### [seq=62 pick_loot] zone_02
_L5 · HP 63% · 172g · stash 6/10 · enc_at_time=29_
- money +80g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 29 [zone_02 idx=2] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 70, took 32, healed 0_

- **r1** hp ?→101 ap 0 st=— | **SURVIVE** | took 21 | end [mystic_slime=27, slime=62, slime=62]
- **r2** hp 101→90 ap 1 st=— | **SURVIVE** | took 11 · KILL mystic_slime · +status(?→self) | end [mystic_slime=0, slime=27, slime=27]
- **r3** hp 90→90 ap 2 st=— | **CHEAT(+2AP)** basic_attack→slime +cheat_extras×2 | dealt 70 · KILL slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=63 pick_loot] zone_02
_L5 · HP 46% · 289g · stash 6/10 · enc_at_time=30_
- money +117g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=64 use_consumable] zone_02
_L5 · HP 72% · 289g · stash 5/10 · enc_at_time=30_
- use minor_potion on mc_einherjar (HP 90→140/195)

### ENC 30 [zone_02 idx=3] vs chunky_slime, swime → **VICTORY** (5 rounds)
_dealt 56, took 19, healed 0_

- **r1** hp ?→132 ap 0 st=— | **SURVIVE** | took 8 | end [chunky_slime=110, swime=45]
- **r2** hp 132→130 ap 1 st=— | **SURVIVE** | took 2 | end [chunky_slime=90, swime=8]
- **r3** hp 130→122 ap 2 st=— | **SURVIVE** | took 8 · KILL swime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=70, swime=0]
- **r4** hp 122→121 ap 3 st=— | **SURVIVE** | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=50, swime=0]
- **r5** hp 121→121 ap 3 st=— | **CHEAT(+3AP)** brace_strike→chunky_slime +cheat_extras×3 | dealt 56 · KILL chunky_slime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=65 pick_loot] zone_02
_L5 · HP 62% · 327g · stash 5/10 · enc_at_time=31_
- money +38g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 31 [zone_02 idx=4] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 9, healed 0_

- **r1** hp ?→118 ap 0 st=— | **SURVIVE** | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=50, slime=62, slime=62]
- **r2** hp 118→114 ap 1 st=— | **SURVIVE** | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=13, slime=27, slime=27]
- **r3** hp 114→111 ap 2 st=— | **SURVIVE** | took 3 · KILL toxic_slime,slime,slime · +status(?→self) | end [toxic_slime=0, slime=0, slime=0]

### [seq=66 pick_loot] zone_02
_L6 · HP 51% · 424g · stash 5/10 · enc_at_time=32_
- money +97g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=67 leave_zone]
_L6 · HP 51% · 424g · stash 5/10 · enc_at_time=32_
- leave zone_02: reason=voluntary_leave, enc_idx=5, overstay=0, cleared=False

### [seq=68 enter_town] (in shinto_town)
_L6 · HP 51% · 424g · stash 5/10 · enc_at_time=32_
- enter town shinto_town

### [seq=69 shop_buy] (in shinto_town)
_L6 · HP 51% · 394g · stash 6/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=70 shop_buy] (in shinto_town)
_L6 · HP 51% · 364g · stash 7/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=71 shop_buy] (in shinto_town)
_L6 · HP 51% · 334g · stash 8/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=72 use_consumable] (in shinto_town)
_L6 · HP 74% · 334g · stash 7/10 · enc_at_time=32_
- use minor_potion on mc_einherjar (HP 111→161/218)

### [seq=73 use_consumable] (in shinto_town)
_L6 · HP 97% · 334g · stash 6/10 · enc_at_time=32_
- use minor_potion on mc_einherjar (HP 161→211/218)

### [seq=74 leave_town]
_L6 · HP 97% · 334g · stash 6/10 · enc_at_time=32_
- leave town shinto_town

### [seq=75 enter_zone] zone_02
_L6 · HP 97% · 334g · stash 6/10 · enc_at_time=32_
- enter zone_02 (already_cleared=False, via=zone_select)

### ENC 32 [zone_02 idx=5] vs swime, mystic_slime, chunky_slime → **VICTORY** (8 rounds)
_dealt 22, took 41, healed 0_

- **r1** hp ?→186 ap 0 st=— | **SURVIVE** | took 25 | end [swime=61, mystic_slime=37, chunky_slime=133]
- **r2** hp 186→183 ap 1 st=— | **SURVIVE** | took 3 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=20, mystic_slime=0, chunky_slime=111]
- **r3** hp 183→174 ap 2 st=— | **SURVIVE** | took 9 · KILL swime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=0, mystic_slime=0, chunky_slime=89]
- **r4** hp 174→173 ap 3 st=— | **SURVIVE** | took 1 | end [swime=0, mystic_slime=0, chunky_slime=67]
- **r5** hp 173→172 ap 3 st=— | **SURVIVE** | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=0, mystic_slime=0, chunky_slime=45]
- **r6** hp 172→171 ap 3 st=— | **SURVIVE** | took 1 | end [swime=0, mystic_slime=0, chunky_slime=23]
- **r7** hp 171→170 ap 3 st=— | **SURVIVE** | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=0, mystic_slime=0, chunky_slime=1]
- **r8** hp 170→170 ap 3 st=— | NORMAL basic_attack→chunky_slime | dealt 22 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=76 pick_loot] zone_02
_L6 · HP 78% · 438g · stash 6/10 · enc_at_time=33_
- money +104g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=77 leave_zone]
_L6 · HP 78% · 438g · stash 6/10 · enc_at_time=33_
- leave zone_02: reason=voluntary_leave, enc_idx=6, overstay=0, cleared=False

### [seq=78 enter_town] (in shinto_town)
_L6 · HP 78% · 438g · stash 6/10 · enc_at_time=33_
- enter town shinto_town

### [seq=79 shop_buy] (in shinto_town)
_L6 · HP 78% · 408g · stash 7/10 · enc_at_time=33_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=80 shop_buy] (in shinto_town)
_L6 · HP 78% · 378g · stash 8/10 · enc_at_time=33_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=81 shop_buy] (in shinto_town)
_L6 · HP 78% · 348g · stash 9/10 · enc_at_time=33_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=82 leave_town]
_L6 · HP 78% · 348g · stash 9/10 · enc_at_time=33_
- leave town shinto_town

### [seq=83 use_consumable]
_L6 · HP 100% · 348g · stash 8/10 · enc_at_time=33_
- use minor_potion on mc_einherjar (HP 170→218/218)

### [seq=84 enter_zone] zone_02
_L6 · HP 100% · 348g · stash 8/10 · enc_at_time=33_
- enter zone_02 (already_cleared=False, via=zone_select)

### ENC 33 [zone_02 idx=6] vs omega_slime → **VICTORY** (11 rounds)
_dealt 138, took 95, healed 71_

- **r1** hp ?→217 ap 0 st=— | **SURVIVE** | took 1 | end [omega_slime=272]
- **r2** hp 217→205 ap 1 st=— | **SURVIVE** | took 12 | end [omega_slime=249]
- **r3** hp 205→193 ap 2 st=— | **SURVIVE** | took 12 | end [omega_slime=227]
- **r4** hp 193→181 ap 3 st=— | **SURVIVE** | took 12 | end [omega_slime=205]
- **r5** hp 181→181 ap 3 st=— | **SURVIVE** | (no events) | end [omega_slime=207]
- **r6** hp 181→181 ap 3 st=— | **CHEAT(+3AP)** use_item(crusader_tonic)→self +cheat_extras×3 | dealt 41 · +status(?→self), +status(?→self), +status(Brace Strike DEF buff→self), -status(Brace Strike DEF buff→self) | end [omega_slime=169]
- **r7** hp 181→152 ap 0 st=— | **SURVIVE** | took 29 | end [omega_slime=137]
- **r8** hp 152→143 ap 1 st=— | **SURVIVE** | took 9 | end [omega_slime=105]
- **r9** hp 143→143 ap 2 st=— | **SURVIVE** | (no events) | end [omega_slime=109]
- **r10** hp 143→123 ap 3 st=— | **SURVIVE** | took 20 | end [omega_slime=78]
- **r11** hp 123→173 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 | dealt 97 · KILL omega_slime · +status(Brace Strike DEF buff→self) | end [omega_slime=0]

### [seq=85 pick_loot] zone_02
_L6 · HP 79% · 593g · stash 7/10 · enc_at_time=34_
- money +245g, offered=['potion', 'scroll_heavy_strike'], **selected**=['potion', 'scroll_heavy_strike'], skipped=[], discarded_stash=[]

### ENC 34 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 81, healed 0_

- **r1** hp ?→146 ap 0 st=— | **SURVIVE** | took 27 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=53, slime=76, slime=57]
- **r2** hp 146→119 ap 1 st=— | **SURVIVE** | took 27 · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=11, slime=37, slime=17]
- **r3** hp 119→92 ap 2 st=— | **SURVIVE** | took 27 · KILL slime,mystic_slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=86 pick_loot] zone_02
_L6 · HP 42% · 763g · stash 7/10 · enc_at_time=35_
- money +170g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 35 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (2 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→89 ap 0 st=— | **SURVIVE** | took 3 | end [toxic_slime=32, slime=38, slime=38]
- **r2** hp 89→86 ap 1 st=— | **SURVIVE** | took 3 · KILL toxic_slime,slime,slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=87 pick_loot] zone_02
_L6 · HP 39% · 873g · stash 7/10 · enc_at_time=36_
- money +110g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 36 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 28, healed 0_

- **r1** hp ?→73 ap 0 st=— | **SURVIVE** | took 13 · enemy_status(Brace Strike DEF buff→slime), +status(?→self) | end [mystic_slime=37, slime=57, slime=57]
- **r2** hp 73→60 ap 1 st=— | **SURVIVE** | took 13 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→slime), +status(?→self), -status(Hex Disrupt→self) | end [mystic_slime=0, slime=17, slime=17]
- **r3** hp 60→58 ap 2 st=— | **SURVIVE** | took 2 · KILL slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=88 pick_loot] zone_02
_L7 · HP 24% · 941g · stash 7/10 · enc_at_time=37_
- money +68g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=89 use_consumable] zone_02
_L7 · HP 45% · 941g · stash 6/10 · enc_at_time=37_
- use minor_potion on mc_einherjar (HP 58→108/241)

### [seq=90 use_consumable] zone_02
_L7 · HP 66% · 941g · stash 5/10 · enc_at_time=37_
- use minor_potion on mc_einherjar (HP 108→158/241)

### ENC 37 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 44, took 4, healed 0_

- **r1** hp ?→156 ap 0 st=— | **SURVIVE** | took 2 | end [slime=33, slime=71]
- **r2** hp 156→154 ap 1 st=— | **SURVIVE** | took 2 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [slime=0, slime=27]
- **r3** hp 154→154 ap 2 st=— | NORMAL basic_attack→slime | dealt 44 · KILL slime | end [slime=0, slime=0]

### [seq=91 pick_loot] zone_02
_L7 · HP 64% · 1000g · stash 5/10 · enc_at_time=38_
- money +59g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 38 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 45, took 4, healed 0_

- **r1** hp ?→152 ap 0 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=52, slime=33]
- **r2** hp 152→150 ap 1 st=— | **SURVIVE** | took 2 · KILL slime | end [slime=7, slime=0]
- **r3** hp 150→150 ap 2 st=— | NORMAL basic_attack→slime | dealt 45 · KILL slime | end [slime=0, slime=0]

### [seq=92 pick_loot] zone_02
_L7 · HP 62% · 1040g · stash 5/10 · enc_at_time=39_
- money +40g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 39 [zone_02 idx=7] vs toxic_slime, slime, slime, bandit_slime → **VICTORY** (2 rounds)
_dealt 94, took 6, healed 0_

- **r1** hp ?→146 ap 0 st=— | NORMAL basic_attack→bandit_slime +bonus×1 | dealt 94 · took 3 · KILL bandit_slime · +status(?→self) | end [toxic_slime=27, slime=33, slime=7, bandit_slime=0]
- **r2** hp 146→143 ap 0 st=— | **SURVIVE** | took 3 · KILL slime,toxic_slime,slime · +status(?→self) | end [toxic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=93 pick_loot] zone_02
_L7 · HP 59% · 1158g · stash 5/10 · enc_at_time=40_
- money +118g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 40 [zone_02 idx=7] vs swime, slime → **VICTORY** (3 rounds)
_dealt 91, took 12, healed 0_

- **r1** hp ?→137 ap 0 st=— | **SURVIVE** | took 6 · enemy_status(Brace Strike DEF buff→slime) | end [swime=56, slime=52]
- **r2** hp 137→131 ap 1 st=— | **SURVIVE** | took 6 · enemy_status(Brace Strike DEF buff→slime) | end [swime=10, slime=7]
- **r3** hp 131→131 ap 2 st=— | **CHEAT(+2AP)** basic_attack→swime +cheat_extras×2 | dealt 91 · KILL swime,slime | end [swime=0, slime=0]

### [seq=94 pick_loot] zone_02
_L7 · HP 54% · 1216g · stash 5/10 · enc_at_time=41_
- money +58g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 41 [zone_02 idx=7] vs swime, slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→129 ap 0 st=— | **SURVIVE** | took 2 | end [swime=35, slime=71]
- **r2** hp 129→126 ap 1 st=— | **SURVIVE** | took 3 · KILL swime | end [swime=0, slime=27]
- **r3** hp 126→125 ap 2 st=— | **SURVIVE** | took 1 · KILL slime | end [swime=0, slime=0]

### [seq=95 pick_loot] zone_02
_L7 · HP 52% · 1268g · stash 5/10 · enc_at_time=42_
- money +52g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 42 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→123 ap 0 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=71, slime=52]
- **r2** hp 123→121 ap 1 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=27, slime=7]
- **r3** hp 121→119 ap 2 st=— | **SURVIVE** | took 2 · KILL slime,slime | end [slime=0, slime=0]

### [seq=96 pick_loot] zone_02
_L8 · HP 45% · 1323g · stash 5/10 · enc_at_time=43_
- money +55g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 43 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 5, healed 0_

- **r1** hp ?→117 ap 0 st=— | **SURVIVE** | took 2 | end [slime=66, slime=28]
- **r2** hp 117→115 ap 1 st=— | **SURVIVE** | took 2 · KILL slime | end [slime=17, slime=0]
- **r3** hp 115→114 ap 2 st=— | **SURVIVE** | took 1 · KILL slime | end [slime=0, slime=0]

### [seq=97 pick_loot] zone_02
_L8 · HP 43% · 1379g · stash 5/10 · enc_at_time=44_
- money +56g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 44 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→112 ap 0 st=— | **SURVIVE** | took 2 | end [slime=66, slime=66]
- **r2** hp 112→110 ap 1 st=— | **SURVIVE** | took 2 | end [slime=17, slime=17]
- **r3** hp 110→108 ap 2 st=— | **SURVIVE** | took 2 · KILL slime,slime | end [slime=0, slime=0]

### [seq=98 pick_loot] zone_02
_L8 · HP 41% · 1421g · stash 5/10 · enc_at_time=45_
- money +42g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=99 leave_zone]
_L8 · HP 41% · 1421g · stash 5/10 · enc_at_time=45_
- leave zone_02: reason=voluntary_leave, enc_idx=7, overstay=11, cleared=True

### [seq=100 enter_town] (in shinto_town)
_L8 · HP 41% · 1421g · stash 5/10 · enc_at_time=45_
- enter town shinto_town

### [seq=101 shop_buy] (in shinto_town)
_L8 · HP 41% · 1391g · stash 6/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=102 shop_buy] (in shinto_town)
_L8 · HP 41% · 1361g · stash 7/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=103 shop_buy] (in shinto_town)
_L8 · HP 41% · 1331g · stash 8/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=104 shop_buy] (in shinto_town)
_L8 · HP 41% · 1301g · stash 9/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=105 use_consumable] (in shinto_town)
_L8 · HP 60% · 1301g · stash 8/10 · enc_at_time=45_
- use minor_potion on mc_einherjar (HP 108→158/264)

### [seq=106 use_consumable] (in shinto_town)
_L8 · HP 79% · 1301g · stash 7/10 · enc_at_time=45_
- use minor_potion on mc_einherjar (HP 158→208/264)

### [seq=107 use_consumable] (in shinto_town)
_L8 · HP 98% · 1301g · stash 6/10 · enc_at_time=45_
- use minor_potion on mc_einherjar (HP 208→258/264)

### [seq=108 use_consumable] (in shinto_town)
_L8 · HP 100% · 1301g · stash 5/10 · enc_at_time=45_
- use minor_potion on mc_einherjar (HP 258→264/264)

### [seq=109 shop_buy] (in shinto_town)
_L8 · HP 100% · 1271g · stash 6/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=110 shop_buy] (in shinto_town)
_L8 · HP 100% · 1241g · stash 7/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=111 shop_buy] (in shinto_town)
_L8 · HP 100% · 1211g · stash 8/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=112 leave_town]
_L8 · HP 100% · 1211g · stash 8/10 · enc_at_time=45_
- leave town shinto_town

### [seq=113 enter_zone] zone_02
_L8 · HP 100% · 1211g · stash 8/10 · enc_at_time=45_
- enter zone_02 (already_cleared=True, via=zone_select)

### ENC 45 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 6, healed 0_

- **r1** hp ?→262 ap 0 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=66, slime=66]
- **r2** hp 262→260 ap 1 st=— | **SURVIVE** | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [slime=17, slime=17]
- **r3** hp 260→258 ap 2 st=— | **SURVIVE** | took 2 · KILL slime,slime | end [slime=0, slime=0]

### [seq=114 pick_loot] zone_02
_L8 · HP 98% · 1242g · stash 8/10 · enc_at_time=46_
- money +31g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 46 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 145, took 49, healed 0_

- **r1** hp ?→256 ap 0 st=— | **SURVIVE** | took 2 · +status(Taunted→self) | end [swime=30, mystic_slime=27, chunky_slime=155]
- **r2** hp 256→209 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×1 | dealt 113 · took 47 · KILL mystic_slime,swime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=10]
- **r3** hp 209→209 ap 0 st=— | NORMAL basic_attack→chunky_slime +bonus×1 | dealt 32 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=115 pick_loot] zone_02
_L8 · HP 79% · 1279g · stash 8/10 · enc_at_time=47_
- money +37g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 47 [zone_02 idx=7] vs mystic_slime, slime, slime, bandit_slime → **VICTORY** (2 rounds)
_dealt 206, took 27, healed 0_

- **r1** hp ?→183 ap 0 st=— | NORMAL basic_attack→bandit_slime +bonus×1 | dealt 106 · took 26 · KILL bandit_slime,mystic_slime · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=0, slime=28, slime=66, bandit_slime=0]
- **r2** hp 183→182 ap 0 st=— | NORMAL basic_attack→slime +bonus×1 | dealt 100 · took 1 · KILL slime,slime | end [mystic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=116 pick_loot] zone_02
_L8 · HP 69% · 1353g · stash 8/10 · enc_at_time=48_
- money +74g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 48 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 103, took 2, healed 0_

- **r1** hp ?→180 ap 0 st=— | **SURVIVE** | took 2 | end [swime=30, slime=28]
- **r2** hp 180→180 ap 1 st=— | NORMAL basic_attack→swime +bonus×1 | dealt 103 · KILL swime,slime | end [swime=0, slime=0]

### [seq=117 pick_loot] zone_02
_L8 · HP 68% · 1365g · stash 8/10 · enc_at_time=49_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 49 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (2 rounds)
_dealt 120, took 8, healed 0_

- **r1** hp ?→179 ap 0 st=— | **SURVIVE** | took 1 · +status(Taunted→self) | end [chunky_slime=130, swime=51]
- **r2** hp 179→172 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×1 | dealt 120 · took 7 · KILL swime,chunky_slime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=118 pick_loot] zone_02
_L8 · HP 65% · 1390g · stash 8/10 · enc_at_time=50_
- money +25g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 50 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 170, took 70, healed 0_

- **r1** hp ?→154 ap 0 st=— | **SURVIVE** | took 18 · +status(?→self), +status(Taunted→self) | end [swime=72, mystic_slime=43, chunky_slime=130]
- **r2** hp 154→102 ap 1 st=Taunted | **CHEAT(+1AP)** thrust→chunky_slime +cheat_extras×1 +bonus×1 | dealt 120 · took 52 · KILL mystic_slime,chunky_slime · +status(Brace Strike DEF buff→self), -status(Hex Disrupt→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=22, mystic_slime=0, chunky_slime=0]
- **r3** hp 102→102 ap 0 st=— | NORMAL basic_attack→swime | dealt 50 · KILL swime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=119 pick_loot] zone_02
_L8 · HP 39% · 1415g · stash 8/10 · enc_at_time=51_
- money +25g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 51 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (2 rounds)
_dealt 154, took 3, healed 0_

- **r1** hp ?→99 ap 0 st=— | **SURVIVE** | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=27, slime=28, slime=47]
- **r2** hp 99→99 ap 1 st=— | **CHEAT(+1AP)** basic_attack→mystic_slime +cheat_extras×1 +bonus×1 | dealt 154 · KILL mystic_slime,slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=120 pick_loot] zone_02
_L8 · HP 38% · 1431g · stash 8/10 · enc_at_time=52_
- money +16g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 52 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 101, took 2, healed 0_

- **r1** hp ?→97 ap 0 st=— | **SURVIVE** | took 2 | end [swime=51, slime=47]
- **r2** hp 97→97 ap 1 st=— | NORMAL basic_attack→swime +bonus×1 | dealt 101 · KILL swime,slime | end [swime=0, slime=0]

### [seq=121 pick_loot] zone_02
_L8 · HP 37% · 1438g · stash 8/10 · enc_at_time=53_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 53 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 195, took 29, healed 0_

- **r1** hp ?→83 ap 0 st=— | **SURVIVE** | took 14 · +status(Taunted→self), +status(?→self) | end [swime=72, mystic_slime=12, chunky_slime=155]
- **r2** hp 83→68 ap 1 st=Taunted | **CHEAT(+1AP)** thrust→chunky_slime +cheat_extras×1 +bonus×1 | dealt 113 · took 15 · KILL mystic_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Hex Disrupt→self), -status(Brace Strike DEF buff→self) | end [swime=22, mystic_slime=0, chunky_slime=10]
- **r3** hp 68→68 ap 0 st=— | NORMAL basic_attack→swime +bonus×1 | dealt 82 · KILL swime,chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=122 pick_loot] zone_02
_L8 · HP 26% · 1442g · stash 8/10 · enc_at_time=54_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=123 leave_zone]
_L8 · HP 26% · 1442g · stash 8/10 · enc_at_time=54_
- leave zone_02: reason=voluntary_leave, enc_idx=7, overstay=20, cleared=True

### [seq=124 enter_town] (in shinto_town)
_L8 · HP 26% · 1442g · stash 8/10 · enc_at_time=54_
- enter town shinto_town

### [seq=125 shop_buy] (in shinto_town)
_L8 · HP 26% · 1412g · stash 9/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=126 shop_buy] (in shinto_town)
_L8 · HP 26% · 1382g · stash 10/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=127 use_consumable] (in shinto_town)
_L8 · HP 45% · 1382g · stash 9/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 68→118/264)

### [seq=128 use_consumable] (in shinto_town)
_L8 · HP 64% · 1382g · stash 8/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 118→168/264)

### [seq=129 use_consumable] (in shinto_town)
_L8 · HP 83% · 1382g · stash 7/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 168→218/264)

### [seq=130 use_consumable] (in shinto_town)
_L8 · HP 100% · 1382g · stash 6/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 218→264/264)

### [seq=131 shop_buy] (in shinto_town)
_L8 · HP 100% · 1352g · stash 7/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=132 shop_buy] (in shinto_town)
_L8 · HP 100% · 1322g · stash 8/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=133 shop_buy] (in shinto_town)
_L8 · HP 100% · 1292g · stash 9/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=134 leave_town]
_L8 · HP 100% · 1292g · stash 9/10 · enc_at_time=54_
- leave town shinto_town

### [seq=135 enter_zone] zone_03
_L8 · HP 100% · 1292g · stash 9/10 · enc_at_time=54_
- enter zone_03 (already_cleared=False, via=zone_select)

### ENC 54 [zone_03 idx=0] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 236, took 66, healed 0_

- **r1** hp ?→250 ap 0 st=— | **SURVIVE** | took 14 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=271, slime=66, slime=66]
- **r2** hp 250→236 ap 1 st=— | **SURVIVE** | took 14 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=250, slime=17, slime=17]
- **r3** hp 236→222 ap 2 st=— | **SURVIVE** | took 14 · KILL slime,slime | end [brute_oni=229, slime=0, slime=0]
- **r4** hp 222→198 ap 3 st=— | **CHEAT(+3AP)** brace_strike→brute_oni +cheat_extras×3 +bonus×1 | dealt 162 · took 24 · +status(Brace Strike DEF buff→self), -status(Brace Strike DEF buff→self) | end [brute_oni=46, slime=0, slime=0]
- **r5** hp 198→198 ap 0 st=— | NORMAL thrust→brute_oni +bonus×1 | dealt 74 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=136 pick_loot] zone_03
_L8 · HP 75% · 1492g · stash 9/10 · enc_at_time=55_
- money +200g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 55 [zone_03 idx=1] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 0, took 102, healed 0_

- **r1** hp ?→164 ap 0 st=— | **SURVIVE** | took 34 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=82, slime=86, slime=66]
- **r2** hp 164→130 ap 1 st=— | **SURVIVE** | took 34 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=31, slime=39, slime=17]
- **r3** hp 130→96 ap 2 st=— | **SURVIVE** | took 34 · KILL caster_kitsune,slime,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=137 pick_loot] zone_03
_L9 · HP 33% · 1583g · stash 9/10 · enc_at_time=56_
- money +91g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=138 use_consumable] zone_03
_L9 · HP 51% · 1583g · stash 8/10 · enc_at_time=56_
- use minor_potion on mc_einherjar (HP 96→146/287)

### [seq=139 use_consumable] zone_03
_L9 · HP 68% · 1583g · stash 7/10 · enc_at_time=56_
- use minor_potion on mc_einherjar (HP 146→196/287)

### [seq=140 use_consumable] zone_03
_L9 · HP 86% · 1583g · stash 6/10 · enc_at_time=56_
- use minor_potion on mc_einherjar (HP 196→246/287)

### ENC 56 [zone_03 idx=2] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 160, took 28, healed 0_

- **r1** hp ?→237 ap 0 st=— | **SURVIVE** | took 9 | end [speeder_tengu=65, swime=109, swime=88]
- **r2** hp 237→218 ap 1 st=— | **SURVIVE** | took 19 · KILL speeder_tengu | end [speeder_tengu=0, swime=56, swime=34]
- **r3** hp 218→218 ap 2 st=— | **CHEAT(+2AP)** basic_attack→swime +cheat_extras×2 | dealt 160 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=141 pick_loot] zone_03
_L9 · HP 76% · 1737g · stash 7/10 · enc_at_time=57_
- money +154g, offered=['battlemage_tonic'], **selected**=['battlemage_tonic'], skipped=[], discarded_stash=[]

### [seq=142 recruit_accept] zone_03
_L9 · HP 76% · 1737g · stash 7/10 · enc_at_time=57_
- recruit_accept: Einherjar Recruit (einherjar L7) id=recruit_einherjar_9051

### [seq=143 use_teach_scroll] zone_03
_L9 · HP 76% · 1737g · stash 6/10 · enc_at_time=57_
- teach heavy_strike from scroll_heavy_strike to mc_einherjar

### [seq=144 leave_zone]
_L9 · HP 76% · 1737g · stash 6/10 · enc_at_time=57_
- leave zone_03: reason=voluntary_leave, enc_idx=3, overstay=0, cleared=False

### [seq=145 enter_town] (in shinto_town)
_L9 · HP 76% · 1737g · stash 6/10 · enc_at_time=57_
- enter town shinto_town

### [seq=146 shop_buy] (in shinto_town)
_L9 · HP 76% · 1637g · stash 7/10 · enc_at_time=57_
- **BOUGHT** iron_blade @ 100g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=147 shop_buy] (in shinto_town)
_L9 · HP 76% · 1517g · stash 8/10 · enc_at_time=57_
- **BOUGHT** iron_guard @ 120g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=148 shop_buy] (in shinto_town)
_L9 · HP 76% · 1487g · stash 9/10 · enc_at_time=57_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=149 shop_buy] (in shinto_town)
_L9 · HP 76% · 1457g · stash 10/10 · enc_at_time=57_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=150 equip] (in shinto_town)
_L9 · HP 76% · 1457g · stash 9/10 · enc_at_time=57_
- equip iron_guard → recruit_einherjar_9051:ARMOR (displaced=None)

### [seq=151 shop_sell] (in shinto_town)
_L9 · HP 76% · 1472g · stash 8/10 · enc_at_time=57_
- **SOLD** iron_blade @ Noneg
- offered: []

### [seq=152 use_consumable] (in shinto_town)
_L9 · HP 93% · 1472g · stash 7/10 · enc_at_time=57_
- use minor_potion on mc_einherjar (HP 218→268/287)

### [seq=153 use_consumable] (in shinto_town)
_L9 · HP 93% · 1472g · stash 6/10 · enc_at_time=57_
- use minor_potion on recruit_einherjar_9051 (HP 158→208/241)

### [seq=154 use_consumable] (in shinto_town)
_L9 · HP 93% · 1472g · stash 5/10 · enc_at_time=57_
- use minor_potion on recruit_einherjar_9051 (HP 208→241/241)

### [seq=155 leave_town]
_L9 · HP 93% · 1472g · stash 5/10 · enc_at_time=57_
- leave town shinto_town

### [seq=156 enter_zone] zone_03
_L9 · HP 93% · 1472g · stash 5/10 · enc_at_time=57_
- enter zone_03 (already_cleared=False, via=zone_select)

### ENC 57 [zone_03 idx=3] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 341, took 54, healed 0_

- **r1** hp ?→268 ap 0 st=— | **SURVIVE** | enemy_status(Rally buff→support_tanuki) | end [support_tanuki=180, brute_oni=292]
- **r2** hp 268→258 ap 1 st=— | **SURVIVE** | took 10 | end [support_tanuki=126, brute_oni=266]
- **r3** hp 258→258 ap 2 st=— | **SURVIVE** | (no events) | end [support_tanuki=82, brute_oni=250]
- **r4** hp 258→258 ap 3 st=— | **CHEAT(+3AP)** heavy_strike→support_tanuki +cheat_extras×3 +bonus×1 | dealt 241 · KILL support_tanuki · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→recruit_einherjar), -status(Brace Strike DEF buff→self) | end [support_tanuki=0, brute_oni=16]
- **r5** hp 258→258 ap 0 st=— | NORMAL basic_attack→brute_oni +bonus×1 | dealt 26 · KILL brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=157 pick_loot] zone_03
_L9 · HP 90% · 1598g · stash 5/10 · enc_at_time=58_
- money +126g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 58 [zone_03 idx=4] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 50, took 68, healed 0_

- **r1** hp ?→257 ap 0 st=— | **SURVIVE** | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=87, speeder_tengu=96, slime=119]
- **r2** hp 257→257 ap 1 st=— | **SURVIVE** | enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=41, speeder_tengu=50, slime=79]
- **r3** hp 257→257 ap 2 st=— | **SURVIVE** | KILL caster_kitsune · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=0, speeder_tengu=4, slime=39]
- **r4** hp 257→257 ap 3 st=— | NORMAL basic_attack→speeder_tengu | retal 50 · KILL speeder_tengu,slime | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=158 pick_loot] zone_03
_L10 · HP 83% · 1846g · stash 5/10 · enc_at_time=59_
- money +248g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=159 leave_zone]
_L10 · HP 83% · 1846g · stash 5/10 · enc_at_time=59_
- leave zone_03: reason=voluntary_leave, enc_idx=5, overstay=0, cleared=False

### [seq=160 enter_town] (in shinto_town)
_L10 · HP 83% · 1846g · stash 5/10 · enc_at_time=59_
- enter town shinto_town

### [seq=161 shop_buy] (in shinto_town)
_L10 · HP 83% · 1816g · stash 6/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=162 shop_buy] (in shinto_town)
_L10 · HP 83% · 1786g · stash 7/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=163 shop_buy] (in shinto_town)
_L10 · HP 83% · 1756g · stash 8/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=164 shop_buy] (in shinto_town)
_L10 · HP 83% · 1726g · stash 9/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=165 use_consumable] (in shinto_town)
_L10 · HP 99% · 1726g · stash 8/10 · enc_at_time=59_
- use minor_potion on mc_einherjar (HP 257→307/310)

### [seq=166 use_consumable] (in shinto_town)
_L10 · HP 99% · 1726g · stash 7/10 · enc_at_time=59_
- use minor_potion on recruit_einherjar_9051 (HP 130→180/241)

### [seq=167 use_consumable] (in shinto_town)
_L10 · HP 99% · 1726g · stash 6/10 · enc_at_time=59_
- use minor_potion on recruit_einherjar_9051 (HP 180→230/241)

### [seq=168 shop_buy] (in shinto_town)
_L10 · HP 99% · 1696g · stash 7/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=169 shop_buy] (in shinto_town)
_L10 · HP 99% · 1666g · stash 8/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=170 shop_buy] (in shinto_town)
_L10 · HP 99% · 1636g · stash 9/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=171 leave_town]
_L10 · HP 99% · 1636g · stash 9/10 · enc_at_time=59_
- leave town shinto_town

### [seq=172 enter_zone] zone_02
_L10 · HP 99% · 1636g · stash 9/10 · enc_at_time=59_
- enter zone_02 (already_cleared=True, via=zone_select)

### [seq=173 leave_zone]
_L10 · HP 99% · 1636g · stash 9/10 · enc_at_time=59_
- leave zone_02: reason=travel_next_zone, enc_idx=7, overstay=20, cleared=True → next=zone_03

### [seq=174 enter_zone] zone_03
_L10 · HP 99% · 1636g · stash 9/10 · enc_at_time=59_
- enter zone_03 (already_cleared=None, via=travel_next_zone)

### ENC 59 [zone_03 idx=5] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (5 rounds)
_dealt 428, took 83, healed 57_

- **r1** hp ?→281 ap 0 st=— | **SURVIVE** | took 26 | end [brute_oni=292, support_tanuki=173, slime=91, slime=91]
- **r2** hp 281→272 ap 1 st=— | **SURVIVE** | took 9 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=261, support_tanuki=116, slime=34, slime=49]
- **r3** hp 272→271 ap 2 st=— | **SURVIVE** | took 1 · KILL slime,slime | end [brute_oni=276, support_tanuki=116, slime=0, slime=0]
- **r4** hp 271→271 ap 3 st=— | **CHEAT(+3AP)** heavy_strike→support_tanuki +cheat_extras×3 +bonus×1 | dealt 266 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→recruit_einherjar), enemy_status(Rally buff→support_tanuki), -status(Brace Strike DEF buff→self) | end [brute_oni=23, support_tanuki=13, slime=0, slime=0]
- **r5** hp 271→271 ap 0 st=— | NORMAL basic_attack→brute_oni +bonus×1 | dealt 88 · KILL brute_oni,support_tanuki | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=175 pick_loot] zone_03
_L10 · HP 87% · 1906g · stash 9/10 · enc_at_time=60_
- money +270g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=176 use_consumable] zone_03
_L10 · HP 87% · 1906g · stash 8/10 · enc_at_time=60_
- use minor_potion on recruit_einherjar_9051 (HP 183→233/241)

### ENC 60 [zone_03 idx=6] vs kodama_elder → **VICTORY** (5 rounds)
_dealt 523, took 33, healed 20_

- **r1** hp ?→270 ap 0 st=— | NORMAL use_item(battlemage_tonic)→self | took 1 · +status(?→self) | end [kodama_elder=327]
- **r2** hp 270→270 ap 0 st=— | **SURVIVE** | (no events) | end [kodama_elder=290]
- **r3** hp 270→269 ap 1 st=— | **SURVIVE** | took 1 | end [kodama_elder=240]
- **r4** hp 269→269 ap 2 st=— | **SURVIVE** | enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [kodama_elder=104, kodama=87, kodama=87]
- **r5** hp 269→269 ap 3 st=— | **CHEAT(+3AP)** heavy_strike→kodama_elder +cheat_extras×3 +bonus×1 | dealt 373 · KILL kodama,kodama,kodama_elder · +status(Brace Strike DEF buff→self) | end [kodama_elder=0, kodama=0, kodama=0]

### [seq=177 pick_loot] zone_03
_L10 · HP 87% · 2130g · stash 9/10 · enc_at_time=61_
- money +224g, offered=['potion', 'scroll_brace_strike'], **selected**=['potion', 'scroll_brace_strike'], skipped=[], discarded_stash=[]
