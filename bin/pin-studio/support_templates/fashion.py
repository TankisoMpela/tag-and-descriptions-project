"""Editorial and fashion support sheets reconstructed from supplied references.

The host injects the renderer API into :func:`register`; this module deliberately
does not import the pin renderer or any of its globals.
"""

import math


def register(api):
    support = api["support"]
    skia = api["skia"]
    C = api["C"]
    paint = api["paint"]
    rule = api["rule"]
    ground = api["ground"]
    light_pool = api["light_pool"]
    speckle = api["speckle"]
    Box = api["Box"]
    readable = api["readable"]
    mix = api["mix"]
    lum = api["lum"]
    gradient_fill = api["gradient_fill"]
    Path = api["Path"]
    ref_dir = Path(api["SUPPORT_REF_DIR"])
    support_copy = api["_support_copy"]
    panel_text = api["panel_text"]
    rolled = api["rolled"]
    lead_in = api["lead_in"]

    PAPER = (249, 247, 241)
    PAPER_SHADE = (239, 236, 228)
    INK = (17, 17, 18)
    RED = (222, 9, 28)
    WHITE = (255, 253, 248)
    GREY = (91, 88, 84)

    def colors(ctx):
        pal = ctx["pal"]
        red = readable(lum(PAPER), mix(RED, pal["accent"], .07), 3.0)
        return red

    def text(sh, ctx, slot, value, box, *, display=True, hi=120, lo=22,
             color=INK, max_lines=1, align="left", valign="middle",
             track=-.012, min_read=18, leading=.86, min_contrast=4.5,
             grad=None):
        value = support_copy(ctx, (), value).strip()
        if not value:
            return None
        return sh.text(slot, ctx["display"] if display else ctx["label"],
                       value, box, hi=hi * sh.scale, lo=lo * sh.scale,
                       color=color, grad=grad, max_lines=max_lines,
                       align=align, valign=valign, track=track,
                       leading=leading, min_read=min_read * sh.scale,
                       min_contrast=min_contrast)

    def paper(sh, seed=37, texture=1500):
        ground(sh.cv, PAPER, PAPER_SHADE, w=sh.w, h=sh.h)
        speckle(sh.cv, (100, 83, 73), n=texture, seed=seed, alpha=.018,
                rad=max(.5, .65 * sh.scale), w=sh.w, h=sh.h)

    def rect(sh, box, color, alpha=1.0, *, bleed=False):
        sh.cv.drawRect(skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h),
                       paint(C(color, alpha)))
        sh.mark("fashion_panel", box, collide=False, bleed=bleed)

    def image(sh, slug, template):
        path = ref_dir / slug
        if not path.is_file():
            sh.problems.append(f"{template}: missing support reference {path}")
            return None
        result = skia.Image.open(str(path))
        if result is None:
            sh.problems.append(f"{template}: could not decode {path.name}")
        return result

    def cropped(sh, img, crop, box, slot, *, alpha=1.0, bleed=False):
        """Draw a normalized source crop, center-covering it into ``box``."""
        if img is None:
            return
        iw, ih = img.width(), img.height()
        x, y, w, h = crop
        sx, sy, sw, shh = x * iw, y * ih, w * iw, h * ih
        src_ratio = sw / shh
        dst_ratio = box.w / box.h
        if src_ratio > dst_ratio:
            nw = shh * dst_ratio
            sx += (sw - nw) / 2
            sw = nw
        else:
            nh = sw / dst_ratio
            sy += (shh - nh) / 2
            shh = nh
        src = skia.Rect.MakeXYWH(sx, sy, sw, shh)
        dst = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        q = paint()
        if alpha < 1.0:
            q.setAlphaf(alpha)
        sh.cv.drawImageRect(img, src, dst,
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear), q)
        sh.mark(slot, box, collide=False, bleed=bleed)

    def contained(sh, img, box, slot, *, bleed=False):
        """Keep a transparent illustration's whole silhouette in its slot."""
        if img is None:
            return
        scale = min(box.w / img.width(), box.h / img.height())
        w, h = img.width() * scale, img.height() * scale
        dst = skia.Rect.MakeXYWH(box.x + (box.w-w)/2,
                                 box.y + (box.h-h)/2, w, h)
        sh.cv.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), dst,
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        sh.mark(slot, Box(dst.x(), dst.y(), dst.width(), dst.height()),
                collide=False, bleed=bleed)

    def line(sh, x1, y1, x2, y2, color, width=1.5, alpha=.85):
        rule(sh.cv, x1, y1, x2, y2, color,
             max(1.0, width * sh.scale), alpha)

    @support("voguecover32",
             "a red-and-ivory editorial cover with a close illustrated portrait, masthead, and restrained issue furniture")
    def voguecover32(sh, ctx):
        red = colors(ctx)
        paper(sh, seed=31, texture=1300)
        portrait = image(sh, "materials/T28576_03_glamorous-manga-portrait.png",
                         "voguecover32")
        # This is the user's transparent portrait that matches the T28576_03
        # source illustration; keep it central, behind the masthead, and uncropped.
        contained(sh, portrait,
                  Box(sh.w * .275, sh.h * .005, sh.w * .70, sh.h * .965),
                  "cover_portrait")

        text(sh, ctx, "cover_masthead", "Vogue",
             Box(sh.w * .025, sh.h * .015, sh.w * .95, sh.h * .255),
             hi=420, lo=95, color=red, track=-.045, min_read=68)
        text(sh, ctx, "cover_issue", "March / Issue",
             Box(sh.w * .035, sh.h * .275, sh.w * .18, sh.h * .035),
             display=False, hi=20, lo=12, color=INK, track=.08, min_read=11)
        text(sh, ctx, "cover_corner", "Japan",
             Box(sh.w * .795, sh.h * .275, sh.w * .17, sh.h * .035),
             display=False, hi=19, lo=11, color=red, align="right",
             track=.08, min_read=10)

        # Left cover lines and the lower-right feature name occupy opposite
        # sides of the portrait, preserving the asymmetric magazine balance.
        text(sh, ctx, "cover_headline", "Discover",
             Box(sh.w * .04, sh.h * .325, sh.w * .29, sh.h * .07),
             hi=118, lo=34, color=INK, max_lines=1, track=-.035,
             min_read=28, leading=.82)
        text(sh, ctx, "cover_deck", "The New\nStreet Fashion\nTrends From",
             Box(sh.w * .04, sh.h * .402, sh.w * .285, sh.h * .17),
             display=False, hi=47, lo=24, color=INK, max_lines=3,
             track=.035, min_read=22, leading=.90)
        text(sh, ctx, "cover_note", "Tokyo",
             Box(sh.w * .04, sh.h * .585, sh.w * .29, sh.h * .055),
             display=False, hi=54, lo=28, color=red, max_lines=1,
             track=.04, min_read=12, leading=.95)
        text(sh, ctx, "cover_reina_name", "Reina Sato",
             Box(sh.w * .04, sh.h * .715, sh.w * .31, sh.h * .06),
             hi=52, lo=25, color=INK, max_lines=1, track=-.02,
             min_read=23)
        text(sh, ctx, "cover_reina_story", "Shows You How\nTo Take The\nPerfect Selfie",
             Box(sh.w * .04, sh.h * .78, sh.w * .31, sh.h * .15),
             display=False, hi=35, lo=19, color=INK, max_lines=3,
             track=.025, min_read=17, leading=.95)
        text(sh, ctx, "cover_feature", "Sakura\nYamaguchi",
             Box(sh.w * .43, sh.h * .545, sh.w * .54, sh.h * .22),
             hi=110, lo=38, color=INK, max_lines=2, align="right",
             track=-.035, min_read=31, leading=.83, min_contrast=3.0)
        text(sh, ctx, "cover_feature_note", "The Making Of\nAsia's Next\nTop Model",
             Box(sh.w * .48, sh.h * .775, sh.w * .47, sh.h * .105),
             display=False, hi=25, lo=14, color=INK, max_lines=3, align="right",
             track=.08, min_read=12, min_contrast=3.0)
        text(sh, ctx, "cover_footer_lead", "Follow Us On Social Media",
             Box(sh.w * .57, sh.h * .902, sh.w * .38, sh.h * .025),
             display=False, hi=17, lo=10, color=INK, align="right",
             track=.04, min_read=9)
        text(sh, ctx, "cover_footer_note", "Facebook / Instagram / TikTok",
             Box(sh.w * .57, sh.h * .933, sh.w * .38, sh.h * .025),
             display=False, hi=15, lo=9, color=INK, align="right",
             track=.02, min_read=8)

    @support("confident32",
             "the confidence poster: a bold red display statement above the clean illustrated close-up from the reference")
    def confident32(sh, ctx):
        red = colors(ctx)
        paper(sh, seed=43, texture=1000)
        portrait = image(sh, "materials/T28576_04_eye-illustration-clean.png",
                         "confident32")
        cropped(sh, portrait, (0, 0, 1, 1),
                Box(sh.w * .045, sh.h * .50, sh.w * .91, sh.h * .44),
                "confidence_portrait")
        # Rebuild the source's framed title panel, split footer line and
        # centered red starburst; the clean eye artwork remains its own plate.
        header = skia.Rect.MakeXYWH(sh.w*.045, sh.h*.055,
                                    sh.w*.91, sh.h*.385)
        sh.cv.drawRect(header, paint(C(INK, .92),
                                     style=skia.Paint.kStroke_Style,
                                     width=2.2*sh.scale))
        text(sh, ctx, "confident_overline", "Keep Looking",
             Box(sh.w * .06, sh.h * .085, sh.w * .56, sh.h * .05),
             display=False, hi=24, lo=13, color=INK, track=.10, min_read=12)
        text(sh, ctx, "confident_tag", "Elthia Typeface",
             Box(sh.w * .72, sh.h * .085, sh.w * .21, sh.h * .05),
             display=False, hi=18, lo=11, color=INK, track=.06,
             align="right", min_read=10)
        headline = "Confident"
        text(sh, ctx, "confident_word", headline,
             Box(sh.w * .055, sh.h * .155, sh.w * .89, sh.h * .195),
             hi=300, lo=78, color=red, track=-.04, min_read=64)
        text(sh, ctx, "confident_sub_left", "Even When",
             Box(sh.w * .06, sh.h * .355, sh.w * .39, sh.h * .055),
             hi=44, lo=20, color=INK, track=-.015, min_read=18)
        text(sh, ctx, "confident_sub_right", "Doubt Looks Back",
             Box(sh.w * .49, sh.h * .355, sh.w * .45, sh.h * .055),
             hi=44, lo=20, color=INK, align="right", track=-.015,
             min_read=18)
        divider_y = sh.h*.44
        line(sh, sh.w*.045, divider_y, sh.w*.465, divider_y, INK, 1.8)
        line(sh, sh.w*.535, divider_y, sh.w*.955, divider_y, INK, 1.8)
        cx, cy = sh.w*.5, divider_y
        for index, (offset, radius) in enumerate(((-22, 9), (0, 20), (22, 9))):
            radius *= sh.scale
            rays = skia.Path()
            for point in range(16):
                angle = -math.pi/2 + point*math.pi/8
                r = radius if point % 2 == 0 else radius*.22
                x = cx+offset*sh.scale+math.cos(angle)*r
                y = cy+math.sin(angle)*r
                if point == 0:
                    rays.moveTo(x, y)
                else:
                    rays.lineTo(x, y)
            rays.close()
            sh.cv.drawPath(rays, paint(C(red)))
            sh.mark(f"confident_red_rays_{index}",
                    Box(cx+offset*sh.scale-radius, cy-radius,
                        2*radius, 2*radius), collide=False)
        sh.cv.drawRect(skia.Rect.MakeXYWH(sh.w*.045, sh.h*.50,
                                          sh.w*.91, sh.h*.44),
                       paint(C(INK, .92), style=skia.Paint.kStroke_Style,
                             width=2.2*sh.scale))

    @support("storyteller32",
             "an illustrated design-studio spread with a right-hand portrait, working-hands detail, and editorial copy")
    def storyteller32(sh, ctx):
        red = colors(ctx)
        eyes = image(sh, "materials/T28576_05_framed-manga-eyes.png",
                    "storyteller32")
        cropped(sh, eyes, (0, 0, 1, 1), Box(0, 0, sh.w, sh.h),
                "framed_eyes_background", bleed=True)
        # The supplied framed eyes are the entire background. Keep a single,
        # deliberately quiet lower lockup; no paper texture, artist cutout,
        # hands strip, divider, or burst competes with the image.
        text(sh, ctx, "story_overline", "Typography / Image / Meaning",
             Box(sh.w * .055, sh.h * .665, sh.w * .79, sh.h * .045),
             display=False, hi=22, lo=13, color=INK, track=.12,
             min_read=12)
        text(sh, ctx, "story_headline", "Storyteller",
             Box(sh.w * .045, sh.h * .715, sh.w * .91, sh.h * .16),
             hi=170, lo=48, color=INK, track=-.045,
             min_read=40, min_contrast=3.0)
        text(sh, ctx, "story_support", "The Silent Language Of Design",
             Box(sh.w * .06, sh.h * .885, sh.w * .84, sh.h * .065),
             display=False, hi=29, lo=16, color=red, track=.08,
             align="center", min_read=14, min_contrast=3.0)

    @support("focusposter32",
             "a focus study with a magnified eye detail, high-impact red headline, and open poster typography")
    def focusposter32(sh, ctx):
        red = colors(ctx)
        paper(sh, seed=61, texture=900)
        background = image(sh, "materials/T28576_06_soft-focus-portrait.png",
                           "focusposter32")
        cropped(sh, background, (0, 0, 1, 1), Box(0, 0, sh.w, sh.h),
                "focus_background", bleed=True)
        # The source's lower quote sits on the pale, defocused part of the
        # portrait. Keep that text field light so its alternating red/black
        # columns stay consistent instead of being contrast-shifted per word.
        sh.cv.drawRect(skia.Rect.MakeXYWH(0, sh.h * .625, sh.w, sh.h * .375),
                       paint(C(WHITE, .56)))
        ref = image(sh, "materials/T28576_06_eye-detail.png",
                    "focusposter32")
        # This crop is the source's framed eye study; its surrounding poster copy is excluded.
        cropped(sh, ref, (0, 0, 1, 1),
                Box(sh.w * .225, sh.h * .177, sh.w * .303, sh.h * .152),
                "focus_eye_detail")
        line(sh, sh.w * .05, sh.h * .350, sh.w * .95, sh.h * .350,
             INK, 1.1)
        text(sh, ctx, "focus_kicker", "Keep The Intention Clear",
             Box(sh.w * .06, sh.h * .365, sh.w * .55, sh.h * .04),
             display=False, hi=22, lo=13, color=INK, track=.12, min_read=12)
        title = support_copy(ctx, ("word",), "Focused")
        text(sh, ctx, "focus_title", title,
             Box(sh.w * .045, sh.h * .420, sh.w * .91, sh.h * .265),
             hi=420, lo=105, color=red, track=-.045, min_read=84)
        # Keep the source's five distinct text columns and staggered word
        # rhythm; combining them into three packed blocks lost the airy layout.
        quote_columns = (
            ("focus_quote_left", .035, .185, red,
             ("Staying", "avoiding", "about", "that", "your")),
            ("focus_quote_inner", .245, .195, INK,
             ("focused", "distractions,", "embracing", "comes from", "truest")),
            ("focus_quote_is", .465, .075, red, ("is",)),
            ("focus_quote_not", .56, .10, red, ("not", "but", "the")),
            ("focus_quote_outer", .685, .275, red,
             ("about", "", "clarity", "pursuing", "intentions.")),
        )
        for slot, x, width, color, words in quote_columns:
            for row, word in enumerate(words):
                if not word:
                    continue
                text(sh, ctx, f"{slot}_{row+1}", word,
                     Box(sh.w * x, sh.h * (.695 + row * .052),
                         sh.w * width, sh.h * .05),
                     hi=44, lo=18, color=color, max_lines=1,
                     track=-.018, min_read=15, min_contrast=3.0)

    @support("wideclaim32",
             "a pure type scale proof built from oversized red and black high-contrast specimen words")
    def wideclaim32(sh, ctx):
        red = colors(ctx)
        paper(sh, seed=17, texture=700)
        text(sh, ctx, "wide_kicker", "High Contrast / Display Study",
             Box(sh.w * .055, sh.h * .035, sh.w * .70, sh.h * .035),
             display=False, hi=24, lo=13, color=INK, track=.14, min_read=12)
        text(sh, ctx, "wide_paragraph",
             "A wide serif face gives short headlines room to make a statement.",
             Box(sh.w * .055, sh.h * .078, sh.w * .82, sh.h * .07),
             display=False, hi=24, lo=14, color=GREY, max_lines=2,
             track=.015, min_read=13, leading=.94)
        line(sh, sh.w * .055, sh.h * .16, sh.w * .945, sh.h * .16,
             INK, 1.5)
        text(sh, ctx, "wide_claim", "Wide",
             Box(sh.w * .035, sh.h * .19, sh.w * .93, sh.h * .37),
             hi=650, lo=150, color=red, track=-.055, min_read=126)
        text(sh, ctx, "wide_serif", "Serif",
             Box(sh.w * .04, sh.h * .59, sh.w * .92, sh.h * .34),
             hi=520, lo=125, color=INK, track=-.04, min_read=105)
        text(sh, ctx, "wide_footer", "A Distinctive Rhythm In Every Letter",
             Box(sh.w * .06, sh.h * .945, sh.w * .88, sh.h * .035),
             display=False, hi=19, lo=11, color=GREY, track=.12, min_read=10)

    @support("blossom32",
             "a calm illustrated portrait beside a simple red wellness-campaign panel")
    def blossom32(sh, ctx):
        red = colors(ctx)
        ground(sh.cv, WHITE, PAPER, w=sh.w, h=sh.h)
        art = image(sh, "materials/T28576_08_blossom-illustration.png",
                    "blossom32")
        contained(sh, art,
                  Box(sh.w * .62, 0, sh.w * .38, sh.h),
                  "blossom_portrait", bleed=True)
        panel = Box(0, 0, sh.w * .62, sh.h)
        rect(sh, panel, red, bleed=True)
        # Restore the earlier straight split and quiet red light pool; the
        # portrait remains a separate, contained illustration on the right.
        sh.cv.save()
        sh.cv.clipRect(skia.Rect.MakeXYWH(panel.x, panel.y, panel.w, panel.h),
                       doAntiAlias=True)
        light_pool(sh.cv, sh.w * .30, sh.h * .25, sh.w * .55,
                   WHITE, .11, w=sh.w, h=sh.h)
        sh.cv.restore()
        text(sh, ctx, "blossom_kicker", "A Retreat For The Senses",
             Box(sh.w * .065, sh.h * .075, sh.w * .52, sh.h * .05),
             display=False, hi=23, lo=13, color=WHITE, track=.12,
             align="left", min_read=12, min_contrast=3.0)
        for slot, wording, y in (("blossom_title_top", "Bloom", .17),
                                 ("blossom_title_bottom", "Into Calm", .30)):
            text(sh, ctx, slot, wording,
                 Box(sh.w * .055, sh.h * y, sh.w * .55, sh.h * .115),
                 hi=180, lo=44, color=WHITE, align="left", track=-.035,
                 min_read=40, min_contrast=3.0)
        text(sh, ctx, "blossom_sub", "Restore Your Natural Rhythm",
             Box(sh.w * .065, sh.h * .435, sh.w * .52, sh.h * .055),
             display=False, hi=28, lo=16, color=WHITE, track=.04,
             align="left",
             min_read=14, min_contrast=3.0)
        line(sh, sh.w * .065, sh.h * .51, sh.w * .58, sh.h * .51,
             WHITE, 1.5, .88)
        body = support_copy(ctx, ("line", "sub"),
                            "Slow down, breathe deeply, and leave space for renewal.")
        text(sh, ctx, "blossom_body", body,
             Box(sh.w * .065, sh.h * .55, sh.w * .51, sh.h * .13),
             display=False, hi=31, lo=15, color=WHITE, max_lines=3,
             track=.005, min_read=15, leading=.95, min_contrast=3.0)
        button = Box(sh.w * .15, sh.h * .67, sh.w * .34, sh.h * .08)
        sh.cv.drawRoundRect(skia.Rect.MakeXYWH(button.x, button.y,
                                               button.w, button.h),
                            button.h * .5, button.h * .5,
                            paint(C(WHITE, 1), style=skia.Paint.kStroke_Style,
                                  width=max(2, 2.2 * sh.scale)))
        sh.mark("booking_button", button, collide=False)
        text(sh, ctx, "blossom_button", "Book A Session",
             Box(button.x + button.w * .06, button.y + button.h * .12,
                 button.w * .88, button.h * .76),
             hi=30, lo=17, color=WHITE, align="center", track=.08,
             min_read=15, min_contrast=3.0)

    @support("ravencover32",
             "a moody luxury cover built around the supplied red tailoring photograph, with clean replacement title bands")
    def ravencover32(sh, ctx):
        art = image(sh, "materials/T28660_00_red-jacket-photo.png",
                    "ravencover32")
        cropped(sh, art, (0, 0, 1, 1), Box(0, 0, sh.w, sh.h),
                "tailoring_photo", bleed=True)
        # The generated clean photo replaces the text-obscured source image;
        # only a light veil is added so the cream display type reads on fabric.
        shade = (16, 10, 12)
        rect(sh, Box(0, 0, sh.w, sh.h), shade, .20, bleed=True)
        ivory = (245, 235, 216)

        # Hairline rules and an outlined oval echo the source's sparse cover
        # furniture; avoid a solid bar so the fashion photograph stays open.
        line(sh, sh.w * .025, sh.h * .030, sh.w * .975, sh.h * .030,
             ivory, 1.2, .88)
        line(sh, sh.w * .025, sh.h * .935, sh.w * .975, sh.h * .935,
             ivory, 1.2, .88)
        badge = Box(sh.w * .405, sh.h * .058, sh.w * .190, sh.h * .108)
        sh.cv.drawOval(skia.Rect.MakeXYWH(badge.x, badge.y, badge.w, badge.h),
                       paint(C(ivory, .90), style=skia.Paint.kStroke_Style,
                             width=max(1.0, 1.2 * sh.scale)))
        sh.mark("raven_oval_badge", badge, collide=False)
        text(sh, ctx, "raven_masthead", "Present By",
             Box(badge.x + badge.w * .09, badge.y + badge.h * .26,
                 badge.w * .82, badge.h * .25),
             display=False, hi=20, lo=11, color=ivory,
             align="center", track=.05, min_read=11)
        text(sh, ctx, "raven_issue", "Muksal Creative",
             Box(badge.x + badge.w * .09, badge.y + badge.h * .53,
                 badge.w * .82, badge.h * .24),
             display=False, hi=18, lo=10, color=ivory,
             align="center", track=.08, min_read=10)

        text(sh, ctx, "raven_title", "Raven Court",
             Box(sh.w * .075, sh.h * .365, sh.w * .85, sh.h * .235),
             hi=330, lo=75, color=ivory, track=-.035, min_read=68,
             min_contrast=3.0)
        text(sh, ctx, "raven_subtitle", "Modern Serif Display Font",
             Box(sh.w * .08, sh.h * .725, sh.w * .84, sh.h * .060),
             display=False, hi=37, lo=17, color=ivory,
             align="center", track=.12, min_read=15)
        text(sh, ctx, "raven_details", "Regular & Italic Font",
             Box(sh.w * .08, sh.h * .810, sh.w * .84, sh.h * .055),
             display=False, hi=29, lo=14, color=ivory,
             align="center", track=.14, min_read=13)
