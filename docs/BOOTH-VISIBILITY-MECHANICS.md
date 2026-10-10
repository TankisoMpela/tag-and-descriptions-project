# What determines visibility on BOOTH

Measured from `booth.db` (4,958 items, 4,956 with likes and a publication date).

---

## The short answer

**Visibility is cumulative likes.** From `analysis_features`:

| feature | Spearman vs likes |
|---|---:|
| **`absolute_position`** | **−0.970** |

Rank and likes are the same variable for practical purposes. BOOTH's popular sort
does not have a hidden quality score that likes merely correlate with — position
is essentially *defined* by the like count.

Everything else is therefore a question about **what accumulates likes**. Four
things do, in this order of magnitude.

---

## 1. Free vs paid — the largest single factor

| catalogue | n | avg likes | **median likes** | max |
|---|---:|---:|---:|---:|
| **FREE** | 1,217 | 513.7 | **109** | 20,054 |
| **PAID** | 3,739 | 146.8 | **11** | 10,358 |

**Free items accumulate ~10× the median likes.** And **43% of the top 300 is
free** (129/300).

This is the mechanism, not a tactic. A "like" is a low-commitment action with no
purchase barrier, so a free item converts viewers to likes far more readily —
and likes *are* the ranking.

**The dominant shop's entire top catalogue is free:**

| likes | price | title |
|---:|---|---|
| 15,474 | FREE | 装甲明朝 |
| 13,273 | FREE | フリーフォント源界明朝 |
| 11,905 | FREE | 異世明・異世ゴ（フリーフォント） |
| 11,117 | FREE | 零ゴシック（フリーフォント） |
| 8,791 | FREE | どきどきファンタジア |

`flopdesign.booth.pm` holds **76 of the top 500** and its leaders are all free
downloads. That shop is not winning on tags, titles, or shop age. It is winning
by giving fonts away and letting the like count do the ranking.

---

## 2. Item age — the accumulation clock

| published | n | avg likes | median |
|---|---:|---:|---:|
| 2015 | 21 | 949 | 532 |
| 2018 | 367 | 235 | 11 |
| 2021 | 387 | 403 | 42 |
| 2024 | 741 | 173 | 14 |
| 2025 | 902 | 120 | 14 |
| **2026** | 718 | **80** | **6** |

Monotonic. A 2015 item has had a decade to accumulate; a 2026 item has had
months. **Ranking is cumulative and never resets, so a new item starts at zero
against items that are not competing on equal terms.**

---

## 3. Shop reputation — real but secondary

Same-age test, isolating item age from shop age. Items published 2025–26:

| | n | avg likes | median | max |
|---|---:|---:|---:|---:|
| from **established** shops | 550 | **145.4** | **13** | 5,038 |
| from **new** shops | 1,070 | 80.0 | 8 | **6,549** |

Established shops get roughly **1.8× the average** and **1.6× the median**. That
is a follower-base advantage — an existing audience sees the item on release.

**But shop age is not a gate.** The single highest-likes new item (6,549) came
from a **new** shop, beating the established-shop maximum (5,038). New sellers
can break out.

---

## 4. Concentration is high

- **179 shops** share the top 500
- the **top 10 hold 39%** (194/500)
- the top shop alone holds **15%**

Not a free-for-all, but not closed either.

---

## What does *not* drive it

| factor | Spearman vs likes |
|---|---:|
| `tag_count` | **+0.029** |
| `desc_len` | +0.107 |
| `price_jpy` | −0.288 |
| `item_image_count` | −0.202 |

Tags are irrelevant to accumulation. Price is the strongest of the weak signals
and it is **negative** — cheaper items get more likes, which is the same
free-is-better effect seen in §1.

---

## What this means for a paid-only shop

A paid catalogue is competing in a system whose ranking function rewards the
exact thing it withholds. That is the whole story behind "my fonts are falling
into obscurity":

