"""Title screen — the first thing the player sees."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option

# ---------------------------------------------------------------------------
# Visual assets
# ---------------------------------------------------------------------------

# Raw title art — gradient coloring applied per-frame by the breather.
_TITLE_RAW: list[str] = [
    r"    __  __                    _                 __   ",
    r"   / / / /__  ________  _____(_)___ ___________/ /_  ",
    "  / /_/ / _ \\/ ___/ _ \\/ ___/ / __ `/ ___/ ___/ __ \\ ",
    r" / __  /  __/ /  /  __(__  ) / /_/ / /  / /__/ / / / ",
    r"/_/ /_/\___/_/   \___/____/_/\__,_/_/   \___/_/ /_/  ",
]

# Breathing palettes — cycle for a slow glow pulse.
# Each list: one color per title line, top to bottom.
_PALETTES: list[list[str]] = [
    ["#5c4480", "#6f5494", "#8266a8", "#9578bc", "#c8a2c8"],  # cool
    ["#6a4f8e", "#7e63a3", "#9277b7", "#a78bcb", "#d0aed0"],  # warming
    ["#785aa0", "#8c6eb4", "#a084c8", "#b49adc", "#d8b8a4"],  # peak
    ["#6a4f8e", "#7e63a3", "#9277b7", "#a78bcb", "#d0aed0"],  # cooling
]

# Divider accent color per phase
_DIV_COLORS: list[str] = ["#3a3a56", "#44446a", "#4e4e7e", "#44446a"]

# Noise mote color per phase — very faint
_NOISE_COLORS: list[str] = ["#181828", "#1c1c2e", "#202034", "#1c1c2e"]

# Sparse noise patterns — dots drift between frames
_NOISE_TOP: list[str] = [
    "      \u00b7           \u00b7                \u00b7           \u00b7     ",
    "           \u00b7                \u00b7           \u00b7            \u00b7",
    "  \u00b7                \u00b7           \u00b7                \u00b7     ",
    "         \u00b7           \u00b7                \u00b7           \u00b7   ",
]
_NOISE_BOT: list[str] = [
    "         \u00b7           \u00b7                \u00b7           \u00b7   ",
    "  \u00b7                \u00b7           \u00b7                \u00b7     ",
    "           \u00b7                \u00b7           \u00b7            \u00b7",
    "      \u00b7           \u00b7                \u00b7           \u00b7     ",
]

# Ornamental divider
_DIVIDER = "\u2500\u2500\u2500\u2500 \u00b7 \u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u25c6 \u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u00b7 \u2500\u2500\u2500\u2500"


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _render_title(palette: list[str]) -> Text:
    """Apply a per-line color gradient to the title art."""
    text = Text()
    for i, raw in enumerate(_TITLE_RAW):
        if i > 0:
            text.append("\n")
        text.append(raw, style=f"bold {palette[i]}")
    return text


def _render_divider(color: str) -> Text:
    return Text(_DIVIDER, style=color)


def _render_noise(pattern: str, color: str) -> Text:
    return Text(pattern, style=color)


def _option_label(key: str, label: str) -> Text:
    """Build a menu option with a dimmed hotkey hint."""
    t = Text()
    t.append(key, style="dim #6b6b6b")
    t.append(f"  {label}", style="#c8a2c8")
    return t


def _build_worlds() -> Text:
    t = Text()
    t.append("Nordic", style="#7b8eaa")
    t.append("  \u00b7  ")
    t.append("Shinto", style="#aa7070")
    t.append("  \u00b7  ")
    t.append("Abrahamic", style="#a89868")
    return t


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------


class TitleScreen(Screen):
    """HERESIARCH -- New Run / Continue / Quit."""

    CSS = """
    TitleScreen {
        align: center middle;
    }
    #title-frame {
        width: auto;
        max-width: 76;
        height: auto;
        border: round #2a2244;
        padding: 1 4;
        background: #0c0c10;
    }
    #noise-top, #noise-bot {
        text-align: center;
        height: 1;
    }
    #title-art {
        text-align: center;
    }
    #title-divider {
        text-align: center;
        margin: 1 0;
    }
    #title-worlds {
        text-align: center;
    }
    #tagline {
        text-align: center;
        color: #4a4a5a;
        margin: 1 0;
    }
    #title-actions {
        height: auto;
        max-height: 6;
        margin: 1 12 0 12;
        border: tall #2a2244;
        background: #0c0c10;
    }
    #title-actions:focus {
        border: tall #333355;
    }
    #title-actions > .option-list--option-highlighted {
        background: #2a1a3e;
        color: #e6c566;
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
        self._phase: int = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="title-frame"):
            yield Static(
                _render_noise(_NOISE_TOP[0], _NOISE_COLORS[0]),
                id="noise-top",
            )
            yield Static(_render_title(_PALETTES[0]), id="title-art")
            yield Static(
                _render_divider(_DIV_COLORS[0]), id="title-divider"
            )
            yield Static(_build_worlds(), id="title-worlds")
            yield Static(
                "Pick a world. Pick a job. Descend.\n"
                "Build synergy. Kill god.",
                id="tagline",
            )
            yield OptionList(id="title-actions")
            yield Static(
                _render_noise(_NOISE_BOT[0], _NOISE_COLORS[0]),
                id="noise-bot",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._populate_actions()
        self.set_interval(0.9, self._breathe)

    def _breathe(self) -> None:
        """Cycle title glow + ambient noise for a slow breathing effect."""
        self._phase = (self._phase + 1) % len(_PALETTES)
        p = self._phase
        self.query_one("#title-art", Static).update(
            _render_title(_PALETTES[p])
        )
        self.query_one("#title-divider", Static).update(
            _render_divider(_DIV_COLORS[p])
        )
        self.query_one("#noise-top", Static).update(
            _render_noise(_NOISE_TOP[p], _NOISE_COLORS[p])
        )
        self.query_one("#noise-bot", Static).update(
            _render_noise(_NOISE_BOT[p], _NOISE_COLORS[p])
        )

    def _populate_actions(self) -> None:
        action_list = self.query_one("#title-actions", OptionList)
        action_list.clear_options()
        self._action_keys = []

        action_list.add_option(Option(_option_label("n", "New Run")))
        self._action_keys.append("new_run")

        has_saves = False
        try:
            runs = self.app.save_manager.list_runs()
            has_saves = len(runs) > 0
        except Exception:
            pass

        if has_saves:
            action_list.add_option(Option(_option_label("c", "Continue")))
            self._action_keys.append("continue_run")
            action_list.add_option(Option(_option_label("l", "Load Game")))
            self._action_keys.append("load_game")

        action_list.add_option(Option(_option_label("q", "Quit")))
        self._action_keys.append("quit_game")

        action_list.focus()
        action_list.highlighted = 0

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
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
        """Quick continue -- load most recent save from most recent run."""
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
        from heresiarch.tui.app import QuitConfirmModal

        self.app.push_screen(QuitConfirmModal())
