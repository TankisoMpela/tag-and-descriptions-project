---
name: font-thumbnail-design
description: Art-direct and review one font-specific thumbnail in OpenPencil, with separate 3:2 and 1:1 compositions.
---

# Font thumbnail design

The thumbnail is the buyer's first proof that this is a particular font, not a
generic graphic. Design it as a real typographic composition in OpenPencil.
Do not select a repository template, use an image model, or make a generic
“hero” card by filling slots.

## Start with font truth

Inspect the supplied font and description before choosing a visual idea. Find
the feature that remains recognisable at small size: proportion, width,
contrast, terminals, counters, rhythm, texture, a strong letter relationship,
or a verified alternate. Shape the proposed words with the actual font and
discard phrases that produce weak or misleading forms. The name may be part of
the image, but do not let the name alone become the whole art direction.

Ask:

- What should a buyer understand in two seconds?
- What makes this font different from an unrelated font with the same palette?
- What short phrase gives the font enough room to show its personality?
- What one supported buyer job can be hinted at without inventing a scene?

The copy does not need a fixed word count. Use one dominant phrase and one or
two supporting labels or facts when they earn their space. Do not add tiny
microcopy, fake feature claims, or decorative words merely to fill empty areas.
Record the actual OpenPencil product font family in `font_files[].family` and
`featured_font_families`; the public font name may differ during a rename, but
the renderer must see the real family on at least one text node.

## Match the proof to the font family

The font's category and personality decide which proof will be the most honest
and the most convincing at thumbnail size. Treat this as a decision ladder, not
a template: the strongest proof for that construction tends to be, in order:

- **Handwritten / Script / Calligraphy** — the lettering itself is the subject:
  a word or phrase set in the actual font, letting its rhythm, joins, and ink
  variation carry the image. Lead with the real wordform, not a background or a
  generic swash.
- **Geometric / clean Sans Serif** — the strongest proof is often *construction
  or system*: evidence of proportion, alignment, or a grid-based relationship,
  or a crisp wordmark that shows industrial precision. Show discipline over
  decoration.
- **Serif / Slab Serif** — lead with editorial rhythm and the weight/contrast
  system: a headline, a composed word pair, or a proof of the serif's character
  (bracketing, terminals, stroke contrast) that reads like an editorial identity.
- **Display / large-format / quirky** — prove *attitude and unique glyphs*: the
  unusual letters, alternates, or a lockup that shows the font's distinctive
  voice, not a busy scene around it.
- **Symbols / decorative glyphs / ornaments** — the proof is the *character set
  itself*: a grid or focused arrangement that shows the range of glyphs and how
  they work together, framed cleanly.

These are starting hypotheses, not fixed assignments. The honest recipe is:
*what this specific font does that an unrelated font of the same category
cannot — make that the two-second message.* A restrained wordmark is still the
right answer when the font's strength is restraint; a construction proof is
right when the font's strength is its system.

## OpenPencil composition

Author a one-off OpenPencil `.jsx` document, compile it to `.fig`, and keep
both. Use named nodes such as `Hero`, `Product Name`, `Buyer Cue`, `Rule`, and
`Background` so `openpencil tree`, `find`, and `node` can inspect the intent.
Useful OpenPencil strengths include:

- large real-font text and deliberate scale relationships;
- flat color fields, panels, rules, masks, clipping, and vector geometry;
- controlled gradients, opacity, shadows, and small amounts of texture;
- repeated shapes or letterforms when repetition is part of the font idea;
- simple layout relationships when they improve alignment.

Avoid fragile techniques unless the exact result is simple and survives review:

- perspective or curved type that is hard to judge;
- photorealistic materials, reflections, and complex 3D;
- dense tiny labels, invented products, and text embedded in a generated image;
- too many competing focal points or effects that cover the glyphs.

The background exists to reveal the type. Choose foreground/background pairs
that separate in practice, not just in a palette swatch. Calculate and record
contrast ratios. No vision tool exists in this runtime; verify separation
through the machine checks and the contrast math. If a color is attractive but
the words would disappear, change the color or remove the element.

## Ratio decisions

Author the 3:2 and 1:1 thumbnails as two designs with a shared promise, not one
design resized twice.

For 3:2, consider what the horizontal field gives you: a long wordform, a
directional read, a large side-by-side relationship, a typographic margin, or a
strong asymmetry. Do not spread elements thinly just because the canvas is
wide.

For 1:1, consider a compact lockup, a decisive crop into one letter, a centered
monogram, a vertical stack, or a dense but controlled typographic field. Do not
shrink the landscape layout into the square or preserve empty side margins
that belonged to the other ratio.

The two sources must have different composition and copy-order notes. A ratio
difference is meaningful only if the focal type, spacing, grouping, or crop
actually changes.

## Review gates

Before moving on, review the asset with the machine QA that needs no vision:
the renderer's structural checks plus `analyze`/`lint`/`info` and the recorded
contrast math, and verify the authored intent against those results. Do not
attempt to view, interpret, or OCR any rendered PNG — no vision or OCR tool
exists in this runtime. Flag taste-only judgments for the human reviewer
instead of leaving them unresolved. Check:

1. Font identity: is the supplied font the first thing the eye can judge?
2. Focal point: is there one clear first read?
3. Typography: are there enough purposeful words to communicate the product,
   with no filler or misleading claim?
4. Contrast: do all important words separate from their immediate background?
5. Composition: is the available canvas used intentionally without crowding?
6. Reliability: are there no clipped glyphs, accidental overlaps, broken
   effects, impossible-to-read details, or generic decoration?
7. Ratio: does each version use the strength of its own canvas?

Use OpenPencil's machine-readable checks as the evidence of record — they need
no vision:

```bash
npx --no-install openpencil info path/to/thumbnail.fig --json
npx --no-install openpencil tree path/to/thumbnail.fig --depth 4 --json
npx --no-install openpencil find path/to/thumbnail.fig --name "PRODUCT NAME" --json
npx --no-install openpencil analyze colors path/to/thumbnail.fig --json
npx --no-install openpencil analyze typography path/to/thumbnail.fig --json
npx --no-install openpencil analyze overlaps path/to/thumbnail.fig --include-absolute --json
npx --no-install openpencil lint path/to/thumbnail.fig --preset strict --json
```

Fix errors and weak visual decisions before authoring supporting images. A
technically valid thumbnail can still be rejected for weak hierarchy,
insufficient typography, poor contrast, or wasted space.

## What is not mandatory

Do not create thumbnail candidates unless the direction is genuinely uncertain.
Do not force abstract art, photography, a product mockup, a three-color system,
a racing treatment, a handwritten treatment, or any other house style. Derive
the idea from the font. If a restrained wordmark field is the strongest proof,
make it excellent; if a more ambitious typographic construction is justified,
make it controlled and legible.

The thumbnail note must record the actual displayed copy, font feature,
visual question, palette/contrast decision, independent 3:2 and 1:1 choices,
what QA was run (machine checks only; no vision or OCR), and any correction
made.
