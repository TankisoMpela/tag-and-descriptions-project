# AGENTS.md — Font Preparation and Visual Workspace

This directory stages raw font files, original visual references, Agent-27 art direction and generated visual handoffs, and generated font-preparation packages for `/font-images` and `/font-prep`.

## Role boundary

Before Agent 13 acts, read `../agents/agent-13-font-prep-specialist.md` completely. Before Agent 27 acts, read `../agents/agent-27-font-image-generator.md` and both dedicated visual skills. Each file is authoritative for its own stage.

Agent 27 is responsible for:
- font-specific visual art direction and, only when useful, candidate review;
- a phrase-led `theme.txt`, `visual-plan.json`, and readable image notes for
  later manual image-model replacement;
- a fast mechanical text-placeholder handoff in both required ratios;
- ratio-specific 3:2 and 1:1 creative briefs; the placeholder renderer is
  mechanical and must not choose a template or invent a fallback composition;
- font-appropriate backgrounds, texture, effects, contrast, purposeful copy,
  and crop-safe layout;
- selecting concrete buyer-use contexts only when the font's supported use
  cases make them appropriate, while allowing construction or glyph proof when
  that is the stronger evidence;
- the two factual font specimen families previously owned by Agent 13;
- `VISUAL-HANDOFF-READY.md` and the explicit Agent-13 handoff message.

Agent 13 is responsible for:
- fontTools, Fontspector, and OpenType Sanitizer QA;
- user-supplied font name metadata and OpenType Name IDs;
- OTF, TTF, WOFF, and WOFF2 packaging in a folder named after the font;
- `{Font-Name}-Commercial-Use.zip` and `{Font-Name}-Personal-Use.zip`
  (both clean; Personal-Use may add a like-request note) plus
  `{Font-Name}-Free-Trial-Demo.zip` (FontFairy demo stamp on digits +
  ASCII punctuation);
- optional Freemium demo subsetting when explicitly requested;
- marketplace description at the preparation output root and audit reports;
- consuming Agent-27's prevalidated 3:2, 1:1, and specimen handoff without inspecting image content, then mechanically encoding creative images (`≤500 KB`);
- mechanically composing four Pinterest outputs (`≤700 KB`) from the supplied 3:2 images.

Agent 13 is **not** responsible for:
- generating or researching names;
- creating, redesigning, or repairing creative images;
- generating the main thumbnail or supporting promos;
- inventing copy for a missing image.

## Input convention

```
font-factory/fonts/{input-slug}/
├── MyFont-Regular.otf
├── MyFont-Bold.otf                 (optional)
├── visual-references/              (original images for Agent 27 to study)
│   ├── thumbnail_reference.png
│   └── supporting/                  (original supporting images)
├── visual-direction/               (Agent 27 art direction, plan, and review)
└── prepared_visuals/               (Agent 27 visual handoff)
    ├── specimens/                  (two factual specimen families per ratio)
    ├── 3x2/                        (thumbnail_main.png, promo_N.png)
    ├── 1x1/                        (thumbnail_main.png, thumbnail_japanese.png, promo_N.png)
    ├── visual-handoff-manifest.md  (Agent-27 visual QA record)
    └── VISUAL-HANDOFF-READY.md

Agent 27 creates both thumbnail ratios, both supporting-image ratios, and the four factual specimen outputs. If the optional Pinterest image is absent, Agent 13 may mechanically compose four Pinterest variants from the completed 3:2 images; it does not generate replacement artwork.

The two ratios are planned independently. A mixed `New-Images` folder may
contain both 3:2 and 1:1 references, but references are not silently treated as
final handoff assets: the selected direction must record the intended ratio and
the agent must create each ratio directly. Do not retrofit a single generic
template or master composition across the ratios.

## Output convention

Agent 13 writes to `outputs/font-preparation/{new-slug}/`:

- `description.txt` at the preparation output root as an internal listing reference; it must never be packaged;
- a `{Font-Name}/` folder containing only OTF, TTF, WOFF, and WOFF2 font binaries; the folder must never be named `pro`;
- `{Font-Name}-Commercial-Use.zip` and `{Font-Name}-Personal-Use.zip`
  (both clean; Personal-Use may add an optional like note) plus
  `{Font-Name}-Free-Trial-Demo.zip` (demo-stamped digits/punctuation),
  each containing that font folder only;
- exact source copies under `visuals/source/3x2/` and `visuals/source/1x1/`;
- full-dimension JPEG delivery copies under `visuals/main/` and `visuals/squares/`, each compressed to `≤500 KB`;
- four mechanically composed Pinterest images under `visuals/pinterest/`, each kept at `≤700 KB`;
- one shared crop-safe marketplace thumbnail under `visuals/platforms/`;
- four Agent-27 factual specimen PNGs copied into the corresponding source and
  delivery folders;
- main `1920x1080` text-only font showcase MP4 and dedicated Etsy `1920x960`
  2:1 showcase MP4 plus `etsy-video-script.txt`;
- `visual-source-manifest.md`.

Agent 27 validates the plan, copy, dimensions, naming, crop safety, and
contrast mechanically before handoff; it does not claim that placeholders are
final creative artwork. If its validator reports a missing or failed asset,
stop and report the exact filename. Agent 13 does not reopen images. A missing
Pinterest image is not a blocker; compose it from the valid copied 3:2 images.
Never derive a square from a 3:2 image, and no long-scroll is created.
