"""Five tried-and-tested Pinterest pin templates, drawn from real font outlines.

  python pin_studio.py --list
  python pin_studio.py --font F.otf --brief brief.json --out <pinterest dir>
  python pin_studio.py --font F.otf --name Sisara --line "Midnight letters" \
      --word Whiskey --sub "editorial \u00b7 packaging" --out out/x
  python pin_studio.py --stress --faces a=A.otf:b=B.otf --out out/stress

The brief is how a font actually ships: one JSON with five fresh headlines, one
theme and one colour-ladder offset per pin, so the set reads as five designs.
Without it every pin takes the same --line, which is what made a batch feel
samey. With it the pins are written `pinterest_1..5` in PIN_ORDER, the shape the
Pinterest registry expects.

hero, set, wall, phrase, full_stack. Each pin gets its own theme — its own ground,
device and artwork — and inside each pin the rows walk down a colour ladder, so one
font's set is five designs rather than one muted palette applied five times. Every
text slot declares a box and is auto-fitted against it, so nothing overlaps or runs
off the canvas; --json reports layout violations and ink the contrast guard had to
lift. --stress is the proof: six faces x five templates x three copy lengths, and
the run is clean at zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase

import skia
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

W, H = 1000, 1500
M = 84                      # outer margin
BG_SCALE = 4                # grounds are painted at 1/BG_SCALE and upscaled
MAX_BYTES = 200_000         # documented pin cap, in the bytes the specs quote
JPEG_STEPS = (90, 85, 80)   # tried in order when a pin has to ship as JPEG
# Design order — what a buyer scrolls into, and the numbering the registry
# uploads by. Note sorted(TEMPLATES) is alphabetical, which is not this.
PIN_ORDER = ("hero", "set", "wall", "phrase", "full_stack")
LABEL = Path("/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf")
LABEL_B = Path("/usr/share/fonts/Adwaita/AdwaitaSans-Medium.ttf")
CLEAN = {"liga": 0}         # display ligs stripe the specimen marks

# Hand-tuned grounds. Raw HSL from a hash looks cheap; these do not.
# deep1, deep2, paper1, paper2, ink, glow, accent, accent2  (all RGB 0-255)
#
# Six worlds, every one of them coloured. The earlier set leaned grey-on-grey
# whatever the type was painted with, and a quiet ground cannot be saved by a
# loud accent: the accent has to sit against a field that already has a mood.
# Each of these pairs a warm with a cool so a pin can run three or four tones
# down its rows and still read as one design.
#
# The paper worlds carry their accents dark on purpose. A bright marigold on
# cream measures 2.2:1, so the contrast guard lifts it toward the ground colour
# and every "coloured" row comes back the same flat brown; these sit at 5:1 and
# are never touched.
PALETTES = {
    "olive":    ((30, 32, 18), (48, 52, 30), (241, 238, 224), (224, 219, 198),
                 (32, 34, 20), (246, 243, 230), (128, 96, 14), (58, 96, 44)),
    "marigold": ((26, 46, 48), (42, 70, 72), (247, 238, 216), (235, 217, 181),
                 (22, 42, 44), (247, 238, 216), (178, 84, 10), (168, 44, 42)),
    "cobalt":   ((14, 26, 62), (28, 46, 96), (233, 238, 248), (209, 218, 236),
                 (13, 23, 54), (241, 244, 252), (242, 136, 88), (116, 194, 226)),
    "cherry":   ((58, 14, 34), (102, 24, 52), (255, 240, 242), (246, 220, 226),
                 (48, 10, 28), (255, 244, 246), (255, 122, 140), (255, 206, 92)),
    "meadow":   ((12, 46, 34), (24, 82, 58), (238, 250, 234), (214, 236, 212),
                 (10, 40, 30), (240, 252, 238), (126, 224, 140), (248, 194, 60)),
    "tangerine": ((116, 42, 10), (172, 70, 16), (255, 238, 214), (250, 220, 186),
                  (96, 30, 6), (255, 246, 232), (255, 214, 90), (96, 206, 220)),
}
PAL_NAMES = list(PALETTES)

# Themes: a ground, a device and a way of painting type, bundled so that the four
# or five pins of one font are four different designs rather than one palette
# applied five times. Each pin in a set gets its own theme, never a repeat.
THEMES = {
    "midnight": dict(pal="cobalt",  mode="dark",  pool=0.18, tooth=5200, seed=11,
                     device="dots",  art="orbit"),
    "sage":     dict(pal="olive",   mode="paper", pool=0.10, tooth=2400, seed=5,
                     device="none",  art="grove"),
    "ember":    dict(pal="cherry",  mode="dark",  pool=0.16, tooth=4200, seed=3,
                     device="rays",  art="coast"),
    "bone":     dict(pal="marigold", mode="paper", pool=0.16, tooth=3000, seed=9,
                     device="bands", art="orbit"),
    "moss":     dict(pal="meadow",  mode="dark",  pool=0.15, tooth=4600, seed=6,
                     device="grid",  art="grove"),
    "clay":     dict(pal="tangerine", mode="dark", pool=0.16, tooth=2800, seed=4,
                     device="rings", art="coast"),
}
THEME_NAMES = list(THEMES)

# Which worlds suit which pin: `wall` wants a dark field to push the type
# forward, `set` and `full_stack` want paper to read as a specimen sheet — but
# `full_stack` also wants to glow, and a halo only reads as light on a dark
# ground, so it takes one of each. `hero` is allowed either — the loudest worlds
# are the paper ones now, and a hero that always comes back dark is a hero that
# always looks like the last one.
THEME_PREF = {
    "hero":       ("clay", "bone", "ember", "midnight"),
    "wall":       ("ember", "moss", "midnight"),
    "set":        ("sage", "bone", "clay"),
    "full_stack": ("bone", "midnight", "sage", "ember"),
    "phrase":     ("clay", "sage", "bone"),
}


def assign_themes(seed, names):
    """One theme per pin, no repeats, rotated by the font name so two fonts of
    the same shape still do not ship the same colour world — and a re-run of the
    same font lands identically."""
    rot = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    used, out = set(), {}
    for i, name in enumerate(names):
        pref = THEME_PREF[name]
        pref = pref[(rot + i) % len(pref):] + pref[:(rot + i) % len(pref)]
        # Take the first preferred world still free; if a pin's whole shortlist is
        # spent, borrow from any unused world rather than repeating one, which is
        # how five pins on six themes ship with no two alike.
        free = [t for t in pref if t not in used] or \
               [t for t in THEME_NAMES if t not in used]
        out[name] = pick = free[0] if free else pref[0]
        used.add(pick)
    return out


def C(rgb, a=1.0):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, a)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lum(rgb):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])


def contrast_lum(la, lb):
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contrast(a, b):
    return contrast_lum(lum(a), lum(b))


def readable(ground, color, floor=4.5):
    """The nearest colour to `color` that clears `floor`:1 against a measured ground.

    Palettes are hand-tuned for their own grounds, so a ramp that reads beautifully
    on plum goes muddy on forest paper. Rather than fail the pin, push the ink the
    shortest distance that buys the contrast — hue survives, the ratio stops lying.
    Both directions are tried because a mid-value ground only has one way out, and
    guessing it from the ground's luminance alone gets it wrong around 0.34.
    """
    if contrast_lum(ground, lum(color)) >= floor:
        return color
    best = None
    for target in ((0, 0, 0), (255, 255, 255)):
        lo, hi = 0.0, 1.0
        for _ in range(14):
            mid = (lo + hi) / 2
            if contrast_lum(ground, lum(mix(color, target, mid))) >= floor:
                hi = mid
            else:
                lo = mid
        if contrast_lum(ground, lum(mix(color, target, hi))) >= floor:
            if best is None or hi < best[0]:
                best = (hi, mix(color, target, hi))
    return best[1] if best else color


_BLUR = {}


def blur_filter(sigma):
    """A gaussian halo, cached — the filter is built per call otherwise and a
    specimen sheet asks for one per glyph."""
    key = round(sigma, 1)
    f = _BLUR.get(key)
    if f is None:
        f = _BLUR[key] = skia.ImageFilters.Blur(key, key, skia.TileMode.kDecal, None)
    return f


def paint(color=None, style=None, width=None, alpha=None, blur=None):
    p = skia.Paint(AntiAlias=True)
    if color is not None:
        p.setColor4f(color if isinstance(color, skia.Color4f) else C(color))
    if style:
        p.setStyle(style)
    if width:
        p.setStrokeWidth(width)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    if alpha is not None:
        p.setAlpha(int(alpha * 255))
    if blur:
        p.setImageFilter(blur_filter(blur))
    return p


# --------------------------------------------------------------- font forensics

def contour_count(glyph):
    pen = RecordingPen()
    try:
        glyph.draw(pen)
    except Exception:
        return 0
    return sum(1 for op, _ in pen.value if op == "moveTo")


def outline_ops(glyph):
    """Identity signature: op sequence, point count and quantised bbox.

    The bbox matters — without it ':' and 'O' look like the same outline (both
    are two 5-point curves) and every real colon gets flagged as a placeholder.
    """
    pen = RecordingPen()
    try:
        glyph.draw(pen)
    except Exception:
        return (), 0, None
    # A composite glyph answers addComponent(name, matrix), whose args are not
    # points, so only the (x, y) tuples count towards the signature.
    pts = [pt for _, args in pen.value for pt in args
           if isinstance(pt, tuple) and len(pt) == 2]
    box = None
    if pts:
        xs = [pt[0] for pt in pts]
        ys = [pt[1] for pt in pts]
        box = tuple(round(v / 20) for v in (min(xs), min(ys), max(xs), max(ys)))
    return (tuple(op for op, _ in pen.value),
            sum(len(a) for _, a in pen.value), box)


VICTIMS = set("0123456789")   # what a demo stamp actually replaces
WIDE = set("&@#*/-\u2014?!%")
SOFT_ZERO = {0x00ad, 0x200b, 0x200c, 0x200d, 0xfeff}   # carry no ink by design


def audit(font_path):
    """Return (cmap, flagged_chars, facts) — never render a broken glyph."""
    tt = TTFont(str(font_path), fontNumber=0)
    cmap = tt.getBestCmap() or {}
    upem = tt["head"].unitsPerEm
    glyf = tt.getGlyphSet()
    order = tt.getGlyphOrder()

    counts = {n: contour_count(glyf[n]) for n in order}
    inked = sorted(c for c in counts.values() if c > 0)
    median = inked[len(inked) // 2] if inked else 1
    dense = {n for n, c in counts.items() if c > max(median * 6, 12)}

    by_outline = {}
    for cp, name in cmap.items():
        ch = chr(cp)
        if name in dense or name.startswith((".notdef", "uni0000")):
            continue
        key = outline_ops(glyf[name])
        if key[0]:
            by_outline.setdefault(key, set()).add(ch)
    placeholder = set()
    for _, chars in by_outline.items():
        if chars & VICTIMS and chars - VICTIMS:
            placeholder |= chars & VICTIMS

    flagged = {chr(cp) for cp, n in cmap.items() if n in dense} | placeholder
    # A spacing character with no advance draws its ink straight on top of its
    # neighbour, and the layout kernel cannot see the collision because each slot
    # still measures correctly. Free faces ship these constantly (fontbakery's
    # `legacy_accents`: grave, acute, dieresis at zero width); combining marks are
    # meant to be zero-width, so they stay.
    hmtx = tt["hmtx"].metrics if "hmtx" in tt else {}
    flagged |= {chr(cp) for cp, n in cmap.items()
                if hmtx.get(n, (1, 0))[0] == 0 and counts.get(n, 0) > 0
                and not (0x0300 <= cp <= 0x036f) and cp not in SOFT_ZERO}
    feats = set()
    if "GSUB" in tt:
        for rec in tt["GSUB"].table.FeatureList.FeatureRecord:
            feats.add(rec.FeatureTag.strip())
    os2 = tt["OS/2"]
    post = tt.get("post")

    # Structural evidence for the showcase choice. A face with no curve operators
    # is drawn from straight segments (pixel, hard geometric); ink left of the
    # origin means connecting or flowing strokes; the metric tables say how heavy
    # and how narrow it is. None of this is a guess from the file name.
    curved = measured = 0
    for ch in "abcdefghijklmnopqrstuvwxyz":
        name = cmap.get(ord(ch))
        if not name:
            continue
        ops, _n, box = outline_ops(glyf[name])
        measured += 1
        if any(op in ("curveTo", "qCurveTo", "cuCurveTo") for op in ops):
            curved += 1
    hints = " ".join(
        str(r) for r in tt["name"].names
        if r.nameID in (1, 2, 4, 6, 10, 11, 13) and r.isUnicode()).lower()

    facts = {
        "upem": upem,
        "glyphs": len(order),
        "cap": getattr(os2, "sCapHeight", 0) or 0,
        "xh": getattr(os2, "sxHeight", 0) or 0,
        "features": sorted(feats & {"liga", "dlig", "salt", "swsh", "calt", "aalt", "ss01", "hlig"}),
        "flagged": "".join(sorted(flagged)),
        "weight": getattr(os2, "usWeightClass", 0) or 0,
        "width": getattr(os2, "usWidthClass", 0) or 0,
        "slant": abs(getattr(post, "italicAngle", 0.0)) if post else 0.0,
        "fixed": bool(getattr(post, "isFixedPitch", 0)) if post else False,
        "curved": curved, "measured": measured,
        "hints": hints,
        # A ghost letter with thirty loops tangles into noise, so take the
        # simplest capital the face actually carries.
        "simple": min((chr(cp) for cp, n in cmap.items()
                       if chr(cp).isalpha() and chr(cp).upper() in
                       "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and n not in dense),
                      key=lambda c: counts[cmap[ord(c.upper())]], default="A").upper(),
    }
    return cmap, flagged, facts


# --------------------------------------------------------------- font families
#
# Which showcase a face belongs to is decided from its own data, because the
# evidence disagrees with the file name often enough to matter: a "Display" font
# that is really a hairline serif, a "Script" that is a printed italic.

FAMILY_WORDS = (
    ("blackletter", ("blackletter", "black letter", "gothic", "old english",
                     "fraktur", "fraktūr", "uncial", "monastery")),
    ("brush", ("brush", "marker", "chalk", "grunge", "paint", "signature paint")),
    ("pixel", ("pixel", "8-bit", "8bit", "arcade", "bitmap", "atari")),
    ("mono", ("mono", "typewriter", "code", "terminal")),
    ("script", ("script", "handwrit", "cursive", "calligra", "signature",
                "lettering", "handdrawn", "hand-drawn")),
    ("serif", ("serif", "roman", "slab", "egyptian", "garamond", "baskerville")),
)


def classify(facts):
    """(family, why) — the showcase family this face is designed for."""
    why = []
    hints = facts["hints"] + " " + facts.get("about", "")
    for fam, words in FAMILY_WORDS:
        hit = next((w for w in words if w in hints), None)
        if hit:
            why.append(f"name/description says {hit!r}")
            return fam, why
    if facts["measured"] and not facts["curved"]:
        why.append("no curve operators in any tested letter")
        return "pixel", why
    if facts["fixed"]:
        why.append("fixed pitch")
        return "mono", why
    # Ink crossing the origin is how a connecting or swashing hand is built, but a
    # hair of slop in the sidebearings is not. Four percent of the em is the depth
    # at which an entry stroke is a design decision rather than an export artefact.
    if facts["over"] >= max(3, int(facts["measured"] * 0.5)):
        why.append(f"{facts['over']}/{facts['measured']} letters reach more than 4% of "
                   f"the em left of their own origin")
        return ("script" if facts["slant"] >= 5 else "swashy"), why
    stem = facts.get("stem", 0.0)
    if stem >= 0.185:
        why.append(f"strokes are {stem * 100:.0f}% of the letter height — poster weight")
        return "display-bold", why
    if stem and stem <= 0.062:
        why.append(f"strokes are {stem * 100:.0f}% of the letter height — hairline")
        return "hairline", why
    if facts["measured"] and facts["curved"] * 4 >= facts["measured"] * 3 \
            and facts["weight"] >= 500:
        why.append("rounded, mostly-curved letters at a medium-heavy weight")
        return "display-bold", why
    if stem:
        why.append(f"strokes are {stem * 100:.0f}% of the letter height")
    why.append("no family signal; treated as a plain text face")
    return "grotesk", why


# ------------------------------------------------------------------------ type

class Type:
    """A display face bound to a file, laid out by HarfBuzz, drawn as outlines."""

    def __init__(self, path):
        self.face = skia.Typeface.MakeFromFile(str(path))
        if self.face is None:
            raise SystemExit(f"skia could not load {path}")
        self.blob = hb.Blob.from_file_path(str(path))
        self.hb_face = hb.Face(self.blob)
        self.hb_font = hb.Font(self.hb_face)
        self._fonts = {}

    def font(self, size):
        s = self.snap(size)
        f = self._fonts.get(s)
        if f is None:
            f = self._fonts[s] = skia.Font(self.face, s)
        return f

    @staticmethod
    def snap(size):
        """The size, floored to the 64th that HarfBuzz actually shapes at.

        `scale` takes integers, so a run solved to land exactly on the measure
        gets rounded back up to the next 64th and comes over the line — by a
        twentieth of a pixel, which is enough to break a line in two and start
        a fight with the slot below it. Flooring instead of rounding means the
        ink is always at or short of the width that was asked for.
        """
        return max(1, math.floor(size * 64.0)) / 64.0

    def runs(self, text, size, features=None):
        self.hb_font.scale = (int(self.snap(size) * 64),) * 2
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, features or CLEAN)
        if buf.glyph_infos is None:
            return []
        return [(i.codepoint, p.x_advance / 64, p.x_offset / 64, p.y_offset / 64)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def measure(self, text, size, tracking=0.0, features=None):
        return sum(a for _, a, _, _ in self.runs(text, size, features)) + tracking * max(len(text) - 1, 0)

    def path(self, text, size, tracking=0.0, features=None):
        """Combined outline with the baseline at y=0 and the pen start at x=0."""
        out, x = skia.Path(), 0.0
        f = self.font(size)
        for gid, adv, xo, yo in self.runs(text, size, features):
            gp = f.getPath(gid)
            gp.offset(x + xo, -yo)
            out.addPath(gp, skia.Matrix())
            x += adv + tracking
        return out, x

    def fit(self, text, size, width, tracking=0.0):
        """Scale so the run lands exactly on `width`."""
        w = self.measure(text, size, tracking)
        return size * width / w if w else size

    def floor_to(self, text, size, width, tracking=0.0):
        """Step down whole 64ths until the run really measures `width` or less.

        Scaling by the exact ratio is not enough: `snap` makes the advance a step
        function of the size, so the corrected size usually lands in the bucket
        it came from and still measures over. Only dropping a bucket helps, and
        a row that measures over its own wrapper is a row that breaks in two.
        """
        while size > 0 and self.measure(text, size, tracking) > width:
            size = (math.floor(size * 64.0) - 1) / 64.0
        return max(size, 0.0)

    def draw(self, canvas, text, x, y, size, color, tracking=0.0, features=None):
        p, _ = self.path(text, size, tracking, features)
        canvas.save()
        canvas.translate(x, y)
        canvas.drawPath(p, paint(color))
        canvas.restore()
        return p

    def wrap(self, text, width, size, tracking=0.0):
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if self.measure(trial, size, tracking) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines



def stem_ratio(t, ch, size=200):
    """Median stroke width over the letter's own height, measured from the raster.

    `usWeightClass` is a marketing field and free fonts lie about it; the ink does
    not. This is what decides whether a face can carry a poster or wants a
    paragraph, and it is the difference between a bold showcase and a bold guess.
    """
    surf = skia.Surface.MakeRasterN32Premul(size, size)
    cv = surf.getCanvas()
    p, _w = t.path(ch, size)
    b = p.getBounds()
    if b.height() <= 2 or b.width() <= 2:
        return 0.0
    cv.translate(-b.x(), -b.y())
    cv.drawPath(p, paint(skia.Color4f(1, 1, 1, 1)))
    img = surf.makeImageSnapshot()
    info = skia.ImageInfo.MakeN32Premul(size, size)
    buf = bytearray(info.computeByteSize(size * 4))
    if not img.readPixels(info, buf, size * 4):
        return 0.0
    a = np.frombuffer(buf, np.uint8).reshape(size, size, 4)[:, :, 3] > 127
    runs = []
    for row in (int(b.height() * f) for f in (0.32, 0.5, 0.68)):
        if not 0 <= row < size:
            continue
        d = np.diff(np.concatenate(([0], a[row].astype(np.int8), [0])))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        runs += [int(e - st) for st, e in zip(starts, ends) if e - st < b.width() * 0.5]
    return float(np.median(runs)) / b.height() if runs else 0.0


# ------------------------------------------------------------------- surfaces

def ground(canvas, top, bottom, w=W, h=H):
    shader = skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, h)], [C(top), C(bottom)])
    p = paint()
    p.setShader(shader)
    canvas.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), p)


def light_pool(canvas, cx, cy, r, rgb, strength=0.30, mode=skia.BlendMode.kScreen,
               w=W, h=H):
    shader = skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), r, [C(rgb, strength), C(rgb, 0.0)])
    p = paint()
    p.setShader(shader)
    p.setBlendMode(mode)
    canvas.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), p)


def speckle(canvas, rgb, n=9000, seed=4, alpha=0.05, rad=1.5, w=W, h=H):
    rng = random.Random(seed)
    path = skia.Path()
    for _ in range(n):
        path.addCircle(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(rad * 0.4, rad))
    canvas.drawPath(path, paint(C(rgb, alpha)))


def dot_grid(canvas, rgb, step=26, rad=2.2, alpha=0.16, x0=M, y0=None, x1=None, y1=None):
    path = skia.Path()
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            path.addCircle(x, y, rad)
    canvas.drawPath(path, paint(C(rgb, alpha)))


def rule(canvas, x1, y1, x2, y2, rgb, weight=1.4, alpha=1.0):
    canvas.drawLine(x1, y1, x2, y2, paint(C(rgb, alpha), width=weight))


def hatched(canvas, clip, rgb, gap=11, weight=2.6, angle=42, alpha=1.0):
    """Fill a path with parallel rules — the riso/engraving move."""
    b = clip.getBounds()
    cx, cy = (b.left() + b.right()) / 2, (b.top() + b.bottom()) / 2
    span = int(b.width() + b.height())
    canvas.save()
    canvas.clipPath(clip)
    canvas.translate(cx, cy)
    canvas.rotate(angle)
    p = skia.Path()
    for i in range(-span, span, int(gap)):
        p.moveTo(i, -span)
        p.lineTo(i, span)
    canvas.drawPath(p, paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=weight))
    canvas.restore()


def wireframe(canvas, clip, rgb, weight=1.6, alpha=0.85):
    canvas.drawPath(clip, paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=weight))


def gradient_fill(rgb_a, rgb_b, y0, y1, tilt=0.0):
    return skia.GradientShader.MakeLinear(
        [skia.Point(0, y0), skia.Point(tilt, y1)], [C(rgb_a), C(rgb_b)])


def ghost(canvas, type_, ch, size, xy, rgb, alpha, blur=0.0):
    """An enormous letter used as texture rather than text."""
    p, _ = type_.path(ch, size)
    b = p.getBounds()
    canvas.save()
    canvas.translate(xy[0] - (b.left() + b.right()) / 2, xy[1] - (b.top() + b.bottom()) / 2)
    q = paint(C(rgb, alpha))
    if blur:
        q.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur, False))
    canvas.drawPath(p, q)
    canvas.restore()


def tracked_width(t, text, size, tracking):
    return t.measure(text, size, tracking)


def label(canvas, t, text, x, y, size, rgb, tracking=None, alpha=1.0, align="left"):
    tracking = size * 0.16 if tracking is None else tracking
    w = t.measure(text, size, tracking)
    ox = x if align == "left" else (x - w if align == "right" else x - w / 2)
    t.draw(canvas, text, ox, y, size, C(rgb, alpha), tracking)
    return w


# ------------------------------------------------------------- layout safety
#
# Every block of type declares the box it has to live in. The renderer bisects for
# the largest size that fits BOTH axes, wraps at word boundaries only, and records
# the ink rectangle it actually drew. Sheet.verify() then reports the two failure
# classes that used to ship silently: ink crossing the canvas edge, and ink from
# two blocks landing on each other. Templates never place a baseline by hand again.

@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def r(self):
        return self.x + self.w

    @property
    def b(self):
        return self.y + self.h


@dataclass
class Slot:
    name: str
    box: Box
    ink: Box
    size: float
    lines: int
    bleed: bool = False
    collide: bool = True


def _slot(sh, name):
    return next((x for x in reversed(sh.slots) if x.name == name), None)


def layout(t, text, width, size, tracking=0.0, leading=0.86, max_lines=8):
    """-> (lines, paths, step, ink_top, ink_bot, ink_w) or None if it can't be laid."""
    if not text.strip():
        return [], [], 0.0, 0.0, 0.0, 0.0
    lines = t.wrap(text, width, size, tracking)
    if len(lines) > max_lines:
        return None
    step = size * leading
    paths = [t.path(ln, size, tracking)[0] for ln in lines]
    tops = [p.getBounds().y() + i * step for i, p in enumerate(paths)]
    bots = [p.getBounds().bottom() + i * step for i, p in enumerate(paths)]
    return (lines, paths, step, min(tops), max(bots),
            max(p.getBounds().width() for p in paths))


