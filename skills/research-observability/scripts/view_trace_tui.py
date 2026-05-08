#!/usr/bin/env python3
"""
view_trace_tui.py — INTERACTIVE (curses) viewer for obs runs.

The interactive sibling of view_trace.py. Reading a 40-turn agent episode as one
scrollback dump does not work: the system prompt and tool results are each
longer than the screen, so the conversation you actually want to read is buried.
This viewer inverts that — everything long is collapsed to a two-line preview
with its true size (lines · chars · words) shown in the header, and you expand
only what you are currently suspicious of.

Three levels, and your cursor position is remembered at each:

    RUN LIST      every run under the roots, newest first, with its config chips
      ↓ Enter
    SESSION LIST  one row per episode: task, turns, tool calls, reward, context
      ↓ Enter
    SESSION VIEW  the conversation, message by message

Keys
    ↓ / j            next message            ↑ / k    previous message
    PgDn / PgUp      jump 5 messages
    → / Enter / l    expand the item under the cursor
    ← / h / ⌫        collapse it (already collapsed: back one level)
    ] / [            scroll one line without moving the cursor
    g / G            first / last message
    e / c            expand all / collapse all
    t                toggle chain-of-thought on every turn
    J                pretty-print tool-call arguments (decode nested JSON strings)
    n                add a note on the message under the cursor
    o                open that message's notes  (inside: a = all notes anywhere)
    a                open ALL notes across every run
    E                export this session to a plain-text file under exports/
    /                filter the session list by task substring
    R                reload from disk (a run still writing)
    q                quit / back

Run it:
    python view_trace_tui.py
    python view_trace_tui.py --roots runs evals_run
    python view_trace_tui.py --run runs/eval-20260802-101500 --task task_007

Everything is read from the obs file format and nothing else, so this works on
any project that writes it — no per-project configuration.
"""
from __future__ import annotations

import argparse
import curses
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from obs import read_jsonl  # noqa: E402
from view_trace import (  # noqa: E402
    INLINE_EVENTS, ctx_label, list_run_dirs, load_run, merge,
    sessions_of, summarize_session, transcripts_file,
)

DEFAULT_ROOTS = ["runs", "sim_runs", "evals_run"]
JUMP = 5
PREVIEW_LINES = 2

# One append-only notes file for the WHOLE system, so a per-message lookup and
# the "all notes" view read the same place. Notes outlive runs on purpose:
# the observation "the model confuses these two policies" is worth more than
# the run that produced it.
NOTES_DIR = Path(os.getenv("OBS_NOTES_DIR", ".obs_notes"))
NOTES_FILE = NOTES_DIR / "notes.jsonl"
EXPORTS_DIR = Path(os.getenv("OBS_EXPORTS_DIR", "exports"))

COLORS = {
    "assistant": (curses.COLOR_CYAN, 0),
    "user": (curses.COLOR_MAGENTA, 0),
    "ok": (curses.COLOR_GREEN, 0),
    "err": (curses.COLOR_RED, 0),
    "warn": (curses.COLOR_YELLOW, 0),
    "meta": (curses.COLOR_BLUE, 0),
    "dim": (curses.COLOR_WHITE, 0),
}
_PAIRS: dict[str, int] = {}


def init_colors() -> None:
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        return
    for i, (name, (fg, _)) in enumerate(COLORS.items(), start=1):
        try:
            curses.init_pair(i, fg, -1)
            _PAIRS[name] = i
        except curses.error:
            pass


def attr(name: str, bold: bool = False) -> int:
    a = curses.color_pair(_PAIRS.get(name, 0))
    return a | curses.A_BOLD if bold else a


def stats(text: str) -> str:
    if not text:
        return "empty"
    return (f"{text.count(chr(10)) + 1} lines · {len(text)} chars · "
            f"{len(text.split())} words")


def unescape(args: Any) -> Any:
    """Decode JSON-string values in place, recursively, so a nested payload
    displays as real JSON instead of one wall of backslashes."""
    if isinstance(args, dict):
        return {k: unescape(v) for k, v in args.items()}
    if isinstance(args, list):
        return [unescape(v) for v in args]
    if isinstance(args, str) and args.lstrip()[:1] in ("{", "["):
        try:
            return unescape(json.loads(args))
        except (json.JSONDecodeError, ValueError):
            pass
    return args


# --------------------------------------------------------------------------- #
# notes
# --------------------------------------------------------------------------- #
def load_notes() -> list[dict]:
    return read_jsonl(NOTES_FILE)


