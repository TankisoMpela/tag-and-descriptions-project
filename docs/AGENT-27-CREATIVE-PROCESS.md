# Agent 27 — thumbnail creative process

This guide describes the current image workflow. The old thumbnail
reimagination process and its flat-only, no-photography, centered-title rules
are retired. The authoritative operational instructions are in
`agents/agent-27-font-image-generator.md`.

The seller's research in
`font-factory/Style-References/thumbnail-prompt-research-2026-10-20/` remains a
required design input. For an ordinary run, read `prompt-findings.md` and
`prototypes/review.md`; these syntheses capture the positive and negative
signals. Do not reopen individual reference or prototype images, which can
anchor new work to their exact subjects and layouts. Inspect one only when the
seller requests it or the written findings leave a specific question unresolved.
This short guide summarizes execution; it does not replace the underlying
research.

## What Agent 27 produces

Agent 27 renders the exact font name in the actual font on a clean white field.
These images preserve the font's real letterforms as raw material for an image
model; they are not finished thumbnail designs. It also writes four complete,
font-specific prompts in `visual-direction/theme.txt`: primary and alternate
directions, each composed separately for 3:2 and 1:1.

Each prompt is paired with the matching ratio's white-background specimen. Use
one direction consistently for the final thumbnail pair. The primary and
alternate directions must differ in subject, medium, or major graphic
structure; a palette change alone is insufficient. No old marketplace
thumbnail is required or used.

## How to build a prompt

Use the actual white-background font specimen, source metadata, shaped copy, and
verified buyer-use facts. Name one visible letterform trait and tie it to one
specific subject, place, material, or graphic action. Let the written research
guide hierarchy, color, detail, and variety without choosing a pictured example
as a template. A palette swap alone is not a new idea. When fewer than five
recent plans exist, compare the concept with the written prototype review, not
its image gallery. All lettering stays a flat, front-facing overlay; never
place the words onto a photographed or rendered surface.

Write concise, complete art direction. The old 80–140-word quota is retired; use only the words needed to describe the name and ratio, font-specific premise, title position/scale, its relationship to the scene, and essential local contrast/focus. The title must span at least 75% of the frame width and its visible glyph block at least 35% of the frame height. Reflow the name or simplify/move the scene if needed; never shrink the title to accommodate background elements. The lettering is always a flat 2D overlay, including when the background is a real 3D scene; it never follows that scene's plane, perspective, lighting, or material. In a photo with a person, crop out the face or soften and subdue it behind the crisp title.

For new plans, set `visual_palette_schema: 1` and `visual_research_schema: 1`.
Record each direction's title, descriptor and text-field colors by name and hex,
with a concept rationale, plus the synthesized preference principle it uses
and what it deliberately avoids. Choose hue, saturation and contrast to fit the
concept and seller's research signals; do not default to weak neutrals or bright
colors without a reason. Keep the background to one legible premise and its
purposeful elements. The handoff validator checks the color and research notes.

Preserve the name's spelling, natural capitalization, glyph shapes, spacing and filled/outlined construction. Keep important glyphs readable and inside the frame. Do not force supporting props or fill open areas. No glitter, sparkles, starbursts, confetti, particles, fake lens flare, arbitrary badges, gratuitous glow, excessive microtexture, or generic AI decoration. Avoid dark-on-dark and similar-value title/background colors. Compare recent plans only when present; when none exist, use a premise grounded in the font rather than a historical prototype. Privately develop three distinct directions and record only a concise novelty note in `candidate-review.md`. Do not rely on generic glossy luxury still lifes as a default. Avoid the rejected oversized cropped initial with orbit rings, split blue/berry descriptor panels, and arch/portal title frames as default recipes. A flat design can use quiet paper, ink, or print texture or a faint relevant illustration; keep it specific and secondary so the image feels authored without becoming busy or sterile.

## Review before handoff

Check that every prompt:

1. is complete enough to use with only its matching specimen;
2. describes one clear, font-specific premise with a restrained amount of detail;
3. gives the 3:2 and 1:1 main versions different compositions;
4. preserves the exact font name and does not add unrequested copy;
5. keeps the lettering legible, unclipped, and distinct from the background;
6. has a premise or major structural choice that distinguishes it from recent prompts; a palette swap alone is insufficient.

The model-generated final artwork is a later manual step. Inspect each result
for exact spelling and capitalization, preserved letterforms, crop, contrast,
small-size readability, visual coherence, and fidelity to its prompt before
approving it for the preparation folder.
