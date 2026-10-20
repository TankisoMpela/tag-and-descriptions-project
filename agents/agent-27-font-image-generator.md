---
name: agent-27-font-image-generator
description: Creates white-background font-name specimens, bespoke full-image prompts, and a validated handoff containing seven HTML/CSS supporting layouts at both ratios, four factual specimens, and all active HTML/CSS Pinterest templates rendered with the font.
user-invocable: true
---

# Font Image Generator — current handoff

This spec replaces the retired eight-custom-promo workflow. The goal is to
deliver reference-led supporting images from the shared HTML/CSS catalogue.
Each selected 3:2 layout also has a square version built from the same code and
materials, with its elements refit for a square artboard instead of stretching
or cropping the landscape image. The seller reviews the completed set and
requests adjustments afterward.

## Scope

Work only in the supplied `font-factory/fonts/{slug}/` folder. Preserve the
supplied font name and verified facts. If the caller supplies no final name,
choose one grounded in the description without external uniqueness research.

Before writing copy, run the family preflight and the fact sheet once:

```bash
python3 bin/font_preflight_audit.py "font-factory/fonts/{slug}/"
python3 bin/font_fact_sheet.py "font-factory/fonts/{slug}/{Primary}.otf" \
  --shape "a proposed phrase" --shape "a second proposed phrase"
```

Use OTF/TTF only as source fonts; never modify, repair, subset, or re-encode
them. Note material family, shaping, glyph-coverage, or kerning limitations in
the existing plan or handoff notes. Do not create a standalone report.

Read `font-factory/support-references/TEMPLATE-GUIDE.md` before the render.
That guide is the complete caption/alt-text and theme-flexibility reference for
all active supporting templates. Use the one-to-one square adaptation in
`font-factory/support-html/` for the matching layout. Keep its reference-locked copy and imagery
intact. Adapt only the fields the guide marks flexible, and never claim a style,
weight, axis, glyph, or use case the font does not have.

Use the HTML/CSS renderer for both ratios. Its editor pages have 3:2 and 1:1
controls; square layouts must preserve each design's subject, palette, image
assets, and hierarchy while making a distinct square composition. Do not
white-pad or crop a 3:2 support render to make its square twin.

Run `python3 bin/check_support_glyph_coverage.py "font-factory/fonts/{slug}/{Primary}.otf"`
before the support render: fixed specimen strings are glyph-stripped silently, so a
tile can ship nearly empty with a clean exit and a normal size in `--json`. An `EMPTY`
line is a finding to report in the handoff notes, not something to work around, and
`--json` slot sizes never prove what actually rendered.

## Deliverables

Author one compact `visual-plan.json` for the three full thumbnail prompts:

- `thumbnail`: the final font name, 3:2 hero direction and 1:1 crop direction;
- `japanese_thumbnail`: the same exact name, with a distinct Japanese-storefront
  direction;
- `renderer_class`: one of `elegant`, `blackletter`, `sports`, or `script`,
  selected from the font's actual forms;
- factual campaign/profile fields, a concept-specific palette and readable
  contrast checks.

Do not author custom supporting-image promos or a `supporting_image_theme`.
The renderer reproducibly selects seven eligible layouts from the shared
HTML/CSS catalogue and records the selected files and exact names in the output
manifest. It renders those same seven designs to `supporting/3x2/` and
`supporting/1x1/`.
Supporting artwork must not repeat the font name; it uses other words to show
the typeface. If the source folder has at least two distinct styles in one real
family, both family-proof layouts are guaranteed in the seven and use the
actual sibling files. The four factual specimen sheets in this handoff are
previews; Agent 13 still renders the final package specimens from the font
binary.

Render every active Pinterest layout from `font-factory/pin-html/` with the
primary font and exact product name into `prepared_visuals/pinterest/` using
`node font-factory/pin-html/render_gallery.mjs --mode pins`. The active set has
23 individual templates; `green_starburst` and `phrase` are retired and must
not appear in this production set. Keep each pin as its own 1000×1500 JPEG at
or below 200 KB. Include `pinterest-template-manifest.json` with the exact
template/index mapping, font hash, byte sizes, and image hashes. Use the actual
font in every display specimen; replace demo family names and unsupported
glyph/feature-count claims with the supplied font name and neutral copy. These
23 pins are later copied unchanged by Agent 13. Agent 30 appends ten composites
after them, and the Pinterest preparer uploads the complete set and records all
public links.

Agent 27 must keep producing the clean, white-background font-name specimens.
Those images are raw lettering material for the later image-generation step;
they are not intended to look like finished thumbnails. Render the exact final
font name with the actual font file, on white, without decoration or added copy.

