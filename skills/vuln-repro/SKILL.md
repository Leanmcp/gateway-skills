---
name: vuln-repro
description: >-
  End-to-end methodology for reproducing AND patching publicly disclosed,
  already-fixed vulnerabilities: sourcing the advisory and the fix commit,
  reading the patch diff, rebuilding a pinned offline lab, building a
  vulnerable-vs-patched contrast harness with proper controls, minimizing the
  trigger, designing and validating the fix, and writing it up as a blog post or
  whitepaper. Use this skill whenever the user wants to reproduce, demonstrate,
  understand, teach, or write about a known vulnerability or security incident:
  "reproduce this CVE", "build a repro for", "how did EchoLeak / Log4Shell /
  the postmark-mcp package actually work", "show me how this exploit worked",
  "write a blog post about this vulnerability", "set up a lab for CVE-XXXX",
  "pull the NVD/CVE/OSV details", or "make a PoC I can publish". Use it just as
  eagerly for the patching half: "how should this be fixed", "is this patch
  correct", "what would have caught this", "review this security fix", "write a
  regression test for this CVE", "how do I backport this", or "what's the right
  fix for this bug class" - even when the user never says the word "reproduce".
  Reach for it on vague asks like "help me understand this security advisory",
  "I want to write about this incident", or "can we test whether we were
  vulnerable" when a disclosed vulnerability is in play. This skill only handles
  ALREADY-PATCHED, publicly disclosed issues and refuses zero-day discovery,
  live targets, and weaponization.
---

# vuln-repro

Reproduce a disclosed vulnerability faithfully, explain the fix that closed it,
and publish the result. The output is a controlled experiment plus an engineering
analysis, not a demo.

## The hard line, read this first

This skill reproduces **the past**. It does not discover **the new**. Everything
below depends on that distinction holding, and it is what keeps the work legal
and publishable.

- **Only patched or withdrawn issues.** A fix version, a patch commit, or a
  withdrawal notice. "Reported to the vendor" and "advisory published" are not
  patched. No fix, no repro. Stop and say so.
- **Use the last public vulnerable version**, pulled from the ordinary public
  channel. You are studying something already on the internet.
- **Never develop new exploitation.** No fuzzing for new bugs, no chaining, no
  variant hunting against unfixed code, no bypassing a control the vendor has
  not fixed. If faithful reproduction would require inventing an undisclosed
  step, leave that step out and write down that you did.
- **Offline, loopback, synthetic.** No third-party host, no real credential, no
  real target or recipient, no persistence, no exfiltration. Success means a
  local marker appears or a policy decision is logged, never that code ran on
  someone's machine or data left the lab.

When a request crosses the line, decline that specific part in one sentence, say
why (it would be new offensive work), and offer the safe version. Do not
moralize; just redraw the boundary and keep building.

One boundary that confuses people: varying **your own payload against your own
patched build** to check the fix is not payload-shaped is *validation*, and it is
in scope. Hunting variants against the **vendor's unfixed** code is *discovery*,
and it is not. If validation surfaces an unpatched sibling, that is a new
finding: it goes to the vendor privately, never into the blog post.

## What a reproduction actually is

A repro is a falsifiable claim, not a screenshot:

> Under environment E, input I drives system S at version V-vuln into state X.
> The same I against V-fixed does not reach X, because of change C.

Everything below exists to make E, I, V, X, and C precise enough that a stranger
re-runs you and gets the same answer. A repro that shows X happening but cannot
explain C is a test case. One that explains C is a paper people cite.

## Workflow

Work these in order. Steps 1-3 are cheap and kill bad targets early; skipping
them is why most repro attempts die in step 6 with an unexplainable failure.

### 1. Gate: is it public and patched?

Fill this table before writing any code. An unknown cell means not ready.

| Fact | Acceptable evidence |
|---|---|
| Disclosure | Vendor advisory, GitHub/GitLab/MSRC advisory, researcher write-up |
| Fix | Fixed version, patch commit SHA, or withdrawal notice |
| Last vulnerable version | The public release immediately before the fix |

Pull the machine-readable half in one shot:

```bash
python3 scripts/triage.py CVE-2025-32711
```

