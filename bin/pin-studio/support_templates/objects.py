"""Illustrated cards, labels, glyph boards, and greeting layouts."""

import math


def register(api):
    support, skia, C, paint, rule = (api[k] for k in
                                     ("support", "skia", "C", "paint", "rule"))
    Box, ground, speckle = api["Box"], api["ground"], api["speckle"]
    support_copy, readable, lum = api["_support_copy"], api["readable"], api["lum"]
    ref_dir = api["SUPPORT_REF_DIR"]

    def type(sh, ctx, slot, wording, box, *, size=120, color=None,
             face=True, align="center", lines=1, track=0, leading=.86,
             min_read=18, min_contrast=3.2, collide=True):
        if not wording:
            return
        sh.text(slot, ctx["display"] if face else ctx["label"], wording, box,
                hi=size*sh.scale, lo=max(8, 12*sh.scale),
                color=color or ctx["pal"]["glow"], max_lines=lines,
                align=align, valign="middle", track=track, leading=leading,
                min_read=min_read*sh.scale, min_contrast=min_contrast,
                collide=collide)

    def line(sh, x1, y1, x2, y2, color, width=1.6, alpha=.92):
        rule(sh.cv, x1, y1, x2, y2, color, width*sh.scale, alpha)

    def rect(sh, box, color, *, radius=0, stroke=False, stroke_color=None,
             width=2, alpha=1, mark=True):
        shape = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        if radius:
            sh.cv.drawRoundRect(shape, radius*sh.scale, radius*sh.scale,
                                paint(C(color, alpha)))
            if stroke:
                sh.cv.drawRoundRect(shape, radius*sh.scale, radius*sh.scale,
                                    paint(C(stroke_color or color, alpha),
                                          style=skia.Paint.kStroke_Style,
                                          width=width*sh.scale))
        else:
            sh.cv.drawRect(shape, paint(C(color, alpha)))
            if stroke:
                sh.cv.drawRect(shape, paint(C(stroke_color or color, alpha),
                                            style=skia.Paint.kStroke_Style,
                                            width=width*sh.scale))
        if mark:
            sh.mark("graphic_panel", box, collide=False)

    def crown(sh, cx, cy, size, color):
        path = skia.Path()
        path.moveTo(cx-size*.5, cy+size*.25)
        path.lineTo(cx-size*.42, cy-size*.18)
        path.lineTo(cx-size*.16, cy+size*.02)
        path.lineTo(cx, cy-size*.34)
        path.lineTo(cx+size*.17, cy+size*.02)
        path.lineTo(cx+size*.42, cy-size*.18)
        path.lineTo(cx+size*.5, cy+size*.25)
        path.close()
        sh.cv.drawPath(path, paint(C(color)))
        line(sh, cx-size*.48, cy+size*.32, cx+size*.48, cy+size*.32,
             color, 4)

    def star(sh, cx, cy, r, color, points=8, alpha=1):
        p = skia.Path()
        for i in range(points*2):
            a = -1.5707963268 + i*3.1415926536/points
            rr = r if i % 2 == 0 else r*.34
            x, y = cx+rr*math.cos(a), cy+rr*math.sin(a)
            (p.moveTo if i == 0 else p.lineTo)(x, y)
        p.close()
        sh.cv.drawPath(p, paint(C(color, alpha)))
        sh.mark("star", Box(cx-r, cy-r, 2*r, 2*r), collide=False)

    def heart(sh, cx, cy, size, color, *, width=2.4, alpha=.95):
        p = skia.Path()
        p.moveTo(cx, cy+size*.42)
        p.cubicTo(cx-size*.16, cy+size*.20, cx-size*.54, cy-size*.03,
                  cx-size*.47, cy-size*.30)
        p.cubicTo(cx-size*.40, cy-size*.57, cx-size*.10, cy-size*.50,
                  cx, cy-size*.27)
        p.cubicTo(cx+size*.10, cy-size*.50, cx+size*.40, cy-size*.57,
                  cx+size*.47, cy-size*.30)
        p.cubicTo(cx+size*.54, cy-size*.03, cx+size*.16, cy+size*.20,
                  cx, cy+size*.42)
        sh.cv.drawPath(p, paint(C(color, alpha),
                                style=skia.Paint.kStroke_Style,
                                width=width*sh.scale))
        sh.mark("heart_doodle", Box(cx-size*.55, cy-size*.55,
                                     size*1.1, size), collide=False)

    def vertical_type(sh, ctx, slot, wording, cx, cy, length, *, size=20,
                      color=None, track=.08):
        face = ctx["label"]
        phrase = support_copy(ctx, (), wording)
        px = size*sh.scale
        spacing = px*track
        px = face.fit(phrase, px, length, tracking=spacing)
        path, _ = face.path(phrase, px, tracking=spacing)
        bounds = path.getBounds()
        sh.cv.save()
        sh.cv.translate(cx, cy)
        sh.cv.rotate(-90)
        sh.cv.translate(-bounds.centerX(), -bounds.centerY())
        sh.cv.drawPath(path, paint(C(color or ctx["pal"]["ink"])))
        sh.cv.restore()
        sh.mark(slot, Box(cx-bounds.height()/2, cy-bounds.width()/2,
                          bounds.height(), bounds.width()), collide=False)

    def image(sh, filename, box, *, focus=(.5,.5), contain=True, crop=None,
              cover=False, bleed=False):
        path = ref_dir / "materials" / filename
        if not path.is_file():
            sh.problems.append(f"missing support material: {path.name}")
            return
        art = skia.Image.open(str(path))
        if art is None:
            sh.problems.append(f"could not decode support material: {path.name}")
            return
        iw, ih = art.width(), art.height()
        src = (skia.Rect.MakeXYWH(iw*crop[0], ih*crop[1],
                                  iw*(crop[2]-crop[0]),
                                  ih*(crop[3]-crop[1])) if crop else
               skia.Rect.MakeWH(iw, ih))
        sw, sh_ = src.width(), src.height()
        if contain:
            scale = min(box.w/sw, box.h/sh_)
            dw, dh = sw*scale, sh_*scale
            dst = skia.Rect.MakeXYWH(box.x+(box.w-dw)/2,
                                     box.y+(box.h-dh)/2,dw,dh)
        elif cover:
            target_aspect = box.w / box.h
            source_aspect = sw / sh_
            if source_aspect > target_aspect:
                cw = sh_ * target_aspect
                sx = src.x() + (sw-cw)*focus[0]
                src = skia.Rect.MakeXYWH(sx, src.y(), cw, sh_)
            else:
                ch = sw / target_aspect
                sy = src.y() + (sh_-ch)*focus[1]
                src = skia.Rect.MakeXYWH(src.x(), sy, sw, ch)
            dst = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        else:
            scale = max(box.w/sw, box.h/sh_)
            cw, ch = box.w/scale, box.h/scale
            sx = src.x() + (sw-cw)*focus[0]
            sy = src.y() + (sh_-ch)*focus[1]
            src = skia.Rect.MakeXYWH(sx, sy, cw, ch)
            dst = skia.Rect.MakeXYWH(box.x, box.y, box.w, box.h)
        sh.cv.drawImageRect(art, src, dst,
                            skia.SamplingOptions(skia.FilterMode.kLinear,
                                                 skia.MipmapMode.kLinear))
        sh.mark(filename.rsplit(".",1)[0], box, collide=False,
                bleed=bleed or box.x<0 or box.y<0 or
                box.r>sh.w or box.b>sh.h)

    @support("dreamchalk32", "a dark-green chalkboard with a framed statement, source-cropped chalk hand, and dry chalk accents")
    def dreamchalk32(sh, ctx):
        green, chalk = (8, 41, 34), (250, 244, 220)
        ground(sh.cv, green, (7, 29, 26), w=sh.w, h=sh.h)
        speckle(sh.cv, (209, 233, 222), n=3600, seed=103, alpha=.085,
                rad=.65*sh.scale, w=sh.w, h=sh.h)
        board = Box(sh.w*.055, sh.h*.11, sh.w*.89, sh.h*.78)
        rect(sh, board, (8, 10, 9), stroke=True, stroke_color=chalk, width=3)
        rect(sh, Box(board.x+sh.w*.014, board.y+sh.h*.018,
                     board.w-sh.w*.028, board.h-sh.h*.036), (8, 10, 9),
             stroke=True, stroke_color=(188, 193, 175), width=1.2, alpha=.82)
        type(sh, ctx, "dream_prompt", "Dare To",
             Box(sh.w*.16, sh.h*.27, sh.w*.40, sh.h*.13), size=115,
             color=chalk, align="left", min_read=38, track=.025)
        image(sh, "T23086_05_chalk-pointing-hand-source.png",
              Box(sh.w*.59, sh.h*.265, sh.w*.32, sh.h*.17),
              crop=(.02,.04,.96,.94))
        type(sh, ctx, "dream_word", "Dream",
             Box(sh.w*.04, sh.h*.445, sh.w*.92, sh.h*.34), size=340,
             color=(250, 217, 90), min_read=78, track=-.035)

    @support("lovecard32", "a bold greeting card on a deep emerald botanical-green field with hand-drawn heart accents")
    def lovecard32(sh, ctx):
        green, white = (12, 64, 42), (255, 252, 236)
        ground(sh.cv, green, (20, 88, 57), w=sh.w, h=sh.h)
        speckle(sh.cv, (114, 168, 105), n=2200, seed=23086,
                alpha=.07, rad=.8*sh.scale, w=sh.w, h=sh.h)
        card = Box(sh.w*.105, sh.h*.12, sh.w*.79, sh.h*.76)
        rect(sh, Box(card.x-sh.w*.008, card.y-sh.h*.009,
                     card.w+sh.w*.016, card.h+sh.h*.018), (17, 43, 30),
             radius=13, stroke=True, stroke_color=(222, 192, 119), width=2)
        rect(sh, card, white, radius=12)
        type(sh, ctx, "love_small", "We Love You",
             Box(card.x+card.w*.08, card.y+card.h*.08,
                 card.w*.84, card.h*.13), size=43, color=green,
             face=False, track=.09, min_read=21)
        for cx, cy, r in ((.39,.37,.036),(.50,.35,.045),(.61,.37,.036)):
            heart(sh, sh.w*cx, sh.h*cy, sh.h*r, (222, 72, 93), width=2.6)
        type(sh, ctx, "love_main", "Good Type!",
             Box(card.x+card.w*.055, card.y+card.h*.47,
                 card.w*.89, card.h*.27), size=390,
             color=(215, 44, 60), track=-.045, min_read=58)
        line(sh, card.x+card.w*.22, card.y+card.h*.81,
             card.x+card.w*.78, card.y+card.h*.81, (73, 132, 81), 1.7)
        type(sh, ctx, "love_signoff", "Made With Heart",
             Box(card.x+card.w*.08, card.y+card.h*.835,
                 card.w*.84, card.h*.075), size=23, color=green,
             face=False, track=.12, min_read=11)

    @support("queens32", "the dark roundel: crowned chalk lettering, teal flourishes, and a small handwritten-style footer")
    def queens32(sh, ctx):
        dark, chalk, teal = (15, 22, 21), (249, 240, 216), (45, 147, 132)
        ground(sh.cv, dark, (6, 12, 12), w=sh.w, h=sh.h)
        speckle(sh.cv, teal, n=1800, seed=26003, alpha=.08,
                rad=.8*sh.scale, w=sh.w, h=sh.h)
        sh.cv.drawCircle(sh.w*.5, sh.h*.52, sh.h*.40,
                         paint(C(teal, .42), style=skia.Paint.kStroke_Style,
                               width=9*sh.scale))
        sh.cv.drawCircle(sh.w*.5, sh.h*.52, sh.h*.37,
                         paint(C(teal, .28), style=skia.Paint.kStroke_Style,
                               width=2*sh.scale))
        for i in range(54):
            angle = 6.28318530718*i/54
            r0 = sh.h*(.385 + (i%3)*.003)
            r1 = sh.h*(.398 + (i%4)*.006)
            line(sh, sh.w*.5+r0*math.cos(angle), sh.h*.52+r0*math.sin(angle),
                 sh.w*.5+r1*math.cos(angle), sh.h*.52+r1*math.sin(angle),
                 teal, 1.7+(i%3)*.45, .58)
        crown(sh, sh.w*.66, sh.h*.195, sh.h*.12, chalk)
        type(sh, ctx, "queens_kicker", "Loud & Lovely",
             Box(sh.w*.12, sh.h*.26, sh.w*.62, sh.h*.08), size=35,
             color=teal, face=False, track=.16, min_read=17)
        type(sh, ctx, "queens_title", "Power",
             Box(sh.w*.035, sh.h*.37, sh.w*.93, sh.h*.31), size=400,
             color=chalk, min_read=80, track=-.05)
        line(sh, sh.w*.20, sh.h*.70, sh.w*.80, sh.h*.70, teal, 2.5)
        type(sh, ctx, "queens_footer", "Own Your Space",
             Box(sh.w*.16, sh.h*.74, sh.w*.68, sh.h*.08), size=37,
             color=chalk, face=False, track=.13, min_read=18)

    @support("lemonade32", "the lemon-soda chalkboard with an engraved transparent glass, speech bubble, and ingredient callouts")
    def lemonade32(sh, ctx):
        paper, ink, yellow, teal = (246, 241, 224), (29, 41, 38), (232, 157, 46), (31, 151, 153)
        ground(sh.cv, paper, (234, 226, 207), w=sh.w, h=sh.h)
        type(sh, ctx, "lemonade_small", "Organic / Citrus / Fresh",
             Box(sh.w*.055, sh.h*.055, sh.w*.43, sh.h*.055), size=23,
             color=ink, face=False, align="left", track=.12, min_read=11)
        bubble = Box(sh.w*.045, sh.h*.17, sh.w*.34, sh.h*.55)
        rect(sh, bubble, (255,253,246), radius=18, stroke=True,
             stroke_color=ink, width=2)
        type(sh, ctx, "lemonade_quote", "When Life\nGives You\nLemons, Make\nSomething\nBright!",
             Box(bubble.x+bubble.w*.08, bubble.y+bubble.h*.07,
                 bubble.w*.84, bubble.h*.86), size=54, color=ink,
             lines=5, track=-.025, min_read=20, leading=.86)
        glass = Box(sh.w*.32, sh.h*.20, sh.w*.40, sh.h*.66)
        image(sh, "T26003_01_lemonade-line-art.png", glass, contain=True)
        type(sh, ctx, "lemonade_head", "Pure\nLemons!",
             Box(sh.w*.56, sh.h*.10, sh.w*.40, sh.h*.34), size=126,
             color=teal, lines=2, track=-.04, min_read=42, leading=.80)
        type(sh, ctx, "lemonade_second", "Vitamin C",
             Box(sh.w*.61, sh.h*.65, sh.w*.36, sh.h*.14), size=75,
             color=(224, 105, 34), min_read=29, track=-.035)
        line(sh, sh.w*.62, sh.h*.81, sh.w*.95, sh.h*.81, yellow, 3.5)
        type(sh, ctx, "lemonade_footer", "Ice / Juice / Good Company",
             Box(sh.w*.59, sh.h*.84, sh.w*.37, sh.h*.06), size=17,
             color=ink, face=False, align="center", track=.08, min_read=9)

    @support("sunkiss32", "a retro lemon-sun product label with concentric rings, capsule captions, and a chunky display headline")
    def sunkiss32(sh, ctx):
        yellow, ink, orange, cream = (255, 216, 22), (31, 28, 24), (228, 75, 23), (255, 245, 213)
        ground(sh.cv, yellow, (245, 191, 13), w=sh.w, h=sh.h)
        rect(sh, Box(sh.w*.035, sh.h*.06, sh.w*.93, sh.h*.87), ink,
             radius=20)
        card = Box(sh.w*.055, sh.h*.085, sh.w*.89, sh.h*.82)
        rect(sh, card, yellow, radius=17)
        sh.cv.drawCircle(sh.w*.80, sh.h*.25, sh.h*.085,
                         paint(C(orange, .95)))
        sh.cv.drawCircle(sh.w*.80, sh.h*.25, sh.h*.098,
                         paint(C(ink, .8), style=skia.Paint.kStroke_Style,
                               width=2*sh.scale))
        type(sh, ctx, "sunkiss_top", "Sun / Citrus / Summer",
             Box(sh.w*.09, sh.h*.16, sh.w*.57, sh.h*.055), size=24,
             color=ink, face=False, align="left", track=.12, min_read=12)
        # A low-set, thickly offset title restores the source label's hierarchy.
        type(sh, ctx, "sunkiss_shadow", "Sunshine",
             Box(sh.w*.065, sh.h*.565, sh.w*.87, sh.h*.27), size=280,
             color=ink, track=-.04, min_read=78, collide=False)
        type(sh, ctx, "sunkiss_title", "Sunshine",
             Box(sh.w*.065, sh.h*.535, sh.w*.87, sh.h*.27), size=280,
             color=cream, track=-.04, min_read=78)
        type(sh, ctx, "sunkiss_second", "Sweet / Bright / Made Daily",
             Box(sh.w*.10, sh.h*.83, sh.w*.80, sh.h*.055), size=27,
             color=ink, face=False, track=.08, min_read=13)

    @support("typewall32", "a tight field of oversized specimen words, rotated like a typographic wallpaper rather than a name card")
    def typewall32(sh, ctx):
        yellow, ink = (249, 211, 25), (27, 24, 19)
        ground(sh.cv, yellow, (248, 223, 43), w=sh.w, h=sh.h)
        rows = ("Classic Culture", "Musical Sunshine", "Electric Love",
                "Good Times", "Sunday Forever", "Wonder Practice",
                "Louder Living", "Lovely People")
        sh.cv.save()
        sh.cv.clipRect(skia.Rect.MakeWH(sh.w, sh.h))
        sh.cv.translate(sh.w*.5, sh.h*.5)
        sh.cv.rotate(-8)
        sh.cv.translate(-sh.w*.5, -sh.h*.5)
        for row, wording in enumerate(rows):
            y = sh.h*(.018 + row*.114)
            box = Box(sh.w*.015, y, sh.w*.97, sh.h*.13)
            type(sh, ctx, f"wall_word{row}", wording, box,
                 size=162 if row%3 else 174, color=ink,
                 align="center" if row%2 else "left", min_read=42,
                 track=-.04, collide=False)
        sh.cv.restore()

    @support("manualbrew32", "a dark-ground, multicolour word-pair specimen with soft rounded letter rhythm and tiny note line")
    def manualbrew32(sh, ctx):
        ground(sh.cv, (26, 27, 34), (17, 18, 24), w=sh.w, h=sh.h)
        colors = ((245, 128, 161), (244, 209, 44), (151, 205, 48),
                  (64, 190, 222), (240, 92, 47), (226, 190, 48))
        def rainbow_word(key, word, box, palette, size):
            face = ctx["display"]
            phrase = support_copy(ctx, (), word)
            font_size = face.fit(phrase, size*sh.scale, box.w)
            full, _ = face.path(phrase, font_size)
            bounds = full.getBounds()
            if bounds.height() > box.h:
                font_size *= box.h/bounds.height()
                full, _ = face.path(phrase, font_size)
                bounds = full.getBounds()
            ox = box.x+(box.w-bounds.width())/2-bounds.x()
            oy = box.y+(box.h-bounds.height())/2-bounds.y()
            for i, glyph in enumerate(word):
                gp, _ = face.path(glyph, font_size)
                gb = gp.getBounds()
                advance = face.measure(phrase[:i], font_size) if i else 0
                gx = ox+advance
                sh.cv.save()
                sh.cv.translate(gx, oy)
                sh.cv.drawPath(gp, paint(C(palette[i%len(palette)])))
                sh.cv.restore()
                sh.mark(f"{key}_{i}",
                        Box(gx+gb.x(), oy+gb.y(), gb.width(), gb.height()),
                        collide=False)
        rainbow_word("brew_top", "Happy",
                     Box(sh.w*.07, sh.h*.14, sh.w*.86, sh.h*.36),
                     colors, 360)
        rainbow_word("brew_bottom", "Hour",
                     Box(sh.w*.12, sh.h*.48, sh.w*.76, sh.h*.35),
                     (colors[4], colors[1], colors[3], colors[2]), 350)
        type(sh, ctx, "brew_note", "A Playful Study In Colour",
             Box(sh.w*.12, sh.h*.86, sh.w*.76, sh.h*.05), size=21,
             color=(228, 225, 215), face=False, track=.12, min_read=11)

    @support("pastpresent32", "a three-step timeline on pink gingham with nested cream labels and teal-orange outlines")
    def pastpresent32(sh, ctx):
        pink, check, ink = (236, 91, 146), (250, 143, 178), (37, 31, 31)
        ground(sh.cv, pink, pink, w=sh.w, h=sh.h)
        cell = sh.w/21
        for y in range(0, int(sh.h), int(cell)):
            for x in range(0, int(sh.w), int(cell)):
                if (x//int(cell)+y//int(cell))%2:
                    sh.cv.drawRect(skia.Rect.MakeXYWH(x,y,cell,cell),
                                   paint(C(check, .9)))
        image(sh, "T26223_04_retro-hand-sign-blank-panels.png",
              Box(0, 0, sh.w, sh.h), contain=False, cover=True, bleed=True)
        for slot, wording, x, y, w, h, size in (
                ("timeline_past", "Past", .29, .205, .42, .15, 116),
                ("timeline_present", "Present", .16, .455, .68, .16, 120),
                ("timeline_future", "Future", .28, .735, .44, .16, 116)):
            type(sh, ctx, slot, wording,
                 Box(sh.w*x, sh.h*y, sh.w*w, sh.h*h), size=size,
                 color=ink, min_read=34, track=-.025)

    @support("herbalproduct32", "a vivid herbal-product carton with botanical side marks, a framed label, and a large central word")
    def herbalproduct32(sh, ctx):
        green, cream, dark = (20, 177, 36), (255, 247, 222), (35, 32, 29)
        orange, yellow = (244, 78, 31), (248, 214, 42)
        ground(sh.cv, green, green, w=sh.w, h=sh.h)
        card = Box(sh.w*.082, sh.h*.105, sh.w*.836, sh.h*.79)
        rect(sh, Box(card.x-sh.w*.018, card.y-sh.h*.025,
                     card.w+sh.w*.036, card.h+sh.h*.05), dark,
             radius=13, stroke=True, stroke_color=yellow, width=4)
        rect(sh, card, cream, radius=8, stroke=True,
             stroke_color=dark, width=3)

        # Source-like engraved sprigs flank a compact oval batch mark.
        cx, cy = sh.w*.50, sh.h*.245
        oval = Box(sh.w*.425, sh.h*.177, sh.w*.15, sh.h*.125)
        sh.cv.drawOval(skia.Rect.MakeXYWH(oval.x, oval.y, oval.w, oval.h),
                       paint(C(dark), style=skia.Paint.kStroke_Style,
                             width=2.8*sh.scale))
        type(sh, ctx, "herbal_batch", "1969",
             Box(oval.x+oval.w*.07, oval.y+oval.h*.17,
                 oval.w*.86, oval.h*.65), size=48, color=dark,
             min_read=22, track=-.02)
        for direction in (-1, 1):
            branch = skia.Path()
            branch.moveTo(cx+direction*sh.w*.045, cy)
            branch.cubicTo(cx+direction*sh.w*.12, cy-sh.h*.035,
                           cx+direction*sh.w*.18, cy-sh.h*.045,
                           cx+direction*sh.w*.25, cy-sh.h*.025)
            sh.cv.drawPath(branch, paint(C(dark), style=skia.Paint.kStroke_Style,
                                         width=2.4*sh.scale))
            for j in range(4):
                t = .24 + j*.18
                lx = cx+direction*sh.w*(.055+t*.18)
                ly = cy-sh.h*(.026 + .012*math.sin(j*.8))
                leaf = Box(lx-sh.w*.014, ly-sh.h*.012,
                           sh.w*.030, sh.h*.018)
                sh.cv.save()
                sh.cv.rotate(direction*(-28+j*4), lx, ly)
                sh.cv.drawOval(skia.Rect.MakeXYWH(leaf.x, leaf.y,
                                                  leaf.w, leaf.h),
                               paint(C(dark), style=skia.Paint.kStroke_Style,
                                     width=1.7*sh.scale))
                sh.cv.restore()

        # The orange new-stock burst deliberately crosses the frame corner.
        badge = star(sh, sh.w*.085, sh.h*.12, sh.h*.103, orange, points=12)
        type(sh, ctx, "herbal_new", "New",
             Box(sh.w*.035, sh.h*.095, sh.w*.10, sh.h*.045), size=33,
             color=cream, face=False, track=.02, min_read=15,
             collide=False)
        type(sh, ctx, "herbal_title", "Arabica",
             Box(card.x+card.w*.10, sh.h*.335, card.w*.80, sh.h*.22),
             size=265, color=dark, min_read=70, track=-.045)

        sub = Box(card.x+card.w*.12, sh.h*.585, card.w*.76, sh.h*.135)
        rect(sh, sub, cream, radius=40, stroke=True, stroke_color=dark,
             width=3)
        type(sh, ctx, "herbal_sub", "Whole Bean Coffee",
             Box(sub.x+sub.w*.06, sub.y+sub.h*.12,
                 sub.w*.88, sub.h*.76), size=36, color=dark,
             min_read=20, track=-.015)

        type(sh, ctx, "herbal_process", "Natural Process\nNet Wt: 12 Oz",
             Box(card.x+card.w*.06, sh.h*.755, card.w*.29, sh.h*.105),
             size=18, color=dark, face=False, align="left", lines=2,
             track=.015, min_read=10, leading=.95)
        type(sh, ctx, "herbal_roast", "Medium Roast",
             Box(card.x+card.w*.37, sh.h*.765, card.w*.34, sh.h*.09),
             size=44, color=dark, min_read=22, track=-.02)
        type(sh, ctx, "herbal_date", "Roast Date\n27 Jun 2024",
             Box(card.x+card.w*.75, sh.h*.755, card.w*.19, sh.h*.105),
             size=17, color=dark, face=False, align="right", lines=2,
             track=.015, min_read=10, leading=.95)

    @support("colosseum32", "the three-language colour specimen with repeating word forms, calm paper, and fine printer's marks")
    def colosseum32(sh, ctx):
        paper, navy, red = (247, 240, 219), (25, 57, 119), (221, 34, 36)
        ground(sh.cv, paper, (237, 228, 207), w=sh.w, h=sh.h)
        speckle(sh.cv, (118, 109, 91), n=7000, seed=26074, alpha=.065,
                rad=.85*sh.scale, w=sh.w, h=sh.h)
        words = ("spectacle", "harmonies", "antipodes")
        inks = (navy, red, navy)
        for i, (word, ink) in enumerate(zip(words, inks)):
            y = sh.h*(.115+i*.265)
            type(sh, ctx, f"colosseum_word{i}", word,
                 Box(sh.w*.15, y, sh.w*.70, sh.h*.19), size=220,
                 color=ink, align="left", min_read=54, track=-.04)
        type(sh, ctx, "colosseum_meta",
             "A Typeface With Spirit / Personality / Distinction",
             Box(sh.w*.22, sh.h*.895, sh.w*.56, sh.h*.045), size=16,
             color=red, face=False, track=.04, min_read=9)

    @support("glyphsheet32", "the green numeral-and-punctuation specimen with crisp one-line rows and small technical labels")
    def glyphsheet32(sh, ctx):
        green, ink, cream = (22, 177, 37), (17, 70, 26), (255, 255, 239)
        ground(sh.cv, green, (12, 152, 26), w=sh.w, h=sh.h)
        speckle(sh.cv, (7, 91, 22), n=3600, seed=26074, alpha=.075,
                rad=.8*sh.scale, w=sh.w, h=sh.h)
        type(sh, ctx, "glyph_row0", "0123456789",
             Box(sh.w*.055, sh.h*.075, sh.w*.89, sh.h*.20), size=270,
             color=cream, min_read=65, track=-.025)
        type(sh, ctx, "glyph_sample", "Pack my box with five dozen liquor jugs!",
             Box(sh.w*.07, sh.h*.325, sh.w*.86, sh.h*.11), size=70,
             color=ink, min_read=20, track=-.01)
        type(sh, ctx, "glyph_row1", "$&%£€!?()",
             Box(sh.w*.06, sh.h*.49, sh.w*.88, sh.h*.27), size=280,
             color=cream, min_read=62, track=-.035)
        line(sh, sh.w*.055, sh.h*.82, sh.w*.945, sh.h*.82, cream, 1.1, .84)
        type(sh, ctx, "glyph_footer", "Figures / Signs / Punctuation",
             Box(sh.w*.22, sh.h*.855, sh.w*.56, sh.h*.065), size=22,
             color=ink, face=False, track=.08, min_read=11)
        for x in (.035,.965):
            sh.cv.drawCircle(sh.w*x, sh.h*.87, sh.h*.018,
                             paint(C((220, 34, 38)),
                                   style=skia.Paint.kStroke_Style,
                                   width=2*sh.scale))
            line(sh, sh.w*x-sh.h*.028, sh.h*.87, sh.w*x+sh.h*.028,
                 sh.h*.87, (220,34,38), 1.3)

    @support("freakscene32", "the hot-pink editorial slab with a double-line display headline and a slim vertical caption")
    def freakscene32(sh, ctx):
        pink, ink, yellow = (234, 103, 157), (20, 24, 23), (244, 225, 82)
        ground(sh.cv, yellow, (241, 222, 74), w=sh.w, h=sh.h)
        panel = Box(sh.w*.026, sh.h*.04, sh.w*.948, sh.h*.92)
        rect(sh, panel, pink)
        sh.cv.save()
        sh.cv.clipRect(skia.Rect.MakeXYWH(panel.x, panel.y,
                                          panel.w, panel.h))
        speckle(sh.cv, (122, 68, 78), n=5000, seed=26074, alpha=.065,
                rad=.8*sh.scale, w=sh.w, h=sh.h)
        sh.cv.restore()
        type(sh, ctx, "freak_title", "Make\nNoise",
             Box(sh.w*.115, sh.h*.18, sh.w*.76, sh.h*.60), size=352,
             color=ink, lines=2, track=-.055, min_read=82, leading=.79)
        vertical_type(sh, ctx, "freak_side", "Type / Noise / Colour",
                      sh.w*.91, sh.h*.50, sh.h*.58, size=17,
                      color=ink, track=.07)
        vertical_type(sh, ctx, "freak_side_left",
                      "A Bright Two-Line Display Study",
                      sh.w*.075, sh.h*.50, sh.h*.55, size=15,
                      color=ink, track=.04)
        for x, y in ((.11,.83),(.83,.13)):
            sh.cv.drawCircle(sh.w*x, sh.h*y, sh.h*.033,
                             paint(C(yellow), style=skia.Paint.kStroke_Style,
                                   width=2.2*sh.scale))
            star(sh, sh.w*x, sh.h*y, sh.h*.017, yellow, points=8)

    @support("greetingsgrid32", "a six-language greeting-wall made from flat color blocks, oversized greetings, and tiny contrast labels")
    def greetingsgrid32(sh, ctx):
        pink, pale, blue = (252, 48, 105), (211, 159, 170), (0, 86, 126)
        yellow, green, navy = (255, 202, 5), (0, 112, 91), (17, 26, 77)
        cream, red, dark = (255, 234, 205), (234, 29, 55), (48, 35, 32)
        ground(sh.cv, pale, yellow, w=sh.w, h=sh.h)
        def greeting(key, word, box, bg, fg, size, *, shadow=None,
                     lines=1, face=True):
            rect(sh, box, bg, mark=False)
            inset = Box(box.x+box.w*.055, box.y+box.h*.12,
                        box.w*.89, box.h*.74)
            if shadow:
                type(sh, ctx, f"{key}_shadow", word,
                     Box(inset.x+sh.w*.009, inset.y+sh.h*.012,
                         inset.w, inset.h), size=size, color=shadow,
                     lines=lines, min_read=size*.25, track=-.025,
                     collide=False)
            type(sh, ctx, key, word, inset, size=size, color=fg,
                 lines=lines, min_read=size*.25, track=-.025)
        greeting("greet_zdravo", "Zdravo!",
                 Box(0,0,sh.w/3,sh.h*.25), pale, dark, 70)
        greeting("greet_howdy", "Howdy!",
                 Box(0,sh.h*.25,sh.w/3,sh.h*.25), blue, (220, 226, 83), 92)
        greeting("greet_halla", "Hallå!",
                 Box(sh.w/3,0,sh.w*2/3,sh.h*.50), yellow, red, 238,
                 shadow=dark)
        greeting("greet_bonjour", "Bonjour!",
                 Box(0,sh.h*.50,sh.w*2/3,sh.h*.50), pink, (255, 223, 77), 222)
        greeting("greet_privet", "Привет!",
                 Box(sh.w*2/3,sh.h*.50,sh.w/3,sh.h*.25), green, cream, 96)
        greeting("greet_hola", "Olá!",
                 Box(sh.w*2/3,sh.h*.75,sh.w/3,sh.h*.25), navy, yellow, 100)

    @support("roadrunner32", "the acid-lime quote poster with a hot-pink frame, tilted sentence, and a simple sunburst stamp")
    def roadrunner32(sh, ctx):
        lime, pink, ink = (220, 236, 69), (244, 89, 146), (42, 47, 25)
        ground(sh.cv, lime, (192, 220, 51), w=sh.w, h=sh.h)
        rect(sh, Box(sh.w*.035, sh.h*.045, sh.w*.93, sh.h*.91), pink,
             radius=7)
        rect(sh, Box(sh.w*.06, sh.h*.075, sh.w*.88, sh.h*.85), lime)
        type(sh, ctx, "road_kicker", "Radio On / Road Open",
             Box(sh.w*.10, sh.h*.12, sh.w*.62, sh.h*.055), size=22,
             color=ink, face=False, align="left", track=.13, min_read=11)
        sh.cv.save()
        sh.cv.clipRect(skia.Rect.MakeWH(sh.w, sh.h))
        sh.cv.translate(sh.w*.5, sh.h*.5)
        sh.cv.rotate(-7)
        sh.cv.translate(-sh.w*.5, -sh.h*.5)
        type(sh, ctx, "road_quote", "Radio On,\nWind At My\nBack!",
             Box(sh.w*.105, sh.h*.24, sh.w*.79, sh.h*.57), size=190,
             color=ink, lines=3, track=-.035, min_read=48, leading=.84)
        sh.cv.restore()
        stamp = skia.Rect.MakeXYWH(sh.w*.79, sh.h*.78,
                                   sh.w*.13, sh.h*.12)
        sh.cv.drawOval(stamp, paint(C((24, 48, 115)),
                                    style=skia.Paint.kStroke_Style,
                                    width=2.3*sh.scale))
        sh.mark("road_stamp", Box(sh.w*.79, sh.h*.78,
                                   sh.w*.13, sh.h*.12), collide=False)
        type(sh, ctx, "road_stamp_copy", "Go!",
             Box(sh.w*.805, sh.h*.805, sh.w*.10, sh.h*.055), size=24,
             color=(24, 48, 115), face=False, track=.08, min_read=11,
             collide=False)
