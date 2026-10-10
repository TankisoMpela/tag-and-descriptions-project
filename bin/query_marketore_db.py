#!/usr/bin/env python3
"""Query the Marketore Fonts SQLite census."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("outputs/research/marketore-live-collector/marketore.db")


def fmt(value):
    return "NULL" if value is None else str(value)


def print_rows(columns, rows, as_csv=False):
    if as_csv:
        writer = csv.writer(sys.stdout)
        writer.writerow(columns)
        writer.writerows(rows)
        return
    widths = [len(str(x)) for x in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(fmt(value)))
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(line)
    print("| " + " | ".join(str(x).ljust(widths[i]) for i, x in enumerate(columns)) + " |")
    print(line)
    for row in rows:
        print("| " + " | ".join(fmt(value).ljust(widths[i]) for i, value in enumerate(row)) + " |")
    print(line)
    print(f"{len(rows)} rows")


def main():
    parser = argparse.ArgumentParser(description="Query Marketore Fonts SQLite")
    parser.add_argument("sql", nargs="?", help="SQL query")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--top-downloads", action="store_true")
    parser.add_argument("--top-designers", action="store_true")
    parser.add_argument("--tag", help="Show products carrying a tag")
    args = parser.parse_args()
    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1
    con = sqlite3.connect(args.db)
    if args.top_downloads:
        args.sql = """SELECT product_id,title,downloads,price,designer_id FROM items
          WHERE downloads IS NOT NULL ORDER BY downloads DESC, title LIMIT 50"""
    elif args.top_designers:
        args.sql = """SELECT d.designer_id,d.shop,d.name,COUNT(i.product_id) AS products,
          COALESCE(SUM(i.downloads),0) AS downloads
          FROM designers d JOIN items i ON i.designer_id=d.designer_id
          GROUP BY d.designer_id ORDER BY downloads DESC, products DESC LIMIT 50"""
    elif args.tag:
        args.sql = """SELECT i.product_id,i.title,i.downloads,i.price,i.designer_id
          FROM item_tags t JOIN items i ON i.product_id=t.product_id
          WHERE lower(t.tag)=lower(?) ORDER BY COALESCE(i.downloads,0) DESC"""
        cur = con.execute(args.sql, (args.tag,))
        rows = cur.fetchall()
        print_rows([x[0] for x in cur.description], rows, args.csv)
        con.close()
        return 0
    if not args.sql:
        args.sql = "SELECT product_id,title,downloads,price,designer_id FROM items ORDER BY COALESCE(downloads,0) DESC LIMIT 20"
    cur = con.execute(args.sql)
    if cur.description:
        print_rows([x[0] for x in cur.description], cur.fetchall(), args.csv)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
