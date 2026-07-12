# Pyodide spike — Heresiarch serverless in the browser

The Python engine compiled to nothing: the stock mobile client
(`src/heresiarch/mobile/static/index.html`) running against wasm
CPython in the page itself. No FastAPI, no LAN server, no network
after first load. See design/mobile-spike.md for the decision context.

## How it fits together

- The client has one transport seam (`transport()` in index.html).
  When `window.HX_LOCAL_DISPATCH` exists, every `/api/*` call goes to
  it instead of `fetch()`.
- `boot.js` defines that hook synchronously, then boots Pyodide,
  loads pydantic+pyyaml from the vendored index, unpacks the
  heresiarch wheel and `data.zip`, and runs `bootstrap.py`.
- `bootstrap.py` builds one `GameSession` and exposes
  `hx_handle(path, body_json)`, which mirrors the FastAPI routes by
  calling the same `heresiarch.mobile.dispatch` functions the LAN
  server uses. The client cannot tell the transports apart.
- Saves and notes live under `/persist`, an IndexedDB mount — runs
  survive page reloads.

## Live deployment

**https://luxiasl.github.io/heresiarch/** — deployed by
`.github/workflows/pages.yml` on every push to main. Being https, the
install is first-class on Android: Chrome menu → Add to Home screen →
Install → fullscreen, offline-capable, saves in IndexedDB. Installed
phones pick up new deploys automatically on their next online launch
(network-first service worker).

## Build + serve locally

```bash
uv run python spikes/pyodide/build.py    # stage dist/ (~18 MiB, self-contained)
uv run python spikes/pyodide/serve.py    # static host on :8643, prints LAN URL
```

`build.py --refresh` re-downloads the pyodide runtime (version pinned
in the script — keep the workflow's cache key in sync). dist/ is
gitignored. All client URLs are relative, so the same bundle works at
the LAN root and under the Pages subpath.

## Headless verification

```bash
npm install pyodide   # anywhere; point PYODIDE_NODE_MODULES at it if not cwd
node spikes/pyodide/verify_node.mjs
```

Mirrors boot.js step-for-step against the staged dist/ and drives
new run → zone → full combat → loot through `hx_handle`. Exit 0 means
the browser build's engine path works. Verified 2026-07-11: pyodide
314.0.2 (CPython 3.14), boot→engine-ready ≈4 s, combat resolves, all
packages from the vendored index (no CDN).

## Known limits (spike cuts)

- Over plain-http LAN serving, the service worker needs Chrome's
  insecure-origin flag (same caveat as the LAN PWA, printed by
  `python -m heresiarch.mobile`). The Pages deployment is https, so
  none of that applies there.
- One session per page; no automatic cross-device save sync — but the
  title screen has per-slot export (downloads the save JSON) and
  import (validated before write), which doubles as device transfer
  and as insurance against browser storage eviction. LAN-server saves
  live in `artifacts/mobile/agent_saves/*.json` and import directly.
- Persistence details: saves flush to IndexedDB debounced 500 ms after
  each action, immediately on import, and on pagehide/hidden.
