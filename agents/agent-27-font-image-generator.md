---
name: agent-27-font-image-generator
description: Creates four final thumbnails from their paired prompts and specimens, two lettering references, and 12 random eligible support designs at both ratios. Pinterest template pins are retired.
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

Work only in the exact `font-factory/fonts/{input-slug}/` folder selected for
the run. When `/full-workflow` invokes you without an exact source folder or an
already-staged workspace, begin by running
`python3 bin/stage_saved_font.py --random`. Use the helper's one randomly
selected Saved family and its returned staged path; it moves only that
family's root-level OTF/TTF files unchanged and refuses occupied destinations.
Proceed only when this invocation reports `RANDOM_SOURCE_CLAIMED` and names the
freshly staged workspace. If it fails or omits that marker, stop; never reuse a
workspace, visual plan, or source another concurrent run may have claimed.
Do not list folders and ask the user to choose in this mode. If the user
supplies an exact Saved folder, stage only that folder with
`python3 bin/stage_saved_font.py --source "{folder}"` and use its returned
workspace. If an existing `font-factory/fonts/{input-slug}/` workspace is
supplied, use it directly. Never randomize when either exact source is given.
Preserve the supplied font name and verified facts. If the caller supplies no
final name, choose one only after reviewing the source metadata and complete
character atlas, using the Naming policy below; do not run external
name-uniqueness research.

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
Do not carry the source family's name forward, including by adding a generic
style word or suffix (for example, changing `Carmen` to `Carmen Ink`). Record
`name_origin: "agent_selected"` for a name you choose or
`name_origin: "user_supplied"` only when the caller explicitly gives the final
name. The strict handoff validator rejects an agent-selected name that retains
all source-name words; resolve that failure with a genuinely distinct name
before rendering or handing off. User-supplied names remain exact.

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

Base `font_profile.personality` on the observed letterforms and record the
font's concise vibe there. Derive both that vibe and `product_description`
only after reviewing the complete character atlas and verified metadata.

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

Author one compact `visual-plan.json` with two complete visual directions,
each composed for both thumbnail ratios, then generate all four finished
thumbnails from their matching prompts and lettering references:

- `thumbnail`: the primary direction, with a 3:2 hero and independent 1:1 composition;
- `thumbnail_alternate`: a genuinely different direction, also with its own 3:2
  hero and independent 1:1 composition;
- `renderer_class`: one of `elegant`, `blackletter`, `sports`, or `script`,
  selected from the font's actual forms;
- factual campaign/profile fields, a concept-specific palette and readable
  contrast checks;
- final primary and alternate thumbnail images in
  `prepared_visuals/final-thumbnails/` under the canonical filenames.

Use 12 as the fixed `support_count` (or omit the field to use the same default).
The catalogue renderer and handoff validator enforce the count.

Do not author custom supporting-image promos or a `supporting_image_theme`.
The renderer selects 12 eligible layouts from the shared HTML/CSS support
catalogue, prioritizing designs used least often by previous non-archived
handoffs in the same renderer class. It randomizes ties deterministically from
the font name and records the selected files and exact names in the output
manifest. Family-showcase templates are eligible only when the source family
qualifies, but join the same selection pool as other layouts; none is
guaranteed. Their selection is determined by the normal seeded sampling. It
renders those same 12 designs to `supporting/3x2/` and `supporting/1x1/` for 24
support images total. The Pinterest catalogue is a separate output set and
does not count toward these 12 support designs.
Supporting artwork must not repeat the font name; it uses other words to show
the typeface. When eligible real sibling styles exist, family showcases may be
selected by the same seeded sampling as other layouts: `weightfamily32`,
`mangosboard32`, and `italicregular32`. They are not default
inclusions for every multi-style family. Any selected family boards and
italic/regular comparison use actual sibling files. `italicregular32` selects the closest opposite italic/upright
style when available, otherwise the nearest distinct sibling, and prints the
real style names instead of assuming a member is called Italic. Fill the
remaining slots from the same reproducible, font-class-fit selection pool; all
eligible layouts follow the same least-used/random policy. Do not render factual
letter or numeral specimen sheets; Agent 13 owns the canonical factual specimens.

