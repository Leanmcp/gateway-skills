# Sourcing: where to look

Ordered by how much you should trust each source. For every factual claim in a
write-up, know which tier it came from. When tiers disagree, publish the
disagreement: getting that right is most of what earns a reputation in this
genre.

---

## Tier 1 — authoritative on "is it patched, and which version"

- **The vendor's own advisory.** Always the first stop, and the only reliable
  source for the fix version. Microsoft MSRC (`msrc.microsoft.com/update-guide`),
  Red Hat (`access.redhat.com/security/cve/<CVE>`), Oracle Critical Patch
  Updates, Cisco PSIRT, Apple security releases, Atlassian, VMware/Broadcom,
  Jenkins (`jenkins.io/security/advisories`), Django, Rails, Kubernetes
  (`kubernetes.io/docs/reference/issues-security/official-cve-feed/`).
- **The patch commit or PR.** The single richest artifact that exists. Entry
  point, precondition, oracle, and bug class, all for free. Find it from the
  advisory's reference list, or with `git log --all --grep='CVE-'` and
  `git log -S'<identifier>'` when the fix was landed silently.
- **GitHub Security Advisories** — `github.com/advisories`. Curated, carries
  fixed versions, links to commits, drives Dependabot. Filter by ecosystem.
- **OSV.dev** — `osv.dev`, API `api.osv.dev/v1/vulns/<ID>`, and query by package
  at `api.osv.dev/v1/query`. The best machine-readable affected-range data across
  npm, PyPI, Go, crates, Maven, Debian, Alpine, and more. When NVD and OSV
  disagree about ranges, OSV is usually right for package ecosystems.

## Tier 2 — good, with known caveats

- **CVE.org / the CNA record** — `cveawg.mitre.org/api/cve/<CVE>`. The CNA's own
  description and affected-version data. Often more accurate than NVD on
  versions, since the CNA is usually the vendor.
- **NVD** — `services.nvd.nist.gov/rest/json/cves/2.0?cveId=<CVE>`. Excellent for
  CVSS vectors, CWE mapping, and a consolidated reference list. Enrichment lags,
  sometimes by months, and CPE version ranges are regularly wrong. Treat as an
  index, not as truth. Set `NVD_API_KEY` to raise the rate limit.
- **Distro security trackers.** Badly underrated, and frequently the clearest
  technical explanation available anywhere, because a maintainer backporting a
  fix has to understand it precisely. Debian
  (`security-tracker.debian.org/tracker/<CVE>`), Ubuntu
  (`ubuntu.com/security/<CVE>`), Red Hat Bugzilla, SUSE, Alpine secdb, Gentoo
  GLSA.
- **CISA KEV** — `cisa.gov/known-exploited-vulnerabilities-catalog`. What is
  actually exploited in the wild. A far better prioritization signal than CVSS,
  and a good filter for "is this worth writing about".
- **EPSS** — `first.org/epss`. Probability of exploitation in the next 30 days.
  Pair with KEV; cite both when you make a "how much does this matter" claim.

## Tier 3 — mechanism and technique

- **Researcher write-ups.** Google Project Zero (`googleprojectzero.blogspot.com`
  and its issue tracker, which publishes full repro detail after the disclosure
  deadline, making it the best free corpus of worked reproductions in existence),
  watchTowr Labs, Assetnote, Orange Tsai, PortSwigger Research, Aim Labs for
  AI-agent work, Trail of Bits, NCC Group technical advisories.
- **Vendor research blogs.** Snyk, Checkmarx, Socket, Phylum, and ReversingLabs
  for supply chain; Qualys, Rapid7, Sentinel Labs, Volexity for OS and network.
- **The project's own regression test.** Search the fix commit for added tests.
  That test is a minimal PoC written by the person who understood the bug best,
  and it is the fastest path to a working trigger.
- **Nuclei templates** — `github.com/projectdiscovery/nuclei-templates`.
  Especially good, because a detection template is a minimized trigger plus an
  oracle, which is exactly the shape you want.
- **Exploit-DB** (`exploit-db.com`) and **Metasploit modules**. Read for
  mechanism.
- **PoC indexes** — `trickest/cve`, `nomi-sec/PoC-in-GitHub`. Treat every PoC
  repo as untrusted code: read it, never run it outside a disposable VM. A
  meaningful fraction of "PoC" repos are malware targeting researchers.

## Tier 4 — for the fix and the defensive assertion

- **CWE** (`cwe.mitre.org`) for the bug class, **CAPEC** for the attack pattern.
- **OWASP cheat sheets** (`cheatsheetseries.owasp.org`) — the fastest correct
  answer to "what is the right fix for this class". Genuinely good.
- **OWASP ASVS** for naming the control that should have existed, and **OWASP
  Top 10 for LLM Applications** for agent and prompt-injection work.
- **Sigma rules** (`github.com/SigmaHQ/sigma`) and **Suricata / Emerging
  Threats** rules — detections you can test against your own harness, including
  the negative control, so you can report false-positive behavior honestly.
- **MITRE ATT&CK** for placing the technique in a model your readers already use.
- **NIST SSDF** and **SLSA** (`slsa.dev`) for supply-chain fixes at layer 4;
  **Sigstore** for provenance.

## Tier 5 — monitoring, to find targets before everyone else

- `oss-security` mailing list, the real disclosure firehose for open source.
- `full-disclosure`, huntr.dev, GitHub Advisory RSS, the Rust and Go vuln DBs.
- Malicious-package feeds from Socket and Phylum, for supply-chain incidents.
- The changelogs and security pages of the projects you actually run. A silent
  fix in your own dependency is the highest-value target you will ever have,
  because you can verify exposure directly.

---

## Practical sequence for a new target

1. `python3 scripts/triage.py <CVE>` for the machine-readable merge and the
   patched verdict.
2. Open the vendor advisory from the reference list. Get the fix version.
3. Find the fix commit. If the advisory does not link one, search the repo:
   `git log --all --grep='<CVE>'`, then `git log -S'<identifier>'`.
4. Read the distro tracker entry for a second, independent explanation.
5. Read the researcher write-up for intent and preconditions.
6. Look for the regression test in the fix commit.
7. Record every source URL with the tier it came from, in the write-up's source
   list, before you start building.

## When sources disagree

They will, constantly, about version ranges. This is content, not an obstacle.
The line "NVD lists 2.14.0 as affected; the CNA says the fix shipped in 2.14.1;
the commit landed after the 2.14.1 tag and therefore first appeared in 2.14.2"
is more useful than any of the three sources alone, and writing it is how you
demonstrate you did the work rather than transcribing a database.
