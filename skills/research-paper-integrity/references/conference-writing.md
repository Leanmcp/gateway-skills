# Writing for top conferences

Applies to NeurIPS, ICML, ICLR, ACL/EMNLP/NAACL, and the adjacent venues. The details
differ (page limits, checklists, anonymity windows) but the reviewing dynamics are the
same, and those dynamics are what should shape the writing.

## What the reviewer actually does

A reviewer has several papers and limited hours. The realistic reading pattern is:
title, abstract, figure 1, the results table, the conclusion, then back to the
introduction if still interested. They form a tentative accept/reject opinion within ten
minutes and spend the rest of the time looking for evidence for it.

Two consequences shape everything below. First, the contribution must be legible from
the abstract, figure 1, and the main table alone. Second, the reasons a paper gets
rejected are usually not "the idea is bad" but "I could not tell what was new", "the
baselines are weak", "the claim is broader than the experiments", and "I do not believe
this would reproduce".

## Structure, by what each part must accomplish

**Title.** Says what the paper does. Not a pun that requires reading the abstract to
decode.

**Abstract, roughly 150-200 words.** Problem, why existing approaches fall short, what
you do, the headline result with an actual number, and the scope of the claim. No
citations, no forward references, no "we show promising results".

**Introduction, about one page.** The job is to get an informed reader to the
contribution without making them wait. A structure that works:

1. The problem and why it matters, in two or three sentences. No "in today's world".
2. The specific gap. Concrete, and fair to prior work, because the authors of that prior
   work are likely reviewing you.
3. What you do, at the level of mechanism, not just outcome.
4. Results, with numbers.
5. A contributions list, three to four items, each one a thing you did, not a thing you
   observed about the field.

The introduction should not restate the abstract in longer form. It should add the
reasoning the abstract had no room for.

**Related work.** Organize by how the prior work relates to yours, not chronologically
and not one-paper-per-sentence. Each paragraph should end with the reader knowing what
that line of work does not do that you do. Be accurate about others' methods: reviewers
who wrote those papers will check, and a mischaracterization costs more credibility than
the paragraph was worth. Place it after the introduction, or after the method if the
method is hard to appreciate without context.

**Method.** Notation defined before use, and consistent throughout. State the actual
mechanism, including the parts that are ugly. Design choices that came from tuning
should be described as such rather than justified post hoc, because reviewers can tell
and because it is an easy thing to be honest about. If there is a figure that makes the
method clear, it is figure 1 and it appears on page 1 or 2.

**Experiments.** Baselines are where papers are won and lost. Include the strongest
current method, not the convenient one. Tune baselines with the same budget you gave
your own method, and say what that budget was; a reviewer who suspects otherwise will
say so and you cannot recover in a rebuttal. Report multiple seeds with variance,
because a single-seed result on a small benchmark is not evidence. Report the cases
where your method does not win, since a paper that names its own limits reads as more
trustworthy, and the reviewer will find them anyway. Ablate the components you claim
matter. If you claim three things contribute, ablate three things.

**Analysis.** This is what separates an accept from a borderline. Explain why the method
works, with evidence. Qualitative examples, error breakdowns, behaviour under
distribution shift, failure cases. A results table plus "our method outperforms
baselines" is a workshop paper.

**Limitations.** Required at ACL venues, and expected at the others in the checklist.
Write real ones. "We only evaluated on English", "the method needs a labelled dev set of
about 500 examples", "we did not test above 7B parameters". Reviewers reward candour
here and punish "our method requires more compute, which we leave to future work" when
the obvious limitation went unmentioned.

**Conclusion.** Short. What was shown and what it implies. Not a summary of the paper's
structure.

## Figures and tables

- The reader must understand a figure from the figure and its caption alone. Captions
  should be full sentences saying what to conclude, not "Results on dataset X".
- Font size in figures at least as large as the body text after scaling. Check the
  printed PDF, not the notebook.
- Colour must survive greyscale and the common colour vision deficiencies. Vary line
  style and marker as well as hue.
- Bold the best number in a table, define what bold means in the caption, and say what
  the error bars are (std over seeds? confidence interval? over what?).
- Every table and figure is referenced in the text, and the text says what to see in it.

## Claims and scope

Match the claim to the evidence. This is the single most common source of reviewer
frustration and the easiest to fix. If you evaluated on three English datasets, the
claim is about three English datasets. Overclaiming in the abstract and then hedging in
Section 5 does not resolve; reviewers read it as bait.

Statistical claims need statistics. "Significantly" is a technical word. If you write
it, report the test, the sample, and the p-value. If you have not run a test, use a
different word.

## Reproducibility

The checklists (NeurIPS's, and the Responsible NLP Checklist at ACL venues) are graded
by reviewers as a signal of care. Cover, either in the paper or the appendix:

- Hyperparameters, search space, and how the final values were selected.
- Compute: hardware, and total runtime including the failed runs, not just the final one.
- Dataset details: source, size, splits, license, preprocessing, and language(s).
- Number of runs and how variance is reported.
- Model versions and API dates if closed models are involved, since results are not
  reproducible without them.
- Code and data availability, or a concrete statement of why not.

Also fill in the AI assistance question, see `references/ai-writing-policy.md`.

## Ethics, broader impact, anonymity

- Write the broader impact section about your actual system's plausible uses, not a
  general essay about AI risk.
- Human subjects or annotators: report compensation, recruitment, and IRB status.
- Respect the anonymity period. No preprint announcements, no repository with your name
  in the git history, no non-anonymous links in the submission.

## Rebuttals

- Answer the question actually asked, first sentence. Reviewers skim rebuttals too.
- Lead with new evidence. An experiment you ran during the rebuttal period moves scores;
  restating what the paper already said does not.
- Concede what is right. "Reviewer 2 is correct that our baseline was undertuned; we
  reran with matched budget and the gap narrows to 1.2 points, which we have added as
  Table 4." This gains more than defending it.
- Group shared concerns into one response rather than repeating yourself per reviewer.
- Keep the tone flat regardless of the review's tone. Irritation is legible in text and
  costs points.
- State exactly what will change in the camera-ready, and then change it.

## Before submitting

- The abstract and the results table tell the same story with the same numbers.
- Every claim in the abstract is supported by a specific section.
- Every citation exists and says what you attributed to it, per
  `references/hallucination-audit.md`.
- No em dashes, no filler, per `references/writing-style.md`.
- Page limit met without shrinking margins or fonts, which desk-rejects.
- Anonymized, including the PDF metadata and the supplementary zip.
- Checklists answered honestly, including AI assistance.
- The paper compiles from a clean checkout of the source you are submitting.
