"""Recruitment screen — CHA-gated inspection, recruit or pass."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.recruitment import InspectionLevel, RecruitCandidate


class RecruitmentScreen(Screen):
    """Inspect a recruit candidate with CHA-gated information reveal."""

    CSS = """
    RecruitmentScreen {
        align: center middle;
    }
    #recruit-container {
        width: auto;
        max-width: 72;
        height: auto;
        padding: 1 2;
    }
    #recruit-actions {
        height: auto;
        max-height: 4;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
    ]

    def __init__(self, candidate: RecruitCandidate) -> None:
        super().__init__()
        self._candidate = candidate
        self._action_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="recruit-container"):
            yield Static("[bold]Recruitment Encounter[/bold]", id="recruit-header")
            yield Label("")
            yield Static("", id="candidate-info")
            yield Label("")
            yield Static("", id="inspection-note")
            yield OptionList(id="recruit-actions")
        yield Footer()

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
        lines.append(f"[bold]{char.name}[/bold] -- {job_name}")
        lines.append(f"  Level: {char.level}")

        if inspection in (InspectionLevel.MODERATE, InspectionLevel.FULL):
            growth = info.get("growth")
            if growth:
                lines.append("")
                lines.append("[bold]Growth Rates[/bold]")
                lines.append(
                    f"  STR +{growth.STR}  MAG +{growth.MAG}  "
                    f"DEF +{growth.DEF}  RES +{growth.RES}  SPD +{growth.SPD}"
                )

        if inspection == InspectionLevel.FULL:
            stats = info.get("stats")
            if stats:
                lines.append("")
                lines.append("[bold]Current Stats[/bold]")
                lines.append(
                    f"  STR {stats.STR:>3}  MAG {stats.MAG:>3}  "
                    f"DEF {stats.DEF:>3}  RES {stats.RES:>3}  SPD {stats.SPD:>3}"
                )
            hp = info.get("hp")
            if hp is not None:
                lines.append(f"  HP: {hp}")

        # Equipment (always visible — you can see what they're carrying)
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
                note_lines.append("[dim]Low CHA -- limited information available[/dim]")
                note_lines.append(f"[dim]CHA: {cha} (need 30 for growth rates, 70 for full stats)[/dim]")
            case InspectionLevel.MODERATE:
                note_lines.append("[dim]Moderate CHA -- growth rates visible[/dim]")
                note_lines.append(f"[dim]CHA: {cha} (need 70 for full stats)[/dim]")
            case InspectionLevel.FULL:
                note_lines.append("[#44aa44]Full inspection -- all information visible[/#44aa44]")

        self.query_one("#inspection-note", Static).update("\n".join(note_lines))

        # Action list
        action_list = self.query_one("#recruit-actions", OptionList)
        action_list.clear_options()
        self._action_keys = []

        total = len(run.party.active) + len(run.party.reserve)
        if total < 4:
            action_list.add_option(Option("Recruit"))
            self._action_keys.append("recruit")
        else:
            action_list.add_option(Option("[dim]Party Full[/dim]"))
            self._action_keys.append("")

        action_list.add_option(Option("Pass"))
        self._action_keys.append("pass")

        action_list.focus()
        action_list.highlighted = 0

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "recruit-actions":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._action_keys):
            return

        action = self._action_keys[idx]
        match action:
            case "recruit":
                self._recruit()
            case "pass":
                self._pass()

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

        self._go_to_zone()

    def _pass(self) -> None:
        self._go_to_zone()

    def _go_to_zone(self) -> None:
        """Return to zone screen after recruit/pass decision."""
        run = self.app.run_state
        if run is not None:
            # Track last offered job for rolling-window prevention
            run = run.model_copy(
                update={"last_recruit_job_id": self._candidate.character.job_id}
            )
            self.app.run_state = run
            try:
                self.app.save_manager.autosave(run)
            except Exception:
                pass

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())

    def action_go_back(self) -> None:
        self._pass()
