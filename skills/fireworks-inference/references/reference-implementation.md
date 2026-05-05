# Working code to read

This skill generalizes a working setup in the `tau2-bench` repo
(`path/to/tau2-bench`). When you want a pattern at
full scale, with the project-specific parts still attached, read these.

## `leanmcp_scripts/` — the runners

| file | what to learn from it |
| --- | --- |
| `README.md` | the endpoint/key matrix, the `--use-proxy` design, model shortcuts, domain quirks. The clearest statement of "same models, same everything — only the endpoint and the key change" |
| `run_tau2.sh` | one cell. Builds `LLM_ARGS` JSON with `api_base`/`api_key` and forwards it to `--agent-llm-args` / `--user-llm-args`; supports `--dry-run` with the key masked, and passes unknown flags through |
| `run_all.sh` | the 2×2 sweep, same flags applied to every cell |
| `run_evals.sh` | the full leaderboard sweep: **defaults to the gateway** (`--direct` to bypass), reads `models.txt`, warms each model via `check_model_ready.py`, writes `manifest.csv` + `run_config.txt` per run, auto-adds `--retrieval-config bm25` for the knowledge domain |
| `run_eval_resume.sh` | resuming from a saved manifest with the **saved** config rather than today's defaults |
| `check_model_ready.py` | the readiness ping, with the exit-code contract (`READY` / `EMPTY` / `HTTP n` / `ERR`) a shell loop can branch on. Read the comment on why the budget is 128 and not 8 |
| `models.txt` | the sweep list, including the `label = accounts/<acct>/deployments/<id>` form for dedicated deployments and why the label matters in results paths |
| `STREAMING_TOKENS_PLAN.md` | how to get live in-flight token counts out of a litellm call path (`stream=True` + `stream_chunk_builder` so everything downstream stays identical) |

## `leanmcp_scripts/workspace/` — the smoke tests and hammers

The ladder this skill's `fw_smoke.py` collapses into one script:

| file | rung |
| --- | --- |
| `test_gateway_raw.py` | one raw HTTP POST to the gateway — no SDK, so a pass means the gateway + key + Fireworks routing are all good |
| `test_gateway_litellm.py` | the same call through litellm, reproducing exactly how the framework calls models; isolates litellm-specific routing |
| `test_custom_raw.py` / `test_custom_litellm.py` / `test_custom_gateway.py` | the same three rungs against a **private dedicated deployment**, with the "the gateway may not see this" caveat spelled out |
| `test_gateway_hammer.py` | N concurrent one-shot calls — reproduces scope/credential errors under concurrency |
| `test_conversation_hammer.py` | N concurrent multi-turn chats with growing history — the shape a real run has |
| `test_output_hammer.py` | N concurrent long-form generations, streamed, with a 3-second heartbeat. The docstring on "no output is slow generation, not a hang" is worth copying into anything long-running |
| `fireworks_models.py` | the catalogue browser: pagination, capability filters, `--litellm` / `--slugs` output, the curl-UA and certifi workarounds |
| `explore_results.py` | reading a sweep's results afterwards |
| `README.md` | how to read each test's outcome — the decision table this skill's [verification.md](verification.md) is built on |

## `workspace/` — one-off probes

| file | what |
| --- | --- |
| `check_serverless.py` | is a given model callable serverless at all? Two independent checks: `/v1/models` visibility, then an actual completion. Includes the "HTTP 200, `finish_reason: stop`, zero tokens" signature that means *not served here* |
| `test_gateway_qwen.py` | gateway → a specific dedicated deployment, and why the base-model path returns an empty `stop` while the deployment path works |

## Details worth stealing verbatim

**The `--dry-run` with a masked key.** It is how you confirm `--use-proxy`
actually reached the framework. A runner that silently ignores it produces a full
sweep of direct calls and an empty observability dashboard.

**The readiness ping doubles as a warm-up trigger.** It is not just a check — it
is what makes a scale-to-zero deployment start.

**`reasoning_content` fallback everywhere.** Every one of those scripts reads
`content` and falls back to `reasoning_content`, because gpt-oss returns
`content: null` on a perfectly successful call whose budget went to reasoning.

**The manifest.** `manifest.csv` (per cell: model, domain, exit code, paths) plus
`run_config.txt` (resolved config + git commit) is what makes a sweep auditable
and resumable after a partial failure.

**The bilingual README.** `run_evals.sh`'s docs are written in English and
Chinese side by side — worth matching if your collaborators do.
