#!/usr/bin/env python3
"""Collect Creative Fabrica tag evidence into a research bank.

Uses the project's serper + firecrawl MCP servers (stdio) to:
  1. scrape the Creative Fabrica Fonts index for the canonical category list;
  2. hit https://www.creativefabrica.com/tag/<slug>-fonts/ for every candidate
     tag and record its published font count ("Explore N stunning X Fonts");
  3. discover popular font products via serper and record the keywords their
     titles and category breadcrumbs use.

Counts are CATALOG COVERAGE signals, never demand or sales evidence.

Outputs:
  outputs/research/creative-fabrica-tag-bank.json
  outputs/research/creative-fabrica-tag-bank.md

Usage:
  python3 bin/collect_creative_fabrica_tags.py [--limit N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

GEMINI_PROXY = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy")
ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "outputs/research/creative-fabrica-tag-bank.json"
OUT_MD = ROOT / "outputs/research/creative-fabrica-tag-bank.md"

SEED_TAGS = [
    # style families
    "script", "handwritten", "cursive", "calligraphy", "signature", "brush",
    "serif", "sans serif", "display", "blackletter", "slab serif", "monogram",
    "modern", "vintage", "retro", "rustic", "boho", "grunge", "graffiti",
    "typewriter", "condensed", "rounded", "bold", "elegant", "luxury",
    "minimalist", "geometric", "decorative", "whimsical", "playful", "funky",
    "western", "tattoo", "comic", "horror", "christmas", "halloween",
    "valentine", "spring", "summer", "winter", "fall", "kids", "baby",
    "wedding", "birthday", "beach", "farmhouse", "cottagecore", "gothic",
    "art deco", "varsity", "collegiate", "sports", "outline", "shadow",
    "stencil", "monoline", "duo", "family", "ligature",
    # structural / platform categories
    "color", "dingbats",
    # use-cases / buyer intent
    "logo", "branding", "invitation", "tshirt", "sublimation", "cricut",
    "packaging", "poster", "headline", "craft", "blog", "social media",
    "greeting card", "label", "signage", "apparel", "stickers", "merch",
]

SERPER_QUERIES = [
    "most popular creative fabrica fonts",
    "creative fabrica best selling script fonts",
    "creative fabrica top handwritten fonts",
    "creative fabrica popular serif fonts",
    "creative fabrica trending display fonts",
    "site:creativefabrica.com/product script font",
    "site:creativefabrica.com/product handwritten font",
    "site:creativefabrica.com/product serif font",
    "site:creativefabrica.com/product display font",
    "site:creativefabrica.com/product calligraphy font",
    "site:creativefabrica.com/product modern font",
    "site:creativefabrica.com/product vintage font",
]

EXPLORE_RE = re.compile(r"Explore\s+([\d,]+)\s+stunning", re.IGNORECASE)
TITLE_COUNT_RE = re.compile(r"([\d,]+)\+\s+Stunning", re.IGNORECASE)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
BREADCRUMB_RE = re.compile(
    r"\[Fonts\]\(https://www\.creativefabrica\.com/fonts/\)\s*/\s*\[([^\]]+)\]"
)
CATEGORY_LINK_RE = re.compile(
    r"\]\((https://www\.creativefabrica\.com/fonts/([a-z0-9-]+)-fonts/)\)"
)
SERPER_PRODUCT_RE = re.compile(
    r"^\d+\.\s+(.+?)\n\s+URL:\s+https://www\.creativefabrica\.com/product/([a-z0-9-]+)/",
    re.MULTILINE,
)


def mcp_call(server: str, tool: str, args: dict, timeout: int = 120) -> dict | None:
    cmd = ["python3", str(GEMINI_PROXY / f"{server}_mcp.py")]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )

    def send(payload: dict) -> None:
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "cf-tag-collector", "version": "1"}}})
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": tool, "arguments": args}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                return None
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("id") == 2:
                return payload
    except (BrokenPipeError, OSError):
        return None
    finally:
        proc.kill()
    return None


def text_of(payload: dict | None) -> str:
    if not payload:
        return ""
    content = (payload.get("result") or {}).get("content") or []
    return "\n".join(part.get("text", "") for part in content if part.get("type") == "text")


def scrape(url: str) -> str:
    return text_of(mcp_call("firecrawl", "firecrawl_scrape", {"url": url}))


def search(query: str, n: int = 10) -> str:
    return text_of(mcp_call("serper", "serper_search", {"query": query, "max_results": n}))


def parse_tag_page(body: str) -> tuple[int | None, str]:
    """Return (coverage_count, h1). Absent pages carry the URL as their H1."""
    if not body:
        return None, ""
    heading = (H1_RE.search(body) or [None, ""])[1].strip() if H1_RE.search(body) else ""
    if heading.startswith("http"):
        return None, heading  # 404 / unknown tag
    for pattern in (EXPLORE_RE, TITLE_COUNT_RE):
        match = pattern.search(body)
        if match:
            return int(match.group(1).replace(",", "")), heading
    return None, heading


def slugify(tag: str) -> str:
    return tag.replace(" ", "-").lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="probe only the first N seed tags")
    args = parser.parse_args()

    stamp = dt.date.today().isoformat()
    seeds = SEED_TAGS[: args.limit] if args.limit else SEED_TAGS

    bank: dict = {
        "platform": "Creative Fabrica",
        "generated": stamp,
        "method": "firecrawl scrape of /tag/<slug>-fonts/ and /fonts/; serper product discovery",
        "caveat": "Counts are catalog coverage / tag-page life, NOT demand or sales evidence.",
        "categories": [],
        "total_fonts": None,
        "tags": [],
        "popular_products": [],
    }

    print(f"[1/3] Fonts index ({stamp})", file=sys.stderr)
    index = scrape("https://www.creativefabrica.com/fonts/")
    bank["categories"] = sorted(
        {name for _, name in CATEGORY_LINK_RE.findall(index)} |
        {"color", "decorative", "dingbats", "display", "sans-serif", "script", "serif", "slab-serif", "blackletter"}
    )
    total = re.search(r"Download\s+([\d,]+)\+\s+font", index, re.IGNORECASE)
    bank["total_fonts"] = int(total.group(1).replace(",", "")) if total else None
    print(f"    categories={len(bank['categories'])} total_fonts={bank['total_fonts']}", file=sys.stderr)

    print(f"[2/3] tag pages: {len(seeds)}", file=sys.stderr)
    for i, tag in enumerate(seeds, 1):
        slug = slugify(tag)
        url = f"https://www.creativefabrica.com/tag/{slug}-fonts/"
        body = scrape(url)
        count, heading = parse_tag_page(body)
        if count is None:  # fall back to the bare slug page
            bare = f"https://www.creativefabrica.com/tag/{slug}/"
            body2 = scrape(bare)
            count2, heading2 = parse_tag_page(body2)
            if count2 is not None:
                url, count, heading = bare, count2, heading2
        bank["tags"].append({
            "tag": tag, "slug": slug, "url": url, "h1": heading,
            "coverage_count": count, "status": "live" if count is not None else "absent",
            "retrieved": stamp,
        })
        print(f"    {i:3}/{len(seeds)} {tag:<18} {count}", file=sys.stderr)

    print("[3/3] serper product discovery", file=sys.stderr)
    seen: set[str] = set()
    for query in SERPER_QUERIES:
        body = search(query, 10)
        for title, slug in SERPER_PRODUCT_RE.findall(body):
            if slug in seen:
                continue
            seen.add(slug)
            bank["popular_products"].append({"title": title.strip(), "slug": slug, "query": query})
    print(f"    products discovered: {len(bank['popular_products'])}", file=sys.stderr)

    print("    enriching category breadcrumbs", file=sys.stderr)
    for item in bank["popular_products"][:8]:
        body = scrape(f"https://www.creativefabrica.com/product/{item['slug']}/")
        match = BREADCRUMB_RE.search(body)
        if match:
            item["category"] = match.group(1).strip()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(bank, indent=2) + "\n", encoding="utf-8")

    live = sorted((t for t in bank["tags"] if t["status"] == "live"),
                  key=lambda t: t["coverage_count"], reverse=True)
    lines = [
        "# Creative Fabrica tag bank (collected evidence)",
        "",
        f"- Generated: {stamp}",
        f"- Method: {bank['method']}",
        f"- **Caveat: {bank['caveat']}**",
        f"- Fonts index total: {bank['total_fonts']:,}" if bank["total_fonts"] else "- Fonts index total: n/a",
        f"- Live tag pages: {len(live)} / {len(bank['tags'])}",
        "",
        "## Canonical Creative Fabrica font categories",
        "",
    ]
    for category in bank["categories"]:
        lines.append(f"- {category}")
    lines += ["", "## Tag coverage ranking (live /tag/<slug>-fonts/ pages)", "",
              "| Tag | Coverage count | H1 | URL |", "|---|---:|---|---|"]
    for tag in live:
        lines.append(f"| {tag['tag']} | {tag['coverage_count']:,} | {tag['h1']} | {tag['url']} |")
    absent = [t for t in bank["tags"] if t["status"] != "live"]
    if absent:
        lines += ["", "## Absent tag pages (no font coverage found)", ""]
        lines += [f"- {t['tag']} ({t['url']})" for t in absent]
    lines += ["", "## Discovered popular products", "", "| Product | Category | Slug |", "|---|---|---|"]
    for product in bank["popular_products"]:
        lines.append(f"| {product['title']} | {product.get('category', '')} | {product['slug']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