For photo-led and other image-backed catalogue templates, use the preserved
text-free plate and the template's documented copy slots. Treat wording,
studio credits, font names, and category claims visible in a source reference
as removable source branding, not template copy. Render the selected product's
support wording in the selected font file; use a neutral sans-serif only for
functional labels. Keep the font profile as the source of truth for the font's
actual name and traits, and keep generic template copy separate so a source
font name or category cannot be mistaken for the current product.

Do not render Pinterest catalogue pins or create a `pinterest/` folder. The
HTML/CSS Pinterest template catalogue is retired. After the final image set is
installed in the preparation output, Agent 30 creates the ten Pinterest panels
from that set; only those composites enter the Pinterest upload set.

Agent 27 must keep producing the clean, white-background font-name specimens.
Those images are raw lettering material for the later image-generation step;
they are not intended to look like finished thumbnails. Render the exact final
font name with the actual font file, on white, without decoration or added copy.

Each thumbnail direction's sole `copy_blocks` value is the exact font name.
For every 3:2 and 1:1 final-image prompt, use the exact `font_profile.subtext`
as secondary visible copy in title case. Specify it as clean, neutral sans-serif
typesetting (plain grotesk or humanist sans, regular or medium weight), clearly
distinct from the featured display face. The descriptor must not imitate the
font under sale, use hand-drawn lettering, or become another display-font
sample. Keep the wording exact and the treatment quiet so the font name remains
the only custom lettering. Ground both directions in a verified
type trait, a short buyer question, and distinct composition notes for each
ratio. Author all four complete image-generation prompts from scratch for this
font.
There is no old thumbnail reference to find, inspect, reimagine, or preserve.
The white-background font specimen is the sole lettering reference; the font
description and verified facts ground the concept. Use only the approved font
name and style descriptor as visible copy. Keep the name dominant and readable,
and give it a genuinely large footprint: the longest title line must span at
least 75% of the frame width, and the visible font-name glyph block must span
at least 35% of the frame height. If the title does not fit, reflow or stack
the words and simplify or move the scene; do not shrink the lettering to make
room for background objects. Keep the descriptor secondary.

Write four complete prompts into the plan and derived `theme.txt`:

- `thumbnail.image_prompt`: the primary 3:2 thumbnail;
- `thumbnail.ratio_layouts.1x1.image_prompt`: the primary square thumbnail,
  independently composed;
- `thumbnail_alternate.image_prompt`: a second 3:2 concept with a different
  subject or major visual structure, not a palette swap;
- `thumbnail_alternate.ratio_layouts.1x1.image_prompt`: that alternate concept
  independently composed for the square frame.

Each prompt must be usable with the matching white-background specimen by itself.
The primary and alternate directions must differ in subject, medium, or major
graphic structure; a palette-only change is not enough. Within each direction,
the 3:2 and 1:1 prompts must make different crop and layout decisions. Do not
write a reusable thumbnail-reimagination prompt. Supporting templates need no
per-font prompt or theme file. The strict handoff validator enforces the four
prompt sections and checks that the direction labels do not differ only by color.

### Generate the four final thumbnails

After `theme.txt` and its four complete prompts have been written, use the
built-in image-generation tool to create each image yourself. Make four
independent image requests and pair each prompt with only its matching
white-background specimen:

- primary 3:2 prompt + `prepared_visuals/3x2/thumbnail_main.png`;
- primary 1:1 prompt + `prepared_visuals/1x1/thumbnail_main.png`;
- alternate 3:2 prompt + `prepared_visuals/3x2/thumbnail_main.png`;
- alternate 1:1 prompt + `prepared_visuals/1x1/thumbnail_main.png`.

