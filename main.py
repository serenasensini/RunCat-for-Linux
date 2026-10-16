import bisect
import fcntl
import json
import os
import re
import sys
import threading
from pathlib import Path

import psutil
import pystray
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'config.json'
RESOURCES_DIR = BASE_DIR / 'resources'
AUTOSTART_FILE = Path.home() / '.config' / 'autostart' / 'runcat.desktop'

# CPU usage (%) thresholds and the frame interval (s) for each band.
# Above the last threshold the animation runs at the fastest speed.
CPU_THRESHOLDS = [10.0, 20.0, 40.0, 60.0]
INTERVALS = [0.5, 0.3, 0.2, 0.1, 0.07]

DEFAULT_SETTINGS = {
    'dark_mode': True,
    'positive_correlation': False,
    'animation': 'cat',
}


# 读取配置 / Load settings, filling in defaults for missing keys
def load_config():
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(CONFIG_PATH, 'r') as file:
            settings.update(json.load(file).get('settings', {}))
    except (OSError, ValueError):
        pass
    return settings


def save_config(settings):
    with open(CONFIG_PATH, 'w') as file:
        json.dump({'settings': settings}, file, indent=4)


# 扫描 resources/ 下的动画 / Discover animations: resources/<name>/<theme>_<name>_<i>.(ico|png)
def discover_animations():
    names = []
    for folder in sorted(RESOURCES_DIR.iterdir()):
        if folder.is_dir() and list(folder.glob(f'dark_{folder.name}_*')):
            names.append(folder.name)
    return names


def load_images(animation, dark_mode):
    prefix = 'dark' if dark_mode else 'light'
    folder = RESOURCES_DIR / animation
    paths = [p for p in folder.glob(f'{prefix}_{animation}_*') if p.suffix in ('.ico', '.png')]
    paths.sort(key=lambda p: int(re.search(r'_(\d+)\.\w+$', p.name).group(1)))
    return [Image.open(p).convert('RGBA') for p in paths]


def interval_for_cpu(cpu_usage, positive_correlation):
    # INTERVALS is slowest-first, so it already maps higher CPU -> faster (positive);
    # otherwise reverse it, as the original did.
    intervals = INTERVALS if positive_correlation else INTERVALS[::-1]
    return intervals[bisect.bisect_right(CPU_THRESHOLDS, cpu_usage)]


class RunCat:
    def __init__(self):
        self.settings = load_config()
        self.animations = discover_animations()
        if self.settings['animation'] not in self.animations:
            self.settings['animation'] = self.animations[0]
        self.images = load_images(self.settings['animation'], self.settings['dark_mode'])
        self.interval = 1.0
        self.stop = threading.Event()
        self.icon = pystray.Icon('RunCat_for_Linux', self.images[0], 'RunCat', self.build_menu())

    # --- background workers -------------------------------------------------
    def watch_cpu(self):
        while not self.stop.is_set():
            cpu = psutil.cpu_percent(interval=1)
            self.interval = interval_for_cpu(cpu, self.settings['positive_correlation'])
            self.icon.title = f'CPU {cpu:.0f}%'

    def animate(self):
        index = 0
        while not self.stop.is_set():
            images = self.images
            self.icon.icon = images[index % len(images)]
            index += 1
            self.stop.wait(self.interval)

    # --- menu ---------------------------------------------------------------
    def build_menu(self):
        def animation_item(name):
            return pystray.MenuItem(
                name.replace('_', ' ').title(),
                lambda icon, item: self.set_animation(name),
                checked=lambda item: self.settings['animation'] == name,
                radio=True)

        return pystray.Menu(
            pystray.MenuItem('Animation', pystray.Menu(*[animation_item(n) for n in self.animations])),
            pystray.MenuItem('White icon (dark panel)', self.toggle_dark_mode,
                             checked=lambda item: self.settings['dark_mode']),
            pystray.MenuItem('Faster with higher CPU', self.toggle_correlation,
                             checked=lambda item: self.settings['positive_correlation']),
            pystray.MenuItem('Start at login', self.toggle_autostart,
                             checked=lambda item: AUTOSTART_FILE.exists()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit', self.quit))

    def reload_images(self):
        self.images = load_images(self.settings['animation'], self.settings['dark_mode'])
        save_config(self.settings)

    def set_animation(self, name):
        self.settings['animation'] = name
        self.reload_images()

    def toggle_dark_mode(self, icon, item):
        self.settings['dark_mode'] = not self.settings['dark_mode']
        self.reload_images()

    def toggle_correlation(self, icon, item):
        self.settings['positive_correlation'] = not self.settings['positive_correlation']
        save_config(self.settings)

    def toggle_autostart(self, icon, item):
        if AUTOSTART_FILE.exists():
            AUTOSTART_FILE.unlink()
        else:
            AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
            AUTOSTART_FILE.write_text(
                '[Desktop Entry]\nType=Application\nName=RunCat for Linux\n'
                f'Exec="{sys.executable}" "{BASE_DIR / "main.py"}"\n'
                'Icon=utilities-system-monitor\nX-GNOME-Autostart-enabled=true\n'
                'X-GNOME-Autostart-Delay=5\n')

    def quit(self, icon, item):
        self.stop.set()
        icon.stop()

    def run(self):
        threading.Thread(target=self.watch_cpu, daemon=True).start()
        threading.Thread(target=self.animate, daemon=True).start()
        self.icon.run()


# 单实例锁 / Allow only one running instance
def acquire_single_instance_lock():
    lock_dir = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
    lock_file = open(lock_dir / 'runcat_for_linux.lock', 'w')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit('RunCat is already running.')
    return lock_file


def main():
    lock = acquire_single_instance_lock()  # keep a reference so the lock is held
    RunCat().run()
    del lock


if __name__ == '__main__':
    main()
