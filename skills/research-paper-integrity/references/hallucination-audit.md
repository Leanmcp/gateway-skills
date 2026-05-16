# Hallucination audit

Two failure modes end a paper's credibility, and both are invisible in a clean-looking
draft: a claim that nothing supports, and a citation to a paper that does not exist or
does not say what you attributed to it. Reviewers who catch either one stop trusting
everything else, including the parts that were correct.

Assume nothing has been verified until you traced it. This applies most strongly to
text that a model helped produce, but human drafts fail the same way, usually from
half-remembered results.

## Pass 1: claim audit

Go through the draft and mark every sentence that asserts something checkable. In
practice these are:

- Numbers: dataset sizes, parameter counts, accuracies, runtimes, costs, dates.
- Attributions: "X et al. showed", "prior work found", "it is known that".
- Comparatives: "the first to", "unlike previous approaches", "the largest", "no
  existing method".
- Definitions and characterizations of other people's methods.
- Anything about a model, benchmark, or system's properties that you did not measure.

For each one, establish which of these it is:

| Status | What to do |
|---|---|
| Traced to your own experiment output | Confirm the number in the draft matches the number in the logs or results file, not just approximately |
| Traced to a source you read | Fine. Confirm the source says what you claim, not something adjacent |
| Traced to a source you only saw the title of | Not verified. Read the abstract at minimum, ideally the relevant section |
| Not traceable | Flag it. Either find the source, weaken it to what you can support, or cut it |

Superlatives ("the first", "the only", "the largest") deserve extra suspicion because
they are unfalsifiable-feeling and trivially falsified by one reviewer who knows the
area. Prefer "to our knowledge, the first" only when you actually searched, and say
where you searched if the claim is load-bearing.

Cross-check numbers for internal consistency too. Abstract vs. results table, table vs.
the sentence describing it, totals that should add up, percentages that should sum to
100, dataset counts quoted in two places. Inconsistency between two places in your own
paper is the single most common thing a careful reviewer finds.

## Pass 2: bibliography audit

For every entry in the .bib file and every `\cite` in the text.

**Does the work exist?** Search for the exact title. Fabricated references usually look
plausible: real authors who work in the area, a real venue, a real-sounding title, a
year that fits. That plausibility is exactly why they survive a casual read. Confirm
against a real record: ACL Anthology, arXiv, DBLP, Semantic Scholar, OpenReview, or the
publisher. A Google Scholar result page you did not open is not confirmation.

**Do the fields match the real record?**
- Author list complete and spelled correctly, including diacritics.
- Title matches exactly, including subtitle.
- Year matches the version you mean. Papers commonly have an arXiv year and a
  proceedings year that differ.
- Venue is the real one. Citing the arXiv preprint of something that appeared at ACL
  three years ago is a small error that reviewers do notice.
- DOI or ACL Anthology ID resolves.

**Does it support the sentence citing it?** This is the check people skip. Open the
paper and confirm the specific claim. A citation attached to a claim the paper does not
make is a misattribution even if the reference is real, and it is more embarrassing than
a broken link because it implies you cited without reading.

**Is anything cited but absent, or present but never cited?** Both mean the reference
list drifted from the text. Also check for duplicate entries under different keys, which
is what happens when a bib file was assembled from several sources.

## Pass 3: red flags that mean look harder

These do not prove fabrication, but each one is worth a direct check:

- A citation with no DOI, no arXiv ID, no URL, and no page numbers.
- Round numbers presented as measurements ("improves by exactly 5%").
- A reference whose author list is a plausible mix of well-known names in the field who
  have never actually co-authored.
- A venue and year combination that does not exist (a workshop that ran in different
  years, a conference edition that was cancelled or virtual).
- Text describing a method in generic terms that would fit any paper in the area. This
  often means the description was generated from the title rather than the paper.
- A related-work paragraph where every citation is from the same two years, or where
  the citations are suspiciously evenly spread. Real reading has clumps.
- Numbers quoted for a baseline that do not appear in the baseline's own paper. Check
  whether you are quoting a reproduction, and if so say so.

## Reporting

Never silently fix and move on. The user needs to know what was wrong so they can judge
whether the underlying argument still holds. Report in three buckets:

```
## Verified
23 of 31 references confirmed against ACL Anthology / arXiv, fields corrected on 4.

## Wrong, corrected
- [vaswani2017] year was 2018, corrected to 2017; venue was arXiv, corrected to NeurIPS.
- Section 4: "1.5M examples" contradicted Table 1 ("1.2M"); Table 1 matches the data
  loading code, so the text was changed.

## Could not verify (your call)
- [chen2023contrastive] "Contrastive Alignment for Low-Resource Retrieval", EMNLP 2023:
  no such paper in the Anthology or arXiv. The claim in Section 2 depends on it.
- Section 5.1 says the method is "the first to combine X and Y". I found no
  counterexample, but I also cannot establish it. Suggest softening or dropping.
```

A claim you could not verify stays flagged. Do not resolve uncertainty by rewording it
into something vaguer that sounds defensible; that hides the problem instead of solving
it.

## When the draft was model-assisted

Everything above applies harder, and there is a disclosure question on top of it. See
`references/ai-writing-policy.md` for what has to be declared and what does not.
