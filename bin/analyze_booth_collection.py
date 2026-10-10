#!/usr/bin/env python3
"""
analyze_booth_collection.py — join BOOTH Data Collector exports with the
FontFairy rank CSV and extract ranking signals.

Scores tag/likes/price/description signals per rank band, finds tags used by
high-liked items that FontFairy items do not use, checks candidate tags
against the frozen BOOTH font tag bank, and writes a markdown findings file.

Usage:
  python3 bin/analyze_booth_collection.py \
    --collection ~/Downloads/booth-*.csv \
    --rank ~/Downloads/booth-rank-papermoonstudio-2026-09-08.csv \
    --bank outputs/research/booth-font-tag-bank.md \
    [--papermoon-tags 'tag1|tag2|...'] \
    [--out outputs/research/booth-collection-analysis-2026-09-08.md] \
    [--min-top-freq 3] \
    [--db outputs/research/booth-live-collector/booth.db]

With --db (the default), every finding is also written to structured
analysis_* tables in the SQLite database built by bin/build_booth_db.py
so you can SQL-join the report numbers against the item data.

Stdlib only (csv, json, sqlite3, statistics, re, glob, argparse).
"""

import argparse
import csv
import glob
import json
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

try:
    from scipy.stats import spearmanr as _scipy_spearmanr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# --------------------------------------------------------------------------
# small stats helpers (stdlib)
# --------------------------------------------------------------------------

def _ranked(values):
    """Rank values ascending-average-ties; returns list of ranks (same order)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    if den == 0:
        return None, n
    return num / den, n


def spearman(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    if HAS_SCIPY:
        r, _ = _scipy_spearmanr(xs, ys)
        return (float(r) if r is not None else None), n
    rx, ry = _ranked(xs), _ranked(ys)
    r, _ = pearson(rx, ry)
    return r, n


def quartile_indexes(values, q):
    """Indexes of the top-q quartile (q in (0,1)) by value, highest first."""
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    return order[: max(1, round(len(order) * q))]


def pct(x, n):
    return (100.0 * x / n) if n else 0.0


def fmt_num(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.2f}"
    return f"{v:,}"


def fmt_int(v):
    if v is None:
        return "-"
    return f"{int(round(v)):,}"


def median(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def iso(v):
    """Parse an int-like value from a CSV cell to int, else None."""
    if v is None or str(v).strip() == "":
        return None
    try:
        return int(float(str(v).replace(",", "")))
    except (ValueError, TypeError):
        return None


def flat_tags(cell):
    if not cell:
        return []
    return [t.strip() for t in str(cell).split("|") if t.strip()]


def load_collection(paths):
    rows = []
    seen = set()
    for p in paths:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                iid = iso(r.get("item_id"))
                if iid is None:
                    continue
                key = iid
                if key in seen:
                    continue
                seen.add(key)
                # Prefer the real wish-list count from browser-hydrated detail rows
                # (item_like_count) over the always-0 card-level `likes` column.
                eff_likes = iso(r.get("item_like_count"))
                if eff_likes is None:
                    eff_likes = iso(r.get("likes")) or 0
                rows.append({
                    "item_id": iid,
                    "title": (r.get("title") or "").strip(),
                    "price_jpy": iso(r.get("price_jpy")),
                    "likes": eff_likes,
                    "item_like_count": iso(r.get("item_like_count")),
                    "tag_count": iso(r.get("tag_count")),
                    "desc_len": iso(r.get("description_length")),
                    "tags": flat_tags(r.get("tags")),
                    "variants": (r.get("variants") or ""),
                    "price_min": iso(r.get("price_min")),
                    "price_max": iso(r.get("price_max")),
                    "formats": (r.get("formats") or ""),
                    "published": (r.get("published") or ""),
                    "item_image_count": iso(r.get("item_image_count")),
                    "detail_fetched": str(r.get("detail_fetched") or "").strip().lower() == "yes",
                    "shop_name": (r.get("shop_name") or "").strip(),
                    "brand": (r.get("brand") or "").strip(),
                    "item_url": (r.get("item_url") or ""),
                    "absolute_position": iso(r.get("absolute_position")),
                    "sort_mode": (r.get("sort_mode") or ""),
                    "source": str(p),
                })
    return rows


def load_rank(paths):
    rows = {}
    for p in paths:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue
            fn = reader.fieldnames
            col_id = next((c for c in ("item_id", "id") if c in fn), fn[3] if len(fn) > 3 else None)
            col_rank = next((c for c in ("global_rank", "rank") if c in fn), "global_rank")
            col_price = next((c for c in ("price", "price_jpy") if c in fn), None)
            for r in reader:
                iid = iso(r.get(col_id))
                if iid is None:
                    continue
                rows[iid] = {
                    "global_rank": iso(r.get(col_rank)),
                    "rank_title": (r.get("title") or "").strip(),
                    "rank_price": iso(r.get(col_price)) if col_price else None,
                    "page": iso(r.get("page")),
                    "in_page_rank": iso(r.get("in_page_rank")),
                }
    return rows


def load_bank_tags(path):
    """Banked tags from the priority table.

    Delegates to build_booth_db.load_tag_bank so the analyst, the DB loader,
    and bin/booth_tag_route_count.py can never disagree about what is banked.
    A looser local parse used to pick up the file's other tables too, treating
    activity bands ('100+', '1–16') and evidence-table product names
    ('toktaro, Angle') as if they were banked tags.
    """
    from build_booth_db import load_tag_bank

    return {r["tag"] for r in load_tag_bank(Path(path))}


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

ANALYSIS_DDL = """
DROP TABLE IF EXISTS analysis_run;
DROP TABLE IF EXISTS analysis_features;
DROP TABLE IF EXISTS analysis_like_bands;
DROP TABLE IF EXISTS analysis_tag_lift;
DROP TABLE IF EXISTS analysis_gap_candidates;
DROP TABLE IF EXISTS analysis_neighbour_diff;
DROP TABLE IF EXISTS analysis_pm_missing_tags;
DROP TABLE IF EXISTS analysis_price_bands;