def append_note(rec: dict) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def note_key(run_name: str, session: str, rec: dict, kind: str) -> str:
    """Stable identity of one message: run + session + the record's gseq (or the
    item kind for synthetic rows that have no log line)."""
    g = rec.get("gseq")
    return f"{run_name}/{session}/{'g%s' % g if g is not None else kind}"


# --------------------------------------------------------------------------- #
# items: one row per message/event of a session
# --------------------------------------------------------------------------- #
class Item:
    def __init__(self, kind: str, rec: dict):
        self.kind = kind
        self.rec = rec
        self.expanded = False
        self.note_count = 0
        self.thinking = ""
        self.tool_calls: list[tuple[str, Any]] = []
        self.body = ""
        self.color = "dim"

        if kind == "turn":
            role = rec.get("role", "?")
            who = {"agent": "ASSISTANT", "assistant": "ASSISTANT",
                   "user": "USER-SIM"}.get(role, str(role).upper())
            self.color = "assistant" if role in ("agent", "assistant") else "user"
            self.thinking = (rec.get("thinking") or "").strip()
            self.body = (rec.get("content") or "").strip()
            self.tool_calls = [(tc.get("name"), tc.get("arguments"))
                               for tc in rec.get("tool_calls") or []]
            think_chip = f" · think {len(self.thinking)}c" if self.thinking else ""
            self.header = (f"{who} #{rec.get('seq')}  {ctx_label(rec)}  "
                           f"({rec.get('n_completion_tokens')} tok, "
                           f"finish={rec.get('finish')}{think_chip})")
        elif kind == "system_prompt":
            who = str(rec.get("role", "?")).upper()
            self.color = "ok"
            self.body = (rec.get("content") or "").strip()
            self.header = f"SYSTEM PROMPT ({who})  — {stats(self.body)}"
        elif kind == "tool_result":
            err = bool(rec.get("error"))
            self.color = "err" if err else "ok"
            self.body = (rec.get("content") or "").strip()
            self.header = (f"⇐ TOOL RESULT [{'ERROR' if err else 'ok'}] "
                           f"{rec.get('name') or ''} — {stats(self.body)}")
        elif kind == "episode_meta":
            self.color = "meta"
            self.expanded = True
            self.body = (rec.get("content") or "").strip()
            self.header = rec.get("title", "EPISODE")
        else:  # one-line events
            ev = rec.get("event")
            if ev == "tool_call_repeat":
                self.color = "err"
                self.header = (f"⚠ identical tool call x{rec.get('count')}: "
                               f"{rec.get('name')} "
                               f"{json.dumps(rec.get('arguments'), default=str)}")
            elif ev == "tool_call_flood":
                self.color = "err"
                self.header = (f"⚠ tool-call flood: {rec.get('n_tool_calls')} "
                               f"calls (threshold {rec.get('threshold')})")
            elif ev == "error":
                self.color = "err"
                self.body = (rec.get("traceback") or "").strip()
                self.header = (f"✗ ERROR in {rec.get('where')}: "
                               f"{rec.get('error_type')}: {rec.get('error')}")
            elif ev == "episode":
                self.color = "meta"
                self.header = f"■ EPISODE DONE  reward={rec.get('reward')}  {ctx_label(rec)}"
            else:
                payload = {k: v for k, v in rec.items()
                           if k not in ("_kind", "ts", "t", "gseq", "seq", "event",
                                        "session", "task", "trial", "phase")}
                self.header = f"· {ev}  {json.dumps(payload, default=str)[:160]}"

    @property
    def expandable(self) -> bool:
        return bool(self.body or self.thinking)

    def lines(self, w: int, show_thinking: bool, pretty: bool) -> list[tuple[str, str]]:
        """(text, color) rows for this item at the current width/toggles."""
        badge = f" ✎{self.note_count}" if self.note_count else ""
        out = [(f"{'▾' if self.expanded else '▸' if self.expandable else ' '} "
                f"{self.header}{badge}", self.color)]
        if self.thinking and (show_thinking or self.expanded):
            for ln in self.thinking.splitlines():
                out += [(f"    think  {x}", "dim")
                        for x in textwrap.wrap(ln, max(20, w - 12)) or [""]]
        for name, args in self.tool_calls:
            rendered = (json.dumps(unescape(args), ensure_ascii=False, indent=2,
                                   default=str) if pretty
                        else json.dumps(args, ensure_ascii=False, default=str))
            first = True
            for ln in rendered.splitlines():
                out.append((f"    → {name} {ln}" if first else f"      {ln}", "warn"))
                first = False
        if self.body:
            src = self.body.splitlines()
            shown = src if self.expanded else src[:PREVIEW_LINES]
            for ln in shown:
                out += [(f"    {x}", "dim" if self.kind != "turn" else self.color)
                        for x in textwrap.wrap(ln, max(20, w - 6)) or [""]]
            if not self.expanded and len(src) > PREVIEW_LINES:
                out.append((f"    … +{len(src) - PREVIEW_LINES} more lines (→)", "meta"))
        return out

    def as_text(self) -> str:
        parts = [self.header]
        if self.thinking:
            parts.append("[thinking]\n" + self.thinking)
        for name, args in self.tool_calls:
            parts.append(f"→ {name} {json.dumps(args, ensure_ascii=False, default=str)}")
        if self.body:
            parts.append(self.body)
        return "\n".join(parts)


