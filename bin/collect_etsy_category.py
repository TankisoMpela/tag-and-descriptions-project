#!/usr/bin/env python3
"""Durable public Etsy category collector (official Open API v3).

Primary source: GET /v3/application/listings/active (findAllListingsActive).
Every catalog page is stored compressed in SQLite and mirrored as raw JSON,
and page state is checkpointed atomically so interruption discards nothing.

Usage:
  ETSY_API_KEY=xxx python3 bin/collect_etsy_category.py \
      --out outputs/research/etsy-live-collector \
      --taxonomy-id 13070
  ETSY_API_KEY=xxx python3 bin/collect_etsy_category.py --resume --keywords "font"

Design notes:
  * Offset pagination (limit<=100). Default newest-first by creation date.
  * sort_on/sort_order only apply when combined with a search option
    (keywords, region, ...). Everforce default order otherwise.
  * Conservative pacing (default 2 rps; API allows 10 rps, 10k/day).
  * Idempotent by listing_id. Interrupted runs must not be treated as
    complete censuses: read crawl-state.json for last completed page.

Environment:
  ETSY_API_KEY   required (free key from https://www.etsy.com/developers)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

API = "https://openapi.etsy.com/v3/application"
UA = "FontFairyResearch/1.0 (public catalog research; registered Etsy api key)"
EXTRACTOR_VERSION = "etsy-category-1.0.0"
SCHEMA_VERSION = 1
STOP = False


def signal_handler(signum, frame):
    global STOP
    STOP = True
    print("[WARN] signal received; finishing current transaction", file=sys.stderr)


for _s in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_s, signal_handler)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def client(api_key: str) -> httpx.Client:
    return httpx.Client(
        headers={"x-api-key": api_key, "User-Agent": UA},
        timeout=30.0,
        follow_redirects=True,
    )


def schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS taxonomy_nodes (
            taxonomy_id INTEGER PRIMARY KEY,
            level INTEGER,
            name TEXT,
            parent_id INTEGER,
            full_path TEXT,
            fetched_at TEXT
        );
        CREATE TABLE IF NOT EXISTS listings (
            listing_id INTEGER PRIMARY KEY,
            shop_id INTEGER,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            rich_description TEXT,
            state TEXT,
            listing_type TEXT,
            taxonomy_id INTEGER,
            price_amount INTEGER,
            price_divisor INTEGER,
            price_currency TEXT,
            converted_amount INTEGER,
            converted_currency TEXT,
            url TEXT,
            num_favorers INTEGER,
            creation_timestamp INTEGER,
            ending_timestamp INTEGER,
            last_modified_timestamp INTEGER,
            original_creation_timestamp INTEGER,
            language TEXT,
            quantity INTEGER,
            featured_rank INTEGER,
            shop_section_id INTEGER,
            is_taxable INTEGER,
            is_customizable INTEGER,
            is_personalizable INTEGER,
            processing_min INTEGER,
            processing_max INTEGER,
            who_made TEXT,
            when_made TEXT,
            is_supply INTEGER,
            has_variations INTEGER,
            should_auto_renew INTEGER,
            is_private INTEGER,
            suggested_title TEXT,
            raw_json BLOB,
            snapshot_date TEXT
        );
        CREATE TABLE IF NOT EXISTS tags (
            listing_id INTEGER,
            tag TEXT,
            position INTEGER,
            PRIMARY KEY (listing_id, position),
            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
        );
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
        CREATE INDEX IF NOT EXISTS idx_listings_taxonomy ON listings(taxonomy_id);
        CREATE INDEX IF NOT EXISTS idx_listings_shop ON listings(shop_id);
        CREATE INDEX IF NOT EXISTS idx_listings_created ON listings(creation_timestamp);
        """
    )
    conn.commit()


