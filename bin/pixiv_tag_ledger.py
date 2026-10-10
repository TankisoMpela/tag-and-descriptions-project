#!/usr/bin/env python3
"""Query and append the Pixiv tag ledger without reading it whole.

Mirrors `booth_tag_ledger.py`: the ledger is a persistent record of which tags
have been used, rejected, or keyword-only across Pixiv packages, and reading it
inline costs tokens on every run. Query it instead.

  --stats                 ledger size and product count
  --check <tag>...        prior use, tier and product for each candidate tag
  --append --listing P    append the listing's own PIXIV TAG EVIDENCE table

`--append` takes the table **from the listing**, so the evidence rows are written
once, by the agent, in the place they belong. Previously the agent was told to
"append the same evidence rows" and satisfied that by reprinting the whole table
inside the listing as `## APPENDIX: LEDGER UPDATE` — the same 23 rows twice, with
the ledger append left for a human to copy. That appendix was ~1,443 output
tokens per package and duplicated a table already in the ledger.

Usage:
    python3 bin/pixiv_tag_ledger.py --stats
    python3 bin/pixiv_tag_ledger.py --check フォント typography 文字デザイン
    python3 bin/pixiv_tag_ledger.py --append \
        --listing outputs/pixiv/86-silken-flourish-pixiv.md \
        --number 86 --product "Silken Flourish" --date 2026-09-22
"""
from __future__ import annotations

import argparse
import re
from datetime import date as _date
from pathlib import Path

DEFAULT_LEDGER = Path("outputs/pixiv/pixiv-tag-ledger.md")
PRODUCT_RE = re.compile(r"^##\s+Product\s+#?(\d+)\s*(?:—|-|–)?\s*(.*)$", re.MULTILINE)
ROW_RE = re.compile(r"^\|(?P<cells>.+)\|\s*$")
EVIDENCE_HEADING = "PIXIV TAG EVIDENCE"
SEPARATOR_CELL = re.compile(r"^[-:\s|]+$")


def load(ledger: Path) -> str:
    if not ledger.is_file():
        return ""
    return ledger.read_text(encoding="utf-8")


def product_sections(text: str) -> list[tuple[str, str, str]]:
    """Return (number, name, body) for each product section."""
    out: list[tuple[str, str, str]] = []
    matches = list(PRODUCT_RE.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        out.append((match.group(1), match.group(2).strip(), text[match.start():end]))
    return out


def rows_of(body: str) -> list[list[str]]:
    """Parse markdown table rows, skipping the header separator."""
    rows: list[list[str]] = []
    for line in body.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group("cells").split("|")]
        if all(SEPARATOR_CELL.match(c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def tag_index(text: str) -> dict[str, list[tuple[str, str, str, str]]]:
    """tag -> [(product number, product name, tier, status), ...]"""
    index: dict[str, list[tuple[str, str, str, str]]] = {}
    for number, name, body in product_sections(text):
        rows = rows_of(body)
        if not rows:
            continue
        header = [c.casefold() for c in rows[0]]
        try:
            tag_i = header.index("tag")
        except ValueError:
            continue
        tier_i = header.index("tier") if "tier" in header else None
        status_i = next((i for i, h in enumerate(header) if "status" in h), None)
        for row in rows[1:]:
            if len(row) <= tag_i or not row[tag_i]:
                continue
            tier = row[tier_i] if tier_i is not None and len(row) > tier_i else "-"
            status = row[status_i] if status_i is not None and len(row) > status_i else "-"
            index.setdefault(row[tag_i], []).append((number, name, tier, status))
    return index


def cmd_stats(ledger: Path) -> int:
    text = load(ledger)
    if not text:
        print(f"ledger not found: {ledger}")
        return 1
    sections = product_sections(text)
    index = tag_index(text)
    print(f"ledger            : {ledger} ({len(text.encode()):,} B)")
    print(f"product sections  : {len(sections)}")
    print(f"distinct tags     : {len(index)}")
    for number, name, body in sections[-3:]:
        print(f"  #{number} {name}: {len(rows_of(body)) - 1} rows")
    print("\nQuery this file, do not read it whole:")
    print("  python3 bin/pixiv_tag_ledger.py --check <tag> [<tag> ...]")
    return 0


def cmd_check(ledger: Path, tags: list[str]) -> int:
    index = tag_index(load(ledger))
    for tag in tags:
        prior = index.get(tag)
        if not prior:
            print(f"{tag}\tNO RECORD\t-\t-")
        else:
            numbers = ",".join(p[0] for p in prior)
            tiers = ",".join(sorted({p[2] for p in prior}))
            print(f"{tag}\tPRIOR USE\t#{numbers}\t{tiers}")
    return 0


def extract_evidence(listing: Path) -> tuple[list[str], list[str]]:
    """Return (header_row, data_rows) from the listing's PIXIV TAG EVIDENCE table."""
    text = listing.read_text(encoding="utf-8")
    if EVIDENCE_HEADING not in text:
        raise SystemExit(f"{listing}: no {EVIDENCE_HEADING} section to append")
    body = text.split(EVIDENCE_HEADING, 1)[1]
    body = body.split("\n## ", 1)[0]
    rows = rows_of(body)
    if len(rows) < 2:
        raise SystemExit(f"{listing}: {EVIDENCE_HEADING} has no table rows")
    return rows[0], rows[1:]


def cmd_append(args) -> int:
    header, rows = extract_evidence(args.listing)
    ledger = args.ledger
    text = load(ledger)
    existing = {str(n) for n, _, _ in product_sections(text)}
    if args.number in existing:
        raise SystemExit(
            f"{ledger}: product #{args.number} is already recorded; "
            "remove that section first if you intend to replace it"
        )

    run_date = args.date or _date.today().isoformat()
    block = [f"\n## Product #{args.number} — {args.product}", "",
             f"Retrieval date: {run_date}", "",
             "| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        padded = row + [""] * (len(header) - len(row))
        block.append("| " + " | ".join(padded[:len(header)]) + " |")
    block.append("")
    entry = "\n".join(block)

    if args.dry_run:
        print(entry)
        return 0

    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    print(f"appended {len(rows)} row(s) for product #{args.number} to {ledger}")
    print("The listing must NOT reprint these rows; the ledger is the record.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, type=Path)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--check", action="store_true", help="check candidate tags against the ledger")
    ap.add_argument("--append", action="store_true", help="append a product section")
    ap.add_argument("tags", nargs="*", help="candidate tags (with --check)")
    ap.add_argument("--listing", type=Path, help="the listing to take the evidence table from")
    ap.add_argument("--number", help="product number for the appended section")
    ap.add_argument("--product", help="product name for the appended section")
    ap.add_argument("--date", help="retrieval date (YYYY-MM-DD); defaults to today")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.stats:
        return cmd_stats(args.ledger)
    if args.append:
        if not args.listing or not args.number or not args.product:
            ap.error("--append needs --listing, --number and --product")
        return cmd_append(args)
    if args.check:
        if not args.tags:
            ap.error("--check needs at least one tag")
        return cmd_check(args.ledger, args.tags)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
