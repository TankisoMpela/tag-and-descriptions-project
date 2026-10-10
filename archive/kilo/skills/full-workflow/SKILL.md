---
name: full-workflow
description: Strict sequential font launch workflow from provisional visual handoff through font preparation, BOOTH, Pixiv, and Creative Fabrica. X, DLsite, and YellowImages are paused.
---

# Full Font Launch Workflow

This is the explicit end-to-end font workflow. The user supplies the required
inputs and may add an optional campaign brief:

- the font workspace directory, such as `font-factory/fonts/my-font/`;
- the old product description **or** a public product URL whose page contains
  the product description (exactly one of the two is required);
- any additional factual constraints the user wants preserved (may include an
  old name for the naming verdict);
- optional campaign facts. Every new-font launch creates the paid Commercial Use
  package plus a separate Free Trial Demo package when supplied. The Demo is a
  reduced non-commercial evaluation build, not Personal Use. Carry its exact
  scope and BOOTH like request into BOOTH, Pixiv, and X. Use an explicit
  campaign state only when the user explicitly passes `CAMPAIGN_MODE` plus the
  exact free scope, start/end or unlock condition, Commercial Use state, and
  target metrics. Preserve supplied start/end or unlock condition, Commercial
  Use state, target metrics, and public BOOTH/X URLs.

Agent 27 owns the font-name decision and the `Supporting-image theme sentence`
(Font Renamer contract): both are outputs of stage 1, decided from the
description or product URL. The user no longer supplies a name or pastes a
theme sentence.

The workflow agent owns orchestration only. It does not write marketplace copy,
design images, package fonts, or inspect image pixels itself.

Before the first delegation, determine one unified product number from the
highest numeric prefix in the existing `outputs/*/*.md` listing files and add
one to it. Pass that same number to BOOTH, Pixiv, and Creative Fabrica; never let each marketplace choose a different
number.

If no campaign mode is supplied for a new font, use the paid-only `NORMAL_PAID`
default above. When a campaign mode is supplied, carry it and its facts
unchanged through the BOOTH, Pixiv, and X handoffs. Do not invent a free scope,
deadline, repost target, milestone, or measurement result.

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
If any stage fails or returns without its required output path, stop immediately
and report the blocking stage. The BOOTH stage may use the documented
evidence-limited fallback for any defensible below-target tag count when its
validator passes; do not infer success from a partial file.

## Stage Handoffs

### Visual generation

Pass the exact workspace, the product description or product URL, and any
supplied facts to `font-image-generator`. Agent 27 first runs the Font Renamer
naming contract — it decides the final two-word font name, authors the
one-sentence `Supporting-image theme sentence`, authors per-image theme
variants in `visual-direction/theme.txt`, and writes
`visual-direction/font-name-report.md` — then creates a fast `text_placeholder`
handoff: a name-only thumbnail plus eight white supporting boards with
font-specific, deliberately differentiated copy and restrained microcopy, plus
factual specimen sheets. The theme sentence is authored by Agent 27 and must be
carried verbatim as `supporting_image_theme`, and each image's one-line
`theme_variant` must be identical in the plan and in `theme.txt`; no pasted
theme is required from the user. The copy ideas and roles are authored per
font; no fixed phrase list or copy-mode menu is imposed.
It does not use reference images, OpenPencil, or image-generation tools.
Require it to create:

- `visual-direction/theme.txt` with exactly ten `##` sections
  (`thumbnail_main`, `thumbnail_japanese`, `promo_1` … `promo_8`), each opening
  with that image's one-line `theme_variant` plus a few lines keeping the
  theme sentence's flat 2D world, palette family, and atmosphere root while
  tailoring the art language, motif, texture, and colour emphasis to that
  board's authored lettering and layout ("same feel, sameish");
- `prepared_visuals/3x2/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_main.png`;
- `prepared_visuals/1x1/thumbnail_japanese.png` with the same name-only thumbnail treatment;
- exactly 8 sequential `promo_N.png` files in both ratios;
- four factual specimen PNGs;
- `visual-handoff-manifest.md` with `status: provisional` and
  `render_mode: text_placeholder`;
- `VISUAL-HANDOFF-READY.md` with a successful mechanical validator result and
  `Visual status: PROVISIONAL — MANUAL IMAGE REPLACEMENT REQUIRED`.

