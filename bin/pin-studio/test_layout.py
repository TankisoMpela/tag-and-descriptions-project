"""Kernel self-test: does the layout layer actually prevent the two bug classes?

Run:  bin/pin-studio/.venv/bin/python bin/pin-studio/test_layout.py

The claim under test is narrow and checkable: for any copy, any face, any box,
Sheet.text() draws ink that (a) stays inside the declared box and (b) cannot
silently land on another block's ink. Everything else is taste; this is correctness.
"""
import sys
from pathlib import Path

import skia
import pin_studio as ps
import audit_support_classes as support_audit
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
sh2b = sheet()
sh2b.text("face", t, "Cosette", Box(M, 400, W - 2 * M, 300), hi=200,
           color=(250, 245, 220))
sh2b.text("decorative shadow", t, "Cosette", Box(M, 405, W - 2 * M, 300),
           hi=200, color=(0, 0, 0), collide=False)
case("intentional text overprint can opt out of collision checks",
     sh2b.verify() == [], str(sh2b.verify()))

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

print("\n7. the specimen frames: 3:2 and 1:1 hold their own geometry")
# The pins were tuned on one 1000x1500 page; the sheets are drawn on two others.
# What that can break is exactly four things, so all four are checked on every
# template rather than on the one that was being looked at that day.
SPEC_FACES = {
    "elegant": "outputs/font-preparation/077-kuro-ripper/Kuro-Ripper/KuroRipper-Regular.otf",
    "blackletter": "font-factory/font-preparation/braewick/Braewick/Braewick-Regular.otf",
    "sports": "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
    "script": "outputs/font-preparation/082-restrained-flourish/Restrained-Flourish/RestrainedFlourish-Regular.otf",
}
for cls, fpath in SPEC_FACES.items():
    ctx = ps.build_ctx(ROOT / fpath, "", dict.fromkeys(("line", "sub", "over", "word"), ""),
                       cls=cls)
    for name in ps.SPECIMEN_ORDERS[cls]:
        _surf, sh = ps.render(name, ctx)
        floor = sh.h - sh.m
        low = [s.name for s in sh.slots if s.ink.b > floor + 1]
        case(f"{name}: nothing prints below the foot margin", not low, str(low)[:70])
        # The rows are the sheet's subject: on a 1600px page a row whose ink is
        # shorter than 80px is a thumbnail, not a specimen. Measured as ink
        # height because most rows are drawn as outlines, not through Sheet.text.
        rows = [s for s in sh.slots if s.name.startswith(("row", "run"))]
        case(f"{name}: the sheet drew its characters", bool(rows), f"{len(rows)} rows")
        thin = [f"{s.name}={s.ink.h:.0f}" for s in rows if s.ink.h < 0.05 * sh.h]
        case(f"{name}: every row is drawn at reading size", not thin, str(thin)[:70])
        spill = [f"{s.name}[{s.ink.x:.0f}..{s.ink.r:.0f}]" for s in rows
                 if s.ink.x < sh.m - 1 or s.ink.r > sh.w - sh.m + 1]
        case(f"{name}: no row hangs out of the side margins", not spill, str(spill)[:70])
        # The kernel's own two checks, on the frame the templates were not tuned for.
        v = sh.verify()
        case(f"{name}: nothing lands off the canvas",
             not [m for m in v if m.startswith("OFF-CANVAS")], str(v)[:70])
        case(f"{name}: no row collides with another block",
             not [m for m in v if m.startswith("OVERLAP")], str(v)[:70])
        text = [s for s in sh.slots if s.size > 0]
        blind = [s.name for s in text if sh._behind(s.box) is None]
        case(f"{name}: the ground under every line was measured", not blind,
             str(blind)[:70])
        # The specimen ground is one flat tone by design, so a lift is not a
        # difficult page — it is the body sampling the wrong colour.
        lifts = [note for note in sh.notes if "lifted" in note.casefold()]
        case(f"{name}: no ink needed lifting", not lifts, str(lifts)[:70])

print("\n8. support catalogue guarantees and copy separation")
support_copy = dict.fromkeys(("line", "sub", "over", "word"), "")
name_ctx = ps.build_ctx(ROOT / FACES["serif"], "Whisky",
                        {**support_copy, "word": "Whisky"})
case("a support headline cannot repeat the font name",
     ps._support_copy(name_ctx, ("word", "line"), "POSTER TYPE") == "POSTER TYPE")
stock_ctx = ps.build_ctx(ROOT / FACES["serif"], "Andallan",
                         {**support_copy, "word": "Whisky"})
case("Whisky is not used as stock display copy",
     ps._support_copy(stock_ctx, ("word",), "POSTER TYPE") == "POSTER TYPE")
