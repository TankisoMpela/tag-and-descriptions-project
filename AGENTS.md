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
`outputs/{booth|creativemarket|pixiv|creative-fabrica}/{NUM}-{slug}-{booth|cm|pixiv|cf}.md`. Numbers
are unpadded, and tools live in `bin/` — never search the tree for one.

---

## ⚡ DEFAULT FONT PIPELINE (`/full-workflow`)

The full font launch runs strictly sequentially, one registered agent at a time; wait for each
stage's final result before starting the next. The only registered agents for this project are the
five specialists below plus the `full-workflow` orchestrator.

1. `font-image-generator` (Agent 27) — bespoke visual handoff.
2. `font-prep-specialist` (Agent 13) — metadata/package pass, rendered specimen
   sheets, and checked installation of Agent 27's 23 HTML/CSS Pinterest template
   pins into `visuals/New-Images/pinterest/`. It never processes the seller's final images.
3. `booth-fonts-specialist` (Agent 20) — BOOTH listing; default campaign is a
   limited-time free offer (`FREE_ACTIVE`) with free-campaign tags and a like CTA.
4. `cm_fonts_specialist` (Agent 2) — Creative Market font listing using a bounded
   per-font Creative Market research pass plus verified product facts; historical
   local listings are optional writing references only.
5. `creative-fabrica-fonts-specialist` (Agent 29) — Creative Fabrica Fonts listing.

Every other agent (Pixiv, Cubebrush, YellowImages, DLsite, Etsy, MasterBundles,
Marketore, Behance, the legacy Pinterest agent 10, X, Telegram, namemaker, brush
workflows, the-converter, booth-ready) is archived under `archive/` and must not be
invoked. `/font-final-images` (Agent 30), `/font-rights-check` (Agent 31) and the two
Pinterest pipeline agents below are live, but deliberately outside `/full-workflow`.

Before stage 1, `/full-workflow` selects one exact source folder from
`font-factory/Saved/`. If the user has not named it, list the available folders
and root-level OTF/TTF files with `python3 bin/stage_saved_font.py --list` and
ask which one to use. Move only that folder's original root-level OTF/TTF files
into a fresh `font-factory/fonts/{input-slug}/` with the same helper; these
remain there as the source of record for completed work. Nested repair/output
folders stay in Saved and are excluded; unrelated existing destinations are
never overwritten. Agent 27 inspects the staged source metadata and full
mapped-glyph specimen before deciding a name or profile.

### Default package copies (Agent 13)

Agent 13 writes font binaries into a folder named after the font, never `pro/`, then creates
two archives: `{Font-Name}-Commercial-Use.zip` and
`{Font-Name}-Personal-Use.zip`. Both contain byte-identical font binaries;
Personal-Use may add a like-request note at the root. The preparation workflow
does not watermark trial fonts. Both archives contain the font folder and the
OTF/TTF/WOFF/WOFF2 files; `description.txt` remains at the preparation output
root and is never packaged.

## 🚧 LISTING-AGENT SCOPE, TAG RULES, PLATFORM MATRIX & FETCH POLICY

Relocated to `agents/reference/AGENTS-annex-listing.md` — current BOOTH and
Creative Fabrica listing agents read it; its Pixiv section is archived
reference only. Creative Market follows its dedicated agent spec.

---

## 🖼️ BESPOKE FONT IMAGE HANDOFF

Relocated to `agents/reference/AGENTS-annex-visual-handoff.md` — read it if you are the
font-image-generator or the font-final-visual-processor.

Agent 27 writes the handoff to `font-factory/fonts/{input-slug}/prepared_visuals/`:
three clean, white-background font-name specimens for use as raw image-model
material, with complete bespoke 3:2, 1:1, and storefront prompts in
`visual-direction/theme.txt`; 13 seeded-random HTML/CSS support designs
at both ratios (including eligible family-showcase templates), four factual
specimen previews, and every active HTML/CSS Pinterest template rendered with
the font. Its `visual-plan.json` also stores the
metadata- and specimen-grounded type label, thumbnail subtext, personality, and
product description, plus a verified product-facts bundle for the listing
stages. Agent 13 writes that description to the preparation
folder's `description.txt`; the orchestrator passes the same profile to the
three listing agents. Agent 13 installs the 23 template pins into
`outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/pinterest/`; the other Agent-27 review assets stay in
`font-factory/`. Final thumbnails are generated from the matching specimen and
prompt; an old thumbnail reference is not part of that process.
After the seller adds final images directly to
`outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/`, including both
`thumbnail_main_3x2` and `thumbnail_main_1x1` plus at least two additional 3:2
images, `/font-final-images` (Agent 30) processes the complete set. It waits
without writing outputs until the named thumbnail pair and Pinterest image pool
are present, targets 200 KB JPEGs with a 300 KB maximum, then adds ten
image-composite Pinterest panels after the templates and writes a manifest for
the complete pin set. `/pinterest-prepare` validates and uploads every template
and composite image to Blob, then writes every public link to `public-urls.md`.
Agent 30 and the Pinterest preparer are outside `/full-workflow`.

