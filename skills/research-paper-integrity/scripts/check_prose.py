#!/usr/bin/env python3
"""Mechanical checks for paper drafts: em dashes, filler, hedge stacking, bib hygiene.

Usage:
    python check_prose.py paper.tex [section.tex ...] [refs.bib]
    python check_prose.py --dir paper/           # all .tex, .md, .bib under a directory

This catches the violations that are boring to find by eye. It does not judge whether a
claim is supported or whether a citation is real; that needs reading. See
references/hallucination-audit.md.

Exit code is 1 if anything was flagged, 0 otherwise, so it can be wired into a
pre-submission check.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EM_DASH_PATTERNS = [
    ("em dash (U+2014)", re.compile(r"\u2014")),
    ("horizontal bar (U+2015)", re.compile(r"\u2015")),
    (r"LaTeX '---'", re.compile(r"---")),
    (r"LaTeX \emdash", re.compile(r"\\emdash\b")),
]

FILLER = [
    "novel", "cutting-edge", "state-of-the-art", "powerful", "seamless", "robustly",
    "significantly", "very", "quite", "really", "extremely", "highly", "deeply",
    "truly", "fundamentally", "essentially", "basically", "arguably", "notably",
    "remarkably", "interestingly", "importantly", "crucially", "clearly", "obviously",
    "evidently", "naturally", "simply", "various", "numerous", "plethora", "myriad",
    "leverage", "leveraging", "utilize", "utilizing", "delve", "shed light",
    "pave the way", "open the door", "unlock", "harness", "revolutionize",
    "transformative", "game-changing", "holistic", "comprehensive", "nuanced",
    "sophisticated", "elegant", "intricate", "tapestry", "landscape", "realm",
    "in today's world", "it is worth noting", "it should be emphasized",
    "it is important to note", "as mentioned earlier", "in order to",
    "due to the fact that", "a number of", "a wide range of", "we believe that",
]

HEDGES = [
    "may", "might", "could", "possibly", "potentially", "perhaps", "seemingly",
    "arguably", "somewhat", "relatively", "suggests", "appears to", "tends to",
]

# "significantly" without any nearby evidence of an actual test
SIG_TEST = re.compile(r"p\s*[<=>]|p-value|bootstrap|t-test|wilcoxon|mann-whitney|"
                      r"permutation test|confidence interval|\bCI\b", re.I)

BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)
BIB_FIELD = re.compile(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", re.S)
CITE_CMD = re.compile(r"\\[a-zA-Z]*cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")

TEX_COMMENT = re.compile(r"(?<!\\)%.*$")


class Report:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, int, str]] = []

    def add(self, kind: str, path: Path, line: int, msg: str) -> None:
        self.items.append((kind, str(path), line, msg))

    def render(self) -> str:
        if not self.items:
            return "No mechanical issues found. Content and citations still need a read."
        out = []
        by_kind: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        for kind, path, line, msg in self.items:
            by_kind[kind].append((path, line, msg))
        for kind in sorted(by_kind, key=lambda k: -len(by_kind[k])):
            rows = by_kind[kind]
            out.append(f"\n## {kind}  ({len(rows)})")
            for path, line, msg in rows[:200]:
                loc = f"{path}:{line}" if line else path
                out.append(f"  {loc}: {msg}")
            if len(rows) > 200:
                out.append(f"  ... and {len(rows) - 200} more")
        out.append(f"\nTotal flagged: {len(self.items)}")
        return "\n".join(out)


def strip_comments(line: str, is_tex: bool) -> str:
    return TEX_COMMENT.sub("", line) if is_tex else line


def snippet(line: str, pos: int, width: int = 60) -> str:
    start = max(0, pos - width // 2)
    return ("..." if start else "") + line[start:start + width].strip() + "..."


def check_prose_file(path: Path, rep: Report) -> None:
    is_tex = path.suffix == ".tex"
    text = path.read_text(encoding="utf-8", errors="replace")
    for n, raw in enumerate(text.splitlines(), 1):
        line = strip_comments(raw, is_tex)
        if not line.strip():
            continue
        low = line.lower()

        for label, pat in EM_DASH_PATTERNS:
            for m in pat.finditer(line):
                rep.add("Em dashes (remove all)", path, n,
                        f"{label}: {snippet(line, m.start())}")

        for word in FILLER:
            pat = re.compile(r"\b" + re.escape(word) + r"\b" if " " not in word
                             else re.escape(word))
            for m in pat.finditer(low):
                if word == "significantly" and SIG_TEST.search(line):
                    continue
                rep.add("Filler and vague words", path, n,
                        f"'{word}': {snippet(line, m.start())}")

        # hedge stacking: two or more hedges in one clause
        found = [h for h in HEDGES if re.search(r"\b" + re.escape(h) + r"\b", low)]
        if len(found) >= 2:
            rep.add("Stacked hedges (keep one)", path, n,
                    f"{', '.join(found)}: {line.strip()[:80]}")

        # long sentences are usually two sentences
        for sent in re.split(r"(?<=[.!?])\s+", line):
            words = len(sent.split())
            if words > 45:
                rep.add("Very long sentence (probably two)", path, n,
                        f"{words} words: {sent.strip()[:80]}...")


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: dict[str, dict[str, str]] = {}
    for m in BIB_ENTRY.finditer(text):
        etype, key, body = m.group(1).lower(), m.group(2).strip(), m.group(3)
        fields = {k.lower(): v.strip() for k, v in BIB_FIELD.findall(body + "\n")}
        fields["__type__"] = etype
        entries[key] = fields
    return entries


def check_bib_file(path: Path, rep: Report) -> dict[str, dict[str, str]]:
    entries = parse_bib(path)
    titles: Counter[str] = Counter()
    for key, f in entries.items():
        missing = [x for x in ("title", "author", "year") if x not in f]
        if missing:
            rep.add("Bib entry missing core fields", path, 0,
                    f"{key}: missing {', '.join(missing)}")

        if not any(k in f for k in ("doi", "url", "eprint", "archiveprefix", "pages")):
            rep.add("Bib entry with no locator (verify it exists)", path, 0,
                    f"{key}: no doi, url, eprint, or pages. Confirm against ACL "
                    f"Anthology / arXiv / publisher.")

        year = f.get("year", "")
        if year and not re.fullmatch(r"\d{4}", year.strip("{} ")):
            rep.add("Bib entry with odd year", path, 0, f"{key}: year={year!r}")

        venue = (f.get("booktitle") or f.get("journal") or "").lower()
        if "arxiv" in venue or f.get("__type__") == "misc":
            rep.add("Preprint citation (check for a published version)", path, 0,
                    f"{key}: cited as preprint")

        t = re.sub(r"\W+", " ", f.get("title", "")).strip().lower()
        if t:
            titles[t] += 1
    for t, c in titles.items():
        if c > 1:
            rep.add("Duplicate bib entries (same title)", path, 0,
                    f"{c} entries titled '{t[:60]}'")
    return entries


def check_citations(tex_files: list[Path], entries: dict[str, dict[str, str]],
                    rep: Report, bib_path: Path | None) -> None:
    cited: set[str] = set()
    for p in tex_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        for n, raw in enumerate(text.splitlines(), 1):
            line = strip_comments(raw, True)
            for m in CITE_CMD.finditer(line):
                for key in m.group(1).split(","):
                    key = key.strip()
                    if not key:
                        continue
                    cited.add(key)
                    if entries and key not in entries:
                        rep.add("Cited key not in .bib", p, n, key)
    if entries and bib_path:
        for key in sorted(set(entries) - cited):
            rep.add("In .bib but never cited", bib_path, 0, key)


def collect(paths: list[str], as_dir: bool) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if as_dir or path.is_dir():
            for suf in (".tex", ".md", ".bib"):
                out.extend(sorted(path.rglob(f"*{suf}")))
        else:
            out.append(path)
    return [p for p in out if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help=".tex/.md/.bib files, or a directory")
    ap.add_argument("--dir", action="store_true", help="treat paths as directories")
    args = ap.parse_args()

    files = collect(args.paths, args.dir)
    if not files:
        print("No .tex/.md/.bib files found.", file=sys.stderr)
        return 1

    rep = Report()
    prose = [f for f in files if f.suffix in (".tex", ".md")]
    bibs = [f for f in files if f.suffix == ".bib"]

    for f in prose:
        check_prose_file(f, rep)

    entries: dict[str, dict[str, str]] = {}
    for f in bibs:
        entries.update(check_bib_file(f, rep))

    tex = [f for f in prose if f.suffix == ".tex"]
    if tex:
        check_citations(tex, entries, rep, bibs[0] if bibs else None)

    print(f"Checked {len(prose)} prose file(s), {len(bibs)} bib file(s), "
          f"{len(entries)} bib entries.")
    print(rep.render())
    print("\nReminder: this is mechanical only. Unsupported claims and fabricated "
          "citations need a human trace, see references/hallucination-audit.md.")
    return 1 if rep.items else 0


if __name__ == "__main__":
    sys.exit(main())
