---
name: agent-pinterest-font-preparer
description: Pinterest asset preparer. Registers a font from its outputs/font-preparation folder, uploads ALL FIVE of its pin images to Vercel Blob, records both product-page URLs (Creative Market + Creative Fabrica) and the description, and writes public-urls.md into the font folder. No Pinterest-side action.
user-invocable: true
---

# Pinterest Font Preparer (asset preparer)

You turn one finished font into a ready-to-pin registry record in
`outputs/pinterest/registry.json`, so the daily run (`/pinterest-daily`) can
work purely from public URLs and never has to open the font folder. Run from
the project root. All mechanics live in `bin/` tools — never reimplement them.

## Where the pin images come from

The five pins are designed and rendered by `/font-prep` (Agent 13, Step 2) from
the font binary, with `bin/render-pins` and a per-font `pins.brief.json` — five
fresh headlines in five colour worlds. The art direction behind them is
`docs/PIN-ART-DIRECTION.md` and the renderer's capability reference is
`docs/SKIA-PIN-RENDERER.md`.

**You never design or render a pin.** Your job starts once
`visuals/New-Images/pinterest/` already holds `pinterest_1..5`.

## Inputs you expect

From the user: the font's `outputs/font-preparation/{NUM}-{slug}/` folder (or
its catalogue number / slug / name), plus the product-page URLs it should point
at — Creative Market and/or Creative Fabrica. Match each font to exactly one
preparation folder (`ls` and match by slug or number). If a font cannot be
matched to exactly one folder, ask; never guess across fonts.

## Per-font procedure (repeat for each input font)

1. `python3 bin/pinterest_registry.py add --slug <slug> --number <N> [--name "<Font Name>"]`
   (add `--update` when re-registering; the tool verifies the prep folder and
   finds `description.txt`, which is the description record).
2. Record BOTH product pages, one command each — the daily run splits a day's
   pins between them:
   `python3 bin/pinterest_registry.py set-url --slug <slug> --url <cm-url>`
   `python3 bin/pinterest_registry.py set-url --slug <slug> --url <cf-url> --market cf`
   Aliases: `cm` (default) and `cf`. If the user gave only one, set that one and
   say the other is missing. Record URLs exactly as supplied — a shop root is
   not a product page; the tools flag it, you do not silently upgrade it.
3. Board suggestion — read only the first ~30 lines of `description.txt` and
   the font name; decide ONE of: `Handwritten Fonts`, `Display Fonts`,
   `Script Fonts`, `Decorative Fonts`; then
   `python3 bin/pinterest_registry.py set-board --slug <slug> --board "<Board>"`.
   The daily run may override this per pin; it is a suggestion, not a lock.
4. Upload the five pin images:
   `python3 bin/pinterest_registry.py upload --slug <slug>`
   If the tool warns that fewer than five images were found, the font has not
   been pinned yet: report that and name the fix (`/font-prep` Step 2 for this
   font). Do not design, copy, or substitute an image here.
   The tool takes every `visuals/New-Images/pinterest/pinterest_N` image — one
   per index (it prefers the lossless `.png` when a `.jpg` twin exists) — pushes
   each to the `pinterest-pins-media` Vercel Blob store and records its public
   URL under that index. Do NOT inspect image content. Already-uploaded indices
   are skipped unless the user asked for `--force`.
5. Write `public-urls.md` at the prep folder root from the registry record
   (`show --slug <slug> --json`) — five image links, both product URLs, board:

   ```markdown
   # Public Pinterest assets — <Font Name>
   - Pin image 1: <public blob URL>
   - Pin image 2: <public blob URL>
   - Pin image 3: <public blob URL>
   - Pin image 4: <public blob URL>
   - Pin image 5: <public blob URL>
   - Creative Market product URL: <url or MISSING>
   - Creative Fabrica product URL: <url or MISSING>
   - Board suggestion: <Board>
   ```

## Report

Per font: slug, board, how many of the five images are live (with URLs), which
product URLs are recorded and which are missing — plus any font you could not
register and why.

## Hard rules

- Never edit font binaries, raw images, or `description.txt`.
- Blob auth comes from `~/.config/papermoon/blob.env`; never print the RW
  token and never add it to any repo file.
- `outputs/pinterest/registry.json` is the sole state store — edit it only via
  the registry tool.
- You do not create, schedule, or publish Pinterest pins. No upload claim to
  Pinterest. Make no claims about live sales pages; record the URL exactly as
  supplied.
