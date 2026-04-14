"""Game loop orchestrator: ties combat, loot, XP, zones, shops, recruitment together.

Stateless orchestrator — all state lives in RunState.
All randomness through injected RNG.
Zero I/O.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData
from heresiarch.engine.formulas import (
    RECRUITMENT_PITY_PER_CLEAR,
    calculate_effective_stats,
    calculate_endless_reward_multiplier,
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
from heresiarch.engine.models.jobs import AbilityUnlock, CharacterInstance
from heresiarch.engine.models.loot import LootResult
from heresiarch.engine.models.party import STASH_LIMIT, Party
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.stats import StatBlock, StatType
from heresiarch.engine.models.zone import ZoneState, ZoneTemplate


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
            enemy_registry=game_data.enemies,
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
            item_registry=game_data.items,
            rng=self.rng,
        )

    def rehydrate_run(self, run: RunState) -> RunState:
        """Recompute all derived fields after loading a save.

        Derived fields (effective_stats, max_hp) depend on game data (job
        templates, item definitions, formula constants) which can change
        between saves.  Always call this after deserializing a RunState.
        """
        new_characters = dict(run.party.characters)
        for char_id, char in new_characters.items():
            new_characters[char_id] = self._recompute_derived(char, run.party)
            # Cap current_hp to recomputed max_hp (but don't raise it)
            rehydrated = new_characters[char_id]
            if rehydrated.current_hp > rehydrated.max_hp:
                new_characters[char_id] = rehydrated.model_copy(
                    update={"current_hp": rehydrated.max_hp}
                )
        new_party = run.party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})

    def _check_ability_unlocks(
        self, char: CharacterInstance, old_level: int, new_level: int
    ) -> CharacterInstance:
        """Grant any abilities unlocked between old_level+1 and new_level."""
        job = self.game_data.jobs.get(char.job_id)
        if job is None:
            return char
        new_abilities = list(char.abilities)
        new_unlocks: list[str] = []
        for unlock in job.ability_unlocks:
            if old_level < unlock.level <= new_level:
                if unlock.ability_id not in new_abilities:
                    new_abilities.append(unlock.ability_id)
                    new_unlocks.append(unlock.ability_id)
        if new_abilities != char.abilities:
            # Update breakpoints source if tracking is active
            sources = dict(char.ability_sources) if char.ability_sources else {}
            if sources:
                bp = list(sources.get("breakpoints", []))
                bp.extend(new_unlocks)
                sources["breakpoints"] = bp
            return char.model_copy(update={
                "abilities": new_abilities,
                "ability_sources": sources if sources else char.ability_sources,
            })
        return char

    def _rebuild_abilities(
        self,
        char: CharacterInstance,
        equipment: dict[str, str | None],
        item_lookup: dict[str, Item],
    ) -> dict[str, Any]:
        """Rebuild ability list from tracked sources.

        Returns a dict suitable for model_copy(update=...) containing
        both 'abilities' (flat list) and 'ability_sources' (source tracker).

        Each source is independent — changing equipment only touches the
        'equipment' source, not 'learned'.
        """
        job = self.game_data.jobs.get(char.job_id)
        innate_id = job.innate_ability_id if job else ""

        # Core: basic_attack (always present)
        core: list[str] = ["basic_attack"]

        # Innate: job innate ability
        innate: list[str] = [innate_id] if innate_id else []

        # Breakpoints: level-gated unlocks
        breakpoints: list[str] = []
        if job:
            for unlock in job.ability_unlocks:
                if unlock.level <= char.level:
                    breakpoints.append(unlock.ability_id)

        # Equipment-granted
        equip_abilities: list[str] = []
        for _slot, eid in equipment.items():
            if eid:
                item = item_lookup.get(eid) or self.game_data.items.get(eid)
                if item and item.granted_ability_id:
                    equip_abilities.append(item.granted_ability_id)

        # Learned: scroll-taught and other permanent abilities.
        # Preserve from existing sources if tracked, otherwise extract from
        # the current flat list (backwards compatibility for old saves).
        if char.ability_sources and "learned" in char.ability_sources:
            learned = list(char.ability_sources["learned"])
        else:
            # Anything on the flat list that isn't from the other sources
            known = set(core + innate + breakpoints + equip_abilities)
            learned = [aid for aid in char.abilities if aid not in known]

        sources = {
            "core": core,
            "innate": innate,
            "breakpoints": breakpoints,
            "equipment": equip_abilities,
            "learned": learned,
        }

        char_with_sources = char.model_copy(update={"ability_sources": sources})
        return {
            "abilities": char_with_sources.get_all_abilities(),
            "ability_sources": sources,
        }

    def _resolve_equipped_items(self, char: CharacterInstance, party: Party | None = None) -> list[Item]:
        """Resolve a character's equipment IDs to Item objects."""
        equipped: list[Item] = []
        for item_id in char.equipment.values():
            if item_id:
                item = (party.items.get(item_id) if party else None) or self.game_data.items.get(item_id)
                if item:
                    equipped.append(item)
        return equipped

    def _recompute_derived(self, char: CharacterInstance, party: Party | None = None) -> CharacterInstance:
        """Recompute effective_stats and max_hp from base_stats + equipment.

        Call this after ANY change to base_stats, equipment, or job.
        """
        equipped = self._resolve_equipped_items(char, party)
        effective = calculate_effective_stats(char.base_stats, equipped, [])
        job = self.game_data.jobs.get(char.job_id)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, char.level, effective.DEF) if job else 0
        return char.model_copy(update={
            "effective_stats": effective,
            "max_hp": max_hp,
        })

    def preview_equipment_change(
        self,
        char: CharacterInstance,
        party: Party,
        slot: str,
        new_item_id: str | None,
    ) -> tuple[StatBlock, int]:
        """Simulate an equipment change and return preview stats without mutating state.

        Returns (preview_effective_stats, preview_max_hp).
        """
        # Build hypothetical equipment dict
        hypothetical_equipment = dict(char.equipment)
        hypothetical_equipment[slot] = new_item_id

        # Resolve items from the hypothetical loadout
        equipped: list[Item] = []
        for item_id in hypothetical_equipment.values():
            if item_id:
                item = party.items.get(item_id) or self.game_data.items.get(item_id)
                if item:
                    equipped.append(item)

        effective = calculate_effective_stats(char.base_stats, equipped, [])
        job = self.game_data.jobs.get(char.job_id)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, char.level, effective.DEF) if job else 0
        return effective, max_hp

    def new_run(self, run_id: str, mc_name: str, mc_job_id: str) -> RunState:
        """Initialize a new run with MC at level 1."""
        job = self.game_data.jobs[mc_job_id]
        stats = calculate_stats_at_level(job.growth, 1)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, 1, stats.DEF)

        # Start with basic_attack + innate, then check for Lv1 breakpoints
        starting_abilities = ["basic_attack", job.innate_ability_id]
        for unlock in job.ability_unlocks:
            if unlock.level <= 1 and unlock.ability_id not in starting_abilities:
                starting_abilities.append(unlock.ability_id)

        mc = CharacterInstance(
            id=f"mc_{mc_job_id}",
            name=mc_name,
            job_id=mc_job_id,
            level=1,
            xp=0,
            base_stats=stats,
            effective_stats=stats,  # No equipment yet
            current_hp=max_hp,
            max_hp=max_hp,
            abilities=starting_abilities,
            is_mc=True,
            growth_history=[(mc_job_id, 1)],
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

    # --- Zone Navigation ---

    def is_zone_unlocked(self, run: RunState, zone_id: str) -> bool:
        """Check whether a zone's unlock requirements are all met."""
        zone = self.game_data.zones.get(zone_id)
        if zone is None:
            return False
        for req in zone.unlock_requires:
            if req.type == "zone_clear":
                if req.zone_id not in run.zones_completed:
                    return False
            elif req.type == "item":
                if req.item_id not in run.party.stash:
                    return False
            elif req.type == "level":
                mc = self._get_mc(run)
                if mc is None or mc.level < (req.level or 0):
                    return False
        return True

    def get_available_zones(self, run: RunState) -> list[ZoneTemplate]:
        """Return all zones the player can currently enter, sorted by zone_level."""
        available = [
            zone
            for zone in self.game_data.zones.values()
            if self.is_zone_unlocked(run, zone.id)
        ]
        available.sort(key=lambda z: z.zone_level)
        return available

    def enter_zone(self, run: RunState, zone_id: str) -> RunState:
        """Begin a zone. Sets current_zone_id and zone_state.

        Restores saved progress if the player previously left mid-zone.
        Re-entering a cleared zone starts in overstay mode (is_cleared=True).
        """
        if zone_id not in self.game_data.zones:
            raise ValueError(f"Unknown zone: {zone_id}")

        # Restore saved progress if it exists
        saved = run.zone_progress.get(zone_id)
        if saved is not None:
            return run.model_copy(
                update={"current_zone_id": zone_id, "zone_state": saved}
            )

        already_cleared = zone_id in run.zones_completed
        zone_state = ZoneState(
            template_id=zone_id,
            is_cleared=already_cleared,
        )
        return run.model_copy(
            update={"current_zone_id": zone_id, "zone_state": zone_state}
        )

    def leave_zone(self, run: RunState) -> RunState:
        """Exit the current zone and save progress. HP persists."""
        new_progress = dict(run.zone_progress)
        if run.current_zone_id and run.zone_state:
            new_progress[run.current_zone_id] = run.zone_state
        run = run.model_copy(update={"zone_progress": new_progress})
        return run.model_copy(
            update={"current_zone_id": None, "zone_state": None}
        )

    # --- Town Navigation ---

    def get_region_for_run(self, run: RunState) -> str | None:
        """Determine the player's current region from zone context."""
        if run.current_zone_id:
            zone = self.game_data.zones.get(run.current_zone_id)
            return zone.region if zone else None
        if run.current_town_id:
            town = self.game_data.towns.get(run.current_town_id)
            return town.region if town else None
        if run.zones_completed:
            last = self.game_data.zones.get(run.zones_completed[-1])
            return last.region if last else None
        # Default: first town's region (game starts in town)
        if self.game_data.towns:
            return next(iter(self.game_data.towns.values())).region
        return None

    def get_town_for_region(self, region: str | None) -> Any:
        """Find the TownTemplate for a region, or None."""
        if not region:
            return None
        for town in self.game_data.towns.values():
            if town.region == region:
                return town
        return None

    def is_town_unlocked(self, run: RunState, town_id: str) -> bool:
        """Check whether a town's unlock requirements are met."""
        town = self.game_data.towns.get(town_id)
        if town is None:
            return False
        for req in town.unlock_requires:
            if req.type == "zone_clear":
                if req.zone_id not in run.zones_completed:
                    return False
        return True

    def enter_town(self, run: RunState, town_id: str) -> RunState:
        """Enter a town. Mutually exclusive with being in a zone."""
        if town_id not in self.game_data.towns:
            raise ValueError(f"Unknown town: {town_id}")
        if run.current_zone_id:
            raise ValueError("Cannot enter town while in a zone — leave zone first")
        if not self.is_town_unlocked(run, town_id):
            raise ValueError(f"Town '{town_id}' is not unlocked yet")
        return run.model_copy(update={"current_town_id": town_id})

    def leave_town(self, run: RunState) -> RunState:
        """Leave the current town."""
        return run.model_copy(update={"current_town_id": None})

    def resolve_town_shop(self, run: RunState) -> list[str]:
        """Compute available shop items from the current region's town progression."""
        region = self.get_region_for_run(run)
        town = self.get_town_for_region(region)
        if not town:
            return []
        items: list[str] = []
        for tier in town.shop_tiers:
            if tier.zone_clear is None or tier.zone_clear in run.zones_completed:
                items.extend(tier.items)
        return items

    def rest_at_lodge(self, run: RunState) -> RunState:
        """Full party heal. Resets incomplete zone progress. Costs gold.

        Must be in a town. Resets encounter progress for all incomplete
        zones — re-cleared encounters give zero rewards until the player
        reaches new encounters past their previous high-water mark.
        """
        if not run.current_town_id:
            raise ValueError("Must be in a town to rest at the lodge")

        town = self.game_data.towns.get(run.current_town_id)
        if not town:
            raise ValueError(f"Unknown town: {run.current_town_id}")

        cost = self._compute_lodge_cost(run, town)

        if run.party.money < cost:
            raise ValueError(
                f"Insufficient funds: have {run.party.money}, need {cost}"
            )

        # 1. Full heal all characters
        new_characters = dict(run.party.characters)
        for char_id in run.party.active + run.party.reserve:
            char = new_characters.get(char_id)
            if char and char.current_hp < char.max_hp:
                new_characters[char_id] = char.model_copy(
                    update={"current_hp": char.max_hp}
                )

        # 2. Reset zone progress for incomplete zones
        new_lodge_resets = dict(run.lodge_reset_zones)
        new_zone_progress = dict(run.zone_progress)

        for zone_id, zstate in list(run.zone_progress.items()):
            if not zstate.is_cleared:
                # Track high-water mark for reward suppression
                new_lodge_resets[zone_id] = max(
                    zstate.current_encounter_index,
                    new_lodge_resets.get(zone_id, 0),
                )
                del new_zone_progress[zone_id]

        # 3. Deduct gold
        new_party = run.party.model_copy(
            update={
                "characters": new_characters,
                "money": run.party.money - cost,
            }
        )

        return run.model_copy(
            update={
                "party": new_party,
                "lodge_reset_zones": new_lodge_resets,
                "zone_progress": new_zone_progress,
                "current_zone_id": None,
                "zone_state": None,
            }
        )

    def _compute_lodge_cost(self, run: RunState, town: Any) -> int:
        """Compute lodge cost based on party's missing HP.

        cost = max(floor, missing_hp_total * gold_per_hp)
        floor = floor_base + floor_per_level * mc_level
        """
        mc = self._get_mc(run)
        mc_level = mc.level if mc else 1
        floor = town.lodge_floor_base + town.lodge_floor_per_level * mc_level

        missing_hp = 0
        for char_id in run.party.active + run.party.reserve:
            char = run.party.characters.get(char_id)
            if char:
                missing_hp += max(0, char.max_hp - char.current_hp)

        return max(floor, int(missing_hp * town.lodge_gold_per_hp))

    def get_lodge_cost(self, run: RunState) -> int | None:
        """Return the lodge rest cost for the current town, or None."""
        if not run.current_town_id:
            return None
        town = self.game_data.towns.get(run.current_town_id)
        if not town:
            return None
        return self._compute_lodge_cost(run, town)

    def try_recruitment(self, run: RunState) -> tuple[RunState, Any]:
        """Roll for a recruitment encounter after a non-boss combat.

        Returns (updated_run, candidate) where candidate is a RecruitCandidate
        if the roll succeeds, or None otherwise. Updates zone_state to mark
        recruitment as offered.
        """
        from heresiarch.engine.recruitment import RecruitCandidate

        if not run.current_zone_id or not run.zone_state:
            return run, None
        if run.zone_state.recruitment_offered:
            return run, None

        zone = self.game_data.zones.get(run.current_zone_id)
        if not zone or zone.recruitment_chance <= 0:
            return run, None

        pity_bonus = len(run.zone_state.encounters_completed) * RECRUITMENT_PITY_PER_CLEAR
        effective_chance = min(1.0, zone.recruitment_chance + pity_bonus)

        roll = self.rng.random()
        if roll >= effective_chance:
            return run, None

        exclude: list[str] = []
        if run.last_recruit_job_id:
            exclude.append(run.last_recruit_job_id)

        candidate: RecruitCandidate = self.recruitment_engine.generate_candidate(
            zone_level=zone.zone_level,
            exclude_job_ids=exclude,
            shop_pool=self.resolve_town_shop(run),
            level_range=zone.enemy_level_range,
        )

        new_zone_state = run.zone_state.model_copy(
            update={"recruitment_offered": True},
        )
        run = run.model_copy(update={"zone_state": new_zone_state})
        return run, candidate

    def get_next_encounter(self, run: RunState) -> list[EnemyInstance]:
        """Generate the next encounter in current zone.

        Endless zones always generate dynamic encounters from their enemy pool.
        In overstay mode (zone already cleared), generates a random
        non-boss encounter from the zone's template list.
        """
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

        zone = self.game_data.zones[run.current_zone_id]

        # Endless zones: always dynamic encounters, never run out
        if zone.is_endless:
            mc = self._get_mc(run)
            player_level = mc.level if mc else zone.endless_min_level
            return self.encounter_generator.generate_endless_encounter(
                enemy_pool=zone.endless_enemy_pool,
                player_level=player_level,
                min_level=zone.endless_min_level,
                max_level=zone.endless_max_level,
            )

        spawns = zone.random_spawns or None
        level_range = zone.enemy_level_range

        if run.zone_state.is_cleared:
            # Overstay: pick a random non-boss encounter
            non_boss = [e for e in zone.encounters if not e.is_boss]
            if not non_boss:
                non_boss = zone.encounters  # fallback: all encounters
            encounter_template = self.rng.choice(non_boss)
            return self.encounter_generator.generate_encounter(
                encounter_template, zone.zone_level,
                random_spawns=spawns, enemy_level_range=level_range,
            )

        idx = run.zone_state.current_encounter_index
        if idx >= len(zone.encounters):
            raise ValueError("No more encounters in this zone")

        encounter_template = zone.encounters[idx]
        return self.encounter_generator.generate_encounter(
            encounter_template, zone.zone_level,
            random_spawns=spawns, enemy_level_range=level_range,
            encounter_index=idx, total_encounters=len(zone.encounters),
        )

    def _get_mc(self, run: RunState) -> CharacterInstance | None:
        """Return the MC character, or None."""
        for char in run.party.characters.values():
            if char.is_mc:
                return char
        return None

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

        # Lodge reset reward suppression: encounters the player already
        # cleared before resting give zero XP, gold, and loot.
        lodge_cap = run.lodge_reset_zones.get(run.current_zone_id or "")
        suppress_rewards = (
            lodge_cap is not None
            and run.zone_state is not None
            and not run.zone_state.is_cleared  # overstay always pays
            and run.zone_state.current_encounter_index < lodge_cap
        )

        # Overstay XP penalty (same curve as loot: -5% per battle, floor 10%)
        overstay = run.zone_state.overstay_battles if run.zone_state else 0
        from heresiarch.engine.loot import OVERSTAY_PENALTY_PER_BATTLE
        overstay_xp_mult = max(0.0, 1.0 - OVERSTAY_PENALTY_PER_BATTLE * overstay)

        # Endless zone reward tapering: diminishing XP as player nears cap
        endless_mult = 1.0
        if zone and zone.is_endless:
            mc = self._get_mc(run)
            player_level = mc.level if mc else 0
            endless_mult = calculate_endless_reward_multiplier(
                player_level=player_level,
                zone_max_level=zone.endless_max_level,
            )

        # --- XP Distribution + HP Persistence ---
        new_characters = dict(party.characters)
        for char_id in combat_result.surviving_character_ids:
            if char_id not in new_characters:
                continue
            char = new_characters[char_id]
            total_xp_gain = 0

            # Use per-enemy levels when available, fall back to zone_level
            enemy_levels = combat_result.defeated_enemy_levels
            xp_mults = combat_result.defeated_enemy_xp_multipliers
            budget_mults = combat_result.defeated_enemy_budget_multipliers

            for idx, budget_mult in enumerate(budget_mults):
                # Per-enemy level (new) or zone_level (backward compat)
                e_level = enemy_levels[idx] if idx < len(enemy_levels) else combat_result.zone_level
                # Per-enemy XP multiplier override, or use budget_multiplier
                xp_mult = xp_mults[idx] if idx < len(xp_mults) and xp_mults[idx] > 0 else budget_mult
                total_xp_gain += calculate_xp_reward(
                    enemy_level=e_level,
                    budget_multiplier=xp_mult,
                    character_level=char.level,
                    xp_cap_level=xp_cap,
                )
            total_xp_gain = int(total_xp_gain * overstay_xp_mult * endless_mult)
            if suppress_rewards:
                total_xp_gain = 0

            new_xp = char.xp + total_xp_gain
            levels_gained = calculate_levels_gained(new_xp, char.level)
            new_level = char.level + levels_gained

            # Post-combat HP: use surviving HP from combat, capped at current max
            surviving_hp = combat_result.surviving_character_hp.get(
                char_id, char.current_hp
            )

            if levels_gained == 0:
                # No level-up: just persist XP and surviving HP
                updated = char.model_copy(update={"xp": new_xp})
                updated = self._recompute_derived(updated, run.party)
                updated = updated.model_copy(
                    update={"current_hp": min(surviving_hp, updated.max_hp)}
                )
                new_characters[char_id] = updated
            else:
                # Recalculate stats at new level
                job = self.game_data.jobs[char.job_id]
                if char.is_mc and char.growth_history:
                    history = list(char.growth_history)
                    if history:
                        job_id, prev_levels = history[-1]
                        history[-1] = (job_id, prev_levels + levels_gained)
                    new_stats = calculate_stats_from_history(
                        history, self.game_data.jobs
                    )
                    updated = char.model_copy(
                        update={
                            "xp": new_xp,
                            "level": new_level,
                            "base_stats": new_stats,
                            "growth_history": history,
                        }
                    )
                else:
                    new_stats = calculate_stats_at_level(job.growth, new_level)
                    updated = char.model_copy(
                        update={
                            "xp": new_xp,
                            "level": new_level,
                            "base_stats": new_stats,
                        }
                    )
                # Check for ability unlocks at new level
                updated = self._check_ability_unlocks(updated, char.level, new_level)
                # Recompute effective stats (equipment scaling changes with new base)
                updated = self._recompute_derived(updated, run.party)
                updated = updated.model_copy(
                    update={"current_hp": min(surviving_hp, updated.max_hp)}
                )
                new_characters[char_id] = updated

        # --- Loot ---
        defeated_instances: list[EnemyInstance] = []
        for idx, tmpl_id in enumerate(combat_result.defeated_enemy_template_ids):
            if tmpl_id in self.game_data.enemies:
                template = self.game_data.enemies[tmpl_id]
                # Use per-enemy level when available, fall back to zone_level
                e_level = (
                    enemy_levels[idx]
                    if idx < len(enemy_levels)
                    else combat_result.zone_level
                )
                instance = self.combat_engine.create_enemy_instance(
                    template, e_level
                )
                instance = instance.model_copy(update={"current_hp": 0})
                defeated_instances.append(instance)

        overstay = run.zone_state.overstay_battles if run.zone_state else 0
        # Pass encounter template for loot overrides
        enc_template = None
        if zone and run.zone_state:
            enc_idx = run.zone_state.current_encounter_index
            if 0 <= enc_idx < len(zone.encounters):
                enc_template = zone.encounters[enc_idx]
        loot = self.loot_resolver.resolve_encounter_drops(
            defeated_enemies=defeated_instances,
            party_cha=party.cha,
            overstay_battles=overstay,
            zone_level=zone.zone_level if zone else 0,
            encounter_template=enc_template,
        )

        # Apply endless zone gold tapering to loot money
        loot_money = int(loot.money * endless_mult)

        # Lodge reset: zero out gold and loot for re-cleared encounters
        if suppress_rewards:
            loot_money = 0
            loot = LootResult()

        # Apply gold: loot gains, minus stolen by enemies, plus stolen by players
        net_gold = (
            party.money
            + loot_money
            - combat_result.gold_stolen_by_enemies
            + combat_result.gold_stolen_by_players
        )
        new_party = party.model_copy(
            update={
                "characters": new_characters,
                "money": max(0, net_gold),
            }
        )
        new_run = run.model_copy(update={"party": new_party})
        return new_run, loot

    def apply_loot(
        self,
        run: RunState,
        loot: LootResult,
        selected_items: list[str],
        discard_items: list[str] | None = None,
    ) -> RunState:
        """Add selected items to party stash. Enforce stash limit.

        Optionally discard existing stash items first to free space.
        """
        party = run.party
        new_stash = list(party.stash)
        new_items = dict(party.items)

        # Remove discarded stash items first to free space
        if discard_items:
            for item_id in discard_items:
                try:
                    new_stash.remove(item_id)
                except ValueError:
                    pass  # Already removed or not in stash

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
        """Move to next encounter in zone. Mark zone cleared if done.

        Endless zones never clear — always bumps the encounter counter.
        In overstay mode, increments the overstay counter instead.
        """
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

        zone = self.game_data.zones[run.current_zone_id]

        # Endless zones never clear — just track battles for recruitment etc.
        if zone.is_endless:
            new_zone_state = run.zone_state.model_copy(
                update={
                    "overstay_battles": run.zone_state.overstay_battles + 1,
                }
            )
            new_progress = dict(run.zone_progress)
            new_progress[run.current_zone_id] = new_zone_state
            return run.model_copy(update={
                "zone_state": new_zone_state,
                "zone_progress": new_progress,
            })

        # Overstay mode — bump the counter and sync to zone_progress
        if run.zone_state.is_cleared:
            new_zone_state = run.zone_state.model_copy(
                update={
                    "overstay_battles": run.zone_state.overstay_battles + 1,
                }
            )
            new_progress = dict(run.zone_progress)
            if run.current_zone_id:
                new_progress[run.current_zone_id] = new_zone_state
            return run.model_copy(update={
                "zone_state": new_zone_state,
                "zone_progress": new_progress,
            })

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

        # Clear lodge reset suppression once player passes the high-water mark
        lodge_cap = run.lodge_reset_zones.get(run.current_zone_id)
        if lodge_cap is not None and new_idx >= lodge_cap:
            new_resets = dict(run.lodge_reset_zones)
            del new_resets[run.current_zone_id]
            updates["lodge_reset_zones"] = new_resets

        if is_cleared:
            zones_completed = list(run.zones_completed)
            if run.current_zone_id not in zones_completed:
                zones_completed.append(run.current_zone_id)
            updates["zones_completed"] = zones_completed
            # Sync cleared state to zone_progress
            new_progress = dict(run.zone_progress)
            if run.current_zone_id:
                new_progress[run.current_zone_id] = new_zone_state
            updates["zone_progress"] = new_progress

        return run.model_copy(update=updates)

    def handle_death(self, run: RunState) -> RunState:
        """Mark run as dead."""
        return run.model_copy(update={"is_dead": True})

    def dismiss_character(self, run: RunState, character_id: str) -> RunState:
        """Dismiss a party member. They leave with all equipped gear.

        Cannot dismiss the MC or the last active party member.
        Returns updated RunState with character and their items removed.
        """
        party = run.party
        if character_id not in party.characters:
            raise ValueError(f"Character {character_id!r} not in party")

        char = party.characters[character_id]
        if char.is_mc:
            raise ValueError("Cannot dismiss the MC")

        if character_id in party.active and len(party.active) <= 1:
            raise ValueError("Cannot dismiss the last active party member")

        # Remove from active or reserve
        new_active = [cid for cid in party.active if cid != character_id]
        new_reserve = [cid for cid in party.reserve if cid != character_id]

        # Remove character
        new_characters = {
            cid: c for cid, c in party.characters.items()
            if cid != character_id
        }

        # Remove their equipped items from party inventory
        dismissed_item_ids: set[str] = set()
        for slot, item_id in char.equipment.items():
            if item_id:
                dismissed_item_ids.add(item_id)
        new_items = {
            iid: item for iid, item in party.items.items()
            if iid not in dismissed_item_ids
        }

        new_party = party.model_copy(
            update={
                "active": new_active,
                "reserve": new_reserve,
                "characters": new_characters,
                "items": new_items,
            }
        )
        return run.model_copy(update={"party": new_party})

    def mc_swap_job(self, run: RunState, new_job_id: str) -> RunState:
        """MC swaps job. Update growth_history, recalculate stats going forward.

        The target job must belong to a non-MC party member (mimic constraint).
        """
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

        # Mimic constraint: job must belong to a current non-MC party member
        party_job_ids = {
            char.job_id for cid, char in party.characters.items()
            if not char.is_mc
        }
        if new_job_id not in party_job_ids:
            raise ValueError(
                f"Cannot mimic job {new_job_id!r} — no party member has it. "
                f"Available: {sorted(party_job_ids)}"
            )

        mc = party.characters[mc_id]
        if mc.job_id == new_job_id:
            raise ValueError(f"MC already has job {new_job_id!r}")

        new_job = self.game_data.jobs[new_job_id]

        # Update growth history: start new segment
        history = list(mc.growth_history)
        history.append((new_job_id, 0))

        # Recalculate stats from full history + recompute derived
        new_stats = calculate_stats_from_history(history, self.game_data.jobs)

        # Strip old job's innate/breakpoint abilities, keep scroll-taught
        old_job = self.game_data.jobs.get(mc.job_id)
        old_job_ability_ids: set[str] = set()
        if old_job:
            old_job_ability_ids.add(old_job.innate_ability_id)
            for unlock in old_job.ability_unlocks:
                old_job_ability_ids.add(unlock.ability_id)
        scroll_abilities = [
            a for a in mc.abilities
            if a not in old_job_ability_ids and a != "basic_attack"
        ]

        # Temporarily set the new job + scroll abilities, then let
        # _rebuild_abilities fill in new innate, breakpoints, and equipment
        new_mc = mc.model_copy(
            update={
                "job_id": new_job_id,
                "base_stats": new_stats,
                "abilities": scroll_abilities,
                "growth_history": history,
            }
        )
        ability_update = self._rebuild_abilities(new_mc, mc.equipment, party.items)
        new_mc = new_mc.model_copy(update=ability_update)
        new_mc = self._recompute_derived(new_mc, party)
        new_mc = new_mc.model_copy(
            update={"current_hp": min(mc.current_hp, new_mc.max_hp)}
        )

        new_characters = dict(party.characters)
        new_characters[mc_id] = new_mc
        new_party = party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})

    # --- Equipment Management ---

    def equip_item(
        self, run: RunState, character_id: str, item_id: str, slot: str
    ) -> RunState:
        """Equip an item from stash onto a character's slot.

        If the slot is occupied, the old item goes back to stash.
        Raises ValueError if character/item not found or slot invalid.
        """
        party = run.party
        if character_id not in party.characters:
            raise ValueError(f"Unknown character: {character_id}")
        if item_id not in party.stash:
            raise ValueError(f"Item '{item_id}' not in stash")
        if slot not in ("WEAPON", "ARMOR", "ACCESSORY_1", "ACCESSORY_2"):
            raise ValueError(f"Invalid slot: {slot}")

        item = self.game_data.items.get(item_id) or party.items.get(item_id)
        if item is None:
            raise ValueError(f"Item data not found: {item_id}")
        if item.is_consumable:
            raise ValueError("Cannot equip a consumable")

        char = party.characters[character_id]
        new_stash = list(party.stash)
        new_items = dict(party.items)
        new_equipment = dict(char.equipment)

        # Unequip current item in slot if any
        old_item_id = new_equipment.get(slot)
        if old_item_id:
            new_stash.append(old_item_id)

        # Equip new item
        new_stash.remove(item_id)
        new_equipment[slot] = item_id
        new_items[item_id] = item

        ability_update = self._rebuild_abilities(char, new_equipment, new_items)

        new_char = char.model_copy(
            update={"equipment": new_equipment, **ability_update}
        )
        new_characters = dict(party.characters)
        new_characters[character_id] = new_char
        new_party = party.model_copy(
            update={"characters": new_characters, "stash": new_stash, "items": new_items}
        )
        # Recompute derived stats and cap HP
        new_char = self._recompute_derived(new_char, new_party)
        if new_char.current_hp > new_char.max_hp:
            new_char = new_char.model_copy(update={"current_hp": new_char.max_hp})
        new_characters[character_id] = new_char
        new_party = new_party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})

    def unequip_item(
        self, run: RunState, character_id: str, slot: str
    ) -> RunState:
        """Unequip item from a slot back to stash.

        Raises ValueError if slot is empty or stash is full.
        """
        party = run.party
        if character_id not in party.characters:
            raise ValueError(f"Unknown character: {character_id}")

        char = party.characters[character_id]
        item_id = char.equipment.get(slot)
        if not item_id:
            raise ValueError(f"Slot '{slot}' is empty")
        if len(party.stash) >= STASH_LIMIT:
            raise ValueError("Stash is full")

        new_stash = list(party.stash) + [item_id]
        new_equipment = dict(char.equipment)
        new_equipment[slot] = None

        ability_update = self._rebuild_abilities(char, new_equipment, party.items)

        new_char = char.model_copy(update={"equipment": new_equipment, **ability_update})
        new_characters = dict(party.characters)
        new_characters[character_id] = new_char
        new_party = party.model_copy(
            update={"characters": new_characters, "stash": new_stash}
        )
        # Recompute derived stats and cap HP
        new_char = self._recompute_derived(new_char, new_party)
        if new_char.current_hp > new_char.max_hp:
            new_char = new_char.model_copy(update={"current_hp": new_char.max_hp})
        new_characters[character_id] = new_char
        new_party = new_party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})

    # --- Party Management ---

    def swap_party_member(
        self, run: RunState, active_id: str, reserve_id: str
    ) -> RunState:
        """Swap an active party member with a reserve member."""
        party = run.party
        if active_id not in party.active:
            raise ValueError(f"'{active_id}' is not in active roster")
        if reserve_id not in party.reserve:
            raise ValueError(f"'{reserve_id}' is not in reserve")

        new_active = [reserve_id if x == active_id else x for x in party.active]
        new_reserve = [active_id if x == reserve_id else x for x in party.reserve]

        new_party = party.model_copy(
            update={"active": new_active, "reserve": new_reserve}
        )
        return run.model_copy(update={"party": new_party})

    def promote_to_active(self, run: RunState, reserve_id: str) -> RunState:
        """Move a reserve member to active. Requires an open active slot."""
        from heresiarch.engine.recruitment import MAX_ACTIVE_SIZE

        party = run.party
        if reserve_id not in party.reserve:
            raise ValueError(f"'{reserve_id}' is not in reserve")
        if len(party.active) >= MAX_ACTIVE_SIZE:
            raise ValueError("Active party is full")

        new_active = list(party.active) + [reserve_id]
        new_reserve = [r for r in party.reserve if r != reserve_id]
        new_party = party.model_copy(
            update={"active": new_active, "reserve": new_reserve}
        )
        return run.model_copy(update={"party": new_party})

    def bench_to_reserve(self, run: RunState, active_id: str) -> RunState:
        """Move an active member to reserve."""
        party = run.party
        if active_id not in party.active:
            raise ValueError(f"'{active_id}' is not in active roster")
        if len(party.active) <= 1:
            raise ValueError("Cannot bench your last active member")

        new_active = [a for a in party.active if a != active_id]
        new_reserve = list(party.reserve) + [active_id]
        new_party = party.model_copy(
            update={"active": new_active, "reserve": new_reserve}
        )
        return run.model_copy(update={"party": new_party})

    # --- Scrolls ---

    def use_teach_scroll(
        self, run: RunState, item_id: str, target_character_id: str
    ) -> RunState:
        """Use a permanent teach scroll: consume it, grant ability to character."""
        party = run.party
        if item_id not in party.stash:
            raise ValueError(f"Item '{item_id}' not in stash")
        if target_character_id not in party.characters:
            raise ValueError(f"Unknown character: {target_character_id}")

        item = self.game_data.items.get(item_id) or party.items.get(item_id)
        if item is None or not item.is_consumable or not item.teaches_ability_id:
            raise ValueError(f"'{item_id}' is not a teach scroll")

        char = party.characters[target_character_id]
        ability_id = item.teaches_ability_id

        # Bootstrap ability_sources if empty (fresh character / old save)
        if not char.ability_sources:
            bootstrap = self._rebuild_abilities(char, char.equipment, party.items)
            char = char.model_copy(update=bootstrap)

        # Check learned source specifically — equipment-granted abilities
        # shouldn't block permanently learning via scroll.
        sources = dict(char.ability_sources)
        learned = list(sources.get("learned", []))
        update: dict[str, Any] = {}
        if ability_id not in learned:
            learned.append(ability_id)
            sources["learned"] = learned
            update["ability_sources"] = sources
            # Rebuild flat list from sources so it stays in sync
            new_abilities = list(char.abilities)
            if ability_id not in new_abilities:
                new_abilities.append(ability_id)
            update["abilities"] = new_abilities

        new_char = char.model_copy(update=update)

        # Remove scroll from stash
        new_stash = list(party.stash)
        new_stash.remove(item_id)

        new_characters = dict(party.characters)
        new_characters[target_character_id] = new_char
        new_party = party.model_copy(
            update={"characters": new_characters, "stash": new_stash}
        )
        return run.model_copy(update={"party": new_party})

    # --- Consumables ---

    def use_consumable(
        self, run: RunState, item_id: str, target_character_id: str
    ) -> RunState:
        """Use a consumable from stash on a character. Removes the item."""
        party = run.party
        if item_id not in party.stash:
            raise ValueError(f"Item '{item_id}' not in stash")
        if target_character_id not in party.characters:
            raise ValueError(f"Unknown character: {target_character_id}")

        item = self.game_data.items.get(item_id) or party.items.get(item_id)
        if item is None or not item.is_consumable:
            raise ValueError(f"'{item_id}' is not a consumable")
        if item.teaches_ability_id:
            raise ValueError(
                f"'{item_id}' is a teach scroll — use use_teach_scroll instead"
            )

        char = party.characters[target_character_id]
        job = self.game_data.jobs[char.job_id]
        # Apply healing using effective max HP
        heal = item.heal_amount + int(char.max_hp * item.heal_percent)
        new_hp = min(char.current_hp + heal, char.max_hp)

        new_stash = list(party.stash)
        new_stash.remove(item_id)

        new_char = char.model_copy(update={"current_hp": new_hp})
        new_characters = dict(party.characters)
        new_characters[target_character_id] = new_char
        new_party = party.model_copy(
            update={"characters": new_characters, "stash": new_stash}
        )
        return run.model_copy(update={"party": new_party})

