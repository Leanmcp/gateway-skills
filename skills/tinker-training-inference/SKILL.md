---
name: tinker-training-inference
description: Train and run models on Tinker (Thinking Machines) — LoRA and full fine-tuning, SFT with correct loss masking, RL/RFT with group-relative advantages and importance sampling, agentic RL over multi-turn tool-using agents, inference via the SamplingClient or the OpenAI-compatible endpoint, checkpoint management and export, every hyperparameter, and cost estimation from the live price table. Use this skill whenever the user mentions Tinker, tinker://, TINKER_API_KEY, console.tinker.ai, or the tinker CLI; wants to fine-tune, SFT, RFT, or RL a model on Tinker; asks about Tinker models, context windows, LoRA rank, sampling params, loss functions (cross_entropy, importance_sampling, ppo, cispo, dro), Datum construction, forward_backward or optim_step; wants to sample from, download, resume, merge, or export a Tinker checkpoint; or asks what a Tinker run will cost. Whenever Tinker work is initialized in a project, this skill also creates a TINKER_PRICING.md there so prices sit next to the training code. Reach for it even on vague asks like "train a model on this data" or "get inference working" when Tinker is the platform in play.
---

# Tinker: training and inference

Tinker gives you token-level control of hosted fine-tuning: you build the
`Datum`s, you own the chat template, you hold the exact prompt and completion
token ids on both sides. That is the reason to use it — a training run stays
auditable, because the tokens the policy was updated on are tokens you can point
at — and it is also why there is more to get right than with a hosted
fine-tuning button. This skill is the map.

## Do this first, in any new Tinker project

**Create the pricing file.** Prices next to the training script get read before a
550B RL run is launched; prices in a browser tab do not.

```bash
python <skill>/scripts/tinker_pricing.py init --out <project dir>
```

That writes `TINKER_PRICING.md` — the full catalogue, what each operation
meters, and the pre-launch checklist. It is a **snapshot**: verify against the
live catalogue at <https://tinker-docs.thinkingmachines.ai/tinker/models/>, and
regenerate with `--force` when it moves. Then:

```bash
export TINKER_API_KEY="..."          # console.tinker.ai
uv pip install tinker
```

## Where to go

| you want to | read |
| --- | --- |
| get set up, pick a model, avoid the context-window trap | [references/setup.md](references/setup.md) |
| supervised fine-tuning | [references/training-sft.md](references/training-sft.md) |
| RL / RFT on single-turn tasks | [references/training-rl.md](references/training-rl.md) |
| RL over a multi-turn tool-using agent | [references/agentic-rl.md](references/agentic-rl.md) |
| sample from a checkpoint (SDK or OpenAI-compatible HTTP) | [references/inference.md](references/inference.md) |
| save, resume, download, merge, export checkpoints | [references/checkpoints.md](references/checkpoints.md) |
| every knob and what it costs to get wrong | [references/hyperparameters.md](references/hyperparameters.md) |
| render prompts, tool schemas, parse completions | [references/chat-templates.md](references/chat-templates.md) |
| the price table and run-cost estimation | [references/pricing.md](references/pricing.md) |
| an error, or a run that is silently wrong | [references/troubleshooting.md](references/troubleshooting.md) |
| working code at full scale | [references/reference-implementation.md](references/reference-implementation.md) |

## Runnable templates

Copy into the project and replace the marked function:

| script | replace |
| --- | --- |
| `scripts/tinker_sft.py` | `load_dataset()` — everything else (Datum construction, loss masking, before/after eval, checkpointing) is the part that is easy to get subtly wrong |
| `scripts/tinker_rl.py` | `TASKS`, `render_prompt()`, `reward()` |
| `scripts/tinker_infer.py` | nothing — CLI, both the SDK and HTTP routes |
| `scripts/tinker_pricing.py` | nothing — catalogue, `init`, and the cost estimator |

## The API in one screen

