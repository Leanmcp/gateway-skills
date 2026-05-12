# The write-up

## Structure

1. **Status and scope.** CVE id, affected range, fix version, and what is
   explicitly out of scope. First section, no exceptions. A reader must know
   within ten seconds that this is a patched issue and that you did not build a
   weapon. This protects you and it is what a serious audience checks first.
2. **One-paragraph summary.** What breaks, why it matters, one sentence of
   mechanism.
3. **Background.** Only the system knowledge needed to follow the mechanism.
   Resist explaining the whole product; readers skip it and it dilutes the post.
4. **The mechanism.** The real content. Annotated code, the patch diff, and the
   causal chain from untrusted input to violated invariant.
5. **The lab.** Environment, pins, harness, run command, expected output.
6. **The contrast.** All four cells with actual output pasted in.
7. **The fix.** What the vendor changed, whether it addresses the mechanism or
   the payload, what it does not cover, and what the layer-1 workaround is for
   people who cannot upgrade today. See `patching.md`.
8. **The defensive assertion.** Which control catches it, at which layer, at what
   cost, and at least one control that **fails** and why. The negative result is
   usually the best paragraph in the post.
9. **Safety limits.** Offline, loopback, synthetic markers, decoy secrets, no
   live targets, destructive steps asserted not performed.
10. **Sources.** Primary links only, with the tier each came from.

## Voice

Write what you observed, not what you assume. Distinguish "the advisory states"
from "I verified". When you infer, say you inferred. When you could not verify
something, say that too. Precision about your own uncertainty is the entire
currency of this genre, and it is the thing readers use to decide whether to
trust the rest.

Include the failed attempts. "I first assumed the trigger was the header; it is
actually the trailing null in the query string" saves readers a day and signals
that you did the work rather than transcribing a PoC.

Match impact claims to what the marker actually proved. If your marker was a file
write in a container running as `nobody` with no network, say that, not "full
RCE". Overclaiming is the fastest way to lose the audience you want.

Do not reprint a CVSS score without saying what it assumes about deployment.

## What to publish and what not to

Publishing a minimal reproducer against a patched version is standard practice
and is what regression tests look like anyway. Publishing a turnkey, evasive,
multi-target tool is a different act with different consequences, and readers
judge you on which one you chose.

If validation surfaced an unpatched sibling, it goes to the vendor privately and
stays out of the post until it is fixed.

## Failure modes that mark an amateur

- **No patch control.** You showed a thing happened, not that it was the CVE.
- **No negative control.** Your harness might fire on anything.
- **Unpinned environment.** Nobody can re-run you in six months.
- **Reasoning from the CVE description instead of the patch.** CVE text is
  written at a distance and is frequently wrong about the mechanism.
- **Trusting NVD version ranges** without checking the vendor and the commits.
- **Transcribing a PoC without minimizing it.** You copied; you did not
  understand.
- **Silent scope creep into bug hunting.** The moment you are trying inputs the
  disclosure never mentioned to see what else breaks, you are doing something
  else under different rules.
- **Skipping the fix analysis.** Half the value, routinely left on the table.
- **Live-fire testing** against anything you do not own. There is no version of
  this that is fine.

## Pre-publication checklist

**Legitimacy**
- [ ] Publicly disclosed, primary source cited.
- [ ] Vendor-patched or withdrawn, fix version or notice cited.
- [ ] Vulnerable version is the last public release before the fix.
- [ ] No step reconstructs an undisclosed mechanism; anything that would is named
      out of scope in writing.
- [ ] No live target, no real credential, no real recipient, no third-party host.

**Rigor**
- [ ] All four cells run and reported.
- [ ] Deterministic, or hit rate reported honestly.
- [ ] Every artifact pinned by hash; environment manifest captured.
- [ ] Mechanism explained from the patch diff.
- [ ] Payload minimized; scaffolding removed.

**Patching**
- [ ] Bug class named, fix matches the class.
- [ ] Fix analyzed at the trust boundary, not payload-shaped.
- [ ] Semantic variants of your own payload also blocked by the patch.
- [ ] Patch functional cell passes.
- [ ] The invariant written as one sentence.
- [ ] Siblings grepped for; anything unpatched reported privately.
- [ ] Layer-1 workaround given.

**Safety**
- [ ] Dangerous verbs replaced by inert markers.
- [ ] Decoy secrets, `.invalid` addresses.
- [ ] Escape and destructive steps asserted, never performed.
- [ ] Egress disabled or loopback-only.
- [ ] Harness exits non-zero when the contrast fails.

**Publication**
- [ ] Status and scope is the first section.
- [ ] Impact claims match what the marker proved.
- [ ] At least one control named that fails, and why.
- [ ] Safety limits stated plainly.
- [ ] Primary sources only, linked.
- [ ] No weaponized, evasive, or multi-target form published.
