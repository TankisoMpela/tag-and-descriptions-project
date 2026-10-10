#!/usr/bin/env python3
"""Walk Creative Fabrica's font-tag graph and append observations to a corpus.

Creative Fabrica product pages do not expose their tag list to the server
(0 `/tag/` links in the raw HTML), but every `/tag/<slug>/` page links to its
neighbours. This walks that graph from the known font seeds, recording each tag
page's display name, published coverage count, and its related font tags.

One Firecrawl call per tag page (formats: links + markdown). Findings are
APPENDED to
  outputs/research/creative-fabrica-tag-corpus.jsonl   (one JSON object per line)
so repeated runs accumulate rather than overwrite. A visited-state file makes
re-runs resume instead of refetching.

Counts are catalog coverage signals, never demand or sales evidence.

Usage:
  python3 bin/collect_creative_fabrica_tag_graph.py [--max-pages N] [--seed SLUG ...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

MCP = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy/firecrawl_mcp.py")
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "outputs/research/creative-fabrica-tag-corpus.jsonl"
STATE = ROOT / "outputs/research/creative-fabrica-tag-corpus.state.json"
BANK = ROOT / "outputs/research/creative-fabrica-tag-bank.json"

CORE_SEEDS = [
    "script-fonts", "handwritten-fonts", "calligraphy-fonts", "cursive-fonts",
    "serif-fonts", "sans-serif-fonts", "display-fonts", "slab-serif-fonts",
    "blackletter-fonts", "decorative-fonts", "monogram-fonts", "brush-fonts",
    "modern-fonts", "elegant-fonts", "retro-fonts", "vintage-fonts",
    "logo-fonts", "wedding-fonts", "cricut-fonts", "bold-fonts",
]
COUNT_PATTERNS = [
    re.compile(r"Explore\s+([\d,]+)\s+stunning", re.IGNORECASE),
    re.compile(r"([\d,]+)\+\s+Stunning", re.IGNORECASE),
]
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FONT_TAG_RE = re.compile(r"/tag/([a-z0-9-]+-fonts)/")


def load_keys() -> list[str]:
    source = MCP.read_text(encoding="utf-8")
    block = re.search(r"FIRECRAWL_KEYS\s*=\s*\[(.*?)\]", source, re.S).group(1)
    return re.findall(r'"([^"]+)"', block)


KEYS = load_keys()


def scrape(url: str, key_index: int = 0) -> dict | None:
    """One Firecrawl call returning links + markdown."""
    payload = {"url": url, "formats": ["links", "markdown"]}
    for attempt in range(len(KEYS)):
        key = KEYS[(key_index + attempt) % len(KEYS)]
        request = urllib.request.Request(
            "https://api.firecrawl.dev/v1/scrape",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode())
            if result.get("success"):
                return result.get("data", {})
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1)
    return None


def parse(data: dict) -> tuple[str, int | None, list[str]]:
    markdown = data.get("markdown") or ""
    heading = (H1_RE.search(markdown).group(1).strip() if H1_RE.search(markdown) else "")
    if heading.startswith("http"):
        return heading, None, []  # 404 / unknown tag
    count = None
    for pattern in COUNT_PATTERNS:
        match = pattern.search(markdown)
        if match:
            count = int(match.group(1).replace(",", ""))
            break
    links = data.get("links") or []
    related = sorted({m for link in links for m in FONT_TAG_RE.findall(link)})
    return heading, count, related


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--state", default=str(STATE))
    args = parser.parse_args()

    stamp = dt.date.today().isoformat()
    state_path = Path(args.state)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"visited": [], "seen_slugs": []}
    visited = set(state.get("visited", []))
    seen = set(state.get("seen_slugs", []))

    queue: deque[str] = deque()
    if args.seed:                      # explicit shard: use exactly these seeds
        seeds = list(args.seed)
    else:
        seeds = list(CORE_SEEDS)
    if not args.seed and BANK.exists():
        bank = json.loads(BANK.read_text(encoding="utf-8"))
        seeds += [t["slug"] + "-fonts" for t in bank.get("tags", [])
                  if t.get("status") == "live" and not t["slug"].endswith("-fonts")]
        seeds += [t["slug"] for t in bank.get("tags", []) if t["slug"].endswith("-fonts")]
    for seed in seeds:
        if seed not in visited:
            queue.append(seed)
            seen.add(seed)

    CORPUS.parent.mkdir(parents=True, exist_ok=True)
    fetched = 0
    with CORPUS.open("a", encoding="utf-8") as out:
        while queue and fetched < args.max_pages:
            slug = queue.popleft()
            if slug in visited:
                continue
            data = scrape(f"https://www.creativefabrica.com/tag/{slug}/")
            visited.add(slug)
            fetched += 1
            if not data:
                print(f"  [{fetched}/{args.max_pages}] {slug} FETCH-FAILED", file=sys.stderr)
                continue
            heading, count, related = parse(data)
            out.write(json.dumps({
                "slug": slug,
                "url": f"https://www.creativefabrica.com/tag/{slug}/",
                "display_name": re.sub(r"\s+\d{4}.*$", "", heading).replace(" Fonts", "").strip() or None,
                "h1": heading,
                "coverage_count": count,
                "related_font_tags": related,
                "observed": stamp,
            }, ensure_ascii=False) + "\n")
            out.flush()
            new = 0
            for tag in related:
                if tag not in seen:
                    seen.add(tag)
                    queue.append(tag)
                    new += 1
            print(f"  [{fetched}/{args.max_pages}] {slug:34} count={count} +{new} new (queue {len(queue)})", file=sys.stderr)

    state_path.write_text(json.dumps({"visited": sorted(visited), "seen_slugs": sorted(seen)}, indent=0), encoding="utf-8")
    print(f"fetched {fetched}; corpus lines -> {CORPUS} ({sum(1 for _ in CORPUS.open(encoding='utf-8', errors='replace'))})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
