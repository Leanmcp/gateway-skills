#!/usr/bin/env bash
#
# Builds the app in this directory and launches it in the iOS Simulator.
#
#   ./workspace/run.sh                 # default simulator (iPhone 16 Pro, else first available)
#   ./workspace/run.sh "iPhone 15"     # a specific simulator by name
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Auto-detected so this script is drop-in for any project.
PROJECT="$(basename "$(ls -d "$PROJECT_ROOT"/*.xcodeproj 2>/dev/null | head -1)")"
[[ -n "$PROJECT" ]] || { echo "No .xcodeproj in $PROJECT_ROOT" >&2; exit 1; }
SCHEME="${SCHEME:-${PROJECT%.xcodeproj}}"
DERIVED_DATA="$PROJECT_ROOT/build/DerivedData"
REQUESTED_DEVICE="${1:-}"

say()  { printf "\n\033[1;33m==> %s\033[0m\n" "$1"; }
fail() { printf "\n\033[1;31mERROR: %s\033[0m\n" "$1" >&2; exit 1; }

# Nothing may exit quietly. `set -e` aborts on any non-zero status, and without
# this trap that abort prints nothing at all — which is indistinguishable from
# success at a glance. Report the line and the command that actually failed.
trap 'status=$?; printf "\n\033[1;31mERROR: aborted at line %s (exit %s)\033[0m\n  command: %s\n" "$LINENO" "$status" "$BASH_COMMAND" >&2' ERR

# --- 1. Toolchain ------------------------------------------------------------
say "Checking toolchain"

DEVELOPER_DIR_PATH="$(xcode-select -p 2>/dev/null || true)"
if [[ "$DEVELOPER_DIR_PATH" != *"Xcode.app"* ]]; then
  fail "Xcode is not selected (currently: ${DEVELOPER_DIR_PATH:-none}).
  Install Xcode from the Mac App Store, then run:
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
fi
# Deliberately NOT `xcodebuild -version | head -1`. `head` exits after the first
# line and closes the pipe, xcodebuild takes SIGPIPE, and `set -o pipefail` turns
# that into a script-killing failure — intermittently, depending on which process
# wins the race. Capture the whole output, then trim.
XCODE_VERSION="$(xcodebuild -version)"
echo "${XCODE_VERSION%%$'\n'*}"

# --- 2. App icon -------------------------------------------------------------
# Always regenerate. Skipping when the file exists means a bad icon from an
# earlier run sticks around and keeps failing the asset-catalog compile.
say "Generating app icon"
swift workspace/make_icon.swift

# --- 3. Pick a simulator -----------------------------------------------------
say "Selecting simulator"

pick_udid() {
  # Args: optional device name filter. Prints "UDID<TAB>Name" of a booted or
  # available iOS simulator, preferring one that is already booted.
  local filter="${1:-}"
  xcrun simctl list devices available --json \
    | python3 -c '
import json, sys
filter_name = sys.argv[1] if len(sys.argv) > 1 else ""
data = json.load(sys.stdin)
candidates = []
for runtime, devices in data["devices"].items():
    if "iOS" not in runtime:
        continue
    for device in devices:
        if filter_name and filter_name.lower() not in device["name"].lower():
            continue
        candidates.append((device["state"] == "Booted", "iPhone" in device["name"], device))
if not candidates:
    sys.exit(1)
candidates.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
chosen = candidates[0][2]
print(chosen["udid"] + "\t" + chosen["name"])
' "$filter"
}

SELECTION="$(pick_udid "$REQUESTED_DEVICE" || true)"
if [[ -z "$SELECTION" && -n "$REQUESTED_DEVICE" ]]; then
  echo "No simulator matching \"$REQUESTED_DEVICE\"; falling back to any iPhone."
  SELECTION="$(pick_udid "iPhone 16 Pro" || pick_udid || true)"
fi
[[ -n "$SELECTION" ]] || fail "No iOS simulators installed. Open Xcode → Settings → Components and download an iOS runtime."

UDID="${SELECTION%%$'\t'*}"
DEVICE_NAME="${SELECTION#*$'\t'}"
echo "$DEVICE_NAME ($UDID)"

# --- 4. Build ----------------------------------------------------------------
say "Building $SCHEME"

xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration Debug \
  -destination "id=$UDID" \
  -derivedDataPath "$DERIVED_DATA" \
  CODE_SIGNING_ALLOWED=NO \
  build

APP_PATH="$DERIVED_DATA/Build/Products/Debug-iphonesimulator/$SCHEME.app"
[[ -d "$APP_PATH" ]] || fail "Build succeeded but $APP_PATH is missing."

# --- 5. Boot, install, launch ------------------------------------------------
# Read the bundle id from the build rather than hardcoding it.
BUNDLE_ID="$(xcodebuild -showBuildSettings -project "$PROJECT" -scheme "$SCHEME" -configuration Debug 2>/dev/null \
  | awk -F' = ' '$1 ~ /^[[:space:]]*PRODUCT_BUNDLE_IDENTIFIER$/ { v=$2 } END { print v }')"
[[ -n "$BUNDLE_ID" ]] || { echo "Could not read PRODUCT_BUNDLE_IDENTIFIER" >&2; exit 1; }

say "Booting simulator"
xcrun simctl bootstatus "$UDID" -b
open -a Simulator --args -CurrentDeviceUDID "$UDID"

say "Installing"
xcrun simctl install "$UDID" "$APP_PATH"

say "Launching"
xcrun simctl launch "$UDID" "$BUNDLE_ID"

say "$SCHEME is running on $DEVICE_NAME"
echo "Screenshot it with:  xcrun simctl io $UDID screenshot ~/Desktop/twenty48.png"
