#!/usr/bin/env python3
"""One-time exhaustive harvest of BOOTH font demand signals.

Design rule: harvest ONCE, record it, and let every later run read the record.
Nothing here should run per listing. Re-running the same seeds would return the
same keywords and only make the agent expensive.

Three record types, all resumable:

  1. **Google autocomplete corpus** (serper, 1 credit/call)
     Every suggestion for a broad seed set, plus kana and latin expansion on the
     productive seeds. This is the only source of *typed-query* data for this
     market — BOOTH publishes no search volume and has no query endpoint.

  2. **BOOTH exact-tag route counts** (Firecrawl, renders past Cloudflare)
     BOOTH-wide supply per tag, i.e. how many items compete for it. The census
     already holds font-category counts; this adds the all-category number.

  3. **Distilled signals** — the corpus reduced to the buckets that change a
     listing: app terms, licensing anxiety, free intent, wording variants.

Outputs (all under outputs/research/booth-demand/):
  autocomplete-corpus.jsonl   one row per (seed, suggestion)
  route-counts.jsonl          one row per (tag, count)
  demand-signals.md           the distilled, human-readable result
  harvest-state.json          resume bookkeeping

Usage:
  python3 bin/harvest_booth_demand.py --autocomplete         # phase 1
  python3 bin/harvest_booth_demand.py --autocomplete --expand # + kana/latin
  python3 bin/harvest_booth_demand.py --routes --top 200      # phase 2
  python3 bin/harvest_booth_demand.py --distil                # phase 3
  python3 bin/harvest_booth_demand.py --all                   # everything

Every phase resumes: completed seeds/tags are skipped, so an interrupted run is
continued simply by re-invoking the same command.
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
from collections import Counter
from datetime import date, datetime
from pathlib import Path

OUT_DIR = Path("outputs/research/booth-demand")
CORPUS = OUT_DIR / "autocomplete-corpus.jsonl"
ROUTES = OUT_DIR / "route-counts.jsonl"
STATE = OUT_DIR / "harvest-state.json"
SIGNALS = OUT_DIR / "demand-signals.md"
DB = Path("outputs/research/booth-live-collector/booth.db")

SERPER_URL = "https://google.serper.dev/autocomplete"
FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
SERPER_KEY_FILE = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy/serper_mcp.py")
FIRECRAWL_KEY_FILE = Path("/home/tankiso/Projects/MCP-and-Integrations/gemini-proxy/firecrawl_mcp.py")
ROUTE = "https://booth.pm/ja/items?tags%5B%5D="
COUNT_RE = re.compile(r"([\d,]+)\s*点")

# Seeds spanning every family agent-20 builds candidates from, so the corpus
# lines up with the tag bank rather than being a random keyword list.
CORE_SEEDS = [
    "booth フォント",
    "フォント 商用利用",
    "booth フォント ロゴ",
    "booth フォント 手書き",
    "booth フォント レトロ",
    "booth フォント おしゃれ",
    "booth フォント ダウンロード",
    "欧文フォント",
    "英字フォント",
    "デザインフォント",
    "booth フォント かっこいい",
    "booth フォント かわいい",
    "booth フォント セリフ",
    "booth フォント サンセリフ",
    "booth フォント 筆記体",
    "booth フォント ヴィンテージ",
    "booth フォント ゴシック",
    "booth フォント 明朝",
    "booth フォント タイトル",
    "booth フォント 同人誌",
    "booth フォント サムネイル",
    "booth フォント ゲーム",
    "booth フォント ウェディング",
    "booth フォント 動画",
    "フォント 商用利用 同人",
]

# Expansion characters. Kana first (this is a Japanese marketplace), then latin
# and digits for the English-language tail.
KANA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわ")
LATIN = list("abcdefghijklmnopqrstuvwxyz0123456789")

# Seeds worth expanding: the ones whose base result sets were largest.
EXPAND_SEEDS = [
    "booth フォント",
    "フォント 商用利用",
    "booth フォント ロゴ",
    "booth フォント 手書き",
    "欧文フォント",
    "デザインフォント",
]

APP_TERMS = [
    "クリスタ", "clip studio", "アイビス", "ibispaint", "イラレ", "illustrator",
    "フォトショ", "photoshop", "canva", "ワード", "word", "パワポ", "powerpoint",
    "プレミア", "premiere", "capcut", "cap cut", "filmora", "affinity", "figma",
    "procreate", "vtuber", "obs", "blender", "unity", "after effects",
]
ANXIETY_TERMS = [
    "バレる", "どこまで", "とは", "安全", "違反", "注意", "できない", "大丈夫",
    "確認", "方法", "怖い", "罰則", "無断", "規約",
]
FREE_TERMS = ["無料", "フリー", "free", "お試し", "0円", "タダ"]


def log(msg: str) -> None:
    print(msg, flush=True)


def key_from(explicit: str | None, env: str, path: Path, pattern: str, name: str) -> str:
    if explicit:
        return explicit.strip()
    if os.environ.get(env):
        return os.environ[env].strip()
    if path.exists():
        m = re.search(pattern, path.read_text(errors="ignore"))
        if m:
            return m.group(0) if "fc-" in pattern else m.group(0)
    sys.exit(f"no {name} key: pass --{name}-key, set {env}, or keep {path}")


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {"autocomplete_done": [], "routes_done": []}


def save_state(state: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1))


def append_jsonl(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# --------------------------------------------------------------- autocomplete


def autocomplete(seed: str, key: str, timeout: int = 25) -> list[str]:
    body = json.dumps({"q": seed})
    for _ in range(3):
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST", SERPER_URL,
                 "-H", f"X-API-KEY: {key}", "-H", "Content-Type: application/json",
                 "-d", body, "--max-time", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 10,
            )
            payload = json.loads(r.stdout)
        except Exception:
            time.sleep(2)
            continue
        if "suggestions" in payload:
            return [str(s.get("value", "")).strip() for s in payload["suggestions"]
                    if str(s.get("value", "")).strip()]
        time.sleep(2)
    return []


def harvest_autocomplete(key: str, expand: bool, workers: int) -> None:
    state = load_state()
    done = set(state["autocomplete_done"])
    seeds = [s for s in CORE_SEEDS if s not in done]
    if expand:
        seeds += [
            f"{base} {ch}"
            for base in EXPAND_SEEDS
            for ch in (KANA + LATIN)
            if f"{base} {ch}" not in done
        ]
    if not seeds:
        log("  autocomplete: nothing to do (all seeds recorded)")
        return

    log(f"  autocomplete: {len(seeds)} seeds x 1 credit")
    stamp = datetime.now().isoformat(timespec="seconds")
    batch: list[dict] = []
    n = 0
    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for seed, sugs in zip(seeds, ex.map(lambda s: autocomplete(s, key), seeds)):
            n += 1
            for rank, s in enumerate(sugs, start=1):
                batch.append({"seed": seed, "rank": rank, "suggestion": s, "at": stamp})
            state["autocomplete_done"].append(seed)
            if len(batch) >= 400:
                append_jsonl(CORPUS, batch); batch = []
                save_state(state)
            if n % 50 == 0:
                log(f"    {n}/{len(seeds)}")
    append_jsonl(CORPUS, batch)
    save_state(state)
    log(f"  autocomplete done: {len(seeds)} seeds, {len(done) + len(seeds)} total recorded")


# --------------------------------------------------------------------- routes


def census_tags(min_items: int) -> list[str]:
    import sqlite3
    c = sqlite3.connect(str(DB))
    return [r[0] for r in c.execute(
        "select tag from item_tags group by tag having count(*) >= ? order by count(*) desc",
        (min_items,),
    )]


def fetch_route(tag: str, key: str, timeout: int = 60) -> int | None:
    url = ROUTE + urllib.parse.quote(tag)
    body = json.dumps({"url": url, "formats": ["rawHtml"], "waitFor": 2000})
    for _ in range(3):
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST", FIRECRAWL_URL,
                 "-H", f"Authorization: Bearer {key}",
                 "-H", "Content-Type: application/json",
                 "-d", body, "--max-time", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 15,
            )
            html = (json.loads(r.stdout).get("data") or {}).get("rawHtml", "") or ""
        except Exception:
            html = ""
        m = COUNT_RE.search(html)
        if m:
            return int(m.group(1).replace(",", ""))
        time.sleep(3)
    return None


def harvest_routes(key: str, top: int, workers: int) -> None:
    state = load_state()
    done = set(state["routes_done"])
    tags = [t for t in census_tags(5)[:top] if t not in done]
    if not tags:
        log("  routes: nothing to do")
        return
    log(f"  routes: {len(tags)} tags via Firecrawl (~{len(tags) * 4 // workers}s)")
    stamp = datetime.now().isoformat(timespec="seconds")
    batch, n = [], 0
    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for tag, count in zip(tags, ex.map(lambda t: fetch_route(t, key), tags)):
            n += 1
            if count is not None:
                batch.append({"tag": tag, "route_count": count, "at": stamp})
                # Only a successful read counts as done, so an interrupted or
                # rate-limited run retries its failures instead of retiring them.
                state["routes_done"].append(tag)
            if len(batch) >= 50:
                append_jsonl(ROUTES, batch); batch = []
                save_state(state)
            if n % 25 == 0:
                log(f"    {n}/{len(tags)}")
    append_jsonl(ROUTES, batch)
    save_state(state)
    log(f"  routes done: {len(tags)} tags")


# --------------------------------------------------------------------- distil


def distil() -> None:
    if not CORPUS.exists():
        log("  distil: no corpus yet")
        return
    sugg = {}
    seeds = Counter()
    with open(CORPUS, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            sugg[r["suggestion"]] = min(sugg.get(r["suggestion"], 99), r["rank"])
            seeds[r["seed"]] += 1
    routes = {}
    if ROUTES.exists():
        with open(ROUTES, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    routes[r["tag"]] = r["route_count"]
                except Exception:
                    pass

    def bucket(terms):
        return sorted([s for s in sugg if any(t in s.casefold() for t in terms)],
                      key=lambda s: sugg[s])

    apps, anxiety, free = bucket(APP_TERMS), bucket(ANXIETY_TERMS), bucket(FREE_TERMS)
    other = [s for s in sorted(sugg, key=lambda s: sugg[s])
             if s not in set(apps) | set(anxiety) | set(free)]

    low = Counter()
    for s in sugg:
        for c in "abcdefghijklmnopqrstuvwxyz":
            if s.casefold().startswith(c):
                low[c] += 1
                break

    lines = [
        "# BOOTH font demand signals",
        "",
        f"Harvested {date.today().isoformat()} from Google autocomplete"
        f" ({len(sugg)} distinct suggestions across {len(seeds)} seeds)",
        f"and BOOTH exact-tag routes ({len(routes)} tags).",
        "",
        "**One-time harvest.** Re-running the seeds returns the same keywords, so",
        "this file is the record; the agent reads it instead of re-querying.",
        "",
        "**Limit:** suggestion order is a popularity hint from Google. There is no",
        "volume number and none can be derived. Never quote these as search counts.",
        "",
        "---",
        "",
        "## App terms — buyers search by the tool they will use the font in",
        "",
        "Near-absent from the tag bank and from current listings. A font that works",
        "in these tools can say so.",
        "",
    ]
    lines += [f"- `{s}`" for s in apps[:40]] or ["- (none found)"]
    lines += ["", "## Licensing anxiety — questions, not keywords", "",
              "Doubt surfaces as questions. A hesitant buyer does not convert, so the",
              "description should answer these directly rather than restate the licence.",
              ""]
    lines += [f"- `{s}`" for s in anxiety[:40]] or ["- (none found)"]
    lines += ["", "## Free intent", "",
              "`無料`/`フリー` saturate the tail of nearly every seed. This is a",
              "free-dominant market; relevant when choosing campaign mode.", ""]
    lines += [f"- `{s}`" for s in free[:30]] or ["- (none found)"]
    lines += ["", "## Other frequent phrasings", ""]
    lines += [f"- `{s}`" for s in other[:80]]
    if routes:
        lines += ["", "---", "", "## BOOTH route counts (BOOTH-wide supply per tag)", "",
                  "How many items compete for the tag across all categories. Lower means",
                  "less competition. Pair with the census font-category count.", "",
                  "| tag | route count |", "|---|---:|"]
        lines += [f"| `{t}` | {n:,} |" for t, n in sorted(routes.items(), key=lambda x: -x[1])[:60]]
    SIGNALS.parent.mkdir(parents=True, exist_ok=True)
    SIGNALS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"  distil: {len(sugg)} suggestions, {len(routes)} routes -> {SIGNALS}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autocomplete", action="store_true")
    ap.add_argument("--expand", action="store_true", help="add kana/latin expansion")
    ap.add_argument("--routes", action="store_true")
    ap.add_argument("--top", type=int, default=200, help="route-count tags to fetch")
    ap.add_argument("--distil", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--serper-key")
    ap.add_argument("--firecrawl-key")
    ap.add_argument("--ac-workers", type=int, default=6)
    ap.add_argument("--route-workers", type=int, default=6)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    did = False
    if args.autocomplete or args.all:
        k = key_from(args.serper_key, "SERPER_API_KEY", SERPER_KEY_FILE, r"[0-9a-f]{40}", "serper")
        harvest_autocomplete(k, args.expand or args.all, args.ac_workers)
        did = True
    if args.routes or args.all:
        k = key_from(args.firecrawl_key, "FIRECRAWL_API_KEY", FIRECRAWL_KEY_FILE, r"fc-[A-Za-z0-9]{20,}", "firecrawl")
        harvest_routes(k, args.top, args.route_workers)
        did = True
    if args.distil or args.all:
        distil()
        did = True
    if not did:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
