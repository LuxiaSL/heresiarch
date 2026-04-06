"""Job select screen — pick a starting job and name your MC."""

from __future__ import annotations

import uuid

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, OptionList, Static
from textual.widgets.option_list import Option


class JobSelectScreen(Screen):
    """Pick a starting job and name your MC."""

    CSS = """
    JobSelectScreen {
        align: center middle;
    }
    #job-select-box {
        width: 80;
        height: auto;
        padding: 1 2;
    }
    #job-list {
        height: auto;
        max-height: 16;
        margin-bottom: 1;
    }
    #job-detail {
        height: auto;
        min-height: 6;
        margin-bottom: 1;
        padding: 0 1;
        border: tall #333355;
    }
    #mc-name-input {
        margin-bottom: 1;
    }
    .job-btn-row {
        height: 3;
        align: center middle;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._selected_job_id: str | None = None
        self._job_ids: list[str] = []

    def compose(self) -> ComposeResult:
        jobs = self.app.game_data.jobs

        # Build option list entries
        options: list[Option] = []
        self._job_ids = []
        for job_id in sorted(jobs.keys()):
            job = jobs[job_id]
            growth = job.growth
            label = (
                f"{job.name} ({job.origin}) — "
                f"STR+{growth.STR} MAG+{growth.MAG} DEF+{growth.DEF} "
                f"RES+{growth.RES} SPD+{growth.SPD}"
            )
            options.append(Option(label, id=job_id))
            self._job_ids.append(job_id)

        with Vertical(id="job-select-box"):
            yield Static("[bold]Choose Your Job[/bold]")
            yield Label("")
            yield OptionList(*options, id="job-list")
            yield Static("", id="job-detail")
            yield Label("Name your character:")
            yield Input(placeholder="Heresiarch", id="mc-name-input", max_length=20)
            with Horizontal(classes="job-btn-row"):
                yield Button("Back", id="btn-back")
                yield Button("Begin Run", variant="primary", id="btn-begin", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#job-list", OptionList).focus()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Show job detail when highlighted (arrow keys)."""
        if event.option.id:
            self._show_job_detail(event.option.id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Select job on Enter."""
        if event.option.id:
            self._selected_job_id = event.option.id
            self._show_job_detail(event.option.id)
            self.query_one("#btn-begin", Button).disabled = False
            # Move focus to name input
            self.query_one("#mc-name-input", Input).focus()

    def _show_job_detail(self, job_id: str) -> None:
        """Render detailed job info in the detail panel."""
        job = self.app.game_data.jobs.get(job_id)
        if job is None:
            return

        growth = job.growth
        ability = self.app.game_data.abilities.get(job.innate_ability_id)
        innate_name = ability.name if ability else job.innate_ability_id
        innate_desc = ability.description if ability else ""

        lines = [
            f"[bold #e6c566]{job.name}[/bold #e6c566] — {job.origin}",
            f"  {job.description}",
            "",
            f"  Growth: STR [bold]+{growth.STR}[/bold]  MAG [bold]+{growth.MAG}[/bold]  "
            f"DEF [bold]+{growth.DEF}[/bold]  RES [bold]+{growth.RES}[/bold]  SPD [bold]+{growth.SPD}[/bold]",
            f"  HP: {job.base_hp} base + {job.hp_growth}/level",
            f"  Innate: [bold]{innate_name}[/bold]"
            + (f" — {innate_desc}" if innate_desc else ""),
        ]

        self.query_one("#job-detail", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-begin":
                self._begin_run()
            case "btn-back":
                self.action_go_back()

    def _begin_run(self) -> None:
        if self._selected_job_id is None:
            return

        name_input = self.query_one("#mc-name-input", Input)
        mc_name = name_input.value.strip() or "Heresiarch"

        run_id = f"run_{uuid.uuid4().hex[:8]}"
        app = self.app
        app.run_state = app.game_loop.new_run(run_id, mc_name, self._selected_job_id)

        # Enter the first zone
        zones = list(app.game_data.zones.keys())
        if zones:
            app.run_state = app.game_loop.enter_zone(app.run_state, zones[0])

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())

    def action_go_back(self) -> None:
        self.app.pop_screen()
