"""Kernel self-test: does the layout layer actually prevent the two bug classes?

Run:  bin/pin-studio/.venv/bin/python bin/pin-studio/test_layout.py

The claim under test is narrow and checkable: for any copy, any face, any box,
Sheet.text() draws ink that (a) stays inside the declared box and (b) cannot
silently land on another block's ink. Everything else is taste; this is correctness.
"""
import sys
from pathlib import Path

import skia
from pin_studio import M, W, H, Box, Sheet, Type

FACES = {
    "didone": "outputs/font-preparation/080-cosette-marque/Cosette-Marque/CosetteMarque-Regular.otf",
    "brush": "outputs/font-preparation/077-kuro-ripper/Kuro-Ripper/KuroRipper-Regular.otf",
    "script": "outputs/font-preparation/082-restrained-flourish/Restrained-Flourish/RestrainedFlourish-Regular.otf",
    "serif": "font-factory/fonts/13-andallan/andallan/Andallan.otf",
}
ROOT = Path(__file__).resolve().parents[2]

COPY = {
    "short": "Stay soft.",
    "quote": "The sea does not reward those who are too anxious, too greedy, or too impatient.",
    "long": ("Be patient: no one can be a diamond at the very first. You must be content "
             "to be a pearl, and a grain of sand, and a shell that has not yet learned "
             "the shape of the water it lives in."),
    "unbreakable": "Supercalifragilisticexpialidocious and antidisestablishmentarianism",
}

fails = 0


def case(name, cond, detail=""):
    global fails
    print(f"  {'ok  ' if cond else 'FAIL'}  {name:52s} {detail}")
    fails += 0 if cond else 1


def sheet():
    s = skia.Surface.MakeRasterN32Premul(W, H)
    s.getCanvas().clear(skia.Color(255, 255, 255))
    return Sheet(s)


print("\n1. fit-to-box: ink never leaves the declared box, any face, any length")
for fname, fpath in FACES.items():
    t = Type(ROOT / fpath)
    for cname, text in COPY.items():
        box = Box(M, 300, W - 2 * M, 520)
        sh = sheet()
        size = sh.text("body", t, text, box, hi=220, lo=14, color=(20, 20, 20),
                       align="center", valign="middle", max_lines=9)
        if size is None:
            case(f"{fname}/{cname}", False, "no size found")
            continue
        i = sh.slots[0].ink
        inside = i.x >= box.x - 1 and i.y >= box.y - 1 and i.r <= box.r + 1 and i.b <= box.b + 1
        case(f"{fname}/{cname}", inside,
             f"{size:5.1f}px {sh.slots[0].lines}L ink "
             f"[{i.x:.0f},{i.y:.0f} -> {i.r:.0f},{i.b:.0f}] box "
             f"[{box.x:.0f},{box.y:.0f} -> {box.r:.0f},{box.b:.0f}]")

print("\n2. overlap is reported, not shipped")
sh = sheet()
t = Type(ROOT / FACES["didone"])
sh.text("hero", t, "Cosette", Box(M, 400, W - 2 * M, 300), hi=200, color=(0, 0, 0))
sh.text("sub", t, "a line of copy", Box(M, 400, W - 2 * M, 300), hi=48, color=(0, 0, 0))
v = sh.verify()
case("deliberate collision is caught", any(x.startswith("OVERLAP") for x in v),
     v[0] if v else "nothing reported")
sh2 = sheet()
sh2.text("hero", t, "Cosette", Box(M, 300, W - 2 * M, 300), hi=200, color=(0, 0, 0))
sh2.text("sub", t, "a line of copy", Box(M, 700, W - 2 * M, 120), hi=48, color=(0, 0, 0))
case("clean layout is silent", sh2.verify() == [], str(sh2.verify()))

print("\n3. off-canvas ink is reported")
sh3 = sheet()
sh3.text("hero", t, "Cosette Marque etymology", Box(-420, 300, 340, 300), hi=200,
         color=(0, 0, 0), bleed=False)
case("a box hanging off the canvas is flagged",
     any(x.startswith("OFF-CANVAS") for x in sh3.verify()), str(sh3.verify())[:80])

print("\n4. a slot that cannot fit at any legal size says so, with the reason")
sh4 = sheet()
r = sh4.text("tiny", t, COPY["unbreakable"], Box(M, 300, 120, 300), hi=200, lo=12)
case("word wider than the slot -> None + reason",
     r is None and "longest word" in (sh4.problems or [""])[0],
     (sh4.problems or ["no problem recorded"])[0][:100])
sh4b = sheet()
r = sh4b.text("tall", t, COPY["long"], Box(M, 300, W - 2 * M, 60), hi=200, lo=40)
case("copy too long for the slot height -> None + reason",
     r is None and "lines at" in (sh4b.problems or [""])[0],
     (sh4b.problems or ["no problem recorded"])[0][:100])

print("\n5. legibility floor is a real constraint, not a comment")
sh5 = sheet()
sh5.text("body", t, COPY["long"], Box(M, 300, W - 2 * M, 90), hi=220, lo=12,
         min_read=48, max_lines=9, color=(0, 0, 0))
case("shrinking below min_read is reported",
     any("legibility" in p for p in sh5.problems),
     f"{sh5.slots[0].size:.1f}px" if sh5.slots else "no slot")

print("\n6. unreadable ink is lifted against the measured ground, and says so")
sh6 = sheet()
sh6.text("onwhite", t, "Cosette", Box(M, 300, W - 2 * M, 260), hi=180,
         color=(250, 250, 250))
case("near-white on the white sheet is corrected, not shipped",
     any("lifted" in n for n in sh6.notes) and not sh6.problems,
     (sh6.notes or ["nothing reported"])[0][:92])
case("the correction clears the floor",
     all(float(n.split("-> ")[1].split(":1")[0]) >= 4.5 for n in sh6.notes),
     str(sh6.notes)[:92])
sh6b = sheet()
sh6b.cv.drawRect(skia.Rect.MakeXYWH(0, 240, W, 400),
                 skia.Paint(Color4f=skia.Color4f(0.06, 0.06, 0.08, 1)))
sh6b.text("onblack", t, "Cosette", Box(M, 300, W - 2 * M, 260), hi=180,
          color=(250, 250, 250))
case("near-white on a dark plate is left alone", not sh6b.notes and not sh6b.problems,
     str(sh6b.notes + sh6b.problems)[:92])
sh6c = sheet()
sh6c.cv.drawRect(skia.Rect.MakeXYWH(0, 240, W, 400),
                 skia.Paint(Color4f=skia.Color4f(0.80, 0.57, 0.39, 1)))
sh6c.text("onband", t, "Cosette", Box(M, 300, W - 2 * M, 260), hi=180,
          grad=((30, 30, 30), (250, 250, 250)))
case("a gradient is judged by its weakest end",
     any("lifted" in n for n in sh6c.notes), (sh6c.notes or ["nothing"])[0][:92])

print(f"\n{'ALL GREEN' if fails == 0 else str(fails) + ' FAILURE(S)'}")
sys.exit(1 if fails else 0)
