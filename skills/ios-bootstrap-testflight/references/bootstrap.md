# Bootstrapping a new iOS app

## Machine setup (once per Mac)

```bash
# Xcode from the Mac App Store first, then:
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
sudo xcodebuild -runFirstLaunch
time xcodebuild -downloadPlatform iOS      # ~10 GB, 20-40 min
```

Verify — this is the definitive check that builds will work:

```bash
xcodebuild -showdestinations -project <name>.xcodeproj -scheme <name>
```

No `platform:iOS Simulator` rows means the platform download hasn't finished.
Every build fails with *"iOS <version> is not installed"* until it does.

**Disk:** Xcode needs ~40 GB free. `df -h /` reports the sealed system volume
and lies; use `df -h /System/Volumes/Data`. Usual reclaim targets:
`brew cleanup --prune=all`, `~/.cache/uv`, `~/Library/Caches/*`,
`docker system prune -a`.

**First GUI launch** shows a components picker with iOS pre-checked at ~10 GB.
If the platform was already downloaded via CLI, uncheck it — nothing is missing.
Uncheck "Predictive Code Completion Model" too unless it's wanted (2 GB).

## Writing the .xcodeproj by hand

A minimal Xcode 16+ project file is short because of
`PBXFileSystemSynchronizedRootGroup`: point it at a *directory* and every file
inside compiles automatically. No `PBXBuildFile` entries, no per-file
bookkeeping, and empty `Sources`/`Resources` build phases are correct.

Requires `objectVersion = 77` and Xcode 16+. Adding a `.swift` file then needs
no project edit at all.

Structure:

```
MyApp.xcodeproj/
├── project.pbxproj
├── project.xcworkspace/contents.xcworkspacedata
└── xcshareddata/xcschemes/MyApp.xcscheme    ← must be committed
MyApp/
├── MyAppApp.swift          @main entry point
├── ContentView.swift
└── Assets.xcassets/{Contents.json,AppIcon.appiconset/,AccentColor.colorset/}
```

The shared scheme **must** be checked in — `xcodebuild -scheme` cannot find
auto-generated schemes, which live in gitignored `xcuserdata/`. Its
`BlueprintIdentifier` must match the `PBXNativeTarget` id exactly or it silently
references nothing.

### Build settings worth setting deliberately

```
GENERATE_INFOPLIST_FILE = YES          # no Info.plist file needed
INFOPLIST_KEY_ITSAppUsesNonExemptEncryption = NO   # skips the export-compliance
                                                   # prompt on every upload
INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone = UIInterfaceOrientationPortrait
CODE_SIGN_STYLE = Automatic
DEVELOPMENT_TEAM = <team id>           # see references/testflight.md
IPHONEOS_DEPLOYMENT_TARGET = 17.0
```

Committing `DEVELOPMENT_TEAM` is normally discouraged as per-developer, but for
a solo project it removes a whole category of signing confusion. Worth it.

## Verifying without a full build

```bash
swiftc -parse MyApp/*.swift          # syntax only, no iOS SDK needed, instant
```

Catches syntax errors but **not** type errors — it can't resolve UIKit/SwiftUI
without the iOS SDK. Useful as a fast pre-check, never as proof it compiles.

## .gitignore

Keep it short. The stock `Swift.gitignore` omits the things that actually
matter:

```
.DS_Store
build/
DerivedData/
*.xcarchive
*.xcuserstate
*.p8
```

`xcshareddata/` must stay tracked. And note `.gitignore` never untracks files
already committed — use `git rm -r --cached build/` for those.
