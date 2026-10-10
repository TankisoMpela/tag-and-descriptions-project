# FontFairy Font Image Director — Knowledge Base

This file is reference material for the Custom GPT instructions. The user's uploaded images in the conversation are always the source of truth for the actual font lettering and required copy.

## Asset contract

| Asset | User workflow | Target |
|---|---|---|
| `thumbnail_main.png` | Seed + old thumbnail | 3:2, normally 1500x1000 or 1600x1067 |
| `promo_N.png` | One old supporting image at a time | 3:2, normally 1500x1000 or 1600x1067 |
| `thumbnail_pinterest.png` | Re-upload approved generated thumbnail | 2:3, normally 1000x1500 |

The user saves approved files in `font-factory/fonts/{font-slug}/prepared_visuals/`. The filenames are case-sensitive and the promo sequence starts at `promo_1.png` with no gaps.

## Visual direction

The work should feel authored, graphic, colourful, and deliberate while remaining a flat, straight-on composition. Do not provide a preset menu of media or motifs; those examples bias the next design. Derive the medium and visual subject from the supplied font identity, name, description, and buyer job. Use texture only when it strengthens that specific concept. Do not chase a generic premium/editorial look.

Because the thumbnail has a name rather than a semantic headline, derive its concept from the supplied identity and name association. A name such as `Silken Flourish` must not trigger a desk, pen, ink bottle, stationery, marble, fabric, foil, or premium tabletop. Translate it into a flat illustrated subject or typographic event, and ask what is happening and what aspect of the supplied identity makes it necessary. If the answer is only a surface, object, material, palette, or atmosphere, reject the concept and restart. The surrounding graphic world must have a point of view.

**The font lettering must never be rendered on or wrapped onto a 3D surface** or made dependent on object depth. **Abstract 3D concept art is forbidden.** Keep the artwork flat and straight-on, with the lettering interacting with a newly invented graphic construction or illustration. For the main thumbnail specifically, photographic or real-life backgrounds are forbidden. Supporting promos may use their own flat contextual art direction and are not required to repeat the thumbnail's motif or layout.

Avoid 3D lettering, extruded type, perspective-heavy product mockups, floating objects, rooms, architecture, isometric scenes, folded or standing objects, cylinders, signage installations, acrylic panels, plinths, perspective-wrapped lettering, abstract 3D concept art, and any concept whose novelty depends on object depth. For thumbnails also hard-reject desks, pens, books, stationery, realistic paper or ink, marble, wood, fabric, leather, foil, plaster, concrete, glass, realistic product surfaces, cast shadows, reflections, lens blur, depth of field, and pseudo-real premium materials. Material words may describe a flat colour or drawn motif only.

## Source transformation rules

Old references provide content and purpose, not a layout template. A successful transformation changes several of: layout grid, text placement, scale relationships, crop, palette, negative space, motifs, surface treatment, and context. Never reuse the exact lettering color from the old reference image; select a distinct new lettering color that fits the new composition while maintaining high contrast. A different background or font name alone is not enough.

The supplied seed/reference lettering is the visual authority. Do not retype it in a generic font, distort distinctive glyphs, change spelling, or invent characters. The old thumbnail is also the authority for the font's legible product facts and claims: preserve every readable headline, slogan, feature label, weight, format, compatibility/language statement, glyph group, and buyer-useful message in the new image. If a detail is uncertain, inspect the uploaded source more carefully; do not drop a legible claim to simplify the layout.

Remove old creator, studio, and foundry names. FontFairy is the user's studio name (the new name replacing the old studio's branding) — the user includes it in the seed, and it may appear as a small attribution wordmark. Do not add URLs, social handles, fake claims, or unverified features.

## Mode-specific notes

### Main thumbnail
The main image features only the font name, stacked as two lines. No subtexts, taglines, supporting phrases, or extra labels. The name is the only typographic element and remains large, legible, and centred as the thumbnail lockup. Personality comes from a newly invented contextual motif/world or typographic event; do not make a name-only reskin or borrow a motif from earlier examples. The background must be a flat, straight-on 2D graphic construction—never a photograph, room, tabletop, landscape, product scene, or real-life backdrop.

### Supporting promo
One source produces one output. Use a realistic use-case phrase as the main text — a headline, title, quote, masthead, tagline, or poster heading that demonstrates what the font could be used for. Do not use the font name. No subtexts or secondary copy blocks. Give it a distinct composition that belongs to the same product identity and quality bar, but do not force it into the thumbnail's setting, palette, layout, or illustration recipe. The phrase must generate the concept: meaning → intention → visual question → physical event → placement. Strategic off-centre placement is preferred when it makes room for contextual artwork. Invent the subject from the current phrase and supplied identity; do not select a motif named in the instructions or repeat a stock visual recipe. A palette swap plus an abstract shape is a failure.
Keep the main phrase normally to 1–4 words, with at least five of eight promos at 1–3 words. Use 5 words only when the concept needs it, and use 6–8 words only once for a deliberate long-phrase legibility proof. Long slogans are not the default. Do not reuse generic workflow-example copy such as `Brand Identity`, `Create Beautifully`, `Your Story Matters`, `The Art of Elegant Lettering`, `Handcrafted with Care`, or `Forever Begins Here` unless the user explicitly supplied it; derive the visible phrase from the current font's name, construction, or visual action.

### Pinterest
The user re-uploads the already approved generated thumbnail. Preserve the same lettering and message while adapting the hierarchy for a vertical 2:3 frame. Use generous safe margins and a clear focal point. Do not use the old thumbnail as the Pinterest source.

## Failure checklist

Reject and regenerate the whole image if any of these occur:

- wrong, substituted, misspelled, duplicated, or nonsense lettering;
- clipped or unreadable required copy;
- old studio branding remains;
- the old composition was copied or only cosmetically reskinned;
- a supporting image's purpose or required copy was dropped;
- the result is 3D, perspective-staged, floating, folded, architectural, or object-mockup driven;
- font lettering is rendered on or wrapped onto a 3D surface (cylinder, box, wall, sign, plinth, or any object with depth), or the lettering itself is extruded/inflated/sculpted as 3D type;
- abstract 3D concept art or a photographic/real-life background is used for the main thumbnail;
- the requested ratio or safe margins are wrong;
- the image contains invented product claims.

The font-prep agent does not creatively repair failures. It only validates the files the user approves, copies the approved 3:2 images into `outputs/font-preparation/{font-slug}/`, and pads centered square derivatives mechanically. Pinterest and any other vertical asset are handled separately; no long-scroll is created.
