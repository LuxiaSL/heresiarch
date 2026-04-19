"""ParticleField -- animated ambient particle backdrop widget.

A lightweight 2D particle system rendered into a Rich Text grid and
updated on a Textual timer.  Designed to drop into any container as a
layered backdrop behind foreground content.

The widget owns its own render loop and manages particle spawning,
advection, and respawn.  Particles carry a life/brightness curve that
maps into a color ramp for fading in/out, and a character ramp for
sizing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from rich.text import Text
from textual.widget import Widget


SpawnEdge = Literal["bottom", "top", "any"]


@dataclass(frozen=True, slots=True)
class ParticleTheme:
    """Visual + motion configuration for a ``ParticleField``.

    All speeds are in cells-per-second; lifetimes in seconds.  The color
    ramp is indexed dim-to-bright by ``life`` (0.0 -> 1.0).  The character
    ramp is sampled per-particle at spawn and held for the particle's
    lifetime, giving visual variety without per-frame ramp indexing.
    """

    chars: tuple[str, ...] = ("\u00b7", "\u2219", "\u2022", "\u25cf")
    colors: tuple[str, ...] = (
        "#1a1428",
        "#241c3a",
        "#2a2244",
        "#3a2a5a",
        "#5c4480",
        "#8266a8",
    )
    count: int = 48
    drift_x: float = 0.0
    drift_y: float = -2.0  # negative = rising
    jitter: float = 0.4
    lifetime_min: float = 4.0
    lifetime_max: float = 9.0
    spawn_edge: SpawnEdge = "bottom"
    fps: float = 10.0


@dataclass(slots=True)
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float  # 1.0 (fresh) -> 0.0 (dead)
    life_decay: float  # per-second decay rate (= 1 / lifetime)
    char_idx: int


class ParticleField(Widget):
    """Animated particle backdrop.

    Use as a layered widget -- put it on a lower layer than foreground
    content, size it to cover the area you want animated.  The widget
    handles resize, particle spawning, advection, and respawn.

    Example CSS::

        Screen { layers: bg fg; }
        #backdrop { layer: bg; width: 100%; height: 100%; }
        #content  { layer: fg; }
    """

    DEFAULT_CSS = """
    ParticleField {
        width: 100%;
        height: 100%;
    }
    """

    def render(self) -> Text:
        """Render the current particle grid as a single Rich Text."""
        return self._build_text()

    def __init__(
        self,
        theme: ParticleTheme | None = None,
        *,
        rng_seed: int | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._theme: ParticleTheme = (
            theme if theme is not None else ParticleTheme()
        )
        self._particles: list[_Particle] = []
        self._rng: random.Random = (
            random.Random(rng_seed)
            if rng_seed is not None
            else random.Random()
        )
        self._w: int = 0
        self._h: int = 0

    def on_mount(self) -> None:
        interval = 1.0 / max(self._theme.fps, 1.0)
        self.set_interval(interval, self._tick)

    # -- particle management -----------------------------------------

    def _reinitialize(self) -> None:
        """Seed particles spread throughout the viewport."""
        self._particles.clear()
        if self._w <= 0 or self._h <= 0:
            return
        for _ in range(self._theme.count):
            self._particles.append(self._spawn(initial=True))

    def _spawn(self, *, initial: bool = False) -> _Particle:
        theme = self._theme
        rng = self._rng
        w = max(self._w - 1, 1)
        h = max(self._h - 1, 1)

        if initial:
            # Pre-distribute across the viewport with random ages so the
            # field looks "in motion" rather than all spawning at once.
            x = rng.uniform(0.0, float(w))
            y = rng.uniform(0.0, float(h))
            life = rng.uniform(0.3, 1.0)
        else:
            edge = theme.spawn_edge
            if edge == "bottom":
                x = rng.uniform(0.0, float(w))
                y = float(h)
            elif edge == "top":
                x = rng.uniform(0.0, float(w))
                y = 0.0
            else:  # "any"
                x = rng.uniform(0.0, float(w))
                y = rng.uniform(0.0, float(h))
            life = 1.0

        lifetime = rng.uniform(theme.lifetime_min, theme.lifetime_max)
        if lifetime <= 0.0:
            lifetime = 1.0
        vx = theme.drift_x + rng.uniform(-theme.jitter, theme.jitter)
        vy = theme.drift_y + rng.uniform(-theme.jitter, theme.jitter)
        char_idx = rng.randint(0, len(theme.chars) - 1)

        return _Particle(
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            life=life,
            life_decay=1.0 / lifetime,
            char_idx=char_idx,
        )

    # -- tick ---------------------------------------------------------

    def _tick(self) -> None:
        # Re-sync to current widget size (handles initial mount + resize).
        size = self.size
        if size.width != self._w or size.height != self._h:
            self._w = size.width
            self._h = size.height
            self._reinitialize()

        if self._w <= 0 or self._h <= 0 or not self._particles:
            return

        theme = self._theme
        dt = 1.0 / max(theme.fps, 1.0)
        jitter_kick = theme.jitter * dt
        rng = self._rng
        w = self._w
        h = self._h

        for i, p in enumerate(self._particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx += rng.uniform(-jitter_kick, jitter_kick)
            p.vy += rng.uniform(-jitter_kick, jitter_kick)
            p.life -= p.life_decay * dt

            if (
                p.life <= 0.0
                or p.x < -1.0
                or p.x > float(w)
                or p.y < -1.0
                or p.y > float(h)
            ):
                self._particles[i] = self._spawn()

        self.refresh()

    # -- render -------------------------------------------------------

    def _build_text(self) -> Text:
        theme = self._theme
        chars = theme.chars
        colors = theme.colors
        n_colors = len(colors)
        w = self._w
        h = self._h

        # Sparse cell map -- only cells touched by a particle.
        # Last writer wins (cheap and visually fine at these densities).
        cells: dict[int, tuple[str, str]] = {}

        for p in self._particles:
            ix = int(p.x)
            iy = int(p.y)
            if ix < 0 or ix >= w or iy < 0 or iy >= h:
                continue
            c_idx = int(p.life * n_colors)
            if c_idx < 0:
                c_idx = 0
            elif c_idx >= n_colors:
                c_idx = n_colors - 1
            cells[iy * w + ix] = (chars[p.char_idx], colors[c_idx])

        # Emit one Text with per-row run-length-encoded styling.  Runs
        # of empty cells collapse to a single unstyled append, which
        # is the common case -- most cells are empty on any given tick.
        text = Text(no_wrap=True)
        for row in range(h):
            base = row * w
            run_chars: list[str] = []
            current_style: str = ""
            for col in range(w):
                cell = cells.get(base + col)
                if cell is None:
                    ch, style = " ", ""
                else:
                    ch, style = cell
                if style != current_style:
                    if run_chars:
                        text.append(
                            "".join(run_chars),
                            style=current_style or None,
                        )
                        run_chars.clear()
                    current_style = style
                run_chars.append(ch)
            if run_chars:
                text.append(
                    "".join(run_chars), style=current_style or None
                )
            if row < h - 1:
                text.append("\n")
        return text


# ---------------------------------------------------------------------------
# Preset themes
# ---------------------------------------------------------------------------

# Slow purple motes rising -- matches the title breathing palette.
THEME_TITLE_EMBERS: ParticleTheme = ParticleTheme(
    chars=("\u00b7", "\u2219", "\u2022", "\u25cf"),
    colors=(
        "#140f1f",
        "#1c162d",
        "#241c3a",
        "#3a2a5a",
        "#5c4480",
        "#8266a8",
    ),
    count=56,
    drift_x=0.15,
    drift_y=-1.8,
    jitter=0.35,
    lifetime_min=5.0,
    lifetime_max=11.0,
    spawn_edge="bottom",
    fps=10.0,
)

# Cold falling ash -- dead run, dark souls energy.
THEME_DEATH_ASH: ParticleTheme = ParticleTheme(
    chars=("\u00b7", "\u2219", "'", "."),
    colors=(
        "#0a0606",
        "#140808",
        "#1f0a0a",
        "#2f1010",
        "#4a1616",
        "#661c1c",
    ),
    count=44,
    drift_x=-0.3,
    drift_y=1.4,
    jitter=0.15,
    lifetime_min=7.0,
    lifetime_max=14.0,
    spawn_edge="top",
    fps=8.0,
)