def build_items(rows: list[dict], summary: dict, cfg: dict) -> list[Item]:
    """Conversation rows plus a header card and a closing metrics card. The
    cards are synthetic (not log lines) — they exist so the two questions you
    always ask, 'what was this run configured as' and 'how did it end', do not
    require leaving the session."""
    head = Item("episode_meta", {
        "title": (f"▣ SESSION {str(summary['session'])[:12]}  task={summary['task']}  "
                  f"trial={summary['trial']}"),
        "content": json.dumps({k: v for k, v in cfg.items()
                               if not k.startswith("_")}, indent=2, default=str),
    })
    items = [head]
    for r in rows:
        if r["_kind"] == "turn":
            items.append(Item("turn", r))
        else:
            ev = r.get("event")
            if ev in ("session_start", "session_end"):
                continue
            items.append(Item(ev if ev in ("system_prompt", "tool_result") else "event", r))
    items.append(Item("episode_meta", {
        "title": (f"⚖ OUTCOME  reward={summary['reward']}  "
                  f"turns={summary['turns']} tools={summary['tool_calls']} "
                  f"tool_errors={summary['tool_errors']} "
                  f"ctx={summary['ctx_tokens']} tok  cost=${summary['cost']:.4f}"),
        "content": json.dumps(summary, indent=2, default=str),
    }))
    return items


# --------------------------------------------------------------------------- #
# generic scrolling list screen
# --------------------------------------------------------------------------- #
def pick(stdscr, title: str, rows: list[tuple[str, str]], start: int = 0,
         footer: str = "↑↓ move · Enter select · q back") -> Optional[int]:
    """Cursor list. Returns the chosen index, or None on q/←."""
    cur, top = start, 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addnstr(0, 0, title, w - 1, attr("meta", True))
        body_h = h - 3
        if cur < top:
            top = cur
        elif cur >= top + body_h:
            top = cur - body_h + 1
        for i in range(top, min(len(rows), top + body_h)):
            text, colour = rows[i]
            a = attr(colour, bold=(i == cur))
            if i == cur:
                a |= curses.A_REVERSE
            stdscr.addnstr(1 + i - top, 0, f" {text}", w - 1, a)
        stdscr.addnstr(h - 1, 0, footer, w - 1, attr("dim"))
        stdscr.refresh()
        k = stdscr.getch()
        if k in (ord("q"), 27, curses.KEY_LEFT, ord("h")):
            return None
        if k in (curses.KEY_DOWN, ord("j")):
            cur = min(len(rows) - 1, cur + 1)
        elif k in (curses.KEY_UP, ord("k")):
            cur = max(0, cur - 1)
        elif k == curses.KEY_NPAGE:
            cur = min(len(rows) - 1, cur + body_h)
        elif k == curses.KEY_PPAGE:
            cur = max(0, cur - body_h)
        elif k == ord("g"):
            cur = 0
        elif k == ord("G"):
            cur = len(rows) - 1
        elif k in (curses.KEY_ENTER, 10, 13, curses.KEY_RIGHT, ord("l")):
            return cur


def prompt(stdscr, label: str) -> str:
    h, w = stdscr.getmaxyx()
    curses.echo()
    curses.curs_set(1)
    stdscr.addnstr(h - 1, 0, " " * (w - 1), w - 1)
    stdscr.addnstr(h - 1, 0, label, w - 1, attr("warn", True))
    stdscr.refresh()
    try:
        text = stdscr.getstr(h - 1, len(label) + 1, w - len(label) - 3).decode("utf-8")
    except Exception:
        text = ""
    curses.noecho()
    curses.curs_set(0)
    return text.strip()


