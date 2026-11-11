#!/usr/bin/env python3
"""Per-font Pinterest ledger — stops pins cannibalizing each other.

outputs/research/pinterest-tags.sqlite holds drafts and confirmed imports.
`prepared_pins` holds the latest assembled drafts; `pins` holds the full text
of rows confirmed accepted by Buffer/Pinterest. `tag_uses` counts their
keywords, and `pinned_runs` drives the 14-day re-pin exclusion. Assembly alone
does not update history; use `mark-imported` only after the destination accepts
the rows. This records import/queue acceptance, not publication.

Usage:
  python3 bin/pinterest_tag_ledger.py record --slug quiet-acre --date 2026-10-10 --tags "boho script font, wedding signage font"
  python3 bin/pinterest_tag_ledger.py mark-imported --date 2026-10-11 --slugs quiet-acre another-font
  python3 bin/pinterest_tag_ledger.py avoid --slug quiet-acre --candidates "boho script font, wedding signage font, ..." --take 5
  python3 bin/pinterest_tag_ledger.py history [--slug quiet-acre] [--limit 3] [--full]
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
CREATE TABLE IF NOT EXISTS pins (
    font_slug   TEXT NOT NULL,
    run_date    TEXT NOT NULL,
    title       TEXT,
    description TEXT,
    alt         TEXT,
    keywords    TEXT,
    board       TEXT,
    image_url   TEXT,
    link        TEXT,
    PRIMARY KEY (font_slug, run_date)
);
CREATE TABLE IF NOT EXISTS prepared_pins (
    font_slug   TEXT NOT NULL,
    run_date    TEXT NOT NULL,
    title       TEXT,
    description TEXT,
    alt         TEXT,
    keywords    TEXT,
    board       TEXT,
    image_url   TEXT,
    link        TEXT,
    csv_path    TEXT,
    PRIMARY KEY (font_slug, run_date)
);
CREATE INDEX IF NOT EXISTS idx_tag_uses ON tag_uses (font_slug, tag);
"""


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
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


def record_pin(con: sqlite3.Connection, *, slug: str, date: str, title: str,
               description: str, alt: str, keywords: list[str], board: str,
               image_url: str, link: str) -> None:
    """Keep the full text of a confirmed imported pin for future rotation."""
    con.execute("""
        INSERT OR REPLACE INTO pins
            (font_slug, run_date, title, description, alt, keywords, board,
             image_url, link)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (slug, date, title, description, alt, ", ".join(keywords), board,
          image_url, link))


def prepare_pin(con: sqlite3.Connection, *, slug: str, date: str, title: str,
                description: str, alt: str, keywords: list[str], board: str,
                image_url: str, link: str, csv_path: str) -> None:
    """Keep the latest assembled draft without treating it as imported."""
    con.execute("""
        INSERT OR REPLACE INTO prepared_pins
            (font_slug, run_date, title, description, alt, keywords, board,
             image_url, link, csv_path)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (slug, date, title, description, alt, ", ".join(keywords), board,
          image_url, link, csv_path))


def font_pins(con: sqlite3.Connection, slug: str,
              limit: int | None = None) -> list[dict]:
    """This font's past pins, newest first — the anti-cannibalization record."""
    sql = "SELECT * FROM pins WHERE font_slug=? ORDER BY run_date DESC"
    if limit:
        sql += " LIMIT ?"
        return [dict(r) for r in con.execute(sql, (slug, limit))]
    return [dict(r) for r in con.execute(sql, (slug,))]


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


def cmd_mark_imported(args, con: sqlite3.Connection) -> int:
    """Record confirmed Buffer/Pinterest imports in pin history."""
    slugs = list(dict.fromkeys(args.slugs))
    if not slugs:
        sys.exit("error: supply at least one --slugs value")

    prepared: dict[str, sqlite3.Row] = {}
    already: set[str] = set()
    missing: list[str] = []
    for slug in slugs:
        if con.execute("SELECT 1 FROM pins WHERE font_slug=? AND run_date=?",
                       (slug, args.date)).fetchone():
            already.add(slug)
            continue
        row = con.execute(
            "SELECT * FROM prepared_pins WHERE font_slug=? AND run_date=?",
            (slug, args.date)).fetchone()
        if row is None:
            missing.append(slug)
        else:
            prepared[slug] = row
    if missing:
        sys.exit(f"error: no prepared pin for {args.date}: {', '.join(missing)}")

    for slug, row in prepared.items():
        record_pin(
            con, slug=slug, date=args.date, title=row["title"] or "",
            description=row["description"] or "", alt=row["alt"] or "",
            keywords=split_tags(row["keywords"] or ""), board=row["board"] or "",
            image_url=row["image_url"] or "", link=row["link"] or "")
        con.execute(
            "INSERT OR IGNORE INTO pinned_runs (font_slug, run_date, csv_path) VALUES (?,?,?)",
            (slug, args.date, row["csv_path"]))
        con.executemany(
            "INSERT INTO tag_uses (font_slug, tag, run_date) VALUES (?,?,?)",
            [(slug, tag, args.date) for tag in split_tags(row["keywords"] or "")])
    con.commit()
    result = {"date": args.date, "recorded": sorted(prepared),
              "already_recorded": sorted(already)}
    print(json.dumps(result, indent=2) if args.json else
          f"{args.date}: recorded {len(prepared)} imported pin(s); "
          f"{len(already)} already recorded. This confirms import/queue acceptance, not publication.")
    return 0