Each thumbnail plan entry needs one copy block containing the exact font name,
one concise style descriptor in title case grounded in the specimen, the
verified type trait, a short buyer question, and distinct composition notes for
each ratio. Author full image-generation prompts from scratch for this font.
There is no old thumbnail reference to find, inspect, reimagine, or preserve.
The white-background font specimen is the sole lettering reference; the font
description and verified facts ground the concept. Use only the approved font
name and style descriptor as visible copy. Keep the name dominant and readable,
but choose its placement and scale from the composition instead of forcing a
centred lockup or fixed percentage.

Write three complete prompts into the plan and derived `theme.txt`:

- `thumbnail.image_prompt`: the main 3:2 thumbnail;
- `thumbnail.ratio_layouts.1x1.image_prompt`: a separately composed square main
  thumbnail using the same font name;
- `japanese_thumbnail.image_prompt`: a separate square storefront design.

Each prompt must be usable with the matching white-background specimen by itself.
The 3:2 and 1:1 prompts must make different crop and layout decisions. Do not
write a reusable thumbnail-reimagination prompt. Supporting templates need no
per-font prompt or theme file.

### Bespoke thumbnail prompt requirements

Read `font-factory/Style-References/thumbnail-prompt-research-2026-10-20/prompt-findings.md`
and `reference-structure-audit.md` before authoring prompts. Shortlist one or
two relevant references, then open each saved image and read its full individual
caption in `captions.json`; do not rely on the audit summary alone. Record the
specific composition mechanism that applies to this font, and distinguish it
from the reference's subject, palette, copy, and secondary details. Never turn
the caption into a prop checklist or copy the source arrangement.

Run the novelty pass in `prompt-findings.md` before choosing a concept. Compare
the five most recently updated, non-archived font plans in `font-factory/fonts/`
using each 3:2 thumbnail concept and its existing route note; inspect a final
image at small size only when one exists. Do not treat the white specimen
placeholder as a finished thumbnail. If fewer than five plans are available,
use the prototype gallery. Privately sketch three distinct directions, then
select the one that fits the specimen and buyer context while changing at
least three of these from recent work: medium, composition, focal subject/device,
palette family, texture/light, and title placement. Record only one concise
novelty note in the already-required `candidate-review.md`; do not include
private chain-of-thought. Do not default to glossy “premium” product still
lifes, amber shallow-focus lighting, velvet/silk, or perfume-and-flower props.
If a repeated motif is genuinely specific to the font, explain that and change
the other design choices.

Honor the seller's rejected directions recorded in `prompt-findings.md`: do not
reuse the oversized cropped initial with orbit rings, the blue/berry split
descriptor panel, or the arch/portal title frame as a default. The lesson is
not to avoid all geometry; it is to avoid letting generic geometry stand in
for a font-specific idea. Across a batch, change the underlying subject or
visual mechanism as well as the palette. For a flat type-led direction, use
one quiet, purposeful paper/ink/print texture or faint relevant illustration
when it helps the design feel tactile and complete. Keep it specific and
secondary; do not add random flecks or texture stacks.

Also apply the preference calibration in `prompt-findings.md` as signals, not
recipes. The seller welcomes both photography and illustration when the
concept fits and the name remains the focus. Do not default to a warm, hazy
"premium" photograph with a large face or staged object occupying one side and
empty title space on the other. That composition is allowed only when the
subject is earned by this font and the balance feels intentional. Likewise,
do not copy the colors or layout of a liked example; carry forward its
font-specific fit, clear type hierarchy, and strong contrast instead.

Start from the actual white-background font-name specimen. Observe its natural
capitalization, proportions, terminals, stroke contrast, joins, and filled or
outlined construction. State only the features visible in the specimen. Then
write a one-sentence concept thesis that ties one of those features to one
specific subject, environment, material, or graphic action. If the idea could
fit any unrelated font unchanged, make it more specific.

Each complete prompt should stand on its matching specimen alone. Do not impose
a word count. State the exact specimen behavior to preserve, one specific visual
premise, the title's scale and position, the supporting subject or graphic
structure, palette/value contrast, and any focus hierarchy needed at thumbnail
size. For the 3:2 main thumbnail and 1:1 main thumbnail, include the exact font
name plus the same concise style descriptor, set as a secondary but readable
line at small size. Use title case for the descriptor; preserve natural title
case in the name, with all caps only when the font itself is designed that way.
The Japanese-storefront prompt may adapt its descriptor to that composition.
Do not add unapproved claims or extra supporting copy. Use enough detail to make
the layout unmistakable, then stop; do not enumerate caption details as props.