- Rank = cumulative likes (§ short answer)
- Likes ≈ 10× easier to get when free (§1)
- Rank never resets, so a 2026 catalogue is permanently behind (§2)
- Shop reputation helps, but only ~1.8×, and it can be beaten (§3)

**This is why the free-version funnel is the highest-leverage move available.**
It is not a promotion strategy — with rank defined by likes, a free edition is
the only mechanism that starts the accumulator.

That is a business decision, not a technical one, and it trades directly against
`CAMPAIGN_MODE: NORMAL_PAID`. The data does not say the shop *must* change; it
says that under the current campaign mode the ceiling is structural, and tag,
title and description work cannot lift it.

---

## Caveats

- **Correlational.** Free items may attract likes for reasons other than price —
  free items are also more likely to be simpler novelty fonts, and to be posted
  by shops whose audience is built for free distribution.
- **The census is the popular sort** (4,958 items down to page ~83). It does not
  include items that never surfaced, so shop-age effects among invisible items
  are not measured.
- **Likes ≠ sales.** A free download and a ¥1,000 licence are not the same
  outcome. The data supports "free ranks higher", not "free earns more".
- One snapshot, 2026-09-08. No account of BOOTH's own editorial features,
  seasonal events, or external traffic.

---

# Addendum: free campaigns, timing, and a correction

## Correction first — my age curve was contaminated by survivorship

The §2 table (median likes falling from 532 in 2015 to 6 in 2026) is **not** a
clean accrual curve. **The census is the popular sort.** An item only appears in
it if it surfaced, so older cohorts are filtered to winners while recent cohorts
still contain everything, including items that never went anywhere. That biases
old years upward and makes the decline look steeper and more mechanical than it
is.

The month-level data shows the truth. Free items, median likes by month:

| month | median | n |
|---|---:|---:|
| 2024-04 | **25** | 21 |
| 2024-11 | **94** | 11 |
| 2025-05 | **8** | 18 |
| 2025-12 | **517** | 12 |
| 2026-04 | **66** | 19 |
| 2026-08 | **3** | 55 |
| 2026-09 | **2** | 23 |

**No ramp.** 2024-04 (25) sits *below* 2026-04 (66). 2025-12 hits 517 while
2025-05 sits at 8. Month-to-month variation is dominated by **individual hits**,
not by systematic accrual. There is no "wait N months and it grows" curve in
this data.

## Question 1 & 3: how long until a free campaign does something?

There is no reliable waiting period, and the honest measure is a **probability**,
not a duration.

For items published since 2025-09 (~12 months old or newer):

| | n | 0 likes | ≥10 | **≥100** | median |
|---|---:|---:|---:|---:|---:|
| **FREE** | 236 | **6%** | 56% | **20%** | 12 |
| **PAID** | 738 | 12% | 43% | **10%** | 7 |

Read that carefully:

- Free **roughly doubles** the odds of reaching 100+ likes (**20% vs 10%**)
- Free **halves** the odds of a total flop (**6% vs 12%** at zero)
- **80% of free items never reach 100 likes**, even a year in

So a free campaign measurably improves the distribution, but **it does not
reliably "go off."** Four out of five free fonts stay modest. The ones that
break out do so because of something the listing does not control — the
distribution is hit-driven, and the top shops' catalogues are dominated by three
to five viral free fonts, not by broad success across everything they post.

**What that means practically:** a free campaign is a *portfolio* bet. You are
buying a ~2× improvement in the odds per item. One free font is more likely than
one paid font to do something, and far more likely than one paid font to do
nothing — but it is still more likely than not to stay under 100 likes.

## Question 2: does engagement help store health?

**Yes, measurably, but modestly.** Isolating item age (items published 2025–26):

| | n | avg likes | median |
|---|---:|---:|---:|
| new items from **established** shops | 550 | **145.4** | **13** |
| new items from **new** shops | 1,070 | 80.0 | 8 |

An established shop's new item gets roughly **1.8× the average** and **1.6× the
median**. That is the store-health effect: an accumulated audience sees a new
release on day one.

