#!/usr/bin/env python3
"""Render a paginated atlas of every Unicode-mapped character in an OTF/TTF."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont


PAGE_COLUMNS = 12
PAGE_ROWS = 12
CELL_WIDTH = 200
CELL_HEIGHT = 150
MARGIN_X = 80
HEADER_HEIGHT = 160
FOOTER_HEIGHT = 55
CANVAS_WIDTH = PAGE_COLUMNS * CELL_WIDTH + 2 * MARGIN_X
CANVAS_HEIGHT = HEADER_HEIGHT + PAGE_ROWS * CELL_HEIGHT + FOOTER_HEIGHT
BACKGROUND = (255, 255, 255)
FOREGROUND = (20, 20, 24)
MUTED = (105, 108, 115)
RULE = (225, 227, 231)
NONPRINTING_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}


def interface_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except OSError:
            return ImageFont.load_default()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def glyph_font(path: Path, size: int, cache: dict[int, ImageFont.FreeTypeFont]) -> ImageFont.FreeTypeFont:
    if size not in cache:
        cache[size] = ImageFont.truetype(str(path), size=size)
    return cache[size]


def mapped_codepoints(path: Path) -> tuple[list[int], int]:
    font = TTFont(str(path), lazy=True)
    try:
        cmap = font.getBestCmap() or {}
        invalid_scalars = sum(
            1 for codepoint in cmap
            if codepoint < 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF
        )
        codepoints = sorted(
            codepoint
            for codepoint, glyph_name in cmap.items()
            if glyph_name != ".notdef"
            and 0 <= codepoint <= 0x10FFFF
            and not 0xD800 <= codepoint <= 0xDFFF
        )
        return codepoints, invalid_scalars
    finally:
        font.close()


def render_page(
    path: Path,
    codepoints: list[int],
    page_index: int,
    page_total: int,
    title_font: ImageFont.ImageFont,
    label_font: ImageFont.ImageFont,
) -> Image.Image:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title = "FULL UNICODE-MAPPED CHARACTER SET"
    subtitle = f"PAGE {page_index + 1} OF {page_total}  |  {len(codepoints)} CHARACTERS"
    draw.text((MARGIN_X, 34), title, font=title_font, fill=FOREGROUND)
    draw.text((MARGIN_X, 92), subtitle, font=label_font, fill=MUTED)

    size_cache: dict[int, ImageFont.FreeTypeFont] = {}
    glyph_area_height = CELL_HEIGHT - 42
    for index, codepoint in enumerate(codepoints):
        row, column = divmod(index, PAGE_COLUMNS)
        x = MARGIN_X + column * CELL_WIDTH
        y = HEADER_HEIGHT + row * CELL_HEIGHT
        draw.line((x, y, x + CELL_WIDTH, y), fill=RULE, width=1)
        draw.line((x, y, x, y + CELL_HEIGHT), fill=RULE, width=1)

        character = chr(codepoint)
        category = unicodedata.category(character)
        if category not in NONPRINTING_CATEGORIES and not character.isspace():
            size = 88
            while size >= 28:
                font = glyph_font(path, size, size_cache)
                bounds = draw.textbbox((0, 0), character, font=font)
                if bounds[2] - bounds[0] <= CELL_WIDTH - 28 and bounds[3] - bounds[1] <= glyph_area_height:
                    break
                size -= 4
            font = glyph_font(path, max(24, size), size_cache)
            bounds = draw.textbbox((0, 0), character, font=font)
            glyph_width = max(0, bounds[2] - bounds[0])
            glyph_height = max(0, bounds[3] - bounds[1])
            gx = x + (CELL_WIDTH - glyph_width) / 2 - bounds[0]
            gy = y + 8 + (glyph_area_height - glyph_height) / 2 - bounds[1]
            draw.text((gx, gy), character, font=font, fill=FOREGROUND)

        label = f"U+{codepoint:04X}"
        label_width = draw.textlength(label, font=label_font)
        draw.text((x + (CELL_WIDTH - label_width) / 2, y + CELL_HEIGHT - 32), label, font=label_font, fill=MUTED)

    draw.line((MARGIN_X, HEADER_HEIGHT + PAGE_ROWS * CELL_HEIGHT, CANVAS_WIDTH - MARGIN_X,
               HEADER_HEIGHT + PAGE_ROWS * CELL_HEIGHT), fill=RULE, width=1)
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", type=Path, help="the original OTF/TTF to render")
    parser.add_argument("output_dir", type=Path, help="directory for atlas pages and manifest")
    parser.add_argument("--name", default=None, help="font label for the manifest; defaults to the source filename")
    args = parser.parse_args()

    source = args.font.expanduser().resolve()
    if source.suffix.lower() not in {".otf", ".ttf"} or not source.is_file():
        raise SystemExit("font must be an existing OTF or TTF file")
    codepoints, invalid_scalar_count = mapped_codepoints(source)
    if not codepoints:
        raise SystemExit("font has no Unicode-mapped characters to show")

    page_size = PAGE_COLUMNS * PAGE_ROWS
    pages = [codepoints[start:start + page_size] for start in range(0, len(codepoints), page_size)]
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    title_font = interface_font(34)
    label_font = interface_font(22)
    page_records = []
    for index, page_codes in enumerate(pages):
        filename = f"character-set-{index + 1:02d}.png"
        image = render_page(source, page_codes, index, len(pages), title_font, label_font)
        image.save(output / filename, format="PNG", optimize=True)
        page_records.append({
            "file": filename,
            "character_count": len(page_codes),
            "first_codepoint": f"U+{page_codes[0]:04X}",
            "last_codepoint": f"U+{page_codes[-1]:04X}",
        })

    manifest = {
        "font_file": source.name,
        "font_label": args.name or source.stem,
        "font_sha256": digest(source),
        "mapped_character_count": len(codepoints),
        "nonprinting_character_count": sum(
            1 for codepoint in codepoints
            if unicodedata.category(chr(codepoint)) in NONPRINTING_CATEGORIES or chr(codepoint).isspace()
        ),
        "invalid_unicode_scalar_mappings_excluded": invalid_scalar_count,
        "page_size": page_size,
        "pages": page_records,
        "coverage_note": "Shows every valid Unicode codepoint in the best cmap. GSUB-only alternates are not separate Unicode mappings; inspect the fact sheet and shaping tests for those.",
    }
    manifest_path = output / "glyph-atlas-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mapped characters: {len(codepoints)}; atlas pages: {len(pages)}")
    print(f"Source SHA-256: {manifest['font_sha256']}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
