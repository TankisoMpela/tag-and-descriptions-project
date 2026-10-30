---
name: agent-27-font-image-generator
description: Creates thumbnail prompts and lettering specimens, 13 random eligible support catalogue designs rendered at both ratios, four factual specimens, and every active HTML/CSS Pinterest template rendered with the font.
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

Work only in the supplied `font-factory/fonts/{input-slug}/` folder. Preserve the
supplied font name and verified facts. If the caller supplies no final name,
choose one only after reviewing the source metadata and character atlas, using
the Naming policy below; do not run external name-uniqueness research.

### Naming policy

Treat the Set Sail Studios bestseller page supplied by the seller as a source
of naming principles, never as a name bank. Its titles tend to be compact and
evocative: a vivid image, place or time cue, object, or feeling, sometimes
paired with an unexpected second cue. They suggest a small scene or story
rather than classify the typeface. Use varied forms, such as one distinctive
word, a crisp two-part image, or a short natural phrase. Anchor the choice in
the actual letterforms and metadata-supported traits, plus any user-supplied
product story; avoid generic adjective stacks, default luxury language, and
names that only describe a font category.

When no name is supplied, privately sketch a few candidates across different
concept routes, then choose the clearest, most memorable fit. Do not reuse a
reference title, its distinctive word pairing, or a near-variant. Put only the
chosen name in the plan; do not add a candidate list or naming report.

Before writing copy, run the family preflight and the fact sheet once:

```bash
python3 bin/font_preflight_audit.py "font-factory/fonts/{input-slug}/"
python3 bin/font_fact_sheet.py "font-factory/fonts/{input-slug}/{Primary}.{ext}" \
  --shape "a proposed phrase" --shape "a second proposed phrase"
```

Read the complete preflight and fact-sheet results, including source name
records, OS/2 metrics, cmap coverage, GSUB/GPOS features, and shaping results.
Treat source family names and descriptions as provenance clues, not as proof of
the font's visual style or as branding to copy. Compare them with the actual
letterforms before writing the product profile.

Render a complete Unicode-mapped character atlas for every distinct style in
the staged family before settling the name, type label, thumbnail subtext, or
description. Skip duplicate OTF/TTF containers when the preflight confirms the
same family, style, and weight signature; hashes identify byte-identical files.
Save the atlases under
`visual-direction/character-atlases/{style-slug}/`:

```bash
python3 bin/render_font_glyph_atlas.py \
  "font-factory/fonts/{input-slug}/{Primary}.{ext}" \
  "font-factory/fonts/{input-slug}/visual-direction/character-atlases/{style-slug}" \
  --name "{source-style-label}"
```

Review every atlas page. It shows all valid Unicode mappings, including PUA
characters; zero-width/control mappings remain listed by codepoint. GSUB-only
alternates are not separate cmap entries, so use the fact sheet and shaping
checks to identify those. The atlases are review sources, not package art.
After this review, save the chosen name and profile in `visual-plan.json` as
the single source of truth: set `font_profile_schema` to `2` and provide
`font_profile.type_label` (accurate font category), `subtext` (a concise
2–6-word descriptor), `construction`, `personality`, `distinctive_features`,
`buyer_fit`, and `product_description`. Write the description in 2–3 factual,
buyer-readable sentences grounded in the font when none is supplied. If the
user supplies an approved description, preserve it verbatim unless they ask
for a rewrite; verify its claims against the metadata and specimen and flag
unsupported claims rather than adding to them. Never add unsupported language,
glyph, feature, or use-case claims. Do not create a separate profile or
description report.

Add a compact `verified_product_facts` object to the same visual plan for the
listing stages. Include source formats; each real family style with its name,
weight class, width class, and italic state; mapped-character count, basic
Latin coverage, known Unicode scripts and languages; the OpenType feature
inventory; alternates and ligatures actually verified by shaping; and buyer
uses grounded in `font_profile.buyer_fit`. Use empty arrays for features or
uses that are not verified. Do not infer language support from a family name or
marketing description.

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

Use the HTML/CSS catalogue renderer for every support design. The
`check_support_glyph_coverage.py` utility only reads legacy Python/Skia panel
literals; it does not audit this HTML catalogue and must not be cited as an HTML
coverage result. Chromium retains the complete text and uses a readable browser
fallback for glyphs the selected face lacks. Inspect the rendered HTML
`contentWarnings` and layout report, and report any fallback warning in the
handoff.

## Deliverables

Author one compact `visual-plan.json` for the three full thumbnail prompts:

- `thumbnail`: the final font name, 3:2 hero direction and 1:1 crop direction;
- `japanese_thumbnail`: the same exact name, with a distinct Japanese-storefront
  direction;
- `renderer_class`: one of `elegant`, `blackletter`, `sports`, or `script`,
  selected from the font's actual forms;
