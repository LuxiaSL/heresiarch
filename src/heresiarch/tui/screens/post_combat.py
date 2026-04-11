"""Post-combat screen — XP summary, loot selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.models.party import STASH_LIMIT
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult


class PostCombatScreen(Screen):
    """Victory! Show XP gains, level-ups, and loot selection."""

    CSS = """
    PostCombatScreen {
        align: center middle;
    }
    #post-combat-container {
        width: 90%;
        max-width: 100;
        height: auto;
        padding: 2 4;
    }
    #loot-options {
        height: auto;
        max-height: 8;
        margin: 1 0;
    }
    """

    BINDINGS = [
        ("enter", "continue_action", "Continue"),
    ]

    def __init__(self, combat_result: CombatResult, loot: LootResult) -> None:
        super().__init__()
        self._result = combat_result
        self._loot = loot
        self._selected_items: set[str] = set()
        self._loot_keys: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="post-combat-container"):
            yield Static("[bold #44aa44]--- VICTORY ---[/bold #44aa44]", id="victory-header")
            yield Label(f"Rounds: {self._result.rounds_taken}", id="rounds-info")
            yield Label("")
            yield Static("", id="xp-summary")
            yield Label("")
            yield Static("", id="loot-summary")
            yield OptionList(id="loot-options")
            yield Label("")
            yield Button("Continue", variant="primary", id="btn-continue")

    def on_mount(self) -> None:
        self._render_xp_summary()
        self._render_loot()
        # Focus loot list if items available, otherwise continue button
        loot_list = self.query_one("#loot-options", OptionList)
        if self._loot_keys:
            loot_list.focus()
        else:
            loot_list.display = False
            self.query_one("#btn-continue", Button).focus()

    def _render_xp_summary(self) -> None:
        """Show XP gains and level-ups for surviving characters."""
        run = self.app.run_state
        if run is None:
            return

        lines: list[str] = []
        for char_id in self._result.surviving_character_ids:
            char = run.party.characters.get(char_id)
            if char is None:
                continue
            job = self.app.game_data.jobs.get(char.job_id)
            job_name = job.name if job else "?"
            lines.append(f"  {char.name} (Lv{char.level} {job_name}) — XP: {char.xp}")

        self.query_one("#xp-summary", Static).update(
            "[bold]XP & Levels[/bold]\n" + "\n".join(lines) if lines else "[dim]No survivors[/dim]"
        )

    def _render_loot(self) -> None:
        """Show money and item drops with interactive loot selection."""
        loot = self._loot
        run = self.app.run_state
        if run is None:
            return

        stash_space = STASH_LIMIT - len(run.party.stash)
        lines: list[str] = [
            f"  Money: [bold #e6c566]+{loot.money}G[/bold #e6c566]",
        ]
        if loot.item_ids:
            lines.append(f"  Items: {len(loot.item_ids)} found (stash space: {stash_space})")

        self.query_one("#loot-summary", Static).update(
            "[bold]Loot[/bold]\n" + "\n".join(lines)
        )

        # Populate interactive loot selection
        loot_list = self.query_one("#loot-options", OptionList)
        loot_list.clear_options()
        self._loot_keys = []

        for item_id in loot.item_ids:
            item = self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            # Auto-select if stash has room
            if stash_space > 0:
                self._selected_items.add(item_id)
                stash_space -= 1
                marker = "[bold #44aa44]+[/bold #44aa44]"
            else:
                marker = "[dim]-[/dim]"
            loot_list.add_option(Option(f"{marker} {name}{desc}"))
            self._loot_keys.append(item_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Toggle item selection on Enter."""
        if event.option_list.id != "loot-options":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._loot_keys):
            return

        item_id = self._loot_keys[idx]
        run = self.app.run_state
        if run is None:
            return

        stash_space = STASH_LIMIT - len(run.party.stash)
        currently_selected = len(self._selected_items)

        if item_id in self._selected_items:
            self._selected_items.discard(item_id)
        elif currently_selected < stash_space:
            self._selected_items.add(item_id)
        # Refresh the display markers
        self._refresh_loot_markers()

    def _refresh_loot_markers(self) -> None:
        """Update the +/- markers in the loot list."""
        loot_list = self.query_one("#loot-options", OptionList)
        loot_list.clear_options()
        for item_id in self._loot_keys:
            item = self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            if item_id in self._selected_items:
                marker = "[bold #44aa44]+[/bold #44aa44]"
            else:
                marker = "[dim]-[/dim]"
            loot_list.add_option(Option(f"{marker} {name}{desc}"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            self._continue()

    def action_continue_action(self) -> None:
        self._continue()

    def _continue(self) -> None:
        """Apply loot, advance zone, check recruitment/victory, autosave."""
        run = self.app.run_state
        if run is None:
            return

        # Apply selected loot items
        run = self.app.game_loop.apply_loot(run, self._loot, list(self._selected_items))

        # Advance zone
        run = self.app.game_loop.advance_zone(run)
        self.app.run_state = run

        if run.zone_state and run.zone_state.is_cleared:
            # Zone just cleared — check for win condition
            zone = self.app.game_data.zones.get(run.current_zone_id or "")
            if zone and zone.is_final:
                # Autosave the victory state
                try:
                    self.app.save_manager.autosave(run)
                except Exception:
                    pass

                from heresiarch.tui.screens.victory import VictoryScreen

                self.app.switch_screen(VictoryScreen())
                return

            # Non-final zone cleared — stay on zone screen, player can
            # keep fighting (overstay) or leave to zone selection
        else:
            # Mid-zone: check for recruitment encounter (once per zone)
            run, candidate = self.app.game_loop.try_recruitment(run)
            self.app.run_state = run
            if candidate is not None:
                from heresiarch.tui.screens.recruitment import RecruitmentScreen

                try:
                    self.app.save_manager.autosave(run)
                except Exception:
                    pass
                self.app.switch_screen(RecruitmentScreen(candidate))
                return

        # Autosave after all state transitions are complete
        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())
