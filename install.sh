#!/usr/bin/env bash
# Create a venv, install the dependencies and start RunCat at every login.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART="$HOME/.config/autostart/runcat.desktop"

python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install --quiet -r "$DIR/requirements.txt"

mkdir -p "$(dirname "$AUTOSTART")"
cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=RunCat for Linux
Exec="$DIR/venv/bin/python" "$DIR/main.py"
Icon=utilities-system-monitor
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=5
EOF

echo "Installed. RunCat will start at the next login."
echo "Start it now (in background) with:  nohup '$DIR/venv/bin/python' '$DIR/main.py' >/dev/null 2>&1 &"
echo "Note: on GNOME the tray icon needs the AppIndicator extension (gnome-shell-extension-appindicator)."
