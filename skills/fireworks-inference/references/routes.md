# Routes: direct, gateway, and the client in between

Every Fireworks call is three independent choices. Almost every confusing
failure is one of them being wrong while you debug another.

```
   YOUR CODE            TRANSPORT              ROUTE                 MODEL
   ─────────            ─────────              ─────                 ─────
   your loop     ->  raw HTTP  /  openai  ->  direct Fireworks  ->  serverless
   a framework       SDK       /  litellm     LeanMCP gateway       dedicated deployment
```

## The route matrix

| | base URL | key |
| --- | --- | --- |
| **direct Fireworks** | `https://api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` |
| **LeanMCP gateway** | `https://aigateway.leanmcp.com/v1/fireworks` | `LEANMCP_API_KEY` |

Same models, same request shape, same response shape. **Only the endpoint and
the key change** — which is what makes a proxy toggle a one-line flag rather
than a code path.

The gateway forwards to Fireworks and logs every request at
<https://app.leanmcp.com/observability>. Keys: <https://app.leanmcp.com/api-keys>
(top up credits first at <https://app.leanmcp.com/billing>).

Note the key swap. Through the gateway you send your **LeanMCP** key, not your
Fireworks key — the gateway holds the Fireworks credential. Sending the
Fireworks key to the gateway fails in a way that reads like a bad gateway.

## Model id forms — three shapes, not interchangeable

| shape | example | what it is |
| --- | --- | --- |
| serverless | `accounts/fireworks/models/gpt-oss-20b` | shared, pay-per-token, always warm |
| dedicated deployment | `accounts/<your-account>/deployments/<id>` | yours, may scale to zero |
| litellm form | `fireworks_ai/` + either of the above | the provider prefix litellm needs |

A bare slug (`gpt-oss-20b`) is shorthand you expand yourself; nothing accepts it
directly.

## Transport differences that actually bite

### Raw HTTP / openai SDK

Use the **bare** Fireworks path as `model`. Both Fireworks and the gateway are
OpenAI-compatible, so the openai SDK works with only a `base_url` change:

```python
client = OpenAI(base_url=GATEWAY_BASE, api_key=os.environ["LEANMCP_API_KEY"])
resp = client.chat.completions.create(
    model="accounts/fireworks/models/gpt-oss-20b",
    messages=[...], max_tokens=1024)
```

### litellm

Two things differ, and both produce failures that look like the service is down:

1. **The model id needs the `fireworks_ai/` prefix** so litellm selects the
   provider. Without it litellm guesses from the string, usually wrongly.
2. **litellm appends `/chat/completions` to whatever `api_base` you give it.**
   Pass the base *without* that suffix.

```python
litellm.completion(
    model="fireworks_ai/accounts/fireworks/models/gpt-oss-20b",
    messages=[...],
    api_base="https://aigateway.leanmcp.com/v1/fireworks",   # no /chat/completions
    api_key=os.environ["LEANMCP_API_KEY"],                    # LeanMCP, not Fireworks
)
```

`litellm._turn_on_debug()` prints the URL it actually hits — that one line
settles most "the gateway is broken" arguments.

## Frameworks: pass the route through, don't fork the code

Most agent frameworks call litellm underneath and accept extra kwargs that are
forwarded verbatim. So routing is configuration, not a code branch. In tau2:

```bash
LLM_ARGS='{"temperature": 0.0, "api_base": "'"$API_BASE"'", "api_key": "'"$API_KEY"'"}'
tau2 run --agent-llm-args "$LLM_ARGS" --user-llm-args "$LLM_ARGS" ...
```

Set `API_BASE`/`API_KEY` from a `--use-proxy` flag and one script covers both
routes. Full pattern in [runner-scripts.md](runner-scripts.md).

**Turn LiteLLM caching off** for anything you are measuring. A cached response
never reaches the gateway, so it is not observed, not billed, and not a real
measurement of the route.

## Choosing a route

**Direct** when you want the fewest moving parts: debugging a model's behaviour,
or a hot loop where you do not need the request logged.

**Gateway** when you want observability — every request, its tokens, and its cost
visible in one place across models and runs, without instrumenting your code. For
benchmark sweeps this is usually the right default, which is why the reference
runner defaults to it and takes `--direct` to opt out.

Note what the gateway can and cannot see: it forwards using **its own**
Fireworks credentials. A **private deployment on your account is invisible to it**
unless the gateway is explicitly wired to that account — expect a 404 /
model-not-found, which is a configuration fact, not a bug. Confirm the deployment
itself is healthy with a direct call before blaming the gateway.

## Verifying a route

Run the layers separately, in order, and stop at the first failure:

```bash
python fw_smoke.py --model gpt-oss-20b              # all transports, gateway
python fw_smoke.py --model gpt-oss-20b --direct     # same, direct
```

Reading it:

- **raw fails** → endpoint, key, credits, or model name. Not your library.
- **raw works, litellm fails** → litellm routing (prefix / `api_base`). `--debug`.
- **direct works, gateway fails** → the gateway cannot reach that model.
- **all pass** → use it.

Then confirm it survives load before a sweep — see
[load-and-concurrency.md](load-and-concurrency.md).
