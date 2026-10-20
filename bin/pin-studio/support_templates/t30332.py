"""Skia remakes of the T30332 supporting-image references.

The module is deliberately independent of pin_studio.py.  Its caller supplies
the renderer API to register(); the registered bodies close over that API and
keep the public template signature at (sh, ctx).
"""

import math


def _box(g, x, y, w, h):
    return g["Box"](x, y, w, h)


def _safe_mark(sh, g, name, x, y, w, h, bleed=False):
    sh.mark(name, _box(g, x, y, w, h), collide=False, bleed=bleed)


def _rect(g, sh, x, y, w, h, color, alpha=1.0, stroke=None, sw=1.0):
    skia = g["skia"]
    cv = sh.cv
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), g["paint"](g["C"](color, alpha)))
    if stroke is not None:
        cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h),
                    g["paint"](g["C"](stroke), style=skia.Paint.kStroke_Style,
                               width=sw))


def _round_rect(g, sh, x, y, w, h, radius, color, alpha=1.0,
                stroke=None, sw=1.0):
    skia = g["skia"]
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    sh.cv.drawRoundRect(rect, radius, radius,
                        g["paint"](g["C"](color, alpha)))
    if stroke is not None:
        sh.cv.drawRoundRect(rect, radius, radius,
                            g["paint"](g["C"](stroke),
                                       style=skia.Paint.kStroke_Style,
                                       width=sw))


def _line(g, sh, x1, y1, x2, y2, color, width=2.0, alpha=1.0):
    g["rule"](sh.cv, x1, y1, x2, y2, color, width, alpha)


def _text(g, sh, key, face, text, box, hi, color, *, lo=None,
          max_lines=2, align="center", valign="middle", track=0.0,
          min_read=None, min_contrast=4.5, alpha=1.0, bleed=False):
    # Fixed labels can accidentally equal a product name too; run every visible
    # string through the same name guard while retaining intentional line breaks.
    ctx = getattr(sh, "_t30332_ctx", None)
    if ctx is not None:
        text = "\n".join(g["_support_copy"](ctx, (), line)
                         for line in str(text).splitlines())
    scale = sh.scale
    return sh.text(
        key, face, text, box,
        hi=hi * scale,
        lo=(lo if lo is not None else max(14.0, hi * 0.28)) * scale,
        max_lines=max_lines, color=color, align=align, valign=valign,
        track=track, min_read=(min_read if min_read is not None else hi * 0.24) * scale,
        min_contrast=min_contrast, alpha=alpha, bleed=bleed)


def _outlined_text(g, sh, key, face, text, box, hi, fill, outline, *,
                   stroke=2.0, lo=None, track=0.0, min_read=None,
                   min_contrast=0.0):
    """Draw a normal, validated text slot, then stroke its exact glyph path."""
    size = _text(g, sh, key, face, text, box, hi, fill, lo=lo,
                 max_lines=1, track=track, min_read=min_read,
                 min_contrast=min_contrast)
    if size is None:
        return None
    ctx = getattr(sh, "_t30332_ctx", None)
    phrase = (g["_support_copy"](ctx, (), str(text)) if ctx is not None
              else str(text))
    tracking = hi * sh.scale * track
    path, _ = face.path(phrase, size, tracking=tracking)
    bounds = path.getBounds()
    ink = sh.slots[-1].ink
    sh.cv.save()
    sh.cv.translate(ink.x - bounds.x(), ink.y - bounds.y())
    sh.cv.drawPath(path, g["paint"](
        g["C"](outline), style=g["skia"].Paint.kStroke_Style,
        width=stroke * sh.scale))
    sh.cv.drawPath(path, g["paint"](g["C"](fill)))
    sh.cv.restore()
    return size


def _vertical_text(g, sh, ctx, key, face, text, cx, cy, length, hi,
                   color, track=0.0):
    """Typeset one line bottom-to-top and mark its true rotated bounds."""
    phrase = g["_support_copy"](ctx, (), str(text))
    tracking = hi * sh.scale * track
    size = face.fit(phrase, hi * sh.scale, length, tracking=tracking)
    path, _ = face.path(phrase, size, tracking=tracking)
    bounds = path.getBounds()
    sh.cv.save()
    sh.cv.translate(cx, cy)
    sh.cv.rotate(-90)
    sh.cv.translate(-bounds.centerX(), -bounds.centerY())
    sh.cv.drawPath(path, g["paint"](g["C"](color)))
    sh.cv.restore()
    sh.mark(key, _box(g, cx - bounds.height() / 2,
                      cy - bounds.width() / 2, bounds.height(),
                      bounds.width()), collide=False)
    return size


