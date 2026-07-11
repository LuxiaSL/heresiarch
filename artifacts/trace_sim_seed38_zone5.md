# Run Trace: sim_einherjar_seed38_zone5 (einherjar 'sim_mc' L18)

**Final state**: L18 · HP 38/374 · 9143g · zones cleared: ['zone_01', 'zone_02', 'zone_03', 'zone_04']
**Encounters**: 112
**Macro events**: 652

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
_dealt 24, took 8, healed 0_

- **r1** hp ?→62 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 62→60 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r3** hp 60→58 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=24, fodder_slime=24]
- **r4** hp 58→56 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=18, fodder_slime=18]
- **r5** hp 56→54 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r6** hp 54→54 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 24 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=3 pick_loot] zone_01
_L1 · HP 83% · 31g · stash 0/10 · enc_at_time=2_
- money +21g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 2 [zone_01 idx=2] vs fodder_slime, fodder_slime → **VICTORY** (7 rounds)
_dealt 18, took 9, healed 0_

- **r1** hp ?→52 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r2** hp 52→50 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=24, fodder_slime=24]
- **r3** hp 50→49 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=18, fodder_slime=24]
- **r4** hp 49→47 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=18]
- **r5** hp 47→47 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=12, fodder_slime=18]
- **r6** hp 47→45 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=6, fodder_slime=12]
- **r7** hp 45→45 ap 3 st=— | **CHEAT(+2AP)** basic_attack→fodder_slime +cheat_extras×2 +bonus×4 | dealt 18 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=4 pick_loot] zone_01
_L2 · HP 56% · 51g · stash 0/10 · enc_at_time=3_
- money +20g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=5 leave_zone]
_L2 · HP 56% · 51g · stash 0/10 · enc_at_time=3_
- leave zone_01: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=6 enter_town] (in shinto_town)
_L2 · HP 56% · 51g · stash 0/10 · enc_at_time=3_
- enter town shinto_town

### [seq=7 shop_buy] (in shinto_town)
_L2 · HP 56% · 21g · stash 1/10 · enc_at_time=3_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=8 leave_town]
_L2 · HP 56% · 21g · stash 1/10 · enc_at_time=3_
- leave town shinto_town

### [seq=9 enter_zone] zone_01
_L2 · HP 56% · 21g · stash 1/10 · enc_at_time=3_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 3 [zone_01 idx=3] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (5 rounds)
_dealt 42, took 11, healed 41_

- **r1** hp ?→42 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=27, fodder_slime=27, fodder_slime=44]
- **r2** hp 42→40 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=27, fodder_slime=18, fodder_slime=36]
- **r3** hp 40→77 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 25 · took 4 · KILL fodder_slime | end [fodder_slime=18, fodder_slime=0, fodder_slime=12]
- **r4** hp 77→75 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=9, fodder_slime=0, fodder_slime=4]
- **r5** hp 75→75 ap 1 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 17 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=10 pick_loot] zone_01
_L2 · HP 93% · 67g · stash 0/10 · enc_at_time=4_
- money +46g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=11 leave_zone]
_L2 · HP 93% · 67g · stash 0/10 · enc_at_time=4_
- leave zone_01: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=12 enter_town] (in shinto_town)
_L2 · HP 93% · 67g · stash 0/10 · enc_at_time=4_
- enter town shinto_town

### [seq=13 shop_buy] (in shinto_town)
_L2 · HP 93% · 37g · stash 1/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=14 shop_buy] (in shinto_town)
_L2 · HP 93% · 7g · stash 2/10 · enc_at_time=4_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=15 leave_town]
_L2 · HP 93% · 7g · stash 2/10 · enc_at_time=4_
- leave town shinto_town

### [seq=16 enter_zone] zone_01
_L2 · HP 93% · 7g · stash 2/10 · enc_at_time=4_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 4 [zone_01 idx=4] vs alpha_slime → **VICTORY** (10 rounds)
_dealt 21, took 66, healed 50_

- **r1** hp ?→73 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=83]
- **r2** hp 73→65 ap 1 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=76]
- **r3** hp 65→57 ap 2 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=69]
- **r4** hp 57→49 ap 3 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=62]
- **r5** hp 49→47 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=55]
- **r6** hp 47→45 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=48]
- **r7** hp 45→43 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=41]
- **r8** hp 43→77 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 14 · took 16 · retal 7 | end [alpha_slime=13]
- **r9** hp 77→75 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=6]
- **r10** hp 75→59 ap 1 st=— | NORMAL basic_attack→alpha_slime +bonus×4 | took 16 · KILL alpha_slime | end [alpha_slime=0]

### [seq=17 pick_loot] zone_01
_L2 · HP 73% · 91g · stash 4/10 · enc_at_time=5_
- money +84g, offered=['potion', 'warding_mail', 'scroll_searing_edge'], **selected**=['potion', 'warding_mail', 'scroll_searing_edge'], skipped=[], discarded_stash=[]

### [seq=18 leave_zone]
_L2 · HP 73% · 91g · stash 4/10 · enc_at_time=5_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=True

### [seq=19 enter_town] (in shinto_town)
_L2 · HP 73% · 91g · stash 4/10 · enc_at_time=5_
- enter town shinto_town

### [seq=20 shop_buy] (in shinto_town)
_L2 · HP 73% · 61g · stash 5/10 · enc_at_time=5_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=21 shop_buy] (in shinto_town)
_L2 · HP 73% · 31g · stash 6/10 · enc_at_time=5_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=22 shop_buy] (in shinto_town)
_L2 · HP 73% · 1g · stash 7/10 · enc_at_time=5_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=23 equip] (in shinto_town)
_L2 · HP 47% · 1g · stash 6/10 · enc_at_time=5_
- equip warding_mail → mc_einherjar:ARMOR (displaced=None)

### [seq=24 leave_town]
_L2 · HP 47% · 1g · stash 6/10 · enc_at_time=5_
- leave town shinto_town

### [seq=25 enter_zone] zone_01
_L2 · HP 47% · 1g · stash 6/10 · enc_at_time=5_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### [seq=26 use_consumable] zone_01
_L2 · HP 87% · 1g · stash 5/10 · enc_at_time=5_
- use minor_potion on mc_einherjar (HP 59→109/126)

### ENC 5 [zone_01 idx=5] vs fodder_slime → **VICTORY** (2 rounds)
_dealt 27, took 1, healed 0_

- **r1** hp ?→108 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=27]
- **r2** hp 108→108 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×4 | dealt 27 · KILL fodder_slime | end [fodder_slime=0]

### [seq=27 pick_loot] zone_01
_L2 · HP 86% · 11g · stash 5/10 · enc_at_time=6_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 6 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (7 rounds)
_dealt 32, took 14, healed 0_

- **r1** hp ?→105 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=27, fodder_slime=44, fodder_slime=44]
- **r2** hp 105→103 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=27, fodder_slime=36, fodder_slime=36]
- **r3** hp 103→102 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=18, fodder_slime=36, fodder_slime=36]
- **r4** hp 102→99 ap 3 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=9, fodder_slime=28, fodder_slime=28]
- **r5** hp 99→96 ap 3 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=20, fodder_slime=20]
- **r6** hp 96→94 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=0, fodder_slime=12, fodder_slime=12]
- **r7** hp 94→94 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 32 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=28 pick_loot] zone_01
_L3 · HP 67% · 53g · stash 5/10 · enc_at_time=7_
- money +42g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 7 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 46, took 4, healed 0_

- **r1** hp ?→92 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=25, fodder_slime=25]
- **r2** hp 92→90 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=14, fodder_slime=14]
- **r3** hp 90→90 ap 2 st=— | **CHEAT(+2AP)** brace_strike→fodder_slime +cheat_extras×2 +bonus×4 | dealt 46 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=29 pick_loot] zone_01
_L3 · HP 64% · 72g · stash 5/10 · enc_at_time=8_
- money +19g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 8 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (4 rounds)
_dealt 35, took 5, healed 0_

- **r1** hp ?→88 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=25, fodder_slime=25]
- **r2** hp 88→87 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=25, fodder_slime=14]
- **r3** hp 87→85 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=14, fodder_slime=3]
- **r4** hp 85→85 ap 3 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 35 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=30 pick_loot] zone_01
_L3 · HP 60% · 89g · stash 5/10 · enc_at_time=9_
- money +17g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 9 [zone_01 idx=5] vs fodder_slime → **VICTORY** (3 rounds)
_dealt 33, took 1, healed 0_

- **r1** hp ?→85 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36]
- **r2** hp 85→84 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=25]
- **r3** hp 84→84 ap 2 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×4 | dealt 33 · KILL fodder_slime | end [fodder_slime=0]

### [seq=31 pick_loot] zone_01
_L3 · HP 60% · 97g · stash 5/10 · enc_at_time=10_
- money +8g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 10 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (4 rounds)
_dealt 46, took 4, healed 0_

- **r1** hp ?→84 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 84→82 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=25, fodder_slime=25]
- **r3** hp 82→80 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=14, fodder_slime=14]
- **r4** hp 80→80 ap 3 st=— | **CHEAT(+2AP)** brace_strike→fodder_slime +cheat_extras×2 +bonus×4 | dealt 46 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=32 pick_loot] zone_01
_L3 · HP 57% · 111g · stash 5/10 · enc_at_time=11_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 11 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 46, took 4, healed 0_

- **r1** hp ?→78 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=25, fodder_slime=25]
- **r2** hp 78→76 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=14, fodder_slime=14]
- **r3** hp 76→76 ap 2 st=— | **CHEAT(+2AP)** brace_strike→fodder_slime +cheat_extras×2 +bonus×4 | dealt 46 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=33 pick_loot] zone_01
_L3 · HP 54% · 126g · stash 5/10 · enc_at_time=12_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=34 use_consumable] zone_01
_L3 · HP 89% · 126g · stash 4/10 · enc_at_time=12_
- use minor_potion on mc_einherjar (HP 76→126/141)

### [seq=35 leave_zone]
_L3 · HP 89% · 126g · stash 4/10 · enc_at_time=12_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=7, cleared=True

### [seq=36 enter_town] (in shinto_town)
_L3 · HP 89% · 126g · stash 4/10 · enc_at_time=12_
- enter town shinto_town

### [seq=37 shop_buy] (in shinto_town)
_L3 · HP 89% · 26g · stash 5/10 · enc_at_time=12_
- **BOUGHT** iron_blade @ 100g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=38 equip] (in shinto_town)
_L3 · HP 89% · 26g · stash 4/10 · enc_at_time=12_
- equip iron_blade → mc_einherjar:WEAPON (displaced=None)

### [seq=39 leave_town]
_L3 · HP 89% · 26g · stash 4/10 · enc_at_time=12_
- leave town shinto_town

### [seq=40 enter_zone] zone_01
_L3 · HP 89% · 26g · stash 4/10 · enc_at_time=12_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 12 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 85, took 1, healed 0_

- **r1** hp ?→125 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=7]
- **r2** hp 125→125 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 85 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=41 pick_loot] zone_01
_L4 · HP 80% · 38g · stash 4/10 · enc_at_time=13_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 13 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→125 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=42 pick_loot] zone_01
_L4 · HP 80% · 44g · stash 4/10 · enc_at_time=14_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 14 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→124 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=2]
- **r2** hp 124→124 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=43 pick_loot] zone_01
_L4 · HP 79% · 56g · stash 4/10 · enc_at_time=15_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=44 leave_zone]
_L4 · HP 79% · 56g · stash 4/10 · enc_at_time=15_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=10, cleared=True

### [seq=45 enter_town] (in shinto_town)
_L4 · HP 79% · 56g · stash 4/10 · enc_at_time=15_
- enter town shinto_town

### [seq=46 shop_buy] (in shinto_town)
_L4 · HP 79% · 26g · stash 5/10 · enc_at_time=15_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=47 leave_town]
_L4 · HP 79% · 26g · stash 5/10 · enc_at_time=15_
- leave town shinto_town

### [seq=48 enter_zone] zone_01
_L4 · HP 79% · 26g · stash 5/10 · enc_at_time=15_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 15 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→124 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=49 pick_loot] zone_01
_L4 · HP 79% · 31g · stash 5/10 · enc_at_time=16_
- money +5g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 16 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 97, took 3, healed 0_

- **r1** hp ?→122 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=36, fodder_slime=19, fodder_slime=19]
- **r2** hp 122→121 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=2, fodder_slime=19, fodder_slime=19]
- **r3** hp 121→121 ap 2 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 97 · KILL fodder_slime,fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=50 pick_loot] zone_01
_L4 · HP 77% · 58g · stash 5/10 · enc_at_time=17_
- money +27g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 17 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 64, took 4, healed 0_

- **r1** hp ?→119 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=19, fodder_slime=52]
- **r2** hp 119→117 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL fodder_slime | end [fodder_slime=2, fodder_slime=0, fodder_slime=19]
- **r3** hp 117→117 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 64 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=51 pick_loot] zone_01
_L4 · HP 75% · 76g · stash 5/10 · enc_at_time=18_
- money +18g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 18 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→116 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=2]
- **r2** hp 116→116 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=52 pick_loot] zone_01
_L4 · HP 74% · 83g · stash 5/10 · enc_at_time=19_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 19 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→116 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=53 pick_loot] zone_01
_L4 · HP 74% · 87g · stash 5/10 · enc_at_time=20_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 20 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→116 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36, fodder_slime=36]
- **r2** hp 116→114 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r3** hp 114→114 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=54 pick_loot] zone_01
_L4 · HP 73% · 91g · stash 5/10 · enc_at_time=21_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 21 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→114 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=55 pick_loot] zone_01
_L4 · HP 73% · 93g · stash 5/10 · enc_at_time=22_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 22 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 63, took 4, healed 0_

- **r1** hp ?→112 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=19, fodder_slime=2, fodder_slime=52]
- **r2** hp 112→110 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL fodder_slime | end [fodder_slime=19, fodder_slime=0, fodder_slime=19]
- **r3** hp 110→110 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 63 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=56 pick_loot] zone_01
_L4 · HP 70% · 99g · stash 5/10 · enc_at_time=23_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 23 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→108 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 108→108 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=57 pick_loot] zone_01
_L4 · HP 69% · 100g · stash 5/10 · enc_at_time=24_
- money +1g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 24 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→107 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=2, fodder_slime=36]
- **r2** hp 107→107 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=58 pick_loot] zone_01
_L4 · HP 68% · 100g · stash 5/10 · enc_at_time=25_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=59 leave_zone]
_L4 · HP 68% · 100g · stash 5/10 · enc_at_time=25_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=20, cleared=True

### [seq=60 enter_zone] zone_02
_L4 · HP 68% · 100g · stash 5/10 · enc_at_time=25_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 25 [zone_02 idx=0] vs slime, slime → **VICTORY** (3 rounds)
_dealt 88, took 4, healed 0_

- **r1** hp ?→105 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=67, slime=48]
- **r2** hp 105→103 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=37, slime=17]
- **r3** hp 103→103 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 88 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [slime=0, slime=0]

### [seq=61 pick_loot] zone_02
_L4 · HP 66% · 147g · stash 5/10 · enc_at_time=26_
- money +47g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 26 [zone_02 idx=1] vs swime, slime → **VICTORY** (3 rounds)
_dealt 60, took 15, healed 0_

- **r1** hp ?→90 ap 0 st=— | **SURVIVE** +bonus×4 | took 13 | end [swime=50, slime=48]
- **r2** hp 90→88 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [swime=18, slime=17]
- **r3** hp 88→88 ap 2 st=— | **CHEAT(+1AP)** brace_strike→swime +cheat_extras×1 +bonus×4 | dealt 60 · KILL swime,slime · +status(Brace Strike DEF buff→self) | end [swime=0, slime=0]

### [seq=62 pick_loot] zone_02
_L5 · HP 51% · 189g · stash 6/10 · enc_at_time=27_
- money +42g, offered=['mystic_tonic'], **selected**=['mystic_tonic'], skipped=[], discarded_stash=[]

### [seq=63 use_consumable] zone_02
_L5 · HP 80% · 189g · stash 5/10 · enc_at_time=27_
- use minor_potion on mc_einherjar (HP 88→138/172)

### [seq=64 leave_zone]
_L5 · HP 80% · 189g · stash 5/10 · enc_at_time=27_
- leave zone_02: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=65 enter_town] (in shinto_town)
_L5 · HP 80% · 189g · stash 5/10 · enc_at_time=27_
- enter town shinto_town

### [seq=66 shop_buy] (in shinto_town)
_L5 · HP 80% · 159g · stash 6/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=67 shop_buy] (in shinto_town)
_L5 · HP 80% · 129g · stash 7/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=68 shop_buy] (in shinto_town)
_L5 · HP 80% · 99g · stash 8/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=69 shop_buy] (in shinto_town)
_L5 · HP 80% · 69g · stash 9/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=70 shop_buy] (in shinto_town)
_L5 · HP 80% · 39g · stash 10/10 · enc_at_time=27_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=71 leave_town]
_L5 · HP 80% · 39g · stash 10/10 · enc_at_time=27_
- leave town shinto_town

### [seq=72 enter_zone] zone_02
_L5 · HP 80% · 39g · stash 10/10 · enc_at_time=27_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 27 [zone_02 idx=2] vs mystic_slime, slime, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 104, took 12, healed 0_

- **r1** hp ?→132 ap 0 st=— | **SURVIVE** +bonus×4 | took 6 · +status(?→self) | end [mystic_slime=42, slime=62, slime=62, bandit_slime=4]
- **r2** hp 132→126 ap 1 st=— | **SURVIVE** +bonus×4 | took 6 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime), +status(?→self), -status(Hex Disrupt→self) | end [mystic_slime=4, slime=27, slime=27, bandit_slime=0]
- **r3** hp 126→126 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 104 · KILL slime,mystic_slime,slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=73 pick_loot] zone_02
_L5 · HP 73% · 188g · stash 10/10 · enc_at_time=28_
- money +188g, offered=['res_tonic'], **selected**=[], skipped=['res_tonic'], discarded_stash=[]

### ENC 28 [zone_02 idx=3] vs chunky_slime, swime → **VICTORY** (7 rounds)
_dealt 94, took 76, healed 0_

