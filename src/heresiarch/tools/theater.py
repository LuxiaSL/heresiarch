"""Theater mode: a multi-panel DVR wall replaying recorded runs.

Reads finished runs from the analytics record DB (see
``heresiarch.analytics.record_db``) and plays them back side by side at
watchable pace — HP bars draining per hit, combat log scrolling, town
trips and loot picks flickering between fights, dead runs tombstoning
in place. Playback pacing reuses the TUI's own per-event delays.

Feed it records from either source:

    uv run heresiarch                                   # TUI autosaves record
    uv run python -m heresiarch.tools.sim run ... --record-db artifacts/run_records.db

Then watch:

    uv run python -m heresiarch.tools.theater                     # latest 4 runs
    uv run python -m heresiarch.tools.theater --limit 9 --cols 3  # 3x3 wall
    uv run python -m heresiarch.tools.theater --job einherjar --loop
    uv run python -m heresiarch.tools.theater --list              # what's in the DB

Controls: [space] pause · [+/-] speed · [r] restart · [q] quit.

Read-only and failure-proof: malformed records degrade to a panel-level
notice, never a crash.
"""

from __future__ import annotations

import argparse
import json
import select
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.columns import Columns
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from heresiarch.analytics.record_db import RecordDB
from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.models.battle_record import EncounterRecord
from heresiarch.engine.models.combat_state import CombatEvent, CombatEventType
from heresiarch.views.event_renderer import get_event_delay, render_event

TICK_S = 0.1
LOG_LINES = 7
PARTY_ROWS = 3  # HP-bar slots for the party (overflow collapses to "+k more")
ENEMY_ROWS = 4  # HP-bar slots for enemies
ROTATE_LINGER_S = 6.0  # how long a finished panel lingers before backfill
POOL_FACTOR = 8  # backfill pool: how many × limit runs to consider
MAX_STEPS_PER_TICK = 400
MACRO_DELAY_MS = 450
BANNER_DELAY_MS = 700
LOOP_PAUSE_S = 3.0

# Event types whose ``value`` is damage applied to ``target_id``.
_DAMAGE_EVENTS = {
    CombatEventType.DAMAGE_DEALT,
    CombatEventType.RETALIATE_TRIGGERED,
    CombatEventType.THORNS_TRIGGERED,
    CombatEventType.DOT_TICK,
}


# ---------------------------------------------------------------------------
# Timeline: a run flattened into playback steps
# ---------------------------------------------------------------------------


@dataclass
class Step:
    """One playback step — deltas only, applied in order."""

    delay_ms: int = 0
    line: str | None = None  # rich markup for the scrolling log
    hp: dict[str, tuple[int, int]] | None = None  # id -> (hp, max_hp)
    roster_players: list[tuple[str, str]] | None = None  # (id, name)
    roster_enemies: list[tuple[str, str]] | None = None
    clear_enemies: bool = False
    zone: str | None = None
    enc: int | None = None
    level: int | None = None
    gold: int | None = None
    status: str | None = None  # panel subtitle override ("in town", "☠ ...")
    final: str | None = None  # terminal state: "dead" | "alive"


def _item_name(game_data: GameData, item_id: str) -> str:
    item = game_data.items.get(item_id)
    return item.name if item is not None else item_id


def _enemy_display_names(
    enemy_ids: list[str], game_data: GameData,
) -> dict[str, str]:
    """Mirror the TUI's naming: template name + letter when >1 enemy."""
    names: dict[str, str] = {}
    for i, eid in enumerate(enemy_ids):
        template_id = eid.rsplit("_", 1)[0] if "_" in eid else eid
        template = game_data.enemies.get(template_id)
        base = template.name if template is not None else template_id
        names[eid] = f"{base} {chr(65 + i)}" if len(enemy_ids) > 1 else base
    return names


def _net_damage_in_round(
    events: list[CombatEvent],
) -> dict[str, int]:
    """Net HP lost per combatant across a round's events (heals negative)."""
    net: dict[str, int] = {}
    for ev in events:
        if ev.event_type in _DAMAGE_EVENTS and ev.target_id:
            net[ev.target_id] = net.get(ev.target_id, 0) + ev.value
        elif ev.event_type == CombatEventType.HEALING and ev.target_id:
            net[ev.target_id] = net.get(ev.target_id, 0) - ev.value
    return net


