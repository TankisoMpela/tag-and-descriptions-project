# BOOTH Font Tag Bank

Status: FROZEN SNAPSHOT — pre-FontFairy catalog expansion, amended 2026-09-22  
Snapshot captured and locked: 2026-09-06  
Amendment 2026-09-22: rows 29–41 added (see "Amendment 2026-09-22" below)  
Owner: BOOTH font listing workflow (Agent 20)

## Purpose

This is the one permanent candidate and evidence bank for paid font listings
on BOOTH. It is intended to stop every run from rediscovering the same small
group of tags and to preserve this pre-expansion activity baseline.
The bank covers Japanese discovery language, Western/Latin font language,
style families, use cases, and purchase/licensing language.

It is not a search-volume report. BOOTH's exact-tag result count and the
`フォント・書体` category count are catalog-coverage/activity signals only.
They do not mean searches, sales, likes, or demand. The recorded values are
historical snapshots and must not be refreshed during ordinary listing runs.
A tag remains subject to the supplied product's fit and rights facts before
selection.

## How Agent 20 should use this bank

1. Read this bank after the persistent BOOTH ledger and strategy file.
2. Start candidate selection from the ordered rows and categorized inventory
   below. This file is the sole permanent activity/tag baseline.
3. Do not re-query, refresh, append to, or replace this bank during an ordinary
   listing run, even when its 2026-09-06 evidence is older than 45 days or
   FontFairy has added products since the snapshot.
4. Preserve the owned-product exclusion and low-activity rules. This bank is a
   candidate source, not a selected-tag target: the selected set is governed by
   `bin/validate_booth_listing.py` (18-25, target 25). Earlier revisions of this
   rule named a "48-candidate bound" and a "40 strongest-candidate target",
   which no longer existed in the validator and contradicted it.
5. The per-product scratch record and persistent rejected-term ledger are
   operational records only; neither is a competing tag bank and neither may
   mutate this snapshot.
6. Never select a rights, format, language-coverage, or use-case term unless
   the supplied product facts support it. A high-coverage tag is not a reason
   to invent a product claim.

## Description keyword layer

Yes: this same frozen bank is also a controlled vocabulary source for the BOOTH
title and description. It does **not** measure description search volume. The
route counts, activity labels, seller repetition, and item-engagement values
only tell the agent that a phrase was observed on BOOTH and how much relevant
catalog coverage was visible in the frozen capture. They must not be presented
as proof that a phrase is searched more often in description text.

Use the bank in two separate passes:

1. **Tag pass:** promote only a bank row with usable exact/category evidence,
   product fit, and any required rights/format/coverage facts into the selected
   tag set.
2. **Description pass:** choose a small natural cluster from the bank's
   identity, style/construction, use-case, and conditional rights/format
   vocabulary. A phrase may be useful in prose even when it is not a confirmed
   native BOOTH tag; label it `keyword phrase - tag not confirmed` in the SEO
   map and never count it toward the selected-tag target.

Description-wording priority is:

1. the supplied product facts and exact final name;
2. banked BOOTH wording that matches the product and recurs on relevant paid
   seller pages;
3. banked keyword-only wording that is natural, specific, and factual;
4. outside wording only when it is supported by the supplied facts, clearly
   marked as unconfirmed, and useful to a buyer.

For the paste-ready description, use one primary identity/style phrase and one
concrete use-case phrase in the first one or two sentences. Add two to four
supporting phrases in the natural product explanation, then put coverage,
formats, compatibility, and rights in factual Japanese sections. Use rights,
format, web-font, and language-coverage phrases only when the supplied facts
support them. Do not paste the 40 tags into the body, repeat near-synonyms in a
single sentence, or use a banked paid/free phrase to change the offer's actual
license.

The scratch/output map should audit the final copy with this schema:

`phrase | role (primary/supporting/keyword-only) | bank family | source/evidence | confirmed BOOTH tag? | description location | factual fit`

This makes the bank useful for both discovery fields and conversion copy while
keeping tag evidence, description vocabulary, and buyer-demand claims separate.

## Evidence and activity rules

| Tier | Meaning |
|---|---|
| A | Exact tag route and `フォント・書体` route recorded, with clear paid-font evidence and fit. |
| B | Exact/category coverage recorded and useful fit, but paid count or seller diversity is only a visible lower bound. |
| C | Live route or local listing evidence exists, but coverage is low, mixed, stale, or needs product-specific confirmation. |
| D | Wording candidate only; no usable live category evidence yet. |

| Activity | Font-category result |
|---|---|
| High | 100+ items |
| Basic/medium | 17–99 items |
| Low | 1–16 items |
| Dead/no coverage | 0 items or route failure with no usable result |

All counts below were captured on 2026-09-06 and are frozen. `≥` means visible
lower bound, not a total. These values are not to be recalculated from future
BOOTH routes during ordinary listing runs.
The standard exact route is:

`https://booth.pm/ja/items?tags%5B%5D={URL-encoded-tag}`

The category route is:

`https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?tags%5B%5D={URL-encoded-tag}`

## Ordered priority bank

The order balances product fit, font-category coverage, and useful Japanese /
English discovery language. Do not treat order as demand or sales ranking.

