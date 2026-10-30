#!/usr/bin/env python3
"""Build thumbnail placeholders, support images, and factual specimens."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from font_outline_renderer import LineMetric, OutlineFont


RATIOS = {"3x2": (2400, 1600), "1x1": (1600, 1600)}
BACKGROUND = (255, 255, 255)
INK = (20, 20, 24)
FALLBACK_FONTS = (
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
)


def resolve_path(value: object, base: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def require_font(value: object, base: Path, label: str) -> Path:
    path = resolve_path(value, base)
    if path is None or not path.is_file():
        raise SystemExit(f"{label} font is missing or unreadable: {path or value}")
    return path


def fallback_font() -> Path:
    for candidate in FALLBACK_FONTS:
        path = Path(candidate)
        if path.is_file():
            return path
    raise SystemExit("No system fallback font is available for placeholder copy")


def blocks_for(owner: object, label: str) -> list[str]:
    if not isinstance(owner, dict):
        raise SystemExit(f"{label} must be an object in the visual plan")
    blocks = owner.get("copy_blocks")
    if not isinstance(blocks, list):
        raise SystemExit(f"{label}.copy_blocks must be a list")
    cleaned = [block.strip() for block in blocks if isinstance(block, str) and block.strip()]
    is_thumbnail = "thumbnail" in label
    if is_thumbnail:
        if len(cleaned) != 1:
            raise SystemExit(f"{label}.copy_blocks must contain exactly 1 text block (the font name stacked)")
    else:
        if len(cleaned) < 1:
            raise SystemExit(f"{label}.copy_blocks must contain at least 1 text block (the main phrase)")
    return cleaned


def default_placements(count: int) -> list[dict[str, str | int]]:
    """Provide a neutral fallback when the authored plan omits placements.

    Placement is a mechanical safety net, not a semantic copy template. The
    agent's plan remains responsible for choosing a font-specific composition.
    """
    anchors = [
        ("center", "hero"),
        ("top-right", "small"),
        ("bottom-left", "medium"),
        ("bottom-right", "small"),
        ("top-left", "small"),
        ("center-right", "small"),
        ("bottom-center", "small"),
        ("center-left", "small"),
    ]
    placements: list[dict[str, str | int]] = []
    for index in range(count):
        anchor, scale = anchors[index % len(anchors)]
        if index >= len(anchors):
            scale = "micro"
        placements.append({"block": index, "anchor": anchor, "scale": scale})
    return placements


def placements_for(owner: dict, count: int, ratio: str | None = None) -> list[dict[str, str | int]]:
    layout = owner.get("layout")
    layouts_by_ratio = owner.get("layout_by_ratio")
    if isinstance(layouts_by_ratio, dict) and isinstance(ratio, str):
        ratio_layout = layouts_by_ratio.get(ratio)
        if isinstance(ratio_layout, dict):
            layout = ratio_layout
    placements = layout.get("placements") if isinstance(layout, dict) else None
    if not isinstance(placements, list):
        return default_placements(count)
    valid: list[dict[str, str | int]] = []
    for placement in placements:
        if not isinstance(placement, dict):
            continue
        block = placement.get("block")
        anchor = placement.get("anchor")
        scale = placement.get("scale", "small")
        if (
            isinstance(block, int)
            and 0 <= block < count
            and isinstance(anchor, str)
            and anchor in PLACEMENT_ANCHORS
            and isinstance(scale, str)
            and scale in SCALE_SPECS
        ):
            if any(int(item["block"]) == block for item in valid):
                continue
            valid.append({"block": block, "anchor": anchor, "scale": scale})
    if not valid:
        return default_placements(count)
    used = {int(item["block"]) for item in valid}
    for item in default_placements(count):
        if int(item["block"]) not in used:
            valid.append(item)
    return valid


@dataclass(frozen=True)
class PositionedLine:
    text: str
    metric: LineMetric
    x: float
    baseline: float


@dataclass(frozen=True)
class BlockGeometry:
    font: OutlineFont
    lines: tuple[PositionedLine, ...]
    box: tuple[float, float, float, float]


SIDE_ANCHORS = frozenset(
    {"top-left", "top-right", "center-left", "center-right", "bottom-left", "bottom-right"}
)

# How much of the full measure a solo side-anchored block may use. It stays
# below 1.0 on purpose: side blocks being smaller than centred ones is the
# set's variety. It sits above the half a shared layout reserves so the type is
# not tiny in an empty frame.
SIDE_ANCHOR_SOLO_SHARE = 0.60

SCALE_SPECS = {
    "hero": (0.24, 0.93, 0.84),
    "word": (0.34, 0.88, 0.72),
    "large": (0.18, 0.90, 0.68),
    "medium": (0.11, 0.76, 0.46),
    "small": (0.075, 0.68, 0.28),
    "micro": (0.055, 0.58, 0.22),
}


def visible_line_height(metrics: list[LineMetric], size: float) -> float:
    visible_heights = [metric.bounds[3] - metric.bounds[1] for metric in metrics if metric.width or metric.bounds[3] != metric.bounds[1]]
    return max(visible_heights or [size * 0.5]) * 1.12


def measured_block(font: OutlineFont, text: str, size: float, max_width: float, stack_words: bool) -> tuple[list[str], list[LineMetric], float, tuple[float, float, float, float]]:
    if stack_words and "\n" not in text and len(text.split()) == 2:
        text = "\n".join(text.split())
    lines = font.wrap_lines(text, size, max_width)
    metrics = [font.line_metric(line, size) for line in lines]
    line_height = visible_line_height(metrics, size)
    boxes = [
        (metric.bounds[0], index * line_height - metric.bounds[3], metric.bounds[2], index * line_height - metric.bounds[1])
        for index, metric in enumerate(metrics)
    ]
    box = (
        min((item[0] for item in boxes), default=0),
        min((item[1] for item in boxes), default=0),
        max((item[2] for item in boxes), default=0),
        max((item[3] for item in boxes), default=0),
    )
    return lines, metrics, line_height, box


def fit_outline_block(
    font: OutlineFont,
    text: str,
    max_width: float,
    start: float,
    minimum: float,
    fill_ratio: float,
    max_height: float,
    stack_words: bool,
) -> tuple[float, list[str], list[LineMetric], float, tuple[float, float, float, float]]:
    ceiling = max(start * 4, max_width * 0.95, max_height * 1.5, 256)
    chosen = None

    # Fitting is monotonic for this renderer: if a size fits, every smaller
    # size also fits. Binary search avoids thousands of outline measurements
    # per block while preserving the largest safe readable size.
    low = int(minimum)
    high = int(ceiling)
    while low <= high:
        size = (low + high) // 2
        candidate = measured_block(font, text, size, max_width, stack_words)
        box = candidate[3]
        fits = (
            len(candidate[0]) <= 4
            and box[2] - box[0] <= max_width
            and box[3] - box[1] <= max_height
        )
        if fits:
            chosen = (size, *candidate)
            low = size + 1
        else:
            high = size - 1
    if chosen is None:
        size = max(int(minimum), int(start))
        candidate = measured_block(font, text, size, max_width, stack_words)
        if len(candidate[0]) > 4 or candidate[3][2] - candidate[3][0] > max_width or candidate[3][3] - candidate[3][1] > max_height:
            raise ValueError(
                f"planned copy cannot fit without clipping, word-breaking, or unsafe scale: {text!r}"
            )
        chosen = (size, *candidate)
    return chosen


def block_geometry(
    font: OutlineFont,
    text: str,
    anchor: str,
    scale: str,
    size: tuple[int, int],
    margin: int,
    stack_words: bool = False,
    solo: bool = False,
) -> BlockGeometry:
    width, height = size
    # A side-anchored block reserves space for whatever shares the canvas. On a
    # two-block layout that means half the measure; with a single block there is
    # nothing to reserve for, so it gets a larger share -- but still less than a
    # centred block, because that difference in scale is what gives the set its
    # variety. Reserving the full half here shrank side-anchored type to 41% of
    # the frame and left the promos looking empty; taking the whole frame made
    # every promo the same size and removed the variety entirely.
    if anchor in SIDE_ANCHORS:
        max_width = (width - margin * 3) / 2 if not solo else (width - margin * 2) * SIDE_ANCHOR_SOLO_SHARE
    else:
        max_width = width - margin * 2
    start_ratio, fill_ratio, height_ratio = SCALE_SPECS.get(scale, SCALE_SPECS["small"])
    font_size, _lines, metrics, _line_height, unplaced_box = fit_outline_block(
        font,
        text,
        max_width,
        width * start_ratio,
        22,
        fill_ratio,
        height * height_ratio,
        stack_words,
    )
    line_height = visible_line_height(metrics, font_size)
    boxes = [
        (metric.bounds[0], index * line_height - metric.bounds[3], metric.bounds[2], index * line_height - metric.bounds[1])
        for index, metric in enumerate(metrics)
    ]
    block_box = (
        min(item[0] for item in boxes),
        min(item[1] for item in boxes),
        max(item[2] for item in boxes),
        max(item[3] for item in boxes),
    )
    vertical_key = "center" if "center" in anchor else "bottom" if "bottom" in anchor else "top"
    horizontal_key = "center" if anchor in {"center", "bottom-center"} else "right" if "right" in anchor else "left"
    if vertical_key == "top":
        shift_y = margin - block_box[1]
    elif vertical_key == "bottom":
        shift_y = height - margin - block_box[3]
    else:
        shift_y = height / 2 - (block_box[1] + block_box[3]) / 2
    target_x = margin if horizontal_key == "left" else width - margin if horizontal_key == "right" else width / 2
    positioned: list[PositionedLine] = []
    for index, metric in enumerate(metrics):
        if horizontal_key == "left":
            shift_x = target_x - metric.bounds[0]
        elif horizontal_key == "right":
            shift_x = target_x - metric.bounds[2]
        else:
            shift_x = target_x - (metric.bounds[0] + metric.bounds[2]) / 2
        positioned.append(
            PositionedLine(
                text=metric.text,
                metric=metric,
                x=shift_x,
                baseline=shift_y + index * line_height,
            )
        )
    # Calculate bounds from the individually aligned glyph outlines.
    shifted_box = (
        min(line.x + line.metric.bounds[0] for line in positioned),
        min(line.baseline - line.metric.bounds[3] for line in positioned),
        max(line.x + line.metric.bounds[2] for line in positioned),
        max(line.baseline - line.metric.bounds[1] for line in positioned),
    )
    return BlockGeometry(font=font, lines=tuple(positioned), box=shifted_box)


def paint_block(svg: list[str], geometry: BlockGeometry, fill: str) -> None:
    for line in geometry.lines:
        geometry.font.draw_line(svg, line.metric, line.x, line.baseline, fill)


PLACEMENT_ANCHORS = (
    "top-left",
    "top-right",
    "center-left",
    "center-right",
    "bottom-left",
    "bottom-right",
    "bottom-center",
    "center",
)


def overlap_area(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    return max(0.0, right - left) * max(0.0, bottom - top)


def overflow_amount(box: tuple[float, float, float, float], size: tuple[int, int]) -> float:
    width, height = size
    left = max(0.0, -box[0])
    top = max(0.0, -box[1])
    right = max(0.0, box[2] - width)
    bottom = max(0.0, box[3] - height)
    return left + top + right + bottom


def placement_score(
    box: tuple[float, float, float, float],
    occupied: list[tuple[float, float, float, float]],
    size: tuple[int, int],
    order: int,
) -> tuple[int, float, int]:
    overlap = sum(overlap_area(box, other) for other in occupied)
    overflow = overflow_amount(box, size)
    invalid = int(overlap > 0 or overflow > 0)
    return invalid, overlap + overflow, order


def choose_placement(
    font: OutlineFont,
    text: str,
    requested_anchor: str,
    scale: str,
    size: tuple[int, int],
    margin: int,
    stack_words: bool,
    occupied: list[tuple[float, float, float, float]],
    reserve: list[tuple[OutlineFont, str, str, str]] | None = None,
    center_only: bool = False,
    solo: bool = False,
) -> tuple[BlockGeometry, str]:
    fallback_scales = ("word", "large", "small", "micro") if scale == "hero" else ("small", "micro")
    if center_only:
        fallback_scales = ("word", "large")
    scales = [scale] + [fallback for fallback in fallback_scales if fallback != scale]
    best_geometry = None
    best_anchor = requested_anchor
    best_score: tuple[int, float, int, int] | None = None
    for scale_order, candidate_scale in enumerate(scales):
        if center_only:
            anchors = ["center"]
        else:
            anchors = [requested_anchor] + [anchor for anchor in PLACEMENT_ANCHORS if anchor != requested_anchor]
        for anchor_order, anchor in enumerate(anchors):
            try:
                geometry = block_geometry(font, text, anchor, candidate_scale, size, margin, stack_words, solo)
            except ValueError:
                # A side anchor can make a word too narrow while a centered or
                # opposite anchor may still fit. Try every legal placement
                # before failing the authored layout.
                continue
            score = placement_score(geometry.box, occupied, size, anchor_order)
            ranked = (score[0], score[1], scale_order, anchor_order)
            if best_score is None or ranked < best_score:
                best_geometry = geometry
                best_anchor = anchor
                best_score = ranked
            if score[0] == 0 and _reserve_has_slots(
                reserve or [], occupied + [geometry.box], size, margin, stack_words, solo
            ):
                return geometry, anchor
    if best_geometry is None:
        raise ValueError(
            f"copy {text!r} cannot fit in any safe placement without word "
            "breaking or clipping"
        )
    raise ValueError(
        f"no collision-free placement for copy {text!r}; revise the authored "
        "copy, placement, or scale instead of allowing overlap"
    )


def _reserve_has_slots(
    reserve: list[tuple[OutlineFont, str, str, str]],
    occupied: list[tuple[float, float, float, float]],
    size: tuple[int, int],
    margin: int,
    stack_words: bool,
    solo: bool = False,
) -> bool:
    """Check that reserved secondary blocks have a safe home after this block."""
    for font, text, requested_anchor, requested_scale in reserve:
        placed = False
        scales = [requested_scale] + [fallback for fallback in ("small", "micro") if fallback != requested_scale]
        for candidate_scale in scales:
            for anchor in [requested_anchor] + [item for item in PLACEMENT_ANCHORS if item != requested_anchor]:
                try:
                    geometry = block_geometry(font, text, anchor, candidate_scale, size, margin, stack_words, solo)
                except ValueError:
                    continue
                if placement_score(geometry.box, occupied, size, 0)[0] == 0:
                    occupied.append(geometry.box)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            return False
    return True


def render_placeholder(
    owner: dict,
    size: tuple[int, int],
    ratio: str,
    label: str,
    primary_font: OutlineFont,
    copy_font: OutlineFont,
) -> tuple[str, list[tuple[float, float, float, float]]]:
    width, height = size
    blocks = blocks_for(owner, label)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', f'<rect width="{width}" height="{height}" fill="#ffffff"/>']
    margin = round(width * 0.06)
    is_thumbnail = "thumbnail" in label
    if is_thumbnail:
        # Thumbnails remain centred product-name lockups. Strategic placement
        # belongs to supporting promos, where the concept needs room for art.
        placements = [{"block": 0, "anchor": "center", "scale": "hero"}]
    else:
        placements = placements_for(owner, len(blocks), ratio)
        placements = sorted(placements, key=lambda item: (int(item["block"]) != 0, int(item["block"])))
    occupied: list[tuple[float, float, float, float]] = []
    solo = len(blocks) == 1
    for position, placement in enumerate(placements):
        item = dict(placement)
        block_index = int(item["block"])
        font = primary_font if block_index == 0 or is_thumbnail else copy_font
        requested_scale = str(placement["scale"])
        if block_index == 0 or is_thumbnail:
            requested_scale = "hero"
        reserve = []
        if block_index == 0 and not is_thumbnail:
            for future in placements[position + 1:]:
                future_index = int(future["block"])
                future_font = primary_font if future_index == 0 else copy_font
                reserve.append((future_font, blocks[future_index], str(future["anchor"]), str(future["scale"])))
        geometry, _actual_anchor = choose_placement(
            font,
            blocks[block_index],
            str(placement["anchor"]),
            requested_scale,
            size,
            margin,
            is_thumbnail,
            occupied,
            reserve,
            center_only=is_thumbnail,
            solo=solo,
        )
        paint_block(svg, geometry, "#141418")
        occupied.append(geometry.box)
    svg.append("</svg>")
    return "\n".join(svg), occupied


def write_placeholder_png(svg: str, destination: Path) -> None:
    renderer = shutil.which("rsvg-convert")
    if renderer is None:
        raise SystemExit("rsvg-convert is required for outline-based placeholder rendering")
    source = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", dir=destination.parent, delete=False, encoding="utf-8") as handle:
            handle.write(svg)
            source = Path(handle.name)
        subprocess.run([renderer, str(source), "-o", str(destination)], check=True, capture_output=True, text=True)
    finally:
        if source is not None:
            source.unlink(missing_ok=True)


def plan_entries(plan: dict) -> list[tuple[str, dict]]:
    """Thumbnail briefs only; programmatic supports have their own guide."""
    return [
        ("thumbnail_main", plan.get("thumbnail") or {}),
        ("thumbnail_japanese", plan.get("japanese_thumbnail") or {}),
    ]


def plan_brief(entry: dict) -> str:
    """The complete image-generation prompt stored on one plan entry."""
    value = entry.get("image_prompt")
    return " ".join(value.split()) if isinstance(value, str) and value.strip() else ""


def plan_prompt_entries(plan: dict) -> list[tuple[str, str, str]]:
    """Return complete prompts paired with their exact specimen and ratio."""
    thumbnail = plan.get("thumbnail") or {}
    japanese = plan.get("japanese_thumbnail") or {}
    prompts: list[tuple[str, str, str]] = []
    main = plan_brief(thumbnail)
    if main:
        prompts.append((
            "thumbnail_main_3x2",
            "prepared_visuals/3x2/thumbnail_main.png",
            main,
        ))
    layouts = thumbnail.get("ratio_layouts") or {}
    square = plan_brief(layouts.get("1x1") or {})
    if square:
        prompts.append((
            "thumbnail_main_1x1",
            "prepared_visuals/1x1/thumbnail_main.png",
            square,
        ))
    storefront = plan_brief(japanese)
    if storefront:
        prompts.append((
            "thumbnail_japanese_1x1",
            "prepared_visuals/1x1/thumbnail_japanese.png",
            storefront,
        ))
    return prompts


def render_note(name: str, entry: dict, plan: dict) -> str:
    """Derive one per-image design note from the plan."""
    lines = [f"# Image Note: {name}", ""]
    for label, field in (("Buyer Question", "visual_question"), ("Verified Font Behavior", "font_feature")):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            lines += [f"## {label}", " ".join(value.split()), ""]

    copy = entry.get("copy_blocks") or []
    if copy:
        lines.append("## Exact Copy")
        lines += [f"- {str(block).replace(chr(10), ' / ')}" for block in copy]
        lines.append("")

    palette = plan.get("palette") or {}
    if palette or plan.get("contrast_checks"):
        lines.append("## Palette / Contrast")
        for key, value in palette.items():
            lines.append(f"- {key}: {value}")
        for check in plan.get("contrast_checks") or []:
            verdict = "passes" if check.get("pass") else "FAILS"
            lines.append(
                f"- {check.get('foreground')} on {check.get('background')}: "
                f"{check.get('ratio')}:1 (minimum {check.get('minimum')}:1) — {verdict}"
            )
        lines.append("")

    budget = entry.get("effect_budget")
    if isinstance(budget, str) and budget.strip():
        lines += ["## Effect Budget", " ".join(budget.split()), ""]

    layouts = entry.get("ratio_layouts") or {}
    for ratio in ("3x2", "1x1"):
        spec = layouts.get(ratio)
        if not isinstance(spec, dict):
            continue
        lines.append(f"## Independent {ratio} Composition")
        composition = spec.get("composition")
        if isinstance(composition, str) and composition.strip():
            lines.append(" ".join(composition.split()))
        if spec.get("focus"):
            lines.append(f"- Focus: {spec['focus']}")
        if spec.get("copy_order"):
            lines.append(f"- Copy order: {', '.join(map(str, spec['copy_order']))}")
        lines.append("")

    if layouts.get("3x2") and layouts.get("1x1"):
        lines += [
            "## Ratio Review",
            "Both ratios were authored as independent compositions, not one artboard "
            "cropped or padded twice; the landscape and square decisions differ above.",
            "",
        ]

    why = entry.get("why_unique")
    if isinstance(why, str) and why.strip():
        lines += ["## Why Not Redundant", " ".join(why.split()), ""]

    provenance = entry.get("copy_provenance")
    if isinstance(provenance, str) and provenance.strip():
        lines += ["## Copy Provenance", " ".join(provenance.split()), ""]

    return "\n".join(lines).rstrip() + "\n"


def render_art_direction(plan: dict, entries: list[tuple[str, dict]]) -> str:
    """Derive art-direction.md from the plan's campaign, profile and palette."""
    campaign = plan.get("campaign") or {}
    profile = plan.get("font_profile") or {}
    lines = [f"# Art Direction — {str(plan.get('font_name', '')).strip()}", ""]

    def section(title: str, *values: object) -> None:
        body = [str(v).strip() for v in values if isinstance(v, str) and str(v).strip()]
        if body:
            lines.extend([f"## {title}", ""] + body + [""])

    section("Font personality and construction", profile.get("construction"), profile.get("personality"))
    section("Product type and thumbnail subtext", profile.get("type_label"), profile.get("subtext"))
    section("Saved product description", profile.get("product_description"))
    features = profile.get("distinctive_features")
    if isinstance(features, list) and features:
        lines += ["- " + str(f) for f in features] + [""]
    section("Buyer and supported jobs", campaign.get("buyer"), profile.get("buyer_fit"))
    section("Central visual idea", campaign.get("visual_world"), campaign.get("palette_rationale"))
    section("What must be recognised in two seconds", campaign.get("thumbnail_promise"))

    palette = plan.get("palette") or {}
    if palette:
        lines += ["## Palette and contrast", ""]
        lines += [f"- {key}: {value}" for key, value in palette.items()]
        for check in plan.get("contrast_checks") or []:
            verdict = "passes" if check.get("pass") else "FAILS"
            lines.append(
                f"- {check.get('foreground')} on {check.get('background')}: "
                f"{check.get('ratio')}:1 (minimum {check.get('minimum')}:1) — {verdict}"
            )
        lines.append("")

    lines += ["## Image roles", ""]
    for name, entry in entries:
        role = str(entry.get("role") or entry.get("primary_job") or entry.get("context_type") or "").strip()
        copies = " / ".join(str(b).replace(chr(10), " ") for b in (entry.get("copy_blocks") or []))
        detail = f"- **{name}**"
        if role:
            detail += f" — {role}"
        if copies:
            detail += f' (copy: "{copies}")'
        lines.append(detail)
    lines.append("")

    themed = [(name, entry) for name, entry in entries if plan_brief(entry)]
    if themed:
        lines += ["## Displayed copy and its provenance", ""]
        for name, entry in themed:
            provenance = str(entry.get("copy_provenance") or "").strip() or "authored for this image"
            lines.append(f"- {name}: {provenance}")
        lines.append("")

    lines += [
        "## Generated from the plan",
        "",
        "This file, `theme.txt`, and `image-notes/` are derived from",
        "`visual-plan.json` by `bin/generate_font_text_placeholders.py`. Edit the",
        "plan, not these views: a hand edit here is overwritten on the next render.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_derived_views(direction: Path, plan: dict) -> list[Path]:
    """Derive theme.txt, image notes and art-direction.md from the plan.

    The plan is the single source of truth. These human-facing documents used to
    be authored separately by the agent, which cost output tokens for every run
    and let them drift out of agreement with the plan (and with each other).
    """
    direction.mkdir(parents=True, exist_ok=True)
    entries = plan_entries(plan)
    written: list[Path] = []

    prompts = plan_prompt_entries(plan)
    if prompts:
        body = "\n".join(
            f"## {name}\nSpecimen: `{specimen}`\n\n{prompt}\n"
            for name, specimen, prompt in prompts
        )
        theme = direction / "theme.txt"
        theme.write_text(body, encoding="utf-8")
        written.append(theme)

    notes_dir = direction / "image-notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    for name, entry in entries:
        note = notes_dir / f"{name}.md"
        note.write_text(render_note(name, entry, plan), encoding="utf-8")
        written.append(note)

    direction_file = direction / "art-direction.md"
    direction_file.write_text(render_art_direction(plan, entries), encoding="utf-8")
    written.append(direction_file)

    return written


def write_manifest(root: Path, plan: dict) -> None:
    family_showcases = [
        template for template in ("plakat32", "weightfamily32", "mangosboard32", "italicregular32")
        if template in (plan.get("_support_templates") or [])
    ]
    rows = [
        "# Visual Handoff Manifest",
        "",
        "- status: provisional",
        "- render_mode: text_placeholder",
        "- manual_replacement_required: thumbnail placeholders only",
        "- source: bin/generate_font_text_placeholders.py",
        "- note: three white-background font-name specimens are raw material for final thumbnail generation; use the matching per-ratio prompts in visual-direction/theme.txt.",
        f"- supporting_templates: {int(plan.get('support_count', 13))} reproducibly selected eligible layouts at 3:2 and 1:1",
        f"- support_renderer_policy: {plan.get('support_renderer', 'html')}",
        "- thumbnail_prompts: `../visual-direction/theme.txt` (derived from `visual-plan.json`)",
        "- family_showcase_templates: " + (", ".join(f"`{template}`" for template in family_showcases)
                                            if family_showcases else "none eligible for this single-style family"),
        "- pinterest_template_renderer: HTML/CSS + Chromium; all active pin templates",
        "- factual_specimen_renderer: Python Skia",
        "",
        "| Asset | Dimensions | Status |",
        "|---|---:|---|",
    ]
    image_paths = sorted([*root.rglob("*.png"), *root.rglob("*.jpg"), *root.rglob("*.jpeg")])
    for path in image_paths:
        with Image.open(path) as image:
            dimensions = f"{image.width}x{image.height}"
        relative = path.relative_to(root).as_posix()
        if relative.startswith("supporting/"):
            template = path.stem.removeprefix("support-").split("_", 1)[-1]
            renderer = (plan.get("_support_renderer_by_template") or {}).get(
                template, "Python Skia")
            status = f"{renderer} supporting template"
        elif relative.startswith("specimens/"):
            status = "factual font specimen"
        elif relative.startswith("pinterest/"):
            status = "HTML/CSS template Pinterest pin"
        else:
            status = "thumbnail placeholder — replace with image-model artwork"
        rows.append(f"| {relative} | {dimensions} | {status} |")
    (root / "visual-handoff-manifest.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_marker(root: Path, status: str, prepared_path: Path | None = None) -> None:
    marker = [
        "# VISUAL-HANDOFF-READY",
        "",
        f"validation: {status}",
        f"prepared visuals: {(prepared_path or root).resolve()}",
        "Visual status: three white-background font-name specimens are raw lettering material; supporting templates and factual specimens are renderer-generated.",
        "Use the matching 3:2, 1:1, and storefront prompts in visual-direction/theme.txt to create final thumbnail artwork, then replace the three matching specimens.",
        "Validator: python bin/validate_font_visual_handoff.py --strict-art-direction",
    ]
    (root / "VISUAL-HANDOFF-READY.md").write_text("\n".join(marker) + "\n", encoding="utf-8")


def validate(staging: Path, allow_pending: bool = False, report_success: bool = True) -> None:
    validator = Path(__file__).resolve().parent / "validate_font_visual_handoff.py"
    command = [
        sys.executable,
        str(validator),
        str(staging),
        "--strict-art-direction",
    ]
    if allow_pending:
        command.append("--allow-pending-marker")
    result = subprocess.run(command, text=True, capture_output=True, cwd=Path(__file__).resolve().parent.parent)
    if result.returncode:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("placeholder visual handoff failed mechanical validation")
    if report_success and result.stdout:
        sys.stdout.write(result.stdout)


def render_programmatic_assets(staging: Path, plan: dict, primary_font: Path) -> None:
    """Render support layouts, factual sheets, and every active Pinterest template."""
    renderer = Path(__file__).resolve().parent / "render-pins"
    if not renderer.is_file():
        raise SystemExit(f"support renderer is missing: {renderer}")
    renderer_class = plan.get("renderer_class")
    if renderer_class not in {"elegant", "blackletter", "sports", "script"}:
        raise SystemExit("visual plan renderer_class must be elegant, blackletter, sports, or script")
    profile = plan.get("font_profile") or {}
    about = " ".join(
        str(profile.get(key, "")).strip()
        for key in ("construction", "personality", "buyer_fit")
        if str(profile.get(key, "")).strip()
    )[:240]
    count = plan.get("support_count", 13)
    if count != 13:
        raise SystemExit("support_count is fixed at 13; omit it or set it to 13")
    support_renderer = plan.get("support_renderer", "html")
    if support_renderer != "html":
        raise SystemExit("support_renderer is fixed at html for the Agent 27 handoff")
    common = ["--font", str(primary_font), "--name", str(plan["font_name"]),
              "--class", renderer_class]
    if about:
        common += ["--about", about]
    support_args = common + [
        "--supports", "--support-count", "13",
        "--support-renderer", support_renderer,
        "--support-ratios", "both",
        "--json",
        "--out", str(staging / "supporting"),
    ]
    for label, args in (
        ("supporting templates", support_args),
        ("factual specimens", common + ["--specimens", "--out", str(staging / "specimens")]),
    ):
        result = subprocess.run([str(renderer), *args], text=True, capture_output=True,
                                cwd=Path(__file__).resolve().parent.parent)
        if result.returncode:
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
            raise SystemExit(f"image renderer failed while creating {label}")
        if label == "supporting templates":
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                raise SystemExit(f"support renderer returned invalid JSON: {error}") from error
            if not payload.get("ok"):
                raise SystemExit("support renderer reported layout errors")
            plan["_support_renderer_by_template"] = {
                item["template"]: item["renderer"]
                for item in payload.get("results", [])
            }
            plan["_support_templates"] = sorted(
                {item["template"] for item in payload.get("results", [])}
            )
            renderers = ", ".join(sorted(set(plan["_support_renderer_by_template"].values())))
            print(f"  supporting templates: {renderers or 'unknown renderer'}")
        elif result.stdout:
            sys.stdout.write(result.stdout)

    pin_renderer = Path(__file__).resolve().parents[1] / "font-factory" / "pin-html" / "render_gallery.mjs"
    if not pin_renderer.is_file():
        raise SystemExit(f"HTML/CSS Pinterest renderer is missing: {pin_renderer}")
    command = ["node", str(pin_renderer), "--mode", "pins", "--font", str(primary_font),
               "--font-name", str(plan["font_name"]), "--out", str(staging / "pinterest")]
    result = subprocess.run(command, text=True, capture_output=True,
                            cwd=Path(__file__).resolve().parent.parent)
    if result.returncode:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise SystemExit("HTML/CSS Pinterest template generation failed")
    if result.stdout:
        sys.stdout.write(result.stdout)


def write_space_report(
    root: Path,
    layout: list[tuple[str, str, tuple[int, int], list[tuple[float, float, float, float]]]],
) -> Path:
    """Report placeholder geometry without prescribing how to fill whitespace."""
    rows = [
        "# Placeholder Space Report",
        "",
        "Derived from the raw text placeholders. This report measures text bounds;",
        "it does not judge the finished thumbnail or prescribe added artwork.",
        "Open areas may remain intentionally empty when that gives the title room.",
        "Add a supporting element only when the font-specific concept needs it.",
        "",
    ]
    for name, ratio, (width, height), boxes in layout:
        if not boxes:
            continue
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        area = max(0.0, (x1 - x0)) * max(0.0, (y1 - y0))
        free = 1 - (area / (width * height))
        # 3x3 occupancy: which cells the text touches at all
        grid = []
        for row in range(3):
            cells = []
            for col in range(3):
                cx0, cx1 = width * col / 3, width * (col + 1) / 3
                cy0, cy1 = height * row / 3, height * (row + 1) / 3
                hit = x0 < cx1 and x1 > cx0 and y0 < cy1 and y1 > cy0
                cells.append("text" if hit else "----")
            grid.append(" ".join(cells))
        rows += [
            f"## {name} ({ratio})",
            "",
            f"- canvas: {width}x{height}",
            f"- text covers: {100 * area / (width * height):.0f}% of the frame; free: {100 * free:.0f}%",
            f"- margins: left {100 * x0 / width:.0f}%, right {100 * (width - x1) / width:.0f}%, "
            f"top {100 * y0 / height:.0f}%, bottom {100 * (height - y1) / height:.0f}%",
            "- occupancy grid (top row first):",
            "",
            "```",
            *grid,
            "```",
            "",
        ]
        free_cells = sum(1 for row in grid for c in row.split() if c == "----")
        if free_cells >= 3:
            rows.append(
                f"- **{free_cells} of 9 regions are free.** The brief for this image must "
                "name the artwork, illustration, effect, or texture that occupies them."
            )
        rows.append("")
    path = root / "space-report.md"
    path.write_text("\n".join(rows).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path, help="visual-direction/visual-plan.json")
    parser.add_argument("--output", required=True, type=Path, help="prepared_visuals directory")
    args = parser.parse_args()

    plan_path = args.plan.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not plan_path.is_file():
        raise SystemExit(f"visual plan not found: {plan_path}")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {output}")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or plan.get("render_mode") not in {"text_placeholder", "placeholder", "white_text"}:
        raise SystemExit("visual plan render_mode must be text_placeholder")
    workspace = plan_path.parent.parent
    font_name = str(plan.get("font_name", "")).strip()
    if not font_name:
        raise SystemExit("visual plan font_name is required")
    primary_font = require_font(plan.get("primary_font"), workspace, "primary")
    japanese_font = resolve_path(plan.get("japanese_font"), workspace)
    if japanese_font is None or not japanese_font.is_file():
        japanese_font = fallback_font()
    primary_outline = OutlineFont(primary_font)
    japanese_outline = OutlineFont(japanese_font)
    promos = plan.get("promos", [])
    if promos not in (None, []):
        raise SystemExit("visual plan promos are retired; supporting images come from the shared template catalogue")
    if plan.get("support_count", 13) != 13:
        raise SystemExit("visual plan support_count must remain 13")
    if plan.get("support_renderer", "html") != "html":
        raise SystemExit("visual plan support_renderer must be html")
    if plan.get("renderer_class") not in {"elegant", "blackletter", "sports", "script"}:
        raise SystemExit("visual plan renderer_class must be elegant, blackletter, sports, or script")

    output.parent.mkdir(parents=True, exist_ok=True)
    # Sweep staging directories orphaned by a previous hard kill: SIGKILL gives the
    # except-block below no chance to run, and the leftovers accumulate invisibly.
    for orphan in output.parent.glob(f".{output.name}.staging-*"):
        shutil.rmtree(orphan, ignore_errors=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=str(output.parent)))
    try:
        for ratio, size in RATIOS.items():
            (staging / ratio).mkdir(parents=True, exist_ok=True)
        layout: list[tuple[str, str, tuple[int, int], list]] = []
        for name, owner, size, ratio in (
            ("thumbnail_main", plan["thumbnail"], RATIOS["3x2"], "3x2"),
            ("thumbnail_main", plan["thumbnail"], RATIOS["1x1"], "1x1"),
            ("thumbnail_japanese", plan["japanese_thumbnail"], RATIOS["1x1"], "1x1"),
        ):
            svg, boxes = render_placeholder(owner, size, ratio, name, primary_outline, japanese_outline if name == "thumbnail_japanese" else primary_outline)
            write_placeholder_png(svg, staging / ratio / f"{name}.png")
            layout.append((name, ratio, size, boxes))
        render_programmatic_assets(staging, plan, primary_font)
        write_space_report(staging, layout)
        write_manifest(staging, plan)
        derived = write_derived_views(plan_path.parent, plan)
        write_marker(staging, "pending", output)
        validate(staging, allow_pending=True, report_success=False)
        write_marker(staging, "PASS", output)
        validate(staging)
        if output.exists():
            output.rmdir()
        staging.replace(output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    print(f"[PASS] provisional text visual handoff ready: {output}")
    print(f"[PASS] derived {len(derived)} view(s) from the plan in {plan_path.parent}")
    print("[PASS] Thumbnail placeholders are provisional; 13 support templates (26 renders) were rendered at both 3:2 and 1:1.")
    print("[PASS] All active HTML/CSS Pinterest templates were rendered with the primary font.")
    print("[PASS] READY FOR FONT PREP HANDOFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
