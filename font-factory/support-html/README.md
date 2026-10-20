# HTML/CSS support-template renderer

This directory contains browser editors and renderers for the support-image
catalogue. The native Skia set remains 61 layouts across 70 stable slots; 14
new source-led remakes are HTML-only. `catalog.json` records stable template
slots, source/module mappings, and port status.

## T26074_12 design benchmark

Open benchmarks/T26074-12/layout-editor.html through a local web server from
the repository root. The editor compares the original reference beside a
source-led HTML/CSS recreation. Its live controls adjust the headline angle,
size, vertical position, line breaks, uploaded local font, and palette. Headline
size reflows for the chosen font and copy. The SVG stamp, CSS shapes, image
texture, and text remain separate layers.

The capture script exports the artboard at 2400 × 1600 and records browser edit
and export timings:

    python -m http.server 8812
    node font-factory/support-html/benchmarks/T26074-12/capture.mjs

The generated screenshots and timing reports are under
benchmarks/T26074-12/output/. comparison.png places the source, current Skia
template output, and HTML/CSS recreation side by side. The recreation is a
source-specific design study and the editor for the opt-in dynamic
roadrunner32 prototype.

The headless renderer accepts a font, multiline headline, angle, size,
label font, descriptor, bottom copy, badge, and palette, then saves a
2400 × 1600 PNG and a JSON record:

    node font-factory/support-html/benchmarks/T26074-12/render_roadrunner.mjs --font /path/to/font.ttf --headline 'Got the radio\non, I am like the\nroadrunner.' --out /tmp/road.png

The Python renderer can exercise the migrated entry from the normal catalogue
job. Use `hybrid` when a selected set mixes browser prototypes with Skia-only
templates; `html` requires every selected template to have a port:

    bin/pin-studio/.venv/bin/python bin/pin-studio/pin_studio.py --font /path/to/font.ttf --class sports --supports --support-renderer hybrid --out /tmp/support-output

The catalogue records each template's browser editor and port status. The 61 native support layouts have HTML/CSS prototypes; the 14 additional references are registered for HTML and hybrid runs only:

`line32`, `duo32`, `card32`, `feature32`, `neon32`, `quote32`,
`crest32`, `contour32`, `mountain32`, `hand32`, `zebra32`, `soldier32`,
`mirror32`, `brutal32`, `rio32`, `boots32`, `plakat32`, `plakatart32`,
`mangos32`, `alphabet32`, `birvase32`, `weightfamily32`, `mangosboard32`, `ovalword32`,
`stardust32`, `cliffpostcard32`, `kindersea32`, `messageframe32`, `contactlist32`, `sunsetpromise32`,
`phonegarden32`, `pixelquote32`, `ravencover32`, `voguecover32`, `confident32`, `storyteller32`,
`focusposter32`, `wideclaim32`, `blossom32`, `neue32`, `electromagnetic32`, `demolition32`,
`yearposter32`, `stadiumposter32`, `signalclock32`, `amberdawn32`, `skinbadge32`, `latestlook32`,
`gelatocards32`, `meditation32`, `strongweak32`, `funkyfashion32`, `typewall32`, `manualbrew32`,
`pastpresent32`, `herbalproduct32`, `colosseum32`, `glyphsheet32`, `freakscene32`, `greetingsgrid32`,
`roadrunner32`.

Each exposes the same `configureTemplate(props)` and `getLayoutReport()` browser contract and uses the shared `render_template.mjs` Playwright exporter. The specimen editors share font upload, fit controls, bounds/contrast reporting, and the responsive editor shell while keeping artwork in per-template CSS and JS. Newly authored display copy uses Title Case: each word starts with a capital letter, while alphabet and glyph specimen strings retain their literal forms.

