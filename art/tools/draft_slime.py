"""Drafting helper: print slime body grids (dome lit from top-left) as YAML.

Not part of the build. The YAML in art/src is the source of truth; this
only produced the first pass of the body shapes, which were then edited
by hand. Kept so new body sizes can be drafted the same way:

    uv run python art/tools/draft_slime.py > /tmp/bodies.yaml
"""

from __future__ import annotations

import math

# name: (W, H, rx, ry_top, ry_bot, base_y, eye_dx, eye_y, eye_h, eye_w)
BODIES: dict[str, tuple[int, int, float, float, float, int, float, int, int, int]] = {
    "body16_small_0": (16, 16, 5.0, 5.5, 1.6, 14, 2, 10, 2, 1),
    "body16_small_1": (16, 16, 5.6, 4.6, 1.5, 14, 2, 11, 2, 1),
    "body16_0": (16, 16, 6.2, 7.5, 1.8, 14, 2.5, 9, 2, 1),
    "body16_1": (16, 16, 6.8, 6.4, 1.7, 14, 2.5, 10, 2, 1),
    "body16_wide_0": (16, 16, 7.0, 6.5, 2.0, 14, 3, 10, 2, 1),
    "body16_wide_1": (16, 16, 7.3, 5.6, 2.0, 14, 3, 11, 2, 1),
    "body24_0": (24, 24, 9.5, 11.0, 2.5, 22, 3.5, 14, 3, 1),
    "body24_1": (24, 24, 10.3, 9.6, 2.4, 22, 3.5, 15, 3, 1),
    "body32_small_0": (32, 32, 10.0, 10.5, 3.0, 29, 4, 21, 4, 2),
    "body32_small_1": (32, 32, 11.0, 9.0, 2.8, 29, 4, 22, 4, 2),
    "body32_0": (32, 32, 13.0, 14.5, 3.5, 29, 5, 18, 5, 2),
    "body32_1": (32, 32, 14.0, 12.8, 3.3, 29, 5, 19, 5, 2),
    "body32_wide_0": (32, 32, 14.8, 12.5, 4.0, 29, 6, 19, 4, 2),
    "body32_wide_1": (32, 32, 15.4, 11.0, 4.0, 29, 6, 20, 4, 2),
    "body48_0": (48, 48, 20.0, 22.0, 5.0, 45, 7, 28, 6, 3),
    "body48_1": (48, 48, 21.5, 19.5, 4.8, 45, 7, 30, 6, 3),
}


def body(
    W: int, H: int, rx: float, ry_top: float, ry_bot: float, base_y: int,
    eye_dx: float, eye_y: int, eye_h: int, eye_w: int,
) -> list[str]:
    cx = (W - 1) / 2
    cy = base_y - ry_bot
    inside = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx = (x - cx) / rx
            dy = (y - cy) / (ry_top if y <= cy else ry_bot)
            p = 2.0 if y <= cy else 4.0  # flatter base below the equator
            inside[y][x] = abs(dx) ** 2 + abs(dy) ** p <= 1.0
    g = [["."] * W for _ in range(H)]
    # Sphere shading: one radius set for the whole dome so the bands are
    # concentric arcs (not horizontal stripes); light from the upper left.
    lx, ly, lz = -0.5, -0.72, 0.48
    n = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / n, ly / n, lz / n
    bottom = max(y for y in range(H) for x in range(W) if inside[y][x])
    for y in range(H):
        for x in range(W):
            if not inside[y][x]:
                continue
            nx = (x - cx) / rx
            ny = (y - cy) / ry_top
            nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
            v = nx * lx + ny * ly + nz * lz
            c = "1" if v > 0.975 else "2" if v > 0.84 else "3" if v > 0.52 else "4" if v > 0.18 else "5"
            if y >= bottom - (0 if H < 24 else 1) and c in "23":
                c = "4"  # contact shadow along the base
            g[y][x] = c
    for y in range(H):
        for x in range(W):
            if inside[y][x]:
                continue
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + ddx, y + ddy
                if 0 <= xx < W and 0 <= yy < H and inside[yy][xx]:
                    g[y][x] = "K"
                    break
    if H >= 48:  # big bodies: keep the gloss clear of brows/eyes
        for y in range(eye_y - 3, eye_y):
            g[y] = ["2" if c == "1" else c for c in g[y]]
    left = math.floor(cx - eye_dx - (eye_w - 1) / 2)
    for ex in (left, W - 1 - left - (eye_w - 1)):  # mirror-exact pair
        for k in range(eye_h):
            for j in range(eye_w):
                g[eye_y + k][ex + j] = "e"
        if eye_h >= 3:
            g[eye_y][ex + (eye_w - 1 if eye_w > 1 else 0)] = "w"
    if W >= 24:
        my, mx = eye_y + eye_h + 1, round(cx)
        g[my][mx - 1] = g[my][mx] = "m"
    sy = base_y + 1
    if sy < H:
        for x in range(W):
            if g[sy][x] == "." and abs(x - cx) <= rx * 0.85:
                g[sy][x] = "s"
    return ["".join(r) for r in g]


def main() -> None:
    for name, cfg in BODIES.items():
        print(f"  {name}:")
        print("    grid: |")
        for r in body(*cfg):
            print("      " + r)


if __name__ == "__main__":
    main()
