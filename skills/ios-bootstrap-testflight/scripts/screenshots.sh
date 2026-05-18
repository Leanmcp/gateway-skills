#!/usr/bin/env bash
#
# Captures App Store screenshots at Apple's required sizes.
#
#   ./workspace/screenshots.sh              # iPhone 6.9" + iPad 13"
#   ./workspace/screenshots.sh iphone       # iPhone only
#
# Apple validates screenshot dimensions exactly and rejects anything else, so
# the device models here are chosen for their native resolutions:
#
#   iPhone 6.9"  -> 1320 x 2868   (required for every iOS app)
#   iPad 13"     -> 2064 x 2752   (required only if the app supports iPad)
#
# The app is driven by hand: the script boots the simulator and installs the
# build, then waits while you navigate. UI automation for five screenshots costs
# more than it saves.
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PROJECT="$(basename "$(ls -d "$PROJECT_ROOT"/*.xcodeproj 2>/dev/null | head -1)")"
SCHEME="${SCHEME:-${PROJECT%.xcodeproj}}"
DERIVED_DATA="$PROJECT_ROOT/build/DerivedData"
OUT_DIR="$PROJECT_ROOT/screenshots"

say()  { printf "\n\033[1;33m==> %s\033[0m\n" "$1"; }
fail() { printf "\n\033[1;31mERROR: %s\033[0m\n" "$1" >&2; exit 1; }
trap 'status=$?; printf "\n\033[1;31mERROR: aborted at line %s (exit %s)\033[0m\n  command: %s\n" "$LINENO" "$status" "$BASH_COMMAND" >&2' ERR

case "${1:-all}" in
  iphone) DEVICES=("iPhone 17 Pro Max") ;;
  ipad)   DEVICES=("iPad Pro 13-inch (M4)") ;;
  all)    DEVICES=("iPhone 17 Pro Max" "iPad Pro 13-inch (M4)") ;;
  *)      fail "Usage: $0 [iphone|ipad|all]" ;;
esac

# Shots to take, in order. Names become filenames, and App Store Connect orders
# screenshots the way you upload them.
SHOTS=(
  "1-home"
  "2-board"
  "3-merge"
  "4-autopilot"
  "5-settings"
)

BUNDLE_ID="$(xcodebuild -showBuildSettings -project "$PROJECT" -scheme "$SCHEME" -configuration Debug 2>/dev/null \
  | awk -F' = ' '$1 ~ /^[[:space:]]*PRODUCT_BUNDLE_IDENTIFIER$/ { v=$2 } END { print v }')"
[[ -n "$BUNDLE_ID" ]] || fail "Could not read PRODUCT_BUNDLE_IDENTIFIER"

for DEVICE in "${DEVICES[@]}"; do
  say "Preparing $DEVICE"

  UDID="$(xcrun simctl list devices available --json \
    | python3 -c '
import json, sys
name = sys.argv[1]
data = json.load(sys.stdin)
for runtime, devices in data["devices"].items():
    if "iOS" not in runtime:
        continue
    for device in devices:
        if device["name"] == name:
            print(device["udid"])
            raise SystemExit
' "$DEVICE" || true)"

  if [[ -z "$UDID" ]]; then
    printf "\033[1;33mSkipping %s — not installed. Add it in Xcode > Windows > Devices and Simulators.\033[0m\n" "$DEVICE"
    continue
  fi

  xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration Debug \
    -destination "id=$UDID" -derivedDataPath "$DERIVED_DATA" \
    CODE_SIGNING_ALLOWED=NO build 2>&1 | grep -E "error:|BUILD" || true

  APP="$DERIVED_DATA/Build/Products/Debug-iphonesimulator/$SCHEME.app"
  [[ -d "$APP" ]] || fail "Build produced no app at $APP"

  xcrun simctl bootstatus "$UDID" -b
  open -a Simulator --args -CurrentDeviceUDID "$UDID"

  # A clean status bar looks deliberate. Apple's own marketing uses 9:41.
  xcrun simctl status_bar "$UDID" override --time "9:41" --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3 || true

  xcrun simctl install "$UDID" "$APP"
  xcrun simctl launch "$UDID" "$BUNDLE_ID"

  DEVICE_DIR="$OUT_DIR/$(echo "$DEVICE" | tr ' ' '-')"
  mkdir -p "$DEVICE_DIR"

  say "Capturing — set up each screen, then press Enter"
  for SHOT in "${SHOTS[@]}"; do
    read -r -p "  $SHOT  (Enter to capture, s to skip) " ANSWER </dev/tty
    [[ "$ANSWER" == "s" ]] && continue
    xcrun simctl io "$UDID" screenshot "$DEVICE_DIR/$SHOT.png"
    SIZE="$(sips -g pixelWidth -g pixelHeight "$DEVICE_DIR/$SHOT.png" | awk '/pixel/{printf "%s ", $2}')"
    echo "    saved ${SHOT}.png  (${SIZE})"
  done

  xcrun simctl status_bar "$UDID" clear || true
done

say "Screenshots in $OUT_DIR"
echo "Upload these in App Store Connect under the version's Previews and Screenshots."
