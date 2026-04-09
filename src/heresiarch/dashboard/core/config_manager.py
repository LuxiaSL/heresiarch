"""Apply and persist formula config overrides."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from heresiarch.dashboard.core.config_model import FormulaConfig

# Module-constant mapping: field_name -> (module_path, attr_name)
_FORMULA_MODULE = "heresiarch.engine.formulas"
_LOOT_MODULE = "heresiarch.engine.loot"

_LOOT_FIELDS = frozenset({"OVERSTAY_PENALTY_PER_BATTLE"})


def _get_module(field_name: str):
    """Return the engine module that owns a given constant."""
    import importlib

    if field_name in _LOOT_FIELDS:
        return importlib.import_module(_LOOT_MODULE)
    return importlib.import_module(_FORMULA_MODULE)


@contextmanager
def apply_formula_config(cfg: FormulaConfig) -> Generator[None, None, None]:
    """Temporarily override engine module-level constants.

    Restores original values on exit. Single-user tool — not thread-safe,
    but fine for a local balance dashboard.
    """
    saved: list[tuple[object, str, object]] = []
    try:
        for field_name, value in cfg.model_dump().items():
            module = _get_module(field_name)
            if hasattr(module, field_name):
                saved.append((module, field_name, getattr(module, field_name)))
                setattr(module, field_name, value)
        yield
    finally:
        for module, name, original in saved:
            setattr(module, name, original)


def load_saved_config(overrides_path: Path) -> FormulaConfig:
    """Load persisted overrides, falling back to engine defaults."""
    if overrides_path.exists():
        try:
            data = json.loads(overrides_path.read_text())
            return FormulaConfig.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass
    return FormulaConfig()


def save_config(cfg: FormulaConfig, overrides_path: Path) -> None:
    """Persist formula config to a JSON file."""
    overrides_path.parent.mkdir(parents=True, exist_ok=True)
    overrides_path.write_text(
        cfg.model_dump_json(indent=2),
        encoding="utf-8",
    )
