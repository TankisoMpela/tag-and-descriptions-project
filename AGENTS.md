# Tag & Description Project — Master Workspace & Agent Execution Guide

This document defines the unified workspace structure, product numbering convention, platform constraints, tag count tracking, and output file management for all registered marketplace and portfolio-marketing agents.

---

## ⚡ TOKEN EFFICIENCY & SPEED ARE FIRST-ORDER (read before changing anything)

Output tokens are the budget: they are generated serially and dominate wall
clock. Input caches at 50× less, and the mechanical scripts total under 20 s.

Any change that adds cost must be justified by a measurement. Before adding a
required output artifact, a spec section or a new step, read
`docs/TOKEN-EFFICIENCY.md` — it holds the baseline, the six rules, and two
mechanical optimisations already tested and rejected.

Short version: author once and derive the rest; query data instead of reading
it; rules belong in validators, not prose; one command beats many turns; and
never cut the listing prose, which is the product.

---

## 🧭 PLACEHOLDER VOCABULARY (do not search for these paths)

| Placeholder | Means | Example |
|---|---|---|
| `{NUM}` | the unified product number, set once and shared by every platform | `88` |
| `{slug}` / `{product-slug}` | the same slug, derived from the final font name | `Andallan` → `andallan` |
| `{input-slug}` | the source workspace folder under `font-factory/fonts/` | `13-andallan` |
| `{Font-Name}` | the final font name, exact spelling | `Andallan` |
| `{YYYY-MM-DD}` | today's date | `2026-09-22` |

Source fonts in `font-factory/fonts/{input-slug}/`; preparation in
`outputs/font-preparation/{NUM}-{slug}/`; listings in
`outputs/{booth|pixiv|creative-fabrica}/{NUM}-{slug}-{booth|pixiv|cf}.md`. Numbers
are unpadded, and tools live in `bin/` — never search the tree for one.

---

## ⚡ DEFAULT FONT PIPELINE (`/full-workflow`)

The full font launch runs strictly sequentially, one registered agent at a time; wait for each
stage's final result before starting the next. The only registered agents for this project are the
five specialists below plus the `full-workflow` orchestrator.

1. `font-image-generator` (Agent 27) — bespoke visual handoff.
2. `font-prep-specialist` (Agent 13) — metadata/package pass, specimens, and an
   empty `visuals/New-Images/` drop directory. It never copies or processes final images.
3. `booth-fonts-specialist` (Agent 20) — BOOTH listing; default campaign is a
   limited-time free offer (`FREE_ACTIVE`) with free-campaign tags and a like CTA.
4. `cm_fonts_specialist` (Agent 2) — Creative Market font listing using a bounded
   per-font Creative Market research pass plus verified product facts; historical
   local listings are optional writing references only.
5. `creative-fabrica-fonts-specialist` (Agent 29) — Creative Fabrica Fonts listing.

Every other agent (Pixiv, Cubebrush, YellowImages, DLsite, Etsy, MasterBundles,
Marketore, Behance, Pinterest, X, Telegram, namemaker, brush workflows, the-converter,
font-final-visual-processor, booth-ready) is archived under `archive/` and must not be invoked.

### Default package copies (Agent 13)

Agent 13 writes font binaries into a folder named after the font, never `pro/`, then creates
three archives: `{Font-Name}-Commercial-Use.zip` and `{Font-Name}-Personal-Use.zip` (both
clean, identical font binaries; Personal-Use may add a like-request note at the root) plus
`{Font-Name}-Free-Trial-Demo.zip` (digits and ASCII punctuation replaced with the FontFairy
demo stamp; letters stay clean for preview).
All archives contain only the font folder and the OTF/TTF/WOFF/WOFF2 files;
`description.txt` remains at the preparation output root and is never packaged.

## 🚧 LISTING-AGENT SCOPE, TAG RULES, PLATFORM MATRIX & FETCH POLICY

Relocated to `agents/reference/AGENTS-annex-listing.md` — listing agents
(BOOTH, Pixiv, Creative Fabrica) read it; the visual, preparation, and
final-image agents do not.

---

## 🖼️ BESPOKE FONT IMAGE HANDOFF

Relocated to `agents/reference/AGENTS-annex-visual-handoff.md` — read it if you are the
font-image-generator or the font-final-visual-processor.

Agent 27's `prepared_visuals/` are DRAFTS: they stay in `font-factory/` and are never copied
into `outputs/`. Agent 13 copies only the four factual specimen PNGs and leaves an empty
`visuals/New-Images/` drop directory. The seller drops their own generated images there and
runs `/font-final-images` (Agent 30), which is deliberately outside `/full-workflow`.

## 📄 TRIAL INSERT PDF (`/booth-pdf-maker` — standalone)

`/booth-pdf-maker` builds a one-page Japanese branded trial-insert PDF (not a like CTA).
It is deliberately outside `/full-workflow`. Required inputs: BOOTH item URL, local font
directory, and trial URL; the product image comes from `{font-dir}/visuals/New-Images/squares/`
(mechanical `thumbnail_main` pick). One command: `python3 bin/make_booth_trial_pdf.py …` →
`outputs/booth-pdfs/{slug}-trial-insert.pdf`. Canonical spec: `agents/agent-booth-pdf-maker.md`.

