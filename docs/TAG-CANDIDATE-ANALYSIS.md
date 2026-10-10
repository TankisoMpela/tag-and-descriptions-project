# Actionable analysis — validating the harvest's tag candidates

Source: `booth.db` (4,958 items, 64,201 tag assignments) cross-referenced with
the one-time harvest in `outputs/research/booth-demand/`.

---

## 1. The app terms fail as tags — but that is not the end of them

The harvest surfaced app terms as its headline finding. Validated against the
census, they do **not** hold up as tags:

| term | font items | median likes | top-300 wins |
|---|---:|---:|---:|
| `photoshop` | 91 | 34.0 | **0** |
| `illustrator` | 80 | 32.0 | **0** |
| `イラストレーター` | 81 | 34.0 | 1 |
| `イラレ` | 74 | 34.5 | **0** |
| `フォトショ` | 76 | 35.5 | 1 |
| `プレミア` | 76 | 9.0 | 2 |
| `procreate` | 8 | 25.5 | **0** |
| `クリスタ` | 1 | 36.0 | **0** |

And these are **not BOOTH tags at all**: `canva`, `アイビス`, `ibispaint`,
`capcut`, `filmora`, `figma`, `obs`, `vtuber`, `blender`, `unity`,
`powerpoint`, `clip studio`, `クリップスタジオ`, `アイビスペイント`.

**Verdict: do not tag them.** Median likes 32–36 against the narrow cluster's
350–420, and zero top-300 winners. They are a *demand* signal, not a *tag*
signal — the distinction matters and I got it wrong two turns ago when I framed
them as a tag opportunity.

**But they are genuinely valuable in descriptions.** Autocomplete proves people
type `フォント 商用利用 クリスタ` and `canva フォント 商用利用`. BOOTH indexes
description text, so saying the font works in those tools reaches those
searchers without spending a tag slot on a tag that does not win.

---

## 2. What the harvest *did* justify: searched AND winning AND unused

Cross-referencing every suggestion against every census tag, keeping only tags
with font-category presence, real engagement, and a top-300 win rate:

Route counts (BOOTH-wide competition) read 2026-09-22:

| tag | font items | median likes | win% | **route count** | banked? |
|---|---:|---:|---:|---:|---|
| **`serif`** | 8 | **407.5** | **37.5%** | **6** | **no** |
| **`セリフ体`** | 8 | **407.5** | **37.5%** | **5** | **no** |
| `筆記体` | 26 | 171.5 | 15.4% | 42 | **no** |
| `手書き風フォント` | 40 | 92.5 | 27.5% | 45 | **no** |
| **`欧文`** | 62 | **346.5** | **22.6%** | **57** | **no** |
| **`英字`** | 50 | **237.5** | **24.0%** | **150** | **no** |
| `セリフ` | 14 | 118.5 | 21.4% | 244 | **no** |
| `商用利用可能` | 161 | 53.0 | 16.8% | 4,044 | **no** |
| `おしゃれ` | 12 | 76.5 | 16.7% | **6,734** | **no** |
| `商用可` | 255 | 65.0 | 11.4% | 9,434 | **no** |

`おしゃれ` and `商用可` are struck from the recommendation: 6,734 and 9,434
BOOTH-wide makes them saturated and generic, whatever their win rate.

**Every one of these is absent from the 41-row bank.** That is the real gap the
harvest exposed — not the app terms.

The standouts share the narrow-high-yield profile the audit already identified:

- **`serif` / `セリフ体`** — 8 items, **407.5 median likes, 37.5% top-300 win**.
  Tiny, uncontested, and directly applicable to any serif product. The same
  term in English and Japanese, so both can be carried.
- **`欧文`** — 62 items, 346.5 median, 22.6%. The plainest possible description
  of what a Latin font is, and the bank carries `欧文フォント` and `欧文書体`
  but **not `欧文` itself**.
- **`英字`** — 50 items, 237.5 median, 24.0%. Same pattern: bank has
  `英字フォント`, not `英字`.

### Two caveats, and they matter

**a. n is tiny.** At n=8 a single winner moves the rate by 12.5%. `serif`'s
37.5% is 3 wins. The **median likes** (407.5) corroborates it and is far above
the saturated vocabulary's 15–22, but treat the rate as suggestive.

**b. Low competition may mean no traffic, not opportunity.** `serif` has 6
BOOTH-wide items and `セリフ体` has 5. That could be an unclaimed space, or it
could be a tag nobody browses. **The route count alone cannot tell these apart**
— and I have no data that does. Compare `欧文` (57 items, 346 median likes),
which is small but demonstrably populated by items that perform.

`欧文` and `英字` are the safest additions: real competition exists, real
engagement exists, and they are the plainest words for what the shop sells.
`serif`/`セリフ体` are the speculative ones — cheap to add, unproven.

---

## 3. The count question — raising 18 → 28 is solving a problem that isn't there

The proposal was to raise the tag ceiling so the new candidates fit. Three
measurements say no:

**a. There is already room.** Listings carry a **median of 14 tags** against a
**cap of 25** — **11 free slots per listing**. Nothing needs to be "fitted in".

**b. The constraint is the floor, not the ceiling.** The validator's
`MIN_BOOTH_TAGS = 18` is what listings fall short of (45 of 48 are under it).
Raising 18 → 28 would move the *floor* up and push every listing further below
it, not create room.

**c. More tags do not buy visibility.** Across all 4,958 items:

| feature | Spearman vs likes |
|---|---:|
| `absolute_position` | −0.970 *(rank is defined by likes)* |
| `price_jpy` | −0.288 |
| `desc_len` | +0.107 |
| **`tag_count`** | **+0.029** |

