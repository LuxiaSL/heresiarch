"""Feature extraction for learned value functions.

Pure functions: game state in, fixed-length float vector out. No I/O,
no model code — this module is the *contract* between data generation
(tools/data_tap.py) and training/inference. Bump FEATURES_VERSION when
a vector's layout changes; training data carries the version so stale
shards can be filtered.

Design notes:
- Fractions and ratios over absolutes wherever possible (hp_frac, stat
  ratios) so features generalize across levels and zones.
- Party/enemy sides are encoded as per-slot blocks (sorted by max_hp,
  descending) padded to fixed slot counts, plus side-level aggregates.
- The two most predictive signals are expected to be the pressure
  ratios: party damage output vs enemy HP pool, and vice versa.
"""

from __future__ import annotations

from heresiarch.engine.models.combat_state import CombatantState, CombatState
from heresiarch.engine.models.run_state import RunState

FEATURES_VERSION = 1

JOB_IDS = ["berserker", "einherjar", "martyr", "onmyoji", "sacrist"]

PARTY_SLOTS = 3
ENEMY_SLOTS = 5
_SLOT_FEATS = [
    "alive", "hp_frac", "level_n", "ap_n", "insight_n", "debt_n",
    "frenzy_level_n", "surviving", "statuses_n",
    "str_n", "mag_n", "def_n", "res_n", "spd_n",
]


def _norm_stat(x: int | float) -> float:
    """Squash a raw stat into (0, 1) — 50 maps to 0.5."""
    x = max(0.0, float(x))
    return x / (x + 50.0)


def _norm_count(x: int | float, scale: float) -> float:
    return min(1.0, max(0.0, float(x) / scale))


def _slot_features(c: CombatantState | None) -> list[float]:
    if c is None:
        return [0.0] * len(_SLOT_FEATS)
    hp_frac = max(0, c.current_hp) / max(1, c.max_hp)
    s = c.effective_stats
    return [
        1.0 if c.is_alive else 0.0,
        hp_frac,
        _norm_count(c.level, 40.0),
        _norm_count(c.action_points, 10.0),
        _norm_count(c.insight_stacks, 10.0),
        _norm_count(c.cheat_debt, 6.0),
        _norm_count(c.frenzy_level, 4.0),
        1.0 if c.is_surviving else 0.0,
        _norm_count(len(c.active_statuses), 6.0),
        _norm_stat(s.STR),
        _norm_stat(s.MAG),
        _norm_stat(s.DEF),
        _norm_stat(s.RES),
        _norm_stat(s.SPD),
    ]


def _side_aggregates(side: list[CombatantState]) -> list[float]:
    alive = [c for c in side if c.is_alive]
    n = len(alive)
    if n == 0:
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    hp_fracs = [max(0, c.current_hp) / max(1, c.max_hp) for c in alive]
    return [
        _norm_count(n, 6.0),
        sum(hp_fracs) / n,
        min(hp_fracs),
        _norm_count(sum(max(0, c.current_hp) for c in alive), 2000.0),
        _norm_count(
            sum(1 for c in alive if c.charging_ability_id or c.invulnerable_turns),
            3.0,
        ),
    ]


def _pressure(attackers: list[CombatantState], defenders: list[CombatantState]) -> float:
    """Crude kill-pressure ratio: attack pool vs defender HP pool."""
    atk = sum(
        max(c.effective_stats.STR, c.effective_stats.MAG)
        for c in attackers if c.is_alive
    )
    hp = sum(max(1, c.current_hp) for c in defenders if c.is_alive)
    return min(1.0, atk / max(1.0, hp))


def combat_feature_names() -> list[str]:
    names = ["round_n", "party_pressure", "enemy_pressure"]
    names += [f"job_{j}" for j in JOB_IDS]
    for prefix, count in (("p", PARTY_SLOTS), ("e", ENEMY_SLOTS)):
        names += [f"{prefix}_agg_{k}" for k in
                  ("n", "hp_mean", "hp_min", "hp_pool", "threats")]
        for i in range(count):
            names += [f"{prefix}{i}_{f}" for f in _SLOT_FEATS]
    return names


def combat_features(state: CombatState, mc_job_id: str) -> list[float]:
    """Fixed-length vector describing a mid-combat position."""
    players = sorted(
        state.player_combatants, key=lambda c: c.max_hp, reverse=True,
    )[:PARTY_SLOTS]
    enemies = sorted(
        state.enemy_combatants, key=lambda c: c.max_hp, reverse=True,
    )[:ENEMY_SLOTS]

    out: list[float] = [
        _norm_count(state.round_number, 20.0),
        _pressure(state.player_combatants, state.enemy_combatants),
        _pressure(state.enemy_combatants, state.player_combatants),
    ]
    out += [1.0 if j == mc_job_id else 0.0 for j in JOB_IDS]
    for side, slots in ((players, PARTY_SLOTS), (enemies, ENEMY_SLOTS)):
        full = state.player_combatants if side is players else state.enemy_combatants
        out += _side_aggregates(full)
        for i in range(slots):
            out += _slot_features(side[i] if i < len(side) else None)
    return out


# ---------------------------------------------------------------------------
# Macro (RunState) features — rung 2
# ---------------------------------------------------------------------------


def macro_feature_names() -> list[str]:
    return [
        "mc_level_n", "mc_hp_frac", "party_size_n", "party_hp_mean",
        "gold_n", "potions_n", "stash_used_n",
        "zone_level_n", "zone_level_delta_n", "encounter_index_n",
        "zones_completed_n", "in_cleared_zone",
    ] + [f"job_{j}" for j in JOB_IDS]


def macro_features(
    run: RunState,
    mc_job_id: str,
    zone_level: int,
    healing_item_ids: frozenset[str],
) -> list[float]:
    """Fixed-length vector describing a between/pre-encounter run state."""
    chars = [run.party.characters[c] for c in run.party.active
             if c in run.party.characters]
    mc = next((c for c in chars if c.is_mc), chars[0] if chars else None)
    mc_level = mc.level if mc else 1
    mc_hp = (max(0, mc.current_hp) / max(1, mc.max_hp)) if mc else 0.0
    hp_fracs = [max(0, c.current_hp) / max(1, c.max_hp) for c in chars]
    potions = sum(1 for i in run.party.stash if i in healing_item_ids)
    enc_idx = run.zone_state.current_encounter_index if run.zone_state else 0
    cleared = bool(run.zone_state and run.zone_state.is_cleared)
    return [
        _norm_count(mc_level, 40.0),
        mc_hp,
        _norm_count(len(chars), 3.0),
        (sum(hp_fracs) / len(hp_fracs)) if hp_fracs else 0.0,
        _norm_count(run.party.money, 2000.0),
        _norm_count(potions, 8.0),
        _norm_count(len(run.party.stash), 20.0),
        _norm_count(zone_level, 40.0),
        _norm_count(zone_level - mc_level + 10, 20.0),  # centered at 0.5
        _norm_count(enc_idx, 20.0),
        _norm_count(len(run.zones_completed), 8.0),
        1.0 if cleared else 0.0,
    ] + [1.0 if j == mc_job_id else 0.0 for j in JOB_IDS]
