"""Heresiarch TUI application — the single owner of game state."""

from __future__ import annotations

import random
from pathlib import Path

from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static

from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.game_loop import GameLoop
from heresiarch.engine.models.combat_state import CombatState
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.run_state import RunState
from heresiarch.engine.save_manager import SaveManager


class QuitConfirmModal(ModalScreen):
    """Y/N modal to prevent accidental quits."""

    CSS = """
    QuitConfirmModal {
        align: center middle;
    }
    #quit-dialog {
        width: 34;
        height: 3;
        border: round #cc4444;
        background: $surface;
        padding: 0 2;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("[bold]Quit game?[/bold]  [dim](y/n)[/dim]", id="quit-dialog")

    def action_confirm(self) -> None:
        self.app.exit()

    def action_cancel(self) -> None:
        self.dismiss()


class HeresiarchApp(App):
    """Pick a world, pick a job, descend, build synergy, kill god."""

    TITLE = "HERESIARCH"
    CSS_PATH = "styles/theme.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "screenshot", "Screenshot"),
    ]

    def __init__(
        self,
        game_data: GameData | None = None,
        data_path: Path | None = None,
        save_path: Path | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__()
        self.game_data = game_data or load_all(data_path or Path("data"))
        self.rng = rng or random.Random()
        self.game_loop = GameLoop(game_data=self.game_data, rng=self.rng)
        self.save_manager = SaveManager(save_dir=save_path or Path("saves"))

        # Game state — set when a run starts or loads
        self.run_state: RunState | None = None

        # Combat state — transient, only set during combat
        self.combat_state: CombatState | None = None
        self.current_enemies: list[EnemyInstance] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Push the title screen on startup."""
        from heresiarch.tui.screens.title import TitleScreen

        self.push_screen(TitleScreen())

    def action_quit(self) -> None:
        """Show confirmation modal instead of quitting immediately."""
        self.push_screen(QuitConfirmModal())

    def action_screenshot(self) -> None:
        """Save an SVG screenshot to screenshots/ for debugging."""
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)

        # Find next available filename
        existing = list(screenshot_dir.glob("screen_*.svg"))
        idx = len(existing) + 1
        path = screenshot_dir / f"screen_{idx:03d}.svg"

        self.save_screenshot(str(path))
        self.notify(f"Screenshot saved: {path}")


def main() -> None:
    """Entry point for the heresiarch CLI command."""
    app = HeresiarchApp()
    app.run()


if __name__ == "__main__":
    main()
