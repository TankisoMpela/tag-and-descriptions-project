#!/usr/bin/env python3
"""Fill the derivable columns of a BOOTH listing's TAG EVIDENCE table.

Two columns of that table encode the tag itself and can never legitimately
disagree with it:

    Exact tag URL        https://booth.pm/ja/items?tags[]=<tag>
    Font-category URL    https://booth.pm/ja/browse/フォント・書体?tags[]=<tag>

Typing those URL-encoded strings by hand is the largest block of avoidable
output in a BOOTH listing, and a mistyped one is a validator failure.

This tool rewrites exactly those columns (plus the language column, also a
property of the tag) and leaves every *observed* value alone: counts,
young-cohort numbers, paid products/sellers, activity/provider status, evidence
tier, and the product-fit reason are preserved byte-for-byte. Live evidence
stays live evidence.

It is deliberately conservative:

  * header-driven, so it handles every column layout the listings use
    (10-column, 11-column young-cohort, abbreviated "Exact URL" headers);
  * it splices only the table block, leaving surrounding prose untouched;
  * it keeps a URL that is already correct, in whatever decoration and encoding
    it uses, so it is a strict no-op on a listing that is already right.

A run may also write the compact eight-column row and let the tool expand it:

    | Tag | Language | Overall count | Font-category count | Paid products / distinct sellers | Activity and provider status | Evidence tier | Product-fit reason |

Usage:
  python3 bin/booth_evidence_table.py --listing outputs/booth/32-archive-meter-booth.md
  python3 bin/booth_evidence_table.py --listing outputs/booth/32-archive-meter-booth.md --write
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

FONT_CATEGORY_ROUTE = "https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93"

STANDARD_HEADER = [
    "Tag", "Language", "Exact tag URL", "Font-category URL", "Overall count",
    "Font-category count", "Paid products / distinct sellers",
    "Activity and provider status", "Evidence tier", "Product-fit reason",
]

# The compact header a run writes when it lets the tool generate the two URL
# columns: the standard header minus exactly those two entries.
COMPACT_HEADER = [c for c in STANDARD_HEADER if c not in ("Exact tag URL", "Font-category URL")]

# Column aliases seen across the listing history.
ALIASES = {
    "tag": ("tag",),
    "lang": ("language", "lang"),
    "exact": ("exact tag url", "exact url", "exact-tag url", "exact tag"),
    "cat": ("font-category url", "font-cat url", "font category url", "font-cat"),
    "phrase": ("phrase", "keyword", "keyword phrase"),
    "placement": (
        "placement", "where placed", "used in", "use",
        # one listing uses the spec's template text verbatim as the column name
        "title/description/selected tag/keyword phrase",
    ),
}

# The validator pins an exact list of historical tag headings and silently
# rejects any listing whose heading predates the list, so match by shape instead.
TAG_SECTION_RE = re.compile(r"^##\s+BOOTH TAGS\b.*$", re.M)
TABLE_BLOCK_RE = re.compile(r"(?:^\|.*\n?)+", re.M)
SEPARATOR_RE = re.compile(r"^\|[\s\-:|]+\|$")

CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def section_span(text: str, pattern: re.Pattern | str) -> tuple[int, int, str] | None:
    """(start, end, body) for a `## ...` section; heading included in the span."""
    rx = pattern if isinstance(pattern, re.Pattern) else re.compile(rf"^## {re.escape(pattern)}\s*$", re.M)
    m = re.search(rx, text)
    if not m:
        return None
    nxt = re.search(r"^## ", text[m.end() :], re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    return m.start(), end, text[m.end() : end]


def parse_tags(text: str) -> list[str]:
    span = section_span(text, TAG_SECTION_RE)
    if span is None:
        return []
    return [
        ln.strip()
        for ln in span[2].splitlines()
        if ln.strip() and not ln.strip().startswith(("#", "|"))
    ]


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_table_block(block: str) -> tuple[list[str], str, list[list[str]]]:
    """(header cells, separator line verbatim, data rows) from a table block."""
    header: list[str] = []
    separator = ""
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if SEPARATOR_RE.match(stripped):
            if not separator:
                separator = stripped
            continue
        cells = split_cells(stripped)
        if not header:
            header = cells
            continue
        rows.append(cells)
    return header, separator, rows


def undecorate(cell: str) -> str:
    return cell.strip().strip("`*").strip()


def derive_language(tag: str, existing: str = "") -> str:
    if existing.strip():
        return existing.strip()
    return "JA" if CJK_RE.search(tag) else "EN"


def urls_for(tag: str) -> tuple[str, str]:
    """BOOTH route URLs. `quote_plus` matches the existing listings and decodes
    identically under the validator's parse_qs."""
    enc = urllib.parse.quote_plus(tag)
    return (
        f"https://booth.pm/ja/items?tags%5B%5D={enc}",
        f"{FONT_CATEGORY_ROUTE}?tags%5B%5D={enc}",
    )


