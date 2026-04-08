"""Death screen — YOU DIED + run recap from BattleRecord."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static


YOU_DIED = r"""
 ██    ██  ██████  ██    ██     ██████  ██ ███████ ██████
  ██  ██  ██    ██ ██    ██     ██   ██ ██ ██      ██   ██
   ████   ██    ██ ██    ██     ██   ██ ██ █████   ██   ██
    ██    ██    ██ ██    ██     ██   ██ ██ ██      ██   ██
    ██     ██████   ██████      ██████  ██ ███████ ██████
"""


class DeathScreen(Screen):
    """The run is over. Dark Souls energy."""

    CSS = """
    DeathScreen {
        align: center middle;
    }
    #death-container {
        width: 65%;
        height: auto;
        padding: 1 4;
    }
    #you-died {
        text-align: center;
    }
    """

    BINDINGS = [
        ("enter", "return_to_title", "Return"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="death-container"):
            yield Static(
                f"[bold #880000]{YOU_DIED}[/bold #880000]",
                id="you-died",
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
        self._delete_saves()
        self.query_one("#btn-return", Button).focus()

    def _render_recap(self) -> None:
        """Generate run recap from BattleRecord."""
        run = self.app.run_state
        if run is None:
            self.query_one("#run-recap", Static).update("[dim]No data.[/dim]")
            return

        record = run.battle_record
        party = run.party

        lines: list[str] = []

        # Party at death
        lines.append("[bold]Final Party[/bold]")
        for char_id in party.active + party.reserve:
            char = party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                lines.append(f"  {char.name} — Lv{char.level} {job_name}")
        lines.append("")

        # Battle stats
        lines.append("[bold]Battle Record[/bold]")
        lines.append(f"  Encounters: {record.total_encounters} ({record.victories}W / {record.defeats}L)")
        lines.append(f"  Total rounds: {record.total_rounds}")
        lines.append(f"  Damage dealt: {record.total_damage_dealt}")
        lines.append(f"  Damage taken: {record.total_damage_taken}")
        lines.append(f"  Healing: {record.total_healing}")

        # Zones
        if run.zones_completed:
            lines.append(f"  Zones cleared: {len(run.zones_completed)}")

        farthest = record.farthest_zone
        if farthest:
            zone = self.app.game_data.zones.get(farthest)
            zone_name = zone.name if zone else farthest
            lines.append(f"  Farthest zone: {zone_name}")

        lines.append(f"  Money: {party.money}G")
        lines.append("")

        # Top damage dealers (player characters only)
        damage_by_char = record.damage_dealt_by_character()
        if damage_by_char:
            player_dmg = {
                cid: dmg for cid, dmg in damage_by_char.items()
                if cid in party.characters
            }
            if player_dmg:
                lines.append("[bold]Top Damage[/bold]")
                sorted_dmg = sorted(player_dmg.items(), key=lambda x: x[1], reverse=True)[:3]
                for char_id, dmg in sorted_dmg:
                    char = party.characters[char_id]
                    lines.append(f"  {char.name}: {dmg}")
            lines.append("")

        # Most used abilities
        ability_counts = record.most_used_abilities()
        if ability_counts:
            lines.append("[bold]Most Used Abilities[/bold]")
            sorted_abilities = sorted(ability_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for aid, count in sorted_abilities:
                ability = self.app.game_data.abilities.get(aid)
                name = ability.name if ability else aid
                lines.append(f"  {name}: {count}x")

        self.query_one("#run-recap", Static).update("\n".join(lines))

    def _delete_saves(self) -> None:
        """Permadeath: nuke all saves for this run."""
        run = self.app.run_state
        if run is None:
            return
        try:
            self.app.save_manager.delete_run_saves(run.run_id)
        except Exception:
            pass  # Save dir might not exist yet

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-return":
            self.action_return_to_title()

    def action_return_to_title(self) -> None:
        self.app.run_state = None
        self.app.combat_state = None

        from heresiarch.tui.screens.title import TitleScreen

        self.app.switch_screen(TitleScreen())
