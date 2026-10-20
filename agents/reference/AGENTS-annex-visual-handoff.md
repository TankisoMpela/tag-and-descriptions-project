# Bespoke Font Image Handoff (annex of AGENTS.md)

Relocated from AGENTS.md so it is loaded only by the agents that perform the
visual work (font-image-generator, font-final-visual-processor) instead of by
every agent in the project. The rules below are authoritative for the visual handoff and Pinterest asset sequence.

## Who makes what

Agent 27 (`font-image-generator`) runs before Agent 13. It authors one
font-specific plan for the main and storefront thumbnail prompts, selects the
renderer class, and runs seven eligible HTML/CSS supporting layouts at both
3:2 and 1:1, plus four factual specimen previews. It reads
`font-factory/support-references/TEMPLATE-GUIDE.md` for each support layout's
specimen copy, caption/alt-text guidance, and theme flexibility. Each square
layout uses the same template code and materials but is fitted independently;
it is not a stretched, cropped, or white-padded landscape render. Supporting
artwork must not repeat the font name. When a real family has at least two
distinct sibling styles, both family-proof templates are guaranteed in the
seven and use actual font files. Agent 27 renders three clean, white-background
font-name specimens as raw lettering material and writes complete prompts for
the 3:2 main, 1:1 main, and storefront square. Those are the only image-model
placeholders. No old thumbnail is needed or used. An essential missing cutout
or texture for a support template may use one ImageGen pass when authorized;
check it once and move on, without iterating. Agent 27 never modifies font
binaries or claims an upload.

When the user does not supply a final font name, Agent 27 decides the best
evocative name from the description under its Naming policy; name-uniqueness
research and the namemaker agent are forbidden (uniqueness does not matter).

Agent 27 also renders all 23 active HTML/CSS Pinterest templates with the
primary font into `prepared_visuals/pinterest/`. It omits the retired
`green_starburst` and `phrase` templates and records each ordered image, font
hash, size, and checksum in `pinterest-template-manifest.json`.

The thumbnail, support, and specimen PNGs in Agent 27's `prepared_visuals/`
stay in `font-factory/` as review drafts and are **not copied into `outputs/`**.
Agent 13 copies only the verified Pinterest JPEGs and manifest into the font's
preparation folder. The seller reviews the other designs and requests any
adjustments.

The seller creates final thumbnail artwork outside the pipeline by pairing each
white-background specimen with its corresponding complete prompt in
`visual-direction/theme.txt`. The specimen is the lettering source; the prompt
is the art direction. Supporting designs are produced by the shared HTML/CSS
catalogue and reviewed as a set.

## Required order

1. `/font-images` → three complete thumbnail prompts plus white-background
   lettering specimens, seven reference-led HTML/CSS support
   layouts rendered at 3:2 and 1:1, four factual specimen previews, and all 23
   active HTML/CSS Pinterest pins rendered with the font. Only thumbnail
   placeholders await image-model replacement.
2. `/font-prep` → the single preparation pass: metadata, package, specimen
   sheets, and checked installation of the 23 Agent-27 pins into
   `outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/pinterest/`. Other
   thumbnail/support drafts remain in the font workspace. Agent 13 renders
   only the final factual specimen sheets from the font binary.
3. **Seller step (manual):** for each output, attach the matching white-background
   font-name specimen and use its complete prompt from
   `font-factory/fonts/{slug}/visual-direction/theme.txt` with an image model.
   Generate the 3:2 and 1:1 main images independently, inspect name spelling,
   letterform fidelity, legibility, contrast, crop, and prompt fidelity, then
   drop the approved raw files into
   `outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/`.
4. `/font-final-images` (Agent 30) → classifies the raw 3:2 and 1:1 files,
   preserves exact source copies, writes full-dimension delivery JPEGs into
   `main/` and `squares/`, and adds ten image-composite Pinterest panels after
   the template pins at the next contiguous indexes. It preserves every pin
   installed by Agent 13 and writes the full-set manifest. This agent is
   deliberately outside `/full-workflow`.
5. `/pinterest-prepare` → validates and uploads every pin listed in the
   manifest, then writes all resulting public image links to `public-urls.md`.

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
