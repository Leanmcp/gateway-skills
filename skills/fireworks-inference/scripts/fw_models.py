#!/usr/bin/env python3
"""
fw_models.py — browse and filter the Fireworks model catalogue.

The catalogue is large, paginated, and full of models you cannot use for the
thing you are doing: image generators, embedders, rerankers, dedicated-only
models, and models without function calling. Picking a model by name from a blog
post and discovering at run time that it is not serverless — or that it reports
`supportsTools: false` — is a slow way to learn this.

    python fw_models.py                                   # everything, as a table
    python fw_models.py --serverless --tools --sort context
    python fw_models.py --search kimi
    python fw_models.py --serverless --tools --litellm    # paste-ready litellm ids
    python fw_models.py --serverless --slugs > models.txt
    python fw_models.py --json --min-context 100000
    python fw_models.py --refresh                         # re-fetch, ignore the cache

Auth: `FIREWORKS_API_KEY` from the environment or a `.env` walking up from cwd.

Two environment quirks this handles, both of which look like "the API is down":
  * Fireworks' WAF 403s the default `Python-urllib` User-Agent — it sends a
    curl-like UA instead.
  * Some Python installs fail TLS verification against the default CA store —
    it uses certifi's bundle when available.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://api.fireworks.ai/v1/accounts/fireworks/models"
PAGE_SIZE = 200
CACHE_PATH = Path(__file__).with_name("fireworks_models_cache.json")
LITELLM_PREFIX = "fireworks_ai/accounts/fireworks/models"


# --------------------------------------------------------------------------- #
# auth
# --------------------------------------------------------------------------- #
def load_api_key() -> str:
    key = os.environ.get("FIREWORKS_API_KEY")
    if key:
        return key
    for parent in [Path.cwd(), *Path(__file__).resolve().parents]:
        env = parent / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("FIREWORKS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: FIREWORKS_API_KEY not set (environment or a .env above cwd).")


# --------------------------------------------------------------------------- #
# fetch
# --------------------------------------------------------------------------- #
def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url: str, key: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "curl/8.4.0",     # the default urllib UA gets 403'd by the WAF
    })
    with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as r:
        return json.load(r)


def fetch_all(key: str) -> list[dict]:
    models: list[dict] = []
    token, page = "", 0
    while True:
        page += 1
        params = {"pageSize": PAGE_SIZE}
        if token:
            params["pageToken"] = token
        data = _get(f"{API_URL}?{urllib.parse.urlencode(params)}", key)
        batch = data.get("models", [])
        models.extend(batch)
        print(f"  page {page}: +{len(batch)} (total {len(models)})", file=sys.stderr)
        token = data.get("nextPageToken") or ""
        if not token:
            break
    return models


def load_models(refresh: bool) -> list[dict]:
    if not refresh and CACHE_PATH.is_file():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    models = fetch_all(load_api_key())
    try:
        CACHE_PATH.write_text(json.dumps(models), encoding="utf-8")
        print(f"  cached -> {CACHE_PATH}", file=sys.stderr)
    except OSError:
        pass
    return models


# --------------------------------------------------------------------------- #
# shape + filter
# --------------------------------------------------------------------------- #
def slug_of(m: dict) -> str:
    return (m.get("name") or "").rsplit("/", 1)[-1]


def row(m: dict) -> dict:
    return {
        "slug": slug_of(m),
        "display": m.get("displayName") or "",
        "kind": m.get("kind") or "",
        "context": int(m.get("contextLength") or 0),
        "serverless": bool(m.get("supportsServerless")),
        "tools": bool(m.get("supportsTools")),
        "vision": bool(m.get("supportsImageInput")),
        "tunable": bool(m.get("tunable")),
        "deprecated": bool(m.get("deprecationDate")),
        "created": m.get("createTime") or "",
    }


def apply_filters(rows: list[dict], a) -> list[dict]:
    def keep(r: dict) -> bool:
        for flag, field in (("serverless", "serverless"), ("tools", "tools"),
                            ("vision", "vision"), ("tunable", "tunable")):
            want = getattr(a, flag)
            if want is not None and r[field] is not want:
                return False
        if a.hide_deprecated and r["deprecated"]:
            return False
        if a.min_context and r["context"] < a.min_context:
            return False
        if a.kind and a.kind.lower() not in r["kind"].lower():
            return False
        if a.search:
            hay = f"{r['slug']} {r['display']}".lower()
            if a.search.lower() not in hay:
                return False
        return True
    return [r for r in rows if keep(r)]


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("(no models matched)")
        return
    w = max(len(r["slug"]) for r in rows)
    print(f"{'SLUG'.ljust(w)}  {'CONTEXT':>8}  SRVL  TOOL  VIS  TUNE  DEPR  KIND")
    print("-" * (w + 52))
    for r in rows:
        def y(b: bool) -> str:
            return " ✓  " if b else " ·  "
        print(f"{r['slug'].ljust(w)}  {r['context']:>8}  {y(r['serverless'])}"
              f"{y(r['tools'])}{y(r['vision'])[:4]}{y(r['tunable'])}"
              f"{y(r['deprecated'])}  {r['kind']}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("serverless", "tools", "vision", "tunable"):
        p.add_argument(f"--{flag}", dest=flag, action="store_true", default=None)
        p.add_argument(f"--no-{flag}", dest=flag, action="store_false")
    p.add_argument("--hide-deprecated", action="store_true")
    p.add_argument("--min-context", type=int)
    p.add_argument("--kind", help="substring match on `kind` (e.g. HF_BASE_MODEL)")
    p.add_argument("--search", help="substring match on slug / display name")
    p.add_argument("--sort", choices=["name", "context", "created", "tools", "serverless"],
                   default="name")
    out = p.add_mutually_exclusive_group()
    out.add_argument("--litellm", action="store_true", help="one litellm id per line")
    out.add_argument("--slugs", action="store_true", help="one bare slug per line")
    out.add_argument("--json", action="store_true")
    p.add_argument("--refresh", action="store_true", help="re-fetch, ignore the cache")
    a = p.parse_args()

    rows = apply_filters([row(m) for m in load_models(a.refresh)], a)
    keys = {"name": lambda r: r["slug"], "context": lambda r: -r["context"],
            "created": lambda r: r["created"], "tools": lambda r: (not r["tools"], r["slug"]),
            "serverless": lambda r: (not r["serverless"], r["slug"])}
    rows.sort(key=keys[a.sort])

    if a.litellm:
        for r in rows:
            print(f"{LITELLM_PREFIX}/{r['slug']}")
    elif a.slugs:
        for r in rows:
            print(r["slug"])
    elif a.json:
        print(json.dumps(rows, indent=2))
    else:
        print_table(rows)
        print(f"\n{len(rows)} model(s). For an agent benchmark you almost always want "
              f"--serverless --tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
