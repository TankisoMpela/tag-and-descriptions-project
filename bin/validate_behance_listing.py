#!/usr/bin/env python3
"""Validate the copy/editorial contract for a Behance font project package.

This checks Behance metadata and handoff structure only. It deliberately does
not inspect image pixels, dimensions, files, font packages, licenses, or
whether a project was actually published.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED = [
    "STATUS",
    "PROJECT TITLE",
    "CREATIVE FIELDS",
    "PROJECT DESCRIPTION (PASTE-READY)",
    "COVER IMAGE",
    "PROJECT IMAGE ORDER",
    "PURCHASE CTA",
    "MANUAL PUBLISH STEPS",
    "RESEARCH NOTES",
]


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[heading] = text[start:end].strip()
    return result


def content_lines(value: str) -> list[str]:
    return [
        line.strip()
        for line in value.splitlines()
        if line.strip() and not line.strip().startswith("<!--")
    ]


def project_tags(value: str) -> list[str]:
    tags: list[str] = []
    for line in content_lines(value):
        if line.startswith("-"):
            tag = line[1:].strip()
            if tag and not tag.lower().startswith(("primary:", "secondary:")):
                tags.extend(item.strip().strip("`").strip() for item in tag.split(",") if item.strip())
        elif not line.lower().startswith(("primary:", "secondary:")):
            tags.extend(item.strip().strip("`").strip() for item in line.split(",") if item.strip())
    return tags


def image_blocks(value: str) -> list[str]:
    return re.findall(r"^###\s+.+?$", value, re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    text = args.listing.read_text(encoding="utf-8")
    meta = frontmatter(text)
    parsed = sections(text)
    failures: list[str] = []
    warnings: list[str] = []

    if meta.get("platform", "").casefold() != "behance":
        failures.append("frontmatter platform must be Behance")

    for heading in REQUIRED:
        if heading not in parsed or not parsed[heading].strip():
            failures.append(f"missing or empty section: {heading}")

    project_tag_heading = next(
        (heading for heading in parsed if heading.startswith("PROJECT TAGS (MAX 10")),
        None,
    )
    if project_tag_heading is None or not parsed[project_tag_heading].strip():
        failures.append("missing or empty section: PROJECT TAGS (MAX 10)")

    title = next(iter(content_lines(parsed.get("PROJECT TITLE", ""))), "")
    if not title:
        failures.append("project title is empty")
    if "[" in title or "]" in title:
        failures.append("project title contains a placeholder")

    fields = parsed.get("CREATIVE FIELDS", "")
    if not re.search(r"\bTypography\b", fields, re.I):
        failures.append("Creative Fields must include Typography for a font project")

    description = parsed.get("PROJECT DESCRIPTION (PASTE-READY)", "")
    if not description.strip():
        failures.append("paste-ready project description is empty")

    tags = project_tags(parsed.get(project_tag_heading, "") if project_tag_heading else "")
    if not tags:
        failures.append("project tag list is empty")
    if len(tags) > 10:
        failures.append(f"project tag count is {len(tags)}; maximum is 10")
    lowered = [tag.casefold() for tag in tags]
    if len(lowered) != len(set(lowered)):
        failures.append("project tags contain duplicates")

    image_order = parsed.get("PROJECT IMAGE ORDER", "")
    blocks = image_blocks(image_order)
    if not blocks:
        failures.append("project image order contains no image blocks")
    elif len(blocks) < 3:
        warnings.append(f"only {len(blocks)} images listed; Behance curation may favor 3+")
    elif len(blocks) > 15:
        warnings.append(f"{len(blocks)} images listed; Behance commonly recommends 5-15")

    image_tags = re.findall(r"^-\s*Image tags:\s*(.+?)\s*$", image_order, re.MULTILINE | re.I)
    if len(image_tags) != len(blocks):
        failures.append(
            f"image tag rows ({len(image_tags)}) do not match image blocks ({len(blocks)})"
        )
    for row in image_tags:
        values = [item.strip().strip("`") for item in row.split(",") if item.strip()]
        if len(values) > 10:
            failures.append(f"an image has {len(values)} tags; maximum is 10")

    alt_texts = re.findall(r"^-\s*Alt text:\s*(.+?)\s*$", image_order, re.MULTILINE | re.I)
    if len(alt_texts) != len(blocks):
        failures.append(
            f"alt-text rows ({len(alt_texts)}) do not match image blocks ({len(blocks)})"
        )
    if any(not value.strip() or value.strip().startswith("[") for value in alt_texts):
        failures.append("one or more image alt-text values are empty or placeholders")

    source_names = re.findall(r"^###\s+.*?`([^`]+)`", image_order, re.MULTILINE)
    if len(source_names) != len(blocks):
        failures.append(
            f"image source filenames ({len(source_names)}) do not match image blocks ({len(blocks)})"
        )

    cta = parsed.get("PURCHASE CTA", "")
    if not re.search(r"https?://\S+", cta):
        warnings.append("purchase CTA has no URL; status should say LINK REQUIRED")
    if "LINK REQUIRED" in parsed.get("STATUS", ""):
        warnings.append("listing is intentionally blocked until a canonical product URL is supplied")

    research = parsed.get("RESEARCH NOTES", "")
    if not re.search(r"https?://\S+", research):
        failures.append("research notes contain no source URL")

    if re.search(r"\b(Free Font|Free|Download)\b", "\n".join([title, description]), re.I):
        warnings.append("free/download language appears in customer-facing copy; confirm it is factual")

    for warning in warnings:
        print(f"[WARN] {warning}")
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(
        f"[PASS] {args.listing}: Behance project metadata, tag limits, image metadata, and research checks passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
