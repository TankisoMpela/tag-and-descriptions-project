# Supporting-image reference library

This directory contains downloaded visual references for rebuilding the supporting-image catalogue. The numbered files are preserved with their source IDs; `originals/` contains seller-provided local materials and screenshots.

The 2026-10-14 request is preserved verbatim in
[`incoming-urls-2026-10-14.txt`](incoming-urls-2026-10-14.txt) (46 URL lines,
including duplicates); its 44 unique source images are indexed in
[`SOURCES.md`](SOURCES.md) and reviewed in
[`previews/incoming-reference-contact-2026-10-14.png`](previews/incoming-reference-contact-2026-10-14.png).

The 2026-10-29 reference set contains 27 original images from 15 source IDs. Original responses, exact URLs, and SHA-256 records are in [`originals/reference-batch-2026-10-29-a/`](originals/reference-batch-2026-10-29-a/); the [contact sheet](previews/reference-contact-2026-10-29-a.png) gives a labelled overview. Each source will be developed as a separate template, with both aspect ratios completed before advancing.

The November 3 Creative Market set contains twelve supplied references and
eight accepted text-free photo plates. Originals, source URLs, hashes, edit
prompts, and rejected plate notes are in
[`materials/user-batch-2026-11-03-a/`](materials/user-batch-2026-11-03-a/)
and [`originals/user-batch-2026-11-03-a/`](originals/user-batch-2026-11-03-a/).
Eight HTML/CSS layouts were created in slots 173–180; `statueframe32`,
`fashioncard32`, and `parkstatement32` are retired, leaving five active.

The November 11 Creative Market batch contains eleven additional recent
Downloads references, remade sequentially in slots 183–193. Originals and
decoded source images are preserved under
[`originals/creative-market-batch-2026-11-11/`](originals/creative-market-batch-2026-11-11/);
transparent character cutouts and text-free art plates are under
[`materials/creative-market-batch-2026-11-11/`](materials/creative-market-batch-2026-11-11/).
Each template has separate wide and square previews linked from its entry in
`support-html/catalog.json`.

These are references and source materials for the Skia and HTML/CSS supporting-image templates. Template code uses selected materials directly; final font-specific artwork belongs in the active font workspace, never beside the reference originals. `materials/` contains transparent user-supplied cutouts, generated image plates, cleaned photo backgrounds, and source-derived crops.

The active catalogue has 144 supporting templates and selects 12 eligible
layouts for a font, prioritizing designs used least often in previous handoffs
of the same renderer class. `weightfamily32`, `mangosboard32`, and
`italicregular32` require at least two actual styles from one family; eligible
family showcases join the selection pool but are not guaranteed.
Supporting artwork uses display specimen copy rather than repeating
the font name. Caption, word-length, palette/contrast, flexibility, and alt-text
guidance is in [TEMPLATE-GUIDE.md](TEMPLATE-GUIDE.md); the exact source mapping is
in [REMAKE-MAP.md](REMAKE-MAP.md). New image-generation prompts are preserved in
[`IMAGEGEN-PROMPTS.md`](IMAGEGEN-PROMPTS.md).

The [full catalogue sheet](previews/template-preview-catalogue.png) and paired
audit are historical 69-template snapshots from before the first-pass review;
the audit images remain useful for inspecting those renders individually.
Current decisions and the line-by-line review are in
[`class-audit-2026-10-14/blackletter-first-pass.md`](class-audit-2026-10-14/blackletter-first-pass.md).
Use the command below for the full current active inventory.
Focused review sheets remain available
for [restored `blossom32` and slots 50–56](previews/updated-layouts-2026-10-14.png)
and [slots 57–70](previews/slots-57-70-2026-10-14.png). Use
`bin/pin-studio/.venv/bin/python bin/pin-studio/pin_studio.py --list --supports`
for the current active list. Actual handoffs render the selected layouts with
the target font and include both family panels when multiple real styles are
present. The current full 3:2 and square review is under
[`support-html/benchmarks/catalogue-review-2026-10-26/`](../support-html/benchmarks/catalogue-review-2026-10-26/).

The [paired six-style catalogue audit](class-audit-2026-10-14/README.md) records
the historical six-style comparison and preflight results; its pool counts
predate the first-pass retirements and blackletter exclusions.

## Reference groups

