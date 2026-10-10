#!/usr/bin/env python3
"""Fetch BOOTH's exact-tag route counts through Firecrawl.

BOOTH sits behind Cloudflare: plain HTTP gets "Just a moment..." on
`/ja/items?tags[]=`, and `/ja/search/suggest` and `/ja/browse/` are walled
outright. Firecrawl renders through it, so the tag route is readable.

What the count means
--------------------
`https://booth.pm/ja/items?tags%5B%5D=<tag>` returns a page whose title reads
`<tag>に関する人気の同人グッズN点`. N is **catalog coverage** — how many items
carry that tag. It is NOT search volume, demand, likes, or sales. It is the
supply side: the number of items competing for that tag. Low N with high
observed engagement is the interesting case.

This is the only BOOTH search-adjacent signal that is publicly reachable.
BOOTH publishes no search-volume or query-log endpoint (tested: no public API,
no `/trending_tags`, no autocomplete JSON).

Usage
-----
  # single tag
  python3 bin/booth_tag_route_count.py 書体ダウンロード

  # a file of tags, one per line
  python3 bin/booth_tag_route_count.py --tags-file tags.txt

  # emit markdown rows for the bank's priority table, ranked after --start-rank
  python3 bin/booth_tag_route_count.py --tags-file tags.txt --markdown --start-rank 29

  # read the tags straight out of the bank's priority table
  python3 bin/booth_tag_route_count.py --from-bank --markdown

Requires a Firecrawl key. Resolution order: --key, $FIRECRAWL_API_KEY, then the
local MCP proxy's key file.
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
DEFAULT_BANK = Path("outputs/research/booth-font-tag-bank.md")
MCP_KEY_FILE = Path(
    "/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy/firecrawl_mcp.py"
)
COUNT_RE = re.compile(r"([\d,]+)\s*点")
ROUTE = "https://booth.pm/ja/items?tags%5B%5D="


def resolve_key(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    env = os.environ.get("FIRECRAWL_API_KEY")
    if env:
        return env.strip()
    if MCP_KEY_FILE.exists():
        m = re.search(r"(fc-[A-Za-z0-9]{20,})", MCP_KEY_FILE.read_text(errors="ignore"))
        if m:
            return m.group(1)
    sys.exit(
        "no Firecrawl key: pass --key, set FIRECRAWL_API_KEY, or keep the MCP "
        f"key file at {MCP_KEY_FILE}"
    )


def fetch_count(tag: str, key: str, attempts: int = 3, timeout: int = 60):
    """Return the route count for one tag, or None if all attempts fail."""
    url = ROUTE + urllib.parse.quote(tag)
    body = json.dumps({"url": url, "formats": ["rawHtml"], "waitFor": 2500})
    for attempt in range(attempts):
        try:
            r = subprocess.run(
                [
                    "curl", "-s", "-X", "POST", FIRECRAWL_URL,
                    "-H", f"Authorization: Bearer {key}",
                    "-H", "Content-Type: application/json",
                    "-d", body, "--max-time", str(timeout),
                ],
                capture_output=True, text=True, timeout=timeout + 15,
            )
            payload = json.loads(r.stdout)
            html = (payload.get("data") or {}).get("rawHtml", "") or ""
        except Exception:
            html = ""
        m = COUNT_RE.search(html)
        if m:
            return int(m.group(1).replace(",", ""))
        if attempt < attempts - 1:
            time.sleep(4)
    return None


def bank_tags(path: Path) -> list[str]:
    """Tags from the bank's priority table only.

    Delegates to the DB loader so this script, the analyst, and tag_bank can
    never disagree about what is banked.
    """
    from build_booth_db import load_tag_bank

    return [r["tag"] for r in load_tag_bank(path)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tags", nargs="*", help="tags to look up")
    ap.add_argument("--tags-file", type=Path, help="file of tags, one per line")
    ap.add_argument("--from-bank", action="store_true", help="read tags from the bank's priority table")
    ap.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    ap.add_argument("--key", help="Firecrawl API key")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--markdown", action="store_true", help="emit priority-table rows")
    ap.add_argument("--start-rank", type=int, default=1, help="first rank for --markdown")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    tags: list[str] = list(args.tags)
    if args.tags_file:
        tags += [t.strip() for t in args.tags_file.read_text(encoding="utf-8").splitlines() if t.strip()]
    if args.from_bank:
        tags += bank_tags(args.bank)
    tags = list(dict.fromkeys(tags))
    if not tags:
        ap.error("no tags given: pass tags, --tags-file, or --from-bank")

    key = resolve_key(args.key)
    results: dict[str, int | None] = {}
    with futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for tag, n in ex.map(lambda t: (t, fetch_count(t, key)), tags):
            results[tag] = n

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    elif args.markdown:
        for i, tag in enumerate(tags, start=args.start_rank):
            n = results[tag]
            ns = f"{n:,}" if n is not None else ""
            route = ROUTE + urllib.parse.quote(tag)
            print(f"| {i} | {tag} |  |  | {ns} |  |  |  |  | [route]({route}) |")
    else:
        failed = 0
        for tag in tags:
            n = results[tag]
            if n is None:
                failed += 1
                print(f"  {tag:<36} FAILED")
            else:
                print(f"  {tag:<36} {n:>8,}  items")
        if failed:
            print(f"\n  {failed}/{len(tags)} failed after retries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
