"""Inventory screen — stash management, use consumables."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from heresiarch.engine.formulas import calculate_max_hp
from heresiarch.engine.game_loop import STASH_LIMIT


class InventoryScreen(Screen):
    """View and manage the party stash."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._selected_item_id: str | None = None
        self._mode: str = "overview"  # overview | use_target

    def compose(self) -> ComposeResult:
        with Horizontal(id="inventory-layout"):
            with Vertical(id="stash-panel"):
                yield Static("[bold]Stash[/bold]", id="stash-header")
                yield Static("", id="stash-list")
                yield Label("")
                yield Button("Back", id="btn-back")

            with Vertical(id="item-detail-panel"):
                yield Static("", id="item-detail")
                yield Label("", id="item-prompt")
                with Vertical(id="item-actions"):
                    yield Static("", id="item-actions-placeholder")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        # Stash list
        lines: list[str] = [
            f"[dim]({len(run.party.stash)}/{STASH_LIMIT} slots)[/dim]",
            "",
        ]

        if not run.party.stash:
            lines.append("[dim]Empty[/dim]")
        else:
            for i, item_id in enumerate(run.party.stash):
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                consumable = " [#44aa44](consumable)[/#44aa44]" if item and item.is_consumable else ""
                marker = " ◄" if item_id == self._selected_item_id else ""
                lines.append(f"  {name}{consumable}{marker}")

        lines.append("")
        lines.append(f"Money: [bold #e6c566]{run.party.money}G[/bold #e6c566]")

        self.query_one("#stash-list", Static).update("\n".join(lines))

        # Item actions
        actions = self.query_one("#item-actions")
        for child in list(actions.children):
            if child.id != "item-actions-placeholder":
                child.remove()

        if self._mode == "overview":
            # Show item selection buttons
            for i, item_id in enumerate(run.party.stash):
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                actions.mount(Button(name, id=f"select-item-{i}-{item_id}"))

        elif self._mode == "use_target" and self._selected_item_id:
            self._show_use_targets()

        if self._selected_item_id:
            self._render_item_detail()

    def _render_item_detail(self) -> None:
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        item = run.party.items.get(self._selected_item_id) or self.app.game_data.items.get(self._selected_item_id)
        if item is None:
            return

        lines: list[str] = [
            f"[bold]{item.name}[/bold]",
            f"  {item.description}" if item.description else "",
            f"  Slot: {item.slot}",
        ]

        if item.is_consumable:
            if item.heal_amount > 0:
                lines.append(f"  Heals: [#44aa44]{item.heal_amount} HP[/#44aa44]")
            if item.heal_percent > 0:
                lines.append(f"  Heals: [#44aa44]{int(item.heal_percent * 100)}% max HP[/#44aa44]")

        if item.scaling:
            lines.append(f"  Scaling: {item.scaling.scaling_type.value} ({item.scaling.stat.value})")

        if item.flat_stat_bonus:
            bonuses = ", ".join(f"{k}+{v}" for k, v in item.flat_stat_bonus.items() if v != 0)
            if bonuses:
                lines.append(f"  Bonuses: {bonuses}")

        if item.granted_ability_id:
            ability = self.app.game_data.abilities.get(item.granted_ability_id)
            aname = ability.name if ability else item.granted_ability_id
            lines.append(f"  Grants: {aname}")

        self.query_one("#item-detail", Static).update("\n".join(lines))

        # Action buttons
        if self._mode == "overview":
            prompt = self.query_one("#item-prompt", Label)
            actions = self.query_one("#item-actions")
            for child in list(actions.children):
                if child.id != "item-actions-placeholder":
                    child.remove()

            if item.is_consumable:
                actions.mount(Button("Use", id="btn-use-consumable", variant="primary"))
            actions.mount(Button("Back to List", id="btn-item-back"))
            prompt.update(f"[bold]{item.name}[/bold]")

    def _show_use_targets(self) -> None:
        """Show character targets for consumable use."""
        run = self.app.run_state
        if run is None:
            return

        prompt = self.query_one("#item-prompt", Label)
        prompt.update("Use on which character?")

        actions = self.query_one("#item-actions")
        for child in list(actions.children):
            if child.id != "item-actions-placeholder":
                child.remove()

        for char_id in run.party.active + run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                max_hp = calculate_max_hp(
                    job.base_hp, job.hp_growth, char.level, char.base_stats.DEF
                ) if job else 0
                hp_str = f"HP: {char.current_hp}/{max_hp}"
                actions.mount(Button(
                    f"{char.name} ({hp_str})",
                    id=f"use-on-{char_id}",
                ))

        actions.mount(Button("Cancel", id="btn-use-cancel"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "btn-back":
            self.app.pop_screen()
            return

        if btn_id.startswith("select-item-"):
            # Extract item_id (after the index)
            parts = btn_id.removeprefix("select-item-").split("-", 1)
            if len(parts) >= 2:
                item_id = parts[1]
                self._selected_item_id = item_id
                self._mode = "overview"
                self._refresh()
            return

        if btn_id == "btn-item-back":
            self._selected_item_id = None
            self._mode = "overview"
            self._refresh()
            return

        if btn_id == "btn-use-consumable":
            self._mode = "use_target"
            self._refresh()
            return

        if btn_id == "btn-use-cancel":
            self._mode = "overview"
            self._refresh()
            return

        if btn_id.startswith("use-on-"):
            char_id = btn_id.removeprefix("use-on-")
            self._use_consumable(char_id)
            return

    def _use_consumable(self, char_id: str) -> None:
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        try:
            self.app.run_state = self.app.game_loop.use_consumable(
                run, self._selected_item_id, char_id
            )
            self._selected_item_id = None
            self._mode = "overview"
        except ValueError:
            pass
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()
