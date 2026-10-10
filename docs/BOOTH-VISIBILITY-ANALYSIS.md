# Is the tag strategy the problem?

Analysed from `outputs/research/booth-live-collector/booth.db` — 4,958 crawled
items, 64,201 tag assignments, 31 of your own ranked items. Collected 2026-09-09,
so roughly two weeks stale.

**Short answer: no. Tags explain almost none of your visibility.** Your tag
profile is statistically indistinguishable from the items that outrank you, and
the strongest lever in the data is a category effect you cannot tag your way out
of.

---

## 1. The saturated-vs-no-motion question is a false choice

The `analysis_tag_lift` table computes, for each tag, how much more likely
top-ranked items are to use it than average (`lift`), and how common it is
overall (`overall_cov_pct`).

Your own tag profile against the top-ranked font items:

| | avg lift | avg coverage | tags per item |
|---|---:|---:|---:|
| **Your 31 items** | 1.92 | 13.8% | **25.6** |
| Top-ranked competitors | 1.96 | — | **9.5** |
| The 60 best in フォント・書体 | 1.96 | — | 9.5 |

Split by whether you use them:

| | n | avg lift | avg coverage |
|---|---:|---:|---:|
| Tags you **use** | 25 | **2.14** | 13.8% |
| Tags you **don't** | 20 | **3.22** | 5.1% |

So there *is* a gap — the tags you skip average 50% higher lift and are 2.7×
less saturated. But two things deflate the obvious reading:

**Most of those high-lift tags are free-giveaway words.** Of the 20 tags you
don't use, **10 are 無料/free tags** (`無料DL可` 3.88, `無料ダウンロード` 3.83,
`free font` 3.79, `無料フォント` 3.50…). They have high lift because free items
dominate and rank well. Putting them on a paid product would misrepresent the
item and attract buyers who will not pay. They are not available to you.

**The remaining 10 are legitimate but narrow:**

| tag | lift | coverage |
|---|---:|---:|
| `タイポグラフィー` | 3.83 | 2.9% |
| `書体 商用利用` | 3.65 | 3.0% |
| `font alphabet download` | 3.65 | 2.8% |
| `書体 商用` | 3.64 | 2.9% |
| `グラフィティ` | 3.62 | 2.8% |
| `フォント 商用利用 ダウンロード` | 3.16 | 4.7% |
| `書体ダウンロード` | 3.00 | 3.5% |
| `配信素材` | 2.64 | 3.9% |
| `フォント 日本語` | 2.47 | 5.8% |

Worth adding. Low-cost, maybe marginal.

One detail worth knowing: **`タイポグラフィー` (lift 3.83) is the long-vowel
variant of `タイポグラフィ` (lift 1.49)** — which you do use. A one-character
difference and 2.6× the lift. That is a real, cheap, testable change.

---

## 2. What actually correlates with likes

From `analysis_features`, across all 4,958 items:

| feature | Spearman vs likes |
|---|---:|
| `absolute_position` | −0.970 *(rank is defined by likes)* |
| `price_jpy` | **−0.288** |
| `item_image_count` | −0.202 |
| `desc_len` | +0.107 |
| **`tag_count`** | **+0.029** |

**Tag count has essentially zero relationship with engagement.** The top
2026-published item has **6,549 likes on 2 tags**. The second-highest has 3. One
of the best performers this year uses two.

That is the direct answer: adding tags, removing tags, or hunting better tags is
not the lever. You are already using 25.6 tags per item where the items that beat
you use 9.5.

---

## 3. The real constraint: category

I grouped items by what their title says they are:

| title contains | n | avg likes | **median likes** |
|---|---:|---:|---:|
| 明朝 (Japanese Mincho) | 99 | 1,097 | **177** |
| ゴシック (Japanese Gothic) | 150 | 493 | **166** |
| 英字 (English letters) | 17 | 216 | **11** |
| 欧文 (Latin / Western) | 48 | 175 | **7.5** |
| **your items** | **31** | **5.9** | **6.0** |

