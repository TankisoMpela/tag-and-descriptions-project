#!/usr/bin/env python3
"""Create deterministic, typography-led font promo images from real glyph outlines.

The prototype deliberately keeps all product-font lettering as SVG paths. This
means the final renderer never has to resolve the product font by family name.
The layouts are fixed, ratio-specific compositions rather than crops of one
another. A seeded vector grain layer supplies restrained print texture without
using generated photography or an image model.
"""

from __future__ import annotations

import argparse
import html
import random
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


CREAM = "#efe4c4"
PAPER = "#e5d7b5"
NAVY = "#142a40"
INK = "#172231"
RED = "#a8442e"
GOLD = "#bf8b3d"
WHITE = "#fff7df"
MUTED = "#bda982"


@dataclass
class ShapedGlyph:
    glyph_name: str
    x_advance: int
    y_advance: int
    x_offset: int
    y_offset: int


class OutlineFont:
    """Shape strings and emit positioned SVG paths for one font file."""

    def __init__(self, path: Path, font_index: int = 0) -> None:
        self.path = path
        self.ttfont = TTFont(path, fontNumber=font_index)
        self.upm = self.ttfont["head"].unitsPerEm
        self.glyph_set = self.ttfont.getGlyphSet()
        self.glyph_order = self.ttfont.getGlyphOrder()
        self.hb_blob = hb.Blob.from_file_path(str(path))
        self.hb_face = hb.Face(self.hb_blob, index=font_index)
        self.hb_font = hb.Font(self.hb_face)
        self.hb_font.scale = (self.upm, self.upm)

    def glyph_name(self, glyph_id: int) -> str:
        name = self.hb_font.glyph_to_string(glyph_id)
        if name in self.glyph_set:
            return name
        if name.startswith("gid"):
            try:
                index = int(name[3:])
            except ValueError:
                return name
            if 0 <= index < len(self.glyph_order):
                return self.glyph_order[index]
        return name

    def shape(self, text: str) -> list[ShapedGlyph]:
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self.hb_font, buffer, {"kern": True, "liga": True})
        return [
            ShapedGlyph(
                glyph_name=self.glyph_name(info.codepoint),
                x_advance=position.x_advance,
                y_advance=position.y_advance,
                x_offset=position.x_offset,
                y_offset=position.y_offset,
            )
            for info, position in zip(buffer.glyph_infos, buffer.glyph_positions)
        ]

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        shaped = self.shape(text)
        if not shaped:
            return 0
        scale = size / self.upm
        return sum(glyph.x_advance for glyph in shaped) * scale + tracking * (len(shaped) - 1)

    def path_for(self, glyph_name: str) -> str:
        glyph = self.glyph_set[glyph_name]
        pen = SVGPathPen(self.glyph_set)
        glyph.draw(pen)
        return pen.getCommands()

    def draw_text(
        self,
        svg: list[str],
        text: str,
        x: float,
        baseline: float,
        size: float,
        fill: str,
        *,
        anchor: str = "left",
        tracking: float = 0,
        max_width: float | None = None,
        stroke: str | None = None,
        stroke_width: float = 0,
        opacity: float = 1,
    ) -> float:
        """Draw shaped text and return the final rendered width in pixels."""
        shaped = self.shape(text)
        scale = size / self.upm
        natural_width = sum(glyph.x_advance for glyph in shaped) * scale + tracking * max(len(shaped) - 1, 0)
        if max_width is not None and natural_width > max_width and natural_width:
            size *= max_width / natural_width
            scale = size / self.upm
            natural_width = sum(glyph.x_advance for glyph in shaped) * scale + tracking * max(len(shaped) - 1, 0)

        if anchor == "center":
            start_x = x - natural_width / 2
        elif anchor == "right":
            start_x = x - natural_width
        else:
            start_x = x

        cursor = start_x
        stroke_attr = "none" if stroke is None else stroke
        stroke_attr_width = 0 if stroke is None else stroke_width / scale

        missing = [
            glyph.glyph_name
            for glyph in shaped
            if glyph.glyph_name not in self.glyph_set or glyph.glyph_name == ".notdef"
        ]
        if missing:
            raise ValueError(f"font has no drawable glyph outline for: {', '.join(sorted(set(missing)))}")

        for index, glyph in enumerate(shaped):
            path = self.path_for(glyph.glyph_name)
            if path:
                tx = cursor + glyph.x_offset * scale
                ty = baseline - glyph.y_offset * scale
                svg.append(
                    f'<path d="{path}" transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f} {-scale:.6f})" '
                    f'fill="{fill}" stroke="{stroke_attr}" stroke-width="{stroke_attr_width:.3f}" '
                    f'paint-order="stroke fill" opacity="{opacity:.3f}"/>'
                )
            cursor += glyph.x_advance * scale
            if index < len(shaped) - 1:
                cursor += tracking
        return natural_width


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def rect(svg: list[str], x: float, y: float, width: float, height: float, fill: str, opacity: float = 1) -> None:
    svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="{fill}" opacity="{opacity:.3f}"/>')


