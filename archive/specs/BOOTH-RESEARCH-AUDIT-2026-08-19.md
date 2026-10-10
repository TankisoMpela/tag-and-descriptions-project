# BOOTH Research and Provider Audit - 2026-08-19

## Scope

This audit covers BOOTH discovery for paid Western/Latin fonts, the current
research providers and repository helpers, and the evidence gates used by
`agent-20-booth-fonts-specialist.md`. It does not claim buyer search volume,
sales volume, conversion rates, or ranking causality.

## Current live findings

- The exact public `欧文フォント` result route returned 122 products during the
  Firecrawl run on 2026-08-19.
- The `フォント・書体` category route for the same tag returned 121 products.
- The related-tag surface exposed `font`, `書体`, `フォント`, `文字`,
  `商用利用可`, `オリジナルフォント`, `フォント・書体`, `フォント 商用`,
  and `書体・フォント`.
- A current English-facing search surface returned paid and free font products;
  this confirms English/Western fonts are ordinary BOOTH inventory, not an
  unusable niche. The mixed result must still be filtered for paid status and
  font-category relevance.
- A current paid product, Wayvair, was rendered successfully by Crawl4AI at
  `https://booth.pm/ja/items/4894970`. Its page exposed Japanese and English
  copy, price, OpenType wording, commercial-use wording, update information,
  usage restrictions, and related paid font products.
- A current paid 39-font Western collection was extracted by Firecrawl at
  `https://booth.pm/ja/items/637274`. Its page exposed a large specimen gallery,
  paid status, and the collection positioning.

These are coverage and content observations. They are not demand scores.

## Provider assessment

| Provider or tool | Best BOOTH role | Strength | Limitation / rule |
|---|---|---|---|
| Firecrawl | Direct page extraction | Clean counts, related tags, product copy, seller/category/page content | A consent or empty shell is a failed content fetch; do not treat HTTP 200 as evidence |
| Crawl4AI | Independent rendered extraction | Recovered full Japanese/English product copy and related products on Wayvair | Browser/runtime can fail; assigned 40% workload, not a Firecrawl retry |
| Serper | URL and phrase discovery | Found relevant paid products and current Japanese title patterns quickly | Snippets are discovery only; must fetch before tag evidence |
| Exa | Semantic recall | Found relevant Japanese Western-font products and alternate phrasing | Scores are not demand; mixed free/paid and duplicate-shop results require filtering |
| Tavily | Optional broad discovery | Configured MCP integration and key rotation responded successfully | Not exposed in the current Codex tool list; not suitable as exact-tag evidence |
| Google Suggest helper | Language expansion | Can reveal general Japanese/English query wording | BOOTH-prefixed queries are Google Suggest, not BOOTH autocomplete; cached zeroes do not reject live BOOTH terms |
| Web search | Official-source verification | Found BOOTH's Japanese help page explaining keyword and multi-tag behavior | Search results still require direct-page confirmation for marketplace evidence |
| Webfetch | One-page fallback | Useful when the assigned crawler fails | One attempt per assigned URL; never use it to reassign the whole batch |
| Playwright / Google Chrome | Authenticated editor inspection | Potentially useful for the seller-side autocomplete, visible tag counter, and editor behavior | Requires an authenticated session and explicit seller-side inspection; public research cannot infer its state |

The current provider smoke test also exposed an important runtime boundary: in
this Codex session Serper, Exa, Firecrawl, and the public web search connector
were callable; the exact BOOTH query returned relevant paid candidates through
Serper and Firecrawl, while Exa returned no results for that narrow query. The
configured Tavily script exists in the OpenCode configuration but no Tavily tool
is exposed in the current callable Codex inventory, so it remains optional
discovery rather than a required stage. The 60/40 allocator assigned three of
four current BOOTH URLs to Firecrawl and one to Crawl4AI. The seller editor URL
redirected to Pixiv sign-in, so autocomplete, tag-chip limits, and editor-side
acceptance remain unverified until an authenticated seller session is available.

The OpenCode log is useful for operational caution but not for estimating a
Firecrawl request failure rate: it contains historical runs and unrelated MCP
startup/model-network events. In the current log snapshot there are 181 generic
timeout/deadline mentions; provider-labelled filtering finds 2 Firecrawl, 3
Tavily, 3 Serper, and 4 Exa timeout/error-associated lines, while the Aug 19
session shows 32 provider connection events. These counts are not request-level
failure rates. The actionable rule remains one assigned provider attempt, then
one WebFetch fallback for that URL, with the failure recorded instead of
hammering Firecrawl.

