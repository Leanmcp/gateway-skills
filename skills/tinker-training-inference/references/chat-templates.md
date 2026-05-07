# Chat formats, tool schemas, and parsing completions

Tinker samples tokens. If you want an agent, you own the render → sample → parse
round trip, and both ends must agree on the model family's format. This is the
layer where a mismatch produces a model that "doesn't follow instructions" when
it is actually being asked in a language it was never trained in.

## The round trip

```
messages + tools  --render_prompt-->  token ids  --sample-->  token ids
                  <--parse_completion--  decoded text
```

Keep the renderer and the parser **next to each other**, in one module. They are
two halves of one contract, and when they drift the failure is silent: the model
emits a correct tool call in its own format and your parser returns `None`, so
the agent looks like it just stopped calling tools.

## Rendering

Start with the tokenizer's own template — it encodes what the model was trained
on:

```python
text = tokenizer.apply_chat_template(
    messages,                       # [{"role": ..., "content": ...}, ...]
    tools=tool_schemas,             # OpenAI-style function schemas, if supported
    tokenize=False,
    add_generation_prompt=True,     # ends with the assistant header, ready to continue
    enable_thinking=True,           # Qwen3-specific; ignored elsewhere
)
prompt_tokens = tokenizer.encode(text)
```

`add_generation_prompt=True` is what makes the model continue as the assistant
rather than predicting the next user turn.

## The three families you will meet

### Hermes-style (Qwen3, most open models)

Turns end with `<|im_end|>`. Tool calls appear inline as JSON in a block:

```
<tool_call>
{"name": "get_weather", "arguments": {"city": "Paris"}}
</tool_call>
```

Several calls fit naturally in one turn. Stop string: `["<|im_end|>"]`.

### Harmony (GPT-OSS)

Channelled messages. The model reasons in an `analysis` channel and answers in
`final`; tool calls are addressed with a recipient:

```
<|channel|>analysis<|message|>...reasoning...
<|channel|>commentary to=functions.get_weather<|message|>{"city": "Paris"}<|call|>
<|channel|>final<|message|>...visible answer...<|return|>
```

Stop strings: `["<|return|>", "<|call|>"]` — `<|return|>` ends a final answer,
`<|call|>` ends a tool call. Consequence: sampling is cut at the *first* tool
call, so one turn carries at most one call unless you deliberately continue
(see [hyperparameters.md](hyperparameters.md)).

GPT-OSS always reasons, and those tokens count against `max_tokens`. Budget
generously — 4096, not 1024.

### Typed-block formats

Some families (e.g. Inkling) wrap each part of a message in its own block:
thinking, text, and tool-invocation blocks inside one model message, with a
distinct end-of-sampling marker.

The trap here: **individual blocks end with a marker that must NOT be a stop
string.** Stop on the per-block terminator and sampling cuts right after the
thinking block, before the reply or tool call was ever emitted. Stop only on the
end-of-message marker.

## Stop strings, in code

```python
if "gpt-oss" in base_model.lower():
    STOP_STRINGS = ["<|return|>", "<|call|>"]
elif "inkling" in base_model.lower():
    STOP_STRINGS = ["<|content_model_end_sampling|>"]      # NOT the per-block end
else:
    STOP_STRINGS = ["<|im_end|>"]                          # Hermes / Qwen
```

Derive them from the model id in one place. Every sampling call — agent,
simulated user, judge, summarizer — must use the same set, or one speaker runs
past its turn and starts writing the other's lines.

## Parsing a completion

One function per format family, returning a common shape:

```python
def parse_completion(text: str) -> tuple[str | None, str | None, list[ToolCall]]:
    """-> (thinking, content, tool_calls). Accumulate a LIST of calls for every
    format — one turn may legitimately carry several, and returning only the
    first silently drops work the model did."""
```

Be liberal in what you accept. Models emit near-miss formatting constantly:
a missing closing tag, arguments as a JSON string instead of an object, a stray
prose sentence before the block. Parse defensively and **log what you could not
parse** as an event — an unparsed turn that silently becomes an empty message is
invisible, and it looks like the model stalled.

## Tool schemas

Build OpenAI-style function schemas once per domain and pass them to the
template on **every** assistant call:

```python
tool_schemas = [{
    "type": "function",
    "function": {"name": t.name, "description": t.description, "parameters": t.params},
} for t in tools]
```

Two consequences worth internalising:

1. **Schemas are a fixed context cost paid every single turn.** Twenty tools
   with long descriptions can be several thousand tokens of every prompt, in an
   agent loop, for the whole episode. Measure it — the per-tool and total token
   cost of that slice is a real number and often a surprising one, and it is the
   first thing to cut when episodes run out of window.
2. **They are not in your traces** unless you put them there, because they are
   built from the domain rather than sampled. Snapshot them to a file next to the
   run so a trace can be interpreted later.

## Verifying the round trip

Before training anything, sample one turn and check by hand:

```python
print(repr(text[-500:]))                       # does the prompt end with the assistant header?
print(repr(tokenizer.decode(completion)))      # is the format what you expected?
print(parse_completion(decoded))               # does the parser recover it?
```

Ten minutes here saves a training run. A silent format mismatch does not error —
it just trains on garbage, and the loss curve looks perfectly healthy while it
does.
