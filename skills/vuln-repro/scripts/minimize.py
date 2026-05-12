#!/usr/bin/env python3
"""
minimize.py — delta-debugging reducer (ddmin) for shrinking a trigger.

Takes an input file and a test command. The command must exit 0 when the
vulnerability still fires against the candidate input, and non-zero when it does
not. minimize.py then repeatedly removes chunks and keeps whatever still fires,
producing the smallest input it can find.

This is workflow step 7. A published PoC is usually 200 lines of scaffolding
around the handful of bytes that matter; finding those bytes is the part readers
value, and it is mechanical enough to automate.

Usage:
    python3 minimize.py --input payload.txt --out minimal.txt \
        --test './harness.sh {}'

  {} in the test command is replaced with the path to the candidate file. If
  omitted, the candidate path is appended as the last argument.

Options:
    --mode bytes|lines   granularity of reduction (default: lines)
    --timeout SECONDS    per-test timeout (default: 60)
    --verbose

Safety: this only runs the command you give it, against your own local harness.
Point it at a repro harness, never at a live target.
"""
import argparse
import os
import shlex
import subprocess
import sys
import tempfile


def run_test(cmd, data, mode, timeout, verbose):
    suffix = ".bin" if mode == "bytes" else ".txt"
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode())
        full = cmd.replace("{}", shlex.quote(path)) if "{}" in cmd \
            else f"{cmd} {shlex.quote(path)}"
        try:
            r = subprocess.run(full, shell=True, timeout=timeout,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok = r.returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
        if verbose:
            size = len(data)
            print(f"  test size={size} -> {'FIRES' if ok else 'no'}", file=sys.stderr)
        return ok
    finally:
        os.unlink(path)


def ddmin(units, joiner, test):
    """Classic ddmin over a list of units (lines or byte chunks)."""
    n = 2
    while len(units) >= 2:
        chunks = [units[i * len(units) // n:(i + 1) * len(units) // n] for i in range(n)]
        reduced = False
        # try each subset
        for c in chunks:
            if c and test(joiner(c)):
                units, n, reduced = c, 2, True
                break
        if not reduced:
            # try each complement
            for i, c in enumerate(chunks):
                comp = [u for j, ch in enumerate(chunks) if j != i for u in ch]
                if comp and test(joiner(comp)):
                    units, n, reduced = comp, max(n - 1, 2), True
                    break
        if not reduced:
            if n >= len(units):
                break
            n = min(n * 2, len(units))
    return units


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--test", required=True,
                   help="command that exits 0 when the bug still fires; {} = candidate path")
    p.add_argument("--mode", choices=["bytes", "lines"], default="lines")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    raw = open(a.input, "rb").read()
    if a.mode == "lines":
        units = raw.split(b"\n")
        joiner = lambda us: b"\n".join(us)
    else:
        units = [raw[i:i + 1] for i in range(len(raw))]
        joiner = lambda us: b"".join(us)

    def test(data):
        return run_test(a.test, data, a.mode, a.timeout, a.verbose)

    print(f"[minimize] baseline: {len(raw)} bytes, {len(units)} {a.mode}")
    if not test(raw):
        raise SystemExit(
            "[minimize] the test command does NOT report the bug on the original input.\n"
            "            Fix the oracle first: it must exit 0 when the bug fires.")

    result = joiner(ddmin(units, joiner, test))
    open(a.out, "wb").write(result)
    pct = 100 * (1 - len(result) / max(len(raw), 1))
    print(f"[minimize] reduced {len(raw)} -> {len(result)} bytes ({pct:.1f}% smaller)")
    print(f"[minimize] wrote {a.out}")
    print("[minimize] re-run the full four-cell harness on the minimized input before "
          "publishing it.")


if __name__ == "__main__":
    main()