That queries NVD, CVE.org, and OSV, prints a merged view, and states a patched
verdict. Individual fetchers (`fetch_nvd.py`, `fetch_cve.py`, `fetch_osv.py`,
`check_patched.py`) exist when you want one source. All are read-only against
public vulnerability databases.

If the verdict is UNCONFIRMED, verify against the vendor by hand. Treat that as a
red light, not a yellow one.

For where to look beyond the APIs, and how much to trust each source, read
`references/sourcing.md`. That file is the answer to "where should I be looking?"
and it is worth reading in full the first few times.

### 2. Decide whether the target is worth it

Not every CVE deserves a week. Score on: is it truly patched; is the mechanism
published in enough detail to reproduce without inventing steps; can you build
the vulnerable environment legally and cheaply; does it teach a *class* of bug
rather than an instance; and is someone else's write-up already definitive.

The best target is usually **a small patch with a large consequence**. A
three-line diff that turns full compromise into a clean refusal is the most
instructive object in security.

A SaaS backend patched server-side (most AI-agent CVEs) cannot be reproduced at
all. You can only *model* it. That is a legitimate artifact, but it must be
labeled a model in the title and the first paragraph. Claiming to reproduce
something you modeled is the fastest way to lose a technical audience.

### 3. Read the patch before you write the exploit

This inverts the amateur order and is the single biggest quality difference
between a good repro and a bad one. The diff gives you the entry point, the
precondition, the oracle, and the bug class for free.

```bash
git log --oneline v1.2.3..v1.2.4          # what changed between vuln and fix
git show <fix-sha>                         # the fix alone
git log --all --grep='CVE-2024' --oneline  # projects often reference the CVE
git log -S'vulnerable_function' --oneline  # finds silent fixes with no CVE label
```

Two things to hunt specifically. **The silent fix**: many projects patch under a
message like "improve input handling"; `git log -S` on the vulnerable identifier
finds these. **The incomplete fix**: check whether a follow-up commit touched the
same function weeks later, because that story is usually the best part of the
write-up.

Reason from the diff, not from the CVE prose. CVE descriptions are written by
people summarizing at a distance and are regularly wrong about the mechanism.

### 4. Rebuild the environment, pinned

The most common cause of "the repro doesn't work" is an undocumented environment
difference. Pin the artifact by hash not tag, pin the runtime (language, libc,
OS), pin the config including which non-default setting the bug needed, and
disable the noise (ASLR, JIT, auto-update, telemetry).

Cut the network. `network_mode: none` whenever real code execution is involved;
an internal-only bridge with a loopback sink when the mechanism genuinely needs a
hop. Never host networking, never egress. The lab should be disposable enough
that total compromise of it costs you a `docker compose down`.

`references/harness-pattern.md` has the container hardening block, the file
layout, and the safety checklist.

### 5. Design the oracle before building the exploit

The oracle decides, mechanically, whether the bug fired. Replace every dangerous
verb with an inert marker; this costs nothing evidentially and is the core safety
technique.

| Real capability | Reproduce it as |
|---|---|
| Shell / exec / RCE | write `MARKER.txt` with a fixed UUID, then exit |
| Credential theft | read a decoy `DECOY_SECRET.txt` = `not-a-real-secret-1f4c9a` |
| Exfiltration | POST to a `127.0.0.1` sink that only logs the body |
| Email to a person | `recipient@example.invalid` (RFC 6761, cannot resolve) |
| Sandbox escape | compute the escaped path and **assert** it; never write |
| Destruction / encryption | assert the target set was selected; never touch it |
| Privilege escalation | assert the privileged state is reachable; do not use it |
| Persistence | assert the write location is reachable; do not persist |

The marker must be greppable and impossible to produce by accident. A random
UUID baked into the harness is right; `pwned` is not.

### 6. Build the four-cell contrast

A single positive result proves almost nothing. Run all four cells and report
all four:

| Cell | Input | Version | Expected |
|---|---|---|---|
| Positive | malicious | vulnerable | marker fires |
| Negative control | benign | vulnerable | no marker |
| Patch control | malicious | patched | no marker, explicit refusal |
| Patch functional | benign | patched | works normally, no regression |

The negative control is what distinguishes "the bug fired" from "my harness
always writes the marker", and skipping it is the most common silent error in
published repros. The patch functional cell is what decides whether a fix
survives production, and almost nobody runs it.

