"""Event renderer: translates CombatEvent objects into display-ready text.

Pure logic — no Textual imports. Used by the combat log widget and death recap.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from heresiarch.engine.models.combat_state import CombatEvent, CombatEventType


@dataclass
class RenderedEvent:
    """A combat event translated into display-ready form."""

    text: str
    color: str  # "damage" | "heal" | "buff" | "debuff" | "death" | "neutral"
    affected_ids: list[str] = field(default_factory=list)
    is_significant: bool = True


# Event delay configuration in milliseconds
EVENT_DELAYS: dict[CombatEventType, int] = {
    CombatEventType.ROUND_START: 300,
    CombatEventType.TURN_START: 200,
    CombatEventType.CHEAT_SURVIVE_DECISION: 300,
    CombatEventType.ACTION_DECLARED: 250,
    CombatEventType.DAMAGE_DEALT: 400,
    CombatEventType.HEALING: 400,
    CombatEventType.STATUS_APPLIED: 300,
    CombatEventType.STATUS_EXPIRED: 200,
    CombatEventType.STATUS_RESISTED: 250,
    CombatEventType.DOT_TICK: 350,
    CombatEventType.DEATH: 800,
    CombatEventType.BONUS_ACTION: 250,
    CombatEventType.RETALIATE_TRIGGERED: 400,
    CombatEventType.PASSIVE_TRIGGERED: 300,
    CombatEventType.TAUNT_REDIRECT: 350,
    CombatEventType.FRENZY_STACK: 250,
    CombatEventType.COMBAT_END: 500,
}

DEFAULT_DELAY_MS: int = 250


def get_event_delay(event: CombatEvent) -> int:
    """Get the display delay in ms for an event type."""
    return EVENT_DELAYS.get(event.event_type, DEFAULT_DELAY_MS)


def _name(combatant_id: str, names: dict[str, str]) -> str:
    """Resolve a combatant ID to a display name."""
    return names.get(combatant_id, combatant_id)


def _ability_name(ability_id: str, ability_names: dict[str, str]) -> str:
    """Resolve an ability ID to a display name."""
    return ability_names.get(ability_id, ability_id)


def render_event(
    event: CombatEvent,
    combatant_names: dict[str, str],
    ability_names: dict[str, str],
    verbose: bool = True,
) -> RenderedEvent:
    """Translate a CombatEvent into display-ready text and metadata.

    Args:
        event: The raw combat event from the engine.
        combatant_names: Mapping of combatant IDs to display names.
        ability_names: Mapping of ability IDs to display names.
        verbose: If False, non-significant events are still rendered but marked.

    Returns:
        A RenderedEvent with Rich markup text, color category, and affected IDs.
    """
    match event.event_type:
        case CombatEventType.ROUND_START:
            return RenderedEvent(
                text=f"[bold]--- Round {event.round_number} ---[/bold]",
                color="neutral",
                is_significant=False,
            )

        case CombatEventType.TURN_START:
            actor = _name(event.actor_id, combatant_names)
            return RenderedEvent(
                text=f"[dim]{actor}'s turn[/dim]",
                color="neutral",
                affected_ids=[event.actor_id],
                is_significant=False,
            )

        case CombatEventType.CHEAT_SURVIVE_DECISION:
            actor = _name(event.actor_id, combatant_names)
            choice = event.details.get("choice", "NORMAL")
            if choice == "CHEAT":
                actions = event.details.get("actions_spent", 0)
                debt = event.details.get("debt", 0)
                return RenderedEvent(
                    text=f"[bold #e6c566]{actor}[/bold #e6c566] [bold]CHEATS[/bold] ({actions} actions, debt: {debt})",
                    color="buff",
                    affected_ids=[event.actor_id],
                )
            elif choice == "SURVIVE":
                ap = event.details.get("ap", 0)
                return RenderedEvent(
                    text=f"[bold #4488cc]{actor}[/bold #4488cc] [bold]SURVIVES[/bold] (AP: {ap})",
                    color="buff",
                    affected_ids=[event.actor_id],
                )
            else:
                return RenderedEvent(
                    text=f"[dim]{actor} acts normally[/dim]",
                    color="neutral",
                    affected_ids=[event.actor_id],
                    is_significant=False,
                )

        case CombatEventType.ACTION_DECLARED:
            actor = _name(event.actor_id, combatant_names)
            ability = _ability_name(event.ability_id, ability_names)
            targets = event.details.get("targets", [])
            target_str = ", ".join(_name(t, combatant_names) for t in targets)
            if target_str:
                return RenderedEvent(
                    text=f"{actor} uses [bold]{ability}[/bold] on {target_str}",
                    color="neutral",
                    affected_ids=[event.actor_id] + targets,
                )
            return RenderedEvent(
                text=f"{actor} uses [bold]{ability}[/bold]",
                color="neutral",
                affected_ids=[event.actor_id],
            )

        case CombatEventType.BONUS_ACTION:
            actor = _name(event.actor_id, combatant_names)
            ability = _ability_name(event.ability_id, ability_names)
            return RenderedEvent(
                text=f"  {actor} [dim](bonus)[/dim] uses [bold]{ability}[/bold]",
                color="neutral",
                affected_ids=[event.actor_id],
                is_significant=False,
            )

        case CombatEventType.DAMAGE_DEALT:
            actor = _name(event.actor_id, combatant_names)
            target = _name(event.target_id, combatant_names)
            is_self = event.details.get("self_damage", False)
            if is_self:
                return RenderedEvent(
                    text=f"  {actor} takes [bold #cc4444]{event.value}[/bold #cc4444] recoil damage",
                    color="damage",
                    affected_ids=[event.actor_id],
                )
            return RenderedEvent(
                text=f"  {target} takes [bold #cc4444]{event.value}[/bold #cc4444] damage from {actor}",
                color="damage",
                affected_ids=[event.target_id, event.actor_id],
            )

        case CombatEventType.HEALING:
            target = _name(event.target_id, combatant_names)
            source = event.details.get("source", "")
            source_str = f" ({source})" if source else ""
            return RenderedEvent(
                text=f"  {target} heals [bold #44aa44]{event.value}[/bold #44aa44] HP{source_str}",
                color="heal",
                affected_ids=[event.target_id],
            )

        case CombatEventType.STATUS_APPLIED:
            actor = _name(event.actor_id, combatant_names)
            target = _name(event.target_id, combatant_names)
            status = event.details.get("status", event.details.get("quality", "effect"))
            return RenderedEvent(
                text=f"  {actor} applies [bold #cc8844]{status}[/bold #cc8844] to {target}",
                color="debuff",
                affected_ids=[event.target_id],
            )

        case CombatEventType.STATUS_EXPIRED:
            target = _name(event.target_id, combatant_names)
            status = event.details.get("status", "effect")
            return RenderedEvent(
                text=f"  [dim]{status} wears off {target}[/dim]",
                color="neutral",
                affected_ids=[event.target_id],
                is_significant=False,
            )

        case CombatEventType.STATUS_RESISTED:
            target = _name(event.target_id, combatant_names)
            quality = event.details.get("quality", "effect")
            return RenderedEvent(
                text=f"  {target} [bold #4488cc]resists[/bold #4488cc] {quality}!",
                color="buff",
                affected_ids=[event.target_id],
            )

        case CombatEventType.DOT_TICK:
            target = _name(event.target_id, combatant_names)
            status = event.details.get("status", "DOT")
            return RenderedEvent(
                text=f"  {target} takes [bold #cc4444]{event.value}[/bold #cc4444] from {status}",
                color="damage",
                affected_ids=[event.target_id],
            )

        case CombatEventType.DEATH:
            target = _name(event.target_id, combatant_names)
            return RenderedEvent(
                text=f"  [bold #880000]{target} falls.[/bold #880000]",
                color="death",
                affected_ids=[event.target_id],
            )

        case CombatEventType.RETALIATE_TRIGGERED:
            actor = _name(event.actor_id, combatant_names)
            target = _name(event.target_id, combatant_names)
            return RenderedEvent(
                text=f"  {actor} [bold]retaliates[/bold] — {event.value} damage to {target}!",
                color="damage",
                affected_ids=[event.actor_id, event.target_id],
            )

        case CombatEventType.PASSIVE_TRIGGERED:
            actor = _name(event.actor_id, combatant_names)
            ability = _ability_name(event.ability_id, ability_names)
            return RenderedEvent(
                text=f"  {actor}'s [bold]{ability}[/bold] triggers!",
                color="buff",
                affected_ids=[event.actor_id],
            )

        case CombatEventType.TAUNT_REDIRECT:
            target = _name(event.target_id, combatant_names)
            original = _name(event.details.get("original_target", ""), combatant_names)
            return RenderedEvent(
                text=f"  [bold]{target}[/bold] draws the attack! (redirected from {original})",
                color="buff",
                affected_ids=[event.target_id],
            )

        case CombatEventType.FRENZY_STACK:
            actor = _name(event.actor_id, combatant_names)
            multiplier = event.details.get("multiplier", 1.0)
            return RenderedEvent(
                text=f"  {actor} [bold #e6c566]Frenzy x{event.value}[/bold #e6c566] ({multiplier:.1f}x damage)",
                color="buff",
                affected_ids=[event.actor_id],
            )

        case CombatEventType.COMBAT_END:
            result = event.details.get("result", "")
            if result == "player_victory":
                return RenderedEvent(
                    text="[bold #44aa44]--- VICTORY ---[/bold #44aa44]",
                    color="heal",
                )
            else:
                return RenderedEvent(
                    text="[bold #880000]--- DEFEAT ---[/bold #880000]",
                    color="death",
                )

        case _:
            return RenderedEvent(
                text=f"[dim]{event.event_type.value}[/dim]",
                color="neutral",
                is_significant=False,
            )


def render_events_summary(
    events: list[CombatEvent],
    combatant_names: dict[str, str],
    ability_names: dict[str, str],
) -> list[RenderedEvent]:
    """Render events in summary mode — only significant events, with damage aggregation.

    Collapses adjacent DAMAGE_DEALT events from the same actor into a single line.
    """
    rendered: list[RenderedEvent] = []
    i = 0
    while i < len(events):
        event = events[i]

        # Aggregate adjacent damage events from the same actor
        if event.event_type == CombatEventType.DAMAGE_DEALT and not event.details.get("self_damage"):
            total_damage = event.value
            targets: set[str] = {event.target_id}
            abilities_used: list[str] = [event.ability_id] if event.ability_id else []
            actor_id = event.actor_id
            j = i + 1
            while j < len(events) and events[j].event_type == CombatEventType.DAMAGE_DEALT and events[j].actor_id == actor_id:
                total_damage += events[j].value
                targets.add(events[j].target_id)
                if events[j].ability_id and events[j].ability_id not in abilities_used:
                    abilities_used.append(events[j].ability_id)
                j += 1

            actor = _name(actor_id, combatant_names)
            target_str = ", ".join(_name(t, combatant_names) for t in targets)
            ability_str = ", ".join(_ability_name(a, ability_names) for a in abilities_used)
            count = j - i

            if count > 1:
                text = f"  {actor} dealt [bold #cc4444]{total_damage}[/bold #cc4444] total to {target_str} ({ability_str} x{count})"
            else:
                text = f"  {target_str} takes [bold #cc4444]{total_damage}[/bold #cc4444] from {actor}"

            rendered.append(RenderedEvent(
                text=text,
                color="damage",
                affected_ids=[actor_id] + list(targets),
            ))
            i = j
            continue

        # For non-damage events, render normally but skip non-significant ones
        r = render_event(event, combatant_names, ability_names, verbose=False)
        if r.is_significant:
            rendered.append(r)
        i += 1

    return rendered
