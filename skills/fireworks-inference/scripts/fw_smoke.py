#!/usr/bin/env python3
"""
fw_smoke.py — prove a Fireworks route works, one layer at a time.

When a Fireworks call fails there are four things it could be: the key, the
endpoint, the model, or the client library. Testing them together tells you
nothing. This script isolates them by running the SAME request through three
transports against either route, so the first one that fails names the culprit.

    transports          routes
      raw   plain HTTP POST        direct   https://api.fireworks.ai/inference/v1
      sdk   openai SDK                      + FIREWORKS_API_KEY
      lite  litellm.completion     gateway  https://aigateway.leanmcp.com/v1/fireworks
                                            + LEANMCP_API_KEY

    python fw_smoke.py --model gpt-oss-20b                    # all transports, gateway
    python fw_smoke.py --model gpt-oss-20b --direct
    python fw_smoke.py --model gpt-oss-120b --transport lite --debug
    python fw_smoke.py --model <deployment-id> --account <your-account-id>   # a deployment
    python fw_smoke.py --model gpt-oss-20b --tools            # also probe function calling

How to read the result (this is the whole point):

    raw FAILS               -> endpoint, key, billing/credits, or model name
    raw OK, sdk/lite FAIL   -> the client library's routing, not the service.
                               Run with --debug to see the URL it actually hit
    all OK on direct,
      all FAIL on gateway   -> the gateway cannot reach that model. For a PRIVATE
                               deployment that is expected unless the gateway is
                               wired to your Fireworks account
    all OK                  -> the route is good; use it in the real runner
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DIRECT_BASE = "https://api.fireworks.ai/inference/v1"
GATEWAY_BASE = "https://aigateway.leanmcp.com/v1/fireworks"
FIREWORKS_ACCOUNT = "accounts/fireworks/models"


def load_env() -> None:
    """Load a repo-root .env if python-dotenv is available. Keys are commonly
    kept there rather than exported, and a missing key looks identical to a
    broken gateway if you do not check."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for parent in [Path.cwd(), *Path.cwd().resolve().parents]:
        env = parent / ".env"
        if env.is_file():
            load_dotenv(env)
            return


def resolve_model(name: str, account: str | None) -> str:
    """Bare slug -> the serverless path. A deployment id -> that deployment.
    Anything already containing '/' is used verbatim.

    Three id shapes exist and they are not interchangeable:
        accounts/fireworks/models/<slug>            serverless, shared
        accounts/<your-account>/deployments/<id>    dedicated, yours
        <slug>                                      shorthand this expands
    """
    if "/" in name:
        return name
    if account:
        return f"accounts/{account}/deployments/{name}"
    return f"{FIREWORKS_ACCOUNT}/{name}"


def tool_spec() -> list[dict]:
    return [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }]


def report(label: str, *, content, reasoning, finish, usage, tool_calls=None) -> bool:
    print(f"\n>>> [{label}] finish_reason: {finish}")
    if tool_calls:
        print(f">>> [{label}] tool calls: "
              + json.dumps(tool_calls, default=str)[:400])
    if content:
        print(f">>> [{label}] content: {str(content)[:400]}")
    elif reasoning:
        # Reasoning models emit chain-of-thought into a SEPARATE channel and
        # only then a final answer. With a small budget they spend everything
        # on reasoning and return content="" — which reads as a broken route
        # but is just an under-budgeted request.
        print(f">>> [{label}] no content, only reasoning_content: {str(reasoning)[:300]}")
    print(f">>> [{label}] usage: {usage}")
    if finish == "length":
        print(f">>> [{label}] NOTE: hit the token limit — raise --max-tokens.")
    ok = bool(content or reasoning or tool_calls)
    print(f">>> [{label}] {'SUCCESS' if ok else 'REACHED BUT EMPTY'}")
    return ok


def via_raw(base, key, model, args) -> bool:
    """Plain HTTP. No SDK in the middle — if this works, the service is fine."""
    import requests

    url = f"{base.rstrip('/')}/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": args.prompt}],
               "max_tokens": args.max_tokens, "temperature": args.temperature}
    if args.tools:
        payload["tools"] = tool_spec()
    print(f"\n[raw ] POST {url}\n[raw ] model {model}")
    try:
        resp = requests.post(url, headers={"Authorization": f"Bearer {key}",
                                           "Content-Type": "application/json"},
                             json=payload, timeout=args.timeout)
    except Exception as e:
        print(f">>> [raw ] REQUEST FAILED (network): {type(e).__name__}: {e}")
        return False
    print(f"[raw ] HTTP {resp.status_code}")
    try:
        data = resp.json()
    except ValueError:
        print(f">>> [raw ] non-JSON body: {resp.text[:500]}")
        return False
    if not resp.ok:
        print(f">>> [raw ] error body: {json.dumps(data)[:800]}")
        return False
    try:
        choice = data["choices"][0]
        msg = choice["message"]
    except (KeyError, IndexError):
        print(f">>> [raw ] 200 but unexpected shape: {json.dumps(data)[:500]}")
        return False
    return report("raw ", content=msg.get("content"),
                  reasoning=msg.get("reasoning_content"),
                  finish=choice.get("finish_reason"), usage=data.get("usage"),
                  tool_calls=msg.get("tool_calls"))


