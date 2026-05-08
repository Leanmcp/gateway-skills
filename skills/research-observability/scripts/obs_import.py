#!/usr/bin/env python3
"""
obs_import.py — backfill EXISTING experiment outputs into the obs format.

Adding observability to a project usually means the last six months of runs
stay invisible, which is exactly backwards: those are the runs you most want to
compare against. This converts already-finished results into an obs run folder,
so old and new experiments show up side by side in the same viewers and the
same report table.

It handles the shapes ad-hoc experiment code actually produces:

  * a JSON file that is a list of episodes, or an object with a list under
    results / episodes / simulations / runs / data
  * a directory of one-JSON-per-episode files
  * a JSONL file, one episode per line

From each episode it looks for a conversation under messages / conversation /
transcript / history (OpenAI-style role/content dicts, with tool_calls and
role="tool" results understood), an id, a task id, and a reward under
reward / score / reward_info.reward / metrics.reward. Anything it does not
recognize is preserved verbatim in the episode artifact, so nothing is lost —
worst case you get a run whose transcript is thin but whose artifacts are whole.

    python obs_import.py results.json --out runs --name legacy-gpt4-sweep
    python obs_import.py old_results/ --out runs --task-key task_id
    python obs_import.py runs.jsonl --out runs --dry-run

Always check with --dry-run first: it prints what it found and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from obs import Run, read_jsonl  # noqa: E402

LIST_KEYS = ("results", "episodes", "simulations", "runs", "data", "records")
MSG_KEYS = ("messages", "conversation", "transcript", "history", "turns")
REWARD_KEYS = ("reward", "score", "return", "success")
TASK_KEYS = ("task_id", "task", "id", "name", "scenario")


def _first(d: dict, keys: Iterable[str]) -> Any:
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def load_episodes(src: Path) -> list[dict]:
    """Every episode found at `src`, whatever container it came in."""
    if src.is_dir():
        out = []
        for p in sorted(src.rglob("*.json")):
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.extend(obj if isinstance(obj, list) else [obj])
        return out
    if src.suffix == ".jsonl":
        return read_jsonl(src)
    obj = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return obj
    inner = _first(obj, LIST_KEYS)
    if isinstance(inner, list):
        return inner
    return [obj]


def find_reward(ep: dict) -> Optional[float]:
    v = _first(ep, REWARD_KEYS)
    if v is None:
        for holder in ("reward_info", "metrics", "evaluation", "grading"):
            sub = ep.get(holder)
            if isinstance(sub, dict):
                v = _first(sub, REWARD_KEYS)
                if v is not None:
                    break
    if v is None:
        return None
    if isinstance(v, bool):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def find_messages(ep: dict) -> list[dict]:
    msgs = _first(ep, MSG_KEYS)
    if isinstance(msgs, list):
        return [m for m in msgs if isinstance(m, dict)]
    for holder in ("simulation", "result", "run", "trajectory"):
        sub = ep.get(holder)
        if isinstance(sub, dict):
            msgs = _first(sub, MSG_KEYS)
            if isinstance(msgs, list):
                return [m for m in msgs if isinstance(m, dict)]
    return []


def norm_tool_calls(m: dict) -> list[dict]:
    out = []
    for tc in m.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") if isinstance(tc.get("function"), dict) else tc
        args = fn.get("arguments", fn.get("args"))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, ValueError):
                pass
        out.append({"name": fn.get("name"), "arguments": args, "id": tc.get("id")})
    return out


def replay(run: Run, ep: dict, task_key: Optional[str], idx: int) -> None:
    task = (ep.get(task_key) if task_key else None) or _first(ep, TASK_KEYS) or f"ep{idx}"
    sid = str(ep.get("id") or ep.get("session") or f"{task}-{idx}")
    with run.session(session=sid, task=str(task), trial=ep.get("trial")):
        for m in find_messages(ep):
            role = str(m.get("role") or "assistant")
            content = m.get("content")
            if isinstance(content, list):  # Anthropic-style block list
                content = "\n".join(b.get("text", "") for b in content
                                    if isinstance(b, dict))
            content = "" if content is None else str(content)
            if role == "system":
                run.system_prompt("agent", content)
            elif role == "tool":
                run.tool_result(requestor="agent", name=m.get("name"),
                                tool_call_id=m.get("tool_call_id"),
                                error=bool(m.get("error")), content=content)
            else:
                run.sample(
                    "agent" if role in ("assistant", "agent") else role,
                    text=content, content=content or None,
                    thinking=m.get("thinking") or m.get("reasoning_content"),
                    tool_calls=norm_tool_calls(m),
                    finish=m.get("finish_reason"),
                    usage=m.get("usage") if isinstance(m.get("usage"), dict) else None,
                    cost=m.get("cost"),
                    imported=True,
                )
        reward = find_reward(ep)
        run.episode_done(reward=reward)
        run.artifact(ep, name=sid, reward=reward, imported=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="JSON / JSONL file, or directory of JSONs")
    p.add_argument("--out", default="runs", help="obs runs root (default: runs)")
    p.add_argument("--name", help="run folder name (default: imported-<source>)")
    p.add_argument("--task-key", help="explicit key holding the task id")
    p.add_argument("--config", help="JSON file describing the original run's config")
    p.add_argument("--dry-run", action="store_true", help="report findings, write nothing")
    args = p.parse_args()

    src = Path(args.source)
    episodes = load_episodes(src)
    if not episodes:
        print(f"No episodes found in {src}", file=sys.stderr)
        return 1

    sample = episodes[0]
    n_msgs = len(find_messages(sample))
    n_graded = sum(1 for e in episodes if find_reward(e) is not None)
    print(f"source        : {src}")
    print(f"episodes      : {len(episodes)}  ({n_graded} with a reward)")
    print(f"first episode : keys={sorted(sample)[:12]}")
    print(f"                {n_msgs} messages detected")
    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0
    if n_msgs == 0:
        print("\nWARN: no conversation found; artifacts will be written but the "
              "transcript will be empty. Pass the right container or extend "
              "MSG_KEYS in this file.", file=sys.stderr)

    cfg = {"_imported_from": str(src.resolve())}
    if args.config:
        cfg.update(json.loads(Path(args.config).read_text(encoding="utf-8")))
    with Run("imported", config=cfg, root=args.out,
             run_name=args.name or f"imported-{src.stem}") as run:
        for i, ep in enumerate(episodes):
            try:
                replay(run, ep, args.task_key, i)
            except Exception as e:  # one malformed episode must not kill the import
                run.error("import", e, episode_index=i)
        print(f"\nimported {len(episodes)} episodes → {run.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
