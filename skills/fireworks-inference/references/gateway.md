# The LeanMCP AI Gateway

An OpenAI-compatible proxy that forwards to Fireworks and logs every request.
The point is observability you get without instrumenting your code: token counts
and cost for every call, across models and runs, in one place.

```
your code ──► https://aigateway.leanmcp.com/v1/fireworks ──► Fireworks
                        (LEANMCP_API_KEY)                    (gateway's credential)
                              │
                              └──► app.leanmcp.com/observability
```

| | base URL | key |
| --- | --- | --- |
| direct | `https://api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` |
| gateway | `https://aigateway.leanmcp.com/v1/fireworks` | `LEANMCP_API_KEY` |

- Keys: <https://app.leanmcp.com/api-keys>
- Credits: <https://app.leanmcp.com/billing> — **top up before creating a key**;
  a key with no credit behind it fails in ways that look like a routing bug
- Observability: <https://app.leanmcp.com/observability>

## Using it

Nothing changes but the endpoint and the key:

```python
# raw / openai SDK — bare Fireworks model path
client = OpenAI(base_url="https://aigateway.leanmcp.com/v1/fireworks",
                api_key=os.environ["LEANMCP_API_KEY"])
client.chat.completions.create(model="accounts/fireworks/models/gpt-oss-20b", ...)

# litellm — provider prefix required
litellm.completion(
    model="fireworks_ai/accounts/fireworks/models/gpt-oss-20b",
    api_base="https://aigateway.leanmcp.com/v1/fireworks",
    api_key=os.environ["LEANMCP_API_KEY"], ...)
```

The key swap is the thing people miss: through the gateway you send your
**LeanMCP** key. The gateway holds the Fireworks credential. Sending the
Fireworks key here fails in a way that reads like a broken gateway.

## What the gateway can and cannot reach

It forwards using **its own** Fireworks credentials, so what it can see is a
property of how it is configured, not of your key.

- **Serverless public models** — reachable.
- **Your private dedicated deployments** — reachable **only if the gateway is
  wired to your Fireworks account.** Otherwise: `404` / model-not-found.

That 404 is a configuration fact, not a bug in your code. Before chasing it,
confirm the deployment itself is healthy:

```bash
python fw_smoke.py --model <deployment-id> --account <account-id> --direct   # is it alive?
python fw_smoke.py --model <deployment-id> --account <account-id>            # can the gateway see it?
```

Direct passing and gateway 404-ing is the signature.

## Errors specific to the gateway

**`scope_error` / `Missing scopes: model.request`** — the gateway's backend
credential failing, characteristically **under concurrency** rather than on a
single call. A one-shot test passes and a twenty-way sweep fails. This is the
main reason to hammer the route before trusting it:

```bash
python fw_hammer.py --mode oneshot --n 20 --concurrency 10
```

**Empty responses only at high concurrency** — usually a dedicated deployment
under-replicated for the load, not the gateway. Reproduce with `--direct`; if it
also happens direct, it is capacity.

**Nothing appears in observability** — either the request never reached the
gateway (check `api_base`), or a client-side cache served it. **Turn LiteLLM
caching off** for anything you are measuring: a cached response is not observed,
not billed, and not a measurement.

## Reading a failure

Run the same request both ways. The difference names the layer:

| direct | gateway | conclusion |
| --- | --- | --- |
| ✅ | ✅ | route is good |
| ✅ | ❌ 404 | gateway cannot see that model (private deployment) |
| ✅ | ❌ 401/403 | LeanMCP key, scopes, or credits |
| ❌ | ❌ | Fireworks side: model name, Fireworks key, or quota |
| ❌ | ✅ | your Fireworks key is the problem, not the model |

That last row is worth remembering — a gateway that works while direct fails
tells you your own key is scoped or capped, which is otherwise hard to see.

## When to use which

**Gateway by default for benchmark sweeps.** The cost and token record across
every model and cell, for free, is worth more than the extra hop — and after the
fact "how much did that sweep cost" is a question you will be asked.

**Direct when you are debugging the model itself**, or in a hot inner loop where
you already have your own tracing. Keep it a flag (`--direct`), not a code
branch, so the two are always one keystroke apart and stay comparable.

## Running both in one experiment

If you route the agent through the gateway and something else (a simulated user,
a judge) direct, record that in the run config. Otherwise the observability
dashboard shows half the traffic and the cost total silently understates the run.
Better: route everything the same way, and vary it only deliberately.

For a per-turn local record of what was actually sent and returned — independent
of any dashboard — use the **research-observability** skill alongside this one.
The gateway tells you what a run cost; a local trace tells you what the model
said and why the episode failed.
