# Worked example: the same thing, shared into six different Discords

You built an eval tracing tool. You are in a few hundred servers. Here is how the same launch looks in six of them, plus the two you should skip.

The lesson: the message is written for the room, not for the product. If you cannot write something specific to a server, that server is not a fit and you should skip it, which is a real and correct outcome.

---

## 1. Your own server, `#announcements`

Direct. Full launch update. `@release` role ping. See `examples/product-launch.md` for the full text.

---

## 2. An ML engineering server where you post weekly

You have credibility here. A direct share in `#showcase` is fine, but make it a build note rather than an announcement.

```
finally shipped the tracing thing i've been complaining about in here for a
month

writes every turn to disk as the run happens instead of after. the reason that
matters: if the process dies you still have everything up to the point it died,
which is exactly the case you need it for

<link>

the cross-provider trace shape problem i asked about in #general a while back
is still unsolved btw. openai and anthropic disagree about what a "step" is and
every unified schema i tried drops something real from one side
```

It references your own prior participation, which is the thing that makes a direct share acceptable.

---

## 3. A large general-AI server, no rapport, no self-promo channel

Do not post a launch. Use the question pattern, and only because the question is real.

```
how are people handling trace shapes across providers?

i've got per-episode traces working fine within one provider but every unified
representation i try ends up lying about one of them. openai and anthropic
don't agree on what constitutes a step

currently keeping them in separate formats and it makes cross-provider
comparison basically useless

has anyone landed on something that works or does everyone just eat this
```

No link. If someone asks what you are using, that is where it goes. If nobody asks, you got an answer to a question you actually had.

---

## 4. A research Discord, adjacent field

Share the finding, not the product.

```
ran into something that might be relevant to people benchmarking agents here

a meaningful chunk of what we'd been recording as model failures were our own
harness timing out. the tell is the distribution: model failures spread across
step durations, infra failures spike at the timeout value

plotting per-step wall time takes ten minutes and it's worth doing before you
trust any agent benchmark number, including your own
```

The product is mentioned nowhere. Anyone who looks at your profile finds it.

---

## 5. A server with a dedicated `#self-promo` channel

Post in that channel, briefly, and expect modest results. That is what the channel is for and that is what it delivers.

```
eval runner with per-episode tracing, terminal viewer, open source

built it because debugging a failed run meant re-running the whole suite

<link>
```

Do not cross-post it into `#general` afterwards.

---

## 6. A server where a relevant question was asked three days ago

The highest-value pattern and the one requiring the most patience. Search for it. Reply in the original thread.

```
late to this but the thing that fixed it for us was logging per-step wall time

our failures all clustered at exactly 30s which turned out to be a hardcoded
timeout in our own runner. we'd spent two weeks on prompt changes before
noticing

worth ruling out before you go further down the prompt path
```

Do not link anything. If they respond, the conversation gets there naturally.

---

## Servers to skip

**A frontend / design community.** The tool is irrelevant to the room. Posting it costs goodwill and returns nothing.

**A server you joined last week and have never posted in.** Join date and message history are both visible. Participate for a few weeks first, or accept that this server is not a distribution channel for you and that is fine.

---

## The pattern underneath

| Your standing in the room | What goes in the message |
|---|---|
| It is your server | The full announcement |
| Regular poster, known | A build note referencing prior context |
| Member, rarely post | A real question, or a finding with no link |
| New or never posted | Nothing. Participate first. |
| Dedicated self-promo channel exists | Two lines in that channel, nowhere else |
| Relevant open question exists | A complete answer, link only if asked |

And the two rules that never bend: **say it is yours when you mention it**, and **never paste the same message into two servers**.