def show_text(stdscr, title: str, body: str) -> None:
    lines = body.splitlines() or ["(empty)"]
    top = 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addnstr(0, 0, title, w - 1, attr("meta", True))
        for i, ln in enumerate(lines[top:top + h - 3]):
            stdscr.addnstr(1 + i, 0, ln, w - 1)
        stdscr.addnstr(h - 1, 0, "↑↓ scroll · q back", w - 1, attr("dim"))
        stdscr.refresh()
        k = stdscr.getch()
        if k in (ord("q"), 27, curses.KEY_LEFT):
            return
        if k in (curses.KEY_DOWN, ord("j")):
            top = min(max(0, len(lines) - 1), top + 1)
        elif k in (curses.KEY_UP, ord("k")):
            top = max(0, top - 1)
        elif k == curses.KEY_NPAGE:
            top = min(max(0, len(lines) - 1), top + h)
        elif k == curses.KEY_PPAGE:
            top = max(0, top - h)


# --------------------------------------------------------------------------- #
# session view
# --------------------------------------------------------------------------- #
def session_view(stdscr, run_dir: Path, sid: str, rows: list[dict], cfg: dict) -> None:
    summary = summarize_session(sid, rows)
    items = build_items(rows, summary, cfg)
    notes = load_notes()
    for it in items:
        key = note_key(run_dir.name, sid, it.rec, it.kind)
        it.note_count = sum(1 for n in notes if n.get("key") == key)

    cur, top, show_thinking, pretty = 0, 0, False, False
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        rcol = ("ok" if summary["reward"] == 1
                else "err" if summary["reward"] == 0 else "warn")
        stdscr.addnstr(0, 0,
                       f" {run_dir.name} · {summary['task']} trial={summary['trial']} "
                       f"· turns={summary['turns']} tools={summary['tool_calls']} "
                       f"ctx={summary['ctx_tokens']} tok ", w - 1, attr("meta", True))
        stdscr.addnstr(0, max(0, w - 18), f" reward={summary['reward']} ",
                       17, attr(rcol, True))

        blocks = [it.lines(w, show_thinking, pretty) for it in items]
        offsets, n = [], 0
        for b in blocks:
            offsets.append(n)
            n += len(b)
        body_h = h - 2
        # Keep the cursor's block on screen; a block taller than the screen
        # pins to its top so you can still line-scroll it with ] / [.
        if offsets[cur] < top:
            top = offsets[cur]
        elif offsets[cur] + len(blocks[cur]) > top + body_h:
            top = min(offsets[cur], max(0, offsets[cur] + len(blocks[cur]) - body_h))

        flat = [(ln, col, i) for i, b in enumerate(blocks) for (ln, col) in b]
        for row, (ln, col, idx) in enumerate(flat[top:top + body_h]):
            a = attr(col, bold=(idx == cur))
            if idx == cur and row == 0 or (idx == cur and flat[top + row - 1][2] != cur):
                a |= curses.A_REVERSE
            stdscr.addnstr(1 + row, 0, ln, w - 1, a)
        stdscr.addnstr(h - 1, 0,
                       "↓↑ move · → expand · t think · J json · n note · o notes "
                       "· E export · q back", w - 1, attr("dim"))
        stdscr.refresh()

        k = stdscr.getch()
        if k in (ord("q"), 27):
            return
        elif k in (curses.KEY_DOWN, ord("j")):
            cur = min(len(items) - 1, cur + 1)
        elif k in (curses.KEY_UP, ord("k")):
            cur = max(0, cur - 1)
        elif k == curses.KEY_NPAGE:
            cur = min(len(items) - 1, cur + JUMP)
        elif k == curses.KEY_PPAGE:
            cur = max(0, cur - JUMP)
        elif k == ord("g"):
            cur = 0
        elif k == ord("G"):
            cur = len(items) - 1
        elif k in (curses.KEY_RIGHT, ord("l"), curses.KEY_ENTER, 10, 13):
            items[cur].expanded = True
        elif k in (curses.KEY_LEFT, ord("h"), curses.KEY_BACKSPACE, 127):
            if items[cur].expanded:
                items[cur].expanded = False
            else:
                return
        elif k == ord("]"):
            top = min(max(0, n - 1), top + 1)
        elif k == ord("["):
            top = max(0, top - 1)
        elif k == ord("e"):
            for it in items:
                it.expanded = True
        elif k == ord("c"):
            for it in items:
                it.expanded = False
        elif k == ord("t"):
            show_thinking = not show_thinking
        elif k == ord("J"):
            pretty = not pretty
        elif k == ord("n"):
            text = prompt(stdscr, "note:")
            if text:
                it = items[cur]
                append_note({
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "key": note_key(run_dir.name, sid, it.rec, it.kind),
                    "run": run_dir.name, "session": sid,
                    "task": summary["task"], "trial": summary["trial"],
                    "header": it.header, "excerpt": it.body[:500], "note": text,
                })
                it.note_count += 1
        elif k == ord("o"):
            key = note_key(run_dir.name, sid, items[cur].rec, items[cur].kind)
            mine = [nn for nn in load_notes() if nn.get("key") == key]
            show_text(stdscr, f"notes on {items[cur].header[:60]}",
                      "\n\n".join(f"[{nn['ts']}] {nn['note']}" for nn in mine)
                      or "(no notes yet — press n)")
        elif k == ord("a"):
            allnotes = load_notes()
            show_text(stdscr, f"ALL NOTES ({len(allnotes)})",
                      "\n\n".join(f"[{nn.get('ts')}] {nn.get('run')} "
                                  f"{nn.get('task')}\n  {nn.get('header', '')[:90]}\n"
                                  f"  → {nn.get('note')}" for nn in allnotes)
                      or "(none)")
        elif k == ord("E"):
            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            name = prompt(stdscr, "export filename:") or \
                f"{summary['task']}_t{summary['trial']}_{run_dir.name}.txt"
            path = EXPORTS_DIR / name
            path.write_text("\n\n".join(it.as_text() for it in items), encoding="utf-8")
            show_text(stdscr, "exported", str(path.resolve()))
        elif k == ord("R"):
            return


