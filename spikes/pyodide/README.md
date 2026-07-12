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

## Build + serve

```bash
uv run python spikes/pyodide/build.py    # stage dist/ (~18 MiB, self-contained)
uv run python spikes/pyodide/serve.py    # static host on :8643, prints LAN URL
```

`build.py --refresh` re-downloads the pyodide runtime (version pinned
in the script). dist/ is gitignored.

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

- The service worker needs a secure context to cache for offline
  (https, localhost, or Chrome's insecure-origin flag for a LAN IP) —
  same caveat as the LAN PWA, printed by `python -m heresiarch.mobile`.
- One session per page; no cross-device save sync.
- iOS may evict IndexedDB for rarely-used sites; export/import of
  saves is future work if this graduates.