def _macro_line(evt: dict[str, Any], game_data: GameData) -> str | None:
    """Render a macro event as a short flavor line (None = silent)."""
    p = evt.get("payload", {}) or {}
    kind = evt.get("event_type", "")
    try:
        match kind:
            case "run_start":
                return "[bold]▶ the run begins[/bold]"
            case "enter_zone":
                return f"[cyan]→ enters {p.get('zone_id', '?')}[/cyan]"
            case "leave_zone":
                reason = p.get("reason", "")
                tag = " (retreat)" if "retreat" in str(reason) else ""
                return f"[cyan]← leaves {p.get('zone_id', '?')}{tag}[/cyan]"
            case "enter_town":
                return f"[magenta]⌂ enters {p.get('town_id', 'town')}[/magenta]"
            case "leave_town":
                return "[magenta]⌂ back to the wilds[/magenta]"
            case "shop_buy":
                name = _item_name(game_data, str(p.get("item_id", "?")))
                return f"[yellow]$ buys {name} (-{p.get('price', '?')}g)[/yellow]"
            case "shop_sell":
                name = _item_name(game_data, str(p.get("item_id", "?")))
                return f"[yellow]$ sells {name} (+{p.get('price', '?')}g)[/yellow]"
            case "pick_loot":
                picked = [
                    x.get("item_id", "?") if isinstance(x, dict) else str(x)
                    for x in (p.get("selected") or [])
                ]
                money = p.get("money_gained", 0)
                if not picked and not money:
                    return None
                parts = [", ".join(_item_name(game_data, i) for i in picked)]
                if money:
                    parts.append(f"+{money}g")
                return f"[green]✦ loot: {' '.join(x for x in parts if x)}[/green]"
            case "equip":
                name = _item_name(game_data, str(p.get("item_id", "?")))
                return f"[blue]⚙ equips {name}[/blue]"
            case "use_consumable":
                name = _item_name(game_data, str(p.get("item_id", "?")))
                if "hp_before" in p and "hp_after" in p:
                    return (
                        f"[green]✚ {name} "
                        f"({p['hp_before']}→{p['hp_after']})[/green]"
                    )
                return f"[green]✚ uses {name}[/green]"
            case "use_teach_scroll":
                name = _item_name(game_data, str(p.get("item_id", "?")))
                return f"[blue]✎ learns from {name}[/blue]"
            case "recruit_accept":
                who = p.get("name") or p.get("job_id") or "a recruit"
                return f"[bold green]☺ recruits {who}[/bold green]"
            case "recruit_dismiss" | "dismiss":
                return "[dim]☹ dismisses a party member[/dim]"
            case "rest_at_lodge" | "lodge_rest":
                return f"[magenta]☾ rests at the lodge (-{p.get('cost', '?')}g)[/magenta]"
            case _:
                return f"[dim]· {kind}[/dim]"
    except Exception:
        return f"[dim]· {kind}[/dim]"


def _macro_step(evt: dict[str, Any], game_data: GameData) -> Step:
    line = _macro_line(evt, game_data)
    hp: dict[str, tuple[int, int]] | None = None
    p = evt.get("payload", {}) or {}
    # Consumables carry authoritative hp_after/max_hp — use them.
    if evt.get("event_type") == "use_consumable":
        target = p.get("target_character_id")
        if target and "hp_after" in p and "max_hp" in p:
            try:
                hp = {str(target): (int(p["hp_after"]), int(p["max_hp"]))}
            except (TypeError, ValueError):
                hp = None
    status = None
    if evt.get("in_town"):
        status = "⌂ in town"
    elif evt.get("event_type") in ("leave_town", "leave_zone"):
        status = ""
    return Step(
        delay_ms=MACRO_DELAY_MS if line else 0,
        line=line,
        hp=hp,
        zone=evt.get("zone_id") or None,
        level=int(evt["mc_level"]) if evt.get("mc_level") else None,
        gold=int(evt["party_gold"]) if evt.get("party_gold") is not None else None,
        status=status,
    )