Require the exact response marker `READY FOR FONT PREP HANDOFF`, the decided
font name, the exact authored theme sentence, the exact `theme.txt` path, and
the exact `prepared_visuals/` path. Capture the decided name, theme sentence,
and theme-variants path and carry them into every later handoff; do not
re-decide them downstream. The theme variants are the ready-made prompts the
seller pastes into the manual image pass — keep the `theme.txt` path handy for
the final report.
The provisional status is not a failure and must not
stop Agent 13 or any later marketplace stage. Stop only for missing inputs,
missing files, or a failed mechanical validator.

### Continuous font preparation

Invoke `font-prep-specialist` with the exact phrase `FULL WORKFLOW CONTINUOUS
MODE`, the original workspace, the decided name from Agent 27, the old
description, the exact Agent-27 theme sentence, and the
prepared-visual path from Agent 27. Agent 13 must execute its complete
font/package/video run in one invocation, copy the four factual specimen PNGs
unchanged into the numbered preparation output's `specimens/` folders, and
must not stop at an intermediate metadata/package handoff.

Agent 13 is not allowed to open, visually inspect, OCR, thumbnail, or reason
from image content. It may record that Agent 27's creative handoff is
provisional, but it may copy only the four named factual specimen PNGs
unchanged; it must not copy, compress, rename, derive, or compose any
thumbnail, supporting promo, or Pinterest asset. It must finish the font
package, technical audit, main video, Etsy video, specimen-copy manifest, and
final reports before returning.

Require a final preparation output path and a successful completion status.

### Marketplace sequence

Pass the original factual product inputs, the decided final name, the exact
Agent-27 theme sentence, preparation output path,
the unified product number, the unchanged campaign mode/facts, and any prior
listing context forward as needed:

1. `booth-fonts-specialist`: permanent paid Japanese-first BOOTH listing and,
   only when campaign mode is explicit, a complete campaign/free-trial state
   with its own product title, Personal Use title, description, and tags. The
   active campaign may use free terms only when the supplied offer matches and
   must keep paid Commercial Use separate. This agent does not upload.
2. `pixiv-fonts-specialist`: one Japanese-first Illustration post package with
   exactly 10 consolidated tags and one description, using the completed BOOTH
   listing's facts and the frozen `outputs/research/pixiv-font-tag-bank.md`
   snapshot. If campaign mode is active, the title/caption must be aggressive
   and front-loaded: free headline + limited-time deadline/trigger when
   supplied + a direct pre-download BOOTH-item like ask. The paste-ready `Tags:` block must contain one
   plain tag per line
   (never a comma-separated line). The public item URL is optional during the
   workflow; use `LINK REQUIRED` when it is not yet available. Ordinary runs
   make no fresh Pixiv research requests. If campaign mode is active, use the
   campaign copy state, exact free scope, trigger/deadline, and BOOTH CTA
   without implying that Commercial Use is free. This agent does not upload or
   publish.
3. `creative-fabrica-fonts-specialist`: Creative Fabrica Fonts category
   listing, exact 40-tag research package, live category/tag/PDP evidence, and
   visible engagement/purchase observations clearly separated from demand or
   sales claims. This agent does not upload or publish.

Do not ask marketplace agents to inspect packages, images, or technical assets.
They may read relevant local product documentation for factual copy only and
must remain within their own listing scope.
Agents 20, 22, and 29 must also use the shared product research checkpoint
protocol, append findings after every request batch, stop at their finite
platform budget, and report complications/method audit/description SEO audit in
their research notes. Do not treat a partial listing or a conversation-only
research result as a completed stage.

## Completion

Return a compact eight-stage table with each registered agent's final status and
output path. Report the two prepared videos explicitly:

- the main 16:9 showcase at `1920x1080`;
- the Etsy 2:1 showcase at `1920x960` (or the explicitly approved 2:1 size).

Report `PROVISIONAL — MANUAL IMAGE REPLACEMENT REQUIRED` when that marker is
present. The seller may later place raw final PNGs in
`outputs/font-preparation/{slug}/visuals/New-Images/` and invoke the standalone
`/font-final-images` processor. That step is outside this sequential run and is
never delegated here. If campaign mode was explicit, report that both copy
states were produced and which state was marked active. Do not claim campaign
activation, publication, or upload for any stage.
