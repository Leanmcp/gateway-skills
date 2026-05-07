#!/usr/bin/env python3
"""
tinker_sft.py — a runnable supervised fine-tuning template for Tinker.

Copy this into a project and replace `load_dataset()`. Everything else — the
Datum construction, the completion-only loss masking, the loss arithmetic, the
before/after evaluation, the checkpointing — is the part that is easy to get
subtly wrong, and getting it wrong produces a model that trains on its own
prompts and looks fine until you evaluate it.

    export TINKER_API_KEY="..."          # console.tinker.ai
    python tinker_sft.py --base-model Qwen/Qwen3-8B --epochs 8
    python tinker_sft.py --resume-from tinker://<run>/weights/epoch-4

Cost before you launch:
    python tinker_pricing.py estimate --model Qwen/Qwen3-8B \
        --prefill-tokens 2e6 --train-tokens 5e5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import tinker
from tinker import types


# --------------------------------------------------------------------------- #
# your data goes here
# --------------------------------------------------------------------------- #
def load_dataset(path: str | None) -> list[tuple[str, str]]:
    """Return [(prompt, completion), ...].

    Two conventions, and the choice matters at inference time:

      * RAW COMPLETION — prompt is literal text ("Q: ...\\nA:"). Simple, and you
        must prompt the trained model the exact same way. `.completions.create`
        on the OpenAI-compatible endpoint, never `.chat.completions`.
      * CHAT TEMPLATE — build the prompt with
        `tokenizer.apply_chat_template(messages, tokenize=False,
        add_generation_prompt=True)`. Required if you want the checkpoint to
        behave like a chat model or to be used with tools.

    Mixing them is the classic failure: SFT on raw text, then evaluate through a
    chat template the model never saw, and conclude the training did nothing.
    """
    if path:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        return [(r["prompt"], r["completion"]) for r in rows]
    return [
        ("Q: What is the capital of France?\nA:", " Paris"),
        ("Q: What is the capital of Japan?\nA:", " Tokyo"),
        ("Q: What is the capital of Italy?\nA:", " Rome"),
    ]


# --------------------------------------------------------------------------- #
# Datum construction — the part worth reading carefully
# --------------------------------------------------------------------------- #
def build_sft_datum(tokenizer, prompt: str, completion: str) -> types.Datum:
    """One (prompt, completion) pair as a training example.

    Next-token prediction alignment:
        full          = prompt_tokens + completion_tokens
        model_input   = full[:-1]      what the model sees
        target_tokens = full[1:]       what it must predict at each position
        weights       = 0 on prompt positions, 1 on completion positions

    The weights are the whole point. Target position i predicts full[i+1], which
    is a completion token when i + 1 >= len(prompt_tokens), i.e. i >= boundary.
    Off-by-one here trains the model to also generate your prompts — which
    quietly costs quality and is invisible in the loss curve.

    `add_special_tokens=False` on the completion: the prompt already carries BOS.
    """
    prompt_tokens = tokenizer.encode(prompt)                       # includes BOS
    completion_tokens = tokenizer.encode(completion, add_special_tokens=False)
    full = prompt_tokens + completion_tokens

    target_tokens = full[1:]
    boundary = len(prompt_tokens) - 1
    weights = [0.0 if i < boundary else 1.0 for i in range(len(target_tokens))]

    return types.Datum(
        model_input=types.ModelInput.from_ints(full[:-1]),
        loss_fn_inputs={"target_tokens": target_tokens, "weights": weights},
    )


def mean_loss(batch: list[types.Datum], result) -> float:
    """Mean next-token NLL over the WEIGHTED (completion) tokens.

    The cross_entropy backend returns per-token `logprobs` in loss_fn_outputs
    and its loss is sum(-logprobs × weights) — so dividing by sum(weights) gives
    a per-token number comparable across batches of different lengths. Reporting
    the raw sum instead makes long batches look worse than they are.
    """
    total_nll = total_weight = 0.0
    for datum, out in zip(batch, result.loss_fn_outputs):
        logprobs = out["logprobs"].to_numpy().astype(np.float64)
        weights = datum.loss_fn_inputs["weights"].to_numpy().astype(np.float64)
        total_nll += float(-(logprobs * weights).sum())
        total_weight += float(weights.sum())
    return total_nll / max(total_weight, 1.0)


def sample(sampling_client, tokenizer, prompt: str, max_tokens: int = 32) -> str:
    params = types.SamplingParams(max_tokens=max_tokens, temperature=0.0, stop=["\n"])
    resp = sampling_client.sample(
        prompt=types.ModelInput.from_ints(tokenizer.encode(prompt)),
        num_samples=1, sampling_params=params,
    ).result()
    return tokenizer.decode(resp.sequences[0].tokens)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default="Qwen/Qwen3-8B")
    ap.add_argument("--data", help="JSON file of [{prompt, completion}, ...]")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=0, help="0 = whole dataset")
    ap.add_argument("--lora-rank", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--save-every", type=int, default=0,
                    help="save resumable training state every N epochs (0 = off)")
    ap.add_argument("--resume-from", help="tinker://<run>/weights/<name>")
    ap.add_argument("--run-name", default="sft")
    args = ap.parse_args()

    if not os.getenv("TINKER_API_KEY"):
        sys.exit("TINKER_API_KEY is not set.\n"
                 "  export TINKER_API_KEY='...'   (console.tinker.ai)")

    service_client = tinker.ServiceClient()

    # Verify the model is actually served before spending anything. Retired
    # models fail here rather than three minutes into the loop.
    caps = service_client.get_server_capabilities()
    served = {m.model_name: m.max_context_length for m in caps.supported_models}
    if args.base_model not in served:
        sys.exit(f"{args.base_model} is not served. Available:\n  "
                 + "\n  ".join(sorted(served)))
    print(f"base model: {args.base_model}  (context {served[args.base_model]})")

    if args.resume_from:
        # Resuming needs the OPTIMIZER state too — a plain weights load restarts
        # Adam's moments at zero, which shows up as a loss spike at resume.
        training_client = service_client.create_training_client_from_state_with_optimizer(
            args.resume_from
        )
        print(f"resumed from {args.resume_from}")
    else:
        training_client = service_client.create_lora_training_client(
            base_model=args.base_model, rank=args.lora_rank
        )
    tokenizer = training_client.get_tokenizer()

    data = load_dataset(args.data)
    batch = [build_sft_datum(tokenizer, p, c) for p, c in data]
    print(f"{len(batch)} examples, "
          f"{sum(int(d.loss_fn_inputs['weights'].to_numpy().sum()) for d in batch)} "
          f"trained tokens per epoch")

    probe = data[0][0]
    before_sampler = training_client.save_weights_and_get_sampling_client(
        name=f"{args.run_name}-before")
    print(f"\nbefore: {probe!r} -> {sample(before_sampler, tokenizer, probe)!r}")

    for epoch in range(1, args.epochs + 1):
        size = args.batch_size or len(batch)
        losses = []
        for i in range(0, len(batch), size):
            chunk = batch[i:i + size]
            # forward_backward computes the forward pass AND accumulates
            # gradients; optim_step consumes them and updates the LoRA weights.
            # Calling forward_backward twice before an optim_step accumulates —
            # that is how you get a larger effective batch than fits at once.
            result = training_client.forward_backward(chunk, loss_fn="cross_entropy").result()
            training_client.optim_step(types.AdamParams(learning_rate=args.lr)).result()
            losses.append(mean_loss(chunk, result))
        print(f"  epoch {epoch:>3}  loss {float(np.mean(losses)):.4f}")
        if args.save_every and epoch % args.save_every == 0:
            resp = training_client.save_state(name=f"{args.run_name}-epoch-{epoch}").result()
            print(f"           state -> {resp.path}")

    after_sampler = training_client.save_weights_and_get_sampling_client(
        name=f"{args.run_name}-after")
    print(f"\nafter : {probe!r} -> {sample(after_sampler, tokenizer, probe)!r}")

    # save_weights_for_sampler gives the DOWNLOADABLE / servable checkpoint.
    # save_state gives the resumable one. They are different things and the
    # download endpoint only accepts the former.
    final = training_client.save_weights_for_sampler(name=f"{args.run_name}-final").result()
    print(f"\nsampler weights: {final.path}")
    print("  sample from it later:  "
          "service_client.create_sampling_client(base_model=..., model_path=<that path>)")
    print(f"  or over HTTP with the OpenAI SDK using that path as `model`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
