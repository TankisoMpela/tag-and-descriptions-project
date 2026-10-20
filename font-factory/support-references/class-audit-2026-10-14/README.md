# Supporting-template catalogue and style audit

## Current review set

The refreshed catalogue is [here](individual-comparisons/README.md): one standalone reference/render image per link, no collages. It covers all 61 active templates across the style-eligible audit groups; 334 renders passed with zero layout findings. References intentionally remain blank for templates with no supplied original.

Unindexed earlier JPEGs are preserved under [historical individual comparisons](historical-individual-comparisons/README.md); withdrawn and ineligible images are not mixed into the current folders.

> Historical snapshot: this report predates the blackletter first-pass review
> and eight global template drops. Its pool counts describe the previous
> catalogue. See [the review and current decisions](blackletter-first-pass.md).

This historical audit renders 69 supporting-image templates against six real
font styles. Where a source exists it is shown on the left, with the Skia render
on the right; templates without a supplied source have a blank left panel. Each contact sheet holds up to 18 comparisons, grouped by
catalogue order; the cards show their stable slot numbers. Withdrawn
`bondibeach32` (slot 43) is omitted and remains a numbering gap. The template
renders were made at 1200 × 800 px; the renderer scales these layouts to the
2400 × 1600 px delivery surface.

For the compact catalogue alone, see the [69-template overview sheet](../previews/template-preview-catalogue.png).
The full-resolution layout/error and palette measurements are in [audit.json](audit.json).

## Paired reference and render sheets

| Font style | Representative font | Pages |
|---|---|---|
| Blackletter | Braewick Regular | [1–18](blackletter-page-01-of-04.jpg) · [19–36](blackletter-page-02-of-04.jpg) · [37–54](blackletter-page-03-of-04.jpg) · [55–70](blackletter-page-04-of-04.jpg) |
| Handwritten / elegant cursive | Gladista Script | [1–18](handwritten-page-01-of-04.jpg) · [19–36](handwritten-page-02-of-04.jpg) · [37–54](handwritten-page-03-of-04.jpg) · [55–70](handwritten-page-04-of-04.jpg) |
| Tech / sports | Circuit Sprint | [1–18](tech-sports-page-01-of-04.jpg) · [19–36](tech-sports-page-02-of-04.jpg) · [37–54](tech-sports-page-03-of-04.jpg) · [55–70](tech-sports-page-04-of-04.jpg) |
| Brush | Kuro Ripper | [1–18](brush-page-01-of-04.jpg) · [19–36](brush-page-02-of-04.jpg) · [37–54](brush-page-03-of-04.jpg) · [55–70](brush-page-04-of-04.jpg) |
| Pixel | AOT Lost Contact | [1–18](pixel-page-01-of-04.jpg) · [19–36](pixel-page-02-of-04.jpg) · [37–54](pixel-page-03-of-04.jpg) · [55–70](pixel-page-04-of-04.jpg) |
| Display | Blazher | [1–18](display-page-01-of-04.jpg) · [19–36](display-page-02-of-04.jpg) · [37–54](display-page-03-of-04.jpg) · [55–70](display-page-04-of-04.jpg) |

## Style-fit and eligible-pool assessment

This is a visual review, not an automatic font classifier. “Strong” means the
template’s composition, voice, and subject reinforce the tested style;
“conditional” means it can work with the right copy, palette, or font
personality; “exclude” means a clear style/context mismatch or a fit/glyph issue.
Conditional pairs remain eligible. The hard exclusions are now enforced by the
renderer’s class/family-aware support filter.

| Font style | Strong | Conditional | Excluded | Eligible after hard exclusions and real-family gates | Strong-only runway |
|---|---:|---:|---:|---:|---|
| Blackletter | 8 | 44 | 17 | 52 | Low — fewer than 14 strong choices |
| Handwritten / cursive | 26 | 34 | 9 | 58 | Healthy |
| Tech / sports | 12 | 36 | 21 | 48 | Low — fewer than 14 strong choices |
| Brush | 17 | 49 | 3 | 63 | Healthy |
| Pixel | 13 | 42 | 14 | 55 | Low — fewer than 14 strong choices |
| Display | 62 | 2 | 5 | 61 | Very healthy |

