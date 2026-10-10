#!/usr/bin/env python3
"""Tag verdict analysis: which tags really work vs which to rule out.
Controls: age window (all / <=365d / <=90d) x pricing (all / paid / free).
Baselines computed per window so tags are compared to their own peer set.
"""
import sqlite3, datetime, statistics, math
from collections import defaultdict

DB = "outputs/research/booth-live-collector/booth.db"
REF = datetime.date(2026, 9, 9)

def pct(vals, p):
    vals = sorted(v for v in vals if v is not None)
    if not vals: return None
    k = (p/100.0)*(len(vals)-1)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi: return vals[int(k)]
    return vals[lo] + (vals[hi]-vals[lo])*(k-lo)

con = sqlite3.connect(DB)
rows = con.execute("SELECT item_id, title, price_jpy, published, item_like_count, detail_fetched FROM items WHERE detail_fetched=1").fetchall()
tagmap = defaultdict(list)
for item_id, tag in con.execute("SELECT item_id, tag FROM item_tags"):
    tagmap[item_id].append(tag)
con.close()

items = []
for iid, title, price, pub, likes, df in rows:
    if not (pub or "").strip(): continue
    age = (REF - datetime.date.fromisoformat(pub)).days
    items.append(dict(id=iid, age=age, likes=likes, free=(price or 0) == 0, tags=tagmap.get(iid, [])))

def wset(items, age=None, kind=None):
    out = items
    if age is not None:
        out = [x for x in out if x["age"] <= age]
    if kind == "paid":
        out = [x for x in out if not x["free"]]
    elif kind == "free":
        out = [x for x in out if x["free"]]
    return out

# Baselines
def base(age=None, kind=None):
    s = wset(items, age, kind)
    return len(s), pct([x["likes"] for x in s], 50), pct([x["likes"] for x in s], 75)

print("=== BASELINES (n / median likes / p75) ===")
print(f"{'window':<18} {'n':>6} {'med':>6} {'p75':>6}")
for age, lbl in ((None, "all"), (365, "<=365d"), (90, "<=90d")):
    for kind, kl in ((None, "all"), ("paid", "paid"), ("free", "free")):
        n, m, q = base(age, kind)
        print(f"{str(lbl)+' '+kl:<18} {n:>6} {m or 0:>6} {q or 0:>6}")

print()
print("=== TAG VERDICT MATRIX ===")
cands = ["テロップ","字幕","動画編集","YouTube","Premiere Pro","テンプレート","エッセンシャルグラフィックス",
 "フォント 商用","書体 商用利用","書体 商用","商用利用可","商業利用可",
 "無料DL可","無料ダウンロード","無料DL","無料フォント","フリーフォント","free font",
 "手書き","手描き","手描き風","タイポグラフィー","タイポグラフィ","グラフィティ","カリグラフィ",
 "日本語フォント","和文","和文フォント","テキスト","文字","ダウンロード",
 "ロゴ","ロゴデザイン","ロゴ素材","サムネイル素材","ブランディング","ウェディング","招待状","名刺","ポスター","見出し",
 "display font","font download","serif font","欧文フォント","英字フォント","英語フォント","デザインフォント","装飾フォント",
 "オリジナルフォント","セリフフォント","筆記体","サンセリフ"]

def stat(tag, age=None, kind=None):
    s = wset(items, age, kind)
    t = [x for x in s if tag in x["tags"]]
    if len(t) < 10: return None
    return len(t), pct([x["likes"] for x in t], 50), pct([x["likes"] for x in t], 75)

print(f"{'tag':<22} {'n':>4} {'med':>5}  {'<=365d':>5} {'<=365dP':>6} {'p90d':>5}  {'free%':>5} {'medAge':>6}")
for tag in cands:
    r = stat(tag)
    if not r: continue
    n, m, q = r
    a = stat(tag, age=365)
    ap = stat(tag, age=365, kind="paid")
    d = stat(tag, age=90)
    fr = 100*sum(1 for x in items if tag in x["tags"] and x["free"])/sum(1 for x in items if tag in x["tags"])
    medage = pct([x["age"] for x in items if tag in x["tags"]], 50)
    am = a[1] if a else 0
    apm = ap[1] if ap else 0
    dm = d[1] if d else 0
    print(f"{tag:<22} {n:>4} {m or 0:>5}  {am or 0:>5} {apm or 0:>6} {dm or 0:>5}  {fr:>5.0f}% {medage or 0:>6.0f}")

print()
print("=== YOUNG-TOP25% TAG LIFT (age<=365d) ===")
y = wset(items, 365)
yl = sorted([x["likes"] for x in y])
thr = pct(yl, 75)
top = [x for x in y if x["likes"] >= thr]
bot = [x for x in y if x["likes"] < thr]
print(f"young n={len(y)}, top25% threshold={thr:.0f}, top n={len(top)}")
tagc = {}
for x in top:
    for t in x["tags"]: tagc.setdefault(t, [0,0]); tagc[t][0] += 1
for x in bot:
    for t in x["tags"]:
        tagc.setdefault(t, [0,0])[1] += 1
rows2 = []
for t, (c, b) in tagc.items():
    if c + b < 15: continue
    lift = (c/max(1,len(top))) / (b/max(1,len(bot))) if b else 99
    rows2.append((t, c, b, lift, c+b))
print(f"{'tag':<24} {'inTop':>5} {'inBot':>5} {'lift':>6} {'n':>5}")
for t, c, b, lift, n in sorted(rows2, key=lambda r: -r[3])[:25]:
    print(f"{t:<24} {c:>5} {b:>5} {lift:>6.2f} {n:>5}")
print("...")
for t, c, b, lift, n in sorted(rows2, key=lambda r: r[3])[:15]:
    print(f"{t:<24} {c:>5} {b:>5} {lift:>6.2f} {n:>5}")