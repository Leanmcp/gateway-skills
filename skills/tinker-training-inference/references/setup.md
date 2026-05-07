# Setup and the client model

## Install and authenticate

```bash
uv pip install tinker           # or: uv sync, if tinker is a declared dependency
export TINKER_API_KEY="..."     # get one at https://console.tinker.ai
```

Fail fast on the key rather than three minutes into a loop:

```python
import os, sys
if not os.getenv("TINKER_API_KEY"):
    sys.exit("TINKER_API_KEY is not set.\n"
             "  export TINKER_API_KEY='your-api-key-here'   (console.tinker.ai)")
```

## The three clients

```python
import tinker
from tinker import types

service_client = tinker.ServiceClient()                      # reads TINKER_API_KEY

training_client = service_client.create_lora_training_client(
    base_model="Qwen/Qwen3-8B", rank=32)

sampling_client = service_client.create_sampling_client(
    base_model="Qwen/Qwen3-8B",
    model_path="tinker://<run>/sampler_weights/<name>")      # omit for the raw base

tokenizer = training_client.get_tokenizer()                  # also on sampling_client
```

| client | what it owns |
| --- | --- |
| `ServiceClient` | auth, capabilities, creating the other two, the REST client |
| `TrainingClient` | `forward_backward`, `optim_step`, `save_state`, `save_weights_for_sampler`, `save_weights_and_get_sampling_client` |
| `SamplingClient` | `sample`, `compute_logprobs` |

Everything returns a **future**; `.result()` blocks. Async variants
(`forward_backward_async`, `sample_async`, ...) exist for every call and are
what you want when rolling out many episodes concurrently.

`save_weights_and_get_sampling_client(name=...)` is the one to reach for in an
RL loop: it persists the current weights *and* hands back a client that samples
from exactly those weights, which is the invariant importance sampling depends
on.

## Choosing a base model

Two things to check, both of which have burned real runs:

**1. Is it actually served?** Models retire — the Llama-3.x family is already
gone. Ask, don't assume:

```python
caps = service_client.get_server_capabilities()
served = {m.model_name: m.max_context_length for m in caps.supported_models}
```

**2. Does the model clear the floor on your task?** A model that scores ~0 on
your benchmark cannot separate any two experimental arms, because a floor at
zero has no resolution. This is worth stating because it is not hypothetical: in
the reference project a small model was the default for months at a 0.9% solve
rate, and every A/B run against it was uninterpretable until the default moved
to a model at 33%. Calibrate the model to the task *before* running ablations.

The live catalogue — sizes, context windows, prices — is at
<https://tinker-docs.thinkingmachines.ai/tinker/models/>. `scripts/tinker_pricing.py list`
carries a snapshot; see [pricing.md](pricing.md).

## Context windows are part of the model id

This is the one that silently corrupts experiments. The base id and its
long-context variant are **different models** at different prices:

```
openai/gpt-oss-120b                  max_context_length = 32768
openai/gpt-oss-120b:peft:131072      max_context_length = 131072
```

If you configure a window above what is served, the guard in your code never
fires and the service rejects oversized requests instead:

```
BadRequestError: 40727 prompt tokens + 4096 max_tokens > 32768
```

Those episodes die mid-run. In the reference project 16 episodes died this way
in one day — including one task in one arm of an A/B and not the other, which
silently unbalanced the comparison. A crash you can see is fine; a crash that
removes different episodes from different arms is a wrong result.

Assert it at startup:

```python
def assert_context_window(service_client, model: str, want: int) -> int:
    """Exit if configured ABOVE what the service serves; warn if below."""
    caps = service_client.get_server_capabilities()
    limits = {m.model_name: m.max_context_length for m in caps.supported_models}
    real = limits.get(model)
    if real is None:
        print(f"[context] service lists no window for {model}; using {want}")
        return want
    if want > real:
        longer = [n for n in limits if n.startswith(model + ":") and limits[n] > real]
        sys.exit(f"context window {want} exceeds what is served for {model}: {real}.\n"
                 f"  requests will be REJECTED instead of ending the episode cleanly\n"
                 + (f"  long-context variants: {', '.join(longer)}\n" if longer else ""))
    if want < real:
        print(f"[context] {want} is below the served limit {real} — episodes end "
              f"earlier than they need to.")
    return real
```

Configured *below* the real limit is safe; it costs episode length, not
correctness.

## Environment variables

| var | effect |
| --- | --- |
| `TINKER_API_KEY` | required |
| `TINKER_SUBPROCESS_SAMPLING=1` | run sampling in a subprocess to avoid GIL contention — worth setting when many rollout threads sample concurrently |

## Recording the run

Tinker itself captures almost nothing locally — just a hosted run UUID. Anything
you want to inspect later (per-turn transcripts, rewards, retries, cost) has to
be written by you.

Use the companion **research-observability** skill for this. It is the sibling
of this skill and was built against exactly this stack: `run.sample()` takes the
prompt and completion token ids Tinker gives you, so a training run stays
auditable — the tokens the policy was updated on are the tokens in the file.
