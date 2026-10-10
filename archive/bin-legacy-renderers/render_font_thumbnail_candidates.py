#!/usr/bin/env python3
"""Compatibility renderer for explicitly authored legacy thumbnail variants.

New Agent-27 work must author each image source directly and does not require
thumbnail candidates. This utility must not be used to choose a new font's
creative direction or to generate a batch of interchangeable layouts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from generate_font_visual_handoff import (
    OutlineFont,
    RATIOS,
    render_one,
    render_svg,
    validate_plan,
)


def candidate_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise SystemExit("thumbnail candidate id must contain a letter or number")
    return slug


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    candidates = plan.get("thumbnail_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise SystemExit("optional thumbnail_candidates must contain at least two variants")

    primary_ref, auxiliary_ref, secondary_ref, japanese_ref = validate_plan(plan, plan_path)
    fonts = {
        "primary": OutlineFont(*primary_ref),
        "auxiliary": OutlineFont(*auxiliary_ref),
        "japanese": OutlineFont(*japanese_ref),
    }
    fonts["secondary"] = OutlineFont(*secondary_ref) if secondary_ref else fonts["primary"]

    candidate_ids: set[str] = set()
    args.output.mkdir(parents=True, exist_ok=True)
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise SystemExit(f"thumbnail_candidates[{index - 1}] must be an object")
        raw_id = candidate.get("id", f"candidate-{index}")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise SystemExit(f"thumbnail_candidates[{index - 1}].id must be non-empty")
        candidate_id = candidate_slug(raw_id)
        if candidate_id in candidate_ids:
            raise SystemExit(f"duplicate thumbnail candidate id: {raw_id}")
        candidate_ids.add(candidate_id)
        content = dict(plan["thumbnail"])
        content.update(candidate)
        candidate_dir = args.output / candidate_id
        if candidate_dir.exists() and any(candidate_dir.iterdir()):
            raise SystemExit(f"refusing to overwrite non-empty candidate directory: {candidate_dir}")
        for ratio, width, height in RATIOS:
            svg_dir = candidate_dir / "svg" / ratio
            png_dir = candidate_dir / ratio
            svg_dir.mkdir(parents=True, exist_ok=True)
            png_dir.mkdir(parents=True, exist_ok=True)
            svg_path = svg_dir / "thumbnail_main.svg"
            png_path = png_dir / "thumbnail_main.png"
            svg_path.write_text(render_one(plan, content, fonts, width, height, index, ratio=ratio), encoding="utf-8")
            render_svg(svg_path, png_path, width, height)
        print(
            f"candidate={candidate_id}|3x2={candidate_dir / '3x2/thumbnail_main.png'}|"
            f"1x1={candidate_dir / '1x1/thumbnail_main.png'}"
        )
    print(f"rendered {len(candidates)} thumbnail candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
