# Viewers and analysis

Three tools over the same files. Nothing here requires configuration — they read
the obs format and only the obs format, so they work on any project that writes
it.

## `view_trace.py` — one-shot dump

The one you want in CI, over SSH, in a pipe, and when someone asks "what
actually happened in task_007?".

```bash
python view_trace.py                          # newest run under ./runs
python view_trace.py --list                   # what runs exist
python view_trace.py --run runs/eval-20260802-101500
python view_trace.py --task task_007 --trial 0
python view_trace.py --session 3f2a           # one episode (prefix ok)
python view_trace.py --summary                # one line per session
python view_trace.py --follow                 # tail a run still writing
python view_trace.py --events '*'             # inline every event kind
python view_trace.py --no-thinking > trace.txt
```

Colour is auto-disabled when stdout is not a tty, so redirected output is clean.
`--roots` scans several run trees at once (`--roots sim_runs evals_run`).

**Diffing two arms** is the highest-value use and needs no special tooling:

```bash
python view_trace.py --run runs/arm-a --task task_007 --no-thinking > /tmp/a.txt
python view_trace.py --run runs/arm-b --task task_007 --no-thinking > /tmp/b.txt
diff -u /tmp/a.txt /tmp/b.txt | head -100
```

The first place the two transcripts diverge is usually the entire explanation
for a score gap.

## `view_trace_tui.py` — interactive reading

Reading a 40-turn episode as one scrollback dump does not work: the system
prompt and each tool result are longer than the screen, so the conversation you
want is buried. The TUI inverts that — everything long is collapsed to a
two-line preview *with its true size in the header* (`14 lines · 3182 chars ·
too big to have been read carefully`), and you expand only what you are
currently suspicious of.

```bash
python view_trace_tui.py
python view_trace_tui.py --roots runs evals_run
python view_trace_tui.py --run runs/eval-20260802 --task task_007
```

Three levels, cursor position remembered at each: **run list → session list →
session view**.

The session list is the triage screen. Each row: task, trial, turns, tool calls,
tool errors, end-of-episode context tokens, a `FLOOD` flag, and a colour-coded
reward. Scan it before opening anything — the pattern (all failures at high
turn counts, or all with tool errors, or all on one task family) usually names
the bug before you read a single transcript.

Keys that matter most:

| key | what |
| --- | --- |
| `→` / `←` | expand / collapse the item under the cursor |
| `t` | toggle chain-of-thought on every turn at once |
| `J` | pretty-print tool arguments, decoding nested JSON strings |
| `e` / `c` | expand all / collapse all |
| `n` / `o` / `a` | add a note / read this message's notes / read all notes |
| `E` | export the session to `exports/` as plain text |
| `]` / `[` | line-scroll without moving the cursor |
| `R` | reload from disk (a run still writing) |

**Notes are the feature to actually use.** They go to one append-only
`.obs_notes/notes.jsonl` for the whole system, keyed by run + session + `gseq`,
and they outlive the run: "the model confuses these two policies" is worth more
six months later than the run that produced it. Messages with notes show a `✎`
badge; `a` opens every note ever taken, which becomes a de facto lab notebook.

Set `OBS_NOTES_DIR` / `OBS_EXPORTS_DIR` to move those locations.

## `obs_report.py` — did the arm actually win?

```bash
python obs_report.py                              # every run under ./runs
python obs_report.py --run runs/arm-a runs/arm-b  # head to head
python obs_report.py --by task                    # per-task breakdown
python obs_report.py --json report.json --csv report.csv
```

Columns: sessions, mean reward **± standard error**, solve rate, mean turns /
tool calls / tool errors, mean and p95 end-of-episode context, total cost,
flood and error counts.

The `± sem` is not decoration. With two arms it prints the delta against the
pooled standard error and says whether the gap clears 2·sem. On a 26-task
benchmark, a 0.04 reward difference is almost always noise, and the table says
so instead of letting you write it up.

`--by task` is how you find the tasks that carry a whole arm: a mean that moved
because three tasks flipped is a different finding from one that moved
everywhere.

## Plotting

`metrics.jsonl` is shaped for pandas on purpose:

```python
import pandas as pd
df = pd.read_json("runs/train-20260802/metrics.jsonl", lines=True)
df.plot(x="step", y=["mean_reward", "loss"], subplots=True)
```

Cross-run comparison of any stream, without new tooling:

```python
from pathlib import Path
import pandas as pd
frames = {p.parent.name: pd.read_json(p, lines=True)
          for p in Path("runs").glob("*/metrics.jsonl")}
pd.concat(frames, names=["run"]).reset_index().pivot_table(
    index="step", columns="run", values="mean_reward").plot()
```

## Extending the viewers for your domain

The shipped viewers deliberately know nothing about your benchmark. When domain
knowledge earns its keep, add it as **extra items in the session view** rather
than by changing the trace format. The reference implementation adds, per
session: a task-explanation card at the top, the ground-truth expected actions
beside the calls actually made, the loaded tool schemas with their fixed token
cost, and the grader's per-check justification. Each is a synthetic `Item` built
from a project file — none of them changed `obs.py`.

The pattern to copy, in `build_items()`:

```python
items.insert(1, Item("episode_meta", {
    "title": f"★ TASK  {summary['task']}",
    "content": load_task_markdown(summary["task"]),   # your project's file
}))
```

Three additions that repay the effort on almost any agent benchmark:

1. **Expected vs actual tool calls**, side by side, with per-call verdicts
   (matched / right tool wrong arguments / off-script). Reading the turn's
   reasoning right where a wrong-argument call happened is the fastest path from
   "it failed" to "here is why".
2. **The grader's justification**, from your episode artifacts. For
   LLM-judged rewards this is the reasoning behind the score, and the transcript
   alone never carries it.
3. **A limit flag** on the session list: paint the turn count red when the
   episode hit `max_steps`, and the tool count red at the flood threshold. An
   episode cut off by an artificial ceiling is not a failure of the same kind as
   one that finished and got it wrong, and conflating them corrupts your
   conclusions.
