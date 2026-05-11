# Harness pattern

The house pattern for a safe vulnerable-vs-patched reproduction. Copy this;
adapt the mechanism.

## File layout

```
<incident>-repro/
├── harness.py            # self-contained, stdlib-only, runs both paths
├── README.md             # status/scope, run command, safety statement
└── results/
    └── run.json          # saved decision transcript (git-tracked or .gitkeep)
```

Use a Docker variant (with `network_mode: none`) only when OS-level isolation
must actually be enforced (e.g. real code execution). For policy/path/config
mechanisms, a stdlib Python harness is enough and is easier to audit.

## Safety checklist (every harness)

- [ ] The issue is publicly disclosed AND vendor-patched/withdrawn.
- [ ] No network egress except a `127.0.0.1` loopback sink (or none at all).
- [ ] Every dangerous verb replaced by an inert marker (writes a fixed string).
- [ ] Secrets/targets are decoys: `not-a-real-secret`, `*.invalid`.
- [ ] Destructive/escape steps are asserted via path math, never performed.
- [ ] Undisclosed mechanism steps are left out of scope, stated in the README.
- [ ] Deterministic: same input → same decision every run.
- [ ] Non-zero exit if the vulnerable/patched contrast does not hold.

## Skeleton

```python
"""
<Incident> (CVE-XXXX-YYYY) — <one-line mechanism>. Offline, loopback, synthetic.
Fixed by vendor in <version>. <what is explicitly out of scope>.
Run: python3 harness.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

def vulnerable(fixture):
    # model the disclosed failure: the marker fires / the unsafe path is chosen
    return {"policy": "vulnerable", "decision": "allow", "marker": True,
            "reason": "<why the flaw let this through>"}

def patched(fixture):
    # the vendor's fix: same input, refused
    return {"policy": "patched", "decision": "block", "marker": False,
            "reason": "<what the fix checks>"}

def main():
    os.makedirs(RESULTS, exist_ok=True)
    fixture = {"synthetic": True}
    out = {"vulnerable": vulnerable(fixture), "patched": patched(fixture)}
    for k, v in out.items():
        print(f"[{k}] decision={v['decision']} marker={v['marker']} {v['reason']}")
    with open(os.path.join(RESULTS, "run.json"), "w") as f:
        json.dump(out, f, indent=2)
    ok = out["vulnerable"]["marker"] and not out["patched"]["marker"]
    print(f"\n{'PASS' if ok else 'FAIL'}: vulnerable fires, patched refuses.")
    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

## Gateway-relevant log fields

Record these so the reproduction maps onto an intent-classification gateway:
`source` (trusted/untrusted_content), `data_class` (synthetic_private/ordinary),
`outbound_channel` (loopback/none), `decision` (allow/block/review), `policy_id`,
and a short human-readable `reason`.
```
