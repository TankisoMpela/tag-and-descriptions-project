#!/usr/bin/env python3
"""Validate the copy-level contract for an X font single-post handoff."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
POST_RE = re.compile(r"^##\s+POST\s+(\d{2}):\s*(.+?)\s*$", re.M)

# X weighted char counting: CJK/CJK-compatible fullwidth count as 2.
CJK_RANGES = [
    (0x1100, 0x115F),   # Hangul Jamo
    (0x2E80, 0xA4CF),   # CJK Radicals, Kangxi, etc.
    (0xAC00, 0xD7A3),   # Hangul Syllables
    (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
    (0xFE30, 0xFE4F),   # CJK Compatibility Forms
    (0xFF01, 0xFF60),   # Fullwidth Forms
    (0xFFE0, 0xFFE6),   # Fullwidth Signs
    (0x20000, 0x2FFFD), # CJK Extension B+
    (0x30000, 0x3FFFD), # CJK Extension G
]


def x_weighted_length(text: str) -> int:
    """Compute X/Twitter weighted character count (CJK=2, others=1)."""
    count = 0
    for ch in text:
        cp = ord(ch)
        is_cjk = any(lo <= cp <= hi for lo, hi in CJK_RANGES)
        count += 2 if is_cjk else 1
    return count


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.search(text)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def post_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(POST_RE.finditer(text))
    blocks: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), match.group(2), text[match.end() : end]))
    return blocks


def field(block: str, label: str) -> str:
    pattern = re.compile(rf"^-\s*{re.escape(label)}:\s*(.*?)\s*$", re.M | re.I)
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    text = args.listing.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    failures: list[str] = []
    warnings: list[str] = []

    if meta.get("platform", "").casefold() != "x":
        failures.append("frontmatter platform must be X")
    if meta.get("type", "").casefold() != "font":
        failures.append("frontmatter type must be Font")
    if meta.get("post_count") != "1":
        failures.append("frontmatter post_count must be 1")
    if not meta.get("product") or meta["product"].startswith("["):
        failures.append("frontmatter product is missing")
    if not meta.get("slug") or meta["slug"].startswith("["):
        failures.append("frontmatter slug is missing")

    destination = meta.get("destination_url", "")
    if destination != "LINK REQUIRED":
        if not re.fullmatch(r"https?://[^\s]+booth\.pm/[^\s]+", destination, re.I):
            failures.append("destination_url must be an exact product-level BOOTH URL or LINK REQUIRED")
        if re.fullmatch(r"https?://[^\s]+booth\.pm/?(?:ja)?/?", destination, re.I):
            failures.append("destination_url must not be only a BOOTH shop root")
    elif "BLOCKED" not in meta.get("status", ""):
        failures.append("LINK REQUIRED destination must use a BLOCKED status")

    blocks = post_blocks(text)
    if len(blocks) != 1:
        failures.append(f"expected exactly 1 POST block, found {len(blocks)}")

    if blocks:
        number, intent, block = blocks[0]
        if number != "01":
            failures.append("POST block must be numbered 01")
        copy = field(block, "Copy (paste-ready, single post)")
        media = field(block, "Media")
        placement = field(block, "Link placement").casefold()
        block_destination = field(block, "Destination link")
        hashtags = re.findall(r"(?<!\w)#\S+", field(block, "Hashtags"))

        if not intent.strip() or intent.startswith("["):
            failures.append("POST has no intent")
        if not copy or copy.startswith("["):
            failures.append("POST has no paste-ready copy")
        if not media:
            failures.append("POST has no Media field")
        elif media == "MEDIA REQUIRED":
            warnings.append("POST still needs an approved image filename")
        if placement not in {"main-post-link", "first-reply-link"}:
            failures.append("POST has an invalid link placement")
        if len(hashtags) > 2:
            failures.append(f"POST has {len(hashtags)} hashtags; maximum is 2")
        if not block_destination:
            failures.append("POST has no Destination link field")
        elif destination != "LINK REQUIRED" and block_destination != destination:
            failures.append("POST destination does not match frontmatter destination_url")
        elif destination == "LINK REQUIRED" and block_destination != "LINK REQUIRED":
            failures.append("POST must keep LINK REQUIRED until a product URL exists")

        if "#フリーフォント" in block or "#freefont" in block.casefold():
            warnings.append("POST uses free-font language; confirm the product is genuinely free")
        if re.search(r"\b(todo|tbd|lorem ipsum)\b|\[(?:copy|insert|replace|unknown)\]", block, re.I):
            failures.append("POST contains an unresolved placeholder")

        # Weighted character count check
        # Build the full paste-ready text (copy + hashtags + URL)
        hashtag_line = ""
        if hashtags:
            hashtag_line = " " + " ".join(hashtags)
        copy_with_hashtags = copy + hashtag_line
        # Count the copy portion (everything except the Destination link line itself)
        weighted = x_weighted_length(copy_with_hashtags)
        url_weight = 23  # t.co wrapping
        total = weighted + url_weight
        char_limit = 280
        if total > char_limit:
            failures.append(
                f"weighted character count exceeds limit: {total} > {char_limit} "
                f"(copy={weighted}, URL={url_weight}). Trim the post copy."
            )

    if "No upload or publication claim" not in text and "PUBLISH RESPONSE RECORDED" not in meta.get("publish_mode", ""):
        failures.append("package must state No upload or publication claim")

    for warning in warnings:
        print(f"[WARN] {warning}")
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(
        f"[PASS] {args.listing}: X single-post structure, character limit, hashtag limit, BOOTH-link, and research checks passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
