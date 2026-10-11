# Bespoke Font Image Handoff (annex of AGENTS.md)

Relocated from AGENTS.md so it is loaded only by the agents that perform the
visual work (font-image-generator, font-final-visual-processor) instead of by
every agent in the project. The rules below are unchanged and remain authoritative.

## Who makes what

Agent 27 (`font-image-generator`) runs before Agent 13. It derives the visual
concept, copy, background, contrast, effects, and ratio-specific layouts from the
specific font. It authors a cohesive phrase/concept ledger, `theme.txt`,
`visual-plan.json`, and image notes, then creates a fast mechanical
text-placeholder handoff and the two factual specimen families. It reviews the
handoff with deterministic machine QA only (the agent has no vision or OCR tool
and never inspects rendered PNGs), and never claims placeholders are final
artwork. It never modifies font binaries or claims an upload; vision is never
used and is never a dependency.

When the user does not supply a final font name, Agent 27 decides the best
evocative name from the description under its Naming policy; name-uniqueness
research and the namemaker agent are forbidden (uniqueness does not matter).

**Agent 27's output is a draft.** Its `prepared_visuals/` (3x2 and 1x1
thumbnails, promos, Pinterest) has NOT been through the seller's manual
image-model step. It stays in `font-factory/fonts/{slug}/prepared_visuals/` and
is **never copied into `outputs/`**.

The seller creates the final artwork themselves, outside the pipeline.

## Required order

1. `/font-images` → phrase-led creative briefs, supporting placeholders, and four
   factual specimen PNGs under `prepared_visuals/specimens/{3x2,1x1}/`.
2. `/font-prep` → the single preparation pass: metadata, package, the
   specimens, the five designed Pinterest pins, and an **empty**
   `outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/` drop directory
   apart from `New-Images/pinterest/`. Agent 13 copies ONLY the four factual
   specimen PNGs out of `prepared_visuals/specimens/`; it copies no creative
   thumbnail or promo, and composes or compresses nothing from the seller's
   artwork. The five pins are drawn from the font binary by `bin/render-pins`
   from a `pins.brief.json` it writes itself (`docs/PIN-ART-DIRECTION.md`).
3. **Seller step (manual):** generate the final images with the image model and
   drop the raw files directly into
   `outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/`.
4. `/font-final-images` (Agent 30) → classifies the raw 3:2 and 1:1 files,
   preserves exact source copies, writes full-dimension delivery JPEGs into
   `main/` and `squares/`, and writes `New-Images/final-image-manifest.md`. It
   leaves `New-Images/pinterest/` alone — those are Agent 13's designed pins.
   This agent is deliberately outside `/full-workflow`.

## Running it

Run `/font-images` first with the raw font files, final name, description, and
font workspace. Wait for `READY FOR FONT PREP HANDOFF`. Then run `/font-prep` for
the preparation pass; it ends at `READY FOR FINAL IMAGES` and names the drop
directory. Generate your images, drop them in, then run `/font-final-images`.

For a single uninterrupted launch, use `/full-workflow` with the exact font
workspace directory, new name, and old description. It runs Agent 27, Agent 13,
then BOOTH, Pixiv, and Creative Fabrica sequentially. Agent 13 does not inspect
image content in this mode; it also creates the main `1920x1080` showcase and the
2:1 `1920x960` promo video plus its script. Final images remain the seller's
manual step after the workflow returns.
