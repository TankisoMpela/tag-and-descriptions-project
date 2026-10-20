# Source URLs

Downloaded on 2026-10-13 for visual study and reconstruction. The files retain the source IDs used by the provider.

| Local file(s) | Source URL |
|---|---|
| `T27673_00.jpg`, `T27673_10.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T27673_2x/c/T27673_00.jpg?20250208080835` / `.../T27673_10.jpg?20250208080835` |
| `T25585_03.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T25585_3x/c/T25585_03.jpg?20240912213354` |
| `T24250_00.jpg`, `02`, `03`, `04`, `06` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T24250_3x/c/T24250_XX.jpg?20240613192455` |
| `T30930_00.jpg`, `01`, `03`, `04`, `05`, `07`, `08` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T30930_2x/c/T30930_XX.jpg?20251008214237` |
| `T33110_02.jpg`, `T33110_08.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T33110_2x/c/T33110_XX.jpg?20260310024142` |
| `T30173_08.jpg` | Local reference used by `duo32`; its source URL was not recorded in the current URL manifest. |
| `T27485_07.jpg` | Local reference used by `feature32`; its source URL was not recorded in the current URL manifest. |
| `T13692_03.jpg`, `06`, `07`, `12` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T13692_2x/c/T13692_XX.jpg?20210217224126` |
| `T33631_05.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T33631_2x/c/T33631_05.jpg?20260621232725` |
| `T33144_02.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T33144_3x/c/T33144_02.jpg?20260315231635` |
| `T13692_01.jpg` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T13692_2x/c/T13692_01.jpg?20210217224126` |

The repeated T24250_00 URL from the original request was stored once. Some provider responses identify as WebP despite the `.jpg` filename; the bytes are preserved unchanged.

## Incoming batch — 2026-10-14

The exact 46-line request (including the repeated `T30332_01` and
`T28576_07` URLs) is preserved in
[`incoming-urls-2026-10-14.txt`](incoming-urls-2026-10-14.txt). The two repeated
URLs resolve to one local file each, leaving 44 downloaded references. Source
bytes are kept unchanged; ImageMagick identifies them as WebP despite the
provider's `.jpg` filenames.

| Local reference files | Source URL family |
|---|---|
| `T30332_00`, `_01`, `_02`, `_04`–`_09` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T30332_2x/c/T30332_XX.jpg?20250826024733` |
| `T28660_00` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T28660_2x/c/T28660_00.jpg?20250425221032` |
| `T28576_03`–`_09` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T28576_2x/c/T28576_XX.jpg?20250421002529` |
| `T25441_04` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T25441_2x/c/T25441_04.jpg?20240908212549` |
| `T19827_01`, `_06` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T19827_2x/c/T19827_XX.jpg?20230525211236` |
| `T21458_04`, `_11` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T21458_3x/c/T21458_XX.jpg?20240610234345` |
| `T23086_05`, `_06` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T23086_2x/c/T23086_XX.jpg?20240325032050` |
| `T24908_00`–`_03` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T24908_3x/c/T24908_XX.jpg?20240724214107` |
| `T25990_02` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T25990_2x/c/T25990_02.jpg?20241010225131` |
| `T26003_00`, `_01` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T26003_2x/c/T26003_XX.jpg?20241011030128` |
| `T26289_00`, `_01` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T26289_2x/c/T26289_XX.jpg?20241025030734` |
| `T26223_00`, `_02`–`_05` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T26223_2x/c/T26223_XX.jpg?20241023204735` |
| `T26074_01`, `_02`, `_03`, `_06`, `_12` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T26074_2x/c/T26074_XX.jpg?20241016220542` |
| `T26392_08` | `https://dfjx2uxqg3cgi.cloudfront.net/img/type/T26392_3x/c/T26392_08.jpg?20241030224422` |

## Incoming-batch materials

Recorded image-generation prompts are in [`IMAGEGEN-PROMPTS.md`](IMAGEGEN-PROMPTS.md). The materials are one-pass outputs, retained as reusable inputs rather than finished template compositions.

