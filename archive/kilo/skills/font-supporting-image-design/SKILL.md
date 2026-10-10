---
name: font-supporting-image-design
description: Plan distinct font-specific supporting-image copy and layouts for the provisional white-background handoff, with independent landscape and square intent.
---

# Font supporting-image design

Supporting images answer the questions a thumbnail cannot. They are not a
gallery of generic promo templates and they are not a quota of random effects.
Choose each image because it proves something useful about this font to a
buyer.

## Choose the proof, not the template

After the thumbnail is approved, list the unanswered buyer questions. Select
exactly eight distinct proofs from the font's actual behavior and supported description.
Possible proof types include:

- display rhythm and headline presence;
- a credible poster, label, package face, title card, badge, or lockup when
  that job is supported;
- glyph character, numerals, punctuation, language coverage, or verified
  alternates;
- weight/style/outline/texture variation when those files or features exist;
- spacing, repetition, contrast, or a letter relationship that is unusually
  characteristic;
- a restrained specimen or construction study when it teaches more than a
  fabricated application.

These are questions, not a mandatory sequence. A font with one strong display
style may need more construction and glyph proof. A family with real weights
or alternates can show the system. If a practical context is not supported,
do not invent it merely to make the set look varied. Abstract or experimental
work is optional and earns a place only when it explains the font better than a
clear typographic proof.

## Weight the proof set by font family

The eight proofs should form one coherent campaign. Which proofs carry the most
weight depends on the font's category and personality — treat this as a
tie-breaking ladder, not a script:

- **Handwritten / Script / Calligraphy** — weight toward *lettering and texture*:
  wordforms, ink/rhythm variation, joins, and a credible invitation/label/quote
  job if supported. Glyph grids matter less; the *living wordform* is the proof.
- **Geometric / clean Sans Serif** — weight toward *construction and system*:
  proportion/grid evidence, alignment proof, weight/duo relationships, and a
  restrained identity or UI-esque use if supported. Discipline over decoration.
- **Serif / Slab Serif** — weight toward *editorial rhythm and contrast system*:
  headline/pull-quote read, weight ladder, and the serif's character details
  (terminals, bracketing). A supported book/editorial identity context works.
- **Display / large-format / quirky** — weight toward *attitude and unique
  glyphs*: the distinctive letters and alternates, a poster/title-card use if
  supported, and construction proof showing how the quirk is built.
- **Symbols / decorative glyphs / ornaments** — weight toward *character-set
  proof*: arranged glyph fields, frames/ornament systems, and how odd symbols
  combine — since the range of glyphs is the product.

When two proofs compete for a slot, keep the one that a buyer cannot get from a
different font of the same category, and the one that genuinely answers a
remaining buyer question. Drop a proof that merely re-states the thumbnail with
a new color or a swapped word. The strongest set reads as *one font*, not one
template repeated.

Every promo must state a different role or buyer question (authored-art plans
may record that as `visual_question`), a different reason to exist, and
deliberate readable on-image copy. The provisional handoff uses
exactly eight copy-led boards, but it has no fixed copy-mode taxonomy or
mandatory genre sequence. A promo's main phrase should feel like believable
real-world copy for the specific font; the idea may be a short phrase, a lone
dominant word, a compact label, an editorial statement, or something else that
answers a buyer question. Do not make every board a feature-label stack, reuse
the same sentence in a new position, or borrow stock examples from this
instruction. Record the exact copy, free-text role, and layout in the visual
plan. Display copy may be fictional for composition and must not be reused as
an unsupported marketplace claim.

## Per-image theme variants (`theme.txt`)

Each image object in the visual plan also records a one-line `theme_variant`:
the exact theme direction for that board's final generated artwork. Author it
*after* the board's display phrase, role, layout placements, and ratio
compositions are decided, because the variant must complete the composition the
agent actually designed — the lettering on white is the seed that the final
theme dresses.

- Write `visual-direction/theme.txt` with exactly ten `##` sections:
  `thumbnail_main`, `thumbnail_japanese`, and `promo_1` … `promo_8`.
- Each section opens with the board's one-line `theme_variant` (the same string
  recorded in the plan JSON), then 2–4 supporting lines: the shared world
  constants to keep from the global `supporting_image_theme` (art language,
  palette family, atmosphere root) and the panel-specific variation to explore
  (motif, texture, colour emphasis, shape language, composition dressing).
- The set must read as one campaign — same flat 2D graphic world, same palette
  family, same atmosphere root — while each panel stays visibly different
  ("same feel, sameish"). Never ten unrelated ideas, never ten copies of the
  same description.
