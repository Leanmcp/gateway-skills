# Runner scripts: one protocol, two routes, many models

The structure that keeps a Fireworks sweep comparable and rerunnable. Template:
`assets/run_fireworks.sh`.

```
runners/
    run_fireworks.sh      one cell: model × domain, --use-proxy toggles the route
    run_sweep.sh          many cells, with manifests
    models.txt            the sweep list
```

## The proxy toggle is the whole design

Direct and gateway differ only in endpoint and key, so routing is one flag, not
a code path — which means the two are always one keystroke apart and stay
comparable:

```bash
if [[ "$USE_PROXY" -eq 1 ]]; then
  API_BASE="https://aigateway.leanmcp.com/v1/fireworks"
  API_KEY="$LEANMCP_API_KEY"
  MODE="Leanmcp gateway"
else
  API_BASE="https://api.fireworks.ai/inference/v1"
  API_KEY="$FIREWORKS_API_KEY"
  MODE="direct Fireworks"
fi
```

Pass it into whatever framework you use as forwarded kwargs. In tau2:

```bash
LLM_ARGS=$(printf '{"temperature": 0.0, "api_base": "%s", "api_key": "%s"}' \
           "$API_BASE" "$API_KEY")
tau2 run --agent-llm-args "$LLM_ARGS" --user-llm-args "$LLM_ARGS" ...
```

Set it for **every** speaker — agent, simulated user, judge. Routing the agent
through the gateway and the user direct gives you a dashboard showing half the
traffic and a cost total that silently understates the run.

## Things the runner must do

**1. Default the route deliberately, and say which one it used.** For sweeps,
default to the gateway (you want the cost record) and take `--direct` to opt out.
Print the resolved mode in the banner.

**2. Mask the key in output — and never in the logs.** Print
`${API_KEY:0:6}…${API_KEY: -4}`. Note that litellm's debug logging prints full
request payloads *including the key*; if you enable it, treat the log as a
secret.

**3. Warm dedicated deployments before starting the cell.**

```bash
if ! python fw_ready.py --api-base "$API_BASE" --model "$MODEL" --wait 600 >/dev/null; then
    echo "SKIP $MODEL — not ready" >&2; continue
fi
```

Without this a sweep launched into a cold deployment dies on its first task with
a `NoneType` error that looks like a code bug.

**4. Support `--dry-run`.** Print the exact command with the key masked. This is
how you check that `--use-proxy` actually reached the framework — a runner that
silently ignores it produces a full sweep of direct calls and an empty dashboard.

**5. Write a manifest and a config snapshot.**

```
eval_runs/<run-name>/run_config.txt      resolved config + git commit
eval_runs/<run-name>/manifest.csv        per cell: model, domain, exit code, paths
eval_runs/<run-name>/<model>__<domain>.log
results/<run-name>/<model>__<domain>/results.json
```

The manifest is what makes a sweep *resumable and auditable*: which cells ran,
which failed, and where each one's output went. Reconstructing that from
directory listings after a partial failure is miserable.

**6. Let unknown flags pass through** to the underlying command, so the full CLI
stays available without the wrapper having to mirror it:

```bash
*) PASSTHROUGH+=("$1"); shift ;;
```

**7. Keep per-domain quirks in the runner, not in your head.** If one domain
needs an extra flag, add it automatically and say so in the README:

```bash
[[ "$domain" == "banking_knowledge" ]] && CMD+=(--retrieval-config bm25)
```

## `models.txt`

```
# One model per line. Blank lines and # comments ignored.
# Bare slugs get the serverless prefix. `label = path` names the results folder.

gpt-oss-20b
gpt-oss-120b
glm-5p2
kimi-k2p6

# Dedicated deployments — full path, label names the results folder
qwen-9b-k9rxxb48 = accounts/<account-id>/deployments/k9rxxb48
```

The label matters: `k9rxxb48__banking/results.json` tells you nothing in six
weeks; `qwen-9b-k9rxxb48__banking` tells you the model *and* the deployment.

Regenerate the serverless section from the catalogue rather than by hand, and
comment the date you last verified it:

```bash
python fw_models.py --serverless --tools --slugs
```

## Naming runs

`<run-name>/<model-label>__<domain>` — the run name gives ordering and intent,
the cell name is self-describing. Put the same information in `run_config.txt`
too; the folder name is a convenience, the config is the record.

## Resuming

A sweep is many independent cells, so resuming is: read the previous
`manifest.csv`, skip cells with exit code 0, rerun the rest **with the saved
config**, not with today's defaults. Re-deriving the scope from flags is how a
resumed run ends up subtly different from the one it is completing.

## Keys

Keep them in a repo-root `.env` the runner auto-loads, and keep `.env` out of
git:

```bash
FIREWORKS_API_KEY=fw_...        # direct route
LEANMCP_API_KEY=leanmcp_...     # gateway route only
```

Fail early with the fix in the message:

```bash
[[ -n "${LEANMCP_API_KEY:-}" ]] || {
    echo "ERROR: --use-proxy needs LEANMCP_API_KEY." >&2
    echo "  get one at https://app.leanmcp.com/api-keys (top up first at /billing)" >&2
    exit 1; }
```

## A README beside the scripts

Record which models are in the sweep and why, which deployments map to which
underlying model, any protocol deviations, and the date each was last verified.
Six weeks later that is the only record of why a given cell exists — and
"`--num-tasks 5`, a smoke comparison, not a full eval" is the note that stops a
smoke run being reported as a result.
