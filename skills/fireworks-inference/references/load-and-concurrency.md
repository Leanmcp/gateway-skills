# Load, concurrency, and throughput

A route that answers one call is not a route that survives a sweep. The failures
that only appear under load are the expensive kind: they surface an hour in, kill
some cells and not others, and leave results that cannot be compared.

## Three load shapes, because they stress different things

```bash
python fw_hammer.py --mode oneshot      --n 20 --concurrency 10
python fw_hammer.py --mode conversation --n 8  --turns 6
python fw_hammer.py --mode output       --n 4  --concurrency 4 --max-tokens 4096
```

| mode | maximises | catches |
| --- | --- | --- |
| `oneshot` | requests/sec | credential and scope errors under concurrency, rate limits |
| `conversation` | growing context per worker | what a real agent run does — context and spend climbing inside each worker |
| `output` | decoded tokens | generation throughput, and a dedicated deployment's real capacity |

`conversation` is the one that resembles a benchmark run. A one-shot hammer with
tiny prompts passes on routes that fall over once each worker is carrying a 20k
context.

## Live progress

Requests stream and a heartbeat prints every few seconds:

```
…    9s | done 0/20 | in-flight 8 | ~1423 chunks streamed
```

so a long run never looks frozen. **A long generation genuinely takes minutes** —
silence is slow generation, not a hang. A bare `^C … KeyboardInterrupt` traceback
only ever means you pressed Ctrl-C.

Streaming is worth using in your own load tests for the same reason: without it
you cannot distinguish "still generating" from "wedged", and you will kill runs
that were fine.

## Reading failures

**`scope_error` / `Missing scopes: model.request`** — a backend credential
failing under concurrency, not your code. Characteristically passes a single call
and fails a 20-way sweep. If it appears through the gateway, reproduce with
`--direct`: gateway-only means the gateway's credential; both means Fireworks.

**HTTP 429 / rate limited** — lower `--concurrency`, or the account needs a
higher limit. Worth finding your actual ceiling *before* a sweep rather than
discovering it as a partial failure across cells.

**Empty responses only at high concurrency** — usually an under-replicated
dedicated deployment. Serverless models rarely do this. Reproduce direct to rule
the gateway out.

**Latency p95 far above p50** — queueing. If your sweep's concurrency is above
what the deployment can serve, you are paying wall-clock for no throughput.
The hammer prints p50/p95/max; pick a concurrency where p95 has not detached.

**Failures in some cells and not others** — the worst outcome, because it
silently unbalances a comparison. If a sweep loses episodes to load errors, it
loses *different* episodes in each arm. Treat a partial failure as a reason to
rerun the arm, not to report it with a footnote.

## Choosing concurrency for a sweep

1. Hammer at your intended concurrency in `conversation` mode.
2. If failures appear, halve it and repeat until clean.
3. Use the clean value, and record it in the run config.

Around 10 is a reasonable starting point for serverless models. Dedicated
deployments depend entirely on replica count — a scale-to-zero deployment with
one replica will not do 16-way concurrency no matter how patient you are.

## Throughput

The hammer reports aggregate words/sec and per-request latency percentiles. Two
comparisons worth making, because they usually decide the model choice more than
quality does:

- **direct vs gateway** at the same concurrency — the proxy hop should be small
  relative to generation time. If it is not, that is worth knowing before you
  route a whole sweep through it.
- **serverless vs your deployment** for the same model — a dedicated deployment
  is only faster if it is provisioned for the load you actually send.

## Cost under load

Concurrency does not change cost per token, but it changes how fast you spend.
A 16-way sweep of long-context agent episodes can burn a budget in minutes.

Two habits:

- **Smoke at `--n 1 --max-tokens 64` first.** It proves the route in seconds for
  cents, before anything expensive runs.
- **Route through the gateway** so the spend is visible per model and per run at
  <https://app.leanmcp.com/observability> rather than reconstructed afterwards.

## Retries

Retrying inside a load test hides the failure you are testing for — run the
hammer without retries, and add them in production code only after you know what
you are retrying *around*. When you do add them: exponential backoff on 429 and
5xx, no retry on 4xx (a 404 will 404 forever), and **log every retry as an
event** — a run whose retries are invisible has an unexplained latency and cost
profile.
