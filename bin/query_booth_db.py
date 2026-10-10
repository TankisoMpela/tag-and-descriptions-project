#!/usr/bin/env python3
"""Run SQL against the BOOTH SQLite DB and print a readable table.

Usage:
  python3 bin/query_booth_db.py "SELECT title, item_like_count FROM items ORDER BY item_like_count DESC LIMIT 10;"
  python3 bin/query_booth_db.py --db outputs/research/booth-live-collector/booth.db \
      --csv "SELECT tag, count(*) FROM item_tags GROUP BY tag ORDER BY 2 DESC LIMIT 20;"

You can also use the sqlite3 CLI directly:
  sqlite3 outputs/research/booth-live-collector/booth.db "SELECT ...;"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("outputs/research/booth-live-collector/booth.db")


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


def _probe_competitors(con, keyword, max_age=365, limit=6, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        SELECT i.item_id, i.title, i.price_min, i.price_max, i.item_like_count,
               ROUND(v.days_since_publish) as age_days, v.likes_per_day,
               i.tags_json, i.variants_json, i.description
        FROM items i
        JOIN v_age_likes v ON i.item_id = v.item_id
        WHERE i.item_id IN (
            SELECT item_id FROM item_tags WHERE tag = ? COLLATE NOCASE
            UNION
            SELECT item_id FROM items WHERE title LIKE ? ESCAPE '\\'
        )
          AND i.price_min > 0
          AND v.days_since_publish <= ?
        ORDER BY i.item_like_count DESC
        LIMIT ?
    """, (keyword, f'%{keyword}%', max_age, limit))
    rows = cur.fetchall()
    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(["item_id", "title", "price_min", "price_max", "likes", "age_days", "likes_per_day", "tags"])
        for r in rows:
            tags = json.loads(r['tags_json']) if r['tags_json'] else []
            w.writerow([r['item_id'], r['title'], r['price_min'], r['price_max'], r['item_like_count'], int(r['age_days']), r['likes_per_day'], "|".join(tags)])
        return

    print(f"\n=== COMPETITOR LENS: Top Young Paid Winners for '{keyword}' (Age <= {max_age}d) ===")
    if not rows:
        print("No matching paid competitors found in this age window.")
        return
    for r in rows:
        tags = json.loads(r['tags_json']) if r['tags_json'] else []
        tags_fmt = ", ".join(tags[:10]) + ("..." if len(tags) > 10 else "")
        vars_raw = json.loads(r['variants_json']) if r['variants_json'] else []
        var_parts = []
        for v in vars_raw[:3]:
            vn = v.get('variant_name') or 'Single'
            vp = v.get('price_jpy')
            var_parts.append(f"{vn} (¥{vp})")
        var_fmt = " | ".join(var_parts) if var_parts else f"¥{r['price_min']}"
        print(f"[{r['item_id']}] {r['title']}")
        print(f"   Likes: {r['item_like_count']} | Age: {int(r['age_days'])}d ({r['likes_per_day']} l/d) | Price: ¥{r['price_min']}~¥{r['price_max']}")
        print(f"   Variants: {var_fmt}")
        print(f"   Tags ({len(tags)}): {tags_fmt}")
        desc = (r['description'] or "").strip().replace("\r\n", "\n").replace("\n\n", "\n")
        lines = [l for l in desc.splitlines() if any(k in l for k in ('商用', '利用', '収録', 'ライセンス', '個人'))]
        if lines:
            print(f"   Licensing/Context: {lines[0][:100]}")
        print()