Essentially zero. The **top 2026-published item has 2 tags.**

**So: add the tags that clear the gate; they fit in the existing headroom.**
Raising the ceiling to make room inverts the logic — the tag should earn its
slot. The spec agrees: *"Do not pad with near-synonyms… merely to reach 20."*

---

## 4. What to apply where

| finding | tags | description |
|---|---|---|
| `serif` / `セリフ体` / `セリフ` | **yes** — for serif products | also natural in copy |
| `欧文` / `英字` | **yes** — any Latin font | natural in copy |
| `筆記体`, `手書き風フォント` | **yes** — only for script/handwritten | — |
| `商用利用可能` | **yes** | — |
| `おしゃれ` | fit-dependent; only if the letterforms support it | — |
| app terms (クリスタ, イラレ, Photoshop, canva, procreate…) | **no** — 0 winners, many not real tags | **yes** — name the tools; BOOTH indexes description text |
| anxiety terms (商用利用 バレる, どこまで, 確認 方法, 規約) | no | **yes** — answer the doubt; a hesitant buyer does not convert |
| free terms (無料/フリー) | **never** on a paid listing | — |
| `配信素材` | **no** — 33,600 BOOTH-wide and not font-specific | — |

---

## 5. Recommended action

1. **Add `serif`, `セリフ体`, `欧文`, `英字`, `セリフ`, `商用利用可能` to the
   bank** — they are searched, they are winning, and none is banked. Route
   counts still need reading for `serif`/`セリフ体`/`欧文`/`英字`/`セリフ`.
2. **Do not change the ceiling.** The candidates fit in the existing 11-slot
   headroom.
3. **Leave the app terms out of tags** and put them in descriptions instead,
   alongside a direct answer to the licensing questions.
4. **Verify `serif` and `セリフ体` on a live listing** before treating 37.5% as
   settled — n=8 is thin.

---

## 6. The app-term challenge, answered properly

### Translation

| tag | meaning |
|---|---|
| `ワード フォント` / `word フォント` | Word font |
| `パワポ フォント` | PowerPoint font (パワポ = the standard colloquial abbreviation) |
| `canva フォント` | Canva font |
| `procreate フォント` | Procreate font |
| `クリスタ フォント` | Clip Studio Paint font (クリスタ = the standard abbreviation for CLIP STUDIO) |
| `アイビス フォント` | ibisPaint font (アイビス, usually アイビスペイント) |
| `イラレ フォント` | Illustrator font (イラレ = colloquial) |
| `illustrator フォント` | Illustrator font |
| `photoshop フォント` | Photoshop font |
| `figma` / `blender` / `filmora` / `affinity` `フォント` | Figma / Blender / Filmora / Affinity font |

### Do these exist as BOOTH tags? No — proven with a control

Fetching the exact-tag route shows BOOTH uses two different page shapes:

| query | page title |
|---|---|
| `書体ダウンロード` (a real tag) | `書体ダウンロードに関する**人気の同人グッズ174点**を通販できる!` |
| `クリスタ フォント` | `クリスタ フォントの同人通販 - BOOTH` — **no count** |
| `イラレ フォント` | `イラレ フォントの同人通販 - BOOTH` — **no count** |
| `photoshop フォント` | same shape, no count |
| `canva フォント` | same shape, no count |
| `procreate フォント` | same shape, no count |
| `illustrator フォント` | same shape, no count |
| `ワード フォント` | same shape, no count |

**A real tag yields `人気の同人グッズN点`. A non-existent tag yields `の同人通販` with no
number.** All 14 `<app> フォント` compounds take the second form. They are not BOOTH
tags, so they cannot be selected.

The **bare** app terms that do exist still fail on performance: `photoshop` 91 font
items / median 34.0 / **0** top-300 wins; `illustrator` 80 / 32.0 / **0**; `イラレ`
74 / 34.5 / **0**; `フォトショ` 76 / 35.5 / 1; `イラストレーター` 81 / 34.0 / 1.

### Are they searched? Yes — but not on BOOTH

**Google autocomplete** (`outputs/research/booth-demand/demand-signals.md`) proves the
demand is real:

- `booth フォント クリスタ`, `booth フォント イラレ`, `booth フォント 手書き クリスタ`
- `フォント 商用利用 クリスタ`, `クリスタ フォント 商用利用 ipad`
- `フォント デザイン canva`, `canva フォント 商用利用`, `canva フォント 商用利用 確認方法`
- `デザインフォント クリスタ`, `booth フォント 使い方 イラレ`

**BOOTH/pixiv has no autocomplete to check against.** Tested via Firecrawl, which
renders past Cloudflare:

| endpoint | result |
|---|---|
| `booth.pm/ja/search/suggest?q=クリスタ` | 368 KB search page, **0 suggestion nodes**, query term not even present |
| `booth.pm/ja/search/suggest.json?q=font` | 131 KB search page, **not JSON** |

So the only typed-query source for this market remains Google.

### The resolution

**Searched, but not taggable.** The demand is real and Google proves it; the tags do
not exist. That is precisely why these belong in the **description** — BOOTH indexes
description text, so naming the tools reaches those searchers without spending a tag
slot on a tag that cannot be selected.

### Correction: I reported a rate limit as a finding

My first pass reported all 16 compounds as `FAILED` and I treated "not in the census"
as the result. The actual cause was **Firecrawl's 50-request/minute cap** — every call
returned `Rate limit exceeded ... Remaining (req/min): 0`. Absence from the census and
absence from BOOTH are different claims, and only the second is now established, via
the control above run at a throttled pace with 14s spacing.
