# The obs data model

This is the contract. Everything else in the skill — the adapters, the viewers,
the report tool — is downstream of it. Get this right for a new platform and all
the tooling works with no further changes; deviate from it and you have built a
one-off logger again.

## Why files, not a dashboard

Hosted observability answers "is it up" well and "why did the model do that in
task_007 three months ago" badly. Plain JSONL on disk is greppable, diffable,
re-gradable, survivable (a run that dies at iteration 7 keeps 0–6, because every
write is flushed), and free of a vendor's retention policy. Mirror to W&B if you
want the dashboards — `Run(..., wandb_project=...)` does that for the scalars —
but keep the files as the source of truth.

## Directory layout

```
<root>/<kind>-<YYYYmmdd-HHMMSS>/
    config.json          written once at start: every knob the run used
    events.jsonl         discrete events, append-only, flushed per write
    metrics.jsonl        scalar time-series, one row per step
    transcripts.jsonl    full per-turn generations
    episodes/
        <phase>__<task>__trial<k>__<id>.json    one complete episode each
        index.jsonl                             one summary line per episode
```

`<root>` is yours to choose. A convention that pays off: separate trees per run
kind (`sim_runs/` for training, `evals_run/` for evaluation) with the viewers
scanning both. Parallel shards each get their own folder — `obs.Run`'s lock is
per-process, so two processes writing one folder interleave into corruption.
Pass an explicit `run_name` when you launch shards in the same second.

## Universal fields

Every record in every stream carries:

| field | meaning |
| --- | --- |
| `ts` | ISO-8601 UTC wall clock |
| `t` | seconds since the run started (for latency plots without date math) |
| `gseq` | global monotonic counter across all streams — **this is the true ordering**, across threads |
| `seq` | per-session counter from 0 — message order *within* one conversation |
| `session`, `task`, `trial`, `iter`, `phase`, `group` | context tags, whichever you set |

Two counters, because they answer different questions. `gseq` interleaves the
streams back into what actually happened; `seq` gives message #3 of task_007 a
stable identity even when forty episodes were batched onto disk together. The
viewers merge on `gseq` and address notes by it.

## `config.json`

The run's entire configuration, written once. The rule that makes this useful:
**one dict, printed to the log AND written here**, so the log and the folder can
never disagree. Include the model id, the sampling params, the dataset/curriculum,
the retrieval or tool setup, the git commit, and any env-var overrides that were
in force. A field you did not record is a comparison you cannot make later.

`obs.Run` adds `_kind`, `_started_at`, `_dir`.

## `events.jsonl`

One line per discrete thing that happened. Every line has `event: <kind>`.
Kinds the shipped tooling understands:

| event | payload | why it exists |
| --- | --- | --- |
| `sample` | `role`, `n_prompt_tokens`, `n_completion_tokens`, `finish`, `n_tool_calls`, `tool_names`, `text_preview`, `thinking_preview`, `cost` | the scannable summary of a generation — grep this stream, replay the other |
| `system_prompt` | `role`, `n_chars`, `content` | logged once per (session, role); constant within an episode, but the first thing you need to explain a behaviour |
| `tool_result` | `requestor`, `name`, `tool_call_id`, `error`, `n_chars`, `content`, `duration_s` | tools run *between* generations, so results never pass through `sample` |
| `tool_call_repeat` | `name`, `arguments`, `count` | the same call N times: a stuck loop, visible without opening transcripts |
| `tool_call_flood` | `n_tool_calls`, `threshold` | the session blew its total-call ceiling |
| `episode` | `reward`, plus whatever else | the outcome; the viewers colour sessions off this |
| `error` | `where`, `error_type`, `error`, `traceback` | a failure that only exists in stderr is invisible to every later analysis |
| `session_start` / `session_end` | — | emitted by the `session()` context manager |
| `artifact_saved` | `file` | pointer to the full episode JSON |
| `run_end` | `elapsed_s` | written by `close()` |

**Custom events are first-class.** `run.event("retrieval", query=q, hits=[...],
latency_s=0.4)` is a normal thing to do — the viewers render unknown kinds as
one-line rows and `obs_report.py` ignores them, so inventing an event costs
nothing and gains you a dimension you can filter on forever. Anything you
currently `print()` in an experiment loop belongs here instead.

## `transcripts.jsonl`

One line per generation — the heavy stream, the replayable one.

| field | notes |
| --- | --- |
| `role` | free-form. `agent`/`user` get friendly labels; use `judge`, `summarizer`, `planner` for auxiliary models — **they belong in the trace too**, and leaving them out is the most common way a trace stops explaining an outcome |
| `text` | raw decoded output, before parsing |
| `content` | visible reply after parsing (`null` when the turn only called tools) |
| `thinking` | reasoning trace, when the provider exposes one |
| `tool_calls` | `[{"name", "arguments", "id"}]` — **arguments as a dict, not a JSON string**, so later analysis can diff fields instead of strings |
| `finish` | `stop` / `length` / `tool_calls` / provider-specific |
| `prompt_tokens`, `completion_tokens` | token id arrays, when the platform exposes them (see below) |
| `n_prompt_tokens`, `n_completion_tokens` | counts, from the arrays or from `usage` |
| `usage`, `cost` | provider accounting |

### On token ids

Token-level platforms (Tinker, vLLM, raw HF) hand you the exact ids on both
sides. Keep them. They are what makes a training run auditable — the tokens the
policy was updated on are the tokens in the file — and they let you recompute
logprobs offline. Hosted APIs cannot give you this; those turns log empty arrays
and the counts come from `usage`. Both are valid; the viewers handle either.

Because the arrays are large, projects commonly gitignore `transcripts.jsonl`
and commit a stripped `transcripts.share.jsonl` (identical records minus the
arrays). Both viewers prefer the full file and fall back to the share file, so a
fresh clone still reads.

### Deriving context length

An agent turn's prompt *is* its whole context so far. So the context the model
ended an episode with is `max(n_prompt_tokens + n_completion_tokens)` over that
session's agent turns — no separate bookkeeping needed. `summarize_session()`
computes it; it is the single best early-warning signal for long-context
degradation.

## `metrics.jsonl`

One row per training/eval step: `{"ts", "t", "step", **scalars}`. Shaped so
`pd.read_json("metrics.jsonl", lines=True)` gives a tidy frame you can plot
without reshaping. Mirrored to W&B when a project is configured.

## `episodes/`

One self-contained JSON per finished episode: the complete result object
(grading breakdown, every message, termination reason) plus your metadata.
Where the streams are per-turn and append-only, this is the whole artifact in
one human-readable file — what you attach to an issue, what a re-grading script
reads, what survives when you change the trace format.

`episodes/index.jsonl` carries one summary line each so a whole run can be
scanned without opening the big files.

## Concurrency rules

1. **Context is thread-local.** Each worker calls `run.set_context(...)` or uses
   `run.session(...)`; it never inherits a sibling's tags and cannot clobber
   them. A shared context dict is why so many logging layers force you to shard
   across processes.
2. **Writes hold a lock and flush.** Safe across threads, *not* across
   processes — give each process its own run folder.
3. **Sequence numbers are per session.** Interleaved episodes still have
   well-defined internal order.

## Minimum viable integration

If you only wire four calls, wire these — everything downstream degrades
gracefully around the rest:

```python
run = Run("eval", config=cfg, root="runs")
with run.session(task=task_id, trial=k):
    run.system_prompt("agent", policy)      # once, per role
    run.sample("agent", text=..., content=..., tool_calls=..., usage=...)
    run.tool_result(requestor="agent", name=..., content=...)
    run.episode_done(reward=r)
run.close()
```
