# Inference on Tinker

Runnable: `scripts/tinker_infer.py`.

The key fact: **the weights live server-side.** Every
`save_weights_for_sampler(name)` created a persistent
`tinker://<run>/sampler_weights/<name>` path, and that path is all you need to
run the model again. The files you downloaded with `tinker checkpoint download`
are only for taking the model *elsewhere* — Fireworks, Ollama, a local merge.

Only `sampler_weights/...` paths work for inference. A `weights/...` path is
training state and both the sampling and download endpoints reject it.

## Route 1: the SDK (token-level)

```python
import tinker
from tinker import types

service_client = tinker.ServiceClient()
sampling_client = service_client.create_sampling_client(
    base_model="Qwen/Qwen3-8B",                 # still required: which base to attach to
    model_path="tinker://<run>/sampler_weights/final")
tokenizer = sampling_client.get_tokenizer()

params = types.SamplingParams(max_tokens=128, temperature=0.0,
                              stop=["<|im_end|>"], seed=1234)
resp = sampling_client.sample(
    prompt=types.ModelInput.from_ints(tokenizer.encode(prompt)),
    num_samples=1, sampling_params=params).result()

print(tokenizer.decode(resp.sequences[0].tokens))
```

Use this inside a training loop or whenever you need exact accounting: you hold
the prompt and completion token ids, and `compute_logprobs` is available on the
same client.

Per sequence you get `tokens`, `logprobs` (usually), and a finish/stop reason —
check it, because `"length"` means the answer was cut off and whatever you parse
out of it is partial.

Omit `model_path` to sample the raw base model.

## Route 2: the OpenAI-compatible endpoint (HTTP)

Tinker exposes an OpenAI-compatible endpoint (beta). No Tinker client, no
tokenizer — override the base URL and use the `tinker://` path as the model name:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1",
    api_key=os.environ["TINKER_API_KEY"])          # the same key

resp = client.completions.create(
    model="tinker://<run>:train:0/sampler_weights/final",
    prompt="Q: What is the capital of France?\nA:",
    max_tokens=32, temperature=0.0, stop=["\n"])
print(resp.choices[0].text)
```

Best for poking at a checkpoint, and it means any tool that speaks the OpenAI API
can drive your fine-tune with a base-URL change.

### `/completions` or `/chat/completions`?

**Match how the checkpoint was trained.** A model SFT'd on raw text
(`"Q: ...\nA:"`) must be prompted that way; wrapping it in a chat template it
never saw gives visibly worse answers and reads like the fine-tune failed. A
chat-templated checkpoint needs `.chat.completions.create`.

This is the single most common confusion with Tinker checkpoints, so record the
format alongside the checkpoint path when you train.

### Beta limitations

The endpoint does not enforce strict `json_schema` decoding. `client.chat.completions.parse(response_format=MyModel)`
therefore fails — the server ignores the schema, the model answers in prose, and
pydantic raises `json_invalid` trying to validate it. The workaround keeps the
Pydantic model as the single source of truth:

```python
schema = MyModel.model_json_schema()
resp = client.chat.completions.create(          # plain create, not .parse
    model=CKPT,
    messages=[{"role": "system",
               "content": f"Reply with JSON only, matching:\n{json.dumps(schema)}"},
              {"role": "user", "content": text}],
    max_tokens=512, temperature=0.0)
raw = resp.choices[0].message.content
raw = raw[raw.index("{"): raw.rindex("}") + 1]  # defensively extract the object
obj = MyModel.model_validate_json(raw)          # validate client-side
```

Switch back to `.parse(response_format=...)` when the endpoint enforces schemas.

Tool calling works through the standard `tools=` parameter, but verify against
your checkpoint — whether the model emits well-formed calls depends on its chat
format and on whether it was trained with tools present.

## Sampling parameters

```python
types.SamplingParams(
    max_tokens=4096,      # reasoning tokens count against this — budget generously
    temperature=0.0,      # 0 for eval/fixtures, ~1.0 for RL exploration
    stop=["<|im_end|>"],  # MUST match the model's chat format
    seed=1234,
)
```

`stop` is not optional for chat-formatted models: get it wrong and the model
runs past the end of its turn and hallucinates the next speaker. See
[chat-templates.md](chat-templates.md) for the per-family values.

`num_samples=G` on one `sample()` call returns G independent completions of the
same prompt — that is how an RL group is drawn, and it is cheaper than G calls
because the prompt is prefilled once.

## Running the model outside Tinker

Three destinations, increasing effort:

1. **Another serving platform (Fireworks, etc.).** Download the adapter
   (`tinker checkpoint download`, or `push-hf` straight to HuggingFace as a PEFT
   adapter) and point the platform at it.
2. **Locally, merged.** The download is a LoRA adapter (~350 MB) and cannot run
   alone. Merge it into the base:
   ```python
   base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-8B", torch_dtype=torch.bfloat16)
   merged = PeftModel.from_pretrained(base, adapter_dir).merge_and_unload()
   merged.save_pretrained(out_dir); tokenizer.save_pretrained(out_dir)
   ```
   Budget ~16 GB download + ~16 GB output and ~32 GB RAM to merge on CPU.
3. **GGUF / Ollama.** Merge first, then convert the merged model.

Full detail in [checkpoints.md](checkpoints.md).
