---
name: research-observability
description: Add file-based observability, tracing, and run analysis to LLM/agent experiments — per-turn transcripts, tool calls and results, reasoning traces, token/cost accounting, per-episode artifacts, plus terminal viewers and a run-comparison report. Platform-agnostic: one small adapter covers OpenAI, Gemini/Vertex, Anthropic, LiteLLM, Tinker, vLLM, or any custom inference stack, and the same tooling then works unchanged. Use this skill whenever the user wants observability, tracing, logging, or run tracking for model experiments; asks why an agent failed a task or wants to replay/debug/diff an episode; wants to compare models, arms, or ablations; wants to instrument a new folder, repo, or platform ("add observability here", "do the same for Tinker/Gemini/OpenAI"); wants to import or tie in existing experiment results so old runs show up alongside new ones; or wants eval runner scripts where many models share one protocol. Reach for this even when they only say "log what the model is doing", "I can't tell what happened in this run", or "set up traces for this experiment".
---

# Research observability

Experiments you cannot replay are experiments you have to rerun. This skill
installs a small, file-based observability layer over any LLM/agent experiment
and the tools to read it: every generation, every tool call and result, every
reasoning trace, every reward — on disk as plain JSONL, greppable, diffable, and
re-gradable months later.

The design bet: **the recording format is fixed and platform-independent, so
adding a platform is writing one ~15-line normalizer, not re-plumbing
observability.** LiteLLM, OpenAI, Gemini, Anthropic, Tinker and a bespoke
inference server all produce identical files, and every viewer, report and diff
downstream works with no further changes.

## Start here

**Adding observability to a project.** Follow
[references/integration.md](references/integration.md) end to end — it is a
seven-step procedure, starting with a survey of the repo (which platform, where
the generations happen, where results go today) and ending with the existing
runs imported so old and new sit in the same viewer. Do the survey before
writing code; the answers determine every later choice.

**A platform not yet wired.** [references/platforms.md](references/platforms.md)
has working recipes for OpenAI, Gemini/Vertex, Anthropic, LiteLLM, Tinker, and
vLLM/self-hosted, plus the 15-line template for anything else and the
framework-level patterns (subclass the model class, or use the callback API).

**Understanding or extending the format.**
[references/data-model.md](references/data-model.md) is the contract: the
directory layout, every field, both sequence counters and why there are two, and
the concurrency rules.

**Reading and comparing runs.** [references/viewers.md](references/viewers.md)
covers the three tools, the diffing recipe, plotting, and how to add
domain-specific panels without changing the trace format.

**Eval scripts across many models.**
[references/runner-scripts.md](references/runner-scripts.md) — one shared runner
holds the protocol, each model gets a ten-line script. Template in
`assets/_common_eval.sh`.

**Seeing it at full scale.**
[references/reference-implementation.md](references/reference-implementation.md)
maps the tau2-bench system this was generalized from, with the details worth
stealing verbatim.

## What gets installed

Copy from `scripts/` into the project (vendor them — research code always wants
project-specific events, and a file you can edit beats a dependency):

| file | role |
| --- | --- |
| `obs.py` | the core. `Run` + the logging surface. No provider imports, no domain knowledge |
| `obs_adapters.py` | per-platform normalizers and `Observed*` client wrappers |
| `view_trace.py` | one-shot dump: pipe it, grep it, diff two arms, `--follow` a live run |
| `view_trace_tui.py` | interactive curses viewer: run list → session list → conversation, with notes |
| `obs_report.py` | cross-run comparison table with ± standard error |
| `obs_import.py` | backfill existing results into the format so old runs show up too |

## The shape of an instrumented run

```python
from obs import Run
from obs_adapters import ObservedLiteLLM, log_tool_results

run = Run("eval", config=run_config, root="runs",
          run_name=f"eval-{stamp}-{model_slug}")
llm = ObservedLiteLLM(run, role="agent")      # or ObservedOpenAI/Gemini/Anthropic

for task in tasks:
    with run.session(task=task.id, trial=k):
        run.system_prompt("agent", policy)
        while not done:
            resp = llm.completion(model=AGENT_MODEL, messages=msgs, tools=tools)
            results = execute_tools(resp)
            log_tool_results(run, results, requestor="agent")
        run.episode_done(reward=reward)
        run.artifact(episode, reward=reward)
run.close()
```

Then:

```bash
python view_trace.py --task task_007      # what happened
python view_trace_tui.py                  # read it properly
python obs_report.py --run runs/arm-a runs/arm-b   # did the arm actually win
```

## Principles that make this worth doing

**Log every speaker, not just the agent.** The user simulator, the LLM judge,
the summarizer, the retrieval model — each under its own `role`. An episode
whose grade came from an unlogged judge cannot be debugged, only re-run. This is
the single most common reason a trace stops explaining an outcome.

**Tool results are part of the conversation.** Tools run *between* generations,
so results never pass through a sample call. Emit them as they arrive, so the
trace reads turn → result → turn. A trace where the agent calls tools into a
void cannot explain what it did next.

**One config dict, printed and written.** Build it once, print it to the log,
hand it to `Run`. Then the log and the run folder can never disagree about what
was run — and a field you did not record is a comparison you cannot make.

**Retries and recoveries are events.** Truncation retries, duplicate-call
resamples, context overflows, cache misses. Each changes the sampled
distribution; unlogged, they make a run irreproducible in a way nobody notices.

**Keep token ids when the platform gives them.** They make a training run
auditable — the tokens the policy was updated on are the tokens in the file —
and let you recompute logprobs offline. Hosted APIs cannot give you this.

**Report variance, not just means.** `obs_report.py` prints ± standard error and
whether a two-arm gap clears 2·sem. On a 26-task benchmark a 0.04 reward
difference is almost always noise, and the table should say so before you write
it up.

**Default it on.** Export the echo and threshold env vars from the runner
scripts. Observability that requires remembering to enable it is observability
you do not have.

## Environment knobs

Prefix defaults to `OBS`; pass `Run(..., env_prefix="MYPROJ")` to adopt a
project's existing convention.

| var | default | effect |
| --- | --- | --- |
| `<P>_ECHO` | `full` | live per-turn stdout trace: `full` / `preview` / `off` |
| `<P>_PREVIEW_CHARS` | `240` | truncation width for previews |
| `<P>_TOOL_REPEAT_WARN` | `3` | emit `tool_call_repeat` at N identical calls |
| `<P>_TOOL_TOTAL_WARN` | `15` | emit `tool_call_flood` past N calls in a session |
| `OBS_NOTES_DIR` | `.obs_notes` | where the TUI's persistent notes live |
| `OBS_EXPORTS_DIR` | `exports` | where `E` writes session exports |

## Related

For Tinker specifically — training, inference, hyperparameters, LoRA,
checkpointing, pricing — use the **tinker-training-inference** skill alongside
this one. That skill runs the loop; this one records it.
