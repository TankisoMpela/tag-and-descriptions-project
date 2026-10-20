#!/usr/bin/env python3
"""Validate Agent 27's thumbnail, support-template, and specimen handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image


SUPPORT_RE = re.compile(r"^support-\d+_[a-z0-9]+\.png$")
THUMBNAIL_VARIANTS = {"left", "center", "band"}
RENDERER_CLASSES = {"elegant", "blackletter", "sports", "script"}
ACTIVE_PIN_TEMPLATES = (
    "hero", "set", "wall", "full_stack", "studio_cover", "specimen_mosaic",
    "initials", "knotband", "scriptorium", "carol", "illuminated_broadside",
    "scribe_gallery", "crest", "bib", "lane", "finish", "timer", "guide",
    "trace", "letter_study", "coffee_roaster", "punk_manifesto", "neon_overprint",
)
PLACEHOLDER_COPY = (
    "Final Name",
    "SHORT SUPPORTED STYLE",
    "A SHORT PHRASE",
    "A BUYER USE CASE",
    "A factual supporting line",
    "A CLEAR TITLE",
    "A straightforward buyer-facing application",
    "approved product description",
)


def check_png(path: Path, expected_size: tuple[int, int], failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"missing: {path}")
        return
    try:
        with Image.open(path) as image:
            image.load()
            if image.size != expected_size:
                failures.append(f"wrong dimensions: {path} is {image.size}, expected {expected_size}")
    except Exception as error:
        failures.append(f"unreadable PNG: {path}: {error}")


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(value: str) -> float:
        value = value.lstrip("#")
        channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    light = max(luminance(foreground), luminance(background))
    dark = min(luminance(foreground), luminance(background))
    return (light + 0.05) / (dark + 0.05)


def validate_copy(owner: object, label: str, plan: dict, failures: list[str]) -> None:
    if not isinstance(owner, dict):
        failures.append(f"strict art-direction: {label} must be an object")
        return
    blocks = owner.get("copy_blocks")
    if not isinstance(blocks, list) or len(blocks) != 1 or not isinstance(blocks[0], str) or not blocks[0].strip():
        failures.append(f"strict art-direction: {label}.copy_blocks must contain exactly the font name")
        return
    shown = " ".join(blocks[0].split())
    expected = " ".join(str(plan.get("font_name", "")).split())
    if shown.casefold() != expected.casefold():
        failures.append(f"strict art-direction: {label} displays {shown!r}, not the exact font name {expected!r}")


def validate_free_space(owner: object, label: str, failures: list[str]) -> None:
    value = owner.get("free_space") if isinstance(owner, dict) else None
    if not isinstance(value, str) or len(value.split()) < 6:
        failures.append(f"strict art-direction: {label}.free_space must describe the open-space decision")


def validate_image_prompt(owner: object, label: str, failures: list[str]) -> None:
    prompt = owner.get("image_prompt") if isinstance(owner, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        failures.append(f"strict art-direction: {label}.image_prompt must be a complete prompt")


def validate_layouts(owner: object, label: str, failures: list[str]) -> None:
    layouts = owner.get("ratio_layouts") if isinstance(owner, dict) else None
    if not isinstance(layouts, dict):
        failures.append(f"strict art-direction: {label}.ratio_layouts is required")
        return
    signatures: list[tuple[str, str, tuple[str, ...]]] = []
    for ratio in ("3x2", "1x1"):
        layout = layouts.get(ratio)
        if not isinstance(layout, dict):
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio} is required")
            continue
        for key in ("composition", "focus"):
            if not isinstance(layout.get(key), str) or not layout[key].strip():
                failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.{key} is required")
        order = layout.get("copy_order")
        if not isinstance(order, list) or not order or any(not isinstance(item, str) or not item.strip() for item in order):
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.copy_order must be non-empty")
            order = []
        if layout.get("layout_variant") not in THUMBNAIL_VARIANTS:
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.layout_variant must be left, center, or band")
        signatures.append((str(layout.get("composition")), str(layout.get("focus")), tuple(order)))
    if len(signatures) == 2 and signatures[0] == signatures[1]:
        failures.append(f"strict art-direction: {label} must make different 3:2 and 1:1 crop decisions")


def validate_japanese_square(owner: object, failures: list[str]) -> None:
    layouts = owner.get("ratio_layouts") if isinstance(owner, dict) else None
    layout = layouts.get("1x1") if isinstance(layouts, dict) else None
    if not isinstance(layout, dict):
        failures.append("strict art-direction: japanese_thumbnail.ratio_layouts.1x1 is required")
        return
    for key in ("composition", "focus"):
        if not isinstance(layout.get(key), str) or not layout[key].strip():
            failures.append(f"strict art-direction: japanese_thumbnail.ratio_layouts.1x1.{key} is required")
    order = layout.get("copy_order")
    if not isinstance(order, list) or not order or any(not isinstance(item, str) or not item.strip() for item in order):
        failures.append("strict art-direction: japanese_thumbnail 1x1 copy_order must be non-empty")


def validate_art_direction(root: Path, failures: list[str]) -> dict | None:
    direction = root.parent / "visual-direction"
    for name in ("art-direction.md", "visual-plan.json", "candidate-review.md"):
        if not (direction / name).is_file():
            failures.append(f"strict art-direction: missing {direction / name}")
    plan_path = direction / "visual-plan.json"
    if not plan_path.is_file():
        return None
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"strict art-direction: unreadable plan: {plan_path}: {error}")
        return None
    if not isinstance(plan, dict):
        failures.append("strict art-direction: visual plan must be an object")
        return None

    if plan.get("render_mode") != "text_placeholder":
        failures.append("strict art-direction: render_mode must be text_placeholder")
    font_name = plan.get("font_name")
    if not isinstance(font_name, str) or not font_name.strip():
        failures.append("strict art-direction: font_name must be non-empty")
    if not isinstance(plan.get("primary_font"), str) or not plan["primary_font"].strip():
        failures.append("strict art-direction: primary_font must identify the source font")
    if plan.get("renderer_class") not in RENDERER_CLASSES:
        failures.append("strict art-direction: renderer_class must be elegant, blackletter, sports, or script")
    if plan.get("support_count", 7) != 7:
        failures.append("strict art-direction: support_count is fixed at 7")
    if plan.get("support_renderer", "html") not in {"skia", "hybrid", "html"}:
        failures.append("strict art-direction: support_renderer must be skia, hybrid, or html")
    if plan.get("promos") not in (None, []):
        failures.append("strict art-direction: custom promos are retired; use the support-template catalogue")
    for retired in ("supporting_image_theme", "thumbnail_candidates", "selected_thumbnail_candidate"):
        if retired in plan:
            failures.append(f"strict art-direction: {retired} is retired from the one-pass handoff")

    campaign = plan.get("campaign")
    if not isinstance(campaign, dict):
        failures.append("strict art-direction: campaign object is required")
    else:
        for key in ("visual_world", "buyer", "thumbnail_promise"):
            if not isinstance(campaign.get(key), str) or not campaign[key].strip():
                failures.append(f"strict art-direction: campaign.{key} must be non-empty")

    profile = plan.get("font_profile")
    if not isinstance(profile, dict):
        failures.append("strict art-direction: font_profile object is required")
    else:
        for key in ("construction", "personality", "buyer_fit"):
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                failures.append(f"strict art-direction: font_profile.{key} must be non-empty")

    checks, palette = plan.get("contrast_checks"), plan.get("palette")
    if not isinstance(checks, list) or len(checks) < 2 or not isinstance(palette, dict):
        failures.append("strict art-direction: palette and at least two contrast_checks are required")
    else:
        for index, check in enumerate(checks, start=1):
            if not isinstance(check, dict):
                failures.append(f"strict art-direction: contrast_checks[{index}] must be an object")
                continue
            foreground = palette.get(check.get("foreground"))
            background = palette.get(check.get("background"))
            minimum = check.get("minimum")
            if not isinstance(foreground, str) or not isinstance(background, str) or not isinstance(minimum, (int, float)):
                failures.append(f"strict art-direction: contrast_checks[{index}] is incomplete")
                continue
            try:
                ratio = contrast_ratio(foreground, background)
            except (TypeError, ValueError):
                failures.append(f"strict art-direction: contrast_checks[{index}] has invalid colours")
                continue
            if ratio < float(minimum):
                failures.append(f"strict art-direction: contrast_checks[{index}] is {ratio:.2f}:1, below {float(minimum):.2f}:1")

    thumbnail = plan.get("thumbnail")
    japanese = plan.get("japanese_thumbnail")
    validate_copy(thumbnail, "thumbnail", plan, failures)
    validate_layouts(thumbnail, "thumbnail", failures)
    validate_free_space(thumbnail, "thumbnail", failures)
    validate_image_prompt(thumbnail, "thumbnail 3:2", failures)
    square_layouts = thumbnail.get("ratio_layouts") if isinstance(thumbnail, dict) else None
    validate_image_prompt(
        square_layouts.get("1x1") if isinstance(square_layouts, dict) else None,
        "thumbnail 1:1",
        failures,
    )
    validate_copy(japanese, "japanese_thumbnail", plan, failures)
    validate_japanese_square(japanese, failures)
    validate_free_space(japanese, "japanese_thumbnail", failures)
    validate_image_prompt(japanese, "japanese_thumbnail 1:1", failures)

    theme_path = direction / "theme.txt"
    if not theme_path.is_file():
        failures.append(f"strict art-direction: missing {theme_path}")
    else:
        theme = theme_path.read_text(encoding="utf-8")
        for heading in (
            "## thumbnail_main_3x2",
            "## thumbnail_main_1x1",
            "## thumbnail_japanese_1x1",
        ):
            if heading not in theme:
                failures.append(f"strict art-direction: theme.txt is missing prompt section {heading[3:]}")

    serialized = json.dumps(plan, ensure_ascii=False)
    for placeholder in PLACEHOLDER_COPY:
        if placeholder in serialized:
            failures.append(f"strict art-direction: replace plan placeholder copy: {placeholder}")
    return plan


def validate_handoff_documents(
    root: Path,
    required_assets: list[str],
    failures: list[str],
    allow_pending_marker: bool,
) -> None:
    marker_path = root / "VISUAL-HANDOFF-READY.md"
    if not marker_path.is_file():
        failures.append(f"missing handoff marker: {marker_path}")
    else:
        marker = marker_path.read_text(encoding="utf-8")
        match = re.search(r"^\s*validation\s*:\s*(\S+)", marker, re.IGNORECASE | re.MULTILINE)
        status = match.group(1).casefold() if match else ""
        if status == "pending" and allow_pending_marker:
            pass
        elif status != "pass":
            failures.append(f"handoff marker must record validation: PASS (found {status or 'missing'})")
        if "prepared visuals" not in marker.casefold():
            failures.append("handoff marker must record the prepared visuals path")
        if status == "pass" and "validate_font_visual_handoff.py" not in marker:
            failures.append("handoff marker must record the successful validator command")

    manifest_path = root / "visual-handoff-manifest.md"
    if not manifest_path.is_file():
        failures.append(f"missing visual manifest: {manifest_path}")
        return
    manifest = manifest_path.read_text(encoding="utf-8")
    if "status" not in manifest.casefold() or "dimension" not in manifest.casefold():
        failures.append("visual manifest must include status and dimension fields")
    required_paths = [
        "3x2/thumbnail_main.png",
        "1x1/thumbnail_main.png",
        "1x1/thumbnail_japanese.png",
        *required_assets,
    ]
    for required in required_paths:
        if required not in manifest:
            failures.append(f"visual manifest is missing an asset row for {required}")


def validate_pinterest_templates(root: Path, plan: dict | None, failures: list[str]) -> list[str]:
    pin_dir = root / "pinterest"
    manifest_path = pin_dir / "pinterest-template-manifest.json"
    if not manifest_path.is_file():
        failures.append(f"missing Pinterest template manifest: {manifest_path}")
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"invalid Pinterest template manifest: {error}")
        return []
    if manifest.get("kind") != "font-template-pinterest-pins":
        failures.append("Pinterest template manifest has the wrong kind")
    if plan and manifest.get("font_name") != plan.get("font_name"):
        failures.append("Pinterest template manifest font name does not match the visual plan")
    rows = manifest.get("images")
    if not isinstance(rows, list) or len(rows) != len(ACTIVE_PIN_TEMPLATES):
        failures.append(f"Pinterest template manifest must contain {len(ACTIVE_PIN_TEMPLATES)} pins")
        return []
    expected_files: list[str] = []
    for index, (row, template) in enumerate(zip(rows, ACTIVE_PIN_TEMPLATES), start=1):
        if not isinstance(row, dict):
            failures.append(f"Pinterest template row {index} must be an object")
            continue
        file = f"pinterest_{index}.jpg"
        expected_files.append(file)
        if row.get("index") != index or row.get("template") != template or row.get("file") != file:
            failures.append(f"Pinterest template row {index} must map to {template} / {file}")
        path = pin_dir / file
        if not path.is_file():
            failures.append(f"missing Pinterest template pin: {path}")
            continue
        if path.stat().st_size > 200000:
            failures.append(f"Pinterest template pin exceeds 200000 bytes: {path}")
        try:
            with Image.open(path) as image:
                image.load()
                if image.format != "JPEG" or image.size != (1000, 1500):
                    failures.append(f"Pinterest template pin must be 1000x1500 JPEG: {path}")
        except Exception as error:
            failures.append(f"unreadable Pinterest template pin {path}: {error}")
        if row.get("bytes") != path.stat().st_size:
            failures.append(f"Pinterest manifest byte size does not match: {path}")
        if row.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            failures.append(f"Pinterest manifest SHA-256 does not match: {path}")
    actual_files = sorted(path.name for path in pin_dir.glob("pinterest_*")
                          if path.is_file() and path.name != "pinterest-template-manifest.json")
    if actual_files != sorted(expected_files):
        failures.append("Pinterest folder must contain exactly the 23 numbered template pins")
    return [f"pinterest/{name}" for name in expected_files]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared_visuals", type=Path)
    parser.add_argument("--strict-art-direction", action="store_true")
    parser.add_argument("--allow-pending-marker", action="store_true")
    args = parser.parse_args()

    root = args.prepared_visuals
    failures: list[str] = []
    if not root.is_dir():
        print(f"[FAIL] missing handoff directory: {root}")
        return 1
    for required in ("VISUAL-HANDOFF-READY.md", "visual-handoff-manifest.md"):
        if not (root / required).is_file():
            failures.append(f"missing handoff file: {root / required}")
    plan = validate_art_direction(root, failures) if args.strict_art_direction else None
    pin_assets = validate_pinterest_templates(root, plan, failures)

    sizes = {"3x2": (2400, 1600), "1x1": (1600, 1600)}
    check_png(root / "3x2" / "thumbnail_main.png", sizes["3x2"], failures)
    check_png(root / "1x1" / "thumbnail_main.png", sizes["1x1"], failures)
    check_png(root / "1x1" / "thumbnail_japanese.png", sizes["1x1"], failures)
    for ratio in sizes:
        stale = list((root / ratio).glob("promo_*.png"))
        if stale:
            failures.append(f"{ratio}: retired promo PNGs remain: {', '.join(path.name for path in stale)}")

    required_assets = [
        "specimens/3x2/specimen-letters.png",
        "specimens/3x2/specimen-numerals.png",
        "specimens/1x1/specimen-letters.png",
        "specimens/1x1/specimen-numerals.png",
    ]
    for relative in required_assets:
        ratio = relative.split("/")[1]
        check_png(root / relative, sizes[ratio], failures)
    required_assets.extend(pin_assets)

    support_names: dict[str, set[str]] = {}
    support_count = 0
    for ratio in sizes:
        support_dir = root / "supporting" / ratio
        supports = sorted(support_dir.glob("support-*.png")) if support_dir.is_dir() else []
        if len(supports) != 7:
            failures.append(f"supporting/{ratio}: expected exactly 7 support templates, found {len(supports)}")
        names = {path.stem.split("_", 1)[-1] for path in supports}
        support_names[ratio] = names
        if len(names) != len(supports):
            failures.append(f"supporting/{ratio}: duplicate template names found")
        for path in supports:
            if not SUPPORT_RE.fullmatch(path.name):
                failures.append(f"supporting/{ratio}: unexpected support filename: {path.name}")
            check_png(path, sizes[ratio], failures)
            required_assets.append(path.relative_to(root).as_posix())
        support_count += len(supports)
    if support_names.get("3x2") != support_names.get("1x1"):
        failures.append("supporting: the selected 3:2 and 1:1 templates must be the same seven layouts")

    png_count = len(list(root.rglob("*.png")))
    if png_count != 21:
        failures.append(f"handoff: expected exactly 21 PNGs (3 thumbnails, 14 support renders, 4 specimens), found {png_count}")

    validate_handoff_documents(root, required_assets, failures, args.allow_pending_marker)
    if plan is not None and plan.get("render_mode") != "text_placeholder":
        failures.append("unsupported visual plan render_mode")
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(f"[PASS] visual handoff valid: {png_count} PNGs, {len(pin_assets)} Pinterest JPEGs (3 thumbnails, {support_count} support renders, 4 factual specimens)")
    print("[PASS] supporting templates: 7 matched layouts at 3:2 and 1:1")
    print("[PASS] factual specimens: 4 across 3x2 and 1x1")
    print(f"[PASS] Pinterest templates: {len(pin_assets)} rendered with the supplied font")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
