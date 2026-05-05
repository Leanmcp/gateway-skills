# Reasoning models on Fireworks (gpt-oss and friends)

Reasoning models break assumptions that hold for every other model, and they
break them *quietly* — HTTP 200, well-formed response, nothing in it. Almost
every "the gateway returns empty" report traces back to this page.

## Two channels, not one

A reasoning model emits chain-of-thought into a **separate field** and only then
the final answer:

```json
{"choices": [{"message": {
    "content": null,
    "reasoning_content": "The user wants a greeting. I should be brief…"
}, "finish_reason": "length"}]}
```

- `content` — the visible answer. **May be `null` or `""`.**
- `reasoning_content` — the trace. Present when the model reasoned.

So code that reads `message.content` and nothing else will see `None` on a
perfectly successful call. Always fall back:

```python
msg = resp.choices[0].message
text = msg.content or getattr(msg, "reasoning_content", None)
```

Field naming varies by provider flavour (`reasoning_content`, `reasoning`);
check both.

## Reasoning tokens spend the same budget

This is the mechanism behind most of the confusion. `max_tokens` covers
reasoning **and** the answer. With a small budget the model spends everything
thinking and returns `content: ""` with `finish_reason: "length"` — it never
reached the answer.

Consequences:

- **A 1024-token budget is a floor for these models, not a generous default.**
  For agent turns with tools, 4096 is a more realistic starting point.
- **`finish_reason: "length"` with empty content means "raise the budget"**, not
  "the model is broken".
- **A tiny readiness ping never succeeds.** An 8-token ping to a reasoning model
  returns empty content forever, so a naive readiness check reports "still
  warming up" indefinitely. Use ≥128 tokens and accept `reasoning_content` as a
  sign of life — that is what `fw_ready.py` does.

## `content: null` crashes downstream

Frameworks that assume a string will die on the `None`, often far from the cause:

```
TypeError: expected string or bytes-like object, got 'NoneType'
```

Two distinct causes produce the identical symptom, and they need opposite fixes:

| cause | tell | fix |
| --- | --- | --- |
| reasoning ate the budget | `finish_reason: "length"`, `reasoning_content` populated | raise `max_tokens` |
| cold dedicated deployment | `finish_reason: "stop"`, zero completion tokens | warm it — [models.md](models.md) |

Check `finish_reason` and the usage counts before deciding which one you have.

## Diagnosing

```bash
# does it produce anything at all, and in which channel?
python fw_smoke.py --model gpt-oss-20b --max-tokens 1024

# same request with a deliberately small budget — reproduces the empty-content case
python fw_smoke.py --model gpt-oss-20b --max-tokens 16
```

`fw_smoke.py` prints `finish_reason`, then `content`, then falls back to
`reasoning_content`, and says explicitly when the budget was the limit.

## In an agent loop

**Budget generously and expect the reasoning to be invisible in the transcript
unless you capture it.** The trace is where the model's actual decision-making
lives, and a transcript that records only `content` cannot explain why the agent
called the wrong tool.

If you are recording runs (the **research-observability** skill), pass it
through as its own field:

```python
run.sample("agent", text=raw, content=msg.content,
           thinking=getattr(msg, "reasoning_content", None),
           tool_calls=calls, finish=choice.finish_reason, usage=resp.usage)
```

Reading the reasoning right where a wrong tool call happened is the fastest path
from "it failed" to "here is why".

## Tool calling

A reasoning model may return **tool calls with `content: null`** — that is
normal and correct: it decided to call a tool instead of speaking. Do not treat
null content as failure when `tool_calls` is populated.

Order of checks for a turn:

1. `tool_calls` non-empty → the model acted.
2. `content` non-empty → the model spoke.
3. neither, `finish_reason == "length"` → budget. Retry with a larger one.
4. neither, `finish_reason == "stop"` → genuinely empty. Investigate the model
   or the deployment, and log it — silently substituting a blank turn hides the
   problem for the rest of the run.

## Cost

Reasoning tokens are billed as output tokens. A model that thinks for 800 tokens
before a 40-token answer costs like an 840-token answer. When comparing models
on price, compare **completion tokens actually consumed**, not the answers' visible
length — the gateway's observability shows the real numbers.