- `T30332_04`: pixel-art sea postcard; `kindersea32` retains the original lavender texture and cropped pixel-art image while redrawing generic headline copy.
- `T30332_05`: textured framed message card; `messageframe32` retains its original decorative artwork while replacing the source quote and font labels.
- `T30332_06`: pastel index-board reference; `contactlist32` retypes its eight track titles and uses generic footer labels over a clean backing plate.
- `T30332_07`: sunset-promise poster; `sunsetpromise32` uses the exact source pixel-art crop over a clean textured plate and resets the four-line headline.
- `T30332_08`: three-screen flower-phone layout; `phonegarden32` restores the source wordmarks and right-screen message while replacing the side foundry/font labels.
- `T30332_09`: hot-pink quote on black; `pixelquote32` resets the five-line source quote and reuses the exact heart, mascot, and pixel-stitch details as transparent materials.
- `T24250_*`: retro display, poster, and geometric layout language; `T24250_04` is the Rio travel-hero reference rebuilt by `rio32`.
- `T25585_03`: editorial collage / expressive display treatment.
- `T28576_*`: fashion-editorial layouts and illustration-led posters; `T28576_06` `focusposter32` pairs a generated soft-focus portrait plate with the exact source eye-detail crop.
- `T27673_*`: restrained editorial / variable-type layouts; `T27673_00` is `plakat32`, and the red/cyan macro-art panel in `T27673_10` is `plakatart32`.
- `T30930_*`: variable sans specimen systems and diagrammatic typography.
- `T28660_00`: red-tailoring fashion cover; `ravencover32` uses its clean photo material with an oversized editorial headline and spare cover furniture.
- `T30930_01`, `_04`, `_05`, and `_07` have dedicated weight-family, modular-family, character-sheet, and Mangos infographic layouts in `weightfamily32`, `mangosboard32`, `alphabet32`, and `mangos32`.
- `T33110_*`: expressive type with image/texture-led compositions; `T33110_08` is rebuilt by `birvase32` over a generated text-free red/cyan print material.
- `T33144_02`: oversized display type with the supplied transparent thumbs-up motif.
- `T33631_05`: dark editorial/type composition using the user's exact mountain crop.
- `T24507_04`: western fashion-photography layout with line-art horseshoe and boot motifs.
- `T13692_01`: paired zebra and rose posters; `T13692_03`: soldier-photo specimen; `T13692_06`: brutalist editorial spread; `T13692_07`: brutalism identity/packaging studies; `T13692_12`: mirror portrait with an overprinted quote.
- Behance project 40630743: `sexyshout32` preserves the reference and rebuilds “Sexy” / “Shout” as live selected-font text over the supplied grayscale photo.
- Envato download `33a5cffa`: `embracesexiest32` retypes “Embrace” and “The Sexiest” over the user's unchanged fashion photo; neutral specimen labels replace the reference foundry credit.
- Behance project 40630743: `sexyshout32` preserves the reference and rebuilds “Sexy” / “Shout” as live selected-font text over the supplied, uncensored grayscale photo.

## Local materials

- `originals/T33631_05-illustration.jpg` — the user's already-cropped mountain illustration, used verbatim by `mountain32`.
- `originals/vintage-rose-on-book-pages.png` — transparent/source material for the T13692-inspired floral treatment.
- `originals/zebra-pair-in-arched-savanna-frame.png` — transparent/source material for the T13692-inspired animal treatment.
- `originals/transparent-thumbs-up-line-art.png` — the user's transparent thumbs-up material, placed directly by `hand32`.
- `materials/reference-batch-2026-10-26-e/sexyshout-user-photo.png` — the user's supplied grayscale photo, preserved unchanged for `sexyshout32`.
- `materials/reference-batch-2026-10-26-f/33a5cffa-user-photo.png` — the user's supplied fashion photo, preserved unchanged for `embracesexiest32`.
- `materials/reference-batch-2026-10-26-e/sexyshout-user-photo.png` — the user's clean grayscale photo, preserved unchanged and used directly by `sexyshout32` in both ratios.

## Reusable derivatives