Copy the harness skeleton and layout from `references/harness-pattern.md`. The
harness is a test: it exits non-zero when the story it tells is not true.

### 7. Minimize

A published PoC is usually 200 lines of scaffolding around the 6 bytes that
matter. Finding those bytes is the intellectual core and the part readers value.

- **Delta-debug the input**: halve, re-run, keep the half that still fires,
  repeat. `scripts/minimize.py` implements this against any command that exits 0
  when the bug fires, so you rarely need to write it again.
- **Bisect the version**: `git bisect run ./harness.sh`. This finds the
  *introducing* commit, not just the fixing one, which tells you how long the bug
  was live and what change caused it.
- **Bisect the environment** when it fires on the host but not in the container:
  add config back one item at a time. The item that restores the bug is a
  precondition you did not know about, and it belongs in the write-up.

Target end state: one paragraph of prose, one code block under twenty lines, one
command.

### 8. Do the patch analysis

This half is not optional, and for most readers it is the more valuable half.
Read `references/patching.md` in full before writing this section. It covers:

- the bug-class-to-correct-fix table (injection, traversal, deserialization,
  memory safety, authz, SSRF, TOCTOU, SSTI, supply chain, agent tool abuse), and
  which plausible-looking fixes silently fail for each;
- the four layers of a fix (virtual patch, mitigation, real fix, class
  elimination) and which clock each runs on;
- how to write a fix that holds: patch at the trust boundary, fail closed,
  separate rather than escape, never denylist, ship the regression test in the
  same commit, grep for siblings;
- how to *prove* a patch holds, which is more than re-running the original
  payload;
- backporting, rollout sequencing, and removing the temporary control;
- how to audit **someone else's** patch, which is what a repro blog usually needs.

The governing principle: prefer a fix that makes the bad state unrepresentable
over one that detects and rejects it. Parameterized queries beat sanitizing
because there is no string to get wrong. Every check you add is a check someone
can later reach around.

### 9. Write the defensive assertion

What control would have caught this, at what layer, and what would it cost? Walk
input validation, architecture, detection (write the actual Sigma or Suricata
rule and test it against your own negative control so you can report false
positives honestly), and supply chain.

Then name at least one control that **fails**, and why. The negative result is
usually the most interesting paragraph in the post, because it is the one readers
cannot get anywhere else.

### 10. Assemble evidence and write it up

Publish enough that a skeptical reader can verify without trusting you:
`run.json` from a clean run, a full transcript, an environment manifest, hashes
of every artifact with its source URL, and copy-pasteable commands in order.
Include the failed attempts; "I first assumed the trigger was the header, it is
actually the trailing null" saves readers a day and signals real work.

`references/writeup.md` has the section structure, the voice rules, and the
pre-publication checklist. Status and scope goes first, always: a reader must
know within ten seconds that this is a patched issue and that you did not build a
weapon.

## Running things

Per this user's standing rule, **do not execute reproduction harnesses
yourself.** Write them, then hand over the exact command and state what a pass
looks like: which marker appears, which decision is logged, what the exit code
means. The same applies to the helper scripts here; write the invocation, let the
user run it.

## Files

- `references/sourcing.md` — where to look for advisories, patches, PoCs,
  detections and fix guidance, tiered by trustworthiness. Read when starting a
  new target or when sources disagree.
- `references/harness-pattern.md` — lab layout, container hardening, safety
  checklist, and the four-cell harness skeleton to copy.
- `references/patching.md` — bug classes and their correct fixes, the four fix
  layers, writing and validating a patch, backporting, auditing someone else's
  fix. Read whenever the work touches the fix.
- `references/writeup.md` — blog/whitepaper structure, voice, failure modes that
  mark an amateur, and the pre-publication checklist.
- `scripts/triage.py` — one-shot NVD + CVE.org + OSV pull with a patched verdict.
- `scripts/fetch_nvd.py`, `fetch_cve.py`, `fetch_osv.py`, `check_patched.py` —
  single-source fetchers.
- `scripts/minimize.py` — delta-debugging reducer for shrinking a trigger.
- `assets/harness_template.py` — runnable four-cell harness to copy into a repro.
