#!/usr/bin/env python3
"""Compatibility renderer for older plan-driven font visual handoffs.

Agent 27's default path is now ``rasterize_font_visual_handoff.py`` with
custom, already-authored artwork. This older renderer remains available for
existing plans that explicitly use its compatibility templates; it should not
choose the creative direction for new fonts.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from deterministic_font_visuals import (
    CREAM,
    GOLD,
    INK,
    MUTED,
    NAVY,
    PAPER,
    RED,
    WHITE,
    OutlineFont,
    finish,
    grain,
    header,
    label,
    line,
    rect,
)


RATIOS = (("3x2", 2400, 1600), ("1x1", 1600, 1600))
DEFAULT_PALETTE = {
    "background": CREAM,
    "ink": NAVY,
    "panel": INK,
    "accent": RED,
    "highlight": GOLD,
    "paper": PAPER,
    "light": WHITE,
    "muted": MUTED,
}


def resolve_path(value: str, plan_path: Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    from_cwd = Path.cwd() / candidate
    if from_cwd.exists():
        return from_cwd.resolve()
    return (plan_path.parent / candidate).resolve()


def resolve_font_ref(value: Any, plan_path: Path, field: str) -> tuple[Path, int]:
    if isinstance(value, str):
        return resolve_path(value, plan_path), 0
    if isinstance(value, dict) and isinstance(value.get("path"), str):
        index = value.get("index", 0)
        if not isinstance(index, int) or index < 0:
            raise SystemExit(f"{field}.index must be a non-negative integer")
        return resolve_path(value["path"], plan_path), index
    raise SystemExit(f"{field} must be a font path or an object with path and index")


def color(plan: dict[str, Any], key: str) -> str:
    palette = {**DEFAULT_PALETTE, **plan.get("palette", {})}
    value = palette.get(key)
    if not isinstance(value, str) or not value.startswith("#"):
        raise SystemExit(f"palette.{key} must be a hex color")
    return value


def text_value(data: dict[str, Any], key: str, fallback: str) -> str:
    value = data.get(key, fallback)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"visual copy field '{key}' must be a non-empty string")
    return value


def palette_is_light(value: str) -> bool:
    value = value.lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    return (0.2126 * red + 0.7152 * green + 0.0722 * blue) > 145


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG relative contrast for two six-digit hex colors."""
    def luminance(value: str) -> float:
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    light = max(luminance(foreground), luminance(background))
    dark = min(luminance(foreground), luminance(background))
    return (light + 0.05) / (dark + 0.05)


def begin(plan: dict[str, Any], width: int, height: int, seed: int) -> list[str]:
    background = color(plan, "background")
    svg: list[str] = []
    header(svg, width, height, background)
    texture = plan.get("texture", {})
    texture_enabled = True if not isinstance(texture, dict) else texture.get("enabled", True)
    if texture_enabled:
        grain(svg, width, height, seed, light=palette_is_light(background))
    return svg


def draw_label(
    sans: OutlineFont,
    svg: list[str],
    value: str,
    x: float,
    y: float,
    size: float,
    fill: str,
    *,
    anchor: str = "left",
    tracking: float = 1.2,
    max_width: float | None = None,
) -> None:
    label(sans, svg, value, x, y, size, fill, anchor=anchor, tracking=tracking, max_width=max_width)


def draw_product(
    svg: list[str],
    fonts: dict[str, OutlineFont],
    value: str,
    x: float,
    baseline: float,
    size: float,
    fill: str,
    *,
    role: str = "primary",
    anchor: str = "left",
    tracking: float = 0,
    max_width: float | None = None,
    stroke: str | None = None,
    stroke_width: float = 0,
    opacity: float = 1,
) -> None:
    fonts[role].draw_text(
        svg,
        value,
        x,
        baseline,
        size,
        fill,
        anchor=anchor,
        tracking=tracking,
        max_width=max_width,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )


