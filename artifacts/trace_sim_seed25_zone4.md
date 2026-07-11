# Run Trace: sim_einherjar_seed25_zone4 (einherjar 'sim_mc' L16)

**Final state**: L16 · HP 14/343 · 6006g · zones cleared: ['zone_01', 'zone_02', 'zone_03', 'zone_04']
**Encounters**: 90
**Macro events**: 507

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
_dealt 24, took 2, healed 0_

- **r1** hp ?→65 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [fodder_slime=36]
- **r2** hp 65→64 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=30]
- **r3** hp 64→63 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=24]
- **r4** hp 63→63 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 24 · KILL fodder_slime | end [fodder_slime=0]

### [seq=2 pick_loot] zone_01
_L1 · HP 97% · 10g · stash 1/10 · enc_at_time=1_
- money +10g, offered=['battlemage_tonic'], **selected**=['battlemage_tonic'], skipped=[], discarded_stash=[]

### ENC 1 [zone_01 idx=1] vs fodder_slime, fodder_slime → **VICTORY** (6 rounds)
_dealt 24, took 8, healed 0_

- **r1** hp ?→61 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=30]
- **r2** hp 61→60 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=30, fodder_slime=24]
- **r3** hp 60→59 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=24, fodder_slime=24]
- **r4** hp 59→57 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=18, fodder_slime=18]
- **r5** hp 57→55 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r6** hp 55→55 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 24 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=3 pick_loot] zone_01
_L1 · HP 85% · 30g · stash 1/10 · enc_at_time=2_
- money +20g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 2 [zone_01 idx=2] vs fodder_slime, fodder_slime → **VICTORY** (6 rounds)
_dealt 24, took 8, healed 0_

- **r1** hp ?→54 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=30]
- **r2** hp 54→52 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=30, fodder_slime=24]
- **r3** hp 52→51 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=24, fodder_slime=24]
- **r4** hp 51→49 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=18, fodder_slime=18]
- **r5** hp 49→47 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r6** hp 47→47 ap 3 st=— | **CHEAT(+3AP)** basic_attack→fodder_slime +cheat_extras×3 +bonus×4 | dealt 24 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=4 pick_loot] zone_01
_L2 · HP 58% · 60g · stash 1/10 · enc_at_time=3_
- money +30g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=5 leave_zone]
_L2 · HP 58% · 60g · stash 1/10 · enc_at_time=3_
- leave zone_01: reason=sim_post_zone, enc_idx=3, overstay=0, cleared=False

### [seq=6 enter_town] (in shinto_town)
_L2 · HP 58% · 60g · stash 1/10 · enc_at_time=3_
- enter town shinto_town

### [seq=7 shop_buy] (in shinto_town)
_L2 · HP 58% · 30g · stash 2/10 · enc_at_time=3_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=8 shop_buy] (in shinto_town)
_L2 · HP 58% · 0g · stash 3/10 · enc_at_time=3_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g]

### [seq=9 leave_town]
_L2 · HP 58% · 0g · stash 3/10 · enc_at_time=3_
- leave town shinto_town

### [seq=10 enter_zone] zone_01
_L2 · HP 58% · 0g · stash 3/10 · enc_at_time=3_
- enter zone_01 (already_cleared=False, via=sim_decide_zone)

### ENC 3 [zone_01 idx=3] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (5 rounds)
_dealt 41, took 10, healed 40_

- **r1** hp ?→44 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=27, fodder_slime=27, fodder_slime=44]
- **r2** hp 44→41 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=18, fodder_slime=18, fodder_slime=36]
- **r3** hp 41→80 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 25 · took 1 | end [fodder_slime=9, fodder_slime=9, fodder_slime=20]
- **r4** hp 80→77 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=12]
- **r5** hp 77→77 ap 1 st=— | **CHEAT(+1AP)** basic_attack→fodder_slime +cheat_extras×1 +bonus×4 | dealt 16 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=11 pick_loot] zone_01
_L2 · HP 95% · 38g · stash 2/10 · enc_at_time=4_
- money +38g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 4 [zone_01 idx=4] vs alpha_slime → **VICTORY** (10 rounds)
_dealt 21, took 60, healed 50_

- **r1** hp ?→75 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=83]
- **r2** hp 75→67 ap 1 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=76]
- **r3** hp 67→65 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=69]
- **r4** hp 65→57 ap 3 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=62]
- **r5** hp 57→55 ap 3 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=55]
- **r6** hp 55→47 ap 3 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=48]
- **r7** hp 47→39 ap 3 st=— | **SURVIVE** +bonus×4 | took 8 | end [alpha_slime=41]
- **r8** hp 39→73 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 14 · took 16 · retal 7 | end [alpha_slime=13]
- **r9** hp 73→71 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [alpha_slime=6]
- **r10** hp 71→67 ap 1 st=— | NORMAL basic_attack→alpha_slime +bonus×4 | took 4 · KILL alpha_slime | end [alpha_slime=0]

### [seq=12 pick_loot] zone_01
_L2 · HP 83% · 129g · stash 5/10 · enc_at_time=5_
- money +91g, offered=['minor_potion', 'warding_mail', 'cast_brace_strike', 'cast_heavy_strike'], **selected**=['minor_potion', 'warding_mail', 'cast_brace_strike', 'cast_heavy_strike'], skipped=[], discarded_stash=[]

### [seq=13 leave_zone]
_L2 · HP 83% · 129g · stash 5/10 · enc_at_time=5_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=True

### [seq=14 enter_town] (in shinto_town)
_L2 · HP 83% · 129g · stash 5/10 · enc_at_time=5_
- enter town shinto_town

### [seq=15 shop_buy] (in shinto_town)
_L2 · HP 83% · 29g · stash 6/10 · enc_at_time=5_
- **BOUGHT** iron_blade @ 100g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=16 equip] (in shinto_town)
_L2 · HP 83% · 29g · stash 5/10 · enc_at_time=5_
- equip iron_blade → mc_einherjar:WEAPON (displaced=None)

### [seq=17 equip] (in shinto_town)
_L2 · HP 53% · 29g · stash 4/10 · enc_at_time=5_
- equip warding_mail → mc_einherjar:ARMOR (displaced=None)

### [seq=18 leave_town]
_L2 · HP 53% · 29g · stash 4/10 · enc_at_time=5_
- leave town shinto_town

### [seq=19 enter_zone] zone_01
_L2 · HP 53% · 29g · stash 4/10 · enc_at_time=5_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### [seq=20 use_consumable] zone_01
_L2 · HP 93% · 29g · stash 3/10 · enc_at_time=5_
- use minor_potion on mc_einherjar (HP 67→117/126)

### ENC 5 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 48, took 2, healed 0_

- **r1** hp ?→115 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=12, fodder_slime=12]
- **r2** hp 115→115 ap 1 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 48 · KILL fodder_slime,fodder_slime | end [fodder_slime=0, fodder_slime=0]

### [seq=21 pick_loot] zone_01
_L2 · HP 91% · 51g · stash 3/10 · enc_at_time=6_
- money +22g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=22 leave_zone]
_L2 · HP 91% · 51g · stash 3/10 · enc_at_time=6_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=1, cleared=True

### [seq=23 enter_town] (in shinto_town)
_L2 · HP 91% · 51g · stash 3/10 · enc_at_time=6_
- enter town shinto_town

### [seq=24 shop_buy] (in shinto_town)
_L2 · HP 91% · 21g · stash 4/10 · enc_at_time=6_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=25 leave_town]
_L2 · HP 91% · 21g · stash 4/10 · enc_at_time=6_
- leave town shinto_town

### [seq=26 enter_zone] zone_01
_L2 · HP 91% · 21g · stash 4/10 · enc_at_time=6_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 6 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 48, took 0, healed 0_

- **r1** hp ?→115 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 48 · KILL fodder_slime | end [fodder_slime=0]

### [seq=27 pick_loot] zone_01
_L3 · HP 82% · 30g · stash 4/10 · enc_at_time=7_
- money +9g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 7 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 58, took 0, healed 0_

- **r1** hp ?→115 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 58 · KILL fodder_slime | end [fodder_slime=0]

### [seq=28 pick_loot] zone_01
_L3 · HP 82% · 39g · stash 4/10 · enc_at_time=8_
- money +9g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 8 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 85, took 3, healed 0_

- **r1** hp ?→112 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=7, fodder_slime=7, fodder_slime=7]
- **r2** hp 112→112 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 85 · KILL fodder_slime,fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=29 pick_loot] zone_01
_L3 · HP 79% · 63g · stash 4/10 · enc_at_time=9_
- money +24g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=30 leave_zone]
_L3 · HP 79% · 63g · stash 4/10 · enc_at_time=9_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=4, cleared=True

### [seq=31 enter_town] (in shinto_town)
_L3 · HP 79% · 63g · stash 4/10 · enc_at_time=9_
- enter town shinto_town

### [seq=32 shop_buy] (in shinto_town)
_L3 · HP 79% · 33g · stash 5/10 · enc_at_time=9_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=33 shop_buy] (in shinto_town)
_L3 · HP 79% · 3g · stash 6/10 · enc_at_time=9_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=34 leave_town]
_L3 · HP 79% · 3g · stash 6/10 · enc_at_time=9_
- leave town shinto_town

### [seq=35 enter_zone] zone_01
_L3 · HP 79% · 3g · stash 6/10 · enc_at_time=9_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 9 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 83, took 3, healed 0_

- **r1** hp ?→109 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=7, fodder_slime=24, fodder_slime=24]
- **r2** hp 109→109 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 83 · KILL fodder_slime,fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=36 pick_loot] zone_01
_L3 · HP 77% · 32g · stash 6/10 · enc_at_time=10_
- money +29g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 10 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 56, took 2, healed 0_

- **r1** hp ?→107 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=7, fodder_slime=7]
- **r2** hp 107→107 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 56 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=37 pick_loot] zone_01
_L3 · HP 76% · 46g · stash 6/10 · enc_at_time=11_
- money +14g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 11 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 58, took 0, healed 0_

- **r1** hp ?→107 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 58 · KILL fodder_slime | end [fodder_slime=0]

### [seq=38 pick_loot] zone_01
_L3 · HP 76% · 53g · stash 6/10 · enc_at_time=12_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 12 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 55, took 4, healed 0_

- **r1** hp ?→105 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=52, fodder_slime=24, fodder_slime=7]
- **r2** hp 105→103 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL fodder_slime | end [fodder_slime=24, fodder_slime=0, fodder_slime=7]
- **r3** hp 103→103 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 55 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=39 pick_loot] zone_01
_L4 · HP 66% · 85g · stash 6/10 · enc_at_time=13_
- money +32g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 13 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 98, took 3, healed 0_

- **r1** hp ?→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [fodder_slime=19, fodder_slime=2, fodder_slime=2]
- **r2** hp 100→100 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 98 · KILL fodder_slime,fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=40 pick_loot] zone_01
_L4 · HP 64% · 106g · stash 6/10 · enc_at_time=14_
- money +21g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 14 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→98 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 98→98 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=41 pick_loot] zone_01
_L4 · HP 62% · 119g · stash 6/10 · enc_at_time=15_
- money +13g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 15 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→96 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 96→96 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=42 pick_loot] zone_01
_L4 · HP 61% · 131g · stash 6/10 · enc_at_time=16_
- money +12g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 16 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→96 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=43 pick_loot] zone_01
_L4 · HP 61% · 135g · stash 6/10 · enc_at_time=17_
- money +4g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 17 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→94 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 94→94 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=44 pick_loot] zone_01
_L4 · HP 60% · 145g · stash 6/10 · enc_at_time=18_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 18 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→92 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 92→92 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=45 pick_loot] zone_01
_L4 · HP 59% · 151g · stash 6/10 · enc_at_time=19_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 19 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→92 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=46 pick_loot] zone_01
_L4 · HP 59% · 154g · stash 6/10 · enc_at_time=20_
- money +3g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 20 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→90 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 90→90 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=47 pick_loot] zone_01
_L4 · HP 57% · 159g · stash 6/10 · enc_at_time=21_
- money +5g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 21 [zone_01 idx=5] vs fodder_slime, fodder_slime, fodder_slime → **VICTORY** (3 rounds)
_dealt 64, took 4, healed 0_

- **r1** hp ?→88 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=19, fodder_slime=2, fodder_slime=52]
- **r2** hp 88→86 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL fodder_slime | end [fodder_slime=0, fodder_slime=2, fodder_slime=19]
- **r3** hp 86→86 ap 2 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 64 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0, fodder_slime=0]

### [seq=48 pick_loot] zone_01
_L4 · HP 55% · 165g · stash 6/10 · enc_at_time=22_
- money +6g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=49 use_consumable] zone_01
_L4 · HP 87% · 165g · stash 5/10 · enc_at_time=22_
- use minor_potion on mc_einherjar (HP 86→136/157)

### [seq=50 leave_zone]
_L4 · HP 87% · 165g · stash 5/10 · enc_at_time=22_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=17, cleared=True

### [seq=51 enter_town] (in shinto_town)
_L4 · HP 87% · 165g · stash 5/10 · enc_at_time=22_
- enter town shinto_town

### [seq=52 shop_buy] (in shinto_town)
_L4 · HP 87% · 135g · stash 6/10 · enc_at_time=22_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=53 shop_buy] (in shinto_town)
_L4 · HP 87% · 105g · stash 7/10 · enc_at_time=22_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=54 shop_buy] (in shinto_town)
_L4 · HP 87% · 75g · stash 8/10 · enc_at_time=22_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=55 shop_buy] (in shinto_town)
_L4 · HP 87% · 45g · stash 9/10 · enc_at_time=22_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=56 shop_buy] (in shinto_town)
_L4 · HP 87% · 15g · stash 10/10 · enc_at_time=22_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=57 leave_town]
_L4 · HP 87% · 15g · stash 10/10 · enc_at_time=22_
- leave town shinto_town

### [seq=58 enter_zone] zone_01
_L4 · HP 87% · 15g · stash 10/10 · enc_at_time=22_
- enter zone_01 (already_cleared=True, via=sim_decide_zone)

### ENC 22 [zone_01 idx=5] vs fodder_slime → **VICTORY** (1 rounds)
_dealt 68, took 0, healed 0_

- **r1** hp ?→136 ap 0 st=— | NORMAL basic_attack→fodder_slime +bonus×4 | dealt 68 · KILL fodder_slime | end [fodder_slime=0]

### [seq=59 pick_loot] zone_01
_L4 · HP 87% · 17g · stash 10/10 · enc_at_time=23_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 23 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 99, took 1, healed 0_

- **r1** hp ?→135 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [fodder_slime=36, fodder_slime=2]
- **r2** hp 135→135 ap 1 st=— | **CHEAT(+1AP)** brace_strike→fodder_slime +cheat_extras×1 +bonus×4 | dealt 99 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=60 pick_loot] zone_01
_L4 · HP 86% · 17g · stash 10/10 · enc_at_time=24_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 24 [zone_01 idx=5] vs fodder_slime, fodder_slime → **VICTORY** (2 rounds)
_dealt 65, took 2, healed 0_