The current 71-image Title Case review—61 active layouts and 10 blackletter
variants—and its five overview sheets are under
`benchmarks/titlecase-rerender-2026-10-15/`. All renders, sheets, the manifest,
and searchable gallery are kept together there. The manifest records four
readable-fallback notices for glyphs Kaitten lacks.
The exporter title-cases copy props before fitting and preserves literal
alphabet, glyph, digit, and symbol specimens. This single-font pass checks copy
casing and fit but does not replace representative-family review.

The remaining catalogue prototypes include the paper-stack baseline (`card32`); the red/cyan print studies (`plakat32`, `plakatart32`, and `birvase32`); the real-style family proof (`weightfamily32`); the three-card colour specimen (`mangosboard32`); the pearlescent oval wordmark (`ovalword32`); the wellness portrait layouts (`stardust32` and `blossom32`); the stepped repetition poster (`neue32`); and the violet/green signal board (`electromagnetic32`). Their source-led editors and captures are grouped under `templates/` and `benchmarks/`.

The normal job can select a renderer in its visual plan with
`support_renderer: "skia"`, `"hybrid"`, or `"html"`. The default remains Skia.

`templates/mountain32/editor.html` rebuilds T33631_05 around its original
engraving crop. It restores the sixth divider, matches the reference charcoal,
and fits all six specimen words to a shared type size so their line rhythm does
not jump around with glyph ascenders and descenders. The controls tune the word
scale, row spacing, number size, illustration scale, and column start while
preserving the locked copy and palette. The source/Skia/HTML comparison and
desktop/mobile captures are under `benchmarks/mountain32/output/`; the shared
`SupportLayout.fitLinesTogether()` helper makes this common-size fitting
available to other row-based layouts.

`templates/contactlist32/editor.html` uses the text-clean T30332_06 index plate,
including its original navy frame, hanging pastel tabs, and pink nodes. It keeps
the seven numbered titles and the unnumbered `the Westhill` continuation as
eight live rows, preserving leading zeroes and reporting font-coverage gaps.
All eight rows share a fitted type size; the controls tune list scale, spacing,
position, and width without moving the lower tab labels. The source/Skia/HTML
comparison and responsive captures are under `benchmarks/contactlist32/output/`.

`templates/messageframe32/editor.html` preserves T30332_05's lavender paper,
hand-drawn frame, pins, hearts, sparkles, and dot fields on its cleaned source
plate. Four source quote lines share one fitted size; the two white margin
labels remain separate, adjustable browser layers. The source labels keep a
scoped contrast exception because they sit in the original lavender texture.
The source/Skia/HTML comparison and responsive captures are in
`benchmarks/messageframe32/output/`.

`templates/cliffpostcard32/editor.html` rebuilds T30332_02 over the cleaned
source photograph, retaining the torn paper edge, sky, hiker, and rock. The two
fixed headline rows share a fitted size and stay clear of the figure; small
neutral captions replace the source foundry and font names. The controls tune
headline scale, tracking, and vertical rhythm. The source/Skia/HTML comparison
and responsive captures are in `benchmarks/cliffpostcard32/output/`.

`templates/kindersea32/editor.html` rebuilds T30332_04 with the cleaned
lavender paper, nearest-neighbor pixel seascape and transparent corner stars.
The two fixed headline rows share a fitted size; headline scale, art scale, row
spacing, tracking and neutral captions remain separate controls. Its AOT Lost
Contact source/Skia/HTML comparison and desktop/mobile captures are in
`benchmarks/kindersea32/output/`; the edit reached paint in 25.6 ms. Both
editor widths stay in bounds, and the 2400 × 1600 HTML export is 2,250,079
bytes versus 2,339,692 for Skia. White text keeps the source's lavender
treatment under a scoped 2.5:1 contrast exception.

`templates/sunsetpromise32/editor.html` restores T30332_07's lavender floral
plate, original pixel-sunset panel, globe and corner marks. Four fixed lines
share one fitted size and a source-matched dark outline; their tighter lower
spacing follows the reference artwork rather than the old Skia box positions.
Its CircuitSprint source/Skia/HTML comparison and responsive editor captures
are under `benchmarks/sunsetpromise32/output/`. The HTML path retains the full
`DUSK / 07` label when the test face omits zero, edits in 27.5 ms, has no
desktop/mobile overflow, and exports to 3,731,991 bytes versus Skia's
4,139,188 bytes.

