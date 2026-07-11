"""Shared structured-view layer.

Frontend-agnostic view builders that translate engine state into
display-ready models. Both the TUI and the mobile web UI consume these
so presentation logic (anchor statuses, path coloring, combat event
rendering) lives in exactly one place.

No I/O, no framework imports — pure state transforms, like the engine.
"""
