"""Entry point: python -m heresiarch.dashboard"""

from __future__ import annotations


def main() -> None:
    import uvicorn

    uvicorn.run(
        "heresiarch.dashboard.app:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
    )


if __name__ == "__main__":
    main()