`templates/phonegarden32/editor.html` rebuilds T30332_08 as three distinct
phone screens over the exact cleaned plate. It layers the source peony and
stars, preserves the broken left wordmark, rotated center lockup, and
right-screen message, and fits each text system independently. Its Blazher
source/Skia/HTML comparison and responsive captures are under
`benchmarks/phonegarden32/output/`; the edit reached paint in 28.8 ms,
desktop/mobile bounds are clear, and the 2400 × 1600 HTML export is 1,163,285
bytes versus 1,295,333 for Skia.

`templates/pixelquote32/editor.html` rebuilds T30332_09's five-line quote on
the locked hot-pink-on-black field. Its source pixel heart, mascot, and corner
stitches remain exact nearest-neighbor layers. Each line fits the original
source-proportioned box; scale, tracking, and vertical rhythm stay adjustable.
The Blazher source/Skia/HTML comparison and responsive captures are in
`benchmarks/pixelquote32/output/`; the edit reached paint in 36.6 ms, contrast
is 6.21:1, desktop/mobile bounds are clear, and the 2400 × 1600 HTML export is
77,664 bytes versus 103,844 for Skia.

`templates/ravencover32/editor.html` rebuilds T28660_00 over the clean red
tailoring photo, preserving the 20% veil, fine cover rules, and outlined oval
issue mark. The headline, issue label, and two supporting lines remain separate
Title Case text layers with independent scale, tracking, vertical position, and
photo-shade controls. The Blazher comparison edits in 39.9 ms, reports 9.77:1
against a representative photo tone under a scoped 3:1 photo exception, has
clear desktop/mobile bounds, and exports to 4,004,112 bytes versus Skia's
4,480,994 bytes. Source/Skia/HTML and responsive captures are under
`benchmarks/ravencover32/output/`.

`templates/confident32/editor.html` rebuilds T28576_04's framed confidence
poster around its cleaned, high-contrast eye crop. The red Title Case headline,
paired taglines, paper rules, and center star ornament remain separate; eye
framing, headline scale and position, tracking, and tagline scale can be tuned.
Blazher source/Skia/HTML and responsive captures are under
`benchmarks/confident32/output/`; the editor reaches paint in 36.8 ms, contrast
is 4.86:1, desktop/mobile bounds are clear, and the 2400 × 1600 HTML export is
1,021,568 bytes versus 1,161,876 for Skia.

`templates/focusposter32/editor.html` rebuilds T28576_06 around its exact eye
detail crop and blurred portrait. The uploaded display face drives the headline;
rotated Title Case edge notes and five staggered italic-serif quote columns stay
independently editable. The original vivid red ink keeps a scoped 3:1 contrast
exception. The Blazher comparison edits in 31.7 ms, reports 4.30:1 contrast,
has clear desktop/mobile bounds, and exports to 1,008,811 bytes versus Skia's
1,950,305 bytes. Captures are under `benchmarks/focusposter32/output/`.

`templates/wideclaim32/editor.html` restores T28576_07's four-line paper
composition. The two-line statement and oversized specimen words stay live in
the uploaded font; the second word keeps its alternating red/black letters.
All copy uses Title Case, and the source red keeps a scoped contrast exception.
The Blazher comparison edits in 40.7 ms, reports 4.30:1 contrast, has clear
desktop/mobile bounds, and exports to 71,529 bytes versus Skia's 118,037 bytes.
Source/Skia/HTML and responsive captures are under
`benchmarks/wideclaim32/output/`.

