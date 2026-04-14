"""Load screen — browse runs and save slots, pick one to load."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.save_manager import SaveSlot


class DeleteConfirmModal(ModalScreen):
    """Y/N modal to confirm save deletion."""

    CSS = """
    DeleteConfirmModal {
        align: center middle;
    }
    #delete-dialog {
        width: 50;
        height: 5;
        border: round #cc4444;
        background: $surface;
        padding: 0 2;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        run_id: str,
        slot_id: str | None = None,
    ) -> None:
        super().__init__()
        self.run_id = run_id
        self.slot_id = slot_id

    def compose(self) -> ComposeResult:
        if self.slot_id is not None:
            label = f"[bold red]Delete slot [/bold red][bold]{self.slot_id}[/bold][bold red]?[/bold red]"
        else:
            label = f"[bold red]Delete run [/bold red][bold]{self.run_id}[/bold][bold red]?[/bold red]"
        yield Static(
            f"{label}\n[dim](y/n)[/dim]",
            id="delete-dialog",
        )

    def action_confirm(self) -> None:
        try:
            if self.slot_id is not None:
                self.app.save_manager.delete_slot(self.run_id, self.slot_id)
            else:
                self.app.save_manager.delete_run_saves(self.run_id)
        except Exception:
            pass  # Silently handle — the refresh will show current state
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


def _format_timestamp(iso_str: str) -> str:
    """Format an ISO timestamp into a human-readable string."""
    if not iso_str:
        return "unknown time"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_str


def _zone_display(zone_id: str | None, game_data: object) -> str:
    """Resolve a zone_id to a display name, with fallback."""
    if zone_id is None:
        return "Zone Select"
    zones = getattr(game_data, "zones", {})
    zone = zones.get(zone_id)
    if zone is not None:
        return getattr(zone, "name", zone_id)
    return zone_id