def url_already_correct(cell: str, tag: str, *, browse: bool) -> bool:
    """True when the cell already holds a correct route URL for `tag`.

    Backticks and other emphasis are ignored for the check so a valid-but-decorated
    URL is left exactly as it is.
    """
    try:
        parsed = urllib.parse.urlparse(undecorate(cell))
        values = urllib.parse.parse_qs(parsed.query, keep_blank_values=True).get("tags[]")
    except Exception:
        return False
    if not values or values[0].strip().casefold() != tag.casefold():
        return False
    return "/browse/" in parsed.path if browse else parsed.path.startswith("/ja/items")


def header_key(cells: list[str]) -> tuple[str, ...]:
    return tuple(undecorate(c).casefold() for c in cells)


COMPACT_KEYS = header_key(COMPACT_HEADER)


def expand_compact_header(tags: list[str], cells_rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    """Grow an 8-column compact table into the full 10-column standard table."""
    out: list[list[str]] = []
    for tag, cells in zip(tags, cells_rows):
        exact, category = urls_for(tag)
        row = list(cells)
        if len(row) > 1:
            row[1] = derive_language(tag, row[1])
        row.insert(2, exact)
        row.insert(3, category)
        row[0] = tag
        out.append(row)
    return list(STANDARD_HEADER), out


def find_index(header: list[str], key: str) -> int | None:
    wanted = ALIASES[key]
    for i, cell in enumerate(header):
        if undecorate(cell).casefold() in wanted:
            return i
    return None


def normalize(header: list[str], tag: str, cells: list[str]) -> tuple[list[str] | None, str]:
    exact, category = urls_for(tag)

    # Compact form: the run wrote the eight columns that are not derivable.
    if len(header) == 10 and len(cells) == 8 and cells[0].casefold() == tag.casefold():
        return [tag, derive_language(tag, cells[1]), exact, category, *cells[2:]], ""

    if len(cells) != len(header):
        return None, (
            f"row for '{tag}' has {len(cells)} columns but the table header has "
            f"{len(header)}; write the full row or the 8-column compact row"
        )

    i_exact = find_index(header, "exact")
    i_cat = find_index(header, "cat")
    if i_exact is None or i_cat is None:
        return None, "table header is missing the exact-tag/font-category URL columns"

    row = list(cells)
    i_tag = find_index(header, "tag")
    i_lang = find_index(header, "lang")
    if i_tag is not None:
        row[i_tag] = tag
    if i_lang is not None:
        row[i_lang] = derive_language(tag, cells[i_lang])
    if not url_already_correct(row[i_exact], tag, browse=False):
        row[i_exact] = exact
    if not url_already_correct(row[i_cat], tag, browse=True):
        row[i_cat] = category
    return row, ""


def placement_for(phrase: str, title: str, description: str, tags: list[str]) -> str:
    """Where a phrase actually landed. Mechanical, so the run never types it."""
    needle = phrase.casefold()
    placed: list[str] = []
    if needle in title.casefold():
        placed.append("title")
    if needle in description.casefold():
        placed.append("description")
    if any(needle == t_.casefold() for t_ in tags):
        placed.append("selected tag")
    elif any(needle in t_.casefold() for t_ in tags):
        placed.append("selected tag (partial)")
    return " / ".join(placed) if placed else "keyword phrase only"


def fill_coverage(text: str) -> tuple[str | None, list[str]]:
    """Fill only the Placement column of KEYWORD COVERAGE.

    The table also carries live research columns (route, raw count, owned
    excluded, independent count) which are preserved verbatim.
    """
    span = section_span(text, "KEYWORD COVERAGE")
    if span is None:
        return None, ["no KEYWORD COVERAGE section found"]
    body = span[2]
    title_body = section_span(text, "PRODUCT TITLE")
    desc_body = section_span(text, "PRODUCT DESCRIPTION (PASTE-READY)")
    title = title_body[2] if title_body else ""
    description = desc_body[2] if desc_body else ""
    tags = parse_tags(text)

    block = TABLE_BLOCK_RE.search(body)
    if block is None:
        # Historical list form. Rows are pipe-separated WITHOUT outer pipes:
        #   - <phrase> | <route> | <raw> | <owned> | <independent> | <placement>
        # Some rows carry prose instead of a full row (e.g. a note about keyword
        # routes), and field counts vary, so touch a line only when its final
        # field is an empty placement slot. Anything else is left byte-identical.
        heading = text[span[0] : span[1] - len(body)]
        lines: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("-", "*")) or "|" not in stripped:
                lines.append(line)
                continue
            prefix = stripped[: len(stripped) - len(stripped.lstrip("-* "))]
            fields = [f.strip() for f in stripped.lstrip("-* ").split("|")]
            if len(fields) >= 2 and undecorate(fields[-1]) in {"", "-", "—"}:
                fields[-1] = placement_for(undecorate(fields[0]), title, description, tags)
                lines.append(f"{prefix}{' | '.join(fields)}")
            else:
                lines.append(line)
        return heading + "\n".join(lines) + "\n", []

    header, separator, rows = parse_table_block(block.group(0))
    i_phrase = find_index(header, "phrase")
    if i_phrase is None:
        return None, ["KEYWORD COVERAGE table has no phrase column"]
    i_place = find_index(header, "placement")

    if i_place is None:
        header = list(header) + ["Placement"]
        i_place = len(header) - 1

    rebuilt: list[list[str]] = []
    for cells in rows:
        if len(cells) < len(header):
            cells = cells + [""] * (len(header) - len(cells))
        row = list(cells)
        phrase = undecorate(row[i_phrase])
        stated = undecorate(row[i_place]) if i_place < len(row) else ""
        # Conservative: a run may state the placement, and a stated value always
        # wins. Fill only what was left blank, so an existing listing is untouched.
        if not stated or stated in {"-", "—"}:
            row[i_place] = placement_for(phrase, title, description, tags)
        rebuilt.append(row)

    new_block = render(header, separator, rebuilt)
    # Return the COMPLETE section, heading included: the caller splices over
    # [span_start, span_end), so a fragment without the heading would delete it.
    heading = text[span[0] : span[1] - len(body)]
    return heading + body[: block.start()] + new_block + body[block.end() :], []