- `materials/T30332_04-clean-lavender-plate.png`, `T30332_04_pixel-sea-art.png`, and `T30332_04_corner-stars.png` — source-derived base, cleaned crop, and transparent sparkles for `kindersea32`; the original display text and font name are removed or replaced.
- `materials/T30332_05-clean-message-plate.png` — text-cleaned original stock/card plate for `messageframe32`; the font-specific headline and labels are removed, while the hearts, stars, frame, and globe remain.
- `materials/T30332_06-clean-index-plate.png` — one-pass image-model cleanup based on `T30332_06.jpg`; it closely retains the frame, tabs, nodes, pastel panel, and footer plates without the source lettering. The eight track titles and generic footer labels are redrawn by `contactlist32`.
- `materials/T30332_07-clean-sunset-background.png` and `T30332_07_pixel-sunset-art.png` — one-pass text-free background plate plus the exact `(54,52,436,238)` pixel-art crop from `T30332_07.jpg`; `sunsetpromise32` retypes the four-line message and generic header labels.
- `materials/T30332_08-clean-phone-plate-no-lettering.png` — one-pass text-free phone layout, with a small leftover pink flower inscription removed by OpenCV; `materials/T30332_08_left-peony-v2.png` is the source-derived transparent flower crop used verbatim by `phonegarden32`.
- `materials/T30332_09_pixel-heart.png`, `T30332_09_pixel-mascot.png`, and `T30332_09_pixel-stitches-{top,bottom}.png` — transparent OpenCV color-mask extractions from `T30332_09.jpg`, placed verbatim by `pixelquote32` around the five-line Skia quote.
- `materials/T13692_soldier-cutout.png` — RGBA crop of the T13692_03 soldier photo. OpenCV contour analysis supplied candidate coordinates; the clipped-corner mask was visually checked against the reference.
- `materials/T13692_mirror-portrait.png` — transparent text-free archival-style portrait and mirror insert, regenerated with more natural photo grain and skin texture because the source lettering obscures the original photo and the prior insert read as AI.
- `materials/T13692_black-plastic-texture.png` — one-pass generated dark crinkled-plastic surface matched to the visible folds in T13692_01 and used by `zebra32`.
- `materials/T13692_06_brutalist-photo-plate.png` — generated four-panel grayscale brutalist-architecture photo plate; `brutal32` crops its clean cells as rectangular image materials.
- `materials/T30173_08_palm-cutout.png` — transparent, reference-derived pair of drooping palms used as a recolorable layer by the HTML/CSS `duo32` prototype.
- `brutalpack32` reuses a portrait crop from the bottom-right cell of that plate inside its arched photo window.
- `materials/T24250_04_rio-dusk-background.png` — generated full-bleed dusk panorama used as the text-free background for `rio32`.
- `materials/T24507_04_saltflat-photo.png` — generated clean black-and-white seated-figure portrait; the original photo crop contains red horseshoe artwork across its top.
- `materials/T24507_04_coral-cowboy-boot.png` — transparent engraved boot illustration; Skia recolors its alpha-backed linework to the poster's muted coral.
- `materials/T27673_10_red-cyan-macro-texture.png` — generated red/cyan fiber-like macro texture used in `plakatart32`; the source reference's original macro image was covered by the overlapping title.
- `materials/T33110_08_red-cyan-print-texture.png` — one-pass generated, text-free red/cyan halftone texture used behind the wordmark in `birvase32`.
- `materials/T13692_zebra-arched.png` and `materials/T13692_rose-strip.png` — supplied transparent materials used directly by `zebra32`.
- `materials/T33144_thumbs-up-line-art.png` — supplied transparent hand art used directly by `hand32`.
- `materials/T30332_01_stardust-photo.png` — the user-provided clean portrait background, copied unchanged from Downloads for `stardust32`; `materials/T30332_02_cliff-sea-background.png` is the one-pass coastal photo plate for its matching editorial layout.
- `materials/T24908_00_amber-dawn-photo.png`, `T24908_01_clean-photo-background.png`, `T24908_02_clean-photo-background.png`, and `T24908_03_gelato-background.png` — one-pass, text-free fashion-photo plates for the matching amber, skincare, lookbook, and gelato layouts. The earlier `T24908_01_skin-portrait-background.png` is retained but no longer used by `skinbadge32`.
- `materials/T26289_01_orange-fashion-cutout.png` and `T28576_03_editorial-face-cutout.png` — transparent photo/illustration cutouts used by active layouts. `T28576_09_beach-fashion-cutout.png` is retained as provenance for withdrawn `bondibeach32`; no active template uses it.
- `materials/T28660_00_red-jacket-photo.png` — the user-provided red-blazer photograph, copied unchanged from Downloads and used instead of the typography-overprinted source cover.
- `materials/T26003_01_lemonade-line-art.png` — one-pass transparent engraved lemonade illustration.
- `materials/T28576_04_eye-illustration.png`, `T28576_05_artist-illustration.png`, `T28576_05_hands-strip.png`, `T28576_06_eye-detail.png`, and `T28576_08_blossom-illustration.png` — exact source crops saved separately from adjacent copy and panel furniture.
- `materials/T28576_04_eye-illustration-clean.png` — one-pass transparent cleanup of the eye crop, removing the tiny source-font imprint across the iris; used by `confident32`.
- `materials/T28576_06_soft-focus-portrait.png` — text-free, high-key grayscale fashion portrait background plate for `focusposter32`; the original eye-detail crop stays separate and sharp.
- `materials/T24908_02_red-jacket-photo.png` and `T25990_02_sea-rocks-photo.png` — retained clean rectangular photo crops from their source references; `latestlook32` now uses the full clean photo plate.
- `materials/T13692_07-folded-package-lines.svg` and `.png` — retained Potrace study of the folded package body from `T13692_07.jpg` (source crop: x=849, y=365, w=292, h=312). The active `brutalpack32` now redraws its folds with clean native Skia paths instead of using the dense trace.

Older mountain experiment files are retained for provenance but are not used by `mountain32`; that template uses the exact crop under `originals/`.