- **r1** hp ?→109 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 · +status(Taunted→self) | end [chunky_slime=155, swime=87]
- **r2** hp 109→73 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 30 · took 36 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=108, swime=52]
- **r3** hp 73→55 ap 0 st=— | **SURVIVE** +bonus×4 | took 18 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=91, swime=17]
- **r4** hp 55→52 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL swime · +status(Taunted→self) | end [chunky_slime=91, swime=0]
- **r5** hp 52→51 ap 2 st=Taunted | **CHEAT(+2AP)** brace_strike→chunky_slime +cheat_extras×2 +bonus×4 | dealt 47 · took 1 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=27, swime=0]
- **r6** hp 51→50 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [chunky_slime=10, swime=0]
- **r7** hp 50→50 ap 1 st=— | NORMAL basic_attack→chunky_slime +bonus×4 | dealt 17 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=74 pick_loot] zone_02
_L5 · HP 29% · 298g · stash 10/10 · enc_at_time=29_
- money +110g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=75 use_consumable] zone_02
_L5 · HP 58% · 298g · stash 9/10 · enc_at_time=29_
- use minor_potion on mc_einherjar (HP 50→100/172)

### ENC 29 [zone_02 idx=4] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 66, took 6, healed 0_

- **r1** hp ?→97 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=37, slime=62, slime=62]
- **r2** hp 97→94 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=0, slime=27, slime=27]
- **r3** hp 94→94 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 66 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [toxic_slime=0, slime=0, slime=0]

### [seq=76 pick_loot] zone_02
_L6 · HP 50% · 410g · stash 10/10 · enc_at_time=30_
- money +112g, offered=['mag_tonic'], **selected**=['mag_tonic'], skipped=[], discarded_stash=[]

### [seq=77 use_consumable] zone_02
_L6 · HP 77% · 410g · stash 9/10 · enc_at_time=30_
- use minor_potion on mc_einherjar (HP 94→144/188)

### ENC 30 [zone_02 idx=5] vs swime, mystic_slime, chunky_slime → **VICTORY** (4 rounds)
_dealt 95, took 33, healed 0_

- **r1** hp ?→128 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 · +status(?→self), +status(Taunted→self) | end [swime=61, mystic_slime=37, chunky_slime=130]
- **r2** hp 128→125 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 45 · took 3 · KILL mystic_slime · +status(Brace Strike DEF buff→self), -status(Hex Disrupt→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=20, mystic_slime=0, chunky_slime=60]
- **r3** hp 125→111 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · KILL swime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [swime=0, mystic_slime=0, chunky_slime=35]
- **r4** hp 111→111 ap 1 st=— | **CHEAT(+1AP)** basic_attack→chunky_slime +cheat_extras×1 +bonus×4 | dealt 50 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=78 pick_loot] zone_02
_L6 · HP 59% · 566g · stash 9/10 · enc_at_time=31_
- money +156g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 31 [zone_02 idx=6] vs omega_slime → **VICTORY** (12 rounds)
_dealt 207, took 142, healed 150_

- **r1** hp ?→111 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=295]
- **r2** hp 111→111 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=295]
- **r3** hp 111→74 ap 2 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=272]
- **r4** hp 74→124 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 69 | end [omega_slime=205]
- **r5** hp 124→124 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=207]
- **r6** hp 124→87 ap 1 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=186]
- **r7** hp 87→103 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 46 · took 34 | end [omega_slime=120]
- **r8** hp 103→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [omega_slime=101]
- **r9** hp 100→97 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [omega_slime=82]
- **r10** hp 97→147 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 46 | end [omega_slime=42]
- **r11** hp 147→119 ap 0 st=— | **SURVIVE** +bonus×4 | took 28 | end [omega_slime=25]
- **r12** hp 119→119 ap 1 st=— | **CHEAT(+1AP)** basic_attack→omega_slime +cheat_extras×1 +bonus×4 | dealt 46 · KILL omega_slime | end [omega_slime=0]

### [seq=79 pick_loot] zone_02
_L6 · HP 63% · 811g · stash 8/10 · enc_at_time=32_
- money +245g, offered=['potion', 'scroll_stalwart'], **selected**=['potion', 'scroll_stalwart'], skipped=[], discarded_stash=[]

### [seq=80 leave_zone]
_L6 · HP 63% · 811g · stash 8/10 · enc_at_time=32_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=81 enter_town] (in shinto_town)
_L6 · HP 63% · 811g · stash 8/10 · enc_at_time=32_
- enter town shinto_town

### [seq=82 shop_buy] (in shinto_town)
_L6 · HP 63% · 781g · stash 9/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=83 shop_buy] (in shinto_town)
_L6 · HP 63% · 751g · stash 10/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=84 leave_town]
_L6 · HP 63% · 751g · stash 10/10 · enc_at_time=32_
- leave town shinto_town

### [seq=85 enter_zone] zone_02
_L6 · HP 63% · 751g · stash 10/10 · enc_at_time=32_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 32 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 139, took 15, healed 0_

- **r1** hp ?→106 ap 0 st=— | **SURVIVE** +bonus×4 | took 13 · +status(Taunted→self) | end [chunky_slime=105, swime=61]
- **r2** hp 106→104 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 76 · took 2 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=2, swime=20]
- **r3** hp 104→104 ap 0 st=— | NORMAL brace_strike→swime +bonus×4 | dealt 63 · KILL swime,chunky_slime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=86 pick_loot] zone_02
_L6 · HP 55% · 808g · stash 10/10 · enc_at_time=33_
- money +57g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 33 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 39, took 9, healed 0_

- **r1** hp ?→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=32, slime=38, slime=76]
- **r2** hp 100→95 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime · +status(?→self) | end [toxic_slime=0, slime=0, slime=37]
- **r3** hp 95→95 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 39 · KILL slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=87 pick_loot] zone_02
_L6 · HP 51% · 907g · stash 10/10 · enc_at_time=34_
- money +99g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=88 use_consumable] zone_02
_L6 · HP 77% · 907g · stash 9/10 · enc_at_time=34_
- use minor_potion on mc_einherjar (HP 95→145/188)

### ENC 34 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (5 rounds)
_dealt 122, took 94, healed 0_

- **r1** hp ?→128 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 · +status(Taunted→self) | end [swime=82, mystic_slime=22, chunky_slime=155]
- **r2** hp 128→70 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 61 · took 58 · KILL mystic_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=42, mystic_slime=0, chunky_slime=72]
- **r3** hp 70→67 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [swime=2, mystic_slime=0, chunky_slime=50]
- **r4** hp 67→51 ap 1 st=— | **SURVIVE** +bonus×4 | took 16 · KILL swime · +status(Taunted→self) | end [swime=0, mystic_slime=0, chunky_slime=50]
- **r5** hp 51→51 ap 2 st=Taunted | **CHEAT(+2AP)** brace_strike→chunky_slime +cheat_extras×2 +bonus×4 | dealt 61 · KILL chunky_slime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=89 pick_loot] zone_02
_L7 · HP 25% · 1043g · stash 9/10 · enc_at_time=35_
- money +136g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=90 use_consumable] zone_02
_L7 · HP 50% · 1043g · stash 8/10 · enc_at_time=35_
- use minor_potion on mc_einherjar (HP 51→101/203)

### [seq=91 leave_zone]
_L7 · HP 50% · 1043g · stash 8/10 · enc_at_time=35_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=92 enter_town] (in shinto_town)
_L7 · HP 50% · 1043g · stash 8/10 · enc_at_time=35_
- enter town shinto_town

### [seq=93 shop_buy] (in shinto_town)
_L7 · HP 50% · 1013g · stash 9/10 · enc_at_time=35_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=94 shop_buy] (in shinto_town)
_L7 · HP 50% · 983g · stash 10/10 · enc_at_time=35_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=95 leave_town]
_L7 · HP 50% · 983g · stash 10/10 · enc_at_time=35_
- leave town shinto_town

### [seq=96 enter_zone] zone_02
_L7 · HP 50% · 983g · stash 10/10 · enc_at_time=35_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### [seq=97 use_consumable] zone_02
_L7 · HP 74% · 983g · stash 9/10 · enc_at_time=35_
- use minor_potion on mc_einherjar (HP 101→151/203)

### ENC 35 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 82, took 6, healed 0_

- **r1** hp ?→148 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=27, slime=71, slime=71]
- **r2** hp 148→145 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=0, slime=27, slime=27]
- **r3** hp 145→145 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 82 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [toxic_slime=0, slime=0, slime=0]

### [seq=98 pick_loot] zone_02
_L7 · HP 71% · 1095g · stash 9/10 · enc_at_time=36_
- money +112g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 36 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 114, took 26, healed 0_

- **r1** hp ?→137 ap 0 st=— | **SURVIVE** +bonus×4 | took 8 · +status(Taunted→self) | end [chunky_slime=130, swime=35]
- **r2** hp 137→119 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 84 · took 18 · KILL swime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=16, swime=0]
- **r3** hp 119→119 ap 0 st=— | NORMAL basic_attack→chunky_slime +bonus×4 | dealt 30 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=99 pick_loot] zone_02
_L7 · HP 59% · 1142g · stash 9/10 · enc_at_time=37_
- money +47g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 37 [zone_02 idx=7] vs toxic_slime, slime, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 45, took 10, healed 0_

- **r1** hp ?→114 ap 0 st=— | **SURVIVE** +bonus×4 | took 4 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=12, slime=52, slime=33, bandit_slime=0]
- **r2** hp 114→109 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime · +status(?→self) | end [toxic_slime=0, slime=7, slime=0, bandit_slime=0]
- **r3** hp 109→109 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 45 · KILL slime | end [toxic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=100 pick_loot] zone_02
_L7 · HP 54% · 1298g · stash 9/10 · enc_at_time=38_
- money +156g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=101 use_consumable] zone_02
_L7 · HP 78% · 1298g · stash 8/10 · enc_at_time=38_
- use minor_potion on mc_einherjar (HP 109→159/203)

### [seq=102 leave_zone]
_L7 · HP 78% · 1298g · stash 8/10 · enc_at_time=38_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=103 enter_town] (in shinto_town)
_L7 · HP 78% · 1298g · stash 8/10 · enc_at_time=38_
- enter town shinto_town

### [seq=104 shop_buy] (in shinto_town)
_L7 · HP 78% · 1268g · stash 9/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=105 shop_buy] (in shinto_town)
_L7 · HP 78% · 1238g · stash 10/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=106 leave_town]
_L7 · HP 78% · 1238g · stash 10/10 · enc_at_time=38_
- leave town shinto_town

### [seq=107 enter_zone] zone_02
_L7 · HP 78% · 1238g · stash 10/10 · enc_at_time=38_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 38 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 85, took 14, healed 0_

- **r1** hp ?→152 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · +status(?→self) | end [mystic_slime=48, slime=33, slime=71]
- **r2** hp 152→145 ap 1 st=— | **SURVIVE** +bonus×4 | took 7 · KILL slime · +status(?→self), -status(Hex Disrupt→self) | end [mystic_slime=1, slime=0, slime=27]
- **r3** hp 145→145 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 85 · KILL slime,mystic_slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0]

### [seq=108 pick_loot] zone_02
_L7 · HP 71% · 1300g · stash 10/10 · enc_at_time=39_
- money +62g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 39 [zone_02 idx=7] vs mystic_slime, slime, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 44, took 23, healed 0_

- **r1** hp ?→139 ap 0 st=— | **SURVIVE** +bonus×4 | took 6 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=32, slime=71, slime=33, bandit_slime=0]
- **r2** hp 139→122 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL mystic_slime,slime · enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [mystic_slime=0, slime=27, slime=0, bandit_slime=0]
- **r3** hp 122→122 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 44 · KILL slime | end [mystic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=109 pick_loot] zone_02
_L8 · HP 56% · 1409g · stash 10/10 · enc_at_time=40_
- money +162g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 40 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 159, took 11, healed 0_

- **r1** hp ?→111 ap 0 st=— | **SURVIVE** +bonus×4 | took 11 · enemy_status(Brace Strike DEF buff→slime) | end [swime=51, slime=66]
- **r2** hp 111→111 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 159 · KILL slime,swime | end [swime=0, slime=0]

### [seq=110 pick_loot] zone_02
_L8 · HP 51% · 1445g · stash 10/10 · enc_at_time=41_
- money +36g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=111 use_consumable] zone_02
_L8 · HP 74% · 1445g · stash 9/10 · enc_at_time=41_
- use minor_potion on mc_einherjar (HP 111→161/219)

### ENC 41 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 108, took 20, healed 0_

- **r1** hp ?→158 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=27, slime=66, slime=66]
- **r2** hp 158→141 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=0, slime=17, slime=17]
- **r3** hp 141→141 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 108 · KILL slime,slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=112 pick_loot] zone_02
_L8 · HP 64% · 1537g · stash 9/10 · enc_at_time=42_
- money +92g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 42 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (2 rounds)
_dealt 161, took 3, healed 0_

- **r1** hp ?→138 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [toxic_slime=35, slime=47, slime=47]
- **r2** hp 138→138 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 161 · KILL slime,toxic_slime,slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=113 pick_loot] zone_02
_L8 · HP 63% · 1620g · stash 9/10 · enc_at_time=43_
- money +83g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 43 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 159, took 2, healed 0_

- **r1** hp ?→136 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [swime=51, slime=66]
- **r2** hp 136→136 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 159 · KILL slime,swime | end [swime=0, slime=0]

### [seq=114 pick_loot] zone_02
_L8 · HP 62% · 1654g · stash 9/10 · enc_at_time=44_
- money +34g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 44 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 107, took 8, healed 0_

- **r1** hp ?→128 ap 0 st=— | **SURVIVE** +bonus×4 | took 8 · enemy_status(Brace Strike DEF buff→slime) | end [swime=30, slime=47]
- **r2** hp 128→128 ap 1 st=— | NORMAL thrust→slime +bonus×4 | dealt 107 · KILL slime,swime | end [swime=0, slime=0]

### [seq=115 pick_loot] zone_02
_L8 · HP 58% · 1674g · stash 9/10 · enc_at_time=45_
- money +20g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 45 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (2 rounds)
_dealt 114, took 31, healed 0_

- **r1** hp ?→118 ap 0 st=— | **SURVIVE** +bonus×4 | took 10 · +status(Taunted→self) | end [chunky_slime=105, swime=51]
- **r2** hp 118→97 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 114 · took 21 · KILL chunky_slime,swime · +status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=0]

### [seq=116 pick_loot] zone_02
_L8 · HP 44% · 1702g · stash 9/10 · enc_at_time=46_
- money +28g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=117 use_consumable] zone_02
_L8 · HP 67% · 1702g · stash 8/10 · enc_at_time=46_
- use minor_potion on mc_einherjar (HP 97→147/219)

### [seq=118 leave_zone]
_L8 · HP 67% · 1702g · stash 8/10 · enc_at_time=46_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=119 enter_town] (in shinto_town)
_L8 · HP 67% · 1702g · stash 8/10 · enc_at_time=46_
- enter town shinto_town

### [seq=120 shop_buy] (in shinto_town)
_L8 · HP 67% · 1672g · stash 9/10 · enc_at_time=46_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=121 shop_buy] (in shinto_town)
_L8 · HP 67% · 1642g · stash 10/10 · enc_at_time=46_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=122 leave_town]
_L8 · HP 67% · 1642g · stash 10/10 · enc_at_time=46_
- leave town shinto_town

### [seq=123 enter_zone] zone_02
_L8 · HP 67% · 1642g · stash 10/10 · enc_at_time=46_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 46 [zone_02 idx=7] vs swime, slime, bandit_slime → **VICTORY** (2 rounds)
_dealt 161, took 3, healed 0_

- **r1** hp ?→144 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL bandit_slime | end [swime=72, slime=28, bandit_slime=0]
- **r2** hp 144→144 ap 1 st=— | **CHEAT(+1AP)** thrust→swime +cheat_extras×1 +bonus×4 | dealt 161 · KILL swime,slime | end [swime=0, slime=0, bandit_slime=0]

### [seq=124 pick_loot] zone_02
_L8 · HP 66% · 1628g · stash 10/10 · enc_at_time=47_
- money +27g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 47 [zone_02 idx=7] vs slime, slime → **VICTORY** (2 rounds)
_dealt 158, took 2, healed 0_

- **r1** hp ?→142 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [slime=66, slime=47]
- **r2** hp 142→142 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 158 · KILL slime,slime | end [slime=0, slime=0]

### [seq=125 pick_loot] zone_02
_L8 · HP 65% · 1646g · stash 10/10 · enc_at_time=48_
- money +18g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 48 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (2 rounds)
_dealt 109, took 53, healed 0_

- **r1** hp ?→117 ap 0 st=— | **SURVIVE** +bonus×4 | took 25 · +status(Taunted→self) | end [swime=51, mystic_slime=27, chunky_slime=130]
- **r2** hp 117→89 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 109 · took 28 · KILL swime,mystic_slime,chunky_slime · +status(Brace Strike DEF buff→self), +status(?→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=126 pick_loot] zone_02
_L8 · HP 41% · 1671g · stash 10/10 · enc_at_time=49_
- money +25g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=127 use_consumable] zone_02
_L8 · HP 63% · 1671g · stash 9/10 · enc_at_time=49_
- use minor_potion on mc_einherjar (HP 89→139/219)

### ENC 49 [zone_02 idx=7] vs mystic_slime, slime, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 54, took 10, healed 0_

- **r1** hp ?→132 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · KILL bandit_slime · +status(?→self) | end [mystic_slime=43, slime=66, slime=47, bandit_slime=0]
- **r2** hp 132→129 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL mystic_slime,slime · enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [mystic_slime=0, slime=17, slime=0, bandit_slime=0]
- **r3** hp 129→129 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [mystic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=128 pick_loot] zone_02
_L8 · HP 59% · 1654g · stash 9/10 · enc_at_time=50_
- money +24g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 50 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 145, took 23, healed 0_

- **r1** hp ?→122 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · +status(Taunted→self) | end [chunky_slime=155, swime=30]
- **r2** hp 122→106 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 101 · took 16 · KILL swime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=22, swime=0]
- **r3** hp 106→106 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 44 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=129 pick_loot] zone_02
_L8 · HP 48% · 1661g · stash 9/10 · enc_at_time=51_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=130 use_consumable] zone_02
_L8 · HP 71% · 1661g · stash 8/10 · enc_at_time=51_
- use minor_potion on mc_einherjar (HP 106→156/219)

### [seq=131 leave_zone]
_L8 · HP 71% · 1661g · stash 8/10 · enc_at_time=51_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=132 enter_town] (in shinto_town)
_L8 · HP 71% · 1661g · stash 8/10 · enc_at_time=51_
- enter town shinto_town

