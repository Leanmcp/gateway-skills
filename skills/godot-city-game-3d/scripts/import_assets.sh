#!/usr/bin/env bash
# Reimport art assets without opening the editor GUI. Run after dropping new
# .glb / texture files into the project.
#
#   bash import_assets.sh
#
# Godot only imports when it has focus, or when told to. On a headless machine
# there is no focus, so this is the only way -- and it is also what you want in
# CI, where the .godot/imported cache is usually gitignored and must be rebuilt.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
require_godot
require_project

say "Importing assets in $GODOT_PROJECT"
"$GODOT_BIN" --headless --path "$GODOT_PROJECT" --import
ok "done"