The eligible-pool counts include Strong and Conditional templates after hard
exclusions, then apply real-style requirements: `boots32`, `weightfamily32`, and
`mangosboard32` need at least two styles from the same family. Test faces had 2
blackletter, 1 handwritten, 3 tech/sports, 1 brush, 2 pixel, and 1 display
style(s). A strong-only runway below 14 means fewer than two strong alternatives
per 7-image selection; by that measure blackletter, tech/sports, and pixel are
low-supply classes. Their total pools still support seven selections. Circuit
Sprint is detected as `brush` despite being used here to test its geometric
tech/sports look; the gate therefore resolves the audited group from both
renderer class and detected family.

The Strong sets are listed below. For each class, the Conditional set is every
active template not in its Strong or hard-exclusion set; this partitions all
414 class/template pairings without repeating the whole catalogue six times.

- Blackletter: `crest32`, `mountain32`, `zebra32`, `soldier32`, `mirror32`,
  `brutal32`, `brutalpack32`, `ravencover32`.
- Handwritten / cursive: `duo32`, `sticker32`, `neon32`, `quote32`, `echo32`,
  `hand32`, `ovalword32`, `stardust32`, `cliffpostcard32`, `kindersea32`,
  `messageframe32`, `voguecover32`, `confident32`, `storyteller32`,
  `focusposter32`, `blossom32`, `amberdawn32`, `latestlook32`, `gelatocards32`,
  `meditation32`, `queens32`, `lemonade32`, `manualbrew32`, `pastpresent32`,
  `herbalproduct32`, `roadrunner32`.
- Tech / sports: `line32`, `contour32`, `plakat32`, `mangos32`, `alphabet32`,
  `electromagnetic32`, `demolition32`, `yearposter32`, `stadiumposter32`,
  `signalclock32`, `glyphsheet32`, `freakscene32`.
- Brush: `line32`, `sticker32`, `neon32`, `quote32`, `echo32`, `hand32`,
  `plakatart32`, `birvase32`, `stardust32`, `voguecover32`, `latestlook32`,
  `funkyfashion32`, `dreamchalk32`, `queens32`, `manualbrew32`, `freakscene32`,
  `roadrunner32`.
- Pixel: `line32`, `feature32`, `contour32`, `plakat32`, `alphabet32`,
  `kindersea32`, `sunsetpromise32`, `pixelquote32`, `electromagnetic32`,
  `yearposter32`, `stadiumposter32`, `signalclock32`, `glyphsheet32`.
- Display: `line32`, `duo32`, `feature32`, `sticker32`, `neon32`, `quote32`,
  `crest32`, `echo32`, `contour32`, `mountain32`, `hand32`, `zebra32`,
  `soldier32`, `mirror32`, `brutal32`, `brutalpack32`, `rio32`, `boots32`,
  `plakat32`, `plakatart32`, `alphabet32`, `birvase32`, `ovalword32`,
  `stardust32`, `cliffpostcard32`, `kindersea32`, `messageframe32`,
  `contactlist32`, `sunsetpromise32`, `phonegarden32`, `pixelquote32`,
  `ravencover32`, `voguecover32`, `confident32`, `storyteller32`,
  `focusposter32`, `wideclaim32`, `blossom32`, `neue32`, `electromagnetic32`,
  `demolition32`, `yearposter32`, `stadiumposter32`, `signalclock32`,
  `amberdawn32`, `latestlook32`, `gelatocards32`, `meditation32`,
  `strongweak32`, `funkyfashion32`, `dreamchalk32`, `lovecard32`, `queens32`,
  `lemonade32`, `sunkiss32`, `typewall32`, `manualbrew32`, `pastpresent32`,
  `herbalproduct32`, `colosseum32`, `freakscene32`, `roadrunner32`.

