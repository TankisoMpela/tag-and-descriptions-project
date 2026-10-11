"""Five tried-and-tested Pinterest pin templates, drawn from real font outlines.

  python pin_studio.py --list
  python pin_studio.py --font F.otf --brief brief.json --out <pinterest dir>
  python pin_studio.py --font F.otf --name Sisara --line "Midnight letters" \
      --word Whiskey --sub "editorial \u00b7 packaging" --out out/x
  python pin_studio.py --stress --faces a=A.otf:b=B.otf --out out/stress

The brief is how a font actually ships: one JSON with five fresh headlines, one
theme and one colour-ladder offset per pin, so the set reads as five designs.
Without it every pin takes the same --line, which is what made a batch feel
samey. With it the pins are written `pinterest_1..5` in the brief's class order —
elegant is hero, set, wall, phrase, full_stack; blackletter is initials, knotband,
scriptorium, folio, carol; sports is crest, bib, lane, finish, timer; script is
guide, copybook, trace, sample, markup — which is the shape the Pinterest registry
expects either way. Each pin gets its own theme — its own ground,
device and artwork — and inside each pin the rows walk down a colour ladder, so one
font's set is five designs rather than one muted palette applied five times. Every
text slot declares a box and is auto-fitted against it, so nothing overlaps or runs
off the canvas; --json reports layout violations and ink the contrast guard had to
lift. --stress is the proof: every class x six faces x five templates x three copy
lengths, and the run is clean at zero.
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
# A template's frame is the surface it is drawn on. `pin` is the shipped size and
# the one everything below was tuned at; the two specimen frames exist because the
# marketplace handoff already demands exactly these pixel dimensions.
FRAMES = {"pin": (W, H), "3x2": (2400, 1600), "1x1": (1600, 1600)}
MAX_BYTES = 200_000         # documented pin cap, in the bytes the specs quote
JPEG_STEPS = (90, 85, 80)   # tried in order when a pin has to ship as JPEG
# Design order — what a buyer scrolls into, and the numbering the registry
# uploads by. Note sorted(TEMPLATES) is alphabetical, which is not this.
PIN_ORDER = ("hero", "set", "wall", "phrase", "full_stack")
BLACK_ORDER = ("initials", "knotband", "scriptorium", "folio", "carol")
SPORT_ORDER = ("crest", "bib", "lane", "finish", "timer")
SCRIPT_ORDER = ("guide", "copybook", "trace", "sample", "markup")
# A brief's optional "class" picks the order; every class still ships
# pinterest_1..5, so the registry, blob and daily tools never learn the word.
CLASS_ORDERS = {"elegant": PIN_ORDER, "blackletter": BLACK_ORDER,
                "sports": SPORT_ORDER, "script": SCRIPT_ORDER}
# The same four classes, on their second surface: the factual specimen sheets that
# replace the Pillow ones. Two sheets per class, each drawn at both marketplace
# ratios, so the order is four names per class and the registry holds sixteen —
# eight bodies, each registered twice. The class is in the name because TEMPLATES
# is flat and `letters_3x2` cannot belong to four classes at once.
SPECIMEN_FRAMES = ("3x2", "1x1")
SPECIMEN_SHEETS = ("letters", "numerals")
SPECIMEN_ORDERS = {cls: tuple(f"{cls}_{s}_{f}"
                              for f in SPECIMEN_FRAMES for s in SPECIMEN_SHEETS)
                   for cls in CLASS_ORDERS}
# One theme per class, not per sheet: sixteen preference rows would be sixteen
# chances to drift, and a specimen is one kind of picture whatever the class.
SPECIMEN_THEME = {"elegant": "sage", "blackletter": "vellum",
                  "sports": "asphalt", "script": "graphite"}
# ...and with a brief in hand the sheet wears the world the class's set-equivalent
# pin wore, so a shop's five pins and its two specimens are one series.
SPECIMEN_SET = {"elegant": "set", "blackletter": "knotband",
                "sports": "lane", "script": "markup"}
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
    # The two sports worlds are neutral grounds with one warm and one cool signal
    # each, because a race number is yellow and a penalty flag is red — the colour
    # carries the meaning, not the mood. No browns: on a hard monoline they read as
    # a printing fault rather than as warmth.
    "asphalt":   ((24, 26, 31), (41, 45, 52), (233, 236, 240), (206, 211, 218),
                  (20, 22, 27), (243, 246, 249), (245, 204, 25), (88, 196, 232)),
    "chrome":    ((30, 34, 40), (52, 58, 66), (224, 228, 234), (198, 204, 212),
                  (26, 30, 36), (240, 244, 248), (150, 24, 36), (18, 74, 130)),
    # The two script worlds are deliberately the two greys of the bench itself: a
    # pencil and an ink bottle. Every other ground is coloured because warm
    # neutral type wanted a field with a mood; here the neutrality *is* the mood,
    # and the warmth comes from the two pencils — red for the correction, blue for
    # the note — so the ladder still runs four distinguishable tones.
    "graphite":  ((52, 56, 64), (74, 80, 92), (243, 244, 246), (216, 220, 228),
                  (30, 34, 42), (247, 249, 252), (168, 40, 50), (22, 92, 142)),
    "inkwell":   ((16, 24, 30), (30, 44, 52), (230, 238, 236), (198, 212, 212),
                  (12, 20, 26), (238, 244, 244), (232, 180, 74), (98, 188, 200)),
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
    # Class-owned worlds. `cls` keeps them out of the elegant rotation: the
    # manuscript grounds only appear when a brief says blackletter, the neutral
    # ones only when it says sports, the two grey ones only when it says script
    # (or the brief names the world itself).
    "vellum":   dict(pal="marigold", mode="paper", pool=0.12, tooth=2600, seed=7,
                     device="bands", art="knot", cls="blackletter"),
    "gilded":   dict(pal="cobalt", mode="dark", pool=0.17, tooth=4800, seed=2,
                     device="rays", art="foil", cls="blackletter"),
    "asphalt":  dict(pal="asphalt", mode="dark", pool=0.16, tooth=3000, seed=8,
                     device="lanes", art="gantry", cls="sports"),
    "chrome":   dict(pal="chrome", mode="paper", pool=0.12, tooth=2600, seed=1,
                     device="grid", art="sector", cls="sports"),
    # Both script worlds wear the same device on purpose: the pricked band is not
    # one theme's decoration, it is the ground this class is drawn on.
    "graphite": dict(pal="graphite", mode="paper", pool=0.12, tooth=2400, seed=10,
                     device="ruling", art="penwork", cls="script"),
    "inkwell":  dict(pal="inkwell", mode="dark", pool=0.15, tooth=4400, seed=12,
                     device="ruling", art="flourish", cls="script"),
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
    # The blackletter class. `knotband` and `carol` are liturgical — a vellum
    # ground under drawn furniture; `scriptorium` is the writing desk at night, so
    # it wants dark; `initials` and `folio` carry either.
    "initials":    ("vellum", "bone", "gilded"),
    "knotband":    ("vellum", "bone", "sage"),
    "scriptorium": ("gilded", "midnight", "moss"),
    "folio":       ("vellum", "gilded", "clay"),
    "carol":       ("vellum", "sage", "gilded"),
    # The sports class. `lane` and `timer` are the two that must read as equipment,
    # so they lead with the grounds no other class owns; the rest take a shared
    # world now and then so a five-pin set is not one grey series.
    "crest":       ("asphalt", "chrome", "midnight"),
    "bib":         ("chrome", "asphalt", "bone"),
    "lane":        ("asphalt", "moss", "chrome"),
    "finish":      ("chrome", "asphalt", "midnight"),
    "timer":       ("asphalt", "midnight", "chrome"),
    # The script class. `copybook` and `sample` are paper objects — a drill page
    # and a pinned sample both want the light ground; `trace` and `markup` are the
    # ink ones. Only this class's own worlds and the six shared ones are named:
    # `assign_themes` filters its fallback pool by class but not the shortlist, so
    # a preference for another class's world would smuggle it in.
    "guide":       ("graphite", "inkwell", "bone"),
    "copybook":    ("graphite", "inkwell", "sage"),
    "trace":       ("inkwell", "graphite", "ember"),
    "sample":      ("graphite", "inkwell", "moss"),
    "markup":      ("inkwell", "graphite", "midnight"),
}


def assign_themes(seed, names, cls="elegant"):
    """One theme per pin, no repeats, rotated by the font name so two fonts of
    the same shape still do not ship the same colour world — and a re-run of the
    same font lands identically."""
    rot = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    used, out = set(), {}
    # A class-owned world (vellum, gilded) never leaks into another class's
    # rotation; a brief can still ask for it explicitly.
    pool = [t for t in THEME_NAMES if THEMES[t].get("cls") in (None, cls)]
    for i, name in enumerate(names):
        pref = THEME_PREF[name]
        pref = pref[(rot + i) % len(pref):] + pref[:(rot + i) % len(pref)]
        # Take the first preferred world still free; if a pin's whole shortlist is
        # spent, borrow from any unused world rather than repeating one, which is
        # how five pins on six themes ship with no two alike.
        free = [t for t in pref if t not in used] or \
               [t for t in pool if t not in used]
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

    def fit(self, text, size, width, tracking=0.0, features=None):
        """Scale so the run lands exactly on `width`."""
        w = self.measure(text, size, tracking, features)
        return size * width / w if w else size

    def floor_to(self, text, size, width, tracking=0.0, features=None):
        """Step down whole 64ths until the run really measures `width` or less.

        Scaling by the exact ratio is not enough: `snap` makes the advance a step
        function of the size, so the corrected size usually lands in the bucket
        it came from and still measures over. Only dropping a bucket helps, and
        a row that measures over its own wrapper is a row that breaks in two.
        """
        while size > 0 and self.measure(text, size, tracking, features) > width:
            size = (math.floor(size * 64.0) - 1) / 64.0
        return max(size, 0.0)

    def draw(self, canvas, text, x, y, size, color, tracking=0.0, features=None):
        p, _ = self.path(text, size, tracking, features)
        canvas.save()
        canvas.translate(x, y)
        canvas.drawPath(p, paint(color))
        canvas.restore()
        return p

    def wrap(self, text, width, size, tracking=0.0, features=None):
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if self.measure(trial, size, tracking, features) <= width or not cur:
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

def ground(canvas, top, bottom, w=None, h=None):
    shader = skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, h or H)], [C(top), C(bottom)])
    p = paint()
    p.setShader(shader)
    canvas.drawRect(skia.Rect.MakeXYWH(0, 0, w or W, h or H), p)


def light_pool(canvas, cx, cy, r, rgb, strength=0.30, mode=skia.BlendMode.kScreen,
               w=None, h=None):
    shader = skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), r, [C(rgb, strength), C(rgb, 0.0)])
    p = paint()
    p.setShader(shader)
    p.setBlendMode(mode)
    canvas.drawRect(skia.Rect.MakeXYWH(0, 0, w or W, h or H), p)


def speckle(canvas, rgb, n=9000, seed=4, alpha=0.05, rad=1.5, w=None, h=None):
    rng = random.Random(seed)
    path = skia.Path()
    for _ in range(n):
        path.addCircle(rng.uniform(0, w or W), rng.uniform(0, h or H),
                       rng.uniform(rad * 0.4, rad))
    canvas.drawPath(path, paint(C(rgb, alpha)))


def dot_grid(canvas, rgb, step=26, rad=2.2, alpha=0.16, x0=None, y0=None, x1=None, y1=None):
    path = skia.Path()
    for y in range(y0, y1, step):
        for x in range(x0 if x0 is not None else M, x1, step):
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


def layout(t, text, width, size, tracking=0.0, leading=0.86, max_lines=8,
           features=None):
    """-> (lines, paths, step, ink_top, ink_bot, ink_w) or None if it can't be laid."""
    if not text.strip():
        return [], [], 0.0, 0.0, 0.0, 0.0
    lines = t.wrap(text, width, size, tracking, features)
    if len(lines) > max_lines:
        return None
    step = size * leading
    paths = [t.path(ln, size, tracking, features)[0] for ln in lines]
    tops = [p.getBounds().y() + i * step for i, p in enumerate(paths)]
    bots = [p.getBounds().bottom() + i * step for i, p in enumerate(paths)]
    return (lines, paths, step, min(tops), max(bots),
            max(p.getBounds().width() for p in paths))


def fit(t, text, box, hi, lo=8.0, tracking=0.0, leading=0.86, max_lines=8,
        features=None):
    """Largest size <= hi whose wrapped ink fits `box` in both axes (None if < lo)."""
    def fits(s):
        laid = layout(t, text, box.w, s, tracking, leading, max_lines, features)
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
        # A sub-sheet is a card of its own, so its checks have to be against the
        # card: sampling or verifying against the page would let type run off the
        # paper it is printed on and call that clean.
        self.w, self.h = surface.width(), surface.height()
        # The pin's own margin is 84 px on a 1000-px short edge, and every offset
        # in the shipped templates is counted from that. Carrying the ratio on the
        # sheet means a different frame scales instead of breaking, and at the
        # pin's 1000 px both of these are the numbers the globals already say.
        #
        # Two ratios, because a 2400x1600 sheet is not a pin scaled up: `scale`
        # sizes *type* (the short edge is what a letter has to be legible against)
        # and `vscale` moves things *down the page*, which has nothing to do with
        # the width. Using `scale` for both parked a specimen's footer 336 px up a
        # 1600-px sheet and let the last row of letters walk over it.
        self.m = int(round(min(self.w, self.h) * 0.084))
        self.scale = min(self.w, self.h) / 1000.0
        self.vscale = self.h / float(H)
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
        if min(xs) < 0 or max(xs) > self.w or min(ys) < 0 or max(ys) > self.h:
            self.problems.append(
                f"card at ({cx:.0f},{cy:.0f}) {angle:+.1f}deg runs off the canvas: "
                f"x {min(xs):.0f}..{max(xs):.0f}, y {min(ys):.0f}..{max(ys):.0f}")
        self.mark("card", Box(min(xs), min(ys), max(xs) - min(xs),
                              max(ys) - min(ys)), collide=False, bleed=True)
        self.problems += [f"card/{m}" for m in sub.verify()]
        self.notes += [f"card/{n}" for n in sub.notes]

    def _behind(self, box):
        """Median relative luminance of whatever is already painted in `box`.

        Measured off the sheet rather than assumed from the palette: a slot can
        land on a light pool, a colour band or a giant glyph, and a hand-picked
        ground colour is how you end up shipping white on white.
        """
        x0, y0 = max(0, int(box.x)), max(0, int(box.y))
        w, h = min(self.w - x0, int(box.w)), min(self.h - y0, int(box.h))
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
             hatch=None, glow=None, features=None):
        tracking = tracking + hi * track
        size = fit(t, string, box, hi, lo, tracking, leading, max_lines, features)
        if size is None:
            laid = layout(t, string, box.w, lo, tracking, leading, 999, features)
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
                                                  leading, max_lines, features)
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
            floor_laid = layout(t, string, box.w, min_read, tracking, leading, 999,
                                features)
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
            if not s.bleed and (b.x < 1 or b.y < 1 or b.r > self.w - 1
                                or b.b > self.h - 1):
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


def cls_names(cls):
    """Template names owned by one class, in design order."""
    return [n for n in CLASS_ORDERS[cls] if n in TEMPLATES]


def cls_names_spec(cls):
    """Specimen sheet names owned by one class, in design order."""
    return [n for n in SPECIMEN_ORDERS[cls] if n in TEMPLATES]


