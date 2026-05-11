#!/usr/bin/env python3
"""
fetch_cve.py CVE-ID — fetch a CVE Record from the public CVE.org REST API.

Read-only. Contacts only cveawg.mitre.org. Prints raw JSON plus a summary of
the CNA description, affected products/versions (including any 'fixed'/'patched'
version markers), and references.

Usage:  python3 fetch_cve.py CVE-2025-32711
"""
import json
import re
import sys
import urllib.request

API = "https://cveawg.mitre.org/api/cve/"


def main():
    if len(sys.argv) != 2 or not re.match(r"^CVE-\d{4}-\d+$", sys.argv[1], re.I):
        raise SystemExit("usage: fetch_cve.py CVE-YYYY-NNNN")
    cve = sys.argv[1].upper()
    req = urllib.request.Request(API + cve, headers={"User-Agent": "security-repro"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        raise SystemExit(f"CVE.org request failed: {e}")

    cna = data.get("containers", {}).get("cna", {})
    desc = next((d["value"] for d in cna.get("descriptions", [])
                 if d.get("lang", "").startswith("en")), "")
    refs = [r.get("url") for r in cna.get("references", [])]

    print(json.dumps(data, indent=2))
    print("\n--- summary ---")
    print(f"id:    {data.get('cveMetadata', {}).get('cveId')}")
    print(f"state: {data.get('cveMetadata', {}).get('state')}")
    print(f"desc:  {desc[:300]}")
    print("affected:")
    for a in cna.get("affected", []):
        vendor = a.get("vendor", "?")
        product = a.get("product", "?")
        for v in a.get("versions", []):
            status = v.get("status", "?")
            ver = v.get("version", "?")
            lt = v.get("lessThan") or v.get("lessThanOrEqual")
            span = f" (< {lt})" if lt else ""
            marker = "  <== FIXED/UNAFFECTED" if status in ("unaffected",) else ""
            print(f"  {vendor}/{product}: {ver}{span} status={status}{marker}")
    print(f"refs:  {len(refs)}")
    for u in refs[:20]:
        print(f"  - {u}")


if __name__ == "__main__":
    main()