Hard exclusions by class (objective fit failures and clear style/context mismatches):

- Blackletter: `duo32`, `card32`, `feature32`, `sticker32`, `neon32`, `quote32`,
  `echo32`, `hand32`, `rio32`, `boots32`, `mangos32`, `ovalword32`,
  `kindersea32`, `messageframe32`, `sunsetpromise32`, `pixelquote32`,
  `greetingsgrid32`.
- Handwritten / cursive: `card32`, `brutal32`, `boots32`, `plakatart32`,
  `contactlist32`, `sunsetpromise32`, `phonegarden32`, `pixelquote32`,
  `greetingsgrid32`.
- Tech / sports: `duo32`, `card32`, `feature32`, `sticker32`, `quote32`, `echo32`,
  `rio32`, `boots32`, `ovalword32`, `cliffpostcard32`, `kindersea32`,
  `messageframe32`, `contactlist32`, `sunsetpromise32`, `phonegarden32`,
  `pixelquote32`, `voguecover32`, `confident32`, `storyteller32`, `blossom32`,
  `greetingsgrid32`.
- Brush: `card32`, `pixelquote32`, `greetingsgrid32`.
- Pixel: `duo32`, `card32`, `sticker32`, `quote32`, `ovalword32`,
  `cliffpostcard32`, `voguecover32`, `confident32`, `storyteller32`,
  `focusposter32`, `blossom32`, `amberdawn32`, `meditation32`,
  `greetingsgrid32`.
- Display: `card32`, `mangos32`, `skinbadge32`, `glyphsheet32`,
  `greetingsgrid32`.

## Objective preflight findings

All six classes produced 69/69 render records, with no render exceptions. The
six spacing fixes (`card32`, `boots32`, `sunsetpromise32`, `contactlist32`,
`phonegarden32`, and `pixelquote32`) now pass with zero layout findings across
all 36 focused 2400 × 1600 delivery-resolution template/style renders.

Remaining preflight findings are separate from those repairs:

- `mangos32`: the display test face cannot fit `BOTANICAL` in its fixed title
  slot at the configured minimum size. This template is excluded for display.
- `skinbadge32`: five fixed repeating-text slots wrap with the display test
  face; this template is also excluded for display.
- `weightfamily32` and `mangosboard32` report the expected two-style gate for
  the single-style handwritten, brush, and display test faces. They are not
  layout failures and are available for real multi-style families.

The palette probe found only 12/69 templates materially change when the display
sample is switched between two palettes (`mean RGB delta > 1`):
`line32`, `duo32`, `card32`, `feature32`, `sticker32`, `neon32`, `quote32`,
`crest32`, `echo32`, `contour32`, `hand32`, and `blossom32`. The other 57 are
effectively palette-locked in this test. This is a useful next improvement, but
should be handled selectively: image-led references often depend on their
original color treatment.

## Suggested next work

1. The spacing fixes are complete. If those concepts should work with display
   faces in future, adapt `mangos32` and `skinbadge32` for longer/wider glyphs;
   otherwise keep their current display exclusions.
2. Improve strong-choice variety where the audit shows low supply: blackletter
   (8), tech/sports (12), and pixel (13). Their full eligible pools still support
   seven outputs, but the weaker alternatives make selection less robust.
3. Add alternate palettes only to templates whose reference art can tolerate
   recoloring; preserve locked photographic/illustration treatments.
4. Keep conditional matches in the pool; expand the hard-exclusion gate only
   when a new render/reference review identifies a clear mismatch or measurable
   failure.

`blossom32` is shown in its restored straight red-panel composition beside the
portrait. `bondibeach32` remains withdrawn and is not selectable; its stable
number is retained as a gap.
