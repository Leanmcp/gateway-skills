# The verification ladder

Before a sweep, climb this. Each rung isolates one layer, so the first failure
names the culprit instead of leaving you with "it doesn't work". Ten minutes
here beats an hour into a sweep that dies unevenly across cells.

## 1. Keys exist

```bash
echo "${FIREWORKS_API_KEY:0:6}…  ${LEANMCP_API_KEY:0:8}…"
```

Keys often live in a repo-root `.env` rather than the shell. All the scripts here
load one if `python-dotenv` is present — but if you are running something else,
a missing key and a broken gateway look identical.

For the gateway, **credits must be topped up before the key works**
(<https://app.leanmcp.com/billing>). A key with no credit behind it fails like a
routing bug.

## 2. The model exists and has the capabilities you need

```bash
python fw_models.py --search <name>
python fw_models.py --serverless --tools --sort context
```

A chat model without function calling will run your agent benchmark, produce
plausible prose, and score zero on every tool task. That reads as a bad model,
not a bad model *choice*.

## 3. The route works — raw first

```bash
python fw_smoke.py --model gpt-oss-20b --direct --transport raw
python fw_smoke.py --model gpt-oss-20b          --transport raw   # gateway
```

Raw HTTP has no SDK in the middle. If raw works, the endpoint, key, credits and
model name are all fine, and **anything that fails from here is your client
library**.

| direct | gateway | conclusion |
| --- | --- | --- |
| ✅ | ✅ | both routes good |
| ✅ | ❌ 404 | the gateway cannot see that model — private deployment |
| ✅ | ❌ 401/403 | LeanMCP key, scopes, or credits |
| ❌ | ❌ | Fireworks side: model name, key, or quota |
| ❌ | ✅ | your own Fireworks key is scoped or capped |

## 4. The client library routes correctly

```bash
python fw_smoke.py --model gpt-oss-20b               # raw + sdk + litellm
python fw_smoke.py --model gpt-oss-20b --transport lite --debug
```

litellm is the one that surprises people, and there are exactly two causes:

- missing `fireworks_ai/` prefix on the model id → wrong provider selected;
- `api_base` that already ends in `/chat/completions` → litellm appends its own.

`--debug` prints the URL litellm actually hits, which settles it immediately.

## 5. Tool calling works, if you need it

```bash
python fw_smoke.py --model gpt-oss-20b --tools
```

Verify per model. The catalogue's `supportsTools` flag is a hint — some models
report `false` and call tools fine.

## 6. The model is warm (dedicated deployments only)

```bash
python fw_ready.py --model <deployment-id> --account <account-id> --wait 600
```

Serverless models are always warm; skip this. A scale-to-zero deployment returns
HTTP 200 with `content: null` while spinning up, which crashes downstream code
with `expected string or bytes-like object, got 'NoneType'`.

## 7. The route survives concurrency

```bash
python fw_hammer.py --mode oneshot --n 20 --concurrency 10
python fw_hammer.py --mode conversation --n 8 --turns 6
```

**This is the rung people skip, and it is the one that costs a sweep.** A single
call proves the route exists; it does not prove it survives twenty concurrent
agent conversations. `Missing scopes: model.request` under load, rate limits, and
under-replicated deployments all pass step 3 cleanly.

Match the concurrency to what your sweep will actually use.

## 8. The framework passes the route through

Dry-run the real command and read the resolved values:

```bash
./run_fireworks.sh --model gpt-oss-120b --use-proxy --dry-run
```

Check the `api_base`, the key (masked), and the model id are what you expect. A
runner that silently ignores `--use-proxy` produces a full sweep of direct calls
and an empty observability dashboard.

Also confirm **client-side caching is off** for anything you are measuring — a
cached response is not observed, not billed, and not a measurement.

## Recording what you verified

Write the resolved config into the run output (route, base URL, masked key,
model id, concurrency, git commit) before the first request. When a result looks
wrong weeks later, this file is the only way to know which route produced it. The
reference runner writes a `run_config.txt` and a per-cell `manifest.csv` for
exactly this — see [runner-scripts.md](runner-scripts.md).
