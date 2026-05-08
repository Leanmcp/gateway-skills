# Platform adapters

One normalizer per platform, then everything downstream is identical. This is
the file to open when the answer to "which platform?" is anything other than one
already listed here.

Contents:
- [The five questions](#the-five-questions)
- [OpenAI](#openai)
- [Google Gemini](#google-gemini)
- [Anthropic](#anthropic)
- [LiteLLM — one wrapper, every provider](#litellm--one-wrapper-every-provider)
- [Tinker (token-level)](#tinker-token-level)
- [vLLM / HF / self-hosted](#vllm--hf--self-hosted)
- [Anything else in 15 lines](#anything-else-in-15-lines)
- [Framework-level wiring](#framework-level-wiring-langchain-agents-sdks-orchestrators)
- [Cost](#cost)

## The five questions

A normalizer answers these about one response, and nothing else:

```python
Turn(
    text=...,          # raw decoded output
    content=...,       # visible reply after parsing (None if tools only)
    thinking=...,      # reasoning trace, if exposed
    tool_calls=[{"name": str, "arguments": dict, "id": str}],
    finish=...,        # stop | length | tool_calls | ...
    usage={"prompt_tokens": int, "completion_tokens": int},
)
```

`scripts/obs_adapters.py` ships `norm_openai`, `norm_anthropic`, `norm_gemini`,
`norm_litellm`, and `norm_auto` (shape-sniffing, for a quick script). The
`Observed*` wrappers call the provider, log the turn, and hand back the
**untouched SDK object** — so wrapping never changes your control flow, and you
can adopt it one call site at a time.

## OpenAI

```python
from openai import OpenAI
from obs import Run
from obs_adapters import ObservedOpenAI, log_tool_results

run = Run("eval", config={"agent_model": "gpt-5.4-nano"}, root="runs")
client = ObservedOpenAI(OpenAI(), run, role="agent")

with run.session(task="task_007", trial=0):
    messages = [{"role": "system", "content": policy},
                {"role": "user", "content": first_turn}]
    for _ in range(MAX_STEPS):
        resp = client.chat(model="gpt-5.4-nano", messages=messages, tools=tools)
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if not msg.tool_calls:
            break
        results = [run_tool(tc) for tc in msg.tool_calls]   # your executor
        log_tool_results(run, results, requestor="agent")   # {"role":"tool",...}
        messages += results
    run.episode_done(reward=grade(messages))
```

The system message is pulled out of `messages` and logged once per session, so
the conversation view is not buried under it on every turn.

Reasoning models: `norm_openai` reads `message.reasoning_content` /
`message.reasoning`, whichever the provider populates. Some models return the
reasoning only as an opaque id — log that id in `extra` so a turn can still be
traced back to a stored trace.

`gpt-5` family models reject a non-default `temperature` (HTTP 400). Record the
fact that you dropped it in `config.json` — a sweep where one arm silently ran
at a different temperature is a sweep you have to rerun.

## Google Gemini

```python
from google import genai
from obs_adapters import ObservedGemini

client = ObservedGemini(genai.Client(), run, role="agent")
resp = client.generate(
    model="gemini-3-pro",
    contents=contents,
    config={"system_instruction": policy, "tools": tools},
)
```

Gemini specifics `norm_gemini` handles for you:

- Parts are heterogeneous: a part is a `function_call`, a normal `text`, or a
  `text` with `thought=True` (the reasoning summary). Concatenating `.text`
  naively merges reasoning into the reply — a mistake that silently corrupts
  every downstream judge.
- `finish_reason` is an enum; `.name` is what you want in a file.
- `usage_metadata` uses `prompt_token_count` / `candidates_token_count`, plus
  `thoughts_token_count` which is billed but **not** in the candidates count.
  Record all three or your cost math will be quietly low on thinking models.
- Function-call `args` is a proto map — `dict(fc.args)` before storing.

Via Vertex AI, auth is env + ADC, not a key:

```bash
export VERTEXAI_PROJECT="your-gcp-project"
export VERTEXAI_LOCATION="us-central1"     # a region that serves the model
gcloud auth application-default login       # or GOOGLE_APPLICATION_CREDENTIALS=<sa.json>
```

## Anthropic

```python
from anthropic import Anthropic
from obs_adapters import ObservedAnthropic

client = ObservedAnthropic(Anthropic(), run, role="agent")
resp = client.create(model="claude-opus-5", max_tokens=4096,
                     system=policy, messages=messages, tools=tools)
```

Content is a list of typed blocks (`text`, `thinking`, `tool_use`), so nothing
needs parsing heuristics — the separation you have to reconstruct on other
providers is given. `usage` carries `cache_read_input_tokens` and
`cache_creation_input_tokens`; `norm_anthropic` keeps both, and you want them,
because prompt-cache behaviour is the main driver of cost variance across
otherwise identical runs.

Some models reject `temperature`/`top_p`/`top_k` outright. Same rule as above:
whatever you drop, record in `config.json`.

## LiteLLM — one wrapper, every provider

Usually the highest-leverage adapter. LiteLLM returns an OpenAI-shaped response
for every provider it fronts, so one logging path covers all of them and a
cross-model comparison becomes a change of one string:

```python
from obs_adapters import ObservedLiteLLM

llm = ObservedLiteLLM(run, role="agent")
resp = llm.completion(model=AGENT_MODEL, messages=messages, tools=tools,
                      max_tokens=4096)
```

| `AGENT_MODEL` | provider | auth |
| --- | --- | --- |
| `gpt-5.4-nano` | OpenAI direct | `OPENAI_API_KEY` |
| `vertex_ai/gemini-3-pro` | Gemini on Vertex | `VERTEXAI_PROJECT` + ADC |
| `vertex_ai/claude-fable-5` | Anthropic on Vertex | `VERTEXAI_PROJECT` + ADC |
| `openrouter/moonshotai/kimi-k3` | OpenRouter | `OPENROUTER_API_KEY` |
| `fireworks_ai/accounts/.../models/...` | Fireworks | `FIREWORKS_API_KEY` |
| `openai/<name>` + `api_base` | your own vLLM server | whatever you set |

**Register prices LiteLLM does not ship**, or `cost` silently records `0.0` for
exactly the models you are least sure about:

```python
import litellm
litellm.register_model({
    "moonshotai/kimi-k3": {"input_cost_per_token": 3.0 / 1e6,
                           "output_cost_per_token": 15.0 / 1e6,
                           "litellm_provider": "openrouter", "mode": "chat"},
})
```
Register under both the bare id and `<provider>/<id>` — the cost lookup may use
either depending on how the model string was passed.

## Tinker (token-level)

Tinker gives you the exact token ids on both sides. That is the whole reason to
prefer it for training work, and dropping the ids throws away the only thing a
hosted API cannot give you.

```python
from obs_adapters import log_tinker_turn, Turn

def parse(text: str) -> Turn:
    """Model-family specific: split the thinking block and the tool calls out
    of the decoded completion. Keep this next to the renderer that BUILT the
    prompt — the two must agree on the chat template."""
    thinking, content, tool_calls = split_chat_template(text)
    return Turn(text=text, content=content, thinking=thinking,
                tool_calls=tool_calls, finish="stop")

result = sampling_client.sample(prompt=prompt, num_samples=1,
                                sampling_params=params)
log_tinker_turn(run, "agent",
                prompt_tokens=prompt.to_ints(),
                completion_tokens=result.sequences[0].tokens,
                text=tokenizer.decode(result.sequences[0].tokens),
                parse=parse,
                truncated=(result.sequences[0].stop_reason == "length"))
```

Things worth logging as events on this path, because they are invisible
otherwise and each one distorts results:

```python
run.event("truncation_retry", role="agent", attempt=1, new_max_tokens=2048)
run.event("empty_output_retry", role="agent", truncated=True)
run.event("duplicate_tool_call_retry", role="agent", tool_name=name,
          arguments=args, retry_temperature=0.7)
run.event("context_overflow", prompt_tokens=n, context_window=w, available=w - n)
run.event("weights_snapshot", sampler=name, path=path)
run.event("checkpoint", name=name, remote_path=p, local_dest=str(dest))
```

For training loops, pair per-turn logging with `run.metric(step=it,
mean_reward=..., loss=..., num_data=..., lr=...)` each iteration. The
per-episode stream tells you *why*; `metrics.jsonl` tells you *whether*.

> The companion **tinker-training-inference** skill covers the training and
> inference side (hyperparameters, LoRA, checkpointing, pricing). Use both
> together: that one runs the loop, this one records it.

## vLLM / HF / self-hosted

Two options, and the choice matters:

- **OpenAI-compatible server** (`vllm serve`): use `ObservedOpenAI` with
  `base_url=`, or `ObservedLiteLLM` with `model="openai/<name>"` and
  `api_base=`. Zero extra code, but you lose the token ids.
- **In-process** (`llm.generate(...)`, HF `model.generate`): use
  `log_tinker_turn` — you have `prompt_token_ids` and `token_ids` on the output,
  so keep them.

## Anything else in 15 lines

```python
from obs_adapters import Turn, ObservedCallable

def norm_myplatform(resp) -> Turn:
    return Turn(
        text=resp["output"],
        content=resp["output"] or None,
        thinking=resp.get("scratchpad"),
        tool_calls=[{"name": c["tool"], "arguments": c["args"]}
                    for c in resp.get("calls", [])],
        finish=resp.get("stop_reason"),
        usage={"prompt_tokens": resp["in_tokens"],
               "completion_tokens": resp["out_tokens"]},
    )

generate = ObservedCallable(my_client.generate, run, role="agent",
                            normalizer=norm_myplatform)
resp = generate(prompt=..., tools=...)     # logged; returns the raw response
```

`ObservedCallable` also records failures: an exception is logged as an `error`
event with its traceback and then re-raised, so a run that crashed still
explains itself.

## Framework-level wiring (LangChain, agent SDKs, orchestrators)

When the loop belongs to a framework, you usually cannot wrap the call site.
Two patterns, in order of preference:

1. **Subclass the framework's model/agent class** and log in its generate hook.
   This is what the reference implementation does — `LoggedLLMAgent` subclasses
   the stock agent, calls `super()._generate_next_message(...)`, and logs the
   result. Behaviour is unchanged by construction, which is the property you
   want when the logged runs are also the reported numbers.
2. **Use the framework's callback/hook interface** and translate its events into
   `run.sample` / `run.tool_result`. Cheaper, but callback APIs tend to omit
   whichever field you later need (usually the reasoning trace or the exact
   arguments), so verify against a known episode before trusting it.

Whichever you pick, log the *auxiliary* models too — the judge, the summarizer,
the router, the retrieval LLM — under their own `role`. An episode whose grade
came from an unlogged judge cannot be debugged, only re-run.

## Cost

Prefer the provider's own number when it exists (`_hidden_params.response_cost`
on LiteLLM, `usage` × registered prices otherwise) and store it per turn.
`obs_report.py` sums it per run. Two runs with the same reward and a 4× cost gap
is a real result, and it is invisible unless you recorded it turn by turn.
