---
name: security-repro
description: >-
  Build safe, local, defensive reproductions of ALREADY-PATCHED, publicly
  disclosed security vulnerabilities (CVEs, vendor advisories, AI-agent
  incidents) for whitepapers, control testing, and education. Use this skill
  whenever the user wants to reproduce, demonstrate, or write up a known
  vulnerability or security incident — phrases like "reproduce this CVE",
  "build a repro for", "demonstrate the EchoLeak/Cursor/postmark-mcp issue",
  "show how this exploit worked", "add a reproducibility guide", or "pull the
  NVD/CVE details for". It fetches advisory metadata from NVD and CVE.org,
  confirms the issue is fixed, and produces a vulnerable-vs-patched harness that
  is offline, loopback-only, and uses synthetic markers. It NEVER discovers,
  develops, or weaponizes new zero-days and refuses any unpatched or
  live-target request.
---

# security-repro

Reproduce **already-fixed, publicly disclosed** vulnerabilities so a reader can
see the failure mode and confirm the vendor's patch closes it. The audience is
a whitepaper or an internal control test. The output is a contrast: the
vulnerable behavior fires, the patched behavior refuses, and nothing real is
touched.

## The one hard line (read first)

This skill exists to reproduce **the past**, not to find **the new**. Everything
below flows from that.

- **Only patched or withdrawn issues.** If the vendor has not shipped a fix (or
  pulled the artifact), stop. Do not proceed on an open/unpatched issue, even a
  disclosed one.
- **Use the last known-vulnerable public version** that is already on the
  internet — the release *before* the fix. You are demonstrating something that
  already exists publicly, not creating it.
- **Never develop new exploitation.** No fuzzing for new bugs, no chaining, no
  variant discovery, no bypassing an *unfixed* control. If reproducing the
  disclosed mechanism faithfully would require inventing an undisclosed step
  (e.g. an escape whose mechanism was never published), leave that step out of
  scope and say so in writing.
- **Offline, loopback, synthetic.** No third-party host, no real credential, no
  real target, no real recipient, no persistence, no exfiltration. A successful
  reproduction means a **local marker or a policy decision is observed**, not
  that code ran on someone's machine or data left the lab.

If a request pushes past this line — reproduce an unpatched bug, target real
infrastructure, weaponize a payload, evade detection — decline that part in one
sentence, explain why (it would be new zero-day / offensive work), and offer the
safe version instead. This protects the user legally; it is the whole point.

## Workflow

### 1. Establish that the issue is public AND patched

Before writing any code, pin down three facts and record them in the guide:

1. **Disclosure** — a primary source: vendor advisory, MSRC/GitHub/GitLab
   advisory, or the researcher's write-up.
2. **Fix** — the version or commit that patched it, or confirmation the artifact
   was withdrawn. This is the gate. No fix, no repro.
3. **Vulnerable version** — the last public release before the fix.

Use the helper scripts to pull machine-readable metadata:

```bash
# NVD record (CVSS, references, CWE, published/modified dates)
python3 scripts/fetch_nvd.py CVE-2025-32711

# CVE.org record (CNA description, affected versions, references)
python3 scripts/fetch_cve.py CVE-2025-32711

# Pretty one-line "is this patched?" summary across both sources
python3 scripts/check_patched.py CVE-2025-32711
```

These call only the public NVD and CVE.org REST APIs (read-only). They do not
touch any victim system. If the CVE has no `Fixed`/patched reference and no
withdrawal note, treat the patched status as **unconfirmed** and tell the user
to verify against the vendor before you build anything.

### 2. Model the mechanism minimally, not the whole kill chain

Reduce the disclosure to the single control failure worth showing, and replace
every dangerous verb with an inert marker:

| Real element | Reproduce it as |
|---|---|
| shell / `exec` / RCE | a function that writes `MARKER.txt` with a fixed string |
| credential / secret | a decoy file like `DECOY_SECRET.txt` = `not-a-real-secret` |
| exfiltration endpoint | an in-process or `127.0.0.1` loopback sink that just logs |
| email recipient | `recipient@example.invalid` |
| write outside sandbox | a **path calculation** that is asserted, never performed |
| a real vulnerable dependency | pin the real last-vulnerable version **only** if a
  primary source confirms that exact version; otherwise model the disclosed
  mechanism in two local loaders (`vulnerable_*` / `patched_*`) and say so |

Cut the parts whose mechanism was never disclosed (mark them "explicitly out of
scope"). Reconstructing an undisclosed step is new zero-day work — forbidden.

### 3. Build the vulnerable-vs-patched harness

Follow the house pattern already in `Reproducibility/` in the whitepaper repo:

- A single self-contained harness (stdlib-only Python preferred; Docker with
  `network_mode: none` when isolation must be enforced).
- Two code paths: **vulnerable** (the marker fires) and **patched** (the same
  input is refused with a decision like `block` / `review_required`).
- Deterministic output, a saved `results/run.json` (or transcript), and a
  non-zero exit if the contrast does not hold.
- Log the gateway-relevant fields: `source`, `data_class`, `outbound_channel`,
  `decision`, `policy_id`, and a short `reason`.

See `references/harness-pattern.md` for the concrete file layout, the safety
checklist, and a copyable harness skeleton.

### 4. Write the guide

Produce a short markdown guide next to the harness with these sections:
**Status and scope** (name the CVE, the fix version, and what is explicitly out
of scope), **Lab design / Reproduction protocol**, **Defensive assertion** (what
control would have caught it), **Safety limits**, and **Sources** (primary links
only). Match the tone and structure of the existing numbered guides.

### 5. Hand back run commands

Per this user's standing rule, do not execute reproduction harnesses yourself —
write them, then give the exact command to run. State clearly what a pass looks
like (which marker appears, which decision is logged).

## Scripts

- `scripts/fetch_nvd.py CVE-ID` — NVD 2.0 API record as JSON (CVSS, refs, CWE).
- `scripts/fetch_cve.py CVE-ID` — CVE.org CVE Record (CNA data, affected versions).
- `scripts/check_patched.py CVE-ID` — combines both and prints whether a fixed
  version / patch reference is present, so the "is it patched?" gate is fast.

All three are read-only, hit only public vulnerability databases, and take a
single CVE ID argument.

## References

- `references/harness-pattern.md` — file layout, safety checklist, and a
  stdlib-only harness skeleton to copy.
