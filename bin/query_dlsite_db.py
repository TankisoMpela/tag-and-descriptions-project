#!/usr/bin/env python3
"""Run SQL and Market Intelligence probes against the DLsite SQLite DB.

Mirrors query_booth_db.py for DLsite Tools/Accessories & Fonts data.

Usage:
  python3 bin/query_dlsite_db.py "SELECT product_id, title, sales_count, favorites_count, price_jpy FROM items ORDER BY sales_count DESC LIMIT 10;"
  python3 bin/query_dlsite_db.py --competitors "ファンタジー"
  python3 bin/query_dlsite_db.py --check-keywords "同人誌,漫画,ゲーム制作,書体,フォント"
  python3 bin/query_dlsite_db.py --suggest-keywords "手書き"
  python3 bin/query_dlsite_db.py --pricing "同人誌"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("outputs/research/dlsite-live-collector/dlsite.db")


def print_table(cols, rows, out):
    if not cols:
        return
    widths = [len(str(c)) for c in cols]
    for r in rows:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], len(_fmt(v)))
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print(sep, file=out)
    print("| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols)) + " |", file=out)
    print(sep, file=out)
    for r in rows:
        print("| " + " | ".join(_fmt(v).ljust(widths[i]) for i, v in enumerate(r)) + " |", file=out)
    print(sep, file=out)
    print(f"{len(rows)} rows", file=out)


def _fmt(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)


def _probe_competitors(con, keyword, max_age=3650, limit=8, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        SELECT i.product_id, i.title, i.maker_name, i.price_jpy, i.sales_count, i.favorites_count,
               i.published, i.genre, i.file_format, i.description
        FROM items i
        WHERE (i.title LIKE ? OR i.description LIKE ? OR i.genre LIKE ?)
        ORDER BY COALESCE(i.sales_count, 0) DESC, COALESCE(i.favorites_count, 0) DESC
        LIMIT ?
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
    rows = cur.fetchall()

    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(["product_id", "title", "maker", "price", "sales", "favorites", "published", "genre", "format"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
        return

    print(f"\n=== DLsite COMPETITOR LENS: Top Winners for '{keyword}' ===")
    if not rows:
        print("No matching items found in the database.")
        return
    for r in rows:
        pid, title, maker, price, sales, favs, pub, genre, fmt, desc = r
        sales_str = f"{sales} DLs" if sales is not None else "N/A"
        favs_str = f"{favs} favs" if favs is not None else "0 favs"
        print(f"[{pid}] {title}")
        print(f"   Maker: {maker or 'Unknown'} | Price: ¥{price or 0} | Sales: {sales_str} | Favorites: {favs_str}")
        print(f"   Genre: {genre or 'None'} | Format: {fmt or 'None'} | Published: {pub or 'Unknown'}")
        if desc:
            lines = [l.strip() for l in desc.splitlines() if any(k in l for k in ('商用', '利用', '収録', 'フォント', '文字', '個人'))]
            if lines:
                print(f"   Snippet: {lines[0][:110]}")
        print()


def _probe_check_keywords(con, keyword_list_str, as_csv=False):
    keywords = [k.strip() for k in keyword_list_str.split(",") if k.strip()]
    if not keywords:
        print("No keywords provided.")
        return

    cur = con.cursor()
    cur.execute("SELECT AVG(sales_count), AVG(favorites_count) FROM items WHERE sales_count IS NOT NULL;")
    market_avg_sales, market_avg_favs = cur.fetchone()
    market_avg_sales = market_avg_sales or 1.0

    cols = ["Keyword", "Matches", "Font Matches", "Avg Sales", "Sales Lift", "Avg Favs", "Verdict"]
    out_rows = []

    for kw in keywords:
        cur.execute("""
            SELECT 
                COUNT(*) as total_n,
                SUM(CASE WHEN is_font = 1 THEN 1 ELSE 0 END) as font_n,
                AVG(sales_count) as avg_sales,
                AVG(favorites_count) as avg_favs
            FROM items
            WHERE title LIKE ? OR description LIKE ? OR genre LIKE ?;
        """, (f'%{kw}%', f'%{kw}%', f'%{kw}%'))
        r = cur.fetchone()
        n = r[0]
        font_n = r[1]
        avg_s = r[2] or 0.0
        avg_f = r[3] or 0.0
        lift = avg_s / market_avg_sales if market_avg_sales else 0.0

        if n == 0:
            verdict = "⚪ UNKNOWN"
        elif n < 3:
            verdict = "⚪ SMALL_N"
        elif lift >= 1.5:
            verdict = "🟢 HIGH-LIFT"
        elif lift < 0.6:
            verdict = "🔴 DRAG_HEAVY"
        else:
            verdict = "🟡 NEUTRAL"

        out_rows.append((kw, n, font_n, f"{avg_s:.1f}", f"{lift:.2f}x", f"{avg_f:.1f}", verdict))

    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        w.writerows(out_rows)
    else:
        print("\n=== DLsite KEYWORD DIAGNOSTIC LENS ===")
        print_table(cols, out_rows, sys.stdout)


def _probe_suggest_keywords(con, keyword, limit=10, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        SELECT ig.genre, count(*) as freq, AVG(i.sales_count) as avg_sales
        FROM item_genres ig
        JOIN items i ON ig.product_id = i.product_id
        WHERE i.title LIKE ? OR i.description LIKE ?
        GROUP BY ig.genre
        ORDER BY avg_sales DESC, freq DESC
        LIMIT ?;
    """, (f'%{keyword}%', f'%{keyword}%', limit))
    rows = cur.fetchall()

    cols = ["Co-occurring Genre/Keyword", "Frequency", "Avg Sales"]
    out_rows = [(r[0], r[1], f"{r[2]:.1f}" if r[2] is not None else "N/A") for r in rows]

    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        w.writerows(out_rows)
    else:
        print(f"\n=== DLsite SUGGESTION LENS: Genres/Keywords matching '{keyword}' ===")
        print_table(cols, out_rows, sys.stdout)


