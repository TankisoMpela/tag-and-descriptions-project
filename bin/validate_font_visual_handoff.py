#!/usr/bin/env python3
"""Validate the generated dual-ratio font visual handoff contract."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from PIL import Image

# One source of truth. The validator must accept exactly the anchors and scales
# the renderer will honour, and must never keep a second copy that can drift
# from it -- that drift is how `layout_by_ratio` went unvalidated.
from generate_font_text_placeholders import PLACEMENT_ANCHORS, SCALE_SPECS

SCALE_NAMES = tuple(SCALE_SPECS)

# Hard ceiling on a promo phrase. Distinct shapes are wanted, but a phrase that
# grows past this stops being a headline and becomes a sentence.
MAX_PROMO_PHRASE_WORDS = 6



PROMO_RE = re.compile(r"^promo_(\d+)\.png$")
# A tuple, not a set: iterating a set of strings follows hash order, which
# varies per process and made this validator print the same failures in a
# different order on every run.
SPECIMEN_NAMES = ("specimen-alphabet-numerals.png", "specimen-multilingual-glyphs.png")


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


def validate_copy_blocks(owner: dict, label: str, failures: list[str]) -> None:
    if not isinstance(owner, dict):
        failures.append(f"strict art-direction: {label} must be an object")
        return
    blocks = owner.get("copy_blocks")
    by_ratio = owner.get("copy_blocks_by_ratio")
    is_thumbnail = "thumbnail" in label
    minimum = 1 if is_thumbnail else 1
    if blocks is None and isinstance(by_ratio, dict):
        for ratio in ("3x2", "1x1"):
            ratio_blocks = by_ratio.get(ratio)
            if not isinstance(ratio_blocks, list) or len(ratio_blocks) < minimum or any(not isinstance(block, str) or not block.strip() for block in ratio_blocks):
                failures.append(f"strict art-direction: {label}.copy_blocks_by_ratio.{ratio} needs at least {minimum} non-empty displayed text block(s)")
            elif len({block.strip().casefold() for block in ratio_blocks}) != len(ratio_blocks):
                failures.append(f"strict art-direction: {label}.copy_blocks_by_ratio.{ratio} contains duplicate filler blocks")
        return
    if not isinstance(blocks, list) or len(blocks) < minimum or any(not isinstance(block, str) or not block.strip() for block in blocks):
        failures.append(f"strict art-direction: {label}.copy_blocks needs at least {minimum} non-empty displayed text block(s)")
    elif len({block.strip().casefold() for block in blocks}) != len(blocks):
        failures.append(f"strict art-direction: {label}.copy_blocks contains duplicate filler blocks")


def validate_stacked_name(plan: dict, owner: dict, label: str, failures: list[str]) -> None:
    """A stacked thumbnail name must break at word boundaries, not inside a word.

    `Velvet Oath` stacked as `Velvet\\nOath` is the name over two lines.
    `Vel\\nvet` is the same word cut in half, and the renderer honours the
    newline it is given -- the spec forbids it ("Treat each word as indivisible")
    but nothing checked, so a plan shipped `Vel\\nvet` and rendered it as the
    product name. The font name is the ground truth: the words of a stacked
    thumbnail block must be exactly the words of the font name.
    """
    font_name = str(plan.get("font_name", "")).strip()
    blocks = owner.get("copy_blocks")
    if not font_name or not isinstance(blocks, list):
        return
    expected = " ".join(font_name.split())
    for index, block in enumerate(blocks):
        if not isinstance(block, str) or not block.strip():
            continue
        shown = " ".join(block.split())
        if shown.casefold() != expected.casefold():
            failures.append(
                f"strict art-direction: {label}.copy_blocks[{index}] shows {shown!r} "
                f"but the font name is {font_name!r}; a stacked name must break at "
                "word boundaries and must not split a word"
            )


def validate_placement_variety(promos: list, failures: list[str]) -> None:
    """The promo set must use several anchors, not one repeated.

    Requiring placements to exist is not enough. If every promo is authored at
    `center`, every promo renders at the same size in the same place and the
    campaign is a template again -- the failure this check exists to prevent. The
    spec tells the agent to vary placement; nothing verified it, so the rule is
    enforced here.

    The thresholds are deliberately loose: they require variety, they do not
    prescribe which anchors to pick. Scale variety follows from anchor variety,
    because a side anchor shares the measure while a centred one does not, so
    this one rule is what keeps the set from flattening.
    """
    anchors: list[str] = []
    for promo in promos:
        if not isinstance(promo, dict):
            continue
        layouts = promo.get("layout_by_ratio")
        if not isinstance(layouts, dict):
            continue
        for ratio in ("3x2", "1x1"):
            ratio_layout = layouts.get(ratio)
            if not isinstance(ratio_layout, dict):
                continue
            for placement in ratio_layout.get("placements") or []:
                if isinstance(placement, dict) and isinstance(placement.get("anchor"), str):
                    anchors.append(placement["anchor"])
    if len(anchors) < 4:
        return
    counts = Counter(anchors)
    distinct = len(counts)
    needed = max(3, len(anchors) // 4)
    if distinct < needed:
        failures.append(
            f"promo placements use only {distinct} distinct anchor(s) across "
            f"{len(anchors)} placements; at least {needed} are required so the set "
            "does not render as one repeated composition"
        )
    anchor, most = counts.most_common(1)[0]
    if most > len(anchors) / 2:
        failures.append(
            f"promo placements use '{anchor}' for {most} of {len(anchors)} placements; "
            "one anchor must not dominate the set"
        )


def validate_free_space(owner: dict, label: str, failures: list[str]) -> None:
    """Every image must declare what occupies the space its type leaves.

    The renderer writes space-report.md and the spec tells the agent to read it
    and revise any brief that leaves free space unaddressed -- but nothing
    verified it, which is the same "spec says it, no check enforces it" pattern
    that let placements and phrase shapes drift. Twelve of nineteen panels here
    leave more than half the frame free, so this cannot be left to instruction.

    The requirement is a declaration, not a description: name the element that
    occupies the free region, or state explicitly that the emptiness is the
    decision. Either answer is valid; having no answer is not, because that is
    how a panel renders flat. Only presence and substance are checked here --
    whether the prose is any good is the agent's job.
    """
    value = owner.get("free_space")
    if not isinstance(value, str) or not value.strip():
        failures.append(
            f"strict art-direction: {label}.free_space is required; state what occupies "
            "the space the type leaves, or declare the emptiness deliberate"
        )
        return
    words = value.split()
    if len(words) < 6:
        failures.append(
            f"strict art-direction: {label}.free_space is too thin ({len(words)} words) "
            "to say what occupies the frame; name the element or declare the emptiness"
        )


def validate_placements(owner: dict, label: str, failures: list[str]) -> None:
    """Require the authored placements the renderer actually reads.

    The spec requires `layout_by_ratio.<ratio>.placements` for every supporting
    promo, and `generate_font_text_placeholders.placements_for` reads exactly
    that field. Nothing validated it. The validator checked
    `ratio_layouts.<ratio>.layout_variant` instead -- a different field, in a
    different place -- so a plan could pass the gate with no placements at all,
    and the renderer would silently fall back to `default_placements(1)`, which
    is a single `center` anchor. Every promo then centred, which is the one
    outcome the spec names as a template failure.

    Absent placements are a failure, not a warning: the fallback is what turns a
    campaign into a template, and it cannot be seen in the render.
    """
    layouts = owner.get("layout_by_ratio")
    if not isinstance(layouts, dict):
        failures.append(
            f"strict art-direction: {label}.layout_by_ratio is required; without it "
            "every text block falls back to the mechanical centre default"
        )
        return
    for ratio in ("3x2", "1x1"):
        ratio_layout = layouts.get(ratio)
        if not isinstance(ratio_layout, dict):
            failures.append(f"strict art-direction: {label}.layout_by_ratio.{ratio} is required")
            continue
        placements = ratio_layout.get("placements")
        if not isinstance(placements, list) or not placements:
            failures.append(
                f"strict art-direction: {label}.layout_by_ratio.{ratio}.placements "
                "needs at least one authored placement"
            )
            continue
        for index, placement in enumerate(placements):
            if not isinstance(placement, dict):
                failures.append(f"strict art-direction: {label}.layout_by_ratio.{ratio}.placements[{index}] must be an object")
                continue
            if not isinstance(placement.get("block"), int):
                failures.append(f"strict art-direction: {label}.layout_by_ratio.{ratio}.placements[{index}].block must be an integer")
            if placement.get("anchor") not in PLACEMENT_ANCHORS:
                failures.append(
                    f"strict art-direction: {label}.layout_by_ratio.{ratio}.placements[{index}].anchor "
                    f"'{placement.get('anchor')}' is not one of the supported anchors"
                )
            if placement.get("scale") not in SCALE_NAMES:
                failures.append(
                    f"strict art-direction: {label}.layout_by_ratio.{ratio}.placements[{index}].scale "
                    f"'{placement.get('scale')}' is not a supported scale"
                )


def validate_promo_phrases(plan: dict, failures: list[str]) -> None:
    """Check the promo phrase set for shape variety and length.

    The spec sets two rules on the eight promo phrases and neither was enforced:
    at least five must be 1-3 words with at most one over four, and the set must
    not be one grammatical mould repeated. The second is the one that matters --
    a set of eight `Adjective & Adjective` taglines satisfies the word-count rule
    completely and still reads as a single phrase written eight times, which is
    what shipped. Word count is mechanical; shape is approximated here by the
    conjunction form, which is the template that actually recurred.
    """
    promos = plan.get("promos")
    if not isinstance(promos, list) or not promos:
        return
    phrases: list[str] = []
    for index, promo in enumerate(promos):
        if not isinstance(promo, dict):
            continue
        blocks = promo.get("copy_blocks")
        if isinstance(blocks, list) and blocks and isinstance(blocks[0], str):
            phrases.append(" ".join(blocks[0].split()))
    if len(phrases) < 4:
        return

    counts = [len(phrase.split()) for phrase in phrases]
    short = sum(1 for n in counts if 1 <= n <= 3)
    long = sum(1 for n in counts if n > 4)
    needed = max(1, (len(phrases) * 5 + 7) // 8)
    if short < needed:
        failures.append(
            f"promo phrases: only {short} of {len(phrases)} are 1-3 words; "
            f"at least {needed} must be (spec: five of eight)"
        )
    if long > 1:
        failures.append(
            f"promo phrases: {long} exceed four words; at most one may"
        )
    over = [(p, len(p.split())) for p in phrases if len(p.split()) > MAX_PROMO_PHRASE_WORDS]
    if over:
        failures.append(
            "promo phrases: "
            + "; ".join(f"{p!r} has {n} words" for p, n in over)
            + f" -- no promo phrase may exceed {MAX_PROMO_PHRASE_WORDS} words"
        )

    conjunctions = [p for p in phrases if " & " in p or " and " in p.lower()]
    if len(conjunctions) > 1:
        failures.append(
            "promo phrases: the conjunction form appears "
            f"{len(conjunctions)}x ({', '.join(repr(c) for c in conjunctions)}); "
            "at most one promo may use it -- the rest must take a different "
            "grammatical shape so the set is not one template"
        )


# Fields that must differ across the promo set. Each maps to a spec rule that
# previously had no way of being checked:
#
#   dominant_hue   -- "every promo must use a distinctly different dominant hue
#                     family". The plan had no per-promo colour field at all, so
#                     the rule could not be recorded, let alone verified.
#   visual_medium  -- "the paragraph opens with a newly chosen format or medium".
#                     Nothing stopped every panel opening with the same one.
#   texture_device -- the "one device, at most once per set" rule. effect_budget
#                     existed but was never compared, and six of eight promos in
#                     the first set built on the same geometric circle.
#
# Only distinctness is required; no particular value is prescribed. The bar is
# deliberately loose because the point is that a decision was made per panel,
# not that any specific palette or medium was chosen.
VARIETY_FIELDS = ("dominant_hue", "visual_medium", "texture_device")


def validate_directional_variety(promos: list, failures: list[str]) -> None:
    """Require art direction, colour, and texture decisions to differ per promo.

    Anchor, phrase, and job variety were checked; art direction, colour, and
    texture were not, so a set could satisfy every gate while every panel shared
    one hue, one medium, and one device. These are the three dimensions a reader
    actually perceives as sameness.
    """
    for field in VARIETY_FIELDS:
        values = []
        for promo in promos:
            if not isinstance(promo, dict):
                continue
            value = promo.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            values.append(" ".join(value.split()).casefold())
        if not values:
            failures.append(
                f"strict art-direction: promos must each record {field}; none do"
            )
            continue
        missing = len([p for p in promos if isinstance(p, dict)]) - len(values)
        if missing:
            failures.append(
                f"strict art-direction: {missing} promo(s) do not record {field}; "
                "every supporting promo must state its own"
            )
        counts = Counter(values)
        needed = max(3, (len(values) * 3 + 3) // 4)
        if len(counts) < needed:
            worst, n = counts.most_common(1)[0]
            failures.append(
                f"strict art-direction: promos share {field} -- only {len(counts)} "
                f"distinct across {len(values)} (need {needed}); '{worst}' appears {n}x"
            )


def validate_ratio_layouts(
    owner: dict,
    label: str,
    failures: list[str],
    allowed_variants: set[str] | None = None,
) -> None:
    if not isinstance(owner, dict):
        failures.append(f"strict art-direction: {label} must be an object")
        return
    layouts = owner.get("ratio_layouts")
    if not isinstance(layouts, dict):
        failures.append(f"strict art-direction: {label}.ratio_layouts is required")
        return
    signatures: list[tuple[str, str, tuple[str, ...]]] = []
    for ratio in ("3x2", "1x1"):
        layout = layouts.get(ratio)
        if not isinstance(layout, dict):
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio} is required")
            continue
        composition = layout.get("composition")
        focus = layout.get("focus")
        copy_order = layout.get("copy_order")
        if not isinstance(composition, str) or not composition.strip():
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.composition is required")
        if not isinstance(focus, str) or not focus.strip():
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.focus is required")
        if not isinstance(copy_order, list) or len(copy_order) < 1 or any(not isinstance(item, str) or not item.strip() for item in copy_order):
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.copy_order needs at least one field")
            copy_order = []
        if allowed_variants is not None and layout.get("layout_variant") not in allowed_variants:
            failures.append(f"strict art-direction: {label}.ratio_layouts.{ratio}.layout_variant is not supported")
        signatures.append((str(composition), str(focus), tuple(copy_order)))
    if len(signatures) == 2 and signatures[0] == signatures[1]:
        failures.append(f"strict art-direction: {label} uses the same composition in both ratios")


def validate_handoff_documents(
    root: Path,
    counts: dict[str, list[int]],
    failures: list[str],
    allow_pending_marker: bool,
) -> None:
    marker_path = root / "VISUAL-HANDOFF-READY.md"
    if marker_path.is_file():
        try:
            marker = marker_path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"unreadable handoff marker: {marker_path}: {error}")
        else:
            status_match = re.search(r"^\s*validation\s*:\s*(\S+)", marker, re.IGNORECASE | re.MULTILINE)
            status = status_match.group(1).casefold() if status_match else ""
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
        return
    try:
        manifest = manifest_path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"unreadable visual manifest: {manifest_path}: {error}")
        return
    lowered = manifest.casefold()
    if "status" not in lowered or "dimension" not in lowered:
        failures.append("visual manifest must include status and dimension fields")
    required_paths = [
        "3x2/thumbnail_main.png",
        "1x1/thumbnail_main.png",
        "1x1/thumbnail_japanese.png",
    ]
    required_paths.extend(f"3x2/promo_{number}.png" for number in counts.get("3x2", []))
    required_paths.extend(f"1x1/promo_{number}.png" for number in counts.get("1x1", []))
    for required in required_paths:
        if required not in manifest:
            failures.append(f"visual manifest is missing an asset row for {required}")
    for ratio in ("3x2", "1x1"):
        for name in SPECIMEN_NAMES:
            if f"{ratio}/{name}" not in manifest:
                failures.append(f"visual manifest is missing an asset row for {ratio}/{name}")


def validate_art_direction(root: Path, failures: list[str]) -> None:
    direction = root.parent / "visual-direction"
    required = ("art-direction.md", "visual-plan.json", "candidate-review.md")
    for name in required:
        if not (direction / name).is_file():
            failures.append(f"strict art-direction: missing {direction / name}")

    plan_path = direction / "visual-plan.json"
    if not plan_path.is_file():
        return
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"strict art-direction: unreadable plan: {plan_path}: {error}")
        return
    if not isinstance(plan, dict):
        failures.append("strict art-direction: visual plan must be an object")
        return
    # Only the text_placeholder mode is reachable: the renderer rejects any other
    # render_mode, and no plan in the repository uses one. The direct-artwork and
    # OpenPencil validation paths were removed with their producing renderers.

    campaign = plan.get("campaign")
    if not isinstance(campaign, dict):
        failures.append("strict art-direction: visual plan needs a campaign object")
    else:
        for key in ("visual_world", "buyer", "thumbnail_promise"):
            if not isinstance(campaign.get(key), str) or not campaign[key].strip():
                failures.append(f"strict art-direction: campaign.{key} must be non-empty")

    font_profile = plan.get("font_profile")
    if not isinstance(font_profile, dict):
        failures.append("strict art-direction: visual plan needs a font_profile object")
    else:
        for key in ("construction", "personality", "buyer_fit"):
            if not isinstance(font_profile.get(key), str) or not font_profile[key].strip():
                failures.append(f"strict art-direction: font_profile.{key} must be non-empty")

    checks = plan.get("contrast_checks")
    palette = plan.get("palette")
    if not isinstance(checks, list) or len(checks) < 2:
        failures.append("strict art-direction: visual plan needs at least two contrast_checks")
    elif not isinstance(palette, dict):
        failures.append("strict art-direction: contrast checks require a palette")
    else:
        for index, check in enumerate(checks, start=1):
            if not isinstance(check, dict):
                failures.append(f"strict art-direction: contrast_checks[{index}] must be an object")
                continue
            foreground = palette.get(check.get("foreground"))
            background = palette.get(check.get("background"))
            minimum = check.get("minimum")
            if not all(isinstance(value, str) for value in (foreground, background)) or not isinstance(minimum, (int, float)):
                failures.append(f"strict art-direction: contrast_checks[{index}] is incomplete")
                continue
            try:
                ratio = contrast_ratio(foreground, background)
            except (TypeError, ValueError):
                failures.append(f"strict art-direction: contrast_checks[{index}] has invalid colors")
                continue
            if ratio < float(minimum):
                failures.append(f"strict art-direction: contrast_checks[{index}] is {ratio:.2f}:1, below {float(minimum):.2f}:1")

    candidates = plan.get("thumbnail_candidates")
    if candidates is None:
        candidates = []
    elif not isinstance(candidates, list) or len(candidates) < 2:
        failures.append("strict art-direction: optional thumbnail_candidates must contain at least two variants")
        candidates = []
    candidate_ids = [candidate.get("id") for candidate in candidates if isinstance(candidate, dict)]
    if candidates:
        candidate_keys = [value if isinstance(value, str) else repr(value) for value in candidate_ids]
        if len(candidate_keys) != len(set(candidate_keys)):
            failures.append("strict art-direction: thumbnail candidate ids must be unique")
        candidate_variants = [str(candidate.get("layout_variant")) for candidate in candidates if isinstance(candidate, dict)]
        if len(set(candidate_variants)) < 2:
            failures.append("strict art-direction: optional thumbnail candidates need distinct simple layout variants")
        for index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                continue
            if candidate.get("template") != "hero":
                failures.append(f"strict art-direction: thumbnail_candidates[{index}] must use the simple hero template")
            if candidate.get("layout_variant") not in {"left", "center", "band"}:
                failures.append(f"strict art-direction: thumbnail_candidates[{index}] needs layout_variant left, center, or band")
    selected = plan.get("selected_thumbnail_candidate")
    if candidates and (not isinstance(selected, str) or selected not in candidate_ids):
        failures.append("strict art-direction: selected_thumbnail_candidate must match an optional candidate id")
    if not candidates and selected is not None:
        failures.append("strict art-direction: selected_thumbnail_candidate requires thumbnail_candidates")
    validate_copy_blocks(plan.get("thumbnail", {}), "thumbnail", failures)
    thumbnail_owner = plan.get("thumbnail", {})
    validate_ratio_layouts(thumbnail_owner, "thumbnail", failures, {"left", "center", "band"})
    validate_stacked_name(plan, thumbnail_owner, "thumbnail", failures)
    validate_free_space(thumbnail_owner, "thumbnail", failures)
    validate_free_space(plan.get("japanese_thumbnail", {}), "japanese_thumbnail", failures)
    validate_stacked_name(plan, plan.get("japanese_thumbnail", {}), "japanese_thumbnail", failures)
    if candidates:
        selected_candidate = next(
            (candidate for candidate in candidates if isinstance(candidate, dict) and candidate.get("id") == selected),
            None,
        )
        if isinstance(selected_candidate, dict):
            validate_copy_blocks(selected_candidate, "selected thumbnail candidate", failures)
            validate_ratio_layouts(selected_candidate, "selected thumbnail candidate", failures, {"left", "center", "band"})

        candidate_root = direction / "candidates"
        for candidate_id in candidate_ids:
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                failures.append("strict art-direction: every thumbnail candidate needs an id")
                continue
            candidate_dir = candidate_root / re.sub(r"[^A-Za-z0-9]+", "-", candidate_id).strip("-").lower()
            for ratio, size in (("3x2", (2400, 1600)), ("1x1", (1600, 1600))):
                check_png(candidate_dir / ratio / "thumbnail_main.png", size, failures)
                source = candidate_dir / "svg" / ratio / "thumbnail_main.svg"
                if not source.is_file():
                    failures.append(f"strict art-direction: missing candidate source: {source}")
        for candidate in candidates:
            if isinstance(candidate, dict):
                validate_copy_blocks(candidate, f"thumbnail candidate {candidate.get('id', '<unknown>')}", failures)
                validate_ratio_layouts(candidate, f"thumbnail candidate {candidate.get('id', '<unknown>')}", failures, {"left", "center", "band"})

    validate_promo_phrases(plan, failures)
    validate_placement_variety(plan.get("promos") or [], failures)
    validate_directional_variety(plan.get("promos") or [], failures)

    promos = plan.get("promos")
    if not isinstance(promos, list):
        failures.append("strict art-direction: promos must be a list")
        promos = []
    jobs: set[str] = set()
    contexts: list[str] = []
    specimen_count = 0
    functional_contexts = {"poster", "label", "package", "packaging", "title card", "badge", "brand lockup", "sign", "social graphic"}
    allowed_promo_templates = {"poster", "use-case", "feature-grid", "contrast"}
    for index, promo in enumerate(promos, start=1):
        if not isinstance(promo, dict):
            failures.append(f"strict art-direction: promos[{index}] must be an object")
            continue
        for key in ("primary_job", "context_type", "copy_provenance", "effect_budget"):
            if not isinstance(promo.get(key), str) or not promo[key].strip():
                failures.append(f"strict art-direction: promos[{index}].{key} is required")
        if promo.get("template") not in allowed_promo_templates:
            failures.append(f"strict art-direction: promos[{index}] uses a disallowed or ambitious template")
        validate_copy_blocks(promo, f"promos[{index}]", failures)
        allowed_variants = {
            "poster": {"wide", "tall"},
            "use-case": {"wide", "tall"},
            "feature-grid": {"rows", "column"},
            "contrast": {"stacked", "split"},
        }.get(str(promo.get("template")))
        validate_ratio_layouts(promo, f"promos[{index}]", failures, allowed_variants)
        validate_placements(promo, f"promos[{index}]", failures)
        validate_free_space(promo, f"promos[{index}]", failures)
        job = str(promo.get("primary_job", "")).strip().lower()
        context = str(promo.get("context_type", "")).strip().lower()
        if job:
            jobs.add(job)
        if context and "specimen" in context:
            specimen_count += 1
        elif context:
            contexts.append(context)
        if context in functional_contexts:
            functional_contexts.discard(context)
    if len(jobs) < 4:
        failures.append("strict art-direction: supporting promos need at least four distinct primary jobs")
    if len(set(contexts)) < 2:
        failures.append("strict art-direction: supporting promos need at least two concrete end-use contexts")
    if specimen_count > 2:
        failures.append("strict art-direction: no more than two promos may be specimen-only")
    if len(set(contexts).intersection({"poster", "label", "package", "packaging", "title card", "badge", "brand lockup", "sign", "social graphic"})) < 1:
        failures.append("strict art-direction: at least one promo must name a functional end-use context")

    placeholders = (
        "Final Name",
        "SHORT SUPPORTED STYLE",
        "A SHORT PHRASE",
        "A BUYER USE CASE",
        "A factual supporting line",
        "A CLEAR TITLE",
        "A straightforward buyer-facing application",
        "approved product description",
    )
    serialized = json.dumps(plan, ensure_ascii=False)
    for placeholder in placeholders:
        if placeholder in serialized:
            failures.append(f"strict art-direction: replace plan placeholder copy: {placeholder}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared_visuals", type=Path)
    parser.add_argument("--min-promos", type=int, default=4)
    parser.add_argument("--max-promos", type=int, default=8)
    parser.add_argument(
        "--strict-art-direction",
        action="store_true",
        help="also validate the Agent 27 campaign plan, optional thumbnail variants, and contextual promo roles",
    )
    parser.add_argument(
        "--allow-pending-marker",
        action="store_true",
        help="allow validation: pending while assembling a handoff; final validation requires PASS",
    )
    args = parser.parse_args()

    root = args.prepared_visuals
    failures: list[str] = []
    if not root.is_dir():
        print(f"[FAIL] missing handoff directory: {root}")
        return 1
    if not (root / "VISUAL-HANDOFF-READY.md").is_file():
        failures.append(f"missing handoff marker: {root / 'VISUAL-HANDOFF-READY.md'}")
    if not (root / "visual-handoff-manifest.md").is_file():
        failures.append(f"missing visual manifest: {root / 'visual-handoff-manifest.md'}")
    if args.strict_art_direction:
        validate_art_direction(root, failures)
    counts: dict[str, list[int]] = {}
    for ratio, size in (("3x2", (2400, 1600)), ("1x1", (1600, 1600))):
        directory = root / ratio
        check_png(directory / "thumbnail_main.png", size, failures)
        if ratio == "1x1":
            check_png(directory / "thumbnail_japanese.png", size, failures)
        promo_numbers = sorted(
            int(match.group(1))
            for path in directory.glob("promo_*.png")
            if (match := PROMO_RE.match(path.name))
        )
        counts[ratio] = promo_numbers
        if not args.min_promos <= len(promo_numbers) <= args.max_promos:
            failures.append(f"{ratio}: expected {args.min_promos}-{args.max_promos} promos, found {len(promo_numbers)}")
        if promo_numbers != list(range(1, len(promo_numbers) + 1)):
            failures.append(f"{ratio}: promo numbering must be contiguous from promo_1.png")
        for number in promo_numbers:
            check_png(directory / f"promo_{number}.png", size, failures)

    if counts["3x2"] != counts["1x1"]:
        failures.append(f"3x2 and 1x1 promo sets differ: {counts['3x2']} versus {counts['1x1']}")

    validate_handoff_documents(root, counts, failures, args.allow_pending_marker)

    for ratio, size in (("3x2", (2400, 1600)), ("1x1", (1600, 1600))):
        specimen_dir = root / "specimens" / ratio
        for name in SPECIMEN_NAMES:
            check_png(specimen_dir / name, size, failures)

    plan_mode = None
    plan_path = root.parent / "visual-direction" / "visual-plan.json"
    if plan_path.is_file():
        try:
            plan_mode = json.loads(plan_path.read_text(encoding="utf-8")).get("render_mode")
        except (OSError, json.JSONDecodeError):
            pass

    if plan_mode in {"text_placeholder", "placeholder", "white_text", None}:
        # The active Agent-27 handoff is intentionally a mechanical PNG/text
        # placeholder handoff. It carries no creative SVG source; final artwork
        # is supplied later by the user. A missing render_mode is accepted for
        # older PNG-only handoffs, and white_text for plans the renderer
        # accepted under that alias.
        pass
    else:
        svg_dir = root / "svg"
        if not svg_dir.is_dir():
            failures.append(f"missing SVG source directory: {svg_dir}")
        else:
            expected_sources = ["thumbnail_main.svg"] + [f"promo_{n}.svg" for n in counts["3x2"]]
            for ratio in ("3x2", "1x1"):
                names = expected_sources + (["thumbnail_japanese.svg"] if ratio == "1x1" else [])
                for name in names:
                    source = svg_dir / ratio / name
                    if not source.is_file():
                        failures.append(f"missing SVG source: {source}")
                        continue
                    try:
                        ET.parse(source)
                    except (ET.ParseError, OSError) as error:
                        failures.append(f"unreadable SVG source: {source}: {error}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    total = 3 + len(counts["3x2"]) * 2 + len(SPECIMEN_NAMES) * 2
    if plan_mode in {"text_placeholder", "placeholder", "white_text", None}:
        source_label = "PNG/text placeholder handoff"
    else:
        source_label = "SVG sources"
    print(f"[PASS] visual handoff valid: {total} PNGs plus {source_label}")
    print(f"[PASS] promos: {len(counts['3x2'])} in each ratio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