def template(name, blurb, cls="elegant", frame="pin"):
    def deco(fn):
        TEMPLATES[name] = (fn, blurb, cls, frame)
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
    w, h = sh.w // BG_SCALE, sh.h // BG_SCALE
    sub = skia.Surface.MakeRasterN32Premul(w, h)
    cv = sub.getCanvas()
    ground(cv, P["deep1"] if dark else P["paper1"],
           P["deep2"] if dark else P["paper2"], w, h)
    p = th["pool"] if pool is None else pool
    light_pool(cv, w * 0.72, h * (0.26 if dark else 0.18),
               int(round(900 * sh.scale)) // BG_SCALE, P["accent"],
               p if dark else p * 0.42,
               skia.BlendMode.kScreen if dark else skia.BlendMode.kMultiply, w, h)
    sh.cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(w, h),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kNone))
    t = th["tooth"] if tooth is None else tooth
    if t:
        speckle(sh.cv, P["glow"] if dark else P["ink"], n=t, seed=th["seed"],
                alpha=0.05, rad=1.4, w=sh.w, h=sh.h)
    if dev:
        device(sh, P, th["device"], dark)
    return dark


def device(sh, P, kind, dark):
    """The theme's graphic signature, under everything and quiet.

    Two pins in the same series may share a colour family; what stops them
    reading as duplicates is that one carries a dot field and the next carries
    rings. Alpha is deliberately near the noise floor — a device you notice is a
    device competing with the type.

    The steps here (`i * 46`, `90 + i * 74`, a 5-band run starting at `H*0.56`) are
    counted against a 1500-px page, so the anchors scale but the counts do not:
    a device that fits the pin walks off a landscape sheet. Specimens therefore
    paint `bg(..., dev=False)` and draw their own furniture.
    """
    Wd, Hd, Md = sh.w, sh.h, sh.m
    ink, mute = (P["glow"], mix(P["glow"], P["deep2"], 0.4)) if dark \
        else (P["ink"], mix(P["ink"], P["paper2"], 0.4))
    cv = sh.cv
    if kind == "dots":
        dot_grid(cv, mute, step=34, rad=2.0, alpha=0.20, x0=Md, y0=int(Hd * 0.62),
                 x1=Wd - Md, y1=int(Hd - 250))
    elif kind == "grid":
        for i in range(9):
            y = Hd * 0.60 + i * 46
            rule(cv, Md, y, Wd - Md, y, mute, 1.0, 0.16)
        for i in range(9):
            x = Md + i * ((Wd - 2 * Md) / 8)
            rule(cv, x, Hd * 0.60, x, Hd - 250, mute, 1.0, 0.16)
    elif kind == "bands":
        for i in range(5):
            y = Hd * 0.56 + i * 96
            q = paint(C(mute, 0.07))
            cv.drawRect(skia.Rect.MakeXYWH(0, y, Wd, 46), q)
    elif kind == "rings":
        q = paint(C(mute, 0.16), style=skia.Paint.kStroke_Style, width=1.6)
        for i in range(6):
            cv.drawCircle(Wd * 0.82, Hd * 0.80, 90 + i * 74, q)
    elif kind == "rays":
        q = paint(C(mute, 0.14), style=skia.Paint.kStroke_Style, width=2.2)
        for i in range(13):
            a = math.radians(-186 + i * 11)
            cv.drawLine(Wd * 0.14, Hd * 0.86,
                        Wd * 0.14 + math.cos(a) * 1500, Hd * 0.86 + math.sin(a) * 1500, q)
    elif kind == "hatch":
        # Manuscript ruling: faint lines the scribe pricked before he wrote, plus
        # the margin line they were pricked to. Under the type, never against it.
        y0, y1 = int(Hd * 0.16), int(Hd * 0.86)
        step = 46
        for i in range((y1 - y0) // step):
            rule(cv, Md * 0.66, y0 + i * step, Wd - Md * 0.66, y0 + i * step,
                 mute, 1.0, 0.11)
        rule(cv, Wd * 0.13, y0 - 40, Wd * 0.13, y1 + 40,
             P["accent"], 1.2, 0.14)
    elif kind == "lanes":
        # The track under the type: water-lane lines ruled the length of the page,
        # and the one centre line a rower is told to hold. Same near-silence
        # contract as `hatch` — a device you notice fights the headline.
        y0, y1 = int(Hd * 0.14), int(Hd - 250)
        step = 58
        for i in range((y1 - y0) // step):
            rule(cv, Md * 0.6, y0 + i * step, Wd - Md * 0.6, y0 + i * step,
                 mute, 1.0, 0.13)
        rule(cv, Wd * 0.5, y0 - 30, Wd * 0.5, y1, P["accent"], 1.4, 0.12)
    elif kind == "ruling":
        # A penman's band rather than `hatch`'s manuscript ruling: the lines come
        # in pairs, a waist and a hair above it, stacked down the page, because a
        # writing hand pricks *bands* — and the margin is two lines, the double
        # rule a practice sheet is folded to. No slant guides: `device()` cannot
        # see the face it is under, and a diagonal rule behind an upright letter
        # is an instruction the letter does not follow.
        y0, y1 = int(Hd * 0.16), int(Hd - 250)
        step = 92
        for i in range((y1 - y0) // step):
            y = y0 + i * step
            rule(cv, Md * 0.7, y, Wd - Md * 0.7, y, mute, 1.0, 0.10)
            rule(cv, Md * 0.7, y + 22, Wd - Md * 0.7, y + 22, mute, 1.0, 0.07)
        for dx in (0.0, 8.0):
            rule(cv, Wd * 0.11 + dx, y0 - 40, Wd * 0.11 + dx, y1 + 40,
                 P["accent"], 1.2, 0.12)


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


def eyebrow(sh, ctx, text, invert=False, y=None):
    """Small tracked title case over a hairline: the series' opening signature."""
    P, L = ctx["pal"], ctx["label"]
    ink, mute, _ = field(P, invert)
    text = tc(text)
    y = int(round(128 * sh.vscale)) if y is None else y
    hi, lo = 21 * sh.scale, 13 * sh.scale
    sh.text("eyebrow", L, text, Box(sh.m, y, sh.w - 2 * sh.m - 70,
                                    26 * sh.scale), hi=hi, lo=lo,
            color=mute, track=0.22, align="left", valign="top", min_read=lo)
    slot = _slot(sh, "eyebrow")
    if not slot:
        return y
    rule(sh.cv, sh.m, slot.ink.b + 16, sh.w - sh.m, slot.ink.b + 16, ink, 1.0, 0.30)
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
    x = x if x is not None else sh.w - int(round(34 * sh.scale))
    cy = cy if cy is not None else sh.h * 0.66
    size, track = 19 * sh.scale, 4.2 * sh.scale
    sh.cv.save()
    sh.cv.translate(x, cy)
    sh.cv.rotate(-90)
    label(sh.cv, L, text, 0, 0, size, mute, tracking=track, alpha=0.62)
    sh.cv.restore()
    sh.mark("edge", Box(x - 24 * sh.scale, cy - L.measure(text, size, track),
                        24 * sh.scale, L.measure(text, size, track)), collide=False)


def footer(sh, ctx, at="Set in", invert=False, exact=False):
    P, L = ctx["pal"], ctx["label"]
    ink, mute, _ = field(P, invert)
    rail = sh.h - int(round(236 * sh.vscale))
    rule(sh.cv, sh.m, rail, sh.m + int(round(96 * sh.scale)), rail, P["accent"], 3.0)
    # `exact` keeps the prefix as written. The specimen sheets report a range
    # ("Lowercase a–j"), and title-casing it into "A–J" claims letters the sheet
    # does not show; the pins' "Set in" ships as "Set In", so that stays.
    sh.text("name", L, f"{at} {tc(ctx['name'])}" if exact
            else tc(f"{at} {ctx['name']}"),
            Box(sh.m, sh.h - int(round(210 * sh.vscale)), sh.w - 2 * sh.m, 40),
            hi=27 * sh.scale, lo=18 * sh.scale, color=ink, track=0.16, align="left",
            valign="top", min_read=18 * sh.scale)
    if ctx["copy"].get("sub"):
        sh.text("sub", L, tc(ctx["copy"]["sub"]),
                Box(sh.m, sh.h - int(round(172 * sh.vscale)), sh.w - 2 * sh.m, 34),
                hi=20 * sh.scale, lo=14 * sh.scale, color=mute,
                track=0.16, align="left", valign="top", min_read=14 * sh.scale)


EDGE = lambda ctx: (f"{ctx['facts']['glyphs']} Glyphs"
                    if not ctx["facts"]["features"] else
                    f"{len(ctx['facts']['features'])} OpenType Features")


# --------------------------------------------------------------- shared parts


def usable(ctx, ch):
    return ch in ctx["chars"] and ch not in ctx["flagged"]


def fit_measure(T, text, width, hi, features=None):
    """Largest size whose INK — not merely its advance — reaches the measure.

    A swashy face can carry ink 10% past its advance width, so sizing by the
    advance leaves the last letters hanging outside the column it was set to.
    The closing clamp matters as much as the ink correction: HarfBuzz scales by
    64ths and the font cache rounds, so a size solved to land exactly on the
    measure can come back a fraction over it, and the wrapper silently breaks
    the row in two.
    """
    size = min(hi, T.fit(text, hi, width, features=features))
    if size <= 0:
        return 0.0
    ink_w = T.path(text, size, features=features)[0].getBounds().width()
    size *= min(1.0, width / ink_w) if ink_w > 0 else 1.0
    return T.floor_to(text, size, width, features=features)


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


GAPROW = 14.0


def row_metrics(T, chars, size, gap=GAPROW):
    """(advance total, ink width, ink height) for a spaced row at `size`."""
    paths = [T.path(c, size)[0] for c in chars]
    widths = [T.measure(c, size) for c in chars]
    edge, pen = 0.0, 0.0
    for p, adv in zip(paths, widths):
        edge = max(edge, pen + p.getBounds().right())
        pen += adv + gap
    ink_w = edge - paths[0].getBounds().left()
    ink_h = (max(p.getBounds().bottom() for p in paths)
             - min(p.getBounds().top() for p in paths))
    return sum(widths) + gap * (len(chars) - 1), ink_w, ink_h


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


def spec_grid(T, seqs, width, room, hi=420.0, lead_frac=0.30, gap=GAPROW):
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
            m = unit[row] = row_metrics(T, row, 100.0, gap)
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


def draw_rows(sh, T, sized, stage, paint_fn, prefix="row", lead_frac=0.10,
              gap=GAPROW, lead=None):
    """Draw rows sized by row_block, top-aligned inside the stage given.

    `lead` overrides the fraction-of-type gap: a block shorter than its stage
    should spend the difference *between* the lines, not leave it under them.
    """
    if not sized:
        return stage.y
    lead = sized[0][1] * lead_frac if lead is None else lead
    y = stage.y
    for i, (row, size, ih) in enumerate(sized):
        widths = [T.measure(c, size) for c in row]
        paths = [T.path(c, size)[0] for c in row]
        row_w = sum(widths) + gap * (len(row) - 1)
        x = stage.x + (stage.w - row_w) / 2
        top_i = min(p.getBounds().top() for p in paths)
        bot_i = max(p.getBounds().bottom() for p in paths)
        sh.cv.save()
        sh.cv.translate(x, y - top_i)
        for j, p in enumerate(paths):
            paint_fn(p, j, i)
            sh.cv.translate(widths[j] + gap, 0)
        sh.cv.restore()
        sh.mark(f"{prefix}{i}", Box(min(x + p.getBounds().left() for p in paths), y,
                                    max(p.getBounds().right() for p in paths)
                                    - min(x + p.getBounds().left() for p in paths),
                                    bot_i - top_i))
        y += (bot_i - top_i) + lead
    return y


def measure_rows(sh, T, P, seq, stage, prefix, hi=460.0, min_read=30.0,
                 fill=False, lead_frac=0.03, min_contrast=4.5, taper=False,
                 centre=False):
    """Set each row to the measure, stack them, scale the block to the stage.

    The shared spine of the funnel pins. `fill` lets the block *grow* to reach the
    bottom of the frame — a wall with air above and below is just a list — and
    then every row is re-clamped to the measure, because HarfBuzz rounds the size
    to 64ths and a row multiplied back up can overshoot by a hair and wrap in two.
    `taper` spends a height shortfall on the first row rather than on every row,
    which is what keeps a funnel's lower lines at the margin.
    `centre` splits the shortfall that survives the re-clamp above and below the
    block, instead of leaving it all under the last line.
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
    laid = []
    for s, size, _ih in sized:
        size = fit_measure(T, s, stage.w, size * k)
        laid.append((s, size, T.path(s, size)[0].getBounds().height()))
    # A row re-clamped to the measure can come in shorter than its share of the
    # stage, and then the whole shortfall pools under the last line — a block of
    # type sitting high on the page with air under it. `centre` splits it.
    block = sum(h for _s, _z, h in laid) + lead * (len(laid) - 1)
    y = stage.y + (max(0.0, (stage.h - block) / 2.0) if centre else 0.0)
    for i, (s, size, ih) in enumerate(laid):
        sh.text(f"{prefix}{i}", T, s, Box(stage.x, y, stage.w, ih + 2),
                hi=size, lo=size, leading=0.86, max_lines=1, min_read=min_read,
                valign="top", min_contrast=min_contrast,
                **tone(P, i))
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


def orn_triquetra(cv, cx, cy, s, rgb, alpha=1.0):
    """The trinity knot: three circles through each other's centres, ringed.

    Not filigree guessed at — this is the three-fold knot of the Book of Kells and
    the high crosses, and it is drawn as pure stroke so it takes the pin's own ink
    and survives the 200px thumbnail.
    """
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(2.0, s * 0.075))
    r = s * 0.56
    for i in range(3):
        a = math.tau * i / 3 - math.pi / 2
        cv.drawCircle(cx + math.cos(a) * r * 0.577, cy + math.sin(a) * r * 0.577,
                      r, q)
    cv.drawCircle(cx, cy, s, q)


def orn_fleur(cv, cx, cy, s, rgb, alpha=1.0):
    """Fleur-de-lis: a spear petal between two scrolling sides, banded and footed."""
    cv.save()
    cv.translate(cx, cy)
    q = paint(C(rgb, alpha))

    def leaf(side):
        p = skia.Path()
        p.moveTo(side * 0.10 * s, 0.16 * s)
        p.cubicTo(side * 0.60 * s, 0.12 * s, side * 0.80 * s, -0.26 * s,
                  side * 0.60 * s, -0.52 * s)
        p.cubicTo(side * 0.46 * s, -0.26 * s, side * 0.26 * s, -0.02 * s,
                  side * 0.12 * s, 0.06 * s)
        p.close()
        return p

    mid = skia.Path()
    mid.moveTo(0, -s)
    mid.cubicTo(0.30 * s, -0.54 * s, 0.22 * s, -0.04 * s, 0, 0.18 * s)
    mid.cubicTo(-0.22 * s, -0.04 * s, -0.30 * s, -0.54 * s, 0, -s)
    mid.close()
    foot = skia.Path()
    foot.moveTo(-0.12 * s, 0.34 * s)
    foot.lineTo(0.12 * s, 0.34 * s)
    foot.cubicTo(0.18 * s, 0.66 * s, 0.26 * s, 0.84 * s, 0.34 * s, 0.96 * s)
    foot.lineTo(-0.34 * s, 0.96 * s)
    foot.cubicTo(-0.26 * s, 0.84 * s, -0.18 * s, 0.66 * s, -0.12 * s, 0.34 * s)
    foot.close()
    cv.drawPath(mid, q)
    cv.drawPath(leaf(1), q)
    cv.drawPath(leaf(-1), q)
    cv.drawRect(skia.Rect.MakeXYWH(-0.30 * s, 0.16 * s, 0.60 * s, 0.18 * s), q)
    cv.drawPath(foot, q)
    cv.restore()


def orn_vine(cv, cx, cy, s, rgb, alpha=1.0, leaves=5, rot=0):
    """A marginal vine: a serpentine stem with pointed leaves alternating off it.

    This is the pen-work in the white margin of an insular page — the thing a frond
    (a straight feathered spine) does not do. The stem is one cubic; the leaves are
    sampled off it at parameter t so they sit ON the curve rather than beside it.
    """
    p0, p1, p2, p3 = (0, -s), (s * 0.36, -s * 0.34), (-s * 0.36, s * 0.34), (0, s)

    def at(t):
        u, iu = 1 - t, t
        return (iu ** 3 * p0[0] + 3 * iu ** 2 * t * p1[0] + 3 * iu * t ** 2 * p2[0] + t ** 3 * p3[0],
                iu ** 3 * p0[1] + 3 * iu ** 2 * t * p1[1] + 3 * iu * t ** 2 * p2[1] + t ** 3 * p3[1])

    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=max(1.6, s * 0.055))
    spine = skia.Path()
    spine.moveTo(*p0)
    spine.cubicTo(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
    cv.drawPath(spine, q)
    L = s * 0.46
    for i in range(leaves):
        t = (i + 0.5) / leaves
        px, py = at(t)
        side = 1 if i % 2 else -1
        lf = skia.Path()
        lf.moveTo(px, py)
        lf.quadTo(px + side * L * 0.52, py - L * 0.44, px + side * L, py - L * 0.02)
        lf.quadTo(px + side * L * 0.52, py + L * 0.34, px, py)
        cv.drawPath(lf, paint(C(rgb, alpha * 0.85)))
    cv.drawCircle(p3[0], p3[1], s * 0.075, paint(C(rgb, alpha)))
    cv.restore()


# ------------------------------------------------------- the angular set
#
# Every ornament above is curvy or organic — a shell, a frond, a vine. A sports
# pin drawn with a scallop is the same lie as a blackletter pin drawn with a
# sunburst, so the class gets its own three marks, all straight strokes, and all
# of them kept inside the ±s box draw_orn() registers: ink outside the mark is
# ink verify() cannot see.
def orn_chevron(cv, cx, cy, s, rgb, alpha=1.0, steps=3):
    """Speed arrows: nested V's pointing right, the marshal's chevron."""
    w, h = s * 0.42, s * 0.56
    p = skia.Path()
    spread = (s * 1.80 - w) / max(steps - 1, 1)
    for i in range(steps):
        x = cx - s * 0.90 + i * spread
        p.moveTo(x, cy - h)
        p.lineTo(x + w, cy)
        p.lineTo(x, cy + h)
    _stroke(cv, p, rgb, max(3.0, s * 0.13), alpha)


def orn_checker(cv, cx, cy, s, rgb, alpha=1.0, cells=4):
    """The finish board: half the cells filled, the ground colour doing the rest."""
    side = 2 * s / cells
    q = paint(C(rgb, alpha))
    for i in range(cells):
        for j in range(cells):
            if (i + j) % 2:
                continue
            cv.drawRect(skia.Rect.MakeXYWH(cx - s + i * side, cy - s + j * side,
                                           side, side), q)
    cv.drawRect(skia.Rect.MakeXYWH(cx - s, cy - s, 2 * s, 2 * s),
                paint(C(rgb, alpha * 0.7), style=skia.Paint.kStroke_Style,
                      width=max(1.6, s * 0.05)))


def orn_bracket(cv, cx, cy, s, rgb, alpha=1.0):
    """Two corner brackets facing each other — the timing gantry's sight mark.

    Drawn as a pair because an ornament placed from an ORN_SET has no idea which
    way up it is: two 180°-opposite corners read as one deliberate mark anywhere.
    """
    a, l = s * 0.80, s * 0.55
    p = skia.Path()
    for dx, dy in ((-1, -1), (1, 1)):
        x, y = cx + dx * a, cy + dy * a
        p.moveTo(x - dx * l, y)
        p.lineTo(x, y)
        p.lineTo(x, y + dy * l)
    _stroke(cv, p, rgb, max(2.5, s * 0.12), alpha)


def orn_nib(cv, cx, cy, s, rgb, alpha=1.0):
    """The pointed pen: a nib's outline, its slit and its vent hole.

    Stroked rather than filled, like the rest of the kit, so the slit reads without
    the ornament having to know what colour the ground behind it is.
    """
    w = max(2.2, s * 0.07)
    p = skia.Path()
    p.moveTo(cx, cy - s * 0.92)
    p.lineTo(cx + s * 0.34, cy + s * 0.06)
    p.lineTo(cx, cy + s * 0.86)
    p.lineTo(cx - s * 0.34, cy + s * 0.06)
    p.close()
    _stroke(cv, p, rgb, w, alpha)
    slit = skia.Path()
    slit.moveTo(cx, cy + s * 0.60)
    slit.lineTo(cx, cy - s * 0.30)
    _stroke(cv, slit, rgb, max(1.8, s * 0.05), alpha * 0.9)
    cv.drawCircle(cx, cy - s * 0.14, max(2.2, s * 0.10),
                  paint(C(rgb, alpha), style=skia.Paint.kStroke_Style,
                        width=max(1.6, s * 0.045)))


def orn_loop(cv, cx, cy, s, rgb, alpha=1.0):
    """One written flourish loop — the cross-over a hand makes at the end of a word.

    Deliberately monoline. The renderer can fake a pointed pen's thick and thin, and
    a flourish that fakes them contradicts whatever face it is drawn beside.
    """
    p = skia.Path()
    p.moveTo(cx - s * 0.88, cy + s * 0.52)
    p.cubicTo(cx - s * 0.30, cy - s * 0.92, cx + s * 0.82, cy - s * 0.42,
              cx + s * 0.20, cy + s * 0.18)
    p.cubicTo(cx - s * 0.42, cy + s * 0.78, cx + s * 0.30, cy + s * 0.86,
              cx + s * 0.86, cy + s * 0.10)
    _stroke(cv, p, rgb, max(2.4, s * 0.09), alpha)


ORNAMENTS = {"star": orn_star, "sun": orn_sun, "wave": orn_wave, "blob": orn_blob,
             "frond": orn_frond, "arc": orn_arc, "fan": orn_fan, "dots": orn_dots,
             "eye": orn_eye, "triquetra": orn_triquetra, "fleur": orn_fleur,
             "vine": orn_vine, "chevron": orn_chevron, "checker": orn_checker,
             "bracket": orn_bracket, "nib": orn_nib, "loop": orn_loop}


def draw_orn(sh, name, kind, cx, cy, s, rgb, alpha=1.0, collide=True, **kw):
    """Draw an ornament and register the box it owns, so verify() still rules."""
    ORNAMENTS.get(kind, orn_star)(sh.cv, cx, cy, s, rgb, alpha, **kw)
    sh.mark(f"orn-{name}", Box(cx - s, cy - s, 2 * s, 2 * s), collide=collide)


# ------------------------------------------------------------ the manuscript kit
#
# The blackletter class needs furniture, not just type: a band of interlace, the
# frame of an initial, the ruled frame of a folio. These are the same vector kit as the
# ornaments — beziers and rules, no images — with one trick the ornaments never
# needed: an interlace has to pass *over and under*, and a raster painter cannot
# do that with draw order alone. So each crossing cuts a notch of ground colour
# out of the strand that loses, then redraws the winner on top of the gap, which
# is precisely how a scribe solved it with two pens.

def _strips(sh, name, box, t=12.0, collide=True):
    """Register a frame as four edge strips, so the picture inside stays legal.

    One box for the whole frame would report every letter inside it as a collision
    with its own border; four strips say the truth — the ink is the border.
    """
    sh.mark(f"{name}-t", Box(box.x, box.y, box.w, t), collide=collide)
    sh.mark(f"{name}-b", Box(box.x, box.b - t, box.w, t), collide=collide)
    sh.mark(f"{name}-l", Box(box.x, box.y + t, t, box.h - 2 * t), collide=collide)
    sh.mark(f"{name}-r", Box(box.r - t, box.y + t, t, box.h - 2 * t), collide=collide)


def knot_band(sh, box, rgb, ground, waves=4, weight=None, alpha=1.0):
    """A plaited ribbon: two strands out of phase, crossing twice a wave.

    The strands are sines half a period apart, so every crossing is a coin toss the
    drawing has to settle. It settles alternately — strand A over at the even
    crossings, B over at the odd — which is the only rule that makes a braid read
    as woven rather than as two lines that happen to touch.
    """
    w = weight or max(6.0, box.h * 0.30)
    amp = max(2.0, (box.h - w) / 2.0)
    ink = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=w)
    # The casing is deliberately wider than the strand: the sliver of ground left
    # showing where a ribbon passes over another is what makes interlace read as
    # woven at feed size. Too wide and the crossings turn into cream blobs.
    cut = paint(C(ground, 1.0), style=skia.Paint.kStroke_Style, width=w * 1.30)
    mid = box.y + box.h / 2

    def strand(phase, t0=0.0, t1=1.0, n=200):
        p = skia.Path()
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            x = box.x + box.w * t
            y = mid + amp * math.sin(math.tau * waves * t + phase)
            p.lineTo(x, y) if i else p.moveTo(x, y)
        return p

    sh.cv.drawPath(strand(0.0), ink)
    sh.cv.drawPath(strand(math.pi, 0.0, 1.0), cut)
    sh.cv.drawPath(strand(math.pi), ink)
    win = (w * 2.2) / box.w
    for k in range(0, 2 * waves + 1, 2):
        tc_ = k / (2.0 * waves)
        t0, t1 = max(0.0, tc_ - win / 2), min(1.0, tc_ + win / 2)
        sh.cv.drawPath(strand(math.pi, t0, t1, 24), cut)
        sh.cv.drawPath(strand(0.0, t0, t1, 24), ink)
    sh.mark("knot", box)


def illum_box(sh, box, rgb, accent, alpha=1.0):
    """A drop-capital's frame: double rule, hairline inside, fleurons at the corners."""
    q = paint(C(rgb, alpha), style=skia.Paint.kStroke_Style,
              width=max(3.0, box.w * 0.014))
    sh.cv.drawRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h), q)
    i2 = 9.0
    sh.cv.drawRect(skia.Rect.MakeXYWH(box.x + i2, box.y + i2, box.w - 2 * i2,
                                      box.h - 2 * i2),
                   paint(C(rgb, alpha * 0.6), style=skia.Paint.kStroke_Style, width=1.4))
    s = max(13.0, box.w * 0.055)
    for j, (fx, fy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        draw_orn(sh, f"cb{j}", "fleur", box.x + i2 + s + fx * (box.w - 2 * (i2 + s)),
                 box.y + i2 + s + fy * (box.h - 2 * (i2 + s)), s, accent, 0.9,
                 collide=False)
    _strips(sh, "illum", box, t=max(10.0, box.w * 0.030))


def border_frame(sh, box, rgb, accent=None, alpha=0.85):
    """Folio rule: a hairline frame, a second line inside it, marks at the corners."""
    sh.cv.drawRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                   paint(C(rgb, alpha), style=skia.Paint.kStroke_Style, width=1.6))
    i2 = 7.0
    sh.cv.drawRect(skia.Rect.MakeXYWH(box.x + i2, box.y + i2, box.w - 2 * i2,
                                      box.h - 2 * i2),
                   paint(C(rgb, alpha * 0.45), style=skia.Paint.kStroke_Style,
                         width=1.0))
    for fx, fy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        sh.cv.drawCircle(box.x + fx * box.w, box.y + fy * box.h, 3.2,
                         paint(C(accent or rgb, alpha)))
    _strips(sh, "frame", box, t=8.0)


def crest_panel(sh, box, rgb, accent, alpha=0.9):
    """A club shield: chamfered shoulders, straight sides, a point at the foot.

    The one panel this class draws that nothing else in the set does, so its ink
    is registered as strips rather than one box — a letter inside a crest must not
    be reported as colliding with its own border.
    """
    x, y, w, h, r = box.x, box.y, box.w, box.h, box.r
    ch, sl = 14.0, h * 0.16          # the chamfer cut and the shoulder line

    def ring(ix, iy, iw, ih):
        ir, ib, cx = ix + iw, iy + ih, ix + iw / 2
        p = skia.Path()
        p.moveTo(ix + ch, iy)
        p.lineTo(ir - ch, iy)
        p.lineTo(ir, iy + sl)
        p.lineTo(ir, iy + ih * 0.62)
        p.lineTo(ir - iw * 0.20, ib - ih * 0.10)
        p.lineTo(cx, ib)
        p.lineTo(ix + iw * 0.20, ib - ih * 0.10)
        p.lineTo(ix, iy + ih * 0.62)
        p.lineTo(ix, iy + sl)
        p.close()
        return p

    i2 = 11.0
    _stroke(sh.cv, ring(x, y, w, h), rgb, max(3.0, w * 0.012), alpha)
    _stroke(sh.cv, ring(x + i2, y + i2, w - 2 * i2, h - 2 * i2), rgb,
            max(1.4, w * 0.005), alpha * 0.55)
    for fx in (0.30, 0.50, 0.70):
        sh.cv.drawCircle(x + w * fx, y + sl * 0.5, max(2.6, w * 0.010),
                         paint(C(accent, alpha)))
    # The ink is the head edge and the two straight sides — there is no bottom
    # rule to collide with, and marking the foot of the box would report every
    # letter in the field as overlapping a line that was never drawn there.
    t = 12.0
    sh.mark("crest-t", Box(x, y, w, t))
    for sx in (x, r - t):
        sh.mark(f"crest-{'l' if sx == x else 'r'}",
                Box(sx, y + t, t, h * 0.62 - 2 * t))


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


# =============================================== the blackletter / celtic class
#
# The elegant set says "type foundry"; this class says "scriptorium" — and says it
# with the same machinery: the same ground, the same colour ladder, the same fitted
# slots and footer rail, plus furniture from the manuscript tradition. Interlace,
# the ruled initial box, rubrication in the scribe's red, pricked ruling lines.
# Type stays the subject in all five; the drawings frame it, never compete with it.


@template("initials", "the illuminated initial: the face's own first letter ruled and gilded, its name beside it",
          cls="blackletter")
def t_initials(sh, ctx):
    """A manuscript page opens with an initial, so this pin is that opening.

    The letter is the face's own — the first one its headline can actually draw —
    set inside double rules with fleurons at the corners, and pen-work climbing the
    empty foot of the name column beside it, which is where a scribe tied an initial
    to the page. The name answers across the column in the next rungs of the ladder,
    and the headline runs under both. Nothing here is a texture: the box, the fringe
    and the rubric red are all drawn, so they cost nothing at the byte level.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    ch = next((c for c in line if c.isalpha() and usable(ctx, c)), "")
    if not ch:
        sh.problems.append("initials: the face draws no letter of this headline")
        return
    y0 = eyebrow(sh, ctx, "Illuminated Initial") + 34
    side = min(500.0, (W - 2 * M) * 0.575)
    ib = Box(M, y0, side, side)
    illum_box(sh, ib, ink, P["accent"])
    sh.text("cap", T, ch, Box(ib.x + 48, ib.y + 42, ib.w - 96, ib.h - 84),
            hi=560, lo=70, max_lines=1, min_read=120, **tone(P, 1))
    col = Box(ib.r + 76, ib.y + 8, W - M - ib.r - 76, ib.h - 16)
    name = shout(ctx, clean(ctx, ctx["name"])).strip() or line
    measure_rows(sh, T, P, pack_lines(name.split(), 2), col, "nm", hi=210,
                 min_read=34, lead_frac=0.07)
    # Marginal pen-work in the foot of the name column: a one-word name leaves the
    # column half empty, and a dead band is a composition bug, not a margin.
    nm = _slot(sh, "nm0")
    free = (nm.ink.b if nm else col.y) + 30
    if col.b - free > 150:
        for i in range(2):
            draw_orn(sh, f"vine{i}", "vine", col.x + col.w * (0.34 + 0.30 * i),
                     free + 74 + i * 96, 88, P["accent2"], 0.6,
                     rot=-12 + 24 * i, collide=False)
    stage = Box(M, ib.b + 34, W - 2 * M, H - ib.b - 282)
    measure_rows(sh, T, P, pack_lines(line.split(), 3), stage, "line", hi=150,
                 min_read=32, fill=True, lead_frac=0.05, centre=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("knotband", "the character set funnelled under a band of interlace, inside a folio frame",
          cls="blackletter")
def t_knotband(sh, ctx):
    """The alphabet as a woven band wears it.

    Same funnel the elegant `set` uses — one pair, two, three, each row set to the
    measure — because the funnel is the shape that keeps the first line enormous.
    What changes is the frame: a plaited ribbon across the head of the page, a
    folio rule round the whole block, and a triquetra where the two meet. The braid
    is drawn with real over-and-under, so the pin reads as made rather than tiled.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.08)
    ink, mute, _ = field(P)
    ground = P["deep1"] if dark else P["paper1"]
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    los = [c for c in ascii_lowercase if usable(ctx, c)]
    n = min(6, len(ups), len(los))
    if n < 3:
        sh.problems.append("knotband: the face carries too few letters to pair up")
        return
    pairs = [f"{ups[i]}{los[i]}" for i in range(n)]
    rows, i = [], 0
    for want in (1, 2, 3):
        rows.append(" ".join(pairs[i:i + want]))
        i += want
    rows = [r for r in rows if r]

    y0 = eyebrow(sh, ctx, "Interlaced Set") + 32
    band = Box(M + 12, y0, W - 2 * (M + 12), 56)
    knot_band(sh, band, ink, ground, waves=5)
    frame = Box(M - 12, band.b + 26, W - 2 * (M - 12), H - band.b - 292)
    border_frame(sh, frame, mute, P["accent"])
    draw_orn(sh, "kn", "triquetra", frame.x + 44, frame.y - 4, 26, P["accent"], 0.95,
             collide=False)
    stage = Box(frame.x + 34, frame.y + 30, frame.w - 68, frame.h - 62)
    measure_rows(sh, T, P, rows, stage, "pair", hi=880, min_read=40,
                 lead_frac=0.045, taper=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=f"{len(ups)} Upper \u00b7 {len(los)} Lower \u00b7")


