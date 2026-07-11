# Run Trace: sim_einherjar_seed45_zone4 (einherjar 'sim_mc' L17)

**Final state**: L17 · HP 18/358 · 7039g · zones cleared: ['zone_01', 'zone_02', 'zone_03', 'zone_04']
**Encounters**: 96
**Macro events**: 508

## Legend

- Round line: `rN hp H→H' ap A st=<statuses> | DECISION primary→target +extras×N +bonus×N | dealt X · took Y · retal Z · KILL foo | end [enemy hp]`
- `hp H→H'` is pre→post-round MC HP. `ap A` is PRE-decision AP (what the policy saw). `st=` is active statuses at round start (taunted, marked, etc.) — inferred from events.
- SURVIVE banks +1 AP (capped at 3). CHEAT(+NAP) spends N AP. NORMAL is a regular turn, no AP change.
- Macro event header: `[seq=N event_type zone]` with L#/HP%/gold context.

---

### [seq=0 run_start]
_L1 · HP 100% · 0g · stash 0/10 · enc_at_time=0_
- start: sim_mc (einherjar)

### [seq=1 enter_zone] zone_01
_L1 · HP 100% · 0g · stash 0/10 · enc_at_time=0_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 0 [zone_01 idx=0] vs fodder_slime → **VICTORY** (4 rounds)
_dealt 18, took 3, healed 0_

- **r1** hp ?→64 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=30]
- **r2** hp 64→63 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=24]
- **r3** hp 63→62 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=18]
- **r4** hp 62→62 ap 3 st=— | **CHEAT(+2AP)** basic_attack→fodder_slime +cheat_extras×2 +bonus×4 | dealt 18 · KILL fodder_slime | end [fodder_slime=0]

### [seq=2 pick_loot] zone_01
_L1 · HP 95% · 10g · stash 0/10 · enc_at_time=1_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 1 [zone_01 idx=1] vs fodder_slime, fodder_slime → **VICTORY** (6 rounds)
_dealt 18, took 9, healed 0_

- **r1** hp ?→60 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r2** hp 60→58 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=24, fodder_slime=24]
- **r3** hp 58→57 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=24, fodder_slime=18]
- **r4** hp 57→55 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=18, fodder_slime=12]
- **r5** hp 55→53 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=6]
- **r6** hp 53→53 ap 3 st=— | **CHEAT(+2AP)** basic_attack→fodder_slime +cheat_extras×2 +bonus×4 | dealt 18 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=3 pick_loot] zone_01
_L1 · HP 82% · 32g · stash 0/10 · enc_at_time=2_
- money +22g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 2 [zone_01 idx=2] vs fodder_slime, fodder_slime → **VICTORY** (5 rounds)
_dealt 24, took 8, healed 0_

- **r1** hp ?→51 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r2** hp 51→49 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=24, fodder_slime=24]
- **r3** hp 49→47 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=18, fodder_slime=18]
- **r4** hp 47→45 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r5** hp 45→45 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 24 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=4 pick_loot] zone_01
_L2 · HP 56% · 56g · stash 0/10 · enc_at_time=3_
- money +24g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=5 leave_zone]
_L2 · HP 56% · 56g · stash 0/10 · enc_at_time=3_
- leave zone_01: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=6 enter_town] (in shinto_town)
_L2 · HP 56% · 56g · stash 0/10 · enc_at_time=3_
- enter town shinto_town

### [seq=7 shop_buy] (in shinto_town)
_L2 · HP 56% · 26g · stash 1/10 · enc_at_time=3_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=8 leave_town]
_L2 · HP 56% · 26g · stash 1/10 · enc_at_time=3_
- leave town shinto_town

### [seq=9 enter_zone] zone_01
_L2 · HP 56% · 26g · stash 1/10 · enc_at_time=3_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 3 [zone_01 idx=3] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (8 rounds)
_dealt 32, took 18, healed 40_

- **r1** hp ?→43 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=44, fodder_slime=52, fodder_slime=44]
- **r2** hp 43→41 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=36, fodder_slime=52, fodder_slime=36]
- **r3** hp 41→79 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 16 · took 2 | end [fodder_slime=36, fodder_slime=28, fodder_slime=36]
- **r4** hp 79→76 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=28, fodder_slime=20, fodder_slime=28]
- **r5** hp 76→73 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=20, fodder_slime=12, fodder_slime=20]
- **r6** hp 73→70 ap 2 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=12, fodder_slime=4, fodder_slime=12]
- **r7** hp 70→67 ap 3 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime | end [fodder_slime=4, fodder_slime=0, fodder_slime=4]
- **r8** hp 67→67 ap 3 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×4 | dealt 16 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=10 pick_loot] zone_01
_L2 · HP 83% · 96g · stash 0/10 · enc_at_time=4_
- money +70g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=11 leave_zone]
_L2 · HP 83% · 96g · stash 0/10 · enc_at_time=4_
- leave zone_01: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=12 enter_town] (in shinto_town)
_L2 · HP 83% · 96g · stash 0/10 · enc_at_time=4_
- enter town shinto_town

### [seq=13 shop_buy] (in shinto_town)
_L2 · HP 83% · 66g · stash 1/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=14 shop_buy] (in shinto_town)
_L2 · HP 83% · 36g · stash 2/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=15 shop_buy] (in shinto_town)
_L2 · HP 83% · 6g · stash 3/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=16 leave_town]
_L2 · HP 83% · 6g · stash 3/10 · enc_at_time=4_
- leave town shinto_town

### [seq=17 enter_zone] zone_01
_L2 · HP 83% · 6g · stash 3/10 · enc_at_time=4_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 4 [zone_01 idx=4] vs alpha_slime → **VICTORY** (9 rounds)
_dealt 28, took 76, healed 50_

- **r1** hp ?→59 ap 0 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=83]
- **r2** hp 59→57 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=76]
- **r3** hp 57→49 ap 2 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=69]
- **r4** hp 49→47 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=62]
- **r5** hp 47→39 ap 3 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=55]
- **r6** hp 39→73 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 14 · took 16 · retal 7 | end [alpha_slime=27]
- **r7** hp 73→65 ap 0 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=20]
- **r8** hp 65→57 ap 1 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=13]
- **r9** hp 57→41 ap 2 st=— | **CHEAT(+1AP)** basic_attack→alpha_slime +cheat_extras×1 +bonus×4 | took 16 · retal 7 · KILL alpha_slime | end [alpha_slime=0]

### [seq=18 pick_loot] zone_01
_L2 · HP 51% · 83g · stash 6/10 · enc_at_time=5_
- money +77g, offered=['minor_potion', 'iron_blade', 'cast_searing_edge', 'cast_heavy_strike'], **selected**=['minor_potion', 'iron_blade', 'cast_searing_edge', 'cast_heavy_strike'], skipped=[], discarded_stash=[]

### [seq=19 use_consumable] zone_01
_L2 · HP 100% · 83g · stash 5/10 · enc_at_time=5_
- use minor_potion on mc_einherjar (HP 41→81/81)

### [seq=20 leave_zone]
_L2 · HP 100% · 83g · stash 5/10 · enc_at_time=5_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=True

### [seq=21 enter_town] (in shinto_town)
_L2 · HP 100% · 83g · stash 5/10 · enc_at_time=5_
- enter town shinto_town

### [seq=22 shop_buy] (in shinto_town)
_L2 · HP 100% · 53g · stash 6/10 · enc_at_time=5_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=23 shop_buy] (in shinto_town)
_L2 · HP 100% · 23g · stash 7/10 · enc_at_time=5_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=24 equip] (in shinto_town)
_L2 · HP 100% · 23g · stash 6/10 · enc_at_time=5_
- equip iron_blade → mc_einherjar:WEAPON (displaced=None)

### [seq=25 leave_town]
_L2 · HP 100% · 23g · stash 6/10 · enc_at_time=5_
- leave town shinto_town

### [seq=26 enter_zone] zone_01
_L2 · HP 100% · 23g · stash 6/10 · enc_at_time=5_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 5 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 71, took 4, healed 0_

- **r1** hp ?→79 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=29, fodder_slime=12, fodder_slime=36]
- **r2** hp 79→77 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL fodder_slime | end [fodder_slime=6, fodder_slime=0, fodder_slime=36]
- **r3** hp 77→77 ap 2 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×4 | dealt 71 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=27 pick_loot] zone_01
_L3 · HP 80% · 78g · stash 6/10 · enc_at_time=6_
- money +55g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 6 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 56, took 2, healed 0_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=7, fodder_slime=7]
- **r2** hp 75→75 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 56 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=28 pick_loot] zone_01
_L3 · HP 78% · 101g · stash 6/10 · enc_at_time=7_
- money +23g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 7 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 56, took 2, healed 0_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 75→73 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=7, fodder_slime=7]
- **r3** hp 73→73 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 56 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=29 pick_loot] zone_01
_L3 · HP 76% · 125g · stash 6/10 · enc_at_time=8_
- money +24g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 8 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 55, took 4, healed 0_

- **r1** hp ?→72 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=7, fodder_slime=36, fodder_slime=52]
- **r2** hp 72→69 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=7, fodder_slime=24]
- **r3** hp 69→69 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 55 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=30 pick_loot] zone_01
_L3 · HP 72% · 166g · stash 6/10 · enc_at_time=9_
- money +41g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 9 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 28, took 5, healed 0_

- **r1** hp ?→67 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=24, fodder_slime=7, fodder_slime=52]
- **r2** hp 67→64 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=24]
- **r3** hp 64→64 ap 2 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 28 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=31 pick_loot] zone_01
_L4 · HP 57% · 215g · stash 6/10 · enc_at_time=10_
- money +49g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 10 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→62 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 62→62 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=32 pick_loot] zone_01
_L4 · HP 55% · 231g · stash 6/10 · enc_at_time=11_
- money +16g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 11 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→62 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=33 pick_loot] zone_01
_L4 · HP 55% · 238g · stash 6/10 · enc_at_time=12_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 12 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→61 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=2, fodder_slime=36]
- **r2** hp 61→61 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=34 pick_loot] zone_01
_L4 · HP 54% · 252g · stash 6/10 · enc_at_time=13_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=35 use_consumable] zone_01
_L4 · HP 99% · 252g · stash 5/10 · enc_at_time=13_
- use minor_potion on mc_einherjar (HP 61→111/112)

### ENC 13 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→109 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 109→109 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=36 pick_loot] zone_01
_L4 · HP 97% · 268g · stash 5/10 · enc_at_time=14_
- money +16g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 14 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→107 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 107→107 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=37 pick_loot] zone_01
_L4 · HP 96% · 281g · stash 5/10 · enc_at_time=15_
- money +13g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 15 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 64, took 4, healed 0_

- **r1** hp ?→106 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=19, fodder_slime=52, fodder_slime=36]
- **r2** hp 106→103 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=19, fodder_slime=2]
- **r3** hp 103→103 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 64 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=38 pick_loot] zone_01
_L4 · HP 92% · 306g · stash 5/10 · enc_at_time=16_
- money +25g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 16 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→103 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=39 pick_loot] zone_01
_L4 · HP 92% · 310g · stash 5/10 · enc_at_time=17_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 17 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→102 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=2]
- **r2** hp 102→102 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=40 pick_loot] zone_01
_L4 · HP 91% · 318g · stash 5/10 · enc_at_time=18_
- money +8g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 18 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 100→100 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=41 pick_loot] zone_01
_L4 · HP 89% · 324g · stash 5/10 · enc_at_time=19_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 19 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 97, took 3, healed 0_

- **r1** hp ?→97 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=19, fodder_slime=2, fodder_slime=19]
- **r2** hp 97→97 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 97 · KILL fodder_slime,fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=42 pick_loot] zone_01
_L4 · HP 87% · 336g · stash 5/10 · enc_at_time=20_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 20 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→96 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=2, fodder_slime=36]
- **r2** hp 96→96 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=43 pick_loot] zone_01
_L4 · HP 86% · 340g · stash 5/10 · enc_at_time=21_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 21 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→94 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 94→94 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=44 pick_loot] zone_01
_L4 · HP 84% · 343g · stash 5/10 · enc_at_time=22_
- money +3g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 22 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→92 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 92→92 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=45 pick_loot] zone_01
_L5 · HP 72% · 345g · stash 5/10 · enc_at_time=23_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 23 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 39, took 1, healed 0_

- **r1** hp ?→91 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · KILL fodder_slime | end [fodder_slime=36, fodder_slime=0]
- **r2** hp 91→91 ap 1 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 39 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=46 pick_loot] zone_01
_L5 · HP 72% · 347g · stash 5/10 · enc_at_time=24_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 24 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 39, took 1, healed 0_

- **r1** hp ?→90 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · KILL fodder_slime | end [fodder_slime=36, fodder_slime=0]
- **r2** hp 90→90 ap 1 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 39 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=47 pick_loot] zone_01
_L5 · HP 71% · 347g · stash 5/10 · enc_at_time=25_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=48 leave_zone]
_L5 · HP 71% · 347g · stash 5/10 · enc_at_time=25_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=20, cleared=True

### [seq=49 enter_zone] zone_02
_L5 · HP 71% · 347g · stash 5/10 · enc_at_time=25_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 25 [zone_02 idx=0] vs slime, slime → **VICTORY** (3 rounds)
_dealt 67, took 4, healed 0_

- **r1** hp ?→88 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=62, slime=43]
- **r2** hp 88→86 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=27, slime=7]
- **r3** hp 86→86 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 67 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [slime=0, slime=0]

### [seq=50 pick_loot] zone_02
_L5 · HP 68% · 445g · stash 5/10 · enc_at_time=26_
- money +98g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 26 [zone_02 idx=1] vs swime, slime → **VICTORY** (3 rounds)
_dealt 68, took 27, healed 0_

- **r1** hp ?→78 ap 0 st=— | **SURVIVE** +bonus×4 | took 8 | end [swime=45, slime=62]
- **r2** hp 78→59 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 | end [swime=8, slime=27]
- **r3** hp 59→59 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 68 · KILL slime,swime · +status(Brace Strike DEF buff→self) | end [swime=0, slime=0]