## 📄 TRIAL INSERT PDF (`/booth-pdf-maker` — standalone)

`/booth-pdf-maker` builds a one-page Japanese branded trial-insert PDF (not a like CTA).
It is deliberately outside `/full-workflow`. Required inputs: BOOTH item URL, local font
directory, and trial URL; the product image comes from `{font-dir}/visuals/New-Images/squares/`
(mechanical `thumbnail_main` pick). One command: `python3 bin/make_booth_trial_pdf.py …` →
`outputs/booth-pdfs/{slug}-trial-insert.pdf`. Canonical spec: `agents/agent-booth-pdf-maker.md`.

## ⚖️ FONT RIGHTS CHECK (`/font-rights-check` — standalone)

`/font-rights-check` (Agent 31, `font-rights-researcher`) judges whether the seller may ship a
font sitting in `font-factory/input/<N>-<Family>/`. It is deliberately outside
`/full-workflow` and must never be invoked by the orchestrator or a listing agent. The staging
`<N>` is not a `{NUM}`; no product number appears in this workflow.

The queue is the unmarked state itself — `python3 bin/font_rights.py status --unmarked` lists
every staged folder with no verdict for its files. Research runs **per staged folder, not per
file**: the seller stages one family per folder and cleans out what does not belong, so
`plan --folder <N>` picks the folder's Regular/normal cut as its one representative and
`write … --fanout` spreads that verdict over every sibling (each keeps its own `fsType`).
`groups --folder <N>` still exists to audit a folder you do not trust, splitting it by
(family, holder, fsType) — a folder that flags foreign holders may only ever go red or amber,
never green. Three states, and the middle one is the point:

| state | means | ship it? |
|---|---|---|
| `claimed` (red) | still sold or held by an active rights owner | no |
| `orphan` (amber) | no active holder found **and** no licence terms found | **no — unlicensed, not safe** |
| `clear` (green) | a grant quote the tool verified in the binary, or the author agreed this run | yes |

`bin/font_rights.py` enforces the evidence rules (a live URL for `claimed`, two searched
avenues for `orphan`, a verbatim grant quote for `clear`) and decides nothing itself; a name
table's "free for commercial use" line is a claim until verified, because these files come out
of a repackaged 29,000-font dump. A `claimed` URL must also be able to *carry* the claim — a
commercial seller, the holder's own domain, or a type-rights reference; free-font directories
and name-table scrapers are provenance sources, not proof of ownership or licence. And a `clear`
never fans across holders: if any file in the folder names a different holder, the tool holds
back every sibling. The pass is **search-first**: 1-2 searches per folder across commercial
places and free-font directories (including DaFont, FontsGeek/FontGeek, FontFreak, FontSpace,
1001Fonts and similar sources), and at most one page fetch for the best source on exact match,
author/uploader, licence label, date or a grant. Record the author/status, earliest date or age,
distribution claims, abandonware assessment, and each relevant page/uploader in the verdict's
structured `research` field; use unknown when a detail cannot be sourced. Abandonware and a free
download never grant permission to ship.
`font-vault/input_inspector.py` renders each verdict as a coloured chip on the row — press ↻
Refresh after a run, and click a chip to read the evidence and provenance history, including
the distribution pages and uploaders (their URLs are clickable and copyable, and **Copy full
report** takes the whole record out as plain text for follow-ups outside the app). The tool never touches a font binary,
a manifest, or `in-use.txt`; deleting or returning a font in the inspector voids its verdict.
The sidecars live in a **gitignored** directory, so a finished run must end with
`python3 bin/font_rights.py sync`, which mirrors them into the tracked
`outputs/research/font-rights-ledger.json` (`sync --check` exits non-zero on drift).
Canonical spec: `agents/agent-31-font-rights-researcher.md`.

## 📌 DAILY PINTEREST RUN (standalone pipeline — outside `/full-workflow`)

The Pinterest image sequence has four stages; the archived Agent 10 stays
archived and is not invoked.

Agent 27 renders every active HTML/CSS Pinterest template with the font into
`prepared_visuals/pinterest/` and records their order, source font hash, sizes,
and checksums. Agent 13 copies those verified pins to
`visuals/New-Images/pinterest/`. After the seller's image-model files are added,
Agent 30 composes exactly ten additional 2:3 panels from the 3:2 image pool in
the same directory: five lead with the thumbnail and five place it between two
random 3:2 images. It appends them after the template set and writes
`pinterest-set-manifest.json`. The preparer validates the complete manifested
set, uploads every image to Blob, and writes every resulting link to
`public-urls.md`. The HTML/CSS source templates are in `font-factory/pin-html/`;
retired `green_starburst` and `phrase` designs stay out of production pins.

