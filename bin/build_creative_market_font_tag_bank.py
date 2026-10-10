#!/usr/bin/env python3
"""Derive a Creative Market font tag-pattern bank from existing listing Markdown.

This is intentionally local and deterministic. It reports repeated wording from
the seller's own Creative Market corpus; it is not a demand or search-volume
measurement and it performs no network requests.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


TAGS_HEADING = re.compile(r"^## TAGS[^\n]*\n", re.IGNORECASE | re.MULTILINE)
NEXT_HEADING = re.compile(r"^##\s", re.MULTILINE)


def extract_tags(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = TAGS_HEADING.search(text)
    if not match:
        return []
    start = match.end()
    next_match = NEXT_HEADING.search(text, start)
    block = text[start : next_match.start() if next_match else len(text)]
    # Existing listings put the priority-ordered tag list on the first
    # non-empty line after the heading. Ignore validation prose and backup
    # sections below it.
    block = next((line for line in block.splitlines() if line.strip()), "")
    tags: list[str] = []
    for raw in block.split(","):
        tag = re.sub(r"[`*_\[\]]", "", raw)
        tag = re.sub(r"^\s*[-•]\s*", "", tag)
        tag = re.sub(r"\s+", " ", tag).strip(" .;:\r\n\t")
        if not tag or tag.startswith("(") or tag.startswith("["):
            continue
        if tag.lower().startswith(("validation", "tag evidence", "all ")):
            continue
        # A malformed or placeholder tag is evidence of a bad source listing,
        # not a reusable pattern.
        if len(tag) < 2 or len(tag) > 80 or tag == ";":
            continue
        tags.append(tag)
    return tags


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/creativemarket"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/research/creative-market-font-tag-bank.md"),
    )
    args = parser.parse_args()

    files = sorted(args.input.glob("*.md"))
    counts: Counter[str] = Counter()
    sources: defaultdict[str, list[str]] = defaultdict(list)
    parsed = 0
    unparsed: list[str] = []
    for path in files:
        tags = extract_tags(path)
        if not tags:
            unparsed.append(path.name)
            continue
        parsed += 1
        seen: set[str] = set()
        for tag in tags:
            key = tag.casefold()
            if key in seen:
                continue
            seen.add(key)
            counts[key] += 1
            sources[key].append(path.name)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Creative Market Font Tag Pattern Bank",
        "",
        "This bank is derived mechanically from every Markdown listing in",
        f"`{args.input}`. It contains seller-corpus repetition, not Creative Market",
        "search volume, demand, or a guarantee that a tag is currently available.",
        "Use it for product-fit candidate generation; retain only terms supported",
        "by the current font's facts and classification.",
        "",
        "## Corpus",
        "",
        f"- Markdown files scanned: {len(files)}",
        f"- Listings with a parseable `## TAGS` section: {parsed}",
        f"- Unique normalized tag phrases: {len(counts)}",
        f"- Total de-duplicated tag assignments: {sum(counts.values())}",
        f"- Listings without a parseable tag line: {', '.join(unparsed) if unparsed else 'none'}",
        "",
        "## Repeated tag patterns",
        "",
        "| Corpus count | Tag phrase | Source listings |",
        "|---:|---|---|",
    ]
    for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        if count < 2:
            continue
        lines.append(f"| {count} | {key} | {', '.join(sources[key])} |")

    lines.extend(
        [
            "",
            "## Usage guardrails",
            "",
            "- Corpus repetition is a candidate-strength signal, not search volume.",
            "- Do not copy a tag merely because it appears here; verify product fit",
            "  against the supplied font facts and the seven allowed CM classifications.",
            "- Prefer a balanced set across style/classification, buyer use case,",
            "  format/feature, and audience terms; avoid mechanically repeating one family.",
            "- Keep the final listing at exactly 30 tags, as required by the CM agent.",
        ]
    )
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} from {parsed} listings and {len(counts)} unique phrases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
