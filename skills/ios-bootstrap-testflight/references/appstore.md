# Public App Store release

TestFlight needs only a build. A public release additionally needs screenshots,
metadata, a hosted privacy policy, and Apple review (1–3 days).

Everything in `testflight.md` still applies — same signing, same upload script.
This is the extra work on top.

## Read the risk first

**Guideline 4.3 (Spam)** is the most likely rejection for any app implementing a
saturated concept — puzzle clones, flashlights, to-do lists, calculators. It is
more likely than any technical failure, and it costs days to discover.

Worth checking before investing in screenshots and copy: does this app do
something the existing ones don't? If yes, lead with that in the description and
in the *first* screenshot. If not, say so plainly rather than letting the user
find out via rejection.

If rejected under 4.3, the productive reply in Resolution Center is a concrete
feature-by-feature list of what differs — not an appeal on principle.

## 1. Screenshots

Apple validates dimensions exactly and rejects anything else.

| Size | Pixels | Required |
|---|---|---|
| iPhone 6.9" | 1320 × 2868 | Always |
| iPad 13" | 2064 × 2752 | Only if `TARGETED_DEVICE_FAMILY` includes `2` |

Dropping iPad support (`TARGETED_DEVICE_FAMILY = "1"`) halves this work and is
worth raising with the user before they capture anything.

```bash
./workspace/screenshots.sh          # both devices
./workspace/screenshots.sh iphone   # iPhone only
```

The script builds, boots the right simulator, fakes a clean 9:41 status bar, and
pauses before each shot so the screen can be set up by hand. UI automation for
five screenshots costs more than it saves.

Minimum one per size; three to five is better. The first one does most of the
work — make it the most distinctive thing the app does, not a splash screen.

## 2. Privacy policy

Required, and must be a live public URL — App Store Connect rejects a version
without one. GitHub Pages is the fastest host.

An app that makes no network calls and uses only local `UserDefaults` collects
nothing, and the policy should say so in plain language rather than hedging with
boilerplate. Apple does not count on-device storage as collection.

## 3. Metadata

| Field | Notes |
|---|---|
| Subtitle | 30 chars |
| Keywords | 100 chars, comma separated, **no spaces after commas** — spaces waste the budget |
| Promotional text | 170 chars, editable later **without review** — the only field that is |
| Description | Lead with what makes it different, not what it is |
| Support URL | Required. A repo page is fine. |
| Category, age rating, price | Age rating is a questionnaire; all-No gives 4+ |

## 4. App Privacy questionnaire

App Store Connect → **App Privacy**. For an app with no network access:
**"No, we do not collect data from this app."**

## 5. Submit

Version page → **Build** → **+** → select the build → resolve any yellow
warnings → **Add for Review** → **Submit to App Review**.

Rejections arrive in Resolution Center citing a specific guideline number and
are usually fixable without a new build.

## Updates after release

```bash
./workspace/upload_testflight.sh --version 1.2
```

Create a new version in App Store Connect, attach the build, submit. Every
update is reviewed; later reviews are usually faster.