def store_listing(conn: sqlite3.Connection, item: dict, snapshot: str):
    listing_id = item.get("listing_id")
    if listing_id is None:
        return
    price = item.get("price") or {}
    conv = item.get("converted_price") or {}
    raw = json.dumps(item, ensure_ascii=False).encode("utf-8")
    conn.execute(
        """
        INSERT OR REPLACE INTO listings (
            listing_id, shop_id, user_id, title, description, rich_description,
            state, listing_type, taxonomy_id, price_amount, price_divisor,
            price_currency, converted_amount, converted_currency, url,
            num_favorers, creation_timestamp, ending_timestamp,
            last_modified_timestamp, original_creation_timestamp, language,
            quantity, featured_rank, shop_section_id, is_taxable,
            is_customizable, is_personalizable, processing_min, processing_max,
            who_made, when_made, is_supply, has_variations, should_auto_renew,
            is_private, suggested_title, raw_json, snapshot_date
        ) VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """,
        (
            listing_id,
            item.get("shop_id"),
            item.get("user_id"),
            item.get("title"),
            item.get("description"),
            item.get("rich_description"),
            item.get("state"),
            item.get("listing_type"),
            item.get("taxonomy_id"),
            price.get("amount"),
            price.get("divisor"),
            price.get("currency_code"),
            conv.get("amount"),
            conv.get("currency_code"),
            item.get("url"),
            item.get("num_favorers"),
            item.get("creation_timestamp"),
            item.get("ending_timestamp"),
            item.get("last_modified_timestamp"),
            item.get("original_creation_timestamp"),
            item.get("language"),
            item.get("quantity"),
            item.get("featured_rank"),
            item.get("shop_section_id"),
            1 if item.get("is_taxable") else 0,
            1 if item.get("is_customizable") else 0,
            1 if item.get("is_personalizable") else 0,
            item.get("processing_min"),
            item.get("processing_max"),
            item.get("who_made"),
            item.get("when_made"),
            1 if item.get("is_supply") else 0,
            1 if item.get("has_variations") else 0,
            1 if item.get("should_auto_renew") else 0,
            1 if item.get("is_private") else 0,
            item.get("suggested_title"),
            gzip.compress(raw),
            snapshot,
        ),
    )
    conn.execute("DELETE FROM tags WHERE listing_id = ?", (listing_id,))
    for pos, tag in enumerate(item.get("tags") or []):
        conn.execute(
            "INSERT INTO tags (listing_id, tag, position) VALUES (?,?,?)",
            (listing_id, str(tag).strip().lower() or None, pos),
        )


def fetch_pages(
    conn: sqlite3.Connection,
    client: httpx.Client,
    out_dir: Path,
    args: argparse.Namespace,
    state: dict,
):
    # --- taxonomy resolution pass (one-time) ---
    if args.resolve_taxonomy:
        _resolve_taxonomy(conn, client, out_dir, args.delay_seconds)

    snapshot = iso_now()
    offset = state.get("next_offset", 0)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    params: dict[str, Any] = {
        "limit": args.limit,
        "offset": offset,
        "is_safe": "true",
    }
    if args.taxonomy_id:
        params["taxonomy_id"] = args.taxonomy_id
    if args.keywords:
        params["keywords"] = args.keywords
    if args.sort_on:
        params["sort_on"] = args.sort_on
        params["sort_order"] = args.sort_order or "asc"
    if args.min_price is not None:
        params["min_price"] = args.min_price
    if args.max_price is not None:
        params["max_price"] = args.max_price
    if args.currency:
        params["currency"] = args.currency

    pages_seen = state.get("pages_seen", 0)
    unique = set()
    empty_count = 0

    while not STOP:
        if offset > args.max_offset:
            print(f"[STOP] offset {offset} exceeds --max-offset {args.max_offset}")
            break
        resp = client.get(f"{API}/listings/active", params=params)
        if resp.status_code == 429:
            retry = int(resp.headers.get("retry-after", "60") or "60")
            print(f"[429] rate limited; pausing {retry}s")
            time.sleep(min(retry, 300))
            continue
        if resp.status_code >= 500:
            print(f"[{resp.status_code}] server error {resp.url}; pausing 30s")
            time.sleep(30)
            continue
        if resp.status_code != 200:
            print(f"[{resp.status_code}] unexpected: {resp.text[:300]}")
            break
        try:
            data = resp.json()
        except ValueError:
            print("[ERROR] non-JSON response; pausing")
            time.sleep(30)
            continue

        results = data.get("results") or []
        if not results:
            empty_count += 1
            print(f"[DONE] empty page at offset={offset}")
            state["next_offset"] = offset
            atomic_write(out_dir / "crawl-state.json", json.dumps(state, indent=2))
            break

        page_file = raw_dir / f"listings-active_offset-{offset:06d}.json"
        raw_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        page_file.write_bytes(raw_bytes)

        new_units = 0
        for item in results:
            listing_id = item.get("listing_id")
            if listing_id is None:
                continue
            if listing_id in unique:
                print(f"[WARN] duplicate listing_id {listing_id} at offset={offset}")
            unique.add(listing_id)
            store_listing(conn, item, snapshot)
            new_units += 1
        conn.commit()

        pages_seen += 1
        offset += len(results)
        params["offset"] = offset
        state["next_offset"] = offset
        state["pages_seen"] = pages_seen
        state["last_page"] = {
            "offset": offset - len(results),
            "size": len(results),
            "fetched_at": iso_now(),
            "raw": str(page_file),
        }
        atomic_write(out_dir / "crawl-state.json", json.dumps(state, indent=2))
        print(
            f"[OK] page {pages_seen} offset={offset - len(results)} "
            f"items={new_units} total_unique={len(unique)} "
            f"remaining_today={resp.headers.get('x-remaining-today', '?')}"
        )
        if len(results) < args.limit:
            print(f"[DONE] short page ({len(results)} < limit {args.limit}); category exhausted")
            break
        if empty_count > 3:
            print("[STOP] repeated empty pages; aborting")
            break
        time.sleep(args.delay_seconds)