@template("scriptorium", "the desk: words, digits and oddments ruled like a pricked manuscript page",
          cls="blackletter")
def t_scriptorium(sh, ctx):
    """A wall of the face, on the lines a scribe pricked before he wrote.

    The elegant `wall` fills the frame with everything the face can set; here the
    same block sits on faint ruling, inside a ruled frame, with the knot at the
    foot of the page where a colophon goes. The ruling is a device, not a grid: it
    is drawn under the type at near the noise floor, so it reads as prepared skin
    rather than as a table.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"], dev=False)
    device(sh, P, "hatch", dark)
    ink, mute, _ = field(P)
    words = [w for w in shout(ctx, clean(ctx, ctx["copy"]["line"])).split() if w]
    digits = "".join(c for c in "0123456789" if usable(ctx, c) and c not in ctx["flagged"])
    punct = " ".join(c for c in "&@?!%*()" if usable(ctx, c) and c not in ctx["flagged"])
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
        sh.problems.append("scriptorium: nothing to set — the face carries no letters or digits")
        return

    y0 = eyebrow(sh, ctx, "Scriptorium") + 30
    frame = Box(M - 14, y0, W - 2 * (M - 14), H - y0 - 250)
    border_frame(sh, frame, mute, P["accent"])
    stage = Box(frame.x + 40, frame.y + 24, frame.w - 56, frame.h - 132)
    measure_rows(sh, T, P, seq, stage, "row", hi=520, min_read=30, fill=True,
                 lead_frac=0.028)
    draw_orn(sh, "seal", "triquetra", frame.x + frame.w - 66, frame.b - 62, 46,
             P["accent"], 0.95)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("folio", "the rubricated line: the first word drawn in the scribe's red, vines above and below",
          cls="blackletter")
def t_folio(sh, ctx):
    """What the font says, set like a page and corrected by hand.

    The block is the elegant `phrase` spine — a short line of copy, one rung of the
    ladder per line, artwork reserved in bands above and below so the type shrinks
    rather than walking over it. The move that makes it a manuscript is the
    rubric: the first word is drawn a second time in the red pen, over the ink it
    already sits on, which is literally what a rubricator did. Its contrast is
    re-measured against the pixels under it, so the red can never go muddy.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"])
    ink, mute, _ = field(P)
    acc, red = P["accent"], P["accent2"]
    # The furniture is the class, not the colour world: a shared theme may bring a
    # nautical art set with it, and a scallop shell on a manuscript page is a lie.
    art = ORN_SETS["foil" if dark else "knot"]
    y0 = eyebrow(sh, ctx, "Rubricated") + 30

    top = Box(M, y0, W - 2 * M, 150)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["top"]):
        s = min(s, top.h / 2.2)  # a band that shrinks carries smaller furniture
        draw_orn(sh, f"t{i}", kind, top.x + top.w * fx_,
                 top.y + max(s, min(top.h * fy, top.h - s)), s,
                 acc if i % 2 else ink, alpha)
    band = Box(M, H - 372, W - 2 * M, 120)
    src = clean(ctx, ctx["copy"]["line"]).strip()
    if 0 < len(src.split()) < 3:
        sh.notes.append(f"folio: {len(src.split())} words is a label, not a phrase "
                        f"— write three or four")
    words = [w for w in shout(ctx, src or ctx["name"]).split() if w]
    if not words:
        sh.problems.append("folio: the line has no words this face can draw")
        return
    # Never more lines than half the words: a scribe who left one word standing
    # alone at the foot of the block was out of room, not being stylish.
    lines = pack_lines(words, min(4, max(2, len(words) // 2)))
    stage = Box(M + 20, top.b + 22, W - 2 * (M + 20), band.y - top.b - 96)
    measure_rows(sh, T, P, lines, stage, "folio", hi=340, min_read=44, fill=True,
                 lead_frac=0.05, centre=True)

    first = _slot(sh, "folio0")
    head = lines[0].split()[0] if first and first.size else ""
    if head:
        # Placed off the line's BASELINE, not its ink top: the tallest ascender in
        # the row is usually further back in the sentence, and anchoring to the top
        # floats the rubric word a few points above the word it is redrawing.
        size = first.size
        lb = T.path(lines[0], size)[0].getBounds()
        p, _w = T.path(head, size)
        b = p.getBounds()
        red = readable(sh._behind(first.ink) or lum(P["paper1"]), red, 4.5)
        sh.cv.save()
        sh.cv.translate(first.ink.x - lb.left(), first.ink.y - lb.top())
        sh.cv.drawPath(p, paint(C(red, 1.0)))
        sh.cv.restore()

    rule(sh.cv, W / 2 - 90, band.y - 34, W / 2 + 90, band.y - 34, acc, 2.4, 0.9)
    draw_orn(sh, "fl", "fleur", W / 2, band.y - 34, 24, acc, 1.0, collide=False)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["bottom"]):
        s = min(s, band.h / 2.2)
        draw_orn(sh, f"b{i}", kind, M + (W - 2 * M) * fx_,
                 band.y + max(s, min(band.h * fy, band.h - s)), s,
                 red if i % 2 else acc, alpha)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("carol", "the specimen sheet with its alternates: the same word plain and shaped by the face's own OpenType features",
          cls="blackletter")
def t_carol(sh, ctx):
    """The foundry spec sheet, with the one line a blackletter buyer came for.

    Name, purpose, then the alphabet at the size the page can carry — the shape of
    `full_stack`, because a specimen pin is saved for the character set whatever
    class it is in. What this adds is the alternate showcase: the same word drawn
    twice, once with the default shaping and once with the feature tags the brief
    asked for, at one shared size so the difference is the letterforms and nothing
    else. It only appears when the face actually ships the features and the brief
    actually names them — an empty promise of an ornament is worse than none.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    facts = ctx["facts"]
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    los = [c for c in ascii_lowercase if usable(ctx, c)]
    ftrs = ctx.get("ftrs") or {}

    feat = (" + ".join(sorted(ftrs)).upper() + " Alternates" if ftrs else
            (" ".join(sorted(facts["features"])[:2]) if facts["features"] else
             f"{facts['glyphs']} Glyphs"))
    sh.text("hdr-l", L, f"({feat})", Box(M, 62, 460, 24), hi=20, lo=12,
            color=ink, track=0.14, align="left", valign="top", min_read=12)
    sh.text("hdr-r", L, "(OTF / TTF / WOFF)", Box(W - M - 460, 62, 460, 24), hi=20,
            lo=12, color=ink, track=0.14, align="right", valign="top", min_read=12)

    name = shout(ctx, clean(ctx, ctx["name"])).strip()
    lines = pack_lines(name.split() or shout(ctx, clean(ctx, ctx["copy"]["line"])).split(), 2)
    y = 124
    for i, ln in enumerate(lines):
        size = fit_measure(T, ln, measure, 300.0)
        if size <= 0:
            continue
        h = T.path(ln, size)[0].getBounds().height()
        sh.text(f"n{i}", T, ln, Box(M, y, measure, h + 2), hi=size, lo=size,
                leading=0.86, max_lines=1, min_read=40, valign="top",
                min_contrast=5.0 if i else 6.5,
                glow=(mix(rung(P, i), P["accent"], 0.4), 0.055, 0.34),
                **tone(P, 1 if i else 0))
        y += h + 26
    y += 14
    tag = tc(clean(ctx, ctx["copy"].get("over") or f"{facts['glyphs']}-glyph display"))
    sh.text("tag", L, tag, Box(M, y, measure, 36), hi=30, lo=14, color=ink,
            track=0.30, align="center", valign="top", min_read=14)
    y += 42

    sample = shout(ctx, clean(ctx, ctx["copy"].get("word") or ctx["name"])).strip()
    if ftrs and facts["features"] and sample:
        w = measure - 132
        hi = 150.0
        size = min(fit_measure(T, sample, w, hi),
                   fit_measure(T, sample, w, hi, ftrs))
        if size > 0:
            # Both lines in the same ink, deliberately: the point of the pair is
            # that the letterforms differ, and walking the colour ladder between
            # them makes the buyer compare the colours instead of the glyphs.
            for i, (cap, feats) in enumerate((("Default", None),
                                              (" + ".join(sorted(ftrs)).upper(), ftrs))):
                sh.text(f"alt{i}", T, sample, Box(M + 132, y, w, size * 1.22),
                        hi=size, lo=size, max_lines=1, align="left", valign="top",
                        min_read=28, features=feats, color=ink)
                label(sh.cv, L, cap, M, y + size * 0.72, 17, mute, tracking=3.2,
                      alpha=0.85)
                y += size * 1.34
            rule(sh.cv, M, y + 4, W - M, y + 4, ink, 1.0, 0.30)
            y += 22
    else:
        sh.text("copy", L, tc(ctx["copy"]["line"]), Box(M + 60, y, measure - 120, 96),
                hi=21, lo=13, color=mute, align="center", valign="top",
                leading=1.42, max_lines=3, min_read=13)
        slot = _slot(sh, "copy")
        y = (slot.ink.b if slot else y + 96) + 26

    rule(sh.cv, M, y, W - M, y, ink, 1.4, 0.5)
    draw_orn(sh, "div0", "triquetra", W / 2, y, 15, P["accent"], 1.0, collide=False)
    y += 20
    sh.text("sec-l", L, "Full Character Set", Box(M, y, 400, 24), hi=20, lo=12,
            color=ink, track=0.16, align="left", valign="top", min_read=12)
    sh.text("sec-r", L, f"{len(ups)} Upper \u00b7 {len(los)} Lower",
            Box(W - M - 400, y, 400, 24), hi=20, lo=12, color=ink, track=0.16,
            align="right", valign="top", min_read=12)

    rows = spec_grid(T, [ups, los], measure, max(H - 124 - (y + 46), 160.0))
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


# ==================================================== the tech / sports class
#
# Elegant says "type foundry", blackletter says "scriptorium"; this class says
# "timing gantry" — one race meet seen five ways: its badge, its number, its start
# list, its photo finish, its board. Every object is a hard-edged panel or a rule,
# because a soft ornament on a hard monoline is the same lie as a scallop shell on
# a manuscript page. These faces are sold as all-caps faces, so the set is an
# all-caps world by fact: no template here asks the page to show a lowercase it
# cannot honestly deliver.


@template("crest", "the club badge: the face's own initial in a pointed shield, wordmark bar across it",
          cls="sports")
def t_crest(sh, ctx):
    """A crest is what this lettering is bought for, so one pin simply is one.

    The shield carries the face's simplest capital, the bar across its point carries
    a single word of it, and the headline runs underneath — the three things a buyer
    actually does with a sports face (logo, wordmark, poster line) in one image. The
    bar is painted before the word is fitted, so the contrast guard is measuring the
    bar and not the page behind it.
    """
    P, T = ctx["pal"], ctx["display"]
    facts = ctx["facts"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    words = [w for w in line.split() if w]
    ch = facts["simple"] if usable(ctx, facts["simple"]) else ""
    ch = ch or next((c for c in line if c.isalpha() and usable(ctx, c)), "")
    if not ch or not words:
        sh.problems.append("crest: nothing for the shield and bar to draw")
        return
    y0 = eyebrow(sh, ctx, "Club Crest") + 34

    pb = Box(296, y0, 408, 372)
    crest_panel(sh, pb, ink, P["accent"])
    sh.text("cap", T, ch, Box(pb.x + 34, pb.y + 42, pb.w - 68, 210),
            hi=300, lo=70, max_lines=1, min_read=110, **tone(P, 1))
    for i, cx in enumerate((150, 850)):
        draw_orn(sh, f"sh{i}", "chevron", cx, pb.y + 110, 58,
                 P["accent"] if i else ink, 0.95, collide=False)

    bar = Box(196, pb.y + 272, 608, 86)
    sh.cv.drawRect(skia.Rect.MakeXYWH(bar.x, bar.y, bar.w, bar.h), paint(C(rung(P, 1))))
    # One word only: a bar this high holds about twelve letters before the fit has
    # to shrink the type under what a thumbnail can read. clean() has already
    # dropped anything the face cannot draw.
    named = [w for w in tc(clean(ctx, ctx["name"])).split() if len(w) <= 12]
    asked = tc(clean(ctx, ctx["copy"].get("word") or "")).split()
    token = (asked or named or words)[0]
    sh.text("word", T, token, Box(bar.x + 30, bar.y + 10, bar.w - 60, bar.h - 20),
            hi=88, lo=14, track=0.10, valign="top", min_read=30,
            color=P["deep1"] if dark else P["paper1"])

    stage = Box(M, bar.b + 22, W - 2 * M, 1242 - bar.b - 22)
    measure_rows(sh, T, P, pack_lines(words, 3), stage, "crest", hi=190,
                 min_read=40, fill=True, lead_frac=0.05, centre=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("bib", "the race number: four figures pinned to a ruled card, the meet line under them",
          cls="sports")
def t_bib(sh, ctx):
    """The number on a vest is the purest test of a sports face there is.

    Readable across a gymnasium, from one glyph to the next, with nothing around it.
    So the card carries figures at the largest size the frame can hold and the
    headline takes the foot of the page. The figures come from the face's own usable
    set — a demo-stamped or placeholder digit is not a specimen, so a four-figure
    number is built from what the font actually draws rather than written down.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    facts = ctx["facts"]
    dark = bg(sh, P, ctx["th"], pool=0.12)
    ink, mute, _ = field(P)
    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    words = [w for w in line.split() if w]
    if not words:
        sh.problems.append("bib: the line has no words this face can draw")
        return
    digits = "".join(c for c in "0123456789" if usable(ctx, c))
    num = digits[:4] if len(digits) >= 4 else words[0]
    y0 = eyebrow(sh, ctx, "Race Number") + 34

    frame = Box(M + 40, y0, W - 2 * (M + 40), 500)
    border_frame(sh, frame, ink, P["accent"])
    numslot = sh.text("num", T, tc(num), Box(frame.x + 34, frame.y + 34,
                                             frame.w - 68, 330),
                      hi=440, lo=60, max_lines=1, min_read=140, **tone(P, 1))
    tag = tc(clean(ctx, ctx["copy"].get("over") or ctx["copy"].get("sub")
                   or f"{facts['glyphs']}-glyph display"))
    y = _slot(sh, "num").ink.b + 26 if numslot else frame.y + 380
    sh.text("meet", L, tag, Box(frame.x + 34, y, frame.w - 68, 44), hi=30, lo=14,
            color=mute, track=0.30, align="center", valign="top")

    stage = Box(M, frame.b + 36, W - 2 * M, 1242 - frame.b - 36)
    measure_rows(sh, T, P, pack_lines(words, 3), stage, "bib", hi=200,
                 min_read=42, fill=True, lead_frac=0.05, centre=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("lane", "the start list: every capital the face carries, at one size, standing on its own rule",
          cls="sports")
def t_lane(sh, ctx):
    """The spacing proof a monoline has to pass.

    A team sheet is twenty-six names in one weight, and that is the whole pin: one
    size for every letter, each row standing on a hairline, two colours alternating
    like lanes. `full_stack` sizes its grid to fit the page; this one is bound by the
    measure, which is why the same face stands a third larger here — and why the
    sequence is the capitals alone. A row of letters that already touches both
    margins cannot be grown by taking the copy out of the way.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], dev=False)
    device(sh, P, "lanes", dark)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    if len(ups) < 8:
        sh.problems.append("lane: the face carries too few capitals to line up")
        return
    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    y0 = eyebrow(sh, ctx, "Start List") + 30
    # The alphabet is the subject, so the line is allowed to go small here in a way
    # it is not allowed to go small on `crest` or `bib`: three lines inside a fixed
    # head, and a floor that stops a 100-character brief from failing the pin.
    sh.text("head", T, line, Box(M, y0, measure, 78), hi=66, lo=16, max_lines=3,
            min_read=18, valign="top", **tone(P, 0))
    slot = _slot(sh, "head")
    y = (slot.ink.b if slot else y0 + 78) + 46

    rows = spec_grid(T, [ups], measure, max(1242 - (y + 40), 200.0))
    if not rows:
        sh.problems.append("lane: no packing of these capitals fits the page")
        return
    tall = sum(h for _r, _s, h in rows) + rows[0][1] * 0.30 * max(len(rows) - 1, 0)
    ground = sh._behind(Box(M, y + 40, measure, min(tall, 1242 - y - 40))) \
        or lum(P["deep2"])
    crisp = [readable(ground, rung(P, i), 4.5) for i in range(2)]

    def paint_lane(p, j, i):
        sh.cv.drawPath(p, paint(C(crisp[i % 2], 1.0)))

    draw_rows(sh, T, rows, Box(M, y + 40, measure, 1), paint_lane, "lane",
              lead_frac=0.30)
    for i in range(len(rows)):
        s = _slot(sh, f"lane{i}")
        if s:
            rule(sh.cv, M, s.ink.b + 12, W - M, s.ink.b + 12, mute, 1.2, 0.55)
    edge_type(sh, ctx, f"{len(ups)} Caps")
    footer(sh, ctx, at=f"{len(ups)} Caps \u00b7")


@template("finish", "the photo finish: a phrase under the beam, its first line run back once in motion",
          cls="sports")
def t_finish(sh, ctx):
    """What the face does to a sentence, and what the beam does to the face.

    The elegant `phrase` spine — copy as the subject, artwork banded above and below
    — with the timing gantry's own furniture, and one move that only a photo finish
    makes: the beam is ruled *before* the type, so the letters cross it rather than
    sit beside it, and the first line is drawn a second time in stripes twenty-four
    pixels back. That is the rubricator's trick from `folio` turned sideways — a
    restatement of the same ink, not a second thought.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"])
    ink, mute, _ = field(P)
    acc = P["accent"]
    art = ORN_SETS["gantry" if dark else "sector"]
    y0 = eyebrow(sh, ctx, "Photo Finish") + 30

    top = Box(M, y0, W - 2 * M, 150)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["top"]):
        s = min(s, top.h / 2.2)  # a band that shrinks carries smaller furniture
        draw_orn(sh, f"t{i}", kind, top.x + top.w * fx_,
                 top.y + max(s, min(top.h * fy, top.h - s)), s,
                 acc if i % 2 else ink, alpha)
    # One spine, not a stripe: the beam is the gantry's centre line, so it runs
    # through the middle ornament of both bands and the type crosses it.
    beam = W * 0.5
    rule(sh.cv, beam, top.b + 12, beam, H - 372 - 12, acc, 2.4, 0.8)
    band = Box(M, H - 372, W - 2 * M, 120)
    src = clean(ctx, ctx["copy"]["line"]).strip()
    if 0 < len(src.split()) < 3:
        sh.notes.append(f"finish: {len(src.split())} words is a label, not a phrase "
                        f"— write three or four")
    words = [w for w in shout(ctx, src or ctx["name"]).split() if w]
    if not words:
        sh.problems.append("finish: the line has no words this face can draw")
        return
    # One line shorter than `phrase`'s cut: a photo finish is a stack of lines
    # crossing the beam, and the extra break is what lets the block stand at full
    # height instead of pooling under a measure-bound row.
    lines = pack_lines(words, min(4, max(2, len(words) - 1)))
    stage = Box(M + 20, top.b + 24, W - 2 * (M + 20), band.y - top.b - 104)
    measure_rows(sh, T, P, lines, stage, "fin", hi=300, min_read=44, fill=True,
                 lead_frac=0.05, centre=True)

    f0 = _slot(sh, "fin0")
    if f0 and f0.size:
        p, _w = T.path(lines[0], f0.size)
        b = p.getBounds()
        sh.cv.save()
        sh.cv.translate(f0.ink.x - b.left() - 30, f0.ink.y - b.top())
        hatched(sh.cv, p, P["accent2"], gap=8, weight=2.4, angle=0, alpha=0.62)
        sh.cv.restore()
        sh.mark("echo", Box(f0.ink.x - 30, f0.ink.y, f0.ink.w, f0.ink.h),
                collide=False)

    for i, (kind, fx_, fy, s, alpha) in enumerate(art["bottom"]):
        s = min(s, band.h / 2.2)
        draw_orn(sh, f"b{i}", kind, M + (W - 2 * M) * fx_,
                 band.y + max(s, min(band.h * fy, band.h - s)), s,
                 P["accent2"] if i % 2 else acc, alpha)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("timer", "the timing board: name, tag, then caps, figures and punctuation in one matrix on a dot field",
          cls="sports")
def t_timer(sh, ctx):
    """Everything the face can send, at one size, the way a gantry board sends it.

    The specimen shape this class shares with `full_stack`, and the place the two
    part company: `full_stack` refuses digits and punctuation because they cost the
    letters their size (`wall` spends them on phrase rows instead), and it walks a
    colour ladder under a bloom that reads as light. A timing board has no light —
    it has pixels. So the rungs stay flat, the ground is a dot matrix, and the set
    is the whole working alphabet: capitals, the figures the face actually draws,
    and the punctuation, which is what a buyer typing a scoreboard checks first.

    The count line says `Caps`, not `Upper / Lower`. This face is sold as an
    all-caps face, and a pin that claims twenty-six lowercase letters it cannot
    show is the one thing a specimen sheet must never do.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10, dev=False)
    device(sh, P, "dots", dark)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    facts = ctx["facts"]
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    digits = "".join(c for c in "0123456789" if usable(ctx, c))
    punct = [c for c in "&@?!%*()" if usable(ctx, c)]
    if len(ups) < 8:
        sh.problems.append("timer: the face carries too few capitals to board out")
        return

    sh.text("hdr-l", L, f"({facts['glyphs']} Glyphs)", Box(M, 62, 460, 24), hi=20,
            lo=12, color=ink, track=0.14, align="left", valign="top", min_read=12)
    sh.text("hdr-r", L, "(OTF / TTF / WOFF)", Box(W - M - 460, 62, 460, 24), hi=20,
            lo=12, color=ink, track=0.14, align="right", valign="top", min_read=12)

    name = shout(ctx, clean(ctx, ctx["name"])).strip()
    lines = pack_lines(name.split() or
                       shout(ctx, clean(ctx, ctx["copy"]["line"])).split(), 2)
    y = 124
    for i, ln in enumerate(lines):
        size = fit_measure(T, ln, measure, 340.0)
        if size <= 0:
            continue
        h = T.path(ln, size)[0].getBounds().height()
        sh.text(f"n{i}", T, ln, Box(M, y, measure, h + 2), hi=size, lo=size,
                leading=0.86, max_lines=1, min_read=40, valign="top",
                min_contrast=5.0 if i else 6.5, **tone(P, 1 if i else 0))
        y += h + 26
    y += 14
    tag = tc(clean(ctx, ctx["copy"].get("over") or f"{facts['glyphs']}-glyph display"))
    sh.text("tag", L, tag, Box(M, y, measure, 36), hi=30, lo=14, color=ink,
            track=0.30, align="center", valign="top", min_read=14)
    y += 42

    rule(sh.cv, M, y, W - M, y, ink, 1.4, 0.5)
    rule(sh.cv, W / 2 - 34, y, W / 2 + 34, y, P["accent"], 3.4)
    y += 20
    sh.text("sec-l", L, "Full Character Set", Box(M, y, 400, 24), hi=20, lo=12,
            color=ink, track=0.16, align="left", valign="top", min_read=12)
    claim = f"{len(ups)} Caps" + (f" \u00b7 {len(digits)} Figures" if digits else "")
    sh.text("sec-r", L, claim, Box(W - M - 400, y, 400, 24), hi=20, lo=12,
            color=ink, track=0.16, align="right", valign="top", min_read=12)

    seqs = [ups] + ([list(digits)] if len(digits) >= 4 else []) \
               + ([punct] if len(punct) >= 4 else [])
    rows = spec_grid(T, seqs, measure, max(1242 - (y + 46), 160.0))
    if not rows:
        sh.problems.append("timer: no packing of this character set fits the board")
        return
    tall = (sum(h for _r, _s, h in rows)
            + rows[0][1] * 0.30 * max(len(rows) - 1, 0))
    ground = (sh._behind(Box(M, y + 46, measure, min(tall, 1242 - y - 46)))
              or lum(P["deep2"]))
    crisp = [readable(ground, rung(P, i), 4.5) for i in range(len(P["tone"]))]

    def paint_cell(p, j, i):
        sh.cv.drawPath(p, paint(C(crisp[i % len(crisp)], 1.0)))

    draw_rows(sh, T, rows, Box(M, y + 46, measure, 1), paint_cell, "chars",
              lead_frac=0.30)
    edge_type(sh, ctx, claim)
    footer(sh, ctx, at=f"{claim} \u00b7")


# ------------------------------------------------------------------ the script class
#
# Handwriting is the one class whose evidence is a *line*: a script is taught on a
# ruled band, drilled a letter at a time, traced before it is inked, pinned up when
# it is finished and proofed against the whole alphabet. So the five objects are the
# penman's bench, and the shared truth across all five is that the letters are set
# standing on something. No template here *depends* on a gradient, and that is
# load-bearing rather than stylistic: `script` is in FLOWING, which replaces the
# ladder's third rung with a flat mix, but under `--stress` the same binary can
# classify otherwise and the gradient returns on its own and stripes the joins. So
# the lettering itself is always one colour — `tone(P, 0)`, `rung()`, or a flat mix —
# and only the headline rows walk the shared ladder the other classes walk.
# Every metric is measured from the binary: a cap height is 0.715em on one script
# and 1.015em on another.


@template("guide", "the specimen word on a band ruled at the face's own cap, waist and descender",
          cls="script")
def t_guide(sh, ctx):
    """A script you cannot rule is a script you cannot learn, so this pin rules it.

    The three faint lines are not a frame and not a constant: they are the ink
    bounds of the face's own capital, minuscule and descender at the size the word
    is actually set at, and they run past the word on both sides so they read as
    the page's ruling rather than a box drawn around one letter. The baseline is
    the heaviest line on the page because it is the only one a hand cannot miss.

    Flat rung 0, and no ghost. `hero` owns the giant initial behind the type; a
    band with a ghost letter in it is a hero with lines under it.
    """
    P, T = ctx["pal"], ctx["display"]
    facts = ctx["facts"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    asked = tc(clean(ctx, ctx["copy"].get("word") or "")).split()
    word = " ".join(asked or tc(clean(ctx, ctx["name"])).split()[:1])
    if not word:
        sh.problems.append("guide: nothing for the band to hold")
        return
    y0 = eyebrow(sh, ctx, "Penman's Band")
    BASE = y0 + 268.0

    size = fit_measure(T, word, measure - 60, 430.0)
    b100 = T.path(word, 100.0)[0].getBounds()
    if b100.height() > 0:
        size = min(size, 100.0 * 560.0 / b100.height())
    # The band has a ceiling as well as a floor: a script's ascender overshoots its
    # own cap, so the word's tallest ink is capped against the eyebrow rule above
    # and the descender room below, both measured from the binary.
    if b100.top() < 0:
        size = min(size, 100.0 * (BASE - y0 - 26) / -b100.top())
    if size < 90:
        sh.problems.append(f"guide: the word only reaches {size:.0f}px on the band — "
                           f"that is a caption, not a specimen")
        return

    def band(chances):
        """Ink bounds of the first glyph of this class the face really carries."""
        ch = next((c for c in chances if c and usable(ctx, c)), "")
        return T.path(ch, size)[0].getBounds() if ch else None

    capb = band([facts.get("simple"), "H", "A", "E", "O"])
    xhb = band(["x", "o", "e", "a", "n"])
    dscb = band(["g", "j", "p", "q", "y"])
    wb = T.path(word, size)[0].getBounds()
    L, R = M * 0.55, W - M * 0.55
    rule(sh.cv, L, BASE, R, BASE, ink, 1.6, 0.62)
    if capb:
        rule(sh.cv, L, BASE + capb.top(), R, BASE + capb.top(), mute, 1.2, 0.40)
    if xhb:
        rule(sh.cv, L, BASE + xhb.top(), R, BASE + xhb.top(), mute, 1.2, 0.55)
    if dscb:
        rule(sh.cv, L, BASE + dscb.bottom(), R, BASE + dscb.bottom(), mute, 1.2, 0.40)
    low = BASE + max(wb.bottom(), dscb.bottom() if dscb else 0.0)
    draw_orn(sh, "nib", "nib", R - 26, BASE - 12, 24, P["accent"], 0.95,
             collide=False)
    # `sh.text` puts the ink's top at the box's top when valign is "top", and the
    # path's bounds are measured from the baseline, so this box is what lands the
    # baseline on BASE exactly — the rules above are drawn from the same bounds.
    sh.text("word", T, word, Box(M, BASE + wb.top(), measure, wb.height() + 2),
            hi=size, lo=size, max_lines=1, valign="top", min_read=60,
            **tone(P, 0))

    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    words = [w for w in line.split() if w]
    if words:
        stage = Box(M, low + 50, measure, 1242 - low - 50)
        measure_rows(sh, T, P, pack_lines(words, 3), stage, "guid", hi=200,
                     min_read=40, fill=True, lead_frac=0.05, centre=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("copybook", "the drill page: one letter five times on a rule, the copies fading as the hand goes",
          cls="script")
def t_copybook(sh, ctx):
    """The way a script is taught, which is also the way it is proved twice.

    One model letter at full ink and four attempts after it walking toward the
    ground — which is what a practice sheet actually looks like — and every row
    standing on its own baseline, so the descenders cross the line rather than
    dodge it. The letters come from the brief's own word when it supplies four of
    them, because a drill page for a face called Silken should be practising Silken.

    `readable()` is load-bearing here, not tidy: `draw_rows` paints raw paths, so
    without it the fourth and fifth copies would simply vanish into the paper.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    word = tc(clean(ctx, ctx["copy"].get("word") or ctx["name"]))
    mine = list(dict.fromkeys(c for c in word.lower()
                             if c.isalpha() and usable(ctx, c)))
    los = [c for c in ascii_lowercase if usable(ctx, c)]
    letters = (mine if len(mine) >= 4 else los)[:6]
    if len(letters) < 4:
        sh.problems.append("copybook: the face carries too few letters to drill")
        return
    y0 = eyebrow(sh, ctx, "Copybook")
    y = y0 + 46
    stage = Box(M, y, measure, 1242 - y - 96)

    reps = [[c] * 5 for c in letters]
    size = min(measure / max(row_metrics(T, r, 100.0)[:2]) * 100.0 for r in reps)
    size = min(size, 220.0)
    lead = size * 0.30
    block = sum(row_metrics(T, r, size)[2] for r in reps) + lead * (len(reps) - 1)
    if block:
        size *= min(1.0, stage.h / block)
        lead = size * 0.30
        sized = [(r, size, row_metrics(T, r, size)[2]) for r in reps]
    else:
        sized = []
    if not sized or size < 60:
        sh.problems.append("copybook: these letters will not stand five across a page")
        return
    tall = sum(h for _r, _s, h in sized) + lead * (len(sized) - 1)
    ground = sh._behind(Box(M, y, measure, min(tall, stage.h))) or lum(P["deep2"])
    base = P["deep2"] if dark else P["paper2"]

    def paint_drill(p, j, i):
        sh.cv.drawPath(p, paint(C(readable(ground, mix(ink, base, j * 0.13), 4.5),
                                  1.0)))

    draw_rows(sh, T, sized, Box(M, y, measure, 1), paint_drill, "copy",
              lead_frac=0.30)
    for i, (row, s, _h) in enumerate(sized):
        slot = _slot(sh, f"copy{i}")
        if not slot:
            continue
        top_i = min(T.path(c, s)[0].getBounds().top() for c in row)
        rule(sh.cv, M * 0.6, slot.ink.y - top_i, W - M * 0.6, slot.ink.y - top_i,
             mute, 1.2, 0.5)
    edge_type(sh, ctx, f"{len(letters)} Letters")
    footer(sh, ctx, at=f"{len(letters)} Letters \u00b7")


@template("trace", "the logotype inked over its own offset outline, the pencil line left showing",
          cls="script")
def t_trace(sh, ctx):
    """The one pin that shows how the lettering was made, by leaving the making on.

    A signwriter traces the word first and the pencil stays visible at one edge of
    the ink. So the outline is drawn at an offset that scales with the word — never
    a constant, or a small word would carry a heavy ghost — and the inked pass goes
    over it. `folio` rubricates the same ink in red and `finish` runs its echo back
    in stripes; both restate the lettering in its own place. This one restates it
    beside it, which is the only move here that shows a hand working rather than a
    face printed.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = bg(sh, P, ctx["th"], pool=0.12)
    ink, mute, _ = field(P)
    acc = P["accent"]
    art = ORN_SETS["penwork" if dark else "flourish"]
    measure = W - 2 * M
    asked = tc(clean(ctx, ctx["copy"].get("word") or "")).split()
    word = " ".join(asked or tc(clean(ctx, ctx["name"])).split()[:2])
    if not word:
        sh.problems.append("trace: no word to lay the pencil under")
        return
    y0 = eyebrow(sh, ctx, "Trace-Through")
    size = fit_measure(T, word, measure - 60, 340.0)
    if size < 60:
        sh.problems.append(f"trace: the word only reaches {size:.0f}px")
        return
    wp = T.path(word, size)[0]
    b = wp.getBounds()
    bw, bh = b.width(), b.height()
    ix = M + (measure - bw) / 2
    iy = y0 + 210 - bh / 2
    d = size * 0.05
    sh.cv.save()
    sh.cv.translate(ix + d - b.left(), iy + d - b.top())
    wireframe(sh.cv, wp, acc, weight=max(1.6, size * 0.006), alpha=0.75)
    sh.cv.restore()
    sh.mark("pencil", Box(ix + d, iy + d, bw, bh), collide=False)
    sh.text("word", T, word, Box(M, iy, measure, bh + 2), hi=size, lo=size,
            max_lines=1, valign="top", min_read=60, **tone(P, 0))

    src = clean(ctx, ctx["copy"]["line"]).strip()
    words = [w for w in shout(ctx, src or ctx["name"]).split() if w]
    band = Box(M, H - 372, W - 2 * M, 120)
    slot = _slot(sh, "word")
    if slot and words:
        stage = Box(M, slot.ink.b + 58, measure, band.y - slot.ink.b - 118)
        measure_rows(sh, T, P, pack_lines(words, 3), stage, "trac", hi=170,
                     min_read=40, fill=True, lead_frac=0.05, centre=True)
    for i, (kind, fx_, fy, s, alpha) in enumerate(art["bottom"]):
        s = min(s, band.h / 2.2)
        draw_orn(sh, f"b{i}", kind, M + measure * fx_,
                 band.y + max(s, min(band.h * fy, band.h - s)), s,
                 P["accent2"] if i % 2 else acc, alpha)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("sample", "the lettered quote on a piece of paper, tipped and taped at the corners",
          cls="script")
def t_sample(sh, ctx):
    """The buyer's actual job: words as artwork, on a surface, in one ink.

    The card is a sheet of its own, so the type inside it gets the same fit,
    contrast and off-canvas checks as type on the page — which is the only reason a
    rotated card can be trusted at all. It is painted flat rather than with `bg()`
    or `device()`, because both are written against the full frame and would sample
    off the paper; the ruling they leave behind belongs to the bench, not the card.

    The ladder inside the card is a single ink. A pinned sample is one pen on one
    sheet, and four colours on a piece of paper is a poster, not a sample.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10)
    line = shout(ctx, clean(ctx, ctx["copy"]["line"] or ctx["name"])).strip()
    words = [w for w in line.split() if w]
    if not words:
        sh.problems.append("sample: nothing to letter on the card")
        return
    eyebrow(sh, ctx, "Pinned Sample")
    CW, CH = 620.0, 800.0
    sub = sh.sub(CW, CH)
    sub.cv.drawRect(skia.Rect.MakeXYWH(0, 0, CW, CH), paint(C(P["paper1"])))
    Pc = dict(P, tone=[dict(color=P["ink"])] * 4)
    kin = P["ink"]
    kmut = mix(P["ink"], P["paper2"], 0.34)
    over = tc(clean(ctx, ctx["copy"].get("over") or "")) or tc(clean(ctx, ctx["name"]))

    sub.text("k-ov", L, over, Box(44, 56, CW - 88, 28), hi=24, lo=13, color=kmut,
             track=0.26, align="left", valign="top", min_read=13)
    stage = Box(44, 118, CW - 88, 452)
    measure_rows(sub, T, Pc, pack_lines(words, min(4, max(2, len(words)))), stage,
                 "card", hi=200, min_read=38, fill=True, lead_frac=0.05,
                 centre=True)
    rule(sub.cv, 44, 612, CW - 44, 612, kin, 1.2, 0.45)
    sig = tc(clean(ctx, ctx["name"])).split()[0]
    sub.text("k-sig", T, sig, Box(44, 636, CW - 88, 110), hi=96, lo=22, color=kmut,
             max_lines=1, align="left", valign="top", min_read=22)
    sh.paste(sub, 500, 712, angle=-2.2)

    sh.cv.save()
    sh.cv.translate(500, 712)
    sh.cv.rotate(-2.2)
    tape = mix(P["paper2"], P["deep2"], 0.5)
    for sx in (-1, 1):
        sh.cv.save()
        sh.cv.translate(sx * CW / 2, -CH / 2 + 8)
        sh.cv.rotate(38 * sx)
        sh.cv.drawRect(skia.Rect.MakeXYWH(-66, -17, 132, 34), paint(C(tape, 0.34)))
        sh.cv.restore()
    sh.cv.restore()
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


@template("markup", "the marked-up proof: the name, the tag, then every letter joined and standing on its own rule",
          cls="script")
def t_markup(sh, ctx):
    """The specimen sheet this class has to earn: the whole set, written, not spelled out.

    `full_stack` and `timer` both lay the character set out as cells, because a
    monoline is one letter at a time. A script is not — its alphabet only exists as
    a run, so the rows here are *strings*, sized as strings, at one pen size, and
    they start at the left margin because writing starts at the left margin. That
    rules out `spec_grid`, which sizes a row on its advance total including the gap
    it inserts between cells: nine joined capitals measure two-thirds of the
    column that way and the line stops short of the margin it was cut to.

    Flat rungs and no halo. The bloom is `full_stack`'s signature, and a proof is
    read for faults under the flattest light it can be given.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    facts = ctx["facts"]
    dark = bg(sh, P, ctx["th"], pool=0.12)
    ink, mute, _ = field(P)
    measure = W - 2 * M
    ups = [c for c in ascii_uppercase if usable(ctx, c)]
    los = [c for c in ascii_lowercase if usable(ctx, c)]
    digits = "".join(c for c in "0123456789" if usable(ctx, c))
    punct = "".join(c for c in "&@?!'.,;-" if usable(ctx, c))
    if len(ups) + len(los) < 12:
        sh.problems.append("markup: the face carries too few letters to proof out")
        return

    y = eyebrow(sh, ctx, "Marked-Up Proof") + 36
    for i, ln in enumerate(pack_lines(shout(ctx, clean(ctx, ctx["name"])).split(), 2)):
        ns = fit_measure(T, ln, measure, 190.0)
        if ns <= 0:
            continue
        hb = T.path(ln, ns)[0].getBounds()
        sh.text(f"n{i}", T, ln, Box(M, y, measure, hb.height() + 2), hi=ns, lo=ns,
                max_lines=1, align="left", valign="top", min_read=44, **tone(P, i))
        y += hb.height() + 18
    tag = tc(clean(ctx, ctx["copy"].get("over") or ctx["copy"].get("sub")
                   or f"{facts['glyphs']}-glyph script"))
    sh.text("tag", L, tag, Box(M, y + 6, measure, 30), hi=28, lo=13, color=mute,
            track=0.28, align="left", valign="top", min_read=13)
    y += 52
    rule(sh.cv, M, y, W - M, y, ink, 1.3, 0.45)
    rule(sh.cv, M, y, M + 76, y, P["accent"], 3.2)
    y += 34

    room = max(1242 - y, 200.0)

    def rows_for(k):
        out = []
        for src in (los, ups):
            if not src:
                continue
            q = math.ceil(len(src) / math.ceil(len(src) / k))
            out += ["".join(src[i:i + q]) for i in range(0, len(src), q)]
        if len(digits) >= 6:
            out.append(digits)
        if len(punct) >= 4:
            out.append(punct)
        return out

    best = None
    for k in range(3, 15):
        cand = rows_for(k)
        sz = min(fit_measure(T, r, measure, 240.0) for r in cand)
        if sz <= 0:
            continue
        block = sum(T.path(r, sz)[0].getBounds().height() for r in cand) \
            + sz * 0.30 * (len(cand) - 1)
        kk = min(1.0, room / block) if block else 1.0
        if best is None or sz * kk > best[0]:
            best = (sz * kk, cand)
    if not best:
        sh.problems.append("markup: no packing of this alphabet fits the proof")
        return
    size, seqs = best
    laid = []
    for r in seqs:
        s = fit_measure(T, r, measure, size)
        laid.append((r, s, T.path(r, s)[0].getBounds()))
    tall = sum(b.height() for _r, _s, b in laid) + size * 0.30 * (len(laid) - 1)
    ground = sh._behind(Box(M, y, measure, min(tall, room))) or lum(P["deep2"])
    crisp = [readable(ground, rung(P, i), 4.5) for i in range(len(P["tone"]))]

    yy = y
    for i, (r, s, b) in enumerate(laid):
        sh.text(f"r{i}", T, r, Box(M, yy, measure, b.height() + 2), hi=s, lo=s,
                max_lines=1, align="left", valign="top", min_read=40,
                color=crisp[i % len(crisp)])
        rule(sh.cv, M, yy - b.top(), W - M, yy - b.top(), mute, 1.2, 0.5)
        yy += b.height() + size * 0.30
    claim = f"{len(ups)} Upper \u00b7 {len(los)} Lower"
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=f"{claim} \u00b7")


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
    # Manuscript sets, one per class theme. The knot world is interlace and
    # fleurons; the foil world is gilding — starry, sharper, fewer bigger marks.
    "knot": dict(top=[("fleur", 0.12, 0.50, 96, 0.95), ("triquetra", 0.50, 0.44, 76, 1.0),
                      ("fleur", 0.88, 0.50, 96, 0.95)],
                 bottom=[("vine", 0.14, 0.46, 104, 0.9), ("triquetra", 0.50, 0.50, 64, 0.95),
                         ("vine", 0.86, 0.46, 104, 0.9)]),
    "foil": dict(top=[("star", 0.20, 0.40, 54, 1.0), ("fleur", 0.50, 0.48, 110, 1.0),
                      ("star", 0.80, 0.40, 54, 1.0)],
                 bottom=[("triquetra", 0.24, 0.50, 72, 0.95), ("fan", 0.52, 0.54, 92, 0.85),
                         ("triquetra", 0.80, 0.50, 72, 0.95)]),
    # The two sports sets, chosen by class and never by colour world: everything
    # straight-edged, one big mark per band so a 300px thumbnail still reads.
    "gantry": dict(top=[("chevron", 0.18, 0.50, 88, 1.0),
                        ("bracket", 0.50, 0.50, 64, 0.95),
                        ("chevron", 0.82, 0.50, 88, 1.0)],
                   bottom=[("checker", 0.20, 0.50, 58, 1.0),
                           ("bracket", 0.50, 0.48, 64, 0.9),
                           ("checker", 0.84, 0.50, 58, 1.0)]),
    "sector": dict(top=[("bracket", 0.16, 0.50, 60, 0.95),
                        ("chevron", 0.50, 0.50, 92, 1.0),
                        ("bracket", 0.84, 0.50, 60, 0.95)],
                   bottom=[("chevron", 0.22, 0.50, 76, 0.9),
                           ("checker", 0.50, 0.50, 62, 1.0),
                           ("chevron", 0.86, 0.50, 76, 0.9)]),
    # The two bench sets, again chosen by class rather than world. `loop` is wide and
    # `nib` is narrow, so they are spaced to alternate rather than to match; `vine`
    # doubles as the flourish it actually is — a looped pen stroke, unlike a frond on
    # a race bib.
    "penwork": dict(top=[("loop", 0.18, 0.50, 84, 0.95),
                         ("nib", 0.50, 0.46, 66, 1.0),
                         ("loop", 0.82, 0.50, 84, 0.95)],
                    bottom=[("nib", 0.24, 0.50, 58, 0.95),
                            ("vine", 0.50, 0.48, 96, 0.9),
                            ("nib", 0.76, 0.50, 58, 0.95)]),
    "flourish": dict(top=[("vine", 0.16, 0.46, 96, 0.9),
                          ("loop", 0.50, 0.50, 92, 1.0),
                          ("vine", 0.84, 0.46, 96, 0.9)],
                     bottom=[("loop", 0.26, 0.50, 78, 0.9),
                             ("nib", 0.52, 0.46, 62, 0.95),
                             ("loop", 0.78, 0.50, 78, 0.9)]),
}


# ================================================================ the specimen set
#
# The same four classes, on the second surface the marketplace asks for: the two
# factual sheets that replace `render_font_specimens.py`. Nothing here is authored
# copy — a specimen says what the face can draw and nothing else — so a body needs
# three things and no more: the glyphs, the class's own furniture, and the frame it
# was registered on. Which is why every one of them reads `sh.w / sh.h / sh.m /
# sh.scale` and not the module globals: the pin templates keep their literals
# because a 1000x1500 page is what they were tuned against, and a sheet that is
# 2400 px wide is not that page scaled up, it is a different composition.


def specimen(cls, sheet, blurb):
    """Register one body at both specimen frames.

    The sheet is the design; the ratio is only the paper it gets printed on. Both
    names come from one function, so a class cannot ship a landscape sheet whose
    square twin drifted — and if a render ever shows the square genuinely wanting a
    different row plan, that is when the body splits, not before.
    """
    def deco(fn):
        for frame in SPECIMEN_FRAMES:
            TEMPLATES[f"{cls}_{sheet}_{frame}"] = (fn, blurb, cls, frame)
        return fn
    return deco


# A–J, not A–Z. Ten letters at the measure is one enormous legible sample;
# twenty-six is a completeness proof the buyer cannot read at thumbnail size, and
# the completeness proof already exists — it is the character count in the footer.
LETTERS_UP = "ABCDEFGHIJ"
LETTERS_LOW = "abcdefghij"
FIGURES = "0123456789"
PUNCT = "! ? . , : ; / & @ # % + - = * ( ) < > { }"


def spec_span(shown, full, label):
    """The sample's own label, plus whichever characters the face left out.

    A count on a specimen sheet is a claim about the font: "10 caps" reads as
    though the alphabet stopped at J, when it is only what this sheet chose to
    show. So the footer names the range it sampled and spends its one number on
    the gap a buyer would otherwise have to discover alone.
    """
    miss = [c for c in full if c not in shown]
    return label if not miss else f"{label} less {' '.join(miss)}"


def spec_bg(sh, ctx, **kw):
    """The ground under a specimen: flat, untextured, and wearing no device.

    `tooth=0` is parity with the Pillow sheets these replace, not thrift — a
    specimen is the one image in the package that has to be *right*, and 9000
    circles of noise over a 2400x1600 field costs near-entropy bytes to say
    nothing. `dev=False` is the other half: `device()` counts its steps against a
    1500-px page, so its bands walk off a landscape sheet. The furniture a sheet
    needs is drawn by the body, in the box it actually has.
    """
    return bg(sh, ctx["pal"], ctx["th"], dev=False, tooth=0, **kw)


def spec_head(sh, ctx, label):
    """The tracked caption and its hairline — every sheet opens the same way."""
    return eyebrow(sh, ctx, label) + int(round(40 * sh.vscale))


def spec_floor(sh):
    """The line nothing is printed below — `footer()` counts its rails from here."""
    return int(round(sh.h - 292 * sh.vscale))


def spec_stage(sh, y0):
    """The band a sheet sets its letters in: from under the head to the footer.

    The 292/1500 reserve is the pin's own footer footprint, so it is counted the
    same way `footer()` counts its rails — down from the bottom edge, by the
    height ratio. Two rules for the same strip of paper is how a row of letters
    ends up printed over the name line.
    """
    return Box(sh.m, y0, sh.w - 2 * sh.m, spec_floor(sh) - y0)


def spec_orn_band(sh, ctx, y0, part="top"):
    """The band of ornaments the sheet's own theme carries, at the head or the foot.

    Each theme carries an ornament set, so one helper gives elegant the arch and the
    star, sports the chevrons and script the nibs and loops — the sheet is wearing
    the same art its pins wear, which is what makes the pair visibly one font. `set`
    draws it to break up a funnel; a sheet draws it as its heading. Returns the
    bottom of the ink, because an ornament that hangs below its box takes the first
    row's air.
    """
    P = ctx["pal"]
    ink, _mute, _ = field(P)
    art = ORN_SETS[ctx["th"]["art"]]
    band = Box(sh.m, y0, sh.w - 2 * sh.m, int(round(76 * sh.vscale)))
    bot = band.b
    for i, (kind, fx_, fy, s, alpha) in enumerate(art[part]):
        # 0.46 of the size a pin gives the same ornament: on a pin the band
        # shares the page with a headline, on a sheet the type is the subject.
        s = s * 0.46 * sh.scale
        cy = band.y + max(s * 0.6, min(band.h * fy, band.h - s * 0.6))
        draw_orn(sh, f"orn{i}", kind, band.x + band.w * fx_, cy, s,
                 P["accent"] if i % 2 else ink, alpha * 0.75)
        bot = max(bot, cy + s)
    return bot


def spec_letters(sh, ctx):
    """The A–J and a–j the face actually carries, as (caps, lowercase, claim).

    A face that is missing half of a–j is a fact about the face, so it says so in
    the footer rather than shipping a row with holes in it; a caps-only face gets
    the capitals twice, which is the honest specimen of it.
    """
    T = ctx["display"]
    ups = [c for c in LETTERS_UP if usable(ctx, c)]
    los = [c for c in LETTERS_LOW if usable(ctx, c)]
    if len(ups) < 4 and len(los) < 4:
        sh.problems.append("letters: the face carries too few of A–J or a–j "
                           "to set a specimen")
        return None
    up = spec_span(ups, LETTERS_UP, "Uppercase A\u2013J")
    low = spec_span(los, LETTERS_LOW, "Lowercase a\u2013j")
    if not los:
        return ups, ups, f"{up} \u00b7 uppercase only \u00b7"
    if not ups:
        return los, los, f"{low} \u00b7 lowercase only \u00b7"
    # Unicameral faces — a lot of brush and chiselled display work — ship a
    # lowercase that is the capital copied, sometimes with a different sidebearing
    # but the same outline. Two rows then look like a rendering bug; the label is
    # what makes them a fact.
    def shape(ch):
        p = T.path(ch, 100)[0]
        pts = [(q.x(), q.y()) for q in p.getPoints()]
        if not pts:
            return None
        x0, y0 = pts[0]
        # Relative to the pen's first point: a sidebearing is a translation.
        return [int(v) for v in p.getVerbs()], [(x - x0, y - y0)
                                               for x, y in pts]

    def copied(a, b):
        # 100 px is drawn on a 1/64-pixel grid, so two copies of one outline can
        # still differ by that much; 0.05 is that noise and nothing visible.
        if not a or not b or a[0] != b[0] or len(a[1]) != len(b[1]):
            return False
        return all(abs(x - u) <= 0.05 and abs(y - v) <= 0.05
                   for (x, y), (u, v) in zip(a[1], b[1]))

    if all(copied(shape(c), shape(c.upper())) for c in los):
        return ups, los, f"{up} \u00b7 {low} drawn as capitals \u00b7"
    return ups, los, f"{up} \u00b7 {low} \u00b7"


def spec_figures(sh, ctx):
    """The figures and marks the face actually carries, as (figures, marks, claim).

    A face missing digits is a fact about the face: it is reported as a problem and
    the sheet still shows what survives, because a short row nobody flagged is how a
    broken font ships. The claim names the ranges rather than counting them — see
    `spec_span`.
    """
    all_marks = PUNCT.split()
    figs = [c for c in FIGURES if usable(ctx, c)]
    marks = [c for c in all_marks if usable(ctx, c)]
    if len(figs) < 10:
        sh.problems.append(f"numerals: the face carries {len(figs)} of the ten figures")
    if len(marks) < 4:
        sh.problems.append(f"numerals: only {len(marks)} punctuation marks to show")
    if not figs and not marks:
        sh.problems.append("numerals: nothing to set \u2014 no figures and no marks")
        return None
    return (figs, marks,
            f"{spec_span(figs, FIGURES, 'Figures 0\u20139')} \u00b7 "
            f"{spec_span(marks, all_marks, 'Punctuation')} \u00b7")


def spec_spread(stage, n, ink, design):
    """Where a block shorter than its stage goes: (lead, air above the first row).

    The leftover goes into the leads, up to a point: rows standing down the page
    is what a specimen looks like, rows huddled under the heading with all the air
    beneath them is what a list looks like. Past a little over twice the design
    leading the rest is split above and below the block instead, because two rows
    of letters with a page's worth of nothing between them is not a set, it is two
    rows that gave up on each other.
    """
    if n <= 1:
        return 0.0, max(0.0, stage.h - ink) / 2
    lead = min(max(design, (stage.h - ink) / (n - 1)), design * 2.2)
    return lead, max(0.0, (stage.h - ink - lead * (n - 1)) / 2)


def spec_char_block(sh, ctx, seqs, stage):
    """The characters, at one point size, standing down the whole stage.

    One size across every row is the factual claim the sheet exists to make: fit
    each row to the measure on its own and a face whose capitals are wide comes
    back with lowercase 40% larger than the uppercase above it, which is not the
    font's proportion but the layout's. Same for four marks against ten figures.
    So `spec_grid` sets the block — one size, the letters shared out evenly, the
    largest the page can carry — and the gap between characters scales with the
    sheet, because `GAPROW`'s 14 px is a pin's air and a landscape sheet's
    collision.

    The grid cannot grow the type past the measure, so on a square sheet the ten
    figures bind the width and the block comes out shorter than its stage. `spec_spread`
    decides where the difference goes.
    """
    P, T = ctx["pal"], ctx["display"]
    gap = GAPROW * sh.scale
    rows = spec_grid(T, seqs, stage.w, stage.h, hi=900.0 * sh.scale,
                     lead_frac=0.30, gap=gap)
    if not rows:
        return 0
    ground = (sh._behind(Box(stage.x, stage.y, stage.w, min(stage.h, 300.0)))
              or lum(P["deep2"]))
    q = paint(C(readable(ground, rung(P, 0), 4.5), 1.0))
    ink = sum(h for _r, _s, h in rows)
    lead, spare = spec_spread(stage, len(rows), ink, rows[0][1] * 0.30)
    draw_rows(sh, T, rows, Box(stage.x, stage.y + spare, stage.w, stage.h),
              lambda p, j, i: sh.cv.drawPath(p, q), "row", gap=gap, lead=lead)
    return len(rows)


@specimen("elegant", "letters",
          "A–J and a–j at one size, under the theme's ornament band")
def s_letters_elegant(sh, ctx):
    """`set`'s grammar without the funnel: the ornament band, then the letters.

    The elegant pin funnels 1/2/3 pairs because it has to sell a *feeling* about
    the alphabet. A factual sheet does not: every letter stands at the same size,
    and how many share a row is whatever the sheet can carry big.
    """
    spec_bg(sh, ctx, pool=0.08)
    built = spec_letters(sh, ctx)
    if not built:
        return
    ups, los, claim = built
    y0 = spec_head(sh, ctx, "Character Set")
    y1 = spec_orn_band(sh, ctx, y0) + int(round(14 * sh.vscale))
    if not spec_char_block(sh, ctx, [ups, los], spec_stage(sh, y1)):
        sh.problems.append("letters: no row of A\u2013J can be set to this measure")
        return
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


@specimen("elegant", "numerals",
          "the ten figures and the marks, one size, on the same band")
def s_numerals_elegant(sh, ctx):
    """The same band again, so the two sheets are visibly one pair."""
    spec_bg(sh, ctx, pool=0.08)
    built = spec_figures(sh, ctx)
    if not built:
        return
    figs, marks, claim = built
    y0 = spec_head(sh, ctx, "Figures & Punctuation")
    y1 = spec_orn_band(sh, ctx, y0) + int(round(14 * sh.vscale))
    if not spec_char_block(sh, ctx, [figs, marks], spec_stage(sh, y1)):
        sh.problems.append("numerals: no row of figures can be set to this measure")
        return
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


def spec_folio(sh, ctx, y0, dark, cap=""):
    """The blackletter page: a braid across the head, a folio rule round the block.

    `knotband`'s furniture, and every part of it is already box-driven, which is
    why this class needed no new drawing machinery — only someone to hand it boxes
    that are the size of the sheet. The braid's wavelength is the pin's, so a wide
    page gets more of them rather than the same five stretched out.

    `cap` is the numerals sheet's illuminated initial: the ampersand the face
    carries, ruled and gilded, with the braid running out of the right side of it
    the way a manuscript's decoration runs out of the initial.
    """
    P, T = ctx["pal"], ctx["display"]
    s = sh.scale
    ink, mute, _ = field(P)
    ground = P["deep1"] if dark else P["paper1"]
    x, head = sh.m, 0
    bh = int(round(56 * s))
    if cap:
        side = int(round(120 * s))
        ib = Box(sh.m, y0, side, side)
        illum_box(sh, ib, ink, P["accent"])
        # Rubricated, but measured against the ground it actually sits on: the
        # accent of a vellum theme is 4.2:1 on its own paper, and a sheet whose
        # one showpiece needs the legibility system to rescue it is a colour bug.
        g = sh._behind(ib) or lum(ground)
        sh.text("cap", T, cap, Box(ib.x + 0.11 * side, ib.y + 0.09 * side,
                                   side * 0.78, side * 0.82),
                hi=side * 0.9, lo=20, max_lines=1, min_read=0.05 * sh.h,
                color=readable(g, rung(P, 1), 4.5))
        x, head = ib.r + int(round(24 * s)), side
    # Centred against the initial when there is one; never above y0, which is
    # where the head rule ended — a band with nothing beside it would otherwise
    # be half over the caption.
    band = Box(x, y0 + max(0, (head - bh) // 2), sh.w - sh.m - x, bh)
    knot_band(sh, band, ink, ground,
              waves=max(4, int(round(band.w / (162 * s)))))
    top = max(band.b, y0 + head) + int(round(26 * s))
    frame = Box(sh.m - int(round(12 * s)), top,
                sh.w - 2 * (sh.m - int(round(12 * s))), spec_floor(sh) - top)
    border_frame(sh, frame, mute, P["accent"])
    draw_orn(sh, "kn", "triquetra", frame.x + int(round(44 * s)),
             frame.y - int(round(4 * s)), 26 * s, P["accent"], 0.95,
             collide=False)
    pad = int(round(34 * s))
    return Box(frame.x + pad, frame.y + int(round(30 * s)),
               frame.w - 2 * pad, frame.h - int(round(62 * s)))


@specimen("blackletter", "letters",
          "A–J and a–j inside a folio rule, under a band of interlace")
def s_letters_blackletter(sh, ctx):
    """`knotband`'s frame without its funnel: the letters on rows of their own.

    The pin funnels pairs because a woven band wants a shape to sit under. A sheet
    wants the letters comparable, so they stand at one size and the frame takes
    whatever is left of the page, which is the part that scales by itself.
    """
    dark = spec_bg(sh, ctx, pool=0.08)
    built = spec_letters(sh, ctx)
    if not built:
        return
    ups, los, claim = built
    stage = spec_folio(sh, ctx, spec_head(sh, ctx, "Character Set"), dark)
    if not spec_char_block(sh, ctx, [ups, los], stage):
        sh.problems.append("letters: no row of A\u2013J can be set to this measure")
        return
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


@specimen("blackletter", "numerals",
          "figures and marks ruled like a folio, opened with an illuminated &")
def s_numerals_blackletter(sh, ctx):
    """The same page, with the initial the numerals sheet has earned.

    An ampersand is the one figure-adjacent mark a blackletter buyer judges the
    face by, so it is the letter that opens the page — and it is drawn from the
    face, not pasted on, which is what makes it a specimen rather than ornament.
    """
    dark = spec_bg(sh, ctx, pool=0.08)
    built = spec_figures(sh, ctx)
    if not built:
        return
    figs, marks, claim = built
    cap = next((c for c in "&0123456789" if usable(ctx, c)),
               marks[0] if marks else "")
    stage = spec_folio(sh, ctx, spec_head(sh, ctx, "Figures & Punctuation"),
                       dark, cap)
    if not spec_char_block(sh, ctx, [figs, marks], stage):
        sh.problems.append("numerals: no row of figures can be set to this measure")
        return
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


def spec_row_rules(sh, ctx, stage, n):
    """A hairline under every row, drawn after the type.

    The rule is what a monoline gets judged on — the spacing has to hold when every
    row shares a baseline — and it is the one piece of this furniture that is
    structure rather than ornament, which is why it is drawn rather than banded.
    After the rows, so it can never cross ink, and clamped to the stage, so the
    last one cannot step on the footer.
    """
    _ink, mute, _ = field(ctx["pal"])
    for i in range(n):
        s = _slot(sh, f"row{i}")
        if s:
            y = min(s.ink.b + int(round(12 * sh.scale)), stage.b)
            rule(sh.cv, stage.x, y, stage.x + stage.w, y, mute, 1.2, 0.55)


@specimen("sports", "letters",
          "A–J and a–j at one size, every row standing on its own rule")
def s_letters_sports(sh, ctx):
    """The start list, which was already the sheet's grammar.

    `lane` puts twenty-six capitals on rules because a team sheet is the only
    thing a monoline has to be good at; the sheet puts twenty letters on the same
    rules and asks the same question at twice the size.
    """
    spec_bg(sh, ctx, pool=0.08)
    built = spec_letters(sh, ctx)
    if not built:
        return
    ups, los, claim = built
    y0 = spec_head(sh, ctx, "Character Set")
    stage = spec_stage(sh, spec_orn_band(sh, ctx, y0)
                       + int(round(14 * sh.vscale)))
    n = spec_char_block(sh, ctx, [ups, los], stage)
    if not n:
        sh.problems.append("letters: no row of A\u2013J can be set to this measure")
        return
    spec_row_rules(sh, ctx, stage, n)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


@specimen("sports", "numerals",
          "figures and marks on the timing board's own lines")
def s_numerals_sports(sh, ctx):
    """The split-time row: figures first, marks under them, each on a rule.

    A race sheet's numbers are the whole document, and this is the one place on
    the pair where the face is checked at the size it will actually be used — the
    scoreboard, not the poster.
    """
    spec_bg(sh, ctx, pool=0.08)
    built = spec_figures(sh, ctx)
    if not built:
        return
    figs, marks, claim = built
    y0 = spec_head(sh, ctx, "Figures & Punctuation")
    stage = spec_stage(sh, spec_orn_band(sh, ctx, y0)
                       + int(round(14 * sh.vscale)))
    n = spec_char_block(sh, ctx, [figs, marks], stage)
    if not n:
        sh.problems.append("numerals: no row of figures can be set to this measure")
        return
    spec_row_rules(sh, ctx, stage, n)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


# ---------------------------------------------------------------- the script pair


def spec_pieces(run, n):
    """A run cut into n pieces as near equal as the letters allow."""
    n = max(1, min(n, len(run)))
    out, i = [], 0
    for j in range(n):
        take = round(len(run) * (j + 1) / n) - i
        out.append(run[i:i + take])
        i += take
    return out


def spec_hand(sh, ctx, runs, stage):
    """Joined runs at one pen size, as [(text, size, baseline, ink top), ...].

    Not `spec_grid`, which sizes a row on the advance total including the gap it
    inserts between cells: ten joined capitals reach only two-thirds of the column
    that way, so the line stops short of the margin it was cut to. A script's
    alphabet exists as a run, so these rows are strings, and they start at the left
    margin because writing starts at the left margin.

    Each run may be cut into pieces, and the search takes the largest pen that both
    fits the stage and fills it: a square sheet has the landscape's height and a
    fifth less width, so two runs of ten letters leave most of it empty while four
    runs of five fill it at a size nobody needs to squint at.
    """
    T, P = ctx["display"], ctx["pal"]
    best = None
    for n in range(1, 4):
        seqs = [p for r in runs for p in spec_pieces(r, n) if p]
        size = min(fit_measure(T, r, stage.w, 900.0 * sh.scale) for r in seqs)
        if size <= 0:
            continue
        ink = sum(T.path(r, size)[0].getBounds().height() for r in seqs)
        block = ink + size * 0.30 * (len(seqs) - 1)
        size *= min(1.0, stage.h / block) if block else 1.0
        score = (min(block, stage.h) >= 0.62 * stage.h, size)
        if best is None or score > best[0]:
            best = (score, seqs, size)
    if not best:
        return []
    _score, seqs, size = best
    laid = [(r, T.path(r, size)[0].getBounds()) for r in seqs]
    lead, spare = spec_spread(stage, len(laid),
                              sum(b.height() for _r, b in laid), size * 0.30)
    ground = (sh._behind(Box(stage.x, stage.y, stage.w, min(stage.h, 300.0)))
              or lum(P["deep2"]))
    crisp = [readable(ground, rung(P, i), 4.5) for i in range(len(P["tone"]))]
    out, y = [], stage.y + spare
    for i, (r, b) in enumerate(laid):
        sh.text(f"run{i}", T, r, Box(stage.x, y, stage.w, b.height() + 2),
                hi=size, lo=size, max_lines=1, align="left", valign="top",
                min_read=0.05 * sh.h, color=crisp[i % len(crisp)])
        out.append((r, size, y - b.top(), y))
        y += b.height() + lead
    return out


def spec_hand_rules(sh, ctx, laid):
    """The ruled hand: a line to write on, and the line the letters touch above it.

    Both measured off the run that was drawn rather than off the metrics table:
    the baseline is where this renderer put the pen, and a rule guessed from
    units-per-em lands a descender's depth under the letters it belongs to.
    """
    _ink, mute, _ = field(ctx["pal"])

    def line(y, alpha):
        if sh.m <= y <= spec_floor(sh):
            rule(sh.cv, sh.m, y, sh.w - sh.m, y, mute, 1.2, alpha)

    for i, (_text, _size, base, top) in enumerate(laid):
        # The first row's top line is the head rule's job already; two hairlines
        # twenty pixels apart read as a mistake rather than as ruling.
        if i:
            line(top, 0.35)
        line(base, 0.55)


def spec_pen_stage(sh, ctx, y0):
    """The stage, stopped short of the foot band the manuscript class writes on.

    Drawing the band here rather than in both bodies is the point: a sheet that
    reserved the room and forgot the nibs, or the other way round, is the same
    sheet with a hole in it.
    """
    top = spec_floor(sh) - int(round(76 * sh.vscale))
    spec_orn_band(sh, ctx, top, part="bottom")
    return Box(sh.m, y0, sh.w - 2 * sh.m,
               top - int(round(40 * sh.vscale)) - y0)


@specimen("script", "letters",
          "A–J and a–j written as joined runs on a ruled hand")
def s_letters_script(sh, ctx):
    """`markup`'s proof without its funnel.

    The pin packs the whole alphabet into rows because a proof has to carry it;
    the sheet has twenty letters and the whole page, so the runs stay joined and
    the pen is as big as the stage allows.
    """
    spec_bg(sh, ctx, pool=0.10)
    built = spec_letters(sh, ctx)
    if not built:
        return
    ups, los, claim = built
    laid = spec_hand(sh, ctx, ["".join(ups), "".join(los)],
                     spec_pen_stage(sh, ctx, spec_head(sh, ctx, "Character Set")))
    if not laid:
        sh.problems.append("letters: no joined run of A–J fits this page")
        return
    spec_hand_rules(sh, ctx, laid)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


@specimen("script", "numerals",
          "the figures and the marks, ruled like a pen drill")
def s_numerals_script(sh, ctx):
    """Ciphers and marks on cells, standing on the sheet's own lines.

    The alphabet is set as runs because a script's letters only exist joined.
    Punctuation does not join, and ten figures against twenty-one marks cannot
    both reach the measure at one pen size — one of the two rows would stop short
    of the margin it was cut to. So this sheet takes the grid, and keeps the class
    in the foot band and the rules.
    """
    spec_bg(sh, ctx, pool=0.10)
    built = spec_figures(sh, ctx)
    if not built:
        return
    figs, marks, claim = built
    stage = spec_pen_stage(sh, ctx, spec_head(sh, ctx, "Figures & Punctuation"))
    n = spec_char_block(sh, ctx, [figs, marks], stage)
    if not n:
        sh.problems.append("numerals: no row of figures can be set to this measure")
        return
    spec_row_rules(sh, ctx, stage, n)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx, at=claim, exact=True)


def build_ctx(font_path, name, copy, palette=None, mode=None, about="",
              cls="elegant"):
    """Everything a pin needs, decided from the font's own data.

    The theme per pin and the showcase family are resolved here once, so a run is
    reproducible from the font alone: same file, same names, same colours.
    """
    cmap, flagged, facts = audit(font_path)
    tt = TTFont(str(font_path), fontNumber=0)
    # A sheet that names nothing sells nothing. When nobody authored a name the
    # font's own family record speaks — that is a fact about the file, which is
    # all a specimen is allowed to carry.
    name = name or (tt["name"].getDebugName(1) or Path(font_path).stem).strip()
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
        "tt": tt,
        "family": family, "why": why, "class": cls,
        "themes": assign_themes(name, sorted(cls_names(cls)), cls),
        "tone_offs": {}, "briefed": False,
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
    """The theme instance for one sheet: its palette, its mode, its colour ladder.

    Only the five pins get a rolled theme, because only the five pins are asked to
    look different from each other. A specimen sheet carries no authored copy, so
    it takes the class's own ground — or, with a brief in hand, whatever the
    class's set-equivalent pin was given.
    """
    _fn, _blurb, tcls, frame = TEMPLATES[name]
    key = ctx["themes"].get(name)
    if key is None:
        key = (SPECIMEN_THEME[tcls] if frame != "pin" else THEME_PREF[name][0])
        # Only a brief is a decision. Without one, `themes` is the roll, and a
        # sheet that took its ground from a hash of the filename would be a
        # coin flip wearing the name of a plan.
        if frame != "pin" and ctx["briefed"]:
            key = ctx["themes"].get(SPECIMEN_SET[tcls], key)
    th = dict(THEMES[key])
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
    fn, _blurb, _cls, frame = TEMPLATES[name]
    fw, fh = FRAMES[frame]
    surf = skia.Surface.MakeRasterN32Premul(fw, fh)
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
    cls = brief.get("class") or "elegant"
    if cls not in CLASS_ORDERS:
        return [f'class "{cls}" is not one of ' + ", ".join(CLASS_ORDERS)], []
    order = CLASS_ORDERS[cls]
    pins = brief.get("pins") or {}
    missing = [t for t in order if t not in pins]
    if missing:
        bad.append("no pin copy for: " + ", ".join(missing))
    unknown = [t for t in pins if t not in order]
    if unknown:
        bad.append(f"unknown template(s) for class {cls}: "
                   + ", ".join(unknown))
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


SPECIMEN_MAX_BYTES = 500_000  # reported, never engineered around


def save_specimen(img, out, frame, sheet):
    """Write one specimen sheet: a flat PNG, no ladder and no JPEG fallback.

    The 200 KB cap is a Pinterest rule, and these files are not pins — nothing
    downstream has ever capped them. A sheet that blows past 500 KB is therefore
    reported rather than quietly re-encoded, because the first lever is the pool
    radius and the last one is the type, and a silently-lossy specimen of a face
    someone is selling is worse than a big file.
    """
    d = out / frame
    d.mkdir(parents=True, exist_ok=True)
    ship = d / f"specimen-{sheet}.png"
    img.save(str(ship))
    from PIL import Image
    with Image.open(ship) as im:
        im.load()
        im.save(ship, "PNG", optimize=True)
        size = ship.stat().st_size
        w, h = im.size
    if (w, h) != FRAMES[frame]:
        raise SystemExit(f"{ship}: wrote {w}x{h}, the {frame} frame is "
                         f"{FRAMES[frame][0]}x{FRAMES[frame][1]}")
    return ship, size


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
    ap.add_argument("--class", dest="cls", choices=tuple(CLASS_ORDERS),
                    help="template family; default is the brief's class, "
                         "else elegant")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--specimens", action="store_true",
                    help="draw the class's specimen sheets instead of its pins: the "
                         "same four classes at 3x2 and 1x1, written into "
                         "<out>/3x2 and <out>/1x1. No authored copy, no brief rules.")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--stress", action="store_true")
    ap.add_argument("--faces", default="", help="name=path:name=path for --stress")
    args = ap.parse_args()

    if args.list:
        names = cls_names_spec if args.specimens else cls_names
        width = 24 if args.specimens else 13
        for cls in CLASS_ORDERS:
            print(f"  [{cls}]")
            for k in names(cls):
                _f, blurb, _c, _fr = TEMPLATES[k]
                print(f"    {k:{width}s} {blurb}")
        return 0

    if args.stress:
        return stress(args)

    if not args.font:
        ap.error("--font is required unless --list or --stress")
    brief = (json.loads(Path(args.brief).read_text(encoding="utf-8"))
             if args.brief else None)
    cls = args.cls or (brief or {}).get("class") or "elegant"
    if cls not in CLASS_ORDERS:
        ap.error(f"unknown class {cls!r} — try one of {', '.join(CLASS_ORDERS)}")
    if args.specimens and not (args.cls or (brief or {}).get("class")):
        # A pin with no class still has four authored headlines to argue with; a
        # specimen has none, so the default would ship a blackletter's sheets in
        # an elegant's clothes and nothing downstream could tell.
        ap.error("--specimens needs --class: the sheet says what the font is, "
                 "so it cannot guess")
    warns = []
    if brief is not None and not args.specimens:
        # check_brief() exists to stop five *authored* headlines repeating each
        # other. A specimen run authors nothing; it takes the brief for the theme
        # and the tone the class's set-equivalent pin was given.
        bad, warns = check_brief(brief, Path(args.out))
        if bad:
            for m in bad:
                print(f"  brief: {m}", file=sys.stderr)
            return 2
    title = args.name or (brief or {}).get("name", "")
    copy = ({"line": "", "sub": "", "over": "", "word": ""} if args.specimens else
            {"line": args.line, "sub": args.sub, "over": args.over,
             "word": args.word})
    # A specimen sheet is drawn from the font and nothing else: the marketing
    # lines a brief authors are the pins' business, and a footer that printed
    # "invitation suite · editorial" over a factual sheet would be an ad.
    ctx = build_ctx(args.font, title, copy,
                    args.palette, args.mode,
                    args.about or (brief or {}).get("about", ""), cls=cls)
    per = {}
    if brief is not None:
        themes, offs, copies = dict(ctx["themes"]), {}, {}
        for t, pin in brief["pins"].items():
            if pin.get("theme"):
                themes[t] = pin["theme"]
            offs[t] = int(pin.get("tone") or 0)
            copies[t] = {k: (pin.get(k) or "")
                         for k in ("line", "sub", "over", "word")}
        ctx = dict(ctx, themes=themes, tone_offs=offs, briefed=True)
        per = {t: dict(ctx, copy=c, ftrs=brief["pins"][t].get("ftrs") or {})
               for t, c in copies.items()}
    if not args.as_json:
        print(f"  {title}: {ctx['family']} — {ctx['why'][0] if ctx['why'] else 'default'}")
        print("  themes: " + ", ".join(f"{k}={v}" for k, v in sorted(ctx["themes"].items())))
    for m in warns:
        print(f"  brief: {m}", file=sys.stderr)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if brief is not None and not args.specimens:
        (out / "pins.brief.json").write_text(
            json.dumps(brief, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    owned = cls_names_spec(cls) if args.specimens else cls_names(cls)
    names = args.template or owned
    stray = [n for n in names if n not in owned]
    if stray:
        ap.error(f"template(s) {', '.join(stray)} are not in class {cls!r}; "
                 f"this class has {', '.join(owned)}")
    errors, notes, payload = [], [], []
    for name in names:
        surf, sh = render(name, per.get(name, ctx))
        img = surf.makeImageSnapshot()
        if args.specimens:
            _, sheet, frame = name.rsplit("_", 2)
            ship, size = save_specimen(img, out, frame, sheet)
            note = None
        else:
            stem = (f"pinterest_{CLASS_ORDERS[cls].index(name) + 1}"
                    if per else name)
            ship, size, note = save_pin(img, out, stem)
        if note:
            sh.notes.append(note)
        kb = size / 1024
        errs = as_errors(name, sh)
        cap = SPECIMEN_MAX_BYTES if args.specimens else MAX_BYTES
        if size > cap:
            errs.append({"template": name, "slot": "file",
                         "message": f"{kb:.0f} KB exceeds the "
                                    f"{cap // 1000} KB "
                                    f"{'specimen' if args.specimens else 'pin'} cap"})
        errors += errs
        notes += [{"template": name, "slot": n.split(":", 1)[0], "message": n}
                  for n in sh.notes]
        payload.append({"template": name, "png": str(ship), "kb": round(kb),
                        "slots": [{"slot": s.name, "size": round(s.size, 1),
                                   "lines": s.lines} for s in sh.slots]})
        if not args.as_json:
            print(f"  {name:24s} {kb:5.0f} KB  " +
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
    cells, errors = [], []
    for fname, fpath in faces:
        for fam in CLASS_ORDERS:
            base = build_ctx(fpath, fname, {}, args.palette, args.mode, cls=fam)
            names = [t for t in cls_names(fam)
                     if args.template is None or t in args.template]
            if not names:
                continue
            print(f"  {fname} [{fam}]: {base['family']} — "
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
