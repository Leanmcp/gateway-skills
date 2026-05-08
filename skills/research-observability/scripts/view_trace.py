#!/usr/bin/env python3
"""
view_trace.py — one-shot, non-interactive dump of an obs run.

The plain sibling of view_trace_tui.py: no curses, no cursor, just the whole
conversation printed in order so you can pipe it, grep it, diff two runs, or
paste it into an issue. This is the viewer you want in CI, over SSH, and when
someone asks "what actually happened in task_007?".

    python view_trace.py                        # newest run under ./runs
    python view_trace.py --run runs/eval-2026...
    python view_trace.py --task task_007 --trial 0
    python view_trace.py --session 3f2a...      # one episode
    python view_trace.py --follow               # tail a run that is still going
    python view_trace.py --summary              # one line per session, no bodies
    python view_trace.py --roots runs evals_run --summary

Reads the same files obs.Run writes; nothing else. If a field is missing (an
API platform has no token ids, a run has no episodes/) the corresponding column
is simply omitted rather than the viewer failing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from obs import read_jsonl  # noqa: E402

DEFAULT_ROOTS = ["runs", "sim_runs", "evals_run"]

# ANSI colours, disabled when stdout is not a tty so pipes stay clean.
_TTY = sys.stdout.isatty()


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


BOLD, DIM = "1", "2"
CYAN, GREEN, YELLOW, RED, MAGENTA, BLUE = "36", "32", "33", "31", "35", "34"


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def transcripts_file(run_dir: Path) -> Path:
    """Full transcripts if present, else a stripped/shared copy. Projects that
    gitignore the heavy file often ship transcripts.share.jsonl (same records
    minus the token-id arrays) so a clone can still be read."""
    full = run_dir / "transcripts.jsonl"
    return full if full.exists() else run_dir / "transcripts.share.jsonl"


def list_run_dirs(roots: list[str]) -> list[Path]:
    """Run folders under any of `roots`, newest first."""
    out = [p for r in roots if Path(r).is_dir()
           for p in Path(r).iterdir()
           if p.is_dir() and transcripts_file(p).exists()]
    return sorted(out, key=lambda p: transcripts_file(p).stat().st_mtime, reverse=True)


def load_run(run_dir: Path) -> tuple[list[dict], list[dict], dict]:
    turns = read_jsonl(transcripts_file(run_dir))
    events = read_jsonl(run_dir / "events.jsonl")
    try:
        cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cfg = {}
    return turns, events, cfg


def ctx_label(rec: dict) -> str:
    return " ".join(f"{k}={rec[k]}" for k in ("phase", "iter", "task", "trial", "group")
                    if rec.get(k) is not None)


# --------------------------------------------------------------------------- #
# merge: transcripts + inline events, in true conversation order
# --------------------------------------------------------------------------- #
# Events that belong INSIDE the conversation rather than beside it. Anything
# else stays out of the transcript view (it is still in events.jsonl).
INLINE_EVENTS = {
    "system_prompt", "tool_result", "tool_call_repeat", "tool_call_flood",
    "episode", "error", "session_start", "session_end",
}


def merge(turns: list[dict], events: list[dict], extra_events: set[str]) -> list[dict]:
    """Both streams interleaved by the global sequence counter obs stamps on
    every line — which is exactly the order things happened, across threads."""
    keep = INLINE_EVENTS | extra_events
    rows = [{**t, "_kind": "turn"} for t in turns]
    rows += [{**e, "_kind": "event"} for e in events
             if e.get("event") in keep or "*" in extra_events]
    return sorted(rows, key=lambda r: r.get("gseq", 0))


def sessions_of(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        sid = r.get("session")
        if sid is not None:
            out.setdefault(str(sid), []).append(r)
    return out


def summarize_session(sid: str, rows: list[dict]) -> dict:
    s = {"session": sid, "task": None, "trial": None, "phase": None,
         "turns": 0, "tool_calls": 0, "tool_errors": 0, "reward": None,
         "ctx_tokens": 0, "cost": 0.0, "flood": False}
    for r in rows:
        for k in ("task", "trial", "phase"):
            if s[k] is None and r.get(k) is not None:
                s[k] = r[k]
        if r["_kind"] == "turn":
            s["turns"] += 1
            s["tool_calls"] += len(r.get("tool_calls") or [])
            s["cost"] += float(r.get("cost") or 0.0)
            # An agent turn's prompt IS its whole context so far, so the max
            # across turns is the context the model ended the episode with.
            if r.get("role") in ("agent", "assistant"):
                tot = (r.get("n_prompt_tokens") or 0) + (r.get("n_completion_tokens") or 0)
                s["ctx_tokens"] = max(s["ctx_tokens"], tot)
        else:
            ev = r.get("event")
            if ev == "episode" and r.get("reward") is not None:
                s["reward"] = r["reward"]
            elif ev == "tool_result" and r.get("error"):
                s["tool_errors"] += 1
            elif ev == "tool_call_flood":
                s["flood"] = True
    return s


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def render_turn(r: dict, show_thinking: bool, width: int) -> str:
    role = r.get("role", "?")
    who = {"agent": "ASSISTANT", "assistant": "ASSISTANT", "user": "USER-SIM"}.get(
        role, str(role).upper())
    colour = CYAN if role in ("agent", "assistant") else MAGENTA
    head = (f"┌─ {who} #{r.get('seq')}  {ctx_label(r)}  "
            f"({r.get('n_completion_tokens')} tok, finish={r.get('finish')})")
    out = [c(head, colour)]
    if show_thinking and r.get("thinking"):
        out += [c(f"│ think  {ln}", DIM) for ln in r["thinking"].strip().splitlines()]
    for tc in r.get("tool_calls") or []:
        args = json.dumps(tc.get("arguments"), ensure_ascii=False, default=str)
        out.append(c(f"│ tool→  {tc.get('name')} {args[:width]}", YELLOW))
    if r.get("content"):
        out += [f"│ reply  {ln}" for ln in str(r["content"]).strip().splitlines()]
    out.append(c("└─", colour))
    return "\n".join(out)


def render_event(r: dict, width: int) -> str:
    ev = r.get("event")
    if ev == "system_prompt":
        body = (r.get("content") or "").strip()
        head = c(f"┌─ SYSTEM PROMPT ({str(r.get('role')).upper()}) "
                 f"— {len(body)} chars", GREEN)
        return "\n".join([head] + [f"│ {ln}" for ln in body.splitlines()] + [c("└─", GREEN)])
    if ev == "tool_result":
        body = (r.get("content") or "").strip()
        colour = RED if r.get("error") else GREEN
        head = c(f"⇐ TOOL RESULT [{'ERROR' if r.get('error') else 'ok'}] "
                 f"{r.get('name') or ''} — {len(body)} chars", colour)
        return "\n".join([head] + [f"│ {ln}" for ln in body.splitlines()])
    if ev == "tool_call_repeat":
        return c(f"⚠ identical tool call x{r.get('count')}: {r.get('name')} "
                 f"{json.dumps(r.get('arguments'), default=str)[:width]}", RED)
    if ev == "tool_call_flood":
        return c(f"⚠ tool-call flood: {r.get('n_tool_calls')} calls "
                 f"(threshold {r.get('threshold')})", RED)
    if ev == "episode":
        return c(f"■ EPISODE DONE  reward={r.get('reward')}  {ctx_label(r)}", BOLD)
    if ev == "error":
        return c(f"✗ ERROR in {r.get('where')}: {r.get('error_type')}: "
                 f"{r.get('error')}", RED)
    if ev in ("session_start", "session_end"):
        return c(f"── {ev} {ctx_label(r)} ──", DIM)
    payload = {k: v for k, v in r.items()
               if k not in ("_kind", "ts", "t", "gseq", "seq", "event")}
    return c(f"· {ev} {json.dumps(payload, default=str)[:width]}", DIM)


def print_session(sid: str, rows: list[dict], args) -> None:
    s = summarize_session(sid, rows)
    reward = s["reward"]
    rcol = GREEN if reward == 1 else RED if reward == 0 else YELLOW
    print()
    print(c("=" * 100, BOLD))
    print(c(f"SESSION {sid[:12]}  task={s['task']} trial={s['trial']}  "
            f"turns={s['turns']} tools={s['tool_calls']} "
            f"errors={s['tool_errors']} ctx={s['ctx_tokens']} "
            f"cost=${s['cost']:.4f}  ", BOLD)
          + c(f"reward={reward}", rcol))
    print(c("=" * 100, BOLD))
    if args.summary:
        return
    for r in rows:
        print(render_turn(r, not args.no_thinking, args.width)
              if r["_kind"] == "turn" else render_event(r, args.width))


# --------------------------------------------------------------------------- #
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", help="run directory (default: newest under --roots)")
    p.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS,
                   help=f"where to look for runs (default: {' '.join(DEFAULT_ROOTS)})")
    p.add_argument("--task", help="only sessions of this task")
    p.add_argument("--trial", type=int, help="only this trial")
    p.add_argument("--session", help="only this session id (prefix ok)")
    p.add_argument("--role", help="only turns of this role")
    p.add_argument("--events", nargs="*", default=[],
                   help="extra event kinds to inline ('*' for all)")
    p.add_argument("--summary", action="store_true", help="session headers only")
    p.add_argument("--no-thinking", action="store_true", help="hide reasoning traces")
    p.add_argument("--width", type=int, default=2000, help="max width per line")
    p.add_argument("--follow", action="store_true",
                   help="poll for new records (a run still writing)")
    p.add_argument("--list", action="store_true", help="list runs and exit")
    args = p.parse_args()

    runs = list_run_dirs(args.roots)
    if args.list:
        for r in runs:
            turns, events, cfg = load_run(r)
            n_sess = len({t.get("session") for t in turns if t.get("session")})
            print(f"{r}  · {n_sess} sessions · {len(turns)} turns "
                  f"· {cfg.get('base_model') or cfg.get('model') or ''}")
        return 0

    run_dir = Path(args.run) if args.run else (runs[0] if runs else None)
    if run_dir is None or not run_dir.is_dir():
        print(f"No run found under {args.roots}. Pass --run explicitly.", file=sys.stderr)
        return 1
    print(c(f"run: {run_dir}", BOLD))

    seen = 0
    while True:
        turns, events, cfg = load_run(run_dir)
        if args.role:
            turns = [t for t in turns if t.get("role") == args.role]
        rows = merge(turns, events, set(args.events))
        rows = [r for r in rows
                if (args.task is None or r.get("task") == args.task)
                and (args.trial is None or r.get("trial") == args.trial)
                and (args.session is None
                     or str(r.get("session") or "").startswith(args.session))]
        if args.follow:
            rows, seen = rows[seen:], len(rows)
            for r in rows:
                print(render_turn(r, not args.no_thinking, args.width)
                      if r["_kind"] == "turn" else render_event(r, args.width))
            time.sleep(2)
            continue

        by_session = sessions_of(rows)
        if not by_session:
            print("(no sessions matched)")
            return 0
        for sid, srows in by_session.items():
            print_session(sid, srows, args)
        if args.summary:
            rewards = [summarize_session(s, r)["reward"] for s, r in by_session.items()]
            got = [x for x in rewards if x is not None]
            if got:
                print()
                print(c(f"{len(got)} graded sessions · mean reward "
                        f"{sum(got) / len(got):.3f}", BOLD))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
