#!/usr/bin/env bash
# Create a GPU VM on GCP that renders the game and streams it to a browser.
#
#   bash cloud/provision_gcp.sh
#   GPU=t4 SPOT=0 ZONE=asia-south1-c bash cloud/provision_gcp.sh
#
# Read cloud costs before running this. Billing starts the moment the VM boots
# and does not stop because you closed the tab:
#   bash cloud/stop.sh
#
# Before anything else: a new GCP project has a GPU quota of ZERO. Request an
# increase first (IAM & Admin > Quotas > NVIDIA_L4_GPUS in your region);
# approval takes hours to days and every other step is blocked on it. The
# preflight below checks so you find out in seconds rather than after a
# ten-minute setup.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib.sh"

NAME="${NAME:-godot-stream}"
ZONE="${ZONE:-us-central1-a}"
GPU="${GPU:-l4}"
SPOT="${SPOT:-1}"
DISK_GB="${DISK_GB:-100}"

command -v gcloud >/dev/null || die "gcloud not found. Install:
   brew install --cask google-cloud-sdk   (or https://cloud.google.com/sdk)"

PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
[[ -n "$PROJECT" && "$PROJECT" != "(unset)" ]] || die "no GCP project set:
   gcloud config set project YOUR_PROJECT"

# ---------------------------------------------------------------- machine
# L4 ships only on G2 machine types, where the GPU is part of the machine.
# T4 attaches to N1 as a separate accelerator. They are not interchangeable,
# and mixing them up produces an unhelpful "invalid machine type" error.
case "$GPU" in
  l4) MACHINE="g2-standard-8"; ACCEL=""; QUOTA="NVIDIA_L4_GPUS" ;;
  t4) MACHINE="n1-standard-8"; ACCEL="--accelerator=type=nvidia-tesla-t4,count=1"; QUOTA="NVIDIA_T4_GPUS" ;;
  *)  die "GPU must be 'l4' or 't4' (got '$GPU')" ;;
esac

REGION="${ZONE%-*}"
say "project $PROJECT / $REGION / $MACHINE / GPU $GPU"

# -------------------------------------------------------------- preflight
LIMIT="$(gcloud compute regions describe "$REGION" \
          --format="value(quotas.filter(\"metric=$QUOTA\").limit)" 2>/dev/null || true)"
if [[ -n "$LIMIT" && "${LIMIT%%.*}" == "0" ]]; then
  die "GPU quota for $QUOTA in $REGION is 0.
   Request an increase: https://console.cloud.google.com/iam-admin/quotas
   Filter on '$QUOTA', select $REGION, Edit Quotas, ask for 1.
   Nothing else here can work until that is approved."
fi

PROVISION=()
if [[ "$SPOT" == "1" ]]; then
  # 60-70% cheaper, but GCP can reclaim it with 30 seconds' notice. Correct for
  # a dev box you are watching; wrong for players you promised uptime to.
  PROVISION=(--provisioning-model=SPOT --instance-termination-action=STOP)
  warn "SPOT instance: cheap, reclaimable at any time. SPOT=0 to disable."
fi

# --------------------------------------------------------------- firewall
if ! gcloud compute firewall-rules describe "${NAME}-web" >/dev/null 2>&1; then
  say "creating firewall rule (tcp:8080)"
  gcloud compute firewall-rules create "${NAME}-web" \
    --allow=tcp:8080 --target-tags="${NAME}" \
    --description="WebRTC signalling + HTTP for ${NAME}"
fi

# --------------------------------------------------------------- instance
say "creating instance $NAME"
gcloud compute instances create "$NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE" \
  ${ACCEL:+$ACCEL} \
  "${PROVISION[@]}" \
  --maintenance-policy=TERMINATE \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size="${DISK_GB}GB" \
  --boot-disk-type=pd-balanced \
  --tags="$NAME" \
  --metadata=godot-version="${GODOT_VERSION}" \
  --metadata-from-file=startup-script="$HERE/setup_host.sh"

IP="$(gcloud compute instances describe "$NAME" --zone="$ZONE" \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"

cat <<EOF

${GREEN}${BOLD}VM is up.${OFF}  external IP: ${IP}

Drivers are still installing -- 5-10 minutes. Watch:

  gcloud compute ssh ${NAME} --zone=${ZONE} \\
    --command='sudo journalctl -u google-startup-scripts -f'

When it prints SETUP COMPLETE:

  bash cloud/deploy_game.sh
  open http://${IP}:8080          # user: player / changeme

${YELLOW}Billing runs while the VM exists.${OFF}  Stop it:  bash cloud/stop.sh
EOF
