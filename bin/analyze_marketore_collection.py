#!/usr/bin/env python3
"""Build reusable Marketore catalog-analysis tables and a Markdown report."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path("outputs/research/marketore-live-collector/marketore.db")


def main():
    parser = argparse.ArgumentParser(description="Analyze Marketore Fonts census")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=Path("outputs/research/marketore-collection-analysis.md"))
    args = parser.parse_args()
    if not args.db.exists():
        parser.error(f"database not found: {args.db}")
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS analysis_run;
    DROP TABLE IF EXISTS analysis_tag_stats;
    DROP TABLE IF EXISTS analysis_designer_stats;
    DROP TABLE IF EXISTS analysis_price_bands;
    DROP TABLE IF EXISTS analysis_tag_pairs;
    CREATE TABLE analysis_run(created_at TEXT,total_items INTEGER,total_designers INTEGER,
      tagged_items INTEGER,detail_items INTEGER,total_downloads INTEGER);
    CREATE TABLE analysis_tag_stats(tag TEXT PRIMARY KEY,item_count INTEGER,designer_count INTEGER,
      avg_downloads REAL,median_downloads REAL,total_downloads INTEGER);
    CREATE TABLE analysis_designer_stats(designer_id TEXT PRIMARY KEY,shop TEXT,name TEXT,
      item_count INTEGER,total_downloads INTEGER,avg_downloads REAL,tagged_items INTEGER);
    CREATE TABLE analysis_price_bands(band TEXT PRIMARY KEY,item_count INTEGER,avg_price REAL,
      median_price REAL,avg_downloads REAL);
    CREATE TABLE analysis_tag_pairs(tag_a TEXT,tag_b TEXT,item_count INTEGER,PRIMARY KEY(tag_a,tag_b));
    """)
    total, designers, tagged, details, downloads = cur.execute("""SELECT COUNT(*),COUNT(DISTINCT designer_id),
      COUNT(DISTINCT CASE WHEN EXISTS(SELECT 1 FROM item_tags t WHERE t.product_id=i.product_id) THEN i.product_id END),
      SUM(detail_fetched),COALESCE(SUM(downloads),0) FROM items i""").fetchone()
    cur.execute("INSERT INTO analysis_run VALUES(?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), total, designers, tagged, details, downloads))
    # Calculate medians in Python because SQLite has no portable median aggregate.
    for tag, in cur.execute("SELECT DISTINCT tag FROM item_tags").fetchall():
        vals = [r[0] for r in cur.execute("SELECT i.downloads FROM item_tags t JOIN items i ON i.product_id=t.product_id WHERE t.tag=? AND i.downloads IS NOT NULL ORDER BY i.downloads", (tag,)).fetchall()]
        median = None if not vals else (vals[len(vals)//2] if len(vals)%2 else (vals[len(vals)//2-1]+vals[len(vals)//2])/2)
        row = cur.execute("""SELECT COUNT(DISTINCT t.product_id),COUNT(DISTINCT i.designer_id),AVG(i.downloads),SUM(i.downloads)
          FROM item_tags t JOIN items i ON i.product_id=t.product_id WHERE t.tag=?""", (tag,)).fetchone()
        cur.execute("INSERT INTO analysis_tag_stats VALUES(?,?,?,?,?,?)", (tag, row[0], row[1], row[2], median, row[3]))
    cur.execute("""INSERT INTO analysis_designer_stats
      SELECT d.designer_id,d.shop,d.name,COUNT(i.product_id),COALESCE(SUM(i.downloads),0),AVG(i.downloads),
      COUNT(DISTINCT CASE WHEN EXISTS(SELECT 1 FROM item_tags t WHERE t.product_id=i.product_id) THEN i.product_id END)
      FROM designers d LEFT JOIN items i ON i.designer_id=d.designer_id GROUP BY d.designer_id""")
    bands = [("$0-9",0,9),("$10-19",10,19),("$20-49",20,49),("$50-99",50,99),("$100+",100,10**9)]
    for label, low, high in bands:
        vals = [r[0] for r in cur.execute("SELECT price FROM items WHERE price>=? AND price<=? AND price IS NOT NULL", (low, high)).fetchall()]
        dls = [r[0] for r in cur.execute("SELECT downloads FROM items WHERE price>=? AND price<=? AND downloads IS NOT NULL", (low, high)).fetchall()]
        median = None if not vals else (sorted(vals)[len(vals)//2] if len(vals)%2 else (sorted(vals)[len(vals)//2-1]+sorted(vals)[len(vals)//2])/2)
        cur.execute("INSERT INTO analysis_price_bands VALUES(?,?,?,?,?)", (label,len(vals),sum(vals)/len(vals) if vals else None,median,sum(dls)/len(dls) if dls else None))
    cur.execute("""INSERT INTO analysis_tag_pairs
      SELECT a.tag,b.tag,COUNT(DISTINCT a.product_id) FROM item_tags a JOIN item_tags b
      ON a.product_id=b.product_id AND a.tag<b.tag GROUP BY a.tag,b.tag""")
    con.commit()
    summary = cur.execute("SELECT * FROM analysis_run").fetchone()
    top_tags = cur.execute("SELECT tag,item_count,designer_count,avg_downloads,total_downloads FROM analysis_tag_stats ORDER BY total_downloads DESC NULLS LAST LIMIT 25").fetchall()
    top_designers = cur.execute("SELECT shop,item_count,total_downloads,avg_downloads FROM analysis_designer_stats ORDER BY total_downloads DESC LIMIT 25").fetchall()
    price_rows = cur.execute("SELECT * FROM analysis_price_bands").fetchall()
    metric_note = "Public downloads are available and used below." if summary[5] else "All public download values are 0 in this snapshot; tag ranking falls back to catalog coverage."
    lines = ["# Marketore Fonts Collection Analysis", "", f"Generated: {summary[0]}", "", "## Coverage", f"- Items: {summary[1]}", f"- Designers: {summary[2]}", f"- Tagged items: {summary[3]}", f"- Detail pages: {summary[4]}", f"- Public downloads total: {summary[5]}", "", metric_note, "Download and engagement values are public platform metrics, not revenue or demand.", "", "## Top Tags By Coverage", "", "| Tag | Items | Designers | Avg downloads | Total downloads |", "|---|---:|---:|---:|---:|"]
    lines.extend(f"| {r[0]} | {r[1]} | {r[2]} | {r[3] or 0:.2f} | {r[4] or 0} |" for r in top_tags)
    lines += ["", "## Designers", "", "| Designer | Items | Downloads | Avg downloads |", "|---|---:|---:|---:|"]
    lines.extend(f"| {r[0] or 'Unknown'} | {r[1]} | {r[2] or 0} | {r[3] or 0:.2f} |" for r in top_designers)
    lines += ["", "## Price Bands", "", "| Band | Items | Avg price | Median price | Avg downloads |", "|---|---:|---:|---:|---:|"]
    lines.extend(f"| {r[0]} | {r[1]} | {r[2] or 0:.2f} | {r[3] or 0:.2f} | {r[4] or 0:.2f} |" for r in price_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    con.close()
    print(f"[PASS] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
