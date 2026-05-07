#!/usr/bin/env python3
"""
tinker_rl.py — a runnable RL / RFT template for Tinker (group-relative advantages).

Copy this into a project and replace `TASKS`, `render_prompt()` and `reward()`.
The rest — sampling a group per task, computing a within-group baseline, aligning
old-policy logprobs to the right token positions, building the RL Datum, and
stepping — is the machinery, and every piece of it has a failure mode that
produces a run that trains happily on a wrong gradient.

The loop, once per iteration:

    save weights -> sampling client   (the OLD policy: rollouts must come from
                                       the same weights whose logprobs you store)
    sample a group of G rollouts per task
    score each rollout                (your reward function)
    advantage = reward - group mean   (GRPO-style baseline, no value network)
    build Datum with old logprobs + per-token advantages
    forward_backward(loss_fn="importance_sampling") -> optim_step

    export TINKER_API_KEY="..."
    python tinker_rl.py --base-model Qwen/Qwen3-8B --iterations 12 --group-size 8

Cost before you launch — RL is where budgets die:
    python tinker_pricing.py estimate-rl --model Qwen/Qwen3-8B \
        --iterations 12 --tasks-per-iter 6 --group-size 8 \
        --turns 1 --avg-prompt 64 --avg-completion 8
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import tinker
from tinker import types


# --------------------------------------------------------------------------- #
# your task goes here
# --------------------------------------------------------------------------- #
TASKS = [(2, 2), (3, 5), (7, 1), (4, 4), (6, 3), (1, 9)]


def render_prompt(task) -> str:
    a, b = task
    return f"{a} + {b} ="


def reward(task, completion_text: str) -> float:
    """Score one rollout in [0, 1].

    Shape it if you can. A reward that is 0 or 1 and almost always 0 gives you
    groups where every rollout ties, the advantage is 0 for all of them, and the
    iteration contributes nothing but cost. Partial credit is what keeps the
    gradient alive early in training.
    """
    a, b = task
    first = (completion_text.strip().split() or [""])[0]
    return 1.0 if first == str(a + b) else 0.0


# --------------------------------------------------------------------------- #
# RL Datum: the same next-token alignment as SFT, plus old logprobs + advantages
# --------------------------------------------------------------------------- #
def build_rl_datum(prompt_tokens: list[int], completion_tokens: list[int],
                   completion_logprobs: list[float], advantage: float) -> types.Datum:
    """One rollout as a training example for `importance_sampling`.

    Only completion positions get weight 1, the advantage, and an old logprob.
    The alignment: target position i predicts full[i+1], so the j-th completion
    token lands at i = boundary + j where boundary = len(prompt_tokens) - 1.
    Get this wrong and you apply the advantage to prompt positions — the loss
    still goes down, and the policy learns nothing you wanted.

    The stored `logprobs` must come from the policy that GENERATED the rollout.
    That is why the loop saves weights and samples from the resulting client
    rather than reusing a sampler from a previous iteration: importance sampling
    corrects for the ratio between the current and old policy, and a stale
    denominator silently biases every update.
    """
    full = prompt_tokens + completion_tokens
    target_tokens = full[1:]
    boundary = len(prompt_tokens) - 1

    weights = [0.0] * len(target_tokens)
    advantages = [0.0] * len(target_tokens)
    old_logprobs = [0.0] * len(target_tokens)
    for j, lp in enumerate(completion_logprobs):
        i = boundary + j
        if i >= len(target_tokens):
            break
        weights[i] = 1.0
        advantages[i] = advantage
        old_logprobs[i] = lp

    return types.Datum(
        model_input=types.ModelInput.from_ints(full[:-1]),
        loss_fn_inputs={"target_tokens": target_tokens, "weights": weights,
                        "logprobs": old_logprobs, "advantages": advantages},
    )


def completion_logprobs(sampling_client, seq, prompt_tokens: list[int]) -> list[float]:
    """Old-policy logprobs for the sampled completion tokens.

    The sampler usually returns them on the sequence. When it does not (or when
    you assembled the token list yourself across several samples), recompute
    over prompt+completion — `all_lp[k]` is the logprob of `full[k]`, so the
    completion starts at `len(prompt_tokens)`.
    """
    if getattr(seq, "logprobs", None) is not None:
        return [float(x) for x in seq.logprobs]
    full = prompt_tokens + list(seq.tokens)
    all_lp = sampling_client.compute_logprobs(types.ModelInput.from_ints(full)).result()
    return [float(x) for x in all_lp[len(prompt_tokens):]]


# --------------------------------------------------------------------------- #
def rollout_and_step(training_client, tokenizer, *, group_size: int, label: str,
                     lr: float, temperature: float, max_tokens: int,
                     stop: list[str], do_optim: bool = True) -> tuple[float, float, int]:
    """One iteration: rollouts -> rewards -> advantages -> one policy-gradient step."""
    # Rollouts MUST come from the current weights — hence save-then-sample.
    sampling_client = training_client.save_weights_and_get_sampling_client(name=label)
    params = types.SamplingParams(max_tokens=max_tokens, temperature=temperature,
                                  stop=stop)

    rl_data: list[types.Datum] = []
    all_rewards: list[float] = []
    n_tied = 0

    for task in TASKS:
        prompt_tokens = tokenizer.encode(render_prompt(task))
        resp = sampling_client.sample(
            prompt=types.ModelInput.from_ints(prompt_tokens),
            num_samples=group_size, sampling_params=params,
        ).result()

        rewards = [reward(task, tokenizer.decode(s.tokens)) for s in resp.sequences]
        all_rewards.extend(rewards)

        # Group-relative advantage: reward minus the group mean. No value
        # network, low variance, and it needs the group to actually differ —
        # if every rollout ties, all advantages are 0 and this task contributes
        # nothing this iteration. Count those: a high tie rate means the reward
        # is too coarse or the temperature too low to explore.
        baseline = float(np.mean(rewards))
        if float(np.std(rewards)) == 0.0:
            n_tied += 1
            continue
        for seq, r in zip(resp.sequences, rewards):
            if not seq.tokens:
                continue
            rl_data.append(build_rl_datum(
                prompt_tokens, list(seq.tokens),
                completion_logprobs(sampling_client, seq, prompt_tokens),
                r - baseline,
            ))

    mean_reward = float(np.mean(all_rewards)) if all_rewards else 0.0
    loss = float("nan")
    if rl_data:
        result = training_client.forward_backward(
            rl_data, loss_fn="importance_sampling").result()
        loss = float(result.metrics.get("loss:sum", float("nan")))
        if do_optim:
            training_client.optim_step(types.AdamParams(learning_rate=lr)).result()
    return mean_reward, loss, n_tied


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default="Qwen/Qwen3-8B")
    ap.add_argument("--iterations", type=int, default=12)
    ap.add_argument("--group-size", type=int, default=8, help="rollouts per task")
    ap.add_argument("--lora-rank", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="rollout temperature — this is your exploration knob")
    ap.add_argument("--max-tokens", type=int, default=16)
    ap.add_argument("--stop", nargs="*", default=["\n"])
    ap.add_argument("--loss-fn", default="importance_sampling",
                    choices=["importance_sampling", "ppo", "cispo", "dro"])
    ap.add_argument("--save-every", type=int, default=0)
    ap.add_argument("--resume-from")
    ap.add_argument("--run-name", default="rl")
    args = ap.parse_args()

    if not os.getenv("TINKER_API_KEY"):
        sys.exit("TINKER_API_KEY is not set (console.tinker.ai)")

    service_client = tinker.ServiceClient()
    if args.resume_from:
        training_client = service_client.create_training_client_from_state_with_optimizer(
            args.resume_from)
    else:
        training_client = service_client.create_lora_training_client(
            base_model=args.base_model, rank=args.lora_rank)
    tokenizer = training_client.get_tokenizer()

    print(f"RL: {args.base_model}  rank={args.lora_rank} lr={args.lr} "
          f"group={args.group_size} T={args.temperature}")
    print(f"    {len(TASKS)} tasks × {args.group_size} rollouts × "
          f"{args.iterations} iterations = "
          f"{len(TASKS) * args.group_size * args.iterations} episodes\n")

    for it in range(args.iterations):
        mean_reward, loss, n_tied = rollout_and_step(
            training_client, tokenizer, group_size=args.group_size,
            label=f"{args.run_name}-iter-{it}", lr=args.lr,
            temperature=args.temperature, max_tokens=args.max_tokens,
            stop=args.stop)
        tie_note = f"   ({n_tied}/{len(TASKS)} tasks tied — no gradient)" if n_tied else ""
        print(f"  iter {it:>3}  reward {mean_reward:.3f}  loss {loss:.4f}{tie_note}")
        if args.save_every and (it + 1) % args.save_every == 0:
            resp = training_client.save_state(name=f"{args.run_name}-iter-{it}").result()
            print(f"            state -> {resp.path}")

    final = training_client.save_weights_for_sampler(name=f"{args.run_name}-final").result()
    print(f"\nsampler weights: {final.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
