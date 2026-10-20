"""Photo led and image rich supporting templates.

The renderer supplies its drawing API so this catalogue can stay a small,
standalone module. Photographs are source material only; every visible word is
re-typeset through ``Sheet.text`` with the active font.
"""

import math


def register(api):
    support = api["support"]
    skia = api["skia"]
    C = api["C"]
    paint = api["paint"]
    rule = api["rule"]
    light_pool = api["light_pool"]
    Box = api["Box"]
    readable = api["readable"]
    mix = api["mix"]
    lum = api["lum"]
    gradient_fill = api["gradient_fill"]
    Path = api["Path"]
    arc_text = api["arc_text"]
    ref_dir = Path(api["SUPPORT_REF_DIR"])
    support_copy = api["_support_copy"]
    rolled = api["rolled"]
    lead_in = api["lead_in"]

    sampling = skia.SamplingOptions(skia.FilterMode.kLinear,
                                    skia.MipmapMode.kLinear)

    def image(sh, template, relative, box, crop=None, bleed=False,
              contain=False, alpha=1.0):
        """Read a reference/material image and place its requested crop."""
        path = ref_dir / relative
        if not path.exists():
            sh.problems.append(f"{template}: missing image {path}")
            return None
        try:
            img = skia.Image.open(str(path))
        except Exception as exc:
            sh.problems.append(f"{template}: could not decode {path.name}: {exc}")
            return None
        if img is None:
            sh.problems.append(f"{template}: could not decode {path.name}")
            return None
        src = (skia.Rect.MakeXYWH(*crop) if crop else
               skia.Rect.MakeWH(img.width(), img.height()))
        if contain:
            scale = min(box.w / src.width(), box.h / src.height())
            dw, dh = src.width() * scale, src.height() * scale
            dst = skia.Rect.MakeXYWH(box.x + (box.w-dw)/2,
                                     box.y + (box.h-dh)/2, dw, dh)
        else:
            dst = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        if alpha < 1.0:
            sh.cv.drawImageRect(img, src, dst, sampling,
                                paint(C((255, 255, 255), alpha)))
        else:
            sh.cv.drawImageRect(img, src, dst, sampling)
        sh.mark(f"{template}_image", box, collide=False, bleed=bleed)
        return img

    def rect(sh, box, rgb, alpha=1.0, radius=0):
        r = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        if radius:
            p = skia.Path()
            p.addRoundRect(r, radius, radius)
            sh.cv.drawPath(p, paint(C(rgb, alpha)))
        else:
            sh.cv.drawRect(r, paint(C(rgb, alpha)))

    def circle(sh, cx, cy, radius, rgb, alpha=1.0):
        sh.cv.drawCircle(cx, cy, radius, paint(C(rgb, alpha)))

    def image_background(sh, template, relative):
        return image(sh, template, relative, Box(0, 0, sh.w, sh.h), bleed=True)

    def theme_ink(ctx, ground_rgb):
        return readable(lum(ground_rgb), ctx["pal"]["accent"], 4.5)

    def starburst(cx, cy, outer, inner, points=16):
        p = skia.Path()
        for i in range(points * 2):
            a = -1.5707963267948966 + i * 3.141592653589793 / points
            r = outer if i % 2 == 0 else inner
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        return p

    @support("amberdawn32", "warm glass-block fashion photography with oversized lemon-yellow specimen lettering")
    def t_amberdawn32(sh, ctx):
        photo = image_background(sh, "amberdawn32",
                                 "materials/T24908_00_amber-dawn-photo.png")
        if photo is None:
            return
        # Keep the supplied glass-and-portrait plate bright; the reference is
        # not a night image, and its photograph should remain the main field.
        rect(sh, Box(0, 0, sh.w, sh.h), (8, 13, 15), .045)
        yellow = (255, 229, 28)
        label_ink = (255, 243, 194)
        accent_ink = mix(yellow, theme_ink(ctx, (12, 20, 21)), .14)
        badge_x, badge_y, badge_r = sh.w * .88, sh.h * .16, sh.h * .092
        ring = skia.Path()
        ring.addArc(skia.Rect.MakeXYWH(badge_x - badge_r * .76,
                                       badge_y - badge_r * .76,
                                       badge_r * 1.52, badge_r * 1.52),
                    96, 102)
        sh.cv.drawPath(ring, paint(C(yellow, .96),
                                   style=skia.Paint.kStroke_Style,
                                   width=3.0 * sh.scale))
        sh.mark("amber_badge_ring",
                Box(badge_x - badge_r, badge_y - badge_r,
                    badge_r * 2, badge_r * 2), collide=False)
        arc_text(sh, ctx["label"], "Three Fonts Included",
                 badge_x, badge_y, badge_r * 1.12, 20 * sh.scale,
                 up=True, color=yellow, track=.15 * sh.scale,
                 name="amber_badge_arc", collide=False)
        sh.text("amber_badge_sample", ctx["display"], "Aa",
                Box(badge_x - badge_r * .65, badge_y - badge_r * .34,
                    badge_r * 1.30, badge_r * .52),
                hi=53 * sh.scale, lo=32 * sh.scale, max_lines=1,
                color=yellow, min_read=27 * sh.scale, track=-.02,
                min_contrast=1.8)
        sh.text("amber_badge_label", ctx["label"], "Glyphs",
                Box(badge_x - badge_r * .75, badge_y + badge_r * .15,
                    badge_r * 1.50, badge_r * .28),
                hi=18 * sh.scale, lo=13 * sh.scale, max_lines=1,
                color=yellow, min_read=12 * sh.scale, track=.08,
                min_contrast=1.8)

        headline = "Golden\nHour"
        sh.text("amber_headline", ctx["display"], headline,
                Box(sh.w * .095, sh.h * .17, sh.w * .72, sh.h * .60),
                hi=400 * sh.scale, lo=94 * sh.scale, max_lines=2,
                color=yellow, min_read=64 * sh.scale, track=-.035,
                leading=.84, min_contrast=3.5)
        rule(sh.cv, sh.w * .405, sh.h * .835, sh.w * .585, sh.h * .835,
             accent_ink, 3.4 * sh.scale, .95)
        caption = support_copy(ctx, ("sub",), "Lively Brush Font")
        sh.text("amber_caption", ctx["label"], caption,
                Box(sh.w * .14, sh.h * .852, sh.w * .25, sh.h * .07),
                hi=35 * sh.scale, lo=20 * sh.scale, max_lines=1,
                color=label_ink, min_read=17 * sh.scale, align="left",
                track=.075)
        sh.text("amber_footer_right", ctx["label"], "By Set Sail Studios",
                Box(sh.w * .61, sh.h * .852, sh.w * .25, sh.h * .07),
                hi=35 * sh.scale, lo=20 * sh.scale, max_lines=1,
                color=label_ink, min_read=17 * sh.scale, align="right",
                track=.075)

    @support("skinbadge32", "two overlapping skincare-style paper seals over a soft beauty portrait")
    def t_skinbadge32(sh, ctx):
        photo = image_background(sh, "skinbadge32",
                                 "materials/T24908_01_clean-photo-background.png")
        if photo is None:
            return
        accent_ink = (243, 241, 235)
        # This one-pass clean plate follows the source's warm hair-and-skin
        # backdrop; opaque redraws replace the overprinted seals and wording.
        left = Box(sh.w * .082, sh.h * .125, sh.w * .503, sh.h * .75)
        right = Box(sh.w * .455, sh.h * .121, sh.w * .460, sh.h * .75)
        sh.cv.drawOval(skia.Rect.MakeXYWH(right.x, right.y, right.w, right.h),
                       paint(C((96, 42, 24))))
        # The source seal repeats its large brush phrase in clipped rows. Keep
        # each row inside the ellipse and let the front seal cover its left side.
        right_clip = skia.Path()
        right_clip.addOval(skia.Rect.MakeXYWH(right.x, right.y,
                                               right.w, right.h))
        right_cx = right.x + right.w/2
        right_cy = right.y + right.h/2
        sh.cv.save()
        sh.cv.clipPath(right_clip, doAntiAlias=True)
        sh.cv.translate(right_cx, right_cy)
        sh.cv.rotate(-13)
        sh.cv.translate(-right_cx, -right_cy)
        for i, yfrac in enumerate((-.02, .17, .36, .55, .74)):
            sh.text(f"skin_pattern{i}", ctx["display"], "Tribe  Tribe",
                    Box(right.x - right.w * .10,
                        right.y + right.h * yfrac,
                        right.w * 1.20, right.h * .18),
                    hi=205 * sh.scale, lo=44 * sh.scale, max_lines=1,
                    color=(218, 189, 252), min_read=36 * sh.scale,
                    track=-.025, collide=False)
        sh.cv.restore()
        sh.cv.drawOval(skia.Rect.MakeXYWH(left.x, left.y, left.w, left.h),
                       paint(C((184, 155, 249))))

        center_x = left.x + left.w / 2
        center_y = left.y + left.h / 2
        rim_r = left.h * .425
        arc_text(sh, ctx["label"], "Skin Care  •  Self Love",
                 center_x, center_y, rim_r, 36 * sh.scale,
                 up=True, color=accent_ink, track=.1 * sh.scale,
                 name="skin_badge_top_arc", collide=False)
        arc_text(sh, ctx["label"], "Self Love  •  Skin Care",
                 center_x, center_y, rim_r, 36 * sh.scale,
                 up=False, color=accent_ink, track=.1 * sh.scale,
                 name="skin_badge_bottom_arc", collide=False)
        star_r = left.h * .421
        star_size = 14 * sh.scale
        for angle in (0, 180):
            a = math.radians(angle)
            sx = center_x + math.cos(a) * star_r
            sy = center_y + math.sin(a) * star_r
            p = starburst(sx, sy, star_size, star_size * .22, points=4)
            sh.cv.drawPath(p, paint(C(accent_ink)))
            sh.mark("skin_badge_star",
                    Box(sx - star_size, sy - star_size,
                        star_size * 2, star_size * 2), collide=False)

        for name, wording, yfrac in (
                ("skin_badge_headline_top", "Skin", .20),
                ("skin_badge_headline_bottom", "Tribe", .45)):
            sh.text(name, ctx["display"], wording,
                    Box(left.x + left.w * .09, left.y + left.h * yfrac,
                        left.w * .82, left.h * .24),
                    hi=280 * sh.scale, lo=66 * sh.scale, max_lines=1,
                    color=accent_ink, min_read=42 * sh.scale,
                    track=-.04, min_contrast=1.8)
        ux0, ux1 = left.x + left.w * .31, left.x + left.w * .78
        uy, thick = left.y + left.h * .75, left.h * .034
        swash = skia.Path()
        swash.moveTo(ux0, uy + thick * .10)
        swash.cubicTo(left.x + left.w * .43, uy - thick * .20,
                      left.x + left.w * .63, uy + thick * .16,
                      ux1, uy - thick * .05)
        swash.cubicTo(left.x + left.w * .69, uy + thick * .48,
                      left.x + left.w * .43, uy + thick * .29,
                      ux0 + thick * .15, uy + thick * .66)
        swash.cubicTo(ux0 - thick * .10, uy + thick * .48,
                      ux0 - thick * .06, uy + thick * .20,
                      ux0, uy + thick * .10)
        swash.close()
        sh.cv.drawPath(swash, paint(C(accent_ink)))
        sh.mark("skin_badge_underline",
                Box(ux0 - thick * .1, uy - thick * .2,
                    ux1 - ux0 + thick * .1, thick * .9), collide=False)

    @support("latestlook32", "a red-jacket lookbook crop paired with a crisp high-fashion type page")
    def t_latestlook32(sh, ctx):
        if image_background(sh, "latestlook32",
                            "materials/T24908_02_clean-photo-background.png") is None:
            return
        ink = (255, 251, 244)
        for name, wording, x, y, width in (
                ("latest_intro", "Get The", .265, .13, .62),
                ("latest_headline", "Latest", .265, .35, .62),
                ("latest_lastline", "Style", .33, .57, .54)):
            sh.text(name, ctx["display"], wording,
                    Box(sh.w * x, sh.h * y, sh.w * width, sh.h * .22),
                    hi=312 * sh.scale, lo=76 * sh.scale, max_lines=1,
                    color=ink, min_read=56 * sh.scale, align="left",
                    track=-.025)
        rule(sh.cv, sh.w * .40, sh.h * .885, sh.w * .59, sh.h * .885,
             ink, 2.8 * sh.scale, .92)
        sh.text("latest_caption", ctx["label"], "Lively Brush Font",
                Box(sh.w * .27, sh.h * .875, sh.w * .27, sh.h * .065),
                hi=32 * sh.scale, lo=18 * sh.scale, max_lines=1,
                color=ink, min_read=15 * sh.scale, align="left", track=.06)
        sh.text("latest_signature", ctx["label"], "Autumn Lookbook",
                Box(sh.w * .62, sh.h * .875, sh.w * .22, sh.h * .065),
                hi=32 * sh.scale, lo=18 * sh.scale, max_lines=1,
                color=ink, min_read=15 * sh.scale, align="right", track=.06)

    @support("gelatocards32", "layered pink and cobalt gelato cards over a bright dessert-shop photograph")
    def t_gelatocards32(sh, ctx):
        photo = image_background(sh, "gelatocards32",
                                 "materials/T24908_03_gelato-background.png")
        if photo is None:
            return
        accent_ink = (255, 255, 255)
        # A thin milky wash lets the two saturated cards sit cleanly over the
        # photograph while leaving the cone and shop recognisable around them.
        rect(sh, Box(0, 0, sh.w, sh.h), (255, 249, 245), .10)
        back = Box(sh.w * .475, sh.h * .175, sh.w * .435, sh.h * .66)
        front = Box(sh.w * .135, sh.h * .13, sh.w * .51, sh.h * .70)
        rect(sh, Box(back.x + 12 * sh.scale, back.y + 18 * sh.scale,
                     back.w, back.h), (24, 31, 91), .28, 24 * sh.scale)
        rect(sh, Box(front.x + 12 * sh.scale, front.y + 18 * sh.scale,
                     front.w, front.h), (117, 46, 106), .25, 24 * sh.scale)

        def patterned_card(card, material, image_alpha, tint=None,
                           tint_alpha=0):
            path = ref_dir / "materials" / material
            if not path.is_file():
                sh.problems.append(f"gelatocards32: missing card pattern {path}")
                return
            art = skia.Image.open(str(path))
            if art is None:
                sh.problems.append(f"gelatocards32: could not decode card pattern {path}")
                return
            target_ratio = card.w/card.h
            source_ratio = art.width()/art.height()
            if source_ratio > target_ratio:
                crop_w = art.height()*target_ratio
                source = skia.Rect.MakeXYWH((art.width()-crop_w)/2, 0,
                                             crop_w, art.height())
            else:
                crop_h = art.width()/target_ratio
                source = skia.Rect.MakeXYWH(0, (art.height()-crop_h)/2,
                                             art.width(), crop_h)
            clip = skia.Path()
            clip.addRoundRect(skia.Rect.MakeXYWH(card.x, card.y,
                                                  card.w, card.h),
                              24 * sh.scale, 24 * sh.scale)
            sh.cv.save()
            sh.cv.clipPath(clip, skia.ClipOp.kIntersect, True)
            pattern_paint = paint()
            pattern_paint.setAlphaf(image_alpha)
            sh.cv.drawImageRect(art, source,
                                skia.Rect.MakeXYWH(card.x, card.y,
                                                   card.w, card.h), sampling,
                                pattern_paint)
            if tint is not None and tint_alpha > 0:
                rect(sh, card, tint, tint_alpha)
            sh.cv.restore()
            sh.mark(f"gelato_{material.removesuffix('.png')}", card,
                    collide=False)

        # These are the user's prepared repeat patterns. Their pale linework is
        # printed as a quiet texture over the source-matched card colors so it
        # supports, rather than competes with, the specimen wording.
        rect(sh, back, (38, 79, 218), 1, 24 * sh.scale)
        rect(sh, front, (255, 191, 215), 1, 24 * sh.scale)
        patterned_card(back, "T24908_03_blue-ice-cream-pattern.png", .18)
        patterned_card(front, "T24908_03_crimson-ice-cream-pattern.png",
                       .24, (255, 191, 215), .42)

        exposed_x = front.r + 18 * sh.scale
        exposed_w = max(120.0, back.r - exposed_x - 18 * sh.scale)
        sh.text("gelato_back_top", ctx["label"], "Scoop  /  Shop",
                Box(exposed_x, back.y + back.h * .075,
                    exposed_w, back.h * .09),
                hi=33 * sh.scale, lo=17 * sh.scale, max_lines=1,
                color=(255, 255, 246), min_read=15 * sh.scale,
                track=.06)
        sh.text("gelato_back_phrase", ctx["display"], "Sweet Scoops",
                Box(exposed_x, back.y + back.h * .34,
                    exposed_w, back.h * .28),
                hi=105 * sh.scale, lo=34 * sh.scale, max_lines=2,
                color=(255, 255, 250), min_read=30 * sh.scale,
                track=-.035)
        sh.text("gelato_front_label", ctx["label"], "Pastel  /  Frozen",
                Box(front.x + front.w * .08, front.y + front.h * .09,
                    front.w * .84, front.h * .08),
                hi=31 * sh.scale, lo=16 * sh.scale, max_lines=1,
                color=(35, 66, 191), min_read=14 * sh.scale,
                align="left", track=.04)
        rule(sh.cv, front.x + front.w * .08, front.y + front.h * .22,
             front.x + front.w * .92, front.y + front.h * .22,
             accent_ink, 2.2 * sh.scale, .9)
        sh.text("gelato_front_headline", ctx["display"], "Sweet\nScoops",
                Box(front.x + front.w * .08, front.y + front.h * .29,
                    front.w * .84, front.h * .37),
                hi=198 * sh.scale, lo=60 * sh.scale, max_lines=3,
                color=(37, 74, 209), min_read=40 * sh.scale,
                track=-.04, leading=.83)
        sh.text("gelato_front_footer", ctx["label"], "A Little Joy In Every Scoop",
                Box(front.x + front.w * .08, front.y + front.h * .83,
                    front.w * .84, front.h * .075),
                hi=27 * sh.scale, lo=15 * sh.scale, max_lines=1,
                color=(35, 66, 191), min_read=13 * sh.scale,
                track=.02)

    @support("meditation32", "a pastel meditation workshop poster with a clean stone-and-water photograph inset")
    def t_meditation32(sh, ctx):
        top, bottom = (230, 168, 213), (137, 195, 231)
        accent_ink = (255, 255, 255)
        p = paint()
        p.setShader(gradient_fill(top, bottom, 0, sh.h, tilt=sh.w * .25))
        sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), p)
        # Soft pools restore the source's broad pastel colour shifts. Its
        # original fine-grain texture is not present in the prepared materials.
        light_pool(sh.cv, sh.w * .10, sh.h * .36, sh.w * .43,
                   (240, 157, 198), .18, skia.BlendMode.kScreen, sh.w, sh.h)
        light_pool(sh.cv, sh.w * .88, sh.h * .30, sh.w * .40,
                   (255, 194, 139), .22, skia.BlendMode.kScreen, sh.w, sh.h)
        light_pool(sh.cv, sh.w * .46, sh.h * .88, sh.w * .48,
                   (84, 162, 226), .30, skia.BlendMode.kScreen, sh.w, sh.h)
        image(sh, "meditation32",
              "materials/T25990_02_meditation-bubble-art.png",
              Box(sh.w * .055, 0, sh.w * .89, sh.h * .575),
              contain=True, alpha=.24, bleed=True)

        for x, y, radius in ((.055, .075, .035), (.86, .43, .032),
                             (.94, .30, .018)):
            star = starburst(sh.w*x, sh.h*y, sh.h*radius,
                             sh.h*radius*.10, 4)
            sh.cv.drawPath(star, paint(C((255, 255, 255), .88)))
            sh.mark("meditation_sparkle",
                    Box(sh.w*x-sh.h*radius, sh.h*y-sh.h*radius,
                        sh.h*radius*2, sh.h*radius*2), collide=False)

        sh.text("meditation_headline", ctx["display"], "Stillness",
                Box(sh.w * .08, sh.h * .075, sh.w * .84, sh.h * .31),
                hi=320 * sh.scale, lo=76 * sh.scale, max_lines=1,
                color=(255, 255, 255), min_read=50 * sh.scale,
                track=-.035, min_contrast=1.55,
                glow=((105, 54, 161), .020, .28))
        pill = Box(sh.w * .37, sh.h * .415, sh.w * .26, sh.h * .065)
        sh.cv.drawRoundRect(skia.Rect.MakeXYWH(pill.x, pill.y, pill.w, pill.h),
                            38 * sh.scale, 38 * sh.scale,
                            paint(C((255, 255, 255), .72),
                                  style=skia.Paint.kStroke_Style,
                                  width=2.4 * sh.scale))
        sh.text("meditation_workshop", ctx["display"], "Workshop",
                Box(pill.x + 12 * sh.scale, pill.y + 4 * sh.scale,
                    pill.w - 24 * sh.scale, pill.h - 8 * sh.scale),
                hi=33 * sh.scale, lo=17 * sh.scale, max_lines=1,
                color=(255, 255, 255), min_read=14 * sh.scale,
                track=.06, min_contrast=1.4,
                glow=((100, 52, 156), .018, .26))

        photo_box = Box(sh.w * .10, sh.h * .55, sh.w * .80, sh.h * .29)
        if image(sh, "meditation32", "materials/T25990_02_sea-rocks-photo.png",
                 photo_box, crop=(0, 0, 949, 261)) is None:
            return
        # A fine inset rule gives the quiet photograph the same framed-panel
        # treatment as the original workshop poster.
        sh.cv.drawRect(skia.Rect.MakeXYWH(photo_box.x, photo_box.y,
                                           photo_box.w, photo_box.h),
                       paint(C((255, 255, 255), .72),
                             style=skia.Paint.kStroke_Style,
                             width=2.2 * sh.scale))
        burst = starburst(sh.w * .095, sh.h * .565, sh.h * .14,
                          sh.h * .112, 17)
        sh.cv.drawPath(burst, paint(C((222, 47, 101), .97)))
        sh.cv.drawPath(burst, paint(C(accent_ink, .8),
                                    style=skia.Paint.kStroke_Style,
                                    width=2.5 * sh.scale))
        sh.text("meditation_badge", ctx["label"], "Pause\nReset",
                Box(sh.w * .015, sh.h * .505, sh.w * .16, sh.h * .13),
                hi=45 * sh.scale, lo=23 * sh.scale, max_lines=2,
                color=(255, 255, 255), min_read=20 * sh.scale,
                track=.01, collide=False)
        sh.text("meditation_date", ctx["label"], "A Moment To Reset",
                Box(sh.w * .10, sh.h * .875, sh.w * .42, sh.h * .06),
                hi=32 * sh.scale, lo=17 * sh.scale, max_lines=1,
                color=(72, 42, 82), min_read=14 * sh.scale,
                align="left", track=.04,
                glow=((255, 255, 255), .012, .16))
        sh.text("meditation_footer", ctx["label"], "Breathe  •  Begin Again",
                Box(sh.w * .56, sh.h * .875, sh.w * .34, sh.h * .06),
                hi=27 * sh.scale, lo=15 * sh.scale, max_lines=1,
                color=(72, 42, 82), min_read=13 * sh.scale,
                align="right", track=.035,
                glow=((255, 255, 255), .012, .16))

    @support("strongweak32", "a bright hand-drawn poster pairing two oversized display specimens")
    def t_strongweak32(sh, ctx):
        orange = (255, 80, 17)
        pink = (255, 183, 207)
        blue = (17, 70, 139)
        cream = (255, 239, 227)
        yellow = (255, 188, 25)
        sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(orange)))
        # Softly uneven concentric mats suggest the hand-cut layered frame.
        outer = Box(sh.w * .025, sh.h * .025, sh.w * .95, sh.h * .95)
        rect(sh, outer, pink, 1, 66 * sh.scale)
        for i in range(19):
            x = sh.w * (.035 + i * .0515)
            circle(sh, x, sh.h * .035, sh.h * .025, pink)
            circle(sh, x, sh.h * .965, sh.h * .025, pink)
        for i in range(11):
            y = sh.h * (.09 + i * .082)
            circle(sh, sh.w * .035, y, sh.w * .012, pink)
            circle(sh, sh.w * .965, y, sh.w * .012, pink)
        card = Box(sh.w * .055, sh.h * .085, sh.w * .89, sh.h * .83)
        rect(sh, card, blue, 1, 78 * sh.scale)

        sh.text("strongweak_kicker", ctx["label"],
                lead_in(ctx, ("Playful Lettering", "Ink With Attitude",
                              "Organic Type Study")),
                Box(sh.w * .26, sh.h * .12, sh.w * .48, sh.h * .075),
                hi=43 * sh.scale, lo=22 * sh.scale, max_lines=1,
                color=yellow, min_read=18 * sh.scale, track=.055)
        sh.text("strongweak_strongest", ctx["display"], "Strongest",
                Box(sh.w * .11, sh.h * .235, sh.w * .78, sh.h * .255),
                hi=310 * sh.scale, lo=88 * sh.scale, max_lines=1,
                color=cream, min_read=52 * sh.scale, track=-.04,
                glow=((7, 44, 94), .018, .42))
        sh.text("strongweak_weakest", ctx["display"], "Weakest",
                Box(sh.w * .11, sh.h * .505, sh.w * .78, sh.h * .275),
                hi=330 * sh.scale, lo=88 * sh.scale, max_lines=1,
                color=cream, min_read=52 * sh.scale, track=-.045,
                glow=((7, 44, 94), .018, .42))

        # The small callouts overlap the display lines as they do on the source
        # poster; the lower line is restored as a separate specimen caption.
        for cx, text, color in ((sh.w * .15, "Hand\nDrawn", yellow),
                                (sh.w * .88, "Regular\nOutline", (227, 101, 211))):
            burst = starburst(cx, sh.h * .46, sh.h * .078,
                              sh.h * .065, 12)
            sh.cv.drawPath(burst, paint(C(color)))
            sh.text(f"strongweak_badge_{int(cx)}", ctx["label"], text,
                    Box(cx - sh.h * .075, sh.h * .425,
                        sh.h * .15, sh.h * .08),
                    hi=28 * sh.scale, lo=15 * sh.scale, max_lines=2,
                    color=(38, 35, 74), min_read=13 * sh.scale,
                    track=.01, collide=False)
        sh.text("strongweak_footer", ctx["display"], "Organic Hand Drawn",
                Box(sh.w * .19, sh.h * .835, sh.w * .62, sh.h * .09),
                hi=68 * sh.scale, lo=28 * sh.scale, max_lines=1,
                color=yellow, min_read=25 * sh.scale, track=.015)

    @support("funkyfashion32", "a pop-fashion layout with a vivid portrait crop, orange motifs, and comic sticker details")
    def t_funkyfashion32(sh, ctx):
        pink = (236, 98, 122)
        cream = (255, 243, 220)
        black = (22, 20, 30)
        accent_ink = theme_ink(ctx, pink)
        sh.cv.drawRect(skia.Rect.MakeWH(sh.w, sh.h), paint(C(pink)))

        # Retain the source's annotation grid and pointer around the prepared
        # transparent portrait, rather than making a generic photo card.
        for row in range(5):
            for col in range(5):
                circle(sh, sh.w * (.075 + col * .030),
                       sh.h * (.51 + row * .030), 3.0 * sh.scale,
                       cream, .86)
        rule(sh.cv, sh.w * .205, sh.h * .55, sh.w * .285, sh.h * .55,
             black, 8 * sh.scale)
        arrow = skia.Path()
        arrow.moveTo(sh.w * .285, sh.h * .55)
        arrow.lineTo(sh.w * .255, sh.h * .528)
        arrow.moveTo(sh.w * .285, sh.h * .55)
        arrow.lineTo(sh.w * .255, sh.h * .572)
        sh.cv.drawPath(arrow, paint(C(black), style=skia.Paint.kStroke_Style,
                                    width=8 * sh.scale))

        # This broad orange disc is part of the reference composition; the
        # user's prepared cutout is then placed at nearly its original scale.
        disk = Box(sh.w * .285, sh.h * .285, sh.w * .48, sh.h * .575)
        sh.cv.drawOval(skia.Rect.MakeXYWH(disk.x, disk.y, disk.w, disk.h),
                       paint(C((198, 105, 56))))
        sh.mark("funky_portrait_backdrop", disk, collide=False)
        portrait = Box(sh.w * .245, sh.h * .16, sh.w * .54, sh.h * .77)
        portrait_clip = skia.Path()
        portrait_clip.addOval(skia.Rect.MakeXYWH(
            disk.x, disk.y, disk.w, disk.h))
        sh.cv.save()
        sh.cv.clipPath(portrait_clip, skia.ClipOp.kIntersect, True)
        if image(sh, "funkyfashion32",
                 "materials/T26289_01_orange-fashion-cutout.png", portrait,
                 contain=True) is None:
            sh.cv.restore()
            return
        sh.cv.restore()

        # A compact layered lightning sticker restores the source's lower-left
        # fashion-comic accent without carrying its lettering into the crop.
        bolt = Box(sh.w * .285, sh.h * .655, sh.w * .105, sh.h * .205)
        bolt_points = ((.58, .00), (.13, .49), (.46, .49),
                       (.27, 1.00), (.91, .36), (.58, .36))
        def bolt_path(dx=0, dy=0):
            path = skia.Path()
            for i, (px, py) in enumerate(bolt_points):
                x, y = bolt.x + bolt.w*(px+dx), bolt.y + bolt.h*(py+dy)
                (path.moveTo if i == 0 else path.lineTo)(x, y)
            path.close()
            return path
        for dx, dy, color in ((.11, .06, (91, 46, 181)),
                              (.065, .035, (38, 139, 219)),
                              (.025, .015, (31, 24, 43)),
                              (0, 0, (255, 226, 29))):
            sh.cv.drawPath(bolt_path(dx, dy), paint(C(color)))
        sh.mark("funky_lightning_sticker", bolt, collide=False)

        # The smiley is a clean crop from the reference; its flat surround
        # matches the sampled page pink, so no approximate replacement is used.
        if image(sh, "funkyfashion32", "T26289_01.jpg",
                 Box(sh.w * .74, sh.h * .20, sh.w * .24, sh.h * .36),
                 crop=(875, 172, 280, 285)) is None:
            return

        # Give the two display words independent boxes. A font with long
        # ascenders/descenders can otherwise collapse the shared leading and
        # let the lower word cross the upper one, even when the auto-fit says
        # the two-line block is clean.
        for slot, wording, y, height in (
                ("funky_headline_top", "Funky", .065, .16),
                ("funky_headline_bottom", "Fashion", .235, .19)):
            sh.text(slot, ctx["display"], wording,
                    Box(sh.w * .045, sh.h * y, sh.w * .46,
                        sh.h * height),
                    hi=260 * sh.scale, lo=62 * sh.scale, max_lines=1,
                    color=cream, min_read=40 * sh.scale, align="left",
                    track=-.035, glow=((31, 26, 32), .014, .38),
                    min_contrast=2.8)

        sh.text("funky_side_label", ctx["display"], "Fashion\nWEEK",
                Box(sh.w * .60, sh.h * .055, sh.w * .20, sh.h * .15),
                hi=47 * sh.scale, lo=22 * sh.scale, max_lines=2,
                color=cream, min_read=19 * sh.scale, track=-.015,
                min_contrast=2.8,
                glow=((35, 29, 40), .012, .24))
        sh.text("funky_body_copy", ctx["display"],
                "Bright layers and playful details make every look feel fresh and entirely your own.",
                Box(sh.w * .68, sh.h * .625, sh.w * .27, sh.h * .22),
                hi=31 * sh.scale, lo=13 * sh.scale, max_lines=6,
                color=cream, min_read=12 * sh.scale, align="left",
                track=-.005, leading=.94, min_contrast=2.0,
                glow=((35, 29, 40), .010, .20))
        sh.text("funky_caption", ctx["label"], "Color  /  Attitude  /  Type",
                Box(sh.w * .52, sh.h * .895, sh.w * .43, sh.h * .055),
                hi=30 * sh.scale, lo=16 * sh.scale, max_lines=1,
                color=cream, min_read=13 * sh.scale, align="right",
                track=.035, min_contrast=2.8)
        rule(sh.cv, sh.w * .72, sh.h * .965, sh.w * .95, sh.h * .965,
             accent_ink, 3 * sh.scale)