def render(header: list[str], separator: str, rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |"]
    lines.append(separator or "|" + "|".join(["---"] * len(header)) + "|")
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Regenerate the derivable TAG EVIDENCE columns (URLs, language) in place."
    )
    ap.add_argument("--listing", required=True, type=Path)
    ap.add_argument("--write", action="store_true", help="rewrite the listing (default: print only)")
    ap.add_argument(
        "--fill-coverage",
        action="store_true",
        help="instead of the evidence table, fill each KEYWORD COVERAGE phrase's placement",
    )
    args = ap.parse_args(argv)

    if not args.listing.exists():
        sys.exit(f"error: listing not found: {args.listing}")
    text = args.listing.read_text(encoding="utf-8")

    if args.fill_coverage:
        new_section, problems = fill_coverage(text)
        if problems:
            for p_ in problems:
                print(f"[FAIL] {p_}", file=sys.stderr)
            return 1
        assert new_section is not None
        span = section_span(text, "KEYWORD COVERAGE")
        assert span is not None
        updated = text[: span[0]] + new_section + text[span[1] :]
        if not args.write:
            print(new_section)
            return 0
        args.listing.write_text(updated, encoding="utf-8")
        print(f"filled KEYWORD COVERAGE placements in {args.listing}")
        return 0

    tags = parse_tags(text)
    if not tags:
        sys.exit("error: could not find a BOOTH tag section in the listing")

    span = section_span(text, "TAG EVIDENCE")
    if span is None:
        sys.exit("error: could not find a TAG EVIDENCE section in the listing")
    sec_start, sec_end, body = span
    block = TABLE_BLOCK_RE.search(body)
    if block is None:
        sys.exit("error: could not find a TAG EVIDENCE table in the listing")

    header, separator, rows = parse_table_block(block.group(0))
    if not rows:
        sys.exit("error: TAG EVIDENCE table has no data rows")
    if len(rows) != len(tags):
        sys.exit(
            f"error: {len(rows)} evidence row(s) but {len(tags)} selected tag(s); "
            "fix the row count before normalising"
        )

    if header_key(header) == COMPACT_KEYS and len(header) == len(rows[0]):
        header, rows = expand_compact_header(tags, rows)
        separator = ""

    problems: list[str] = []
    rebuilt: list[list[str]] = []
    for tag, cells in zip(tags, rows):
        if cells[0].strip("`* ").casefold() != tag.casefold():
            problems.append(f"row '{cells[0]}' does not match selected tag '{tag}'")
            continue
        row, err = normalize(header, tag, cells)
        if err:
            problems.append(err)
            continue
        rebuilt.append(row)

    if problems:
        for p in problems:
            print(f"[FAIL] {p}", file=sys.stderr)
        return 1

    new_block = render(header or STANDARD_HEADER, separator, rebuilt)
    new_body = body[: block.start()] + new_block + body[block.end() :]
    # `body` is the section content immediately after its heading line.
    updated = text[: sec_end - len(body)] + new_body + text[sec_end:]

    if not args.write:
        print(new_block)
        print(
            f"(dry run — {len(rebuilt)} row(s) rebuilt; pass --write to update {args.listing})",
            file=sys.stderr,
        )
        return 0

    args.listing.write_text(updated, encoding="utf-8")
    print(f"rewrote TAG EVIDENCE for {len(rebuilt)} tag(s) in {args.listing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
