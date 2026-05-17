# Style: professional

Measured, credible, precise. The register you would use writing to a colleague at another company whom you respect but do not know well.

This is the default for LinkedIn, company accounts, academic announcements, and anything a hiring manager, reviewer, or investor might read.

## The trap

"Professional" is the register AI writing defaults to, which means this style has the highest risk of sounding generated. Corporate-neutral and AI-generated are nearly the same voice. Getting this right requires more discipline than the casual styles, not less.

The difference between professional and corporate is that professional has an author. It makes claims, states preferences, admits limits, and occasionally disagrees with the reader. Corporate avoids all four.

## Rules

- Full sentences, standard capitalisation, standard punctuation.
- Contractions are fine and make it read as human. "We don't" not "We do not", unless the emphasis is deliberate.
- First person. "We built" and "I found", not "It was determined that". Passive voice is the fastest route to sounding institutional.
- Specific nouns and real numbers. This is what carries the credibility, not the vocabulary.
- One opinion per piece, minimum. Something you would defend.
- One stated limit, minimum.
- Paragraphs of two to four sentences. Varied sentence length.
- No emoji. No exclamation marks, or one at most across the whole piece.
- Zero to two hashtags.
- Zero em dashes.

## Words this style does not use

The entire vocabulary list in `references/anti-ai-tells.md` is disproportionately dangerous here, because these are exactly the words that feel appropriately professional. Leverage, robust, seamless, comprehensive, pivotal, innovative, streamline, empower, holistic.

Replace each with the specific thing. "Leveraged our existing infrastructure" becomes "ran it on the three machines we already had". The second is more professional, not less, because it contains information.

## Structure

1. The concrete situation or problem. Two or three sentences.
2. What was done, with specifics.
3. The result, measured, with the conditions stated.
4. The limitation or the open question.
5. Credit and link.

No preamble, no summary paragraph at the end.

## Example

```
Our evaluation suite gave us almost nothing to work with when a task failed.
The output was a stack trace and whatever remained in the terminal buffer,
which in practice meant re-running the full suite to find out what the model
had done at the step that broke. Roughly three hours each time.

We now write every turn to disk as the run happens: tool calls with arguments,
results, reasoning traces, token counts, and per-episode artifacts. A failed
run is read back as a transcript rather than reconstructed.

The result we did not expect is that most of what we had classified as model
failures were not. Our harness had a hardcoded 30-second timeout, and steps
on longer reasoning chains were exceeding it silently. That single change
accounted for a larger share of our failure rate than any prompt work we had
done.

The runner handles about 40 episodes in parallel on one machine. The viewer
is a terminal interface rather than a web dashboard, which is a deliberate
tradeoff and one some people will find limiting.

What we have not solved is comparing runs across providers. Trace structures
differ enough between OpenAI and Anthropic that every unified representation
we have tried misrepresents one of them.

Repository linked in the comments. Built with [Name] and [Name].
```

About 1,100 characters. Professional, no AI tells, and it contains four things a generated version would not: a real number, an admission that they had been wrong about their own failure classification, a tradeoff volunteered against their own interest, and an unsolved problem.

## Where it fits

| Platform | Fit |
|---|---|
| LinkedIn | default |
| Medium / Substack | default for the body |
| YouTube description | default |
| X / Twitter | works, though lowercase often fits better |
| Discord (own server) | slightly formal but fine for announcements |
| Discord (other servers) | too formal, use lowercase or builder-technical |
| Instagram | usually too stiff |
