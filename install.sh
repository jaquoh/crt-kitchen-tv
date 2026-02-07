#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="crt-kitchen-tv"
INSTALL_DIR="/opt/${PROJECT_NAME}"
CONFIG_DIR="/etc/${PROJECT_NAME}"
DEFAULT_CONFIG="${CONFIG_DIR}/config.yaml"
SERVICE_DIR="/etc/systemd/system"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

require_root() {
  if [ "${EUID}" -ne 0 ]; then
    echo "Please run install.sh as root (e.g., sudo ./install.sh)" >&2
    exit 1
  fi
}

apt_install() {
  echo "[install] Installing apt packages"
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip mpv ffmpeg git fonts-dejavu \
    python3-dev build-essential alsa-utils rsync
}

sync_project_files() {
  echo "[install] Syncing project to ${INSTALL_DIR}"
  mkdir -p "${INSTALL_DIR}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude .git --exclude __pycache__/ "${REPO_ROOT}/" "${INSTALL_DIR}/"
  else
    cp -r "${REPO_ROOT}"/* "${INSTALL_DIR}/"
  fi
}

create_venv() {
  echo "[install] Ensuring Python venv"
  if [ ! -d "${INSTALL_DIR}/venv" ]; then
    python3 -m venv "${INSTALL_DIR}/venv"
  fi
  "${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
  "${INSTALL_DIR}/venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"
}

install_config() {
  echo "[install] Ensuring default config at ${DEFAULT_CONFIG}"
  mkdir -p "${CONFIG_DIR}"
  if [ ! -f "${DEFAULT_CONFIG}" ]; then
    cp "${INSTALL_DIR}/config/default_config.yaml" "${DEFAULT_CONFIG}"
  fi
}

enable_interfaces() {
  echo "[install] Enabling composite video config + SPI (and leaving I2C optional)"

  CONFIG_FILE="/boot/config.txt"
  [ -f /boot/firmware/config.txt ] && CONFIG_FILE="/boot/firmware/config.txt"

  if [ ! -f "${CONFIG_FILE}" ]; then
    echo "[install] ERROR: Boot config file not found at ${CONFIG_FILE}" >&2
    exit 1
  fi

  BLOCK_START="# --- ${PROJECT_NAME} COMPOSITE CONFIG START ---"
  BLOCK_END="# --- ${PROJECT_NAME} COMPOSITE CONFIG END ---"

  if ! grep -qF "${BLOCK_START}" "${CONFIG_FILE}"; then
    # Only create a backup when we actually modify the file
    BACKUP="${CONFIG_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    cp "${CONFIG_FILE}" "${BACKUP}"
    echo "[install] Backed up ${CONFIG_FILE} to ${BACKUP}"

    cat >> "${CONFIG_FILE}" <<'CFG'
# --- crt-kitchen-tv COMPOSITE CONFIG START ---
# Enable composite video output and SPI for LEDs
enable_tvout=1
sdtv_mode=2       # 0=NTSC,1=NTSC-J,2=PAL
sdtv_aspect=1     # 4:3

# Prefer a stable framebuffer size for CRT UIs
framebuffer_width=640
framebuffer_height=480
framebuffer_depth=16
framebuffer_ignore_alpha=1

# SPI for APA102 LEDs
dtparam=spi=on

# I2C kept available for future use (enable later if needed)
# dtparam=i2c_arm=on

# I2S typically enabled by ReSpeaker driver installer
# --- crt-kitchen-tv COMPOSITE CONFIG END ---
CFG

    echo "[install] Appended composite/SPI block to ${CONFIG_FILE}"
  else
    echo "[install] Composite block already present in ${CONFIG_FILE} (no changes made, no backup created)"
  fi
}

install_services() {
  echo "[install] Installing systemd units"

  cp "${INSTALL_DIR}/services/crt-web.service" "${SERVICE_DIR}/"
  cp "${INSTALL_DIR}/services/crt-ui.service" "${SERVICE_DIR}/"

  systemctl daemon-reload
  systemctl enable crt-web.service
  systemctl enable crt-ui.service

  # Start/restart the web service immediately (UI is best tested after reboot)
  echo "[install] Restarting crt-web.service now (no reboot required for web UI)"
  systemctl restart crt-web.service || true
  systemctl status crt-web.service --no-pager || true
}

maybe_install_respeaker() {
  if [ "${INSTALL_RESPEAKER:-0}" = "1" ]; then
    echo "[install] Installing ReSpeaker driver"
    bash "${INSTALL_DIR}/scripts/install_respeaker_driver.sh"
  else
    echo "[install] Skipping ReSpeaker driver install (set INSTALL_RESPEAKER=1 to enable)"
  fi
}

main() {
  require_root
  apt_install
  sync_project_files
  create_venv
  install_config
  enable_interfaces
  install_services
  maybe_install_respeaker
  echo "[install] Done. Reboot recommended to apply boot config and services."
}

main "$@"
