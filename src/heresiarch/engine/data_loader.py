"""Loads YAML data files and validates them into pydantic models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from heresiarch.engine.models.abilities import Ability
from heresiarch.engine.models.enemies import EnemyTemplate
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.jobs import JobTemplate
from heresiarch.engine.models.loot import DropTable
from heresiarch.engine.models.zone import ZoneTemplate


class GameData(BaseModel):
    """Immutable container for all static game data."""

    jobs: dict[str, JobTemplate]
    abilities: dict[str, Ability]
    items: dict[str, Item]
    enemies: dict[str, EnemyTemplate]
    drop_tables: dict[str, DropTable] = {}
    zones: dict[str, ZoneTemplate] = {}

    def validate_cross_references(self) -> list[str]:
        """Check that all ID references resolve. Returns list of errors."""
        errors: list[str] = []

        for job_id, job in self.jobs.items():
            if job.innate_ability_id not in self.abilities:
                errors.append(
                    f"Job '{job_id}' references unknown ability '{job.innate_ability_id}'"
                )

        for enemy_id, enemy in self.enemies.items():
            for ability_id in enemy.abilities:
                if ability_id not in self.abilities:
                    errors.append(
                        f"Enemy '{enemy_id}' references unknown ability '{ability_id}'"
                    )
            for item_id in enemy.equipment:
                if item_id not in self.items:
                    errors.append(
                        f"Enemy '{enemy_id}' references unknown item '{item_id}'"
                    )

        for dt_id, dt in self.drop_tables.items():
            if dt.enemy_template_id not in self.enemies:
                errors.append(
                    f"Drop table '{dt_id}' references unknown enemy '{dt.enemy_template_id}'"
                )
            for item_id in dt.common_item_ids:
                if item_id not in self.items:
                    errors.append(
                        f"Drop table '{dt_id}' references unknown common item '{item_id}'"
                    )
            for item_id in dt.rare_item_ids:
                if item_id not in self.items:
                    errors.append(
                        f"Drop table '{dt_id}' references unknown rare item '{item_id}'"
                    )

        for zone_id, zone in self.zones.items():
            for enc in zone.encounters:
                for tmpl_id in enc.enemy_templates:
                    if tmpl_id not in self.enemies:
                        errors.append(
                            f"Zone '{zone_id}' encounter references unknown enemy '{tmpl_id}'"
                        )
            for item_id in zone.shop_item_pool:
                if item_id not in self.items:
                    errors.append(
                        f"Zone '{zone_id}' shop references unknown item '{item_id}'"
                    )

        return errors


def _load_yaml(path: Path) -> Any:
    """Load a single YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_jobs(directory: Path) -> dict[str, JobTemplate]:
    """Load all job YAML files from a directory. Returns id -> JobTemplate."""
    jobs: dict[str, JobTemplate] = {}
    if not directory.exists():
        return jobs

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue
        job = JobTemplate(**data)
        jobs[job.id] = job

    return jobs


def load_abilities(directory: Path) -> dict[str, Ability]:
    """Load all ability YAML files from a directory.

    Each file can contain a single ability dict or a list of abilities.
    Returns id -> Ability.
    """
    abilities: dict[str, Ability] = {}
    if not directory.exists():
        return abilities

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue

        items_list: list[dict[str, Any]] = data if isinstance(data, list) else [data]
        for item_data in items_list:
            ability = Ability(**item_data)
            abilities[ability.id] = ability

    return abilities


def load_items(directory: Path) -> dict[str, Item]:
    """Load all item YAML files from a directory.

    Each file can contain a single item dict or a list of items.
    Returns id -> Item.
    """
    items: dict[str, Item] = {}
    if not directory.exists():
        return items

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue

        items_list: list[dict[str, Any]] = data if isinstance(data, list) else [data]
        for item_data in items_list:
            item = Item(**item_data)
            items[item.id] = item

    return items


def load_enemies(directory: Path) -> dict[str, EnemyTemplate]:
    """Load all enemy YAML files from a directory.

    Each file can contain a single enemy dict or a list of enemies.
    Returns id -> EnemyTemplate.
    """
    enemies: dict[str, EnemyTemplate] = {}
    if not directory.exists():
        return enemies

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue

        items_list: list[dict[str, Any]] = data if isinstance(data, list) else [data]
        for item_data in items_list:
            enemy = EnemyTemplate(**item_data)
            enemies[enemy.id] = enemy

    return enemies


def load_drop_tables(directory: Path) -> dict[str, DropTable]:
    """Load all drop table YAML files from a directory.

    Each file can contain a single drop table dict or a list.
    Returns enemy_template_id -> DropTable.
    """
    tables: dict[str, DropTable] = {}
    if not directory.exists():
        return tables

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue

        items_list: list[dict[str, Any]] = data if isinstance(data, list) else [data]
        for item_data in items_list:
            dt = DropTable(**item_data)
            tables[dt.enemy_template_id] = dt

    return tables


def load_zones(directory: Path) -> dict[str, ZoneTemplate]:
    """Load all zone YAML files from a directory.

    Each file can contain a single zone dict or a list.
    Returns id -> ZoneTemplate.
    """
    zones: dict[str, ZoneTemplate] = {}
    if not directory.exists():
        return zones

    for path in sorted(directory.glob("*.yaml")):
        data = _load_yaml(path)
        if data is None:
            continue

        items_list: list[dict[str, Any]] = data if isinstance(data, list) else [data]
        for item_data in items_list:
            zone = ZoneTemplate(**item_data)
            zones[zone.id] = zone

    return zones


def load_all(data_dir: Path) -> GameData:
    """Load everything from the data directory. Returns a GameData container."""
    jobs = load_jobs(data_dir / "jobs")
    abilities = load_abilities(data_dir / "abilities")
    items = load_items(data_dir / "items")
    enemies = load_enemies(data_dir / "enemies")
    drop_tables = load_drop_tables(data_dir / "loot")
    zones = load_zones(data_dir / "zones")

    game_data = GameData(
        jobs=jobs,
        abilities=abilities,
        items=items,
        enemies=enemies,
        drop_tables=drop_tables,
        zones=zones,
    )

    errors = game_data.validate_cross_references()
    if errors:
        raise ValueError(
            f"Data validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return game_data
