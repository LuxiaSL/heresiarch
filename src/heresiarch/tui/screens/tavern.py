"""Tavern screen — NPC hints and interaction (stub)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static


class TavernScreen(Screen):
    """Tavern stub — future home of NPCs, hints, and interaction."""

    CSS = """
    TavernScreen {
        align: center middle;
    }
    #tavern-box {
        width: 50;
        height: auto;
        padding: 2 3;
        border: tall #333355;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="tavern-box"):
            yield Static(
                "[bold #e6c566]Tavern[/bold #e6c566]\n\n"
                "  The tavern is quiet.\n"
                "  A few lanterns flicker in the dim light.\n"
                "  No one seems to be around.\n\n"
                "  [dim]NPCs and hints coming in a future update.[/dim]\n\n"
                "  [dim][Esc] back[/dim]"
            )
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()