def _resolve_taxonomy(conn: sqlite3.Connection, client: httpx.Client, out_dir: Path, delay_seconds: float):
    """Mirror the seller-taxonomy tree so taxonomy_id can be mapped to a path."""
    print("[TAXONOMY] downloading seller taxonomy tree ...")
    offset = 0
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    nodes: dict[int, dict] = {}
    while True:
        resp = client.get(f"{API}/seller-taxonomy/nodes", params={"limit": 100, "offset": offset})
        if resp.status_code != 200:
            print(f"[TAXONOMY] {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        results = data.get("results") or []
        if not results:
            break
        (raw_dir / f"seller-taxonomy_offset-{offset:06d}.json").write_bytes(
            json.dumps(data, ensure_ascii=False).encode("utf-8")
        )
        for node in results:
            nodes[int(node["taxonomy_id"])] = node
        offset += len(results)
        print(f"[TAXONOMY] {len(nodes)} nodes so far")
        if len(results) < 100:
            break
        time.sleep(delay_seconds)
    conn.execute("DELETE FROM taxonomy_nodes")
    for tid, node in nodes.items():
        name = node.get("name")
        level = node.get("level")
        parent = node.get("parent_id")
        path = []
        cur: dict | None = node
        while cur is not None:
            path.append(str(cur.get("name", "")))
            cur = nodes.get(int(cur["parent_id"])) if cur.get("parent_id") else None
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy_nodes"
            " (taxonomy_id, level, name, parent_id, full_path, fetched_at)"
            " VALUES (?,?,?,?,?,?)",
            (tid, level, name, parent, " / ".join(reversed(path)), iso_now()),
        )
    conn.commit()
    print(f"[TAXONOMY] stored {len(nodes)} nodes")


def main():
    ap = argparse.ArgumentParser(description="Etsy category collector (Open API v3)")
    ap.add_argument("--out", default="outputs/research/etsy-live-collector")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--taxonomy-id", type=int, help="seller/buyer taxonomy category id")
    ap.add_argument("--resolve-taxonomy", action="store_true", help="snapshot taxonomy tree first")
    ap.add_argument("--keywords", help="keyword filter for the crawl")
    ap.add_argument("--sort-on", choices=["created", "price", "updated", "score"])
    ap.add_argument("--sort-order", choices=["asc", "ascending", "desc", "descending", "up", "down"])
    ap.add_argument("--min-price", type=float)
    ap.add_argument("--max-price", type=float)
    ap.add_argument("--currency")
    ap.add_argument("--limit", type=int, default=100, help="page size (1..100)")
    ap.add_argument("--max-offset", type=int, default=10000,
                    help="safety cap for offset pagination (deep offsets degrade)")
    ap.add_argument("--delay-seconds", type=float, default=0.5,
                    help="pacing between pages (API allows 10 rps; be conservative)")
    args = ap.parse_args()

    api_key = os.environ.get("ETSY_API_KEY")
    if not api_key:
        print("ERROR: ETSY_API_KEY env var required (free: https://www.etsy.com/developers)",
              file=sys.stderr)
        sys.exit(2)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(out_dir / "etsy.db")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    schema(conn)
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",
                 (str(SCHEMA_VERSION),))
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('extractor',?)",
                 (EXTRACTOR_VERSION,))
    conn.commit()

    state = {"next_offset": 0, "pages_seen": 0, "last_page": None,
             "started_at": iso_now()}
    if args.resume and (out_dir / "crawl-state.json").exists():
        state.update(json.loads((out_dir / "crawl-state.json").read_text()))
        print(f"[RESUME] continuing from offset {state['next_offset']}")

    with client(api_key) as c:
        fetch_pages(conn, c, out_dir, args, state)

    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('last_run_ended',?)",
                 (iso_now(),))
    conn.commit()
    conn.close()
    print("[DONE] collector finished. DB:", out_dir / "etsy.db")


if __name__ == "__main__":
    main()