### [seq=51 pick_loot] zone_02
_L5 · HP 46% · 490g · stash 5/10 · enc_at_time=27_
- money +45g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=52 use_consumable] zone_02
_L5 · HP 86% · 490g · stash 4/10 · enc_at_time=27_
- use minor_potion on mc_einherjar (HP 59→109/127)

### [seq=53 leave_zone]
_L5 · HP 86% · 490g · stash 4/10 · enc_at_time=27_
- leave zone_02: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=54 enter_town] (in shinto_town)
_L5 · HP 86% · 490g · stash 4/10 · enc_at_time=27_
- enter town shinto_town

### [seq=55 shop_buy] (in shinto_town)
_L5 · HP 86% · 290g · stash 5/10 · enc_at_time=27_
- **BOUGHT** warding_mail @ 200g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=56 shop_buy] (in shinto_town)
_L5 · HP 86% · 170g · stash 6/10 · enc_at_time=27_
- **BOUGHT** iron_guard @ 120g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=57 shop_buy] (in shinto_town)
_L5 · HP 86% · 50g · stash 7/10 · enc_at_time=27_
- **BOUGHT** spirit_mantle @ 120g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=58 shop_buy] (in shinto_town)
_L5 · HP 86% · 20g · stash 8/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=59 equip] (in shinto_town)
_L5 · HP 63% · 20g · stash 7/10 · enc_at_time=27_
- equip warding_mail → mc_einherjar:ARMOR (displaced=None)

### [seq=60 leave_town]
_L5 · HP 63% · 20g · stash 7/10 · enc_at_time=27_
- leave town shinto_town

### [seq=61 enter_zone] zone_02
_L5 · HP 63% · 20g · stash 7/10 · enc_at_time=27_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 27 [zone_02 idx=2] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 100, took 28, healed 0_

- **r1** hp ?→95 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=27, slime=81, slime=43]
- **r2** hp 95→81 ap 1 st=— | **SURVIVE** +bonus×4 | took 14 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=0, slime=47, slime=7]
- **r3** hp 81→81 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 100 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0]

### [seq=62 pick_loot] zone_02
_L5 · HP 47% · 148g · stash 7/10 · enc_at_time=28_
- money +128g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=63 use_consumable] zone_02
_L5 · HP 76% · 148g · stash 6/10 · enc_at_time=28_
- use minor_potion on mc_einherjar (HP 81→131/172)

### [seq=64 leave_zone]
_L5 · HP 76% · 148g · stash 6/10 · enc_at_time=28_
- leave zone_02: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=65 enter_town] (in shinto_town)
_L5 · HP 76% · 148g · stash 6/10 · enc_at_time=28_
- enter town shinto_town

### [seq=66 shop_buy] (in shinto_town)
_L5 · HP 76% · 118g · stash 7/10 · enc_at_time=28_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=67 shop_buy] (in shinto_town)
_L5 · HP 76% · 88g · stash 8/10 · enc_at_time=28_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=68 shop_buy] (in shinto_town)
_L5 · HP 76% · 58g · stash 9/10 · enc_at_time=28_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=69 shop_buy] (in shinto_town)
_L5 · HP 76% · 28g · stash 10/10 · enc_at_time=28_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=70 leave_town]
_L5 · HP 76% · 28g · stash 10/10 · enc_at_time=28_
- leave town shinto_town

### [seq=71 enter_zone] zone_02
_L5 · HP 76% · 28g · stash 10/10 · enc_at_time=28_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 28 [zone_02 idx=3] vs chunky_slime, swime → **VICTORY** (5 rounds)
_dealt 76, took 21, healed 0_

- **r1** hp ?→117 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · +status(Taunted→self) | end [chunky_slime=130, swime=66]
- **r2** hp 117→113 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 36 · took 4 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=74, swime=30]
- **r3** hp 113→111 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · KILL swime | end [chunky_slime=54, swime=0]
- **r4** hp 111→110 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [chunky_slime=34, swime=0]
- **r5** hp 110→110 ap 2 st=— | **CHEAT(+1AP)** basic_attack→chunky_slime +cheat_extras×1 +bonus×4 | dealt 40 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=72 pick_loot] zone_02
_L5 · HP 64% · 68g · stash 10/10 · enc_at_time=29_
- money +40g, offered=['sentinel_tonic'], **selected**=[], skipped=['sentinel_tonic'], discarded_stash=[]

### ENC 29 [zone_02 idx=4] vs toxic_slime, slime, slime → **VICTORY** (4 rounds)
_dealt 34, took 13, healed 0_

- **r1** hp ?→106 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self) | end [toxic_slime=50, slime=81, slime=43]
- **r2** hp 106→102 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=13, slime=47, slime=7]
- **r3** hp 102→97 ap 2 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime · +status(?→self), -status(Searing Edge DOT→self) | end [toxic_slime=0, slime=13, slime=0]
- **r4** hp 97→97 ap 3 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 34 · KILL slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=73 pick_loot] zone_02
_L6 · HP 52% · 174g · stash 10/10 · enc_at_time=30_
- money +106g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=74 use_consumable] zone_02
_L6 · HP 78% · 174g · stash 9/10 · enc_at_time=30_
- use minor_potion on mc_einherjar (HP 97→147/188)

### ENC 30 [zone_02 idx=5] vs swime, mystic_slime, chunky_slime → **VICTORY** (5 rounds)
_dealt 90, took 82, healed 0_

- **r1** hp ?→144 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(Taunted→self) | end [swime=82, mystic_slime=53, chunky_slime=130]
- **r2** hp 144→102 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 45 · took 42 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=42, mystic_slime=11, chunky_slime=60]
- **r3** hp 102→67 ap 0 st=— | **SURVIVE** +bonus×4 | took 35 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=2, mystic_slime=0, chunky_slime=35]
- **r4** hp 67→65 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL swime · +status(Taunted→self) | end [swime=0, mystic_slime=0, chunky_slime=35]
- **r5** hp 65→65 ap 2 st=Taunted | **CHEAT(+2AP)** brace_strike→chunky_slime +cheat_extras×2 +bonus×4 | dealt 45 · KILL chunky_slime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=75 pick_loot] zone_02
_L6 · HP 35% · 297g · stash 9/10 · enc_at_time=31_
- money +123g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=76 use_consumable] zone_02
_L6 · HP 61% · 297g · stash 8/10 · enc_at_time=31_
- use minor_potion on mc_einherjar (HP 65→115/188)

### ENC 31 [zone_02 idx=6] vs omega_slime → **VICTORY** (14 rounds)
_dealt 184, took 168, healed 150_

- **r1** hp ?→98 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 | end [omega_slime=272]
- **r2** hp 98→98 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=272]
- **r3** hp 98→148 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 46 | end [omega_slime=227]
- **r4** hp 148→111 ap 0 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=205]
- **r5** hp 111→108 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [omega_slime=184]
- **r6** hp 108→105 ap 2 st=— | **SURVIVE** +bonus×4 | took 3 | end [omega_slime=163]
- **r7** hp 105→105 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=166]
- **r8** hp 105→105 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=169]
- **r9** hp 105→68 ap 3 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=149]
- **r10** hp 68→118 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 69 | end [omega_slime=85]
- **r11** hp 118→118 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=90]
- **r12** hp 118→81 ap 1 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=72]
- **r13** hp 81→97 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 46 · took 34 | end [omega_slime=9]
- **r14** hp 97→97 ap 0 st=— | NORMAL basic_attack→omega_slime +bonus×4 | dealt 23 · KILL omega_slime | end [omega_slime=0]

### [seq=77 pick_loot] zone_02
_L6 · HP 52% · 437g · stash 8/10 · enc_at_time=32_
- money +140g, offered=['minor_potion', 'scroll_brace_strike', 'endurance_plate'], **selected**=['minor_potion', 'scroll_brace_strike', 'endurance_plate'], skipped=[], discarded_stash=[]

### [seq=78 use_consumable] zone_02
_L6 · HP 78% · 437g · stash 7/10 · enc_at_time=32_
- use minor_potion on mc_einherjar (HP 97→147/188)

### [seq=79 leave_zone]
_L6 · HP 78% · 437g · stash 7/10 · enc_at_time=32_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=80 enter_town] (in shinto_town)
_L6 · HP 78% · 437g · stash 7/10 · enc_at_time=32_
- enter town shinto_town

### [seq=81 shop_buy] (in shinto_town)
_L6 · HP 78% · 407g · stash 8/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=82 shop_buy] (in shinto_town)
_L6 · HP 78% · 377g · stash 9/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=83 shop_buy] (in shinto_town)
_L6 · HP 78% · 347g · stash 10/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=84 leave_town]
_L6 · HP 78% · 347g · stash 10/10 · enc_at_time=32_
- leave town shinto_town

### [seq=85 enter_zone] zone_02
_L6 · HP 78% · 347g · stash 10/10 · enc_at_time=32_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 32 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 39, took 4, healed 0_

- **r1** hp ?→145 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=76, slime=38]
- **r2** hp 145→143 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime | end [slime=37, slime=0]
- **r3** hp 143→143 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 39 · KILL slime | end [slime=0, slime=0]

### [seq=86 pick_loot] zone_02
_L6 · HP 76% · 445g · stash 10/10 · enc_at_time=33_
- money +98g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 33 [zone_02 idx=7] vs slime, slime → **VICTORY** (3 rounds)
_dealt 73, took 5, healed 0_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=57, slime=76]
- **r2** hp 141→139 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [slime=17, slime=37]
- **r3** hp 139→138 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 73 · took 1 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [slime=0, slime=0]

### [seq=87 pick_loot] zone_02
_L7 · HP 68% · 536g · stash 10/10 · enc_at_time=34_
- money +91g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 34 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 129, took 9, healed 0_

- **r1** hp ?→129 ap 0 st=— | **SURVIVE** +bonus×4 | took 9 | end [swime=35, slime=71]
- **r2** hp 129→129 ap 1 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 129 · KILL slime,swime · +status(Brace Strike DEF buff→self) | end [swime=0, slime=0]

### [seq=88 pick_loot] zone_02
_L7 · HP 64% · 606g · stash 10/10 · enc_at_time=35_
- money +70g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 35 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 82, took 9, healed 0_

- **r1** hp ?→125 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=40, slime=71, slime=71]
- **r2** hp 125→120 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=0, slime=27, slime=27]
- **r3** hp 120→120 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 82 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [toxic_slime=0, slime=0, slime=0]

### [seq=89 pick_loot] zone_02
_L7 · HP 59% · 698g · stash 10/10 · enc_at_time=36_
- money +92g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 36 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (4 rounds)
_dealt 102, took 72, healed 0_

- **r1** hp ?→118 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · +status(Taunted→self) | end [swime=77, mystic_slime=17, chunky_slime=155]
- **r2** hp 118→64 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 75 · took 54 · KILL mystic_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=32, mystic_slime=0, chunky_slime=53]
- **r3** hp 64→48 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 · KILL swime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=0, mystic_slime=0, chunky_slime=26]
- **r4** hp 48→48 ap 1 st=— | NORMAL basic_attack→chunky_slime +bonus×4 | dealt 27 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=90 pick_loot] zone_02
_L7 · HP 24% · 799g · stash 10/10 · enc_at_time=37_
- money +101g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=91 leave_zone]
_L7 · HP 24% · 799g · stash 10/10 · enc_at_time=37_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=92 enter_town] (in shinto_town)
_L7 · HP 24% · 799g · stash 10/10 · enc_at_time=37_
- enter town shinto_town

### [seq=93 leave_town]
_L7 · HP 24% · 799g · stash 10/10 · enc_at_time=37_
- leave town shinto_town

### [seq=94 enter_zone] zone_02
_L7 · HP 24% · 799g · stash 10/10 · enc_at_time=37_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### [seq=95 use_consumable] zone_02
_L7 · HP 48% · 799g · stash 9/10 · enc_at_time=37_
- use minor_potion on mc_einherjar (HP 48→98/203)

### ENC 37 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 132, took 13, healed 0_

- **r1** hp ?→85 ap 0 st=— | **SURVIVE** +bonus×4 | took 13 | end [swime=56, slime=33]
- **r2** hp 85→85 ap 1 st=— | **CHEAT(+1AP)** brace_strike→swime +cheat_extras×1 +bonus×4 | dealt 132 · KILL swime,slime · +status(Brace Strike DEF buff→self) | end [swime=0, slime=0]

### [seq=96 pick_loot] zone_02
_L7 · HP 42% · 845g · stash 9/10 · enc_at_time=38_
- money +46g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=97 use_consumable] zone_02
_L7 · HP 67% · 845g · stash 8/10 · enc_at_time=38_
- use minor_potion on mc_einherjar (HP 85→135/203)

### [seq=98 leave_zone]
_L7 · HP 67% · 845g · stash 8/10 · enc_at_time=38_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=99 enter_town] (in shinto_town)
_L7 · HP 67% · 845g · stash 8/10 · enc_at_time=38_
- enter town shinto_town

### [seq=100 shop_buy] (in shinto_town)
_L7 · HP 67% · 815g · stash 9/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=101 shop_buy] (in shinto_town)
_L7 · HP 67% · 785g · stash 10/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=102 leave_town]
_L7 · HP 67% · 785g · stash 10/10 · enc_at_time=38_
- leave town shinto_town

### [seq=103 enter_zone] zone_02
_L7 · HP 67% · 785g · stash 10/10 · enc_at_time=38_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 38 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 135, took 77, healed 0_

- **r1** hp ?→119 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 · +status(Taunted→self) | end [swime=77, mystic_slime=32, chunky_slime=105]
- **r2** hp 119→58 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 90 · took 61 · KILL mystic_slime,chunky_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=32, mystic_slime=0, chunky_slime=0]
- **r3** hp 58→58 ap 0 st=— | NORMAL basic_attack→swime +bonus×4 | dealt 45 · KILL swime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=104 pick_loot] zone_02
_L8 · HP 26% · 861g · stash 10/10 · enc_at_time=39_
- money +76g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=105 use_consumable] zone_02
_L8 · HP 49% · 861g · stash 9/10 · enc_at_time=39_
- use minor_potion on mc_einherjar (HP 58→108/219)

