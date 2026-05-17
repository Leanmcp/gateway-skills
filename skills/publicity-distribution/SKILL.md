---
name: publicity-distribution
description: Write and distribute launch and publicity content across LinkedIn, X/Twitter, Instagram, Discord, Medium, Substack, and YouTube. Produces per-platform copy that does not read as AI-written (no em dashes, no "thrilled to announce", no engagement-bait), plus the exact image/video specs and character limits each platform wants. Use this skill whenever the user wants to announce, launch, publicize, promote, cross-post, or share anything - a product, a feature, an open-source release, a research paper, a blog post, a demo video, a milestone, a job opening, or a conference talk. Trigger it on phrases like "post this on LinkedIn", "write a launch tweet", "announce this", "share this in Discord", "turn this into a thread", "what should I post", "write a Medium article about", "help me with distribution", "draft a YouTube description", "make this sound less like AI", or "de-slop this post". Also use it when the user has just finished shipping something and asks how to get it in front of people.
---

# Publicity and Distribution

Shipping something is half the work. This skill covers the other half: turning one thing you built into channel-native copy that people actually read, without it smelling like it came out of a language model.

## The two failure modes

Almost all bad launch content fails in one of two ways:

1. **It reads as AI-written.** Em dashes, "I'm thrilled to announce", rocket emojis, three perfectly parallel bullets, a closing question nobody will answer. Readers on LinkedIn and X have been trained to spot this in under a second and they scroll past it or, worse, mock it in the comments. Fixing this is not optional and it is not cosmetic.
2. **It is the same paragraph pasted five times.** A LinkedIn post and a tweet and a Discord message are different formats for different rooms. Copying one into the other five places is visible and it is lazy.

Everything below exists to avoid those two things.

## Workflow

### 1. Build the fact sheet first

Before writing any post, collect the raw material in one place. Do not skip this. Almost every weak post traces back to a writer who had nothing concrete to say and padded with adjectives.

Ask for or dig out:

- What exactly shipped, in one plain sentence a stranger would understand
- Who it is for, specifically (not "developers", but "people running evals on self-hosted models")
- The single most surprising number, before/after, or constraint (latency, cost, lines of code, time saved, accuracy)
- What was hard or what broke on the way. This is the most valuable item on the list and the one people forget to ask for.
- What it does NOT do yet
- The link, the repo, the paper, the demo
- Who else worked on it, by name

If the user cannot supply a concrete number or a real story, say so and ask for one rather than inventing filler. Never fabricate metrics, user counts, benchmark results, or quotes. If a number is unverified, leave a clearly marked `[NUMBER?]` placeholder in the draft instead of guessing.

### 2. Pick the campaign shape

What is being published changes the whole structure, not just the wording. Read the matching playbook in `references/campaign-playbooks.md`:

| What shipped | Playbook |
|---|---|
| Research paper / preprint | Paper launch |
| Product or company launch | Product launch |
| Feature or version release | Feature release |
| Open-source repo or tool | OSS release |
| Blog post or long-form write-up | Content amplification |
| Demo video | Video launch |
| Milestone, funding, hiring, personal news | Milestone |

### 3. Pick a voice

`styles/` holds the voice presets. Ask which one the user wants if it is not obvious from context, or infer it from how the user writes to you.

- `styles/professional.md` - measured, credible, no slang. Default for LinkedIn, papers, company accounts.
- `styles/whatsapp-lowercase.md` - all lowercase, short lines, conversational. Default for X, Discord, indie-builder audiences.
- `styles/builder-technical.md` - engineer-to-engineer. Specifics over adjectives. Default for OSS, Hacker News, dev Discords.

Voice is not the same thing as platform. You can post lowercase on LinkedIn and it works if the account has that personality. Hold the voice consistent across channels in a single campaign, and vary the format.

### 4. Draft per platform

Read only the platform files you actually need. Each contains the format rules, the character limits, the asset specs, and worked examples.

- `platforms/linkedin.md`
- `platforms/twitter-x.md`
- `platforms/instagram.md`
- `platforms/discord.md` - read this one carefully, it splits into "your own server" vs "someone else's server" and those are completely different jobs
- `platforms/medium.md`
- `platforms/substack.md`
- `platforms/youtube.md` - demo videos, scripts, thumbnails, Shorts

If you need every spec at once without the strategy, `references/asset-specs.md` is the one-page cheat sheet.

### 5. Run the de-AI pass

Before showing the user anything, run every draft through `references/anti-ai-tells.md`. This is a hard gate, not a nice-to-have. The file has a scan list and a rewrite table.

The single non-negotiable: **zero em dashes (—) and zero en dashes used as em dashes (–)**. Use a period, a comma, a colon, parentheses, or restructure the sentence. This applies to every output, including long-form.

### 6. Sequence the release

A launch is not one post. Give the user an ordered list with timing, because posting everywhere at once wastes the material. Default ladder:

1. Long-form first (Medium/Substack/blog) so there is something to link to
2. X thread, morning in your main audience's timezone
3. LinkedIn post, separately written, a few hours later or next morning
4. Your own Discord as a launch update, same day
5. Other people's Discords and communities, staggered over the following days, in soft-share form
6. Instagram carousel or Reel if the material is visual, day 2 or 3
7. YouTube demo whenever it is ready, then re-share the link into the channels above

### 7. Deliver

Format the handoff so the user can copy-paste and post. For each channel give:

- The copy, in a fenced block so nothing gets mangled
- Character count against the platform limit
- The asset spec needed (exact pixels, format, count)
- A one-line note on timing or where it goes

Then add a short "what I could not verify" list if any placeholders remain.

## Things that are always true

**Write the hook for someone who does not know you.** The first line on every platform is competing with the entire rest of the feed. It should be a concrete claim, a number, or a real observation. It should never be "Excited to share" or a restatement of the title.

**One idea per post.** If the material has three ideas, that is three posts, or one post and two follow-ups.

**Links suppress reach on LinkedIn and X.** Put the link in the first comment or a reply, and say in the post that it is there. On LinkedIn you can also edit the link into the post after the first hour.

**Specificity is the whole game.** "Made it faster" is noise. "Cut p99 from 1.8s to 240ms by batching the embedding calls" is a post. When a draft feels flat, the fix is almost never better adjectives. It is a concrete detail you left out.

**Credit people by name and tag them.** It is correct, and it is also the cheapest distribution there is.

**Do not claim things the artifact does not support.** If the benchmark is on one dataset, say one dataset. Overclaiming in public is expensive to walk back, and on technical platforms someone will check.
