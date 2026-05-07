# Every knob, and what it costs to get wrong

Grouped by what they control. The defaults column is a working starting point,
not a recommendation for your task.

## Model and adapter

| knob | default | notes |
| --- | --- | --- |
| `base_model` | — | must be currently served (`get_server_capabilities()`); models retire |
| `rank` (LoRA) | 32 | capacity. 8–16 for style/format, 32 for most task fine-tuning, 64+ when the task needs genuinely new behaviour. Higher rank costs training throughput and overfits small datasets faster |
| context window | model-dependent | **part of the model id** — `:peft:131072` variants are different models at different prices |

Pick the model against your task before running ablations. A model that scores
~0 on your benchmark cannot separate two arms — a floor at zero has no
resolution — and every comparison you run against it is uninterpretable.

## Optimizer

| knob | default | notes |
| --- | --- | --- |
| `AdamParams(learning_rate=...)` | `1e-4` | for LoRA. Full fine-tuning wants ~10× lower. Too high on RL shows up as reward collapsing after a good iteration |
| effective batch | — | not a parameter: call `forward_backward` several times before one `optim_step` and gradients accumulate |
| epochs / iterations | — | SFT overfits small datasets fast; check the samples, not just the loss |

## Sampling

```python
types.SamplingParams(max_tokens=4096, temperature=0.7, stop=["<|im_end|>"], seed=1234)
```

| knob | notes |
| --- | --- |
| `max_tokens` | **reasoning tokens count against this.** A model that spends its budget inside `<think>` emits neither a reply nor a tool call — an invalid message. 4096 is a sane floor for reasoning models; 1024 is not |
| `temperature` | 0.0 for evaluation and for anything that should be a fixture; ~1.0 for RL exploration; ~0.5 when you want some diversity in eval |
| `stop` | must match the chat format — see [chat-templates.md](chat-templates.md). Wrong stop strings make the model run past its turn and hallucinate the next speaker |
| `seed` | forward it. A bridge that accepts a seed and never passes it to `SamplingParams` leaves every turn unseeded, and you spend weeks wondering why nothing reproduces |
| `num_samples` | G completions of one prompt in one call — how an RL group is drawn, and cheaper than G calls since the prompt prefills once |

### Temperature deserves its own paragraph

In group-relative RL the advantage is computed **within** a group of rollouts of
the same task. Any variation from a source other than the policy is noise
injected straight into the gradient and attributed to the policy.

So: the agent explores at ~1.0, and every fixture — a simulated user, a
stochastic tool, an LLM judge — runs at 0.0. Measured in the reference project:
with the simulated user at 0.5, two runs of the *same* configuration with the
same seed differed by 0.099 vs 0.242 mean reward, which is the same magnitude as
the effect the experiment was built to detect. At that setting the experiment
cannot resolve its own question.

Consistency is not correctness — a fixture that invents a wrong detail will now
invent the same wrong detail every time. But consistency is what makes a
measurement possible at all.

## Context and truncation guards

| knob | typical | why |
| --- | --- | --- |
| `MODEL_CONTEXT_WINDOW` | from the service | assert it at startup; configured *above* the served limit means rejected requests instead of clean episode ends |
| `MIN_COMPLETION_TOKENS` | 256 | less room than this left → end the episode rather than send a doomed request |
| `CONTEXT_OVERFLOW_REWARD` | 0.0 | overflow becomes a *scored* outcome, not a crash |
| `TRUNCATION_RETRIES` | 2 | resample with a doubled budget when the completion hit `max_tokens` |
| `MAX_TOKENS_HARD_CAP` | 8192 | ceiling on that doubling |

Always clamp the budget to what the window has left:
`budget = min(max_tokens, MAX_TOKENS_HARD_CAP, available)`.

## Episode / rollout structure (agentic RL)

| knob | typical | notes |
| --- | --- | --- |
| `max_steps` | task-dependent | orchestrator turns per episode, counting agent + user + one env turn per tool call. Too low truncates episodes before they can succeed, and a truncated episode is a different failure from a wrong one — do not let them share a bucket |
| `group_size` | 8 | rollouts per task for the GRPO baseline. Doubling it doubles the bill |
| `tasks_per_iter` | 8 | |
| `iterations` | 10–50 | |
| `rollout_workers` | 1–8 | episodes are embarrassingly parallel; the usual blocker is a logging layer with shared mutable context |

Cost is the product of all of these — run
`scripts/tinker_pricing.py estimate-rl` before launching.

## Reasoning / thinking

| knob | notes |
| --- | --- |
| `enable_thinking` | a Qwen3 chat-template kwarg. Ignored by families whose template always reasons (GPT-OSS always emits an analysis channel) |
| budget | thinking is billed and counted like any other completion token. Gemini-style separate accounting does not apply here |

## Multiple tool calls per turn

Whether a model can emit two tool calls in one turn is a **chat-format**
question, not a capability question. On Harmony, `<|call|>` is both the
terminator of a tool-call message and a stop string, so sampling is cut at the
first call and the model never gets to ask for a second. On Hermes-style formats
several calls already fit in one sample — models simply rarely do it, which is a
prompting matter.

If you need batched calls, the fix is not to remove `<|call|>` from the stop
list: Harmony's protocol after `<|call|>` is "a tool result comes next", so a
model left running will hallucinate one and answer from it. Re-sample with the
next assistant header forced, and keep the continuation **only** if the model
put a real recipient on it. Cost: one extra sample per tool-call turn, thrown
away when the answer is no. Make it opt-in, per arm.

Cap calls per turn so a model that keeps saying "yes, another one" cannot spend
the whole window inside one turn.

## Reward shaping

Not a Tinker knob, but the one that decides whether an RL run does anything.

All-or-nothing rewards on hard tasks produce groups where every rollout scores
zero, all advantages are zero, and the iteration costs a full group of sampling
for no gradient. **Count your tied groups** — a high tie rate means the reward is
too coarse or the temperature too low to explore. Partial credit is what keeps
the gradient alive until the policy is good enough for the sparse signal.

## Recording all of it

Build **one config dict**, print it to the log, and write it to the run folder —
so the log and the run can never disagree about what was run. Every knob above
belongs in it, including the ones you left at their defaults: a value you did not
record is a comparison you cannot make later. The **research-observability**
skill's `Run(config=...)` does this.
