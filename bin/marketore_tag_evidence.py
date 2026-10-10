#!/usr/bin/env python3
"""Batch tag evidence lookup for the Marketore Fonts census."""

from __future__ import annotations

import argparse
import json
import sqlite3
import math
from pathlib import Path

DEFAULT_DB = Path("outputs/research/marketore-live-collector/marketore.db")


def median(values):
    values = sorted(x for x in values if x is not None)
    if not values:
        return None
    n = len(values)
    return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2


def evaluate(con, tag, fit_score=None):
    rows = con.execute("""SELECT i.product_id,i.downloads,i.designer_id,i.subcategory
      FROM item_tags t JOIN items i ON i.product_id=t.product_id WHERE lower(t.tag)=lower(?)""", (tag,)).fetchall()
    downloads = [r[1] for r in rows if r[1] is not None]
    catalog_total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0] or 1
    designer_total = con.execute("SELECT COUNT(DISTINCT designer_id) FROM items").fetchone()[0] or 1
    category_total = con.execute("SELECT COUNT(DISTINCT subcategory) FROM items WHERE subcategory IS NOT NULL").fetchone()[0] or 1
    max_downloads = con.execute("""SELECT MAX(total_downloads) FROM (
      SELECT t.tag, SUM(COALESCE(i.downloads, 0)) AS total_downloads
      FROM item_tags t JOIN items i ON i.product_id=t.product_id GROUP BY t.tag
    )""").fetchone()[0] or 1
    catalog_matches = len(rows)
    designers = len({r[2] for r in rows if r[2]})
    categories = len({r[3] for r in rows if r[3]})
    total_downloads = sum(downloads)
    coverage_score = math.log1p(catalog_matches) / math.log1p(catalog_total)
    diversity_score = math.log1p(designers) / math.log1p(designer_total)
    category_score = min(categories / category_total, 1.0)
    engagement_score = math.log1p(total_downloads) / math.log1p(max_downloads)
    evidence_score = (0.40 * coverage_score + 0.35 * diversity_score +
                      0.20 * category_score + 0.05 * engagement_score)
    result = {
        "tag": tag,
        "catalog_matches": catalog_matches,
        "designer_matches": designers,
        "category_matches": categories,
        "subcategory_matches": categories,
        "downloads_total": total_downloads,
        "downloads_median": median(downloads),
        "downloads_average": sum(downloads) / len(downloads) if downloads else None,
        "coverage_score": round(coverage_score, 4),
        "diversity_score": round(diversity_score, 4),
        "category_score": round(category_score, 4),
        "engagement_score": round(engagement_score, 4),
        "evidence_score": round(evidence_score, 4),
        "fit_score": fit_score,
        "evidence": "catalog coverage and public engagement only",
        "product_fit": "PENDING",
        "decision": "PENDING",
    }
    result["selection_score"] = (round(0.50 * fit_score + 0.50 * evidence_score, 4)
                                  if fit_score is not None else None)
    result["score_formula"] = ("0.50*fit + 0.20*coverage + 0.175*designer_diversity + "
                                "0.10*category + 0.025*engagement")
    return result


def main():
    parser = argparse.ArgumentParser(description="Marketore tag evidence")
    parser.add_argument("tags", nargs="*")
    parser.add_argument("-f", "--file", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fit", action="append", default=[], metavar="TAG=SCORE",
                        help="seller/product-fit score from 0 to 1; repeat per tag")
    args = parser.parse_args()
    tags = list(args.tags)
    if args.file:
        tags.extend(line.strip() for line in args.file.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#"))
    tags = list(dict.fromkeys(tags))
    if not tags:
        parser.error("provide tags or --file")
    con = sqlite3.connect(args.db)
    fit_scores = {}
    for value in args.fit:
        if "=" not in value:
            parser.error("--fit must use TAG=SCORE")
        fit_tag, raw_score = value.rsplit("=", 1)
        try:
            score = float(raw_score)
        except ValueError:
            parser.error(f"invalid fit score: {raw_score}")
        if not 0 <= score <= 1:
            parser.error("fit scores must be between 0 and 1")
        fit_scores[fit_tag.casefold()] = score
    rows = [evaluate(con, tag, fit_scores.get(tag.casefold())) for tag in tags]
    con.close()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print("| Tag | Catalog matches | Designers | Categories | Evidence score | Selection score | Decision |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for row in rows:
        print(f"| `{row['tag']}` | {row['catalog_matches']} | {row['designer_matches']} | {row['category_matches']} | {row['evidence_score']:.4f} | {row['selection_score'] if row['selection_score'] is not None else 'FIT REQUIRED'} | PENDING |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