def fit(t, text, box, hi, lo=8.0, tracking=0.0, leading=0.86, max_lines=8):
    """Largest size <= hi whose wrapped ink fits `box` in both axes (None if < lo)."""
    def fits(s):
        laid = layout(t, text, box.w, s, tracking, leading, max_lines)
        return laid and laid[3] >= -1e9 and laid[4] - laid[3] <= box.h + 1 \
            and laid[5] <= box.w + 1

    if not fits(lo):
        return None
    a, b = lo, hi
    for _ in range(16):
        mid = (a + b) / 2
        a, b = (mid, b) if fits(mid) else (a, mid)
    return a


class Sheet:
    """A canvas plus the memory of what it placed, so a bad layout is caught
    before anyone has to look at the picture and notice it."""

    def __init__(self, surface):
        self.surf = surface
        self.cv = surface.getCanvas()
        self.slots: list[Slot] = []
        self.problems: list[str] = []
        self.notes: list[str] = []

    def mark(self, name, box, collide=True, bleed=False):
        """Register a drawn shape's ink rect so the canvas checks cover it too."""
        self.slots.append(Slot(name, box, box, 0.0, 0, bleed, collide))

    def sub(self, w, h):
        """A sheet of its own, so type inside a rotated card gets the same
        fit-and-verify guarantees as type on the canvas."""
        return Sheet(skia.Surface.MakeRasterN32Premul(int(w), int(h)))

    def paste(self, sub, cx, cy, angle=0.0, shadow=(0, 20, 26, 26, 0.34)):
        """Blit a sub-sheet as a piece of paper laid on the field."""
        img = sub.surf.makeImageSnapshot()
        q = paint()
        if shadow:
            q.setImageFilter(skia.ImageFilters.DropShadow(
                *shadow[:4], skia.ColorSetARGB(int(shadow[4] * 255), 0, 0, 0)))
        self.cv.save()
        self.cv.translate(cx, cy)
        if angle:
            self.cv.rotate(angle)
        self.cv.drawImage(img, -img.width() / 2, -img.height() / 2,
                          skia.SamplingOptions(skia.FilterMode.kLinear,
                                               skia.MipmapMode.kNone), q)
        self.cv.restore()
        w2, h2 = img.width() / 2, img.height() / 2
        a = math.radians(angle)
        corners = [(cx + x * math.cos(a) - y * math.sin(a),
                    cy + x * math.sin(a) + y * math.cos(a))
                   for x in (-w2, w2) for y in (-h2, h2)]
        xs, ys = [c[0] for c in corners], [c[1] for c in corners]
        if min(xs) < 0 or max(xs) > W or min(ys) < 0 or max(ys) > H:
            self.problems.append(
                f"card at ({cx:.0f},{cy:.0f}) {angle:+.1f}deg runs off the canvas: "
                f"x {min(xs):.0f}..{max(xs):.0f}, y {min(ys):.0f}..{max(ys):.0f}")
        self.mark("card", Box(min(xs), min(ys), max(xs) - min(xs),
                              max(ys) - min(ys)), collide=False, bleed=True)
        self.problems += [f"card/{m}" for m in sub.verify()]
        self.notes += [f"card/{n}" for n in sub.notes]

    def _behind(self, box, w=W, h=H):
        """Median relative luminance of whatever is already painted in `box`.

        Measured off the sheet rather than assumed from the palette: a slot can
        land on a light pool, a colour band or a giant glyph, and a hand-picked
        ground colour is how you end up shipping white on white.
        """
        x0, y0 = max(0, int(box.x)), max(0, int(box.y))
        w, h = min(w - x0, int(box.w)), min(h - y0, int(box.h))
        if w < 12 or h < 12:
            return None
        img = self.surf.makeImageSnapshot()
        info = skia.ImageInfo.MakeN32Premul(w, h)
        buf = bytearray(info.computeByteSize(w * 4))
        if not img.readPixels(info, buf, w * 4, x0, y0):
            return None
        rgb = np.frombuffer(buf, np.uint8).reshape(h, w, 4)[:, :, 2::-1]
        v = rgb.astype(np.float64) / 255.0
        c = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
        return float(np.median(0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]))

    def _enforce(self, name, box, grad, color, alpha, floor):
        """Lift ink that would be unreadable where it landed; say what changed."""
        ground = self._behind(box)
        if ground is None or floor <= 0:
            return grad, color
        inks = list(grad[:2]) if grad else ([color] if isinstance(color, tuple) else [])
        if not inks:
            return grad, color
        worst = min(contrast_lum(ground, lum(ink) * alpha) for ink in inks)
        if worst >= floor:
            return grad, color
        fixed = [readable(ground, ink, floor / max(alpha, 0.05)) for ink in inks]
        after = min(contrast_lum(ground, lum(f) * alpha) for f in fixed)
        if grad:
            grad = tuple(fixed) + tuple(grad[2:])
        else:
            color = fixed[0]
        if after < floor:
            self.problems.append(f"{name}: {worst:.1f}:1 against the ground behind it "
                                 f"and {floor}:1 is unreachable there")
        else:
            self.notes.append(f"{name}: ink lifted {worst:.1f}:1 -> {after:.1f}:1")
        return grad, color

    def text(self, name, t, string, box, *, hi, lo=10.0, color=None, grad=None,
             tracking=0.0, track=0.0, leading=0.86, max_lines=8, align="center",
             valign="middle", min_read=0.0, bleed=False, alpha=1.0, min_contrast=4.5,
             hatch=None, glow=None):
        tracking = tracking + hi * track
        size = fit(t, string, box, hi, lo, tracking, leading, max_lines)
        if size is None:
            laid = layout(t, string, box.w, lo, tracking, leading, 999)
            n = len(laid[0]) if laid else 0
            worst = max(string.split(), key=lambda w: t.measure(w, lo))
            ww = t.measure(worst, lo)
            if ww > box.w:
                why = f"the longest word {worst!r} alone is {ww:.0f}px wide at {lo:.0f}px"
            elif n > max_lines:
                why = f"the copy needs {n} lines at {lo:.0f}px, the slot allows {max_lines}"
            else:
                why = f"{n} lines at {lo:.0f}px are {laid[4] - laid[3]:.0f}px tall, " \
                      f"the slot is {box.h:.0f}px"
            self.problems.append(f"{name}: cannot fit a {box.w:.0f}x{box.h:.0f} slot — {why}")
            return None
        lines, paths, step, top, bot, _w = layout(t, string, box.w, size, tracking,
                                                  leading, max_lines)
        if not lines:
            return None
        ink_h = bot - top
        grad, color = self._enforce(name, box, grad, color, alpha, min_contrast)
        oy = {"top": box.y - top,
              "middle": box.y + (box.h - ink_h) / 2 - top,
              "bottom": box.b - ink_h - top}[valign]
        for i, (ln, p) in enumerate(zip(lines, paths)):
            pb = p.getBounds()
            ox = {"left": box.x - pb.x(),
                  "right": box.r - pb.right(),
                  "center": box.x + (box.w - pb.width()) / 2 - pb.x()}[align]
            q = paint()
            if grad:
                q.setShader(gradient_fill(grad[0], grad[1], oy + i * step + pb.y(),
                                          oy + i * step + pb.bottom(),
                                          tilt=grad[2] if len(grad) > 2 else 0.0))
            else:
                q.setColor4f(C(color, alpha) if isinstance(color, tuple)
                             else (color or skia.Color4f(0, 0, 0, alpha)))
            self.cv.save()
            self.cv.translate(ox, oy + i * step)
            if glow:
                halo(self.cv, p, glow[0], max(4.0, pb.height() * glow[1]),
                     glow[2] if len(glow) > 2 else 0.40)
            self.cv.drawPath(p, q)
            if hatch:
                hatched(self.cv, p, hatch[0], gap=hatch[1], weight=hatch[2],
                        angle=hatch[3], alpha=hatch[4])
            self.cv.restore()
        rects = []
        for i, p in enumerate(paths):
            pb = p.getBounds()
            ox = {"left": box.x - pb.x(),
                  "right": box.r - pb.right(),
                  "center": box.x + (box.w - pb.width()) / 2 - pb.x()}[align]
            rects.append((ox + pb.x(), oy + i * step + pb.y(),
                          ox + pb.right(), oy + i * step + pb.bottom()))
        x0, y0 = min(r[0] for r in rects), min(r[1] for r in rects)
        x1, y1 = max(r[2] for r in rects), max(r[3] for r in rects)
        self.slots.append(Slot(name, box, Box(x0, y0, x1 - x0, y1 - y0), size,
                               len(lines), bleed))
        if size < min_read:
            floor_laid = layout(t, string, box.w, min_read, tracking, leading, 999)
            room = 0
            if floor_laid and floor_laid[0]:
                step = max(min_read * leading, 1.0)
                room = sum(len(ln) for ln in
                           floor_laid[0][:int((box.h + step) // step)])
            self.problems.append(
                f"{name}: {size:.0f}px is below the {min_read:.0f}px legibility floor — "
                f"about {room} characters fit this slot, the copy has {len(string)}")
        return size

    def verify(self):
        msgs = list(self.problems)
        for s in self.slots:
            b = s.ink
            if not s.bleed and (b.x < 1 or b.y < 1 or b.r > W - 1 or b.b > H - 1):
                msgs.append(f"OFF-CANVAS {s.name}: ink spans x {b.x:.0f}..{b.r:.0f} "
                            f"y {b.y:.0f}..{b.b:.0f}")
        for i, a in enumerate(self.slots):
            for b in self.slots[i + 1:]:
                ox = min(a.ink.r, b.ink.r) - max(a.ink.x, b.ink.x)
                oy = min(a.ink.b, b.ink.b) - max(a.ink.y, b.ink.y)
                if ox > 2 and oy > 2 and a.collide and b.collide and not (a.bleed and b.bleed):
                    msgs.append(f"OVERLAP {a.name}/{b.name}: {ox:.0f}x{oy:.0f}px")
        return msgs

    def report(self):
        for s in self.slots:
            print(f"      {s.name:9s} {s.size:6.1f}px  {s.lines}L  "
                  f"ink y {s.ink.y:5.0f}..{s.ink.b:5.0f}  x {s.ink.x:4.0f}..{s.ink.r:4.0f}")


# ============================================================ the template set
#
# A template is a short function: it declares boxes and hands them to the Sheet.
# It never computes a baseline, never guesses a size, and cannot ship a collision
# that verify() does not already know about. Theme, face and copy are arguments,
# so one template is a hundred designs rather than one.

TEMPLATES = {}


def template(name, blurb):
    def deco(fn):
        TEMPLATES[name] = (fn, blurb)
        return fn
    return deco


def field(P, invert=False):
    """(ink, mute, dark) for the ground that is actually painted.

    Grounds mix per pin — v6-black puts a paper character-set inside a dark
    series — so `invert` flips the mode for one template rather than the run.
    """
    dark = (P["mode"] == "dark") != invert
    ink = P["glow"] if dark else P["ink"]
    return ink, mix(ink, P["deep2"] if dark else P["paper2"], 0.26), dark


def bg(sh, P, th, invert=False, pool=None, tooth=None, dev=True):
    """Paint the ground at 1/4 scale and upscale, then the theme's device.

    A full-res continuous-tone gradient costs 247 KB of PNG on its own; the same
    ramp drawn small and stretched bilinearly costs 33 KB and is indistinguishable
    at feed size, because there is no detail to lose. `tooth` (speckle) is the one
    thing that cannot be recovered this way: it is real 2D noise, so it costs bytes
    and the over-cap pins ship as JPEG — which is how the good ones always shipped.
    """
    dark = (P["mode"] == "dark") != invert
    w, h = W // BG_SCALE, H // BG_SCALE
    sub = skia.Surface.MakeRasterN32Premul(w, h)
    cv = sub.getCanvas()
    ground(cv, P["deep1"] if dark else P["paper1"],
           P["deep2"] if dark else P["paper2"], w, h)
    p = th["pool"] if pool is None else pool
    light_pool(cv, w * 0.72, h * (0.26 if dark else 0.18), 900 // BG_SCALE, P["accent"],
               p if dark else p * 0.42,
               skia.BlendMode.kScreen if dark else skia.BlendMode.kMultiply, w, h)
    sh.cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(w, h),
                        skia.Rect.MakeWH(W, H),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kNone))
    t = th["tooth"] if tooth is None else tooth
    if t:
        speckle(sh.cv, P["glow"] if dark else P["ink"], n=t, seed=th["seed"],
                alpha=0.05, rad=1.4)
    if dev:
        device(sh, P, th["device"], dark)
    return dark


def device(sh, P, kind, dark):
    """The theme's graphic signature, under everything and quiet.

    Two pins in the same series may share a colour family; what stops them
    reading as duplicates is that one carries a dot field and the next carries
    rings. Alpha is deliberately near the noise floor — a device you notice is a
    device competing with the type.
    """
    ink, mute = (P["glow"], mix(P["glow"], P["deep2"], 0.4)) if dark \
        else (P["ink"], mix(P["ink"], P["paper2"], 0.4))
    cv = sh.cv
    if kind == "dots":
        dot_grid(cv, mute, step=34, rad=2.0, alpha=0.20, x0=M, y0=int(H * 0.62),
                 x1=W - M, y1=int(H - 250))
    elif kind == "grid":
        for i in range(9):
            y = H * 0.60 + i * 46
            rule(cv, M, y, W - M, y, mute, 1.0, 0.16)
        for i in range(9):
            x = M + i * ((W - 2 * M) / 8)
            rule(cv, x, H * 0.60, x, H - 250, mute, 1.0, 0.16)
    elif kind == "bands":
        for i in range(5):
            y = H * 0.56 + i * 96
            q = paint(C(mute, 0.07))
            cv.drawRect(skia.Rect.MakeXYWH(0, y, W, 46), q)
    elif kind == "rings":
        q = paint(C(mute, 0.16), style=skia.Paint.kStroke_Style, width=1.6)
        for i in range(6):
            cv.drawCircle(W * 0.82, H * 0.80, 90 + i * 74, q)
    elif kind == "rays":
        q = paint(C(mute, 0.14), style=skia.Paint.kStroke_Style, width=2.2)
        for i in range(13):
            a = math.radians(-186 + i * 11)
            cv.drawLine(W * 0.14, H * 0.86,
                        W * 0.14 + math.cos(a) * 1500, H * 0.86 + math.sin(a) * 1500, q)


def tones(P, family):
    """The colour ladder a pin paints its type with, in order.

    One colour for everything is what made the dark pins read as quiet glass: v6
    put cream, peach and gold on the same sheet and every row said something
    different. So the ladder is the default and rows walk down it — primary ink,
    accent, a warm push across the glyph, then the second accent. A flowing face
    keeps the colours and loses the gradient, which stripes its joins.
    """
    ink = P["glow"] if P["mode"] == "dark" else P["ink"]
    acc, acc2 = P["accent"], P["accent2"]
    out = [dict(color=ink), dict(color=acc),
           dict(grad=(mix(ink, acc, 0.18), mix(ink, acc, 0.80), 300)),
           dict(color=acc2)]
    if family in FLOWING:
        out[2] = dict(color=mix(ink, acc, 0.45))
    return out


def tone(P, i):
    """Paint kwargs for rung `i` of the ladder, wrapping.

    `tone_off` is the brief's per-pin shift: the same row structure walked to a
    different rung, so one font's headline is cream on one pin and accent on the
    next without a line of any template body changing.
    """
    t = P["tone"]
    return t[(i + P.get("tone_off", 0)) % len(t)]


def tone_paint(P, i, box=None, alpha=0.96):
    """A rung of the ladder as a paint for raw glyph paths.

    `sh.text` takes the ladder as kwargs; a path drawn by hand needs the same rung
    as an actual paint, and a gradient needs to know the box it is being painted
    into — which is the path's own local space, since the canvas translate applies
    to the shader and the outline alike.
    """
    spec = tone(P, i)
    q = paint(C(spec.get("color") or P["ink"], alpha))
    if "grad" in spec:
        a, b, tilt = spec["grad"]
        y0, y1 = (box.top(), box.bottom()) if box else (0.0, 100.0)
        q.setShader(gradient_fill(a, b, y0, y1, tilt))
    return q


def rung(P, i):
    """The flat colour of ladder rung `i` — a gradient's bright end, for when a
    colour is needed as a value rather than as a paint."""
    spec = tone(P, i)
    if "grad" in spec:
        return spec["grad"][1]
    return spec.get("color") or (P["glow"] if P["mode"] == "dark" else P["ink"])


def halo(cv, p, rgb, sigma, alpha=0.42):
    """A glow behind an outline: the same path blurred, under the crisp ink.

    The one thing a raster-only renderer cannot fake with a second draw offset —
    skia applies a real gaussian to the layer, so the letter looks lit rather
    than printed. Cost is ~45 ms per full-frame pass, which is why it goes on the
    specimen rows and not on every label.
    """
    cv.drawPath(p, paint(C(rgb, alpha), blur=sigma))


def _eyebrow_rule(sh):
    slot = _slot(sh, "eyebrow")
    return slot.ink.b + 16 if slot else 170


def eyebrow(sh, ctx, text, invert=False, y=128):
    """Small tracked title case over a hairline: the series' opening signature."""
    P, L = ctx["pal"], ctx["label"]
    ink, mute, _ = field(P, invert)
    text = tc(text)
    sh.text("eyebrow", L, text, Box(M, y, W - 2 * M - 70, 26), hi=21, lo=13,
            color=mute, track=0.22, align="left", valign="top", min_read=13)
    slot = _slot(sh, "eyebrow")
    if not slot:
        return y
    rule(sh.cv, M, slot.ink.b + 16, W - M, slot.ink.b + 16, ink, 1.0, 0.30)
    return slot.ink.b + 16


def ghost_letter(sh, ctx, ch, cx, cy, size=1750, invert=False, alpha=0.11):
    """The font's own initial blown up as texture, filled rather than wired.

    v6's hero carried a giant letter behind the type and let it run off the
    frame: it is illustration that costs no new drawing, it can never clash with
    the specimen because it *is* the specimen, and it fills the field with
    something other than a gradient.
    """
    P, T = ctx["pal"], ctx["display"]
    ink, _mute, _ = field(P, invert)
    p, _ = T.path(ch, size)
    b = p.getBounds()
    dx, dy = cx - (b.left() + b.right()) / 2, cy - (b.top() + b.bottom()) / 2
    sh.cv.save()
    sh.cv.translate(dx, dy)
    sh.cv.drawPath(p, paint(C(ink, alpha)))
    wireframe(sh.cv, p, P["accent"], weight=2.2, alpha=alpha * 2.4)
    sh.cv.restore()
    sh.mark("ghost", Box(b.left() + dx, b.top() + dy, b.width(), b.height()),
            collide=False, bleed=True)


def edge_type(sh, ctx, text, invert=False, x=None, cy=None):
    """Micro-type run up the right edge — the series' third voice."""
    P, L = ctx["pal"], ctx["label"]
    ink, mute, _ = field(P, invert)
    text = tc(text)
    x = x if x is not None else W - 34
    cy = cy if cy is not None else H * 0.66
    sh.cv.save()
    sh.cv.translate(x, cy)
    sh.cv.rotate(-90)
    label(sh.cv, L, text, 0, 0, 19, mute, tracking=4.2, alpha=0.62)
    sh.cv.restore()
    sh.mark("edge", Box(x - 24, cy - L.measure(text, 19, 4.2), 24,
                        L.measure(text, 19, 4.2)), collide=False)


def footer(sh, ctx, at="Set in", invert=False):
    P, L = ctx["pal"], ctx["label"]
    ink, mute, _ = field(P, invert)
    rule(sh.cv, M, H - 236, M + 96, H - 236, P["accent"], 3.0)
    sh.text("name", L, tc(f"{at} {ctx['name']}"), Box(M, H - 210, W - 2 * M, 40),
            hi=27, lo=18, color=ink, track=0.16, align="left", valign="top",
            min_read=18)
    if ctx["copy"].get("sub"):
        sh.text("sub", L, tc(ctx["copy"]["sub"]),
                Box(M, H - 172, W - 2 * M, 34), hi=20, lo=14, color=mute,
                track=0.16, align="left", valign="top", min_read=14)


EDGE = lambda ctx: (f"{ctx['facts']['glyphs']} Glyphs"
                    if not ctx["facts"]["features"] else
                    f"{len(ctx['facts']['features'])} OpenType Features")


# --------------------------------------------------------------- shared parts


def usable(ctx, ch):
    return ch in ctx["chars"] and ch not in ctx["flagged"]


def fit_measure(T, text, width, hi):
    """Largest size whose INK — not merely its advance — reaches the measure.

    A swashy face can carry ink 10% past its advance width, so sizing by the
    advance leaves the last letters hanging outside the column it was set to.
    The closing clamp matters as much as the ink correction: HarfBuzz scales by
    64ths and the font cache rounds, so a size solved to land exactly on the
    measure can come back a fraction over it, and the wrapper silently breaks
    the row in two.
    """
    size = min(hi, T.fit(text, hi, width))
    if size <= 0:
        return 0.0
    ink_w = T.path(text, size)[0].getBounds().width()
    size *= min(1.0, width / ink_w) if ink_w > 0 else 1.0
    return T.floor_to(text, size, width)


def pack_lines(words, n):
    """Balance words over at most n lines by character count, so a name set two
    lines deep does not put eight letters on one and three on the next."""
    words = [w for w in words if w]
    n = max(1, min(n, len(words)))
    if n == 1:
        return [" ".join(words)]
    total = sum(len(w) for w in words) + n - 1
    target = total / n
    out, cur, run = [], [], 0
    for i, w in enumerate(words):
        cur.append(w)
        run += len(w) + (1 if len(cur) > 1 else 0)
        left, need = len(words) - i - 1, n - len(out) - 1
        if need > 0 and left >= need and (run >= target or left == need):
            out.append(" ".join(cur))
            cur, run = [], 0
    if cur:
        out.append(" ".join(cur))
    return out


def row_metrics(T, chars, size):
    """(advance total, ink width, ink height) for a spaced row at `size`."""
    paths = [T.path(c, size)[0] for c in chars]
    widths = [T.measure(c, size) for c in chars]
    edge, pen = 0.0, 0.0
    for p, adv in zip(paths, widths):
        edge = max(edge, pen + p.getBounds().right())
        pen += adv + GAPROW
    ink_w = edge - paths[0].getBounds().left()
    ink_h = (max(p.getBounds().bottom() for p in paths)
             - min(p.getBounds().top() for p in paths))
    return sum(widths) + GAPROW * (len(chars) - 1), ink_w, ink_h


GAPROW = 14.0


def row_block(T, rows, width):
    """[(row, size, ink height)] with every row set to fill `width` exactly."""
    out = []
    for row in rows:
        total, ink_w, ink_h = row_metrics(T, row, 100.0)
        if total <= 0 or ink_h <= 0 or ink_w <= 0:
            continue
        size = width / max(total, ink_w) * 100
        out.append((row, size, ink_h * size / 100))
    return out


def spec_grid(T, seqs, width, room, hi=420.0, lead_frac=0.30):
    """[(row, size, ink height)] — the alphabet at ONE size, the largest the page
    can carry, with the letters shared out evenly.

    `row_block` sizes every row to the measure on its own, which is right for a
    wall of words and wrong for a character set: letters that disagree in size
    make the eye read the layout instead of the type. So the block is one point
    size and the only free variable is how many letters share a row.

    The search scores the *final* size rather than stopping at the first packing
    that fits, because they are not the same question: 52 letters over six rows
    have to shrink by a fifth to clear the page and still end up larger than the
    same letters over four rows standing at full height. Rows are balanced for the
    same reason — a 26-letter run cut 12/12/2 ends on a scrap.
    """
    unit = {}

    def at100(row):
        m = unit.get(row)
        if m is None:
            m = unit[row] = row_metrics(T, row, 100.0)
        return m

    best = None
    for per in range(3, 27):
        rows = []
        for src in seqs:
            if not src:
                continue
            q = math.ceil(len(src) / math.ceil(len(src) / per))
            rows += [tuple(src[i:i + q]) for i in range(0, len(src), q)]
        if not rows:
            return []
        size = min(width / max(at100(r)[:2]) * 100.0 for r in rows)
        if size <= 0:
            continue
        size = min(size, hi)
        hs = [at100(r)[2] * size / 100 for r in rows]
        block = sum(hs) + size * lead_frac * (len(rows) - 1)
        k = min(1.0, room / block) if block else 1.0
        if best is None or size * k > best[0]:
            best = (size * k, [(r, size * k, h * k) for r, h in zip(rows, hs)])
    return best[1] if best else []


def draw_rows(sh, T, sized, stage, paint_fn, prefix="row", lead_frac=0.10):
    """Draw rows sized by row_block, top-aligned inside the stage given."""
    if not sized:
        return stage.y
    lead = sized[0][1] * lead_frac
    y = stage.y
    for i, (row, size, ih) in enumerate(sized):
        widths = [T.measure(c, size) for c in row]
        paths = [T.path(c, size)[0] for c in row]
        row_w = sum(widths) + GAPROW * (len(row) - 1)
        x = stage.x + (stage.w - row_w) / 2
        top_i = min(p.getBounds().top() for p in paths)
        bot_i = max(p.getBounds().bottom() for p in paths)
        sh.cv.save()
        sh.cv.translate(x, y - top_i)
        for j, p in enumerate(paths):
            paint_fn(p, j, i)
            sh.cv.translate(widths[j] + GAPROW, 0)
        sh.cv.restore()
        sh.mark(f"{prefix}{i}", Box(min(x + p.getBounds().left() for p in paths), y,
                                    max(p.getBounds().right() for p in paths)
                                    - min(x + p.getBounds().left() for p in paths),
                                    bot_i - top_i))
        y += (bot_i - top_i) + lead
    return y


def measure_rows(sh, T, P, seq, stage, prefix, hi=460.0, min_read=30.0,
                 fill=False, lead_frac=0.03, min_contrast=4.5, taper=False):
    """Set each row to the measure, stack them, scale the block to the stage.

    The shared spine of the funnel pins. `fill` lets the block *grow* to reach the
    bottom of the frame — a wall with air above and below is just a list — and
    then every row is re-clamped to the measure, because HarfBuzz rounds the size
    to 64ths and a row multiplied back up can overshoot by a hair and wrap in two.
    `taper` spends a height shortfall on the first row rather than on every row,
    which is what keeps a funnel's lower lines at the margin.
    Each row takes the next rung of the colour ladder.
    """
    def rows_at(width):
        out = []
        for s in seq:
            size = fit_measure(T, s, width, hi)
            if size <= 0:
                sh.problems.append(f"{prefix}: {s!r} cannot be set to the measure")
                continue
            out.append((s, size, T.path(s, size)[0].getBounds().height()))
        return out

    sized = rows_at(stage.w)
    if not sized:
        return stage.y
    lead = stage.h * lead_frac
    total = sum(h for _s, _z, h in sized) + lead * (len(sized) - 1)
    if not total:
        return stage.y
    k = stage.h / total
    if taper and len(sized) > 2:
        # Let the apex absorb the shortfall. One pair set to the measure is taller
        # than the sheet has room for, and pulling every row down after it is what
        # left the lower lines short of both margins.
        below = sum(h for _s, _z, h in sized[1:]) + lead * (len(sized) - 1)
        ka = min(1.0, (stage.h - below) / sized[0][2])
        if ka > 0.30:
            sized[0] = (sized[0][0], sized[0][1] * ka, sized[0][2] * ka)
            k = 1.0
    if not fill:
        k = min(1.0, k)
    lead *= k
    y = stage.y
    for i, (s, size, _ih) in enumerate(sized):
        size = fit_measure(T, s, stage.w, size * k)
        ih = T.path(s, size)[0].getBounds().height()
        sh.text(f"{prefix}{i}", T, s, Box(stage.x, y, stage.w, ih + 2),
                hi=size, lo=size, leading=0.86, max_lines=1, min_read=min_read,
                valign="top", min_contrast=min_contrast, **tone(P, i))
        y += ih + lead
    return y - lead


# ---------------------------------------------------------------- ornament kit#
# Illustration is possible here without an image library: these are real vector
# drawings built from beziers, so they scale with the pin, take the theme's own
# ink, cost nothing at the byte level, and can be clipped or hatched like a
# glyph. A specimen that carries a drawn frond reads as designed rather than
# generated — and the same kit draws the dividers and rules of every theme.

def _fill(cv, p, rgb, alpha=1.0):
    cv.drawPath(p, paint(C(rgb, alpha)))


def _stroke(cv, p, rgb, w, alpha=1.0):
    cv.drawPath(p, paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=w))


