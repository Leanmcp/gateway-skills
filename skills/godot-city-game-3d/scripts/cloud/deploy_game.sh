#!/usr/bin/env bash
# Export a Linux build and push it to the streaming VM.
#
#   bash cloud/deploy_game.sh
#   NAME=my-vm ZONE=europe-west4-b bash cloud/deploy_game.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib.sh"
require_godot
require_project

NAME="${NAME:-godot-stream}"
ZONE="${ZONE:-us-central1-a}"
OUT="${OUT:-$(dirname "$GODOT_PROJECT")/build/linux}"

python3 "$HERE/../ensure_export_presets.py" --project "$GODOT_PROJECT" --preset Linux

say "exporting Linux build"
mkdir -p "$OUT"
if ! "$GODOT_BIN" --headless --path "$GODOT_PROJECT" \
      --export-release "Linux" "$OUT/game.x86_64"; then
  cat >&2 <<'EOF'

Export failed. Almost always one of:

  1. Export templates not installed:  bash install_godot.sh --templates
  2. The preset exists but targets the wrong architecture -- the VM is x86_64
     even if your laptop is arm64.
EOF
  exit 1
fi
chmod +x "$OUT/game.x86_64"
ok "$(du -h "$OUT/game.x86_64" | cut -f1) built"

say "uploading to $NAME"
gcloud compute scp --recurse --zone="$ZONE" "$OUT/" "$NAME:/opt/game/"

say "restarting stream"
gcloud compute ssh "$NAME" --zone="$ZONE" --command \
  'sudo systemctl restart godot-stream && sleep 3 && sudo systemctl is-active godot-stream'

IP="$(gcloud compute instances describe "$NAME" --zone="$ZONE" \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo
echo "${GREEN}Play at:${OFF}  http://${IP}:8080     (player / changeme)"
echo "${YELLOW}Stop billing when done:${OFF}  bash cloud/stop.sh"
