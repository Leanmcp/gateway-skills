#!/usr/bin/env bash
# Stop the VM so it stops billing compute.
#
#   bash cloud/stop.sh              # stop (disk still bills, ~$10/mo per 100GB)
#   DELETE=1 bash cloud/stop.sh     # delete instance, disk and firewall rule
#   bash cloud/stop.sh --status     # is anything running right now?
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib.sh"

NAME="${NAME:-godot-stream}"
ZONE="${ZONE:-us-central1-a}"

if [[ "${1:-}" == "--status" ]]; then
  gcloud compute instances list --filter="name=$NAME" \
    --format='table(name,zone.basename(),status,machineType.basename())'
  exit 0
fi

if [[ "${DELETE:-0}" == "1" ]]; then
  say "deleting $NAME (destroys the boot disk too)"
  gcloud compute instances delete "$NAME" --zone="$ZONE" --quiet
  gcloud compute firewall-rules delete "${NAME}-web" --quiet 2>/dev/null || true
  ok "gone. Nothing is billing."
else
  say "stopping $NAME"
  gcloud compute instances stop "$NAME" --zone="$ZONE" --quiet
  ok "compute billing stopped"
  echo "  boot disk still bills (~\$10/mo per 100GB) -- DELETE=1 to remove it"
  echo "  start again: gcloud compute instances start $NAME --zone=$ZONE"
fi
