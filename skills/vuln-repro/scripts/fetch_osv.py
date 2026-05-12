#!/usr/bin/env python3
"""
fetch_osv.py CVE-ID|OSV-ID [--package ecosystem:name]
    Fetch vulnerability data from OSV.dev (read-only, public API).

OSV usually has the most accurate affected/fixed version ranges for package
ecosystems (npm, PyPI, Go, crates.io, Maven, Debian, Alpine, ...). Prefer it over
NVD's CPE ranges when the two disagree about a library.

Examples:
    python3 fetch_osv.py CVE-2021-44228
    python3 fetch_osv.py --package npm:postmark-mcp
"""
import json
import sys
import urllib.request

VULN = "https://api.osv.dev/v1/vulns/"
QUERY = "https://api.osv.dev/v1/query"


def post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"User-Agent": "vuln-repro", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "vuln-repro"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def summarize(v):
    print(f"\n=== {v.get('id')} ===")
    if v.get("aliases"):
        print(f"aliases:   {', '.join(v['aliases'])}")
    print(f"published: {v.get('published')}  modified: {v.get('modified')}")
    if v.get("withdrawn"):
        print(f"WITHDRAWN: {v['withdrawn']}  <-- satisfies the 'resolved' gate")
    print(f"summary:   {(v.get('summary') or '').strip()[:200]}")
    for a in v.get("affected", []):
        pkg = a.get("package", {})
        name = f"{pkg.get('ecosystem','?')}:{pkg.get('name','?')}"
        for r in a.get("ranges", []):
            events = r.get("events", [])
            intro = [e["introduced"] for e in events if "introduced" in e]
            fixed = [e["fixed"] for e in events if "fixed" in e]
            lastaff = [e["last_affected"] for e in events if "last_affected" in e]
            print(f"  {name} [{r.get('type')}] introduced={intro} "
                  f"fixed={fixed or '-'} last_affected={lastaff or '-'}")
        if a.get("versions"):
            vs = a["versions"]
            print(f"  {name} affected versions ({len(vs)}): "
                  f"{vs[0]} .. {vs[-1]}")
    for ref in v.get("references", [])[:20]:
        print(f"  ref [{ref.get('type')}] {ref.get('url')}")
    fixed_any = any("fixed" in e
                    for a in v.get("affected", [])
                    for r in a.get("ranges", [])
                    for e in r.get("events", []))
    verdict = ("FIXED VERSION PRESENT" if fixed_any
               else "WITHDRAWN" if v.get("withdrawn")
               else "NO FIXED VERSION IN OSV - verify with the vendor")
    print(f"verdict:   {verdict}")


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    try:
        if args[0] == "--package":
            eco, _, name = args[1].partition(":")
            res = post(QUERY, {"package": {"ecosystem": eco, "name": name}})
            vulns = res.get("vulns", [])
            print(f"{len(vulns)} vulnerabilit(ies) for {eco}:{name}")
            for v in vulns:
                summarize(v)
        else:
            summarize(get(VULN + args[0].upper()))
    except Exception as e:
        raise SystemExit(f"OSV request failed: {e}")


if __name__ == "__main__":
    main()
