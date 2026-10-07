#!/usr/bin/env bash
# run_fireworks.sh — one inference run against Fireworks, direct or through the
# Leanmcp AI Gateway. Copy this next to your project and replace the marked
# COMMAND section.
#
# The design: direct and gateway differ ONLY in endpoint + key, so the route is
# one flag rather than a code path — the two stay one keystroke apart and stay
# comparable.
#
#   ./run_fireworks.sh --model gpt-oss-120b
#   ./run_fireworks.sh --model gpt-oss-20b --use-proxy
#   ./run_fireworks.sh --model <deployment-id> --account <acct> --use-proxy
#   ./run_fireworks.sh --model gpt-oss-120b --dry-run
#
# Keys (repo-root .env, auto-loaded; keep .env out of git):
#   FIREWORKS_API_KEY=fw_...        direct route
#   LEANMCP_API_KEY=leanmcp_...     gateway route only
#     -> https://app.leanmcp.com/api-keys (top up first at /billing)

set -euo pipefail

# ------------------------------- defaults ---------------------------------- #
MODEL="gpt-oss-20b"
ACCOUNT=""                 # set -> --model is treated as a deployment id
USE_PROXY=0
DRY_RUN=0
CONCURRENCY="${CONCURRENCY:-10}"
MAX_TOKENS="${MAX_TOKENS:-4096}"
TEMPERATURE="${TEMPERATURE:-0.0}"
RUN_NAME="${RUN_NAME:-run-$(date +%Y%m%d_%H%M%S)}"
WARM_TIMEOUT="${WARM_TIMEOUT:-600}"

DIRECT_BASE="https://api.fireworks.ai/inference/v1"
PROXY_BASE="https://aigateway.leanmcp.com/v1/fireworks"

PASSTHROUGH=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)        MODEL="$2"; shift 2 ;;
    --account)      ACCOUNT="$2"; shift 2 ;;
    --use-proxy)    USE_PROXY=1; shift ;;
    --direct|--no-proxy) USE_PROXY=0; shift ;;
    --concurrency)  CONCURRENCY="$2"; shift 2 ;;
    --max-tokens)   MAX_TOKENS="$2"; shift 2 ;;
    --run-name)     RUN_NAME="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=1; shift ;;
    -h|--help)      sed -n '2,20p' "$0"; exit 0 ;;
    # Anything unrecognised is forwarded to the underlying command, so the full
    # CLI stays available without this wrapper mirroring it.
    *)              PASSTHROUGH+=("$1"); shift ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$REPO_ROOT/.env" ]] && set -a && . "$REPO_ROOT/.env" && set +a

# --------------------------- route + credentials --------------------------- #
if [[ "$USE_PROXY" -eq 1 ]]; then
  API_BASE="$PROXY_BASE"; API_KEY="${LEANMCP_API_KEY:-}"; MODE="Leanmcp gateway"
  [[ -n "$API_KEY" ]] || {
    echo "ERROR: --use-proxy needs LEANMCP_API_KEY." >&2
    echo "  get one at https://app.leanmcp.com/api-keys" >&2
    echo "  (top up credits first at https://app.leanmcp.com/billing)" >&2
    exit 1; }
else
  API_BASE="$DIRECT_BASE"; API_KEY="${FIREWORKS_API_KEY:-}"; MODE="direct Fireworks"
  [[ -n "$API_KEY" ]] || { echo "ERROR: FIREWORKS_API_KEY is not set." >&2; exit 1; }
fi
MASKED="${API_KEY:0:6}…${API_KEY: -4}"

