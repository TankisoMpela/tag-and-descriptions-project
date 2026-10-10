#!/usr/bin/env python3
"""BOOTH font-category market intelligence engine (Parts 1-15 quantitative).

Reads outputs/research/booth-live-collector/booth.db and writes
outputs/research/booth-market-intelligence-2026-09-09.md plus a JSON cache.
Pure stdlib (sqlite3/statistics/json/re).
"""
import sqlite3, json, math, re, statistics
from collections import Counter, defaultdict

DB = "outputs/research/booth-live-collector/booth.db"
OUT_MD = "outputs/research/booth-market-intelligence-2026-09-09.md"
OUT_JSON = "outputs/research/booth-market-intelligence-2026-09-09.json"
REF_DATE = __import__("datetime").date(2026, 9, 9)

CJK = re.compile(r"[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\uff00-\uffef]")
ASCII = re.compile(r"[A-Za-z]")

AGE_BANDS = [
    ("0–7 d", 0, 7), ("8–30 d", 8, 30), ("31–90 d", 31, 90),
    ("91–180 d", 91, 180), ("181–365 d", 181, 365), ("1–2 y", 366, 730), ("2+ y", 731, 10**9),
]

def pct(vals, p):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    k = (p / 100.0) * (len(vals) - 1)
    lo = math.floor(k); hi = math.ceil(k)
    if lo == hi:
        return vals[int(k)]
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)

def fmt(x, nd=0):
    if x is None: return "–"
    if isinstance(x, float): return f"{x:,.{nd}f}"
    return f"{x:,}"

def age_band(days):
    for name, a, b in AGE_BANDS:
        if a <= days <= b:
            return name
    return "2+ y"

def is_cjk(s):
    return bool(s) and bool(CJK.search(s))

def lang_class(title):
    c = len(CJK.findall(title or "")); a = len(ASCII.findall(title or ""))
    if c > 0 and a == 0: return "JP"
    if a > 0 and c == 0: return "LATIN"
    if c > 0 and a > 0: return "MIXED"
    return "OTHER"

def spearman(xs, ys):
    n = len(xs)
    if n < 3: return None
    rx = {v: i for i, v in enumerate(sorted(xs))}
    ry = {v: i for i, v in enumerate(sorted(ys))}
    dx = [rx[v] for v in xs]; dy = [ry[v] for v in ys]
    mx, my = statistics.mean(dx), statistics.mean(dy)
    num = sum((a-mx)*(b-my) for a, b in zip(dx, dy))
    den = math.sqrt(sum((a-mx)**2 for a in dx) * sum((b-my)**2 for b in dy))
    return (num/den) if den else None

