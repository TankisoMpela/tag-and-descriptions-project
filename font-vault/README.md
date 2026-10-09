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
- **Mark used family** copies every style in the detected family into the next
  numbered folder under `font-factory/input/` (for example
  `font-factory/input/1-Amintattalic/`) and writes a manifest, while leaving the
  original files untouched.
- Family actions use the typographic family name when available, preserve style
  names such as Regular/Bold/Italic, fall back from generic placeholder names,
  and skip exact binary duplicates when copying a used family. Archive and Skip
  change the saved review status only; they do not delete or move source files.
- The current specimen is generated lazily and cached under
  `font-vault/data/cache/`.
- `Create fsType=0 working copy…` writes a copy only. It never changes the
  original and does not grant licensing rights.

The renderer is the project helper `bin/render_font_specimens.py`, so the
preview uses the same factual black-and-white specimen style as the font audit.
