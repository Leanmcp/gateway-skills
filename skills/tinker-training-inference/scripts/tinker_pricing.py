#!/usr/bin/env python3
"""
tinker_pricing.py — Tinker model catalogue, price table, and run-cost estimator.

Two jobs:

  1. `init` — drop a `TINKER_PRICING.md` into a project. Do this whenever you
     start Tinker work in a new folder. A price table that lives next to the
     training script is a price table people actually read before launching a
     550B RL run; one that lives in a browser tab is not.

  2. `estimate` — tell you what a run will cost BEFORE you launch it. RL is
     where budgets die: cost scales as iterations × tasks × group_size × turns,
     and every one of those is a flag someone bumps without doing the
     multiplication. This does the multiplication.

Prices are per 1M tokens (USD), effective July 17. Three metered operations:

    PREFILL  every prompt token you send (sampling AND forward_backward)
    SAMPLE   every token the model generates
    TRAIN    every token a gradient is computed on

Cached prefill is 80% off — the discount applies when a prompt shares a prefix
with one you recently sent, which is exactly what an agent loop does (the system
prompt and the whole conversation so far are resent every turn).

    python tinker_pricing.py list
    python tinker_pricing.py list --size medium --context 64000
    python tinker_pricing.py init --out .
    python tinker_pricing.py show Qwen/Qwen3-8B
    python tinker_pricing.py estimate --model Qwen/Qwen3-8B \
        --prefill-tokens 5e6 --sample-tokens 2e5 --train-tokens 1e6
    python tinker_pricing.py estimate-rl --model openai/gpt-oss-120b \
        --iterations 10 --tasks-per-iter 8 --group-size 8 \
        --turns 20 --avg-prompt 8000 --avg-completion 400

ALWAYS re-check against the live catalogue before trusting a number here:
    https://tinker-docs.thinkingmachines.ai/tinker/models/
and, in code, `service_client.get_server_capabilities()` for what is actually
served right now (models retire; the Llama-3.x family already did).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

DOCS_URL = "https://tinker-docs.thinkingmachines.ai/tinker/models/"
CONSOLE_URL = "https://console.tinker.ai"
PRICING_EFFECTIVE = "July 17"

# Cached prefill is 80% off the listed prefill rate.
CACHE_DISCOUNT = 0.80


@dataclass
class Model:
    name: str
    tinker_id: str
    type: str
    arch: str
    size: str
    context: int
    prefill: float          # $ / 1M tokens
    prefill_cached: float
    sample: float
    train: float
    note: str = ""


# Effective July 17. Source: PRICING_AFTER_JULY_17.md; verify against DOCS_URL.
MODELS: list[Model] = [
    Model("Nemotron-3-Ultra-550B-A55B", "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16",
          "Hybrid", "MoE", "Large", 65536, 2.49, 0.498, 6.225, 5.478, "50% discount"),
    Model("Nemotron-3-Ultra-550B-A55B (256K)",
          "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16:peft:262144",
          "Hybrid", "MoE", "Large", 262144, 3.32, 0.664, 8.30, 9.96, "50% discount"),
    Model("Nemotron-3-Super-120B-A12B", "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
          "Hybrid", "MoE", "Large", 65536, 0.57, 0.114, 1.44, 1.276, "50% discount"),
    Model("Nemotron-3-Super-120B-A12B (256K)",
          "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16:peft:262144",
          "Hybrid", "MoE", "Large", 262144, 0.76, 0.152, 1.92, 2.32, "50% discount"),
    Model("Nemotron-3-Nano-30B-A3B", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
          "Hybrid", "MoE", "Medium", 65536, 0.195, 0.039, 0.495, 0.44, "50% discount"),
    Model("Kimi-K2.6", "moonshotai/Kimi-K2.6",
          "Reasoning + Vision", "MoE", "Large", 32768, 2.205, 0.441, 5.49, 4.84),
    Model("Kimi-K2.6 (128K)", "moonshotai/Kimi-K2.6:peft:131072",
          "Reasoning + Vision", "MoE", "Large", 131072, 5.15, 1.03, 12.81, 15.40),
    Model("Kimi-K2.5", "moonshotai/Kimi-K2.5",
          "Reasoning + Vision", "MoE", "Large", 32768, 2.205, 0.441, 5.49, 4.84,
          "RETIRING July 12"),
    Model("Kimi-K2.5 (128K)", "moonshotai/Kimi-K2.5:peft:131072",
          "Reasoning + Vision", "MoE", "Large", 131072, 5.15, 1.03, 12.81, 15.40,
          "RETIRING July 12"),
    Model("Qwen3.6-35B-A3B", "Qwen/Qwen3.6-35B-A3B",
          "Hybrid + Vision", "MoE", "Medium", 65536, 0.54, 0.108, 1.335, 1.177),
    Model("Qwen3.6-27B", "Qwen/Qwen3.6-27B",
          "Hybrid + Vision", "Dense", "Medium", 65536, 1.86, 0.372, 5.595, 4.103),
    Model("Qwen3.5-397B-A17B", "Qwen/Qwen3.5-397B-A17B",
          "Hybrid + Vision", "MoE", "Large", 65536, 3.00, 0.60, 7.50, 6.60),
    Model("Qwen3.5-397B-A17B (256K)", "Qwen/Qwen3.5-397B-A17B:peft:262144",
          "Hybrid + Vision", "MoE", "Large", 262144, 4.00, 0.80, 10.00, 12.00),
    Model("Qwen3.5-35B-A3B-Base", "Qwen/Qwen3.5-35B-A3B-Base",
          "Base", "MoE", "Medium", 65536, 0.54, 0.108, 1.335, 1.177),
    Model("Qwen3.5-9B", "Qwen/Qwen3.5-9B",
          "Hybrid + Vision", "Dense", "Small", 65536, 0.66, 0.132, 1.995, 1.463),
    Model("Qwen3.5-9B-Base", "Qwen/Qwen3.5-9B-Base",
          "Base", "Dense", "Small", 65536, 0.66, 0.132, 1.995, 1.463),
    Model("Qwen3.5-4B", "Qwen/Qwen3.5-4B",
          "Hybrid + Vision", "Dense", "Compact", 65536, 0.33, 0.066, 1.005, 0.737),
    Model("Qwen3-8B", "Qwen/Qwen3-8B",
          "Hybrid", "Dense", "Small", 32768, 0.195, 0.039, 0.60, 0.44),
    Model("GPT-OSS-120B", "openai/gpt-oss-120b",
          "Reasoning", "MoE", "Medium", 32768, 0.33, 0.066, 0.84, 0.737),
    Model("GPT-OSS-120B (128K)", "openai/gpt-oss-120b:peft:131072",
          "Reasoning", "MoE", "Medium", 131072, 0.78, 0.156, 1.94, 2.33),
    Model("GPT-OSS-20B", "openai/gpt-oss-20b",
          "Reasoning", "MoE", "Small", 32768, 0.18, 0.036, 0.45, 0.396),
    Model("DeepSeek-V3.1", "deepseek-ai/DeepSeek-V3.1",
          "Hybrid", "MoE", "Large", 32768, 1.695, 0.339, 4.215, 3.718),
]

BY_ID = {m.tinker_id: m for m in MODELS}


def find(model_id: str) -> Model:
    if model_id in BY_ID:
        return BY_ID[model_id]
    matches = [m for m in MODELS if model_id.lower() in m.tinker_id.lower()
               or model_id.lower() in m.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"Unknown model {model_id!r}. Run `list` to see the catalogue, "
                 f"or check {DOCS_URL} — it may be newer than this table.")
    sys.exit("Ambiguous: " + ", ".join(m.tinker_id for m in matches))


# --------------------------------------------------------------------------- #
# cost model
# --------------------------------------------------------------------------- #
def cost(model: Model, *, prefill_tokens: float = 0, sample_tokens: float = 0,
         train_tokens: float = 0, cache_hit_rate: float = 0.0) -> dict:
    """USD for a workload. `cache_hit_rate` is the fraction of prefill tokens
    served from cache (80% off) — in an agent loop this is high, because every
    turn resends the system prompt and the whole conversation so far."""
    cached = prefill_tokens * cache_hit_rate
    fresh = prefill_tokens - cached
    c_prefill = (fresh * model.prefill + cached * model.prefill_cached) / 1e6
    c_sample = sample_tokens * model.sample / 1e6
    c_train = train_tokens * model.train / 1e6
    return {"prefill": c_prefill, "sample": c_sample, "train": c_train,
            "total": c_prefill + c_sample + c_train}


def estimate_rl(model: Model, *, iterations: int, tasks_per_iter: int,
                group_size: int, turns: int, avg_prompt: int,
                avg_completion: int, cache_hit_rate: float = 0.8,
                train_fraction: float = 1.0) -> dict:
    """Cost of an agentic RL run.

    The multiplication people skip:
        episodes      = iterations × tasks_per_iter × group_size
        generations   = episodes × turns
        prefill       = generations × avg_prompt
        sampled       = generations × avg_completion
        trained       = sampled × train_fraction   (only completion tokens carry
                                                    a loss weight in an RL Datum)

    `avg_prompt` is the MEAN prompt over the episode, and in an agent loop the
    prompt grows every turn — so use roughly half the final context, not the
    first turn's prompt. Underestimating this is the single most common way an
    RL budget is blown.
    """
    episodes = iterations * tasks_per_iter * group_size
    generations = episodes * turns
    prefill_tokens = generations * avg_prompt
    sample_tokens = generations * avg_completion
    train_tokens = sample_tokens * train_fraction
    # forward_backward re-prefills each trained sequence once.
    train_prefill = train_tokens
    c = cost(model, prefill_tokens=prefill_tokens + train_prefill,
             sample_tokens=sample_tokens, train_tokens=train_tokens,
             cache_hit_rate=cache_hit_rate)
    return {**c, "episodes": episodes, "generations": generations,
            "prefill_tokens": prefill_tokens + train_prefill,
            "sample_tokens": sample_tokens, "train_tokens": train_tokens}


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def table_md(models: list[Model]) -> str:
    head = ("| MODEL | TINKER ID | TYPE | ARCH | SIZE | CONTEXT | PREFILL | "
            "PREFILL (cached) | SAMPLE | TRAIN |\n|---|---|---|---|---|---|---|---|---|---|")
    rows = []
    for m in models:
        name = m.name + (f" *({m.note})*" if m.note else "")
        ctx = f"{m.context // 1024}K"
        rows.append(f"| {name} | `{m.tinker_id}` | {m.type} | {m.arch} | {m.size} | "
                    f"{ctx} | ${m.prefill} | ${m.prefill_cached} | ${m.sample} | ${m.train} |")
    return head + "\n" + "\n".join(rows)


def pricing_doc() -> str:
    return f"""# Tinker model pricing and catalogue

