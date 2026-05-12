#!/usr/bin/env python3
"""
<Incident name> (CVE-XXXX-YYYY) — <one-line mechanism>.

Status:   publicly disclosed <date>, fixed by <vendor> in <version> (<link>).
Lab:      offline, loopback-only, synthetic markers, decoy secrets.
Scope:    <the undisclosed step you are NOT reconstructing, stated plainly>.

Run:      python3 harness.py
Pass:     all four cells match expectations; exit code 0.
Fail:     exit code 1 — the contrast this repro claims does not hold.

This harness performs no dangerous action. Every capability the original bug
provided is represented by an inert marker or an assertion.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# Greppable, impossible to produce by accident. Regenerate per repro.
MARKER = "REPRO-MARKER-1f4c9a2e-REPLACE-ME"

# Decoys only. RFC 6761 reserves .invalid so it can never resolve.
DECOY_SECRET = "not-a-real-secret-1f4c9a"
DECOY_RECIPIENT = "recipient@example.invalid"

MALICIOUS = {"synthetic": True, "payload": "<the minimal trigger>"}
BENIGN = {"synthetic": True, "payload": "<ordinary input, same shape>"}


def _record(policy, decision, marker, reason, **extra):
    """Standard log shape so repros stay comparable and map onto a policy engine."""
    return {
        "policy": policy,
        "source": "untrusted_content",
        "data_class": "synthetic_private",
        "outbound_channel": "loopback" if marker else "none",
        "decision": decision,
        "policy_id": extra.pop("policy_id", "none"),
        "marker": marker,
        "reason": reason,
        **extra,
    }


def vulnerable(fixture):
    """
    The pre-fix code path.

    Model the disclosed mechanism only. When the real bug executed code, wrote
    outside a sandbox, or exfiltrated data, represent that here by returning
    MARKER — never by performing the action. For an escape, compute the escaped
    path and assert it rather than writing to it.
    """
    triggered = "<the condition the flaw failed to check>" in str(fixture["payload"])
    return _record(
        "vulnerable",
        decision="allow" if triggered else "allow",
        marker=MARKER if triggered else None,
        reason=("no provenance/bounds check, so untrusted input reached the sink"
                if triggered else "benign input, nothing to trigger"),
    )


def patched(fixture):
    """
    The post-fix code path.

    If you are modelling a vendor fix whose details were not published, say so in
    the module docstring and describe this as a plausible class of fix, not as
    the vendor's fix. Conflating the two is the central error of this genre.
    """
    triggered = "<the condition the flaw failed to check>" in str(fixture["payload"])
    if triggered:
        return _record("patched", decision="block", marker=None,
                       policy_id="<the check the fix added>",
                       reason="<what the fix verifies, and why the invariant now holds>")
    return _record("patched", decision="allow", marker=None,
                   policy_id="<the check the fix added>",
                   reason="benign input passes the new check; no functional regression")


CELLS = [
    # name,               fn,          fixture,   expect_marker, expect_decision
    ("positive",          vulnerable,  MALICIOUS, True,          "allow"),
    ("negative_control",  vulnerable,  BENIGN,    False,         "allow"),
    ("patch_control",     patched,     MALICIOUS, False,         "block"),
    ("patch_functional",  patched,     BENIGN,    False,         "allow"),
]


def main():
    os.makedirs(RESULTS, exist_ok=True)
    out, failures = {}, []

    for name, fn, fixture, want_marker, want_decision in CELLS:
        r = fn(fixture)
        out[name] = r
        got_marker = r["marker"] is not None
        ok = got_marker == want_marker and r["decision"] == want_decision
        if not ok:
            failures.append(
                f"{name}: expected marker={want_marker} decision={want_decision}, "
                f"got marker={got_marker} decision={r['decision']}")
        print(f"[{'ok ' if ok else 'FAIL'}] {name:18} "
              f"decision={r['decision']:6} marker={'yes' if got_marker else 'no ':3} "
              f"{r['reason']}")

    with open(os.path.join(RESULTS, "run.json"), "w") as f:
        json.dump(out, f, indent=2)

    if failures:
        print("\nFAIL: the four-cell contrast does not hold.")
        for f_ in failures:
            print(f"  - {f_}")
        print("Do not publish this run. Either the model is wrong or an "
              "assumption changed.")
        sys.exit(1)

    print("\nPASS: vulnerable fires, benign is inert, the patch refuses the "
          "malicious input and still serves the benign one.")
    print(f"transcript: {os.path.join(RESULTS, 'run.json')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
