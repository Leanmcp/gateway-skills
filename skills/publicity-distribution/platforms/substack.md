# Substack

Substack is email first. Every post lands in an inbox, which is a fundamentally different contract from a feed: you are asking for a slot in someone's day, repeatedly. That means fewer posts, higher quality, and a consistent shape people come to expect.

The thing Substack gives you that nothing else does is **the list**. You own the email addresses and can export them. Medium, LinkedIn and X can all change their algorithm tomorrow and your reach goes with it. A Substack list is yours.

## When to use it over Medium

| Goal | Platform |
|---|---|
| Rank on Google, reach strangers | Medium |
| Build a list you own | Substack |
| Paid subscriptions | Substack (you keep roughly 87%, Substack takes 10% and Stripe about 3%) |
| Portfolio pieces, one-offs | Medium |
| Recurring series, research notes, build logs | Substack |

Running both is reasonable. Publish to Substack, then import to Medium with the canonical pointing back. See `platforms/medium.md`.

## Format rules

**The subject line is the post title.** Both jobs at once. It has to work in a crowded inbox next to receipts and newsletters the reader is already ignoring. Specific beats clever. Curiosity gaps ("You won't believe what we found") do not survive contact with a technical audience.

**The first line shows as preview text** in most email clients. Do not waste it on "Hi everyone, welcome back to another edition of". Open on the substance.

**Length.** Substack tolerates longer pieces than Medium because the audience opted in. 1,500 to 3,000 words is normal. Still cut anything that is not carrying weight.

**Sections.** Use headers. People scan email before they read it.

**Code blocks** render reasonably. Long code is still better as a Gist embed.

**Footnotes** are native and good. Use them for caveats, methodology notes, and the detail that would break the flow. Technical readers appreciate that the rigour is available without it interrupting the argument.

**Buttons.** Substack's subscribe button and share button are embeddable mid-post. One subscribe button, placed after the first strong section rather than at the top. A button before the reader has got anything is a bad trade.

## Notes

Substack Notes is the platform's short-form feed, similar in shape to X. Worth using because it distributes to Substack's own network of readers rather than your subscribers only.

For a launch: post the long piece, then post a Note that is not a link dump. Pull the single most interesting paragraph out and post it as a standalone thought, with the link underneath. Same discipline as X: make the Note worth reading even if nobody clicks.

## Asset specs

| Asset | Dimensions | Notes |
|---|---|---|
| Post cover image | 1200 x 630 (1.91:1) | Max 10 MB. Shows at the top of the post and in email preview. |
| Inline images | Up to 1200 px wide | Max 10 MB |
| Publication logo | 256 x 256 minimum, square | Max 5 MB. Appears in subscriber inboxes. |
| Publication cover photo | 600 x 600 minimum | Max 10 MB. Scales to about 324 x 324. |
| Author photo | 256 x 256 minimum | Max 5 MB, rendered circular |
| Wordmark (horizontal logo) | 1344 x 256 minimum (21:4) | Alternative to the square logo in headers |

Supported image formats: JPG, PNG, GIF, WEBP, AVIF. Logos and author photos: PNG or JPG.

**Video posts:** up to 20 GB. MP4, MOV, AVI, 3GP, FLV, MPEG-2. 4K supported, 1080p recommended.

**Podcast / audio:** up to 250 MB. MP3, WAV, AAC.

## Character limits

| Field | Limit |
|---|---|
| Post title | 100 |
| Post subtitle | 250 |
| Publication name | 50 |
| Publication description | 255 |
| Author bio | 250 |
| Post body | No limit |

The 100-character title cap is tighter than Medium's 140. If you are cross-posting, write to Substack's limit and the title works on both.

## Email-specific things that catch people out

- **Dark mode.** Many clients render email in dark mode and invert backgrounds. Images with white backgrounds end up as glaring white rectangles. Use transparent PNGs or images with a mid-tone background.
- **Image-heavy posts get clipped.** Gmail truncates messages over roughly 102 KB with a "View entire message" link, which kills completion. Keep the email version lean and push the heavy figures below the fold or into the web version.
- **Test send to yourself** before publishing. Always. The web preview and the email render differently.
- **Send time.** Tuesday to Thursday morning in your main audience's timezone is the conventional answer and it is conventional because it works.

## Do not

- Open with "Welcome back to another edition"
- Apologise for not posting in a while. Nobody noticed, and it reframes the post around you rather than the content.
- Put the subscribe button before the reader has received anything
- Send more often than you can sustain. An inconsistent weekly is worse than a reliable monthly.
