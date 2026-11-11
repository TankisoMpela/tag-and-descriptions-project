#!/usr/bin/env python3
"""Validate Agent 27's thumbnail, support-template, and specimen handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_CATALOG = PROJECT_ROOT / "font-factory" / "support-html" / "catalog.json"
SUPPORT_RE = re.compile(r"^support-\d+_[a-z0-9]+(?:-[a-z0-9]+)*\.png$")
THUMBNAIL_VARIANTS = {"left", "center", "band"}
RENDERER_CLASSES = {"elegant", "blackletter", "sports", "script"}
FAMILY_SHOWCASE_TEMPLATES = {
    "weightfamily32", "mangosboard32", "italicregular32",
}
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
CONCEPT_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on",
    "one", "the", "to", "with", "your", "font", "name", "thumbnail",
    "direction", "design", "visual", "image", "concept", "style", "using",
}
PALETTE_WORDS = {
    "amber", "aqua", "beige", "black", "blue", "bone", "brick", "bronze",
    "brown", "charcoal", "coral", "cream", "crimson", "cyan", "gold", "gray",
    "grey", "green", "ivory", "jade", "lavender", "lime", "magenta", "maroon",
    "mint", "navy", "ochre", "olive", "orange", "pale", "pink", "purple", "red",
    "rose", "rust", "saturated", "scarlet", "slate", "teal", "turquoise", "vermilion",
    "warm", "white", "yellow", "muted", "deep", "dark", "light",
}


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


def check_generated_thumbnail(path: Path, ratio: float, failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"missing generated thumbnail: {path}")
        return
    try:
        with Image.open(path) as image:
            image.load()
            actual = image.width / image.height
            if abs(actual - ratio) > 0.025:
                failures.append(
                    f"wrong thumbnail ratio: {path} is {image.width}x{image.height}, expected approximately {ratio:.2f}:1"
                )
    except Exception as error:
        failures.append(f"unreadable generated thumbnail: {path}: {error}")


def active_html_support_templates(failures: list[str]) -> set[str]:
    try:
        catalog = json.loads(SUPPORT_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"support catalogue: cannot read {SUPPORT_CATALOG}: {error}")
        return set()
    templates = catalog.get("templates") if isinstance(catalog, dict) else None
    if not isinstance(templates, list):
        failures.append(f"support catalogue: templates must be a list in {SUPPORT_CATALOG}")
        return set()
    return {
        item["id"] for item in templates
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("htmlEntry")
        and item.get("portStatus") in {"prototype", "ported"}
    }


def source_family_style_count(root: Path, plan: dict, failures: list[str]) -> int | None:
    value = plan.get("primary_font")
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    workspace = root.parent.resolve()
    if not path.is_absolute():
        path = workspace / path
    path = path.resolve()
    try:
        path.relative_to(workspace)
    except ValueError:
        failures.append("strict art-direction: primary_font must remain inside the font-factory/fonts source workspace")
        return None
    if not path.is_file():
        failures.append(f"strict art-direction: source font is missing: {path}")
        return None

    try:
        from fontTools.ttLib import TTFont

        primary = TTFont(str(path), fontNumber=0, lazy=True)
        try:
            names = primary["name"]
            family = (names.getDebugName(16) or names.getDebugName(1) or "").strip()
            cmap = primary.getBestCmap() or {}
            basic_latin = sum(
                1 for codepoint in cmap
                if 0x41 <= codepoint <= 0x5A or 0x61 <= codepoint <= 0x7A
            )
            plan["_verified_coverage"] = {
                "mapped_characters": len(cmap),
                "basic_latin": f"{basic_latin}/52",
            }
        finally:
            primary.close()
        if not family:
            failures.append(f"strict art-direction: source font has no family name: {path}")
            return None

        candidates = [
            candidate for candidate in sorted(path.parent.iterdir())
            if candidate.suffix.casefold() in {".otf", ".ttf"}
        ]
        plan["_verified_source_formats"] = sorted(
            {candidate.suffix[1:].upper() for candidate in candidates}
        )
        styles: dict[tuple[str, int], dict] = {}
        for candidate in candidates:
            try:
                face = TTFont(str(candidate), fontNumber=0, lazy=True)
                try:
                    face_names = face["name"]
                    face_family = (
                        face_names.getDebugName(16) or face_names.getDebugName(1) or ""
                    ).strip()
                    if face_family.casefold() != family.casefold():
                        continue
                    style = (
                        face_names.getDebugName(17) or face_names.getDebugName(2) or "Regular"
                    ).strip()
                    os2 = face["OS/2"]
                    weight = int(getattr(os2, "usWeightClass", 400))
                    width = int(getattr(os2, "usWidthClass", 5))
                    selection = int(getattr(os2, "fsSelection", 0))
                    post = face["post"] if "post" in face else None
                    italic = bool(selection & (1 | (1 << 9))) or bool(
                        post and abs(float(getattr(post, "italicAngle", 0.0))) > 0.01
                    ) or any(token in style.casefold() for token in ("italic", "oblique"))
                    key = (style.casefold(), weight)
                    row = {
                        "style_name": style,
                        "weight_class": weight,
                        "width_class": width,
                        "italic": italic,
                    }
                    prior = styles.get(key)
                    if prior is None or (
                        candidate.suffix.casefold() == ".otf"
                        and prior.get("_format") != "otf"
                    ):
                        row["_format"] = candidate.suffix.casefold()[1:]
                        styles[key] = row
                finally:
                    face.close()
            except Exception:
                continue
        rows = sorted(
            styles.values(),
            key=lambda item: (item["weight_class"], item["style_name"].casefold()),
        )
        plan["_verified_family_styles"] = [
            {key: value for key, value in row.items() if key != "_format"}
            for row in rows
        ]
        return max(1, len(rows))
    except Exception as error:
        failures.append(f"strict art-direction: cannot inspect source font family: {path}: {error}")
        return None


def name_tokens(value: str) -> set[str]:
    """Normalize a name for detecting source-name carry-through."""
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    normalized = unicodedata.normalize("NFKD", spaced)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", ascii_text)}


def validate_product_name(root: Path, plan: dict, failures: list[str]) -> None:
    """Reject an agent-selected product name that merely carries the source name."""
    origin = plan.get("name_origin", "agent_selected")
    if origin not in {"agent_selected", "user_supplied"}:
        failures.append(
            "strict art-direction: name_origin must be 'agent_selected' or 'user_supplied'"
        )
        return
    if origin == "user_supplied":
        return

    primary_value = plan.get("primary_font")
    product_name = plan.get("font_name")
    if not isinstance(primary_value, str) or not isinstance(product_name, str):
        return
    workspace = root.parent.resolve()
    source = Path(primary_value).expanduser()
    if not source.is_absolute():
        source = workspace / source
    source = source.resolve()
    try:
        source.relative_to(workspace)
    except ValueError:
        return  # The primary-font validator reports the path violation.
    if not source.is_file():
        return  # The primary-font validator reports the missing source.

    try:
        from fontTools.ttLib import TTFont
    except ImportError as error:
        failures.append(f"strict art-direction: cannot inspect source names: {error}")
        return

    source_names: set[str] = set()
    for candidate in sorted(source.parent.iterdir()):
        if candidate.suffix.casefold() not in {".otf", ".ttf"}:
            continue
        source_names.add(candidate.stem)
        try:
            face = TTFont(str(candidate), fontNumber=0, lazy=True)
            try:
                names = face["name"]
                for name_id in (1, 16):
                    value = (names.getDebugName(name_id) or "").strip()
                    if value:
                        source_names.add(value)
            finally:
                face.close()
        except Exception:
            continue

    product_tokens = name_tokens(product_name)
    for source_name in sorted(source_names):
        tokens = name_tokens(source_name)
        if tokens and tokens <= product_tokens:
            failures.append(
                f"strict art-direction: agent-selected font_name {product_name!r} reuses "
                f"source name {source_name!r}; choose a distinct product name or record "
                "name_origin='user_supplied' for an explicitly requested name"
            )
            return


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


def validate_lettering_colors(owner: object, label: str, failures: list[str]) -> None:
    if not isinstance(owner, dict):
        return
    colors = owner.get("lettering_colors")
    if not isinstance(colors, dict):
        failures.append(f"strict art-direction: {label}.lettering_colors is required when visual_palette_schema is 1")
        return

    parsed: dict[str, dict[str, str]] = {}
    for role in ("title", "descriptor", "background"):
        value = colors.get(role)
        if not isinstance(value, dict):
            failures.append(f"strict art-direction: {label}.lettering_colors.{role} must name a color and hex")
            continue
        name, hex_value = value.get("name"), value.get("hex")
        if not isinstance(name, str) or not name.strip() or not isinstance(hex_value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_value):
            failures.append(f"strict art-direction: {label}.lettering_colors.{role} needs a color name and six-digit hex")
            continue
        parsed[role] = {"name": name.strip(), "hex": hex_value.upper()}

    rationale = colors.get("rationale")
    if not isinstance(rationale, str) or len(rationale.split()) < 5:
        failures.append(f"strict art-direction: {label}.lettering_colors.rationale must connect the lettering color to the concept")
    if all(role in parsed for role in ("title", "descriptor", "background")):
        for role in ("title", "descriptor"):
            ratio = contrast_ratio(parsed[role]["hex"], parsed["background"]["hex"])
            if ratio < 4.5:
                failures.append(f"strict art-direction: {label} {role} color contrast is {ratio:.2f}:1, below 4.50:1")
        prompts = [owner.get("image_prompt", "")]
        layouts = owner.get("ratio_layouts")
        square = layouts.get("1x1") if isinstance(layouts, dict) else None
        prompts.append(square.get("image_prompt", "") if isinstance(square, dict) else "")
        for ratio_label, prompt in zip(("3:2", "1:1"), prompts):
            prompt_text = prompt.casefold() if isinstance(prompt, str) else ""
            for role, color in parsed.items():
                if color["hex"].casefold() not in prompt_text:
                    failures.append(f"strict art-direction: {label} {ratio_label} prompt must include {role} hex {color['hex']}")


def validate_reference_influence(owner: object, label: str, failures: list[str]) -> str | None:
    if not isinstance(owner, dict):
        return None
    influence = owner.get("reference_influence")
    if not isinstance(influence, dict):
        failures.append(f"strict art-direction: {label}.reference_influence is required when visual_research_schema is 1")
        return None
    source = influence.get("source")
    if not isinstance(source, str) or "font-factory/Style-References/thumbnail-prompt-research-2026-10-20/" not in source:
        failures.append(f"strict art-direction: {label}.reference_influence.source must identify a saved thumbnail research item")
        source = None
    for key in ("mechanism", "fit", "adapted", "left_out"):
        value = influence.get(key)
        if not isinstance(value, str) or len(value.split()) < 4:
            failures.append(f"strict art-direction: {label}.reference_influence.{key} must be a specific note")
    return source


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
    elif "neutral sans-serif" not in prompt.casefold():
        failures.append(
            f"strict art-direction: {label}.image_prompt must specify the descriptor in a neutral sans-serif"
        )


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


def validate_verified_product_facts(owner: object, failures: list[str]) -> None:
    facts = owner.get("verified_product_facts") if isinstance(owner, dict) else None
    if not isinstance(facts, dict):
        failures.append("strict art-direction: verified_product_facts object is required for listing handoff")
        return

    def string_list(value: object, label: str, *, required: bool = False) -> None:
        if (not isinstance(value, list)
                or any(not isinstance(item, str) or not item.strip() for item in value)
                or required and not value):
            suffix = " must be a non-empty string list" if required else " must be a string list"
            failures.append(f"strict art-direction: verified_product_facts.{label}{suffix}")

    string_list(facts.get("source_formats"), "source_formats", required=True)
    styles = facts.get("family_styles")
    if not isinstance(styles, list) or not styles:
        failures.append("strict art-direction: verified_product_facts.family_styles must be a non-empty list")
    else:
        for index, style in enumerate(styles):
            if not isinstance(style, dict):
                failures.append(f"strict art-direction: family_styles[{index}] must be an object")
                continue
            if not isinstance(style.get("style_name"), str) or not style["style_name"].strip():
                failures.append(f"strict art-direction: family_styles[{index}].style_name is required")
            for key in ("weight_class", "width_class"):
                value = style.get(key)
                if not isinstance(value, int) or isinstance(value, bool):
                    failures.append(f"strict art-direction: family_styles[{index}].{key} must be an integer")
            if not isinstance(style.get("italic"), bool):
                failures.append(f"strict art-direction: family_styles[{index}].italic must be a boolean")

    coverage = facts.get("coverage")
    if not isinstance(coverage, dict):
        failures.append("strict art-direction: verified_product_facts.coverage object is required")
    else:
        mapped = coverage.get("mapped_characters")
        if not isinstance(mapped, int) or isinstance(mapped, bool) or mapped < 0:
            failures.append("strict art-direction: coverage.mapped_characters must be a non-negative integer")
        if not isinstance(coverage.get("basic_latin"), str):
            failures.append("strict art-direction: coverage.basic_latin must be a string")
        string_list(coverage.get("unicode_scripts"), "coverage.unicode_scripts")
        string_list(coverage.get("languages"), "coverage.languages")

    for key in ("opentype_features", "verified_alternates",
                "verified_ligatures", "buyer_uses"):
        string_list(facts.get(key), key)


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
    else:
        validate_product_name(root, plan, failures)
    if not isinstance(plan.get("primary_font"), str) or not plan["primary_font"].strip():
        failures.append("strict art-direction: primary_font must identify the source font")
    else:
        family_style_count = source_family_style_count(root, plan, failures)
        if family_style_count is not None:
            plan["_verified_family_style_count"] = family_style_count
    if plan.get("renderer_class") not in RENDERER_CLASSES:
        failures.append("strict art-direction: renderer_class must be elegant, blackletter, sports, or script")
    if plan.get("support_count", 12) != 12:
        failures.append("strict art-direction: support_count is fixed at 12")
    if plan.get("support_renderer", "html") != "html":
        failures.append("strict art-direction: support_renderer must be html")
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
    profile_schema = plan.get("font_profile_schema")
    if profile_schema != 2:
        failures.append("strict art-direction: font_profile_schema must be 2")
    if not isinstance(profile, dict):
        failures.append("strict art-direction: font_profile object is required")
    else:
        for key in ("construction", "personality", "buyer_fit"):
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                failures.append(f"strict art-direction: font_profile.{key} must be non-empty")
        if plan.get("font_profile_schema") == 2:
            for key in ("type_label", "subtext", "product_description"):
                if not isinstance(profile.get(key), str) or not profile[key].strip():
                    failures.append(f"strict art-direction: font_profile.{key} must be non-empty for schema 2")
            subtext = profile.get("subtext")
            if isinstance(subtext, str) and subtext.strip() and not 2 <= len(subtext.split()) <= 6:
                failures.append("strict art-direction: font_profile.subtext must contain 2–6 words")
            features = profile.get("distinctive_features")
            if not isinstance(features, list) or not features or any(not isinstance(value, str) or not value.strip() for value in features):
                failures.append("strict art-direction: font_profile.distinctive_features must be a non-empty string list for schema 2")
    validate_verified_product_facts(plan, failures)
    product_facts = plan.get("verified_product_facts")
    if isinstance(product_facts, dict):
        actual_formats = set(plan.get("_verified_source_formats", []))
        claimed_formats = product_facts.get("source_formats")
        if isinstance(claimed_formats, list):
            normalized_formats = {
                str(value).strip().removeprefix(".").upper()
                for value in claimed_formats if isinstance(value, str)
            }
            if normalized_formats != actual_formats:
                failures.append(
                    "strict art-direction: verified_product_facts.source_formats "
                    "must match the source workspace files"
                )

        actual_styles = {
            (
                str(style.get("style_name", "")).casefold(),
                style.get("weight_class"),
                style.get("width_class"),
                style.get("italic"),
            )
            for style in plan.get("_verified_family_styles", [])
        }
        claimed_styles = product_facts.get("family_styles")
        if isinstance(claimed_styles, list) and all(
            isinstance(style, dict) for style in claimed_styles
        ):
            normalized_styles = {
                (
                    str(style.get("style_name", "")).casefold(),
                    style.get("weight_class"),
                    style.get("width_class"),
                    style.get("italic"),
                )
                for style in claimed_styles
            }
            if normalized_styles != actual_styles:
                failures.append(
                    "strict art-direction: verified_product_facts.family_styles "
                    "must match the source family metadata"
                )

        coverage = product_facts.get("coverage")
        actual_coverage = plan.get("_verified_coverage")
        if isinstance(coverage, dict) and isinstance(actual_coverage, dict):
            for key in ("mapped_characters", "basic_latin"):
                if coverage.get(key) != actual_coverage.get(key):
                    failures.append(
                        f"strict art-direction: verified_product_facts.coverage.{key} "
                        "must match the source font cmap"
                    )

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

    palette_schema = plan.get("visual_palette_schema")
    if palette_schema is not None:
        if palette_schema != 1:
            failures.append("strict art-direction: visual_palette_schema must be 1")
        else:
            validate_lettering_colors(plan.get("thumbnail"), "thumbnail", failures)
            validate_lettering_colors(plan.get("thumbnail_alternate"), "thumbnail_alternate", failures)

    research_schema = plan.get("visual_research_schema")
    if research_schema is not None:
        if research_schema != 1:
            failures.append("strict art-direction: visual_research_schema must be 1")
        else:
            validate_reference_influence(plan.get("thumbnail"), "thumbnail", failures)
            validate_reference_influence(plan.get("thumbnail_alternate"), "thumbnail_alternate", failures)

    thumbnail = plan.get("thumbnail")
    alternate = plan.get("thumbnail_alternate")
    if "japanese_thumbnail" in plan:
        failures.append("strict art-direction: japanese_thumbnail is retired; use thumbnail_alternate for the second direction")
    for owner, label in ((thumbnail, "thumbnail"), (alternate, "thumbnail_alternate")):
        validate_copy(owner, label, plan, failures)
        validate_layouts(owner, label, failures)
        validate_free_space(owner, label, failures)
        validate_image_prompt(owner, f"{label} 3:2", failures)
        layouts = owner.get("ratio_layouts") if isinstance(owner, dict) else None
        square_layout = layouts.get("1x1") if isinstance(layouts, dict) else None
        validate_image_prompt(square_layout, f"{label} 1:1", failures)

    primary_direction = thumbnail.get("visual_direction") if isinstance(thumbnail, dict) else None
    alternate_direction = alternate.get("visual_direction") if isinstance(alternate, dict) else None
    if not isinstance(primary_direction, str) or len(primary_direction.split()) < 5:
        failures.append("strict art-direction: thumbnail.visual_direction must name the primary visual premise")
    if not isinstance(alternate_direction, str) or len(alternate_direction.split()) < 5:
        failures.append("strict art-direction: thumbnail_alternate.visual_direction must name a distinct visual premise")
    elif isinstance(primary_direction, str) and alternate_direction.casefold() == primary_direction.casefold():
        failures.append("strict art-direction: primary and alternate thumbnail visual_direction values must differ")
    if isinstance(primary_direction, str) and isinstance(alternate_direction, str):
        tokens = lambda value: {
            token for token in re.findall(r"[a-z0-9]+", value.casefold())
            if token not in CONCEPT_STOPWORDS and token not in PALETTE_WORDS
        }
        primary_tokens, alternate_tokens = tokens(primary_direction), tokens(alternate_direction)
        smaller = min(len(primary_tokens), len(alternate_tokens))
        overlap = (len(primary_tokens & alternate_tokens) / smaller) if smaller else 1.0
        if overlap > 0.35:
            failures.append("strict art-direction: primary and alternate directions share too much non-palette concept language; change the subject, medium, or structure")
    if isinstance(thumbnail, dict) and isinstance(alternate, dict):
        primary_prompt = str(thumbnail.get("image_prompt", "")).strip().casefold()
        alternate_prompt = str(alternate.get("image_prompt", "")).strip().casefold()
        if primary_prompt and alternate_prompt and primary_prompt == alternate_prompt:
            failures.append("strict art-direction: alternate 3:2 prompt must use a different direction")

    theme_path = direction / "theme.txt"
    if not theme_path.is_file():
        failures.append(f"strict art-direction: missing {theme_path}")
    else:
        theme = theme_path.read_text(encoding="utf-8")
        for heading in (
            "## thumbnail_main_3x2",
            "## thumbnail_main_1x1",
            "## thumbnail_alt_3x2",
            "## thumbnail_alt_1x1",
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
    if "thumbnail_state: generated final thumbnails" not in manifest.casefold():
        failures.append("visual manifest must confirm all four generated final thumbnails")
    if "manual_replacement_required" in manifest.casefold():
        failures.append("visual manifest still requires manual thumbnail replacement")
    required_paths = [
        "3x2/thumbnail_main.png",
        "1x1/thumbnail_main.png",
        "final-thumbnails/thumbnail_main_3x2.png",
        "final-thumbnails/thumbnail_main_1x1.png",
        "final-thumbnails/thumbnail_alt_3x2.png",
        "final-thumbnails/thumbnail_alt_1x1.png",
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

    sizes = {"3x2": (2400, 1600), "1x1": (1600, 1600)}
    check_png(root / "3x2" / "thumbnail_main.png", sizes["3x2"], failures)
    check_png(root / "1x1" / "thumbnail_main.png", sizes["1x1"], failures)
    retired_thumbnail = root / "1x1" / "thumbnail_japanese.png"
    if retired_thumbnail.exists():
        failures.append(f"retired storefront thumbnail reference must be removed: {retired_thumbnail}")
    for ratio in sizes:
        stale = list((root / ratio).glob("promo_*.png"))
        if stale:
            failures.append(f"{ratio}: retired promo PNGs remain: {', '.join(path.name for path in stale)}")

    if (root / "specimens").exists():
        failures.append("retired Agent 27 factual specimen previews must not be present")
    required_assets: list[str] = []

    active_templates = active_html_support_templates(failures)
    support_names: dict[str, set[str]] = {}
    support_count = 0
    for ratio in sizes:
        support_dir = root / "supporting" / ratio
        supports = sorted(support_dir.glob("support-*.png")) if support_dir.is_dir() else []
        if len(supports) != 12:
            failures.append(f"supporting/{ratio}: expected exactly 12 support templates, found {len(supports)}")
        names = {path.stem.split("_", 1)[-1] for path in supports}
        support_names[ratio] = names
        if len(names) != len(supports):
            failures.append(f"supporting/{ratio}: duplicate template names found")
        for path in supports:
            if not SUPPORT_RE.fullmatch(path.name):
                failures.append(f"supporting/{ratio}: unexpected support filename: {path.name}")
            template = path.stem.split("_", 1)[-1]
            if template not in active_templates:
                failures.append(
                    f"supporting/{ratio}: {template} is not an active HTML/CSS catalogue template"
                )
            check_png(path, sizes[ratio], failures)
            required_assets.append(path.relative_to(root).as_posix())
        support_count += len(supports)
    if support_names.get("3x2") != support_names.get("1x1"):
        failures.append("supporting: the selected 3:2 and 1:1 templates must be the same 12 layouts")
    if plan is not None:
        family_style_count = plan.get("_verified_family_style_count")
        if isinstance(family_style_count, int):
            selected_family = support_names.get("3x2", set()) & FAMILY_SHOWCASE_TEMPLATES
            if family_style_count < 2 and selected_family:
                failures.append(
                    "supporting: single-style source fonts must not include family showcases: "
                    + ", ".join(sorted(selected_family))
                )

    for name, ratio in (
        ("thumbnail_main_3x2.png", 1.5),
        ("thumbnail_main_1x1.png", 1.0),
        ("thumbnail_alt_3x2.png", 1.5),
        ("thumbnail_alt_1x1.png", 1.0),
    ):
        check_generated_thumbnail(root / "final-thumbnails" / name, ratio, failures)

    png_count = len(list(root.rglob("*.png")))
    if png_count != 30:
        failures.append(f"handoff: expected exactly 30 PNGs (2 lettering references, 4 generated thumbnails, 24 support renders), found {png_count}")

    validate_handoff_documents(root, required_assets, failures, args.allow_pending_marker)
    if plan is not None and plan.get("render_mode") != "text_placeholder":
        failures.append("unsupported visual plan render_mode")
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(f"[PASS] visual handoff valid: {png_count} PNGs (2 lettering references, 4 generated thumbnails, {support_count} support renders)")
    print("[PASS] supporting templates: 12 matched layouts at 3:2 and 1:1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
