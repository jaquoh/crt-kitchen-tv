# Installation (TL;DR)

This guide describes how to install **crt-kitchen-tv** on a Raspberry Pi (tested on Pi Zero) using **DietPi** and a composite CRT display.

---

## Requirements

- Raspberry Pi with composite video output
- CRT TV (PAL or NTSC)
- SD card with **DietPi** installed
- Network access (Ethernet or WiFi)
- Another machine for development (Linux/macOS/Windows)

---

## 1. Prepare DietPi

1. Flash DietPi to the SD card
2. Boot the Pi
3. Complete the initial DietPi setup
4. Enable SSH
5. Configure composite video via `dietpi-config`
   - Display Options → Composite
   - Example: `sdtv_mode=2` (PAL)

---

## 2. Create runtime user

Log in via SSH as root and create the runtime user:

```
adduser crt
usermod -aG sudo,audio,video,input,render,spi,i2c,gpio,adm,systemd-journal crt
```

Log out and back in as user `crt`.

---

## 3. Clone the repository

```
cd /opt
git clone https://github.com/jaquoh/crt-kitchen-tv.git
sudo chown -R crt:crt /opt/crt-kitchen-tv
cd /opt/crt-kitchen-tv
```

---

## 4. Run the installer

Run the installer as root:

```
sudo ./install.sh
```

The installer will:
- Install all required system packages
- Create and configure the runtime environment
- Set up Python virtual environment
- Install systemd services
- Configure X11 auto-start on tty1

---

## 5. Reboot

```
sudo reboot
```

After reboot, the system should boot directly into the CRT UI.

---

## 6. Verify

- CRT shows the fullscreen UI
- Web UI reachable on port `8080`
- `journalctl -u crt-ui` shows no errors

---

## Updating

To update the Pi after making changes on the development machine:

```
cd /opt/crt-kitchen-tv
git fetch origin
git reset --hard origin/main
sudo systemctl restart crt-ui
```

---

This system is intended to behave like a dedicated appliance. No desktop environment or window manager is used.
