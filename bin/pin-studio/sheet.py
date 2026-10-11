"""Compose a font's rendered pins into one contact sheet for review.

    bin/pin-studio/.venv/bin/python bin/pin-studio/sheet.py <dir> [width] [names...]
"""
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).parent))
from pin_studio import LABEL, LABEL_B, PIN_ORDER, _down  # noqa: E402

d = Path(sys.argv[1])
w = int(sys.argv[2]) if len(sys.argv) > 2 else 300
names = sys.argv[3:] or [f"pinterest_{i + 1}" for i in range(len(PIN_ORDER))]
imgs = []
for n in names:
    for ext in (".jpg", ".png"):
        p = d / (n + ext)
        if p.exists():
            imgs.append((n, _down(skia.Image.MakeFromEncoded(
                skia.Data.MakeFromFileName(str(p))), w)))
            break
label = {f"pinterest_{i + 1}": t for i, t in enumerate(PIN_ORDER)}
tw, th = w, int(w * 1.5)
pad = 10
sheet = skia.Surface.MakeRasterN32Premul(len(imgs) * (tw + pad) + pad, th + 2 * pad)
cv = sheet.getCanvas()
cv.clear(skia.Color(22, 22, 24))
font = skia.Font(skia.Typeface.MakeFromFile(
    str(LABEL_B if LABEL_B.exists() else LABEL)), 16)
for i, (n, im) in enumerate(imgs):
    x = i * (tw + pad) + pad
    cv.drawImage(im, x, pad)
    cv.drawString(label.get(n, n), x + 4, th + pad + 4, font,
                  skia.Paint(Color4f=skia.Color4f(1, 1, 1, 1)))
sheet.makeImageSnapshot().save(str(d / "sheet.png"))
print("wrote", d / "sheet.png", len(imgs), "pins")