### ENC 39 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (2 rounds)
_dealt 163, took 13, healed 0_

- **r1** hp ?→95 ap 0 st=— | **SURVIVE** +bonus×4 | took 13 · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=12, slime=28, slime=28]
- **r2** hp 95→95 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 163 · KILL slime,mystic_slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=106 pick_loot] zone_02
_L8 · HP 43% · 916g · stash 9/10 · enc_at_time=40_
- money +55g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=107 use_consumable] zone_02
_L8 · HP 66% · 916g · stash 8/10 · enc_at_time=40_
- use minor_potion on mc_einherjar (HP 95→145/219)

### [seq=108 leave_zone]
_L8 · HP 66% · 916g · stash 8/10 · enc_at_time=40_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=109 enter_town] (in shinto_town)
_L8 · HP 66% · 916g · stash 8/10 · enc_at_time=40_
- enter town shinto_town

### [seq=110 shop_buy] (in shinto_town)
_L8 · HP 66% · 886g · stash 9/10 · enc_at_time=40_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=111 shop_buy] (in shinto_town)
_L8 · HP 66% · 856g · stash 10/10 · enc_at_time=40_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=112 leave_town]
_L8 · HP 66% · 856g · stash 10/10 · enc_at_time=40_
- leave town shinto_town

### [seq=113 enter_zone] zone_02
_L8 · HP 66% · 856g · stash 10/10 · enc_at_time=40_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 40 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 195, took 43, healed 0_

- **r1** hp ?→131 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · +status(Taunted→self) | end [chunky_slime=155, swime=72]
- **r2** hp 131→102 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 101 · took 29 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=22, swime=22]
- **r3** hp 102→102 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 94 · KILL chunky_slime,swime | end [chunky_slime=0, swime=0]

### [seq=114 pick_loot] zone_02
_L8 · HP 47% · 925g · stash 10/10 · enc_at_time=41_
- money +69g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=115 use_consumable] zone_02
_L8 · HP 69% · 925g · stash 9/10 · enc_at_time=41_
- use minor_potion on mc_einherjar (HP 102→152/219)

### ENC 41 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 145, took 3, healed 0_

- **r1** hp ?→151 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(Taunted→self) | end [chunky_slime=155, swime=30]
- **r2** hp 151→149 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 101 · took 2 · KILL swime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=22, swime=0]
- **r3** hp 149→149 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 44 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=116 pick_loot] zone_02
_L8 · HP 68% · 957g · stash 9/10 · enc_at_time=42_
- money +32g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 42 [zone_02 idx=7] vs slime, slime → **VICTORY** (2 rounds)
_dealt 106, took 2, healed 0_

- **r1** hp ?→147 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=47, slime=28]
- **r2** hp 147→147 ap 1 st=— | NORMAL thrust→slime +bonus×4 | dealt 106 · KILL slime,slime | end [slime=0, slime=0]

### [seq=117 pick_loot] zone_02
_L8 · HP 67% · 995g · stash 9/10 · enc_at_time=43_
- money +38g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 43 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (2 rounds)
_dealt 114, took 16, healed 0_

- **r1** hp ?→146 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(Taunted→self) | end [chunky_slime=105, swime=30]
- **r2** hp 146→131 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 114 · took 15 · KILL chunky_slime,swime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=118 pick_loot] zone_02
_L8 · HP 60% · 1023g · stash 9/10 · enc_at_time=44_
- money +28g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 44 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 159, took 11, healed 0_

- **r1** hp ?→120 ap 0 st=— | **SURVIVE** +bonus×4 | took 11 | end [swime=51, slime=66]
- **r2** hp 120→120 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 159 · KILL slime,swime | end [swime=0, slime=0]

### [seq=119 pick_loot] zone_02
_L8 · HP 55% · 1070g · stash 9/10 · enc_at_time=45_
- money +47g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=120 use_consumable] zone_02
_L8 · HP 78% · 1070g · stash 8/10 · enc_at_time=45_
- use minor_potion on mc_einherjar (HP 120→170/219)

### [seq=121 leave_zone]
_L8 · HP 78% · 1070g · stash 8/10 · enc_at_time=45_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=122 enter_town] (in shinto_town)
_L8 · HP 78% · 1070g · stash 8/10 · enc_at_time=45_
- enter town shinto_town

### [seq=123 shop_buy] (in shinto_town)
_L8 · HP 78% · 1040g · stash 9/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=124 shop_buy] (in shinto_town)
_L8 · HP 78% · 1010g · stash 10/10 · enc_at_time=45_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=125 leave_town]
_L8 · HP 78% · 1010g · stash 10/10 · enc_at_time=45_
- leave town shinto_town

### [seq=126 enter_zone] zone_02
_L8 · HP 78% · 1010g · stash 10/10 · enc_at_time=45_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 45 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 107, took 2, healed 0_

- **r1** hp ?→168 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [swime=30, slime=47]
- **r2** hp 168→168 ap 1 st=— | NORMAL thrust→slime +bonus×4 | dealt 107 · KILL slime,swime | end [swime=0, slime=0]

### [seq=127 pick_loot] zone_02
_L8 · HP 77% · 1041g · stash 10/10 · enc_at_time=46_
- money +31g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 46 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime, bandit_slime → **VICTORY** (2 rounds)
_dealt 114, took 25, healed 0_

- **r1** hp ?→153 ap 0 st=— | **SURVIVE** +bonus×4 | took 15 · KILL bandit_slime · +status(?→self), +status(Taunted→self) | end [swime=51, mystic_slime=43, chunky_slime=105, bandit_slime=0]
- **r2** hp 153→143 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 114 · took 10 · KILL chunky_slime,swime,mystic_slime · +status(Brace Strike DEF buff→self), +status(?→self) | end [swime=0, mystic_slime=0, chunky_slime=0, bandit_slime=0]

### [seq=128 pick_loot] zone_02
_L8 · HP 65% · 1104g · stash 10/10 · enc_at_time=47_
- money +63g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 47 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (2 rounds)
_dealt 114, took 22, healed 0_

- **r1** hp ?→142 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(Taunted→self) | end [chunky_slime=105, swime=51]
- **r2** hp 142→121 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 114 · took 21 · KILL chunky_slime,swime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=129 pick_loot] zone_02
_L8 · HP 55% · 1120g · stash 10/10 · enc_at_time=48_
- money +16g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 48 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (2 rounds)
_dealt 109, took 3, healed 0_

- **r1** hp ?→120 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(Taunted→self) | end [chunky_slime=130, swime=51]
- **r2** hp 120→118 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 109 · took 2 · KILL swime,chunky_slime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=130 pick_loot] zone_02
_L8 · HP 54% · 1135g · stash 10/10 · enc_at_time=49_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=131 use_consumable] zone_02
_L8 · HP 77% · 1135g · stash 9/10 · enc_at_time=49_
- use minor_potion on mc_einherjar (HP 118→168/219)

### ENC 49 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 54, took 22, healed 0_

- **r1** hp ?→163 ap 0 st=— | **SURVIVE** +bonus×4 | took 5 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime), +status(?→self) | end [mystic_slime=27, slime=66, slime=47]
- **r2** hp 163→146 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL slime,mystic_slime · enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [mystic_slime=0, slime=17, slime=0]
- **r3** hp 146→146 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=132 pick_loot] zone_02
_L8 · HP 67% · 1150g · stash 9/10 · enc_at_time=50_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 50 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 145, took 3, healed 0_

- **r1** hp ?→145 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(Taunted→self) | end [chunky_slime=155, swime=30]
- **r2** hp 145→143 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 101 · took 2 · KILL swime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=22, swime=0]
- **r3** hp 143→143 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 44 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=133 pick_loot] zone_02
_L8 · HP 65% · 1158g · stash 9/10 · enc_at_time=51_
- money +8g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 51 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 54, took 22, healed 0_

- **r1** hp ?→138 ap 0 st=— | **SURVIVE** +bonus×4 | took 5 · enemy_status(Brace Strike DEF buff→slime), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=27, slime=28, slime=66]
- **r2** hp 138→121 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL mystic_slime,slime · -status(Hex Disrupt→self) | end [mystic_slime=0, slime=0, slime=17]
- **r3** hp 121→121 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=134 pick_loot] zone_02
_L8 · HP 55% · 1163g · stash 9/10 · enc_at_time=52_
- money +5g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=135 leave_zone]
_L8 · HP 55% · 1163g · stash 9/10 · enc_at_time=52_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=136 enter_town] (in shinto_town)
_L8 · HP 55% · 1163g · stash 9/10 · enc_at_time=52_
- enter town shinto_town

### [seq=137 shop_buy] (in shinto_town)
_L8 · HP 55% · 1133g · stash 10/10 · enc_at_time=52_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=138 leave_town]
_L8 · HP 55% · 1133g · stash 10/10 · enc_at_time=52_
- leave town shinto_town

### [seq=139 enter_zone] zone_03
_L8 · HP 55% · 1133g · stash 10/10 · enc_at_time=52_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 52 [zone_03 idx=0] vs brute_oni, slime, slime → **VICTORY** (6 rounds)
_dealt 255, took 120, healed 50_

- **r1** hp ?→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 21 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=271, slime=66, slime=66]
- **r2** hp 100→79 ap 1 st=— | **SURVIVE** +bonus×4 | took 21 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=250, slime=17, slime=17]
- **r3** hp 79→89 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 123 · took 40 · KILL slime,slime | end [brute_oni=155, slime=0, slime=0]
- **r4** hp 89→70 ap 0 st=— | **SURVIVE** +bonus×4 | took 19 | end [brute_oni=134, slime=0, slime=0]
- **r5** hp 70→51 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 | end [brute_oni=113, slime=0, slime=0]
- **r6** hp 51→51 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 132 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=140 pick_loot] zone_03
_L9 · HP 22% · 1316g · stash 10/10 · enc_at_time=53_
- money +183g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=141 use_consumable] zone_03
_L9 · HP 43% · 1316g · stash 9/10 · enc_at_time=53_
- use minor_potion on mc_einherjar (HP 51→101/234)

### ENC 53 [zone_03 idx=1] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 173, took 52, healed 0_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 | end [caster_kitsune=77, slime=61, slime=61]
- **r2** hp 75→49 ap 1 st=— | **SURVIVE** +bonus×4 | took 26 | end [caster_kitsune=21, slime=7, slime=7]
- **r3** hp 49→49 ap 2 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 173 · KILL caster_kitsune,slime,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=142 pick_loot] zone_03
_L9 · HP 21% · 1411g · stash 9/10 · enc_at_time=54_
- money +95g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=143 use_consumable] zone_03
_L9 · HP 42% · 1411g · stash 8/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 49→99/234)

### [seq=144 leave_zone]
_L9 · HP 42% · 1411g · stash 8/10 · enc_at_time=54_
- leave zone_03: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=145 enter_town] (in shinto_town)
_L9 · HP 42% · 1411g · stash 8/10 · enc_at_time=54_
- enter town shinto_town

### [seq=146 shop_buy] (in shinto_town)
_L9 · HP 42% · 1381g · stash 9/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=147 shop_buy] (in shinto_town)
_L9 · HP 42% · 1351g · stash 10/10 · enc_at_time=54_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=148 leave_town]
_L9 · HP 42% · 1351g · stash 10/10 · enc_at_time=54_
- leave town shinto_town

### [seq=149 enter_zone] zone_03
_L9 · HP 42% · 1351g · stash 10/10 · enc_at_time=54_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=150 use_consumable] zone_03
_L9 · HP 64% · 1351g · stash 9/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 99→149/234)

### ENC 54 [zone_03 idx=2] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 117, took 71, healed 0_

- **r1** hp ?→114 ap 0 st=— | **SURVIVE** +bonus×4 | took 35 | end [speeder_tengu=65, swime=88, swime=109]
- **r2** hp 114→79 ap 1 st=— | **SURVIVE** +bonus×4 | took 35 | end [speeder_tengu=8, swime=34, swime=56]
- **r3** hp 79→78 ap 2 st=— | **CHEAT(+2AP)** thrust→swime +cheat_extras×2 +bonus×4 | dealt 59 · took 1 · retal 58 · KILL speeder_tengu,swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=151 pick_loot] zone_03
_L9 · HP 33% · 1461g · stash 9/10 · enc_at_time=55_
- money +110g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=152 use_consumable] zone_03
_L9 · HP 55% · 1461g · stash 8/10 · enc_at_time=55_
- use minor_potion on mc_einherjar (HP 78→128/234)

### [seq=153 leave_zone]
_L9 · HP 55% · 1461g · stash 8/10 · enc_at_time=55_
- leave zone_03: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=154 enter_town] (in shinto_town)
_L9 · HP 55% · 1461g · stash 8/10 · enc_at_time=55_
- enter town shinto_town

### [seq=155 shop_buy] (in shinto_town)
_L9 · HP 55% · 1431g · stash 9/10 · enc_at_time=55_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=156 shop_buy] (in shinto_town)
_L9 · HP 55% · 1401g · stash 10/10 · enc_at_time=55_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=157 leave_town]
_L9 · HP 55% · 1401g · stash 10/10 · enc_at_time=55_
- leave town shinto_town

### [seq=158 enter_zone] zone_03
_L9 · HP 55% · 1401g · stash 10/10 · enc_at_time=55_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=159 use_consumable] zone_03
_L9 · HP 76% · 1401g · stash 9/10 · enc_at_time=55_
- use minor_potion on mc_einherjar (HP 128→178/234)

### ENC 55 [zone_03 idx=3] vs support_tanuki, brute_oni → **VICTORY** (9 rounds)
_dealt 368, took 212, healed 100_