| Rank | Tag | Family | Language | Overall | Font category | Activity | Evidence | Fit / selection rule | Exact route |
|---:|---|---|---|---:|---:|---|---|---|---|
| 1 | フォント | object | JP | 3,400 | 3,093 | high | A | Core product term; use for every font | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 2 | font | object | EN | 1,648 | 1,617 | high | A | English/Latin discovery term | [route](https://booth.pm/ja/items?tags%5B%5D=font) |
| 3 | オリジナルフォント | object | JP | 1,085 | 1,078 | high | B | Use when the font is original work | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%AA%E3%83%AA%E3%82%B8%E3%83%8A%E3%83%AB%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 4 | タイポグラフィ | design | JP | 1,268 | 638 | high | B | OUTRANKED by タイポグラフィー (row 35). This form wins 3.9%, below the 5% floor; the long-vowel variant wins 22.2%. Prefer row 35 | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BF%E3%82%A4%E3%83%9D%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3) |
| 5 | ロゴ | use case | JP | 6,604 | 352 | high | B | Only when logo use is plausible | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%AD%E3%82%B4) |
| 6 | ロゴデザイン | use case | JP | 1,071 | 159 | high | B | Stronger design-specific logo phrase | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%AD%E3%82%B4%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3) |
| 7 | 欧文フォント | Western/Latin | JP | 146 | 144 | high | A | English/Latin glyph product | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%AC%A7%E6%96%87%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 8 | 欧文書体 | Western/Latin | JP | 30 | 29 | basic | B | Latin typeface positioning | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%AC%A7%E6%96%87%E6%9B%B8%E4%BD%93) |
| 9 | 英語フォント | Western/Latin | JP | 115 | 111 | high | B | Use for an English/Latin font | [route](https://booth.pm/ja/items?tags%5B%5D=%E8%8B%B1%E8%AA%9E%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 10 | 英字フォント | Western/Latin | JP | 33 | 32 | basic | B | Alphabet/Latin positioning | [route](https://booth.pm/ja/items?tags%5B%5D=%E8%8B%B1%E5%AD%97%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 11 | display font | style | EN | 30 | 29 | basic | B | Western display font equivalent | [route](https://booth.pm/ja/items?tags%5B%5D=display%20font) |
| 12 | ディスプレイフォント | style | JP | 25 | 24 | basic | B | Prominent headline/display construction | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 13 | デザインフォント | style | JP | 313 | 313 | high | B | Designed/display treatment | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 14 | 装飾フォント | style | JP | 22 | 22 | basic | B | Decorative construction is factual | [route](https://booth.pm/ja/items?tags%5B%5D=%E8%A3%85%E9%A3%BE%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 15 | font design | design | EN | 187 | 186 | high | B | English design discovery phrase | [route](https://booth.pm/ja/items?tags%5B%5D=font%20design) |
| 16 | フォント デザイン | design | JP | 295 | 293 | high | B | Japanese design phrase | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%20%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3) |
| 17 | グラフィックデザイン | use case | JP | 649 | 89 | basic | B | Graphics-led presentation | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%83%E3%82%AF%E3%83%87%E3%82%B6%E3%82%A4%E3%83%B3) |
| 18 | 見出し | use case | JP | 372 | 88 | basic | B | Headline/display use | [route](https://booth.pm/ja/items?tags%5B%5D=%E8%A6%8B%E5%87%BA%E3%81%97) |
| 19 | フォント ダウンロード | intent | JP | 265 | 262 | high | B | Paid download product; not a free claim | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%20%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89) |
| 20 | font download | intent | EN | 167 | 166 | high | B | English paid-download wording | [route](https://booth.pm/ja/items?tags%5B%5D=font%20download) |
| 21 | fonts | object | EN | 290 | 282 | high | B | English plural term | [route](https://booth.pm/ja/items?tags%5B%5D=fonts) |
| 22 | フォント 英語 | language | JP | 354 | 352 | high | B | English-language font discovery | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%20%E8%8B%B1%E8%AA%9E) |
| 23 | title | use case | EN | 63 | 33 | basic | C | English title use; avoid if too broad | [route](https://booth.pm/ja/items?tags%5B%5D=title) |
| 24 | クリーン | style | JP | 68 | 41 | basic | B | Clean construction is supported | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3) |
| 25 | モダン | style | JP | 776 | 17 | basic | B | Modern style only when visibly supported | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%A2%E3%83%80%E3%83%B3) |
| 26 | ブランディング | use case | JP | 38 | 9 | low | C | Useful exception for branding-focused fonts | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%96%E3%83%A9%E3%83%B3%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0) |
| 27 | 太字 | style | JP | 13 | 13 | low | C | Only for demonstrably bold fonts | [route](https://booth.pm/ja/items?tags%5B%5D=%E5%A4%AA%E5%AD%97) |
| 28 | 多言語フォント | language | JP | 1 | 1 | low | C | Only when supplied language facts support it | [route](https://booth.pm/ja/items?tags%5B%5D=%E5%A4%9A%E8%A8%80%E8%AA%9E%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 29 | 書体 商用利用 | licensing | JP | 155 | 151 | high | B | Paid commercial-use typeface wording; use when the product carries a commercial licence | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%20%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8) |
| 30 | 書体 商用 | licensing | JP | 146 | 145 | high | B | Short commercial-use typeface form; pair with `書体 商用利用`, not instead of it | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%20%E5%95%86%E7%94%A8) |
| 31 | 書体ダウンロード | intent | JP | 174 | 172 | high | B | Paid typeface download intent; not a free claim | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89) |
| 32 | 書体 商用利用 ダウンロード | intent | JP | 124 | 124 | high | B | Commercial-use plus download intent; strongest of the `書体` intent cluster | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%20%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8%20%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89) |
| 33 | 書体商用 | licensing | JP | 125 | 126 | high | B | No-space commercial typeface form; distinct BOOTH tag from the spaced variants | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%E5%95%86%E7%94%A8) |
| 34 | 書体 英語 | language | JP | 135 | 135 | high | B | Latin/English typeface positioning; applies to any Western font product | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%9B%B8%E4%BD%93%20%E8%8B%B1%E8%AA%9E) |
| 35 | タイポグラフィー | design | JP | 290 | 143 | high | B | Long-vowel variant of `タイポグラフィ`; a distinct BOOTH tag, not a duplicate | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BF%E3%82%A4%E3%83%9D%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%BC) |
| 36 | y2k | style | EN | 672 | 126 | high | B | Y2K styling; only when the letterforms visibly support it | [route](https://booth.pm/ja/items?tags%5B%5D=y2k) |
| 37 | Graffiti | style | EN | 158 | 123 | high | B | Latin graffiti wording; use for spray/tag/street letterforms | [route](https://booth.pm/ja/items?tags%5B%5D=Graffiti) |
| 38 | グラフィティ | style | JP | 460 | 139 | high | B | Japanese graffiti wording; the JP-language counterpart of `Graffiti` | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%86%E3%82%A3) |
| 39 | 商用利用可能素材 | licensing | JP | 1,145 | 23 | high | B | Commercial-use material phrasing; low competition against the saturated `商用利用可` | [route](https://booth.pm/ja/items?tags%5B%5D=%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8%E5%8F%AF%E8%83%BD%E7%B4%A0%E6%9D%90) |
| 40 | フォント 商用利用 ダウンロード | intent | JP | 233 | 233 | high | B | Commercial-use font download; the `フォント` counterpart of the `書体` intent cluster | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%20%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8%20%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89) |
| 41 | 配信素材 | use case | JP |  | 194 | high | C | DO NOT SELECT - DEMOTED 2026-09-22. BOOTH-wide route is 33,600 and its top-300 win rate is 4.1%, below the 5% floor. It was added on its font-category count (194) alone, which was the wrong test; it is a generic non-font tag. Listed here only so it is not re-added. Keyword-only. | [route](https://booth.pm/ja/items?tags%5B%5D=%E9%85%8D%E4%BF%A1%E7%B4%A0%E6%9D%90) |
| 42 | serif | style | EN | 6 | 8 | high | B | Serif class. Low competition and high observed engagement; n=8 is thin, so treat as unproven but cheap | [route](https://booth.pm/ja/items?tags%5B%5D=serif) |
| 43 | セリフ体 | style | JP | 5 | 8 | high | B | Japanese serif-class term; the JP counterpart of `serif`. Same thin-n caveat | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BB%E3%83%AA%E3%83%95%E4%BD%93) |
| 44 | 欧文 | Western/Latin | JP | 57 | 62 | high | B | The plainest word for a Latin/Western font. Distinct BOOTH tag from `欧文フォント` and `欧文書体` | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%AC%A7%E6%96%87) |
| 45 | 英字 | Western/Latin | JP | 150 | 50 | high | B | Alphabet/Latin positioning. Distinct tag from `英字フォント` | [route](https://booth.pm/ja/items?tags%5B%5D=%E8%8B%B1%E5%AD%97) |
| 46 | セリフ | style | JP | 244 | 14 | high | B | Serif style term without the `体` suffix; a separate BOOTH tag from `セリフ体` | [route](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BB%E3%83%AA%E3%83%95) |
| 47 | 筆記体 | style | JP | 42 | 26 | high | B | Cursive/script letterforms only; use when the product is genuinely cursive | [route](https://booth.pm/ja/items?tags%5B%5D=%E7%AD%86%E8%A8%98%E4%BD%93) |
| 48 | 手書き風フォント | style | JP | 45 | 40 | high | B | Handwritten-look fonts only; `風` means the look, not a literal handwritten construction | [route](https://booth.pm/ja/items?tags%5B%5D=%E6%89%8B%E6%9B%B8%E3%81%8D%E9%A2%A8%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) |
| 49 | 商用利用可能 | licensing | JP | 4,044 | 161 | high | B | Commercial-use phrasing. Moderate BOOTH-wide saturation; prefer over `商用利用可`, which is 17,659 | [route](https://booth.pm/ja/items?tags%5B%5D=%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8%E5%8F%AF%E8%83%BD) |


## Amendment 2026-09-22 (b) — searched AND winning AND unbanked

Rows 42–49 come from cross-referencing the one-time Google autocomplete harvest
(`outputs/research/booth-demand/`) against the census. Only tags that are
**actually searched**, **present in the font category**, and **winning in the
top 300** were kept.

Route counts below are BOOTH-wide reads taken 2026-09-22; `font items` is the
census `フォント・書体` count; `win%` is the share of items using the tag that
place in the top 300.

| tag | route | font items | median likes | win% |
|---|---:|---:|---:|---:|
| `serif` | 6 | 8 | 407.5 | 37.5% |
| `セリフ体` | 5 | 8 | 407.5 | 37.5% |
| `筆記体` | 42 | 26 | 171.5 | 15.4% |
| `手書き風フォント` | 45 | 40 | 92.5 | 27.5% |
| `欧文` | 57 | 62 | 346.5 | 22.6% |
| `英字` | 150 | 50 | 237.5 | 24.0% |
| `セリフ` | 244 | 14 | 118.5 | 21.4% |
| `商用利用可能` | 4,044 | 161 | 53.0 | 16.8% |

**Why these were missing.** The bank carried `欧文フォント` and `欧文書体` but not
`欧文`; `英字フォント` but not `英字`; `タイポグラフィ` but not the plain forms. The
matching in the 2026-09-06 snapshot was thorough about compounds and thin on the
simplest words for what the shop actually sells.

**Two caveats, both recorded deliberately.**

1. **n is small.** `serif`'s 37.5% is three wins out of eight; at n=8 one item
   moves the rate by 12.5%. The median-likes figure corroborates it and sits
   well above the saturated vocabulary's 15–22, but the rate is suggestive, not
   settled.
2. **Low competition may mean no traffic.** `serif` (6 BOOTH-wide) and `セリフ体`
   (5) could be unclaimed space or a tag nobody browses. The route count cannot
   distinguish these. `欧文` and `英字` are the safer additions — real
   competition, real engagement. `serif`/`セリフ体` are cheap to try and
   unproven.

**Rejected despite decent win rates:** `おしゃれ` (route 6,734) and `商用可`
(route 9,434). Saturated and generic BOOTH-wide regardless of win rate.

**App terms are deliberately absent.** `photoshop` (91 items, median 34.0, zero
top-300 wins), `illustrator`, `イラレ`, `フォトショ`, `procreate` all have real
font-category presence and **no winners**, and `canva`, `アイビス`, `capcut`,
`filmora`, `figma`, `obs`, `vtuber`, `blender`, `unity`, `powerpoint` are not
BOOTH tags at all. They belong in the description, not in a tag slot.

**Do not refresh these counts mid-run.** As with the 2026-09-06 values, they are
the evidence for the addition. Re-read deliberately with
`python3 bin/booth_tag_route_count.py <tags>` or rebuild the corpus with
`python3 bin/harvest_booth_demand.py`.



## Amendment 2026-09-22 — low-saturation / high-yield cluster

Rows 29–41 were added after an empirical review of the BOOTH font market
(4,958 crawled items, 64,201 tag assignments). The finding was a consistent
split between the tags the bank already carried and a cluster it did not.

**Saturated vocabulary already banked** — high coverage, low observed engagement:

| tag | `フォント・書体` items | median likes |
|---|---:|---:|
| `フォント` | 3,092 | 17 |
| `font` | 1,620 | 15 |
| `商用利用可` | 1,334 | 16 |
| `書体` | 1,262 | 22 |
| `タイポグラフィ` | 640 | 54 |

**The missing cluster** — low coverage, several times the observed engagement:

| tag | `フォント・書体` items | median likes |
|---|---:|---:|
| `商用利用可能素材` | 23 | 423 |
| `書体 商用利用 ダウンロード` | 124 | 415 |
| `書体商用` | 126 | 412 |
| `書体 商用` | 145 | 403 |
| `書体 商用利用` | 151 | 398 |
| `書体ダウンロード` | 172 | 358 |
| `フォント 商用利用 ダウンロード` | 233 | 352 |

The pattern is not "add more tags" — every added row is a **narrow variant of a
term the bank already holds**, and the narrow form is where the engagement is.
The bank already carried `フォント ダウンロード` (265 items, median 346); it did
not carry its three siblings, all of which show the same profile.

**Two limits on this evidence, and both matter:**

1. **It is correlational.** Items using narrow commercial/download tags may be
   better sellers for reasons unrelated to the tag — a sophisticated seller is
   more likely to use precise licensing vocabulary. The bank's existing fit
   rules and rights gate still apply to every row; a high-engagement median is
   never by itself a reason to select a tag.
2. **`Overall` for rows 29–41 is a 2026-09-22 route read**, not the 2026-09-06
   snapshot. Where a row shows a lower `Overall` than `Font category`, the route
   count is the narrower read. `配信素材` has no route count — the read failed
   and the value is deliberately blank rather than guessed.

**Do not refresh these counts during a listing run.** They are evidence for the
addition, exactly as the 2026-09-06 values are evidence for the original 28. To
re-read route counts deliberately, use:

    python3 bin/booth_tag_route_count.py --from-bank

A tag whose coverage has moved materially is a reason to amend this file as a
versioned act, not to re-query mid-run.


## Final 2026-09-06 route and seller-language additions

These are additions from live BOOTH route checks. The paid items and seller
examples are wording/market-position evidence, not sales or likes evidence.

| Candidate / route | Snapshot | What it shows | Status |
|---|---|---|---|
| [手書きフォント](https://booth.pm/ja/items?tags%5B%5D=%E6%89%8B%E6%9B%B8%E3%81%8D%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | 256 overall; 235 `フォント・書体` | Strong paid handwritten-font vocabulary; visible ¥300–¥5,500 products, commercial editions, digital-planner and broad design use | high / A when product is handwritten |
| [筆記体](https://booth.pm/ja/items?tags%5B%5D=%E7%AD%86%E8%A8%98%E4%BD%93) | 45 overall; 25 font-category | Paid script/calligraphic examples from multiple sellers, including ¥1,100–¥4,400 products | B; final frozen basic/medium route |
| [ドットフォント](https://booth.pm/ja/items?tags%5B%5D=%E3%83%89%E3%83%83%E3%83%88%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | 38 overall; 38 font-category | Paid `FFCDOTS`, `千菜`, `あわドット`, `PixelCube`, and other independent products | B; final frozen basic/medium route |
| [ピクセルフォント](https://booth.pm/ja/items?tags%5B%5D=%E3%83%94%E3%82%AF%E3%82%BB%E3%83%AB%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | 38 overall; 37 font-category | Paid Yokohama Dots, PIXELVF, Romly ARF Pixel Coding, and other independent products | B; final frozen basic/medium route |
| [ウェディング](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A6%E3%82%A7%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0) | 536 overall; 1 font-category item in this snapshot | Wedding is broad and mostly non-font on BOOTH; use only as a rare fit-driven exception, never as generic padding | low / C |
| [同人誌](https://booth.pm/ja/items?tags%5B%5D=%E5%90%8C%E4%BA%BA%E8%AA%8C) | 6,275 overall; 98 font-category items | Useful creator use case with meaningful font-category coverage; product must suit covers, headings, or doujinshi layout | basic / B |
| [バナー](https://booth.pm/ja/items?tags%5B%5D=%E3%83%90%E3%83%8A%E3%83%BC) | 755 overall; 77 font-category items | Banner design is mixed but has a meaningful font-category slice; select only for display/graphic fonts | basic / B |
| [ゲーム](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B2%E3%83%BC%E3%83%A0) | about 12,088 overall; 24 font-category items | Game is very broad; font-category activity is low/basic, but useful for pixel, fantasy, title, or UI fonts | basic / C |
| [広告](https://booth.pm/ja/items?tags%5B%5D=%E5%BA%83%E5%91%8A) | 465 overall; mixed catalog | Advertising vocabulary appears beside posters, flyers, banners, and design assets; treat as use-case wording, not a core font tag | C |

## Category banks

### Core object and taxonomy

High-priority: `フォント`, `font`, `fonts`, `オリジナルフォント`, `フォントデータ`,
`フォント・書体`, `書体`, `書体・フォント`, `欧文`, `欧文フォント`, `欧文書体`,
`typeface`, `font 書体`, `字体`, `英字`, `英字フォント`, `英語`, `英語フォント`,
`フォント 英語`, `アルファベット`, `アルファベットフォント`, `英数字`,
`英数字フォント`, `英文`.

Use `書体`, `書体・フォント`, `フォント・書体`, and `文字` mainly as
description vocabulary or carefully selected tags: they are often broader
synonyms/structural categories and can duplicate the core object terms.

### Western / Latin / English positioning

Validated or locally evidenced: `font`, `fonts`, `display font`, `font design`,
`font download`, `serif font`, `serif`, `script font`, `typeface`, `lettering`,
`title`, `font logo`, `欧文フォント`, `欧文書体`, `英字フォント`, `英語フォント`,
`フォント 英語`, `英数字フォント`, `アルファベットフォント`.

Candidate vocabulary not validated as a selectable tag in this frozen bank:
`western font`, `western`, `latin font`, `latin typeface`, `english typeface`,
`gothic font`, `blackletter`, `blackletter font`, `old english font`,
`display type`, `headline font`, `poster font`, `logo font`, `decorative type`,
`lettering font`, `calligraphy font`, `vintage font`, `retro font`,
`handwritten font`, `modern font`, `bold font`, `clean font`, `minimal font`.

English tags with spaces are retained as wording candidates even when a direct
route provider normalizes or blocks the URL. They are not selectable tags in
the frozen snapshot unless an exact route is already recorded elsewhere in
this file; local listing recurrence is not proof of BOOTH coverage.

### Style families

| Family | Banked Japanese terms | Banked English terms | Selection note |
|---|---|---|---|
| Display / headline | ディスプレイフォント, ディスプレイ体, 見出し, タイトル, テロップ | display font, display type, headline, title | Strong for large, attention-led lettering; avoid unsupported generic headline claims |
| Serif | セリフフォント, セリフ体, セリフ | serif font, serif | Select only when the font visibly has serifs |
| Sans | サンセリフ | sans serif, sans serif font | BOOTH paid examples use `サンセリフ` and `サンセリフ書体` wording |
| Script / handwriting | 手書き, 手書きフォント, 手書き風, 手書き風フォント, 筆記体, カリグラフィ, スクリプト | script font, handwritten font, calligraphy | Frozen route evidence is strongest for `手書きフォント`, `筆記体`, and `カリグラフィ`; no ordinary-run refresh |
| Blackletter / historical | ブラックレター, 中世, ケルト | blackletter, blackletter font, gothic font, old english font | Needs exact/category validation; do not infer from a vaguely ornate font |
| Pixel / dot | ドット, ドットフォント, ドット絵, ピクセル, ピクセルフォント, 8bit | pixel font, bitmap font, dot font | Final frozen routes show several independent paid products; exact totals are recorded in the final pre-freeze pass |
| Retro / vintage | レトロ, レトロ風, ヴィンテージ, 80年代風 | retro, retro font, vintage font, 80s font | Use only when visual facts support it |
| Decorative / graphic | 装飾フォント, デザインフォント, グラフィック, グラフィティ, ブラシ, スタンプ | decorative font, graffiti font, brush font, stamp font | Distinguish font from brush/graphic products; category evidence required |
| Personality | シンプル, クリーン, モダン, エレガント, かわいい, かわいいフォント, ポップ, ファンタジー, 美しいフォント | clean, modern, elegant, cute, pop, fantasy | Descriptive terms are useful but may have weak font-category coverage; do not fill tags with them automatically |
| Weight | 太字, ボールドフォント | bold font | `太字` is currently low but can be a fit-driven exception |

### Use-case and buyer-intent bank

| Use-case family | Banked terms | Current signal / rule |
|---|---|---|
| Brand/logo | ロゴ, ロゴデザイン, ロゴ素材, ブランド, ブランド名, ブランディング, font logo | Strong font-category coverage for `ロゴ` and `ロゴデザイン`; use product-fit gate |
| Editorial/headline | 見出し, タイトル, タイトルロゴ, 表紙, 書籍タイトル, 装丁, headline, title | Stronger when specimen shows large headlines, covers, or editorial hierarchy |
| Posters/advertising | ポスター, 広告, チラシ, バナー, poster, banner | `ポスター` has mixed high overall but low font-category coverage; `バナー` has 77 font-category items in the final snapshot |
| Packaging/labels | パッケージ, ラベル, グッズ, 素材 | Useful phrase family; must not claim packaging suitability without plausible display behavior |
| Creator publishing | 同人誌, 書籍タイトル, 表紙, 配信, 配信素材, サムネ, サムネイル, サムネイル素材 | `同人誌` has 98 font-category items in the final snapshot; thumbnail and stream terms are mixed catalog signals |
| Games / screens | ゲーム, テロップ, ピクセル, ピクセルフォント, 8bit | `ゲーム` has 24 font-category items in the final snapshot; prefer pixel/title/UI fit |
| Events / stationery | ウェディング, 招待状, 名刺, wedding, invitation, business card | Wedding is currently low font-category coverage; only use when supported by the product |
| General design | グラフィックデザイン, デザイン, デザイン素材, 素材, graphic design | `グラフィックデザイン` has 89 font-category items; broad roots are keyword vocabulary, not automatic tags |

### Rights, delivery, and format language

Banked candidates: `商用利用可`, `商用利用可能`, `商用可`, `商用利用OK`,
`ロイヤリティフリー`, `フォント ダウンロード`, `フォントダウンロード`,
`font download`, `フォントデータ`, `otf`, `OTF`, `ttf`, `TTF`, `WOFF2`,
`Webフォント`, `フォント 商用`, `商用利用`.

These are conditional tags. Rights tags require supplied license facts; format
tags require supplied file-format facts; web-font tags require web-use facts.
`フリーフォント` must never be used for a paid-only product without a
confirmed free version. `ロイヤリティフリー` is not interchangeable with
commercial use.

## Existing listing inventory and recurrence

The 45 existing `outputs/booth/*.md` listing files contain 142 unique tag
strings. Recurrence is FontFairy's own prior workflow usage, not independent
marketplace demand. It is retained as a language-prior and deduplication aid.

Most recurrent: `欧文フォント` 43, `font` 42, `ロゴ` 42,
`タイポグラフィ` 40, `オリジナルフォント` 39, `フォント` 38,
`書体` 36, `フォント・書体` 33, `英字フォント` 33,
`display font` 31, `ディスプレイフォント` 30, `英語フォント` 28,
`ロゴデザイン` 27, `font design` 25, `フォント ダウンロード` 24,
`font download` 22, `文字` 22, `書体・フォント` 21, `良いフォント` 21,
`fonts` 20, `typography` 20, `フォント デザイン` 20,
`フォント 英語` 20, `商用利用可` 18, `欧文書体` 18, `見出し` 18,
`装飾フォント` 17, `デザインフォント` 16, `セリフフォント` 15,
`フォントデータ` 14, `欧文` 14, `serif font` 12, `OpenType` 11,
`フォントデザイン` 10, `ブランディング` 10, `サンセリフ` 9,
`手書きフォント` 9, `レトロ` 8, `アルファベットフォント` 8,
`ウェディング` 7, `パッケージ` 7, `モダン` 7, `筆記体` 6,
`グラフィックデザイン` 6, `ポスター` 6, `商用利用可能` 6,
`手書き` 5, `エレガント` 5, `ロイヤリティフリー` 5.

Long-tail inventory to test selectively: `80年代風`, `8bit`, `calligraphy`,
`Font`, `Typography`, `Webフォント`, `WOFF2`, `かわいい`, `オリジナル`,
`カリグラフィ`, `クリーン`, `グラフィティ`, `ケルト`, `シンプル`,
`スクリプト`, `スタンプ`, `タイトル`, `タイトルロゴ`, `デザイン素材`,
`ドット`, `ドットフォント`, `ドット絵`, `バナー`, `ピクセル`,
`ピクセルフォント`, `ファンタジー`, `ブランド`, `ブランド名`,
`ボールドフォント`, `レトロ風`, `ロゴ素材`, `中世`, `名刺`, `商用利用OK`,
`多言語フォント`, `字体`, `広告`, `手書き風`, `手書き風フォント`,
`招待状`, `映画タイトル`, `書籍タイトル`, `美しいフォント`, `英数字`,
`英文`, `英語`, `表紙`, `配信素材`, `script font`, `lettering`, `typeface`,
`font logo`, `serif`, `title`, `script`, `blackletter`, `western font`,
`latin font`, `gothic font`, `vintage font`, `retro font`.

## Exclusions and maintenance notes

- FontFairy-owned products and shop pages are never independent competitor
  evidence. This includes owned items encountered in the BOOTH routes such as
  Merriloop, Pale Orison, Vertical Matter, Evercourt, and Mira Venn.
- Do not convert a high overall count into a font count. Mixed routes such as
  `ゲーム`, `広告`, `ウェディング`, `サムネイル`, and `グッズ` need the
  font-category split and a product-fit reason.
- `書体`, `文字`, `デザイン`, and `素材` are useful description vocabulary but
  can be broad or synonymically redundant. Keep them out of a 40-tag set when
  they do not add a distinct discovery angle.
- `modern`, `modern font`, `headline`, `poster`, `multilingual`, `glyph`,
  `グリフ`, `ミニマル`, and `ボールド` currently have dead/no-font-category or
  weak evidence in the Archive Meter snapshot. Keep them keyword-only unless
  the user explicitly replaces this baseline with a new research pass.
- Last known detailed local evidence is in
  `outputs/booth/booth-tag-ledger.md` and the product research files under
  `outputs/booth/.research/`. The final pre-freeze pass is authoritative for
  the permanent bank; do not append new live snapshots or silently replace
  these values during an ordinary listing run.

## Research provenance

Local listing recurrence and Archive Meter evidence: `outputs/booth/*.md` and
`outputs/booth/booth-tag-ledger.md`, primarily checked 2026-09-05.

Final route checks: BOOTH exact-tag/category pages checked with the available
web provider on 2026-09-06. The provider was not treated as Firecrawl when the
runtime exposed only generic web retrieval. The values are permanently frozen
for this workflow even though BOOTH's public catalog may change later.

## Historical seller-language sweep: 2026-09-06

This sweep adds wording and paid-product positioning from independent BOOTH
font sellers. These pages are not being treated as tag counts unless an exact
tag/category route is separately recorded above.

| Seller/product evidence | New vocabulary to test | Why it matters |
|---|---|---|
| [Abyss Dive Punk Retro](https://booth.pm/ja/items/7913697), そらマート, paid | レトロフューチャー, 海洋SF風, 有料販売専用, TrueType, 商用利用可 | Shows that a named visual concept plus `レトロ` can describe a paid Western/display font; test `レトロフューチャー` only as a candidate until route evidence exists |
| [はたレトロ](https://booth.pm/ja/items/2690724), hataretro-font, paid | レトロチック, アルファベット, ひらがな, 個人利用・商用利用OK, OTF, TTF | Confirms a small independent seller uses retro and format/licensing language around a paid font; format/rights remain fact-gated |
| [りんごひめ](https://booth.pm/ja/items/4275687), いらめもフォント部, paid | レトロキュート, 手描き文字, 昭和, 少女向け雑誌, 2ウェイト, OpenType | Adds differentiated Japanese style language for cute/retro handwritten fonts |
| [MARQUETRY](https://booth.pm/ja/items/8808861), FontFairy, paid | モダンセリフ, ブランディング用, プレミアム, エディトリアル, ラグジュアリー, ラベル, 名刺, 引用デザイン | High-tier storefront-style positioning joins serif, branding, editorial, packaging, and invitation use cases |
| [Signalrun](https://booth.pm/ja/items/8808875), FontFairy, paid | 太字ディスプレイ, ブランドアイデンティティ, イベントポスター, キャンペーン用見出し, 商品ラベル, アパレルグラフィック | Shows how a bold display font is advertised through concrete commercial use cases rather than generic style adjectives |
| [Fancy Star Script route](https://booth.pm/ja/items?tags%5B%5D=%E7%AD%86%E8%A8%98%E4%BD%93), Satsuyako Design Works, paid examples | 筆記体, カリグラフィー, script, wedding/invitation vocabulary | Independent paid script products appear in the live route; retain `筆記体` and `カリグラフィー` as style/use-case candidates |

The following phrases were reviewed during the final pass. Only phrases with
the route evidence recorded elsewhere in this file are selectable tags; the
rest remain description vocabulary or rejected candidates:
`レトロフューチャー`, `海洋SF`, `レトロチック`, `レトロキュート`,
`モダンセリフ`, `プレミアムフォント`, `ラグジュアリーフォント`,
`ブランドアイデンティティ`, `イベントポスター`, `キャンペーン見出し`,
`商品ラベル`, `アパレルグラフィック`, `エディトリアルフォント`,
`引用デザイン`, `サンセリフ書体`, `ウェブフォント`, `Latin Extended`,
`レタリングデザイン`.

The FontFairy products returned in the same sweep—Tracery, Mellow Tone, and
ByteFrame—are intentionally excluded from independent-seller evidence. Their
copy can still be used internally as a reminder to keep product facts and
licensing claims separate from vocabulary research.

## Historical exact-route sweep: 2026-09-06

| Tag | Exact route snapshot | Font-category count | Activity | Paid / seller observation | Decision |
|---|---:|---:|---|---|---|
| [サンセリフ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B5%E3%83%B3%E3%82%BB%E3%83%AA%E3%83%95) | 28 overall | 27 | basic | Paid results include TYP store, TYPE-LABO, and そらマート examples | Strong sans candidate when construction is factual |
| [セリフ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BB%E3%83%AA%E3%83%95) | 247 overall | 14 | low | Paid/paid-option products appear from Amari_design and other sellers | Fit-driven low-activity exception only |
| [カリグラフィ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%AB%E3%83%AA%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3) | 138 overall | 126 | high | Many paid YutaONE typefaces plus other font sellers; route includes style and lettering language | Strong when calligraphic construction is factual |
| [ゴシック](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B4%E3%82%B7%E3%83%83%E3%82%AF) | 7,114 overall | 45 | basic | Mixed catalog, with 45 font-category items; do not confuse gothic clothing with gothic type | Use for gothic fonts only after fit check |
| [エレガント](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A8%E3%83%AC%E3%82%AC%E3%83%B3%E3%83%88) | 1,021 overall | 6 | low | Mostly mixed fashion/3D/background catalog; paid font category is sparse | Description language or rare fit-driven tag |
| [レトロ](https://booth.pm/ja/items?tags%5B%5D=%E3%83%AC%E3%83%88%E3%83%AD) | 6,778 overall | 128 | high | Mixed catalog but 128 font-category items, including paid script and display fonts | Strong style candidate when retro is factual |
| [ブランド](https://booth.pm/ja/items?tags%5B%5D=%E3%83%96%E3%83%A9%E3%83%B3%E3%83%89) | 102 overall | 2 | low | Mixed brand merchandise and only a small font slice | Use only for explicit branding products |
| [セリフフォント search/category wording](https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?q=%E3%82%BB%E3%83%AA%E3%83%95) | 159 font-category keyword results | 159 keyword results | basic/high wording signal | Paid products include TYP store and Amari_design; this is keyword search, not an exact tag count | Keep as discovery language; exact tag route still pending |
| [ブラックレター search with font filter](https://booth.pm/ja/search/%E3%83%96%E3%83%A9%E3%83%83%E3%82%AF%E3%83%AC%E3%82%BF%E3%83%BC?tags%5B%5D=font) | 22 filtered results | 22 filtered font-category results | basic filtered signal | Paid examples include Amari_design, そらマート, ymnk-design, and Lena; related terms include `欧文フォント`, `フォント 商用`, `商業利用可` | Permanent wording/comparator evidence; not exact `ブラックレター` tag validation |

The exact-route sweep confirms that the current agent's repeated `display`,
`欧文`, `logo`, and `font` vocabulary is not the whole market. Sans, serif,
calligraphic, gothic, retro, pixel, handwriting, and use-case routes produce
distinct catalog slices, but their counts vary sharply. This is why the bank
keeps both a priority score and a fit gate instead of simply selecting the
largest overall route.

### What the higher-tier shops are doing

The large-catalog / high-price examples are useful for vocabulary structure,
not proof that a tag caused sales. The YutaONE font-category search currently
surfaces 122 products, including a 256-font bundle and many individual
typefaces at ¥30,000, with names that combine a memorable concept and a clear
style signal: `バトルサンセリフ`, `ベイパーピクセル`, `ネオクラシカルゴス`,
`メカニカルサンセリフ`, `ブリックテキストロゴ`, `ナインマットスクリプト`,
`ピクセレーションセリフ`, and `スタジアムスラブ`. This suggests a useful
research pattern: style/object terms can be more specific than generic
`font`, but should be selected only when the product actually has that style.

The same results show separate paid/free timing and bundle language. Keep
`無料`, `フリー`, and `商用` out of a paid listing unless the supplied product
facts support the exact offer. The bank records these as conversion-language
signals, not automatic tags.

### Likes and engagement field limitation

The public rendered BOOTH pages checked in the initial pass exposed item
prices, category placement, related tags, and result counts, but did not expose
a reliable numeric likes/favorites field in the retrieved text. The final
pre-freeze pass separately recorded structured item-level wish-list counts;
those values are documented below and are not tag demand. This bank does not
invent or infer likes from “popular” labels, price, product age, or catalog
order.

## Historical exact-route and use-case sweep: 2026-09-06

This sweep records additional Japanese style, English/Latin positioning, and
creator-use routes. Counts are live BOOTH catalog snapshots from 2026-09-06;
they are not search volume or sales. A category count is the number shown in
the `フォント・書体` category slice, not the number of paid products. Visible
paid cards are recorded only as a presence/language signal.

### Selector-ready route registry

The table is deliberately compact and machine-readable enough for Agent 20 to
seed its candidate queue. `A/B/C` follows the evidence definitions above;
`conditional` means a product fact must pass before the term can be selected.
`paid visible` means at least one paid card was visible during the route check,
not a paid-item total.

| Priority group | Tag | Family | Language | Exact route snapshot | Font category | Activity | Evidence | Paid / seller signal | Fit gate | Last checked |
|---|---|---|---|---:|---:|---|---|---|---|---|
| high | [手書き](https://booth.pm/ja/items?tags%5B%5D=%E6%89%8B%E6%9B%B8%E3%81%8D) | handwriting | JP | 1,411 | 123 | high | B | paid visible; mixed sellers | only handwritten/hand-drawn construction | 2026-09-06 |
| high | [手書き風フォント](https://booth.pm/ja/items?tags%5B%5D=%E6%89%8B%E6%9B%B8%E3%81%8D%E9%A2%A8%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | handwriting | JP | 42 | 38 | basic | B | paid font cards visible | only handwritten-style construction | 2026-09-06 |
| high | [カリグラフィ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%AB%E3%83%AA%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3) | script/calligraphy | JP | 138 | 126 | high | A | paid YutaONE and other font sellers visible | only calligraphic/script construction | 2026-09-06 |
| high | [レトロ](https://booth.pm/ja/items?tags%5B%5D=%E3%83%AC%E3%83%88%E3%83%AD) | era/style | JP | 6,778 | 128 | high | B | paid script/display cards visible | only retro period/vibe is supported | 2026-09-06 |
| high | [英字](https://booth.pm/ja/items?tags%5B%5D=%E8%8B%B1%E5%AD%97) | Western/Latin | JP | 150 | 48 | basic | B | paid font cards visible | Latin/English letter coverage | 2026-09-06 |
| high | [アルファベット](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A2%E3%83%AB%E3%83%95%E3%82%A1%E3%83%99%E3%83%83%E3%83%88) | Western/Latin | JP | 664 | 88 | basic | B | paid font cards visible | alphabet/Latin product fit | 2026-09-06 |
| high | [フォント 商用](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88+%E5%95%86%E7%94%A8) | rights/intent | JP | 1,003 | 999 | high | B | paid font cards visible | supplied commercial-use fact must be exact | 2026-09-06 |
| high | [フォント 日本語](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88+%E6%97%A5%E6%9C%AC%E8%AA%9E) | language | JP | 296 | 291 | high | B | paid font cards visible | Japanese support must be supplied | 2026-09-06 |
| conditional | [フリーフォント](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%83%AA%E3%83%BC%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | rights/intent | JP | 947 | 912 | high | B | paid and free cards can coexist | confirmed free version required; never use for paid-only | 2026-09-06 |
| basic | [サンセリフ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B5%E3%83%B3%E3%82%BB%E3%83%AA%E3%83%95) | sans | JP | 28 | 27 | basic | B | paid TYP store, TYPE-LABO, and そらマート cards | sans construction must be factual | 2026-09-06 |
| low-fit | [セリフ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BB%E3%83%AA%E3%83%95) | serif | JP | 247 | 14 | low | C | paid/paid-option font cards visible | serif construction must be factual; low-activity exception | 2026-09-06 |
| basic | [ゴシック](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B4%E3%82%B7%E3%83%83%E3%82%AF) | gothic | JP | 7,114 | 45 | basic | B | font-category cards visible among a mixed route | gothic type style, not clothing/fashion | 2026-09-06 |
| low-fit | [エレガント](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A8%E3%83%AC%E3%82%AC%E3%83%B3%E3%83%88) | personality | JP | 1,021 | 6 | low | C | sparse font slice | use only when the supplied style supports it | 2026-09-06 |
| low-fit | [ブランド](https://booth.pm/ja/items?tags%5B%5D=%E3%83%96%E3%83%A9%E3%83%B3%E3%83%89) | branding | JP | 102 | 2 | low | C | mostly mixed brand merchandise | explicit branding fit only | 2026-09-06 |
| basic | [タイトルロゴ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%BF%E3%82%A4%E3%83%88%E3%83%AB%E3%83%AD%E3%82%B4) | logo/headline | JP | 152 | 15 | low | C | paid font cards visible; route also has logo assets | title/logo fit; do not confuse asset products with fonts | 2026-09-06 |
| basic | [サムネイル](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B5%E3%83%A0%E3%83%8D%E3%82%A4%E3%83%AB) | creator use | JP | 7,296 | 96 | basic | C | paid font-category slice plus creator assets | use for fonts suited to thumbnail headlines | 2026-09-06 |
| basic | [配信](https://booth.pm/ja/items?tags%5B%5D=%E9%85%8D%E4%BF%A1) | creator use | JP | 13,328 | 83 | basic | C | paid creator/design cards; mixed route | streaming/title use must be plausible | 2026-09-06 |
| basic | [同人誌](https://booth.pm/ja/items?tags%5B%5D=%E5%90%8C%E4%BA%BA%E8%AA%8C) | creator publishing | JP | 6,275 | 98 | basic | B | paid font-category cards visible | covers/headings/editorial fit | 2026-09-06 |
| basic | [バナー](https://booth.pm/ja/items?tags%5B%5D=%E3%83%90%E3%83%8A%E3%83%BC) | graphic use | JP | 755 | 77 | basic | B | paid font-category cards visible | banner/display fit | 2026-09-06 |
| basic | [ゲーム](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B2%E3%83%BC%E3%83%A0) | games/screens | JP | 12,088 | 24 | basic | C | mixed route; font cards visible | pixel/title/UI/game fit only | 2026-09-06 |
| low-fit | [スポーツ](https://booth.pm/ja/items?tags%5B%5D=%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%84) | sports/branding | JP | 1,303 | 2 | low | C | a few font-category results; paid handwritten card visible | sports/display identity must be explicit | 2026-09-06 |
| low-fit | [ポスター](https://booth.pm/ja/items?tags%5B%5D=%E3%83%9D%E3%82%B9%E3%82%BF%E3%83%BC) | poster use | JP | 3,695 | 8 | low | C | paid font cards visible in a mixed route | poster/display fit; low-activity exception | 2026-09-06 |
| low-fit | [チラシ](https://booth.pm/ja/items?tags%5B%5D=%E3%83%81%E3%83%A9%E3%82%B7) | flyer use | JP | 433 | 6 | low | C | paid font/graphic-style cards visible | flyer/display fit; low-activity exception | 2026-09-06 |
| low-fit | [名刺](https://booth.pm/ja/items?tags%5B%5D=%E5%90%8D%E5%88%BA) | stationery/use | JP | 426 | 1 | low | C | one font-category result in snapshot | business-card/identity fit; normally description vocabulary | 2026-09-06 |
| low-fit | [招待状](https://booth.pm/ja/items?tags%5B%5D=%E6%8B%9B%E5%BE%85%E7%8A%B6) | events/stationery | JP | 114 | 2 | low | C | two font-category results; one visible result is FontFairy-owned and excluded from independent evidence | invitation/wedding fit; exclude owned result | 2026-09-06 |
| low-fit | [ウェディング](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A6%E3%82%A7%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0) | events | JP | 536 | 1 | low | C | font slice is sparse and mixed | wedding suitability must be explicit; never generic padding | 2026-09-06 |
| keyword-only/pending | [ラベル](https://booth.pm/ja/items?tags%5B%5D=%E3%83%A9%E3%83%99%E3%83%AB) | packaging/labels | JP | 188 | not exposed | pending | C | route live but no usable `フォント・書体` total in captured response | description wording only in the frozen snapshot | 2026-09-06 |

### Route interpretation and seller-language notes

- `手書き` and `手書き風フォント` are separate opportunities: the broad
  handwriting route has high font-category coverage, while the more specific
  phrase has a smaller but much cleaner font slice. Keep both as conditional
  candidates rather than treating them as duplicate padding.
- `英字` and `アルファベット` provide a Japanese-facing bridge to
  Western/Latin font discovery. They are not substitutes for the exact
  `欧文フォント`/`英語フォント` rows already in the bank; select the terms
  that match the actual character coverage and avoid stacking every synonym.
- `フォント 商用` is a very strong rights-intent route, but rights are not
  inferred from a paid listing. It is eligible only when the supplied license
  facts explicitly support commercial use. `フリーフォント` remains a
  separate conditional route even though paid cards can appear beside free
  versions.
- Creator-use routes have different quality: `同人誌` (98 font-category),
  `サムネイル` (96), `バナー` (77), and `配信` (83) have useful basic activity;
  `ポスター` (8), `チラシ` (6), `名刺` (1), and `招待状` (2) are low-activity
  fit exceptions. Their large overall counts must not hide that difference.
- `タイトルロゴ` is a discovery bridge between logo assets and fonts. The
  route includes paid font cards, but also many logo/streaming assets, so the
  category split and product fit are mandatory.
- `招待状` includes a FontFairy-owned font in the visible category slice. It is
  excluded from independent-seller, paid-product, and diversity evidence; the
  route count is retained only as a catalog-coverage snapshot.
- `ラベル` is not promoted to a validated tag from this sweep because the
  captured page did not expose a usable font-category total. Keep it as
  description wording; do not use a future ordinary-run update to change the
  frozen decision.

### Superseded list-first recommendation

The earlier list-first recommendation in this historical section is superseded
by the `Permanent snapshot lock` below. It is retained only to show the method
used before the final freeze. Agent 20 must use the frozen instructions at the
top of this file: select from this bank, apply the supplied-font fit gate, and
do not perform ordinary-run live route refreshes or append new route counts.

## Historical English/Western route and engagement addendum: 2026-09-06

This addendum closes two gaps in the earlier bank: English/Western-facing
vocabulary and item-level engagement evidence. All route counts below are
public BOOTH coverage snapshots from 2026-09-06. They are not search volume,
sales, or conversion estimates. English routes are especially noisy because
BOOTH's global catalog includes non-font products, so the font-category slice
and visible paid font cards matter more than the overall count.

### English, Western, and Latin route registry

| Priority | Tag or route | Exact route snapshot | Font category | Activity | Evidence | Decision / fit gate | Last checked |
|---|---|---:|---:|---|---|---|---|
| high | [typeface](https://booth.pm/ja/items?tags%5B%5D=typeface) | 35 | 35 | basic | A/B | Strong English-facing typeface wording; use when the product is a complete typeface/font, not a lettering asset | 2026-09-06 |
| high | [font logo](https://booth.pm/ja/items?tags%5B%5D=font+logo) | 129 | 129 | high | A/B | Good Western-style logo/discovery bridge; use only where logo/title construction is a genuine use case | 2026-09-06 |
| high | [英字](https://booth.pm/ja/items?tags%5B%5D=%E8%8B%B1%E5%AD%97) | 150 | 48 | basic | B | Japanese-facing Latin/English-letter bridge; requires Latin/English coverage | 2026-09-06 |
| high | [アルファベット](https://booth.pm/ja/items?tags%5B%5D=%E3%82%A2%E3%83%AB%E3%83%95%E3%82%A1%E3%83%99%E3%83%83%E3%83%88) | 664 | 88 | basic | B | Use for alphabet/Latin lettering products; do not stack with every equivalent | 2026-09-06 |
| high | [フォント 商用](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88+%E5%95%86%E7%94%A8) | 1,003 | 999 | high | B | Very strong commercial-intent route; only if supplied license facts explicitly support it | 2026-09-06 |
| high | [フォント 日本語](https://booth.pm/ja/items?tags%5B%5D=%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88+%E6%97%A5%E6%9C%AC%E8%AA%9E) | 296 | 291 | high | B | Only for products with supplied Japanese glyph/language support | 2026-09-06 |
| basic | [明朝体](https://booth.pm/ja/items?tags%5B%5D=%E6%98%8E%E6%9C%9D%E4%BD%93) | 73 | 63 | basic | B | Japanese serif/Mincho construction; paid examples from multiple sellers were visible | 2026-09-06 |
| basic | [筆文字](https://booth.pm/ja/items?tags%5B%5D=%E7%AD%86%E6%96%87%E5%AD%97) | 670 | 86 | basic | B | Brush/brush-lettering construction; paid examples from multiple sellers were visible | 2026-09-06 |
| conditional | [english](https://booth.pm/ja/items?tags%5B%5D=english) | 100 | 3 | low | C | Mixed exact route; wording bridge only unless the product has a strong English-font fit | 2026-09-06 |
| conditional | [western](https://booth.pm/ja/items?tags%5B%5D=western) | 32 | no usable font slice | pending | C | Mixed/non-font route; do not select as a validated font tag from this snapshot | 2026-09-06 |
| conditional | [script](https://booth.pm/ja/items?tags%5B%5D=script) | 321 | no usable font slice | pending | C | English wording only until a current font-category result is established | 2026-09-06 |
| conditional | [display](https://booth.pm/ja/items?tags%5B%5D=display) | 20 | no usable font slice | pending | C | Prefer the established `display font` route; bare `display` remains wording-only in the frozen snapshot | 2026-09-06 |

The exact English-facing `font` route currently shows 1,651 results on
[BOOTH's English exact-tag route](https://booth.pm/en/items?tags%5B%5D=font),
with a visible Fonts category slice. The broader
[English font search](https://booth.pm/en/search/font) shows 3,806 indexed
results and the [English Fonts browse page](https://booth.pm/en/browse/Fonts)
shows 4,673 catalog entries in their respective snapshots. These are useful
for language and catalog-surface context, not demand numbers. The existing
banked `欧文フォント`, `英字フォント`, `英語フォント`, `display font`,
`font design`, `font download`, and `fonts` rows remain preferred when their
individual exact/category evidence and product-fit gates pass.

### What stronger sellers actually say

Use these as vocabulary and positioning patterns, not as facts to transfer to
another product. The repeated pattern is a style or construction label first,
then a concrete use-case cluster, then language/format/licensing details when
the seller supplies them.

| Seller / product evidence | Observed language pattern | How Agent 20 may use it |
|---|---|---|
| [YutaONE font/logo route](https://booth.pm/ja/items?tags%5B%5D=font+logo) | Large paid collections and individual styles use distinct style names and logo/display positioning; visible examples include BattleSansSerif, FlamingoSerif, VaporPixel, BrickTextLogo, NeoSlashGoth, and PixelationSerif | Use concrete construction/style words such as logo, display, serif, gothic, pixel, or retro only when the supplied font supports them; do not imitate a collection claim |
| [FLOP 412-font bundle](https://booth.pm/en/items/4443275) | Large bundle language, hand-drawn/rounded gothic positioning, logo/photo text/manga use, OTF and commercial-use wording | For a matching font, combine one accurate style term with one or two use cases; do not claim a bundle, glyph count, or format without supplied facts |
| [toktaro Angle](https://booth.pm/en/items/6049679) | Handwritten variable font; title/headline/decorative use; English, Latin, and symbol coverage; paid and free versions | Separate writing/display purpose from technical coverage; use headline or decorative wording only where visually supported |
| [FLOP かなたとひなた](https://booth.pm/en/items/3742636) | Hand-drawn rounded gothic; logo, photo text, and manga use; single-font and set pricing | Supports the recurring use-case cluster `logo`, `photo text`, and `manga` for matching fonts, not as universal tags |
| [YMNK-design font catalogue](https://booth.pm/en/items/1320846) | Individual named fonts are merchandised as recognizable style products rather than generic “font” items | Keep the final font name first, then add only the most accurate style/use bridge |
| [G.Ikoma historical revival typeface](https://booth.pm/ja/items/7303096) | Historical source/revival, European print influence, Jugendstil/Blackletter framing, logos/posters/packaging/title use | Western/Latin fonts benefit from era, source, and concrete application language when those facts are actually supplied |
| [Keisasa blackletter](https://booth.pm/ja/items/7303096) and [collection wording](https://booth.pm/ja/items/7303333) | Blackletter is explained through medieval/European manuscript atmosphere and logo, poster, packaging, title, doujinshi, and video-title use | Use atmosphere and applications as selective copy vocabulary; do not turn a fictional theme into a product-history claim |
| REN FONT and AngelVibes products surfaced on the `typeface` route | Paid independent fonts are sold through named families, specific display styles, and individual products rather than broad English synonyms alone | Keep `typeface` as a supporting English-facing tag; prioritize the actual style family and use case |
| FontFairy `MARQUETRY` and `Signalrun` | Branding, editorial, packaging, logo, poster, label, and apparel language around named display styles | Use design-use vocabulary for fonts suited to identity/editorial/packaging; retain labels as description language unless the tag route is revalidated |
| [まっつん丸 retro lamp font](https://booth.pm/en/items/3592632) | Retro display concept with print, web, video, logo, game, app, and doujin use; free/paid variants | Supports a broad but concrete application cluster for genuinely retro/display fonts; rights and pricing wording stay product-specific |

The Western/Latin pattern is therefore not “add `western` everywhere.” It is
Japanese discovery bridges (`欧文`, `英字`, `アルファベット`) plus selective
English product language (`typeface`, `font logo`, `display font`, `font
design`) and a concrete use case. Bare `western`, `english`, `script`, and
`display` remain weak or mixed exact tags in this snapshot.

### Item-level likes/favorites evidence (separate from tag activity)

The earlier rendered-page limitation is corrected by this final evidence note:
public BOOTH item HTML often omits a visible number, but a public structured
wish-list response can expose a count. The endpoint shape is documented in the
read-only [third-party SDK endpoint source](https://raw.githubusercontent.com/thisoverride/BoothPM-SDK/main/src/lib/core/api/ApiEndPoint.ts)
and the field mapping is visible in its
[product-service source](https://raw.githubusercontent.com/thisoverride/BoothPM-SDK/main/src/lib/domain/services/impl/ProductService.ts).
This is not an official BOOTH API claim and should be treated as an
undocumented public response that may change.

Read-only request on 2026-09-06:

`https://accounts.booth.pm/wish_lists.json?item_ids%5B%5D=2890872&item_ids%5B%5D=7303096&item_ids%5B%5D=8808861&item_ids%5B%5D=8808875`

Returned `wishlists_counts`:

| Item | Seller / product | Price observed | Wish-list count | Interpretation |
|---:|---|---:|---:|---|
| 2890872 | YutaONE large font bundle | ¥128,000 | 9,511 | High item-level engagement signal for this item; not tag demand or sales |
| 7303096 | Keisasa / G.Ikoma blackletter | ¥300 | 14 | Low observed item-level engagement; still a paid-product/style-language anchor |
| 8808861 | FontFairy `MARQUETRY` | ¥1,000 | 0 | Observed zero in the response; do not convert to unknown or infer sales |
| 8808875 | FontFairy `Signalrun` | ¥1,000 | 0 | Observed zero in the response; do not convert to unknown or infer sales |

Agent 20 must not build tag scores, cohorts, medians, percentiles, or sales
claims from these values. When the user explicitly asks for likes/favorites,
the agent may query this endpoint for the already-selected global paid
comparator items, then record item ID, URL, seller, paid status, retrieval date,
and the raw count. Otherwise it should avoid the extra request and keep the
field `not requested`. A missing or failed response is `not exposed`; a
returned zero is a genuine observed zero for that item. Likes measure item
engagement, while exact-tag/category counts measure catalog coverage and font
relevance; neither is BOOTH search volume.

### Selector-ready conclusion

The bank is sufficient for frozen-snapshot Agent 20 selection: it contains the
existing FontFairy tag vocabulary, a ranked Japanese and English/Western core,
style and use-case long tails, exact/category route URLs and activity tiers,
paid-product/seller-language observations, exclusion rules, and a documented
item-engagement path. Use the frozen records with the supplied-font fit gate;
do not refresh stale rows, append changed counts, or let later FontFairy
uploads rewrite the baseline.

## Historical source correction: 2026-09-06

The G.Ikoma comparator labels in the preceding seller-language table are
clarified here: item `6852452` is
[Olympian Stephenson Extended](https://booth.pm/ja/items/6852452), while
[HISPANIA is item 8273414](https://booth.pm/ja/items/8273414). Item `7303096`
is the separate [Keisasa blackletter item](https://booth.pm/ja/items/7303096).
Keep the three products as separate comparator records and do not merge their
likes, prices, or product-language observations.

The final English exact-`font` route capture on 2026-09-06 recorded 1,651
results; it supersedes the earlier 1,648 observation within this permanent
snapshot. The earlier value remains only as historical provenance.

## Historical paid-font likes sample expansion: 2026-09-06

The same public structured response was queried for a wider, deliberately
mixed paid-font comparator sample. Request URL:

`https://accounts.booth.pm/wish_lists.json?item_ids%5B%5D=6852452&item_ids%5B%5D=7303333&item_ids%5B%5D=6049679&item_ids%5B%5D=3742636&item_ids%5B%5D=3592632&item_ids%5B%5D=4443275&item_ids%5B%5D=3617002&item_ids%5B%5D=7913697&item_ids%5B%5D=2690724&item_ids%5B%5D=4275687`

Returned `wishlists_counts` on 2026-09-06:

| Item | Seller / product | Paid observation | Wish-list count | What it can and cannot show |
|---:|---|---|---:|---|
| 6049679 | toktaro, Angle | ¥2,800 paid version plus free version | 6,719 | Strong item-level engagement for this item; not a tag or sales result |
| 3742636 | FLOP Design Font, かなたとひなた | ¥2,480 single / ¥6,980 set | 4,530 | Item engagement for a recognizable paid font product; not transferable to every handwritten/rounded tag |
| 3592632 | まっつん丸, retro lamp font | free / ¥500 / ¥1,100 versions | 4,122 | Engagement includes a product with multiple offer states; do not compare as a pure paid-only cohort |
| 3617002 | YMNK-design, 金魚ランタン | ¥5,000 paid font | 2,969 | Item signal for a named paid font; not evidence of a particular tag's demand |
| 4443275 | FLOP Design Font, 412-font bundle | ¥24,800–¥24,980 bundle | 2,465 | Bundle engagement is not comparable to one-font engagement or tag activity |
| 2690724 | hataretro-font, はたレトロ | paid item | 967 | Seller-language and item signal; exact price was not part of this read |
| 4275687 | いらめもフォント部, りんごひめ | paid item | 233 | Item signal for a named retro/handwritten product |
| 6852452 | G.Ikoma Type Foundry, historical revival typeface | ¥1,100 paid font | 23 | Paid Western/historical comparator with low observed item engagement |
| 7303333 | Keisasa, 11-style font collection | ¥2,000 paid collection | 2 | Small observed item signal; product-language evidence remains useful |
| 7913697 | そらマート, Abyss Dive Punk Retro | paid item | 4 | Small observed item signal; do not infer weak demand for the `レトロ` family |

This sample is intentionally not a performance benchmark: product age,
audience, seller size, offer structure, and catalog placement are uncontrolled.
Agent 20 may cite these values only as item-level engagement observations when
the user asks for likes/favorites. It must not average them into a tag score,
rank tags by the likes of one seller's product, or call them BOOTH demand.

### Transparent route-activity score key

When a user explicitly asks for a simple activity score, use the font-category
route only, so the score remains reproducible and does not smuggle item likes
into tag demand:

| Score | Font-category count | Label | Selection treatment |
|---:|---:|---|---|
| 3 | 100+ | high | Strong coverage signal; still require product fit and paid/seller evidence |
| 2 | 17–99 | basic/medium | Usable coverage signal; compare specificity and fit against higher-coverage alternatives |
| 1 | 1–16 | low | At most three fit-driven exceptions across a 40-tag set; record the exception |
| 0 | 0 / failed | dead/no coverage | Do not select as a validated tag; retain as keyword-only or ledger rejection |

Evidence tier, paid-product presence, distinct-seller count, and product fit
remain separate fields. Likes are a separate item-engagement column and never
change this route-activity score. This makes the bank's “ordered” list auditable
without pretending that a tag route or a popular item is a BOOTH search-volume
measurement.

## Final pre-freeze research pass: 2026-09-06

This is the last research pass for the permanent baseline. The values below
are the final snapshots to use in normal BOOTH listing runs. Future FontFairy
uploads must not update, replace, or invalidate this baseline. The bank is
intentionally a historical pre-expansion snapshot: later changes to BOOTH's
catalog may be useful context only when the user explicitly commissions a new
research project, never as an automatic update during an ordinary listing run.

### Resolved long-tail routes

| Candidate / route | Final exact snapshot | Font-category snapshot | Activity score | Paid and seller evidence | Permanent decision |
|---|---:|---:|---:|---|---|
| [筆記体](https://booth.pm/ja/items?tags%5B%5D=%E7%AD%86%E8%A8%98%E4%BD%93) | 45 | 25 | 2 | Paid Satsuyako Design Works products at ¥2,200–¥4,400, Loca Scheme at ¥300, G.Ikoma at ¥1,100, and Keisasa at ¥300 were visible | Valid basic/medium style tag for genuine cursive/script products; commercial or free wording remains fact-gated |
| [ドットフォント](https://booth.pm/ja/items?tags%5B%5D=%E3%83%89%E3%83%83%E3%83%88%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | 38 | 38 | 2 | Font-category route includes paid products such as しかくふと at ¥1,000, PIXELVF at ¥500+, FFCDOTS at ¥300, 千菜 at ¥350, PixelCube at ¥300, あわドット at ¥980, and まめドット at ¥500; many free/paid variants coexist | Valid basic/medium pixel/dot tag when the font genuinely has a dot/bitmap construction; do not inherit `無料` |
| [ピクセルフォント](https://booth.pm/ja/items?tags%5B%5D=%E3%83%94%E3%82%AF%E3%82%BB%E3%83%AB%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88) | 38 | 37 | 2 | Paid examples include Yokohama Dots at ¥500, PIXELVF at ¥500+, Romly ARF Pixel Coding at ¥700, and multiple ¥100–¥300 products | Valid basic/medium pixel tag; use the concrete game, UI, coding, or retro use case only when the product supports it |
| [ブラックレター + font filter](https://booth.pm/ja/search/%E3%83%96%E3%83%A9%E3%83%83%E3%82%AF%E3%83%AC%E3%82%BF%E3%83%BC?tags%5B%5D=font) | 22 filtered keyword results | 22 filtered font-category results | 2 as a filtered coverage signal | Paid Amari_design at ¥600, SoraMart products at ¥2,500, ymnk-design at ¥5,000, Lena at ¥4,980, plus YutaONE and Keisasa; related labels include `商用可`, `梵字`, `欧文フォント`, `フォント 商用`, and `font design` | Strong permanent wording/comparator evidence, but not an exact `ブラックレター` tag validation; use exact-tag evidence only if separately captured |
| [カリグラフィー](https://booth.pm/ja/items?tags%5B%5D=%E3%82%AB%E3%83%AA%E3%82%B0%E3%83%A9%E3%83%95%E3%82%A3%E3%83%BC) | 86 | 5 | 1 | Mostly mixed calligraphy assets, with paid font-category examples such as かりぐらスキップ at ¥3,300 and さなフォン飾 at ¥500+; G.Ikoma HISPANIA and SYLPHIDE also appear | Keep as a low-activity fit exception only; prefer the stronger exact `カリグラフィ` route (138/126) for font tags |
| [ラベル](https://booth.pm/ja/items?tags%5B%5D=%E3%83%A9%E3%83%99%E3%83%AB) | 188 | no font-category result exposed | 0 | Route is dominated by sticker, illustration, frame, and packaging assets | Description/use-case wording only; do not select as a validated font tag from this snapshot |

The final route reading confirms the important distinction between a phrase's
overall popularity and font relevance. `ドットフォント` and `ピクセルフォント`
are compact, font-heavy opportunities. `筆記体` is smaller but still useful.
The long-vowel `カリグラフィー` route is mostly mixed assets, while the exact
`カリグラフィ` route already banked above is the stronger font route. Wedding
and invitation vocabulary remains fit-driven: the permanent baseline records
`ウェディング` at one font-category result and `招待状` at two, with an owned
FontFairy result excluded from independent evidence. No unvalidated
`ウェディングフォント`, `結婚式 フォント`, or `招待状 フォント` phrase is
promoted into selected-tag evidence.

### Additional independent paid-seller positioning patterns

The final product pass used independent sellers only for market-language
patterns. It did not inspect local assets or transfer competitor claims to
FontFairy products.

| Seller/product | Observed positioning and tag-language pattern | Reusable rule |
|---|---|---|
| [Fancy Star Script — Satsuyako Design Works](https://booth.pm/ja/items/5458468) | `レトロ`, `ポップ`, `筆記体`, alternate glyphs, OpenType/TTF, Adobe-oriented usage, free specimen PDF | A script listing can lead with mood and construction, then explain alternates and format facts; do not promise alternates without supplied facts |
| [Slashed Serif — そらマート](https://booth.pm/ja/items/5168700) | Slashed motif, cyberpunk blackletter, TrueType, commercial use; related products use sharp named variants such as `Amber Nuveau`, `Dandy Laser`, `Caltrop Serif`, and `Solid Voltage` | Western fonts benefit from a distinctive construction/motif plus a style family term; do not use `cyberpunk` or blackletter without fit |
| [HISPANIA — G.Ikoma Type Foundry](https://booth.pm/ja/items/8273414) | 19th-century European print source, Copperplate/Engraving Script, historical revival, swash capitals, logos, invitations, packaging, weddings; ¥1,100 | Historical/Western products are advertised through source/era + construction + use case, not merely `western` |
| [Olympian Stephenson Extended — G.Ikoma Type Foundry](https://booth.pm/ja/items/6852452) | Victorian Display Serif, heavy serif, decorative lettering, logos, newspaper/magazine headings, antique packaging, labels, titles, T-shirts, posters; ¥1,100 | Use era and application clusters selectively; the seller explicitly warns against body text/small-size use, which is useful copy structure when supplied facts allow it |
| [あわドット — やまたな工房](https://booth.pm/ja/items/8656430) | Round dot Japanese font, LED/Y2K/推し活 positioning, two-style offer, paid ¥980 plus free experience version | Pixel/dot products can segment by visual era and audience; free/paid status must remain product-specific |
| [Kunpuh — kiyotoda_font](https://booth.pm/ja/items/6890891) | Handwritten but not overly sweet, open strokes, display use, Regular/Bold/set pricing, print/web/game/app/video/logo/doujin uses | A handwriting listing can differentiate personality from sweetness and separate weights/sets; do not infer formats or licensing |
| [Keisasa-handwriting](https://booth.pm/ja/items/6711992) | Casual/natural handwritten style, Japanese and alphabet wording, TTF, titles, logos, message cards, commercial use; ¥300 | Normal Japanese listings often pair a warm personality word with a concrete everyday use case and a format/license block |
| [春風手書きフォント](https://booth.pm/ja/items/7711699) | Warm imperfect handwriting, standard/personal-commercial, app/game embedding license, corporate full license; ¥500/¥2,000/¥5,000 | Tiered license variants are a recurring commercial pattern, but Agent 20 must repeat only the supplied FontFairy license facts |
| [ざらめフォント — vanillabeanz](https://booth.pm/ja/items/714819) | Rough handmade POP texture, Japanese/English coverage, OpenType, print/video/social/logo use, paid product plus free Latin trial | Japanese-facing copy often combines tactile construction, supported characters, formats, and a concrete trial/offer structure |

This pass also confirms that seller quality is not represented by one universal
tag vocabulary. Larger or premium-feeling shops use named style systems,
historical references, and explicit application clusters. Smaller paid sellers
often use a single emotional descriptor plus a format/license/use-case block.
Agent 20 should choose among those patterns according to the supplied font,
while keeping exact BOOTH tag selection tied to the frozen route registry.

## Permanent snapshot lock: 2026-09-06

This file is now the one and only BOOTH font activity/tag baseline for the
workflow. It is no longer a living bank, rolling cache, or refresh queue.

- `Status: FINAL FROZEN SNAPSHOT — pre-FontFairy catalog expansion`
- `Snapshot date: 2026-09-06`
- `Snapshot owner: BOOTH font listing workflow (Agent 20)`
- Future product uploads do not change the route counts, activity scores,
  seller observations, likes sample, rankings, or evidence classifications in
  this file.
- Agent 20 must not re-query banked routes during an ordinary listing run and
  must not create a second tag bank. It may still perform the supplied-font fit
  check, owned-product exclusion, and per-product copy validation.
- The per-product scratch record and the persistent rejected-term ledger are
  operational records, not alternate tag banks. They cannot replace or mutate
  this snapshot.
- New phrases discovered during an ordinary run remain keyword-only or go to
  the rejected-term ledger; they do not silently enter the permanent snapshot.
- A future research request may be reported separately outside this workflow,
  but must not create or mutate another tag bank. It may replace this file only
  when the user explicitly directs a new permanent baseline.
