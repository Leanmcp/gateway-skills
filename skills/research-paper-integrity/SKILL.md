---
name: research-paper-integrity
description: Standards and audits for writing academic papers, especially ML/NLP submissions to NeurIPS, ICML, ICLR, ACL, EMNLP, NAACL. Covers the author's house prose rules (zero em dashes, zero fluff, every sentence earns its place), verification of hallucinated claims and hallucinated or malformed bibliography entries, the ACL policy on AI writing assistance and what must be disclosed, and best practices for paper structure, experiments, reproducibility checklists, and rebuttals. Use this skill whenever the user is drafting, editing, polishing, restructuring, or reviewing a paper, abstract, intro, related work, rebuttal, or camera-ready; whenever they ask to "clean up" or "tighten" academic writing; whenever citations or a .bib file need checking; and whenever they ask what has to be disclosed about AI assistance. Reach for it even when the user only says "make this section better", "check my references", or "is this ready to submit".
---

# Research paper integrity

This skill is the index. Each area below lives in its own reference file so you only
load what the current task needs. Read the file before acting on that area, not after,
because these rules change what you write rather than how you check it afterwards.

## What lives where

| Area | File | Read it when |
|---|---|---|
| Prose rules: no em dashes, no fluff, necessity test | `references/writing-style.md` | Writing or editing any prose the user will submit |
| Hallucination audit: unsupported claims, fake or wrong citations, bib hygiene | `references/hallucination-audit.md` | Any draft has claims or references that were not hand-verified |
| AI assistance disclosure (ACL 2023 policy and its logic) | `references/ai-writing-policy.md` | The user asks what to disclose, fills a responsible-NLP checklist, or used a model for text, ideas, or code |
| Conference craft: structure, experiments, figures, rebuttals, checklists | `references/conference-writing.md` | Planning a paper, restructuring sections, prepping a submission or rebuttal |

`scripts/check_prose.py` is a fast mechanical pass for em dashes, banned filler,
hedge stacking, and suspicious bib entries. It catches the boring violations so your
attention goes to the ones that need judgment. Per the user's global rule, do not run
it yourself: write it into the relevant workspace if needed and hand over the exact
command.

## The three commitments

Everything in this skill reduces to three things the user cares about. Keep them in
mind even when you have only loaded this index.

**1. The text contains no em dashes and no filler.** Not because em dashes are wrong
in general, but because in this user's papers they signal a sentence that was never
restructured, and filler signals a claim that was never sharpened. Replace an em dash
with a period, a colon, a comma, or parentheses, whichever the actual logic calls for.
Details and the filler list are in `references/writing-style.md`.

**2. Every sentence has been asked twice whether it needs to exist.** First pass: does
this sentence carry information the reader does not already have? Second pass: if it
does, is this the shortest honest form of it? A paragraph that survives both passes is
usually a third shorter than the draft. Cutting is the main editing operation here, not
rewording.

**3. Nothing is asserted that has not been checked, and no reference is cited that has
not been confirmed to exist.** Fabricated citations and confidently wrong numbers are
the two failure modes that end a paper's credibility, and both look completely normal
in a draft. Treat every number, every "prior work shows", and every bib entry as
unverified until you have traced it. Procedure in `references/hallucination-audit.md`.

## Default workflow when handed a draft

Adapt this, do not perform it mechanically. If the user asked only for a citation
check, do only that.

1. Read the draft fully before changing anything. Local edits made without the whole
   argument in mind are how papers lose their thread.
2. Run the hallucination audit first. There is no point polishing a sentence built on a
   claim that turns out to be unsupported, and finding a broken citation early changes
   what the surrounding paragraph should say.
3. Then the prose pass: cut, de-fluff, remove em dashes, tighten.
4. Then structure: does each section do the job `references/conference-writing.md`
   describes, in the order a reviewer reads.
5. Report what you changed and, separately, what you could not verify. The second list
   matters more than the first. Never quietly leave an unverifiable claim in place
   without flagging it.

## How to report

Give the user the edited text plus a short audit section. Something like:

```
## Changes
- Cut 4 sentences from the intro that restated the abstract
- Removed 11 em dashes, restructured the 3 sentences that needed it
- Section 4.2: "significantly improves" -> stated the actual delta and the test

## Could not verify (needs your call)
- [Smith 2021] claimed for the pretraining result: no paper by that name found in
  ACL Anthology or arXiv. Either the citation is wrong or the claim needs a source.
- Table 2 baseline number differs from the number quoted in Section 5.
```

Flagging honestly is the whole value here. A silent pass that leaves a fabricated
citation in place is worse than no pass at all, because it launders the error.
