"""Lodge screen — rest at the lodge for a full party heal."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, OptionList, Static
from textual.widgets.option_list import Option


class LodgeScreen(Screen):
    """Confirm and execute lodge rest: full heal, gold cost, zone reset."""

    CSS = """
    LodgeScreen {
        align: center middle;
    }
    #lodge-box {
        width: 60;
        height: auto;
        padding: 1 2;
        border: tall #333355;
    }
    #lodge-actions {
        height: auto;
        max-height: 6;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rested = False

    def compose(self) -> ComposeResult:
        with Vertical(id="lodge-box"):
            yield Static("", id="lodge-header")
            yield Static("", id="lodge-detail")
            yield Label("", id="lodge-result")
            yield OptionList(id="lodge-actions")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_display()
        self.query_one("#lodge-actions", OptionList).focus()

    def _refresh_display(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        self.query_one("#lodge-header", Static).update(
            "[bold #c8a2c8]Lodge[/bold #c8a2c8]"
        )

        cost = self.app.game_loop.get_lodge_cost(run)
        gold = run.party.money
        can_afford = gold >= (cost or 0)

        # Party HP summary
        hp_lines: list[str] = []
        for char_id in run.party.active:
            char = run.party.characters.get(char_id)
            if char is None:
                continue
            max_hp = char.max_hp or 1
            hp_pct = char.current_hp / max(max_hp, 1)
            hp_color = (
                "#44aa44"
                if hp_pct > 0.5
                else "#cccc44" if hp_pct > 0.25 else "#cc4444"
            )
            hp_lines.append(
                f"  {char.name}: "
                f"[{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
            )

        # Zones that will be reset
        reset_zones: list[str] = []
        for zone_id, zstate in run.zone_progress.items():
            if not zstate.is_cleared:
                zone = self.app.game_data.zones.get(zone_id)
                name = zone.name if zone else zone_id
                reset_zones.append(name)

        detail_lines = [
            f"  Cost: [bold #e6c566]{cost}G[/bold #e6c566]  "
            f"|  Gold: {gold}G",
            "",
            "  [bold]Party HP:[/bold]",
            *hp_lines,
        ]

        if reset_zones:
            detail_lines.append("")
            detail_lines.append(
                f"  [bold #cc4444]Zone progress reset:[/bold #cc4444] "
                f"{', '.join(reset_zones)}"
            )

        self.query_one("#lodge-detail", Static).update("\n".join(detail_lines))

        # Actions
        actions = self.query_one("#lodge-actions", OptionList)
        actions.clear_options()

        if self._rested:
            actions.add_option(Option("[b] Back to town"))
        elif can_afford:
            actions.add_option(Option(f"[r] Rest ({cost}G)"))
            actions.add_option(Option("[b] Back"))
        else:
            actions.add_option(
                Option("[dim]Not enough gold[/dim]")
            )
            actions.add_option(Option("[b] Back"))

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option_list.id != "lodge-actions":
            return

        if self._rested:
            self.app.pop_screen()
            return

        if event.option_index == 0:
            self._do_rest()
        else:
            self.app.pop_screen()

    def _do_rest(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        cost = self.app.game_loop.get_lodge_cost(run) or 0
        gold_before = run.party.money

        try:
            run = self.app.game_loop.rest_at_lodge(run)
        except ValueError:
            return

        run = run.record_macro(
            "lodge_rest",
            {
                "cost": cost,
                "gold_before": gold_before,
                "gold_after": run.party.money,
            },
        )
        self.app.run_state = run
        self._rested = True

        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        self.query_one("#lodge-result", Label).update(
            "[bold #44aa44]The party rests well. All HP restored.[/bold #44aa44]"
        )
        self._refresh_display()

    def action_go_back(self) -> None:
        self.app.pop_screen()
