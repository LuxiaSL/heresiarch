"""Serve the staged serverless build (spikes/pyodide/dist/) on the LAN.

A plain static file server — no game logic, no session, no API. The
stdlib http.server guesses some MIME types wrong for wasm-era assets,
which breaks module loading; this pins the ones that matter.

    uv run python spikes/pyodide/serve.py [--port 8643]
"""

from __future__ import annotations

import argparse
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DIST = Path(__file__).parent / "dist"


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
        ".webmanifest": "application/manifest+json",
        ".whl": "application/octet-stream",
    }

    def end_headers(self) -> None:
        # Dev server: always revalidate; the service worker does the caching
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass  # quiet


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except OSError:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8643)
    args = parser.parse_args()

    if not (DIST / "index.html").exists():
        raise SystemExit(
            "dist/ is not staged — run: uv run python spikes/pyodide/build.py"
        )

    print()
    print("  Heresiarch serverless — open on your phone:")
    print(f"    http://{_lan_ip()}:{args.port}")
    print()
    print("  The engine runs in the browser; this server only hands out files.")
    print()

    handler = partial(Handler, directory=str(DIST))
    ThreadingHTTPServer((args.host, args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