def line(svg: list[str], x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2, opacity: float = 1) -> None:
    svg.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width:.2f}" opacity="{opacity:.3f}"/>')


def circle(svg: list[str], cx: float, cy: float, radius: float, fill: str, opacity: float = 1, stroke: str | None = None, stroke_width: float = 0) -> None:
    stroke_attr = "none" if stroke is None else stroke
    svg.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="{fill}" stroke="{stroke_attr}" stroke-width="{stroke_width:.2f}" opacity="{opacity:.3f}"/>')


def polygon(svg: list[str], points: str, fill: str, opacity: float = 1) -> None:
    svg.append(f'<polygon points="{points}" fill="{fill}" opacity="{opacity:.3f}"/>')


def checker(svg: list[str], x: float, y: float, columns: int, size: float, fill: str, alternate: str) -> None:
    for row in range(2):
        for column in range(columns):
            rect(svg, x + column * size, y + row * size, size, size, fill if (row + column) % 2 == 0 else alternate)


def grain(svg: list[str], width: int, height: int, seed: int, light: bool = True) -> None:
    """Add a small seeded vector texture, intentionally subtle at thumbnail size."""
    rng = random.Random(seed)
    light_color = WHITE if light else INK
    dark_color = INK if light else WHITE
    for _ in range(420):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        dot_size = rng.uniform(0.7, 4.5)
        color = light_color if rng.random() > 0.42 else dark_color
        rect(svg, x, y, dot_size, dot_size * rng.uniform(0.5, 1.8), color, rng.uniform(0.025, 0.11))
    for _ in range(18):
        x = rng.uniform(-width * 0.1, width * 0.9)
        y = rng.uniform(0, height)
        line(svg, x, y, x + rng.uniform(50, 240), y + rng.uniform(-8, 8), dark_color, rng.uniform(1, 3), rng.uniform(0.03, 0.1))


def label(font: OutlineFont, svg: list[str], text: str, x: float, baseline: float, size: float, fill: str, *, anchor: str = "left", tracking: float = 1.2, max_width: float | None = None) -> None:
    font.draw_text(svg, text, x, baseline, size, fill, anchor=anchor, tracking=tracking, max_width=max_width)


def header(svg: list[str], width: int, height: int, background: str) -> None:
    svg.extend([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{background}"/>',
    ])