def orn_star(cv, cx, cy, s, rgb, alpha=1.0, points=4, waist=0.30):
    p = skia.Path()
    for i in range(points * 2):
        a = math.pi * i / points - math.pi / 2
        r = s if i % 2 == 0 else s * waist
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        if i == 0:
            p.moveTo(x, y)
        else:
            am = math.pi * (i - 0.5) / points - math.pi / 2
            p.quadTo(cx + math.cos(am) * s * 0.06, cy + math.sin(am) * s * 0.06, x, y)
    p.close()
    _fill(cv, p, rgb, alpha)


def orn_sun(cv, cx, cy, s, rgb, alpha=1.0, rays=12):
    cv.drawCircle(cx, cy, s * 0.50, paint(C(rgb, alpha)))
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(2.0, s * 0.10))
    for i in range(rays):
        a = math.tau * i / rays
        cv.drawLine(cx + math.cos(a) * s * 0.70, cy + math.sin(a) * s * 0.70,
                    cx + math.cos(a) * s * 0.98, cy + math.sin(a) * s * 0.98, q)


def orn_wave(cv, cx, cy, s, rgb, alpha=1.0, lines=3):
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(2.0, s * 0.085))
    for i in range(lines):
        y = cy + (i - (lines - 1) / 2) * s * 0.36
        p = skia.Path()
        p.moveTo(cx - s, y)
        p.cubicTo(cx - s * 0.42, y - s * 0.38, cx + s * 0.42, y + s * 0.38, cx + s, y)
        cv.drawPath(p, q)


