#!/usr/bin/env python3
"""
analyze_dlsite_collection.py — analyze DLsite Tools/Accessories & Fonts collection.

Extracts sales and ranking signals, computes correlations of price/description/age
vs sales (dl_count) and favorites (wishlist_count), calculates keyword and genre lift
in top selling quartiles, and writes both a markdown findings report and structured
analysis_* tables into dlsite.db.

Usage:
  python3 bin/analyze_dlsite_collection.py \
    --db outputs/research/dlsite-live-collector/dlsite.db \
    --bank outputs/research/dlsite-font-tag-bank.md \
    --out outputs/research/dlsite-collection-analysis-2026-09-09.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlsite_tag_bank import parse_tag_bank as _parse_tag_bank  # noqa: E402

DEFAULT_DB = Path("outputs/research/dlsite-live-collector/dlsite.db")
DEFAULT_BANK = Path("outputs/research/dlsite-font-tag-bank.md")


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    if den == 0:
        return None, n
    return num / den, n


def spearman(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n

    def _rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx = _rank(xs)
    ry = _rank(ys)
    return pearson(rx, ry)


def median(vals):
    v = [x for x in vals if x is not None]
    return statistics.median(v) if v else None


def main():
    ap = argparse.ArgumentParser(description="Analyze DLsite Tools/Accessories Collection")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Path to dlsite.db")
    ap.add_argument("--bank", default=str(DEFAULT_BANK), help="Path to dlsite-font-tag-bank.md")
    ap.add_argument("--out", default=None, help="Output markdown report path")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        return 1

    out_path = Path(args.out) if args.out else Path(f"outputs/research/dlsite-collection-analysis-{date.today().isoformat()}.md")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # 1. Overview counts
    cur.execute("SELECT count(*), sum(case when is_font=1 then 1 else 0 end), sum(detail_fetched) FROM items;")
    total_items, total_fonts, total_detailed = cur.fetchone()
    total_fonts = total_fonts or 0

    cur.execute("SELECT count(distinct maker_id) FROM items WHERE maker_id != '';")
    total_makers = cur.fetchone()[0]

    cur.execute("SELECT min(published), max(published) FROM items WHERE published != '';")
    min_pub, max_pub = cur.fetchone()

    # 2. Sales and Favorites distributions
    cur.execute("SELECT sales_count FROM items WHERE sales_count IS NOT NULL;")
    all_sales = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT favorites_count FROM items WHERE favorites_count IS NOT NULL;")
    all_favs = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT price_jpy FROM items WHERE price_jpy IS NOT NULL AND price_jpy > 0;")
    all_prices = [r[0] for r in cur.fetchall()]

    sales_med = median(all_sales) if all_sales else 0
    favs_med = median(all_favs) if all_favs else 0
    price_med = median(all_prices) if all_prices else 0

    # 3. Correlations: price, desc_length, age vs sales
    cur.execute("""
        SELECT price_jpy, description_length, 
               julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published) as age_days,
               sales_count, favorites_count
        FROM items
        WHERE sales_count IS NOT NULL AND published != '' AND published IS NOT NULL;
    """)
    corr_data = cur.fetchall()

    features_out = []
    if len(corr_data) >= 5:
        prices = [r[0] or 0 for r in corr_data]
        descs = [r[1] or 0 for r in corr_data]
        ages = [r[2] or 0 for r in corr_data]
        sales = [r[3] or 0 for r in corr_data]
        favs = [r[4] or 0 for r in corr_data]

        for feat_name, feat_vals in [("price_jpy", prices), ("desc_length", descs), ("age_days", ages)]:
            p_s, _ = pearson(feat_vals, sales)
            s_s, _ = spearman(feat_vals, sales)
            features_out.append(("sales_count", feat_name, len(sales), p_s, s_s))

        for feat_name, feat_vals in [("price_jpy", prices), ("desc_length", descs), ("age_days", ages)]:
            p_f, _ = pearson(feat_vals, favs)
            s_f, _ = spearman(feat_vals, favs)
            features_out.append(("favorites_count", feat_name, len(favs), p_f, s_f))

    # 4. Price bands
    price_bands_def = [
        ("¥0 (Free)", 0, 0),
        ("¥1~¥500 (Impulse)", 1, 500),
        ("¥501~¥1,000 (Standard)", 501, 1000),
        ("¥1,001~¥2,000 (Pro/Bundle)", 1001, 2000),
        ("¥2,001+ (High)", 2001, 9999999),
    ]
    price_bands_data = []
    for label, pmin, pmax in price_bands_def:
        cur.execute("""
            SELECT count(*), AVG(sales_count), AVG(favorites_count)
            FROM items
            WHERE price_jpy >= ? AND price_jpy <= ?;
        """, (pmin, pmax))
        n, a_s, a_f = cur.fetchone()
        price_bands_data.append((label, n, a_s or 0.0, a_f or 0.0))

    # 5. Tag / Keyword analysis against tag bank
    bank_path = Path(args.bank)
    bank_keywords = _parse_tag_bank(bank_path)
    bank_keywords = [r["keyword"] for r in bank_keywords]

    # Top selling items quartile threshold
    cur.execute("SELECT sales_count FROM items WHERE sales_count IS NOT NULL ORDER BY sales_count ASC;")
    sales_sorted = [r[0] for r in cur.fetchall()]
    top_quartile_thresh = sales_sorted[int(len(sales_sorted) * 0.75)] if len(sales_sorted) >= 4 else (sales_med or 1)

    tag_lift_data = []
    test_keywords = list(dict.fromkeys(bank_keywords + ["フォント", "書体", "欧文", "英字", "手書き", "同人誌", "漫画", "ゲーム制作", "タイトル", "見出し", "ロゴ", "ファンタジー"]))

    for kw in test_keywords:
        cur.execute("""
            SELECT 
                COUNT(*) as total_n,
                SUM(CASE WHEN sales_count >= ? THEN 1 ELSE 0 END) as top_n,
                AVG(sales_count) as avg_sales
            FROM items
            WHERE title LIKE ? OR description LIKE ? OR genre LIKE ?;
        """, (top_quartile_thresh, f'%{kw}%', f'%{kw}%', f'%{kw}%'))
        r = cur.fetchone()
        n = r[0]
        top_n = r[1] or 0
        avg_s = r[2] or 0.0
        cov_pct = (n / total_items * 100.0) if total_items else 0.0
        # Lift = (top_n / n) / 0.25
        lift = ((top_n / n) / 0.25) if n > 0 else 0.0
        tag_lift_data.append((kw, n, cov_pct, lift, avg_s))

    # Write tables to SQLite database
    cur.execute("DROP TABLE IF EXISTS analysis_run;")
    cur.execute("""
        CREATE TABLE analysis_run (
            created_at TEXT,
            total_items INTEGER,
            total_fonts INTEGER,
            total_makers INTEGER,
            sales_median REAL,
            favorites_median REAL,
            price_median REAL
        );
    """)
    cur.execute("""
        INSERT INTO analysis_run VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (datetime.now().isoformat(), total_items, total_fonts, total_makers, sales_med, favs_med, price_med))

    cur.execute("DROP TABLE IF EXISTS analysis_features;")
    cur.execute("""
        CREATE TABLE analysis_features (
            metric TEXT,
            feature TEXT,
            n INTEGER,
            pearson REAL,
            spearman REAL
        );
    """)
    for row in features_out:
        cur.execute("INSERT INTO analysis_features VALUES (?, ?, ?, ?, ?);", row)

    cur.execute("DROP TABLE IF EXISTS analysis_price_bands;")
    cur.execute("""
        CREATE TABLE analysis_price_bands (
            band TEXT,
            item_count INTEGER,
            avg_sales REAL,
            avg_favorites REAL
        );
    """)
    for row in price_bands_data:
        cur.execute("INSERT INTO analysis_price_bands VALUES (?, ?, ?, ?);", row)

    cur.execute("DROP TABLE IF EXISTS analysis_tag_lift;")
    cur.execute("""
        CREATE TABLE analysis_tag_lift (
            keyword TEXT,
            matches INTEGER,
            coverage_pct REAL,
            lift REAL,
            avg_sales REAL
        );
    """)
    for row in tag_lift_data:
        cur.execute("INSERT INTO analysis_tag_lift VALUES (?, ?, ?, ?, ?);", row)

    con.commit()
    con.close()

    # Generate Markdown Report
    lines = []
    def out(s=""):
        lines.append(s)

    out(f"# DLsite Tools/Accessories Collection Analysis — {date.today().isoformat()}")
    out()
    out(f"- Database source: `{db_path}`")
    out(f"- Total catalog items indexed: **{total_items}**")
    out(f"- Verified font products: **{total_fonts}**")
    out(f"- Unique circles / makers: **{total_makers}**")
    out(f"- Publication date range: `{min_pub or 'N/A'}` ~ `{max_pub or 'N/A'}`")
    out(f"- Market median sales: **{sales_med} DLs** | Median favorites: **{favs_med} favs** | Median price: **¥{price_med}**")
    out()
    out("---")
    out()
    out("## 1. Feature Correlations (Sales & Favorites)")
    out()
    out("| Metric | Feature | Sample (n) | Pearson r | Spearman rho | Direction |")
    out("|---|---|---|---|---|---|")
    if features_out:
        for m, f, n, pr, sp in features_out:
            pr_s = f"{pr:.3f}" if pr is not None else "N/A"
            sp_s = f"{sp:.3f}" if sp is not None else "N/A"
            dir_str = "Positive" if (sp or 0) > 0.15 else ("Negative" if (sp or 0) < -0.15 else "Neutral")
            out(f"| {m} | {f} | {n} | {pr_s} | {sp_s} | {dir_str} |")
    else:
        out("| Insufficient data for feature correlation | - | - | - | - | - |")
    out()
    out("---")
    out()
    out("## 2. Price Band Performance")
    out()
    out("| Price Band | Item Count | Avg Sales (DLs) | Avg Favorites | Strategy Note |")
    out("|---|---|---|---|---|")
    for band, n, as_, af_ in price_bands_data:
        out(f"| {band} | {n} | {as_:.1f} | {af_:.1f} | DLsite benchmark |")
    out()
    out("---")
    out()
    out("## 3. High-Confidence Keyword & Genre Lift (Top 25% Sales Cohort)")
    out()
    out("| Keyword / Genre | Matches (n) | Catalog Cov % | Sales Lift | Avg Sales (DLs) | Verdict |")
    out("|---|---|---|---|---|---|")
    for kw, n, cov, lift, avg_s in sorted(tag_lift_data, key=lambda x: -x[3]):
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
        out(f"| `{kw}` | {n} | {cov:.1f}% | {lift:.2f}x | {avg_s:.1f} | {verdict} |")
    out()
    out("---")
    out()
    out("*Generated by bin/analyze_dlsite_collection.py*")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Analysis written to: {out_path}")
    print(f"Analysis tables written to: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
