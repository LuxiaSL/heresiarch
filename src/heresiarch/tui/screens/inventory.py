"""Inventory screen — stash management, use consumables, equip items."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.models.party import STASH_LIMIT


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
        self._target_keys: list[str] = []  # keys per target option
        self._selected_item_id: str | None = None
        self._mode: str | None = None  # "use", "equip_action", "equip_target", "equip_slot"
        self._equip_char_id: str | None = None  # for accessory slot selection

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
        self._mode = None
        self._equip_char_id = None

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
                elif item:
                    self._selected_item_id = item_id
                    self._show_equipment_actions()

        elif event.option_list.id == "target-list":
            idx = event.option_index
            if 0 <= idx < len(self._target_keys) and self._target_keys[idx]:
                key = self._target_keys[idx]
                if key == "cancel":
                    self._cancel_use()
                elif self._mode == "use":
                    self._use_consumable(key)
                elif self._mode == "equip_action":
                    if key == "equip":
                        self._show_equip_targets()
                    elif key == "party":
                        self._go_to_party()
                elif self._mode == "equip_target":
                    self._handle_equip_target(key)
                elif self._mode == "equip_slot":
                    if self._equip_char_id:
                        self._do_equip_item(self._equip_char_id, key)

    def _show_item_detail(self, item_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return

        item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
        if item is None:
            return

        lines: list[str] = [
            f"[bold]{item.name}[/bold]",
        ]
        if item.description:
            lines.append(f"  {item.description}")
        lines.append(f"  Type: {item.display_type}")

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

    # ------------------------------------------------------------------
    # Equipment action menu
    # ------------------------------------------------------------------

    def _show_equipment_actions(self) -> None:
        """Show action menu for non-consumable items."""
        if self._selected_item_id is None:
            return

        self._mode = "equip_action"
        item = self.app.game_data.items.get(self._selected_item_id)
        item_name = item.name if item else self._selected_item_id

        self.query_one("#action-prompt", Label).update(
            f"[bold]{item_name}[/bold]"
        )

        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = True
        self._target_keys = []

        target_list.add_option(Option("Equip"))
        self._target_keys.append("equip")

        target_list.add_option(Option("Check in party"))
        self._target_keys.append("party")

        target_list.add_option(Option("[dim]Cancel[/dim]"))
        self._target_keys.append("cancel")
        target_list.focus()

    def _go_to_party(self) -> None:
        """Navigate to the party screen from equipment action."""
        self._cancel_use()
        from heresiarch.tui.screens.party import PartyScreen

        self.app.push_screen(PartyScreen())

    # ------------------------------------------------------------------
    # Equip flow: target selection → (optional slot) → equip
    # ------------------------------------------------------------------

    def _show_equip_targets(self) -> None:
        """Show party members to equip the selected item on."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        self._mode = "equip_target"
        item = self.app.game_data.items.get(self._selected_item_id)
        item_name = item.name if item else self._selected_item_id
        from heresiarch.engine.models.items import EquipType

        is_accessory = item.equip_type == EquipType.ACCESSORY if item else False
        equip_slot = item.equip_type.value if item and item.equip_type else ""

        self.query_one("#action-prompt", Label).update(
            f"Equip [bold]{item_name}[/bold] on:"
        )

        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = True
        self._target_keys = []

        for char_id in run.party.active + run.party.reserve:
            char = run.party.characters.get(char_id)
            if char is None:
                continue
            job = self.app.game_data.jobs.get(char.job_id)
            job_name = job.name if job else char.job_id
            reserve = " [dim][reserve][/dim]" if char_id in run.party.reserve else ""

            # Show replacement info for weapon/armor (slot is known)
            replacing = ""
            if equip_slot and not is_accessory:
                current_id = char.equipment.get(equip_slot)
                if current_id:
                    ci = run.party.items.get(current_id) or self.app.game_data.items.get(current_id)
                    replacing = f" [dim](replacing {ci.name})[/dim]" if ci else ""

            target_list.add_option(Option(
                f"{char.name} — Lv{char.level} {job_name}{reserve}{replacing}"
            ))
            self._target_keys.append(char_id)

        target_list.add_option(Option("[dim]Cancel[/dim]"))
        self._target_keys.append("cancel")
        target_list.focus()

    def _handle_equip_target(self, char_id: str) -> None:
        """Handle character selection for equipping."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        item = self.app.game_data.items.get(self._selected_item_id)
        if item is None:
            return

        from heresiarch.engine.models.items import EquipType

        if item.equip_type == EquipType.ACCESSORY:
            # Accessories can go in either slot — need to pick
            self._equip_char_id = char_id
            self._show_slot_selection(char_id)
        elif item.equip_type:
            self._do_equip_item(char_id, item.equip_type.value)
        else:
            # Consumable or unknown — shouldn't reach here
            pass

    def _show_slot_selection(self, char_id: str) -> None:
        """Show accessory slot picker."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        self._mode = "equip_slot"
        item = self.app.game_data.items.get(self._selected_item_id)
        item_name = item.name if item else self._selected_item_id
        char = run.party.characters.get(char_id)
        char_name = char.name if char else char_id

        self.query_one("#action-prompt", Label).update(
            f"Equip [bold]{item_name}[/bold] on {char_name} — pick slot:"
        )

        target_list = self.query_one("#target-list", OptionList)
        target_list.clear_options()
        target_list.display = True
        self._target_keys = []

        for acc_slot in ("ACCESSORY_1", "ACCESSORY_2"):
            current_id = char.equipment.get(acc_slot) if char else None
            if current_id:
                ci = run.party.items.get(current_id) or self.app.game_data.items.get(current_id)
                current_info = f" [dim](replacing {ci.name})[/dim]" if ci else ""
            else:
                current_info = " [dim](empty)[/dim]"
            target_list.add_option(Option(f"{acc_slot}{current_info}"))
            self._target_keys.append(acc_slot)

        target_list.add_option(Option("[dim]Cancel[/dim]"))
        self._target_keys.append("cancel")
        target_list.focus()

    def _do_equip_item(self, char_id: str, slot: str) -> None:
        """Execute equip through the game loop."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        try:
            self.app.run_state = self.app.game_loop.equip_item(
                run, char_id, self._selected_item_id, slot
            )
        except ValueError:
            pass

        self._selected_item_id = None
        self._mode = None
        self._equip_char_id = None
        self._populate_stash()
        self.query_one("#stash-list", OptionList).focus()

    # ------------------------------------------------------------------
    # Consumable use flow
    # ------------------------------------------------------------------

    def _show_use_targets(self) -> None:
        """Show character targets for consumable use."""
        run = self.app.run_state
        if run is None or self._selected_item_id is None:
            return

        self._mode = "use"
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

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _cancel_use(self) -> None:
        self._selected_item_id = None
        self._mode = None
        self._equip_char_id = None
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
        self._mode = None
        self._populate_stash()
        self.query_one("#stash-list", OptionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        if self._mode == "equip_slot":
            # Step back to character selection
            self._equip_char_id = None
            self._show_equip_targets()
        elif self._mode == "equip_target":
            # Step back to action menu
            self._show_equipment_actions()
        elif self._selected_item_id is not None:
            self._cancel_use()
        else:
            self.app.pop_screen()
