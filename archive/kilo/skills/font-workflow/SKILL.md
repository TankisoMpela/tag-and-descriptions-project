---
name: font-workflow
description: End-to-end font workflow with metadata-first preparation, fast provisional visual handoff, and strict sequential marketplace SEO delegation. Creative Market, Behance, and Pinterest are paused from the default run.
---

# Unified Font Preparation and Marketplace SEO Pipeline

This skill covers the visual-generation handoff, technical preparation, and the
paid marketplace-copy stages. Agent 27 creates the visual handoff first. Agent
13 then handles package preparation, metadata, audit, videos, and the unchanged
factual-specimen handoff while leaving the provisional creative marketing images
untouched. Once preparation is complete,
marketplace agents run strictly one at a time. Final seller-replaced image
delivery is a separate explicit Agent-30 stage.

## Preparation handoff

1. Stage raw font files in `font-factory/fonts/{font-slug}/`.
2. Run Agent 27 / `font-images` for the naming decision and fast visual
   handoff. Supply the exact font workspace plus the old product description or
   a public product URL, and optional factual constraints. Agent 27 first runs
   the Font Renamer naming contract from that description/URL — it decides the
   final two-word font name, authors the one-sentence
   `Supporting-image theme sentence` (carried verbatim as
   `supporting_image_theme` in the visual plan and handoff manifest), authors
   per-image theme variants in `visual-direction/theme.txt`
   (`thumbnail_main`, `thumbnail_japanese`, `promo_1` … `promo_8`), and
   writes `visual-direction/font-name-report.md`. It never uses reference
   images and never prints the theme sentence as image copy or replaces it with
   a generic theme. It writes white text placeholders for
   the thumbnail and exactly eight supporting
   images, four factual specimen PNGs, a `text_placeholder` visual plan/manifest, and
   `VISUAL-HANDOFF-READY.md` under the font workspace. It does not use
   OpenPencil or image-generation tools.
3. Run Agent 13 for metadata and package preparation.
   Agent 13 writes font binaries to a font-named folder under
   `outputs/font-preparation/{catalogue-number}-{font-slug}/`, creates the
   `Commercial-Use` ZIP (font binaries only) and `Personal-Use` ZIP (font
   binaries + `PLEASE-GIVE-US-A-LIKE.txt` at the archive root), and keeps
   `description.txt` outside the package at the output root. It also renders the main and Etsy
   showcase videos. It copies the four named factual specimen PNGs unchanged
   into the output `specimens/` folder when Agent 27's validated handoff is
   available. It does not copy, compress, rename, inspect, or compose creative
   marketing images.
4. Continue to the marketplace stages. The Agent-27 handoff remains
   provisional/deferred and does not stop the workflow.
5. After final artwork is manually placed in
   `outputs/font-preparation/{catalogue-number}-{font-slug}/visuals/New-Images/`, run the explicit
   `/font-final-images` command. Agent 30 performs the image delivery and
   Pinterest pass inside that folder.

Agent 27 owns creation of the provisional text handoff and factual specimens.
Agent 13 owns font/package/video preparation plus the unchanged copy of those
four factual specimens. Agent 30 owns final creative image delivery;
marketplace agents do not repeat either technical pass.

## Required post-preparation sequence

The default marketplace stages are:

1. Agent 20 — BOOTH
2. Agent 24 — DLsite
3. Agent 23 — YellowImages

YellowImages uses the eventual approved 3:2 visual set from
`visuals/New-Images/main/` when Agent 30 has completed; Agent 13 does not
create a separate YellowImages image set or a special 1160x772 creative
variant. Creative Market, MasterBundles, Cubebrush, Behance, Pinterest, Pixiv,
Creative Fabrica, Etsy, and DaFont/FontSpace remain explicit standalone stages unless the user
requests them.

Do not dispatch these agents concurrently, in one task array, through
`Promise.all`, or as background workers. After each delegate returns its final
result, pass the needed product facts and prior output path forward, then start
the next delegate. If a stage fails or the user says stop, halt the chain and do
not launch later stages.

## Marketplace commands

```text
/booth-font "outputs/font-preparation/{catalogue-number}-{font-slug}/"
/dlsite-font "outputs/font-preparation/{catalogue-number}-{font-slug}/"
/yellowimages-font "outputs/font-preparation/{catalogue-number}-{font-slug}/"
/creative-fabrica-font "outputs/font-preparation/{catalogue-number}-{font-slug}/"
```