### [seq=133 shop_buy] (in shinto_town)
_L8 · HP 71% · 1631g · stash 9/10 · enc_at_time=51_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=134 shop_buy] (in shinto_town)
_L8 · HP 71% · 1601g · stash 10/10 · enc_at_time=51_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=135 leave_town]
_L8 · HP 71% · 1601g · stash 10/10 · enc_at_time=51_
- leave town shinto_town

### [seq=136 enter_zone] zone_02
_L8 · HP 71% · 1601g · stash 10/10 · enc_at_time=51_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 51 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 54, took 8, healed 0_

- **r1** hp ?→152 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=35, slime=66, slime=47]
- **r2** hp 152→148 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=0, slime=17, slime=0]
- **r3** hp 148→148 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=137 pick_loot] zone_02
_L8 · HP 68% · 1607g · stash 10/10 · enc_at_time=52_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=138 leave_zone]
_L8 · HP 68% · 1607g · stash 10/10 · enc_at_time=52_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=139 enter_zone] zone_03
_L8 · HP 68% · 1607g · stash 10/10 · enc_at_time=52_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 52 [zone_03 idx=0] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 194, took 117, healed 50_

- **r1** hp ?→130 ap 0 st=— | **SURVIVE** +bonus×4 | took 18 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=225, slime=66, slime=66]
- **r2** hp 130→112 ap 1 st=— | **SURVIVE** +bonus×4 | took 18 | end [brute_oni=200, slime=17, slime=17]
- **r3** hp 112→129 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 129 · took 33 · KILL slime,slime | end [brute_oni=95, slime=0, slime=0]
- **r4** hp 129→113 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 | end [brute_oni=70, slime=0, slime=0]
- **r5** hp 113→81 ap 1 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 65 · took 32 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=140 pick_loot] zone_03
_L9 · HP 35% · 1772g · stash 9/10 · enc_at_time=53_
- money +165g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=141 use_consumable] zone_03
_L9 · HP 56% · 1772g · stash 8/10 · enc_at_time=53_
- use minor_potion on mc_einherjar (HP 81→131/234)

### [seq=142 leave_zone]
_L9 · HP 56% · 1772g · stash 8/10 · enc_at_time=53_
- leave zone_03: reason=sim_post_zone, enc_idx=1, overstay=0, cleared=False

### [seq=143 enter_town] (in shinto_town)
_L9 · HP 56% · 1772g · stash 8/10 · enc_at_time=53_
- enter town shinto_town

### [seq=144 shop_buy] (in shinto_town)
_L9 · HP 56% · 1742g · stash 9/10 · enc_at_time=53_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=145 shop_buy] (in shinto_town)
_L9 · HP 56% · 1712g · stash 10/10 · enc_at_time=53_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=146 leave_town]
_L9 · HP 56% · 1712g · stash 10/10 · enc_at_time=53_
- leave town shinto_town

### [seq=147 enter_zone] zone_03
_L9 · HP 56% · 1712g · stash 10/10 · enc_at_time=53_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 53 [zone_03 idx=1] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 176, took 36, healed 0_

- **r1** hp ?→121 ap 0 st=— | **SURVIVE** +bonus×4 | took 10 · +status(?→self) | end [caster_kitsune=77, slime=81, slime=81]
- **r2** hp 121→95 ap 1 st=— | **SURVIVE** +bonus×4 | took 26 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [caster_kitsune=21, slime=29, slime=29]
- **r3** hp 95→95 ap 2 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 176 · KILL slime,caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=148 pick_loot] zone_03
_L9 · HP 41% · 1886g · stash 10/10 · enc_at_time=54_
- money +174g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=149 recruit_accept] zone_03
_L9 · HP 41% · 1886g · stash 10/10 · enc_at_time=54_
- recruit_accept: Einherjar Recruit (einherjar L5) id=recruit_einherjar_2449

### [seq=150 use_consumable] zone_03
_L9 · HP 62% · 1886g · stash 9/10 · enc_at_time=54_
- use minor_potion on mc_einherjar (HP 95→145/234)

### ENC 54 [zone_03 idx=2] vs speeder_tengu, swime, swime, bandit_slime → **VICTORY** (3 rounds)
_dealt 178, took 44, healed 0_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 4 · KILL bandit_slime | end [speeder_tengu=51, swime=108, swime=67, bandit_slime=0]
- **r2** hp 141→140 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu | end [speeder_tengu=0, swime=74, swime=32, bandit_slime=0]
- **r3** hp 140→140 ap 2 st=— | **CHEAT(+2AP)** thrust→swime +cheat_extras×2 +bonus×4 | dealt 178 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0, bandit_slime=0]

### [seq=151 pick_loot] zone_03
_L9 · HP 60% · 2103g · stash 9/10 · enc_at_time=55_
- money +294g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 55 [zone_03 idx=3] vs support_tanuki, brute_oni → **VICTORY** (9 rounds)
_dealt 469, took 247, healed 150_

- **r1** hp ?→118 ap 0 st=— | **SURVIVE** +bonus×4 | took 22 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=180, brute_oni=312]
- **r2** hp 118→114 ap 1 st=— | **SURVIVE** +bonus×4 | took 4 | end [support_tanuki=180, brute_oni=312]
- **r3** hp 114→164 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 134 | end [support_tanuki=92, brute_oni=230]
- **r4** hp 164→142 ap 0 st=— | **SURVIVE** +bonus×4 | took 22 | end [support_tanuki=58, brute_oni=208]
- **r5** hp 142→142 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=69, brute_oni=200]
- **r6** hp 142→120 ap 2 st=— | **SURVIVE** +bonus×4 | took 22 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=69, brute_oni=178]
- **r7** hp 120→170 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 174 | end [support_tanuki=60, brute_oni=56]
- **r8** hp 170→149 ap 0 st=— | **SURVIVE** +bonus×4 | took 21 | end [support_tanuki=6, brute_oni=54]
- **r9** hp 149→149 ap 1 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 121 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=152 pick_loot] zone_03
_L10 · HP 60% · 2198g · stash 6/10 · enc_at_time=56_
- money +95g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=153 leave_zone]
_L10 · HP 60% · 2198g · stash 6/10 · enc_at_time=56_
- leave zone_03: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=154 enter_town] (in shinto_town)
_L10 · HP 60% · 2198g · stash 6/10 · enc_at_time=56_
- enter town shinto_town

### [seq=155 shop_buy] (in shinto_town)
_L10 · HP 60% · 2168g · stash 7/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=156 shop_buy] (in shinto_town)
_L10 · HP 60% · 2138g · stash 8/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=157 shop_buy] (in shinto_town)
_L10 · HP 60% · 2108g · stash 9/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=158 shop_buy] (in shinto_town)
_L10 · HP 60% · 2078g · stash 10/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=159 leave_town]
_L10 · HP 60% · 2078g · stash 10/10 · enc_at_time=56_
- leave town shinto_town

### [seq=160 enter_zone] zone_03
_L10 · HP 60% · 2078g · stash 10/10 · enc_at_time=56_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=161 use_consumable] zone_03
_L10 · HP 60% · 2078g · stash 9/10 · enc_at_time=56_
- use minor_potion on recruit_einherjar_2449 (HP 65→115/210)

### ENC 56 [zone_03 idx=4] vs caster_kitsune, speeder_tengu, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 160, took 39, healed 100_

- **r1** hp ?→123 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 | end [caster_kitsune=72, speeder_tengu=81, slime=120, bandit_slime=1]
- **r2** hp 123→112 ap 1 st=— | **SURVIVE** +bonus×4 | took 11 · KILL bandit_slime · +status(?→self) | end [caster_kitsune=11, speeder_tengu=20, slime=64, bandit_slime=0]
- **r3** hp 112→161 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 62 · took 1 · retal 62 · KILL speeder_tengu,slime,caster_kitsune · +status(?→self) | end [caster_kitsune=0, speeder_tengu=0, slime=0, bandit_slime=0]

### [seq=162 pick_loot] zone_03
_L10 · HP 64% · 2335g · stash 7/10 · enc_at_time=57_
- money +257g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=163 leave_zone]
_L10 · HP 64% · 2335g · stash 7/10 · enc_at_time=57_
- leave zone_03: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=164 enter_town] (in shinto_town)
_L10 · HP 64% · 2335g · stash 7/10 · enc_at_time=57_
- enter town shinto_town

### [seq=165 shop_buy] (in shinto_town)
_L10 · HP 64% · 2305g · stash 8/10 · enc_at_time=57_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=166 shop_buy] (in shinto_town)
_L10 · HP 64% · 2275g · stash 9/10 · enc_at_time=57_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=167 shop_buy] (in shinto_town)
_L10 · HP 64% · 2245g · stash 10/10 · enc_at_time=57_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=168 leave_town]
_L10 · HP 64% · 2245g · stash 10/10 · enc_at_time=57_
- leave town shinto_town

### [seq=169 enter_zone] zone_03
_L10 · HP 64% · 2245g · stash 10/10 · enc_at_time=57_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 57 [zone_03 idx=5] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (10 rounds)
_dealt 509, took 332, healed 200_

- **r1** hp ?→135 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime), enemy_status(Rally buff→brute_oni) | end [brute_oni=353, support_tanuki=230, slime=114, slime=114]
- **r2** hp 135→116 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=352, support_tanuki=173, slime=59, slime=84]
- **r3** hp 116→164 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 139 · took 2 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=324, support_tanuki=173, slime=0, slime=29]
- **r4** hp 164→145 ap 0 st=— | **SURVIVE** +bonus×4 | took 19 · KILL slime | end [brute_oni=319, support_tanuki=116, slime=0, slime=0]
- **r5** hp 145→145 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [brute_oni=318, support_tanuki=116, slime=0, slime=0]
- **r6** hp 145→121 ap 2 st=— | **SURVIVE** +bonus×4 | took 24 | end [brute_oni=295, support_tanuki=84, slime=0, slime=0]
- **r7** hp 121→123 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 183 · took 48 · KILL support_tanuki | end [brute_oni=144, support_tanuki=0, slime=0, slime=0]
- **r8** hp 123→123 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=143, support_tanuki=0, slime=0, slime=0]
- **r9** hp 123→123 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=143, support_tanuki=0, slime=0, slime=0]
- **r10** hp 123→123 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 149 · KILL brute_oni | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=170 pick_loot] zone_03
_L11 · HP 46% · 2637g · stash 6/10 · enc_at_time=58_
- money +392g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=171 leave_zone]
_L11 · HP 46% · 2637g · stash 6/10 · enc_at_time=58_
- leave zone_03: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=172 enter_town] (in shinto_town)
_L11 · HP 46% · 2637g · stash 6/10 · enc_at_time=58_
- enter town shinto_town

### [seq=173 shop_buy] (in shinto_town)
_L11 · HP 46% · 2607g · stash 7/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=174 shop_buy] (in shinto_town)
_L11 · HP 46% · 2577g · stash 8/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=175 shop_buy] (in shinto_town)
_L11 · HP 46% · 2547g · stash 9/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=176 shop_buy] (in shinto_town)
_L11 · HP 46% · 2517g · stash 10/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=177 leave_town]
_L11 · HP 46% · 2517g · stash 10/10 · enc_at_time=58_
- leave town shinto_town

### [seq=178 enter_zone] zone_03
_L11 · HP 46% · 2517g · stash 10/10 · enc_at_time=58_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=179 use_consumable] zone_03
_L11 · HP 46% · 2517g · stash 9/10 · enc_at_time=58_
- use minor_potion on recruit_einherjar_2449 (HP 70→120/210)

### [seq=180 use_consumable] zone_03
_L11 · HP 65% · 2517g · stash 8/10 · enc_at_time=58_
- use minor_potion on mc_einherjar (HP 123→173/265)

### [seq=181 leave_zone]
_L11 · HP 65% · 2517g · stash 8/10 · enc_at_time=58_
- leave zone_03: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=182 enter_town] (in shinto_town)
_L11 · HP 65% · 2517g · stash 8/10 · enc_at_time=58_
- enter town shinto_town

### [seq=183 shop_buy] (in shinto_town)
_L11 · HP 65% · 2487g · stash 9/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=184 shop_buy] (in shinto_town)
_L11 · HP 65% · 2457g · stash 10/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=185 leave_town]
_L11 · HP 65% · 2457g · stash 10/10 · enc_at_time=58_
- leave town shinto_town

### [seq=186 enter_zone] zone_03
_L11 · HP 65% · 2457g · stash 10/10 · enc_at_time=58_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 58 [zone_03 idx=6] vs kodama_elder → **VICTORY** (10 rounds)
_dealt 860, took 127, healed 150_

- **r1** hp ?→173 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=381, kodama=87, kodama=87]
- **r2** hp 173→173 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→kodama_elder) | end [kodama_elder=381, kodama=87, kodama=87]
- **r3** hp 173→142 ap 2 st=— | **SURVIVE** +bonus×4 | took 31 | end [kodama_elder=322, kodama=87, kodama=87]
- **r4** hp 142→192 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 263 | end [kodama_elder=107, kodama=22, kodama=87]
- **r5** hp 192→192 ap 0 st=— | **SURVIVE** +bonus×4 | KILL kodama | end [kodama_elder=133, kodama=0, kodama=87]
- **r6** hp 192→192 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=145, kodama=0, kodama=87, kodama=87, kodama=87]
- **r7** hp 192→191 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [kodama_elder=97, kodama=0, kodama=87, kodama=87, kodama=87]
- **r8** hp 191→191 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=82, kodama=0, kodama=87, kodama=87, kodama=87]
- **r9** hp 191→167 ap 3 st=— | **SURVIVE** +bonus×4 | took 24 · KILL kodama | end [kodama_elder=10, kodama=0, kodama=0, kodama=87, kodama=87]
- **r10** hp 167→167 ap 3 st=— | **CHEAT(+3AP)** thrust→kodama +cheat_extras×3 +bonus×4 | dealt 341 · KILL kodama_elder,kodama,kodama | end [kodama_elder=0, kodama=0, kodama=0, kodama=0, kodama=0]

### [seq=187 pick_loot] zone_03
_L11 · HP 63% · 2821g · stash 10/10 · enc_at_time=59_
- money +364g, offered=['minor_potion', 'cast_bolt', 'cast_quick_strike'], **selected**=['minor_potion', 'cast_bolt', 'cast_quick_strike'], skipped=[], discarded_stash=[]

### ENC 59 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 132, took 21, healed 0_

- **r1** hp ?→164 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime), enemy_status(?→recruit_einherjar) | end [caster_kitsune=73, speeder_tengu=0, slime=90]
- **r2** hp 164→163 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=31, speeder_tengu=0, slime=29]
- **r3** hp 163→163 ap 2 st=— | NORMAL thrust→caster_kitsune +bonus×4 | dealt 132 · KILL caster_kitsune,slime | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=188 pick_loot] zone_03
_L11 · HP 62% · 3052g · stash 10/10 · enc_at_time=60_
- money +231g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 60 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (7 rounds)
_dealt 379, took 124, healed 100_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=373, slime=109, slime=109]
- **r2** hp 161→160 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=373, slime=74, slime=49]
- **r3** hp 160→136 ap 2 st=— | **SURVIVE** +bonus×4 | took 24 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=336, slime=39, slime=0]
- **r4** hp 136→186 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 201 · KILL slime | end [brute_oni=192, slime=0, slime=0]
- **r5** hp 186→163 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 | end [brute_oni=164, slime=0, slime=0]
- **r6** hp 163→163 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=161, slime=0, slime=0]
- **r7** hp 163→163 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 169 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=189 pick_loot] zone_03
_L12 · HP 58% · 3249g · stash 8/10 · enc_at_time=61_
- money +197g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=190 leave_zone]
_L12 · HP 58% · 3249g · stash 8/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=191 enter_town] (in shinto_town)
_L12 · HP 58% · 3249g · stash 8/10 · enc_at_time=61_
- enter town shinto_town

### [seq=192 shop_buy] (in shinto_town)
_L12 · HP 58% · 3219g · stash 9/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=193 shop_buy] (in shinto_town)
_L12 · HP 58% · 3189g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=194 leave_town]
_L12 · HP 58% · 3189g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=195 enter_zone] zone_03
_L12 · HP 58% · 3189g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=196 use_consumable] zone_03
_L12 · HP 58% · 3189g · stash 9/10 · enc_at_time=61_
- use minor_potion on recruit_einherjar_2449 (HP 108→158/241)

### [seq=197 leave_zone]
_L12 · HP 58% · 3189g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=198 enter_town] (in shinto_town)
_L12 · HP 58% · 3189g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=199 shop_buy] (in shinto_town)
_L12 · HP 58% · 3159g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=200 leave_town]
_L12 · HP 58% · 3159g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=201 enter_zone] zone_03
_L12 · HP 58% · 3159g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 61 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (6 rounds)
_dealt 358, took 111, healed 50_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 22 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=343, slime=129, slime=104]
- **r2** hp 141→118 ap 1 st=— | **SURVIVE** +bonus×4 | took 23 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=310, slime=64, slime=39]
- **r3** hp 118→168 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 169 · KILL slime | end [brute_oni=198, slime=24, slime=0]
- **r4** hp 168→147 ap 0 st=— | **SURVIVE** +bonus×4 | took 21 · KILL slime | end [brute_oni=165, slime=0, slime=0]
- **r5** hp 147→147 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=157, slime=0, slime=0]
- **r6** hp 147→147 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 189 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=202 pick_loot] zone_03
_L12 · HP 52% · 3295g · stash 9/10 · enc_at_time=62_
- money +136g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=203 use_consumable] zone_03
_L12 · HP 52% · 3295g · stash 8/10 · enc_at_time=62_
- use minor_potion on recruit_einherjar_2449 (HP 113→163/241)

### [seq=204 leave_zone]
_L12 · HP 52% · 3295g · stash 8/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=205 enter_town] (in shinto_town)
_L12 · HP 52% · 3295g · stash 8/10 · enc_at_time=62_
- enter town shinto_town

### [seq=206 shop_buy] (in shinto_town)
_L12 · HP 52% · 3265g · stash 9/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=207 shop_buy] (in shinto_town)
_L12 · HP 52% · 3235g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=208 leave_town]
_L12 · HP 52% · 3235g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=209 enter_zone] zone_03
_L12 · HP 52% · 3235g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=210 use_consumable] zone_03
_L12 · HP 70% · 3235g · stash 9/10 · enc_at_time=62_
- use minor_potion on mc_einherjar (HP 147→197/281)

