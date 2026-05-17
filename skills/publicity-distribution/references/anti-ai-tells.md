# Removing AI tells

Run every draft through this before delivering it. On LinkedIn and X especially, readers now pattern-match AI writing in about one second, and the reaction is not neutral. It reads as "this person did not care enough to write it themselves", which is the opposite of what a launch post is for.

The goal is not to obfuscate that a model helped. The goal is copy that carries a real person's judgment, specifics, and rhythm, because that is what makes it worth reading.

## Contents

1. [The hard rules](#the-hard-rules)
2. [Punctuation and typography tells](#punctuation-and-typography-tells)
3. [Sentence-shape tells](#sentence-shape-tells)
4. [Vocabulary tells](#vocabulary-tells)
5. [Structure tells](#structure-tells)
6. [Platform-specific slop](#platform-specific-slop)
7. [What to do instead](#what-to-do-instead)
8. [The scan checklist](#the-scan-checklist)
9. [Before and after](#before-and-after)

---

## The hard rules

These are absolute. Violating any one of them is enough for a reader to write the post off.

1. **No em dashes.** Not one. The character `—` and the character `–` do not appear in the output. This is the loudest single tell in existence right now.
2. **No "I'm thrilled/excited/humbled to announce"** or any variant.
3. **No closing engagement bait.** "What do you think?" / "Thoughts?" / "Let me know in the comments" / "Who else has experienced this?" all go.
4. **No emoji bullet lists.** Especially 🚀 ✨ 💡 🔥 🎯 as line-starters.
5. **No "It's not just X, it's Y"** and no "X isn't about Y. It's about Z."
6. **No hashtag stacks.** Zero to two hashtags, and only if they are real communities.

---

## Punctuation and typography tells

| Tell | Why it reads as AI | Fix |
|---|---|---|
| Em dash `—` | Models use it 5-10x more than human writers, and most people cannot type it easily on a phone | Period, comma, colon, parentheses, or split the sentence |
| En dash `–` used mid-sentence | Same, plus it looks like a typo'd hyphen | Same as above |
| Semicolons in social copy | Nobody uses semicolons in a tweet | Period |
| Perfectly balanced colons: "The result: faster builds." | Formulaic beat | Write it as a sentence |
| Curly quotes mixed with straight quotes | Copy-paste artifact | Pick one, usually straight |
| Title Case On Every Heading | Blog-template energy | Sentence case |
| A bold lead-in on every single bullet | Template fill | Bold at most one or two, or none |

## Sentence-shape tells

**Tricolon everywhere.** "Faster, cheaper, and more reliable." "It's simple, powerful, and free." Models love groups of three. Humans use two, or four, or one. Break at least half of them.

**Uniform sentence length.** AI prose runs 15-22 words per sentence, every sentence. Real writing lurches. Put a four-word sentence next to a thirty-word one. Read it aloud. If the rhythm is flat, it is not fixed yet.

**The negation pivot.** "This isn't a tool. It's a workflow." "Not because it's easy, but because it's right." Delete the first half and just say the thing.

**Hedged non-claims.** "can be a powerful way to", "has the potential to", "is designed to help you". Either it does the thing or it does not.

**Summary sentence at the end of every paragraph.** Models close loops compulsively. Let some paragraphs just stop.

**Rhetorical question as a transition.** "So what changed?" "The best part?" "Here's the thing." All of these are model filler that a human would cut on the second read.

## Vocabulary tells

Words and phrases that are now effectively a watermark. Not all are bad English. They are just statistically overused enough that a reader clocks them.

**Verbs:** delve, leverage, harness, unlock, elevate, streamline, supercharge, empower, foster, navigate (as in "navigate the complexities"), underscore, showcase, embark, curate, revolutionize, transform (when used vaguely), spearhead, dive deep

**Adjectives:** robust, seamless, cutting-edge, game-changing, groundbreaking, innovative, comprehensive, invaluable, pivotal, crucial, vibrant, bespoke, holistic, meticulous, unparalleled

**Nouns:** landscape, realm, tapestry, testament, journey, ecosystem (when not literal), paradigm, cornerstone, treasure trove, deep dive, game-changer, powerhouse

**Openers:** "In today's fast-paced world", "In an era where", "Let's be honest", "Picture this", "We've all been there", "Imagine a world where"

**Connectives:** moreover, furthermore, additionally, that said, ultimately, in conclusion, at the end of the day, it's worth noting that

**Meta-narration:** "Let that sink in", "And that changes everything", "The implications are staggering", "This is huge"

Replacement rule: when you delete one of these, do not swap in a synonym. Replace it with the specific thing it was standing in for. "Leverage our robust infrastructure" becomes "run it on the same three boxes we already had".

## Structure tells

**The pyramid.** Hook, three bullets, summary, question. If the skeleton is that predictable, the content is invisible.

**Every list is the same length.** Three bullets, three bullets, three bullets.

**Parallel grammatical structure across all bullets.** "Building X. Shipping Y. Scaling Z." Real notes are uneven.

**No dead ends.** Human posts contain a thing that does not resolve: an open question, an admission, a complaint, a thing that is still broken. Include one. It is the strongest single signal of a real author.

**Perfect politeness.** No writer is that agreeable about their own work for a whole post. Have an opinion about something.

## Platform-specific slop

**LinkedIn.** The one-sentence-per-line broetry format ("I did a thing.\n\nIt changed everything.\n\nHere's why:") is itself now a tell, separate from AI. Use real paragraphs of two to four lines. Also cut: "humbled", "beyond grateful", "lessons learned", "here's what I learned", the fake-vulnerable opener that pivots into a pitch.

**X/Twitter.** Cut: "A thread 🧵", "Let me break it down", "Bookmark this", "1/ Introduction", numbered threads where thread post 1 is just a label. Cut the "hook, thread, engagement CTA, follow me for more" stack.

**Instagram.** Cut the caption that repeats the slide text verbatim, and the 30-hashtag block.

**Discord.** Cut anything that reads as a press release. Discord is a room with people in it. See `platforms/discord.md`.

**Medium/Substack.** Cut: the "Introduction" heading, the "Conclusion" heading, the TL;DR that restates the title, and the "Thanks for reading! If you enjoyed this, clap 50 times" outro.

## What to do instead

Deleting tells gets you to neutral. These get you to good.

1. **Name a specific moment.** "At 2am on Thursday the eval harness started returning empty strings for every reasoning model" beats any amount of framing.
2. **Include a number you had to go look up.** Not a round one.
3. **Admit the limit.** "It only works for single-file repos right now." Readers trust the rest of the post more.
4. **Name people.** Real names, tagged.
5. **Keep one sentence that is slightly too long** and one that is three words.
6. **Write the first line last.** Draft the body, then find the most interesting sentence in it and move it to the top.
7. **Cut the last paragraph.** It is almost always a summary nobody needed. Posts are better when they end abruptly.
8. **Read it aloud.** Anything you would not say out loud to a colleague, cut.

## The scan checklist

Run literally, in order, before delivering:

```
[ ] grep for — and – : zero hits
[ ] grep for 🚀 ✨ 💡 as line starters: zero hits
[ ] "thrilled|excited|humbled to (announce|share)": zero hits
[ ] Closing question mark on the final line: none
[ ] Hashtag count: 0-2
[ ] Vocabulary list above: zero hits, or one deliberate hit
[ ] Any three-item list: at least half changed to 2 or 4 items
[ ] Sentence lengths: at least one under 6 words and one over 25
[ ] One concrete number, name, or timestamp present
[ ] One admitted limitation or open problem present
[ ] Final paragraph: is it a summary? If yes, delete it.
[ ] Read aloud test passed
```

For the mechanical ones, actually run the grep rather than eyeballing it:

```bash
grep -n '[—–]' draft.md
grep -nE 'thrilled|excited to (announce|share)|humbled|delve|leverage|robust|seamless|game.?chang|unlock|elevate|tapestry|testament|landscape of|in today.s' draft.md
```

## Before and after

**Before (LinkedIn, AI-default):**

> 🚀 Thrilled to announce that we've just shipped our new evaluation framework!
>
> After months of hard work, our team has built a robust, scalable solution that empowers researchers to seamlessly benchmark their models.
>
> Key highlights:
> ✨ Blazing-fast parallel execution
> 💡 Comprehensive observability out of the box
> 🎯 Support for all major providers
>
> This isn't just a tool — it's a new paradigm for model evaluation.
>
> What's your biggest challenge with evals? Let me know in the comments! 👇
>
> #AI #MachineLearning #Innovation #Tech #Evaluation #OpenSource #DataScience

**After:**

> We kept losing three hours every time an eval run failed, because the only record of what happened was whatever scrolled past in the terminal.
>
> So we wrote down every turn instead. Tool calls, reasoning traces, token counts, per-episode artifacts. When a run goes wrong now you open the episode and read it like a transcript, which is what we wanted the whole time.
>
> It runs about 40 tasks in parallel on one machine. The viewer is a terminal UI, not a web app, which some people will hate.
>
> Still no good story for comparing runs across different model providers. That is next.
>
> Repo in the comments. Built with [name] and [name].

What changed: a specific failure, a specific fix, a real number, an admitted tradeoff, an open problem, named collaborators, no em dashes, no emoji, no hashtags, no closing question. It is also shorter.