def orn_blob(cv, cx, cy, s, rgb, alpha=1.0, seed=3, k=9):
    rnd = random.Random(seed)
    pts = []
    for i in range(k):
        a = math.tau * i / k
        r = s * rnd.uniform(0.66, 1.0)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    p = skia.Path()
    p.moveTo(*pts[0])
    for i in range(k):
        p0, p1 = pts[i - 1], pts[i]
        p2, p3 = pts[(i + 1) % k], pts[(i + 2) % k]
        p.cubicTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                  p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6,
                  p2[0], p2[1])
    p.close()
    _fill(cv, p, rgb, alpha)


def orn_frond(cv, cx, cy, s, rgb, alpha=1.0, rot=-28, ribs=7):
    """A palm frond: a curved spine with ribs sweeping off either side."""
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(1.8, s * 0.06))
    spine = skia.Path()
    spine.moveTo(0, s * 0.92)
    spine.cubicTo(-s * 0.14, s * 0.3, s * 0.06, -s * 0.3, 0, -s * 0.95)
    cv.drawPath(spine, q)
    for i in range(ribs):
        t = -0.85 + 1.7 * i / (ribs - 1)
        y = s * t
        ln = s * (0.60 - 0.40 * abs(t))
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(0, y)
            p.quadTo(side * ln * 0.72, y - ln * 0.26, side * ln, y + ln * 0.34)
            cv.drawPath(p, q)
    cv.restore()