- **r1** hp ?→155 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 | end [support_tanuki=152, brute_oni=312]
- **r2** hp 155→155 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=203, brute_oni=312]
- **r3** hp 155→132 ap 2 st=— | **SURVIVE** +bonus×4 | took 23 | end [support_tanuki=150, brute_oni=290]
- **r4** hp 132→110 ap 3 st=— | **SURVIVE** +bonus×4 | took 22 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=150, brute_oni=268]
- **r5** hp 110→160 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 173 | end [support_tanuki=148, brute_oni=148]
- **r6** hp 160→115 ap 0 st=— | **SURVIVE** +bonus×4 | took 45 | end [support_tanuki=95, brute_oni=126]
- **r7** hp 115→93 ap 1 st=— | **SURVIVE** +bonus×4 | took 22 | end [support_tanuki=95, brute_oni=155]
- **r8** hp 93→66 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 133 · took 77 · KILL support_tanuki | end [support_tanuki=0, brute_oni=53]
- **r9** hp 66→66 ap 0 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 62 · KILL brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=160 pick_loot] zone_03
_L9 · HP 28% · 1520g · stash 9/10 · enc_at_time=56_
- money +119g, offered=['str_tonic', 'minor_potion'], **selected**=['str_tonic', 'minor_potion'], skipped=[], discarded_stash=[]

### [seq=161 use_consumable] zone_03
_L9 · HP 50% · 1520g · stash 8/10 · enc_at_time=56_
- use minor_potion on mc_einherjar (HP 66→116/234)

### [seq=162 leave_zone]
_L9 · HP 50% · 1520g · stash 8/10 · enc_at_time=56_
- leave zone_03: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=163 enter_town] (in shinto_town)
_L9 · HP 50% · 1520g · stash 8/10 · enc_at_time=56_
- enter town shinto_town

### [seq=164 shop_buy] (in shinto_town)
_L9 · HP 50% · 1490g · stash 9/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=165 shop_buy] (in shinto_town)
_L9 · HP 50% · 1460g · stash 10/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=166 leave_town]
_L9 · HP 50% · 1460g · stash 10/10 · enc_at_time=56_
- leave town shinto_town

### [seq=167 enter_zone] zone_03
_L9 · HP 50% · 1460g · stash 10/10 · enc_at_time=56_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=168 use_consumable] zone_03
_L9 · HP 71% · 1460g · stash 9/10 · enc_at_time=56_
- use minor_potion on mc_einherjar (HP 116→166/234)

### [seq=169 leave_zone]
_L9 · HP 71% · 1460g · stash 9/10 · enc_at_time=56_
- leave zone_03: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=170 enter_town] (in shinto_town)
_L9 · HP 71% · 1460g · stash 9/10 · enc_at_time=56_
- enter town shinto_town

### [seq=171 shop_buy] (in shinto_town)
_L9 · HP 71% · 1430g · stash 10/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=172 leave_town]
_L9 · HP 71% · 1430g · stash 10/10 · enc_at_time=56_
- leave town shinto_town

### [seq=173 enter_zone] zone_03
_L9 · HP 71% · 1430g · stash 10/10 · enc_at_time=56_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 56 [zone_03 idx=4] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 118, took 18, healed 0_

- **r1** hp ?→152 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · +status(?→self) | end [caster_kitsune=114, speeder_tengu=106, slime=81]
- **r2** hp 152→148 ap 1 st=— | **SURVIVE** +bonus×4 | took 4 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [caster_kitsune=59, speeder_tengu=0, slime=29]
- **r3** hp 148→148 ap 2 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 118 · KILL caster_kitsune,slime | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=174 pick_loot] zone_03
_L10 · HP 59% · 1694g · stash 10/10 · enc_at_time=57_
- money +264g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=175 recruit_accept] zone_03
_L10 · HP 59% · 1694g · stash 10/10 · enc_at_time=57_
- recruit_accept: Martyr Recruit (martyr L6) id=recruit_martyr_5367

### ENC 57 [zone_03 idx=5] vs brute_oni, support_tanuki, slime, slime, bandit_slime → **VICTORY** (6 rounds)
_dealt 385, took 160, healed 50_

- **r1** hp ?→146 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Rally buff→brute_oni) | end [brute_oni=282, support_tanuki=180, slime=114, slime=76, bandit_slime=69]
- **r2** hp 146→145 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=220, support_tanuki=180, slime=59, slime=112, bandit_slime=67]
- **r3** hp 145→119 ap 2 st=— | **SURVIVE** +bonus×4 | took 26 | end [brute_oni=189, support_tanuki=146, slime=50, slime=55, bandit_slime=65]
- **r4** hp 119→169 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 215 · KILL bandit_slime,slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=89, support_tanuki=146, slime=0, slime=46, bandit_slime=0]
- **r5** hp 169→168 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime | end [brute_oni=38, support_tanuki=112, slime=0, slime=0, bandit_slime=0]
- **r6** hp 168→168 ap 1 st=— | **CHEAT(+1AP)** thrust→support_tanuki +cheat_extras×1 +bonus×4 | dealt 170 · KILL brute_oni,support_tanuki | end [brute_oni=0, support_tanuki=0, slime=0, slime=0, bandit_slime=0]

### [seq=176 pick_loot] zone_03
_L10 · HP 67% · 1668g · stash 10/10 · enc_at_time=58_
- money +378g, offered=['crusader_tonic', 'battlemage_tonic'], **selected**=['crusader_tonic'], skipped=['battlemage_tonic'], discarded_stash=[]

### [seq=177 use_consumable] zone_03
_L10 · HP 67% · 1668g · stash 9/10 · enc_at_time=58_
- use minor_potion on recruit_martyr_5367 (HP 75→125/205)

### [seq=178 leave_zone]
_L10 · HP 67% · 1668g · stash 9/10 · enc_at_time=58_
- leave zone_03: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=179 enter_town] (in shinto_town)
_L10 · HP 67% · 1668g · stash 9/10 · enc_at_time=58_
- enter town shinto_town

### [seq=180 shop_buy] (in shinto_town)
_L10 · HP 67% · 1638g · stash 10/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=181 leave_town]
_L10 · HP 67% · 1638g · stash 10/10 · enc_at_time=58_
- leave town shinto_town

### [seq=182 enter_zone] zone_03
_L10 · HP 67% · 1638g · stash 10/10 · enc_at_time=58_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 58 [zone_03 idx=6] vs kodama_elder → **VICTORY** (8 rounds)
_dealt 492, took 133, healed 50_

- **r1** hp ?→167 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [kodama_elder=327]
- **r2** hp 167→167 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=329, kodama=87, kodama=87]
- **r3** hp 167→167 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→kodama_elder) | end [kodama_elder=331, kodama=87, kodama=87]
- **r4** hp 167→135 ap 3 st=— | **SURVIVE** +bonus×4 | took 32 | end [kodama_elder=279, kodama=87, kodama=87]
- **r5** hp 135→121 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 243 · took 64 | end [kodama_elder=56, kodama=27, kodama=87]
- **r6** hp 121→121 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→kodama_elder) | end [kodama_elder=72, kodama=27, kodama=87]
- **r7** hp 121→121 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=29, kodama=27, kodama=87]
- **r8** hp 121→121 ap 2 st=— | **CHEAT(+2AP)** thrust→kodama +cheat_extras×2 +bonus×4 | dealt 249 · KILL kodama,kodama,kodama_elder | end [kodama_elder=0, kodama=0, kodama=0]

### [seq=183 pick_loot] zone_03
_L11 · HP 46% · 2058g · stash 10/10 · enc_at_time=59_
- money +420g, offered=['minor_potion', 'cast_heavy_strike', 'cast_brace_strike'], **selected**=['minor_potion'], skipped=['cast_heavy_strike', 'cast_brace_strike'], discarded_stash=[]

### [seq=184 use_consumable] zone_03
_L11 · HP 46% · 2058g · stash 9/10 · enc_at_time=59_
- use minor_potion on recruit_martyr_5367 (HP 89→139/205)

### [seq=185 use_consumable] zone_03
_L11 · HP 65% · 2058g · stash 8/10 · enc_at_time=59_
- use minor_potion on mc_einherjar (HP 121→171/265)

### [seq=186 leave_zone]
_L11 · HP 65% · 2058g · stash 8/10 · enc_at_time=59_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=187 enter_town] (in shinto_town)
_L11 · HP 65% · 2058g · stash 8/10 · enc_at_time=59_
- enter town shinto_town

### [seq=188 shop_buy] (in shinto_town)
_L11 · HP 65% · 2028g · stash 9/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=189 shop_buy] (in shinto_town)
_L11 · HP 65% · 1998g · stash 10/10 · enc_at_time=59_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=190 leave_town]
_L11 · HP 65% · 1998g · stash 10/10 · enc_at_time=59_
- leave town shinto_town

### [seq=191 enter_zone] zone_03
_L11 · HP 65% · 1998g · stash 10/10 · enc_at_time=59_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 59 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 171, took 136, healed 50_

- **r1** hp ?→170 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime), enemy_status(?→recruit_martyr) | end [caster_kitsune=108, speeder_tengu=88, slime=159]
- **r2** hp 170→169 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=61, speeder_tengu=2, slime=150]
- **r3** hp 169→168 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu | end [caster_kitsune=14, speeder_tengu=0, slime=56]
- **r4** hp 168→168 ap 3 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 137 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=192 pick_loot] zone_03
_L11 · HP 63% · 2202g · stash 10/10 · enc_at_time=60_
- money +204g, offered=['spd_tonic', 'paladin_tonic'], **selected**=['spd_tonic'], skipped=['paladin_tonic'], discarded_stash=[]

### [seq=193 use_consumable] zone_03
_L11 · HP 63% · 2202g · stash 9/10 · enc_at_time=60_
- use minor_potion on recruit_martyr_5367 (HP 56→106/205)

### [seq=194 leave_zone]
_L11 · HP 63% · 2202g · stash 9/10 · enc_at_time=60_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=1, cleared=True

### [seq=195 enter_town] (in shinto_town)
_L11 · HP 63% · 2202g · stash 9/10 · enc_at_time=60_
- enter town shinto_town

### [seq=196 shop_buy] (in shinto_town)
_L11 · HP 63% · 2172g · stash 10/10 · enc_at_time=60_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=197 leave_town]
_L11 · HP 63% · 2172g · stash 10/10 · enc_at_time=60_
- leave town shinto_town

### [seq=198 enter_zone] zone_03
_L11 · HP 63% · 2172g · stash 10/10 · enc_at_time=60_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=199 use_consumable] zone_03
_L11 · HP 63% · 2172g · stash 9/10 · enc_at_time=60_
- use minor_potion on recruit_martyr_5367 (HP 106→156/205)

### [seq=200 leave_zone]
_L11 · HP 63% · 2172g · stash 9/10 · enc_at_time=60_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=1, cleared=True

### [seq=201 enter_town] (in shinto_town)
_L11 · HP 63% · 2172g · stash 9/10 · enc_at_time=60_
- enter town shinto_town

### [seq=202 shop_buy] (in shinto_town)
_L11 · HP 63% · 2142g · stash 10/10 · enc_at_time=60_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=203 leave_town]
_L11 · HP 63% · 2142g · stash 10/10 · enc_at_time=60_
- leave town shinto_town

### [seq=204 enter_zone] zone_03
_L11 · HP 63% · 2142g · stash 10/10 · enc_at_time=60_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 60 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (6 rounds)
_dealt 224, took 215, healed 50_

- **r1** hp ?→168 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=175, brute_oni=277]
- **r2** hp 168→168 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=175, brute_oni=265]
- **r3** hp 168→149 ap 2 st=— | **SURVIVE** +bonus×4 | took 19 | end [support_tanuki=120, brute_oni=231]
- **r4** hp 149→149 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=86, brute_oni=174]
- **r5** hp 149→129 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=22, brute_oni=142]
- **r6** hp 129→129 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 201 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=205 pick_loot] zone_03
_L11 · HP 49% · 2280g · stash 9/10 · enc_at_time=61_
- money +138g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=206 leave_zone]
_L11 · HP 49% · 2280g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=207 enter_town] (in shinto_town)
_L11 · HP 49% · 2280g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=208 shop_buy] (in shinto_town)
_L11 · HP 49% · 2250g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=209 leave_town]
_L11 · HP 49% · 2250g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=210 enter_zone] zone_03
_L11 · HP 49% · 2250g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=211 use_consumable] zone_03
_L11 · HP 49% · 2250g · stash 9/10 · enc_at_time=61_
- use minor_potion on recruit_martyr_5367 (HP 30→80/205)

### [seq=212 leave_zone]
_L11 · HP 49% · 2250g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=213 enter_town] (in shinto_town)
_L11 · HP 49% · 2250g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=214 shop_buy] (in shinto_town)
_L11 · HP 49% · 2220g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=215 leave_town]
_L11 · HP 49% · 2220g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=216 enter_zone] zone_03
_L11 · HP 49% · 2220g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=217 use_consumable] zone_03
_L11 · HP 49% · 2220g · stash 9/10 · enc_at_time=61_
- use minor_potion on recruit_martyr_5367 (HP 80→130/205)

### [seq=218 leave_zone]
_L11 · HP 49% · 2220g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=219 enter_town] (in shinto_town)
_L11 · HP 49% · 2220g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=220 shop_buy] (in shinto_town)
_L11 · HP 49% · 2190g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=221 leave_town]
_L11 · HP 49% · 2190g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=222 enter_zone] zone_03
_L11 · HP 49% · 2190g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=223 use_consumable] zone_03
_L11 · HP 68% · 2190g · stash 9/10 · enc_at_time=61_
- use minor_potion on mc_einherjar (HP 129→179/265)

### [seq=224 leave_zone]
_L11 · HP 68% · 2190g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=225 enter_town] (in shinto_town)
_L11 · HP 68% · 2190g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=226 shop_buy] (in shinto_town)
_L11 · HP 68% · 2160g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=227 leave_town]
_L11 · HP 68% · 2160g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=228 enter_zone] zone_03
_L11 · HP 68% · 2160g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 61 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (4 rounds)
_dealt 240, took 66, healed 50_

- **r1** hp ?→178 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=99, slime=126, slime=51]
- **r2** hp 178→178 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [caster_kitsune=71, slime=119, slime=44]
- **r3** hp 178→177 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=67, slime=72, slime=0]
- **r4** hp 177→177 ap 3 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 202 · KILL slime,caster_kitsune · enemy_status(?→recruit_martyr) | end [caster_kitsune=0, slime=0, slime=0]

