#!/usr/bin/env python3
"""Create a product-level DLsite keyword evidence and decision sheet.

The frozen DB supplies the numeric evidence. Product fit and final selection
remain explicit agent decisions instead of being inferred from lift alone.

Usage:
  python3 bin/dlsite_keyword_batch.py \
    --product "Example Font" \
    --slug example-font \
    --candidates candidates.txt \
    --out outputs/dlsite/.research/example-font-keywords.md
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlsite_tag_evidence import (  # noqa: E402
    DEFAULT_BANK,
    DEFAULT_DB,
    evaluate_keyword,
    load_bank_map,
)


def read_candidates(path: Path) -> list[str]:
    candidates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            candidates.append(value)
    return list(dict.fromkeys(candidates))


def build_report(product: str, slug: str, candidates: list[str], results: list[dict]) -> str:
    lines = [
        f"# DLsite Keyword Batch — {product}",
        "",
        f"- Product slug: `{slug}`",
        "- Evidence source: frozen `outputs/research/dlsite-live-collector/dlsite.db`",
        "- Interpretation: average-sales lift is catalog association, not search volume or a sales forecast.",
        "- Selection rule: the agent must complete Product Fit and Decision; numeric PASS alone does not select a keyword.",
        "",
        "## Evidence And Decisions",
        "",
        "| Keyword | Verdict | TOL matches | Font matches | Median sales | Avg sales | Font avg sales | Avg lift | Font lift | Median favs | Tier | Activity | Evidence role | Product fit reason | Decision |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for result in results:
        fit = "[agent to complete]"
        decision = "PENDING"
        lines.append(
            "| {keyword} | {verdict} | {matches_total} | {matches_fonts} | "
            "{median_sales:.0f} | {avg_sales:.2f} | {font_avg_sales:.2f} | "
            "{sales_lift:.2f}x | {font_sales_lift:.2f}x | {median_favs:.0f} | "
            "{evidence_tier} | {activity} | {evidence_role} | {fit} | {decision} |".format(
                **result,
                fit=fit,
                decision=decision,
            )
        )
    lines.extend(
        [
            "",
            "## Agent Decision Rules",
            "",
            "- Select only terms with a direct product-fit reason and a usable CLI verdict.",
            "- Broad creator terms may be selected as adjacent-audience evidence even when font matches are zero, but label them as audience evidence only.",
            "- Require direct font evidence for font-type/style claims; do not convert broad TOL sales lift into font demand.",
            "- Keep descriptive low-activity terms only when they accurately identify the product.",
            "- Reject terms that are mathematically strong but unrelated to the font's actual use.",
            "- Never describe coverage, lift, median sales, or favorites as search volume, demand, conversion, or guaranteed sales.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a DLsite product keyword decision sheet")
    parser.add_argument("--product", required=True, help="Product name")
    parser.add_argument("--slug", required=True, help="Product slug")
    parser.add_argument("--candidates", required=True, type=Path, help="One candidate keyword per line")
    parser.add_argument("--out", required=True, type=Path, help="Markdown decision-sheet path")
    parser.add_argument("--db", default=DEFAULT_DB, type=Path)
    parser.add_argument("--bank", default=DEFAULT_BANK, type=Path)
    args = parser.parse_args()

    if not args.candidates.is_file():
        parser.error(f"candidate file does not exist: {args.candidates}")
    if not args.db.is_file():
        parser.error(f"database does not exist: {args.db}")

    candidates = read_candidates(args.candidates)
    if not candidates:
        parser.error("candidate file contains no keywords")

    connection = sqlite3.connect(args.db)
    bank_map = load_bank_map(args.bank)
    try:
        results = [evaluate_keyword(connection, bank_map, keyword) for keyword in candidates]
    finally:
        connection.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_report(args.product, args.slug, candidates, results), encoding="utf-8")
    print(f"[PASS] wrote {args.out} ({len(results)} unique candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
