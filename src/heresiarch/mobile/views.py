"""Structured view models for the mobile UI.

The GameSession returns prose (built for LLM consumption); a touch UI
needs tappable data. These builders read session/run state and produce
pydantic view models. Read-only — no game logic, no state mutation.

Spike note: this reads a few private session fields (_combat_state,
_last_loot, _enemy_combatant_templates, _round_events). If the mobile
frontend graduates, promote these into a formal structured-view layer
on the summarizer side (see design/mobile-spike.md).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from heresiarch.agent import summarizer as S
from heresiarch.views.event_renderer import (
    get_event_delay,
    render_event,
    render_events_summary,
)
from heresiarch.engine.formulas import (
    calculate_buy_price,
    calculate_sell_price,
    calculate_speed_bonus,
    xp_for_level,
)
from heresiarch.engine.models.abilities import AbilityCategory
from heresiarch.engine.models.stats import GrowthVector, StatBlock
from heresiarch.engine.recruitment import MAX_PARTY_SIZE, InspectionLevel
from heresiarch.views.map_builder import (
    MapVM,
    build_region_map_vm,
    build_town_map_vm,
    build_zone_map_vm,
)

if TYPE_CHECKING:
    from heresiarch.agent.session import GameSession
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.combat_state import CombatantState
    from heresiarch.engine.models.items import Item
    from heresiarch.engine.models.jobs import CharacterInstance
    from heresiarch.engine.models.run_state import RunState

_STAT_KEYS = ("STR", "MAG", "DEF", "RES", "SPD")


def _stats_dict(sb: StatBlock | GrowthVector) -> dict[str, int]:
    return {k: getattr(sb, k, 0) for k in _STAT_KEYS}


# ---------------------------------------------------------------------------
# View models
# ---------------------------------------------------------------------------


class JobView(BaseModel):
    id: str
    name: str
    origin: str = ""


class AbilityView(BaseModel):
    id: str
    name: str
    category: str
    target: str
    cooldown_remaining: int = 0
    windup_turns: int = 0
    insight_amplified: bool = False
    description: str = ""


class ItemView(BaseModel):
    id: str
    name: str
    type: str = ""
    description: str = ""
    is_consumable: bool = False
    heal_amount: int = 0
    heal_percent: float = 0.0
    equip_slot: str | None = None  # WEAPON / ARMOR / ACCESSORY, None = not equippable
    price: int | None = None       # buy price (shop context)
    sell_price: int | None = None  # sell price (stash context)
    # What the item IS, for UI routing: equip / heal / tonic / teach / cast / other
    kind: str = "other"
    hp_bonus: int = 0
    flat_stat_bonus: dict[str, int] = Field(default_factory=dict)
    combat_stat_buff: dict[str, int] = Field(default_factory=dict)
    scaling_desc: str = ""            # e.g. "scales with STR"
    granted_ability: str | None = None  # ability NAME granted while equipped
    teaches_ability: str | None = None  # ability NAME a teach scroll grants
    casts_ability: str | None = None    # ability NAME a cast scroll fires


class CombatantView(BaseModel):
    id: str
    name: str
    is_player: bool
    hp: int
    max_hp: int
    level: int = 1
    ap: int = 0
    cheat_debt: int = 0
    insight: int = 0
    frenzy_level: float = 1.0
    speed_bonus: int = 0
    is_alive: bool = True
    is_surviving: bool = False
    charging: str | None = None
    taunted_by: list[str] = Field(default_factory=list)  # combatant ids
    statuses: list[str] = Field(default_factory=list)
    abilities: list[AbilityView] = Field(default_factory=list)


class CombatEventView(BaseModel):
    """One display-ready combat event for client-side paced playback."""

    type: str
    text: str
    color: str = "neutral"  # damage / heal / buff / debuff / death / neutral
    actor_id: str = ""
    target_id: str = ""
    value: int = 0
    self_damage: bool = False  # DAMAGE_DEALT recoil: HP loss lands on the actor
    significant: bool = True
    delay_ms: int = 250


class CombatView(BaseModel):
    round_number: int
    players: list[CombatantView] = Field(default_factory=list)
    enemies: list[CombatantView] = Field(default_factory=list)
    consumables: list[ItemView] = Field(default_factory=list)
    log_lines: list[str] = Field(default_factory=list)
    # Auto-battle: a recorded victory vs this enemy group has rounds left
    auto_available: bool = False
    # Set when the TUI's halt rule applies (client stops the auto loop)
    auto_halt: str | None = None


class ZoneCardView(BaseModel):
    id: str
    name: str
    zone_level: int
    cleared: bool = False
    is_final: bool = False
    is_endless: bool = False
    n_encounters: int = 0
    recruitment_chance: float = 0.0


class TownCardView(BaseModel):
    id: str
    name: str


class ZoneSelectView(BaseModel):
    zones: list[ZoneCardView] = Field(default_factory=list)
    towns: list[TownCardView] = Field(default_factory=list)


class ZoneStatusView(BaseModel):
    zone_id: str
    name: str
    encounter_index: int = 0
    total_encounters: int = 0
    overstay_battles: int = 0
    is_cleared: bool = False
    is_endless: bool = False


class TownView(BaseModel):
    town_id: str
    name: str
    lodge_cost: int | None = None
    shop_items: list[ItemView] = Field(default_factory=list)


class LootView(BaseModel):
    money: int = 0
    items: list[ItemView] = Field(default_factory=list)


class CharacterView(BaseModel):
    id: str
    name: str
    job_id: str
    job_name: str
    level: int
    hp: int
    max_hp: int
    xp: int = 0
    xp_next: int = 0  # cumulative XP needed for the next level
    is_mc: bool = False
    is_active: bool = True
    base_stats: dict[str, int] = Field(default_factory=dict)
    effective_stats: dict[str, int] = Field(default_factory=dict)
    abilities: list[str] = Field(default_factory=list)
    equipment: dict[str, str | None] = Field(default_factory=dict)  # slot -> item name
    equipment_ids: dict[str, str | None] = Field(default_factory=dict)  # slot -> item id


class RecruitView(BaseModel):
    """CHA-gated candidate reveal, mirroring RecruitmentEngine.inspect_candidate."""

    name: str
    job_id: str
    job_name: str
    inspection: str  # MINIMAL / MODERATE / FULL
    cha: int
    growth: dict[str, int] | None = None       # MODERATE+
    level: int | None = None                   # FULL
    stats: dict[str, int] | None = None        # FULL
    hp: int | None = None                      # FULL
    equipment: list[str] = Field(default_factory=list)  # item names
    party_size: int = 0
    max_party: int = MAX_PARTY_SIZE
    party_full: bool = False


class RecapView(BaseModel):
    """End-of-run summary for the death and victory screens."""

    won: bool = False
    mc_name: str = ""
    mc_level: int = 0
    gold: int = 0
    zones_completed: list[str] = Field(default_factory=list)
    encounters: int = 0
    victories: int = 0
    defeats: int = 0
    rounds: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    healing: int = 0
    character_deaths: int = 0


class EquipPreview(BaseModel):
    """Stat-diff preview for an equipment change (before committing)."""

    ok: bool = True
    error: str | None = None
    slot: str = ""
    replacing: str | None = None  # name of the currently equipped item, if any
    current: dict[str, int] = Field(default_factory=dict)
    preview: dict[str, int] = Field(default_factory=dict)
    current_max_hp: int = 0
    preview_max_hp: int = 0


class PartyView(BaseModel):
    gold: int = 0
    cha: int = 0
    stash: list[ItemView] = Field(default_factory=list)
    stash_used: int = 0
    stash_limit: int = 10
    characters: list[CharacterView] = Field(default_factory=list)


class StatePayload(BaseModel):
    """Everything the phone UI needs to render one screen."""

    phase: str
    text: str = ""
    error: str | None = None
    jobs: list[JobView] = Field(default_factory=list)
    party: PartyView | None = None
    zone_select: ZoneSelectView | None = None
    zone: ZoneStatusView | None = None
    town: TownView | None = None
    combat: CombatView | None = None
    loot: LootView | None = None
    recruit: RecruitView | None = None
    recap: RecapView | None = None
    map: MapVM | None = None
    # Last processed round, for paced playback: verbose events (per-type
    # delays), one-line-per-turn summary, and HP at round start so bars
    # can animate down event-by-event. Present in COMBAT and on the
    # screen right after combat ends (POST_COMBAT / DEAD).
    events: list[CombatEventView] = Field(default_factory=list)
    events_summary: list[CombatEventView] = Field(default_factory=list)
    hp_start: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _item_kind(item: Item) -> str:
    if item.equip_type:
        return "equip"
    if item.teaches_ability_id:
        return "teach"
    if item.casts_ability_id:
        return "cast"
    if item.combat_stat_buff:
        return "tonic"
    if item.heal_amount or item.heal_percent:
        return "heal"
    return "other"


def _ability_name(game_data: GameData, ability_id: str | None) -> str | None:
    if not ability_id:
        return None
    ability = game_data.abilities.get(ability_id)
    return ability.name if ability else ability_id


def _item_view(
    item: Item | None,
    item_id: str,
    *,
    game_data: GameData | None = None,
    buy_cha: int | None = None,
    with_sell: bool = False,
) -> ItemView:
    if item is None:
        return ItemView(id=item_id, name=item_id)
    scaling_desc = ""
    if item.scaling is not None:
        scaling_desc = f"scales with {item.scaling.stat.value}"
    return ItemView(
        id=item.id,
        name=item.name,
        type=item.display_type,
        description=item.description,
        is_consumable=item.is_consumable,
        heal_amount=item.heal_amount,
        heal_percent=item.heal_percent,
        equip_slot=item.equip_type.value if item.equip_type else None,
        price=(
            calculate_buy_price(item.base_price, buy_cha)
            if buy_cha is not None
            else None
        ),
        sell_price=calculate_sell_price(item.base_price) if with_sell else None,
        kind=_item_kind(item),
        hp_bonus=item.hp_bonus,
        flat_stat_bonus=dict(item.flat_stat_bonus),
        combat_stat_buff=dict(item.combat_stat_buff),
        scaling_desc=scaling_desc,
        granted_ability=(
            _ability_name(game_data, item.granted_ability_id) if game_data else None
        ),
        teaches_ability=(
            _ability_name(game_data, item.teaches_ability_id) if game_data else None
        ),
        casts_ability=(
            _ability_name(game_data, item.casts_ability_id) if game_data else None
        ),
    )


def _lookup_item(session: GameSession, item_id: str) -> Item | None:
    item = session.game_data.items.get(item_id)
    if item is None and session.run is not None:
        item = session.run.party.items.get(item_id)
    return item


def _ability_view(
    ability_id: str, game_data: GameData, cooldowns: dict[str, int] | None = None,
) -> AbilityView:
    ability = game_data.abilities.get(ability_id)
    if ability is None:
        return AbilityView(
            id=ability_id, name=ability_id, category="?", target="SINGLE_ENEMY",
        )
    return AbilityView(
        id=ability.id,
        name=ability.name,
        category=ability.category.value,
        target=ability.target.value,
        cooldown_remaining=(cooldowns or {}).get(ability_id, 0),
        windup_turns=ability.windup_turns,
        insight_amplified=ability.insight_amplified,
        description=ability.description,
    )


def _character_view(
    char: CharacterInstance, run: RunState, game_data: GameData,
) -> CharacterView:
    job = game_data.jobs.get(char.job_id)
    equipment_names: dict[str, str | None] = {}
    for slot, item_id in char.equipment.items():
        if item_id:
            item = run.party.items.get(item_id) or game_data.items.get(item_id)
            equipment_names[slot] = item.name if item else item_id
        else:
            equipment_names[slot] = None
    return CharacterView(
        id=char.id,
        name=char.name,
        job_id=char.job_id,
        job_name=job.name if job else char.job_id,
        level=char.level,
        hp=char.current_hp,
        max_hp=char.max_hp,
        xp=char.xp,
        xp_next=xp_for_level(char.level + 1),
        is_mc=char.is_mc,
        is_active=char.id in run.party.active,
        base_stats=_stats_dict(char.base_stats),
        effective_stats=_stats_dict(char.effective_stats),
        abilities=char.get_all_abilities(),
        equipment=equipment_names,
        equipment_ids=dict(char.equipment),
    )


def build_party_view(session: GameSession) -> PartyView | None:
    run = session.run
    if run is None:
        return None
    stash_views = [
        _item_view(
            _lookup_item(session, iid), iid,
            game_data=session.game_data, with_sell=True,
        )
        for iid in run.party.stash
    ]
    ordered_ids = list(run.party.active) + [
        cid for cid in run.party.characters if cid not in run.party.active
    ]
    return PartyView(
        gold=run.party.money,
        cha=run.party.cha,
        stash=stash_views,
        stash_used=len(run.party.stash),
        stash_limit=10,
        characters=[
            _character_view(run.party.characters[cid], run, session.game_data)
            for cid in ordered_ids
            if cid in run.party.characters
        ],
    )


def build_zone_select_view(session: GameSession) -> ZoneSelectView | None:
    run = session.run
    gl = session.game_loop
    if run is None or gl is None:
        return None
    zones = [
        ZoneCardView(
            id=z.id,
            name=z.name,
            zone_level=z.zone_level,
            cleared=z.id in run.zones_completed,
            is_final=z.is_final,
            is_endless=z.is_endless,
            n_encounters=len(z.encounters),
            recruitment_chance=z.recruitment_chance,
        )
        for z in gl.get_available_zones(run)
    ]
    towns: list[TownCardView] = []
    region = gl.get_region_for_run(run)
    town = gl.get_town_for_region(region)
    if town is not None and gl.is_town_unlocked(run, town.id):
        towns.append(TownCardView(id=town.id, name=town.name))
    return ZoneSelectView(zones=zones, towns=towns)


def build_zone_status_view(session: GameSession) -> ZoneStatusView | None:
    run = session.run
    if run is None or run.current_zone_id is None:
        return None
    zone = session.game_data.zones.get(run.current_zone_id)
    zs = run.zone_state
    return ZoneStatusView(
        zone_id=run.current_zone_id,
        name=zone.name if zone else run.current_zone_id,
        encounter_index=zs.current_encounter_index if zs else 0,
        total_encounters=len(zone.encounters) if zone else 0,
        overstay_battles=zs.overstay_battles if zs else 0,
        is_cleared=zs.is_cleared if zs else False,
        is_endless=zone.is_endless if zone else False,
    )


def build_town_view(session: GameSession) -> TownView | None:
    run = session.run
    gl = session.game_loop
    if run is None or gl is None or run.current_town_id is None:
        return None
    town = session.game_data.towns.get(run.current_town_id)
    shop_items = [
        _item_view(
            session.game_data.items.get(iid), iid,
            game_data=session.game_data, buy_cha=run.party.cha,
        )
        for iid in gl.resolve_town_shop(run)
    ]
    return TownView(
        town_id=run.current_town_id,
        name=town.name if town else run.current_town_id,
        lodge_cost=gl.get_lodge_cost(run),
        shop_items=shop_items,
    )


def _combatant_names(session: GameSession) -> dict[str, str]:
    """Display names for all combatants, mirroring the TUI's naming.

    Players get character names; enemies get template names with a
    letter suffix (Slime A, Slime B) whenever the fight has more than
    one enemy. Built from session state so it survives combat teardown
    (the final round's events render on the post-combat screen).
    """
    names: dict[str, str] = {}
    if session.run is not None:
        for cid, char in session.run.party.characters.items():
            names[cid] = char.name
    enemy_ids = list(session._enemy_combatant_templates)
    multi = len(enemy_ids) > 1
    for i, cid in enumerate(enemy_ids):
        tmpl = session.game_data.enemies.get(
            session._enemy_combatant_templates[cid],
        )
        base = tmpl.name if tmpl else cid
        names[cid] = f"{base} {chr(65 + i)}" if multi else base
    return names


def _combatant_view(
    c: CombatantState,
    session: GameSession,
    names: dict[str, str],
    *,
    slowest_enemy_spd: int = 0,
) -> CombatantView:
    game_data = session.game_data
    name = names.get(c.id, c.id)

    charging = None
    if c.charging_ability_id:
        ab = game_data.abilities.get(c.charging_ability_id)
        charging = (
            f"{ab.name if ab else c.charging_ability_id}"
            f" in {c.charge_turns_remaining}"
        )

    abilities = []
    if c.is_player:
        abilities = [
            av
            for av in (
                _ability_view(aid, game_data, c.cooldowns) for aid in c.ability_ids
            )
            if av.category != AbilityCategory.PASSIVE.value
        ]

    speed_bonus = 0
    if c.is_player and c.is_alive and slowest_enemy_spd > 0:
        speed_bonus = calculate_speed_bonus(c.effective_stats.SPD, slowest_enemy_spd)

    return CombatantView(
        id=c.id,
        name=name,
        is_player=c.is_player,
        hp=c.current_hp,
        max_hp=c.max_hp,
        level=c.level,
        ap=c.action_points,
        cheat_debt=c.cheat_debt,
        insight=c.insight_stacks,
        frenzy_level=c.frenzy_level,
        speed_bonus=speed_bonus,
        is_alive=c.is_alive,
        is_surviving=c.is_surviving,
        charging=charging,
        taunted_by=list(c.taunted_by),
        statuses=[f"{s.name} ({s.rounds_remaining})" for s in c.active_statuses],
        abilities=abilities,
    )


def build_combat_view(session: GameSession) -> CombatView | None:
    combat = session._combat_state
    run = session.run
    if combat is None or run is None:
        return None

    living_enemy_spds = [
        e.effective_stats.SPD for e in combat.enemy_combatants if e.is_alive
    ]
    slowest = min(living_enemy_spds) if living_enemy_spds else 0

    log_lines: list[str] = []
    for event in session._round_events:
        try:
            rendered = S._render_combat_event(event, combat, session.game_data)
        except Exception:  # noqa: BLE001 — rendering must never break the payload
            rendered = None
        if rendered:
            log_lines.append(rendered)

    consumables = [
        v
        for v in (
            _item_view(_lookup_item(session, iid), iid, game_data=session.game_data)
            for iid in run.party.stash
        )
        if v.is_consumable
    ]

    # Auto-battle availability: a recorded win vs this group with rounds
    # left to replay; halted (TUI rule) once anyone drops to half HP.
    from heresiarch.engine.replay import find_matching_record

    record = find_matching_record(
        run.battle_record.encounters,
        list(session._enemy_combatant_templates.values()),
    )
    auto_available = (
        record is not None and combat.round_number < len(record.rounds)
    )
    auto_halt = None
    if any(
        c.current_hp <= c.max_hp // 2
        for c in combat.player_combatants
        if c.is_alive
    ):
        auto_halt = "party HP below 50%"

    names = _combatant_names(session)
    return CombatView(
        round_number=combat.round_number,
        players=[
            _combatant_view(c, session, names, slowest_enemy_spd=slowest)
            for c in combat.player_combatants
        ],
        enemies=[
            _combatant_view(c, session, names)
            for c in combat.enemy_combatants
        ],
        consumables=consumables,
        log_lines=log_lines,
        auto_available=auto_available,
        auto_halt=auto_halt,
    )


# Rich markup tags ([bold #cc4444] … [/bold #cc4444]) → plain text
_RICH_TAG_RE = re.compile(r"\[/?[a-zA-Z#][^\[\]]*\]")


def _strip_markup(text: str) -> str:
    return _RICH_TAG_RE.sub("", text)


def _events_phase_active(session: GameSession) -> bool:
    """Round events are shown mid-combat and on the screen right after."""
    from heresiarch.agent.session import Phase

    return session.phase in (Phase.COMBAT, Phase.POST_COMBAT, Phase.DEAD)


def build_round_events(session: GameSession) -> list[CombatEventView]:
    """Verbose per-event playback list with TUI-matching delays."""
    if not _events_phase_active(session) or not session._round_events:
        return []
    names = _combatant_names(session)
    ability_names = {a.id: a.name for a in session.game_data.abilities.values()}

    views: list[CombatEventView] = []
    for event in session._round_events:
        try:
            rendered = render_event(event, names, ability_names, verbose=True)
        except Exception:  # noqa: BLE001 — rendering must never break the payload
            rendered = None
        if rendered is None:
            continue
        views.append(CombatEventView(
            type=event.event_type.value,
            text=_strip_markup(rendered.text),
            color=rendered.color,
            actor_id=event.actor_id,
            target_id=event.target_id,
            value=event.value,
            self_damage=bool(event.details.get("self_damage", False)),
            significant=rendered.is_significant,
            delay_ms=get_event_delay(event),
        ))
    return views


def build_round_events_summary(session: GameSession) -> list[CombatEventView]:
    """One-line-per-turn collapse of the last round (TUI summary mode)."""
    if not _events_phase_active(session) or not session._round_events:
        return []
    names = _combatant_names(session)
    ability_names = {a.id: a.name for a in session.game_data.abilities.values()}
    try:
        rendered = render_events_summary(
            session._round_events, names, ability_names,
        )
    except Exception:  # noqa: BLE001 — degrade to empty, never 500
        return []
    return [
        CombatEventView(
            type="SUMMARY",
            text=_strip_markup(r.text),
            color=r.color,
            delay_ms=300,
        )
        for r in rendered
    ]


def build_hp_start(session: GameSession) -> dict[str, int]:
    if not _events_phase_active(session):
        return {}
    return dict(session._round_start_hp)


def build_loot_view(session: GameSession) -> LootView | None:
    loot = session._last_loot
    if loot is None:
        return None
    return LootView(
        money=loot.money,
        items=[
            _item_view(
                session.game_data.items.get(iid), iid, game_data=session.game_data,
            )
            for iid in loot.item_ids
        ],
    )


def build_recruit_view(session: GameSession) -> RecruitView | None:
    candidate = session._current_candidate
    run = session.run
    gl = session.game_loop
    if candidate is None or run is None or gl is None:
        return None

    level = gl.recruitment_engine.get_inspection_level(run.party.cha)
    char = candidate.character
    job = session.game_data.jobs.get(char.job_id)

    equipment_names: list[str] = []
    for item_id in char.equipment.values():
        if item_id:
            item = session.game_data.items.get(item_id)
            equipment_names.append(item.name if item else item_id)

    party_size = len(run.party.active) + len(run.party.reserve)
    view = RecruitView(
        name=char.name,
        job_id=char.job_id,
        job_name=job.name if job else char.job_id,
        inspection=level.value,
        cha=run.party.cha,
        equipment=equipment_names,
        party_size=party_size,
        party_full=party_size >= MAX_PARTY_SIZE,
    )
    if level in (InspectionLevel.MODERATE, InspectionLevel.FULL):
        view.growth = _stats_dict(candidate.growth)
    if level == InspectionLevel.FULL:
        view.level = char.level
        view.stats = _stats_dict(char.base_stats)
        view.hp = char.current_hp
    return view


def build_recap_view(session: GameSession) -> RecapView | None:
    run = session.run
    if run is None:
        return None
    from heresiarch.agent.session import Phase

    if session.phase not in (Phase.DEAD, Phase.VICTORY):
        return None

    mc_name, mc_level = "", 0
    for char in run.party.characters.values():
        if char.is_mc:
            mc_name, mc_level = char.name, char.level
            break

    encounters = run.battle_record.encounters
    return RecapView(
        won=session.phase == Phase.VICTORY,
        mc_name=mc_name,
        mc_level=mc_level,
        gold=run.party.money,
        zones_completed=list(run.zones_completed),
        encounters=len(encounters),
        victories=sum(1 for e in encounters if e.result == "victory"),
        defeats=sum(1 for e in encounters if e.result != "victory"),
        rounds=sum(e.rounds_taken for e in encounters),
        damage_dealt=sum(e.total_damage_dealt for e in encounters),
        damage_taken=sum(e.total_damage_taken for e in encounters),
        healing=sum(e.total_healing for e in encounters),
        character_deaths=sum(len(e.character_deaths) for e in encounters),
    )


def build_equip_preview(
    session: GameSession, character_id: str, item_id: str, slot: str | None,
) -> EquipPreview:
    """Stat-diff for equipping item_id on character_id. Read-only."""
    run = session.run
    gl = session.game_loop
    if run is None or gl is None:
        return EquipPreview(ok=False, error="No active run.")

    char = run.party.characters.get(character_id)
    if char is None:
        return EquipPreview(ok=False, error=f"Unknown character: {character_id}")

    item = _lookup_item(session, item_id)
    if item is None or item.equip_type is None:
        return EquipPreview(ok=False, error=f"'{item_id}' is not equippable.")

    if slot is None:
        if item.equip_type.value == "ACCESSORY":
            slot = (
                "ACCESSORY_1" if not char.equipment.get("ACCESSORY_1")
                else "ACCESSORY_2" if not char.equipment.get("ACCESSORY_2")
                else "ACCESSORY_1"
            )
        else:
            slot = item.equip_type.value
    if slot not in char.equipment:
        return EquipPreview(ok=False, error=f"Unknown slot: {slot}")

    replacing = None
    replaced_id = char.equipment.get(slot)
    if replaced_id:
        replaced = _lookup_item(session, replaced_id)
        replacing = replaced.name if replaced else replaced_id

    try:
        preview_stats, preview_hp = gl.preview_equipment_change(
            char, run.party, slot, item_id,
        )
    except Exception as e:  # noqa: BLE001 — surface, don't 500
        return EquipPreview(ok=False, error=f"Preview failed: {e}")

    return EquipPreview(
        slot=slot,
        replacing=replacing,
        current=_stats_dict(char.effective_stats),
        preview=_stats_dict(preview_stats),
        current_max_hp=char.max_hp,
        preview_max_hp=preview_hp,
    )


def build_map_view(session: GameSession) -> MapVM | None:
    """Phase-appropriate ASCII map: region, zone path, or town interior."""
    run = session.run
    gl = session.game_loop
    if run is None or gl is None:
        return None
    from heresiarch.agent.session import Phase

    match session.phase:
        case Phase.ZONE_SELECT:
            return build_region_map_vm(run, session.game_data, gl)
        case Phase.IN_ZONE:
            return build_zone_map_vm(run, session.game_data)
        case Phase.IN_TOWN:
            return build_town_map_vm(run, session.game_data)
        case _:
            return None


def build_state_payload(
    session: GameSession, *, text: str = "", error: str | None = None,
) -> StatePayload:
    """Assemble the full payload for the current session state.

    Every builder is individually guarded: a broken view must degrade to
    None/empty, never take down the endpoint.
    """

    def _safe(builder, default=None):  # type: ignore[no-untyped-def]
        try:
            return builder(session)
        except Exception:  # noqa: BLE001 — spike: degrade views, never 500
            return default

    jobs = [
        JobView(id=j.id, name=j.name, origin=getattr(j, "origin", ""))
        for j in session.game_data.jobs.values()
    ]

    return StatePayload(
        phase=session.phase.value,
        text=text,
        error=error,
        jobs=jobs,
        party=_safe(build_party_view),
        zone_select=_safe(build_zone_select_view),
        zone=_safe(build_zone_status_view),
        town=_safe(build_town_view),
        combat=_safe(build_combat_view),
        loot=_safe(build_loot_view),
        recruit=_safe(build_recruit_view),
        recap=_safe(build_recap_view),
        map=_safe(build_map_view),
        events=_safe(build_round_events, default=[]),
        events_summary=_safe(build_round_events_summary, default=[]),
        hp_start=_safe(build_hp_start, default={}),
    )
