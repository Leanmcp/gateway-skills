# Pricing, cost estimation, and the model catalogue

Live catalogue (always the authority):
**<https://tinker-docs.thinkingmachines.ai/tinker/models/>**
Console: <https://console.tinker.ai>

## Create the pricing file when you start

**Whenever you begin Tinker work in a project, write a `TINKER_PRICING.md` into
it:**

```bash
python <skill>/scripts/tinker_pricing.py init --out <project dir>
```

A price table next to the training script is one people read before launching a
550B RL run. One that lives in a browser tab is not, and the difference is a
four-figure surprise. The generated file carries the full catalogue, what each
operation meters, and the pre-launch checklist.

Regenerate it (`--force`) whenever prices or the model list change upstream, and
note in the project that the file is a **snapshot** — verify against the docs URL
before relying on a number.

## What is metered

| operation | charged on | when |
| --- | --- | --- |
| **PREFILL** | every prompt token you send | sampling *and* `forward_backward` |
| **PREFILL (cached)** | prompt tokens sharing a recent prefix — **80% off** | constantly in an agent loop: every turn resends the system prompt and the whole conversation so far |
| **SAMPLE** | every token generated | `sample()` |
| **TRAIN** | every token a gradient is computed on | `forward_backward` — in an RL `Datum` only completion positions carry weight |

Effective July 17: cached prefill got the 80% discount; prefill and sample rose
~50%, train ~10%.

The cache discount is why agentic workloads are cheaper than the naive
multiplication suggests, and why it is worth **not** perturbing the prefix of
your prompts between turns. A system prompt that includes a timestamp, or tool
schemas that reorder run to run, throws the discount away on every turn of every
episode.

## Prices (per 1M tokens, USD)

| MODEL | TINKER ID | CONTEXT | PREFILL | PREFILL (cached) | SAMPLE | TRAIN |
|---|---|---|---|---|---|---|
| Nemotron-3-Ultra-550B-A55B *(50% off)* | `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16` | 64K | $2.49 | $0.498 | $6.225 | $5.478 |
| Nemotron-3-Ultra-550B-A55B (256K) *(50% off)* | `…-BF16:peft:262144` | 256K | $3.32 | $0.664 | $8.30 | $9.96 |
| Nemotron-3-Super-120B-A12B *(50% off)* | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` | 64K | $0.57 | $0.114 | $1.44 | $1.276 |
| Nemotron-3-Super-120B-A12B (256K) *(50% off)* | `…-BF16:peft:262144` | 256K | $0.76 | $0.152 | $1.92 | $2.32 |
| Nemotron-3-Nano-30B-A3B *(50% off)* | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16` | 64K | $0.195 | $0.039 | $0.495 | $0.44 |
| Kimi-K2.6 | `moonshotai/Kimi-K2.6` | 32K | $2.205 | $0.441 | $5.49 | $4.84 |
| Kimi-K2.6 (128K) | `moonshotai/Kimi-K2.6:peft:131072` | 128K | $5.15 | $1.03 | $12.81 | $15.40 |
| Kimi-K2.5 *(retiring July 12)* | `moonshotai/Kimi-K2.5` | 32K | $2.205 | $0.441 | $5.49 | $4.84 |
| Kimi-K2.5 (128K) *(retiring July 12)* | `moonshotai/Kimi-K2.5:peft:131072` | 128K | $5.15 | $1.03 | $12.81 | $15.40 |
| Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` | 64K | $0.54 | $0.108 | $1.335 | $1.177 |
| Qwen3.6-27B | `Qwen/Qwen3.6-27B` | 64K | $1.86 | $0.372 | $5.595 | $4.103 |
| Qwen3.5-397B-A17B | `Qwen/Qwen3.5-397B-A17B` | 64K | $3.00 | $0.60 | $7.50 | $6.60 |
| Qwen3.5-397B-A17B (256K) | `Qwen/Qwen3.5-397B-A17B:peft:262144` | 256K | $4.00 | $0.80 | $10.00 | $12.00 |
| Qwen3.5-35B-A3B-Base | `Qwen/Qwen3.5-35B-A3B-Base` | 64K | $0.54 | $0.108 | $1.335 | $1.177 |
| Qwen3.5-9B | `Qwen/Qwen3.5-9B` | 64K | $0.66 | $0.132 | $1.995 | $1.463 |
| Qwen3.5-9B-Base | `Qwen/Qwen3.5-9B-Base` | 64K | $0.66 | $0.132 | $1.995 | $1.463 |
| Qwen3.5-4B | `Qwen/Qwen3.5-4B` | 64K | $0.33 | $0.066 | $1.005 | $0.737 |
| Qwen3-8B | `Qwen/Qwen3-8B` | 32K | $0.195 | $0.039 | $0.60 | $0.44 |
| GPT-OSS-120B | `openai/gpt-oss-120b` | 32K | $0.33 | $0.066 | $0.84 | $0.737 |
| GPT-OSS-120B (128K) | `openai/gpt-oss-120b:peft:131072` | 128K | $0.78 | $0.156 | $1.94 | $2.33 |
| GPT-OSS-20B | `openai/gpt-oss-20b` | 32K | $0.18 | $0.036 | $0.45 | $0.396 |
| DeepSeek-V3.1 | `deepseek-ai/DeepSeek-V3.1` | 32K | $1.695 | $0.339 | $4.215 | $3.718 |

22 models. Snapshot — verify against the docs URL.

Note the long-context variants: `openai/gpt-oss-120b:peft:131072` is a
**different model** from `openai/gpt-oss-120b` at ~2.4× the prefill rate and
~3.2× the train rate. Choosing the 128K variant "just in case" is a real cost
decision, not a safety margin.

## Estimating a run

```bash
# raw token workload
python scripts/tinker_pricing.py estimate --model Qwen/Qwen3-8B \
    --prefill-tokens 5e6 --sample-tokens 2e5 --train-tokens 1e6 --cache-hit-rate 0.8

# agentic RL
python scripts/tinker_pricing.py estimate-rl --model openai/gpt-oss-120b \
    --iterations 10 --tasks-per-iter 8 --group-size 8 \
    --turns 20 --avg-prompt 8000 --avg-completion 400
```

The arithmetic RL cost obeys:

```
episodes    = iterations × tasks_per_iter × group_size
generations = episodes × turns
prefill     = generations × avg_prompt        (+ one re-prefill per trained sequence)
sampled     = generations × avg_completion
trained     = sampled × train_fraction
```

Two ways people get this badly wrong:

1. **`avg_prompt` is the mean over the episode, not the first turn's prompt.**
   In an agent loop the prompt grows every turn — the mean is roughly *half the
   final context*. Using the opening prompt underestimates by several times.
2. **Every one of those four multipliers is a flag.** Doubling `group_size`
   because the gradient looked noisy doubles the bill. Do the multiplication
   before, not after.

## Keeping cost in the record

Log cost per run alongside reward. Two arms with the same score and a 4× cost
gap is a real result, and it is invisible unless it was recorded run by run. The
**research-observability** skill's report table sums it for you.

## Checks before a big launch

1. Model is served and not retiring — `get_server_capabilities()`.
2. Context window matches the model id you chose (see [setup.md](setup.md)).
3. `TINKER_PRICING.md` exists in the project and is current.
4. `estimate-rl` run, and the number written down where the team can see it.
5. Checkpoint TTLs decided, so a sweep does not leave hundreds of them
   accumulating (see [checkpoints.md](checkpoints.md)).
