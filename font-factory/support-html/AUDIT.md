# Support-template renderer audit

## Scope and current state

- The active support catalogue has 61 templates in 70 stable numbered slots.
- The registry has 22 retired names; nine numbered slots remain tombstones.
- The code is split across pin_studio.py (23 active layouts) and five
  support_templates modules: objects.py (9), t30332.py (9), fashion.py (7),
  photo.py (7), and poster.py (6).
- Each selected font currently receives seven eligible support images at
  2400 × 1600. Three family layouts require multiple real styles; two are
  guaranteed when their eligibility gate passes.
- All 61 active templates now have opt-in HTML/CSS prototypes, listed in catalogue order:
  line32, duo32, card32, feature32, neon32, quote32,
  crest32, contour32, mountain32, hand32, zebra32, soldier32,
  mirror32, brutal32, rio32, boots32, plakat32, plakatart32,
  mangos32, alphabet32, birvase32, weightfamily32, mangosboard32, ovalword32,
  stardust32, cliffpostcard32, kindersea32, messageframe32, contactlist32, sunsetpromise32,
  phonegarden32, pixelquote32, ravencover32, voguecover32, confident32, storyteller32,
  focusposter32, wideclaim32, blossom32, neue32, electromagnetic32, demolition32,
  yearposter32, stadiumposter32, signalclock32, amberdawn32, skinbadge32, latestlook32,
  gelatocards32, meditation32, strongweak32, funkyfashion32, typewall32, manualbrew32,
  pastpresent32, herbalproduct32, colosseum32, glyphsheet32, freakscene32, greetingsgrid32,
  roadrunner32.
  Skia remains the default renderer.

## Existing pipeline

bin/generate_font_text_placeholders.py builds per-font placeholder assets and
invokes bin/render-pins, which launches bin/pin-studio/pin_studio.py.
pin_studio.py owns font inspection, shaping/fitting, class and support
eligibility, theme/copy selection, layout verification, and image saving. The
support functions are registered from the five family modules but share that
runtime and its Skia Sheet.

The same runtime also renders Pinterest pins and factual specimen sheets.
It also uses Skia-backed font outlines for measurement, fitting, and some
contrast/layout checks. Replacing support-image composition with browser
layouts does not by itself remove those Skia call sites. OpenPencil's per-font
creative handoff is a separate path and is not the 61-template catalogue.

The HTML export itself is rasterized by headless Chromium at 2400 × 1600; it
does not draw pixels with Skia. The integrated `pin_studio.py` HTML route still
imports Skia and builds Skia-backed font outline context before dispatching the
browser render, so it is not yet a Skia-independent command. The catalogue has
61 of 61 browser contracts, but every row is still marked `prototype` and Skia
remains the default. Template props are also split between the catalogue,
per-template browser code, and the large Python `render_support_html` dispatch.
The next architecture steps are to centralize the catalogue inventory, move
template props into local adapters, separate renderer-neutral font facts from
outline analysis, and reuse one Chromium process for a multi-image batch.
The T26074-12 iteration benchmark shows the main workflow gain: browser edits
paint in 11.7–33 ms, a local font upload paints in 82 ms, and a full-size
2400 × 1600 screenshot takes about 1.9–2.1 seconds. The Skia comparison draws
in 0.75–1.63 seconds and its measured PNG optimize/write pass takes 0.97–1.07
seconds. HTML is much quicker for successive layout adjustments; the export
timings are comparable, and this benchmark alone does not prove visual parity.

## References and materials

- The updated individual-comparison set contains 334 images (about 124 MB).
  322 comparisons have a source image; 12 are fit-only because line32 and
  card32 have no source reference across the reviewed sample.
- The full support-reference tree contains 639 files, including 72 under
  `materials/` and four under `originals/`. Code and reference notes show
  that some assets support active layouts while others preserve withdrawn,
  superseded, or source-provenance work. Do not bulk-delete the unused assets.
- The material catalogue has 32 named literal references and no missing
  paths. A source scan found 13 filenames in `materials/` that are not named
  by active renderer or editor code; the broader direct-template scan has 15
  unmapped assets because it uses a different provenance criterion. Keep both
  candidate sets until their source notes are checked; do not bulk-delete.
  The 13 unmentioned files are `T24908_01_skin-portrait-background.png`,
  `T33631_mountain-pentagram-transparent.png`, `T24908_02_red-jacket-photo.png`,
  `T28576_03_editorial-face-cutout.png`, `T24507_04_saltflat-photo.png`,
  `T13692_07-folded-package-lines.svg`, `mountain-occult-screenprint-transparent.png`,
  `T30332_02_cliff-sea-background.png`, `T30332_08-clean-phone-plate.png`,
  `T30332_08_left-peony.png`, `T33631_mountain-pentagram-640.png`,
  `T28576_04_eye-illustration.png`, and `T28576_09_beach-fashion-cutout.png`.