### [seq=211 leave_zone]
_L12 · HP 70% · 3235g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=212 enter_town] (in shinto_town)
_L12 · HP 70% · 3235g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=213 shop_buy] (in shinto_town)
_L12 · HP 70% · 3205g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=214 leave_town]
_L12 · HP 70% · 3205g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=215 enter_zone] zone_03
_L12 · HP 70% · 3205g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 62 [zone_03 idx=7] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (8 rounds)
_dealt 475, took 211, healed 100_

- **r1** hp ?→196 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Rally buff→brute_oni) | end [brute_oni=322, support_tanuki=230, slime=110, slime=66]
- **r2** hp 196→151 ap 1 st=— | **SURVIVE** +bonus×4 | took 45 | end [brute_oni=285, support_tanuki=163, slime=44, slime=24]
- **r3** hp 151→165 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 177 · took 36 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=175, support_tanuki=96, slime=3, slime=0]
- **r4** hp 165→165 ap 0 st=— | **SURVIVE** +bonus×4 | KILL slime | end [brute_oni=220, support_tanuki=96, slime=0, slime=0]
- **r5** hp 165→165 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [brute_oni=172, support_tanuki=54, slime=0, slime=0]
- **r6** hp 165→165 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=172, support_tanuki=111, slime=0, slime=0]
- **r7** hp 165→147 ap 3 st=— | **SURVIVE** +bonus×4 | took 18 | end [brute_oni=135, support_tanuki=69, slime=0, slime=0]
- **r8** hp 147→147 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 220 · KILL support_tanuki,brute_oni | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=216 pick_loot] zone_03
_L12 · HP 52% · 3484g · stash 8/10 · enc_at_time=63_
- money +279g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=217 leave_zone]
_L12 · HP 52% · 3484g · stash 8/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=218 enter_town] (in shinto_town)
_L12 · HP 52% · 3484g · stash 8/10 · enc_at_time=63_
- enter town shinto_town

### [seq=219 shop_buy] (in shinto_town)
_L12 · HP 52% · 3454g · stash 9/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=220 shop_buy] (in shinto_town)
_L12 · HP 52% · 3424g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=221 leave_town]
_L12 · HP 52% · 3424g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=222 enter_zone] zone_03
_L12 · HP 52% · 3424g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=223 use_consumable] zone_03
_L12 · HP 52% · 3424g · stash 9/10 · enc_at_time=63_
- use minor_potion on recruit_einherjar_2449 (HP 102→152/264)

### [seq=224 use_consumable] zone_03
_L12 · HP 70% · 3424g · stash 8/10 · enc_at_time=63_
- use minor_potion on mc_einherjar (HP 147→197/281)

### [seq=225 leave_zone]
_L12 · HP 70% · 3424g · stash 8/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=226 enter_town] (in shinto_town)
_L12 · HP 70% · 3424g · stash 8/10 · enc_at_time=63_
- enter town shinto_town

### [seq=227 shop_buy] (in shinto_town)
_L12 · HP 70% · 3394g · stash 9/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=228 shop_buy] (in shinto_town)
_L12 · HP 70% · 3364g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=229 leave_town]
_L12 · HP 70% · 3364g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=230 enter_zone] zone_03
_L12 · HP 70% · 3364g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 63 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 147, took 41, healed 0_

- **r1** hp ?→169 ap 0 st=— | **SURVIVE** +bonus×4 | took 28 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=80, speeder_tengu=71, slime=105]
- **r2** hp 169→157 ap 1 st=— | **SURVIVE** +bonus×4 | took 12 · KILL speeder_tengu · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=9, speeder_tengu=0, slime=39]
- **r3** hp 157→157 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 147 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=231 pick_loot] zone_03
_L12 · HP 56% · 3521g · stash 10/10 · enc_at_time=64_
- money +157g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 64 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (2 rounds)
_dealt 216, took 25, healed 0_

- **r1** hp ?→133 ap 0 st=— | **SURVIVE** +bonus×4 | took 24 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=62, slime=66, slime=66]
- **r2** hp 133→133 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 216 · KILL slime,caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=232 pick_loot] zone_03
_L13 · HP 45% · 3676g · stash 10/10 · enc_at_time=65_
- money +155g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=233 use_consumable] zone_03
_L13 · HP 62% · 3676g · stash 9/10 · enc_at_time=65_
- use minor_potion on mc_einherjar (HP 133→183/296)

### [seq=234 use_consumable] zone_03
_L13 · HP 62% · 3676g · stash 8/10 · enc_at_time=65_
- use minor_potion on recruit_einherjar_2449 (HP 150→200/287)

### [seq=235 leave_zone]
_L13 · HP 62% · 3676g · stash 8/10 · enc_at_time=65_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=236 enter_town] (in shinto_town)
_L13 · HP 62% · 3676g · stash 8/10 · enc_at_time=65_
- enter town shinto_town

### [seq=237 shop_buy] (in shinto_town)
_L13 · HP 62% · 3646g · stash 9/10 · enc_at_time=65_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=238 shop_buy] (in shinto_town)
_L13 · HP 62% · 3616g · stash 10/10 · enc_at_time=65_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=239 leave_town]
_L13 · HP 62% · 3616g · stash 10/10 · enc_at_time=65_
- leave town shinto_town

### [seq=240 enter_zone] zone_03
_L13 · HP 62% · 3616g · stash 10/10 · enc_at_time=65_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 65 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 78, took 33, healed 0_

- **r1** hp ?→180 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [caster_kitsune=75, speeder_tengu=31, slime=81]
- **r2** hp 180→152 ap 1 st=— | **SURVIVE** +bonus×4 | took 28 · KILL speeder_tengu,caster_kitsune · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=0, speeder_tengu=0, slime=29]
- **r3** hp 152→152 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 78 · KILL slime | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=241 pick_loot] zone_03
_L13 · HP 51% · 3788g · stash 10/10 · enc_at_time=66_
- money +172g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=242 use_consumable] zone_03
_L13 · HP 68% · 3788g · stash 9/10 · enc_at_time=66_
- use minor_potion on mc_einherjar (HP 152→202/296)

### [seq=243 leave_zone]
_L13 · HP 68% · 3788g · stash 9/10 · enc_at_time=66_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=7, cleared=True

### [seq=244 enter_town] (in shinto_town)
_L13 · HP 68% · 3788g · stash 9/10 · enc_at_time=66_
- enter town shinto_town

### [seq=245 shop_buy] (in shinto_town)
_L13 · HP 68% · 3758g · stash 10/10 · enc_at_time=66_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=246 leave_town]
_L13 · HP 68% · 3758g · stash 10/10 · enc_at_time=66_
- leave town shinto_town

### [seq=247 enter_zone] zone_03
_L13 · HP 68% · 3758g · stash 10/10 · enc_at_time=66_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 66 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 77, took 35, healed 0_

- **r1** hp ?→179 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 · KILL bandit_slime | end [caster_kitsune=38, speeder_tengu=66, slime=99, bandit_slime=0]
- **r2** hp 179→167 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL speeder_tengu,caster_kitsune · +status(?→self) | end [caster_kitsune=0, speeder_tengu=0, slime=29, bandit_slime=0]
- **r3** hp 167→167 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 77 · KILL slime | end [caster_kitsune=0, speeder_tengu=0, slime=0, bandit_slime=0]

### [seq=248 pick_loot] zone_03
_L13 · HP 56% · 3875g · stash 10/10 · enc_at_time=67_
- money +206g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 67 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (2 rounds)
_dealt 230, took 26, healed 0_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=57, speeder_tengu=0, slime=99]
- **r2** hp 141→141 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 230 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=249 pick_loot] zone_03
_L13 · HP 48% · 3995g · stash 10/10 · enc_at_time=68_
- money +120g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=250 use_consumable] zone_03
_L13 · HP 65% · 3995g · stash 9/10 · enc_at_time=68_
- use minor_potion on mc_einherjar (HP 141→191/296)

### [seq=251 leave_zone]
_L13 · HP 65% · 3995g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=252 enter_town] (in shinto_town)
_L13 · HP 65% · 3995g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=253 shop_buy] (in shinto_town)
_L13 · HP 65% · 3965g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=254 leave_town]
_L13 · HP 65% · 3965g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=255 enter_zone] zone_03
_L13 · HP 65% · 3965g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 68 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 450, took 140, healed 50_

- **r1** hp ?→190 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [support_tanuki=158, brute_oni=358]
- **r2** hp 190→172 ap 1 st=— | **SURVIVE** +bonus×4 | took 18 | end [support_tanuki=86, brute_oni=340]
- **r3** hp 172→172 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=143, brute_oni=322]
- **r4** hp 172→152 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=39, brute_oni=173]
- **r5** hp 152→152 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 287 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=256 pick_loot] zone_03
_L13 · HP 51% · 4065g · stash 9/10 · enc_at_time=69_
- money +100g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=257 use_consumable] zone_03
_L13 · HP 51% · 4065g · stash 8/10 · enc_at_time=69_
- use minor_potion on recruit_einherjar_2449 (HP 147→197/287)

### [seq=258 leave_zone]
_L13 · HP 51% · 4065g · stash 8/10 · enc_at_time=69_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=259 enter_town] (in shinto_town)
_L13 · HP 51% · 4065g · stash 8/10 · enc_at_time=69_
- enter town shinto_town

### [seq=260 shop_buy] (in shinto_town)
_L13 · HP 51% · 4035g · stash 9/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=261 shop_buy] (in shinto_town)
_L13 · HP 51% · 4005g · stash 10/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=262 leave_town]
_L13 · HP 51% · 4005g · stash 10/10 · enc_at_time=69_
- leave town shinto_town

### [seq=263 enter_zone] zone_03
_L13 · HP 51% · 4005g · stash 10/10 · enc_at_time=69_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=264 use_consumable] zone_03
_L13 · HP 68% · 4005g · stash 9/10 · enc_at_time=69_
- use minor_potion on mc_einherjar (HP 152→202/296)

### [seq=265 leave_zone]
_L13 · HP 68% · 4005g · stash 9/10 · enc_at_time=69_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=266 enter_town] (in shinto_town)
_L13 · HP 68% · 4005g · stash 9/10 · enc_at_time=69_
- enter town shinto_town

### [seq=267 shop_buy] (in shinto_town)
_L13 · HP 68% · 3975g · stash 10/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=268 leave_town]
_L13 · HP 68% · 3975g · stash 10/10 · enc_at_time=69_
- leave town shinto_town

### [seq=269 enter_zone] zone_03
_L13 · HP 68% · 3975g · stash 10/10 · enc_at_time=69_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 69 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (4 rounds)
_dealt 311, took 64, healed 0_

- **r1** hp ?→202 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=126, brute_oni=292]
- **r2** hp 202→189 ap 1 st=— | **SURVIVE** +bonus×4 | took 13 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=126, brute_oni=246]
- **r3** hp 189→169 ap 2 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=52, brute_oni=246]
- **r4** hp 169→169 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 311 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=270 pick_loot] zone_03
_L13 · HP 57% · 4023g · stash 10/10 · enc_at_time=70_
- money +48g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=271 use_consumable] zone_03
_L13 · HP 57% · 4023g · stash 9/10 · enc_at_time=70_
- use minor_potion on recruit_einherjar_2449 (HP 166→216/310)

### [seq=272 leave_zone]
_L13 · HP 57% · 4023g · stash 9/10 · enc_at_time=70_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=11, cleared=True

### [seq=273 enter_town] (in shinto_town)
_L13 · HP 57% · 4023g · stash 9/10 · enc_at_time=70_
- enter town shinto_town

### [seq=274 shop_buy] (in shinto_town)
_L13 · HP 57% · 3993g · stash 10/10 · enc_at_time=70_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=275 leave_town]
_L13 · HP 57% · 3993g · stash 10/10 · enc_at_time=70_
- leave town shinto_town

### [seq=276 enter_zone] zone_03
_L13 · HP 57% · 3993g · stash 10/10 · enc_at_time=70_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 70 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (4 rounds)
_dealt 282, took 34, healed 0_

- **r1** hp ?→169 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=334, slime=95, slime=95]
- **r2** hp 169→167 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [brute_oni=307, slime=24, slime=24]
- **r3** hp 167→150 ap 2 st=— | **SURVIVE** +bonus×4 | took 17 · KILL slime,slime | end [brute_oni=265, slime=0, slime=0]
- **r4** hp 150→150 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 282 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=277 pick_loot] zone_03
_L13 · HP 51% · 4070g · stash 10/10 · enc_at_time=71_
- money +77g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=278 use_consumable] zone_03
_L13 · HP 68% · 4070g · stash 9/10 · enc_at_time=71_
- use minor_potion on mc_einherjar (HP 150→200/296)

### [seq=279 leave_zone]
_L13 · HP 68% · 4070g · stash 9/10 · enc_at_time=71_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=280 enter_town] (in shinto_town)
_L13 · HP 68% · 4070g · stash 9/10 · enc_at_time=71_
- enter town shinto_town

### [seq=281 shop_buy] (in shinto_town)
_L13 · HP 68% · 4040g · stash 10/10 · enc_at_time=71_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=282 leave_town]
_L13 · HP 68% · 4040g · stash 10/10 · enc_at_time=71_
- leave town shinto_town

### [seq=283 enter_zone] zone_03
_L13 · HP 68% · 4040g · stash 10/10 · enc_at_time=71_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 71 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (2 rounds)
_dealt 231, took 22, healed 0_

- **r1** hp ?→179 ap 0 st=— | **SURVIVE** +bonus×4 | took 21 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=38, slime=61, slime=76]
- **r2** hp 179→179 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 231 · KILL slime,caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=284 pick_loot] zone_03
_L13 · HP 60% · 4106g · stash 10/10 · enc_at_time=72_
- money +66g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 72 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 0, took 46, healed 0_

- **r1** hp ?→169 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · +status(?→self) | end [speeder_tengu=86, swime=62, swime=62]
- **r2** hp 169→136 ap 1 st=— | **SURVIVE** +bonus×4 | took 15 · KILL swime,swime · +status(?→self) | end [speeder_tengu=11, swime=0, swime=0]
- **r3** hp 136→135 ap 2 st=— | NORMAL thrust→speeder_tengu +bonus×4 | took 1 · KILL speeder_tengu | end [speeder_tengu=0, swime=0, swime=0]

### [seq=285 pick_loot] zone_03
_L13 · HP 46% · 4151g · stash 10/10 · enc_at_time=73_
- money +45g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=286 use_consumable] zone_03
_L13 · HP 62% · 4151g · stash 9/10 · enc_at_time=73_
- use minor_potion on mc_einherjar (HP 135→185/296)

### [seq=287 leave_zone]
_L13 · HP 62% · 4151g · stash 9/10 · enc_at_time=73_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=288 enter_town] (in shinto_town)
_L13 · HP 62% · 4151g · stash 9/10 · enc_at_time=73_
- enter town shinto_town

### [seq=289 shop_buy] (in shinto_town)
_L13 · HP 62% · 4121g · stash 10/10 · enc_at_time=73_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=290 leave_town]
_L13 · HP 62% · 4121g · stash 10/10 · enc_at_time=73_
- leave town shinto_town

### [seq=291 enter_zone] zone_03
_L13 · HP 62% · 4121g · stash 10/10 · enc_at_time=73_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 73 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (2 rounds)
_dealt 230, took 4, healed 0_

- **r1** hp ?→182 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL speeder_tengu · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=57, speeder_tengu=0, slime=95]
- **r2** hp 182→182 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 230 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=292 pick_loot] zone_03
_L13 · HP 61% · 4184g · stash 10/10 · enc_at_time=74_
- money +63g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 74 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 149, took 40, healed 0_

- **r1** hp ?→172 ap 0 st=— | **SURVIVE** +bonus×4 | took 10 · +status(?→self) | end [caster_kitsune=75, slime=99, slime=76]
- **r2** hp 172→144 ap 1 st=— | **SURVIVE** +bonus×4 | took 28 · KILL caster_kitsune · -status(Hex Disrupt→self) | end [caster_kitsune=0, slime=29, slime=19]
- **r3** hp 144→144 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 149 · KILL slime,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=293 pick_loot] zone_03
_L13 · HP 49% · 4254g · stash 10/10 · enc_at_time=75_
- money +70g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=294 use_consumable] zone_03
_L13 · HP 66% · 4254g · stash 9/10 · enc_at_time=75_
- use minor_potion on mc_einherjar (HP 144→194/296)

### [seq=295 leave_zone]
_L13 · HP 66% · 4254g · stash 9/10 · enc_at_time=75_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=296 enter_town] (in shinto_town)
_L13 · HP 66% · 4254g · stash 9/10 · enc_at_time=75_
- enter town shinto_town

### [seq=297 shop_buy] (in shinto_town)
_L13 · HP 66% · 4224g · stash 10/10 · enc_at_time=75_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=298 leave_town]
_L13 · HP 66% · 4224g · stash 10/10 · enc_at_time=75_
- leave town shinto_town

### [seq=299 enter_zone] zone_03
_L13 · HP 66% · 4224g · stash 10/10 · enc_at_time=75_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 75 [zone_03 idx=7] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (4 rounds)
_dealt 449, took 27, healed 50_

- **r1** hp ?→193 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Rally buff→brute_oni) | end [brute_oni=250, support_tanuki=230, slime=41, slime=56]
- **r2** hp 193→193 ap 1 st=— | **SURVIVE** +bonus×4 | KILL slime,slime | end [brute_oni=215, support_tanuki=173, slime=0, slime=0]
- **r3** hp 193→193 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=180, support_tanuki=230, slime=0, slime=0]
- **r4** hp 193→193 ap 3 st=— | **CHEAT(+3AP)** thrust→support_tanuki +cheat_extras×3 +bonus×4 | dealt 399 · KILL support_tanuki,brute_oni | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=300 pick_loot] zone_03
_L13 · HP 65% · 4252g · stash 9/10 · enc_at_time=76_
- money +28g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=301 leave_zone]
_L13 · HP 65% · 4252g · stash 9/10 · enc_at_time=76_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=17, cleared=True

### [seq=302 enter_town] (in shinto_town)
_L13 · HP 65% · 4252g · stash 9/10 · enc_at_time=76_
- enter town shinto_town

### [seq=303 shop_buy] (in shinto_town)
_L13 · HP 65% · 4222g · stash 10/10 · enc_at_time=76_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=304 leave_town]
_L13 · HP 65% · 4222g · stash 10/10 · enc_at_time=76_
- leave town shinto_town