def _backdrop(g, sh, ctx, top, bottom, *, pool=None, grain=0,
              grain_color=None):
    P = ctx["pal"]
    seed = int(ctx.get("th", {}).get("seed", 7))
    g["ground"](sh.cv, top, bottom, sh.w, sh.h)
    if pool:
        g["light_pool"](sh.cv, sh.w * 0.73, sh.h * 0.18,
                        int(sh.h * 0.82), P["accent"], strength=pool,
                        mode=g["skia"].BlendMode.kScreen, w=sh.w, h=sh.h)
    if grain:
        g["speckle"](sh.cv, grain_color or P["glow"], n=grain, seed=seed,
                      alpha=0.065, rad=max(1.0, 1.2 * sh.scale),
                      w=sh.w, h=sh.h)
    _safe_mark(sh, g, "ground", 0, 0, sh.w, sh.h, bleed=True)


def _star(g, sh, cx, cy, radius, color, *, points=8, inner=0.22,
          stroke=None, sw=2.0, alpha=1.0):
    skia = g["skia"]
    path = skia.Path()
    count = points * 2
    for i in range(count):
        angle = -math.pi / 2 + math.pi * i / points
        r = radius if i % 2 == 0 else radius * inner
        x, y = cx + math.cos(angle) * r, cy + math.sin(angle) * r
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    q = g["paint"](g["C"](color, alpha))
    if stroke is not None:
        q.setStyle(skia.Paint.kStroke_Style)
        q.setStrokeWidth(sw)
    sh.cv.drawPath(path, q)
    _safe_mark(sh, g, "spark", cx - radius, cy - radius,
               2 * radius, 2 * radius)


def _pixel_spark(g, sh, cx, cy, unit, color):
    """Eight-bit cross sparkle used by the T30332 portrait specimen."""
    skia = g["skia"]
    rows = ("00011000", "00011000", "00011000", "11111111",
            "11111111", "00011000", "00011000", "00011000")
    q = g["paint"](g["C"](color))
    x0, y0 = cx - 4*unit, cy - 4*unit
    for row, bits in enumerate(rows):
        for col, bit in enumerate(bits):
            if bit == "1":
                sh.cv.drawRect(skia.Rect.MakeXYWH(x0+col*unit,
                                                   y0+row*unit,
                                                   unit, unit), q)
    _safe_mark(sh, g, "pixel_spark", x0, y0, 8*unit, 8*unit)


def _pixel_heart(g, sh, x, y, unit, color):
    rows = ("01100110", "11111111", "11111111", "01111110",
            "00111100", "00011000")
    q = g["paint"](g["C"](color))
    for r, row in enumerate(rows):
        for c, bit in enumerate(row):
            if bit == "1":
                sh.cv.drawRect(g["skia"].Rect.MakeXYWH(
                    x + c * unit, y + r * unit, unit, unit), q)


