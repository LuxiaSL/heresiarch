"""Self-test for the art compiler's failure modes.

    uv run --with pillow python art/tools/selftest.py

Checks that bad sources fail loudly (ragged rows, spaces, unknown palette
chars, unknown sprites/palettes) and that the atlas contract notices a
missing required frame. Exits non-zero on any miss.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build as b  # noqa: E402


def main() -> int:
    failures = 0
    pal = b.load_palettes(b.SRC_DIR / "palettes.yaml")

    def expect(fn: Callable[[], object], label: str) -> None:
        nonlocal failures
        try:
            fn()
        except b.BuildError as e:
            print(f"ok   {label}: {str(e).splitlines()[0]}")
            return
        failures += 1
        print(f"FAIL {label}: no BuildError raised")

    expect(lambda: b.parse_grid("KK\nK", "shrine", "t: ragged"), "ragged rows")
    expect(lambda: b.parse_grid("K K", "shrine", "t: space"), "space in grid")

    r = b.Resolver(pal)
    r.add(b.Entry("bad_char", b.SpriteSpec(grid="K!", palette="shrine"), "s", "t.yaml"))
    expect(lambda: r.render("bad_char"), "char not in palette")
    r.add(b.Entry("bad_from", b.SpriteSpec.model_validate({"from": "nope"}), "s", "t.yaml"))
    expect(lambda: r.resolve("bad_from"), "unknown `from` sprite")
    r.add(b.Entry("bad_pal", b.SpriteSpec(grid="K", palette="nopal"), "s", "t.yaml"))
    expect(lambda: r.resolve("bad_pal"), "unknown palette")
    expect(lambda: r.add(b.Entry("bad_pal", b.SpriteSpec(grid="K", palette="shrine"), "s", "u.yaml")),
           "duplicate sprite name")

    full = b.Resolver(pal)
    b.load_sources(full)
    del full.entries["wall_7"]
    missing = [n for n in b.required_frames() if n not in full.entries]
    if missing == ["wall_7"]:
        print("ok   contract notices a missing required frame")
    else:
        failures += 1
        print(f"FAIL contract check: {missing}")

    print("selftest:", "PASS" if not failures else f"{failures} FAILURE(S)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
