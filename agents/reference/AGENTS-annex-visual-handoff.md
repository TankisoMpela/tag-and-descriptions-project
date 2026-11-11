# Bespoke Font Image Handoff (annex of AGENTS.md)

Relocated from AGENTS.md so it is loaded only by the agents that perform the
visual work (font-image-generator, font-final-visual-processor) instead of by
every agent in the project. The rules below are authoritative for the visual handoff and Pinterest asset sequence.

## Who makes what

Agent 27 (`font-image-generator`) runs before Agent 13. It authors one
font-specific plan with primary and alternate thumbnail directions, each
composed for both ratios, selects the
renderer class, and selects 12 eligible HTML/CSS support designs at both 3:2
and 1:1. It prioritizes least-used designs from earlier non-archived handoffs
in the same renderer class, with font-name-seeded random tie-breaking. Factual
specimen previews are retired from Agent 27;
Agent 13 renders the canonical factual sheets from the font. Agent 27 reads
`font-factory/support-references/TEMPLATE-GUIDE.md` for each support layout's
specimen copy, caption/alt-text guidance, and theme flexibility. Each square
layout uses the same template code and materials but is fitted independently;
it is not a stretched, cropped, or white-padded landscape render. Supporting
artwork must not repeat the font name. When real sibling styles make family
showcase templates eligible, `weightfamily32`, `mangosboard32`, and
`italicregular32` join the selection pool; none is guaranteed. Any selected
family showcases use actual font files.
Use Title Case for new or replacement support copy. Intentional all-caps
support copy is limited to `support-23_alphabet32.png`,
`support-25_weightfamily32.png`, `support-44_neue32.png`, and
`support-141_practicehard32.png`.
Agent 27 renders two clean, white-background
font-name specimens as raw lettering material and writes four complete prompts:
a primary and a distinctly different alternate direction, each with a 3:2 and
1:1 composition. It then uses the built-in image-generation tool on each exact
prompt with its matching specimen, producing the main and alternate thumbnails
at both ratios. Save them in `prepared_visuals/final-thumbnails/` as
`thumbnail_main_3x2.png`, `thumbnail_main_1x1.png`, `thumbnail_alt_3x2.png`,
and `thumbnail_alt_1x1.png`. Inspect the four images, make at most one targeted
retry per visibly failed image, and include their dimensions in the handoff
manifest. Those two specimens are the only thumbnail image-model references.
No storefront square or old thumbnail is needed. Agent 27 never modifies font
binaries or claims an upload.

When the user does not supply a final font name, Agent 27 decides the best
concept-led name from the description under the Naming policy in the canonical
Agent-27 spec. External name-uniqueness research and the archived namemaker
agent are outside this workflow; treat reference names as pattern evidence and
never copy them or close variants.

Pinterest template pins are retired. Agent 27 does not render a Pinterest
template folder or manifest. Agent 30 later composes ten panels from the
prepared 3:2 image pool.

The two white-background lettering specimens remain in `font-factory/` as
image-generation references. Agent 13 copies the four generated thumbnails and
all 24 support renders into
`outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/`, preserving their
source files. The thumbnail prompts remain in `visual-direction/theme.txt` and
each generated image is paired with its matching prompt and specimen.

The font name must be a large visual event in both thumbnail ratios: its
longest line spans at least 75% of the full frame width, and its visible glyph
block spans at least 35% of the frame height. Reflow the name or simplify/move
the background if needed; do not shrink the type to make room for scene detail.

The exact style descriptor is secondary visible copy in all four thumbnail
prompts. Specify its treatment as clean, neutral sans-serif typesetting in a
plain grotesk or humanist sans at regular or medium weight. Keep it visually
distinct from the featured display face; do not use the font under sale for
the descriptor, and do not leave the descriptor's font style for the image
model to invent.

## Full workflow and follow-up stages

Codex `/full-workflow` uses an exact source supplied by the user; if none is
supplied, Agent 27 randomly selects one eligible folder in
`font-factory/Saved/` with `python3 bin/stage_saved_font.py --random`. The
staging helper moves only its root-level OTF/TTF files into
`font-factory/fonts/{input-slug}/`; those source files remain there for future
completed-work checks. Agent 27 reviews the full mapped-glyph atlas before
recording a factual description and observed vibe in the visual plan. It writes
its review handoff under that same input-slug folder. Agent 13 writes new package and
preparation artifacts to `outputs/font-preparation/{NUM}-{slug}/`. The
orchestrator then runs BOOTH, Creative Market, and Creative Fabrica in order.
Each Codex child must finish successfully before the next begins.

Agent 27 generates the primary and alternate thumbnails before Agent 13
preparation. Agent 13 installs all four thumbnails plus its 24 support renders
into the preparation directory. After BOOTH, Creative Market, and Creative
Fabrica succeed, the full-workflow orchestrator runs Agent 30 when the
mechanical readiness check passes. If either named thumbnail pair or the
minimum 3:2 pool is missing or invalid, stop the image stage and report the
specific blocker. The 3:2 images form the Pinterest composite pool; the square
images are delivered as square thumbnails and promos.

Agent 30 uses both named thumbnail pairs and prepared images, then classifies
the raw 3:2 and 1:1 files, preserves exact source copies, writes full-dimension
delivery JPEGs into `main/` and `squares/` targeting 200 KB with a default
300 KB ceiling that may be raised at the user's request. Each ratio folder
retains `thumbnail_main.jpg` and `thumbnail_alt.jpg`; the alternate 3:2 image
is available among the Pinterest supporting images. Agent 30 adds ten
image-composite Pinterest panels from the prepared image pool and writes the
full-set manifest. Agent 30 is stage 6 of `/full-workflow` and remains
standalone for a previously prepared product. Pinterest preparation is still
separate and uploads the manifested set only when invoked as its own stage.
