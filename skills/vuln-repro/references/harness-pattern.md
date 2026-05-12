# Harness pattern

The lab layout, the safety checklist, and a four-cell harness to copy.

## File layout

```
<incident>-repro/
├── README.md              # status/scope, run command, safety statement
├── harness.py             # self-contained, stdlib-only where possible
├── docker-compose.yml     # only when OS isolation must be enforced
├── fixtures/
│   ├── payload.txt        # the minimal trigger, as data not code
│   └── benign.txt         # the negative control input
└── results/
    └── run.json           # saved decision transcript, committed
```

Use the Docker variant when the mechanism involves real code execution or an OS
primitive. For policy, path, parsing, or config mechanisms a stdlib Python
harness is enough, easier to audit, and far more likely to still run in two
years.

## Non-negotiable properties

- **Self-contained.** Stdlib only if you can manage it. Every dependency is a
  thing that will have rotted when someone tries to re-run you.
- **Deterministic.** Same input, same decision, every run. If the bug is a race,
  run it N times, report the hit rate, and say so explicitly rather than
  pretending it is deterministic.
- **Two named code paths**, `vulnerable_*` and `patched_*`, so the diff is
  legible in the harness itself and not only in the upstream repo.
- **Structured output** to `results/run.json`, not just stdout.
- **Non-zero exit when the contrast does not hold.** The harness is a test. It
  must fail loudly when the story it tells stops being true.

## Container hardening

```yaml
services:
  vulnerable-app:
    build: ./vulnerable
    network_mode: none          # no egress, period
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 512m
    pids_limit: 128
    tmpfs: [/tmp]
```

If the mechanism genuinely needs a network hop (SSRF, exfiltration), replace
`network_mode: none` with an `internal: true` bridge and a loopback sink
container that only logs request bodies. Never host networking. Never egress.

Isolate the whole lab: ephemeral VM, no host mounts, no credentials on the box,
no VPN to anything real. Total compromise of the lab should cost a
`docker compose down`.

## Pinning

- Artifact by hash, not tag: commit SHA, npm integrity hash, `--hash=sha256:` in
  requirements, or a vendored tarball with a recorded checksum. Put the hash in
  the README so readers can verify they have your bytes.
- Runtime: language version, libc, OS. A heap overflow that works on glibc 2.31
  may not on 2.35; a deserialization bug behaves differently across Python 3.8
  and 3.12.
- Config: the exact settings, and the *default* too, because "only exploitable if
  you had enabled X" is important to readers.
- Noise off: ASLR, JIT, auto-update, telemetry, network timeouts.

## Safety checklist

- [ ] Publicly disclosed AND vendor-patched or withdrawn, with sources.
- [ ] Vulnerable version is the last public release before the fix, from a normal
      public channel.
- [ ] No network egress except a `127.0.0.1` sink, or none at all.
- [ ] Every dangerous verb replaced by an inert, greppable marker.
- [ ] Secrets are decoys (`not-a-real-secret-...`); addresses use `.invalid`.
- [ ] Escape and destructive steps asserted via path math, never performed.
- [ ] Undisclosed mechanism steps left out of scope and stated in the README.
- [ ] Deterministic, or hit rate reported honestly.
- [ ] Non-zero exit if the four-cell contrast does not hold.

## The four cells

| Cell | Input | Version | Expected |
|---|---|---|---|
| Positive | malicious | vulnerable | marker fires |
| Negative control | benign | vulnerable | no marker |
| Patch control | malicious | patched | no marker, explicit refusal |
| Patch functional | benign | patched | works normally, no regression |

Positive alone proves nothing. The negative control separates "the bug fired"
from "my harness always writes the marker". The patch functional cell separates a
fix that ships from a fix that gets reverted.

## Log fields worth standardizing

Log the same fields in every repro so a body of work becomes comparable and maps
onto a real policy engine:

`source` (trusted / untrusted_content) · `data_class` (synthetic_private /
ordinary) · `outbound_channel` (loopback / none / internal) · `decision` (allow /
block / review_required) · `policy_id` · `reason`.

## Skeleton

A runnable version lives at `assets/harness_template.py`. Copy it and replace the
two code paths; the four-cell scaffolding, the marker discipline, the JSON
transcript, and the exit-code contract are already correct.
