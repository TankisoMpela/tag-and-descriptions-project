---
name: full-workflow
description: Strict sequential font launch workflow from visual generation through font preparation, BOOTH, Creative Market, and Creative Fabrica. Pixiv, Marketore, YellowImages, and DLsite are paused.
---

# Full Font Launch Workflow

This is the explicit end-to-end font workflow. The user supplies these inputs:

- the font workspace directory, such as `font-factory/fonts/my-font/`;
- the final new font name — **supplied by the user only when they give one**;
  when absent, Agent 27 decides the best evocative name from the description
  under its Naming policy (name-uniqueness research and the namemaker agent are
  forbidden; uniqueness does not matter) and returns it in the handoff marker;
- the old product description;
- any additional factual constraints the user wants preserved.

The workflow agent owns orchestration only. It does not write marketplace copy,
design images, package fonts, or inspect image pixels itself.

Before the first delegation, determine one unified product number from the
highest numeric prefix in the existing `outputs/*/*.md` listing files and add
one to it. Pass that same number to BOOTH, Creative Market, and Creative Fabrica; never
let each marketplace choose a different number.

## Required Sequence

Run registered agents strictly one at a time, waiting for a final successful
result before starting the next:

1. `font-image-generator`
2. `font-prep-specialist`
3. `booth-fonts-specialist`
4. `cm-fonts-specialist`
5. `creative-fabrica-fonts-specialist`

Never use a task array, `Promise.all`, background delegation, shell
orchestration, or a second marketplace agent while an earlier stage is running.
If any stage fails, is blocked, or returns without its required output path,
stop immediately and report the blocking stage. Do not infer success from a
partial file.

## Stage Handoffs

### Visual generation

Pass the exact workspace, the new name when the user supplied one (otherwise
the instruction that Agent 27 decides it under its Naming policy), the old
description, and any supplied facts to `font-image-generator`. Agent 27 creates
white-background font-name specimens, complete matching prompts for the 3:2
main, 1:1 main, and storefront square, the documented HTML/CSS support layouts,
factual specimen previews, and active Pinterest template renders. No old
marketplace thumbnail is required. If the user explicitly requests a prompt
prototype, use the matching specimen and prompt with the built-in
image-generation tool and inspect the result. Require:

- `prepared_visuals/3x2/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_japanese.png` with the same name-only
  specimen treatment;
- seven layouts under `prepared_visuals/supporting/3x2/` and the matching seven
  under `prepared_visuals/supporting/1x1/`;
- four previews under `prepared_visuals/specimens/`;
- all 23 active template renders under `prepared_visuals/pinterest/` and their
  template manifest;
- `visual-handoff-manifest.md`, and `VISUAL-HANDOFF-READY.md`.

Require the exact response marker `READY FOR FONT PREP HANDOFF`, the exact
`prepared_visuals/` path, and the final decision-set name (the user-supplied
spelling, or Agent 27's decided name when the user gave none). Do not start
Agent 13 without all three.

### Continuous font preparation

Invoke `font-prep-specialist` with the exact phrase `FULL WORKFLOW CONTINUOUS
MODE`, the original workspace, the new name, and the old description.
Agent 13 must execute its complete run in
one invocation and must not stop at the metadata/package handoff.

Agent 13 is not allowed to open, visually inspect, OCR, thumbnail, or reason
from image content. It does not copy thumbnail or support-layout drafts; it
installs only Agent 27's checksummed Pinterest template pins. Its single pass
packages and audits the font, writes the description, installs those pins, and
renders the factual specimen sheets. It must finish the font package, the
technical audit, the specimen sheets and the final reports before returning.
Agent 13 installs the
23 checksummed Pinterest template pins from Agent 27 with
`bin/install_template_pinterest_pins.py`; it does not create a new Pinterest
brief or render a second pin set. It then renders four factual specimen sheets
at both ratios with `bin/render-specimens --class`. This stage does not inspect
the thumbnail or support-layout images. Showcase video rendering is archived
(`archive/video/README.md`); do not attempt it. The seller's final thumbnail
artwork is generated separately from the matching specimen and prompt, then
processed by `/font-final-images` after it is added to the output folder.

Require a final preparation output path, a successful completion status, the
23 template pins, the four specimen sheets, and an **empty**
`visuals/New-Images/` drop directory left in place for the seller apart from
that `pinterest/` folder.

Agent 13 leaves Agent 27's thumbnail and support-layout drafts in
`font-factory/`, and installs only the checksummed Pinterest pins. The seller
generates the final artwork themselves, drops the raw
files into `visuals/New-Images/`, and runs `/font-final-images` (Agent 30), which
is outside this workflow.

### Marketplace sequence

Pass the original factual product inputs, final name, preparation output path,
the unified product number, and any prior listing context forward as needed:

1. `booth-fonts-specialist`: Japanese-first BOOTH listing and its required
   live-evidence copy output. Default campaign is a limited-time free offer
   (`FREE_ACTIVE`); pass any user-supplied window or free scope with it. This
   agent does not upload. Tag evidence is collected once per product: if a run
   (yours or an interrupted one) already fetched tag counts, freeze them to a
   research file and pass its path — the agent then performs zero count
   fetches. Never re-dispatch without the frozen file after a cancellation.
2. `cm-fonts-specialist`: Creative Market copy-only handoff using one bounded,
   per-font research pass over current Creative Market taxonomy, popular results,
   and representative product pages. Historical local listings are optional
   writing references only. No Firecrawl, Serper, Exa, Tavily, autocomplete, or
   long live-research loop.
3. `creative-fabrica-fonts-specialist`: Creative Fabrica Fonts listing with
   exactly 40 internal handoff tags and evidence for every selected tag. This
   agent does not upload.

Do not ask marketplace agents to inspect packages, images, or technical assets.
They may read relevant local product documentation for factual copy only and
must remain within their own listing scope.

Marketore, YellowImages, DLsite, X, Cubebrush, Etsy, Behance, Pinterest, and
all other marketplace stages are paused and must not be delegated by this
workflow. Do not let this skill's older stage list override the canonical
`agents/agent-28-full-workflow.md` routing contract.

## Completion

Return a compact stage table with each registered agent's final status and
output path.

Do not claim publication or upload for any stage.