### [seq=305 enter_zone] zone_03
_L13 · HP 65% · 4222g · stash 10/10 · enc_at_time=76_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 76 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 77, took 58, healed 0_

- **r1** hp ?→165 ap 0 st=— | **SURVIVE** +bonus×4 | took 28 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=75, slime=95, slime=41]
- **r2** hp 165→138 ap 1 st=— | **SURVIVE** +bonus×4 | took 27 · KILL caster_kitsune,slime | end [caster_kitsune=0, slime=39, slime=0]
- **r3** hp 138→138 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 77 · KILL slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=306 pick_loot] zone_03
_L13 · HP 47% · 4253g · stash 10/10 · enc_at_time=77_
- money +31g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=307 use_consumable] zone_03
_L13 · HP 64% · 4253g · stash 9/10 · enc_at_time=77_
- use minor_potion on mc_einherjar (HP 138→188/296)

### [seq=308 leave_zone]
_L13 · HP 64% · 4253g · stash 9/10 · enc_at_time=77_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=18, cleared=True

### [seq=309 enter_town] (in shinto_town)
_L13 · HP 64% · 4253g · stash 9/10 · enc_at_time=77_
- enter town shinto_town

### [seq=310 shop_buy] (in shinto_town)
_L13 · HP 64% · 4223g · stash 10/10 · enc_at_time=77_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=311 leave_town]
_L13 · HP 64% · 4223g · stash 10/10 · enc_at_time=77_
- leave town shinto_town

### [seq=312 enter_zone] zone_03
_L13 · HP 64% · 4223g · stash 10/10 · enc_at_time=77_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 77 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 300, took 94, healed 0_

- **r1** hp ?→188 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=173, brute_oni=307]
- **r2** hp 188→170 ap 1 st=— | **SURVIVE** +bonus×4 | took 18 | end [support_tanuki=101, brute_oni=280]
- **r3** hp 170→170 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [support_tanuki=101, brute_oni=253]
- **r4** hp 170→128 ap 3 st=— | **SURVIVE** +bonus×4 | took 42 | end [support_tanuki=29, brute_oni=211]
- **r5** hp 128→128 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 300 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=313 pick_loot] zone_03
_L13 · HP 43% · 4232g · stash 10/10 · enc_at_time=78_
- money +9g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=314 use_consumable] zone_03
_L13 · HP 60% · 4232g · stash 9/10 · enc_at_time=78_
- use minor_potion on mc_einherjar (HP 128→178/296)

### [seq=315 leave_zone]
_L13 · HP 60% · 4232g · stash 9/10 · enc_at_time=78_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=316 enter_town] (in shinto_town)
_L13 · HP 60% · 4232g · stash 9/10 · enc_at_time=78_
- enter town shinto_town

### [seq=317 shop_buy] (in shinto_town)
_L13 · HP 60% · 4202g · stash 10/10 · enc_at_time=78_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=318 leave_town]
_L13 · HP 60% · 4202g · stash 10/10 · enc_at_time=78_
- leave town shinto_town

### [seq=319 enter_zone] zone_03
_L13 · HP 60% · 4202g · stash 10/10 · enc_at_time=78_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 78 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 504, took 117, healed 100_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=230, brute_oni=292]
- **r2** hp 161→161 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=230, brute_oni=307]
- **r3** hp 161→177 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 192 · took 34 | end [support_tanuki=101, brute_oni=145]
- **r4** hp 177→177 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=44, brute_oni=40]
- **r5** hp 177→177 ap 1 st=— | NORMAL thrust→support_tanuki +bonus×4 | dealt 120 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=320 pick_loot] zone_03
_L13 · HP 60% · 4209g · stash 8/10 · enc_at_time=79_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=321 leave_zone]
_L13 · HP 60% · 4209g · stash 8/10 · enc_at_time=79_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=322 enter_town] (in shinto_town)
_L13 · HP 60% · 4209g · stash 8/10 · enc_at_time=79_
- enter town shinto_town

### [seq=323 shop_buy] (in shinto_town)
_L13 · HP 60% · 4179g · stash 9/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=324 shop_buy] (in shinto_town)
_L13 · HP 60% · 4149g · stash 10/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=325 leave_town]
_L13 · HP 60% · 4149g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=326 enter_zone] zone_04
_L13 · HP 60% · 4149g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=327 use_consumable] zone_04
_L13 · HP 60% · 4149g · stash 9/10 · enc_at_time=79_
- use minor_potion on recruit_einherjar_2449 (HP 166→216/310)

### [seq=328 leave_zone]
_L13 · HP 60% · 4149g · stash 9/10 · enc_at_time=79_
- leave zone_04: reason=sim_post_zone, enc_idx=0, overstay=0, cleared=False

### [seq=329 enter_town] (in shinto_town)
_L13 · HP 60% · 4149g · stash 9/10 · enc_at_time=79_
- enter town shinto_town

### [seq=330 shop_buy] (in shinto_town)
_L13 · HP 60% · 4119g · stash 10/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=331 leave_town]
_L13 · HP 60% · 4119g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=332 enter_zone] zone_04
_L13 · HP 60% · 4119g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 79 [zone_04 idx=0] vs split_slime, split_slime, slime → **VICTORY** (3 rounds)
_dealt 490, took 6, healed 0_

- **r1** hp ?→174 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=81, split_slime=98, slime=99]
- **r2** hp 174→171 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [split_slime=9, split_slime=27, slime=29]
- **r3** hp 171→171 ap 2 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 232 · KILL slime,mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=333 pick_loot] zone_04
_L14 · HP 55% · 4517g · stash 10/10 · enc_at_time=80_
- money +398g, offered=['minor_potion'], **selected**=[], skipped=['minor_potion'], discarded_stash=[]

### [seq=334 use_consumable] zone_04
_L14 · HP 71% · 4517g · stash 9/10 · enc_at_time=80_
- use minor_potion on mc_einherjar (HP 171→221/312)

### [seq=335 leave_zone]
_L14 · HP 71% · 4517g · stash 9/10 · enc_at_time=80_
- leave zone_04: reason=sim_post_zone, enc_idx=1, overstay=0, cleared=False

### [seq=336 enter_town] (in shinto_town)
_L14 · HP 71% · 4517g · stash 9/10 · enc_at_time=80_
- enter town shinto_town

### [seq=337 shop_buy] (in shinto_town)
_L14 · HP 71% · 4487g · stash 10/10 · enc_at_time=80_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=338 leave_town]
_L14 · HP 71% · 4487g · stash 10/10 · enc_at_time=80_
- leave town shinto_town

### [seq=339 enter_zone] zone_04
_L14 · HP 71% · 4487g · stash 10/10 · enc_at_time=80_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 80 [zone_04 idx=1] vs brute_oni, mystic_slime → **VICTORY** (4 rounds)
_dealt 319, took 112, healed 50_

- **r1** hp ?→195 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 | end [brute_oni=348, mystic_slime=59]
- **r2** hp 195→169 ap 1 st=— | **SURVIVE** +bonus×4 | took 26 · KILL mystic_slime | end [brute_oni=320, mystic_slime=0]
- **r3** hp 169→181 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 167 · took 38 | end [brute_oni=110, mystic_slime=0]
- **r4** hp 181→181 ap 0 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 105 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=340 pick_loot] zone_04
_L14 · HP 58% · 4623g · stash 10/10 · enc_at_time=81_
- money +136g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=341 recruit_accept] zone_04
_L14 · HP 58% · 4623g · stash 10/10 · enc_at_time=81_
- recruit_accept: Onmyoji Recruit (onmyoji L8) id=recruit_onmyoji_5132

### ENC 81 [zone_04 idx=2] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (6 rounds)
_dealt 609, took 203, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→181 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_einherjar), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=187, chunky_slime=230, chunky_slime=280]
- **r2** hp 181→180 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→recruit_einherjar), enemy_status(?→recruit_onmyoji), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=187, chunky_slime=230, chunky_slime=159]
- **r3** hp 180→180 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=187, chunky_slime=230, chunky_slime=126]
- **r4** hp 180→180 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(Taunted→recruit_einherjar), +status(Taunted→self) | end [caster_kitsune=187, chunky_slime=230, chunky_slime=126]
- **r5** hp 180→111 ap 3 st=Taunted | **CHEAT(+3AP)** brace_strike→chunky_slime +cheat_extras×3 +bonus×4 | dealt 328 · took 69 · KILL chunky_slime,chunky_slime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→recruit_einherjar), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=27, chunky_slime=0, chunky_slime=0]
- **r6** hp 111→111 ap 0 st=— | NORMAL thrust→caster_kitsune +bonus×4 | dealt 85 · KILL caster_kitsune | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=342 pick_loot] zone_04
_L14 · HP 36% · 4859g · stash 10/10 · enc_at_time=82_
- money +236g, offered=['minor_potion', 'warden_tonic'], **selected**=[], skipped=['minor_potion', 'warden_tonic'], discarded_stash=[]

### [seq=343 use_consumable] zone_04
_L14 · HP 52% · 4859g · stash 9/10 · enc_at_time=82_
- use minor_potion on mc_einherjar (HP 111→161/312)

### [seq=344 use_consumable] zone_04
_L14 · HP 52% · 4859g · stash 8/10 · enc_at_time=82_
- use minor_potion on recruit_einherjar_2449 (HP 192→242/356)

### [seq=345 leave_zone]
_L14 · HP 52% · 4859g · stash 8/10 · enc_at_time=82_
- leave zone_04: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=346 enter_town] (in shinto_town)
_L14 · HP 52% · 4859g · stash 8/10 · enc_at_time=82_
- enter town shinto_town

### [seq=347 shop_buy] (in shinto_town)
_L14 · HP 52% · 4829g · stash 9/10 · enc_at_time=82_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=348 shop_buy] (in shinto_town)
_L14 · HP 52% · 4799g · stash 10/10 · enc_at_time=82_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=349 leave_town]
_L14 · HP 52% · 4799g · stash 10/10 · enc_at_time=82_
- leave town shinto_town

### [seq=350 enter_zone] zone_04
_L14 · HP 52% · 4799g · stash 10/10 · enc_at_time=82_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=351 use_consumable] zone_04
_L14 · HP 68% · 4799g · stash 9/10 · enc_at_time=82_
- use minor_potion on mc_einherjar (HP 161→211/312)

### [seq=352 leave_zone]
_L14 · HP 68% · 4799g · stash 9/10 · enc_at_time=82_
- leave zone_04: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=353 enter_town] (in shinto_town)
_L14 · HP 68% · 4799g · stash 9/10 · enc_at_time=82_
- enter town shinto_town

### [seq=354 shop_buy] (in shinto_town)
_L14 · HP 68% · 4769g · stash 10/10 · enc_at_time=82_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=355 leave_town]
_L14 · HP 68% · 4769g · stash 10/10 · enc_at_time=82_
- leave town shinto_town

### [seq=356 enter_zone] zone_04
_L14 · HP 68% · 4769g · stash 10/10 · enc_at_time=82_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 82 [zone_04 idx=3] vs split_slime, speeder_tengu, slime, bandit_slime → **VICTORY** (4 rounds)
_dealt 408, took 146, healed 50_

- **r1** hp ?→197 ap 0 st=— | **SURVIVE** +bonus×4 | took 4 · KILL bandit_slime · enemy_status(?→recruit_onmyoji), +status(?→self) | end [split_slime=76, speeder_tengu=101, slime=104, bandit_slime=0]
- **r2** hp 197→186 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=76, speeder_tengu=21, slime=104, bandit_slime=0]
- **r3** hp 186→165 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu · enemy_status(?→recruit_onmyoji), +status(?→self), enemy_status(Brace Strike DEF buff→slime), -status(Searing Edge DOT→self) | end [split_slime=9, speeder_tengu=0, slime=95, bandit_slime=0]
- **r4** hp 165→165 ap 3 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 247 · KILL slime,mini_slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, bandit_slime=0, mini_slime=0, mini_slime=0]

### [seq=357 pick_loot] zone_04
_L15 · HP 50% · 5131g · stash 9/10 · enc_at_time=83_
- money +612g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=358 use_consumable] zone_04
_L15 · HP 66% · 5131g · stash 8/10 · enc_at_time=83_
- use minor_potion on mc_einherjar (HP 165→215/327)

### [seq=359 leave_zone]
_L15 · HP 66% · 5131g · stash 8/10 · enc_at_time=83_
- leave zone_04: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=360 enter_town] (in shinto_town)
_L15 · HP 66% · 5131g · stash 8/10 · enc_at_time=83_
- enter town shinto_town

### [seq=361 shop_buy] (in shinto_town)
_L15 · HP 66% · 5101g · stash 9/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=362 shop_buy] (in shinto_town)
_L15 · HP 66% · 5071g · stash 10/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=363 leave_town]
_L15 · HP 66% · 5071g · stash 10/10 · enc_at_time=83_
- leave town shinto_town

### [seq=364 enter_zone] zone_04
_L15 · HP 66% · 5071g · stash 10/10 · enc_at_time=83_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=365 use_consumable] zone_04
_L15 · HP 66% · 5071g · stash 9/10 · enc_at_time=83_
- use minor_potion on recruit_onmyoji_5132 (HP 49→97/97)

### [seq=366 leave_zone]
_L15 · HP 66% · 5071g · stash 9/10 · enc_at_time=83_
- leave zone_04: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=367 enter_town] (in shinto_town)
_L15 · HP 66% · 5071g · stash 9/10 · enc_at_time=83_
- enter town shinto_town

### [seq=368 shop_buy] (in shinto_town)
_L15 · HP 66% · 5041g · stash 10/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=369 leave_town]
_L15 · HP 66% · 5041g · stash 10/10 · enc_at_time=83_
- leave town shinto_town

### [seq=370 enter_zone] zone_04
_L15 · HP 66% · 5041g · stash 10/10 · enc_at_time=83_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 83 [zone_04 idx=4] vs support_tanuki, swime, brute_oni, bandit_slime → **VICTORY** (9 rounds)
_dealt 525, took 457, healed 100, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→165 ap 0 st=— | **SURVIVE** +bonus×4 | took 50 · KILL bandit_slime | end [support_tanuki=174, swime=84, brute_oni=460, bandit_slime=0]
- **r2** hp 165→117 ap 1 st=— | **SURVIVE** +bonus×4 | took 48 · KILL swime | end [support_tanuki=237, swime=0, brute_oni=460, bandit_slime=0]
- **r3** hp 117→115 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 207 · took 52 | end [support_tanuki=156, swime=0, brute_oni=292, bandit_slime=0]
- **r4** hp 115→115 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=219, swime=0, brute_oni=267, bandit_slime=0]
- **r5** hp 115→115 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(Rally buff→brute_oni) | end [support_tanuki=219, swime=0, brute_oni=267, bandit_slime=0]
- **r6** hp 115→81 ap 2 st=— | **SURVIVE** +bonus×4 | took 34 | end [support_tanuki=219, swime=0, brute_oni=290, bandit_slime=0]
- **r7** hp 81→28 ap 3 st=— | **SURVIVE** +bonus×4 | took 53 | end [support_tanuki=138, swime=0, brute_oni=250, bandit_slime=0]
- **r8** hp 28→2 ap 3 st=— | **SURVIVE** +bonus×4 | took 26 | end [support_tanuki=72, swime=0, brute_oni=210, bandit_slime=0]
- **r9** hp 2→2 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 316 · KILL support_tanuki,brute_oni | end [support_tanuki=0, swime=0, brute_oni=0, bandit_slime=0]

### [seq=371 pick_loot] zone_04
_L15 · HP 1% · 5271g · stash 9/10 · enc_at_time=84_
- money +480g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=372 use_consumable] zone_04
_L15 · HP 16% · 5271g · stash 8/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 2→52/327)

### [seq=373 leave_zone]
_L15 · HP 16% · 5271g · stash 8/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=374 enter_town] (in shinto_town)
_L15 · HP 16% · 5271g · stash 8/10 · enc_at_time=84_
- enter town shinto_town

### [seq=375 shop_buy] (in shinto_town)
_L15 · HP 16% · 5241g · stash 9/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=376 shop_buy] (in shinto_town)
_L15 · HP 16% · 5211g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=377 leave_town]
_L15 · HP 16% · 5211g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=378 enter_zone] zone_04
_L15 · HP 16% · 5211g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=379 use_consumable] zone_04
_L15 · HP 31% · 5211g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 52→102/327)

### [seq=380 use_consumable] zone_04
_L15 · HP 31% · 5211g · stash 8/10 · enc_at_time=84_
- use minor_potion on recruit_einherjar_2449 (HP 195→245/379)

### [seq=381 leave_zone]
_L15 · HP 31% · 5211g · stash 8/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=382 enter_town] (in shinto_town)
_L15 · HP 31% · 5211g · stash 8/10 · enc_at_time=84_
- enter town shinto_town

### [seq=383 shop_buy] (in shinto_town)
_L15 · HP 31% · 5181g · stash 9/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=384 shop_buy] (in shinto_town)
_L15 · HP 31% · 5151g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=385 leave_town]
_L15 · HP 31% · 5151g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=386 enter_zone] zone_04
_L15 · HP 31% · 5151g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=387 use_consumable] zone_04
_L15 · HP 46% · 5151g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 102→152/327)

### [seq=388 leave_zone]
_L15 · HP 46% · 5151g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=389 enter_town] (in shinto_town)
_L15 · HP 46% · 5151g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=390 shop_buy] (in shinto_town)
_L15 · HP 46% · 5121g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=391 leave_town]
_L15 · HP 46% · 5121g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=392 enter_zone] zone_04
_L15 · HP 46% · 5121g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=393 use_consumable] zone_04
_L15 · HP 62% · 5121g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 152→202/327)

### [seq=394 leave_zone]
_L15 · HP 62% · 5121g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=395 enter_town] (in shinto_town)
_L15 · HP 62% · 5121g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=396 shop_buy] (in shinto_town)
_L15 · HP 62% · 5091g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=397 leave_town]
_L15 · HP 62% · 5091g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=398 enter_zone] zone_04
_L15 · HP 62% · 5091g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 84 [zone_04 idx=5] vs brute_oni, caster_kitsune, split_slime → **VICTORY** (7 rounds)
_dealt 481, took 275, healed 100_