def draw_product_name(
    svg: list[str],
    fonts: dict[str, OutlineFont],
    value: str,
    x: float,
    baseline: float,
    size: float,
    fill: str,
    *,
    role: str = "primary",
    anchor: str = "left",
    tracking: float = 0,
    max_width: float | None = None,
    stroke: str | None = None,
    stroke_width: float = 0,
    line_gap: float | None = None,
) -> None:
    """Draw a product name, stacking exactly two words for storefront impact."""
    words = value.split()
    if len(words) != 2:
        draw_product(
            svg,
            fonts,
            value,
            x,
            baseline,
            size,
            fill,
            role=role,
            anchor=anchor,
            tracking=tracking,
            max_width=max_width,
            stroke=stroke,
            stroke_width=stroke_width,
        )
        return

    line_size = size * 0.72
    step = line_gap if line_gap is not None else line_size * 0.88
    for word, line_baseline in zip(words, (baseline - step / 2, baseline + step / 2)):
        draw_product(
            svg,
            fonts,
            word,
            x,
            line_baseline,
            line_size,
            fill,
            role=role,
            anchor=anchor,
            tracking=tracking,
            max_width=max_width,
            stroke=stroke,
            stroke_width=stroke_width,
        )


def content_for_ratio(content: dict[str, Any], ratio: str | None) -> dict[str, Any]:
    """Apply a reviewed ratio-specific layout without inventing copy."""
    if ratio is None:
        return content
    merged = dict(content)
    ratio_layouts = content.get("ratio_layouts")
    if isinstance(ratio_layouts, dict) and isinstance(ratio_layouts.get(ratio), dict):
        merged.update(ratio_layouts[ratio])
    return merged


def common_top(
    plan: dict[str, Any],
    svg: list[str],
    sans: OutlineFont,
    width: int,
    height: int,
    content: dict[str, Any],
    index: int,
) -> None:
    draw_label(
        sans,
        svg,
        text_value(content, "kicker", "PAPERMOON / FONT STUDY"),
        width * 0.06,
        height * 0.07,
        max(18, height * 0.018),
        color(plan, "ink"),
        tracking=2.0,
        max_width=width * 0.65,
    )
    draw_label(
        sans,
        svg,
        f"{index:02d}",
        width * 0.94,
        height * 0.07,
        max(18, height * 0.018),
        color(plan, "accent"),
        anchor="right",
        tracking=2.0,
    )
    line(svg, width * 0.06, height * 0.095, width * 0.94, height * 0.095, color(plan, "accent"), 2, 0.8)