- **r1** hp ?→133 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [fodder_slime=2, fodder_slime=2]
- **r2** hp 133→133 ap 1 st=— | NORMAL brace_strike→fodder_slime +bonus×4 | dealt 65 · KILL fodder_slime,fodder_slime · +status(Brace Strike DEF buff→self) | end [fodder_slime=0, fodder_slime=0]

### [seq=61 pick_loot] zone_01
_L4 · HP 85% · 17g · stash 10/10 · enc_at_time=25_
- money +0g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=62 leave_zone]
_L4 · HP 85% · 17g · stash 10/10 · enc_at_time=25_
- leave zone_01: reason=sim_post_zone, enc_idx=5, overstay=20, cleared=True

### [seq=63 enter_zone] zone_02
_L4 · HP 85% · 17g · stash 10/10 · enc_at_time=25_
- enter zone_02 (already_cleared=False, via=sim_decide_zone)

### ENC 25 [zone_02 idx=0] vs slime, slime → **VICTORY** (4 rounds)
_dealt 57, took 6, healed 0_

- **r1** hp ?→131 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=67, slime=67]
- **r2** hp 131→129 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=37, slime=37]
- **r3** hp 129→127 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=7, slime=7]
- **r4** hp 127→127 ap 3 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 57 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [slime=0, slime=0]

### [seq=64 pick_loot] zone_02
_L5 · HP 74% · 129g · stash 10/10 · enc_at_time=26_
- money +112g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 26 [zone_02 idx=1] vs swime, slime → **VICTORY** (3 rounds)
_dealt 68, took 17, healed 0_

- **r1** hp ?→112 ap 0 st=— | **SURVIVE** +bonus×4 | took 15 · enemy_status(Brace Strike DEF buff→slime) | end [swime=66, slime=43]
- **r2** hp 112→110 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [swime=30, slime=7]
- **r3** hp 110→110 ap 2 st=— | **CHEAT(+1AP)** brace_strike→swime +cheat_extras×1 +bonus×4 | dealt 68 · KILL swime,slime · +status(Brace Strike DEF buff→self) | end [swime=0, slime=0]

### [seq=65 pick_loot] zone_02
_L5 · HP 64% · 199g · stash 10/10 · enc_at_time=27_
- money +70g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 27 [zone_02 idx=2] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 104, took 10, healed 0_

- **r1** hp ?→103 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · +status(?→self) | end [mystic_slime=58, slime=43, slime=62]
- **r2** hp 103→100 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime), -status(Hex Disrupt→self) | end [mystic_slime=21, slime=7, slime=27]
- **r3** hp 100→100 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 104 · KILL slime,slime,mystic_slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0]

### [seq=66 pick_loot] zone_02
_L5 · HP 58% · 329g · stash 10/10 · enc_at_time=28_
- money +130g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 28 [zone_02 idx=3] vs chunky_slime, swime → **VICTORY** (7 rounds)
_dealt 81, took 49, healed 50_

- **r1** hp ?→86 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · +status(Taunted→self) | end [chunky_slime=155, swime=66]
- **r2** hp 86→56 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 30 · took 30 · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=108, swime=30]
- **r3** hp 56→54 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · KILL swime · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=91, swime=0]
- **r4** hp 54→53 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=74, swime=0]
- **r5** hp 53→102 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 34 · took 1 | end [chunky_slime=23, swime=0]
- **r6** hp 102→101 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime) | end [chunky_slime=6, swime=0]
- **r7** hp 101→101 ap 1 st=— | NORMAL basic_attack→chunky_slime +bonus×4 | dealt 17 · KILL chunky_slime | end [chunky_slime=0, swime=0]

### [seq=67 pick_loot] zone_02
_L5 · HP 59% · 410g · stash 9/10 · enc_at_time=29_
- money +81g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 29 [zone_02 idx=4] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 103, took 8, healed 0_

- **r1** hp ?→97 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=50, slime=62, slime=62]
- **r2** hp 97→93 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=13, slime=27, slime=27]
- **r3** hp 93→93 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 103 · KILL slime,toxic_slime,slime · +status(Brace Strike DEF buff→self) | end [toxic_slime=0, slime=0, slime=0]

### [seq=68 pick_loot] zone_02
_L6 · HP 49% · 553g · stash 10/10 · enc_at_time=30_
- money +143g, offered=['str_tonic'], **selected**=['str_tonic'], skipped=[], discarded_stash=[]

### [seq=69 use_consumable] zone_02
_L6 · HP 76% · 553g · stash 9/10 · enc_at_time=30_
- use minor_potion on mc_einherjar (HP 93→143/188)

### ENC 30 [zone_02 idx=5] vs swime, mystic_slime, chunky_slime → **VICTORY** (5 rounds)
_dealt 105, took 52, healed 0_

- **r1** hp ?→137 ap 0 st=— | **SURVIVE** +bonus×4 | took 6 · +status(?→self), +status(Taunted→self) | end [swime=61, mystic_slime=53, chunky_slime=155]
- **r2** hp 137→99 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 39 · took 38 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Hex Disrupt→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=20, mystic_slime=11, chunky_slime=94]
- **r3** hp 99→92 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · KILL swime,mystic_slime · +status(?→self) | end [swime=0, mystic_slime=0, chunky_slime=72]
- **r4** hp 92→91 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→chunky_slime), -status(Hex Disrupt→self) | end [swime=0, mystic_slime=0, chunky_slime=50]
- **r5** hp 91→91 ap 2 st=— | **CHEAT(+2AP)** basic_attack→chunky_slime +cheat_extras×2 +bonus×4 | dealt 66 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=70 pick_loot] zone_02
_L6 · HP 48% · 658g · stash 9/10 · enc_at_time=31_
- money +105g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=71 use_consumable] zone_02
_L6 · HP 75% · 658g · stash 8/10 · enc_at_time=31_
- use minor_potion on mc_einherjar (HP 91→141/188)

### ENC 31 [zone_02 idx=6] vs omega_slime → **VICTORY** (13 rounds)
_dealt 184, took 202, healed 100_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=295]
- **r2** hp 141→141 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=295]
- **r3** hp 141→104 ap 2 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=272]
- **r4** hp 104→104 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=272]
- **r5** hp 104→104 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=272]
- **r6** hp 104→67 ap 3 st=— | **SURVIVE** +bonus×4 | took 37 | end [omega_slime=249]
- **r7** hp 67→83 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 69 · took 34 | end [omega_slime=159]
- **r8** hp 83→83 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=162]
- **r9** hp 83→83 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [omega_slime=165]
- **r10** hp 83→59 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 46 · took 74 | end [omega_slime=100]
- **r11** hp 59→56 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [omega_slime=81]
- **r12** hp 56→39 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 | end [omega_slime=63]
- **r13** hp 39→39 ap 2 st=— | **CHEAT(+2AP)** basic_attack→omega_slime +cheat_extras×2 +bonus×4 | dealt 69 · KILL omega_slime | end [omega_slime=0]

### [seq=72 pick_loot] zone_02
_L6 · HP 21% · 745g · stash 8/10 · enc_at_time=32_
- money +87g, offered=['minor_potion', 'scroll_brace_strike'], **selected**=['minor_potion', 'scroll_brace_strike'], skipped=[], discarded_stash=[]

### [seq=73 leave_zone]
_L6 · HP 21% · 745g · stash 8/10 · enc_at_time=32_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=0, cleared=True

### [seq=74 enter_town] (in shinto_town)
_L6 · HP 21% · 745g · stash 8/10 · enc_at_time=32_
- enter town shinto_town

### [seq=75 shop_buy] (in shinto_town)
_L6 · HP 21% · 715g · stash 9/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=76 shop_buy] (in shinto_town)
_L6 · HP 21% · 685g · stash 10/10 · enc_at_time=32_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=77 leave_town]
_L6 · HP 21% · 685g · stash 10/10 · enc_at_time=32_
- leave town shinto_town

### [seq=78 enter_zone] zone_02
_L6 · HP 21% · 685g · stash 10/10 · enc_at_time=32_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### [seq=79 use_consumable] zone_02
_L6 · HP 47% · 685g · stash 9/10 · enc_at_time=32_
- use minor_potion on mc_einherjar (HP 39→89/188)

### ENC 32 [zone_02 idx=7] vs swime, slime → **VICTORY** (3 rounds)
_dealt 39, took 13, healed 0_

- **r1** hp ?→78 ap 0 st=— | **SURVIVE** +bonus×4 | took 11 | end [swime=40, slime=76]
- **r2** hp 78→76 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL swime | end [swime=0, slime=37]
- **r3** hp 76→76 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 39 · KILL slime | end [swime=0, slime=0]

### [seq=80 pick_loot] zone_02
_L6 · HP 40% · 750g · stash 9/10 · enc_at_time=33_
- money +65g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=81 use_consumable] zone_02
_L6 · HP 67% · 750g · stash 8/10 · enc_at_time=33_
- use minor_potion on mc_einherjar (HP 76→126/188)

### ENC 33 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 40, took 17, healed 0_

- **r1** hp ?→112 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=22, slime=57, slime=38]
- **r2** hp 112→109 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL slime,mystic_slime · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=0, slime=17, slime=0]
- **r3** hp 109→109 ap 2 st=— | NORMAL basic_attack→slime +bonus×4 | dealt 40 · KILL slime | end [mystic_slime=0, slime=0, slime=0]

### [seq=82 pick_loot] zone_02
_L7 · HP 54% · 847g · stash 8/10 · enc_at_time=34_
- money +97g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=83 use_consumable] zone_02
_L7 · HP 78% · 847g · stash 7/10 · enc_at_time=34_
- use minor_potion on mc_einherjar (HP 109→159/203)

### [seq=84 leave_zone]
_L7 · HP 78% · 847g · stash 7/10 · enc_at_time=34_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=85 enter_town] (in shinto_town)
_L7 · HP 78% · 847g · stash 7/10 · enc_at_time=34_
- enter town shinto_town

### [seq=86 shop_buy] (in shinto_town)
_L7 · HP 78% · 817g · stash 8/10 · enc_at_time=34_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=87 shop_buy] (in shinto_town)
_L7 · HP 78% · 787g · stash 9/10 · enc_at_time=34_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=88 shop_buy] (in shinto_town)
_L7 · HP 78% · 757g · stash 10/10 · enc_at_time=34_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=89 leave_town]
_L7 · HP 78% · 757g · stash 10/10 · enc_at_time=34_
- leave town shinto_town

### [seq=90 enter_zone] zone_02
_L7 · HP 78% · 757g · stash 10/10 · enc_at_time=34_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 34 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 129, took 14, healed 0_

- **r1** hp ?→152 ap 0 st=— | **SURVIVE** +bonus×4 | took 7 · enemy_status(Brace Strike DEF buff→slime), +status(?→self) | end [mystic_slime=48, slime=71, slime=71]
- **r2** hp 152→145 ap 1 st=— | **SURVIVE** +bonus×4 | took 7 · enemy_status(Brace Strike DEF buff→slime), +status(?→self), -status(Hex Disrupt→self) | end [mystic_slime=1, slime=27, slime=27]
- **r3** hp 145→145 ap 2 st=— | **CHEAT(+2AP)** brace_strike→slime +cheat_extras×2 +bonus×4 | dealt 129 · KILL slime,mystic_slime,slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0]

### [seq=91 pick_loot] zone_02
_L7 · HP 71% · 895g · stash 10/10 · enc_at_time=35_
- money +138g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 35 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 153, took 91, healed 0_

- **r1** hp ?→115 ap 0 st=— | **SURVIVE** +bonus×4 | took 30 · +status(Taunted→self) | end [swime=77, mystic_slime=32, chunky_slime=130]
- **r2** hp 115→54 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 84 · took 61 · KILL mystic_slime · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=32, mystic_slime=0, chunky_slime=16]
- **r3** hp 54→54 ap 0 st=— | NORMAL brace_strike→swime +bonus×4 | dealt 69 · KILL swime,chunky_slime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=92 pick_loot] zone_02
_L7 · HP 27% · 994g · stash 10/10 · enc_at_time=36_
- money +99g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=93 use_consumable] zone_02
_L7 · HP 51% · 994g · stash 9/10 · enc_at_time=36_
- use minor_potion on mc_einherjar (HP 54→104/203)

### ENC 36 [zone_02 idx=7] vs chunky_slime, swime → **VICTORY** (3 rounds)
_dealt 136, took 37, healed 0_

- **r1** hp ?→92 ap 0 st=— | **SURVIVE** +bonus×4 | took 12 · +status(Taunted→self) | end [chunky_slime=105, swime=56]
- **r2** hp 92→67 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 90 · took 25 · KILL chunky_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [chunky_slime=0, swime=10]
- **r3** hp 67→67 ap 0 st=— | NORMAL basic_attack→swime +bonus×4 | dealt 46 · KILL swime | end [chunky_slime=0, swime=0]

### [seq=94 pick_loot] zone_02
_L7 · HP 33% · 1050g · stash 9/10 · enc_at_time=37_
- money +56g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=95 use_consumable] zone_02
_L7 · HP 58% · 1050g · stash 8/10 · enc_at_time=37_
- use minor_potion on mc_einherjar (HP 67→117/203)

### ENC 37 [zone_02 idx=7] vs mystic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 84, took 34, healed 0_

- **r1** hp ?→100 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=32, slime=52, slime=52]
- **r2** hp 100→83 ap 1 st=— | **SURVIVE** +bonus×4 | took 17 · KILL mystic_slime · enemy_status(Brace Strike DEF buff→slime) | end [mystic_slime=0, slime=7, slime=7]
- **r3** hp 83→83 ap 2 st=— | **CHEAT(+1AP)** brace_strike→slime +cheat_extras×1 +bonus×4 | dealt 84 · KILL slime,slime · +status(Brace Strike DEF buff→self) | end [mystic_slime=0, slime=0, slime=0]

### [seq=96 pick_loot] zone_02
_L7 · HP 41% · 1152g · stash 8/10 · enc_at_time=38_
- money +102g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=97 use_consumable] zone_02
_L7 · HP 66% · 1152g · stash 7/10 · enc_at_time=38_
- use minor_potion on mc_einherjar (HP 83→133/203)

### [seq=98 leave_zone]
_L7 · HP 66% · 1152g · stash 7/10 · enc_at_time=38_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=99 enter_town] (in shinto_town)
_L7 · HP 66% · 1152g · stash 7/10 · enc_at_time=38_
- enter town shinto_town

### [seq=100 shop_buy] (in shinto_town)
_L7 · HP 66% · 1122g · stash 8/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=101 shop_buy] (in shinto_town)
_L7 · HP 66% · 1092g · stash 9/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=102 shop_buy] (in shinto_town)
_L7 · HP 66% · 1062g · stash 10/10 · enc_at_time=38_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=103 leave_town]
_L7 · HP 66% · 1062g · stash 10/10 · enc_at_time=38_
- leave town shinto_town

### [seq=104 enter_zone] zone_02
_L7 · HP 66% · 1062g · stash 10/10 · enc_at_time=38_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 38 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 154, took 61, healed 0_