### [seq=229 pick_loot] zone_03
_L11 · HP 67% · 2354g · stash 9/10 · enc_at_time=62_
- money +194g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=230 leave_zone]
_L11 · HP 67% · 2354g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=231 enter_town] (in shinto_town)
_L11 · HP 67% · 2354g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=232 shop_buy] (in shinto_town)
_L11 · HP 67% · 2324g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=233 leave_town]
_L11 · HP 67% · 2324g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=234 enter_zone] zone_03
_L11 · HP 67% · 2324g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 62 [zone_03 idx=7] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (6 rounds)
_dealt 309, took 174, healed 50_

- **r1** hp ?→162 ap 0 st=— | **SURVIVE** +bonus×4 | took 15 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=256, support_tanuki=146, slime=160, slime=142]
- **r2** hp 162→161 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=205, support_tanuki=180, slime=150, slime=81]
- **r3** hp 161→132 ap 2 st=— | **SURVIVE** +bonus×4 | took 29 | end [brute_oni=167, support_tanuki=116, slime=141, slime=55]
- **r4** hp 132→116 ap 3 st=— | **SURVIVE** +bonus×4 | took 16 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=131, support_tanuki=52, slime=132, slime=46]
- **r5** hp 116→87 ap 3 st=— | **SURVIVE** +bonus×4 | took 29 · KILL support_tanuki · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=95, support_tanuki=0, slime=123, slime=37]
- **r6** hp 87→56 ap 3 st=— | **CHEAT(+3AP)** thrust→slime +cheat_extras×3 +bonus×4 | dealt 289 · took 31 · KILL slime,slime,brute_oni | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=235 pick_loot] zone_03
_L12 · HP 20% · 2584g · stash 9/10 · enc_at_time=63_
- money +260g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=236 leave_zone]
_L12 · HP 20% · 2584g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=237 enter_town] (in shinto_town)
_L12 · HP 20% · 2584g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=238 shop_buy] (in shinto_town)
_L12 · HP 20% · 2554g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=239 leave_town]
_L12 · HP 20% · 2554g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=240 enter_zone] zone_03
_L12 · HP 20% · 2554g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=241 use_consumable] zone_03
_L12 · HP 38% · 2554g · stash 9/10 · enc_at_time=63_
- use minor_potion on mc_einherjar (HP 56→106/281)

### [seq=242 leave_zone]
_L12 · HP 38% · 2554g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=243 enter_town] (in shinto_town)
_L12 · HP 38% · 2554g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=244 shop_buy] (in shinto_town)
_L12 · HP 38% · 2524g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=245 leave_town]
_L12 · HP 38% · 2524g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=246 enter_zone] zone_03
_L12 · HP 38% · 2524g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=247 use_consumable] zone_03
_L12 · HP 56% · 2524g · stash 9/10 · enc_at_time=63_
- use minor_potion on mc_einherjar (HP 106→156/281)

### [seq=248 leave_zone]
_L12 · HP 56% · 2524g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=249 enter_town] (in shinto_town)
_L12 · HP 56% · 2524g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=250 shop_buy] (in shinto_town)
_L12 · HP 56% · 2494g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=251 leave_town]
_L12 · HP 56% · 2494g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=252 enter_zone] zone_03
_L12 · HP 56% · 2494g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 63 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 296, took 52, healed 0_

- **r1** hp ?→155 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=73, speeder_tengu=106, slime=85]
- **r2** hp 155→154 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=31, speeder_tengu=90, slime=19]
- **r3** hp 154→154 ap 2 st=— | **CHEAT(+2AP)** thrust→speeder_tengu +cheat_extras×2 +bonus×4 | dealt 296 · KILL speeder_tengu,slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=253 pick_loot] zone_03
_L12 · HP 55% · 2590g · stash 10/10 · enc_at_time=64_
- money +96g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=254 use_consumable] zone_03
_L12 · HP 55% · 2590g · stash 9/10 · enc_at_time=64_
- use minor_potion on recruit_martyr_5367 (HP 63→113/205)

### [seq=255 leave_zone]
_L12 · HP 55% · 2590g · stash 9/10 · enc_at_time=64_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=256 enter_town] (in shinto_town)
_L12 · HP 55% · 2590g · stash 9/10 · enc_at_time=64_
- enter town shinto_town

### [seq=257 shop_buy] (in shinto_town)
_L12 · HP 55% · 2560g · stash 10/10 · enc_at_time=64_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=258 leave_town]
_L12 · HP 55% · 2560g · stash 10/10 · enc_at_time=64_
- leave town shinto_town

### [seq=259 enter_zone] zone_03
_L12 · HP 55% · 2560g · stash 10/10 · enc_at_time=64_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=260 use_consumable] zone_03
_L12 · HP 73% · 2560g · stash 9/10 · enc_at_time=64_
- use minor_potion on mc_einherjar (HP 154→204/281)

### [seq=261 leave_zone]
_L12 · HP 73% · 2560g · stash 9/10 · enc_at_time=64_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=262 enter_town] (in shinto_town)
_L12 · HP 73% · 2560g · stash 9/10 · enc_at_time=64_
- enter town shinto_town

### [seq=263 shop_buy] (in shinto_town)
_L12 · HP 73% · 2530g · stash 10/10 · enc_at_time=64_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=264 leave_town]
_L12 · HP 73% · 2530g · stash 10/10 · enc_at_time=64_
- leave town shinto_town

### [seq=265 enter_zone] zone_03
_L12 · HP 73% · 2530g · stash 10/10 · enc_at_time=64_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 64 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 262, took 114, healed 50_

- **r1** hp ?→203 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=241, slime=104, slime=142]
- **r2** hp 203→202 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=190, slime=95, slime=76]
- **r3** hp 202→188 ap 2 st=— | **SURVIVE** +bonus×4 | took 14 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=147, slime=85, slime=50]
- **r4** hp 188→173 ap 3 st=— | **SURVIVE** +bonus×4 | took 15 | end [brute_oni=106, slime=20, slime=42]
- **r5** hp 173→173 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 242 · KILL slime,slime,brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=266 pick_loot] zone_03
_L12 · HP 62% · 2695g · stash 9/10 · enc_at_time=65_
- money +165g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=267 leave_zone]
_L12 · HP 62% · 2695g · stash 9/10 · enc_at_time=65_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=268 enter_town] (in shinto_town)
_L12 · HP 62% · 2695g · stash 9/10 · enc_at_time=65_
- enter town shinto_town

### [seq=269 shop_buy] (in shinto_town)
_L12 · HP 62% · 2665g · stash 10/10 · enc_at_time=65_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=270 leave_town]
_L12 · HP 62% · 2665g · stash 10/10 · enc_at_time=65_
- leave town shinto_town

### [seq=271 enter_zone] zone_03
_L12 · HP 62% · 2665g · stash 10/10 · enc_at_time=65_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=272 use_consumable] zone_03
_L12 · HP 62% · 2665g · stash 9/10 · enc_at_time=65_
- use minor_potion on recruit_martyr_5367 (HP 80→130/217)

### [seq=273 leave_zone]
_L12 · HP 62% · 2665g · stash 9/10 · enc_at_time=65_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=274 enter_town] (in shinto_town)
_L12 · HP 62% · 2665g · stash 9/10 · enc_at_time=65_
- enter town shinto_town

### [seq=275 shop_buy] (in shinto_town)
_L12 · HP 62% · 2635g · stash 10/10 · enc_at_time=65_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=276 leave_town]
_L12 · HP 62% · 2635g · stash 10/10 · enc_at_time=65_
- leave town shinto_town

### [seq=277 enter_zone] zone_03
_L12 · HP 62% · 2635g · stash 10/10 · enc_at_time=65_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 65 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 219, took 62, healed 0_

- **r1** hp ?→172 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=99, slime=66, slime=107]
- **r2** hp 172→171 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=47, slime=0, slime=99]
- **r3** hp 171→171 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 219 · KILL slime,caster_kitsune | end [caster_kitsune=0, slime=0, slime=0]

### [seq=278 pick_loot] zone_03
_L12 · HP 61% · 2776g · stash 10/10 · enc_at_time=66_
- money +141g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=279 use_consumable] zone_03
_L12 · HP 61% · 2776g · stash 9/10 · enc_at_time=66_
- use minor_potion on recruit_martyr_5367 (HP 70→120/217)

### [seq=280 leave_zone]
_L12 · HP 61% · 2776g · stash 9/10 · enc_at_time=66_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=7, cleared=True

### [seq=281 enter_town] (in shinto_town)
_L12 · HP 61% · 2776g · stash 9/10 · enc_at_time=66_
- enter town shinto_town

### [seq=282 shop_buy] (in shinto_town)
_L12 · HP 61% · 2746g · stash 10/10 · enc_at_time=66_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=283 leave_town]
_L12 · HP 61% · 2746g · stash 10/10 · enc_at_time=66_
- leave town shinto_town

### [seq=284 enter_zone] zone_03
_L12 · HP 61% · 2746g · stash 10/10 · enc_at_time=66_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 66 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 142, took 84, healed 0_

- **r1** hp ?→170 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [speeder_tengu=29, swime=94, swime=110]
- **r2** hp 170→168 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL speeder_tengu | end [speeder_tengu=0, swime=46, swime=42]
- **r3** hp 168→168 ap 2 st=— | NORMAL thrust→swime +bonus×4 | dealt 142 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=285 pick_loot] zone_03
_L12 · HP 60% · 2854g · stash 10/10 · enc_at_time=67_
- money +108g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=286 use_consumable] zone_03
_L12 · HP 60% · 2854g · stash 9/10 · enc_at_time=67_
- use minor_potion on recruit_martyr_5367 (HP 39→89/217)

### [seq=287 leave_zone]
_L12 · HP 60% · 2854g · stash 9/10 · enc_at_time=67_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=288 enter_town] (in shinto_town)
_L12 · HP 60% · 2854g · stash 9/10 · enc_at_time=67_
- enter town shinto_town

### [seq=289 shop_buy] (in shinto_town)
_L12 · HP 60% · 2824g · stash 10/10 · enc_at_time=67_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=290 leave_town]
_L12 · HP 60% · 2824g · stash 10/10 · enc_at_time=67_
- leave town shinto_town

### [seq=291 enter_zone] zone_03
_L12 · HP 60% · 2824g · stash 10/10 · enc_at_time=67_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=292 use_consumable] zone_03
_L12 · HP 60% · 2824g · stash 9/10 · enc_at_time=67_
- use minor_potion on recruit_martyr_5367 (HP 89→139/217)

### [seq=293 leave_zone]
_L12 · HP 60% · 2824g · stash 9/10 · enc_at_time=67_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=294 enter_town] (in shinto_town)
_L12 · HP 60% · 2824g · stash 9/10 · enc_at_time=67_
- enter town shinto_town

### [seq=295 shop_buy] (in shinto_town)
_L12 · HP 60% · 2794g · stash 10/10 · enc_at_time=67_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=296 leave_town]
_L12 · HP 60% · 2794g · stash 10/10 · enc_at_time=67_
- leave town shinto_town

### [seq=297 enter_zone] zone_03
_L12 · HP 60% · 2794g · stash 10/10 · enc_at_time=67_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 67 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 218, took 83, healed 0_

- **r1** hp ?→157 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(?→recruit_martyr), +status(?→self), enemy_status(?→recruit_martyr) | end [caster_kitsune=93, speeder_tengu=89, slime=126]
- **r2** hp 157→146 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=51, speeder_tengu=0, slime=117]
- **r3** hp 146→146 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 218 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=298 pick_loot] zone_03
_L13 · HP 49% · 2935g · stash 10/10 · enc_at_time=68_
- money +141g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=299 use_consumable] zone_03
_L13 · HP 49% · 2935g · stash 9/10 · enc_at_time=68_
- use minor_potion on recruit_martyr_5367 (HP 78→128/238)

### [seq=300 leave_zone]
_L13 · HP 49% · 2935g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=301 enter_town] (in shinto_town)
_L13 · HP 49% · 2935g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=302 shop_buy] (in shinto_town)
_L13 · HP 49% · 2905g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=303 leave_town]
_L13 · HP 49% · 2905g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=304 enter_zone] zone_03
_L13 · HP 49% · 2905g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=305 use_consumable] zone_03
_L13 · HP 66% · 2905g · stash 9/10 · enc_at_time=68_
- use minor_potion on mc_einherjar (HP 146→196/296)

### [seq=306 leave_zone]
_L13 · HP 66% · 2905g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=307 enter_town] (in shinto_town)
_L13 · HP 66% · 2905g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=308 shop_buy] (in shinto_town)
_L13 · HP 66% · 2875g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=309 leave_town]
_L13 · HP 66% · 2875g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=310 enter_zone] zone_03
_L13 · HP 66% · 2875g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=311 use_consumable] zone_03
_L13 · HP 66% · 2875g · stash 9/10 · enc_at_time=68_
- use minor_potion on recruit_martyr_5367 (HP 128→178/238)

### [seq=312 leave_zone]
_L13 · HP 66% · 2875g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=313 enter_town] (in shinto_town)
_L13 · HP 66% · 2875g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=314 shop_buy] (in shinto_town)
_L13 · HP 66% · 2845g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=315 leave_town]
_L13 · HP 66% · 2845g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=316 enter_zone] zone_03
_L13 · HP 66% · 2845g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 68 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (4 rounds)
_dealt 166, took 115, healed 50_

- **r1** hp ?→177 ap 0 st=— | **SURVIVE** +bonus×4 | took 19 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=292, slime=99, slime=80]
- **r2** hp 177→175 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=235, slime=29, slime=9]
- **r3** hp 175→173 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime,slime | end [brute_oni=178, slime=0, slime=0]
- **r4** hp 173→139 ap 3 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 162 · took 34 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=317 pick_loot] zone_03
_L13 · HP 47% · 2958g · stash 9/10 · enc_at_time=69_
- money +113g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=318 leave_zone]
_L13 · HP 47% · 2958g · stash 9/10 · enc_at_time=69_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=319 enter_town] (in shinto_town)
_L13 · HP 47% · 2958g · stash 9/10 · enc_at_time=69_
- enter town shinto_town

