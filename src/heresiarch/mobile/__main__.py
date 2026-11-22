"""Entry point: python -m heresiarch.mobile

Serves the phone UI on the LAN. Prints the address to open on the phone.
"""

from __future__ import annotations

import argparse
import socket


def _lan_ip() -> str:
    """Best-effort LAN IP discovery (no traffic is actually sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except OSError:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Heresiarch mobile sniff test")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8642)
    parser.add_argument(
        "--linear", action="store_true",
        help="classic linear zones (Fight button) instead of dungeon floors",
    )
    args = parser.parse_args()

    import uvicorn

    from heresiarch.mobile.app import create_app

    origin = f"http://{_lan_ip()}:{args.port}"
    print()
    print("  Heresiarch mobile — open on your phone:")
    print(f"    {origin}")
    print()
    print("  Install to homescreen (fullscreen launch):")
    print("    iOS: Share → Add to Home Screen (works over plain http)")
    print("    Android: needs a secure context for install + offline shell —")
    print("      add this origin under chrome://flags/#unsafely-treat-insecure-origin-as-secure")
    print(f"      ({origin}), relaunch Chrome, then menu → Add to Home screen")
    print()

    uvicorn.run(create_app(dungeon_mode=not args.linear), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