All thumbnail lettering is a flat, front-facing 2D graphic layer. It may
overlap a photograph, person, illustration, or color field, but it stays
independent of background perspective, lighting, shadows, and materials. Never
ask for text written, printed, painted, mounted, embossed, extruded, or
perspective-warped onto a photographed/rendered object, clothing, page, wall,
product, or 3D environment. Background photography and 3D environments remain
available when they serve the concept; the type is always visibly a graphic
overlay.

For type-led work, a large title on an empty field is not enough. Give the
composition at least two deliberate design moves beyond the name and a plain
background, such as large/small type scale, a tight crop, asymmetric balance,
an intentional color division, oversized glyph fragments, or one meaningful
illustration. Do not add unrelated shapes to satisfy this gate. A real scene
can provide the structure, or one relevant subject can frame or counterbalance
the title. Flat work may use one restrained paper, ink, print, or other
font-specific texture, or a faint illustration, so the background does not feel
sterile. Keep useful negative space, but do not default to a blank, clinical
field. Describe the texture or illustration clearly and keep it secondary;
never substitute scattered specks or stacked effects for an actual concept.

Use photography only with a deliberate crop and focus hierarchy. If a model or
person appears, keep the face secondary: crop it out, show the lower face/body,
or place it soft and subdued in the background. The name remains the sharp,
bright first read; do not emphasize eyes, facial beauty or expression. Motion
blur belongs only on secondary moving forms. Use a material/focus treatment
only when it names a real choice, and avoid stacking grain, haze, scratches,
glow, blur and overlays.

The seller's visual constraints are firm: no glitter, sparkles, starbursts,
confetti, floating particles, fake lens flare, ornamental filler, arbitrary
badges, generic AI-style decoration, gratuitous glow, or excessive texture.
Do not fill open areas just because they are empty. Avoid dark-on-dark type and
similar-value colors; inspect contrast across every letter, especially on
photographs. Preserve the name's supplied capitalization; never force all caps.
If the user requests supporting words, use Title Case.

Before writing the final prompt, add a compact composition map to
`candidate-review.md`: the font-specific reason for the idea; the title's
position, scale and overlap; the background/illustration role; the palette
contrast; the one or two design moves that make the image feel finished; and
the one-sentence novelty note.
Name one or two reference mechanisms and state what was deliberately left out.
Before accepting the render, check at full size and at 300×200 that the name
leads, every glyph fits, any face remains secondary, local contrast holds, and
the composition reads as a designed thumbnail rather than a raw name sample.
Reject surface-embedded lettering even when an image model produces it from an
otherwise successful prompt.

The Japanese-storefront thumbnail still shows only the exact supplied name.
Compose it separately for 1:1 and follow the same hierarchy, flat-title,
contrast and restraint rules; a Japanese destination does not call for invented copy or
unsupported glyph claims.

## One-pass render and validation

Create `visual-direction/visual-plan.json` and a short
`visual-direction/candidate-review.md` decision note. Run the handoff command
once:

```bash
python3 bin/generate_font_text_placeholders.py \
  --plan font-factory/fonts/{slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{slug}/prepared_visuals
```

It generates three thumbnail placeholders, seven eligible HTML/CSS supporting
templates at both 3:2 and 1:1, four factual specimen sheets, and all 23 Pinterest
template pins. It also derives `theme.txt`,
`image-notes/`, `art-direction.md`, the manifest and ready marker. Do not hand
edit generated views. If a mechanical validator error occurs, fix that error
and rerun; do not create multiple visual variants or polish a PNG for its own
sake.

The prepared handoff is expected to contain:

```text
prepared_visuals/
  3x2/thumbnail_main.png
  1x1/thumbnail_main.png
  1x1/thumbnail_japanese.png
  supporting/3x2/support-*_*.png       # seven eligible templates
  supporting/1x1/support-*_*.png       # the same seven square adaptations
  specimens/{3x2,1x1}/specimen-{letters,numerals}.png
  pinterest/pinterest_1.jpg ... pinterest_23.jpg
  pinterest/pinterest-template-manifest.json
  visual-handoff-manifest.md
  VISUAL-HANDOFF-READY.md
```

Thumbnail, support, and specimen PNGs stay in `font-factory/`; Agent 13 must not
copy or reinterpret them. Agent 13 copies only the 23 verified Pinterest JPEGs
and their manifest into the final preparation folder.
The three thumbnail placeholder files are white-background font-name specimens
for later image-model use. Supporting templates and factual specimens are
renderer-generated assets, not image-model placeholders. Never move to Agent 13
if the renderer or validator fails.

## Completion response

When validation passes, report:

```text
READY FOR FONT PREP HANDOFF
Font: {exact-font-name}
Draft visuals (stay in font-factory): {absolute prepared_visuals path}
Contents: 7 HTML/CSS supporting templates at 3:2 and 1:1, 4 factual specimen previews, 3 thumbnail placeholders
Validation: PASS
```
