# BOOTH Data Collector — Chrome Extension

Full-buffet BOOTH collector. For a given BOOTH **tag**, **browse/category**, or
**search** page it extracts, per page, every product card (name, price, likes,
position, shop) and then fetches each **item detail page** (full description,
all tags, variants + prices, formats, image count, published date). It walks
pagination automatically on your active tab and exports the lot as **CSV
(UTF-8 BOM, Excel-safe)** and **JSONL** for offline ranking/tag analysis.

Built from a live DOM analysis of `booth.pm` search-result pages:

- product cards are `li.item-card` with reliable `data-*` attributes
  (`data-product-id`, `data-product-name`, `data-product-price`,
  `data-product-position`, `data-product-brand`, `data-product-category`, …)
- likes sit in `.l-item-card-favorite .typography-14`
- pagination is `a[rel="next"]`
- list pages contain **no descriptions** — the extension fetches each item
  page separately to get description + tags + variants.

## Install (load unpacked)

1. Open `chrome://extensions`.
2. Enable **Developer mode** (top-right).
3. Click **Load unpacked**.
4. Select this folder (`extensions/booth-data-collector/`).
5. Pin the extension if you want the popup handy.

No external dependencies, no analytics, no remote servers. Everything stays in
your browser + `Downloads`.

## How to use

1. Visit the BOOTH page you want to mine, e.g.
   - Tag: `https://booth.pm/ja/items?tags%5B%5D=フォント&sort=popular`
   - Browse: `https://booth.pm/ja/browse/フォント・書体?sort=popular`
   - English: `https://booth.pm/en/browse/Fonts?sort=popular`
2. Set the sort you want **recorded** (e.g. popularity / most-liked). The
   extension does not force a sort — it *records* `sort_mode` per crawl so your
   analysis knows which ranking the `position`/`absolute_position` come from.
3. Open the popup → confirm the **Context** box shows your tag/category/sort.
4. Press **▶ Start crawl**. The extension:
   - walks pages forward on the active tab (`a[rel="next"]`, up to `Max pages`),
   - keeps unique product IDs (no duplicates across pages),
   - then fetches each item page with bounded concurrency + randomized delay
     (and stops entirely if you press **■ Stop** — the partial data stays
     exported).
5. Press **⬇ CSV** or **⬇ JSONL** to save the collected dataset to Downloads.
   Files are named `booth-{tag}-{date}-{sort}.{csv,jsonl}`.

You can close the popup mid-crawl — the service worker keeps running and
re-persists progress to `chrome.storage.local`. Re-open the popup to watch
progress and export.

## Collected fields

| Field | Where |
|---|---|
| `item_id`, `title`, `price_jpy`, `likes`, `brand`, `shop_name`, `shop_url` | list card (`data-*` + DOM) |
| `page`, `position`, `absolute_position`, `sort_mode`, `context_tag`, `context_category` | crawl context |
| `description`, `description_length`, `tags`, `tag_count`, `tag_source` | item detail page |
| `variants` (`Name:¥price \| …`), `price_min`, `price_max` | item detail page |
| `formats` (OTF/TTF/WOFF/ZIP…), `published`, `item_like_count`, `item_image_count`, `category_breadcrumb` | item detail page |
| `detail_fetched`, `detail_fetched_at`, `extractor_version` | provenance |

JSONL rows keep nested `tags` and `variants` arrays; CSV flattens them
(`tags` joined by ` | `, `variants` as `Name:¥price | …`).

## Efficiency & reliability choices

- **No images are ever downloaded** by the collector — detail pages are
  fetched as text and parsed with `DOMParser` in the background worker.
- **Rate limiting**: detail fetches run at concurrency 1–6 (default 3) with a
  randomized delay (default 900 ms); HTTP 429/5xx and network failures retry
  with exponential backoff, capped at 3 attempts.
