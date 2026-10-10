#!/usr/bin/env python3
"""
Creative Fabrica tag-metadata analysis + Popular Tags backfill.

Reads the tag-metadata crawl DB and its saved raw HTML, then:
  1. Builds tag_related_edges: source tag -> target tag co-mention edges
     harvested from the rendered /tag/ links on every saved page.
  2. Discovers related tags that are NOT part of the original 369
     directory set (new vocabulary recovered from pages, no re-crawl).
  3. Writes a coverage report (per-tag status, catalog total, samples).
  4. Emits a readable summary.

Usage:
  python3 bin/analyze_creative_fabrica_tag_metadata.py [--out DIR]
"""

import argparse
import csv
import gzip
import pathlib
import re
import sqlite3
import sys
from collections import Counter, defaultdict

TAG_LINK_RE = re.compile(r'href="(https://www\.creativefabrica\.com/tag/([^/"?]+)/|/tag/([^/"?]+)/)"')


def parse_tag_links(html):
    seen = {}
    for full, slug_abs, slug_rel in TAG_LINK_RE.findall(html):
        slug = slug_abs or slug_rel
        seen[f"https://www.creativefabrica.com/tag/{slug}/"] = slug
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/research/creative-fabrica-tag-metadata")
    args = ap.parse_args()
    root = pathlib.Path(args.out)
    db_path = root / "creative-fabrica-tags.db"
    if not db_path.exists():
        sys.exit(f"missing database: {db_path}")

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode = WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS tag_related_edges (
          source_tag_id INTEGER REFERENCES tags(tag_id),
          target_tag_id INTEGER REFERENCES tags(tag_id),
          target_slug TEXT NOT NULL,
          target_url TEXT NOT NULL,
          occurrences INTEGER NOT NULL DEFAULT 0,
          first_seen_run_id TEXT,
          PRIMARY KEY (source_tag_id, target_slug)
        );
        CREATE INDEX IF NOT EXISTS idx_related_target ON tag_related_edges(target_slug);
    """)

    slug_to_id = {row[0]: row[1] for row in db.execute(
        "SELECT canonical_slug, tag_id FROM tags")}

    # Map raw_documents -> source slug (tag_route) or source key (directory-N).
    docs = db.execute("""
        SELECT raw_id, url, document_type, storage_path FROM raw_documents
    """).fetchall()

    unknown_targets = Counter()
    edges = defaultdict(Counter)
    source_missing = 0
    direct = []
    for raw_id, url, doc_type, storage in docs:
        src_slug = None
        if doc_type == "tag_route":
            m = re.search(r"/tag/([^/]+)/$", url or "")
            src_slug = m.group(1) if m else None
        else:
            src_slug = f"dir:{pathlib.Path(storage).name}"
        p = pathlib.Path(storage)
        if not p.exists():
            source_missing += 1
            continue
        html = gzip.decompress(p.read_bytes()).decode("utf-8", "replace")
        links = parse_tag_links(html)
        for target_url, target_slug in links.items():
            if target_slug in ("page", "search"):
                continue
            edges[src_slug][target_slug] += 1
            unknown_targets[target_slug] += 1

    upsert_sql = """
        INSERT OR REPLACE INTO tag_related_edges
          (source_tag_id, target_tag_id, target_slug, target_url, occurrences, first_seen_run_id)
        VALUES (?,?,?,?,?,?)
    """
    for src_slug, targets in edges.items():
        src_id = slug_to_id.get(src_slug)
        for target_slug, count in targets.items():
            target_id = slug_to_id.get(target_slug)
            turl = f"https://www.creativefabrica.com/tag/{target_slug}/"
            db.execute(upsert_sql, (src_id, target_id, target_slug, turl, count, None))
    db.commit()

    known = set(slug_to_id)
    related_total = sum(unknown_targets.values())
    related_unique = len(unknown_targets)
    discovered_new = {s for s in unknown_targets if s not in known}

    # ---- coverage report ----
    report_path = root / "tag-coverage-report.csv"
    with open(report_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "status", "observed_total", "expected_pages",
                    "successful_pages", "failed_pages", "sample_products"])
        for slug, status, obs, exp, ok, fail, samples in db.execute("""
            SELECT t.canonical_slug, s.status, s.observed_total, s.expected_pages,
                   s.successful_pages, s.failed_pages,
                   (SELECT COUNT(*) FROM product_route_observations r
                    JOIN tag_crawl_status sc ON sc.run_id = r.run_id AND sc.tag_id = r.tag_id
                    WHERE sc.tag_id = s.tag_id AND r.page_number <= 1) AS samples
            FROM tag_crawl_status s JOIN tags t ON t.tag_id = s.tag_id
            ORDER BY t.canonical_slug
        """):
            w.writerow([slug, status, obs, exp, ok, fail, samples])

    prod_total = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    rel_total = db.execute("SELECT COUNT(*) FROM product_tags").fetchone()[0]
    tag_total = db.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    edge_total = db.execute("SELECT COUNT(*) FROM tag_related_edges").fetchone()[0]
    statuses = dict(db.execute(
        "SELECT status, COUNT(*) FROM tag_crawl_status GROUP BY status").fetchall())
    doc_total = db.execute("SELECT COUNT(*) FROM raw_documents").fetchone()[0]

    print("=" * 64)
    print("CREATIVE FABRICA TAG METADATA — ANALYSIS & BACKFILL SUMMARY")
    print("=" * 64)
    print(f"directory tags       : {tag_total}")
    print(f"tag statuses         : {statuses}")
    pages_complete = db.execute(
        "SELECT COUNT(*) FROM tag_pages WHERE status='COMPLETE'").fetchone()[0]
    pages_failed = db.execute(
        "SELECT COUNT(*) FROM tag_pages WHERE status='FAILED'").fetchone()[0]
    print(f"tag pages            : complete={pages_complete} failed={pages_failed}")
    print(f"products sampled     : {prod_total}")
    print(f"product-tag rels     : {rel_total}")
    print(f"raw documents        : {doc_total} (missing from disk: {source_missing})")
    print(f"crawl errors         : {db.execute('SELECT COUNT(*) FROM crawl_errors').fetchone()[0]}")
    print()
    print("POPULAR TAGS / RELATED-TAG GRAPH")
    print(f"related edges        : {edge_total}")
    print(f"related occurrences  : {related_total} across {len(edges)} source pages")
    top = unknown_targets.most_common(15)
    if top:
        print("top co-mentioned tags :")
        for slug, n in top:
            marker = " [NEW - not in 369]" if slug not in known else ""
            print(f"  {n:5d}  {slug}{marker}")
    if discovered_new:
        print(f"new vocabulary found via related links (not in the 369): {len(discovered_new)}")
    else:
        print("no new vocabulary: every related tag was already in the 369 set")
    print()
    import os
    print(f"coverage report written to: {os.path.relpath(report_path)}")
    db.close()


if __name__ == "__main__":
    main()