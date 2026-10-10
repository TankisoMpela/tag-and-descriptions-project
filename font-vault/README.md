# Font Vault

Font Vault is a local desktop reviewer for large font directories.
It does not upload fonts or use a browser. It scans filenames and metadata, then
renders only the font you select or reach with **Next**.

## Run

From the project root:

```bash
python3 font-vault/font_vault.py
```

It uses the PySide6 desktop runtime and does not open a browser. Install the
project dependencies first with `uv sync` or `pip install -r requirements.txt`.

Choose **Open directory**. The app supports TTF, OTF, WOFF, and WOFF2 files,
including nested folders. Saved directories appear in **Load recent**, and each
source behaves as its own saved vault with its own search/filter position.

Use **Load recent** to reopen a saved directory and **Unload** when finished.
Unloading clears the active index from memory but keeps review statuses, cached
previews, and the saved vault entry. Directory indexing runs in the background;
the queue shows at most 2,000 rows at a time with paging, while search still
narrows the full indexed collection.

## Architecture & Persistence (SQLite WAL Engine)

Font Vault uses an embedded SQLite database (`font-vault/data/vault.db`) running
in Write-Ahead Log (`WAL`) mode with B-tree indices, one connection per thread,
and rolling snapshots of the review data:

- **Instant Opens:** Directories are indexed into SQLite on first load. Reopening a
  vault reads only the page that is displayed, without touching the filesystem.
- **ACID Reliability:** All reviews, skips, archives, and breakage findings are committed
  with atomic transactions, and each thread has its own connection so a background
  scan can never finalize a write in progress on the UI thread.
- **Backups:** The review database is snapshotted into `font-vault/data/backups/`
  (`vault-<timestamp>.db`, plus a `reviews.json` ledger) at startup and on quit
  whenever a snapshot is missing, older than 20 hours, or predates the last
  review change — so a crash loses at most one day of triage. Keepers: the 10
  newest.
- **Bounded Memory:** The queue materializes at most `MAX_QUEUE_ROWS` records and
  the preview caches are trimmed as they fill, so memory tracks the page you are
  looking at rather than the whole collection.
- **Search & Filters:** Filtering happens in SQL against the whole indexed vault,
  with paging. A keyword search is a `LIKE '%term%'` match, which no B-tree index
  can serve, so it scans the vault's rows and costs milliseconds rather than
  sub-millisecond time.
- **↻ Re-sync:** If you add new font files to an existing directory, click **↻ Re-sync**
  to incrementally discover and index new files while preserving all existing review
  decisions.

## Review flow

- `Review queue`, `Unreviewed`, `Used`, `Archived`, `Skipped`, `Broken / excluded`,
  and `All scanned` views persist in `font-vault/data/vault.db`.
- Review queue immediately excludes fonts with missing A–Z/a–z mappings. The
  deeper blank-outline and identical-uppercase/lowercase-outline checks run
  when a font is opened, with a timeout so malformed historical fonts cannot
  freeze startup; those fonts then move to the excluded classification. The
  excluded view keeps them available with the reason. Punctuation is
  intentionally not used as a breakage gate.
- **Randomize** jumps to a different font in the current view without changing
  its saved review status.
- The combined specimen renders the factual character sheet and “The quick
  brown fox jumps over the lazy dog.” together, with a visible gap between them.
- Font metadata includes the internal `head` table creation and modification
  dates when the source font provides valid timestamps. These are historical
  metadata, not necessarily the date the typeface was originally designed.
- Long metadata (license text, URLs, font dates) stays inside a compact
  scrollable strip above the specimen, so it never pushes the specimen off the
  preview area.