> Generated by `tinker_pricing.py init`. Prices per 1M tokens (USD), effective
> {PRICING_EFFECTIVE}. **Verify against the live catalogue before relying on a
> number here — models retire and prices move:** {DOCS_URL}

## What is metered

| operation | charged on | when |
| --- | --- | --- |
| **PREFILL** | every prompt token you send | sampling *and* `forward_backward` |
| **PREFILL (cached)** | prompt tokens sharing a recent prefix | 80% off — an agent loop hits this constantly, since every turn resends the system prompt and the whole conversation |
| **SAMPLE** | every token generated | `sample()` / `sample_async()` |
| **TRAIN** | every token a gradient is computed on | `forward_backward` — in an RL `Datum` only the completion positions carry weight |

Recent change: 80% discount now applies to cached prefill; prefill and sample
rose ~50% and train ~10%.

## Catalogue

{table_md(MODELS)}

_{len(MODELS)} models._

## Before you launch

```bash
# what a run will cost, before spending it
python tinker_pricing.py estimate-rl --model <id> \\
    --iterations 10 --tasks-per-iter 8 --group-size 8 \\
    --turns 20 --avg-prompt 8000 --avg-completion 400
```

Two checks worth making every time:

1. **Context window.** The base id and its long-context variant are *different
   models* at different prices (`openai/gpt-oss-120b` is 32K;
   `openai/gpt-oss-120b:peft:131072` is 128K and ~2.4× the prefill rate).
   Confirm with `service_client.get_server_capabilities()` rather than assuming —
   a window configured above what is served makes every long episode die on a
   `BadRequestError` instead of ending cleanly.
