#!/usr/bin/env python3
"""Print the FontFairy-owned BOOTH product registry without reading every listing.

Agent-20 must build an exclusion registry of already-owned products before it
opens any live BOOTH page, and the spec's algorithm for doing so is purely
mechanical:

    frontmatter `product`, `slug`, `number`, falling back to the first product
    name in `## PRODUCT TITLE`, keeping the source filename, deduplicated by
    product name/slug.

Reading all ~87 listings to run that algorithm costs roughly 0.5M input tokens
and repeats on every run. This tool runs the same algorithm against the same
files and prints a few hundred bytes instead, so the agent gets the registry
exactly as specified, at a rounding error of the cost.

Usage:
  python3 bin/booth_owned_registry.py
  python3 bin/booth_owned_registry.py --json
  python3 bin/booth_owned_registry.py --slugs-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path("outputs/booth")
EXCLUDE = {"booth-tag-ledger.md"}
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
TITLE_RE = re.compile(r"^##\s+PRODUCT TITLE\s*$\n(.*?)(?=^## |\Z)", re.M | re.S)
# A product name ends where the listing starts decorating: 名前【タグ】, 名前 | x, 名前（x）
NAME_SPLIT_RE = re.compile(r"[【（(\[|｜]")


def frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().casefold()] = value.strip().strip("'\"")
    return fields


def first_title_name(text: str) -> str:
    m = TITLE_RE.search(text)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        stripped = line.strip().strip("*_` ")
        if not stripped:
            continue
        return NAME_SPLIT_RE.split(stripped, maxsplit=1)[0].strip()
    return ""


def collect(directory: Path) -> list[dict[str, object]]:
    if not directory.is_dir():
        sys.exit(f"error: directory not found: {directory}")
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for path in sorted(directory.glob("*-booth.md")):
        if path.name in EXCLUDE:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        product = fm.get("product", "") or first_title_name(text)
        slug = fm.get("slug", "")
        number = fm.get("number", "")
        if not product and not slug:
            continue
        key = (str(product).casefold(), str(slug).casefold())
        # Deduplicate by product name/slug as the spec requires, but keep every
        # source filename so nothing is silently dropped from the registry.
        record = groups.setdefault(
            key,
            {"number": number, "product": product, "slug": slug, "files": []},
        )
        record["files"].append(path.name)  # type: ignore[union-attr]
        if not record["number"] and number:
            record["number"] = number
    return list(groups.values())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Print the owned BOOTH product exclusion registry as compact text."
    )
    ap.add_argument("--dir", default=DEFAULT_DIR, type=Path)
    ap.add_argument("--json", action="store_true", help="emit JSON records")
    ap.add_argument("--slugs-only", action="store_true", help="print just the slugs")
    args = ap.parse_args(argv)

    records = collect(args.dir)

    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return 0

    if args.slugs_only:
        for r in records:
            if r["slug"]:
                print(r["slug"])
        return 0

    print(
        f"FontFairy-owned BOOTH products ({len(records)}) — all are excluded from competitor, "
        "repetition, paid-product, distinct-seller and activity evidence."
    )
    print("num\tproduct\tslug\tfile(s)")
    for r in records:
        files = ",".join(r["files"])  # type: ignore[arg-type]
        print(f"{r['number'] or '-'}\t{r['product'] or '-'}\t{r['slug'] or '-'}\t{files}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. `| head`
        sys.exit(0)