- **r1** hp ?→120 ap 0 st=— | **SURVIVE** +bonus×4 | took 13 · +status(Taunted→self) | end [swime=56, mystic_slime=17, chunky_slime=130]
- **r2** hp 120→72 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 84 · took 48 · KILL mystic_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=10, mystic_slime=0, chunky_slime=16]
- **r3** hp 72→72 ap 0 st=— | NORMAL brace_strike→chunky_slime +bonus×4 | dealt 70 · KILL chunky_slime,swime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=105 pick_loot] zone_02
_L8 · HP 33% · 1157g · stash 10/10 · enc_at_time=39_
- money +95g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=106 use_consumable] zone_02
_L8 · HP 56% · 1157g · stash 9/10 · enc_at_time=39_
- use minor_potion on mc_einherjar (HP 72→122/219)

### ENC 39 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 108, took 9, healed 0_

- **r1** hp ?→118 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime), +status(?→self) | end [toxic_slime=22, slime=66, slime=66]
- **r2** hp 118→113 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime · +status(?→self) | end [toxic_slime=0, slime=17, slime=17]
- **r3** hp 113→113 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 108 · KILL slime,slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=107 pick_loot] zone_02
_L8 · HP 52% · 1242g · stash 9/10 · enc_at_time=40_
- money +85g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=108 use_consumable] zone_02
_L8 · HP 74% · 1242g · stash 8/10 · enc_at_time=40_
- use minor_potion on mc_einherjar (HP 113→163/219)

### ENC 40 [zone_02 idx=7] vs slime, slime → **VICTORY** (2 rounds)
_dealt 158, took 2, healed 0_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [slime=47, slime=66]
- **r2** hp 161→161 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 158 · KILL slime,slime | end [slime=0, slime=0]

### [seq=109 pick_loot] zone_02
_L8 · HP 74% · 1296g · stash 8/10 · enc_at_time=41_
- money +54g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 41 [zone_02 idx=7] vs slime, slime → **VICTORY** (2 rounds)
_dealt 106, took 2, healed 0_

- **r1** hp ?→159 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [slime=47, slime=28]
- **r2** hp 159→159 ap 1 st=— | NORMAL thrust→slime +bonus×4 | dealt 106 · KILL slime,slime | end [slime=0, slime=0]

### [seq=110 pick_loot] zone_02
_L8 · HP 73% · 1325g · stash 8/10 · enc_at_time=42_
- money +29g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 42 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (2 rounds)
_dealt 162, took 4, healed 0_

- **r1** hp ?→155 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=35, slime=28, slime=47]
- **r2** hp 155→155 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 162 · KILL slime,slime,toxic_slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=111 pick_loot] zone_02
_L8 · HP 71% · 1387g · stash 8/10 · enc_at_time=43_
- money +62g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 43 [zone_02 idx=7] vs toxic_slime, slime, slime, bandit_slime → **VICTORY** (3 rounds)
_dealt 54, took 9, healed 0_

- **r1** hp ?→150 ap 0 st=— | **SURVIVE** +bonus×4 | took 4 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=22, slime=28, slime=66, bandit_slime=0]
- **r2** hp 150→146 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime | end [toxic_slime=0, slime=0, slime=17, bandit_slime=0]
- **r3** hp 146→146 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [toxic_slime=0, slime=0, slime=0, bandit_slime=0]

### [seq=112 pick_loot] zone_02
_L8 · HP 67% · 1487g · stash 8/10 · enc_at_time=44_
- money +100g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 44 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (2 rounds)
_dealt 109, took 5, healed 0_

- **r1** hp ?→144 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · +status(Taunted→self) | end [swime=30, mystic_slime=43, chunky_slime=130]
- **r2** hp 144→141 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 109 · took 3 · KILL mystic_slime,chunky_slime,swime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=113 pick_loot] zone_02
_L8 · HP 64% · 1546g · stash 8/10 · enc_at_time=45_
- money +59g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 45 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 164, took 28, healed 0_

- **r1** hp ?→116 ap 0 st=— | **SURVIVE** +bonus×4 | took 25 · +status(Taunted→self) | end [swime=72, mystic_slime=12, chunky_slime=130]
- **r2** hp 116→113 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 109 · took 3 · KILL chunky_slime,mystic_slime · +status(Brace Strike DEF buff→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=22, mystic_slime=0, chunky_slime=0]
- **r3** hp 113→113 ap 0 st=— | NORMAL thrust→swime +bonus×4 | dealt 55 · KILL swime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=114 pick_loot] zone_02
_L8 · HP 52% · 1592g · stash 8/10 · enc_at_time=46_
- money +46g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=115 use_consumable] zone_02
_L8 · HP 74% · 1592g · stash 7/10 · enc_at_time=46_
- use minor_potion on mc_einherjar (HP 113→163/219)

### [seq=116 leave_zone]
_L8 · HP 74% · 1592g · stash 7/10 · enc_at_time=46_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=117 enter_town] (in shinto_town)
_L8 · HP 74% · 1592g · stash 7/10 · enc_at_time=46_
- enter town shinto_town

### [seq=118 shop_buy] (in shinto_town)
_L8 · HP 74% · 1562g · stash 8/10 · enc_at_time=46_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=119 shop_buy] (in shinto_town)
_L8 · HP 74% · 1532g · stash 9/10 · enc_at_time=46_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=120 shop_buy] (in shinto_town)
_L8 · HP 74% · 1502g · stash 10/10 · enc_at_time=46_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=121 leave_town]
_L8 · HP 74% · 1502g · stash 10/10 · enc_at_time=46_
- leave town shinto_town

### [seq=122 enter_zone] zone_02
_L8 · HP 74% · 1502g · stash 10/10 · enc_at_time=46_
- enter zone_02 (already_cleared=True, via=sim_decide_zone)

### ENC 46 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 105, took 2, healed 0_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [swime=51, slime=47]
- **r2** hp 161→161 ap 1 st=— | NORMAL thrust→swime +bonus×4 | dealt 105 · KILL swime,slime | end [swime=0, slime=0]

### [seq=123 pick_loot] zone_02
_L8 · HP 74% · 1518g · stash 10/10 · enc_at_time=47_
- money +16g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 47 [zone_02 idx=7] vs slime, slime, bandit_slime → **VICTORY** (2 rounds)
_dealt 159, took 3, healed 0_

- **r1** hp ?→158 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL bandit_slime | end [slime=66, slime=28, bandit_slime=0]
- **r2** hp 158→158 ap 1 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 159 · KILL slime,slime | end [slime=0, slime=0, bandit_slime=0]

### [seq=124 pick_loot] zone_02
_L8 · HP 72% · 1522g · stash 10/10 · enc_at_time=48_
- money +45g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 48 [zone_02 idx=7] vs toxic_slime, slime, slime → **VICTORY** (3 rounds)
_dealt 54, took 6, healed 0_

- **r1** hp ?→155 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=7, slime=28, slime=66]
- **r2** hp 155→152 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 · KILL toxic_slime,slime · enemy_status(Brace Strike DEF buff→slime) | end [toxic_slime=0, slime=0, slime=17]
- **r3** hp 152→152 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 54 · KILL slime | end [toxic_slime=0, slime=0, slime=0]

### [seq=125 pick_loot] zone_02
_L8 · HP 69% · 1548g · stash 10/10 · enc_at_time=49_
- money +26g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 49 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (3 rounds)
_dealt 145, took 62, healed 0_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 11 · +status(?→self), +status(Taunted→self) | end [swime=30, mystic_slime=43, chunky_slime=155]
- **r2** hp 141→90 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 101 · took 51 · KILL mystic_slime,swime · +status(Brace Strike DEF buff→self), -status(Hex Disrupt→self), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=22]
- **r3** hp 90→90 ap 0 st=— | NORMAL thrust→chunky_slime +bonus×4 | dealt 44 · KILL chunky_slime | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=126 pick_loot] zone_02
_L8 · HP 41% · 1570g · stash 10/10 · enc_at_time=50_
- money +22g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=127 use_consumable] zone_02
_L8 · HP 64% · 1570g · stash 9/10 · enc_at_time=50_
- use minor_potion on mc_einherjar (HP 90→140/219)

### ENC 50 [zone_02 idx=7] vs swime, mystic_slime, chunky_slime → **VICTORY** (2 rounds)
_dealt 109, took 5, healed 0_

- **r1** hp ?→138 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · +status(Taunted→self) | end [swime=51, mystic_slime=12, chunky_slime=130]
- **r2** hp 138→135 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 109 · took 3 · KILL swime,chunky_slime,mystic_slime · +status(Brace Strike DEF buff→self) | end [swime=0, mystic_slime=0, chunky_slime=0]

### [seq=128 pick_loot] zone_02
_L8 · HP 62% · 1580g · stash 9/10 · enc_at_time=51_
- money +10g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 51 [zone_02 idx=7] vs swime, slime → **VICTORY** (2 rounds)
_dealt 107, took 2, healed 0_

- **r1** hp ?→133 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [swime=30, slime=47]
- **r2** hp 133→133 ap 1 st=— | NORMAL thrust→slime +bonus×4 | dealt 107 · KILL slime,swime | end [swime=0, slime=0]

### [seq=129 pick_loot] zone_02
_L8 · HP 61% · 1582g · stash 9/10 · enc_at_time=52_
- money +2g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=130 leave_zone]
_L8 · HP 61% · 1582g · stash 9/10 · enc_at_time=52_
- leave zone_02: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=131 enter_zone] zone_03
_L8 · HP 61% · 1582g · stash 9/10 · enc_at_time=52_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 52 [zone_03 idx=0] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 234, took 69, healed 50_

- **r1** hp ?→131 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=250, slime=86, slime=66]
- **r2** hp 131→113 ap 1 st=— | **SURVIVE** +bonus×4 | took 18 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=225, slime=39, slime=17]
- **r3** hp 113→130 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 129 · took 33 · KILL slime,slime | end [brute_oni=120, slime=0, slime=0]
- **r4** hp 130→114 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 | end [brute_oni=95, slime=0, slime=0]
- **r5** hp 114→114 ap 1 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 105 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=132 pick_loot] zone_03
_L9 · HP 49% · 1778g · stash 8/10 · enc_at_time=53_
- money +196g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=133 use_consumable] zone_03
_L9 · HP 70% · 1778g · stash 7/10 · enc_at_time=53_
- use minor_potion on mc_einherjar (HP 114→164/234)

### [seq=134 leave_zone]
_L9 · HP 70% · 1778g · stash 7/10 · enc_at_time=53_
- leave zone_03: reason=sim_post_zone, enc_idx=1, overstay=0, cleared=False

### [seq=135 enter_town] (in shinto_town)
_L9 · HP 70% · 1778g · stash 7/10 · enc_at_time=53_
- enter town shinto_town

### [seq=136 shop_buy] (in shinto_town)
_L9 · HP 70% · 1748g · stash 8/10 · enc_at_time=53_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=137 shop_buy] (in shinto_town)
_L9 · HP 70% · 1718g · stash 9/10 · enc_at_time=53_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=138 shop_buy] (in shinto_town)
_L9 · HP 70% · 1688g · stash 10/10 · enc_at_time=53_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=139 leave_town]
_L9 · HP 70% · 1688g · stash 10/10 · enc_at_time=53_
- leave town shinto_town

### [seq=140 enter_zone] zone_03
_L9 · HP 70% · 1688g · stash 10/10 · enc_at_time=53_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 53 [zone_03 idx=1] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 177, took 26, healed 0_

- **r1** hp ?→141 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=58, slime=81, slime=81]
- **r2** hp 141→138 ap 1 st=— | **SURVIVE** +bonus×4 | took 3 | end [caster_kitsune=1, slime=29, slime=29]
- **r3** hp 138→138 ap 2 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 177 · KILL slime,caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=141 pick_loot] zone_03
_L9 · HP 59% · 1859g · stash 10/10 · enc_at_time=54_
- money +171g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 54 [zone_03 idx=2] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 119, took 18, healed 0_

- **r1** hp ?→135 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 | end [speeder_tengu=86, swime=88, swime=67]
- **r2** hp 135→121 ap 1 st=— | **SURVIVE** +bonus×4 | took 14 | end [speeder_tengu=30, swime=34, swime=12]
- **r3** hp 121→120 ap 2 st=— | **CHEAT(+2AP)** thrust→swime +cheat_extras×2 +bonus×4 | dealt 60 · took 1 · retal 59 · KILL speeder_tengu,swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=142 pick_loot] zone_03
_L9 · HP 51% · 2015g · stash 10/10 · enc_at_time=55_
- money +156g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=143 recruit_accept] zone_03
_L9 · HP 51% · 2015g · stash 10/10 · enc_at_time=55_
- recruit_accept: Martyr Recruit (martyr L5) id=recruit_martyr_8311

### [seq=144 use_consumable] zone_03
_L9 · HP 73% · 2015g · stash 9/10 · enc_at_time=55_
- use minor_potion on mc_einherjar (HP 120→170/234)

### ENC 55 [zone_03 idx=3] vs support_tanuki, brute_oni, bandit_slime → **VICTORY** (8 rounds)
_dealt 303, took 354, healed 150, deaths: ['recruit_martyr_8311']_

- **r1** hp ?→144 ap 0 st=— | **SURVIVE** +bonus×4 | took 26 · KILL bandit_slime | end [support_tanuki=191, brute_oni=358, bandit_slime=0]
- **r2** hp 144→119 ap 1 st=— | **SURVIVE** +bonus×4 | took 25 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=191, brute_oni=340, bandit_slime=0]
- **r3** hp 119→117 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 126 · took 52 | end [support_tanuki=87, brute_oni=254, bandit_slime=0]
- **r4** hp 117→117 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=144, brute_oni=193, bandit_slime=0]
- **r5** hp 117→117 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→brute_oni) | end [support_tanuki=144, brute_oni=132, bandit_slime=0]
- **r6** hp 117→167 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 134 | end [support_tanuki=22, brute_oni=99, bandit_slime=0]
- **r7** hp 167→167 ap 0 st=— | **SURVIVE** +bonus×4 | KILL support_tanuki,recruit_martyr | end [support_tanuki=0, brute_oni=27, bandit_slime=0]
- **r8** hp 167→167 ap 1 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 37 · KILL brute_oni | end [support_tanuki=0, brute_oni=0, bandit_slime=0]

### [seq=145 pick_loot] zone_03
_L10 · HP 67% · 2234g · stash 7/10 · enc_at_time=56_
- money +296g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=146 leave_zone]
_L10 · HP 67% · 2234g · stash 7/10 · enc_at_time=56_
- leave zone_03: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=147 enter_town] (in shinto_town)
_L10 · HP 67% · 2234g · stash 7/10 · enc_at_time=56_
- enter town shinto_town

### [seq=148 shop_buy] (in shinto_town)
_L10 · HP 67% · 2204g · stash 8/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=149 shop_buy] (in shinto_town)
_L10 · HP 67% · 2174g · stash 9/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=150 shop_buy] (in shinto_town)
_L10 · HP 67% · 2144g · stash 10/10 · enc_at_time=56_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=151 leave_town]
_L10 · HP 67% · 2144g · stash 10/10 · enc_at_time=56_
- leave town shinto_town

### [seq=152 enter_zone] zone_03
_L10 · HP 67% · 2144g · stash 10/10 · enc_at_time=56_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### ENC 56 [zone_03 idx=4] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 191, took 160, healed 50_