The top 30 items on BOOTH's font ranking are essentially all Japanese typefaces —
`手書き風フォント「からかぜ」` (20,054 likes), `装甲明朝` (15,474),
`フリーフォント源界明朝` (13,273), `零ゴシック` (11,117). Japanese-language fonts
sell to a Japanese marketplace with a **~20× larger font audience** than Latin
fonts do.

**You sell 欧文 (Latin) fonts.** Your median of 6 likes sits essentially on your
category's median of 7.5. You are not being suppressed, penalised, or
out-tagged. You are performing normally for your category, in a category whose
ceiling is roughly one-twentieth of the dominant one.

---

## 4. You are also structurally new

| | median publication year |
|---|---|
| Top 100 items | **2021** |
| Top 500 items | 2022 |
| **Your items** | **2026 (all 31)** |

BOOTH's `popular` sort ranks on **cumulative** likes. A 2026 item cannot outrank
a 2021 item that has accumulated 4,000 of them. Being new is a hard cap on
position, independent of anything you control.

Measured against your own cohort, you are mid-pack, not failing:

- your **best item (17 likes) would rank #137 of 546** among 2026 paid items —
  top 25%
- your **median (6 likes) ranks #260 of 546** — middle

Your rank of 2,541–4,871 is the all-time view; the cohort view says you are doing
roughly what a new paid Latin font does.

---

## 5. What the successful new items actually do

The 2026 items ranked inside the top 500:

| likes | price | tags | title |
|---:|---:|---:|---|
| 6,549 | ¥500 | **2** | 白光明朝（フリーフォント） |
| 5,038 | ¥1717 | 53 | 【9/9 23:59まで延長】17万人記念フォント無料配布パック |
| 1,995 | ¥0 | 8 | 【フリーフォント】あおぞらミルク（商用利用可） |
| 1,812 | ¥550 | **3** | フォント「Somnelia」 |
| 1,731 | ¥500 | **2** | 侵食明朝（フリーフォント） |
| 1,595 | ¥550 | 7 | おとぎの明朝【無料版あり】 |
| 1,488 | ¥880 | 67 | 【商用可/無料版有】手書きフォント「瞬風 shunpu」 |
| 1,442 | ¥500 | **2** | 黒華明朝（フリーフォント） |

Three patterns, none of them about tag craft:

1. **¥500 is the dominant price point.** Many sit exactly there.
2. **A free version is the standard funnel** — `【無料版あり】`, `【商用可/無料版有】`,
   フリーフォント, 無料配布パック. The free edition is what accumulates likes and
   drags the paid edition into view.
3. **Japanese typefaces**, confirming §3.

Against the whole market, the top 25% by likes has a **median price of ¥100**;
the bottom 25% has **¥980**. Your ¥250–1,399 sits in the low-engagement band.

But careful — within *your* own items, price correlates **+0.25** with likes: your
higher-priced items are your better-performing ones (FineLetter at ¥1,000 is your
best). The market-level negative correlation is a free/cheap skew, not a signal
that you should cut prices. For your catalogue specifically, price is not your
problem either.

---

## 6. So what is actually wrong

Ranked by evidence:

| Factor | Evidence | Can you act on it? |
|---|---|---|
| **Category ceiling** | 欧文 median 7.5 likes vs 明朝 177 | Only by changing what you sell |
| **Cumulative rank + newness** | top 100 median year 2021; you are all 2026 | Time, and a like-accumulating funnel |
| **No free funnel** | the winners all run one | **Yes — the clearest action** |
| **Engagement at volume** | your best is 17; top 500 median is 1,054 | Follows from the above |
| **Tag craft** | Spearman **+0.029** | Effectively no |

