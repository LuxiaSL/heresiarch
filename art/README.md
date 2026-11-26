# Heresiarch art: sprites as code

All pixel art lives as text in `art/src/*.yaml`. A compiler turns it into
PNG sprite sheets and an atlas that the phone client loads. The style is
"GBA-bright": 16×16 tiles, saturated colour ramps, and a heavy plum-black
outline on everything that moves.

## Build

```bash
uv run --with pillow python art/build.py           # sheets + atlas + previews
uv run --with pillow python art/build.py --check   # validate only
uv run --with pillow python art/tools/selftest.py  # failure-mode self-test
```

Pillow is not a project dependency. `--with pillow` brings it in for the run.

The build writes:

| Output | What it is |
|---|---|
| `src/heresiarch/mobile/static/sprites/<sheet>.png` | packed sheets (1 px transparent gutter) |
| `src/heresiarch/mobile/static/sprites/atlas.json` | frame lookup, see the contract below |
| `art/preview/sheet_<sheet>.png` | contact sheets at ×4, with labels |
| `art/preview/mock_scene.png` | a dungeon room built from the tiles, with a party and two packs |
| `art/preview/mock_battle.png` | the battle backdrop with three enemies and a menu box |

Look at the previews after every change. They exist so that the art gets judged as a scene and not only frame by frame.

## Source format

**Palettes** (`art/src/palettes.yaml`):

- `colors` is the master swatch. Every hex value in the game lives there.
- `palettes` map single characters to a colour name or a raw `#rrggbb[aa]`.
- A palette can `extends:` another and override a few characters. Job colourways and slime variants are made this way.
- `.` is always transparent.

Characters are *semantic*. In the `slime` palette, `2`–`5` run from light to deep and `e` is the eye. A variant only remaps what those characters mean.

**Sprites** (every other YAML file). Each file sets `sheet:` and optional `defaults:`, then lists `sprites:`:

```yaml
sprites:
  floor_0:
    grid: |            # one char per pixel; rows must all be the same width
      2222...
  mob_swime_0:
    from: body16_0     # derive from another sprite (any file)
    palette: slime_swime        # repaint every cell with this palette
    swap: {hero: hero_onmyoji}  # or: swap only cells from one palette
    recolor: {"e": "3"}         # remap chars before colouring
    mirror: true                # horizontal flip (flip_v also exists)
    offset: [0, 1]              # shift the content
    layers:                     # composite on top, in order
      - {sprite: acc16_swime, palette: slime_swime, at: [0, 0]}
      - {grid: "KK", at: [3, 4]}
    export: false               # a part: usable by others, not in the atlas
    ax: 8                       # anchor; defaults to bottom-centre (w/2, h)
    ay: 16
```

**`generate:`** stamps out a family of sprites. Every string in `spec` is `str.format`-ed with the loop variables. `heroes.yaml` builds all 72 hero frames from 9 body frames this way: job × direction × frame, with `right` mirrored from `left`.

**`autotile:`** builds `wall_0`…`wall_15` from parts. The parts are keyed by mask bit: the stone face is added when the bit for floor-to-the-south is set, and the edge lines when the north, east or west bits are set.

**Drafting helpers** (`art/tools/`):

- `draft_slime.py` prints shaded slime-body grids.
- `draft_backdrop.py` prints the procedural backdrop.

They produced the first pass of the bodies and the backdrop. The committed YAML is now the source of truth: edit it by hand, and rerun a drafter only to start a shape over.

The build fails loudly in these cases:

- ragged rows
- spaces in a grid
- characters missing from the palette
- unknown sprites or palettes
- duplicate names
- reference cycles
- any frame that the contract requires but the sources don't define

## Atlas contract

```json
{"tile": 16,
 "sheets": {"<sheet>": "<file>.png"},
 "frames": {"<name>": {"sheet": "...", "x": 0, "y": 0, "w": 16, "h": 16, "ax": 8, "ay": 16}}}
```

`ax`/`ay` give the pixel in the frame that sits on the **bottom-centre of its tile**. To draw a frame at tile (tx, ty), draw it at `(tx*16 + 8 - ax, ty*16 + 16 - ay)`.