### [seq=320 shop_buy] (in shinto_town)
_L13 · HP 47% · 2928g · stash 10/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=321 leave_town]
_L13 · HP 47% · 2928g · stash 10/10 · enc_at_time=69_
- leave town shinto_town

### [seq=322 enter_zone] zone_03
_L13 · HP 47% · 2928g · stash 10/10 · enc_at_time=69_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=323 use_consumable] zone_03
_L13 · HP 64% · 2928g · stash 9/10 · enc_at_time=69_
- use minor_potion on mc_einherjar (HP 139→189/296)

### [seq=324 leave_zone]
_L13 · HP 64% · 2928g · stash 9/10 · enc_at_time=69_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=325 enter_town] (in shinto_town)
_L13 · HP 64% · 2928g · stash 9/10 · enc_at_time=69_
- enter town shinto_town

### [seq=326 shop_buy] (in shinto_town)
_L13 · HP 64% · 2898g · stash 10/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=327 leave_town]
_L13 · HP 64% · 2898g · stash 10/10 · enc_at_time=69_
- leave town shinto_town

### [seq=328 enter_zone] zone_03
_L13 · HP 64% · 2898g · stash 10/10 · enc_at_time=69_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 69 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 231, took 30, healed 0_

- **r1** hp ?→189 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=73, slime=126, slime=124]
- **r2** hp 189→187 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(?→recruit_martyr) | end [caster_kitsune=51, slime=54, slime=52]
- **r3** hp 187→187 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 231 · KILL slime,caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=329 pick_loot] zone_03
_L13 · HP 63% · 3001g · stash 10/10 · enc_at_time=70_
- money +103g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 70 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 151, took 58, healed 0_

- **r1** hp ?→185 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [caster_kitsune=99, slime=61, slime=80]
- **r2** hp 185→183 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=47, slime=0, slime=9]
- **r3** hp 183→183 ap 2 st=— | NORMAL thrust→caster_kitsune +bonus×4 | dealt 151 · KILL caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=330 pick_loot] zone_03
_L13 · HP 62% · 3077g · stash 10/10 · enc_at_time=71_
- money +76g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=331 use_consumable] zone_03
_L13 · HP 62% · 3077g · stash 9/10 · enc_at_time=71_
- use minor_potion on recruit_martyr_5367 (HP 88→138/238)

### [seq=332 leave_zone]
_L13 · HP 62% · 3077g · stash 9/10 · enc_at_time=71_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=333 enter_town] (in shinto_town)
_L13 · HP 62% · 3077g · stash 9/10 · enc_at_time=71_
- enter town shinto_town

### [seq=334 shop_buy] (in shinto_town)
_L13 · HP 62% · 3047g · stash 10/10 · enc_at_time=71_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=335 leave_town]
_L13 · HP 62% · 3047g · stash 10/10 · enc_at_time=71_
- leave town shinto_town

### [seq=336 enter_zone] zone_03
_L13 · HP 62% · 3047g · stash 10/10 · enc_at_time=71_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 71 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (7 rounds)
_dealt 346, took 236, healed 50, deaths: ['recruit_martyr_5367']_

- **r1** hp ?→183 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [support_tanuki=230, brute_oni=341]
- **r2** hp 183→183 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=230, brute_oni=315]
- **r3** hp 183→158 ap 2 st=— | **SURVIVE** +bonus×4 | took 25 | end [support_tanuki=143, brute_oni=252]
- **r4** hp 158→138 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=104, brute_oni=214]
- **r5** hp 138→138 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=161, brute_oni=153]
- **r6** hp 138→138 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr · enemy_status(Rally buff→brute_oni) | end [support_tanuki=161, brute_oni=92]
- **r7** hp 138→138 ap 3 st=— | **CHEAT(+3AP)** thrust→support_tanuki +cheat_extras×3 +bonus×4 | dealt 329 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=337 pick_loot] zone_03
_L13 · HP 47% · 3116g · stash 9/10 · enc_at_time=72_
- money +69g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=338 leave_zone]
_L13 · HP 47% · 3116g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=339 enter_town] (in shinto_town)
_L13 · HP 47% · 3116g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=340 shop_buy] (in shinto_town)
_L13 · HP 47% · 3086g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=341 leave_town]
_L13 · HP 47% · 3086g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=342 enter_zone] zone_03
_L13 · HP 47% · 3086g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=343 use_consumable] zone_03
_L13 · HP 64% · 3086g · stash 9/10 · enc_at_time=72_
- use minor_potion on mc_einherjar (HP 138→188/296)

### [seq=344 leave_zone]
_L13 · HP 64% · 3086g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=345 enter_town] (in shinto_town)
_L13 · HP 64% · 3086g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=346 shop_buy] (in shinto_town)
_L13 · HP 64% · 3056g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=347 leave_town]
_L13 · HP 64% · 3056g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=348 enter_zone] zone_03
_L13 · HP 64% · 3056g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 72 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 156, took 64, healed 0_

- **r1** hp ?→186 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [speeder_tengu=85, swime=125, swime=89]
- **r2** hp 186→183 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL speeder_tengu | end [speeder_tengu=0, swime=53, swime=37]
- **r3** hp 183→183 ap 2 st=— | **CHEAT(+1AP)** thrust→swime +cheat_extras×1 +bonus×4 | dealt 156 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=349 pick_loot] zone_03
_L13 · HP 62% · 3133g · stash 10/10 · enc_at_time=73_
- money +77g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=350 use_consumable] zone_03
_L13 · HP 62% · 3133g · stash 9/10 · enc_at_time=73_
- use minor_potion on recruit_martyr_5367 (HP 79→129/238)

### [seq=351 leave_zone]
_L13 · HP 62% · 3133g · stash 9/10 · enc_at_time=73_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=352 enter_town] (in shinto_town)
_L13 · HP 62% · 3133g · stash 9/10 · enc_at_time=73_
- enter town shinto_town

### [seq=353 shop_buy] (in shinto_town)
_L13 · HP 62% · 3103g · stash 10/10 · enc_at_time=73_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=354 leave_town]
_L13 · HP 62% · 3103g · stash 10/10 · enc_at_time=73_
- leave town shinto_town

### [seq=355 enter_zone] zone_03
_L13 · HP 62% · 3103g · stash 10/10 · enc_at_time=73_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=356 use_consumable] zone_03
_L13 · HP 62% · 3103g · stash 9/10 · enc_at_time=73_
- use minor_potion on recruit_martyr_5367 (HP 129→179/238)

### [seq=357 leave_zone]
_L13 · HP 62% · 3103g · stash 9/10 · enc_at_time=73_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=358 enter_town] (in shinto_town)
_L13 · HP 62% · 3103g · stash 9/10 · enc_at_time=73_
- enter town shinto_town

### [seq=359 shop_buy] (in shinto_town)
_L13 · HP 62% · 3073g · stash 10/10 · enc_at_time=73_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=360 leave_town]
_L13 · HP 62% · 3073g · stash 10/10 · enc_at_time=73_
- leave town shinto_town

### [seq=361 enter_zone] zone_03
_L13 · HP 62% · 3073g · stash 10/10 · enc_at_time=73_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 73 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 314, took 6, healed 0_

- **r1** hp ?→182 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=165, slime=41, slime=108]
- **r2** hp 182→180 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime | end [caster_kitsune=161, slime=0, slime=34]
- **r3** hp 180→180 ap 2 st=— | **CHEAT(+2AP)** thrust→caster_kitsune +cheat_extras×2 +bonus×4 | dealt 314 · KILL slime,caster_kitsune | end [caster_kitsune=0, slime=0, slime=0]

### [seq=362 pick_loot] zone_03
_L13 · HP 61% · 3137g · stash 10/10 · enc_at_time=74_
- money +64g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 74 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 231, took 52, healed 0_

- **r1** hp ?→179 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=86, slime=126, slime=80]
- **r2** hp 179→177 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [caster_kitsune=39, slime=54, slime=9]
- **r3** hp 177→177 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 231 · KILL slime,slime,caster_kitsune | end [caster_kitsune=0, slime=0, slime=0]

### [seq=363 pick_loot] zone_03
_L13 · HP 60% · 3174g · stash 10/10 · enc_at_time=75_
- money +37g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=364 use_consumable] zone_03
_L13 · HP 60% · 3174g · stash 9/10 · enc_at_time=75_
- use minor_potion on recruit_martyr_5367 (HP 127→177/259)

### [seq=365 leave_zone]
_L13 · HP 60% · 3174g · stash 9/10 · enc_at_time=75_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=366 enter_town] (in shinto_town)
_L13 · HP 60% · 3174g · stash 9/10 · enc_at_time=75_
- enter town shinto_town

### [seq=367 shop_buy] (in shinto_town)
_L13 · HP 60% · 3144g · stash 10/10 · enc_at_time=75_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=368 leave_town]
_L13 · HP 60% · 3144g · stash 10/10 · enc_at_time=75_
- leave town shinto_town

### [seq=369 enter_zone] zone_03
_L13 · HP 60% · 3144g · stash 10/10 · enc_at_time=75_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 75 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (8 rounds)
_dealt 308, took 109, healed 50_

- **r1** hp ?→176 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=180, brute_oni=338]
- **r2** hp 176→176 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=136, brute_oni=277]
- **r3** hp 176→176 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=118, brute_oni=308]
- **r4** hp 176→176 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [support_tanuki=118, brute_oni=296]
- **r5** hp 176→156 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=163, brute_oni=258]
- **r6** hp 156→155 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 | end [support_tanuki=89, brute_oni=246]
- **r7** hp 155→135 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=55, brute_oni=208]
- **r8** hp 135→135 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 288 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=370 pick_loot] zone_03
_L13 · HP 46% · 3175g · stash 9/10 · enc_at_time=76_
- money +31g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=371 leave_zone]
_L13 · HP 46% · 3175g · stash 9/10 · enc_at_time=76_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=17, cleared=True

### [seq=372 enter_town] (in shinto_town)
_L13 · HP 46% · 3175g · stash 9/10 · enc_at_time=76_
- enter town shinto_town

### [seq=373 shop_buy] (in shinto_town)
_L13 · HP 46% · 3145g · stash 10/10 · enc_at_time=76_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=374 leave_town]
_L13 · HP 46% · 3145g · stash 10/10 · enc_at_time=76_
- leave town shinto_town

### [seq=375 enter_zone] zone_03
_L13 · HP 46% · 3145g · stash 10/10 · enc_at_time=76_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=376 use_consumable] zone_03
_L13 · HP 62% · 3145g · stash 9/10 · enc_at_time=76_
- use minor_potion on mc_einherjar (HP 135→185/296)

### [seq=377 leave_zone]
_L13 · HP 62% · 3145g · stash 9/10 · enc_at_time=76_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=17, cleared=True

### [seq=378 enter_town] (in shinto_town)
_L13 · HP 62% · 3145g · stash 9/10 · enc_at_time=76_
- enter town shinto_town

### [seq=379 shop_buy] (in shinto_town)
_L13 · HP 62% · 3115g · stash 10/10 · enc_at_time=76_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=380 leave_town]
_L13 · HP 62% · 3115g · stash 10/10 · enc_at_time=76_
- leave town shinto_town

### [seq=381 enter_zone] zone_03
_L13 · HP 62% · 3115g · stash 10/10 · enc_at_time=76_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 76 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (4 rounds)
_dealt 123, took 85, healed 50_

- **r1** hp ?→185 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [speeder_tengu=101, swime=125, swime=132]
- **r2** hp 185→184 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [speeder_tengu=85, swime=68, swime=59]
- **r3** hp 184→166 ap 2 st=— | **SURVIVE** +bonus×4 | took 18 · KILL swime,swime | end [speeder_tengu=27, swime=0, swime=0]
- **r4** hp 166→166 ap 3 st=— | NORMAL thrust→speeder_tengu +bonus×4 | dealt 81 · KILL speeder_tengu | end [speeder_tengu=0, swime=0, swime=0]

### [seq=382 pick_loot] zone_03
_L13 · HP 56% · 3143g · stash 9/10 · enc_at_time=77_
- money +28g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=383 leave_zone]
_L13 · HP 56% · 3143g · stash 9/10 · enc_at_time=77_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=18, cleared=True

### [seq=384 enter_town] (in shinto_town)
_L13 · HP 56% · 3143g · stash 9/10 · enc_at_time=77_
- enter town shinto_town

### [seq=385 shop_buy] (in shinto_town)
_L13 · HP 56% · 3113g · stash 10/10 · enc_at_time=77_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=386 leave_town]
_L13 · HP 56% · 3113g · stash 10/10 · enc_at_time=77_
- leave town shinto_town

### [seq=387 enter_zone] zone_03
_L13 · HP 56% · 3113g · stash 10/10 · enc_at_time=77_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 77 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 152, took 64, healed 0_

- **r1** hp ?→164 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · KILL speeder_tengu | end [speeder_tengu=0, swime=125, swime=115]
- **r2** hp 164→137 ap 1 st=— | **SURVIVE** +bonus×4 | took 27 | end [speeder_tengu=0, swime=53, swime=41]
- **r3** hp 137→137 ap 2 st=— | NORMAL thrust→swime +bonus×4 | dealt 152 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=388 pick_loot] zone_03
_L13 · HP 46% · 3133g · stash 10/10 · enc_at_time=78_
- money +20g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=389 use_consumable] zone_03
_L13 · HP 46% · 3133g · stash 9/10 · enc_at_time=78_
- use minor_potion on recruit_martyr_5367 (HP 109→159/259)

### [seq=390 leave_zone]
_L13 · HP 46% · 3133g · stash 9/10 · enc_at_time=78_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=391 enter_town] (in shinto_town)
_L13 · HP 46% · 3133g · stash 9/10 · enc_at_time=78_
- enter town shinto_town

### [seq=392 shop_buy] (in shinto_town)
_L13 · HP 46% · 3103g · stash 10/10 · enc_at_time=78_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=393 leave_town]
_L13 · HP 46% · 3103g · stash 10/10 · enc_at_time=78_
- leave town shinto_town

### [seq=394 enter_zone] zone_03
_L13 · HP 46% · 3103g · stash 10/10 · enc_at_time=78_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=395 use_consumable] zone_03
_L13 · HP 63% · 3103g · stash 9/10 · enc_at_time=78_
- use minor_potion on mc_einherjar (HP 137→187/296)

