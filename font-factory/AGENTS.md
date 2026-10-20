# AGENTS.md — Font Preparation and Visual Workspace

This directory stages raw font files, original visual references, Agent-27 art direction and generated visual handoffs, and generated font-preparation packages for `/font-images` and `/font-prep`.

## Role boundary

Before Agent 13 acts, read `../agents/agent-13-font-prep-specialist.md` completely. Before Agent 27 acts, read `../agents/agent-27-font-image-generator.md` and `support-references/TEMPLATE-GUIDE.md`. These files are authoritative for their stages.

Agent 27 is responsible for:
- a compact font-specific `visual-plan.json` for the main 3:2 thumbnail, its
  independently composed 1:1 version, and the separate storefront square;
- three clean white-background font-name specimens and a `theme.txt` containing
  the three complete, font-specific image-generation prompts that use those
  specimens as raw lettering material;
- seven eligible reference-led HTML/CSS supporting
  layouts rendered at both 3:2 and 1:1, and four factual specimen previews in the prepared handoff; support
  artwork does not repeat the font name, and both family-proof layouts are
  guaranteed when at least two real sibling styles are available;
- reading `font-factory/support-references/TEMPLATE-GUIDE.md` and preserving
  each template's visual hierarchy and source artwork while adapting only its
  documented theme and copy fields;
- rendering every active HTML/CSS Pinterest template with the primary font into
  `prepared_visuals/pinterest/`, with a checksum manifest, for Agent 13 to copy;
- a one-pass image-generation rule for genuinely missing cutout/texture assets:
  generate once, check usability once, then move on;
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
- consuming Agent-27's prevalidated 3:2 and 1:1 handoff without inspecting image content, then mechanically encoding creative images (`≤500 KB`);
- installing Agent 27's 23 verified HTML/CSS Pinterest template pins into
  `visuals/New-Images/pinterest/`; Agent 13 does not render Pinterest pins.
- rendering the two factual specimen sheets at both ratios (`bin/render-specimens --class …` into `specimens/{3x2,1x1}/`) — they need the class call, which only Agent 13 makes.

Agent 13 is **not** responsible for:
- generating or researching names;
- designing per-font Skia templates (Agent 27 and the shared renderer own those);
- generating the main thumbnail or supporting images;
- inventing copy for a missing image.

## Input convention

```
font-factory/fonts/{input-slug}/
├── MyFont-Regular.otf
├── MyFont-Bold.otf                 (optional)
├── visual-references/              (optional source material; no old thumbnail is required)
│   └── supporting/                  (original supporting images)
├── visual-direction/               (Agent 27 art direction, plan, and review)
└── prepared_visuals/               (Agent 27 visual handoff)
    ├── 3x2/                        (thumbnail_main.png)
    ├── 1x1/                        (thumbnail_main.png, thumbnail_japanese.png)
    ├── supporting/3x2/             (seven eligible HTML/CSS templates)
    ├── supporting/1x1/             (the same seven square adaptations)
    ├── specimens/{3x2,1x1}/        (four factual specimen previews)
    ├── visual-handoff-manifest.md  (Agent-27 visual QA record)
    └── VISUAL-HANDOFF-READY.md

Agent 27 makes the white-background raw lettering specimen for each final
thumbnail, with a separate full prompt for the 3:2 main, the 1:1 main, and the
storefront square. No old thumbnail is part of this image-generation workflow.
It also creates the Japanese square placeholder,
seven HTML/CSS support designs at 3:2 and 1:1, four specimen previews, and all
23 active HTML/CSS Pinterest pins with the actual font. Agent 13 copies the
checksummed pin set and renders the final factual specimen sheets. Pinterest
pins are not redesigned in Agent 13.

The thumbnail ratios are planned independently. The correct white-background
specimen and its matching prompt are used for each output. A mixed `New-Images`
folder may contain both 3:2 and 1:1 final artwork, but references are not silently
treated as final handoff assets: the selected direction must record the intended
ratio and the image model must create each ratio directly. For support designs, preserve each
3:2 template's code and materials while creating its separately fitted 1:1
adaptation. Never stretch, crop, or white-pad the 3:2 render to make a square.

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
- the 23 HTML/CSS Pinterest pins `pinterest_1..23` under
  `visuals/New-Images/pinterest/`, each at or below `200000` bytes, plus
  `pinterest-template-manifest.json`; Agent 30 later appends ten composites.
- one shared crop-safe marketplace thumbnail under `visuals/platforms/`;
- the four specimen sheets (`specimen-letters.png`, `specimen-numerals.png` at each
  ratio), rendered by Agent 13 into `specimens/3x2/` and `specimens/1x1/`;
- main `1920x1080` text-only font showcase MP4 and dedicated Etsy `1920x960`
  2:1 showcase MP4 plus `etsy-video-script.txt`;
- `visual-source-manifest.md`.

Agent 27 validates the plan, copy, dimensions, naming, crop safety, and
contrast mechanically before handoff; it does not claim that placeholders are
final creative artwork. If its validator reports a missing or failed asset,
stop and report the exact filename. Agent 13 does not inspect image content; it copies Agent 27's checksummed
Pinterest pins and renders final factual specimens. The ten additional composite
panels are made later by Agent 30 from the seller's 3:2 final images. Never derive
a square support template from a 3:2 image, and no long-scroll is created.
