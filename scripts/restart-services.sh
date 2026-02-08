#!/bin/sh
set -e

echo "== CRT Kitchen TV: restarting services =="

# Ensure systemd sees any updated unit files
echo "-- Reloading systemd units"
sudo systemctl daemon-reload

# Restart UI (X11 + pygame)
echo "-- Restarting crt-ui"
sudo systemctl restart crt-ui

# Restart web config UI
echo "-- Restarting crt-web"
sudo systemctl restart crt-web

echo "== Done =="
echo "UI and web services restarted."