---
name: ios-bootstrap-testflight
description: Scaffold a native iOS app (SwiftUI, no dependencies) from nothing, run it in the Simulator, and archive + upload it to TestFlight entirely from the command line. Bundles working scripts for icon generation, simulator run, and signed upload via the App Store Connect API. Use this whenever the user wants to build, run, ship, or debug an iOS/iPhone/iPad app, mentions Xcode, SwiftUI, .xcodeproj, xcodebuild, simctl, provisioning, code signing, App Store Connect, TestFlight, archiving, or "get this on my phone" — and also when an existing iOS build is failing on icons, signing, teams, destinations, or duplicate build numbers.
---

# iOS bootstrap → TestFlight

Two jobs: create an iOS app that builds, and get it onto a real phone. Both are
almost entirely CLI. Xcode's UI is only needed for first-time account setup.

## Read next

| File | When |
|---|---|
| `references/bootstrap.md` | Creating a new project, or the project won't open/build |
| `references/testflight.md` | Signing, archiving, uploading. **Holds the user's Team ID and API key details.** |
| `references/appstore.md` | Public release — screenshots, metadata, privacy policy, review. Read the 4.3 risk section *before* the user invests in assets. |
| `references/caveats.md` | Anything looks wrong on device — button styling, layout, gestures, animation |

## Scripts

Copy into the project's `workspace/` and run from the project root. They
auto-detect the `.xcodeproj` and scheme, so they work unmodified in any project.

```bash
mkdir -p workspace
cp ~/.claude/skills/ios-bootstrap-testflight/scripts/* workspace/
chmod +x workspace/*.sh
```

| Script | Does |
|---|---|
| `make_icon.swift` | Renders a 1024×1024 App Store icon into the asset catalog |
| `run.sh` | Build → boot simulator → install → launch |
| `upload_testflight.sh` | Bump build number → icon → archive → upload to TestFlight |
| `screenshots.sh` | Captures App Store screenshots at Apple's exact required sizes |

```bash
time ./workspace/run.sh                          # test locally
time ./workspace/upload_testflight.sh --validate # archive only, no API key needed
time ./workspace/upload_testflight.sh            # bump + archive + upload
```

## The rule that saves the most time

**Never run `xcodebuild` raw and read the output.** It emits thousands of lines
and buries the one that matters. Always filter:

```bash
xcodebuild ... 2>&1 | grep -E "error:|warning:|BUILD"
```

A build can print `** BUILD FAILED **` while every Swift file compiled fine —
asset catalog and signing failures look identical to code failures in raw logs.
Check *which* build command failed before assuming the code is broken.

## Environment expectations

- Xcode (full app, not Command Line Tools) — `xcode-select -p` must contain `Xcode.app`
- ~40 GB free disk for Xcode + one iOS platform
- Apple Developer Program membership for TestFlight (free tier cannot upload)

If any of that is missing, `references/bootstrap.md` has the setup commands in
order.
