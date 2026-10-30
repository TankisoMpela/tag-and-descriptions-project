---
name: agent-pinterest-font-preparer
description: Pinterest asset preparer. Uploads every manifested template pin and ten final-image composites to Vercel Blob, records product-page URLs and the description, then writes all public links to public-urls.md. Does not publish Pins.
user-invocable: true
---

# Pinterest Font Preparer

Prepare one finished font in `outputs/pinterest/registry.json` so the daily run
can use its public image and product-page links without opening the font folder.
Run from the project root. Use `bin/pinterest_registry.py` for all registry,
Blob-upload, validation, and link-file operations.

## Where the images come from

- Agent 27 renders every active HTML/CSS Pinterest template with the font and
  writes the image files plus `pinterest-template-manifest.json` into its
  `prepared_visuals/pinterest/` handoff.
- Agent 13 copies those verified pins unchanged into
  `visuals/New-Images/pinterest/`.
- Agent 30 appends exactly ten final-image composites after the template pins
  and writes `pinterest-set-manifest.json` with the full ordered set, dimensions,
  byte sizes, and SHA-256 hashes.

This agent starts only after Agent 30 has completed. The registry tool verifies
both manifests, every file hash, contiguous numbering, and the ten-composite
count before uploading. Do not design, render, copy, rename, or substitute pins.

## Inputs

The user supplies a font's `outputs/font-preparation/{NUM}-{slug}/` folder (or
its catalogue number / slug / name) and its Creative Market and/or Creative
Fabrica product-page URLs. Match each font to exactly one preparation folder;
if it cannot be matched unambiguously, ask rather than guessing.

## Per-font procedure

1. Register the preparation folder:

   ```bash
   python3 bin/pinterest_registry.py add --slug <slug> --number <N> --name "<Font Name>"
   ```

   Use `--update` when updating an existing record. The tool finds the folder's
   `description.txt`.

2. Record the supplied product URLs exactly as given:

   ```bash
   python3 bin/pinterest_registry.py set-url --slug <slug> --url <cm-url>
   python3 bin/pinterest_registry.py set-url --slug <slug> --url <cf-url> --market cf
   ```

   Omit the command for a URL the user did not provide, then report it as
   missing. Do not silently replace a shop root with a product-page URL.

3. Read only the first ~30 lines of `description.txt` and the font name. Choose
   one board: `Handwritten Fonts`, `Display Fonts`, `Script Fonts`, or
   `Decorative Fonts`, then record it as a suggestion in the registry:

   ```bash
   python3 bin/pinterest_registry.py set-board --slug <slug> --board "<Board>"
   ```

   This does not create the Pinterest board. Buffer imports require the named
   board to exist, so create the suggested boards in Pinterest before the first
   Buffer batch. Pinterest's native CSV import can create a missing board.
   References: [Buffer bulk upload](https://support.buffer.com/articles/how-to-upload-posts-in-bulk-to-buffer-cTIhl4mv6H)
   and [Pinterest bulk upload](https://help.pinterest.com/en/business/article/bulk-upload-video-pins).

4. Upload the complete manifested set to the `pinterest-pins-media` Vercel
   Blob store:

   ```bash
   python3 bin/pinterest_registry.py upload --slug <slug>
   ```

   The helper discovers the template count from the manifest, checks that the
   set contains those template pins followed by exactly ten composites, then
   uploads every numbered file to a content-hash pathname, so changed artwork
   gets a fresh public URL instead of a stale cached copy. It skips unchanged
   files already recorded unless the user explicitly requests `--force`. Use
   `--index N` only for a targeted retry.
   If validation reports a missing file, hash, or manifest, stop and complete
   the missing upstream stage; never fill a gap manually.

5. Write the full set of public image links and the supplied product URLs to the
   font folder:

   ```bash
   python3 bin/pinterest_registry.py write-urls --slug <slug>
   ```

   This creates `public-urls.md` with one row for every uploaded image link, so
   it grows with the template count plus ten composites. Use
   `show --slug <slug> --json` if you need the machine-readable registry
   record.

## Report

For each font, report its slug, board, number of image links uploaded and the
full `public-urls.md` path. State which product URLs were recorded or are
missing. The Blob upload provides public image links for the daily publishing
workflow; it does not create, schedule, or publish Pins on Pinterest.

## Hard rules

- Never edit font binaries, raw images, or `description.txt`.
- Blob credentials come from `~/.config/papermoon/blob.env`; never print or
  commit the write token.
- `list --ready` requires every image in a current manifest-backed set. Older
  pre-manifest records remain readable during migration if their stored image
  links are present.
- `outputs/pinterest/registry.json` is the only registry state store; change it
  only through `bin/pinterest_registry.py`.
- Do not inspect image content or claim that Pins were published.
