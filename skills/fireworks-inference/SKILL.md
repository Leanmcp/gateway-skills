---
name: fireworks-inference
description: Run inference on Fireworks AI — direct, through the Leanmcp AI Gateway proxy (aigateway.leanmcp.com) for observability, or via LiteLLM / the OpenAI SDK / raw HTTP. Covers the endpoint-and-key matrix for each route, serverless vs dedicated deployments and their cold starts, browsing and filtering the model catalogue, reasoning models that return content:null with the answer in reasoning_content, function calling, concurrency and load testing, and runner scripts where many models share one protocol with a --use-proxy toggle. Use this skill whenever the user mentions Fireworks, FIREWORKS_API_KEY, api.fireworks.ai, fireworks_ai/ model ids, accounts/fireworks/models/..., a Fireworks deployment id, the Leanmcp gateway or LEANMCP_API_KEY, app.leanmcp.com observability, or gpt-oss / kimi / glm / qwen / deepseek served on Fireworks; wants to route LLM calls through a proxy for logging or cost tracking; is debugging empty responses, 404s, scope errors, cold starts, or "the gateway isn't working"; wants to pick a Fireworks model with tool calling; or wants to sweep several models over one benchmark. Reach for it even on vague asks like "why is this model returning nothing" or "set up inference for these models" when Fireworks is in play.
---

# Fireworks inference

Inference on Fireworks is three independent choices, and nearly every confusing
failure is one of them being wrong while you debug another:

```
   TRANSPORT                ROUTE                        MODEL
   ─────────                ─────                        ─────
   raw HTTP                 direct Fireworks             serverless
   openai SDK        ×      api.fireworks.ai        ×    accounts/fireworks/models/<slug>
   litellm                  Leanmcp gateway              dedicated deployment
                            aigateway.leanmcp.com        accounts/<acct>/deployments/<id>
```

This skill's job is to let you isolate them one at a time instead of guessing.

## The route matrix — memorize this

| | base URL | key |
| --- | --- | --- |
| **direct Fireworks** | `https://api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` |
| **Leanmcp gateway** | `https://aigateway.leanmcp.com/v1/fireworks` | `LEANMCP_API_KEY` |

Same models, same request and response shape. **Only the endpoint and the key
change** — which is why routing should be a flag, never a code path. Note the
key swap: through the gateway you send your *Leanmcp* key; the gateway holds the
Fireworks credential.

Gateway keys at <https://app.leanmcp.com/api-keys> (top up credits first at
<https://app.leanmcp.com/billing>); every request then shows up at
<https://app.leanmcp.com/observability>.

## Start here

**Something is broken.** Climb the ladder in
[references/verification.md](references/verification.md) — each rung isolates one
layer, so the first failure names the culprit.

```bash
python scripts/fw_smoke.py --model gpt-oss-20b            # raw + sdk + litellm, gateway
python scripts/fw_smoke.py --model gpt-oss-20b --direct   # same, direct
```

**The model returns nothing.** Almost always
[references/reasoning-models.md](references/reasoning-models.md) (the answer is in
`reasoning_content`, or the budget went to reasoning) or a cold deployment
([references/models.md](references/models.md)).

**Picking a model.** [references/models.md](references/models.md), then
`python scripts/fw_models.py --serverless --tools --sort context`.

**Setting up a route or a framework.** [references/routes.md](references/routes.md)
for the transport quirks, [references/gateway.md](references/gateway.md) for the
proxy specifics.

**Building a sweep.** [references/runner-scripts.md](references/runner-scripts.md)
+ `assets/run_fireworks.sh`, and hammer it first
([references/load-and-concurrency.md](references/load-and-concurrency.md)).

**Working code at full scale.**
[references/reference-implementation.md](references/reference-implementation.md).

## Scripts

| script | what |
| --- | --- |
| `fw_smoke.py` | the same request through raw HTTP, the openai SDK, and litellm, against either route — the first transport that fails names the layer |
| `fw_models.py` | browse/filter the catalogue: serverless, tools, vision, context; emits paste-ready litellm ids or a `models.txt` |
| `fw_ready.py` | readiness ping for cold deployments; also *triggers* the scale-up. Shell-friendly exit codes, `--wait` to block |
| `fw_hammer.py` | load test in three shapes (oneshot / conversation / output), streamed with a heartbeat, p50/p95 latency and failure breakdown |

## Model ids — three shapes, not interchangeable

```
accounts/fireworks/models/gpt-oss-20b            serverless, shared, always warm
accounts/<your-account>/deployments/<id>         dedicated, yours, scales to zero
fireworks_ai/<either of the above>               the litellm form
```

A bare slug is shorthand you expand yourself; nothing accepts it directly.

## litellm: two things that look like the service is down

1. **The model id needs the `fireworks_ai/` prefix** so litellm picks the
   provider. Without it litellm guesses from the string, usually wrongly.
2. **litellm appends `/chat/completions` to `api_base`.** Pass the base without
   that suffix.

```python
litellm.completion(
    model="fireworks_ai/accounts/fireworks/models/gpt-oss-20b",
    messages=[...],
    api_base="https://aigateway.leanmcp.com/v1/fireworks",   # no /chat/completions
    api_key=os.environ["LEANMCP_API_KEY"],                    # Leanmcp, not Fireworks
)
```

`litellm._turn_on_debug()` prints the URL it actually hits — that one line
settles most "the gateway is broken" arguments. (It also prints the API key, so
treat such a log as a secret.)

## Things that are true and easy to miss

**`content: null` is not failure.** Reasoning models put chain-of-thought in
`reasoning_content` and may return no `content` at all — especially when the
budget ran out mid-thought (`finish_reason: "length"`). Always read
`msg.content or msg.reasoning_content`, and budget 4096, not 1024. A tool call
with null content is also correct: the model acted instead of speaking.

**Cold deployments return 200 with an empty body.** A scale-to-zero deployment
does not error while spinning up — downstream code dies on the `None` with
`TypeError: expected string or bytes-like object, got 'NoneType'`, which reads as
a code bug. Warm it first with `fw_ready.py --wait`.

**The gateway forwards with *its* credentials.** Your private deployment is
invisible to it unless the gateway is wired to your Fireworks account — expect a
404, which is configuration, not a bug. Confirm the deployment is alive with a
direct call before blaming the gateway.

**Tool support is per model, and the flag is a hint.** `--serverless --tools`
filters the catalogue, but some models report `supportsTools: false` and call
tools fine. Probe with `fw_smoke.py --tools`.

**Load reveals what a single call cannot.** `Missing scopes: model.request`, rate
limits, and under-replicated deployments all pass a smoke test and fail a sweep —
unevenly across cells, which silently unbalances the comparison. Hammer at your
intended concurrency before launching.

**Turn client-side caching off for anything you measure.** A cached response is
not observed, not billed, and not a measurement.

**Route every speaker the same way.** Agent through the gateway and the simulated
user direct gives you a dashboard showing half the traffic and a cost total that
understates the run.

## Related

- **research-observability** — the gateway tells you what a run cost; a local
  per-turn trace tells you what the model said and why the episode failed. Use
  both; the adapters there take LiteLLM/OpenAI responses directly.
- **tinker-training-inference** — for the Tinker platform (training and its own
  inference endpoints).