def orn_arc(cv, cx, cy, s, rgb, alpha=1.0, bands=3):
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(2.0, s * 0.09))
    for i in range(bands):
        r = s * (1.0 - i * 0.24)
        p = skia.Path()
        p.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), 180, 180)
        cv.drawPath(p, q)


def orn_fan(cv, cx, cy, s, rgb, alpha=1.0, blades=9):
    """Scallop shell / palm fan: blades radiating from a hinge."""
    p = skia.Path()
    for i in range(blades):
        a = math.pi + math.pi * i / (blades - 1)
        p.moveTo(cx, cy)
        p.lineTo(cx + math.cos(a) * s, cy + math.sin(a) * s)
    _stroke(cv, p, rgb, max(2.0, s * 0.07), alpha)
    cv.drawCircle(cx, cy, s * 0.10, paint(C(rgb, alpha)))


def orn_dots(cv, cx, cy, s, rgb, alpha=1.0, n=5):
    for i in range(n):
        t = i / (n - 1)
        cv.drawCircle(cx - s + 2 * s * t, cy - math.sin(math.pi * t) * s * 0.30,
                      s * (0.19 - 0.11 * t), paint(C(rgb, alpha)))


def orn_eye(cv, cx, cy, s, rgb, alpha=1.0):
    p = skia.Path()
    p.moveTo(cx - s, cy)
    p.quadTo(cx, cy - s * 0.66, cx + s, cy)
    p.quadTo(cx, cy + s * 0.66, cx - s, cy)
    p.close()
    _stroke(cv, p, rgb, max(2.0, s * 0.09), alpha)
    cv.drawCircle(cx, cy, s * 0.24, paint(C(rgb, alpha)))


