#!/usr/bin/env python3
"""Validate DLsite font listing-copy hard gates.

This checks the copy/research contract only. It deliberately does not inspect
font files, packages, images, licenses, or upload readiness.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED = [
    "PRODUCT TITLE",
    "WORK FORMAT",
    "GENRE SELECTION",
    "PRODUCT DESCRIPTION",
    "KEYWORD BLOCK",
    "KEYWORD EVIDENCE",
    "RECOMMENDED PRICING",
    "PROMOTION PLAN",
    "RESEARCH NOTES",
]


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


def evidence_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0].casefold() in {"#", "keyword", "term"}:
            continue
        if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


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

    if not re.search(r"^platform:\s*DLsite\s*$", text, re.MULTILINE | re.IGNORECASE):
        failures.append("frontmatter platform must be DLsite")

    for heading in REQUIRED:
        if not parsed.get(heading, "").strip():
            failures.append(f"missing or empty section: {heading}")

    title = first_content(parsed.get("PRODUCT TITLE"))
    if not title:
        failures.append("empty product title")
    elif len(title) > 100:
        warnings.append(f"product title is {len(title)} characters; verify against DLsite editor limit")

    work_format = first_content(parsed.get("WORK FORMAT"))
    if not work_format:
        failures.append("empty work format")
    elif "ツール/アクセサリ" not in work_format:
        failures.append("work format must contain ツール/アクセサリ")

    genre = first_content(parsed.get("GENRE SELECTION"))
    if not genre:
        failures.append("empty genre selection")
    elif genre.casefold() in {"none", "unknown", "n/a", "no genre"}:
        warnings.append("genre selection is marked as none/unknown; verify against live seller form")

    description = parsed.get("PRODUCT DESCRIPTION", "")
    description_text = " ".join(line.strip() for line in description.splitlines() if line.strip())
    if len(description_text) < 100:
        failures.append(f"product description is {len(description_text)} characters; minimum 100 recommended")

    keywords = parsed.get("KEYWORD BLOCK", "")
    keyword_lines = [
        line.strip()
        for line in keywords.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("|")
    ]
    if len(keyword_lines) < 5:
        failures.append(f"keyword block has {len(keyword_lines)} entries; at least 5 recommended")

    evidence = parsed.get("KEYWORD EVIDENCE", "")
    rows = evidence_rows(evidence)
    if len(rows) < 5:
        failures.append(f"keyword evidence rows are {len(rows)}; at least 5 recommended")

    pricing = parsed.get("RECOMMENDED PRICING", "")
    if not re.search(r"JPY|yen|円", pricing, re.IGNORECASE):
        failures.append("pricing must include JPY/yen values")

    notes = parsed.get("RESEARCH NOTES", "")
    if not re.search(r"firecrawl|serper|exa|webfetch", notes, re.IGNORECASE):
        failures.append("RESEARCH NOTES must identify at least one research provider")

    if not parsed.get("MARKET FIT VERDICT", "").strip():
        warnings.append("MARKET FIT VERDICT section is missing; record FITS or SKIP-AS-PRIMARY")

    if "Link Required" in text or "LINK REQUIRED" in text:
        warnings.append("LINK REQUIRED placeholder found; replace before publishing")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        for warning in warnings:
            print(f"[WARN] {warning}")
        return 1

    for warning in warnings:
        print(f"[WARN] {warning}")
    print(f"[PASS] {args.listing}: DLsite listing-copy hard gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
