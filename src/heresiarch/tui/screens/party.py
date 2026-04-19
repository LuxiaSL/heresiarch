"""Party management screen — view characters, equip/unequip, swap, MC Mimic."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.models.stats import StatBlock

# Stat comparison colors
_CLR_BETTER = "#44aa44"  # Green — preview stat is higher than current
_CLR_WORSE = "#cc4444"   # Red — preview stat is lower than current
_CLR_SAME = "#4488cc"    # Blue — preview stat matches current
_CLR_DEBUFF = "#cc4444"  # Red — equipment debuff in default mode


def _stat_line(
    name: str,
    base_val: int,
    display_val: int,
    *,
    compare_to: int | None = None,
) -> str:
    """Render a single stat value.

    Default mode (compare_to=None): bold for equipment buffs, red for debuffs.
    Preview mode (compare_to set): green/red/blue vs current effective.
    """
    if compare_to is not None:
        # Preview mode — color relative to current effective stats
        if display_val > compare_to:
            color = _CLR_BETTER
        elif display_val < compare_to:
            color = _CLR_WORSE
        else:
            color = _CLR_SAME
        return f"  {name} [bold]{base_val:>3}[/bold] → [bold {color}]{display_val:>3}[/bold {color}]"
    # Default mode — no color for buffs, red for debuffs
    if display_val > base_val:
        return f"  {name} [bold]{base_val:>3}[/bold] → [bold]{display_val:>3}[/bold]"
    if display_val < base_val:
        return f"  {name} [bold]{base_val:>3}[/bold] → [bold {_CLR_DEBUFF}]{display_val:>3}[/bold {_CLR_DEBUFF}]"
    return f"  {name} [bold]{base_val:>3}[/bold]"


class PartyScreen(Screen):
    """View and manage party members, equipment, and MC job swap."""

    CSS = """
    PartyScreen {
        layout: horizontal;
    }
    #char-list-panel {
        width: 30;
        height: 100%;
        padding: 1;
    }
    #char-detail-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    #char-option-list {
        height: auto;
        max-height: 12;
    }
    #action-option-list {
        height: auto;
        max-height: 12;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._char_ids: list[str] = []
        self._action_keys: list[str] = []  # maps action option index → action key
        self._current_char_id: str | None = None  # currently displayed character

    def compose(self) -> ComposeResult:
        with Vertical(id="char-list-panel"):
            yield Static("[bold]Party[/bold]")
            yield OptionList(id="char-option-list")
            yield Label("")
            yield Button("Back", id="btn-back")

        with Vertical(id="char-detail-panel"):
            yield Static("", id="char-detail")
            yield Label("", id="action-prompt")
            yield OptionList(id="action-option-list")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_char_list()
        self.query_one("#char-option-list", OptionList).focus()

    def on_screen_resume(self) -> None:
        self._populate_char_list()

    def _populate_char_list(self) -> None:
        """Fill the character OptionList."""
        run = self.app.run_state
        if run is None:
            return

        char_list = self.query_one("#char-option-list", OptionList)
        char_list.clear_options()
        self._char_ids = []

        for char_id in run.party.active:
            char = run.party.characters.get(char_id)
            if char:
                mc = " [MC]" if char.is_mc else ""
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                char_list.add_option(Option(f"{char.name} (Lv{char.level} {job_name}){mc}"))
                self._char_ids.append(char_id)

        for char_id in run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                job = self.app.game_data.jobs.get(char.job_id)
                job_name = job.name if job else "?"
                char_list.add_option(Option(f"{char.name} (Lv{char.level} {job_name}) [reserve]"))
                self._char_ids.append(char_id)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "char-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._char_ids):
                self._current_char_id = self._char_ids[idx]
                self._show_char_detail(self._char_ids[idx])

        elif event.option_list.id == "action-option-list":
            self._on_action_highlighted(event.option_index)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "char-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._char_ids):
                self._show_char_actions(self._char_ids[idx])

        elif event.option_list.id == "action-option-list":
            idx = event.option_index
            if 0 <= idx < len(self._action_keys):
                self._handle_action(self._action_keys[idx])

    def _show_char_detail(
        self,
        char_id: str,
        preview: tuple[StatBlock, int] | None = None,
    ) -> None:
        """Render character stats in the detail panel.

        If *preview* is ``(preview_effective, preview_max_hp)``, stats are
        colored relative to the character's **current** effective stats
        (green = better, red = worse, blue = same).  Otherwise the default
        rendering is used (bold for equipment buffs, red for debuffs).
        """
        run = self.app.run_state
        if run is None:
            return

        char = run.party.characters.get(char_id)
        if char is None:
            return

        job = self.app.game_data.jobs.get(char.job_id)
        job_name = job.name if job else "?"

        base = char.base_stats
        eff = char.effective_stats

        # --- Header ---
        lines: list[str] = [
            f"[bold]{char.name}[/bold] — Lv{char.level} {job_name}",
        ]

        # --- HP line (with optional preview) ---
        if preview:
            preview_eff, preview_max_hp = preview
            if preview_max_hp > char.max_hp:
                hp_color = _CLR_BETTER
            elif preview_max_hp < char.max_hp:
                hp_color = _CLR_WORSE
            else:
                hp_color = _CLR_SAME
            lines.append(
                f"  HP: {char.current_hp}/[bold {hp_color}]{preview_max_hp}[/bold {hp_color}]  XP: {char.xp}"
            )
        else:
            lines.append(f"  HP: {char.current_hp}/{char.max_hp}  XP: {char.xp}")

        # --- Stats ---
        if preview:
            preview_eff, _ = preview
            lines.append("")
            lines.append("[bold]Stats[/bold]  [dim](base → preview)[/dim]")
            stat_parts = [
                _stat_line("STR", base.STR, preview_eff.STR, compare_to=eff.STR),
                _stat_line("MAG", base.MAG, preview_eff.MAG, compare_to=eff.MAG),
                _stat_line("DEF", base.DEF, preview_eff.DEF, compare_to=eff.DEF),
                _stat_line("RES", base.RES, preview_eff.RES, compare_to=eff.RES),
                _stat_line("SPD", base.SPD, preview_eff.SPD, compare_to=eff.SPD),
            ]
        else:
            lines.append("")
            lines.append("[bold]Stats[/bold]  [dim](base → effective)[/dim]")
            stat_parts = [
                _stat_line("STR", base.STR, eff.STR),
                _stat_line("MAG", base.MAG, eff.MAG),
                _stat_line("DEF", base.DEF, eff.DEF),
                _stat_line("RES", base.RES, eff.RES),
                _stat_line("SPD", base.SPD, eff.SPD),
            ]
        lines.append("  ".join(stat_parts))

        # --- Equipment ---
        lines.append("")
        lines.append("[bold]Equipment[/bold]")
        for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            item_id = char.equipment.get(slot)
            if item_id:
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                lines.append(f"  {slot}: {name}")
            else:
                lines.append(f"  {slot}: [dim]empty[/dim]")

        # --- Abilities ---
        lines.append("")
        lines.append("[bold]Abilities[/bold]")
        for aid in char.abilities:
            ability = self.app.game_data.abilities.get(aid)
            name = ability.name if ability else aid
            innate = " (innate)" if ability and ability.is_innate else ""
            lines.append(f"  {name}{innate}")

        # --- Growth History (MC only) ---
        if char.is_mc and char.growth_history:
            lines.append("")
            lines.append("[bold]Growth History[/bold]")
            for jid, levels in char.growth_history:
                j = self.app.game_data.jobs.get(jid)
                jname = j.name if j else jid
                lines.append(f"  {jname}: {levels} levels")

        self.query_one("#char-detail", Static).update("\n".join(lines))

    def _on_action_highlighted(self, idx: int) -> None:
        """When an action is hovered, show equipment preview if applicable."""
        if idx < 0 or idx >= len(self._action_keys) or self._current_char_id is None:
            return

        run = self.app.run_state
        if run is None:
            return

        char = run.party.characters.get(self._current_char_id)
        if char is None:
            return

        key = self._action_keys[idx]
        parts = key.split(":")

        preview: tuple[StatBlock, int] | None = None
        try:
            if parts[0] == "equip":
                _, _char_id, item_id, slot = parts
                preview = self.app.game_loop.preview_equipment_change(
                    char, run.party, slot, item_id,
                )
            elif parts[0] == "unequip":
                _, _char_id, slot = parts
                preview = self.app.game_loop.preview_equipment_change(
                    char, run.party, slot, None,
                )
        except (ValueError, KeyError):
            preview = None

        self._show_char_detail(self._current_char_id, preview=preview)

    def _show_char_actions(self, char_id: str) -> None:
        """Populate the action OptionList for a selected character."""
        run = self.app.run_state
        if run is None:
            return

        char = run.party.characters.get(char_id)
        if char is None:
            return

        self._current_char_id = char_id
        action_list = self.query_one("#action-option-list", OptionList)
        action_list.clear_options()
        self._action_keys = []

        prompt = self.query_one("#action-prompt", Label)
        prompt.update(f"[bold]{char.name}[/bold] — select action:")

        # Equip/Unequip
        for slot in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            item_id = char.equipment.get(slot)
            if item_id:
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                action_list.add_option(Option(f"Unequip {slot}: {name}"))
                self._action_keys.append(f"unequip:{char_id}:{slot}")

        # Equip from stash
        for item_id in run.party.stash:
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            if item and not item.is_consumable:
                from heresiarch.engine.models.items import EquipType

                if item.equip_type == EquipType.ACCESSORY:
                    # Accessories can go in either slot
                    for acc_slot in ("ACCESSORY_1", "ACCESSORY_2"):
                        current = char.equipment.get(acc_slot)
                        current_name = ""
                        if current:
                            ci = run.party.items.get(current) or self.app.game_data.items.get(current)
                            current_name = f" (replacing {ci.name})" if ci else ""
                        action_list.add_option(Option(f"Equip {item.name} → {acc_slot}{current_name}"))
                        self._action_keys.append(f"equip:{char_id}:{item_id}:{acc_slot}")
                elif item.equip_type:
                    slot = item.equip_type.value
                    action_list.add_option(Option(f"Equip {item.name} → {slot}"))
                    self._action_keys.append(f"equip:{char_id}:{item_id}:{slot}")

        # Swap / Move
        from heresiarch.engine.recruitment import MAX_ACTIVE_SIZE

        if char_id in run.party.active:
            # Bench to reserve (if not the only active member)
            if len(run.party.active) > 1:
                action_list.add_option(Option("Move to reserve"))
                self._action_keys.append(f"bench:{char_id}")
            # Swap with specific reserve member
            for rid in run.party.reserve:
                rc = run.party.characters.get(rid)
                if rc:
                    action_list.add_option(Option(f"Swap with {rc.name} (reserve)"))
                    self._action_keys.append(f"swap:{char_id}:{rid}")
        elif char_id in run.party.reserve:
            # Promote to active (if there's room)
            if len(run.party.active) < MAX_ACTIVE_SIZE:
                action_list.add_option(Option("Move to active"))
                self._action_keys.append(f"promote:{char_id}")
            # Swap with specific active member
            for aid in run.party.active:
                ac = run.party.characters.get(aid)
                if ac:
                    action_list.add_option(Option(f"Swap with {ac.name} (active)"))
                    self._action_keys.append(f"swap:{aid}:{char_id}")

        # MC Mimic
        if char.is_mc:
            for cid, c in run.party.characters.items():
                if c.job_id != char.job_id:
                    job = self.app.game_data.jobs.get(c.job_id)
                    jname = job.name if job else c.job_id
                    action_list.add_option(Option(f"Mimic → {jname}"))
                    self._action_keys.append(f"mimic:{c.job_id}")

        # Dismiss (non-MC, not last active)
        if not char.is_mc:
            can_dismiss = (
                char_id in run.party.reserve
                or len(run.party.active) > 1
            )
            if can_dismiss:
                equipped = [iid for iid in char.equipment.values() if iid]
                if equipped:
                    gear_names = []
                    for eid in equipped:
                        item = self.app.game_data.items.get(eid)
                        gear_names.append(item.name if item else eid)
                    warning = f" [#cc4444](loses: {', '.join(gear_names)})[/#cc4444]"
                else:
                    warning = ""
                action_list.add_option(Option(f"[#cc4444]Dismiss{warning}[/#cc4444]"))
                self._action_keys.append(f"dismiss:{char_id}")

        action_list.add_option(Option("Cancel"))
        self._action_keys.append("cancel")

        action_list.focus()

    def _confirm_dismiss(self, character_id: str) -> None:
        """Show dismiss confirmation with gear loss warning."""
        run = self.app.run_state
        if run is None:
            return
        char = run.party.characters.get(character_id)
        if char is None:
            return

        action_list = self.query_one("#action-option-list", OptionList)
        action_list.clear_options()
        self._action_keys = []

        # Build warning text
        equipped = [item_id for item_id in char.equipment.values() if item_id]
        gear_lines: list[str] = []
        for eid in equipped:
            item = self.app.game_data.items.get(eid)
            gear_lines.append(item.name if item else eid)

        if gear_lines:
            warn = f"[bold #cc4444]Dismiss {char.name}? They leave with: {', '.join(gear_lines)}[/bold #cc4444]"
        else:
            warn = f"[bold #cc4444]Dismiss {char.name}? (No equipped gear to lose.)[/bold #cc4444]"

        action_list.add_option(Option(warn))
        self._action_keys.append("")  # non-selectable label

        action_list.add_option(Option(f"[#cc4444]Yes — dismiss {char.name}[/#cc4444]"))
        self._action_keys.append(f"confirm_dismiss:{character_id}")
        action_list.add_option(Option("No — cancel"))
        self._action_keys.append("cancel_dismiss")
        action_list.focus()
        action_list.highlighted = 2  # Default to cancel

    def _handle_action(self, key: str) -> None:
        """Execute an action from the action list."""
        run = self.app.run_state
        if run is None:
            return

        parts = key.split(":")

        mutated = False
        try:
            match parts[0]:
                case "unequip":
                    _, char_id, slot = parts
                    char = run.party.characters.get(char_id)
                    prev = char.equipment.get(slot) if char else None
                    run = self.app.game_loop.unequip_item(run, char_id, slot)
                    run = run.record_macro(
                        "unequip",
                        {
                            "character_id": char_id,
                            "slot": slot,
                            "item_id": prev,
                        },
                    )
                    self.app.run_state = run
                    mutated = True
                case "equip":
                    _, char_id, item_id, slot = parts
                    char = run.party.characters.get(char_id)
                    prev = char.equipment.get(slot) if char else None
                    run = self.app.game_loop.equip_item(run, char_id, item_id, slot)
                    run = run.record_macro(
                        "equip",
                        {
                            "character_id": char_id,
                            "slot": slot,
                            "item_id": item_id,
                            "displaced_item_id": prev,
                        },
                    )
                    self.app.run_state = run
                    mutated = True
                case "swap":
                    _, active_id, reserve_id = parts
                    run = self.app.game_loop.swap_party_member(run, active_id, reserve_id)
                    run = run.record_macro(
                        "swap_party_member",
                        {"active_id": active_id, "reserve_id": reserve_id},
                    )
                    self.app.run_state = run
                    mutated = True
                case "promote":
                    _, char_id = parts
                    run = self.app.game_loop.promote_to_active(run, char_id)
                    run = run.record_macro(
                        "promote_to_active", {"character_id": char_id},
                    )
                    self.app.run_state = run
                    mutated = True
                case "bench":
                    _, char_id = parts
                    run = self.app.game_loop.bench_to_reserve(run, char_id)
                    run = run.record_macro(
                        "bench_to_reserve", {"character_id": char_id},
                    )
                    self.app.run_state = run
                    mutated = True
                case "mimic":
                    _, job_id = parts
                    mc = next(
                        (c for c in run.party.characters.values() if c.is_mc),
                        None,
                    )
                    old_job = mc.job_id if mc else None
                    run = self.app.game_loop.mc_swap_job(run, job_id)
                    run = run.record_macro(
                        "mc_swap_job",
                        {"old_job_id": old_job, "new_job_id": job_id},
                    )
                    self.app.run_state = run
                    mutated = True
                case "dismiss":
                    _, char_id = parts
                    self._confirm_dismiss(char_id)
                    return  # Don't refresh yet — show confirmation
                case "confirm_dismiss":
                    _, char_id = parts
                    char = run.party.characters.get(char_id)
                    info: dict[str, object] = {"character_id": char_id}
                    if char is not None:
                        info.update({
                            "job_id": char.job_id,
                            "level": char.level,
                            "name": char.name,
                        })
                    run = self.app.game_loop.dismiss_character(run, char_id)
                    run = run.record_macro("party_dismiss", info)
                    self.app.run_state = run
                    mutated = True
                case "cancel_dismiss" | "cancel":
                    pass
        except ValueError:
            pass

        if mutated:
            self.app.persist_run()

        # Refresh after action
        self._populate_char_list()
        self.query_one("#action-option-list", OptionList).clear_options()
        self._action_keys = []
        self.query_one("#action-prompt", Label).update("")
        self.query_one("#char-option-list", OptionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
