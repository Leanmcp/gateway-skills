# Adding observability to an existing project

The procedure for walking into a folder that has experiments but no trace, and
leaving it with both — including the runs that already happened.

Contents:
- [Step 0: survey before you touch anything](#step-0-survey-before-you-touch-anything)
- [Step 1: install the core](#step-1-install-the-core)
- [Step 2: find the call sites](#step-2-find-the-call-sites)
- [Step 3: wire the run](#step-3-wire-the-run)
- [Step 4: wire the turns](#step-4-wire-the-turns)
- [Step 5: verify against a known episode](#step-5-verify-against-a-known-episode)
- [Step 6: tie in the existing experiments](#step-6-tie-in-the-existing-experiments)
- [Step 7: make it the default](#step-7-make-it-the-default)
- [Common failure modes](#common-failure-modes)

## Step 0: survey before you touch anything

Ask the repo four questions and write the answers down — they determine every
later choice:

```bash
# 1. Which platform(s)? Look at what is imported, not what the README claims.
grep -rEn "openai|anthropic|google\.genai|genai|litellm|tinker|vllm|transformers|ollama|cohere|mistralai" \
  --include="*.py" . | grep -v test | head -40

# 2. Where do generations happen? These are your instrumentation points.
grep -rEn "\.create\(|\.completion\(|generate_content|\.generate\(|\.sample\(|chat\.completions" \
  --include="*.py" . | head -40

# 3. Where do results go today? These become the imports in step 6.
find . -name "*.json" -path "*result*" -o -name "*.jsonl" -path "*run*" | head -20

# 4. What launches a run? These are the scripts to extend, not replace.
ls *.sh scripts/ 2>/dev/null; grep -rln "argparse" --include="*.py" . | head
```

If the project is a training loop, also find the iteration boundary (where a
step's loss is computed) — that is where `run.metric(...)` goes.

## Step 1: install the core

Copy `scripts/obs.py` and `scripts/obs_adapters.py` next to the experiment code
(a vendored file you can edit beats a dependency for research code — you will
want project-specific events). Copy the viewers too, or point them at the run
root with `--roots`.

Set the env prefix to the project's own if it already has conventions:

```python
run = Run("eval", config=cfg, root="runs", env_prefix="MYPROJ")
# now MYPROJ_ECHO, MYPROJ_TOOL_TOTAL_WARN, ... control it
```

## Step 2: find the call sites

From the step-0 survey, list every place a model is sampled. Include the ones
that are easy to forget, because they are the ones whose absence breaks an
investigation later:

- the agent under test
- the **user simulator / environment model**, if the benchmark has one
- the **LLM judge** that produces the reward
- any **summarizer / router / retrieval LLM** inside a tool
- retry paths that resample (they change the distribution, silently)

Each gets its own `role` string. An episode whose grade came from an unlogged
judge cannot be debugged, only re-run.

## Step 3: wire the run

At the top of the entry point, build **one config dict** and use it twice — print
it to the log and hand it to `Run`. This is the cheapest possible guard against
the log and the run folder disagreeing about what was run:

```python
run_config = {
    "agent_model": args.agent_model,
    **vars(args),
    "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                 capture_output=True, text=True).stdout.strip(),
    "hyperparams": {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
                    "context_window": CONTEXT_WINDOW},
    "retrieval": retrieval_info(),      # whatever your tools are configured with
}
print("Run config:\n" + json.dumps(run_config, indent=2, default=str))

run = Run("eval", config=run_config, root="runs",
          run_name=args.run_name or f"eval-{datetime.now():%Y%m%d-%H%M%S}-{model_slug}",
          wandb_project=os.getenv("WANDB_PROJECT"))
```

Put the model slug in the folder name. Parallel evals of different models
started in the same second otherwise collide into one folder and interleave
their writes — `obs.Run`'s lock is per-process, not cross-process.

## Step 4: wire the turns

```python
with run.session(task=task.id, trial=k):
    run.system_prompt("agent", policy_text)
    ...                                    # your loop, with Observed* clients
    run.tool_result(requestor="agent", name=name, content=result, error=is_err)
    run.episode_done(reward=reward, termination=reason)
    run.artifact(simulation_object, reward=reward)
run.close()
```

For a training loop, add per-iteration scalars:

```python
run.set_context(iter=it)
run.metric(step=it, mean_reward=mean_r, loss=loss, num_data=len(data), lr=lr)
```

**Concurrency:** if episodes run in threads, each worker calls
`run.session(...)` itself. Context is thread-local, so workers cannot clobber
each other's tags. If episodes run in *processes*, give each process its own run
folder via `run_name`.

## Step 5: verify against a known episode

Do not trust the wiring until you have read one episode end to end:

```bash
python view_trace.py --task <a task you know> --run runs/<new run>
```

Check, in order:

1. **Order.** Does it read turn → tool result → next turn? If tool results are
   missing or clumped at the end, you are logging them in the wrong place —
   they must be emitted as they arrive, before the next generation.
2. **The reasoning.** Is `thinking` populated where the model actually reasoned?
   An empty `thinking` on a reasoning model usually means the normalizer is
   reading the wrong field, and you will not notice until you need it.
3. **Tool arguments.** Are they dicts, not escaped JSON strings?
4. **Token counts.** Non-zero? Does the last agent turn's
   `n_prompt_tokens + n_completion_tokens` look like the real context size?
5. **The reward.** Does `episode` carry it, and does it match what the project's
   own results file says for that task? If they disagree, the logging is wrong —
   or the results file is, which is more interesting.

Then `python obs_report.py` and confirm the mean reward matches the number the
project already reports. That agreement is the acceptance test.

## Step 6: tie in the existing experiments

Old runs are the baseline you will compare everything against, so import them:

```bash
python obs_import.py old_results/results.json --out runs --name legacy-gpt4-sweep --dry-run
python obs_import.py old_results/results.json --out runs --name legacy-gpt4-sweep
```

`obs_import.py` recognises the shapes ad-hoc experiment code actually produces
(a list, an object with `results`/`episodes`/`simulations`, a directory of
per-episode JSONs, a JSONL). Anything it does not recognise is preserved
verbatim in the episode artifact, so nothing is lost — worst case the transcript
is thin but the artifacts are whole.

Always `--dry-run` first: it reports how many episodes it found, how many carry
a reward, and how many messages it detected in the first one. Zero messages
means the conversation lives under a key it does not know — pass the right
container or extend `MSG_KEYS` at the top of the file (a two-line edit).

Give imported runs an obvious `--name` (`legacy-`, `imported-`) so the run list
tells you at a glance which rows are reconstructed and which are native.

## Step 7: make it the default

Observability that requires remembering to enable it is observability you do not
have. Fold the env knobs into whatever launches runs:

```bash
export MYPROJ_ECHO="${MYPROJ_ECHO:-full}"          # live per-turn trace
export MYPROJ_TOOL_TOTAL_WARN="${MYPROJ_TOOL_TOTAL_WARN:-15}"
export MYPROJ_TOOL_REPEAT_WARN="${MYPROJ_TOOL_REPEAT_WARN:-3}"
```

and tee stdout to a per-run log file so the live echo is also durable. See
[runner-scripts.md](runner-scripts.md) for the full pattern.

## Common failure modes

| symptom | cause | fix |
| --- | --- | --- |
| Tool calls appear, results never do | results logged after the loop, or not at all | emit `tool_result` as each arrives, before the next generation |
| Two workers' turns land under the wrong task | context set on a shared object | use `run.session(...)` per worker; context is thread-local |
| Concurrent shards interleave into one `events.jsonl` | same folder, different processes | distinct `run_name` per shard |
| `thinking` always empty | normalizer reads the wrong field | check the provider's actual response shape (see platforms.md) |
| `cost` always `0.0` | provider price not registered in LiteLLM | `litellm.register_model({...})` for both id forms |
| Reward in the trace ≠ reward in results.json | `episode_done` called before grading finishes | move it after, or log both and diff |
| Traces balloon to gigabytes | token id arrays on every turn | keep them; gitignore `transcripts.jsonl` and commit `transcripts.share.jsonl` |
| Everything logged, nothing readable | one giant system prompt per turn | `run.system_prompt` dedupes per session — use it instead of `sample` |