def _probe_check_tags(con, tag_list_str, as_csv=False):
    tags = [t.strip() for t in tag_list_str.split(",") if t.strip()]
    if not tags:
        print("No tags provided.")
        return
    banned_set = {
        '名刺', '招待状', '書籍タイトル', 'チラシ', 'バナー', '装丁', '美しいフォント',
        '良いフォント', 'クリーン', 'シンプル', 'display font', 'script font',
        'handcraft', 'lettering', 'typeface', 'OTF', 'OpenType', '日本語フォント',
        '和文', '和文フォント', 'ひらがな', '漢字', 'Premiere pro', '動画編集', 'テロップ',
        '字幕', 'YouTube', 'テンプレート'
    }
    cur = con.cursor()
    placeholders = ",".join("?" for _ in tags)
    cur.execute(f"""
        WITH young_stats AS (
            SELECT item_id, item_like_count,
                   NTILE(4) OVER (ORDER BY item_like_count ASC) as quartile
            FROM items
            WHERE item_like_count IS NOT NULL
              AND (JULIANDAY('2026-09-08') - JULIANDAY(published)) <= 365
        )
        SELECT 
            it.tag,
            count(distinct it.item_id) as total_n,
            AVG(i.item_like_count) as avg_likes,
            SUM(CASE WHEN ys.quartile = 4 THEN 1 ELSE 0 END) * 1.0 / NULLIF(count(distinct ys.item_id), 0) as young_top_pct,
            SUM(CASE WHEN ys.quartile = 1 THEN 1 ELSE 0 END) * 1.0 / NULLIF(count(distinct ys.item_id), 0) as young_bot_pct
        FROM item_tags it
        JOIN items i ON it.item_id = i.item_id
        LEFT JOIN young_stats ys ON it.item_id = ys.item_id
        WHERE it.tag IN ({placeholders})
        GROUP BY it.tag
    """, tags)

    data = {r['tag']: r for r in cur.fetchall()}
    cols = ["Tag", "n (all)", "Top Lift", "Bot Drag", "Verdict"]
    out_rows = []
    for t in tags:
        if t in data:
            r = data[t]
            n = r['total_n']
            top_p = r['young_top_pct'] or 0
            bot_p = r['young_bot_pct'] or 0
            lift = top_p / 0.25 if top_p else 0
            drag = bot_p / 0.25 if bot_p else 0
            if t in banned_set:
                verdict = "🔴 BANNED_DRAG"
            elif n < 10:
                verdict = "⚪ SMALL_N"
            elif lift >= 1.5 and drag < 1.0:
                verdict = "🟢 HIGH-LIFT"
            elif drag >= 1.5 or lift < 0.5:
                verdict = "🔴 DRAG_HEAVY"
            else:
                verdict = "🟡 NEUTRAL"
            out_rows.append((t, n, f"{lift:.2f}x", f"{drag:.2f}x", verdict))
        else:
            out_rows.append((t, 0, "0.00x", "0.00x", "⚪ UNKNOWN_TAG"))

    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        w.writerows(out_rows)
    else:
        print("\n=== TAG DIAGNOSTIC LENS: Candidate Empirical Metrics ===")
        print_table(cols, out_rows, sys.stdout)


