#!/usr/bin/env bash
# Export to WebAssembly and serve it locally with the headers the build needs.
#
#   bash export_web.sh              # export + serve on :8000
#   PORT=9000 bash export_web.sh
#   bash export_web.sh --no-serve   # export only (for uploading somewhere)
#
# This is the cheapest way to put the game in front of other people: it runs on
# whoever opens the page, so there is no GPU server, no per-hour cost and no
# concurrency limit. The tradeoff is the renderer -- browsers run WebGL 2 only,
# which means the Compatibility backend. A project authored for Forward+ (SSAO,
# SSIL, glow, volumetric fog) will look flatter here. Budget art-tuning time.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"
require_godot
require_project

PORT="${PORT:-8000}"
OUT="${OUT:-$(dirname "$GODOT_PROJECT")/build/web}"
SERVE=1
[[ "${1:-}" == "--no-serve" ]] && SERVE=0

python3 "$HERE/ensure_export_presets.py" --project "$GODOT_PROJECT" --preset Web

say "Exporting web build -> $OUT"
mkdir -p "$OUT"
if ! "$GODOT_BIN" --headless --path "$GODOT_PROJECT" \
      --export-release "Web" "$OUT/index.html"; then
  cat >&2 <<'EOF'

Export failed. In order of likelihood:

  1. Export templates missing (most common on a fresh machine or a VM):
       bash install_godot.sh --templates

  2. Renderer is Forward+. Browsers only run Compatibility. In project.godot:
       [rendering]
       renderer/rendering_method="gl_compatibility"
     Or keep Forward+ for desktop and override just the web export by setting
     renderer/rendering_method.web="gl_compatibility".

  3. A shader uses a feature Compatibility does not support. The export log
     names the file.
EOF
  exit 1
fi
ok "exported"

if [[ "$SERVE" == "0" ]]; then
  echo "Files are in $OUT. They must be served with COOP/COEP headers -- see serve_web.py."
  exit 0
fi

say "Serving http://localhost:${PORT}"
exec python3 "$HERE/serve_web.py" --port "$PORT" --dir "$OUT"
