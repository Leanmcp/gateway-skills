#!/usr/bin/env python3
"""
obs.py — local, append-only observability for LLM agent experiments.

Platform-agnostic core. Nothing in this file imports a provider SDK, knows what
a "task" is, or cares whether the model is served by OpenAI, Gemini, Anthropic,
Tinker, vLLM or a local process. It records the pathways of a run to plain JSONL
on disk so you can replay, diff and plot it later — and optionally mirrors the
scalar metrics to Weights & Biases.

The bet this file makes: hosted dashboards capture almost nothing you can grep,
diff, or re-grade six months later. Files do. Everything here is append-only and
flushed per write, so a run that dies at iteration 7/10 keeps iterations 0-6.

One `Run` == one invocation (train, eval, sweep shard, ...). It opens a
timestamped folder:

    <root>/<kind>-<YYYYmmdd-HHMMSS>/
        config.json         # the run's config/args (written once, at start)
        events.jsonl        # every discrete event: samples (summary), tool
                            #   results, system prompts, episodes, errors, and
                            #   any custom event you emit
        metrics.jsonl       # per-step scalar time-series (pandas-shaped:
                            #   pd.read_json(path, lines=True) -> plot)
        transcripts.jsonl   # FULL per-turn transcripts: decoded text, parsed
                            #   content, thinking, every tool call with complete
                            #   arguments, and token ids when the platform
                            #   exposes them (one line per sampled turn)
        episodes/           # one self-contained JSON per finished episode
            index.jsonl     #   + one summary line each, for fast scanning

Usage sketch:

    from obs import Run

    run = Run("eval", config={"model": "gemini-3-pro", "n": 26},
              root="runs", wandb_project=os.getenv("WANDB_PROJECT"))

    with run.session(task="task_007", trial=0) as sid:
        run.system_prompt("agent", policy_text)
        run.sample("agent", text=reply, content=reply, tool_calls=[...],
                   thinking=cot, finish="stop", usage={...})
        run.tool_result(requestor="agent", content=result_json)
        run.episode_done(reward=1.0, n_turns=8)
        run.artifact(episode_obj, reward=1.0)

    run.metric(step=it, mean_reward=0.62, loss=0.41)
    run.close()

Every one of those calls is optional and independently useful. Wire the ones
your platform can supply; the viewers degrade gracefully around what is missing.

Environment knobs (prefix defaults to OBS, override per-Run with
`Run(..., env_prefix="TAU2")` so an existing project's variables keep working):

    <P>_ECHO=full|preview|off    live per-turn echo to stdout (default full)
    <P>_PREVIEW_CHARS=240        truncation width for previews
    <P>_TOOL_REPEAT_WARN=3       emit tool_call_repeat at N identical calls
    <P>_TOOL_TOTAL_WARN=15       emit tool_call_flood once past N calls/session
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence

__all__ = ["Run", "read_jsonl"]

DEFAULT_ROOT = Path(os.getenv("OBS_ROOT", "runs"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path | str) -> list[dict]:
    """Every parsed line of a JSONL file. A torn tail line (a run still
    writing) is skipped rather than raising — you can read a live run."""
    path = Path(path)
    if not path.exists():
        return []
    out: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


class Run:
    """A single observed run. Owns the JSONL streams + optional wandb mirror.

    Thread-safe: every write holds a lock, and the per-turn context (the tags
    stamped onto each record) is thread-local, so concurrent rollouts can each
    set their own task/session without clobbering a sibling's tags.
    """

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        kind: str,
        *,
        config: Optional[dict[str, Any]] = None,
        root: Path | str = DEFAULT_ROOT,
        run_name: Optional[str] = None,
        wandb_project: Optional[str] = None,
        wandb_run_name: Optional[str] = None,
        env_prefix: str = "OBS",
    ):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = run_name or f"{kind}-{stamp}"
        self.dir = Path(root) / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.kind = kind
        self.name = name

        # --- env knobs, read once, under the caller's prefix -------------- #
        def _env(key: str, default: str) -> str:
            return os.getenv(f"{env_prefix}_{key}", default).strip()

        self.echo_mode = _env("ECHO", "full").lower()
        self.preview_chars = int(_env("PREVIEW_CHARS", "240"))
        self.tool_repeat_warn = int(_env("TOOL_REPEAT_WARN", "3"))
        self.tool_total_warn = int(_env("TOOL_TOTAL_WARN", "15"))

        self._lock = threading.Lock()
        self._t0 = time.time()
        # Context is PER THREAD, with the last main-thread value as the base for
        # threads that never set one. A single shared dict makes concurrent
        # rollouts impossible: two workers would overwrite each other's tags and
        # file each other's events under the wrong task.
        self._ctx_local = threading.local()
        self._root_ctx: dict[str, Any] = {}
        self._main_thread = threading.get_ident()
        # Per-session sequence: each session gets its own counter from 0, so
        # message order WITHIN a conversation is well-defined even when many
        # sessions interleave on disk. `gseq` is a global monotonic tiebreaker.
        self._seq_by_session: dict[str, int] = {}
        self._gseq = 0
        self._tool_counts: dict[str, dict[str, int]] = {}
        self._flooded: set[str] = set()
        self._sysprompt_seen: set[tuple[str, str, int]] = set()
        self._closed = False

        self._events = open(self.dir / "events.jsonl", "a", encoding="utf-8")
        self._metrics = open(self.dir / "metrics.jsonl", "a", encoding="utf-8")
        self._transcripts = open(self.dir / "transcripts.jsonl", "a", encoding="utf-8")

        cfg = dict(config or {})
        cfg.update({"_kind": kind, "_started_at": _now_iso(), "_dir": str(self.dir)})
        with open(self.dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, default=str)

        self._wandb = None
        if wandb_project:
            try:
                import wandb  # lazy: only needed when a project is set

                wandb_dir = Path(root).parent / "wandb_runs"
                wandb_dir.mkdir(parents=True, exist_ok=True)
                self._wandb = wandb.init(
                    project=wandb_project,
                    name=wandb_run_name or name,
                    config=cfg,
                    dir=str(wandb_dir),
                )
            except Exception as e:  # logging must never break the experiment
                print(f"[obs] wandb disabled ({e!r}); local JSONL only.")
                self._wandb = None

        print(f"[obs] run dir: {self.dir}")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.event("run_end", elapsed_s=round(time.time() - self._t0, 3))
        with self._lock:
            for fh in (self._events, self._metrics, self._transcripts):
                try:
                    fh.close()
                except Exception:
                    pass
        if self._wandb is not None:
            try:
                self._wandb.finish()
            except Exception:
                pass

    def __enter__(self) -> "Run":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # context: tags stamped onto every subsequent record
    # ------------------------------------------------------------------ #
    @property
    def _ctx(self) -> dict[str, Any]:
        own = getattr(self._ctx_local, "ctx", None)
        return dict(self._root_ctx) if own is None else own

    def set_context(self, **kw: Any) -> None:
        """Replace this THREAD's tags (task/trial/iter/session/phase/...).

        A worker rolling out one episode sets its own; it will not inherit a
        sibling's and cannot clobber it."""
        ctx = {k: v for k, v in kw.items() if v is not None}
        self._ctx_local.ctx = ctx
        if threading.get_ident() == self._main_thread:
            with self._lock:
                self._root_ctx = dict(ctx)

    def update_context(self, **kw: Any) -> None:
        ctx = dict(self._ctx)
        ctx.update({k: v for k, v in kw.items() if v is not None})
        self._ctx_local.ctx = ctx
        if threading.get_ident() == self._main_thread:
            with self._lock:
                self._root_ctx = dict(ctx)

    @contextmanager
    def session(self, session: Optional[str] = None, **tags: Any) -> Iterator[str]:
        """Scope one episode/conversation. Yields the session id.

        A `session` id is what stitches turns into a conversation for the
        viewers — without one, records are still logged but appear as loose
        messages. Restores the previous context on exit, so nesting is safe.

            with run.session(task="task_007", trial=0) as sid:
                ...
        """
        sid = session or uuid.uuid4().hex
        prev = getattr(self._ctx_local, "ctx", None)
        self.update_context(session=sid, **tags)
        self.event("session_start")
        try:
            yield sid
        finally:
            self.event("session_end")
            self._ctx_local.ctx = prev

    # ------------------------------------------------------------------ #
    # low-level writers
    # ------------------------------------------------------------------ #
    def _reserve_seq(self, sid: Optional[str]) -> Optional[int]:
        """Reserve the next per-session sequence number. Used when ONE logical
        message spans two physical lines (a sample's summary + its transcript)
        so both share a single seq."""
        if sid is None:
            return None
        with self._lock:
            seq = self._seq_by_session.get(str(sid), 0)
            self._seq_by_session[str(sid)] = seq + 1
            return seq

    def _write(self, fh, obj: dict[str, Any]) -> None:
        with self._lock:
            if "seq" not in obj:
                sid = obj.get("session")
                if sid is not None:
                    seq = self._seq_by_session.get(str(sid), 0)
                    self._seq_by_session[str(sid)] = seq + 1
                    obj["seq"] = seq
                else:
                    obj["seq"] = None
            obj["gseq"] = self._gseq
            self._gseq += 1
            fh.write(json.dumps(obj, default=str) + "\n")
            fh.flush()

    # ------------------------------------------------------------------ #
    # the public logging surface
    # ------------------------------------------------------------------ #
    def event(self, kind: str, *, seq: Any = "auto", **payload: Any) -> None:
        """Append one discrete event to events.jsonl, tagged with the current
        context. Use it for anything the schema below does not cover —
        retrieval hits, retries, guardrail trips, cache misses, your own
        domain milestones. Unknown event kinds are carried through the viewers
        as one-line rows, so inventing one costs nothing."""
        rec = {
            "ts": _now_iso(),
            "t": round(time.time() - self._t0, 3),
            "event": kind,
            **self._ctx,
            **payload,
        }
        if seq != "auto":
            rec["seq"] = seq
        self._write(self._events, rec)

    def error(self, where: str, exc: BaseException, **payload: Any) -> None:
        """One failure, with its traceback, as a first-class event. Failures
        that only exist in stderr are invisible to every later analysis."""
        import traceback

        self.event(
            "error",
            where=where,
            error_type=type(exc).__name__,
            error=str(exc),
            traceback="".join(traceback.format_exception(exc))[-4000:],
            **payload,
        )

    def metric(self, step: Optional[int] = None, **scalars: Any) -> None:
        """Append one row of scalar metrics (+ wandb if enabled).

        Shaped so `pd.read_json("metrics.jsonl", lines=True)` gives a tidy
        time-series frame you can plot without reshaping."""
        rec = {"ts": _now_iso(), "t": round(time.time() - self._t0, 3)}
        if step is not None:
            rec["step"] = step
        rec.update(scalars)
        self._write(self._metrics, rec)
        if self._wandb is not None:
            try:
                self._wandb.log(dict(scalars), step=step)
            except Exception:
                pass

    def sample(
        self,
        role: str,
        prompt_tokens: Optional[Sequence[int]] = None,
        completion_tokens: Optional[Sequence[int]] = None,
        text: str = "",
        *,
        finish: Optional[str] = None,
        content: Optional[str] = None,
        tool_calls: Optional[list[dict]] = None,
        thinking: Optional[str] = None,
        usage: Optional[dict] = None,
        cost: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """Log ONE model generation — nothing dropped.

        Two streams, by design, because they answer different questions:
          * events.jsonl     — scannable summary: role, token counts, finish
            reason, tool-call NAMES, a short preview. Grep this.
          * transcripts.jsonl — the full turn: raw text, parsed content,
            thinking, every tool call with complete arguments, and token ids
            when the platform exposes them. Replay this.

        `role` is free-form; "agent" and "user" get friendly labels in the
        viewers, everything else is shown verbatim (use "judge", "summarizer",
        "planner", ... for auxiliary models — they belong in the trace too).

        `prompt_tokens` / `completion_tokens` are optional: token-level
        platforms (Tinker, vLLM, raw HF) have them, hosted APIs do not. Pass
        `usage={"prompt_tokens": n, "completion_tokens": m}` instead and the
        counts still land in the record.
        """
        tool_calls = tool_calls or []
        prompt_tokens = list(prompt_tokens or [])
        completion_tokens = list(completion_tokens or [])
        usage = usage if isinstance(usage, dict) else (
            dict(usage) if usage is not None and hasattr(usage, "keys") else None
        )
        n_prompt = len(prompt_tokens) or int((usage or {}).get("prompt_tokens") or 0)
        n_completion = len(completion_tokens) or int(
            (usage or {}).get("completion_tokens") or 0
        )

        # One message == one per-session seq, shared by BOTH lines below.
        msg_seq = self._reserve_seq(self._ctx.get("session"))
        extra = {k: v for k, v in extra.items() if k != "n_tool_calls"}

        self.event(
            "sample",
            seq=msg_seq,
            role=role,
            n_prompt_tokens=n_prompt,
            n_completion_tokens=n_completion,
            finish=finish,
            cost=cost,
            n_tool_calls=len(tool_calls),
            tool_names=[tc.get("name") for tc in tool_calls],
            text_preview=(text or "")[: self.preview_chars],
            thinking_preview=(thinking or "")[: self.preview_chars],
            **extra,
        )
        self._write(
            self._transcripts,
            {
                "ts": _now_iso(),
                **self._ctx,
                "seq": msg_seq,
                "role": role,
                "finish": finish,
                "n_prompt_tokens": n_prompt,
                "n_completion_tokens": n_completion,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "text": text,
                "thinking": thinking,
                "content": content if content is not None else text,
                "tool_calls": tool_calls,
                "usage": usage,
                "cost": cost,
                **extra,
            },
        )
        if self.echo_mode != "off":
            self._echo_turn(role, msg_seq, finish, thinking, content or text,
                            tool_calls, n_completion, text)
        self._track_tool_calls(role, tool_calls)

    def system_prompt(self, role: str, text: str) -> None:
        """Log the system prompt a speaker runs under, ONCE per (session, role,
        content). Deduped on purpose: it is constant within an episode, so
        logging it per turn would bury the conversation — but not logging it at
        all is worse, because six months later the policy text is the first
        thing you need in order to explain a behaviour."""
        text = text or ""
        key = (str(self._ctx.get("session")), role, hash(text))
        with self._lock:
            if key in self._sysprompt_seen:
                return
            self._sysprompt_seen.add(key)
        self.event("system_prompt", role=role, n_chars=len(text), content=text)
        if self.echo_mode != "off":
            out = [f"\n┌─ SYSTEM PROMPT ({self._who(role)})  [{self._ctx_label()}]"]
            out += [f"│ {ln}" for ln in self._clip(text.strip()).splitlines()]
            out.append("└─")
            print("\n".join(out), flush=True)

    def tool_result(
        self,
        *,
        requestor: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        error: bool = False,
        content: Optional[str] = None,
        duration_s: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """Log one executed tool RESULT — the environment's answer to a call.

        Tools usually run BETWEEN sampled turns, so results never pass through
        sample(). Emit them as they arrive and the trace reads in true
        conversation order: turn -> tool result -> next turn. Skip this and
        you get traces where the agent calls tools into a void, which is
        useless for diagnosing why it then did something strange."""
        content = content or ""
        self.event(
            "tool_result",
            requestor=requestor,
            name=name,
            tool_call_id=tool_call_id,
            error=bool(error),
            duration_s=duration_s,
            n_chars=len(content),
            content=content,
            **extra,
        )
        if self.echo_mode != "off":
            status = "ERROR" if error else "ok"
            out = [f"┌─ TOOL RESULT [{status}] {name or ''}  [{self._ctx_label()}]"]
            out += [f"│ {ln}" for ln in self._clip(content.strip()).splitlines()]
            out.append("└─")
            print("\n".join(out), flush=True)

    def episode_done(self, *, reward: Optional[float] = None, **payload: Any) -> None:
        """Close out one episode with its outcome. The viewers key their
        per-session verdict colours off this."""
        self.event("episode", reward=reward, **payload)

    def artifact(self, obj: Any, *, name: Optional[str] = None, **meta: Any) -> Path:
        """Save one FULL finished episode as a standalone JSON file.

        Where sample()/event() are per-turn append-only streams, this captures
        the complete episode in one self-contained, human-readable file: the
        whole result object (grading breakdown, every message, termination
        reason) plus whatever `meta` you attach. One file per episode:

            <run dir>/episodes/<phase>__<task>__trial<k>__<id>.json

        plus one summary line in episodes/index.jsonl so a whole run can be
        scanned without opening the big files.

        `obj` may be a pydantic model (dumped via model_dump), a dataclass, or
        a plain dict.
        """
        def _dump(o: Any) -> Any:
            if o is None or isinstance(o, (dict, list, str, int, float, bool)):
                return o
            if hasattr(o, "model_dump"):
                return o.model_dump(mode="json")
            if hasattr(o, "__dataclass_fields__"):
                import dataclasses

                return dataclasses.asdict(o)
            if hasattr(o, "__dict__"):
                return {k: str(v) for k, v in vars(o).items()}
            return str(o)

        def _safe(s: Any) -> str:
            return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(s)) or "x"

        eps = self.dir / "episodes"
        eps.mkdir(exist_ok=True)
        phase = meta.get("phase") or self._ctx.get("phase") or self.kind
        task = self._ctx.get("task") or "episode"
        trial = self._ctx.get("trial")
        eid = str(name or self._ctx.get("session") or self._gseq)
        fname = (
            f"{_safe(phase)}__{_safe(task)}"
            + (f"__trial{trial}" if trial is not None else "")
            + f"__{_safe(eid)[:12]}.json"
        )
        path = eps / fname

        record = {"ts": _now_iso(), **self._ctx, **meta, "episode": _dump(obj)}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        summary = {
            "ts": record["ts"],
            **self._ctx,
            **{k: v for k, v in meta.items() if not isinstance(v, (dict, list))},
            "file": fname,
        }
        with self._lock:
            with open(eps / "index.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, default=str) + "\n")
        self.event("artifact_saved", file=str(path.relative_to(self.dir)))
        return path

    # ------------------------------------------------------------------ #
    # live echo + tool-call flood detection
    # ------------------------------------------------------------------ #
    def _clip(self, s: str) -> str:
        if self.echo_mode == "full" or len(s) <= self.preview_chars:
            return s
        return s[: self.preview_chars] + " …"

    @staticmethod
    def _who(role: Any) -> str:
        return {"agent": "ASSISTANT", "assistant": "ASSISTANT",
                "user": "USER-SIM"}.get(role, str(role).upper())

    def _ctx_label(self) -> str:
        parts = [
            f"{k}={self._ctx[k]}"
            for k in ("phase", "iter", "task", "trial", "group")
            if self._ctx.get(k) is not None
        ]
        sid = self._ctx.get("session")
        if sid is not None:
            parts.append(f"session={str(sid)[:8]}")
        return " ".join(parts)

    def _echo_turn(self, role, seq, finish, thinking, content, tool_calls,
                   n_tokens, text) -> None:
        """Print one sampled turn: who spoke, its chain-of-thought, every tool
        call with full arguments, and the visible reply. Shell runners tee
        stdout to a log, so this doubles as a durable human-readable trace of
        every speaker in exact conversation order, as it happens."""
        out = [
            f"\n┌─ {self._who(role)} #{seq}  [{self._ctx_label()}]  "
            f"({n_tokens} tok, finish={finish})"
        ]
        if thinking:
            out += [f"│ think  {ln}" for ln in self._clip(thinking.strip()).splitlines()]
        for tc in tool_calls or []:
            args = json.dumps(tc.get("arguments"), ensure_ascii=False, default=str)
            out.append(f"│ tool→  {tc.get('name')} {self._clip(args)}")
        if content:
            out += [f"│ reply  {ln}" for ln in self._clip(content.strip()).splitlines()]
        if not thinking and not tool_calls and not content:
            out += [f"│ raw    {ln}" for ln in self._clip((text or "").strip()).splitlines()]
        out.append("└─")
        print("\n".join(out), flush=True)

    def _track_tool_calls(self, role: str, tool_calls: list[dict]) -> None:
        """Per-session repeat/flood detection. Emits `tool_call_repeat` the
        moment one identical (name, arguments) call hits the threshold, and
        `tool_call_flood` once the session's total crosses its ceiling — so a
        search-spam loop is visible in events.jsonl without opening
        transcripts. Detection only; nothing is stopped."""
        sid = self._ctx.get("session")
        if sid is None or not tool_calls:
            return
        counts = self._tool_counts.setdefault(str(sid), {"__total__": 0})
        for tc in tool_calls:
            counts["__total__"] += 1
            key = json.dumps({"n": tc.get("name"), "a": tc.get("arguments")},
                             sort_keys=True, default=str)
            counts[key] = counts.get(key, 0) + 1
            if counts[key] == self.tool_repeat_warn:
                self.event("tool_call_repeat", role=role, name=tc.get("name"),
                           arguments=tc.get("arguments"), count=counts[key])
                if self.echo_mode != "off":
                    print(f"⚠  identical tool call repeated x{counts[key]}: "
                          f"{tc.get('name')} {tc.get('arguments')}", flush=True)
        if counts["__total__"] >= self.tool_total_warn and str(sid) not in self._flooded:
            self._flooded.add(str(sid))
            self.event("tool_call_flood", role=role,
                       n_tool_calls=counts["__total__"],
                       threshold=self.tool_total_warn)
            if self.echo_mode != "off":
                print(f"⚠  tool-call flood: {counts['__total__']} calls this "
                      f"episode (threshold {self.tool_total_warn})", flush=True)
