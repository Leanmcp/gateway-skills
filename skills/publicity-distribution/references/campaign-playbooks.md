# Campaign playbooks

What you are publishing changes the structure, the channel mix, and the order. Find the matching playbook.

## Contents

1. [Paper launch](#paper-launch)
2. [Product launch](#product-launch)
3. [Feature release](#feature-release)
4. [OSS release](#oss-release)
5. [Content amplification](#content-amplification)
6. [Video launch](#video-launch)
7. [Milestone](#milestone)

---

## Paper launch

**The core problem:** your paper is written for reviewers. Your feed is not reviewers. Pasting the abstract is the single most common mistake and it guarantees the post is skipped.

**The translation job.** For each channel, answer three questions in plain language:
1. What did people believe or do before this paper?
2. What did you find?
3. What changes because of it?

If the answer to (3) is "nothing yet, it is a step", say that. Honest framing of an incremental result is more respected than inflated framing, particularly among the researchers you actually want to reach.

**Sequence:**

| Day | Channel | Form |
|---|---|---|
| 0 | arXiv / OpenReview | The paper goes up first, so everything else has a stable link |
| 0 | X thread | 5 to 7 posts. Post 1 is the finding, with the key figure. |
| 0 | Own Discord / lab channel | Launch update with the link |
| 1 | LinkedIn | Plain-language post plus a document carousel of the figures |
| 1 to 3 | Relevant research Discords / Slacks | Soft share, usually the question pattern |
| 3 to 7 | Blog or Substack | The extended version: motivation, what failed, what you would do differently |
| Ongoing | Replies | Answer every substantive question. This is how papers get cited. |

**X thread shape for a paper:**
1. The finding, one sentence, with the main figure attached
2. The setup: what problem, what was tried before
3. The method, plainly
4. The result, with the number and the conditions
5. The failure case or the negative result. Include one.
6. Limitations, stated by you before a reviewer states them
7. Link, co-authors tagged, code and data links

**LinkedIn shape for a paper:** see `examples/paper-launch.md` for the full worked example. The short version is: lead with the problem a non-specialist recognises, give the result as a comparison, name what it does not solve, tag every co-author, put the arXiv link in the first comment.

**The carousel.** Papers are the best possible use of a LinkedIn document carousel. 8 to 10 slides:
1. Title card: the finding, not the paper title
2. The problem, one sentence, one visual
3. Why existing approaches fall short
4. The method, one diagram
5. to 7. Results, one figure per slide, each with a plain-language caption
8. The limitation
9. What is next
10. Authors, affiliations, arXiv link, code link

**Do not:** paste the abstract, use the paper title as the hook, list every author's full affiliation in the post body, claim SOTA without stating the benchmark and setup, or use the words "novel", "we propose", "extensive experiments demonstrate" in social copy.

---

## Product launch

**The core problem:** you know the product too well. The post explains features to people who do not yet have the problem.

Lead with the problem, and make it a problem the reader has had this month.

**Sequence:**

| Day | Channel | Form |
|---|---|---|
| -7 | Build-in-public teasers | Optional, only if the account already posts regularly |
| 0 | Landing page and demo video live | Everything links here |
| 0 | X | Main launch post with the demo video, native upload |
| 0 | Own Discord | Announcement with `@release` role ping |
| 0 | Hacker News / Product Hunt / relevant aggregators | If applicable |
| 1 | LinkedIn | Separately written, founder's account outperforms the company page |
| 1 | Substack / email list | The full story |
| 2 to 5 | Other communities | Soft share, staggered |
| 2 to 3 | Instagram | Carousel or Reel if the product is visual |
| 7 | Follow-up | What happened in week one, with real numbers |

The week-one follow-up is underrated. It gets a second wave of attention and it is more credible than the launch post because it has data in it.

---

## Feature release

Smaller surface, lower ceremony. The mistake here is treating a feature like a launch and burning audience patience.

- Own Discord `#changelog`, always. No ping unless it is breaking.
- X, one post, if it is genuinely interesting to people outside your users.
- LinkedIn only if there is a story behind it. "We shipped dark mode" is not a LinkedIn post. "We shipped dark mode after a user showed us they were using the product at 3am in a hospital" is.
- Email only if it changes how existing users work.
- Skip Instagram, Medium and YouTube unless the feature is visually demonstrable.

The best feature posts are about the bug, not the feature.

---

## OSS release

**Where it actually matters:** the README, Hacker News, relevant developer Discords, X. LinkedIn is secondary. Instagram is usually irrelevant.

- README first. It is the landing page and most traffic never goes anywhere else. Install command in the first screen.
- Use `styles/builder-technical.md` everywhere.
- Include the install line in every post. Reduce the distance between reading and trying to nothing.
- Post the architecture decision that people will argue with. Arguments are distribution.
- Answer the "why not just use X" question in the launch post itself.
- Show a terminal, not a logo.

---

## Content amplification

You published a blog post or article and want it read.

The post is the asset. Every channel gets a different extract, never the same teaser.

- **X:** pull the single best paragraph and post it as a standalone thought. Link in the reply. If the paragraph is good, people will click.
- **LinkedIn:** rewrite the argument as a native post of 900 to 1,300 characters that stands alone. Somebody who reads only the LinkedIn post should get value. Link in the comments.
- **Substack Notes:** the most surprising finding, standalone.
- **Discord:** share it where it answers a live question, not as a broadcast.
- **Medium:** import the post with a canonical link back to the original.

The rule: **never post a link with only a teaser line.** Give the value in the post itself. Counterintuitively, this increases clicks, because it demonstrates the piece is worth reading.

---

## Video launch

See `platforms/youtube.md` for the video itself. For distribution:

1. Publish on YouTube, pin a comment with links
2. Cut a 30 to 60 second vertical Short from the best moment
3. Upload that Short natively to X, Instagram Reels, and LinkedIn. Three separate native uploads, not links.
4. Upload the file directly to Discord if it fits under the size cap
5. Embed the full video in the blog or Substack post
6. A week later, post the single best 10-second clip as a standalone

Every platform suppresses links to competitors' video. Native upload every time.

---

## Milestone

Funding, hiring, an award, a user-count number, an anniversary.

The risk is that these posts are inherently about you, which makes them boring to everyone else. Fix that by making the post about something other than the milestone:

- Funding: what you are going to build with it, specifically
- Hiring: what the person will actually work on, and the hard problem they will own
- User number: what you learned from the users, with an example
- Anniversary: the thing you got wrong in year one

Channels: LinkedIn (primary), X, own Discord. Usually nothing else.

Thank people by name. Do not use the word "humbled".