`templates/line32/editor.html` preserves the existing Skia broadside because
the slot has no source reference. Its title, overline, edge note, and footer
are Title Case in the editor; the uploaded face can render capitals naturally.
The Blazher edit reaches paint in 32.9 ms with clear desktop/mobile bounds.
Captures are under `benchmarks/line32/output/`.

`templates/rio32/editor.html` rebuilds T24250_04 over the separate clean Rio
panorama. The destination title stays in the uploaded display face; navigation,
the outlined booking control, and the three-line close remain separate layers.
Copy uses Title Case and the panorama position and title scale are adjustable.
The Blazher edit reaches paint in 55.6 ms at 14.58:1 contrast with clear
desktop/mobile bounds; HTML exports to 4,210,846 bytes versus Skia's 4,658,905.
Captures are under `benchmarks/rio32/output/`.

Open `templates/quote32/editor.html` through the same local server to iterate
on T24954_05, `templates/feature32/editor.html` for T27485_07,
`templates/crest32/editor.html` for T27485_08, or
`templates/hand32/editor.html` for T33144_02. They provide live layout controls,
local font upload, a source comparison, and the same fixed 2400 × 1600 export
frame. `hand32` keeps the supplied hand illustration as an independently
tintable alpha-mask layer.
`templates/zebra32/editor.html` rebuilds T13692_01 as two independent square
boards, preserving its source plastic texture and separate zebra and rose
assets while fitting each live copy line independently.
Its source/Skia/HTML comparison and responsive editor captures are in
`benchmarks/zebra32/output/`. Run
`node font-factory/support-html/benchmarks/zebra32/capture.mjs` to refresh them
after updating the saved renderer outputs.
`templates/freakscene32/editor.html` rebuilds T26074_03 with its lemon field,
finely grained pink slab, enlarged two-line lettering, rotated source notes, and
hand-drawn oval printer marks. Its source/Skia/HTML comparison and responsive
editor captures are saved under `benchmarks/freakscene32/output/`.
`templates/brutal32/editor.html` rebuilds T13692_06 with source-proportioned
page tones, the offset architectural photo crops, an ink-dark center fold, and
four independently fitted title rows that cross the photography. Its editor
supports live copy, font, scale, and tracking changes. Source/Skia/HTML,
desktop/mobile, and edit-to-paint benchmark outputs are under
`benchmarks/brutal32/output/`; refresh them with
`node font-factory/support-html/benchmarks/brutal32/capture.mjs` after updating
the saved Skia and HTML exports. The same-face 2400 × 1600 sample exports to
2,049,646 bytes in HTML/CSS and 971,747 bytes in Skia; the captured single
headline edit reached paint in about 18 ms on Chromium 153.
`templates/neon32/editor.html` rebuilds T30173_07 as a photographed theatre-door marquee: the two script rows, centered `Coming Soon`, warm glass bloom, dark wall fold and grain, and paired seven-window film gates are independent layers. Its source-led palette is the default, while copy, tube color, glow spread, gate brightness, and wall tone stay editable. Missing display glyphs remain in the phrase and raise a readable-fallback warning. The source/Skia/HTML comparison, responsive editor captures, and browser edit timing are under `benchmarks/neon32/output/`; refresh them with `node font-factory/support-html/benchmarks/neon32/capture.mjs` after updating the saved Skia and HTML exports. Both renderer samples use Gladista Script; an edit reached paint in 45.1 ms. At 2400 × 1600, the HTML/Skia PNGs are 3,366,691/1,121,291 bytes, and desktop/mobile reports show no out-of-bounds elements.
`templates/mirror32/editor.html` restores T13692_12 with the approved transparent portrait at its natural aspect ratio, six right-aligned editable quotation lines, and the original black field. The long first line crosses the image as it does in the source. Missing quote glyphs remain visible with an explicit fallback warning. Its source/Skia/HTML comparison and responsive browser captures are under `benchmarks/mirror32/output/`; both renderer samples use Maidega, a quote edit reached paint in 22.5 ms, and desktop/mobile bounds are clear. At 2400 × 1600, the HTML/Skia PNGs are 1,100,498/1,254,297 bytes.
`templates/duo32/editor.html` rebuilds T30173_08 with the oversized initial,
crossing word, coral sun, screenprint grain, and an independently tintable,
transparent palm cutout derived from the reference. The editor fits the live
display font to the initial and crossing word and allows copy, palette, and
grain iteration without redrawing the palm illustration. Its source/Skia/HTML
comparison, responsive editor captures, and browser edit timing are under
`benchmarks/duo32/output/`; run
`node font-factory/support-html/benchmarks/duo32/capture.mjs` after updating the
saved Skia and HTML exports.
`templates/mangos32/editor.html` rebuilds T30930_07 as a source-proportioned
botanical specimen: cyan identity marks, a warm-to-ink weight ramp, a large
Latin name, the original nutrition-style facts, and an editable fruit glyph.
The browser editor supports a live weight axis, tracking, local font upload,
and palette tuning. Source/Skia/HTML comparisons, responsive captures, and the
edit-to-paint record are under `benchmarks/mangos32/output/`.
`templates/alphabet32/editor.html`, `templates/glyphsheet32/editor.html`, and
`templates/greetingsgrid32/editor.html` add source-led editable type specimens.
The alphabet keeps five independently fitted character runs; the glyph sheet
restores the source currency row and paper grain; the greeting grid preserves
its asymmetrical blocks, print texture, inset headline margins, and small
printer seals. Both symbol-heavy designs report readable fallbacks when the
selected face lacks a required character.
`templates/storyteller32/editor.html` restores the source's editorial column,
artist illustration, hands strip, and red emphasis as separate layers.
`templates/voguecover32/editor.html` restores T28576_03's oversized masthead,
overprinted portrait, stacked issue label, three-row editorial copy, and
lower-right feature block with live multiline controls.
`templates/demolition32/editor.html` keeps T19827_06's exact prismatic field,
restores its twin-globe stamp and archive caption, and fits each display line
independently so handwriting styles no longer collide.
`templates/yearposter32/editor.html` uses the original distressed paper plate
as its ground and a source-derived wear mask on the editable year lettering.
Unsupported digits stay visible in a browser fallback, with a clear warning when
the selected display face lacks a year glyph.
`templates/stadiumposter32/editor.html` keeps the original football plate,
rebuilds the headline as two individually fitted live lines, and carries a
reference-derived wear mask into the cream ink. The editor exposes the first
and second lines independently, so you can rebalance the stadium hierarchy
directly. Its source/Skia/HTML comparison and
desktop/mobile editor captures are under `benchmarks/stadiumposter32/output/`;
run `node font-factory/support-html/benchmarks/stadiumposter32/capture.mjs`
after updating the saved renderer images. The 2400 × 1600 same-face export is
about 4.82 MB in HTML/CSS and 4.21 MB in Skia; its headline edit reached paint in
16.6 ms on Chromium 153.
`templates/signalclock32/editor.html` rebuilds the source's spare black price
composition with a live fitted value and the overlapping chamfered DOLLAR tab.
The price and condensed tag lettering have separate font pickers; a Noto Sans
Condensed light face supplies a source-like tag label until one is uploaded.
The editor now preserves unsupported price characters with visible browser
fallbacks and a warning, and its price-width control keeps the tab's overlap
consistent as display-font widths change.
Its source/Skia/HTML comparison and desktop/mobile editor captures are under
`benchmarks/signalclock32/output/`; run
`node font-factory/support-html/benchmarks/signalclock32/capture.mjs` after
updating the saved renderer images. The refreshed 2400 × 1600 same-face export
is 106 KB in HTML/CSS and 102 KB in Skia; its price edit reached paint in
17.3 ms on Chromium 153.
`templates/amberdawn32/editor.html` keeps the original sunlit portrait plate and
rebuilds its centered lemon-yellow script pair, circular three-font seal, and
restrained footer as individually fitted layers. `templates/skinbadge32/editor.html`
recreates the lavender and brown overlapping seals, clipped brush-letter
pattern, curved skincare copy, eight perimeter stars, and broad painted
underline over the original beauty portrait. Same-face source/Skia/HTML
comparisons and desktop/mobile editor captures are saved under
`benchmarks/amberdawn32/output/` and `benchmarks/skinbadge32/output/`.
`templates/latestlook32/editor.html` keeps the original red-jacket photo, fits
all three editorial lines independently, and gives the two footer captions
their own stacked label blocks around the source rule.
`templates/gelatocards32/editor.html` clips the supplied pink and cobalt repeat
art into offset rounded cards, then layers separate shadows, labels, editable
headlines, and a compact footer above the original ice-cream photograph. Their
source/Skia/HTML sheets and responsive editor captures live under the matching
benchmark output directories. Refresh them with
`node font-factory/support-html/benchmarks/latestlook32/capture.mjs` and
`node font-factory/support-html/benchmarks/gelatocards32/capture.mjs` after
updating the saved renderer outputs. On Chromium 153, the same-face 2400 × 1600
lookbook export is 3,881,354 bytes in HTML/CSS and 4,338,455 bytes in Skia; its
line edit reached paint in 19.9 ms. The gelato export is 2,242,368 bytes in
HTML/CSS and 2,579,414 bytes in Skia; its headline edit reached paint in
27.3 ms. The amber HTML and Skia exports are 3,836,217 and 4,376,993 bytes; its
headline edit reached paint in 26.9 ms. The skincare HTML and Skia exports are
1,452,264 and 1,717,042 bytes; its word edit reached paint in 40.3 ms.
`templates/meditation32/editor.html` layers the source's bubble art, soft pastel
color pools, woven paper lines, framed shore photograph, pink `DISC 30%` burst,
and original date and web-address footer. `templates/strongweak32/editor.html`
rebuilds the orange, scalloped pink, and cobalt frame, with individually fitted
specimen words, registration shadows, and the reference's `YOUNGTYPE STUDIO`,
`HAND DRAWN`, `STROKE / REGULAR / OUTLINE`, and `ORGANIC HAND DRAWN` labels.
Their source/Skia/HTML comparisons and responsive editor captures are saved
under the matching benchmark folders. Refresh them with
`node font-factory/support-html/benchmarks/meditation32/capture.mjs` and
`node font-factory/support-html/benchmarks/strongweak32/capture.mjs`. On
Chromium 153, the same-face meditation export is 3,026,432 bytes in HTML/CSS
and 1,929,952 bytes in Skia; its headline edit reached paint in 23.7 ms. The
type-study export is 495,170 bytes in HTML/CSS and 495,281 bytes in Skia; its
headline edit reached paint in 39.7 ms.
`templates/funkyfashion32/editor.html` layers the clipped orange-backed portrait,
editable original headline and copy, vector smiley and lightning stickers,
dotted annotation, and offset signature. `templates/typewall32/editor.html`
turns the reference's tilted yellow specimen into a full-bleed repeating field;
its controls adjust eight independent lines, tilt, scale, row spacing, and
horizontal stagger so narrower typefaces still cover the page. Three-way
comparisons and desktop/mobile editor captures are in
`benchmarks/funkyfashion32/output/` and `benchmarks/typewall32/output/`. Refresh
them with `node font-factory/support-html/benchmarks/funkyfashion32/capture.mjs`
and `node font-factory/support-html/benchmarks/typewall32/capture.mjs`. On
Chromium 153, the same-face fashion export is 1,559,060 bytes in HTML/CSS and
1,957,077 bytes in Skia; its headline edit reached paint in 25.3 ms. The
type-wall export is 632,259 bytes in HTML/CSS and 337,352 bytes in Skia; its
row edit reached paint in 42.0 ms.
`templates/manualbrew32/editor.html` restores the source's `MANUAL`/`BREW`
copy, six-color and four-color letter sequences, charcoal ground, and rounded
studio credit. Its live controls include per-word fitting, line spacing,
tracking, palette, and adjustable letter height. `templates/pastpresent32/editor.html`
layers three editable sign labels over the reference-derived hand-sign plate,
with a CSS gingham field and rounded source credit. Lilita One provides a
source-matched preview face for these comparisons; both editors still support
uploading any live display font. Their source/Skia/HTML comparisons and
responsive editor captures are in `benchmarks/manualbrew32/output/` and
`benchmarks/pastpresent32/output/`. Refresh them with
`node font-factory/support-html/benchmarks/manualbrew32/capture.mjs` and
`node font-factory/support-html/benchmarks/pastpresent32/capture.mjs`. On
Chromium 153, the 2400 × 1600 manual-brew export is 116,960 bytes in HTML/CSS
and 96,847 bytes in Skia; a word edit reached paint in 26.7 ms. The timeline
export is 1,138,160 bytes in HTML/CSS and 1,451,590 bytes in Skia; a sign edit
reached paint in 23.9 ms.
The `crest32` source/Skia/HTML sheet is at
`benchmarks/crest32/output/comparison.png`; the lower text path and center fit
are separated so script descenders no longer add a ghost line beneath the hero.

