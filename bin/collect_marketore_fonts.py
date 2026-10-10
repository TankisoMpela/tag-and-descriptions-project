#!/usr/bin/env python3
"""Durable public Marketore Fonts collector.

The catalog endpoint is the primary source. Public product pages are fetched
separately for descriptions, tags, formats, and license text. Every response
is stored in SQLite (compressed) and mirrored to raw files. Page/detail state
is checkpointed atomically after each successful unit so interruption does not
discard completed work.

Usage:
  python3 bin/collect_marketore_fonts.py --out outputs/research/marketore-live-collector
  python3 bin/collect_marketore_fonts.py --resume --detail-limit 100
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from lxml import html as lhtml

ROOT = "https://marketore.com"
API = f"{ROOT}/api/marketplace/products"
UA = "FontFairyResearch/1.0 (+public catalog research; contact seller if needed)"
EXTRACTOR_VERSION = "marketore-fonts-1.0.0"
STOP = False


def signal_handler(signum, frame):
    global STOP
    STOP = True
    print(f"[WARN] received signal {signum}; finishing current transaction", file=sys.stderr)


for _signal in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_signal, signal_handler)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value or None


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def json_default(value):
    return str(value)


def extract_product_arrays(value: Any):
    if isinstance(value, dict):
        products = value.get("products")
        if isinstance(products, list) and products and all(isinstance(x, dict) for x in products):
            yield products
        for child in value.values():
            yield from extract_product_arrays(child)
    elif isinstance(value, list):
        for child in value:
            yield from extract_product_arrays(child)


def parse_ng_state(document: str) -> list[dict]:
    try:
        tree = lhtml.fromstring(document)
    except Exception:
        return []
    states = tree.xpath("//script[@id='ng-state']/text()")
    products = []
    seen = set()
    for raw in states:
        try:
            state = json.loads(raw)
        except (TypeError, ValueError):
            continue
        for group in extract_product_arrays(state):
            for product in group:
                pid = str(product.get("id") or product.get("slug") or "")
                if pid and pid not in seen:
                    seen.add(pid)
                    products.append(product)
    return products


def parse_detail(document: str, expected_id: str | None, expected_slug: str | None) -> dict:
    result: dict[str, Any] = {
        "detail_title": None,
        "subtitle": None,
        "description": None,
        "detail_product_json": None,
        "tags": [],
        "formats": [],
        "detail_text": None,
    }
    products = parse_ng_state(document)
    matched = None
    for product in products:
        if expected_id and str(product.get("id")) == str(expected_id):
            matched = product
            break
        if expected_slug and product.get("slug") == expected_slug:
            matched = product
            break
    if matched is None and products:
        matched = products[0]
    if matched:
        result["detail_product_json"] = matched
        result["detail_title"] = clean(matched.get("title"))
        result["subtitle"] = clean(matched.get("subtitle"))
        description = matched.get("description")
        if description:
            try:
                result["description"] = clean(lhtml.fromstring(f"<div>{description}</div>").text_content())
            except Exception:
                result["description"] = clean(description)
        result["tags"] = [clean(x) for x in (matched.get("tags") or []) if clean(x)]
    try:
        tree = lhtml.fromstring(document)
        result["detail_title"] = result["detail_title"] or clean(" ".join(tree.xpath("//h1//text()")))
        visible = clean(tree.text_content()) or ""
        result["detail_text"] = visible
        if not result["description"]:
            result["description"] = clean(" ".join(tree.xpath("//*[contains(@class,'prose')]//text()")))
        if not result["tags"]:
            result["tags"] = [
                x for x in (clean(" ".join(a.xpath(".//text()"))) for a in tree.xpath("//a"))
                if x and x.startswith("#")
            ]
        formats = re.findall(r"\b(?:OTF|TTF|TTC|WOFF2?|ZIP|Web Font)\b", visible, re.I)
        result["formats"] = sorted(set(formats), key=str.casefold)
    except Exception:
        pass
    return result


def init_db(con: sqlite3.Connection):
    con.executescript("""
    PRAGMA foreign_keys=ON;
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=FULL;
    CREATE TABLE IF NOT EXISTS crawl_runs (
      run_id TEXT PRIMARY KEY NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
      base_url TEXT NOT NULL, extractor_version TEXT NOT NULL, status TEXT NOT NULL,
      pages_target INTEGER, details_target INTEGER, errors INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS raw_responses (
      response_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
      url TEXT NOT NULL, fetched_at TEXT NOT NULL, status INTEGER,
      content_type TEXT, sha256 TEXT NOT NULL, body_gzip BLOB NOT NULL,
      FOREIGN KEY(run_id) REFERENCES crawl_runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS pages (
      run_id TEXT NOT NULL, page INTEGER NOT NULL, url TEXT NOT NULL,
      status INTEGER, fetched_at TEXT, product_count INTEGER, total INTEGER,
      total_pages INTEGER, response_id INTEGER, error TEXT,
      PRIMARY KEY(run_id, page), FOREIGN KEY(response_id) REFERENCES raw_responses(response_id)
    );
    CREATE TABLE IF NOT EXISTS catalog_occurrences (
      run_id TEXT NOT NULL, product_id TEXT NOT NULL, page INTEGER NOT NULL,
      position INTEGER NOT NULL, sort_key TEXT NOT NULL, seen_at TEXT NOT NULL,
      PRIMARY KEY(run_id, product_id, page), FOREIGN KEY(product_id) REFERENCES items(product_id),
      FOREIGN KEY(run_id) REFERENCES crawl_runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS designers (
      designer_id TEXT PRIMARY KEY, slug TEXT, name TEXT, shop TEXT,
      verified INTEGER, avatar_url TEXT, first_seen TEXT, last_seen TEXT
    );
    CREATE TABLE IF NOT EXISTS items (
      product_id TEXT PRIMARY KEY, slug TEXT UNIQUE, canonical_url TEXT NOT NULL,
      title TEXT, subtitle TEXT, category TEXT, subcategory TEXT, subcategory_slug TEXT,
      price REAL, original_price REAL,
      currency TEXT, on_sale INTEGER, badge TEXT, rating REAL, review_count INTEGER,
      downloads INTEGER, is_test INTEGER, designer_id TEXT, file_size TEXT,
      compatible_with TEXT, license_text TEXT, created_at TEXT, detail_fetched INTEGER DEFAULT 0,
      detail_fetched_at TEXT, description TEXT, detail_text TEXT, published_at TEXT,
      updated_at TEXT, source_run_id TEXT NOT NULL, extractor_version TEXT NOT NULL,
      catalog_json TEXT, detail_json TEXT,
      FOREIGN KEY(designer_id) REFERENCES designers(designer_id)
    );
    CREATE TABLE IF NOT EXISTS item_tags (
      product_id TEXT NOT NULL, tag TEXT NOT NULL, source TEXT NOT NULL,
      PRIMARY KEY(product_id, tag), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE TABLE IF NOT EXISTS item_categories (
      product_id TEXT NOT NULL, category TEXT NOT NULL,
      PRIMARY KEY(product_id, category), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE TABLE IF NOT EXISTS item_images (
      product_id TEXT NOT NULL, image_role TEXT NOT NULL, image_url TEXT NOT NULL,
      PRIMARY KEY(product_id, image_role, image_url), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE TABLE IF NOT EXISTS item_license_prices (
      product_id TEXT NOT NULL, license TEXT NOT NULL, price REAL,
      PRIMARY KEY(product_id, license), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE TABLE IF NOT EXISTS item_formats (
      product_id TEXT NOT NULL, format TEXT NOT NULL,
      PRIMARY KEY(product_id, format), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE TABLE IF NOT EXISTS item_attributes (
      product_id TEXT NOT NULL, attribute TEXT NOT NULL, value TEXT,
      PRIMARY KEY(product_id, attribute), FOREIGN KEY(product_id) REFERENCES items(product_id)
    );
    CREATE INDEX IF NOT EXISTS idx_items_designer ON items(designer_id);
    CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
    CREATE INDEX IF NOT EXISTS idx_items_downloads ON items(downloads);
    CREATE INDEX IF NOT EXISTS idx_tags_tag ON item_tags(tag);
    CREATE INDEX IF NOT EXISTS idx_pages_page ON pages(page);
    CREATE INDEX IF NOT EXISTS idx_occurrences_product ON catalog_occurrences(product_id);
    CREATE INDEX IF NOT EXISTS idx_attributes_attribute ON item_attributes(attribute);
    """)
    existing = {row[1] for row in con.execute("PRAGMA table_info(items)")}
    for column, definition in {
        "subcategory": "TEXT", "subcategory_slug": "TEXT", "file_size": "TEXT",
        "compatible_with": "TEXT", "license_text": "TEXT", "created_at": "TEXT",
        "updated_at": "TEXT", "published_at": "TEXT",
    }.items():
        if column not in existing:
            con.execute(f"ALTER TABLE items ADD COLUMN {column} {definition}")
    con.commit()


def backfill_detail_columns(con: sqlite3.Connection):
    """Normalize fields already preserved in detail_json after a safe resume."""
    rows = con.execute("SELECT product_id,detail_json FROM items WHERE detail_json IS NOT NULL").fetchall()
    for product_id, raw in rows:
        try:
            product = json.loads(raw)
        except (TypeError, ValueError):
            continue
        compatible = product.get("compatibleWith")
        license_value = product.get("license")
        with con:
            con.execute("""UPDATE items SET subcategory=?,subcategory_slug=?,file_size=?,compatible_with=?,
              license_text=?,created_at=?,updated_at=?,published_at=? WHERE product_id=?""", (
                product.get("subcategory"), product.get("subcategorySlug"), product.get("fileSize"),
                json.dumps(compatible, ensure_ascii=False, default=json_default) if compatible is not None else None,
                json.dumps(license_value, ensure_ascii=False, default=json_default) if license_value is not None else None,
                product.get("createdAt"), product.get("updatedAt"), product.get("publishedAt"), product_id))
        for key in ("compatibleWith", "license"):
            value = product.get(key)
            if value is not None:
                con.execute("INSERT OR REPLACE INTO item_attributes VALUES(?,?,?)", (
                    product_id, key, json.dumps(value, ensure_ascii=False, default=json_default)))
        for fmt in product.get("fileFormats") or []:
            con.execute("INSERT OR IGNORE INTO item_formats VALUES(?,?)", (product_id, str(fmt)))
        for role, gallery in (("gallery", product.get("gallery")), ("galleryWebp", product.get("galleryWebp"))):
            if isinstance(gallery, list):
                for image in gallery:
                    if isinstance(image, dict):
                        image = image.get("url") or image.get("src") or image.get("image")
                    if image:
                        con.execute("INSERT OR IGNORE INTO item_images VALUES(?,?,?)", (product_id, role, urljoin(ROOT, str(image))))


def backfill_catalog_occurrences(con: sqlite3.Connection, raw_api: Path, run_id: str):
    """Preserve every page observation, including products repeated across pages."""
    for path in sorted(raw_api.glob("page-*.json")):
        try:
            page = int(path.stem.split("-")[-1])
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        for position, product in enumerate(payload.get("products") or [], 1):
            product_id = str(product.get("id") or "").strip()
            if product_id:
                con.execute("INSERT OR IGNORE INTO catalog_occurrences VALUES(?,?,?,?,?,?)", (
                    run_id, product_id, page, position, "popular", iso_now()))
    con.commit()


def store_raw(con, run_id: str, url: str, response: httpx.Response) -> int:
    body = response.content
    digest = hashlib.sha256(body).hexdigest()
    cur = con.execute(
        "INSERT INTO raw_responses(run_id,url,fetched_at,status,content_type,sha256,body_gzip) VALUES(?,?,?,?,?,?,?)",
        (run_id, url, iso_now(), response.status_code, response.headers.get("content-type"), digest, gzip.compress(body)),
    )
    return int(cur.lastrowid)


def upsert_catalog(con, run_id: str, product: dict):
    pid = str(product.get("id") or "").strip()
    if not pid:
        return
    author = product.get("author") or {}
    designer_id = str(author.get("id") or "") or None
    if designer_id:
        con.execute("""INSERT INTO designers(designer_id,slug,name,shop,verified,avatar_url,first_seen,last_seen)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(designer_id) DO UPDATE SET
          slug=excluded.slug,name=excluded.name,shop=excluded.shop,verified=excluded.verified,
          avatar_url=excluded.avatar_url,last_seen=excluded.last_seen""", (
            designer_id, author.get("slug"), author.get("name"), author.get("shop"),
            int(bool(author.get("verified"))), urljoin(ROOT, author.get("avatar") or ""), iso_now(), iso_now()))
    con.execute("""INSERT INTO items(product_id,slug,canonical_url,title,category,price,original_price,currency,
      on_sale,badge,rating,review_count,downloads,is_test,designer_id,source_run_id,extractor_version,catalog_json)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET
      slug=excluded.slug,canonical_url=excluded.canonical_url,title=excluded.title,category=excluded.category,
      price=excluded.price,original_price=excluded.original_price,currency=excluded.currency,on_sale=excluded.on_sale,
      badge=excluded.badge,rating=excluded.rating,review_count=excluded.review_count,downloads=excluded.downloads,
      is_test=excluded.is_test,designer_id=excluded.designer_id,source_run_id=excluded.source_run_id,
      extractor_version=excluded.extractor_version,catalog_json=excluded.catalog_json""", (
        pid, product.get("slug"), urljoin(ROOT, "/" + str(product.get("slug") or "")), product.get("title"),
        product.get("category"), product.get("price"), product.get("originalPrice"), "USD",
        int(bool(product.get("onSale"))), product.get("badge"), product.get("rating"), product.get("reviewCount"),
        product.get("downloads"), int(bool(product.get("isTest"))), designer_id, run_id, EXTRACTOR_VERSION,
        json.dumps(product, ensure_ascii=False, default=json_default)))
    con.execute("INSERT OR IGNORE INTO item_categories VALUES(?,?)", (pid, product.get("category") or "Fonts"))
    for role in ("image", "imageCard", "imageCard480", "imageCard960", "imageCard1280"):
        if product.get(role):
            con.execute("INSERT OR IGNORE INTO item_images VALUES(?,?,?)", (pid, role, urljoin(ROOT, product[role])))
    for license_name, price in (product.get("licensePrices") or {}).items():
        con.execute("INSERT OR REPLACE INTO item_license_prices VALUES(?,?,?)", (pid, license_name, price))


def apply_detail(con, product_id: str, detail: dict, response_id: int | None):
    product = detail.get("detail_product_json") or {}
    con.execute("""UPDATE items SET subtitle=COALESCE(?,subtitle),description=COALESCE(?,description),
      detail_text=COALESCE(?,detail_text),detail_fetched=1,detail_fetched_at=?,detail_json=? WHERE product_id=?""", (
        detail.get("subtitle"), detail.get("description"), detail.get("detail_text"), iso_now(),
        json.dumps(product, ensure_ascii=False, default=json_default), product_id))
    for tag in detail.get("tags") or product.get("tags") or []:
        if tag:
            con.execute("INSERT OR IGNORE INTO item_tags VALUES(?,?,?)", (product_id, tag, "detail"))
    for fmt in detail.get("formats") or []:
        con.execute("INSERT OR IGNORE INTO item_formats VALUES(?,?)", (product_id, fmt))


def fetch(client: httpx.Client, url: str, retries: int, delay: float) -> httpx.Response:
    time.sleep(max(0.0, delay))
    last = None
    for attempt in range(retries + 1):
        try:
            response = client.get(url)
            if response.status_code == 429 or response.status_code >= 500:
                last = RuntimeError(f"HTTP {response.status_code}")
                time.sleep(min(30.0, 2 ** attempt))
                continue
            response.raise_for_status()
            return response
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(min(30.0, 2 ** attempt))
    raise RuntimeError(f"request failed: {url}: {last}")


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"pages_done": [], "details_done": [], "errors": []}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Durable Marketore Fonts crawler")
    parser.add_argument("--out", type=Path, default=Path("outputs/research/marketore-live-collector"))
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--size", type=int, default=48)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--detail-limit", type=int, default=None)
    parser.add_argument("--no-details", action="store_true")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    db_path = args.db or args.out / "marketore.db"
    state_path = args.out / "crawl-state.json"
    raw_api = args.out / "raw" / "api"
    raw_detail = args.out / "raw" / "details"
    if args.reset:
        for path in (db_path, state_path):
            if path.exists():
                path.unlink()
    state = load_state(state_path) if args.resume else {"pages_done": [], "details_done": [], "errors": []}
    run_id = (state.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")) if args.resume else datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state["run_id"] = run_id
    state["started_at"] = state.get("started_at") or iso_now()
    state["db_path"] = str(db_path)
    con = sqlite3.connect(db_path)
    init_db(con)
    backfill_detail_columns(con)
    con.execute("INSERT OR IGNORE INTO crawl_runs(run_id,started_at,base_url,extractor_version,status) VALUES(?,?,?,?,?)",
                (run_id, state["started_at"], ROOT, EXTRACTOR_VERSION, "running"))
    con.commit()
    backfill_catalog_occurrences(con, args.out / "raw" / "api", run_id)
    products_by_id = {}
    con.row_factory = sqlite3.Row
    for row in con.execute("SELECT product_id,slug FROM items"):
        products_by_id[row["product_id"]] = {"id": row["product_id"], "slug": row["slug"]}
    con.row_factory = None

    with httpx.Client(headers={"User-Agent": UA, "Accept": "application/json, text/html"}, follow_redirects=True, timeout=45) as client:
        total_pages = state.get("total_pages")
        if total_pages:
            state["pages_done"] = [p for p in state.get("pages_done", []) if p < total_pages]
        page = 0
        while not STOP and (args.max_pages is None or page < args.max_pages):
            # Marketore pages are zero-based: valid pages are 0..totalPages-1.
            if total_pages and page >= total_pages:
                break
            if page in state.get("pages_done", []):
                page += 1
                continue
            url = f"{API}?category=fonts&sort=popular&page={page}&size={args.size}"
            try:
                response = fetch(client, url, args.retries, args.delay)
                payload = response.json()
                products = payload.get("products") or []
                pagination = payload.get("pagination") or {}
                total_pages = int(pagination.get("totalPages") or total_pages or page)
                with con:
                    response_id = store_raw(con, run_id, url, response)
                    for product in products:
                        upsert_catalog(con, run_id, product)
                        products_by_id[str(product.get("id"))] = product
                    con.execute("""INSERT OR REPLACE INTO pages VALUES(?,?,?,?,?,?,?,?,?,?)""", (
                        run_id, page, url, response.status_code, iso_now(), len(products),
                        pagination.get("total"), pagination.get("totalPages"), response_id, None))
                raw_api.mkdir(parents=True, exist_ok=True)
                atomic_write(raw_api / f"page-{page:04d}.json", response.text)
                state["pages_done"] = sorted(set(state.get("pages_done", []) + [page]))
                state["total_pages"] = total_pages
                atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2))
                print(f"[PAGE {page}/{total_pages}] {len(products)} products")
                if page >= total_pages:
                    break
                page += 1
            except Exception as exc:
                message = {"stage": "catalog", "page": page, "url": url, "error": str(exc), "at": iso_now()}
                state.setdefault("errors", []).append(message)
                atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2))
                print(f"[ERROR] {message}", file=sys.stderr)
                break

        if not args.no_details and not STOP:
            detail_rows = list(products_by_id.values())
            detail_rows.sort(key=lambda row: int(row.get("id", 0)) if str(row.get("id", "")).isdigit() else str(row.get("id", "")))
            if args.detail_limit is not None:
                detail_rows = detail_rows[:args.detail_limit]
            for index, product in enumerate(detail_rows, 1):
                pid = str(product.get("id") or "")
                if not pid or pid in set(state.get("details_done", [])):
                    continue
                slug = product.get("slug")
                url = urljoin(ROOT, f"/{slug}")
                try:
                    response = fetch(client, url, args.retries, args.delay)
                    detail = parse_detail(response.text, pid, slug)
                    with con:
                        response_id = store_raw(con, run_id, url, response)
                        apply_detail(con, pid, detail, response_id)
                    raw_detail.mkdir(parents=True, exist_ok=True)
                    atomic_write(raw_detail / f"{pid}.html", response.text)
                    state["details_done"] = sorted(set(state.get("details_done", []) + [pid]))
                    atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2))
                    print(f"[DETAIL {index}/{len(detail_rows)}] {pid} {slug}")
                except Exception as exc:
                    message = {"stage": "detail", "product_id": pid, "url": url, "error": str(exc), "at": iso_now()}
                    state.setdefault("errors", []).append(message)
                    atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2))
                    print(f"[ERROR] {message}", file=sys.stderr)

    partial = bool(args.max_pages and state.get("total_pages") and args.max_pages < state["total_pages"])
    status = "interrupted" if STOP else ("complete-with-errors" if state.get("errors") else ("partial" if partial else "complete"))
    con.execute("UPDATE crawl_runs SET finished_at=?,status=?,errors=? WHERE run_id=?",
                (iso_now(), status, len(state.get("errors", [])), run_id))
    con.commit()
    con.close()
    state["finished_at"] = iso_now()
    state["status"] = status
    atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2))
    print(f"[{status.upper()}] DB: {db_path}")
    return 0 if not state.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
