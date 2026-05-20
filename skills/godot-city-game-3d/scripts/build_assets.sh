#!/usr/bin/env bash
# Regenerate .glb models from the Blender generator scripts.
#
#   bash build_assets.sh                 # every gen_*.py found
#   bash build_assets.sh drone weapon    # named generators only
#   BLENDER=/path/to/blender bash build_assets.sh
#   ASSETS_DIR=workspace/assets bash build_assets.sh
#
# Generating models instead of hand-modelling them is what makes the art
# reviewable: the source is diffable Python in git, a bad edit is `git checkout`
# rather than a redownload, and every asset is parametric. The cost is that the
# build must actually be run, so it needs to be one command.
#
# Blender is chatty. Only the per-asset report lines are shown on success; on
# failure the traceback is printed, because that is when you need the log.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ASSETS="${ASSETS_DIR:-$ROOT/workspace/assets}"
[[ -d "$ASSETS" ]] || die "no generator directory at $ASSETS (set ASSETS_DIR)"

# ------------------------------------------------------------------ blender
if [[ -z "${BLENDER:-}" ]]; then
  for c in \
      "$(command -v blender 2>/dev/null || true)" \
      "/Applications/Blender.app/Contents/MacOS/Blender" \
      "/usr/local/bin/blender"; do
    [[ -n "$c" && -x "$c" ]] && { BLENDER="$c"; break; }
  done
fi
[[ -n "${BLENDER:-}" && -x "$BLENDER" ]] || die "Blender not found.
   Install from https://www.blender.org/download/ (free, GPL), or:
   BLENDER=/path/to/blender bash $0"

say "blender: $("$BLENDER" --version 2>/dev/null | head -1)"
say "sources: $ASSETS"

# ---------------------------------------------------------------- selection
GENERATORS=("$@")
if [[ ${#GENERATORS[@]} -eq 0 ]]; then
  for f in "$ASSETS"/gen_*.py; do
    [[ -e "$f" ]] || continue
    n="$(basename "$f")"; n="${n#gen_}"; n="${n%.py}"
    GENERATORS+=("$n")
  done
fi
[[ ${#GENERATORS[@]} -gt 0 ]] || die "no gen_*.py generators in $ASSETS"

LOG="$(mktemp -t build_assets)"
trap 'rm -f "$LOG"' EXIT
failed=0

for name in "${GENERATORS[@]}"; do
  script="$ASSETS/gen_${name}.py"
  [[ -f "$script" ]] || { warn "no generator named '$name' ($script)"; failed=1; continue; }

  echo "== $name"
  # --factory-startup ignores the user's Blender config, so the build is the
  # same on every machine regardless of installed addons or preferences.
  if "$BLENDER" --background --factory-startup --python "$script" >"$LOG" 2>&1; then
    grep -E '\.glb' "$LOG" | head -30 || {
      warn "no assets reported; full log:"; cat "$LOG"; failed=1; }
  else
    warn "FAILED:"
    sed -n '/Traceback/,$p' "$LOG" | head -40 || tail -20 "$LOG"
    failed=1
  fi
  echo
done

[[ $failed -eq 0 ]] || die "build finished with errors"
ok "done. Now reimport so Godot picks them up:  bash $HERE/import_assets.sh"
