"""Shared test fixtures: game data, seeded RNG, premade characters."""

import random
from pathlib import Path

import pytest

from heresiarch.engine.combat import CombatEngine
from heresiarch.engine.data_loader import GameData, load_all
from heresiarch.engine.formulas import calculate_max_hp, calculate_stats_at_level
from heresiarch.engine.models.enemies import EnemyInstance
from heresiarch.engine.models.jobs import CharacterInstance
from heresiarch.engine.models.stats import StatBlock


@pytest.fixture
def game_data() -> GameData:
    """Load all game data from YAML files."""
    return load_all(Path("data"))


@pytest.fixture
def seeded_rng() -> random.Random:
    """Deterministic RNG for reproducible combat tests."""
    return random.Random(42)


@pytest.fixture
def combat_engine(game_data: GameData, seeded_rng: random.Random) -> CombatEngine:
    """Pre-wired CombatEngine with all game data and deterministic RNG."""
    return CombatEngine(
        ability_registry=game_data.abilities,
        item_registry=game_data.items,
        job_registry=game_data.jobs,
        rng=seeded_rng,
    )


def _make_character(
    game_data: GameData, job_id: str, level: int, weapon_id: str | None = None
) -> CharacterInstance:
    """Helper to create a leveled character with optional weapon."""
    job = game_data.jobs[job_id]
    stats = calculate_stats_at_level(job.growth, level)
    equipment = {"WEAPON": weapon_id, "ARMOR": None, "ACCESSORY_1": None, "ACCESSORY_2": None}
    max_hp = calculate_max_hp(job.base_hp, job.hp_growth, level, stats.DEF)

    return CharacterInstance(
        id=f"{job_id}_test",
        name=job.name,
        job_id=job_id,
        level=level,
        base_stats=stats,
        equipment=equipment,
        current_hp=max_hp,
        abilities=[job.innate_ability_id],
    )


@pytest.fixture
def einherjar_lv15(game_data: GameData) -> CharacterInstance:
    return _make_character(game_data, "einherjar", 15, "iron_blade")


@pytest.fixture
def onmyoji_lv15(game_data: GameData) -> CharacterInstance:
    return _make_character(game_data, "onmyoji", 15, "spirit_lens")


@pytest.fixture
def martyr_lv15(game_data: GameData) -> CharacterInstance:
    return _make_character(game_data, "martyr", 15)


@pytest.fixture
def berserker_lv15(game_data: GameData) -> CharacterInstance:
    return _make_character(game_data, "berserker", 15, "iron_blade")


@pytest.fixture
def brute_oni_zone15(game_data: GameData, combat_engine: CombatEngine) -> EnemyInstance:
    """Zone 15 Oni (Brute archetype)."""
    template = game_data.enemies["brute_oni"]
    return combat_engine.create_enemy_instance(template, zone_level=15)


@pytest.fixture
def fodder_slime_zone5(game_data: GameData, combat_engine: CombatEngine) -> EnemyInstance:
    """Zone 5 Slime (Fodder archetype)."""
    template = game_data.enemies["fodder_slime"]
    return combat_engine.create_enemy_instance(template, zone_level=5)
