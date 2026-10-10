---
name: agent-booth-pdf-maker
description: Builds a single-page branded Japanese trial-insert PDF from a BOOTH item URL, a local font directory, a trial URL, and the New-Images squares thumbnail. No upload claim.
user-invocable: true
---

# Booth PDF Maker

You produce **one single-page portrait PDF** that acts as a small branded
insert for a BOOTH font purchase — not an instruction manual and not a like
solicitation.

The customer has already found the font on BOOTH. The PDF's only jobs are:

1. Confirm what they downloaded.
2. Establish the shop brand.
3. Give the trial download link.
4. Say what the trial is.
5. Give one quiet reason to remember the shop.

Do **not** put the post-download support / “please like BOOTH” message in the
PDF. That moment belongs to the trial page after the download.

## Required inputs

Collect these three facts from the user (or from the slash-command argument
string). Ask once, clearly, if any are missing — never invent URLs.

| Input | Meaning | Example |
|---|---|---|
| BOOTH item URL | Full product page | `https://shop.booth.pm/items/123456` |
| Font directory | Local folder that contains the font binary (and, when available, `visuals/New-Images/squares/`) | `font-factory/fonts/{slug}` or `outputs/font-preparation/{NUM}-{slug}` |
| Trial URL | Public trial page on font-showroom | `https://your-domain/trial/{slug}` |

Optional (use sensible defaults when omitted):

- **Font name** — derive from the font file / folder name if not given.
- **Specimen line** — one short personality line set in the font (not the full alphabet only). Choose a line that matches the font’s character (cute / horror / retro / elegant). Default is a clean ABC/abc/0123 block under the hero name.
- **Shop name** — default `Font Studio`.
- **Tagline** — default `INDEPENDENT TYPE / FONT STUDIO`.
- **Accent color** — default near-black `#111111` on warm paper `#F7F4EF`.
- **Page size** — default **A5 portrait**; allow `letter` if asked.

## Product image

The product image for the PDF is the thumbnail from:

```text
{font-directory}/visuals/New-Images/squares/
```

Resolution order (mechanical — no vision, no semantic guessing):

1. `--image` if the user pointed at a specific file.
2. `{font_dir}/visuals/New-Images/squares/thumbnail_main.*` (any extension).
3. First lexicographic image in `{font_dir}/visuals/New-Images/squares/`.
4. Same two rules under `{font_dir}/visuals/squares/`.
5. A `visuals/New-Images/squares/` found under `{font_dir}` (bounded search).

Supported images: `.png`, `.jpg`, `.jpeg`, `.webp`. Fail closed if none exist
and no `--image` was supplied. Never invent, crop, or substitute art.

## Required command

Run from the repository root. One command builds the HTML and prints the PDF:

```bash
python3 bin/make_booth_trial_pdf.py \
  --booth-url "https://shop.booth.pm/items/…" \
  --trial-url "https://…/trial/{slug}" \
  --font-dir "path/to/font-dir" \
  --font-name "Mochi" \
  --specimen "A little font for big ideas." \
  --shop-name "Font Studio" \
  --output "outputs/booth-pdfs/{slug}-trial-insert.pdf"
```

Useful flags: `--image`, `--tagline`, `--accent`, `--page a5|letter`,
`--keep-html`. The script embeds the font, embeds the squares thumbnail,
writes Japanese customer copy, adds clickable `href`s for both buttons, and
renders one page via headless Chromium (`chromium --headless --print-to-pdf`).

Exit code `0` means a PDF exists at `--output`. Non-zero means fail closed —
do not hand-edit a partial PDF into existence.

## Layout (authoritative hierarchy)

Single page, portrait. Rough density:

```text
                 SHOP / LOGO
        INDEPENDENT TYPE / FONT STUDIO

                    FONT NAME          ← huge, set in the font

              [ PRODUCT IMAGE ]        ← New-Images squares thumbnail

         Specimen line + ABC/abc/09    ← set in the font

              PERSONAL USE TRIAL

       ご挨拶 + これは Personal Use 版

          ┌─────────────────────┐
          │  フォントを入手する →  │     ← ONLY giant functional element
          └─────────────────────┘
              trial-url (visible)

          ───── お試しについて ─────

       個人利用のみ / 商用は BOOTH のフル版

          フル版を見る →

          ─────────────────────────
          SHOP NAME · tagline
          BOOTH · trial · more fonts
          ─────────────────────────
```

Design rules:

- **Font is the star.** Hero name and specimen lines use the product font.
- Branding at the top stays restrained: logo/shop name + one tiny line.
- **GET YOUR FONT** (label may be Japanese: `フォントを入手する →`) is the
  only large functional element. Everything else is quieter.
- Show the trial URL as plain text under the button (print + digital fallback).
- Second CTA goes to the BOOTH product (`フル版を見る →`).
- Keep Japanese for all customer-facing body copy. Short English eyebrow
  labels (`PERSONAL USE TRIAL`, `ABOUT THIS TRIAL`) are allowed for rhythm.
- Same system across fonts; specimen line, accent, and image change per font
  so the PDF feels collectible.
- **Never** include “いいねしてください / Please like this product on BOOTH”.

## Output

Default directory:

```text
outputs/booth-pdfs/{slug}-trial-insert.pdf
```

Also leave the generated HTML beside it when `--keep-html` is set (useful for
iteration). Report:

- exact PDF path
- font file used
- image path used
- trial URL and BOOTH URL embedded
- page size
- `No upload or publication claim`

## Scope boundary

- No upload, publish, or marketplace claim.
- Do not modify font binaries, package archives, or `New-Images` sources.
- Do not run `/full-workflow`, listing agents, or image processors.
- Do not fetch BOOTH HTML unless a required URL is missing; if the BOOTH URL
  was supplied, trust it and only normalize the scheme/host.
- Fail closed on missing font file, missing trial URL, missing BOOTH URL, or
  missing thumbnail.
