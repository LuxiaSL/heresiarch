"""Render a holistic play-by-play timeline for a single TUI run.

Interleaves macro events with encounter rounds into one chronological
markdown document for pattern-mining analysis.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from heresiarch.analytics.record_db import RecordDB


# Default target — can be overridden via CLI args.
DEFAULT_RUN_ID = "run_d9f92b01"
DEFAULT_OUT = Path("artifacts/trace_run_d9f92b01.md")
DEFAULT_DB = Path("artifacts/run_records.db")


def pct(n: float) -> str:
    return f"{round(n * 100)}%"


def render_macro(evt: dict[str, Any]) -> str:
    """One-line (or multi-line) macro event entry."""
    header = (
        f"### [seq={evt['seq']} {evt['event_type']}]"
        f"{' ' + evt['zone_id'] if evt['zone_id'] else ''}"
        f"{' (in ' + evt['town_id'] + ')' if evt.get('in_town') else ''}"
    )
    ctx = (
        f"_L{evt['mc_level']} · HP {pct(evt['mc_hp_pct'])} · "
        f"{evt['party_gold']}g · stash {evt['stash_used']}/"
        f"{evt['stash_used'] + evt['stash_free']} · enc_at_time={evt['encounter_seq_at_time']}_"
    )
    payload = evt.get("payload", {})
    payload_lines = _summarize_payload(evt["event_type"], payload)
    lines = [header, ctx, *payload_lines]
    return "\n".join(lines)


def _summarize_payload(event_type: str, p: dict[str, Any]) -> list[str]:
    """Event-type-specific payload rendering."""
    out: list[str] = []
    if event_type == "run_start":
        out.append(f"- start: {p.get('mc_name')} ({p.get('mc_job_id')})")
    elif event_type == "enter_zone":
        out.append(
            f"- enter {p.get('zone_id')} "
            f"(already_cleared={p.get('already_cleared')}, via={p.get('via')})"
        )
    elif event_type == "leave_zone":
        line = (
            f"- leave {p.get('zone_id')}: reason={p.get('reason')}, "
            f"enc_idx={p.get('current_encounter_index')}, "
            f"overstay={p.get('overstay_battles')}, "
            f"cleared={p.get('zone_cleared')}"
        )
        if p.get("next_zone_id"):
            line += f" → next={p['next_zone_id']}"
        out.append(line)
    elif event_type == "enter_town":
        out.append(f"- enter town {p.get('town_id')}")
    elif event_type == "leave_town":
        out.append(f"- leave town {p.get('town_id')}")
    elif event_type == "shop_buy":
        offered = p.get("offered", [])
        offered_str = ", ".join(
            f"{o.get('item_id')}@{o.get('price')}g" for o in offered
        )
        out.append(
            f"- **BOUGHT** {p.get('item_id')} @ {p.get('price')}g "
            f"(to {p.get('destination', '?')})"
        )
        out.append(f"- offered: [{offered_str}]")
    elif event_type == "shop_sell":
        offered = p.get("offered", [])
        offered_str = ", ".join(
            f"{o.get('item_id')}@{o.get('price')}g" for o in offered
        )
        out.append(f"- **SOLD** {p.get('item_id')} @ {p.get('price')}g")
        out.append(f"- offered: [{offered_str}]")
    elif event_type == "pick_loot":
        offered = p.get("offered", [])
        selected = p.get("selected", [])
        skipped = p.get("skipped", [])
        discarded = p.get("discarded_from_stash", [])
        out.append(
            f"- money +{p.get('money_gained')}g, "
            f"offered={offered}, **selected**={selected}, "
            f"skipped={skipped}, discarded_stash={discarded}"
        )
    elif event_type == "equip":
        out.append(
            f"- equip {p.get('item_id')} → {p.get('character_id')}:{p.get('slot')} "
            f"(displaced={p.get('displaced_item_id')})"
        )
    elif event_type == "unequip":
        out.append(
            f"- unequip {p.get('item_id')} from "
            f"{p.get('character_id')}:{p.get('slot')}"
        )
    elif event_type == "use_consumable":
        in_combat = " [IN-COMBAT]" if p.get("in_combat") else ""
        out.append(
            f"- use {p.get('item_id')} on {p.get('target_character_id', '?')} "
            f"(HP {p.get('hp_before', '?')}→{p.get('hp_after', '?')}"
            f"/{p.get('max_hp', '?')}){in_combat}"
        )
    elif event_type == "use_teach_scroll":
        out.append(
            f"- teach {p.get('teaches_ability_id')} from {p.get('item_id')} "
            f"to {p.get('target_character_id')}"
        )
    elif event_type == "lodge_rest":
        out.append(
            f"- lodge rest cost {p.get('cost')}g "
            f"(gold {p.get('gold_before')}→{p.get('gold_after')})"
        )
    elif event_type in ("recruit_accept", "recruit_pass"):
        out.append(
            f"- {event_type}: {p.get('name')} "
            f"({p.get('job_id')} L{p.get('level')}) id={p.get('candidate_id')}"
        )
    elif event_type == "party_dismiss":
        out.append(
            f"- dismiss: {p.get('name')} "
            f"({p.get('job_id')} L{p.get('level')}) id={p.get('character_id')}"
        )
    elif event_type in ("party_swap", "party_promote", "party_bench"):
        out.append(f"- {event_type}: {json.dumps(p, default=str)}")
    else:
        out.append(f"- payload: {json.dumps(p, default=str)}")
    return out


def render_encounter(enc: dict[str, Any], chrono_idx: int) -> str:
    """Render one encounter as a compact header + per-round lines."""
    rounds = enc.get("rounds", [])
    header = (
        f"### ENC {chrono_idx} [{enc['zone_id']} idx={enc['encounter_index']}] "
        f"vs {', '.join(enc['enemy_template_ids'])} → "
        f"**{enc['result'].upper()}** ({enc['rounds_taken']} rounds)"
    )
    summary = (
        f"_dealt {enc['total_damage_dealt']}, took {enc['total_damage_taken']}, "
        f"healed {enc['total_healing']}"
    )
    if enc.get("character_deaths"):
        summary += f", deaths: {enc['character_deaths']}"
    summary += "_"

    lines = [header, summary, ""]

    # Find the MC combatant id (first player_decisions key)
    mc_id: str | None = None
    for rnd in rounds:
        if rnd.get("player_decisions"):
            mc_id = next(iter(rnd["player_decisions"].keys()))
            break

    # Track AP + HP trajectory ourselves — the engine logs post-decision
    # AP only for SURVIVE (as `ap` in details); CHEAT logs actions_spent/debt
    # without the final AP. Simpler to simulate.
    ap_pre = 0  # AP visible to the policy at start of round 1 is 0
    prev_hp: int | None = None
    # Track active MC statuses (derived from STATUS_APPLIED / STATUS_EXPIRED)
    active_statuses: set[str] = set()

    for rnd in rounds:
        rnum = rnd["round_number"]
        decisions = rnd.get("player_decisions", {})
        mc_decision = decisions.get(mc_id) if mc_id else None

        # Pre-decision HP = end-of-previous-round HP (or max_hp on round 1)
        hp_pre = prev_hp

        # Status summary at round start — use tracked set
        status_str = ",".join(sorted(active_statuses)) if active_statuses else "—"

        end_hp = rnd.get("player_hp", {}).get(mc_id) if mc_id else None
        e_hp = rnd.get("enemy_hp", {})

        decision_str = _decision_summary(mc_decision, mc_id)
        outcome_str = _round_outcome(rnd["events"], mc_id)

        # Update AP bank based on the decision
        # (caps at MAX_AP=3, debt for CHEAT)
        if mc_decision:
            cs = mc_decision.get("cheat_survive", "NORMAL")
            if cs == "SURVIVE":
                ap_pre_next = min(ap_pre + 1, 3)
            elif cs == "CHEAT":
                spent = mc_decision.get("cheat_actions", 0)
                ap_pre_next = max(ap_pre - spent, 0)
            else:
                ap_pre_next = ap_pre
        else:
            ap_pre_next = ap_pre

        # Update active statuses from this round's events.
        # Status name is in details.status (e.g., "Taunted", "Brace Strike DEF buff").
        for e in rnd.get("events", []):
            if e["event_type"] == "STATUS_APPLIED" and e.get("target_id") == mc_id:
                sid = e.get("details", {}).get("status", "").strip()
                if sid:
                    active_statuses.add(sid)
            elif e["event_type"] == "STATUS_EXPIRED" and e.get("target_id") == mc_id:
                sid = e.get("details", {}).get("status", "").strip()
                if sid and sid in active_statuses:
                    active_statuses.discard(sid)

        hp_cell = (
            f"hp {hp_pre}→{end_hp}" if hp_pre is not None else f"hp ?→{end_hp}"
        )
        ap_cell = f"ap {ap_pre}"
        enemies_str = (
            "[" + ", ".join(f"{k.rsplit('_', 1)[0]}={v}" for k, v in e_hp.items()) + "]"
        )
        status_cell = f"st={status_str}"

        lines.append(
            f"- **r{rnum}** {hp_cell} {ap_cell} {status_cell} | "
            f"{decision_str} | {outcome_str} | end {enemies_str}"
        )

        prev_hp = end_hp
        ap_pre = ap_pre_next

    return "\n".join(lines)


def _decision_summary(decision: dict[str, Any] | None, mc_id: str | None) -> str:
    if not decision:
        return "—"
    cs = decision.get("cheat_survive", "NORMAL")
    if cs == "SURVIVE":
        base = "**SURVIVE**"
    elif cs == "CHEAT":
        base = f"**CHEAT(+{decision.get('cheat_actions', 0)}AP)**"
    else:
        base = "NORMAL"
    pa = decision.get("primary_action")
    if pa:
        tgt = pa.get("target_ids", [])
        tgt_str = ",".join(_short_tgt(t, mc_id) for t in tgt) if tgt else "?"
        ability = pa.get("ability_id", "?")
        extra = ""
        if pa.get("item_id"):
            extra = f"({pa.get('item_id')})"
        base += f" {ability}{extra}→{tgt_str}"
    extras = decision.get("cheat_extra_actions", [])
    if extras:
        base += f" +cheat_extras×{len(extras)}"
    bonus = decision.get("bonus_actions", [])
    if bonus:
        base += f" +bonus×{len(bonus)}"
    return base


def _short_tgt(target_id: str, mc_id: str | None) -> str:
    if target_id == mc_id:
        return "self"
    # Strip trailing _N suffix for enemies
    parts = target_id.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return target_id


def _round_outcome(events: list[dict[str, Any]], mc_id: str | None) -> str:
    """Pull high-signal events: damage dealt/taken/retaliate/heal/status."""
    dealt = 0
    taken = 0
    retaliate_dmg = 0
    heals = 0
    specials: list[str] = []
    kills: list[str] = []
    retaliate_pending = False  # RETALIATE_TRIGGERED flags the NEXT DAMAGE_DEALT
    for e in events:
        et = e["event_type"]
        details = e.get("details", {})
        val = e.get("value", 0)
        actor = e.get("actor_id", "")
        target = e.get("target_id", "")

        if et == "RETALIATE_TRIGGERED":
            retaliate_pending = True
        elif et == "DAMAGE_DEALT":
            if retaliate_pending and actor == mc_id:
                retaliate_dmg += val
                retaliate_pending = False
            else:
                if actor == mc_id:
                    dealt += val
                elif target == mc_id:
                    taken += val
                retaliate_pending = False
        elif et == "HEAL":
            if target == mc_id:
                heals += val
        elif et == "DEATH":
            # Any death — MC or enemy. Record enemy deaths as kills.
            if target != mc_id and target:
                kills.append(_short_tgt(target, mc_id))
        elif et == "STATUS_APPLIED":
            sname = details.get("status", "?")
            sub = _short_tgt(target, mc_id)
            # Only surface statuses applied to the MC or that change enemy
            # behavior meaningfully (taunt-source, brace_strike on enemy).
            if target == mc_id:
                specials.append(f"+status({sname}→self)")
            else:
                specials.append(f"enemy_status({sname}→{sub})")
        elif et == "STATUS_EXPIRED":
            sname = details.get("status", "?")
            if target == mc_id:
                specials.append(f"-status({sname}→self)")

    parts: list[str] = []
    if dealt:
        parts.append(f"dealt {dealt}")
    if taken:
        parts.append(f"took {taken}")
    if retaliate_dmg:
        parts.append(f"retal {retaliate_dmg}")
    if heals:
        parts.append(f"heal {heals}")
    if kills:
        parts.append(f"KILL {','.join(kills)}")
    if specials:
        # Cap specials to 6 to keep lines from sprawling
        parts.append(", ".join(specials[:6]))
    return " · ".join(parts) if parts else "(no events)"


def main() -> None:
    # CLI: python dump_trace.py [run_id] [out_path] [db_path]
    run_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RUN_ID
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    db_path = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_DB

    db = RecordDB(db_path)
    cur = db.conn.execute(
        "SELECT run_state_json FROM runs WHERE run_id = ?", (run_id,),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"No run {run_id} in {db_path}")
    run = json.loads(row[0])

    macro_events = run["macro_log"]
    encounters = run["battle_record"]["encounters"]

    # Group macro events by encounter_seq_at_time
    events_by_slot: dict[int, list[dict[str, Any]]] = {}
    for evt in macro_events:
        events_by_slot.setdefault(evt["encounter_seq_at_time"], []).append(evt)
    for k in events_by_slot:
        events_by_slot[k].sort(key=lambda e: e["seq"])

    # Build timeline: pre-encounter events, then each encounter + post-events
    sections: list[str] = []

    # Header
    mc = None
    for c in run["party"]["characters"].values():
        if c.get("is_mc"):
            mc = c
            break
    mc_desc = (
        f"einherjar '{mc['name']}' L{mc['level']}" if mc else "unknown MC"
    )
    sections.append(f"# Run Trace: {run_id} ({mc_desc})")
    sections.append("")
    sections.append(
        f"**Final state**: L{mc['level'] if mc else '?'} · "
        f"HP {mc['current_hp'] if mc else '?'}/{mc['max_hp'] if mc else '?'} · "
        f"{run['party']['money']}g · "
        f"zones cleared: {run['zones_completed']}"
    )
    sections.append(f"**Encounters**: {len(encounters)}")
    sections.append(f"**Macro events**: {len(macro_events)}")
    sections.append("")
    sections.append("## Legend")
    sections.append("")
    sections.append(
        "- Round line: `rN hp H→H' ap A st=<statuses> | DECISION primary→target "
        "+extras×N +bonus×N | dealt X · took Y · retal Z · KILL foo "
        "| end [enemy hp]`"
    )
    sections.append(
        "- `hp H→H'` is pre→post-round MC HP. `ap A` is PRE-decision AP "
        "(what the policy saw). `st=` is active statuses at round start "
        "(taunted, marked, etc.) — inferred from events."
    )
    sections.append(
        "- SURVIVE banks +1 AP (capped at 3). CHEAT(+NAP) spends N AP. "
        "NORMAL is a regular turn, no AP change."
    )
    sections.append(
        "- Macro event header: `[seq=N event_type zone]` with L#/HP%/gold context."
    )
    sections.append("")
    sections.append("---")
    sections.append("")

    # Pre-encounter macro events (slot=0)
    if 0 in events_by_slot:
        for evt in events_by_slot[0]:
            sections.append(render_macro(evt))
            sections.append("")

    # For each encounter: emit it, then macro events with slot = idx+1
    for chrono_idx, enc in enumerate(encounters):
        sections.append(render_encounter(enc, chrono_idx))
        sections.append("")
        slot = chrono_idx + 1
        for evt in events_by_slot.get(slot, []):
            sections.append(render_macro(evt))
            sections.append("")

    out = "\n".join(sections)
    out_path.write_text(out)
    print(f"Wrote {out_path} ({len(out):,} bytes, {out.count(chr(10)):,} lines)")


if __name__ == "__main__":
    main()
