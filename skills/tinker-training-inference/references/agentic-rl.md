# Agentic RL: training a tool-using agent in an environment

Single-turn RL (prompt → completion → reward) is the tutorial. Training an agent
that holds a multi-turn conversation, calls tools, and gets graded at the end
needs a layer between Tinker and the environment. This is what that layer has to
do, drawn from a working implementation
(`TAU2_WITH_TINKER/tinker_backend.py` + `train_tau2_tinker.py` in the tau2-bench
repo).

## The shape

Your environment/orchestrator expects an OpenAI-style `generate(system, messages,
tools) -> AssistantMessage`. Tinker speaks tokens. The bridge:

```
render_prompt(chat template + tool schemas)  ->  ModelInput.from_ints
    -> sampling_client.sample(...)           ->  token ids
    -> tokenizer.decode + parse_completion   ->  content / tool_calls
    -> AssistantMessage
```

and, for RL, it *also* records per generated turn:

```python
@dataclass
class TurnRecord:
    prompt_tokens: list[int]
    completion_tokens: list[int]
    logprobs: list[float]
```

which is exactly what `build_rl_datum` needs. One episode produces a list of
`TurnRecord`s; the episode's reward becomes the advantage on every one of them.

## Credit assignment across turns

The simplest scheme, and the one to start with: the episode's shaped reward
minus the group mean is applied to **every** agent turn in that episode. It is
crude — a good turn in a failed episode gets punished — but it works, it needs
no value network, and per-turn credit assignment is a research problem you do
not want between you and a first result.

Only the **agent's** turns become training data. The simulated user's turns are
sampled too (and should be logged), but they are environment, not policy.

## Things that break, and the guards for them

Every one of these has cost real runs. They are why the bridge is more than
thirty lines.

### Context overflow

An episode's prompt grows every turn. Past the window, the service rejects the
request and the episode dies mid-run — differently in different arms, silently
unbalancing an A/B.

```python
available = MODEL_CONTEXT_WINDOW - len(prompt_tokens)
if available < MIN_COMPLETION_TOKENS:          # e.g. 256
    run.event("context_overflow", prompt_tokens=len(prompt_tokens),
              available=available, context_window=MODEL_CONTEXT_WINDOW)
    raise ContextOverflowError(len(prompt_tokens), available)
```

Catch it in the rollout loop and end the episode with a fixed reward
(`CONTEXT_OVERFLOW_REWARD = 0.0`) so it is a *scored* outcome rather than a
crash. Keep a server-side backstop too — token accounting can differ slightly:

```python
except tinker.BadRequestError as e:
    if "context window" in str(e).lower():
        raise ContextOverflowError(...) from e
    raise
```

And clamp the sampling budget to what is left: `budget = min(max_tokens, MAX_TOKENS_HARD_CAP, available)`.

### Truncated completions

A reasoning model can spend its whole budget inside `<think>` and emit neither a
reply nor a tool call. That message fails validation and cannot reach the
orchestrator.

```python
truncated = ("length" in str(finish).lower() or len(completion_tokens) >= budget)
if truncated and retries < TRUNCATION_RETRIES and budget < cap:
    retries += 1
    budget = min(budget * 2, cap)
    run.event("truncation_retry", role=role, attempt=retries, new_max_tokens=budget)
    # resample
```

Give reasoning models real headroom: 4096 for both agent and simulated user is a
sane starting point, because thinking tokens count against the same budget as
the answer.

### Empty output

If the retry still yields nothing, resample once with a small tight budget and a
direct nudge appended to the system prompt — and if *that* fails, substitute a
fallback reply rather than propagating an invalid message.

### Duplicate tool calls

At greedy temperature a model that repeats a call has no randomness to escape
with, and it burns steps until `max_steps` at zero progress. Detect an exact
repeat (same name, same arguments) of this role's own previous call, then
resample **once** with a one-line reminder and a *floored* temperature —
resampling at the temperature that just got stuck does not maximise the odds of
escaping.

```python
run.event("duplicate_tool_call_retry", role=role, tool_name=name,
          arguments=args, retry_temperature=retry_temperature)
```

Cap it at one retry: a model that repeats even after being told should hit
`max_steps`, not a second layer of retries.

### The seed

`types.SamplingParams` takes a `seed`. If your bridge does not forward it, every
turn is unseeded no matter what the caller computed — which matters most for the
simulated user, where variation is pure noise. This is an easy field to forget
and produces "why can't I reproduce this" for weeks.

## Sampling parameters that matter here

| knob | agent | simulated user | why |
| --- | --- | --- | --- |
| temperature (rollout) | 1.0 | **0.0** | the agent explores; the user is a fixture and should not roll dice inside a GRPO group |
| temperature (eval) | 0.5 | 0.0 | |
| max_tokens | 4096 | 4096 | thinking counts against it |
| stop | per chat format | per chat format | see [chat-templates.md](chat-templates.md) |
| seed | per-episode | per-episode | reproducibility |

## Concurrency

Rollouts are embarrassingly parallel; run episodes in threads and use the
`_async` client methods. Set `TINKER_SUBPROCESS_SAMPLING=1` to move sampling out
of the GIL's way.

The thing that usually blocks thread-parallel rollouts is not Tinker but the
logging layer: a single shared context dict means two workers overwrite each
other's task tags. The **research-observability** skill's `Run` keeps context
thread-local for exactly this reason, so workers can each call
`run.session(task=..., trial=...)` safely.

## Evaluating during training

Evaluate off a **saved sampler checkpoint**, not the live training client, so
the eval sees a fixed policy:

```python
eval_sampler = training_client.save_weights_and_get_sampling_client(name=f"eval-{it}")
```

Use the same episode machinery as training but at eval temperature and without
recording `TurnRecord`s. Tag the events with `phase="eval"` so one run folder
holds both and the viewers can separate them.

## Ordering of the pieces

1. Get the bridge returning valid `AssistantMessage`s and log every turn.
2. Run **eval only** first. If the base model scores ~0 on your tasks, no amount
   of RL will separate your arms — a floor at zero has no resolution. Fix the
   task, the reward shaping, or the model before training anything.
3. Add the reward, and check its distribution: how often is a group tied?
4. Only then turn on training.

Step 2 is the one people skip, and it is the one that decides whether the
resulting numbers mean anything.
