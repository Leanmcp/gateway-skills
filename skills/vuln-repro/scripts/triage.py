#!/usr/bin/env python3
"""
triage.py CVE-ID — one-shot gate for the vuln-repro workflow.

Queries NVD, CVE.org and OSV.dev (read-only, public vulnerability databases
only; no victim system is contacted) and prints a merged view plus a patched
verdict, so step 1 of the workflow takes one command instead of four.

What it answers:
  - Is there a record at all, and is it REJECTED/DISPUTED?
  - Severity and bug class (CVSS, CWE)
  - Which versions are affected, and which version fixed it
  - Which references are the patch commit / advisory (these are what you read next)
  - Whether the "already patched" gate is satisfied

Usage:  python3 triage.py CVE-2021-44228
Optional: export NVD_API_KEY=... to raise the NVD rate limit.
"""
import json
import os
import re
import sys
import urllib.request

NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="
CVEORG = "https://cveawg.mitre.org/api/cve/"
OSV = "https://api.osv.dev/v1/vulns/"
UA = {"User-Agent": "vuln-repro"}

PATCH_HINTS = ("commit", "/pull/", "/compare/", "releases/tag", "security/advisories",
               "changelog", "release-notes", "git.kernel.org", "patch")


def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def section(t):
    print(f"\n{'=' * 68}\n{t}\n{'=' * 68}")


def main():
    if len(sys.argv) != 2 or not re.match(r"^CVE-\d{4}-\d+$", sys.argv[1], re.I):
        raise SystemExit("usage: triage.py CVE-YYYY-NNNN")
    cve = sys.argv[1].upper()
    fix_signals, refs, notes = [], [], []

    section(f"{cve} — NVD")
    try:
        h = {"apiKey": os.environ["NVD_API_KEY"]} if os.environ.get("NVD_API_KEY") else {}
        data = get(NVD + cve, h)
        vulns = data.get("vulnerabilities", [])
        if not vulns:
            print("  no NVD record")
            notes.append("no NVD record (may be too recent, or not a CVE)")
        else:
            c = vulns[0]["cve"]
            desc = next((d["value"] for d in c.get("descriptions", [])
                         if d.get("lang") == "en"), "")
            print(f"  status:    {c.get('vulnStatus')}")
            print(f"  published: {c.get('published')}   modified: {c.get('lastModified')}")
            if c.get("vulnStatus") in ("Rejected",):
                notes.append("NVD status is Rejected — this is not a real vulnerability")
            metrics = c.get("metrics", {})
            for k in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if metrics.get(k):
                    m = metrics[k][0]["cvssData"]
                    print(f"  cvss:      {m.get('baseScore')} "
                          f"({m.get('baseSeverity','?')}) via {k}")
                    print(f"  vector:    {m.get('vectorString')}")
                    break
            cwes = [d["value"] for w in c.get("weaknesses", [])
                    for d in w.get("description", []) if d.get("lang") == "en"]
            print(f"  cwe:       {', '.join(cwes) or 'n/a'}   <- your bug class starting point")
            print(f"  desc:      {desc[:400]}")
            for r in c.get("references", []):
                refs.append((r["url"], r.get("tags", [])))
                if "Patch" in r.get("tags", []):
                    fix_signals.append(f"NVD reference tagged Patch: {r['url']}")
    except Exception as e:
        print(f"  NVD error: {e}")

    section(f"{cve} — CVE.org (CNA record)")
    try:
        rec = get(CVEORG + cve)
        meta = rec.get("cveMetadata", {})
        cna = rec.get("containers", {}).get("cna", {})
        print(f"  state:     {meta.get('state')}   assigner: {meta.get('assignerShortName')}")
        for a in cna.get("affected", []):
            prod = f"{a.get('vendor','?')}/{a.get('product','?')}"
            for v in a.get("versions", []):
                mark = "FIXED/UNAFFECTED" if v.get("status") == "unaffected" else v.get("status")
                lt = v.get("lessThan") or v.get("lessThanOrEqual")
                print(f"    {prod}: {v.get('version')}"
                      f"{' < ' + lt if lt else ''}  [{mark}]")
                if v.get("status") == "unaffected":
                    fix_signals.append(f"CVE.org unaffected range: {prod} {v.get('version')}")
        for r in cna.get("references", []):
            refs.append((r.get("url", ""), r.get("tags", [])))
    except Exception as e:
        print(f"  CVE.org error: {e}")

    section(f"{cve} — OSV.dev (package version ranges)")
    try:
        v = get(OSV + cve)
        if v.get("withdrawn"):
            print(f"  WITHDRAWN: {v['withdrawn']}")
            fix_signals.append(f"OSV withdrawn: {v['withdrawn']}")
        for a in v.get("affected", []):
            pkg = a.get("package", {})
            name = f"{pkg.get('ecosystem','?')}:{pkg.get('name','?')}"
            for rng in a.get("ranges", []):
                ev = rng.get("events", [])
                intro = [e["introduced"] for e in ev if "introduced" in e]
                fixed = [e["fixed"] for e in ev if "fixed" in e]
                print(f"    {name}: introduced={intro} fixed={fixed or '-'}")
                for f in fixed:
                    fix_signals.append(f"OSV fixed version: {name} {f}")
        for r in v.get("references", []):
            refs.append((r.get("url", ""), [r.get("type", "")]))
    except Exception as e:
        print(f"  OSV: no record or error ({e})")

    section("References worth opening first")
    seen = set()
    ranked = []
    for url, tags in refs:
        if not url or url in seen:
            continue
        seen.add(url)
        score = 0
        if "Patch" in tags or "Vendor Advisory" in tags:
            score += 2
        if any(h in url.lower() for h in PATCH_HINTS):
            score += 2
        if "exploit" in url.lower() or "Exploit" in tags:
            score += 1
        ranked.append((score, url, tags))
    for score, url, tags in sorted(ranked, key=lambda x: -x[0])[:20]:
        star = "*" if score >= 2 else " "
        print(f" {star} [{','.join(t for t in tags if t) or '-'}] {url}")

    section("VERDICT")
    if fix_signals:
        print("  PATCH SIGNAL FOUND — the 'already patched' gate is provisionally satisfied:")
        for s in dict.fromkeys(fix_signals):
            print(f"    - {s}")
    else:
        print("  UNCONFIRMED — no fixed version or patch reference found.")
        print("  Do NOT build a reproduction until you confirm the fix in the vendor advisory.")
    for n in notes:
        print(f"  note: {n}")
    print("\n  Next: open the starred references above, find the fix commit, and read")
    print("  the diff BEFORE writing any exploit code (workflow step 3).")


if __name__ == "__main__":
    main()