## 📁 WORKSPACE & OUTPUT DIRECTORY STRUCTURE

All generated marketplace listing copy and font preparation outputs live under `outputs/`:

```
tag-and-description-project/
├── font-factory/                       ← FONT INPUT, VISUAL-REFERENCE, PROMPT, AND PREPARATION WORKSPACE
│   └── fonts/{font-slug}/
│       ├── raw .otf/.ttf files
│       ├── visual-references/          ← original thumbnail/supporting images used to write prompt briefs
│       ├── visual-direction/           ← Agent 27 art direction, plan, and review
│       ├── visual-prompts/             ← supporting-image briefs and references
│       └── prepared_visuals/           ← Agent 27 DRAFT visuals; stay here, never copied to outputs/
│           ├── 3x2/                    ← thumbnail_main.png and promo_N.png
│           ├── 1x1/                    ← thumbnail_main.png, thumbnail_japanese.png, promo_N.png
│           ├── specimens/              ← two factual specimen families per ratio
│           └── visual-handoff-manifest.md
├── outputs/                            ← ALL MARKETPLACE LISTING OUTPUTS
│   ├── font-preparation/               ← Agent 13 {NUM}-{slug} packages, ZIP copies, and visual derivatives
│   ├── booth/                          ← {NEXT_NUM}-{slug}-booth.md + booth-tag-ledger.md
│   ├── booth-pdfs/                     ← /booth-pdf-maker one-page trial inserts
│   ├── pixiv/                          ← {NEXT_NUM}-{slug}-pixiv.md + pixiv-tag-ledger.md
│   ├── creative-fabrica/               ← {NEXT_NUM}-{slug}-cf.md
│   └── research/                       ← research banks, collectors, and SQLite DBs
├── agents/                             ← canonical agent specs (+ reference/)
├── archive/                            ← archived agents, specs, commands, and the kilo/claude harnesses
├── bin/                                ← search.js plus validators and collectors
└── opencode.json                       ← opencode agent registry (omp registers agents from .omp/agents)
```

---

## 🔢 UNIFIED PRODUCT NUMBERING ALGORITHM (`{NEXT_NUM}`)

Every product processed in the pipeline receives a **unified numeric ID** (`{NEXT_NUM}`) that is shared across all platform outputs for that product.

### How Agents Determine `{NEXT_NUM}`:

1. **Existing Product Lookup (Cross-Platform Alignment)**:
   - When an agent is called to generate a listing for an existing product (e.g. generating the Creative Market listing for product `#3`), the agent may use an explicitly supplied prior listing filename or product number to preserve alignment. Listing agents must not scan or open product packages, source folders, or assets to determine numbering.
   - Maintain the exact same number and slug across all platform output files!

2. **New Product Generation**:
   - If generating a new product from scratch, scan **all platform folders** (`outputs/*/*.md`) for existing numeric file prefixes (`[0-9]*.md`) — never a single platform folder on its own, or different platforms will collide on the same number.
   - Extract the highest existing numeric prefix (`MAX_NUM`). If no files exist, set `MAX_NUM = 0`.
   - Set `NEXT_NUM = MAX_NUM + 1`, and pass that one number to every stage (BOOTH, Pixiv, Creative Fabrica) — the orchestrator computes it once and supplies it.
   - Use this `{NEXT_NUM}` prefix for all platform output files created during the run (e.g., `33-my-font-booth.md`, `33-my-font-pixiv.md`, `33-my-font-cf.md`).

---

## 🏷️ CREATIVE FABRICA TAG STRATEGY

Relocated into `agents/agent-29-creative-fabrica-fonts-specialist.md` — read it if you are the
Creative Fabrica agent.

## 📚 Archived guidance

Non-active platforms (Pixiv, Etsy, MasterBundles, Cubebrush, YellowImages,
Marketore, Behance, Pinterest, DaFont/FontSpace freemium, Procreate brushes, Obsidian export)
and pricing reference are preserved in `agents/reference/AGENTS-full-archive.md`.
Read it only when the user explicitly reactivates one of those workflows.

## CODEX ROUTING (NATIVE REGISTRY)

When this repository is operated by Codex, use only the Codex registrations in
`.codex/agents/`. The active Codex font workflow is `full_workflow`, and its
child-agent mapping is:

| Codex agent | Project role |
|---|---|
| `font_image_generator` | Agent 27 visual handoff |
| `font_preparer` | Agent 13 font preparation |
| `booth_fonts_specialist` | Agent 20 BOOTH listing |
| `cm_fonts_specialist` | Agent 2 Creative Market listing |
| `creative_fabrica_fonts_specialist` | Agent 29 Creative Fabrica listing |

Do not use `opencode.json`, OpenCode slash commands, or the hyphenated OpenCode
names for Codex delegation. The existing `agents/agent-28-full-workflow.md`
belongs to the OpenCode workflow and is not the Codex orchestrator; Codex uses
`.codex/agents/full-workflow.toml` instead.
