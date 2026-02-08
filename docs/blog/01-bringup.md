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

## Composite video configuration

The CRT is connected using the Raspberry Pi composite output. Video mode is configured via the Raspberry Pi firmware options.

Typical configuration (PAL example):
- `sdtv_mode=2` (PAL)
- Framebuffer resolution: `720x576`

On DietPi, this is configured through `dietpi-config` → Display Options.

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
3. Run `install.sh` as root
4. Reboot

The installer:
- Installs all required packages
- Creates and configures the runtime user
- Sets up a Python virtual environment
- Installs systemd services
- Configures X11 auto-start on tty1

## First validation steps

- System boots directly into the CRT UI
- Composite video is stable and correctly scaled
- Web UI reachable over the network
- mpv playback works from the command line
- GPIO access available for future IR input

## Current state

The system boots reliably into a fullscreen CRT-optimized UI running under a minimal X11 environment.

No desktop environment or window manager is used. The Raspberry Pi behaves like a dedicated appliance.

## Next steps

- CRT video tuning
- UI iteration
- IR remote
- LED status indicators
- Curated content sources