case("fixed support furniture is cleaned and cannot repeat the font name",
     ps.support_render_copy(name_ctx, "Whisky") == "TYPE"
     and ps.support_render_copy(stock_ctx, "Whisky") == "TYPE")
case("fixed support copy keeps intentional line breaks",
     ps.support_render_copy(stock_ctx, "MADE WITH\nCARE") == "MADE WITH\nCARE")
lit_ctx = dict(stock_ctx, copy={**stock_ctx["copy"], "line": "", "word": ""})
case("neon fallback keeps the reference's two-line sign lockup",
     len(ps._lit_lockup_text(
         lit_ctx, ("opening night", "last call", "one night only",
                   "live on stage", "the main event")).split()) >= 2)
retired = {"announce32", "ladder32", "retro32", "variable32", "archive32",
           "cast32", "loop32", "sticker32", "echo32", "brutalpack32",
           "dreamchalk32", "lovecard32", "queens32", "lemonade32", "sunkiss32"}
old_retired = {"announce32", "ladder32", "retro32", "variable32", "archive32",
               "cast32", "loop32"}
new_tombstones = retired - old_retired
case("withdrawn support concepts are absent from the live template registry",
     retired.isdisjoint(ps.TEMPLATES))
case("dropped review templates retain only stable numbering tombstones",
     new_tombstones <= set(ps.SUPPORT_ORDER)
     and new_tombstones <= ps.SUPPORT_RETIRED
     and all(name not in ps.TEMPLATES for name in new_tombstones))
case("comparison sources stay blank when no original was supplied",
     support_audit.REFERENCES["line32"][0] is None
     and support_audit.REFERENCES["card32"][0] is None
     and support_audit.REFERENCES["duo32"][0] == "T30173_08")
case("feature callouts use real GSUB names when available",
     ps.feature_callout_labels({"facts": {"features": ["salt", "dlig"]}})
     == ["Discretionary Ligatures", "Stylistic Alternate"])
case("feature callouts stay truthful when the font exposes no feature tags",
     ps.feature_callout_labels({"facts": {"features": []}})
     == ["Feature Set Varies", "See Available Glyphs"])
case("70 stable support slots retain 61 active templates",
     len(ps.SUPPORT_ORDER) == 70
     and len(set(ps.SUPPORT_ORDER)) == 70
     and ps.SUPPORT_ORDER[42] == "bondibeach32"
     and "bondibeach32" in ps.SUPPORT_RETIRED
     and "bondibeach32" not in ps.TEMPLATES
     and len([name for name in ps.SUPPORT_ORDER
              if name not in ps.SUPPORT_RETIRED]) == 61
     and set(name for name in ps.SUPPORT_ORDER
             if name not in ps.SUPPORT_RETIRED) <= set(ps.TEMPLATES)
     and all(name in ps.THEME_PREF for name in ps.SUPPORT_ORDER
             if name not in ps.SUPPORT_RETIRED),
     f"{len(ps.SUPPORT_ORDER)} slots / {len(set(ps.SUPPORT_ORDER))} unique")
case("Bondi Beach cannot be selected by any support class",
     all("bondibeach32" not in ps.support_names(cls)
         for cls in ps.CLASS_ORDERS))
blackletter_no = {
    "duo32", "contour32", "mirror32", "ovalword32", "kindersea32",
    "messageframe32", "pixelquote32", "ravencover32", "voguecover32",
    "confident32", "storyteller32", "wideclaim32", "neue32",
    "demolition32", "skinbadge32", "gelatocards32", "meditation32",
    "typewall32", "pastpresent32",
}
case("first-pass blackletter exclusions are unavailable to its random pool",
     blackletter_no.isdisjoint(
         ps.support_names("blackletter", "blackletter", 2)))
blackletter_audit_names = support_audit.class_audit_names(
    "blackletter", list(support_audit.ACTIVE), "blackletter", 2, False)
case("blackletter comparison rerenders follow the reviewed eligible pool",
     set(blackletter_audit_names)
     == set(ps.support_names("blackletter", "blackletter", 2)))
case("contour32 stays available only for handwritten and display styles",
     "contour32" in ps.support_names("script", "script", 1)
     and "contour32" in ps.support_names("elegant", "display-bold", 1)
     and all("contour32" not in ps.support_names(cls, family, styles)
             for cls, family, styles in (
                 ("blackletter", "blackletter", 2), ("script", "brush", 1),
                 ("sports", "brush", 3), ("sports", "pixel", 2))))
