# LinkedIn

The highest-reach platform for technical and professional launches, and the one where AI-written copy is punished hardest. LinkedIn's feed is full of generated posts and the audience is fatigued. A post that reads as written by a person with an actual opinion stands out purely by contrast.

## Format rules

**Length.** The hard cap is 3,000 characters including spaces, line breaks, hashtags and mentions. The useful range is 900 to 1,600 characters. Longer posts do fine if the first three lines earn the expand.

**The truncation point is the whole game.** LinkedIn cuts the post at roughly 140 characters on mobile and around 200 on desktop, then shows "...see more". Everything before that cut is your ad for the rest. Two rules follow:

- Do not spend the first line on "I'm excited to share". You have burned the only real estate that matters.
- Do not put a line break in the first 140 characters unless the line before it is a complete, interesting thought.

**Paragraphs, not broetry.** One-sentence-per-line with a blank line between each was a 2021 growth hack and now reads as engagement farming. Write paragraphs of two to four lines with blank lines between them. It is easier to read on mobile than a wall, and it does not look like a template.

**Links kill reach.** An external link in the post body suppresses distribution. Put the link in the first comment immediately after posting and write "link in the comments" at the end of the post. Alternatively post without the link and edit it in after about an hour.

**Hashtags.** Two at most, and only ones that are real. LinkedIn's hashtag following is weak, so they buy you very little and a stack of five signals a template.

**Tagging.** Tag collaborators, co-authors, and the company. Each tagged person's network gets some exposure when they engage. Do not tag people who were not involved. It is visible and it annoys them.

**Native beats external, always.** Documents (PDF carousels) and native video get more reach than a link preview. Put the substance in the post.

## Post shapes that work

**The problem-first post.** Open with the concrete problem, describe what you tried, state the result, name the limit. This is the default and it is hard to beat.

**The number post.** Open with the surprising measurement. "Our eval suite took 6 hours. It now takes 11 minutes." Then explain how, in three or four short paragraphs.

**The lesson post.** Only works if the lesson is non-obvious and you paid for it. "We spent two weeks building X before realising Y" is a post. "Consistency is key" is not.

**The document carousel.** Best for papers, benchmarks, and anything with a figure. See specs below. The post text still has to stand on its own, because many people never swipe.

**The build-in-public update.** Short, casual, specific. Works well if the account posts regularly. Does not work as a one-off.

## Asset specs

| Asset | Dimensions | Ratio | Notes |
|---|---|---|---|
| Portrait image | 1080 x 1350 | 4:5 | Takes the most vertical feed space on mobile. Default choice. |
| Square image | 1080 x 1080 | 1:1 | Safe, works everywhere |
| Landscape image | 1200 x 627 | 1.91:1 | Same size LinkedIn uses for link previews |
| Document carousel | 1080 x 1080 or 1080 x 1350 | 1:1 or 4:5 | Upload as PDF |
| Video (landscape) | 1920 x 1080 | 16:9 | |
| Video (vertical) | 1080 x 1920 | 9:16 | Better mobile completion rates |

**File limits.** Images under 5 MB (JPG or PNG). Documents: PDF, up to 100 MB and 300 pages. Video up to 5 GB; keep it under 2 minutes for feed video regardless of what the cap allows.

**Carousel slide count.** Six to twelve. Under six feels thin, over twelve loses people. Slide 1 is a title card that has to work as a thumbnail. Put the call to action on the last slide, and repeat it in the post text since most readers never reach it.

**Text on images.** Use large type. The feed renders these small. If you would not read it at 400px wide, it is too small.

**Alt text.** LinkedIn supports it on images. Add it. It is a small accessibility win and takes ten seconds.

## Other character limits worth knowing

| Field | Limit |
|---|---|
| Post body | 3,000 |
| Comment | 1,250 |
| Headline (profile) | 220 |
| About section | 2,600 |
| Article body | 110,000 |
| Poll question | 140 |
| Poll option | 30 (up to 4 options) |

## Worked example: research paper

See `examples/paper-launch.md` for the full treatment including the carousel breakdown and the co-author tagging pattern.

Short version of what makes an academic post work on LinkedIn: LinkedIn is not a conference audience. Lead with the problem in plain language, give the result as a number, say what it does not solve, then link the arXiv page in the comments. Do not paste the abstract. The abstract is written for reviewers, and it will read as impenetrable to 95% of your feed.

## Worked example: feature release

```
Our eval runner used to lose everything when a task crashed. You got a stack
trace and whatever had scrolled past in the terminal, which meant three hours
of re-running to find out what the model had actually done.

We now write every turn to disk as it happens. Tool calls, arguments, results,
reasoning traces, token counts, per-episode artifacts. When something fails you
open that episode and read it top to bottom like a transcript.

The part that surprised us: most of our failures were not model errors. They
were our own harness timing out at 30 seconds on a step that legitimately took
90. We would never have found that without the traces.

It runs roughly 40 episodes in parallel on a single machine. The viewer is a
terminal UI rather than a web dashboard, which some people are going to dislike.

Still no good answer for diffing runs across different providers. Working on it.

Link in the comments. Built with [Name] and [Name].
```

Character count: about 1,030. Note what is absent: no emoji, no hashtags, no em dashes, no closing question, no "excited to". Note what is present: a specific failure, a number, an admission that surprised them, a tradeoff some readers will object to, an open problem, named collaborators.