# --------------------------------------------------------------------------- #
def session_rows(run_dir: Path, task: Optional[str]) -> tuple[list, dict, dict]:
    turns, events, cfg = load_run(run_dir)
    rows = merge(turns, events, set())
    if task:
        rows = [r for r in rows if str(r.get("task") or "").find(task) >= 0]
    return rows, sessions_of(rows), cfg


def run(stdscr, roots: list[str], only_run: Optional[str], task: Optional[str]) -> None:
    curses.curs_set(0)
    init_colors()
    runs = [Path(only_run)] if only_run else list_run_dirs(roots)
    if not runs:
        show_text(stdscr, "no runs", f"Nothing found under: {', '.join(roots)}")
        return

    notes = load_notes()
    per_run: dict[str, int] = {}
    for nn in notes:
        per_run[nn.get("run", "")] = per_run.get(nn.get("run", ""), 0) + 1

    run_cur = 0
    while True:
        rows = []
        for r in runs:
            try:
                cfg = json.loads((r / "config.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                cfg = {}
            chips = [str(cfg[k]) for k in ("base_model", "model", "agent_model",
                                           "domain") if cfg.get(k)]
            if per_run.get(r.name):
                chips.append(f"✎{per_run[r.name]}")
            rows.append((f"{r.parent.name}/{r.name}"
                         + (f"   · {' · '.join(chips)}" if chips else ""), "dim"))
        idx = pick(stdscr, " RUNS (newest first) ", rows, run_cur)
        if idx is None:
            return
        run_cur = idx
        run_dir = runs[idx]

        sess_cur, task_filter = 0, task
        while True:
            all_rows, by_session, cfg = session_rows(run_dir, task_filter)
            sids = list(by_session)
            if not sids:
                show_text(stdscr, "no sessions", f"{run_dir} has no session rows.")
                break
            summaries = [summarize_session(s, by_session[s]) for s in sids]
            srows = []
            for s in summaries:
                col = ("ok" if s["reward"] == 1 else "err" if s["reward"] == 0
                       else "warn" if s["reward"] is not None else "dim")
                srows.append((
                    f"{str(s['task'] or '?'):<22} t{s['trial']}  "
                    f"turns={s['turns']:<3} tools={s['tool_calls']:<3} "
                    f"err={s['tool_errors']:<2} ctx={s['ctx_tokens']:<6} "
                    f"{'FLOOD ' if s['flood'] else '      '}"
                    f"reward={s['reward']}", col))
            title = (f" {run_dir.name}  ·  {len(sids)} sessions"
                     + (f"  ·  filter={task_filter}" if task_filter else ""))
            j = pick(stdscr, title, srows, min(sess_cur, len(srows) - 1),
                     footer="Enter open · / filter · R reload · q back")
            if j is None:
                break
            sess_cur = j
            session_view(stdscr, run_dir, sids[j], by_session[sids[j]], cfg)


def main() -> int:
    p = argparse.ArgumentParser(description="Interactive viewer for obs runs")
    p.add_argument("--run", help="open this run directly")
    p.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    p.add_argument("--task", help="filter sessions by task substring")
    args = p.parse_args()
    curses.wrapper(run, args.roots, args.run, args.task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
