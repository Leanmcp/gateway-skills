#!/usr/bin/env bash
# Runs ON the GCP VM as its startup script. Do not run this on your laptop.
#
# Installs the NVIDIA datacenter driver, Docker with the NVIDIA runtime, a
# virtual X display bound to the GPU, and Selkies (open-source WebRTC desktop
# streaming, started by Google engineers -- effectively self-hosted Stadia).
#
# The virtual display is the part that surprises people. A datacenter GPU has
# no display output, so there is no X server for Godot to open, and Godot exits
# instantly with "cannot open display". Streaming stacks solve this by running
# their own X server against the GPU, which is what the container below does.
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

if [ -f /var/lib/godot-stream-setup-done ]; then
  echo "already provisioned"; exit 0
fi

GODOT_VERSION="$(curl -fsS -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/attributes/godot-version' \
  2>/dev/null || echo 4.7.1)"

# ------------------------------------------------------------------- base
apt-get update
apt-get install -y --no-install-recommends \
  curl ca-certificates gnupg lsb-release \
  xserver-xorg-core xserver-xorg-video-dummy xinit x11-xserver-utils \
  pulseaudio unzip jq

# ----------------------------------------------------------------- driver
# The -server driver, not the desktop one: these GPUs have no display out.
curl -fsSL -o /tmp/cuda-keyring.deb \
  https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i /tmp/cuda-keyring.deb
apt-get update
apt-get install -y nvidia-driver-570-server

# ----------------------------------------------------------------- docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  > /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
                   docker-compose-plugin nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# ------------------------------------------------------------------ godot
cd /opt
curl -fsSL -o godot.zip \
  "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
unzip -o godot.zip
mv "Godot_v${GODOT_VERSION}-stable_linux.x86_64" /usr/local/bin/godot
chmod +x /usr/local/bin/godot
rm godot.zip

mkdir -p /opt/game
chown -R ubuntu:ubuntu /opt/game

# -------------------------------------------------------------- streaming
cat >/etc/systemd/system/godot-stream.service <<'UNIT'
[Unit]
Description=Godot game streamed over WebRTC
After=docker.service
Requires=docker.service

[Service]
Restart=always
RestartSec=5
ExecStartPre=-/usr/bin/docker rm -f godot-stream
ExecStart=/usr/bin/docker run --rm --name godot-stream \
  --gpus all \
  --device /dev/dri \
  -p 8080:8080 \
  -e SELKIES_ENABLE_BASIC_AUTH=true \
  -e SELKIES_BASIC_AUTH_USER=player \
  -e SELKIES_BASIC_AUTH_PASSWORD=changeme \
  -e SELKIES_ENCODER=nvh264enc \
  -e SELKIES_FRAMERATE=60 \
  -e SELKIES_VIDEO_BITRATE=12000 \
  -e SELKIES_H264_FULLCOLOR=true \
  -e DISPLAY_SIZEW=1280 -e DISPLAY_SIZEH=720 \
  -v /opt/game:/opt/game:ro \
  -v /usr/local/bin/godot:/usr/local/bin/godot:ro \
  --shm-size=2g \
  ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:latest-ubuntu24.04

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable godot-stream

touch /var/lib/godot-stream-setup-done
echo "=========================================="
echo " SETUP COMPLETE"
echo " Rebooting to load the NVIDIA driver."
echo "=========================================="
reboot
