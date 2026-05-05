# Models: serverless, dedicated, and picking one that works

## Two kinds of model, with different failure modes

| | serverless | dedicated deployment |
| --- | --- | --- |
| path | `accounts/fireworks/models/<slug>` | `accounts/<your-account>/deployments/<id>` |
| who runs it | Fireworks, shared | you, on your account |
| billing | per token | per replica-hour (usually) |
| cold start | none — always warm | **scales to zero**; first call after idle returns empty |
| visible to a gateway | yes | only if the gateway is wired to your account |
| model choice | the public catalogue | anything you can deploy, including your own fine-tunes |

Most confusion comes from treating these as the same thing. A slug that works
serverless will not work as a deployment id, and a private deployment that works
directly may 404 through a gateway.

## Browsing the catalogue

The catalogue is large, paginated, and full of models that are wrong for an
agent workload — image generators, embedders, rerankers, and chat models without
function calling.

```bash
python fw_models.py                                   # everything
python fw_models.py --serverless --tools --sort context
python fw_models.py --search kimi
python fw_models.py --serverless --tools --litellm    # paste-ready litellm ids
python fw_models.py --serverless --slugs > models.txt
python fw_models.py --refresh                         # ignore the cache
```

Filter flags map to catalogue fields: `supportsServerless`, `supportsTools`,
`supportsImageInput`, `tunable`, `contextLength`, `deprecationDate`, `kind`.

**For an agent benchmark you almost always want `--serverless --tools`.** A model
without function calling will run, produce plausible prose, and score zero on
every task that needs a tool — a failure that looks like the model being bad.

Two environment quirks the script handles, both of which read as "the API is
down": Fireworks' WAF 403s the default `Python-urllib` User-Agent (it sends a
curl-like UA), and some Python installs fail TLS against the default CA store (it
uses certifi's bundle).

### `supportsTools: false` is a hint, not a verdict

Some models report `tools=false` and still behave correctly in a tool-calling
loop; the flag reflects what Fireworks certifies, not what the model can do.
`gpt-oss-20b` is the standing example. Probe it rather than trusting the flag:

```bash
python fw_smoke.py --model gpt-oss-20b --tools
```

## A `models.txt` for sweeps

Keep the sweep list in a file, not in a script, so adding a model is one line and
the list is diffable:

```
# One model per line. Blank lines and # comments ignored.
# Bare slugs get the serverless prefix. `label = path` names the results folder.

gpt-oss-20b
gpt-oss-120b
deepseek-v4-pro
glm-5p2
kimi-k2p6
qwen3p7-plus

# Our own DEDICATED deployments — full path, so the label matters
qwen-9b-k9rxxb48   = accounts/<account-id>/deployments/k9rxxb48
qwen3.6-27b-b2f04w5c = accounts/<account-id>/deployments/b2f04w5c
```

The `label =` form is worth the effort: a deployment id in a results folder name
(`k9rxxb48__banking/results.json`) tells you nothing six weeks later, while
`qwen-9b-k9rxxb48__banking` tells you both which model and which deployment.

Regenerate the serverless section from the catalogue rather than by hand:

```bash
python fw_models.py --serverless --tools --slugs
```

and record the date you last verified it in a comment. Models get deprecated,
and a sweep that silently drops a model is worse than one that fails loudly.

## Cold starts on dedicated deployments

A scale-to-zero deployment does not error when cold. It returns **HTTP 200 with
`content: null`** while a replica spins up. Downstream code then dies on the
`None` with something that looks unrelated:

```
TypeError: expected string or bytes-like object, got 'NoneType'
```

so a sweep launched into a cold deployment fails on its first task and reads as a
code bug.

Ping before you launch — the ping both checks readiness and *triggers* the
scale-up:

```bash
python fw_ready.py --model <deployment-id> --account <account-id> --wait 600
```

Exit codes are designed for a shell loop: `0 READY`, `1 EMPTY` (still warming),
`2 HTTP <code>`, `3 ERR`. Wire it into the runner so each cell warms its model
before starting (see [runner-scripts.md](runner-scripts.md)).

**Use at least ~128 max_tokens for the ping.** Reasoning models spend their
budget on the reasoning channel before any final-answer token appears, so an
8-token ping returns `content: ""` forever and reads as "never warms up" — see
[reasoning-models.md](reasoning-models.md).

## Is this model available serverless at all?

Worth checking before you build around a deployment. Two independent probes:

```bash
# 1. does the key see it?
curl -s -H "Authorization: Bearer $FIREWORKS_API_KEY" \
     https://api.fireworks.ai/inference/v1/models | grep <slug>

# 2. does a serverless completion actually work?
python fw_smoke.py --model <slug> --direct --transport lite
```

If (2) returns text, you can drop the deployment and point at the serverless
path — cheaper, no cold starts, no gateway visibility problem. If it 404s or
returns empty, the model is dedicated-only.

A note on that second case: a base-model path can return HTTP 200 with
`finish_reason: stop` and **zero tokens**. That is Fireworks saying "not served
here", not the model choosing to say nothing. Check the token counts, not just
the status code.

## Context windows

`contextLength` is in the catalogue (`--min-context N` filters on it). It is the
constraint that decides whether long agent episodes finish or die mid-run, so
record it in the run config next to the model id — and prefer discovering it from
the catalogue over trusting a number from a blog post.
