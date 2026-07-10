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
        ("M", "toggle_music", "Music"),
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

        # Analytics record DB: every autosaved run lands here.
        # Failures are swallowed internally — never blocks the game.
        from heresiarch.analytics.record_db import RecordDB
        record_db: RecordDB | None = None
        try:
            record_db = RecordDB(Path("artifacts/run_records.db"))
        except Exception:
            record_db = None

        self.save_manager = SaveManager(
            save_dir=save_path or Path("saves"),
            record_db=record_db,
        )

        # Game state — set when a run starts or loads
        self.run_state: RunState | None = None

        # Combat state — transient, only set during combat
        self.combat_state: CombatState | None = None
        self.current_enemies: list[EnemyInstance] | None = None

        # Training-data tap: human play becomes labeled feature rows
        # (artifacts/tapdata_play/), same contract as sim shards.
        # Failure-proof; disable with HERESIARCH_NO_PLAY_TAP=1.
        self.data_tap = None

        # Background music — failure-proof, toggled with M.
        from heresiarch.tui.music import MusicPlayer
        self.music = MusicPlayer()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Push the title screen on startup."""
        from heresiarch.tui.screens.title import TitleScreen

        if self.music.autostart_enabled():
            self.music.start()
        self.push_screen(TitleScreen())

    def on_unmount(self) -> None:
        self.music.stop()

    def action_toggle_music(self) -> None:
        if not self.music.available:
            self.notify(
                "No audio backend found (need ffplay, paplay, or aplay)",
                severity="warning",
            )
            return
        playing = self.music.toggle()
        self.notify("♪ music on" if playing else "music muted", timeout=2)

    def action_quit(self) -> None:
        """Show confirmation modal instead of quitting immediately."""
        self.push_screen(QuitConfirmModal())

    def start_play_tap(self, run: RunState) -> None:
        """Open a training-data tap for this run's play session.

        Called on new run and on load. Shards append across sessions
        (stable filename per run_id); the seed field is derived from
        the run_id so train/test splits stay leak-free.
        """
        self.data_tap = None
        import os
        if os.environ.get("HERESIARCH_NO_PLAY_TAP"):
            return
        try:
            import zlib
            from heresiarch.tools.data_tap import DataTap

            self.data_tap = DataTap(
                Path("artifacts/tapdata_play")
                / f"tap_{run.mc_job_id}_human_{run.run_id}.jsonl.gz",
                mc_job_id=run.mc_job_id,
                seed=zlib.crc32(run.run_id.encode()) % 100_000_000,
                game_data=self.game_data,
                policy_name="human",
            )
        except Exception:
            self.data_tap = None

    def end_play_tap(self, won_region: bool) -> None:
        """Close out a finished run: label + flush the tap, and give
        the analytics DB its final outcome. Death and victory skip
        autosave (death even deletes saves), so without this the
        records DB keeps the last mid-run snapshot marked
        'in_progress' forever."""
        run = self.run_state
        if run is not None and self.save_manager.record_db is not None:
            try:
                from heresiarch.analytics.record_db import RunRecordMetadata

                outcome = "won" if won_region else (
                    "dead" if run.is_dead else "clean_exit"
                )
                self.save_manager.record_db.record_run(
                    run, RunRecordMetadata(source="tui"), outcome=outcome,
                )
            except Exception:
                pass

        tap, self.data_tap = self.data_tap, None
        if tap is None or run is None:
            return
        try:
            tap.on_run_end(run, won_region)
            tap.flush()
        except Exception:
            pass

    def persist_run(self) -> None:
        """Autosave the current run, swallowing failures.

        Called after every macro decision so a crash/quit never loses
        progress. A no-op if there is no active run.
        """
        if self.run_state is None:
            return
        try:
            self.save_manager.autosave(self.run_state)
        except Exception:
            pass

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
