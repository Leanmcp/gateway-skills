# Prose rules

These are the user's house rules for anything that will appear in a submitted paper.
They are stricter than general good writing advice, and that is deliberate: reviewers
read fast, and every unnecessary word spends attention that the actual contribution
needs.

## No em dashes, anywhere

Zero. Not in the abstract, not in figure captions, not in the appendix, not in the
rebuttal.

An em dash almost always marks a sentence whose structure was never decided. The fix is
to decide. Look at what the dash is actually doing and use the punctuation that says it:

| The dash is doing this | Use instead |
|---|---|
| Joining two independent statements | A period, or a semicolon if they are genuinely one thought |
| Introducing an explanation or a list | A colon |
| Setting off an aside | Commas, or parentheses if it is truly parenthetical |
| Setting off an aside you did not want to cut | Cut it, or promote it to its own sentence |
| Trailing off, adding an afterthought | Delete the afterthought |

The last row is the common case. Text after an em dash is frequently something the
author added because they were not confident the preceding claim landed. Strengthen the
claim instead.

En dashes stay where they are correct: numeric ranges (pages 12-18 typeset as 12–18),
and compound author names in citation styles that use them. Hyphens in compound
modifiers are fine. The rule is about the em dash and about the habit it represents.

Do not swap one crutch for another. A draft where every em dash became a semicolon has
not improved.

## No fluff

Delete on sight, unless the word is carrying real technical content in that sentence:

*Novel, cutting-edge, state-of-the-art (as an adjective for your own work), powerful,
seamless, robust (unless you measured robustness), significantly (unless you ran a
significance test and report it), very, quite, really, extremely, highly, deeply, truly,
fundamentally, essentially, basically, arguably, notably, remarkably, interestingly,
importantly, crucially, clearly, obviously, evidently, naturally, simply, just, various,
numerous, a wide range of, a plethora of, myriad, leverage (say "use"), utilize (say
"use"), delve into, shed light on, pave the way, open the door, unlock, harness,
revolutionize, transformative, game-changing, holistic, comprehensive (unless the
coverage is actually exhaustive and you say what the bound is), rich, nuanced,
sophisticated, elegant, intricate, tapestry, landscape, realm, in today's world, it is
worth noting that, it should be emphasized that, it is important to note that, as
mentioned earlier, in order to (say "to"), due to the fact that (say "because"), a
number of (say "some" or give the number).*

Also cut these structural tics:

- Sentences that announce what the next sentence will do ("In this section, we first
  describe X, then Y."), unless the section is long enough that the reader genuinely
  needs a map. Under two pages, they do not.
- Restating the abstract in the introduction, and restating the introduction in the
  conclusion. Each should say something the other does not.
- "We believe", "we argue that", "we hypothesize" attached to something you actually
  demonstrated. State the result.
- Hedge stacking: "may potentially suggest", "could possibly indicate". One hedge is
  honest, two is evasion. Keep the strongest single hedge that is still true.

## Ask twice

Every sentence gets two questions before it survives.

**Does the reader learn something here they did not already have?** Information already
carried by the abstract, an earlier section, a table, or the figure it sits under is not
new. Delete rather than reword.

**Is this the shortest honest form?** "Honest" is doing real work in that sentence. The
short form must not overclaim, and it must not drop the caveat that makes the claim
true. Compressing "improves accuracy by 2.1 points on three of five datasets" into
"improves accuracy" fails this test even though it is shorter.

Apply the same test one level up, to paragraphs and to whole subsections. An entire
related-work paragraph that only establishes "other people have worked on this" is a
sentence, not a paragraph.

## Replace vague with specific

The rewrite that most improves a paper is replacing an evaluative adjective with the
measurement behind it.

- "significantly outperforms" -> "outperforms by 3.4 F1 (p < 0.01, paired bootstrap, n=5 seeds)"
- "is much faster" -> "runs in 0.8x the wall-clock time on the same hardware"
- "a large dataset" -> "1.2M examples"
- "works well across domains" -> name the domains and give the spread
- "recent work" -> cite it, with the year

If you cannot supply the specific, that is a signal the claim is not yet supported. Do
not paper over it with a stronger adjective. Flag it for the user under "could not
verify".

## Voice and tense

- Active voice by default. Passive is fine when the actor genuinely does not matter
  ("the model was trained for 3 epochs"), and reads better than contorting to avoid it.
- "We" for what the authors did. Not "the authors" or "this paper", which read as
  distancing.
- Present tense for what the paper and the method do, past tense for what you ran.
- One term per concept. If it is a "retriever" in Section 3, it is not a "retrieval
  module" in Section 5. Synonym variation is a virtue in prose and a defect in a paper,
  because the reader cannot tell whether you mean the same thing.

## Mechanical pass

`scripts/check_prose.py` flags em dashes, the filler list, stacked hedges, and a few
citation-shaped problems. It is a filter, not a judge: it will miss context-dependent
fluff and will flag the occasional legitimate use. Do the reading pass yourself and use
the script to catch what your eye slid over.

Per the user's global rule, do not execute it. Hand over the command:

```
python ~/.claude/skills/research-paper-integrity/scripts/check_prose.py path/to/paper.tex
```
