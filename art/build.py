"""Sprite-as-code compiler.

    uv run --with pillow python art/build.py            # build sheets + atlas + previews
    uv run --with pillow python art/build.py --check    # validate only, write nothing

Sources live in ``art/src/*.yaml``. Palettes are named char→colour maps;
sprites are text grids (one char per pixel, ``.`` = transparent) that
reference a palette. A sprite can also be derived from another sprite
(``from``), palette-swapped (``palette`` / ``swap`` / ``recolor``),
mirrored, shifted, and composed from layers. ``generate`` blocks stamp out
families of sprites from a template, and ``autotile`` blocks build the
16 orthogonal-mask wall tiles from parts.

Output:
  src/heresiarch/mobile/static/sprites/<sheet>.png
  src/heresiarch/mobile/static/sprites/atlas.json
  art/preview/sheet_<sheet>.png   (×4 contact sheets, labelled)
  art/preview/mock_scene.png      (dungeon room composed from tiles)
  art/preview/mock_battle.png     (battle backdrop + 3 enemies)

See art/README.md for the source format and the atlas contract.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - environment guard
    sys.exit(
        "Pillow is not installed. Run with:\n"
        "  uv run --with pillow python art/build.py"
    )

ART_DIR = Path(__file__).resolve().parent
REPO_ROOT = ART_DIR.parent
SRC_DIR = ART_DIR / "src"
OUT_DIR = REPO_ROOT / "src" / "heresiarch" / "mobile" / "static" / "sprites"
PREVIEW_DIR = ART_DIR / "preview"

TRANSPARENT = "."
TILE = 16
SHEET_MAX_WIDTH = 256
PAD = 1  # transparent gutter between packed frames (guards against bleed)


class BuildError(Exception):
    """Any problem in the art sources. The message names file + sprite."""


# ---------------------------------------------------------------------------
# Source models
# ---------------------------------------------------------------------------


class Layer(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    sprite: str | None = None
    grid: str | None = None
    palette: str | None = None
    swap: dict[str, str] = Field(default_factory=dict)
    recolor: dict[str, str] = Field(default_factory=dict)
    at: tuple[int | str, int | str] = (0, 0)
    mirror: bool = False
    optional: bool = False  # skip silently if `sprite` doesn't exist


class SpriteSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    grid: str | None = None
    from_: str | None = Field(default=None, alias="from")
    palette: str | None = None
    swap: dict[str, str] = Field(default_factory=dict)  # palette name → palette name
    recolor: dict[str, str] = Field(default_factory=dict)  # char → char
    mirror: bool = False
    flip_v: bool = False
    offset: tuple[int | str, int | str] = (0, 0)
    size: tuple[int, int] | None = None  # canvas size (needed for layer-only sprites)
    layers: list[Layer] = Field(default_factory=list)
    ax: int | None = None
    ay: int | None = None
    export: bool = True
    sheet: str | None = None
    # Palette used to parse inline layer grids when `palette` isn't set
    # (filled from file defaults by the loader).
    default_palette: str | None = None


class GenerateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    for_: dict[str, list[Any]] = Field(alias="for")
    spec: dict[str, Any]


class AutotileSpec(BaseModel):
    """Build ``<prefix>0`` … ``<prefix>15`` from parts keyed by mask bit."""

    model_config = ConfigDict(extra="forbid")

    prefix: str
    base: str
    bits: dict[int, list[Layer]]
    order: list[int] = Field(default_factory=lambda: [4, 1, 2, 8])
    palette: str | None = None


class SourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet: str = "misc"
    defaults: dict[str, Any] = Field(default_factory=dict)
    sprites: dict[str, dict[str, Any]] = Field(default_factory=dict)
    generate: list[GenerateSpec] = Field(default_factory=list)
    autotile: list[AutotileSpec] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

RGBA = tuple[int, int, int, int]
_HEX = re.compile(r"^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")


def parse_hex(value: str, where: str) -> RGBA:
    m = _HEX.match(value.strip())
    if not m:
        raise BuildError(f"{where}: bad colour {value!r} (want #rrggbb or #rrggbbaa)")
    rgb = m.group(1)
    alpha = int(m.group(2), 16) if m.group(2) else 255
    return (int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16), alpha)


def load_palettes(path: Path) -> dict[str, dict[str, RGBA]]:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise BuildError(f"{path}: expected a mapping")
    colors_raw: dict[str, str] = raw.get("colors", {}) or {}
    colors = {name: parse_hex(v, f"{path.name}: colors.{name}") for name, v in colors_raw.items()}
    pal_raw: dict[str, dict[str, Any]] = raw.get("palettes", {}) or {}

    resolved: dict[str, dict[str, RGBA]] = {}

    def resolve(name: str, stack: tuple[str, ...] = ()) -> dict[str, RGBA]:
        if name in resolved:
            return resolved[name]
        if name in stack:
            raise BuildError(f"{path.name}: palette inheritance cycle {' -> '.join(stack + (name,))}")
        if name not in pal_raw:
            raise BuildError(f"{path.name}: unknown palette {name!r}")
        body = dict(pal_raw[name])
        parent = body.pop("extends", None)
        out: dict[str, RGBA] = dict(resolve(parent, stack + (name,))) if parent else {}
        for ch, ref in body.items():
            ch = str(ch)
            if len(ch) != 1 or ch == TRANSPARENT:
                raise BuildError(f"{path.name}: palette {name}: key {ch!r} must be one char, not '.'")
            ref = str(ref)
            if ref.startswith("#"):
                out[ch] = parse_hex(ref, f"{path.name}: palette {name}.{ch}")
            elif ref in colors:
                out[ch] = colors[ref]
            else:
                raise BuildError(f"{path.name}: palette {name}.{ch} -> unknown colour {ref!r}")
        resolved[name] = out
        return out

    for name in pal_raw:
        resolve(name)
    return resolved


# ---------------------------------------------------------------------------
# Cell canvases: each pixel remembers (char, palette) so swaps work after
# composition. Rendering to RGBA happens once at the end.
# ---------------------------------------------------------------------------

Cell = tuple[str, str] | None  # (char, palette name)


@dataclass
class Canvas:
    w: int
    h: int
    cells: list[list[Cell]] = field(default_factory=list)

    @classmethod
    def blank(cls, w: int, h: int) -> Canvas:
        return cls(w, h, [[None] * w for _ in range(h)])

    def copy(self) -> Canvas:
        return Canvas(self.w, self.h, [row[:] for row in self.cells])

    def mirrored(self) -> Canvas:
        return Canvas(self.w, self.h, [row[::-1] for row in self.cells])

    def flipped(self) -> Canvas:
        return Canvas(self.w, self.h, [row[:] for row in self.cells[::-1]])

    def shifted(self, dx: int, dy: int) -> Canvas:
        out = Canvas.blank(self.w, self.h)
        for y, row in enumerate(self.cells):
            for x, c in enumerate(row):
                nx, ny = x + dx, y + dy
                if c is not None and 0 <= nx < self.w and 0 <= ny < self.h:
                    out.cells[ny][nx] = c
        return out

    def paste(self, other: Canvas, ox: int, oy: int) -> None:
        for y, row in enumerate(other.cells):
            for x, c in enumerate(row):
                nx, ny = x + ox, y + oy
                if c is not None and 0 <= nx < self.w and 0 <= ny < self.h:
                    self.cells[ny][nx] = c

    def map_cells(self, fn) -> Canvas:  # type: ignore[no-untyped-def]
        return Canvas(self.w, self.h, [[fn(c) if c is not None else None for c in row] for row in self.cells])


def parse_grid(text: str, palette: str, where: str) -> Canvas:
    rows = [r.rstrip() for r in text.strip("\n").split("\n")]
    rows = [r.strip() for r in rows]
    if not rows or not rows[0]:
        raise BuildError(f"{where}: empty grid")
    width = len(rows[0])
    for i, r in enumerate(rows):
        if len(r) != width:
            raise BuildError(
                f"{where}: ragged grid — row {i} has {len(r)} px, row 0 has {width}\n    {r!r}"
            )
        if " " in r:
            raise BuildError(f"{where}: row {i} contains a space; use '.' for transparency")
    cells: list[list[Cell]] = [
        [None if ch == TRANSPARENT else (ch, palette) for ch in r] for r in rows
    ]
    return Canvas(width, len(rows), cells)


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


@dataclass
class Entry:
    name: str
    spec: SpriteSpec
    sheet: str
    origin: str  # file name for error messages


class Resolver:
    def __init__(self, palettes: dict[str, dict[str, RGBA]]):
        self.palettes = palettes
        self.entries: dict[str, Entry] = {}
        self._cache: dict[str, Canvas] = {}

    def add(self, entry: Entry) -> None:
        if entry.name in self.entries:
            prev = self.entries[entry.name].origin
            raise BuildError(f"{entry.origin}: sprite {entry.name!r} already defined in {prev}")
        self.entries[entry.name] = entry

    def resolve(self, name: str, stack: tuple[str, ...] = ()) -> Canvas:
        if name in self._cache:
            return self._cache[name]
        if name in stack:
            raise BuildError(f"sprite reference cycle: {' -> '.join(stack + (name,))}")
        if name not in self.entries:
            via = f" (referenced by {stack[-1]})" if stack else ""
            raise BuildError(f"unknown sprite {name!r}{via}")
        entry = self.entries[name]
        canvas = self._build(entry, stack + (name,))
        self._cache[name] = canvas
        return canvas

    def _palette_name(self, name: str | None, where: str) -> str:
        if name is None:
            raise BuildError(f"{where}: no palette (set `palette:` or file defaults)")
        if name not in self.palettes:
            raise BuildError(f"{where}: unknown palette {name!r}")
        return name

    def _apply_colour_ops(
        self, canvas: Canvas, palette: str | None, swap: dict[str, str], recolor: dict[str, str], where: str
    ) -> Canvas:
        if recolor:
            for k, v in recolor.items():
                if len(k) != 1 or len(v) != 1:
                    raise BuildError(f"{where}: recolor keys/values must be single chars ({k!r}->{v!r})")
            canvas = canvas.map_cells(lambda c: (recolor.get(c[0], c[0]), c[1]))
        if swap:
            for new in swap.values():
                self._palette_name(new, where)
            canvas = canvas.map_cells(lambda c: (c[0], swap.get(c[1], c[1])))
        if palette is not None:
            pal = self._palette_name(palette, where)
            canvas = canvas.map_cells(lambda c: (c[0], pal))
        return canvas

    def _layer_canvas(self, layer: Layer, default_palette: str | None, where: str, stack: tuple[str, ...]) -> Canvas | None:
        if layer.sprite is not None:
            if layer.sprite not in self.entries:
                if layer.optional:
                    return None
                raise BuildError(f"{where}: layer references unknown sprite {layer.sprite!r}")
            c = self.resolve(layer.sprite, stack)
        elif layer.grid is not None:
            c = parse_grid(layer.grid, self._palette_name(layer.palette or default_palette, where), where + " (layer)")
        else:
            raise BuildError(f"{where}: layer needs `sprite` or `grid`")
        c = self._apply_colour_ops(c, layer.palette if layer.sprite else None, layer.swap, layer.recolor, where)
        if layer.mirror:
            c = c.mirrored()
        return c

    def _build(self, entry: Entry, stack: tuple[str, ...]) -> Canvas:
        s = entry.spec
        where = f"{entry.origin}: {entry.name}"
        if s.grid is not None and s.from_ is not None:
            raise BuildError(f"{where}: use either `grid` or `from`, not both")

        if s.grid is not None:
            base = parse_grid(s.grid, self._palette_name(s.palette, where), where)
            base = self._apply_colour_ops(base, None, s.swap, s.recolor, where)
        elif s.from_ is not None:
            base = self.resolve(s.from_, stack).copy()
            base = self._apply_colour_ops(base, s.palette, s.swap, s.recolor, where)
        elif s.size is not None:
            base = Canvas.blank(*s.size)
        elif s.layers:
            first = self._layer_canvas(s.layers[0], s.palette or s.default_palette, where, stack)
            if first is None:
                raise BuildError(f"{where}: first layer is missing and no `size` given")
            base = Canvas.blank(first.w, first.h)
        else:
            raise BuildError(f"{where}: needs `grid`, `from`, `size` or `layers`")

        if s.size is not None and (base.w, base.h) != tuple(s.size):
            if s.grid is not None or s.from_ is not None:
                raise BuildError(f"{where}: declared size {s.size} but source is {base.w}x{base.h}")

        for layer in s.layers:
            lc = self._layer_canvas(layer, s.palette or s.default_palette, where, stack)
            if lc is None:
                continue
            ax, ay = (_as_int(v, where) for v in layer.at)
            base.paste(lc, ax, ay)

        if s.mirror:
            base = base.mirrored()
        if s.flip_v:
            base = base.flipped()
        dx, dy = (_as_int(v, where) for v in s.offset)
        if dx or dy:
            base = base.shifted(dx, dy)
        return base

    def render(self, name: str) -> Image.Image:
        canvas = self.resolve(name)
        img = Image.new("RGBA", (canvas.w, canvas.h), (0, 0, 0, 0))
        px = img.load()
        entry = self.entries[name]
        for y, row in enumerate(canvas.cells):
            for x, c in enumerate(row):
                if c is None:
                    continue
                ch, pal = c
                colour = self.palettes[pal].get(ch)
                if colour is None:
                    raise BuildError(
                        f"{entry.origin}: {name}: char {ch!r} at ({x},{y}) not in palette {pal!r}"
                    )
                px[x, y] = colour  # type: ignore[index]
        return img


def _as_int(v: int | str, where: str) -> int:
    try:
        return int(v)
    except (TypeError, ValueError) as e:
        raise BuildError(f"{where}: expected an integer, got {v!r}") from e


def _fmt(obj: Any, vars_: dict[str, Any]) -> Any:
    """Recursively str.format every string in a generate template."""
    if isinstance(obj, str):
        try:
            return obj.format(**vars_)
        except (KeyError, IndexError) as e:
            raise BuildError(f"generate: template {obj!r} uses unknown var {e}") from e
    if isinstance(obj, list):
        return [_fmt(x, vars_) for x in obj]
    if isinstance(obj, dict):
        return {_fmt(k, vars_): _fmt(v, vars_) for k, v in obj.items()}
    return obj


def _expand_for(for_: dict[str, list[Any]]) -> Iterable[dict[str, Any]]:
    keys = list(for_)
    for combo in itertools.product(*(for_[k] for k in keys)):
        vars_: dict[str, Any] = {}
        for k, v in zip(keys, combo, strict=True):
            if isinstance(v, dict):  # tuple-style entries merge their keys
                vars_.update(v)
            else:
                vars_[k] = v
        yield vars_


def load_sources(resolver: Resolver) -> None:
    files = sorted(p for p in SRC_DIR.glob("*.yaml") if p.name != "palettes.yaml")
    if not files:
        raise BuildError(f"no sprite sources in {SRC_DIR}")
    for path in files:
        raw = yaml.safe_load(path.read_text()) or {}
        try:
            src = SourceFile.model_validate(raw)
        except ValidationError as e:
            raise BuildError(f"{path.name}: {e}") from e

        def make(name: str, body: dict[str, Any], origin: str) -> None:
            merged = {**src.defaults, **body}
            # A file-default palette is for parsing grids. On a derived
            # sprite it would repaint every cell and undo `swap`, so it
            # only applies to `from` sprites when set explicitly.
            merged.setdefault("default_palette", src.defaults.get("palette"))
            if "from" in body and "palette" not in body:
                merged.pop("palette", None)
            try:
                spec = SpriteSpec.model_validate(merged)
            except ValidationError as e:
                raise BuildError(f"{origin}: {name}: {e}") from e
            resolver.add(Entry(name, spec, spec.sheet or src.sheet, origin))

        for name, body in src.sprites.items():
            make(name, body or {}, path.name)
        for gen in src.generate:
            for vars_ in _expand_for(gen.for_):
                make(_fmt(gen.name, vars_), _fmt(gen.spec, vars_), f"{path.name} (generate {gen.name})")
        for at in src.autotile:
            for mask in range(16):
                layers: list[dict[str, Any]] = [{"sprite": at.base}]
                for bit in at.order:
                    if mask & bit:
                        layers.extend(l.model_dump(exclude_defaults=True) for l in at.bits.get(bit, []))
                body: dict[str, Any] = {"layers": layers}
                if at.palette:
                    body["palette"] = at.palette
                make(f"{at.prefix}{mask}", body, f"{path.name} (autotile {at.prefix})")


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

JOBS = ["einherjar", "onmyoji", "berserker", "martyr", "sacrist", "default"]
DIRS = ["down", "up", "left", "right"]
MOB_TEMPLATES = [
    "fodder_slime", "slime", "alpha_slime", "swime", "mystic_slime",
    "chunky_slime", "toxic_slime", "omega_slime", "default",
]


def required_frames() -> list[str]:
    req: list[str] = []
    req += [f"floor_{i}" for i in range(4)]
    req += [f"wall_{i}" for i in range(16)]
    req += ["void", "stairs_down", "exit_torii"]
    req += [f"hero_{j}_{d}_{f}" for j in JOBS for d in DIRS for f in range(3)]
    req += [f"mob_{t}_{f}" for t in MOB_TEMPLATES for f in range(2)]
    req += [f"battle_{t}_{f}" for t in MOB_TEMPLATES for f in range(2)]
    req += ["ui_cursor", "ui_alert", "ui_item_bag", "bg_shrine_path"]
    return req


# ---------------------------------------------------------------------------
# Packing + output
# ---------------------------------------------------------------------------


@dataclass
class Placed:
    name: str
    sheet: str
    x: int
    y: int
    img: Image.Image
    ax: int
    ay: int


def pack(resolver: Resolver) -> dict[str, list[Placed]]:
    by_sheet: dict[str, list[tuple[str, Image.Image, Entry]]] = {}
    for name, entry in resolver.entries.items():
        if not entry.spec.export:
            continue
        by_sheet.setdefault(entry.sheet, []).append((name, resolver.render(name), entry))

    placed: dict[str, list[Placed]] = {}
    for sheet, items in by_sheet.items():
        width = max(SHEET_MAX_WIDTH, max(img.width for _, img, _ in items) + 2 * PAD)
        x = y = PAD
        shelf_h = 0
        out: list[Placed] = []
        for name, img, entry in items:
            if x + img.width + PAD > width:
                x = PAD
                y += shelf_h + PAD
                shelf_h = 0
            ax = entry.spec.ax if entry.spec.ax is not None else img.width // 2
            ay = entry.spec.ay if entry.spec.ay is not None else img.height
            out.append(Placed(name, sheet, x, y, img, ax, ay))
            x += img.width + PAD
            shelf_h = max(shelf_h, img.height)
        placed[sheet] = out
    return placed


def write_outputs(placed: dict[str, list[Placed]]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atlas: dict[str, Any] = {"tile": TILE, "sheets": {}, "frames": {}}
    for sheet, items in sorted(placed.items()):
        w = max(p.x + p.img.width for p in items) + PAD
        h = max(p.y + p.img.height for p in items) + PAD
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for p in items:
            img.paste(p.img, (p.x, p.y))
        fname = f"{sheet}.png"
        img.save(OUT_DIR / fname, optimize=True)
        atlas["sheets"][sheet] = fname
        for p in items:
            atlas["frames"][p.name] = {
                "sheet": sheet, "x": p.x, "y": p.y,
                "w": p.img.width, "h": p.img.height, "ax": p.ax, "ay": p.ay,
            }
    atlas["frames"] = dict(sorted(atlas["frames"].items()))
    (OUT_DIR / "atlas.json").write_text(json.dumps(atlas, indent=1) + "\n")
    return atlas


# ---------------------------------------------------------------------------
# Previews
# ---------------------------------------------------------------------------


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _checker(w: int, h: int, a: RGBA = (58, 52, 74, 255), b: RGBA = (68, 62, 86, 255), cell: int = 8) -> Image.Image:
    img = Image.new("RGBA", (w, h), a)
    d = ImageDraw.Draw(img)
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            if (xx // cell + yy // cell) % 2:
                d.rectangle([xx, yy, xx + cell - 1, yy + cell - 1], fill=b)
    return img


def contact_sheet(sheet: str, items: list[Placed], scale: int = 4) -> Image.Image:
    font = _font(11)
    label_w = max(int(font.getlength(p.name)) for p in items)
    cell_w = max(max(p.img.width for p in items) * scale, label_w) + 14
    cell_h = max(p.img.height for p in items) * scale + 26
    cols = max(1, min(len(items), 1600 // cell_w))
    rows = (len(items) + cols - 1) // cols
    out = Image.new("RGBA", (cols * cell_w, rows * cell_h + 24), (24, 20, 34, 255))
    d = ImageDraw.Draw(out)
    d.text((6, 4), f"sheet: {sheet}  ({len(items)} frames, x{scale})", fill=(255, 240, 200, 255), font=font)
    for i, p in enumerate(items):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h + 24
        big = p.img.resize((p.img.width * scale, p.img.height * scale), Image.NEAREST)
        bg = _checker(big.width, big.height)
        bg.alpha_composite(big)
        out.paste(bg, (cx + 6, cy + 2))
        d.text((cx + 6, cy + big.height + 6), p.name, fill=(220, 220, 235, 255), font=font)
    return out


SCENE = [
    "######################",
    "######################",
    "###........###########",
    "###........###########",
    "###..a.....#####....##",
    "###..........>......##",
    "###........#####..b.##",
    "###...H....#####....##",
    "###........#####....##",
    "#####..#############.#",
    "#####..#############.#",
    "#####..##.......####.#",
    "#####.........i.....##",
    "#########.......######",
    "######################",
]


def _is_wall(grid: list[str], x: int, y: int) -> bool:
    return not (0 <= y < len(grid) and 0 <= x < len(grid[y])) or grid[y][x] == "#"


def _wall_mask(grid: list[str], x: int, y: int) -> int:
    def floor(xx: int, yy: int) -> bool:
        return 0 <= yy < len(grid) and 0 <= xx < len(grid[yy]) and grid[yy][xx] != "#"

    m = 0
    if floor(x, y - 1):
        m |= 1
    if floor(x + 1, y):
        m |= 2
    if floor(x, y + 1):
        m |= 4
    if floor(x - 1, y):
        m |= 8
    return m


def _blit(canvas: Image.Image, frames: dict[str, Image.Image], atlas: dict[str, Any], name: str, tx: int, ty: int) -> None:
    """Draw frame `name` anchored to tile (tx, ty) bottom-center."""
    f = atlas["frames"][name]
    img = frames[name]
    px = tx * TILE + TILE // 2 - f["ax"]
    py = ty * TILE + TILE - f["ay"]
    canvas.alpha_composite(img, (px, py))


def mock_scene(frames: dict[str, Image.Image], atlas: dict[str, Any], scale: int = 3) -> Image.Image:
    h, w = len(SCENE), len(SCENE[0])
    img = Image.new("RGBA", (w * TILE, h * TILE), (0, 0, 0, 255))
    actors: list[tuple[int, int, str]] = []
    for y, row in enumerate(SCENE):
        for x, ch in enumerate(row):
            hsh = ((x * 73856093) ^ (y * 19349663)) & 0xFFFF
            if ch == "#":
                m = _wall_mask(SCENE, x, y)
                # Recommended renderer rule: walls touching floor in any of the
                # 8 directions draw wall_<mask> (wall_0 for diagonal-only);
                # rock with no floor around it is `void`.
                near = any(
                    0 <= y + dy < h and 0 <= x + dx < w and SCENE[y + dy][x + dx] != "#"
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                )
                _blit(img, frames, atlas, f"wall_{m}" if near else "void", x, y)
                continue
            walls_ns = _is_wall(SCENE, x, y - 1) and _is_wall(SCENE, x, y + 1)
            walls_ew = _is_wall(SCENE, x - 1, y) and _is_wall(SCENE, x + 1, y)
            corridor = "corridor_0" in frames and (walls_ns or walls_ew)
            _blit(img, frames, atlas, f"corridor_{hsh % 2}" if corridor else f"floor_{hsh % 4}", x, y)
            if ch == ".":
                if hsh % 11 == 0 and "decor_grass_0" in frames:
                    _blit(img, frames, atlas, f"decor_grass_{hsh % 3}", x, y)
            elif ch == ">":
                _blit(img, frames, atlas, "stairs_down", x, y)
            elif ch == "i":
                _blit(img, frames, atlas, "ui_item_bag", x, y)
            elif ch == "H":
                actors.append((y, x, "hero"))
            elif ch in "ab":
                actors.append((y, x, ch))
    # decor along the top wall face of the big room
    for (x, y, name) in ((4, 2, "decor_lantern"), (9, 2, "decor_lantern"), (16, 4, "decor_bamboo")):
        if name in frames:
            _blit(img, frames, atlas, name, x, y)
    for y, x, kind in sorted(actors):
        if kind == "hero":
            _blit(img, frames, atlas, "hero_onmyoji_down_0", x, y)
            _blit(img, frames, atlas, "hero_einherjar_right_1", x - 1, y)
            _blit(img, frames, atlas, "hero_martyr_up_0", x, y + 1)
        elif kind == "a":
            _blit(img, frames, atlas, "mob_slime_0", x, y)
            _blit(img, frames, atlas, "mob_swime_1", x + 1, y)
        else:
            _blit(img, frames, atlas, "mob_mystic_slime_0", x, y)
            _blit(img, frames, atlas, "mob_toxic_slime_1", x - 1, y + 1)
            _blit(img, frames, atlas, "ui_alert", x, y - 1)
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def mock_battle(frames: dict[str, Image.Image], scale: int = 3) -> Image.Image:
    bg = frames["bg_shrine_path"].copy()
    W, H = bg.size
    lineup = ["battle_chunky_slime_0", "battle_omega_slime_0", "battle_mystic_slime_1"]
    imgs = [frames[n] for n in lineup]
    ground = int(H * 0.86)
    slots = [W * 0.22, W * 0.5, W * 0.78]
    for img, sx in zip(imgs, slots, strict=True):
        bg.alpha_composite(img, (int(sx - img.width / 2), ground - img.height))
    cur = frames["ui_cursor"]
    bg.alpha_composite(cur, (int(slots[1] - cur.width / 2), ground - imgs[1].height - cur.height - 1))
    # fake menu box to judge contrast against UI
    out = Image.new("RGBA", (W, H + 40), (20, 14, 30, 255))
    out.paste(bg, (0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle([2, H + 2, W - 3, H + 37], outline=(255, 240, 200, 255), fill=(34, 26, 60, 255))
    font = _font(9)
    d.text((8, H + 6), "Chunky Lv4  Omega Lv8  Mystic Lv5", fill=(255, 255, 255, 255), font=font)
    d.text((8, H + 20), "> Attack   Survive   Cheat   Item", fill=(255, 224, 120, 255), font=font)
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def write_previews(placed: dict[str, list[Placed]], atlas: dict[str, Any]) -> list[Path]:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    frames = {p.name: p.img for items in placed.values() for p in items}
    for sheet, items in sorted(placed.items()):
        path = PREVIEW_DIR / f"sheet_{sheet}.png"
        contact_sheet(sheet, items).save(path)
        written.append(path)
    path = PREVIEW_DIR / "mock_scene.png"
    mock_scene(frames, atlas).save(path)
    written.append(path)
    path = PREVIEW_DIR / "mock_battle.png"
    mock_battle(frames).save(path)
    written.append(path)
    return written


# ---------------------------------------------------------------------------


def build(check_only: bool) -> int:
    palettes = load_palettes(SRC_DIR / "palettes.yaml")
    resolver = Resolver(palettes)
    load_sources(resolver)

    missing = [n for n in required_frames() if n not in resolver.entries or not resolver.entries[n].spec.export]
    if missing:
        raise BuildError(
            f"atlas contract: {len(missing)} required frame(s) missing:\n  " + "\n  ".join(missing)
        )
    placed = pack(resolver)  # renders everything → surfaces palette errors
    n_frames = sum(len(v) for v in placed.values())
    if check_only:
        print(f"ok: {n_frames} frames across {len(placed)} sheets (check only, nothing written)")
        return 0
    atlas = write_outputs(placed)
    previews = write_previews(placed, atlas)
    print(f"wrote {n_frames} frames, {len(placed)} sheets -> {OUT_DIR}")
    for p in previews:
        print(f"preview: {p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate sources only")
    args = ap.parse_args()
    try:
        return build(args.check)
    except BuildError as e:
        print(f"art build FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
