# Brush-Factory Staging Policy

This folder is the input boundary for the Procreate brush listing agents.

## Authority

- `description.md` is the authority for the product name, concept, brush purpose, count, and honest feature claims.
- `source/` is the authority for the downloadable `.brushset`/`.brush` files. Never infer included brushes from a screenshot.
- `prepared_visuals/` contains user-approved creative assets made in the FontFairy Procreate Brush Image Director Custom GPT.
- `references/` is context only. Do not publish old branding, old copy, or old compositions.

## Handoff

Each product needs at least one `.brushset` or `.brush` file, `description.md`, and `prepared_visuals/thumbnail_main.png`. It may include `promo_N.png` files and an optional `thumbnail_pinterest.png`.

The listing agents inspect dimensions, readability, old branding, file names, and facts directly. A missing or unclear field is reported as a research gap; no separate brush-prep stage repairs it.

## Product safety

- Keep original brush files unchanged. The listing workflow is metadata-only.
- State **requires Procreate on iPad** unless the source product explicitly supports another app.
- Never claim a brush count, texture source, compatibility version, or commercial permission that is not evidenced by the source files or user description.
- If any listing visual was AI-generated, carry that fact into the Cubebrush `AI-CONTENT CHECK`; do not silently call it handmade or AI-free.

## Generated output

- Creative Market: `outputs/brush-creativemarket/{NUM}-{slug}-cm-brush.md`
- Cubebrush: `outputs/brush-cubebrush/{NUM}-{slug}-cb-brush.md`
