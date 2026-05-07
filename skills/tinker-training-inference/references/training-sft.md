# Supervised fine-tuning on Tinker

Runnable template: `scripts/tinker_sft.py`. This file explains what it does and
why each piece is shaped that way.

## The loop

```python
service_client  = tinker.ServiceClient()
training_client = service_client.create_lora_training_client(
    base_model="Qwen/Qwen3-8B", rank=32)
tokenizer = training_client.get_tokenizer()

batch = [build_sft_datum(tokenizer, p, c) for p, c in dataset]

for epoch in range(epochs):
    result = training_client.forward_backward(batch, loss_fn="cross_entropy").result()
    training_client.optim_step(types.AdamParams(learning_rate=1e-4)).result()
    print(mean_loss(batch, result))

final = training_client.save_weights_for_sampler(name="final").result()
```

`forward_backward` runs the forward pass and **accumulates** gradients;
`optim_step` consumes them and updates the LoRA weights. They are separate on
purpose: call `forward_backward` several times before one `optim_step` and you
get a larger effective batch than fits in a single request. That is the
gradient-accumulation knob, and it is free.

## Building a Datum — read this part carefully

```python
def build_sft_datum(tokenizer, prompt: str, completion: str) -> types.Datum:
    prompt_tokens = tokenizer.encode(prompt)                       # includes BOS
    completion_tokens = tokenizer.encode(completion, add_special_tokens=False)
    full = prompt_tokens + completion_tokens

    target_tokens = full[1:]                # what must be predicted at each position
    boundary = len(prompt_tokens) - 1       # first completion target position
    weights = [0.0 if i < boundary else 1.0 for i in range(len(target_tokens))]

    return types.Datum(
        model_input=types.ModelInput.from_ints(full[:-1]),
        loss_fn_inputs={"target_tokens": target_tokens, "weights": weights},
    )
```

Three things that go wrong here, none of which show up in the loss curve:

1. **The boundary is `len(prompt_tokens) - 1`, not `len(prompt_tokens)`.**
   Target position `i` predicts `full[i+1]`, so the first completion token is
   predicted at position `len(prompt_tokens) - 1`. Off by one and you either
   train on one prompt token or skip the first completion token.
2. **`add_special_tokens=False` on the completion.** The prompt already carries
   BOS; encoding the completion with specials injects one mid-sequence.
3. **Weights are the only thing stopping the model from learning to generate
   your prompts.** Weight everything at 1.0 and the model trains on the
   questions as well as the answers. It still converges, it just gets worse at
   the thing you wanted.

## Reading the loss

`cross_entropy` returns per-token `logprobs` in `loss_fn_outputs`, and the
backend loss is `sum(-logprobs × weights)`. Divide by `sum(weights)`:

```python
def mean_loss(batch, result) -> float:
    total_nll = total_weight = 0.0
    for datum, out in zip(batch, result.loss_fn_outputs):
        logprobs = out["logprobs"].to_numpy().astype(np.float64)
        weights = datum.loss_fn_inputs["weights"].to_numpy().astype(np.float64)
        total_nll += float(-(logprobs * weights).sum())
        total_weight += float(weights.sum())
    return total_nll / max(total_weight, 1.0)
```

Reporting the raw sum makes long batches look worse than short ones and makes
the curve depend on your batching rather than your model.

## Raw completion vs chat template — decide once

This choice determines how you must prompt the model *forever after*, and
getting it inconsistent is the most common reason a fine-tune "does nothing".

**Raw completion.** Train on literal text (`"Q: ...\nA:"`). Simple, and at
inference you must use the exact same shape — `.completions.create` on the
OpenAI-compatible endpoint, never `.chat.completions`.

**Chat template.** Build the prompt through the tokenizer:

```python
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True)
```

Required if you want the checkpoint to behave like a chat model, or to be used
with tools. See [chat-templates.md](chat-templates.md) — the template differs by
model family (Hermes / Harmony / typed-block) and so do the stop strings.

Whichever you pick, **record it in the run config** next to the checkpoint path.
A checkpoint whose prompt format you have to guess is a checkpoint you will
re-train.

## Loss functions

| `loss_fn` | use |
| --- | --- |
| `cross_entropy` | SFT / next-token prediction |
| `importance_sampling` | basic policy-gradient RL |
| `ppo` | PPO — clipped ratio, more stable at larger steps |
| `cispo` | contrastive importance sampling |
| `dro` | distributionally robust objective |
| custom | `forward_backward_custom_async` with your own loss |

## Checkpointing during SFT

Two different things, and they are not interchangeable:

```python
training_client.save_state(name="epoch-4")              # -> weights/...
#   resumable: carries OPTIMIZER state. NOT downloadable, NOT servable.

training_client.save_weights_for_sampler(name="final")  # -> sampler_weights/...
#   servable and downloadable. NO optimizer state.
```

Save state periodically during a long run so a crash costs one epoch instead of
all of them, and resume with
`create_training_client_from_state_with_optimizer(path)` — plain weights loading
restarts Adam's moments at zero, which shows up as a loss spike right at the
resume point. Full detail in [checkpoints.md](checkpoints.md).

## Evaluate before and after, on the same probe

```python
before = training_client.save_weights_and_get_sampling_client(name="before")
# ... train ...
after  = training_client.save_weights_and_get_sampling_client(name="after")
```

Sampling the same prompt from both, greedily, at the start and end of the run is
thirty seconds of work and it is the difference between "the loss went down" and
"the model learned the thing". A loss that falls while the samples do not change
usually means the mask is wrong.

## Full fine-tuning vs LoRA

`create_lora_training_client(base_model=..., rank=32)` trains a low-rank adapter:
cheap, fast, and what the checkpoint export path assumes (the download is a PEFT
adapter, ~350 MB, not a standalone model). Rank is the capacity knob — see
[hyperparameters.md](hyperparameters.md). To run the result outside Tinker you
merge the adapter into the base weights; see [checkpoints.md](checkpoints.md).