### [seq=396 leave_zone]
_L13 · HP 63% · 3103g · stash 9/10 · enc_at_time=78_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=397 enter_town] (in shinto_town)
_L13 · HP 63% · 3103g · stash 9/10 · enc_at_time=78_
- enter town shinto_town

### [seq=398 shop_buy] (in shinto_town)
_L13 · HP 63% · 3073g · stash 10/10 · enc_at_time=78_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=399 leave_town]
_L13 · HP 63% · 3073g · stash 10/10 · enc_at_time=78_
- leave town shinto_town

### [seq=400 enter_zone] zone_03
_L13 · HP 63% · 3073g · stash 10/10 · enc_at_time=78_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 78 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (3 rounds)
_dealt 319, took 39, healed 0_

- **r1** hp ?→176 ap 0 st=— | **SURVIVE** +bonus×4 | took 11 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=200, slime=61, slime=159]
- **r2** hp 176→174 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime | end [brute_oni=174, slime=0, slime=89]
- **r3** hp 174→154 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 319 · took 20 · KILL slime,brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=401 pick_loot] zone_03
_L13 · HP 52% · 3082g · stash 10/10 · enc_at_time=79_
- money +9g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=402 leave_zone]
_L13 · HP 52% · 3082g · stash 10/10 · enc_at_time=79_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=403 enter_town] (in shinto_town)
_L13 · HP 52% · 3082g · stash 10/10 · enc_at_time=79_
- enter town shinto_town

### [seq=404 leave_town]
_L13 · HP 52% · 3082g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=405 enter_zone] zone_04
_L13 · HP 52% · 3082g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=406 use_consumable] zone_04
_L13 · HP 69% · 3082g · stash 9/10 · enc_at_time=79_
- use minor_potion on mc_einherjar (HP 154→204/296)

### [seq=407 leave_zone]
_L13 · HP 69% · 3082g · stash 9/10 · enc_at_time=79_
- leave zone_04: reason=sim_post_zone, enc_idx=0, overstay=0, cleared=False

### [seq=408 enter_town] (in shinto_town)
_L13 · HP 69% · 3082g · stash 9/10 · enc_at_time=79_
- enter town shinto_town

### [seq=409 shop_buy] (in shinto_town)
_L13 · HP 69% · 3052g · stash 10/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=410 leave_town]
_L13 · HP 69% · 3052g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=411 enter_zone] zone_04
_L13 · HP 69% · 3052g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 79 [zone_04 idx=0] vs split_slime, split_slime, slime → **VICTORY** (7 rounds)
_dealt 630, took 9, healed 0_

- **r1** hp ?→203 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=81, split_slime=146, slime=160]
- **r2** hp 203→202 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=9, split_slime=139, slime=151]
- **r3** hp 202→201 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=2, split_slime=67, slime=142]
- **r4** hp 201→201 ap 3 st=— | **CHEAT(+3AP)** thrust→slime +cheat_extras×3 +bonus×4 | dealt 310 · KILL slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=42, mini_slime=42, mini_slime=42, mini_slime=42]
- **r5** hp 201→201 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=0, split_slime=0, slime=0, mini_slime=42, mini_slime=42, mini_slime=42, mini_slime=42]
- **r6** hp 201→201 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=0, split_slime=0, slime=0, mini_slime=42, mini_slime=42, mini_slime=42, mini_slime=42]
- **r7** hp 201→201 ap 2 st=— | **CHEAT(+2AP)** thrust→mini_slime +cheat_extras×2 +bonus×4 | dealt 320 · KILL mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=412 pick_loot] zone_04
_L13 · HP 68% · 3380g · stash 10/10 · enc_at_time=80_
- money +328g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 80 [zone_04 idx=1] vs brute_oni, mystic_slime → **VICTORY** (5 rounds)
_dealt 317, took 219, healed 50_

- **r1** hp ?→173 ap 0 st=— | **SURVIVE** +bonus×4 | took 28 · enemy_status(?→recruit_martyr) | end [brute_oni=430, mystic_slime=125]
- **r2** hp 173→145 ap 1 st=— | **SURVIVE** +bonus×4 | took 28 · enemy_status(?→recruit_martyr) | end [brute_oni=400, mystic_slime=95]
- **r3** hp 145→195 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 181 · KILL mystic_slime · enemy_status(?→recruit_martyr) | end [brute_oni=222, mystic_slime=0]
- **r4** hp 195→195 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=150, mystic_slime=0]
- **r5** hp 195→138 ap 1 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 136 · took 57 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=413 pick_loot] zone_04
_L14 · HP 44% · 3645g · stash 9/10 · enc_at_time=81_
- money +265g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=414 leave_zone]
_L14 · HP 44% · 3645g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=415 enter_town] (in shinto_town)
_L14 · HP 44% · 3645g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=416 shop_buy] (in shinto_town)
_L14 · HP 44% · 3615g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=417 leave_town]
_L14 · HP 44% · 3615g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=418 enter_zone] zone_04
_L14 · HP 44% · 3615g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=419 use_consumable] zone_04
_L14 · HP 44% · 3615g · stash 9/10 · enc_at_time=81_
- use minor_potion on recruit_martyr_5367 (HP 41→91/280)

### [seq=420 leave_zone]
_L14 · HP 44% · 3615g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=421 enter_town] (in shinto_town)
_L14 · HP 44% · 3615g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=422 shop_buy] (in shinto_town)
_L14 · HP 44% · 3585g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=423 leave_town]
_L14 · HP 44% · 3585g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=424 enter_zone] zone_04
_L14 · HP 44% · 3585g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=425 use_consumable] zone_04
_L14 · HP 44% · 3585g · stash 9/10 · enc_at_time=81_
- use minor_potion on recruit_martyr_5367 (HP 91→141/280)

### [seq=426 leave_zone]
_L14 · HP 44% · 3585g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=427 enter_town] (in shinto_town)
_L14 · HP 44% · 3585g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=428 shop_buy] (in shinto_town)
_L14 · HP 44% · 3555g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=429 leave_town]
_L14 · HP 44% · 3555g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=430 enter_zone] zone_04
_L14 · HP 44% · 3555g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=431 use_consumable] zone_04
_L14 · HP 60% · 3555g · stash 9/10 · enc_at_time=81_
- use minor_potion on mc_einherjar (HP 138→188/312)

### [seq=432 leave_zone]
_L14 · HP 60% · 3555g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=433 enter_town] (in shinto_town)
_L14 · HP 60% · 3555g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=434 shop_buy] (in shinto_town)
_L14 · HP 60% · 3525g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=435 leave_town]
_L14 · HP 60% · 3525g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=436 enter_zone] zone_04
_L14 · HP 60% · 3525g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=437 use_consumable] zone_04
_L14 · HP 60% · 3525g · stash 9/10 · enc_at_time=81_
- use minor_potion on recruit_martyr_5367 (HP 141→191/280)

### [seq=438 leave_zone]
_L14 · HP 60% · 3525g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=439 enter_town] (in shinto_town)
_L14 · HP 60% · 3525g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=440 shop_buy] (in shinto_town)
_L14 · HP 60% · 3495g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=441 leave_town]
_L14 · HP 60% · 3495g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=442 enter_zone] zone_04
_L14 · HP 60% · 3495g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 81 [zone_04 idx=2] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (6 rounds)
_dealt 376, took 116, healed 0_

- **r1** hp ?→188 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr), enemy_status(Taunted→recruit_martyr), enemy_status(Taunted→recruit_martyr) | end [caster_kitsune=143, chunky_slime=230, chunky_slime=230]
- **r2** hp 188→187 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=62, chunky_slime=174, chunky_slime=220]
- **r3** hp 187→187 ap 2 st=— | **SURVIVE** +bonus×4 | KILL caster_kitsune · enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=164, chunky_slime=211]
- **r4** hp 187→187 ap 3 st=— | **SURVIVE** +bonus×4 | +status(Taunted→self), enemy_status(Taunted→recruit_martyr) | end [caster_kitsune=0, chunky_slime=164, chunky_slime=211]
- **r5** hp 187→186 ap 3 st=Taunted | **CHEAT(+3AP)** brace_strike→chunky_slime +cheat_extras×3 +bonus×4 | dealt 302 · took 1 · KILL chunky_slime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=31]
- **r6** hp 186→186 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 69 · KILL chunky_slime | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=443 pick_loot] zone_04
_L14 · HP 60% · 3699g · stash 10/10 · enc_at_time=82_
- money +204g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=444 use_consumable] zone_04
_L14 · HP 60% · 3699g · stash 9/10 · enc_at_time=82_
- use minor_potion on recruit_martyr_5367 (HP 77→127/280)

### [seq=445 leave_zone]
_L14 · HP 60% · 3699g · stash 9/10 · enc_at_time=82_
- leave zone_04: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=446 enter_town] (in shinto_town)
_L14 · HP 60% · 3699g · stash 9/10 · enc_at_time=82_
- enter town shinto_town

### [seq=447 shop_buy] (in shinto_town)
_L14 · HP 60% · 3669g · stash 10/10 · enc_at_time=82_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=448 leave_town]
_L14 · HP 60% · 3669g · stash 10/10 · enc_at_time=82_
- leave town shinto_town

### [seq=449 enter_zone] zone_04
_L14 · HP 60% · 3669g · stash 10/10 · enc_at_time=82_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=450 use_consumable] zone_04
_L14 · HP 60% · 3669g · stash 9/10 · enc_at_time=82_
- use minor_potion on recruit_martyr_5367 (HP 127→177/280)

### [seq=451 leave_zone]
_L14 · HP 60% · 3669g · stash 9/10 · enc_at_time=82_
- leave zone_04: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=452 enter_town] (in shinto_town)
_L14 · HP 60% · 3669g · stash 9/10 · enc_at_time=82_
- enter town shinto_town

### [seq=453 shop_buy] (in shinto_town)
_L14 · HP 60% · 3639g · stash 10/10 · enc_at_time=82_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=454 leave_town]
_L14 · HP 60% · 3639g · stash 10/10 · enc_at_time=82_
- leave town shinto_town

### [seq=455 enter_zone] zone_04
_L14 · HP 60% · 3639g · stash 10/10 · enc_at_time=82_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 82 [zone_04 idx=3] vs split_slime, speeder_tengu, slime → **VICTORY** (5 rounds)
_dealt 490, took 14, healed 0_

- **r1** hp ?→184 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [split_slime=174, speeder_tengu=110, slime=133]
- **r2** hp 184→183 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu | end [split_slime=163, speeder_tengu=0, slime=119]
- **r3** hp 183→183 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=152, speeder_tengu=0, slime=105]
- **r4** hp 183→183 ap 3 st=— | **CHEAT(+3AP)** thrust→split_slime +cheat_extras×3 +bonus×4 | dealt 324 · KILL slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=50, mini_slime=50]
- **r5** hp 183→183 ap 0 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 166 · KILL mini_slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=456 pick_loot] zone_04
_L14 · HP 59% · 4079g · stash 10/10 · enc_at_time=83_
- money +440g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=457 recruit_accept] zone_04
_L14 · HP 59% · 4079g · stash 10/10 · enc_at_time=83_
- recruit_accept: Berserker Recruit (berserker L8) id=recruit_berserker_4619

### ENC 83 [zone_04 idx=4] vs support_tanuki, swime, brute_oni → **VICTORY** (9 rounds)
_dealt 160, took 483, healed 50, deaths: ['recruit_berserker_4619', 'recruit_martyr_5367']_

- **r1** hp ?→182 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=255, swime=126, brute_oni=502]
- **r2** hp 182→182 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=255, swime=110, brute_oni=403]
- **r3** hp 182→182 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=238, swime=93, brute_oni=302]
- **r4** hp 182→182 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→swime) | end [support_tanuki=238, swime=14, brute_oni=302]
- **r5** hp 182→154 ap 3 st=— | **SURVIVE** +bonus×4 | took 28 · KILL swime,recruit_berserker | end [support_tanuki=162, swime=0, brute_oni=302]
- **r6** hp 154→124 ap 3 st=— | **SURVIVE** +bonus×4 | took 30 | end [support_tanuki=108, swime=0, brute_oni=271]
- **r7** hp 124→93 ap 3 st=— | **SURVIVE** +bonus×4 | took 31 | end [support_tanuki=32, swime=0, brute_oni=240]
- **r8** hp 93→92 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL support_tanuki,recruit_martyr | end [support_tanuki=0, swime=0, brute_oni=141]
- **r9** hp 92→92 ap 3 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 141 · KILL brute_oni | end [support_tanuki=0, swime=0, brute_oni=0]

### [seq=458 pick_loot] zone_04
_L15 · HP 28% · 4478g · stash 10/10 · enc_at_time=84_
- money +399g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=459 use_consumable] zone_04
_L15 · HP 43% · 4478g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 92→142/327)

### [seq=460 leave_zone]
_L15 · HP 43% · 4478g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=461 enter_town] (in shinto_town)
_L15 · HP 43% · 4478g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=462 shop_buy] (in shinto_town)
_L15 · HP 43% · 4448g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=463 leave_town]
_L15 · HP 43% · 4448g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=464 enter_zone] zone_04
_L15 · HP 43% · 4448g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=465 use_consumable] zone_04
_L15 · HP 59% · 4448g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 142→192/327)

### [seq=466 leave_zone]
_L15 · HP 59% · 4448g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=467 enter_town] (in shinto_town)
_L15 · HP 59% · 4448g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=468 shop_buy] (in shinto_town)
_L15 · HP 59% · 4418g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=469 leave_town]
_L15 · HP 59% · 4418g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=470 enter_zone] zone_04
_L15 · HP 59% · 4418g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 84 [zone_04 idx=5] vs brute_oni, caster_kitsune, split_slime → **VICTORY** (8 rounds)
_dealt 378, took 267, healed 50, deaths: ['recruit_berserker_4619']_

