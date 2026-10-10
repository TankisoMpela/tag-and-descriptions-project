---
name: full-workflow
description: Strict sequential font launch workflow from visual generation through font preparation, BOOTH, Pixiv, and Creative Fabrica. Marketore, YellowImages, and DLsite are paused.
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
one to it. Pass that same number to BOOTH, Pixiv, and Creative Fabrica; never
let each marketplace choose a different number.

## Required Sequence

Run registered agents strictly one at a time, waiting for a final successful
result before starting the next:

1. `font-image-generator`
2. `font-prep-specialist`
3. `booth-fonts-specialist`
4. `pixiv-fonts-specialist`
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
description, and any supplied facts to
`font-image-generator`. It must inspect the actual font and references, author
independent OpenPencil `.jsx`/`.fig` compositions for each ratio with named
nodes, render prominent lettering as real-font text (not outlined SVG), and
create:

- `prepared_visuals/3x2/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_japanese.png` with Japanese surrounding copy;
- 4-8 sequential `promo_N.png` files in both ratios;
- four factual specimen PNGs;
- ratio-specific OpenPencil `.fig` and `.jsx` source files in
  `prepared_visuals/openpencil/3x2/` and `prepared_visuals/openpencil/1x1/`;
- `openpencil-render-report.json`, `visual-handoff-manifest.md`, and
  `VISUAL-HANDOFF-READY.md`.

Require the exact response marker `READY FOR FONT PREP HANDOFF`, the exact
`prepared_visuals/` path, and the final decision-set name (the user-supplied
spelling, or Agent 27's decided name when the user gave none). Do not start
Agent 13 without all three.

### Continuous font preparation

Invoke `font-prep-specialist` with the exact phrase `FULL WORKFLOW CONTINUOUS
MODE`, the original workspace, the new name, the old description, and the
prepared-visual path from Agent 27. Agent 13 must execute its complete run in
one invocation and must not stop at the metadata/package handoff.

Agent 13 is not allowed to open, visually inspect, OCR, thumbnail, or reason
from image content. It trusts Agent 27's successful visual validator and
manifest, uses the exact canonical filenames, and performs only mechanical
copying, bounded encoding, and requested composition. It must finish the font
package, audit, derivatives, main video, Etsy video, and final reports before
returning.

Require a final preparation output path and a successful completion status.

### Marketplace sequence

Pass the original factual product inputs, final name, preparation output path,
the unified product number, and any prior listing context forward as needed:

1. `booth-fonts-specialist`: paid Japanese-first BOOTH listing and its required
   live-evidence copy output. This agent does not upload.
2. `pixiv-fonts-specialist`: Japanese-first Pixiv post and BOOTH funnel copy
   tags, compatibility, pricing observations, and evidence output.
3. `creative-fabrica-fonts-specialist`: Creative Fabrica Fonts listing and
   40-tag package, category, and evidence output.

Do not ask marketplace agents to inspect packages, images, or technical assets.
They may read relevant local product documentation for factual copy only and
must remain within their own listing scope.

## Completion

Return a compact stage table with each registered agent's final status and
output path. Report the two prepared videos explicitly:

- the main 16:9 showcase at `1920x1080`;
- the Etsy 2:1 showcase at `1920x960` (or the explicitly approved 2:1 size).

Do not claim publication or upload for any stage.
