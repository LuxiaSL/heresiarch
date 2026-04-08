"""Encounter generation: creates enemy groups from zone templates."""

from __future__ import annotations

import random

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.models.enemies import EnemyInstance, EnemyTemplate
from heresiarch.engine.models.zone import EncounterTemplate, RandomSpawn

BOSS_BUDGET_MULTIPLIER: float = 1.5


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

    def generate_encounter(
        self,
        encounter_template: EncounterTemplate,
        zone_level: int,
        random_spawns: list[RandomSpawn] | None = None,
    ) -> list[EnemyInstance]:
        """Create EnemyInstance list from an EncounterTemplate.

        For boss encounters, enemies get 1.5x budget multiplier.
        Each instance gets a unique ID: "{template_id}_{index}".
        Random spawns are rolled and injected if they hit.
        """
        instances: list[EnemyInstance] = []
        global_idx = 0

        for tmpl_id, count in zip(
            encounter_template.enemy_templates,
            encounter_template.enemy_counts,
            strict=True,
        ):
            template = self.enemy_registry[tmpl_id]

            if encounter_template.is_boss:
                template = template.model_copy(
                    update={
                        "budget_multiplier": template.budget_multiplier
                        * BOSS_BUDGET_MULTIPLIER
                    }
                )

            for i in range(count):
                instance_id = f"{tmpl_id}_{global_idx}"
                instance = self.combat_engine.create_enemy_instance(
                    template, zone_level, instance_id=instance_id
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
                    instance_id = f"{spawn.enemy_template_id}_{global_idx}"
                    instance = self.combat_engine.create_enemy_instance(
                        template, zone_level, instance_id=instance_id
                    )
                    instances.append(instance)
                    global_idx += 1

        return instances