The honest conclusion: **you are not going for tags that are too saturated, and
the alternatives are not dead tags.** Your tags are fine. You are a new Latin-font
seller in a marketplace whose font audience buys Japanese typefaces, ranked by a
cumulative score you start at zero on.

---

## 7. What I would do, in order

1. **Stop spending effort on tag optimisation.** The data says it explains ~0 of
   your visibility. Add the ten legitimate high-lift tags from §1 — cheap, may
   help marginally — then move on.
2. **Test the free-version funnel.** Every high-performing 2026 item runs one.
   A free cut-down edition (or a free single weight) is the mechanism that
   accumulates the likes which drive the ranking. This is the one lever in the
   data that a new seller can actually pull.
3. **Move the price toward the market's engagement band** where the product allows
   — ¥500 is where the winners sit. Test on one product, not the catalogue.
4. **Decide about the category.** The 欧文 audience is ~20× smaller than the
   明朝/ゴシック audience. That is a product-strategy decision, not a listing
   decision. Either accept the niche (and stop measuring yourself against
   Japanese typefaces) or add Japanese typefaces.
5. **Re-measure before believing any of this.** The DB is 2026-09-09, and the
   correlation is not causation.

---

## 8. Caveats on the data itself

- **Two weeks stale** (collected 2026-09-09).
- **`analysis_pm_missing_tags` is misnamed or inverted.** All 594 of its rows have
  `pm_items_using > 0`, so it lists tags you *already use*, not ones you are
  missing. It cannot answer the gap question — the gap analysis in §1 was
  computed from `analysis_tag_lift` instead.
- **Price is unreliable in `papermoon_rank`** — it shows `price=0` for Braewick
  and WallJam, which are listed as paid. Cross-check against `items.price_jpy`.
- **`lift` is correlational.** High-lift tags are used disproportionately by
  top-ranked items; that does not establish that the tag causes the rank. Tags
  that long-established shops habitually use will inherit their lift.
