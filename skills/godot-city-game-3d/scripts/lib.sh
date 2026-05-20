#!/usr/bin/env bash
# Sourced by every other script here. Resolves the two things that differ on
# every machine -- where Godot is, and where the project is -- so that no other
# script has to hardcode a path. That is what lets the same commands work on a
# laptop, a CI runner and a headless cloud VM without edits.
#
#   source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
#
# Override either by exporting GODOT_BIN or GODOT_PROJECT.

BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; OFF=$'\033[0m'
say()  { echo "${BOLD}==>${OFF} $*"; }
ok()   { echo "${GREEN}  ok${OFF} $*"; }
warn() { echo "${YELLOW}  !!${OFF} $*" >&2; }
die()  { echo "${RED}  xx${OFF} $*" >&2; exit 1; }

GODOT_VERSION="${GODOT_VERSION:-4.7.1}"

# ------------------------------------------------------------------- godot
# Search order puts an explicit override first, then a PATH install (which is
# what CI and Linux VMs have), then the macOS app bundle.
find_godot() {
  local c
  for c in \
      "${GODOT_BIN:-}" \
      "$(command -v godot 2>/dev/null || true)" \
      "$HOME/.local/bin/godot" \
      "/Applications/Godot.app/Contents/MacOS/Godot" \
      "/usr/local/bin/godot" \
      "/opt/godot/godot"; do
    if [[ -n "$c" && -x "$c" ]]; then
      printf '%s' "$c"
      return 0
    fi
  done
  return 1
}

require_godot() {
  GODOT_BIN="$(find_godot)" || die "Godot not found. Install it:
     bash \"$(dirname "${BASH_SOURCE[0]}")/install_godot.sh\"
   or point at an existing binary:  export GODOT_BIN=/path/to/godot"
  export GODOT_BIN
}

# ----------------------------------------------------------------- project
# A Godot project is the directory holding project.godot. Walk up from the
# working directory, then try the common nested layouts, so the caller can be
# standing anywhere in the repo.
find_project() {
  if [[ -n "${GODOT_PROJECT:-}" ]]; then
    [[ -f "$GODOT_PROJECT/project.godot" ]] || return 1
    ( cd "$GODOT_PROJECT" && pwd )
    return 0
  fi

  local d="$PWD"
  while [[ "$d" != "/" ]]; do
    if [[ -f "$d/project.godot" ]]; then printf '%s' "$d"; return 0; fi
    for sub in game godot client; do
      if [[ -f "$d/$sub/project.godot" ]]; then printf '%s' "$d/$sub"; return 0; fi
    done
    d="$(dirname "$d")"
  done
  return 1
}

require_project() {
  GODOT_PROJECT="$(find_project)" || die "No project.godot found from $PWD.
   Run from inside the repo, or:  export GODOT_PROJECT=/path/to/project"
  export GODOT_PROJECT
}

# Godot writes editor/export config under these. Knowing them is what lets the
# installer drop export templates in without opening the GUI.
godot_data_dir() {
  case "$(uname -s)" in
    Darwin) printf '%s' "$HOME/Library/Application Support/Godot" ;;
    *)      printf '%s' "${XDG_DATA_HOME:-$HOME/.local/share}/godot" ;;
  esac
}
