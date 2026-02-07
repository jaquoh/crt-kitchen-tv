#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=/var/log/crt-kitchen-tv
LOG_FILE="$LOG_DIR/respeaker-driver.log"
REPO_URL="https://github.com/respeaker/seeed-voicecard.git"
REPO_DIR="/tmp/seeed-voicecard"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[respeaker] Starting driver install at $(date)"

if lsmod | grep -q "seeed_voicecard"; then
  echo "[respeaker] Driver already loaded; skipping install."
  exit 0
fi

if [ -d "$REPO_DIR" ]; then
  echo "[respeaker] Reusing existing clone at $REPO_DIR"
  (cd "$REPO_DIR" && git pull --ff-only || true)
else
  echo "[respeaker] Cloning driver repo"
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
echo "[respeaker] Running install script (may prompt for kernel headers download)"
# The install script handles enabling I2S overlays and blacklisting HDMI audio.
bash install.sh || {
  echo "[respeaker] Driver install script failed; leaving system untouched." >&2
  exit 1
}

# Ensure modules are loaded at boot
if ! grep -q "seeed-voicecard" /etc/modules; then
  echo "seeed-voicecard" | sudo tee -a /etc/modules >/dev/null
fi

echo "[respeaker] Install complete"
