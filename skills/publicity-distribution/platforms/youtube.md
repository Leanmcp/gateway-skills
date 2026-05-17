# YouTube (demo videos)

A demo video is the highest-leverage asset in a launch, because it is the only format where people see the thing actually work. It is also the one most often ruined by a two-minute preamble before anything happens on screen.

The governing rule: **show the output in the first five seconds.** Not the logo, not your face, not "hey everyone, so in today's video". The result. Then explain how you got there.

## Picking the format

| Format | Length | Use for |
|---|---|---|
| Short | Under 60s, 9:16 | One feature, one wow moment. Highest reach, lowest depth. Also reusable as a Reel and an X video. |
| Demo | 2 to 5 min, 16:9 | Launch centrepiece. What it is, it working, how to get it. |
| Walkthrough | 8 to 20 min, 16:9 | Tutorial, deep dive, conference-talk style. For people already interested. |

For a launch, make the 2 to 5 minute demo first, then cut a Short out of the best 30 seconds of it. Do not shoot them separately.

## Demo video structure

1. **0:00 to 0:05, the payoff.** The thing working. Real output on screen. No intro card.
2. **0:05 to 0:25, the problem.** Why this exists, stated concretely. One sentence of context, not a history of the field.
3. **0:25 to 2:30, the demo.** Real screen recording, real terminal, real latency. Do not fake it and do not speed up past the interesting parts. If something takes 30 seconds, cut to it finishing rather than pretending it is instant.
4. **2:30 to 3:00, the limits.** What it does not do. This buys more credibility than any amount of polish.
5. **Last 15 seconds, where to get it.** Link, install command, repo. Say it and put it on screen.

No outro card, no "smash that subscribe". End on the last useful frame.

## Recording quality notes

These matter more than production value:

- **Font size.** Set your terminal and editor to a much larger size than you work at. Most viewers are on a phone. If it is not readable at 400 px wide, it is not readable.
- **Audio is more important than video.** Viewers tolerate a mediocre screen recording and abandon bad audio instantly. Any decent microphone in a room with soft furnishings beats a laptop mic.
- **Clean desktop.** Hide the bookmarks bar, close Slack, clear notifications, use a fresh profile. A notification popping up mid-demo is the single most common re-record.
- **Cursor.** Move deliberately. Frantic mouse movement is hard to follow.
- **Cut the dead air.** Anything where nothing happens on screen and nothing is being said gets cut.
- **Captions.** Upload an SRT or use YouTube's auto-captions and correct them. A large share of views are muted, and captions help search.

## Title

100 character cap, but search results, suggested-video tiles, end screens and notifications all truncate around 70 characters on most viewports. Write to 60 to 70.

Front-load the distinguishing word. "Eval traces you can actually read" not "Introducing the new version of our evaluation framework, now with tracing".

Avoid: ALL CAPS, excessive punctuation, "You Won't Believe", and the generic "Introducing X". Nobody searches for "Introducing".

## Description

5,000 character cap. Roughly the first 150 characters show before "Show more", and those same characters feed search snippets. Put the summary and the primary link there.

Template:

```
[One or two sentences of what this is and what it does. Link.]

Repo: <link>
Docs: <link>
Paper: <link>

Chapters:
00:00 What this does
00:23 The problem
01:05 Live run
02:40 What it can't do yet
03:10 Install

[Two or three paragraphs of real context: why it was built, what the
constraints were, what is coming. This section is indexed by search and
by Google, so write it for a reader, not as keyword filler.]

Built with [names]. 
```

**Chapters** require the first timestamp to be `00:00` and at least three chapters, each a minimum of ten seconds long. Keep chapter titles under about 40 characters since that is what the player shows on hover, and under 30 for mobile.

## Asset specs

| Asset | Dimensions | Notes |
|---|---|---|
| Video (standard) | 1920 x 1080, 16:9 | 1280 x 720 minimum acceptable |
| Shorts | 1080 x 1920, 9:16 | Under 3 minutes |
| Thumbnail | 1280 x 720, 16:9 | Under 2 MB. JPG, PNG or GIF. Minimum width 640 px. |
| Channel banner | 2560 x 1440 | Safe area for all devices is the central 1546 x 423 |
| Channel avatar | 800 x 800 | Rendered as a circle |

**Encoding:** MP4 container, H.264 video, AAC audio. 30 or 60 fps. Match your source frame rate rather than converting.

## Thumbnails

The thumbnail does more for views than the video does. It is shown at around 360 px wide in most feeds and smaller on mobile, so:

- Four to five words maximum, in very large type
- High contrast, one focal point
- Do not put important content in the bottom right, the duration stamp covers it
- No thin fonts, no small text, no screenshot of an IDE at native resolution
- A face gets clicks. This is annoying and it is also true. If the creator is comfortable on camera, a reaction shot with three words of text outperforms a clean design almost every time.
- Never use a thumbnail that misrepresents the video. It burns retention and the algorithm punishes it.

## Character limits

| Field | Limit |
|---|---|
| Title | 100 (truncates around 70) |
| Description | 5,000 (about 150 visible) |
| Chapter title | 100 (about 40 shown, 25 to 30 on mobile) |
| Tags | 500 total across all tags |
| Comment | 10,000 |

## Distribution after upload

The video is not the launch. It is an asset the launch uses:

1. Upload unlisted, watch it once end to end, fix the obvious problem.
2. Publish, then pin a comment with the links.
3. Embed it in the Medium or Substack post.
4. Post the Short natively to X, Instagram Reels and LinkedIn as separate native uploads. Do not post a YouTube link to those platforms, all of them suppress external video links.
5. Upload the video file directly into Discord if it is under the server's size cap. Inline playback beats a click-out by a wide margin.

Native upload everywhere. The same file, five times. It is a small amount of extra work for a large difference in reach.
