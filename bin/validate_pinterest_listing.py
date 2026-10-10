#!/usr/bin/env python3
"""Validate the copy and handoff contract for a four-Pin Pinterest package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


PIN_HEADINGS = {
    1: "## PIN 1:",
    2: "## PIN 2:",
    3: "## PIN 3:",
    4: "## PIN 4:",
}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def value_after(label: str, block: str) -> str:
    match = re.search(rf"^-\s*{re.escape(label)}\s*:\s*(.+)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def clean(value: str) -> str:
    return value.strip().strip("`").strip()


def topic_count(value: str) -> int:
    value = clean(value)
    if not value or value in {"...", "[topics]"}:
        return 0
    return len([item for item in re.split(r",|\|", value) if item.strip()])


def product_url(value: str) -> bool:
    parsed = urlparse(clean(value))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.netloc.casefold() not in {"creativemarket.com", "www.creativemarket.com"}:
        return False
    segments = [segment for segment in parsed.path.split("/") if segment]
    return len(segments) >= 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    text = args.listing.read_text(encoding="utf-8")
    meta = frontmatter(text)
    failures: list[str] = []
    warnings: list[str] = []

    if meta.get("platform", "").casefold() != "pinterest":
        failures.append("frontmatter platform must be Pinterest")
    if meta.get("pin_count") != "4":
        failures.append("frontmatter pin_count must be 4")

    status = meta.get("status", "")
    shared_url = clean(meta.get("destination_url", ""))
    blocked = status.casefold().startswith("blocked")
    if blocked:
        if "PRODUCT URL REQUIRED" not in status:
            failures.append("blocked status must explain that the product URL is required")
        if shared_url not in {"LINK REQUIRED", "[exact product URL or LINK REQUIRED]"}:
            warnings.append("blocked package has a destination_url other than LINK REQUIRED")
    elif not product_url(shared_url):
        failures.append("READY package needs an exact Creative Market product URL")

    sections = re.findall(r"^## PIN ([1-4]):.*$", text, re.MULTILINE)
    if len(sections) != 4 or sorted(sections) != ["1", "2", "3", "4"]:
        failures.append("listing must contain exactly four PIN 1–4 sections")

    pins: list[dict[str, str]] = []
    for number in range(1, 5):
        heading = PIN_HEADINGS[number]
        match = re.search(
            rf"^{re.escape(heading)}.*?$(.*?)(?=^## PIN [1-4]:|^## [A-Z]|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        if not match:
            failures.append(f"missing section for PIN {number}")
            continue
        block = match.group(1)
        image = clean(value_after("Image", block))
        title = clean(value_after("Title (max 100 chars)", block))
        description = clean(value_after("Description (max 800 chars)", block))
        alt = clean(value_after("Alt text (max 500 chars)", block))
        destination = clean(value_after("Destination link", block))
        topics = value_after("Related topics (max 10)", block)

        expected = f"pinterest_{number}.png"
        if expected not in image:
            failures.append(f"PIN {number} must use {expected}")
        if not title or title in {"...", "[title]"}:
            failures.append(f"PIN {number} has no usable title")
        elif len(title) > 100:
            failures.append(f"PIN {number} title is {len(title)} characters; maximum is 100")
        if not description or description in {"...", "[description]"}:
            failures.append(f"PIN {number} has no usable description")
        elif len(description) > 800:
            failures.append(f"PIN {number} description is {len(description)} characters; maximum is 800")
        if not alt or alt in {"...", "[alt text]"}:
            failures.append(f"PIN {number} has no usable alt text")
        elif len(alt) > 500:
            failures.append(f"PIN {number} alt text is {len(alt)} characters; maximum is 500")
        if not blocked and destination != shared_url:
            failures.append(f"PIN {number} destination does not match the shared product URL")
        if topic_count(topics) > 10:
            failures.append(f"PIN {number} has more than 10 related topics")
        pins.append({"title": title, "description": description, "destination": destination})

    titles = [pin["title"].casefold() for pin in pins if pin["title"]]
    descriptions = [pin["description"].casefold() for pin in pins if pin["description"]]
    if len(titles) != len(set(titles)):
        failures.append("Pin titles must be distinct")
    if len(descriptions) != len(set(descriptions)):
        failures.append("Pin descriptions must be distinct")

    if "https://help.pinterest.com/" not in text and "https://business.pinterest.com/" not in text:
        failures.append("research notes must include an official Pinterest source URL")
    if "LINK REQUIRED" in text and not blocked:
        failures.append("LINK REQUIRED may not appear in a READY package")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        for warning in warnings:
            print(f"[WARN] {warning}")
        return 1

    for warning in warnings:
        print(f"[WARN] {warning}")
    print(f"[PASS] {args.listing}: four-Pin Pinterest metadata, link, image, and research checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