Use the prompt text from `visual-direction/theme.txt` verbatim as the art
direction. Do not substitute a summary, combine ratios, or invent another
prompt. Save the returned images, without cropping or recompressing them, as:

- `prepared_visuals/final-thumbnails/thumbnail_main_3x2.png`;
- `prepared_visuals/final-thumbnails/thumbnail_main_1x1.png`;
- `prepared_visuals/final-thumbnails/thumbnail_alt_3x2.png`;
- `prepared_visuals/final-thumbnails/thumbnail_alt_1x1.png`.

Inspect all four generated images at full size and at small marketplace size.
Confirm the exact product name and descriptor, visible lettering fidelity,
ratio, title prominence, contrast, and that each image follows its matching
theme prompt. If an image has an obvious text, ratio, or composition failure,
make at most one targeted regeneration for that image with the same specimen
and prompt. Do not leave final thumbnail creation for the seller. If the
image-generation tool fails or an image remains unusable after that retry,
stop and report the specific missing or failed output rather than marking the
handoff ready.

After saving the four images, update `visual-handoff-manifest.md` to list their
actual dimensions and set `thumbnail_state: generated final thumbnails`;
remove any manual-replacement-required thumbnail note. Then run the strict handoff
validator. It requires both lettering references, all four generated
thumbnails, and all 24 support renders.

### Bespoke thumbnail prompt requirements

Read `docs/AGENT-27-CREATIVE-PROCESS.md` and the seller's saved research in
`font-factory/Style-References/thumbnail-prompt-research-2026-10-20/` before
authoring prompts. That research is active preference evidence, not an
optional gallery. For an ordinary run, read only `prompt-findings.md` and
`prototypes/review.md`; their synthesis is sufficient. Do not retrieve
individual records from `reference-review.md` or `captions.json`, and do not
open research or prototype images. This avoids anchoring a new direction to a
favorite example's exact layout, subject, palette, or props. Inspect a specific
reference only when the seller asks to use it or when the written findings are
ambiguous; in that case, use it to resolve that question, not as a template.
No old marketplace thumbnail for the current font is required.

Compare up to five recent visual plans only when they exist in the current
workspace. Use the saved research's positive and negative findings to calibrate
focus, color, detail, and user taste; do not inspect the underlying reference
images. If fewer than five plans exist, use the written prototype review, not
the prototype gallery. Build the novelty pass from the specimen, name, buyer
context, and synthesized preference principles: privately sketch at least
three distinct directions, then select a primary and an alternate that fit
this font.
The alternate must differ from the primary in subject, medium, or major
structure; a palette-only change is not a new concept. Both must differ in
subject or major structure from available recent plans. Do not include private
chain-of-thought. Record a concise novelty note for both directions in the
already-required `candidate-review.md`.

Start from the actual white-background font-name specimen. Observe its natural
capitalization, proportions, terminals, stroke contrast, joins, and filled or
outlined construction. State only the features visible in the specimen. Then
write a one-sentence concept thesis that ties one of those features to one
specific subject, environment, material, or graphic action. If the idea could
fit any unrelated font unchanged, make it more specific.

Each complete prompt should stand on its matching white-background specimen
alone. Do not impose a word count. State the exact specimen behavior to
preserve, one specific visual premise, the title's position and minimum
occupancy (75% of frame width and 35% of frame height), the supporting subject
or graphic structure, palette/value contrast, and any focus hierarchy needed
at thumbnail size. All four prompts include the exact font
name plus the same concise style descriptor, set as a secondary but readable
line at small size in clean, neutral sans-serif typesetting. Name the neutral
sans-serif treatment explicitly in every prompt; do not leave the descriptor's
font style for the image model to invent. Use title case for the descriptor;
preserve natural title case in the name, with all caps only when the font itself
is designed that way.
Do not add unapproved claims or extra supporting copy. Use enough detail to
make each layout unmistakable, then stop; do not enumerate caption details as
props.