## Current benchmark

On Chromium 153.0.8010.36 at a 2400 × 1600 export size:

- First page load with local fonts: about 956 ms.
- CSS edit to next painted frame: about 13–33 ms for angle, copy, or color.
- Uploading and applying a local TTF: about 73 ms.
- Full size HTML screenshot: about 1.9 seconds.
- Warm Skia draw plus PNG optimize/write: about 1.7–2.0 seconds.
- HTML PNGs: about 3.20–3.31 MB; Skia PNG: about 158 KB.

These timings measure two different steps: an interactive browser adjustment
does not encode a PNG, while the Skia figure includes rendering and saving.
Full-size export time is similar; the faster part is changing layout and seeing
it immediately. PNG size is a real tradeoff, largely due to the full-frame
grain layer, and needs attention before production rollout.

The `hand32` sample in `benchmarks/hand32/output/comparison.png` uses the same
local display font and copy for Skia and HTML/CSS. Both exports are 2400 × 1600;
the HTML/CSS PNG is 181,548 bytes and the Skia PNG is 213,653 bytes. The browser
version follows the source's reference colors and type-box positions, keeps the
supplied hand art as a recolorable mask, and lets the caption use its own ink.
The source display color pair measures 1.59:1 contrast, so the renderer allows
that exact source palette down to 1.5:1 for this poster only; the caption is
10.66:1 and the editor controls retain the normal contrast checks. Run
`node font-factory/support-html/benchmarks/hand32/capture.mjs` to refresh the
comparison and desktop/mobile editor previews after updating the saved Skia
and HTML exports.

