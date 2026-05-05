#!/usr/bin/env python3
"""
fw_hammer.py — load-test a Fireworks route before trusting it with a real sweep.

A single smoke test proves the route exists. It does not prove the route
survives twenty concurrent agent conversations, which is what a benchmark run
actually is. Failures that only appear under load are the expensive kind: they
show up an hour into a sweep, kill some cells and not others, and leave you with
results you cannot compare.

Three load shapes, because they stress different things:

  oneshot       N concurrent short calls. Maximises REQUESTS/sec. This is what
                surfaces credential and scope errors that a single call never
                shows (`Missing scopes: model.request`), plus rate limits.
  conversation  N concurrent multi-turn chats with growing history. Mimics real
                agent load: context and spend climb inside each worker, which is
                how a benchmark run behaves and how a one-shot test does not.
  output        N concurrent long-form generations. Maximises DECODED tokens —
                stresses generation throughput rather than request count, and is
                where a scale-to-zero deployment's real capacity shows up.

    python fw_hammer.py --mode oneshot --n 20 --concurrency 10
    python fw_hammer.py --mode conversation --n 8 --turns 6
    python fw_hammer.py --mode output --n 4 --concurrency 4 --max-tokens 4096
    python fw_hammer.py --mode oneshot --direct --model gpt-oss-120b
    python fw_hammer.py --model <deployment-id> --account <your-account-id>

Requests stream, and a heartbeat prints every few seconds:

    …   9s | done 0/20 | in-flight 8 | ~1423 tokens streamed

so a long run never looks frozen. A long generation can take minutes — no output
is slow generation, not a hang. A bare `^C ... KeyboardInterrupt` traceback only
ever means you pressed Ctrl-C.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DIRECT_BASE = "https://api.fireworks.ai/inference/v1"
GATEWAY_BASE = "https://aigateway.leanmcp.com/v1/fireworks"

TOPICS = [
    "the history and future of deep-sea exploration",
    "how cities might be redesigned around walking instead of cars",
    "the physics and philosophy of time",
    "the economics of the global coffee trade",
    "the evolution of human language",
    "the geopolitics of fresh water",
    "the biology of sleep and dreaming",
    "the mathematics hidden in music",
    "the history of cartography and how maps shape thought",
    "the secret life of fungi and underground networks",
    "the history of cryptography and secret-keeping",
    "the philosophy and science of consciousness",
]
STYLES = ["a rigorous academic essay with clear sections",
          "an immersive narrative essay that tells stories",
          "a skeptical analysis that weighs competing claims",
          "a practical guide aimed at a curious beginner"]


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for parent in [Path.cwd(), *Path.cwd().resolve().parents]:
        if (parent / ".env").is_file():
            load_dotenv(parent / ".env")
            return


class Progress:
    """Shared counters + a heartbeat, so a slow run is visibly alive."""

    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self.inflight = 0
        self.chunks = 0
        self.lock = threading.Lock()
        self.t0 = time.time()
        self.stop = threading.Event()

    def start(self, every: float = 3.0) -> None:
        def beat():
            while not self.stop.wait(every):
                with self.lock:
                    print(f"… {time.time() - self.t0:5.0f}s | done {self.done}/{self.total}"
                          f" | in-flight {self.inflight} | ~{self.chunks} chunks streamed",
                          flush=True)
        threading.Thread(target=beat, daemon=True).start()


def one_call(model, base, key, messages, max_tokens, temperature, timeout,
             prog: Progress, tools=None) -> dict:
    """One streamed completion. Returns a result record; never raises."""
    import litellm

    with prog.lock:
        prog.inflight += 1
    t0 = time.time()
    text_parts, n_chunks, err = [], 0, None
    try:
        stream = litellm.completion(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature, api_base=base, api_key=key,
            timeout=timeout, stream=True, tools=tools)
        for chunk in stream:
            n_chunks += 1
            with prog.lock:
                prog.chunks += 1
            try:
                delta = chunk.choices[0].delta
                piece = getattr(delta, "content", None) or getattr(
                    delta, "reasoning_content", None)
                if piece:
                    text_parts.append(piece)
            except (AttributeError, IndexError):
                continue
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    finally:
        with prog.lock:
            prog.inflight -= 1
            prog.done += 1

    text = "".join(text_parts)
    return {"ok": err is None and bool(text), "error": err, "text_len": len(text),
            "words": len(text.split()), "chunks": n_chunks,
            "seconds": round(time.time() - t0, 2)}


def build_messages(mode: str, i: int, rng: random.Random, min_words: int) -> list[dict]:
    if mode == "oneshot":
        return [{"role": "user", "content": f"Reply with exactly: OK {i}"}]
    if mode == "output":
        return [{"role": "user",
                 "content": f"Write {rng.choice(STYLES)} of at least {min_words} words "
                            f"on {rng.choice(TOPICS)}. Do not stop early."}]
    return [{"role": "user", "content": f"Let's discuss {rng.choice(TOPICS)}. "
                                        f"Start with one paragraph."}]


def run_conversation(model, base, key, args, i, rng, prog) -> dict:
    """A multi-turn chat with growing history — the shape a real agent run has."""
    messages = build_messages("conversation", i, rng, args.min_words)
    total = {"ok": True, "error": None, "text_len": 0, "words": 0,
             "chunks": 0, "seconds": 0.0}
    for turn in range(args.turns):
        r = one_call(model, base, key, messages, args.max_tokens, args.temperature,
                     args.timeout, prog)
        for k in ("text_len", "words", "chunks", "seconds"):
            total[k] += r[k]
        if not r["ok"]:
            return {**total, "ok": False, "error": r["error"]}
        messages.append({"role": "assistant", "content": "…"})
        messages.append({"role": "user", "content":
                         f"Good. Now expand on point {turn + 1} in more detail."})
    return total


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", choices=["oneshot", "conversation", "output"],
                   default="oneshot")
    p.add_argument("--model", default="gpt-oss-20b")
    p.add_argument("--account", help="Fireworks account id — makes --model a deployment id")
    p.add_argument("--direct", action="store_true", help="Fireworks directly, not the gateway")
    p.add_argument("--api-base")
    p.add_argument("--n", type=int, default=20, help="total requests (or conversations)")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--turns", type=int, default=5, help="conversation mode: turns per chat")
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--min-words", type=int, default=1200, help="output mode target length")
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--timeout", type=float, default=900.0)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    load_env()
    if args.direct:
        base = args.api_base or DIRECT_BASE
        key, keyname = os.getenv("FIREWORKS_API_KEY"), "FIREWORKS_API_KEY"
        route = "DIRECT Fireworks"
    else:
        base = args.api_base or GATEWAY_BASE
        key, keyname = os.getenv("LEANMCP_API_KEY"), "LEANMCP_API_KEY"
        route = "LeanMCP gateway"
    if not key:
        sys.exit(f"ERROR: {keyname} is not set.")

    model = args.model
    if "/" not in model:
        model = (f"accounts/{args.account}/deployments/{model}" if args.account
                 else f"accounts/fireworks/models/{model}")
    if not model.startswith("fireworks_ai/"):
        model = f"fireworks_ai/{model}"      # litellm needs the provider prefix

    print("=" * 72)
    print(f"mode {args.mode} · route {route}\napi_base {base}\nmodel {model}")
    print(f"n={args.n} concurrency={args.concurrency} max_tokens={args.max_tokens}"
          + (f" turns={args.turns}" if args.mode == "conversation" else ""))
    print("=" * 72)

    prog = Progress(args.n)
    prog.start()
    t0 = time.time()
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {}
            for i in range(args.n):
                rng = random.Random(args.seed + i)
                if args.mode == "conversation":
                    fut = pool.submit(run_conversation, model, base, key, args, i, rng, prog)
                else:
                    msgs = build_messages(args.mode, i, rng, args.min_words)
                    fut = pool.submit(one_call, model, base, key, msgs, args.max_tokens,
                                      args.temperature, args.timeout, prog)
                futures[fut] = i
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                mark = "✓" if r["ok"] else "✗"
                print(f"  {mark} #{futures[fut]:<3} {r['seconds']:>6.1f}s "
                      f"{r['words']:>7} words {r['chunks']:>5} chunks"
                      + (f"  {r['error']}" if r["error"] else ""), flush=True)
    except KeyboardInterrupt:
        print("\n(interrupted by you — partial results below)")
    finally:
        prog.stop.set()

    elapsed = time.time() - t0
    ok = [r for r in results if r["ok"]]
    bad = [r for r in results if not r["ok"]]
    words = sum(r["words"] for r in results)
    print("\n" + "=" * 72)
    print(f"  {len(ok)}/{len(results)} succeeded in {elapsed:.1f}s")
    print(f"  {words:,} words generated  (~{words / max(elapsed, 1e-9):.0f} words/s aggregate)")
    if ok:
        lat = sorted(r["seconds"] for r in ok)
        print(f"  latency  p50 {lat[len(lat) // 2]:.1f}s   "
              f"p95 {lat[min(len(lat) - 1, int(0.95 * len(lat)))]:.1f}s   "
              f"max {lat[-1]:.1f}s")
    if bad:
        print(f"\n  {len(bad)} FAILURES:")
        for msg, count in Counter(r["error"] for r in bad).most_common():
            print(f"    ×{count}  {msg}")
        print("\n  'Missing scopes: model.request' -> the route's backend credential "
              "breaks under concurrency, not your code.\n"
              "  429 / rate limit -> lower --concurrency, or the account needs a "
              "higher limit.\n"
              "  Empty results only at high concurrency -> a dedicated deployment "
              "is under-replicated for this load.")
        return 1
    print("\n  Route held up under this load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
