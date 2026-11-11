"""Pinterest pin template library, drawn from real font outlines.

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
The default set still ships five pins per font. Ten optional compositions broaden
the authorable library without changing that production contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
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
HALO_MIN = 130              # px: below this a halo is drawn straight, not stretched
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
# The first five remain the normal production set. These ten alternates can be
# selected in a brief's `templates` list or rendered directly with `--template`.
CLASS_VARIANTS = {
    "elegant": ("studio_cover", "specimen_mosaic", "wordmark_atelier"),
    "blackletter": ("illuminated_broadside", "reliquary_seal", "scribe_gallery"),
    "sports": ("jersey_panel", "scoreboard_split"),
    "script": ("letter_study", "garden_note"),
}
CLASS_TEMPLATE_POOLS = {
    cls: (*CLASS_ORDERS[cls], *CLASS_VARIANTS[cls]) for cls in CLASS_ORDERS
}
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
# The supporting-image catalogue: a shared pool drawn at 3:2, the same idea as
# the specimen sheets' second surface but with authored copy. These names
# are deliberately NOT in CLASS_ORDERS — pinterest_1..5 and the registry never
# learn them; --supports is a separate surface with its own numbering.
# Retired names stay in this tuple as tombstones so the remaining slot IDs stay stable.
SUPPORT_ORDER = ("line32",
                 "duo32",
                 "card32",
                 "feature32",
                 "sticker32",
                 "neon32",
                 "quote32",
                 "crest32",
                 "echo32",
                 "contour32",
                 "mountain32",
                 "hand32",
                 "zebra32",
                 "soldier32",
                 "mirror32",
                 "brutal32",
                 "brutalpack32",
                 "rio32",
                 "boots32",
                 "plakat32",
                 "plakatart32",
                 "mangos32",
                 "alphabet32",
                 "birvase32",
                 "weightfamily32",
                 "mangosboard32",
                 "ovalword32",
                 "stardust32",
                 "cliffpostcard32",
                 "kindersea32",
                 "messageframe32",
                 "contactlist32",
                 "sunsetpromise32",
                 "phonegarden32",
                 "pixelquote32",
                 "ravencover32",
                 "voguecover32",
                 "confident32",
                 "storyteller32",
                 "focusposter32",
                 "wideclaim32",
                 "blossom32",
                 # Withdrawn; keep this tombstone so later slot IDs do not move.
                 "bondibeach32",
                 "neue32",
                 "electromagnetic32",
                 "demolition32",
                 "yearposter32",
                 "stadiumposter32",
                 "signalclock32",
                 "amberdawn32",
                 "skinbadge32",
                 "latestlook32",
                 "gelatocards32",
                 "meditation32",
                 "strongweak32",
                 "funkyfashion32",
                 "dreamchalk32",
                 "lovecard32",
                 "queens32",
                 "lemonade32",
                 "sunkiss32",
                 "typewall32",
                 "manualbrew32",
                 "pastpresent32",
                 "herbalproduct32",
                 "colosseum32",
                 "glyphsheet32",
                 "freakscene32",
                 "greetingsgrid32",
                 "roadrunner32",
                 "palmello32", "quietattempt32", "hushglow32",
                 "italianhorror32", "dreamwarriors32", "nesting32",
                 "erotica32", "conspiracytheory32", "overglow32",
                 "pinkvice32", "attitude32", "indieground32",
                 "caramelsundae32", "sweettreat32",
                 "saucystack32", "anteliascard32", "peacebreath32",
                 "nyccoffee32", "afterhours32", "outofoffice32",
                 "skincareroutine32", "youlookgood32", "spiritadventure32",
                 "dreamfollow32", "angelinastyle32", "comesnatural32",
                 "calmafterstorm32", "beachclub32", "splitampersand32",
                 "setrum32", "nectarambience32", "fluorescentduo32",
                 "sacharon32", "lastnightsweden32", "crywolf32",
                 "welcomemorning32", "esens32", "asbon32", "italicregular32",
                 "smokeletters32", "blackerwear32", "silentnight32", "playgrid32",
                 "fridayrunning32", "greatness32", "medievalcreatures32",
                 "littlemadquote32",
                 "soulrevenge32",
                 "allworkplay32",
                 "sociato32",
                 "owlstory32",
                 "hazysky32",
                 "itsokay32",
                 "nightonearth32",
                 "goodthingstothose32",
                 "rudybrownie32",
                 "spaceprint32",
                 "scriptgrid32",
                 "smashcourt32",
                 "scriptpattern32",
                 "brushpanel32",
                 "avalonbrush32",
                 "ssrange32",
                 "allsummerlong32",
                 "boldcampaign32",
                 "goodtimeroll32",
                 "childhoodbook32",
                 "playerglyph32",
                 "alicebadge32",
                 "notallroads32",
                 "practicehard32",
                 "rainbowstack32",
                 "wakefamous32",
                 "sexyshout32",
                 "embracesexiest32",
                 "prettyinpink32",
                 "dynamicplayful32",
                 "retroshowcase32",
                 "iconicposter32",
                 "summerparadise32",
                 "calgarywelcome32",
                 "latinmaxims32",
                 "onlygooddieyoung32",
                 "blackholesun32",
                 "somethingabouther32",
                 "darknightbrighterday32",
                 "tc-panthoma-specimen32",
                 "tcpanthomarepeat32",
                 "strongerquote32",
                 "scarygangsta32",
                 "darkbriton32",
                 "darkbritonthankyou32",
                 "hailcrash32",
                 "awakeportrait32",
                 "pixelledger32",
                 "winevintage32",
                 "blackgold32",
                 "hongkongcrisis32",
                 "caves46532",
                 "yabbadabbadoo32",
                 "choosinghappiness32",
                 "fatkillkat32",
                 "crimsonportrait32",
                 "statueframe32",
                 "portraitcard32",
                 "warmportrait32",
                 "fashioncard32",
                 "cinemaportrait32",
                 "parkstatement32",
                 "amberquote32",
                 "numeralfolio32",
                 "timechange32",
                 "bottleoffer32",
                 "bootzyfear32",
                 "bootzyalmost32",
                 "bootzygraphic32",
                 "bootzybunny32",
                 "quadfont32",
                 "mythicallions32",
                 "lifeinblackwhite32",
                 "romanstrips32",
                 "floraltriptych32",
                 "homequote32",
                 )
HTML_ONLY_SUPPORT = frozenset({
    "palmello32", "quietattempt32", "hushglow32", "italianhorror32",
    "dreamwarriors32", "nesting32", "erotica32", "conspiracytheory32",
    "overglow32", "pinkvice32", "attitude32", "indieground32",
    "caramelsundae32", "sweettreat32",
    "saucystack32", "anteliascard32", "peacebreath32",
    "nyccoffee32", "afterhours32", "outofoffice32",
    "skincareroutine32", "youlookgood32", "spiritadventure32",
    "dreamfollow32", "angelinastyle32", "comesnatural32",
    "calmafterstorm32", "beachclub32", "splitampersand32",
    "setrum32", "nectarambience32", "fluorescentduo32",
    "sacharon32", "lastnightsweden32", "crywolf32", "welcomemorning32",
    "esens32", "asbon32", "italicregular32", "smokeletters32",
    "blackerwear32",
    "silentnight32",
    "playgrid32",
    "fridayrunning32",
    "medievalcreatures32",
    "littlemadquote32",
    "soulrevenge32",
    "allworkplay32",
    "sociato32",
    "owlstory32",
    "hazysky32",
    "itsokay32",
    "nightonearth32",
    "goodthingstothose32",
    "rudybrownie32",
    "spaceprint32",
    "scriptgrid32",
    "smashcourt32",
    "scriptpattern32",
    "brushpanel32",
    "avalonbrush32",
    "ssrange32",
    "allsummerlong32",
    "boldcampaign32",
    "goodtimeroll32",
    "childhoodbook32",
    "playerglyph32",
    "alicebadge32",
    "notallroads32",
    "practicehard32",
    "rainbowstack32",
    "wakefamous32",
    "sexyshout32",
    "embracesexiest32",
    "prettyinpink32",
    "dynamicplayful32",
    "retroshowcase32",
    "iconicposter32",
    "summerparadise32",
    "calgarywelcome32",
    "latinmaxims32",
    "onlygooddieyoung32",
    "blackholesun32",
    "somethingabouther32",
    "darknightbrighterday32",
    "tc-panthoma-specimen32",
    "tcpanthomarepeat32",
    "strongerquote32",
    "scarygangsta32",
    "darkbriton32",
    "darkbritonthankyou32",
    "hailcrash32",
    "awakeportrait32",
    "pixelledger32",
    "winevintage32",
    "blackgold32",
    "hongkongcrisis32",
    "caves46532",
    "yabbadabbadoo32",
    "choosinghappiness32",
    "fatkillkat32",
    "crimsonportrait32", "statueframe32", "portraitcard32", "warmportrait32",
    "fashioncard32", "cinemaportrait32", "parkstatement32", "amberquote32",
    "numeralfolio32", "timechange32", "bottleoffer32", "bootzyfear32",
    "bootzyalmost32", "bootzygraphic32", "bootzybunny32", "quadfont32",
    "mythicallions32", "lifeinblackwhite32", "romanstrips32",
    "floraltriptych32", "homequote32",
})
# Retired layouts are out of the active support catalogue. This set exists only
# so a later support run can withdraw their old renderer-owned PNGs safely.
SUPPORT_RETIRED = frozenset({
    "announce32", "ladder32", "retro32", "variable32", "archive32",
    "cast32", "loop32", "deboss32", "anatomy32", "riso32", "shear32",
    "mosaic32", "stencil32", "bondibeach32", "sticker32", "echo32",
    "brutalpack32", "dreamchalk32", "lovecard32", "queens32",
    "lemonade32", "sunkiss32", "greatness32",
    # Seller-selected retirements on 2026-10-26.
    "line32", "duo32", "card32", "hand32", "zebra32",
    "electromagnetic32", "demolition32", "skinbadge32", "gelatocards32",
    "angelinastyle32", "beachclub32", "fluorescentduo32",
    "lastnightsweden32", "spaceprint32",
    # Seller-selected retirements on 2026-10-29.
    "soldier32", "brutal32", "storyteller32", "blossom32", "meditation32",
    "sociato32", "scriptpattern32", "avalonbrush32", "boldcampaign32",
    "skincareroutine32", "saucystack32", "indieground32", "crest32",
    # Seller-selected retirements on 2026-11-03; keep their slot tombstones.
    "herbalproduct32", "nectarambience32", "playerglyph32", "alicebadge32",
    "statueframe32", "fashioncard32",
    # Seller-selected retirements on 2026-11-07; keep their slot tombstones.
    "contour32", "plakat32", "voguecover32", "confident32",
    "parkstatement32",
    # Seller-selected retirement on 2026-11-11.
    "littlemadquote32",
})
# Mono faces still avoid the two badge/card constructions that rely on a
# proportioned wordmark. Style-specific exclusions below were assigned after
# comparing every active template against six real representative faces.
SUPPORT_UNFIT = {
    "crest32":  ("mono",),
    "card32":   ("mono",),
}

# Explicit hard mismatches from the paired reference/render review. Conditional
# fits remain selectable; this list only removes templates whose visual voice,
# subject context, glyph coverage, or measured fit conflicts with the tested
# style. The style group is inferred from both the renderer class and the
# classifier family because sports/pixel and script/brush share renderer classes.
SUPPORT_STYLE_EXCLUDE = {
    "blackletter": frozenset({
        "duo32", "hand32", "rio32", "boots32", "mangos32", "contour32",
        "mirror32", "ovalword32", "kindersea32", "messageframe32",
        "pixelquote32", "ravencover32", "voguecover32", "confident32",
        "storyteller32", "wideclaim32", "neue32", "demolition32",
        "skinbadge32", "gelatocards32", "meditation32", "typewall32",
        "pastpresent32", "greetingsgrid32",
    }),
    "handwritten": frozenset({
        "card32", "brutal32", "boots32", "plakatart32", "contactlist32",
        "sunsetpromise32", "phonegarden32", "pixelquote32", "greetingsgrid32",
        "neue32",
    }),
    "tech-sports": frozenset({
        "duo32", "contour32", "card32", "feature32", "quote32",
        "echo32",
        "rio32", "boots32", "ovalword32", "cliffpostcard32", "kindersea32",
        "messageframe32", "contactlist32", "sunsetpromise32", "phonegarden32",
        "pixelquote32", "voguecover32", "confident32", "storyteller32",
        "blossom32", "greetingsgrid32",
    }),
    "brush": frozenset({
        "contour32", "card32", "pixelquote32", "greetingsgrid32", "neue32",
    }),
    "pixel": frozenset({
        "contour32", "duo32", "card32", "quote32", "ovalword32",
        "cliffpostcard32", "voguecover32", "confident32", "storyteller32",
        "focusposter32", "blossom32", "amberdawn32", "meditation32",
        "greetingsgrid32", "neue32",
    }),
    "display": frozenset({
        "card32", "mangos32", "skinbadge32", "glyphsheet32", "greetingsgrid32",
        "neue32",
    }),
}


SUPPORT_MIN_STYLES = {
    "boots32": 2, "weightfamily32": 2, "mangosboard32": 2,
    "italicregular32": 2,
}

# Keep every eligible layout available to every class. A small relative weight
# gives blackletter runs a few more chances to land on typographic, framed, or
# engraved panels that show that face well without turning the catalogue into a
# class-specific whitelist.
BLACKLETTER_SUPPORT_AFFINITY = frozenset({
    "line32", "feature32", "quote32", "crest32", "mountain32", "zebra32",
    "soldier32", "brutal32", "plakatart32", "alphabet32", "stardust32",
    "contactlist32", "focusposter32", "electromagnetic32", "yearposter32",
    "amberdawn32", "colosseum32", "glyphsheet32", "freakscene32",
})
BLACKLETTER_SUPPORT_WEIGHT = 1.16


def support_style_group(cls, family):
    """Map the four renderer classes to the six audited visual style groups."""
    if cls == "blackletter":
        return "blackletter"
    if cls == "script":
        return "brush" if family == "brush" else "handwritten"
    if cls == "sports":
        return "pixel" if family == "pixel" else "tech-sports"
    if cls == "elegant" and family == "display-bold":
        return "display"
    return None


def support_fits(name, cls, family, family_styles=1, has_weight_triplet=False):
    """True when one support panel may be sold for this class / showcase family."""
    bad = SUPPORT_UNFIT.get(name, ())
    style = support_style_group(cls, family)
    return (name not in SUPPORT_RETIRED and cls not in bad and family not in bad
            and name not in SUPPORT_STYLE_EXCLUDE.get(style, ())
            and family_styles >= SUPPORT_MIN_STYLES.get(name, 1))


def support_names(cls, family="", family_styles=1, has_weight_triplet=False):
    """The support catalogue as it ships for one face: the pool minus what cannot
    wear it. `SUPPORT_ORDER` still supplies the numbering, so a panel keeps its
    slot in the folder name whatever else was dropped. Family proof panels are
    offered only when the source folder contains at least two distinct styles;
    they use real sibling files without synthesizing missing weights."""
    return [n for n in SUPPORT_ORDER if support_fits(
        n, cls, family, family_styles, has_weight_triplet)]


def support_review_names(family_styles=1):
    """Return every active support layout for a catalogue review, independent
    of class fit but retaining retired and real-family-style gates."""
    return [name for name in SUPPORT_ORDER
            if name not in SUPPORT_RETIRED
            and family_styles >= SUPPORT_MIN_STYLES.get(name, 1)]


def support_history_counts(font_path, cls):
    """Count prior uses by this class from prepared handoff manifests.

    The current source folder is excluded so rerunning one font does not count
    its previous selection against itself. Only direct, non-archived font
    workspaces are considered.
    """
    fonts_root = Path(__file__).resolve().parents[2] / "font-factory" / "fonts"
    current_workspace = Path(font_path).expanduser().resolve().parent
    counts = {}
    pattern = re.compile(
        r"supporting/3x2/support-\d+_([a-z0-9]+(?:-[a-z0-9]+)*)\.png"
    )
    for manifest in sorted(fonts_root.glob("*/prepared_visuals/visual-handoff-manifest.md")):
        workspace = manifest.parent.parent.resolve()
        if workspace == current_workspace:
            continue
        plan_path = workspace / "visual-direction" / "visual-plan.json"
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            if plan.get("renderer_class") != cls:
                continue
            text = manifest.read_text(encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            continue
        for name in set(pattern.findall(text)):
            counts[name] = counts.get(name, 0) + 1
    return counts


def sample_supports(rng, names, count, cls, usage_counts=None):
    """Choose least-used eligible layouts first, randomizing ties.

    Blackletter-friendly weighting applies among equally used candidates; it
    never overrides usage balancing or removes/guarantees a template.
    """
    candidates = list(names)
    selected = []
    usage = dict(usage_counts or {})
    count = min(max(0, count), len(candidates))
    for _ in range(count):
        least_used = min(usage.get(name, 0) for name in candidates)
        tied = [name for name in candidates
                if usage.get(name, 0) == least_used]
        weights = [BLACKLETTER_SUPPORT_WEIGHT
                   if cls == "blackletter" and name in BLACKLETTER_SUPPORT_AFFINITY
                   else 1.0 for name in tied]
        choice = rng.choices(tied, weights=weights, k=1)[0]
        selected.append(choice)
        usage[choice] = least_used + 1
        candidates.remove(choice)
    return selected


def select_support_templates(rng, names, count, cls, usage_counts=None):
    """Sample all eligible layouts; family showcases have no guaranteed slots."""
    selected = sample_supports(rng, names, count, cls, usage_counts)
    return sorted(selected, key=SUPPORT_ORDER.index)
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
    "studio_cover": ("clay", "bone", "ember", "sage"),
    "specimen_mosaic": ("sage", "bone", "midnight", "moss"),
    "wordmark_atelier": ("clay", "midnight", "sage", "bone"),
    "wall":       ("ember", "moss", "midnight"),
    "set":        ("sage", "bone", "clay"),
    "full_stack": ("bone", "midnight", "sage", "ember"),
    "phrase":     ("clay", "sage", "bone"),
    "illuminated_broadside": ("vellum", "gilded", "bone", "ember"),
    "reliquary_seal": ("gilded", "vellum", "midnight", "clay"),
    "scribe_gallery": ("vellum", "gilded", "sage", "moss"),
    "jersey_panel": ("asphalt", "chrome", "midnight", "ember"),
    "scoreboard_split": ("chrome", "asphalt", "midnight", "bone"),
    "letter_study": ("graphite", "inkwell", "sage"),
    "garden_note": ("inkwell", "graphite", "bone", "sage"),
    "mountain32": ("midnight", "ember", "asphalt", "bone"),
    "hand32":     ("bone", "sage", "clay", "midnight", "ember"),
    "zebra32":    ("inkwell", "bone", "sage", "clay"),
    "soldier32":  ("inkwell", "midnight", "bone", "gilded"),
    "mirror32":   ("midnight", "inkwell", "clay", "bone"),
    "brutal32":   ("midnight", "inkwell", "bone", "asphalt"),
    "brutalpack32": ("inkwell", "midnight", "bone", "asphalt"),
    "rio32":      ("midnight", "ember", "asphalt", "inkwell"),
    "boots32":    ("sage", "moss", "bone", "clay"),
    "plakat32":   ("midnight", "chrome", "inkwell", "asphalt"),
    "plakatart32": ("midnight", "inkwell", "asphalt", "chrome"),
    "mangos32":   ("midnight", "chrome", "inkwell", "asphalt"),
    "alphabet32": ("bone", "sage", "clay", "midnight"),
    "birvase32":  ("midnight", "ember", "inkwell", "chrome"),
    "weightfamily32": ("midnight", "chrome", "bone", "sage"),
    "mangosboard32": ("midnight", "chrome", "inkwell", "asphalt"),
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
    # The support catalogue is one shared pool across all four classes, so its
    # shortlists name only the six shared worlds; `assign_themes` prepends the
    # class's own worlds at render time, which is how one body wears four suits.
    "line32":      ("midnight", "clay", "ember", "sage"),
    "duo32":       ("ember", "moss", "bone", "midnight"),
    "card32":      ("sage", "bone", "moss", "clay"),
    "feature32":   ("bone", "sage", "clay", "midnight"),
    "sticker32":   ("clay", "bone", "ember", "moss"),
    "neon32":      ("midnight", "ember", "clay", "moss"),
    "quote32":     ("sage", "midnight", "bone", "ember"),
    "crest32":     ("moss", "ember", "midnight", "bone"),
    "echo32":      ("clay", "bone", "moss", "ember"),
    "contour32":   ("bone", "sage", "midnight", "clay"),
    # Added 2026-10-14 from the downloaded supporting-image reference set.
    "ovalword32": ("bone", "sage", "clay", "midnight"),
    "stardust32": ("midnight", "sage", "bone", "ember"),
    "cliffpostcard32": ("sage", "bone", "midnight", "clay"),
    "kindersea32": ("bone", "sage", "clay", "midnight"),
    "messageframe32": ("sage", "bone", "clay", "midnight"),
    "contactlist32": ("bone", "sage", "midnight", "clay"),
    "sunsetpromise32": ("clay", "ember", "bone", "sage"),
    "phonegarden32": ("bone", "sage", "clay", "moss"),
    "pixelquote32": ("midnight", "ember", "clay", "bone"),
    "ravencover32": ("midnight", "ember", "clay", "bone"),
    "voguecover32": ("bone", "ember", "midnight", "sage"),
    "confident32": ("bone", "ember", "sage", "midnight"),
    "storyteller32": ("bone", "ember", "sage", "clay"),
    "focusposter32": ("bone", "ember", "midnight", "sage"),
    "wideclaim32": ("bone", "ember", "midnight", "clay"),
    "blossom32": ("ember", "bone", "clay", "sage"),
    "neue32": ("bone", "clay", "midnight", "sage"),
    "electromagnetic32": ("midnight", "clay", "ember", "moss"),
    "demolition32": ("midnight", "clay", "ember", "bone"),
    "yearposter32": ("ember", "clay", "midnight", "bone"),
    "stadiumposter32": ("ember", "midnight", "clay", "bone"),
    "signalclock32": ("midnight", "ember", "clay", "bone"),
    "amberdawn32": ("clay", "bone", "ember", "sage"),
    "skinbadge32": ("bone", "clay", "sage", "ember"),
    "latestlook32": ("ember", "clay", "bone", "midnight"),
    "gelatocards32": ("bone", "sage", "clay", "ember"),
    "meditation32": ("sage", "bone", "midnight", "clay"),
    "strongweak32": ("clay", "bone", "ember", "sage"),
    "funkyfashion32": ("clay", "ember", "bone", "sage"),
    "dreamchalk32": ("midnight", "sage", "bone", "clay"),
    "lovecard32": ("moss", "bone", "ember", "sage"),
    "queens32": ("midnight", "moss", "bone", "ember"),
    "lemonade32": ("bone", "sage", "clay", "moss"),
    "sunkiss32": ("bone", "clay", "sage", "ember"),
    "typewall32": ("midnight", "bone", "sage", "clay"),
    "manualbrew32": ("midnight", "bone", "clay", "sage"),
    "pastpresent32": ("bone", "clay", "sage", "moss"),
    "herbalproduct32": ("moss", "sage", "bone", "clay"),
    "colosseum32": ("bone", "sage", "clay", "midnight"),
    "glyphsheet32": ("moss", "bone", "midnight", "sage"),
    "freakscene32": ("clay", "bone", "midnight", "ember"),
    "greetingsgrid32": ("clay", "bone", "sage", "moss"),
    "roadrunner32": ("bone", "clay", "ember", "sage"),
    "palmello32": ("sage", "moss", "bone"),
    "quietattempt32": ("graphite", "inkwell", "sage"),
    "hushglow32": ("graphite", "inkwell", "clay"),
    "italianhorror32": ("ember", "midnight", "bone"),
    "dreamwarriors32": ("midnight", "ember", "inkwell"),
    "nesting32": ("ember", "midnight", "bone"),
    "erotica32": ("ember", "midnight", "clay"),
    "conspiracytheory32": ("midnight", "ember", "inkwell"),
    "overglow32": ("midnight", "clay", "bone"),
    "pinkvice32": ("midnight", "clay", "bone"),
    "attitude32": ("midnight", "clay", "bone"),
    "indieground32": ("clay", "midnight", "bone"),
    "caramelsundae32": ("clay", "bone", "sage"),
    "sweettreat32": ("clay", "bone", "sage"),
    "saucystack32": ("clay", "ember", "sage"),
    "anteliascard32": ("bone", "sage", "clay"),
    "peacebreath32": ("sage", "bone", "midnight"),
    "nyccoffee32": ("bone", "clay", "midnight"),
    "afterhours32": ("sage", "clay", "bone"),
    "outofoffice32": ("ember", "clay", "bone"),
    "skincareroutine32": ("bone", "sage", "clay"),
    "youlookgood32": ("sage", "bone", "midnight"),
    "spiritadventure32": ("midnight", "bone", "sage"),
    "dreamfollow32": ("midnight", "sage", "bone"),
    "angelinastyle32": ("midnight", "sage", "bone"),
    "comesnatural32": ("bone", "sage", "clay"),
    "calmafterstorm32": ("sage", "bone", "clay"),
    "beachclub32": ("clay", "bone", "sage"),
    "splitampersand32": ("bone", "midnight", "clay"),
    "setrum32": ("midnight", "chrome", "bone"),
    "nectarambience32": ("midnight", "clay", "sage"),
    "fluorescentduo32": ("clay", "bone", "midnight"),
    "sacharon32": ("clay", "midnight", "bone"),
    "lastnightsweden32": ("midnight", "clay", "bone"),
    "crywolf32": ("midnight", "bone", "clay"),
    "welcomemorning32": ("clay", "bone", "sage"),
    "esens32": ("clay", "bone", "sage"),
    "asbon32": ("clay", "bone", "sage"),
    "italicregular32": ("bone", "clay", "sage"),
    "smokeletters32": ("bone", "midnight", "clay"),
    "blackerwear32": ("midnight", "bone", "clay"),
    "silentnight32": ("midnight", "bone", "clay"),
    "playgrid32": ("midnight", "bone", "clay"),
    "fridayrunning32": ("midnight", "bone", "clay"),
    "medievalcreatures32": ("midnight", "clay", "bone"),
    "littlemadquote32": ("midnight", "bone", "clay"),
    "soulrevenge32": ("midnight", "bone", "clay"),
    "allworkplay32": ("midnight", "bone", "clay"),
    "sociato32": ("midnight", "bone", "clay"),
    "owlstory32": ("bone", "clay", "sage"),
    "hazysky32": ("clay", "sage", "bone"),
    "itsokay32": ("midnight", "clay", "bone"),
    "nightonearth32": ("midnight", "bone", "clay"),
    "goodthingstothose32": ("midnight", "bone", "clay", "ember"),
    "rudybrownie32": ("afterhours", "ember", "midnight", "clay"),
    "spaceprint32": ("midnight", "clay", "ember"),
    "scriptgrid32": ("midnight", "bone", "inkwell"),
    "smashcourt32": ("midnight", "afterhours", "bone"),
    "scriptpattern32": ("bone", "clay", "sage"),
    "brushpanel32": ("clay", "sage", "bone"),
    "avalonbrush32": ("bone", "clay", "sage"),
    "ssrange32": ("midnight", "clay", "bone"),
    "allsummerlong32": ("midnight", "clay", "bone"),
    "boldcampaign32": ("bone", "midnight", "sage"),
    "goodtimeroll32": ("afterhours", "bone", "clay"),
    "childhoodbook32": ("bone", "ember", "afterhours"),
    "playerglyph32": ("midnight", "afterhours", "clay"),
    "alicebadge32": ("midnight", "afterhours", "clay"),
    "notallroads32": ("midnight", "afterhours", "clay"),
    "practicehard32": ("midnight", "afterhours", "clay"),
    "rainbowstack32": ("midnight", "afterhours", "bone"),
    "wakefamous32": ("midnight", "afterhours", "clay"),
    "sexyshout32": ("midnight", "bone", "clay"),
    "embracesexiest32": ("clay", "bone", "midnight"),
    # Reference-led additions need catalogue themes too, even when their HTML
    # editors carry a fixed source palette. These shortlists keep the review
    # rotation complete and deterministic for every active slot.
    "prettyinpink32": ("clay", "bone", "sage"),
    "dynamicplayful32": ("clay", "sage", "bone"),
    "retroshowcase32": ("clay", "midnight", "bone"),
    "iconicposter32": ("midnight", "clay", "bone"),
    "summerparadise32": ("sage", "clay", "bone"),
    "calgarywelcome32": ("clay", "sage", "bone"),
    "latinmaxims32": ("midnight", "bone", "clay"),
    "onlygooddieyoung32": ("midnight", "ember", "bone"),
    "blackholesun32": ("midnight", "ember", "clay"),
    "somethingabouther32": ("midnight", "clay", "bone"),
    "darknightbrighterday32": ("midnight", "bone", "sage"),
    "tc-panthoma-specimen32": ("midnight", "bone", "clay"),
    "tcpanthomarepeat32": ("midnight", "bone", "clay"),
    "strongerquote32": ("midnight", "clay", "bone"),
    "scarygangsta32": ("midnight", "ember", "bone"),
    "darkbriton32": ("midnight", "gilded", "vellum", "bone"),
    "darkbritonthankyou32": ("midnight", "gilded", "vellum", "bone"),
    "hailcrash32": ("midnight", "ember", "clay", "bone"),
    "awakeportrait32": ("midnight", "clay", "bone"),
    "pixelledger32": ("midnight", "chrome", "bone"),
    "winevintage32": ("midnight", "gilded", "clay", "bone"),
    "blackgold32": ("midnight", "gilded", "bone"),
    "hongkongcrisis32": ("midnight", "ember", "bone"),
    "caves46532": ("midnight", "clay", "bone"),
    "yabbadabbadoo32": ("bone", "clay", "sage"),
    "choosinghappiness32": ("clay", "sage", "bone"),
    "fatkillkat32": ("midnight", "clay", "bone"),
    "crimsonportrait32": ("midnight", "clay", "bone"),
    "statueframe32": ("bone", "gilded", "sage"),
    "portraitcard32": ("bone", "sage", "clay"),
    "warmportrait32": ("midnight", "clay", "bone"),
    "fashioncard32": ("bone", "clay", "sage"),
    "cinemaportrait32": ("midnight", "ember", "bone"),
    "parkstatement32": ("midnight", "bone", "clay"),
    "amberquote32": ("midnight", "ember", "clay"),
}


def assign_themes(seed, names, cls="elegant", prefs=None):
    """One theme per pin, no repeats, rotated by the font name so two fonts of
    the same shape still do not ship the same colour world — and a re-run of the
    same font lands identically."""
    rot = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    used, out = set(), {}
    # A class-owned world (vellum, gilded) never leaks into another class's
    # rotation; a brief can still ask for it explicitly.
    pool = [t for t in THEME_NAMES if THEMES[t].get("cls") in (None, cls)]
    for i, name in enumerate(names):
        pref = (prefs or THEME_PREF)[name]
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
                       if chr(cp).isalpha() and len(chr(cp).upper()) == 1
                       and chr(cp).upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                       and n not in dense),
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
             valign="middle", min_read=0.0, bleed=False, collide=True,
             alpha=1.0, min_contrast=4.5, hatch=None, glow=None, features=None):
        support_ctx = getattr(self, "_support_ctx", None)
        if support_ctx is not None:
            string = support_render_copy(support_ctx, string)
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
                               len(lines), bleed, collide))
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
    return [n for n in CLASS_TEMPLATE_POOLS[cls] if n in TEMPLATES]


def cls_names_spec(cls):
    """Specimen sheet names owned by one class, in design order."""
    return [n for n in SPECIMEN_ORDERS[cls] if n in TEMPLATES]


def template(name, blurb, cls="elegant", frame="pin"):
    def deco(fn):
        TEMPLATES[name] = (fn, blurb, cls, frame)
        return fn
    return deco


def support(name, blurb):
    """Register one landscape support panel.

    Like `@specimen`, one body at one frame; unlike a pin, the panel belongs to
    no class — the class enters through the theme roll (world, ornament set,
    colour ladder), not through the registry. The frame is fixed to 3:2 because
    that is the only surface a marketplace supporting image ships on.
    """
    def deco(fn):
        if name not in SUPPORT_RETIRED:
            TEMPLATES[name] = (fn, blurb, "elegant", "3x2")
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


# Shared, byte-budgeted material texture toolkit. It is applied after the
# gradient/device ground and before lettering, so the existing contrast
# measurements still see the actual surface underneath each text slot.
TEXTURE_ALLOW_BYTES = 5_200
TEXTURE_STRENGTH = 0.35
TEXTURE_KINDS = ("press", "laid", "raster", "worn", "damp", "sieve")
_TEX_CACHE = {}


def bg(sh, P, th, invert=False, pool=None, tooth=None, dev=True, tex=None):
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
    if tex is not False:
        texture_pack(sh, P, kind=tex or _tex_kind(th), strength=TEXTURE_STRENGTH,
                     seed=_tex_seed(th), box=Box(0.0, 0.0, float(sh.w), float(sh.h)))
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




def rung(P, i):
    """The flat colour of ladder rung `i` — a gradient's bright end, for when a
    colour is needed as a value rather than as a paint."""
    spec = tone(P, i)
    if "grad" in spec:
        return spec["grad"][1]
    return spec.get("color") or (P["glow"] if P["mode"] == "dark" else P["ink"])


def _lift(spec, ground, floor):
    """A ladder rung pushed clear of the ground it is about to be painted on.

    The checker in `Sheet._enforce` measures the ground under each row and lifts
    anything that lands below its floor, which is correct but noisy: a template
    that knows where its type is going should resolve its own ink first and ship
    without a note. The catch is *which* ground — the whole stage and one row of
    it are different medians once there is a pool or a band across the sheet, so
    the lift has to happen per row, against the same box the checker will read.
    """
    out = dict(spec)
    if "color" in out:
        out["color"] = readable(ground, out["color"], floor)
    if "grad" in out:
        a, b, ang = out["grad"]
        out["grad"] = (readable(ground, a, floor), readable(ground, b, floor), ang)
    return out


def halo(cv, p, rgb, sigma, alpha=0.42):
    """A glow behind an outline: the same path blurred, under the crisp ink.

    The one thing a raster-only renderer cannot fake with a second draw offset —
    skia applies a real gaussian to the layer, so the letter looks lit rather
    than printed. Cost is ~45 ms per full-frame pass, which is why it goes on the
    specimen rows and not on every label.

    A blur is pure continuous tone, so it is the one thing on the sheet that can
    be rendered small and stretched without losing anything a viewer can see —
    and the only thing that *must* be, because a full-res gaussian over a
    marquee-sized path costs half a megabyte of PNG on its own. Below `HALO_MIN`
    there is too little area to pay for a second surface, so the small ones are
    drawn straight.

    Measured against the obvious alternative: replacing a bloom with a few flat
    concentric rings — the trick that made `wash_band` cheap — costs *more* here,
    not less (a perforation strip went from 16 KB to 25 KB), because the rings
    buy their sharpness with a dozen new antialiased edges and the stretched
    gaussian buys the same area with one. What actually costs bytes is the
    *spread*: the ramp is paid for once per pixel it covers, so a glow is kept
    thin by shrinking its sigma, never by stepping it.
    """
    b = p.getBounds()
    pad = 3.0 * sigma + 2.0
    vw, vh = b.width() + 2 * pad, b.height() + 2 * pad
    if min(vw, vh) < HALO_MIN:
        cv.drawPath(p, paint(C(rgb, alpha), blur=sigma))
        return
    s = BG_SCALE
    sw, sh_ = max(1, int(vw / s)), max(1, int(vh / s))
    sub = skia.Surface.MakeRasterN32Premul(sw, sh_)
    if sub is None:
        cv.drawPath(p, paint(C(rgb, alpha), blur=sigma))
        return
    scv = sub.getCanvas()
    scv.scale(1.0 / s, 1.0 / s)
    scv.translate(-(b.left() - pad), -(b.top() - pad))
    # The filter works in device pixels, so the sigma shrinks with the surface.
    scv.drawPath(p, paint(C(rgb, alpha), blur=sigma / s))
    cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(sw, sh_),
                     skia.Rect.MakeXYWH(b.left() - pad, b.top() - pad, vw, vh),
                     skia.SamplingOptions(skia.FilterMode.kLinear,
                                          skia.MipmapMode.kNone))




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
    # One line when a subtitle follows, the rest of the band when it does not.
    # A specimen's claim is long and factual — "Figures 0–9 less 0 9 · Lowercase
    # a–j drawn as capitals" — and a 40px slot makes it wrap with nowhere to go,
    # which ships the sheet with the font's name missing.
    band = 40 if ctx["copy"].get("sub") else sh.h - sh.m - int(round(210 * sh.vscale))
    # `exact` keeps the prefix as written. The specimen sheets report a range
    # ("Lowercase a–j"), and title-casing it into "A–J" claims letters the sheet
    # does not show; the pins' "Set in" ships as "Set In", so that stays.
    footer_copy = ("Display Specimen" if ctx.get("_support_render") else
                   f"{at} {tc(ctx['name'])}" if exact
                   else tc(f"{at} {ctx['name']}"))
    sh.text("name", L, footer_copy,
            Box(sh.m, sh.h - int(round(210 * sh.vscale)), sh.w - 2 * sh.m, band),
            hi=27 * sh.scale, lo=18 * sh.scale, color=ink, track=0.16, align="left",
            valign="top", min_read=18 * sh.scale)
    if ctx["copy"].get("sub"):
        sbox = Box(sh.m, sh.h - int(round(172 * sh.vscale)), sh.w - 2 * sh.m, 34)
        gnd = sh._behind(sbox)
        sh.text("sub", L, tc(ctx["copy"]["sub"]), sbox,
                hi=20 * sh.scale, lo=14 * sh.scale,
                color=readable(gnd, mute, 4.5) if gnd else mute,
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
        # Every glyph's own box has to be offset by where its pen came down:
        # `getBounds()` is path-local, and the pen walks right by the advances.
        # Register the row without that offset and its ink rect sits back near
        # x=0, which makes the canvas checks for the row vacuous.
        pen, edges = x, []
        for j, p in enumerate(paths):
            b = p.getBounds()
            edges.append((pen + b.left(), pen + b.right()))
            pen += widths[j] + gap
        x0, x1 = min(e[0] for e in edges), max(e[1] for e in edges)
        sh.mark(f"{prefix}{i}", Box(x0, y, x1 - x0, bot_i - top_i))
        y += (bot_i - top_i) + lead
    return y


def contour_density(T, text, size=500.0):
    """How much outline a face draws per unit of the area it covers.

    Scale-invariant, so two faces can be compared on two words. A one-weight
    gothic gives away a whole letter for the price of one stroke; an extruded
    sports face spends a hundred verbs on each counter. The first can be grown
    to the measure and still read at feed size, the second turns to mush there
    — and it also eats the byte budget, because a PNG pays for edges and a busy
    contour is nothing but edges.
    """
    p, _ = T.path(text, size)
    b = p.getBounds()
    return p.countVerbs() / max(b.width() * b.height() / 1000.0, 1.0)


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
        rb = Box(stage.x, y, stage.w, ih + 2)
        gnd = sh._behind(rb)
        tn = tone(P, i)
        if gnd is not None:
            tn = _lift(tn, gnd, min_contrast)
        sh.text(f"{prefix}{i}", T, s, rb,
                hi=size, lo=size, leading=0.86, max_lines=1, min_read=min_read,
                valign="top", min_contrast=min_contrast,
                **tn)
        y += ih + lead
    return y - lead


def arc_text(sh, T, text, cx, cy, r, size, sweep=None, up=True, color=None,
             track=0.0, name="arc", alpha=1.0, features=None, collide=True):
    """NEW module-level helper (belongs here, next to fit_measure/measure_rows):
    set a run along an invisible circle, rotated to the tangent.

    Shaping is done ONCE over the whole phrase with HarfBuzz (`T.runs`), so
    kerning pairs and ligatures survive: a ligature is one positioned glyph in
    the shaped run, and only the placement rotates, never the shaping. Each
    glyph's advance midpoint rides the circle of radius `r` about (cx, cy);
    `sweep` is the angle in radians the run subtends — None takes the natural
    sweep for this advance at this radius. `up=True` arches over the centre
    (letters hang above the circle, apex at the top); `up=False` arches under
    it. The union ink AABB is registered with `sh.mark`, so the off-canvas and
    overlap checks see the arch like any other slot. Returns the ink Box or
    None. Caveat for reuse: per-glyph rotation breaks the pen joins of a
    connected script mid-word — set arch phrases in caps or title case.
    """
    if not text or not text.strip() or r <= 0 or size <= 0:
        return None
    gs = T.runs(text, size, features)
    if not gs:
        return None
    f = T.font(size)
    # One pass to shape and measure: a glyph's slot on the arc is as wide as its
    # INK if the ink overruns the advance (swashy italics do), so rotated glyphs
    # never ride into each other; its own ink centre, not its pen origin, is what
    # rides the circle.
    items = []
    for gid, adv, xo, yo in gs:
        gp = f.getPath(gid)
        b = gp.getBounds()
        step = max(adv, 0.0) if b.isEmpty() else max(adv, b.width())
        items.append((gp, b, xo, yo, step))
    total = sum(it[4] for it in items) + track * max(len(items) - 1, 0)
    th = float(sweep) if sweep else total / r
    if th <= 0 or th > 2.6:
        sh.problems.append(f"{name}: {th:.2f} rad of arc will not read as lettering")
        return None
    q = paint(C(color, alpha)) if isinstance(color, tuple) \
        else paint(color or skia.Color4f(0, 0, 0, alpha))
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    pen, drawn = 0.0, 0
    for gp, b, xo, yo, step in items:
        mid = pen + step / 2.0 - total / 2.0
        pen += step + track
        if b.isEmpty():
            continue
        a = mid / r
        sa, ca = math.sin(a), math.cos(a)
        px = cx + r * sa
        py = (cy - r * ca) if up else (cy + r * ca)
        ox = xo - (b.left() + b.right()) / 2.0
        oy = -yo
        gp.offset(ox, oy)
        sh.cv.save()
        sh.cv.translate(px, py)
        sh.cv.rotate(math.degrees(a))
        sh.cv.drawPath(gp, q)
        sh.cv.restore()
        for lx, ly in ((b.left() + ox, b.top() + oy), (b.right() + ox, b.top() + oy),
                       (b.left() + ox, b.bottom() + oy),
                       (b.right() + ox, b.bottom() + oy)):
            wx, wy = px + lx * ca - ly * sa, py + lx * sa + ly * ca
            x0, y0 = min(x0, wx), min(y0, wy)
            x1, y1 = max(x1, wx), max(y1, wy)
        drawn += 1
    if not drawn:
        return None
    box = Box(x0, y0, x1 - x0, y1 - y0)
    sh.mark(name, box, collide=collide)
    return box


def brush_swash(sh, name, cx, cy, half_len, thick, rgb, alpha=1.0, bow=0.62):
    """A sign-writer's divider: one closed lens, needle-thin at both tips.

    Not a stroked path — a filled outline whose two edges are quadratics that
    meet at the tips, so the stroke is thick at its middle and tapers to a
    point at each end, the way a flat brush comes off the board. The control
    points sit left of centre (the belly hangs over the entry, not the exit)
    and both edges bow upward by `bow` half-widths, which is what gives the
    swash its lifted, painted arc. Registers its ink box so verify() rules.
    """
    b = bow * thick
    p = skia.Path()
    p.moveTo(cx - half_len, cy)
    p.quadTo(cx - half_len * 0.30, cy - b - thick, cx + half_len, cy)
    p.quadTo(cx - half_len * 0.30, cy - b + thick, cx - half_len, cy)
    p.close()
    _fill(sh.cv, p, rgb, alpha)
    top = cy - (b + thick) / 2.0
    bot = cy + max(0.0, (thick - b)) / 2.0
    sh.mark(name, Box(cx - half_len, top, 2 * half_len, bot - top))


def _wash_stroke(left, right, top, bot, seed=7):
    """The outline of one loaded brush: fat at the middle, off-thin at the tips,
    with both long edges wandering a few pixels so it is a stroke, not a pill."""
    rnd = random.Random(seed)
    n = 6
    span, height = right - left, bot - top
    taper, amp = height * 0.11, height * 0.055

    def y_at(i, base, sign):
        pinch = taper * (1.0 - math.sin(math.pi * i / n))
        wander = 0.0 if i in (0, n) else amp * rnd.uniform(-1, 1)
        return base + sign * pinch + wander

    pts = [(left + span * i / n, y_at(i, top, 1.0)) for i in range(n + 1)]
    pts += [(left + span * (n - i) / n, y_at(n - i, bot, -1.0))
            for i in range(1, n + 1)]
    m = len(pts)
    p = skia.Path()
    p.moveTo(*pts[0])
    for i in range(m):
        p1, p2 = pts[i], pts[(i + 1) % m]
        p0, p3 = pts[i - 1], pts[(i + 2) % m]
        p.cubicTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                  p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
    p.close()
    return p


def wash_band(sh, cx, cy, half_w, half_h, base, deep, light, alpha=1.0):
    """A painted watercolour stripe, laid at 1/BG_SCALE and stretched.

    The one device in the catalogue that has to pass for paint: pigment pooling
    along a wet rim, the way a loaded brush comes off paper. It is painted small
    and upscaled bilinearly like `bg()`, but it gets no gaussian feather, and
    that is the whole point of drawing it this way: a blur
    makes every one of its pixels a different number, and PNG pays per pixel, so
    a soft-edged band across a 2400-px sheet costs 250 KB of nothing. A hard
    outline with flat tone *between* the edges costs 30 KB — and the two-step
    bloom below, four device pixels wide, is invisible at feed size anyway.
    Everything uneven about the wash is therefore an *edge*: the wandering
    outline, the rim where the pigment stopped. Edges are what a sheet can afford
    to draw; fields of varying tone are what it cannot. `base` is the body
    the ink stands on, `deep` the pooled rim, `light` the bloom. Registers with
    `collide=False` because the lettering is meant to ride through it.
    """
    s = BG_SCALE
    pad = 10                                  # bloom margin, in low-res px
    bw = max(2, int(2 * half_w / s) + 2 * pad)
    bh = max(2, int(2 * half_h / s) + 2 * pad)
    sub = skia.Surface.MakeRasterN32Premul(bw, bh)
    if sub is None:
        return
    cv = sub.getCanvas()
    p = pad * 0.5
    # two steps of bloom outside the body: at four device pixels a step, the
    # give reads as a soft edge and costs the sheet two outlines, not a field
    for inset, aa in ((0.0, 0.14), (p * 0.45, 0.24)):
        cv.drawPath(_wash_stroke(inset, bw - inset, inset, bh - inset),
                    paint(C(light, aa * alpha)))
    body = _wash_stroke(p, bw - p, p, bh - p)
    cv.drawPath(body, paint(C(base, 0.94 * alpha)))
    cv.save()
    cv.clipPath(body)
    # pigment pools at the wet edge: one wide stroke of the outline, kept inside
    # the body by the clip, so the rim darkens wherever the brush wandered. A
    # vector edge costs two more outline pixels, not a field of them.
    cv.drawPath(body, paint(C(deep, 0.30 * alpha), style=skia.Paint.kStroke_Style,
                            width=bh * 0.13))
    cv.restore()
    sh.cv.drawImageRect(
        sub.makeImageSnapshot(), skia.Rect.MakeWH(bw, bh),
        skia.Rect.MakeXYWH(cx - half_w - pad * s, cy - half_h - pad * s,
                           2 * half_w + 2 * pad * s, 2 * half_h + 2 * pad * s),
        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone))
    sh.mark("wash", Box(cx - half_w, cy - half_h, 2 * half_w, 2 * half_h),
            collide=False, bleed=True)


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
    """The ground under a specimen: untextured by device, and textured by the pack.

    `tooth=0` is parity with the Pillow sheets these replace, not thrift — a
    specimen is the one image in the package that has to be *right*, and 9000
    circles of noise over a 2400x1600 field costs near-entropy bytes to say
    nothing. `dev=False` is the other half: `device()` counts its steps against a
    1500-px page, so its bands walk off a landscape sheet. The furniture a sheet
    needs is drawn by the body, in the box it actually has. Flat in the *device*
    sense, then — not in the other one, which is the complaint: a specimen or a
    support that is one continuous-tone gradient reads as pasted, and the ground
    texture is what puts the press back under it. Pass `tex=0` to get the old sheet.
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
        sh.notes.append(f"numerals: the face carries {len(figs)} of the ten figures")
    if len(marks) < 4:
        sh.notes.append(f"numerals: only {len(marks)} punctuation marks to show")
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


def family_profile(font_path, primary_tt=None):
    """Find distinct sibling styles in the same typographic font family.

    Format twins (.otf/.ttf) count once. Weight-family specimen panels use the
    nearest real light, regular, and bold siblings rather than simulating weight
    by stretching a single outline.
    """
    path = Path(font_path).resolve()
    owns_tt = primary_tt is None
    primary = primary_tt or TTFont(str(path), fontNumber=0, lazy=True)
    names = primary["name"]
    family = (names.getDebugName(16) or names.getDebugName(1) or "").strip()
    if owns_tt:
        primary.close()
    if not family:
        return {"family_styles": [], "family_style_count": 1,
                "weight_paths": {}, "weight_labels": {},
                "sample_paths": [], "sample_labels": []}

    records = {}
    for candidate in sorted(path.parent.iterdir()):
        if candidate.suffix.casefold() not in {".otf", ".ttf"}:
            continue
        try:
            face = TTFont(str(candidate), fontNumber=0, lazy=True)
            face_names = face["name"]
            face_family = (face_names.getDebugName(16)
                           or face_names.getDebugName(1) or "").strip()
            if face_family.casefold() != family.casefold():
                face.close()
                continue
            style = (face_names.getDebugName(17)
                     or face_names.getDebugName(2) or "Regular").strip()
            weight = int(getattr(face["OS/2"], "usWeightClass", 400))
            selection = int(getattr(face["OS/2"], "fsSelection", 0))
            post = face["post"] if "post" in face else None
            italic = bool(selection & (1 | (1 << 9))) or bool(
                post and abs(float(getattr(post, "italicAngle", 0.0))) > 0.01
            ) or any(token in style.casefold() for token in ("italic", "oblique"))
            face.close()
            key = (style.casefold(), weight)
            prior = records.get(key)
            # Prefer OTF when an identical style is shipped in both formats.
            if prior is None or candidate.suffix.casefold() == ".otf":
                records[key] = {"path": candidate, "style": style,
                                "weight": weight, "italic": italic}
        except Exception:
            continue

    styles = sorted(records.values(), key=lambda item: (item["weight"], item["style"].casefold()))
    upright = [row for row in styles if not row["italic"]]
    light = [row for row in upright if row["weight"] <= 250]
    regular = [row for row in upright if 300 <= row["weight"] <= 550]
    bold = [row for row in upright if row["weight"] >= 600]
    picked = {}
    for label, group in (("light", light), ("regular", regular), ("bold", bold)):
        if group:
            picked[label] = min(group, key=lambda row: abs(
                row["weight"] - {"light": 200, "regular": 400, "bold": 700}[label]))
    if len({str(row["path"]) for row in picked.values()}) < 3:
        picked = {}
    if picked:
        sample = [picked[key] for key in ("light", "regular", "bold")]
    else:
        # Family boards are useful for any actual multi-style family, not only
        # the rare Light/Regular/Bold triplet. Prefer upright siblings, then use
        # another real style (including italic) only when that is what exists.
        sample_pool = upright if len(upright) >= 2 else styles
        if len(sample_pool) <= 3:
            sample = sample_pool
        else:
            indices = sorted({round(i * (len(sample_pool) - 1) / 2)
                              for i in range(3)})
            sample = [sample_pool[i] for i in indices]
    return {"family_styles": styles,
            "family_style_count": max(1, len(styles)),
            "weight_paths": {label: row["path"] for label, row in picked.items()},
            "weight_labels": {label: row["style"] for label, row in picked.items()},
            "sample_paths": [row["path"] for row in sample],
            "sample_labels": [row["style"] for row in sample]}


def family_style_label(family_name, style_name):
    """Format an actual sibling-style name without duplicating its family."""
    family_name = str(family_name or "").strip()
    style_name = str(style_name or "").strip()
    if family_name and family_name.casefold() not in style_name.casefold():
        return f"{family_name} {style_name}".strip()
    return style_name or family_name


def real_italic_sibling(ctx):
    """Choose the nearest actual Italic style in this font's detected family."""
    current_path = Path(ctx["font_path"]).resolve()
    styles = ctx.get("family_styles", [])
    current = next((style for style in styles
                    if Path(style["path"]).resolve() == current_path), None)
    candidates = [style for style in styles
                  if style.get("italic") and
                  Path(style["path"]).resolve() != current_path]
    if not candidates:
        return None
    current_weight = current.get("weight", 400) if current else 400
    return min(candidates, key=lambda style: (
        abs(style.get("weight", 400) - current_weight),
        any(token in style.get("style", "").casefold()
            for token in ("condensed", "narrow")),
        style.get("style", "").casefold(), str(style["path"])))


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
    family_data = family_profile(font_path, tt)
    weight_faces = {key: Type(value)
                    for key, value in family_data["weight_paths"].items()}
    family_samples = [
        {"label": label, "face": Type(face_path), "path": Path(face_path).resolve()}
        for label, face_path in zip(family_data["sample_labels"],
                                    family_data["sample_paths"])
    ]
    return {
        "facts": facts, "chars": {chr(cp) for cp in cmap}, "flagged": flagged,
        "name": name, "copy": copy,
        "display": display, "label": Type(LABEL_B if LABEL_B.exists() else LABEL),
        "tt": tt,
        "family": family, "why": why, "class": cls,
        "font_path": Path(font_path).resolve(),
        "family_styles": family_data["family_styles"],
        "family_style_count": family_data["family_style_count"],
        "family_weight_faces": weight_faces,
        "family_weight_labels": family_data["weight_labels"],
        "has_weight_triplet": len(weight_faces) == 3,
        "family_samples": family_samples,
        "themes": assign_themes(name, sorted(cls_names(cls)), cls),
        "tone_offs": {}, "briefed": False,
        "palette_override": palette, "mode_override": mode,
    }


FLOWING = ("script", "brush", "blackletter", "swashy")


def tc(text):
    """Capitalize each word and turn shouty source copy into Title Case.

    Mixed case is preserved after each word's initial, so foundry names such as
    OpenType keep their spelling while all-caps copy no longer forces capitals
    on display faces that have useful lowercase forms.
    """
    urls = []

    def save_url(match):
        marker = f"\ue000{len(urls)}\ue001"
        urls.append(match.group(0))
        return marker

    text = re.sub(r"(?:https?://|www\.)[^\s]+", save_url, str(text),
                  flags=re.IGNORECASE)

    def title_word(match):
        word = match.group(0)
        initial = word[0].upper()
        rest = word[1:].lower() if word.upper() == word else word[1:]
        return initial + rest

    text = re.sub(r"[^\W\d_]+(?:['’][^\W\d_]+)*", title_word, text,
                  flags=re.UNICODE)
    return re.sub(r"\ue000(\d+)\ue001",
                  lambda match: urls[int(match.group(1))], text)


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
        if name in SUPPORT_ORDER:
            # A support panel is an authored picture like a pin: it wears the
            # world it was rolled, never the class's single specimen ground.
            key = THEME_PREF[name][0]
        else:
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
    support_class_themes = {
        "line32", "duo32", "card32", "feature32", "neon32", "quote32",
        "crest32", "hand32", "boots32",
    }
    if ctx["class"] == "blackletter" and name in support_class_themes:
        th["mode"] = "dark"
        colors = ((18, 18, 20), (34, 34, 36), (244, 241, 233),
                  (223, 220, 211), (19, 19, 21), (255, 253, 247),
                  (190, 160, 105), (165, 165, 160))
    else:
        colors = PALETTES[th["pal"]]
    pal = dict(zip(("deep1", "deep2", "paper1", "paper2", "ink", "glow",
                    "accent", "accent2"), colors))
    pal["mode"] = th["mode"]
    pal["tone"] = tones(pal, ctx["family"])
    pal["tone_off"] = ctx.get("tone_offs", {}).get(name, 0)
    return th, pal


def clean(ctx, text):
    """Drop what the face does not carry, so no slot ever renders tofu."""
    return "".join(c for c in text
                   if (c in ctx["chars"] or c.isspace()) and c not in ctx["flagged"])


def _copy_tokens(text):
    return re.findall(r"[^\W_]+", (text or "").casefold(), flags=re.UNICODE)


def _support_has_font_name(ctx, text):
    name = _copy_tokens(ctx.get("name", ""))
    words = _copy_tokens(text)
    return bool(name and any(words[i:i+len(name)] == name
                             for i in range(len(words)-len(name)+1)))


SUPPORT_STOCK_COPY = frozenset({
    "whisky", "whiskey", "midnight letters and loud labels",
    "invitation suite editorial packaging",
})


def _support_copy(ctx, keys, fallback):
    """Pick authored specimen copy while keeping the thumbnail's name unique."""
    for key in keys:
        candidate = " ".join(clean(ctx, ctx["copy"].get(key) or "").split())
        if (candidate and candidate.casefold() not in SUPPORT_STOCK_COPY
                and not _support_has_font_name(ctx, candidate)):
            return tc(candidate)
    candidate = " ".join(clean(ctx, fallback).split())
    if _support_has_font_name(ctx, candidate):
        candidate = "Letterforms In Motion"
    return tc(candidate)


def panel_text(ctx, pool=()):
    """What a support panel sets when the point of the panel is not the name.

    The catalogue was built as a run of name cards and it reads as eight sheets
    printing the same word — the shop saying it looked at the face once and
    photographing it from eight angles. So the display text of a panel is authored
    copy first: `word` if there is one, otherwise a short phrase from `line` (four
    words is the most a lockup can take before the size it lands at stops being the
    design's point). Only when nobody authored anything does a panel fall back to
    its own `pool` — a small vocabulary of things that suit that particular picture,
    rotated by the font's name so two faces of the same shape do not both ship
    "OPENING NIGHT". A candidate is taken only when the face draws every letter of
    it, because a bitten word is a worse sheet than a repeated name. If neither
    authored copy nor the panel vocabulary works, it uses a generic specimen label;
    the font name never fills this slot.
    """
    for key in ("word", "line"):
        candidate = " ".join(clean(ctx, ctx["copy"].get(key) or "").split())
        if (candidate and (key != "line" or len(candidate.split()) <= 4)
                and candidate.casefold() not in SUPPORT_STOCK_COPY
                and not _support_has_font_name(ctx, candidate)):
            return tc(candidate)
    if pool:
        rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
        for cand in pool[rot % len(pool):] + pool[:rot % len(pool)]:
            if (not _support_has_font_name(ctx, cand)
                    and all(usable(ctx, ch) for ch in cand if not ch.isspace())):
                return tc(cand)
    return _support_copy(ctx, (), "Type Study")


def rolled(ctx, pool):
    """One line out of a panel's own vocabulary, chosen by the font's name.

    The small companion type on a support panel is the one place a template cannot
    fall back on the face's own lettering to decide what to say, so without a roll
    every font in the shop would ship the same lead-in. Rotating on the name keeps
    one font's series identical to itself on a re-run, which is the same bargain
    `assign_themes` strikes with colour.
    """
    rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
    return tc(pool[rot % len(pool)])


def support_render_copy(ctx, text):
    """Clean every support string, including fixed furniture, against the face.

    The name/stock-copy guard cannot stop at authored brief fields: a fixed
    headline can coincidentally equal the showcased font's name too. Keep the
    layout's text box alive with a short generic replacement in that rare case.
    """
    candidate = clean(ctx, text or "")
    normalized = " ".join(candidate.split())
    stock = " ".join(_copy_tokens(normalized)) in SUPPORT_STOCK_COPY
    if normalized and not stock and not _support_has_font_name(ctx, normalized):
        return tc(candidate)
    for fallback in ("Type", "Form", "Print", "Glyph", "Letters"):
        replacement = clean(ctx, fallback)
        if (replacement and replacement.casefold() not in SUPPORT_STOCK_COPY
                and not _support_has_font_name(ctx, replacement)):
            return tc(replacement)
    return ""


# The words every foundry reaches for when it has not thought of one, and which
# therefore say nothing about the face in front of them. A brief that authors one of
# these as a lead-in has not authored anything, so the panel rolls its own instead.
STOCK_LEAD = ("introducing", "now available", "new release", "coming soon",
              "announcing", "just released", "launch day", "available now")


def lead_in(ctx, pool):
    """The authored lead-in above the type, unless it is a stock announcement word."""
    asked = " ".join(clean(ctx, ctx["copy"].get("over") or "").split()).strip()
    if asked and asked.lower() not in STOCK_LEAD:
        return tc(asked)
    return rolled(ctx, pool)


def render(name, ctx, frame_override=None):
    fn, _blurb, _cls, frame = TEMPLATES[name]
    frame = frame_override or frame
    fw, fh = FRAMES[frame]
    surf = skia.Surface.MakeRasterN32Premul(fw, fh)
    sh = Sheet(surf)
    th, pal = theme_for(name, ctx)
    copy = {k: clean(ctx, v or "") for k, v in ctx["copy"].items()}
    if name in SUPPORT_ORDER:
        for key, value in copy.items():
            if (" ".join(_copy_tokens(value)) in SUPPORT_STOCK_COPY
                    or _support_has_font_name(ctx, value)):
                copy[key] = ""
    ctx = dict(ctx, copy=copy, _support_render=name in SUPPORT_ORDER,
               th=th, pal=pal)
    sh._support_ctx = ctx if name in SUPPORT_ORDER else None
    fn(sh, ctx)
    return surf, sh


SUPPORT_HTML_CATALOG = (Path(__file__).resolve().parents[2] / "font-factory" /
                        "support-html" / "catalog.json")
try:
    _support_html_catalog = json.loads(SUPPORT_HTML_CATALOG.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise RuntimeError(f"cannot read support HTML catalogue: {SUPPORT_HTML_CATALOG}: {exc}") from exc
SUPPORT_HTML_SPECS = {
    item["id"]: item for item in _support_html_catalog.get("templates", [])
    if item.get("htmlEntry") and item.get("portStatus") in {"prototype", "ported"}
}
SUPPORT_HTML_RENDERERS = frozenset(SUPPORT_HTML_SPECS)


def render_support_html(name, ctx, destination, ratio="3x2", review_mode=False):
    """Render a migrated support layout with Chromium, then verify its frame."""
    if name not in SUPPORT_HTML_RENDERERS:
        raise ValueError(f"no HTML/CSS renderer is registered for {name}")
    root = SUPPORT_REF_DIR.parent
    spec = SUPPORT_HTML_SPECS[name]
    script = root / "support-html" / "render_template.mjs"
    if not script.is_file():
        raise SystemExit(f"HTML support renderer is missing: {script}")
    family_args = []
    label_args = []
    if name in HTML_ONLY_SUPPORT:
        fallbacks = {
            "palmello32": "Palmello", "quietattempt32": "Quiet Attempt",
            "hushglow32": "Hush And Glow", "italianhorror32": "Italian Horror",
            "dreamwarriors32": "Dream Warriors", "nesting32": "The Nesting",
            "erotica32": "Erotica", "conspiracytheory32": "Conspiracy Theory",
            "overglow32": "Overglow", "pinkvice32": "Pink Vice",
            "attitude32": "Attitude", "indieground32": "Indieground Font Foundry",
            "caramelsundae32": "Caramel Sundae",
            "sweettreat32": "Sweet Treat Dreams",
            "saucystack32": "Saucy Stack",
            "anteliascard32": "Antelias",
            "peacebreath32": "Keep Your Mind Open To Peace Make Space To Slow Down And Breathe",
            "nyccoffee32": "New York Coffee Shops",
            "afterhours32": "After Hours",
            "outofoffice32": "Out Of Office",
            "skincareroutine32": "Night Skincare Routine",
            "youlookgood32": "You Look Good Today",
            "spiritadventure32": "Spirit Of Adventure",
            "dreamfollow32": "Follow Your Dreams",
            "angelinastyle32": "Angelina Jolie",
            "comesnatural32": "Do What Comes Natural",
            "calmafterstorm32": "Calm After The Storm",
            "beachclub32": "Beach Club",
            "splitampersand32": "Letters Matter",
            "setrum32": "Setrum",
            "nectarambience32": "Nector Ambience",
            "fluorescentduo32": "Fluorescent Adolescent",
            "sacharon32": "Sacharon",
            "lastnightsweden32": "Last Night In Sweden",
            "crywolf32": "Cry Wolf",
            "welcomemorning32": "Welcome Morning",
            "esens32": "ESENS",
            "asbon32": "ASBON",
            "italicregular32": "Family Member Sample vs Current Style Sample Aa",
            "smokeletters32": "fh",
            "blackerwear32": "Blacker Wear Trendy Fashion",
            "silentnight32": "Silent Night",
            "playgrid32": "Pickle 2037 Play 82 69 45",
            "fridayrunning32": "Friday Running 20 Club 25",
            "medievalcreatures32": "medieval creatures 1348 manuscript and bestiaries",
            "littlemadquote32": "We All Go A Little Mad Sometimes Psycho 1960",
            "soulrevenge32": "Soul's Revenge The Dragon Knight 1987 A Legend Awakens",
            "allworkplay32": "All work and no play makes Jack a dull boy All play and no work makes Jack a mere toy",
            "sociato32": "Sociato Quirky Type",
            "owlstory32": "The Owl Who Couldn’t Sleep",
            "hazysky32": "Hazy Sky Session IPA",
            "itsokay32": "it's Okay Fenotype Studios POSTRE Tasty Display Type",
            "nightonearth32": "Night on earth",
            "goodthingstothose32": "Good things come to those who Lurk Mull Sniggle Garble Scuttle",
            "rudybrownie32": "Rudy Brownie",
            "spaceprint32": "HOLO 2023",
            "scriptgrid32": "Decline Courier Pianist Interim Actuals Fruited Rolling",
            "smashcourt32": "Smash Court Elevate Your Potential Master the Court Own the Match Unleash Your Potential on the Court Elevate Your Game",
            "scriptpattern32": "Everyday Time Sometimes Moon Sunday",
            "brushpanel32": "Orchid North Design Fresh Believe to Achieve Vivid Boutique",
            "avalonbrush32": "Avalon Font Specimen",
            "ssrange32": "S/S Range New Vogue Fashion Lettering",
            "allsummerlong32": "All Summer Long",
            "boldcampaign32": "Cool Sh*t We've Done This Week Give Away We're Hiring 8 Brands Killin' It Right Now",
            "goodtimeroll32": "Let The Good Times Roll",
            "childhoodbook32": "This book Read naked remind me about my Childhood",
            "playerglyph32": "Player your game manifestation",
            "alicebadge32": "Rabbits Go Ask Alice Follow The White Rabbit",
            "notallroads32": "NOT all roads ARE simple,",
            "practicehard32": "Practice HARD Train HARD Work HARD Play HARDER",
            "rainbowstack32": "RAINBOW RAINBOW RAINBOW RAINBOW",
            "wakefamous32": "WAKE ME UP WHEN I'M FAMOUS!",
            "sexyshout32": "Sexy Shout",
            "embracesexiest32": "Embrace The Sexiest With Bold And Simplicity",
            "crimsonportrait32": "Own The Moment",
            "statueframe32": "Make A Lasting Impression",
            "portraitcard32": "A Quiet Confidence",
            "warmportrait32": "Softly In Focus",
            "fashioncard32": "Made To Be Seen",
            "cinemaportrait32": "Stay With The Story",
            "parkstatement32": "A Shared Beginning",
            "numeralfolio32": "0123456789",
            "timechange32": "Time Change 380",
            "bottleoffer32": "Bottle Offer Equipped With Ligatures",
            "bootzyfear32": "I Live In Fear I Have No Beer I Sleep In Jail And Everything Fails",
            "bootzyalmost32": "Almost Almost",
            "bootzygraphic32": "Graphic Design Is Easy With Type Mania",
            "bootzybunny32": "Your Love Is Weird",
            "quadfont32": "Dark Bold Modern Font",
            "mythicallions32": "Sea Lions Coastal Study",
            "lifeinblackwhite32": "Life In Black And White",
            "romanstrips32": "Velvet Grace Silhouette Novella Whisper Serenade",
            "floraltriptych32": "Flowers Are Nature’s Poetry Bloom",
            "homequote32": "Home Is More Than Just A Place Where We Find Comfort",
        }
        fallback = fallbacks.get(name)
        if fallback is None:
            # New source-led HTML templates own their copy in the editor module;
            # use the readable catalogue id as a glyph probe when no explicit
            # renderer sample has been authored for that entry yet.
            fallback = name.removesuffix("32").replace("-", " ")
        candidate = panel_text(ctx, (fallback,))
        missing = sorted({character for character in candidate
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected display copy has unsupported glyphs; Chromium will "
                "use a readable fallback for: " + " ".join(missing))
        props = {"warnings": warnings}
        if name in {"numeralfolio32", "timechange32"}:
            props.update({"fontType": ctx["family"]})
        elif name in {"crimsonportrait32", "statueframe32", "portraitcard32",
                    "warmportrait32", "fashioncard32", "cinemaportrait32",
                    "parkstatement32"}:
            props.update({"headline": support_render_copy(ctx, candidate)})
        elif name == "welcomemorning32":
            words = candidate.split()
            if len(words) == 1:
                words.append(words[0])
            lines = pack_lines(words, 2)
            props.update({"lineOne": lines[0].upper(),
                          "lineTwo": lines[1].upper() if len(lines) > 1 else ""})
        elif name == "esens32":
            props.update({"headline": candidate.upper(),
                          "caption": "LOTION BEAUTY SKINCARE"})
        elif name == "asbon32":
            props.update({"headline": candidate.upper()})
        elif name == "awakeportrait32":
            props.update({"headline": support_render_copy(ctx, "Awake").upper()})
        elif name == "calgarywelcome32":
            props.update({"eyebrow": support_render_copy(ctx, "Welcome to"),
                          "headline": support_render_copy(ctx, "Calgary")})
        elif name == "peacebreath32":
            headline = clean(
                ctx, "keep your mind\nopen to PEACE\nmake space to\nslow down and\nBREATHE")
            props.update({"headline": headline})
        elif name == "italicregular32":
            styles = ctx.get("family_styles", [])
            current_path = Path(ctx["font_path"]).resolve()
            current = next((style for style in styles
                            if Path(style["path"]).resolve() == current_path), None)
            siblings = [style for style in styles
                        if Path(style["path"]).resolve() != current_path]
            if current is None or not siblings:
                raise ValueError(
                    "italicregular32 requires a distinct sibling font in the same family")
            opposite_style = [style for style in siblings
                              if style["italic"] != current["italic"]]
            sibling = min(opposite_style or siblings, key=lambda style: (
                abs(style["weight"] - current["weight"]),
                any(token in style["style"].casefold()
                    for token in ("condensed", "narrow")),
                style["style"].casefold(), str(style["path"])))
            props.update({
                "leftLabel": f"{sibling['style']} Sample",
                "rightLabel": f"vs {current['style']} Sample",
                # Use identical specimen text in both panels so the comparison
                # demonstrates the sibling face rather than uppercase vs lowercase.
                "leftGlyph": "Aa", "rightGlyph": "Aa",
            })
            family_args.extend(["--family-font", str(sibling["path"])])
        elif name == "smokeletters32":
            props.update({"leftGlyph": "f", "rightGlyph": "h"})
        elif name == "blackerwear32":
            props.update({"leftTitle": "Blacker", "leftTagline": "Wear",
                          "rightTitle": "Trendy", "rightItalic": "Fashion",
                          "bodyCopy": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."})
        elif name == "silentnight32":
            props.update({"leftWord": "Silent", "rightWord": "Night"})
        elif name == "nesting32":
            props.update({"headline": "Nesting", "pretitle": "The"})
        elif name == "skincareroutine32":
            props.update({"headline": "night & skincare\nROUTINE"})
        elif name == "youlookgood32":
            props.update({"headline": "you look\ngood today"})
        elif name == "spiritadventure32":
            props.update({"headline": "the Spirit\nof\nAdventure"})
        elif name == "dreamfollow32":
            props.update({"headline": "follow your dreams\nno matter what!"})
        elif name == "comesnatural32":
            props.update({"headline": "Do\nWhat\nComes\nNatural"})
        elif name == "splitampersand32":
            props.update({"headline": "Letters\nMatter"})
        elif name == "nectarambience32":
            props.update({"headline": "Nector Ambience"})
        elif name == "playgrid32":
            props.update({"topLeft": "hora nocte", "topRight": "neyro mono",
                          "label": "Pickle", "year": "2037", "gridTitle": "PLAY",
                          "topNumber": "82", "leftNumber": "69",
                          "rightNumber": "45", "bottomNumber": "82"})
        elif name == "fridayrunning32":
            props.update({"topLeftLabel": "HORA NOCTE", "topRightLabel": "NEYRO MONO",
                          "topTitle": "FRIDAY", "headline": "RUNNING",
                          "leftNumber": "20", "club": "CLUB", "rightNumber": "25",
                          "footerLeft": "6 STYLES", "footerRight": "© 2025"})
        elif name == "medievalcreatures32":
            props.update({"topLine": "medieval creatures", "yearLine": "{1348}",
                          "bottomLine": "manuscript and bestiaries"})
        elif name == "littlemadquote32":
            props.update({"topLeft": "Hora Nocte", "topRight": "HN Relvick",
                          "lineOne": "We All Go", "lineTwo": "A Little Mad",
                          "lineThree": "Sometimes", "attribution": "Psycho (1960)",
                          "footerLeft": "20 Styles",
                          "footerRight": "All Right Reserved © 2026"})
        elif name == "soulrevenge32":
            props.update({"cinemaCredit": "23 CINEMAS PRESENT",
                          "titleOne": "Soul’s", "titleTwo": "Revenge",
                          "director": "A Film By Daniel V. Harrington",
                          "castOne": "Victor\nWHITMORE",
                          "castTwo": "Eleanor\nGRAVES",
                          "castThree": "Isabella\nCROWE",
                          "castFour": "Lucas\nBLACKWOOD",
                          "dragonTitle": "THE DRAGON KNIGHT",
                          "yearOne": "1", "yearTwo": "9",
                          "yearThree": "8", "yearFour": "7",
                          "dragonTagline": "A LEGEND AWAKENS"})
        elif name == "allworkplay32":
            props.update({"lineOne": "All work and no play",
                          "lineTwo": "makes Jack a dull boy,",
                          "lineThree": "All play and no work",
                          "lineFour": "makes Jack a mere toy."})
        elif name == "sociato32":
            props.update({"initial": "R", "highlight": "Quirky.",
                          "bodyCopy": "Perfect for modern trends, it’s a typeface full of character. The typeface was inspired by a declaration published during the French Revolution that extolled the development of a new religion, the cult of the Supreme Being. It’s a stunning piece of work, with a wild, baroque layout and hand drawn typography. It’s a veritable goldmine of typographic ideas."})
        elif name == "owlstory32":
            props.update({"titleLineOne": "The", "titleLineTwo": "Owl",
                          "captionOne": "WHO", "captionTwo": "COULDN’T",
                          "captionThree": "SLEEP"})
        elif name == "hazysky32":
            props.update({"headlineOne": "hazy", "headlineTwo": "sky",
                          "caption": "SESSION IPA"})
        elif name == "itsokay32":
            props.update({"headlineOne": "it's", "headlineTwo": "Okay!",
                          "studioOne": "Fenotype", "studioTwo": "Studios",
                          "footer": "POSTRE - TASTY DISPLAY TYPE"})
        elif name == "nightonearth32":
            props.update({"headlineOne": "Night on", "headlineTwo": "earth."})
        elif name == "goodthingstothose32":
            props.update({"brandLetter": "F", "lineOne": "Good things",
                          "lineTwo": "come to those", "lineThree": "who",
                          "period": ".", "optionOne": "Lurk", "optionTwo": "Mull",
                          "optionThree": "Sniggle", "optionFour": "Garble",
                          "optionFive": "Scuttle", "checkedOption": 2})
        elif name == "rudybrownie32":
            props.update({"lineOne": "Rudy", "lineTwo": "Brownie",
                          "displayScale": 1})
        elif name == "spaceprint32":
            props.update({"topWord": "HOLO", "year": "2023",
                          "displayScale": 1})
        elif name == "scriptgrid32":
            name_table = ctx["tt"]["name"]
            family_label = (name_table.getDebugName(16)
                            or name_table.getDebugName(1)
                            or ctx["name"]).strip()
            designer = (name_table.getDebugName(9) or "Family Specimen").strip()
            props.update({
                "familyName": family_label,
                "typeLabel": "Type Specimen",
                "creatorLabel": designer,
                "formatLabel": "OpenType",
                **{f"word{i + 1}": word for i, word in enumerate(
                    ("Decline", "Courier", "Pianist", "Interim",
                     "Actuals", "Fruited", "Decline", "Rolling"))},
                "displayScale": 1,
            })
        elif name == "smashcourt32":
            props.update({
                "lineOne": "“Smash Court",
                "lineTwo": "Elevate Your",
                "lineThree": "Potential”",
                "rightCaption": "MASTER THE\nCOURT\nOWN THE\nMATCH",
                "footerCaption": "UNLEASH YOUR\nPOTENTIAL ON THE COURT\nELEVATE YOUR GAME",
                "displayScale": 1,
            })
        elif name == "scriptpattern32":
            props.update({
                "word1": "Everyday",
                "word2": "Time",
                "word3": "Sometimes",
                "word4": "Moon",
                "word5": "Sunday",
                "displayScale": 1,
            })
        elif name == "brushpanel32":
            props.update({
                "topWordOne": "Orchid",
                "topWordTwo": "North",
                "topCaption": "DESIGN",
                "repeatWord": "#FRESH",
                "beliefWord": "Believe",
                "connector": "TO",
                "achievement": "Achieve",
                "bottomWord": "Vivid",
                "bottomCaption": "BOUTIQUE",
                "displayScale": 1,
            })
        elif name == "avalonbrush32":
            props.update({"mainWord": "Avalon", "displayScale": 1})
        elif name == "ssrange32":
            props.update({"lineOne": "S/S_RANGE", "lineTwo": "NEW_vogue",
                          "displayScale": 1})
        elif name == "allsummerlong32":
            name_table = ctx["tt"]["name"]
            family_label = (name_table.getDebugName(16)
                            or name_table.getDebugName(1)
                            or ctx["name"]).strip()
            props.update({"lineOne": "ALL", "lineTwo": "Summer",
                          "lineThree": "Long", "familyLabel": family_label,
                          "displayScale": 1})
        elif name == "boldcampaign32":
            name_table = ctx["tt"]["name"]
            family_label = (name_table.getDebugName(16)
                            or name_table.getDebugName(1)
                            or ctx["name"]).strip()
            props.update({
                "coolLineOne": "Cool Sh*t",
                "coolLineTwo": "We've Done",
                "coolLineThree": "This Week",
                "giveLineOne": "GIVE",
                "giveLineTwo": "AWAY",
                "hireLineOne": "We're",
                "hireLineTwo": "HIRING",
                "brandsLineOne": "8 Brands",
                "brandsLineTwo": "Killin' it",
                "brandsLineThree": "Right Now",
                "familyLabel": family_label,
                "displayScale": 1,
            })
        elif name == "goodtimeroll32":
            words = candidate.split()
            lines = pack_lines(words, 2)
            props.update({
                "lineOne": lines[0] if lines else "Let the Good",
                "lineTwo": lines[1] if len(lines) > 1 else "Times Roll!",
                "displayScale": 1,
            })
        elif name == "childhoodbook32":
            props.update({
                "lineOneLead": "This book",
                "lineOneAccent": "Read",
                "lineTwoAccent": "naked",
                "lineTwoLead": "remind",
                "lineThree": "me about my",
                "lineFour": "Childhood...",
                "displayScale": 1,
            })
        elif name == "playerglyph32":
            props.update({
                "monogram": "Q",
                "headline": "Player",
                "secondLine": "your game",
                "thirdLine": "manifestation",
                "displayScale": 1,
            })
        elif name == "alicebadge32":
            props.update({
                "topText": "RABBITS · GO ASK ALICE",
                "bottomText": "FOLLOW THE WHITE RABBIT",
                "displayScale": 1,
            })
        elif name == "notallroads32":
            italic_member = real_italic_sibling(ctx)
            use_italic_sibling = italic_member is not None
            if use_italic_sibling:
                family_args.extend(["--family-font", str(italic_member["path"])])
            props.update({
                "topLine": "NOT",
                "secondLine": "all roads",
                "thirdLine": "ARE",
                "bottomLine": "simple,",
                "displayScale": 1,
                "useItalicSibling": use_italic_sibling,
            })
        elif name == "practicehard32":
            italic_member = real_italic_sibling(ctx)
            use_italic_sibling = italic_member is not None
            if use_italic_sibling:
                family_args.extend(["--family-font", str(italic_member["path"])])
            props.update({
                "verbOne": "Practice", "powerOne": "HARD",
                "verbTwo": "Train", "powerTwo": "HARD",
                "verbThree": "Work", "powerThree": "HARD",
                "verbFour": "Play", "powerFour": "HARDER",
                "displayScale": 1,
                "useItalicSibling": use_italic_sibling,
            })
        elif name == "rainbowstack32":
            props.update({
                "outlineOne": "RAINBOW", "solidOne": "RAINBOW",
                "outlineTwo": "RAINBOW", "solidTwo": "RAINBOW",
                "displayScale": 1,
            })
        elif name == "wakefamous32":
            props.update({
                "lineOne": "WAKE ME UP",
                "lineTwo": "WHEN I'M",
                "lineThree": "FAMOUS!",
                "displayScale": 1,
            })
        elif name == "sexyshout32":
            italic_member = real_italic_sibling(ctx)
            use_italic_sibling = italic_member is not None
            if use_italic_sibling:
                family_args.extend(["--family-font", str(italic_member["path"])])
            props.update({
                "lineOne": "Sexy",
                "lineTwo": "Shout",
                "displayScale": 1,
                "useItalicSibling": use_italic_sibling,
            })
        elif name == "embracesexiest32":
            props.update({
                "eyebrowOne": "TYPE STUDY",
                "eyebrowTwo": "DISPLAY FORM",
                "headline": "Embrace",
                "article": "The",
                "highlight": "Sexiest",
                "tagline": "with bold & simplicity",
                "displayScale": 1,
            })
        elif name == "sweettreat32":
            lines = pack_lines(candidate.split(), min(3, len(candidate.split())))
            props.update({f"line{i+1}": lines[i] if i < len(lines) else ""
                          for i in range(3)})
        elif name == "amberquote32":
            # Keep the five-line editable source quote from the editor config;
            # a short generic phrase breaks this layout's hierarchy.
            pass
        elif name in {"quietattempt32", "dreamwarriors32", "conspiracytheory32",
                      "indieground32", "caramelsundae32"}:
            props["headline"] = "\n".join(pack_lines(
                candidate.split(), min(2, len(candidate.split()))))
        else:
            props["headline"] = candidate
    elif name == "line32":
        raw = " ".join(_support_copy(ctx, ("line", "word"),
                                     "Letters That Matter").split())
        words = raw.split()
        if not words or len(words) > 4:
            words = "Letters That Matter".split()
        headline = tc(" ".join(words).lower())
        lines = pack_lines(headline.split(), min(2, len(headline.split())))
        overline = " ".join(clean(ctx, ctx["copy"].get("over") or "").split())
        overline = tc((overline or "New Release").lower())
        edge = tc(EDGE(ctx).lower())
        missing = sorted({character for text in (headline, overline, edge,
                                                  "Display Specimen")
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these broadside characters; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        paper_one = palette["deep1"] if dark else palette["paper1"]
        paper_two = palette["deep2"] if dark else palette["paper2"]
        ink = readable(lum(paper_one), palette["glow"] if dark else palette["ink"], 4.5)
        accent = readable(lum(paper_one), palette["accent"], 4.5)
        muted = mix(ink, paper_two, .4)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        to_rgb = lambda color: " ".join(str(int(channel)) for channel in color)
        echo = (len(lines) > 1 and ctx["family"] not in FLOWING
                and contour_density(ctx["display"], lines[0]) < 0.5)
        props = {
            "headline": headline, "lines": lines,
            "overline": overline, "edge": edge,
            "footer": "Display Specimen",
            "ink": to_hex(ink), "accent": to_hex(accent),
            "muted": to_hex(muted),
            "paperOne": to_hex(paper_one), "paperTwo": to_hex(paper_two),
            "inkRgb": to_rgb(ink), "accentRgb": to_rgb(accent),
            "mutedRgb": to_rgb(muted),
            "dark": dark, "pool": .05 if dark else .021,
            "device": theme["device"], "echo": echo,
            "warnings": warnings,
        }
        label_args = ["--label-font", str(root / "support-html" / "assets" /
                                             "NotoSans-CondensedLight.ttf")]
    elif name == "rio32":
        title_the, title_city = "The", "Janeiro"
        if _support_has_font_name(ctx, title_city):
            title_city = "Rio"
        subtitle = "The Weekend Holiday Trip"
        booking = "Book Now"
        footer = (
            "Happiness Consists Of Living Each Day As If It Were The First Day\n"
            "Of Your Honeymoon And The Last Day Of Your Vacation\n"
            "Trust Your Holiday Plans With Us"
        )
        copy = (title_the, title_city, subtitle, booking, *footer.splitlines())
        missing = sorted({character for text in copy for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these Rio travel copy glyphs; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        props = {"titleThe": title_the, "titleCity": title_city,
                 "subtitle": subtitle, "booking": booking, "footer": footer,
                 "imageScale": 1, "imageX": 50, "imageY": 50,
                 "titleScale": 1, "subtitleScale": 1, "footerScale": 1,
                 "cream": "#f6efdc", "shadow": "#241c19",
                 "warnings": warnings}
        label_args = ["--label-font", str(root / "support-html" / "assets" /
                                             "NotoSans-CondensedLight.ttf")]
    elif name == "card32":
        language = _card_language(ctx)
        if language is None:
            language = {"word": "Always", "phrase": "Made To Be Read",
                        "cap": "In Hand", "foot": "Fresh From The Bench"}
        language = {key: tc(value.lower()) for key, value in language.items()}
        word_lines = pack_lines(language["word"].split(),
                                min(2, len(language["word"].split())))
        phrase_words = language["phrase"].split()
        phrase_lines = pack_lines(phrase_words,
                                  min(3, max(2, len(phrase_words))))
        theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        ground = palette["deep1"] if dark else palette["paper1"]
        ground_two = palette["deep2"] if dark else palette["paper2"]
        base = palette["glow"] if dark else palette["ink"]
        paper_candidates = (
            palette["paper1"], palette["paper2"],
            mix(palette["paper1"], palette["glow"], .5),
            mix(palette["deep1"], palette["paper2"], .45),
            palette["deep1"], palette["deep2"],
        )
        bench_lum = lum(mix(ground, ground_two, .36))
        paper = max(paper_candidates,
                    key=lambda color: contrast_lum(bench_lum, lum(color)))
        paper_back = mix(paper, (255, 255, 255) if lum(paper) < .45
                         else (0, 0, 0), .10)
        ink = readable(lum(ground), mix(base, palette["accent"], .40), 4.5)
        ink_on_paper = readable(lum(paper), base, 4.5)
        accent_on_paper = readable(lum(paper), palette["accent"], 4.5)
        muted_on_paper = readable(lum(paper), mix(base, paper, .42), 4.5)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        to_rgb = lambda color: " ".join(str(int(channel)) for channel in color)
        missing = sorted({character for text in
                          (language["word"], language["phrase"])
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these paper-stack glyphs; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        props = {
            **language, "caption": language["cap"],
            "wordLines": word_lines, "phraseLines": phrase_lines,
            "footer": "Display Specimen", "edge": tc(EDGE(ctx).lower()),
            "ground": to_hex(ground), "groundTwo": to_hex(ground_two),
            "paper": to_hex(paper), "paperBack": to_hex(paper_back),
            "ink": to_hex(ink), "accent": to_hex(palette["accent"]),
            "muted": to_hex(muted_on_paper),
            "inkRgb": to_rgb(ink), "accentRgb": to_rgb(palette["accent"]),
            "mutedRgb": to_rgb(muted_on_paper),
            "paperBackRgb": to_rgb(paper_back),
            "inkOnPaper": to_hex(ink_on_paper),
            "accentOnPaper": to_hex(accent_on_paper),
            "device": theme["device"], "deviceOpacity": .50,
            "warnings": warnings,
        }
        label_args = ["--label-font", str(root / "support-html" / "assets" /
                                             "NotoSans-CondensedLight.ttf")]
    elif name in {"plakat32", "plakatart32", "birvase32", "weightfamily32",
                  "mangosboard32", "ovalword32", "stardust32", "blossom32",
                  "neue32", "electromagnetic32"}:
        # Source-backed HTML layouts share the same Title Case and glyph-safety
        # rules as their Skia counterparts. Alphabet rows and symbol runs stay
        # literal specimen data; new phrases keep the case they are meant to use.
        fallback_copy = {
            "plakat32": ("headline", "Plakat"),
            "plakatart32": ("headline", "Plakat"),
            "birvase32": ("headline", "Birvase"),
            "mangosboard32": ("headline", "Variable"),
            "ovalword32": ("headline", "Sadie"),
            "neue32": ("repeated", "Neue!"),
        }
        values = {}
        if name in fallback_copy:
            key, fallback = fallback_copy[name]
            if name in {"birvase32", "plakatart32", "mangosboard32",
                        "ovalword32", "neue32"}:
                candidate = _support_word(ctx, fallback).split()
                candidate = candidate[0] if candidate else fallback
            else:
                candidate = _support_copy(ctx, ("line", "word"), fallback)
            rendered_copy = support_render_copy(ctx, candidate)
            values[key] = (rendered_copy.upper() if name == "neue32"
                           else tc(rendered_copy))
        if name == "stardust32":
            values.update({"lineTwo": tc("Studio"),
                           "eyebrow": tc("Type Studio"),
                           "footer": tc("In Good Company")})
        elif name == "plakat32":
            styles = ctx.get("family_styles", [])
            upright = [style for style in styles if not style.get("italic")]
            style_pool = upright or styles
            fvar = ctx["tt"]["fvar"] if "fvar" in ctx["tt"] else None
            variable_axes = getattr(fvar, "axes", [])
            italic = (any(style.get("italic") for style in styles) or
                      any(axis.axisTag in {"ital", "slnt"} for axis in variable_axes))
            weight_axis = next((axis for axis in variable_axes
                                if axis.axisTag == "wght"), None)
            weight_values = [float(style["weight"]) for style in style_pool
                             if style.get("weight") is not None]
            minimum = (float(weight_axis.minValue) if weight_axis else
                       min(weight_values, default=100.0))
            maximum = (float(weight_axis.maxValue) if weight_axis else
                       max(weight_values, default=900.0))
            current = float(ctx.get("facts", {}).get("weight", 400))
            marker_one = ((current - minimum) / (maximum - minimum)
                          if maximum > minimum else .5)
            style_labels = [tc(style.get("style", "")) for style in style_pool
                            if style.get("style")]
            weight_name = lambda value: (
                "Thin" if value <= 250 else "Light" if value <= 350 else
                "Regular" if value <= 450 else "Medium" if value <= 550 else
                "Bold" if value <= 700 else "Black")
            left_style = (style_labels[0] if style_labels else
                          weight_name(minimum))
            right_style = (style_labels[-1] if len(style_labels) > 1 else
                           weight_name(maximum))
            style_count = max(1, int(ctx.get("family_style_count") or
                                     len(style_labels) or 1))
            glyph_count = int(ctx.get("facts", {}).get("glyphs") or 0)
            style_word = "Style" if style_count == 1 else "Styles"
            values.update({"note": f"{glyph_count} Glyphs\n"
                                    f"{style_count} Available {style_word}",
                           "railOne": left_style,
                           "railTwo": "Roman",
                           "railRightOne": right_style,
                           "railRightTwo": "Italic" if italic else "No Italic",
                           "markerOne": max(.04, min(.96, marker_one)),
                           "markerTwo": .92 if italic else .08,
                           "variable": tc("Variable" if "fvar" in ctx["tt"]
                                          else "Family"),
                           "footer": tc("A Variable Typeface Study" if "fvar" in ctx["tt"]
                                         else "A Typeface Family Study")})
        elif name == "plakatart32":
            styles = ctx.get("family_styles", [])
            upright = [style for style in styles if not style.get("italic")]
            style_pool = upright or styles
            fvar = ctx["tt"]["fvar"] if "fvar" in ctx["tt"] else None
            variable_axes = getattr(fvar, "axes", [])
            weight_axis = next((axis for axis in variable_axes
                                if axis.axisTag == "wght"), None)
            weight_values = [float(style["weight"]) for style in style_pool
                             if style.get("weight") is not None]
            minimum = (float(weight_axis.minValue) if weight_axis else
                       min(weight_values, default=400.0))
            maximum = (float(weight_axis.maxValue) if weight_axis else
                       max(weight_values, default=400.0))
            weight_name = lambda value: (
                "Thin" if value <= 250 else "Light" if value <= 350 else
                "Regular" if value <= 450 else "Medium" if value <= 550 else
                "Bold" if value <= 700 else "Black")
            italic_axis = any(axis.axisTag in {"ital", "slnt"}
                              for axis in variable_axes)
            has_italics = italic_axis or any(style.get("italic")
                                             for style in styles)
            style_count = max(1, int(ctx.get("family_style_count") or 1))
            style_word = "Style" if style_count == 1 else "Styles"
            weight_range = (weight_name(minimum) if maximum == minimum else
                            f"{weight_name(minimum)} · {weight_name(maximum)}")
            values.update({
                "metaStyles": f"{style_count} {style_word}",
                "metaVariable": "Variable Font" if "fvar" in ctx["tt"] else "Static Font",
                "metaWeights": weight_range,
                "metaItalics": "Italics Available" if has_italics else "Upright Only",
                "metaDesigned": "Designed By",
                "metaFoundry": "Mabütype",
                "metaYear": "2025",
            })
        elif name == "weightfamily32":
            alphabet = "".join(ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                               if usable(ctx, ch))
            split = (len(alphabet) + 1) // 2
            alphabet_rows = alphabet[:split] + "\n" + alphabet[split:]
            values.update({"row1": alphabet_rows, "row2": alphabet_rows,
                           "row3": alphabet_rows})
            samples = ctx.get("family_samples", [])
            values["familySampleCount"] = len(samples)
            for index, sample in enumerate(samples, 1):
                values[f"label{index}"] = tc(sample["label"])
        elif name == "mangosboard32":
            glyphs = "C€Ω½?†qTTD0123456789"
            name_table = ctx["tt"]["name"]
            family_name = (name_table.getDebugName(16)
                           or name_table.getDebugName(1)
                           or ctx.get("name", "Family"))
            values.update({"glyphs": glyphs,
                           "variable": tc("Variable" if "fvar" in ctx["tt"]
                                          else "Family"),
                           "tileA": "Aa", "tileWord": tc("Mangos"),
                           "tileAt": "@"})
            samples = ctx.get("family_samples", [])
            values["familySampleCount"] = len(samples)
            for index, sample in enumerate(samples, 1):
                keys = ("familyThin", "familyRegular", "familyBlack")
                if index <= len(keys):
                    values[keys[index - 1]] = tc(
                        f"{family_name} {sample['label']}")
        elif name == "ovalword32":
            values.update({"kicker": tc("T&N Type Co."),
                           "sub": tc("Display Sans")})
        elif name == "blossom32":
            values.update({"kicker": tc("A Retreat For The Senses"),
                           "subhead": tc("Restore Your Natural Rhythm"),
                           "body": tc("A Place To Rest And Reconnect.\n"
                                      "Gentle Rituals Support Your Natural Rhythm.\n"
                                      "Time To Return To Yourself."),
                           "button": tc("Book A Visit")})
        elif name == "neue32":
            values.update({"pillTop": tc("Instant"), "pillMid": tc("Type"),
                           "pillBottom": tc("Form"),
                           "metaLeft": tc("Type Study / 01"),
                           "metaRight": tc("Display Sans Design"),
                           "footer": tc("A Study In Geometric Form")})
        elif name == "electromagnetic32":
            values.update({"kickerLeft": tc("Type Study / 03"),
                           "kickerRight": tc("Frequency / Field"),
                           "footerLeft": tc("Noise / Light / Motion"),
                           "footerRight": tc("Type / 03")})
        all_copy = [str(value) for value in values.values()]
        missing = sorted({character for text in all_copy
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks some source-layout glyphs; Chromium "
                "will use a readable fallback for: " + " ".join(missing))
        props = {**values, "scale": 1, "warnings": warnings}
        label_args = []
        if name in {"weightfamily32", "mangosboard32"}:
            for sample in ctx.get("family_samples", []):
                family_args.extend(["--family-font", str(sample["path"])])
    elif name == "roadrunner32":
        label_path = LABEL_B if LABEL_B.exists() else LABEL
        lines = support_render_copy(
            ctx, "Got the radio\non, I'm like the\nroadrunner.")
        descriptor = support_render_copy(
            ctx, "Distinctive letterforms with spirit,\npersonality and motion.")
        body = support_render_copy(
            ctx, "A lively typeface can make a message stand out,\n"
                 "and leave a lasting impression.")
        badge = support_render_copy(ctx, "Nektar")
        props = {"headline": lines, "descriptor": descriptor, "body": body,
                 "badge": badge}
        if ctx["class"] == "blackletter":
            props.update({"lime": "#171719", "ink": "#f6f2e9",
                          "pink": "#b89f71"})
        label_args = ["--label-font", str(label_path)]
    elif name == "mountain32":
        words = ("Diabolically", "Equalizing", "Revaluation", "Pandemic",
                 "Submachine", "Challenger")
        missing = sorted({character for word in words for character in word
                          if not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these mountain specimen glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {"scale": 1, "artScale": 1, "wordScale": 1,
                 "numberScale": 1, "rowStep": .145, "wordLeft": .455,
                 "warnings": warnings}
        label_args = []
    elif name == "contactlist32":
        rows = ("01.Misread", "02.Cayman Island", "03.Homesick",
                "04.Boat Behind", "05.Rumours", "06.Renegade",
                "07.Summer On", "The Westhill")
        missing = sorted({character for text in rows for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these index-list glyphs; Chromium will "
                "draw them with a readable fallback: " + " ".join(missing))
        props = {"rows": list(rows), "scale": 1, "rowStep": .091,
                 "top": .12, "left": .12, "width": .76,
                 "trackLabel": "Track List", "numberLabel": "No. 07",
                 "warnings": warnings}
        label_args = []
    elif name == "messageframe32":
        lines = ("You Will Look Back", "On These Days And",
                 "Be So Grateful You", "Made It Through")
        missing = sorted({character for line in lines for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these message glyphs; Chromium will "
                "draw them with a readable fallback: " + " ".join(missing))
        props = {"scale": 1, "top": .245, "rowStep": .13,
                 "tracking": -.012, "warnings": warnings}
        label_args = []
    elif name == "cliffpostcard32":
        headlines = ("Wander Where", "Your Soul Feels Wild.")
        missing = sorted({character for line in headlines for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these postcard headline glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {"scale": 1, "top": .195, "gap": .14,
                 "tracking": -.02, "warnings": warnings}
        label_args = []
    elif name == "kindersea32":
        headlines = ("I Wish You", "A Kinder Sea.")
        missing = sorted({character for line in headlines for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these postcard headline glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {"scale": 1, "artScale": 1, "top": .648,
                 "rowStep": .15, "tracking": -.012,
                 "warnings": warnings}
        label_args = []
    elif name == "sunsetpromise32":
        headlines = ("Every", "Sunset Brings", "The Promise Of", "A New Day")
        missing = sorted({character for line in headlines for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these sunset headline glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {"scale": 1, "artScale": 1, "top": .305,
                 "lineSpacing": 0, "tracking": -.012, "outline": .006,
                 "warnings": warnings}
        label_args = []
    elif name == "phonegarden32":
        visible = ("Covent", "Garden",
                   "Timeless", "Charm,", "Rooted In", "Grace.")
        missing = sorted({character for line in visible for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these phone-screen glyphs; Chromium "
                "will draw them with a readable fallback: "
                + " ".join(missing))
        props = {"scale": 1, "centerScale": .9, "tracking": -.012,
                 "rightSpacing": .073, "warnings": warnings}
        label_args = []
    elif name == "pixelquote32":
        lines = ("A Little", "Nonsense", "Now & Then", "Is Relished By",
                 "The Wisest Man")
        missing = sorted({character for line in lines for character in line
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these quote glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        props = {"scale": 1, "lineSpacing": 0, "tracking": -.018,
                 "warnings": warnings}
        label_args = []
    elif name == "ravencover32":
        copy = ("Present By", "Muksal Creative", "Raven Court",
                "Modern Serif Display Font",
                "Regular & Italic Font")
        missing = sorted({character for text in copy for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these cover glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        props = {"masthead": copy[0], "issue": copy[1], "headline": copy[2],
                 "subtitle": copy[3], "details": copy[4], "scale": 1,
                 "top": .365, "tracking": -.035, "captionScale": 1,
                 "shade": .20, "warnings": warnings}
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "confident32":
        headline = "Confident"
        copy = (headline, "Keep Looking", "Elthia Typeface",
                "Even When", "Doubt Looks Back")
        missing = sorted({character for text in copy for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these poster glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        props = {"headline": headline, "overline": copy[1], "tag": copy[2],
                 "taglineLeft": copy[3], "taglineRight": copy[4],
                 "scale": 1, "top": .155, "tracking": -.04,
                 "taglineScale": 1, "eyeScale": 1,
                 "warnings": warnings}
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "focusposter32":
        candidate = " ".join(_support_copy(ctx, ("word",), "Focused").split())
        if len(candidate.split()) != 1:
            candidate = "Focused"
        headline = tc(candidate.lower())
        columns = (
            "Staying\nAvoiding\nAbout\nThat\nYour",
            "Focused\nDistractions,\nEmbracing\nComes From\nTruest",
            "Is",
            "Not\nBut\nThe",
            "About\nClarity\nPursuing\nIntentions.",
        )
        fixed_text = " ".join(columns)
        missing = sorted({character for text in (headline, fixed_text)
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these focus-poster characters; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        props = {"headline": headline, "columns": list(columns),
                 "warnings": warnings}
        label_args = []
    elif name == "wideclaim32":
        copy = ("A Typeface Is", "A Visual Voice", "Wide")
        font_type = ctx["family"]
        missing = sorted({character for text in (*copy, font_type) for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these specimen characters; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        props = {"lineOne": copy[0], "lineTwo": copy[1],
                 "wordOne": copy[2], "fontType": ctx["family"],
                 "warnings": warnings}
        label_args = []
    elif name == "neon32":
        headline = "La Dolce\nMarea"
        coming_soon = "Coming Soon"
        requested = f"{headline}\n{coming_soon}"
        missing = sorted({character for character in requested
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these marquee glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        _theme, palette = theme_for(name, ctx)
        props = {"headline": headline, "comingSoon": coming_soon,
                 "scale": 1, "glowStrength": .78, "gateStrength": .82,
                 "wall": "#" + "".join(f"{c:02x}" for c in palette["deep1"]),
                 "tube": "#" + "".join(f"{c:02x}" for c in palette["glow"]),
                 "glow": "#" + "".join(f"{c:02x}" for c in palette["accent"]),
                 "gate": "#" + "".join(f"{c:02x}" for c in palette["paper1"]),
                 "warnings": warnings}
        label_args = []
    elif name == "quote32":
        headline = support_render_copy(
            ctx, _support_copy(ctx, ("line", "word"), "Just Like Sweet Chocolate"))
        _theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        paper = palette["deep1"] if dark else palette["paper1"]
        ink = readable(lum(paper), palette["glow"] if dark else palette["ink"], 4.5)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        props = {"headline": headline, "paper": to_hex(paper),
                 "ink": to_hex(ink), "quotes": usable(ctx, '"')}
        label_args = []
    elif name == "mirror32":
        quote = {
            "line1": "People Hasten",
            "line2": "To Judge",
            "line3": "In Order",
            "line4": "Not To Be",
            "line5": "Judged",
            "line6": "Themselves",
        }
        missing = sorted({character for text in quote.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these mirror-quote glyphs; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        props = {**quote, "scale": 1, "tracking": -.026,
                 "portraitScale": 1, "portraitX": 5,
                 "warnings": warnings}
        label_args = []
    elif name == "crest32":
        word = shout(ctx, _support_copy(
            ctx, ("word", "line"), "Ordinary")).strip()
        top = _support_copy(ctx, ("line", "over"), "Escape From")
        bottom = _support_copy(ctx, ("sub",), "Adventure")
        _theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        paper = palette["deep1"] if dark else palette["paper1"]
        ink = readable(lum(paper), palette["glow"] if dark else palette["ink"], 4.5)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        props = {"headline": support_render_copy(ctx, word),
                 "top": support_render_copy(ctx, top),
                 "bottom": support_render_copy(ctx, bottom),
                 "arcFont": "label" if ctx["family"] in FLOWING else "display",
                 "paper": to_hex(paper), "ink": to_hex(ink)}
        label_path = LABEL_B if LABEL_B.exists() else LABEL
        label_args = ["--label-font", str(label_path)]
    elif name == "feature32":
        labels = feature_callout_labels(ctx)
        candidate = _support_copy(ctx, ("word", "line"), "Crystal")
        label_tokens = {token.casefold() for text in labels for token in text.split()}
        hero_words = [word.strip(".,!?;:()[]{}\"'") for word in candidate.split()]
        hero_words = [word for word in hero_words
                      if len(word) >= 3 and word.casefold() not in label_tokens]
        hero = max(hero_words, key=lambda word: ctx["display"].measure(word, 100.0),
                   default="Crystal")
        hero = support_render_copy(ctx, shout(ctx, clean(ctx, hero)).strip())
        _theme, palette = theme_for(name, ctx)
        paper = palette["paper1"]
        ink, accent = palette["ink"], palette["accent"]
        ground_lum = lum(paper)
        ink = readable(ground_lum, ink, 5.5)
        accent = readable(ground_lum, accent, 5.0)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        props = {"headline": hero, "topLabel": labels[0],
                 "bottomLabel": labels[1], "paper": to_hex(paper),
                 "ink": to_hex(ink), "accent": to_hex(accent)}
        label_args = []
    elif name == "hand32":
        _theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        ground = palette["deep1"] if dark else palette["paper1"]
        type_ink = readable(lum(ground), palette["glow"] if dark else palette["ink"], 4.5)
        hand_ink = readable(lum(ground), palette["accent"], 4.5)
        note_ink = type_ink if dark else readable(lum(ground), palette["ink"], 4.5)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        props = {"nice": "Nice", "big": "Big", "font": "Font",
                 "note": "Sometimes You\nJust Need A...",
                 "ground": to_hex(ground), "ink": to_hex(type_ink),
                 "handInk": to_hex(hand_ink), "noteInk": to_hex(note_ink)}
        label_path = LABEL_B if LABEL_B.exists() else LABEL
        label_args = ["--label-font", str(label_path)]
    elif name == "duo32":
        _theme, palette = theme_for(name, ctx)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        display = shout(ctx, _support_copy(ctx, ("word", "line"), "California")).strip()
        tagline = _support_copy(ctx, ("sub",), "knows how to party").strip()
        # Match render_support(), which blanks catalogue-wide stock subtitles
        # after normalizing punctuation before the individual layout runs.
        if " ".join(_copy_tokens(tagline)) in SUPPORT_STOCK_COPY:
            tagline = "knows how to party"
        dark = palette["mode"] == "dark"
        ground, ground_light = ((palette["deep1"], palette["deep2"]) if dark
                                else (palette["paper1"], palette["paper2"]))
        sun = palette["accent"]
        ink = readable(lum(sun), palette["glow"] if dark else palette["ink"], 2.2)
        silhouette = palette["deep1"] if dark else palette["ink"]
        props = {"word": support_render_copy(ctx, display),
                 "tagline": tagline,
                 "ground": to_hex(ground), "groundLight": to_hex(ground_light),
                 "sun": to_hex(sun), "ink": to_hex(ink),
                 "silhouette": to_hex(silhouette), "grain": 31}
        label_args = []
    elif name == "mangos32":
        _theme, palette = theme_for(name, ctx)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        if ctx.get("palette_override"):
            ground, paper, cyan, orange = (
                palette["deep1"], palette["paper1"],
                palette["accent"], palette["accent2"])
        else:
            ground, paper, cyan, orange = (
                (13, 15, 15), (244, 244, 239), (35, 201, 229), (247, 112, 28))
        props = {
            "wordmark": support_render_copy(ctx, "Mangos"),
            "foundry": support_render_copy(ctx, "Mabütype"),
            "latinName": support_render_copy(ctx, "Mangifera indica L."),
            "energyCaption": support_render_copy(ctx, "Energy provided"),
            "trademark": clean(ctx, "™"),
            "weight": 400, "tracking": -0.045,
            "ground": to_hex(ground), "paper": to_hex(paper),
            "cyan": to_hex(cyan), "orange": to_hex(orange),
        }
        label_args = []
    elif name == "storyteller32":
        props = {"scale": 1}
        label_args = []
    elif name == "yearposter32":
        year = " ".join(str(ctx.get("copy", {}).get("word") or "1982").split())
        year = year or "1982"
        if (_support_has_font_name(ctx, " ".join(year.split()))
                or year.casefold() in SUPPORT_STOCK_COPY):
            year = "1982"
        missing = sorted({character for character in year
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these year glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        props = {"year": year, "warnings": warnings}
        label_args = []
    elif name == "soldier32":
        specimen = {
            "year": "1935",
            "thisLine": "This",
            "warLine": "War Is",
            "uselessLine": "Useless",
            "digits": "1234567890",
            "symbols": "!?$¢€£&",
        }
        missing = sorted({character for text in
                          [specimen["year"], specimen["thisLine"],
                           specimen["warLine"], specimen["uselessLine"],
                           specimen["digits"], specimen["symbols"]]
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these archival specimen glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {**specimen, "warnings": warnings}
        label_args = []
    elif name == "voguecover32":
        _theme, palette = theme_for(name, ctx)
        paper_rgb = (249, 247, 241)
        red_rgb = readable(lum(paper_rgb),
                           mix((222, 9, 28), palette["accent"], .07), 3.0)
        to_hex = lambda color: "#" + "".join(f"{int(c):02x}" for c in color)
        specimen = {
            "masthead": "Vogue",
            "submast": "Japan",
            "issue": "March\nIssue",
            "leftKicker": "Discover",
            "leftStory": "The New\nStreet Fashion\nTrends From",
            "destination": "Tokyo",
            "lowerKicker": "Reina Sato",
            "lowerStory": "Shows You How\nTo Take The\nPerfect Selfie",
            "featureLines": "Sakura\nYamaguchi",
            "featureNote": "The Making Of\nAsia's Next\nTop Model",
            "footerLead": "Follow Us On Social Media",
            "footerNote": "Facebook / Instagram / TikTok",
        }
        fallbacks = {
            "masthead": "Vogue", "submast": "Japan", "issue": "March\nIssue",
            "leftKicker": "Discover",
            "leftStory": "The New\nStreet Fashion\nTrends From",
            "destination": "Tokyo",
            "lowerKicker": "Reina Sato",
            "lowerStory": "Shows You How\nTo Take The\nPerfect Selfie",
            "featureLines": "Sakura\nYamaguchi",
            "featureNote": "The Making Of\nAsia's Next\nTop Model",
            "footerLead": "Follow Us On Social Media",
            "footerNote": "Facebook / Instagram / TikTok",
        }
        guarded = {}
        for key, value in specimen.items():
            normalized = " ".join(value.split())
            if (_support_has_font_name(ctx, normalized)
                    or normalized.casefold() in SUPPORT_STOCK_COPY):
                value = _support_copy(ctx, (), fallbacks[key])
            guarded[key] = value
        missing = sorted({character for text in guarded.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these editorial cover glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {**guarded, "paper": to_hex(paper_rgb),
                 "red": to_hex(red_rgb), "ink": "#111112",
                 "warnings": warnings}
        label_args = []
    elif name == "demolition32":
        specimen = {
            "row1": "Beh-Ago",
            "row2": "Demolition",
            "row3": "Abnormal(Ey)",
            "row4": "Mal-Out",
            "caption": "Normal Area (000-0385)",
        }
        fallbacks = {
            "row1": "Type-Form",
            "row2": "Lettering",
            "row3": "Print Study",
            "row4": "Form-Out",
            "caption": "Field Type (000-0385)",
        }
        guarded = {}
        for key, value in specimen.items():
            normalized = " ".join(value.split())
            if (_support_has_font_name(ctx, normalized)
                    or normalized.casefold() in SUPPORT_STOCK_COPY):
                value = _support_copy(ctx, (), fallbacks[key])
            guarded[key] = value
        missing = sorted({character for text in guarded.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these poster glyphs; Chromium will draw "
                "them with a readable fallback: " + " ".join(missing))
        props = {**guarded, "ink": "#121014", "warnings": warnings}
        label_args = []
    elif name == "boots32":
        _theme, palette = theme_for(name, ctx)
        dark = palette["mode"] == "dark"
        ground = palette["deep1"] if dark else palette["paper1"]
        ink = readable(lum(ground), palette["glow"] if dark else palette["ink"], 4.5)
        accent = readable(lum(ground), palette["accent"], 3.0)
        to_hex = lambda color: "#" + "".join(f"{int(channel):02x}" for channel in color)
        specimen = {"title": "Wild Boots", "subtitle": "Photography"}
        missing = sorted({character for text in specimen.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these western-poster glyphs; "
                "Chromium will draw them with a readable fallback: "
                + " ".join(missing))
        props = {**specimen, "ground": to_hex(ground), "ink": to_hex(ink),
                 "accent": to_hex(accent), "warnings": warnings}
        label_args = []
    elif name == "stadiumposter32":
        requested = "Real Madrid"
        missing = sorted({character for character in requested
                          if not character.isspace() and not usable(ctx, character)})
        headline = support_render_copy(ctx, requested) or "North Stand"
        warnings = []
        if missing:
            warnings.append(
                "Unsupported stadium headline characters were omitted: "
                + " ".join(missing))
        props = {"headline": headline, "warnings": warnings}
        label_args = []
    elif name == "signalclock32":
        requested = " ".join((ctx.get("copy", {}).get("word") or "$50.50").split())
        if (not requested or requested.casefold() in SUPPORT_STOCK_COPY
                or _support_has_font_name(ctx, requested)):
            requested = "$50.50"
        missing = sorted({character for character in requested
                          if not character.isspace() and not usable(ctx, character)})
        # Preserve the source string. Chromium will use its readable fallback
        # for missing glyphs instead of dropping zeroes from the price.
        value = requested
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these price glyphs; Chromium will draw "
                "them with a readable fallback: "
                + " ".join(missing))
        props = {"value": value, "label": "Dollar", "warnings": warnings}
        signal_label = (root / "support-html" / "assets" /
                        "NotoSans-CondensedLight.ttf")
        label_args = ["--label-font", str(signal_label)]
    elif name == "amberdawn32":
        caption = "Lively Brush Font"
        props = {
            "lineOne": "Amber",
            "lineTwo": "Dawn",
            "caption": caption,
            "glyphCount": str(ctx.get("facts", {}).get("glyphs") or 482),
        }
        label_args = []
    elif name == "skinbadge32":
        warnings = []
        def skin_copy(text):
            missing = sorted({character for character in text
                              if not character.isspace() and not usable(ctx, character)})
            if missing:
                warnings.append(
                    "The skincare seal copy may be incomplete; unsupported characters: "
                    + " ".join(missing))
            return support_render_copy(ctx, text)

        props = {
            "wordOne": skin_copy("Skin") or "Skin",
            "wordTwo": skin_copy("Tribe") or "Tribe",
            "repeatWord": skin_copy("Skin Tribe  Skin Tribe") or "Skin Tribe  Skin Tribe",
            "warnings": warnings,
        }
        label_args = []
    elif name == "latestlook32":
        caption = _support_copy(ctx, ("sub",), "Display Lettering").strip()
        if len(caption) > 24 or len(caption.split()) > 3:
            caption = "Display Lettering"
        props = {
            "lineOne": support_render_copy(ctx, "Get The") or "Get The",
            "lineTwo": support_render_copy(ctx, "Latest") or "Latest",
            "lineThree": support_render_copy(ctx, "Style") or "Style",
            "caption": caption,
            "signature": "Autumn Lookbook",
        }
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "gelatocards32":
        warnings = []
        def gelato_copy(text):
            missing = sorted({character for character in text
                              if not character.isspace() and not usable(ctx, character)})
            if missing:
                warnings.append(
                    "Gelato headline copy may be incomplete; unsupported characters: "
                    + " ".join(missing))
            return support_render_copy(ctx, text)

        props = {
            "frontOne": gelato_copy("Sweet") or "Sweet",
            "frontTwo": gelato_copy("Scoops") or "Scoops",
            "backOne": gelato_copy("Sweet") or "Sweet",
            "backTwo": gelato_copy("Scoops") or "Scoops",
            "frontLabel": "Pastel  /  Frozen",
            "backLabel": "Scoop  /  Shop",
            "footer": "A Little Joy In Every Scoop",
            "warnings": warnings,
        }
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "meditation32":
        requested = {
            "headline": "Meditation",
            "workshop": "Workshop",
        }
        missing = sorted({character for text in requested.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Meditation display copy may be incomplete; unsupported characters: "
                + " ".join(missing))
        props = {
            "headline": support_render_copy(ctx, requested["headline"]),
            "workshop": support_render_copy(ctx, requested["workshop"]),
            "badge": "Disc 30%",
            "date": "September 30",
            "year": "2025",
            "tagline": "Sign Up Here\nwww.meditatewithdelaine.com",
            "warnings": warnings,
        }
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "strongweak32":
        requested = ("Youngtype Studio", "Strongest", "Weakest",
                     "Organic Hand Drawn")
        missing = sorted({character for text in requested for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Strong/weak display copy may be incomplete; unsupported characters: "
                + " ".join(missing))
        props = {
            "kicker": support_render_copy(ctx, requested[0]),
            "strongest": support_render_copy(ctx, requested[1]),
            "weakest": support_render_copy(ctx, requested[2]),
            "leftBadge": "Hand Drawn",
            "rightBadge": "Stroke Regular Outline",
            "footer": support_render_copy(ctx, requested[3]),
            "warnings": warnings,
        }
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "funkyfashion32":
        requested = {
            "headlineOne": "Funky",
            "headlineTwo": "Fashion",
            "week": "Fashion\nWeek",
            "paragraph": (
                "To be fashionable is to rub elbows with every new clothing and "
                "accessory item that hits the Market. It can be daunting trying "
                "to do such a thing. Not to Mention it is so dull and "
                "time-consuming a thing to keep up with all the latest styles."
            ),
            "signature": "Sarah\nSchwartz",
            "website": "www.funkyfashion.com",
        }
        missing = sorted({character for text in requested.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Funky Fashion display copy may be incomplete; unsupported "
                "characters: " + " ".join(missing))
        props = {key: support_render_copy(ctx, value)
                 for key, value in requested.items()}
        props["warnings"] = warnings
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "typewall32":
        rows = ("Classic Culture", "Musical Synchrony", "Cargo Manual",
                "Magical Unicorns", "Practical Pony", "Bright Zenith",
                "Culture In Motion", "Lovely People")
        missing = sorted({character for text in rows for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Typewall specimen copy may be incomplete; unsupported "
                "characters: " + " ".join(missing))
        props = {"rows": [support_render_copy(ctx, row) for row in rows],
                 "rotation": -8, "scale": 1, "spacing": 12.2,
                 "stagger": 7, "warnings": warnings}
        label_args = []
    elif name == "contour32":
        requested = {
            "title": "9 Ligatures",
            "lineOne": "ADCAQO",
            "lineTwo": "STSZTTZS",
        }
        missing = sorted({character for text in requested.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Contour specimen may be incomplete; unsupported characters: "
                + " ".join(missing))
        props = {key: support_render_copy(ctx, text)
                 for key, text in requested.items()}
        props["warnings"] = warnings
        label_args = []
    elif name == "manualbrew32":
        requested = {"lineOne": "Manual", "lineTwo": "Brew"}
        missing = sorted({character for text in requested.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Manual Brew lettering may be incomplete; unsupported characters: "
                + " ".join(missing))
        props = {key: support_render_copy(ctx, text) for key, text in requested.items()}
        props.update({
            "credit": "Our SunKits © Rivari Studio 2024",
            "background": "#2c2626",
            "pink": "#f580a1", "yellow": "#f4d12c", "green": "#97cd30",
            "blue": "#40bedf", "orange": "#f05c2f",
            "scale": 1, "tracking": .015, "lineGap": 1,
            "warnings": warnings,
        })
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "pastpresent32":
        requested = {"past": "Past", "present": "Present", "future": "Future"}
        missing = sorted({character for text in requested.values()
                          for character in text
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Timeline sign copy may be incomplete; unsupported characters: "
                + " ".join(missing))
        props = {key: support_render_copy(ctx, text) for key, text in requested.items()}
        props.update({"credit": "Our SunKits © Rivari Studio 2024",
                      "scale": 1, "tracking": -.025, "gap": 1,
                      "warnings": warnings})
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "herbalproduct32":
        requested = {
            "headline": "Herbals",
            "productName": "Arabica Whole Beans Coffee",
            "batch": "1969",
            "badge": "New",
            "process": "Process: Natural\nNet Weight: 12 Oz",
            "roast": "Medium Roast",
            "date": "Roast Date\n27 June 2024",
        }
        display_keys = ("headline", "productName", "batch", "badge", "roast")
        missing = sorted({character for key in display_keys
                          for character in requested[key]
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "The selected face lacks these Herbal Product glyphs; Chromium "
                "will draw them with a readable fallback: " + " ".join(missing))
        # Keep exact stock copy; Chromium handles unsupported display glyphs.
        props = dict(requested)
        props.update({"scale": 1, "tracking": -.018, "detailScale": 1,
                      "green": "#19b722", "cream": "#faf0d5",
                      "ink": "#2a211f", "yellow": "#f4d329",
                      "orange": "#f55324", "warnings": warnings})
        label_path = root / "support-html" / "assets" / "NotoSans-CondensedLight.ttf"
        label_args = ["--label-font", str(label_path)]
    elif name == "colosseum32":
        requested = {
            "lineOne": "Colosseum",
            "lineTwo": "Gröngöling",
            "lineThree": "Antarctica",
            "tagline": "A Typeface With Spirit, Personality & Distinction",
            "url": "www.more-etc.com • @MoreEtcStudios",
        }
        missing = sorted({character for key in ("lineOne", "lineTwo", "lineThree")
                          for character in requested[key]
                          if not character.isspace() and not usable(ctx, character)})
        warnings = []
        if missing:
            warnings.append(
                "Colosseum specimen copy may be incomplete; unsupported "
                "characters: " + " ".join(missing))
        props = {key: support_render_copy(ctx, text)
                 for key, text in requested.items()}
        props.update({"scale": 1, "tracking": .01, "rowGap": 1,
                      "paper": "#ded7c3", "navy": "#12387e",
                      "red": "#ea0003", "warnings": warnings})
        label_args = []
    elif name == "glyphsheet32":
        requested_symbols = "$&%£€!?()"
        missing_symbols = [character for character in requested_symbols
                           if not usable(ctx, character)]
        requested_digits = "0123456789"
        missing_digits = [character for character in requested_digits
                          if not usable(ctx, character)]
        warnings = []
        if missing_symbols:
            warnings.append(
                "The selected face lacks these source symbols; Chromium will "
                "draw them with a readable fallback: "
                + " ".join(missing_symbols))
        if missing_digits:
            warnings.append(
                "The selected face lacks these figure glyphs; Chromium will "
                "draw them with a readable fallback: "
                + " ".join(missing_digits))
        pangram = "Pack My Box With Five Dozen Liquor Jugs!"
        missing_pangram = sorted({character for character in pangram
                                  if not character.isspace()
                                  and not usable(ctx, character)})
        if missing_pangram:
            warnings.append(
                "The selected face lacks these pangram glyphs; Chromium will "
                "draw them with a readable fallback: "
                + " ".join(missing_pangram))
        props = {"symbols": requested_symbols,
                 "pangram": pangram,
                 "warnings": warnings}
        label_args = []
    elif name == "greetingsgrid32":
        warnings = []
        def covered_or_fallback(text, fallback, label):
            missing = [character for character in text
                       if not character.isspace() and not usable(ctx, character)]
            if not missing:
                return text
            warnings.append(
                f"{label} uses a readable fallback; unsupported characters: "
                + " ".join(dict.fromkeys(missing)))
            return fallback

        greetings = {
            "zdravo": "Zdravo!",
            "howdy": "Howdy!",
            "halla": covered_or_fallback("Hallå!", "Halla!", "Swedish greeting"),
            "bonjour": "Bonjour!",
            "privet": covered_or_fallback("Привет!", "Privet!", "Russian greeting"),
            "ola": covered_or_fallback("Olá!", "Ola!", "Portuguese greeting"),
        }
        props = {"greetings": greetings, "warnings": warnings}
        label_args = []
    elif name == "brutal32":
        lines = ("Brutalism", "A Play Between", "Crudity", "And Finesse")
        props = {"lines": [support_render_copy(ctx, line) for line in lines],
                 "leftPage": "#333435", "rightPage": "#1c1d1f",
                 "scale": 100, "tracking": -0.025}
        label_args = []
    elif name == "freakscene32":
        props = {
            "headline": support_render_copy(ctx, "Freak\nScene"),
            "leftCaption": "A Soft Sans Serif\nWith Spirit, Personality\nAnd Distinction.",
            "rightCaption": (
                "This Bold And Semi-Condensed Typeface\n"
                "Is Lively And Eye-Catching, Ideal For\n"
                "When And Where You Want To Make A\n"
                "Lasting Impression."),
            "ground": "#eee05b", "slab": "#fb8dbb",
            "ink": "#191719", "accent": "#e4d849", "grain": 22,
        }
        label_path = LABEL_B if LABEL_B.exists() else LABEL
        label_args = ["--label-font", str(label_path)]
    elif name == "zebra32":
        poem = ("Roses", "Are Red", "Chocolates", "Are Brown",
                "Valentine", "Is Bored", "If You Are", "Alone")
        props = {"love": support_render_copy(ctx, clean(ctx, "Love")),
                 "poemLines": [support_render_copy(ctx, clean(ctx, line))
                               for line in poem],
                 "film": 20}
        label_args = []
    else:
        lines = shout(ctx, _support_copy(
            ctx, ("line", "word"), "Just Like Sweet Chocolate")).strip()
        props = {"headline": support_render_copy(ctx, lines),
                 "quotes": usable(ctx, '"')}
        label_args = []
    if isinstance(props, dict):
        props["fontClass"] = ctx["class"]
        if review_mode:
            props["reviewMode"] = True
    args = ["node", str(script), "--template", name,
            "--ratio", ratio,
            "--editor", spec["htmlEntry"],
            "--source", spec.get("sourceId") or "",
            "--font", str(ctx["font_path"]), *label_args, *family_args,
            "--props", json.dumps(props, ensure_ascii=False),
            "--out", str(destination.resolve()), "--no-record"]
    result = subprocess.run(args, text=True, capture_output=True, cwd=root)
    if result.returncode:
        raise SystemExit("HTML support render failed for " + name + ":\n"
                         + result.stderr.strip())
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"HTML support renderer returned invalid JSON: {exc}") from exc
    layout = report.get("layoutReport") or {}
    if layout.get("outOfBounds"):
        raise SystemExit(f"{name}: HTML layout has off-canvas elements")
    from PIL import Image
    with Image.open(destination) as image:
        image.load()
        if image.size != FRAMES[ratio]:
            raise SystemExit(f"{destination}: HTML renderer wrote {image.width}x{image.height}, "
                             f"expected {FRAMES[ratio][0]}x{FRAMES[ratio][1]}")
        # Chromium already wrote the final PNG. Re-encoding it with Pillow's
        # optimize pass changes no pixels and dominates batch-render time.
    report["outputBytes"] = destination.stat().st_size
    report["ratio"] = ratio
    return destination, destination.stat().st_size, report


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
    order = brief.get("templates") or CLASS_ORDERS[cls]
    if not isinstance(order, list):
        return ['"templates" must be a list of five template names'], []
    if len(order) != 5 or len(set(order)) != 5:
        bad.append('"templates" must contain five distinct template names')
    unknown_order = [t for t in order if t not in CLASS_TEMPLATE_POOLS[cls]]
    if unknown_order:
        bad.append(f"unknown template(s) for class {cls}: "
                   + ", ".join(unknown_order))
    pins = brief.get("pins") or {}
    missing = [t for t in order if t not in pins]
    if missing and not (not pins and brief.get("supports")):
        # A supports-only brief authors the second surface and nothing else; the
        # five-pin contract simply does not apply to it.
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

    # Supports are an optional second surface: nothing is demanded, but whatever
    # is authored joins the anti-samey contract with the pins' headlines, because
    # one font shipping the same phrase on a pin and on a support panel is the
    # shop saying it looked twice at the same idea.
    sups = brief.get("supports") or {}
    unknown_s = [t for t in sups
                 if t not in SUPPORT_ORDER or t in SUPPORT_RETIRED]
    if unknown_s:
        bad.append("unknown support template(s): " + ", ".join(unknown_s))
    seen_theme_s = {}
    for t, pin in sups.items():
        line = (pin.get("line") or "").strip()
        if line:
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
                seen_theme_s.setdefault(th, []).append(t)
    for th, ts in seen_theme_s.items():
        if len(ts) > 1:
            bad.append(f"support theme {th} on {', '.join(ts)} — four panels "
                       "want four different worlds")

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


def save_specimen(img, out, frame, sheet, prefix="specimen"):
    """Write one specimen or support sheet: a flat PNG, no ladder and no JPEG fallback.

    The 200 KB cap is a Pinterest rule, and these files are not pins — nothing
    downstream has ever capped them. A sheet that blows past 500 KB is therefore
    reported rather than quietly re-encoded, because the first lever is the pool
    radius and the last one is the type, and a silently-lossy specimen of a face
    someone is selling is worse than a big file.
    """
    d = out / frame
    d.mkdir(parents=True, exist_ok=True)
    ship = d / f"{prefix}-{sheet}.png"
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


# ------------------------------------------------------- the support catalogue
#
# Marketplace supporting images, drawn natively at 2400x1600. The pins pile their
# boxes against the W/M/H globals, so forcing a wide sheet leaves the right
# two-thirds empty; these bodies read the real sheet (sh.w/sh.m/sh.h), spend the
# width on purpose, and take their identity from the class's theme roll — world,
# ornament set, ladder — the same way a pin does.
#
# Each panel is one structural idea, not one headline placement. A support slot
# has to *argue* something the other slots don't: the phrase argues personality,
# the reveal argues the release, the split argues scale control, the stack argues
# "this is your job, done". The argument decides the furniture — rules, light,
# paper, dividers — and the type takes the frame either way.

def support_device(sh, P, th, dark, tex=None):
    """The theme's signature drawn for the wide sheet.

    `device()` counts its steps against a 1500-px page, so on 2400x1600 its bands
    stop short and its rings walk off the edge. Each kind is re-anchored here to
    the real sheet at the same near-silence alpha: a flat ground reads as pasted,
    a textured one reads as printed, and the difference is most of what makes a
    listing image look made rather than generated.
    """
    x = (TEXTURE_STRENGTH if tex is None else tex)
    if x > 0 and not getattr(sh, "_tex", None):
        # A panel that painted its own ground and never went through `bg()` still
        # gets a textured one; a panel that did is already wearing its theme.
        texture_pack(sh, P, _tex_kind(th), strength=x, seed=_tex_seed(th),
                     box=Box(0.0, 0.0, float(sh.w), float(sh.h)))
    kind = th["device"]
    if kind == "none":
        return
    Wd, Hd, Md = sh.w, sh.h, sh.m
    s = sh.scale
    ink, mute = (P["glow"], mix(P["glow"], P["deep2"], 0.4)) if dark \
        else (P["ink"], mix(P["ink"], P["paper2"], 0.4))
    cv = sh.cv
    if kind == "dots":
        dot_grid(cv, mute, step=int(34 * s), rad=2.2 * s, alpha=0.17,
                 x0=Md, y0=int(Hd * 0.50), x1=Wd - Md,
                 y1=Hd - int(250 * sh.vscale))
    elif kind == "grid":
        for i in range(13):
            x = Md + i * ((Wd - 2 * Md) / 12)
            rule(cv, x, int(Hd * 0.54), x, Hd - int(250 * sh.vscale), mute, 1.0, 0.13)
        for i in range(5):
            y = int(Hd * 0.54 + i * (Hd * 0.32 / 4))
            rule(cv, Md, y, Wd - Md, y, mute, 1.0, 0.13)
    elif kind == "bands":
        for i in range(4):
            y = int(Hd * 0.58 + i * Hd * 0.10)
            cv.drawRect(skia.Rect.MakeXYWH(0, y, Wd, int(46 * s)),
                        paint(C(mute, 0.06)))
    elif kind == "rings":
        q = paint(C(mute, 0.13), style=skia.Paint.kStroke_Style, width=1.6 * s)
        for i in range(6):
            cv.drawCircle(Wd * 0.93, Hd * 0.88, (150 + i * 170) * s, q)
    elif kind == "rays":
        q = paint(C(mute, 0.11), style=skia.Paint.kStroke_Style, width=2.2 * s)
        for i in range(17):
            a = math.radians(-184 + i * 8)
            cv.drawLine(Wd * 0.05, Hd * 0.94,
                        Wd * 0.05 + math.cos(a) * Hd * 1.15,
                        Hd * 0.94 + math.sin(a) * Hd * 1.15, q)
    elif kind in ("hatch", "ruling"):
        y0, y1 = int(Hd * 0.13), int(Hd * 0.88)
        for i in range((y1 - y0) // int(46 * s)):
            rule(cv, Md * 0.6, y0 + i * 46 * s, Wd - Md * 0.6, y0 + i * 46 * s,
                 mute, 1.0, 0.09)
        rule(cv, Wd * 0.105, y0 - 40, Wd * 0.105, y1 + 40, P["accent"], 1.2, 0.13)
    elif kind == "lanes":
        y0, y1 = int(Hd * 0.12), int(Hd - 250 * sh.vscale)
        for i in range((y1 - y0) // int(58 * s)):
            rule(cv, Md * 0.6, y0 + i * 58 * s, Wd - Md * 0.6, y0 + i * 58 * s,
                 mute, 1.0, 0.11)




@support("line32", "the broadside: the phrase as a letterpress poster — full-measure lines over the theme's own texture, line one echoed in outline, the initial bleeding off the corner")
def t_line32(sh, ctx):
    """The face doing its job in words, big enough to be the picture.

    The oldest way to sell a piece of type is the broadside: the headline takes
    the whole measure in two lines — every row grown edge to edge, the second row
    in the accent so the sentence lands as one object — over the theme's texture,
    under an accent tick rule. Line one is echoed once in outline behind itself
    (the `finish` pin's photo-finish move, spent on the phrase), and the face's
    own initial bleeds off the bottom-right corner so the poster sits *on*
    something rather than pasted into a gradient.
    """
    P, T = ctx["pal"], ctx["display"]
    dark = spec_bg(sh, ctx, pool=0.05)
    support_device(sh, P, ctx["th"], dark)
    line = shout(ctx, _support_copy(ctx, ("line", "word"),
                                    "Letters That Matter")).strip()
    words = [w for w in line.split() if w]
    if not words:
        sh.problems.append("line32: the face draws no word of this line")
        return
    ch = next((c for c in reversed(line) if c.isalpha() and usable(ctx, c)), "")
    if ch:
        ghost_letter(sh, ctx, ch.upper(), sh.w * 0.90, sh.h * 0.96,
                     size=int(round(1450 * sh.scale)), alpha=0.10)
    over = clean(ctx, ctx["copy"].get("over") or "").strip()
    top = eyebrow(sh, ctx, over or "New Release")
    rule(sh.cv, sh.m, top + int(round(9 * sh.vscale)),
         sh.m + int(round(210 * sh.scale)), top + int(round(9 * sh.vscale)),
         P["accent"], 3.4 * sh.scale, 0.9)
    y0 = top + int(round(44 * sh.vscale))
    stage = Box(sh.m, y0, sh.w - 2 * sh.m,
                spec_floor(sh) - y0 - int(round(30 * sh.vscale)))
    lines = pack_lines(words, min(2, len(words)))
    # The ladder is walked to the ground each row actually stands on, inside
    # `measure_rows` — a stage-wide lift is a different median from a row of it
    # once the theme's texture crosses the sheet, and the checker reads the row.
    measure_rows(sh, T, P, lines, stage, "ln", hi=560 * sh.scale,
                 min_read=46 * sh.scale, fill=True, lead_frac=0.08, centre=True)
    slot = _slot(sh, "ln0")
    # A wireframe echo is a second, hairline copy of the whole line, and a PNG
    # pays for edges: on the broadside it is 137 KB of the sheet on an extruded
    # sports face and only 20 KB on a flat gothic. Measured across the foundry's
    # five test faces the kit splits cleanly — flat sans, script and blackletter
    # sit under 0.45, an outlined varsity face starts at 0.6 — and above the split
    # the lattice is neither legible nor cheap. So the busy contour is left to be
    # the picture on its own.
    #
    # A flowing hand is excluded for the opposite reason: its contour is the
    # cheapest to trace, and precisely because it is thin and connected, the
    # lattice of a second copy of it is unreadable as a wireframe — it smears
    # behind the solid line and costs 140 KB of noise. The echo is a device for
    # faces with an inside; a script already has one.
    if (slot and len(lines) > 1 and ctx["family"] not in FLOWING
            and contour_density(T, lines[0]) < 0.5):
        p, _adv = T.path(lines[0], slot.size)
        b = p.getBounds()
        dx = slot.ink.x - b.left() + int(round(24 * sh.scale))
        dy = slot.ink.y - b.top() + int(round(26 * sh.scale))
        sh.cv.save()
        sh.cv.translate(dx, dy)
        wireframe(sh.cv, p, P["accent"], weight=2.0 * sh.scale, alpha=0.30)
        sh.cv.restore()
        sh.mark("echo", Box(b.left() + dx, b.top() + dy, b.width(), b.height()),
                collide=False, bleed=True)
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)


def hero_pair(T, words, stage):
    """The announcement's name block — two lines whenever one would be a band.

    A wide face can make even a seven-letter name a single flat stripe no taller
    than a caption, and the reference's whole gesture is the name broken across
    two lines. So a one-word name is broken too, at the seam that leaves the two
    halves nearest the same ink width: that is the break which reads as a stack
    rather than as a word cut in half.
    """
    if len(words) > 1:
        return pack_lines(words, min(2, len(words)))
    word = words[0] if words else ""
    if len(word) < 6:
        return [word]
    size = fit_measure(T, word, stage.w, 640.0)
    if size <= 0:
        return [word]
    if T.path(word, size)[0].getBounds().height() >= 0.30 * stage.h:
        return [word]
    best, gain = None, None
    for i in range(3, len(word) - 2):
        d = abs(T.measure(word[:i], 100.0) - T.measure(word[i:], 100.0))
        if gain is None or d < gain:
            best, gain = i, d
    if best is None:
        return [word]
    return [word[:best], word[best:]]


def t_announce32(sh, ctx):
    """Rebuilt from T24507_00 (Rodeo Cowgirls).

    The reference's whole trick is restraint: the ground is flat, *every line is
    one ink*, and the only colour on the sheet is four little drawings in the
    corners. The font says its own name once, enormous, across two lines; the lead-in
    and the descriptor are set in the companion face, because a shopfront where the
    goods are also the signage is a shop that owns one alphabet. No rules, no tabs,
    no footer: the ornaments are the decoration and the name is the picture.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    th = ctx["th"]
    dark = spec_bg(sh, ctx, pool=0.06)
    name = shout(ctx, clean(ctx, ctx["name"])).strip()
    if not name or not T.fit(name, 100.0, sh.w - 2 * sh.m):
        sh.problems.append("announce32: the face draws no usable word of the name")
        return
    ink, mute, _ = field(P)
    Pi = dict(P, tone=[dict(color=ink)] * 4)
    lead = lead_in(ctx, ("just cut", "fresh from the press", "new this season",
                         "set and printed", "off the bench"))
    sh.text("lead", L, " ".join(tc(lead).split()),
            Box(sh.m, int(round(96 * sh.vscale)), sh.w - 2 * sh.m,
                int(round(120 * sh.vscale))),
            hi=52 * sh.scale, lo=24, max_lines=1, align="center",
            valign="top", track=0.24, min_read=22 * sh.scale, color=ink)
    lb = _slot(sh, "lead")
    y0 = (lb.ink.b if lb else sh.m) + int(round(46 * sh.vscale))
    words = name.split()
    an_box = Box(sh.m + int(round(60 * sh.scale)), y0,
                 sh.w - 2 * (sh.m + int(round(60 * sh.scale))),
                 int(round((sh.h - y0) * 0.74)))
    measure_rows(sh, T, Pi, hero_pair(T, words, an_box), an_box,
                 "an", hi=640 * sh.scale, min_read=56 * sh.scale, fill=True,
                 lead_frac=0.04, centre=True)
    sub = clean(ctx, ctx["copy"].get("sub") or "").strip()
    # The descriptor keeps the case the copy was written in: a companion line set
    # in a plain sans does not need every word shouted, and title-casing it would
    # turn "for posters and patches" into a headline that competes with the name.
    desc = " ".join(sub.split()) if sub else rolled(
        ctx, ("for posters and patches", "cut for the shopfront",
              "made for big headlines", "letterpress and label work"))
    sh.text("desc", L, desc,
            Box(sh.m + int(round(80 * sh.scale)), int(round(sh.h * 0.805)),
                sh.w - 2 * (sh.m + int(round(80 * sh.scale))),
                int(round(90 * sh.vscale))),
            hi=48 * sh.scale, lo=18, max_lines=1, align="center",
            valign="top", track=0.06, min_read=18 * sh.scale, color=ink)
    art = ORN_SETS[th["art"]]
    # Four *different* characterful marks, one per corner. A blob is just a rock
    # at this size, and the reference's corners are all objects, so the set's
    # shapeless kinds drop out and the alternation carries the colour.
    kinds, seen = [], set()
    for band in ("top", "bottom"):
        for o in art[band]:
            if o[0] not in seen and o[0] != "blob":
                seen.add(o[0])
                kinds.append(o[0])
    while len(kinds) < 4:
        kinds.append("star")
    cols = (P["accent"], P["accent2"])
    spots = ((sh.m * 1.15, sh.m * 1.05), (sh.w - sh.m * 1.15, sh.m * 1.05),
             (sh.m * 1.15, sh.h - sh.m * 0.95),
             (sh.w - sh.m * 1.15, sh.h - sh.m * 0.95))
    for i, ((cx, cy), kind) in enumerate(zip(spots, kinds[:4])):
        draw_orn(sh, f"cor{i}", kind, cx, cy, 52 * sh.scale, cols[i % 2], 0.9,
                 collide=False)
    # The reference also sparks the name itself — a bolt by the first line, an
    # asterisk by the second. Two small stars do the same job.
    nb0, nb1 = _slot(sh, "an0"), _slot(sh, "an1")
    if nb0 and nb1:
        draw_orn(sh, "sp0", "star", nb0.ink.x - int(36 * sh.scale),
                 nb0.ink.y + int(32 * sh.scale), 20 * sh.scale,
                 P["accent"], 0.95, collide=False)
        draw_orn(sh, "sp1", "star", nb1.ink.r + int(36 * sh.scale),
                 nb1.ink.y + int(32 * sh.scale), 20 * sh.scale,
                 P["accent2"], 0.95, collide=False)
def _palm_tree(cv, bx, by, cx, cy, L, angles, rgb, seed=5, droop=0.28,
               nleaf=11):
    """One palm cut as a flat silhouette: a curving tapered trunk and fronds
    built from real tapered spines carrying leaflet spikes.

    A palm reads by its outline, so this draws the outline the way a mid-century
    poster cutter did: the trunk is a quadratic that narrows from base to crown;
    each frond leaves the crown along its own angle, arcs, and lets gravity pull
    the tip down (the `droop` term); and the frond's edge is not smooth — short
    triangles sprout off the spine, angled back and drooping, longest near the
    frond's base and dying out toward its tip. That tapering fringe is the whole
    difference between a palm and a dandelion.

    Every part is filled separately in one opaque colour, so the parts union
    into a silhouette with no winding artefacts and the sheet pays only for the
    outline — the inside is flat tone. Returns the ink bounds drawn.
    """
    rnd = random.Random(seed)
    q = paint(C(rgb, 1.0))
    ink = None

    def fill(p):
        nonlocal ink
        cv.drawPath(p, q)
        b = p.getBounds()
        ink = (Box(b.left(), b.top(), b.width(), b.height()) if ink is None
               else Box(min(ink.x, b.left()), min(ink.y, b.top()),
                        max(ink.r, b.right()) - min(ink.x, b.left()),
                        max(ink.b, b.bottom()) - min(ink.y, b.top())))

    def _q2(p0, p1, p2, t):
        u = 1.0 - t
        return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])

    def _dq2(p0, p1, p2, t):
        return (2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]),
                2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]))

    # --- trunk: sampled quadratic offset to both sides, fat at the ground,
    # narrow at the crown, with a hand-cut bend toward the lean of the tree.
    H0 = max(1.0, abs(by - cy))
    p0, p2 = (bx, by), (cx, cy)
    p1 = (bx + (cx - bx) * 0.30 + (0.05 * L if cx >= bx else -0.05 * L),
          by + (cy - by) * 0.62)
    wb, wt = 0.034 * H0 + 3.0, 0.014 * H0 + 2.0
    N = 12
    lefts, rights = [], []
    for i in range(N + 1):
        t = i / N
        x, y = _q2(p0, p1, p2, t)
        dx, dy = _dq2(p0, p1, p2, t)
        m = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / m, dx / m
        w = wb + (wt - wb) * t
        lefts.append((x + nx * w, y + ny * w))
        rights.append((x - nx * w, y - ny * w))
    tr = skia.Path()
    tr.moveTo(*lefts[0])
    for x, y in lefts[1:] + list(reversed(rights)):
        tr.lineTo(x, y)
    tr.close()
    fill(tr)

    # --- fronds: splayed from the crown, each one a drooping tapered spine
    # with leaflets. Different seeds per tree make the splays siblings, not
    # twins; the crown knot joins the spine bases so the head reads solid.
    head = skia.Path()
    head.addCircle(cx, cy, max(2.0, 0.030 * L))
    fill(head)
    wf = 0.022
    for deg in angles:
        a = math.radians(deg + rnd.uniform(-5, 5))
        ca, sa = math.sin(a), -math.cos(a)
        Lk = L * (0.84 + 0.24 * rnd.random())

        def cpt(t, ca=ca, sa=sa, Lk=Lk):
            return (cx + ca * Lk * t, cy + sa * Lk * t + droop * Lk * t * t)

        def ctan(t, ca=ca, sa=sa, Lk=Lk):
            dx, dy = ca * Lk, sa * Lk + 2 * droop * Lk * t
            m = math.hypot(dx, dy) or 1.0
            return dx / m, dy / m

        M = 10
        ls, rs = [], []
        for i in range(M + 1):
            t = i / M
            x, y = cpt(t)
            tx, ty = ctan(t)
            nx, ny = -ty, tx
            w = wf * Lk * min(1.0, 7 * t) * (1.0 - t) ** 0.62
            ls.append((x + nx * w, y + ny * w))
            rs.append((x - nx * w, y - ny * w))
        fr = skia.Path()
        fr.moveTo(*ls[0])
        for x, y in ls[1:] + list(reversed(rs)):
            fr.lineTo(x, y)
        fr.close()
        for j in range(nleaf):
            t = 0.06 + 0.92 * j / (nleaf - 1)
            x, y = cpt(t)
            tx, ty = ctan(t)
            ll = 0.28 * Lk * (1.02 - t) * (0.84 + 0.28 * rnd.random())
            x0, y0 = cpt(max(0.0, t - 0.05))
            x1, y1 = cpt(min(1.0, t + 0.05))
            for side in (-1, 1):
                nx, ny = -ty * side, tx * side
                ddx, ddy = nx - 0.52 * tx, ny - 0.52 * ty
                m = math.hypot(ddx, ddy) or 1.0
                fr.moveTo(x0, y0)
                fr.lineTo(x + ddx / m * ll, y + ddy / m * ll + 0.16 * ll)
                fr.lineTo(x1, y1)
                fr.close()
        fill(fr)
    return ink

@support("duo32", "the summer sign: an oversized initial behind its crossing word, a coral sun, two palm silhouettes, and a small specimen tagline")
def t_duo32(sh, ctx):
    """Rebuilt from T30173_08 (the California sun-and-palms card).

    The reference is not a specimen sheet, it is a poster made out of the font:
    one oversized letter held near the left edge, the rest of its word
    crossing that initial and walking across a flat sun and two palm silhouettes,
    with a small tagline
    hanging off the end of it. All the type is one ink on a grainy ground —
    the colour belongs to the drawing, never to the letters — and the sheet
    carries no rule, no label, no footer: the picture is the argument.
    """
    P, T = dict(ctx["pal"]), ctx["display"]
    # This illustration has a fixed cobalt / coral / ivory identity in its
    # source. Letting the rolled font theme recolour it was washing the reference
    # into charcoal, mauve, or muted pink. Explicit CLI palette/mode choices still
    # work, but the normal render stays faithful to the source's vivid print.
    if not ctx.get("palette_override"):
        P.update(
            deep1=(50, 52, 154), deep2=(58, 60, 166),
            paper1=(255, 246, 227), paper2=(247, 231, 205),
            ink=(26, 19, 51), glow=(255, 246, 227),
            accent=(252, 102, 89), accent2=(255, 198, 113),
        )
    if not ctx.get("mode_override"):
        P["mode"] = "dark"
    P["tone"] = tones(P, ctx["family"])
    # The reference is a saturated, nearly flat blue print with fine worn grain;
    # a theme's light-pool device is not part of this artwork.
    inv = P["mode"] != "dark"
    bg(sh, P, ctx["th"], dev=False, pool=0.0, tooth=5200,
       invert=inv, tex="worn")
    ink, _mute, _ = field(P, invert=inv)
    word = shout(ctx, _support_copy(ctx, ("word", "line"), "California")).strip()
    word = word.strip()
    if len(word) < 3 or not T.fit(word, 100.0, sh.w):
        sh.problems.append("duo32: the face draws no word long enough to split")
        return
    head, tail = word[0], word[1:]
    sil = (39, 16, 33) if not ctx.get("palette_override") else P["deep1"]

    # The sun: one flat disc, right of centre, nothing on it but the palms —
    # with a thin halo just off its rim so it reads as light and not paint.
    # The halo is one gaussian drawn at 1/BG_SCALE and stretched back up
    # (`halo` does the bookkeeping), and its sigma is deliberately small: a
    # glow pays for its *spread*, per pixel, so the bloom is kept thin by
    # shrinking sigma rather than by stepping it into rings.
    dcx, dcy = int(sh.w * 0.775), int(sh.h * 0.375)
    dr = int(round(sh.h * 0.24))
    disc = skia.Path()
    disc.addCircle(dcx, dcy, dr)
    halo(sh.cv, disc, mix(P["accent"], P["glow"], 0.35), 26 * sh.scale, 0.38)
    sh.cv.drawPath(disc, paint(C(P["accent"], 1.0)))
    sh.mark("disc", Box(dcx - dr, dcy - dr, 2 * dr, 2 * dr), collide=False)

    # Two palms, cut as one flat silhouette colour each. They are not one tree
    # stamped twice: the near tree is taller, sits its crown high in the disc,
    # leans the other way and carries a different number of fronds and a
    # different leaflet seed, so the pair reads like a clump, not a mirror.
    # A low mound of the same black joins their trunks at the bottom edge, the
    # way the reference grounds them.
    mound = skia.Path()
    mound.addOval(skia.Rect.MakeXYWH(sh.w * 0.585, sh.h * 0.965,
                                     sh.w * 0.335, sh.h * 0.13))
    sh.cv.drawPath(mound, paint(C(sil, 1.0)))
    sh.mark("mound", Box(int(sh.w * 0.585), int(sh.h * 0.965),
                         int(sh.w * 0.335), int(round(sh.h * 0.13))),
            collide=False, bleed=True)
    for i, tb_ in enumerate((
            _palm_tree(sh.cv, int(sh.w * 0.695), int(sh.h * 1.045),
                       int(sh.w * 0.645), int(sh.h * 0.50), int(round(sh.h * 0.165)),
                       (-112, -74, -38, -4, 34, 76, 116), sil,
                       seed=11, droop=0.30, nleaf=18),
            _palm_tree(sh.cv, int(sh.w * 0.845), int(sh.h * 1.06),
                       int(sh.w * 0.855), int(sh.h * 0.335), int(round(sh.h * 0.205)),
                       (-124, -88, -52, -14, 26, 66, 104, 138), sil,
                       seed=23, droop=0.25, nleaf=20))):
        sh.mark(f"palm{i}", tb_, collide=False, bleed=True)

    # The source separates these two baselines: the initial is an oversized
    # poster letter, while the rest of the word crosses the sun at mid-height.
    # Tying them together made ordinary display capitals much too small and
    # turned the source's signature into a conventional drop cap.
    p0, _ = T.path(head, 1000.0)
    b0 = p0.getBounds()
    head_top = int(round(sh.h * 0.055))
    s_h = sh.h * 0.89 * 1000.0 / max(1.0, b0.height())
    s_w = (sh.w * 0.36) * 1000.0 / max(1.0, b0.width())
    hsize = max(1.0, min(s_h, s_w))
    p, _adv = T.path(head, hsize)
    b = p.getBounds()
    dx = int(round(sh.w * 0.085)) - b.left()
    dy = head_top - b.top()
    sh.cv.save()
    sh.cv.translate(dx, dy)
    sh.cv.drawPath(p, paint(C(ink, 1.0)))
    sh.cv.restore()
    sh.mark("head", Box(b.left() + dx, b.top() + dy, b.width(), b.height()),
            collide=False, bleed=True)

    # The word runs through the lower half of the initial, like the lettering
    # in the source, then travels across the palms and sun. Its baseline is
    # independent of the giant opening letter.
    y_base = int(round(sh.h * 0.52))
    tail_x = int(dx + b.left() + b.width() * 0.38)
    avail = int(sh.w * 0.955) - tail_x
    tsize = fit_measure(T, tail, avail, 470 * sh.scale)
    tp, _ = T.path(tail, tsize)
    tb = tp.getBounds()
    if tb.height() * 2.1 > b.height():
        tsize *= b.height() / (2.1 * tb.height())
        tp, _ = T.path(tail, tsize)
        tb = tp.getBounds()
    # A restrained keyline keeps the ivory word readable over both the coral
    # disc and dark fronds without overpowering the source's clean lettering.
    sh.cv.save()
    sh.cv.translate(tail_x, y_base)
    sh.cv.drawPath(tp, paint(C(sil, 1.0), style=skia.Paint.kStroke_Style,
                             width=tsize * 0.038))
    sh.cv.restore()
    wpad = tsize * 0.038
    wbox = Box(tail_x - 1, y_base + tb.top(), tb.width() + 2 * wpad + 2,
               tb.height())
    sh.text("word", T, tail, wbox,
            hi=tsize, lo=tsize, max_lines=1, align="left", valign="top",
            min_read=40 * sh.scale, min_contrast=2.2, color=ink)

    tag = _support_copy(ctx, ("sub", "over"), "knows how to party").strip()
    if tag:
        sh.text("tag", T, tag,
                Box(int(sh.w * 0.36),
                    int(y_base + tb.bottom() + 26 * sh.scale),
                    int(sh.w * 0.955) - int(sh.w * 0.36),
                    int(round(150 * sh.vscale))),
                hi=158 * sh.scale, lo=20, max_lines=1, align="right",
                valign="top", min_read=20 * sh.scale, min_contrast=2.2,
                color=ink)




def _ink_right_in_band(path, y0, y1, x_lo, x_hi, steps=32, rows=7):
    """The rightmost ink of a filled path between two horizontal lines.

    skia-python exposes no path boolean op, so a glyph's edge inside a band is
    found by probing the fill instead of cutting it: walk in from the path's own
    right bound, stop at the first column the glyph actually covers, then bisect
    that column. `contains` is a scanline test, so the cost is the probe count —
    one coarse walk plus a dozen bisections of a handful of samples each.
    """
    def hit(x):
        for i in range(rows + 1):
            if path.contains(x, y0 + (y1 - y0) * i / float(rows)):
                return True
        return False

    step = max(1.0, (x_hi - x_lo) / float(steps))
    x, found = x_hi, False
    while x > x_lo:
        if hit(x):
            found = True
            break
        x -= step
    if not found:
        return x_lo
    lo, hi = x, min(x + step, x_hi)
    for _ in range(12):
        mid = 0.5 * (lo + hi)
        if hit(mid):
            lo = mid
        else:
            hi = mid
    return lo


# ------------------------------------------------- card/sticker language (name-free)
#
# Both panels were shipping the font's name as their subject: `card32` lettered
# it once in the full-height column and again on the card, and `sticker32`
# stickered it across the whole sheet. A buyer opens a listing whose *title* is
# that name; the panel that prints it a second and third time sells nothing they
# could not read in the heading. The helpers below decide what each panel may
# letter instead — real language the brief already authoring — and enforce the
# guarantee in code: every slot is filtered for the name's own tokens, so even
# a brief that authors "Gladista" into the word key cannot put the name back on
# the sheet.


def _nm_free(ctx, text, display=True):
    """One authored string made safe to letter, or '' when it is not safe.

    Three ways a candidate dies here. It is empty or whitespace — no language,
    no slot. `display` is True and the face cannot draw every character of it —
    `clean` alone would bite a hole in the word and ship the stump as copy, so
    the whole candidate is refused instead (text that will be set in the
    companion face passes `display=False`; the companion draws any letter this
    vocabulary uses). Or it carries the font's own name — any substantial token
    of it, case- and punctuation-folded — which is the exact repetition these
    two panels were rebuilt to stop. Title-casing happens here so every
    survivor is already display-ready; the font's name is never a fallback.
    """
    t = tc(text or "") if not display else tc(clean(ctx, text or ""))
    t = " ".join(t.split())
    if not t:
        return ""
    if display and not all(usable(ctx, ch) for ch in t if not ch.isspace()):
        return ""
    flat = "".join(ch for ch in t.casefold() if ch.isalnum())
    for tok in ctx["name"].replace("-", " ").replace("/", " ").split():
        key = "".join(ch for ch in tok.casefold() if ch.isalnum())
        if len(key) >= 3 and key in flat:
            return ""
    return t


def _pool_roll(ctx, pool):
    """The pool's candidates rotated by the font's name, this face's first.

    The same bargain `rolled` strikes with the small type: one font always
    re-renders its own choice, and two faces of the same shape do not both ship
    the pool's first entry.
    """
    rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
    return pool[rot % len(pool):] + pool[:rot % len(pool)]


CARD_WORD_POOL = ("Always", "Steady", "Brightly", "By heart", "Onward")
CARD_LINE_POOL = ("Made to be read", "Set in good faith", "Worth reading twice",
                  "Cut for the long run", "Printed to be kept")
CARD_CAP_POOL = ("In hand", "Fresh off the press", "On the bench",
                 "Proof for the buyer")
CARD_FOOT_POOL = ("Invitations and vows", "Mastheads and margins",
                  "Posters and patches", "Banners and tickets",
                  "Marquees and sleeves")
STICKER_POOL = ("Hand set", "Fresh ink", "Read me", "Made to last",
                "Say it loud")


def _card_language(ctx):
    """Everything card32 may letter: the word, the phrase, the caption, the foot.

    The brief comes first; when a key is missing — or authored the name, or the
    display face cannot spell it — the panel's own vocabulary takes the slot.
    Nothing here ever falls back to the font's name: this function is the
    guarantee. Returns None only when the face cannot draw any candidate at
    all, which fails the panel rather than lettering the name out of need.
    """
    copy = ctx["copy"]
    word = _nm_free(ctx, copy.get("word") or "")
    if not word:
        word = next((c for c in _pool_roll(ctx, CARD_WORD_POOL)
                     if _nm_free(ctx, c)), "")
    phrase = _nm_free(ctx, copy.get("line") or "")
    if not phrase:
        phrase = next((c for c in _pool_roll(ctx, CARD_LINE_POOL)
                       if _nm_free(ctx, c)), "")
    cap = _nm_free(ctx, copy.get("over") or "", display=False)
    if not cap:
        cap = next((c for c in _pool_roll(ctx, CARD_CAP_POOL)
                    if _nm_free(ctx, c, display=False)), "In Hand")
    foot = _nm_free(ctx, copy.get("sub") or "", display=False)
    if not foot:
        foot = next((c for c in _pool_roll(ctx, CARD_FOOT_POOL)
                     if _nm_free(ctx, c, display=False)), "Fresh From The Bench")
    if not word or not phrase:
        return None
    return {"word": word, "phrase": phrase, "cap": cap, "foot": foot}


def _sticker_phrase(ctx):
    """The one thing sticker32 may letter — a word or short phrase, never the name.

    Same guarantee as `_card_language`, one slot: the brief's `word` first, a
    brief `line` only while it still reads as a logotype (three words at most,
    because a sticker of four lines is a paragraph), then the panel's own
    vocabulary. The name is not in any of these lists and `_nm_free` keeps any
    authored copy that hides it out of the sheet.
    """
    copy = ctx["copy"]
    for cand in (copy.get("word") or "", copy.get("line") or ""):
        t = _nm_free(ctx, cand)
        if t and len(t.split()) <= 3:
            return t
    for cand in _pool_roll(ctx, STICKER_POOL):
        t = _nm_free(ctx, cand)
        if t:
            return t
    return ""


@support("card32", "the stack: two sheets of paper tipped one over the other on the bench — the word standing full-height beside them, the phrase lettered across the top sheet, every ink resolved against the ground it actually landed on")
def t_card32(sh, ctx):
    """Where the buyer sees their own job done, in real language.

    The `sample` pin's tipped card, doubled and enlarged: a blank sheet lies
    under the lettered one, rotated the other way and edged out from behind it,
    so the pair reads as prints picked up off a bench rather than one rectangle
    pasted on a gradient. The name used to be lettered here twice — the
    full-height column *and* the card's caption — and a listing already titled
    with that name learns nothing from the repetition. The column now carries
    the face's one authored *word* and the card carries its *phrase*, with a
    caption and a foot line set in the companion face; `_card_language` filters
    every slot (and every fallback) so the name cannot reach the sheet even
    from a brief that authors it. The colours are decided the same measured
    way: the paper is picked against the bench that is actually painted behind
    it, and every ink on the card is resolved against that paper through
    `readable()` — a card the colour of its own ground was the other half of
    the complaint.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = spec_bg(sh, ctx, pool=0.14)
    support_device(sh, P, ctx["th"], dark)
    lang = _card_language(ctx)
    if lang is None:
        sh.problems.append("card32: the face draws neither a word nor a phrase "
                           "that is not the name — there is nothing to letter")
        return
    y0 = eyebrow(sh, ctx, lang["cap"]) + int(round(34 * sh.vscale))
    floor = spec_floor(sh)

    # --- the word column: where the name used to stand twice. Its ink is
    # resolved against the measured bench, rung-mixed with the accent so the
    # sheet has one loud voice and the card another.
    colbox = Box(sh.m, y0, int(round(sh.w * 0.34)), floor - y0)
    gnd = sh._behind(colbox)
    base = P["glow"] if P["mode"] == "dark" else P["ink"]
    colink = readable(gnd, mix(base, P["accent"], 0.40), 4.5) \
        if gnd is not None else mix(base, P["accent"], 0.40)
    Pw = dict(P, tone=[dict(color=colink)] * 4)
    wwords = [w for w in lang["word"].split() if w]
    measure_rows(sh, T, Pw, pack_lines(wwords, min(2, len(wwords))), colbox,
                 "nm", hi=520 * sh.scale, min_read=48 * sh.scale, fill=True,
                 lead_frac=0.06, centre=True)

    # --- the cards. The paper is chosen against the ground that is *actually
    # painted* under it, not assumed from the palette: on a bright bench the
    # sheet lands dark, on a dark one cream, and either way it reads as a
    # piece of paper someone set down.
    CW, CH = int(round(sh.w * 0.50)), int(round(sh.h * 0.62))
    cx, cy = int(sh.w * 0.655), int(sh.h * 0.485)
    bench = sh._behind(Box(cx - CW / 2, cy - CH / 2, CW, CH))
    if bench is None:
        bench = 0.12 if dark else lum(P["paper1"])
    paper = max((P["paper1"], P["paper2"], mix(P["paper1"], P["glow"], 0.5),
                 mix(P["deep1"], P["paper2"], 0.45), P["deep1"], P["deep2"]),
                key=lambda c: contrast_lum(bench, lum(c)))
    gp = lum(paper)
    bcol = mix(paper, (255, 255, 255) if gp < 0.45 else (0, 0, 0), 0.10)
    # the sheet underneath: blank paper, tipped the other way — the stack is
    # what sells the top card as a real object.
    back = sh.sub(int(CW * 0.84), int(CH * 0.86))
    back.cv.drawRect(skia.Rect.MakeXYWH(0, 0, back.w, back.h), paint(C(bcol)))
    sh.paste(back, cx + int(round(150 * sh.scale)),
             cy + int(round(52 * sh.vscale)), angle=2.8,
             shadow=(0, 18 * sh.scale, 24 * sh.scale, 24 * sh.scale, 0.26))

    # --- the inks on the card: all three resolved against the card's own
    # measured paper, so the caption can never be paper-on-paper again.
    kin = readable(gp, base, 4.5)
    kacc = readable(gp, P["accent"], 4.5)
    kmut = readable(gp, mix(base, paper, 0.42), 4.5)
    sub = sh.sub(CW, CH)
    sub.cv.drawRect(skia.Rect.MakeXYWH(0, 0, CW, CH), paint(C(paper)))
    border_frame(sub, Box(34, 34, CW - 68, CH - 68),
                 mix(kin, paper, 0.35), kacc, alpha=0.55)
    Pc = dict(P, tone=[dict(color=kin), dict(color=kacc),
                       dict(color=kin), dict(color=kacc)])
    inset = int(round(CW * 0.15))
    inner_w = CW - 2 * inset
    sub.text("k-ov", L, lang["cap"],
             Box(inset, int(round(CH * 0.15)), inner_w,
                 int(round(CH * 0.06))), hi=32, lo=14,
             color=kacc, track=0.26, align="left", valign="top", min_read=14)
    words = [w for w in lang["phrase"].split() if w]
    rows = len(words) if len(words) < 3 else min(3, max(2, len(words)))
    measure_rows(sub, T, Pc, pack_lines(words, rows),
                 Box(inset, int(round(CH * 0.24)), inner_w,
                     int(round(CH * 0.48))), "cd", hi=380,
                 min_read=44, fill=True, lead_frac=0.05, centre=True)
    rule_y = int(round(CH * 0.76))
    rule(sub.cv, inset, rule_y, CW - inset, rule_y, kin, 1.2, 0.45)
    # the foot: the brief's quiet detail line in the companion face — a
    # card's small print, not the name for the third time.
    sub.text("k-sig", L, lang["foot"],
             Box(inset, int(round(CH * 0.80)), inner_w,
                 int(round(CH * 0.07))),
             hi=34, lo=15, color=kmut, track=0.20, align="left", valign="top",
             min_read=15)
    sh.paste(sub, cx, cy, angle=-2.2,
             shadow=(0, 26 * sh.scale, 34 * sh.scale, 34 * sh.scale, 0.38))
    sh.cv.save()
    sh.cv.translate(cx, cy)
    sh.cv.rotate(-2.2)
    tape = readable(bench, mix(P["paper2"], P["deep2"], 0.5), 1.6)
    for sx in (-1, 1):
        sh.cv.save()
        sh.cv.translate(sx * CW / 2, -CH / 2 + 10)
        sh.cv.rotate(38 * sx)
        sh.cv.drawRect(skia.Rect.MakeXYWH(-66 * sh.scale, -17 * sh.scale,
                                          133 * sh.scale, 34 * sh.scale),
                       paint(C(tape, 0.34)))
        sh.cv.restore()
    sh.cv.restore()
    edge_type(sh, ctx, EDGE(ctx))
    footer(sh, ctx)
FEAT_WORDS = {
    "liga": "Standard Ligatures", "dlig": "Discretionary Ligatures",
    "salt": "Stylistic Alternate", "swsh": "Swash",
    "calt": "Contextual Alternates", "aalt": "All Alternates",
    "ss01": "Stylistic Set 1", "hlig": "Historic Ligatures",
}


def feature_callout_labels(ctx):
    """Use real OpenType labels where present; never invent font capabilities."""
    available = set(ctx.get("facts", {}).get("features", ()))
    order = ("dlig", "salt", "ss01", "swsh", "liga", "calt", "aalt", "hlig")
    labels = [FEAT_WORDS[tag] for tag in order if tag in available]
    if len(labels) >= 2:
        return labels[:2]
    if labels:
        return [labels[0], "Feature Set Varies"]
    return ["Feature Set Varies", "See Available Glyphs"]


@support("feature32", "the feature card: one large specimen word inside a scalloped frame, with OpenType callouts ruled and dotted around it")
def t_feature32(sh, ctx):
    """Rebuilt from T27485_07 (Crystal, OpenType Features card).

    The reference sells the extras with the restraint of a letterpress call
    card: a flat ground, one strong ink for everything on the sheet, a scalloped
    frame cut in the same colour, and two small labels — each under (or over) a
    rule with a dot where it touches the art — annotating the lettering like a
    patent drawing. The hero is authored copy, not the font's own name: the
    brief's name-free `word` (or the widest usable word in `line`) grown across
    the card, so the panel shows the face writing something rather than introducing
    itself for the ninth time. The two callouts sit in the bands above and
    below that block with their rules *between the label and the art* — the
    dot always at the end of the rule nearest the thing it annotates, because
    an annotation whose leader points at the headline above it is pointing at
    nothing.
    """
    P, T, L = dict(ctx["pal"]), ctx["display"], ctx["label"]
    # Match the source's warm stock and oxblood print by default. Explicit CLI
    # palette/mode choices remain available for a deliberately art-directed run.
    if not ctx.get("palette_override"):
        P.update(
            deep1=(87, 69, 58), deep2=(112, 86, 66),
            paper1=(230, 219, 198), paper2=(230, 219, 198),
            ink=(157, 28, 37), glow=(255, 246, 227),
            accent=(144, 32, 22), accent2=(157, 28, 37),
        )
    if not ctx.get("mode_override"):
        P["mode"] = "paper"
    P["tone"] = tones(P, ctx["family"])
    art_ctx = dict(ctx, pal=P)
    spec_bg(sh, art_ctx, pool=0.0, tex=False)   # flat stock; frame is the furniture
    ink, _mute, _ = field(P)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(P["paper1"])
    frame = readable(gnd, P["ink"], 5.5)
    pop = readable(gnd, P["accent"], 5.0)
    # Callouts report actual GSUB capabilities where the font exposes them;
    # fallback copy keeps the annotation useful without promising absent features.
    labels = feature_callout_labels(ctx)
    head = "OpenType Features"

    # The scalloped frame: one line, corners bitten inward with a concave
    # scallop, drawn in the same ink as the type — a cut card, not a border.
    fx, fy = sh.m * 0.55, sh.m * 0.55
    fw, fh = sh.w - 2 * fx, sh.h - 2 * fy
    cr = 92 * sh.scale
    p = skia.Path()
    p.moveTo(fx, fy + cr)
    p.quadTo(fx + cr * 0.92, fy + cr * 0.92, fx + cr, fy)      # bite inward
    p.lineTo(fx + fw - cr, fy)
    p.quadTo(fx + fw - cr * 0.92, fy + cr * 0.92, fx + fw, fy + cr)
    p.lineTo(fx + fw, fy + fh - cr)
    p.quadTo(fx + fw - cr * 0.92, fy + fh - cr * 0.92, fx + fw - cr, fy + fh)
    p.lineTo(fx + cr, fy + fh)
    p.quadTo(fx + cr * 0.92, fy + fh - cr * 0.92, fx, fy + fh - cr)
    p.close()
    _stroke(sh.cv, p, frame, max(3.0, 5.2 * sh.scale), 0.96)
    t = 10 * sh.scale
    for i, b in enumerate((Box(fx, fy, fw, t), Box(fx, fy + fh - t, fw, t),
                           Box(fx, fy, t, fh), Box(fx + fw - t, fy, t, fh))):
        sh.mark(f"fr{i}", b, collide=False)

    sh.text("ht", L, head,
            Box(fx + fw * 0.18, int(sh.h * 0.125), fw * 0.64,
                int(sh.h * 0.075)),
            hi=64 * sh.scale, lo=20, max_lines=1, align="center",
            valign="top", min_read=20 * sh.scale, min_contrast=4.5,
            track=0.02, color=frame)

    # One oversized specimen word, as in the source card. The source's font
    # name is deliberately replaced; no secondary phrase competes with the
    # feature annotations.
    candidate = _support_copy(ctx, ("word", "line"), "Crystal")
    label_tokens = {token.casefold() for text in labels for token in text.split()}
    hero_words = [word.strip(".,!?;:()[]{}\"'") for word in candidate.split()]
    hero_words = [word for word in hero_words
                  if len(word) >= 3 and word.casefold() not in label_tokens]
    hero = max(hero_words, key=lambda word: T.measure(word, 100.0),
               default="Crystal")
    hero = shout(ctx, clean(ctx, hero)).strip()
    hero_box = Box(fx + fw * 0.08, int(sh.h * 0.30), fw * 0.84,
                   int(sh.h * 0.43))
    hero_size = sh.text("hero", T, hero, hero_box,
                        hi=720 * sh.scale, lo=32, max_lines=1,
                        align="center", valign="middle",
                        min_read=40 * sh.scale, min_contrast=4.5,
                        color=ink)
    if hero_size is None:
        sh.problems.append("feature32: the face draws no usable specimen word")
        return

    # The two labels sit on opposite shoulders of the large word. Their ruled
    # leaders and dots use the source's patent-drawing callout treatment.
    f0_box = Box(fx + fw * 0.34, int(sh.h * 0.235), fw * 0.34,
                 int(sh.h * 0.055))
    sh.text("f0", L, labels[0], f0_box, hi=48 * sh.scale, lo=14,
            max_lines=1, align="left", valign="top", min_read=14 * sh.scale,
            min_contrast=4.5, track=0.02, color=frame)
    s0 = _slot(sh, "f0")
    f1_box = Box(fx + fw * 0.51, int(sh.h * 0.71), fw * 0.35,
                 int(sh.h * 0.06))
    sh.text("f1", L, labels[1], f1_box, hi=48 * sh.scale, lo=14,
            max_lines=1, align="right", valign="top", min_read=14 * sh.scale,
            min_contrast=4.5, track=0.02, color=frame)
    s1 = _slot(sh, "f1")

    dot = max(4.0, 7 * sh.scale)
    if s0:
        ry = f0_box.y - 10 * sh.vscale
        x0, x1 = s0.ink.x, s0.ink.r
        rule(sh.cv, x0, ry, x1, ry, pop, max(1.6, 2.6 * sh.scale), 0.96)
        rule(sh.cv, x0, ry, x0, ry + 8 * sh.vscale,
             pop, max(1.6, 2.6 * sh.scale), 0.96)
        sh.cv.drawCircle(x0, ry + 8 * sh.vscale + dot, dot, paint(C(pop, 0.96)))
    if s1:
        ry = f1_box.y - 10 * sh.vscale
        x0, x1 = s1.ink.x, s1.ink.r
        rule(sh.cv, x0, ry, x1, ry, pop, max(1.6, 2.6 * sh.scale), 0.96)
        rule(sh.cv, x1, ry, x1, ry + 8 * sh.vscale,
             pop, max(1.6, 2.6 * sh.scale), 0.96)
        sh.cv.drawCircle(x1, ry + 8 * sh.vscale + dot, dot, paint(C(pop, 0.96)))

def blush_cloud(sh, cx, cy, half_w, half_h, base, deep, light, seed=7):
    """One irregular cloud of pale colour: a union of overlapping lobes with
    hard-ish edges and a two-step bloom, painted at 1/BG_SCALE and stretched.

    The reference's blush is a watercolour *silhouette*, not a stripe: the
    unevenness lives entirely in the outline, and the tone between the edges is
    flat — the same bargain `wash_band` struck, and for the same reason. A
    gaussian feather over a 1600-px-wide shape makes every feathered pixel a
    different number and PNG pays per pixel; here each pass is a set of opaque
    lobes blitted through one alpha, so overlapping lobes union for free and
    the whole device costs a handful of outlines. `base` is the body, `deep`
    the pigment pooling in two inner lobes (clipped to the body, so a pool can
    never escape the cloud it stains), `light` the two-step bloom. The lobes
    are spread wide against the half-extent so the silhouette itself — not a
    wider bloom — is what fills the sheet, and the bloom steps are kept tight
    because graded ring is exactly what the byte law taxes. Registers with
    `collide=False` because the lettering rides through it.
    """
    s = BG_SCALE
    pad = 10
    bw = max(2, int(2 * half_w / s) + 2 * pad)
    bh = max(2, int(2 * half_h / s) + 2 * pad)
    rnd = random.Random(seed)
    layout = [(0.5, 0.5, 0.34, 0.38)]
    for _ in range(7):
        a = rnd.uniform(0.0, 2.0 * math.pi)
        rr = rnd.uniform(0.26, 0.42)
        layout.append((0.5 + math.cos(a) * rr * 0.95, 0.5 + math.sin(a) * rr,
                       rnd.uniform(0.16, 0.30), rnd.uniform(0.20, 0.34)))
    pools = [(0.32, 0.52, 0.15, 0.20), (0.56, 0.62, 0.12, 0.15)]

    def lobe_set(scale, subset=None):
        out = []
        for fx, fy, rx, ry in (subset if subset is not None else layout):
            x = pad + (bw - 2 * pad) * (0.5 + (fx - 0.5) * scale)
            y = pad + (bh - 2 * pad) * (0.5 + (fy - 0.5) * scale)
            out.append(_cloud_lobe(x, y, (bw - 2 * pad) * rx * scale,
                                   (bh - 2 * pad) * ry * scale, rnd))
        return out

    def pass_(paths, rgb, alpha, clip=None):
        sub = skia.Surface.MakeRasterN32Premul(bw, bh)
        if sub is None:
            return
        cv = sub.getCanvas()
        if clip is not None:
            cv.clipPath(clip)
        for p in paths:
            cv.drawPath(p, paint(C(rgb)))
        sh.cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(bw, bh),
                            skia.Rect.MakeXYWH(cx - bw * s / 2.0,
                                               cy - bh * s / 2.0,
                                               bw * s, bh * s),
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kNone),
                            paint(alpha=alpha))

    pass_(lobe_set(1.10), light, 0.26)
    pass_(lobe_set(1.045), light, 0.40)
    body = lobe_set(1.0)
    union = skia.Path()
    for p in body:
        union.addPath(p)
    pass_(body, base, 0.95)
    pass_(lobe_set(1.0, pools), deep, 0.38, clip=union)
    sh.mark("cloud", Box(cx - half_w, cy - half_h, 2 * half_w, 2 * half_h),
            collide=False, bleed=True)

@support("blush32", "the blush note: a flowing multi-line phrase written at one size with its baselines deliberately unaligned — each line its own length, the block drifting sideways — riding across a pale watercolour cloud that fills most of the sheet")
def t_blush32(sh, ctx):
    """Rebuilt from T9150_03 (a handwritten quote card).

    The reference is two inks and nothing else: a pale watercolour cloud with
    a charcoal hairline sentence floating on it, three lines long, each line
    its own length and none of them sharing a margin. The difference from
    `wash32` is the silhouette — a multi-lobe cloud, not a stripe — and from
    `quote32` the typesetting: this block is one point size drifting out of a
    common column, not three lines grown to one measure. The cloud is drawn
    hard-edged at 1/BG_SCALE and stretched (rule 3: a feather would cost a
    fifth of the byte cap in nothing), and the ground is forced to the paper
    pole because a hairline hand cannot survive a dark field.
    """
    P, T = ctx["pal"], ctx["display"]
    inv = P["mode"] == "dark"                    # a cloud on paper, always
    spec_bg(sh, ctx, pool=0.06, invert=inv)
    ink, _, _ = field(P, invert=inv)
    line = shout(ctx, _support_copy(ctx, ("line", "word"),
                                    "Grow With Grace")).strip()
    words = [w for w in line.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.9):
        sh.problems.append("blush32: the face draws no usable word of this line")
        return
    stage = Box(sh.m, round(sh.h * 0.055), sh.w - 2 * sh.m, round(sh.h * 0.89))
    gap = int(round(8 * sh.vscale))

    def _cut(i, j):
        return [" ".join(words[a:b]) for a, b in ((0, i), (i, j), (j, len(words)))
                if a < b]

    def _split(n):
        """Words into n lines minimising the WIDEST line's advance.

        `pack_lines` balances by character count, which is a fair proxy on a
        narrow pen face and a bad one on a wide display cut: the size of this
        block is set by its longest line alone, so the split that wins is the
        one whose worst row is shortest. No imports, no itertools: at most
        three rows means at most a double loop over the word joins."""
        if n >= len(words):
            return list(words)
        if n == 1:
            return [" ".join(words)]
        best = None
        if n == 2:
            cuts = [(i, len(words)) for i in range(1, len(words))]
        else:
            cuts = [(i, j) for i in range(1, len(words) - 1)
                    for j in range(i + 1, len(words))]
        for i, j in cuts:
            lines = _cut(i, j) if n == 3 else [" ".join(words[:i]),
                                               " ".join(words[i:])]
            wmax = max(T.measure(ln, 100.0) for ln in lines)
            if best is None or wmax < best[0] - 1e-9:
                best = (wmax, lines)
        return best[1]

    # How deep to break the sentence: one size serves every line (this is a
    # hand writing, not a poster filling measures), so the size is the largest
    # at which the LONGEST row fits — and the best line count is simply the one
    # that makes that longest row shortest. Two words stay one line: a stack
    # of single words is a lockup, not a sentence — but three words may break
    # 2/1, since one line of three is where this gesture dies.
    nmax = min(3, (len(words) + 1) // 2) if len(words) > 2 else 1
    best = None
    for n in range(1, nmax + 1):
        lns = _split(n)
        s = min(fit_measure(T, ln, stage.w * 0.94, 900 * sh.scale) for ln in lns)
        if s <= 0:
            continue
        hs = [T.path(ln, s)[0].getBounds().height() for ln in lns]
        tot = sum(hs) + gap * (len(lns) - 1)
        k = min(1.0, stage.h / tot) if tot > 0 else 0.0
        if best is None or (s * k, len(lns)) > (best[0], len(best[1])):
            best = (s * k, lns)
    if best is None:
        sh.problems.append("blush32: no line of the phrase can be set to the measure")
        return
    size, lines = best
    # The drift: each line hangs off the column's centre by its own amount —
    # the first out to the right, the next stepped back left — so the block
    # reads as a hand moving across paper, not a stack aligned to a rod.
    drifts = ((0.02,), (0.06, -0.045), (0.075, -0.05, 0.025))[len(lines) - 1]
    boxes = [T.path(ln, size)[0].getBounds() for ln in lines]
    # Rows only share air when they interlock — a descender from one reaching
    # into the next row's space. A caps-only face stacks tight boxes, and the
    # hair leading a handwritten block wants then reads as a collision, so
    # when no row reaches below the baseline the leading opens with the size.
    if len(boxes) > 1 and max(b.height() for b in boxes) < 0.92 * size:
        gap = max(gap, int(round(0.15 * size)))
    total = sum(b.height() for b in boxes) + gap * (len(lines) - 1)
    y = stage.y + (stage.h - total) / 2.0
    # The cloud is the sheet's second subject: sized to fill most of the card
    # behind the whole block, not a swatch parked under its middle. The first
    # line's ascenders and the last line's descenders still walk out of it —
    # the blush stops behind the words, the words do not stop inside the blush.
    blush_cloud(sh, stage.x + stage.w * (0.5 + sum(drifts) / len(drifts) * 0.45),
                y + total * 0.47, int(stage.w * 0.60),
                int(min(max(total * 0.55, stage.h * 0.30), stage.h * 0.60)),
                mix(P["accent"], P["paper1"], 0.74),
                mix(P["accent"], P["paper1"], 0.52),
                mix(P["accent"], P["paper1"], 0.90))
    # The ink resolves against the cloud now under it, with a unit of margin
    # above the floor so a re-theme cannot push the guard into lifting it.
    gnd = sh._behind(Box(stage.x, y, stage.w, total)) or lum(P["paper1"])
    pop = readable(gnd, ink, 5.5)
    for i, (ln, b) in enumerate(zip(lines, boxes)):
        dx = drifts[i] * stage.w
        sh.text(f"bl{i}", T, ln,
                Box(stage.x + dx, y - 2, stage.w, b.height() + 4),
                hi=size, lo=size, max_lines=1, align="center", valign="top",
                min_read=44 * sh.scale, min_contrast=4.5, color=pop)
        y += b.height() + gap




@support("sticker32", "the die-cut: one word of the face's own language in two fat lines each grown to the measure, thrown hard to the lower right in a flat offset shadow — never the name, nothing else on the sheet")
def t_sticker32(sh, ctx):
    """Rebuilt from T24954_06 (Private Label), with the label written fresh.

    The die-cut sticker look: one saturated ink, one flat neutral shadow offset
    hard to the corner — no blur, no gradient, no rule — and the word so large
    the sheet is nothing but the word. Each line is grown to its own measure,
    so a short second word sits as a slab under the first like the reference's
    `Label`. The shadow is why the block is drawn by hand: it has to lie *under*
    the ink, and a blurred drop-shadow would read as a screenshot, not a sticker.

    What it lettered used to be the font's name — the same word the listing
    title already carries, blown up and said again. The subject is now the
    brief's one authored word (or phrase), filtered by `_sticker_phrase` so the
    name cannot reach the sheet even from a brief that authors it, and the
    buyer sees the face *used*: the wedge of a letterform at sticker size, the
    join of two words, the descender the catalogue photo cut off.

    The last thing that kept it short of a sticker was the cut itself. Ink
    straight on the wall is a painted sign, so the lettering now sits on paper:
    every stroke is grown outward by a round-joined band of the sticker's own
    stock, and the shadow is thrown by that silhouette rather than by the
    glyphs. It tips a degree or two off the level, because nothing anyone
    stuck on by hand is square. That makes three colours to settle and they
    settle in order — the stock against the measured wall, the ink against the
    stock, the shadow against the wall — since a sticker the colour of its own
    wall peels off nothing, and lettering the colour of its own sticker is
    invisible twice over.
    """
    P, T = ctx["pal"], ctx["display"]
    # `spec_bg` pins `tooth=0` for the specimen sheets, where noise says nothing;
    # here the wall is the subject, so the ground takes the speckle.
    bg(sh, P, ctx["th"], dev=False, pool=0.13, tooth=1)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(P["paper1"])
    stock = readable(gnd, mix((255, 255, 255), P["paper1"], 0.14)
                     if gnd < 0.56 else P["deep1"], 2.6)
    pop = readable(lum(stock), P["accent"], 3.2)
    shadow = readable(gnd, mix(P["deep1"], P["paper1"], 0.35), 1.7)
    phrase = _sticker_phrase(ctx)
    words = [w for w in phrase.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.9):
        sh.problems.append("sticker32: the face draws no usable word that is "
                           "not the name")
        return
    stage = Box(sh.m * 0.7, sh.h * 0.09, sh.w - 1.4 * sh.m, sh.h * 0.82)
    # The sticker is two slabs, not one band. A single wide word grown to the
    # measure sets no taller than a caption and leaves the sheet empty around it,
    # so the word breaks at the seam that leaves the halves nearest equal width —
    # the cut that reads as a stacked logotype rather than as a word sawn in two.
    lines = hero_pair(T, words, stage)

    sizes = [fit_measure(T, ln, stage.w, 820 * sh.scale) for ln in lines]
    if min(sizes) < 40 * sh.scale:
        sh.problems.append("sticker32: the phrase is too long to sticker")
        return
    boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
    off = max(8.0, 17 * sh.scale)
    # The cut band is a fixed throw around every line, not a share of each line's
    # own size: a two-word sticker is one piece of die-cut stock, and banding the
    # small line proportionally would give it a wider border than the big one.
    band = max(6.0, 0.052 * max(sizes))
    # The throw of the shadow is the leading floor, and the band rides on top of
    # it: two slabs knit closer than `off` + the band and the upper line's shadow
    # lands on the lower line's paper, which a single cut never does.
    gap = int(max(14 * sh.vscale, 1.45 * off + 2.2 * band))
    total = sum(b.height() for b in boxes) + gap * (len(lines) - 1)
    if total > stage.h:
        kk = stage.h / total
        sizes = [s * kk for s in sizes]
        band *= kk
        boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
        total = sum(b.height() for b in boxes) + gap * (len(lines) - 1)
    y = stage.y + (stage.h - total) / 2

    def cutout(path, x, dy, rgb):
        """The glyph path grown by `band` — the stock the cutter followed."""
        sh.cv.save()
        sh.cv.translate(x, dy)
        edge = paint(C(rgb, 1.0), style=skia.Paint.kStroke_Style,
                     width=2 * band)
        edge.setStrokeJoin(skia.Paint.kRound_Join)
        sh.cv.drawPath(path, edge)
        sh.cv.drawPath(path, paint(C(rgb, 1.0)))
        sh.cv.restore()

    # Nothing stuck on by hand is square, and a level block reads as a screenshot.
    tilt = ((int(ctx["th"]["seed"]) % 9) - 4) * 0.75
    sh.cv.save()
    sh.cv.translate(stage.x + stage.w / 2.0, stage.y + stage.h / 2.0)
    sh.cv.rotate(tilt)
    sh.cv.translate(-stage.x - stage.w / 2.0, -stage.y - stage.h / 2.0)
    for i, (ln, s, b) in enumerate(zip(lines, sizes, boxes)):
        p, _adv = T.path(ln, s)
        dx = stage.x + (stage.w - b.width()) / 2 - b.left()
        dy = y - b.top()
        cutout(p, dx + off, dy + off, shadow)
        cutout(p, dx, dy, stock)
        sh.cv.save()
        sh.cv.translate(dx, dy)
        sh.cv.drawPath(p, paint(C(pop, 1.0)))
        sh.cv.restore()
        sh.mark(f"st{i}", Box(b.left() + dx - band, b.top() + dy - band,
                              b.width() + 2 * band, b.height() + 2 * band),
                collide=False, bleed=True)
        y += b.height() + gap
    sh.cv.restore()
def _lit_lockup_text(ctx, pool):
    """`panel_text()` with the name-exit welded shut — for the two panels whose
    lettering must be a phrase of its own, never the face's name.

    The authored copy is read exactly like `panel_text` reads it (`word`, then a
    short `line`). Where `panel_text` then falls back to the font's own name for
    a face that cannot spell any candidate, these marquees refuse: the panel's
    pool is tried in Title Case, then a wide emergency vocabulary of short
    words any sellable face can spell. Only a face that cannot spell any of
    those reports the problem and stands down — it never prints its name.
    """
    word = tc(" ".join(clean(ctx, ctx["copy"].get("word") or "").split()))
    if word:
        return word
    line = tc(" ".join(clean(ctx, ctx["copy"].get("line") or "").split()))
    if line and len(line.split()) <= 4:
        return line
    rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
    phrases = list(pool) + ["after hours", "big night", "now open",
                            "lights up", "make a scene", "one more time",
                            "last call", "go live", "the main event"]
    order = phrases[rot % len(phrases):] + phrases[:rot % len(phrases)]
    for c in order:
        form = tc(c)
        if all(usable(ctx, ch) for ch in form if not ch.isspace()):
            return form
    # Keep the reference's two-line marquee even for unusually partial fonts:
    # its former emergency list could settle on a single word like “Onyx”,
    # leaving half of the lit sign's characteristic lockup empty.
    spare = ("night", "lights", "opening", "stage", "after", "hours",
             "one", "more", "show", "live", "good", "time", "last",
             "call", "dream", "wild", "magic", "star")
    supported = [tc(w) for w in spare
                 if all(usable(ctx, ch) for ch in tc(w))]
    if len(supported) >= 2:
        start = rot % len(supported)
        a, b = supported[start], supported[(start + 1) % len(supported)]
        form = f"{a} {b}"
        return tc(form)
    return ""

@support("neon32", "the marquee: a phrase lit like a tube on a dark wall — warm halo, film-strip perforations glowing down both edges, a small coming-soon under the last line")
def t_neon32(sh, ctx):
    """Rebuilt from T30173_07 (Jazzbury, the theatre-door card).

    The reference is a photograph of a lit sign: a grainy dark ground, the
    phrase in warm tube-white with a real bloom around the strokes, a small
    `Coming Soon` beneath, and a strip of glowing perforations marching down
    both edges like a film gate. The bloom is the product shot — the face looks
    installed somewhere at night — so the ink is one warm white, the halo does
    the colour work, and nothing else competes with the letters. The marquee
    and its coming-soon line are one block and the block is seated at the
    centre of the sheet: the perforations march past it on both sides and no
    third of the wall is left dead under the last line.
    """
    P, T = ctx["pal"], ctx["display"]
    # The source is a photographed incandescent sign on a scuffed brown-black
    # wall. Keep that material palette fixed across theme rolls: a blue or paper
    # ground changes the subject, not just its mood.
    wall = Box(0.0, 0.0, float(sh.w), float(sh.h))
    ground(sh.cv, (37, 22, 15), (18, 11, 9), sh.w, sh.h)
    light_pool(sh.cv, sh.w * 0.52, sh.h * 0.48, sh.w * 0.47,
               (173, 93, 45), 0.22, skia.BlendMode.kScreen, sh.w, sh.h)
    noise_wash(sh.cv, wall, strength=0.30, seed=3017307, cell=480)
    grain(sh.cv, wall, 0.18, seed=3017308, cell=96, magnify=5)
    vignette(sh.cv, wall, 0.10, spread=0.60)
    warm = (255, 242, 215)
    glow_c = (255, 174, 94)

    # The perforations: two columns of lit blocks with a soft bloom, and the
    # hairline of the film gate between the strip and the field.
    ph, pw = sh.h * 0.082, sh.w * 0.068
    ys = [sh.h * f for f in (0.075, 0.215, 0.355, 0.495, 0.635, 0.775, 0.915)]
    for side, xc in (("l", sh.w * 0.034), ("r", sh.w * 0.966)):
        for j, cy in enumerate(ys):
            p = skia.Path()
            p.addRoundRect(skia.Rect.MakeXYWH(xc - pw / 2, cy - ph / 2, pw, ph),
                           7 * sh.scale, 7 * sh.scale)
            halo(sh.cv, p, glow_c, 17 * sh.scale, 0.55)
            sh.cv.drawPath(p, paint(C(warm, 0.98)))
            sh.mark(f"perf{side}{j}",
                    Box(xc - pw / 2, cy - ph / 2, pw, ph),
                    collide=False, bleed=True)
    for xc in (sh.w * 0.073, sh.w * 0.927):
        rule(sh.cv, xc, sh.h * 0.02, xc, sh.h * 0.98, glow_c,
             max(1.4, 2.2 * sh.scale), 0.34)

    name = shout(ctx, _lit_lockup_text(
        ctx, ("opening night", "last call", "one night only",
              "live on stage", "the main event"))).strip()
    words = [w for w in name.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.72):
        sh.problems.append("neon32: the face draws no usable word to light up")
        return
    lines = pack_lines(words, min(2, len(words)))
    # A glow is only cheap when there is wall left around it, and a busy
    # contour spends the wall first — so the busier the face, the more of it
    # `wall` keeps clear of the lettering. The ramp itself is kept thin on
    # purpose: PNG pays for every pixel the falloff touches, and a marquee-sized
    # bloom at the widest sigma the look could tolerate put this sheet within
    # 1.6% of the byte cap, where a thinner one still reads as light.
    dens = contour_density(T, " ".join(lines))
    wall_clearance = max(0.62, min(1.0, 1.05 - 0.45 * dens))
    sw = 0.68 * wall_clearance
    stage_w = sh.w * sw
    x0 = (sh.w - stage_w) / 2.0
    sizes = [fit_measure(T, ln, stage_w, 760 * sh.scale) for ln in lines]
    boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
    gap = int(26 * sh.vscale)

    tag = clean(ctx, ctx["copy"].get("over") or ctx["copy"].get("sub") or "").strip()
    tag = tc(tag) if tag else "Coming Soon"
    tsize = fit_measure(T, tag, stage_w * 0.82, 118 * sh.scale)
    tbody = T.path(tag, tsize)[0].getBounds()
    tag_gap = int(34 * sh.vscale)

    # The whole lit stack — marquee lines plus the coming-soon line — is one
    # block, and the block is seated at the centre of the sheet. The marquee
    # used to hang from the top of a fixed stage and leave the ground below it
    # silent; the wall around a lit sign is part of the picture, but only when
    # it is balanced on every side.
    total = sum(b.height() for b in boxes) + gap * (len(lines) - 1) \
        + tag_gap + tbody.height()
    avail = sh.h * 0.86
    if total > avail:
        k = avail / total
        sizes = [s * k for s in sizes]
        boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
        tsize *= k
        tbody = T.path(tag, tsize)[0].getBounds()
        total = sum(b.height() for b in boxes) + gap * (len(lines) - 1) \
            + tag_gap + tbody.height()
    y = (sh.h - total) / 2.0
    for i, (ln, s, b) in enumerate(zip(lines, sizes, boxes)):
        sh.text(f"nm{i}", T, ln, Box(x0, y - 2, stage_w, b.height() + 4),
                hi=s, lo=s, max_lines=1, align="center", valign="top",
                min_read=40 * sh.scale, min_contrast=3.0, color=warm,
                glow=(glow_c, 0.095, 0.58))
        y += b.height() + gap
    sh.text("soon", T, tag,
            Box(x0, y + tag_gap - 2, stage_w, tbody.height() + 4),
            hi=tsize, lo=tsize, max_lines=1, align="center", valign="top",
            min_read=20 * sh.scale, min_contrast=3.0, color=warm,
            glow=(glow_c, 0.095, 0.52))

def t_loop32(sh, ctx):
    """Rebuilt from T25756_00 (Jingers).

    The reference is a logotype reveal, not a layout: one connected-script word
    grown until it is the picture, level on a flat butter ground, and only three
    pieces of furniture share the sheet — a hairline ellipse of tracked caps
    ("PROUDLY PRESENT") hovering over the left shoulder, a ringed founder's
    monogram perched over the right, and one quiet tracked line of the
    descriptor underneath. Two inks, no third tone, no rule, no shadow, and the
    emptiness is the design: everything but the word stays small.

    The catalogue already owns three kinds of big name — `sticker32` (two fat
    lines with an offset shadow), `cast32` (two lines climbing with a cast),
    `ripple32` (centre-set inside waves) — and `pill32` owns the giant badge
    with the (R) disc. What none of them owns is the *single unbroken line at
    the face's own slant on an almost-empty sheet*, so the word is set once,
    straight, grown to the measure, and the halo ellipse and disc are placed by
    walking them off the real ink until the outlines genuinely clear it.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    inv = P["mode"] == "dark"                    # the sheet prints on paper
    spec_bg(sh, ctx, pool=0.0, invert=inv)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(P["paper1"])
    ink = readable(gnd, P["ink"], 5.5)           # the one drawing ink, pre-resolved
    name = shout(ctx, _lit_lockup_text(
        ctx, ("halo", "orbit", "encore", "compass", "aurora",
              "crest", "lantern", "vow"))).strip()
    words = [w for w in name.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.9):
        sh.problems.append("loop32: the face draws no usable word of this phrase")
        return
    # One word carries the logotype — the heaviest one, so the line has mass.
    word = max(words, key=len)

    # The word is seated at the centre of the sheet, not hung from its top: the
    # halo hovers above it, the descriptor sits under it, and the whole lockup
    # reads as one block placed in the ground. The stage keeps the word's own
    # ink band off the furniture lines at the top and foot of the sheet.
    stage = Box(sh.m * 0.55, sh.h * 0.21, sh.w - 1.1 * sh.m, sh.h * 0.545)
    size = fit_measure(T, word, stage.w, 900 * sh.scale)
    if size <= 0:
        sh.problems.append("loop32: the word cannot be set to the measure")
        return
    wb0 = T.path(word, size)[0].getBounds()
    if wb0.height() > stage.h:
        size *= stage.h / wb0.height()
    if size < 40 * sh.scale:
        sh.problems.append("loop32: the name is too long to halo")
        return
    sh.text("word", T, word, stage, hi=size, lo=size, max_lines=1,
            align="center", valign="middle", min_read=44 * sh.scale,
            min_contrast=5.0, color=ink)
    wb = _slot(sh, "word")
    if not wb:
        return
    # `T.path` answers in pen coordinates (baseline at y=0); the hover searches
    # run in canvas space, so carry the outline to where the slot actually drew
    # it — the slot's own ink box is the translation.
    word_path = T.path(word, wb.size)[0]
    _pb = word_path.getBounds()
    word_path.offset(wb.ink.x - _pb.x(), wb.ink.y - _pb.y())

    # --- the halo: a hairline ellipse of tracked caps over the left shoulder.
    # It is sized from its own text, then HOVERED: for a few candidate anchors
    # along the word's left half we binary-search the lowest centre whose oval
    # still clears the real ink, and keep the one that may hang deepest — the
    # reference's ellipse sits in whatever gap the hand left, never on top of
    # a stroke, so the placement is a fact about these outlines, not a fraction.
    over = " ".join(tc(clean(ctx, ctx["copy"].get("over") or "").strip()
                     or "Proudly Present").split())
    track = 0.22
    s_t = 42 * sh.scale
    while s_t > 18 * sh.scale:
        tw = L.path(over, s_t, s_t * track)[0].getBounds().width()
        if tw <= sh.w * 0.21:
            break
        s_t *= 0.9
    tb = L.path(over, s_t, s_t * track)[0].getBounds()
    pad = 30 * sh.scale
    a_e = (tb.width() + 2 * pad) / 2.0
    b_e = max(a_e * 0.27, (s_t * 1.75) / 2.0)
    def _oval(cx, cy, a, b):
        p = skia.Path()
        p.addOval(skia.Rect.MakeXYWH(cx - a, cy - b, 2 * a, 2 * b))
        return p
    def _hover(cand_x, a, b, floor_y, ceil_y):
        """Lowest centre y on `cand_x` whose disc clears the word's ink."""
        lo, hi = floor_y, ceil_y
        if lo > hi:
            return None
        for _ in range(16):
            mid = (lo + hi) / 2
            if _paths_touch(word_path, _oval(cand_x, mid, a, b)):
                hi = mid
            else:
                lo = mid
        if _paths_touch(word_path, _oval(cand_x, lo, a, b)):
            return None
        return lo
    floor_y = sh.h * 0.052 + b_e
    # The ring may sink into the word's band, but the tracked line inside it
    # may not touch the word's ink box — so the deepest hover keeps the tag's
    # own descender line clear of the tallest stroke on the sheet.
    ceil_y = min(wb.ink.y + b_e * 0.45, wb.ink.y - s_t * 0.85)
    best = None
    for f in (0.30, 0.24, 0.36, 0.42, 0.20, 0.50, 0.16, 0.58):
        cx = wb.ink.x + wb.ink.w * f
        cy = _hover(cx, a_e, b_e, floor_y, ceil_y)
        if cy is not None and (best is None or cy > best[1] + b_e * 0.12):
            best = (cx, cy)
        if best and best[1] >= wb.ink.y - b_e * 0.2:
            break
    if best is None:
        best = (wb.ink.x + wb.ink.w * 0.30, floor_y)
    cx_e, cy_e = best
    sh.cv.drawOval(skia.Rect.MakeXYWH(cx_e - a_e, cy_e - b_e, 2 * a_e, 2 * b_e),
                   paint(C(ink, 1.0), style=skia.Paint.kStroke_Style,
                         width=max(1.6, 2.6 * sh.scale)))
    sh.mark("halo", Box(cx_e - a_e, cy_e - b_e, 2 * a_e, 2 * b_e),
            collide=False)
    sh.text("halotxt", L, over,
            Box(cx_e - a_e + pad * 0.55, cy_e - b_e * 0.78,
                2 * (a_e - pad * 0.55), 2 * b_e * 0.78),
            hi=s_t, lo=12 * sh.scale, max_lines=1, align="center",
            valign="middle", track=track, min_read=15 * sh.scale,
            min_contrast=5.0, color=ink)

    # --- the disc: a ringed monogram perched over the right shoulder, the
    # reference's founder's mark. It hovers above the word's LAST stroke's own
    # sky — measured from the real ink in a band at the right edge — not above
    # the tallest letter of the whole word, and it is drawn by hand (not a
    # text slot) so the mark may sit down inside the word's band the way the
    # reference's does without tripping the box checker.
    mono = "".join(w[0] for w in words)[:2].upper()
    mono = "".join(c for c in mono if usable(ctx, c)) or "R"
    rr = 25 * sh.scale
    ib = wb.ink
    # `Region.setPath` only answers when the path is walked near the origin (as
    # `_paths_touch` does it), so the band is measured in a translated copy.
    x0 = int(ib.r - ib.w * 0.20)
    y0 = int(ib.y)
    clip = skia.Region()
    clip.setRect(skia.IRect(0, 0, int(ib.w * 0.20) + 1, int(ib.h) + 1))
    qp = skia.Path(word_path)
    qp.offset(-x0, -y0)
    reg = skia.Region()
    if reg.setPath(qp, clip) and not reg.getBounds().isEmpty():
        shoulder = y0 + reg.getBounds().top()
    else:
        shoulder = ib.y
    cx_d = min(wb.ink.r - rr * 0.45, sh.w - 6 - rr)
    cy_d = max(shoulder - rr * 1.15, sh.h * 0.052 + rr)
    disc_p = _oval(cx_d, cy_d, rr, rr)
    lift = 0
    while _paths_touch(word_path, disc_p) and lift < 12:
        cy_d -= rr * 0.4
        lift += 1
        disc_p = _oval(cx_d, cy_d, rr, rr)
    sh.cv.drawOval(skia.Rect.MakeXYWH(cx_d - rr, cy_d - rr, 2 * rr, 2 * rr),
                   paint(C(ink, 1.0), style=skia.Paint.kStroke_Style,
                         width=max(1.4, 2.2 * sh.scale)))
    sh.mark("disc", Box(cx_d - rr, cy_d - rr, 2 * rr, 2 * rr), collide=False)
    ms = rr * (0.95 if len(mono) > 1 else 1.15)
    mp = L.path(mono, ms, ms * 0.06)[0]
    mb = mp.getBounds()
    mdx = cx_d - (mb.x() + mb.right()) / 2.0
    mdy = cy_d - (mb.y() + mb.bottom()) / 2.0
    sh.cv.save()
    sh.cv.translate(mdx, mdy)
    sh.cv.drawPath(mp, paint(C(ink, 1.0)))
    sh.cv.restore()
    sh.mark("mono", Box(mb.x() + mdx, mb.y() + mdy, mb.width(), mb.height()),
            collide=False)

    # --- the descriptor: one quiet tracked line under the word, centred, the
    # same ink, much smaller — the reference's `MONOLINE SCRIPT TYPEFACE`.
    sub = clean(ctx, ctx["copy"].get("sub") or "").strip()
    if not sub:
        sub = {"script": "connected pen script", "brush": "modern brush script",
               "blackletter": "a bold blackletter", "serif": "a display serif",
               }.get(ctx["family"], "a display typeface")
    sub = " ".join(tc(sub).split())
    # A tall script word parks its bottom near the foot and wants the line
    # tucked right under it; a wide short display word floats higher, so the
    # descriptor keeps a seat of its own near the foot of the sheet — the
    # lockup (halo, word, line) spans the ground top to bottom and no third of
    # the sheet is left dead under the last element.
    dy = max(wb.ink.b + int(round(0.042 * sh.h)), int(round(0.795 * sh.h)))
    dy = min(dy, int(round(0.862 * sh.h)))
    sh.text("desc", L, sub,
            Box(sh.m * 0.8, dy, sh.w - 1.6 * sh.m, int(round(52 * sh.vscale))),
            hi=36 * sh.scale, lo=16 * sh.scale, max_lines=1, align="center",
            valign="top", track=0.16, min_read=15 * sh.scale,
            min_contrast=5.0, color=ink)



def _tube_bloom(cv, p, rgb, sigma, alpha, s=8):
    """A marquee bloom at a fraction of the bytes a full-res gaussian costs.

    PNG pays for the area of graded tone, and `halo` already buys its cheapness
    by rendering the blur at quarter scale and stretching it. A neon spread that
    reaches a real three-sigma ramp at marquee size still sat within 1% of the
    byte cap that way. This does the same trick one step further out — with one
    guard that the eighth scale makes *load-bearing*: the gaussian must stay
    resolvable on the small surface (measured: a sub-pixel `sigma/s` blur comes
    back as blocky aliased mush and the sheet gains a hundred kilobytes, not
    loses one). So the blur is floored at ~2.2 px on the surface and the caller
    gets `max(sigma, 2.2*s)` of spread for free — which for a bloom is the
    right direction to err. A smooth ramp stretched from eighth scale is pure
    continuous tone; PNG spends almost nothing on it and the eye cannot find
    the grid. Small paths (under `HALO_MIN`) are not worth a second surface at
    all and are drawn straight, exactly as `halo` does.
    """
    b = p.getBounds()
    sigma = max(sigma, 2.2 * s)
    pad = 3.0 * sigma + 2.0
    vw, vh = b.width() + 2 * pad, b.height() + 2 * pad
    if min(vw, vh) < HALO_MIN:
        cv.drawPath(p, paint(C(rgb, alpha), blur=sigma))
        return
    sw_, sh_ = max(1, int(vw / s)), max(1, int(vh / s))
    sub = skia.Surface.MakeRasterN32Premul(sw_, sh_)
    if sub is None:
        cv.drawPath(p, paint(C(rgb, alpha), blur=sigma))
        return
    scv = sub.getCanvas()
    scv.scale(1.0 / s, 1.0 / s)
    scv.translate(-(b.left() - pad), -(b.top() - pad))
    # The filter works in device pixels, so the sigma shrinks with the surface.
    scv.drawPath(p, paint(C(rgb, alpha), blur=sigma / s))
    cv.save()
    cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(sw_, sh_),
                     skia.Rect.MakeXYWH(b.left() - pad, b.top() - pad, vw, vh),
                     skia.SamplingOptions(skia.FilterMode.kLinear,
                                          skia.MipmapMode.kNone))
    cv.restore()

@support("quote32", "the say-so: the line quoted like a sign-writer's showpiece — three staggered lines grown to the measure in one ink, the face's own quote marks opening and closing the block")
def t_quote32(sh, ctx):
    """Rebuilt from T24954_05 (Just Like Sweet Chocolate).

    The source is a cream card with a saturated cobalt quote: four words in a
    broad, short, broad three-line rhythm, with the opening and closing marks
    hung outside the type. Its contrast comes from that blue-on-paper pairing,
    not a theme-roll's unrelated neon ink and dark ground.
    """
    T = ctx["display"]
    paper = (248, 246, 237)
    ground(sh.cv, paper, (244, 241, 230), sh.w, sh.h)
    grain(sh.cv, Box(0.0, 0.0, float(sh.w), float(sh.h)),
          0.025, seed=2495405, cell=96, magnify=6)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(paper)
    blue = readable(gnd, (28, 70, 190), 4.5)
    line = shout(ctx, _support_copy(ctx, ("line", "word"),
                                    "Just Like Sweet Chocolate")).strip()
    words = [w for w in line.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.8):
        sh.problems.append("quote32: the face draws no usable word of this line")
        return
    stage = Box(sh.w * 0.08, sh.h * 0.075, sh.w * 0.84, sh.h * 0.85)
    gap = int(10 * sh.vscale)

    def _set(n):
        """Pack the line into n staggered rows and return (lines, anchors,
        sizes, boxes, k) — k is how far the block had to shrink to stand up."""
        lines = pack_lines(words, n)
        # The lean: the short line is hung off the measure and on the other side
        # of the block, so the full lines bracket a narrower one.
        fracs, anchors = ((0.98, 0.62, 1.0), ("left", "center", "left")) \
            if len(lines) == 3 else \
            ((0.86, 1.0), ("right", "left")) if len(lines) == 2 else \
            ((1.0,), ("left",))
        sizes = [fit_measure(T, ln, stage.w * f, 640 * sh.scale)
                 for ln, f in zip(lines, fracs)]
        # A short measure alone does not make a small line — three letters filled
        # to it come back taller than nine. The lean needs the short line capped
        # below its neighbours in *height* as well as width, or it reads as a stack.
        full = [s for s, f in zip(sizes, fracs) if f >= 1.0]
        if full:
            sizes = [min(s, min(full) * (0.35 + 0.65 * f)) if f < 1.0 else s
                     for s, f in zip(sizes, fracs)]
        boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
        total = sum(b.height() for b in boxes) + gap * (len(lines) - 1)
        k = min(1.0, stage.h / total) if total > 0 else 0.0
        if k < 1.0:
            sizes = [s * k for s in sizes]
            boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
            total = sum(b.height() for b in boxes) + gap * (len(lines) - 1)
        return lines, anchors, sizes, boxes, total, k

    # A short line of few words fills the measure at a size too tall for the
    # sheet, and shrinking it back leaves the block floating in the middle of the
    # ground. Better to break it one line sooner and let the letters stay big.
    best = _set(min(3, len(words)))
    for n in range(min(3, len(words)) - 1, 0, -1):
        if best[5] >= 0.82:
            break
        best = _set(n)
    lines, anchors, sizes, boxes, total, _ = best
    y = stage.y + (stage.h - total) / 2
    for i, (ln, s, b) in enumerate(zip(lines, sizes, boxes)):
        tbox = Box(stage.x, y - 2, stage.w, b.height() + 4)
        lgnd = sh._behind(tbox) or gnd
        lpop = readable(lgnd, blue, 4.5)
        # A restrained edge bloom keeps the hand-lettered sign quality without
        # washing out the crisp blue strokes on the pale source-like ground.
        lit = mix(lpop, (255, 255, 255), 0.55)
        sh.text(f"qt{i}", T, ln, tbox,
                hi=s, lo=s, max_lines=1, align=anchors[i], valign="top",
                min_read=44 * sh.scale, min_contrast=4.5, color=lpop,
                glow=(lit, 0.013, 0.16))
        y += b.height() + gap
    first, last = _slot(sh, "qt0"), _slot(sh, f"qt{len(lines) - 1}")
    if not (first and last):
        return
    # The face quotes itself: its own ` and " hung outside the two full lines
    # that open and close the block, sized off the line they touch. A face with
    # no straight-quote glyphs loses the marks rather than a substituted box.
    if usable(ctx, '"'):
        def _q(target_h):
            s = 200.0
            h = T.path('"', s)[0].getBounds().height() or 1.0
            return s * target_h / h

        def _hang(name, box, off, y):
            # A two-word line filled to the measure is tall enough that a mark
            # scaled off its own height would run past the sheet: the gutter, not
            # the line, is the mark's ceiling. `off` is where the mark starts, in
            # widths of the mark itself, measured from the line's ink edge.
            q = _q(min(box.ink.h * 0.19, sh.h * 0.070))
            b = T.path('"', q)[0].getBounds()
            x = (box.ink.x if off < 0 else box.ink.r) + off * b.width()
            mb = Box(min(max(x, sh.m * 0.35), sh.w - sh.m * 0.35 - b.width()),
                     y, b.width() * 1.3, b.height() + 4)
            # The mark hangs outside the line, so it rides ground the line's own
            # measurement never saw: resolve it against the strip it lands in.
            mg = sh._behind(mb) or gnd
            mpop = readable(mg, blue, 4.5)
            sh.text(name, T, '"', mb,
                    hi=q, lo=q, max_lines=1, align="left", valign="top",
                    min_read=16 * sh.scale, min_contrast=4.5, color=mpop,
                    glow=(mix(mpop, paper, 0.45), 0.025, 0.14))

        _hang("qo", first, -1.12, first.ink.y + first.ink.h * 0.02)
        _hang("qc", last, 0.12, last.ink.y + last.ink.h * 0.02)




def _crest_arch(sh, T, text, cx, cy, r, size, sweep, up, color, track=0.0,
                name="arch", alpha=1.0, features=None):
    if not text or not text.strip() or r <= 0 or size <= 0:
        return None
    gs = T.runs(text, size, features)
    if not gs:
        return None
    f = T.font(size)
    items = []
    for gid, adv, xo, yo in gs:
        gp = f.getPath(gid)
        b = gp.getBounds()
        step = max(adv, 0.0) if b.isEmpty() else max(adv, b.width())
        items.append((gp, b, xo, yo, step))
    total = sum(it[4] for it in items) + track * max(len(items) - 1, 0)
    th = float(sweep) if sweep else total / r
    if th <= 0 or th > 2.6:
        sh.problems.append(f"{name}: {th:.2f} rad of arc will not read as lettering")
        return None
    q = paint(C(color, alpha)) if isinstance(color, tuple) \
        else paint(color or skia.Color4f(0, 0, 0, alpha))
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    pen, drawn = 0.0, 0
    for gp, b, xo, yo, step in items:
        mid = pen + step / 2.0 - total / 2.0
        pen += step + track
        if b.isEmpty():
            continue
        a = mid / r
        # The glyph rides the circle at parameter `a`; its own rotation is `a`
        # for an up-arch and -a for a down-arch (tops toward the centre).
        ang = a if up else -a
        sa, ca = math.sin(a), math.cos(a)
        px = cx + r * sa
        py = (cy - r * ca) if up else (cy + r * ca)
        ra, rb = math.sin(ang), math.cos(ang)
        ox = xo - (b.left() + b.right()) / 2.0
        oy = -yo
        gp.offset(ox, oy)
        sh.cv.save()
        sh.cv.translate(px, py)
        sh.cv.rotate(math.degrees(ang))
        sh.cv.drawPath(gp, q)
        sh.cv.restore()
        for lx, ly in ((b.left() + ox, b.top() + oy), (b.right() + ox, b.top() + oy),
                       (b.left() + ox, b.bottom() + oy),
                       (b.right() + ox, b.bottom() + oy)):
            wx, wy = px + lx * rb - ly * ra, py + lx * ra + ly * rb
            x0, y0 = min(x0, wx), min(y0, wy)
            x1, y1 = max(x1, wx), max(y1, wy)
        drawn += 1
    if not drawn:
        return None
    box = Box(x0, y0, x1 - x0, y1 - y0)
    sh.mark(name, box, collide=True)
    return box
@support("crest32", "the crest: an open frame of paired corner brackets around a three-part lockup — the phrase arched over the word, a second arched under it, one ink on a flat field")
def t_crest32(sh, ctx):
    """Rebuilt from T27485_08 (Escape from Ordinary).

    The reference's whole argument is the arch: a flat ground, one cream ink for
    everything, four corner motifs drawn as two offset right-angle brackets each (an open
    frame, not a box), and a lockup in the middle — a short phrase curved UP over
    a single dominant word at full width, a second phrase curved DOWN beneath it.
    The arched lines are set on an invisible circle and read as ornament, not
    body copy; `arc_text` is the primitive that makes them. Everything scales off
    the sheet: the chord of each arch is a fraction of the width, the word is
    grown to its own measure, and the block is centred by its real ink.
    """
    T = ctx["display"]
    # A slanted hand turned onto a circle collides at the ends of the sweep: its
    # ink leans further off the tangent than its advance can pay for. The
    # reference never asks the script to do that — its arches are a plain upright
    # companion and only the word carries the hand, so do the same here.
    A = ctx["label"] if ctx["family"] in FLOWING else T
    # Keep the reference's strong red/ivory print instead of letting the theme
    # roll muddy the background toward burgundy or swap it to another world.
    ground(sh.cv, (184, 24, 37), (170, 18, 31), sh.w, sh.h)
    pop = (255, 244, 220)
    wt = max(4.0, 9.0 * sh.scale)

    def bracket_line(x1, y1, x2, y2):
        path = skia.Path()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        halo(sh.cv, path, pop, 4.5 * sh.scale, 0.20)
        q = paint(C(pop), style=skia.Paint.kStroke_Style, width=wt)
        q.setStrokeCap(skia.Paint.kButt_Cap)
        sh.cv.drawPath(path, q)

    # The source uses two offset Ls per corner: a short horizontal paired with
    # a long vertical, then a long horizontal paired with a short vertical.
    # Keeping them as independent right-angle brackets removes the old plus-like
    # crossings and preserves the generous open red margins.
    fx, fy = sh.w * 0.035, sh.h * 0.060
    ix, iy = sh.w * 0.055, sh.h * 0.035
    short_w, long_w = sh.w * 0.075, sh.w * 0.205
    long_h, short_h = sh.h * 0.225, sh.h * 0.090
    for sx in (1, -1):
        for sy in (1, -1):
            x0, y0 = (fx if sx > 0 else sh.w - fx,
                      fy if sy > 0 else sh.h - fy)
            x1, y1 = (ix if sx > 0 else sh.w - ix,
                      iy if sy > 0 else sh.h - iy)
            bracket_line(x0, y0, x0 + sx * short_w, y0)
            bracket_line(x0, y0, x0, y0 + sy * long_h)
            bracket_line(x1, y1, x1 + sx * long_w, y1)
            bracket_line(x1, y1, x1, y1 + sy * short_h)
            xs = (x0, x0 + sx * short_w, x1, x1 + sx * long_w)
            ys = (y0, y0 + sy * long_h, y1, y1 + sy * short_h)
            bx, by = min(xs), min(ys)
            bw, bh = max(xs) - bx, max(ys) - by
            sh.mark(f"br{'lr'[sx > 0]}{'tb'[sy > 0]}",
                    Box(bx - wt, by - wt, bw + 2 * wt, bh + 2 * wt),
                    collide=False)

    # Copy, defensively: word -> the dominant display word, line -> the upper
    # arch, over/sub -> the lower arch; every piece falls back to a fact.
    word = shout(ctx, _support_copy(ctx, ("word", "line"), "Ordinary")).strip()
    if not word or not T.fit(word, 100.0, sh.w * 0.66):
        sh.problems.append("crest32: the face draws no dominant word")
        return
    # Caps, the way a crest is engraved: an arch of lowercase collides with
    # itself at the ends of the sweep, where the tangent turns one descender into
    # its neighbour, and small letters on a curve read as a mistake rather than a
    # device.
    top = _support_copy(ctx, ("line", "over"), "Escape From")
    bot = _support_copy(ctx, ("sub",), "Adventure")

    # The arch plan: chord -> radius -> the size whose advance fills the arc,
    # with the ink envelope measured from the real glyph bounds. A long phrase
    # widens its chord before it shrinks its letters: an arch set small is just
    # curved body copy, and this is the ornament.
    th = 1.12                                   # radians of arch for a full chord
    kk = th / (2 * math.sin(th / 2))

    def plan(text, c):
        m100 = A.measure(text, 100.0)
        if m100 <= 0:
            return None
        den = m100 + 13.0 * max(len(text) - 1, 0)
        s = 100.0 * c * kk / den
        if s < 30 * sh.scale:
            c = min(0.60 * sh.w, 30 * sh.scale * den / (100.0 * kk))
            s = 100.0 * c * kk / den
        s = min(s, 132 * sh.scale)
        r = c / (2 * math.sin(th / 2))
        track = 0.13 * s
        # Mirror arc_text's own spacing rule so the planned sweep and sagitta
        # match what the helper will actually draw.
        f = A.font(s)
        runs = A.runs(text, s)
        bs, steps = [], 0.0
        for gid, adv, _xo, _yo in runs:
            b = f.getPath(gid).getBounds()
            steps += max(adv, 0.0) if b.isEmpty() else max(adv, b.width())
            if not b.isEmpty():
                bs.append(b)
        ta = min(th, (steps + track * max(len(runs) - 1, 0)) / r)
        cap = min(b.top() for b in bs) if bs else -0.70 * s
        desc = max(b.bottom() for b in bs) if bs else 0.0
        sag = r * (1 - math.cos(ta / 2))
        # The checker sees the rotated AABB of every glyph, so the envelope is
        # the rotated ink box of the end glyphs measured exactly like arc_text
        # draws it: `rise`/`fall` are the arch's extremes relative to its apex
        # baseline (centre of the circle side positive-down).
        wmax = max((b.width() for b in bs), default=0.0)
        ch, sh_ = math.cos(ta / 2), math.sin(ta / 2)
        rise = min(cap, -sag + cap * ch - (wmax / 2) * sh_)
        fall = max(desc, sag + desc * ch + (wmax / 2) * sh_)
        return dict(c=c, r=r, s=s, track=track, ta=ta, cap=cap, desc=desc,
                    sag=sag, rise=rise, fall=fall, ext=fall - rise)

    wc = 0.74 * sh.w
    wsize = fit_measure(T, word, wc, 760 * sh.scale)
    wb = T.path(word, wsize)[0].getBounds()
    pu, pd = plan(top, 0.43 * sh.w), plan(bot, 0.43 * sh.w)
    if not (pu and pd):
        sh.problems.append("crest32: the face draws no usable arch phrase")
        return
    gap = 46 * sh.vscale
    total = pu["ext"] + wb.height() + pd["ext"] + 2 * gap
    stage_h = sh.h * 0.90
    k = min(1.0, stage_h / total) if total > 0 else 0.0
    if k < 1.0:
        wc *= k
        wsize = fit_measure(T, word, wc, 760 * sh.scale)
        wb = T.path(word, wsize)[0].getBounds()
        pu, pd = plan(top, pu["c"] * k), plan(bot, pd["c"] * k)
        total = pu["ext"] + wb.height() + pd["ext"] + 2 * gap
    if min(pu["s"], pd["s"]) < 24 * sh.scale:
        sh.problems.append("crest32: an arch phrase is too long to stay legible")
        return

    ystart = (sh.h - total) / 2
    yb_up = ystart - pu["rise"]                  # baseline at the upper arch apex
    cy_up = yb_up + pu["r"]
    _crest_arch(sh, A, top, sh.w / 2, cy_up, pu["r"], pu["s"], pu["ta"], up=True,
                color=pop, track=pu["track"], name="arch0")
    wy = yb_up + pu["fall"] + gap
    sh.text("word", T, word, Box(sh.w / 2 - wc / 2, wy, wc, wb.height() + 4),
            hi=wsize, lo=wsize, max_lines=1, align="center", valign="top",
            min_read=44 * sh.scale, min_contrast=3.5, color=pop)
    yb_dn = wy + wb.height() + gap - pd["rise"]
    cy_dn = yb_dn - pd["r"]
    _crest_arch(sh, A, bot, sh.w / 2, cy_dn, pd["r"], pd["s"], pd["ta"], up=False,
                color=pop, track=pd["track"], name="arch1")







# --- NEW module-level helper — belongs with the other drawing helpers, just
# --- before main() (i.e. after t_quote32). Nothing else calls it; only tilt32 does.
def _tilt_bbox(pts, ang, px, py):
    """Axis-aligned page box of a point list rotated `ang` degrees about (px, py).

    skia rotates clockwise for positive angles on a y-down canvas, so a
    counter-clockwise lean is a negative angle. The box is conservative — it
    holds the corners of an upright box, not the tight ink — which is exactly
    what the fit wants: whatever stands inside it is inside the sheet.
    """
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    xs, ys = [], []
    for x, y in pts:
        dx, dy = x - px, y - py
        xs.append(px + dx * ca - dy * sa)
        ys.append(py + dx * sa + dy * ca)
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)




def _paperway(P, family):
    """The paper side of a palette as a full colourway: the same six values,
    read as light ground and dark ink, with the ladder recomputed for that
    mode. The reference's two cards are both papers — cool and warm — so the
    twin prints on the light side of each world whatever the world's own mode."""
    Q = dict(P, mode="paper")
    Q["tone"] = tones(Q, family)
    return Q


def _twin_companion(ctx):
    """The companion palette for the right-hand card, or None when the run
    collapsed the pair (a `--palette` override pins both themes to one)."""
    key = ctx["themes"].get("twin32") or THEME_PREF["twin32"][0]
    cls = ctx.get("class") or "elegant"
    cands = [t for t in THEME_NAMES
             if THEMES[t].get("cls") in (None, cls)
             and THEMES[t]["pal"] != THEMES[key]["pal"]]
    if not cands:
        return None
    rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
    _th2, pal2 = theme_for(
        "twin32", dict(ctx, themes=dict(ctx["themes"], twin32=cands[rot % len(cands)])))
    if pal2["paper1"] == ctx["pal"]["paper1"]:
        return None
    return pal2




def _wave_ring(cx, cy, a, b, amp, k, n, rev=False):
    """A closed rippling ellipse: the point at angle theta sits at radius
    `base + amp * sin(k * theta)` on an ellipse of semi-axes (a, b).

    The modulation scales with each axis (`amp * b / a` vertically) so the
    crests stand up the same fraction of the radius all the way round — a wave
    that pinches at the sides of a wide sheet is the failure mode this avoids.
    `n` is the whole smoothness budget: a polyline reads smooth once the chord
    sag is sub-pixel, and every extra sample is edge the PNG has to encode.
    `rev` winds the ring the other way, which is what punches the hole in a
    band built from two of these.
    """
    p = skia.Path()
    for j in range(n + 1):
        th = math.tau * (n - j if rev else j) / n
        w = amp * math.sin(k * th)
        x, y = cx + (a + w) * math.cos(th), cy + (b + w * b / a) * math.sin(th)
        if j == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    return p


def _wave_band(cx, cy, a, b, amp, k, n, ta, tb):
    """The thick swell: one fill between an outer ring and one inset (ta, tb).

    Outer wound forward, inner wound back, so the default winding fill leaves
    the pale gap as a hole — the band and the field inside it are one draw.
    """
    p = _wave_ring(cx, cy, a, b, amp, k, n)
    p.addPath(_wave_ring(cx, cy, a - ta, b - tb, amp, k, n, rev=True))
    return p





def wordmark_block(T, words, width, hi, lead=0.05):
    """Typeset `words` as a wordmark block ONCE.

    Returns dict(lines, sizes, items, uw, uh) where items is
    [(path, box, ink_top)] with every line's ink centred on x=0 and stacked
    down from y=0, and (uw, uh) is the union ink envelope. Each line is grown
    to `width` with fit_measure and the words balanced with pack_lines, so the
    SAME object can be painted at letter size and again as a watermark without
    a second pass through the shaper. None if the face cannot set a line.
    """
    words = [w for w in words if w]
    if not words:
        return None
    lines = pack_lines(words, min(2, len(words)))
    items, sizes = [], []
    for ln in lines:
        s = fit_measure(T, ln, width, hi)
        if s <= 0:
            return None
        p, _ = T.path(ln, s)
        b = p.getBounds()
        if b.isEmpty() or b.height() <= 0:
            return None
        items.append((p, b, 0.0))
        sizes.append(s)
    gap = lead * max(b.height() for _p, b, _y in items)
    y = 0.0
    for i, (p, b, _y0) in enumerate(items):
        items[i] = (p, b, y)
        y += b.height() + gap
    return dict(lines=lines, sizes=sizes, items=items,
                uw=max(b.width() for _p, b, _y in items), uh=y - gap)


def paint_block(sh, block, cx, top, k, q, name, collide=True, bleed=False):
    """Paint a wordmark_block as one unit centred on x=`cx`, ink top at
    `top`, scaled `k` about that point; register each line's page-space ink
    box. The echo and the lettering both call this on the same block — the
    only difference is the (k, paint) pair, so the two can never drift.
    """
    sh.cv.save()
    sh.cv.translate(cx, top)
    if k != 1.0:
        sh.cv.scale(k, k)
    for p, b, y in block["items"]:
        sh.cv.save()
        sh.cv.translate(-(b.left() + b.right()) / 2.0, y - b.top())
        sh.cv.drawPath(p, q)
        sh.cv.restore()
    sh.cv.restore()
    for i, (_p, b, y) in enumerate(block["items"]):
        sh.mark(f"{name}{i}", Box(cx - k * b.width() / 2.0, top + k * y,
                                  k * b.width(), k * b.height()),
                collide=collide, bleed=bleed)
@support("sign32", "the shop sign: a three-line display phrase grown to a diamond over one painted brush swash — a flat ground, a single ink, the address lettered small below")
def t_sign32(sh, ctx):
    """Rebuilt from T27072_08 (Astro Coffee Roasters).

    The whole sheet is a hand-painted sign set in the display face and nothing
    else: three lines of the name, each grown to its own measure so the block
    stands as a diamond (short, long, short), one tapered brush swash as the
    only divider, and two small lettered lines below where the address would
    go. No frame, no second colour, no device — the taper of the swash is the
    whole personality, so it is drawn as a filled outline, not a stroked rule.
    """
    P, T = ctx["pal"], ctx["display"]
    # The sign is always painted on a pale board: invert only when the rolled
    # world is a dark one, never when it is already paper. One ink, flat ground,
    # no device — the reference has no second colour and no texture worth naming.
    spec_bg(sh, ctx, pool=0.0, invert=(P["mode"] == "dark"))
    ink = P["ink"]                             # one ink for the whole sheet
    c = ctx["copy"]

    # This is a type specimen, not another name card: use a short display phrase
    # and let its line lengths make the sign's diamond.
    phrase = shout(ctx, _support_copy(ctx, ("word", "line"),
                                      "Letters Make Meaning")).strip()
    nw = [w for w in phrase.split() if w]
    parts = nw[:3]
    spares = []
    for k in ("line", "word", "over"):
        s = " ".join(shout(ctx, _support_copy(ctx, (k,), "")).split())
        if s and s not in parts and s not in spares:
            spares.append(s)
    while len(parts) < 3 and spares:
        parts.append(spares.pop(0))
    if not parts:
        sh.problems.append("sign32: the face draws no usable display phrase")
        return
    # The diamond: the longest line is the girdle, the shorter ones sit above
    # and below it — order of appearance survives, the widest line moves centre
    # (a name line wins a tie). But the girdle has to DOMINATE the sheet: a
    # thirty-character tagline filled to its measure is a label, not a sign, so
    # any line that cannot reach a fair height is demoted to the small lines
    # under the swash instead of shrinking the whole block.
    W = sh.w - 2 * sh.m
    demoted = []
    while len(parts) > 1:
        i = max(range(len(parts)), key=lambda j: len(parts[j]))
        if fit_measure(T, parts[i], W * 0.82, 620 * sh.scale) >= sh.h * 0.095:
            break
        demoted.insert(0, parts.pop(i))
    if len(parts) >= 3:
        i = max(range(3), key=lambda j: len(parts[j]))
        rest = [p for j, p in enumerate(parts) if j != i]
        parts = [rest[0], parts[i], rest[1]]
    elif len(parts) == 2:
        g = 0 if len(parts[0]) >= len(parts[1]) else 1
        parts = [parts[1 - g], parts[g]]

    # The address: the copy's own location lines first (they are what a sign
    # puts at the bottom), the block's demoted lines after them, and whatever
    # the name stack never spent last. In every case the address is lettered
    # IN the display face, so it must be able to stand at a readable size —
    # lines that cannot are dropped, not shrunk to a whisper.
    used = {p.lower() for p in parts}
    addrs = []
    for k in ("sub", "over"):
        s = " ".join(tc(_support_copy(ctx, (k,), "")).split())
        if s and s.lower() not in used and s not in addrs:
            addrs.append(s)
    for s in demoted:
        if s.lower() not in used and s not in addrs:
            addrs.append(s)
    for k in ("word", "line"):
        s = " ".join(tc(_support_copy(ctx, (k,), "")).split())
        if s and s.lower() not in used and s not in addrs:
            addrs.append(s)
    addrs = addrs[:2] or [EDGE(ctx)]

    fracs = {3: (0.62, 0.94, 0.66), 2: (0.78, 0.94), 1: (0.92,)}[len(parts)]
    sizes = [fit_measure(T, ln, W * f, 760 * sh.scale)
             for ln, f in zip(parts, fracs)]
    if min(sizes) <= 0:
        sh.problems.append("sign32: no line of the display phrase fits the measure")
        return
    # The steps: the girdle rules, the top line never out-towers it, the closing
    # line is a third smaller — the reference's `since 1997` sits under, not beside.
    if len(sizes) == 3:
        sizes = [min(sizes[0], sizes[1]), sizes[1], min(sizes[2], sizes[1] * 0.72)]
        if sizes[2] < 30 * sh.scale:
            parts, sizes = parts[:2], sizes[:2]
            sizes = [min(sizes[0], sizes[1] * 0.92), sizes[1]]
    elif len(sizes) == 2:
        sizes = [min(sizes[0], sizes[1] * 0.92), sizes[1]]
        if sizes[0] < 28 * sh.scale:
            parts, sizes = parts[1:], sizes[1:]
    if sizes[-1 if len(sizes) == 1 else 1] < 30 * sh.scale:
        sh.problems.append("sign32: the display phrase is too long to sign")
        return
    hs = [T.path(ln, s)[0].getBounds().height() for ln, s in zip(parts, sizes)]
    mid = sizes[1] if len(sizes) > 1 else sizes[0]

    # The two small lines, grown to their own measures and capped just under
    # the girdle — the address is read, not shouted, but on a painted board it
    # is still lettered big enough to be part of the sign, not a footnote. The
    # short one goes on top, the longer one closes the sheet, as the reference's
    # address does.
    addrs.sort(key=len)
    af = (0.58, 0.78)[:len(addrs)]
    asz = [min(fit_measure(T, a, W * f, 300 * sh.scale), mid * 0.70)
           for a, f in zip(addrs, af)]
    keep = [(a, s) for a, s in zip(addrs, asz) if s >= 24 * sh.scale]
    addrs, asz = [x[0] for x in keep], [x[1] for x in keep]
    if not addrs:
        # A very wide face shrinks a long line below the floor; then the sheet
        # still needs a small close, so fall back to the edge count, which is
        # short and always has a legible size.
        addrs = [" ".join(tc(clean(ctx, EDGE(ctx))).split())]
        af = (0.58,)
        asz = [min(fit_measure(T, addrs[0], W * af[0], 300 * sh.scale), mid * 0.70)]
    ahs = [T.path(a, s)[0].getBounds().height() for a, s in zip(addrs, asz)]

    # The stack, measured before it is placed so the whole sign sits centred.
    # Every gap is knit: the swash belongs to the block it divides, the two
    # address lines are one unit, and the ground the lettering cannot take
    # goes to the margins — one even band of air above and below the sign,
    # never a hole in the middle of it.
    gapb = int(round(sh.h * 0.018))
    gapa = int(round(sh.h * 0.013))
    g1 = int(round(sh.h * 0.040))
    g2 = int(round(sh.h * 0.044))
    sw_t, sw_l = sh.h * 0.036, sh.w * 0.16
    sw_h = sw_t                                  # the lens spans exactly one `thick`
    total = (sum(hs) + gapb * (len(hs) - 1) + g1 + sw_h + g2
             + sum(ahs) + gapa * max(len(ahs) - 1, 0))
    room = sh.h - 2 * int(round(sh.m * 0.82))
    if total > room:
        # One shrink for the whole sign — every line keeps its step, the sheet
        # keeps its air. A long name comes down; it never re-wraps.
        k = room / total
        sizes = [s * k for s in sizes]
        asz = [s * k for s in asz]
        hs = [h * k for h in hs]
        ahs = [h * k for h in ahs]
        sw_t *= k
        sw_l *= k
        sw_h = sw_t
        total *= k
    elif total < room:
        # The board is bigger than the lettering: grow the whole sign toward
        # it, capped so the girdle still fits inside the sheet (the measure is
        # the limit, never the height). Whatever the letters cannot take stays
        # in the margins, where air belongs; the gaps do not stretch.
        k = min(room / total, 1.045)
        sizes = [s * k for s in sizes]
        asz = [s * k for s in asz]
        hs = [h * k for h in hs]
        ahs = [h * k for h in ahs]
        sw_t *= k
        sw_l *= k
        sw_h = sw_t
        total *= k
    y = (sh.h - total) / 2.0
    for i, (ln, s, h) in enumerate(zip(parts, sizes, hs)):
        sh.text(f"sg{i}", T, ln, Box(sh.m, y, W, h + 2),
                hi=s, lo=s, max_lines=1, align="center", valign="top",
                min_read=28 * sh.scale, min_contrast=4.0, color=ink)
        y += h + gapb
    y += g1 - gapb
    # the lens's ink runs from cy-(bow+1)*t/2 to cy+(1-bow)*t/2; land its top on y
    brush_swash(sh, "swash", sh.w / 2.0, y + 0.81 * sw_t, sw_l, sw_t, ink, 0.98)
    y += sw_h + g2 - gapa
    for i, (a, s, h) in enumerate(zip(addrs, asz, ahs)):
        sh.text(f"ad{i}", T, a, Box(sh.m, y, W, h + 2),
                hi=s, lo=s, max_lines=1, align="center", valign="top",
                min_read=22 * sh.scale, min_contrast=4.0, color=ink)
        y += h + gapa

def _ghost_flat(sh, block, cx, top, k, g_top, g_bot, ink, name, alpha=0.17):
    """Paint a wordmark_block ghost as a FLAT tone instead of an alpha blend.

    The ghost is the largest ink field on the sheet. Blended at low alpha it
    re-paints the ground's tooth under every one of those strokes — a big
    contiguous field of noise — and PNG charges for noise. A gradient across
    the fill costs a new number per row, so the tone is ONE flat colour: the
    ground's mid value pulled toward the ink far enough to read as a deliberate
    echo, quiet enough to stay under the real lettering. The byte bill this
    sheet really carries is the ghost's edge perimeter — brush outlines are
    long — which is why the ghost's scale, not its alpha, is what the 500 KB
    cap decides. Only `echo32` calls this; the marks land where `paint_block`
    would have put them (collide=False, bleed=True).
    """
    mid = tuple((g_top[i] + g_bot[i]) // 2 for i in range(3))
    q = paint(C(mix(mid, ink, alpha), 1.0))
    sh.cv.save()
    sh.cv.translate(cx, top)
    if k != 1.0:
        sh.cv.scale(k, k)
    for p, b, y in block["items"]:
        sh.cv.save()
        sh.cv.translate(-(b.left() + b.right()) / 2.0, y - b.top())
        sh.cv.drawPath(p, q)
        sh.cv.restore()
    sh.cv.restore()
    for i, (_p, b, y) in enumerate(block["items"]):
        sh.mark(f"{name}{i}", Box(cx - k * b.width() / 2.0, top + k * y,
                                  k * b.width(), k * b.height()),
                collide=False, bleed=True)

@support("echo32", "the double print: a specimen phrase set twice from one typesetting — the whole lockup grown past the sheet's edges as a ghost of itself, the real lettering centred full-ink on top, an arched eyebrow dotted either side and two small lettered lines below")
def t_echo32(sh, ctx):
    """Rebuilt from T24954_00.

    The wordmark IS the background: the same two-line lockup is drawn twice at
    radically different scales — once enormous, faint and bleeding off every
    edge as a texture that fills the whole sheet, and once at its true size
    and full ink strength, centred on top of it. One `wordmark_block` feeds
    both, so the ghost can never say a different word than the lettering.
    Above the real lockup a short eyebrow rides a gentle upward arch with a
    dot either side; below it two small letter-spaced caps lines give the
    category and the copyright. The engineering the sheet leans on: the echo
    is ink under the ink, so the ground under the real lockup is measured with
    `sh._behind` AFTER the ghost is painted and the ink resolved with
    `readable` before a single stroke of the lettering goes down — the echo
    must never raise the floor the wordmark has to clear, and the wordmark
    must never be dulled by the echo behind it.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = spec_bg(sh, ctx, pool=0.05)
    ink, mute, _ = field(P)
    wordmark = shout(ctx, _support_copy(ctx, ("word", "line"),
                                        "Type In Motion")).strip()
    block = wordmark_block(T, wordmark.split(), 0.92 * sh.w, 900 * sh.scale)
    if not block or min(block["sizes"]) < 44 * sh.scale:
        sh.problems.append("echo32: the face draws no wordmark big enough to echo")
        return

    # The arch plan (crest32's lesson): a FLOWING hand turned onto a circle
    # collides at the ends of the sweep, so the arch is set in the upright
    # companion face and the phrase is caps — only the word carries the hand.
    A = L if ctx["family"] in FLOWING else T
    _t = _support_copy(ctx, ("over",), "Just Set Type")
    if A is T:
        # Only text set in the DISPLAY face needs the coverage filter; the
        # companion sans draws everything the brief carries.
        _t = clean(ctx, _t)
    top_txt = tc(" ".join(_t.split()) or "New Release")
    th = 0.62                                   # radians: a gentle rise, not a rainbow
    kk = th / (2 * math.sin(th / 2))

    def plan(text, c):
        m100 = A.measure(text, 100.0)
        if m100 <= 0:
            return None
        den = m100 + 16.0 * max(len(text) - 1, 0)     # 0.16*size track, at size 100
        s = min(100.0 * c * kk / den, 112 * sh.scale)
        r = c / (2 * math.sin(th / 2))
        track = 0.16 * s
        f = A.font(s)
        runs = A.runs(text, s)
        bs, steps = [], 0.0
        for gid, adv, _xo, _yo in runs:
            b = f.getPath(gid).getBounds()
            steps += max(adv, 0.0) if b.isEmpty() else max(adv, b.width())
            if not b.isEmpty():
                bs.append(b)
        if not bs or s < 22 * sh.scale:
            return None
        ta = min(th, (steps + track * max(len(runs) - 1, 0)) / r)
        cap = min(b.top() for b in bs)
        desc = max(b.bottom() for b in bs)
        sag = r * (1 - math.cos(ta / 2))
        wmax = max(b.width() for b in bs)
        ch, sn = math.cos(ta / 2), math.sin(ta / 2)
        rise = min(cap, -sag + cap * ch - (wmax / 2) * sn)
        fall = max(desc, sag + desc * ch + (wmax / 2) * sn)
        return dict(r=r, s=s, track=track, ta=ta, rise=rise, fall=fall,
                    ext=fall - rise)

    pu = plan(top_txt, 0.52 * sh.w)
    if not pu:
        sh.problems.append("echo32: the eyebrow phrase will not fit its arch")
        return

    # The column: arch, lettering, two small lines — centred as one stack.
    # The block is typeset near the full measure so the display lettering
    # dominates the sheet; if the whole column still stands taller than the
    # sheet has room for, one factor k brings the arch and the block down
    # together. The centring is on the column's own ink, so the stack lands
    # dead middle whatever the face's proportions.
    gap1, gap2 = 0.040 * sh.h, 0.042 * sh.h
    foot_h = 2 * 38 * sh.scale + 14 * sh.vscale
    room = 0.88 * sh.h - gap1 - gap2 - foot_h
    k_r = min(1.0, room / (pu["ext"] + block["uh"])) if room > 0 else 0.0
    if k_r <= 0:
        sh.problems.append("echo32: the lockup cannot be stood up on the sheet")
        return
    if k_r < 1.0:
        pu = plan(top_txt, 0.52 * sh.w * k_r) or pu
    total = pu["ext"] + gap1 + block["uh"] * k_r + gap2 + foot_h
    y_top = (sh.h - total) / 2.0
    yb = y_top - pu["rise"]                     # arch baseline at its apex
    cy = yb + pu["r"]
    block_top = yb + pu["fall"] + gap1

    # The ghost: the same block, grown until it reads as a poster-size echo
    # bleeding off the sheet's sides, painted one step off the ground so it is
    # a deliberate presence, not a stain. Its scale is clamped: big enough to
    # bleed, never so big that the sheet keeps only an unrecognisable fragment
    # of one letter — the echo has to still say the word. Painted FLAT (see
    # `_ghost_flat`); the ghost's edge perimeter is what the 500 KB cap buys
    # on the brush faces, so this scale sits just under the clamp.
    k_e = min(max(1.72 * sh.w / max(1.0, k_r * block["uw"]),
                  1.40 * sh.h / max(1.0, k_r * block["uh"])), 3.6)
    echo_top = block_top + block["uh"] * k_r / 2.0 - k_e * block["uh"] / 2.0
    _ghost_flat(sh, block, sh.w / 2.0, echo_top, k_e,
                P["deep1"] if dark else P["paper1"],
                P["deep2"] if dark else P["paper2"], ink, "echo", alpha=0.17)

    # The lettering sits on ink now, not on the ground: measure the REAL
    # lockup's box after the ghost went down and resolve the ink against it,
    # so the contrast guard has nothing left to lift.
    lbox = Box(sh.w / 2.0 - k_r * block["uw"] / 2.0, block_top,
               k_r * block["uw"], k_r * block["uh"])
    gnd = sh._behind(lbox) or lum(P["deep1"] if dark else P["paper1"])
    pop = readable(gnd, ink, 4.5)
    paint_block(sh, block, sh.w / 2.0, block_top, k_r, paint(C(pop, 1.0)), "mark")
    ab = arc_text(sh, A, top_txt, sh.w / 2.0, cy, pu["r"], pu["s"], pu["ta"],
                  up=True, color=pop, track=pu["track"], name="arch")
    if ab:
        dr = 6.5 * sh.scale
        for sgn in (-1, 1):
            x = sh.w / 2.0 + sgn * (ab.w / 2.0 + 30 * sh.scale)
            y = ab.y + ab.h * 0.42
            sh.cv.drawCircle(x, y, dr, paint(C(pop, 0.95)))
            sh.mark(f"dot{'lr'[sgn > 0]}", Box(x - dr, y - dr, 2 * dr, 2 * dr))

    # The two small lines: category and copyright, tracked caps in the
    # companion face, quieter than the wordmark but never below the floor.
    # They are lettered, not stamped — the companion sans draws everything the
    # brief carries, so the copy is not filtered through the display face.
    foot1 = tc(_support_copy(ctx, ("sub",), "Display Study"))
    foot2 = "Type Specimen"
    fy = block_top + block["uh"] * k_r + gap2
    fbox = Box(sh.w * 0.14, fy, sh.w * 0.72, 2 * 38 * sh.scale + 14 * sh.vscale)
    gnd_f = sh._behind(fbox) or gnd
    # Each line is resolved against the strip it will actually be measured on,
    # not the pair's combined box: a ghost edge crossing one footer line and not
    # the other is the difference between a quiet grey and an auto-lift.
    b0 = Box(fbox.x, fy, fbox.w, 38 * sh.scale)
    fink = readable(sh._behind(b0) or gnd_f, mute, 5.0)
    sh.text("ft0", L, foot1, b0,
            hi=34 * sh.scale, lo=18 * sh.scale, color=fink, track=0.22,
            align="center", valign="top", min_read=18 * sh.scale)
    s0 = _slot(sh, "ft0")
    b1 = Box(fbox.x, (s0.ink.b if s0 else fy + 38 * sh.scale) + 14 * sh.vscale,
             fbox.w, 34 * sh.scale)
    sh.text("ft1", L, foot2, b1,
            hi=31 * sh.scale, lo=16 * sh.scale,
            color=readable(sh._behind(b1) or gnd_f, mute, 5.0), track=0.22,
            align="center", valign="top", min_read=16 * sh.scale)








def _paths_touch(a, b):
    """True when two outlines share real ink (not just a bounding box).

    The rising lockup tucks its second line up into the descender zone of the
    first; how far it may go is a fact about these two words in this one face,
    not a fraction anyone can guess — a script's tails are thin and the lines
    interleave, a blackletter's legs are slabs. `skia.Path` has no boolean op in
    this build, so the test runs through `skia.Region`, which rasterises each
    path once at device scale and answers the intersection exactly.
    """
    ba, bb = a.getBounds(), b.getBounds()
    if ba.isEmpty() or bb.isEmpty() or not ba.intersects(bb):
        return False
    x0 = math.floor(min(ba.left(), bb.left()))
    y0 = math.floor(min(ba.top(), bb.top()))
    x1 = math.ceil(max(ba.right(), bb.right()))
    y1 = math.ceil(max(ba.bottom(), bb.bottom()))
    clip = skia.Region()
    clip.setRect(skia.IRect(0, 0, x1 - x0, y1 - y0))
    ra, rb = skia.Region(), skia.Region()
    pa, pb = skia.Path(a), skia.Path(b)
    pa.offset(-x0, -y0)
    pb.offset(-x0, -y0)
    if not ra.setPath(pa, clip) or not rb.setPath(pb, clip):
        return False
    return ra.intersects(rb)
def _phrase(ctx, pool):
    """Display copy for the wash/cast panels — never the font's own name.

    The owner's note on the catalogue was that a panel repeating the name of
    the font it sits under says the same word twice: the listing already
    prints that name above the sheet. So these two panels set a phrase — the
    brief's `word`/`line` first, then the panel's own pool rotated by the
    name. The difference from `panel_text` is the last resort: where that
    helper escapes to the font's name when no candidate is fully drawable, a
    name card is exactly what these two panels must never be, so this one
    takes the pool candidate the face can spell the *most* of instead, and a
    bitten phrase still beats a repeated name here because the briefs now
    author a word for every face and this path is a safety net, not a route.
    """
    got = " ".join(panel_text(ctx, pool).split())
    if got and got.lower() != " ".join(ctx["name"].split()).lower():
        return got
    rot = int(hashlib.sha256(ctx["name"].encode()).hexdigest(), 16)
    ordered = list(pool[rot % len(pool):]) + list(pool[:rot % len(pool)])
    best, keep = "", -1
    for cand in ordered:
        cut = " ".join(clean(ctx, cand).split())
        score = sum(len(w) for w in cut.split())
        if score > keep:
            best, keep = cut, score
    return best

@support("wash32", "the watercolour card: a single soft painted band laid across the paper with a phrase written huge straight through it — a small lead-in above, a quiet descriptor below, and nothing else but the wash")
def t_wash32(sh, ctx):
    """Rebuilt from T9150_00 (Aneisha, a modern handwritten script ad).

    The reference is one gesture on warm paper: a blush watercolour stripe
    painted across the middle of the sheet, a phrase written through it huge,
    a small lowercase lead-in above and a lowercase descriptor below. The wash
    is the whole device and the thin hand is the whole risk, so the ground is
    forced to the light "paper" pole of whatever world rolls (a dark field
    would swallow a hairline script), the band is kept light enough that the
    dark ink always clears it, and the phrase — never the font's own name,
    which the listing already prints — is grown to the measure as the one
    dominant block on the sheet. When the phrase breaks into two lines the
    second climbs under the first's descenders the way `cast32` tucks its
    rising pair: how far is a fact about these two words in this one face,
    measured by real ink (`_paths_touch`) rather than guessed, because a
    script's thin tails let the lines interleave while a block face's slabs
    stop the climb at once. The small type is held to the same bar as the
    big: its ink is resolved against the ground actually painted under it at
    a small-type floor, so it reads at thumbnail instead of drifting gray.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    inv = P["mode"] == "dark"                    # paint on paper, always
    spec_bg(sh, ctx, pool=0.08, invert=inv)
    ink, mute, _ = field(P, invert=inv)
    phrase = shout(ctx, _phrase(
        ctx, ("morning light", "still water", "slow tide", "open sky"))).strip()
    words = [w for w in phrase.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.9):
        sh.problems.append("wash32: the face draws no usable word of this phrase")
        return
    # lead-in — small upright sans, lowercase, tracked, centred at the top
    over = lead_in(ctx, ("just painted", "softly set", "fresh off the brush",
                         "laid by hand", "new this season")).lower()
    ly = int(round(0.06 * sh.h))
    lh = int(round(52 * sh.vscale))
    gnd_cap = sh._behind(Box(sh.m, ly, sh.w - 2 * sh.m, lh)) or lum(P["paper1"])
    cap = readable(gnd_cap, mute, 6.5)           # small type still has to read
    sh.text("lead", L, over, Box(sh.m, ly, sh.w - 2 * sh.m, lh),
            hi=36 * sh.scale, lo=18 * sh.scale, max_lines=1, align="center",
            valign="top", track=0.14, min_read=16 * sh.scale, color=cap,
            min_contrast=4.5)
    lead = _slot(sh, "lead")
    top = (lead.ink.b if lead else ly + lh) + int(round(0.025 * sh.h))
    # descriptor — small upright sans, lowercase, centred at the foot
    sub = clean(ctx, ctx["copy"].get("sub") or "").strip()
    if not sub:
        sub = {"script": "modern handwritten typeface", "brush": "modern brush script",
               "blackletter": "a bold blackletter", "serif": "a display serif",
               }.get(ctx["family"], "a display typeface")
    sub = sub.lower()
    dy = int(round(0.905 * sh.h))
    # the phrase block — grown to the measure, two lines tucking if it must
    side = int(round(44 * sh.scale))
    stage = Box(sh.m + side, top, sh.w - 2 * (sh.m + side),
                (dy - int(round(0.045 * sh.h))) - top)
    lines = pack_lines(words, min(2, len(words)))
    hi = 820 * sh.scale
    sizes = [fit_measure(T, ln, stage.w, hi) for ln in lines]
    paths = [T.path(ln, s)[0] for ln, s in zip(lines, sizes)]
    boxes = [p.getBounds() for p in paths]
    lead_px = int(round(0.025 * sh.h))
    total = sum(b.height() for b in boxes) + lead_px * (len(lines) - 1)
    if total > stage.h and total > 0:
        k = stage.h / total
        sizes = [s * k for s in sizes]
        paths = [T.path(ln, s)[0] for ln, s in zip(lines, sizes)]
        boxes = [p.getBounds() for p in paths]
        total = sum(b.height() for b in boxes) + lead_px * (len(lines) - 1)
    # The tuck is walked at the FINAL sizes, so the ink that was proven clear
    # of ink is the ink that ships: how far line two may climb under line
    # one's descenders is measured by real paths touching, not by a fraction
    # anyone can guess.
    tuck = 0.0
    if len(lines) > 1:
        b0, b1 = boxes[0], boxes[1]
        for ov in (0.54, 0.44, 0.34, 0.24, 0.14, 0.0):
            q = skia.Path(paths[1])
            q.offset((b0.x() + b0.width() / 2) - (b1.x() + b1.width() / 2),
                     b0.bottom() - ov * min(b0.height(), b1.height())
                     + lead_px - b1.y())
            if not _paths_touch(paths[0], q):
                tuck = ov
                break
        total -= tuck * min(boxes[0].height(), boxes[1].height())
    by = stage.y + (stage.h - total) / 2.0
    # the wash hugs the block: a light painted stripe, low-res + stretched
    base = mix(P["accent"], P["paper1"], 0.60)
    deep = mix(P["accent"], P["paper1"], 0.36)
    light = mix(P["accent"], P["paper1"], 0.85)
    # The band is a stripe, not a field: it hugs the middle of the block and
    # deliberately stops short of its full height, so the ascenders and the
    # descenders walk out of it — which is the reference's whole gesture.
    hh = int(round(min(total * 0.34, 0.20 * sh.h)))
    hw = int(sh.w * 0.44)
    wash_band(sh, sh.w * 0.5, by + total / 2.0, hw, hh, base, deep, light)
    # name ink resolved against the wash now under it, so the guard never lifts it
    gnd = sh._behind(Box(sh.w * 0.5 - hw, by + total / 2.0 - hh,
                         2 * hw, 2 * hh)) or lum(P["paper1"])
    pop = readable(gnd, ink, 4.5)
    y = by
    for i, (ln, s, b) in enumerate(zip(lines, sizes, boxes)):
        sh.text(f"nm{i}", T, ln, Box(stage.x, y - 2, stage.w, b.height() + 4),
                hi=s, lo=s, max_lines=1, align="center", valign="top",
                min_read=52 * sh.scale, min_contrast=4.5, color=pop)
        sl = _slot(sh, f"nm{i}")
        if sl is not None:
            sl.collide = False       # the lines ride through each other's air
        y += b.height() - (tuck * min(b.height(),
                                      boxes[i + 1].height()) if tuck and i + 1 < len(boxes)
                            else 0.0) + lead_px
    gnd_foot = sh._behind(Box(sh.m, dy, sh.w - 2 * sh.m, lh)) or lum(P["paper1"])
    sh.text("desc", L, sub, Box(sh.m, dy, sh.w - 2 * sh.m, lh),
            hi=36 * sh.scale, lo=18 * sh.scale, max_lines=1, align="center",
            valign="top", track=0.14, min_read=16 * sh.scale,
            color=readable(gnd_foot, mute, 6.5), min_contrast=4.5)

def t_cast32(sh, ctx):
    """Rebuilt from T24954_06 (Private Label).

    The reference is a logotype, not a typeset block: "Private" and "Label"
    rise to the right on parallel baselines, the short line stepped in and
    tucked up under the long one's descender, one saturated ink with a hard
    flat grey shadow cast to the lower left, and the final letter's tail
    swept back as a tapered underline beneath the whole second line — and
    nothing else on the sheet. `sticker32` took the die-cut half of this
    picture (upright rows grown to the measure, shadow to the other corner);
    this body takes the rising half. The lockup is built in its own frame at
    ONE point size — line one's baseline at the origin, line two stepped in
    by a fraction of line one's ink and tucked up by a measured fraction of
    the two lines' real descender/ascender depths, the closing flourish drawn
    as a vector lens because no face is owed a swash glyph — then rotated
    whole onto a rising slant and struck twice, shadow first, ink over it.
    The lean is honest to the face: a flowing hand climbs the full nine
    degrees, a poster-fat display face a cautious five and a half.
    """
    P, T = ctx["pal"], ctx["display"]
    inv = P["mode"] == "dark"                 # the lockup is struck on paper
    spec_bg(sh, ctx, pool=0.0, invert=inv)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(P["paper1"])
    # The loud ink is resolved against the ground actually painted under the
    # whole sheet — and at a display floor, not a body-text one: a rose that
    # "clears" 4:1 on pink paper is exactly the lettering that dies at
    # thumbnail size. Pre-resolving here is also why the guard never has to
    # lift this sheet.
    pop = readable(gnd, mix(P["accent"], P["deep1"], 0.20), 6.0)
    shadow = mix(P["paper2"], P["deep1"], 0.18)
    phrase = shout(ctx, _phrase(
        ctx, ("hold fast", "built to last", "day by day", "rise up"))).strip()
    words = [w for w in phrase.split() if w]
    if not words or not T.fit(words[0], 100.0, sh.w * 0.9):
        sh.problems.append("cast32: the face draws no usable word of this phrase")
        return
    lines = pack_lines(words, 2)
    if len(words) > 2:
        # The lockup wants its two lines balanced in ink, not in greed: take the
        # split whose halves are closest in length, preferring the longer line
        # on top — the reference's `Private` over its `Label`.
        best = min(range(1, len(words)),
                   key=lambda i: (abs(sum(map(len, words[:i])) + i - 1 -
                                    (sum(map(len, words[i:])) + len(words) - i - 1)),
                                  -i))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    if len(lines) > 1:
        # A line of one stray word is not the second voice of a lockup, it is
        # an orphan: "Build" over "It" left a stub hanging in the sheet's
        # corner and a dead half beside it. When the short line carries less
        # than half the longer one's letters, the phrase sets as ONE rising
        # line with the swash under it — which is the reference's other
        # shape, the single-word logotype, and it fills the measure instead
        # of drifting into it.
        short, long_ = sorted(lines, key=len)
        if len(short) < 0.5 * len(long_):
            lines = [" ".join(words)]
    fam, stem = ctx["family"], ctx["facts"].get("stem", 0.0) or 0.0
    tilt = 9.0 if fam in FLOWING else (5.5 if stem >= 0.16 else 7.0)
    stage = Box(sh.m * 0.5, sh.m * 0.42, sh.w - sh.m, sh.h - 0.84 * sh.m)

    fracs = (0.94, 0.80) if len(lines) > 1 else (0.90,)
    sizes = [fit_measure(T, ln, stage.w * f, 900 * sh.scale)
             for ln, f in zip(lines, fracs)]
    if min(sizes) <= 0:
        sh.problems.append("cast32: no line of the phrase can be set to the measure")
        return
    s = min(sizes)

    def cast(size):
        """The shadow's throw: a real distance in the sheet, but never more
        than a hair of the letter height — and the interline gap is held to at
        least this, so line one's cast never lands on line two's ink."""
        return min(22.0 * sh.scale, max(8.0, 0.075 * size))

    def plan(size):
        """The lockup in its own frame; paths come back pre-offset into it."""
        p1, _ = T.path(lines[0], size)
        b1 = p1.getBounds()
        desc1 = max(0.0, b1.bottom())
        boxes = [(b1.left(), b1.top(), b1.width(), b1.height())]
        p2, b2 = None, b1
        if len(lines) > 1:
            p2, _ = T.path(lines[1], size)
            asc2 = max(0.0, -p2.getBounds().top())
            x2 = b1.width() * 0.14                # the step-in
            gap = max(size * 0.05, cast(size))    # room for the throw
            # The tuck: walk line two up toward line one's baseline and let the
            # ink itself say how far it may go — a script's thin tails let the
            # lines interleave like the reference, a blackletter's slabs stop
            # the climb the moment real ink would touch real ink.
            for tuck in (0.34, 0.22, 0.12, 0.0):
                y2 = desc1 - tuck * min(desc1, asc2) + gap + asc2
                q = skia.Path(p2)
                q.offset(x2, y2)
                if not _paths_touch(p1, q):
                    break
            p2 = q
            b2 = p2.getBounds()
            boxes.append((b2.left(), b2.top(), b2.width(), b2.height()))
        # The closing flourish: a lens swept under the last line, needle-thin
        # at both tips and lifted by its bow — the reference's underline, drawn
        # rather than trusted to a glyph the face may not ship.
        thick = max(6.0, size * 0.075)
        bow = 0.62 * thick
        half = max(b2.width() * 0.44, thick)
        scx = b2.x() + b2.width() * 0.54
        scy = b2.bottom() + size * 0.08 + (bow + thick) / 2.0
        sw = skia.Path()
        sw.moveTo(scx - half, scy)
        sw.quadTo(scx - half * 0.30, scy - bow - thick, scx + half, scy)
        sw.quadTo(scx - half * 0.30, scy - bow + thick, scx - half, scy)
        sw.close()
        boxes.append((scx - half, b2.bottom() + size * 0.08, 2 * half, thick))
        ux0 = min(bx[0] for bx in boxes)
        uy0 = min(bx[1] for bx in boxes)
        ux1 = max(bx[0] + bx[2] for bx in boxes)
        uy1 = max(bx[1] + bx[3] for bx in boxes)
        return p1, p2, sw, boxes, (ux0, uy0, ux1 - ux0, uy1 - uy0)

    def spun(ub):
        corners = [(ub[0], ub[1]), (ub[0] + ub[2], ub[1]),
                   (ub[0] + ub[2], ub[1] + ub[3]), (ub[0], ub[1] + ub[3])]
        cxl, cyl = ub[0] + ub[2] / 2, ub[1] + ub[3] / 2
        return corners, cxl, cyl, _tilt_bbox(corners, -tilt, cxl, cyl)

    p1, p2, sw, boxes, ub = plan(s)
    _c, _cx, _cy, rb = spun(ub)
    k = min(1.0, stage.w / rb[2], stage.h / rb[3]) if rb[2] and rb[3] else 0.0
    if k <= 0 or s * k < 40 * sh.scale:
        sh.problems.append("cast32: the phrase is too long to cast")
        return
    s = s * k
    p1, p2, sw, boxes, ub = plan(s)
    corners, cxl, cyl, rb = spun(ub)

    off = cast(s)
    sdx, sdy = -off * 0.62, off            # the cast: down and to the LEFT
    px = stage.x + (stage.w - rb[2]) / 2 + (cxl - rb[0]) - sdx / 2
    py = stage.y + (stage.h - rb[3]) / 2 + (cyl - rb[1]) - sdy / 2
    q_sh = paint(C(shadow, 1.0))
    q_ink = paint(C(pop, 1.0))
    for dx, dy, q in ((sdx, sdy, q_sh), (0.0, 0.0, q_ink)):
        sh.cv.save()
        sh.cv.translate(px + dx, py + dy)
        sh.cv.rotate(-tilt)
        sh.cv.translate(-cxl, -cyl)
        sh.cv.drawPath(p1, q)
        if p2 is not None:
            sh.cv.drawPath(p2, q)
        sh.cv.drawPath(sw, q)
        sh.cv.restore()
    # The checker sees the axis-aligned box each spun piece sweeps — the
    # conservative truth about where the ink lies — and the lines deliberately
    # interlock, so the marks stand registered but not colliding. They carry
    # the lockup's real point size, because a hand-struck logotype is still
    # the display lettering of its sheet and has to be weighed as one.
    ox, oy = px - cxl, py - cyl
    for i, bx in enumerate(boxes):
        r = _tilt_bbox([(bx[0], bx[1]), (bx[0] + bx[2], bx[1]),
                        (bx[0] + bx[2], bx[1] + bx[3]), (bx[0], bx[1] + bx[3])],
                       -tilt, cxl, cyl)
        sh.slots.append(Slot(f"cs{i}", Box(r[0] + ox, r[1] + oy, r[2], r[3]),
                             Box(r[0] + ox, r[1] + oy, r[2], r[3]),
                             s if i < len(lines) else 0.0, 1, False, False))
    sh.mark("cshd", Box(rb[0] + ox + sdx, rb[1] + oy + sdy, rb[2], rb[3]),
            collide=False)



def _ladder_wash(cv, box, strength=0.10, seed=7):
    """One cloudy perlin field multiplied over a box — a damp print, not a wash.

    Invented the way the texture kit invents it: generated at a small tile and
    repeated, so neighbouring pixels agree with each other and the PNG only pays
    once per tile. A full-res per-pixel noise would cost a third of a megabyte;
    this costs kilobytes and reads as paper that dried unevenly.
    """
    if box is None or box.w < 8 or box.h < 8 or strength <= 0.004:
        return
    n = 256
    sub = skia.Surface.MakeRasterN32Premul(n, n)
    if sub is None:
        return
    q = skia.Paint(AntiAlias=False)
    q.setColor4f(skia.Color4f(0.0, 0.0, 0.0, max(0.0, min(1.0, strength))))
    q.setShader(skia.PerlinNoiseShader.MakeFractalNoise(3.0 / n, 3.0 / n, 2,
                                                        seed, skia.ISize(n, n)))
    sub.getCanvas().drawRect(skia.Rect.MakeWH(n, n), q)
    img = sub.makeImageSnapshot()
    p = skia.Paint(AntiAlias=False)
    p.setBlendMode(skia.BlendMode.kMultiply)
    m = skia.Matrix()
    m.preScale(4.0, 4.0)
    m.preTranslate((seed % 977) / 977.0 * n, ((seed * 5) % 977) / 977.0 * n)
    p.setShader(img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                               skia.SamplingOptions(), m))
    cv.drawRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h), p)

def _ladder_ground(sh, ctx, dark, plan):
    """The typographic stage the ladder stands on.

    A scale specimen is drawn on a guideline sheet, so the ground says so: the
    column spine and its ruler ticks, one rule per baseline (extended exactly to
    where that rung stops, so the rules measure the widths as well as the sizes),
    an ascender line over the top rung, a damp perlin field and a thin tooth.
    Every mark is axis-aligned — a rotated mesh would cost more than the type.
    """
    P = ctx["pal"]
    cv = sh.cv
    _ink, mute, _ = field(P, invert=not dark)
    x_c, x_r = plan["x_c"], plan["x_r"]
    top, floor_y = plan["top"], plan["floor_y"]
    s = sh.scale
    g_stage = Box(x_c - int(30 * s), top, x_r - x_c + int(60 * s), floor_y - top)
    gnd = sh._behind(g_stage)
    line = readable(gnd, mute, 3.4) if gnd else mute
    deep = readable(gnd, mix(mute, P["deep2"] if dark else P["paper2"], 0.35),
                    2.6) if gnd else mute
    _ladder_wash(cv, g_stage, 0.10, seed=ctx["th"]["seed"] * 7 + 13)
    # The tooth is a graph: a specimen is measured on squared paper, and a PNG
    # pays almost nothing for lines that repeat along the row filter — a full
    # sheet grille at this alpha is single-digit kilobytes, where real per-pixel
    # noise costs a third of a megabyte. The grid also *is* the subject here.
    gp = skia.Path()
    step = int(34 * s)
    gy = floor_y
    while gy > top - 2 * step:
        gp.moveTo(x_c - int(24 * s), gy)
        gp.lineTo(x_r, gy)
        gy -= step
    gx = x_c
    while gx < x_r:
        gp.moveTo(gx, top - int(14 * s))
        gp.lineTo(gx, floor_y)
        gx += step
    cv.save()
    cv.clipRect(skia.Rect.MakeXYWH(g_stage.x, g_stage.y, g_stage.w, g_stage.h))
    cv.drawPath(gp, paint(C(deep, 0.55), style=skia.Paint.kStroke_Style,
                          width=1.0))
    cv.restore()
    # column spine and its ruler ticks
    rule(cv, x_c, top, x_c, floor_y, line, 1.2 * s, 0.5)
    step = int(34 * s)
    tk = skia.Path()
    y = floor_y
    while y > top:
        tk.moveTo(x_c - step, y)
        tk.lineTo(x_c, y)
        y -= step
    cv.drawPath(tk, paint(C(deep, 1.0), style=skia.Paint.kStroke_Style,
                          width=1.0 * s))
    # the top rung's ascender line, drawn through the full measure
    rule(cv, x_c - int(24 * s), plan["asc_y"], x_r, plan["asc_y"],
         deep, 1.0 * s, 0.8)
    # one baseline rule per rung, ending at a tab where the rung's ink ends
    for b, xr in zip(plan["baselines"], plan["ink_r"]):
        xe = min(x_r, xr + int(46 * s))
        rule(cv, x_c, b, xe, b, line, 1.4 * s, 1.0)
        cv.drawRect(skia.Rect.MakeXYWH(xe - 3 * s, b - 7 * s, 6 * s, 14 * s),
                    paint(C(line, 0.9)))

def t_ladder32(sh, ctx):
    """The one question a display face gets that no panel answers: at what size
    does it stop working? One phrase, six rungs, a geometric ratio, a shared
    baseline grid and a legibility floor the face itself sets.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = spec_bg(sh, ctx, pool=0.05)
    phrase = shout(ctx, clean(ctx, panel_text(ctx))).strip()
    phrase = " ".join(phrase.split())
    if not phrase or T.measure(phrase, 100.0) <= 0:
        sh.problems.append("ladder32: the face draws no word of this phrase")
        return
    over = clean(ctx, ctx["copy"].get("over") or "").strip()
    top = eyebrow(sh, ctx, over or ctx["name"]) + int(round(30 * sh.vscale))
    x_c = sh.m + int(round(58 * sh.scale))
    x_r = sh.w - sh.m
    floor_y = sh.h - int(round(0.58 * sh.m))
    s = sh.scale
    # face-driven floor for the last rung, from the face's own contour density
    dens = contour_density(T, phrase if len(phrase) <= 24 else phrase[:24])
    s5 = (22 + 78 * min(dens, 1.15)) * s
    m100 = T.path(phrase, 100.0)[0].getBounds()
    a100, d100 = -m100.y(), m100.bottom()
    w100 = max(T.measure(phrase, 100.0), m100.width())
    s0 = min(fit_measure(T, phrase, (x_r - x_c) * 0.995, 640 * s),
             0.42 * (floor_y - top) * 100.0 / max(a100 + d100, 1.0))
    s5 = min(s5, 0.34 * s0)
    if s0 < 60 * s:
        sh.problems.append("ladder32: the phrase is too long to climb down")
        return
    sizes = None
    for _ in range(12):
        r = (s5 / s0) ** 0.2
        sizes = [s0 * r ** i for i in range(6)]
        a = [a100 * z / 100.0 for z in sizes]
        d = [d100 * z / 100.0 for z in sizes]
        pitch_min = [d[i] + a[i + 1] + max(7 * s, 0.10 * sizes[i + 1])
                     for i in range(5)]
        avail = floor_y - top - a[0] - d[5]
        if sum(pitch_min) <= avail:
            break
        s0 *= 0.88
        s5 = min(s5, 0.34 * s0)
    else:
        sh.problems.append("ladder32: the ladder cannot stand inside the sheet")
        return
    extra = avail - sum(pitch_min)
    air = extra / sum(sizes[:5])
    pitch = [pitch_min[i] + air * sizes[i] for i in range(5)]
    baselines, yb = [], top + a[0]
    for pv in pitch:
        baselines.append(yb)
        yb += pv
    baselines.append(yb)
    ink_r = [x_c + w100 * z / 100.0 for z in sizes]

    _ladder_ground(sh, ctx, dark, dict(x_c=x_c, x_r=x_r, top=top - 6,
                                       floor_y=floor_y, baselines=baselines,
                                       ink_r=ink_r, asc_y=baselines[0] - a[0]))

    # the six rungs, pinned to exact sizes, each lifted against its own ground
    for i, (z, b) in enumerate(zip(sizes, baselines)):
        ah = a100 * z / 100.0
        dh = d100 * z / 100.0
        bw = ink_r[i] - x_c + 6
        rb = Box(x_c, b - ah, bw, ah + dh + 4)
        gnd = sh._behind(Box(x_c, b - ah, min(bw, sh.w - x_c), ah + dh + 4))
        tn = tone(P, i)
        if gnd is not None:
            tn = _lift(tn, gnd, 4.5)
        sh.text(f"rung{i}", T, phrase, rb, hi=z, lo=z, max_lines=1,
                align="left", valign="top", min_read=z, min_contrast=4.5,
                bleed=ink_r[i] > sh.w - 2, **tn)
        # the rail: this rung's size, in points of the sheet
        nb = Box(sh.m - int(14 * s), b - 20 * s,
                 x_c - int(16 * s) - (sh.m - int(14 * s)), 30 * s)
        ng = sh._behind(nb)
        sh.text(f"px{i}", L, f"{int(round(z))}", nb, hi=22 * s, lo=22 * s,
                align="right", valign="middle", min_read=14 * s,
                min_contrast=3.2,
                color=readable(ng, mix(P["glow"] if dark else P["ink"],
                                       P["deep2"] if dark else P["paper2"],
                                       0.30), 3.2) if ng else P["ink"])
    # --- the coda: the phrase set as a real paragraph at the last rung's size,
    # tucked into the triangle of quiet the ladder leaves at the lower right.
    # This is the panel's proof line — the smallest rung is not a stunt, the
    # face carries text with it.
    x_p = max(ink_r[3] + int(64 * s), x_c + int((x_r - x_c) * 0.52))
    ptop = baselines[3] - a[3] + int(10 * s)
    pw = x_r - x_p
    step5 = s5 * 0.86
    cand = 3
    txt = " ".join([phrase] * cand)
    lines = T.wrap(txt, pw, s5)
    while len(lines) < 2 and cand < 12:
        cand += 1
        txt = " ".join([phrase] * cand)
        lines = T.wrap(txt, pw, s5)
    while cand > 2 and (len(lines) > 4 or
                        (len(lines) - 1) * step5 + (a100 + d100) * s5 / 100.0
                        > floor_y - ptop):
        cand -= 1
        txt = " ".join([phrase] * cand)
        lines = T.wrap(txt, pw, s5)
    if cand >= 2 and len(lines) <= 4:
        ph = (len(lines) - 1) * step5 + (a100 + d100) * s5 / 100.0 + 6
        pb = Box(x_p, ptop, pw, ph)
        pg = sh._behind(pb)
        sh.text("body", T, txt, pb, hi=s5, lo=s5,
                max_lines=4, align="left", valign="top", leading=0.86,
                min_contrast=4.5,
                color=readable(pg, mix(P["glow"] if dark else P["ink"],
                                       P["deep2"] if dark else P["paper2"],
                                       0.16), 4.5) if pg else P["ink"])

def _contour_char(ctx, pools=("terrain", "ridgeline", "summit", "elevation",
                              "highland", "baseline")):
    """The one letter the survey sheet cuts its contours around.

    Authored copy first (the brief's `word`), then the font's own initial —
    which is the letter a buyer of THIS font is most likely to draw with — and
    only then a letter rolled off the panel's own vocabulary, so five faces do
    not all survey the same shape. A face that does not carry the capital gets
    the lowercase that does; a face with neither is reported, not faked.
    """
    for cand in (clean(ctx, ctx["copy"].get("word") or "").strip(),
                 shout(ctx, clean(ctx, ctx["name"])).strip(),
                 panel_text(ctx, pools)):
        for c in cand:
            if c.isalpha() and usable(ctx, c):
                return c.upper() if usable(ctx, c.upper()) else c
    return ""

def _contour_field(sh, P, dark, path, hh, stem, limit=None):
    """One glyph expanded into concentric bands of elevation — the whole sheet.

    skia-python 144 has no path booleans, so a true offset cannot be computed
    on the outline. But a stroke of width 2d swept along the path IS the
    morphological dilation of that path by a disc of radius d, and the stroke
    union in the concavities is done exactly, by the rasteriser, at full
    resolution. Draw the dilations widest-first in a stepped tone and clip away
    the glyph's own ink (one even-odd path: the sheet rect plus the outline),
    and what stands is a topographic map: nested contour bands rising off the
    letter, counters filling like basins, ridges merging where two arms of the
    glyph come together — every face making its own landform from its own
    shape. The bands ARE the drawing; there is no solid ink anywhere.
    Returns (spread, n, step) so the caller can register and caption it.
    """
    ink, _mute, _ = field(P)
    ground = P["deep2"] if dark else P["paper2"]
    c_near = mix(ink, ground, 0.14)          # the shoulder next to the letter
    c_far = mix(ink, ground, 0.84)           # the lowland it fades into
    # Ring pitch is a fact about the face: a fat display stem wants wide valley
    # floors or its rings swamp each other, a text serif's hairlines can carry
    # the fine survey. Measured off the face's own median stem, not guessed.
    w0 = hh * min(max(0.030 + 1.25 * stem, 0.032), 0.072)
    spread = 0.30 * sh.w
    n = max(8, min(13, int(round(spread / w0))))
    step = spread / n
    clip = skia.Path()
    clip.addRect(skia.Rect.MakeWH(sh.w, sh.h))
    clip.addPath(path, skia.Matrix())
    clip.setFillType(skia.PathFillType.kEvenOdd)
    sh.cv.save()
    if limit is not None:
        # The terrain stops at the sheet's ruled margin rather than running
        # under the caption: a survey is mounted on a page, and the page has a
        # border the drawing does not cross.
        sh.cv.clipRect(skia.Rect.MakeXYWH(0, 0, sh.w, limit))
    sh.cv.clipPath(clip)
    for i in range(n, 0, -1):
        t = (n - i + 0.5) / n
        if i % 4 == 0:                        # index contour: deepen every fourth
            t = max(0.0, t - 0.13)
        q = paint(C(mix(c_near, c_far, t ** 1.25)),
                  style=skia.Paint.kStroke_Style, width=2.0 * step * i)
        q.setStrokeJoin(skia.Paint.Join.kRound_Join)
        sh.cv.drawPath(path, q)
    # The shoreline: the glyph's own outline as a hairline of full ink, the
    # outer half of which survives the clip — the one edge that must never be
    # soft, because it is the edge that says which letter this is.
    sh.cv.drawPath(path, paint(C(ink), style=skia.Paint.kStroke_Style,
                               width=max(1.6, 2.6 * sh.scale)))
    sh.cv.restore()
    return spread, n, step

def _contour_grid(sh, P, dark):
    """The survey sheet's graticule: hairline cross-rules over the field, and
    the doubled frame tick at each margin. Quiet enough to sit under the
    lettering, present enough that the ground reads as paper that was ruled
    before it was drawn on — not a gradient somebody stopped early."""
    _ink, mute, _ = field(P)
    a = 0.10 if dark else 0.09
    step = int(round(168 * sh.scale))
    for x in range(step, sh.w, step):
        rule(sh.cv, x, 0, x, sh.h, mute, max(1.0, 1.1 * sh.scale), a)
    for y in range(step, sh.h, step):
        rule(sh.cv, 0, y, sh.w, y, mute, max(1.0, 1.1 * sh.scale), a)

@support("contour32", "the letter as terrain: one glyph surveyed as concentric contour bands — no solid ink anywhere, the shoreline struck in a hairline, counters filling like basins, the survey sheet's own graticule, interval and elevation captions")
def t_contour32(sh, ctx):
    """The shape itself as the picture: a topographic survey of one letter.

    Every other panel in the catalogue typesets the face; this one draws it.
    The outline is grown outward in stepped bands the way a survey grows a
    hillside off its shoreline, and the only solid thing on the sheet is a
    hairline. What the buyer learns is the silhouette — a blackletter's knots
    dam a different landscape than a brush script's single-stroke spine or a
    didone's hairline ridge, because the terrain is computed from that face's
    actual outline, stem thickness included.
    """
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], dev=False, pool=ctx["th"]["pool"] * 0.7,
              tooth=int(ctx["th"]["tooth"] * 0.6))
    ch = _contour_char(ctx)
    if not ch:
        sh.problems.append("contour32: the face draws no letter to survey")
        return
    size = fit_measure(T, ch, 0.52 * sh.w, 1500 * sh.scale)
    if size <= 0:
        sh.problems.append(f"contour32: {ch!r} cannot be cut at any size")
        return
    path = T.path(ch, size)[0]
    b = path.getBounds()
    tgt_h = 0.58 * sh.h
    if b.height() > tgt_h:
        size *= tgt_h / b.height()
        path = T.path(ch, size)[0]
        b = path.getBounds()
    if size < 40 * sh.scale:
        sh.problems.append(f"contour32: {ch!r} is too wide to stand at reading size")
        return
    path.offset(sh.w * 0.50 - (b.x() + b.width() / 2.0),
                sh.h * 0.485 - (b.y() + b.height() / 2.0))
    b = path.getBounds()
    stem = ctx["facts"].get("stem") or 0.05
    # The sheet is a mounted survey: the terrain runs to three edges and stops
    # at a ruled margin at the foot, so the caption sits on ground the drawing
    # never touched. Thin type over a banded mid-tone is exactly where the
    # contrast guard would otherwise bite, and a guard that has to bite here
    # would be lifting ink off a picture that was never meant to be read there.
    band = int(round(0.155 * sh.h))
    spread, n, step = _contour_field(sh, P, dark, path, b.height(), stem,
                                     limit=sh.h - band)
    _contour_grid(sh, P, dark)

    # The field is the picture, so it is registered as one bleeding shape the
    # lettering is allowed to ride over — same contract as `ghost` and `cloud`.
    fx0, fy0 = b.x() - spread, b.y() - spread
    sh.mark("field", Box(max(0.0, fx0), max(0.0, fy0),
                         min(float(sh.w), b.right() + spread) - max(0.0, fx0),
                         min(float(sh.h - band), b.bottom() + spread)
                         - max(0.0, fy0)), collide=False, bleed=True)

    ink, mute, _ = field(P)
    my = sh.h - band
    rule(sh.cv, sh.m, my, sh.w - sh.m, my, mute, max(1.4, 2.2 * sh.scale), 0.72)
    rule(sh.cv, sh.m, my, sh.m + int(round(120 * sh.scale)), my, P["accent"],
         3.4 * sh.scale, 0.95)

    cb = Box(sh.m, my + int(round(0.17 * band)), sh.w - 2 * sh.m,
             int(round(58 * sh.vscale)))
    g_bot = sh._behind(cb) or 0.5
    sh.text("cname", L, tc(f"{ch} surveyed \u2014 contour study"), cb,
            hi=36 * sh.scale, lo=18 * sh.scale,
            color=readable(g_bot, ink, 4.5), track=0.06, align="left",
            valign="top", min_read=18 * sh.scale)
    s0 = _slot(sh, "cname")
    ib = Box(sh.m, (s0.ink.b if s0 else cb.b) + int(round(11 * sh.vscale)),
             sh.w - 2 * sh.m, int(round(44 * sh.vscale)))
    g_i = sh._behind(ib) or 0.5
    sh.text("ival", L,
            tc(" ".join(f"contour interval {int(round(step))} \u00b7 "
                        f"{n} rings \u00b7 {EDGE(ctx)}".split())),
            ib, hi=26 * sh.scale, lo=14 * sh.scale,
            color=readable(g_i, mute, 4.5), track=0.20, align="left",
            valign="top", min_read=14 * sh.scale)
def _support_word(ctx, fallback):
    """Short authored copy for material studies; never leak the font name."""
    return shout(ctx, _support_copy(ctx, ("word", "line"), fallback))


def _native_glyph(sh, ctx, glyph, box, color, key="glyph", max_size=900):
    """Draw one face-driven glyph in a bounded box without raster references."""
    T = ctx["display"]
    glyph = next((c for c in glyph if usable(ctx, c)), "A")
    size = fit_measure(T, glyph, box.w * 0.88, max_size * sh.scale)
    if size <= 0:
        return None
    p, _ = T.path(glyph, size)
    b = p.getBounds()
    p.offset(box.x + (box.w - b.width()) / 2 - b.left(),
             box.y + (box.h - b.height()) / 2 - b.top())
    sh.cv.drawPath(p, paint(C(color, 1.0)))
    sh.mark(key, Box(p.getBounds().x(), p.getBounds().y(),
                     p.getBounds().width(), p.getBounds().height()),
            collide=False)
    return p


def _slot_ink(sh, box, preferred):
    """Resolve a preferred ink against the pixels already under a text slot."""
    ground = sh._behind(box)
    return readable(ground if ground is not None else 0.5, preferred, 4.5)


def t_retro32(sh, ctx):
    P = ctx["pal"]
    bg(sh, P, ctx["th"], dev=False, pool=0.08, tooth=1)
    ink = readable(lum(P["paper1"]), P["ink"], 5.0)
    warm = readable(lum(P["paper1"]), P["accent"], 3.8)
    cool = readable(lum(P["paper1"]), P["accent2"], 3.8)
    for i, col in enumerate((warm, cool, P["deep2"])):
        y = int(sh.h * (0.12 + i * 0.085))
        sh.cv.drawRect(skia.Rect.MakeXYWH(sh.m, y, sh.w - 2 * sh.m, int(sh.h * 0.055)), paint(C(col, .92)))
        sh.mark(f"band{i}", Box(sh.m, y, sh.w - 2 * sh.m, sh.h * .055), collide=False)
    cx, cy, r = int(sh.w * .77), int(sh.h * .70), int(sh.h * .20)
    sh.cv.drawCircle(cx, cy, r, paint(C(warm, .92)))
    sh.mark("sun", Box(cx-r, cy-r, 2*r, 2*r), collide=False)
    word = _support_word(ctx, "Back To Nature")
    word_box = Box(sh.m, int(sh.h * .34), int(sh.w * .66), int(sh.h * .34))
    note_box = Box(sh.m, int(sh.h * .88), int(sh.w * .78), int(sh.h * .06))
    sh.text("retro", ctx["display"], word, word_box,
            hi=360 * sh.scale, lo=40, max_lines=2,
            color=_slot_ink(sh, word_box, ink), min_read=54 * sh.scale, track=-.02)
    sh.text("retro_sub", ctx["label"], "Modern Classic / 1970s Study", note_box,
            hi=28 * sh.scale, lo=14, max_lines=1,
            color=_slot_ink(sh, note_box, ink), min_read=14 * sh.scale, track=.12)


def t_variable32(sh, ctx):
    P = ctx["pal"]
    bg(sh, P, ctx["th"], dev=False, pool=.07, tooth=1)
    ink = readable(lum(P["paper1"]), P["ink"], 5.0)
    accent = readable(lum(P["paper1"]), P["accent"], 4.2)
    for i, label in enumerate(("Thin", "Regular", "Bold")):
        y = int(sh.h * (.16 + i * .25))
        rule(sh.cv, sh.m, y - 14 * sh.scale, sh.w - sh.m, y - 14 * sh.scale, accent, 2.0 * sh.scale, .7)
        size = (76 + i * 12) * sh.scale
        text = _support_word(ctx, "Variable Type")
        word_box = Box(sh.m, y, sh.w * .92, sh.h * .21)
        axis_box = Box(sh.w * .52, y + sh.h * .21, sh.w * .43, sh.h * .04)
        sh.text(f"var{i}", ctx["display"], text, word_box,
                hi=size, lo=size, max_lines=1,
                color=_slot_ink(sh, word_box, ink), min_read=30 * sh.scale,
                track=-.025 + i * .01)
        sh.text(f"axis{i}", ctx["label"], f"Weight {i+1:02d}  /  Optical Scale", axis_box,
                hi=22 * sh.scale, lo=12, max_lines=1,
                color=_slot_ink(sh, axis_box, accent), min_read=12 * sh.scale,
                align="right", track=.10)


def t_archive32(sh, ctx):
    P = ctx["pal"]
    bg(sh, P, ctx["th"], dev=False, pool=.09, tooth=1)
    paper = readable(lum(P["deep1"]), P["paper1"], 4.5)
    red = readable(lum(P["deep1"]), P["accent"], 4.0)
    for x, y, w, h, c in ((.08,.15,.30,.30,paper), (.56,.12,.31,.40,P["deep2"]),
                          (.12,.58,.36,.24,P["paper2"]), (.62,.62,.22,.22,red)):
        xx, yy, ww, hh = int(sh.w*x), int(sh.h*y), int(sh.w*w), int(sh.h*h)
        sh.cv.drawRect(skia.Rect.MakeXYWH(xx, yy, ww, hh), paint(C(c, .92)))
        sh.mark("archive", Box(xx, yy, ww, hh), collide=False)
    word = _support_word(ctx, "Found Objects")
    word_box = Box(sh.m, int(sh.h*.39), int(sh.w*.82), int(sh.h*.24))
    note_box = Box(sh.m, int(sh.h*.90), sh.w*.72, sh.h*.05)
    sh.text("archive_word", ctx["display"], word, word_box,
            hi=250*sh.scale, lo=34, max_lines=2,
            color=_slot_ink(sh, word_box, red), min_read=42*sh.scale, track=-.02)
    sh.text("archive_note", ctx["label"], "Plate 04 / Print Room", note_box,
            hi=24*sh.scale, lo=12, max_lines=1,
            color=_slot_ink(sh, note_box, paper), min_read=12*sh.scale, track=.14)


@support("mountain32", "a T33631-inspired specimen layout using the user's exact cropped mountain artwork")
def t_mountain32(sh, ctx):
    P = ctx["pal"]
    art = dict(P, deep1=(19, 20, 21), deep2=(27, 28, 29),
               paper1=(244, 239, 224), paper2=(229, 222, 204),
               ink=(19, 20, 21), glow=(244, 239, 224),
               accent=(181, 37, 45), accent2=(181, 37, 45), mode="dark")
    bg(sh, art, ctx["th"], dev=False, pool=0.0, tooth=1800, tex=False)

    # This follows the T33631 product image's actual architecture: one cream
    # illustration panel on the left and six numbered specimen rows on black.
    panel = Box(sh.w*.052, sh.h*.08, sh.w*.30, sh.h*.81)
    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "originals" /
                  "T33631_05-illustration.jpg")
    if not asset_path.exists():
        sh.problems.append(f"mountain32: missing reference illustration {asset_path}")
        return
    illustration = skia.Image.open(str(asset_path))
    if illustration is None:
        sh.problems.append(f"mountain32: could not decode {asset_path.name}")
        return
    scale = min(panel.w / illustration.width(), panel.h / illustration.height())
    iw, ih = illustration.width()*scale, illustration.height()*scale
    dst = skia.Rect.MakeXYWH(panel.x+(panel.w-iw)/2,
                             panel.y+(panel.h-ih)/2, iw, ih)
    sh.cv.drawImageRect(illustration,
                        skia.Rect.MakeWH(illustration.width(), illustration.height()),
                        dst, skia.SamplingOptions(skia.FilterMode.kLinear,
                                                  skia.MipmapMode.kLinear))

    cream = art["glow"]
    words = ("Diabolically", "Equalizing", "Revaluation",
             "Pandemic", "Submachine", "Challenger")
    left = sh.w*.405
    right = sh.w*.956
    row_h = sh.h*.105
    step = sh.h*.145
    for i, word in enumerate(words):
        y = sh.h*(.065 + i*.145)
        num_box = Box(left, y, sh.w*.042, row_h)
        word_box = Box(sh.w*.455, y, right-sh.w*.455, row_h)
        sh.text(f"mountain_num{i}", ctx["label"], f"{i+1:02d}.", num_box,
                hi=23*sh.scale, lo=12, max_lines=1,
                color=_slot_ink(sh, num_box, cream), min_read=12*sh.scale,
                align="left", valign="middle", track=.03)
        sh.text(f"mountain_word{i}", ctx["display"], word, word_box,
                hi=124*sh.scale, lo=42*sh.scale, max_lines=1,
                color=_slot_ink(sh, word_box, cream), min_read=35*sh.scale,
                align="left", valign="middle", track=-.015)
        if i < len(words)-1:
            yy = y + step*.77
            rule(sh.cv, sh.w*.39, yy, right, yy, art["paper2"],
                 max(1.2, 1.7*sh.scale), .72)


@support("hand32", "the supplied T33144 line-art hand with theme-adapted ground and oversized three-line type")
def t_hand32(sh, ctx):
    P = ctx["pal"]
    dark = P["mode"] == "dark"
    ground = P["deep1"] if dark else P["paper1"]
    type_ink = readable(lum(ground), P["glow"] if dark else P["ink"], 4.5)
    hand_ink = readable(lum(ground), P["accent"], 4.5)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(ground, 1)))
    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T33144_thumbs-up-line-art.png")
    if not asset_path.exists():
        sh.problems.append(f"hand32: missing reference illustration {asset_path}")
        return
    illustration = skia.Image.open(str(asset_path))
    if illustration is None:
        sh.problems.append(f"hand32: could not decode {asset_path.name}")
        return
    # Match the source's proportions: its hand is a compact left-edge gesture
    # (about 23% of the width and 52% of the height), not a full-height backdrop.
    # The transparent cutout's alpha bounds are 57% x 85% of its canvas.
    hand_box = Box(-sh.w*.005, sh.h*.13, sh.w*.41, sh.h*.61)
    hand_tint = paint()
    hand_tint.setColorFilter(skia.ColorFilters.Blend(
        C(hand_ink), skia.BlendMode.kSrcIn))
    sh.cv.save()
    sh.cv.translate(hand_box.x, hand_box.y)
    sh.cv.scale(hand_box.w / illustration.width(),
                hand_box.h / illustration.height())
    sh.cv.drawImage(illustration, 0, 0,
                    skia.SamplingOptions(skia.FilterMode.kLinear,
                                         skia.MipmapMode.kLinear), hand_tint)
    sh.cv.restore()
    sh.mark("supplied_hand_illustration", hand_box, collide=False, bleed=True)

    for name, word, box, size in (
            ("hand_nice", "Nice", Box(sh.w*.16, sh.h*.025, sh.w*.80, sh.h*.30), 415),
            ("hand_big", "Big", Box(sh.w*.43, sh.h*.33, sh.w*.56, sh.h*.30), 415),
            ("hand_font", "Font", Box(sh.w*.16, sh.h*.64, sh.w*.80, sh.h*.31), 415)):
        sh.text(name, ctx["display"], word, box, hi=size*sh.scale,
                lo=86*sh.scale, max_lines=1, color=type_ink,
                min_read=74*sh.scale, track=-.045, min_contrast=1.6)
    note_box = Box(sh.w*.255, sh.h*.415, sh.w*.165, sh.h*.14)
    sh.text("hand_note", ctx["label"], "Sometimes you\njust need a...",
            note_box, hi=37*sh.scale, lo=24*sh.scale, max_lines=2,
            color=type_ink, min_read=20*sh.scale, track=-.025)


@support("zebra32", "the supplied T13692 zebra and rose cutouts in the original two-panel specimen composition")
def t_zebra32(sh, ctx):
    # The source is two square black posters photographed together on a pale
    # page. Preserve that pair, rather than flattening its contents into one
    # edge-to-edge composition.
    paper, black, white = (239, 239, 237), (9, 10, 11), (246, 243, 236)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(paper)))
    card_y, card_h = sh.h*.164, sh.h*.674
    card_w, left_x, right_x = sh.w*.452, sh.w*.042, sh.w*.506
    cards = (Box(left_x, card_y, card_w, card_h),
             Box(right_x, card_y, card_w, card_h))
    texture_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                    "support-references" / "materials" /
                    "T13692_black-plastic-texture.png")
    texture = skia.Image.open(str(texture_path)) if texture_path.exists() else None
    if texture is None:
        sh.problems.append(f"zebra32: missing/decode failure for plastic texture {texture_path}")
        return
    for i, card in enumerate(cards):
        side = min(texture.width(), texture.height())
        sx = 0 if i == 0 else texture.width()-side
        src = skia.Rect.MakeXYWH(sx, 0, side, side)
        dst = skia.Rect.MakeXYWH(card.x, card.y, card.w, card.h)
        sh.cv.drawImageRect(texture, src, dst,
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        # Darken the generated film just enough to keep the type authoritative.
        sh.cv.drawRect(dst, paint(C(black, .20)))
        sh.mark(f"zebra_card{i}", card, collide=False)

    root = (Path(__file__).resolve().parents[2] / "font-factory" /
            "support-references" / "materials")
    art_specs = (
        ("T13692_zebra-arched.png",
         Box(left_x+card_w*.065, card_y+card_h*.105,
             card_w*.87, card_w*.87/1.5), "zebra_photo"),
        ("T13692_rose-strip.png",
         Box(right_x+card_w*.035, card_y+card_h*.665,
             card_w*.93, card_w*.93/3.0), "rose_photo"),
    )
    for filename, box, slot in art_specs:
        asset_path = root / filename
        if not asset_path.exists():
            sh.problems.append(f"zebra32: missing supplied material {asset_path}")
            return
        image = skia.Image.open(str(asset_path))
        if image is None:
            sh.problems.append(f"zebra32: could not decode {asset_path.name}")
            return
        sh.cv.drawImageRect(image,
                            skia.Rect.MakeWH(image.width(), image.height()),
                            skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        sh.mark(slot, box, collide=False)

    love_box = Box(left_x+card_w*.07, card_y+card_h*.625,
                   card_w*.86, card_h*.28)
    sh.text("zebra_love", ctx["display"], clean(ctx, "Love"), love_box,
            hi=275*sh.scale, lo=82*sh.scale, max_lines=1,
            color=white, min_read=64*sh.scale, track=-.045)
    rule(sh.cv, left_x+card_w*.12, card_y+card_h*.935,
         left_x+card_w*.88, card_y+card_h*.935, white,
         max(2.0, 3.0*sh.scale), .88)

    poem = ("Roses", "Are Red", "Chocolates", "Are Brown",
            "Valentine", "Is Bored", "If You Are", "Alone")
    # Right edges share one measure, while deliberately varied leading and word
    # widths keep the poem's left edge lively like the reference rather than a grid.
    poem_y = (.018, .096, .180, .262, .350, .430, .512, .588)
    for i, line in enumerate(poem):
        row = Box(right_x+card_w*.055,
                  card_y+card_h*poem_y[i], card_w*.89, card_h*.073)
        sh.text(f"zebra_poem{i}", ctx["display"], clean(ctx, line), row,
                hi=76*sh.scale, lo=23*sh.scale, max_lines=1,
                color=white, min_read=22*sh.scale, track=-.018,
                align="right", leading=.82)


@support("soldier32", "the T13692 clipped-corner archival photo, large year, headline, and character strip rebuilt around the extracted source photo")
def t_soldier32(sh, ctx):
    dark, white = (7, 8, 9), (245, 243, 237)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(dark)))
    frame = Box(sh.w*.05, sh.h*.202, sh.w*.90, sh.h*.594)
    line = paint(C(white, .68), style=skia.Paint.kStroke_Style,
                 width=max(1.5, 1.8*sh.scale))
    sh.cv.drawRect(skia.Rect.MakeXYWH(frame.x, frame.y, frame.w, frame.h), line)
    split_x = sh.w*.47
    split_y = sh.h*.614
    sh.cv.drawLine(split_x, frame.y, split_x, frame.b, line)
    sh.cv.drawLine(split_x, split_y, frame.r, split_y, line)

    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T13692_soldier-cutout.png")
    if not asset_path.exists():
        sh.problems.append(f"soldier32: missing OpenCV-reviewed source crop {asset_path}")
        return
    photo = skia.Image.open(str(asset_path))
    if photo is None:
        sh.problems.append(f"soldier32: could not decode {asset_path.name}")
        return
    photo_box = Box(sh.w*.08, sh.h*.244, sh.w*.36, sh.w*.36*photo.height()/photo.width())
    sh.cv.drawImageRect(photo,
                        skia.Rect.MakeWH(photo.width(), photo.height()),
                        skia.Rect.MakeXYWH(photo_box.x, photo_box.y,
                                           photo_box.w, photo_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("soldier_photo", photo_box, collide=False)

    year_box = Box(sh.w*.075, sh.h*.619, sh.w*.365, sh.h*.155)
    sh.text("soldier_year", ctx["display"], "1935", year_box,
            hi=285*sh.scale, lo=85*sh.scale, max_lines=1,
            color=white, min_read=62*sh.scale, track=-.045)
    headline_lines = ("This", "War Is", "Useless")
    for i, line in enumerate(headline_lines):
        row = Box(sh.w*.495, sh.h*(.232+i*.123),
                  sh.w*.435, sh.h*.107)
        sh.text(f"soldier_headline{i}", ctx["display"],
                clean(ctx, line), row,
                hi=164*sh.scale, lo=46*sh.scale, max_lines=1,
                color=white, min_read=42*sh.scale, track=-.025,
                align="center")
    digits = Box(sh.w*.50, sh.h*.621, sh.w*.43, sh.h*.077)
    symbols = Box(sh.w*.50, sh.h*.704, sh.w*.43, sh.h*.075)
    sh.text("soldier_digits", ctx["display"], "1234567890", digits,
            hi=86*sh.scale, lo=28*sh.scale, max_lines=1,
            color=white, min_read=24*sh.scale, track=-.018,
            align="center")
    sh.text("soldier_symbols", ctx["display"], clean(ctx, "!?$€£&"), symbols,
            hi=82*sh.scale, lo=27*sh.scale, max_lines=1,
            color=white, min_read=23*sh.scale, track=-.015,
            align="center")


@support("mirror32", "the T13692 mirror portrait and six-line overprinted quotation, using a transparent portrait material")
def t_mirror32(sh, ctx):
    dark, white = (5, 6, 7), (246, 244, 239)
    # The source is a flat black poster. Keep its supplied/regenerated portrait
    # insert, but do not borrow the crinkled-plastic ground from zebra32.
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(dark)))
    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T13692_mirror-portrait.png")
    if not asset_path.exists():
        sh.problems.append(f"mirror32: missing transparent portrait material {asset_path}")
        return
    portrait = skia.Image.open(str(asset_path))
    if portrait is None:
        sh.problems.append(f"mirror32: could not decode {asset_path.name}")
        return
    ph = sh.h*.67
    # Preserve the regenerated photo's natural aspect ratio; the previous insert
    # was stretched horizontally, which made the face feel more synthetic.
    pw = ph*portrait.width()/portrait.height()
    photo_box = Box(sh.w*.05, sh.h*.166, pw, ph)
    sh.cv.drawImageRect(portrait,
                        skia.Rect.MakeWH(portrait.width(), portrait.height()),
                        skia.Rect.MakeXYWH(photo_box.x, photo_box.y,
                                           photo_box.w, photo_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("mirror_portrait", photo_box, collide=False)

    lines = ("People Hasten", "To Judge", "In Order",
             "Not To Be", "Judged", "Themselves")
    for i, line in enumerate(lines):
        row = Box(sh.w*.205, sh.h*(.158+i*.116), sh.w*.745, sh.h*.112)
        sh.text(f"mirror_quote{i}", ctx["display"], clean(ctx, line), row,
                hi=142*sh.scale, lo=40*sh.scale, max_lines=1,
                color=white, min_read=36*sh.scale, track=-.026,
                align="right")


@support("brutal32", "the T13692_06 brutalist-photo book spread, rebuilding its four image panels and four-line editorial statement")
def t_brutal32(sh, ctx):
    black, left_page, right_page = (5, 6, 7), (43, 44, 45), (27, 28, 30)
    white, border = (246, 244, 239), (225, 225, 222)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))

    spread = Box(sh.w*.082, sh.h*.085, sh.w*.836, sh.h*.83)
    split = sh.w*.5
    sh.cv.drawRect(skia.Rect.MakeXYWH(spread.x, spread.y,
                                      split-spread.x, spread.h), paint(C(left_page)))
    sh.cv.drawRect(skia.Rect.MakeXYWH(split, spread.y,
                                      spread.r-split, spread.h), paint(C(right_page)))
    sh.cv.drawRect(skia.Rect.MakeXYWH(spread.x, spread.y, spread.w, spread.h),
                   paint(C(border, .92), style=skia.Paint.kStroke_Style,
                         width=max(3.0, 4.0*sh.scale)))
    sh.cv.drawLine(split, spread.y, split, spread.b,
                   paint(C((10, 10, 11), .68), width=max(2.0, 3.0*sh.scale)))

    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T13692_06_brutalist-photo-plate.png")
    plate = skia.Image.open(str(asset_path)) if asset_path.exists() else None
    if plate is None:
        sh.problems.append(f"brutal32: missing/decode failure for photo plate {asset_path}")
        return

    # The image model produced a four-cell archive contact sheet. Crop each
    # photograph away from the separator lines and keep the source proportions.
    source_cells = (
        (9, 66, 747, 373), (780, 66, 747, 373),
        (9, 582, 747, 373), (780, 582, 747, 373),
    )
    photo_w = sh.w*.20
    photo_h = sh.h*.15
    photo_slots = (
        Box(sh.w*.17, sh.h*.17, photo_w, photo_h),
        Box(sh.w*.64, sh.h*.17, photo_w, photo_h),
        Box(sh.w*.12, sh.h*.40, photo_w, photo_h),
        Box(sh.w*.53, sh.h*.71, photo_w, photo_h),
    )
    for i, (src_data, box) in enumerate(zip(source_cells, photo_slots)):
        src = skia.Rect.MakeXYWH(*src_data)
        dst = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        sh.cv.drawImageRect(plate, src, dst,
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        sh.cv.drawRect(dst, paint(C(border, .68),
                                  style=skia.Paint.kStroke_Style,
                                  width=max(1.5, 2.0*sh.scale)))
        sh.mark(f"brutal_photo{i}", box, collide=False)

    headline = (
        ("Brutalism", .22, .285, .56),
        ("A Play Between", .08, .40, .84),
        ("Crudity", .27, .515, .46),
        ("And Finesse", .17, .63, .66),
    )
    for i, (line, x, y, width) in enumerate(headline):
        row = Box(sh.w*x, sh.h*y, sh.w*width, sh.h*.09)
        sh.text(f"brutal_headline{i}", ctx["display"], clean(ctx, line), row,
                hi=252*sh.scale, lo=38*sh.scale, max_lines=1,
                color=white, min_read=34*sh.scale, track=-.026,
                align="center")


@support("brutalpack32", "the T13692_07 brutalism identity set: two vertical labels, an arched image card, and a geometric letter package")
def t_brutalpack32(sh, ctx):
    black, ink = (5, 6, 7), (32, 32, 33)
    paper, edge = (243, 242, 237), (210, 210, 207)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))

    pointed = Box(sh.w*.038, sh.h*.115, sh.w*.108, sh.h*.80)
    arched = Box(sh.w*.163, sh.h*.115, sh.w*.108, sh.h*.80)
    card = Box(sh.w*.289, sh.h*.115, sh.w*.416, sh.h*.80)
    package = Box(sh.w*.727, sh.h*.15, sh.w*.247, sh.h*.73)

    def label_shape(box, kind):
        x, y, w, h = box.x, box.y, box.w, box.h
        p = skia.Path()
        if kind == "point":
            peak = h*.105
            p.moveTo(x+w*.5, y)
            p.lineTo(x+w, y+peak)
            p.lineTo(x+w, y+h)
            p.lineTo(x, y+h)
            p.lineTo(x, y+peak)
            p.close()
        else:
            radius = w*.5
            p.moveTo(x, y+h)
            p.lineTo(x, y+radius)
            p.cubicTo(x, y+radius*.42, x+radius*.42, y,
                      x+radius, y)
            p.cubicTo(x+w-radius*.42, y, x+w, y+radius*.42,
                      x+w, y+radius)
            p.lineTo(x+w, y+h)
            p.close()
        sh.cv.drawPath(p, paint(C(paper)))
        sh.mark(f"brutalpack_{kind}_label", box, collide=False)

    label_shape(pointed, "point")
    label_shape(arched, "arch")
    for i, box in enumerate((pointed, arched)):
        sub = sh.sub(int(round(box.h)), int(round(box.w)))
        text_box = Box(sub.w*.055, sub.h*.12, sub.w*.89, sub.h*.76)
        sub.text(f"brutalpack_vertical{i}", ctx["display"],
                 clean(ctx, "Brutalism"), text_box,
                 hi=175*sh.scale, lo=42*sh.scale, max_lines=1,
                 color=ink, min_read=34*sh.scale, track=-.035)
        sh.paste(sub, box.x+box.w/2, box.y+box.h/2,
                 angle=90, shadow=None)

    sh.cv.drawRect(skia.Rect.MakeXYWH(card.x, card.y, card.w, card.h),
                   paint(C(paper)))
    sh.cv.drawLine(card.x+max(2.0, 3*sh.scale), card.y,
                   card.x+max(2.0, 3*sh.scale), card.b,
                   paint(C(edge, .9), width=max(2.0, 3*sh.scale)))
    sh.mark("brutalpack_architectural_card", card, collide=False)

    plate_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T13692_06_brutalist-photo-plate.png")
    plate = skia.Image.open(str(plate_path)) if plate_path.exists() else None
    if plate is None:
        sh.problems.append(f"brutalpack32: missing/decode failure for photo plate {plate_path}")
        return

    image_box = Box(sh.w*.385, sh.h*.205, sh.w*.23, sh.h*.40)
    x, y, w, h = image_box.x, image_box.y, image_box.w, image_box.h
    arch = skia.Path()
    arch.moveTo(x, y+h)
    arch.lineTo(x, y+w*.5)
    arch.cubicTo(x, y+w*.18, x+w*.22, y, x+w*.5, y)
    arch.cubicTo(x+w*.78, y, x+w, y+w*.18, x+w, y+w*.5)
    arch.lineTo(x+w, y+h)
    arch.close()
    sh.cv.save()
    sh.cv.clipPath(arch, skia.ClipOp.kIntersect, True)
    src = skia.Rect.MakeXYWH(1000, 520, 425, 496)
    dst = skia.Rect.MakeXYWH(x, y, w, h)
    sh.cv.drawImageRect(plate, src, dst,
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.cv.restore()
    sh.cv.drawPath(arch, paint(C(edge, .72), style=skia.Paint.kStroke_Style,
                               width=max(1.5, 2.0*sh.scale)))
    sh.mark("brutalpack_arch_photo", image_box, collide=False)

    sh.text("brutalpack_bruta", ctx["display"], clean(ctx, "Bruta"),
            Box(sh.w*.32, sh.h*.625, sh.w*.35, sh.h*.085),
            hi=155*sh.scale, lo=42*sh.scale, max_lines=1,
            color=ink, min_read=34*sh.scale, track=-.03)
    rule_y = sh.h*.765
    rule_x = sh.w*.385
    rule(sh.cv, rule_x, rule_y, rule_x+sh.w*.045, rule_y, ink,
         max(2.0, 3.0*sh.scale), .88)
    sh.text("brutalpack_lism", ctx["display"], clean(ctx, "Lism"),
            Box(sh.w*.435, sh.h*.73, sh.w*.18, sh.h*.085),
            hi=150*sh.scale, lo=42*sh.scale, max_lines=1,
            color=ink, min_read=34*sh.scale, track=-.025,
            align="left")

    hx, hy, hw, hh = package.x, package.y, package.w, package.h*.43
    hexagon = skia.Path()
    hexagon.moveTo(hx+hw*.25, hy)
    hexagon.lineTo(hx+hw*.75, hy)
    hexagon.lineTo(hx+hw, hy+hh*.5)
    hexagon.lineTo(hx+hw*.75, hy+hh)
    hexagon.lineTo(hx+hw*.25, hy+hh)
    hexagon.lineTo(hx, hy+hh*.5)
    hexagon.close()
    sh.cv.drawPath(hexagon, paint(C(paper)))
    sh.mark("brutalpack_hexagon", Box(hx, hy, hw, hh), collide=False)
    sh.text("brutalpack_initial", ctx["display"], clean(ctx, "B"),
            Box(hx+hw*.19, hy+hh*.15, hw*.62, hh*.70),
            hi=224*sh.scale, lo=62*sh.scale, max_lines=1,
            color=ink, min_read=48*sh.scale)

    body_y = hy+hh
    body_h = package.b-body_y
    # Use the transparent Potrace extraction of this exact folded package; the
    # previous hand-drawn wireframe lost its characteristic folded silhouette.
    fold_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                 "support-references" / "materials" /
                 "T13692_07-folded-package-lines.png")
    fold = skia.Image.open(str(fold_path)) if fold_path.exists() else None
    if fold is None:
        sh.problems.append(f"brutalpack32: missing/decode failure for fold material {fold_path}")
        return
    scale = min(hw/fold.width(), body_h/fold.height())
    fw, fh = fold.width()*scale, fold.height()*scale
    fold_box = Box(hx+(hw-fw)/2, body_y+(body_h-fh)/2, fw, fh)
    sh.cv.drawImageRect(fold, skia.Rect.MakeWH(fold.width(), fold.height()),
                        skia.Rect.MakeXYWH(fold_box.x, fold_box.y,
                                           fold_box.w, fold_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("brutalpack_folded_package", fold_box, collide=False)


@support("rio32", "the T24250_04 Rio de Janeiro travel landing-page hero rebuilt over a generated dusk panorama")
def t_rio32(sh, ctx):
    cream, ink = (246, 239, 220), (22, 18, 16)
    image_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T24250_04_rio-dusk-background.png")
    image = skia.Image.open(str(image_path)) if image_path.exists() else None
    if image is None:
        sh.problems.append(f"rio32: missing/decode failure for Rio background {image_path}")
        return
    sh.cv.drawImageRect(image,
                        skia.Rect.MakeWH(image.width(), image.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(ink, .23)))
    sh.mark("rio_background", Box(0, 0, sh.w, sh.h),
            collide=False, bleed=True)

    brand = (("Type", .054), ("Study", .101))
    for i, (line, y) in enumerate(brand):
        sh.text(f"rio_brand{i}", ctx["display"], clean(ctx, line),
                Box(sh.w*.038, sh.h*y, sh.w*.15, sh.h*.047),
                hi=48*sh.scale, lo=22*sh.scale, max_lines=1,
                color=cream, min_read=17*sh.scale, track=-.01,
                align="left")
    nav = (("Home", .535, .095),
           ("Catalog", .68, .14),
           ("Contact", .842, .14))
    for i, (label_text, x, width) in enumerate(nav):
        sh.text(f"rio_nav{i}", ctx["display"], clean(ctx, label_text),
                Box(sh.w*x, sh.h*.061, sh.w*width, sh.h*.058),
                hi=42*sh.scale, lo=20*sh.scale, max_lines=1,
                color=cream, min_read=16*sh.scale, track=.008)

    sh.text("rio_title_the", ctx["display"], clean(ctx, "The"),
            Box(sh.w*.25, sh.h*.215, sh.w*.22, sh.h*.105),
            hi=132*sh.scale, lo=48*sh.scale, max_lines=1,
            color=cream, min_read=40*sh.scale, track=-.02,
            align="left")
    sh.text("rio_title_janeiro", ctx["display"], clean(ctx, "Janeiro"),
            Box(sh.w*.145, sh.h*.33, sh.w*.72, sh.h*.205),
            hi=286*sh.scale, lo=72*sh.scale, max_lines=1,
            color=cream, min_read=58*sh.scale, track=-.035)
    sh.text("rio_subtitle", ctx["display"],
            clean(ctx, "The Weekend Holiday Trip"),
            Box(sh.w*.15, sh.h*.555, sh.w*.70, sh.h*.082),
            hi=62*sh.scale, lo=24*sh.scale, max_lines=1,
            color=cream, min_read=22*sh.scale, track=.008)

    button = Box(sh.w*.428, sh.h*.721, sh.w*.144, sh.h*.062)
    sh.cv.drawRoundRect(skia.Rect.MakeXYWH(button.x, button.y,
                                           button.w, button.h),
                        sh.h*.015, sh.h*.015,
                        paint(C(cream, .95),
                              style=skia.Paint.kStroke_Style,
                              width=max(2.0, 2.5*sh.scale)))
    sh.mark("rio_booking_button", button, collide=False)
    sh.text("rio_booking_label", ctx["display"], clean(ctx, "Book Now"),
            Box(button.x+button.w*.06, button.y+button.h*.13,
                button.w*.88, button.h*.74),
            hi=38*sh.scale, lo=18*sh.scale, max_lines=1,
            color=cream, min_read=15*sh.scale, track=-.012)

    footer = (
        "Happiness Consists Of Living Each Day As If It Were The First Day",
        "Of Your Honeymoon And The Last Day Of Your Vacation",
        "Trust Your Holiday Plans With Us",
    )
    for i, line in enumerate(footer):
        sh.text(f"rio_footer{i}", ctx["display"], clean(ctx, line),
                Box(sh.w*.08, sh.h*(.842+i*.034), sh.w*.84, sh.h*.03),
                hi=25*sh.scale, lo=14*sh.scale, max_lines=1,
                color=cream, min_read=12*sh.scale, track=-.008)


@support("boots32", "the T24507_04 western photography poster with a clean salt-flat image, coral horseshoes, and a transparent engraved boot")
def t_boots32(sh, ctx):
    sage, green, coral = (214, 222, 190), (27, 82, 44), (217, 101, 95)
    paper = Box(0, 0, sh.w, sh.h)
    photo_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T24507_04_saltflat-photo-crop.png")
    photo = skia.Image.open(str(photo_path)) if photo_path.exists() else None
    if photo is None:
        sh.problems.append(f"boots32: missing/decode failure for salt-flat photo {photo_path}")
        return

    # Let the source landscape softly echo through the sage paper field while
    # keeping the inset photograph crisp and all text at full contrast.
    soft = paint(C((255, 255, 255), .12))
    soft.setImageFilter(skia.ImageFilters.Blur(sh.w*.055, sh.h*.055))
    sh.cv.drawImageRect(photo, skia.Rect.MakeWH(photo.width(), photo.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear), soft)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(sage, .91)))
    grain(sh.cv, paper, .075, seed=24507, cell=96, magnify=6)

    panel = Box(sh.w*.062, sh.h*.125, sh.w*.40, sh.h*.75)
    sky = skia.GradientShader.MakeLinear(
        [skia.Point(panel.x, panel.y), skia.Point(panel.x, panel.y+panel.h*.47)],
        [C((47, 47, 49)), C((80, 80, 82))])
    sky_paint = paint()
    sky_paint.setShader(sky)
    sky_box = Box(panel.x, panel.y, panel.w, panel.h*.47)
    sh.cv.drawRect(skia.Rect.MakeXYWH(sky_box.x, sky_box.y,
                                      sky_box.w, sky_box.h), sky_paint)
    sh.mark("boots_soft_focus_sky", sky_box, collide=False)
    photo_box = Box(panel.x, panel.y+panel.h*.47, panel.w, panel.h*.53)
    sh.cv.drawImageRect(photo, skia.Rect.MakeWH(photo.width(), photo.height()),
                        skia.Rect.MakeXYWH(photo_box.x, photo_box.y,
                                           photo_box.w, photo_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("boots_saltflat_photo", photo_box, collide=False)

    boot_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                 "support-references" / "materials" /
                 "T24507_04_coral-cowboy-boot.png")
    boot = skia.Image.open(str(boot_path)) if boot_path.exists() else None
    if boot is None:
        sh.problems.append(f"boots32: missing/decode failure for transparent boot art {boot_path}")
        return
    boot_box = Box(sh.w*.81, sh.h*.635, sh.w*.18, sh.h*.325)
    tint = paint()
    tint.setColorFilter(skia.ColorFilters.Blend(
        C(coral), skia.BlendMode.kSrcIn))
    sh.cv.drawImageRect(boot,
                        skia.Rect.MakeWH(boot.width(), boot.height()),
                        skia.Rect.MakeXYWH(boot_box.x, boot_box.y,
                                           boot_box.w, boot_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear),
                        tint)
    sh.mark("boots_engraved_boot", boot_box, collide=False)

    def draw_star(cx, cy, radius):
        p = skia.Path()
        for j in range(16):
            angle = -math.pi/2 + j*math.pi/8
            r = radius if j % 2 == 0 else radius*.28
            px, py = cx+math.cos(angle)*r, cy+math.sin(angle)*r
            if j == 0:
                p.moveTo(px, py)
            else:
                p.lineTo(px, py)
        p.close()
        sh.cv.drawPath(p, paint(C(coral, .96)))

    def draw_horseshoe(cx, cy, width, height, angle):
        sh.cv.save()
        sh.cv.translate(cx, cy)
        sh.cv.rotate(angle)
        stroke = paint(C(coral, .92), style=skia.Paint.kStroke_Style,
                       width=max(2.0, 3.0*sh.scale))
        outer = skia.Path()
        outer.moveTo(-width*.42, -height*.42)
        outer.cubicTo(-width*.44, height*.18, -width*.24, height*.45,
                      0, height*.45)
        outer.cubicTo(width*.24, height*.45, width*.44, height*.18,
                      width*.42, -height*.42)
        sh.cv.drawPath(outer, stroke)
        inner = skia.Path()
        inner.moveTo(-width*.26, -height*.38)
        inner.cubicTo(-width*.27, height*.06, -width*.14, height*.29,
                      0, height*.29)
        inner.cubicTo(width*.14, height*.29, width*.27, height*.06,
                      width*.26, -height*.38)
        sh.cv.drawPath(inner, stroke)
        sh.cv.drawLine(-width*.43, -height*.42,
                       -width*.28, -height*.42, stroke)
        sh.cv.drawLine(width*.43, -height*.42,
                       width*.28, -height*.42, stroke)
        for sx, sy in ((-.33, -.07), (-.22, .22), (0, .39),
                       (.22, .22), (.33, -.07)):
            draw_star(sx*width, sy*height, max(5.0, width*.026))
        sh.cv.restore()
        sh.mark("boots_horseshoe", Box(cx-width*.55, cy-height*.55,
                                       width*1.10, height*1.10),
                collide=False, bleed=True)

    draw_horseshoe(sh.w*.065, sh.h*.145, sh.w*.105, sh.h*.19, -14)
    draw_horseshoe(sh.w*.145, sh.h*.115, sh.w*.125, sh.h*.22, 0)
    draw_horseshoe(sh.w*.225, sh.h*.15, sh.w*.095, sh.h*.18, 13)

    sh.text("boots_title", ctx["display"], clean(ctx, "Wild Boots"),
            Box(sh.w*.515, sh.h*.39, sh.w*.445, sh.h*.14),
            hi=176*sh.scale, lo=50*sh.scale, max_lines=1,
            color=green, min_read=42*sh.scale, track=-.028)
    sh.text("boots_subtitle", ctx["display"], clean(ctx, "photography"),
            Box(sh.w*.63, sh.h*.55, sh.w*.29, sh.h*.075),
            hi=76*sh.scale, lo=30*sh.scale, max_lines=1,
            color=green, min_read=28*sh.scale, track=-.02)


@support("plakat32", "the T27673_00 poster specimen with a large two-line display phrase, enlarged cyan symbol band, and compact factual axes")
def t_plakat32(sh, ctx):
    navy, cream = (4, 20, 39), (247, 242, 229)
    cyan = (45, 190, 226)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(navy)))
    grain(sh.cv, Box(0, 0, sh.w, sh.h), .06,
          seed=27673, cell=128, magnify=6)
    sh.mark("plakat_navy_ground", Box(0, 0, sh.w, sh.h),
            collide=False, bleed=True)

    caps = sum(usable(ctx, chr(cp)) for cp in range(ord("A"), ord("Z")+1))
    lowers = sum(usable(ctx, chr(cp)) for cp in range(ord("a"), ord("z")+1))
    facts = f"{caps}/26 Caps   ·   {lowers}/26 Lower"
    sh.text("plakat_facts", ctx["label"], facts,
            Box(sh.w*.065, sh.h*.035, sh.w*.87, sh.h*.045),
            hi=25*sh.scale, lo=15*sh.scale, max_lines=1,
            color=cream, min_read=14*sh.scale, track=.015,
            align="center")

    words = _support_word(ctx, "Plakat").split()
    if len(words) > 1:
        split_at = (len(words)+1)//2
        headline = " ".join(words[:split_at])+"\n"+" ".join(words[split_at:])
    else:
        first = words[0] if words else "Poster"
        headline = first
    sh.text("plakat_headline", ctx["display"], clean(ctx, headline),
            Box(sh.w*.065, sh.h*.095, sh.w*.87, sh.h*.405),
            hi=445*sh.scale, lo=68*sh.scale, max_lines=2,
            color=cream, min_read=46*sh.scale, track=-.045,
            align="center", valign="middle")

    # The illustrated symbol strip is intentionally a broad, tall feature now;
    # facts and axes are compact rails rather than competing panels.
    panel = Box(sh.w*.07, sh.h*.545, sh.w*.86, sh.h*.235)
    row_h = panel.h
    panel_stroke = paint(C(cream, .91), style=skia.Paint.kStroke_Style,
                         width=max(1.5, 2.0*sh.scale))
    left_w, icon_w = sh.w*.24, sh.w*.47
    icon_x = panel.x+left_w
    variable_x = icon_x+icon_w
    sh.cv.drawRect(skia.Rect.MakeXYWH(icon_x, panel.y, icon_w, row_h),
                   paint(C(cyan)))
    sh.cv.drawRect(skia.Rect.MakeXYWH(variable_x, panel.y,
                                      panel.r-variable_x, row_h),
                   paint(C(cream)))
    sh.cv.drawRect(skia.Rect.MakeXYWH(panel.x, panel.y, panel.w, panel.h),
                   panel_stroke)
    sh.cv.drawLine(icon_x, panel.y, icon_x, panel.y+row_h, panel_stroke)
    sh.cv.drawLine(variable_x, panel.y, variable_x, panel.y+row_h, panel_stroke)
    sh.text("plakat_glyphs", ctx["label"],
            f"{ctx['facts']['glyphs']} Glyphs",
            Box(panel.x+sh.w*.014, panel.y+sh.h*.048,
                left_w-sh.w*.028, sh.h*.055),
            hi=35*sh.scale, lo=18*sh.scale, max_lines=1,
            color=cream, min_read=16*sh.scale, track=-.015,
            align="left", valign="middle")
    sh.text("plakat_multilingual", ctx["label"],
            f"{caps}/26 Caps\n{lowers}/26 Lower",
            Box(panel.x+sh.w*.014, panel.y+sh.h*.116,
                left_w-sh.w*.028, sh.h*.085),
            hi=25*sh.scale, lo=15*sh.scale, max_lines=2,
            color=cream, min_read=14*sh.scale, track=-.01,
            align="left", valign="middle")
    variable_box = Box(variable_x+sh.w*.012, panel.y+sh.h*.009,
                       panel.r-variable_x-sh.w*.024, sh.h*.217)
    sh.text("plakat_variable", ctx["display"], clean(ctx, "Form"),
            variable_box, hi=116*sh.scale, lo=30*sh.scale, max_lines=1,
            color=navy, min_read=24*sh.scale, track=-.035,
            align="center", valign="middle")
    sh.mark("plakat_variable_cell", Box(variable_x, panel.y,
                                        panel.r-variable_x, row_h),
            collide=False)

    tile = Box(icon_x, panel.y, icon_w, row_h)
    sh.mark("plakat_icon_tile", tile, collide=False)
    white_ink = paint(C(cream), style=skia.Paint.kStroke_Style,
                      width=max(2.4, 3.0*sh.scale))
    cy = panel.y+row_h*.5
    icon_r = min(row_h*.30, icon_w*.070)
    centers = [icon_x+icon_w*(.10+i*.20) for i in range(5)]

    def star_icon(cx, cy0, radius, points=8):
        p = skia.Path()
        for j in range(points*2):
            ang = -math.pi/2+j*math.pi/points
            r = radius if j % 2 == 0 else radius*.34
            px, py = cx+math.cos(ang)*r, cy0+math.sin(ang)*r
            if j == 0:
                p.moveTo(px, py)
            else:
                p.lineTo(px, py)
        p.close()
        sh.cv.drawPath(p, paint(C(cream)))

    def loop_icon(cx, cy0, radius, reverse=False):
        arc = skia.Path()
        start, sweep = ((34, 286) if not reverse else (216, 286))
        arc.addArc(skia.Rect.MakeXYWH(cx-radius, cy0-radius,
                                     radius*2, radius*2), start, sweep)
        sh.cv.drawPath(arc, white_ink)
        end_ang = math.radians(start+sweep)
        ex, ey = cx+radius*math.cos(end_ang), cy0+radius*math.sin(end_ang)
        tangent = (-math.sin(end_ang), math.cos(end_ang))
        if reverse:
            tangent = (-tangent[0], -tangent[1])
        side = (-tangent[1], tangent[0])
        p = skia.Path()
        p.moveTo(ex+tangent[0]*8*sh.scale,
                 ey+tangent[1]*8*sh.scale)
        p.lineTo(ex-tangent[0]*7*sh.scale+side[0]*6*sh.scale,
                 ey-tangent[1]*7*sh.scale+side[1]*6*sh.scale)
        p.lineTo(ex-tangent[0]*7*sh.scale-side[0]*6*sh.scale,
                 ey-tangent[1]*7*sh.scale-side[1]*6*sh.scale)
        p.close()
        sh.cv.drawPath(p, paint(C(cream)))

    def flower_icon(cx, cy0, radius):
        for j in range(8):
            ang = j*math.pi/4
            sh.cv.drawCircle(cx+math.cos(ang)*radius*.48,
                             cy0+math.sin(ang)*radius*.48,
                             radius*.24, paint(C(cream)))
        sh.cv.drawCircle(cx, cy0, radius*.23, paint(C(cream)))

    def heart_icon(cx, cy0, radius):
        p = skia.Path()
        p.moveTo(cx, cy0+radius*.78)
        p.cubicTo(cx-radius*1.2, cy0+radius*.05,
                  cx-radius*.9, cy0-radius*.92,
                  cx-radius*.38, cy0-radius*.76)
        p.cubicTo(cx-radius*.10, cy0-radius*.68,
                  cx, cy0-radius*.35, cx, cy0-radius*.30)
        p.cubicTo(cx, cy0-radius*.35,
                  cx+radius*.10, cy0-radius*.68,
                  cx+radius*.38, cy0-radius*.76)
        p.cubicTo(cx+radius*.9, cy0-radius*.92,
                  cx+radius*1.2, cy0+radius*.05,
                  cx, cy0+radius*.78)
        p.close()
        sh.cv.drawPath(p, paint(C(cream)))

    loop_icon(centers[0], cy, icon_r*.82)
    star_icon(centers[1], cy, icon_r*.76, points=8)
    flower_icon(centers[2], cy, icon_r*.84)
    heart_icon(centers[3], cy, icon_r*.76)
    loop_icon(centers[4], cy, icon_r*.82, reverse=True)

    weight_position = max(.06, min(.94, (ctx["facts"]["weight"]-100) / 800))
    slanted = ctx["facts"]["slant"] > .01
    row_defs = (("Thin", "Black", .858, weight_position),
                ("Upright", "Italic", .945, .92 if slanted else .08))
    for i, (left, right, yfrac, marker) in enumerate(row_defs):
        y = sh.h*yfrac
        label_y = y-sh.h*.034
        sh.text(f"plakat_axis_left{i}", ctx["label"], left,
                Box(sh.w*.07, label_y, sh.w*.14, sh.h*.035),
                hi=26*sh.scale, lo=16*sh.scale, max_lines=1,
                color=cream, min_read=14*sh.scale, align="left")
        sh.text(f"plakat_axis_right{i}", ctx["label"], right,
                Box(sh.w*.82, label_y, sh.w*.11, sh.h*.035),
                hi=26*sh.scale, lo=16*sh.scale, max_lines=1,
                color=cream, min_read=14*sh.scale, align="right")
        x0, x1 = sh.w*.23, sh.w*.81
        rule(sh.cv, x0, y, x1, y, (54, 107, 137),
             max(1.5, 2.0*sh.scale), .88)
        mx = x0+(x1-x0)*marker
        diamond = skia.Path()
        size = 7*sh.scale
        diamond.moveTo(mx, y-size)
        diamond.lineTo(mx+size, y)
        diamond.lineTo(mx, y+size)
        diamond.lineTo(mx-size, y)
        diamond.close()
        sh.cv.drawPath(diamond, paint(C(cyan)))
        sh.cv.drawLine(mx, y, mx, y+sh.h*.009,
                       paint(C(cyan, .58), width=max(1.2, 1.5*sh.scale)))


@support("plakatart32", "the T27673_10 red/cyan macro-texture specimen with compact metadata and oversized overlapping display copy")
def t_plakatart32(sh, ctx):
    black, cream, cyan = (3, 4, 5), (246, 243, 233), (47, 190, 224)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))

    asset_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T27673_10_red-cyan-macro-texture.png")
    texture = skia.Image.open(str(asset_path)) if asset_path.exists() else None
    if texture is None:
        sh.problems.append(f"plakatart32: missing/decode failure for macro texture {asset_path}")
        return
    # The reference uses a wide, nearly square macro-texture window. Crop the
    # generated 3:2 plate symmetrically so the fibers retain their natural scale.
    src_w = texture.height() * 1.2
    src = skia.Rect.MakeXYWH((texture.width() - src_w) / 2, 0,
                             src_w, texture.height())
    art = Box(sh.w*.315, sh.h*.075, sh.w*.615, sh.h*.77)
    sh.cv.drawImageRect(texture, src,
                        skia.Rect.MakeXYWH(art.x, art.y, art.w, art.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("plakatart_texture", art, collide=False)

    meta = (
        ("plakatart_styles", "Display Study", .075, .075, cyan),
        ("plakatart_variable", "Form & Space", .075, .111, cyan),
        ("plakatart_weights", "Letterforms", .075, .147, cyan),
        ("plakatart_italics", "Ink / Image", .075, .183, cyan),
        ("plakatart_designed", "Type Culture", .075, .382, cream),
        ("plakatart_foundry", "Red + Cyan", .075, .418, cream),
        ("plakatart_year", "Specimen", .075, .454, cream),
    )
    for name, label, x, y, color in meta:
        sh.text(name, ctx["label"], label,
                Box(sh.w*x, sh.h*y, sh.w*.205, sh.h*.027),
                hi=34*sh.scale, lo=18*sh.scale, max_lines=1,
                color=color, min_read=16*sh.scale, track=.015,
                align="left")

    # Deliberate overlap over the lower-left of the art panel mirrors the
    # reference's nameplate; the image is non-colliding by design.
    sh.text("plakatart_title", ctx["display"],
            clean(ctx, _support_word(ctx, "Plakat")),
            Box(sh.w*.062, sh.h*.485, sh.w*.655, sh.h*.355),
            hi=505*sh.scale, lo=95*sh.scale, max_lines=1,
            color=cream, min_read=82*sh.scale, track=-.035,
            align="left", glow=((0, 0, 0), 0.11, .58))


@support("mangos32", "the T30930_07 Mangos botanical specimen poster with a weight ramp, fruit details, and nutrition-style data")
def t_mangos32(sh, ctx):
    black, white, cyan, orange = (13, 15, 15), (244, 244, 239), (35, 201, 229), (247, 112, 28)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))

    sh.text("mangos_title", ctx["display"], clean(ctx, "Botanical"),
            Box(sh.w*.066, sh.h*.055, sh.w*.36, sh.h*.12),
            hi=170*sh.scale, lo=42*sh.scale, max_lines=1,
            color=cyan, min_read=40*sh.scale, track=-.025, align="left")
    sh.text("mangos_foundry", ctx["label"], "Field Notes",
            Box(sh.w*.605, sh.h*.064, sh.w*.33, sh.h*.095),
            hi=118*sh.scale, lo=44*sh.scale, max_lines=1,
            color=white, min_read=36*sh.scale, track=-.015, align="right")

    # Variable-axis arrow: a clean, compact sign between the two wordmarks.
    ax0, ax1, ay = sh.w*.455, sh.w*.555, sh.h*.112
    arrow = paint(C(cyan), style=skia.Paint.kStroke_Style,
                  width=max(3.0, 4.0*sh.scale))
    arrow.setStrokeCap(skia.Paint.kRound_Cap)
    arrow.setStrokeJoin(skia.Paint.kRound_Join)
    sh.cv.drawLine(ax0, ay, ax1, ay, arrow)
    for x, direction in ((ax0, -1), (ax1, 1)):
        p = skia.Path()
        p.moveTo(x-direction*15*sh.scale, ay-16*sh.scale)
        p.lineTo(x, ay)
        p.lineTo(x-direction*15*sh.scale, ay+16*sh.scale)
        sh.cv.drawPath(p, arrow)

    # The amber-to-black strip is the variable weight ramp in the reference.
    ramp = Box(sh.w*.215, sh.h*.247, sh.w*.72, sh.h*.085)
    shader = skia.GradientShader.MakeLinear(
        [skia.Point(ramp.x, ramp.y), skia.Point(ramp.r, ramp.y)],
        [C(orange), C((205, 69, 20)), C((35, 24, 21))], [0.0, .48, 1.0])
    ramp_paint = paint()
    ramp_paint.setShader(shader)
    sh.cv.drawRect(skia.Rect.MakeXYWH(ramp.x, ramp.y, ramp.w, ramp.h),
                   ramp_paint)
    sh.mark("mangos_weight_ramp", ramp, collide=False)

    # A small infinity loop stands in for the variable-axis symbol at left.
    cx, cy, rx, ry = sh.w*.125, sh.h*.285, sh.w*.057, sh.h*.041
    loop = skia.Path()
    loop.moveTo(cx-rx, cy)
    loop.cubicTo(cx-rx*.5, cy-ry*1.2, cx-rx*.2, cy-ry*1.2,
                 cx, cy)
    loop.cubicTo(cx+rx*.25, cy+ry*1.2, cx+rx*.5, cy+ry*1.2,
                 cx+rx, cy)
    loop.cubicTo(cx+rx*.5, cy-ry*1.2, cx+rx*.25, cy-ry*1.2,
                 cx, cy)
    loop.cubicTo(cx-rx*.2, cy+ry*1.2, cx-rx*.5, cy+ry*1.2,
                 cx-rx, cy)
    sh.cv.drawPath(loop, paint(C(cyan), style=skia.Paint.kStroke_Style,
                               width=max(3.0, 4.0*sh.scale)))

    for i, line in enumerate(("Botanical", "Tropical", "Fruit Study")):
        sh.text(f"mangos_descriptor{i}", ctx["label"], line,
                Box(sh.w*.068, sh.h*(.382+i*.052), sh.w*.19, sh.h*.045),
                hi=43*sh.scale, lo=21*sh.scale, max_lines=1,
                color=white, min_read=18*sh.scale, track=-.015,
                align="left")
    sh.text("mangos_botanical", ctx["display"], clean(ctx, "Mangifera indica L."),
            Box(sh.w*.285, sh.h*.365, sh.w*.64, sh.h*.145),
            hi=162*sh.scale, lo=49*sh.scale, max_lines=1,
            color=white, min_read=43*sh.scale, track=-.025,
            align="center")

    sh.text("mangos_weight", ctx["display"], "100g",
            Box(sh.w*.07, sh.h*.545, sh.w*.25, sh.h*.12),
            hi=158*sh.scale, lo=65*sh.scale, max_lines=1,
            color=cyan, min_read=54*sh.scale, track=-.04, align="left")
    sh.text("mangos_ounces", ctx["display"], "(3.53oz)",
            Box(sh.w*.375, sh.h*.545, sh.w*.34, sh.h*.12),
            hi=146*sh.scale, lo=53*sh.scale, max_lines=1,
            color=cyan, min_read=44*sh.scale, track=-.035, align="center")
    # A simple plant/fruit sign balances the figures without importing a photo.
    fx, fy = sh.w*.855, sh.h*.602
    sh.cv.drawCircle(fx, fy, sh.h*.035,
                     paint(C(cyan), style=skia.Paint.kStroke_Style,
                           width=max(3.0, 4.0*sh.scale)))
    leaf = skia.Path()
    leaf.moveTo(fx, fy-sh.h*.045)
    leaf.cubicTo(fx+sh.w*.018, fy-sh.h*.105,
                 fx+sh.w*.073, fy-sh.h*.091,
                 fx+sh.w*.074, fy-sh.h*.045)
    leaf.cubicTo(fx+sh.w*.039, fy-sh.h*.027,
                 fx+sh.w*.018, fy-sh.h*.032, fx, fy-sh.h*.045)
    leaf.close()
    sh.cv.drawPath(leaf, paint(C(cyan)))
    sh.mark("mangos_botanical_icon", Box(fx-sh.h*.04, fy-sh.h*.11,
                                          sh.h*.13, sh.h*.15), collide=False)

    sh.text("mangos_energy", ctx["display"], "Energy provided",
            Box(sh.w*.07, sh.h*.685, sh.w*.52, sh.h*.115),
            hi=142*sh.scale, lo=48*sh.scale, max_lines=1,
            color=white, min_read=40*sh.scale, track=-.035, align="left")
    sh.text("mangos_kilojoules", ctx["display"], "~ 272 kJ",
            Box(sh.w*.65, sh.h*.685, sh.w*.28, sh.h*.115),
            hi=145*sh.scale, lo=51*sh.scale, max_lines=1,
            color=cyan, min_read=43*sh.scale, track=-.03, align="right")
    sh.text("mangos_tropical", ctx["display"], "Tropical",
            Box(sh.w*.07, sh.h*.855, sh.w*.30, sh.h*.082),
            hi=108*sh.scale, lo=36*sh.scale, max_lines=1,
            color=cyan, min_read=29*sh.scale, track=-.035, align="left")
    sh.text("mangos_fraction", ctx["display"], "1/2",
            Box(sh.w*.455, sh.h*.842, sh.w*.10, sh.h*.10),
            hi=122*sh.scale, lo=42*sh.scale, max_lines=1,
            color=cyan, min_read=34*sh.scale, align="center")
    sh.text("mangos_subtropical", ctx["display"], "Subtropical",
            Box(sh.w*.62, sh.h*.855, sh.w*.31, sh.h*.082),
            hi=108*sh.scale, lo=36*sh.scale, max_lines=1,
            color=cyan, min_read=29*sh.scale, track=-.035, align="right")


@support("alphabet32", "the T30930_05 geometric sans specimen with uppercase, lowercase, and figure rows separated by fine rules")
def t_alphabet32(sh, ctx):
    paper, ink, orange, muted = (250, 249, 239), (20, 20, 20), (231, 101, 27), (112, 109, 100)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(paper)))
    rule_y = (sh.h*.345, sh.h*.695)
    for y in rule_y:
        rule(sh.cv, sh.w*.055, y, sh.w*.945, y, (205, 201, 187),
             max(1.4, 1.8*sh.scale), .8)

    upper = clean(ctx, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # Two generous alphabet rows match the source specimen's hierarchy. The
    # orange letters are drawn over the same outlines at measured advances, so
    # the small colour accents stay attached to the correct glyphs at any size.
    def alphabet_line(name, text, box, hi, indices, align="center"):
        face = ctx["display"]
        track = hi * -.035
        size = fit(face, text, box, hi, 52*sh.scale,
                   track, .86, 1)
        sh.text(name, face, text, box,
                hi=hi, lo=52*sh.scale, max_lines=1,
                color=ink, min_read=39*sh.scale, track=-.035,
                align=align)
        if size is None:
            return
        whole, _ = face.path(text, size, track)
        whole_bounds = whole.getBounds()
        origin_x = (box.x + (box.w - whole_bounds.width())/2 - whole_bounds.x()
                    if align == "center" else box.x - whole_bounds.x())
        baseline = box.y + (box.h - whole_bounds.height())/2 - whole_bounds.y()
        x = 0.0
        chosen = set(indices)
        font = face.font(size)
        for glyph_index, (gid, advance, xoff, yoff) in enumerate(
                face.runs(text, size)):
            glyph = font.getPath(gid)
            glyph.offset(x + xoff + origin_x, baseline - yoff)
            if glyph_index in chosen:
                sh.cv.drawPath(glyph, paint(C(orange)))
                bounds = glyph.getBounds()
                sh.mark(f"{name}_orange{glyph_index}",
                        Box(bounds.x(), bounds.y(), bounds.width(), bounds.height()),
                        collide=False)
            x += advance + track

    upper_rows = ("ABCDEFGHIJKLM", "NOPQRSTUVWXYZ")
    for i, text in enumerate(upper_rows):
        alphabet_line(f"alphabet_upper{i}", text,
                      Box(sh.w*.055, sh.h*(.045+i*.142), sh.w*.89, sh.h*.132),
                      246*sh.scale, (0, 12) if i == 0 else (8,))

    for i, label in enumerate(("Uppercase", "Lowercase", "Figures")):
        sh.text(f"alphabet_descriptor{i}", ctx["label"], label,
                Box(sh.w*.07, sh.h*(.425+i*.055), sh.w*.22, sh.h*.045),
                hi=42*sh.scale, lo=20*sh.scale, max_lines=1,
                color=muted, min_read=17*sh.scale, track=-.015,
                align="left")
    for i, letters in enumerate(("abcdefghijklm", "nopqrstuvwxyz")):
        alphabet_line(f"alphabet_lower{i}", clean(ctx, letters),
                      Box(sh.w*.335, sh.h*(.395+i*.137), sh.w*.60, sh.h*.125),
                      178*sh.scale, (0,) if i == 0 else (11,), align="left")

    figures = clean(ctx, "#0123456789")
    alphabet_line("alphabet_figures", figures,
                  Box(sh.w*.07, sh.h*.738, sh.w*.66, sh.h*.19),
                  190*sh.scale, (3,), align="left")
    sh.text("alphabet_foundry", ctx["label"], "Letterform Study",
            Box(sh.w*.73, sh.h*.847, sh.w*.20, sh.h*.048),
            hi=46*sh.scale, lo=22*sh.scale, max_lines=1,
            color=orange, min_read=18*sh.scale, track=-.01,
            align="right")
    sh.text("alphabet_signature", ctx["label"], "Glyph Specimen",
            Box(sh.w*.71, sh.h*.895, sh.w*.22, sh.h*.035),
            hi=28*sh.scale, lo=16*sh.scale, max_lines=1,
            color=muted, min_read=14*sh.scale, track=.005,
            align="right")


@support("birvase32", "the T33110_08 red/cyan screenprint poster with a single centered face-driven specimen word")
def t_birvase32(sh, ctx):
    image_path = (Path(__file__).resolve().parents[2] / "font-factory" /
                  "support-references" / "materials" /
                  "T33110_08_red-cyan-print-texture.png")
    image = skia.Image.open(str(image_path)) if image_path.exists() else None
    if image is None:
        sh.problems.append(f"birvase32: missing/decode failure for red/cyan print texture {image_path}")
        return
    sh.cv.drawImageRect(image,
                        skia.Rect.MakeWH(image.width(), image.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("birvase_print_ground", Box(0, 0, sh.w, sh.h),
            collide=False, bleed=True)
    word = " ".join(_support_word(ctx, "Birvase").split()[:2])
    sh.text("birvase_wordmark", ctx["display"], clean(ctx, word),
            Box(sh.w*.13, sh.h*.31, sh.w*.74, sh.h*.38),
            hi=440*sh.scale, lo=90*sh.scale, max_lines=1,
            color=(5, 5, 7), min_read=72*sh.scale, track=-.04,
            glow=((250, 245, 231), 0.035, .2))


@support("weightfamily32", "the T30930_01 family proof, with two or three real sibling-style alphabets led by orange style labels")
def t_weightfamily32(sh, ctx):
    black, paper, orange = (18, 20, 20), (245, 244, 239), (235, 105, 27)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))
    rows = ctx.get("family_samples", [])
    if len(rows) < 2:
        sh.problems.append("weightfamily32: needs at least two real styles from this family")
        return
    available_h = sh.h*.88
    row_weights = [.95] + [1.0] * (len(rows)-1)
    row_unit = available_h/sum(row_weights)
    y = sh.h*.055
    for i, sample in enumerate(rows):
        row_h = row_unit*row_weights[i]
        label_box = Box(sh.w*.045, y, sh.w*.20, row_h*.78)
        sh.text(f"weightfamily_label{i}", ctx["label"],
                tc(clean(ctx, sample["label"])), label_box,
                hi=42*sh.scale, lo=18*sh.scale, max_lines=2,
                color=orange, min_read=17*sh.scale, track=.02,
                align="left", valign="middle")
        rule(sh.cv, sh.w*.045, y+row_h*.91, sh.w*.245,
             y+row_h*.91, orange, max(1.5, 2.0*sh.scale), .84)
        face = sample["face"]
        for j, letters in enumerate(("ABCDEFGHIJKLM", "NOPQRSTUVWXYZ")):
            sh.text(f"weightfamily_alphabet{i}_{j}", face, clean(ctx, letters),
                    Box(sh.w*.275, y+row_h*(.02+j*.44),
                        sh.w*.68, row_h*.39),
                    hi=145*sh.scale, lo=45*sh.scale, max_lines=1,
                    color=paper, min_read=35*sh.scale, track=-.018,
                    align="left")
        y += row_h


@support("mangosboard32", "the T30930_04 modular type-family board: two or three real styles, a central character strip, and colour-block specimens")
def t_mangosboard32(sh, ctx):
    black, white = (13, 15, 15), (250, 249, 243)
    orange, cyan = (255, 105, 17), (25, 198, 235)
    sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(black)))
    left, top, gap = sh.w*.035, sh.h*.035, sh.w*.018
    orange_box = Box(left, top, sh.w*.365, sh.h*.255)
    variable_box = Box(orange_box.r+gap, top,
                       sh.w*.965-(orange_box.r+gap), sh.h*.255)
    radius = sh.h*.012

    def glossy_card(box, fill, edge):
        rect = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        sh.cv.drawRoundRect(rect, radius, radius, paint(C(fill)))
        # A narrow, restrained top highlight restores the laminated print sheen
        # visible in the reference without turning the cards into chrome.
        rule(sh.cv, box.x+radius, box.y+radius*.55,
             box.r-radius, box.y+radius*.55, edge,
             max(1.3, 1.8*sh.scale), .45)
        sh.cv.drawRoundRect(rect, radius, radius,
                            paint(C(edge, .46),
                                  style=skia.Paint.kStroke_Style,
                                  width=max(1.2, 1.6*sh.scale)))

    glossy_card(orange_box, orange, white)
    glossy_card(variable_box, white, (212, 207, 194))
    rows = ctx.get("family_samples", [])
    if len(rows) < 2:
        sh.problems.append("mangosboard32: needs at least two real styles from this family")
        return
    specimen = "Type"
    row_h = orange_box.h/len(rows)
    for i, sample in enumerate(rows):
        y = orange_box.y+i*row_h
        style_name = family_style_label(ctx.get("name"), sample.get("label"))
        # This is a factual family proof, the one deliberate exception to the
        # support-copy rule against repeating the showcased product name.
        support_ctx = getattr(sh, "_support_ctx", None)
        sh._support_ctx = None
        try:
            sh.text(f"mangosboard_style{i}", ctx["label"],
                    clean(ctx, style_name),
                    Box(orange_box.x+orange_box.w*.055, y+row_h*.04,
                        orange_box.w*.89, row_h*.25),
                    hi=25*sh.scale, lo=14*sh.scale, max_lines=1,
                    color=black, min_read=14*sh.scale, track=.01,
                    align="left")
        finally:
            sh._support_ctx = support_ctx
        sh.text(f"mangosboard_specimen{i}", sample["face"], specimen,
                Box(orange_box.x+orange_box.w*.055, y+row_h*.31,
                    orange_box.w*.89, row_h*.64),
                hi=72*sh.scale, lo=28*sh.scale, max_lines=1,
                color=black, min_read=26*sh.scale, track=-.025,
                align="left")
    sh.text("mangosboard_title", ctx["display"], clean(ctx, "Family"),
            Box(variable_box.x+variable_box.w*.055,
                variable_box.y+variable_box.h*.12,
                variable_box.w*.89, variable_box.h*.72),
            hi=190*sh.scale, lo=50*sh.scale, max_lines=1,
            color=orange, min_read=42*sh.scale, track=-.04)

    glyphs = "C€Ω½?†qTTD0123456789"
    glyphs = "".join(ch for ch in glyphs if usable(ctx, ch)) or "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    strip = Box(left, sh.h*.31, sh.w*.93, sh.h*.335)
    sh.cv.drawRect(skia.Rect.MakeXYWH(strip.x, strip.y, strip.w, strip.h),
                   paint(C((31, 33, 33))))
    sh.cv.drawRect(skia.Rect.MakeXYWH(strip.x, strip.y, strip.w, strip.h),
                   paint(C((174, 178, 176), .8),
                         style=skia.Paint.kStroke_Style,
                         width=max(1.4, 2.0*sh.scale)))
    sh.text("mangosboard_glyphs", ctx["display"], glyphs,
            Box(strip.x+strip.w*.035, strip.y+strip.h*.08,
                strip.w*.93, strip.h*.82),
            hi=214*sh.scale, lo=48*sh.scale, max_lines=1,
            color=white, min_read=36*sh.scale, track=-.03)

    bottom_y, bottom_h = sh.h*.665, sh.h*.30
    tile_w, tile_gap = sh.w*.225, sh.w*.018
    left_tile = Box(left, bottom_y, tile_w, bottom_h)
    center_tile = Box(left_tile.r+tile_gap, bottom_y,
                      sh.w*.43, bottom_h)
    right_tile = Box(center_tile.r+tile_gap, bottom_y,
                     sh.w*.93-(center_tile.r+tile_gap), bottom_h)
    glossy_card(left_tile, cyan, white)
    sh.text("mangosboard_Aa", ctx["display"], clean(ctx, "Aa"),
            Box(left_tile.x+left_tile.w*.06, left_tile.y+left_tile.h*.08,
                left_tile.w*.88, left_tile.h*.82),
            hi=245*sh.scale, lo=62*sh.scale, max_lines=1,
            color=white, min_read=44*sh.scale, track=-.04)

    glossy_card(center_tile, white, (212, 207, 194))
    sh.text("mangosboard_center_specimen", ctx["display"], clean(ctx, "Form"),
            Box(center_tile.x+center_tile.w*.035,
                center_tile.y+center_tile.h*.08,
                center_tile.w*.93, center_tile.h*.82),
            hi=212*sh.scale, lo=54*sh.scale, max_lines=1,
            color=orange, min_read=38*sh.scale, track=-.035,
            align="center", valign="middle")

    glossy_card(right_tile, orange, white)
    symbol = "@" if usable(ctx, "@") else "A"
    sh.text("mangosboard_symbol", ctx["display"], symbol,
            Box(right_tile.x+right_tile.w*.07, right_tile.y+right_tile.h*.08,
                right_tile.w*.86, right_tile.h*.82),
            hi=235*sh.scale, lo=58*sh.scale, max_lines=1,
            color=black, min_read=42*sh.scale, track=-.04)


@support("anatomy32", "the designer's bench: one glyph enlarged with cap, x-height and baseline rules, stem calipers, overshoot circles and measured construction marks")
def t_anatomy32(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    bg(sh, P, ctx["th"], dev=False, pool=0.08, tooth=1)
    ch = next((c for c in shout(ctx, ctx["name"]) if usable(ctx, c)), "A")
    size = fit_measure(T, ch, sh.w * 0.48, sh.h * 0.62)
    p, _ = T.path(ch, size)
    b = p.getBounds()
    p.offset(sh.w * 0.52 - (b.left() + b.right()) / 2,
             sh.h * 0.52 - (b.top() + b.bottom()) / 2)
    b = p.getBounds()
    ink, mute, _ = field(P)
    g = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) or lum(P["paper1"])
    ruleink = readable(g, mix(ink, P["accent"], 0.35), 3.5)
    q = paint(C(ruleink, 0.62), style=skia.Paint.kStroke_Style, width=max(1.5, 2.0 * sh.scale))
    for y in (b.top(), b.bottom(), b.top() + b.height() * 0.34):
        sh.cv.drawLine(sh.m, y, sh.w - sh.m, y, q)
    sh.cv.drawPath(p, paint(C(readable(g, ink, 5.0), 0.18), style=skia.Paint.kStroke_Style,
                            width=max(2.0, 3.0 * sh.scale)))
    sh.cv.drawPath(p, paint(C(readable(g, ink, 5.0), 0.12)))
    # Stem-width caliper and overshoot circles make this a measurement image,
    # not another decorated wordmark.
    cx = b.left() + b.width() * 0.20
    sh.cv.drawLine(cx, b.top() - 40 * sh.scale, cx, b.bottom() + 40 * sh.scale, q)
    sh.cv.drawLine(cx - 30 * sh.scale, b.top() - 40 * sh.scale,
                   cx + 30 * sh.scale, b.top() - 40 * sh.scale, q)
    sh.cv.drawLine(cx - 30 * sh.scale, b.bottom() + 40 * sh.scale,
                   cx + 30 * sh.scale, b.bottom() + 40 * sh.scale, q)
    circ = paint(C(P["accent"], 0.72), style=skia.Paint.kStroke_Style,
                 width=max(1.5, 2.0 * sh.scale))
    r = min(b.width(), b.height()) * 0.16
    sh.cv.drawCircle(b.left() + b.width() * 0.72, b.top() + b.height() * 0.30, r, circ)
    sh.cv.drawCircle(b.left() + b.width() * 0.72, b.bottom() - b.height() * 0.12, r * 0.7, circ)
    sh.mark("glyph", Box(b.left(), b.top(), b.width(), b.height()), collide=False)
    label = Box(sh.m, sh.h - 0.14 * sh.h, sh.w - 2 * sh.m, 0.09 * sh.h)
    sh.text("anatomy-label", L, tc(f"{ch} / cap line / x-height / baseline / overshoot"), label,
            hi=28 * sh.scale, lo=17 * sh.scale, color=readable(g, mute, 6.0),
            track=0.12, align="left", valign="top", min_read=16 * sh.scale)


@support("riso32", "the two-colour misregistration: one phrase printed twice in offset riso inks over a toothy paper field with a sparse halftone screen")
def t_riso32(sh, ctx):
    P, T = ctx["pal"], ctx["display"]
    bg(sh, P, ctx["th"], dev=False, pool=0.11, tooth=2)
    word = _support_word(ctx, "Printed")
    # Long authored sentences belong in the other panels; this print-study
    # needs one compact lockup so the registration remains a material detail.
    word = clean(ctx, word.split()[0] if word.split() else "Ink") or "Ink"
    word = clean(ctx, word) or "Ink"
    s = fit_measure(T, word, sh.w * 0.80, 500 * sh.scale)
    p, _ = T.path(word, s); b = p.getBounds()
    p.offset(sh.w * .50 - (b.left() + b.right()) / 2, sh.h * .48 - (b.top() + b.bottom()) / 2)
    b = p.getBounds()
    g = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) or lum(P["paper1"])
    c1 = readable(g, P["accent"], 4.5); c2 = readable(g, P["deep1"], 4.5)
    for dx, dy, col in ((-8 * sh.scale, 3 * sh.scale, c1), (8 * sh.scale, -3 * sh.scale, c2)):
        sh.cv.save(); sh.cv.translate(dx, dy); sh.cv.drawPath(p, paint(C(col, 0.78))); sh.cv.restore()
    dots = paint(C(readable(g, mix(c1, c2, .5), 3.0), 0.20))
    step = max(20, int(28 * sh.scale))
    for y in range(int(sh.m), int(sh.h - sh.m), step * 3):
        for x in range(int(sh.m), int(sh.w - sh.m), step * 3):
            sh.cv.drawCircle(x + ((y // step) % 2) * step, y, 2.2 * sh.scale, dots)
    sh.mark("riso-word", Box(b.left() - 12 * sh.scale, b.top() - 8 * sh.scale,
                             b.width() + 24 * sh.scale, b.height() + 16 * sh.scale), collide=False)


@support("shear32", "the kinetic slice: a display word cut into horizontal bands, each displaced progressively with a compact smear trail")
def t_shear32(sh, ctx):
    P, T = ctx["pal"], ctx["display"]
    bg(sh, P, ctx["th"], dev=False, pool=0.09, tooth=1)
    word = _support_word(ctx, "Move Fast")
    word = " ".join(word.split()[:2])
    word = clean(ctx, word) or "Move"
    s = fit_measure(T, word, sh.w * .78, 520 * sh.scale)
    p, _ = T.path(word, s); b = p.getBounds()
    p.offset(sh.w*.50-(b.left()+b.right())/2, sh.h*.49-(b.top()+b.bottom())/2); b=p.getBounds()
    g = sh._behind(Box(sh.m, sh.m, sh.w-2*sh.m, sh.h-2*sh.m)) or lum(P["paper1"])
    ink = readable(g, P["ink"], 5.0); accent = readable(g, P["accent"], 4.5)
    bands = 12; bh = b.height() / bands
    for i in range(bands):
        y0 = b.top() + i * bh
        dx = (i - bands/2) * 3.3 * sh.scale
        sh.cv.save(); sh.cv.clipRect(skia.Rect.MakeXYWH(0, y0, sh.w, bh + 1), skia.ClipOp.kIntersect, True)
        sh.cv.translate(dx, (i % 3 - 1) * 1.5 * sh.scale)
        sh.cv.drawPath(p, paint(C(accent if i % 4 == 0 else ink, 0.88)))
        sh.cv.restore()
        if i % 3 == 0:
            sh.cv.save(); sh.cv.clipRect(skia.Rect.MakeXYWH(0, y0, sh.w, bh + 1), skia.ClipOp.kIntersect, True)
            sh.cv.translate(dx - 20 * sh.scale, 0); sh.cv.drawPath(p, paint(C(accent, .14))); sh.cv.restore()
    sh.mark("shear-word", Box(b.left()-40*sh.scale, b.top(), b.width()+80*sh.scale, b.height()), collide=False)


@support("mosaic32", "the character-set wallpaper: usable glyphs, figures, punctuation and symbols tiled in an irregular rhythm rather than a specimen table")
def t_mosaic32(sh, ctx):
    P, T = ctx["pal"], ctx["display"]
    bg(sh, P, ctx["th"], dev=False, pool=.08, tooth=1)
    g = sh._behind(Box(sh.m, sh.m, sh.w-2*sh.m, sh.h-2*sh.m)) or lum(P["paper1"])
    ink = readable(g, P["ink"], 4.5); accent = readable(g, P["accent"], 4.5)
    chars = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&?!@#$%+-=/()[]{}" if usable(ctx, c)]
    if not chars: chars = [c for c in ctx["name"] if usable(ctx, c)] or ["A"]
    seed = int(hashlib.sha256(ctx["name"].encode()).hexdigest()[:8], 16); rnd = random.Random(seed)
    for row in range(4):
        for col in range(7):
            ch = chars[(row*7 + col + seed) % len(chars)]
            size = rnd.uniform(.18, .34) * sh.h
            x = sh.m + (col + .5) * (sh.w - 2*sh.m) / 7 + rnd.uniform(-.10, .10) * sh.w
            y = sh.m + (row + .8) * (sh.h - 2*sh.m) / 4 + rnd.uniform(-.06, .06) * sh.h
            p, _ = T.path(ch, size); b = p.getBounds(); p.offset(x-(b.left()+b.right())/2, y-(b.top()+b.bottom())/2)
            sh.cv.drawPath(p, paint(C(accent if (row+col)%5==0 else ink, .66)))
    sh.mark("mosaic", Box(sh.m, sh.m, sh.w-2*sh.m, sh.h-2*sh.m), collide=False, bleed=True)


@support("stencil32", "the spray stencil: a large word on a grained wall with bridge cuts, overspray, a cast offset and two deliberate drips")
def t_stencil32(sh, ctx):
    P, T = ctx["pal"], ctx["display"]
    bg(sh, P, ctx["th"], dev=False, pool=.14, tooth=3)
    word = _support_word(ctx, "Make Noise"); word = clean(ctx, word) or "Type"
    s = fit_measure(T, word, sh.w*.78, 520*sh.scale); p, _ = T.path(word, s); b=p.getBounds()
    p.offset(sh.w*.50-(b.left()+b.right())/2, sh.h*.49-(b.top()+b.bottom())/2); b=p.getBounds()
    g = sh._behind(Box(sh.m, sh.m, sh.w-2*sh.m, sh.h-2*sh.m)) or lum(P["paper1"])
    ink = readable(g, P["accent"], 5.0); shadow = readable(g, P["deep1"], 4.5)
    sh.cv.save(); sh.cv.translate(18*sh.scale, 22*sh.scale); sh.cv.drawPath(p, paint(C(shadow, .45))); sh.cv.restore()
    sh.cv.drawPath(p, paint(C(ink, .88)))
    # Sparse overspray and drips, deterministic and cheap.
    rnd = random.Random(int(hashlib.sha256((ctx["name"]+word).encode()).hexdigest()[:8],16))
    spray = paint(C(ink, .22))
    for _ in range(90):
        x = b.left()+rnd.random()*b.width(); y=b.top()+rnd.random()*b.height()
        sh.cv.drawCircle(x, y, rnd.uniform(1.0, 4.0)*sh.scale, spray)
    for x in (b.left()+b.width()*.30, b.left()+b.width()*.72):
        sh.cv.drawLine(x, b.bottom(), x, b.bottom()+rnd.uniform(30,80)*sh.scale, paint(C(ink,.55), width=3*sh.scale))
    sh.mark("stencil", Box(b.left()-20*sh.scale, b.top()-20*sh.scale, b.width()+60*sh.scale, b.height()+100*sh.scale), collide=False)
def _tex_img(rgba):
    """(n, n, 4) unpremultiplied uint8 -> an immutable skia.Image to repeat."""
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    px = np.dstack([(rgba[:, :, :3] * a).round().astype(np.uint8), rgba[:, :, 3]])
    return skia.Image.fromarray(np.ascontiguousarray(px),
                                colorType=skia.ColorType.kRGBA_8888_ColorType,
                                alphaType=skia.AlphaType.kPremul_AlphaType, copy=True)

def _tex_tile(kind, a, b, c, seed):
    """One repeatable texture cell, built once per (kind, params) and cached.

    A screen and a mesh are generated at a whole number of periods per tile, so they
    are seamless by construction; the grain is white noise, which repeats without a
    seam because nothing in it is correlated with anything else. `c` is the angle in
    degrees, snapped to the axis by the caller — see `halftone()`.
    """
    key = (kind, round(a, 2), round(b, 3), round(c, 1), seed)
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]
    rng = np.random.default_rng(seed)
    out = None
    if kind == "grain":
        n = max(16, int(a))
        amp = (rng.random((n, n)) * 2.0 - 1.0) * max(0.0, min(1.0, c)) * 255.0
        out = (_tex_img(np.dstack([np.full((n, n, 3), 255, np.uint8),
                                   np.clip(amp, 0, 255).astype(np.uint8)])),
               _tex_img(np.dstack([np.zeros((n, n, 3), np.uint8),
                                   np.clip(-amp, 0, 255).astype(np.uint8)])))
    elif kind == "grille":
        step = max(2.0, round(a))
        thick = min(max(0.8, b * step), step - 0.8)
        n = int(step) * 8
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        d = np.abs(((yy if c < 45 else xx) % step) - step / 2.0)
        alpha = np.clip(step / 2.0 + 0.6 - d, 0, 1)
        out = _tex_img(np.dstack([np.zeros((n, n, 3), np.uint8),
                                  (alpha * 255).astype(np.uint8)]))
    elif kind == "dot":
        step = max(3.0, round(a))
        rfrac = min(max(0.10, b), 0.46)
        n = int(step) * 8
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        u, v = (xx, yy) if c < 45 else (xx * 0.7071 + yy * 0.7071,
                                        -xx * 0.7071 + yy * 0.7071)
        row = np.floor(v / step).astype(np.int32)
        du = u / step - np.round(u / step)
        off = 0.5 * (row % 2)
        dv = v / step - off - np.round(v / step - off)
        d = np.sqrt(du * du + dv * dv) * step
        alpha = np.clip(rfrac * step - d, 0, 1)
        out = _tex_img(np.dstack([np.zeros((n, n, 3), np.uint8),
                                  (alpha * 255).astype(np.uint8)]))
    _TEX_CACHE[key] = out
    return out

def _tex_repeat(cv, box, img, alpha, seed=0, mode=skia.BlendMode.kSrcOver, scale=1.0):
    """Repeat one cached cell across `box`, phase-offset by `seed`.

    Nearest sampling on purpose: a filtered repeat invents a new value at every
    pixel boundary and pays the per-pixel price this whole section is trying to
    avoid, while a block-true repeat keeps the cell count at the cell count.
    """
    if img is None or box is None or box.w < 4 or box.h < 4 or alpha <= 0.004:
        return
    n = img.width() * scale
    p = skia.Paint(AntiAlias=False)
    p.setAlpha(int(round(max(0.0, min(1.0, alpha)) * 255)))
    p.setBlendMode(mode)
    m = skia.Matrix()
    m.preScale(scale, scale)
    m.preTranslate((seed % 977) / 977.0 * n, ((seed * 5) % 977) / 977.0 * n)
    p.setShader(img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                               skia.SamplingOptions(), m))
    cv.drawRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h), p)

def _tex_field(cv, box, kind, strength, seed, cell=600):
    """A smooth large-scale field, invented at 1/BG_SCALE and grown back.

    This is the difference between +6.6 KB and +336 KB for the same mottling: a
    continuous ramp is one ramp whatever resolution it is computed at, so it is
    computed where it is cheap and given to the sheet bilinear, exactly as `bg()`
    gives it its gradient.
    """
    if box is None or strength <= 0.004:
        return
    w = max(8, int(box.w) // BG_SCALE)
    h = max(8, int(box.h) // BG_SCALE)
    sub = skia.Surface.MakeRasterN32Premul(w, h)
    if sub is None:
        return
    cv2 = sub.getCanvas()
    if kind == "mottle":
        f = 1.0 / max(24.0, cell / BG_SCALE)
        sh_ = skia.PerlinNoiseShader.MakeFractalNoise(f, f, 2, seed, skia.ISize(w, h))
        q = skia.Paint(AntiAlias=False)
        q.setColor4f(skia.Color4f(0.07, 0.075, 0.09, max(0.0, min(1.0, strength))))
        q.setShader(sh_)
        q.setBlendMode(skia.BlendMode.kMultiply)
        cv2.drawRect(skia.Rect.MakeWH(w, h), q)
    else:
        g = skia.GradientShader.MakeRadial(
            skia.Point(w * 0.5, h * 0.5), max(w, h) * 0.62,
            [skia.Color4f(0, 0, 0, 0.0), skia.Color4f(0, 0, 0, strength)])
        q = skia.Paint(AntiAlias=False)
        q.setShader(g)
        q.setBlendMode(skia.BlendMode.kMultiply)
        cv2.drawRect(skia.Rect.MakeWH(w, h), q)
    cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(w, h),
                     skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                     skia.SamplingOptions(skia.FilterMode.kLinear,
                                          skia.MipmapMode.kNone))

def grain(cv, box, amount, seed, cell=96, magnify=6, tint=None):
    """Fine paper tooth, mean-zero: pale flecks and dark flecks in equal measure.

    `amount` is the top of the alpha ramp, not the visible contrast: 0.12 lands
    about fifteen levels off the ground at the extremes, which is what tooth reads
    as at feed size. Symmetric on purpose — a line of type measured against this
    ground afterwards sees the same median it saw before, so no ink gets lifted.

    `magnify` is the lever that decides the bill, because a PNG charges per
    independent cell: one value per pixel is +286 KB over a flat field, 6 px blocks
    are +44 KB on a real ground, and a band of the same tooth is affordable. Use it
    on a band, a corner or a card. Full-sheet film grain is the treatment in this
    catalogue that cannot be made both cheap and good, and that is its report.
    """
    if box is None or box.w < 8 or box.h < 8 or amount <= 0.004:
        return
    pale, dark = _tex_tile("grain", cell, 0, max(0.0, min(1.0, amount)) * 0.5, seed)
    for img, mode in ((dark, skia.BlendMode.kMultiply), (pale, skia.BlendMode.kScreen)):
        _tex_repeat(cv, box, img, amount, seed=seed, mode=mode,
                    scale=max(1, int(magnify)))

def noise_wash(cv, box, strength=0.10, seed=7, cell=560, tint=None):
    """Large-scale uneven ink: a damp patch, a roller that ran short, a cloudy wash.

    Two octaves of fractal noise, multiplied down, invented at quarter resolution
    (`_tex_field`) so the sheet pays for one ramp rather than for 3.8M samples.
    +6.6 KB over a whole ground at 0.14 — and the same field computed at full
    resolution, which looks the same, is +336 KB.
    """
    _tex_field(cv, box, "mottle", strength, seed, cell=cell)

def vignette(cv, box, strength, spread=0.62, cx=0.5, cy=0.5):
    """Corner falloff that pulls the eye back to the middle of the sheet.

    Painted at 1/BG_SCALE and grown, the way `bg()` paints its gradient. It is
    still the second most expensive thing on this menu (+15.5 KB at 0.05 over a
    2400x1600 ground), so the pack buys it last and keeps it under 0.06 — a
    falloff loud enough to be read as a mood is a falloff that costs a cap.
    """
    if box is None or strength <= 0.004:
        return
    w = max(8, int(box.w) // BG_SCALE)
    h = max(8, int(box.h) // BG_SCALE)
    sub = skia.Surface.MakeRasterN32Premul(w, h)
    if sub is None:
        return
    g = skia.GradientShader.MakeRadial(
        skia.Point(w * cx, h * cy), max(w, h) * spread,
        [skia.Color4f(0, 0, 0, 0.0), skia.Color4f(0, 0, 0, strength)])
    q = skia.Paint(AntiAlias=False)
    q.setShader(g)
    q.setBlendMode(skia.BlendMode.kMultiply)
    sub.getCanvas().drawRect(skia.Rect.MakeWH(w, h), q)
    cv.drawImageRect(sub.makeImageSnapshot(), skia.Rect.MakeWH(w, h),
                     skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                     skia.SamplingOptions(skia.FilterMode.kLinear,
                                          skia.MipmapMode.kNone))

def halftone(cv, box, step=12.0, alpha=0.30, angle=0.0, cell="grille", seed=3):
    """The screen itself: a line grille or a dot mesh, at a chosen pitch and angle.

    This is the workhouse, because it is the move that reads loudly and costs
    nothing — and, at a coarse enough pitch, reads loudly and *pays*: a 12 px grille
    at 0.40 took 0.8 KB off the chrome ground it was tested on, because quantising a
    smooth gradient into bands gives the row filter something to predict that it did
    not have before. A 5 px screen is +14 KB, so the coarse end of the mesh is where
    the value is.

    Rotation is the trap: the same dots at 45 degrees cost +181 KB against +31 KB
    unrotated, because no row predicts the next. `angle` is therefore snapped to the
    axis, and a laid-paper diagonal is asked for as a vertical screen.
    """
    if box is None or box.w < 4 or box.h < 4 or alpha <= 0.004:
        return
    q = round(angle / 90.0) * 90.0 % 180.0
    img = _tex_tile(cell, max(2.0, step), 0.42 if cell == "dot" else 0.44, q, seed)
    _tex_repeat(cv, box, img, alpha, seed=seed + int(q // 90),
                mode=skia.BlendMode.kMultiply)

def scratch(cv, box, n, seed, alpha=0.38, length=(0.02, 0.17), weight=1.0, dust=0.24):
    """Sparse wear: hairline scuffs, a fibre, the fleck that bit the plate.

    Paid per mark at about +1.3 KB — an antialiased diagonal is continuous tone with
    no neighbour to help it — so this buys the most *look* per byte at low counts
    and stops being affordable by the hundred. Also mean-zero: most marks are dark
    and a quarter are pale, so the ground a line of type is measured against does
    not slide.
    """
    if box is None or box.w < 8 or n <= 0:
        return
    rng = random.Random(seed)
    short = min(box.w, box.h)
    pale, dark = skia.Path(), skia.Path()
    for i in range(int(n)):
        x = box.x + rng.uniform(0.0, box.w)
        y = box.y + rng.uniform(0.0, box.h)
        L = rng.uniform(*length) * short
        a = rng.uniform(-0.42, 0.42) if i % 2 else rng.uniform(1.15, 1.99)
        dx, dy = math.cos(a) * L, math.sin(a) * L
        bow = rng.uniform(-0.06, 0.06) * L
        path = pale if rng.random() < dust else dark
        path.moveTo(x, y)
        path.quadTo(x + dx * 0.5 + bow, y + dy * 0.5 - bow, x + dx, y + dy)
        if rng.random() < 0.16:
            path.addCircle(x + dx, y + dy, rng.uniform(0.5, 2.2) * weight)
    q = skia.Paint(AntiAlias=True)
    q.setStyle(skia.Paint.kStroke_Style)
    q.setStrokeCap(skia.Paint.kRound_Cap)
    q.setStrokeWidth(weight)
    q.setColor4f(skia.Color4f(0, 0, 0, alpha))
    cv.drawPath(dark, q)
    q.setColor4f(skia.Color4f(1, 1, 1, alpha))
    cv.drawPath(pale, q)

def _tex_rect(sh, box):
    return skia.IRect(int(box.x), int(box.y), int(min(sh.w, box.x + box.w)),
                      int(min(sh.h, box.y + box.h)))

def _tex_encode(sh, box):
    """Bytes this sheet would ship as, measured on the pixels that are on it now."""
    img = sh.surf.makeImageSnapshot().makeSubset(_tex_rect(sh, box))
    return img.encodeToData().size() if img is not None else 0

def _tex_restore(cv, box, img):
    """Put the pixels back: a rejected layer must not survive the roll-back."""
    if img is not None:
        cv.drawImage(img, _tex_rect(None, box).x() if False else int(box.x),
                     int(box.y), skia.SamplingOptions(),
                     skia.Paint(BlendMode=skia.BlendMode.kSrc, AntiAlias=False))

def _tex_layer(sh, box, name, kw, strength, seed):
    """Draw one named texture layer, so the pack and its caller share one path."""
    if name == "grille" or name == "dot":
        halftone(sh.cv, box, step=kw["step"], alpha=kw["alpha"] * strength,
                 angle=kw.get("angle", 0.0), cell=name, seed=seed)
    elif name == "wash":
        noise_wash(sh.cv, box, strength=kw["strength"] * strength, seed=seed,
                   cell=kw.get("cell", 560))
    elif name == "vig":
        vignette(sh.cv, box, kw["strength"] * strength)
    elif name == "wear":
        scratch(sh.cv, box, kw["n"], seed, alpha=kw.get("alpha", 0.38) * strength,
                length=kw.get("length", (0.02, 0.17)))
    elif name == "grain":
        grain(sh.cv, box, kw["amount"] * strength, seed, cell=kw.get("cell", 96),
              magnify=kw.get("magnify", 6))

def _tex_plan(kind, s, sh):
    """What one kind of ground is made of, in the order it is bought.

    Ordered by look per byte, because the budget is spent once: the coarse screen
    that costs nothing goes first and is on every panel, then the marks that read
    as wear, and only then the damp and the falloff, which are the items that can
    price themselves out. The tooth in `worn` and `sieve` is a coarse one, on a
    band rather than a whole sheet, for the reason given at the head of this
    section.
    """
    return {
        "press": [("grille", dict(step=13.0 * s, alpha=0.34, angle=0.0)),
                  ("wear", dict(n=7)),
                  ("wash", dict(strength=0.12)),
                  ("grille", dict(step=5.0 * s, alpha=0.12, angle=90.0)),
                  ("vig", dict(strength=0.05))],
        "laid": [("grille", dict(step=11.0 * s, alpha=0.30, angle=90.0)),
                 ("wear", dict(n=7)),
                 ("wash", dict(strength=0.10, cell=760)),
                 ("grille", dict(step=4.5 * s, alpha=0.10, angle=0.0)),
                 ("vig", dict(strength=0.05))],
        "raster": [("grille", dict(step=15.0 * s, alpha=0.28, angle=0.0)),
                   ("dot", dict(step=26.0 * s, alpha=0.16)),
                   ("wear", dict(n=5)),
                   ("wash", dict(strength=0.10)),
                   ("vig", dict(strength=0.05))],
        "worn": [("grille", dict(step=12.0 * s, alpha=0.26, angle=90.0)),
                 ("wear", dict(n=13)),
                 ("grain", dict(amount=0.14, magnify=7, cell=64)),
                 ("wash", dict(strength=0.10, cell=820)),
                 ("wear", dict(n=6, alpha=0.30, length=(0.05, 0.30)))],
        "damp": [("grille", dict(step=14.0 * s, alpha=0.24, angle=0.0)),
                 ("wash", dict(strength=0.18, cell=520)),
                 ("wear", dict(n=6)),
                 ("wash", dict(strength=0.10, cell=900)),
                 ("vig", dict(strength=0.05))],
        "sieve": [("grille", dict(step=10.0 * s, alpha=0.26, angle=0.0)),
                  ("dot", dict(step=22.0 * s, alpha=0.14, angle=90.0)),
                  ("wear", dict(n=6)),
                  ("grain", dict(amount=0.12, magnify=8, cell=64)),
                  ("vig", dict(strength=0.05))],
    }[kind]

def _tex_seed(th):
    """The seed a theme textures with: its own, folded with its palette's."""
    return (int(th.get("seed", 0) or 0) * 131 +
            sum(ord(c) * (i + 3) for i, c in
                enumerate(str(th.get("pal", "")) + str(th.get("device", "")))) % 4093)

def _tex_kind(th):
    """Which ground a theme wears, decided by the theme — never by the clock.

    Keyed on the world's own seed, palette and device, so two faces that roll the
    same world print the same way (that is what makes a world recognisable) and one
    face's panels do not all wear the same mesh.
    """
    rot = int(hashlib.sha256(
        f"{th.get('pal', '')}|{th.get('device', '')}|{th.get('art', '')}".encode()
    ).hexdigest(), 16)
    return TEXTURE_KINDS[(rot + int(th.get("seed", 0) or 0)) % len(TEXTURE_KINDS)]

def texture_pack(sh, P, kind=None, strength=1.0, seed=0, box=None,
                 allow=TEXTURE_ALLOW_BYTES):
    """One call that stops a ground being flat, and stops when it has spent its bytes.

    Every layer is tried in price order and billed for real: the sheet is encoded
    before the layer and after it, and the layer is kept only while the ground can
    still pay `allow` for the whole pack — if it cannot, the pixels it touched are
    put back with a `kSrc` redraw of the snapshot and the next, cheaper idea is
    tried. There is no price table because a table would be wrong: the same dot mesh
    costs 2 KB over a flat fill and 150 KB over a ground that already wears a device,
    and this function only ever sees the ground that is actually there.

    `strength` scales the visibility and the allowance together, so a caller that
    asks for 0.4 gets a whisper and not a whisper that costs full price. The first
    layer of every kind is the coarse screen, which measured *negative* bytes, so no
    panel can end up back where it started.
    """
    if strength <= 0.0 or getattr(sh, "_tex", None):
        return None
    box = box or Box(0.0, 0.0, float(sh.w), float(sh.h))
    kind = kind if kind in TEXTURE_KINDS else "press"
    allow = max(1500.0, allow * min(1.0, max(0.2, strength)))
    now = _tex_encode(sh, box)
    spent, done = 0, []
    for name, kw in _tex_plan(kind, sh.scale, sh):
        if spent >= allow:
            break
        keep = sh.surf.makeImageSnapshot().makeSubset(_tex_rect(sh, box))
        _tex_layer(sh, box, name, kw, strength, seed)
        cost = _tex_encode(sh, box)
        if cost - now > allow - spent:
            _tex_restore(sh.cv, box, keep)
            continue
        spent += cost - now
        now = cost
        done.append(name)
    if not done:                        # a coarse screen is never a net cost, and a
        _tex_layer(sh, box, "grille",   # flat ground is the one failure here
                   dict(step=13.0 * sh.scale, alpha=0.30), strength, seed)
        done.append("grille")
    sh._tex = (kind, tuple(done), int(spent))
    return done

def aged_ground(sh, ctx, kind=None, strength=TEXTURE_STRENGTH, box=None,
                allow=TEXTURE_ALLOW_BYTES):
    """The panel's one call: its theme's own ground texture, at its theme's own seed.

    `kind` comes from the theme unless the panel asks for one, and the seed is the
    theme's, so re-rendering the same brief gives back the same pixels to the level.
    Ink is never surprised by any of this: it is painted after, every layer here is
    mean-zero or a fraction of a percent of the ground's own range, and the pack has
    already paid for itself out of the texture allowance rather than out of the
    contrast the lettering stands on.
    """
    P, th = ctx["pal"], ctx["th"]
    if getattr(sh, "_tex", None):
        return None
    return texture_pack(sh, P, kind or _tex_kind(th), strength=strength,
                        seed=_tex_seed(th), box=box, allow=allow)




def _deboss_word(sh, ctx, T):
    """The one word the press goes down on, and never the font's own name.

    A blind-debossed sheet is a piece of thick paper with a single word in it,
    and every other panel in the catalogue already spends its space on the
    name. The brief's `word` is tried first, then any single word off the
    phrase, then the phrase itself if it is short enough to still be huge.
    """
    cand = [clean(ctx, ctx["copy"].get("word") or "").strip()]
    line = clean(ctx, ctx["copy"].get("line") or "").strip()
    cand += line.split() if len(line.split()) <= 2 else []
    cand.append(line if len(line.split()) <= 3 else "")
    for c in cand:
        c = shout(ctx, c).strip()
        if not c or any(not usable(ctx, ch) for ch in c if not ch.isspace()):
            continue
        if _nm_free(ctx, c):
            return c
    return ""

@support("deboss32", "the blind impression: one word pressed into thick cotton paper with no ink anywhere — the bite reads off a raking highlight on its upper lip and a shadow thrown down its far wall")
def t_deboss32(sh, ctx):
    """The face proved by light instead of colour.

    Every other panel puts ink on a ground. This one takes the ground — thick
    cotton stock, real tooth — and pushes a letter into it. What makes a blind
    deboss legible is not the shape of the bite but the way a single raking
    light falls across it: the wall the light reaches becomes a lip of pale
    fibre, the wall behind it becomes a shadow, and the floor of the bite goes
    a shade darker than the sheet around it. Three draws do all of that, and
    none of them is a fill of the letter: a pale blurred copy of the path
    offset up-light and clipped to everything *outside* the letter, a dark
    blurred copy offset down-shadow and clipped to everything *inside* it, and
    a hair of overall darkening on the floor so the counters do not read as
    printed. There is no ink on this sheet, which is the whole point a buyer
    of a display face wants proved: the drawing holds up with the colour turned
    off.
    """
    P, T = ctx["pal"], ctx["display"]
    # The paper should feel tactile, but the deboss itself is the focal
    # texture. A restrained tooth keeps the large field compressible so the
    # supporting image remains deliverable on script and heavy faces too.
    bg(sh, P, ctx["th"], dev=False, pool=0.10, tooth=1, tex=False)
    gnd = sh._behind(Box(sh.m, sh.m, sh.w - 2 * sh.m, sh.h - 2 * sh.m)) \
        or lum(P["paper1"])
    hi = readable(gnd, mix(P["paper1"], (255, 255, 255), 0.55), 1.30) \
        if gnd > 0.42 else mix(P["glow"], (255, 255, 255), 0.55)
    lo = readable(gnd, mix(P["deep1"], (0, 0, 0), 0.25), 1.30) \
        if gnd > 0.42 else mix(P["deep1"], (0, 0, 0), 0.35)

    word = _deboss_word(sh, ctx, T)
    if not word:
        sh.problems.append("deboss32: the brief left no word the face can press")
        return
    words = word.split()
    lines = pack_lines(words, min(2, len(words)))
    stage = Box(sh.m * 1.15, sh.m * 1.05, sh.w - 2.3 * sh.m, sh.h - 2.1 * sh.m)
    sizes = [fit_measure(T, ln, stage.w, 900 * sh.scale) for ln in lines]
    boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
    lead = int(max(18 * sh.vscale, 0.06 * max(sizes)))
    total = sum(b.height() for b in boxes) + lead * (len(lines) - 1)
    if total > stage.h:
        k = stage.h / total
        sizes = [s * k for s in sizes]
        boxes = [T.path(ln, s)[0].getBounds() for ln, s in zip(lines, sizes)]
        lead = int(lead * k)
        total = sum(b.height() for b in boxes) + lead * (len(lines) - 1)
    path = skia.Path()
    y = stage.y + (stage.h - total) / 2.0
    for ln, s, b in zip(lines, sizes, boxes):
        p, _adv = T.path(ln, s)
        p.offset(stage.x + (stage.w - b.width()) / 2 - b.x(), y - b.y())
        path.addPath(p, skia.Matrix())
        y += b.height() + lead
    if path.isEmpty():
        sh.problems.append("deboss32: the word drew no outline")
        return
    pb = path.getBounds()
    sh.mark("bite", Box(pb.x(), pb.y(), pb.width(), pb.height()), collide=False)

    # The bite is scaled to the letter, not to the sheet: a deboss is cut by a
    # die, and the deeper the stroke the wider the wall it leaves. The stem
    # width is the only honest measure of that, so a hairline didone gets a
    # razor lip and a slab gets a soft one.
    stem = ctx["facts"].get("stem") or 0.06
    reach = pb.height() * min(max(0.020 + 0.10 * stem, 0.026), 0.062)
    off = reach * 0.85
    # A broad full-resolution blur produces expensive alpha ramps without
    # adding useful structure to the impression. Keep the lip crisp enough to
    # read while staying within the support PNG budget.
    sig = max(0.75, reach * 0.20)

    # 1. the lip: pale fibre on the side the light comes from, and only there
    # — clipped to everything the letter is not, so it never fills the bite.
    sh.cv.save()
    sh.cv.clipPath(path, skia.ClipOp.kDifference, True)
    q = paint(C(hi, 0.32), blur=sig)
    sh.cv.save()
    sh.cv.translate(-off, -off)
    sh.cv.drawPath(path, q)
    sh.cv.restore()
    sh.cv.restore()

    # 2. the far wall: the shadow the letter throws down itself, clipped to
    # inside the outline, which is what leaves the near wall bright.
    sh.cv.save()
    sh.cv.clipPath(path, skia.ClipOp.kIntersect, True)
    q = paint(C(lo, 0.40), blur=sig)
    sh.cv.save()
    sh.cv.translate(off, off)
    sh.cv.drawPath(path, q)
    sh.cv.restore()
    # 3. the floor, a shade down on the sheet around it — without this the
    # counters read as printed rather than pressed.
    sh.cv.drawPath(path, paint(C(lo, 0.10)))
    sh.cv.restore()




def _cloud_lobe(cx, cy, rx, ry, rnd, n=9, wob=0.14):
    """One lobe of the cloud: an ellipse whose radius wanders point to point,
    smoothed through the same Catmull-Rom to beziers `_wash_stroke` uses, so it
    closes as one soft wet shape instead of a polygon."""
    pts = [(cx + math.cos(2 * math.pi * i / n) * rx
            * (1.0 + rnd.uniform(-wob, wob)),
            cy + math.sin(2 * math.pi * i / n) * ry
            * (1.0 + rnd.uniform(-wob, wob)))
           for i in range(n)]
    p = skia.Path()
    p.moveTo(*pts[0])
    m = len(pts)
    for i in range(m):
        p1, p2 = pts[i], pts[(i + 1) % m]
        p0, p3 = pts[i - 1], pts[(i + 2) % m]
        p.cubicTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                  p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
    p.close()
    return p



# ---------------------------------------------------------------- alternate pin compositions

def _pin_variant_card(sh, box, fill, edge, radius=22.0, alpha=1.0):
    rect = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
    sh.cv.drawRoundRect(rect, radius * sh.scale, radius * sh.scale,
                        paint(C(fill, alpha)))
    sh.cv.drawRoundRect(rect, radius * sh.scale, radius * sh.scale,
                        paint(C(edge, 0.72), style=skia.Paint.kStroke_Style,
                              width=max(1.2, 1.5 * sh.scale)))
    sh.mark("panel", box, collide=False)


@template("studio_cover", "an editorial cover with a large title, a colored statement band, and three character studies")
def t_studio_cover(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    bg(sh, P, ctx["th"], pool=0.09)
    ink, mute, dark = field(P)
    y = eyebrow(sh, ctx, "Type Foundry · Vol. 01") + 34
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    lines = pack_lines(name.split(), 2)
    measure_rows(sh, T, P, lines, Box(M, y, W - 2 * M, 340), "cover-name",
                 hi=245, min_read=36, fill=True, lead_frac=0.035, centre=True)

    band = Box(M + 12, 585, W - 2 * (M + 12), 258)
    _pin_variant_card(sh, band, rung(P, 1), P["accent"], 26)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "Letters With A Point Of View"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 2),
                 Box(band.x + 34, band.y + 24, band.w - 68, band.h - 48),
                 "cover-line", hi=142, min_read=32, fill=True, centre=True,
                 lead_frac=0.02)

    samples = (("Aa", "Upper And Lower"), ("Bb", "Open Shapes"),
               ("Cc", "Character Study"))
    gap = 18 * sh.scale
    cell_w = (W - 2 * M - 2 * gap) / 3
    y0 = 900
    for i, (glyph, caption) in enumerate(samples):
        box = Box(M + i * (cell_w + gap), y0, cell_w, 265)
        _pin_variant_card(sh, box, P["deep2"] if dark else P["paper2"],
                          rung(P, i + 1), 18)
        sh.text(f"cover-glyph-{i}", T, glyph,
                Box(box.x + 10, box.y + 28, box.w - 20, 138), hi=126, lo=54,
                min_read=32, **tone(P, i + 1))
        sh.text(f"cover-caption-{i}", L, caption,
                Box(box.x + 14, box.y + 190, box.w - 28, 30), hi=20, lo=13,
                color=ink, track=0.12, min_read=13)
    footer(sh, ctx)


@template("specimen_mosaic", "a six-cell letter mosaic that gives paired capitals and lowercase equal space")
def t_specimen_mosaic(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.08)
    ink, mute, _ = field(P)
    y = eyebrow(sh, ctx, "Letter Index") + 24
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    sh.text("mosaic-name", T, name, Box(M, y, W - 2 * M, 136), hi=118,
            lo=40, max_lines=2, min_read=34, **tone(P, 0))

    pairs = [("Aa Bb", "01 · Form"), ("Cc Dd", "02 · Rhythm"),
             ("Ee Ff", "03 · Contrast"), ("Gg Hh", "04 · Structure"),
             ("Ii Jj", "05 · Texture"), ("Kk Ll", "06 · Voice")]
    gap_x, gap_y = 18 * sh.scale, 18 * sh.scale
    cell_w = (W - 2 * M - gap_x) / 2
    cell_h = 224 * sh.vscale
    y0 = y + 160
    fill = P["deep2"] if dark else P["paper2"]
    for i, (glyphs, caption) in enumerate(pairs):
        row, col = divmod(i, 2)
        box = Box(M + col * (cell_w + gap_x), y0 + row * (cell_h + gap_y),
                  cell_w, cell_h)
        _pin_variant_card(sh, box, fill, rung(P, i + 1), 16)
        sh.text(f"mosaic-glyph-{i}", T, glyphs,
                Box(box.x + 16, box.y + 36, box.w - 32, 108), hi=94, lo=32,
                min_read=30, **tone(P, i + 1))
        sh.text(f"mosaic-label-{i}", L, caption,
                Box(box.x + 18, box.y + 170, box.w - 36, 24), hi=17, lo=12,
                color=mute, track=0.12, min_read=12)
    footer(sh, ctx, at="Letter Index")


@template("wordmark_atelier", "a brand identity study pairing a monogram, wordmark, phrase, and lowercase proof")
def t_wordmark_atelier(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    bg(sh, P, ctx["th"], invert=True, pool=0.09)
    ink, mute, dark = field(P, invert=True)
    eyebrow(sh, ctx, "Atelier · Identity Study", invert=True)
    outer = Box(M, 220, W - 2 * M, 590)
    _pin_variant_card(sh, outer, P["deep2"] if dark else P["paper2"],
                      P["accent"], 18)
    cx, cy, radius = M + 194, outer.y + outer.h / 2, 128 * sh.scale
    sh.cv.drawCircle(cx, cy, radius, paint(C(P["accent"], 0.95)))
    sh.cv.drawCircle(cx, cy, radius - 13 * sh.scale,
                     paint(C(ink, 0.78), style=skia.Paint.kStroke_Style,
                           width=2.0 * sh.scale))
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    initial = next((c for c in name if c.isalpha() and usable(ctx, c)), "A")
    sh.text("atelier-monogram", T, initial,
            Box(cx - radius + 24, cy - radius + 18, 2 * radius - 48,
                2 * radius - 36), hi=230, lo=60, min_read=95,
            color=P["paper1"] if dark else P["deep1"])
    title = pack_lines(name.split(), 2)
    measure_rows(sh, T, P, title, Box(M + 354, outer.y + 100,
                 W - M - (M + 354), 360), "atelier-wordmark", hi=162,
                 min_read=34, fill=True, centre=True, lead_frac=0.04)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "A Signature In Every Detail"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 2),
                 Box(M + 12, 870, W - 2 * M - 24, 142), "atelier-phrase",
                 hi=82, min_read=27, fill=True, centre=True, lead_frac=0.02)
    strip = Box(M + 12, 1050, W - 2 * M - 24, 112)
    rule(sh.cv, strip.x, strip.y, strip.r, strip.y, mute, 1.2, 0.58)
    sh.text("atelier-glyphs", T, "Aa Bb Cc Dd",
            Box(strip.x + 10, strip.y + 18, strip.w * 0.62, 72), hi=58,
            lo=24, min_read=24, color=ink)
    sh.text("atelier-caption", L, "A Typeface For Distinctive Names",
            Box(strip.x + strip.w * 0.64, strip.y + 35, strip.w * 0.36 - 8, 28),
            hi=19, lo=12, color=mute, track=0.10, min_read=12)
    footer(sh, ctx, at="Identity Study", invert=True)


@template("illuminated_broadside", "a framed gothic broadside with a centered declaration and a lower character row",
          cls="blackletter")
def t_illuminated_broadside(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.12, tex="laid")
    ink, mute, _ = field(P)
    y = eyebrow(sh, ctx, "The Scriptorium · Broadside") + 38
    frame = Box(M + 16, y, W - 2 * (M + 16), 830)
    sh.cv.drawRect(skia.Rect.MakeXYWH(frame.x, frame.y, frame.w, frame.h),
                   paint(C(ink, 0.68), style=skia.Paint.kStroke_Style,
                         width=1.8 * sh.scale))
    inset = 12 * sh.scale
    sh.cv.drawRect(skia.Rect.MakeXYWH(frame.x + inset, frame.y + inset,
                   frame.w - 2 * inset, frame.h - 2 * inset),
                   paint(C(P["accent"], 0.50), style=skia.Paint.kStroke_Style,
                         width=1.0 * sh.scale))
    for i, (x, cy) in enumerate(((frame.x + 32, frame.y + 34),
                                  (frame.r - 32, frame.y + 34),
                                  (frame.x + 32, frame.b - 34),
                                  (frame.r - 32, frame.b - 34))):
        draw_orn(sh, f"broadside-corner-{i}", "fleur", x, cy,
                 18 * sh.scale, P["accent"], 0.90, collide=False)
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    sh.text("broadside-name", T, name, Box(frame.x + 38, frame.y + 42,
            frame.w - 76, 118), hi=94, lo=30, max_lines=2, min_read=28,
            color=ink)
    rule(sh.cv, frame.x + 54, frame.y + 188, frame.r - 54, frame.y + 188,
         P["accent"], 2.1, 0.78)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "Words With An Older Soul"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 3),
                 Box(frame.x + 60, frame.y + 220, frame.w - 120, 354),
                 "broadside-phrase", hi=182, min_read=38, fill=True,
                 centre=True, lead_frac=0.04)
    draw_orn(sh, "broadside-knot", "triquetra", W / 2, frame.y + 634,
             35 * sh.scale, P["accent"], 0.95, collide=False)
    glyphs = "Aa Bb Cc Dd Ee Ff"
    sh.text("broadside-glyphs", T, glyphs,
            Box(frame.x + 38, frame.y + 698, frame.w - 76, 74), hi=54,
            lo=24, min_read=22, color=ink)
    footer(sh, ctx, at="Printed In The Scriptorium")


@template("reliquary_seal", "a double-ring seal that turns the font's initial into a central emblem",
          cls="blackletter")
def t_reliquary_seal(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.12)
    ink, mute, _ = field(P)
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    measure_rows(sh, T, P, pack_lines(name.split(), 2),
                 Box(M + 30, 180, W - 2 * (M + 30), 174),
                 "seal-name", hi=130, min_read=34, fill=True,
                 centre=True, lead_frac=0.02)
    cx, cy, radius = W / 2, 710, 270 * sh.scale
    for i, (r, col, width) in enumerate(((radius, ink, 3.2),
                                         (radius - 17 * sh.scale, P["accent"], 1.7),
                                         (radius - 36 * sh.scale, ink, 1.0))):
        sh.cv.drawCircle(cx, cy, r, paint(C(col, 0.82 if i != 1 else 0.92),
                         style=skia.Paint.kStroke_Style, width=width * sh.scale))
    for i in range(12):
        a = math.tau * i / 12
        x, y = cx + math.cos(a) * radius * 0.90, cy + math.sin(a) * radius * 0.90
        sh.cv.drawCircle(x, y, 3.1 * sh.scale,
                         paint(C(P["accent"] if i % 3 == 0 else ink, 0.9)))
    initial = next((c for c in name if c.isalpha() and usable(ctx, c)), "A")
    sh.text("seal-initial", T, initial,
            Box(cx - radius * 0.53, cy - radius * 0.55, radius * 1.06,
                radius * 1.06), hi=375, lo=90, min_read=120,
            color=ink, glow=(P["accent"], 0.035, 0.25))
    draw_orn(sh, "seal-top", "fleur", cx, cy - radius - 26 * sh.scale,
             27 * sh.scale, P["accent"], 0.95, collide=False)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "A Mark Made To Endure"))
    sh.text("seal-caption", L, phrase,
            Box(M + 30, 1040, W - 2 * (M + 30), 58), hi=28, lo=15,
            color=mute, track=0.16, min_read=15)
    footer(sh, ctx, at="The Reliquary Press")


@template("scribe_gallery", "a two-column manuscript specimen with an initial, a phrase, and factual glyph rows",
          cls="blackletter")
def t_scribe_gallery(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10, tex="laid")
    ink, mute, _ = field(P)
    y = eyebrow(sh, ctx, "Scribe's Working Page") + 32
    sheet = Box(M, y, W - 2 * M, 920)
    sh.cv.drawRoundRect(skia.Rect.MakeXYWH(sheet.x, sheet.y, sheet.w, sheet.h),
                        12 * sh.scale, 12 * sh.scale,
                        paint(C(P["paper2"] if dark else P["deep2"], 0.32)))
    sh.cv.drawRoundRect(skia.Rect.MakeXYWH(sheet.x, sheet.y, sheet.w, sheet.h),
                        12 * sh.scale, 12 * sh.scale,
                        paint(C(P["accent"], 0.72), style=skia.Paint.kStroke_Style,
                              width=1.5 * sh.scale))
    sh.mark("scribe-sheet", sheet, collide=False)
    divider = sheet.x + 286 * sh.scale
    rule(sh.cv, divider, sheet.y + 46, divider, sheet.b - 46, ink, 1.2, 0.38)
    name = tc(clean(ctx, ctx["name"])).strip() or "Letterforms"
    initial = next((c for c in name if c.isalpha() and usable(ctx, c)), "A")
    sh.text("scribe-initial", T, initial,
            Box(sheet.x + 28, sheet.y + 110, divider - sheet.x - 56, 330),
            hi=300, lo=70, min_read=100, **tone(P, 1))
    sh.text("scribe-name", L, name,
            Box(sheet.x + 28, sheet.y + 495, divider - sheet.x - 56, 110),
            hi=24, lo=13, color=ink, track=0.05, min_read=13, max_lines=2)
    draw_orn(sh, "scribe-vine", "vine", sheet.x + 143 * sh.scale,
             sheet.y + 744, 94 * sh.scale, P["accent"], 0.68, collide=False)
    right = Box(divider + 28, sheet.y + 54, sheet.r - divider - 56, 800)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "Form And Function In Harmony"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 2),
                 Box(right.x, right.y, right.w, 190), "scribe-phrase",
                 hi=95, min_read=27, fill=True, centre=True, lead_frac=0.03)
    rule(sh.cv, right.x, right.y + 226, right.r, right.y + 226,
         P["accent"], 1.8, 0.72)
    sh.text("scribe-lower", T, "Aa Bb Cc Dd Ee Ff",
            Box(right.x, right.y + 264, right.w, 124), hi=72, lo=28,
            min_read=24, **tone(P, 0))
    sh.text("scribe-figures", T, "0123456789",
            Box(right.x, right.y + 422, right.w, 102), hi=58, lo=25,
            min_read=22, color=ink)
    sh.text("scribe-punctuation", T, "& · ? ! @",
            Box(right.x, right.y + 560, right.w, 92), hi=52, lo=23,
            min_read=20, **tone(P, 1))
    sh.text("scribe-caption", L, "Uppercase · Lowercase · Figures · Marks",
            Box(right.x, right.y + 702, right.w, 34), hi=18, lo=12,
            color=mute, track=0.12, min_read=12)
    footer(sh, ctx, at="Scribe's Specimen")


@template("jersey_panel", "a custom jersey silhouette built around a large number and the font's wordmark",
          cls="sports")
def t_jersey_panel(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.09, dev=False)
    device(sh, P, "lanes", dark)
    ink, mute, _ = field(P)
    y = eyebrow(sh, ctx, "Club Issue · Home Kit") + 26
    x, top, width, height = 240 * sh.scale, y + 42, 520 * sh.scale, 760 * sh.vscale
    p = skia.Path()
    p.moveTo(x + width * 0.28, top)
    p.lineTo(x + width * 0.42, top + 16 * sh.scale)
    p.quadTo(x + width * 0.50, top + 68 * sh.scale,
             x + width * 0.58, top + 16 * sh.scale)
    p.lineTo(x + width * 0.72, top)
    p.lineTo(x + width, top + 112 * sh.vscale)
    p.lineTo(x + width * 0.84, top + 246 * sh.vscale)
    p.lineTo(x + width * 0.75, top + 204 * sh.vscale)
    p.lineTo(x + width * 0.75, top + height)
    p.lineTo(x + width * 0.25, top + height)
    p.lineTo(x + width * 0.25, top + 204 * sh.vscale)
    p.lineTo(x + width * 0.16, top + 246 * sh.vscale)
    p.lineTo(x, top + 112 * sh.vscale)
    p.close()
    sh.cv.drawPath(p, paint(C(rung(P, 1), 0.92)))
    sh.cv.drawPath(p, paint(C(ink, 0.86), style=skia.Paint.kStroke_Style,
                             width=4.0 * sh.scale))
    sh.mark("jersey", Box(x, top, width, height), collide=False)
    # Sleeve stripes echo the angular class without borrowing a generic badge.
    for side in (0, 1):
        sx = x + (18 if side == 0 else width - 88) * sh.scale
        stripe = skia.Path()
        stripe.moveTo(sx, top + 128 * sh.vscale)
        stripe.lineTo(sx + 70 * sh.scale, top + 190 * sh.vscale)
        sh.cv.drawPath(stripe, paint(C(P["accent"], 0.85),
                           style=skia.Paint.kStroke_Style,
                           width=7.0 * sh.scale))
    word = tc(clean(ctx, ctx["copy"].get("word") or ctx["name"])).split()
    sh.text("jersey-word", T, " ".join(word[:2]),
            Box(x + 90 * sh.scale, top + 252 * sh.vscale,
                width - 180 * sh.scale, 76 * sh.vscale),
            hi=64, lo=22, min_read=20, color=ink)
    digits = "".join(c for c in "0123456789" if usable(ctx, c))
    number = digits[:2] if len(digits) >= 2 else "20"
    sh.text("jersey-number", T, number,
            Box(x + 72 * sh.scale, top + 350 * sh.vscale,
                width - 144 * sh.scale, 278 * sh.vscale),
            hi=300, lo=70, min_read=90, **tone(P, 0))
    sh.text("jersey-captain", L, "First Team · Season 2026",
            Box(M + 16, top + height + 42, W - 2 * (M + 16), 38),
            hi=24, lo=14, color=mute, track=0.18, min_read=14)
    footer(sh, ctx, at="Built For The Match")


@template("scoreboard_split", "a split score panel turns numerals and a match line into a compact sports poster",
          cls="sports")
def t_scoreboard_split(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.10, dev=False)
    device(sh, P, "grid", dark)
    ink, mute, _ = field(P)
    eyebrow(sh, ctx, "Matchday · Scoreboard")
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "Made For The Final Minute"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 2),
                 Box(M, 190, W - 2 * M, 286), "score-title", hi=145,
                 min_read=34, fill=True, centre=True, lead_frac=0.04)
    boxes = (Box(M + 10, 560, (W - 2 * M - 34) / 2, 478),
             Box(W / 2 + 7, 560, (W - 2 * M - 34) / 2, 478))
    digits = "".join(c for c in "0123456789" if usable(ctx, c))
    sample = digits[:2] if len(digits) >= 2 else "20"
    for i, (box, label_text, score) in enumerate(zip(
            boxes, ("Home", "Away"), (sample, sample[::-1]))):
        _pin_variant_card(sh, box, P["deep2"] if dark else P["paper2"],
                          rung(P, i + 1), 20)
        sh.text(f"score-label-{i}", L, label_text,
                Box(box.x + 24, box.y + 28, box.w - 48, 32), hi=23, lo=14,
                color=mute, track=0.18, min_read=14)
        sh.text(f"score-number-{i}", T, score,
                Box(box.x + 18, box.y + 108, box.w - 36, 220), hi=206,
                lo=70, min_read=70, **tone(P, i + 1))
        sh.text(f"score-record-{i}", L,
                "League Match" if i == 0 else "Away Fixture",
                Box(box.x + 20, box.y + 392, box.w - 40, 28), hi=19, lo=12,
                color=ink, track=0.10, min_read=12)
    draw_orn(sh, "score-check", "checker", W / 2, 1086,
             34 * sh.scale, P["accent"], 0.85, collide=False)
    footer(sh, ctx, at="Full Time")


@template("letter_study", "a calligraphy practice page built around one expressive phrase and its writing line",
          cls="script")
def t_letter_study(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], pool=0.08, dev=False)
    device(sh, P, "ruling", dark)
    ink, mute, _ = field(P)
    y = eyebrow(sh, ctx, "Pen Study · No. 01") + 36
    art = ORN_SETS["penwork" if dark else "flourish"]
    for i, (kind, fx, fy, size, alpha) in enumerate(art["top"]):
        draw_orn(sh, f"letter-study-orn-{i}", kind,
                 M + (W - 2 * M) * fx, y + 92 * sh.vscale,
                 min(size * sh.scale, 58 * sh.scale),
                 P["accent"] if i % 2 else ink, alpha * 0.78,
                 collide=False)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "The Quiet Art Of Writing"))
    lines = pack_lines(phrase.split(), 3)
    measure_rows(sh, T, P, lines,
                 Box(M + 18, y + 188 * sh.vscale, W - 2 * (M + 18),
                     548 * sh.vscale), "letter-study-phrase", hi=190,
                 min_read=38, fill=True, centre=True, lead_frac=0.06)
    base = y + 806 * sh.vscale
    rule(sh.cv, M + 18, base, W - M - 18, base, ink, 1.4, 0.48)
    rule(sh.cv, M + 18, base + 18 * sh.vscale, W - M - 18,
         base + 18 * sh.vscale, mute, 1.0, 0.28)
    signature = tc(clean(ctx, ctx["copy"].get("word") or ctx["name"])).split()
    sig = " ".join(signature[:2])
    sh.text("letter-study-signature", T, sig,
            Box(W * 0.38, base + 38 * sh.vscale, W * 0.50, 126 * sh.vscale),
            hi=98, lo=35, min_read=30, **tone(P, 1))
    draw_orn(sh, "letter-study-nib", "nib", M + 60 * sh.scale,
             base + 92 * sh.vscale, 35 * sh.scale, P["accent"], 0.92,
             collide=False)
    footer(sh, ctx, at="A Handwritten Specimen")


@template("garden_note", "a botanical note card pairs a flowing phrase with a small signature and a drawn frond",
          cls="script")
def t_garden_note(sh, ctx):
    P, T, L = ctx["pal"], ctx["display"], ctx["label"]
    dark = bg(sh, P, ctx["th"], invert=True, pool=0.07)
    ink, mute, _ = field(P, invert=True)
    y = eyebrow(sh, ctx, "Correspondence · Spring Edition", invert=True)
    card = Box(M + 24, 220, W - 2 * (M + 24), 900)
    _pin_variant_card(sh, card, P["paper1"] if dark else P["deep1"],
                      P["accent"], 18)
    accent = P["accent"]
    for i, (x, rot) in enumerate(((card.x + 62, -22), (card.r - 62, 202))):
        draw_orn(sh, f"garden-frond-{i}", "frond", x, card.y + 300,
                 112 * sh.scale, accent, 0.80, collide=False)
    sh.text("garden-date", L, "A Note For The Season",
            Box(card.x + 110, card.y + 54, card.w - 220, 34), hi=21,
            lo=13, color=mute, track=0.18, min_read=13)
    phrase = tc(clean(ctx, ctx["copy"].get("line") or "Let The Day Unfold"))
    measure_rows(sh, T, P, pack_lines(phrase.split(), 3),
                 Box(card.x + 118, card.y + 154, card.w - 236, 420),
                 "garden-phrase", hi=170, min_read=38, fill=True,
                 centre=True, lead_frac=0.05)
    rule(sh.cv, card.x + 150, card.y + 658, card.r - 150,
         card.y + 658, accent, 1.8, 0.62)
    signature = tc(clean(ctx, ctx["copy"].get("word") or ctx["name"])).split()
    sh.text("garden-signature", T, " ".join(signature[:2]),
            Box(card.x + 120, card.y + 700, card.w - 240, 112), hi=92,
            lo=28, min_read=26, color=ink)
    draw_orn(sh, "garden-star", "fleur", W / 2, card.b - 38,
             20 * sh.scale, accent, 0.90, collide=False)
    footer(sh, ctx, at="Written By Hand", invert=True)


# Incoming reference remakes live as independent modules so their drawing code
# stays out of the original pin/studio templates and can be reviewed by family.
SUPPORT_REF_DIR = (Path(__file__).resolve().parents[2] / "font-factory" /
                   "support-references")
from support_templates import register as register_incoming_support_templates
register_incoming_support_templates(globals())


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
                    "refuses copy that repeats. Optional 'templates' lists five distinct "
                    "layouts from the selected class; omit it for the default five.")
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
    ap.add_argument("--supports", action="store_true",
                    help="draw a reproducible random sample of supporting-image "
                         "templates into <out>/3x2 as support-N_<name>.png")
    ap.add_argument("--support-count", type=int, default=12,
                    help="number of eligible support templates to sample (default: 12; "
                         "use --support-review-all for the full active HTML catalogue)")
    ap.add_argument("--support-review-all", action="store_true",
                    help="render every active HTML/CSS support template for review, "
                         "bypassing class-fit filters but keeping retirement and "
                         "real-family-style gates")
    ap.add_argument("--support-renderer", choices=("skia", "hybrid", "html"),
                    default="skia",
                    help="support output backend: skia (default), hybrid (HTML for "
                         "ported templates, Skia for the rest), or html (require every "
                         "selected template to have an HTML/CSS port)")
    ap.add_argument("--support-ratios", choices=("both", "3x2", "1x1"),
                    default="both",
                    help="ratios to render for --supports (default: both 3:2 and square)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--stress", action="store_true")
    ap.add_argument("--faces", default="", help="name=path:name=path for --stress")
    args = ap.parse_args()

    if args.list:
        if args.supports:
            print("  [supports]")
            for k in SUPPORT_ORDER:
                if k in SUPPORT_RETIRED:
                    continue
                _f, blurb, _c, _fr = TEMPLATES[k]
                print(f"    {k:13s} {blurb}")
            return 0
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

    if args.supports and args.specimens:
        ap.error("--supports and --specimens are different surfaces; pick one")
    if args.support_renderer != "skia" and not args.supports:
        ap.error("--support-renderer requires --supports")
    if args.support_review_all and not args.supports:
        ap.error("--support-review-all requires --supports")
    if args.support_review_all and args.support_renderer != "html":
        ap.error("--support-review-all requires --support-renderer html")
    if args.support_ratios != "both" and not args.supports:
        ap.error("--support-ratios requires --supports")
    support_ratio_names = (("3x2", "1x1") if args.support_ratios == "both"
                           else (args.support_ratios,))
    if args.supports and args.support_count < 1:
        ap.error("--support-count must be at least 1")
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
    if args.supports:
        # Class flavour: the pool stays shared, but a class that owns worlds
        # opens with them, so a blackletter's supports ship in vellum or gilded
        # and an elegant's never see either.
        cls_worlds = {"blackletter": ("vellum", "gilded"),
                      "sports": ("asphalt", "chrome"),
                      "script": ("graphite", "inkwell")}
        active_supports = tuple(
            support_review_names(ctx["family_style_count"])
            if args.support_review_all else
            support_names(cls, ctx["family"], ctx["family_style_count"],
                          ctx["has_weight_triplet"]))
        if args.support_renderer == "skia":
            active_supports = tuple(name for name in active_supports
                                    if name not in HTML_ONLY_SUPPORT)
        prefs = {n: cls_worlds.get(cls, ()) + THEME_PREF[n]
                 for n in active_supports}
        ctx["themes"] = dict(ctx["themes"],
                             **assign_themes(ctx["name"], sorted(active_supports),
                                             cls, prefs))
    per = {}
    if brief is not None:
        themes, offs, copies = dict(ctx["themes"]), {}, {}
        for block in ("pins", "supports"):
            for t, pin in (brief.get(block) or {}).items():
                if pin.get("theme"):
                    themes[t] = pin["theme"]
                offs[t] = int(pin.get("tone") or 0)
                copies[t] = {k: (pin.get(k) or "")
                             for k in ("line", "sub", "over", "word")}
        ctx = dict(ctx, themes=themes, tone_offs=offs, briefed=True)
        per = {t: dict(ctx, copy=c,
                       ftrs=(brief.get("pins") or {}).get(t, {}).get("ftrs") or {})
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
    owned = ((support_review_names(ctx["family_style_count"])
              if args.support_review_all else
              support_names(cls, ctx["family"], ctx["family_style_count"],
                            ctx["has_weight_triplet"])) if args.supports else
             cls_names_spec(cls) if args.specimens else cls_names(cls))
    if args.supports and args.support_renderer == "skia":
        owned = [name for name in owned if name not in HTML_ONLY_SUPPORT]
    if args.supports and not args.template and args.support_review_all:
        names = list(owned)
        if not args.as_json:
            print(f"  supports: review-all selected {len(names)} of {len(owned)} active templates")
    elif args.supports and not args.template:
        seed = int(hashlib.sha256(
            f"{ctx['name']}|{cls}|support-catalogue".encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)
        count = min(args.support_count, len(owned))
        usage_counts = support_history_counts(args.font, cls)
        names = select_support_templates(rng, owned, count, cls, usage_counts)
        if not args.as_json:
            print(f"  supports: selected {len(names)} of {len(owned)} eligible templates, prioritizing least-used layouts")
    elif args.specimens:
        names = args.template or owned
    else:
        names = (args.template or (brief or {}).get("templates")
                 or CLASS_ORDERS[cls])
    stray = [n for n in names if n not in owned]
    if stray:
        what = ("supports" if args.supports else "specimen sheets"
                if args.specimens else f"class {cls!r}")
        ap.error(f"template(s) {', '.join(stray)} are not in {what}; "
                 f"{what} has {', '.join(owned)}")
    if args.supports and args.support_renderer == "html":
        missing_html = [name for name in names
                        if name not in SUPPORT_HTML_RENDERERS]
        if missing_html:
            ap.error("--support-renderer html has no port for: "
                     + ", ".join(missing_html))
    if args.supports and not args.template:
        # A brief that authored a panel this face cannot wear is not wrong, it is
        # spent — say so rather than let the shop count the missing sheet by hand.
        idle = ([t for t in sorted((brief.get("supports") or {}))
                 if t in SUPPORT_ORDER and t not in SUPPORT_RETIRED and t not in owned]
                if brief is not None else [])
        if idle:
            print(f"  supports: not shipped for {cls}/{ctx['family']}: "
                  + ", ".join(idle), file=sys.stderr)
        # This is a thirteen-design deliverable, not a cache of every panel ever
        # rendered. Remove only the renderer's own support-* outputs outside the
        # newly selected set, leaving every unrelated file untouched.
        for ratio in support_ratio_names:
            keep = out / ratio
            if keep.is_dir():
                for stale in sorted(keep.glob("support-*_*")):
                    stem = stale.name.split("_", 1)[1].rsplit(".", 1)[0]
                    if (stem in SUPPORT_RETIRED
                            or stem in SUPPORT_ORDER and stem not in names):
                        stale.unlink()
                        print(f"  supports: withdrew unselected {ratio}/{stale.name}", file=sys.stderr)
    errors, notes, payload = [], [], []
    render_ratios = support_ratio_names if args.supports else ("3x2",)
    for name in names:
        browser_enabled = (args.supports
                           and args.support_renderer in ("hybrid", "html")
                           and name in SUPPORT_HTML_RENDERERS)
        for ratio in render_ratios:
            html_report = None
            content_warnings = []
            if browser_enabled:
                ship = out / ratio / (
                    f"support-{SUPPORT_ORDER.index(name) + 1}_{name}.png")
                ship.parent.mkdir(parents=True, exist_ok=True)
                ship, size, html_report = render_support_html(
                    name, per.get(name, ctx), ship, ratio,
                    review_mode=args.support_review_all)
                report = html_report.get("layoutReport") or {}
                if name == "roadrunner32":
                    font_px = float(str(report.get("headlineFontSize", "0")).removesuffix("px"))
                    slots = [
                        {"name": "road_quote", "size": font_px * 2,
                         "lines": len(html_report.get("headline", "").splitlines())},
                        {"name": "road_descriptor",
                         "size": float(str(report.get("descriptorFontSize", "0")).removesuffix("px")) * 2,
                         "lines": len(html_report.get("descriptor", "").splitlines())},
                        {"name": "road_bodycopy",
                         "size": float(str(report.get("bodyFontSize", "0")).removesuffix("px")) * 2,
                         "lines": len(html_report.get("body", "").splitlines())},
                        {"name": "road_badge",
                         "size": float(str(report.get("badgeFontSize", "0")).removesuffix("px")) * 2,
                         "lines": 1},
                    ]
                else:
                    def css_px(value):
                        return float(str(value or "0").removesuffix("px").strip())

                    slots = [{"name": item["name"],
                              "size": css_px(item.get("fontSize", 0)) * 2,
                              "lines": 1}
                             for item in report.get("slots", [])]
                errs = []
                content_warnings = html_report.get("contentWarnings", [])
                sheet_notes = [f"content: {warning}" for warning in content_warnings]
                sheet_notes.extend(
                    f"review: {warning}"
                    for warning in html_report.get("reviewWarnings", []))
            else:
                surf, sh = render(name, per.get(name, ctx),
                                  frame_override=ratio if args.supports else None)
                img = surf.makeImageSnapshot()
                if args.supports:
                    ship, size = save_specimen(
                        img, out, ratio, f"{SUPPORT_ORDER.index(name) + 1}_{name}",
                        prefix="support")
                    note = None
                elif args.specimens:
                    _, sheet, frame = name.rsplit("_", 2)
                    ship, size = save_specimen(img, out, frame, sheet)
                    note = None
                else:
                    stem = (f"pinterest_{names.index(name) + 1}"
                            if per else name)
                    ship, size, note = save_pin(img, out, stem)
                if note:
                    sh.notes.append(note)
                errs = as_errors(name, sh)
                sheet_notes = sh.notes
                slots = [{"name": s.name, "size": s.size, "lines": s.lines}
                         for s in sh.slots]
            kb = size / 1024
            # Supporting images are art-directed deliverables, not feed pins.
            cap = (None if args.supports else
                   SPECIMEN_MAX_BYTES if args.specimens else MAX_BYTES)
            if cap is not None and size > cap:
                surface = "specimen" if args.specimens else "pin"
                errs.append({"template": name, "slot": "file",
                             "message": f"{kb:.0f} KB exceeds the "
                                        f"{cap // 1000} KB {surface} cap"})
            errors += [dict(error, ratio=ratio) for error in errs]
            notes += [{"template": name, "ratio": ratio,
                       "slot": n.split(":", 1)[0], "message": n}
                      for n in sheet_notes]
            payload.append({"template": name, "ratio": ratio,
                            "png": str(ship), "kb": round(kb),
                            "renderer": "HTML/CSS" if html_report else "Python Skia",
                            **({"contentWarnings": content_warnings}
                               if html_report else {}),
                            "slots": [{"slot": s["name"], "size": round(s["size"], 1),
                                       "lines": s["lines"]} for s in slots]})
            if not args.as_json:
                print(f"  {ratio:3s} {name:24s} {kb:5.0f} KB  " +
                      "  ".join(f"{s['name']}={s['size']:.0f}px/{s['lines']}L"
                                for s in slots))
                for e in errs:
                    print(f"      ! {e['message']}")
                for n in sheet_notes:
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


def _html_reference_placeholder(_sheet, _ctx):
    raise RuntimeError("This reference remake requires --support-renderer html or hybrid")


for _html_reference_id in HTML_ONLY_SUPPORT:
    TEMPLATES[_html_reference_id] = (
        _html_reference_placeholder,
        "User-supplied source-led HTML/CSS remake",
        "elegant",
        "3x2",
    )


if __name__ == "__main__":
    raise SystemExit(main())