class LoadScreen(Screen):
    """Browse saved runs and slots, pick one to load."""

    CSS = """
    LoadScreen {
        align: center middle;
    }
    #load-box {
        width: 80;
        height: auto;
        padding: 1 2;
    }
    #load-header {
        text-align: center;
        margin-bottom: 1;
    }
    #load-list {
        height: auto;
        max-height: 20;
        margin: 1 0;
    }
    #load-detail {
        height: auto;
        min-height: 3;
        padding: 0 1;
        border: tall #333355;
    }
    #load-hint {
        margin-top: 1;
        color: #6b6b6b;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
        ("d", "delete", "Delete"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Tracks which view we're in: "runs" or "slots"
        self._view: str = "runs"
        # Parallel list of action keys for the current option list
        self._action_keys: list[str] = []
        # When viewing slots, the currently selected run_id
        self._current_run_id: str | None = None
        # Cache of loaded slots per run_id
        self._slots_cache: dict[str, list[SaveSlot]] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="load-box"):
            yield Static("[bold]Load Game[/bold]", id="load-header")
            yield OptionList(id="load-list")
            yield Static("", id="load-detail")
            yield Static("[dim]Enter to select  |  d to delete  |  Esc to go back[/dim]", id="load-hint")
        yield Footer()

    def on_mount(self) -> None:
        self._show_runs()

    # ------------------------------------------------------------------
    # Run list view
    # ------------------------------------------------------------------

    def _show_runs(self) -> None:
        """Populate the option list with available runs."""
        self._view = "runs"
        self._current_run_id = None
        option_list = self.query_one("#load-list", OptionList)
        option_list.clear_options()
        self._action_keys = []

        try:
            runs = self.app.save_manager.list_runs()
        except Exception:
            runs = []

        if not runs:
            self.query_one("#load-detail", Static).update(
                "[dim]No saved runs found.[/dim]"
            )
            option_list.focus()
            return

        # List all runs, newest first
        for run_id in reversed(runs):
            slots = self._get_slots(run_id)
            if not slots:
                continue
            newest_slot = max(slots, key=lambda s: s.saved_at or "")
            zone_name = _zone_display(newest_slot.zone_id, self.app.game_data)
            timestamp = _format_timestamp(newest_slot.saved_at)
            slot_count = len(slots)
            option_list.add_option(
                Option(
                    f"[bold]{run_id}[/bold]  "
                    f"{zone_name}  |  "
                    f"{newest_slot.party_level_summary}  |  "
                    f"[dim]{timestamp}  ({slot_count} save{'s' if slot_count != 1 else ''})[/dim]"
                )
            )
            self._action_keys.append(f"run:{run_id}")

        option_list.focus()
        option_list.highlighted = 0
        self._update_detail_for_runs(0)

    def _update_detail_for_runs(self, idx: int) -> None:
        """Show detail for the highlighted run."""
        detail = self.query_one("#load-detail", Static)
        if idx < 0 or idx >= len(self._action_keys):
            detail.update("")
            return

        key = self._action_keys[idx]
        if key.startswith("run:"):
            run_id = key[4:]
            slots = self._get_slots(run_id)
            lines = [f"[bold]{run_id}[/bold] — {len(slots)} save slot{'s' if len(slots) != 1 else ''}"]
            for slot in slots:
                zone_name = _zone_display(slot.zone_id, self.app.game_data)
                timestamp = _format_timestamp(slot.saved_at)
                lines.append(
                    f"  {slot.slot_id}: {zone_name}  |  "
                    f"{slot.party_level_summary}  |  [dim]{timestamp}[/dim]"
                )
            detail.update("\n".join(lines))
        else:
            detail.update("")

    # ------------------------------------------------------------------
    # Slot list view (within a run)
    # ------------------------------------------------------------------

    def _show_slots(self, run_id: str) -> None:
        """Drill into a run and show its save slots."""
        self._view = "slots"
        self._current_run_id = run_id
        option_list = self.query_one("#load-list", OptionList)
        option_list.clear_options()
        self._action_keys = []

        self.query_one("#load-header", Static).update(
            f"[bold]Load Game[/bold] > [bold #e6c566]{run_id}[/bold #e6c566]"
        )

        slots = self._get_slots(run_id)
        if not slots:
            self.query_one("#load-detail", Static).update(
                "[dim]No save slots found for this run.[/dim]"
            )
            option_list.focus()
            return

        # Sort slots: most recent first
        sorted_slots = sorted(slots, key=lambda s: s.saved_at or "", reverse=True)

        for slot in sorted_slots:
            zone_name = _zone_display(slot.zone_id, self.app.game_data)
            timestamp = _format_timestamp(slot.saved_at)
            label = (
                f"[bold]{slot.slot_id}[/bold]  "
                f"{zone_name}  |  "
                f"{slot.party_level_summary}  |  "
                f"[dim]{timestamp}[/dim]"
            )
            option_list.add_option(Option(label))
            self._action_keys.append(f"slot:{run_id}:{slot.slot_id}")

        option_list.focus()
        option_list.highlighted = 0
        self._update_detail_for_slots(0)

    def _update_detail_for_slots(self, idx: int) -> None:
        """Show detail for the highlighted slot."""
        detail = self.query_one("#load-detail", Static)
        if idx < 0 or idx >= len(self._action_keys):
            detail.update("")
            return

        key = self._action_keys[idx]
        if not key.startswith("slot:"):
            detail.update("")
            return

        parts = key.split(":", 2)
        run_id, slot_id = parts[1], parts[2]
        slots = self._get_slots(run_id)
        slot = next((s for s in slots if s.slot_id == slot_id), None)
        if slot is None:
            detail.update("")
            return

        zone_name = _zone_display(slot.zone_id, self.app.game_data)
        timestamp = _format_timestamp(slot.saved_at)
        lines = [
            f"[bold #e6c566]{slot.slot_id}[/bold #e6c566]  —  {timestamp}",
            f"  Zone: {zone_name}",
            f"  Party: {slot.party_level_summary}",
        ]
        detail.update("\n".join(lines))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option_list.id != "load-list":
            return
        idx = event.option_index
        if self._view == "runs":
            self._update_detail_for_runs(idx)
        else:
            self._update_detail_for_slots(idx)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option_list.id != "load-list":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._action_keys):
            return

        key = self._action_keys[idx]

        if key.startswith("run:"):
            run_id = key[4:]
            self._show_slots(run_id)
        elif key.startswith("slot:"):
            parts = key.split(":", 2)
            self._do_load(parts[1], parts[2])

    def action_go_back(self) -> None:
        """Escape/backspace: go up one level or back to title."""
        if self._view == "slots":
            self.query_one("#load-header", Static).update(
                "[bold]Load Game[/bold]"
            )
            self._show_runs()
        else:
            self.app.pop_screen()

    def action_delete(self) -> None:
        """Prompt to delete the highlighted run or slot."""
        option_list = self.query_one("#load-list", OptionList)
        idx = option_list.highlighted
        if idx is None or idx < 0 or idx >= len(self._action_keys):
            return

        key = self._action_keys[idx]
        if key.startswith("run:"):
            run_id = key[4:]
            self.app.push_screen(
                DeleteConfirmModal(run_id=run_id),
                callback=self._on_delete_dismissed,
            )
        elif key.startswith("slot:"):
            parts = key.split(":", 2)
            run_id, slot_id = parts[1], parts[2]
            self.app.push_screen(
                DeleteConfirmModal(run_id=run_id, slot_id=slot_id),
                callback=self._on_delete_dismissed,
            )

    def _on_delete_dismissed(self, confirmed: bool) -> None:
        """Refresh the list after the delete modal closes."""
        if not confirmed:
            return
        # Invalidate the slot cache so we pick up the deletion
        self._slots_cache.clear()
        if self._view == "slots":
            # If the run was fully deleted, go back to runs view
            run_id = self._current_run_id
            if run_id and not self._get_slots(run_id):
                self.query_one("#load-header", Static).update(
                    "[bold]Load Game[/bold]"
                )
                self._show_runs()
            else:
                self._show_slots(self._current_run_id)
        else:
            self._show_runs()

    # ------------------------------------------------------------------
    # Load logic
    # ------------------------------------------------------------------

    def _do_load(self, run_id: str, slot_id: str) -> None:
        """Load a save slot and route to the appropriate screen."""
        try:
            run_state = self.app.save_manager.load_run(run_id, slot_id)
        except FileNotFoundError:
            self.query_one("#load-detail", Static).update(
                f"[bold red]Save not found:[/bold red] {run_id}/{slot_id}"
            )
            return
        except Exception as exc:
            self.query_one("#load-detail", Static).update(
                f"[bold red]Failed to load save:[/bold red] {exc}"
            )
            return

        try:
            self.app.run_state = self.app.game_loop.rehydrate_run(run_state)
        except Exception as exc:
            self.query_one("#load-detail", Static).update(
                f"[bold red]Failed to rehydrate run:[/bold red] {exc}"
            )
            return

        if self.app.run_state.current_zone_id is not None:
            from heresiarch.tui.screens.zone import ZoneScreen

            self.app.switch_screen(ZoneScreen())
        else:
            from heresiarch.tui.screens.zone_select import ZoneSelectScreen

            self.app.switch_screen(ZoneSelectScreen())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_slots(self, run_id: str) -> list[SaveSlot]:
        """Get slots for a run, with caching and error handling."""
        if run_id in self._slots_cache:
            return self._slots_cache[run_id]
        try:
            slots = self.app.save_manager.list_slots(run_id)
        except Exception:
            slots = []
        self._slots_cache[run_id] = slots
        return slots