- **r1** hp ?→155 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(?→recruit_martyr), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=86, speeder_tengu=99, slime=95]
- **r2** hp 155→144 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=39, speeder_tengu=18, slime=87]
- **r3** hp 144→134 ap 2 st=— | **SURVIVE** +bonus×4 | KILL speeder_tengu · -status(Searing Edge DOT→self) | end [caster_kitsune=35, speeder_tengu=0, slime=77]
- **r4** hp 134→134 ap 3 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 189 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=153 pick_loot] zone_03
_L10 · HP 54% · 2304g · stash 9/10 · enc_at_time=57_
- money +160g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=154 use_consumable] zone_03
_L10 · HP 74% · 2304g · stash 8/10 · enc_at_time=57_
- use minor_potion on mc_einherjar (HP 134→184/250)

### ENC 57 [zone_03 idx=5] vs brute_oni, support_tanuki, slime, slime, bandit_slime → **VICTORY** (7 rounds)
_dealt 392, took 214, healed 100_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=307, support_tanuki=168, slime=76, slime=142, bandit_slime=0]
- **r2** hp 161→140 ap 1 st=— | **SURVIVE** +bonus×4 | took 21 | end [brute_oni=280, support_tanuki=168, slime=120, slime=134, bandit_slime=0]
- **r3** hp 140→119 ap 2 st=— | **SURVIVE** +bonus×4 | took 21 · enemy_status(Rally buff→support_tanuki) | end [brute_oni=251, support_tanuki=168, slime=113, slime=126, bandit_slime=0]
- **r4** hp 119→126 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 192 · took 43 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=140, support_tanuki=168, slime=47, slime=70, bandit_slime=0]
- **r5** hp 126→103 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 · KILL slime | end [brute_oni=113, support_tanuki=156, slime=0, slime=14, bandit_slime=0]
- **r6** hp 103→80 ap 1 st=— | **SURVIVE** +bonus×4 | took 23 · KILL slime | end [brute_oni=86, support_tanuki=98, slime=0, slime=0, bandit_slime=0]
- **r7** hp 80→80 ap 2 st=— | **CHEAT(+2AP)** thrust→support_tanuki +cheat_extras×2 +bonus×4 | dealt 198 · KILL support_tanuki,brute_oni | end [brute_oni=0, support_tanuki=0, slime=0, slime=0, bandit_slime=0]

### [seq=155 pick_loot] zone_03
_L11 · HP 30% · 2575g · stash 6/10 · enc_at_time=58_
- money +449g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=156 use_consumable] zone_03
_L11 · HP 49% · 2575g · stash 5/10 · enc_at_time=58_
- use minor_potion on mc_einherjar (HP 80→130/265)

### [seq=157 leave_zone]
_L11 · HP 49% · 2575g · stash 5/10 · enc_at_time=58_
- leave zone_03: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=158 enter_town] (in shinto_town)
_L11 · HP 49% · 2575g · stash 5/10 · enc_at_time=58_
- enter town shinto_town

### [seq=159 shop_buy] (in shinto_town)
_L11 · HP 49% · 2545g · stash 6/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=160 shop_buy] (in shinto_town)
_L11 · HP 49% · 2515g · stash 7/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=161 shop_buy] (in shinto_town)
_L11 · HP 49% · 2485g · stash 8/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=162 shop_buy] (in shinto_town)
_L11 · HP 49% · 2455g · stash 9/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=163 shop_buy] (in shinto_town)
_L11 · HP 49% · 2425g · stash 10/10 · enc_at_time=58_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g]

### [seq=164 leave_town]
_L11 · HP 49% · 2425g · stash 10/10 · enc_at_time=58_
- leave town shinto_town

### [seq=165 enter_zone] zone_03
_L11 · HP 49% · 2425g · stash 10/10 · enc_at_time=58_
- enter zone_03 (already_cleared=False, via=sim_decide_zone)

### [seq=166 use_consumable] zone_03
_L11 · HP 68% · 2425g · stash 9/10 · enc_at_time=58_
- use minor_potion on mc_einherjar (HP 130→180/265)

### [seq=167 use_consumable] zone_03
_L11 · HP 68% · 2425g · stash 8/10 · enc_at_time=58_
- use minor_potion on recruit_martyr_8311 (HP 88→138/175)

### ENC 58 [zone_03 idx=6] vs kodama_elder → **VICTORY** (9 rounds)
_dealt 471, took 109, healed 100_

- **r1** hp ?→180 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=381, kodama=87, kodama=87]
- **r2** hp 180→156 ap 1 st=— | **SURVIVE** +bonus×4 | took 24 | end [kodama_elder=322, kodama=87, kodama=87]
- **r3** hp 156→156 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=275, kodama=87, kodama=87]
- **r4** hp 156→156 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=231, kodama=87, kodama=87]
- **r5** hp 156→156 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→kodama_elder) | end [kodama_elder=235, kodama=87, kodama=87]
- **r6** hp 156→125 ap 3 st=— | **SURVIVE** +bonus×4 | took 31 | end [kodama_elder=183, kodama=87, kodama=87]
- **r7** hp 125→175 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 263 · KILL kodama_elder | end [kodama_elder=0, kodama=22, kodama=87]
- **r8** hp 175→175 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kodama_elder=0, kodama=22, kodama=87]
- **r9** hp 175→175 ap 1 st=— | **CHEAT(+1AP)** thrust→kodama +cheat_extras×1 +bonus×4 | dealt 205 · KILL kodama,kodama | end [kodama_elder=0, kodama=0, kodama=0]

### [seq=168 pick_loot] zone_03
_L11 · HP 66% · 2789g · stash 10/10 · enc_at_time=59_
- money +364g, offered=['potion', 'cast_quick_strike', 'cast_brace_strike', 'leech_fang'], **selected**=['potion', 'cast_quick_strike', 'cast_brace_strike', 'leech_fang'], skipped=[], discarded_stash=[]

### ENC 59 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (4 rounds)
_dealt 328, took 37, healed 0_

- **r1** hp ?→173 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [brute_oni=241, slime=49, slime=108]
- **r2** hp 173→172 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime | end [brute_oni=195, slime=0, slime=101]
- **r3** hp 172→172 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=186, slime=0, slime=94]
- **r4** hp 172→172 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 328 · KILL slime,brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=169 pick_loot] zone_03
_L11 · HP 65% · 2940g · stash 10/10 · enc_at_time=60_
- money +151g, offered=['spd_tonic'], **selected**=[], skipped=['spd_tonic'], discarded_stash=[]

### ENC 60 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 284, took 214, healed 50, deaths: ['recruit_martyr_8311']_

- **r1** hp ?→157 ap 0 st=— | **SURVIVE** +bonus×4 | took 15 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=180, brute_oni=256]
- **r2** hp 157→157 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=180, brute_oni=241]
- **r3** hp 157→157 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=132, brute_oni=188]
- **r4** hp 157→142 ap 3 st=— | **SURVIVE** +bonus×4 | took 15 · KILL recruit_martyr | end [support_tanuki=98, brute_oni=152]
- **r5** hp 142→111 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 278 · took 31 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=170 pick_loot] zone_03
_L11 · HP 42% · 3070g · stash 9/10 · enc_at_time=61_
- money +130g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=171 leave_zone]
_L11 · HP 42% · 3070g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=172 enter_town] (in shinto_town)
_L11 · HP 42% · 3070g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=173 shop_buy] (in shinto_town)
_L11 · HP 42% · 3040g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=174 leave_town]
_L11 · HP 42% · 3040g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=175 enter_zone] zone_03
_L11 · HP 42% · 3040g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=176 use_consumable] zone_03
_L11 · HP 61% · 3040g · stash 9/10 · enc_at_time=61_
- use minor_potion on mc_einherjar (HP 111→161/265)

### [seq=177 leave_zone]
_L11 · HP 61% · 3040g · stash 9/10 · enc_at_time=61_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=2, cleared=True

### [seq=178 enter_town] (in shinto_town)
_L11 · HP 61% · 3040g · stash 9/10 · enc_at_time=61_
- enter town shinto_town

### [seq=179 shop_buy] (in shinto_town)
_L11 · HP 61% · 3010g · stash 10/10 · enc_at_time=61_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=180 leave_town]
_L11 · HP 61% · 3010g · stash 10/10 · enc_at_time=61_
- leave town shinto_town

### [seq=181 enter_zone] zone_03
_L11 · HP 61% · 3010g · stash 10/10 · enc_at_time=61_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 61 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 0, took 164, healed 0_

- **r1** hp ?→99 ap 0 st=— | **SURVIVE** +bonus×4 | took 52 · enemy_status(?→recruit_martyr), +status(?→self) | end [speeder_tengu=94, swime=36, swime=63]
- **r2** hp 99→83 ap 1 st=— | **SURVIVE** +bonus×4 | took 6 · KILL swime,swime | end [speeder_tengu=8, swime=0, swime=0]
- **r3** hp 83→83 ap 2 st=— | NORMAL thrust→speeder_tengu +bonus×4 | KILL speeder_tengu · enemy_status(?→recruit_martyr) | end [speeder_tengu=0, swime=0, swime=0]

### [seq=182 pick_loot] zone_03
_L12 · HP 30% · 3244g · stash 10/10 · enc_at_time=62_
- money +234g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=183 leave_zone]
_L12 · HP 30% · 3244g · stash 10/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=184 enter_town] (in shinto_town)
_L12 · HP 30% · 3244g · stash 10/10 · enc_at_time=62_
- enter town shinto_town

### [seq=185 leave_town]
_L12 · HP 30% · 3244g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=186 enter_zone] zone_03
_L12 · HP 30% · 3244g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=187 use_consumable] zone_03
_L12 · HP 30% · 3244g · stash 9/10 · enc_at_time=62_
- use minor_potion on recruit_martyr_8311 (HP 14→64/196)

### [seq=188 leave_zone]
_L12 · HP 30% · 3244g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=189 enter_town] (in shinto_town)
_L12 · HP 30% · 3244g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=190 shop_buy] (in shinto_town)
_L12 · HP 30% · 3214g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=191 leave_town]
_L12 · HP 30% · 3214g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=192 enter_zone] zone_03
_L12 · HP 30% · 3214g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=193 use_consumable] zone_03
_L12 · HP 47% · 3214g · stash 9/10 · enc_at_time=62_
- use minor_potion on mc_einherjar (HP 83→133/281)

### [seq=194 leave_zone]
_L12 · HP 47% · 3214g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=195 enter_town] (in shinto_town)
_L12 · HP 47% · 3214g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=196 shop_buy] (in shinto_town)
_L12 · HP 47% · 3184g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=197 leave_town]
_L12 · HP 47% · 3184g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=198 enter_zone] zone_03
_L12 · HP 47% · 3184g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=199 use_consumable] zone_03
_L12 · HP 47% · 3184g · stash 9/10 · enc_at_time=62_
- use minor_potion on recruit_martyr_8311 (HP 64→114/196)

### [seq=200 leave_zone]
_L12 · HP 47% · 3184g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=201 enter_town] (in shinto_town)
_L12 · HP 47% · 3184g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=202 shop_buy] (in shinto_town)
_L12 · HP 47% · 3154g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=203 leave_town]
_L12 · HP 47% · 3154g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=204 enter_zone] zone_03
_L12 · HP 47% · 3154g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=205 use_consumable] zone_03
_L12 · HP 65% · 3154g · stash 9/10 · enc_at_time=62_
- use minor_potion on mc_einherjar (HP 133→183/281)

### [seq=206 leave_zone]
_L12 · HP 65% · 3154g · stash 9/10 · enc_at_time=62_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=3, cleared=True

### [seq=207 enter_town] (in shinto_town)
_L12 · HP 65% · 3154g · stash 9/10 · enc_at_time=62_
- enter town shinto_town

### [seq=208 shop_buy] (in shinto_town)
_L12 · HP 65% · 3124g · stash 10/10 · enc_at_time=62_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=209 leave_town]
_L12 · HP 65% · 3124g · stash 10/10 · enc_at_time=62_
- leave town shinto_town

### [seq=210 enter_zone] zone_03
_L12 · HP 65% · 3124g · stash 10/10 · enc_at_time=62_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 62 [zone_03 idx=7] vs brute_oni, support_tanuki, slime, slime, bandit_slime → **VICTORY** (6 rounds)
_dealt 430, took 132, healed 50_

- **r1** hp ?→171 ap 0 st=— | **SURVIVE** +bonus×4 | took 12 | end [brute_oni=323, support_tanuki=85, slime=126, slime=126, bandit_slime=45]
- **r2** hp 171→152 ap 1 st=— | **SURVIVE** +bonus×4 | took 19 · KILL bandit_slime · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=286, support_tanuki=123, slime=117, slime=117, bandit_slime=0]
- **r3** hp 152→165 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 177 · took 37 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Rally buff→support_tanuki) | end [brute_oni=139, support_tanuki=123, slime=41, slime=110, bandit_slime=0]
- **r4** hp 165→145 ap 0 st=— | **SURVIVE** +bonus×4 | took 20 · KILL slime | end [brute_oni=140, support_tanuki=123, slime=0, slime=43, bandit_slime=0]
- **r5** hp 145→144 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=83, support_tanuki=53, slime=0, slime=36, bandit_slime=0]
- **r6** hp 144→144 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 253 · KILL brute_oni,slime,support_tanuki | end [brute_oni=0, support_tanuki=0, slime=0, slime=0, bandit_slime=0]

### [seq=211 pick_loot] zone_03
_L12 · HP 51% · 3418g · stash 9/10 · enc_at_time=63_
- money +294g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=212 leave_zone]
_L12 · HP 51% · 3418g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=213 enter_town] (in shinto_town)
_L12 · HP 51% · 3418g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=214 shop_buy] (in shinto_town)
_L12 · HP 51% · 3388g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=215 leave_town]
_L12 · HP 51% · 3388g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=216 enter_zone] zone_03
_L12 · HP 51% · 3388g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=217 use_consumable] zone_03
_L12 · HP 51% · 3388g · stash 9/10 · enc_at_time=63_
- use minor_potion on recruit_martyr_8311 (HP 71→121/196)

### [seq=218 leave_zone]
_L12 · HP 51% · 3388g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=219 enter_town] (in shinto_town)
_L12 · HP 51% · 3388g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=220 shop_buy] (in shinto_town)
_L12 · HP 51% · 3358g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=221 leave_town]
_L12 · HP 51% · 3358g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=222 enter_zone] zone_03
_L12 · HP 51% · 3358g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=223 use_consumable] zone_03
_L12 · HP 69% · 3358g · stash 9/10 · enc_at_time=63_
- use minor_potion on mc_einherjar (HP 144→194/281)

### [seq=224 leave_zone]
_L12 · HP 69% · 3358g · stash 9/10 · enc_at_time=63_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=4, cleared=True

### [seq=225 enter_town] (in shinto_town)
_L12 · HP 69% · 3358g · stash 9/10 · enc_at_time=63_
- enter town shinto_town