def _encounter_steps(
    enc: EncounterRecord,
    enc_idx: int,
    player_names: dict[str, str],
    ability_names: dict[str, str],
    game_data: GameData,
    peaks: dict[str, int],
) -> list[Step]:
    """Flatten one encounter into playback steps."""
    steps: list[Step] = []
    if not enc.rounds:
        steps.append(Step(
            delay_ms=BANNER_DELAY_MS,
            line=f"[dim]⚔ {', '.join(enc.enemy_template_ids)} — no rounds recorded[/dim]",
            zone=enc.zone_id,
            enc=enc_idx,
        ))
        return steps

    first_round = enc.rounds[0]
    player_ids = list(first_round.player_hp.keys())
    enemy_ids = list(first_round.enemy_hp.keys())
    enemy_names = _enemy_display_names(enemy_ids, game_data)
    names = {pid: player_names.get(pid, pid) for pid in player_ids}
    names.update(enemy_names)

    # Round snapshots are end-of-round; recover start-of-combat HP by
    # adding back the net damage dealt during round 1.
    net_r1 = _net_damage_in_round(first_round.events)
    cur: dict[str, int] = {}
    maxes: dict[str, int] = {}
    initial_hp: dict[str, tuple[int, int]] = {}
    for cid in player_ids + enemy_ids:
        snap = (
            first_round.player_hp.get(cid)
            if cid in first_round.player_hp
            else first_round.enemy_hp.get(cid, 0)
        )
        start = max(0, (snap or 0) + net_r1.get(cid, 0))
        cur[cid] = start
        if cid in player_ids:
            peaks[cid] = max(peaks.get(cid, 0), start)
            maxes[cid] = peaks[cid]
        else:
            maxes[cid] = max(start, 1)
        initial_hp[cid] = (start, maxes[cid])

    versus = ", ".join(enemy_names[eid] for eid in enemy_ids)
    steps.append(Step(
        delay_ms=BANNER_DELAY_MS,
        line=f"[bold]⚔ {versus}[/bold]",
        roster_players=[(pid, names[pid]) for pid in player_ids],
        roster_enemies=[(eid, enemy_names[eid]) for eid in enemy_ids],
        hp=initial_hp,
        zone=enc.zone_id,
        enc=enc_idx,
        status="",
    ))

    for rnd in enc.rounds:
        for ev in rnd.events:
            if ev.event_type == CombatEventType.COMBAT_END:
                continue  # we add our own result banner
            hp_delta: dict[str, tuple[int, int]] | None = None
            if ev.event_type in _DAMAGE_EVENTS and ev.target_id:
                cur[ev.target_id] = max(0, cur.get(ev.target_id, 0) - ev.value)
                hp_delta = {ev.target_id: (cur[ev.target_id], maxes.get(ev.target_id, 1))}
            elif ev.event_type == CombatEventType.HEALING and ev.target_id:
                peak = maxes.get(ev.target_id, 0)
                cur[ev.target_id] = cur.get(ev.target_id, 0) + ev.value
                if ev.target_id in peaks:
                    peaks[ev.target_id] = max(peaks[ev.target_id], cur[ev.target_id])
                    maxes[ev.target_id] = peaks[ev.target_id]
                else:
                    maxes[ev.target_id] = max(peak, cur[ev.target_id])
                hp_delta = {ev.target_id: (cur[ev.target_id], maxes[ev.target_id])}
            elif ev.event_type == CombatEventType.DEATH:
                dead_id = ev.target_id or ev.actor_id
                if dead_id:
                    cur[dead_id] = 0
                    hp_delta = {dead_id: (0, maxes.get(dead_id, 1))}

            try:
                rendered = render_event(ev, names, ability_names, verbose=True)
                line = rendered.text if (
                    rendered.is_significant
                    or ev.event_type == CombatEventType.ROUND_START
                ) else None
            except Exception:
                line = None
            steps.append(Step(
                delay_ms=get_event_delay(ev),
                line=line,
                hp=hp_delta,
            ))

        # Resync to the round's authoritative snapshot; enemies missing
        # from it are gone (dead/split-consumed), new ids are splits.
        resync: dict[str, tuple[int, int]] = {}
        roster_add: list[tuple[str, str]] = []
        for pid, hp_val in rnd.player_hp.items():
            if pid in peaks:
                peaks[pid] = max(peaks[pid], hp_val)
                maxes[pid] = peaks[pid]
            if cur.get(pid) != hp_val:
                resync[pid] = (hp_val, maxes.get(pid, max(hp_val, 1)))
            cur[pid] = hp_val
        seen_enemies = set(rnd.enemy_hp.keys())
        for eid, hp_val in rnd.enemy_hp.items():
            if eid not in maxes:  # split-spawned mid-fight
                maxes[eid] = max(hp_val, 1)
                template_id = eid.rsplit("_", 1)[0] if "_" in eid else eid
                template = game_data.enemies.get(template_id)
                names[eid] = template.name if template else template_id
                roster_add.append((eid, names[eid]))
            if cur.get(eid) != hp_val:
                resync[eid] = (hp_val, maxes[eid])
            cur[eid] = hp_val
        for eid in enemy_ids:
            if eid not in seen_enemies and cur.get(eid, 0) > 0:
                cur[eid] = 0
                resync[eid] = (0, maxes.get(eid, 1))
        enemy_ids = list(rnd.enemy_hp.keys())
        if resync or roster_add:
            steps.append(Step(
                hp=resync or None,
                roster_enemies=roster_add or None,
            ))

    if enc.was_victory:
        steps.append(Step(
            delay_ms=BANNER_DELAY_MS,
            line=f"[green]✓ victory ({enc.rounds_taken} rounds)[/green]",
            clear_enemies=True,
        ))
    else:
        steps.append(Step(
            delay_ms=BANNER_DELAY_MS,
            line="[bold red]✗ DEFEATED[/bold red]",
        ))
    return steps