For every newly authored visual plan, set `visual_palette_schema` and
`visual_research_schema` to `1`. For each direction, cite the relevant
synthesized finding by summary-file path and principle, then record how it
fits this font, what the design applies, and what it avoids. Cite only
`prompt-findings.md` or `prototypes/review.md`; both directions may use the same
summary because the design must come from the font, not from finding a new
reference image. The handoff validator checks these records.

Give each direction a `lettering_colors` record for the title, descriptor, and
the field directly behind both lines. Name each color, give its hex value, and
explain why the title color belongs to the concept. Choose hue, saturation and
contrast to fit the concept and the seller's research signals; do not default
to weak, unconsidered neutrals or to bright colors without a reason. Use the
color contrast validator against the backing field and include the same hex
values in both ratio prompts. Keep the title over its named backing field; if
it crosses multiple colors, provide and validate each actual pairing.

Keep the background to one visual premise and its purposeful subjects or
materials. Avoid unrelated prop piles, labels and effects, but do not force a
flat or minimal solution when the research and font idea call for a richer
photograph, illustration or print treatment. Color contrast, lettering color,
and background should support the same idea rather than compete.
Do not mistake a written rationale for visual impact. Before rendering, confirm
that the concept has a visible anchor or a memorable type relationship—not just
a solid field with fine grids, circles, or abstract marks. A restrained design
still needs a clear visual payoff at thumbnail size. Give the palette a
distinctive, concept-led color relationship and an intentional accent; numeric
contrast alone does not make a palette vivid or cohesive. Avoid low-energy,
near-monochrome color and pale decorative accents as defaults. Do not force
neon or unrelated saturation; choose colors that make this specific font idea
read clearly and feel compelling.

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
candidate-review.md: the font-specific reason for the idea; the synthesized
preference finding and principle used; what the design applies and deliberately
leaves out; the title's
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

## One-pass render and validation

Create `visual-direction/visual-plan.json` and a short
`visual-direction/candidate-review.md` decision note. Run the handoff command
once:

```bash
python3 bin/generate_font_text_placeholders.py \
  --plan font-factory/fonts/{input-slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{input-slug}/prepared_visuals
```

It generates two thumbnail lettering references and 12 eligible HTML/CSS support
templates at both 3:2 and 1:1. It also derives `theme.txt`,
`image-notes/`, `art-direction.md`, the manifest and ready marker. Do not hand
edit generated views. If a mechanical validator error occurs, fix that error
and rerun; do not create multiple visual variants or polish a PNG for its own
sake.

The prepared handoff is expected to contain:

```text
prepared_visuals/
  3x2/thumbnail_main.png
  1x1/thumbnail_main.png
  supporting/3x2/support-*_*.png       # 12 eligible templates
  supporting/1x1/support-*_*.png       # the same 12 square adaptations
  visual-handoff-manifest.md
  VISUAL-HANDOFF-READY.md
```

Thumbnail and support PNGs stay in `font-factory/`; Agent 13 must not
copy or reinterpret them. Agent 13 does not install Pinterest assets. The handoff manifest
lists all 24 support renders and links to
`visual-direction/theme.txt`, which contains four prompts: a primary and an
alternate direction, each with 3:2 and 1:1 compositions. Both directions use
the matching-ratio lettering specimen. Supporting templates
are renderer-generated review assets, not image-model placeholders. Never
move to Agent 13 if the renderer or validator fails.

## Completion response

When validation passes, report:

```text
READY FOR FONT PREP HANDOFF
Font: {exact-font-name}
Source: {Saved source folder or existing staged workspace}
Staged workspace: {exact font-factory/fonts/{input-slug} path}
Draft visuals (stay in font-factory): {absolute prepared_visuals path}
Contents: 12 HTML/CSS support designs (24 renders), 2 thumbnail lettering references, 4 thumbnail prompts across 2 distinct directions
Profile: {type label}; {subtext}; description saved in visual-direction/visual-plan.json
Character atlases: {absolute character-atlases path}; {mapped character count} per style
Validation: PASS
```
