# AI writing assistance: what to disclose

Primary source: ACL 2023 Program Chairs (Jordan Boyd-Graber, Naoaki Okazaki, Anna
Rogers), "ACL 2023 Policy on AI Writing Assistance", published 2023-01-10,
https://2023.aclweb.org/blog/ACL-2023-policy/

The ACL policy remains the clearest statement of the reasoning in the field, and other
venues (NeurIPS, ICML, ICLR) have converged on compatible positions. Always check the
current call for papers of the venue you are submitting to, since specific wording and
checklist questions change year to year. Use this file for the reasoning and the default
answers; use the venue's own page for the binding text.

## The mechanism

ACL 2023 added a question about writing assistants to the mandatory Responsible NLP
Checklist (which originated at NAACL 2022). If such tools were used in any way, authors
must elaborate on the scope and nature of that use.

Three things about this that matter for how you advise the user:

1. It is not a desk-reject trigger. Like the questions about releasing code, releasing
   data, compensating participants, and IRB approval, the point is author reflection and
   norm-setting, not automatic punishment.
2. Answers are disclosed to reviewers, who may flag a paper for case-by-case ethics
   review if they see a problem.
3. At ACL 2023 the answers were also published as appendices to accepted papers,
   comparable to Nature's reporting summaries. So write the answer as something a public
   reader will see.

The underlying concerns are concrete: errors in model output, plagiarism of sources in
the training data, and authorship. ACM's definition of plagiarism covers not only
verbatim and near-verbatim copying but intentional paraphrasing of another's work.
Reviewers volunteer their time and should not be expected to check for these problems on
the authors' behalf.

## The six cases, and what each requires

**Language assistance only (paraphrasing, polishing your own content).** No disclosure
required. This is treated like Grammarly, spell checkers, dictionaries, and thesauruses,
which have been acceptable for years. The stated caveat is worth passing on: authors who
are not fluent enough to notice when generated output drifts from their intended meaning
can end up worse off than with simpler but more accurate English.

**Short-form input assistance (predictive keyboards, smart compose).** No disclosure
required. Nobody objected to these because generating long, unique, coherent text this
way is impractical.

**Literature search.** Allowed. Models may be used as search assistants to identify
relevant work. You are expected to read and discuss what you cite, exactly as with a
search engine or a recommendation tool. Normal standards for citation accuracy and
thoroughness of the literature review apply, and suggested citations carry possible
biases. Practically: everything in `references/hallucination-audit.md` applies, and this
is the case that most often produces fabricated references.

**Low-novelty text (generated descriptions of widely known concepts).** Disclose where
it was used. You must also convince reviewers that the generation was checked for
accuracy and carries relevant citations, using block quotes for anything verbatim. If
the generation reproduces existing text, cite both the source of the text and the source
of the idea.

**New ideas from the model.** Acknowledge the use of the model, on the reasoning that a
human colleague contributing at this level would get co-authorship or an
acknowledgement. Also check for known prior sources for those ideas and cite them,
because most likely they came from someone else's work in the training data.

**New ideas plus new text.** Discouraged. A contributor of both ideas and their
execution matches the definition of a co-author, which a model cannot be. If you go this
route anyway, you are welcome to make the case to reviewers that it should be allowed
and that the content is correct, coherent, original, and not missing citations. Note the
open question ICML raised: it is not settled who would hold credit for generated text,
the model developers, the authors of the training data, or the user who prompted it.

## Code assistants

Code is supplementary material, which reviewers may check but are not obliged to.
Norms around Copilot and similar tools are not fully established. The ACL 2023 ask:

- Acknowledge the use and its scope in the README of the code attachment or repository.
- Check for potential plagiarism. Copilot in particular was at the time the subject of a
  piracy lawsuit, and may suggest snippets under licenses incompatible with yours.
- Using a code assistant does not reduce the authors' responsibility for the correctness
  of their methods and results.

A README line for this looks like:

```
## AI assistance
Parts of the training and evaluation harness in `src/train/` and `src/eval/` were
written with GitHub Copilot / Claude Code assistance. All generated code was reviewed
and tested by the authors, who are responsible for its correctness. We checked
generated snippets against their likely sources for license compatibility.
```

## Drafting the checklist answer

Be specific about scope and nature. Vague answers invite scrutiny; precise ones close
the question. A usable template:

```
We used [tool] for [specific purpose] in [specific sections]. Specifically:
- [e.g., grammar and phrasing improvements to Sections 1 and 6, on text we wrote]
- [e.g., initial drafts of the background paragraphs in Section 2.1, which we then
  verified against the cited sources and rewrote]
All content was verified by the authors, who take responsibility for its accuracy. All
references were checked against [ACL Anthology / arXiv / publisher records]. No research
ideas, experimental designs, analyses, or conclusions were generated by these tools.
```

If the honest answer is "language polishing only", say that and say nothing more. Do not
over-disclose into sounding like the model wrote the paper when it did not.

## Reviewing

ACL 2023 issued a separate policy on AI assistance in writing reviews. If the user is
writing reviews rather than papers, point them to the current venue policy before they
paste anything into a model, since review text is confidential material belonging to the
authors and submitting it to a third-party service may itself violate the venue's
confidentiality terms independent of any authorship question.