- **20–25 s abort** per fetch so a hanging page never stalls the crawl.
- **Dedup**: products are keyed by `itemId|itemUrl`.
- **Crash-safe**: state (list + details) persists to
  `chrome.storage.local` (with `unlimitedStorage` permission) after every page
  and on heartbeats during the detail phase.
- **Sort honesty**: the extension records the actual sort of the page; it
  never fakes a "popularity" rank.

## Common failure states

- `Active tab is not a BOOTH page` → navigate your active tab to booth.pm
  before starting.
- 0 details fetched → the tab was navigated away during the crawl; re-run, or
  leave the tab alone while it works.
- `fetch failed` rows in the popup log → normally 429/network; re-run the
  crawl (persisted state is overwritten on a new start) or lower concurrency /
  raise delay.

## Wiring into the analysis pipeline

The exported CSV is meant to be joined (on `item_id`) with the FontFairy rank
CSV and fed to the number-cruncher:

```bash
python3 bin/analyze_booth_collection.py \
  --collection ~/Downloads/booth-*.csv \
  --rank ~/Downloads/booth-rank-papermoonstudio-2026-09-08.csv \
  --bank outputs/research/booth-font-tag-bank.md
```

That script scores tag/likes/price/description signals per rank band, finds
tags used by high-liked items that FontFairy items don't use, checks them
against the frozen tag bank, and writes
`outputs/research/booth-collection-analysis-{date}.md`.

Note: `booth-rank-*.csv` contains only FontFairy's own items. The extension
crawl covers whatever page you point it at (typically the whole Fonts
category / a tag), so the two datasets intersect at FontFairy items and the
crawl adds every competitor around them.

## Two collection paths (extension vs. headless CLI)

BOOTH hydrates tags, like counts, and wish-list buttons client-side: the
server HTML ships empty containers (`<div id="js-item-tag-list"></div>`,
`.l-item-card-favorite`) and a real browser fills them in after load. This is
the only reason the two collectors below behave differently:

| | **This extension** | **Headless CLI** (`bin/collect_booth_category.py`) |
|---|---|---|
| Where it runs | Your live Chrome tab | Local Python process, no browser until `--browser` |
| List cards (rank, price, shop) | ✅ via live DOM | ✅ via server HTML (`data-*`, verified identical) |
| Card like counts | ✅ hydrated DOM (`.l-item-card-favorite .typography-14`) | ❌ always 0 (server HTML) |
| Item descriptions | ✅ detail fetch | ✅ detail fetch |
| Item tags | ⚠️ only when the item page is loaded as a live tab; the background `fetch()` gets un-hydrated HTML | ✅ with `--browser` (headless Chromium hydrates `#js-item-tag-list`); ❌ on plain raw-HTTP runs |
| Item like counts | ⚠️ same tab-hydration caveat | ✅ with `--browser` (`#js-item-wishlist-button .typography-14`) |
| Full-category "all pages" walk | Manual (tab must stay focused, page-by-page) | ✅ automatic via `a[rel="next"]`, resumable, can run overnight |
| Output | CSV/JSONL in Downloads | CSV/JSONL/manifest/state in `outputs/research/booth-live-collector/{date}/` |

**Recommendation:** for the full Fonts-category crawl, use the headless CLI
with `--browser` — it walks every `?sort=popular` page automatically, ranks by
`absolute_position`, and captures the champion zone's real tags + likes:

```bash
# venv deps:
uv pip install --python .venv/bin/python httpx lxml playwright

# full category, most-popular first, 200 champion details browser-hydrated:
python3 .venv/bin/python bin/collect_booth_category.py \
  --start "https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?sort=popular" \
  --detail-limit 200 --browser \
  --out outputs/research/booth-live-collector/2026-09-08/fonts-popular
```

The extension remains the fastest tool when you want **real wish-list counts
for every card on a bounded page set** (it reads the hydrated `.typography-14`
without loading each item page in a browser). Both share the same CSV schema,
so either output feeds `bin/analyze_booth_collection.py`.