- `/pinterest-prepare` (pinterest-font-preparer) runs after Agent 30 for each
  font, on its `outputs/font-preparation/{NUM}-{slug}/` folder. It validates
  the dynamic template count plus ten composites from the pin-set manifest,
  then uploads every image to the `pinterest-pins-media` Vercel Blob store (one
  URL per image). It also records both supplied product-page URLs, the
  description (`description.txt`), and a board suggestion (Handwritten / Display
  / Script / Decorative Fonts), then writes all image URLs into `public-urls.md`
  (`pinterest-assets/` holds the linked project; auth lives in
  `~/.config/papermoon/blob.env` — never commit or print the token).
- `/pinterest-daily` (daily-pinterest-run) randomly picks 10 ready fonts per
  day (14-day re-pin exclusion), writes fresh title/description/alt/keywords
  per font, and validates + assembles `outputs/pinterest/{YYYY-MM-DD}/buffer.csv`
  (Buffer free-plan import — carries Alt Text; staggered hourly from 09:00
  UTC) plus `pins.csv` as the Pinterest-native fallback. Per pin it takes ONE
  manifested image link and one product link; image indexes are balanced across
  the batch and both choices are stable for that date.
  Anti-cannibalization lives in `outputs/research/pinterest-tags.sqlite`:
  `prepared_pins` holds editable drafts; after a human confirms import,
  `tag_uses` (keyword counts), `pinned_runs` (re-pin window), and `pins` record
  accepted rows. Read confirmed copy with
  `python3 bin/pinterest_tag_ledger.py history --slug <slug> --full`; that
  history is included automatically in `brief.md`.

Tools: `font-factory/pin-html/render_gallery.mjs` (run by Agent 27),
`bin/install_template_pinterest_pins.py` (Agent 13 handoff),
`bin/process_final_font_images.py` (Agent 30 composites),
`bin/pinterest_registry.py`, `bin/papermoon-blob.py`,
`bin/pinterest_tag_ledger.py`, `bin/make_daily_pins.py`. Carousels are not
supported by the bulk CSV (one Media URL per row) — one image per pin.
Buffer is the primary human import. Its Pinterest `Board Name` must already
exist in Pinterest, so create the four suggested boards before the first Buffer
import ([Buffer guide](https://support.buffer.com/articles/how-to-upload-posts-in-bulk-to-buffer-cTIhl4mv6H)). The
Pinterest-native CSV importer can create a missing board ([Pinterest guide](https://help.pinterest.com/en/business/article/bulk-upload-video-pins)). After
Buffer accepts/queues rows (or Pinterest accepts the native CSV), record only
those fonts with `python3 bin/pinterest_tag_ledger.py mark-imported --date D
--slugs slug-a slug-b`; this records import acceptance, not publication. Buffer's
free queue is limited to 10 waiting posts, so import within remaining slots.
The agents make no publication claim. Keyword candidates are seeded
mechanically in `brief.md` from each font's description.txt, then rotated via
the ledger — CM listing tags / `bin/search.js` validation remain optional
future seed sources.

## 📁 WORKSPACE & OUTPUT DIRECTORY STRUCTURE

All generated marketplace listing copy and font preparation outputs live under `outputs/`:

```
tag-and-description-project/
├── font-factory/                       ← FONT INPUT, VISUAL-REFERENCE, PROMPT, AND PREPARATION WORKSPACE
│   └── fonts/{input-slug}/
│       ├── raw .otf/.ttf files
│       ├── visual-references/          ← optional source material; no old thumbnail is required
│       ├── visual-direction/           ← Agent 27 art direction, plan, and review
│       └── prepared_visuals/           ← Agent 27 DRAFT visuals; stay here, never copied to outputs/
│           ├── 3x2/                    ← thumbnail_main.png
│           ├── 1x1/                    ← thumbnail_main.png and thumbnail_japanese.png
│           ├── supporting/3x2/         ← 13 eligible HTML/CSS templates
│           ├── supporting/1x1/         ← the same 13 square adaptations
│           ├── specimens/{3x2,1x1}/   ← four factual specimen previews
│           └── visual-handoff-manifest.md
├── outputs/                            ← GENERATED LISTINGS AND FONT PREPARATION OUTPUTS
│   ├── font-preparation/               ← Agent 13 {NUM}-{slug} packages, ZIP copies, and visual derivatives
│   ├── booth/                          ← {NEXT_NUM}-{slug}-booth.md + booth-tag-ledger.md
│   ├── creativemarket/                 ← {NEXT_NUM}-{slug}-cm.md
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
   - Set `NEXT_NUM = MAX_NUM + 1`, and pass that one number to every active listing stage (BOOTH, Creative Market, Creative Fabrica) — the orchestrator computes it once and supplies it.
   - Use this `{NEXT_NUM}` prefix for all platform output files created during the run (e.g., `33-my-font-booth.md`, `33-my-font-cm.md`, `33-my-font-cf.md`).

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

`agents/agent-28-full-workflow.md` is the shared, runtime-neutral full-workflow
contract. Codex, Qwen, OMP, and OpenCode registrations must preserve its
five-stage order and handoffs while using only their own native delegation
mechanism. Run `python3 bin/check_full_workflow_sync.py` after changing a
runtime registration to check that stage order and child-agent entries remain
aligned.

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
