# Worked example: academic paper launch

A full multi-channel treatment of one paper. The paper below is illustrative and the numbers are placeholders. What matters is the shape of each piece and the translation from paper language into channel language.

**The paper (fictional):** "Timeout-Induced Failure Attribution in Agentic Evaluation Harnesses". Finding: across three public agent benchmarks, 31% of reported model failures were harness timeouts rather than model errors, and correcting for this changes the published ranking of two of the five models evaluated.

---

## Step 1: The translation

Before writing anything, answer these three in plain language.

**What did people believe before?** That published agent benchmark scores measure model capability.

**What did you find?** A large share of recorded failures were the evaluation infrastructure timing out, not the model failing. Fixing that reorders the leaderboard.

**What changes?** Anyone reporting agent benchmark numbers needs to log per-step wall time and separate infrastructure failures from model failures, or their rankings may be wrong.

Every piece below is built from those three sentences. The abstract is never used.

---

## Step 2: X thread

Post 1 (with the main figure attached):
```
we re-ran three public agent benchmarks with per-step timing instrumentation

31% of the recorded "model failures" were our harness timing out, not the
model failing

correcting for it reorders 2 of the 5 models
```

Post 2:
```
the setup: agent benchmarks record a task as failed when the episode doesn't
reach a terminal state. nothing distinguishes "the model did the wrong thing"
from "the runner gave up at 30s"

so we instrumented wall time per step across every episode
```

Post 3:
```
the distribution is the giveaway. model failures are spread across step
durations. infra failures pile up in a spike right at whatever the timeout
value is

once you see the spike you can't unsee it
```

Post 4:
```
the effect isn't uniform, which is the problem. reasoning models with longer
chains hit the ceiling more often, so the bias systematically penalises
exactly the models the benchmark is meant to evaluate
```

Post 5:
```
what we couldn't do: we only had the harness configs for 3 of the benchmarks
we wanted. for the other two we're inferring timeout values from the failure
distribution, which is suggestive, not proof
```

Post 6:
```
limitations, stated plainly:

single hardware config. we didn't vary the timeout to find the threshold
where the effect disappears. and we have no way to check closed evaluation
harnesses at all
```

Post 7:
```
paper: <arxiv link>
code + the instrumented harness: <repo>
with @handle @handle @handle
```

Note: post 5 is a negative result and post 6 states limitations before a reviewer does. Both increase credibility with a research audience, and both are the kind of content generated copy never contains.

---

## Step 3: LinkedIn post

LinkedIn's audience is broader than X's. Fewer of them run evaluations. Lead with the implication, not the method.

```
We re-ran three public agent benchmarks with timing instrumentation on every
step, expecting to confirm the scores. Instead we found that 31% of what those
benchmarks recorded as model failures were our evaluation harness giving up
before the model finished.

The distinction matters because it is not evenly distributed. Models that
reason in longer chains hit the timeout more often, which means the harness
was systematically penalising the behaviour the benchmark exists to measure.
Correcting for it changes the relative ranking of two of the five models we
looked at.

The detection method is simple enough that anyone can check their own setup.
Model failures spread out across step durations. Infrastructure failures
cluster in a spike at whatever your timeout value is. If you plot per-step
wall time and see that spike, some share of your reported scores is measuring
your runner.

What we cannot claim: this is one hardware configuration, and we only had
harness configs for three of the five benchmarks we wanted. For the other two
we are inferring timeout values from the failure distribution, which is
suggestive rather than conclusive. We also have no way to inspect closed
evaluation harnesses, which is where most reported numbers now come from.

Preprint and the instrumented harness are in the comments.

With [Co-author], [Co-author] and [Co-author] at [Institution].
```

About 1,450 characters. Tag every co-author and the institution. Put the arXiv link in the first comment, posted immediately.

**What was deliberately avoided:** the abstract, the paper title as the hook, "we propose", "novel", "extensive experiments", any claim of SOTA, a closing question, hashtags beyond two, and any em dash.

---

## Step 4: LinkedIn document carousel

Ten slides, 1080 x 1350, exported as a single PDF. Large type.

| Slide | Content |
|---|---|
| 1 | "31% of agent benchmark failures were our own timeouts" as the full-bleed headline. Not the paper title. |
| 2 | The problem: one sentence plus a diagram of an episode reaching the timeout mid-step |
| 3 | What benchmarks currently record, and what they cannot distinguish |
| 4 | The method: per-step wall-time instrumentation, one diagram |
| 5 | The key figure: two failure distributions side by side, with the timeout spike labelled |
| 6 | The correction: ranking before and after, as a simple table |
| 7 | Why it is biased: longer reasoning chains hit the ceiling more often |
| 8 | Limitations, written out plainly |
| 9 | How to check your own harness, three steps |
| 10 | Authors, affiliations, arXiv link, repo link |

Slide 1 is the thumbnail in the feed and does most of the work. Slide 10 will be seen by a small minority, so the links also go in the post text and the first comment.

---

## Step 5: Own Discord / lab channel

```
## New preprint: timeout-induced failure attribution in agent evals

We instrumented per-step wall time across three public agent benchmarks.
31% of recorded model failures were the harness timing out. Correcting for
it reorders 2 of the 5 models.

**The check you can run on your own setup:** plot per-step wall time for your
failed episodes. Model failures spread across durations. Infra failures spike
at the timeout value. If you see the spike, some of your numbers are measuring
your runner.

**What we can't claim:** one hardware config, and for 2 of the 5 benchmarks
we're inferring the timeout from the distribution rather than reading it from
a config.

Paper: <arxiv>
Instrumented harness: <repo>

Happy to answer anything in the thread.
```

Then open a thread on it and stay in it for an hour.

---

## Step 6: Other servers and communities, soft share

For an ML research Discord where you are a member but not a regular poster, use the question pattern. It is honest here because the question is genuinely open:

```
has anyone found a clean way to separate infra failures from model failures
in agent eval runs?

we've been plotting per-step wall time and looking for a spike at the timeout
value, which catches the obvious cases. but it doesn't catch anything where
the harness fails for a reason other than a timeout, and i don't have a good
general approach

(context: we just put out a preprint where this turned out to account for 31%
of recorded failures on public benchmarks, so i'm fairly motivated to get the
detection right. <link> if relevant, it's ours)
```

The question is real, the disclosure is explicit, and the link is a parenthetical rather than the point of the message.

---

## Step 7: Long-form, day 3 to 7

A Substack or blog post with the material that does not fit in a paper: what you expected to find, what you tried first that did not work, the three weeks spent on a detection method you abandoned, and what you would do differently. See `platforms/substack.md`.

This is the piece that gets shared inside labs.

---

## Checklist before any of it goes out

```
[ ] arXiv link is live and stable
[ ] Code repo is public and the README works
[ ] Every co-author is tagged with the correct handle on each platform
[ ] Co-authors have seen the posts before they go up
[ ] No claim in any post exceeds what the paper supports
[ ] Benchmark names and conditions stated wherever a number appears
[ ] Zero em dashes across all outputs
[ ] No abstract pasted anywhere
[ ] Limitations appear in every long-form piece and in the X thread
[ ] Links in first comment on LinkedIn, in reply on X
```
