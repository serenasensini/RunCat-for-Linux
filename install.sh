#!/usr/bin/env bash
# Create a venv, install the dependencies and start RunCat at every login.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART="$HOME/.config/autostart/runcat.desktop"

# system site-packages: pystray needs the distro PyGObject (gi) for the AppIndicator backend,
# which is the only one that works on Wayland/GNOME.
python3 -m venv --system-site-packages "$DIR/venv"
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
echo "Note: on GNOME you need the AppIndicator extension and PyGObject:"
echo "  sudo apt install gnome-shell-extension-appindicator python3-gi gir1.2-ayatanaappindicator3-0.1"