- Generated photo plates: `materials/T30332_01_stardust-photo.png`, `T30332_02_cliff-sea-background.png`, `T24908_00_amber-dawn-photo.png`, `T24908_01_skin-portrait-background.png`, `T24908_02_clean-photo-background.png`, `T24908_03_gelato-background.png`, and `T28660_00_red-jacket-photo.png`.
- `materials/T24908_01_clean-photo-background.png` — one-pass text-removal reconstruction of the warm hair-and-skin photo behind the two seals in `skinbadge32`.
- `materials/T24908_02_clean-photo-background.png` — one-pass edit of `T24908_02.jpg` removing the lookbook lettering while preserving its red blazer, model crop, and architecture; used full-bleed by `latestlook32`.
- `materials/T24908_03_blue-ice-cream-pattern.png` and `T24908_03_crimson-ice-cream-pattern.png` — the user's prepared `Ice-Cream-Background-Designs` files, retained unchanged and clipped into the rear and front cards of `gelatocards32`.
- `materials/T28576_03_glamorous-manga-portrait.png` — the user's transparent `Glamorous Over-the-Shoulder Manga Portrait.png`, retained unchanged for the matching manga cover in `voguecover32`.
- `materials/T28576_05_framed-manga-eyes.png` — the user's `Framed Manga Eyes in Monochrome.png`, retained unchanged and used as the full-bleed background for `storyteller32`.
- `materials/T26223_04_retro-hand-sign-blank-panels.png` — the user's transparent `Retro Hand Sign Blank Panels.png`, retained unchanged and used behind the three overlaid words in `pastpresent32`.
- `materials/T25990_02_meditation-bubble-art.png` — one-pass built-in image-generation output for the added orange/violet bubble illustration in `meditation32`; generated as a transparent isolated asset with this prompt: “Create a polished illustration of a small cluster of floating translucent bubbles in warm orange and violet/lavender, with gentle iridescent highlights and soft inner reflections; refined editorial illustration, crisp graceful glassy soap bubbles; wide horizontal arrangement, transparent background, no text, border, container, extra objects, or watermark.”
- `materials/T30332_00-clean-pastel-background.png` — `T30332_00` background plate cleaned with OpenCV 5.0.0 Telea inpainting (5px radius) to remove the source brand line and caption while preserving its pastel airbrush, halftone field, and stars; the source word inside the oval is covered by the Skia redraw.
- `materials/T30332_04-clean-lavender-plate.png` — the `T30332_04` composition with its brand, font name, and headline removed by OpenCV-contrib `xphoto.INPAINT_SHIFTMAP` in CIELab; the original paper grain, card placement, and pixel-art scene remain intact as the template's textured base.
- `materials/T30332_04_pixel-sea-art.png` — exact crop `(112,96,962,396)` from `T30332_04`; source corner sparkles and a tiny overprint were removed with OpenCV Telea (5px) so the artwork is a clean independent layer.
- `materials/T30332_04_corner-stars.png` — transparent extraction of the two source pixel sparkles, retained as an overlay so they cross the card edge exactly as in the reference.
- `materials/T30332_05-clean-message-plate.png` — `T30332_05` base with only the four-line quote, foundry label, and font name removed using OpenCV-contrib `xphoto.INPAINT_SHIFTMAP` in CIELab; the textured stock, framed card, hearts, dots, stars, corner blocks, and globe are retained.
- `materials/T30332_06-clean-index-plate.png` — one-pass built-in image-generation cleanup based on `T30332_06.jpg`; provides a text-free backing plate with the reference's white board, navy frame, pastel tabs, registration nodes, gradient panel, and two footer plates. The generated plate is composition-matched rather than pixel-identical; all eight titles and generic footer labels are reset in Skia.
- `materials/T30332_07-clean-sunset-background.png` — one-pass built-in image-generation cleanup of the title and two source header labels from `T30332_07.jpg`. It restores a clean lavender floral field and white header in the original composition; the background plate is not pixel-identical.
- `materials/T30332_07_pixel-sunset-art.png` — exact source crop `(54,52,436,238)` from `T30332_07.jpg`, including its dark frame; overlaid on the generated backing plate to preserve the source pixel artwork verbatim.
- `materials/T30332_08-clean-phone-plate-no-lettering.png` — one-pass image-generation cleanup of the source copy and side labels; the small pink lettering left on the upper flower was locally removed with OpenCV Telea inpainting (6px radius).
- `materials/T30332_08_left-peony-v2.png` — transparent source crop `(120,465,170,150)` from `T30332_08.jpg`; HSV color masking isolates the original pink peony, yellow center, and green stem, which `phonegarden32` places over the generated plate's lower-left flower.
- `materials/T30332_09_pixel-heart.png`, `T30332_09_pixel-mascot.png`, `T30332_09_pixel-stitches-top.png`, and `T30332_09_pixel-stitches-bottom.png` — transparent pink-mask crops from `T30332_09.jpg` at `(495,96,49,41)`, `(341,689,63,57)`, `(889,49,235,26)`, and `(67,720,234,26)`, respectively; `pixelquote32` places these original pixel details verbatim.
- Generated transparent art: `materials/T26289_01_orange-fashion-cutout.png`, `T28576_03_editorial-face-cutout.png`, `T28576_09_beach-fashion-cutout.png`, and `T26003_01_lemonade-line-art.png`. Alpha was verified on the four cutouts. The T28576_09 cutout is now retained as provenance only; its `bondibeach32` template is withdrawn.
- Source crops saved separately: `materials/T28576_04_eye-illustration.png` `(46,394,1091,353)`; `T28576_05_artist-illustration.png` `(762,15,374,729)`; `T28576_05_hands-strip.png` `(49,403,707,73)`; `T28576_06_eye-detail.png` `(268,141,357,120)`; `T28576_08_blossom-illustration.png` `(718,14,466,733)`; `T24908_02_red-jacket-photo.png` `(0,0,455,1201)`; `T25990_02_sea-rocks-photo.png` `(118,396,949,261)`; and `T24507_04_saltflat-photo-crop.png` `(112,571,720,480)`, the unobstructed lower landscape photograph.
- `materials/T28576_04_eye-illustration-clean.png` — one-pass OpenAI image-generation edit of the source eye crop to remove the tiny embedded lettering from the iris; the generated 2170x725 transparent output was cropped 12px at top and 14px at bottom to discard edge artifacts. `confident32` uses this clean version; the original source crop is retained separately.
- `materials/T28576_06_soft-focus-portrait.png` — one-pass 1536x1024 grayscale portrait background, softly defocused and text-free, for `focusposter32`; the sharp eye inset remains the exact crop `(268,141,357,120)` from `T28576_06.jpg`.