def build_timeline(
    run_row: dict[str, Any],
    encounters: list[EncounterRecord],
    macro_events: list[dict[str, Any]],
    game_data: GameData,
    *,
    live: bool = False,
) -> list[Step]:
    """Flatten a full recorded run into an ordered list of Steps.

    ``live=True`` builds a *prefix* timeline for a run still being
    recorded: macro events that trail the last known encounter and the
    final outcome banner are held back, so a later rebuild with more
    encounters strictly extends the previous step list (cursor-safe).
    """
    player_names: dict[str, str] = {}
    try:
        run_state = json.loads(run_row.get("run_state_json") or "{}")
        for cid, char in (run_state.get("party", {}).get("characters", {}) or {}).items():
            player_names[cid] = char.get("name", cid)
    except (json.JSONDecodeError, AttributeError):
        pass
    ability_names = {aid: ab.name for aid, ab in game_data.abilities.items()}

    # Macro events keyed by how many encounters existed when they fired —
    # they interleave *between* encounter k-1 and k.
    macro_by_seq: dict[int, list[dict[str, Any]]] = {}
    for evt in macro_events:
        macro_by_seq.setdefault(int(evt.get("encounter_seq_at_time", 0)), []).append(evt)

    steps: list[Step] = []
    peaks: dict[str, int] = {}
    for enc_idx, enc in enumerate(encounters):
        for evt in macro_by_seq.pop(enc_idx, []):
            steps.append(_macro_step(evt, game_data))
        try:
            steps.extend(_encounter_steps(
                enc, enc_idx, player_names, ability_names, game_data, peaks,
            ))
        except Exception:
            steps.append(Step(
                delay_ms=BANNER_DELAY_MS,
                line=f"[dim red]⚠ unplayable encounter record #{enc_idx}[/dim red]",
            ))
    if live:
        # Hold back trailing macros + outcome banner: they'll be
        # emitted once the run finishes (or more encounters land).
        return steps

    # Trailing macro events (after the last recorded encounter).
    for seq in sorted(macro_by_seq):
        for evt in macro_by_seq[seq]:
            steps.append(_macro_step(evt, game_data))

    outcome = str(run_row.get("outcome", ""))
    if outcome == "dead":
        killer_ids = [k for k in str(run_row.get("killed_by") or "").split(",") if k]
        killer_names: list[str] = []
        for kid in killer_ids:
            template = game_data.enemies.get(kid)
            name = template.name if template is not None else kid
            if name not in killer_names:
                killer_names.append(name)
        killer = ", ".join(killer_names) or "?"
        where = run_row.get("killed_at_zone") or "?"
        steps.append(Step(
            delay_ms=BANNER_DELAY_MS,
            line=f"[bold red]☠ slain by {killer} in {where}[/bold red]",
            status=f"☠ DEAD — {where}",
            final="dead",
        ))
    else:
        steps.append(Step(
            delay_ms=BANNER_DELAY_MS,
            line=f"[bold green]★ run ends: {outcome}[/bold green]",
            status=f"★ {outcome.upper()}",
            final="alive",
        ))
    return steps


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------


@dataclass
class PanelPlayer:
    """Owns one run's timeline and its live display state."""

    title: str
    steps: list[Step]
    run_id: str = ""
    sig: tuple = ()  # (rounds_total, encounters_cleared, outcome) change detector
    live: bool = False  # run is still being recorded (follow mode)
    stale: bool = False  # in_progress but no recent DB updates
    finished_at: float | None = None  # monotonic ts when playback completed
    cursor: int = 0
    budget_ms: float = 0.0
    zone: str = ""
    enc: int = 0
    level: int = 0
    gold: int = 0
    status: str = ""
    final: str | None = None
    players: dict[str, tuple[str, int, int]] = field(default_factory=dict)
    enemies: dict[str, tuple[str, int, int]] = field(default_factory=dict)
    log: deque[Text] = field(default_factory=lambda: deque(maxlen=LOG_LINES))

    @property
    def done(self) -> bool:
        return self.cursor >= len(self.steps)

    def reset(self) -> None:
        self.cursor = 0
        self.budget_ms = 0.0
        self.finished_at = None
        self.zone, self.enc, self.level, self.gold = "", 0, 0, 0
        self.status, self.final = "", None
        self.players.clear()
        self.enemies.clear()
        self.log.clear()

    def advance(self, dt_ms: float) -> None:
        if self.done:
            return
        self.budget_ms += dt_ms
        applied = 0
        while not self.done and applied < MAX_STEPS_PER_TICK:
            step = self.steps[self.cursor]
            if self.budget_ms < step.delay_ms:
                break
            self.budget_ms -= step.delay_ms
            self._apply(step)
            self.cursor += 1
            applied += 1
        if self.done:
            self.budget_ms = 0.0

    def _apply(self, step: Step) -> None:
        if step.roster_players is not None:
            self.players = {
                pid: (name, self.players.get(pid, (name, 0, 1))[1],
                      self.players.get(pid, (name, 0, 1))[2])
                for pid, name in step.roster_players
            }
        if step.clear_enemies:
            self.enemies.clear()
        if step.roster_enemies is not None:
            if not step.clear_enemies and step.zone is None and self.enemies:
                # mid-fight roster additions (splits) append
                for eid, name in step.roster_enemies:
                    self.enemies.setdefault(eid, (name, 0, 1))
            else:
                self.enemies = {eid: (name, 0, 1) for eid, name in step.roster_enemies}
        if step.hp is not None:
            for cid, (hp, max_hp) in step.hp.items():
                if cid in self.players:
                    name = self.players[cid][0]
                    self.players[cid] = (name, hp, max(max_hp, 1))
                elif cid in self.enemies:
                    name = self.enemies[cid][0]
                    self.enemies[cid] = (name, hp, max(max_hp, 1))
        if step.line is not None:
            try:
                self.log.append(Text.from_markup(step.line))
            except Exception:
                self.log.append(Text(step.line))
        if step.zone is not None:
            self.zone = step.zone
        if step.enc is not None:
            self.enc = step.enc
        if step.level is not None:
            self.level = step.level
        if step.gold is not None:
            self.gold = step.gold
        if step.status is not None:
            self.status = step.status
        if step.final is not None:
            self.final = step.final