### [seq=226 shop_buy] (in shinto_town)
_L12 · HP 69% · 3328g · stash 10/10 · enc_at_time=63_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=227 leave_town]
_L12 · HP 69% · 3328g · stash 10/10 · enc_at_time=63_
- leave town shinto_town

### [seq=228 enter_zone] zone_03
_L12 · HP 69% · 3328g · stash 10/10 · enc_at_time=63_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 63 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 330, took 175, healed 50_

- **r1** hp ?→180 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 | end [support_tanuki=191, brute_oni=251]
- **r2** hp 180→166 ap 1 st=— | **SURVIVE** +bonus×4 | took 14 | end [support_tanuki=230, brute_oni=210]
- **r3** hp 166→166 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=189, brute_oni=158]
- **r4** hp 166→166 ap 3 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→brute_oni) | end [support_tanuki=189, brute_oni=107]
- **r5** hp 166→166 ap 3 st=— | **CHEAT(+3AP)** thrust→support_tanuki +cheat_extras×3 +bonus×4 | dealt 327 · KILL brute_oni,support_tanuki | end [support_tanuki=0, brute_oni=0]

### [seq=229 pick_loot] zone_03
_L12 · HP 59% · 3476g · stash 9/10 · enc_at_time=64_
- money +148g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=230 leave_zone]
_L12 · HP 59% · 3476g · stash 9/10 · enc_at_time=64_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=231 enter_town] (in shinto_town)
_L12 · HP 59% · 3476g · stash 9/10 · enc_at_time=64_
- enter town shinto_town

### [seq=232 shop_buy] (in shinto_town)
_L12 · HP 59% · 3446g · stash 10/10 · enc_at_time=64_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=233 leave_town]
_L12 · HP 59% · 3446g · stash 10/10 · enc_at_time=64_
- leave town shinto_town

### [seq=234 enter_zone] zone_03
_L12 · HP 59% · 3446g · stash 10/10 · enc_at_time=64_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=235 use_consumable] zone_03
_L12 · HP 59% · 3446g · stash 9/10 · enc_at_time=64_
- use minor_potion on recruit_martyr_8311 (HP 24→74/196)

### [seq=236 leave_zone]
_L12 · HP 59% · 3446g · stash 9/10 · enc_at_time=64_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=237 enter_town] (in shinto_town)
_L12 · HP 59% · 3446g · stash 9/10 · enc_at_time=64_
- enter town shinto_town

### [seq=238 shop_buy] (in shinto_town)
_L12 · HP 59% · 3416g · stash 10/10 · enc_at_time=64_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=239 leave_town]
_L12 · HP 59% · 3416g · stash 10/10 · enc_at_time=64_
- leave town shinto_town

### [seq=240 enter_zone] zone_03
_L12 · HP 59% · 3416g · stash 10/10 · enc_at_time=64_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=241 use_consumable] zone_03
_L12 · HP 59% · 3416g · stash 9/10 · enc_at_time=64_
- use minor_potion on recruit_martyr_8311 (HP 74→124/196)

### [seq=242 leave_zone]
_L12 · HP 59% · 3416g · stash 9/10 · enc_at_time=64_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=5, cleared=True

### [seq=243 enter_town] (in shinto_town)
_L12 · HP 59% · 3416g · stash 9/10 · enc_at_time=64_
- enter town shinto_town

### [seq=244 shop_buy] (in shinto_town)
_L12 · HP 59% · 3386g · stash 10/10 · enc_at_time=64_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=245 leave_town]
_L12 · HP 59% · 3386g · stash 10/10 · enc_at_time=64_
- leave town shinto_town

### [seq=246 enter_zone] zone_03
_L12 · HP 59% · 3386g · stash 10/10 · enc_at_time=64_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 64 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 219, took 38, healed 0_

- **r1** hp ?→163 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(?→recruit_martyr) | end [caster_kitsune=123, speeder_tengu=9, slime=46]
- **r2** hp 163→163 ap 1 st=— | **SURVIVE** +bonus×4 | KILL speeder_tengu · enemy_status(?→recruit_martyr) | end [caster_kitsune=95, speeder_tengu=0, slime=39]
- **r3** hp 163→163 ap 2 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 219 · KILL caster_kitsune,slime | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=247 pick_loot] zone_03
_L12 · HP 58% · 3522g · stash 10/10 · enc_at_time=65_
- money +136g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=248 use_consumable] zone_03
_L12 · HP 58% · 3522g · stash 9/10 · enc_at_time=65_
- use minor_potion on recruit_martyr_8311 (HP 89→139/217)

### [seq=249 leave_zone]
_L12 · HP 58% · 3522g · stash 9/10 · enc_at_time=65_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=6, cleared=True

### [seq=250 enter_town] (in shinto_town)
_L12 · HP 58% · 3522g · stash 9/10 · enc_at_time=65_
- enter town shinto_town

### [seq=251 shop_buy] (in shinto_town)
_L12 · HP 58% · 3492g · stash 10/10 · enc_at_time=65_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=252 leave_town]
_L12 · HP 58% · 3492g · stash 10/10 · enc_at_time=65_
- leave town shinto_town

### [seq=253 enter_zone] zone_03
_L12 · HP 58% · 3492g · stash 10/10 · enc_at_time=65_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 65 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 150, took 40, healed 0_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [caster_kitsune=99, speeder_tengu=72, slime=46]
- **r2** hp 161→159 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · KILL speeder_tengu,slime | end [caster_kitsune=95, speeder_tengu=0, slime=0]
- **r3** hp 159→159 ap 2 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 150 · KILL caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=254 pick_loot] zone_03
_L12 · HP 57% · 3583g · stash 10/10 · enc_at_time=66_
- money +91g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=255 use_consumable] zone_03
_L12 · HP 57% · 3583g · stash 9/10 · enc_at_time=66_
- use minor_potion on recruit_martyr_8311 (HP 103→153/217)

### [seq=256 leave_zone]
_L12 · HP 57% · 3583g · stash 9/10 · enc_at_time=66_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=7, cleared=True

### [seq=257 enter_town] (in shinto_town)
_L12 · HP 57% · 3583g · stash 9/10 · enc_at_time=66_
- enter town shinto_town

### [seq=258 shop_buy] (in shinto_town)
_L12 · HP 57% · 3553g · stash 10/10 · enc_at_time=66_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=259 leave_town]
_L12 · HP 57% · 3553g · stash 10/10 · enc_at_time=66_
- leave town shinto_town

### [seq=260 enter_zone] zone_03
_L12 · HP 57% · 3553g · stash 10/10 · enc_at_time=66_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 66 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (4 rounds)
_dealt 281, took 20, healed 50_

- **r1** hp ?→157 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [brute_oni=251, slime=108, slime=66]
- **r2** hp 157→141 ap 1 st=— | **SURVIVE** +bonus×4 | took 16 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=210, slime=39, slime=0]
- **r3** hp 141→191 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 183 · KILL slime | end [brute_oni=86, slime=0, slime=0]
- **r4** hp 191→191 ap 0 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 98 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=261 pick_loot] zone_03
_L13 · HP 65% · 3710g · stash 9/10 · enc_at_time=67_
- money +157g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=262 leave_zone]
_L13 · HP 65% · 3710g · stash 9/10 · enc_at_time=67_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=8, cleared=True

### [seq=263 enter_town] (in shinto_town)
_L13 · HP 65% · 3710g · stash 9/10 · enc_at_time=67_
- enter town shinto_town

### [seq=264 shop_buy] (in shinto_town)
_L13 · HP 65% · 3680g · stash 10/10 · enc_at_time=67_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=265 leave_town]
_L13 · HP 65% · 3680g · stash 10/10 · enc_at_time=67_
- leave town shinto_town

### [seq=266 enter_zone] zone_03
_L13 · HP 65% · 3680g · stash 10/10 · enc_at_time=67_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 67 [zone_03 idx=7] vs brute_oni, support_tanuki, slime, slime → **VICTORY** (7 rounds)
_dealt 508, took 124, healed 50_

- **r1** hp ?→157 ap 0 st=— | **SURVIVE** +bonus×4 | took 34 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=338, support_tanuki=106, slime=99, slime=143]
- **r2** hp 157→155 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime), enemy_status(Brace Strike DEF buff→slime), enemy_status(Rally buff→slime) | end [brute_oni=277, support_tanuki=106, slime=29, slime=72]
- **r3** hp 155→205 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 184 · KILL slime | end [brute_oni=196, support_tanuki=106, slime=0, slime=64]
- **r4** hp 205→191 ap 0 st=— | **SURVIVE** +bonus×4 | took 14 · KILL slime | end [brute_oni=135, support_tanuki=32, slime=0, slime=0]
- **r5** hp 191→191 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=123, support_tanuki=77, slime=0, slime=0]
- **r6** hp 191→191 ap 2 st=— | **CHEAT(+2AP)** thrust→brute_oni +cheat_extras×2 +bonus×4 | dealt 245 · KILL brute_oni · enemy_status(Rally buff→support_tanuki) | end [brute_oni=0, support_tanuki=3, slime=0, slime=0]
- **r7** hp 191→191 ap 0 st=— | NORMAL thrust→support_tanuki +bonus×4 | dealt 79 · KILL support_tanuki | end [brute_oni=0, support_tanuki=0, slime=0, slime=0]

### [seq=267 pick_loot] zone_03
_L13 · HP 65% · 3880g · stash 9/10 · enc_at_time=68_
- money +200g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=268 leave_zone]
_L13 · HP 65% · 3880g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=269 enter_town] (in shinto_town)
_L13 · HP 65% · 3880g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=270 shop_buy] (in shinto_town)
_L13 · HP 65% · 3850g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=271 leave_town]
_L13 · HP 65% · 3850g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=272 enter_zone] zone_03
_L13 · HP 65% · 3850g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=273 use_consumable] zone_03
_L13 · HP 65% · 3850g · stash 9/10 · enc_at_time=68_
- use minor_potion on recruit_martyr_8311 (HP 77→127/238)

### [seq=274 leave_zone]
_L13 · HP 65% · 3850g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=275 enter_town] (in shinto_town)
_L13 · HP 65% · 3850g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=276 shop_buy] (in shinto_town)
_L13 · HP 65% · 3820g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=277 leave_town]
_L13 · HP 65% · 3820g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=278 enter_zone] zone_03
_L13 · HP 65% · 3820g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=279 use_consumable] zone_03
_L13 · HP 65% · 3820g · stash 9/10 · enc_at_time=68_
- use minor_potion on recruit_martyr_8311 (HP 127→177/238)

### [seq=280 leave_zone]
_L13 · HP 65% · 3820g · stash 9/10 · enc_at_time=68_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=9, cleared=True

### [seq=281 enter_town] (in shinto_town)
_L13 · HP 65% · 3820g · stash 9/10 · enc_at_time=68_
- enter town shinto_town

### [seq=282 shop_buy] (in shinto_town)
_L13 · HP 65% · 3790g · stash 10/10 · enc_at_time=68_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=283 leave_town]
_L13 · HP 65% · 3790g · stash 10/10 · enc_at_time=68_
- leave town shinto_town

### [seq=284 enter_zone] zone_03
_L13 · HP 65% · 3790g · stash 10/10 · enc_at_time=68_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 68 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (4 rounds)
_dealt 147, took 66, healed 0_

- **r1** hp ?→190 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [caster_kitsune=73, slime=99, slime=143]
- **r2** hp 190→190 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [caster_kitsune=31, slime=90, slime=135]
- **r3** hp 190→188 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · KILL caster_kitsune · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=0, slime=20, slime=64]
- **r4** hp 188→188 ap 3 st=— | NORMAL thrust→slime +bonus×4 | dealt 147 · KILL slime,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=285 pick_loot] zone_03
_L13 · HP 64% · 3931g · stash 10/10 · enc_at_time=69_
- money +141g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=286 use_consumable] zone_03
_L13 · HP 64% · 3931g · stash 9/10 · enc_at_time=69_
- use minor_potion on recruit_martyr_8311 (HP 114→164/238)

### [seq=287 leave_zone]
_L13 · HP 64% · 3931g · stash 9/10 · enc_at_time=69_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=10, cleared=True

### [seq=288 enter_town] (in shinto_town)
_L13 · HP 64% · 3931g · stash 9/10 · enc_at_time=69_
- enter town shinto_town

### [seq=289 shop_buy] (in shinto_town)
_L13 · HP 64% · 3901g · stash 10/10 · enc_at_time=69_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=290 leave_town]
_L13 · HP 64% · 3901g · stash 10/10 · enc_at_time=69_
- leave town shinto_town

### [seq=291 enter_zone] zone_03
_L13 · HP 64% · 3901g · stash 10/10 · enc_at_time=69_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 69 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 299, took 90, healed 50_

- **r1** hp ?→186 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 | end [brute_oni=341, slime=41, slime=80]
- **r2** hp 186→165 ap 1 st=— | **SURVIVE** +bonus×4 | took 21 · KILL slime | end [brute_oni=303, slime=0, slime=72]
- **r3** hp 165→145 ap 2 st=— | **SURVIVE** +bonus×4 | took 20 | end [brute_oni=265, slime=0, slime=64]
- **r4** hp 145→195 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 242 · KILL slime | end [brute_oni=33, slime=0, slime=0]
- **r5** hp 195→195 ap 0 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 57 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=292 pick_loot] zone_03
_L13 · HP 66% · 4027g · stash 9/10 · enc_at_time=70_
- money +126g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=293 leave_zone]
_L13 · HP 66% · 4027g · stash 9/10 · enc_at_time=70_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=11, cleared=True

### [seq=294 enter_town] (in shinto_town)
_L13 · HP 66% · 4027g · stash 9/10 · enc_at_time=70_
- enter town shinto_town

### [seq=295 shop_buy] (in shinto_town)
_L13 · HP 66% · 3997g · stash 10/10 · enc_at_time=70_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=296 leave_town]
_L13 · HP 66% · 3997g · stash 10/10 · enc_at_time=70_
- leave town shinto_town

### [seq=297 enter_zone] zone_03
_L13 · HP 66% · 3997g · stash 10/10 · enc_at_time=70_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=298 use_consumable] zone_03
_L13 · HP 66% · 3997g · stash 9/10 · enc_at_time=70_
- use minor_potion on recruit_martyr_8311 (HP 117→167/238)

### [seq=299 leave_zone]
_L13 · HP 66% · 3997g · stash 9/10 · enc_at_time=70_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=11, cleared=True

### [seq=300 enter_town] (in shinto_town)
_L13 · HP 66% · 3997g · stash 9/10 · enc_at_time=70_
- enter town shinto_town

### [seq=301 shop_buy] (in shinto_town)
_L13 · HP 66% · 3967g · stash 10/10 · enc_at_time=70_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=302 leave_town]
_L13 · HP 66% · 3967g · stash 10/10 · enc_at_time=70_
- leave town shinto_town

### [seq=303 enter_zone] zone_03
_L13 · HP 66% · 3967g · stash 10/10 · enc_at_time=70_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 70 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (6 rounds)
_dealt 293, took 165, healed 50_

