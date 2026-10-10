---
name: brush-workflow
description: Procreate brush image handoff and Creative Market/Cubebrush listing workflow.
---

# Unified Procreate Brush Workflow

This workflow is parallel to `font-workflow`. It takes user-supplied `.brushset`/`.brush` files, user-approved creative images from the PaperMoon Procreate Brush Image Director Custom GPT, and a user-written product description. It never generates, repackages, or rewrites brush files inside Codex.

## Pipeline

```text
brush-factory/brushes/{slug}/
  source/*.brushset or *.brush
  description.md
  prepared_visuals/thumbnail_main.png + promo_N.png (+ thumbnail_pinterest.png)
          |
          +--> Agent 15 /cm-brush -> outputs/brush-creativemarket/{NUM}-{slug}-cm-brush.md
          |
          +--> Agent 16 /cb-brush  -> outputs/brush-cubebrush/{NUM}-{slug}-cb-brush.md
```

Run `/cm-brush` first and `/cb-brush` second so both outputs reuse the same product number. Both agents are listing-only; there is no brush preparation stage.

## User handoff

1. Put original brush files in `brush-factory/brushes/{slug}/source/`.
2. Put the user-supplied product facts and final name in `description.md`.
3. Create one image at a time in the Custom GPT using the old reference only as a content/purpose reference.
4. Approve the new images and save them as `thumbnail_main.png`, `promo_1.png`, etc. in `prepared_visuals/`.
5. Optionally save the approved 2:3 image as `thumbnail_pinterest.png`.
6. Run `/cm-brush brush-factory/brushes/{slug}/`.
7. Run `/cb-brush brush-factory/brushes/{slug}/`.

## Agent responsibilities

### Agent 15: Creative Market

- Reads the source files, description, and approved visuals directly from Brush-Factory.
- Researches live CM brush categories, popular listings, competitor pages, and autocomplete.
- Outputs a maximum-36-character title, maximum-55-character meta title, maximum-155-character meta description, approximately 400-word PDP copy, exactly 30 evidence-backed tags, category, content disclosure, and alt text.
- Does not package files or modify the brush archive.

### Agent 16: Cubebrush

- Reads the source files, description, and approved visuals directly from Brush-Factory.
- Researches live Cubebrush brush listings/editor/help pages and competitor language.
- Outputs a keyword-first title under 100 characters, a 300+ word **plain-text description body** for direct Cubebrush paste, current category labels (public brush listings commonly use Tools / Software Brushes / Procreate), Basic/Commercial/Studio license choice when exposed, 20 primary terms + 10 extended terms, image handoff, alt text, and the mandatory AI-content check.
- Never turns uncertain upload or payout details into hard facts. Important cover content stays in the middle 60% because the thumbnail may center-crop. The internal output file may be Markdown; the Cubebrush description field must not contain Markdown syntax.

## Shared rules

- The final user-supplied product name is authoritative. No naming agent is part of this workflow.
- Do not read or publish `references/`; it exists only to help the separate image GPT understand old copy and purpose.
- Never claim a brush count, app version, material, license, or AI provenance that is not in the source facts.
- If a tool or live page fails, record the failure and proceed only with evidence that remains. Do not invent a taxonomy.
- Marketplace listing files use the existing brush product number when available; otherwise each output folder assigns the next numeric prefix.
- No Pinterest or freemium stage is included here; add a separate stage only when explicitly requested.