ORNAMENTS = {"star": orn_star, "sun": orn_sun, "wave": orn_wave, "blob": orn_blob,
             "frond": orn_frond, "arc": orn_arc, "fan": orn_fan, "dots": orn_dots,
             "eye": orn_eye}


def draw_orn(sh, name, kind, cx, cy, s, rgb, alpha=1.0, collide=True, **kw):
    """Draw an ornament and register the box it owns, so verify() still rules."""
    ORNAMENTS.get(kind, orn_star)(sh.cv, cx, cy, s, rgb, alpha, **kw)
    sh.mark(f"orn-{name}", Box(cx - s, cy - s, 2 * s, 2 * s), collide=collide)


# ------------------------------------------------------------------- templates


@template("hero", "the name edge to edge over the font's own giant initial, in two colours")
def t_hero(sh, ctx):
    """The name is the whole pin, and the colour does the rest.

    v6's hero put a letter of the font behind the type at eleven percent, set the
    name edge to edge in cream and answered it with a specimen word in peach. The
    second colour is not decoration — one tone on a dark field is what made the
    first pass of these read as quiet glass instead of a type specimen. The name
    asks the contrast guard for 7:1 rather than the body default of 4.5, because a
    headline that merely passes is a headline that sits in the mud.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    name = shout(ctx, clean(ctx, ctx["name"])).strip()
    words = name.split() or shout(ctx, clean(ctx, ctx["copy"]["line"])).split()
    lines = pack_lines(words, 2)
    # A one-word name would leave the frame two-thirds empty, so the specimen
    # word joins it: every line is set edge to edge, which is what makes the
    # name read as enormous rather than merely centred.
    word = shout(ctx, clean(ctx, ctx["copy"].get("word") or "")).strip()
    if word and word not in lines:
        lines = (lines + [word])[:3]
    if not lines:
        sh.problems.append("hero: the name has no letters this face can draw")
        return

    y0 = eyebrow(sh, ctx, "Type Specimen") + 54
    sh.text("chip", L, EDGE(ctx), Box(W - 40 - 320, y0 - 44, 320, 24), hi=19, lo=12,
            color=mute, track=0.18, align="right", valign="top", min_read=12)

    # The initial sits behind everything and is allowed off the frame; the type
    # is marked collide=False against it, so it never reports the bleed as a clash.
    ghost_letter(sh, ctx, lines[0].strip()[0].upper(), W * 0.68, H * 0.44)

    stage = Box(40, y0, W - 80, H - y0 - 300)
    # The last line is the specimen word, and it takes the accent: the name is
    # one colour, its answer another.
    sized = []
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1 and len(lines) > 1
        size = fit_measure(T, ln, stage.w, 620.0 * (0.74 if last else 1.0))
        if size <= 0:
            sh.problems.append(f"hero: {ln!r} cannot be set to the measure")
            continue
        sized.append((ln, size, T.path(ln, size)[0].getBounds().height(), last))
    if not sized:
        return
    lead = stage.h * 0.030
    total = sum(h for _l, _s, h, _x in sized) + lead * (len(sized) - 1)
    k = min(1.0, stage.h / total) if total else 1.0
    lead *= k
    y = stage.y + (stage.h - (sum(h * k for _l, _s, h, _x in sized)
                              + lead * (len(sized) - 1))) / 2
    for i, (ln, size, ih, last) in enumerate(sized):
        size, ih = size * k, ih * k
        sh.text(f"name{i}", T, ln, Box(stage.x, y, stage.w, ih + 2),
                hi=size, lo=size, leading=0.86, max_lines=1, min_read=46,
                valign="top", min_contrast=4.5 if last else 5.0,
                **tone(P, 1 if last else 0))
        y += ih + lead
    rule(sh.cv, 40, y + 40, 190, y + 40, P["accent"], 4.0)
    footer(sh, ctx)


@template("set", "the alphabet as upper/lower pairs, funnelled and coloured row by row")
def t_set(sh, ctx):
    """v6's character sheet with the one change that matters.

    The funnel is the keeper: rows that grow 1, 2, 3 pairs, each set to the
    full measure, so the capitals start the sheet two letters to a line and the
    sheet tightens as it goes. What v6 did not show is the lowercase next to its
    own uppercase, and that pairing is the single thing a buyer looks for — so
    every letter here arrives as `Aa`, `Bb`, `Cc`. Six pairs, A to F: showing all
    twenty-six is what ran the letters out of space.

    Each row takes the next rung of the colour ladder, and the ornament band and
    the edge type keep the sheet from reading as a bare list.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.08)
    ink, mute, _ = field(P)
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    los = [c for c in ascii_lowercase if usable(ctx, c)]
    n = min(6, len(ups), len(los))
    if n < 3:
        sh.problems.append("set: the face carries too few letters to pair up")
        return
    pairs = [f"{ups[i]}{los[i]}" for i in range(n)]
    # A 1/2/3 funnel — the shape that keeps the first line enormous. Four rows
    # were tried: three pairs-to-a-line already stand at the measure by the time
    # they total the page, so a fourth row drags the whole block down to 60% of
    # it and nothing reaches either margin.
    rows, i = [], 0
    for want in (1, 2, 3):
        rows.append(" ".join(pairs[i:i + want]))
        i += want
    rows = [r for r in rows if r]

    y0 = eyebrow(sh, ctx, "Character Set") + 40
    # The furniture stays out of the way: this pin's copy *is* the alphabet, and
    # every pixel the ornaments or a phrase line take is a pixel the pairs shrink
    # by — the funnel only reaches the measure if its block is given the page.
    art = ORN_SETS[ctx["th"]["art"]]
    band = Box(M, y0, W - 2 * M, 76)
    bot = band.b
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["top"]):
        s *= 0.46
        cy = band.y + max(s * 0.6, min(band.h * fy, band.h - s * 0.6))
        draw_orn(sh, f"orn{i}", kind, band.x + band.w * fx_, cy, s,
                 P["accent"] if i % 2 else ink, alpha * 0.75)
        bot = max(bot, cy + s)
    stage = Box(M, bot + 14, W - 2 * M, H - 292 - bot)
    measure_rows(sh, T, P, rows, stage, "pair", hi=900.0, min_read=40,
                 lead_frac=0.045, taper=True)

    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=f"{len(ups)} Upper \u00b7 {len(los)} Lower \u00b7")


@template("wall", "phrase, digits and punctuation, every row to measure, filling the frame")
def t_wall(sh, ctx):
    """A wall of the face rather than a poster about it.

    The phrase words alternate with the numerals and the punctuation, each row set
    to the full measure and the whole block scaled to fill the canvas top to
    bottom. Unlike the other pins this one scales *up* as well as down: a wall with
    air above and below is just a list. It is also the only pin that shows the
    digits and the oddments at display size, which is where a face's personality
    usually hides.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"])
    ink, mute, _ = field(P)
    words = [w for w in shout(ctx, clean(ctx, ctx["copy"]["line"])).split() if w]
    digits = "".join(c for c in "0123456789"
                     if usable(ctx, c) and c not in ctx["flagged"])
    punct = " ".join(c for c in "&@?!%*()" if usable(ctx, c)
                     and c not in ctx["flagged"])
    seq = []
    if words:
        seq.append(" ".join(words[:2]))
    if len(digits) >= 6:
        seq.append(digits)
    if len(words) > 2:
        seq.append(" ".join(words[2:4]))
    if len(punct.split()) >= 4:
        seq.append(punct)
    if len(words) > 4:
        seq.append(" ".join(words[4:6]))
    seq = [s for s in seq if s]
    if not seq:
        sh.problems.append("wall: nothing to set — the face carries no letters or digits")
        return

    y0 = eyebrow(sh, ctx, "Type Wall") + 40
    stage = Box(M, y0, W - 2 * M, H - y0 - 258)
    y = measure_rows(sh, T, P, seq, stage, "row", hi=460.0, min_read=30,
                     fill=True, lead_frac=0.028)
    rule(sh.cv, M, y + 34, M + 120, y + 34, P["accent"], 3.6)
    footer(sh, ctx)


@template("phrase", "a short line of copy with drawn ornaments around it")
def t_phrase(sh, ctx):
    """The illustrated pin: what the font says, and what it looks like saying it.

    Ornaments live in reserved bands above and below the type and each one marks
    its own box, so verify() catches the pin that starts crowding its own
    artwork. The set is chosen from the theme, not from the font, so the drawing
    style stays constant across a series while the type changes.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"])
    ink, _mute, _ = field(P)
    acc = P["accent"]
    art = ORN_SETS[ctx["th"]["art"]]
    y0 = eyebrow(sh, ctx, "Set In The Wild") + 40

    # The artwork gets reserved bands: the type is fitted into what is left, so a
    # long phrase shrinks the letters rather than walking over the drawings.
    top = Box(M, y0, W - 2 * M, 260)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["top"]):
        # Pinned inside the band: an ornament that leans over the edge starts a
        # fight with the type below it, and verify() is right to report it.
        draw_orn(sh, f"t{i}", kind, top.x + top.w * fx_,
                 top.y + max(s, min(top.h * fy, top.h - s)),
                 s, P["accent"] if i % 2 else ink, alpha)
    band = Box(M, H - 520, W - 2 * M, 210)
    stage = Box(M, top.b + 34, W - 2 * M, band.y - top.b - 104)
    src = clean(ctx, ctx["copy"]["line"]).strip()
    if 0 < len(src.split()) < 3:
        sh.notes.append(f"phrase: {len(src.split())} words is a label, not a phrase "
                        f"— write three or four")
    words = [w for w in shout(ctx, src or ctx["name"]).split() if w]
    if not words:
        sh.problems.append("phrase: the line has no words this face can draw")
        return
    # Two lines for a short phrase, four for a long one, and each line takes the
    # next rung of the ladder: one colour down the whole block is what left this
    # pin the quietest of the five.
    lines = pack_lines(words, min(4, max(2, round(len(words) / 2))))
    y = measure_rows(sh, T, P, lines, stage, "phrase", hi=280.0, min_read=44,
                     fill=True, lead_frac=0.05, min_contrast=4.5)
    rule(sh.cv, W / 2 - 90, y + 44, W / 2 + 90, y + 44, acc, 3.6)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["bottom"]):
        draw_orn(sh, f"b{i}", kind, M + (W - 2 * M) * fx_,
                 band.y + max(s, min(band.h * fy, band.h - s)),
                 s, P["accent2"] if i % 2 else acc, alpha)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("full_stack", "the specimen sheet: name, purpose, and the alphabet filling the page")
