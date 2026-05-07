# Reinforcement learning / RFT on Tinker

Runnable template: `scripts/tinker_rl.py`. For RL over a multi-turn agent in an
environment, read this first and then [agentic-rl.md](agentic-rl.md).

## The loop

```
save weights -> sampling client     # the OLD policy
sample G rollouts per task
score each rollout                  # your reward function
advantage = reward - group mean     # GRPO-style baseline, no value network
build Datum: old logprobs + per-token advantages
forward_backward(loss_fn="importance_sampling")
optim_step
repeat
```

```python
sampling_client = training_client.save_weights_and_get_sampling_client(name=f"iter-{it}")
params = types.SamplingParams(max_tokens=16, temperature=1.0, stop=["\n"])

resp = sampling_client.sample(
    prompt=types.ModelInput.from_ints(prompt_tokens),
    num_samples=group_size, sampling_params=params).result()

rewards  = [reward(task, tokenizer.decode(s.tokens)) for s in resp.sequences]
baseline = float(np.mean(rewards))

rl_data = [build_rl_datum(prompt_tokens, list(s.tokens),
                          completion_logprobs(sampling_client, s, prompt_tokens),
                          r - baseline)
           for s, r in zip(resp.sequences, rewards) if s.tokens]

result = training_client.forward_backward(rl_data, loss_fn="importance_sampling").result()
training_client.optim_step(types.AdamParams(learning_rate=lr)).result()
```

## Why the loop starts by saving weights

Importance sampling corrects for the ratio between the current policy and the
one that generated the rollouts. The stored `logprobs` must therefore come from
**exactly the weights that produced those tokens**. `save_weights_and_get_sampling_client`
guarantees that in one call. Reusing a sampler from a previous iteration leaves
a stale denominator that biases every update — and nothing errors, the loss just
means something else than you think.

## The RL Datum

```python
def build_rl_datum(prompt_tokens, completion_tokens, completion_logprobs, advantage):
    full = prompt_tokens + completion_tokens
    target_tokens = full[1:]
    boundary = len(prompt_tokens) - 1

    weights = [0.0] * len(target_tokens)
    advantages = [0.0] * len(target_tokens)
    old_logprobs = [0.0] * len(target_tokens)
    for j, lp in enumerate(completion_logprobs):
        i = boundary + j                     # target position of the j-th completion token
        weights[i] = 1.0
        advantages[i] = advantage
        old_logprobs[i] = lp

    return types.Datum(
        model_input=types.ModelInput.from_ints(full[:-1]),
        loss_fn_inputs={"target_tokens": target_tokens, "weights": weights,
                        "logprobs": old_logprobs, "advantages": advantages},
    )
```

Same next-token alignment as SFT, plus two extra arrays. The advantage is
constant across the completion (one scalar reward per rollout, spread over the
tokens that produced it) and zero everywhere else. Misalign the boundary and you
apply the advantage to prompt positions: the loss still moves, the policy learns
nothing you intended.

## Old-policy logprobs

```python
def completion_logprobs(sampling_client, seq, prompt_tokens):
    if getattr(seq, "logprobs", None) is not None:
        return [float(x) for x in seq.logprobs]
    full = prompt_tokens + list(seq.tokens)
    all_lp = sampling_client.compute_logprobs(types.ModelInput.from_ints(full)).result()
    return [float(x) for x in all_lp[len(prompt_tokens):]]      # all_lp[k] = logprob of full[k]
```

The sampler normally attaches them. You need the recompute path whenever you
**assembled** the token list yourself — e.g. a multi-tool-call continuation that
stitched several samples together. In that case the sequence's own logprobs
cover only the first sample, and silently using them leaves most of the
completion with a wrong (or zero) denominator.

## Group-relative advantages

The baseline is the mean reward within a group of rollouts of the *same* task.
No value network, low variance, and it makes one property essential:

**Everything except the policy must be held constant inside a group.** The
advantage is a difference between rollouts of the same task, so any variation
from another source — a stochastic environment, a simulated user sampling at
temperature, a nondeterministic tool — is noise injected directly into the
gradient and attributed to the policy. In the reference project, dropping the
simulated user's temperature from 0.5 to 0.0 was worth as much as any
experimental arm being tested; at 0.5, two runs of the *same* configuration
differed by more than the effect under study.

**Tied groups contribute nothing.** If every rollout in a group gets the same
reward, all advantages are zero and that task cost you a full group of sampling
for no gradient. Count them — a high tie rate means the reward is too coarse
(all-or-nothing on a hard task = all zeros) or the temperature too low to
explore. Shaped, partial-credit rewards are what keep the gradient alive early.

## Choosing the RL loss

| `loss_fn` | when |
| --- | --- |
| `importance_sampling` | the default. Simple, correct, fine for modest steps |
| `ppo` | clips the ratio — reach for it when large advantages destabilise the run |
| `cispo` | contrastive variant |
| `dro` | distributionally robust |

For `importance_sampling` the reported loss lives in metrics:

```python
loss = float(result.metrics.get("loss:sum", float("nan")))
```

Do not read it as "lower is better" — it is a surrogate objective, not an error.
**Mean reward per iteration is the number that matters**, and it is the one to
plot.

## What to record each iteration

RL runs are long and expensive and you get one shot at capturing what happened:

```python
run.metric(step=it, mean_reward=mean_r, loss=loss, n_data=len(rl_data),
           n_tied_groups=n_tied, lr=lr, temperature=temperature)
run.event("weights_snapshot", sampler=label, path=path)
run.event("checkpoint", name=name, tinker_path=p)
```

Plus every rollout's transcript. Use the **research-observability** skill — it
takes the prompt and completion token ids directly, so the trace records exactly
the tokens the policy was updated on.

## Cost, before you launch

RL cost is a product of four flags, and people bump them independently:

```
episodes = iterations × tasks_per_iter × group_size
generations = episodes × turns_per_episode
```

Doubling the group size doubles the bill. Do the multiplication first:

```bash
python scripts/tinker_pricing.py estimate-rl --model openai/gpt-oss-120b \
    --iterations 10 --tasks-per-iter 8 --group-size 8 \
    --turns 20 --avg-prompt 8000 --avg-completion 400
```

`--avg-prompt` is the **mean** prompt across the episode. In an agent loop the
prompt grows every turn, so use roughly half the final context — using the first
turn's prompt underestimates by several times, which is the usual way an RL
budget is blown.
