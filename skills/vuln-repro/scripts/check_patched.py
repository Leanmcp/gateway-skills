#!/usr/bin/env python3
"""
check_patched.py CVE-ID — fast "is this already patched?" gate.

Pulls the NVD and CVE.org records (read-only, public APIs only) and reports
whether either source shows a fix: a patch-tagged reference, an 'unaffected'
version range, or an explicit fixed version. This is a heuristic to speed up the
gate in the vuln-repro workflow, NOT a substitute for reading the vendor
advisory. If it prints UNCONFIRMED, verify manually before building anything.

Usage:  python3 check_patched.py CVE-2025-32711
"""
import json
import os
import re
import sys
import urllib.request

NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="
CVEORG = "https://cveawg.mitre.org/api/cve/"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "vuln-repro"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    if len(sys.argv) != 2 or not re.match(r"^CVE-\d{4}-\d+$", sys.argv[1], re.I):
        raise SystemExit("usage: check_patched.py CVE-YYYY-NNNN")
    cve = sys.argv[1].upper()
    signals = []

    # NVD: look for references tagged Patch, and non-REJECTED status
    try:
        h = {"User-Agent": "vuln-repro"}
        if os.environ.get("NVD_API_KEY"):
            h["apiKey"] = os.environ["NVD_API_KEY"]
        nvd = get(NVD + cve, h)
        v = nvd.get("vulnerabilities", [])
        if v:
            c = v[0]["cve"]
            for ref in c.get("references", []):
                tags = ref.get("tags", [])
                if "Patch" in tags or "Release Notes" in tags:
                    signals.append(f"NVD ref tagged {tags}: {ref['url']}")
            if c.get("vulnStatus"):
                signals.append(f"NVD status: {c['vulnStatus']}")
        else:
            signals.append("NVD: no record")
    except Exception as e:
        signals.append(f"NVD error: {e}")

    # CVE.org: look for 'unaffected' version ranges (typical fixed marker)
    try:
        rec = get(CVEORG + cve)
        cna = rec.get("containers", {}).get("cna", {})
        for a in cna.get("affected", []):
            for ver in a.get("versions", []):
                if ver.get("status") == "unaffected":
                    signals.append(
                        f"CVE.org unaffected/fixed: {a.get('product')} "
                        f"{ver.get('version')}")
        state = rec.get("cveMetadata", {}).get("state")
        if state:
            signals.append(f"CVE.org state: {state}")
    except Exception as e:
        signals.append(f"CVE.org error: {e}")

    patched = any("Patch" in s or "unaffected" in s or "fixed" in s.lower()
                  for s in signals)
    print(f"=== {cve} ===")
    for s in signals:
        print(f"  - {s}")
    verdict = "PATCH SIGNAL FOUND" if patched else "UNCONFIRMED — verify vendor advisory manually"
    print(f"\nverdict: {verdict}")
    print("note: always read the primary advisory before reproducing.")


if __name__ == "__main__":
    main()
