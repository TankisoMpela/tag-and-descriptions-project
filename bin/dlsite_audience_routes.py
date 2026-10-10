#!/usr/bin/env python3
"""Score DLsite adjacent-audience routes for a font listing.

This is not a sales predictor. It combines frozen TOL audience evidence with
the specialist's explicit judgment about whether the supplied font solves a
creator task for that audience.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlsite_tag_evidence import DEFAULT_BANK, DEFAULT_DB, evaluate_keyword, load_bank_map  # noqa: E402


def scale(value: float, maximum: float) -> float:
    return math.log1p(value) / math.log1p(maximum) if maximum > 0 else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Score DLsite adjacent creator audiences")
    parser.add_argument("keywords", nargs="*", help="Audience routes, for example ゲーム制作 漫画")
    parser.add_argument("-f", "--file", type=Path, help="One audience route per line")
    parser.add_argument("--bridge", action="append", default=[], metavar="ROUTE=SCORE",
                        help="manual font-to-task bridge score from 0 to 1")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    routes = list(args.keywords)
    if args.file:
        routes.extend(line.strip() for line in args.file.read_text(encoding="utf-8").splitlines()
                      if line.strip() and not line.startswith("#"))
    routes = list(dict.fromkeys(routes))
    if not routes:
        parser.error("provide audience routes or --file")
    if not args.db.is_file():
        parser.error(f"database does not exist: {args.db}")

    bridges = {}
    for raw in args.bridge:
        if "=" not in raw:
            parser.error("--bridge must use ROUTE=SCORE")
        route, value = raw.rsplit("=", 1)
        try:
            score = float(value)
        except ValueError:
            parser.error(f"invalid bridge score: {value}")
        if not 0 <= score <= 1:
            parser.error("bridge scores must be between 0 and 1")
        bridges[route.casefold()] = score

    con = sqlite3.connect(args.db)
    bank = load_bank_map(args.bank)
    results = [evaluate_keyword(con, bank, route) for route in routes]
    con.close()

    max_matches = max((r["matches_total"] for r in results), default=0)
    max_favs = max((r["median_favs"] for r in results), default=0)
    max_sales = max((r["avg_sales"] for r in results), default=0)
    output = []
    for result in results:
        route = result["keyword"]
        reach = scale(result["matches_total"], max_matches)
        favorites = scale(result["median_favs"], max_favs)
        sales = scale(result["avg_sales"], max_sales)
        font_relevance = min(result["matches_fonts"] / 3, 1.0)
        audience_score = 0.45 * reach + 0.30 * favorites + 0.15 * sales + 0.10 * font_relevance
        bridge = bridges.get(route.casefold())
        route_score = round(0.60 * bridge + 0.40 * audience_score, 4) if bridge is not None else None
        output.append({
            "route": route,
            "matches_total": result["matches_total"],
            "matches_fonts": result["matches_fonts"],
            "median_favorites": result["median_favs"],
            "average_sales": result["avg_sales"],
            "evidence_role": "font evidence" if result["matches_fonts"] else "adjacent audience evidence only",
            "reach_score": round(reach, 4),
            "favorite_score": round(favorites, 4),
            "sales_context_score": round(sales, 4),
            "font_relevance_score": round(font_relevance, 4),
            "audience_score": round(audience_score, 4),
            "bridge_score": bridge,
            "route_score": route_score,
            "recommendation": ("PRIORITIZE" if route_score is not None and route_score >= 0.75
                               else "REVIEW" if route_score is not None and route_score >= 0.50
                               else "BRIDGE REQUIRED" if bridge is None else "WEAK"),
        })

    if args.json:
        import json
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    print("| Audience route | TOL matches | Font matches | Median favs | Evidence role | Bridge | Audience | Route score | Recommendation |")
    print("|---|---:|---:|---:|---|---:|---:|---:|---|")
    for row in output:
        bridge = "REQUIRED" if row["bridge_score"] is None else f'{row["bridge_score"]:.2f}'
        route_score = "REQUIRED" if row["route_score"] is None else f'{row["route_score"]:.4f}'
        print(f'| `{row["route"]}` | {row["matches_total"]} | {row["matches_fonts"]} | '
              f'{row["median_favorites"]:.0f} | {row["evidence_role"]} | {bridge} | '
              f'{row["audience_score"]:.4f} | {route_score} | {row["recommendation"]} |')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
