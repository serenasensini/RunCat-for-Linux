#!/usr/bin/env bash
# Remove the autostart entry and stop any running instance (the venv is kept).
set -euo pipefail

rm -f "$HOME/.config/autostart/runcat.desktop"
pkill -f "RunCat_for_Linux/main.py" || true
echo "Autostart removed."