- Every variant keeps the flat-2D constraints of the global theme sentence: no
  live 3D environment, photograph, room/landscape/tabletop scene, staged
  object, people/hands, perspective surface, depth, or cinematic set; no
  "scene", "environment", "immersive", "in a room", or "on a product".
- The variants are the ready-made prompts for the seller's manual image pass;
  phrase them so a Custom GPT/image model can act on them directly and never
  invent product facts or unsupported claims.

## Premium presentation principles

Typography-led premium font listings commonly let the type be the subject:
large display words, clean fields, considered editorial or identity contexts,
glyph/style details, and short factual labels. A supporting set can feel rich
without background photography. YouWorkForThem product pages are useful
current references because they separate Images, Glyphs, and Type Tester and
show how distinct images can support both taste and product proof:

- https://www.youworkforthem.com/font/T23669
- https://www.youworkforthem.com/font/T19176
- https://www.youworkforthem.com/font/T22207/dx-slight/194598
- https://www.youworkforthem.com/font/T19242
- https://www.youworkforthem.com/font/T4031/

Study the hierarchy and buyer questions, not their particular art, wording,
or brand treatment. Keep visible claims tied to the supplied description and
font inspection.

## Provisional text-placeholder handoff

The active Agent 27 path does not author editor source files or generate
finished artwork. It writes a JSON visual plan and runs
`bin/generate_font_text_placeholders.py`, which renders the real product font
and copy font as large black typography on white in both 3:2 and 1:1 ratios.
The white boards are intentionally useful references for the user's later
Custom GPT/image-model pass; their provisional status is recorded in metadata,
not printed on the images. They must be allowed to pass downstream so the
listing workflow can finish.

For every promo, plan a main phrase plus one concise supporting block, adding
more blocks only when the particular idea truly needs them. Specify a free-text
role or buyer question, a mandatory authored placement for every displayed
block, a scale, and a short rationale explaining why that placement and scale
serve the intended composition. Make the roles materially different based on
the font's actual personality and plausible uses; there is no required list of
genres. Place copy in intentional zones and leave a clear gap around a centered
hero; supporting copy must never run across the main phrase. The dominant block
must use a substantial scale, and every block must fit safely inside both
canvas ratios without becoming a tiny island. The thumbnail remains name-only,
including the Japanese thumbnail.

Do not add workflow notices, replacement instructions, fake feature claims, or
generic filler to the PNGs. Factual font specimens remain separate from the
creative promo copy.

## Copy and contrast

Use one dominant typographic statement plus only the supporting copy that earns
its space. More words are not automatically more informative. The important
display type must use the real product font; auxiliary copy may use the
verified copy font. The placeholder renderer uses black on white for reliable
contrast and keeps copy large enough to become a useful image-model reference.

## Ratio-specific composition

The 3:2 and 1:1 files are independently authored. Never crop, pad, rescale, or
retrofit one master composition.

Use the 3:2 field for a deliberate horizontal idea: a long word, directional
relationship, editorial spread, side-by-side comparison, or controlled open
space. Use the square for a compact idea: a stack, monogram, crop, seal-like
lockup, dense glyph field, or centered message. These examples are prompts for
reasoning, not fixed layouts. The actual font decides.

The ratio note must say what changes in focal type, grouping, spacing, crop,
and copy order. If the two sources look interchangeable, redesign one of them.

## Per-image review

Write the image note before authoring. It must record the buyer question, exact
copy, verified font behavior, palette and contrast decision, effect budget,
independent ratio decisions, and why the promo is not redundant.

Run the placeholder helper and strict handoff validator:

```bash
python bin/generate_font_text_placeholders.py \
  --plan font-factory/fonts/{font-slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{font-slug}/prepared_visuals
python bin/validate_font_visual_handoff.py \
  font-factory/fonts/{font-slug}/prepared_visuals --strict-art-direction
```

The machine checks confirm:

- font identity and first read;
- required ratios, filenames, dimensions, and specimen families;
- name-only thumbnails;
- exactly eight promos, readable copy blocks, distinct roles/main copy,
  mandatory authored layout/rationale, and the provisional marker;
- readable, non-empty text blocks and the provisional marker.

The resulting PNGs are intentionally provisional. Do not block the listing
workflow on their taste-level finish; after the workflow, the user can place
final raw artwork in `outputs/font-preparation/{font-slug}/visuals/New-Images/`
and invoke the standalone `/font-final-images` processor.

The final set should feel like one font campaign because the font is the same,
not because every image repeats the same template, palette recipe, or effect.