- **r1** hp ?→183 ap 0 st=— | **SURVIVE** +bonus×4 | took 19 · enemy_status(?→recruit_onmyoji), +status(?→self) | end [brute_oni=476, caster_kitsune=140, split_slime=25]
- **r2** hp 183→166 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL split_slime · enemy_status(?→recruit_onmyoji), +status(?→self), -status(Hex Disrupt→self) | end [brute_oni=476, caster_kitsune=57, split_slime=0]
- **r3** hp 166→216 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 203 · KILL caster_kitsune · -status(Hex Disrupt→self) | end [brute_oni=328, caster_kitsune=0, split_slime=0]
- **r4** hp 216→216 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=328, caster_kitsune=0, split_slime=0]
- **r5** hp 216→187 ap 1 st=— | **SURVIVE** +bonus×4 | took 29 | end [brute_oni=292, caster_kitsune=0, split_slime=0]
- **r6** hp 187→158 ap 2 st=— | **SURVIVE** +bonus×4 | took 29 | end [brute_oni=256, caster_kitsune=0, split_slime=0]
- **r7** hp 158→158 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 276 · KILL brute_oni | end [brute_oni=0, caster_kitsune=0, split_slime=0]

### [seq=399 pick_loot] zone_04
_L16 · HP 46% · 5300g · stash 9/10 · enc_at_time=85_
- money +209g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=400 use_consumable] zone_04
_L16 · HP 46% · 5300g · stash 8/10 · enc_at_time=85_
- use minor_potion on recruit_onmyoji_5132 (HP 3→53/97)

### [seq=401 leave_zone]
_L16 · HP 46% · 5300g · stash 8/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=402 enter_town] (in shinto_town)
_L16 · HP 46% · 5300g · stash 8/10 · enc_at_time=85_
- enter town shinto_town

### [seq=403 shop_buy] (in shinto_town)
_L16 · HP 46% · 5270g · stash 9/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=404 shop_buy] (in shinto_town)
_L16 · HP 46% · 5240g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=405 leave_town]
_L16 · HP 46% · 5240g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=406 enter_zone] zone_04
_L16 · HP 46% · 5240g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=407 use_consumable] zone_04
_L16 · HP 61% · 5240g · stash 9/10 · enc_at_time=85_
- use minor_potion on mc_einherjar (HP 158→208/343)

### [seq=408 use_consumable] zone_04
_L16 · HP 61% · 5240g · stash 8/10 · enc_at_time=85_
- use minor_potion on recruit_onmyoji_5132 (HP 53→97/97)

### [seq=409 leave_zone]
_L16 · HP 61% · 5240g · stash 8/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=410 enter_town] (in shinto_town)
_L16 · HP 61% · 5240g · stash 8/10 · enc_at_time=85_
- enter town shinto_town

### [seq=411 shop_buy] (in shinto_town)
_L16 · HP 61% · 5210g · stash 9/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=412 shop_buy] (in shinto_town)
_L16 · HP 61% · 5180g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=413 leave_town]
_L16 · HP 61% · 5180g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=414 enter_zone] zone_04
_L16 · HP 61% · 5180g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=415 use_consumable] zone_04
_L16 · HP 61% · 5180g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_einherjar_2449 (HP 208→258/379)

### [seq=416 leave_zone]
_L16 · HP 61% · 5180g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=417 enter_town] (in shinto_town)
_L16 · HP 61% · 5180g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=418 shop_buy] (in shinto_town)
_L16 · HP 61% · 5150g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=419 leave_town]
_L16 · HP 61% · 5150g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=420 enter_zone] zone_04
_L16 · HP 61% · 5150g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 85 [zone_04 idx=6] vs kappa → **VICTORY** (18 rounds)
_dealt 555, took 647, healed 100, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→208 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=671]
- **r2** hp 208→208 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji | end [kappa=671]
- **r3** hp 208→208 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=671]
- **r4** hp 208→154 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=638]
- **r5** hp 154→204 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 180 | end [kappa=450]
- **r6** hp 204→204 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=314]
- **r7** hp 204→150 ap 1 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=298]
- **r8** hp 150→149 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [kappa=283]
- **r9** hp 149→148 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 | end [kappa=269]
- **r10** hp 148→148 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=289]
- **r11** hp 148→94 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=275]
- **r12** hp 94→94 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=276]
- **r13** hp 94→94 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=277]
- **r14** hp 94→93 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 | end [kappa=263]
- **r15** hp 93→57 ap 3 st=— | **SURVIVE** +bonus×4 | took 36 | end [kappa=250]
- **r16** hp 57→57 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=253]
- **r17** hp 57→3 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=240]
- **r18** hp 3→3 ap 3 st=— | **CHEAT(+3AP)** thrust→kappa +cheat_extras×3 +bonus×4 | dealt 240 · KILL kappa | end [kappa=0]

### [seq=421 pick_loot] zone_04
_L16 · HP 1% · 5590g · stash 10/10 · enc_at_time=86_
- money +440g, offered=['minor_potion', 'cast_heavy_strike', 'cast_quick_strike', 'spd_to_mag_charm'], **selected**=['minor_potion', 'cast_heavy_strike'], skipped=['cast_quick_strike', 'spd_to_mag_charm'], discarded_stash=[]

### [seq=422 use_consumable] zone_04
_L16 · HP 15% · 5590g · stash 9/10 · enc_at_time=86_
- use minor_potion on mc_einherjar (HP 3→53/343)

### [seq=423 leave_zone]
_L16 · HP 15% · 5590g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=424 enter_town] (in shinto_town)
_L16 · HP 15% · 5590g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=425 shop_buy] (in shinto_town)
_L16 · HP 15% · 5560g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=426 leave_town]
_L16 · HP 15% · 5560g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=427 enter_zone] zone_04
_L16 · HP 15% · 5560g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=428 use_consumable] zone_04
_L16 · HP 15% · 5560g · stash 9/10 · enc_at_time=86_
- use minor_potion on recruit_einherjar_2449 (HP 13→63/379)

### [seq=429 leave_zone]
_L16 · HP 15% · 5560g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=430 enter_town] (in shinto_town)
_L16 · HP 15% · 5560g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=431 shop_buy] (in shinto_town)
_L16 · HP 15% · 5530g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=432 leave_town]
_L16 · HP 15% · 5530g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=433 enter_zone] zone_04
_L16 · HP 15% · 5530g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=434 use_consumable] zone_04
_L16 · HP 30% · 5530g · stash 9/10 · enc_at_time=86_
- use minor_potion on mc_einherjar (HP 53→103/343)

### [seq=435 leave_zone]
_L16 · HP 30% · 5530g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=436 enter_town] (in shinto_town)
_L16 · HP 30% · 5530g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=437 shop_buy] (in shinto_town)
_L16 · HP 30% · 5500g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=438 leave_town]
_L16 · HP 30% · 5500g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=439 enter_zone] zone_04
_L16 · HP 30% · 5500g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=440 use_consumable] zone_04
_L16 · HP 30% · 5500g · stash 9/10 · enc_at_time=86_
- use minor_potion on recruit_einherjar_2449 (HP 63→113/379)

### [seq=441 leave_zone]
_L16 · HP 30% · 5500g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=442 enter_town] (in shinto_town)
_L16 · HP 30% · 5500g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=443 shop_buy] (in shinto_town)
_L16 · HP 30% · 5470g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=444 leave_town]
_L16 · HP 30% · 5470g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=445 enter_zone] zone_04
_L16 · HP 30% · 5470g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=446 use_consumable] zone_04
_L16 · HP 30% · 5470g · stash 9/10 · enc_at_time=86_
- use minor_potion on recruit_einherjar_2449 (HP 113→163/379)

### [seq=447 leave_zone]
_L16 · HP 30% · 5470g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=448 enter_town] (in shinto_town)
_L16 · HP 30% · 5470g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=449 shop_buy] (in shinto_town)
_L16 · HP 30% · 5440g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=450 leave_town]
_L16 · HP 30% · 5440g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=451 enter_zone] zone_04
_L16 · HP 30% · 5440g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=452 use_consumable] zone_04
_L16 · HP 45% · 5440g · stash 9/10 · enc_at_time=86_
- use minor_potion on mc_einherjar (HP 103→153/343)

### [seq=453 leave_zone]
_L16 · HP 45% · 5440g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=454 enter_town] (in shinto_town)
_L16 · HP 45% · 5440g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=455 shop_buy] (in shinto_town)
_L16 · HP 45% · 5410g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=456 leave_town]
_L16 · HP 45% · 5410g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=457 enter_zone] zone_04
_L16 · HP 45% · 5410g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=458 use_consumable] zone_04
_L16 · HP 45% · 5410g · stash 9/10 · enc_at_time=86_
- use minor_potion on recruit_einherjar_2449 (HP 163→213/379)

### [seq=459 leave_zone]
_L16 · HP 45% · 5410g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=460 enter_town] (in shinto_town)
_L16 · HP 45% · 5410g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=461 shop_buy] (in shinto_town)
_L16 · HP 45% · 5380g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=462 leave_town]
_L16 · HP 45% · 5380g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=463 enter_zone] zone_04
_L16 · HP 45% · 5380g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=464 use_consumable] zone_04
_L16 · HP 59% · 5380g · stash 9/10 · enc_at_time=86_
- use minor_potion on mc_einherjar (HP 153→203/343)

### [seq=465 leave_zone]
_L16 · HP 59% · 5380g · stash 9/10 · enc_at_time=86_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=466 enter_town] (in shinto_town)
_L16 · HP 59% · 5380g · stash 9/10 · enc_at_time=86_
- enter town shinto_town

### [seq=467 shop_buy] (in shinto_town)
_L16 · HP 59% · 5350g · stash 10/10 · enc_at_time=86_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=468 leave_town]
_L16 · HP 59% · 5350g · stash 10/10 · enc_at_time=86_
- leave town shinto_town

### [seq=469 enter_zone] zone_04
_L16 · HP 59% · 5350g · stash 10/10 · enc_at_time=86_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 86 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (5 rounds)
_dealt 500, took 146, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→203 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=418, mystic_slime=140]
- **r2** hp 203→203 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(?→recruit_onmyoji) | end [brute_oni=418, mystic_slime=140]
- **r3** hp 203→195 ap 2 st=— | **SURVIVE** +bonus×4 | took 8 · +status(?→self) | end [brute_oni=384, mystic_slime=49]
- **r4** hp 195→195 ap 3 st=— | **SURVIVE** +bonus×4 | KILL mystic_slime · -status(Hex Disrupt→self) | end [brute_oni=219, mystic_slime=0]
- **r5** hp 195→195 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 259 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=470 pick_loot] zone_04
_L16 · HP 57% · 5564g · stash 9/10 · enc_at_time=87_
- money +214g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=471 leave_zone]
_L16 · HP 57% · 5564g · stash 9/10 · enc_at_time=87_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=1, cleared=True

### [seq=472 enter_town] (in shinto_town)
_L16 · HP 57% · 5564g · stash 9/10 · enc_at_time=87_
- enter town shinto_town

### [seq=473 shop_buy] (in shinto_town)
_L16 · HP 57% · 5534g · stash 10/10 · enc_at_time=87_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=474 leave_town]
_L16 · HP 57% · 5534g · stash 10/10 · enc_at_time=87_
- leave town shinto_town

### [seq=475 enter_zone] zone_04
_L16 · HP 57% · 5534g · stash 10/10 · enc_at_time=87_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 87 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (4 rounds)
_dealt 458, took 11, healed 0_

- **r1** hp ?→194 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=81, split_slime=48, slime=169]
- **r2** hp 194→193 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL split_slime | end [split_slime=9, split_slime=0, slime=169]
- **r3** hp 193→193 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 270 · KILL slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=42, mini_slime=42]
- **r4** hp 193→193 ap 1 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 188 · KILL mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=476 pick_loot] zone_04
_L16 · HP 56% · 5677g · stash 10/10 · enc_at_time=88_
- money +143g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 88 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (4 rounds)
_dealt 711, took 12, healed 0_

- **r1** hp ?→192 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=169, split_slime=153, slime=103]
- **r2** hp 192→191 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=93, split_slime=153, slime=19]
- **r3** hp 191→190 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=7, split_slime=153, slime=19]
- **r4** hp 190→190 ap 3 st=— | **CHEAT(+3AP)** thrust→split_slime +cheat_extras×3 +bonus×4 | dealt 369 · KILL slime,mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=477 pick_loot] zone_04
_L16 · HP 55% · 6171g · stash 10/10 · enc_at_time=89_
- money +494g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 89 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (3 rounds)
_dealt 604, took 5, healed 0_

- **r1** hp ?→187 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [split_slime=43, split_slime=25, slime=84]
- **r2** hp 187→187 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 268 · KILL slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=50, mini_slime=50, mini_slime=54, mini_slime=54]
- **r3** hp 187→187 ap 0 st=— | **SURVIVE** +bonus×4 | KILL mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=478 pick_loot] zone_04
_L16 · HP 55% · 6600g · stash 10/10 · enc_at_time=90_
- money +429g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=479 use_consumable] zone_04
_L16 · HP 69% · 6600g · stash 9/10 · enc_at_time=90_
- use minor_potion on mc_einherjar (HP 187→237/343)

### [seq=480 leave_zone]
_L16 · HP 69% · 6600g · stash 9/10 · enc_at_time=90_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=481 enter_town] (in shinto_town)
_L16 · HP 69% · 6600g · stash 9/10 · enc_at_time=90_
- enter town shinto_town

### [seq=482 shop_buy] (in shinto_town)
_L16 · HP 69% · 6570g · stash 10/10 · enc_at_time=90_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=483 leave_town]
_L16 · HP 69% · 6570g · stash 10/10 · enc_at_time=90_
- leave town shinto_town

### [seq=484 enter_zone] zone_04
_L16 · HP 69% · 6570g · stash 10/10 · enc_at_time=90_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 90 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (7 rounds)
_dealt 405, took 204, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→237 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=418, mystic_slime=170]
- **r2** hp 237→237 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=374, mystic_slime=170]
- **r3** hp 237→236 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(?→recruit_onmyoji) | end [brute_oni=323, mystic_slime=162]
- **r4** hp 236→216 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 · enemy_status(?→recruit_onmyoji) | end [brute_oni=274, mystic_slime=162]
- **r5** hp 216→216 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=230, mystic_slime=162]
- **r6** hp 216→196 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 · KILL recruit_onmyoji | end [brute_oni=181, mystic_slime=162]
- **r7** hp 196→196 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 395 · KILL brute_oni,mystic_slime | end [brute_oni=0, mystic_slime=0]

### [seq=485 pick_loot] zone_04
_L16 · HP 57% · 6682g · stash 9/10 · enc_at_time=91_
- money +112g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=486 leave_zone]
_L16 · HP 57% · 6682g · stash 9/10 · enc_at_time=91_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=487 enter_town] (in shinto_town)
_L16 · HP 57% · 6682g · stash 9/10 · enc_at_time=91_
- enter town shinto_town

### [seq=488 shop_buy] (in shinto_town)
_L16 · HP 57% · 6652g · stash 10/10 · enc_at_time=91_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=489 leave_town]
_L16 · HP 57% · 6652g · stash 10/10 · enc_at_time=91_
- leave town shinto_town

### [seq=490 enter_zone] zone_04
_L16 · HP 57% · 6652g · stash 10/10 · enc_at_time=91_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 91 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (5 rounds)
_dealt 507, took 169, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→196 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=466, mystic_slime=140]
- **r2** hp 196→196 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=466, mystic_slime=140]
- **r3** hp 196→196 ap 2 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji | end [brute_oni=310, mystic_slime=54]
- **r4** hp 196→171 ap 3 st=— | **SURVIVE** +bonus×4 | took 25 · KILL mystic_slime | end [brute_oni=274, mystic_slime=0]
- **r5** hp 171→171 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 301 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=491 pick_loot] zone_04
_L16 · HP 50% · 6811g · stash 9/10 · enc_at_time=92_
- money +159g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=492 leave_zone]
_L16 · HP 50% · 6811g · stash 9/10 · enc_at_time=92_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=493 enter_town] (in shinto_town)
_L16 · HP 50% · 6811g · stash 9/10 · enc_at_time=92_
- enter town shinto_town

### [seq=494 shop_buy] (in shinto_town)
_L16 · HP 50% · 6781g · stash 10/10 · enc_at_time=92_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=495 leave_town]
_L16 · HP 50% · 6781g · stash 10/10 · enc_at_time=92_
- leave town shinto_town

### [seq=496 enter_zone] zone_04
_L16 · HP 50% · 6781g · stash 10/10 · enc_at_time=92_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=497 use_consumable] zone_04
_L16 · HP 64% · 6781g · stash 9/10 · enc_at_time=92_
- use minor_potion on mc_einherjar (HP 171→221/343)

### [seq=498 leave_zone]
_L16 · HP 64% · 6781g · stash 9/10 · enc_at_time=92_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=499 enter_town] (in shinto_town)
_L16 · HP 64% · 6781g · stash 9/10 · enc_at_time=92_
- enter town shinto_town

### [seq=500 shop_buy] (in shinto_town)
_L16 · HP 64% · 6751g · stash 10/10 · enc_at_time=92_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=501 leave_town]
_L16 · HP 64% · 6751g · stash 10/10 · enc_at_time=92_
- leave town shinto_town

### [seq=502 enter_zone] zone_04
_L16 · HP 64% · 6751g · stash 10/10 · enc_at_time=92_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 92 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (3 rounds)
_dealt 89, took 12, healed 0_

- **r1** hp ?→218 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=100, split_slime=33, slime=147]
- **r2** hp 218→214 ap 1 st=— | **SURVIVE** +bonus×4 | took 4 · KILL split_slime,split_slime · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=0, split_slime=0, slime=66]
- **r3** hp 214→214 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 89 · KILL slime | end [split_slime=0, split_slime=0, slime=0]

### [seq=503 pick_loot] zone_04
_L17 · HP 60% · 6851g · stash 10/10 · enc_at_time=93_
- money +100g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 93 [zone_04 idx=7] vs support_tanuki, swime, brute_oni → **VICTORY** (4 rounds)
_dealt 462, took 141, healed 50_

- **r1** hp ?→197 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 | end [support_tanuki=138, swime=100, brute_oni=376]
- **r2** hp 197→170 ap 1 st=— | **SURVIVE** +bonus×4 | took 27 | end [support_tanuki=138, swime=65, brute_oni=318]
- **r3** hp 170→189 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 246 · took 31 · KILL swime | end [support_tanuki=56, swime=0, brute_oni=106]
- **r4** hp 189→189 ap 0 st=— | **SURVIVE** +bonus×4 | KILL brute_oni,support_tanuki | end [support_tanuki=0, swime=0, brute_oni=0]

