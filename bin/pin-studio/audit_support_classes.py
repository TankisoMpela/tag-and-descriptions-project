#!/usr/bin/env python3
"""Render the whole support catalogue against six representative font styles.

    bin/pin-studio/.venv/bin/python bin/pin-studio/audit_support_classes.py

The diagnostic covers the active catalogue, but blackletter comparisons
respect the user-reviewed class gate. Outputs are paired JPEG sheets, a
compact all-template overview, and machine-readable audit.json preflight data.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import skia

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pin_studio as ps  # noqa: E402


CLASSES = {
    "blackletter": {
        "title": "Blackletter",
        "font": "font-factory/font-preparation/braewick/Braewick/Braewick-Regular.otf",
        "render_class": "blackletter",
        "about": "blackletter type with angular fractured strokes",
    },
    "handwritten": {
        "title": "Handwritten / elegant cursive",
        "font": "font-factory/fonts/16-Gladista-Script/Gladista.ttf",
        "render_class": "script",
        "about": "handwritten connected cursive script",
    },
    "tech-sports": {
        "title": "Tech / sports",
        "font": "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
        "render_class": "sports",
        "about": "technical sports and racing typeface",
    },
    "brush": {
        "title": "Brush",
        "font": "outputs/font-preparation/077-kuro-ripper/Kuro-Ripper/KuroRipper-Regular.otf",
        "render_class": "script",
        "about": "rough brush lettering",
    },
    "pixel": {
        "title": "Pixel",
        "font": "font-factory/fonts/Lost Contact/AOT Lost Contact – Contemporary Pixel Font RGMBLWG/OpenType-TT/AOT Lost Contact.ttf",
        "render_class": "sports",
        "about": "pixel arcade bitmap typeface with block-grid letterforms",
    },
    "display": {
        "title": "Display",
        "font": "font-factory/fonts/20-Blazher/Blazher – Modern Font Typeface 3T2KRAB/Blazher.otf",
        "render_class": "elegant",
        "about": "display font",
    },
    "family": {
        "title": "Real multi-style family",
        "font": "font-factory/fonts/3-Lindgre/Lindgre L2THLSE/Lindgre/Lindgre-Regular.otf",
        "font_label": "Lindgre family · Regular + Italic",
        "render_class": "elegant",
        "about": "a real two-style font family",
    },
}

# Source-of-truth references from REMAKE-MAP.md and the template source notes.
# A `None` source is intentional: its comparison's reference panel stays blank.
REFERENCES = {
    "line32": (None, "none", "No source reference was supplied; leave blank."),
    "duo32": ("T30173_08", "source", ""),
    "card32": (None, "none", "No source reference was supplied; leave blank."),
    "feature32": ("T27485_07", "source", ""),
    "neon32": ("T30173_07", "source", ""),
    "quote32": ("T24954_05", "source", ""),
    "crest32": ("T27485_08", "source", ""),
    "contour32": ("T30930_03", "source", ""),
    "mountain32": ("T33631_05", "source", ""),
    "hand32": ("T33144_02", "source", ""),
    "zebra32": ("T13692_01", "source", ""),
    "soldier32": ("T13692_03", "source", ""),
    "mirror32": ("T13692_12", "source", ""),
    "brutal32": ("T13692_06", "source", ""),
    "rio32": ("T24250_04", "source", ""),
    "boots32": ("T24507_04", "source", ""),
    "plakat32": ("T27673_00", "source", ""),
    "plakatart32": ("T27673_10", "source", ""),
    "mangos32": ("T30930_07", "source", ""),
    "alphabet32": ("T30930_05", "source", ""),
    "birvase32": ("T33110_08", "source", ""),
    "weightfamily32": ("T30930_01", "source", ""),
    "mangosboard32": ("T30930_04", "source", ""),
    "ovalword32": ("T30332_00", "source", ""),
    "stardust32": ("T30332_01", "source", ""),
    "cliffpostcard32": ("T30332_02", "source", ""),
    "kindersea32": ("T30332_04", "source", ""),
    "messageframe32": ("T30332_05", "source", ""),
    "contactlist32": ("T30332_06", "source", ""),
    "sunsetpromise32": ("T30332_07", "source", ""),
    "phonegarden32": ("T30332_08", "source", ""),
    "pixelquote32": ("T30332_09", "source", ""),
    "ravencover32": ("T28660_00", "source", ""),
    "voguecover32": ("T28576_03", "source", ""),
    "confident32": ("T28576_04", "source", ""),
    "storyteller32": ("T28576_05", "source", ""),
    "focusposter32": ("T28576_06", "source", ""),
    "wideclaim32": ("T28576_07", "source", ""),
    "blossom32": ("T28576_08", "source", ""),
    "neue32": ("T25441_04", "source", ""),
    "electromagnetic32": ("T19827_01", "source", ""),
    "demolition32": ("T19827_06", "source", ""),
    "yearposter32": ("T21458_04", "source", ""),
    "stadiumposter32": ("T21458_11", "source", ""),
    "signalclock32": ("T26392_08", "source", ""),
    "amberdawn32": ("T24908_00", "source", ""),
    "skinbadge32": ("T24908_01", "source", ""),
    "latestlook32": ("T24908_02", "source", ""),
    "gelatocards32": ("T24908_03", "source", ""),
    "meditation32": ("T25990_02", "source", ""),
    "strongweak32": ("T26289_00", "source", ""),
    "funkyfashion32": ("T26289_01", "source", ""),
    "typewall32": ("T26223_02", "source", ""),
    "manualbrew32": ("T26223_03", "source", ""),
    "pastpresent32": ("T26223_04", "source", ""),
    "herbalproduct32": ("T26223_05", "source", ""),
    "colosseum32": ("T26074_01", "source", ""),
    "glyphsheet32": ("T26074_02", "source", ""),
    "freakscene32": ("T26074_03", "source", ""),
    "greetingsgrid32": ("T26074_06", "source", ""),
    "roadrunner32": ("T26074_12", "source", ""),
}

ACTIVE = tuple(n for n in ps.SUPPORT_ORDER
               if n not in ps.SUPPORT_RETIRED and n not in ps.HTML_ONLY_SUPPORT)
COPY = {key: "" for key in ("line", "sub", "over", "word")}
CLASS_WORLDS = {
    "blackletter": ("vellum", "gilded"),
    "sports": ("asphalt", "chrome"),
    "script": ("graphite", "inkwell"),
}
PAGE_SIZE = 18
COLS = 3
CARD_W, CARD_H, GAP = 690, 282, 18
IMAGE_W, IMAGE_H = 326, 217
PAGE_HEAD = 82


def rgb_sample(image: skia.Image) -> list[int]:
    info = skia.ImageInfo.MakeN32(
        image.width(), image.height(), skia.AlphaType.kUnpremul_AlphaType)
    stride = info.minRowBytes()
    buf = bytearray(info.computeByteSize(stride))
    if not image.readPixels(info, buf, stride):
        raise RuntimeError("Skia could not read the rendered pixels")
    return [buf[y * stride + x * 4 + c]
            for y in range(6, image.height(), 12)
            for x in range(6, image.width(), 12)
            for c in range(3)]


def mean_delta(left: skia.Image, right: skia.Image) -> float:
    a, b = rgb_sample(left), rgb_sample(right)
    if len(a) != len(b):
        raise RuntimeError("Palette comparison images have different dimensions")
    return sum(abs(x - y) for x, y in zip(a, b)) / max(1, len(a))


def draw_text(canvas, text: str, x: float, y: float, font, color):
    canvas.drawString(text, x, y, font,
                      skia.Paint(Color4f=color, AntiAlias=True))


def scaled_image(canvas, image: skia.Image, x: float, y: float):
    src = skia.Rect.MakeWH(image.width(), image.height())
    dst = skia.Rect.MakeXYWH(x, y, IMAGE_W, IMAGE_H)
    canvas.drawImageRect(image, src, dst,
                         skia.SamplingOptions(skia.FilterMode.kLinear))


def make_pages(out: Path, slug: str, title: str, font_label: str,
               rendered: list[dict], reference_images: dict[str, skia.Image | None]):
    face = skia.Typeface.MakeFromFile(str(ps.LABEL))
    header_font = skia.Font(face, 25)
    title_font = skia.Font(face, 15)
    note_font = skia.Font(face, 13)
    width = COLS * CARD_W + (COLS + 1) * GAP
    rows = math.ceil(PAGE_SIZE / COLS)
    height = PAGE_HEAD + rows * CARD_H + (rows + 1) * GAP
    pages = math.ceil(len(rendered) / PAGE_SIZE)
    for page in range(pages):
        subset = rendered[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
        surf = skia.Surface.MakeRasterN32Premul(width, height)
        canvas = surf.getCanvas()
        canvas.clear(skia.Color(24, 25, 29))
        draw_text(canvas, f"{title}  ·  {page + 1}/{pages}", GAP, 36,
                  header_font, skia.Color4f(0.96, 0.96, 0.93, 1))
        draw_text(canvas, f"Test font: {font_label}  ·  1200×800 Skia render; source and render shown at equal scale",
                  GAP, 61, note_font, skia.Color4f(0.70, 0.72, 0.75, 1))
        for i, row in enumerate(subset):
            col, local_row = i % COLS, i // COLS
            x = GAP + col * (CARD_W + GAP)
            y = PAGE_HEAD + GAP + local_row * (CARD_H + GAP)
            card = skia.Rect.MakeXYWH(x, y, CARD_W, CARD_H)
            canvas.drawRoundRect(card, 10, 10,
                                 skia.Paint(Color=skia.Color(39, 41, 47),
                                            AntiAlias=True))
            slot = row["slot"]
            label = f"{slot:02d}  {row['template']}"
            draw_text(canvas, label, x + 12, y + 23, title_font,
                      skia.Color4f(0.97, 0.96, 0.91, 1))
            left_x, right_x = x + 12, x + 12 + IMAGE_W + 12
            image_y = y + 40
            draw_text(canvas, "REFERENCE", left_x, image_y - 5, note_font,
                      skia.Color4f(0.72, 0.78, 0.86, 1))
            draw_text(canvas, "TEST FONT", right_x, image_y - 5, note_font,
                      skia.Color4f(0.72, 0.88, 0.75, 1))
            ref = reference_images[row["template"]]
            if ref is not None:
                scaled_image(canvas, ref, left_x, image_y + 5)
            test = row.get("preview")
            if test is not None:
                scaled_image(canvas, test, right_x, image_y + 5)
            else:
                canvas.drawRect(skia.Rect.MakeXYWH(right_x, image_y + 5,
                                                   IMAGE_W, IMAGE_H),
                                skia.Paint(Color=skia.Color(58, 54, 49)))
            ref_id = row.get("reference_id") or "no source reference"
            kind = "closest inspiration" if row.get("reference_kind") == "closest" else ref_id
            fit = "ERROR" if row.get("errors") else "fit clean"
            details = f"{kind}  ·  {fit}  ·  {row.get('text_slots', 0)} text slots"
            draw_text(canvas, details[:78], x + 12, y + CARD_H - 9,
                      note_font, skia.Color4f(0.73, 0.75, 0.78, 1))
        img = surf.makeImageSnapshot()
        data = img.encodeToData(skia.EncodedImageFormat.kJPEG, 88)
        if data is None:
            raise RuntimeError(f"Could not encode contact sheet {slug}/{page + 1}")
        dest = out / f"{slug}-page-{page + 1:02d}-of-{pages:02d}.jpg"
        dest.write_bytes(bytes(data))
        print(f"  wrote {dest} ({len(subset)} pairs)")


def make_catalogue_overview(out: Path, rendered: list[dict]):
    """Write the compact all-template sheet from the same fresh renders."""
    cols, tile_w, image_h, label_h, gap = 5, 320, 214, 26, 16
    tile_h = image_h + label_h
    rows = math.ceil(len(rendered) / cols)
    width = cols * tile_w + (cols + 1) * gap
    height = rows * tile_h + (rows + 1) * gap
    face = skia.Typeface.MakeFromFile(str(ps.LABEL))
    label_font = skia.Font(face, 17)
    surf = skia.Surface.MakeRasterN32Premul(width, height)
    canvas = surf.getCanvas()
    canvas.clear(skia.Color(16, 17, 20))
    for i, row in enumerate(rendered):
        x = gap + (i % cols) * (tile_w + gap)
        y = gap + (i // cols) * (tile_h + gap)
        card = skia.Rect.MakeXYWH(x, y, tile_w, tile_h)
        canvas.drawRoundRect(card, 5, 5,
                             skia.Paint(Color=skia.Color(30, 31, 35),
                                        AntiAlias=True))
        preview = row.get("preview")
        if preview is not None:
            src = skia.Rect.MakeWH(preview.width(), preview.height())
            dst = skia.Rect.MakeXYWH(x, y, tile_w, image_h)
            canvas.drawImageRect(preview, src, dst,
                                 skia.SamplingOptions(skia.FilterMode.kLinear))
        draw_text(canvas, f"support-{row['slot']}_{row['template']}",
                  x + 8, y + image_h + 19, label_font,
                  skia.Color4f(0.94, 0.94, 0.92, 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    data = surf.makeImageSnapshot().encodeToData()
    if data is None:
        raise RuntimeError(f"Could not encode compact catalogue: {out}")
    out.write_bytes(bytes(data))
    print(f"  wrote compact catalogue {out} ({len(rendered)} templates)")


def make_individual_comparisons(out: Path, slug: str, title: str,
                                font_label: str, rendered: list[dict],
                                reference_images: dict[str, skia.Image | None]):
    """Write one full-resolution, side-by-side source/render image per template."""
    panel_w, panel_h = 1200, 800
    image_y = 102
    width, height = panel_w * 2, image_y + panel_h
    face = skia.Typeface.MakeFromFile(str(ps.LABEL))
    title_font, detail_font, panel_font = (
        skia.Font(face, 25), skia.Font(face, 15), skia.Font(face, 15))
    out.mkdir(parents=True, exist_ok=True)
    for row in rendered:
        surf = skia.Surface.MakeRasterN32Premul(width, height)
        canvas = surf.getCanvas()
        canvas.clear(skia.Color(24, 25, 29))
        ref_id = row.get("reference_id") or "no source reference"
        ref_kind = ("closest inspiration" if row.get("reference_kind") == "closest"
                    else "source" if row.get("reference_id") else "not supplied")
        fit = "RENDER ERROR" if row.get("errors") else "fit check clean"
        draw_text(canvas,
                  f"{title}  ·  {row['slot']:02d} {row['template']}",
                  28, 31, title_font,
                  skia.Color4f(0.96, 0.96, 0.93, 1))
        draw_text(canvas,
                  f"Test font: {font_label}  ·  Reference: {ref_id} ({ref_kind})  ·  {fit}",
                  28, 58, detail_font,
                  skia.Color4f(0.70, 0.72, 0.75, 1))
        ref_heading = ("REFERENCE" if row.get("reference_id")
                       else "REFERENCE · NOT SUPPLIED")
        draw_text(canvas, ref_heading, 28, 88, panel_font,
                  skia.Color4f(0.72, 0.78, 0.86, 1))
        draw_text(canvas, f"RENDER · {font_label}", panel_w + 28, 88,
                  panel_font, skia.Color4f(0.72, 0.88, 0.75, 1))
        for x, image, label in (
                (28, reference_images.get(row["template"]), "reference"),
                (panel_w + 28, row.get("preview"), "render")):
            if image is None:
                if label != "reference":
                    canvas.drawRect(skia.Rect.MakeXYWH(x, image_y, panel_w, panel_h),
                                    skia.Paint(Color=skia.Color(58, 54, 49)))
                    draw_text(canvas, f"NO {label.upper()} IMAGE", x + 32,
                              image_y + panel_h / 2, detail_font,
                              skia.Color4f(0.98, 0.78, 0.52, 1))
                continue
            src = skia.Rect.MakeWH(image.width(), image.height())
            dst = skia.Rect.MakeXYWH(x, image_y, panel_w, panel_h)
            canvas.drawImageRect(image, src, dst,
                                 skia.SamplingOptions(skia.FilterMode.kLinear))
        data = surf.makeImageSnapshot().encodeToData(
            skia.EncodedImageFormat.kJPEG, 92)
        if data is None:
            raise RuntimeError(f"Could not encode comparison {slug}/{row['template']}")
        dest = out / f"{row['slot']:02d}-{row['template']}.jpg"
        dest.write_bytes(bytes(data))
    print(f"  wrote {len(rendered)} individual comparisons to {out}")


def write_individual_index(out: Path, outputs: dict[str, dict]):
    """Write simple links to standalone comparison files, never an image grid."""
    lines = [
        "# Individual support-template comparisons",
        "",
        "Each link opens one image with its reference on the left and the fresh "
        "Skia render on the right. These are standalone comparisons, not a collage.",
        "",
    ]
    for slug, result in outputs.items():
        rows = result["results"]
        lines.extend((f"## {result['title']} — {result['font_label']}", ""))
        for row in rows:
            filename = f"{row['slot']:02d}-{row['template']}.jpg"
            lines.append(
                f"- [{row['slot']:02d} {row['template']}]({slug}/{filename})"
            )
        lines.append("")
    index = out / "README.md"
    index.write_text("\n".join(lines), encoding="utf-8")
    print(f"individual comparison index written to {index}")


def class_audit_names(slug: str, names: list[str], family: str,
                      family_styles: int, has_weight_triplet: bool) -> list[str]:
    """Return panels this test face can genuinely render.

    Family-only boards are rendered in their own audit group with actual sibling
    files; single-style specimens omit them rather than producing misleading
    blank/error comparisons. Blackletter also follows its explicitly reviewed
    suitability gate.
    """
    if slug == "blackletter":
        allowed = set(ps.support_names("blackletter", family, family_styles,
                                       has_weight_triplet))
        names = [name for name in names if name in allowed]
    if slug == "family":
        names = [name for name in names
                 if ps.SUPPORT_MIN_STYLES.get(name, 1) > 1]
    return [name for name in names
            if family_styles >= ps.SUPPORT_MIN_STYLES.get(name, 1)]


def run_class(out: Path, slug: str, cfg: dict, names: list[str], ref_dir: Path,
              refs: dict[str, tuple[str | None, str, str]], font_scale: tuple[int, int],
              individuals: bool = False):
    font_path = ROOT / cfg["font"]
    if not font_path.is_file():
        raise SystemExit(f"missing {slug} test font: {font_path}")
    font_label = cfg["font_label"]
    ctx = ps.build_ctx(font_path, "", COPY, about=cfg["about"],
                       cls=cfg["render_class"])
    ctx["themes"] = dict(
        ctx["themes"],
        **ps.assign_themes(
            ctx["name"], sorted(ACTIVE), cfg["render_class"],
            {n: CLASS_WORLDS.get(cfg["render_class"], ()) + ps.THEME_PREF[n]
             for n in ACTIVE},
        ),
    )
    styles = ctx["family_style_count"]
    names = class_audit_names(slug, names, ctx["family"], styles,
                              ctx["has_weight_triplet"])
    render_rows, records = [], []
    print(f"[{slug}] {font_label} ({ctx['family']} detected; {styles} real style(s))")
    for i, name in enumerate(names, 1):
        slot = ps.SUPPORT_ORDER.index(name) + 1
        source_id, source_kind, source_note = refs[name]
        reference = ref_dir / f"{source_id}.jpg" if source_id else None
        ref_image = (skia.Image.open(str(reference))
                     if reference is not None and reference.is_file() else None)
        if source_id and ref_image is None:
            raise SystemExit(f"missing mapped reference for {name}: {reference}")
        try:
            surf, sh = ps.render(name, ctx)
            image = surf.makeImageSnapshot()
            errors = ps.as_errors(name, sh)
            preview = image
            color = None
            if slug == "display":
                theme, _pal = ps.theme_for(name, ctx)
                alternate = "cherry" if theme["pal"] != "cherry" else "cobalt"
                alt_ctx = dict(ctx, palette_override=alternate)
                try:
                    alt_surface, _alt_sh = ps.render(name, alt_ctx)
                    color = {
                        "base_palette": theme["pal"],
                        "alternate_palette": alternate,
                        "mean_rgb_delta": round(mean_delta(
                            image, alt_surface.makeImageSnapshot()), 3),
                    }
                except Exception as color_exc:
                    color = {"error": f"{type(color_exc).__name__}: {color_exc}"}
            typed = [s for s in sh.slots if s.size > 0]
            scale = max(0.01, sh.scale)
            row = {
                "slot": slot,
                "template": name,
                "reference_id": source_id,
                "reference_kind": source_kind,
                "reference_note": source_note,
                "preview": preview,
                "errors": [e["message"] for e in errors],
                "notes": list(sh.notes),
                "text_slots": len(typed),
                "min_text_size_at_2400px": (round(min(s.size for s in typed) / scale, 1)
                                             if typed else None),
                "typed_lines": sum(s.lines for s in typed),
                "style_count": styles,
                "style_gate_required": ps.SUPPORT_MIN_STYLES.get(name, 1),
                "style_gate_pass": styles >= ps.SUPPORT_MIN_STYLES.get(name, 1),
                "current_gate_pass": ps.support_fits(
                    name, cfg["render_class"], ctx["family"], styles,
                    ctx["has_weight_triplet"]),
                "theme": ps.theme_for(name, ctx)[0]["pal"],
                "color_test": color,
            }
        except Exception as exc:  # Keep the matrix complete when one panel crashes.
            preview = None
            print(f"  render failed: {name}: {type(exc).__name__}: {exc}")
            row = {
                "slot": slot, "template": name, "reference_id": source_id,
                "reference_kind": source_kind, "reference_note": source_note,
                "preview": None, "errors": [f"render exception: {type(exc).__name__}: {exc}"],
                "notes": [], "text_slots": 0, "min_text_size_at_2400px": None,
                "typed_lines": 0, "style_count": styles,
                "style_gate_required": ps.SUPPORT_MIN_STYLES.get(name, 1),
                "style_gate_pass": styles >= ps.SUPPORT_MIN_STYLES.get(name, 1),
                "current_gate_pass": False, "theme": None, "color_test": None,
            }
        records.append({key: value for key, value in row.items()
                        if key != "preview"})
        render_rows.append(row)
        if i % 10 == 0 or i == len(names):
            print(f"  {i}/{len(names)} rendered")
    reference_images = {
        r["template"]: (
            skia.Image.open(str(ref_dir / f"{refs[r['template']][0]}.jpg"))
            if refs[r["template"]][0] else None)
        for r in render_rows
    }
    if individuals:
        make_individual_comparisons(out / "individual-comparisons" / slug,
                                    slug, cfg["title"], font_label,
                                    render_rows, reference_images)
    else:
        make_pages(out, slug, cfg["title"], font_label, render_rows,
                   reference_images)
        if slug == "tech-sports":
            make_catalogue_overview(
                ROOT / "font-factory/support-references/previews" /
                "template-preview-catalogue.png", render_rows)
    return {
        "title": cfg["title"], "font": cfg["font"], "font_label": font_label,
        "render_class": cfg["render_class"], "detected_family": ctx["family"],
        "family_reason": ctx["why"], "real_style_count": styles,
        "results": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "font-factory/support-references/class-audit-2026-10-14")
    parser.add_argument("--class", dest="classes", action="append",
                        choices=tuple(CLASSES), help="run one group; repeatable")
    parser.add_argument("--limit", type=int,
                        help="render only the first N templates (for a benchmark)")
    parser.add_argument("--template", dest="templates", action="append",
                        choices=tuple(ACTIVE),
                        help="render only this template; repeat to select several")
    parser.add_argument("--short-edge", type=int, default=800,
                        help="rendering size used for comparison; default 800px")
    parser.add_argument("--individuals", action="store_true",
                        help="write one reference/render image per template; skip all collages")
    args = parser.parse_args()
    if args.short_edge < 400:
        parser.error("--short-edge must be at least 400 pixels")
    active = list(ACTIVE)
    if set(REFERENCES) != set(active):
        missing = sorted(set(active) - set(REFERENCES))
        extra = sorted(set(REFERENCES) - set(active))
        parser.error(f"reference map drift; missing={missing}, extra={extra}")
    if args.templates and args.limit is not None:
        parser.error("--template and --limit cannot be combined")
    ref_dir = ROOT / "font-factory/support-references"
    bad_refs = [f"{name}:{ref[0]}" for name, ref in REFERENCES.items()
                if ref[0] and not (ref_dir / f"{ref[0]}.jpg").is_file()]
    if bad_refs:
        parser.error("missing reference files: " + ", ".join(bad_refs))
    if args.templates:
        selected = set(args.templates)
        active = [name for name in active if name in selected]
    elif args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        active = active[:args.limit]
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    args.out.mkdir(parents=True, exist_ok=True)
    original = ps.FRAMES["3x2"]
    ps.FRAMES["3x2"] = (args.short_edge * 3 // 2, args.short_edge)
    outputs = {}
    try:
        for slug in args.classes or list(CLASSES):
            cfg = dict(CLASSES[slug])
            cfg["font_label"] = cfg.get("font_label", Path(cfg["font"]).name)
            outputs[slug] = run_class(args.out, slug, cfg, active, ref_dir,
                                      REFERENCES, original,
                                      individuals=args.individuals)
    finally:
        ps.FRAMES["3x2"] = original
    serial = {
        "schema": 1,
        "active_template_count": len(ACTIVE),
        "tested_template_counts_by_class": {
            slug: len(result["results"]) for slug, result in outputs.items()
        },
        "render_size": [args.short_edge * 3 // 2, args.short_edge],
        "palette_test": "display sample: assigned theme vs the alternate of cobalt/cherry; mean RGB sample delta > 1 is materially movable",
        "classes": outputs,
    }
    if set(outputs) == set(CLASSES) and len(active) == len(ACTIVE):
        (args.out / "audit.json").write_text(
            json.dumps(serial, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"audit written to {args.out / 'audit.json'}")
    else:
        print("partial audit; existing full audit.json left unchanged")
    if args.individuals and not args.templates:
        write_individual_index(args.out / "individual-comparisons", outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