```python
import tinker
from tinker import types

service_client  = tinker.ServiceClient()                      # reads TINKER_API_KEY
training_client = service_client.create_lora_training_client(
    base_model="Qwen/Qwen3-8B", rank=32)
tokenizer = training_client.get_tokenizer()

# SFT ---------------------------------------------------------------------
result = training_client.forward_backward(batch, loss_fn="cross_entropy").result()
training_client.optim_step(types.AdamParams(learning_rate=1e-4)).result()

# RL ----------------------------------------------------------------------
sampler = training_client.save_weights_and_get_sampling_client(name=f"iter-{it}")
resp = sampler.sample(prompt=types.ModelInput.from_ints(prompt_tokens),
                      num_samples=8,
                      sampling_params=types.SamplingParams(
                          max_tokens=4096, temperature=1.0,
                          stop=STOP_STRINGS, seed=seed)).result()
training_client.forward_backward(rl_data, loss_fn="importance_sampling").result()
training_client.optim_step(types.AdamParams(learning_rate=1e-4)).result()

# checkpoints -------------------------------------------------------------
training_client.save_state(name="iter-40")               # -> weights/…  resumable
training_client.save_weights_for_sampler(name="final")   # -> sampler_weights/…  servable
```

Every call returns a future; `.result()` blocks, and an `_async` variant exists
for each. Loss functions: `cross_entropy` (SFT), `importance_sampling` (RL
default), `ppo`, `cispo`, `dro`, or your own via `forward_backward_custom_async`.

## Things that are true and easy to miss

**Two checkpoint types, not interchangeable.** `save_weights_for_sampler` →
`sampler_weights/…` is servable and downloadable. `save_state` → `weights/…`
carries optimizer state and is for resuming. The download endpoint rejects the
latter with a 400. Save both.

**The context window is part of the model id.** `openai/gpt-oss-120b` is 32K;
`openai/gpt-oss-120b:peft:131072` is a different model at 128K and ~2.4× the
prefill price. Assert your configured window against
`get_server_capabilities()` at startup — configured above the served limit means
episodes die on `BadRequestError` mid-run, and they die in whichever arm has
longer conversations, which silently unbalances an A/B.

**Prompt format is a contract that outlives the run.** A checkpoint SFT'd on raw
text must be prompted as raw text forever after; wrapping it in a chat template
it never saw looks exactly like a fine-tune that did nothing. Record the format
next to the checkpoint path.

**In RL, everything except the policy must be constant inside a group.** The
advantage is a within-group difference, so a simulated user sampling at
temperature injects noise straight into the gradient and attributes it to the
policy. Measured in the reference project: at user temperature 0.5, two runs of
the *same* configuration differed by as much as the effect under study.

**Evaluate the base model before training it.** If it sits at a floor on your
task, every rollout in every group ties, every advantage is zero, and no
gradient ever flows — and no ablation you run against it can resolve anything.

**Reasoning tokens count against `max_tokens`.** A model that spends its budget
inside `<think>` emits neither a reply nor a tool call, which is not a valid
message. Budget 4096, not 1024, and add a truncation retry.

**Do the multiplication before launching.** RL cost is
`iterations × tasks_per_iter × group_size × turns`. Every one of those is a flag
someone bumps on its own:

```bash
python scripts/tinker_pricing.py estimate-rl --model openai/gpt-oss-120b \
    --iterations 10 --tasks-per-iter 8 --group-size 8 \
    --turns 20 --avg-prompt 8000 --avg-completion 400
```

## Recording the run

Tinker keeps almost nothing locally — a hosted run UUID and that is it. Anything
you want to inspect later has to be written by you.

Use the companion **research-observability** skill. It was built against this
stack: `run.sample()` takes Tinker's prompt and completion token ids directly, so
the trace records exactly the tokens the policy was updated on, and its viewers
and cost report work on the result unchanged. That skill records the loop; this
one runs it.

## Links

- Docs and model catalogue: <https://tinker-docs.thinkingmachines.ai/tinker/models/>
- CLI reference: <https://tinker-docs.thinkingmachines.ai/tinker/cli/checkpoint/>
- Console / API keys: <https://console.tinker.ai>
