# 🐈RunCat_for_Linux
🇨🇳[ 简体中文](README.zh.md)  

A cute running cat animation on your Linux taskbar.  
The speed depends on your CPU usage.

# Demo

![Demo](/resources/demo.gif)  

**You only have to run the main.py**

# Installation

```bash
./install.sh      # creates ./venv, installs deps, starts RunCat at every login
```

On GNOME (Wayland) the tray icon needs the AppIndicator extension and PyGObject:
`sudo apt install gnome-shell-extension-appindicator python3-gi gir1.2-ayatanaappindicator3-0.1`.
The venv is created with `--system-site-packages` so pystray can use them; without
them pystray falls back to the X11 backend, whose menu does not work on Wayland. Remove autostart with `./uninstall.sh`.

# Usage

```bash
nohup venv/bin/python main.py >/dev/null 2>&1 &   # run in background
```

Right-click the tray icon to choose the animation, switch icon colour, invert
the speed/CPU relation, toggle "Start at login" or quit. Choices are saved in
`config.json`. Only one instance runs at a time.

# Configuration

```json
{
    "settings": {
        "dark_mode": true,             // true = white icons (dark panel)
        "positive_correlation": false, // true = higher CPU -> faster animation
        "animation": "cat"             // any folder in resources/
    }
}
```

# Adding animations

Put frames in `resources/<name>/` named `dark_<name>_0.png`, `light_<name>_0.png`,
`dark_<name>_1.png`, ... (.ico or .png). They show up in the menu automatically.
`tools/import_sprites.py` shows how the bundled panther, stickman and dog were
generated. Sprite credits are in [CREDITS.md](CREDITS.md).

# Acknowledgements

This project was inspired by the work done in [Runcat_for_Windows](https://github.com/Kyome22/RunCat_for_windows). Special thanks to the original authors for their innovative ideas and contributions to the open-source community.😺😺😺
