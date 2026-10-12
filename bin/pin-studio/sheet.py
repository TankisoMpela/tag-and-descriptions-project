"""Compose rendered sheets into one contact sheet for review.

    bin/pin-studio/.venv/bin/python bin/pin-studio/sheet.py <dir> [width] [names...]

A name is a template name, a file in <dir>, or a path — so the 3:2 and 1:1
versions of the same sheet sit side by side, which is the only way to tell
whether a landscape sheet really wanted a different row plan. Each tile is
scaled to the same width and keeps its own aspect, because judging a sheet at
the marketplace's thumbnail width is the point; a fixed tile height would force
the pin's 2:3 onto a sheet rendered on another frame.
"""
import json
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).parent))
from pin_studio import CLASS_ORDERS, LABEL, LABEL_B, _down  # noqa: E402

d = Path(sys.argv[1])
w = int(sys.argv[2]) if len(sys.argv) > 2 else 300
bf = d / "pins.brief.json"
order = CLASS_ORDERS["elegant"]
if bf.exists():
    order = CLASS_ORDERS.get(json.loads(bf.read_text()).get("class") or "elegant",
                             CLASS_ORDERS["elegant"])
names = sys.argv[3:] or [f"pinterest_{i + 1}" for i in range(len(order))]


def locate(n):
    for cand in (d / n, *(d / (n + e) for e in (".jpg", ".png")), Path(n)):
        if cand.exists():
            return cand
    return None


imgs = []
for n in names:
    p = locate(n)
    if p is None:
        continue
    im = _down(skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(p))), w)
    imgs.append((n if p.parent == d else f"{p.parent.name}/{p.stem}", im))
label = {f"pinterest_{i + 1}": t for i, t in enumerate(order)}
pad = 10
th = max(im.height() for _, im in imgs)
sheet = skia.Surface.MakeRasterN32Premul(len(imgs) * (w + pad) + pad, th + 2 * pad)
cv = sheet.getCanvas()
cv.clear(skia.Color(22, 22, 24))
font = skia.Font(skia.Typeface.MakeFromFile(
    str(LABEL_B if LABEL_B.exists() else LABEL)), 16)
for i, (n, im) in enumerate(imgs):
    x = i * (w + pad) + pad
    cv.drawImage(im, x, pad)
    cv.drawString(label.get(n, n), x + 4, th + pad + 4, font,
                  skia.Paint(Color4f=skia.Color4f(1, 1, 1, 1)))
sheet.makeImageSnapshot().save(str(d / "sheet.png"))
print("wrote", d / "sheet.png", len(imgs), "sheets")
