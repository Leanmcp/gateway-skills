#!/usr/bin/env python3
"""
obs_report.py — aggregate obs runs into a comparison table.

The viewers answer "what happened in this episode". This answers the other
question: "which arm won, and by how much, and was that noise?". It reads the
same JSONL files, so there is no second source of truth and no export step —
point it at your runs directory and it tells you where you are.

    python obs_report.py                          # every run under ./runs
    python obs_report.py --roots runs evals_run
    python obs_report.py --run runs/eval-a runs/eval-b   # compare two arms
    python obs_report.py --by task                 # per-task breakdown
    python obs_report.py --json report.json        # machine-readable
    python obs_report.py --csv report.csv

Columns: sessions, mean reward (± the standard error, so you can see whether a
gap is real), solve rate, mean turns / tool calls / tool errors, mean and p95
end-of-episode context, total cost, and how many episodes hit a flood or an
error. Reward is read from `episode` events; runs with no grading still report
everything else.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from view_trace import (  # noqa: E402
    list_run_dirs, load_run, merge, sessions_of, summarize_session,
)

DEFAULT_ROOTS = ["runs", "sim_runs", "evals_run"]


def pct(xs: list[float], q: float) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def sem(xs: list[float]) -> Optional[float]:
    """Standard error of the mean — the number that decides whether an arm
    actually beat another one or just got a friendlier sample of tasks."""
    if len(xs) < 2:
        return None
    return statistics.stdev(xs) / math.sqrt(len(xs))


def collect(run_dir: Path) -> dict:
    turns, events, cfg = load_run(run_dir)
    rows = merge(turns, events, {"error"})
    by_session = sessions_of(rows)
    sessions = [summarize_session(s, r) for s, r in by_session.items()]
    n_errors = sum(1 for e in events if e.get("event") == "error")
    return {"run": run_dir.name, "path": str(run_dir), "config": cfg,
            "sessions": sessions, "n_errors": n_errors}


def aggregate(label: str, sessions: list[dict], n_errors: int = 0) -> dict:
    rewards = [float(s["reward"]) for s in sessions if s["reward"] is not None]
    ctx = [s["ctx_tokens"] for s in sessions if s["ctx_tokens"]]
    return {
        "label": label,
        "n_sessions": len(sessions),
        "n_graded": len(rewards),
        "mean_reward": statistics.fmean(rewards) if rewards else None,
        "sem_reward": sem(rewards),
        "solve_rate": (sum(1 for r in rewards if r >= 1.0) / len(rewards)
                       if rewards else None),
        "mean_turns": statistics.fmean([s["turns"] for s in sessions]) if sessions else 0,
        "mean_tool_calls": (statistics.fmean([s["tool_calls"] for s in sessions])
                            if sessions else 0),
        "mean_tool_errors": (statistics.fmean([s["tool_errors"] for s in sessions])
                             if sessions else 0),
        "mean_ctx_tokens": statistics.fmean(ctx) if ctx else None,
        "p95_ctx_tokens": pct([float(x) for x in ctx], 0.95),
        "total_cost": sum(s["cost"] for s in sessions),
        "n_floods": sum(1 for s in sessions if s["flood"]),
        "n_errors": n_errors,
    }


def fmt(v: Any, nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def print_table(rows: list[dict]) -> None:
    cols = [
        ("label", "arm / run", 40, 0), ("n_sessions", "n", 5, 0),
        ("mean_reward", "reward", 8, 3), ("sem_reward", "±sem", 7, 3),
        ("solve_rate", "solved", 8, 3), ("mean_turns", "turns", 7, 1),
        ("mean_tool_calls", "tools", 7, 1), ("mean_tool_errors", "toolerr", 8, 2),
        ("mean_ctx_tokens", "ctx", 8, 0), ("p95_ctx_tokens", "ctx p95", 9, 0),
        ("total_cost", "cost $", 9, 3), ("n_floods", "flood", 6, 0),
        ("n_errors", "err", 5, 0),
    ]
    head = "  ".join(h.ljust(w) for _, h, w, _ in cols)
    print(head)
    print("-" * len(head))
    for r in rows:
        print("  ".join(fmt(r.get(k), nd)[:w].ljust(w) for k, _, w, nd in cols))

    graded = [r for r in rows if r["mean_reward"] is not None]
    if len(graded) == 2:
        a, b = graded
        delta = b["mean_reward"] - a["mean_reward"]
        pooled = math.sqrt(sum((r["sem_reward"] or 0) ** 2 for r in graded))
        verdict = ("within noise" if pooled and abs(delta) < 2 * pooled
                   else "outside 2·sem" if pooled else "no variance estimate")
        print()
        print(f"Δ reward ({b['label']} − {a['label']}) = {delta:+.3f}  "
              f"(pooled sem {fmt(pooled)}) → {verdict}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", nargs="*", help="specific run dirs (default: all under --roots)")
    p.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    p.add_argument("--by", choices=["run", "task", "phase"], default="run",
                   help="group rows by run (default), task, or phase")
    p.add_argument("--limit", type=int, default=40, help="max runs to scan")
    p.add_argument("--json", help="also write the report as JSON")
    p.add_argument("--csv", help="also write the report as CSV")
    args = p.parse_args()

    dirs = ([Path(r) for r in args.run] if args.run
            else list_run_dirs(args.roots)[: args.limit])
    if not dirs:
        print(f"No runs under {args.roots}.", file=sys.stderr)
        return 1

    collected = [collect(d) for d in dirs]
    if args.by == "run":
        rows = [aggregate(c["run"], c["sessions"], c["n_errors"]) for c in collected]
    else:
        buckets: dict[str, list[dict]] = {}
        for c in collected:
            for s in c["sessions"]:
                buckets.setdefault(str(s.get(args.by)), []).append(s)
        rows = [aggregate(k, v) for k, v in sorted(buckets.items())]

    print_table(rows)
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2, default=str),
                                   encoding="utf-8")
        print(f"\nwrote {args.json}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