## Visual review of the updated comparisons

These are the remaining differences from the current 334-image set, separate
from the older review. The review swept the active-template contact sheets and
checked suspected cases at full size; it is not a 334-image one-by-one fidelity
certification.

| Template | Finding | Action |
| --- | --- | --- |
| line32 | No source image was supplied for this slot; the Skia rendering is the only available visual baseline. | The HTML/CSS editor preserves the broadside layout as separate Title Case text and paper layers, with live font fitting, the outline echo, the clipped initial, and responsive controls. A Blazher edit reaches paint in 32.9 ms with clear desktop/mobile bounds; captures are under `benchmarks/line32/output/`. |
| rio32 | T24250_04 puts a destination headline over a Rio dusk panorama with top navigation, a booking capsule, and centered closing copy. The existing Skia layout substitutes unrelated art and copy. | The HTML/CSS port restores the generated panorama, source-proportioned Title Case destination, navigation, outlined booking button, and three-line footer as independent layers. The Blazher edit reaches paint in 55.6 ms at 14.58:1 contrast with clear desktop/mobile bounds; HTML exports to 4,210,846 bytes versus Skia's 4,658,905. Captures are under `benchmarks/rio32/output/`. |
| contour32 | Skia turns the reference's arrow row, orange ribbons, frame, caption, and two-line ligature specimen into a single contour glyph. | The new HTML/CSS prototype rebuilds the T30930_03 layout, keeps the source's `ADCAQO` and `STSZTTZS` specimens, and exposes glyph width, scale, tracking, and palette controls. |
| mountain32 | In the current Skia comparison, the six rows fit individually, so ascenders and descenders make the type scale jump; the final divider is missing, and the field is darker than the source. | The HTML port uses the approved mountain crop, fits all six words at one shared size, restores the bottom divider, and matches the source charcoal (#1b1b1b sampled from the reference). The Braewick comparison edits in 29.4 ms; desktop/mobile bounds are clear. The three-way comparison is in `benchmarks/mountain32/output/`. |
| contactlist32 | The CircuitSprint comparison drops the leading zeroes from all seven list indices; the source's `07. Summer on` plus `the Westhill` continuation also needs to keep one visual entry. | The HTML port layers the original cleaned index plate under the exact eight source lines, preserves every zero with readable browser fallback, and fits all rows at one shared size. Missing glyphs are reported. The current source/Skia comparison is under `class-audit-2026-10-14/individual-comparisons/tech-sports/32-contactlist32.jpg`; the new three-way render is in `benchmarks/contactlist32/output/`. |
| kindersea32 | The postcard depends on exact pixel-art seascape, corner stars, lavender grain, and a two-line white lockup; generic background reconstruction loses the print character. | The HTML/CSS port layers the cleaned source plate, pixel seascape, and extracted stars separately, and fits the two fixed lines together. The AOT Lost Contact comparison edits in 25.6 ms; desktop/mobile bounds are clear. Its 2.5:1 contrast exception preserves the original white-on-lavender treatment. The three-way comparison is in `benchmarks/kindersea32/output/`. |
| sunsetpromise32 | The original packs four equal-weight outlined lines into a tight lower stack over lavender grain; the existing boxes push the last lines toward and beyond the paper edge. | The HTML/CSS port uses the exact cleaned plate and pixel sunset, fits all four lines together, matches the source's progressively tighter vertical rhythm, and retains `DUSK / 07` when CircuitSprint lacks zero. The comparison edits in 27.5 ms; desktop/mobile bounds are clear. Captures are in `benchmarks/sunsetpromise32/output/`. |
| phonegarden32 | T30332_08 has three separate phone layouts, a source peony, rotated center lettering, and small decorative marks that are flattened or lost by a single reconstructed text area. | The HTML/CSS port preserves the three source lockups over the cleaned phone plate, layers the peony and stars separately, and fits each text system independently. The Blazher comparison edits in 28.8 ms; desktop/mobile bounds are clear, and HTML export is 1,163,285 bytes versus Skia's 1,295,333. Captures are in `benchmarks/phonegarden32/output/`. |
| pixelquote32 | The five-line quote relies on exact title case, a pink-on-black contrast floor, and four small pixel-art ornaments that disappear if reconstructed procedurally. | The HTML/CSS port reuses the exact source heart, mascot, and stitch crops, preserves the five fixed lines and source proportions, and exposes scale, tracking, and line-rhythm controls. The Blazher comparison edits in 36.6 ms, reports 6.21:1 contrast, and has no desktop/mobile overflow; HTML export is 77,664 bytes versus Skia's 103,844. Captures are in `benchmarks/pixelquote32/output/`. |
| ravencover32 | The source cover depends on a clean red-tailoring photograph, a restrained oval masthead, fine rules, and a large ivory headline across the figure. | The HTML/CSS port keeps the clean full-bleed photo and 20% veil, restores the oval and rules as separate layers, and fits the Title Case headline and supporting lines independently. The Blazher comparison edits in 39.9 ms, reports 9.77:1 against its representative photo tone under a scoped 3:1 photo exception, and has no desktop/mobile overflow; HTML export is 4,004,112 bytes versus Skia's 4,480,994. Captures are in `benchmarks/ravencover32/output/`. |
| confident32 | The source uses a very large red display word, two black supporting lines, a framed illustration, and a small centered star rule; the exact eye crop carries the most character. | The HTML/CSS port keeps the cleaned eye crop, source proportions, and separated frame, taglines, and star divider. Its Blazher comparison edits in 36.8 ms, reports 4.86:1 contrast, and has no desktop/mobile overflow; HTML export is 1,021,568 bytes versus Skia's 1,161,876. Captures are in `benchmarks/confident32/output/`. |
| focusposter32 | The source combines a blurred portrait, framed eye detail, a wide red headline, rotated edge notes, and five staggered quote columns; Skia loses the source's editorial balance and type rhythm. | The HTML/CSS port preserves the eye crop and portrait, lets the uploaded face drive the headline, and fits the Title Case quote in an italic serif. The Blazher comparison edits in 31.7 ms, reports 4.30:1 contrast, has clear desktop/mobile bounds, and exports to 1,008,811 bytes versus Skia's 1,950,305. Captures are under `benchmarks/focusposter32/output/`. |
| wideclaim32 | T28576_07 has two leading statement lines over a red/black specimen pair; current Skia adds an unrelated rule and copy that can suggest font properties it cannot guarantee. | The HTML/CSS port restores the four-line source rhythm, the live-font display words, and per-letter red/black accents. Fixed support copy uses Title Case and avoids describing the showcased face. The Blazher comparison edits in 40.7 ms, reports 4.30:1 contrast, has clear desktop/mobile bounds, and exports to 71,529 bytes versus Skia's 118,037; captures are under `benchmarks/wideclaim32/output/`. |
| roadrunner32 | Current Skia layout changes the source quote, omits the small descriptive copy and both source seals, and uses a heavier inset frame. | The HTML/CSS prototype restores these details and now renders through the opt-in pipeline. It still needs representative-font review before becoming the default. |
| crest32 | Long script descenders made the center lockup collide with the lower arc, unlike the clear three-part source composition. | The HTML/CSS prototype now reserves a source-proportioned center stage and moves the lower text path down; `getLayoutReport()` returns no hero/arc overlap for the saved same-font comparison. More script and mono face review remains. |
| neon32 | T30173_07 centers two warm script lines and a small `Coming Soon` tag on a dark theatre door, with seven glowing film-gate windows at each edge. | The HTML/CSS prototype keeps the door grain, fold, tube type, and perforations as separate layers. Its source-warm palette and independent glow controls remain live; copied text is preserved and missing face glyphs are reported. The 2400 × 1600 comparison uses Gladista Script on both renderers, edit-to-paint is 45.1 ms, and desktop/mobile bounds are clear. Captures are under `benchmarks/neon32/output/`. |
| mirror32 | T13692_12 layers a six-line high-contrast quote over a natural-aspect mirrored portrait on flat black; the first line crosses the portrait and every line shares the right edge. | The HTML/CSS port retains the approved transparent photo asset, source placement, and per-line fitting. All six lines are editable; missing quote glyphs remain visible and produce a readable-fallback warning. The Maidega source/Skia/HTML comparison edits in 22.5 ms, and desktop/mobile bounds are clear; captures are under `benchmarks/mirror32/output/`. |
| hand32 | The supplied illustration, headline proportions, caption, and original pink/ivory/black palette should stay independently editable. | The HTML/CSS prototype uses the source alpha mask, reference-led type boxes and separate caption ink. Its display contrast exception is scoped to the original low-contrast poster colors; note and editor controls retain high contrast. The source/Skia/HTML comparison and desktop/mobile editor captures are saved under `benchmarks/hand32/output/`. Broader family review remains. |
| zebra32 | The source is a pair of square, crinkled-plastic boards with a shaped photo and distinct text systems. | The HTML/CSS prototype separates both cards, preserves the real texture and source photographs, and fits the live word and eight poem lines independently. Representative-font review remains. |
| freakscene32 | The source's oversized two-line lettering and finely textured pink paper slab have more dominance than the current render. | The HTML/CSS prototype restores the reference palette, paper grain, source annotations and oval marks, and enlarges the fitted title. Representative-font review remains. |
| brutal32 | The source is a photographed two-page architectural spread; the current Skia version regularizes its staggered photo and headline overlaps. | The HTML/CSS prototype restores the source's page tones, central binding shadow, four offset photo crops, and individually fitted headline rows. Representative-font review remains. |
| duo32 | The source's palms are fine, drooping silhouettes, while procedural Skia fronds can become sharp spokes at some scales. | The HTML/CSS prototype uses a separate reference-derived transparent palm cutout, then layers the editable sun and selected-font lettering in source order. Representative-font review remains. |
| mangos32 | T30930_07 uses a compact cyan wordmark row, a variable-weight color ramp, a botanical name, and sharply aligned nutrition-style facts. | The HTML/CSS prototype restores the source copy and grid, uses separate vector marks and an editable fruit illustration, and adds live weight-axis, tracking, and palette controls. Representative-font review remains. |
| alphabet32 | The source is a specimen page with a two-line uppercase row, a smaller two-line lowercase row, a narrow descriptor column, and a separate figure line. | The HTML/CSS editor preserves those distinct widths and scales each character run to the chosen font. Its controls expose specimen scale, tracking, paper, and accent ink. |
| glyphsheet32 | The source's green ink has visible print grain, and its large sign row is specifically `$&%£€!?()`; flat fills and glyph substitution weaken the specimen. | The HTML/CSS port keeps the source symbol sequence and uses a source-derived grain tile. It retains unsupported symbols and digits through Chromium's readable font fallback, while recording missing-glyph warnings. |
| greetingsgrid32 | The Skia grid keeps the source block rhythm but omits its paper texture and small printer seals; the HTML draft's large words also sat too close to tile edges. Missing Cyrillic or accented glyphs can silently erase part of a greeting. | The port retains the offset tile geometry, adds print grain and neutral press marks, gives each word more inset space, and substitutes legible transliterations when the selected face lacks a character. The render report records those substitutions. |
| storyteller32 | The current Skia version uses a blurred framed-portrait plate in place of the source's editorial story page and drops its hands strip and much of the type hierarchy. | The HTML/CSS prototype restores the four-line editorial title, red word accents, source hands strip, framed illustrator, and lower narrative lines as separate layers. |
| yearposter32 | CircuitSprint drops the `9` from `1982` despite passing layout fit. The cream numerals also need the reference's worn, uneven print texture. | The HTML/CSS prototype keeps the paper and wear mask, preserves the raw year for browser fallback, and warns when the selected face lacks a digit. Representative-font review remains. |
| stadiumposter32 | The source's football plate and towering stepped words are distinctive, but the selected test face can change the word widths; a flat fill also loses the screenprinted feel. | The HTML/CSS prototype reuses the original football plate, fits the two display rows independently, preserves the left/right stagger, and uses a separate source-derived wear mask in the cream ink. Desktop and mobile layout reports are in `benchmarks/stadiumposter32/output/benchmark.json`; the tested headline edit reached paint in 16.6 ms. |
| signalclock32 | With CircuitSprint, `$50.50` loses both zeroes and reads as `$55`; the red tag also crowds the final digit, though fit passes. | The HTML/CSS path keeps the raw price string so Chromium draws missing digits with a readable fallback and reports the gap. A price-width control keeps the source's intentional tag-over-final-digit overlap consistent across narrow and wide faces. |
| amberdawn32 | The source layers oversized lemon brush lettering over the model, with a circular three-font seal and low, widely spaced footer. | The HTML/CSS prototype preserves the original photo plate and rebuilds centered live display lines, the seal, and footer independently. Its source/Skia/HTML comparison and responsive editor captures are saved in `benchmarks/amberdawn32/output/`. |
| skinbadge32 | The skincare graphic depends on two overlapping circular seals, repeated brush lettering clipped to the rear seal, fine curved rim copy, scattered stars, and a heavy hand-painted underline. | The HTML/CSS prototype keeps the clean portrait plate and uses independent clipped seals, SVG text paths and star marks, live headline fitting, and a shaped swash. Its source/Skia/HTML comparison and responsive editor captures are saved in `benchmarks/skinbadge32/output/`. |
| latestlook32 | The lookbook reference places three large white display lines over the red jacket and stone wall, with a sparse two-part footer separated by a short rule. | The HTML/CSS prototype reuses the clean photo plate, independently fits the three headline rows, and stacks each small footer caption clear of the rule. Its source/Skia/HTML comparison and responsive editor captures are saved in `benchmarks/latestlook32/output/`; the live line edit reached paint in 19.9 ms. |
| gelatocards32 | The source uses two offset rounded cards, separate pink and cobalt ice-cream line patterns, and a live cone-shop crop visible around the edges. | The HTML/CSS prototype clips the original pattern assets into independent cards and layers the offset shadows, separately fitted front and rear headings, labels, and footer. Its source/Skia/HTML comparison and responsive editor captures are saved in `benchmarks/gelatocards32/output/`; all text stays inside the cards at desktop and mobile editor widths. |
| meditation32 | The poster balances a very large white `MEDITATION` headline and iridescent bubbles against soft pastel print, a photographic shore panel, and the source's pink `DISC 30%` burst. | The HTML/CSS prototype keeps the bubbles, textured color field, framed stone photograph, star details, discount burst, and original September 30, 2025 date and URL footer as editable layers. Its source/Skia/HTML comparisons and responsive editor captures are in `benchmarks/meditation32/output/`; the tested headline edit reached paint in 23.7 ms. |
| strongweak32 | The source relies on a scalloped pink frame, cobalt inset, deep blue registration shadows, oversized specimen words, and two comic stickers. | The HTML/CSS prototype builds the scallops from individually positioned circles, fits the two display words separately, and preserves the `YOUNGTYPE STUDIO`, `HAND DRAWN`, `STROKE / REGULAR / OUTLINE`, and `ORGANIC HAND DRAWN` copy. Its source/Skia/HTML comparisons and responsive editor captures are in `benchmarks/strongweak32/output/`; the tested line edit reached paint in 39.7 ms. |
| funkyfashion32 | The original flyer overlaps cream display lettering with an orange-backed cutout portrait, dotted arrow, layered smiley sticker, lightning bolt, designer name, and a specific paragraph. | The HTML/CSS prototype uses the source portrait cutout, separates the cream headline and exact copy into fitted layers, and redraws the sticker and bolt as scalable vectors. It adds responsive type fitting while retaining the source's two-tone print shadows. Its source/Skia/HTML comparison and responsive editor captures are in `benchmarks/funkyfashion32/output/`; the headline edit reached paint in 25.3 ms. |
| typewall32 | T26223_02 is a tightly cropped field of oversized dark words on vivid yellow, with every row following one diagonal rhythm. | The HTML/CSS prototype repeats each editable specimen line only as needed to keep the surface full when the selected face is narrower than the source display face. Tilt, type scale, row spacing, and horizontal stagger remain live controls. Its source/Skia/HTML comparison and desktop/mobile editor captures are in `benchmarks/typewall32/output/`; the row edit reached paint in 42 ms. |
| manualbrew32 | T26223_03 uses two large, individually colored rounded words on charcoal with a tiny centered studio credit; letter height and line position set the print rhythm. | The HTML/CSS prototype restores the source copy, per-letter palette order, and rounded credit font. It fits the two rows independently and exposes adjustable letter height, tracking, palette, and line separation. Lilita One is the source-matched benchmark face while the uploaded display font remains live. Desktop/mobile layout reports are in `benchmarks/manualbrew32/output/benchmark.json`; the word edit reached paint in 26.7 ms. |
| pastpresent32 | T26223_04 combines pink gingham with three separate retro sign shapes, illustrated hand badges, centered labels, and a tiny studio credit. | The HTML/CSS prototype layers editable fitted words over a reference-derived blank sign plate, scales the gingham to the source rhythm, and positions each label within its own sign. It uses the bundled rounded credit face and preserves an uploaded live display font. Its source/Skia/HTML comparison and responsive editor captures are in `benchmarks/pastpresent32/output/`; a sign edit reached paint in 23.9 ms. |
| herbalproduct32 | The source combines a green carton, inset cream-and-yellow frame, orange `NEW` burst, botanical crest, batch oval, rounded `HERBALS` title, outlined coffee description, and three compact detail columns. | The HTML/CSS prototype keeps these elements as live source-scaled layers. It preserves full batch/date/process/weight strings and reports missing display glyphs while Chromium renders readable fallbacks; process and date remain two-line editable controls. The same-face comparison is under `benchmarks/herbalproduct32/output/`. |
| soldier32 | CircuitSprint drops the `9` in `1935` and reduces `1234567890` to `12345678`; the year also loses its leading hierarchy below the photo. | The HTML/CSS prototype now matches T13692_03's clipped photo, frame divisions, date, headline, and both specimen rows. It restores the full `1234567890` and `!?$¢€£&` source strings, with browser fallback glyphs and a report warning when the selected face lacks characters. Representative-font review remains. |
| glyphsheet32 | CircuitSprint renders `0123456789` as `12345678`, weakening the core figure specimen; the source symbols need coverage review too. | The HTML port now keeps `0123456789` and `$&%£€!?()` intact and warns which characters need readable fallback glyphs. A Kaitten render keeps the full row and warns for `£` and `€`. |
| boots32 | The Skia boot illustration is cut off at the right and bottom edges, while the source shows the full engraving over the landscape photo. | The HTML/CSS prototype restores the split dark-sky and salt-flat portrait, builds source-scaled engraved horseshoes as independent vectors, and tints the supplied full boot with a coral alpha mask inset from both edges. Title, subtitle, portrait framing, horseshoes, and boot placement are adjustable; representative-font review remains. |
| voguecover32 | Skia reduces the T28576_03 cover to a sparse headline and portrait, dropping the tall editorial column and several lower cover lines. | The HTML/CSS prototype restores the stacked issue mark, three-line left column, lower editorial block, and right feature deck around the supplied portrait; multiline copy and scale controls are live. The final 2400 × 1600 export has no off-canvas elements and reports 17.62:1 ink contrast. |
| demolition32 | Four specimen lines collide in the handwritten comparison; the source keeps its geometric rows distinct and evenly spaced. | The HTML/CSS prototype keeps the supplied color field, independently fits the four source rows, and restores the archive caption and twin-globe mark. The fifth-percentile contrast is 2.85:1, matching the source's charcoal ink over active color; the artboard render has no off-canvas elements. |
| colosseum32 | T26074_01 is a warm, textured specimen with three centered display lines, the exact `gröngöling` spelling, and a compact red publisher footer. | The HTML prototype restores the paper grain, exact copy, and separated footer layers. Representative-font coverage remains. |
| stardust32 | The portrait crop/material differs from the lighter source portrait, though the broad hierarchy is similar. | Keep untouched as requested; retain as a known source-material difference. |
| blossom32 | The current red panel is slightly less vivid than the reference. | Leave in its reverted state as requested. |

The review also confirmed source-geometry problems in the Skia versions of
`typewall32` and `roadrunner32`; their HTML prototypes restore the diagonal
repeat and three-line quote hierarchy. Per the user's instruction,
`stardust32` and `blossom32` are excluded from this review.

### Follow-up contact-sheet sweep — 2026-10-15

I visually swept all 334 updated individual comparisons. The set has 322
source-backed comparisons and 12 fit-only images; all report a clean layout
fit, which does not guarantee source fidelity or glyph coverage. These findings
add to the earlier review above and are limited to newly checked items. Each
template links to its current source/Skia panel. Where noted, I also checked
the saved three-way HTML capture.

| Template | Finding in the updated source/Skia comparison | HTML/CSS cross-check |
| --- | --- | --- |
| [alphabet32](../support-references/class-audit-2026-10-14/individual-comparisons/tech-sports/23-alphabet32.jpg) | CircuitSprint repeats the uppercase specimen where the lowercase rows belong and renders `#12345678`, omitting `0` and `9`, despite a clean fit result. | The saved Gladista three-way comparison preserves separate upper/lower rows and the full `#0123456789` figure string. |
| [feature32](../support-references/class-audit-2026-10-14/individual-comparisons/tech-sports/04-feature32.jpg) | The source's `Crystal` specimen and feature labels were replaced by generic copy in the Skia comparison. | The live HTML editor uses `Crystal`, `Discretionary Ligatures`, and `Stylistic Alternate`, matching the source wording. Refresh the saved capture after the final design pass. |
| [plakat32](../support-references/class-audit-2026-10-14/individual-comparisons/tech-sports/20-plakat32.jpg) | The source's `Plakat` headline and compact variable-font proof are replaced by `Poster Type` and a different glyph/specimen block. | The live HTML design restores `Plakat`, the source-like glyph strip, actual glyph/style facts, and dynamically positioned style rails. Its saved comparison predates the latest rail and copy changes. |
| [plakatart32](../support-references/class-audit-2026-10-14/individual-comparisons/blackletter/21-plakatart32.jpg) | The source places a large `Plakat` across the lower-left of the textured image with a narrow information rail; the Skia render changes the wording and recentres the title over the image. | The live HTML design now puts `Plakat` at the lower-left edge and restores a seven-line rail with selected-font style count, variable-font status, weight range, and italics support. Its updated capture is pending. |
| [birvase32](../support-references/class-audit-2026-10-14/individual-comparisons/blackletter/24-birvase32.jpg) | The source word `BIRVASE` becomes `VIVID FORM`, and the displayed phrase expands across the print field. | The live HTML editor now uses the source word `Birvase`; the saved render still shows the earlier substitute. |
| [mangosboard32](../support-references/class-audit-2026-10-14/individual-comparisons/family/26-mangosboard32.jpg) | The source is a Mango family and glyph proof; the selected Lindgre family output changes its labels and symbol specimen, so the pair is not a like-for-like font-family check. | The live HTML design now uses actual family/style names, the source glyph sequence, a variable-or-family label based on `fvar`, and a repeated Mangos sample in the lower card. Its saved capture predates these corrections. |
| [ovalword32](../support-references/class-audit-2026-10-14/individual-comparisons/display/27-ovalword32.jpg) | The source's central `Sadie` word had been replaced by `Daydream` in the Skia comparison. | The Skia fallback and live HTML design now use the source's `Sadie`, `T&N Type Co.` and `Display Sans` lines. Saved captures predate these copy corrections. |
| [weightfamily32](../support-references/class-audit-2026-10-14/individual-comparisons/family/25-weightfamily32.jpg) | The source shows Thin, Regular, and Bold; the comparison family has only Regular and Italic, so its two-style output cannot be compared as a three-weight match. | The HTML capture correctly labels the two available styles. Use a matching three-weight family for a direct source-fidelity comparison. |


## Additional catalogue ports

The catalogue now includes browser prototypes for these active layouts:

| Template | Current HTML/CSS direction |
| --- | --- |
| card32 | Paper-stack specimen with independently fitted wording and layered paper. |
| plakat32 | Source-title specimen with a cyan glyph band, selected-font glyph/style facts, and navy texture. |
| plakatart32 | Lower-left `Plakat` wordmark over the red/cyan macro-texture, with a compact, font-aware specification rail. |
| birvase32 | One editable specimen word over the saved red/cyan print texture. |
| weightfamily32 | Alphabet proof with live thin, regular, and bold settings; available sibling styles form separate proof rows. |
| mangosboard32 | Orange/ivory family cards, the source glyph strip, and three color tiles with the repeated Mangos sample. |
| ovalword32 | Rebuilt oval lockup over the cleaned pearlescent field, with the source `T&N Type Co.` credit, `Sadie` word, and `Display Sans` line. |
| stardust32 | Monochrome portrait plate with editable editorial headline, footer, and checker detail. |
| blossom32 | Wellness portrait illustration paired with a red campaign panel and editable call to action. |
| neue32 | Stepped repetition and angled signal pills on the original pink palette. |
| electromagnetic32 | Violet/green signal stack, rails, and globe rebuilt as editable browser layers. |

These remain opt-in prototypes. The current 61-image Title Case export is a
single-font catalogue pass and does not replace representative-family fidelity
review.

## Systemic validation gap

The current `support_fits` gate checks layout eligibility, not complete glyph
coverage. The existing `bin/check_support_glyph_coverage.py` audit identified
greeting, currency, and numeral gaps; the CircuitSprint comparisons also show
that `soldier32`, `yearposter32`, `signalclock32`, `herbalproduct32`, and
`glyphsheet32` can lose digits while passing fit. The HTML paths now preserve
the requested copy and surface missing-font warnings, including the full
glyphsheet digit and symbol strings. Keep using the existing coverage audit
and do not treat a clean fit result as proof that all copy rendered.

## Port plan

Newly authored display copy uses Title Case: each word begins with a capital
letter, while fonts designed for capitals can render those glyphs naturally.
All 61 templates now have browser ports. The 61-image Title Case export under
`benchmarks/titlecase-rerender-2026-10-15/` was refreshed after the latest
source-layout changes. `render_template.mjs` applies Title Case to copy props
before fitting while preserving literal alphabet, glyph, digit, symbol, and
colour data. The pass recorded zero layout/frame errors and four font-coverage
notices. It uses one font, so it cannot replace representative-family
comparison captures.

1. Keep a single catalogue manifest with the stable slot, source mapping,
   required input fields, local materials, and port status for every template.
2. Port source-backed designs through the shared browser contract. All 61
   prototype IDs listed in Scope have editable HTML/CSS artboards, use
   `configureTemplate` and `getLayoutReport`, and export through the
   catalogue-selected Chromium runner behind `--support-renderer html/hybrid`.
   Each keeps the selected display font; several also use local label fonts.
   Review them over representative font classes before rollout. The active
   line32 and card32 records have no source reference in the current corpus,
   so keep their existing visual designs while moving their layout surface.
3. Compare both renderers over representative fonts and classes. Verify the
   copy, glyphs, fit/bounds, image crops, color/contrast, and exported frame.
4. Preserve family-style eligibility, deterministic selection, and the two
   guaranteed family panels across the existing browser ports.
5. Run the full class comparison set and inspect a contact sheet plus
   difficult templates individually. Switch production output only after
   parity and then remove Skia only from the support-rendering path.

The browser benchmark demonstrates a faster visual adjustment loop, but this
does not claim completed parity or a production rollout. All 61 active support
templates have browser prototypes; Skia remains the default and is still used
by the separate pin/specimen call sites.

## Renderer throughput follow-up — 2026-10-15

A seven-template HTML render using Kaitten Modern Sans took 79.5 seconds
before the Python PNG pass was removed. Timing the same seven images showed
Pillow's `optimize=True` re-encode accounted for about 54 seconds. Chromium's
PNG export is now validated for dimensions and retained as-is. The same render
then took 24.8 seconds, a 69% wall-time reduction. All seven output images are
pixel-identical to the prior optimized files; total PNG size rose from 9.7 MiB
to about 10.3 MiB. The renderer still validates the 2400 × 1600 frame and
preserves its missing-glyph warning for the selected Kaitten face.

The source review also corrected four specimen-word fallbacks: `feature32` now
uses `Crystal`; `plakat32` and `plakatart32` use `Plakat`; `birvase32` uses
`Birvase`. The fallback words stay in Title Case, including the wordmark whose
source reference is all caps. The full 61-template HTML catalogue was freshly
exported after the latest source edits; see
`benchmarks/titlecase-rerender-2026-10-15/render-manifest.json` and its four
overview sheets. The shared export path capitalizes each copy word, protects
URLs, and keeps literal glyph runs unchanged. `plakat32` derives its glyph and
family-style counts from selected files, uses separate endpoint labels, and
positions each rail marker from the selected font's weight and italic support.
The `plakatart32` rail now reports selected-font facts while retaining the
source's cyan labels, left column, macro texture, and low-set wordmark.
Representative-family HTML comparisons remain separate work.

## Source copy and casing pass — 2026-10-15

The latest design edit pass applies Title Case to authored display copy in
both the browser prototypes and Skia support fallbacks. Each word starts with
a capital; URLs stay lowercase, and literal alphabet, ligature, digit, and
symbol specimens keep their actual characters. This also corrects leftover
all-caps Skia labels in the zebra poem, weight-axis cards, and postcard footers,
and replaces a few old all-caps placeholders in the hand, crest, and Freak
Scene editor artboards.

The source-led copy was checked again for `amberdawn32`, `ravencover32`,
`confident32`, `voguecover32`, `stadiumposter32`, and `neon32`. Their current
defaults preserve the source wording and hierarchy in Title Case. A fresh
61-image HTML export now captures the current catalogue state under
`benchmarks/titlecase-rerender-2026-10-15/`; it reports zero render/layout
errors and four font-coverage notices. The separate 334-image individual set
still compares source references with Skia outputs; it does not yet contain a
representative-font HTML replacement for each comparison.

The audit's representative-font review flags still apply after that refresh,
including `roadrunner32`, `crest32`, `hand32`, `zebra32`, `freakscene32`,
`brutal32`, `duo32`, `mangos32`, `skinbadge32`, `yearposter32`, `soldier32`,
`boots32`, and `colosseum32`. The saved representative comparisons also need
refreshing for `alphabet32`, `feature32`, `plakat32`, `plakatart32`,
`birvase32`, `mangosboard32`, and `ovalword32`; `weightfamily32` needs a
source-matched family with Thin, Regular, and Bold. `line32` and `card32` have
no source images, while `stardust32` and `blossom32` remain excluded from
design revision per the earlier instruction.
