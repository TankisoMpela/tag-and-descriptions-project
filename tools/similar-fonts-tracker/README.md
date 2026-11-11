# Similar Font Review

A local Electron spreadsheet with Creative Market and Creative Fabrica tabs.
Both sheets show ten fonts per page with larger rows. On the Creative Market
sheet, green means no similar font found and red means a similar font was
found; clicking the selected mark clears it. Dealt marks are green or amber,
appear only after a red Similar mark, and also clear on a second click. Missing
Creative Market links show `No CM link yet`.

The Creative Fabrica sheet shows the source font family name, its prepared
repackage name, a confirmed source-font listing URL, and the prepared font's
Creative Fabrica product URL. The Pinterest preparer records a direct source
match or a checked no-match result; unchecked rows say `Not searched`. Dealt is
available only when a source-font link is confirmed. Creative Fabrica Dealt marks are stored separately in
`data/creative-fabrica-reviews.json`; Creative Market marks remain in
`data/reviews.json`.

The Pinterest preparer adds links and source-font search results to
`outputs/pinterest/registry.json`. This app reads that registry and updates an
open window when it changes. The preparer also runs the sync command below.
Creative Fabrica's generic recommendations are not a dedicated Similar Fonts
page; its sheet instead tracks whether the original source font has a direct
Creative Fabrica item listing.

## Run

From this directory:

```bash
npm install
npm start
```

From the project root, the Pinterest preparer runs:

```bash
node tools/similar-fonts-tracker/scripts/sync-registry.cjs
```

## Inspect the review data

From this directory:

```bash
node cli.cjs summary
node cli.cjs list
node cli.cjs show <slug>
node cli.cjs cf-summary
node cli.cjs cf-list
node cli.cjs cf-show <slug>
node cli.cjs set-cf-dealt <slug> <green|amber|clear>
```

`summary` reports missing product links and the remaining Similar/Dealt marks.

Only Creative Market item URLs with numeric product IDs appear. Seller and
search pages are ignored.