The `zebra32` sample in `benchmarks/zebra32/output/comparison.png` uses the
same Noto Serif Display Black face and original copy in both renderers. Both
exports are 2400 × 1600; the HTML/CSS PNG is 2,593,021 bytes and the Skia PNG
is 3,229,780 bytes. The CSS version matches the source photo's arch scale and
placement, carries the poem's tighter line rhythm, and restores the curved
underline while leaving texture, photography, and copy as editable layers.

The `freakscene32` source/Skia/HTML sheet is at
`benchmarks/freakscene32/output/comparison.png`. It compares the current Skia
copy with the source wording restored in HTML/CSS; the selected test face is
the same in both renders. The 2400 × 1600 HTML/CSS file is 2,570,316 bytes;
the Skia file is 206,613 bytes. The browser paper grain adds a measurable PNG
size cost in this print-heavy design.

## Renderer direction

Keep Python as the font and job orchestrator: inspect font metadata, decide
class and eligible templates, select themes, and prepare content/material
references. Represent each support composition as HTML/CSS with SVG for
ornaments and local image assets for photography or illustrations. Use
headless Chromium for layout preview and final 2400 × 1600 export. Preserve a
shared fit, glyph-coverage, contrast, and bounds report before replacing any
production output.

The active templates also use the broader pin/studio path in
bin/pin-studio/pin_studio.py; it creates Pinterest artwork and factual
specimens and uses Skia-backed font outlines for measurement and fit checks.
Migrating the 61 supports alone therefore does not remove Skia from the
repository.