- **r1** hp ?→191 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=441, caster_kitsune=223, split_slime=122]
- **r2** hp 191→191 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=348, caster_kitsune=223, split_slime=122]
- **r3** hp 191→190 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=327, caster_kitsune=223, split_slime=28]
- **r4** hp 190→189 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL split_slime | end [brute_oni=234, caster_kitsune=223, split_slime=0]
- **r5** hp 189→189 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_berserker | end [brute_oni=234, caster_kitsune=223, split_slime=0]
- **r6** hp 189→189 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [brute_oni=215, caster_kitsune=171, split_slime=0]
- **r7** hp 189→163 ap 3 st=— | **SURVIVE** +bonus×4 | took 26 · enemy_status(?→recruit_martyr) | end [brute_oni=175, caster_kitsune=119, split_slime=0]
- **r8** hp 163→163 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 361 · KILL brute_oni,caster_kitsune | end [brute_oni=0, caster_kitsune=0, split_slime=0]

### [seq=471 pick_loot] zone_04
_L15 · HP 50% · 4690g · stash 10/10 · enc_at_time=85_
- money +272g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=472 use_consumable] zone_04
_L15 · HP 50% · 4690g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_5367 (HP 112→162/301)

### [seq=473 leave_zone]
_L15 · HP 50% · 4690g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=474 enter_town] (in shinto_town)
_L15 · HP 50% · 4690g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=475 shop_buy] (in shinto_town)
_L15 · HP 50% · 4660g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=476 leave_town]
_L15 · HP 50% · 4660g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=477 enter_zone] zone_04
_L15 · HP 50% · 4660g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=478 use_consumable] zone_04
_L15 · HP 65% · 4660g · stash 9/10 · enc_at_time=85_
- use minor_potion on mc_einherjar (HP 163→213/327)

### [seq=479 leave_zone]
_L15 · HP 65% · 4660g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=480 enter_town] (in shinto_town)
_L15 · HP 65% · 4660g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=481 shop_buy] (in shinto_town)
_L15 · HP 65% · 4630g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=482 leave_town]
_L15 · HP 65% · 4630g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=483 enter_zone] zone_04
_L15 · HP 65% · 4630g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=484 use_consumable] zone_04
_L15 · HP 65% · 4630g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_5367 (HP 162→212/301)

### [seq=485 leave_zone]
_L15 · HP 65% · 4630g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=486 enter_town] (in shinto_town)
_L15 · HP 65% · 4630g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=487 shop_buy] (in shinto_town)
_L15 · HP 65% · 4600g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=488 leave_town]
_L15 · HP 65% · 4600g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=489 enter_zone] zone_04
_L15 · HP 65% · 4600g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 85 [zone_04 idx=6] vs kappa → **VICTORY** (14 rounds)
_dealt 167, took 421, healed 50, deaths: ['recruit_berserker_4619', 'recruit_martyr_5367']_

- **r1** hp ?→213 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=554]
- **r2** hp 213→213 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=559]
- **r3** hp 213→213 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=546]
- **r4** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=552]
- **r5** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=557]
- **r6** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=445]
- **r7** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=370]
- **r8** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=385]
- **r9** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=313]
- **r10** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_berserker | end [kappa=330]
- **r11** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=230]
- **r12** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=252]
- **r13** hp 213→213 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr | end [kappa=155]
- **r14** hp 213→213 ap 3 st=— | **CHEAT(+2AP)** thrust→kappa +cheat_extras×2 +bonus×4 | dealt 165 · KILL kappa | end [kappa=0]

### [seq=490 pick_loot] zone_04
_L15 · HP 65% · 5128g · stash 10/10 · enc_at_time=86_
- money +528g, offered=['potion', 'scroll_searing_edge'], **selected**=['potion'], skipped=['scroll_searing_edge'], discarded_stash=[]

### ENC 86 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (4 rounds)
_dealt 1000, took 9, healed 0_

- **r1** hp ?→212 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=185, split_slime=105, slime=169]
- **r2** hp 212→211 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=105, split_slime=94, slime=169]
- **r3** hp 211→209 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=25, split_slime=14, slime=156]
- **r4** hp 209→209 ap 3 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 270 · KILL slime,mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=491 pick_loot] zone_04
_L16 · HP 61% · 5536g · stash 10/10 · enc_at_time=87_
- money +408g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 87 [zone_04 idx=7] vs support_tanuki, swime, brute_oni → **VICTORY** (9 rounds)
_dealt 337, took 409, healed 0, deaths: ['recruit_berserker_4619']_

- **r1** hp ?→188 ap 0 st=— | **SURVIVE** +bonus×4 | took 21 | end [support_tanuki=195, swime=140, brute_oni=367]
- **r2** hp 188→188 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=265, swime=140, brute_oni=367]
- **r3** hp 188→187 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Rally buff→swime) | end [support_tanuki=265, swime=53, brute_oni=274]
- **r4** hp 187→163 ap 3 st=— | **SURVIVE** +bonus×4 | took 24 | end [support_tanuki=265, swime=123, brute_oni=229]
- **r5** hp 163→163 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_berserker | end [support_tanuki=265, swime=123, brute_oni=229]
- **r6** hp 163→163 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=265, swime=50, brute_oni=245]
- **r7** hp 163→142 ap 3 st=— | **SURVIVE** +bonus×4 | took 21 | end [support_tanuki=180, swime=8, brute_oni=152]
- **r8** hp 142→129 ap 3 st=— | **SURVIVE** +bonus×4 | took 13 · KILL swime | end [support_tanuki=250, swime=0, brute_oni=59]
- **r9** hp 129→129 ap 3 st=— | **CHEAT(+2AP)** thrust→support_tanuki +cheat_extras×2 +bonus×4 | dealt 337 · KILL brute_oni,support_tanuki | end [support_tanuki=0, swime=0, brute_oni=0]

### [seq=492 pick_loot] zone_04
_L16 · HP 38% · 5784g · stash 10/10 · enc_at_time=88_
- money +248g, offered=['minor_potion'], **selected**=[], skipped=['minor_potion'], discarded_stash=[]

### ENC 88 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 417, took 34, healed 0_

- **r1** hp ?→128 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=159, speeder_tengu=111, slime=157]
- **r2** hp 128→127 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=159, speeder_tengu=22, slime=157]
- **r3** hp 127→125 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=73, speeder_tengu=0, slime=157]
- **r4** hp 125→125 ap 3 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 270 · KILL slime,mini_slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=493 pick_loot] zone_04
_L16 · HP 36% · 6133g · stash 10/10 · enc_at_time=89_
- money +349g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 89 [zone_04 idx=7] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (7 rounds)
_dealt 535, took 152, healed 0, deaths: ['recruit_berserker_4619', 'recruit_martyr_5367']_

- **r1** hp ?→125 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_martyr), +status(Taunted→self) | end [caster_kitsune=205, chunky_slime=230, chunky_slime=280]
- **r2** hp 125→125 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 192 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=205, chunky_slime=38, chunky_slime=278]
- **r3** hp 125→123 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · KILL recruit_berserker,chunky_slime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=205, chunky_slime=0, chunky_slime=220]
- **r4** hp 123→123 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_martyr) | end [caster_kitsune=198, chunky_slime=0, chunky_slime=220]
- **r5** hp 123→122 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(?→recruit_martyr), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=150, chunky_slime=0, chunky_slime=159]
- **r6** hp 122→122 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr · enemy_status(?→recruit_martyr) | end [caster_kitsune=102, chunky_slime=0, chunky_slime=149]
- **r7** hp 122→122 ap 3 st=— | **CHEAT(+3AP)** thrust→chunky_slime +cheat_extras×3 +bonus×4 | dealt 338 · KILL chunky_slime,caster_kitsune | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=494 pick_loot] zone_04
_L16 · HP 36% · 6351g · stash 10/10 · enc_at_time=90_
- money +218g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 90 [zone_04 idx=7] vs split_slime, split_slime, slime, bandit_slime → **VICTORY** (5 rounds)
_dealt 850, took 12, healed 0_

- **r1** hp ?→120 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [split_slime=174, split_slime=83, slime=103, bandit_slime=92]
- **r2** hp 120→119 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=174, split_slime=83, slime=19, bandit_slime=88]
- **r3** hp 119→118 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime | end [split_slime=163, split_slime=73, slime=0, bandit_slime=88]
- **r4** hp 118→118 ap 3 st=— | **CHEAT(+3AP)** thrust→bandit_slime +cheat_extras×3 +bonus×4 | dealt 371 · KILL bandit_slime | end [split_slime=0, split_slime=0, slime=0, bandit_slime=0, mini_slime=46, mini_slime=46, mini_slime=50, mini_slime=50]
- **r5** hp 118→118 ap 0 st=— | **SURVIVE** +bonus×4 | KILL mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, bandit_slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=495 pick_loot] zone_04
_L16 · HP 34% · 6341g · stash 10/10 · enc_at_time=91_
- money +401g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 91 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 376, took 50, healed 0_

- **r1** hp ?→115 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [split_slime=66, speeder_tengu=111, slime=103]
- **r2** hp 115→113 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [split_slime=66, speeder_tengu=22, slime=19]
- **r3** hp 113→101 ap 2 st=— | **CHEAT(+2AP)** thrust→split_slime +cheat_extras×2 +bonus×4 | dealt 187 · took 1 · retal 93 · KILL speeder_tengu,slime,mini_slime · enemy_status(?→recruit_berserker), +status(?→self) | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=42]
- **r4** hp 101→101 ap 0 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 96 · KILL mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=496 pick_loot] zone_04
_L17 · HP 28% · 6548g · stash 10/10 · enc_at_time=92_
- money +207g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 92 [zone_04 idx=7] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (7 rounds)
_dealt 720, took 134, healed 0, deaths: ['recruit_berserker_4619']_

- **r1** hp ?→101 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_berserker), +status(Taunted→self), +status(Taunted→self) | end [caster_kitsune=223, chunky_slime=305, chunky_slime=305]
- **r2** hp 101→100 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 124 · took 1 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=223, chunky_slime=169, chunky_slime=244]
- **r3** hp 100→99 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=223, chunky_slime=157, chunky_slime=183]
- **r4** hp 99→99 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_berserker), +status(Taunted→self), enemy_status(Taunted→recruit_berserker) | end [caster_kitsune=223, chunky_slime=157, chunky_slime=183]
- **r5** hp 99→99 ap 2 st=Taunted | **CHEAT(+2AP)** brace_strike→chunky_slime +cheat_extras×2 +bonus×4 | dealt 203 · KILL chunky_slime,chunky_slime,recruit_berserker · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=223, chunky_slime=0, chunky_slime=0]
- **r6** hp 99→99 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [caster_kitsune=171, chunky_slime=0, chunky_slime=0]
- **r7** hp 99→99 ap 1 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 198 · KILL caster_kitsune | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=497 pick_loot] zone_04
_L17 · HP 28% · 6778g · stash 10/10 · enc_at_time=93_
- money +230g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 93 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (6 rounds)
_dealt 435, took 15, healed 0_

- **r1** hp ?→98 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=169, split_slime=169, slime=137]
- **r2** hp 98→98 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=159, split_slime=159, slime=137]
- **r3** hp 98→98 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Brace Strike DEF buff→slime) | end [split_slime=159, split_slime=159, slime=137]
- **r4** hp 98→97 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=159, split_slime=68, slime=122]
- **r5** hp 97→95 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 · KILL split_slime | end [split_slime=159, split_slime=0, slime=36]
- **r6** hp 95→95 ap 3 st=— | **CHEAT(+2AP)** thrust→split_slime +cheat_extras×2 +bonus×4 | dealt 288 · KILL slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=498 pick_loot] zone_04
_L17 · HP 27% · 6939g · stash 10/10 · enc_at_time=94_
- money +161g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=499 leave_zone]
_L17 · HP 27% · 6939g · stash 10/10 · enc_at_time=94_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=500 enter_town] (in shinto_town)
_L17 · HP 27% · 6939g · stash 10/10 · enc_at_time=94_
- enter town shinto_town

### [seq=501 leave_town]
_L17 · HP 27% · 6939g · stash 10/10 · enc_at_time=94_
- leave town shinto_town

### [seq=502 enter_zone] zone_04
_L17 · HP 27% · 6939g · stash 10/10 · enc_at_time=94_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 94 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (5 rounds)
_dealt 304, took 200, healed 0, deaths: ['recruit_berserker_4619', 'recruit_martyr_5367']_

- **r1** hp ?→95 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=418, mystic_slime=170]
- **r2** hp 95→76 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 · KILL recruit_berserker | end [brute_oni=364, mystic_slime=170]
- **r3** hp 76→57 ap 2 st=— | **SURVIVE** +bonus×4 | took 19 | end [brute_oni=310, mystic_slime=164]
- **r4** hp 57→57 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr | end [brute_oni=224, mystic_slime=86]
- **r5** hp 57→18 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 304 · took 39 · KILL mystic_slime,brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=503 pick_loot] zone_04
_L17 · HP 5% · 7039g · stash 10/10 · enc_at_time=95_
- money +100g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=504 leave_zone]
_L17 · HP 5% · 7039g · stash 10/10 · enc_at_time=95_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=505 enter_town] (in shinto_town)
_L17 · HP 5% · 7039g · stash 10/10 · enc_at_time=95_
- enter town shinto_town

### [seq=506 leave_town]
_L17 · HP 5% · 7039g · stash 10/10 · enc_at_time=95_
- leave town shinto_town

### [seq=507 enter_zone] zone_04
_L17 · HP 5% · 7039g · stash 10/10 · enc_at_time=95_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 95 [zone_04 idx=7] vs brute_oni, caster_kitsune, split_slime → **DEFEAT** (2 rounds)
_dealt 0, took 85, healed 0, deaths: ['recruit_berserker_4619', 'recruit_martyr_5367', 'mc_einherjar']_

- **r1** hp ?→18 ap 0 st=— | **SURVIVE** +bonus×4 | KILL recruit_berserker · enemy_status(?→recruit_berserker) | end [brute_oni=418, caster_kitsune=223, split_slime=144]
- **r2** hp 18→0 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 · KILL recruit_martyr · enemy_status(?→recruit_martyr) | end [brute_oni=364, caster_kitsune=171, split_slime=135]