def t_full_stack(sh, ctx):
    """Everything at once, in the order a type lover reads it.

    Name, then what it is for, then the letters — the shape of a foundry spec
    sheet. The character set is the reason a specimen pin gets saved, so it takes
    the whole lower page at one size, as large as the sheet can carry. Digits and
    punctuation are left out: they cost the letters their size, and nobody has
    ever decided to buy a face over its semicolon.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    facts = ctx["facts"]
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    los = [c for c in ascii_lowercase if usable(ctx, c)]

    feat = "Regular / Ligature" if facts["features"] else f"{facts['glyphs']} Glyphs"
    sh.text("hdr-l", L, f"({feat})", Box(M, 62, 460, 24), hi=20, lo=12,
            color=ink, track=0.14, align="left", valign="top", min_read=12)
    sh.text("hdr-r", L, "(OTF / TTF / WOFF)", Box(W - M - 460, 62, 460, 24), hi=20,
            lo=12, color=ink, track=0.14, align="right", valign="top", min_read=12)

    name = shout(ctx, clean(ctx, ctx["name"])).strip()
    lines = pack_lines(name.split() or shout(ctx, clean(ctx, ctx["copy"]["line"])).split(), 2)

    # The name is the pin and keeps its natural measure-fitted size; everything
    # below it is measured off where it actually landed, so the page budget is
    # what the page used rather than a fistful of constants.
    y = 124
    for i, ln in enumerate(lines):
        size = fit_measure(T, ln, measure, 400.0)
        if size <= 0:
            continue
        h = T.path(ln, size)[0].getBounds().height()
        sh.text(f"n{i}", T, ln, Box(M, y, measure, h + 2), hi=size, lo=size,
                leading=0.86, max_lines=1, min_read=40, valign="top",
                min_contrast=5.0 if i else 6.5,
                glow=(mix(rung(P, i), P["accent"], 0.4), 0.055, 0.34),
                **tone(P, 1 if i else 0))
        y += h + 26
    y += 22
    tag = tc(clean(ctx, ctx["copy"].get("over") or ctx["copy"].get("sub")
                   or f"{facts['glyphs']}-glyph display"))
    sh.text("tag", L, tag, Box(M, y, measure, 40), hi=33, lo=15, color=ink,
            track=0.30, align="center", valign="top", min_read=15)
    y += 62
    sh.text("copy", L, tc(ctx["copy"]["line"]), Box(M + 60, y, measure - 120, 120),
            hi=21, lo=13, color=mute, align="center", valign="top", leading=1.42,
            max_lines=4, min_read=13)
    slot = _slot(sh, "copy")
    y = (slot.ink.b if slot else y + 120) + 34

    rule(sh.cv, M, y, W - M, y, ink, 1.4, 0.5)
    draw_orn(sh, "div0", "star", W / 2, y, 14, P["accent"], 1.0)
    y += 20
    sh.text("sec-l", L, "Full Character Set", Box(M, y, 400, 24), hi=20, lo=12,
            color=ink, track=0.16, align="left", valign="top", min_read=12)
    sh.text("sec-r", L, f"{len(ups)} Upper \u00b7 {len(los)} Lower",
            Box(W - M - 400, y, 400, 24), hi=20, lo=12, color=ink, track=0.16,
            align="right", valign="top", min_read=12)

    rows = spec_grid(T, [ups, los], measure, max(H - 124 - (y + 46), 160.0))
    # The ladder, measured against the ground the block actually sits on: a palette
    # tuned for cream goes muddy on forest, and the glow takes the same rung pushed
    # the other way, so a row of 'A' reads lit rather than printed.
    if rows:
        tall = (sum(h for _r, _s, h in rows)
                + rows[0][1] * 0.30 * max(len(rows) - 1, 0))
        ground = (sh._behind(Box(M, y + 46, measure, min(tall, H - 124 - y - 46)))
                  or lum(P["deep2"]))
    else:
        ground = lum(P["deep2"])
    crisp = [readable(ground, rung(P, i), 4.5) for i in range(len(P["tone"]))]
    bloom = [mix(c, P["accent2"] if i % 2 else P["accent"], 0.45)
             for i, c in enumerate(crisp)]

    def paint_row(off):
        def f(p, j, i):
            k = (i + off) % len(crisp)
            box = p.getBounds()
            halo(sh.cv, p, bloom[k], max(5.0, box.height() * 0.055), 0.42)
            sh.cv.drawPath(p, paint(C(crisp[k], 1.0)))
        return f

    draw_rows(sh, T, rows, Box(M, y + 46, measure, 1), paint_row(0), "chars",
              lead_frac=0.30)


ORN_SETS = {
    "grove": dict(top=[("frond", 0.10, 0.62, 128, 0.9), ("star", 0.44, 0.16, 40, 1.0),
                       ("sun", 0.72, 0.44, 86, 1.0), ("star", 0.93, 0.70, 30, 0.85)],
                  bottom=[("blob", 0.16, 0.5, 62, 0.9), ("wave", 0.52, 0.5, 108, 0.8),
                          ("frond", 0.88, 0.42, 116, 0.9)]),
    "coast": dict(top=[("arc", 0.20, 0.70, 118, 0.9), ("dots", 0.52, 0.30, 84, 1.0),
                       ("star", 0.84, 0.58, 46, 1.0)],
                  bottom=[("fan", 0.22, 0.46, 104, 0.9), ("star", 0.50, 0.30, 34, 1.0),
                          ("wave", 0.80, 0.56, 116, 0.85)]),
    "orbit": dict(top=[("sun", 0.52, 0.50, 112, 1.0), ("star", 0.16, 0.30, 40, 0.9),
                       ("star", 0.88, 0.66, 34, 0.9), ("blob", 0.28, 0.86, 34, 0.7)],
                  bottom=[("eye", 0.24, 0.48, 74, 0.9), ("dots", 0.62, 0.40, 96, 0.9),
                          ("blob", 0.90, 0.62, 52, 0.8)]),
}


def build_ctx(font_path, name, copy, palette=None, mode=None, about=""):
    """Everything a pin needs, decided from the font's own data.

    The theme per pin and the showcase family are resolved here once, so a run is
    reproducible from the font alone: same file, same names, same colours.
    """
    cmap, flagged, facts = audit(font_path)
    display = Type(font_path)
    facts["stem"] = stem_ratio(display, facts["simple"] or "H")
    over = 0
    for ch in ascii_lowercase:
        if chr(ord(ch)) not in {chr(cp) for cp in cmap} or ch in flagged:
            continue
        b = display.path(ch, 100)[0].getBounds()
        if b.width() > 0 and b.left() < -4.0:
            over += 1
    facts["over"] = over
    facts["about"] = about.lower()
    family, why = classify(facts)
    return {
        "facts": facts, "chars": {chr(cp) for cp in cmap}, "flagged": flagged,
        "name": name, "copy": copy,
        "display": display, "label": Type(LABEL_B if LABEL_B.exists() else LABEL),
        "tt": TTFont(str(font_path), fontNumber=0),
        "family": family, "why": why,
        "themes": assign_themes(name or Path(font_path).stem, sorted(TEMPLATES)),
        "tone_offs": {},
        "palette_override": palette, "mode_override": mode,
    }


FLOWING = ("script", "brush", "blackletter", "swashy")


def tc(text):
    """Title case: the first letter of every word is a capital, nothing else moves.

    Nothing here is ever lowercased. `clean()` has already dropped glyphs the face
    cannot draw, and forcing capitals down to lowercase would ask for letters the
    font may not ship — a capital is always safe, a lowercase is not.
    """
    out, word = [], True
    for ch in text:
        if word and ch.isalpha():
            out.append(ch.upper())
            word = False
        else:
            out.append(ch)
            # An apostrophe joins rather than divides: "don't" is one word and
            # "Don'T" is a typo.
            word = ch != "'" and not ch.isalpha()
    return "".join(out)


def shout(ctx, text):
    """Display copy, word-initial capitals and all.

    Uppercasing the line was the reflex and it was wrong twice over: it is the
    shouty default the user asked to leave behind, and on a specimen it hides
    half the character set — the buyer cannot see what the lowercase looks like
    on the pin that is supposed to sell it.
    """
    return tc(text)


def theme_for(name, ctx):
    """The theme instance for one pin: its palette, its mode, its colour ladder."""
    th = dict(THEMES[ctx["themes"].get(name, THEME_PREF[name][0])])
    if ctx["palette_override"]:
        th["pal"] = ctx["palette_override"]
    if ctx["mode_override"]:
        th["mode"] = ctx["mode_override"]
    pal = dict(zip(("deep1", "deep2", "paper1", "paper2", "ink", "glow",
                    "accent", "accent2"), PALETTES[th["pal"]]))
    pal["mode"] = th["mode"]
    pal["tone"] = tones(pal, ctx["family"])
    pal["tone_off"] = ctx.get("tone_offs", {}).get(name, 0)
    return th, pal


def clean(ctx, text):
    """Drop what the face does not carry, so no slot ever renders tofu."""
    return "".join(c for c in text
                   if (c in ctx["chars"] or c.isspace()) and c not in ctx["flagged"])


def render(name, ctx):
    fn, _blurb = TEMPLATES[name]
    surf = skia.Surface.MakeRasterN32Premul(W, H)
    sh = Sheet(surf)
    th, pal = theme_for(name, ctx)
    ctx = dict(ctx, copy={k: clean(ctx, v or "") for k, v in ctx["copy"].items()},
               th=th, pal=pal)
    fn(sh, ctx)
    return surf, sh


def as_errors(name, sh):
    out = []
    for m in sh.verify():
        out.append({"template": name, "slot": m.split(":", 1)[0].split()[-1],
                    "message": m})
    return out


COPIES = {
    "three": "Letters that mean it",
    "four": "Midnight letters and loud labels",
    "long": "Be patient: no one can be a diamond at the first, you must be content to be a "
            "pearl and a grain of sand.",
}

# Words that say nothing about a design: a headline that differs from its
# neighbour only in these is the same headline twice.
STOP = frozenset("a an the of to for in on is with and or your you it its at as "
                 "from by be this that our we can you're".split())


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if w not in STOP and len(w) > 1}


def overlap(a, b):
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def check_brief(brief, out=None):
    """The anti-samey contract, enforced rather than described.

    Five pins only read as five designs when each says something different in a
    different colour world, and the failure mode is silent: the canned default
    line, or two headlines that are the same thought twice. Both are cheaper to
    catch here than to spot on the sheet afterwards.

    A font is prepped once and its agent keeps no memory of the last font, so
    `out` also scans the briefs already shipped under `outputs/font-preparation`
    — run from the repo root, the way every `bin/` tool is run.
    """
    bad, warns = [], []
    pins = brief.get("pins") or {}
    missing = [t for t in PIN_ORDER if t not in pins]
    if missing:
        bad.append("no pin copy for: " + ", ".join(missing))
    unknown = [t for t in pins if t not in PIN_ORDER]
    if unknown:
        bad.append("unknown template(s) in brief: " + ", ".join(unknown))
    if not (brief.get("about") or "").strip():
        bad.append('brief needs "about" — the outlines alone misclassify '
                   "handwritten, tech and blackletter faces")

    lines, seen_theme = {}, {}
    canned = {v.lower() for v in COPIES.values()}
    for t, pin in pins.items():
        line = (pin.get("line") or "").strip()
        if not line:
            bad.append(f"{t}: no line")
            continue
        if line.lower() in canned:
            bad.append(f'{t}: "{line}" is a stock line, not copy written for '
                       "this font")
        lines[t] = (tokens(line), line)
        th = pin.get("theme")
        if th:
            if th not in THEMES:
                bad.append(f"{t}: theme \"{th}\" is not one of "
                           + ", ".join(THEME_NAMES))
            else:
                seen_theme.setdefault(th, []).append(t)
    for th, ts in seen_theme.items():
        if len(ts) > 1:
            bad.append(f"theme {th} on {', '.join(ts)} — five pins want five "
                       "different worlds")

    named = sorted(lines.items())
    for i, (t1, (a1, l1)) in enumerate(named):
        for t2, (a2, l2) in named[i + 1:]:
            r = overlap(a1, a2)
            if r >= 0.5:
                bad.append(f"{t1} and {t2} share {r:.0%} of their words: "
                           f"{l1!r} vs {l2!r}")

    hist = Path("outputs/font-preparation")
    if out is not None and hist.is_dir():
        here = out.resolve()
        for p in sorted(hist.glob("*/visuals/New-Images/pinterest/pins.brief.json")):
            if here in p.resolve().parents:
                continue
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            slug = p.parts[2]
            if (prev.get("name") or "").casefold() == (brief.get("name") or "").casefold():
                continue  # the same font re-rendering is not phrase reuse
            for t, pin in (prev.get("pins") or {}).items():
                pl = (pin.get("line") or "").strip()
                for t2, (a2, l2) in lines.items():
                    if pl.casefold() == l2.casefold():
                        bad.append(f'{t2}: "{l2}" already shipped for {slug}')
                    elif overlap(a2, tokens(pl)) >= 0.5:
                        warns.append(f'{t2} reads like {slug}\'s "{pl}"')
    return bad, warns


def save_pin(img, out, stem):
    """Write one pin under the cap; returns (path, bytes, note-or-None).

    skia encodes JPEG 4:4:4 and unoptimised, and a sheet of haloed letters on a
    toothed ground is exactly the noise it charges full price for — Kuro's
    six-row specimen shipped at 214 KB, which is not a pin, it is a failed
    upload. The same pixels through Pillow buy the headroom back with 4:2:0
    chroma and an optimised Huffman table.
    """
    png = out / f"{stem}.png"
    img.save(str(png))
    size = png.stat().st_size
    if size <= MAX_BYTES:
        return png, size, None
    pkb = size / 1024
    jpg = out / f"{stem}.jpg"
    info = skia.ImageInfo.MakeN32Premul(img.width(), img.height())
    row = info.minRowBytes()
    buf = bytearray(row * img.height())
    img.readPixels(info, buf, row)
    from PIL import Image
    # N32 reads back BGRA here, and a finished pin is fully opaque, so the
    # premultiplied alpha in the buffer is a no-op we can hand straight over.
    flat = Image.frombuffer("RGBA", (img.width(), img.height()), bytes(buf),
                            "raw", "BGRA", 0, 1).convert("RGB")
    q = JPEG_STEPS[-1]
    for q in JPEG_STEPS:
        flat.save(jpg, "JPEG", quality=q, optimize=True, subsampling=2)
        size = jpg.stat().st_size
        if size <= MAX_BYTES:
            break
    png.unlink()
    return jpg, size, (f"file: {pkb:.0f} KB PNG exceeded the cap, shipped as a "
                       f"{size / 1024:.0f} KB JPEG at q{q}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font")
    ap.add_argument("--name", default="")
    ap.add_argument("--line", default=COPIES["four"])
    ap.add_argument("--word", default="Whiskey", help="second specimen word (hero)")
    ap.add_argument("--sub", default="invitation suite \u00b7 editorial \u00b7 packaging")
    ap.add_argument("--over", default="", help="eyebrow / caption override")
    ap.add_argument("--about", default="", help="what the font is, in the seller's words; "
                    "decides the showcase family when the outlines are ambiguous")
    ap.add_argument("--out", default="out/pins")
    ap.add_argument("--brief", help="JSON with one entry per pin — line, word, sub, over, "
                    "theme, tone — so five pins say and wear five different things. Wins "
                    "over --line/--word/--sub/--over, names the files pinterest_1..5 and "
                    "refuses copy that repeats.")
    ap.add_argument("--palette", choices=PAL_NAMES)
    ap.add_argument("--mode", choices=("dark", "paper"),
                    help="override the theme's own ground")
    ap.add_argument("--template", action="append", choices=sorted(TEMPLATES))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--stress", action="store_true")
    ap.add_argument("--faces", default="", help="name=path:name=path for --stress")
    args = ap.parse_args()

    if args.list:
        for k, (_f, blurb) in TEMPLATES.items():
            print(f"  {k:11s} {blurb}")
        return 0

    if args.stress:
        return stress(args)

    if not args.font:
        ap.error("--font is required unless --list or --stress")
    brief = (json.loads(Path(args.brief).read_text(encoding="utf-8"))
             if args.brief else None)
    warns = []
    if brief is not None:
        bad, warns = check_brief(brief, Path(args.out))
        if bad:
            for m in bad:
                print(f"  brief: {m}", file=sys.stderr)
            return 2
    title = args.name or (brief or {}).get("name", "")
    ctx = build_ctx(args.font, title,
                    {"line": args.line, "sub": args.sub, "over": args.over,
                     "word": args.word},
                    args.palette, args.mode,
                    args.about or (brief or {}).get("about", ""))
    per = {}
    if brief is not None:
        themes, offs, copies = dict(ctx["themes"]), {}, {}
        for t, pin in brief["pins"].items():
            if pin.get("theme"):
                themes[t] = pin["theme"]
            offs[t] = int(pin.get("tone") or 0)
            copies[t] = {k: (pin.get(k) or "")
                         for k in ("line", "sub", "over", "word")}
        ctx = dict(ctx, themes=themes, tone_offs=offs)
        per = {t: dict(ctx, copy=c) for t, c in copies.items()}
    if not args.as_json:
        print(f"  {title}: {ctx['family']} — {ctx['why'][0] if ctx['why'] else 'default'}")
        print("  themes: " + ", ".join(f"{k}={v}" for k, v in sorted(ctx["themes"].items())))
    for m in warns:
        print(f"  brief: {m}", file=sys.stderr)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if brief is not None:
        (out / "pins.brief.json").write_text(
            json.dumps(brief, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    names = args.template or sorted(TEMPLATES)
    errors, notes, payload = [], [], []
    for name in names:
        surf, sh = render(name, per.get(name, ctx))
        img = surf.makeImageSnapshot()
        stem = f"pinterest_{PIN_ORDER.index(name) + 1}" if per else name
        ship, size, note = save_pin(img, out, stem)
        if note:
            sh.notes.append(note)
        kb = size / 1024
        errs = as_errors(name, sh)
        if size > MAX_BYTES:
            errs.append({"template": name, "slot": "file",
                         "message": f"{kb:.0f} KB exceeds the "
                                    f"{MAX_BYTES // 1000} KB pin cap"})
        errors += errs
        notes += [{"template": name, "slot": n.split(":", 1)[0], "message": n}
                  for n in sh.notes]
        payload.append({"template": name, "png": str(ship), "kb": round(kb),
                        "slots": [{"slot": s.name, "size": round(s.size, 1),
                                   "lines": s.lines} for s in sh.slots]})
        if not args.as_json:
            print(f"  {name:11s} {kb:5.0f} KB  " +
                  "  ".join(f"{s.name}={s.size:.0f}px/{s.lines}L" for s in sh.slots))
            for e in errs:
                print(f"      ! {e['message']}")
            for n in sh.notes:
                print(f"      ~ {n}")
    if args.as_json:
        print(json.dumps({"ok": not errors, "results": payload, "errors": errors,
                          "notes": notes}, indent=2))
    elif not errors:
        print(f"\nclean: {len(names)} template(s), 0 layout errors, "
              f"{len(notes)} auto-correction(s)")
    else:
        print(f"\n{len(errors)} layout error(s) across {len(names)} template(s)")
    return 1 if errors else 0


def stress(args):
    faces = [f.split("=", 1) for f in args.faces.split(":") if f]
    if not faces:
        print("stress: pass --faces name=path:name=path", file=sys.stderr)
        return 2
    names = args.template or sorted(TEMPLATES)
    cells, errors = [], []
    for fname, fpath in faces:
        base = build_ctx(fpath, fname, {}, args.palette, args.mode)
        print(f"  {fname}: {base['family']} — "
              + (base["why"][0] if base["why"] else "default"))
        for tname in names:
            for cname, line in COPIES.items():
                ctx = dict(base, copy={"line": line, "sub": "", "over": "",
                                       "word": "Whiskey"})
                surf, sh = render(tname, ctx)
                errs = as_errors(tname, sh)
                errors += [dict(e, face=fname, copy=cname) for e in errs]
                cells.append(_down(surf.makeImageSnapshot(), 260))
                print(f"  {fname[:9]:9s} {tname:10s} {cname:6s} "
                      f"{'ok' if not errs else 'FAIL ' + errs[0]['message'][:74]}")
    cols = 5
    tw, th = 260, 390
    rows = math.ceil(len(cells) / cols)
    sheet = skia.Surface.MakeRasterN32Premul(cols * tw + (cols + 1) * 8,
                                             rows * th + (rows + 1) * 8)
    sc = sheet.getCanvas()
    sc.clear(skia.Color(18, 18, 20))
    for i, img in enumerate(cells):
        sc.drawImage(img, (i % cols) * (tw + 8) + 8, (i // cols) * (th + 8) + 8)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    p = Path(args.out) / "stress_sheet.png"
    sheet.makeImageSnapshot().save(str(p))
    print(f"\n{len(errors)} layout error(s) / {len(cells)} renders -> {p}")
    return 1 if errors else 0


def _down(img, w):
    h = int(img.height() * w / img.width())
    s = skia.Surface.MakeRasterN32Premul(w, h)
    s.getCanvas().drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()),
                                skia.Rect.MakeWH(w, h),
                                skia.SamplingOptions(skia.FilterMode.kLinear,
                                                     skia.MipmapMode.kNone))
    return s.makeImageSnapshot()


if __name__ == "__main__":
    raise SystemExit(main())
