#!/bin/sh
set -eu

README="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/README.md"

require_contains() {
  needle="$1"
  if ! grep -Fq "$needle" "$README"; then
    echo "Missing expected README reference: $needle" >&2
    exit 1
  fi
}

require_absent() {
  needle="$1"
  if grep -Fq "$needle" "$README"; then
    echo "Unexpected stale README reference: $needle" >&2
    exit 1
  fi
}

require_contains "https://img.shields.io/github/stars/Leanmcp/superview.sh?style=flat-square&color=yellow"
require_contains "https://github.com/Leanmcp/superview.sh/stargazers"
require_contains "https://www.star-history.com/?repos=Leanmcp%2Fsuperview.sh&type=date&legend=top-left"
require_contains "https://api.star-history.com/image?repos=Leanmcp/superview.sh&type=date&theme=dark&legend=top-left"
require_contains "https://api.star-history.com/image?repos=Leanmcp/superview.sh&type=date&legend=top-left"
require_absent "https://img.shields.io/github/stars/chatgptprojects/clear-code?style=for-the-badge&color=yellow"
require_absent "https://github.com/chatgptprojects/clear-code/stargazers"
require_absent "https://www.star-history.com/?repos=chatgptprojects%2Fclear-code&type=date&legend=top-left"
require_absent "https://api.star-history.com/image?repos=chatgptprojects/clear-code&type=date&theme=dark&legend=top-left"
require_absent "https://api.star-history.com/image?repos=chatgptprojects/clear-code&type=date&legend=top-left"

echo "README repository metrics references are correct."
