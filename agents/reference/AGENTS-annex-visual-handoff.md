# Bespoke Font Image Handoff (annex of AGENTS.md)

Relocated from AGENTS.md so it is loaded only by the agents that perform the
visual work (font-image-generator, font-final-visual-processor) instead of by
every agent in the project. The rules below are authoritative for the visual handoff and Pinterest asset sequence.

## Who makes what

Agent 27 (`font-image-generator`) runs before Agent 13. It authors one
font-specific plan for the main and storefront thumbnail prompts, selects the
renderer class, and reproducibly selects 13 random eligible HTML/CSS support designs
at both 3:2 and 1:1, plus four factual specimen previews. It reads
`font-factory/support-references/TEMPLATE-GUIDE.md` for each support layout's
specimen copy, caption/alt-text guidance, and theme flexibility. Each square
layout uses the same template code and materials but is fitted independently;
it is not a stretched, cropped, or white-padded landscape render. Supporting
artwork must not repeat the font name. When real sibling styles make family
showcase templates eligible, `plakat32`, `weightfamily32`, `mangosboard32`,
and `italicregular32` are guaranteed in the 13 and use actual font files.
Use Title Case for new or replacement support copy. Intentional all-caps
support copy is limited to `support-23_alphabet32.png`,
`support-25_weightfamily32.png`, `support-44_neue32.png`, and
`support-141_practicehard32.png`.
Agent 27 renders three clean, white-background
font-name specimens as raw lettering material and writes complete prompts for
the 3:2 main, 1:1 main, and storefront square. Those are the only image-model
placeholders. No old thumbnail is needed or used. An essential missing cutout
or texture for a support template may use one ImageGen pass when authorized;
check it once and move on, without iterating. Agent 27 never modifies font
binaries or claims an upload.

When the user does not supply a final font name, Agent 27 decides the best
concept-led name from the description under the Naming policy in the canonical
Agent-27 spec. External name-uniqueness research and the archived namemaker
agent are outside this workflow; treat reference names as pattern evidence and
never copy them or close variants.

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

## Full workflow and follow-up stages

Codex `/full-workflow` starts from one user-selected folder in
`font-factory/Saved/`. The staging helper moves its original root-level
OTF/TTF files into `font-factory/fonts/{input-slug}/`; those source files
remain there for future completed-work checks. Agent 27 writes its review
handoff under that same input-slug folder. Agent 13 writes new package and
preparation artifacts to `outputs/font-preparation/{NUM}-{slug}/`. The
orchestrator then runs BOOTH, Creative Market, and Creative Fabrica in order.
Each Codex child must finish successfully before the next begins.

Final thumbnail generation and the image drop are seller follow-up work. Pair
each white-background specimen with its complete prompt from
`font-factory/fonts/{input-slug}/visual-direction/theme.txt`. Generate the 3:2
and square main images independently, then place both in the preparation
directory named by Agent 13, along with at least two additional 3:2 images for
Pinterest composites.

Agent 30 waits for the named thumbnail pair and minimum 3:2 image pool, then
classifies the raw 3:2 and 1:1 files, preserves exact source copies, writes
full-dimension delivery JPEGs into `main/` and `squares/` targeting 200 KB
with a 300 KB ceiling, and adds ten image-composite Pinterest panels after the
template pins. It preserves every pin installed by Agent 13 and writes the
full-set manifest. Agent 30 and the Pinterest preparer are separate from
`/full-workflow`; Pinterest preparation uploads the manifested set only when
invoked as its own stage.
