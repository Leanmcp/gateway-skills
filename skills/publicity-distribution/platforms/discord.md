# Discord

Discord is not a feed. It is a room with people in it who can see each other. That single fact changes everything about how you post, and it is why the same message that works on LinkedIn will get you ignored, muted, or removed here.

There are two completely different jobs, and confusing them is the most common and most costly mistake:

- **Your own server.** These people opted in to hear from you. A direct launch update is correct and welcome.
- **Someone else's server.** Nobody there joined to receive your marketing. A direct launch post is a tax on the room, and it reads as such. What works is participation that happens to surface your work.

Read the section that applies. If the user is posting to both, write two genuinely different messages.

---

## Part 1: Your own server

Your members joined to follow the work. Withholding a launch from them would be strange. Post directly.

### Where it goes

| Channel type | Use |
|---|---|
| `#announcements` (Announcement channel) | Real releases only. Followers in other servers can pull these in, so treat each post as public. |
| `#changelog` or `#releases` | Version bumps, small features. High frequency is fine here. |
| `#general` | The conversational version, after the announcement. "posted the release above, happy to answer anything" |
| Forum channel | Launches that will generate discussion. Each post becomes its own thread, which keeps `#general` clean. |

### Pinging

This is where goodwill is spent or wasted.

- `@everyone` is for things that genuinely affect everyone: a major release, a breaking change, a migration deadline, a live event starting now. Two or three times a year, not two or three times a month.
- `@here` for time-sensitive things where only active members matter. A live stream in ten minutes.
- A dedicated `@release` or `@announcements` opt-in role is the correct default. Set one up if the server does not have one. Members self-select, and you can then ping freely without cost.
- Silent-ping the rest. Most launches deserve no ping at all.

The rule of thumb: if you are unsure whether it warrants `@everyone`, it does not.

### Format

Discord supports full markdown, so use it. Headers (`#`, `##`), bold, bullets, and code blocks all render. This is the one platform where formatted structure helps rather than looking like a template, because people read Discord the way they read a README.

Structure for a launch update:

```
## v0.4 is out

**What's new**
- Full episode traces written to disk as runs happen
- Terminal viewer for reading back a failed run
- ~40 episodes in parallel on one machine

**What broke and got fixed**
Timeouts were hardcoded at 30s and silently killing legitimate long steps.
Now configurable, default 120s. If you were seeing empty results on reasoning
models, this was why.

**Not there yet**
Cross-provider run diffing. The trace shapes differ enough that any unified
view currently lies about one of them. Open to ideas in #feedback.

Install: `uv add <pkg>` or pull latest from <repo link>

Full notes: <link>
```

Keep it under 2,000 characters (the message cap). If it runs longer, split it into a second message in the same thread rather than trimming the substance, or attach the full notes as a file.

### Discord-specific formatting that helps

- Code blocks with a language tag for anything installable or runnable. People copy-paste from Discord constantly.
- `<link>` wrapped in angle brackets suppresses the link preview embed. Use this when you have three links and do not want three giant cards.
- Upload a short screen recording directly rather than linking to YouTube. Inline playback gets far more views than a click-out.
- Emoji are fine on Discord in a way they are not on LinkedIn. Discord is informal by nature. Still do not build a bullet list out of them.
- Add a reaction to your own post to prime others. Low effort, works.
- Open a thread on your announcement immediately and put the detail there. Keeps the channel readable and gives people a place to ask.

### After posting

Stay in the channel for the next hour and answer. A launch post with fifteen replies underneath it from the author reads completely differently from one sitting alone. This is the highest-value hour of the entire launch and most people skip it.

---

## Part 2: Someone else's server

You are in a few hundred of these. Almost all of them have a rule against self-promotion, and even where they do not, the social rule exists regardless. The goal here is not to announce. It is to be useful in a way that leaves a trail back to you.

### Before posting anything, check three things