The workflow orchestrator must await each command’s agent result before issuing
the next command. The default sequence ends after YellowImages. Etsy and
DaFont/FontSpace remain separate explicit-request commands.

## Agent responsibilities

- Agent 2: Creative Market title, description, tags, and SEO metadata.
- Agent 20: Japanese-first BOOTH title, description, tags, and SEO evidence.
- Agent 23: YellowImages title, description, category, canonical-first tags,
  and evidence. It reuses the eventual approved 3:2 visuals from the final
  `New-Images/main/` delivery set and does not generate or request a dedicated
  image derivative.
- Agent 24: DLsite Japanese-first title, description, work format, selected
  genre(s), recommended keyword block, JPY pricing, promotion plan, and
  evidence.
- Agent 29: Creative Fabrica Fonts title, description, category, exactly 40
  researched tags, live tag/category/PDP evidence, and clearly labelled
  engagement/purchase observations. Its 40-tag block is an internal research
  package, not a claimed Creative Fabrica author limit.
- Agent 8: MasterBundles title, description, keyword fields, and SEO metadata
  when explicitly requested.
- Agent 9: Cubebrush title, description, and keyword coverage when explicitly
  requested.
- Agent 21: Behance project title, Creative Fields, project/image tags,
  description, image order, alt text, CTA, and manual publishing handoff.
- Agent 10: four Pinterest Pin sections using `pinterest_1.png`–`pinterest_4.png`,
  distinct search intents, exact Creative Market product-page links, alt text,
  related topics, boards, and research notes.

- Agent 27: Font Renamer naming decision (final two-word name + one-sentence
  `Supporting-image theme sentence` written to `visual-direction/font-name-report.md`)
  plus per-image theme variants in `visual-direction/theme.txt` — the
  ready-made prompts the seller pastes into each manual image generation
  (kept in the same flat 2D world, palette family, and atmosphere root,
  "same feel, sameish") — followed by the fast `text_placeholder` thumbnail and exactly eight supporting-image copy boards,
  factual specimen sheets, and the explicit provisional handoff.
  The thumbnail contains only the decided font name; promos use thoughtful
  display copy plus restrained supporting microcopy, with roles, wording,
  placements, and scales derived from the specific intended design rather than
  a fixed copy-mode menu. Every promo must record an authored layout rationale;
  the dominant block cannot be tiny, and all text must fit inside the canvas.
  It renders the supplied font with the local font on white canvases and keeps
  provisional status in the handoff documents. The seller may later create
  final raw files in the preparation output's
  `visuals/New-Images/` folder and invoke Agent 30 after the workflow; that
  optional replacement does not block the default chain.
- Agent 13: package, metadata, audit, and video preparation, plus unchanged
  copies of Agent 27's four factual specimen PNGs into the numbered output's
  `specimens/3x2/` and `specimens/1x1/` folders when the validated handoff is
  available. It leaves all creative thumbnail, promo, and Pinterest artwork
  deferred and does not process or compose those images.
- Agent 30: standalone final seller-image processing from
  `outputs/font-preparation/{catalogue-number}-{font-slug}/visuals/New-Images/`, including exact
  ratio-specific source copies, bounded `main/` and `squares/` JPEGs, four
  bounded Pinterest PNGs, and the final-image manifest. It is never invoked by
  `/full-workflow`.

All listing agents may read relevant product documentation for factual copy
input. They must not duplicate package, image, license, upload, or technical QA.
BOOTH, Pixiv, and Creative Fabrica must use
`agents/research-checkpoint-protocol.md` and their product-specific `.research/`
scratch files. Each must record completed request batches, complications, method
limitations, and actual description/caption keyword placement before continuing
or reporting completion.

## Trigger

```text
/all-fonts "Modern handwritten script font with OTF, TTF, WOFF, and WOFF2"
```

Conceptually, the orchestrator performs:

```text
booth_result = await Agent 20
dlsite_result = await Agent 24
yellowimages_result = await Agent 23
```

Never replace this with a parallel batch.

## Optional standalone stages

```text
/cm-font "..."
/mb-font "..."
/cb-font "..."
/pixiv-font "..."
/behance-font "..."
/pinterest-font "..."
/font-final-images "..."
/etsy-font "..."
/freemium-font "..."
```

Run these only when explicitly requested; they are not part of the required
four-marketplace chain.
