"""Inventory screen — stash management, use consumables."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.game_loop import STASH_LIMIT


class InventoryScreen(Screen):
    """View and manage the party stash."""

    CSS = """
    #stash-panel {
        width: 40;
        height: 100%;
        padding: 1;
    }
    #detail-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    #stash-list {
        height: auto;
        max-height: 14;
    }
    #target-list {
        height: auto;
        max-height: 8;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._stash_keys: list[str] = []  # item_id per option
        self._target_keys: list[str] = []  # char_id per target option
        self._selected_item_id: str | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="stash-panel"):
                yield Static("[bold]Stash[/bold]", id="stash-header")
                yield OptionList(id="stash-list")
                yield Label("", id="stash-info")
                yield Button("[ESC] Back", id="btn-back")

            with Vertical(id="detail-panel"):
                yield Static("", id="item-detail")
                yield Label("", id="action-prompt")
                yield OptionList(id="target-list")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_stash()
        self.query_one("#stash-list", OptionList).focus()

    def on_screen_resume(self) -> None:
        self._populate_stash()

    def _populate_stash(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        stash_list = self.query_one("#stash-list", OptionList)
        stash_list.clear_options()
        self._stash_keys = []

        self.query_one("#stash-info", Label).update(
            f"[dim]({len(run.party.stash)}/{STASH_LIMIT} slots)[/dim]  "
            f"Money: [bold #e6c566]{run.party.money}G[/bold #e6c566]"
        )

        # Clear detail/targets before rebuilding (must run even if stash is empty)
        self.query_one("#item-detail", Static).update("")
        self.query_one("#action-prompt", Label).update("")
        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = False
        self._target_keys = []
        self._selected_item_id = None

        if not run.party.stash:
            stash_list.add_option(Option("[dim]Empty[/dim]"))
            self._stash_keys.append("")
            return

        for item_id in run.party.stash:
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            consumable = " [#44aa44](use)[/#44aa44]" if item and item.is_consumable else ""
            stash_list.add_option(Option(f"{name}{consumable}"))
            self._stash_keys.append(item_id)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "stash-list":
            idx = event.option_index
            if 0 <= idx < len(self._stash_keys) and self._stash_keys[idx]:
                self._show_item_detail(self._stash_keys[idx])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "stash-list":
            idx = event.option_index
            if 0 <= idx < len(self._stash_keys) and self._stash_keys[idx]:
                item_id = self._stash_keys[idx]
                item = self.app.game_data.items.get(item_id)
                if item and item.is_consumable:
                    self._selected_item_id = item_id
                    self._show_use_targets()

        elif event.option_list.id == "target-list":
            idx = event.option_index
            if 0 <= idx < len(self._target_keys) and self._target_keys[idx]:
                if self._target_keys[idx] == "cancel":
                    self._cancel_use()
                else:
                    self._use_consumable(self._target_keys[idx])

    def _show_item_detail(self, item_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
        if item is None:
            return

        slot_name = item.slot.value if hasattr(item.slot, "value") else str(item.slot)
        lines: list[str] = [
            f"[bold]{item.name}[/bold]",
        ]
        if item.description:
            lines.append(f"  {item.description}")
        lines.append(f"  Slot: {slot_name}")

        if item.is_consumable:
            if item.heal_amount > 0:
                lines.append(f"  Heals: [#44aa44]{item.heal_amount} HP[/#44aa44]")
            if item.heal_percent > 0:
                lines.append(f"  Heals: [#44aa44]{int(item.heal_percent * 100)}% max HP[/#44aa44]")
            lines.append("")
            lines.append("[dim]Press Enter to use[/dim]")

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

    def _show_use_targets(self) -> None:
        """Show character targets for consumable use."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        item = self.app.game_data.items.get(self._selected_item_id)
        item_name = item.name if item else self._selected_item_id

        self.query_one("#action-prompt", Label).update(
            f"Use [bold]{item_name}[/bold] on:"
        )

        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = True
        self._target_keys = []

        for char_id in run.party.active + run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                max_hp = char.max_hp
                hp_pct = char.current_hp / max(max_hp, 1)
                hp_color = "#44aa44" if hp_pct > 0.5 else "#cccc44" if hp_pct > 0.25 else "#cc4444"
                target_list.add_option(Option(
                    f"{char.name} — [{hp_color}]{char.current_hp}/{max_hp}[/{hp_color}]"
                ))
                self._target_keys.append(char_id)

        target_list.add_option(Option("[dim]Cancel[/dim]"))
        self._target_keys.append("cancel")
        target_list.focus()

    def _cancel_use(self) -> None:
        self._selected_item_id = None
        self.query_one("#action-prompt", Label).update("")
        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = False
        self._target_keys = []
        self.query_one("#stash-list", OptionList).focus()

    def _use_consumable(self, char_id: str) -> None:
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        try:
            self.app.run_state = self.app.game_loop.use_consumable(
                run, self._selected_item_id, char_id
            )
        except ValueError:
            pass

        self._selected_item_id = None
        self._populate_stash()
        self.query_one("#stash-list", OptionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        if self._selected_item_id is not None:
            self._cancel_use()
        else:
            self.app.pop_screen()
