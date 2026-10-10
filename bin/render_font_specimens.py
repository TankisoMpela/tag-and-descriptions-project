#!/usr/bin/env python3
"""Render factual black-and-white font specimen sheets from a font cmap."""

from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont


WIDTH = 2400
BACKGROUND = (8, 8, 10)
FOREGROUND = (248, 248, 245)
MUTED = (155, 155, 155)
SCRIPT_NAMES = (
    "ARABIC",
    "ARMENIAN",
    "BENGALI",
    "CANADIAN SYLLABICS",
    "CYRILLIC",
    "DEVANAGARI",
    "ETHIOPIC",
    "GEORGIAN",
    "GREEK",
    "GUJARATI",
    "GURMUKHI",
    "HEBREW",
    "HIRAGANA",
    "KATAKANA",
    "KHMER",
    "LAO",
    "LATIN",
    "MALAYALAM",
    "MYANMAR",
    "ORIYA",
    "SINHALA",
    "TAMIL",
    "TELUGU",
    "THAI",
    "TIBETAN",
    "HANGUL",
)


def font_for(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def get_supported_codepoints(path: Path) -> list[int]:
    font = TTFont(path, lazy=True)
    cmap = font.getBestCmap() or {}
    return sorted(codepoint for codepoint, glyph in cmap.items() if glyph != ".notdef")


def script_for(char: str) -> str:
    name = unicodedata.name(char, "")
    for script in SCRIPT_NAMES:
        if script in name:
            return script.title()
    return "Other Unicode"


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fit_font_size(font_path: Path, text: str, max_width: int, start: int, minimum: int = 24) -> int:
    """Find the largest size that keeps a line inside the intended canvas."""
    size = start
    while size > minimum and ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(
        text, font=font_for(font_path, size)
    ) > max_width:
        size -= 2
    return size


def render_basic(font_path: Path, display_name: str, size: tuple[int, int]) -> Image.Image:
    width, height = size
    title_font = font_for(font_path, max(42, round(width * 0.035)))
    label_font = font_for(font_path, max(28, round(width * 0.022)))
    lines = [
        ("UPPERCASE", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("LOWERCASE", "abcdefghijklmnopqrstuvwxyz"),
        ("NUMBERS", "0123456789"),
        ("PUNCTUATION", "! ? . , : ; / & @ # % + - = ( ) [ ] { }"),
    ]
    content_width = width - 160
    rows = []
    for label, text in lines:
        target_width = content_width if label != "NUMBERS" else round(content_width * 0.7)
        start_size = round(width * (0.105 if label != "PUNCTUATION" else 0.075))
        specimen_size = fit_font_size(font_path, text, target_width, start_size)
        rows.append((label, text, font_for(font_path, specimen_size), specimen_size))

    row_heights = [font.getbbox(text)[3] - font.getbbox(text)[1] + label_font.size + 100 for _, text, font, _ in rows]
    block_height = title_font.size + label_font.size + 36 + sum(row_heights)
    y = max(60, (height - block_height) // 2)
    image = Image.new("RGB", size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    for text, font, color in ((display_name, title_font, FOREGROUND), ("CHARACTER SPECIMEN", label_font, MUTED)):
        text_width = draw.textlength(text, font=font)
        draw.text(((width - text_width) / 2, y), text, font=font, fill=color)
        y += font.size + (12 if color == FOREGROUND else 24)
    for label, text, font, _ in rows:
        label_width = draw.textlength(label, font=label_font)
        draw.text(((width - label_width) / 2, y), label, font=label_font, fill=MUTED)
        y += label_font.size + 12
        text_width = draw.textlength(text, font=font)
        draw.text(((width - text_width) / 2, y), text, font=font, fill=FOREGROUND)
        y += font.getbbox(text)[3] - font.getbbox(text)[1] + 100
    return image


def render_multilingual(font_path: Path, display_name: str, canvas_size: tuple[int, int]) -> Image.Image:
    width, height = canvas_size
    supported = get_supported_codepoints(font_path)
    grouped: dict[str, list[str]] = {}
    for codepoint in supported:
        if codepoint < 0x80 or codepoint > 0xFFFF:
            continue
        char = chr(codepoint)
        category = unicodedata.category(char)
        if not category.startswith("L"):
            continue
        script = script_for(char)
        grouped.setdefault(script, []).append(char)

    title_font = font_for(font_path, max(42, round(width * 0.035)))
    section_font = font_for(font_path, max(28, round(width * 0.022)))
    max_width = width - 160
    rows: list[tuple[str, list[str], ImageFont.FreeTypeFont]] = []
    for script, chars in grouped.items():
        text = " ".join(chars)
        specimen_size = round(width * 0.06)
        widest_char = max(chars, key=lambda char: ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(char, font=font_for(font_path, specimen_size)))
        specimen_size = fit_font_size(font_path, widest_char, max_width, specimen_size, 30)
        specimen_font = font_for(font_path, specimen_size)
        rows.append((script.upper(), wrap_text(ImageDraw.Draw(Image.new("RGB", (1, 1))), text, specimen_font, max_width), specimen_font))

    def block_height() -> int:
        return title_font.size + section_font.size + 40 + sum(
            section_font.size + 18 + len(lines) * (font.getbbox(lines[0])[3] - font.getbbox(lines[0])[1] + 24) + 28
            for _, lines, font in rows
        )

    while rows and block_height() > height - 100:
        smallest = min(font.size for _, _, font in rows)
        if smallest <= 12:
            raise SystemExit(
                "multilingual specimen cannot fit the requested canvas without "
                "dropping supported glyphs"
            )
        resized: list[tuple[str, list[str], ImageFont.FreeTypeFont]] = []
        for label, lines, font in rows:
            font_size = max(12, font.size - 4)
            resized_font = font_for(font_path, font_size)
            resized.append(
                (
                    label,
                    wrap_text(ImageDraw.Draw(Image.new("RGB", (1, 1))), " ".join(lines), resized_font, max_width),
                    resized_font,
                )
            )
        rows = resized

    image = Image.new("RGB", canvas_size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    y = max(50, (height - block_height()) // 2)
    for text, font, color in ((display_name, title_font, FOREGROUND), ("SUPPORTED MULTILINGUAL GLYPHS", section_font, MUTED)):
        text_width = draw.textlength(text, font=font)
        draw.text(((width - text_width) / 2, y), text, font=font, fill=color)
        y += font.size + (14 if color == FOREGROUND else 26)
    if not rows:
        text = "No non-ASCII letter glyphs found in the font cmap."
        draw.text(((width - draw.textlength(text, font=section_font)) / 2, y), text, font=section_font, fill=FOREGROUND)
    else:
        for label, lines, font in rows:
            label_width = draw.textlength(label, font=section_font)
            draw.text(((width - label_width) / 2, y), label, font=section_font, fill=MUTED)
            y += section_font.size + 18
            for line in lines:
                line_width = draw.textlength(line, font=font)
                draw.text(((width - line_width) / 2, y), line, font=font, fill=FOREGROUND)
                y += font.getbbox(line)[3] - font.getbbox(line)[1] + 24
            y += 28
    return image


def save_variants(render, main_path: Path, square_path: Path) -> None:
    main_path.parent.mkdir(parents=True, exist_ok=True)
    square_path.parent.mkdir(parents=True, exist_ok=True)
    render((2400, 1600)).save(main_path, format="PNG", optimize=True)
    render((1600, 1600)).save(square_path, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--name", default=None, help="Display name; defaults to the font filename")
    args = parser.parse_args()
    if args.font.suffix.lower() not in {".otf", ".ttf"}:
        raise SystemExit("The input must be an OTF or TTF file")
    if not args.font.is_file():
        raise SystemExit(f"Font not found: {args.font}")
    display_name = args.name or args.font.stem
    main_dir = args.output_dir / "main"
    square_dir = args.output_dir / "squares"
    save_variants(lambda size: render_basic(args.font, display_name, size), main_dir / "specimen-alphabet-numerals.png", square_dir / "specimen-alphabet-numerals.png")
    save_variants(lambda size: render_multilingual(args.font, display_name, size), main_dir / "specimen-multilingual-glyphs.png", square_dir / "specimen-multilingual-glyphs.png")
    for path in (
        main_dir / "specimen-alphabet-numerals.png",
        main_dir / "specimen-multilingual-glyphs.png",
        square_dir / "specimen-alphabet-numerals.png",
        square_dir / "specimen-multilingual-glyphs.png",
    ):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