- **r1** hp ?→175 ap 0 st=— | **SURVIVE** +bonus×4 | took 20 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=180, brute_oni=338]
- **r2** hp 175→175 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=136, brute_oni=277]
- **r3** hp 175→155 ap 2 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=133, brute_oni=282]
- **r4** hp 155→135 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=133, brute_oni=244]
- **r5** hp 135→115 ap 3 st=— | **SURVIVE** +bonus×4 | took 20 | end [support_tanuki=59, brute_oni=183]
- **r6** hp 115→115 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 288 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=304 pick_loot] zone_03
_L13 · HP 39% · 4031g · stash 9/10 · enc_at_time=71_
- money +64g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=305 leave_zone]
_L13 · HP 39% · 4031g · stash 9/10 · enc_at_time=71_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=306 enter_town] (in shinto_town)
_L13 · HP 39% · 4031g · stash 9/10 · enc_at_time=71_
- enter town shinto_town

### [seq=307 shop_buy] (in shinto_town)
_L13 · HP 39% · 4001g · stash 10/10 · enc_at_time=71_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=308 leave_town]
_L13 · HP 39% · 4001g · stash 10/10 · enc_at_time=71_
- leave town shinto_town

### [seq=309 enter_zone] zone_03
_L13 · HP 39% · 4001g · stash 10/10 · enc_at_time=71_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=310 use_consumable] zone_03
_L13 · HP 56% · 4001g · stash 9/10 · enc_at_time=71_
- use minor_potion on mc_einherjar (HP 115→165/296)

### [seq=311 leave_zone]
_L13 · HP 56% · 4001g · stash 9/10 · enc_at_time=71_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=12, cleared=True

### [seq=312 enter_town] (in shinto_town)
_L13 · HP 56% · 4001g · stash 9/10 · enc_at_time=71_
- enter town shinto_town

### [seq=313 shop_buy] (in shinto_town)
_L13 · HP 56% · 3971g · stash 10/10 · enc_at_time=71_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=314 leave_town]
_L13 · HP 56% · 3971g · stash 10/10 · enc_at_time=71_
- leave town shinto_town

### [seq=315 enter_zone] zone_03
_L13 · HP 56% · 3971g · stash 10/10 · enc_at_time=71_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 71 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (5 rounds)
_dealt 281, took 159, healed 50_

- **r1** hp ?→147 ap 0 st=— | **SURVIVE** +bonus×4 | took 18 | end [support_tanuki=158, brute_oni=364]
- **r2** hp 147→147 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=119, brute_oni=303]
- **r3** hp 147→197 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 186 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=47, brute_oni=128]
- **r4** hp 197→172 ap 0 st=— | **SURVIVE** +bonus×4 | took 25 · KILL support_tanuki | end [support_tanuki=0, brute_oni=67]
- **r5** hp 172→172 ap 1 st=— | NORMAL thrust→brute_oni +bonus×4 | dealt 95 · KILL brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=316 pick_loot] zone_03
_L13 · HP 58% · 4049g · stash 9/10 · enc_at_time=72_
- money +78g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=317 leave_zone]
_L13 · HP 58% · 4049g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=318 enter_town] (in shinto_town)
_L13 · HP 58% · 4049g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=319 shop_buy] (in shinto_town)
_L13 · HP 58% · 4019g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=320 leave_town]
_L13 · HP 58% · 4019g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=321 enter_zone] zone_03
_L13 · HP 58% · 4019g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=322 use_consumable] zone_03
_L13 · HP 58% · 4019g · stash 9/10 · enc_at_time=72_
- use minor_potion on recruit_martyr_8311 (HP 16→66/238)

### [seq=323 leave_zone]
_L13 · HP 58% · 4019g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=324 enter_town] (in shinto_town)
_L13 · HP 58% · 4019g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=325 shop_buy] (in shinto_town)
_L13 · HP 58% · 3989g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=326 leave_town]
_L13 · HP 58% · 3989g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=327 enter_zone] zone_03
_L13 · HP 58% · 3989g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=328 use_consumable] zone_03
_L13 · HP 58% · 3989g · stash 9/10 · enc_at_time=72_
- use minor_potion on recruit_martyr_8311 (HP 66→116/238)

### [seq=329 leave_zone]
_L13 · HP 58% · 3989g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=330 enter_town] (in shinto_town)
_L13 · HP 58% · 3989g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=331 shop_buy] (in shinto_town)
_L13 · HP 58% · 3959g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=332 leave_town]
_L13 · HP 58% · 3959g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=333 enter_zone] zone_03
_L13 · HP 58% · 3959g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=334 use_consumable] zone_03
_L13 · HP 58% · 3959g · stash 9/10 · enc_at_time=72_
- use minor_potion on recruit_martyr_8311 (HP 116→166/238)

### [seq=335 leave_zone]
_L13 · HP 58% · 3959g · stash 9/10 · enc_at_time=72_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=13, cleared=True

### [seq=336 enter_town] (in shinto_town)
_L13 · HP 58% · 3959g · stash 9/10 · enc_at_time=72_
- enter town shinto_town

### [seq=337 shop_buy] (in shinto_town)
_L13 · HP 58% · 3929g · stash 10/10 · enc_at_time=72_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=338 leave_town]
_L13 · HP 58% · 3929g · stash 10/10 · enc_at_time=72_
- leave town shinto_town

### [seq=339 enter_zone] zone_03
_L13 · HP 58% · 3929g · stash 10/10 · enc_at_time=72_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 72 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (4 rounds)
_dealt 157, took 61, healed 0_

- **r1** hp ?→171 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=99, slime=99, slime=160]
- **r2** hp 171→169 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [caster_kitsune=95, slime=29, slime=90]
- **r3** hp 169→167 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 · KILL slime | end [caster_kitsune=43, slime=0, slime=20]
- **r4** hp 167→167 ap 3 st=— | **CHEAT(+1AP)** thrust→caster_kitsune +cheat_extras×1 +bonus×4 | dealt 157 · KILL caster_kitsune,slime | end [caster_kitsune=0, slime=0, slime=0]

### [seq=340 pick_loot] zone_03
_L13 · HP 56% · 4010g · stash 10/10 · enc_at_time=73_
- money +81g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=341 use_consumable] zone_03
_L13 · HP 56% · 4010g · stash 9/10 · enc_at_time=73_
- use minor_potion on recruit_martyr_8311 (HP 110→160/259)

### [seq=342 leave_zone]
_L13 · HP 56% · 4010g · stash 9/10 · enc_at_time=73_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=14, cleared=True

### [seq=343 enter_town] (in shinto_town)
_L13 · HP 56% · 4010g · stash 9/10 · enc_at_time=73_
- enter town shinto_town

### [seq=344 shop_buy] (in shinto_town)
_L13 · HP 56% · 3980g · stash 10/10 · enc_at_time=73_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=345 leave_town]
_L13 · HP 56% · 3980g · stash 10/10 · enc_at_time=73_
- leave town shinto_town

### [seq=346 enter_zone] zone_03
_L13 · HP 56% · 3980g · stash 10/10 · enc_at_time=73_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 73 [zone_03 idx=7] vs speeder_tengu, swime, swime → **VICTORY** (3 rounds)
_dealt 155, took 41, healed 0_

- **r1** hp ?→166 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [speeder_tengu=78, swime=98, swime=78]
- **r2** hp 166→157 ap 1 st=— | **SURVIVE** +bonus×4 | took 9 · KILL speeder_tengu | end [speeder_tengu=0, swime=23, swime=3]
- **r3** hp 157→157 ap 2 st=— | NORMAL thrust→swime +bonus×4 | dealt 155 · KILL swime,swime | end [speeder_tengu=0, swime=0, swime=0]

### [seq=347 pick_loot] zone_03
_L13 · HP 53% · 4040g · stash 10/10 · enc_at_time=74_
- money +60g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=348 use_consumable] zone_03
_L13 · HP 53% · 4040g · stash 9/10 · enc_at_time=74_
- use minor_potion on recruit_martyr_8311 (HP 129→179/259)

### [seq=349 leave_zone]
_L13 · HP 53% · 4040g · stash 9/10 · enc_at_time=74_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=15, cleared=True

### [seq=350 enter_town] (in shinto_town)
_L13 · HP 53% · 4040g · stash 9/10 · enc_at_time=74_
- enter town shinto_town

### [seq=351 shop_buy] (in shinto_town)
_L13 · HP 53% · 4010g · stash 10/10 · enc_at_time=74_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=352 leave_town]
_L13 · HP 53% · 4010g · stash 10/10 · enc_at_time=74_
- leave town shinto_town

### [seq=353 enter_zone] zone_03
_L13 · HP 53% · 4010g · stash 10/10 · enc_at_time=74_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### [seq=354 use_consumable] zone_03
_L13 · HP 70% · 4010g · stash 9/10 · enc_at_time=74_
- use minor_potion on mc_einherjar (HP 157→207/296)

### [seq=355 leave_zone]
_L13 · HP 70% · 4010g · stash 9/10 · enc_at_time=74_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=15, cleared=True

### [seq=356 enter_town] (in shinto_town)
_L13 · HP 70% · 4010g · stash 9/10 · enc_at_time=74_
- enter town shinto_town

### [seq=357 shop_buy] (in shinto_town)
_L13 · HP 70% · 3980g · stash 10/10 · enc_at_time=74_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=358 leave_town]
_L13 · HP 70% · 3980g · stash 10/10 · enc_at_time=74_
- leave town shinto_town

### [seq=359 enter_zone] zone_03
_L13 · HP 70% · 3980g · stash 10/10 · enc_at_time=74_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 74 [zone_03 idx=7] vs support_tanuki, brute_oni → **VICTORY** (6 rounds)
_dealt 252, took 84, healed 50_

- **r1** hp ?→190 ap 0 st=— | **SURVIVE** +bonus×4 | took 17 | end [support_tanuki=224, brute_oni=292]
- **r2** hp 190→189 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [support_tanuki=152, brute_oni=281]
- **r3** hp 189→189 ap 2 st=— | **SURVIVE** +bonus×4 | enemy_status(Rally buff→support_tanuki) | end [support_tanuki=152, brute_oni=224]
- **r4** hp 189→172 ap 3 st=— | **SURVIVE** +bonus×4 | took 17 | end [support_tanuki=139, brute_oni=182]
- **r5** hp 172→155 ap 3 st=— | **SURVIVE** +bonus×4 | took 17 | end [support_tanuki=139, brute_oni=197]
- **r6** hp 155→203 ap 3 st=— | **CHEAT(+3AP)** use_item(minor_potion)→self +cheat_extras×3 +bonus×4 | dealt 252 · took 2 · KILL support_tanuki,brute_oni | end [support_tanuki=0, brute_oni=0]

### [seq=360 pick_loot] zone_03
_L13 · HP 69% · 4025g · stash 9/10 · enc_at_time=75_
- money +45g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=361 leave_zone]
_L13 · HP 69% · 4025g · stash 9/10 · enc_at_time=75_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=16, cleared=True

### [seq=362 enter_town] (in shinto_town)
_L13 · HP 69% · 4025g · stash 9/10 · enc_at_time=75_
- enter town shinto_town

### [seq=363 shop_buy] (in shinto_town)
_L13 · HP 69% · 3995g · stash 10/10 · enc_at_time=75_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=364 leave_town]
_L13 · HP 69% · 3995g · stash 10/10 · enc_at_time=75_
- leave town shinto_town

### [seq=365 enter_zone] zone_03
_L13 · HP 69% · 3995g · stash 10/10 · enc_at_time=75_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 75 [zone_03 idx=7] vs caster_kitsune, slime, slime → **VICTORY** (3 rounds)
_dealt 312, took 10, healed 0_

- **r1** hp ?→202 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(?→recruit_martyr) | end [caster_kitsune=93, slime=41, slime=143]
- **r2** hp 202→201 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL slime · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=89, slime=0, slime=134]
- **r3** hp 201→201 ap 2 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 312 · KILL slime,caster_kitsune | end [caster_kitsune=0, slime=0, slime=0]

### [seq=366 pick_loot] zone_03
_L13 · HP 68% · 4036g · stash 10/10 · enc_at_time=76_
- money +41g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=367 use_consumable] zone_03
_L13 · HP 68% · 4036g · stash 9/10 · enc_at_time=76_
- use minor_potion on recruit_martyr_8311 (HP 141→191/259)

### [seq=368 leave_zone]
_L13 · HP 68% · 4036g · stash 9/10 · enc_at_time=76_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=17, cleared=True

### [seq=369 enter_town] (in shinto_town)
_L13 · HP 68% · 4036g · stash 9/10 · enc_at_time=76_
- enter town shinto_town

### [seq=370 shop_buy] (in shinto_town)
_L13 · HP 68% · 4006g · stash 10/10 · enc_at_time=76_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=371 leave_town]
_L13 · HP 68% · 4006g · stash 10/10 · enc_at_time=76_
- leave town shinto_town

### [seq=372 enter_zone] zone_03
_L13 · HP 68% · 4006g · stash 10/10 · enc_at_time=76_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 76 [zone_03 idx=7] vs brute_oni, slime, slime → **VICTORY** (5 rounds)
_dealt 174, took 67, healed 50_

- **r1** hp ?→200 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=292, slime=108, slime=80]
- **r2** hp 200→199 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=241, slime=34, slime=72]
- **r3** hp 199→198 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [brute_oni=190, slime=26, slime=1]
- **r4** hp 198→184 ap 3 st=— | **SURVIVE** +bonus×4 | took 14 · KILL slime,slime | end [brute_oni=140, slime=0, slime=0]
- **r5** hp 184→184 ap 3 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 170 · KILL brute_oni | end [brute_oni=0, slime=0, slime=0]

### [seq=373 pick_loot] zone_03
_L13 · HP 62% · 4027g · stash 9/10 · enc_at_time=77_
- money +21g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=374 leave_zone]
_L13 · HP 62% · 4027g · stash 9/10 · enc_at_time=77_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=18, cleared=True

### [seq=375 enter_town] (in shinto_town)
_L13 · HP 62% · 4027g · stash 9/10 · enc_at_time=77_
- enter town shinto_town

### [seq=376 shop_buy] (in shinto_town)
_L13 · HP 62% · 3997g · stash 10/10 · enc_at_time=77_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=377 leave_town]
_L13 · HP 62% · 3997g · stash 10/10 · enc_at_time=77_
- leave town shinto_town

### [seq=378 enter_zone] zone_03
_L13 · HP 62% · 3997g · stash 10/10 · enc_at_time=77_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 77 [zone_03 idx=7] vs speeder_tengu, swime, swime, bandit_slime → **VICTORY** (3 rounds)
_dealt 80, took 86, healed 0_

- **r1** hp ?→158 ap 0 st=— | **SURVIVE** +bonus×4 | took 16 · KILL bandit_slime · enemy_status(?→recruit_martyr), +status(?→self) | end [speeder_tengu=84, swime=47, swime=47, bandit_slime=0]
- **r2** hp 158→140 ap 1 st=— | **SURVIVE** +bonus×4 | took 8 · KILL speeder_tengu,swime | end [speeder_tengu=0, swime=0, swime=3, bandit_slime=0]
- **r3** hp 140→140 ap 2 st=— | NORMAL thrust→swime +bonus×4 | dealt 80 · KILL swime | end [speeder_tengu=0, swime=0, swime=0, bandit_slime=0]