_NAME_W = 15


def _hp_row(name: str, hp: int, max_hp: int, width: int) -> Text:
    """`name ████░░ 45%` — colored by remaining fraction."""
    pct = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0.0
    bar_w = max(4, width - _NAME_W - 8)
    filled = int(round(pct * bar_w))
    color = "green" if pct > 0.6 else "yellow" if pct > 0.3 else "red"
    shown = name if len(name) <= _NAME_W else name[: _NAME_W - 1] + "…"
    row = Text()
    row.append(f"{shown:<{_NAME_W}} ", style="bold" if hp > 0 else "dim")
    if hp <= 0:
        row.append("─" * bar_w, style="grey23")
        row.append("  KO", style="dim red")
    else:
        row.append("█" * filled, style=color)
        row.append("░" * (bar_w - filled), style="grey37")
        row.append(f" {pct:>4.0%}", style=color)
    return row


def _hp_section(
    combatants: dict[str, tuple[str, int, int]],
    slots: int,
    width: int,
) -> list[Text]:
    """Fixed-height block of HP rows; overflow collapses into '+k more'."""
    rows: list[Text] = []
    entries = list(combatants.values())
    if len(entries) > slots:
        shown, extra = entries[: slots - 1], entries[slots - 1 :]
    else:
        shown, extra = entries, []
    for name, hp, max_hp in shown:
        rows.append(_hp_row(name, hp, max_hp, width))
    if extra:
        alive = sum(1 for _, hp, _ in extra if hp > 0)
        rows.append(Text(f"  +{len(extra)} more ({alive} alive)", style="dim"))
    while len(rows) < slots:
        rows.append(Text())
    return rows


def render_panel(pp: PanelPlayer, width: int) -> Panel:
    inner_w = width - 4
    rows: list[RenderableType] = []
    rows.extend(_hp_section(pp.players, PARTY_ROWS, inner_w))
    rows.append(Text("─" * min(inner_w, 16), style="grey23") if pp.enemies else Text())
    rows.extend(_hp_section(pp.enemies, ENEMY_ROWS, inner_w))
    rows.append(Text())
    pad = LOG_LINES - len(pp.log)
    for _ in range(pad):
        rows.append(Text())
    for line in pp.log:
        t = line.copy()
        t.truncate(inner_w, overflow="ellipsis")
        rows.append(t)

    if pp.final == "dead":
        border = "red"
    elif pp.final == "alive":
        border = "green"
    else:
        border = "cyan"
    subtitle = pp.status or (f"{pp.zone} · enc {pp.enc}" if pp.zone else "")
    sub_style = "dim" if not pp.final else border
    if pp.final is None:
        if pp.stale:
            subtitle = f"⏳ {subtitle or 'stale'}"
        elif pp.live:
            subtitle = f"● {subtitle or 'live'}"
            sub_style = "bold red" if pp.done else "red"
    header = f"{pp.title} · lv{pp.level} · {pp.gold}g"
    return Panel(
        Group(*rows),
        title=Text(header, style="bold"),
        subtitle=Text(subtitle, style=sub_style),
        border_style=border if pp.final else "dim cyan",
        width=width,
        padding=(0, 1),
    )