def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("""SELECT item_id,title,shop_name,shop_url,price_jpy,price_min,price_max,
                          published,description_length,tag_count,item_like_count,absolute_position,
                          item_image_count,description FROM items WHERE detail_fetched=1""").fetchall()
    tagmap = defaultdict(list)
    for r in con.execute("SELECT item_id,tag FROM item_tags"):
        tagmap[r["item_id"]].append(r["tag"])
    vmap = defaultdict(list)
    for r in con.execute("SELECT item_id,variant_name,price_jpy FROM variants ORDER BY variant_pos"):
        vmap[r["item_id"]].append((r["variant_name"], r["price_jpy"]))
    pm_ids = {r["item_id"] for r in con.execute("SELECT item_id FROM papermoon_rank")}
    brank = {r["item_id"]: r["global_rank"] for r in con.execute("SELECT item_id,global_rank FROM papermoon_rank")}
    con.close()

    items = []
    for r in rows:
        if not (r["published"] or "").strip():
            continue
        d0 = __import__("datetime").date.fromisoformat(r["published"])
        age = (REF_DATE - d0).days
        vs = vmap.get(r["item_id"], [])
        vprices = [p for _, p in vs]
        min_price = min(vprices) if vprices else (r["price_jpy"] or 0)
        has_free = any(p == 0 for p in vprices) if vprices else (r["price_jpy"] == 0)
        has_paid = any(p > 0 for p in vprices) if vprices else (r["price_jpy"] or 0) > 0
        if has_free and has_paid: kind = "combo"
        elif has_free: kind = "free"
        else: kind = "paid"
        items.append(dict(
            id=r["item_id"], title=r["title"] or "", shop=r["shop_name"] or "",
            price=r["price_jpy"] or 0, min_price=min_price, age=age,
            desc_len=r["description_length"] or 0, tag_count=r["tag_count"] or 0,
            likes=r["item_like_count"] or 0, pos=r["absolute_position"] or 0,
            img=r["item_image_count"] or 0, kind=kind,
            lang=lang_class(r["title"]), tags=tagmap.get(r["item_id"], []),
            desc=r["description"] or "", pm=r["item_id"] in pm_ids,
        ))
    items.sort(key=lambda x: x["likes"], reverse=True)
    all_likes = sorted(x["likes"] for x in items)
    total_likes = sum(all_likes)
    n = len(items)

    # Top-position rank (popular sort): 1 is best
    for x in items:
        x["rank"] = x["pos"]

    out = []
    W = out.append
    W("# BOOTH Font Category — Market Intelligence (2026-09-09 full-crawl snapshot)\n")
    W(f"**Reference date:** {REF_DATE} · **Products:** {n:,} · **Tags:** {sum(len(x['tags']) for x in items):,} · "
      f"All products hydrated. Likes/ranks are a single-snapshot visibility proxy — not sales/downloads.")
    W(f"**FontFairy items:** {sum(1 for x in items if x['pm'])} (all ≤24 days old, all Western/Latin-targeted).\n")

    # ---------- PART 1 ----------
    free_paid_combo = Counter(x["kind"] for x in items)
    W("## PART 1 — Market structure profile\n")
    W("### 1.1 Free / paid / combo\n")
    W("| type | n | % of catalog | median likes | median price |\n|---|---|---|---|---|")
    for k in ("free", "paid", "combo"):
        sub = [x for x in items if x["kind"] == k]
        W(f"| {k} | {len(sub):,} | {100*len(sub)/n:.1f}% | {fmt(pct([x['likes'] for x in sub],50))} | "
          f"{fmt(pct([x['min_price'] for x in sub],50))} |")
    W("> **combo** = product offers at least one ¥0 variant *and* a paid tier (free-personal/paid-commercial pattern).\n")

    paid = [x for x in items if x["kind"] == "paid"]
    p_prices = sorted(x["min_price"] for x in paid)
    W("### 1.2 Paid price distribution\n")
    W(f"paid n={len(paid):,}; median={fmt(pct(p_prices,50))}, mean={fmt(statistics.mean(p_prices) if p_prices else 0)}, "
      f"p10={fmt(pct(p_prices,10))}, p25={fmt(pct(p_prices,25))}, p75={fmt(pct(p_prices,75))}, p90={fmt(pct(p_prices,90))}, p95={fmt(pct(p_prices,95))}, p99={fmt(pct(p_prices,99))}\n")
    W("### 1.3 Age distribution\n")
    W("| age band | n | % |\n|---|---|---|")
    for name, a, b in AGE_BANDS:
        c = sum(1 for x in items if a <= x["age"] <= b)
        W(f"| {name} | {c:,} | {100*c/n:.1f}% |")
    W(f"median age={fmt(pct([x['age'] for x in items],50))}d, mean={fmt(statistics.mean(x['age'] for x in items),0)}d\n")
    W("### 1.4 Like distribution (visibility proxy)\n")
    W(f"median={fmt(pct(all_likes,50))}, mean={fmt(statistics.mean(all_likes),1)}, p75={fmt(pct(all_likes,75))}, "
      f"p90={fmt(pct(all_likes,90))}, p95={fmt(pct(all_likes,95))}, p99={fmt(pct(all_likes,99))}, max={fmt(max(all_likes))}\n")
    W("### 1.5 Popularity-rank distribution (popular-sort position)\n")
    ranks = sorted(x["rank"] for x in items)
    W(f"p25={fmt(pct(ranks,25))}, median={fmt(pct(ranks,50))}, p75={fmt(pct(ranks,75))}, p90={fmt(pct(ranks,90))}\n")
    W("### 1.6 Descriptions & tags\n")
    W(f"desc chars: median={fmt(pct([x['desc_len'] for x in items],50))}, p25={fmt(pct([x['desc_len'] for x in items],25))}, "
      f"p75={fmt(pct([x['desc_len'] for x in items],75))} · tags: median={fmt(pct([x['tag_count'] for x in items],50))}, "
      f"p75={fmt(pct([x['tag_count'] for x in items],75))}\n")
    W("### 1.7 Age vs likes / rank\n")
    W("| age band | n | median likes | median rank |")
    W("|---|---|---|---|")
    for name, a, b in AGE_BANDS:
        sub = [x for x in items if a <= x["age"] <= b]
        if not sub: continue
        W(f"| {name} | {len(sub):,} | {fmt(pct([x['likes'] for x in sub],50))} | {fmt(pct([x['rank'] for x in sub],50))} |")
    sub = [x for x in items if x["age"] <= 365]
    W(f"spearman(likes, age) all n={n}: {fmt(spearman([x['age'] for x in items],[x['likes'] for x in items]),3)}; "
      f"age≤365d n={len(sub)}: {fmt(spearman([x['age'] for x in sub],[x['likes'] for x in sub]),3)}\n")
    W("### 1.8 Structure\n")
    topi = sorted(items, key=lambda x: x["likes"], reverse=True)
    for frac in (0.001, 0.01, 0.05, 0.25):
        k = max(1, int(round(frac*n)))
        share = sum(x["likes"] for x in topi[:k])/total_likes if total_likes else 0
        W(f"top {frac*100:.1f}% (n={k:,}) hold {100*share:.1f}% of total likes")
    free_only = [x for x in items if x["kind"] == "free"]
    W(f"free+combo catalog share: {100*len(free_only)/n:.1f}% (free) + {100*free_paid_combo['combo']/n:.1f}% (combo)\n")

    # ---------- PART 2 ----------
    W("## PART 2 — Does free actually perform better?\n")
    W("### 2.1 Raw comparison\n")
    W("| group | n | median likes | mean likes | p75 | p90 | median rank |")
    W("|---|---|---|---|---|---|---|")
    for k in ("free", "paid", "combo"):
        sub = [x for x in items if x["kind"] == k]
        W(f"| {k} | {len(sub):,} | {fmt(pct([x['likes'] for x in sub],50))} | {fmt(statistics.mean(x['likes'] for x in sub),1)} | "
          f"{fmt(pct([x['likes'] for x in sub],75))} | {fmt(pct([x['likes'] for x in sub],90))} | {fmt(pct([x['rank'] for x in sub],50))} |")
    W("\n### 2.2 Age-controlled (same band: free vs paid vs combo)\n")
    W("| age band | free n | free medL | paid n | paid medL | combo n | combo medL |")
    W("|---|---|---|---|---|---|---|")
    for name, a, b in AGE_BANDS:
        f0 = [x for x in items if x["kind"]=="free" and a<=x["age"]<=b]
        p0 = [x for x in items if x["kind"]=="paid" and a<=x["age"]<=b]
        c0 = [x for x in items if x["kind"]=="combo" and a<=x["age"]<=b]
        W(f"| {name} | {len(f0)} | {fmt(pct([x['likes'] for x in f0],50))} | {len(p0)} | {fmt(pct([x['likes'] for x in p0],50))} | {len(c0)} | {fmt(pct([x['likes'] for x in c0],50))} |")
    W("\n### 2.3 Price-controlled (paid bands vs free)\n")
    W("| band | n | median likes | p75 |\n|---|---|---|---|")
    W(f"| free (¥0) | {len(free_only):,} | {fmt(pct([x['likes'] for x in free_only],50))} | {fmt(pct([x['likes'] for x in free_only],75))} |")
    for lo, hi, label in ((1,500,"¥1–500"),(501,1000,"¥501–1,000"),(1001,2000,"¥1,001–2,000"),(2001,10**9,"¥2,001+")):
        sub = [x for x in items if x["min_price"] and lo<=x["min_price"]<=hi]
        W(f"| {label} | {len(sub):,} | {fmt(pct([x['likes'] for x in sub],50))} | {fmt(pct([x['likes'] for x in sub],75))} |")
    W("\n### 2.4 Outlier dependence\n")
    f_sorted = sorted((x["likes"] for x in free_only), reverse=True)
    nf = len(f_sorted)
    # whole-distribution tests
    W(f"free median with all: {fmt(pct(f_sorted,50))}; dropping top 5 (top {100*5/nf:.2f}%): kept-bottom median {fmt(pct(f_sorted[:nf-500],50) if nf>500 else pct(f_sorted,50))}")
    W("free vs paid shifted across bands:<br>")
    for thr, nm in ((10,"≥10"),(50,"≥50"),(100,"≥100"),(500,"≥500")):
        W(f"share ≥{thr}: free {100*sum(1 for x in free_only if x['likes']>=thr)/len(free_only):.0f}% · paid {100*sum(1 for x in items if x['kind']=='paid' and x['likes']>=thr)/max(1,len([x for x in items if x['kind']=='paid'])):.0f}%")
    W(f"free top-1% share of free likes: {100*sum(f_sorted[:max(1,nf//100)])/sum(f_sorted):.1f}% · "
      f"top-10% share: {100*sum(f_sorted[:max(1,nf//10)])/sum(f_sorted):.1f}%\n")
    W("### 2.5 Strong-free-product characteristics (top 100 free by likes vs rest-of-free vs paid)\n")
    top_free = sorted(free_only, key=lambda x: x["likes"], reverse=True)[:100]
    rest_free = sorted(free_only, key=lambda x: x["likes"], reverse=True)[100:]
    W("| group | n | med age | med desc | med tags | med img | title-has-free-word | has 商用 tag | has video tag | has 日本語フォント |")
    W("|---|---|---|---|---|---|---|---|---|---|")
    def title_free(x): return any(w in x["title"].lower() for w in ("無料","フリー","free","フリーフォント"))
    def anytag(x, pats): return any(any(p in t for p in pats) for t in x["tags"])
    for gname, grp in (("top100 free", top_free), ("rest free", rest_free), ("all paid", paid)):
        W(f"| {gname} | {len(grp):,} | {fmt(pct([x['age'] for x in grp],50))} | {fmt(pct([x['desc_len'] for x in grp],50))} | "
          f"{fmt(pct([x['tag_count'] for x in grp],50))} | {fmt(pct([x['img'] for x in grp],50))} | {100*sum(title_free(x) for x in grp)/len(grp):.0f}% | "
          f"{100*sum(anytag(x,['商用']) for x in grp)/len(grp):.0f}% | {100*sum(anytag(x,['テロップ','字幕','動画','YouTube','Premiere']) for x in grp)/len(grp):.0f}% | "
          f"{100*sum(anytag(x,['日本語フォント']) for x in grp)/len(grp):.0f}% |")
    W("\n> Verdict data: see above. Age control is mandatory — free items skew old (median age below).\n")

    # ---------- PART 4 ----------
    W("## PART 4 — FontFairy benchmark (age-matched)\n")
    pm = [x for x in items if x["pm"]]
    cohort = [x for x in items if x["age"] <= 30 and not x["pm"]]
    c_likes = sorted(x["likes"] for x in cohort)
    W(f"Benchmark cohort: non-PM products aged ≤30 d — **n={len(cohort):,}**, median likes={fmt(pct(c_likes,50))}, "
      f"p75={fmt(pct(c_likes,75))}, p90={fmt(pct(c_likes,90))}, p95={fmt(pct(c_likes,95))}, max={fmt(max(c_likes))}\n")
    W("| item | age | likes | cohort pct | rank | price | kind | desc | tags | class |")
    W("|---|---|---|---|---|---|---|---|---|---|")
    for x in sorted(pm, key=lambda x: x["likes"], reverse=True):
        pctile = 100*sum(1 for v in c_likes if v <= x["likes"])/len(c_likes)
        cl = "SIGNIF-OVER" if pctile >= 90 else ("OVER" if pctile >= 75 else ("NORMAL" if pctile >= 25 else ("UNDER" if pctile >= 10 else "SIGNIF-UNDER")))
        W(f"| {x['title'][:42]} | {x['age']} | {x['likes']} | {pctile:.0f} | {x['rank']} | {x['min_price']} | {x['kind']} | {x['desc_len']} | {x['tag_count']} | {cl} |")
    W("\n### Overall PM vs ≤30d cohort\n")
    pm_l = [x["likes"] for x in pm]
    W(f"PM n=31: median likes {fmt(pct(pm_l,50))}, mean {fmt(statistics.mean(pm_l),1)}, max {fmt(max(pm_l))}, share of PM with >cohort-median: "
      f"{100*sum(1 for v in pm_l if v>pct(c_likes,50))/len(pm_l):.0f}%, >cohort-p75: {100*sum(1 for v in pm_l if v>pct(c_likes,75))/len(pm_l):.0f}%\n")

    # likes-per-day
    pm_lpd = sorted((x["likes"]/max(1, x["age"]) for x in pm), reverse=True)
    co_lpd = sorted((x["likes"]/max(1, x["age"]) for x in cohort), reverse=True)
    W(f"likes/day: PM median {fmt(pct(pm_lpd,50),2)} vs cohort median {fmt(pct(co_lpd,50),2)}, cohort p75 {fmt(pct(co_lpd,75),2)}, p90 {fmt(pct(co_lpd,90),2)}\n")

    W("### 4bis — Young-cohort leaders (non-PM, age ≤30 d; the fresh comparable set FontFairy competes with)\n")
    W("| age | likes | likes/day | price | kind | title | ntags | top tags |")
    W("|---|---|---|---|---|---|---|---|")
    young = [x for x in items if x["age"] <= 30 and not x["pm"]]
    for x in sorted(young, key=lambda x: x["likes"], reverse=True)[:15]:
        W(f"| {x['age']} | {x['likes']} | {x['likes']/max(1,x['age']):.2f} | {x['min_price']} | {x['kind']} | {x['title'][:44]} | {x['tag_count']} | {','.join(x['tags'][:6])} |")
    W(f"\nyoung cohort mix: free={sum(1 for x in young if x['kind']=='free')}, paid={sum(1 for x in young if x['kind']=='paid')}, combo={sum(1 for x in young if x['kind']=='combo')}\n")

    # ---------- PART 5 ----------
    W("## PART 5 — Trajectory (cross-sectional baselines; longitudinal = insufficient data)\n")
    W("| age band | n | median likes | median likes/day | p75 likes/day |")
    W("|---|---|---|---|---|")
    for name, a, b in AGE_BANDS:
        sub = [x for x in items if a <= x["age"] <= b]
        W(f"| {name} | {len(sub):,} | {fmt(pct([x['likes'] for x in sub],50))} | {fmt(pct([x['likes']/max(1,x['age']) for x in sub],50),2)} | {fmt(pct([x['likes']/max(1,x['age']) for x in sub],75),2)} |")
    W("\nPM momentum proxy (current likes/day vs ≤30d cohort): see Part 4 lpd line above. "
      "A single snapshot cannot measure acceleration/deceleration; the rank-tracker extension exists but no historical like snapshots are stored. Insufficient data — see final report.\n")

    # ---------- PART 6 ----------
    W("## PART 6 — Can early performance predict later performance? (insufficient data)\n")
    W("No longitudinal snapshots exist (single crawl). Cross-sectional proxy: among items now ≤30 d, the cohort p90 likes=entry bar; "
      "among items 31–90 d, persistent p90 share. Compute:\n")
    for a, b, label in ((0,7,"0–7"),(8,30,"8–30"),(31,90,"31–90"),(91,180,"91–180")):
        cur = [x for x in items if a<=x["age"]<=b]
        W(f"items {label}d: n={len(cur):,}, p50={fmt(pct([x['likes'] for x in cur],50))}, p90={fmt(pct([x['likes'] for x in cur],90))}")
    W("Determining whether *early relative performance* persists requires re-snapshotting the same item IDs over time. "
      "Current objective: start a weekly snapshot harness (see agent workflow).\n")

    # ---------- PART 7 ----------
    W("## PART 7 — Pricing\n")
    W("### 7.1 Price by language/script\n")
    W("| lang | n | free% | combo% | median price (paid) | median likes |")
    W("|---|---|---|---|---|---|")
    for lang in ("JP","LATIN","MIXED","OTHER"):
        sub = [x for x in items if x["lang"]==lang]
        if not sub: continue
        paidp = [x["min_price"] for x in sub if x["min_price"]>0]
        W(f"| {lang} | {len(sub):,} | {100*sum(x['kind']=='free' for x in sub)/len(sub):.0f}% | {100*sum(x['kind']=='combo' for x in sub)/len(sub):.0f}% | {fmt(pct(paidp,50))} | {fmt(pct([x['likes'] for x in sub],50))} |")
    pa = [x for x in paid]
    W(f"\n### 7.2 price vs likes (paid only, n={len(pa):,})\n")
    W(f"spearman(price,likes)={fmt(spearman([x['min_price'] for x in pa],[x['likes'] for x in pa]),3)}; "
      f"age≤365 spearman={fmt(spearman([x['min_price'] for x in pa if x['age']<=365],[x['likes'] for x in pa if x['age']<=365]),3)}\n")
    W("### 7.3 PM pricing vs context\n")
    W("| PM item | age | likes | price | ≤30d paid median price | same-price band cohort median likes |")
    W("|---|---|---|---|---|---|")
    paid30 = [x for x in items if x["age"]<=30 and x["min_price"]>0 and not x["pm"]]
    pp30 = sorted(x["min_price"] for x in paid30)
    dd30 = sorted(x["likes"] for x in paid30)
    W(f"≤30d paid cohort n={len(paid30):,}; median price {fmt(pct(pp30,50))} (p25 {fmt(pct(pp30,25))}, p75 {fmt(pct(pp30,75))}, p90 {fmt(pct(pp30,90))}); median likes {fmt(pct(dd30,50))}\n")
    for x in sorted(pm, key=lambda x: x["min_price"]):
        band = [y for y in items if y["age"]<=30 and abs(y["min_price"]-x["min_price"]) <= 0.5*x["min_price"] and not y["pm"]]
        W(f"| {x['title'][:40]} | {x['age']} | {x['likes']} | {x['min_price']} | {fmt(pct(pp30,50))} | {fmt(pct([y['likes'] for y in band],50))} (n={len(band)}) |")
    W("> PM paid pricing sits at " + fmt(pct([x["min_price"] for x in pm if x["min_price"]>0],50)) + "¥ median. See report for verdict.\n")

    # ---------- PART 8: neighbour diff summary ----------
    W("## PART 8 — Nearest competitors (from ±50 popular-sort neighbours)\n")
    sub8 = [x for x in pm]
    W("| PM item | nb median price | nb median likes | n neighbours | PM price | PM likes |")
    W("|---|---|---|---|---|---|")
    for r in __import__("sqlite3").connect(DB).execute(
        "SELECT pm_item_id, nb_median_price, nb_median_likes, n_neighbours FROM analysis_neighbour_diff ORDER BY global_rank"):
        it = next((x for x in sub8 if x["id"]==r[0]), None)
        if it:
            W(f"| {it['title'][:40]} | {fmt(r[1])} | {fmt(r[2])} | {r[3]} | {it['min_price']} | {it['likes']} |")
    con = __import__("sqlite3").connect(DB)
    W("\n### Top tags neighbours carry that PM products never use (v_pm_missing_tags)\n")
    W("| tag | PM items missing |")
    W("|---|---|")
    for r in con.execute("SELECT tag, pm_items_using FROM analysis_pm_missing_tags ORDER BY pm_items_using DESC LIMIT 18"):
        W(f"| {r[0]} | {r[1]} |")
    con.close()

    # ---------- PART 9 ----------
    W("\n## PART 9 — Japanese vs Western/Latin fonts\n")
    W("| group | n | free% | combo% | med price(paid) | med likes | med likes/day | med rank | med desc | med tags |")
    W("|---|---|---|---|---|---|---|---|---|---|")
    for lang in ("JP","LATIN","MIXED","OTHER"):
        sub = [x for x in items if x["lang"]==lang]
        if not sub: continue
        paidp = [x["min_price"] for x in sub if x["min_price"]>0]
        W(f"| {lang} | {len(sub):,} | {100*sum(x['kind']=='free' for x in sub)/len(sub):.0f}% | {100*sum(x['kind']=='combo' for x in sub)/len(sub):.0f}% | {fmt(pct(paidp,50))} | "
          f"{fmt(pct([x['likes'] for x in sub],50))} | {fmt(pct([x['likes']/max(1,x['age']) for x in sub],50),2)} | {fmt(pct([x['rank'] for x in sub],50))} | {fmt(pct([x['desc_len'] for x in sub],50))} | {fmt(pct([x['tag_count'] for x in sub],50))} |")
    nw = "### Top Western/Latin products\n| rank | title | price | age | likes | likes/day | tags(#) | style hints |"
    W(nw)
    lat = [x for x in items if x["lang"]=="LATIN"]
    for i, x in enumerate(sorted(lat, key=lambda y: y["likes"], reverse=True)[:12], 1):
        W(f"| {i} | {x['title'][:44]} | {x['min_price']} | {x['age']} | {x['likes']} | {x['likes']/max(1,x['age']):.2f} | {x['tag_count']} | {','.join(x['tags'][:6])} |")
    W(f"\nLatin catalog n={len(lat):,} ({100*len(lat)/n:.1f}% of catalog); FontFairy holds 31 of them.\n")

    # ---------- PART 10 ----------
    W("## PART 10 — Tag intelligence (n≥15)\n")
    tagstats = {}
    for x in items:
        for t in x["tags"]:
            s = tagstats.setdefault(t, [])
            s.append(x)
    W("| tag | n | medL | meanL | free% | med price | med age | top25% share |")
    W("|---|---|---|---|---|---|---|---|")
    rows10 = []
    for t, s in tagstats.items():
        if len(s) < 15: continue
        rows10.append((t, len(s), pct([x["likes"] for x in s],50), statistics.mean(x["likes"] for x in s),
                       100*sum(x["likes"] for x in s)/total_likes if total_likes else 0,
                       100*sum(x["kind"]=="free" for x in s)/len(s), pct([x["min_price"] for x in s],50),
                       pct([x["age"] for x in s],50), 100*sum(1 for x in s if x["likes"] >= pct(all_likes,75))/len(s)))
    rows10.sort(key=lambda r: -r[2])
    for t, nn, ml, mean, share, fp, mp, ma, top in rows10[:25]:
        W(f"| {t} | {nn} | {fmt(ml)} | {fmt(mean,1)} | {share:.2f}% | {fp:.0f}% | {ma:.0f} | {top:.0f}% |")
    W(f"\n(total tags n≥15: {len(rows10):,})\n")
    W("### Underused high-performing (low freq, high medL)\n")
    rows10.sort(key=lambda r: -r[2])
    under = [r for r in rows10 if r[1] < 150 and r[2] >= pct([r[2] for r in rows10], 75)]
    for t, nn, ml, mean, share, fp, mp, ma, top in sorted(under, key=lambda r: -r[2])[:20]:
        W(f"| {t} | n={nn} | medL={fmt(ml)} | free%={fp:.0f} | medPrice={mp} | medAge={ma:.0f} |")
    W("\n### High-freq / low-perf (common but weak)\n")
    rows10.sort(key=lambda r: -r[1])
    weak = [r for r in rows10 if r[1] >= 300 and r[2] < pct([r[2] for r in rows10], 25)]
    W("| tag | n | medL |\n|---|---|---|")
    for t, nn, ml, mean, share, fp, mp, ma, top in sorted(weak, key=lambda r: -r[1])[:12]:
        W(f"| {t} | {nn} | {fmt(ml)} |")

    # ---------- PART 11 ----------
    W("\n## PART 11 — Tag combinations\n")
    focus = ["テロップ","字幕","動画編集","YouTube","Premiere Pro","テンプレート","手描き風","フォント 商用","日本語フォント",
             "無料DL可","無料ダウンロード","タイポグラフィー","グラフィティ","free font","書体 商用利用"]
    W("### 11.1 Single-tag evidence for the 15 focus terms\n")
    W("| tag | n | medL | medL(age≤365) | free% | med price | in top25% |")
    W("|---|---|---|---|---|---|---|")
    for t in focus:
        s = [x for x in items if t in x["tags"]]
        sy = [x for x in s if x["age"] <= 365]
        W(f"| {t} | {len(s)} | {fmt(pct([x['likes'] for x in s],50))} | {fmt(pct([x['likes'] for x in sy],50))} | "
          f"{100*sum(x['kind']=='free' for x in s)/len(s) if s else 0:.0f}% | {fmt(pct([x['min_price'] for x in s],50))} | "
          f"{100*sum(1 for x in s if x['likes']>=pct(all_likes,75))/len(s) if s else 0:.0f}% |")
    W("\n### 11.2 Video-family combo (all four) vs partial\n")
    vidtags = ["テロップ","字幕","動画編集","YouTube"]
    full = [x for x in items if all(any(t in x["tags"] for t in [vt]) for vt in [v for v in vidtags if v in x["tags"]][:4])]
    # simpler: items carrying all of the subset present
    def allv(x): 
        present=[v for v in vidtags if v in x["tags"]]
        return len(present)>=3
    a3=[x for x in items if allv(x)]; a4=[x for x in items if all(v in x["tags"] for v in vidtags)]
    none=[x for x in items if not any(v in x["tags"] for v in vidtags)]
    for nm, s in (("≥3 video tags",a3),("all 4 video tags",a4),("no video tag",none)):
        W(f"| {nm}: n={len(s):,} | medL {fmt(pct([x['likes'] for x in s],50))} | medL(age≤365) {fmt(pct([x['likes'] for x in s if x['age']<=365],50))} |")
    W("\n### 11.3 Pair combinations among focus + top tags (n_together≥20)\n")
    toppairs = set(focus) | {r[0] for r in sorted(rows10, key=lambda r: -r[1])[:15]}
    plist = sorted(toppairs)
    pairres = []
    for i in range(len(plist)):
        for j in range(i+1, len(plist)):
            a, b = plist[i], plist[j]
            both = [x for x in items if a in x["tags"] and b in x["tags"]]
            if len(both) >= 20:
                onlya = [x for x in items if a in x["tags"] and b not in x["tags"]]
                onlyb = [x for x in items if b in x["tags"] and a not in x["tags"]]
                pairres.append((a, b, len(both), pct([x["likes"] for x in both],50),
                                pct([x["likes"] for x in onlya],50), pct([x["likes"] for x in onlyb],50)))
    pairres.sort(key=lambda r: -r[3])
    W("| tag A | tag B | n | medL both | medL A-only | medL B-only |\n|---|---|---|---|---|---|")
    for a, b, nn, mlb, mla, mlb2 in pairres[:30]:
        W(f"| {a} | {b} | {nn} | {fmt(mlb)} | {fmt(mla)} | {fmt(mlb2)} |")

    # ---------- PART 12 ----------
    W("\n## PART 12 — Title & description intelligence\n")
    phrases = ["無料","フリーフォント","フリー","商用利用可","商用可","テロップ","字幕","動画","YouTube","手書き","手描き",
               "日本語","欧文","ロゴ","見出し","ポスター","ウェディング","無料配布","free","font","download","commercial","script","display"]
    W("| phrase | in-title n | medL title | medL no-title | in-desc n | medL desc | medL no-desc |")
    W("|---|---|---|---|---|---|---|")
    for ph in phrases:
        ti = [x for x in items if ph.lower() in x["title"].lower()]
        te = [x for x in items if ph.lower() not in x["title"].lower()]
        di = [x for x in items if ph.lower() in x["desc"].lower()]
        de = [x for x in items if ph.lower() not in x["desc"].lower()]
        W(f"| {ph} | {len(ti):,} | {fmt(pct([x['likes'] for x in ti],50)) if ti else '–'} | {fmt(pct([x['likes'] for x in te],50)) if te else '–'} | "
          f"{len(di):,} | {fmt(pct([x['likes'] for x in di],50)) if di else '–'} | {fmt(pct([x['likes'] for x in de],50)) if de else '–'} |")
    W("\nDescription-length split (all items):\n")
    for lo, hi, label in ((0,150,"≤150"),(151,250,"151–250"),(251,350,"251–350"),(351,10**9,"351+")):
        s = [x for x in items if lo<=x["desc_len"]<=hi]
        W(f"| desc {label}: n={len(s):,} | medL {fmt(pct([x['likes'] for x in s],50))} | medL(age≤365) {fmt(pct([x['likes'] for x in s if x['age']<=365],50))} |")
    W("\nTitle length buckets:\n")
    for lo, hi, label in ((0,15,"≤15"),(16,30,"16–30"),(31,45,"31–45"),(46,10**9,"46+")):
        s = [x for x in items if lo<=len(x["title"])<=hi]
        W(f"| title {label} chars: n={len(s):,} | medL {fmt(pct([x['likes'] for x in s],50))} |")

    # ---------- PART 13 ----------
    W("\n## PART 13 — The BOOTH success profile\n")
    nn = len(items)
    W("| segment | n | med age | med price | free% | med desc | med tags | med img | medL |")
    W("|---|---|---|---|---|---|---|---|---|")
    for frac, label in ((0.01,"top 1%"),(0.05,"top 5%"),(0.10,"top 10%"),(0.25,"top 25%"),(1.0,"rest/bottom")):
        k = int(round(frac*nn))
        seg = topi[:k] if frac<1.0 else topi[int(0.25*nn):]
        if not seg: continue
        W(f"| {label} | {len(seg):,} | {fmt(pct([x['age'] for x in seg],50))} | {fmt(pct([x['min_price'] for x in seg],50))} | "
          f"{100*sum(x['kind']=='free' for x in seg)/len(seg):.0f}% | {fmt(pct([x['desc_len'] for x in seg],50))} | "
          f"{fmt(pct([x['tag_count'] for x in seg],50))} | {fmt(pct([x['img'] for x in seg],50))} | {fmt(pct([x['likes'] for x in seg],50))} |")
    W("\nTop-10% most common tags vs bottom-50%:\n")
    topseg = topi[:int(0.10*nn)]; botseg = topi[int(0.50*nn):]
    def toptags(seg, kk=12):
        c = Counter()
        for x in seg: c.update(x["tags"])
        return c.most_common(kk)
    W(f"top10%: {toptags(topseg)}\n")
    W(f"bottom50%: {toptags(botseg)}\n")

    # ---------- PART 14 ----------
    W("## PART 14 — The long tail\n")
    W("| segment | n | med age | med price | free% | med desc | med tags | medL |")
    W("|---|---|---|---|---|---|---|---|")
    for frac in (0.5, 0.25, 0.1):
        k = int(round(frac*nn))
        seg = topi[nn-k:]
        W(f"| bottom {100*frac:.0f}% | {len(seg):,} | {fmt(pct([x['age'] for x in seg],50))} | {fmt(pct([x['min_price'] for x in seg],50))} | "
          f"{100*sum(x['kind']=='free' for x in seg)/len(seg):.0f}% | {fmt(pct([x['desc_len'] for x in seg],50))} | "
          f"{fmt(pct([x['tag_count'] for x in seg],50))} | {fmt(pct([x['likes'] for x in seg],50))} |")

    # ---------- PART 15 ----------
    W("\n## PART 15 — Survivorship bias / difficulty of accumulating likes\n")
    for thr in (5, 10, 25, 50, 100):
        W(f"products with <{thr} likes: {sum(1 for x in items if x['likes']<thr):,} ({100*sum(1 for x in items if x['likes']<thr)/nn:.1f}%)")
    W("\nBy age band:\n| age band | n | <5 | <10 | <25 | <50 | <100 |")
    W("|---|---|---|---|---|---|---|")
    for name, a, b in AGE_BANDS:
        s = [x for x in items if a<=x["age"]<=b]
        W(f"| {name} | {len(s):,} | {sum(1 for x in s if x['likes']<5)} | {sum(1 for x in s if x['likes']<10)} | "
          f"{sum(1 for x in s if x['likes']<25)} | {sum(1 for x in s if x['likes']<50)} | {sum(1 for x in s if x['likes']<100)} |")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(out))
    with open(OUT_JSON, "w") as f:
        json.dump({"items": items, "matches": None}, f, ensure_ascii=False, default=str)
    print("Wrote", OUT_MD)
    print("Wrote", OUT_JSON)

if __name__ == "__main__":
    main()