def via_sdk(base, key, model, args) -> bool:
    """The openai SDK. Fireworks and the gateway are both OpenAI-compatible, so
    the model id here is the BARE Fireworks path — no provider prefix."""
    from openai import OpenAI

    client = OpenAI(base_url=base, api_key=key, timeout=args.timeout)
    print(f"\n[sdk ] openai SDK -> {base}\n[sdk ] model {model}")
    kw = {}
    if args.tools:
        kw["tools"] = tool_spec()
    try:
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": args.prompt}],
            max_tokens=args.max_tokens, temperature=args.temperature, **kw)
    except Exception as e:
        print(f">>> [sdk ] FAILED: {type(e).__name__}: {e}")
        return False
    c = resp.choices[0]
    return report("sdk ", content=c.message.content,
                  reasoning=getattr(c.message, "reasoning_content", None),
                  finish=c.finish_reason, usage=resp.usage,
                  tool_calls=[t.model_dump() for t in (c.message.tool_calls or [])])


def via_litellm(base, key, model, args) -> bool:
    """litellm — the path most frameworks (tau2, LangChain, ...) actually take.

    Two things differ from the SDK route and both bite people:
      * the model id needs the `fireworks_ai/` PREFIX so litellm selects the
        provider; without it litellm guesses, usually wrongly;
      * litellm appends `/chat/completions` to whatever `api_base` you give it,
        so pass the base WITHOUT that suffix.
    """
    import litellm

    if args.debug:
        litellm._turn_on_debug()
    lite_model = model if model.startswith("fireworks_ai/") else f"fireworks_ai/{model}"
    print(f"\n[lite] litellm.completion -> {base}\n[lite] model {lite_model}")
    kw = {}
    if args.tools:
        kw["tools"] = tool_spec()
    try:
        resp = litellm.completion(
            model=lite_model, messages=[{"role": "user", "content": args.prompt}],
            max_tokens=args.max_tokens, temperature=args.temperature,
            api_base=base, api_key=key, timeout=args.timeout, **kw)
    except Exception as e:
        print(f">>> [lite] FAILED: {type(e).__name__}: {e}")
        print(">>> [lite] if raw/sdk worked, this is litellm routing — rerun with "
              "--debug to see the URL it actually hit.")
        return False
    c = resp.choices[0]
    return report("lite", content=c.message.content,
                  reasoning=getattr(c.message, "reasoning_content", None),
                  finish=getattr(c, "finish_reason", None), usage=getattr(resp, "usage", None),
                  tool_calls=[t.model_dump() for t in (c.message.tool_calls or [])])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="gpt-oss-20b",
                   help="slug, deployment id (with --account), or a full path")
    p.add_argument("--account", help="your Fireworks account id — makes --model a deployment id")
    p.add_argument("--direct", action="store_true",
                   help="hit Fireworks directly instead of the LeanMCP gateway")
    p.add_argument("--api-base", help="override the base URL entirely")
    p.add_argument("--transport", choices=["all", "raw", "sdk", "lite"], default="all")
    p.add_argument("--prompt", default="Reply with one short sentence confirming you are reachable.")
    p.add_argument("--max-tokens", type=int, default=1024,
                   help="keep high: reasoning models spend the budget on "
                        "reasoning_content before any final answer appears")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--tools", action="store_true", help="also probe function calling")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--debug", action="store_true", help="litellm verbose logging")
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
        print(f"ERROR: {keyname} is not set (shell env or a repo .env).")
        if not args.direct:
            print("  Gateway keys: https://app.leanmcp.com/api-keys "
                  "(top up first at https://app.leanmcp.com/billing)")
        return 1

    model = resolve_model(args.model, args.account)
    print("=" * 72)
    print(f"route    : {route}")
    print(f"api_base : {base}")
    print(f"key      : {keyname} = {key[:6]}…{key[-4:]}")
    print(f"model    : {model}")
    print("=" * 72)

    runners = {"raw": via_raw, "sdk": via_sdk, "lite": via_litellm}
    chosen = list(runners) if args.transport == "all" else [args.transport]
    results = {}
    for name in chosen:
        try:
            results[name] = runners[name](base, key, model, args)
        except ImportError as e:
            print(f"\n>>> [{name}] skipped — {e}")
            results[name] = None

    print("\n" + "=" * 72)
    for name, ok in results.items():
        print(f"  {name:<5} {'ok' if ok else 'SKIPPED' if ok is None else 'FAIL'}")
    tested = [v for v in results.values() if v is not None]
    if tested and all(tested):
        print(f"\nAll transports reached {model} via {route}.")
        if not args.direct:
            print("The request should now appear at https://app.leanmcp.com/observability")
        return 0
    if results.get("raw") is False:
        print("\nraw failed -> the endpoint, key, credits, or model name is the problem, "
              "not your client library.")
    elif results.get("raw") and not all(tested):
        print("\nraw worked but a client library did not -> it is a routing problem in "
              "that library (model prefix / api_base), not the service.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
