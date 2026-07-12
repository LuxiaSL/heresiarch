"""Stage a fully self-contained, serverless Heresiarch web build.

Output: spikes/pyodide/dist/ — the real mobile client (index.html,
PWA shell) plus boot.js, the engine wheel, zipped YAML data, and a
vendored Pyodide runtime with the pydantic/pyyaml wheel closure.
Everything is local: after the first page load the game runs with no
server and no network (the service worker caches what it fetched).

Usage:
    uv run python spikes/pyodide/build.py             # stage dist/
    uv run python spikes/pyodide/build.py --refresh   # re-download pyodide
    uv run python spikes/pyodide/serve.py             # then serve it
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PYODIDE_VERSION = "314.0.2"
CDN = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

# Core runtime files of the pyodide distribution
CORE_FILES = [
    "pyodide.js",
    "pyodide.asm.mjs",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
]

# Engine dependency roots; the lockfile closure is vendored from these
PACKAGE_ROOTS = ["pydantic", "pyyaml"]

SPIKE_DIR = Path(__file__).parent
REPO = SPIKE_DIR.parent.parent
DIST = SPIKE_DIR / "dist"
STATIC = REPO / "src" / "heresiarch" / "mobile" / "static"

BOOT_TAG = '<script src="./boot.js"></script>'


def log(msg: str) -> None:
    print(f"  {msg}")


def build_wheel() -> None:
    subprocess.run(
        ["uv", "build", "--wheel"], cwd=REPO, check=True, capture_output=True,
    )
    wheels = sorted((REPO / "dist").glob("heresiarch-*-py3-none-any.whl"))
    if not wheels:
        sys.exit("uv build produced no wheel in dist/")
    shutil.copy(wheels[-1], DIST / "heresiarch.whl")
    log(f"engine wheel: {wheels[-1].name}")


def zip_data() -> None:
    out = DIST / "data.zip"
    data_dir = REPO / "data"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(data_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(data_dir))
    log(f"data.zip: {out.stat().st_size // 1024} KiB")


def stage_client() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    if BOOT_TAG not in html:
        # boot.js must run before the client's inline script so the
        # HX_LOCAL_DISPATCH seam exists by the first transport() call
        html = html.replace("<body>", f"<body>\n{BOOT_TAG}", 1)
        if BOOT_TAG not in html:
            sys.exit("could not inject boot.js: <body> tag not found")
    (DIST / "index.html").write_text(html, encoding="utf-8")

    shutil.copy(SPIKE_DIR / "boot.js", DIST / "boot.js")
    shutil.copy(SPIKE_DIR / "bootstrap.py", DIST / "bootstrap.py")
    for name in ("manifest.webmanifest", "sw.js"):
        shutil.copy(STATIC / name, DIST / name)
    shutil.copytree(STATIC / "icons", DIST / "icons", dirs_exist_ok=True)
    # Belt-and-braces for GitHub Pages: never run Jekyll over the bundle
    (DIST / ".nojekyll").touch()
    log("client staged (index.html + boot.js + PWA shell)")


def _download(name: str, dest: Path) -> None:
    url = CDN + name
    with urllib.request.urlopen(url, timeout=120) as res:
        dest.write_bytes(res.read())
    log(f"pyodide/{name}: {dest.stat().st_size // 1024} KiB")


def package_closure(lock: dict) -> list[str]:
    """Wheel filenames for PACKAGE_ROOTS plus transitive depends."""
    packages = lock["packages"]
    seen: set[str] = set()
    queue = list(PACKAGE_ROOTS)
    files: list[str] = []
    while queue:
        name = queue.pop()
        key = name.replace("_", "-").lower()
        if key in seen:
            continue
        seen.add(key)
        entry = packages.get(key) or packages.get(name)
        if entry is None:
            sys.exit(f"package {name!r} not in pyodide lockfile")
        files.append(entry["file_name"])
        queue.extend(entry.get("depends", []))
    return files


def vendor_pyodide(refresh: bool) -> None:
    vendor = DIST / "pyodide"
    lock_path = vendor / "pyodide-lock.json"
    if refresh and vendor.exists():
        shutil.rmtree(vendor)
    vendor.mkdir(parents=True, exist_ok=True)

    for name in CORE_FILES:
        if not (vendor / name).exists():
            _download(name, vendor / name)

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    got_python = lock["info"]["python"]
    log(f"pyodide {PYODIDE_VERSION} (CPython {got_python})")

    for file_name in package_closure(lock):
        if not (vendor / file_name).exists():
            _download(file_name, vendor / file_name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true",
        help="re-download the vendored pyodide runtime",
    )
    args = parser.parse_args()

    DIST.mkdir(parents=True, exist_ok=True)
    print("Staging serverless build:")
    build_wheel()
    zip_data()
    stage_client()
    vendor_pyodide(refresh=args.refresh)
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"Done: {DIST} ({total / 1_048_576:.1f} MiB)")
    print("Serve it:  uv run python spikes/pyodide/serve.py")


if __name__ == "__main__":
    main()