| Frames | Size | Notes |
|---|---|---|
| `floor_0..3`, `corridor_0..1` | 16×16 | pick the variant with a position hash; corridors are optional |
| `wall_0..15` | 16×16 | mask of orthogonal *floor* neighbours: N=1 E=2 S=4 W=8 |
| `void` | 16×16 | rock with no floor near it, or unexplored |
| `stairs_down`, `exit_torii` | 16×16 | opaque; floor is baked in |
| `decor_lantern`, `decor_bamboo`, `decor_grass_0..2` | 16×16 | optional scatter, drawn over floor |
| `hero_<job>_<dir>_<f>` | 16×24 | job ∈ default/einherjar/onmyoji/berserker/martyr/sacrist; dir ∈ down/up/left/right; f ∈ 0 (stand), 1, 2 (steps) |
| `mob_<template>_<f>` | 16×16, bosses 24×24 | f ∈ 0/1 bounce |
| `battle_<template>_<f>` | 32×32, bosses 48×48 | front-facing idle, f ∈ 0/1 |
| `ui_cursor` 9×8, `ui_alert` 10×11, `ui_item_bag` 16×16 | | |
| `bg_shrine_path` | 160×96 | anchor (0,0); scale to the panel |

Slime templates: `fodder_slime`, `slime`, `swime`, `mystic_slime`, `chunky_slime`, `toxic_slime`, `bandit_slime`, `alpha_slime` (boss), `omega_slime` (boss). For any other template, fall back to `mob_default_*` and `battle_default_*`.

### Renderer notes

- Turn smoothing off (`ctx.imageSmoothingEnabled = false`) and scale by a whole number. Every frame has a 1 px gutter, but fractional scales will still shimmer.
- **Walls vs void.** A rock cell that touches floor in any of its 8 neighbours draws `wall_<mask>` (diagonal-only contact gives `wall_0`, the plain canopy). Rock with no floor around it draws `void`. Drawing every rock cell as a wall makes a solid green mass. Drawing mask-0 cells as void cuts black notches into room corners. `mock_scene` uses this rule.
- **Draw order.** Draw floor and walls first. Then draw decor and items. Then draw actors sorted by tile row, so a hero south of a slime overlaps it.
- **Walk cycle.** Play frames 0, 1, 0, 2. Mobs alternate 0 and 1 at about 2–3 Hz.
- `ui_alert` sits one tile above a pack that has spotted the party. `ui_cursor` bobs above the battle target.

## Dungeon themes (one look per zone)

Every zone names a **dungeon theme**. A theme has two halves, and each half is its own file, so several people (or agents) can work on different themes without touching shared files:

| Half | File | What it holds |
|---|---|---|
| Data | `data/region_<r>/dungeon_themes/<id>.yaml` | `layout` (generator knobs), `decor` (frame names to scatter on floors), `decor_density`, `backdrop` (battle backdrop id) |
| Art | `art/src/themes/<id>.yaml` | its own `colors`/`palettes`, its own `sheet`, and sprites |

**How art resolves.** The client draws `<id>.<frame>` when it exists and falls back to the base frame (zone 1's art) when it doesn't. A theme file can override the whole terrain set or just a few pieces. Battle backdrops are `bg_<backdrop>`. Decor names in the data file are looked up the same way: `decor_moss_0` resolves to `<id>.decor_moss_0`, then to `decor_moss_0`.

**Rules for a theme art file** (`build.py` enforces them):
- Top-level `theme: <id>`, and a `sheet:` of its own (e.g. `theme_<id>`).
- Every sprite name, helper parts included, starts with `<id>.`, or with `bg_<id>` for a backdrop.
- Colour and palette names must not clash with `palettes.yaml` or other themes. Prefix them, e.g. `moss_leaf1`, palette `mossy_path`.
- A theme file must define the full terrain set: `<id>.floor_0..3`, `<id>.wall_0..15` (the `autotile` block with `prefix: "<id>.wall_"` is the easy way), `<id>.void`, `<id>.stairs_down`, `<id>.stairs_up`, `<id>.exit_torii`. A `bg_<id>` backdrop (160×96) is strongly encouraged. Set `backdrop: <id>` in the data file to use it.

**Layout knobs** (`LayoutParams` in `src/heresiarch/engine/dungeon/models.py`):

| Knob | What it does |
|---|---|
| `width`, `height` | Floor size in tiles |
| `grid_cols`, `grid_rows` | The cell grid: one room or junction per cell |
| `room_min_w/h`, `room_max_w/h` | Room size range |
| `room_chance`, `min_rooms` | How many cells get rooms |
| `extra_edge_chance` | Extra loops between rooms |
| `room_shape` | `rect`, `round` (clearings) or `mixed` |
| `corridor_width` | 1 or 2 |
| `edge_jitter` | Ragged, organic room edges, 0–0.6 |
| `pillar_density` | Columns inside rooms (never disconnecting) |

**Preview.** Every build writes `art/preview/theme_<id>.png`: a real generated floor using the theme's layout, drawn with its tiles and decor under the client's rules, plus its battle backdrop. Look at it after every change.
