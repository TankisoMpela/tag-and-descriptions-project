---
name: font-supporting-image-design
description: Art-direct and review distinct font-specific supporting images in OpenPencil, with independent landscape and square compositions.
---

# Font supporting-image design

Supporting images answer the questions a thumbnail cannot. They are not a
gallery of generic promo templates and they are not a quota of random effects.
Choose each image because it proves something useful about this font to a
buyer.

## Choose the proof, not the template

After the thumbnail is approved, list the unanswered buyer questions. Select
4-8 distinct proofs from the font's actual behavior and supported description.
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

The 4-8 proofs should form one coherent campaign. Which proofs carry the most
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

Every promo must have a different `visual_question`, a different reason to
exist, and actual copy that is useful. Avoid repeating the thumbnail with a
new color or swapping the same word into five layouts.

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

## OpenPencil authoring rules

Author every promo as its own OpenPencil `.jsx` and `.fig`. Use named nodes and
clear grouping so the intent can be inspected with the CLI. OpenPencil is good
at:

- type-led fields and deliberate scale;
- panels, rules, grids, masks, clipping, simple vector geometry, and clean
  repetition;
- controlled fills, gradients, opacity, shadows, and bounded texture;
- compact systems of labels and display type that remain editable and queryable.

Use these strengths to make ambitious ideas practical. Do not ask the tool to
solve fragile visual problems such as photorealistic backgrounds, complicated
perspective, physically accurate 3D, realistic reflections, lots of tiny
objects, or tiny copy that must be read at thumbnail size. Every treatment
must be verifiable confidently by the machine checks; there is no vision tool
in this runtime to look at a rendered PNG. If a treatment cannot be verified,
simplify it.

Do not make a one-off “generic art generator” that emits all promos by
substituting words, colors, or coordinates. If a single authored JSX file
contains several deliberately related panels, that relationship must be the
design decision and be explained in the note. Otherwise each source file is
one image.

## Copy and contrast

Use one dominant typographic statement plus only the supporting labels or facts
that earn their space. More words are not automatically more informative. Do
not use placeholder copy, fake feature names, or microscopic captions.

The important display type must use the real font. Auxiliary text may use a
verified secondary face only when it improves hierarchy. Every important
foreground/background pair must have a recorded contrast calculation and must
survive the visual check. Texture and effects cannot be allowed to reduce the
legibility of the font.
Record the actual OpenPencil product font family in `font_files[].family` and
`featured_font_families`; if the public marketplace name differs from the
internal/render family during a rename, the render family is what the machine
check must see on at least one text node.

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

For each ratio, run structural inspection:

```bash
npx --no-install openpencil info path/to/promo.fig --json
npx --no-install openpencil tree path/to/promo.fig --depth 4 --json
npx --no-install openpencil analyze colors path/to/promo.fig --json
npx --no-install openpencil analyze typography path/to/promo.fig --json
npx --no-install openpencil analyze overlaps path/to/promo.fig --include-absolute --json
npx --no-install openpencil lint path/to/promo.fig --preset strict --json
```

Then render the exact output with the local-font-aware handoff bridge. These
machine checks run without vision and are the evidence of record — no vision or
OCR tool exists in this runtime, so never attempt to view, interpret, or OCR a
rendered PNG.
`analyze overlaps` and `analyze typography` detect clipping, overlaps, spacing,
and effect failure; `lint` and `info` confirm structure and fonts; the recorded
contrast math covers color separation. Check:

- font identity and first read;
- distinct buyer proof;
- sufficient, legible, purposeful typography;
- color separation at every important text block;
- clipping, overlap, awkward spacing, and effect failure;
- whether the canvas is used intentionally;
- whether the image still reads when reduced;
- whether the landscape and square versions use their own strengths.

Record what pops, what failed, and the correction. Reject weak images even if
the PNG dimensions and source files are technically valid. If a judgment is
taste-only, flag it for the human reviewer rather than leaving it unresolved.

The final set should feel like one font campaign because the font is the same,
not because every image repeats the same template, palette recipe, or effect.
