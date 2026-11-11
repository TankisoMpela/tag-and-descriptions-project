#!/usr/bin/env python3
"""Validate Creative Market listing-copy hard gates and the font category when present.

This validator intentionally checks copy structure, SEO constraints, and the
user-requested primary font classification only. Package, media, pricing,
license, and upload checks belong to the preparation or seller-operation
workflows.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from marketplace_description_rules import validate_marketplace_description


REQUIRED = [
    "PRODUCT TITLE",
    "PRODUCT DESCRIPTION",
    "META TITLE",
    "META DESCRIPTION",
    "CLASSIFICATION",
    "RESEARCH NOTES",
]

BANNED_TAGS = {
    "vector",
    "illustration",
    "clipart",
    "png",
    "svg",
    "digital art",
    "drawing",
    "graphic",
    "design",
    "artwork",
    "file",
    "download",
    "high quality",
    "premium",
    "professional",
    "font",
    "typeface",
    "cool",
    "best",
    "top",
    "awesome",
    "perfect",
    "beautiful",
    "unique",
    "bundle",
    "pack",
    "set",
    "quality",
}

ALLOWED_CLASSIFICATIONS = {
    "blackletter",
    "handwritten",
    "sans serif",
    "script",
    "serif",
    "slab serif",
    "symbols",
}

MAX_TAGS = 20

TECHNICAL_TAG_REVIEW_PATTERNS = (
    (re.compile(r"\b\d+\s+(?:mapped\s+)?characters?\b", re.IGNORECASE), "raw character count"),
    (re.compile(r"\b(?:gsub|gpos)\b", re.IGNORECASE), "OpenType table name"),
    (re.compile(r"\blegacy\s+kern(?:ing)?\b", re.IGNORECASE), "kerning implementation detail"),
    (re.compile(r"\b(?:single|regular)\s+(?:font\s+)?(?:style|weight)\b", re.IGNORECASE), "style or weight metadata"),
    (re.compile(r"\b(?:basic\s+latin|latin\s+extended(?:\s*-?\s*a)?)\b", re.IGNORECASE), "Unicode range label"),
    (re.compile(r"\bweb\s?fonts?\b", re.IGNORECASE), "web font capability or license claim"),
)

FILE_FORMAT_TAG = re.compile(r"^(?:otf|ttf|woff2?|opentype|truetype)(?:\s+(?:font|format))?$", re.IGNORECASE)


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[heading] = text[start:end].strip()
    return result


def first_content(value: str | None) -> str:
    if not value:
        return ""
    for line in value.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("[") and not stripped.startswith("<!--"):
            return stripped
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    text = args.listing.read_text(encoding="utf-8")
    parsed = sections(text)
    failures: list[str] = []

    for heading in REQUIRED:
        if heading not in parsed or not parsed[heading].strip():
            failures.append(f"missing or empty section: {heading}")

    title = first_content(parsed.get("PRODUCT TITLE"))
    meta_title = first_content(parsed.get("META TITLE"))
    meta_description = first_content(parsed.get("META DESCRIPTION"))
    if title and len(title) > 36:
        failures.append(f"product title is {len(title)} characters; maximum is 36")
    if meta_title and len(meta_title) > 55:
        failures.append(f"meta title is {len(meta_title)} characters; maximum is 55")
    if meta_description and len(meta_description) > 155:
        failures.append(f"meta description is {len(meta_description)} characters; maximum is 155")

    failures.extend(validate_marketplace_description(parsed.get("PRODUCT DESCRIPTION", "")))

    classification = parsed.get("CLASSIFICATION", "").strip()
    if classification:
        first_line = first_content(classification).strip().casefold()
        category_match = re.search(
            r"classification\s*>\s*(blackletter|handwritten|sans serif|script|serif|slab serif|symbols)",
            classification,
            re.IGNORECASE,
        )
        if first_line not in ALLOWED_CLASSIFICATIONS and not category_match:
            failures.append(
                "classification must be exactly one of: Blackletter, Handwritten, Sans Serif, Script, Serif, Slab Serif, Symbols"
            )

    tags: list[str] = []
    if "## TAGS" not in text:
        failures.append("missing TAGS section")
    else:
        tag_heading = next((line for line in text.splitlines() if line.startswith("## TAGS")), "")
        heading_index = text.splitlines().index(tag_heading)
        lines = text.splitlines()
        tag_line = ""
        for line in lines[heading_index + 1 :]:
            stripped = line.strip()
            if stripped.startswith("## "):
                break
            if stripped and not stripped.lower().startswith("validation") and not stripped.startswith("["):
                tag_line = stripped
                break
        tags = [item.strip() for item in tag_line.split(",") if item.strip()]
        if not tags:
            failures.append("TAGS section must contain at least one tag")
        if len(tags) > MAX_TAGS:
            failures.append(f"TAGS section has {len(tags)} tags; maximum is {MAX_TAGS}")
        lowered = [item.casefold() for item in tags]
        if len(lowered) != len(set(lowered)):
            failures.append("tags contain duplicates")
        for tag in tags:
            if len(tag.split()) < 2:
                failures.append(f"tag is not 2+ words: {tag}")
            if tag.casefold() in BANNED_TAGS or FILE_FORMAT_TAG.fullmatch(tag):
                failures.append(f"banned mechanical tag: {tag}")

    tag_reviews: list[tuple[str, str]] = []
    for tag in tags:
        for pattern, reason in TECHNICAL_TAG_REVIEW_PATTERNS:
            if pattern.search(tag):
                tag_reviews.append((tag, reason))
                break

    if "—" in text:
        failures.append("em dash found; replace with a hyphen")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    for tag, reason in tag_reviews:
        print(f"[REVIEW] tag may be technical metadata ({reason}): {tag}")

    print(f"[PASS] {args.listing}: Creative Market listing-copy hard gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
