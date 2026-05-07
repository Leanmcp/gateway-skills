# Troubleshooting

Real failures from real runs, with the fix and — where it matters — the reason
the failure was expensive rather than merely annoying.

## Errors

### `BadRequestError: N prompt tokens + M max_tokens > W`

Your configured context window is above what the service serves for that model,
so your own overflow guard never fired.

```python
caps = service_client.get_server_capabilities()
{m.model_name: m.max_context_length for m in caps.supported_models}
```

Set the window to the served value, or switch to the long-context model id
(`…:peft:131072`) — a different model at a different price. Assert this at
startup ([setup.md](setup.md)).

**Why it matters beyond the crash:** these episodes die *mid-run*, and they die
in whichever arm happens to have longer conversations. That silently unbalances
an A/B — one arm loses a task the other completes. A wrong number, not a wrong
log line.

### `400 - Checkpoint weights/<name> is not a sampler weights checkpoint`

You tried to download or sample a training-state checkpoint. Only
`sampler_weights/…` works for that; `weights/…` exists to resume training.
Re-save with `save_weights_for_sampler(name)`. See
[checkpoints.md](checkpoints.md).

### `No such command 'checkpoints'`

The CLI command is `tinker checkpoint` — singular.

### Model creation fails outright

The model retired. The Llama-3.x family is gone; Kimi-K2.5 is marked retiring.
List what is served and pick from that.

### `RequestFailedError: For field input_sequence[0][0], token_ids max …`

A token id in your `ModelInput` is outside the model's vocabulary — almost
always a tokenizer mismatch: tokens encoded with one model's tokenizer and sent
to another. Always use `training_client.get_tokenizer()` / the sampling client's,
never a separately constructed one.

## Silent wrongness — the expensive category

### The fine-tune "did nothing"

Check, in order:

1. **Format mismatch.** SFT on raw completion text, evaluated through a chat
   template (or the reverse). The model never saw the shape you are asking in.
   `.completions.create` for raw-trained, `.chat.completions.create` for
   chat-trained.
2. **Loss mask.** If `weights` is 1.0 everywhere, the model also trained on your
   prompts. The loss curve looks fine.
3. **Boundary off by one.** `boundary = len(prompt_tokens) - 1`, because target
   position `i` predicts `full[i+1]`.
4. **Never actually evaluated.** Sample the same probe before and after,
   greedily. A falling loss with unchanged samples usually means 2 or 3.

### RL reward flat at zero from the start

The base model cannot do the task at all, so every rollout in every group scores
zero, every advantage is zero, and no gradient ever flows. **Run eval before
training.** If the base model is at a floor, no amount of RL separates your arms
— a floor has no resolution. Fix the task, shape the reward, or change the model.

In the reference project this went undetected for months: a small model was the
default at a 0.9% solve rate while ablations were run against it, and every
`mean_reward 0.000` in the results was that, not the arms.

### RL reward moves but the experiment does not replicate

Something other than the policy is varying **inside** a group. The advantage is
a within-group difference, so a stochastic simulated user, a nondeterministic
tool, or an unseeded judge injects noise straight into the gradient, attributed
to the policy.

Measured: with the simulated user at temperature 0.5, two runs of the *same*
configuration and seed differed by 0.099 vs 0.242 mean reward — the same
magnitude as the effect under study. Set every fixture to 0.0.

### Nothing reproduces despite a seed

The seed is not reaching `types.SamplingParams`. A bridge that accepts a `seed`
argument and forgets to forward it leaves every turn unseeded, and the symptom is
indistinguishable from "LLMs are just nondeterministic".

### The agent stops calling tools

Your parser is silently failing on the model's output. Log the raw decoded text
of every turn and the parse result — a near-miss format (missing closing tag,
arguments as a JSON string, prose before the block) returns no calls and looks
like the model gave up. Parse liberally; emit an event when parsing fails.

### The model runs past its turn and writes the other speaker's lines

Wrong `stop` strings for the chat format. Derive them from the model id in one
place, and use the same set for every speaker. See
[chat-templates.md](chat-templates.md).

### Turns come back empty

The completion was truncated inside the reasoning block: the model spent
`max_tokens` thinking and emitted neither a reply nor a tool call. Raise the
budget (4096, not 1024, for reasoning models) and add a truncation retry with a
doubled budget. See [agentic-rl.md](agentic-rl.md).

### Episodes stall in a loop until `max_steps`

The model repeats an identical tool call. At greedy temperature there is no
randomness to escape with. Detect an exact repeat, resample **once** with a
one-line reminder and a floored temperature, then let `max_steps` be the
backstop.

Also: never let a `max_steps` truncation and a genuine wrong answer share a
bucket in your results. They are different failures and conflating them corrupts
the conclusion — flag them separately.

### A loss spike exactly at resume

You loaded weights without the optimizer state, so Adam's moments restarted at
zero. Use `create_training_client_from_state_with_optimizer(path)`.

### Cost far above the estimate

`avg_prompt` was set from the first turn's prompt rather than the episode mean.
In an agent loop the prompt grows every turn; use roughly half the final context.
Also check whether something perturbs the prompt prefix between turns (a
timestamp in the system prompt, tool schemas reordering) — that throws away the
80% cached-prefill discount on every turn of every episode.

## Performance

**Rollouts are slow.** They are embarrassingly parallel: run episodes in threads
with the `_async` client methods, and set `TINKER_SUBPROCESS_SAMPLING=1` to keep
sampling out of the GIL's way. If parallelism is blocked, check whether your
*logging* layer has shared mutable state — that, not Tinker, is the usual reason
a rollout loop is forced to shard across processes.

**Sampling a group.** `num_samples=G` in one call prefills the prompt once; G
separate calls prefill G times. Real money in an RL loop.
