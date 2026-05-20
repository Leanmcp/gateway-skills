#!/usr/bin/env bash
# Headless build check: import the project, boot each scene, quit, and fail
# loudly if anything errored. No window opens, so this runs on CI and over SSH.
#
#   bash check_project.sh                          # main scene
#   bash check_project.sh res://scenes/city_sf.tscn res://scenes/city_sg.tscn
#   CITY=sg bash check_project.sh                  # with an env-selected variant
#   SECONDS_PER_SCENE=20 bash check_project.sh
#
# Why this exists: a procedural city is built in code at load time, so a typo in
# a generator does not show up until something instances it. `--import` alone
# will not catch that -- it only parses and imports resources. Actually booting
# the scene is the cheapest thing that exercises the generator end to end.
#
# The subtle part is the exit code. Godot exits 0 even when GDScript throws at
# runtime, so a green exit means nothing on its own. This scrapes the log for
# the error signatures Godot prints and fails on them, which is what turns the
# check into something you can gate a commit on.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
require_godot
require_project

SECONDS_PER_SCENE="${SECONDS_PER_SCENE:-30}"
# Godot counts --quit-after in frames when given an integer. At 60 fps a
# generous budget for a city that builds ~3000 buildings is a few hundred.
FRAMES=$(( SECONDS_PER_SCENE * 60 ))

SCENES=("$@")
if [[ ${#SCENES[@]} -eq 0 ]]; then
  MAIN="$(sed -n 's/^run\/main_scene="\(.*\)"$/\1/p' "$GODOT_PROJECT/project.godot" | head -1)"
  SCENES=("${MAIN:-res://scenes/main.tscn}")
fi

LOG="$(mktemp -t godot_check)"
trap 'rm -f "$LOG"' EXIT
failed=0

# Signatures Godot prints on the failures that matter. Warnings are deliberately
# not fatal -- they are too common to gate on and you will start ignoring them.
ERROR_PATTERN='SCRIPT ERROR|Parse Error|Compile Error|ERROR: |Failed to load|Cannot open|Invalid access|Condition ".*" is true'

say "Importing $GODOT_PROJECT"
if ! "$GODOT_BIN" --headless --path "$GODOT_PROJECT" --import >"$LOG" 2>&1; then
  echo "import failed:"; cat "$LOG"; exit 1
fi
if grep -qE 'SCRIPT ERROR|Parse Error' "$LOG"; then
  warn "import reported script errors:"
  grep -E -A3 'SCRIPT ERROR|Parse Error' "$LOG" | head -40
  failed=1
fi
ok "imported"

for SCENE in "${SCENES[@]}"; do
  echo
  say "Booting $SCENE (${SECONDS_PER_SCENE}s budget)"
  "$GODOT_BIN" --headless --path "$GODOT_PROJECT" \
      --quit-after "$FRAMES" "$SCENE" >"$LOG" 2>&1
  code=$?

  # Print whatever the game itself reported -- generators conventionally log a
  # one-line summary, and that line is the fastest signal that the build is sane.
  grep -E '^\[' "$LOG" | head -20 || true

  if [[ $code -ne 0 ]]; then
    warn "exited $code"
    tail -30 "$LOG"
    failed=1
  elif grep -qE "$ERROR_PATTERN" "$LOG"; then
    warn "errors during load:"
    grep -E -B1 -A4 "$ERROR_PATTERN" "$LOG" | head -60
    failed=1
  else
    ok "$SCENE built clean"
  fi
done

echo
if [[ $failed -ne 0 ]]; then
  die "check FAILED"
fi
echo "${GREEN}${BOLD}All scenes built clean.${OFF}"
