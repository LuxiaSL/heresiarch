"""Recruitment screen — CHA-gated inspection, recruit or pass."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from heresiarch.engine.recruitment import InspectionLevel, RecruitCandidate


class RecruitmentScreen(Screen):
    """Inspect a recruit candidate with CHA-gated information reveal."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, candidate: RecruitCandidate) -> None:
        super().__init__()
        self._candidate = candidate

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="recruit-container"):
                    yield Static("[bold]Recruitment Encounter[/bold]", id="recruit-header")
                    yield Label("")
                    yield Static("", id="candidate-info")
                    yield Label("")
                    yield Static("", id="inspection-note")
                    yield Label("")
                    yield Button("Recruit", variant="primary", id="btn-recruit")
                    yield Button("Pass", id="btn-pass")

    def on_mount(self) -> None:
        self._render_candidate()

    def _render_candidate(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        candidate = self._candidate
        char = candidate.character
        cha = run.party.cha
        inspection = self.app.game_loop.recruitment_engine.get_inspection_level(cha)
        info = self.app.game_loop.recruitment_engine.inspect_candidate(candidate, cha)

        lines: list[str] = []

        # Always visible: name and job
        job = self.app.game_data.jobs.get(char.job_id)
        job_name = job.name if job else char.job_id
        lines.append(f"[bold]{char.name}[/bold] — {job_name}")
        lines.append(f"  Level: {char.level}")

        if inspection in (InspectionLevel.MODERATE, InspectionLevel.FULL):
            # Show growth rates
            growth = info.get("growth")
            if growth:
                lines.append("")
                lines.append("[bold]Growth Rates[/bold]")
                lines.append(
                    f"  STR +{growth.STR}  MAG +{growth.MAG}  "
                    f"DEF +{growth.DEF}  RES +{growth.RES}  SPD +{growth.SPD}"
                )

        if inspection == InspectionLevel.FULL:
            # Show full stats
            stats = info.get("stats")
            if stats:
                lines.append("")
                lines.append("[bold]Current Stats[/bold]")
                lines.append(
                    f"  STR {stats.STR:>3}  MAG {stats.MAG:>3}  "
                    f"DEF {stats.DEF:>3}  RES {stats.RES:>3}  SPD {stats.SPD:>3}"
                )
            hp = info.get("hp")
            if hp:
                lines.append(f"  HP: {hp}")

            # Equipment
            equipment = char.equipment
            has_equip = any(v for v in equipment.values())
            if has_equip:
                lines.append("")
                lines.append("[bold]Equipment[/bold]")
                for slot, item_id in equipment.items():
                    if item_id:
                        item = self.app.game_data.items.get(item_id)
                        name = item.name if item else item_id
                        lines.append(f"  {slot}: {name}")

        self.query_one("#candidate-info", Static).update("\n".join(lines))

        # Inspection note
        note_lines: list[str] = []
        match inspection:
            case InspectionLevel.MINIMAL:
                note_lines.append("[dim]Low CHA — limited information available[/dim]")
                note_lines.append(f"[dim]CHA: {cha} (need 30 for growth rates, 70 for full stats)[/dim]")
            case InspectionLevel.MODERATE:
                note_lines.append("[dim]Moderate CHA — growth rates visible[/dim]")
                note_lines.append(f"[dim]CHA: {cha} (need 70 for full stats)[/dim]")
            case InspectionLevel.FULL:
                note_lines.append("[#44aa44]Full inspection — all information visible[/#44aa44]")

        self.query_one("#inspection-note", Static).update("\n".join(note_lines))

        # Check if party is full (max 4: 3 active + 1 reserve)
        total = len(run.party.active) + len(run.party.reserve)
        recruit_btn = self.query_one("#btn-recruit", Button)
        if total >= 4:
            recruit_btn.label = "Party Full"
            recruit_btn.disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-recruit":
                self._recruit()
            case "btn-pass":
                self.app.pop_screen()

    def _recruit(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        try:
            new_party = self.app.game_loop.recruitment_engine.recruit(
                run.party, self._candidate
            )
            self.app.run_state = run.model_copy(update={"party": new_party})
        except ValueError:
            pass

        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
