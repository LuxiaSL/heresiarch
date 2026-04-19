"""Post-combat screen — XP summary, loot selection, stash management."""

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
    """Victory! Show XP gains, level-ups, and loot selection.

    When the stash is too full for all dropped items, a second list shows
    current stash contents so the player can discard items to make room.
    """

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
    #stash-options {
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
        # Index-based tracking (handles duplicate item IDs correctly)
        self._selected_loot: set[int] = set()
        self._loot_keys: list[str] = []
        self._discarded_stash: set[int] = set()
        self._stash_keys: list[str] = []

    @property
    def _effective_space(self) -> int:
        """Available stash slots, accounting for items marked for discard."""
        run = self.app.run_state
        if run is None:
            return 0
        return STASH_LIMIT - len(run.party.stash) + len(self._discarded_stash)

    def compose(self) -> ComposeResult:
        with Vertical(id="post-combat-container"):
            yield Static("[bold #44aa44]--- VICTORY ---[/bold #44aa44]", id="victory-header")
            yield Label(f"Rounds: {self._result.rounds_taken}", id="rounds-info")
            yield Label("")
            yield Static("", id="xp-summary")
            yield Label("")
            yield Static("", id="loot-summary")
            yield OptionList(id="loot-options")
            yield Static("", id="stash-label")
            yield OptionList(id="stash-options")
            yield Label("")
            yield Button("Continue", variant="primary", id="btn-continue")

    def on_mount(self) -> None:
        self._render_xp_summary()
        self._render_loot()
        loot_list = self.query_one("#loot-options", OptionList)
        if self._loot_keys:
            loot_list.focus()
        else:
            loot_list.display = False
            self.query_one("#stash-label", Static).display = False
            self.query_one("#stash-options", OptionList).display = False
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

        space = self._effective_space
        lines: list[str] = [
            f"  Money: [bold #e6c566]+{loot.money}G[/bold #e6c566]",
        ]
        if loot.item_ids:
            lines.append(f"  Items: {len(loot.item_ids)} found (stash space: {space})")

        self.query_one("#loot-summary", Static).update(
            "[bold]Loot[/bold]\n" + "\n".join(lines)
        )

        # Populate interactive loot selection
        loot_list = self.query_one("#loot-options", OptionList)
        loot_list.clear_options()
        self._loot_keys = []
        self._selected_loot.clear()

        for i, item_id in enumerate(loot.item_ids):
            item = self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            if len(self._selected_loot) < space:
                self._selected_loot.add(i)
                marker = "[bold #44aa44]+[/bold #44aa44]"
            else:
                marker = "[dim]-[/dim]"
            loot_list.add_option(Option(f"{marker} {name}{desc}"))
            self._loot_keys.append(item_id)

        # Show stash for discard if loot exceeds available space
        self._render_stash()

    def _render_stash(self) -> None:
        """Show stash items for discard when drops exceed available space."""
        run = self.app.run_state
        stash_label = self.query_one("#stash-label", Static)
        stash_list = self.query_one("#stash-options", OptionList)

        if run is None or not self._loot.item_ids:
            stash_label.display = False
            stash_list.display = False
            return

        base_space = STASH_LIMIT - len(run.party.stash)
        if base_space >= len(self._loot.item_ids) or not run.party.stash:
            # Enough room for all loot, or nothing to discard
            stash_label.display = False
            stash_list.display = False
            return

        stash_label.update("[bold]Stash[/bold] [dim](select to discard)[/dim]")
        stash_label.display = True
        stash_list.display = True

        stash_list.clear_options()
        self._stash_keys = list(run.party.stash)

        for i, item_id in enumerate(self._stash_keys):
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            if i in self._discarded_stash:
                marker = "[bold #cc4444]x[/bold #cc4444]"
            else:
                marker = "[dim]-[/dim]"
            stash_list.add_option(Option(f"{marker} {name}{desc}"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Toggle item selection on Enter."""
        if event.option_list.id == "loot-options":
            self._toggle_loot(event.option_index)
        elif event.option_list.id == "stash-options":
            self._toggle_stash(event.option_index)

    def _toggle_loot(self, idx: int) -> None:
        """Toggle loot item selection."""
        if idx < 0 or idx >= len(self._loot_keys):
            return

        if idx in self._selected_loot:
            self._selected_loot.discard(idx)
        elif len(self._selected_loot) < self._effective_space:
            self._selected_loot.add(idx)

        self._refresh_loot_markers()

    def _toggle_stash(self, idx: int) -> None:
        """Toggle stash item for discard, updating available loot space."""
        if idx < 0 or idx >= len(self._stash_keys):
            return

        if idx in self._discarded_stash:
            self._discarded_stash.discard(idx)
            # Space shrunk — deselect excess loot from the bottom up
            self._reconcile_selections()
        else:
            self._discarded_stash.add(idx)

        self._refresh_loot_markers()
        self._refresh_stash_markers()
        self._update_loot_header()

    def _reconcile_selections(self) -> None:
        """Deselect excess loot items when effective space shrinks."""
        space = self._effective_space
        while len(self._selected_loot) > space:
            last = max(self._selected_loot)
            self._selected_loot.discard(last)

    def _refresh_loot_markers(self) -> None:
        """Update the +/- markers in the loot list."""
        loot_list = self.query_one("#loot-options", OptionList)
        loot_list.clear_options()
        for i, item_id in enumerate(self._loot_keys):
            item = self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            if i in self._selected_loot:
                marker = "[bold #44aa44]+[/bold #44aa44]"
            else:
                marker = "[dim]-[/dim]"
            loot_list.add_option(Option(f"{marker} {name}{desc}"))

    def _refresh_stash_markers(self) -> None:
        """Update the x/- markers in the stash list."""
        stash_list = self.query_one("#stash-options", OptionList)
        stash_list.clear_options()
        run = self.app.run_state
        for i, item_id in enumerate(self._stash_keys):
            item = (
                (run.party.items.get(item_id) if run else None)
                or self.app.game_data.items.get(item_id)
            )
            name = item.name if item else item_id
            desc = f" — {item.description}" if item and item.description else ""
            if i in self._discarded_stash:
                marker = "[bold #cc4444]x[/bold #cc4444]"
            else:
                marker = "[dim]-[/dim]"
            stash_list.add_option(Option(f"{marker} {name}{desc}"))

    def _update_loot_header(self) -> None:
        """Refresh the stash space counter in the loot summary."""
        run = self.app.run_state
        if run is None:
            return
        loot = self._loot
        space = self._effective_space
        lines: list[str] = [
            f"  Money: [bold #e6c566]+{loot.money}G[/bold #e6c566]",
        ]
        if loot.item_ids:
            lines.append(f"  Items: {len(loot.item_ids)} found (stash space: {space})")
        self.query_one("#loot-summary", Static).update(
            "[bold]Loot[/bold]\n" + "\n".join(lines)
        )

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

        # Build selected loot and discarded stash item lists
        selected = [self._loot_keys[i] for i in sorted(self._selected_loot)]
        discarded = [self._stash_keys[i] for i in sorted(self._discarded_stash)]
        offered = list(self._loot_keys)
        skipped = [iid for i, iid in enumerate(self._loot_keys) if i not in self._selected_loot]

        # Apply loot (discards stash items first, then adds selected loot)
        run = self.app.game_loop.apply_loot(
            run, self._loot, selected, discarded or None
        )

        # Advance zone before logging so the macro event snapshot captures
        # the updated is_cleared/current_encounter_index flags.
        run = self.app.game_loop.advance_zone(run)

        run = run.record_macro(
            "pick_loot",
            {
                "offered": offered,
                "selected": selected,
                "skipped": skipped,
                "discarded_from_stash": discarded,
                "money_gained": self._loot.money,
            },
        )
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