style_pools = {
    "blackletter": ("blackletter", "blackletter", 2, 37),
    "handwritten": ("script", "script", 1, 48),
    "tech-sports": ("sports", "brush", 3, 41),
    "brush": ("script", "brush", 1, 52),
    "pixel": ("sports", "pixel", 2, 46),
    "display": ("elegant", "display-bold", 1, 51),
}
case("renderer classes resolve to the six audited support styles",
     ps.support_style_group("blackletter", "blackletter") == "blackletter"
     and ps.support_style_group("script", "script") == "handwritten"
     and ps.support_style_group("script", "brush") == "brush"
     and ps.support_style_group("sports", "brush") == "tech-sports"
     and ps.support_style_group("sports", "pixel") == "pixel"
     and ps.support_style_group("elegant", "display-bold") == "display")
for group, (cls, family, styles, expected_count) in style_pools.items():
    pool = set(ps.support_names(cls, family, styles))
    excluded = ps.SUPPORT_STYLE_EXCLUDE[group]
    case(f"{group}: hard mismatches are discounted",
         excluded.isdisjoint(pool), f"still eligible: {sorted(excluded & pool)}")
    case(f"{group}: eligible pool has expected size and can supply seven",
         len(pool) == expected_count and len(pool) >= 7,
         f"{len(pool)} eligible; expected {expected_count}")
case("Neue is reserved for the sports/tech specimen class",
     all("neue32" in ps.SUPPORT_STYLE_EXCLUDE[group]
         for group in ("blackletter", "handwritten", "brush", "pixel", "display"))
     and "neue32" not in ps.SUPPORT_STYLE_EXCLUDE["tech-sports"])
family_font = ROOT / "font-factory/fonts/3-Lindgre/Lindgre L2THLSE/Lindgre/Lindgre-Regular.otf"
family_ctx = ps.build_ctx(family_font, "Lindgre", support_copy)
family_panels = {"plakat32", "weightfamily32", "mangosboard32"}
eligible = set(ps.support_names("elegant", family_ctx["family"],
                                family_ctx["family_style_count"],
                                family_ctx["has_weight_triplet"]))
case("family-only boards and Plakat are eligible for a real multi-style family",
     family_ctx["family_style_count"] >= 2 and family_panels <= eligible,
     f"{family_ctx['family_style_count']} styles")
case("family boards do not invent sibling styles for a single face",
     family_panels.isdisjoint(ps.support_names("elegant", "single", 1)))
family_panel_names = {"boots32", "plakat32", "weightfamily32", "mangosboard32"}
case("family label names retain the real family and style",
     ps.family_style_label("Mangos", "Black") == "Mangos Black"
     and ps.family_style_label("Mangos", "Mangos Regular") == "Mangos Regular")
case("family audit uses all and only genuine family-gated templates",
     set(support_audit.class_audit_names(
         "family", list(support_audit.ACTIVE), family_ctx["family"],
         family_ctx["family_style_count"], family_ctx["has_weight_triplet"]))
     == family_panel_names
     and not (family_panel_names & set(support_audit.class_audit_names(
         "display", list(support_audit.ACTIVE), "single", 1, False))))
family_findings = []
for template in sorted(family_panel_names):
    _, family_sheet = ps.render(template, family_ctx)
    family_findings.extend(
        f"{template}: {error['message']}"
        for error in ps.as_errors(template, family_sheet)
    )
case("family-gated designs render cleanly with real Lindgre siblings",
     not family_findings,
     "; ".join(family_findings[:3]) or "4 real-family renders; 0 findings")

focused_supports = {
    "card32", "boots32", "sunsetpromise32", "contactlist32",
    "phonegarden32", "pixelquote32",
}
support_findings = []
for slug, cfg in support_audit.CLASSES.items():
    if slug == "family":
        continue
    ctx = ps.build_ctx(ROOT / cfg["font"], "", support_audit.COPY,
                       about=cfg["about"], cls=cfg["render_class"])
    ctx["themes"] = dict(
        ctx["themes"],
        **ps.assign_themes(
            ctx["name"], sorted(support_audit.ACTIVE), cfg["render_class"],
            {n: support_audit.CLASS_WORLDS.get(cfg["render_class"], ())
                + ps.THEME_PREF[n] for n in support_audit.ACTIVE},
        ),
    )
    for template in sorted(focused_supports):
        _, support_sheet = ps.render(template, ctx)
        support_findings.extend(
            f"{slug}/{template}: {error['message']}"
            for error in ps.as_errors(template, support_sheet)
        )
case("six spacing fixes pass across all six audited styles",
     not support_findings,
     "36 focused renders; " + ("0 findings" if not support_findings
                              else "; ".join(support_findings[:3])))

print(f"\n{'ALL GREEN' if fails == 0 else str(fails) + ' FAILURE(S)'}")
sys.exit(1 if fails else 0)
