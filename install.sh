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
  apt-get install -y \
    python3 python3-venv python3-pip python3-dev build-essential pkg-config \
    git rsync \
    mpv ffmpeg \
    alsa-utils \
    fonts-dejavu \
    # X11 minimal stack for pygame UI on composite CRT (no window manager required)
    xserver-xorg xinit x11-xserver-utils \
    unclutter \
    # Helpful framebuffer utilities for debugging CRT output
    fbset fbi \
    # GPIO backend preferred by gpiozero (used for IR / buttons later)
    python3-lgpio \
    # SDL2 headers (only needed if wheels build; safe to include)
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev
}

sync_project_files() {
  echo "[install] Syncing project to ${INSTALL_DIR}"
  mkdir -p "${INSTALL_DIR}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude .git --exclude __pycache__/ --exclude .DS_Store "${REPO_ROOT}/" "${INSTALL_DIR}/"
  else
    cp -r "${REPO_ROOT}"/* "${INSTALL_DIR}/"
  fi
}

ensure_runtime_user() {
  # We run services as a dedicated non-root user.
  if ! id -u crt >/dev/null 2>&1; then
    echo "[install] Creating user 'crt'"
    useradd -m -s /bin/bash crt
  fi

  # Ensure useful groups for video/audio/GPIO and journal viewing.
  for grp in sudo audio video input render spi i2c gpio adm systemd-journal; do
    getent group "$grp" >/dev/null 2>&1 && usermod -aG "$grp" crt || true
  done

  # Ensure install directory ownership.
  mkdir -p "${INSTALL_DIR}"
  chown -R crt:crt "${INSTALL_DIR}" || true
}

create_venv() {
  echo "[install] Ensuring Python venv (as user crt)"

  # Create venv if missing
  if [ ! -d "${INSTALL_DIR}/venv" ]; then
    sudo -u crt -H python3 -m venv "${INSTALL_DIR}/venv"
  fi

  # Upgrade pip and install requirements
  sudo -u crt -H "${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
  sudo -u crt -H "${INSTALL_DIR}/venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"
}

install_xinitrc() {
  echo "[install] Writing /home/crt/.xinitrc (minimal X11, no window manager)"
  cat >/home/crt/.xinitrc <<'EOF'
#!/bin/sh
set -e

cd /opt/crt-kitchen-tv

# Disable screen blanking / power saving
xset -dpms
xset s off
xset s noblank

# Hide mouse cursor if installed
command -v unclutter >/dev/null 2>&1 && unclutter -idle 0.5 -root &

# Start the UI
exec /opt/crt-kitchen-tv/venv/bin/python -m ui.main
EOF
  chown crt:crt /home/crt/.xinitrc
  chmod +x /home/crt/.xinitrc
}

install_config() {
  echo "[install] Ensuring default config at ${DEFAULT_CONFIG}"
  mkdir -p "${CONFIG_DIR}"
  if [ ! -f "${DEFAULT_CONFIG}" ]; then
    cp "${INSTALL_DIR}/config/default_config.yaml" "${DEFAULT_CONFIG}"
  fi
}

enable_interfaces() {
  echo "[install] Enabling composite video config + SPI (DietPi/RPi firmware config)"

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

  # Enable both services
  systemctl enable crt-web.service
  systemctl enable crt-ui.service

  # Start/restart services immediately; UI launches via startx on tty1.
  echo "[install] Restarting crt-web.service now (web UI should be reachable on :8080)"
  systemctl restart crt-web.service || true
  systemctl status crt-web.service --no-pager || true

  echo "[install] Restarting crt-ui.service now (CRT UI on tty1)"
  systemctl restart crt-ui.service || true
  systemctl status crt-ui.service --no-pager || true
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
  ensure_runtime_user
  sync_project_files
  create_venv
  install_config
  enable_interfaces
  install_xinitrc
  install_services
  maybe_install_respeaker
  echo "[install] Done. Reboot recommended to apply boot config and ensure tty1 UI starts cleanly."
}

main "$@"