def render_wall(
    panels: list[PanelPlayer],
    console: Console,
    cols: int,
    speed: float,
    paused: bool,
) -> Group:
    width = max(30, (console.size.width - 2) // max(1, cols) - 1)
    rendered = [render_panel(pp, width) for pp in panels]
    finished = sum(1 for pp in panels if pp.done and pp.final is not None)
    n_live = sum(1 for pp in panels if pp.live and not pp.stale and pp.final is None)
    live_part = f" · [red]● {n_live} live[/red]" if n_live else ""
    state = "⏸ PAUSED" if paused else f"▶ ×{speed:g}"
    header = Text.from_markup(
        f"[bold]⚔ THEATER[/bold] — {len(panels)} runs · {finished} finished"
        f"{live_part} · "
        f"{state}   [dim]\\[space] pause · +/- speed · r restart · q quit[/dim]"
    )
    if not panels:
        return Group(header, Text("  … waiting for runs to appear", style="dim"))
    return Group(header, Columns(rendered, padding=(0, 1)))


# ---------------------------------------------------------------------------
# Keyboard (raw, non-blocking, optional)
# ---------------------------------------------------------------------------


class KeyReader:
    """Non-blocking single-key reader; inert when stdin isn't a TTY."""

    def __init__(self) -> None:
        self._enabled = False
        self._saved: Any = None

    def __enter__(self) -> KeyReader:
        try:
            import termios
            import tty

            if sys.stdin.isatty():
                self._saved = termios.tcgetattr(sys.stdin.fileno())
                tty.setcbreak(sys.stdin.fileno())
                self._enabled = True
        except Exception:
            self._enabled = False
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._enabled and self._saved is not None:
            try:
                import termios

                termios.tcsetattr(
                    sys.stdin.fileno(), termios.TCSADRAIN, self._saved,
                )
            except Exception:
                pass

    def read(self) -> str | None:
        if not self._enabled:
            return None
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            if ready:
                return sys.stdin.read(1)
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Run selection + CLI
# ---------------------------------------------------------------------------


def select_runs(db: RecordDB, args: argparse.Namespace) -> list[dict[str, Any]]:
    sql = """
        SELECT run_id, source, mc_job_id, mc_name, seed, outcome,
               killed_by, killed_at_zone, encounters_cleared, rounds_total,
               zones_cleared, recorded_at, run_state_json
        FROM runs WHERE 1=1
    """
    params: list[Any] = []
    if args.run_ids:
        placeholders = ",".join("?" for _ in args.run_ids)
        sql += f" AND run_id IN ({placeholders})"
        params.extend(args.run_ids)
    if args.job:
        sql += " AND mc_job_id = ?"
        params.append(args.job)
    if args.source:
        sql += " AND source = ?"
        params.append(args.source)
    sql += " ORDER BY recorded_at DESC LIMIT ?"
    params.append(args.limit)
    cur = db.conn.execute(sql, tuple(params))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _make_title(row: dict[str, Any]) -> str:
    seed = row.get("seed")
    tag = f" s{seed}" if seed is not None else ""
    return f"{row['mc_job_id']}{tag} · {str(row['run_id'])[-8:]}"


def _row_sig(row: dict[str, Any]) -> tuple:
    return (
        row.get("rounds_total"),
        row.get("encounters_cleared"),
        row.get("outcome"),
    )


def _is_stale(row: dict[str, Any], stale_after_s: float) -> bool:
    """An in_progress run with no recent upserts (killed/abandoned)."""
    if str(row.get("outcome")) != "in_progress":
        return False
    try:
        from datetime import datetime, timezone

        rec = datetime.fromisoformat(str(row.get("recorded_at")))
        if rec.tzinfo is None:
            rec = rec.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - rec).total_seconds()
        return age > stale_after_s
    except (ValueError, TypeError):
        return True


def _build_panel_steps(
    db: RecordDB,
    row: dict[str, Any],
    game_data: GameData,
    *,
    live: bool,
) -> list[Step]:
    run_id = str(row["run_id"])
    encounters = load_run_encounters(db, run_id)
    macro = db.macro_events_for_run(run_id)
    return build_timeline(row, encounters, macro, game_data, live=live)


def _make_panel(
    db: RecordDB, row: dict[str, Any], game_data: GameData,
) -> PanelPlayer | None:
    run_id = str(row["run_id"])
    live = str(row.get("outcome")) == "in_progress"
    try:
        steps = _build_panel_steps(db, row, game_data, live=live)
    except Exception:
        return None
    return PanelPlayer(
        title=_make_title(row), steps=steps, run_id=run_id,
        sig=_row_sig(row), live=live,
    )