def render_hero(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    svg = begin(plan, width, height, int(plan["seed"]) + index * 17)
    common_top(plan, svg, fonts["auxiliary"], width, height, content, index)
    ink, accent, panel = (color(plan, key) for key in ("ink", "accent", "panel"))
    rect(svg, width * 0.06, height * 0.17, width * 0.18, height * 0.015, accent)
    display = text_value(content, "display", plan["font_name"])
    stacked = len(display.split()) == 2
    variant = text_value(content, "layout_variant", "left").strip().lower()
    if variant == "center":
        draw_product_name(
            svg, fonts, display, width / 2, height * (0.49 if stacked else 0.54),
            height * (0.20 if stacked else 0.24), ink, anchor="center",
            max_width=width * 0.78, stroke=color(plan, "background"), stroke_width=2,
        )
        draw_label(
            fonts["auxiliary"], svg, text_value(content, "descriptor", "DISPLAY TYPE"),
            width / 2, height * (0.70 if stacked else 0.66), max(20, height * 0.025),
            accent, anchor="center", tracking=2.6, max_width=width * 0.70,
        )
        rect(svg, width * 0.16, height * 0.78, width * 0.68, height * 0.11, panel, 0.96)
        footer_x, footer_y, footer_anchor, footer_width = width / 2, height * 0.852, "center", width * 0.60
    elif variant == "band":
        rect(svg, width * 0.06, height * 0.28, width * 0.88, height * 0.34, panel, 0.96)
        draw_product_name(
            svg, fonts, display, width * 0.10, height * (0.49 if stacked else 0.52),
            height * (0.20 if stacked else 0.24), color(plan, "light"),
            max_width=width * 0.80, stroke=panel, stroke_width=2,
        )
        draw_label(
            fonts["auxiliary"], svg, text_value(content, "descriptor", "DISPLAY TYPE"),
            width * 0.10, height * (0.72 if stacked else 0.69), max(20, height * 0.025),
            accent, tracking=2.6, max_width=width * 0.70,
        )
        footer_x, footer_y, footer_anchor, footer_width = width * 0.10, height * 0.84, "left", width * 0.70
    else:
        draw_product_name(
            svg, fonts, display, width * 0.06, height * (0.49 if stacked else 0.55),
            height * (0.23 if stacked else 0.27), ink, max_width=width * 0.86,
            stroke=color(plan, "background"), stroke_width=2,
        )
        draw_label(
            fonts["auxiliary"], svg, text_value(content, "descriptor", "DISPLAY TYPE"),
            width * 0.07, height * (0.72 if stacked else 0.66), max(20, height * 0.025),
            accent, tracking=3.0, max_width=width * 0.52,
        )
        rect(svg, width * 0.58, height * (0.80 if stacked else 0.77), width * 0.36, height * 0.13, panel, 0.96)
        footer_x, footer_y, footer_anchor, footer_width = width * 0.76, height * (0.875 if stacked else 0.845), "center", width * 0.30
    draw_label(
        fonts["auxiliary"], svg, text_value(content, "footer", "TYPE / FORM / RHYTHM"),
        footer_x, footer_y, max(18, height * 0.018), color(plan, "light"),
        anchor=footer_anchor, tracking=2.2, max_width=footer_width,
    )
    return svg


def render_japanese_thumbnail(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    """Render a square storefront variant with Japanese supporting copy."""
    svg = begin(plan, width, height, int(plan["seed"]) + 901)
    ink, accent, panel, highlight, light = (
        color(plan, key) for key in ("ink", "accent", "panel", "highlight", "light")
    )
    rect(svg, width * 0.08, height * 0.12, width * 0.84, height * 0.76, panel, 0.98)
    rect(svg, width * 0.08, height * 0.12, width * 0.84, height * 0.11, accent, 0.98)
    draw_product(
        svg,
        fonts,
        text_value(content, "kicker", "日本向けフォント"),
        width * 0.14,
        height * 0.195,
        height * 0.038,
        light,
        role="japanese",
        max_width=width * 0.72,
    )
    display = text_value(content, "display", plan["font_name"])
    stacked = len(display.split()) == 2
    draw_product_name(
        svg,
        fonts,
        display,
        width / 2,
        height * (0.48 if stacked else 0.52),
        height * (0.22 if stacked else 0.25),
        color(plan, "paper"),
        anchor="center",
        max_width=width * 0.76,
        stroke=panel,
        stroke_width=2,
    )
    line_y = height * (0.65 if stacked else 0.60)
    line(svg, width * 0.14, line_y, width * 0.86, line_y, highlight, 3)
    draw_product(
        svg,
        fonts,
        text_value(content, "descriptor", "商用利用におすすめの書体"),
        width / 2,
        height * (0.74 if stacked else 0.70),
        height * 0.045,
        light,
        role="japanese",
        anchor="center",
        max_width=width * 0.72,
    )
    draw_product(
        svg,
        fonts,
        text_value(content, "footer", "ロゴ・タイトル・ポスターに"),
        width / 2,
        height * (0.83 if stacked else 0.80),
        height * 0.035,
        color(plan, "highlight"),
        role="japanese",
        anchor="center",
        max_width=width * 0.72,
    )
    draw_product(
        svg,
        fonts,
        text_value(content, "brandline", "日本語向け・書体見本"),
        width / 2,
        height * 0.91,
        height * 0.028,
        accent,
        role="japanese",
        anchor="center",
        max_width=width * 0.72,
    )
    return svg


def render_poster(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    svg = begin(plan, width, height, int(plan["seed"]) + index * 17)
    common_top(plan, svg, fonts["auxiliary"], width, height, content, index)
    ink, accent, panel, light = (color(plan, key) for key in ("ink", "accent", "panel", "light"))
    variant = text_value(content, "layout_variant", "wide").strip().lower()
    headline = text_value(content, "headline", text_value(content, "display", plan["font_name"]))
    subheadline = text_value(content, "subheadline", plan["font_name"])
    if variant == "tall":
        rect(svg, width * 0.08, height * 0.18, width * 0.84, height * 0.54, color(plan, "paper"), 0.98)
        rect(svg, width * 0.08, height * 0.18, width * 0.84, height * 0.12, panel, 0.98)
        draw_label(fonts["auxiliary"], svg, text_value(content, "side_label", "POSTER / TITLE"), width * 0.50, height * 0.255, max(18, height * 0.018), light, anchor="center", tracking=2.0, max_width=width * 0.68)
        draw_product(svg, fonts, headline, width / 2, height * 0.50, height * 0.19, ink, anchor="center", max_width=width * 0.72)
        draw_product(svg, fonts, subheadline, width / 2, height * 0.66, height * 0.12, panel, role="secondary", anchor="center", max_width=width * 0.68)
        line(svg, width * 0.18, height * 0.75, width * 0.82, height * 0.75, accent, 3)
        footer_x, footer_y, footer_anchor = width / 2, height * 0.83, "center"
    else:
        rect(svg, width * 0.06, height * 0.18, width * 0.88, height * 0.56, color(plan, "paper"), 0.98)
        rect(svg, width * 0.06, height * 0.18, width * 0.12, height * 0.56, accent, 0.95)
        draw_label(fonts["auxiliary"], svg, text_value(content, "side_label", "FORM / FORCE"), width * 0.12, height * 0.49, max(18, height * 0.018), light, anchor="center", tracking=2.0, max_width=height * 0.42)
        draw_product(svg, fonts, headline, width * 0.25, height * 0.46, height * 0.22, ink, max_width=width * 0.64)
        draw_product(svg, fonts, subheadline, width * 0.25, height * 0.68, height * 0.14, panel, role="secondary", max_width=width * 0.62)
        line(svg, width * 0.25, height * 0.77, width * 0.86, height * 0.77, accent, 3)
        footer_x, footer_y, footer_anchor = width * 0.25, height * 0.85, "left"
    draw_label(fonts["auxiliary"], svg, text_value(content, "footer", "A LETTERING SYSTEM"), footer_x, footer_y, max(18, height * 0.018), accent, anchor=footer_anchor, tracking=2.0)
    return svg


def render_use_case(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    svg = begin(plan, width, height, int(plan["seed"]) + index * 17)
    ink, accent, panel, paper = (color(plan, key) for key in ("ink", "accent", "panel", "paper"))
    context = text_value(content, "context_type", "poster").strip().lower()
    variant = text_value(content, "layout_variant", "wide").strip().lower()
    outer_x, outer_y, outer_w, outer_h = (0.07, 0.14, 0.86, 0.72) if variant == "wide" else (0.10, 0.12, 0.80, 0.76)
    rect(svg, width * outer_x, height * outer_y, width * outer_w, height * outer_h, paper, 0.98)
    if context in {"label", "package", "packaging"}:
        # A flat label/package face gives the buyer a concrete end-use surface
        # without fabricating a product photograph or unreadable 3-D object.
        rect(svg, width * outer_x, height * outer_y, width * outer_w, height * 0.12, panel, 0.98)
        card_x, card_y, card_w, card_h = (0.14, 0.29, 0.72, 0.45) if variant == "wide" else (0.16, 0.30, 0.68, 0.40)
        rect(svg, width * card_x, height * card_y, width * card_w, height * card_h, color(plan, "background"), 0.98)
        line(svg, width * card_x, height * card_y, width * (card_x + card_w), height * card_y, accent, 3)
        line(svg, width * (card_x + card_w * 0.70), height * (card_y + card_h * 0.70), width * (card_x + card_w * 0.88), height * (card_y + card_h * 0.70), panel, 2, 0.75)
        line(svg, width * (card_x + card_w * 0.70), height * (card_y + card_h * 0.76), width * (card_x + card_w * 0.84), height * (card_y + card_h * 0.76), panel, 2, 0.75)
    elif context in {"brand lockup", "sign", "badge"}:
        rect(svg, width * 0.12, height * (0.28 if variant == "wide" else 0.30), width * 0.76, height * (0.38 if variant == "wide" else 0.34), panel, 0.98)
        line(svg, width * 0.16, height * (0.32 if variant == "wide" else 0.34), width * 0.84, height * (0.32 if variant == "wide" else 0.34), accent, 3)
        line(svg, width * 0.16, height * (0.62 if variant == "wide" else 0.60), width * 0.84, height * (0.62 if variant == "wide" else 0.60), accent, 3)
    else:
        # Poster/title-card default: a strong header bar and open paper field.
        rect(svg, width * outer_x, height * outer_y, width * outer_w, height * 0.12, panel, 0.98)
    draw_label(fonts["auxiliary"], svg, text_value(content, "kicker", "USE CASE / 01"), width * 0.10, height * 0.215, max(18, height * 0.018), color(plan, "light"), tracking=2.0)
    draw_label(fonts["auxiliary"], svg, text_value(content, "category", context.upper()), width * 0.90, height * 0.215, max(16, height * 0.016), accent, anchor="right", tracking=1.4, max_width=width * 0.45)
    headline = text_value(content, "headline", text_value(content, "display", plan["font_name"]))
    draw_product(svg, fonts, headline, width * 0.12, height * 0.53, height * 0.24, ink, max_width=width * 0.76)
    line(svg, width * 0.12, height * 0.59, width * 0.88, height * 0.59, accent, 3)
    draw_label(fonts["auxiliary"], svg, text_value(content, "body", "A SHORT MESSAGE WITH ROOM TO BREATHE"), width * 0.12, height * 0.72, max(18, height * 0.02), panel, tracking=1.0, max_width=width * 0.64)
    draw_label(fonts["auxiliary"], svg, text_value(content, "footer", "REAL TYPE / CLEAR HIERARCHY"), width * 0.12, height * 0.81, max(16, height * 0.016), accent, tracking=1.8)
    return svg


def render_feature_grid(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    svg = begin(plan, width, height, int(plan["seed"]) + index * 17)
    common_top(plan, svg, fonts["auxiliary"], width, height, content, index)
    ink, accent, panel, light = (color(plan, key) for key in ("ink", "accent", "panel", "light"))
    variant = text_value(content, "layout_variant", "rows").strip().lower()
    display = text_value(content, "display", "Aa")
    if variant == "column":
        rect(svg, width * 0.12, height * 0.18, width * 0.76, height * 0.62, panel)
        line(svg, width * 0.16, height * 0.39, width * 0.84, height * 0.39, light, 1, 0.25)
        line(svg, width * 0.16, height * 0.60, width * 0.84, height * 0.60, light, 1, 0.25)
        draw_product(svg, fonts, display, width / 2, height * 0.34, height * 0.16, light, anchor="center", max_width=width * 0.60)
        draw_product(svg, fonts, text_value(content, "line_2", plan["font_name"]), width / 2, height * 0.55, height * 0.11, color(plan, "highlight"), anchor="center", max_width=width * 0.64)
        draw_product(svg, fonts, text_value(content, "line_3", "0123456789"), width / 2, height * 0.74, height * 0.07, accent, anchor="center", max_width=width * 0.66, tracking=1.6)
    else:
        rect(svg, width * 0.06, height * 0.17, width * 0.88, height * 0.60, panel)
        for fraction in (0.29, 0.52, 0.75):
            line(svg, width * 0.06, height * fraction, width * 0.94, height * fraction, light, 1, 0.25)
        draw_product(svg, fonts, display, width * 0.18, height * 0.39, height * 0.18, light, max_width=width * 0.62)
        draw_product(svg, fonts, text_value(content, "line_2", plan["font_name"]), width * 0.18, height * 0.60, height * 0.12, color(plan, "highlight"), max_width=width * 0.68)
        draw_product(svg, fonts, text_value(content, "line_3", "0123456789"), width * 0.18, height * 0.73, height * 0.08, accent, max_width=width * 0.68, tracking=2.0)
    draw_label(fonts["auxiliary"], svg, text_value(content, "footer", "DETAIL / SCALE / SPACING"), width * 0.06, height * 0.86, max(16, height * 0.016), ink, tracking=2.0)
    return svg


def render_contrast(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
) -> list[str]:
    svg = begin(plan, width, height, int(plan["seed"]) + index * 17)
    ink, accent, panel, light = (color(plan, key) for key in ("ink", "accent", "panel", "light"))
    variant = text_value(content, "layout_variant", "stacked").strip().lower()
    if variant == "split":
        rect(svg, width * 0.50, 0, width * 0.50, height, panel)
    else:
        rect(svg, 0, height * 0.50, width, height * 0.50, panel)
    draw_label(fonts["auxiliary"], svg, text_value(content, "kicker", "ONE FONT / TWO READS"), width * 0.06, height * 0.08, max(18, height * 0.018), ink, tracking=2.0)
    word = text_value(content, "display", text_value(content, "headline", plan["font_name"]))
    if variant == "split":
        draw_label(fonts["auxiliary"], svg, text_value(content, "top_label", "CLEAN"), width * 0.08, height * 0.24, max(18, height * 0.018), accent, tracking=2.2)
        draw_product(svg, fonts, word, width * 0.08, height * 0.43, height * 0.15, ink, max_width=width * 0.38)
        draw_label(fonts["auxiliary"], svg, text_value(content, "bottom_label", "TEXTURE"), width * 0.58, height * 0.24, max(18, height * 0.018), color(plan, "highlight"), tracking=2.2)
        draw_product(svg, fonts, word, width * 0.58, height * 0.43, height * 0.15, light, role="secondary", max_width=width * 0.34, stroke=panel, stroke_width=2)
    else:
        draw_label(fonts["auxiliary"], svg, text_value(content, "top_label", "CLEAN"), width * 0.06, height * 0.22, max(18, height * 0.018), accent, tracking=2.4)
        draw_product(svg, fonts, word, width * 0.06, height * 0.41, height * 0.20, ink, max_width=width * 0.87)
        draw_label(fonts["auxiliary"], svg, text_value(content, "bottom_label", "TEXTURE"), width * 0.06, height * 0.64, max(18, height * 0.018), color(plan, "highlight"), tracking=2.4)
        draw_product(svg, fonts, word, width * 0.06, height * 0.84, height * 0.20, light, role="secondary", max_width=width * 0.87, stroke=panel, stroke_width=2)
    return svg


TEMPLATES = {
    "hero": render_hero,
    "japanese": render_japanese_thumbnail,
    "poster": render_poster,
    "use-case": render_use_case,
    "feature-grid": render_feature_grid,
    "contrast": render_contrast,
}


def render_one(
    plan: dict[str, Any],
    content: dict[str, Any],
    fonts: dict[str, OutlineFont],
    width: int,
    height: int,
    index: int,
    *,
    ratio: str | None = None,
) -> str:
    content = content_for_ratio(content, ratio)
    template = content.get("template", "hero")
    if template not in TEMPLATES:
        raise SystemExit(f"unsupported visual template: {template}")
    return finish(TEMPLATES[template](plan, content, fonts, width, height, index))


def validate_plan(plan: dict[str, Any], plan_path: Path) -> tuple[Any, Any, Any, Any]:
    for required in ("font_name", "primary_font", "auxiliary_font", "japanese_font", "seed", "dimensions", "thumbnail", "japanese_thumbnail", "promos"):
        if required not in plan:
            raise SystemExit(f"visual plan is missing '{required}'")
    if not isinstance(plan["font_name"], str) or not plan["font_name"].strip():
        raise SystemExit("font_name must be a non-empty string")
    if not isinstance(plan["seed"], int):
        raise SystemExit("seed must be an integer")
    if not isinstance(plan["promos"], list) or not 4 <= len(plan["promos"]) <= 8:
        raise SystemExit("visual plan must contain 4-8 supporting-image promos")
    dimensions = plan.get("dimensions", {ratio: [width, height] for ratio, width, height in RATIOS})
    expected_dimensions = {ratio: [width, height] for ratio, width, height in RATIOS}
    if dimensions != expected_dimensions:
        raise SystemExit(f"visual plan dimensions must be {expected_dimensions}")
    contrast_checks = plan.get("contrast_checks")
    if not isinstance(contrast_checks, list) or len(contrast_checks) < 2:
        raise SystemExit("visual plan must contain at least two contrast_checks")
    for index, check in enumerate(contrast_checks, start=1):
        if not isinstance(check, dict):
            raise SystemExit(f"contrast_checks[{index}] must be an object")
        foreground = check.get("foreground")
        background = check.get("background")
        minimum = check.get("minimum", 3.0)
        if not isinstance(foreground, str) or not isinstance(background, str) or not isinstance(minimum, (int, float)):
            raise SystemExit(f"contrast_checks[{index}] requires foreground, background, and numeric minimum")
        ratio = contrast_ratio(color(plan, foreground), color(plan, background))
        if ratio < float(minimum):
            raise SystemExit(
                f"contrast check failed for {foreground}/{background}: {ratio:.2f}:1 < {float(minimum):.2f}:1"
            )
    primary, primary_index = resolve_font_ref(plan["primary_font"], plan_path, "primary_font")
    auxiliary, auxiliary_index = resolve_font_ref(plan["auxiliary_font"], plan_path, "auxiliary_font")
    secondary_value = plan.get("secondary_font")
    secondary_ref = resolve_font_ref(secondary_value, plan_path, "secondary_font") if secondary_value else None
    japanese, japanese_index = resolve_font_ref(plan["japanese_font"], plan_path, "japanese_font")
    for path in (primary, auxiliary, japanese, secondary_ref[0] if secondary_ref else None):
        if path is not None and not path.is_file():
            raise SystemExit(f"font file not found: {path}")
    if not shutil.which("rsvg-convert"):
        raise SystemExit("rsvg-convert is required but was not found on PATH")
    return (primary, primary_index), (auxiliary, auxiliary_index), secondary_ref, (japanese, japanese_index)


def render_creative(plan: dict[str, Any], plan_path: Path, output: Path) -> None:
    primary_ref, auxiliary_ref, secondary_ref, japanese_ref = validate_plan(plan, plan_path)
    primary_path, primary_index = primary_ref
    auxiliary_path, auxiliary_index = auxiliary_ref
    japanese_path, japanese_index = japanese_ref
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty visual handoff: {output}")
    output.mkdir(parents=True, exist_ok=True)
    fonts = {
        "primary": OutlineFont(primary_path, primary_index),
        "auxiliary": OutlineFont(auxiliary_path, auxiliary_index),
        "japanese": OutlineFont(japanese_path, japanese_index),
    }
    fonts["secondary"] = OutlineFont(*secondary_ref) if secondary_ref else fonts["primary"]
    thumbnail = dict(plan["thumbnail"])
    selected_candidate = plan.get("selected_thumbnail_candidate")
    if selected_candidate is not None:
        candidates = plan.get("thumbnail_candidates", [])
        match = next(
            (
                candidate
                for candidate in candidates
                if isinstance(candidate, dict) and candidate.get("id") == selected_candidate
            ),
            None,
        )
        if match is None:
            raise SystemExit(f"selected_thumbnail_candidate not found: {selected_candidate}")
        thumbnail.update(match)
    svg_root = output / "svg"
    for ratio, width, height in RATIOS:
        (output / ratio).mkdir(parents=True, exist_ok=True)
        (svg_root / ratio).mkdir(parents=True, exist_ok=True)
        thumbnail_name = "thumbnail_main"
        thumbnail_svg = render_one(plan, thumbnail, fonts, width, height, 1, ratio=ratio)
        (svg_root / ratio / f"{thumbnail_name}.svg").write_text(thumbnail_svg, encoding="utf-8")
        render_svg(svg_root / ratio / f"{thumbnail_name}.svg", output / ratio / f"{thumbnail_name}.png", width, height)
        for number, content in enumerate(plan["promos"], start=1):
            promo_svg = render_one(plan, content, fonts, width, height, number + 1, ratio=ratio)
            svg_path = svg_root / ratio / f"promo_{number}.svg"
            png_path = output / ratio / f"promo_{number}.png"
            svg_path.write_text(promo_svg, encoding="utf-8")
            render_svg(svg_path, png_path, width, height)

        if ratio == "1x1":
            japanese_svg = render_one(plan, plan["japanese_thumbnail"], fonts, width, height, 0, ratio=ratio)
            japanese_svg_path = svg_root / ratio / "thumbnail_japanese.svg"
            japanese_png_path = output / ratio / "thumbnail_japanese.png"
            japanese_svg_path.write_text(japanese_svg, encoding="utf-8")
            render_svg(japanese_svg_path, japanese_png_path, width, height)

    specimen_temp = output / ".specimen-render"
    if specimen_temp.exists():
        shutil.rmtree(specimen_temp)
    specimen_script = Path(__file__).with_name("render_font_specimens.py")
    subprocess.run(
        [sys.executable, str(specimen_script), str(primary_path), str(specimen_temp), "--name", str(plan["font_name"])],
        check=True,
    )
    for ratio, source_dir, size in (
        ("3x2", specimen_temp / "main", "3x2"),
        ("1x1", specimen_temp / "squares", "1x1"),
    ):
        destination = output / "specimens" / ratio
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("specimen-alphabet-numerals.png", "specimen-multilingual-glyphs.png"):
            source = source_dir / name
            if not source.is_file():
                raise SystemExit(f"specimen renderer did not create {source}")
            shutil.copy2(source, destination / name)
    shutil.rmtree(specimen_temp)


def render_svg(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    subprocess.run(
        ["rsvg-convert", "--width", str(width), "--height", str(height), "--output", str(png_path), str(svg_path)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"visual plan not found: {args.plan}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid visual plan JSON: {error}")
    if not isinstance(plan, dict):
        raise SystemExit("visual plan root must be a JSON object")
    if plan.get("render_mode") in {"direct_artwork", "direct"}:
        raise SystemExit(
            "direct artwork plans must use bin/rasterize_font_visual_handoff.py; "
            "the plan-driven compatibility renderer is not a creative fallback"
        )
    render_creative(plan, args.plan.resolve(), args.output)
    print(f"created visual handoff assets in {args.output}")
    print(f"created {len(plan['promos'])} promos in each ratio")
    print("created four factual specimen PNGs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
