# CRT Kitchen TV – From Idea to First Boot

## Why this project exists

I wanted to reuse a small 5" CRT TV as a modern, network-connected kitchen display, without turning it into a full smart TV or browser-based mess.

The goal is a purpose-built appliance:
- Big, readable UI designed specifically for a CRT
- No free browsing, only curated content
- Controlled by a remote (and later maybe voice)
- Configurable through a simple web interface
- Reliable, fast to boot, and understandable

This document describes the initial bring-up phase: hardware decisions, OS preparation, security setup, and first installation.

## Hardware used (initial version)

- Small CRT TV with composite video input and mono audio input
- Raspberry Pi Zero W (v1.3)
- ReSpeaker 2-Mics Pi HAT
- Micro SD card (8–32 GB)
- Power supply suitable for Pi + HAT

## Software architecture (high level)

The system is split into three main parts:
1. Frontend UI (pygame-based, CRT-optimized, running under minimal X11)
2. Player (mpv wrapper for local files and streams)
3. Web UI (Flask-based configuration interface)

## Operating system choice

After initial experiments with Raspberry Pi OS Lite, the final choice for this project is **DietPi**.

Reasons for choosing DietPi:
- Extremely small and fast base system
- Excellent support for Raspberry Pi Zero (ARMv6)
- Clean framebuffer and composite video support
- No desktop environment by default
- Easy to reason about and reproduce

DietPi provides `/dev/fb0` for composite output and allows adding only the minimal X11 stack required for SDL/pygame.

Modern Raspberry Pi OS versions based on the Bookworm kernel no longer support SDL framebuffer backends reliably on ARMv6 hardware like the Pi Zero. This limitation necessitated adding a minimal X11 layer to ensure stable and compatible rendering for the CRT UI.

## Composite video configuration

The CRT is connected using the Raspberry Pi composite output. Video mode is configured via the Raspberry Pi firmware options.

Typical configuration (PAL example):
- `sdtv_mode=2` (PAL)
- Framebuffer resolution: `720x576`

On DietPi, this is configured through `dietpi-config` → Display Options.

## Rendering stack: why minimal X11

SDL's fbcon/fbdev backends are broken or unavailable on modern Raspberry Pi kernels, especially on ARMv6 devices. This prevents direct framebuffer rendering from working reliably.

Running pygame with SDL 2 under X11 provides a stable and consistent rendering environment. By using Xorg with `startx` but without any desktop environment or window manager, the system remains lightweight and focused.

This minimal X11 approach keeps performance acceptable on the Pi Zero while ensuring compatibility with the CRT display and the custom UI.

## Boot & runtime flow (simplified)

```
Power on
  │
  ├─ Raspberry Pi firmware
  │
  ├─ Linux kernel (ARMv6)
  │
  ├─ systemd
  │   ├─ networking
  │   ├─ ssh
  │   └─ crt-ui.service
  │
  ├─ startx (tty1, no window manager)
  │
  ├─ Xorg (minimal)
  │
  └─ pygame UI (fullscreen, CRT-optimized)
```

This illustrates the intentionally short and deterministic boot path.

## System preparation

- DietPi installed on the SD card
- SSH enabled
- Dedicated runtime user created: `crt`
- SSH key-based authentication enabled
- Password authentication disabled
- Root login disabled

The system is administered exclusively through the `crt` user using `sudo`.

## First install on the Pi

1. Log in as user `crt`
2. Clone the repository into `/opt/crt-kitchen-tv`
3. Run `install.sh` as root (using `sudo`)
4. Reboot

The installer:
- Installs all required packages
- Installs a minimal X11 stack (`xserver-xorg`, `xinit`, fonts)
- Installs no window manager
- Creates and configures the runtime user
- Sets up a Python virtual environment
- Installs systemd services
- Configures X11 auto-start on tty1

## First validation steps

- System boots directly into the CRT UI
- Composite video is stable and correctly scaled
- Web UI reachable over the network via `http://<pi-ip>:8080`
- mpv playback works from the command line
- GPIO access available for future IR input
- Verified `crt-ui.service` runs `startx` on tty1

## Lessons learned

- Framebuffer-only rendering is no longer viable on modern Pi kernels
- Minimal X11 is the most reliable option for CRT + Pi Zero
- DietPi makes it easy to keep the system small and deterministic
- Treat the Pi as a deployment target, not a dev machine

## Why not Electron / browser-based UI?

A browser or Electron-based solution was intentionally avoided.

What an Electron setup would look like:
- Full Chromium runtime
- Node.js + Electron
- GPU acceleration requirements
- Significantly higher RAM and storage usage
- Longer boot times
- More background processes

On a Raspberry Pi Zero, this would result in:
- Poor performance
- Long startup times
- High memory pressure
- Unpredictable rendering latency

Electron excels at cross-platform desktop apps, but this project is an embedded appliance with fixed hardware and a single purpose.

By using pygame with a minimal X11 stack:
- The rendering path is simple and predictable
- Startup time is short
- Resource usage stays within Pi Zero limits
- The UI behaves like firmware, not an application

This trade-off favors reliability and clarity over portability.

## Current state

The system boots reliably into a fullscreen CRT-optimized UI running under a minimal X11 environment.

No desktop environment or window manager is used. The Raspberry Pi behaves like a dedicated appliance.

## Next steps

- CRT video tuning
- UI iteration
- IR remote
- LED status indicators
- Curated content sources
