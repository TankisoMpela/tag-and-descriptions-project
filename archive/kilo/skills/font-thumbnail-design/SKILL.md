---
name: font-thumbnail-design
description: Plan a readable name-only font thumbnail for the provisional white-background handoff in 3:2 and 1:1 ratios.
---

# Font thumbnail design

The thumbnail is the buyer's first proof that this is a particular font, not a
generic graphic. In the active fast handoff, make it a clean name-only
typographic reference on white. Do not select a repository template, use an
image model, or add a generic “hero” card around it.

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

Before authoring the plan, confirm the final font name, the real product font
file, and the copy font/path available to the placeholder renderer. The active
handoff does not need a design-editor preflight or image-model call.

The thumbnail copy is exactly the final font name, rendered large in the real
product font. If it has two words, stack those words for visibility. Do not add
a tagline, category, feature label, workflow notice, replacement instruction,
or descriptive sentence. The Japanese thumbnail follows the same name-only
rule. Supporting phrases belong on the differentiated promo boards.

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

## Provisional name-only composition

Record a thumbnail plan with exactly one `copy_blocks` entry containing the
final font name and a centered `hero` placement. Also record a one-line
`theme_variant` on each thumbnail object: the art/mood/palette direction for
the final generated thumbnail artwork (same flat 2D world as the global
`supporting_image_theme`, tailored to the name-only lockup). That exact line
later appears under `## thumbnail_main` / `## thumbnail_japanese` in
`visual-direction/theme.txt`, which the seller pastes into the manual image
pass. The helper renders the real
product font on a white 3:2 board and a white 1:1 board; if the name has two
words, it stacks them automatically. The Japanese thumbnail uses the same
name-only copy with the available Japanese-capable copy font.

Do not add a tagline, category, feature label, fake claim, workflow notice,
replacement instruction, or tiny decoration. Supporting phrases, use-case
signals, and differentiated layouts belong on the promo boards. The thumbnail
must be highly legible when reduced and must not be allowed to collide with
itself or clip at the canvas edge.

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

Run the placeholder helper and strict handoff validator. They verify that the
thumbnail is name-only, uses the real font, has the required ratios and
dimensions, and contains no workflow text:

```bash
python bin/generate_font_text_placeholders.py \
  --plan font-factory/fonts/{font-slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{font-slug}/prepared_visuals
python bin/validate_font_visual_handoff.py \
  font-factory/fonts/{font-slug}/prepared_visuals --strict-art-direction
```

This is a provisional handoff, not a finished creative review. Do not stop the
listing workflow over the plain white treatment; after the workflow, the user
can place final raw artwork in
`outputs/font-preparation/{font-slug}/visuals/New-Images/` and invoke the
standalone `/font-final-images` processor. Supporting-image differentiation is
reviewed on the promo boards, not by adding copy to the thumbnail.

## What is not mandatory

Do not create thumbnail candidates unless the direction is genuinely uncertain.
Do not force abstract art, photography, a product mockup, a three-color system,
a racing treatment, a handwritten treatment, or any other house style. Derive
the idea from the font. If a restrained wordmark field is the strongest proof,
make it excellent; if a more ambitious typographic construction is justified,
make it controlled and legible.

The thumbnail plan must record the exact displayed name, real font path,
available copy font, ratio placements, and the QA command that was run.
