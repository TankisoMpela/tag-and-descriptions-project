---
name: font-workflow
description: End-to-end multi-marketplace font preparation with a metadata-first handoff, approved 3:2 visual processing, automatic Pinterest composition when needed, square derivatives, and listing optimization. Unifies the user-run Custom GPT image workflow, Font Preparation & Metadata (Agent 13 / Codex CLI), Creative Market (Agent 2), MasterBundles (Agent 8), Cubebrush (Agent 9), Pinterest (Agent 10), and DaFont/FontSpace (Agent 11).
---

# Unified Font Preparation, Approved Visual Handoff & Marketplace Pipeline

This skill orchestrates the complete font lifecycle in two passes: Agent 13 finishes metadata and packages first, then stops while the user prepares approved 3:2 images; the user resumes Agent 13 with the exact image directory for visual validation, square derivatives, and automatic Pinterest composition when `thumbnail_pinterest.png` is absent. Creative images are created outside this skill in the FontFairy Font Image Director Custom GPT. Agent 13 never generates creative art; it copies a supplied Pinterest image or mechanically stacks the approved 3:2 images with `bin/compose_pinterest.py`, then compresses the Pinterest output to `≤700 KB`.

---

## 🚀 Unified Pipeline Execution Sequence

```
[User Stages Files in font-factory/fonts/{font-slug}/]
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1A: Font Metadata & Package Pass                      │
│ Agent 13 / Codex CLI (gpt-5.6-luna:high)                    │
│ +- Audits fonts + embeds metadata + builds Pro package     │
│ +- No prepared images required; stops with handoff message  │
│ Input: font-factory/fonts/{slug}/ raw font files            │
│ Output: outputs/font-preparation/{new-slug}/                │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1B: User Visual Handoff + Agent 13 Resume             │
│ +- User prepares approved 3:2 images in the Custom GPT                  │
│ +- User supplies the exact image directory to Agent 13                  │
│ +- Agent 13 validates/copies images + makes square variants             │
│ +- Missing Pinterest image is mechanically stacked with bin/compose...  │
│ +- Squares target ≤500 KB; Pinterest output targets ≤700 KB             │
│ Input: thumbnail_main + promo_N (+ optional thumbnail_pinterest.png)    │
│ Output: copied 3:2 visuals, squares, Pinterest, manifest               │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Free-to-List Marketplace & Marketing Agents        │
│ Agents 2, 8, 9, 10 (Fast Sequential Batch Launch)           │
│ +- Locks unified product number {NEXT_NUM} across platforms  │
│ +- Reads outputs/font-preparation/{new-slug}/ for context    │
│ +- Applies outputs/pricing-reference.md pricing tables       │
│                                                             │
│ 1. Agent 2  => outputs/creativemarket/{NUM}-{slug}-cm.md    │
│ 2. Agent 8  => outputs/masterbundles/{NUM}-{slug}-mb.md     │
│ 3. Agent 9  => outputs/cubebrush/{NUM}-{slug}-cb.md         │
│ 4. Agent 10 => outputs/pinterest/{NUM}-{slug}-pin.md + Vault│
│                                                             │
│ (Etsy Agent 6 & DaFont Freemium Agent 11 are OMITTED)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ How to Trigger

### Stage 1A — Metadata & Package Pass:
```bash
/font-prep "font-factory/fonts/vellum/, final name: Vellum"
```

Agent 13 stops after metadata/package completion and prints `READY FOR VISUAL HANDOFF`. Prepare the images separately while it is stopped.

### Optional With Freemium (DaFont/FontSpace Included):
```bash
/font-workflow "font-factory/fonts/vellum/ --with-freemium"
```

### Stage 1B — Resume Visual Handoff:
```bash
/font-prep "continue visual handoff for Vellum; prepared visuals: /absolute/path/to/prepared_visuals/"
```

Run Stage 2 marketplace commands only after Stage 1B completes.

### Stage 2 Marketplace Commands (Sequential Pipeline: CM -> MasterBundles -> Cubebrush):
```bash
/cm-font "outputs/font-preparation/vellum/"
/mb-font "outputs/font-preparation/vellum/"
/cb-font "outputs/font-preparation/vellum/"
/pinterest-font "outputs/font-preparation/vellum/"
```

### Optional Standalone Commands (not in the sequential run):
```bash
/etsy-font "outputs/font-preparation/vellum/"
/freemium-font "outputs/font-preparation/vellum/"
```
