"""Post-combat screen — XP summary, loot selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Label, Static

from heresiarch.engine.game_loop import STASH_LIMIT
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.run_state import CombatResult


class PostCombatScreen(Screen):
    """Victory! Show XP gains, level-ups, and loot selection."""

    def __init__(self, combat_result: CombatResult, loot: LootResult) -> None:
        super().__init__()
        self._result = combat_result
        self._loot = loot
        self._selected_items: set[str] = set()

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="post-combat-container"):
                    yield Static("[bold #44aa44]--- VICTORY ---[/bold #44aa44]", id="victory-header")
                    yield Label(f"Rounds: {self._result.rounds_taken}", id="rounds-info")
                    yield Label("")
                    yield Static("", id="xp-summary")
                    yield Label("")
                    yield Static("", id="loot-summary")
                    yield Label("")
                    yield Static("", id="loot-selection")
                    yield Label("")
                    yield Button("Continue", variant="primary", id="btn-continue")

    def on_mount(self) -> None:
        self._render_xp_summary()
        self._render_loot()

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
        """Show money and item drops."""
        loot = self._loot
        lines: list[str] = [f"  Money: [bold #e6c566]+{loot.money}G[/bold #e6c566]"]

        self.query_one("#loot-summary", Static).update(
            "[bold]Loot[/bold]\n" + "\n".join(lines)
        )

        # Item selection
        run = self.app.run_state
        if run is None:
            return

        stash_space = STASH_LIMIT - len(run.party.stash)
        if loot.item_ids:
            selection_container = self.query_one("#loot-selection", Static)
            item_lines: list[str] = [f"[bold]Items Found[/bold] (stash space: {stash_space})"]
            for item_id in loot.item_ids:
                item = self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                desc = item.description if item else ""
                item_lines.append(f"  {name} — {desc}")
                # Auto-select if stash has room
                if stash_space > 0:
                    self._selected_items.add(item_id)
                    stash_space -= 1
            selection_container.update("\n".join(item_lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            self._continue()

    def _continue(self) -> None:
        """Apply loot, advance zone, check recruitment, autosave."""
        run = self.app.run_state
        if run is None:
            return

        # Apply selected loot items
        run = self.app.game_loop.apply_loot(run, self._loot, list(self._selected_items))

        # Advance zone
        run = self.app.game_loop.advance_zone(run)
        self.app.run_state = run

        # Autosave after combat
        try:
            self.app.save_manager.autosave(run)
        except Exception:
            pass

        if run.zone_state and run.zone_state.is_cleared:
            # Zone cleared — heal and move to next zone
            run = self.app.game_loop.enter_safe_zone(run)
            self.app.run_state = run

            # Check if there are more zones
            zones = list(self.app.game_data.zones.keys())
            completed = set(run.zones_completed)
            remaining = [z for z in zones if z not in completed]

            if remaining:
                run = self.app.game_loop.enter_zone(run, remaining[0])
                self.app.run_state = run
        else:
            # Mid-zone: check for recruitment encounter
            if run.current_zone_id:
                zone = self.app.game_data.zones.get(run.current_zone_id)
                if zone and zone.recruitment_chance > 0:
                    roll = self.app.rng.random()
                    if roll < zone.recruitment_chance:
                        candidate = self.app.game_loop.recruitment_engine.generate_candidate(
                            zone_level=zone.zone_level
                        )
                        from heresiarch.tui.screens.recruitment import RecruitmentScreen

                        self.app.switch_screen(RecruitmentScreen(candidate))
                        return

        from heresiarch.tui.screens.zone import ZoneScreen

        self.app.switch_screen(ZoneScreen())