## Authenticated BOOTH editor finding

The signed-in seller editor was subsequently inspected read-only on an existing
paid font edit page. The tag field is labelled `add Tag` and exposes an ARIA
autocomplete listbox. `英字フォント` produced a matching suggestion. A custom
English phrase (`fantasy font`) and the compound `フォント, フォント・書体`
produced no suggestion options, but BOOTH still displayed an explicit Enter
action to add the typed value. This proves that “no autocomplete” does not mean
“not allowed.” It also means the agent must separate three signals: editor
wording suggestion, exact public-tag existence, and current relevant page life.
The inspected page showed no visible numeric tag counter or rejection limit;
the 20-30 selected-tag range therefore remains our internal evidence-led range,
not an observed BOOTH maximum. The separate `おすすめタグ（履歴）` list is
account/editor recommendation history and should not be treated as current
product evidence by itself.

## Stronger validation model

Every final tag should have a row containing:

1. exact BOOTH tag URL;
2. `フォント・書体` category URL for the same tag;
3. overall exact-tag count, if exposed;
4. font-category count, if exposed;
5. current paid-product count and distinct-seller count among inspected pages;
6. page-life status and assigned/actual provider;
7. evidence tier and product-fit reason.

The strongest tags are not merely large-count tags. The preferred order is:

`product fit -> exact live tag -> font-category relevance -> active page -> paid
product repetition -> distinct-seller diversity -> co-occurrence -> overall
coverage count -> generic wording expansion`.

The official Japanese help page says BOOTH keyword search can use product name,
description, shop name, and creator name, while multiple selected tags are
combined. Therefore the agent must keep three different things separate:

- selected exact BOOTH tags;
- title/description keyword phrases that are useful but not confirmed tags;
- rejected or low-activity tags recorded in the persistent ledger.

Two-tag searches are useful co-occurrence evidence, but a phrase does not become
a selected compound tag unless that compound has its own exact live tag route.

## Japanese source hierarchy

1. BOOTH's Japanese help/search documentation for platform behavior.
2. `フォント・書体` category pages and exact-tag category routes.
3. Exact tag pages and related-tag chips.
4. Japanese keyword-search routes with `sort=new`, `in_stock=true`, and visible
   category filters.
5. Comparable paid product pages from distinct shops.
6. Serper/Exa/Tavily discovery, followed by direct-page confirmation.
7. Google Suggest only for alternate wording.

## Japanese creator-side analytics tools