def refresh_follow(
    db: RecordDB,
    args: argparse.Namespace,
    game_data: GameData,
    panels: list[PanelPlayer],
    watched: dict[str, float] | None = None,
) -> list[PanelPlayer]:
    """Poll the DB: extend changed runs, attach new ones, backfill idle.

    Live timelines are strict prefixes of their later rebuilds (see
    build_timeline), so replacing a panel's step list preserves its
    cursor position.

    ``watched`` (run_id → monotonic ts of last full playback) drives the
    backfill: a finished panel that has lingered ROTATE_LINGER_S gets
    replaced with the newest run the wall hasn't shown yet — and, once
    everything has been seen, with the least-recently-watched replay —
    so the aquarium never goes dark between recording bursts.
    """
    try:
        rows = select_runs(db, args)
    except Exception:
        return panels  # transient DB hiccup — keep playing what we have
    by_id = {pp.run_id: pp for pp in panels}
    for row in rows:
        run_id = str(row["run_id"])
        sig = _row_sig(row)
        stale = _is_stale(row, args.stale_after)
        live = str(row.get("outcome")) == "in_progress"
        pp = by_id.get(run_id)
        if pp is not None:
            pp.stale = stale
            if pp.sig == sig:
                continue
            try:
                steps = _build_panel_steps(db, row, game_data, live=live)
            except Exception:
                continue
            if len(steps) < pp.cursor:
                pp.reset()  # record shrank (shouldn't happen) — replay
            pp.steps = steps
            pp.sig = sig
            pp.live = live
            pp.finished_at = None
            continue
        # New run — attach if there's room or a finished panel to bump.
        # Finished runs the wall already played go through the backfill
        # queue instead (unwatched-first, then LRU replays).
        if watched is not None and not live and run_id in watched:
            continue
        new_pp = _make_panel(db, row, game_data)
        if new_pp is None:
            continue
        new_pp.stale = stale
        if len(panels) < args.limit:
            panels.append(new_pp)
            by_id[run_id] = new_pp
        else:
            for i, old in enumerate(panels):
                if old.done and not (old.live and not old.stale):
                    by_id.pop(old.run_id, None)
                    panels[i] = new_pp
                    by_id[run_id] = new_pp
                    break

    if watched is None:
        return panels

    # ---- Backfill: keep the wall full and moving -----------------------
    now = time.monotonic()
    linger = getattr(args, "rotate_linger", ROTATE_LINGER_S)
    for pp in panels:
        if pp.done and pp.final is not None:
            if pp.finished_at is None:
                pp.finished_at = now
            watched[pp.run_id] = watched.get(pp.run_id) or now
    idle = [
        i for i, pp in enumerate(panels)
        if pp.done and pp.final is not None
        and pp.finished_at is not None
        and now - pp.finished_at >= linger
    ]
    room = args.limit - len(panels)
    if not idle and room <= 0:
        return panels

    try:
        pool = select_runs(db, argparse.Namespace(
            run_ids=args.run_ids, job=args.job, source=args.source,
            limit=max(args.limit * POOL_FACTOR, 40),
        ))
    except Exception:
        return panels
    on_wall = {pp.run_id for pp in panels}
    fresh = [
        r for r in pool
        if str(r["run_id"]) not in watched and str(r["run_id"]) not in on_wall
    ]
    queue = list(fresh)
    if not getattr(args, "no_rotate", False):
        replays = sorted(
            (r for r in pool
             if str(r["run_id"]) in watched
             and str(r["run_id"]) not in on_wall),
            key=lambda r: watched[str(r["run_id"])],
        )
        queue += replays
    while room > 0 and queue:
        new_pp = _make_panel(db, queue.pop(0), game_data)
        if new_pp is not None:
            panels.append(new_pp)
            on_wall.add(new_pp.run_id)
            room -= 1
    for i in idle:
        if not queue:
            break
        new_pp = _make_panel(db, queue.pop(0), game_data)
        if new_pp is not None:
            watched[panels[i].run_id] = now
            panels[i] = new_pp
            on_wall.add(new_pp.run_id)
    return panels


def load_run_encounters(db: RecordDB, run_id: str) -> list[EncounterRecord]:
    cur = db.conn.execute(
        "SELECT encounter_json FROM encounters WHERE run_id = ? ORDER BY encounter_seq",
        (run_id,),
    )
    out: list[EncounterRecord] = []
    for (blob,) in cur.fetchall():
        try:
            out.append(EncounterRecord.model_validate_json(blob))
        except Exception:
            continue
    return out


