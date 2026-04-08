"""Title screen — the first thing the player sees."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option


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
    #title-actions {
        height: auto;
        max-height: 6;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("n", "new_run", "New Run"),
        ("c", "continue_run", "Continue"),
        ("l", "load_game", "Load Game"),
        ("q", "quit_game", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._action_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="title-box"):
            yield Static(TITLE_ART, id="title-art")
            yield Static(
                "[dim]Pick a world, pick a job, descend, build synergy, kill god.[/dim]",
                id="tagline",
            )
            yield OptionList(id="title-actions")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_actions()

    def _populate_actions(self) -> None:
        action_list = self.query_one("#title-actions", OptionList)
        action_list.clear_options()
        self._action_keys = []

        action_list.add_option(Option("[n] New Run"))
        self._action_keys.append("new_run")

        has_saves = False
        try:
            runs = self.app.save_manager.list_runs()
            has_saves = len(runs) > 0
        except Exception:
            pass

        if has_saves:
            action_list.add_option(Option("[c] Continue"))
            self._action_keys.append("continue_run")
            action_list.add_option(Option("[l] Load Game"))
            self._action_keys.append("load_game")

        action_list.add_option(Option("[q] Quit"))
        self._action_keys.append("quit_game")

        action_list.focus()
        action_list.highlighted = 0

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "title-actions":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._action_keys):
            return

        action = self._action_keys[idx]
        match action:
            case "new_run":
                self.action_new_run()
            case "continue_run":
                self.action_continue_run()
            case "load_game":
                self.action_load_game()
            case "quit_game":
                self.action_quit_game()

    def action_new_run(self) -> None:
        from heresiarch.tui.screens.job_select import JobSelectScreen

        self.app.push_screen(JobSelectScreen())

    def action_continue_run(self) -> None:
        """Quick continue — load most recent save from most recent run."""
        try:
            runs = self.app.save_manager.list_runs()
            if not runs:
                return
            run_id = runs[-1]
            slots = self.app.save_manager.list_slots(run_id)
            if not slots:
                return
            latest = max(slots, key=lambda s: s.saved_at or "")
            run_state = self.app.save_manager.load_run(run_id, latest.slot_id)
            self.app.run_state = self.app.game_loop.rehydrate_run(run_state)

            if self.app.run_state.current_zone_id is not None:
                from heresiarch.tui.screens.zone import ZoneScreen
                self.app.push_screen(ZoneScreen())
            else:
                from heresiarch.tui.screens.zone_select import ZoneSelectScreen
                self.app.push_screen(ZoneSelectScreen())
        except Exception:
            pass

    def action_load_game(self) -> None:
        """Open the save browser to pick a specific run/slot."""
        from heresiarch.tui.screens.load import LoadScreen

        self.app.push_screen(LoadScreen())

    def action_quit_game(self) -> None:
        self.app.exit()
