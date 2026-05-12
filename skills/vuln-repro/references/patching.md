# Patching

The other half of the discipline. A repro without a patch analysis is a bug
report; a repro with one is engineering. This file is what to do once the harness
goes green.

Contents:
1. Classify the bug
2. Bug class to correct fix
3. The four layers of a fix
4. Writing a fix that holds
5. Proving the patch actually holds
6. Backporting and rollout
7. Documenting the fix
8. Auditing someone else's patch
9. Regression tests
10. Anti-patterns

---

## 1. Classify the bug

You cannot choose a fix until you name the class, because each class has a small
set of fixes that work and a large set that look like they work. Get the class
from the patch diff and the data flow, not from the CVE prose or the CWE number,
both of which are assigned at a distance and are often approximate.

Three questions identify almost any class:

1. **What invariant was supposed to hold?** ("this path stays under the root",
   "this string is never parsed as SQL", "this object belongs to this user")
2. **Where did untrusted input cross into a place that assumed trust?** That
   crossing is the trust boundary, and it is where the fix belongs.
3. **Was the failure a missing check, or a check that could be reached around?**
   Missing checks get checks. Reachable-around checks need the design changed,
   because adding a second check just moves the race.

---

## 2. Bug class to correct fix

| Class | Invariant that broke | Fixes that hold | Fixes that fail |
|---|---|---|---|
| **SQL / NoSQL injection** | Data crossed into the query grammar | Parameterized queries / prepared statements; ORM binding | Escaping quotes; blocking keywords; stripping `'` |
| **Command injection** | Data crossed into the shell grammar | `execve` with an argv array, no shell; absolute binary paths | Quoting; `shlex.quote` on a string you then concatenate; denylisting `;` and `` ` `` |
| **Prompt injection / agent tool abuse** | Untrusted content was read as instructions | Provenance labels carried through the context; capability scoping per tool; egress decision keyed on data class; human confirmation for irreversible actions | "Ignore instructions in the document" in the system prompt; classifier-only filtering; trusting model self-report |
| **Path traversal** | Resolved path escaped the root | `realpath()` then verify the prefix; `openat` on a root fd with `O_NOFOLLOW`; index by opaque id instead of a filename | Stripping `..`; regex on the input; checking before normalization |
| **Deserialization** | Untrusted bytes chose the code that ran | Change format to data-only (JSON + schema); if impossible, a strict class allowlist | Class denylists; "we removed the known gadget"; signing without verifying before parse |
| **XXE / entity expansion** | Parser followed references in untrusted input | Disable external entities and DTDs at parser construction; use a hardened parser by default project-wide | Filtering `<!ENTITY` in the input |
| **SSTI** | A template was compiled from user data | Never compile untrusted strings; pass them as context to a fixed template; sandboxed engine only as depth | Escaping template delimiters |
| **XSS** | Data crossed into the HTML/JS grammar | Context-aware output encoding at render; a framework that encodes by default; CSP as depth | Input sanitizing at intake; a regex denylist of `<script>` |
| **Buffer overflow** | A write left its allocation | Bounds check at the boundary; checked APIs; move the parser to a memory-safe language | Increasing the buffer size; checking after the copy |
| **Integer overflow** | Arithmetic wrapped before the bounds check | Checked arithmetic; wider types; validate operands before the operation | Checking the result for negativity |
| **Use-after-free / double free** | Lifetime assumption violated | Ownership discipline; null after free plus a state machine; a safe language | Adding a "is it freed" flag checked non-atomically |
| **AuthN bypass** | Identity was assumed, not proven | Verify at the point of use, not only at the entry point; fail closed on any parse or lookup error | Trusting a header, a cookie value, or a client-supplied role |
| **AuthZ / IDOR** | The object was reachable without an ownership check | Scope the query to the principal so unauthorized objects are not in the result set | Adding an `if user.id != obj.owner: 403` at one of nine call sites |
| **SSRF** | An outbound destination came from the request | Allowlist destinations; re-resolve and check the IP *after* DNS to defeat rebinding; use a dedicated egress proxy | Blocking `127.0.0.1` and `169.254.169.254` by string; checking the hostname before resolution |
| **Race / TOCTOU** | State changed between check and use | Make check and use one atomic operation; operate on the handle, not the name; `O_EXCL`, compare-and-swap, a transaction | Shortening the window; adding a second check; sleeping |
| **CSRF** | A cross-origin request carried ambient authority | `SameSite` cookies plus a per-session token verified server side | Checking `Referer` only |
| **Cryptographic misuse** | A primitive was used outside its contract | Use a vetted high-level library; authenticated encryption; constant-time comparison; unique nonces | Rolling your own mode; `==` on a MAC |
| **Supply chain** | An artifact was trusted by name | Pin by integrity hash; verify provenance/attestation; quarantine by publication age; vendor allowlist for names | Pinning a version tag only; trusting a lockfile you never verify |
| **Secrets exposure** | A secret was reachable from a lower-trust context | Rotate first, then remove; move to a secret manager with short-lived credentials; scope the credential down | Deleting the commit; adding it to `.gitignore` |
| **Denial of service** | Unbounded work from bounded input | Bound the input, the recursion depth, and the time; stream instead of buffering; reject before allocating | Raising the timeout |

**The governing principle: prefer a fix that makes the bad state unrepresentable
over one that detects and rejects it.** Parameterized queries beat sanitizing
because there is no string left to get wrong. Scoped queries beat permission
checks because the object never enters the result set. Every check you add is a
check someone can later reach around, forget at a new call site, or get wrong
under a different encoding.

---

## 3. The four layers of a fix

Real incident response runs several of these at once, on different clocks. Naming
the layer prevents the common failure where a team ships a WAF rule, feels done,
and never fixes the code.

**Layer 1 — Virtual patch (minutes to hours).** WAF rule, egress policy, feature
flag off, config change, proxy filter, network segmentation. Buys time. Almost
always blocks a payload *shape* rather than the behavior, so it is bypassable by
construction. Give it an owner and an expiry date in writing, or it becomes
permanent, rots, and eventually breaks something legitimate that nobody can
explain.

**Layer 2 — Mitigation (hours to days).** Reduce blast radius without fixing the
flaw: drop privileges, sandbox the component, narrow a token's scope, add rate
limiting, disable the vulnerable feature by default, add the detection rule. Good
mitigations outlive the fix and keep paying off against the *next* bug in the
same component, which is why they are worth doing even after the real fix ships.

**Layer 3 — The real fix (days).** Change the code so the invariant cannot break.
Section 2 applies here.

**Layer 4 — Class elimination (weeks to quarters).** Make the whole class
impossible: a type that cannot be misused, a lint that fails the build, a wrapper
that becomes the only permitted way to call the dangerous API, a memory-safe
rewrite of the parser, provenance types that will not compile if untrusted data
reaches an instruction sink. This is what separates teams that fix bugs from
teams that stop having them.

For a write-up, walking a reader down all four layers for one CVE is unusually
valuable, because most posts stop at layer 3 while most readers need layer 1
today and layer 4 next quarter.

---

## 4. Writing a fix that holds

In rough order of importance:

1. **Fix at the trust boundary.** Ask where the data stops being untrusted. Patch
   there, once. A fix scattered across nine call sites will be incomplete at the
   tenth, which someone adds next month and nobody reviews as security-relevant.
2. **Fail closed.** On parse failure, unknown input, timeout, or exception:
   deny. A fix whose error path allows is not a fix, and error paths are exactly
   what an attacker steers you into.
3. **Separate rather than escape.** Escaping requires you to model the consumer's
   grammar perfectly and forever, including the next version of the consumer.
4. **Never denylist.** A denylist encodes the payloads you thought of.
5. **Preserve the interface, or version it explicitly.** A security fix that
   silently breaks legitimate callers gets rolled back, and then you have the
   vulnerability again plus a political problem that makes the second attempt
   harder.
6. **Keep the fix small and obviously correct.** A reviewer must be able to see
   the invariant now holds. Refactoring goes in a separate commit; mixing them is
   how a fix gets reverted wholesale during an incident.
7. **Ship the regression test in the same commit.** The test is your minimized
   reproducer. See section 9.
8. **Grep for siblings before closing.** The same mistake almost always appears
   more than once. Most "incomplete fix" CVEs exist because nobody did this.
9. **Consider what the fix costs.** Latency, compatibility, false positives,
   operational burden. State it. A fix nobody can afford to deploy is not a fix.

---

## 5. Proving the patch actually holds

Applying the patch and re-running the original payload proves almost nothing:
that test passes both for a correct fix and for a fix that only blocks your exact
string. Do all four.

**Original payload blocked.** Necessary, not sufficient.

**Semantic variants blocked.** Re-express the same payload and try again:
different encoding (URL, double URL, HTML entity, base64 where the sink decodes),
case variation, unicode normalization forms and homoglyphs, overlong UTF-8,
alternate separators, whitespace and null bytes, nesting and recursion, chunked
or multipart framing, and the same input arriving through a different entry
point. If a variant gets through, you patched the payload, not the bug.

Scope note: doing this against **your own patch on your own build** is
validation and is in scope. Doing it against the **vendor's unfixed** code is
discovery and is not. If a variant reveals an unpatched sibling in shipping code,
that is a new finding: report it privately to the vendor, keep it out of the blog
post until it is fixed.

**Benign traffic still works.** Run the project's own test suite plus functional
cases for the feature you touched. A fix with false positives gets reverted, and
the revert is usually done by someone who does not understand the security
context.

**The invariant, written down.** One sentence: "after this change, X is
guaranteed because Y." If you cannot write that sentence, you do not yet
understand the fix, and you should not ship it.

Then re-run the four-cell table:

| Cell | Input | Version | Expected |
|---|---|---|---|
| Positive | malicious | vulnerable | marker fires |
| Negative control | benign | vulnerable | no marker |
| Patch control | malicious | patched | no marker, explicit refusal |
| Patch functional | benign | patched | works normally, no regression |

The fourth cell is the one people skip and the one that decides whether the fix
survives contact with production.

---

## 6. Backporting and rollout

- **Enumerate every supported branch.** The fix must land on all of them or the
  advisory is wrong and users on an LTS line are silently exposed.
- **Backport the minimal change,** not the refactor around it. Older branches
  lack the surrounding changes, and a large backport is how you introduce a new
  bug during an incident, at the worst possible moment for review quality.
- **Re-run the harness per branch.** Different code, different result. Assume
  nothing carries over.
- **Sequence the rollout:** virtual patch everywhere → canary the real fix →
  fleet rollout → **remove the virtual patch and confirm the harness still
  reports blocked**. That last step is universally skipped and is how teams
  discover the real fix never actually deployed.
- **Define the rollback trigger before deploying,** with a named metric and a
  named owner.
- **Look backwards.** Once you have a detection signature, run it over retained
  logs for the window between introduction and fix. "Were we exploited?" is a
  separate question from "are we fixed?", and only the signature answers it.

---

## 7. Documenting the fix

Whether you are the maintainer or a researcher writing it up:

- Affected version range, precisely, and the fixed version.
- What the fix changes in behavior, **including anything legitimate that now
  breaks**. Burying this is how you get reverted.
- The workaround for people who cannot upgrade today: that is your layer 1.
- The detection signature, so defenders can look backwards.
- Credit to the reporter, and the disclosure timeline.
- If the first fix was incomplete, say so loudly and issue a new identifier.
  Quietly strengthening a patch under the old CVE leaves everyone who already
  "patched" wrong and unaware.

---

## 8. Auditing someone else's patch

This is what a repro blog usually needs, and almost nobody does it, which is why
it is the most respected part of a good write-up. Answer three questions in the
post:

1. **Does the fix address the mechanism or the payload?** Read the diff. A new
   regex or a new string check is a yellow flag. A changed data flow, a
   parameterized call, a resolved-then-verified path, or a scoped query is a green
   one.
2. **Is the fix at the right boundary?** Or did they patch one call site among
   several? Grep for siblings. Report responsibly: an unpatched sibling goes to
   the vendor privately.
3. **What does the fix not cover, by the vendor's own admission?** Advisories
   frequently say "this does not address X" or "customers using Y remain
   affected". Quote it. Readers need it, and it is the part that gets lost when
   the news cycle summarizes the advisory.

Also worth checking: did the project add a regression test? A fix with no test is
a fix that will regress. Whether one exists is a fair and useful observation
about the project's security posture, stated neutrally.

---

## 9. Regression tests

The regression test is where the repro and the patch meet, and it is the durable
artifact. Properties of a good one:

- **It is your minimized trigger**, not the original PoC.
- **It asserts the refusal, not the absence of a crash.** "Did not segfault" is
  satisfied by a thousand wrong behaviors.
- **It is fast and hermetic** enough to run on every commit, or it will be
  disabled within a quarter.
- **It carries the CVE id and a one-line explanation in a comment**, so the next
  person does not "simplify" it away.
- **It includes the benign case** alongside the malicious one, so a future
  over-broad fix that breaks functionality also fails the test.

If you are writing up someone else's CVE, offering an upstream regression test as
a PR is a genuinely useful contribution and a good way to have the write-up taken
seriously.

---

## 10. Anti-patterns

- **Patching the payload.** A regex against the published PoC string. Ships fast,
  fails to the first variant, and creates false confidence that ends the
  remediation effort.
- **Fixing at the wrong layer and calling it done.** A WAF rule with no code fix
  behind it.
- **Adding a check instead of removing the possibility.** Especially for races,
  where a second check just moves the window.
- **Denylists**, in any form, as the primary control.
- **Silent strengthening under the old CVE.** Everyone who "patched" is now wrong
  and does not know it.
- **Fixing without a test.** It regresses. It always regresses.
- **Not grepping for siblings.** The most common cause of incomplete-fix CVEs.
- **Not removing the temporary control**, so nobody ever learns the real fix
  failed to deploy.
- **Rotating nothing after a secret exposure.** Removing the secret from the repo
  does not un-disclose it.
- **Treating CVSS as the priority.** Use CISA KEV and EPSS for exploitation
  reality, and your own architecture for blast radius. A 9.8 in a component you
  do not expose matters less than a 6.5 on your edge.
