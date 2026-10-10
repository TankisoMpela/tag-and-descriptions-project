#!/usr/bin/env python3
"""Per-tag BOOTH evidence lookup against the frozen census DB (young-cohort gate).

This is the canonical per-tag evidence gate named by AGENTS.md for the BOOTH
font workflow. It reads the frozen census snapshot only (no live requests) and
reports, for every candidate tag, the numbers the validator's TAG EVIDENCE rows
need plus the *young-cohort* selection gate:

    New doctrine gate (age-consistent, replaces the old all-time-lift gate):

        STRONG   = young-paid win-rate >= 10%  AND young paid n >= 30
        MODERATE = young-paid win-rate 5-10%   AND young paid n >= 30
        THIN     = young paid n < 30  (honest label; selectable ONLY on direct
                   product fit — high win-rate with small n is labelled thin-n,
                   never claimed as a clean PASS)

    Young-paid win-rate = share of <=365-day PAID items wearing the tag that
    reach the winner band (absolute_position <= 300 in the census popularity
    proxy). The baseline is the overall young-paid winner rate for the whole
    census, so win-rates are interpretable against the cohort, not in a vacuum.

    All-time lift (analysis_tag_lift) is REPORTED but labelled all-time and is
    NEVER a pass condition. The old free/viral-cluster lift numbers (無料DL可
    etc.) contaminated the previous gate; they are parked in the output only
    for context.

    Rejected vocabulary classes (already banned by the blueprint) are excluded
    from --top-lanes discovery and flagged on single-tag lookups.

Usage:
  python3 bin/booth_tag_evidence.py "タイポグラフィー" "書体 商用利用" "display font" ...
  python3 bin/booth_tag_evidence.py --json "フォント かっこいい" "ネオン"
  python3 bin/booth_tag_evidence.py --top-lanes --min-win-rate 0.10 --max-pm-uses 2
  python3 bin/booth_tag_evidence.py --db outputs/research/booth-live-collector/booth.db -f candidates.txt

The whole frozen census is a フォント・書体 (Fonts category) capture, so the
font-category count equals the overall count here; the columns are kept so the
evidence table stays mechanically consistent with the validator.

Counts are catalog coverage / competition signals, never search volume or
demand. Copy the constructed URLs and DB numbers into the listing's TAG
EVIDENCE rows with provider/date `frozen snapshot 2026-09-08`.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign_mode  # noqa: E402

DEFAULT_DB = Path("outputs/research/booth-live-collector/booth.db")
SNAPSHOT_LABEL = "frozen snapshot 2026-09-08"
FONT_CATEGORY_ROUTE = "https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93"

# ---- New young-cohort gate constants -----------------------------------
WINNER_BAND = 300                 # absolute_position <= this = "winner" proxy
WIN_RATE_STRONG = 0.10            # >= 10% young-paid win-rate
WIN_RATE_MODERATE = 0.05          # 5-10% band
STRONG_MIN_YOUNG_PAID = 30        # n >= 30 for a clean STRONG/MODERATE verdict
YOUNG_DAYS = 365
SHORT_DAYS = 90
TOPLANES_MIN_YOUNG_PAID = 5
TOPLANES_MIN_WIN_RATE = 0.05

# ---- Rejected vocabulary classes (blueprint bans + paid-only rule) ------
# Each entry is a case-insensitive substring; a tag that contains ANY of these
# substrings in a family is excluded from --top-lanes discovery and flagged.
REJECTED_FAMILIES = {
    "print/DTP": ["名刺", "招待状", "書籍タイトル", "チラシ", "バナー", "装丁", "表紙", "ポスター"],
    "video-stack": ["テロップ", "字幕", "動画編集", "youtube", "プレミアプロ", "premiere pro", "テンプレート"],
    "fluff": ["美しいフォント", "良いフォント", "クリーン", "シンプル"],
    "bare-English-tech": ["display font", "script font", "handcraft", "lettering", "typeface", "otf", "opentype", "ttf", "woff"],
    "false-Japanese-glyph": ["日本語フォント", "日本語", "和文フォント", "和文", "ひらがな", "漢字", "カタカナ", "平仮名", "片仮名"],
    "free-promo": ["無料", "フリーフォント", "フリー", "お試し", "期間限定", "free", "freebie"],
}


def rejected_family(tag: str, allow_free: bool = False) -> str | None:
    """Return the rejected vocabulary family a tag belongs to, if any.

    `allow_free` lifts the `free-promo` ban for an explicit free campaign: the
    free vocabulary is banned in the permanent paid state, not in a
    limited-time free offer. Every other family stays banned in both modes.
    """
    low = tag.casefold()
    for family, needles in REJECTED_FAMILIES.items():
        if allow_free and family == "free-promo":
            continue
        for n in needles:
            if n.casefold() in low:
                return family
    return None


def pct(vals, p):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    k = (p / 100.0) * (len(vals) - 1)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return vals[int(k)]
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)


def activity_label(font_cat_n):
    """Validator-compatible BOOTH activity label for the status cell.

    Under the young-cohort contract the "low activity" label no longer forces
    an exception slot on its own; the young win-rate cell carries the evidence
    weight. The label stays for page-life description.
    """
    if font_cat_n is None or font_cat_n <= 0:
        return "dead/no coverage"
    if font_cat_n < 17:
        return "low activity"
    return "live"


def make_urls(tag):
    enc = urllib.parse.quote(tag, safe="")
    exact = f"https://booth.pm/ja/items?tags%5B%5D={enc}"
    category = f"{FONT_CATEGORY_ROUTE}?tags%5B%5D={enc}"
    return exact, category


def evidence_for(con, tag, ref, *, base_young_win_rate=None, winner_band=WINNER_BAND,
                 young_days=YOUNG_DAYS, short_days=SHORT_DAYS, allow_free=False, _batch=None):
    cur = con.cursor()

    if _batch is not None:
        tag_to_ids, id_to_row, lift_by_lower = _batch
        lt = tag.lower()
        item_ids = tag_to_ids.get(lt, set())
        overall_n = len(item_ids)
        rows = [id_to_row[i] for i in item_ids if i in id_to_row]
        lift_row = lift_by_lower.get(lt)
    else:
        ci = cur.execute(
            "SELECT DISTINCT item_id FROM item_tags WHERE tag = ? COLLATE NOCASE", (tag,)
        ).fetchall()
        item_ids = {r["item_id"] for r in ci}
        overall_n = len(item_ids)
        rows = []
        if item_ids:
            idlist = list(item_ids)
            placeholders = ", ".join("?" * len(idlist))
            cur.execute(
                f"SELECT item_id, title, shop_name, price_jpy, published, "
                f"item_like_count, absolute_position FROM items WHERE item_id IN ({placeholders})",
                idlist,
            )
            rows = cur.fetchall()
        lift_row = cur.execute(
            "SELECT tag, in_top, overall_cov_pct, lift, pm_uses, banked "
            "FROM analysis_tag_lift WHERE tag = ? COLLATE NOCASE",
            (tag,),
        ).fetchone()

    def age_days(published_str):
        try:
            return (ref - date.fromisoformat(published_str)).days
        except (TypeError, ValueError):
            return None

    all_likes = []
    young_likes = []
    young_paid_likes = []
    short_paid_likes = []
    young_free_likes = []
    young_paid_n = 0
    young_paid_wins = 0
    young_paid_sellers = set()
    young_free_n = 0
    young_n = 0
    all_paid_n = 0
    all_paid_sellers = set()
    any_free = False
    free_n = 0
    free_likes = []
    for r in rows:
        likes = r["item_like_count"]
        age = age_days(r["published"] or "")
        price = r["price_jpy"] or 0
        free = price == 0
        paid = not free
        pos = r["absolute_position"]
        all_likes.append(likes)
        if free:
            # Free-cohort coverage is age-independent: a free campaign tag is
            # judged on how many free items carry it and how they engage, not
            # on the young-paid winner band, which is a paid-only construct.
            free_n += 1
            if likes is not None:
                free_likes.append(likes)
        if paid:
            all_paid_n += 1
            all_paid_sellers.add(r["shop_name"])
        if age is None:
            continue
        if age <= young_days:
            young_n += 1
            young_likes.append(likes)
            if paid:
                young_paid_n += 1
                young_paid_likes.append(likes)
                young_paid_sellers.add(r["shop_name"])
                if pos is not None and pos <= winner_band:
                    young_paid_wins += 1
            else:
                young_free_n += 1
                young_free_likes.append(likes)
                any_free = True
            if paid and age <= short_days:
                short_paid_likes.append(likes)

    free_pct_young = round(100 * young_free_n / young_n, 1) if young_n else None

    font_cat_n = overall_n  # whole census is the Fonts category
    exact_url, category_url = make_urls(tag)

    lift = lift_row["lift"] if lift_row else None
    in_top = lift_row["in_top"] if lift_row else None
    pm_uses = lift_row["pm_uses"] if lift_row else None
    banked = lift_row["banked"] if lift_row else None

    young_paid_median = pct(young_paid_likes, 50)
    all_median = pct(all_likes, 50)
    young_median = pct(young_likes, 50)
    short_paid_median = pct(short_paid_likes, 50)

    # --- New young-cohort gate ------------------------------------------
    young_paid_win_rate = (young_paid_wins / young_paid_n) if young_paid_n else None
    if base_young_win_rate:
        young_paid_lift = (
            young_paid_win_rate / base_young_win_rate if young_paid_win_rate else None
        )
    else:
        young_paid_lift = None

    if young_paid_win_rate is None:
        strength = "no-cohort"
        gate_pass = False
        verdict = "FAIL gate — no young paid cohort (n=0); all-time lift is not a pass condition"
    elif young_paid_n < STRONG_MIN_YOUNG_PAID:
        strength = "THIN"
        gate_pass = True if young_paid_win_rate >= WIN_RATE_MODERATE else False
        verdict = (
            f"THIN (young paid n={young_paid_n} < {STRONG_MIN_YOUNG_PAID}) — "
            f"young-paid win-rate {100*young_paid_win_rate:.1f}% on small sample; "
            f"selectable ONLY on direct product fit with an honest `thin-n` label"
        )
    elif young_paid_win_rate >= WIN_RATE_STRONG:
        strength = "STRONG"
        gate_pass = True
        verdict = (
            f"STRONG PASS — young-paid win-rate {100*young_paid_win_rate:.1f}% "
            f"({young_paid_wins}/{young_paid_n} paid ≤365d reach the winner band), "
            f"n={young_paid_n} >= {STRONG_MIN_YOUNG_PAID}"
        )
    elif young_paid_win_rate >= WIN_RATE_MODERATE:
        strength = "MODERATE"
        gate_pass = True
        verdict = (
            f"MODERATE PASS — young-paid win-rate {100*young_paid_win_rate:.1f}% "
            f"in [5,10)% band, n={young_paid_n}"
        )
    else:
        strength = "WEAK"
        gate_pass = False
        verdict = (
            f"FAIL gate — young-paid win-rate {100*young_paid_win_rate:.1f}% "
            f"below the {int(WIN_RATE_MODERATE*100)}% band ({young_paid_wins}/{young_paid_n} paid ≤365d)"
        )

    free_heavy = (
        young_paid_n > 0
        and free_pct_young is not None
        and free_pct_young > 60
    )
    rej_family = rejected_family(tag, allow_free=allow_free)

    # Free-cohort verdict. Under a free campaign the paid young-cohort gate is
    # the wrong instrument (it measures paid reach); the campaign tag is judged
    # on how the FREE cohort uses it.
    free_median = pct(free_likes, 50)
    if not allow_free:
        free_verdict = None
    elif free_n == 0:
        free_verdict = (
            "FAIL — no free items carry this tag; it is not a free-campaign lane"
        )
    elif free_n < 17:
        free_verdict = (
            f"THIN — free cohort n={free_n}, median likes {fmt(free_median)}; "
            f"usable on direct product fit with an honest thin-cohort label"
        )
    else:
        free_verdict = (
            f"FREE-CAMPAIGN lane — free cohort n={free_n}, median likes {fmt(free_median)}"
        )

    return {
        "tag": tag,
        "overall_n": overall_n,
        "font_cat_n": font_cat_n,
        "all_median": all_median,
        "free_n": free_n,
        "free_median": free_median,
        "allow_free": allow_free,
        "free_verdict": free_verdict,
        "young_n": young_n,
        "young_median": young_median,
        "young_paid_n": young_paid_n,
        "young_paid_wins": young_paid_wins,
        "young_paid_win_rate": young_paid_win_rate,
        "young_paid_lift": young_paid_lift,
        "base_young_win_rate": base_young_win_rate,
        "winner_band": winner_band,
        "young_paid_median": young_paid_median,
        "young_paid_sellers": len(young_paid_sellers),
        "short_paid_median": short_paid_median,
        "free_pct_young": free_pct_young,
        "all_paid_n": all_paid_n,
        "all_paid_sellers": len(all_paid_sellers),
        "lift": lift,
        "in_top": in_top,
        "pm_uses": pm_uses,
        "banked": banked,
        "activity": activity_label(font_cat_n),
        "exact_url": exact_url,
        "category_url": category_url,
        "gate_pass": gate_pass,
        "strength": strength,
        "free_heavy": free_heavy,
        "rejected_family": rej_family,
        "verdict": verdict,
        "snapshot_label": SNAPSHOT_LABEL,
    }


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def render(e):
    tag = e["tag"]
    winr = e["young_paid_win_rate"]
    lines = [
        f"## {tag}",
        f"- Verdict: **{e['verdict']}**  (gate: young-paid win-rate ≥ {int(WIN_RATE_STRONG*100)}% "
        f"with n ≥ {STRONG_MIN_YOUNG_PAID}; all-time lift is reported, never a pass; "
        f"{e['snapshot_label']}, no live requests)",
        f"- Strength tier: {e['strength']}",
        f"- Young-paid winner proxy: n={e['young_paid_n']}, wins={e['young_paid_wins']} "
        f"(absolute_position ≤ {e['winner_band']}), win-rate={fmt((winr*100 if winr is not None else None))}% "
        f"vs cohort baseline {fmt((e.get('base_young_win_rate') or 0)*100)}%",
        f"- Young-paid lift: {fmt(e['young_paid_lift'])}  (win-rate / cohort baseline)",
        f"- Likes medians: all-time {fmt(e['all_median'])} | ≤365d {fmt(e['young_median'])} "
        f"| ≤365d paid {fmt(e['young_paid_median'])} | ≤90d paid {fmt(e['short_paid_median'])}",
        f"- Young cohort: n={e['young_n']} (paid n={e['young_paid_n']}, "
        f"distinct paid sellers={e['young_paid_sellers']}, free%={fmt(e['free_pct_young'])})",
        f"- Free cohort: n={fmt(e.get('free_n'))}, median likes {fmt(e.get('free_median'))}"
        + (f"  | free-campaign verdict: {e['free_verdict']}" if e.get("free_verdict") else ""),
        f"- Coverage: overall {e['overall_n']} | font-category {e['font_cat_n']} "
        f"| activity label: {e['activity']}",
        f"- All-time paid: items={e['all_paid_n']}, distinct sellers={e['all_paid_sellers']} "
        f"(validated `Paid products / distinct sellers` cell)",
        f"- analysis_tag_lift (all-time, context only): {fmt(e['lift'])} "
        f"(in_top={fmt(e['in_top'])}, pm_uses={fmt(e['pm_uses'])}, banked={fmt(e['banked'])})",
    ]
    flags = []
    if e["free_heavy"]:
        flags.append("free-heavy young cohort — caution for a paid-only product")
    if e["rejected_family"]:
        flags.append(f"rejected vocabulary family: {e['rejected_family']} — do not select")
    if e["strength"] == "no-cohort":
        flags.append("zero young paid sample; all-time numbers are not a pass (free/viral-cluster contamination risk)")
    if flags:
        lines.append("- Flags: " + "; ".join(flags))
    lines.append("- Evidence rows (validator-ready):")
    lines.append(f"  - Exact tag URL: `{e['exact_url']}`")
    lines.append(f"  - Font-category URL: `{e['category_url']}`")
    lines.append(f"  - Status cell: `{e['snapshot_label']}: {e['activity']}`")
    return "\n".join(lines) + "\n"


def compute_base_young_win_rate(con, ref, winner_band=WINNER_BAND, young_days=YOUNG_DAYS):
    """Share of ALL young paid items reaching the winner band (cohort baseline)."""
    cutoff = (ref - timedelta(days=young_days)).isoformat()
    row = con.execute(
        "SELECT COUNT(*), "
        "SUM(CASE WHEN absolute_position IS NOT NULL AND absolute_position <= ? THEN 1 ELSE 0 END) "
        "FROM items WHERE price_min > 0 AND published >= ? AND absolute_position IS NOT NULL",
        (winner_band, cutoff),
    ).fetchone()
    total, wins = row[0], row[1] or 0
    return (wins / total) if total else None


def load_batch(con, tags):
    """Preload item-id sets, rows, and lift rows for a list of tags (one query)."""
    uniq_lower = {t.lower(): t for t in tags}
    tag_to_ids: dict[str, set[int]] = {k: set() for k in uniq_lower}
    if not uniq_lower:
        return {}, {}, {}
    lowers = list(uniq_lower.keys())
    ph = ",".join("?" for _ in lowers)
    for row in con.execute(
        f"SELECT LOWER(tag) AS lt, item_id FROM item_tags WHERE LOWER(tag) IN ({ph})", lowers
    ):
        tag_to_ids[row["lt"]].add(row["item_id"])
    all_ids = set()
    for s in tag_to_ids.values():
        all_ids.update(s)
    id_to_row: dict[int, sqlite3.Row] = {}
    if all_ids:
        idlist = list(all_ids)
        iph = ",".join("?" for _ in idlist)
        for r in con.execute(
            f"SELECT item_id, title, shop_name, price_jpy, published, item_like_count, "
            f"absolute_position FROM items WHERE item_id IN ({iph})", idlist
        ):
            id_to_row[r["item_id"]] = r
    lift_by_lower: dict[str, sqlite3.Row] = {}
    try:
        for row in con.execute(
            f"SELECT LOWER(tag) AS lt, tag, in_top, overall_cov_pct, lift, pm_uses, banked "
            f"FROM analysis_tag_lift WHERE LOWER(tag) IN ({ph})", lowers
        ):
            lift_by_lower[row["lt"]] = row
    except sqlite3.OperationalError:
        pass
    return tag_to_ids, id_to_row, lift_by_lower


def top_lanes(con, ref, *, min_n=TOPLANES_MIN_YOUNG_PAID, min_win=TOPLANES_MIN_WIN_RATE,
              max_pm_uses=None, winner_band=WINNER_BAND, young_days=YOUNG_DAYS,
              allow_free=False, limit=40):
    """Table-driven discovery: rank ALL census tags by young-paid win-rate.

    This replaces the old seed-driven loop (the agent only ever tested tags it
    already typed). Rejection families and the free/viral cluster are excluded
    unless `allow_free` lifts the free-promo ban for an explicit free campaign;
    pm_uses from analysis_tag_lift marks FontFairy ownership so under-used lanes
    surface instead of the same 12 universal core tags.
    """
    cutoff = (ref - timedelta(days=young_days)).isoformat()
    rows = con.execute(
        "SELECT t.tag, COUNT(DISTINCT i.item_id) AS n, "
        "SUM(CASE WHEN i.absolute_position IS NOT NULL AND i.absolute_position <= ? THEN 1 ELSE 0 END) AS wins "
        "FROM item_tags t JOIN items i ON i.item_id = t.item_id "
        "WHERE i.price_min > 0 AND i.published >= ? AND i.absolute_position IS NOT NULL "
        "GROUP BY t.tag",
        (winner_band, cutoff),
    ).fetchall()
    base = compute_base_young_win_rate(con, ref, winner_band, young_days) or 0.0
    out = []
    for r in rows:
        tag = r["tag"]
        n, wins = r["n"], r["wins"] or 0
        if n < min_n:
            continue
        win_rate = wins / n
        if win_rate < min_win:
            continue
        if rejected_family(tag, allow_free=allow_free):
            continue
        lift_row = con.execute(
            "SELECT pm_uses, banked FROM analysis_tag_lift WHERE tag = ? COLLATE NOCASE", (tag,)
        ).fetchone()
        pm_uses = lift_row["pm_uses"] if lift_row else None
        if pm_uses is None:
            pm_uses = 0
        if max_pm_uses is not None and pm_uses > max_pm_uses:
            continue
        overall_n = con.execute(
            "SELECT COUNT(DISTINCT item_id) FROM item_tags WHERE tag = ? COLLATE NOCASE", (tag,)
        ).fetchone()[0]
        out.append({
            "tag": tag,
            "young_paid_n": n,
            "young_paid_wins": wins,
            "young_paid_win_rate": win_rate,
            "young_paid_lift": (win_rate / base) if base else None,
            "pm_uses": pm_uses,
            "banked": bool(lift_row["banked"]) if lift_row else False,
            "overall_n": overall_n,
        })
    out.sort(key=lambda d: (-d["young_paid_win_rate"], -d["young_paid_n"]))
    return out[:limit], base


def free_lanes(con, *, limit=40, free_only=False):
    """Rank census tags by coverage among FREE items (price_min = 0).

    The paid young-cohort gate deliberately measures paid reach and bans the
    free-promo vocabulary, so it can never surface a free-campaign tag. This
    lane reads the free cohort directly: how many free items carry the tag and
    how they engage, which is the evidence a limited-time free offer needs.

    Coverage is catalog coverage, never demand; likes are comparison signals,
    never sales.
    """
    rows = con.execute(
        "SELECT t.tag AS tag, i.item_id AS item_id, i.price_min AS price_min, "
        "i.item_like_count AS likes "
        "FROM item_tags t JOIN items i ON i.item_id = t.item_id"
    ).fetchall()
    agg: dict[str, dict] = {}
    for r in rows:
        d = agg.setdefault(r["tag"], {"free_n": 0, "all_n": 0, "likes": []})
        d["all_n"] += 1
        if (r["price_min"] or 0) == 0:
            d["free_n"] += 1
            if r["likes"] is not None:
                d["likes"].append(r["likes"])
    out = []
    for tag, d in agg.items():
        if free_only and not campaign_mode.is_free_offer_tag(tag):
            continue
        out.append({
            "tag": tag,
            "free_n": d["free_n"],
            "all_n": d["all_n"],
            "free_share_pct": round(100 * d["free_n"] / d["all_n"], 1) if d["all_n"] else None,
            "free_median_likes": pct(d["likes"], 50),
            "free_offer_term": campaign_mode.is_free_offer_tag(tag),
        })
    out.sort(key=lambda x: (-x["free_n"], -x["all_n"], x["tag"]))
    return out[:limit]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Per-tag BOOTH young-cohort evidence gate + --top-lanes discovery")
    ap.add_argument("tags", nargs="*", help="tags to evaluate")
    ap.add_argument("--db", default=DEFAULT_DB, type=Path)
    ap.add_argument("-f", "--file", type=Path, help="read tags from a file, one per line")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument("--ref", default="2026-09-09", help="census reference date (YYYY-MM-DD)")
    ap.add_argument("--band", type=int, default=WINNER_BAND, help="winner band (absolute_position <= N); default 300")
    # --- --top-lanes discovery options ---
    ap.add_argument("--top-lanes", action="store_true", help="scan the whole census for high young-win-rate lanes")
    ap.add_argument("--min-n", type=int, default=TOPLANES_MIN_YOUNG_PAID, help="minimum young paid n for --top-lanes")
    ap.add_argument("--min-win-rate", type=float, default=TOPLANES_MIN_WIN_RATE, help="minimum young win-rate for --top-lanes")
    ap.add_argument("--max-pm-uses", type=int, default=None, help="include only lanes with pm_uses <= N (FontFairy ownership)")
    # --- campaign awareness ---
    ap.add_argument(
        "--campaign",
        default=campaign_mode.DEFAULT_MODE,
        help="campaign mode (default FREE_ACTIVE); free modes lift the free-promo tag ban",
    )
    ap.add_argument(
        "--free-lanes",
        action="store_true",
        help="discover free-campaign lanes by ranking tags on the FREE cohort",
    )
    ap.add_argument(
        "--free-only",
        action="store_true",
        help="with --free-lanes, keep only free-offer vocabulary tags",
    )
    args = ap.parse_args(argv)

    if not args.db.exists():
        sys.exit(f"error: census DB not found: {args.db}")

    ref = date.fromisoformat(args.ref)
    allow_free = campaign_mode.is_free_mode(args.campaign)
    con = sqlite3.connect(str(args.db))
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA cache_size=-64000")
        con.execute("PRAGMA temp_store=MEMORY")
    except sqlite3.Error:
        pass

    base = compute_base_young_win_rate(con, ref, args.band)

    if args.free_lanes:
        lanes = free_lanes(con, limit=50, free_only=args.free_only)
        if args.json:
            print(json.dumps({"cohort": "free", "lanes": lanes}, ensure_ascii=False, indent=2))
        else:
            print(
                f"BOOTH FREE-CAMPAIGN LANES — {SNAPSHOT_LABEL}, reference {args.ref}\n"
                f"Cohort: items with price_min = 0. Coverage is catalog coverage, "
                f"never demand; likes are comparison signals, never sales.\n"
                f"Filter: {'free-offer vocabulary only' if args.free_only else 'all tags'}\n"
            )
            print(
                f"{'lane':30s} {'free n':>7s} {'all n':>7s} {'free%':>6s} "
                f"{'med likes':>10s} {'free-term':>9s}"
            )
            for d in lanes:
                print(
                    f"{d['tag']:30s} {d['free_n']:7d} {d['all_n']:7d} "
                    f"{(d['free_share_pct'] if d['free_share_pct'] is not None else 0):6.1f} "
                    f"{fmt(d['free_median_likes']):>10s} "
                    f"{'yes' if d['free_offer_term'] else '':>9s}"
                )
        con.close()
        return 0

    if args.top_lanes:
        lanes, base_rate = top_lanes(
            con, ref, min_n=args.min_n, min_win=args.min_win_rate,
            max_pm_uses=args.max_pm_uses, winner_band=args.band, allow_free=allow_free,
            limit=50,
        )
        if args.json:
            print(json.dumps({"base_young_win_rate": base_rate, "lanes": lanes},
                             ensure_ascii=False, indent=2))
        else:
            print(f"BOOTH TOP LANES — {SNAPSHOT_LABEL}, reference {args.ref}\n"
                  f"Cohort baseline young-paid winner rate (position ≤ {args.band}): "
                  f"{100*(base_rate or 0):.1f}%\n"
                  f"Lanes: young paid n ≥ {args.min_n}, young win-rate ≥ {args.min_win_rate*100:.0f}%, "
                  f"rejected families excluded, pm_uses ≤ {args.max_pm_uses if args.max_pm_uses is not None else 'any'}\n")
            print(f"{'lane':34s} {'young n':>7s} {'wins':>5s} {'win%':>6s} {'lift':>5s} {'pm_uses':>7s} {'bank':>4s} {'all-time n':>9s}")
            for d in lanes:
                print(f"{d['tag']:34s} {d['young_paid_n']:7d} {d['young_paid_wins']:5d} "
                      f"{100*d['young_paid_win_rate']:6.1f}% "
                      f"{d['young_paid_lift']:5.2f} {d['pm_uses']:7d} "
                      f"{'Y' if d['banked'] else 'n':>4s} {d['overall_n']:9d}")
        con.close()
        return 0

    tags = list(args.tags)
    if args.file:
        tags.extend(
            ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()
        )
    if not tags:
        ap.error("provide at least one tag (args or -f file) or use --top-lanes")

    batch = load_batch(con, tags)
    results = [
        evidence_for(con, tag, ref, base_young_win_rate=base, winner_band=args.band,
                     allow_free=allow_free, _batch=batch)
        for tag in tags
    ]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(
            f"BOOTH census evidence — {SNAPSHOT_LABEL} (crawl_date "
            f"{con.execute('SELECT MAX(crawl_date) FROM items').fetchone()[0]}), "
            f"reference date {args.ref}\n"
            f"Gate: young-paid win-rate ≥ {int(WIN_RATE_STRONG*100)}% with n ≥ {STRONG_MIN_YOUNG_PAID} "
            f"(STRONG), 5-{int(WIN_RATE_STRONG*100)}% (MODERATE), thin-n < {STRONG_MIN_YOUNG_PAID} "
            f"(honest label only). All-time lift is context, never a pass.\n"
            f"Cohort baseline: {100*(base or 0):.1f}% of young paid items reach position ≤ {args.band}.\n"
        )
        for e in results:
            print(render(e))

    con.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. `| head`
        sys.exit(0)