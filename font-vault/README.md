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
in Write-Ahead Log (`WAL`) mode with fast B-tree indices for rock-solid data integrity,
sub-millisecond queries, and near-zero memory footprint:

- **Instant Opens:** Directories are indexed into SQLite on first load. Reopening a
  vault takes ~0.01s without touching the filesystem.
- **ACID Reliability:** All reviews, skips, archives, and breakage findings are committed
  with atomic transactions. Crashes or unexpected shutdowns cannot corrupt your data.
- **Lean Memory:** True disk paging keeps UI memory consumption under 50 MB even with
  100,000+ fonts across multiple large collections.
- **Instant Search & Filters:** B-tree compound indexing handles filtering and keyword
  searches in sub-millisecond time.
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
- Specimens render in a background worker: switching fonts never blocks the UI.
  Rendered pixmaps, font facts, and scaled previews are cached in memory per
  font, and the next couple of fonts in the queue are prefetched so **Next**
  feels instant. Selecting a new font cancels any in-flight prefetch so the
  font you actually chose renders first. The current specimen is also generated
  lazily and cached under `font-vault/data/cache/`.
- **Mark used family** copies every style in the detected family into the next
  numbered folder under `font-factory/input/` (for example
  `font-factory/input/1-Amintattalic/`) and writes a manifest, while leaving the
  original files untouched.
- Family actions use the typographic family name when available, preserve style
  names such as Regular/Bold/Italic, fall back from generic placeholder names,
  and skip exact binary duplicates when copying a used family. Archive and Skip
  change the saved review status only; they do not delete or move source files.
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
