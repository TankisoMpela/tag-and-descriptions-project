"""Bold, text-free remakes of the assigned editorial and display poster references."""

import math
import random
from pathlib import Path


def register(api):
    support, skia, C, paint, rule = (api[k] for k in
                                     ("support", "skia", "C", "paint", "rule"))
    Box, ground = api["Box"], api["ground"]
    support_copy = api["_support_copy"]
    ref_dir = Path(api["SUPPORT_REF_DIR"])
    mix = api["mix"]
    layout_text = api["layout"]

    def text(sh, ctx, name, wording, box, *, size, color=None,
             display=True, max_lines=1, align="center", track=0.0,
             min_read=18, leading=.84, min_contrast=4.5, hatch=None,
             distress=None, collide=True):
        if not wording:
            return
        face = ctx["display"] if display else ctx["label"]
        hi = size*sh.scale
        tracking = hi*track
        sh.text(name, face, wording, box,
                hi=hi, lo=max(8, 12*sh.scale), tracking=tracking,
                color=color or ctx["pal"]["glow"], max_lines=max_lines,
                align=align, valign="middle", leading=leading,
                min_read=min_read*sh.scale, min_contrast=min_contrast,
                hatch=hatch, collide=collide)
        if distress:
            slot = next((s for s in reversed(sh.slots) if s.name == name), None)
            if slot is None or not slot.lines:
                return
            laid = layout_text(face, wording, box.w, slot.size, tracking,
                               leading, max_lines)
            if not laid or not laid[0]:
                return
            lines, paths, step, top, bottom, _ = laid
            ink_h = bottom-top
            oy = box.y + (box.h-ink_h)/2-top
            dcolor, density, alpha, radius = distress
            for index, (line_text, path) in enumerate(zip(lines, paths)):
                bounds = path.getBounds()
                ox = {"left": box.x-bounds.x(),
                      "right": box.r-bounds.right(),
                      "center": box.x+(box.w-bounds.width())/2-bounds.x()}[align]
                sh.cv.save()
                sh.cv.translate(ox, oy+index*step)
                sh.cv.clipPath(path)
                grit = skia.Path()
                count = max(40, int(bounds.width()*bounds.height()*density))
                rng = random.Random(sum(map(ord, line_text))+index*97)
                for _ in range(count):
                    x = rng.uniform(bounds.left(), bounds.right())
                    y = rng.uniform(bounds.top(), bounds.bottom())
                    r = sh.scale*radius*(.25+rng.random()*.75)
                    grit.addCircle(x, y, r)
                sh.cv.drawPath(grit, paint(C(dcolor, alpha)))
                sh.cv.restore()

    def line(sh, x1, y1, x2, y2, color, width=1.5, alpha=.9):
        rule(sh.cv, x1, y1, x2, y2, color, width*sh.scale, alpha)

    def rounded(sh, box, color, radius, *, fill=True, width=2, alpha=1):
        p = paint(C(color, alpha),
                  style=None if fill else skia.Paint.kStroke_Style,
                  width=width*sh.scale)
        sh.cv.drawRoundRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                            radius*sh.scale, radius*sh.scale, p)
        sh.mark("poster_shape", box, collide=False)

    def texture_plate(sh, filename, fallback_top, fallback_bottom):
        path = ref_dir / "materials" / filename
        plate = skia.Image.open(str(path)) if path.is_file() else None
        if plate is None:
            sh.problems.append(f"poster texture missing or unreadable: {path.name}")
            ground(sh.cv, fallback_top, fallback_bottom, w=sh.w, h=sh.h)
            return False
        sh.cv.drawImageRect(plate,
                            skia.Rect.MakeWH(plate.width(), plate.height()),
                            skia.Rect.MakeWH(sh.w, sh.h),
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        return True

    @support("neue32", "the neo-grotesk repetition poster with oversized repeated words and rounded signal pills")
    def neue32(sh, ctx):
        pink, black = (246, 173, 193), (17, 14, 20)
        coral, lilac, white = (250, 67, 62), (135, 83, 189), (255, 255, 255)
        sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(pink)))
        text(sh, ctx, "neue_meta_left", "Type Study / 01",
             Box(sh.w*.065, sh.h*.075, sh.w*.43, sh.h*.045), size=18,
             color=black, display=False, align="left", track=.005, min_read=12)
        text(sh, ctx, "neue_meta_right", "Display Sans Design",
             Box(sh.w*.69, sh.h*.075, sh.w*.25, sh.h*.045), size=20,
             color=black, display=False, align="right", track=.005, min_read=11)

        # The three specimen lines deliberately step down and right, matching
        # the source's loose typographic rhythm rather than sitting in panels.
        specimen_word = "Neue!"
        rows = ((.055, .16, .48, .205), (.265, .405, .56, .205),
                (.395, .645, .58, .205))
        for i, (x, y, w, h) in enumerate(rows):
            text(sh, ctx, f"neue_word{i}", specimen_word,
                 Box(sh.w*x, sh.h*y, sh.w*w, sh.h*h), size=205,
                 color=black, min_read=75, align="left", track=-.025,
                 leading=.86)

        # Source-like slanted capsules sit over the specimen, not in a row.
        def angled_pill(key, phrase, x, y, w, h, angle, fill, ink):
            cx, cy = sh.w*(x+w/2), sh.h*(y+h/2)
            pw, ph = sh.w*w, sh.h*h
            sh.cv.save()
            sh.cv.translate(cx, cy)
            sh.cv.rotate(angle)
            sh.cv.drawRoundRect(skia.Rect.MakeXYWH(-pw/2, -ph/2, pw, ph),
                                ph/2, ph/2, paint(C(fill)))
            face = ctx["display"]
            size = 33*sh.scale
            tracking = .02*size
            size = face.fit(phrase, size, pw*.82, tracking=tracking)
            path, _ = face.path(phrase, size, tracking=tracking)
            bounds = path.getBounds()
            sh.cv.save()
            sh.cv.translate(-bounds.centerX(), -bounds.centerY())
            sh.cv.drawPath(path, paint(C(ink)))
            sh.cv.restore()
            sh.cv.restore()
            # Track the rotated capsule's enclosing box for diagnostics.
            rad = math.radians(angle)
            aw = abs(pw*math.cos(rad)) + abs(ph*math.sin(rad))
            ah = abs(pw*math.sin(rad)) + abs(ph*math.cos(rad))
            sh.mark(key, Box(cx-aw/2, cy-ah/2, aw, ah), collide=False)

        angled_pill("neue_pill_top", "Display", .515, .105, .395, .165,
                    9, coral, white)
        angled_pill("neue_pill_mid", "Type", .72, .435, .26, .135,
                    3, white, pink)
        angled_pill("neue_pill_bottom", "Form", .02, .685, .35, .17,
                    -10, lilac, white)

        text(sh, ctx, "neue_footer_left", "A Study In Geometric Form",
             Box(sh.w*.065, sh.h*.925, sh.w*.43, sh.h*.04), size=16,
             color=black, display=False, align="left", track=.005, min_read=10)
        text(sh, ctx, "neue_footer_right", "OpenType / Variable Support",
             Box(sh.w*.64, sh.h*.925, sh.w*.30, sh.h*.04), size=19,
             color=black, display=False, align="right", track=.01, min_read=10)

    @support("electromagnetic32", "the dark signal poster with violet and acid-green atmospheric glows around compact techno lettering")
    def electromagnetic32(sh, ctx):
        texture_path = ref_dir / "materials/T19827_01_electromagnetic-texture.png"
        texture = skia.Image.open(str(texture_path)) if texture_path.is_file() else None
        if texture is None:
            sh.problems.append(f"electromagnetic32: missing or unreadable {texture_path.name}")
            ground(sh.cv, (14, 15, 21), (30, 22, 38), w=sh.w, h=sh.h)
        else:
            sh.cv.drawImageRect(texture, skia.Rect.MakeWH(texture.width(), texture.height()),
                                skia.Rect.MakeWH(sh.w, sh.h),
                                skia.SamplingOptions(skia.FilterMode.kLinear,
                                                     skia.MipmapMode.kLinear))
        ink = (13, 12, 17)
        rail_ink = (224, 220, 225)

        # Rebuild the source's two technical rails without retaining its logos
        # or the small font-name lockup.
        text(sh, ctx, "em_kicker_left", "Type STUDY / 03",
             Box(sh.w*.15, sh.h*.105, sh.w*.34, sh.h*.045), size=18,
             color=rail_ink, display=False, align="left", track=.045,
             min_read=10, min_contrast=2.0)
        text(sh, ctx, "em_kicker_right", "Frequency / Field",
             Box(sh.w*.60, sh.h*.105, sh.w*.24, sh.h*.045), size=17,
             color=rail_ink, display=False, align="right", track=.035,
             min_read=9, min_contrast=2.0)
        line(sh, sh.w*.15, sh.h*.16, sh.w*.79, sh.h*.16, rail_ink, 1.5, .9)
        cx, cy = sh.w*.85, sh.h*.145
        rx, ry = sh.w*.045, sh.h*.027
        globe = skia.Rect.MakeLTRB(cx-rx, cy-ry, cx+rx, cy+ry)
        mesh = paint(C((198, 222, 133), .96),
                     style=skia.Paint.kStroke_Style, width=1.7*sh.scale)
        sh.cv.drawOval(globe, mesh)
        for side in (-1, 0, 1):
            meridian = skia.Path()
            meridian.moveTo(cx, cy-ry)
            meridian.cubicTo(cx+side*rx*.72, cy-ry*.54,
                             cx+side*rx*.72, cy+ry*.54, cx, cy+ry)
            sh.cv.drawPath(meridian, mesh)
        for offset in (-.34, .34):
            latitude = skia.Path()
            y = cy + ry*offset
            latitude.moveTo(cx-rx*.91, y)
            latitude.cubicTo(cx-rx*.38, y+ry*.30,
                             cx+rx*.38, y+ry*.30, cx+rx*.91, y)
            sh.cv.drawPath(latitude, mesh)
        sh.mark("electromagnetic_globe", Box(cx-rx, cy-ry, rx*2, ry*2),
                 collide=False)

        # Four compact lines reproduce the source's dense centered display block.
        phrase = "Electro\nMagnetic\nShady-01\nCourse-"
        text(sh, ctx, "em_word", phrase,
             Box(sh.w*.155, sh.h*.245, sh.w*.70, sh.h*.50), size=135,
             color=ink, max_lines=4, min_read=32, min_contrast=1.7,
             align="left", track=-.025, leading=.90)

        line(sh, sh.w*.15, sh.h*.785, sh.w*.85, sh.h*.785, ink, 1.2, .76)
        text(sh, ctx, "em_footer_left", "Noise / Light / Motion",
             Box(sh.w*.15, sh.h*.81, sh.w*.48, sh.h*.05), size=18,
             color=rail_ink, display=False, align="left", track=.045,
             min_read=10, min_contrast=2.0)
        text(sh, ctx, "em_footer_right", "Type / 03",
             Box(sh.w*.72, sh.h*.81, sh.w*.13, sh.h*.05), size=17,
             color=rail_ink, display=False, align="right", track=.04,
             min_read=9, min_contrast=2.0)

    @support("demolition32", "the demolition poster with chromatic energy fields, dense stacked display copy, and a small impact mark")
    def demolition32(sh, ctx):
        texture_path = ref_dir / "materials/T19827_06_demolition-texture.png"
        texture = skia.Image.open(str(texture_path)) if texture_path.is_file() else None
        if texture is None:
            sh.problems.append(f"demolition32: missing or unreadable {texture_path.name}")
            ground(sh.cv, (38, 25, 29), (41, 28, 38), w=sh.w, h=sh.h)
        else:
            sh.cv.drawImageRect(texture, skia.Rect.MakeWH(texture.width(), texture.height()),
                                skia.Rect.MakeWH(sh.w, sh.h),
                                skia.SamplingOptions(skia.FilterMode.kLinear,
                                                     skia.MipmapMode.kLinear))
        ink, light = (18, 16, 20), (239, 224, 190)
        phrase = "Beh-Ago\nDemolition\nAbnormal(Ey)\nMal-Out"
        text(sh, ctx, "demo_title", phrase,
             Box(sh.w*.16, sh.h*.205, sh.w*.69, sh.h*.535), size=132,
             color=ink, max_lines=4, align="left", track=-.03,
             leading=.89, min_read=31, min_contrast=1.7)
        text(sh, ctx, "demo_meta", "Normal Area / 03",
             Box(sh.w*.17, sh.h*.74, sh.w*.18, sh.h*.035), size=15,
             color=ink, display=False, align="left", track=.015,
             min_read=8, min_contrast=1.8)
        # The compact source-positioned globe stamp replaces its font label.
        cx, cy, r = sh.w*.375, sh.h*.785, sh.h*.052
        sh.cv.drawCircle(cx, cy, r, paint(C(ink)))
        land = skia.Path()
        land.moveTo(cx-r*.77, cy-r*.28)
        land.cubicTo(cx-r*.52, cy-r*.53, cx-r*.31, cy-r*.42, cx-r*.23, cy-r*.12)
        land.cubicTo(cx-r*.10, cy+r*.02, cx-r*.23, cy+r*.14, cx-r*.29, cy+r*.48)
        land.cubicTo(cx-r*.56, cy+r*.37, cx-r*.74, cy+r*.06, cx-r*.77, cy-r*.28)
        land.moveTo(cx+r*.03, cy-r*.48)
        land.cubicTo(cx+r*.20, cy-r*.53, cx+r*.25, cy-r*.36, cx+r*.43, cy-r*.31)
        land.cubicTo(cx+r*.52, cy-r*.13, cx+r*.37, cy-r*.02, cx+r*.32, cy+r*.10)
        land.cubicTo(cx+r*.44, cy+r*.34, cx+r*.28, cy+r*.49, cx+r*.09, cy+r*.46)
        land.cubicTo(cx-r*.03, cy+r*.23, cx+r*.02, cy+r*.04, cx-r*.09, cy-r*.08)
        land.cubicTo(cx-r*.21, cy-r*.25, cx-r*.10, cy-r*.39, cx+r*.03, cy-r*.48)
        land.close()
        sh.cv.drawPath(land, paint(C((239, 224, 190), .9)))
        sh.cv.drawCircle(cx, cy, r, paint(C(ink, .8),
                                            style=skia.Paint.kStroke_Style,
                                            width=1.0*sh.scale))
        sh.mark("demo_globe", Box(cx-r, cy-r, r*2, r*2), collide=False)

    @support("yearposter32", "the monumental red date poster with worn cream numerals and a narrow archival footer")
    def yearposter32(sh, ctx):
        P = ctx["pal"]
        texture_plate(sh, "T21458_04_distressed-red-paper.png",
                      mix((192, 34, 39), P["accent"], .035),
                      mix((139, 24, 31), P["accent2"], .035))
        text(sh, ctx, "year_top_left", "Type Study / 1982",
             Box(sh.w*.03, sh.h*.035, sh.w*.34, sh.h*.04), size=20,
             color=(255, 239, 220), display=False, align="left", track=.02,
             min_read=10)
        text(sh, ctx, "year_top_right", "Distressed Numerals",
             Box(sh.w*.66, sh.h*.035, sh.w*.31, sh.h*.04), size=19,
             color=(255, 239, 220), display=False, align="right", track=.015,
             min_read=10)
        year = support_copy(ctx, ("word",), "1982")
        text(sh, ctx, "year_title", year,
             Box(sh.w*.025, sh.h*.12, sh.w*.95, sh.h*.66), size=810,
             color=(250, 239, 216), min_read=160, track=-.055,
             distress=((112, 24, 26), .006, .40, .8))
        # Light horizontal rules and small date annotation preserve the source's poster restraint.
        line(sh, sh.w*.06, sh.h*.83, sh.w*.94, sh.h*.83,
             (247, 220, 202), 1.5, .84)
        text(sh, ctx, "year_bottom_left", "Archive / Print Series",
             Box(sh.w*.06, sh.h*.87, sh.w*.56, sh.h*.05), size=23,
             color=(255, 239, 220), display=False, align="left", track=.15,
             min_read=12)
        text(sh, ctx, "year_bottom_right", "No. 082",
             Box(sh.w*.72, sh.h*.87, sh.w*.22, sh.h*.05), size=23,
             color=(255, 239, 220), display=False, align="right", track=.12,
             min_read=12)

    @support("stadiumposter32", "the red stadium broadside with towering two-line sports lettering and a ghosted crowd field")
    def stadiumposter32(sh, ctx):
        red, light = (184, 34, 40), (246, 235, 218)
        texture_plate(sh, "T21458_11_stadium-red-print.png", red,
                      (129, 20, 29))
        text(sh, ctx, "stadium_top_left", "YWFT Becks",
             Box(sh.w*.03, sh.h*.035, sh.w*.44, sh.h*.04), size=19,
             color=light, display=False, align="left", track=.025,
             min_read=10)
        text(sh, ctx, "stadium_top_right", "A Distressed OpenType SVG Font",
             Box(sh.w*.63, sh.h*.035, sh.w*.34, sh.h*.04), size=18,
             color=light, display=False, align="right", track=.015,
             min_read=9)
        text(sh, ctx, "stadium_word1", "Real",
             Box(sh.w*.02, sh.h*.07, sh.w*.56, sh.h*.46), size=560,
             color=light, min_read=82, track=-.045,
             distress=((127, 20, 28), .005, .40, .8))
        text(sh, ctx, "stadium_word2", "Madrid",
             Box(sh.w*.20, sh.h*.50, sh.w*.78, sh.h*.46), size=560,
             color=light, min_read=82, track=-.055,
             distress=((127, 20, 28), .005, .40, .8))
        text(sh, ctx, "stadium_footer_left", "Designed By YouWorkForThem",
             Box(sh.w*.03, sh.h*.955, sh.w*.40, sh.h*.035), size=17,
             color=light, display=False, align="left", track=.02,
             min_read=9)
        text(sh, ctx, "stadium_footer_right", "Exclusive",
             Box(sh.w*.73, sh.h*.955, sh.w*.24, sh.h*.035), size=17,
             color=light, display=False, align="right", track=.02,
             min_read=9)

    @support("signalclock32", "the black digital-price graphic with angular numerals, decimal point, and a red chamfered label")
    def signalclock32(sh, ctx):
        ground(sh.cv, (0, 0, 0), (0, 0, 0), w=sh.w, h=sh.h)
        value = "$50.50"
        text(sh, ctx, "signal_value", value,
             Box(sh.w*.14, sh.h*.14, sh.w*.76, sh.h*.72), size=660,
             color=(248, 247, 244), min_read=105, track=-.06)
        plaque = Box(sh.w*.72, sh.h*.535, sh.w*.19, sh.h*.155)
        path = skia.Path()
        path.moveTo(plaque.x+plaque.w*.10, plaque.y)
        path.lineTo(plaque.r-plaque.w*.10, plaque.y)
        path.lineTo(plaque.r, plaque.y+plaque.h*.16)
        path.lineTo(plaque.r, plaque.b-plaque.h*.16)
        path.lineTo(plaque.r-plaque.w*.10, plaque.b)
        path.lineTo(plaque.x+plaque.w*.10, plaque.b)
        path.lineTo(plaque.x, plaque.b-plaque.h*.16)
        path.lineTo(plaque.x, plaque.y+plaque.h*.16)
        path.close()
        sh.cv.drawPath(path, paint(C((199, 20, 31))))
        sh.mark("signal_plaque", plaque, collide=False)
        text(sh, ctx, "signal_currency", "Dollar",
             Box(plaque.x+plaque.w*.04, plaque.y+plaque.h*.12,
                 plaque.w*.92, plaque.h*.76), size=68,
             color=(255, 255, 255), display=False, track=-.025,
             min_read=20, min_contrast=3.0, collide=False)
