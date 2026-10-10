#!/usr/bin/env python3
"""Harvest the popular fonts inside each Creative Fabrica font category.

One firecrawl call per category on `/fonts/<category>-fonts/` returns the live
popular-font grid; the product titles are the category-native language that top
sellers actually use. Results merge into
outputs/research/creative-fabrica-tag-bank.json under `category_affinity`, and
bin/build_creative_fabrica_tag_strategy.py folds them into the strategy.

Counts and titles are catalog signals, never demand or sales evidence.

Usage:
  python3 bin/font_category_affinity.py                 # all nine categories
  python3 bin/font_category_affinity.py --category script   # one category (1 call)
  python3 bin/font_category_affinity.py --show script       # print only, no write
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

GEMINI_PROXY = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy")
ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "outputs/research/creative-fabrica-tag-bank.json"

# Creative Fabrica's nine canonical font categories (from /fonts/).
CATEGORIES = [
    "blackletter", "color", "decorative", "dingbats", "display",
    "sans-serif", "script", "serif", "slab-serif",
]

TITLE_PATTERNS = [
    re.compile(r"\[!\[([^\]]{3,80})\]\(https://cdn\.creativefabrica\.com"),
    re.compile(r"\[([A-Za-z0-9][^\]\n]{2,70})\]\(https://www\.creativefabrica\.com/product/"),
]
STOP = {
    "font", "fonts", "by", "the", "and", "of", "a", "for", "with", "creative",
    "fabrica", "graphic", "design", "studio", "typeface", "duo", "bundle",
    "svg", "png", "alphabet", "letters", "numbers", "set", "pack",
}


def mcp_call(server: str, tool: str, args: dict, timeout: int = 120) -> dict | None:
    cmd = ["python3", str(GEMINI_PROXY / f"{server}_mcp.py")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(payload: dict) -> None:
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "cf-affinity", "version": "1"}}})
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


def scrape(url: str) -> str:
    payload = mcp_call("firecrawl", "firecrawl_scrape", {"url": url})
    if not payload:
        return ""
    content = (payload.get("result") or {}).get("content") or []
    return "\n".join(part.get("text", "") for part in content if part.get("type") == "text")


def harvest(category: str) -> list[str]:
    body = scrape(f"https://www.creativefabrica.com/fonts/{category}-fonts/")
    titles: list[str] = []
    for pattern in TITLE_PATTERNS:
        for match in pattern.findall(body):
            title = " ".join(match.split())
            if title and title not in titles:
                titles.append(title)
    return titles


def words(titles: list[str]) -> Counter:
    counter: Counter = Counter()
    for title in titles:
        for word in re.sub(r"[^A-Za-z ]", " ", title).lower().split():
            if len(word) > 2 and word not in STOP:
                counter[word] += 1
    return counter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=CATEGORIES)
    parser.add_argument("--show", choices=CATEGORIES, help="print without writing")
    args = parser.parse_args()

    targets = [args.show or args.category] if (args.show or args.category) else CATEGORIES
    stamp = dt.date.today().isoformat()

    bank = json.loads(BANK.read_text(encoding="utf-8")) if BANK.exists() else {}
    affinity = bank.setdefault("category_affinity", {})

    for category in targets:
        titles = harvest(category)
        affinity[category] = {"retrieved": stamp, "titles": titles}
        top = words(titles).most_common(18)
        print(f"{category:12} titles={len(titles):3}  top: " + ", ".join(w for w, _ in top), file=sys.stderr)

    if not args.show:
        BANK.write_text(json.dumps(bank, indent=2) + "\n", encoding="utf-8")
        print(f"merged into {BANK}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