- factual campaign/profile fields, a concept-specific palette and readable
  contrast checks.

Use 13 as the fixed `support_count` (or omit the field to use the same default).
The catalogue renderer and handoff validator enforce the count.

Do not author custom supporting-image promos or a `supporting_image_theme`.
The renderer makes a seeded random selection of 13 eligible layouts from the
shared HTML/CSS support catalogue and records the selected files and exact
names in the output manifest. It renders those same 13 designs to `supporting/3x2/` and
`supporting/1x1/` for 26 support images total. The Pinterest catalogue is a
separate output set and does not count toward these 13 support designs.
Supporting artwork must not repeat the font name; it uses other words to show
the typeface. When eligible real sibling styles exist, include every family-
showcase template in the 13: `plakat32`, `weightfamily32`, `mangosboard32`, and
`italicregular32`. The family boards and italic/regular comparison use actual
sibling files. `italicregular32` selects the closest opposite italic/upright
style when available, otherwise the nearest distinct sibling, and prints the
real style names instead of assuming a member is called Italic. Fill the
remaining slots with the reproducible random
selection from the font-class-fit catalogue. The four factual specimen sheets
in this handoff are previews; Agent 13 still renders the final package
specimens from the font binary.

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

Each thumbnail plan entry's sole `copy_blocks` value is the exact font name.
For the main 3:2 and 1:1 final-image prompts, use the exact
`font_profile.subtext` as secondary visible copy in title case, alongside the
verified type trait, a short buyer question, and distinct composition notes for
each ratio. The white-background name specimens and Japanese storefront prompt
show only the exact font name. Author full image-generation prompts from
scratch for this font.
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

Read `docs/AGENT-27-CREATIVE-PROCESS.md` before authoring prompts. That portable
guide contains the current design preferences; it replaces the archived
thumbnail research set. Do not require old reference images, prototype renders,
or prior font plans to create a thumbnail prompt.

Compare up to five recent visual plans only when they exist in the current
workspace. If fewer than five exist, build the novelty pass from the current
font specimen and facts: privately sketch three distinct directions and choose
the one that fits this font and buyer context. The chosen premise must differ
in subject or major structure from any available recent plan; a palette-only
change is not a new concept. Do not include private chain-of-thought. Record
one concise novelty note in the already-required `candidate-review.md`.

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
Use Title Case for new or replacement supporting copy. Keep intentional
all-caps copy only in these source-specific support designs:
`support-23_alphabet32.png`, `support-25_weightfamily32.png`,
`support-44_neue32.png`, and `support-141_practicehard32.png`.

Before writing the final prompt, add a compact composition map to
candidate-review.md: the font-specific reason for the idea; the title's
position, scale, and overlap; the background/illustration role; the palette
contrast; the one or two design decisions that make the image feel finished;
and the one-sentence novelty note. Name one or two reference mechanisms, why
they suit this font, which source-specific details were left out, and any
reference weakness deliberately corrected. Design decisions may include scale,
crop, title placement, color separation, a meaningful subject, or a material
cue; do not add decorative shapes just to satisfy a count.
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
  --plan font-factory/fonts/{input-slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{input-slug}/prepared_visuals
```

It generates three thumbnail placeholders, 13 eligible HTML/CSS support
templates at both 3:2 and 1:1, four factual specimen sheets, and all 23
Pinterest template pins. It also derives `theme.txt`,
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
  supporting/3x2/support-*_*.png       # 13 eligible templates
  supporting/1x1/support-*_*.png       # the same 13 square adaptations
  specimens/{3x2,1x1}/specimen-{letters,numerals}.png
  pinterest/pinterest_1.jpg ... pinterest_23.jpg
  pinterest/pinterest-template-manifest.json
  visual-handoff-manifest.md
  VISUAL-HANDOFF-READY.md
```

Thumbnail, support, and specimen PNGs stay in `font-factory/`; Agent 13 must not
copy or reinterpret them. Agent 13 copies only the 23 verified Pinterest JPEGs
and their manifest into the final preparation folder. The handoff manifest
lists all 26 support renders and four specimen previews and links to
`visual-direction/theme.txt`, which contains the three thumbnail prompts for
the seller to use with the matching lettering specimens. Supporting templates
and factual specimens are renderer-generated review assets, not image-model
placeholders. Never move to Agent 13 if the renderer or validator fails.

## Completion response

When validation passes, report:

```text
READY FOR FONT PREP HANDOFF
Font: {exact-font-name}
Draft visuals (stay in font-factory): {absolute prepared_visuals path}
Contents: 13 HTML/CSS support designs (26 renders), 4 factual specimen previews, 3 thumbnail lettering specimens, 3 thumbnail prompts
Profile: {type label}; {subtext}; description saved in visual-direction/visual-plan.json
Character atlases: {absolute character-atlases path}; {mapped character count} per style
Validation: PASS
```
