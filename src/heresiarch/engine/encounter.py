"""Encounter generation: creates enemy groups from zone templates."""

from __future__ import annotations

import random

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.models.enemies import EnemyInstance, EnemyTemplate
from heresiarch.engine.models.zone import EncounterTemplate, RandomSpawn

ENDLESS_MIN_ENEMIES: int = 2
ENDLESS_MAX_ENEMIES: int = 4


class EncounterGenerator:
    """Generates concrete enemy groups from zone encounter templates."""

    def __init__(
        self,
        enemy_registry: dict[str, EnemyTemplate],
        combat_engine: CombatEngine,
        rng: random.Random | None = None,
    ):
        self.enemy_registry = enemy_registry
        self.combat_engine = combat_engine
        self.rng = rng or random.Random()

    def _interpolate_level_range(
        self,
        zone_min: int,
        zone_max: int,
        encounter_index: int,
        total_encounters: int,
    ) -> tuple[int, int]:
        """Compute a sub-range within the zone range based on encounter position.

        Earlier encounters skew toward zone_min, later ones toward zone_max.
        Each position gets a +/-1 window around its interpolated center,
        clamped to the zone bounds.
        """
        t = encounter_index / (total_encounters - 1)
        center = zone_min + t * (zone_max - zone_min)
        interp_min = max(zone_min, round(center - 1))
        interp_max = min(zone_max, round(center + 1))
        return (interp_min, interp_max)

    def _resolve_enemy_level(
        self,
        encounter_template: EncounterTemplate,
        zone_level_range: tuple[int, int],
        zone_level: int,
        encounter_index: int | None = None,
        total_encounters: int | None = None,
    ) -> int:
        """Determine the enemy level for an encounter.

        Priority:
        1. encounter_template.enemy_level_override (boss hardcoded levels)
        2. encounter_template.enemy_level_range (per-encounter override)
        3. Auto-interpolation from zone range based on encounter position
        4. Flat zone range (for overstay or single-encounter zones)
        5. zone_level fallback (backward compat)
        """
        # 1. Boss hardcoded override
        if encounter_template.enemy_level_override is not None:
            return encounter_template.enemy_level_override

        # 2. Per-encounter range override
        if encounter_template.enemy_level_range is not None:
            enc_min, enc_max = encounter_template.enemy_level_range
            if enc_min > 0 and enc_max >= enc_min:
                return self.rng.randint(enc_min, enc_max)

        # 3-4. Zone range (interpolated if position known, flat otherwise)
        zone_min, zone_max = zone_level_range
        if zone_min > 0 and zone_max >= zone_min:
            if (
                encounter_index is not None
                and total_encounters is not None
                and total_encounters > 1
            ):
                interp_min, interp_max = self._interpolate_level_range(
                    zone_min, zone_max, encounter_index, total_encounters,
                )
                return self.rng.randint(interp_min, interp_max)
            return self.rng.randint(zone_min, zone_max)

        # 5. zone_level fallback
        return zone_level

    def generate_encounter(
        self,
        encounter_template: EncounterTemplate,
        zone_level: int,
        random_spawns: list[RandomSpawn] | None = None,
        enemy_level_range: tuple[int, int] = (0, 0),
        encounter_index: int | None = None,
        total_encounters: int | None = None,
    ) -> list[EnemyInstance]:
        """Create EnemyInstance list from an EncounterTemplate.

        For boss encounters, enemies get 1.5x budget multiplier.
        Each instance gets a unique ID: "{template_id}_{index}".
        Random spawns are rolled and injected if they hit.

        Enemy levels are determined by (in priority order):
        1. encounter_template.enemy_level_override (for bosses)
        2. encounter_template.enemy_level_range (per-encounter override)
        3. Auto-interpolation from zone range based on encounter position
        4. Flat zone range (for overstay or single-encounter zones)
        5. zone_level (backward compat fallback)
        """
        instances: list[EnemyInstance] = []
        global_idx = 0

        for tmpl_id, count in zip(
            encounter_template.enemy_templates,
            encounter_template.enemy_counts,
            strict=True,
        ):
            template = self.enemy_registry[tmpl_id]

            for _i in range(count):
                # Each enemy gets its own level roll from the resolved range
                enemy_level = self._resolve_enemy_level(
                    encounter_template, enemy_level_range, zone_level,
                    encounter_index, total_encounters,
                )
                instance_id = f"{tmpl_id}_{global_idx}"
                instance = self.combat_engine.create_enemy_instance(
                    template, enemy_level, instance_id=instance_id
                )
                instances.append(instance)
                global_idx += 1

        # Roll for random spawn injections (skip boss encounters)
        if random_spawns and not encounter_template.is_boss:
            for spawn in random_spawns:
                if spawn.enemy_template_id not in self.enemy_registry:
                    continue
                if self.rng.random() < spawn.chance:
                    template = self.enemy_registry[spawn.enemy_template_id]
                    enemy_level = self._resolve_enemy_level(
                        encounter_template, enemy_level_range, zone_level,
                        encounter_index, total_encounters,
                    )
                    instance_id = f"{spawn.enemy_template_id}_{global_idx}"
                    instance = self.combat_engine.create_enemy_instance(
                        template, enemy_level, instance_id=instance_id
                    )
                    instances.append(instance)
                    global_idx += 1

        return instances

    def generate_endless_encounter(
        self,
        enemy_pool: list[str],
        player_level: int,
        min_level: int,
        max_level: int,
    ) -> list[EnemyInstance]:
        """Generate a dynamic encounter for an endless zone.

        Picks 2-4 enemies from the pool. Enemy level rubber-bands to
        player level, clamped within [min_level, max_level].
        """
        valid_pool = [tid for tid in enemy_pool if tid in self.enemy_registry]
        if not valid_pool:
            raise ValueError("No valid enemies in endless pool")

        enemy_level = max(min_level, min(player_level, max_level))
        num_enemies = self.rng.randint(ENDLESS_MIN_ENEMIES, ENDLESS_MAX_ENEMIES)

        instances: list[EnemyInstance] = []
        for idx in range(num_enemies):
            template_id = self.rng.choice(valid_pool)
            template = self.enemy_registry[template_id]
            # Small level variance: ±1 around the base, clamped to zone range
            level_jitter = self.rng.randint(-1, 1)
            actual_level = max(min_level, min(enemy_level + level_jitter, max_level))
            instance_id = f"{template_id}_{idx}"
            instance = self.combat_engine.create_enemy_instance(
                template, actual_level, instance_id=instance_id
            )
            instances.append(instance)

        return instances
