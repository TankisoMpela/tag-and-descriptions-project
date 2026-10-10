#!/usr/bin/env python3
"""Report Pixiv tag reuse across the project's listing packages.

This is a portfolio-rotation warning, not a demand, ranking, or reach score.
It reads only tag lines from Pixiv markdown handoffs and never decides whether
a tag is relevant to a particular product.

Scope accounting
----------------
This report is the instrument for tag rotation, so a partial scan is worse than
no scan: it returns confident percentages over a fraction of the catalogue. The
previous version required a `## POST <n> -` heading and silently skipped every
package that used the older `## PIXIV POST` block, printing
`Packages scanned: 2` against 13 files with no indication that 11 were missing.

Two rules now hold, and neither may be relaxed:

- every `.md` package under the directory is either **scanned** or **listed as
  skipped with a reason** -- silent omission is the bug this guards against;
- if any package is skipped, or any package yields no tags, the report says so
  and exits non-zero, because a reuse percentage computed over part of the
  catalogue is not a rotation signal.

Format
------
Tags are one per line. Older packages in this project also carry them
comma-separated on one line; those are read so historical rotation stays
visible, and flagged so the drift is not mistaken for conformance.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

# Both the current `## POST 1 - STYLE SHOWCASE` heading and the legacy
# `## PIXIV POST` block. The legacy form carries one consolidated tag set per
# package rather than three angles; treating it as an unknown heading is what
# made the report blind to eleven of thirteen packages.
POST_HEADING = re.compile(
    r"^##\s+(?:POST\s+\d+\s*[-—]|PIXIV\s+POST)\s*(.*)$",
    re.IGNORECASE,
)
TAG_HEADING = re.compile(
    r"^(?:\*\*Tags:\*\*|Tags:|### Tags(?:\s*\([^\n]*\))?\s*:?)\s*$",
    re.IGNORECASE,
)

# A tag block ends at a blank line, a heading, or the next labelled field. The
# latter matters: several packages run `Tags:` straight into `Alt text:` and
# `Approved image order:` with no blank line between, and reading through those
# produced tags like "Alt text:" and "Approved image order:".
# A labelled field ends the block whether the value is on its own line
# (`Caption:` then text) or inline on the same line (`Caption: text`).
# Requiring an empty value let `Caption: ...` and `Image source root: ...`
# be read as tags, which inflated a 10-tag post to 12 and looked like a
# limit violation.
FIELD_LINE = re.compile(
    r"^(?:\*\*)?[A-Za-z][A-Za-z0-9 _/-]{1,40}:(?:\*\*)?(?:\s|$)"
)
LIST_LINE = re.compile(r"^(?:[-*+]\s|\d+\.\s)")
LEDGER_NAME = "pixiv-tag-ledger.md"
BANK = Path("outputs/research/pixiv-font-tag-bank.md")


def banked_priority_tags(bank: Path) -> list[str]:
    """Tags from the bank's `Frozen priority bank` table.

    The spec credits this report with warning when a banked candidate has not
    been used recently. It did not, and that is the one warning that drives
    rotation -- reuse shows a tag is over-used, but only this shows a tagable,
    banked route is sitting unused.
    """
    if not bank.is_file():
        return []
    text = bank.read_text(encoding="utf-8", errors="ignore")
    section = re.search(r"(?ms)^##\s+Frozen priority bank\s*$(.*?)(?=^##\s|\Z)", text)
    if not section:
        return []
    tags = []
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Priority", "---:"} or set(cells[0]) <= {"-", ":"}:
            continue
        if cells[0].isdigit() and cells[1] and cells[1] not in {"Tag"}:
            tags.append(cells[1])
    return tags


def parse_tags(path: Path) -> tuple[list[tuple[str, list[str]]], bool]:
    """Return (posts, used_comma_form). One tag per line is the contract."""
    lines = path.read_text(encoding="utf-8").splitlines()
    posts: list[tuple[str, list[str]]] = []
    comma_form = False
    current = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if POST_HEADING.match(line):
            current = line.lstrip("# ").strip()
        elif TAG_HEADING.match(line) and current:
            # Read the block: consecutive non-blank lines, ending at a blank
            # line or a new heading.
            tags: list[str] = []
            j = i + 1
            while j < len(lines):
                raw = lines[j].strip()
                if (
                    not raw
                    or raw.startswith("#")
                    or FIELD_LINE.match(raw)
                    or LIST_LINE.match(raw)
                ):
                    break
                if "," in raw:
                    comma_form = True
                    tags.extend(part.strip().strip("`") for part in raw.split(",") if part.strip())
                else:
                    tags.append(raw.strip("`"))
                j += 1
            if tags:
                posts.append((current, tags))
            i = j
            continue
        i += 1
    return posts, comma_form


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="outputs/pixiv")
    parser.add_argument("--warn-listing-share", type=float, default=0.60)
    args = parser.parse_args()

    root = Path(args.directory)
    if not root.is_dir():
        print(f"[FAIL] not a directory: {root}")
        return 1
    all_files = sorted(p for p in root.glob("*.md") if p.name != LEDGER_NAME)

    file_tags: dict[Path, set[str]] = {}
    occurrences: Counter[str] = Counter()
    listing_occurrences: Counter[str] = Counter()
    package_posts: defaultdict[str, list[str]] = defaultdict(list)
    duplicate_posts: list[tuple[Path, str]] = []
    skipped: list[tuple[Path, str]] = []
    comma_files: list[Path] = []

    for path in all_files:
        posts, comma_form = parse_tags(path)
        if comma_form:
            comma_files.append(path)
        if not posts:
            skipped.append((path, "no post heading, or no tag block"))
            continue
        tags_for_file: set[str] = set()
        for heading, tags in posts:
            seen: set[str] = set()
            for tag in tags:
                occurrences[tag] += 1
                tags_for_file.add(tag)
                package_posts[tag].append(f"{path.name}:{heading}")
                if tag in seen:
                    duplicate_posts.append((path, tag))
                seen.add(tag)
        file_tags[path] = tags_for_file
        for tag in tags_for_file:
            listing_occurrences[tag] += 1

    total_files = len(file_tags)
    scanned = len(all_files) - len(skipped)
    total_posts = sum(len(parse_tags(path)[0]) for path in file_tags)

    print("Pixiv tag circulation report")
    print(f"Packages found: {len(all_files)}; scanned: {scanned}; skipped: {len(skipped)}")
    print(f"Post angles scanned: {total_posts}")
    print("Warning thresholds are portfolio reuse only, not performance claims.")
    print()

    if skipped:
        print("SKIPPED PACKAGES -- the report below does NOT cover these:")
        for path, reason in skipped:
            print(f"- {path.name}: {reason}")
        print()
    if comma_files:
        print("FORMAT DRIFT -- comma-separated tags, contract is one per line:")
        for path in comma_files:
            print(f"- {path.name}")
        print()

    if not file_tags:
        print("[FAIL] no packages with parseable tag sections found.")
        return 1

    print("Tag reuse:")
    for tag, count in sorted(occurrences.items(), key=lambda item: (-item[1], item[0].lower())):
        listings = listing_occurrences[tag]
        share = listings / total_files
        if share >= args.warn_listing_share:
            label = "WARN: high listing share"
        elif listings <= 1:
            label = "RARE: little portfolio use"
        else:
            label = "OK"
        print(f"- {tag}: {count} post uses across {listings}/{total_files} packages ({share:.0%}) — {label}")

    print()
    print("Warnings:")
    warning_count = 0
    for path, tag in duplicate_posts:
        print(f"- duplicate within one post: {path.name} -> {tag}")
        warning_count += 1
    for tag, locations in sorted(package_posts.items()):
        package_names = {location.split(":", 1)[0] for location in locations}
        if len(package_names) == total_files and total_files >= 2:
            print(f"- repeated across every scanned package: {tag}")
            warning_count += 1
        for package in package_names:
            if sum(location.startswith(package + ":") for location in locations) >= 3:
                print(f"- used in all three angles of one package: {package} -> {tag}")
                warning_count += 1

    if warning_count == 0:
        print("- none")

    # Banked but unused: the rotation signal. Reuse above shows a tag is
    # over-used; only this shows a banked, product-fit route sitting idle.
    banked = banked_priority_tags(BANK)
    unused = [tag for tag in banked if tag not in listing_occurrences]
    print()
    print("Banked candidates not used by any package:")
    if not banked:
        print(f"- bank not found or has no priority table: {BANK}")
    elif not unused:
        print("- none; every banked priority tag appears in at least one package")
    else:
        for tag in unused:
            print(f"- {tag}: banked priority tag, 0 packages -- available for rotation")
    print()
    print("Use warnings to create healthy tag rotation only where product fit remains valid.")

    # A partial or drifting scan is not a clean result. Exit non-zero so the
    # caller cannot read a fraction of the catalogue as a healthy portfolio.
    if skipped or comma_files:
        print()
        print(f"[FAIL] {len(skipped)} skipped, {len(comma_files)} non-conforming. "
              "Fix coverage before trusting these percentages.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
