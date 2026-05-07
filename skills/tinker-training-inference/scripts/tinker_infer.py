#!/usr/bin/env python3
"""
tinker_infer.py — inference against a Tinker checkpoint, both ways.

On Tinker the LoRA weights live SERVER-SIDE. Every `save_weights_for_sampler(name)`
created a persistent `tinker://.../sampler_weights/<name>` path, and that path is
all you need to run the model again — the files you downloaded with
`tinker checkpoint download` are only for taking the model *elsewhere*
(Fireworks, Ollama, a local merge).

Two routes to the same checkpoint:

  --sdk    tinker SamplingClient. Token-level: you hold the prompt and completion
           token ids, so this is what you want inside a training loop or when you
           need exact accounting.
  --http   Tinker's OpenAI-compatible endpoint with the plain `openai` SDK. No
           tokenizer, no Tinker client — just a base_url override and the
           tinker:// path as the model name. Best for poking at a checkpoint.

    export TINKER_API_KEY="..."
    python tinker_infer.py --model tinker://<run>/sampler_weights/final \
        --base-model Qwen/Qwen3-8B --prompt "Q: What is the capital of France?\nA:"
    python tinker_infer.py --http --model tinker://... --chat --prompt "hello"

ONLY `sampler_weights/...` paths work for inference. A `weights/...` path is
training state (optimizer included) for resuming — the sampling and download
endpoints both reject it.
"""
from __future__ import annotations

import argparse
import os
import sys

BASE_URL = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"


def via_sdk(args) -> int:
    import tinker
    from tinker import types

    service_client = tinker.ServiceClient()
    # base_model is still required: the server needs to know which base to
    # attach the adapter to.
    sampling_client = service_client.create_sampling_client(
        base_model=args.base_model, model_path=args.model)
    tokenizer = sampling_client.get_tokenizer()

    prompt = args.prompt
    if args.chat:
        # Only if the checkpoint was TRAINED through a chat template. Wrapping a
        # raw-completion checkpoint in a template it never saw gives noticeably
        # worse answers and looks like the training failed.
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": args.prompt}],
            tokenize=False, add_generation_prompt=True)

    params = types.SamplingParams(max_tokens=args.max_tokens,
                                  temperature=args.temperature,
                                  stop=args.stop or None,
                                  seed=args.seed)
    resp = sampling_client.sample(
        prompt=types.ModelInput.from_ints(tokenizer.encode(prompt)),
        num_samples=args.n, sampling_params=params).result()

    for i, seq in enumerate(resp.sequences):
        text = tokenizer.decode(seq.tokens)
        finish = getattr(seq, "finish_reason", None) or getattr(seq, "stop_reason", None)
        print(f"\n--- sample {i}  ({len(seq.tokens)} tok, finish={finish}) ---")
        print(text)
    return 0


def via_http(args) -> int:
    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL, api_key=os.environ["TINKER_API_KEY"])
    if args.chat:
        resp = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": args.prompt}],
            max_tokens=args.max_tokens, temperature=args.temperature, n=args.n)
        for c in resp.choices:
            print(f"\n--- choice {c.index} (finish={c.finish_reason}) ---")
            print(c.message.content)
    else:
        resp = client.completions.create(
            model=args.model, prompt=args.prompt, max_tokens=args.max_tokens,
            temperature=args.temperature, n=args.n, stop=args.stop or None)
        for c in resp.choices:
            print(f"\n--- choice {c.index} (finish={c.finish_reason}) ---")
            print(c.text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="tinker://<run>/sampler_weights/<name>")
    ap.add_argument("--base-model", default="Qwen/Qwen3-8B",
                    help="the base the LoRA was trained on (SDK route only)")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--http", action="store_true",
                    help="use the OpenAI-compatible endpoint instead of the SDK")
    ap.add_argument("--chat", action="store_true",
                    help="wrap in a chat template — only for chat-trained checkpoints")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--stop", nargs="*", default=[])
    args = ap.parse_args()

    if not os.getenv("TINKER_API_KEY"):
        sys.exit("TINKER_API_KEY is not set (console.tinker.ai)")
    if "/sampler_weights/" not in args.model and args.model.startswith("tinker://"):
        print("WARN: that looks like a training-state path (weights/...). "
              "Inference needs a sampler_weights/... checkpoint.", file=sys.stderr)

    return via_http(args) if args.http else via_sdk(args)


if __name__ == "__main__":
    raise SystemExit(main())
