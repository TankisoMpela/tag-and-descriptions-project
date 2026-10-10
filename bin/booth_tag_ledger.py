#!/usr/bin/env python3
"""Query and append the BOOTH dead/useless-tag ledger without reading it whole.

`outputs/booth/booth-tag-ledger.md` is a long human-readable record of the tags
BOOTH research has already rejected or deprioritised. Reading the whole file at
the start of every run is the single most expensive input in the BOOTH workflow,
and the file only grows. The workflow never needs the whole file -- it needs the
answer to one question per candidate:

    "has this tag already been decided?"

This tool answers that question directly, and appends new decisions
mechanically, so the ledger stays the source of truth while the agent stops
paying to read all of it.

Usage:
  python3 bin/booth_tag_ledger.py --check "タイポグラフィー" "書体 商用利用"
  python3 bin/booth_tag_ledger.py --check -f candidates.txt
  python3 bin/booth_tag_ledger.py --check --json -f candidates.txt
  python3 bin/booth_tag_ledger.py --append --number 32 --product "Archive Meter" \
      --date 2026-09-21 --verdict rejected --reason "no exact tag" --tags "foo,bar"
  python3 bin/booth_tag_ledger.py --stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign_mode  # noqa: E402

DEFAULT_LEDGER = Path("outputs/booth/booth-tag-ledger.md")

# A decision line labels itself before its tag list ("- New set (...): a, b" or
# "- Rejected, dead/no coverage: a | fc 0 | ..."), and lists its tags as
# `tag (evidence)` or `tag | evidence`. Classification is anchored to the LABEL
# and to tag OWNERSHIP of an item, never to a substring appearing anywhere on
# the line: `かっこいい` must not match the item `フォント かっこいい`.
SELECT_LABEL = re.compile(
    r"\bselected\b|new set|priority block|priority tag|passing lane", re.IGNORECASE
)
REJECT_LABEL = re.compile(
    r"\brejected\b|gate fail|\bFAIL\b|dead/no coverage|deprioriti|excluded|not selected"
    r"|archived|blocked|not universal-core",
    re.IGNORECASE,
)
SEGMENT_SPLIT = re.compile(r",\s+|\s*/\s*")

VERDICT_REJECTED = "KNOWN-REJECTED"
VERDICT_SELECTED = "KNOWN-SELECTED"
VERDICT_BOTH = "DECIDED-BOTH (selected for one product, rejected for another)"
VERDICT_SEEN = "SEEN (context only, no verdict)"
VERDICT_NONE = "NO RECORD"
# A free-offer tag rejected under a paid-only campaign is not a dead lead in a
# free campaign: the rejection was conditional on the campaign mode.
VERDICT_MODE_CONDITIONAL = (
    "MODE-CONDITIONAL (rejected under a paid-only campaign; retest under this free campaign)"
)


def load_lines(ledger: Path) -> list[str]:
    if not ledger.exists():
        sys.exit(f"error: ledger not found: {ledger}")
    return ledger.read_text(encoding="utf-8", errors="replace").splitlines()


def truncate(text: str, width: int) -> str:
    text = " ".join(text.split())
    if len(text) > width:
        text = text[: width - 1].rstrip() + "…"
    # Never end mid-parenthetical.
    if text.count("(") > text.count(")") and "(" in text:
        text = text[: text.rfind("(")].rstrip()
    return text


def item_core(segment: str) -> str:
    """`フォント かっこいい (THIN n=22)` / `書体 | fc 89` -> the bare tag."""
    return re.split(r"\s*[(|]", segment.strip(), maxsplit=1)[0].strip().strip("`*").strip()


def owned_item(line: str, tag: str, width: int) -> str | None:
    """Return the displayed item if `line` carries `tag` as an item of its list."""
    body = line.lstrip("-*# ").strip()
    _, _, rest = body.partition(": ")
    if not rest:
        rest = body
    wanted = tag.casefold()
    for part in SEGMENT_SPLIT.split(rest):
        if item_core(part).casefold() == wanted:
            return truncate(part, width)
    return None


def classify(tag: str, lines: list[str], width: int) -> dict:
    selected: list[str] = []
    rejected: list[str] = []
    context: list[str] = []
    for line in lines:
        item = owned_item(line, tag, width)
        if item is None:
            continue
        head = line.lstrip("-*# ").strip().split(": ", 1)[0]
        if SELECT_LABEL.search(head):
            selected.append(item)
        elif REJECT_LABEL.search(head):
            rejected.append(item)
        elif REJECT_LABEL.search(item):
            rejected.append(item)
        elif SELECT_LABEL.search(item):
            selected.append(item)
        else:
            context.append(item)

    if selected and rejected:
        verdict = VERDICT_BOTH
    elif selected:
        verdict = VERDICT_SELECTED
    elif rejected:
        verdict = VERDICT_REJECTED
    elif context:
        verdict = VERDICT_SEEN
    else:
        return {"tag": tag, "verdict": VERDICT_NONE, "selected_items": 0, "rejected_items": 0, "shown": []}

    shown: list[str] = []
    if selected:
        shown.append(f"selected  — {selected[-1]}")
    if rejected:
        shown.append(f"rejected  — {rejected[-1]}")
    if not shown:
        shown.append(f"context   — {context[-1]}")
    return {
        "tag": tag,
        "verdict": verdict,
        "selected_items": len(selected),
        "rejected_items": len(rejected),
        "shown": shown,
    }


# Cross-listing usage. The ledger answers "did I already judge this tag"; it
# cannot answer "do I already use it everywhere", which is the differentiation
# question a new listing actually faces. A tag carried by most of the catalogue
# has no discovery breadth left and cannot be tested, so the count is shown
# alongside the verdict.
BOOTH_DIR = Path("outputs/booth")


def listing_usage() -> tuple[dict[str, int], int]:
    """tag -> number of prior listings carrying it, and the listing count."""
    counts: dict[str, int] = {}
    n = 0
    for path in sorted(BOOTH_DIR.glob("*-booth.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = re.search(r"(?im)^##\s*BOOTH TAGS[^\n]*\n(.*?)(?=\n##\s|\Z)", text, re.S)
        if not m:
            continue
        tags = [
            l.strip()
            for l in m.group(1).splitlines()
            if l.strip() and not l.strip().startswith(("|", "-", "#"))
        ]
        if not tags:
            continue
        n += 1
        for tag in set(tags):
            counts[tag] = counts.get(tag, 0) + 1
    return counts, n


def usage_label(tag: str, counts: dict[str, int], n: int) -> str:
    if not n:
        return ""
    c = counts.get(tag, 0)
    pct = 100 * c / n
    if c == 0:
        note = "fresh - no listing uses it"
    elif pct >= 80:
        note = "NEAR-UNIVERSAL - no differentiation, untestable"
    elif pct >= 50:
        note = "core - reuse carries little new signal"
    elif pct >= 25:
        note = "moderate reuse"
    else:
        note = "low reuse"
    return f"used in {c}/{n} listings ({pct:.0f}%) - {note}"


def read_tags(args) -> list[str]:
    tags = list(args.tags)
    if args.file:
        tags.extend(
            ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()
        )
    tags = [t.strip() for t in tags if t.strip()]
    if not tags:
        sys.exit("error: provide tags or -f FILE")
    return tags


def cmd_check(args) -> int:
    tags = read_tags(args)
    lines = load_lines(args.ledger)
    results = [classify(tag, lines, args.width) for tag in tags]

    # Under a free campaign, a free-offer tag's paid-only rejection is
    # conditional, not final. Reclassify it so the agent retests instead of
    # treating it as a dead lead.
    allow_free = campaign_mode.is_free_mode(args.campaign)
    if allow_free:
        for r in results:
            if (
                campaign_mode.is_free_offer_tag(r["tag"])
                and r["rejected_items"]
                and not r["selected_items"]
            ):
                r["verdict"] = VERDICT_MODE_CONDITIONAL

    usage, n_listings = listing_usage()

    if args.json:
        for r in results:
            r["used_in_listings"] = usage.get(r["tag"], 0)
            r["listings_total"] = n_listings
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"BOOTH tag ledger — {len(tags)} candidate(s)")
    for verdict, n in sorted(counts.items()):
        print(f"  {n:>3}  {verdict}")
    print()
    for r in results:
        print(f"{r['tag']}  ->  {r['verdict']}")
        lbl = usage_label(r["tag"], usage, n_listings)
        if lbl:
            print(f"    {lbl}")
        for line in r["shown"]:
            print(f"    {line}")
    print()
    if n_listings:
        print(f"Usage counts span {n_listings} prior listings. Prefer fresh or low-reuse")
        print("candidates for a new listing; near-universal tags add no breadth.")
    print("KNOWN-REJECTED candidates must not be re-researched or promoted into selected tags.")
    print("MODE-CONDITIONAL means the rejection held under a paid-only campaign; a free")
    print("campaign may retest it. DECIDED-BOTH means the tag was used by one product and rejected by another — judge on fit.")
    return 0


def cmd_stats(args) -> int:
    lines = load_lines(args.ledger)
    products = [ln for ln in lines if ln.startswith("## ")]
    print(f"BOOTH tag ledger — {args.ledger}")
    print(f"  lines:    {len(lines):,}")
    print(f"  bytes:    {args.ledger.stat().st_size:,}")
    print(f"  products: {len(products)}")
    if products:
        print(f"  latest:   {products[-1][3:]}")
    return 0


def cmd_append(args) -> int:
    tags = [t.strip() for t in (args.append_tags or "").split(",") if t.strip()]
    reason = args.reason or ""
    if args.reason_file:
        reason = args.reason_file.read_text(encoding="utf-8").strip()
    if not args.product or not reason:
        sys.exit("error: --append requires --product and (--reason or --reason-file)")

    entry = [
        "",
        f"## Product {args.number}: {args.product} — {args.verdict.upper()} run ({args.date})",
    ]
    if tags:
        entry.append(f"- Candidate tags ({args.verdict}): {', '.join(tags)}")
    entry.append(f"- Reason: {reason}")
    if args.evidence:
        entry.append(f"- Evidence: {args.evidence}")

    block = "\n".join(entry) + "\n"
    if args.dry_run:
        print(block)
        return 0

    with args.ledger.open("a", encoding="utf-8") as fh:
        fh.write(block)
    print(f"appended {args.verdict} entry for Product {args.number} ({args.product}) to {args.ledger}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Query/append the BOOTH dead-tag ledger without reading it whole."
    )
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, type=Path)
    ap.add_argument("--check", action="store_true", help="check candidate tags against the ledger")
    ap.add_argument("--stats", action="store_true", help="print ledger size/product stats")
    ap.add_argument("--append", action="store_true", help="append a decision entry")
    ap.add_argument("tags", nargs="*", help="candidate tags (with --check)")
    ap.add_argument("-f", "--file", type=Path, help="read candidate tags from a file, one per line")
    ap.add_argument("--json", action="store_true", help="emit JSON (with --check)")
    ap.add_argument("--width", type=int, default=150, help="truncate displayed items to this width")
    ap.add_argument(
        "--campaign",
        default=campaign_mode.LEGACY_MODE,
        help="campaign mode; a free mode reclassifies free-offer rejections as MODE-CONDITIONAL",
    )
    # --append options
    ap.add_argument("--number", help="product number for the appended entry")
    ap.add_argument("--product", help="product name for the appended entry")
    ap.add_argument("--date", help="run date (YYYY-MM-DD)")
    ap.add_argument(
        "--tags", dest="append_tags", help="comma-separated candidate tags for --append"
    )
    ap.add_argument("--verdict", default="rejected", choices=["rejected", "deprioritised", "selected"])
    ap.add_argument("--reason", help="rejection/deprioritisation reason")
    ap.add_argument("--reason-file", type=Path, help="read the reason from a file")
    ap.add_argument("--evidence", help="optional evidence line (URLs, counts, provider)")
    ap.add_argument("--dry-run", action="store_true", help="print the entry instead of appending")
    args = ap.parse_args(argv)

    if args.append:
        return cmd_append(args)
    if args.stats:
        return cmd_stats(args)
    if args.check or args.tags or args.file:
        return cmd_check(args)
    ap.error("choose --check, --stats, or --append")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. `| head`
        sys.exit(0)
