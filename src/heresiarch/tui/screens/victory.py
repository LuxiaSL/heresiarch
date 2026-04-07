"""Victory screen — YOU WIN after clearing the final zone."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static


YOU_WIN = r"""
 ██    ██  ██████  ██    ██     ██     ██ ██ ███    ██
  ██  ██  ██    ██ ██    ██     ██     ██ ██ ████   ██
   ████   ██    ██ ██    ██     ██  █  ██ ██ ██ ██  ██
    ██    ██    ██ ██    ██     ██ ███ ██ ██ ██  ██ ██
    ██     ██████   ██████       ███ ███  ██ ██   ████
"""


class VictoryScreen(Screen):
    """The run is won. The math broke in your favor."""

    CSS = """
    VictoryScreen {
        align: center middle;
    }
    #victory-container {
        width: auto;
        max-width: 72;
        height: auto;
        padding: 1 2;
    }
    #you-win {
        text-align: center;
    }
    """

    BINDINGS = [
        ("enter", "return_to_title", "Return"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="victory-container"):
            yield Static(
                f"[bold #e6c566]{YOU_WIN}[/bold #e6c566]",
                id="you-win",
            )
            yield Label("")
            yield Static("", id="run-recap")
            yield Label("")
            yield Button(
                "Return to Title",
                variant="primary",
                id="btn-return",
            )

    def on_mount(self) -> None:
        self._render_recap()
        self.query_one("#btn-return", Button).focus()

    def _render_recap(self) -> None:
        run = self.app.run_state
        if run is None:
            self.query_one("#run-recap", Static).update("[dim]No data.[/dim]")
            return

        record = run.battle_record
        party = run.party

        lines: list[str] = []

        lines.append("[bold #e6c566]The heretic prevails.[/bold #e6c566]")
        lines.append("")

        # Final party
        lines.append("[bold]Final Party[/bold]")
        for char_id in party.active + party.reserve:
            char = party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                lines.append(f"  {char.name} -- Lv{char.level} {job_name}")
        lines.append("")

        # Battle stats
        lines.append("[bold]Battle Record[/bold]")
        lines.append(f"  Encounters: {record.total_encounters} ({record.victories}W / {record.defeats}L)")
        lines.append(f"  Total rounds: {record.total_rounds}")
        lines.append(f"  Damage dealt: {record.total_damage_dealt}")
        lines.append(f"  Damage taken: {record.total_damage_taken}")
        lines.append(f"  Zones cleared: {len(run.zones_completed)}")
        lines.append(f"  Money: {party.money}G")

        self.query_one("#run-recap", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-return":
            self.action_return_to_title()

    def action_return_to_title(self) -> None:
        self.app.run_state = None
        self.app.combat_state = None

        from heresiarch.tui.screens.title import TitleScreen

        self.app.switch_screen(TitleScreen())
