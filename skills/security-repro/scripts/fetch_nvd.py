#!/usr/bin/env python3
"""
fetch_nvd.py CVE-ID — fetch a CVE record from the public NVD 2.0 REST API.

Read-only. Contacts only services.nvd.nist.gov. No victim system is touched.
Prints the raw JSON plus a short summary (CVSS, CWE, references, dates).

Usage:  python3 fetch_nvd.py CVE-2025-32711
Optional: set NVD_API_KEY in the environment to raise the rate limit.
"""
import json
import os
import re
import sys
import urllib.request

API = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="


def main():
    if len(sys.argv) != 2 or not re.match(r"^CVE-\d{4}-\d+$", sys.argv[1], re.I):
        raise SystemExit("usage: fetch_nvd.py CVE-YYYY-NNNN")
    cve = sys.argv[1].upper()
    req = urllib.request.Request(API + cve, headers={"User-Agent": "security-repro"})
    key = os.environ.get("NVD_API_KEY")
    if key:
        req.add_header("apiKey", key)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        raise SystemExit(f"NVD request failed: {e}")

    vulns = data.get("vulnerabilities", [])
    if not vulns:
        raise SystemExit(f"{cve}: no NVD record found")
    c = vulns[0]["cve"]

    desc = next((d["value"] for d in c.get("descriptions", [])
                 if d.get("lang") == "en"), "")
    metrics = c.get("metrics", {})
    cvss = None
    for k in ("cvssMetricV31", "cvssMetricV40", "cvssMetricV30", "cvssMetricV2"):
        if metrics.get(k):
            m = metrics[k][0]["cvssData"]
            cvss = f"{m.get('baseScore')} ({m.get('baseSeverity','?')}) {k}"
            break
    cwes = [d["value"] for w in c.get("weaknesses", [])
            for d in w.get("description", []) if d.get("lang") == "en"]
    refs = [r["url"] for r in c.get("references", [])]

    print(json.dumps(c, indent=2))
    print("\n--- summary ---")
    print(f"id:        {c.get('id')}")
    print(f"status:    {c.get('vulnStatus')}")
    print(f"published: {c.get('published')}  modified: {c.get('lastModified')}")
    print(f"cvss:      {cvss}")
    print(f"cwe:       {', '.join(cwes) or 'n/a'}")
    print(f"desc:      {desc[:300]}")
    print(f"refs:      {len(refs)}")
    for u in refs[:20]:
        print(f"  - {u}")


if __name__ == "__main__":
    main()
