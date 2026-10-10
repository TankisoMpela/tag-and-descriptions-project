# Font Factory Input Staging Workspace 🎨

`font-factory/` is the input workspace for raw font files and the **user-approved visual handoff** used by the second pass of the FontFairy Font Preparation & Metadata Specialist (`agent-13-font-prep-specialist` / `/font-prep`).

## 📁 Directory Structure & Input Conventions

Create one folder per font using a short slug (lowercase, hyphens):

```
font-factory/
├── fonts/
│   └── {font-slug}/                    ← Staging folder for one font
│       ├── MyFont-Regular.otf          ← Raw .otf / .ttf font files
│       ├── MyFont-Bold.otf             (optional additional weights)
│       │   ├── prepared_visuals/           ← approved normal 3:2 images
│       │   │   ├── thumbnail_main.png      ← approved 3:2 main image
│       │   │   └── promo_1.png, promo_2.png... ← approved 3:2 supporting images
│       └── old_references/             ← optional archive for the image workflow
├── Style-References/                   ← optional quality references for the Custom GPT
└── README.md                           ← This workspace guide
```

## 🚀 Quick Start Instructions

1. **Create the font workspace**:
   ```bash
   mkdir -p font-factory/fonts/{font-slug}/prepared_visuals
   ```
2. **Place the raw font file(s)** (`.otf` / `.ttf`) in `font-factory/fonts/{font-slug}/`.
3. **Run Agent 13 metadata/package pass first**:
   > "Please run font-prep for font-factory/fonts/{font-slug}/, final name: [name], description: [description]."
4. While Agent 13 stops at `READY FOR VISUAL HANDOFF`, use the FontFairy Font Image Director Custom GPT:
   - provide the seed and old thumbnail to create `thumbnail_main.png`;
   - provide each old supporting image one at a time to create `promo_N.png`;
   - optionally create `thumbnail_pinterest.png` (2:3, normally 1000x1500).
5. Save the approved 3:2 files and any optional Pinterest file in `prepared_visuals/` using those exact filenames.
6. **Resume Agent 13 visual processing**:
   > "Continue visual handoff for [name]; prepared visuals: font-factory/fonts/{font-slug}/prepared_visuals/"

Agent 13 does not generate creative images. It validates the 3:2 handoff, makes centered square derivatives, mechanically stacks the copied 3:2 images with `bin/compose_pinterest.py` when Pinterest was not supplied, and compresses squares to `≤500 KB` plus Pinterest to `≤700 KB`.

## 📦 Generated Outputs (`outputs/font-preparation/{font-slug}/`)

Agent 13 writes technical packages, metadata, and mechanical derivatives directly to:

```
outputs/font-preparation/{font-slug}/
├── name-report.md                  ← User-provided name and slug lock
├── audit-report.md                 ← Fontspector + fontTools QA & metadata audit log
├── pro/                            ← Full commercial package
├── freemium/                       ← Optional demo package
├── thumbnail_main.png              ← Copied approved 3:2 image (not compressed)
├── thumbnail_square.png            ← Mechanical 1:1 derivative (≤500 KB)
├── promo_1.png, promo_2.png...     ← Copied approved 3:2 supporting images (not compressed)
├── promo_1_square.png, ...         ← Mechanical 1:1 derivatives (≤500 KB)
├── thumbnail_pinterest.png         ← Copied or mechanically composed Pinterest image (≤700 KB)
└── visual-source-manifest.md       ← Handoff, derivative, and compression QA
```
