#!/usr/bin/env bash
# Play the game without opening the editor.
#
#   bash run.sh                       # main scene
#   bash run.sh res://scenes/city_sg.tscn
#   CITY=sg bash run.sh               # if the project reads a CITY env var
#   bash run.sh --editor              # open the editor instead
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
require_godot
require_project

if [[ "${1:-}" == "--editor" ]]; then
  say "Editing $GODOT_PROJECT"
  exec "$GODOT_BIN" --editor --path "$GODOT_PROJECT"
fi

say "Running $GODOT_PROJECT"
exec "$GODOT_BIN" --path "$GODOT_PROJECT" "$@"
