# X (Twitter)

Fastest-moving channel and the one where technical audiences actually congregate. Also the least forgiving of padding: on X, a wasted word is a scroll.

## Format rules

**Length.** 280 characters on a standard account. Premium accounts can post up to 25,000, but long single posts get collapsed behind "Show more" and read as blog posts in the wrong place. Write to 280 unless there is a real reason not to.

**Front-load.** The first seven or eight words decide it. No wind-up, no "So I've been working on something".

**Lowercase is native here.** Especially for builder and research audiences. See `styles/whatsapp-lowercase.md`. Sentence case is fine too. Title Case is not.

**Links suppress reach.** Same as LinkedIn. Put the link in a reply to your own post, and end the main post with something like "link below" only if it does not eat your character budget. Many accounts just accept the hit and include the link; if the post is strong, it still travels.

**No thread announcements.** "a thread 🧵" as post 1 is dead. If you are writing a thread, post 1 should be the single most interesting fact, standalone, such that someone who reads only that one post got something.

**Numbering.** Do not number threads. It commits you to a length and post 1 becomes a table of contents. If you must, number from post 2 onward.

**Images get attention.** A post with one image outperforms plain text for most launch content. A screenshot of real output, a terminal, a chart, or a before/after beats a designed graphic almost every time on technical X.

**Quote-tweet yourself later.** A week after launch, quote your own launch post with a new fact ("this is now running on 200 repos"). It is free second distribution.

## Thread structure

A good thread is four to eight posts. Longer than that and completion collapses.

1. The single strongest fact or claim. Standalone. Usually with the image.
2. The problem, concretely.
3. What you tried that did not work. This post is the reason people stay.
4-6. The approach, one idea per post.
7. The limit. What it does not do.
8. Link, repo, credits.

Every post has to survive alone, because people land mid-thread from quote tweets.

## Asset specs

| Asset | Dimensions | Ratio | Notes |
|---|---|---|---|
| Landscape image | 1200 x 675 | 16:9 | Standard, no crop in timeline |
| Link preview card | 1200 x 628 | 1.91:1 | What gets pulled from og:image |
| Vertical image | 1080 x 1350 | 4:5 | More mobile feed space, increasingly common |
| Square | 1080 x 1080 | 1:1 | Safe |
| Video | 1280 x 720 or 1920 x 1080 | 16:9 | 9:16 vertical also supported |

**Limits.** Up to 4 images per post. Images up to 5 MB (JPG/PNG), GIFs up to 15 MB. Video: MP4 or MOV, H.264 video with AAC audio, up to 512 MB and 140 seconds on a standard account, with Premium extending both. Supported video aspect ratios run from 1:3 to 3:1.

**Alt text** supports up to 1,000 characters. Use it, especially on charts and screenshots. Describe what the chart shows, not just "a chart".

**Multi-image layouts crop.** Two images side by side crop to roughly 7:8 each. Four images crop to 2:1 each. If the detail matters, post one image.

## Worked example: OSS release

Post 1:
```
spent the weekend making our eval traces readable. every tool call, every
reasoning trace, every token count written to disk as it happens

turns out most of our "model failures" were our own harness timing out at 30s
```
(with a screenshot of the terminal viewer)

Post 2:
```
before this, a failed run gave you a stack trace and whatever had scrolled
past in tmux. finding out what the model actually did meant re-running the
whole thing. ~3 hours each time
```

Post 3:
```
first attempt was structured logging into one jsonl. useless. you cannot read
a 400mb jsonl and you cannot diff two of them

one directory per episode fixed it. boring, works
```

Post 4:
```
runs ~40 episodes in parallel on one box. viewer is a terminal ui, not a web
dashboard, which i know some people will hate
```

Post 5:
```
still no good way to diff runs across providers. openai and anthropic traces
have different shapes and i have not found a representation that does not lie
about one of them

open to ideas
```

Post 6:
```
repo: <link>
built with @handle and @handle
```

Why it works: each post stands alone, post 3 is a failure, post 4 volunteers a tradeoff, post 5 asks a real question rather than engagement bait, and there is not a single em dash, emoji, or hashtag in it.
