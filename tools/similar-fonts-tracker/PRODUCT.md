# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Electron with a local HTML/CSS/JavaScript renderer; no remote backend.

## Users

The font seller tracking marketplace products and the Pinterest preparer that records confirmed marketplace product links.

## Product Purpose

Keep two local font spreadsheets: Creative Market Similar Fonts review and Creative Fabrica source-font search review.

## Product Positioning

The Creative Market sheet derives Similar Fonts pages from exact product URLs. The Creative Fabrica sheet shows each original source font beside its prepared name, any confirmed source-font listing, and the prepared product listing. Product links and source-match results come from the Pinterest preparer registry; human marks stay local.

## Operating Context

Products are recorded in `outputs/pinterest/registry.json` by the Pinterest preparer. The tracker reads that registry locally, derives source family names from preparation reports, and stores human review marks in local JSON files. The seller opens links in a browser and marks rows in the app.

## Capabilities and Constraints

- Show the prepared font name beside its source font name, followed by the Creative Market product URL, Similar Fonts URL, and similarity marks.
- Green means no similar font found; red means a similar font found. Clicking the selected mark clears it.
- Dealt is green or amber, appears only after red, and can also be cleared by clicking it again.
- Show `No CM link yet` when there is no confirmed Creative Market product URL; retry discovery on a later Pinterest preparer run.
- Derive the Similar Fonts URL from the numeric Creative Market product ID.
- The Creative Fabrica sheet shows source font family, prepared/repackaged name, confirmed source-font item URL, and prepared font item URL.
- The Pinterest preparer searches Creative Fabrica for the original source font and records either a confirmed direct item URL or a checked no-match result.
- Creative Fabrica Dealt is green or amber and may be set only when a source-font item URL is confirmed; clicking the selected mark clears it.
- Both sheets show ten fonts per page with larger rows.
- Preserve review decisions when product links are refreshed.
- Creative Fabrica has no confirmed dedicated Similar Fonts route; its sheet tracks source-font listings, not similarity recommendations.
- Do not publish, scrape, or modify marketplace products.

## Evidence on Hand

The Pinterest registry is the source of marketplace links and agent search results. Creative Market uses `/similar/fonts/{product_id}` for its Similar Fonts pages. Creative Fabrica product pages show generic recommendations but no confirmed dedicated similar-font route.

## Product Principles

- Keep confirmed product links traceable to the Pinterest registry.
- Make pending review obvious and result states unmistakable.
- Keep the review lightweight and local.