### [seq=379 pick_loot] zone_03
_L13 · HP 47% · 3932g · stash 10/10 · enc_at_time=78_
- money +36g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=380 use_consumable] zone_03
_L13 · HP 64% · 3932g · stash 9/10 · enc_at_time=78_
- use minor_potion on mc_einherjar (HP 140→190/296)

### [seq=381 leave_zone]
_L13 · HP 64% · 3932g · stash 9/10 · enc_at_time=78_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=19, cleared=True

### [seq=382 enter_town] (in shinto_town)
_L13 · HP 64% · 3932g · stash 9/10 · enc_at_time=78_
- enter town shinto_town

### [seq=383 shop_buy] (in shinto_town)
_L13 · HP 64% · 3902g · stash 10/10 · enc_at_time=78_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=384 leave_town]
_L13 · HP 64% · 3902g · stash 10/10 · enc_at_time=78_
- leave town shinto_town

### [seq=385 enter_zone] zone_03
_L13 · HP 64% · 3902g · stash 10/10 · enc_at_time=78_
- enter zone_03 (already_cleared=True, via=sim_decide_zone)

### ENC 78 [zone_03 idx=7] vs caster_kitsune, speeder_tengu, slime → **VICTORY** (3 rounds)
_dealt 153, took 72, healed 0_

- **r1** hp ?→188 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=86, speeder_tengu=43, slime=80]
- **r2** hp 188→178 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu · enemy_status(?→recruit_martyr), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [caster_kitsune=39, speeder_tengu=0, slime=71]
- **r3** hp 178→178 ap 2 st=— | NORMAL thrust→slime +bonus×4 | dealt 153 · KILL slime,caster_kitsune | end [caster_kitsune=0, speeder_tengu=0, slime=0]

### [seq=386 pick_loot] zone_03
_L13 · HP 60% · 3909g · stash 10/10 · enc_at_time=79_
- money +7g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=387 leave_zone]
_L13 · HP 60% · 3909g · stash 10/10 · enc_at_time=79_
- leave zone_03: reason=sim_post_zone, enc_idx=7, overstay=20, cleared=True

### [seq=388 enter_town] (in shinto_town)
_L13 · HP 60% · 3909g · stash 10/10 · enc_at_time=79_
- enter town shinto_town

### [seq=389 leave_town]
_L13 · HP 60% · 3909g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=390 enter_zone] zone_04
_L13 · HP 60% · 3909g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=391 use_consumable] zone_04
_L13 · HP 60% · 3909g · stash 9/10 · enc_at_time=79_
- use minor_potion on recruit_martyr_8311 (HP 89→139/259)

### [seq=392 leave_zone]
_L13 · HP 60% · 3909g · stash 9/10 · enc_at_time=79_
- leave zone_04: reason=sim_post_zone, enc_idx=0, overstay=0, cleared=False

### [seq=393 enter_town] (in shinto_town)
_L13 · HP 60% · 3909g · stash 9/10 · enc_at_time=79_
- enter town shinto_town

### [seq=394 shop_buy] (in shinto_town)
_L13 · HP 60% · 3879g · stash 10/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=395 leave_town]
_L13 · HP 60% · 3879g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=396 enter_zone] zone_04
_L13 · HP 60% · 3879g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=397 use_consumable] zone_04
_L13 · HP 60% · 3879g · stash 9/10 · enc_at_time=79_
- use minor_potion on recruit_martyr_8311 (HP 139→189/259)

### [seq=398 leave_zone]
_L13 · HP 60% · 3879g · stash 9/10 · enc_at_time=79_
- leave zone_04: reason=sim_post_zone, enc_idx=0, overstay=0, cleared=False

### [seq=399 enter_town] (in shinto_town)
_L13 · HP 60% · 3879g · stash 9/10 · enc_at_time=79_
- enter town shinto_town

### [seq=400 shop_buy] (in shinto_town)
_L13 · HP 60% · 3849g · stash 10/10 · enc_at_time=79_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=401 leave_town]
_L13 · HP 60% · 3849g · stash 10/10 · enc_at_time=79_
- leave town shinto_town

### [seq=402 enter_zone] zone_04
_L13 · HP 60% · 3849g · stash 10/10 · enc_at_time=79_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 79 [zone_04 idx=0] vs split_slime, split_slime, slime → **VICTORY** (6 rounds)
_dealt 385, took 12, healed 0_

- **r1** hp ?→178 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [split_slime=161, split_slime=161, slime=177]
- **r2** hp 178→176 ap 1 st=— | **SURVIVE** +bonus×4 | took 2 | end [split_slime=90, split_slime=90, slime=167]
- **r3** hp 176→174 ap 2 st=— | **SURVIVE** +bonus×4 | took 2 | end [split_slime=82, split_slime=19, slime=98]
- **r4** hp 174→173 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL split_slime | end [split_slime=74, split_slime=0, slime=88]
- **r5** hp 173→173 ap 3 st=— | **CHEAT(+2AP)** thrust→slime +cheat_extras×2 +bonus×4 | dealt 229 · KILL slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=46, mini_slime=46]
- **r6** hp 173→173 ap 1 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 156 · KILL mini_slime,mini_slime | end [split_slime=0, split_slime=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=403 pick_loot] zone_04
_L14 · HP 55% · 4056g · stash 10/10 · enc_at_time=80_
- money +207g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 80 [zone_04 idx=1] vs brute_oni, mystic_slime → **VICTORY** (4 rounds)
_dealt 275, took 146, healed 50_

- **r1** hp ?→173 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [brute_oni=367, mystic_slime=74]
- **r2** hp 173→173 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [brute_oni=274, mystic_slime=39]
- **r3** hp 173→146 ap 2 st=— | **SURVIVE** +bonus×4 | took 27 · KILL mystic_slime · enemy_status(?→recruit_martyr) | end [brute_oni=237, mystic_slime=0]
- **r4** hp 146→146 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 267 · KILL brute_oni | end [brute_oni=0, mystic_slime=0]

### [seq=404 pick_loot] zone_04
_L14 · HP 47% · 4222g · stash 10/10 · enc_at_time=81_
- money +166g, offered=['minor_potion'], **selected**=['minor_potion'], skipped=[], discarded_stash=[]

### [seq=405 use_consumable] zone_04
_L14 · HP 47% · 4222g · stash 9/10 · enc_at_time=81_
- use minor_potion on recruit_martyr_8311 (HP 113→163/280)

### [seq=406 leave_zone]
_L14 · HP 47% · 4222g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=407 enter_town] (in shinto_town)
_L14 · HP 47% · 4222g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=408 shop_buy] (in shinto_town)
_L14 · HP 47% · 4192g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=409 leave_town]
_L14 · HP 47% · 4192g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=410 enter_zone] zone_04
_L14 · HP 47% · 4192g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=411 use_consumable] zone_04
_L14 · HP 63% · 4192g · stash 9/10 · enc_at_time=81_
- use minor_potion on mc_einherjar (HP 146→196/312)

### [seq=412 leave_zone]
_L14 · HP 63% · 4192g · stash 9/10 · enc_at_time=81_
- leave zone_04: reason=sim_post_zone, enc_idx=2, overstay=0, cleared=False

### [seq=413 enter_town] (in shinto_town)
_L14 · HP 63% · 4192g · stash 9/10 · enc_at_time=81_
- enter town shinto_town

### [seq=414 shop_buy] (in shinto_town)
_L14 · HP 63% · 4162g · stash 10/10 · enc_at_time=81_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=415 leave_town]
_L14 · HP 63% · 4162g · stash 10/10 · enc_at_time=81_
- leave town shinto_town

### [seq=416 enter_zone] zone_04
_L14 · HP 63% · 4162g · stash 10/10 · enc_at_time=81_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 81 [zone_04 idx=2] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (5 rounds)
_dealt 379, took 183, healed 0, deaths: ['recruit_martyr_8311']_

- **r1** hp ?→196 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(Taunted→recruit_martyr), +status(Taunted→self) | end [caster_kitsune=198, chunky_slime=280, chunky_slime=230]
- **r2** hp 196→194 ap 1 st=Taunted | **CHEAT(+1AP)** brace_strike→chunky_slime +cheat_extras×1 +bonus×4 | dealt 164 · took 2 · +status(Brace Strike DEF buff→self), enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→chunky_slime), -status(Taunted→self), -status(Brace Strike DEF buff→self) | end [caster_kitsune=109, chunky_slime=230, chunky_slime=12]
- **r3** hp 194→194 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [caster_kitsune=61, chunky_slime=220, chunky_slime=3]
- **r4** hp 194→194 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr), +status(Taunted→self), enemy_status(Taunted→recruit_martyr) | end [caster_kitsune=13, chunky_slime=220, chunky_slime=3]
- **r5** hp 194→192 ap 2 st=Taunted | **CHEAT(+2AP)** brace_strike→chunky_slime +cheat_extras×2 +bonus×4 | dealt 213 · took 2 · KILL caster_kitsune,recruit_martyr,chunky_slime,chunky_slime · +status(Brace Strike DEF buff→self) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=417 pick_loot] zone_04
_L14 · HP 62% · 4368g · stash 10/10 · enc_at_time=82_
- money +206g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 82 [zone_04 idx=3] vs split_slime, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 347, took 120, healed 50_

- **r1** hp ?→178 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · enemy_status(?→recruit_martyr), +status(?→self) | end [split_slime=76, speeder_tengu=90, slime=94]
- **r2** hp 178→155 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · KILL speeder_tengu · enemy_status(?→recruit_martyr), +status(?→self), enemy_status(Brace Strike DEF buff→slime) | end [split_slime=67, speeder_tengu=0, slime=81]
- **r3** hp 155→133 ap 2 st=— | **CHEAT(+1AP)** thrust→slime +cheat_extras×1 +bonus×4 | dealt 165 · KILL slime · -status(Searing Edge DOT→self) | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=28, mini_slime=42]
- **r4** hp 133→133 ap 1 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 168 · KILL mini_slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=418 pick_loot] zone_04
_L14 · HP 43% · 4691g · stash 9/10 · enc_at_time=83_
- money +323g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=419 leave_zone]
_L14 · HP 43% · 4691g · stash 9/10 · enc_at_time=83_
- leave zone_04: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=420 enter_town] (in shinto_town)
_L14 · HP 43% · 4691g · stash 9/10 · enc_at_time=83_
- enter town shinto_town

### [seq=421 shop_buy] (in shinto_town)
_L14 · HP 43% · 4661g · stash 10/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=422 leave_town]
_L14 · HP 43% · 4661g · stash 10/10 · enc_at_time=83_
- leave town shinto_town

### [seq=423 enter_zone] zone_04
_L14 · HP 43% · 4661g · stash 10/10 · enc_at_time=83_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=424 use_consumable] zone_04
_L14 · HP 59% · 4661g · stash 9/10 · enc_at_time=83_
- use minor_potion on mc_einherjar (HP 133→183/312)

### [seq=425 leave_zone]
_L14 · HP 59% · 4661g · stash 9/10 · enc_at_time=83_
- leave zone_04: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=426 enter_town] (in shinto_town)
_L14 · HP 59% · 4661g · stash 9/10 · enc_at_time=83_
- enter town shinto_town

### [seq=427 shop_buy] (in shinto_town)
_L14 · HP 59% · 4631g · stash 10/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=428 leave_town]
_L14 · HP 59% · 4631g · stash 10/10 · enc_at_time=83_
- leave town shinto_town

### [seq=429 enter_zone] zone_04
_L14 · HP 59% · 4631g · stash 10/10 · enc_at_time=83_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=430 use_consumable] zone_04
_L14 · HP 59% · 4631g · stash 9/10 · enc_at_time=83_
- use minor_potion on recruit_martyr_8311 (HP 152→202/280)

### [seq=431 leave_zone]
_L14 · HP 59% · 4631g · stash 9/10 · enc_at_time=83_
- leave zone_04: reason=sim_post_zone, enc_idx=4, overstay=0, cleared=False

### [seq=432 enter_town] (in shinto_town)
_L14 · HP 59% · 4631g · stash 9/10 · enc_at_time=83_
- enter town shinto_town

### [seq=433 shop_buy] (in shinto_town)
_L14 · HP 59% · 4601g · stash 10/10 · enc_at_time=83_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=434 leave_town]
_L14 · HP 59% · 4601g · stash 10/10 · enc_at_time=83_
- leave town shinto_town

### [seq=435 enter_zone] zone_04
_L14 · HP 59% · 4601g · stash 10/10 · enc_at_time=83_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 83 [zone_04 idx=4] vs support_tanuki, swime, brute_oni → **VICTORY** (6 rounds)
_dealt 399, took 274, healed 50_

- **r1** hp ?→161 ap 0 st=— | **SURVIVE** +bonus×4 | took 22 | end [support_tanuki=205, swime=157, brute_oni=332]
- **r2** hp 161→161 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [support_tanuki=275, swime=78, brute_oni=246]
- **r3** hp 161→167 ap 2 st=— | **CHEAT(+2AP)** use_item(minor_potion)→self +cheat_extras×2 +bonus×4 | dealt 240 · took 44 · KILL swime | end [support_tanuki=36, swime=0, brute_oni=228]
- **r4** hp 167→144 ap 0 st=— | **SURVIVE** +bonus×4 | took 23 · enemy_status(Rally buff→support_tanuki) | end [support_tanuki=36, swime=0, brute_oni=189]
- **r5** hp 144→121 ap 1 st=— | **SURVIVE** +bonus×4 | took 23 · KILL support_tanuki | end [support_tanuki=0, swime=0, brute_oni=150]
- **r6** hp 121→121 ap 2 st=— | **CHEAT(+1AP)** thrust→brute_oni +cheat_extras×1 +bonus×4 | dealt 159 · KILL brute_oni | end [support_tanuki=0, swime=0, brute_oni=0]

### [seq=436 pick_loot] zone_04
_L15 · HP 37% · 4942g · stash 9/10 · enc_at_time=84_
- money +341g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=437 recruit_accept] zone_04
_L15 · HP 37% · 4942g · stash 9/10 · enc_at_time=84_
- recruit_accept: Einherjar Recruit (einherjar L8) id=recruit_einherjar_9286

### [seq=438 leave_zone]
_L15 · HP 37% · 4942g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=439 enter_town] (in shinto_town)
_L15 · HP 37% · 4942g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=440 shop_buy] (in shinto_town)
_L15 · HP 37% · 4912g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=441 leave_town]
_L15 · HP 37% · 4912g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=442 enter_zone] zone_04
_L15 · HP 37% · 4912g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=443 use_consumable] zone_04
_L15 · HP 37% · 4912g · stash 9/10 · enc_at_time=84_
- use minor_potion on recruit_martyr_8311 (HP 40→90/301)

### [seq=444 leave_zone]
_L15 · HP 37% · 4912g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=445 enter_town] (in shinto_town)
_L15 · HP 37% · 4912g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=446 shop_buy] (in shinto_town)
_L15 · HP 37% · 4882g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=447 leave_town]
_L15 · HP 37% · 4882g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=448 enter_zone] zone_04
_L15 · HP 37% · 4882g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=449 use_consumable] zone_04
_L15 · HP 37% · 4882g · stash 9/10 · enc_at_time=84_
- use minor_potion on recruit_martyr_8311 (HP 90→140/301)

