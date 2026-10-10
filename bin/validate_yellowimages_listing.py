#!/usr/bin/env python3
"""Validate YellowImages Creative Store font listing-copy hard gates."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED = [
    "PRODUCT TITLE",
    "PRODUCT DESCRIPTION",
    "CATEGORY",
    "TAGS (30 - YellowImages canonical terms first, comma-separated)",
    "TAG EVIDENCE",
    "RESEARCH NOTES",
]


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[match.end() : end].strip()
    return result


def first_content(value: str) -> str:
    for line in value.splitlines():
        line = line.strip()
        if line and not line.startswith("[") and not line.startswith("<!--"):
            return line
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
        if not parsed.get(heading, "").strip():
            failures.append(f"missing or empty section: {heading}")

    if not first_content(parsed.get("PRODUCT TITLE", "")):
        failures.append("empty product title")
    if "```" in parsed.get("PRODUCT DESCRIPTION", ""):
        failures.append("product description contains a fenced code block")

    tag_heading = "TAGS (30 - YellowImages canonical terms first, comma-separated)"
    tag_line = next(
        (line.strip() for line in parsed.get(tag_heading, "").splitlines() if line.strip() and not line.lstrip().startswith("[")),
        "",
    )
    tags = [tag.strip() for tag in tag_line.split(",") if tag.strip()]
    if len(tags) != 30:
        failures.append(f"tag count is {len(tags)}; expected exactly 30")
    folded = [tag.casefold() for tag in tags]
    if len(folded) != len(set(folded)):
        failures.append("tags contain duplicates")
    for tag in tags:
        if len(tag.split()) < 2:
            failures.append(f"tag is not 2+ words: {tag}")
        if tag.startswith("#"):
            failures.append(f"hashtag is not allowed: {tag}")
    starts: dict[str, int] = {}
    for tag in tags:
        first = tag.casefold().split()[0]
        starts[first] = starts.get(first, 0) + 1
    for first, count in starts.items():
        if count > 3:
            failures.append(f"leading-word repetition exceeds 3: {first} ({count})")

    evidence_rows = [
        line for line in parsed.get("TAG EVIDENCE", "").splitlines()
        if line.strip().startswith("|")
        and not line.strip().startswith("| Tag |")
        and not line.strip().startswith("|---")
    ]
    if len(evidence_rows) < 30:
        failures.append(f"tag evidence rows are {len(evidence_rows)}; expected at least 30")

    if "Creative Store" not in parsed.get("CATEGORY", "") or "Fonts" not in parsed.get("CATEGORY", ""):
        failures.append("category must identify Creative Store > Fonts")
    if "—" in text:
        failures.append("em dash found; replace with a hyphen")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print(f"[PASS] {args.listing}: YellowImages listing-copy hard gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
