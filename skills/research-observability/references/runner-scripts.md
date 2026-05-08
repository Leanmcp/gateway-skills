# Runner scripts: one protocol, many models

Observability of the *run*, not the turn. A comparison is only meaningful if
every arm ran the same protocol, and the reliable way to guarantee that is
structural: **one shared runner holds the protocol, and each model gets a
thin script that sets only what differs.**

```
multi_evals/
    _common_eval.sh              the protocol — sourced, never run directly
    eval_gemini_vertex.sh        AGENT_MODEL + MODEL_SLUG, then `source`
    eval_openai.sh
    eval_kimi_openrouter.sh
    eval_claude_vertex.sh
    README.md                    the table of what exists and why
```

The property this buys: when a reviewer asks "did the Gemini arm use the same
retrieval setup?", the answer is visible in ten lines instead of requiring a
diff of two 200-line scripts. And when you change the protocol, you change it
once, so no arm silently keeps the old value.

## The thin per-model script

Everything is `${VAR:-default}` so any knob can be overridden from the calling
shell without editing the file:

```bash
#!/usr/bin/env bash
# Google Gemini (on Vertex AI) as the agent. Auth:
#   export VERTEXAI_PROJECT="your-gcp-project"
#   export VERTEXAI_LOCATION="us-central1"   # a region that serves the model
#   gcloud auth application-default login     # or GOOGLE_APPLICATION_CREDENTIALS=<sa.json>
set -euo pipefail

AGENT_MODEL="${AGENT_MODEL:-vertex_ai/gemini-3-pro}"
MODEL_SLUG="${MODEL_SLUG:-gemini3-vertex}"

export DOMAIN="${DOMAIN:-my_domain}"
LIMIT="${LIMIT:-26}"
TRIALS="${TRIALS:-1}"
MAX_STEPS="${MAX_STEPS:-30}"

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common_eval.sh"
```

The header comment carrying the exact auth incantation is not optional — it is
the difference between a colleague running your arm in a minute and not running
it at all.

## What the shared runner must do

`assets/_common_eval.sh` is a working template. The parts that matter:

1. **Require what cannot be defaulted**, loudly and early:
   `: "${AGENT_MODEL:?set AGENT_MODEL before sourcing}"`.
2. **Default every protocol knob** from the environment, so a sweep can vary one
   thing without new files.
3. **Check provider auth before spending anything**, with the fix in the error:
   `export OPENROUTER_API_KEY='sk-or-...'` beats "401".
4. **Export the observability knobs** (`*_ECHO`, `*_TOOL_TOTAL_WARN`,
   `*_TOOL_REPEAT_WARN`) so tracing is on by default. Observability you have to
   remember to enable is observability you do not have.
5. **Tee stdout and stderr to a per-run log**: `exec > >(tee -a "$LOG_FILE") 2>&1`.
   With `ECHO=full`, that log is a complete human-readable trace of both
   speakers — a second, format-independent copy of the run.
6. **Run Python unbuffered** (`python -u`) or the log fills in lurching chunks
   and `tail -f` is useless.
7. **Print the resolved configuration** before starting. The one thing you will
   want when a result looks wrong is what the run actually resolved to.

## Beware `${VAR:-}` when empty is meaningful

If an empty value *selects* something (empty `API_USER` = use the local
simulator rather than a hosted one), `${API_USER:-default}` cannot express it —
bash treats set-but-empty as unset, so `export API_USER=""` silently gets the
default back. Use `${API_USER-default}` (no colon): unset takes the default,
set-but-empty stays empty. This is a real bug that costs a sweep.

## Parallel shards

Sharding one eval across processes is the standard way to make a long run
finish, and the one thing it must get right is the run folder:

```bash
for s in $(seq 0 $((JOBS-1))); do
    RUN_NAME="eval-$(date +%Y%m%d-%H%M%S)-${MODEL_SLUG}-s${s}" \
    SHARD="$s" SHARDS="$JOBS" bash "$SCRIPT" &
done
wait
```

`obs.Run`'s lock is per-process, so two shards sharing a folder interleave into
a corrupt `events.jsonl`. Distinct `--run-name` per shard, then aggregate:

```bash
python obs_report.py --run runs/eval-*-s*     # all shards, one table
```

Name shards with a `-sN` suffix so viewers can filter them out of the run list
by default — otherwise a few sweeps bury every other run under dozens of
near-identical rows.

## A README beside the scripts

Keep a table of every script: which model, which context window, which protocol
deviation and *why*. Six weeks later this is the only record of why
`eval_x_oracle.sh` exists, and "isolates reasoning from retrieval error by
handing the agent the ground-truth documents" is the sentence you will not
reconstruct from the code.

Note deviations explicitly, e.g. "runs only the first 5 tasks — a smoke
comparison, not a full eval". A smoke run mistaken for a full one is a wrong
number in a paper.

## Naming runs

`<kind>-<timestamp>-<model-slug>[-<variant>][-s<shard>]`

The timestamp gives ordering, the slug survives parallel launches in the same
second, and the variant is what makes a run list self-describing. Put the same
information in `config.json` too — the folder name is a convenience, the config
is the record.
