"""Training-data tap: feature contracts and end-to-end shard writing."""

import gzip
import json
import math
from pathlib import Path

from heresiarch.engine.data_loader import GameData
from heresiarch.policy.builtin.floor import FloorCombatPolicy
from heresiarch.policy.builtin.floor_plus import FloorPlusMacroPolicy
from heresiarch.policy.features import (
    combat_feature_names,
    macro_feature_names,
)
from heresiarch.tools.data_tap import DataTap
from heresiarch.tools.run_driver import simulate_run


def _run_with_tap(tmp_path: Path, game_data: GameData, seed: int = 5):
    shard = tmp_path / f"tap_{seed}.jsonl.gz"
    tap = DataTap(shard, mc_job_id="einherjar", seed=seed,
                  game_data=game_data, policy_name="floor")
    result = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=FloorPlusMacroPolicy(),
        seed=seed,
        max_encounters=25,
        game_data=game_data,
        data_tap=tap,
    )
    return shard, result


def test_tap_writes_labeled_shard(tmp_path: Path, game_data: GameData):
    shard, result = _run_with_tap(tmp_path, game_data)
    assert shard.exists()
    rows = [json.loads(line) for line in
            gzip.open(shard, "rt", encoding="utf-8")]
    combat = [r for r in rows if r["kind"] == "combat"]
    macro = [r for r in rows if r["kind"] == "macro"]
    assert combat and macro

    n_combat = len(combat_feature_names())
    n_macro = len(macro_feature_names())
    for r in combat:
        assert len(r["x"]) == n_combat
        assert all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in r["x"])
        assert isinstance(r["y"]["won"], bool)
        assert 0.0 <= r["y"]["value"] <= 2.0
        assert r["y"]["rounds_left"] >= 0
    for r in macro:
        assert len(r["x"]) == n_macro
        assert all(math.isfinite(v) for v in r["x"])
        assert r["y"]["zones_ahead"] >= 0
        assert isinstance(r["y"]["survived"], bool)

    # Sanity: every encounter contributed a macro row; battle rounds
    # produced at least as many combat rows as encounters.
    assert len(macro) == result.encounters_cleared + (1 if result.is_dead else 0) \
        or len(macro) >= result.encounters_cleared


def test_value_label_matches_terminal_semantics(
    tmp_path: Path, game_data: GameData,
):
    """Won rows land in [1,2], lost finished rows are 0."""
    shard, _ = _run_with_tap(tmp_path, game_data, seed=6)
    rows = [json.loads(line) for line in
            gzip.open(shard, "rt", encoding="utf-8")]
    for r in rows:
        if r["kind"] != "combat":
            continue
        if r["y"]["won"]:
            assert 1.0 <= r["y"]["value"] <= 2.0
        elif r["y"]["finished"]:
            assert r["y"]["value"] == 0.0


def test_tap_skip_existing_resumes(tmp_path: Path, monkeypatch, capsys):
    """--tap-skip-existing runs only the seeds without a shard."""
    import sys

    from heresiarch.tools.sim import main

    tap = tmp_path / "shards"
    base = [
        "sim", "run", "--job", "einherjar", "--policy", "floor",
        "--macro", "floor_plus_macro", "--max-encounters", "3",
        "--seed-start", "50", "--tap-out", str(tap), "--quiet",
    ]
    monkeypatch.setattr(sys, "argv", base + ["--n", "1"])
    main()
    first = tap / "tap_einherjar_floor_50.jsonl.gz"
    assert first.exists()
    rows_before = first.read_bytes()

    monkeypatch.setattr(
        sys, "argv", base + ["--n", "3", "--tap-skip-existing"],
    )
    main()
    out = capsys.readouterr().out
    assert "Resume: 1 of 3" in out
    for seed in (50, 51, 52):
        assert (tap / f"tap_einherjar_floor_{seed}.jsonl.gz").exists()
    # The existing shard was skipped, not re-run (append would grow it).
    assert first.read_bytes() == rows_before

    # Third pass: everything present -> no work at all.
    monkeypatch.setattr(
        sys, "argv", base + ["--n", "3", "--tap-skip-existing"],
    )
    main()
    assert "Nothing to do" in capsys.readouterr().out


def test_tap_never_breaks_the_sim(tmp_path: Path, game_data: GameData):
    """A tap whose writer explodes must not affect the run result."""

    class BrokenTap(DataTap):
        def _flush(self):  # type: ignore[override]
            raise OSError("disk on fire")

    tap = BrokenTap(tmp_path / "x.jsonl.gz", mc_job_id="einherjar",
                    seed=7, game_data=game_data)
    result = simulate_run(
        mc_job_id="einherjar",
        combat_policy=FloorCombatPolicy(),
        macro_policy=FloorPlusMacroPolicy(),
        seed=7,
        max_encounters=15,
        game_data=game_data,
        data_tap=tap,
    )
    assert result.encounters_cleared >= 0  # run completed normally


def test_tap_failure_is_logged_not_silent(
    tmp_path: Path, game_data: GameData, caplog, monkeypatch,
):
    """Swallowed tap failures emit a rate-limited warning (data loss!)."""
    import logging

    import heresiarch.tools.data_tap as data_tap_mod
    from heresiarch.logutil import RateLimitedLogger

    # Fresh limiter: another test may have burned this key's window.
    monkeypatch.setattr(data_tap_mod, "_rate_limited", RateLimitedLogger())

    class BrokenTap(DataTap):
        def _flush(self):  # type: ignore[override]
            raise OSError("disk on fire")

    tap = BrokenTap(tmp_path / "x.jsonl.gz", mc_job_id="einherjar",
                    seed=7, game_data=game_data)
    with caplog.at_level(logging.WARNING, "heresiarch.tools.data_tap"):
        result = simulate_run(
            mc_job_id="einherjar",
            combat_policy=FloorCombatPolicy(),
            macro_policy=FloorPlusMacroPolicy(),
            seed=7,
            max_encounters=15,
            game_data=game_data,
            data_tap=tap,
        )
    assert result.encounters_cleared >= 0  # run still completed normally
    assert "on_run_end failed" in caplog.text
    assert "OSError" in caplog.text
