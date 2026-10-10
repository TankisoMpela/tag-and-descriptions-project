#!/usr/bin/env python3
"""Build a queryable SQLite database from BOOTH collector output.

Loads one collector run (JSONL, CSV, or crawl-state.json — it auto-detects),
optionally the FontFairy rank CSV and the frozen tag bank, and writes a fully
normalized schema for SQL reasoning:

    items                 one row per BOOTH item (all crawl + detail fields)
    item_tags             normalized tags        (item_id, tag, tag_pos)
    variants              normalized variants    (item_id, name, price_jpy)
    formats               normalized formats     (item_id, format)
    papermoon_rank        FontFairy shop items   (join key item_id)
    tag_bank              frozen bank tags + evidence columns
    neighbours            for each PM item, the items ±NEIGHBOUR_WINDOW in
                          crawl order around it (the fail/survive analysis)
    v_pm_items            items joined to papermoon_rank
    v_neighbour_tags      tag usage across each PM item's neighbours
    v_pm_missing_tags     neighbours' recurring tags the PM item does NOT use

The DB is disposable: every build is a full rebuild (fast at this size).

Usage:
  # live / mid-crawl refresh (reads crawl-state.json atomically):
  python3 bin/build_booth_db.py \
    --source outputs/research/booth-live-collector/2026-09-08/fonts-popular \
    --rank ~/Downloads/booth-rank-papermoonstudio-2026-09-08.csv \
    --bank outputs/research/booth-font-tag-bank.md

Then query:
  python3 bin/query_booth_db.py "SELECT * FROM items WHERE item_like_count > 5000 ORDER BY item_like_count DESC LIMIT 10;"
  sqlite3 outputs/research/booth-live-collector/booth.db "SELECT tag, count(*) FROM item_tags GROUP BY tag ORDER BY 2 DESC LIMIT 20;"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

DEFAULT_DB = Path("outputs/research/booth-live-collector/booth.db")

# ---------------------------------------------------------------- record loaders

def _clean(v, default=None):
    if v is None or v == "":
        return default
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return default
    return v


def load_jsonl(path: Path):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_state(path: Path):
    state = json.loads(path.read_text(encoding="utf-8"))
    products = state.get("products", [])
    details = state.get("details", {})
    for rec in products:
        detail = details.get(str(rec.get("item_id"))) or details.get(rec.get("item_id"))
        if detail:
            rec = dict(rec)
            rec.update(detail)
            yield rec
        else:
            yield rec


def _parse_variant_string(s):
    """'Name:¥1200 | Name2:¥349' -> [{'name': ..., 'priceJpy': ...}]."""
    if not s:
        return []
    out = []
    for part in str(s).split("|"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.*):(¥?\d+)$", part)
        if m:
            out.append({"name": m.group(1).strip(), "priceJpy": int(m.group(2).replace("¥", ""))})
        else:
            out.append({"name": part, "priceJpy": None})
    return out


def _parse_formats_string(s):
    return [x for x in re.split(r"\s+", str(s or "").strip()) if x]


def normalize(rec):
    """Normalize any collector row (JSONL/CSV/state) into canonical fields."""
    tags = _clean(rec.get("tags"))
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split("|") if t.strip()]
    tags = tags or []

    variants = rec.get("variants")
    if isinstance(variants, str):
        variants = _parse_variant_string(variants)
    if not isinstance(variants, list):
        variants = variants if variants else []
    variants = [v for v in variants if isinstance(v, dict)]

    formats = rec.get("formats")
    if isinstance(formats, str):
        formats = _parse_formats_string(formats)
    if not isinstance(formats, list):
        formats = formats if formats else []

    # camelCase (JSONL/state detail) -> canonical
    def pick(snake, camel):
        return _clean(rec.get(snake, rec.get(camel)))

    published = pick("published", "published")
    # normalize to zero-padded YYYY-MM-DD so julianday() works
    pub_norm = ""
    pub_year = None
    if published:
        m = re.match(r"^(\d{4})[年\/\-.](\d{1,2})(?:[月\/\-.](\d{1,2}))?", published)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
            pub_norm = f"{y:04d}-{mo:02d}-{d:02d}"
            pub_year = y

    try:
        item_id = int(rec["item_id"])
    except (KeyError, TypeError, ValueError):
        item_id = None

    def pint(v):
        try:
            if v is None or v == "":
                return None
            return int(float(str(v).replace(",", "").replace("¥", "")))
        except (TypeError, ValueError):
            return None

    return {
        "item_id": item_id,
        "item_url": _clean(rec.get("item_url")) or "",
        "title": _clean(rec.get("title", rec.get("detailTitle"))),
        "brand": _clean(rec.get("brand")) or "",
        "shop_name": _clean(rec.get("shop_name", rec.get("shopName"))) or "",
        "shop_url": _clean(rec.get("shop_url", rec.get("shopUrl"))) or "",
        "price_jpy": pint(rec.get("price_jpy")),
        "price_min": pint(pick("price_min", "priceMin")),
        "price_max": pint(pick("price_max", "priceMax")),
        "page": pint(rec.get("page")),
        "position": pint(rec.get("position")),
        "absolute_position": pint(rec.get("absolute_position")),
        "sort_mode": _clean(rec.get("sort_mode")) or "",
        "context_category": _clean(rec.get("context_category")) or "",
        "crawl_date": _clean(rec.get("crawl_date")) or date.today().isoformat(),
        "card_image_count": pint(rec.get("card_image_count")),
        "detail_fetched": 1 if rec.get("detail_fetched") or rec.get("detailFetched") or "description" in rec else 0,
        "detail_fetched_at": _clean(pick("detail_fetched_at", "detailFetchedAt")),
        "description": _clean(rec.get("description")) or "",
        "description_length": pint(pick("description_length", "descriptionLength")),
        "tag_count": len(tags),
        "tag_source": _clean(pick("tag_source", "tagSource")) or "",
        "published": pub_norm,
        "published_year": pub_year,
        "item_like_count": pint(pick("item_like_count", "likeCountItem")),
        "item_image_count": pint(pick("item_image_count", "imageCountItem")),
        "category_breadcrumb": _clean(pick("category_breadcrumb", "categoryBreadcrumb")) or "",
        "extractor_version": _clean(rec.get("extractor_version")) or "",
        "tags": tags,
        "variants": variants,
        "formats": formats,
    }


def iter_records(source: Path):
    """Yield canonical records from a collector dir or file."""
    p = Path(source)
    if p.is_dir():
        state_f = p / "crawl-state.json"
        jsonl = sorted(p.glob("*-items.jsonl"))
        csvf = sorted(p.glob("*-items.csv"))
        if state_f.exists():
            yield from load_state(state_f)
            return
        if jsonl:
            for row in load_jsonl(jsonl[0]):
                yield row
            return
        if csvf:
            yield from load_csv(csvf[0])
            return
        raise SystemExit(f"No collector output found in {p}")
    if p.suffix == ".jsonl":
        yield from load_jsonl(p)
    elif p.suffix == ".csv":
        yield from load_csv(p)
    elif p.name == "crawl-state.json":
        yield from load_state(p)
    else:
        raise SystemExit(f"Unsupported source file: {p}")


# ---------------------------------------------------------------- tag bank

def load_tag_bank(path):
    """Parse the frozen bank's priority table into rows."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            # | Rank | Tag | Family | Language | Overall | Font cat | Activity | Evidence | Fit | Route |
            if len(parts) >= 8 and parts[1].isdigit():
                def num(x):
                    try:
                        return int(x.replace(",", "")) if x else None
                    except ValueError:
                        return None
                rows.append({
                    "bank_rank": num(parts[1]),
                    "tag": parts[2],
                    "family": parts[3] if len(parts) > 3 else "",
                    "language": parts[4] if len(parts) > 4 else "",
                    "overall": num(parts[5]) if len(parts) > 5 else None,
                    "font_category": num(parts[6]) if len(parts) > 6 else None,
                    "activity": parts[7] if len(parts) > 7 else "",
                    "evidence_tier": parts[8] if len(parts) > 8 else "",
                    "fit_rule": parts[9] if len(parts) > 9 else "",
                    "exact_route": parts[10] if len(parts) > 10 else "",
                })
    return rows


