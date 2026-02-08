# crt-kitchen-tv

Raspberry Pi OS Lite project that boots straight into a fullscreen, big-button UI on a small CRT (composite video) and uses the ReSpeaker 2-Mics Pi HAT for audio. A lightweight Flask web UI lets you update config on the LAN.

## Features
- Framebuffer pygame UI with News, Movies, and Library menus
- mpv playback for streams/files, returns to menu when done
- Optional ReSpeaker button (GPIO17) for select/back; optional APA102 status LEDs over SPI
- Web UI at `http://<pi>:8080` to edit config
- Systemd-managed services and single `install.sh`

## Hardware
- ReSpeaker 2-Mics Pi HAT: button on GPIO17, 3x APA102 LEDs on SPI, WM8960 audio codec (driver via seeed-voicecard)
- Composite CRT: enables `enable_tvout=1` and PAL by default (edit block in `/boot/config.txt` if needed)

## Install
```bash
sudo ./install.sh          # INSTALL_RESPEAKER=1 ./install.sh to also install driver
sudo reboot                # apply boot config + services
```

What install.sh does:
- apt installs: python3, python3-venv, python3-pip, mpv, ffmpeg, git, fonts-dejavu, python3-dev, build-essential, alsa-utils
- Syncs repo to `/opt/crt-kitchen-tv`, builds venv, installs `requirements.txt`
- Places default config at `/etc/crt-kitchen-tv/config.yaml` if missing
- Enables SPI (and leaves I2C/I2S hooks) plus composite video block in `/boot/config.txt` or `/boot/firmware/config.txt` (backs up first)
- Installs and enables systemd units `crt-web.service` and `crt-ui.service`
- Optional ReSpeaker driver install via `scripts/install_respeaker_driver.sh`

## Services
- `crt-web.service`: Flask via waitress on `0.0.0.0:8080`
- `crt-ui.service`: pygame UI on tty1/framebuffer

Manage services:
```bash
sudo systemctl status crt-web.service
sudo systemctl status crt-ui.service
sudo journalctl -u crt-ui.service -f
```

## Config
Default: `/etc/crt-kitchen-tv/config.yaml`
```yaml
news_streams:
  - https://example.com/stream.m3u8
movies_dir: /home/pi/Videos
media_root: /var/lib/crt-kitchen-tv/media
collections:
  - Inbox
  - News
  - Movies
library_sort: newest   # or alpha
mpv_backend: drm       # drm, x11, or auto
audio_output: respeaker   # or hdmi / analog
font_size: 48
overscan:
  top: 0
  bottom: 0
  left: 0
  right: 0
leds_enabled: true
```
Edit via web UI or manually then restart services.

## Running pieces manually
```bash
# Web API/UI
CRT_CONFIG=./config/default_config.yaml venv/bin/waitress-serve --listen=0.0.0.0:8080 --call server.app:create_app

# Frontend UI (framebuffer or X11)
CRT_CONFIG=./config/default_config.yaml venv/bin/python ui/main.py

# Play a test stream
CRT_CONFIG=./config/default_config.yaml venv/bin/python - <<'PY'
from player import play
play.play_media('https://example.com/stream.m3u8', {})
PY
```

## Debugging tips
- Check audio devices: `aplay -l`, `amixer scontrols`
- If LEDs don't light, confirm SPI: `ls /dev/spidev*`
- To change TV standard, edit the composite block in `/boot/config.txt` and reboot
- If UI fails to start, ensure tty1 free: `sudo systemctl stop getty@tty1`
- Web diagnostics page: `http://<pi>:8080/` (bottom section, includes UI debug and service logs)
- JSON diagnostics endpoint: `http://<pi>:8080/api/logs?lines=200`

## Notes
- Button long-press (~1s) = back/home, short press = select
- Movies list shows common video extensions in `movies_dir`
- Library shows configured collections under `media_root` and refreshes every 10 seconds while viewing a collection
- LEDs are optional; disable in config if absent
