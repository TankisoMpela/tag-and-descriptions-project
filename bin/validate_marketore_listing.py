#!/usr/bin/env python3
"""Validate Marketore font listing-copy hard gates.

This checks the copy/research contract only. It deliberately does not inspect
font files, packages, images, licenses, or upload readiness.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED = [
    "PRODUCT TITLE",
    "MARKETORE TAXONOMY",
    "PRODUCT DESCRIPTION",
    "TAGS (EXACTLY 10, COMMA-SEPARATED)",
    "TAG EVIDENCE",
    "COMPATIBLE WITH",
    "RECOMMENDED PRICING",
    "RESEARCH NOTES",
]

SUBCATEGORIES = {
    "none",
    "serif",
    "sans serif",
    "script",
    "western",
    "modern",
    "handwriting",
    "display",
    "vintage",
    "slab serif",
    "font-bundles",
    "other fonts",
}


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parsed[match.group(1).strip()] = text[match.end() : end].strip()
    return parsed


def first_content(value: str | None) -> str:
    if not value:
        return ""
    for line in value.splitlines():
        line = line.strip()
        if line and not line.startswith("[") and not line.startswith("<!--"):
            return line
    return ""


def field(body: str, label: str) -> str:
    match = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def sentence(text: str) -> str:
    """Return the first sentence, allowing a normal abbreviation-free opener."""
    match = re.search(r".+?[.!?](?=\s|$)", text)
    return match.group(0).strip() if match else ""


def evidence_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0].casefold() in {"#", "tag"}:
            continue
        if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def vocabulary(root: Path) -> dict[str, str]:
    path = root / "outputs" / "research" / "marketore-tags-vocabulary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(row["tag"]): str(row["tag"]) for row in data}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    text = args.listing.read_text(encoding="utf-8")
    parsed = sections(text)
    failures: list[str] = []
    warnings: list[str] = []

    if not re.search(r"^platform:\s*Marketore\s*$", text, re.MULTILINE | re.IGNORECASE):
        failures.append("frontmatter platform must be Marketore")

    for heading in REQUIRED:
        if not parsed.get(heading, "").strip():
            failures.append(f"missing or empty section: {heading}")

    title = first_content(parsed.get("PRODUCT TITLE"))
    if not title:
        failures.append("empty product title")
    elif len(title) > 100:
        warnings.append(f"product title is {len(title)} characters; no stable live hard limit was observed")

    taxonomy = parsed.get("MARKETORE TAXONOMY", "")
    if not re.search(r"^\s*Main category\s*:\s*Fonts\s*$", taxonomy, re.MULTILINE):
        failures.append("Main category must be exactly Fonts")
    subcategory = field(taxonomy, "Subcategory")
    if not subcategory:
        failures.append("taxonomy is missing Subcategory")
    elif subcategory.casefold() not in SUBCATEGORIES:
        failures.append("Subcategory is not one of the observed Marketore font choices")

    description = parsed.get("PRODUCT DESCRIPTION", "")
    description_text = " ".join(line.strip() for line in description.splitlines() if line.strip())
    if len(description_text) < 50:
        failures.append(f"product description is {len(description_text)} characters; live form minimum is 50")
    opening = sentence(description_text)
    if not opening:
        failures.append("product description must begin with a complete first sentence")
    elif len(opening) > 155:
        failures.append(f"first description sentence is {len(opening)} characters; keep it <=155 for the meta description")
    if "```" in description:
        failures.append("product description contains a fenced code block")

    tag_heading = "TAGS (EXACTLY 10, COMMA-SEPARATED)"
    tag_line = first_content(parsed.get(tag_heading))
    tags = [tag.strip() for tag in tag_line.split(",") if tag.strip()]
    if len(tags) != 10:
        failures.append(f"tag count is {len(tags)}; expected exactly 10")
    folded = [tag.casefold() for tag in tags]
    if len(folded) != len(set(folded)):
        failures.append("tags contain duplicates")

    try:
        vocab = vocabulary(root)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        failures.append(f"could not load Marketore vocabulary: {exc}")
        vocab = {}
    vocab_folded = {tag.casefold(): tag for tag in vocab}
    for tag in tags:
        canonical = vocab_folded.get(tag.casefold())
        if canonical is None:
            failures.append(f"tag is absent from captured Marketore vocabulary: {tag}")
        elif tag != canonical:
            failures.append(f"tag casing/spelling must match vocabulary exactly: {tag} -> {canonical}")

    starts: dict[str, int] = {}
    for tag in tags:
        first = tag.casefold().split()[0] if tag.split() else ""
        starts[first] = starts.get(first, 0) + 1
    for first, count in starts.items():
        if count > 3:
            failures.append(f"leading-word repetition exceeds 3: {first} ({count})")

    rows = evidence_rows(parsed.get("TAG EVIDENCE", ""))
    if len(rows) < 10:
        failures.append(f"tag evidence rows are {len(rows)}; expected at least 10")
    evidence_tags = {row[1].casefold() for row in rows if len(row) > 1}
    for tag in tags:
        if tag.casefold() not in evidence_tags:
            failures.append(f"missing evidence row for selected tag: {tag}")

    pricing = parsed.get("RECOMMENDED PRICING", "")
    for label in ("Personal price", "Commercial price", "Extended Commercial price"):
        if not re.search(rf"^\s*{re.escape(label)}\s*:", pricing, re.MULTILINE | re.IGNORECASE):
            failures.append(f"pricing is missing {label}")

    notes = parsed.get("RESEARCH NOTES", "")
    if not re.search(r"firecrawl", notes, re.IGNORECASE):
        failures.append("RESEARCH NOTES must identify Firecrawl assignment/actual status")
    if not re.search(r"crawl4ai", notes, re.IGNORECASE):
        failures.append("RESEARCH NOTES must identify Crawl4AI assignment/actual status")
    if not re.search(r"assigned|actual provider|fallback", notes, re.IGNORECASE):
        failures.append("RESEARCH NOTES must record assigned/actual provider or fallback")

    if "—" in text:
        failures.append("em dash found; replace with a hyphen")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        for warning in warnings:
            print(f"[WARN] {warning}")
        return 1

    for warning in warnings:
        print(f"[WARN] {warning}")
    print(f"[PASS] {args.listing}: Marketore listing-copy hard gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
