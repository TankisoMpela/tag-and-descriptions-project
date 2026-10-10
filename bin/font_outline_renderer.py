#!/usr/bin/env python3
"""Shape font text and render it as deterministic SVG glyph paths."""

from __future__ import annotations

import html
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


@dataclass(frozen=True)
class ShapedGlyph:
    glyph_name: str
    x_advance: int
    y_advance: int
    x_offset: int
    y_offset: int


@dataclass(frozen=True)
class LineMetric:
    text: str
    size: float
    advance: float
    bounds: tuple[float, float, float, float]
    glyphs: tuple[ShapedGlyph, ...]

    @property
    def width(self) -> float:
        return max(0.0, self.bounds[2] - self.bounds[0])


class OutlineFontError(ValueError):
    """Raised when the supplied font cannot draw planned copy."""


class OutlineFont:
    """Shape text with HarfBuzz and expose exact outline geometry."""

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

    def shape(self, text: str) -> tuple[ShapedGlyph, ...]:
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self.hb_font, buffer, {"kern": True, "liga": True, "clig": True})
        shaped = tuple(
            ShapedGlyph(
                glyph_name=self.glyph_name(info.codepoint),
                x_advance=position.x_advance,
                y_advance=position.y_advance,
                x_offset=position.x_offset,
                y_offset=position.y_offset,
            )
            for info, position in zip(buffer.glyph_infos, buffer.glyph_positions)
        )
        missing = sorted({glyph.glyph_name for glyph in shaped if glyph.glyph_name in {".notdef", "gid0"} or glyph.glyph_name not in self.glyph_set})
        if missing:
            raise OutlineFontError(f"{self.path.name} has no drawable glyph outline for: {', '.join(missing)}")
        return shaped

    @lru_cache(maxsize=4096)
    def glyph_bounds(self, glyph_name: str) -> tuple[float, float, float, float] | None:
        if glyph_name not in self.glyph_set:
            return None
        pen = BoundsPen(self.glyph_set)
        self.glyph_set[glyph_name].draw(pen)
        return pen.bounds

    @lru_cache(maxsize=4096)
    def glyph_path(self, glyph_name: str) -> str:
        if glyph_name not in self.glyph_set:
            return ""
        pen = SVGPathPen(self.glyph_set)
        self.glyph_set[glyph_name].draw(pen)
        return pen.getCommands()

    def line_metric(self, text: str, size: float, tracking: float = 0) -> LineMetric:
        shaped = self.shape(text)
        scale = size / self.upm
        cursor = 0.0
        x_min = float("inf")
        y_min = float("inf")
        x_max = float("-inf")
        y_max = float("-inf")
        drawable = False
        for index, glyph in enumerate(shaped):
            bounds = self.glyph_bounds(glyph.glyph_name)
            if bounds is not None:
                drawable = True
                left, bottom, right, top = bounds
                x_min = min(x_min, cursor + glyph.x_offset + left)
                y_min = min(y_min, glyph.y_offset + bottom)
                x_max = max(x_max, cursor + glyph.x_offset + right)
                y_max = max(y_max, glyph.y_offset + top)
            cursor += glyph.x_advance
            if index < len(shaped) - 1:
                cursor += tracking / scale if scale else 0
        if not drawable:
            x_min = y_min = x_max = y_max = 0.0
        return LineMetric(
            text=text,
            size=size,
            advance=cursor * scale,
            bounds=(x_min * scale, y_min * scale, x_max * scale, y_max * scale),
            glyphs=shaped,
        )

    def line_height(self, size: float, leading: float = 0.12) -> float:
        hhea = self.ttfont["hhea"]
        return (hhea.ascent - hhea.descent) * (size / self.upm) * (1 + leading)

    def wrap_lines(self, text: str, size: float, max_width: float, tracking: float = 0) -> list[str]:
        lines: list[str] = []
        for paragraph in text.splitlines() or [text]:
            words = paragraph.split(" ")
            current = ""
            for word in words:
                candidate = word if not current else f"{current} {word}"
                if current and self.line_metric(candidate, size, tracking).width > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
                # Keep words intact. The placeholder handoff must never show
                # a word as character fragments; callers must reduce the type
                # size or revise the copy when a word is too wide.
                if current and self.line_metric(current, size, tracking).width > max_width:
                    lines.append(current)
                    current = ""
            if current:
                lines.append(current)
        return lines or [""]

    def draw_line(
        self,
        svg: list[str],
        metric: LineMetric,
        x: float,
        baseline: float,
        fill: str,
        tracking: float = 0,
    ) -> None:
        scale = metric.size / self.upm
        cursor = x
        for index, glyph in enumerate(metric.glyphs):
            path = self.glyph_path(glyph.glyph_name)
            if path:
                tx = cursor + glyph.x_offset * scale
                ty = baseline - glyph.y_offset * scale
                svg.append(
                    f'<path d="{html.escape(path, quote=True)}" '
                    f'transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f} {-scale:.6f})" '
                    f'fill="{html.escape(fill, quote=True)}"/>'
                )
            cursor += glyph.x_advance * scale
            if index < len(metric.glyphs) - 1:
                cursor += tracking