2. **Model availability.** Retired models fail at client creation. The Llama-3.x
   family is already gone; Kimi-K2.5 is marked retiring above.

Console: {CONSOLE_URL} · Docs: {DOCS_URL}
"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="the catalogue")
    pl.add_argument("--size", help="Compact | Small | Medium | Large")
    pl.add_argument("--arch", help="Dense | MoE")
    pl.add_argument("--context", type=int, help="minimum context window")
    pl.add_argument("--json", action="store_true")

    ps = sub.add_parser("show", help="one model's row")
    ps.add_argument("model")

    pi = sub.add_parser("init", help="write TINKER_PRICING.md into a project")
    pi.add_argument("--out", default=".", help="project directory (default: cwd)")
    pi.add_argument("--force", action="store_true")

    pe = sub.add_parser("estimate", help="cost of a raw token workload")
    pe.add_argument("--model", required=True)
    pe.add_argument("--prefill-tokens", type=float, default=0)
    pe.add_argument("--sample-tokens", type=float, default=0)
    pe.add_argument("--train-tokens", type=float, default=0)
    pe.add_argument("--cache-hit-rate", type=float, default=0.0)

    pr = sub.add_parser("estimate-rl", help="cost of an agentic RL run")
    pr.add_argument("--model", required=True)
    pr.add_argument("--iterations", type=int, required=True)
    pr.add_argument("--tasks-per-iter", type=int, required=True)
    pr.add_argument("--group-size", type=int, default=8)
    pr.add_argument("--turns", type=int, default=20, help="generations per episode")
    pr.add_argument("--avg-prompt", type=int, required=True,
                    help="MEAN prompt tokens per generation (≈ half the final context)")
    pr.add_argument("--avg-completion", type=int, required=True)
    pr.add_argument("--cache-hit-rate", type=float, default=0.8)
    pr.add_argument("--train-fraction", type=float, default=1.0)

    args = p.parse_args()

    if args.cmd == "list":
        ms = MODELS
        if args.size:
            ms = [m for m in ms if m.size.lower() == args.size.lower()]
        if args.arch:
            ms = [m for m in ms if m.arch.lower() == args.arch.lower()]
        if args.context:
            ms = [m for m in ms if m.context >= args.context]
        if args.json:
            print(json.dumps([asdict(m) for m in ms], indent=2))
        else:
            print(table_md(ms))
            print(f"\n{len(ms)} models. Verify against {DOCS_URL}")
        return 0

    if args.cmd == "show":
        m = find(args.model)
        print(json.dumps(asdict(m), indent=2))
        return 0

    if args.cmd == "init":
        dest = Path(args.out) / "TINKER_PRICING.md"
        if dest.exists() and not args.force:
            print(f"{dest} already exists (use --force to overwrite).")
            return 1
        dest.write_text(pricing_doc(), encoding="utf-8")
        print(f"wrote {dest.resolve()}")
        print(f"Verify prices against {DOCS_URL} — this table is a snapshot.")
        return 0

    m = find(args.model)
    if args.cmd == "estimate":
        c = cost(m, prefill_tokens=args.prefill_tokens,
                 sample_tokens=args.sample_tokens, train_tokens=args.train_tokens,
                 cache_hit_rate=args.cache_hit_rate)
        print(f"model: {m.tinker_id}")
        for k in ("prefill", "sample", "train", "total"):
            print(f"  {k:<8} ${c[k]:>10,.2f}")
        return 0

    c = estimate_rl(m, iterations=args.iterations, tasks_per_iter=args.tasks_per_iter,
                    group_size=args.group_size, turns=args.turns,
                    avg_prompt=args.avg_prompt, avg_completion=args.avg_completion,
                    cache_hit_rate=args.cache_hit_rate,
                    train_fraction=args.train_fraction)
    print(f"model      : {m.tinker_id}  (context {m.context // 1024}K)")
    print(f"episodes   : {c['episodes']:,}   generations: {c['generations']:,}")
    print(f"prefill    : {c['prefill_tokens']:>14,.0f} tok   ${c['prefill']:>10,.2f}")
    print(f"sample     : {c['sample_tokens']:>14,.0f} tok   ${c['sample']:>10,.2f}")
    print(f"train      : {c['train_tokens']:>14,.0f} tok   ${c['train']:>10,.2f}")
    print(f"TOTAL      : {'':>18}   ${c['total']:>10,.2f}")
    print(f"\n(cache hit rate {args.cache_hit_rate:.0%}; avg_prompt is the MEAN "
          f"over the episode — if the prompt grows every turn, this should be "
          f"roughly half the final context, not the first turn's prompt.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