def load_rank_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "global_rank": int(r["global_rank"]) if r.get("global_rank") else None,
                "page": int(r["page"]) if r.get("page") else None,
                "in_page_rank": int(r["in_page_rank"]) if r.get("in_page_rank") else None,
                "item_id": int(r["item_id"]) if r.get("item_id") else None,
                "title": r.get("title", ""),
                "price": int(r["price"]) if r.get("price") and str(r["price"]).strip() else None,
                "shop_brand": r.get("shop_brand", ""),
                "shop_name": r.get("shop_name", ""),
                "shop_url": r.get("shop_url", ""),
                "item_url": r.get("item_url", ""),
            })
    return rows


# ---------------------------------------------------------------- schema

SCHEMA = """
CREATE TABLE items (
  item_id INTEGER PRIMARY KEY,
  item_url TEXT NOT NULL,
  title TEXT,
  brand TEXT,
  shop_name TEXT,
  shop_url TEXT,
  price_jpy INTEGER,
  price_min INTEGER,
  price_max INTEGER,
  page INTEGER,
  position INTEGER,
  absolute_position INTEGER,
  sort_mode TEXT,
  context_category TEXT,
  crawl_date TEXT,
  card_image_count INTEGER,
  detail_fetched INTEGER,
  detail_fetched_at TEXT,
  description TEXT,
  description_length INTEGER,
  tag_count INTEGER,
  tag_source TEXT,
  published TEXT,
  published_year INTEGER,
  item_like_count INTEGER,
  item_image_count INTEGER,
  category_breadcrumb TEXT,
  extractor_version TEXT,
  tags_json TEXT,
  variants_json TEXT,
  formats_json TEXT
);
CREATE TABLE item_tags (
  item_id INTEGER NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
  tag TEXT NOT NULL,
  tag_pos INTEGER,
  PRIMARY KEY (item_id, tag)
);
CREATE TABLE variants (
  item_id INTEGER NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
  variant_name TEXT,
  price_jpy INTEGER,
  variant_pos INTEGER
);
CREATE TABLE formats (
  item_id INTEGER NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
  format TEXT
);
CREATE TABLE papermoon_rank (
  global_rank INTEGER,
  page INTEGER,
  in_page_rank INTEGER,
  item_id INTEGER PRIMARY KEY,
  title TEXT,
  price INTEGER,
  shop_brand TEXT,
  shop_name TEXT,
  shop_url TEXT,
  item_url TEXT
);
CREATE TABLE tag_bank (
  bank_rank INTEGER,
  tag TEXT PRIMARY KEY,
  family TEXT,
  language TEXT,
  overall INTEGER,
  font_category INTEGER,
  activity TEXT,
  evidence_tier TEXT,
  fit_rule TEXT,
  exact_route TEXT
);

CREATE INDEX idx_items_likes   ON items(item_like_count DESC);
CREATE INDEX idx_items_pub     ON items(published);
CREATE INDEX idx_items_abs     ON items(absolute_position);
CREATE INDEX idx_items_price   ON items(price_min);
CREATE INDEX idx_items_detail_pub ON items(detail_fetched, published);
CREATE INDEX idx_items_price_pub  ON items(price_min, published);
CREATE INDEX idx_tags_tag      ON item_tags(tag);
CREATE INDEX idx_tags_tag_nocase ON item_tags(tag COLLATE NOCASE);
CREATE INDEX idx_tags_item     ON item_tags(item_id);
CREATE INDEX idx_variants_pr   ON variants(price_jpy);

CREATE VIEW v_pm_items AS
SELECT i.*, r.global_rank AS pm_rank
FROM items i
JOIN papermoon_rank r USING (item_id);

CREATE VIEW v_neighbour_tags AS
SELECT n.pm_item_id, t.tag AS neighbour_tag, COUNT(DISTINCT n.neighbour_id) AS items_using,
       COUNT(*) AS instances
FROM neighbours n
JOIN item_tags t ON t.item_id = n.neighbour_id
GROUP BY n.pm_item_id, t.tag;

CREATE VIEW v_pm_missing_tags AS
SELECT nt.pm_item_id, nt.neighbour_tag, nt.items_using,
       CASE WHEN b.tag IS NOT NULL THEN 'banked' ELSE 'NEW-CANDIDATE' END AS bank_status
FROM v_neighbour_tags nt
LEFT JOIN tag_bank b ON b.tag = nt.neighbour_tag
WHERE NOT EXISTS (
  SELECT 1 FROM item_tags mine WHERE mine.item_id = nt.pm_item_id AND mine.tag = nt.neighbour_tag
);

CREATE VIEW v_age_likes AS
SELECT item_id, title, published, published_year,
       julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published) AS days_since_publish,
       item_like_count,
       ROUND(item_like_count * 1.0 / NULLIF(julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published), 0), 2) AS likes_per_day
FROM items
WHERE detail_fetched = 1 AND published != ''
  AND item_like_count IS NOT NULL;
"""


