#!/usr/bin/env python3
"""Reject Markdown syntax inside a MasterBundles or Cubebrush description body."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADINGS = {
    "masterbundles": "## 3. Product Description",
    "cubebrush": "## PRODUCT DESCRIPTION",
}


def description_lines(path: Path, platform: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = HEADINGS[platform]
    try:
        start = lines.index(heading) + 1
    except ValueError as exc:
        raise ValueError(f"missing description heading: {heading}") from exc

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    body = lines[start:end]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return body


def violations(lines: list[str]) -> list[str]:
    checks = [
        (re.compile(r"^\s{0,3}#{1,6}\s"), "heading marker"),
        (re.compile(r"^\s*[-*+]\s+"), "bullet marker"),
        (re.compile(r"^\s*\d+[.)]\s+"), "numbered-list marker"),
        (re.compile(r"^\s*\|.*\|\s*$"), "table row"),
        (re.compile(r"\[([^\]]+)\]\([^)]*\)"), "Markdown link"),
        (re.compile(r"(```?|\*\*|__|~~)"), "inline Markdown marker"),
        (re.compile(r"<[^>]+>"), "HTML tag"),
    ]
    found: list[str] = []
    for number, line in enumerate(lines, 1):
        for pattern, label in checks:
            if pattern.search(line):
                found.append(f"line {number}: {label}: {line}")
                break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=sorted(HEADINGS), required=True)
    parser.add_argument("--name", required=True, help="exact product/font name that must appear as plain text")
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    try:
        body = description_lines(args.listing, args.platform)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {args.listing}: {exc}", file=sys.stderr)
        return 1

    if not body:
        print(f"[FAIL] {args.listing}: description body is empty", file=sys.stderr)
        return 1

    errors = violations(body)
    if errors:
        print(f"[FAIL] {args.listing}: Markdown syntax found in description body")
        print("\n".join(errors))
        return 1

    text = " ".join(body)
    if not re.search(rf"(?<!\w){re.escape(args.name)}(?!\w)", text):
        print(f"[FAIL] {args.listing}: exact product name is missing from plain-text description: {args.name}")
        return 1

    words = re.findall(r"\b[\w’'-]+\b", text)
    print(f"[PASS] {args.listing}: plain-text description with product name ({len(words)} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
