# Tinker model pricing and catalogue

> Snapshot. Prices per 1M tokens (USD), effective July 17.
> **Verify against the live catalogue before relying on a number here — models
> retire and prices move:** <https://tinker-docs.thinkingmachines.ai/tinker/models/>
>
> Regenerate with: `python tinker_pricing.py init --out . --force`

## What is metered

| operation | charged on | when |
| --- | --- | --- |
| **PREFILL** | every prompt token you send | sampling *and* `forward_backward` |
| **PREFILL (cached)** | prompt tokens sharing a recent prefix | 80% off — an agent loop hits this constantly, since every turn resends the system prompt and the whole conversation |
| **SAMPLE** | every token generated | `sample()` / `sample_async()` |
| **TRAIN** | every token a gradient is computed on | `forward_backward` — in an RL `Datum` only the completion positions carry weight |

Recent change: 80% discount now applies to cached prefill; prefill and sample
rose ~50% and train ~10%.

Keep your prompt prefix stable between turns — a timestamp in the system prompt
or tool schemas that reorder run to run throws the cache discount away on every
turn of every episode.

## Catalogue

| MODEL | TINKER ID | TYPE | ARCH | SIZE | CONTEXT | PREFILL | PREFILL (cached) | SAMPLE | TRAIN |
|---|---|---|---|---|---|---|---|---|---|
| Nemotron-3-Ultra-550B-A55B *(50% discount)* | `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16` | Hybrid | MoE | Large | 64K | $2.49 | $0.498 | $6.225 | $5.478 |
| Nemotron-3-Ultra-550B-A55B (256K) *(50% discount)* | `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16:peft:262144` | Hybrid | MoE | Large | 256K | $3.32 | $0.664 | $8.3 | $9.96 |
| Nemotron-3-Super-120B-A12B *(50% discount)* | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` | Hybrid | MoE | Large | 64K | $0.57 | $0.114 | $1.44 | $1.276 |
| Nemotron-3-Super-120B-A12B (256K) *(50% discount)* | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16:peft:262144` | Hybrid | MoE | Large | 256K | $0.76 | $0.152 | $1.92 | $2.32 |
| Nemotron-3-Nano-30B-A3B *(50% discount)* | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16` | Hybrid | MoE | Medium | 64K | $0.195 | $0.039 | $0.495 | $0.44 |
| Kimi-K2.6 | `moonshotai/Kimi-K2.6` | Reasoning + Vision | MoE | Large | 32K | $2.205 | $0.441 | $5.49 | $4.84 |
| Kimi-K2.6 (128K) | `moonshotai/Kimi-K2.6:peft:131072` | Reasoning + Vision | MoE | Large | 128K | $5.15 | $1.03 | $12.81 | $15.4 |
| Kimi-K2.5 *(RETIRING July 12)* | `moonshotai/Kimi-K2.5` | Reasoning + Vision | MoE | Large | 32K | $2.205 | $0.441 | $5.49 | $4.84 |
| Kimi-K2.5 (128K) *(RETIRING July 12)* | `moonshotai/Kimi-K2.5:peft:131072` | Reasoning + Vision | MoE | Large | 128K | $5.15 | $1.03 | $12.81 | $15.4 |
| Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` | Hybrid + Vision | MoE | Medium | 64K | $0.54 | $0.108 | $1.335 | $1.177 |
| Qwen3.6-27B | `Qwen/Qwen3.6-27B` | Hybrid + Vision | Dense | Medium | 64K | $1.86 | $0.372 | $5.595 | $4.103 |
| Qwen3.5-397B-A17B | `Qwen/Qwen3.5-397B-A17B` | Hybrid + Vision | MoE | Large | 64K | $3.0 | $0.6 | $7.5 | $6.6 |
| Qwen3.5-397B-A17B (256K) | `Qwen/Qwen3.5-397B-A17B:peft:262144` | Hybrid + Vision | MoE | Large | 256K | $4.0 | $0.8 | $10.0 | $12.0 |
| Qwen3.5-35B-A3B-Base | `Qwen/Qwen3.5-35B-A3B-Base` | Base | MoE | Medium | 64K | $0.54 | $0.108 | $1.335 | $1.177 |
| Qwen3.5-9B | `Qwen/Qwen3.5-9B` | Hybrid + Vision | Dense | Small | 64K | $0.66 | $0.132 | $1.995 | $1.463 |
| Qwen3.5-9B-Base | `Qwen/Qwen3.5-9B-Base` | Base | Dense | Small | 64K | $0.66 | $0.132 | $1.995 | $1.463 |
| Qwen3.5-4B | `Qwen/Qwen3.5-4B` | Hybrid + Vision | Dense | Compact | 64K | $0.33 | $0.066 | $1.005 | $0.737 |
| Qwen3-8B | `Qwen/Qwen3-8B` | Hybrid | Dense | Small | 32K | $0.195 | $0.039 | $0.6 | $0.44 |
| GPT-OSS-120B | `openai/gpt-oss-120b` | Reasoning | MoE | Medium | 32K | $0.33 | $0.066 | $0.84 | $0.737 |
| GPT-OSS-120B (128K) | `openai/gpt-oss-120b:peft:131072` | Reasoning | MoE | Medium | 128K | $0.78 | $0.156 | $1.94 | $2.33 |
| GPT-OSS-20B | `openai/gpt-oss-20b` | Reasoning | MoE | Small | 32K | $0.18 | $0.036 | $0.45 | $0.396 |
| DeepSeek-V3.1 | `deepseek-ai/DeepSeek-V3.1` | Hybrid | MoE | Large | 32K | $1.695 | $0.339 | $4.215 | $3.718 |

_22 models._

## Before you launch

```bash
# what a run will cost, before spending it
python tinker_pricing.py estimate-rl --model <id> \
    --iterations 10 --tasks-per-iter 8 --group-size 8 \
    --turns 20 --avg-prompt 8000 --avg-completion 400
```

`--avg-prompt` is the **mean** prompt across the episode. In an agent loop the
prompt grows every turn, so use roughly half the final context — using the first
turn's prompt underestimates by several times.

Two checks worth making every time:

1. **Context window.** The base id and its long-context variant are *different
   models* at different prices (`openai/gpt-oss-120b` is 32K;
   `openai/gpt-oss-120b:peft:131072` is 128K at ~2.4× the prefill rate). Confirm
   with `service_client.get_server_capabilities()` rather than assuming — a
   window configured above what is served makes every long episode die on a
   `BadRequestError` instead of ending cleanly, and it kills different episodes
   in different arms.
2. **Model availability.** Retired models fail at client creation. The Llama-3.x
   family is already gone; Kimi-K2.5 is marked retiring above.

Console: <https://console.tinker.ai> · Docs: <https://tinker-docs.thinkingmachines.ai/tinker/models/>
