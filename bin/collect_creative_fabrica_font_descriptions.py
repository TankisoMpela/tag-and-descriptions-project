#!/usr/bin/env python3
"""Harvest popular-font product descriptions from Creative Fabrica.

Product pages do not expose their tag list, but they DO expose the seller's
description prose — the buyer language sellers actually write with. This
collects it, append-only, so the tag-pattern guide can learn phrasing instead of
only tag names.

Phase A: collect product slugs from each canonical category page
         (`/fonts/<category>-fonts/`, ~36 popular fonts each).
Phase B: scrape each product page and store title, category breadcrumb and the
         seller description.

Findings APPEND to
  outputs/research/creative-fabrica-description-corpus.jsonl
with a state file so re-runs resume.

Usage:
  python3 bin/collect_creative_fabrica_font_descriptions.py [--max-products N] [--shard i/n]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MCP = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy/firecrawl_mcp.py")
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "outputs/research/creative-fabrica-description-corpus.jsonl"
SLUGS = ROOT / "outputs/research/creative-fabrica-product-slugs.json"

CATEGORIES = [
    "blackletter", "color", "decorative", "dingbats", "display",
    "sans-serif", "script", "serif", "slab-serif",
]

PRODUCT_LINK_RE = re.compile(r"/product/([a-z0-9-]+)/")
SPECIMEN_RE = re.compile(r"/view/specimen/\)\s*\n+\s*(.+?)\n+\s*\*\s?\*\s?\*", re.S)
PIN_DESC_RE = re.compile(r"[?&]description=([^&\s\"]+)")
BREADCRUMB_RE = re.compile(r"\[Fonts\]\(https://www\.creativefabrica\.com/fonts/\)\s*/\s*\[([^\]]+)\]")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MD_JUNK_RE = re.compile(r"[*_`>#!]")


def load_keys() -> list[str]:
    source = MCP.read_text(encoding="utf-8")
    block = re.search(r"FIRECRAWL_KEYS\s*=\s*\[(.*?)\]", source, re.S).group(1)
    return re.findall(r'"([^"]+)"', block)


KEYS = load_keys()


def scrape(url: str, formats: list[str], key_index: int = 0) -> dict | None:
    payload = {"url": url, "formats": formats}
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


def clean(text: str) -> str:
    text = MD_LINK_RE.sub(r"\1", text)
    text = MD_JUNK_RE.sub("", text)
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_description(markdown: str) -> str | None:
    match = SPECIMEN_RE.search(markdown)
    if match:
        text = clean(match.group(1))
        if len(text) >= 40:
            return text
    pin = PIN_DESC_RE.search(markdown)
    if pin:
        text = clean(urllib.parse.unquote_plus(pin.group(1)))
        if len(text) >= 40:
            return text
    return None


def collect_slugs(max_categories: int) -> dict[str, str]:
    """slug -> category it was discovered under."""
    found: dict[str, str] = {}
    for category in CATEGORIES[:max_categories]:
        data = scrape(f"https://www.creativefabrica.com/fonts/{category}-fonts/", ["links"])
        for link in (data or {}).get("links") or []:
            match = PRODUCT_LINK_RE.search(link)
            if match and "/view/" not in link and match.group(1) not in found:
                found[match.group(1)] = category
        print(f"  slugs from {category:12} -> {len(found)} total", file=sys.stderr)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-products", type=int, default=100)
    parser.add_argument("--shard", default="1/1")
    parser.add_argument("--categories", type=int, default=len(CATEGORIES))
    args = parser.parse_args()

    index, total = (int(x) for x in args.shard.split("/"))
    stamp = dt.date.today().isoformat()

    if SLUGS.exists():
        discovered = json.loads(SLUGS.read_text(encoding="utf-8"))
    else:
        discovered = collect_slugs(args.categories)
        SLUGS.write_text(json.dumps(discovered, indent=2), encoding="utf-8")

    done = set()
    if CORPUS.exists():
        for line in CORPUS.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                done.add(json.loads(line)["slug"])
            except Exception:
                continue

    todo = [s for s in sorted(discovered) if s not in done]
    todo = todo[index - 1 :: total][: args.max_products]

    wrote = 0
    with CORPUS.open("a", encoding="utf-8") as out:
        for slug in todo:
            data = scrape(f"https://www.creativefabrica.com/product/{slug}/", ["markdown"])
            markdown = (data or {}).get("markdown") or ""
            if not markdown:
                print(f"  {slug} FETCH-FAILED", file=sys.stderr)
                continue
            heading = (H1_RE.search(markdown).group(1).strip() if H1_RE.search(markdown) else "")
            breadcrumb = BREADCRUMB_RE.search(markdown)
            description = extract_description(markdown)
            record = {
                "slug": slug,
                "title": clean(heading) or None,
                "category": breadcrumb.group(1).strip() if breadcrumb else discovered.get(slug),
                "description": description,
                "description_chars": len(description or ""),
                "observed": stamp,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            wrote += 1
            print(f"  [{wrote}/{len(todo)}] {slug:34} desc={record['description_chars']}", file=sys.stderr)
    print(f"shard {args.shard}: wrote {wrote} descriptions -> {CORPUS}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