def _probe_suggest_tags(con, keyword, limit=12, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        WITH style_items AS (
            SELECT i.item_id
            FROM items i
            JOIN v_age_likes v ON i.item_id = v.item_id
            WHERE i.item_id IN (
                SELECT item_id FROM item_tags WHERE tag = ? COLLATE NOCASE
                UNION
                SELECT item_id FROM items WHERE title LIKE ? ESCAPE '\\'
            )
              AND i.item_like_count >= 125 -- top quartile
        )
        SELECT it.tag, count(*) as freq, atl.lift,
               CASE WHEN tb.tag IS NOT NULL THEN 'Yes' ELSE 'No' END as banked
        FROM item_tags it
        JOIN style_items st ON it.item_id = st.item_id
        LEFT JOIN analysis_tag_lift atl ON it.tag = atl.tag
        LEFT JOIN tag_bank tb ON it.tag = tb.tag
        WHERE it.tag NOT IN ('フォント', 'font', 'fonts', '書体', 'フォント・書体', '文字')
        GROUP BY it.tag
        HAVING freq >= 2
        ORDER BY atl.lift DESC, freq DESC
        LIMIT ?
    """, (f'%{keyword}%', f'%{keyword}%', limit))
    rows = cur.fetchall()
    cols = ["Recommended Tag", "Freq (in style)", "Market Lift", "In Frozen Bank"]
    out_rows = []
    for r in rows:
        lift = f"{r['lift']:.2f}x" if r['lift'] else "—"
        out_rows.append((r['tag'], r['freq'], lift, r['banked']))

    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(cols)
        w.writerows(out_rows)
    else:
        print(f"\n=== STYLE TAG SUGGESTIONS: High-Lift Co-occurring Tags for '{keyword}' ===")
        print_table(cols, out_rows, sys.stdout)


def _probe_pricing(con, keyword, as_csv=False):
    cur = con.cursor()
    cur.execute("""
        SELECT price_min
        FROM items
        WHERE item_id IN (
            SELECT item_id FROM item_tags WHERE tag = ? COLLATE NOCASE
            UNION
            SELECT item_id FROM items WHERE title LIKE ? ESCAPE '\\'
        )
          AND price_min > 0
        ORDER BY price_min ASC
    """, (keyword, f'%{keyword}%'))
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
        w.writerow(["style", "n", "p25", "median", "p75", "min", "max"])
        w.writerow([keyword, n, p25, median, p75, prices[0], prices[-1]])
    else:
        print(f"\n=== PRICING LENS: Paid Font Benchmark for '{keyword}' (n={n}) ===")
        print(f"  P25: ¥{p25} | Median: ¥{median} | P75: ¥{p75} | Range: ¥{prices[0]} ~ ¥{prices[-1]}")
        print("  Standard Strategy: ¥500 (Personal Impulse) / ¥1,500 (Commercial Standard)")


def main():
    ap = argparse.ArgumentParser(description="Query the BOOTH SQLite DB & Market Intelligence Lenses")
    ap.add_argument("sql", nargs="?", help="SQL statement(s). Omit for an interactive REPL.")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB path")
    ap.add_argument("--csv", action="store_true", help="CSV output instead of table")
    ap.add_argument("--competitors", help="Probe 1: Find top young paid competitor listings for a style/keyword")
    ap.add_argument("--check-tags", help="Probe 2: Test candidate tags for sample size, lift, drag, and verdict")
    ap.add_argument("--suggest-tags", help="Probe 3: Suggest high-lift tags that co-occur in top-quartile items for a style")
    ap.add_argument("--pricing", help="Probe 4: Check pricing percentiles and recommendations for a style")
    ap.add_argument("--max-age", type=int, default=365, help="Max product age in days for competitor search (default: 365)")
    ap.add_argument("--limit", type=int, default=6, help="Result limit (default: 6)")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        sys.exit(f"DB not found: {db}\nBuild it first with bin/build_booth_db.py")
    con = sqlite3.connect(str(db))
    try:
        con.execute("PRAGMA cache_size=-64000")
        con.execute("PRAGMA temp_store=MEMORY")
    except sqlite3.Error:
        pass
    con.row_factory = sqlite3.Row

    # Check for dedicated probes first
    if args.competitors:
        _probe_competitors(con, args.competitors, max_age=args.max_age, limit=args.limit, as_csv=args.csv)
        return 0
    if args.check_tags:
        _probe_check_tags(con, args.check_tags, as_csv=args.csv)
        return 0
    if args.suggest_tags:
        _probe_suggest_tags(con, args.suggest_tags, limit=args.limit, as_csv=args.csv)
        return 0
    if args.pricing:
        _probe_pricing(con, args.pricing, as_csv=args.csv)
        return 0

    statements = [args.sql] if args.sql else None

    if statements is None:
        # tiny REPL
        print("BOOTH DB REPL  (Ctrl+D to exit)")
        while True:
            try:
                sql = input("sql> ").strip()
            except EOFError:
                break
            if not sql:
                continue
            if sql.lower() in ("exit", "quit", ".quit"):
                break
            _run(con, sql, args.csv)
    else:
        for s in statements:
            _run(con, s, args.csv)


def _run(con, sql, as_csv):
    stmt = sql.strip().rstrip(";")
    if not stmt:
        return
    cur = con.execute(stmt)
    if cur.description:
        cols = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        if as_csv:
            w = csv.writer(sys.stdout)
            w.writerow(cols)
            w.writerows(rows)
        else:
            print_table(cols, rows, sys.stdout)
    else:
        print(f"done: {cur.rowcount} rows affected")


if __name__ == "__main__":
    raise SystemExit(main())