See AUDIT.md for the catalogue, architecture, visual review, and migration
checklist.

`templates/herbalproduct32/editor.html` restores T26223_05 as a framed green coffee carton label, with the original `HERBALS` title, botanical crest, batch oval, twelve-ray `NEW` badge, outlined coffee description, and three distinct roast-detail columns. `templates/colosseum32/editor.html` restores T26074_01 as three centered, independently fitted rows on softly grained paper, including the original `gröngöling` umlauts and the Nektar / More Etc footer. Their source/Skia/HTML comparisons and desktop/mobile captures are under `benchmarks/herbalproduct32/output/` and `benchmarks/colosseum32/output/`. Refresh them with `node font-factory/support-html/benchmarks/herbalproduct32/capture.mjs` and `node font-factory/support-html/benchmarks/colosseum32/capture.mjs`. Both use the same Lilita One display face in the browser/Skia comparison; HTML text edits reached paint in 44 ms and 40.9 ms, respectively. At 2400 × 1600, their HTML/Skia PNGs are 730,920/176,579 bytes and 3,358,245/283,274 bytes. Desktop and mobile layout reports show no out-of-bounds elements. The Herbal Product HTML path also preserves every requested batch, date, process, and weight character; unsupported display-font glyphs are reported while Chromium draws a readable fallback. Product-detail copy uses two-row textareas so its printed line breaks remain editable.