- **Only 45 tags have lift computed**, so your 416 tags outside that set (and the
  competitors' 211) are not represented.

---

# Addendum: three follow-up questions

## A. Are there *lower-lift* tags that are still relevant, get traffic, and you miss?

Yes — and this is the most actionable thing in the whole analysis. I recomputed
per-tag statistics from the raw `item_tags` join over **all 494 tags** you never
use, then filtered out free-giveaway words and Japanese-script-only tags
(`和文`, `明朝`, `ゴシック`, `日本語`) that a Latin-font seller cannot honestly use.

What survives:

| tag | items using it | median likes | max likes | your status |
|---|---:|---:|---:|---|
| `書体 商用利用` | 151 | **398** | 11,905 | **you ship a 商用利用 variant and don't tag it** |
| `書体 商用` | 145 | **403** | 15,474 | missing |
| `書体 商用利用 ダウンロード` | 124 | **415** | 9,521 | missing |
| `書体ダウンロード` | 172 | **358** | 9,521 | missing |
| `書体商用` | 126 | **412** | 9,521 | missing |
| `書体 英語` | 135 | **405** | 9,521 | missing — you sell 欧文/英字 |
| `書体 ダウンロード` | 129 | **415** | 9,521 | missing |
| `フォント 商用利用 ダウンロード` | 233 | 352 | 9,949 | missing |
| `タイポグラフィー` | 143 | 405 | — | long-vowel variant of one you use |
| `y2k` | 126 | **421** | 9,521 | missing |
| `Graffiti` (Latin) | 123 | **416** | 9,521 | missing — you have WallJam |
| `グラフィティ` | 139 | 394 | 9,521 | missing |
| `配信素材` | 194 | 322 | 9,521 | missing |
| `商用利用可能素材` | 23 | 423 | 3,036 | missing |

These are **moderate-lift but high-coverage** — exactly the profile you asked
about. They do not appear in the 45-tag `analysis_tag_lift` table, which is why
the earlier pass missed them.

**The standout: the `書体 商用利用` / `書体 ○○ ダウンロード` family.** Your own
products carry variants literally named `商用利用版 | Commercial Use`
(18 of your items), and you are not using the tag that says so. That is a direct,
verified mismatch between what you sell and what you tag — not a theory.

**Correction worth recording:** `バリアブルフォント` (variable font) has the
*highest* median of anything I found — **491 likes** — but it is **not usable by
you**. I checked your `variants_json`: 18 items are `single`, the rest are
commercial/personal splits. You do not ship variable fonts, so that tag would be
a false claim. Same for `和文フォント` (528 median), `和文` (471) — Japanese-script
fonts only.

## B. Can we get BOOTH's actual user search / typed-query data?

**Not publicly, and not reliably by scraping.** What I actually tested:

| endpoint | result |
|---|---|
| `booth.pm/ja/items?tags[]=<tag>` | **200 — works**, returns an item count |
| `booth.pm/ja/search/suggest?q=…` | Cloudflare challenge ("Just a moment…") |
| `booth.pm/ja/browse/<cat>` | Cloudflare challenge |
| `booth.pm/ja/trending_tags` | 404 — does not exist |
| `api.booth.pm/api/v2/items` | 404 — no public API |

**BOOTH does not publish search volume**, and there is no query-log endpoint.
Inferring typed queries from the site is guesswork.

**But one real thing works, and it matters.** `booth.pm/ja/items?tags[]=<tag>`
returns a **supply count** — e.g. `書体` → *"1,279点"*. That is the number of
items competing for a tag. Pair supply with the likes you already have and you get
what you were actually asking for: **traffic proxy ÷ competition**. A tag with
1,279 competing items is not a discovery channel; a tag with 23 items
(`商用利用可能素材`, median 423 likes) is.

Two better sources of true typed-query data, both real:

1. **Your own BOOTH seller dashboard** (`accounts.booth.pm`) — as the shop owner
   you can see your items' views and impressions. That is your actual funnel.
2. **Google Search Console** for your shop/product pages — this is *literally*
   user-typed query data ("booth 欧文フォント", "graffiti font 商用利用"). If any
   of your traffic arrives via Google, GSC hands you the exact queries. Neither
   of these needs scraping and both are free.

## C. If a font gets no likes in the first few days, is it gone?

**No. Not remotely.** Measured across all 4,958 items:

Average likes by publication year — likes accrue monotonically with age:

| published | n | avg likes | median |
|---|---:|---:|---:|
| 2015 | 21 | 949 | 532 |
| 2018 | 367 | 235 | 11 |
| 2021 | 387 | 403 | 42 |
| 2024 | 741 | 173 | 14 |
| 2025 | 902 | 120 | 14 |
| **2026** | **718** | **80** | **6** |

The decisive test — **items published Jul–Sep 2026**, i.e. your exact cohort
(n=278):

| likes | count | share |
|---|---:|---:|
| **0** | 55 | **19.8%** |
| 1–9 | 160 | 57.6% |
| 10–99 | 43 | 15.5% |
| 100–999 | 17 | 6.1% |
| **1000+** | 3 | **1.1%** |

p50 = 3, p75 = 9, p90 = 63, **max 5,038**.

Three things fall out of that:

1. **A third of all young items sit under 10 likes** (19.8% at exactly zero). You
   are not an outlier for having 0–6 early.
2. **The spread within one cohort is 0 → 5,038.** Same age, wildly different
   outcomes. Early likes are therefore *not* destiny — some items that ended up
   with thousands started in the same week as items that got zero.
3. The September 2026 slice is **38% zero-likes with a median of 2** — that is
   just recency, not failure. Compare January 2026: 4% zero, median 11. Same
   quality of listings, more time.

**So: not gg.** Early silence is the normal state and the ranking is cumulative.
The practical consequence is the opposite of what you feared — an item with zero
likes still has full upside, which is exactly why the free-version funnel in §7
matters: it is the mechanism that starts the accumulator.
