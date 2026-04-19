"""Aggregation utilities for N RunResults → balance signal.

Pure functions that take a list of RunResult and return structured
summaries (pydantic models) + pretty-print helpers. Kept separate from
the driver so the dashboard and post-run report can reuse it.
"""

from __future__ import annotations

import statistics
from collections import Counter

from pydantic import BaseModel, Field

from heresiarch.policy.protocols import RunResult


class DistributionStats(BaseModel):
    """Basic descriptive stats for a numeric distribution."""

    mean: float = 0.0
    median: float = 0.0
    stdev: float = 0.0
    min: float = 0.0
    max: float = 0.0
    p10: float = 0.0
    p90: float = 0.0


class BatchSummary(BaseModel):
    """Aggregate stats across a batch of runs of one policy × job."""

    mc_job_id: str
    combat_policy_name: str
    macro_policy_name: str
    n_runs: int
    n_wins: int   # survived (not is_dead at termination)
    n_deaths: int
    win_rate: float
    zones_cleared: DistributionStats
    farthest_zone_level: DistributionStats
    encounters_cleared: DistributionStats
    rounds_taken_total: DistributionStats
    final_mc_level: DistributionStats
    final_gold: DistributionStats
    death_cause_counts: dict[str, int] = Field(default_factory=dict)
    death_zone_counts: dict[str, int] = Field(default_factory=dict)
    termination_reason_counts: dict[str, int] = Field(default_factory=dict)
    farthest_zone_counts: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _distribution(values: list[float]) -> DistributionStats:
    if not values:
        return DistributionStats()
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _pct(p: float) -> float:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return float(sorted_vals[idx])

    return DistributionStats(
        mean=statistics.fmean(values),
        median=statistics.median(values),
        stdev=statistics.pstdev(values) if n > 1 else 0.0,
        min=float(min(values)),
        max=float(max(values)),
        p10=_pct(0.10),
        p90=_pct(0.90),
    )


def summarize(results: list[RunResult]) -> BatchSummary:
    """Aggregate N RunResults. Assumes homogeneous job + policy pair."""
    if not results:
        raise ValueError("Need at least one RunResult to summarize")

    sample = results[0]
    n = len(results)
    n_deaths = sum(1 for r in results if r.is_dead)

    zones = [float(len(r.zones_cleared)) for r in results]
    zone_levels = [float(r.farthest_zone_level) for r in results]
    encs = [float(r.encounters_cleared) for r in results]
    rounds_ = [float(r.rounds_taken_total) for r in results]
    levels = [float(r.final_mc_level) for r in results]
    gold = [float(r.final_gold) for r in results]

    death_cause = Counter(r.killed_by for r in results if r.is_dead and r.killed_by)
    death_zones = Counter(r.killed_at_zone for r in results if r.is_dead and r.killed_at_zone)
    term = Counter(r.termination_reason for r in results)
    farthest = Counter(r.farthest_zone for r in results if r.farthest_zone)

    return BatchSummary(
        mc_job_id=sample.mc_job_id,
        combat_policy_name=sample.combat_policy_name,
        macro_policy_name=sample.macro_policy_name,
        n_runs=n,
        n_wins=n - n_deaths,
        n_deaths=n_deaths,
        win_rate=(n - n_deaths) / n if n else 0.0,
        zones_cleared=_distribution(zones),
        farthest_zone_level=_distribution(zone_levels),
        encounters_cleared=_distribution(encs),
        rounds_taken_total=_distribution(rounds_),
        final_mc_level=_distribution(levels),
        final_gold=_distribution(gold),
        death_cause_counts=dict(death_cause),
        death_zone_counts=dict(death_zones),
        termination_reason_counts=dict(term),
        farthest_zone_counts=dict(farthest),
    )


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------


def format_summary(summary: BatchSummary) -> str:
    lines: list[str] = []
    lines.append("")
    lines.append(
        f"=== {summary.mc_job_id} × {summary.combat_policy_name}/"
        f"{summary.macro_policy_name} (n={summary.n_runs}) ==="
    )
    lines.append(
        f"  Win rate: {summary.win_rate:.1%} "
        f"({summary.n_wins} survived / {summary.n_deaths} died)"
    )
    lines.append("")

    def _dist_row(label: str, d: DistributionStats) -> str:
        return (
            f"  {label:<24} "
            f"mean={d.mean:>6.1f}  median={d.median:>5.1f}  "
            f"stdev={d.stdev:>5.1f}  "
            f"p10={d.p10:>4.0f}  p90={d.p90:>5.0f}  "
            f"[{d.min:.0f} .. {d.max:.0f}]"
        )

    lines.append(_dist_row("zones_cleared", summary.zones_cleared))
    lines.append(_dist_row("farthest_zone_level", summary.farthest_zone_level))
    lines.append(_dist_row("encounters_cleared", summary.encounters_cleared))
    lines.append(_dist_row("rounds_taken_total", summary.rounds_taken_total))
    lines.append(_dist_row("final_mc_level", summary.final_mc_level))
    lines.append(_dist_row("final_gold", summary.final_gold))
    lines.append("")

    if summary.farthest_zone_counts:
        lines.append("  Farthest zone reached:")
        for zone, count in sorted(
            summary.farthest_zone_counts.items(), key=lambda kv: -kv[1],
        )[:10]:
            lines.append(f"    {zone:<20} {count:>3}")
        lines.append("")

    if summary.death_cause_counts:
        lines.append("  Top death causes:")
        for cause, count in sorted(
            summary.death_cause_counts.items(), key=lambda kv: -kv[1],
        )[:5]:
            lines.append(f"    {cause:<20} {count:>3}")
        lines.append("")

    if summary.termination_reason_counts:
        lines.append("  Termination reasons:")
        for reason, count in sorted(
            summary.termination_reason_counts.items(), key=lambda kv: -kv[1],
        ):
            lines.append(f"    {reason:<20} {count:>3}")

    return "\n".join(lines)