def _pixel_sunrise(g, sh, x, y, w, h):
    """A compact sunset scene built from hard-edged, square colour cells."""
    skia = g["skia"]
    cols, rows = 64, 22
    cw, ch = w / cols, h / rows
    sky = (255, 211, 173)
    warm = (249, 146, 165)
    pale = (255, 233, 197)
    sea = (247, 133, 178)
    sea2 = (237, 102, 164)
    mountain = (46, 62, 86)
    dolphin_rows = (
        "000000111100000000", "000011111111000000",
        "001111111111110000", "111111111111111000",
        "001111111111111100", "000011111110011110",
        "000001110000000110")
    paints = {}
    for r in range(rows):
        for c in range(cols):
            col = None
            if r < 13:
                col = sky if r < 7 else pale
                # Pixel-cloud silhouettes, in three broad broken banks.
                cloud = ((r in (2, 3, 4) and 4 <= c <= 19) or
                         (r in (4, 5, 6) and 22 <= c <= 39) or
                         (r in (2, 3, 4, 5) and 43 <= c <= 60))
                if cloud and ((c + r * 3) % 5 != 0):
                    col = warm
                # A small block-built sun sits above the distant ridge.
                if 29 <= c <= 35 and 5 <= r <= 10:
                    col = (255, 196, 93)
            else:
                col = sea if (r + c // 7) % 4 else sea2
                # Distant dark hills meet the water in staggered pixels.
                ridge = 13 + int(2 * math.sin(c * 0.23))
                if r == ridge or (r == ridge + 1 and c % 7 < 3):
                    col = mountain
            # A jumping dolphin silhouette, offset slightly above the horizon.
            dc, dr = c - 24, r - 8
            if 0 <= dr < len(dolphin_rows) and 0 <= dc < len(dolphin_rows[dr]):
                if dolphin_rows[dr][dc] == "1":
                    col = (93, 137, 196)
            if col is not None:
                if col not in paints:
                    paints[col] = g["paint"](g["C"](col))
                sh.cv.drawRect(skia.Rect.MakeXYWH(
                    x + c * cw, y + r * ch, cw + 0.6, ch + 0.6), paints[col])


def _pixel_sea_card(g, sh, x, y, w, h):
    """Pastel 8-bit sky, block clouds, a pixel sun, water, and a leaping dolphin."""
    skia = g["skia"]
    cols, rows = 72, 25
    cw, ch = w / cols, h / rows
    dolphin = (
        "000000001100000", "000001111111000", "000111111111110",
        "111111111111111", "001111111111110", "000011110011100",
        "000001100000000")
    paints = {}
    for r in range(rows):
        for c in range(cols):
            color = (255, 222, 191) if r < 13 else (250, 164, 190)
            if r in (3, 4, 5, 6) and ((6 <= c <= 18) or (23 <= c <= 34)
                                      or (45 <= c <= 63)) and (c + r) % 4:
                color = (255, 174, 194)
            if 33 <= c <= 38 and 2 <= r <= 8:
                color = (255, 235, 153)
            if r == 12 and c % 5:
                color = (255, 198, 187)
            if r >= 14:
                color = ((247, 143, 190) if (c // 4 + r) % 3
                         else (255, 191, 192))
            # Horizon and pixel wave highlights.
            if r in (13, 18, 21) and (c % 8) in (1, 2, 3, 4, 5):
                color = (255, 225, 207)
            # Dolphin silhouette facing right, clear of the pixel horizon.
            dx, dy = c - 28, r - 10
            if 0 <= dy < len(dolphin) and 0 <= dx < len(dolphin[dy]):
                if dolphin[dy][dx] == "1":
                    color = (105, 147, 211)
            if color not in paints:
                paints[color] = g["paint"](g["C"](color))
            sh.cv.drawRect(skia.Rect.MakeXYWH(
                x + c * cw, y + r * ch, cw + 0.5, ch + 0.5), paints[color])


def _flower(g, sh, cx, cy, size, petal, center, leaf):
    skia = g["skia"]
    q = g["paint"](g["C"](petal))
    for ox, oy in ((0, -1), (1, 0), (0, 1), (-1, 0),
                   (.7, -.7), (.7, .7), (-.7, .7), (-.7, -.7)):
        sh.cv.drawCircle(cx + ox * size * .55, cy + oy * size * .55,
                         size * .34, q)
    sh.cv.drawCircle(cx, cy, size * .20, g["paint"](g["C"](center)))
    stem = skia.Path()
    stem.moveTo(cx, cy + size * .48)
    stem.cubicTo(cx - size * .08, cy + size * 1.1,
                 cx + size * .12, cy + size * 1.6,
                 cx + size * .02, cy + size * 2.1)
    sh.cv.drawPath(stem, g["paint"](g["C"](leaf),
                                    style=skia.Paint.kStroke_Style,
                                    width=max(2.5, size * .11)))
    for direction in (-1, 1):
        leaf_path = skia.Path()
        yy = cy + size * (1.10 if direction < 0 else 1.50)
        leaf_path.moveTo(cx, yy)
        leaf_path.cubicTo(cx + direction * size * .42, yy - size * .35,
                          cx + direction * size * .70, yy - size * .10,
                          cx + direction * size * .66, yy + size * .10)
        leaf_path.cubicTo(cx + direction * size * .39, yy + size * .20,
                          cx + direction * size * .16, yy + size * .10, cx, yy)
        leaf_path.close()
        sh.cv.drawPath(leaf_path, g["paint"](g["C"](leaf)))


def _ovalword32(g, sh, ctx):
    P = ctx["pal"]
    skia = g["skia"]
    art = _load_image(g, sh, "materials/T30332_00-clean-pastel-background.png",
                      "ovalword32")
    if art is None:
        return
    sh.cv.drawImageRect(art, skia.Rect.MakeWH(art.width(), art.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    _safe_mark(sh, g, "reference_pastel_ground", 0, 0, sh.w, sh.h, bleed=True)
    _text(g, sh, "oval_meta", ctx["label"], "T&N Type Co.",
          _box(g, sh.w * .12, sh.h * .08, sh.w * .76, sh.h * .085),
          36, P["ink"], max_lines=1, track=.20, min_read=21)
    # The fill is slightly oversize to cover the original specimen word and
    # its oval edge; a fresh measured outline restores the source's silhouette.
    cover = skia.Rect.MakeXYWH(sh.w * .050, sh.h * .261,
                               sh.w * .908, sh.h * .444)
    sh.cv.drawOval(cover, g["paint"](g["C"]((255, 255, 255))))
    oval = skia.Rect.MakeXYWH(sh.w * .055, sh.h * .267,
                              sh.w * .898, sh.h * .43)
    sh.cv.drawOval(oval, g["paint"](g["C"]((255, 255, 255))))
    sh.cv.drawOval(oval, g["paint"](g["C"]((22, 24, 30)),
                                    style=skia.Paint.kStroke_Style,
                                    width=4 * sh.scale))
    sh.mark("oval", _box(g, oval.left(), oval.top(), oval.width(),
                          oval.height()), collide=False)
    phrase = g["panel_text"](ctx, ("Sadie",))
    _text(g, sh, "oval_word", ctx["display"], phrase,
          _box(g, sh.w * .105, sh.h * .325, sh.w * .79, sh.h * .30),
          430, (16, 17, 21), max_lines=1, min_read=100, track=-.025)
    _text(g, sh, "oval_caption", ctx["label"], "Display Sans",
          _box(g, sh.w * .12, sh.h * .775, sh.w * .76, sh.h * .085),
          42, P["ink"], max_lines=1, track=.13, min_read=24)


def _stardust32(g, sh, ctx):
    skia = g["skia"]
    image = _load_image(g, sh, "materials/T30332_01_stardust-photo.png",
                        "stardust32")
    if image is None:
        _backdrop(g, sh, ctx, (42, 43, 43), (15, 16, 18), grain=900)
    else:
        sh.cv.drawImageRect(image, skia.Rect.MakeWH(image.width(), image.height()),
                            skia.Rect.MakeWH(sh.w, sh.h),
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        _safe_mark(sh, g, "portrait", 0, 0, sh.w, sh.h, bleed=True)
        sh.cv.drawRect(skia.Rect.MakeXYWH(0, 0, sh.w, sh.h),
                       g["paint"](g["C"]((9, 12, 17), .24)))
    _text(g, sh, "stardust_eyebrow", ctx["label"],
          g["lead_in"](ctx, ("Stories in light", "A little after dark",
                             "Portraits and type" )).title(),
          _box(g, sh.w * .09, sh.h * .055, sh.w * .82, sh.h * .075),
          33, (255, 255, 255), max_lines=1, track=.20, min_read=20)
    phrase = g["_support_copy"](ctx, (),
                                "Stardust\nAnd Stories\nStudio")
    _text(g, sh, "stardust_headline", ctx["display"], phrase,
          _box(g, sh.w * .075, sh.h * .18, sh.w * .85, sh.h * .62),
          300, (255, 255, 255), max_lines=4, min_read=82, track=-.015)
    # The reference uses a tiny checker strip, not a long editorial rule.
    cell = 11 * sh.scale
    cols, rows = 12, 2
    sx = (sh.w-cols*cell)/2
    sy = sh.h*.855
    for r in range(rows):
        for c in range(cols):
            color = (245, 245, 240) if (r+c)%2 == 0 else (24, 26, 29)
            sh.cv.drawRect(skia.Rect.MakeXYWH(sx+c*cell, sy+r*cell,
                                               cell, cell),
                           g["paint"](g["C"](color)))
    _safe_mark(sh, g, "pixel_checker", sx, sy, cols*cell, rows*cell)
    _text(g, sh, "stardust_footer", ctx["label"], "Light  /  Texture  /  Type",
          _box(g, sh.w * .10, sh.h * .895, sh.w * .80, sh.h * .065),
          26, (255, 255, 255), max_lines=1, track=.12, min_read=16)
    for cx, cy, unit, color in (
            (sh.w * .13, sh.h * .15, 7 * sh.scale, (255, 255, 255)),
            (sh.w * .91, sh.h * .17, 9 * sh.scale, (255, 203, 62)),
            (sh.w * .16, sh.h * .84, 6 * sh.scale, (255, 203, 62)),
            (sh.w * .92, sh.h * .85, 6 * sh.scale, (255, 255, 255))):
        _pixel_spark(g, sh, cx, cy, unit, color)


def _cliffpostcard32(g, sh, ctx):
    skia = g["skia"]
    image = _load_image(g, sh,
                        "materials/T30332_02-clean-postcard-background.png",
                        "cliffpostcard32")
    if image is None:
        return
    sh.cv.drawImageRect(image, skia.Rect.MakeWH(image.width(), image.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    _safe_mark(sh, g, "clean_torn_postcard", 0, 0, sh.w, sh.h, bleed=True)
    _text(g, sh, "cliff_headline_1", ctx["display"], "Wander where",
          _box(g, sh.w * .13, sh.h * .195, sh.w * .74, sh.h * .13),
          235, (12, 15, 18), max_lines=1, min_read=68, track=-.02)
    _text(g, sh, "cliff_headline_2", ctx["display"], "your soul feels wild.",
          _box(g, sh.w * .075, sh.h * .335, sh.w * .85, sh.h * .13),
          235, (12, 15, 18), max_lines=1, min_read=68, track=-.02)
    _text(g, sh, "cliff_left", ctx["label"], "Open Air / Study 02",
          _box(g, sh.w * .10, sh.h * .655, sh.w * .36, sh.h * .06),
          24, (24, 31, 33), max_lines=1, align="left", track=.10,
          min_read=15)
    _text(g, sh, "cliff_right", ctx["label"], "Land  /  Sea  /  Sky",
          _box(g, sh.w * .55, sh.h * .655, sh.w * .35, sh.h * .06),
          24, (24, 31, 33), max_lines=1, align="right", track=.10,
          min_read=15)


def _load_image(g, sh, relpath, slug):
    root = g["Path"](g["SUPPORT_REF_DIR"])
    path = root / relpath
    if not path.is_file():
        sh.problems.append(f"{slug}: missing image asset {path}")
        return None
    try:
        image = g["skia"].Image.open(str(path))
    except Exception as exc:
        sh.problems.append(f"{slug}: image decode failed for {path}: {exc}")
        return None
    if image is None or image.width() <= 0 or image.height() <= 0:
        sh.problems.append(f"{slug}: image decode failed for {path}")
        return None
    return image


def _kindersea32(g, sh, ctx):
    skia = g["skia"]
    plate = _load_image(g, sh,
                        "materials/T30332_04-clean-lavender-plate.png",
                        "kindersea32")
    if plate is None:
        return
    sh.cv.drawImageRect(plate,
                        skia.Rect.MakeWH(plate.width(), plate.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
    _safe_mark(sh, g, "source_lavender_stock", 0, 0, sh.w, sh.h,
               bleed=True)

    # Keep the illustration as its own clean layer: this exact source crop has
    # the original dolphin, clouds, moon, water dithering and corner rainbow.
    x, y = sh.w * (112 / 1184), sh.h * (96 / 792)
    w, h = sh.w * (962 / 1184), sh.h * (396 / 792)
    art = _load_image(g, sh, "materials/T30332_04_pixel-sea-art.png",
                      "kindersea32")
    stars = _load_image(g, sh, "materials/T30332_04_corner-stars.png",
                        "kindersea32")
    if art is None or stars is None:
        return
    pixel_sampling = skia.SamplingOptions(skia.FilterMode.kNearest)
    sh.cv.drawImageRect(art, skia.Rect.MakeWH(art.width(), art.height()),
                        skia.Rect.MakeXYWH(x, y, w, h), pixel_sampling)
    sh.mark("source_pixel_seascape", _box(g, x, y, w, h), collide=False)
    # The two gold/navy sparkles are source-extracted transparent pixels, so
    # they cross the card edge in the same places as the reference.
    sh.cv.drawImageRect(stars,
                        skia.Rect.MakeWH(stars.width(), stars.height()),
                        skia.Rect.MakeWH(sh.w, sh.h), pixel_sampling)

    _text(g, sh, "kinder_top_label", ctx["label"], "Field Notes",
          _box(g, sh.w * .095, sh.h * .071, sh.w * .30, sh.h * .045),
          22, (255, 255, 255), max_lines=1, align="left", min_read=14,
          track=.08, min_contrast=2.5)
    side = g["_support_copy"](ctx, (), "Postcard")
    side_size, side_track = 20 * sh.scale, 2.0 * sh.scale
    side_width = ctx["label"].measure(side, side_size, side_track)
    side_x, side_y = sh.w * .927, sh.h * .595
    sh.cv.save()
    sh.cv.translate(side_x, side_y)
    sh.cv.rotate(-90)
    g["label"](sh.cv, ctx["label"], side, 0, 0, side_size,
               (255, 255, 255), tracking=side_track)
    sh.cv.restore()
    _safe_mark(sh, g, "kinder_side_label", side_x - 18 * sh.scale,
               side_y - side_width, 22 * sh.scale, side_width)

    phrase_a = g["_support_copy"](ctx, (), "I Wish You")
    phrase_b = g["_support_copy"](ctx, (), "A Kinder Sea.")
    _text(g, sh, "kinder_headline_1", ctx["display"], phrase_a,
          _box(g, sh.w * .145, sh.h * .648, sh.w * .71, sh.h * .13),
          225, (255, 255, 255), max_lines=1, min_read=68, track=-.012,
          min_contrast=2.5)
    _text(g, sh, "kinder_headline_2", ctx["display"], phrase_b,
          _box(g, sh.w * .095, sh.h * .798, sh.w * .81, sh.h * .14),
          225, (255, 255, 255), max_lines=1, min_read=68, track=-.012,
          min_contrast=2.5)


def _messageframe32(g, sh, ctx):
    skia = g["skia"]
    plate = _load_image(g, sh,
                        "materials/T30332_05-clean-message-plate.png",
                        "messageframe32")
    if plate is None:
        return
    # Retain the exact source stock, framed paper, pinheads, hearts, sparkles and
    # dot fields. Only the overprinted quote and identifying labels were removed.
    sh.cv.drawImageRect(plate,
                        skia.Rect.MakeWH(plate.width(), plate.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
    _safe_mark(sh, g, "source_message_plate", 0, 0, sh.w, sh.h,
               bleed=True)

    _text(g, sh, "message_top_label", ctx["label"], "Field Notes",
          _box(g, sh.w * .145, sh.h * .073, sh.w * .26, sh.h * .05),
          24, (255, 255, 255), max_lines=1, align="left", track=.08,
          min_read=14, min_contrast=2.5)
    for index, (phrase, x, width, y) in enumerate((
            ("You Will Look Back", .12, .76, .245),
            ("On These Days And", .12, .76, .375),
            ("Be So Grateful You", .12, .76, .505),
            ("Made It Through", .18, .64, .635))):
        _text(g, sh, f"message_quote_{index+1}", ctx["display"], phrase,
              _box(g, sh.w * x, sh.h * y, sh.w * width, sh.h * .125),
              138, (10, 10, 13), max_lines=1, valign="top",
              min_read=58, track=-.012)
    _text(g, sh, "message_signature", ctx["label"], "A Note To Keep",
          _box(g, sh.w * .70, sh.h * .865, sh.w * .20, sh.h * .05),
          21, (255, 255, 255), max_lines=1, align="right", track=.13,
          min_read=13, min_contrast=2.5)


def _contactlist32(g, sh, ctx):
    skia = g["skia"]
    plate = _load_image(g, sh,
                        "materials/T30332_06-clean-index-plate.png",
                        "contactlist32")
    if plate is None:
        return
    # This cleaned source plate retains the exact frame, nodes, tabs, and
    # pastel gradient; only the list copy and identifying footer labels were
    # removed for replacement with the active specimen font.
    sh.cv.drawImageRect(plate,
                        skia.Rect.MakeWH(plate.width(), plate.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    _safe_mark(sh, g, "source_index_plate", 0, 0, sh.w, sh.h,
               bleed=True)

    rows = (
        ("01.Misread", .120),
        ("02.Cayman Island", .211),
        ("03.Homesick", .302),
        ("04.Boat Behind", .393),
        ("05.Rumours", .484),
        ("06.Renegade", .575),
        ("07.Summer On", .666),
        ("The Westhill", .757),
    )
    navy = (26, 41, 60)
    for index, (phrase, y) in enumerate(rows):
        _text(g, sh, f"index_item{index+1}", ctx["display"], phrase,
              _box(g, sh.w * .12, sh.h * y, sh.w * .76, sh.h * .07),
              72, navy, max_lines=1, align="center", track=-.012,
              min_read=36)
    _text(g, sh, "index_tag", ctx["label"], "Track List",
          _box(g, sh.w * .805, sh.h * .849, sh.w * .114, sh.h * .035),
          18, navy, max_lines=1, min_read=11, track=.025)
    _text(g, sh, "index_subtag", ctx["label"], "No. 07",
          _box(g, sh.w * .825, sh.h * .922, sh.w * .074, sh.h * .026),
          17, navy, max_lines=1, min_read=10, track=.025)


def _sunsetpromise32(g, sh, ctx):
    skia = g["skia"]
    plate = _load_image(g, sh,
                        "materials/T30332_07-clean-sunset-background.png",
                        "sunsetpromise32")
    art = _load_image(g, sh,
                      "materials/T30332_07_pixel-sunset-art.png",
                      "sunsetpromise32")
    if plate is None or art is None:
        return
    sh.cv.drawImageRect(plate,
                        skia.Rect.MakeWH(plate.width(), plate.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    _safe_mark(sh, g, "source_sunset_plate", 0, 0, sh.w, sh.h,
               bleed=True)
    # Use the exact pixel-art crop, not a redraw; nearest-neighbour scaling
    # preserves the original grid while the clean plate supplies the texture.
    art_box = _box(g, sh.w * (54 / 1184), sh.h * (52 / 792),
                   sh.w * (436 / 1184), sh.h * (238 / 792))
    sh.cv.drawImageRect(art, skia.Rect.MakeWH(art.width(), art.height()),
                        skia.Rect.MakeXYWH(art_box.x, art_box.y,
                                           art_box.w, art_box.h),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
    sh.mark("source_pixel_sunset", art_box, collide=False)

    _text(g, sh, "sunset_header0", ctx["label"], "Field Notes",
          _box(g, sh.w * .585, sh.h * .106, sh.w * .16, sh.h * .058),
          18, (27, 43, 63), max_lines=1, track=.08, min_read=11)
    _text(g, sh, "sunset_header1", ctx["label"], "Dusk / 07",
          _box(g, sh.w * .77, sh.h * .106, sh.w * .12, sh.h * .058),
          17, (27, 43, 63), max_lines=1, track=.07, min_read=10)

    rows = (("Every", .305, .132),
            ("Sunset Brings", .455, .155),
            ("the Promise of", .63, .155),
            ("a New Day", .81, .15))
    for index, (phrase, y, height) in enumerate(rows):
        _outlined_text(
            g, sh, f"sunset_headline{index+1}", ctx["display"], phrase,
            _box(g, sh.w * .15, sh.h * y, sh.w * .80, sh.h * height),
            170, (255, 255, 255), (20, 24, 39), stroke=1.0,
            track=-.012, min_read=52, min_contrast=0.0)


def _phonegarden32(g, sh, ctx):
    skia = g["skia"]
    plate = _load_image(g, sh,
                        "materials/T30332_08-clean-phone-plate-no-lettering.png",
                        "phonegarden32")
    flower = _load_image(g, sh, "materials/T30332_08_left-peony-v2.png",
                         "phonegarden32")
    if plate is None or flower is None:
        return
    sh.cv.drawImageRect(plate,
                        skia.Rect.MakeWH(plate.width(), plate.height()),
                        skia.Rect.MakeWH(sh.w, sh.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    _safe_mark(sh, g, "source_phone_plate", 0, 0, sh.w, sh.h, bleed=True)
    ink = (10, 11, 15)
    cream = (253, 245, 229)

    # Replace the model-cleaned lower-left flower with the exact transparent
    # crop from the reference. The screen-color patch also clears the original
    # generated flower and the letter-free area behind the cutout.
    flower_patch = _box(g, sh.w * (110 / 1184), sh.h * (462 / 792),
                        sh.w * (185 / 1184), sh.h * (258 / 792))
    _rect(g, sh, flower_patch.x, flower_patch.y, flower_patch.w,
          flower_patch.h, cream)
    flower_box = _box(g, sh.w * (120 / 1184), sh.h * (465 / 792),
                      sh.w * (170 / 1184), sh.h * (150 / 792))
    sh.cv.drawImageRect(flower, skia.Rect.MakeWH(flower.width(), flower.height()),
                        skia.Rect.MakeXYWH(flower_box.x, flower_box.y,
                                           flower_box.w, flower_box.h),
                        skia.SamplingOptions(skia.FilterMode.kLinear,
                                             skia.MipmapMode.kLinear))
    sh.mark("source_peony", flower_box, collide=False)
    # The blue outlined dot just to the flower's left is separate furniture.
    sh.cv.drawCircle(sh.w * (194 / 1184), sh.h * (598 / 792),
                     4.2 * sh.scale,
                     g["paint"](g["C"]((19, 51, 77)),
                                style=skia.Paint.kStroke_Style,
                                width=1.5 * sh.scale))
    # Blank the two stars that sit behind fresh text so their exact-position
    # foreground redraws do not double with the backing-plate versions.
    sh.cv.drawCircle(sh.w * .165, sh.h * .222, sh.h * .038,
                     g["paint"](g["C"](cream)))
    sh.cv.drawCircle(sh.w * .565, sh.h * .19, sh.h * .075,
                     g["paint"](g["C"](cream)))

    # Left phone: the four-piece vertical lockup, then the repeated two-line
    # name beneath the source peony. The tiny pink star sits back inside the O.
    for index, (word, y) in enumerate((
            ("Con", .168), ("Vent", .270), ("Gard", .372), ("En", .474))):
        _text(g, sh, f"phone_left_word{index+1}", ctx["display"], word,
              _box(g, sh.w * .06, sh.h * y, sh.w * .225, sh.h * .09),
              94, ink, max_lines=1, track=-.035, min_read=34)
    _star(g, sh, sh.w * .165, sh.h * .222, sh.h * .025,
          (235, 99, 164), points=5, inner=.47, stroke=(235, 99, 164),
          sw=1.3 * sh.scale)
    _text(g, sh, "phone_left_repeat1", ctx["display"], "Convent",
          _box(g, sh.w * .055, sh.h * .77, sh.w * .23, sh.h * .055),
          57, ink, max_lines=1, track=-.035, min_read=24)
    _text(g, sh, "phone_left_repeat2", ctx["display"], "Garden",
          _box(g, sh.w * .055, sh.h * .85, sh.w * .23, sh.h * .055),
          57, ink, max_lines=1, track=-.035, min_read=24)

    # Center phone: two bottom-to-top word columns, with the source star kept
    # clear at their upper ends.
    for key, word, x in (("phone_mid_word1", "Convent", .415),
                         ("phone_mid_word2", "Garden", .568)):
        _vertical_text(g, sh, ctx, key, ctx["display"], word,
                       sh.w * x, sh.h * .505, sh.h * .69, 150, ink,
                       track=-.035)
    _star(g, sh, sh.w * .565, sh.h * .19, sh.h * .062,
          (255, 242, 151), points=8, inner=.42)
    _star(g, sh, sh.w * .565, sh.h * .19, sh.h * .062,
          (28, 51, 69), points=8, inner=.42,
          stroke=(28, 51, 69), sw=1.4 * sh.scale)

    # Right phone: a compact header above the original flower-and-sparkle
    # arrangement and the four-line garden message below it.
    _text(g, sh, "phone_right_title1", ctx["display"], "Convent",
          _box(g, sh.w * .715, sh.h * .15, sh.w * .255, sh.h * .052),
          48, ink, max_lines=1, track=-.04, min_read=22)
    _text(g, sh, "phone_right_title2", ctx["display"], "Garden",
          _box(g, sh.w * .715, sh.h * .225, sh.w * .255, sh.h * .052),
          48, ink, max_lines=1, track=-.04, min_read=22)
    for index, (phrase, y) in enumerate((
            ("Timeless", .600), ("Charm,", .673),
            ("Rooted In", .746), ("Grace.", .819))):
        _text(g, sh, f"phone_right_copy{index+1}", ctx["display"], phrase,
              _box(g, sh.w * .715, sh.h * y, sh.w * .255, sh.h * .066),
              52, ink, max_lines=1, track=-.025, min_read=22)

    # Neutral labels replace the vertical foundry/font labels in the source.
    _vertical_text(g, sh, ctx, "phone_left_meta", ctx["label"],
                   "Field Notes", sh.w * .336, sh.h * .505,
                   sh.h * .20, 20, ink, track=.07)
    _vertical_text(g, sh, ctx, "phone_right_meta", ctx["label"],
                   "Flora / 08", sh.w * .665, sh.h * .505,
                   sh.h * .18, 19, ink, track=.06)


def _pixelquote32(g, sh, ctx):
    skia = g["skia"]
    _rect(g, sh, 0, 0, sh.w, sh.h, (4, 4, 6))
    _safe_mark(sh, g, "black_field", 0, 0, sh.w, sh.h, bleed=True)
    hot = (244, 76, 157)
    # These exact transparent crops retain the reference's pixel geometry.
    # Positions are expressed in the source's 1184x792 coordinate system.
    materials = (
        ("pixel_stitches_top", "materials/T30332_09_pixel-stitches-top.png",
         889, 49, 235, 26),
        ("pixel_stitches_bottom", "materials/T30332_09_pixel-stitches-bottom.png",
         67, 720, 234, 26),
        ("pixel_heart", "materials/T30332_09_pixel-heart.png",
         495, 96, 49, 41),
        ("pixel_mascot", "materials/T30332_09_pixel-mascot.png",
         341, 689, 63, 57),
    )
    for name, relpath, x, y, w, h in materials:
        image = _load_image(g, sh, relpath, "pixelquote32")
        if image is None:
            continue
        dx, dy = sh.w / 1184, sh.h / 792
        sh.cv.drawImageRect(
            image, skia.Rect.MakeWH(image.width(), image.height()),
            skia.Rect.MakeXYWH(x * dx, y * dy, w * dx, h * dy),
            skia.SamplingOptions(skia.FilterMode.kNearest,
                                 skia.MipmapMode.kNone))
        _safe_mark(sh, g, name, x * dx, y * dy, w * dx, h * dy)

    # Preserve the quote and five-line hierarchy from the source; the font is
    # deliberately the active specimen face, not a rasterized source wordmark.
    lines = (
        ("A Little", .28, .169, .44, .132),
        ("Nonsense", .27, .302, .46, .132),
        ("Now & Then", .20, .435, .60, .132),
        ("is Relished by", .17, .570, .66, .132),
        ("the Wisest Man", .14, .72, .74, .132),
    )
    for index, (phrase, x, y, w, h) in enumerate(lines, 1):
        _text(g, sh, f"pixel_quote_{index}", ctx["display"], phrase,
              _box(g, sh.w * x, sh.h * y, sh.w * w, sh.h * h),
              250, hot, max_lines=1, min_read=52, track=-.018)


def _register_body(api, body, name):
    def fn(sh, ctx):
        sh._t30332_ctx = ctx
        try:
            return body(api, sh, ctx)
        finally:
            del sh._t30332_ctx
    fn.__name__ = f"t_{name}"
    return fn


def register(api):
    """Register the nine T30332 templates through the supplied renderer API."""
    templates = (
        ("ovalword32", "pearlescent pastel field, outlined oval and centered display phrase",
         _ovalword32),
        ("stardust32", "monochrome portrait plate with oversized editorial type and star marks",
         _stardust32),
        ("cliffpostcard32", "coastal photograph framed by torn pastel paper and a broadside phrase",
         _cliffpostcard32),
        ("kindersea32", "pixel seascape postcard above a lavender field and a hopeful phrase",
         _kindersea32),
        ("messageframe32", "textured source quote card with a framed four-line message and hearts",
         _messageframe32),
        ("contactlist32", "pastel index board with numbered display rows and pink frame details",
         _contactlist32),
        ("sunsetpromise32", "violet sunset poster with a framed pixel landscape and large type",
         _sunsetpromise32),
        ("phonegarden32", "three cream mobile screens with botanical editorial layouts",
         _phonegarden32),
        ("pixelquote32", "hot-pink display quote on black with an 8-bit heart and pixel rails",
         _pixelquote32),
    )
    for name, blurb, body in templates:
        api["support"](name, blurb)(_register_body(api, body, name))
