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
    ├── supporting/                    12 shared HTML/CSS layouts at both ratios
    └── pinterest/                     active template pins and manifest
```

## Workflow

1. Stage the source font file(s) in `font-factory/fonts/{font-slug}/`.
2. Run `/font-images` with the font workspace, final name if already chosen,
   and the product description.
3. Agent 27 produces two clean white-background name lettering references with the actual font
   and writes four complete, font-specific prompts: a primary and a distinctly
   different alternate direction, each composed separately for landscape 3:2
   and square 1:1. The matching prompts appear in `theme.txt` under
   `thumbnail_main_3x2`, `thumbnail_main_1x1`, `thumbnail_alt_3x2`, and
   `thumbnail_alt_1x1`. Use one direction consistently for the thumbnail pair.
4. To make final thumbnail artwork, attach the matching specimen and use its
   prompt with the image model. Do not supply an old marketplace thumbnail.
   Review spelling, letterform fidelity, crop, contrast, readability, and
   whether the finished image follows the prompt.
5. Run `/font-prep` for packaging and the preparation handoff. Final approved
   images are processed by `/font-final-images` after they are placed in the
   preparation folder named in the handoff.

The two thumbnail specimens are raw lettering references, not finished
designs. Agent 27 renders 12 support layouts at both ratios and the active
Pinterest template pins. It no longer makes factual specimen sheets; Agent 13
creates those during preparation. See `AGENTS.md` for the handoff paths.
