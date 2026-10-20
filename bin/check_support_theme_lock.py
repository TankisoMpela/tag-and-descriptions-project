"""Which support panels does the theme actually move?

Renders take a long time, so this compares two sweeps that have already been
made — run pin_studio.py twice on the same font with two different --palette
values and point this script at the two 3x2 folders:

    python3 bin/check_support_theme_lock.py /tmp/a/3x2 /tmp/b/3x2

A panel whose bytes are identical cannot be moved by the theme at all. A panel
that differs prints its mean RGB delta, which separates a real recolour from a
panel that only shuffled its grain.
"""
import hashlib
import pathlib
import re
import sys


def key(path):
    return re.sub(r"^support-\d+_", "", path.stem)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    dirs = [pathlib.Path(a) for a in sys.argv[1:]]
    sheets = [{key(p): p for p in d.glob("*.png")} for d in dirs]
    names = sorted(set(sheets[0]) & set(sheets[1]))
    if not names:
        sys.exit(f"no support PNGs shared between {dirs[0]} and {dirs[1]}")
    print(f"{len(names)} panels compared")
    locked, moved = [], []
    for name in names:
        a, b = sheets[0][name], sheets[1][name]
        digest = [hashlib.sha1(p.read_bytes()).hexdigest() for p in (a, b)]
        if digest[0] == digest[1]:
            locked.append((name, 0.0))
        else:
            moved.append((name, delta(a, b)))
    print(f"  locked {len(locked)}  moved {len(moved)}\n")
    for group, label in ((moved, "MOVED BY THE THEME"), (locked, "THEME-LOCKED")):
        print(label)
        for name, d in sorted(group, key=lambda x: -x[1]):
            note = "  (grain shuffle only, colour is fixed)" if 0 < d < 1.0 else ""
            print(f"  {name:<20}{d:8.2f}{note}")
    return 0


def delta(a, b):
    """Mean absolute RGB difference over a fixed sample of pixels."""
    import random
    import skia
    pixels = []
    for path in (a, b):
        image = skia.Image.open(str(path))
        info = skia.ImageInfo.MakeN32(image.width(), image.height(),
                                      skia.ColorType.kRGBA_8888_ColorType,
                                      skia.AlphaType.kUnpremul_AlphaType)
        buf = bytearray(info.min_storable_bytes())
        if not image.read_pixels(info, {"pixels": buf, "stride": info.row_bytes()}):
            raise SystemExit(f"cannot decode {path}")
        pixels.append(buf)
    one, two = pixels
    rng = random.Random(7)
    total = n = 0
    for _ in range(20000):
        i = rng.randrange(0, min(len(one), len(two)) - 3, 4)
        for c in range(3):
            total += abs(one[i + c] - two[i + c])
            n += 1
    return total / max(1, n)


if __name__ == "__main__":
    sys.exit(main())
