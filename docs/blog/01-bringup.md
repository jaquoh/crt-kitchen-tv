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
1. Frontend UI (framebuffer-based, CRT-optimized)
2. Player (mpv wrapper for local files and streams)
3. Web UI (Flask-based configuration interface)

## Preparing the Raspberry Pi OS

- Raspberry Pi OS Lite
- SSH enabled
- Custom user created: crt

## Securing SSH access

- SSH key-based authentication
- Password authentication disabled
- Root login disabled

## Installing base packages

sudo apt update && sudo apt install -y \
  git ca-certificates curl wget openssh-client \
  python3 python3-venv python3-pip build-essential \
  alsa-utils mpv ffmpeg fonts-dejavu

## Project repository and installation flow

The entire system is installed via a single Git repository and managed using systemd.

## First install on the Pi

1. Clone the repository
2. Make scripts executable
3. Run install.sh
4. Reboot

## First validation steps

- SSH access works
- Web UI reachable
- Audio devices detected
- Composite video stable

## Current state

Base system installed and stable.

## Next steps

- CRT video tuning
- UI iteration
- IR remote
- LED status indicators
- Curated content sources