`templates/contour32/editor.html` rebuilds T30930_03 around its thin orange frame, seven cyan arrows, three cropped orange ribbons, compact `9 LIGATURES` caption, and original `ADCAQO` / `STSZTTZS` rows. The editor keeps the source palette and exposes glyph scale, width, tracking, and color controls while preserving the uploaded font's letterforms.

## Blackletter reference template set

The 18 Esviga blackletter recreations are each editable in `templates/<id>/editor.html` and `design.js`. Their individual 2400 × 1600 exports, per-image layout reports, one-column gallery, and render manifest are in `benchmarks/blackletter-reference-templates-2026-10-15/`. The gallery links to each separate PNG; it does not combine them into a collage. Each template maps directly to one source in `support-references/blackletter-references/`.

## October 2026 source remakes

Fourteen additional reference-led editors use the supplied T33329, T32243,
T15503, T16576 and T36099 images. Each page keeps its downloaded reference
beside the live artwork. Twelve generated text-free plates are stored under
`support-references/materials/user-batch-2026-10-20/`; T33329_00 and T16576_09
use their original flat green and pink fields as CSS, so no cleanup plate is
needed. The originals, source URLs, generated-material mapping, and SHA-256
checksums are documented in
`support-references/originals/user-batch-2026-10-20/SOURCES.md`.

The editors are `palmello32`, `quietattempt32`, `hushglow32`,
`italianhorror32`, `dreamwarriors32`, `nesting32`, `erotica32`,
`conspiracytheory32`, `overglow32`, `pinkvice32`, `attitude32`,
`indieground32`, `caramelsundae32` and `sweettreat32`. Their layouts use
reference-positioned lettering boxes, real uploaded font metrics, and a 10% ×
24% fitting inset. Text boxes clip at their reserved edges and report a warning
when the font and copy cannot fit. These fourteen HTML-only templates are
available to `--support-renderer html` and `hybrid`; the default Skia renderer
continues to sample its own native layouts.