### [seq=504 pick_loot] zone_04
_L17 · HP 53% · 7020g · stash 9/10 · enc_at_time=94_
- money +169g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=505 leave_zone]
_L17 · HP 53% · 7020g · stash 9/10 · enc_at_time=94_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=506 enter_town] (in shinto_town)
_L17 · HP 53% · 7020g · stash 9/10 · enc_at_time=94_
- enter town shinto_town

### [seq=507 shop_buy] (in shinto_town)
_L17 · HP 53% · 6990g · stash 10/10 · enc_at_time=94_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=508 leave_town]
_L17 · HP 53% · 6990g · stash 10/10 · enc_at_time=94_
- leave town shinto_town

### [seq=509 enter_zone] zone_04
_L17 · HP 53% · 6990g · stash 10/10 · enc_at_time=94_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=510 use_consumable] zone_04
_L17 · HP 53% · 6990g · stash 9/10 · enc_at_time=94_
- use minor_potion on recruit_onmyoji_5132 (HP 39→89/97)

### [seq=511 leave_zone]
_L17 · HP 53% · 6990g · stash 9/10 · enc_at_time=94_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=512 enter_town] (in shinto_town)
_L17 · HP 53% · 6990g · stash 9/10 · enc_at_time=94_
- enter town shinto_town

### [seq=513 shop_buy] (in shinto_town)
_L17 · HP 53% · 6960g · stash 10/10 · enc_at_time=94_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=514 leave_town]
_L17 · HP 53% · 6960g · stash 10/10 · enc_at_time=94_
- leave town shinto_town

### [seq=515 enter_zone] zone_04
_L17 · HP 53% · 6960g · stash 10/10 · enc_at_time=94_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=516 use_consumable] zone_04
_L17 · HP 53% · 6960g · stash 9/10 · enc_at_time=94_
- use minor_potion on recruit_einherjar_2449 (HP 208→258/448)

### [seq=517 leave_zone]
_L17 · HP 53% · 6960g · stash 9/10 · enc_at_time=94_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=518 enter_town] (in shinto_town)
_L17 · HP 53% · 6960g · stash 9/10 · enc_at_time=94_
- enter town shinto_town

### [seq=519 shop_buy] (in shinto_town)
_L17 · HP 53% · 6930g · stash 10/10 · enc_at_time=94_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=520 leave_town]
_L17 · HP 53% · 6930g · stash 10/10 · enc_at_time=94_
- leave town shinto_town

### [seq=521 enter_zone] zone_04
_L17 · HP 53% · 6930g · stash 10/10 · enc_at_time=94_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=522 use_consumable] zone_04
_L17 · HP 67% · 6930g · stash 9/10 · enc_at_time=94_
- use minor_potion on mc_einherjar (HP 189→239/358)

### [seq=523 leave_zone]
_L17 · HP 67% · 6930g · stash 9/10 · enc_at_time=94_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=524 enter_town] (in shinto_town)
_L17 · HP 67% · 6930g · stash 9/10 · enc_at_time=94_
- enter town shinto_town

### [seq=525 shop_buy] (in shinto_town)
_L17 · HP 67% · 6900g · stash 10/10 · enc_at_time=94_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=526 leave_town]
_L17 · HP 67% · 6900g · stash 10/10 · enc_at_time=94_
- leave town shinto_town

### [seq=527 enter_zone] zone_04
_L17 · HP 67% · 6900g · stash 10/10 · enc_at_time=94_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 94 [zone_04 idx=7] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (4 rounds)
_dealt 614, took 33, healed 0_

- **r1** hp ?→239 ap 0 st=— | **SURVIVE** +bonus×4 | +status(Taunted→self), +status(Taunted→self) | end [caster_kitsune=169, chunky_slime=255, chunky_slime=255]
- **r2** hp 239→239 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 198 · KILL chunky_slime · +status(Brace Strike DEF buff→self), enemy_status(?→recruit_onmyoji), -status(Taunted→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=169, chunky_slime=0, chunky_slime=194]
- **r3** hp 239→239 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=169, chunky_slime=0, chunky_slime=194]
- **r4** hp 239→239 ap 1 st=— | **SURVIVE** +bonus×4 | KILL chunky_slime,caster_kitsune | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=528 pick_loot] zone_04
_L17 · HP 67% · 7064g · stash 10/10 · enc_at_time=95_
- money +164g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 95 [zone_04 idx=7] vs brute_oni, caster_kitsune, split_slime → **VICTORY** (5 rounds)
_dealt 515, took 221, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→239 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=369, caster_kitsune=169, split_slime=153]
- **r2** hp 239→220 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 · KILL recruit_onmyoji | end [brute_oni=315, caster_kitsune=169, split_slime=153]
- **r3** hp 220→190 ap 2 st=— | **SURVIVE** +bonus×4 | took 30 | end [brute_oni=266, caster_kitsune=74, split_slime=66]
- **r4** hp 190→141 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 317 · took 99 · KILL caster_kitsune,brute_oni | end [brute_oni=0, caster_kitsune=0, split_slime=0, mini_slime=42, mini_slime=42]
- **r5** hp 141→141 ap 0 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 198 · KILL mini_slime,mini_slime | end [brute_oni=0, caster_kitsune=0, split_slime=0, mini_slime=0, mini_slime=0]

### [seq=529 pick_loot] zone_04
_L17 · HP 39% · 7235g · stash 9/10 · enc_at_time=96_
- money +171g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=530 leave_zone]
_L17 · HP 39% · 7235g · stash 9/10 · enc_at_time=96_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=531 enter_town] (in shinto_town)
_L17 · HP 39% · 7235g · stash 9/10 · enc_at_time=96_
- enter town shinto_town

### [seq=532 shop_buy] (in shinto_town)
_L17 · HP 39% · 7205g · stash 10/10 · enc_at_time=96_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=533 leave_town]
_L17 · HP 39% · 7205g · stash 10/10 · enc_at_time=96_
- leave town shinto_town

### [seq=534 enter_zone] zone_04
_L17 · HP 39% · 7205g · stash 10/10 · enc_at_time=96_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=535 use_consumable] zone_04
_L17 · HP 53% · 7205g · stash 9/10 · enc_at_time=96_
- use minor_potion on mc_einherjar (HP 141→191/358)

### [seq=536 leave_zone]
_L17 · HP 53% · 7205g · stash 9/10 · enc_at_time=96_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=537 enter_town] (in shinto_town)
_L17 · HP 53% · 7205g · stash 9/10 · enc_at_time=96_
- enter town shinto_town

### [seq=538 shop_buy] (in shinto_town)
_L17 · HP 53% · 7175g · stash 10/10 · enc_at_time=96_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=539 leave_town]
_L17 · HP 53% · 7175g · stash 10/10 · enc_at_time=96_
- leave town shinto_town

### [seq=540 enter_zone] zone_04
_L17 · HP 53% · 7175g · stash 10/10 · enc_at_time=96_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=541 use_consumable] zone_04
_L17 · HP 67% · 7175g · stash 9/10 · enc_at_time=96_
- use minor_potion on mc_einherjar (HP 191→241/358)

### [seq=542 leave_zone]
_L17 · HP 67% · 7175g · stash 9/10 · enc_at_time=96_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=543 enter_town] (in shinto_town)
_L17 · HP 67% · 7175g · stash 9/10 · enc_at_time=96_
- enter town shinto_town

### [seq=544 shop_buy] (in shinto_town)
_L17 · HP 67% · 7145g · stash 10/10 · enc_at_time=96_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=545 leave_town]
_L17 · HP 67% · 7145g · stash 10/10 · enc_at_time=96_
- leave town shinto_town

### [seq=546 enter_zone] zone_04
_L17 · HP 67% · 7145g · stash 10/10 · enc_at_time=96_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 96 [zone_04 idx=7] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (5 rounds)
_dealt 532, took 187, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→241 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji), enemy_status(Taunted→recruit_onmyoji), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=223, chunky_slime=305, chunky_slime=305]
- **r2** hp 241→239 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL recruit_onmyoji · enemy_status(Brace Strike DEF buff→recruit_einherjar), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=223, chunky_slime=244, chunky_slime=129]
- **r3** hp 239→197 ap 2 st=— | **SURVIVE** +bonus×4 | took 42 · enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=130, chunky_slime=188, chunky_slime=68]
- **r4** hp 197→156 ap 3 st=— | **SURVIVE** +bonus×4 | took 41 · enemy_status(Taunted→recruit_einherjar), +status(Taunted→self) | end [caster_kitsune=37, chunky_slime=188, chunky_slime=68]
- **r5** hp 156→156 ap 3 st=Taunted | **CHEAT(+3AP)** brace_strike→chunky_slime +cheat_extras×3 +bonus×4 | dealt 302 · KILL chunky_slime,caster_kitsune,chunky_slime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=547 pick_loot] zone_04
_L17 · HP 44% · 7287g · stash 10/10 · enc_at_time=97_
- money +142g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=548 use_consumable] zone_04
_L17 · HP 58% · 7287g · stash 9/10 · enc_at_time=97_
- use minor_potion on mc_einherjar (HP 156→206/358)

### [seq=549 leave_zone]
_L17 · HP 58% · 7287g · stash 9/10 · enc_at_time=97_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=11, cleared=True

### [seq=550 enter_town] (in shinto_town)
_L17 · HP 58% · 7287g · stash 9/10 · enc_at_time=97_
- enter town shinto_town

### [seq=551 shop_buy] (in shinto_town)
_L17 · HP 58% · 7257g · stash 10/10 · enc_at_time=97_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=552 leave_town]
_L17 · HP 58% · 7257g · stash 10/10 · enc_at_time=97_
- leave town shinto_town

### [seq=553 enter_zone] zone_04
_L17 · HP 58% · 7257g · stash 10/10 · enc_at_time=97_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 97 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (5 rounds)
_dealt 460, took 77, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→206 ap 0 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(?→recruit_onmyoji) | end [brute_oni=460, mystic_slime=155]
- **r2** hp 206→205 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=460, mystic_slime=60]
- **r3** hp 205→196 ap 2 st=— | **SURVIVE** +bonus×4 | took 9 · KILL mystic_slime · +status(?→self) | end [brute_oni=415, mystic_slime=0]
- **r4** hp 196→246 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 269 · -status(Hex Disrupt→self) | end [brute_oni=146, mystic_slime=0]
- **r5** hp 246→246 ap 0 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 123 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=554 pick_loot] zone_04
_L17 · HP 69% · 7354g · stash 9/10 · enc_at_time=98_
- money +97g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=555 leave_zone]
_L17 · HP 69% · 7354g · stash 9/10 · enc_at_time=98_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=556 enter_town] (in shinto_town)
_L17 · HP 69% · 7354g · stash 9/10 · enc_at_time=98_
- enter town shinto_town

### [seq=557 shop_buy] (in shinto_town)
_L17 · HP 69% · 7324g · stash 10/10 · enc_at_time=98_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=558 leave_town]
_L17 · HP 69% · 7324g · stash 10/10 · enc_at_time=98_
- leave town shinto_town

### [seq=559 enter_zone] zone_04
_L17 · HP 69% · 7324g · stash 10/10 · enc_at_time=98_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=560 use_consumable] zone_04
_L17 · HP 69% · 7324g · stash 9/10 · enc_at_time=98_
- use minor_potion on recruit_einherjar_2449 (HP 241→291/448)

### [seq=561 leave_zone]
_L17 · HP 69% · 7324g · stash 9/10 · enc_at_time=98_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=562 enter_town] (in shinto_town)
_L17 · HP 69% · 7324g · stash 9/10 · enc_at_time=98_
- enter town shinto_town

### [seq=563 shop_buy] (in shinto_town)
_L17 · HP 69% · 7294g · stash 10/10 · enc_at_time=98_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=564 leave_town]
_L17 · HP 69% · 7294g · stash 10/10 · enc_at_time=98_
- leave town shinto_town

### [seq=565 enter_zone] zone_04
_L17 · HP 69% · 7294g · stash 10/10 · enc_at_time=98_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 98 [zone_04 idx=7] vs support_tanuki, swime, brute_oni → **VICTORY** (7 rounds)
_dealt 411, took 206, healed 41, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→234 ap 0 st=— | **SURVIVE** +bonus×4 | took 12 | end [support_tanuki=143, swime=90, brute_oni=376]
- **r2** hp 234→222 ap 1 st=— | **SURVIVE** +bonus×4 | took 12 · KILL swime | end [support_tanuki=200, swime=0, brute_oni=323]
- **r3** hp 222→222 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=199, swime=0, brute_oni=321]
- **r4** hp 222→207 ap 3 st=— | **SURVIVE** +bonus×4 | took 15 | end [support_tanuki=199, swime=0, brute_oni=263]
- **r5** hp 207→192 ap 3 st=— | **SURVIVE** +bonus×4 | took 15 · enemy_status(Rally buff→brute_oni) | end [support_tanuki=199, swime=0, brute_oni=205]
- **r6** hp 192→192 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji | end [support_tanuki=112, swime=0, brute_oni=205]
- **r7** hp 192→192 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 408 · KILL support_tanuki,brute_oni | end [support_tanuki=0, swime=0, brute_oni=0]

### [seq=566 pick_loot] zone_04
_L17 · HP 54% · 7407g · stash 9/10 · enc_at_time=99_
- money +113g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=567 leave_zone]
_L17 · HP 54% · 7407g · stash 9/10 · enc_at_time=99_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=568 enter_town] (in shinto_town)
_L17 · HP 54% · 7407g · stash 9/10 · enc_at_time=99_
- enter town shinto_town

### [seq=569 shop_buy] (in shinto_town)
_L17 · HP 54% · 7377g · stash 10/10 · enc_at_time=99_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=570 leave_town]
_L17 · HP 54% · 7377g · stash 10/10 · enc_at_time=99_
- leave town shinto_town

### [seq=571 enter_zone] zone_04
_L17 · HP 54% · 7377g · stash 10/10 · enc_at_time=99_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=572 use_consumable] zone_04
_L17 · HP 68% · 7377g · stash 9/10 · enc_at_time=99_
- use minor_potion on mc_einherjar (HP 192→242/358)

### [seq=573 leave_zone]
_L17 · HP 68% · 7377g · stash 9/10 · enc_at_time=99_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=574 enter_town] (in shinto_town)
_L17 · HP 68% · 7377g · stash 9/10 · enc_at_time=99_
- enter town shinto_town

### [seq=575 shop_buy] (in shinto_town)
_L17 · HP 68% · 7347g · stash 10/10 · enc_at_time=99_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=576 leave_town]
_L17 · HP 68% · 7347g · stash 10/10 · enc_at_time=99_
- leave town shinto_town

### [seq=577 enter_zone] zone_04
_L17 · HP 68% · 7347g · stash 10/10 · enc_at_time=99_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 99 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (6 rounds)
_dealt 348, took 252, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→242 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=460, mystic_slime=170]
- **r2** hp 242→219 ap 1 st=— | **SURVIVE** +bonus×4 | took 23 · enemy_status(?→recruit_onmyoji) | end [brute_oni=410, mystic_slime=170]
- **r3** hp 219→219 ap 2 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(?→recruit_onmyoji) | end [brute_oni=408, mystic_slime=166]
- **r4** hp 219→208 ap 3 st=— | **SURVIVE** +bonus×4 | took 11 · +status(?→self) | end [brute_oni=363, mystic_slime=71]
- **r5** hp 208→154 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 · KILL mystic_slime · -status(Hex Disrupt→self) | end [brute_oni=313, mystic_slime=0]
- **r6** hp 154→154 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 342 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=578 pick_loot] zone_04
_L17 · HP 43% · 7381g · stash 9/10 · enc_at_time=100_
- money +34g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=579 leave_zone]
_L17 · HP 43% · 7381g · stash 9/10 · enc_at_time=100_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=580 enter_town] (in shinto_town)
_L17 · HP 43% · 7381g · stash 9/10 · enc_at_time=100_
- enter town shinto_town

### [seq=581 shop_buy] (in shinto_town)
_L17 · HP 43% · 7351g · stash 10/10 · enc_at_time=100_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=582 leave_town]
_L17 · HP 43% · 7351g · stash 10/10 · enc_at_time=100_
- leave town shinto_town

### [seq=583 enter_zone] zone_04
_L17 · HP 43% · 7351g · stash 10/10 · enc_at_time=100_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=584 use_consumable] zone_04
_L17 · HP 57% · 7351g · stash 9/10 · enc_at_time=100_
- use minor_potion on mc_einherjar (HP 154→204/358)

### [seq=585 leave_zone]
_L17 · HP 57% · 7351g · stash 9/10 · enc_at_time=100_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=586 enter_town] (in shinto_town)
_L17 · HP 57% · 7351g · stash 9/10 · enc_at_time=100_
- enter town shinto_town

### [seq=587 shop_buy] (in shinto_town)
_L17 · HP 57% · 7321g · stash 10/10 · enc_at_time=100_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=588 leave_town]
_L17 · HP 57% · 7321g · stash 10/10 · enc_at_time=100_
- leave town shinto_town

### [seq=589 enter_zone] zone_04
_L17 · HP 57% · 7321g · stash 10/10 · enc_at_time=100_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 100 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 285, took 82, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→201 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [split_slime=78, speeder_tengu=53, slime=205]
- **r2** hp 201→186 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL speeder_tengu,split_slime,recruit_onmyoji · enemy_status(?→recruit_onmyoji), +status(?→self) | end [split_slime=0, speeder_tengu=0, slime=205]
- **r3** hp 186→186 ap 2 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 285 · KILL slime | end [split_slime=0, speeder_tengu=0, slime=0]

### [seq=590 pick_loot] zone_04
_L17 · HP 52% · 7389g · stash 10/10 · enc_at_time=101_
- money +68g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=591 use_consumable] zone_04
_L17 · HP 66% · 7389g · stash 9/10 · enc_at_time=101_
- use minor_potion on mc_einherjar (HP 186→236/358)

### [seq=592 leave_zone]
_L17 · HP 66% · 7389g · stash 9/10 · enc_at_time=101_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=15, cleared=True

### [seq=593 enter_town] (in shinto_town)
_L17 · HP 66% · 7389g · stash 9/10 · enc_at_time=101_
- enter town shinto_town

### [seq=594 shop_buy] (in shinto_town)
_L17 · HP 66% · 7359g · stash 10/10 · enc_at_time=101_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=595 leave_town]
_L17 · HP 66% · 7359g · stash 10/10 · enc_at_time=101_
- leave town shinto_town

