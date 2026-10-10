#!/usr/bin/env python3
"""Create a fast provisional white-background font visual handoff.

The handoff deliberately contains only readable copy and factual specimen
sheets. It is a temporary downstream-compatible stand-in for the user's later
Custom GPT/image-model artwork and does not invoke OpenPencil.
"""

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
    """Ordered (name, entry) pairs, matching the rendered PNG names."""
    entries: list[tuple[str, dict]] = [
        ("thumbnail_main", plan.get("thumbnail") or {}),
        ("thumbnail_japanese", plan.get("japanese_thumbnail") or {}),
    ]
    for index, promo in enumerate(plan.get("promos") or [], start=1):
        key = str(promo.get("key") or "").strip() or f"promo_{index}"
        entries.append((key, promo))
    return entries


def plan_brief(entry: dict) -> str:
    """The creative brief for one image. One source, one place."""
    for field in ("theme_variant", "brief"):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return ""


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

    briefs = [(name, plan_brief(entry)) for name, entry in entries]
    briefs = [(name, brief) for name, brief in briefs if brief]
    if briefs:
        body = "\n".join(f"## {name}\n{brief}\n" for name, brief in briefs)
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
    rows = [
        "# Visual Handoff Manifest",
        "",
        "- status: provisional",
        "- render_mode: text_placeholder",
        "- manual_replacement_required: true",
        "- source: bin/generate_font_text_placeholders.py",
        "- note: white-background text placeholders are intentionally passed downstream until manually replaced.",
        f"- supporting_image_theme: {str(plan.get('supporting_image_theme', '')).strip()}",
        f"- theme_variants_file: {str(plan.get('theme_variants_file', '')).strip()}",
        "",
        "| Asset | Dimensions | Status |",
        "|---|---:|---|",
    ]
    for path in sorted(root.rglob("*.png")):
        with Image.open(path) as image:
            dimensions = f"{image.width}x{image.height}"
        rows.append(f"| {path.relative_to(root).as_posix()} | {dimensions} | provisional handoff |")
    (root / "visual-handoff-manifest.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_marker(root: Path, status: str, prepared_path: Path | None = None) -> None:
    marker = [
        "# VISUAL-HANDOFF-READY",
        "",
        f"validation: {status}",
        f"prepared visuals: {(prepared_path or root).resolve()}",
        "Visual status: PROVISIONAL — MANUAL IMAGE REPLACEMENT REQUIRED",
        "The default workflow may continue with these text placeholders. Replace the PNGs later with the user's Custom GPT/image-model artwork.",
        "Validator: python bin/validate_font_visual_handoff.py --strict-art-direction",
    ]
    (root / "VISUAL-HANDOFF-READY.md").write_text("\n".join(marker) + "\n", encoding="utf-8")


def render_specimens(staging: Path, primary_font: Path, font_name: str) -> None:
    specimen_output = Path(tempfile.mkdtemp(prefix="font-specimens-", dir=str(staging.parent)))
    try:
        renderer = Path(__file__).resolve().parent / "render_font_specimens.py"
        subprocess.run(
            [sys.executable, str(renderer), str(primary_font), str(specimen_output), "--name", font_name],
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        for source_ratio, target_ratio in (("main", "3x2"), ("squares", "1x1")):
            target = staging / "specimens" / target_ratio
            target.mkdir(parents=True, exist_ok=True)
            for source in specimen_output.joinpath(source_ratio).glob("specimen-*.png"):
                shutil.copy2(source, target / source.name)
    finally:
        shutil.rmtree(specimen_output, ignore_errors=True)


def validate(staging: Path, allow_pending: bool = False) -> None:
    validator = Path(__file__).resolve().parent / "validate_font_visual_handoff.py"
    command = [
        sys.executable,
        str(validator),
        str(staging),
        "--strict-art-direction",
        "--min-promos",
        "8",
        "--max-promos",
        "8",
    ]
    if allow_pending:
        command.append("--allow-pending-marker")
    result = subprocess.run(command, text=True, capture_output=True, cwd=Path(__file__).resolve().parent.parent)
    if result.returncode:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("placeholder visual handoff failed mechanical validation")
    if result.stdout:
        sys.stdout.write(result.stdout)


def write_space_report(
    root: Path,
    layout: list[tuple[str, str, tuple[int, int], list[tuple[float, float, float, float]]]],
) -> Path:
    """Report where the text sits and how much space it leaves, as text.

    This agent has no vision, so it cannot look at the rendered placeholder --
    which is why briefs were written blind and one of them described two thirds
    of the frame as "empty amber-tinted field". The renderer knows the exact
    geometry, so it states it: a 3x3 occupancy map plus the free margins. The
    brief can then commit to what occupies the empty region instead of guessing.
    """
    rows = [
        "# Placeholder Space Report",
        "",
        "Derived from the rendered text placeholders. The brief for each image must",
        "account for the free space named here: say what occupies it, not merely what",
        "colour it is. An `empty` region described only as a colour field is a wasted",
        "panel.",
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
    supporting_image_theme = plan.get("supporting_image_theme")
    if not isinstance(supporting_image_theme, str) or not supporting_image_theme.strip():
        raise SystemExit("visual plan supporting_image_theme is required; paste the Font Renamer theme sentence verbatim")
    if "\n" in supporting_image_theme or "\r" in supporting_image_theme:
        raise SystemExit("visual plan supporting_image_theme must be exactly one line")
    primary_font = require_font(plan.get("primary_font"), workspace, "primary")
    japanese_font = resolve_path(plan.get("japanese_font"), workspace)
    if japanese_font is None or not japanese_font.is_file():
        japanese_font = fallback_font()
    primary_outline = OutlineFont(primary_font)
    japanese_outline = OutlineFont(japanese_font)
    promos = plan.get("promos")
    if not isinstance(promos, list) or len(promos) != 8:
        raise SystemExit("visual plan promos must contain exactly 8 entries")

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
        for index, promo in enumerate(promos, start=1):
            for ratio, size in (("3x2", RATIOS["3x2"]), ("1x1", RATIOS["1x1"])):
                svg, boxes = render_placeholder(promo, size, ratio, f"promo_{index}", primary_outline, primary_outline)
                write_placeholder_png(svg, staging / ratio / f"promo_{index}.png")
                layout.append((f"promo_{index}", ratio, size, boxes))
        write_space_report(staging, layout)
        render_specimens(staging, primary_font, font_name)
        write_manifest(staging, plan)
        derived = write_derived_views(plan_path.parent, plan)
        write_marker(staging, "pending", output)
        validate(staging, allow_pending=True)
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
    print("[PASS] Visual status: PROVISIONAL — MANUAL IMAGE REPLACEMENT REQUIRED")
    print("[PASS] READY FOR FONT PREP HANDOFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
