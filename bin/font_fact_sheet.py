#!/usr/bin/env python3
"""Print the factual font fact sheet Agent 27 uses for art direction.

Gives the visual director the machine-checkable half of its brief without asking
it to write fontTools/uharfbuzz code inline: metrics, cmap coverage, OpenType
feature inventory, and the exact shaping of proposed display words.

This is not package QA. Agent 13 owns technical validation; this is a read-only
description of what the font is, so copy and art direction stay grounded in
verified traits instead of plausible design language.

Usage:
    python3 bin/font_fact_sheet.py "font-factory/fonts/13-andallan/Font.otf" \\
        --shape "Silken Flourish" --shape "The Art of Quiet Luxury"
"""
from __future__ import annotations

import argparse
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

# Feature tags worth surfacing to an art director, with what they mean visually.
FEATURE_NOTES = {
    "liga": "standard ligatures",
    "dlig": "discretionary ligatures",
    "clig": "contextual ligatures",
    "rlig": "required ligatures",
    "salt": "stylistic alternates",
    "swsh": "swashes",
    "calt": "contextual alternates",
    "onum": "oldstyle figures",
    "lnum": "lining figures",
    "frac": "fractions",
    "sups": "superiors",
    "subs": "inferiors",
    "smcp": "small capitals",
    "c2sc": "capitals to small capitals",
    "kern": "kerning",
    "mark": "mark positioning",
    "mkmk": "mark-to-mark positioning",
    "locl": "localised forms",
    "ss01": "stylistic set 01",
    "ss02": "stylistic set 02",
    "ss03": "stylistic set 03",
}
JAPANESE_RANGES = (
    ("hiragana", 0x3040, 0x309F),
    ("katakana", 0x30A0, 0x30FF),
    ("kanji (CJK unified)", 0x4E00, 0x9FFF),
    ("halfwidth/fullwidth forms", 0xFF00, 0xFFEF),
)


def metric_block(font: TTFont) -> list[str]:
    head, hhea, os2 = font["head"], font["hhea"], font["OS/2"]
    rows = [
        f"- units per em: {head.unitsPerEm}",
        f"- ascender / descender / line gap (hhea): {hhea.ascent} / {hhea.descent} / {hhea.lineGap}",
        f"- cap height: {getattr(os2, 'sCapHeight', 'not set')}",
        f"- x-height: {getattr(os2, 'sxHeight', 'not set')}",
        f"- typo ascender / descender / gap (OS/2): {os2.sTypoAscender} / {os2.sTypoDescender} / {os2.sTypoLineGap}",
        f"- weight class / width class: {os2.usWeightClass} / {os2.usWidthClass}",
        f"- italic angle: {font['post'].italicAngle}",
    ]
    xh = getattr(os2, "sxHeight", 0) or 0
    cap = getattr(os2, "sCapHeight", 0) or 0
    if xh and cap:
        rows.append(f"- x-height / cap-height ratio: {xh / cap:.2f} (higher reads larger at small sizes)")
    if font["post"].italicAngle:
        rows.append("- italic or oblique: yes")
    return rows


def coverage_block(font: TTFont) -> list[str]:
    cmap = font.getBestCmap() or {}
    rows = [f"- mapped characters: {len(cmap)}"]
    latin = sum(1 for c in cmap if 0x41 <= c <= 0x5A or 0x61 <= c <= 0x7A)
    rows.append(f"- basic Latin A-Z/a-z: {latin}/52")
    for label, low, high in JAPANESE_RANGES:
        count = sum(1 for c in cmap if low <= c <= high)
        if count:
            rows.append(f"- {label}: {count}")
    if not any(low <= c <= high for c in cmap for _, low, high in JAPANESE_RANGES):
        rows.append("- Japanese coverage: none (do not claim Japanese support)")
    return rows


def feature_block(font: TTFont) -> list[str]:
    rows: list[str] = []
    rows.append(f"- legacy kern table: {'present' if 'kern' in font else 'absent'}")
    for table_tag, label in (("GSUB", "substitution"), ("GPOS", "positioning")):
        if table_tag not in font:
            rows.append(f"- {table_tag}: absent")
            continue
        table = font[table_tag].table
        scripts = sorted({record.ScriptTag for record in table.ScriptList.ScriptRecord})
        tags = sorted({record.FeatureTag for record in table.FeatureList.FeatureRecord})
        named = ", ".join(f"{t} ({FEATURE_NOTES[t]})" if t in FEATURE_NOTES else t for t in tags)
        rows.append(f"- {table_tag} ({label}) scripts: {', '.join(scripts)}")
        rows.append(f"- {table_tag} features: {named}")
        lookups = table.LookupList.LookupCount if table.LookupList else 0
        rows.append(f"- {table_tag} lookups: {lookups}")
    subs = [r for r in (font.get("GSUB").table.FeatureList.FeatureRecord if "GSUB" in font else [])]
    alternates = [r for r in subs if r.FeatureTag in ("salt", "swsh", "ss01", "ss02", "ss03", "calt")]
    if alternates:
        rows.append(f"- alternate-bearing features: {', '.join(sorted({r.FeatureTag for r in alternates}))}")
    else:
        rows.append("- alternate-bearing features: none (do not claim alternates)")
    return rows


def shape_block(path: Path, text: str) -> list[str]:
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    hb_font = hb.Font(face)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(hb_font, buffer, {"kern": True, "liga": True, "clig": True})
    infos, positions = buffer.glyph_infos, buffer.glyph_positions
    glyphs = [hb_font.glyph_to_string(i.codepoint) for i in infos]
    lines = [
        f'- "{text}"',
        f"  - {len(glyphs)} glyph(s) from {len(text)} character(s)"
        + ("  <- substitution or ligature is active" if len(glyphs) != len(text) else ""),
        f"  - sequence: {' '.join(glyphs)}",
    ]
    if len(glyphs) != len(text):
        lines.append("  - the font changes this word's glyph count: shape display copy before trusting it")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("font", type=Path, help="the font file to describe")
    parser.add_argument("--shape", action="append", default=[],
                        help="a display word or phrase to shape exactly; repeatable")
    args = parser.parse_args()

    path = args.font.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"font not found: {path}")

    font = TTFont(str(path))
    names = {r.nameID: r.toUnicode() for r in font["name"].names if r.platformID == 3}
    print(f"# Font Fact Sheet — {path.name}")
    print()
    print("## Identity")
    print(f"- family: {names.get(1, '?')}")
    print(f"- style: {names.get(2, '?')}")
    print(f"- version: {names.get(5, '?')}")
    print(f"- glyphs in font: {len(font.getGlyphOrder())}")
    print()
    for title, block in (
        ("Metrics", metric_block(font)),
        ("Character coverage", coverage_block(font)),
        ("OpenType features", feature_block(font)),
    ):
        print(f"## {title}")
        print("\n".join(block))
        print()
    if args.shape:
        print("## Exact shaping of proposed display copy")
        for text in args.shape:
            print("\n".join(shape_block(path, text)))
        print()
    print("## How to use this")
    print("These are verified facts. Do not claim a feature, language, or alternate")
    print("that is absent above, and do not use machine facts as visual inspiration:")
    print("this sheet constrains the copy, it does not design the image.")
    font.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
