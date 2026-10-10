#!/usr/bin/env python3
"""Answer "is this Creative Fabrica tag already measured?" without reading the bank.

`outputs/research/creative-fabrica-tag-bank.json` is the measured tag study. The
agent's "do not pay twice" rule says: if a selected tag is already measured with a
snapshot inside 45 days, cite it as `strategy snapshot route` instead of spending
a live fetch. That is a lookup, but the file is ~47 KB, so reading it to answer the
question costs more than the fetches it is meant to avoid.

This tool reads the bank and prints only the matches:

  python3 bin/creative_fabrica_tag_lookup.py --check "Modern Font" "Script Font" "Quilted Font"
  python3 bin/creative_fabrica_tag_lookup.py --check -f candidates.txt
  python3 bin/creative_fabrica_tag_lookup.py --stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_BANK = Path("outputs/research/creative-fabrica-tag-bank.json")
SNAPSHOT_MAX_AGE_DAYS = 45

TRAILING_FONT_RE = re.compile(r"\s+(fonts?|typefaces?)$", re.IGNORECASE)


def load_bank(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"error: bank not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalise(text: str) -> str:
    """`Modern Serif Font` -> `modern serif`, matching how the bank stores modifiers."""
    low = " ".join(str(text).lower().split())
    while TRAILING_FONT_RE.search(low):
        low = TRAILING_FONT_RE.sub("", low)
    return low.strip()


def build_index(bank: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for record in bank.get("tags", []):
        for key in (record.get("tag", ""), record.get("slug", "")):
            normalised = normalise(key)
            if normalised:
                index.setdefault(normalised, record)
    return index


def snapshot_age(record: dict) -> int | None:
    try:
        return (date.today() - date.fromisoformat(record["retrieved"])).days
    except Exception:
        return None


def lookups_for(candidate: str, index: dict[str, dict]) -> list[tuple[str, dict]]:
    """The candidate itself, then progressively shorter leading phrases.

    A selected tag like `Modern Serif Font` usually has no route of its own; the
    measured route is its leading modifier (`modern`). Report every measured
    prefix so the caller can cite a snapshot instead of paying for a live fetch.
    """
    words = normalise(candidate).split()
    hits: list[tuple[str, dict]] = []
    for length in range(len(words), 0, -1):
        key = " ".join(words[:length])
        record = index.get(key)
        if record is not None:
            hits.append((key, record))
    return hits


def report(candidate: str, index: dict[str, dict], max_age: int) -> dict:
    hits = lookups_for(candidate, index)
    if not hits:
        return {"candidate": candidate, "measured": False, "routes": []}
    routes = []
    for key, record in hits:
        age = snapshot_age(record)
        routes.append(
            {
                "matched_on": key,
                "tag": record.get("tag"),
                "url": record.get("url"),
                "coverage_count": record.get("coverage_count"),
                "status": record.get("status"),
                "retrieved": record.get("retrieved"),
                "age_days": age,
                "fresh": (age is not None and age <= max_age),
            }
        )
    return {"candidate": candidate, "measured": True, "routes": routes}


def cmd_check(args) -> int:
    candidates = list(args.tags)
    if args.file:
        candidates += [
            ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
    if not candidates:
        sys.exit("error: provide tags or -f FILE")

    index = build_index(load_bank(args.bank))
    results = [report(c, index, args.max_age) for c in candidates]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    measured = sum(1 for r in results if r["measured"])
    fresh = sum(1 for r in results for x in r["routes"] if x["fresh"])
    print(
        f"Creative Fabrica tag bank — {len(candidates)} candidate(s), {measured} with a measured "
        f"route, {fresh} fresh (<= {args.max_age}d; cite these as `strategy snapshot route`)"
    )
    print()
    for r in results:
        if not r["measured"]:
            print(f"{r['candidate']}  ->  NOT MEASURED (needs a live fetch if selected)")
            continue
        print(f"{r['candidate']}  ->  measured")
        for x in r["routes"]:
            flag = "FRESH - cite, do not refetch" if x["fresh"] else "STALE - verify live"
            print(
                f"    {x['matched_on']:<22} {x['url']}  "
                f"coverage={x['coverage_count']}  {x['status']}  {x['retrieved']}  [{flag}]"
            )
    return 0


def cmd_stats(args) -> int:
    bank = load_bank(args.bank)
    tags = bank.get("tags", [])
    live = [t for t in tags if t.get("status") == "live"]
    ages = [a for a in (snapshot_age(t) for t in tags) if a is not None]
    print(f"Creative Fabrica tag bank — {args.bank}")
    print(f"  generated:      {bank.get('generated')}")
    print(f"  total fonts:    {bank.get('total_fonts')}")
    print(f"  tags measured:  {len(tags)}  (live {len(live)}, absent {len(tags) - len(live)})")
    print(f"  categories:     {len(bank.get('categories', []))}")
    print(f"  popular products: {len(bank.get('popular_products', []))}")
    if ages:
        print(f"  snapshot age:   oldest {max(ages)}d, newest {min(ages)}d "
              f"(stale beyond {SNAPSHOT_MAX_AGE_DAYS}d)")
    print(f"  file size:      {args.bank.stat().st_size / 1024:.1f} KB "
          f"(query it with --check; do not read it whole)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Look up Creative Fabrica tag measurements without reading the whole bank."
    )
    ap.add_argument("--bank", default=DEFAULT_BANK, type=Path)
    ap.add_argument("--check", action="store_true", help="check candidate tags against the bank")
    ap.add_argument("--stats", action="store_true", help="summarise the bank without dumping it")
    ap.add_argument("tags", nargs="*", help="candidate tags (with --check)")
    ap.add_argument("-f", "--file", type=Path, help="read candidate tags from a file, one per line")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--max-age", type=int, default=SNAPSHOT_MAX_AGE_DAYS)
    args = ap.parse_args(argv)

    if args.stats:
        return cmd_stats(args)
    if args.check or args.tags or args.file:
        return cmd_check(args)
    ap.error("choose --check or --stats")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