### [seq=450 leave_zone]
_L15 · HP 37% · 4882g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=451 enter_town] (in shinto_town)
_L15 · HP 37% · 4882g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=452 shop_buy] (in shinto_town)
_L15 · HP 37% · 4852g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=453 leave_town]
_L15 · HP 37% · 4852g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=454 enter_zone] zone_04
_L15 · HP 37% · 4852g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=455 use_consumable] zone_04
_L15 · HP 52% · 4852g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 121→171/327)

### [seq=456 leave_zone]
_L15 · HP 52% · 4852g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=457 enter_town] (in shinto_town)
_L15 · HP 52% · 4852g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=458 shop_buy] (in shinto_town)
_L15 · HP 52% · 4822g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=459 leave_town]
_L15 · HP 52% · 4822g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=460 enter_zone] zone_04
_L15 · HP 52% · 4822g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=461 use_consumable] zone_04
_L15 · HP 52% · 4822g · stash 9/10 · enc_at_time=84_
- use minor_potion on recruit_martyr_8311 (HP 140→190/301)

### [seq=462 leave_zone]
_L15 · HP 52% · 4822g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=463 enter_town] (in shinto_town)
_L15 · HP 52% · 4822g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=464 shop_buy] (in shinto_town)
_L15 · HP 52% · 4792g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=465 leave_town]
_L15 · HP 52% · 4792g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=466 enter_zone] zone_04
_L15 · HP 52% · 4792g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=467 use_consumable] zone_04
_L15 · HP 68% · 4792g · stash 9/10 · enc_at_time=84_
- use minor_potion on mc_einherjar (HP 171→221/327)

### [seq=468 leave_zone]
_L15 · HP 68% · 4792g · stash 9/10 · enc_at_time=84_
- leave zone_04: reason=sim_post_zone, enc_idx=5, overstay=0, cleared=False

### [seq=469 enter_town] (in shinto_town)
_L15 · HP 68% · 4792g · stash 9/10 · enc_at_time=84_
- enter town shinto_town

### [seq=470 shop_buy] (in shinto_town)
_L15 · HP 68% · 4762g · stash 10/10 · enc_at_time=84_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=471 leave_town]
_L15 · HP 68% · 4762g · stash 10/10 · enc_at_time=84_
- leave town shinto_town

### [seq=472 enter_zone] zone_04
_L15 · HP 68% · 4762g · stash 10/10 · enc_at_time=84_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 84 [zone_04 idx=5] vs brute_oni, caster_kitsune, split_slime → **VICTORY** (5 rounds)
_dealt 295, took 267, healed 50_

- **r1** hp ?→220 ap 0 st=— | **SURVIVE** +bonus×4 | took 1 | end [brute_oni=459, caster_kitsune=128, split_slime=122]
- **r2** hp 220→220 ap 1 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [brute_oni=458, caster_kitsune=76, split_slime=86]
- **r3** hp 220→219 ap 2 st=— | **SURVIVE** +bonus×4 | took 1 · KILL caster_kitsune | end [brute_oni=362, caster_kitsune=0, split_slime=7]
- **r4** hp 219→218 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 · KILL split_slime | end [brute_oni=269, caster_kitsune=0, split_slime=0]
- **r5** hp 218→218 ap 3 st=— | **CHEAT(+3AP)** thrust→brute_oni +cheat_extras×3 +bonus×4 | dealt 292 · KILL brute_oni | end [brute_oni=0, caster_kitsune=0, split_slime=0]

### [seq=473 pick_loot] zone_04
_L15 · HP 67% · 5007g · stash 9/10 · enc_at_time=85_
- money +245g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### [seq=474 leave_zone]
_L15 · HP 67% · 5007g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=475 enter_town] (in shinto_town)
_L15 · HP 67% · 5007g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=476 shop_buy] (in shinto_town)
_L15 · HP 67% · 4977g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=477 leave_town]
_L15 · HP 67% · 4977g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=478 enter_zone] zone_04
_L15 · HP 67% · 4977g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=479 use_consumable] zone_04
_L15 · HP 67% · 4977g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_8311 (HP 1→51/301)

### [seq=480 leave_zone]
_L15 · HP 67% · 4977g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=481 enter_town] (in shinto_town)
_L15 · HP 67% · 4977g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=482 shop_buy] (in shinto_town)
_L15 · HP 67% · 4947g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=483 leave_town]
_L15 · HP 67% · 4947g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=484 enter_zone] zone_04
_L15 · HP 67% · 4947g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=485 use_consumable] zone_04
_L15 · HP 67% · 4947g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_8311 (HP 51→101/301)

### [seq=486 leave_zone]
_L15 · HP 67% · 4947g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=487 enter_town] (in shinto_town)
_L15 · HP 67% · 4947g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=488 shop_buy] (in shinto_town)
_L15 · HP 67% · 4917g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=489 leave_town]
_L15 · HP 67% · 4917g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=490 enter_zone] zone_04
_L15 · HP 67% · 4917g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=491 use_consumable] zone_04
_L15 · HP 67% · 4917g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_8311 (HP 101→151/301)

### [seq=492 leave_zone]
_L15 · HP 67% · 4917g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=493 enter_town] (in shinto_town)
_L15 · HP 67% · 4917g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=494 shop_buy] (in shinto_town)
_L15 · HP 67% · 4887g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=495 leave_town]
_L15 · HP 67% · 4887g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=496 enter_zone] zone_04
_L15 · HP 67% · 4887g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### [seq=497 use_consumable] zone_04
_L15 · HP 67% · 4887g · stash 9/10 · enc_at_time=85_
- use minor_potion on recruit_martyr_8311 (HP 151→201/301)

### [seq=498 leave_zone]
_L15 · HP 67% · 4887g · stash 9/10 · enc_at_time=85_
- leave zone_04: reason=sim_post_zone, enc_idx=6, overstay=0, cleared=False

### [seq=499 enter_town] (in shinto_town)
_L15 · HP 67% · 4887g · stash 9/10 · enc_at_time=85_
- enter town shinto_town

### [seq=500 shop_buy] (in shinto_town)
_L15 · HP 67% · 4857g · stash 10/10 · enc_at_time=85_
- **BOUGHT** minor_potion @ 30g (to ?)
- offered: [minor_potion@30g, iron_blade@100g, spirit_lens@100g, iron_guard@120g, spirit_mantle@120g, warding_mail@200g, potion@90g]

### [seq=501 leave_town]
_L15 · HP 67% · 4857g · stash 10/10 · enc_at_time=85_
- leave town shinto_town

### [seq=502 enter_zone] zone_04
_L15 · HP 67% · 4857g · stash 10/10 · enc_at_time=85_
- enter zone_04 (already_cleared=False, via=sim_decide_zone)

### ENC 85 [zone_04 idx=6] vs kappa → **VICTORY** (21 rounds)
_dealt 222, took 714, healed 50, deaths: ['recruit_einherjar_9286']_

- **r1** hp ?→218 ap 0 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=671]
- **r2** hp 218→218 ap 1 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=554]
- **r3** hp 218→218 ap 2 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=541]
- **r4** hp 218→217 ap 3 st=— | **SURVIVE** +bonus×4 | took 1 | end [kappa=519]
- **r5** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=440]
- **r6** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=450]
- **r7** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=460]
- **r8** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=470]
- **r9** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=464]
- **r10** hp 217→217 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=357]
- **r11** hp 217→163 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=344]
- **r12** hp 163→163 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=274]
- **r13** hp 163→109 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=265]
- **r14** hp 109→55 ap 3 st=— | **SURVIVE** +bonus×4 | took 54 | end [kappa=257]
- **r15** hp 55→55 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=276]
- **r16** hp 55→55 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=294]
- **r17** hp 55→18 ap 3 st=— | **SURVIVE** +bonus×4 | took 37 | end [kappa=284]
- **r18** hp 18→18 ap 3 st=— | **SURVIVE** +bonus×4 | KILL recruit_einherjar | end [kappa=302]
- **r19** hp 18→18 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=320]
- **r20** hp 18→18 ap 3 st=— | **SURVIVE** +bonus×4 | (no events) | end [kappa=220]
- **r21** hp 18→18 ap 3 st=— | **CHEAT(+3AP)** thrust→kappa +cheat_extras×3 +bonus×4 | dealt 220 · KILL kappa | end [kappa=0]

### [seq=503 pick_loot] zone_04
_L15 · HP 6% · 5077g · stash 10/10 · enc_at_time=86_
- money +220g, offered=['potion', 'cast_brace_strike', 'cast_searing_edge', 'res_to_str_charm'], **selected**=['potion'], skipped=['cast_brace_strike', 'cast_searing_edge', 'res_to_str_charm'], discarded_stash=[]

### ENC 86 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (4 rounds)
_dealt 438, took 8, healed 0_

- **r1** hp ?→15 ap 0 st=— | **SURVIVE** +bonus×4 | took 3 · KILL speeder_tengu | end [split_slime=114, speeder_tengu=0, slime=147]
- **r2** hp 15→14 ap 1 st=— | **SURVIVE** +bonus×4 | took 1 · enemy_status(Brace Strike DEF buff→slime) | end [split_slime=105, speeder_tengu=0, slime=71]
- **r3** hp 14→14 ap 2 st=— | **CHEAT(+2AP)** thrust→split_slime +cheat_extras×2 +bonus×4 | dealt 260 · KILL slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=42, mini_slime=42]
- **r4** hp 14→14 ap 0 st=— | NORMAL thrust→mini_slime +bonus×4 | dealt 178 · KILL mini_slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=504 pick_loot] zone_04
_L16 · HP 4% · 5391g · stash 10/10 · enc_at_time=87_
- money +314g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 87 [zone_04 idx=7] vs split_slime, speeder_tengu, slime → **VICTORY** (7 rounds)
_dealt 231, took 49, healed 0, deaths: ['mc_einherjar', 'recruit_martyr_8311']_

- **r1** hp ?→0 ap 0 st=— | **SURVIVE** +bonus×4 | took 2 · enemy_status(?→recruit_martyr), +status(?→self) | end [split_slime=190, speeder_tengu=99, slime=142]
- **r2** hp 0→0 ap 1 st=— | — | KILL recruit_martyr | end [split_slime=179, speeder_tengu=15, slime=109]
- **r3** hp 0→0 ap 1 st=— | — | KILL speeder_tengu | end [split_slime=143, speeder_tengu=0, slime=76]
- **r4** hp 0→0 ap 1 st=— | — | enemy_status(Brace Strike DEF buff→slime) | end [split_slime=107, speeder_tengu=0, slime=43]
- **r5** hp 0→0 ap 1 st=— | — | (no events) | end [split_slime=71, speeder_tengu=0, slime=10]
- **r6** hp 0→0 ap 1 st=— | — | KILL slime,mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=54]
- **r7** hp 0→0 ap 1 st=— | — | KILL mini_slime | end [split_slime=0, speeder_tengu=0, slime=0, mini_slime=0, mini_slime=0]

### [seq=505 pick_loot] zone_04
_L16 · HP 4% · 5748g · stash 10/10 · enc_at_time=88_
- money +357g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 88 [zone_04 idx=7] vs caster_kitsune, chunky_slime, chunky_slime → **VICTORY** (20 rounds)
_dealt 313, took 106, healed 0, deaths: ['recruit_martyr_8311', 'mc_einherjar']_

- **r1** hp ?→14 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr), enemy_status(Taunted→recruit_martyr), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=143, chunky_slime=280, chunky_slime=280]
- **r2** hp 14→14 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr · enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [caster_kitsune=62, chunky_slime=270, chunky_slime=239]
- **r3** hp 14→0 ap 2 st=— | **SURVIVE** +bonus×4 | took 14 · KILL caster_kitsune · +status(?→self), enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=212, chunky_slime=229]
- **r4** hp 0→0 ap 3 st=— | — | enemy_status(Taunted→recruit_einherjar), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=212, chunky_slime=229]
- **r5** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=144, chunky_slime=219]
- **r6** hp 0→0 ap 3 st=— | — | (no events) | end [caster_kitsune=0, chunky_slime=134, chunky_slime=209]
- **r7** hp 0→0 ap 3 st=— | — | enemy_status(Taunted→recruit_einherjar), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=134, chunky_slime=209]
- **r8** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=66, chunky_slime=199]
- **r9** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=56, chunky_slime=189]
- **r10** hp 0→0 ap 3 st=— | — | enemy_status(Taunted→recruit_einherjar), enemy_status(Taunted→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=56, chunky_slime=189]
- **r11** hp 0→0 ap 3 st=— | — | KILL chunky_slime · enemy_status(Brace Strike DEF buff→chunky_slime), enemy_status(Brace Strike DEF buff→recruit_einherjar) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=179]
- **r12** hp 0→0 ap 3 st=— | — | (no events) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=169]
- **r13** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=159]
- **r14** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=149]
- **r15** hp 0→0 ap 3 st=— | — | (no events) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=139]
- **r16** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=129]
- **r17** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=119]
- **r18** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=109]
- **r19** hp 0→0 ap 3 st=— | — | enemy_status(Brace Strike DEF buff→chunky_slime) | end [caster_kitsune=0, chunky_slime=0, chunky_slime=99]
- **r20** hp 0→0 ap 3 st=— | — | KILL chunky_slime | end [caster_kitsune=0, chunky_slime=0, chunky_slime=0]

### [seq=506 pick_loot] zone_04
_L16 · HP 4% · 6006g · stash 10/10 · enc_at_time=89_
- money +258g, offered=[], **selected**=[], skipped=[], discarded_stash=[]

### ENC 89 [zone_04 idx=7] vs brute_oni, mystic_slime → **DEFEAT** (15 rounds)
_dealt 0, took 352, healed 0, deaths: ['recruit_martyr_8311', 'mc_einherjar', 'recruit_einherjar_9286']_

- **r1** hp ?→14 ap 0 st=— | **SURVIVE** +bonus×4 | enemy_status(?→recruit_martyr) | end [brute_oni=332, mystic_slime=141]
- **r2** hp 14→14 ap 1 st=— | **SURVIVE** +bonus×4 | KILL recruit_martyr | end [brute_oni=331, mystic_slime=59]
- **r3** hp 14→0 ap 2 st=— | **SURVIVE** +bonus×4 | took 34 · KILL mystic_slime | end [brute_oni=330, mystic_slime=0]
- **r4** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=329, mystic_slime=0]
- **r5** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=328, mystic_slime=0]
- **r6** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=328, mystic_slime=0]
- **r7** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=327, mystic_slime=0]
- **r8** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=326, mystic_slime=0]
- **r9** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=325, mystic_slime=0]
- **r10** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=324, mystic_slime=0]
- **r11** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=323, mystic_slime=0]
- **r12** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=322, mystic_slime=0]
- **r13** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=321, mystic_slime=0]
- **r14** hp 0→0 ap 3 st=— | — | (no events) | end [brute_oni=320, mystic_slime=0]
- **r15** hp 0→0 ap 3 st=— | — | KILL recruit_einherjar | end [brute_oni=319, mystic_slime=0]
