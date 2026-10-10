#!/usr/bin/env python3
"""Per-keyword DLsite evidence lookup against the DLsite census DB.

Authoritative keyword evidence gate for Agent 24 (DLsite font specialist).
Reads the frozen DLsite census DB (outputs/research/dlsite-live-collector/dlsite.db)
and reports empirical metrics for candidate keywords:

    - Catalog matches (all TOL products)
    - Font-specific matches (v_fonts)
    - Total / Median / Average sales (dl_count)
    - Average-sales lift vs TOL baseline
    - Median / Average favorites (wishlist_count)
    - Gate Verdict: PASS / LOW-N / REJECT

Usage:
  python3 bin/dlsite_tag_evidence.py "同人誌" "漫画" "ゲーム制作" "書体" "ファンタジー"
  python3 bin/dlsite_tag_evidence.py --json "同人誌" "フォント"
  python3 bin/dlsite_tag_evidence.py -f candidates.txt
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import urllib.parse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlsite_tag_bank import load_bank_map as _load_bank_map  # noqa: E402

DEFAULT_DB = Path("outputs/research/dlsite-live-collector/dlsite.db")
DEFAULT_BANK = Path("outputs/research/dlsite-font-tag-bank.md")

GATE_LIFT = 1.2
GATE_MIN_SALES = 10
LOW_N = 3

BANNED_DRAG = {
    "デザインフォント", "ロゴフォント", "装飾フォント", "フォント素材", "漫画フォント",
    "タイトルフォント", "素材集", "デザイン", "ロゴ", "モダン"
}


def activity_label(cat_n):
    if cat_n is None or cat_n <= 0:
        return "dead/no coverage"
    if cat_n < 5:
        return "low activity"
    return "live"


def median(vals):
    v = sorted([x for x in vals if x is not None])
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 == 1 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def evaluate_keyword(con, bank_map, kw):
    cur = con.cursor()

    # Query all matches
    cur.execute("""
        SELECT sales_count, favorites_count, is_font, price_jpy
        FROM items
        WHERE title LIKE ? OR description LIKE ? OR genre LIKE ?;
    """, (f'%{kw}%', f'%{kw}%', f'%{kw}%'))
    rows = cur.fetchall()

    n_all = len(rows)
    n_fonts = sum(1 for r in rows if r[2] == 1)
    sales = [r[0] for r in rows if r[0] is not None]
    font_sales = [r[0] for r in rows if r[2] == 1 and r[0] is not None]
    favs = [r[1] for r in rows if r[1] is not None]

    tot_sales = sum(sales) if sales else 0
    avg_sales = (tot_sales / len(sales)) if sales else 0.0
    med_sales = median(sales) if sales else 0.0
    font_avg_sales = (sum(font_sales) / len(font_sales)) if font_sales else 0.0

    tot_favs = sum(favs) if favs else 0
    avg_favs = (tot_favs / len(favs)) if favs else 0.0
    med_favs = median(favs) if favs else 0.0

    # Baseline sales
    cur.execute("SELECT AVG(sales_count) FROM items WHERE sales_count IS NOT NULL;")
    base_s = cur.fetchone()[0] or 1.0
    lift = avg_sales / base_s if base_s > 0 else 0.0
    font_lift = font_avg_sales / base_s if base_s > 0 and font_sales else 0.0

    # Check bank
    banked_info = bank_map.get(kw)
    tier = banked_info.get("tier", "Unbanked") if banked_info else "Unbanked"

    # Verdict
    if kw in BANNED_DRAG:
        verdict = "REJECT (BANNED/DRAG)"
        reason = "Rejected in DLsite tag bank (noisy/zero-yield term)"
    elif n_all == 0 and tier == "Unbanked":
        verdict = "REJECT (NO_COVERAGE)"
        reason = "Zero matches across TOL category"
    elif n_all < LOW_N and tier != "High":
        verdict = "LOW-N"
        reason = f"Sample size too small ({n_all} matches)"
    elif lift >= GATE_LIFT or med_sales >= GATE_MIN_SALES or tier == "High":
        verdict = "PASS"
        reason = f"Supported by evidence (lift: {lift:.2f}x, med sales: {med_sales:.0f}, tier: {tier})"
    else:
        verdict = "NEUTRAL"
        reason = "Meets baseline thresholds without strong lift"

    encoded_kw = urllib.parse.quote(kw)
    dlsite_url = f"https://www.dlsite.com/home/fsr/=/work_type/TOL/keyword/{encoded_kw}"

    return {
        "keyword": kw,
        "matches_total": n_all,
        "matches_fonts": n_fonts,
        "total_sales": tot_sales,
        "median_sales": med_sales,
        "avg_sales": avg_sales,
        "font_avg_sales": font_avg_sales,
        "font_sales_sample": len(font_sales),
        "baseline_avg_sales": base_s,
        "sales_lift": lift,
        "font_sales_lift": font_lift,
        "median_favs": med_favs,
        "avg_favs": avg_favs,
        "evidence_tier": tier,
        "activity": activity_label(n_all),
        "verdict": verdict,
        "verdict_reason": reason,
        "evidence_role": "font evidence" if n_fonts else "adjacent audience evidence only",
        "dlsite_search_url": dlsite_url,
    }


def load_bank_map(bank_path: Path):
    """Canonical tier/meaning map from the tag bank (shared parser)."""
    return _load_bank_map(str(bank_path))


def main():
    ap = argparse.ArgumentParser(description="DLsite Per-Keyword Evidence Lookup")
    ap.add_argument("keywords", nargs="*", help="Candidate keywords to evaluate")
    ap.add_argument("-f", "--file", help="File with one candidate keyword per line")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Path to dlsite.db")
    ap.add_argument("--bank", default=str(DEFAULT_BANK), help="Path to dlsite-font-tag-bank.md")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")
    args = ap.parse_args()

    candidates = list(args.keywords)
    if args.file:
        p = Path(args.file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                c = line.strip()
                if c and not c.startswith("#"):
                    candidates.append(c)

    # Preserve caller order while preventing duplicate evidence rows.
    candidates = list(dict.fromkeys(candidates))

    if not candidates:
        print("No keywords provided. Pass keywords as arguments or with -f.", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        return 1

    bank_map = load_bank_map(Path(args.bank))
    con = sqlite3.connect(db_path)

    results = [evaluate_keyword(con, bank_map, kw) for kw in candidates]
    con.close()

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    # Markdown output
    print(f"| Keyword | TOL Matches | Font Matches | Med Sales | Avg Sales Lift | Med Favs | Tier | Activity | Gate Verdict |")
    print(f"|---|---:|---:|---:|---:|---:|---|---|---|")
    for r in results:
        print(f"| `{r['keyword']}` | {r['matches_total']} | {r['matches_fonts']} | {r['median_sales']:.0f} | {r['sales_lift']:.2f}x | {r['median_favs']:.0f} | {r['evidence_tier']} | {r['activity']} | **{r['verdict']}** |")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