### [seq=596 enter_zone] zone_04
_L17 · HP 66% · 7359g · stash 10/10 · enc_at_time=101_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 101 [zone_04 idx=7] vs brute_oni, caster_kitsune, split_slime → **VICTORY** (8 rounds)
_dealt 328, took 227, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→236 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=461, caster_kitsune=169, split_slime=169]
- **r2** hp 236→236 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=461, caster_kitsune=169, split_slime=169]
- **r3** hp 236→210 ap 2 st=— | **SURVIVE** +bonus×4 | took 26 · enemy_status(?→recruit_onmyoji) | end [brute_oni=413, caster_kitsune=164, split_slime=83]
- **r4** hp 210→184 ap 3 st=— | **SURVIVE** +bonus×4 | took 26 · KILL split_slime · enemy_status(?→recruit_onmyoji) | end [brute_oni=367, caster_kitsune=164, split_slime=0]
- **r5** hp 184→184 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji | end [brute_oni=367, caster_kitsune=164, split_slime=0]
- **r6** hp 184→154 ap 3 st=— | **SURVIVE** +bonus×4 | took 30 | end [brute_oni=326, caster_kitsune=69, split_slime=0]
- **r7** hp 154→141 ap 3 st=— | **SURVIVE** +bonus×4 | took 13 · KILL caster_kitsune · +status(?→self) | end [brute_oni=280, caster_kitsune=0, split_slime=0]
- **r8** hp 141→141 ap 3 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 256 · KILL brute_oni | end [brute_oni=0, caster_kitsune=0, split_slime=0]

### [seq=597 pick_loot] zone_04
_L17 · HP 39% · 7401g · stash 9/10 · enc_at_time=102_
- money +42g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=598 leave_zone]
_L17 · HP 39% · 7401g · stash 9/10 · enc_at_time=102_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=599 enter_town] (in shinto_town)
_L17 · HP 39% · 7401g · stash 9/10 · enc_at_time=102_
- enter town shinto_town

### [seq=600 shop_buy] (in shinto_town)
_L17 · HP 39% · 7371g · stash 10/10 · enc_at_time=102_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=601 leave_town]
_L17 · HP 39% · 7371g · stash 10/10 · enc_at_time=102_
- leave town shinto_town

### [seq=602 enter_zone] zone_04
_L17 · HP 39% · 7371g · stash 10/10 · enc_at_time=102_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=603 use_consumable] zone_04
_L17 · HP 53% · 7371g · stash 9/10 · enc_at_time=102_
- use minor_potion on mc_einherjar (HP 141→191/358)

### [seq=604 leave_zone]
_L17 · HP 53% · 7371g · stash 9/10 · enc_at_time=102_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=605 enter_town] (in shinto_town)
_L17 · HP 53% · 7371g · stash 9/10 · enc_at_time=102_
- enter town shinto_town

### [seq=606 shop_buy] (in shinto_town)
_L17 · HP 53% · 7341g · stash 10/10 · enc_at_time=102_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=607 leave_town]
_L17 · HP 53% · 7341g · stash 10/10 · enc_at_time=102_
- leave town shinto_town

### [seq=608 enter_zone] zone_04
_L17 · HP 53% · 7341g · stash 10/10 · enc_at_time=102_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=609 use_consumable] zone_04
_L17 · HP 53% · 7341g · stash 9/10 · enc_at_time=102_
- use minor_potion on recruit_einherjar_2449 (HP 236→286/448)

### [seq=610 leave_zone]
_L17 · HP 53% · 7341g · stash 9/10 · enc_at_time=102_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=611 enter_town] (in shinto_town)
_L17 · HP 53% · 7341g · stash 9/10 · enc_at_time=102_
- enter town shinto_town

### [seq=612 shop_buy] (in shinto_town)
_L17 · HP 53% · 7311g · stash 10/10 · enc_at_time=102_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=613 leave_town]
_L17 · HP 53% · 7311g · stash 10/10 · enc_at_time=102_
- leave town shinto_town

### [seq=614 enter_zone] zone_04
_L17 · HP 53% · 7311g · stash 10/10 · enc_at_time=102_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### [seq=615 use_consumable] zone_04
_L17 · HP 67% · 7311g · stash 9/10 · enc_at_time=102_
- use minor_potion on mc_einherjar (HP 191→241/358)

### [seq=616 leave_zone]
_L17 · HP 67% · 7311g · stash 9/10 · enc_at_time=102_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=617 enter_town] (in shinto_town)
_L17 · HP 67% · 7311g · stash 9/10 · enc_at_time=102_
- enter town shinto_town

### [seq=618 shop_buy] (in shinto_town)
_L17 · HP 67% · 7281g · stash 10/10 · enc_at_time=102_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=619 leave_town]
_L17 · HP 67% · 7281g · stash 10/10 · enc_at_time=102_
- leave town shinto_town

### [seq=620 enter_zone] zone_04
_L17 · HP 67% · 7281g · stash 10/10 · enc_at_time=102_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 102 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (4 rounds)
_dealt 430, took 68, healed 50_

- **r1** hp ?→240 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=318, mystic_slime=185]
- **r2** hp 240→240 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=265, mystic_slime=185]
- **r3** hp 240→225 ap 2 st=— | **SURVIVE** +bonus×4 | took 15 | end [brute_oni=205, mystic_slime=181]
- **r4** hp 225→225 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 424 · KILL brute_oni,mystic_slime | end [brute_oni=0, mystic_slime=0]

### [seq=621 pick_loot] zone_04
_L17 · HP 63% · 7314g · stash 9/10 · enc_at_time=103_
- money +33g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=622 leave_zone]
_L17 · HP 63% · 7314g · stash 9/10 · enc_at_time=103_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=17, cleared=True

### [seq=623 enter_town] (in shinto_town)
_L17 · HP 63% · 7314g · stash 9/10 · enc_at_time=103_
- enter town shinto_town

### [seq=624 shop_buy] (in shinto_town)
_L17 · HP 63% · 7284g · stash 10/10 · enc_at_time=103_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=625 leave_town]
_L17 · HP 63% · 7284g · stash 10/10 · enc_at_time=103_
- leave town shinto_town

### [seq=626 enter_zone] zone_04
_L17 · HP 63% · 7284g · stash 10/10 · enc_at_time=103_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 103 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 200, took 67, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→224 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=61, speeder_tengu=181, slime=84]
- **r2** hp 224→222 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL split_slime,slime | end [split_slime=0, speeder_tengu=181, slime=0]
- **r3** hp 222→222 ap 2 st=— | **CHEAT(+1AP)** thrust→speeder_tengu +cheat_extras×1 +bonus×4 | dealt 200 · KILL recruit_onmyoji,speeder_tengu | end [split_slime=0, speeder_tengu=0, slime=0]

### [seq=627 pick_loot] zone_04
_L17 · HP 62% · 7299g · stash 10/10 · enc_at_time=104_
- money +15g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 104 [zone_04 idx=7] vs split_slime, split_slime, slime → **VICTORY** (4 rounds)
_dealt 661, took 25, healed 50_

- **r1** hp ?→221 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [split_slime=95, split_slime=153, slime=142]
- **r2** hp 221→221 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=10, split_slime=153, slime=142]
- **r3** hp 221→220 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=10, split_slime=64, slime=56]
- **r4** hp 220→220 ap 3 st=— | **CHEAT(+1AP)** thrust→split_slime +cheat_extras×1 +bonus×4 | dealt 281 · KILL slime,mini_slime,mini_slime,mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0, mini_slime=0, mini_slime=0]

### [seq=628 pick_loot] zone_04
_L17 · HP 61% · 7331g · stash 9/10 · enc_at_time=105_
- money +32g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=629 leave_zone]
_L17 · HP 61% · 7331g · stash 9/10 · enc_at_time=105_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=630 enter_town] (in shinto_town)
_L17 · HP 61% · 7331g · stash 9/10 · enc_at_time=105_
- enter town shinto_town

### [seq=631 shop_buy] (in shinto_town)
_L17 · HP 61% · 7301g · stash 10/10 · enc_at_time=105_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=632 leave_town]
_L17 · HP 61% · 7301g · stash 10/10 · enc_at_time=105_
- leave town shinto_town

### [seq=633 enter_zone] zone_04
_L17 · HP 61% · 7301g · stash 10/10 · enc_at_time=105_
- enter zone_04 (already_cleared=True, via=sim_decide_zone)

### ENC 105 [zone_04 idx=7] vs brute_oni, mystic_slime → **VICTORY** (4 rounds)
_dealt 566, took 94, healed 50_

- **r1** hp ?→194 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 | end [brute_oni=456, mystic_slime=155]
- **r2** hp 194→194 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_onmyoji) | end [brute_oni=415, mystic_slime=155]
- **r3** hp 194→244 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 235 · enemy_status(?→recruit_onmyoji) | end [brute_oni=234, mystic_slime=60]
- **r4** hp 244→244 ap 0 st=— | **SURVIVE** +bonus×4 | KILL mystic_slime,brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=634 pick_loot] zone_04
_L17 · HP 68% · 7311g · stash 9/10 · enc_at_time=106_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=635 leave_zone]
_L17 · HP 68% · 7311g · stash 9/10 · enc_at_time=106_
- leave zone_04: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=636 enter_town] (in shinto_town)
_L17 · HP 68% · 7311g · stash 9/10 · enc_at_time=106_
- enter town shinto_town

### [seq=637 shop_buy] (in shinto_town)
_L17 · HP 68% · 7281g · stash 10/10 · enc_at_time=106_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=638 leave_town]
_L17 · HP 68% · 7281g · stash 10/10 · enc_at_time=106_
- leave town shinto_town

### [seq=639 enter_zone] zone_05
_L17 · HP 68% · 7281g · stash 10/10 · enc_at_time=106_
- enter zone_05 (already_cleared=False, via=sim_decide_zone)

### [seq=640 use_consumable] zone_05
_L17 · HP 68% · 7281g · stash 9/10 · enc_at_time=106_
- use minor_potion on recruit_onmyoji_5132 (HP 39→89/91)

### [seq=641 leave_zone]
_L17 · HP 68% · 7281g · stash 9/10 · enc_at_time=106_
- leave zone_05: reason=sim_post_zone, enc_idx=0, overstay=0, cleared=False

### [seq=642 enter_town] (in shinto_town)
_L17 · HP 68% · 7281g · stash 9/10 · enc_at_time=106_
- enter town shinto_town

### [seq=643 shop_buy] (in shinto_town)
_L17 · HP 68% · 7251g · stash 10/10 · enc_at_time=106_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=644 leave_town]
_L17 · HP 68% · 7251g · stash 10/10 · enc_at_time=106_
- leave town shinto_town

### [seq=645 enter_zone] zone_05
_L17 · HP 68% · 7251g · stash 10/10 · enc_at_time=106_
- enter zone_05 (already_cleared=False, via=sim_decide_zone)

### ENC 106 [zone_05 idx=0] vs leech_slime, slime, slime → **VICTORY** (5 rounds)
_dealt 386, took 173, healed 50, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→243 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [leech_slime=187, slime=137, slime=241]
- **r2** hp 243→243 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [leech_slime=187, slime=137, slime=241]
- **r3** hp 243→243 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Brace Strike DEF buff→slime) | end [leech_slime=187, slime=56, slime=159]
- **r4** hp 243→242 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL recruit_onmyoji · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [leech_slime=187, slime=56, slime=74]
- **r5** hp 242→242 ap 3 st=— | **CHEAT(+3AP)** thrust→leech_slime +cheat_extras×3 +bonus×4 | dealt 384 · KILL slime,slime,leech_slime | end [leech_slime=0, slime=0, slime=0]

### [seq=646 pick_loot] zone_05
_L17 · HP 68% · 7553g · stash 10/10 · enc_at_time=107_
- money +302g, offered=['warden_tonic'], **selected**=['warden_tonic'], skipped=[], discarded_stash=[]

### ENC 107 [zone_05 idx=1] vs speeder_tengu, caster_kitsune → **VICTORY** (4 rounds)
_dealt 98, took 232, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→226 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(?→recruit_onmyoji), +status(?→self) | end [speeder_tengu=186, caster_kitsune=259]
- **r2** hp 226→190 ap 1 st=— | **SURVIVE** +bonus×4 | took 21 · KILL recruit_onmyoji · +status(?→self) | end [speeder_tengu=186, caster_kitsune=167]
- **r3** hp 190→110 ap 2 st=— | **SURVIVE** +bonus×4 | took 50 · +status(?→self), -status(Searing Edge DOT→self), -status(Hex Disrupt→self) | end [speeder_tengu=94, caster_kitsune=75]
- **r4** hp 110→108 ap 3 st=— | **CHEAT(+1AP)** thrust→speeder_tengu +cheat_extras×1 +bonus×4 | took 2 · retal 98 · KILL speeder_tengu,caster_kitsune | end [speeder_tengu=0, caster_kitsune=0]

### [seq=647 pick_loot] zone_05
_L17 · HP 30% · 7839g · stash 10/10 · enc_at_time=108_
- money +286g, offered=['berserker_tonic'], **selected**=[], skipped=['berserker_tonic'], discarded_stash=[]

### ENC 108 [zone_05 idx=2] vs brute_oni, leech_slime, swime → **VICTORY** (6 rounds)
_dealt 314, took 311, healed 0, deaths: ['recruit_onmyoji_5132', 'mc_einherjar']_

- **r1** hp ?→76 ap 0 st=— | **SURVIVE** +bonus×4 | took 32 | end [brute_oni=502, leech_slime=217, swime=174]
- **r2** hp 76→76 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji | end [brute_oni=460, leech_slime=217, swime=174]
- **r3** hp 76→10 ap 2 st=— | **SURVIVE** +bonus×4 | took 66 | end [brute_oni=418, leech_slime=127, swime=86]
- **r4** hp 10→0 ap 3 st=— | **SURVIVE** +bonus×4 | took 22 · KILL swime | end [brute_oni=376, leech_slime=43, swime=0]
- **r5** hp 0→0 ap 3 st=— | — | KILL leech_slime | end [brute_oni=334, leech_slime=0, swime=0]
- **r6** hp 0→0 ap 3 st=— | — | KILL brute_oni | end [brute_oni=0, leech_slime=0, swime=0]

### [seq=648 pick_loot] zone_05
_L17 · HP 30% · 8160g · stash 10/10 · enc_at_time=109_
- money +321g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=649 recruit_accept] zone_05
_L17 · HP 30% · 8160g · stash 10/10 · enc_at_time=109_
- recruit_accept: Einherjar Recruit (einherjar L12) id=recruit_einherjar_4356

### ENC 109 [zone_05 idx=3] vs split_slime, split_slime, support_tanuki, chunky_slime → **VICTORY** (12 rounds)
_dealt 730, took 262, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→108 ap 0 st=— | **SURVIVE** +bonus×4 | +status(Taunted→self), enemy_status(Rally buff→split_slime) | end [split_slime=146, split_slime=249, support_tanuki=380, chunky_slime=355]
- **r2** hp 108→108 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 170 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [split_slime=59, split_slime=163, support_tanuki=294, chunky_slime=185]
- **r3** hp 108→106 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · KILL split_slime | end [split_slime=0, split_slime=77, support_tanuki=294, chunky_slime=130]
- **r4** hp 106→105 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL split_slime · enemy_status(Taunted→recruit_onmyoji) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=130]
- **r5** hp 105→104 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=69]
- **r6** hp 104→104 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=164]
- **r7** hp 104→104 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_onmyoji) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=164]
- **r8** hp 104→103 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL recruit_onmyoji | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=106]
- **r9** hp 103→102 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Rally buff→chunky_slime) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=51]
- **r10** hp 102→102 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_einherjar) | end [split_slime=0, split_slime=0, support_tanuki=380, chunky_slime=146]
- **r11** hp 102→102 ap 3 st=— | **SURVIVE** +bonus×4 | KILL chunky_slime · enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [split_slime=0, split_slime=0, support_tanuki=114, chunky_slime=0]
- **r12** hp 102→102 ap 3 st=— | NORMAL thrust→support_tanuki +bonus×4 | dealt 180 · KILL support_tanuki | end [split_slime=0, split_slime=0, support_tanuki=0, chunky_slime=0]

### [seq=650 pick_loot] zone_05
_L18 · HP 27% · 8538g · stash 10/10 · enc_at_time=110_
- money +378g, offered=['minor_potion'], **selected**=[], skipped=['minor_potion'], discarded_stash=[]

### ENC 110 [zone_05 idx=4] vs speeder_tengu, speeder_tengu, caster_kitsune, toxic_slime → **VICTORY** (3 rounds)
_dealt 306, took 187, healed 0, deaths: ['recruit_onmyoji_5132']_

- **r1** hp ?→98 ap 0 st=— | **SURVIVE** +bonus×4 | took 4 · KILL recruit_onmyoji · enemy_status(?→recruit_einherjar) | end [speeder_tengu=106, speeder_tengu=84, caster_kitsune=295, toxic_slime=127]
- **r2** hp 98→38 ap 1 st=— | **SURVIVE** +bonus×4 | took 60 · KILL speeder_tengu,speeder_tengu | end [speeder_tengu=0, speeder_tengu=0, caster_kitsune=199, toxic_slime=32]
- **r3** hp 38→38 ap 2 st=— | **CHEAT(+2AP)** thrust→caster_kitsune +cheat_extras×2 +bonus×4 | dealt 306 · KILL toxic_slime,caster_kitsune | end [speeder_tengu=0, speeder_tengu=0, caster_kitsune=0, toxic_slime=0]

### [seq=651 pick_loot] zone_05
_L18 · HP 10% · 9143g · stash 10/10 · enc_at_time=111_
- money +605g, offered=['minor_potion'], **selected**=[], skipped=['minor_potion'], discarded_stash=[]

### ENC 111 [zone_05 idx=5] vs brute_oni, caster_kitsune, leech_slime → **DEFEAT** (2 rounds)
_dealt 0, took 205, healed 0, deaths: ['recruit_onmyoji_5132', 'mc_einherjar', 'recruit_einherjar_2449']_

- **r1** hp ?→38 ap 0 st=— | **SURVIVE** +bonus×4 | KILL recruit_onmyoji · enemy_status(?→recruit_onmyoji) | end [brute_oni=628, caster_kitsune=277, leech_slime=217]
- **r2** hp 38→0 ap 1 st=— | **SURVIVE** +bonus×4 | took 52 · KILL recruit_einherjar | end [brute_oni=628, caster_kitsune=180, leech_slime=122]