def list_runs(db: RecordDB, console: Console) -> None:
    from rich.table import Table

    cur = db.conn.execute(
        """
        SELECT run_id, source, mc_job_id, outcome, zones_cleared,
               encounters_cleared, rounds_total, recorded_at
        FROM runs ORDER BY recorded_at DESC
        """
    )
    table = Table(title=f"{db.path} — {db.count_runs()} runs")
    for col in ("run_id", "source", "job", "outcome", "zones", "encs", "rounds", "recorded"):
        table.add_column(col)
    for row in cur.fetchall():
        run_id, source, job, outcome, zones, encs, rounds, ts = row
        try:
            zone_count = str(len(json.loads(zones)))
        except (json.JSONDecodeError, TypeError):
            zone_count = "?"
        table.add_row(
            run_id, source, job, outcome, zone_count,
            str(encs), str(rounds), str(ts)[:16],
        )
    console.print(table)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Theater mode: replay recorded runs as a multi-panel wall",
    )
    ap.add_argument("--db", default="artifacts/run_records.db",
                    help="Path to the record DB (default: artifacts/run_records.db)")
    ap.add_argument("--data", default="data", help="Game data dir (for names)")
    ap.add_argument("--run-ids", nargs="*", default=None,
                    help="Explicit run_ids to play")
    ap.add_argument("--job", default=None, help="Filter runs by MC job")
    ap.add_argument("--source", default=None, help="Filter by source: sim | tui")
    ap.add_argument("--limit", type=int, default=4,
                    help="How many runs to put on the wall (default 4)")
    ap.add_argument("--cols", type=int, default=2, help="Grid columns (default 2)")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="Playback speed multiplier (default 1.0)")
    ap.add_argument("--loop", action="store_true",
                    help="Restart the wall when every run finishes")
    ap.add_argument("--follow", action="store_true",
                    help="Tail the DB: attach to in-flight runs (live "
                         "recording via --record-every / policy_opt "
                         "--record-db) and extend as they grow")
    ap.add_argument("--poll", type=float, default=2.0,
                    help="Follow mode: DB poll interval in seconds")
    ap.add_argument("--stale-after", type=float, default=240.0,
                    help="Follow mode: mark an in_progress run stale after "
                         "this many seconds without DB updates")
    ap.add_argument("--no-rotate", action="store_true",
                    help="Follow mode: don't cycle already-watched replays "
                         "while waiting for fresh runs (fresh runs still "
                         "attach; the wall may go idle)")
    ap.add_argument("--list", action="store_true", dest="list_runs",
                    help="List recorded runs and exit")
    args = ap.parse_args()

    console = Console()
    db_path = Path(args.db)
    if not db_path.exists():
        if args.follow:
            console.print(f"[dim]Waiting for {db_path} to appear…[/dim]")
            while not db_path.exists():
                time.sleep(1.0)
        else:
            console.print(f"[red]No record DB at {db_path}[/red] — "
                          "record runs first (TUI autosaves, or sim run --record-db).")
            raise SystemExit(1)

    db = RecordDB(db_path)
    try:
        if args.list_runs:
            list_runs(db, console)
            return

        game_data = load_all(Path(args.data))
        panels: list[PanelPlayer] = []
        watched: dict[str, float] = {}
        if args.follow:
            panels = refresh_follow(db, args, game_data, panels, watched)
        else:
            rows = select_runs(db, args)
            if not rows:
                console.print("[yellow]No matching runs in the DB.[/yellow] "
                              "Try --list to see what's recorded.")
                raise SystemExit(1)
            console.print(f"[dim]Loading {len(rows)} runs…[/dim]")
            for row in rows:
                steps = _build_panel_steps(db, row, game_data, live=False)
                panels.append(PanelPlayer(
                    title=_make_title(row), steps=steps,
                    run_id=str(row["run_id"]), sig=_row_sig(row),
                ))

        speed = max(0.1, args.speed)
        paused = False
        with KeyReader() as keys:
            with Live(
                render_wall(panels, console, args.cols, speed, paused),
                console=console,
                refresh_per_second=10,
                screen=True,
            ) as live:
                last = time.monotonic()
                last_poll = time.monotonic()
                all_done_at: float | None = None
                try:
                    while True:
                        key = keys.read()
                        if key in ("q", "Q", "\x03"):
                            break
                        elif key == " ":
                            paused = not paused
                        elif key in ("+", "="):
                            speed = min(64.0, speed * 2)
                        elif key in ("-", "_"):
                            speed = max(0.25, speed / 2)
                        elif key in ("r", "R"):
                            for pp in panels:
                                pp.reset()
                            all_done_at = None

                        now = time.monotonic()
                        dt = now - last
                        last = now
                        if not paused:
                            for pp in panels:
                                pp.advance(dt * 1000.0 * speed)

                        if args.follow and now - last_poll >= args.poll:
                            last_poll = now
                            panels = refresh_follow(
                                db, args, game_data, panels, watched,
                            )

                        if (
                            args.loop
                            and not args.follow
                            and panels
                            and all(pp.done for pp in panels)
                        ):
                            if all_done_at is None:
                                all_done_at = now
                            elif now - all_done_at > LOOP_PAUSE_S:
                                for pp in panels:
                                    pp.reset()
                                all_done_at = None
                        live.update(render_wall(
                            panels, console, args.cols, speed, paused,
                        ))
                        time.sleep(TICK_S)
                except KeyboardInterrupt:
                    pass
    finally:
        db.close()


if __name__ == "__main__":
    main()
