#!/usr/bin/env bash
#
# Archives the app in this directory and uploads it to TestFlight. No Xcode UI.
#
#   ./workspace/upload_testflight.sh                # bump build, archive, upload
#   ./workspace/upload_testflight.sh --validate     # everything but the upload
#   ./workspace/upload_testflight.sh --build 7      # force a build number
#   ./workspace/upload_testflight.sh --version 1.1  # also set the marketing version
#   ./workspace/upload_testflight.sh --no-bump      # reuse the current build number
#
# Requires an App Store Connect API key (see TESTFLIGHT.md "CLI upload"):
#
#   export ASC_KEY_ID=XXXXXXXXXX
#   export ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
#   export ASC_KEY_PATH=~/.appstoreconnect/private_keys/AuthKey_XXXXXXXXXX.p8
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Auto-detected so this script is drop-in for any project.
PROJECT="$(basename "$(ls -d "$PROJECT_ROOT"/*.xcodeproj 2>/dev/null | head -1)")"
[[ -n "$PROJECT" ]] || { echo "No .xcodeproj in $PROJECT_ROOT" >&2; exit 1; }
SCHEME="${SCHEME:-${PROJECT%.xcodeproj}}"
PBXPROJ="$PROJECT/project.pbxproj"
# Overridable, but this is the account's only team. See references/testflight.md.
TEAM_ID="${APPLE_TEAM_ID:-<TEAM_ID>}"
BUILD_DIR="$PROJECT_ROOT/build"
ARCHIVE_PATH="$BUILD_DIR/$SCHEME.xcarchive"
EXPORT_DIR="$BUILD_DIR/export"
EXPORT_OPTIONS="$BUILD_DIR/ExportOptions.plist"

say()  { printf "\n\033[1;33m==> %s\033[0m\n" "$1"; }
ok()   { printf "\033[1;32m%s\033[0m\n" "$1"; }
fail() { printf "\n\033[1;31mERROR: %s\033[0m\n" "$1" >&2; exit 1; }

# No step may die quietly. `set -e` otherwise aborts with no output at all.
trap 'status=$?; printf "\n\033[1;31mERROR: aborted at line %s (exit %s)\033[0m\n  command: %s\n" "$LINENO" "$status" "$BASH_COMMAND" >&2' ERR

# --- Arguments ---------------------------------------------------------------
VALIDATE_ONLY=false
BUMP=true
FORCED_BUILD=""
NEW_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --validate)  VALIDATE_ONLY=true; shift ;;
    --no-bump)   BUMP=false; shift ;;
    --build)     FORCED_BUILD="${2:?--build needs a number}"; BUMP=false; shift 2 ;;
    --version)   NEW_VERSION="${2:?--version needs a value like 1.1}"; shift 2 ;;
    -h|--help)   sed -n '2,20p' "$0"; exit 0 ;;
    *)           fail "Unknown option: $1  (try --help)" ;;
  esac
done

# --- 1. Preflight ------------------------------------------------------------
say "Preflight"

DEVELOPER_DIR_PATH="$(xcode-select -p 2>/dev/null || true)"
[[ "$DEVELOPER_DIR_PATH" == *"Xcode.app"* ]] || fail "Xcode is not selected. Run:
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"

if [[ "$VALIDATE_ONLY" == false ]]; then
  : "${ASC_KEY_ID:?Set ASC_KEY_ID — see TESTFLIGHT.md 'CLI upload'}"
  : "${ASC_ISSUER_ID:?Set ASC_ISSUER_ID — see TESTFLIGHT.md 'CLI upload'}"
  : "${ASC_KEY_PATH:?Set ASC_KEY_PATH — see TESTFLIGHT.md 'CLI upload'}"

  # Expand a leading ~, which does not expand inside quoted env vars.
  ASC_KEY_PATH="${ASC_KEY_PATH/#\~/$HOME}"
  [[ -f "$ASC_KEY_PATH" ]] || fail "API key not found at: $ASC_KEY_PATH"
fi

XCODE_VERSION="$(xcodebuild -version)"
echo "${XCODE_VERSION%%$'\n'*}"

if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  printf "\033[1;33mNote: working tree has uncommitted changes.\033[0m\n"
fi

# --- 2. Version numbers ------------------------------------------------------
say "Version"

# Read the whole settings dump before filtering. Piping xcodebuild into a
# command that exits early (head, grep -m1, awk with exit) gives it SIGPIPE,
# which pipefail turns into a script-killing failure.
SETTINGS="$(xcodebuild -showBuildSettings -project "$PROJECT" -scheme "$SCHEME" -configuration Release 2>/dev/null)"
read_setting() {
  printf '%s\n' "$SETTINGS" | awk -F' = ' -v key="$1" '$1 ~ ("^[[:space:]]*" key "$") { value = $2 } END { print value }'
}

CURRENT_BUILD="$(read_setting CURRENT_PROJECT_VERSION)"
CURRENT_VERSION="$(read_setting MARKETING_VERSION)"
[[ -n "$CURRENT_BUILD" ]] || fail "Could not read CURRENT_PROJECT_VERSION"

if [[ -n "$NEW_VERSION" ]]; then
  sed -i '' "s/MARKETING_VERSION = $CURRENT_VERSION;/MARKETING_VERSION = $NEW_VERSION;/g" "$PBXPROJ"
  echo "Marketing version: $CURRENT_VERSION -> $NEW_VERSION"
  CURRENT_VERSION="$NEW_VERSION"
fi

if [[ -n "$FORCED_BUILD" ]]; then
  TARGET_BUILD="$FORCED_BUILD"
elif [[ "$BUMP" == true ]]; then
  TARGET_BUILD=$((CURRENT_BUILD + 1))
else
  TARGET_BUILD="$CURRENT_BUILD"
fi

if [[ "$TARGET_BUILD" != "$CURRENT_BUILD" ]]; then
  # App Store Connect rejects a build number it has already seen, so this is
  # the one thing that must change on every upload.
  sed -i '' "s/CURRENT_PROJECT_VERSION = $CURRENT_BUILD;/CURRENT_PROJECT_VERSION = $TARGET_BUILD;/g" "$PBXPROJ"
fi

ok "Uploading as $CURRENT_VERSION ($TARGET_BUILD)"

# --- 3. App icon -------------------------------------------------------------
say "Generating app icon"
# The PNG is gitignored and Xcode will not create it. A missing or wrongly
# sized icon fails at upload, after the whole archive has been built.
swift workspace/make_icon.swift

# --- 4. Archive --------------------------------------------------------------
say "Archiving (Release)"

rm -rf "$ARCHIVE_PATH" "$EXPORT_DIR"
mkdir -p "$BUILD_DIR"

xcodebuild archive \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath "$ARCHIVE_PATH" \
  -allowProvisioningUpdates \
  | grep -E "error:|warning:|ARCHIVE|Signing" || true

[[ -d "$ARCHIVE_PATH" ]] || fail "Archive not produced at $ARCHIVE_PATH"
ok "Archived"

# --- 5. Export options -------------------------------------------------------
cat > "$EXPORT_OPTIONS" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>destination</key>
    <string>$([[ "$VALIDATE_ONLY" == true ]] && echo export || echo upload)</string>
    <key>teamID</key>
    <string>$TEAM_ID</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
PLIST

# --- 6. Export / upload ------------------------------------------------------
if [[ "$VALIDATE_ONLY" == true ]]; then
  say "Exporting .ipa (no upload)"
else
  say "Uploading to App Store Connect"
fi

EXPORT_ARGS=(
  -exportArchive
  -archivePath "$ARCHIVE_PATH"
  -exportOptionsPlist "$EXPORT_OPTIONS"
  -exportPath "$EXPORT_DIR"
  -allowProvisioningUpdates
)

if [[ "$VALIDATE_ONLY" == false ]]; then
  EXPORT_ARGS+=(
    -authenticationKeyPath "$ASC_KEY_PATH"
    -authenticationKeyID "$ASC_KEY_ID"
    -authenticationKeyIssuerID "$ASC_ISSUER_ID"
  )
fi

xcodebuild "${EXPORT_ARGS[@]}"

# --- 7. Done -----------------------------------------------------------------
if [[ "$VALIDATE_ONLY" == true ]]; then
  say "Exported to $EXPORT_DIR"
  echo "No upload was attempted (--validate)."
else
  say "Uploaded $CURRENT_VERSION ($TARGET_BUILD)"
  echo "Processing takes 5-30 min. Track it at:"
  echo "  https://appstoreconnect.apple.com/apps"
  echo
  echo "Once the build leaves 'Processing' it appears for your internal testers"
  echo "automatically, provided the group has 'Automatically distribute builds' on."
fi

echo
echo "Commit the version bump:"
echo "  git add $PBXPROJ && git commit -m \"Build $TARGET_BUILD\""