Two limits on it:

1. **It is a multiplier, not a floor.** 1.8× on a base of ~80 likes is a lift,
   not a guarantee of visibility.
2. **It is beatable.** The highest-likes new item in the whole census (6,549)
   came from a **new** shop.

So yes — engagement compounds into future items. But it compounds *within* the
free-is-better regime, not instead of it.

## What I cannot answer from this data

- **Accrual rate over time.** One snapshot cannot measure how fast an individual
  item accumulates. A 48-hour re-crawl of a handful of known items would settle
  it, and it is cheap to run.
- **The shape of a breakout.** Whether a hit accumulates in week one or year two
  is unknown here.
- **Sales.** Likes are not revenue, and a free download is not a ¥1,000 licence.
  Nothing in this file says free *earns* more.

---

# Addendum 2: would a free campaign leave money on the table?

**Not if it is freemium. Yes if it is literally free — and nobody successful does
the second one.**

## The top free-font shops all sell paid items

| shop | free items | paid items | paid median price | paid max likes |
|---|---:|---:|---:|---:|
| `flopdesign` | 31 | **76** | ¥500 | 10,358 |
| `typingart` | 12 | **9** | **¥1,200** | 5,498 |
| `ymnk-design` | 10 | **14** | **¥5,000** | 3,123 |
| `yutaone` | **0** | **122** | **¥30,000** | 9,521 |

Even `flopdesign` — whose *top* items are all free downloads, and which holds 76
of the top 500 — has **76 paid listings**. The free catalogue is the shop's
visibility engine; the paid catalogue is the business.

And `yutaone` proves the other direction too: **zero free items, 122 paid, at a
median of ¥30,000**, with a max of 9,521 likes. Paid-only is viable.

## The freemium pattern is everywhere

**66 base product names** in the census have **both** a free and a paid item:

| free item | | paid item | |
|---|---:|---|---:|
| `ぱんきじ かな フォント（FREE版）` | 1,805 likes | `ぱんきじ かな フォント（商用利用版）` ¥500 | 310 likes |
| `g_コミックホラー恐怖(R)-教漢版` | 733 likes | `g_コミックホラー恐怖(R)-有料版` ¥3,600 | 622 likes |
| `藍原サインペン（フリー版）` | 572 likes | `藍原サインペン（シェア版）` ¥3,600 | 117 likes |
| `【商用可・無料フォント お試し版】デイリー・レイジー` | 234 likes | `【商用可・縦書き対応】デイリー・レイジー` ¥100 | 75 likes |

The shape is consistent: **the free edition carries the likes, the paid edition
carries the money.** The free item is a customer-acquisition cost that buys rank,
not a giveaway.

## So what would actually be "money on the table"

| approach | ranks? | earns? | leaves money on the table? |
|---|---|---|---|
| **Whole font free** | yes | **¥0 on that product** | **yes** — and no top shop does this |
| **Free cut-down + paid full** | yes (via the free item) | yes | **no** — this is the standard model |
| **Paid only, current prices** | poorly (median 7–11 likes, rank ~3,500/5,000) | yes, if anyone finds it | **it is the invisible catalogue that is the problem** |
| **Paid only, high price** | viable (`yutaone`, ¥30,000 median) | yes | not applicable |

**The real tension is rank vs margin, not free vs paid.** Likes favour cheap and
free (`price_jpy` vs likes is **−0.288**), while revenue favours expensive. The
shops that win are the ones that split the two: a free or cheap edition for rank,
a high-priced edition for margin. `typingart` runs free items beside a **¥1,200**
median; `yutaone` runs no free items at **¥30,000**.

Your catalogue is priced at **¥250–1,399** — below `typingart`'s median and two
orders below `yutaone`'s. So the question worth asking may be less "should I go
free" and more **"am I priced to capture margin, and separately, is anything
built to accumulate rank?"** Those want two different products, not one
compromise.

