# Worked example: product launch

One product, five channels, five genuinely different pieces of writing. The product is illustrative: a hosted eval runner with per-episode tracing. Numbers are placeholders.

The point of this example is the contrast between channels. Read the five side by side. They share facts and share nothing else.

---

## The fact sheet

- **What:** hosted runner for agent evals with full per-episode traces
- **For:** teams running agent benchmarks who currently re-run failed suites to find out what happened
- **The number:** a failed run used to cost about 3 hours of re-running. Now it is a file you open.
- **What was hard:** cross-provider trace shapes. Still unsolved.
- **What it does not do:** no cross-provider diffing, no web UI, single-region
- **Links:** landing page, docs, repo
- **People:** two co-founders, one contributor

---

## X (launch post, native video attached)

```
shipped: hosted eval runner that writes every turn to disk as the run happens

a failed run used to mean re-running the whole suite to find out what the
model did on turn 4. about 3 hours. now you open the episode and read it

<video>
```

Then, in a reply:
```
the thing that surprised us building this: most of what we'd been calling
model failures were our own harness timing out at 30s on steps that needed 90

we'd have never found that without the traces

<link>
```

Style: `styles/whatsapp-lowercase.md`. No hashtags, no emoji, link in the reply.

---

## LinkedIn (day 1, founder's personal account)

```
Every team I know running agent evaluations has the same 3am workflow: a run
fails, the output is a stack trace and whatever is left in the terminal, and
the only way to find out what the model actually did is to run the whole suite
again. About three hours, and you often need to do it twice.

We built the thing that fixes that. Every turn is written to disk as the run
happens: tool calls with arguments, results, reasoning traces, token counts,
and whatever artifacts the task produced. A failed run is a file you open and
read, not a thing you reconstruct.

The part we did not expect was what it showed us about our own results. A
large share of what we had been classifying as model failures were our harness
timing out at 30 seconds on steps that legitimately took 90. That single
finding changed our internal rankings more than any prompt work we had done
that quarter.

It is genuinely incomplete. There is no cross-provider diffing yet, because
OpenAI and Anthropic trace structures differ enough that every unified view we
have tried misrepresents one of them. Single region. No web dashboard, the
viewer is a terminal interface, which is a deliberate choice and one that will
put some people off.

Link in the comments. Built with [Name] and [Name].
```

Style: `styles/professional.md`. About 1,350 characters. Note it volunteers three limitations, which on LinkedIn is unusual enough to be memorable.

---

## Own Discord, `#announcements`, `@release` role ping

````
## Hosted runner is live

@release

**What it is**
Runs your eval suite and writes every turn to disk as it goes. Tool calls,
arguments, results, reasoning traces, token counts, per-episode artifacts.

**Why**
Because "the run failed" plus a stack trace is not debuggable, and re-running
a suite to find out what happened costs about 3 hours.

**What it doesn't do yet**
- No cross-provider diffing. Trace shapes differ too much and every unified
  schema we tried drops something real from one side. Actively want ideas
  on this, #feedback
- Single region
- Terminal viewer, no web UI

**Try it**
```
uv add <pkg>
```

Docs: <link>
Landing: <link>

Thread below, ask me anything for the next hour.
````

---

## Another server, `#showcase` channel, soft share

Different server, different room, completely different message. This one answers a question that was asked two days ago:

```
@someone re: your question about debugging eval failures the other day

the thing that fixed it for us was logging per-step wall time. our failures
all clustered in a spike right at 30s, which turned out to be a hardcoded
timeout in our runner, not the models doing anything wrong. worth checking
before you go further into prompt debugging

we ended up building a hosted version of the tracing (<link>, ours) but
honestly the timing log alone will tell you if that's your problem
```

The useful answer is complete without the link. The disclosure is explicit. The message explicitly says they may not need the product.

---

## Substack, day 1

Title: `Most of our model failures were our own timeouts`
Subtitle: `What happened when we started writing every turn to disk`

Opens on the 3am incident, not on the product. The product appears around 60% of the way down, after the reader has got the useful part. Ends on the unsolved cross-provider problem.

Full structure in `platforms/substack.md`.

---

## What to notice across the five

| | X | LinkedIn | Own Discord | Other Discord | Substack |
|---|---|---|---|---|---|
| Style | lowercase | professional | technical, formatted | lowercase | professional |
| Length | 280 | 1,350 | ~900 | ~500 | 2,000 words |
| Leads with | the change | the reader's problem | what shipped | their question |  the incident |
| The product is | the subject | the subject | the subject | a parenthetical | mentioned at 60% |
| Install command | no | no | yes | no | yes |
| Limitations stated | 1 | 3 | 3 | n/a | throughout |
| Ping / CTA | none | link in comments | @release role | none | subscribe, mid-post |

Not one sentence is reused across the five. That is the standard.
