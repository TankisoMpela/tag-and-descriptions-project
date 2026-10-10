# BOOTH Rank Tracker — Chrome extension

Finds **where all of your shop's products rank** on a BOOTH tag/category search
page: which result page each product appears on, its in-page position, and its
global rank across the whole tag listing.

## How it works

- Open any BOOTH tag or category listing page, for example:
  - `https://booth.pm/en/browse/Fonts?tags%5B%5D=font`
  - `https://booth.pm/en/items?tags%5B%5D=フォント`
  - `https://booth.pm/ja/browse/Fonts?tags%5B%5D=font`
- Click the **🏷 Rank** button (bottom-right).
- Enter your shop slug (default `papermoonstudio`) and the max pages to scan.
- Click **Scan tag rankings**.

The extension reads the current page (server-rendered `li.item-card` elements
with `data-product-brand`, `data-product-position`, `data-product-id`, …),
then fetches each remaining page same-origin (with a polite delay), parses the
cards, matches every card whose shop brand equals your slug, and reports:

| Column | Meaning |
|---|---|
| **Global** | Rank across the entire tag listing — `(page − 1) × 60 + position` |
| **Page** | Which result page of the tag the product appears on |
| **Pos** | Position within that page (1–60) |
| **Item** | BOOTH item ID |
| **Title / Shop** | Product title + shop display name |
| **Price** | List price in JPY |

Results auto-sort by global rank. **Export CSV** downloads a BOM-prefixed CSV
(Excel-safe for Japanese titles).

## Verification evidence (2026-09-08)

All selectors and logic were validated against live BOOTH page HTML in a
headless DOM harness:

- Tag URL format confirmed: `?tags%5B%5D={tag}` (the `tags[0]=` form is
  ignored by BOOTH's server).
- `per-page` card count = **60**; positions are 0-based and reset per page.
- Pager exposes `a.nav-item.last-page` (`?page=28`) → total page count.
- Pages 2..N are server-rendered and fetchable same-origin.
- Full test results: 63/63 assertions passing.

## Install (developer mode)

1. Open `chrome://extensions`.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked** and select the `extensions/booth-rank-tracker/`
   folder.
4. Browse to any BOOTH tag/category listing page and click **🏷 Rank**.

A packaged ZIP is also available at
`/home/tankiso/Downloads/booth-rank-tracker-extension.zip`.

## Settings

- **Shop slug or URL** — either `papermoonstudio` or the full shop URL
  `https://fontfairy.booth.pm/` (normalized automatically). This is the
  `data-product-brand` value used to identify *your* products.
- **Max pages** — safety cap (1–500, default 50) so very large tags cannot
  hammer the server. Full coverage for the `font` tag (28 pages) fits under
  the default.

## Notes & limitations

- Rankings are relative to the listing order of the exact URL/tag/sort you
  open. Changing the sort order changes the results.
- Only server-rendered listing pages are scanned; BOOTH item detail pages and
  shop front pages are ignored (the button only appears on listing routes).
- Newly published items may need time to appear in tag search results.
- Politeness delay between page fetches is 350 ms by default.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | MV3 manifest, storage permission, BOOTH host permissions |
| `content.js` | Scan logic + in-page panel (shadow-DOM UI, no background worker) |
| `icons/icon{16,48,128}.png` | Extension icons |