## What is still unmeasurable here

**Conversion.** Likes are not revenue, and the census contains no sales data at
all. Nothing above shows that a free download leads to a paid purchase — only
that the shops which win run both.

**GA4 now settles it.** BOOTH's integration supports **enhanced ecommerce**, so
once the property is collecting, the funnel is measurable end to end: free item
views → paid item views → purchases. That is the only way to know whether the
free edition is a cost or an investment, and it is already switched on.

---

# Addendum 3: the commercial/personal split, and a price correction

## These are two different things — do not conflate them

| pattern | evidence | verdict |
|---|---|---|
| **Free version + paid version** | **66 base-name pairs**; `flopdesign` runs 31 free beside 76 paid | **evidenced** — the standard winner model |
| **Personal variant + commercial variant** | **74 of 4,956 items (1.5%)**; no top shop uses it | **not evidenced** |

Everything I said was worth it refers to the **first** row. The second is a
different practice and the data does not support it.

## The split is rare, and the winners do not use it

Variant names on the six largest shops by top-500 presence:

| shop | variant names found |
|---|---|
| `flopdesign` | `single` ×104, `フリー版` ×1, `投げ銭版` ×1 |
| `yutaone` | `single` ×114, `通常価格` ×4, `BOOST` ×3 |
| `amaridesign` | `single` ×109, `投げ銭版` ×7, `無料版` ×5 |
| `typingart` | `single` ×21 |
| `ymnk-design` | `single` ×24 |
| `satsuyako` | `収録文字の見本(pdf)` ×10, `single` ×7 |

**Every one sells `single`.** Not one splits personal from commercial.

## And they do not even mention commercial use

Counting items whose title or variants mention commercial or personal rights:

| shop | items | mentions commercial | mentions personal |
|---|---:|---:|---:|
| `amaridesign` | 128 | **0** | 0 |
| `yutaone` | 122 | **0** | 0 |
| `ymnk-design` | 24 | **0** | 0 |
| `satsuyako` | 24 | **0** | 0 |
| `typingart` | 21 | **0** | 0 |
| `flopdesign` | 107 | 1 *(a ¥24,800 complete set)* | 0 |

The likely reason: in this market **commercial use is the default in the
licence**, so there is no separate tier to sell. The commercial/personal split
appears to be a convention of overseas-facing sellers, not of the shops that
actually win the ranking. That is an inference about *why*, not a measurement.

## Correction: price barely affects likes among paid items

I said the tension was "rank vs margin" because `price_jpy` vs likes is −0.288.
That coefficient is driven by **free items at price 0**. Within paid items:

| price band | n | **median likes** |
|---|---:|---:|
| ¥1–499 | 815 | 12.0 |
| ¥500–999 | 899 | 13.0 |
| ¥1,000–2,999 | 1,285 | 9.0 |
| ¥3,000–9,999 | 359 | 10.0 |
| ¥10,000+ | 381 | **16.0** |

**Flat, 9–16 across every band** — and the ¥10,000+ band has the *highest* median.
Among paid items, **raising price does not cost you likes.** My "rank vs margin"
framing was wrong for paid catalogues; it only applies to the free-vs-paid
decision.

## What the data says about conversion: nothing

**The census contains no sales data of any kind.** Not units, not revenue, not
buyer counts. It has likes and rank.

So on the question that matters — *does a commercial/personal split convert
better than a single price?* — **this data is silent, and I will not infer an
answer from it.** Likes are not purchases. An item with 300 likes and zero sales
and an item with 30 likes and ten sales look identical in every table above.

Two things follow:

1. **Anything I said about "worth it" is about rank and likes, not money.**
   Free ranks higher — that is measured. Whether it *earns* more is not.
2. **GA4 with enhanced ecommerce answers it.** Once the property has a few weeks
   of data: item views, add-to-cart and purchases per item, split by variant.
   That is the only instrument that separates conversion from popularity, and it
   is already collecting.
