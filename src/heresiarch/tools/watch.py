"""Live terminal viewer for sim/optimizer progress streams.

Tails a progress JSONL file (see heresiarch.tools.progress) and renders
a multi-panel live view: every in-flight seed ticking through zones
with an HP bar, finished seeds folding into a tally, and optimizer
generation banners as they land.

Usage:
    uv run python -m heresiarch.tools.watch <progress.jsonl>

The viewer is read-only and can attach/detach at any time — state is
rebuilt from the full file on startup.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from heresiarch.tools.progress import read_events

REFRESH_S = 0.5
FLASH_S = 6.0  # how long a finished seed lingers before folding into the tally


@dataclass
class SeedState:
    seed: int
    job: str = ""
    zone: str = ""
    enc: int = 0
    level: int = 0
    hp_pct: float = 1.0
    gold: int = 0
    started_ts: float = 0.0
    last_ts: float = 0.0
    finished_ts: float = 0.0
    dead: bool | None = None
    reason: str = ""


@dataclass
class WatchState:
    seeds: dict[int, SeedState] = field(default_factory=dict)
    gen_lines: list[str] = field(default_factory=list)
    phase: str = ""
    total_encounters: int = 0

    def apply(self, ev: dict) -> None:
        kind = ev.get("kind")
        if kind == "run_start":
            seed = int(ev.get("seed", -1))
            st = self.seeds.setdefault(seed, SeedState(seed=seed))
            # Re-runs of the same seed (new arm/generation) reset it.
            st.job = str(ev.get("job", ""))
            st.started_ts = float(ev.get("ts", 0.0))
            st.last_ts = st.started_ts
            st.finished_ts = 0.0
            st.dead = None
            st.zone, st.enc, st.level, st.hp_pct = "", 0, 0, 1.0
        elif kind == "encounter":
            seed = int(ev.get("seed", -1))
            st = self.seeds.setdefault(seed, SeedState(seed=seed))
            st.zone = str(ev.get("zone", ""))
            st.enc = int(ev.get("enc", 0))
            st.level = int(ev.get("level", 0))
            st.hp_pct = float(ev.get("hp_pct", 1.0))
            st.gold = int(ev.get("gold", 0))
            st.last_ts = float(ev.get("ts", 0.0))
            self.total_encounters += 1
        elif kind == "run_end":
            seed = int(ev.get("seed", -1))
            st = self.seeds.setdefault(seed, SeedState(seed=seed))
            st.dead = bool(ev.get("dead", False))
            st.reason = str(ev.get("reason", ""))
            st.enc = int(ev.get("enc", st.enc))
            st.finished_ts = float(ev.get("ts", time.time()))
        elif kind == "generation":
            self.gen_lines.append(
                f"gen {ev.get('gen')}: best={ev.get('best')} "
                f"pop_mean={ev.get('pop_mean')} best_ever={ev.get('best_ever')} "
                f"win={float(ev.get('win_rate', 0)):.0%}"
            )
        elif kind == "phase":
            self.phase = str(ev.get("label", ""))


def _hp_bar(pct: float, width: int = 12) -> Text:
    pct = max(0.0, min(1.0, pct))
    filled = int(round(pct * width))
    color = "green" if pct > 0.6 else "yellow" if pct > 0.3 else "red"
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="grey37")
    bar.append(f" {pct:>4.0%}", style=color)
    return bar


def render(state: WatchState, path: Path) -> Group:
    now = time.time()
    active: list[SeedState] = []
    flashing: list[SeedState] = []
    done_alive = done_dead = 0

    for st in state.seeds.values():
        if st.dead is None:
            active.append(st)
        elif now - st.finished_ts < FLASH_S:
            flashing.append(st)
        elif st.dead:
            done_dead += 1
        else:
            done_alive += 1

    table = Table(
        title=f"⚔ {path.name} — {len(active)} running · "
              f"{done_alive + sum(not s.dead for s in flashing)} alive · "
              f"{done_dead + sum(bool(s.dead) for s in flashing)} dead · "
              f"{state.total_encounters} encounters simulated",
        title_style="bold",
        expand=False,
    )
    table.add_column("seed", justify="right")
    table.add_column("zone", justify="left")
    table.add_column("enc", justify="right")
    table.add_column("lv", justify="right")
    table.add_column("party HP", justify="left")
    table.add_column("gold", justify="right")
    table.add_column("t", justify="right")

    for st in sorted(active, key=lambda s: s.seed):
        stale = now - st.last_ts > 120
        elapsed = max(0.0, now - st.started_ts) if st.started_ts else 0.0
        table.add_row(
            str(st.seed),
            st.zone or "—",
            str(st.enc),
            str(st.level),
            _hp_bar(st.hp_pct),
            str(st.gold),
            f"{elapsed/60:.0f}m" + (" ⏳" if stale else ""),
        )

    for st in sorted(flashing, key=lambda s: s.finished_ts):
        verdict = Text("☠ DEAD", style="bold red") if st.dead else Text(
            "★ SURVIVED", style="bold green",
        )
        table.add_row(
            str(st.seed), st.zone or "—", str(st.enc), str(st.level),
            verdict, str(st.gold), st.reason,
        )

    parts: list = [table]
    if state.gen_lines:
        parts.append(Panel(
            "\n".join(state.gen_lines[-4:]),
            title="tuner", border_style="cyan", expand=False,
        ))
    if state.phase:
        parts.append(Text(f"phase: {state.phase}", style="bold magenta"))
    return Group(*parts)


def main() -> None:
    ap = argparse.ArgumentParser(description="Watch a sim progress stream live")
    ap.add_argument("path", help="Path to the progress JSONL file")
    args = ap.parse_args()
    path = Path(args.path)

    console = Console()
    state = WatchState()
    offset = 0

    with Live(render(state, path), console=console, refresh_per_second=4) as live:
        try:
            while True:
                if path.exists():
                    events, offset = read_events(path, offset)
                    for ev in events:
                        state.apply(ev)
                live.update(render(state, path))
                time.sleep(REFRESH_S)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
