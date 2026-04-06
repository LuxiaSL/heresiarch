"""Game loop orchestrator: ties combat, loot, XP, zones, shops, recruitment together.

Stateless orchestrator — all state lives in RunState.
All randomness through injected RNG.
Zero I/O.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    calculate_levels_gained,
    calculate_max_hp,
    calculate_stats_at_level,
    calculate_stats_from_history,
    calculate_xp_reward,
    xp_for_level,
)
from heresiarch.engine.models.combat_state import CombatState
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.stats import StatType
from heresiarch.engine.models.zone import ZoneState

STASH_LIMIT: int = 10


class GameLoop:
    """Orchestrates a run: combat -> loot -> XP -> zone progression."""

    def __init__(
        self,
        game_data: GameData,
        rng: random.Random | None = None,
    ):
        self.game_data = game_data
        self.rng = rng or random.Random()
        self.combat_engine = CombatEngine(
            ability_registry=game_data.abilities,
            item_registry=game_data.items,
            job_registry=game_data.jobs,
            rng=self.rng,
        )
        # Lazy imports to avoid circular deps at module level
        from heresiarch.engine.encounter import EncounterGenerator
        from heresiarch.engine.loot import LootResolver
        from heresiarch.engine.recruitment import RecruitmentEngine
        from heresiarch.engine.shop import ShopEngine

        self.loot_resolver = LootResolver(
            item_registry=game_data.items,
            drop_tables=game_data.drop_tables,
            rng=self.rng,
        )
        self.encounter_generator = EncounterGenerator(
            enemy_registry=game_data.enemies,
            combat_engine=self.combat_engine,
            rng=self.rng,
        )
        self.shop_engine = ShopEngine(item_registry=game_data.items)
        self.recruitment_engine = RecruitmentEngine(
            job_registry=game_data.jobs,
            rng=self.rng,
        )

    def new_run(self, run_id: str, mc_name: str, mc_job_id: str) -> RunState:
        """Initialize a new run with MC at level 1."""
        job = self.game_data.jobs[mc_job_id]
        stats = calculate_stats_at_level(job.growth, 1)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, 1, stats.DEF)

        mc = CharacterInstance(
            id=f"mc_{mc_job_id}",
            name=mc_name,
            job_id=mc_job_id,
            level=1,
            xp=0,
            base_stats=stats,
            current_hp=max_hp,
            abilities=[job.innate_ability_id],
            is_mc=True,
            growth_history=[(mc_job_id, 0)],
        )

        party = Party(
            active=[mc.id],
            characters={mc.id: mc},
        )

        return RunState(
            run_id=run_id,
            party=party,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def enter_zone(self, run: RunState, zone_id: str) -> RunState:
        """Begin a zone. Sets current_zone_id and zone_state."""
        if zone_id not in self.game_data.zones:
            raise ValueError(f"Unknown zone: {zone_id}")

        zone_state = ZoneState(template_id=zone_id)
        return run.model_copy(
            update={"current_zone_id": zone_id, "zone_state": zone_state}
        )

    def get_next_encounter(self, run: RunState) -> list[EnemyInstance]:
        """Generate the next encounter in current zone."""
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

        zone = self.game_data.zones[run.current_zone_id]
        idx = run.zone_state.current_encounter_index

        if idx >= len(zone.encounters):
            raise ValueError("No more encounters in this zone")

        encounter_template = zone.encounters[idx]
        return self.encounter_generator.generate_encounter(
            encounter_template, zone.zone_level
        )

    def resolve_combat_result(
        self,
        run: RunState,
        combat_result: CombatResult,
    ) -> tuple[RunState, LootResult]:
        """Post-combat: distribute XP, apply level-ups, roll loot, persist HP."""
        party = run.party
        zone = self.game_data.zones[run.current_zone_id] if run.current_zone_id else None
        xp_cap = zone.xp_cap_level if zone else 0

        if not combat_result.player_won:
            return self.handle_death(run), LootResult()

        # --- XP Distribution ---
        new_characters = dict(party.characters)
        for char_id in combat_result.surviving_character_ids:
            if char_id not in new_characters:
                continue
            char = new_characters[char_id]
            total_xp_gain = 0
            for budget_mult in combat_result.defeated_enemy_budget_multipliers:
                total_xp_gain += calculate_xp_reward(
                    zone_level=combat_result.zone_level,
                    budget_multiplier=budget_mult,
                    character_level=char.level,
                    xp_cap_level=xp_cap,
                )

            new_xp = char.xp + total_xp_gain
            levels_gained = calculate_levels_gained(new_xp, char.level)
            new_level = char.level + levels_gained

            # Recalculate stats at new level
            job = self.game_data.jobs[char.job_id]
            if char.is_mc and char.growth_history:
                # MC Mimic: update levels in current job segment
                history = list(char.growth_history)
                if history:
                    job_id, prev_levels = history[-1]
                    history[-1] = (job_id, prev_levels + levels_gained)
                new_stats = calculate_stats_from_history(history, self.game_data.jobs)
                new_hp = calculate_max_hp(
                    job.base_hp, job.hp_growth, new_level, new_stats.DEF
                )
                new_characters[char_id] = char.model_copy(
                    update={
                        "xp": new_xp,
                        "level": new_level,
                        "base_stats": new_stats,
                        "current_hp": min(char.current_hp, new_hp),
                        "growth_history": history,
                    }
                )
            else:
                new_stats = calculate_stats_at_level(job.growth, new_level)
                new_hp = calculate_max_hp(
                    job.base_hp, job.hp_growth, new_level, new_stats.DEF
                )
                new_characters[char_id] = char.model_copy(
                    update={
                        "xp": new_xp,
                        "level": new_level,
                        "base_stats": new_stats,
                        "current_hp": min(char.current_hp, new_hp),
                    }
                )

        # --- Loot ---
        defeated_instances: list[EnemyInstance] = []
        for tmpl_id in combat_result.defeated_enemy_template_ids:
            if tmpl_id in self.game_data.enemies:
                template = self.game_data.enemies[tmpl_id]
                instance = self.combat_engine.create_enemy_instance(
                    template, combat_result.zone_level
                )
                instance = instance.model_copy(update={"current_hp": 0})
                defeated_instances.append(instance)

        loot = self.loot_resolver.resolve_encounter_drops(
            defeated_enemies=defeated_instances,
            zone_level=combat_result.zone_level,
            party_cha=party.cha,
        )

        new_party = party.model_copy(
            update={
                "characters": new_characters,
                "money": party.money + loot.money,
            }
        )
        new_run = run.model_copy(update={"party": new_party})
        return new_run, loot

    def apply_loot(
        self,
        run: RunState,
        loot: LootResult,
        selected_items: list[str],
    ) -> RunState:
        """Add selected items to party stash. Enforce stash limit."""
        party = run.party
        new_stash = list(party.stash)
        new_items = dict(party.items)

        for item_id in selected_items:
            if len(new_stash) >= STASH_LIMIT:
                break
            if item_id in self.game_data.items:
                new_stash.append(item_id)
                new_items[item_id] = self.game_data.items[item_id]

        new_party = party.model_copy(
            update={"stash": new_stash, "items": new_items}
        )
        return run.model_copy(update={"party": new_party})

    def advance_zone(self, run: RunState) -> RunState:
        """Move to next encounter in zone. Mark zone cleared if done."""
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

        zone = self.game_data.zones[run.current_zone_id]
        new_idx = run.zone_state.current_encounter_index + 1
        completed = list(run.zone_state.encounters_completed)
        completed.append(run.zone_state.current_encounter_index)

        is_cleared = new_idx >= len(zone.encounters)

        new_zone_state = run.zone_state.model_copy(
            update={
                "current_encounter_index": new_idx,
                "encounters_completed": completed,
                "is_cleared": is_cleared,
            }
        )

        updates: dict = {"zone_state": new_zone_state}
        if is_cleared:
            zones_completed = list(run.zones_completed)
            zones_completed.append(run.current_zone_id)
            updates["zones_completed"] = zones_completed

        return run.model_copy(update=updates)

    def handle_death(self, run: RunState) -> RunState:
        """Mark run as dead."""
        return run.model_copy(update={"is_dead": True})

    def mc_swap_job(self, run: RunState, new_job_id: str) -> RunState:
        """MC swaps job. Update growth_history, recalculate stats going forward."""
        if new_job_id not in self.game_data.jobs:
            raise ValueError(f"Unknown job: {new_job_id}")

        party = run.party
        mc_id = None
        for char_id, char in party.characters.items():
            if char.is_mc:
                mc_id = char_id
                break

        if mc_id is None:
            raise ValueError("No MC in party")

        mc = party.characters[mc_id]
        new_job = self.game_data.jobs[new_job_id]

        # Update growth history: start new segment
        history = list(mc.growth_history)
        history.append((new_job_id, 0))

        # Recalculate stats from full history
        new_stats = calculate_stats_from_history(history, self.game_data.jobs)
        new_hp = calculate_max_hp(
            new_job.base_hp, new_job.hp_growth, mc.level, new_stats.DEF
        )

        new_mc = mc.model_copy(
            update={
                "job_id": new_job_id,
                "base_stats": new_stats,
                "current_hp": min(mc.current_hp, new_hp),
                "abilities": [new_job.innate_ability_id],
                "growth_history": history,
            }
        )

        new_characters = dict(party.characters)
        new_characters[mc_id] = new_mc
        new_party = party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})
