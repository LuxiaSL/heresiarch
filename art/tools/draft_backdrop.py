"""Drafting helper: procedurally lay out the shrine-path battle backdrop.

Prints a backdrops YAML (160x96, `shrine` palette chars) to stdout. Like the
slime drafts, the output grid is the source of truth once committed; rerun
this only to start a backdrop over.

    uv run python art/tools/draft_backdrop.py > /tmp/backdrop.yaml
"""

from __future__ import annotations

import math

W, H = 160, 96
HORIZON = 50



def main() -> None:
    g = [["." for _ in range(W)] for _ in range(H)]

    def put(x: int, y: int, c: str) -> None:
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    # --- sky: lavender -> pink -> peach -> cream, dithered band edges
    bands = [(0, "L"), (12, "F"), (26, "E"), (38, "D")]
    for y in range(HORIZON):
        idx = max(i for i, (y0, _) in enumerate(bands) if y >= y0)
        c = bands[idx][1]
        nxt = bands[idx + 1] if idx + 1 < len(bands) else None
        for x in range(W):
            cc = c
            if nxt and nxt[0] - y <= 2:
                d = nxt[0] - y
                if (d == 2 and (x + y) % 4 == 0) or (d == 1 and (x + y) % 2 == 0):
                    cc = nxt[1]
            g[y][x] = cc

    # --- sun disc behind the gate
    sx, sy, sr = 80, 30, 11
    for y in range(sy - sr, sy + sr + 1):
        for x in range(sx - sr, sx + sr + 1):
            d = math.hypot(x - sx, y - sy)
            if d <= sr:
                put(x, y, "P" if d < sr - 1.5 else "D")

    # --- far mountains (two layers)
    for x in range(W):
        h1 = 40 + 5 * math.sin(x / 13.0) + 3 * math.sin(x / 5.3 + 1)
        h2 = 45 + 3 * math.sin(x / 9.0 + 2) + 2 * math.sin(x / 3.7)
        for y in range(int(h1), HORIZON):
            put(x, y, "x")
        for y in range(int(h2), HORIZON):
            put(x, y, "y")
        put(x, int(h1), "w")

    # --- ground
    for y in range(HORIZON, H):
        for x in range(W):
            g[y][x] = "n"
    for y in range(HORIZON, H):  # grass texture
        for x in range(W):
            if (x * 7 + y * 13) % 11 == 0:
                g[y][x] = "m"
            elif (x * 5 + y * 3) % 13 == 0:
                g[y][x] = "o"

    # --- stone path in perspective
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        half = 6 + t * 62
        x0, x1 = int(80 - half), int(80 + half)
        for x in range(x0, x1 + 1):
            # paving courses get taller toward the viewer
            course = int(math.log1p(t * 12) * 6)
            u = (x - 80) / max(1.0, half)  # -1..1 across the path
            seam_x = int((u + 1) * (3 + course % 2 * 0.5) * 2) != int(((x + 1 - 80) / max(1.0, half) + 1) * (3 + course % 2 * 0.5) * 2)
            row_top = int(math.log1p(((y - 1) - HORIZON) / (H - HORIZON) * 12) * 6) != course
            if row_top:
                c = "r"
            elif seam_x:
                c = "r"
            else:
                c = "p" if u < -0.3 else "q"
            put(x, y, c)
        put(x0 - 1, y, "o")
        put(x1 + 1, y, "o")

    # --- cedar trees, left and right
    def cedar(cx: int, base: int, height: int, width: int) -> None:
        for y in range(base - height, base):
            t = (y - (base - height)) / height
            half = max(1, int(width * t * 0.5 + 0.5))
            # jagged tiers
            if int(t * 6) % 2 == 1:
                half = max(1, half - 1)
            for x in range(cx - half, cx + half + 1):
                c = "d" if x < cx - half // 3 else ("e" if x > cx + half // 3 else "d")
                if x == cx - half or x == cx + half:
                    c = "K"
                put(x, y, c)
            if t > 0.15 and (y % 4 == 0):
                put(cx - half + 1, y, "c")
        for y in range(base, base + 4):
            put(cx, y, "C")
            put(cx + 1, y, "C")

    for cx, base, hgt, wd in [(6, 62, 54, 22), (24, 58, 46, 18), (38, 55, 34, 14),
                              (154, 62, 54, 22), (136, 58, 46, 18), (122, 55, 34, 14),
                              (-4, 70, 60, 26), (164, 70, 60, 26)]:
        cedar(cx, base, hgt, wd)

    # --- torii: big one framing the arena, two smaller receding ones
    def torii(cx: int, top: int, span: int, height: int) -> None:
        beam = max(1, height // 12)
        # kasagi (top beam), overhanging, dark cap
        for y in range(top, top + beam + 1):
            for x in range(cx - span // 2 - beam * 2, cx + span // 2 + beam * 2 + 1):
                put(x, y, "U" if y == top else "S")
        for x in range(cx - span // 2 - beam * 2 - 1, cx + span // 2 + beam * 2 + 2):
            put(x, top - 1, "K")
            put(x, top + beam + 1, "K")
        # nuki (tie beam)
        ny = top + beam * 3 + 2
        for y in range(ny, ny + max(1, beam)):
            for x in range(cx - span // 2 - beam, cx + span // 2 + beam + 1):
                put(x, y, "T")
        for x in range(cx - span // 2 - beam - 1, cx + span // 2 + beam + 2):
            put(x, ny - 1, "K")
            put(x, ny + max(1, beam), "K")
        # pillars
        pw = max(2, beam + 1)
        for px in (cx - span // 2, cx + span // 2 - pw + 1):
            for y in range(top + beam + 2, top + height):
                put(px - 1, y, "K")
                put(px + pw, y, "K")
                for x in range(px, px + pw):
                    put(x, y, "R" if x == px else ("T" if x == px + pw - 1 else "S"))
            for x in range(px - 1, px + pw + 1):
                put(x, top + height, "K")
                put(x, top + height - 1, "z")

    torii(80, 14, 76, 62)

    # --- stone lanterns flanking the path
    def lantern(cx: int, base: int, s: int) -> None:
        for y in range(base - 5 * s, base):
            t = (base - y) / (5 * s)
            half = s if t < 0.5 else (s // 2 if t < 0.7 else s)
            for x in range(cx - half, cx + half + 1):
                c = "w" if x < cx else "y"
                if 0.5 <= t < 0.7:
                    c = "G" if x != cx - half and x != cx + half else "K"
                put(x, y, c)
            put(cx - half - 1, y, "K")
            put(cx + half + 1, y, "K")

    lantern(9, 78, 3)
    lantern(151, 78, 3)
    lantern(52, 66, 2)
    lantern(108, 66, 2)

    lines = ["# Battle backdrops. 160x96, `shrine` palette. Drafted by",
             "# art/tools/draft_backdrop.py; this grid is the source of truth.",
             "sheet: backdrops", "defaults:", "  palette: shrine", "  ax: 0", "  ay: 0", "",
             "sprites:", "  bg_shrine_path:", "    grid: |"]
    lines += ["      " + "".join(r) for r in g]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
