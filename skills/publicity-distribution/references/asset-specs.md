# Asset specs cheat sheet

Every dimension and limit in one place, for when you need the number without the strategy. Verified September 2026. Platforms change these, so if a number is load-bearing for a paid campaign, confirm against the platform's own documentation.

## Images

| Platform | Format | Dimensions | Ratio | Max size |
|---|---|---|---|---|
| LinkedIn | Portrait (recommended) | 1080 x 1350 | 4:5 | 5 MB |
| LinkedIn | Square | 1080 x 1080 | 1:1 | 5 MB |
| LinkedIn | Landscape / link preview | 1200 x 627 | 1.91:1 | 5 MB |
| LinkedIn | Document carousel (PDF) | 1080 x 1080 or 1080 x 1350 | 1:1 or 4:5 | 100 MB, 300 pages |
| X | Landscape | 1200 x 675 | 16:9 | 5 MB |
| X | Link preview card | 1200 x 628 | 1.91:1 | 5 MB |
| X | Vertical | 1080 x 1350 | 4:5 | 5 MB |
| X | GIF | | | 15 MB |
| Instagram | Feed (recommended) | 1080 x 1350 | 4:5 | |
| Instagram | Feed square | 1080 x 1080 | 1:1 | |
| Instagram | Grid preview crop | 1080 x 1440 | 3:4 | |
| Instagram | Carousel | 1080 x 1350 | 4:5 | up to 20 slides |
| Instagram | Stories / Reels cover | 1080 x 1920 | 9:16 | |
| Medium | Cover image | 1200 x 680 | ~1.76:1 | 25 MB |
| Medium | Inline full width | 1400 px wide | | 25 MB |
| Medium | Inline in-column | 700 px wide | | 25 MB |
| Substack | Post cover | 1200 x 630 | 1.91:1 | 10 MB |
| Substack | Inline | up to 1200 px wide | | 10 MB |
| Substack | Wordmark | 1344 x 256 | 21:4 | |
| YouTube | Thumbnail | 1280 x 720 | 16:9 | 2 MB |
| YouTube | Channel banner | 2560 x 1440 (safe area 1546 x 423) | | 6 MB |

## Video

| Platform | Dimensions | Ratio | Max length | Max size |
|---|---|---|---|---|
| LinkedIn | 1920 x 1080 or 1080 x 1920 | 16:9 or 9:16 | 15 min | 5 GB |
| X | 1280 x 720 or 1920 x 1080 | 16:9, 9:16, 1:3 to 3:1 | 140 s standard | 512 MB |
| Instagram Reels | 1080 x 1920 | 9:16 | 3 min | |
| Instagram Stories | 1080 x 1920 | 9:16 | 60 s per frame | |
| YouTube | 1920 x 1080 | 16:9 | no practical limit | 256 GB |
| YouTube Shorts | 1080 x 1920 | 9:16 | 3 min | |
| Substack | 1080p recommended, 4K supported | | | 20 GB |
| Discord | any | any | any | 10 MB free, more with boosts |

**Encoding everywhere:** MP4 container, H.264 video, AAC audio, 30 or 60 fps. X accepts MOV as well.

## Text limits

| Platform | Field | Limit | Visible before truncation |
|---|---|---|---|
| LinkedIn | Post | 3,000 | ~140 mobile, ~200 desktop |
| LinkedIn | Comment | 1,250 | |
| LinkedIn | Article | 110,000 | |
| LinkedIn | Poll question / option | 140 / 30 | max 4 options |
| X | Post | 280 (25,000 Premium) | all |
| X | Alt text | 1,000 | |
| Instagram | Caption | 2,200 | ~125 |
| Instagram | Hashtags | 30 max | use 3 to 5 |
| Medium | Title / subtitle | 140 / 140 | |
| Medium | Tags | 5 | |
| Medium | Newsletter subject | 150 | |
| Substack | Title / subtitle | 100 / 250 | |
| Substack | Publication description | 255 | |
| Discord | Message | 2,000 (4,000 Nitro) | |
| Discord | Embed description | 4,096 | total 6,000 across embeds |
| Discord | Embeds per message | 10 | |
| YouTube | Title | 100 | ~70 |
| YouTube | Description | 5,000 | ~150 |
| YouTube | Chapter title | 100 | ~40 desktop, ~25 mobile |
| YouTube | Tags (total) | 500 | |

## Safe zones

- **Instagram Stories / Reels:** keep text out of the top 250 px and bottom 420 px.
- **YouTube thumbnail:** avoid the bottom right, the duration stamp sits there.
- **YouTube banner:** only the central 1546 x 423 is visible on every device.
- **LinkedIn document carousel:** leave a margin, the viewer adds chrome at the bottom.

## One asset set that covers everything

If you are producing a minimal kit for a launch, make these five:

1. `1080x1350` portrait image. Works on LinkedIn, X and Instagram feed.
2. `1200x630` landscape. Link preview card for Substack, Medium cover, og:image.
3. `1280x720` thumbnail. YouTube.
4. `1080x1920` vertical video, under 60 s. Reels, Shorts, X, LinkedIn vertical.
5. `1080x1350` carousel, 6 to 10 slides, exported as PDF for LinkedIn and PNGs for Instagram.