def cmd_avoid(args, con: sqlite3.Connection) -> int:
    candidates = split_tags(args.candidates)
    if not candidates:
        sys.exit("error: no candidates given")
    used = font_counts(con, args.slug)
    global_used = dict(con.execute("SELECT tag, COUNT(*) FROM tag_uses GROUP BY tag"))
    # Never-used for this font first; within each tier, prefer phrases less
    # saturated across the full account history. Alphabetical keeps ties stable.
    ranked = sorted(candidates, key=lambda t: (used.get(t, 0), global_used.get(t, 0), t))
    take = ranked[: args.take]
    out = {"slug": args.slug, "take": args.take, "selected": take,
            "font_usage": {t: used.get(t, 0) for t in candidates},
            "global_usage": {t: global_used.get(t, 0) for t in candidates}}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print("\n".join(take))
    return 0


def cmd_history(args, con: sqlite3.Connection) -> int:
    """What this font has already been pinned with, and when."""
    slugs = [args.slug] if args.slug else [
        r[0] for r in con.execute("SELECT DISTINCT font_slug FROM pins ORDER BY font_slug")
    ]
    if not slugs:
        print("(no pins recorded yet — every font is on its first run)")
        return 0
    report = []
    for slug in slugs:
        pins = font_pins(con, slug, args.limit)
        runs = [r[0] for r in con.execute(
            "SELECT run_date FROM pinned_runs WHERE font_slug=? ORDER BY run_date DESC",
            (slug,))]
        report.append({"slug": slug, "pin_count": len(pins),
                       "run_dates": runs, "history": pins})
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    for r in report:
        print(f"\n{r['slug']} — {r['pin_count']} pin(s) recorded"
              f"; run dates: {', '.join(r['run_dates']) or 'none'}")
        for p in r["history"]:
            print(f"  {p['run_date']}  [{p['board']}]  {p['title']}")
            if args.full:
                print(f"      description: {p['description']}")
                print(f"      alt:         {p['alt']}")
                print(f"      keywords:    {p['keywords']}")
                print(f"      image:       {p['image_url']}")
                print(f"      link:        {p['link']}")
        if not r["history"]:
            used = font_counts(con, r["slug"])
            for t, c in sorted(used.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
                print(f"  {c}x  {t}")
            if used:
                print("  (pin text predates the history table — keywords shown)")
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
    p = con.execute("SELECT COUNT(*) FROM pins WHERE font_slug=?", (args.slug,)).fetchone()[0]
    d = con.execute("SELECT COUNT(*) FROM prepared_pins WHERE font_slug=?", (args.slug,)).fetchone()[0]
    if not args.yes:
        sys.exit(f"error: {args.slug} has {n} tag use(s), {p} imported pin(s), and {d} draft(s) — pass --yes to clear them")
    con.execute("DELETE FROM tag_uses WHERE font_slug=?", (args.slug,))
    con.execute("DELETE FROM pinned_runs WHERE font_slug=?", (args.slug,))
    con.execute("DELETE FROM pins WHERE font_slug=?", (args.slug,))
    con.execute("DELETE FROM prepared_pins WHERE font_slug=?", (args.slug,))
    con.commit()
    print(f"{args.slug}: cleared {n} tag use(s), {p} imported pin(s), and {d} draft(s)")
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

    imported = sub.add_parser("mark-imported", parents=[common])
    imported.add_argument("--date", required=True)
    imported.add_argument("--slugs", nargs="+", required=True,
                          help="font slugs whose rows Buffer/Pinterest accepted")
    imported.set_defaults(func=cmd_mark_imported)

    av = sub.add_parser("avoid", parents=[common])
    av.add_argument("--slug", required=True)
    av.add_argument("--candidates", required=True)
    av.add_argument("--take", type=int, default=5)
    av.set_defaults(func=cmd_avoid)

    st = sub.add_parser("stats", parents=[common])
    st.add_argument("--slug")
    st.set_defaults(func=cmd_stats)

    hi = sub.add_parser("history", parents=[common])
    hi.add_argument("--slug")
    hi.add_argument("--limit", type=int, default=5,
                    help="most recent pins per font (default 5)")
    hi.add_argument("--full", action="store_true",
                    help="also print description, alt, keywords, image and link")
    hi.set_defaults(func=cmd_history)

    rs = sub.add_parser("reset", parents=[common])
    rs.add_argument("--slug", required=True)
    rs.add_argument("--yes", action="store_true")
    rs.set_defaults(func=cmd_reset)

    args = ap.parse_args(argv)
    return args.func(args, open_db())


if __name__ == "__main__":
    sys.exit(main())