def finish(svg: list[str]) -> str:
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def cover(regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    svg: list[str] = []
    header(svg, width, height, CREAM)
    grain(svg, width, height, 101, light=True)
    if width > height:
        label(sans, svg, "PAPERMOON  /  TYPE SPECIMEN", 62, 62, 22, NAVY, tracking=2.4)
        label(sans, svg, "01", width - 62, 62, 22, RED, anchor="right", tracking=2.4)
        line(svg, 62, 88, width - 62, 88, RED, 2, 0.8)
        regular.draw_text(svg, font_name.upper(), width / 2, 400, 355, NAVY, anchor="center", max_width=width - 120, stroke=CREAM, stroke_width=2)
        label(sans, svg, "DISPLAY TYPE / USE CASE", width / 2, 475, 28, RED, anchor="center", tracking=4.0)
        rect(svg, 0, 610, width, height - 610, NAVY)
        grain(svg, width, height - 610, 102, light=False)
        stamp.draw_text(svg, "RACING", width * 0.30, 810, 172, CREAM, anchor="center", max_width=width * 0.52)
        label(sans, svg, "REGULAR  +  STAMP", width * 0.78, 730, 25, GOLD, anchor="center", tracking=3.0)
        line(svg, width * 0.66, 760, width * 0.90, 760, GOLD, 2)
        checker(svg, width * 0.68, 796, 8, 18, GOLD, CREAM)
        label(sans, svg, "TWO DISPLAY STYLES  /  2026", width * 0.78, 880, 18, CREAM, anchor="center", tracking=2.2)
    else:
        label(sans, svg, "PAPERMOON / TYPE SPECIMEN", 54, 58, 18, NAVY, tracking=1.5)
        label(sans, svg, "01", width - 54, 58, 18, RED, anchor="right", tracking=2.0)
        line(svg, 54, 82, width - 54, 82, RED, 2)
        regular.draw_text(svg, font_name.upper(), width / 2, 382, 260, NAVY, anchor="center", max_width=width - 90, stroke=CREAM, stroke_width=2)
        label(sans, svg, "DISPLAY TYPE / USE CASE", width / 2, 445, 21, RED, anchor="center", tracking=2.2)
        rect(svg, 0, 550, width, height - 550, NAVY)
        grain(svg, width, height - 550, 102, light=False)
        stamp.draw_text(svg, "RACING", width / 2, 730, 144, CREAM, anchor="center", max_width=width - 90)
        label(sans, svg, "REGULAR  +  STAMP", width / 2, 812, 22, GOLD, anchor="center", tracking=2.4)
        checker(svg, 332, 852, 8, 16, GOLD, CREAM)
        label(sans, svg, "TWO DISPLAY STYLES  /  2026", width / 2, 955, 16, CREAM, anchor="center", tracking=1.6)
    return svg


def race_repeat(regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    svg: list[str] = []
    header(svg, width, height, NAVY)
    grain(svg, width, height, 201, light=False)
    if width > height:
        label(sans, svg, "02  /  DISPLAY TYPE", 64, 66, 22, GOLD, tracking=2.2)
        label(sans, svg, f"{font_name.upper()} REGULAR", width - 64, 66, 20, CREAM, anchor="right", tracking=2.0)
        regular.draw_text(svg, "RACE", 80, 360, 395, CREAM, max_width=width - 160, stroke=NAVY, stroke_width=3)
        regular.draw_text(svg, "REPEAT", width - 80, 625, 270, RED, anchor="right", tracking=1.5, max_width=width - 160)
        polygon(svg, f"{width * 0.08:.0f},700 {width * 0.74:.0f},670 {width * 0.69:.0f},770 {width * 0.04:.0f},800", RED, 0.92)
        label(sans, svg, "FULL SPEED / CUSTOM LETTERING", width * 0.42, 755, 25, CREAM, anchor="center", tracking=2.8)
        checker(svg, width * 0.73, 820, 9, 20, GOLD, NAVY)
        stamp.draw_text(svg, "GO", width * 0.86, 890, 78, GOLD, anchor="center", max_width=width * 0.18)
        line(svg, 64, 918, width - 64, 918, GOLD, 2)
        label(sans, svg, "A TYPEFACE BUILT FOR HEADLINES", width / 2, 958, 18, CREAM, anchor="center", tracking=2.4)
    else:
        label(sans, svg, "02 / DISPLAY TYPE", 50, 58, 18, GOLD, tracking=1.5)
        label(sans, svg, "REGULAR", width - 50, 58, 18, CREAM, anchor="right", tracking=1.8)
        regular.draw_text(svg, "RACE", width / 2, 330, 270, CREAM, anchor="center", max_width=width - 80)
        regular.draw_text(svg, "REPEAT", width / 2, 535, 168, RED, anchor="center", max_width=width - 80)
        polygon(svg, "70,600 930,570 900,660 42,688", RED, 0.92)
        label(sans, svg, "FULL SPEED / CUSTOM LETTERING", width / 2, 635, 22, CREAM, anchor="center", tracking=1.8, max_width=width - 100)
        checker(svg, 170, 760, 9, 18, GOLD, NAVY)
        stamp.draw_text(svg, "GO", width / 2, 895, 116, GOLD, anchor="center", max_width=width - 160)
        label(sans, svg, "BUILT FOR HEADLINES", width / 2, 966, 16, CREAM, anchor="center", tracking=1.6)
    return svg


def road_form(regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    svg: list[str] = []
    header(svg, width, height, RED)
    grain(svg, width, height, 301, light=False)
    if width > height:
        label(sans, svg, "03  /  RETRO RACING", 62, 62, 22, CREAM, tracking=2.0)
        label(sans, svg, "REGULAR + STAMP", width - 62, 62, 20, GOLD, anchor="right", tracking=2.0)
        regular.draw_text(svg, "ROAD", width * 0.30, 330, 300, CREAM, anchor="center", max_width=width * 0.50, stroke=RED, stroke_width=3)
        regular.draw_text(svg, "FORM", width * 0.30, 570, 275, CREAM, anchor="center", max_width=width * 0.50)
        rect(svg, width * 0.60, 150, width * 0.32, 570, NAVY, 0.94)
        stamp.draw_text(svg, "RIDE", width * 0.76, 350, 170, CREAM, anchor="center", max_width=width * 0.28)
        stamp.draw_text(svg, "HARD", width * 0.76, 535, 152, CREAM, anchor="center", max_width=width * 0.28)
        circle(svg, width * 0.76, 820, 104, GOLD, 0.95)
        stamp.draw_text(svg, "ESTD", width * 0.76, 795, 36, NAVY, anchor="center", tracking=1.0)
        label(sans, svg, "1957", width * 0.76, 850, 43, NAVY, anchor="center", tracking=2.0)
        line(svg, 62, 790, width * 0.48, 790, CREAM, 3)
        label(sans, svg, "BUILT TO MOVE", width * 0.28, 850, 26, CREAM, anchor="center", tracking=3.2)
        checker(svg, 62, 900, 15, 18, GOLD, RED)
    else:
        label(sans, svg, "03 / RETRO RACING", 48, 58, 18, CREAM, tracking=1.4)
        label(sans, svg, "REGULAR + STAMP", width - 48, 58, 16, GOLD, anchor="right", tracking=1.4)
        regular.draw_text(svg, "ROAD", width / 2, 300, 235, CREAM, anchor="center", max_width=width - 90)
        regular.draw_text(svg, "FORM", width / 2, 500, 220, CREAM, anchor="center", max_width=width - 90)
        rect(svg, 78, 570, width - 156, 235, NAVY, 0.94)
        stamp.draw_text(svg, "RIDE HARD", width / 2, 715, 125, CREAM, anchor="center", max_width=width - 190)
        circle(svg, width / 2, 884, 72, GOLD, 0.95)
        stamp.draw_text(svg, "ESTD", width / 2, 870, 25, NAVY, anchor="center", tracking=0.8)
        label(sans, svg, "1957", width / 2, 908, 28, NAVY, anchor="center", tracking=1.4)
        checker(svg, 146, 970, 12, 14, GOLD, RED)
    return svg


def style_split(regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    svg: list[str] = []
    header(svg, width, height, CREAM)
    grain(svg, width, height, 401, light=True)
    if width > height:
        midpoint = width / 2
        rect(svg, midpoint, 0, midpoint, height, NAVY)
        grain(svg, int(midpoint), height, 402, light=False)
        line(svg, midpoint, 48, midpoint, height - 48, GOLD, 2)
        label(sans, svg, "04  /  TWO VOICES", 54, 65, 21, NAVY, tracking=2.0)
        label(sans, svg, font_name.upper(), width - 54, 65, 21, CREAM, anchor="right", tracking=2.0)
        label(sans, svg, "REGULAR", midpoint / 2, 170, 25, RED, anchor="center", tracking=3.0)
        label(sans, svg, "STAMP", midpoint + midpoint / 2, 170, 25, GOLD, anchor="center", tracking=3.0)
        regular.draw_text(svg, "RACE", midpoint / 2, 500, 285, NAVY, anchor="center", max_width=midpoint - 80)
        stamp.draw_text(svg, "RACE", midpoint + midpoint / 2, 500, 285, CREAM, anchor="center", max_width=midpoint - 80)
        label(sans, svg, "CLEAN", midpoint / 2, 610, 20, RED, anchor="center", tracking=2.4)
        label(sans, svg, "DISTRESSED", midpoint + midpoint / 2, 610, 20, GOLD, anchor="center", tracking=2.4)
        line(svg, 54, 790, midpoint - 54, 790, RED, 2)
        line(svg, midpoint + 54, 790, width - 54, 790, GOLD, 2)
        label(sans, svg, "ONE FAMILY / TWO DISPLAY STYLES", width / 2, 900, 22, RED, anchor="center", tracking=2.8)
        checker(svg, width / 2 - 90, 930, 10, 18, RED, CREAM)
    else:
        midpoint = height / 2
        rect(svg, 0, midpoint, width, midpoint, NAVY)
        grain(svg, width, int(midpoint), 402, light=False)
        line(svg, 48, midpoint, width - 48, midpoint, GOLD, 2)
        label(sans, svg, "04 / TWO VOICES", 48, 62, 18, NAVY, tracking=1.5)
        label(sans, svg, font_name.upper(), width - 48, 62, 18, CREAM, anchor="right", tracking=1.8)
        label(sans, svg, "REGULAR", width / 2, 150, 23, RED, anchor="center", tracking=2.6)
        label(sans, svg, "STAMP", width / 2, 590, 23, GOLD, anchor="center", tracking=2.6)
        regular.draw_text(svg, "RACE", width / 2, 390, 235, NAVY, anchor="center", max_width=width - 100)
        stamp.draw_text(svg, "RACE", width / 2, 830, 235, CREAM, anchor="center", max_width=width - 100)
        label(sans, svg, "CLEAN", width / 2, 460, 18, RED, anchor="center", tracking=2.0)
        label(sans, svg, "DISTRESSED", width / 2, 900, 18, GOLD, anchor="center", tracking=2.0)
        checker(svg, 290, 950, 12, 14, GOLD, NAVY)
    return svg


def glyph_grid(regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    svg: list[str] = []
    header(svg, width, height, PAPER)
    grain(svg, width, height, 501, light=True)
    if width > height:
        label(sans, svg, "05  /  GLYPH STUDY", 62, 62, 22, NAVY, tracking=2.0)
        label(sans, svg, "UPPER  /  LOWER  /  NUMERALS", width - 62, 62, 19, RED, anchor="right", tracking=1.7)
        line(svg, 62, 88, width - 62, 88, RED, 2)
        regular.draw_text(svg, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", width / 2, 255, 92, NAVY, anchor="center", max_width=width - 130, tracking=1.0)
        regular.draw_text(svg, "abcdefghijklmnopqrstuvwxyz", width / 2, 405, 88, NAVY, anchor="center", max_width=width - 130, tracking=0.8)
        rect(svg, 62, 500, width - 124, 350, NAVY)
        grain(svg, width - 124, 350, 502, light=False)
        stamp.draw_text(svg, "0123456789", width / 2, 685, 152, CREAM, anchor="center", max_width=width - 190, tracking=1.0)
        stamp.draw_text(svg, "Aa  Gg  Rr  Ww", width / 2, 805, 75, GOLD, anchor="center", max_width=width - 190, tracking=1.4)
        label(sans, svg, "OPENTYPE DISPLAY / REGULAR + STAMP", width / 2, 940, 20, RED, anchor="center", tracking=2.2)
    else:
        label(sans, svg, "05 / GLYPH STUDY", 48, 58, 18, NAVY, tracking=1.4)
        label(sans, svg, "UPPER / LOWER / NUMERALS", width - 48, 58, 16, RED, anchor="right", tracking=1.1)
        line(svg, 48, 82, width - 48, 82, RED, 2)
        regular.draw_text(svg, "Aa", width / 2, 310, 250, NAVY, anchor="center", max_width=width - 100)
        label(sans, svg, "REGULAR", width / 2, 370, 20, RED, anchor="center", tracking=2.2)
        rect(svg, 55, 465, width - 110, 390, NAVY)
        grain(svg, width - 110, 390, 502, light=False)
        regular.draw_text(svg, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", width / 2, 555, 54, CREAM, anchor="center", max_width=width - 120, tracking=0.2)
        regular.draw_text(svg, "abcdefghijklmnopqrstuvwxyz", width / 2, 650, 51, CREAM, anchor="center", max_width=width - 120, tracking=0.1)
        stamp.draw_text(svg, "0123456789", width / 2, 785, 102, CREAM, anchor="center", max_width=width - 150)
        label(sans, svg, "STAMP / OPENTYPE DISPLAY", width / 2, 930, 18, RED, anchor="center", tracking=1.5)
    return svg


def render_design(index: int, regular: OutlineFont, stamp: OutlineFont, sans: OutlineFont, width: int, height: int, font_name: str) -> list[str]:
    designs = (cover, race_repeat, road_form, style_split, glyph_grid)
    return designs[index](regular, stamp, sans, width, height, font_name)


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regular", type=Path, required=True, help="Regular/display OTF or TTF")
    parser.add_argument("--stamp", type=Path, required=True, help="Distressed/stamp OTF or TTF")
    parser.add_argument("--sans", type=Path, required=True, help="Fixed auxiliary sans font")
    parser.add_argument("--font-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1000)
    args = parser.parse_args()

    for path in (args.regular, args.stamp, args.sans):
        if not path.is_file():
            raise SystemExit(f"Missing font file: {path}")
    if shutil.which("rsvg-convert") is None:
        raise SystemExit("rsvg-convert is required but was not found on PATH")

    regular = OutlineFont(args.regular)
    stamp = OutlineFont(args.stamp)
    sans = OutlineFont(args.sans)
    landscape_dir = args.output / "3x2"
    square_dir = args.output / "1x1"
    svg_landscape_dir = args.output / "svg" / "3x2"
    svg_square_dir = args.output / "svg" / "1x1"
    for directory in (landscape_dir, square_dir, svg_landscape_dir, svg_square_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for index in range(5):
        design_name = "thumbnail_main" if index == 0 else f"promo_{index}"
        for ratio, width, height, png_dir, svg_dir in (
            ("3x2", args.width, args.height, landscape_dir, svg_landscape_dir),
            ("1x1", args.height, args.height, square_dir, svg_square_dir),
        ):
            svg_text = render_design(index, regular, stamp, sans, width, height, args.font_name)
            svg_path = svg_dir / f"{design_name}.svg"
            png_path = png_dir / f"{design_name}.png"
            svg_path.write_text(f"<!-- {esc(args.font_name)} / {ratio} / deterministic prototype -->\n{finish(svg_text)}", encoding="utf-8")
            subprocess.run(
                ["rsvg-convert", "--width", str(width), "--height", str(height), "--output", str(png_path), str(svg_path)],
                check=True,
            )
            print(f"created {png_path} ({width}x{height})")


if __name__ == "__main__":
    run()