## Prepared image materials

- `materials/T19827_01_electromagnetic-texture.png` — one-shot built-in OpenAI image-generation cleanup based on `T19827_01.jpg`; keeps the textured charcoal, violet/green glow, and vignette while removing the source type, marks, and logo so Skia can rebuild the poster cleanly.
- `materials/T19827_06_demolition-texture.png` — one-shot built-in OpenAI image-generation cleanup based on `T19827_06.jpg`; retains the amber/violet/lime atmospheric field and grain while removing all typography and the globe, which is redrawn in Skia.
- `materials/T21458_04_distressed-red-paper.png` — one-shot built-in image-generation cleanup based on `T21458_04.jpg`; preserves the red fibrous print texture and worn edges while clearing its large numerals and labels.
- `materials/T21458_11_stadium-red-print.png` — one-shot built-in image-generation cleanup based on `T21458_11.jpg`; retains a red-printed football photograph and smoky grain while removing the source typography and logos.
- `materials/T13692_soldier-cutout.png` — crop from `T13692_03.jpg` with an OpenCV-reviewed polygon mask; no source text is baked into the cutout.
- `materials/T13692_mirror-portrait.png` — one-pass built-in image-generation output: transparent, text-free black-and-white archival-style woman/mirror portrait with visible film grain and natural skin/hair texture. The source lettering overlaps the original photograph, and this replaces the prior insert that read as AI.
- `materials/T13692_black-plastic-texture.png` — one-pass built-in image-generation output based on the black folded-plastic surfaces in `T13692_01`: a dark, low-key crumpled-polymer texture with restrained silver creases and no typography or props. Used by `zebra32`.
- `materials/T13692_06_brutalist-photo-plate.png` — generated with the built-in OpenAI image-generation tool as four clean black-and-white brutalist-architecture documentary photographs in a crop-safe contact sheet, without the typography that obscures the source photos in T13692_06. Used by `brutal32`.
- `materials/T30173_08_palm-cutout.png` — a transparent palm-pair silhouette redrawn from the layout of `T30173_08.jpg`; `duo32` uses its alpha as a separately recolorable cutout.
- `materials/T13692_07-folded-package-lines.svg` and `.png` — transparent Potrace extraction of the folded-package body in `T13692_07.jpg`, crop `(x=849, y=365, width=292, height=312)`. `brutalpack32` now uses the extracted artwork directly and draws the separate hexagonal `B` header in Skia.
- The portrait building crop in `brutalpack32` is taken from the lower-right cell of `materials/T13692_06_brutalist-photo-plate.png`; it is clipped by Skia to the T13692_07 arch shape.
- `materials/T24250_04_rio-dusk-background.png` — generated with the built-in OpenAI image-generation tool as a 3:2 aerial Rio dusk panorama: dense coastal city, Guanabara Bay, Sugarloaf-like mountain, muted sepia-olive palette, light analog grain, and no text. Used as the clean photographic background for `rio32`.
- `materials/T24507_04_saltflat-photo-crop.png` — exact crop from the unobstructed lower photo panel in `T24507_04.jpg`; `boots32` places it beneath a source-like dark sky block and softly blurred sage wash. The earlier generated `T24507_04_saltflat-photo.png` remains as an unused fallback reference.
- `materials/T24507_04_coral-cowboy-boot.png` — transparent coral-ink engraving generated with the built-in OpenAI image-generation tool, then trimmed to its alpha bounds. Skia tints the linework to match `boots32`; the interior remains transparent.
- `materials/T27673_10_red-cyan-macro-texture.png` — text-free red/cyan macro fiber image generated once for `plakatart32`, replacing the source's title-obscured rectangular artwork.
- `materials/T33110_08_red-cyan-print-texture.png` — text-free 3:2 red/cyan organic-ribbon halftone plate generated once for `birvase32`; the single-word composition is rebuilt in Skia.
- `materials/T13692_zebra-arched.png`, `materials/T13692_rose-strip.png`, `materials/T33144_thumbs-up-line-art.png`, and `originals/T33631_05-illustration.jpg` — user-prepared materials placed directly in their matching compositions.
- `materials/T23086_05_chalk-pointing-hand-source.png` — transparent extraction of the exact right-pointing white-chalk hand from `T23086_05.jpg` (crop x=650, y=235, 130×100); the black inset is discarded.
