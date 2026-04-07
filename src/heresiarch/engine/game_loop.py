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
    calculate_effective_stats,
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
from heresiarch.engine.models.party import Party
from heresiarch.engine.models.run_state import CombatResult, RunState
from heresiarch.engine.models.stats import StatType
from heresiarch.engine.models.zone import ZoneState, ZoneTemplate

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
        for unlock in job.ability_unlocks:
            if old_level < unlock.level <= new_level:
                if unlock.ability_id not in new_abilities:
                    new_abilities.append(unlock.ability_id)
        if new_abilities != char.abilities:
            return char.model_copy(update={"abilities": new_abilities})
        return char

    def _recompute_derived(self, char: CharacterInstance, party: Party | None = None) -> CharacterInstance:
        """Recompute effective_stats and max_hp from base_stats + equipment.

        Call this after ANY change to base_stats, equipment, or job.
        """
        equipped: list[Item] = []
        for slot, item_id in char.equipment.items():
            if item_id:
                item = (party.items.get(item_id) if party else None) or self.game_data.items.get(item_id)
                if item:
                    equipped.append(item)
        effective = calculate_effective_stats(char.base_stats, equipped, [])
        job = self.game_data.jobs.get(char.job_id)
        max_hp = calculate_max_hp(job.base_hp, job.hp_growth, char.level, effective.DEF) if job else 0
        return char.model_copy(update={
            "effective_stats": effective,
            "max_hp": max_hp,
        })

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
        """Exit the current zone, save progress, and heal the party."""
        new_progress = dict(run.zone_progress)
        if run.current_zone_id and run.zone_state:
            new_progress[run.current_zone_id] = run.zone_state
        run = run.model_copy(update={"zone_progress": new_progress})
        run = self.enter_safe_zone(run)
        return run.model_copy(
            update={"current_zone_id": None, "zone_state": None}
        )

    def get_next_encounter(self, run: RunState) -> list[EnemyInstance]:
        """Generate the next encounter in current zone.

        In overstay mode (zone already cleared), generates a random
        non-boss encounter from the zone's template list.
        """
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

        zone = self.game_data.zones[run.current_zone_id]

        if run.zone_state.is_cleared:
            # Overstay: pick a random non-boss encounter
            non_boss = [e for e in zone.encounters if not e.is_boss]
            if not non_boss:
                non_boss = zone.encounters  # fallback: all encounters
            encounter_template = self.rng.choice(non_boss)
            return self.encounter_generator.generate_encounter(
                encounter_template, zone.zone_level
            )

        idx = run.zone_state.current_encounter_index
        if idx >= len(zone.encounters):
            raise ValueError("No more encounters in this zone")

        encounter_template = zone.encounters[idx]
        return self.encounter_generator.generate_encounter(
            encounter_template, zone.zone_level
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

        # --- XP Distribution + HP Persistence ---
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
        for tmpl_id in combat_result.defeated_enemy_template_ids:
            if tmpl_id in self.game_data.enemies:
                template = self.game_data.enemies[tmpl_id]
                instance = self.combat_engine.create_enemy_instance(
                    template, combat_result.zone_level
                )
                instance = instance.model_copy(update={"current_hp": 0})
                defeated_instances.append(instance)

        overstay = run.zone_state.overstay_battles if run.zone_state else 0
        loot = self.loot_resolver.resolve_encounter_drops(
            defeated_enemies=defeated_instances,
            zone_level=combat_result.zone_level,
            party_cha=party.cha,
            overstay_battles=overstay,
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
        """Move to next encounter in zone. Mark zone cleared if done.

        In overstay mode, increments the overstay counter instead.
        """
        if run.zone_state is None or run.current_zone_id is None:
            raise ValueError("Not in a zone")

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

        # Recalculate stats from full history + recompute derived
        new_stats = calculate_stats_from_history(history, self.game_data.jobs)

        new_mc = mc.model_copy(
            update={
                "job_id": new_job_id,
                "base_stats": new_stats,
                "abilities": ["basic_attack", new_job.innate_ability_id],
                "growth_history": history,
            }
        )
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

        # Rebuild abilities: basic_attack + innate + equipment-granted
        innate_id = self.game_data.jobs[char.job_id].innate_ability_id
        new_abilities = ["basic_attack", innate_id]
        for s, eid in new_equipment.items():
            if eid and eid in new_items and new_items[eid].granted_ability_id:
                new_abilities.append(new_items[eid].granted_ability_id)

        new_char = char.model_copy(
            update={"equipment": new_equipment, "abilities": new_abilities}
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

        # Rebuild abilities: basic_attack + innate + remaining equipment-granted
        innate_id = self.game_data.jobs[char.job_id].innate_ability_id
        new_abilities = ["basic_attack", innate_id]
        for s, eid in new_equipment.items():
            if eid:
                eq_item = party.items.get(eid) or self.game_data.items.get(eid)
                if eq_item and eq_item.granted_ability_id:
                    new_abilities.append(eq_item.granted_ability_id)

        new_char = char.model_copy(update={"equipment": new_equipment, "abilities": new_abilities})
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

        # Grant the ability if not already known
        new_abilities = list(char.abilities)
        if ability_id not in new_abilities:
            new_abilities.append(ability_id)

        new_char = char.model_copy(update={"abilities": new_abilities})

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

    # --- Safe Zone Healing ---

    def enter_safe_zone(self, run: RunState) -> RunState:
        """Heal all party members to full HP upon entering a safe zone.

        Called between zones — at shops, recruitment points, zone transitions.
        """
        party = run.party
        new_characters = dict(party.characters)

        for char_id in party.active + party.reserve:
            if char_id not in new_characters:
                continue
            char = new_characters[char_id]
            if char.current_hp < char.max_hp:
                new_characters[char_id] = char.model_copy(
                    update={"current_hp": char.max_hp}
                )

        new_party = party.model_copy(update={"characters": new_characters})
        return run.model_copy(update={"party": new_party})
