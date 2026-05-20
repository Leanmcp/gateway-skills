#!/usr/bin/env bash
# Installs Godot 4 plus the export templates, on macOS or Linux, with or
# without a display.
#
#   bash install_godot.sh                 # engine only
#   bash install_godot.sh --templates     # engine + export templates
#   GODOT_VERSION=4.7.1 bash install_godot.sh --templates
#
# Export templates are the part everyone forgets. Without them `--export-release`
# fails with a message that sounds like a preset problem, and the usual fix
# ("open the editor, Manage Export Templates") is impossible on a headless VM.
# Installing them here is what makes web export and cloud deploy scriptable.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

WANT_TEMPLATES=0
[[ "${1:-}" == "--templates" ]] && WANT_TEMPLATES=1

OS="$(uname -s)"
ARCH="$(uname -m)"

# ------------------------------------------------------------------ engine
if EXISTING="$(find_godot 2>/dev/null)"; then
  ok "Godot already present: $EXISTING ($("$EXISTING" --version 2>/dev/null | head -1))"
else
  case "$OS" in
    Darwin)
      say "Installing Godot $GODOT_VERSION (macOS)"
      if command -v brew >/dev/null 2>&1; then
        brew install --cask godot
      else
        TMP="$(mktemp -d)"
        curl -fsSL -o "$TMP/godot.zip" \
          "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_macos.universal.zip"
        unzip -q -o "$TMP/godot.zip" -d /Applications
        rm -rf "$TMP"
      fi
      # A manual download carries the quarantine flag; the app refuses to launch
      # until it is cleared, and the error macOS shows blames the developer.
      xattr -dr com.apple.quarantine /Applications/Godot.app 2>/dev/null || true
      mkdir -p "$HOME/.local/bin"
      ln -sf "/Applications/Godot.app/Contents/MacOS/Godot" "$HOME/.local/bin/godot"
      ;;
    Linux)
      say "Installing Godot $GODOT_VERSION (Linux $ARCH)"
      case "$ARCH" in
        x86_64|amd64) SUFFIX="linux.x86_64" ;;
        aarch64|arm64) SUFFIX="linux.arm64" ;;
        *) die "unsupported architecture $ARCH" ;;
      esac
      TMP="$(mktemp -d)"
      curl -fsSL -o "$TMP/godot.zip" \
        "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_${SUFFIX}.zip"
      unzip -q -o "$TMP/godot.zip" -d "$TMP"
      mkdir -p "$HOME/.local/bin"
      mv "$TMP/Godot_v${GODOT_VERSION}-stable_${SUFFIX}" "$HOME/.local/bin/godot"
      chmod +x "$HOME/.local/bin/godot"
      rm -rf "$TMP"
      ;;
    *) die "unsupported OS $OS" ;;
  esac

  case ":${PATH}:" in
    *":$HOME/.local/bin:"*) : ;;
    *) warn "~/.local/bin is not on PATH. Add to your shell rc:
       export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
  esac
fi

require_godot
VER="$("$GODOT_BIN" --version 2>/dev/null | head -1 || true)"
[[ -n "$VER" ]] || die "Godot did not report a version"
ok "Godot $VER at $GODOT_BIN"
case "$VER" in 4.*) ;; *) warn "expected Godot 4.x, got '$VER'" ;; esac

# --------------------------------------------------------------- templates
if [[ "$WANT_TEMPLATES" == "1" ]]; then
  # Templates must match the engine build exactly. Ask the binary rather than
  # trusting GODOT_VERSION -- a brew install may be a different point release,
  # and a mismatch fails at export time with a confusing message.
  # `godot --version` prints e.g. 4.7.1.stable.official.1a2b3c4d -- take the
  # numeric head, which is also how the template directory is named.
  FULL="$(printf '%s' "$VER" | sed -E 's/\.(stable|beta|rc|dev|alpha).*$//')"
  DEST="$(godot_data_dir)/export_templates/${FULL}.stable"

  if [[ -d "$DEST" ]] && compgen -G "$DEST/*" >/dev/null; then
    ok "export templates already installed: $DEST"
  else
    say "Installing export templates ${FULL}"
    TMP="$(mktemp -d)"
    curl -fsSL -o "$TMP/tpz.zip" \
      "https://github.com/godotengine/godot/releases/download/${FULL}-stable/Godot_v${FULL}-stable_export_templates.tpz" \
      || die "could not download templates for ${FULL}. Check the version exists at
     https://github.com/godotengine/godot/releases"
    mkdir -p "$DEST"
    # The .tpz is a zip whose entries live under templates/.
    unzip -q -o "$TMP/tpz.zip" -d "$TMP"
    mv "$TMP"/templates/* "$DEST"/
    rm -rf "$TMP"
    ok "templates -> $DEST"
  fi
fi

# ------------------------------------------------------------------ extras
if command -v blender >/dev/null 2>&1 || [[ -d /Applications/Blender.app ]]; then
  ok "Blender present (needed only for regenerating .glb assets)"
else
  warn "Blender not installed. Only needed for build_assets.sh."
fi

echo
echo "${GREEN}${BOLD}Done.${OFF}"
echo "  bash $HERE/check_project.sh    # headless build check"
echo "  bash $HERE/run.sh              # play"