1. **The rules channel.** Read it. Many servers have a `#self-promo` or `#showcase` channel specifically for this, and posting elsewhere gets you removed. If a designated channel exists, that is where a direct link goes, and expect modest results from it.
2. **Have you been present?** If your last message in the server was four months ago and your next one is a link to your product, everyone can see that. Servers show join dates and message history. If you have not participated, participate for a week first, or do not post.
3. **Is it actually relevant to that room?** A Rust server does not want your Python eval tool. Relevance is the entire permission structure.

### The four soft-share patterns

**1. Answer a question with your work as the answer.**

The strongest pattern by far. Search the server for people describing the problem you solved. Answer their question properly, in full, so the answer stands alone if they never click your link. Then mention the tool as one option.

```
yeah this bites everyone. the issue is the harness timeout, not the model.
check whether your runner has a hardcoded limit, mine was at 30s and reasoning
models blow straight through that on long chains.

easiest check: log the wall time per step and see if your failures all cluster
right at the timeout value.

i ended up writing a thing that dumps every turn to disk so i could actually
see this, <link> if it's useful, but honestly just adding the timing log will
tell you whether that's your problem
```

Note the structure: the useful answer comes first and is complete without the link. The link is offered, not pushed. And it explicitly tells them they may not need it, which is the part that makes it land.

**2. Ask a real question you actually have.**

This is the indirect approach done right, and it is only honest if the question is real.

```
question for people running multi-provider evals: how are you handling the
fact that openai and anthropic traces have totally different shapes?

i've got per-episode traces working fine within one provider, but every
unified representation i try ends up lying about one of them. currently
keeping them separate and it makes cross-provider comparison useless.

is there a canonical format people have settled on or does everyone just
eat this?
```

Nothing is being sold. But the question establishes that you have built the thing, demonstrates the depth, and reliably produces "wait, what are you using for the traces?" in the replies. That is where the link goes, in response to an ask.

If nobody asks, you still got an answer to a real question. That is why this only works when the question is genuine.

**3. Share the artifact, not the product.**

The blog post, the benchmark, the diagram, the failure write-up. Content is shareable in rooms where products are not.

```
wrote up why our eval failures were mostly harness timeouts rather than model
errors, with the traces: <link>

the part that surprised me was how many "refusals" were actually truncation
```

The product is mentioned nowhere. It is one click deeper, for anyone who cares.

**4. Reply in context, days later.**

Set a reminder. When someone in that server hits the problem next week, you are the person who already solved it. This compounds and costs nothing.

### Never do these

- Copy-paste the same message into twelve servers. People are in multiple servers and they will see it twice. This is the fastest way to become the person everyone mutes.
- DM members unprompted. This gets you banned from most servers and it is genuinely rude.
- Post a launch announcement into `#general` of a server you do not run.
- Use `@here` or `@everyone` anywhere you are a guest. You almost certainly cannot, and attempting it is noticed.
- Lead with the link. A message that is a link with one line of framing reads as a drive-by.
- Pretend not to be the author. "Found this cool tool" about your own project is dishonest and people find out. Say "I built this".

### Disclosure

When you mention your own project, say that it is yours. One clause: "i built this", "disclaimer, mine". It costs nothing, it is correct, and in practice it makes people more receptive rather than less, because the alternative reads as an ad.

---

## Limits

| Thing | Limit |
|---|---|
| Message | 2,000 characters (4,000 with Nitro) |
| Embed description | 4,096 characters |
| Embed title | 256 characters |
| Embed field value | 1,024 characters |
| Embeds per message | 10, combined 6,000 characters across all of them |
| Channel name | 100 characters |
| Nickname | 32 characters |
| File upload | 10 MB on free servers, higher with server boosts |

These are the published ceilings as of 2026 and Discord adjusts them periodically. Verify against Discord's own documentation if a number is load-bearing.

## Writing a set of Discord messages

When the user is posting to their own server plus several others, produce:

1. One announcement for their server, formatted with markdown headers, with a ping recommendation.
2. A separate soft-share message per target server, each one genuinely different, each one tuned to that room's topic. Ask the user what each server is about if you do not know. Generic soft-shares are worse than none.
3. A note on which servers to skip, if any look like a poor fit. Restraint is part of the deliverable.
