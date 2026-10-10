# BOOTH Dashboard Download Count & Product Details — Chrome Extension

Extracts **full product details** plus **per-variant download counts** from your
BOOTH seller dashboard (`https://manage.booth.pm/items/`) with a toolbar button
and popup UI.

## Features

- **Toolbar button** — click the extension icon in Chrome to open the popup.
- **Scan Dashboard** — reads every product card on the current dashboard page:
  - Title
  - Public item URL + edit URL
  - Sales / stock number
  - Tags
  - Variants / prices
  - **Per-file download counts** (fetched from each item's edit page with your
    logged-in session — the same data the old bookmarklet showed, now in a UI).
- **📋 Copy** — copy a readable plain-text summary to the clipboard.
- **💾 Export CSV** — download a spreadsheet (one row per file variant).
- **Collapse / Expand** — collapse long lists.

## Install (Chrome, Manifest V3, unpacked)

1. Open `chrome://extensions`.
2. Toggle **Developer mode** ON (top-right).
3. Click **Load unpacked**.
4. Select this folder:
   ```
   extensions/booth-download-count/
   ```
   (or wherever you copied it — pick the folder that contains `manifest.json`).
5. The extension appears. Pin it to the toolbar if you like (puzzle icon → pin).
6. Go to **`https://manage.booth.pm/items/`** and **make sure you are logged in**
   as the seller.
7. Click the extension icon → **Scan Dashboard**.
8. Review the extracted cards, then **Copy** or **Export CSV**.

## Firefox (optional)

The code is a standard WebExtension and works in Firefox with a small manifest
change:
- Use a `manifest_version: 2` variant, or
- Add `"browser_specific_settings": { "gecko": { "id": "..." } }` and load via
  `about:debugging#/runtime/this-firefox` → Load Temporary Add-on → pick
  `manifest.json`.

## Requirements

- A **Chrome browser** (or Chromium-based browser: Edge, Brave, etc.).
- **Logged-in BOOTH seller session** in Chrome.
- You must be on the **seller items dashboard** page
  (`manage.booth.pm/items/`), not the public storefront.

## Privacy

- The extension only reads the current BOOTH dashboard tab.
- Download counts are fetched from `manage.booth.pm` using your existing
  session. No data leaves your browser and nothing is sent anywhere else.

## Troubleshooting

- **"Could not read dashboard cards"** — make sure you're on
  `manage.booth.pm/items/` (the seller list, not the shop page) and logged in.
- **Download counts empty** — BOOTH may have changed the edit-page markup, or
  the item's edit page needs a moment to render its file table. Re-scan. If a
  single item shows nothing while others work, that item may have no uploaded
  files viewable to the script.
- **Reload after edits**: after changing `content.js` or `popup.js`, reload the
  extension at `chrome://extensions` (↻), reopen the popup, and re-scan.
- If BOOTH updates its DOM, the card selectors (`.cell.item-name-with-stock`,
  title prompts, `.dashboard-items-tags`) may need updating in `content.js`.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | MV3 manifest (permissions, icons, popup) |
| `content.js` | Extracts dashboard card fields AND fetches per-file download counts via same-origin hidden iframes to each item's edit page |
| `popup.html` / `popup.js` | Toolbar popup UI (scan, copy, CSV) |
| `icons/` | 16/48/128 toolbar icons |
