"""Convert the CC0 OpenGameArt assets into tray-sized (128x128) PNG frames.

Usage: python3 tools/import_sprites.py <download_dir>

<download_dir> must contain cat/kitka.gif, stick/Layer N.png (12 frames) and
dog/German Shepherd/x3/Shepherd_run_N.png (5 frames). See CREDITS.md.
Output: resources/<name>/{dark,light}_<name>_<i>.png
  "dark" = white icon (for dark panels), "light" = black icon, as for the cat.
"""
import glob
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageSequence

SIZE = 128  # the panel downscales to ~22px, so draw big and bold
ROOT = Path(__file__).resolve().parent.parent / 'resources'


def load_panther(src):
    gif = Image.open(Path(src) / 'cat' / 'kitka.gif')
    return [f.convert('RGBA') for f in ImageSequence.Iterator(gif)]


def load_stickman(src):
    paths = sorted(glob.glob(str(Path(src) / 'stick' / '[Ll]ayer *.png')),
                   key=lambda p: int(''.join(c for c in Path(p).stem if c.isdigit())))
    return [Image.open(p).convert('RGBA') for p in paths]


def load_dog(src):
    d = Path(src) / 'dog' / 'German Shepherd' / 'x3'
    return [Image.open(d / f'Shepherd_run_{i}.png').convert('RGBA') for i in range(1, 6)]


# name -> (loader, silhouette?, stroke thickening in px at SIZE)
# silhouettes are recoloured per theme, others kept as is; thin strokes would vanish at tray size
ANIMATIONS = {
    'panther': (load_panther, True, 5),
    'stickman': (load_stickman, True, 5),
    'dog': (load_dog, False, 0),
}


def common_bbox(frames):
    boxes = [f.getchannel('A').point(lambda a: 255 if a > 40 else 0).getbbox() for f in frames]
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def to_square(frames):
    box = common_bbox(frames)
    frames = [f.crop(box) for f in frames]
    w, h = frames[0].size
    scale = SIZE / max(w, h)
    new = (max(1, round(w * scale)), max(1, round(h * scale)))
    out = []
    for f in frames:
        f = f.resize(new, Image.BICUBIC)
        canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
        canvas.paste(f, ((SIZE - new[0]) // 2, (SIZE - new[1]) // 2), f)
        out.append(canvas)
    return out


def thicken(frame, px):
    if not px:
        return frame
    alpha = frame.getchannel('A').filter(ImageFilter.MaxFilter(px | 1))
    frame = frame.copy()
    frame.putalpha(alpha)
    return frame


def recolor(frame, rgb):
    solid = Image.new('RGBA', frame.size, rgb + (255,))
    solid.putalpha(frame.getchannel('A'))
    return solid


def main(src):
    for name, (loader, silhouette, px) in ANIMATIONS.items():
        frames = [thicken(f, px) for f in to_square(loader(src))]
        out_dir = ROOT / name
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(frames):
            dark = recolor(f, (255, 255, 255)) if silhouette else f
            light = recolor(f, (0, 0, 0)) if silhouette else f
            dark.save(out_dir / f'dark_{name}_{i}.png')
            light.save(out_dir / f'light_{name}_{i}.png')
        print(f'{name}: {len(frames)} frames -> {out_dir}')


if __name__ == '__main__':
    main(sys.argv[1])
