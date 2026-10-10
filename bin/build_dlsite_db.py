#!/usr/bin/env python3
"""Build a queryable SQLite database from DLsite Tools/Accessories collector output.

Loads one collector run (JSONL, CSV, or crawl-state.json — auto-detects),
loads the frozen DLsite font tag bank, and writes a normalized schema for SQL reasoning:

    items                 one row per DLsite item (all crawl, ajax, and detail fields)
    item_genres           normalized genres       (product_id, genre)
    item_formats          normalized file formats (product_id, format)
    custom_genres         campaign/custom genres  (product_id, custom_genre)
    makers                maker/circle aggregates (maker_id, maker_name, item_count, font_count, total_sales, median_sales)
    tag_bank              frozen DLsite tag bank  (keyword, meaning, evidence_tier, category, notes)
    v_fonts               view of items where is_font = 1
    v_age_sales           items with days_since_publish, sales_per_year, fav_to_sales_ratio

The DB is disposable: every build is a full rebuild (mirrors booth.db pipeline).

Usage:
  python3 bin/build_dlsite_db.py \
    --source outputs/research/dlsite-live-collector/2026-09-09/tools-accessories \
    --bank outputs/research/dlsite-font-tag-bank.md \
    --db outputs/research/dlsite-live-collector/dlsite.db

Then query:
  python3 bin/query_dlsite_db.py "SELECT product_id, title, sales_count, favorites_count, price_jpy FROM v_fonts ORDER BY sales_count DESC LIMIT 10;"
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlsite_tag_bank import parse_tag_bank as _parse_tag_bank  # noqa: E402

DEFAULT_DB = Path("outputs/research/dlsite-live-collector/dlsite.db")
DEFAULT_BANK = Path("outputs/research/dlsite-font-tag-bank.md")


def _clean(v, default=None):
    if v is None or v == "":
        return default
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return default
    return v


def pint(v):
    try:
        if v is None or v == "":
            return None
        return int(float(str(v).replace(",", "").replace("¥", "").replace("$", "")))
    except (TypeError, ValueError):
        return None


def pfloat(v):
    try:
        if v is None or v == "":
            return None
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def load_crawl_state(path: Path):
    with path.open("r", encoding="utf-8") as f:
        state = json.load(f)
    products = state.get("products", [])
    details = state.get("details", {})
    merged = []
    for p in products:
        d = details.get(p.get("product_id")) or {}
        rec = {**p, **d}
        if d:
            rec["detailFetched"] = True
        merged.append(rec)
    return merged


def auto_load_source(source_dir: Path):
    if not source_dir.exists():
        raise FileNotFoundError(f"Source path not found: {source_dir}")

    if source_dir.is_file():
        if source_dir.suffix == ".jsonl":
            return load_jsonl(source_dir)
        if source_dir.suffix == ".csv":
            return load_csv(source_dir)
        if source_dir.name == "crawl-state.json":
            return load_crawl_state(source_dir)
        raise ValueError(f"Unknown source file format: {source_dir}")

    # directory auto-detection preference:
    # 1. crawl-state.json (live/latest)
    # 2. tools-accessories-items.jsonl
    # 3. tools-accessories-items.csv
    state_file = source_dir / "crawl-state.json"
    if state_file.exists():
        return load_crawl_state(state_file)

    jsonl_files = list(source_dir.glob("*.jsonl"))
    if jsonl_files:
        return load_jsonl(jsonl_files[0])

    csv_files = list(source_dir.glob("*.csv"))
    if csv_files:
        return load_csv(csv_files[0])

    raise FileNotFoundError(f"No valid data file found in {source_dir}")


def normalize_item(rec: dict) -> dict:
    pid = _clean(rec.get("product_id"))
    if not pid:
        pid = _clean(rec.get("id"))
    
    title = _clean(rec.get("title") or rec.get("detailTitle") or rec.get("work_name"))
    title_jp = _clean(rec.get("title_jp") or rec.get("work_name") or title)

    published = _clean(rec.get("published") or rec.get("regist_date"))
    pub_norm = ""
    pub_year = None
    if published:
        m = re.search(r"(\d{4})[年\/\-.](\d{1,2})(?:[月\/\-.](\d{1,2}))?", str(published))
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
            pub_norm = f"{y:04d}-{mo:02d}-{d:02d}"
            pub_year = y

    is_font_val = rec.get("is_font")
    is_font = 1 if (is_font_val is True or str(is_font_val).lower() in ("yes", "1", "true")) else 0

    # Secondary precision check
    fmt_lower = str(rec.get("file_format") or "").lower()
    title_lower = (str(title) + " " + str(title_jp)).lower()
    desc_lower = str(rec.get("description") or "").lower()

    has_font_format = any(k in fmt_lower for k in ["トゥルータイプ", "フォント", "書体", "ttf", "otf", "ttc"])
    has_font_title = any(k in title_lower for k in ["フォント", "書体", "font", "typeface"])

    if has_font_format or has_font_title:
        is_font = 1
    elif any(k in desc_lower for k in ["フォント", "書体", "ttf", "otf", "ttc"]):
        if not any(k in fmt_lower for k in ["アプリケーション", "プラグイン", "ゲーム", "exe", "apk"]):
            is_font = 1
        else:
            is_font = 0

    if any(k in title_lower for k in [
        "synthesizer", "voicepeak", "voiceroid", "cevio", "a.i.voice", "歌声",
        "ティラノビルダー", "tyranobuilder", "srpg studio", "エンジン", "制作ツール"
    ]):
        if not has_font_format:
            is_font = 0

    detail_fetched = 1 if (rec.get("detail_fetched") in ("yes", True, 1) or rec.get("detailFetched") or rec.get("description")) else 0

    cg_raw = rec.get("custom_genres")
    custom_genres = []
    if isinstance(cg_raw, list):
        custom_genres = [str(x).strip() for x in cg_raw if str(x).strip()]
    elif isinstance(cg_raw, str) and cg_raw:
        custom_genres = [x.strip() for x in cg_raw.split("|") if x.strip()]

    return {
        "product_id": pid,
        "item_url": _clean(rec.get("item_url")) or f"https://www.dlsite.com/home/work/=/product_id/{pid}.html",
        "title": title,
        "title_jp": title_jp,
        "maker_id": _clean(rec.get("maker_id")) or "",
        "maker_name": _clean(rec.get("maker_from_outline") or rec.get("maker_name")) or "",
        "maker_url": _clean(rec.get("maker_url")) or "",
        "price_jpy": pint(rec.get("price_jpy")),
        "official_price": pint(rec.get("official_price")),
        "page": pint(rec.get("page")),
        "position": pint(rec.get("position")),
        "absolute_position": pint(rec.get("absolute_position")),
        "work_type": _clean(rec.get("work_type")) or "TOL",
        "context_category": _clean(rec.get("context_category")) or "Tools / Accessories",
        "crawl_date": _clean(rec.get("crawl_date")) or date.today().isoformat(),
        "thumb_url": _clean(rec.get("thumb_url")) or "",
        "detail_fetched": detail_fetched,
        "detail_fetched_at": _clean(rec.get("detail_fetched_at") or rec.get("detailFetchedAt")),
        "description": _clean(rec.get("description")) or "",
        "description_length": pint(rec.get("description_length") or rec.get("descriptionLength")) or len(_clean(rec.get("description")) or ""),
        "genre": _clean(rec.get("genre")) or "",
        "file_format": _clean(rec.get("file_format")) or "",
        "file_size": _clean(rec.get("file_size")) or "",
        "published": pub_norm,
        "published_year": pub_year,
        "sales_count": pint(rec.get("sales_count")),
        "favorites_count": pint(rec.get("favorites_count")),
        "rating_count": pint(rec.get("rating_count")),
        "rate_average": pfloat(rec.get("rate_average")),
        "review_count": pint(rec.get("review_count")),
        "language": _clean(rec.get("language")) or "",
        "is_font": is_font,
        "custom_genres": custom_genres,
        "extractor_version": _clean(rec.get("extractor_version")) or "cli-dlsite-1.1.0",
    }


def parse_tag_bank(bank_path: Path):
    """Parse ONLY section-5 keyword tables from the tag bank (shared canonical parser)."""
    return _parse_tag_bank(str(bank_path))


def build_database(records, tag_bank_rows, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("PRAGMA journal_mode = WAL;")

    # 1. items table
    cur.execute("""
    CREATE TABLE items (
        product_id TEXT PRIMARY KEY,
        item_url TEXT NOT NULL,
        title TEXT,
        title_jp TEXT,
        maker_id TEXT,
        maker_name TEXT,
        maker_url TEXT,
        price_jpy INTEGER,
        official_price INTEGER,
        page INTEGER,
        position INTEGER,
        absolute_position INTEGER,
        work_type TEXT,
        context_category TEXT,
        crawl_date TEXT,
        thumb_url TEXT,
        detail_fetched INTEGER,
        detail_fetched_at TEXT,
        description TEXT,
        description_length INTEGER,
        genre TEXT,
        file_format TEXT,
        file_size TEXT,
        published TEXT,
        published_year INTEGER,
        sales_count INTEGER,
        favorites_count INTEGER,
        rating_count INTEGER,
        rate_average REAL,
        review_count INTEGER,
        language TEXT,
        is_font INTEGER,
        custom_genres_json TEXT,
        extractor_version TEXT
    );
    """)

    # 2. item_genres table
    cur.execute("""
    CREATE TABLE item_genres (
        product_id TEXT NOT NULL REFERENCES items(product_id) ON DELETE CASCADE,
        genre TEXT NOT NULL,
        PRIMARY KEY (product_id, genre)
    );
    """)

    # 3. item_formats table
    cur.execute("""
    CREATE TABLE item_formats (
        product_id TEXT NOT NULL REFERENCES items(product_id) ON DELETE CASCADE,
        format TEXT NOT NULL,
        PRIMARY KEY (product_id, format)
    );
    """)

    # 4. custom_genres table
    cur.execute("""
    CREATE TABLE custom_genres (
        product_id TEXT NOT NULL REFERENCES items(product_id) ON DELETE CASCADE,
        custom_genre TEXT NOT NULL,
        PRIMARY KEY (product_id, custom_genre)
    );
    """)

    # 5. tag_bank table
    cur.execute("""
    CREATE TABLE tag_bank (
        keyword TEXT PRIMARY KEY,
        meaning TEXT,
        evidence_tier TEXT,
        category TEXT,
        notes TEXT
    );
    """)

    # Insert items
    for r in records:
        cur.execute("""
        INSERT OR REPLACE INTO items (
            product_id, item_url, title, title_jp, maker_id, maker_name, maker_url,
            price_jpy, official_price, page, position, absolute_position,
            work_type, context_category, crawl_date, thumb_url,
            detail_fetched, detail_fetched_at, description, description_length,
            genre, file_format, file_size, published, published_year,
            sales_count, favorites_count, rating_count, rate_average, review_count,
            language, is_font, custom_genres_json, extractor_version
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        );
        """, (
            r["product_id"], r["item_url"], r["title"], r["title_jp"], r["maker_id"], r["maker_name"], r["maker_url"],
            r["price_jpy"], r["official_price"], r["page"], r["position"], r["absolute_position"],
            r["work_type"], r["context_category"], r["crawl_date"], r["thumb_url"],
            r["detail_fetched"], r["detail_fetched_at"], r["description"], r["description_length"],
            r["genre"], r["file_format"], r["file_size"], r["published"], r["published_year"],
            r["sales_count"], r["favorites_count"], r["rating_count"], r["rate_average"], r["review_count"],
            r["language"], r["is_font"], json.dumps(r["custom_genres"], ensure_ascii=False), r["extractor_version"]
        ))

        # insert genres
        if r["genre"]:
            for g in re.split(r"[/,、\s]+", r["genre"]):
                g = g.strip()
                if g:
                    cur.execute("INSERT OR IGNORE INTO item_genres (product_id, genre) VALUES (?, ?);", (r["product_id"], g))

        # insert formats
        if r["file_format"]:
            for f in re.split(r"[/,、\s]+", r["file_format"]):
                f = f.strip()
                if f and f not in ("その他形式", "形式"):
                    cur.execute("INSERT OR IGNORE INTO item_formats (product_id, format) VALUES (?, ?);", (r["product_id"], f))

        # insert custom_genres
        for cg in r["custom_genres"]:
            cur.execute("INSERT OR IGNORE INTO custom_genres (product_id, custom_genre) VALUES (?, ?);", (r["product_id"], cg))

    # Insert tag bank
    for tb in tag_bank_rows:
        cur.execute("""
        INSERT OR REPLACE INTO tag_bank (keyword, meaning, evidence_tier, category, notes)
        VALUES (?, ?, ?, ?, ?);
        """, (tb["keyword"], tb["meaning"], tb["evidence_tier"], tb["category"], tb["notes"]))

    # 6. makers table
    cur.execute("""
    CREATE TABLE makers AS
    SELECT 
        maker_id,
        COALESCE(NULLIF(maker_name, ''), maker_id) as maker_name,
        maker_url,
        COUNT(*) as item_count,
        SUM(CASE WHEN is_font = 1 THEN 1 ELSE 0 END) as font_count,
        SUM(sales_count) as total_sales,
        AVG(sales_count) as avg_sales,
        SUM(favorites_count) as total_favorites,
        AVG(favorites_count) as avg_favorites
    FROM items
    WHERE maker_id IS NOT NULL AND maker_id != ''
    GROUP BY maker_id;
    """)

    # 7. Views
    cur.execute("""
    CREATE VIEW v_fonts AS
    SELECT * FROM items WHERE is_font = 1;
    """)

    cur.execute("""
    CREATE VIEW v_age_sales AS
    SELECT 
        product_id,
        title,
        maker_name,
        is_font,
        price_jpy,
        sales_count,
        favorites_count,
        published,
        published_year,
        ROUND(julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published)) AS days_since_publish,
        ROUND((sales_count * 365.0) / NULLIF(julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published), 0), 2) AS sales_per_year,
        ROUND((sales_count * 30.0) / NULLIF(julianday(COALESCE(NULLIF(crawl_date,''), date('now'))) - julianday(published), 0), 2) AS sales_per_month,
        ROUND(favorites_count * 1.0 / NULLIF(sales_count, 0), 2) AS fav_to_sales_ratio
    FROM items
    WHERE published != '' AND published IS NOT NULL;
    """)

    # Indexes
    cur.execute("CREATE INDEX idx_items_is_font ON items(is_font);")
    cur.execute("CREATE INDEX idx_items_sales ON items(sales_count);")
    cur.execute("CREATE INDEX idx_items_favs ON items(favorites_count);")
    cur.execute("CREATE INDEX idx_items_price ON items(price_jpy);")
    cur.execute("CREATE INDEX idx_items_maker ON items(maker_id);")
    cur.execute("CREATE INDEX idx_items_pub ON items(published);")

    con.commit()
    con.close()


def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def main():
    ap = argparse.ArgumentParser(description="Build DLsite SQLite database")
    ap.add_argument("--source", default="outputs/research/dlsite-live-collector/2026-09-09/tools-accessories", help="Collector directory or data file")
    ap.add_argument("--bank", default=str(DEFAULT_BANK), help="Path to dlsite-font-tag-bank.md")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Path to output dlsite.db")
    args = ap.parse_args()

    source_path = Path(args.source)
    bank_path = Path(args.bank)
    db_path = Path(args.db)

    print(f"Loading DLsite collection from: {source_path}")
    raw_records = auto_load_source(source_path)
    print(f"Loaded {len(raw_records)} raw records.")

    normalized = [normalize_item(r) for r in raw_records]
    print(f"Normalized {len(normalized)} items.")

    tag_bank_rows = parse_tag_bank(bank_path)
    print(f"Parsed {len(tag_bank_rows)} tag bank entries from {bank_path}.")

    print(f"Building SQLite database at: {db_path}")
    build_database(normalized, tag_bank_rows, db_path)
    print(f"Done. Database ready at {db_path}")

    # Print summary
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT count(*), sum(case when is_font=1 then 1 else 0 end) FROM items;")
    total, fonts = cur.fetchone()
    cur.execute("SELECT count(*) FROM makers;")
    makers = cur.fetchone()[0]
    print(f"Summary: {total} items ({fonts} font products), {makers} makers/circles indexed.")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
