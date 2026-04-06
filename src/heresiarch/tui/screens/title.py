"""Title screen — the first thing the player sees."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static


TITLE_ART = """\
[bold #c8a2c8]
    __  __                     _                 __
   / / / /__  ________  _____(_)___ ___________/ /_
  / /_/ / _ \\/ ___/ _ \\/ ___/ / __ `/ ___/ ___/ __ \\
 / __  /  __/ /  /  __(__  ) / /_/ / /  / /__/ / / /
/_/ /_/\\___/_/   \\___/____/_/\\__,_/_/   \\___/_/ /_/
[/bold #c8a2c8]"""


class TitleScreen(Screen):
    """HERESIARCH — New Run / Continue / Quit."""

    CSS = """
    TitleScreen {
        align: center middle;
    }
    #title-box {
        width: auto;
        max-width: 72;
        height: auto;
        padding: 1 2;
    }
    #title-art {
        text-align: center;
        width: auto;
    }
    #tagline {
        text-align: center;
        color: #6b6b6b;
        margin: 1 0;
    }
    .title-btn {
        width: 100%;
    }
    """

    BINDINGS = [
        ("n", "new_run", "New Run"),
        ("c", "continue_run", "Continue"),
        ("q", "quit_game", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="title-box"):
            yield Static(TITLE_ART, id="title-art")
            yield Static(
                "[dim]Pick a world, pick a job, descend, build synergy, kill god.[/dim]",
                id="tagline",
            )
            yield Button("New Run", variant="primary", id="btn-new-run", classes="title-btn")
            yield Button("Continue", id="btn-continue", classes="title-btn")
            yield Button("Quit", id="btn-quit", classes="title-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#btn-new-run", Button).focus()

        try:
            runs = self.app.save_manager.list_runs()
            self.query_one("#btn-continue", Button).disabled = len(runs) == 0
        except Exception:
            self.query_one("#btn-continue", Button).disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-new-run":
                self.action_new_run()
            case "btn-continue":
                self.action_continue_run()
            case "btn-quit":
                self.action_quit_game()

    def action_new_run(self) -> None:
        from heresiarch.tui.screens.job_select import JobSelectScreen

        self.app.push_screen(JobSelectScreen())

    def action_continue_run(self) -> None:
        try:
            runs = self.app.save_manager.list_runs()
            if not runs:
                return
            run_id = runs[-1]
            run_state = self.app.save_manager.load_run(run_id, "autosave")
            self.app.run_state = run_state

            from heresiarch.tui.screens.zone import ZoneScreen

            self.app.push_screen(ZoneScreen())
        except Exception:
            pass

    def action_quit_game(self) -> None:
        self.app.exit()