def build(args):
    db_path = Path(args.db)
    out_dir = db_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    records = list(iter_records(Path(args.source)))
    # de-dupe by item_id (keep last occurrence — richest detail)
    by_id = {}
    for r in records:
        if r["item_id"] is None:
            continue
        by_id[r["item_id"]] = normalize(r)
    records = list(by_id.values())

    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA)

    tag_bank_rows = load_tag_bank(args.bank) if args.bank and Path(args.bank).exists() else []
    rank_rows = load_rank_csv(args.rank) if args.rank and Path(args.rank).exists() else []

    items = []
    for r in records:
        items.append((
            r["item_id"], r["item_url"], r["title"], r["brand"], r["shop_name"],
            r["shop_url"], r["price_jpy"], r["price_min"], r["price_max"], r["page"],
            r["position"], r["absolute_position"], r["sort_mode"], r["context_category"],
            r["crawl_date"], r["card_image_count"], r["detail_fetched"], r["detail_fetched_at"],
            r["description"], r["description_length"], r["tag_count"], r["tag_source"],
            r["published"], r["published_year"], r["item_like_count"], r["item_image_count"],
            r["category_breadcrumb"], r["extractor_version"],
            json.dumps(r["tags"], ensure_ascii=False),
            json.dumps(r["variants"], ensure_ascii=False),
            json.dumps(r["formats"], ensure_ascii=False),
        ))

    tag_rows, var_rows, fmt_rows = [], [], []
    for r in records:
        iid = r["item_id"]
        for pos, t in enumerate(r["tags"]):
            tag_rows.append((iid, t, pos))
        for pos, v in enumerate(r["variants"]):
            name = v.get("name")
            try:
                vprice = v.get("priceJpy")
                if vprice is not None:
                    vprice = int(vprice)
            except (TypeError, ValueError):
                vprice = None
            var_rows.append((iid, name or "", vprice, pos))
        for f in r["formats"]:
            fmt_rows.append((iid, f))

    con.executemany("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", items)
    con.executemany("INSERT INTO item_tags VALUES (?,?,?)", tag_rows)
    con.executemany("INSERT INTO variants VALUES (?,?,?,?)", var_rows)
    con.executemany("INSERT INTO formats VALUES (?,?)", fmt_rows)
    con.executemany("INSERT INTO tag_bank VALUES (?,?,?,?,?,?,?,?,?,?)", [
        (t["bank_rank"], t["tag"], t["family"], t["language"], t["overall"], t["font_category"],
         t["activity"], t["evidence_tier"], t["fit_rule"], t["exact_route"])
        for t in tag_bank_rows
    ])
    con.executemany("INSERT INTO papermoon_rank VALUES (?,?,?,?,?,?,?,?,?,?)", [
        (r["global_rank"], r["page"], r["in_page_rank"], r["item_id"], r["title"], r["price"],
         r["shop_brand"], r["shop_name"], r["shop_url"], r["item_url"])
        for r in rank_rows
    ])

    # neighbours: ± window around each PM item in crawl order
    if rank_rows:
        window = args.neighbour_window
        con.execute(f"""
            CREATE TABLE neighbours AS
            SELECT pm.item_id AS pm_item_id, pm.absolute_position AS pm_pos,
                   pm.pm_rank, n.item_id AS neighbour_id,
                   n.absolute_position AS nb_pos, n.title AS nb_title,
                   n.item_like_count AS nb_likes, n.price_min AS nb_price_min
            FROM (
                SELECT i.item_id, i.absolute_position, r.global_rank AS pm_rank
                FROM items i JOIN papermoon_rank r USING (item_id)
                WHERE i.absolute_position IS NOT NULL
            ) pm
            JOIN items n ON n.item_id <> pm.item_id
              AND n.absolute_position BETWEEN pm.absolute_position - {int(window)}
                                         AND pm.absolute_position + {int(window)}
        """)
    else:
        con.execute("CREATE TABLE neighbours AS SELECT 0 AS pm_item_id, 0 AS pm_pos, NULL AS pm_rank, 0 AS neighbour_id, 0 AS nb_pos, '' AS nb_title, NULL AS nb_likes, NULL AS nb_price_min WHERE 1=0")

    con.commit()

    # ---- summary
    def one(q):
        return con.execute(q).fetchone()[0]

    n_items = one("SELECT count(*) FROM items")
    n_det = one("SELECT count(*) FROM items WHERE detail_fetched=1")
    n_tags_rows = one("SELECT count(*) FROM item_tags")
    n_tags_items = one("SELECT count(*) FROM items WHERE tag_count > 0 AND detail_fetched=1")
    n_likes = one("SELECT count(*) FROM items WHERE item_like_count IS NOT NULL")
    n_pub = one("SELECT count(*) FROM items WHERE published != ''")
    n_pm = one("SELECT count(*) FROM papermoon_rank")
    n_bank = one("SELECT count(*) FROM tag_bank")
    print(f"DB written: {db_path}")
    print(f"  items: {n_items}  (detail_fetched {n_det})")
    print(f"  tag rows: {n_tags_rows} across {n_tags_items} detailed items")
    print(f"  items with real likes: {n_likes} | with published date: {n_pub}")
    print(f"  papermoon_rank rows: {n_pm} | tag_bank rows: {n_bank}")
    if rank_rows:
        nb = one("SELECT count(*) FROM neighbours")
        print(f"  neighbours (window ±{args.neighbour_window}): {nb}")
    con.close()


def main():
    ap = argparse.ArgumentParser(description="Build a SQLite DB from BOOTH collector output")
    ap.add_argument("--source", required=True,
                    help="Collector dir or file (jsonl/csv/crawl-state.json)")
    ap.add_argument("--rank", default=str(Path.home() / "Downloads/booth-rank-papermoonstudio-2026-09-08.csv"),
                    help="FontFairy rank CSV")
    ap.add_argument("--bank", default="outputs/research/booth-font-tag-bank.md",
                    help="Frozen tag bank markdown")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Output SQLite path")
    ap.add_argument("--neighbour-window", type=int, default=50,
                    help="±positions around each PM item for the neighbours table")
    build(ap.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())