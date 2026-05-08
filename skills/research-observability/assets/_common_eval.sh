#!/usr/bin/env bash
# _common_eval.sh — shared runner template. Do NOT run this directly.
#
# Each eval_<model>.sh sets AGENT_MODEL / MODEL_SLUG (and any protocol
# override) and then sources this file. Everything the arms have in common
# lives here exactly once, so a protocol change cannot land in some arms and
# not others.
#
# Copy this next to your per-model scripts, replace the marked sections, and
# delete what does not apply.

set -euo pipefail

# ---------------------------- required inputs ------------------------------ #
: "${AGENT_MODEL:?set AGENT_MODEL (e.g. vertex_ai/gemini-3-pro) before sourcing}"
: "${MODEL_SLUG:?set MODEL_SLUG (used in the run folder name) before sourcing}"

# ------------------------- shared eval protocol ---------------------------- #
# Every knob defaults from the environment, so a sweep varies one thing without
# needing a new file. Change a default here and EVERY arm changes together.
DOMAIN="${DOMAIN:-my_domain}"
DATASET="${DATASET:-data/tasks.jsonl}"
LIMIT="${LIMIT:-26}"
OFFSET="${OFFSET:-0}"
TRIALS="${TRIALS:-1}"
MAX_STEPS="${MAX_STEPS:-30}"

# The simulated user / environment model, held FIXED across arms so every agent
# faces the same counterpart. NOTE the `-` not `:-`: an explicitly empty value
# selects the local simulator, which `:-` could not express (bash treats
# set-but-empty as unset).
API_USER="${API_USER-gpt-5.4-nano}"

# ------------------------- observability (obs.py) -------------------------- #
# On by default. Observability you have to remember to enable is observability
# you do not have.
export OBS_ECHO="${OBS_ECHO:-full}"                    # full | preview | off
export OBS_TOOL_TOTAL_WARN="${OBS_TOOL_TOTAL_WARN:-15}"
export OBS_TOOL_REPEAT_WARN="${OBS_TOOL_REPEAT_WARN:-3}"
RUNS_ROOT="${RUNS_ROOT:-runs}"
# --------------------------------------------------------------------------- #

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-$([ -x "$REPO_ROOT/.venv/bin/python" ] \
    && echo "$REPO_ROOT/.venv/bin/python" || echo python)}"

# Mirror stdout AND stderr to a per-run log. With OBS_ECHO=full this log is a
# complete human-readable trace of every speaker — a second, format-independent
# copy of the run.
LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/eval_${MODEL_SLUG}_${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Logging to: $LOG_FILE"

# ------------------------- provider auth checks ---------------------------- #
# Fail before spending anything, and put the fix in the error message.
case "$AGENT_MODEL" in
    vertex_ai/*)
        if [[ -z "${VERTEXAI_PROJECT:-}" ]]; then
            echo "ERROR: $AGENT_MODEL needs Vertex AI credentials." >&2
            echo "  export VERTEXAI_PROJECT='your-gcp-project'" >&2
            echo "  export VERTEXAI_LOCATION='us-central1'   # a region that serves it" >&2
            echo "  gcloud auth application-default login    # or GOOGLE_APPLICATION_CREDENTIALS=<sa.json>" >&2
            exit 1
        fi ;;
    openrouter/*)
        [[ -n "${OPENROUTER_API_KEY:-}" ]] || {
            echo "ERROR: $AGENT_MODEL needs OPENROUTER_API_KEY." >&2
            echo "  export OPENROUTER_API_KEY='sk-or-...'" >&2; exit 1; } ;;
    gemini/*)
        [[ -n "${GEMINI_API_KEY:-}" ]] || {
            echo "ERROR: $AGENT_MODEL needs GEMINI_API_KEY." >&2; exit 1; } ;;
    anthropic/*|claude-*)
        [[ -n "${ANTHROPIC_API_KEY:-}" ]] || {
            echo "ERROR: $AGENT_MODEL needs ANTHROPIC_API_KEY." >&2; exit 1; } ;;
    *)
        [[ -n "${OPENAI_API_KEY:-}" ]] || {
            echo "ERROR: $AGENT_MODEL looks OpenAI-routed; set OPENAI_API_KEY." >&2
            exit 1; } ;;
esac
if [[ -n "$API_USER" && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: API_USER=$API_USER needs OPENAI_API_KEY (the user simulator)." >&2
    exit 1
fi

# --------------------------- resolved config ------------------------------- #
# Print what the run ACTUALLY resolved to. This is the first thing you want
# when a result looks wrong.
cat <<EOF

Eval: agent=$AGENT_MODEL  user=${API_USER:-local-sim}
      domain=$DOMAIN dataset=$DATASET
      $LIMIT task(s) (offset $OFFSET) x $TRIALS trial(s), max_steps=$MAX_STEPS
      runs_root=$RUNS_ROOT  echo=$OBS_ECHO

EOF

# -u: unbuffered, so the log streams live instead of in lurching chunks.
"$PYTHON" -u run_eval.py \
    --agent-model "$AGENT_MODEL" \
    --domain "$DOMAIN" \
    --dataset "$DATASET" \
    --limit "$LIMIT" \
    --offset "$OFFSET" \
    --trials "$TRIALS" \
    --max-steps "$MAX_STEPS" \
    --runs-root "$RUNS_ROOT" \
    --run-name "eval-${STAMP}-${MODEL_SLUG}${RUN_SUFFIX:-}" \
    ${API_USER:+--api-user "$API_USER"} \
    ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