The research found Japanese-facing tools for analyzing a seller's own BOOTH
CSV exports, including [BOOTH Sales Visualizer](https://github.com/lemoneru/BOOTH-Sales-Visualizer)
and [BoothViz](https://booth.pm/ja/items/6575925). These can help later with
our own title/tag experiments after sales data exists, but they do not expose
market-wide BOOTH keyword volume or competitor tag demand. BOOTH's official
help also says page access counts are not shown directly in BOOTH and can be
measured with Google Analytics instead:
https://booth.pixiv.help/hc/ja/articles/231284988-%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B9%E6%95%B0%E3%82%92%E7%A2%BA%E8%AA%8D%E3%81%99%E3%82%8B%E6%96%B9%E6%B3%95%E3%81%8C%E7%9F%A5%E3%82%8A%E3%81%9F%E3%81%84

The practical strategy is therefore: public BOOTH route coverage for
pre-publication tag selection, then seller CSV and analytics data for
post-publication learning. Do not purchase or add an external BOOTH analytics
service expecting hidden search-volume data unless it can show a documented
source and measurement method.

## Important exclusions

The agent must not count the current product, previous PaperMoon products, or
the seller's own shop as independent competitor repetition. It must also filter
free products out of paid-product corroboration, while retaining them only as
language/presentation evidence when relevant.

## Implemented changes

- Creative Market is paused in the default font workflow; its standalone agent
  remains available.
- The default chain is now MasterBundles -> Cubebrush -> BOOTH.
- BOOTH agent instructions now define provider roles, official Japanese search
  behavior, recent-page checks, distinct-seller corroboration, co-occurrence
  checks, and keyword-vs-tag separation.
- BOOTH evidence output now requires a 10-column provider/activity-aware table.
- `bin/validate_booth_listing.py` rejects selected-tag evidence rows that lack
-  the expanded provider/activity/source structure, and now rejects rows whose
  selected tag, exact-tag route, or font-category route does not match the row.

## Sources used

- https://booth.pixiv.help/hc/ja/articles/57495772454809-%E5%95%86%E5%93%81%E3%82%92%E3%82%AD%E3%83%BC%E3%83%AF%E3%83%BC%E3%83%89%E3%81%A7%E7%B5%9E%E3%82%8A%E8%BE%BC%E3%82%93%E3%81%A7%E6%8E%A2%E3%81%99%E6%96%B9%E6%B3%95%E3%81%8C%E7%9F%A5%E3%82%8A%E3%81%9F%E3%81%84
- https://booth.pm/ja/items?tags%5B%5D=%E6%AC%A7%E6%96%87%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88
- https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?tags%5B%5D=%E6%AC%A7%E6%96%87%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88
- https://booth.pm/ja/items/4894970
- https://booth.pm/ja/items/637274

## 2026-08-19 seller and saturation audit

### What BOOTH can and cannot tell us

BOOTH exposes result and category coverage on public routes, but it does not
expose a market-wide monthly visitor count or per-tag search-volume metric.
There is therefore no honest number of monthly visitors at which a tag becomes
"saturated." The workflow must treat exact-tag count, font-category count,
recent visible products, paid-font repetition, and distinct-seller diversity as
competition/coverage signals only. They are not demand, traffic, sales, or
conversion estimates.

The current practical bands are:

- broad short-tail roots such as `font`, `フォント`, `書体`, `文字`, and
  `オリジナルフォント`: strong reach, high competition, and insufficient
  alone for a Western display font;
- core mid-tail language such as `欧文フォント`, `英語フォント`,
  `英字フォント`, and `英数字フォント`: more precise Latin/English-font
  discovery with materially less coverage than the generic roots;
- style/use long-tail such as `display font`, `ディスプレイフォント`,
  `フォント 商用`, or a supported style term: lower coverage but stronger
  intent when the product genuinely matches.

The observed route snapshots are consistent with this: `欧文フォント` had
roughly 115 overall results in the captured route, the `フォント 英語`
exact-tag route showed roughly 332 mixed results, and the font-category search
for `フォント 英語` showed roughly 516 results. These are not comparable
monthly volumes; they are route coverage snapshots and can change.

### What current successful sellers are doing

The visible paid-font examples show several repeatable strategies:

- Tabun's Wayvair family uses a Japanese/English title pair (`欧文フォント
  「Wayvair」 | Wayvair Font`), a clear OTF and Latin-glyph statement, a
  commercial-use explanation, and a family of related products at a consistent
  price. This is a catalogue and trust strategy, not a tag-stuffing strategy.
- FontStyles sells a 39-font Latin collection as a value bundle, with a large
  specimen gallery. This captures collection/value intent rather than relying
  only on the broad `font` root.
- Lemonin combines Japanese product language with selective English terms such
  as `font 英語`, `font design`, and `font 商用`, alongside native style and
  commercial-use terms. The English is supporting discovery, not a duplicated
  full English page.
- Other visible paid catalogues, including daybreakrain/10R11-style series,
  repeatedly publish related weights and styles at accessible price points.
  G.Ikoma's current pages use bilingual style descriptors such as
  `Historical Revival Typeface`, `display font`, and `Old English` while
  retaining Japanese category and license language.

This supports our direction for an English/Latin font: Japanese-first title and
description, the exact font name first, selective English style/use phrases,
native BOOTH font terms, and a product-specific family of tags. English
alphabet fonts are not inherently too niche for BOOTH; they are found through
Japanese category terms plus English style phrases and bilingual product names.

### Exactly-30 decision and validation quality

The internal output obligation is now exactly 30 selected BOOTH tags. The first
positions remain the strongest product-fit and Tier A/B tags; positions 21--30
are a required evidence-backed expansion block, not filler. If 30 defensible
tags cannot survive the second expansion and page-life pass, the listing is
blocked rather than padded with generic web keywords.

Validation is strong enough for pre-publication selection because every chosen
tag must have the exact-tag route, the `フォント・書体` route, a page-life
check, and evidence of relevant paid products/sellers where available. It is
not a substitute for BOOTH demand analytics because BOOTH does not publish
that metric. The likely missed tags are therefore reduced at the vocabulary
and coverage level, but cannot be called negligible in terms of sales demand.
Post-publication seller access/analytics is the only way to learn which of the
validated tags actually brings visits and purchases.
