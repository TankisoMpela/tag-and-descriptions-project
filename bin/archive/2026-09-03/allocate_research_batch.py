#!/usr/bin/env python3
"""Print de-duplicated URLs in Firecrawl-safe sequential batches.

The utility keeps stable URL order, labels each URL as Firecrawl-primary, and
never puts more than six URLs in one batch. Search MCPs and WebFetch are
complements only when Firecrawl rate-limits or fails.
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=6,
        help="URLs per sequential Firecrawl batch (maximum 6; default: 6)",
    )
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 6:
        parser.error("--batch-size must be between 1 and 6")
    raw = args.urls or [line.strip() for line in sys.stdin if line.strip()]
    urls = list(dict.fromkeys(raw))
    for index, url in enumerate(urls):
        batch = index // args.batch_size + 1
        position = index % args.batch_size + 1
        print(f"batch-{batch}\t{position}\tfirecrawl-primary\t{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