def _probe_pricing(con, keyword, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        SELECT price_jpy
        FROM items
        WHERE (title LIKE ? OR description LIKE ?)
          AND price_jpy > 0
        ORDER BY price_jpy ASC;
    """, (f'%{keyword}%', f'%{keyword}%'))
    prices = [r[0] for r in cur.fetchall()]
    if not prices:
        print(f"No paid items found for '{keyword}'.")
        return
    n = len(prices)
    median = prices[n // 2]
    p25 = prices[int(n * 0.25)]
    p75 = prices[int(n * 0.75)]
    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(["keyword", "n", "p25", "median", "p75", "min", "max"])
        w.writerow([keyword, n, p25, median, p75, prices[0], prices[-1]])
    else:
        print(f"\n=== DLsite PRICING LENS: Paid Benchmark for '{keyword}' (n={n}) ===")
        print(f"  P25: ¥{p25} | Median: ¥{median} | P75: ¥{p75} | Range: ¥{prices[0]} ~ ¥{prices[-1]}")
        print("  DLsite Font Reference: ¥550 (Standard) / ¥1,100~¥1,650 (Bundle/Pro)")


def main():
    ap = argparse.ArgumentParser(description="Query DLsite Database & Market Intelligence Lenses")
    ap.add_argument("sql", nargs="?", help="SQL statement(s)")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB path")
    ap.add_argument("--csv", action="store_true", help="CSV output")
    ap.add_argument("--competitors", help="Find top winners for a keyword/style")
    ap.add_argument("--check-keywords", help="Empirical diagnostic check on comma-separated keywords")
    ap.add_argument("--suggest-keywords", help="Find high-lift genres/keywords for a style")
    ap.add_argument("--pricing", help="Check pricing benchmarks for a keyword")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}. Build it first with bin/build_dlsite_db.py", file=sys.stderr)
        return 1

    con = sqlite3.connect(db_path)

    if args.competitors:
        _probe_competitors(con, args.competitors, as_csv=args.csv)
        con.close()
        return 0

    if getattr(args, "check_keywords", None):
        kw_arg = getattr(args, "check_keywords", None) or getattr(args, "check-keywords", None)
        _probe_check_keywords(con, kw_arg, as_csv=args.csv)
        con.close()
        return 0

    if args.suggest_keywords:
        _probe_suggest_keywords(con, args.suggest_keywords, as_csv=args.csv)
        con.close()
        return 0

    if args.pricing:
        _probe_pricing(con, args.pricing, as_csv=args.csv)
        con.close()
        return 0

    if args.sql:
        cur = con.cursor()
        cur.execute(args.sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        if args.csv:
            w = csv.writer(sys.stdout)
            if cols:
                w.writerow(cols)
            w.writerows(rows)
        else:
            print_table(cols, rows, sys.stdout)
        con.close()
        return 0

    print("No query or lens specified. Pass SQL statement or --help for lenses.", file=sys.stderr)
    con.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