# ------------------------------ model id ----------------------------------- #
# Three shapes, not interchangeable:
#   accounts/fireworks/models/<slug>          serverless
#   accounts/<account>/deployments/<id>       dedicated
#   fireworks_ai/<either>                     what litellm needs (provider prefix)
if [[ "$MODEL" == */* ]]; then
  MODEL_PATH="$MODEL"
elif [[ -n "$ACCOUNT" ]]; then
  MODEL_PATH="accounts/${ACCOUNT}/deployments/${MODEL}"
else
  MODEL_PATH="accounts/fireworks/models/${MODEL}"
fi
LITELLM_MODEL="fireworks_ai/${MODEL_PATH}"
MODEL_LABEL="$(basename "$MODEL_PATH")"

# --------------------------------- banner ---------------------------------- #
cat <<EOF

┌─ Fireworks run: $RUN_NAME
│   route      : $MODE
│   api_base   : $API_BASE
│   api_key    : $MASKED
│   model      : $MODEL_PATH
│   litellm id : $LITELLM_MODEL
│   concurrency: $CONCURRENCY   max_tokens: $MAX_TOKENS   temp: $TEMPERATURE
└─
EOF

# ------------------------- warm dedicated deployments ---------------------- #
# Scale-to-zero deployments return HTTP 200 with content:null while spinning up,
# which crashes downstream code with "expected string or bytes-like object, got
# 'NoneType'". The ping both checks readiness and triggers the scale-up.
if [[ "$MODEL_PATH" == *"/deployments/"* && "$DRY_RUN" -eq 0 ]]; then
  echo "warming $MODEL_LABEL (up to ${WARM_TIMEOUT}s)…"
  if ! python fw_ready.py --api-base "$API_BASE" --model "$MODEL_PATH" \
        --wait "$WARM_TIMEOUT" >/dev/null; then
    echo "ERROR: $MODEL_PATH never became ready." >&2
    exit 1
  fi
  echo "  ready."
fi

# ------------------------------ run record --------------------------------- #
OUT_DIR="eval_runs/${RUN_NAME}"
mkdir -p "$OUT_DIR"
{
  echo "run_name    : $RUN_NAME"
  echo "timestamp   : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "route       : $MODE"
  echo "api_base    : $API_BASE"
  echo "api_key     : $MASKED"
  echo "model       : $MODEL_PATH"
  echo "concurrency : $CONCURRENCY"
  echo "max_tokens  : $MAX_TOKENS"
  echo "temperature : $TEMPERATURE"
  echo "git_commit  : $(git rev-parse HEAD 2>/dev/null || echo n/a)"
  echo "passthrough : ${PASSTHROUGH[*]:-}"
} > "$OUT_DIR/run_config.txt"

# ================================ COMMAND ================================== #
# Replace this with your actual runner. The pattern that matters: api_base and
# api_key are forwarded VERBATIM into the underlying litellm call, so the route
# is configuration rather than a code branch — and they go to EVERY speaker
# (agent, simulated user, judge), or the observability dashboard shows half the
# traffic and the cost total understates the run.
LLM_ARGS=$(printf '{"temperature": %s, "max_tokens": %s, "api_base": "%s", "api_key": "%s"}' \
           "$TEMPERATURE" "$MAX_TOKENS" "$API_BASE" "$API_KEY")

CMD=(
  your-runner
  --agent-llm "$LITELLM_MODEL"
  --agent-llm-args "$LLM_ARGS"
  --user-llm-args "$LLM_ARGS"
  --max-concurrency "$CONCURRENCY"
  --save-to "results/${RUN_NAME}/${MODEL_LABEL}.json"
)
[[ ${#PASSTHROUGH[@]} -gt 0 ]] && CMD+=("${PASSTHROUGH[@]}")
# =========================================================================== #

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] would execute (api_key masked):"
  printf '%q ' "${CMD[@]}" | sed "s|$API_KEY|$MASKED|g"
  echo
  exit 0
fi

# Tee to a per-cell log. NOTE: if you enable litellm debug logging it prints
# full request payloads INCLUDING the api_key — treat such a log as a secret.
LOG="$OUT_DIR/${MODEL_LABEL}.log"
echo "logging to $LOG"
"${CMD[@]}" 2>&1 | tee "$LOG"
STATUS="${PIPESTATUS[0]}"

echo "${MODEL_LABEL},${STATUS},${LOG}" >> "$OUT_DIR/manifest.csv"
exit "$STATUS"
