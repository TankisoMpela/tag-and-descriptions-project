#!/usr/bin/env python3
"""Canonical parser for the frozen DLsite font tag bank.

The bank (outputs/research/dlsite-font-tag-bank.md) contains multiple markdown
tables. Only section 5.x tables are keyword tables:

    | Keyword | Meaning | Evidence tier | Notes |

Sections 1-3, 6, 8, 10 are prose/bullets. Sections 4 (search query counts),
7 (observed competitor products), and 9 (noisy/rejected keywords) are tables
that are NOT keyword candidates and must never leak into the keyword universe.

All DLsite tooling must parse the bank through this single function so the
keyword universe stays stable across the DB builder, the analyzer, and the
per-keyword evidence gate.
"""

from __future__ import annotations

import re
from pathlib import Path


def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_tag_bank(bank_path):
    """Return only valid keyword rows from section 5.x of the tag bank.

    Each row: {keyword, meaning, evidence_tier, category, notes}
    """
    rows = []
    if not isinstance(bank_path, Path):
        bank_path = Path(bank_path)
    if not bank_path.exists():
        return rows

    current_category = "General"
    in_keyword_section = False
    for line in bank_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        # Heading detection (only plain '#' headings, not table pipes)
        if stripped.startswith("#"):
            # Only sections labeled "### 5.x" contain keyword tables.
            if re.match(r"^###\s+5\.\d", stripped):
                in_keyword_section = True
                current_category = clean_text(stripped.lstrip("#").strip())
            else:
                in_keyword_section = False
            continue

        if not in_keyword_section:
            continue
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|?$", stripped):  # separator row
            continue

        parts = [p.strip() for p in stripped.split("|")[1:-1]]
        if len(parts) < 4:
            continue
        kw, meaning, tier, notes = parts[0], parts[1], parts[2], parts[3]
        if not kw or kw in ("Keyword", "Query", "Product ID"):
            continue
        # Guard against stray header variants / malformed leaks
        if kw.lower() in ("title", "price (jpy)", "sales", "favorites", "reviews"):
            continue
        rows.append({
            "keyword": kw,
            "meaning": meaning,
            "evidence_tier": tier,
            "category": current_category,
            "notes": notes,
        })
    return rows


def load_keyword_names(bank_path):
    """Return the ordered list of keyword strings from the bank."""
    return [r["keyword"] for r in parse_tag_bank(bank_path)]


def load_bank_map(bank_path):
    """Return {keyword: {"tier": ..., "meaning": ...}} for tier-aware gates."""
    return {
        r["keyword"]: {"tier": r["evidence_tier"], "meaning": r["meaning"]}
        for r in parse_tag_bank(bank_path)
    }