"""General-purpose combat simulator using the real CombatEngine.

Drives scripted player decisions through the actual engine, so every passive,
status, frenzy chain, thorns reflect, and enemy AI action fires exactly as it
would in a real game.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.encounter import EncounterGenerator
from heresiarch.engine.formulas import (
    calculate_effective_stats,
    calculate_max_hp,
    calculate_stats_at_level,
)
from heresiarch.engine.models.combat_state import (
    CheatSurviveChoice,
    CombatAction,
    CombatEventType,
    CombatState,
    PlayerTurnDecision,
)
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.jobs import CharacterInstance

if TYPE_CHECKING:
    from heresiarch.engine.data_loader import GameData
    from heresiarch.engine.models.abilities import TargetType
    from heresiarch.engine.models.zone import ZoneTemplate


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ActionKind(str, Enum):
    SURVIVE = "survive"
    NORMAL = "normal"
    CHEAT = "cheat"
    ITEM = "item"


@dataclass
class ActionStep:
    kind: ActionKind
    ability_id: str = "basic_attack"
    cheat_ap: int = 0
    item_id: str = ""


@dataclass
class EncounterConfig:
    enemy_id: str
    enemy_level: int
    enemy_count: int = 1


@dataclass
class Scenario:
    job_id: str
    level: int = 1
    equipment: dict[str, str | None] = field(
        default_factory=lambda: {
            "WEAPON": None, "ARMOR": None,
            "ACCESSORY_1": None, "ACCESSORY_2": None,
        }
    )
    cycle: list[ActionStep] = field(default_factory=list)
    zone_id: str | None = None
    encounters: list[EncounterConfig] = field(default_factory=list)
    between_encounters: dict[int, list[ActionStep]] = field(default_factory=dict)
    seed: int = 42
    max_rounds: int = 50


@dataclass
class RoundSummary:
    round_num: int
    action: str
    damage_dealt: int = 0
    damage_taken: int = 0
    player_hp: int = 0
    player_ap: int = 0
    cheat_debt: int = 0
    insight_stacks: int = 0
    enemy_hp: dict[str, int] = field(default_factory=dict)  # id → current HP
    details: list[str] = field(default_factory=list)


@dataclass
class EncounterResult:
    index: int
    label: str
    rounds: int = 0
    player_won: bool = False
    player_hp: int = 0
    player_max_hp: int = 0
    enemies_killed: int = 0
    total_enemies: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    round_summaries: list[RoundSummary] = field(default_factory=list)


@dataclass
class SimResult:
    encounter_results: list[EncounterResult] = field(default_factory=list)
    final_hp: int = 0
    run_failed_at: int | None = None


# ---------------------------------------------------------------------------
# Cycle DSL parser
# ---------------------------------------------------------------------------


def parse_cycle(cycle_str: str) -> list[ActionStep]:
    """Parse a cycle string into a list of ActionStep.

    Tokens (case-insensitive, comma-separated):
      S or survive           → ActionStep(SURVIVE)
      A or attack            → ActionStep(NORMAL, basic_attack)
      A:ability_id           → ActionStep(NORMAL, ability_id)
      C{N}                   → ActionStep(CHEAT, basic_attack, ap=N)
      C{N}:ability_id        → ActionStep(CHEAT, ability_id, ap=N)
      I:item_id              → ActionStep(ITEM, item_id=item_id)
    """
    steps: list[ActionStep] = []
    for raw in cycle_str.split(","):
        token = raw.strip().lower()
        if not token:
            continue

        if token in ("s", "survive"):
            steps.append(ActionStep(kind=ActionKind.SURVIVE))
        elif token.startswith("i:"):
            steps.append(ActionStep(kind=ActionKind.ITEM, item_id=token[2:]))
        elif token.startswith("c"):
            rest = token[1:]
            if ":" in rest:
                ap_str, ability = rest.split(":", 1)
            else:
                ap_str, ability = rest, "basic_attack"
            steps.append(ActionStep(
                kind=ActionKind.CHEAT,
                cheat_ap=int(ap_str),
                ability_id=ability,
            ))
        elif token in ("a", "attack"):
            steps.append(ActionStep(kind=ActionKind.NORMAL))
        elif token.startswith("a:"):
            steps.append(ActionStep(kind=ActionKind.NORMAL, ability_id=token[2:]))
        else:
            # Treat bare token as ability ID for a normal action
            steps.append(ActionStep(kind=ActionKind.NORMAL, ability_id=token))
    return steps


def parse_between(between_str: str) -> dict[int, list[ActionStep]]:
    """Parse between-encounter actions.

    Format: "1:minor_potion,2:minor_potion" → {1: [item step], 2: [item step]}
    """
    result: dict[int, list[ActionStep]] = {}
    if not between_str:
        return result
    for raw in between_str.split(","):
        token = raw.strip()
        if ":" not in token:
            continue
        idx_str, item_id = token.split(":", 1)
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        result.setdefault(idx, []).append(
            ActionStep(kind=ActionKind.ITEM, item_id=item_id)
        )
    return result


# ---------------------------------------------------------------------------
# CombatSimulator
# ---------------------------------------------------------------------------


class CombatSimulator:
    """Drives the real CombatEngine with scripted player decisions."""

    def __init__(self, game_data: GameData, seed: int = 42) -> None:
        self.gd = game_data
        self.seed = seed

    # --- Character construction ---

    def _build_character(self, scenario: Scenario) -> CharacterInstance:
        """Build a CharacterInstance from scenario config."""
        job = self.gd.jobs[scenario.job_id]
        stats = calculate_stats_at_level(job.growth, scenario.level)

        equipped_items = []
        for slot, item_id in scenario.equipment.items():
            if item_id and item_id in self.gd.items:
                equipped_items.append(self.gd.items[item_id])

        effective = calculate_effective_stats(stats, equipped_items, [])
        max_hp = calculate_max_hp(
            job.base_hp, job.hp_growth, scenario.level, effective.DEF,
        )

        # Build abilities: basic_attack + innate + unlocks at level
        abilities = ["basic_attack", "survive", job.innate_ability_id]
        for unlock in job.ability_unlocks:
            if unlock.level <= scenario.level:
                abilities.append(unlock.ability_id)
        # Deduplicate preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for a in abilities:
            if a not in seen:
                seen.add(a)
                deduped.append(a)

        return CharacterInstance(
            id=f"{scenario.job_id}_sim",
            name=job.name,
            job_id=scenario.job_id,
            level=scenario.level,
            base_stats=stats,
            effective_stats=effective,
            max_hp=max_hp,
            current_hp=max_hp,
            equipment=dict(scenario.equipment),
            abilities=deduped,
        )

    # --- Encounter construction ---

    def _build_encounters_from_zone(
        self, zone: ZoneTemplate,
    ) -> list[tuple[list[EnemyInstance], str]]:
        """Build encounter list from a zone template."""
        rng = random.Random(self.seed)
        engine = self._make_engine(rng)
        gen = EncounterGenerator(
            enemy_registry=self.gd.enemies,
            combat_engine=engine,
            rng=rng,
        )
        total_enc = len(zone.encounters)
        results = []
        for idx, enc_tmpl in enumerate(zone.encounters):
            enemies = gen.generate_encounter(
                enc_tmpl, zone.zone_level,
                enemy_level_range=zone.enemy_level_range,
                encounter_index=idx,
                total_encounters=total_enc,
            )
            boss_tag = " (BOSS)" if enc_tmpl.is_boss else ""
            # Build label from enemy composition
            comp_parts = []
            for tmpl_id, cnt in zip(enc_tmpl.enemy_templates, enc_tmpl.enemy_counts, strict=True):
                comp_parts.append(f"{cnt}x {tmpl_id}")
            label = f"Enc {idx}: {', '.join(comp_parts)}{boss_tag}"
            results.append((enemies, label))
        return results

    def _build_encounters_explicit(
        self, configs: list[EncounterConfig],
    ) -> list[tuple[list[EnemyInstance], str]]:
        """Build encounters from explicit configs."""
        rng = random.Random(self.seed)
        engine = self._make_engine(rng)
        results = []
        for idx, cfg in enumerate(configs):
            tmpl = self.gd.enemies[cfg.enemy_id]
            enemies = [
                engine.create_enemy_instance(
                    tmpl, cfg.enemy_level,
                    instance_id=f"{cfg.enemy_id}_{i}",
                )
                for i in range(cfg.enemy_count)
            ]
            label = f"Enc {idx}: {cfg.enemy_count}x {cfg.enemy_id} Lv{cfg.enemy_level}"
            results.append((enemies, label))
        return results

    # --- Decision construction ---

    def _auto_target(
        self, ability_id: str, state: CombatState, char_id: str,
    ) -> list[str]:
        """Pick targets automatically based on ability target type."""
        from heresiarch.engine.models.abilities import TargetType

        ability = self.gd.abilities.get(ability_id)
        if ability is None:
            return [state.living_enemies[0].id] if state.living_enemies else []

        if ability.target == TargetType.SINGLE_ENEMY:
            return [state.living_enemies[0].id] if state.living_enemies else []
        elif ability.target == TargetType.ALL_ENEMIES:
            return [e.id for e in state.living_enemies]
        elif ability.target == TargetType.SELF:
            return [char_id]
        elif ability.target == TargetType.SINGLE_ALLY:
            return [char_id]  # solo sim — target self
        elif ability.target == TargetType.ALL_ALLIES:
            return [char_id]
        return [state.living_enemies[0].id] if state.living_enemies else []

    def _build_decision(
        self, step: ActionStep, char_id: str, state: CombatState,
    ) -> PlayerTurnDecision:
        """Convert an ActionStep into a PlayerTurnDecision."""
        if step.kind == ActionKind.SURVIVE:
            return PlayerTurnDecision(
                combatant_id=char_id,
                cheat_survive=CheatSurviveChoice.SURVIVE,
            )

        if step.kind == ActionKind.ITEM:
            primary = CombatAction(
                actor_id=char_id,
                ability_id="use_item",
                item_id=step.item_id,
                target_ids=[char_id],
            )
            return PlayerTurnDecision(
                combatant_id=char_id,
                primary_action=primary,
            )

        targets = self._auto_target(step.ability_id, state, char_id)
        primary = CombatAction(
            actor_id=char_id,
            ability_id=step.ability_id,
            target_ids=targets,
        )

        if step.kind == ActionKind.CHEAT:
            extras = [
                CombatAction(
                    actor_id=char_id,
                    ability_id=step.ability_id,
                    target_ids=self._auto_target(step.ability_id, state, char_id),
                )
                for _ in range(step.cheat_ap)
            ]
            return PlayerTurnDecision(
                combatant_id=char_id,
                cheat_survive=CheatSurviveChoice.CHEAT,
                cheat_actions=step.cheat_ap,
                primary_action=primary,
                cheat_extra_actions=extras,
            )

        # NORMAL
        return PlayerTurnDecision(
            combatant_id=char_id,
            cheat_survive=CheatSurviveChoice.NORMAL,
            primary_action=primary,
        )

    # --- Engine helpers ---

    def _make_engine(self, rng: random.Random | None = None) -> CombatEngine:
        return CombatEngine(
            ability_registry=self.gd.abilities,
            item_registry=self.gd.items,
            job_registry=self.gd.jobs,
            rng=rng or random.Random(self.seed),
        )

    # --- Round summary extraction ---

    def _extract_round_summary(
        self, state: CombatState, round_num: int, action_label: str, char_id: str,
    ) -> RoundSummary:
        """Read the event log for a specific round and build a summary."""
        dmg_dealt = 0
        dmg_taken = 0
        details: list[str] = []

        for ev in state.log:
            if ev.round_number != round_num:
                continue
            if ev.event_type == CombatEventType.DAMAGE_DEALT:
                if ev.actor_id == char_id:
                    dmg_dealt += ev.value
                    details.append(f"  hit {ev.target_id} for {ev.value}")
                elif ev.target_id == char_id:
                    dmg_taken += ev.value
                    details.append(f"  took {ev.value} from {ev.actor_id}")
            elif ev.event_type == CombatEventType.DEATH:
                details.append(f"  {ev.target_id} died")
            elif ev.event_type == CombatEventType.THORNS_TRIGGERED:
                details.append(f"  thorns: {ev.value} to {ev.target_id}")
            elif ev.event_type == CombatEventType.RETALIATE_TRIGGERED:
                details.append(f"  retaliate: {ev.value} to {ev.target_id}")
            elif ev.event_type == CombatEventType.HEALING:
                details.append(f"  heal {ev.target_id} for {ev.value}")
            elif ev.event_type == CombatEventType.ITEM_USED:
                details.append(f"  used {ev.details.get('item_name', ev.details.get('item_id', '?'))}")
            elif ev.event_type == CombatEventType.FRENZY_STACK:
                if ev.details:
                    details.append(f"  frenzy chain={ev.details.get('chain', '?')}")
            elif ev.event_type == CombatEventType.INSIGHT_CONSUMED:
                details.append(f"  insight consumed")

        player = state.get_combatant(char_id)
        hp = player.current_hp if player else 0
        ap = player.action_points if player else 0
        debt = player.cheat_debt if player else 0
        insight = player.insight_stacks if player else 0

        enemy_hp = {
            e.id: e.current_hp for e in state.enemy_combatants if e.is_alive
        }

        return RoundSummary(
            round_num=round_num,
            action=action_label,
            damage_dealt=dmg_dealt,
            damage_taken=dmg_taken,
            player_hp=hp,
            player_ap=ap,
            cheat_debt=debt,
            insight_stacks=insight,
            enemy_hp=enemy_hp,
            details=details,
        )

    # --- Single encounter ---

    def _run_encounter(
        self,
        char: CharacterInstance,
        enemies: list[EnemyInstance],
        cycle: list[ActionStep],
        max_rounds: int,
    ) -> EncounterResult:
        """Run one encounter to completion."""
        rng = random.Random(self.seed)
        engine = self._make_engine(rng)
        state = engine.initialize_combat([char], enemies)
        char_id = f"{char.id}"

        # Find the actual combatant ID assigned by initialize_combat
        for p in state.player_combatants:
            char_id = p.id
            break

        total_enemies = len(enemies)
        round_summaries: list[RoundSummary] = []
        cycle_idx = 0

        while not state.is_finished and state.round_number < max_rounds:
            step = cycle[cycle_idx % len(cycle)]
            cycle_idx += 1

            # Item use is a proper action — goes through process_round
            if step.kind == ActionKind.ITEM:
                item = self.gd.items.get(step.item_id)
                if not (item and item.is_consumable):
                    continue

            decision = self._build_decision(step, char_id, state)
            prev_round = state.round_number
            state = engine.process_round(
                state, {char_id: decision}, self.gd.enemies,
            )

            # Build action label
            if step.kind == ActionKind.SURVIVE:
                label = "SURVIVE"
            elif step.kind == ActionKind.CHEAT:
                label = f"CHEAT x{step.cheat_ap + 1} ({step.ability_id})"
            elif step.kind == ActionKind.ITEM:
                label = f"USE {step.item_id}"
            else:
                label = f"{step.ability_id}"

            summary = self._extract_round_summary(
                state, state.round_number, label, char_id,
            )
            round_summaries.append(summary)

        # Tally results
        player = state.get_combatant(char_id)
        player_hp = player.current_hp if player and player.is_alive else 0
        player_max = player.max_hp if player else 0
        enemies_dead = sum(1 for e in state.enemy_combatants if not e.is_alive)
        total_dmg_dealt = sum(r.damage_dealt for r in round_summaries)
        total_dmg_taken = sum(r.damage_taken for r in round_summaries)

        return EncounterResult(
            index=0,
            label="",
            rounds=state.round_number,
            player_won=state.player_won is True,
            player_hp=player_hp,
            player_max_hp=player_max,
            enemies_killed=enemies_dead,
            total_enemies=total_enemies,
            damage_dealt=total_dmg_dealt,
            damage_taken=total_dmg_taken,
            round_summaries=round_summaries,
        )

    # --- Full run ---

    def run(self, scenario: Scenario) -> SimResult:
        """Run a full scenario (multiple encounters with HP carry-over)."""
        if not scenario.cycle:
            scenario.cycle = [
                ActionStep(kind=ActionKind.SURVIVE),
                ActionStep(kind=ActionKind.SURVIVE),
                ActionStep(kind=ActionKind.SURVIVE),
                ActionStep(kind=ActionKind.CHEAT, cheat_ap=3),
            ]

        char = self._build_character(scenario)

        # Build encounters
        if scenario.zone_id:
            zone = self.gd.zones[scenario.zone_id]
            enc_list = self._build_encounters_from_zone(zone)
        elif scenario.encounters:
            enc_list = self._build_encounters_explicit(scenario.encounters)
        else:
            raise ValueError("Scenario must specify zone_id or encounters")

        results: list[EncounterResult] = []

        for idx, (enemies, label) in enumerate(enc_list):
            # Apply between-encounter actions (potions etc.)
            if idx in scenario.between_encounters:
                for step in scenario.between_encounters[idx]:
                    if step.kind == ActionKind.ITEM:
                        item = self.gd.items.get(step.item_id)
                        if item:
                            heal = item.heal_amount + int(char.max_hp * item.heal_percent)
                            char = char.model_copy(update={
                                "current_hp": min(char.max_hp, char.current_hp + heal),
                            })

            result = self._run_encounter(
                char, enemies, scenario.cycle, scenario.max_rounds,
            )
            result.index = idx
            result.label = label
            results.append(result)

            if not result.player_won:
                return SimResult(
                    encounter_results=results,
                    final_hp=0,
                    run_failed_at=idx,
                )

            # Carry over HP
            char = char.model_copy(update={"current_hp": result.player_hp})

        return SimResult(
            encounter_results=results,
            final_hp=char.current_hp,
        )


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_sim_result(result: SimResult, verbose: bool = True) -> str:
    """Format SimResult as human-readable text."""
    lines: list[str] = []

    for enc in result.encounter_results:
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  {enc.label}")
        lines.append("=" * 70)

        if verbose:
            for rs in enc.round_summaries:
                hp_str = f"HP {rs.player_hp}/{enc.player_max_hp}"
                # State tags: AP, debt, insight
                tags: list[str] = []
                if rs.player_ap > 0:
                    tags.append(f"AP={rs.player_ap}")
                if rs.cheat_debt > 0:
                    tags.append(f"debt={rs.cheat_debt}")
                if rs.insight_stacks > 0:
                    tags.append(f"insight={rs.insight_stacks}")
                tag_str = f"  [{', '.join(tags)}]" if tags else ""
                # Damage summary
                dmg_str = ""
                if rs.damage_dealt > 0:
                    dmg_str += f" dealt={rs.damage_dealt}"
                if rs.damage_taken > 0:
                    dmg_str += f" took={rs.damage_taken}"
                lines.append(f"  R{rs.round_num:>2} {rs.action:<30}{hp_str}{tag_str}{dmg_str}")
                for d in rs.details:
                    lines.append(f"      {d}")
                # Enemy HP bar
                if rs.enemy_hp:
                    ehp_parts = [f"{eid}={hp}" for eid, hp in rs.enemy_hp.items()]
                    lines.append(f"      enemies: {', '.join(ehp_parts)}")

        status = "WIN" if enc.player_won else "LOSS"
        lines.append(f"\n  [{status}] {enc.rounds} rounds"
                     f"  |  {enc.enemies_killed}/{enc.total_enemies} killed"
                     f"  |  HP {enc.player_hp}/{enc.player_max_hp}"
                     f"  |  dealt {enc.damage_dealt} / took {enc.damage_taken}")

    # Run summary
    lines.append("")
    lines.append("-" * 70)
    total_enc = len(result.encounter_results)
    won = sum(1 for e in result.encounter_results if e.player_won)
    if result.run_failed_at is not None:
        lines.append(f"  RUN FAILED at encounter {result.run_failed_at}"
                     f"  ({won}/{total_enc} encounters cleared)")
    else:
        lines.append(f"  RUN COMPLETE: {won}/{total_enc} encounters"
                     f"  |  Final HP: {result.final_hp}")

    return "\n".join(lines)