CREATE TABLE analysis_run (
  created_at TEXT, finished_at TEXT, report_path TEXT,
  collection_paths TEXT, rank_paths TEXT, bank_path TEXT,
  min_top_freq INTEGER, neighbour_window INTEGER,
  n_items INTEGER, n_pm INTEGER
);
CREATE TABLE analysis_features (
  scope TEXT, feature TEXT, n INTEGER, pearson REAL, spearman REAL
);
CREATE TABLE analysis_like_bands (
  band TEXT, n INTEGER, median_price INTEGER, median_tags INTEGER,
  median_desc INTEGER, median_item_images INTEGER
);
CREATE TABLE analysis_tag_lift (
  tag TEXT, in_top INTEGER, overall_cov_pct REAL, lift REAL,
  pm_uses INTEGER, banked INTEGER
);
CREATE TABLE analysis_gap_candidates (
  tag TEXT, in_top INTEGER, overall_cov_pct REAL, lift REAL, bank_status TEXT
);
CREATE TABLE analysis_neighbour_diff (
  pm_item_id INTEGER, global_rank INTEGER, pos INTEGER, pm_likes INTEGER,
  pm_price INTEGER, n_neighbours INTEGER, nb_median_price INTEGER,
  nb_median_likes INTEGER, nb_median_desc INTEGER, nb_with_detail INTEGER,
  missing_tags_json TEXT, lonely_tags_json TEXT
);
CREATE TABLE analysis_pm_missing_tags (
  tag TEXT, pm_items_using INTEGER
);
CREATE TABLE analysis_price_bands (
  band TEXT, n INTEGER, median_likes INTEGER, median_tags INTEGER, median_desc INTEGER
);
"""


def build_report(items, rank, bank_tags, papermoon_tags, out_path, min_top_freq,
                 neighbour_window, db_con=None, report_path_str=""):
    lines = []
    def out(s=""):
        lines.append(s)

    ins = {}
    if db_con is not None:
        def ins_rows(table, rows):
            if not rows:
                return
            cols = list(rows[0].keys())
            db_con.executemany(
                f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                [tuple(r[c] for c in cols) for r in rows])

    n = len(items)
    with_detail = sum(1 for r in items if r["detail_fetched"])
    only_rank = [r for r in items if r["item_id"] in rank]
    out(f"# BOOTH Collection Analysis — {date.today().isoformat()}")
    out()
    out(f"Rows analyzed from collection: **{n}** (unique item_ids)")
    out(f"Item-detail pages fetched: **{with_detail}** ({pct(with_detail, n):.1f}%)")
    out(f"Collection rows that are FontFairy items (matched rank CSV): **{len(only_rank)}**")
    out(f"FontFairy global ranks present: {', '.join(str(rank[r['item_id']]['global_rank']) for r in sorted(only_rank, key=lambda x: rank[x['item_id']]['global_rank'])[:12])}")
    out()
    out("> This is an internal research report. BOOTH exact-tag counts and likes are")
    out("> catalog/popularity signals, not sales or demand. Correlation is exploratory,")
    out("> not causal.")
    out()

    # ---- 1. numeric signals across the whole collection (target: likes) ----
    out("## 1. What moves likes (all collected items)")
    out()
    out("| Feature | n | Pearson vs likes | Spearman vs likes |")
    out("|---|---:|---:|---:|")
    features = [
        ("price_jpy", "price (JPY)"),
        ("tag_count", "tag count"),
        ("desc_len", "description length"),
        ("item_image_count", "item image count"),
        ("absolute_position", "crawl position (order on page)"),
    ]
    feat_rows = []
    for key, label in features:
        pairs = [(r[key], r["likes"]) for r in items if r[key] is not None]
        if len(pairs) < 5:
            out(f"| {label} | {len(pairs)} | - | - |")
            continue
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        pr, pn = pearson(xs, ys)
        sr, sn = spearman(xs, ys)
        out(f"| {label} | {pn} | {fmt_num(pr)} | {fmt_num(sr)} |")
        feat_rows.append({"scope": "all_vs_likes", "feature": key, "n": pn,
                          "pearson": pr, "spearman": sr})
    if db_con is not None and feat_rows:
        ins_rows("analysis_features", feat_rows)
    out()

    # ---- 2. FontFairy rows: what correlates with global rank ----
    if only_rank:
        out("## 2. FontFairy items — signals vs global rank (lower = better)")
        out()
        out("Higher global rank means further down the search results (worse visibility).")
        out("A negative correlation means the signal helps.")
        out()
        out("| Feature | n | Pearson vs global rank | Spearman vs global rank |")
        out("|---|---:|---:|---:|")
        pm_feat_rows = []
        for key, label in features:
            pairs = [(rank[r["item_id"]]["global_rank"], r[key]) for r in only_rank if r[key] is not None]
            if len(pairs) < 3:
                out(f"| {label} | {len(pairs)} | - | - |")
                continue
            ranks_v = [p[0] for p in pairs]
            vals = [p[1] for p in pairs]
            pr, pn = pearson(ranks_v, vals)
            sr, sn = spearman(ranks_v, vals)
            out(f"| {label} | {pn} | {fmt_num(pr)} | {fmt_num(sr)} |")
            pm_feat_rows.append({"scope": "pm_vs_global_rank", "feature": key, "n": pn,
                                 "pearson": pr, "spearman": sr})
        if db_con is not None and pm_feat_rows:
            ins_rows("analysis_features", pm_feat_rows)
        out()
        pm_likes = [r["likes"] for r in only_rank]
        out(f"FontFairy items median likes: **{fmt_int(median(pm_likes))}** · "
            f"median global rank: **{fmt_int(median([rank[r['item_id']]['global_rank'] for r in only_rank]))}**")
        out()
    else:
        out("## 2. FontFairy items — no rank-CSV matches in this collection")
        out("The crawl did not capture any FontFairy items in the merged window. Run a")
        out("crawl over the top pages of the Fonts category (or the FontFairy shop item")
        out("page) to get direct global-rank-vs-signal numbers, or pass `--papermoon-tags`.")
        out()

    # ---- 3. quartile bands by likes ----
    liked = [r for r in items if r["likes"] is not None]
    out("## 3. Rank bands by likes (top-liked vs bottom-liked items)")
    out()
    default_tags = set()
    if only_rank:
        pm_ids = {r["item_id"] for r in only_rank}
    else:
        pm_ids = set()
    if papermoon_tags:
        default_tags = set(papermoon_tags)

    # PM union of tags if we have their rows
    pm_rows = [r for r in items if r["item_id"] in pm_ids]
    if pm_rows:
        pm_tag_union = set()
        for r in pm_rows:
            pm_tag_union.update(r["tags"])
        default_tags = default_tags | pm_tag_union

    if liked:
        top_idx = quartile_indexes([r["likes"] for r in liked], 0.25)
        bottom_idx = quartile_indexes([r["likes"] for r in liked], 0.25)
        bottom_idx = sorted(set(range(len(liked))) - set(top_idx))[-len(top_idx):]
        top = [liked[i] for i in top_idx]
        bottom = [liked[i] for i in bottom_idx]

        out("| Like band | n | median price | median tags | median desc len | median item images |")
        out("|---|---:|---:|---:|---:|---:|")
        band_rows = []
        for name, band in (("top 25% (highest likes)", top), ("bottom 25%", bottom), ("all", liked)):
            out(f"| {name} | {len(band)} | {fmt_int(median([r['price_jpy'] for r in band]))} | "
                f"{fmt_int(median([r['tag_count'] for r in band]))} | "
                f"{fmt_int(median([r['desc_len'] for r in band]))} | "
                f"{fmt_int(median([r['item_image_count'] for r in band]))} |")
            band_rows.append({
                "band": name, "n": len(band),
                "median_price": median([r['price_jpy'] for r in band]),
                "median_tags": median([r['tag_count'] for r in band]),
                "median_desc": median([r['desc_len'] for r in band]),
                "median_item_images": median([r['item_image_count'] for r in band]),
            })
        if db_con is not None and band_rows:
            ins_rows("analysis_like_bands", band_rows)
        out()

        # ---- 4. tag frequencies in top band vs overall ----
        out("## 4. Tag frequency — top-liked band vs overall")
        out()
        total_q = len(top)
        overall = Counter()
        topc = Counter()
        for r in liked:
            overall.update(r["tags"])
        for r in top:
            topc.update(r["tags"])
        n_all = len(liked) or 1
        rows_tag = []
        for tag, tc in topc.items():
            oc = overall.get(tag, 0)
            base = tc / max(1, total_q) / (oc / n_all)
            rows_tag.append((tc, base, tag, oc))
        rows_tag.sort(key=lambda x: (-x[0], -x[1]))
        out("Coverage = share of all items carrying the tag. Lift = share within top")
        out("band ÷ coverage (1.0 means it is as common in the top band as overall;")
        out(">1 means top-liked items carry it disproportionately).")
        out()
        out(f"| Tag | in top {total_q} | overall coverage | lift | PM uses it? | in frozen bank? |")
        out("|---|---:|---:|---:|---|---|")
        lift_rows = []
        for tc, base, tag, oc in rows_tag[:45]:
            pm_use = "yes" if (tag in default_tags) else "no"
            banked = "yes" if tag in bank_tags else ("NO" if tag else "-")
            out(f"| {tag} | {tc} | {pct(oc, n_all):.1f}% | {base:.2f} | {pm_use} | {banked} |")
            lift_rows.append({
                "tag": tag, "in_top": tc,
                "overall_cov_pct": pct(oc, n_all), "lift": base,
                "pm_uses": 1 if pm_use == "yes" else 0,
                "banked": 1 if banked == "yes" else 0,
            })
        if db_con is not None and lift_rows:
            ins_rows("analysis_tag_lift", lift_rows)
        out()

        # ---- 5. gap candidates ----
        out("## 5. Candidate tags the top-liked items use that FontFairy does not")
        out()
        out(f"Threshold: appears on ≥{min_top_freq} top-liked items.")
        out()
        cands = []
        for tag, tc in topc.items():
            if tc < min_top_freq or tc == 0:
                continue
            if tag in default_tags:
                continue
            oc = overall.get(tag, 0)
            base = tc / max(1, total_q) / (oc / n_all)
            cands.append((tc, base, tag, "banked" if tag in bank_tags else "NEW-CANDIDATE"))
        cands.sort(key=lambda x: (-x[0], -x[1]))
        cand_rows = []
        if cands:
            out(f"| Tag | in top {total_q} | overall coverage | lift | bank status |")
            out("|---|---:|---:|---:|---|")
            for tc, base, tag, status in cands[:40]:
                out(f"| {tag} | {tc} | {pct(overall.get(tag, 0), n_all):.1f}% | {base:.2f} | {status} |")
                cand_rows.append({
                    "tag": tag, "in_top": tc,
                    "overall_cov_pct": pct(overall.get(tag, 0), n_all),
                    "lift": base, "bank_status": status,
                })
            if db_con is not None and cand_rows:
                ins_rows("analysis_gap_candidates", cand_rows)
            out()
            out("`banked` = already in the frozen tag bank (confirm product fit, then it is a")
            out("straightforward select once the bank is refreshed per the addendum rule).")
            out("`NEW-CANDIDATE` = recurring on top-liked items but absent from the bank —")
            out("log these as new research-layer candidates, not as edits to the frozen bank.")
        else:
            out("No recurring top-band tags are currently unused by FontFairy. Consider that")
            out("the signal is driven by description/variants/pricing rather than missing tags.")
        out()

        # FontFairy-specific gap: tags PM uses that top band does NOT
        pm_only = sorted(default_tags - set(topc.keys()))
        if pm_only:
            out("### Tags FontFairy uses that no top-liked item carries")
            out()
            out("> These are not automatically weak — they may be long-tail product-fit tags —")
            out("> but review them: a tag that appears on zero top-liked items and zero visible")
            out("> competitor pages may just be consuming a 30-tag slot.")
            out()
            out(f"`{'`, `'.join(pm_only)}`")
            out()

    # ---- 6. FontFairy items vs crawl-position neighbours ----
    out("## 6. FontFairy items vs crawl-position neighbours")
    out()
    if pm_ids and any(r.get("absolute_position") is not None for r in items):
        out(f"Window: collection rows within ±{neighbour_window} crawl positions of each")
        out("FontFairy item (the same popularity-sorted crawl region = the items it")
        out("actually competes with for visibility). FontFairy's own items are excluded.")
        out()
        positions = [r for r in items if r.get("absolute_position") is not None]
        pm_with_pos = [r for r in items if r["item_id"] in pm_ids and r.get("absolute_position") is not None]
        if not pm_with_pos:
            out("No FontFairy rows in the collection carried a crawl position — the crawl")
            out("window did not reach their rank zone (check the analysed CSVs' page depth,")
            out("e.g. raise the collector's page range so FontFairy's rank band is covered).")
        else:
            rows_out = []
            agg_missing = Counter()
            agg_lonely = Counter()
            for pm in sorted(pm_with_pos, key=lambda r: rank[r["item_id"]]["global_rank"]):
                pos = pm["absolute_position"]
                nbs = [r for r in positions
                       if abs((r["absolute_position"] or 0) - pos) <= neighbour_window
                       and r["item_id"] != pm["item_id"]
                       and r["item_id"] not in pm_ids]
                if not nbs:
                    rows_out.append((pm, None))
                    continue
                nb_tags_counter = Counter()
                for r in nbs:
                    nb_tags_counter.update(r["tags"])
                pm_tags = set(pm["tags"])
                missing = sorted(t for t, c in nb_tags_counter.items()
                                 if c >= 2 and t not in pm_tags)
                lonely = sorted(t for t in pm_tags if t not in nb_tags_counter)
                agg_missing.update(missing)
                agg_lonely.update(lonely)
                rows_out.append((pm, dict(
                    n=len(nbs),
                    nb_price=median([r["price_jpy"] for r in nbs]),
                    nb_likes=median([r["likes"] for r in nbs]),
                    nb_desc=median([r["desc_len"] for r in nbs if r["desc_len"] is not None]),
                    nb_with_detail=sum(1 for r in nbs if r["detail_fetched"]),
                    missing=missing,
                    lonely=lonely)))
            out("| PM item | rank | pos | likes | price | nbrs | nbr median price | nbr median likes | nbr median desc | nbrs w/ detail |")
            out("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
            diff_rows = []
            for pm, di in rows_out:
                rk = rank[pm["item_id"]]["global_rank"]
                if di is None:
                    out(f"| {pm['title'][:34]} | {fmt_int(rk)} | {pm['absolute_position']} | "
                        f"{fmt_int(pm['likes'])} | {fmt_int(pm['price_jpy'])} | — | — | — | — | — |")
                    continue
                out(f"| {pm['title'][:34]} | {fmt_int(rk)} | {pm['absolute_position']} | "
                    f"{fmt_int(pm['likes'])} | {fmt_int(pm['price_jpy'])} | {di['n']} | "
                    f"{fmt_int(di['nb_price'])} | {fmt_int(di['nb_likes'])} | "
                    f"{fmt_int(di['nb_desc'])} | {di['nb_with_detail']} |")
                diff_rows.append({
                    "pm_item_id": pm["item_id"], "global_rank": rk,
                    "pos": pm["absolute_position"], "pm_likes": pm["likes"],
                    "pm_price": pm["price_jpy"], "n_neighbours": di["n"],
                    "nb_median_price": di["nb_price"], "nb_median_likes": di["nb_likes"],
                    "nb_median_desc": di["nb_desc"], "nb_with_detail": di["nb_with_detail"],
                    "missing_tags_json": json.dumps(di["missing"], ensure_ascii=False),
                    "lonely_tags_json": json.dumps(di["lonely"], ensure_ascii=False),
                })
            if db_con is not None:
                if diff_rows:
                    ins_rows("analysis_neighbour_diff", diff_rows)
                if agg_missing:
                    ins_rows("analysis_pm_missing_tags",
                             [{"tag": t, "pm_items_using": c} for t, c in agg_missing.items()])
            out()
            rec = sorted(t for t, c in agg_missing.items() if c >= 2)
            if rec:
                out("Recurring neighbour tags this seller is missing (present on ≥2 neighbours, "
                    "across ≥2 FontFairy items):")
                out()
                out(f"`{'`, `'.join(rec)}`")
            else:
                out("No neighbour tag recurs across multiple FontFairy items — either the tag gaps")
                out("are item-specific, or the crawl did not fetch neighbour detail pages (raw-HTTP")
                out("runs hide tags; re-run with --browser or use the extension's live-DOM CSV for the")
                out("tag diff).")
            out()
            if agg_lonely:
                out("Tags FontFairy uses that its position-neighbours never carry (isolation check):")
                out()
                out(f"`{'`, `'.join(sorted(t for t, c in agg_lonely.items() if c >= 1))}`")
            out()
    elif not pm_ids:
        out("No FontFairy items matched this collection, so no neighbour diff was possible —")
        out("add the rank CSV join (crawl the top pages of the Fonts category) or pass")
        out("`--papermoon-tags` to get the tag-gap view instead.")
        out()

    # ---- 7. price bands ----
    out("## 7. Price bands vs likes (all items)")
    out()
    bands = [
        ("¥0 (free)", lambda p: p == 0),
        ("¥1–500", lambda p: 1 <= p <= 500),
        ("¥501–1,000", lambda p: 501 <= p <= 1000),
        ("¥1,001–2,000", lambda p: 1001 <= p <= 2000),
        ("¥2,001+", lambda p: p > 2000),
    ]
    out("| Price band | n | median likes | median tags | median desc len |")
    out("|---|---:|---:|---:|---:|")
    pb_rows = []
    for label, fn in bands:
        band = [r for r in items if r["price_jpy"] is not None and fn(r["price_jpy"])]
        if not band:
            out(f"| {label} | 0 | - | - | - |")
            continue
        out(f"| {label} | {len(band)} | {fmt_int(median([r['likes'] for r in band]))} | "
            f"{fmt_int(median([r['tag_count'] for r in band]))} | "
            f"{fmt_int(median([r['desc_len'] for r in band]))} |")
        pb_rows.append({
            "band": label, "n": len(band),
            "median_likes": median([r['likes'] for r in band]),
            "median_tags": median([r['tag_count'] for r in band]),
            "median_desc": median([r['desc_len'] for r in band]),
        })
    if db_con is not None and pb_rows:
        ins_rows("analysis_price_bands", pb_rows)
    out()

    # ---- 8. description insights ----
    out("## 8. Description observations")
    out()
    if with_detail:
        d_rows = [r for r in items if r["desc_len"] is not None]
        lens = sorted(r["desc_len"] for r in d_rows)
        out(f"Description length (chars): count={len(lens)} min={fmt_int(lens[0]) if lens else '-'} "
            f"median={fmt_int(median(lens))} max={fmt_int(lens[-1]) if lens else '-'}")
        out()
        fmt_counts = Counter()
        for r in d_rows:
            for f in re.findall(r"\b(OTF|TTF|WOFF2?|OPS?|ZIP)\b", (r["formats"] or "").upper()):
                fmt_counts[f] += 1
        if fmt_counts:
            out("Format mentions (from item pages): " + ", ".join(f"{k}={v}" for k, v in fmt_counts.most_common()))
            out()
        nonempty_desc = [r for r in d_rows if (r["desc_len"] or 0) > 50]
        out(f"Rows with a substantive description (>50 chars): {len(nonempty_desc)}/{len(d_rows)} "
            f"({pct(len(nonempty_desc), len(d_rows)):.0f}%)")
    else:
        out("No item details were fetched in this dataset — re-run the crawl with **Fetch item")
        out("details** enabled for description/tag analysis.")
    out()

    # ---- 9. recommendations ----
    out("## 9. Recommendations for the BOOTH agent (Agent 20)")
    out()
    recs = []
    if top:
        high = [r for r in liked if r["likes"] >= median([r["likes"] for r in top])]
        high_tags = Counter()
        for r in high:
            high_tags.update(r["tags"])
        top_tags = [t for t, _ in high_tags.most_common(20)]
        recs.append(f"Top-liked items repeatedly carry: `{'`, `'.join(top_tags[:12])}`. "
                    "Verify each against the frozen bank + product fit before selecting.")
    if not recs and not (only_rank):
        recs.append("Crawl the top pages of the Fonts browse (sort=popular) to get competitor "
                    "signals; this run only contained context rows without overlapping FontFairy items.")
    for r0 in recs:
        out(f"- {r0}")
    out()
    out(f"- Tag-lift table (section 4) and gap list (section 5) are the direct inputs for the "
        "next `booth-font-specialist` research-layer run.")
    out(f"- If FontFairy rows landed inside the crawl, section 6 diff's the seller's items against")
    out("  the ±position competitors: which tags/price/description posture the neighbours carry.")
    out(f"- Banked gaps are safe to add once product fit is verified; new candidates need a "
        "dated research layer before entering guidance (the 2026-09-06 bank stays frozen).")
    out(f"- If FontFairy's own rows were captured (section 2), watch the global-rank "
        "correlations: desc length / tag count moving negatively against rank means more "
        "content is helping visibility on BOOTH now.")

    # write file
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Analyze BOOTH collector + rank CSV data")
    ap.add_argument("--collection", nargs="+", required=True,
                    help="Path(s) or glob(s) to BOOTH Data Collector CSV exports")
    ap.add_argument("--rank", nargs="+", required=True,
                    help="Path(s) or glob(s) to FontFairy rank CSVs")
    ap.add_argument("--bank", default="outputs/research/booth-font-tag-bank.md",
                    help="Frozen tag bank markdown (for banked-tag status)")
    ap.add_argument("--papermoon-tags", default="",
                    help="Extra FontFairy tag list separated by '|' when their rows are not in the collection")
    ap.add_argument("--out", default=None,
                    help="Output markdown path (default: outputs/research/booth-collection-analysis-{date}.md)")
    ap.add_argument("--min-top-freq", type=int, default=3,
                    help="Minimum appearances on top-liked items for a gap candidate (default 3)")
    ap.add_argument("--neighbour-window", type=int, default=50,
                    help="Crawl-position window around each FontFairy item for the neighbour diff (default 50)")
    ap.add_argument("--db", default="outputs/research/booth-live-collector/booth.db",
                    help="SQLite DB path for analysis_* findings tables (default: "
                         "outputs/research/booth-live-collector/booth.db). Pass --db none to skip.")
    args = ap.parse_args()

    def expand(paths):
        out_paths = []
        for p in paths:
            matches = sorted(glob.glob(p))
            out_paths.extend(matches or [p])
        return list(dict.fromkeys(out_paths))

    coll_paths = [p for p in expand(args.collection) if "rank" not in Path(p).name.lower()]
    rank_paths = [p for p in expand(args.rank) if "rank" in Path(p).name.lower()] or expand(args.rank)

    items = load_collection(coll_paths)
    rank = load_rank(rank_paths)
    bank_tags = set()
    if Path(args.bank).exists():
        bank_tags = load_bank_tags(args.bank)
        print(f"Loaded {len(bank_tags)} banked tags from {args.bank}")
    else:
        print(f"Warning: bank file not found: {args.bank} (running without bank status)")

    papermoon_tags = [t.strip() for t in args.papermoon_tags.split("|") if t.strip()]

    if not items:
        print("No collection rows loaded. Check --collection paths.")
        return 2

    out_path = Path(args.out) if args.out else Path(f"outputs/research/booth-collection-analysis-{date.today().isoformat()}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db_con = None
    db_path = None
    if args.db and args.db.strip().lower() != "none":
        db_path = Path(args.db)
        if not db_path.suffix:
            db_path = db_path.with_suffix(".db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_con = sqlite3.connect(str(db_path))
        db_con.executescript(ANALYSIS_DDL)
        print(f"Analysis findings will be written to {db_path}")

    created_at = datetime.now().isoformat(timespec="seconds")
    report = build_report(items, rank, bank_tags, papermoon_tags, out_path,
                          args.min_top_freq, args.neighbour_window,
                          db_con=db_con, report_path_str=str(out_path))

    if db_con is not None:
        db_con.execute(
            "INSERT INTO analysis_run (created_at, finished_at, report_path, collection_paths,"
            " rank_paths, bank_path, min_top_freq, neighbour_window, n_items, n_pm)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (created_at, datetime.now().isoformat(timespec="seconds"), str(out_path),
             ", ".join(coll_paths), ", ".join(rank_paths),
             str(Path(args.bank)) if Path(args.bank).exists() else "",
             args.min_top_freq, args.neighbour_window, len(items), len(rank)))
        db_con.commit()
        db_con.close()
        print(f"Analysis findings written to {db_path} (analysis_run/analysis_tag_lift/"
              "analysis_gap_candidates/analysis_neighbour_diff/analysis_price_bands/...)")

    print(f"Analyzed {len(items)} collection rows; {len(rank)} FontFairy rank rows loaded.")
    print(f"Report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())