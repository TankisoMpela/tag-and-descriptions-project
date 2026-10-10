#!/usr/bin/env python3
"""Index the existing Creative Fabrica listings without reading them.

The Creative Fabrica agent is told to read "the existing Creative Fabrica
ledger/listings" before choosing tags, so a new listing does not repeat the same
vocabulary as the ones already published. That directory is ~247 KB across 14
files, and the only questions actually being asked of it are:

    - which products do we already have?              -> --registry
    - which tags are already saturated across them?   -> --tag-usage

This tool answers both from the same files and prints a few hundred bytes.

Usage:
  python3 bin/creative_fabrica_owned.py
  python3 bin/creative_fabrica_owned.py --tag-usage
  python3 bin/creative_fabrica_owned.py --json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path("outputs/creative-fabrica")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
# ## TAGS (40 - Creative Fabrica research package, comma-separated)
TAGS_RE = re.compile(r"^##\s+TAGS\b[^\n]*\n\s*\n?(.*?)(?=\n## |\Z)", re.M | re.S)
# Heading variants: `## PRODUCT TITLE`, `## PRODUCT TITLE (≤30 chars)`.
TITLE_RE = re.compile(r"^##\s+PRODUCT TITLE\b[^\n]*\n+\s*(.+?)\s*$", re.M)


def frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().casefold()] = value.strip().strip("'\"")
    return fields


def parse_tags(text: str) -> list[str]:
    m = TAGS_RE.search(text)
    if not m:
        return []
    body = m.group(1).strip().strip("*_`")
    return [t.strip().strip("*_`") for t in body.split(",") if t.strip()]


def pick(fields: dict[str, str], *names: str) -> str:
    for name in names:
        value = fields.get(name, "")
        if value:
            return value
    return ""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def collect(directory: Path) -> list[dict]:
    if not directory.is_dir():
        sys.exit(f"error: directory not found: {directory}")
    records: list[dict] = []
    for path in sorted(directory.glob("*-cf.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        title_m = TITLE_RE.search(text)
        title = title_m.group(1) if title_m else ""
        # Three front-matter conventions exist across the listing history:
        # product_number/slug, product-number/product-slug, and number/product.
        product = pick(fm, "product", "product-name", "product_name")
        slug = pick(fm, "product-slug", "product_slug", "slug") or slugify(product or title)
        records.append(
            {
                "number": pick(fm, "product-number", "product_number", "number"),
                "slug": slug,
                "title": title,
                "tags": parse_tags(text),
                "file": path.name,
            }
        )
    return records


def cmd_registry(records: list[dict], args) -> int:
    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return 0
    print(
        f"Existing Creative Fabrica listings ({len(records)}) — already published; "
        "a new listing must not repeat their vocabulary wholesale."
    )
    print("num\tslug\ttags\ttitle")
    for r in records:
        print(f"{r['number'] or '-'}\t{r['slug'] or '-'}\t{len(r['tags'])}\t{r['title'] or '-'}")
    return 0


def cmd_tag_usage(records: list[dict], args) -> int:
    counts: collections.Counter[str] = collections.Counter()
    for r in records:
        counts.update(r["tags"])
    ranked = counts.most_common()
    if args.json:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
        return 0
    total = len(ranked)
    print(
        f"Tag usage across {len(records)} existing Creative Fabrica listings — "
        f"{total} distinct tags. High counts are saturated; prefer distinct routes."
    )
    shown = ranked if args.all else ranked[: args.limit]
    for tag, n in shown:
        print(f"{n:>3}  {tag}")
    if not args.all and total > args.limit:
        print(f"    … {total - args.limit} more distinct tag(s); pass --all to see them")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Index existing Creative Fabrica listings without reading them."
    )
    ap.add_argument("--dir", default=DEFAULT_DIR, type=Path)
    ap.add_argument("--tag-usage", action="store_true", help="rank tags by how many listings use them")
    ap.add_argument("--limit", type=int, default=60, help="rows to show with --tag-usage")
    ap.add_argument("--all", action="store_true", help="show every tag with --tag-usage")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    records = collect(args.dir)
    if not records:
        sys.exit(f"error: no *-cf.md listings found in {args.dir}")
    return cmd_tag_usage(records, args) if args.tag_usage else cmd_registry(records, args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
