# Font Factory Workspace

`font-factory/` stages font files, visual direction, draft assets, and the
Agent-27 handoff consumed by font preparation. The current role instructions are
in `../agents/agent-27-font-image-generator.md` and `AGENTS.md`.

## Font workspace

```text
font-factory/fonts/{font-slug}/
├── Font-Name.otf or .ttf
├── visual-references/                 optional source material; no old thumbnail needed
├── visual-direction/
│   ├── visual-plan.json               single source for the visual handoff
│   ├── theme.txt                      complete prompts for each thumbnail ratio
│   └── candidate-review.md
└── prepared_visuals/
    ├── 3x2/thumbnail_main.png         white-background font-name specimen
    ├── 1x1/thumbnail_main.png         white-background font-name specimen
    ├── 1x1/thumbnail_japanese.png     white-background font-name specimen
    ├── supporting/                    shared HTML/CSS template renders
    ├── specimens/                     factual font specimen previews
    └── pinterest/                     active template pins and manifest
```

## Workflow

1. Stage the source font file(s) in `font-factory/fonts/{font-slug}/`.
2. Run `/font-images` with the font workspace, final name if already chosen,
   and the product description.
3. Agent 27 produces clean white-background name specimens with the actual font
   and writes three complete, font-specific prompts: the landscape 3:2 main
   image, an independently composed square main image, and the storefront
   square. Each prompt is paired with the matching specimen in `theme.txt`
   under `thumbnail_main_3x2`, `thumbnail_main_1x1`, or
   `thumbnail_japanese_1x1`.
4. To make final thumbnail artwork, attach the matching specimen and use its
   prompt with the image model. Do not supply an old marketplace thumbnail.
   Review spelling, letterform fidelity, crop, contrast, readability, and
   whether the finished image follows the prompt.
5. Run `/font-prep` for packaging and the preparation handoff. Final approved
   images are processed by `/font-final-images` after they are placed in the
   preparation folder named in the handoff.

The thumbnail specimens are raw lettering references, not finished designs.
Supporting layouts and factual specimens are separate review drafts. Agent 27
also renders the active Pinterest template pins; see `AGENTS.md` for the
complete handoff boundaries and paths.