- Specimens render in a background worker, so the preview never blocks the UI.
  Opening a font does run its deep outline check on the UI thread, bounded by a
  0.5 s timeout. A font that answers is never checked again; a font that runs out
  of time is left unverified and retried on the next selection, because running
  out of time is not evidence that the font is broken.
  Rendered pixmaps, font facts, and scaled previews are cached in memory per
  font, and the next couple of fonts in the queue are prefetched so **Next**
  feels instant. Selecting a new font cancels any in-flight prefetch so the
  font you actually chose renders first. The current specimen is also generated
  lazily and cached under `font-vault/data/cache/`.
- **Mark used family** copies every style in the detected family into the next
  numbered folder under `font-factory/input/` (for example
  `font-factory/input/1-Amintattalic/`) and writes a manifest, while leaving the
  original files untouched.
- Family grouping is driven by what the font says about itself, in this order:
  the typographic family (`nameID 16`, with its style from `nameID 17`), then the
  legacy family (`nameID 1`), then the family part of the PostScript name
  (`nameID 6`, e.g. `Chaz-CondensedBold` → Chaz Condensed), and only then the
  filename. Weight, width and italic come from `OS/2` and `post` when the name
  table is silent.
- Two layers sit on top of that, and each keeps what the other is bad at:
  the name the font reports is **shown and never stripped of words** — so
  `Encode Sans Condensed`, `Encode Sans Narrow` and `Encode Sans Compressed`
  are three families, and foundry tags (`BT`, `ITC`, `EF`, `URW`, …) keep vendor
  clones apart — while the **comparison key** re-segments that same name, so
  `BulmerMTDisplay` and `Bulmer MT Display`, or `Geo957` and `Geo 957`, are
  recognized as one family rather than two. Re-segmenting can only cancel
  spacing and capitalization noise; it never deletes a word, which is the
  mistake the old filename guesser made.
  Where the font's own name is missing or unusable, the old filename route still
  answers: a staged file whose stem begins with the family and ends in recogniz-
  able style words joins that family. A font that names a different family is
  never pulled in by a look-alike filename.
  Each resolved family is written back to the index, so a vault is read once, and
  exact binary duplicates are skipped when a used family is copied.
  The trade-off is deliberate: a folder can offer many small families to decide
  on instead of one large lump, and grouping is only as tidy as the metadata the
  fonts were shipped with.
  Archive and Skip change the saved review status only; they do not delete or
  move source files.
- `Create fsType=0 working copy…` writes a copy only. It never changes the
  original and does not grant licensing rights.

The renderer is the project helper `bin/render_font_specimens.py`, so the
preview uses the same factual black-and-white specimen style as the font audit.

## Input Inspector

```bash
python3 font-vault/input_inspector.py
```

Input Inspector reviews the staged family folders under `font-factory/input/`
that Font Vault's **Mark used family** creates. The sidebar lists every family
folder with its font count; the main pane shows one preview row per font in the
selected folder — uppercase, lowercase, digits, and punctuation together in a
single cached strip — so stray fonts in a family are easy to spot.

- **◀ Previous / Next ▶** move between family folders. **Next Unmarked →**
  jumps to the next font in the current folder that is not marked In Use
  (wrapping to the top; clicking any row selects it as the starting point).
- **In Use** is a per-font checkable mark (gold when active). It is stored in
  the folder's `in-use.txt` — one filename per line — purely as a local
  tracker for which staged fonts are in use; it is removed automatically when
  the font is returned or deleted.
- **↩ Return to source** sends a font back to the folder it was copied from,
  using the folder's `font-vault-manifest.json` (or `source-directory.txt`).
  If the original is still there, only the staged copy is removed; if it is
  missing, the file is moved back. The manifest is updated either way.
- **✕ Delete** permanently removes a font from the staged folder (with
  confirmation) and records the removal in
  `font-factory/input/deleted-fonts.md` with its original source and the
  reason "does not match the family". Never restore files listed there —
  Agent 27 (font-image-generator) no longer checks original source
  directories at all, so family completeness is verified here instead.

Preview strips are cached under `font-vault/data/cache/inspector/`, so folders
open instantly after the first render.
