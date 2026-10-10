#!/usr/bin/env python3
"""Per-font Pinterest tag ledger — stops fonts cannibalizing each other.

outputs/research/pinterest-tags.sqlite records every keyword the daily run
uses, per font. Before writing a pin the agent asks `avoid` for the least-used
candidate tags for that font; after the CSV is assembled `record` logs the
choice. `stats` shows usage counts and percentages so drift is visible.

Usage:
  python3 bin/pinterest_tag_ledger.py record --slug quiet-acre --date 2026-10-10 --tags "boho script font, wedding signage font"
  python3 bin/pinterest_tag_ledger.py avoid --slug quiet-acre --candidates "boho script font, wedding signage font, ..." --take 5
  python3 bin/pinterest_tag_ledger.py stats [--slug quiet-acre]
  python3 bin/pinterest_tag_ledger.py reset --slug quiet-acre [--yes]
  Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("outputs/research/pinterest-tags.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tag_uses (
    id        INTEGER PRIMARY KEY,
    font_slug TEXT NOT NULL,
    tag       TEXT NOT NULL,
    run_date  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pinned_runs (
    font_slug TEXT NOT NULL,
    run_date  TEXT NOT NULL,
    csv_path  TEXT,
    UNIQUE (font_slug, run_date)
);
CREATE INDEX IF NOT EXISTS idx_tag_uses ON tag_uses (font_slug, tag);
"""


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def norm(tag: str) -> str:
    return " ".join(tag.strip().lower().removeprefix("#").split())


def split_tags(raw: str) -> list[str]:
    seen, out = set(), []
    for t in raw.split(","):
        t = norm(t)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def font_counts(con: sqlite3.Connection, slug: str) -> dict[str, int]:
    return dict(con.execute("SELECT tag, COUNT(*) FROM tag_uses WHERE font_slug=? GROUP BY tag", (slug,)))


def cmd_record(args, con: sqlite3.Connection) -> int:
    tags = split_tags(args.tags)
    if not tags:
        sys.exit("error: no tags given")
    con.executemany(
        "INSERT INTO tag_uses (font_slug, tag, run_date) VALUES (?,?,?)",
        [(args.slug, t, args.date) for t in tags],
    )
    con.execute("INSERT OR IGNORE INTO pinned_runs (font_slug, run_date, csv_path) VALUES (?,?,?)",
                (args.slug, args.date, args.csv))
    con.commit()
    out = {"slug": args.slug, "date": args.date, "recorded": tags}
    print(json.dumps(out, indent=2) if args.json else f"{args.slug}: recorded {len(tags)} tag use(s) for {args.date}")
    return 0


def cmd_avoid(args, con: sqlite3.Connection) -> int:
    candidates = split_tags(args.candidates)
    if not candidates:
        sys.exit("error: no candidates given")
    used = font_counts(con, args.slug)
    # never-used first, then least-used, stable alphabetical within a tier
    ranked = sorted(candidates, key=lambda t: (used.get(t, 0), t))
    take = ranked[: args.take]
    out = {"slug": args.slug, "take": args.take, "selected": take,
            "font_usage": {t: used.get(t, 0) for t in candidates}}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print("\n".join(take))
    return 0


def cmd_stats(args, con: sqlite3.Connection) -> int:
    slugs = [args.slug] if args.slug else [
        r[0] for r in con.execute("SELECT DISTINCT font_slug FROM tag_uses ORDER BY font_slug")
    ]
    if not slugs:
        print("(no tag usage recorded yet)")
        return 0
    report = []
    for slug in slugs:
        counts = font_counts(con, slug)
        total = sum(counts.values())
        tags = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        report.append({
            "slug": slug,
            "total_tag_uses": total,
            "distinct_tags": len(counts),
            "top_share_pct": round(100 * tags[0][1] / total, 1) if total else 0.0,
            "tags": [{"tag": t, "uses": c, "pct": round(100 * c / total, 1)} for t, c in tags],
        })
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report:
            print(f"\n{r['slug']} — {r['total_tag_uses']} uses, {r['distinct_tags']} distinct tags, "
                  f"heaviest tag {r['top_share_pct']}% of this font's usage")
            for t in r["tags"][:15]:
                bar = "#" * max(1, round(t["pct"] / 5))
                print(f"  {t['uses']:>3}  {t['pct']:>5}%  {bar:<8} {t['tag']}")
            if len(r["tags"]) > 15:
                print(f"  … {len(r['tags']) - 15} more")
    return 0


def cmd_reset(args, con: sqlite3.Connection) -> int:
    n = con.execute("SELECT COUNT(*) FROM tag_uses WHERE font_slug=?", (args.slug,)).fetchone()[0]
    if not args.yes:
        sys.exit(f"error: {args.slug} has {n} recorded tag uses — pass --yes to clear them")
    con.execute("DELETE FROM tag_uses WHERE font_slug=?", (args.slug,))
    con.execute("DELETE FROM pinned_runs WHERE font_slug=?", (args.slug,))
    con.commit()
    print(f"{args.slug}: cleared {n} tag use(s)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", parents=[common])
    rec.add_argument("--slug", required=True)
    rec.add_argument("--date", required=True)
    rec.add_argument("--tags", required=True)
    rec.add_argument("--csv", help="path of the pins.csv this record belongs to")
    rec.set_defaults(func=cmd_record)

    av = sub.add_parser("avoid", parents=[common])
    av.add_argument("--slug", required=True)
    av.add_argument("--candidates", required=True)
    av.add_argument("--take", type=int, default=5)
    av.set_defaults(func=cmd_avoid)

    st = sub.add_parser("stats", parents=[common])
    st.add_argument("--slug")
    st.set_defaults(func=cmd_stats)

    rs = sub.add_parser("reset", parents=[common])
    rs.add_argument("--slug", required=True)
    rs.add_argument("--yes", action="store_true")
    rs.set_defaults(func=cmd_reset)

    args = ap.parse_args(argv)
    return args.func(args, open_db())


if __name__ == "__main__":
    sys.exit(main())
