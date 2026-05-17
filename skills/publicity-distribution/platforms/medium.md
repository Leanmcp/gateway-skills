# Medium

Use Medium when you want search traffic and distribution to strangers. Medium ranks well on Google and its own recommendation system can put a post in front of people who have never heard of you. What you do not get is the reader's email address or any ongoing relationship. Medium owns the audience.

Rule of thumb: **Medium for discovery, Substack for retention.** If you are doing both, see the canonical URL section below so you do not split your SEO.

## Format rules

**Title and subtitle.** The first H1 in the story becomes the title and the first H2 becomes the subtitle. Both cap at 140 characters. The subtitle shows in previews and in search results, so it is a second hook, not a decoration.

Titles that work are specific and concrete. "Why our eval failures were mostly timeouts" beats "Lessons learned from building an evaluation framework". Avoid the listicle-plus-colon construction ("5 Things I Learned: A Deep Dive") which is both overused and an AI tell.

**Length.** Seven minutes read time (roughly 1,600 to 1,800 words) is the sweet spot for technical posts. Medium shows the estimated read time, and it affects click-through.

**Structure.** Use H2 for sections, H3 sparingly. Do not write a section called "Introduction" or one called "Conclusion". Open with the concrete problem and close with the open question or the next step.

**Code blocks.** Medium supports code blocks but the syntax highlighting is poor and long code reads badly. For anything over roughly fifteen lines, embed a GitHub Gist instead. Gists render properly and stay in sync if you fix a bug.

**Images.** Break up the text. A post with no images loses readers around the four-minute mark. Charts, terminal screenshots, and diagrams all work.

**Pull quotes and section dividers** are native Medium features and worth using, sparingly.

**Tags.** Five maximum. Pick the ones with real followings in your area rather than the most generic. Tags drive Medium's internal distribution, so this matters more than hashtags do elsewhere.

**Publications.** Submitting to a relevant publication multiplies reach substantially over posting to your personal profile. Identify one that fits the topic and check its submission process, which is usually in its about page. Expect a delay of a few days.

## Canonical URLs and cross-posting

If the post also lives on your own blog or Substack, decide which one is canonical, meaning the version search engines should credit.

- **Your blog is canonical:** use Medium's import tool (`medium.com/p/import`). It automatically sets `rel=canonical` pointing back at the original. This is the correct default if you have a blog you care about.
- **Medium is canonical:** paste directly. Set canonical tags on the other copies pointing at Medium.

Never publish the same text in two places with neither marked canonical. You split the ranking signal and both versions rank worse.

Publish to your own site first, wait for it to get indexed (a day or two), then import to Medium.

## Asset specs

| Asset | Dimensions | Notes |
|---|---|---|
| Featured / cover image | 1200 x 680 | Max 25 MB. JPG, PNG or GIF. Shows in previews and social cards. |
| Inline image (full width) | 1400 px wide | Minimum 1192 px to render full-bleed |
| Inline image (in column) | 700 px wide | |
| Profile photo | 400 x 400 | Rendered as a circle, max 5 MB |
| Publication logo | 300 x 300 minimum | Max 5 MB |

**No native video.** Medium does not host video. Embed YouTube or Vimeo by pasting the URL on its own line. Animated GIFs up to 25 MB upload directly.

## Character limits

| Field | Limit |
|---|---|
| Story title | 140 |
| Subtitle | 140 |
| Profile bio | 160 |
| Publication name | 80 |
| Newsletter subject line | 150 |
| Story body | No hard limit |

## Structure for a technical post

1. **The concrete problem**, two or three paragraphs. A real incident, with specifics. No scene-setting about the industry.
2. **Why the obvious fix does not work.** This is what makes it worth reading rather than a README.
3. **What you tried that failed.** Keep this. It is the most-quoted part of technical writing and the strongest signal of a real author.
4. **The approach**, with code or diagrams.
5. **Results**, with real numbers and the conditions they were measured under.
6. **Limits and open problems.**
7. **Links**: repo, docs, related work, credits.

Then run the whole thing through `references/anti-ai-tells.md`. Long-form is where AI tells accumulate fastest, because there is more surface area. Pay particular attention to the vocabulary list and to paragraph-ending summary sentences.

## Do not

- Open with "In today's rapidly evolving landscape of..."
- Write a TL;DR that restates the title
- End with "Thanks for reading! Clap 50 times and follow for more"
- Use headings called Introduction, Background, Conclusion, Final Thoughts
- Pad to hit a word count. A tight 900-word post beats a padded 2,000-word one.
