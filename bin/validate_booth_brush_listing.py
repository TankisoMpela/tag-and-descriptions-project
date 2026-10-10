#!/usr/bin/env python3
"""Validate the copy/research contract for a BOOTH brush listing."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}[ \t]*$\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()
    text = args.listing.read_text(encoding="utf-8")
    failures: list[str] = []

    if not re.search(r"^platform:\s*BOOTH BRUSH\s*$", text, re.MULTILINE):
        failures.append("frontmatter platform must be BOOTH BRUSH")
    if not re.search(r"^type:\s*(?:Procreate|Photoshop) Brush\s*$", text, re.MULTILINE):
        failures.append("frontmatter type must be Procreate Brush or Photoshop Brush")

    title = section(text, "PRODUCT TITLE")
    if not title:
        failures.append("missing PRODUCT TITLE")
    elif len(title.splitlines()[0]) > 100:
        failures.append("product title exceeds 100 characters")

    description = section(text, "PRODUCT DESCRIPTION (PASTE-READY PLAIN TEXT)")
    if not description:
        failures.append("missing product description")
    for line in description.splitlines():
        if re.match(r"^\s*(#|[-*+]\s)", line) or "**" in line or "`" in line:
            failures.append("BOOTH description body must be plain text")
            break

    tag_heading = re.search(r"^## BOOTH TAGS [^\n]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    tags = []
    if not tag_heading:
        failures.append("missing BOOTH TAGS section")
    else:
        tags = [line.strip() for line in tag_heading.group(1).splitlines() if line.strip()]
        if len(tags) != 30:
            failures.append(f"BOOTH brush tag count is {len(tags)}; expected exactly 30")
        if len(tags) != len(set(tags)):
            failures.append("BOOTH brush tags contain duplicates")
        if any("," in tag for tag in tags):
            failures.append("BOOTH brush tags must be one tag per line, not comma-separated")

    evidence = section(text, "TAG EVIDENCE")
    evidence_rows = [line for line in evidence.splitlines() if re.match(r"^\|\s*\d+\s*\|", line)]
    if len(evidence_rows) < len(tags):
        failures.append("TAG EVIDENCE must contain one row for every selected tag")

    if "visuals/main/" not in text or "visuals/squares/" not in text:
        failures.append("IMAGE HANDOFF must identify main and square delivery folders")
    if "visual-source-manifest.md" not in text:
        failures.append("IMAGE HANDOFF must reference visual-source-manifest.md")
    if "package/README.txt" not in text or "-booth.zip" not in text:
        failures.append("IMAGE HANDOFF must identify the Japanese README and BOOTH ZIP")
    if "https://fontfairy.booth.pm/" not in text:
        failures.append("listing must record the FontFairy BOOTH store URL")

    research = section(text, "RESEARCH NOTES")
    for provider in ("Firecrawl", "Crawl4AI", "webfetch"):
        if provider.casefold() not in research.casefold():
            failures.append(f"RESEARCH NOTES missing provider/fallback record: {provider}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print(f"[PASS] {args.listing}: BOOTH brush copy, exactly 30 tags, evidence, handoff, and provider checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
