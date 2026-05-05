#!/usr/bin/env python3
"""
fw_ready.py — is a (possibly cold) Fireworks model actually serving yet?

Dedicated deployments scale to zero. The first request after idle does not fail
— it returns HTTP 200 with `content: null` while the replica spins up. Frameworks
downstream then crash on the None with something unrelated-looking, e.g.

    TypeError: expected string or bytes-like object, got 'NoneType'

so a sweep launched into a cold deployment dies on its first task and looks like
a code bug. Call this before a sweep: the ping both *checks* readiness and
*triggers* the scale-up, and `--wait` blocks until the model answers.

    python fw_ready.py --model <deployment-id> --account <your-account-id>
    python fw_ready.py --model gpt-oss-20b --direct
    python fw_ready.py --model <deployment-id> --account <acct> --wait 600
    python fw_ready.py --api-base https://aigateway.leanmcp.com/v1/fireworks \
                       --model accounts/fireworks/models/gpt-oss-20b

Exit codes (stdout is one status word; detail goes to stderr):
    0  READY   non-empty content (or reasoning_content) came back
    1  EMPTY   HTTP 200 but nothing generated — still warming up
    2  HTTP    the endpoint returned an error status
    3  ERR     connection / timeout / TLS / usage error
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DIRECT_BASE = "https://api.fireworks.ai/inference/v1"
GATEWAY_BASE = "https://aigateway.leanmcp.com/v1/fireworks"


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for parent in [Path.cwd(), *Path.cwd().resolve().parents]:
        if (parent / ".env").is_file():
            load_dotenv(parent / ".env")
            return


def post(url: str, body: dict, key: str, timeout: float, ctx) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.load(resp)


def ping(api_base: str, key: str, model: str, timeout: float) -> tuple[int, str]:
    """(exit_code, status_word). One tiny completion against the model."""
    # litellm's provider prefix means nothing to the HTTP endpoint.
    if model.startswith("fireworks_ai/"):
        model = model[len("fireworks_ai/"):]
    url = api_base.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        # 128, not 8. Reasoning models emit chain-of-thought into a separate
        # channel before any final-answer token lands in `content`; with a tiny
        # budget they spend it all reasoning and return content="" forever,
        # which a naive readiness check misreads as "never warms up".
        "max_tokens": 128,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": "ping"}],
    }

    # Verified TLS first; some environments fail against the default CA store,
    # and this is only an internal readiness ping.
    for i, ctx in enumerate((ssl.create_default_context(),
                             ssl._create_unverified_context())):
        try:
            data = post(url, body, key, timeout, ctx)
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", "replace")
            sys.stderr.write(f"HTTP {e.code}: {detail}\n")
            if e.code == 404:
                sys.stderr.write(
                    "  404 usually means this route cannot SEE the model: a private "
                    "deployment behind a gateway not wired to your account, or a "
                    "wrong model path.\n")
            return 2, f"HTTP {e.code}"
        except ssl.SSLError as e:
            if i == 0:
                continue
            sys.stderr.write(f"ERR ssl: {e}\n")
            return 3, "ERR"
        except Exception as e:
            sys.stderr.write(f"ERR: {type(e).__name__}: {e}\n")
            return 3, "ERR"

        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError):
            sys.stderr.write(f"unexpected shape: {json.dumps(data)[:400]}\n")
            return 1, "EMPTY"
        content = msg.get("content") or msg.get("reasoning_content")
        if content:
            sys.stderr.write(f"READY: {str(content)[:160]!r}\n")
            return 0, "READY"
        sys.stderr.write("EMPTY: HTTP 200 with no content — replica still warming up.\n")
        return 1, "EMPTY"
    return 3, "ERR"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="slug, deployment id, or full path")
    p.add_argument("--account", help="Fireworks account id — makes --model a deployment id")
    p.add_argument("--api-base", help="override the base URL")
    p.add_argument("--direct", action="store_true", help="Fireworks directly, not the gateway")
    p.add_argument("--timeout", type=float, default=60.0, help="per-request HTTP timeout")
    p.add_argument("--wait", type=float, default=0.0,
                   help="keep pinging up to N seconds until READY (cold start)")
    p.add_argument("--interval", type=float, default=15.0, help="seconds between retries")
    a = p.parse_args()

    load_env()
    if a.direct:
        base = a.api_base or DIRECT_BASE
        key, keyname = os.getenv("FIREWORKS_API_KEY"), "FIREWORKS_API_KEY"
    else:
        base = a.api_base or GATEWAY_BASE
        key, keyname = os.getenv("LEANMCP_API_KEY"), "LEANMCP_API_KEY"
    if not key:
        sys.stderr.write(f"ERR: {keyname} not set.\n")
        print("ERR")
        return 3

    model = a.model
    if "/" not in model:
        model = (f"accounts/{a.account}/deployments/{model}" if a.account
                 else f"accounts/fireworks/models/{model}")

    sys.stderr.write(f"pinging {model} via {base}\n")
    deadline = time.time() + a.wait
    while True:
        code, status = ping(base, key, model, a.timeout)
        if code == 0 or code == 2 or time.time() >= deadline:
            print(status)
            return code
        sys.stderr.write(f"  not ready ({status}); retrying in {a.interval:.0f}s "
                         f"({deadline - time.time():.0f}s left)\n")
        time.sleep(a.interval)


if __name__ == "__main__":
    raise SystemExit(main())
