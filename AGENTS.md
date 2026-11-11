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
six specialists below plus the `full-workflow` orchestrator.

1. `font-image-generator` (Agent 27) — bespoke visual handoff, complete theme
   prompts, and four ImageGen thumbnails (main and alternate at both ratios).
2. `font-prep-specialist` (Agent 13) — metadata/package pass and rendered
   specimen sheets; installs Agent 27's four thumbnails and all 24 support
   renders into the final image input folder. Pinterest template pins are retired.
3. `cm_fonts_specialist` (Agent 2) — Creative Market font listing using a bounded
   per-font Creative Market research pass plus verified product facts; historical
   local listings are optional writing references only.
4. `creative-fabrica-fonts-specialist` (Agent 29) — Creative Fabrica Fonts listing.
5. `font-final-visual-processor` (Agent 30) — final full-size JPEGs, ten
   edge-to-edge PNG Pinterest composites, and image manifest. Run after listings when both
   named thumbnail pairs and the required image pool pass the readiness check.

Every other agent (Pixiv, Cubebrush, YellowImages, DLsite, Etsy, MasterBundles,
Marketore, Behance, the legacy Pinterest agent 10, X, Telegram, namemaker, brush
workflows, the-converter, booth-ready) is archived under `archive/` and must not be
invoked. Agent 30 is included as stage 6 and remains available through
`/font-final-images` for previously prepared products. `/font-rights-check`
(Agent 31) and the two Pinterest pipeline agents below remain outside
`/full-workflow`.

Before stage 1, honor an exact Saved source folder or staged workspace supplied
by the user. Stage an exact Saved folder with `--source`. If none is supplied,
Agent 27 starts by running `python3 bin/stage_saved_font.py --random`, which
chooses and stages one eligible Saved family without asking the user to
choose. It moves only that folder's root-level OTF/TTF files into a fresh
`font-factory/fonts/{input-slug}/`, where they remain as the source of record.
Concurrent selections are serialized; Agent 27 must continue only when its own
call reports `RANDOM_SOURCE_CLAIMED`. Otherwise, stop instead of adopting a
workspace another run may be using.
Nested repair/output folders stay in Saved and are excluded; existing
destinations are never overwritten. Agent 27 reads the metadata and reviews
every page of the full mapped-glyph atlas before recording the factual
description and observed vibe in its visual plan.

### Default package copies (Agent 13)

Agent 13 writes OTF, TTF, and WOFF files into separate `OTF/`, `TTF/`, and
`WOFF/` subfolders inside a folder named after the font, never `pro/`. It then
creates one archive named `{Font-Name}.zip` containing that folder and all
three validated formats. `description.txt` remains at the preparation output
root and is never packaged. Do not produce WOFF2 files or separate use-based
archives.

Keep each source's native outline format intact: glyf/TTF inputs feed the TTF
and WOFF, with CFF/OTF derived; CFF/OTF inputs feed the OTF and WOFF, with TTF
derived. The package command compares cmap, layout, shaping, legacy `kern`
pairs, and native hint data against its source. It records raster deltas at
small sizes and 96/200 px in the existing audit report.

## 🚧 LISTING-AGENT SCOPE, TAG RULES, PLATFORM MATRIX & FETCH POLICY

Relocated to `agents/reference/AGENTS-annex-listing.md` — current BOOTH and
Creative Fabrica listing agents read it; its Pixiv section is archived
reference only. Creative Market follows its dedicated agent spec.

---

## 🖼️ BESPOKE FONT IMAGE HANDOFF

Relocated to `agents/reference/AGENTS-annex-visual-handoff.md` — read it if you are the
font-image-generator or the font-final-visual-processor.

Agent 27 writes the handoff to `font-factory/fonts/{input-slug}/prepared_visuals/`:
two clean, white-background font-name specimens, the four prompts in
`visual-direction/theme.txt`, four matching generated thumbnails, and 12
seeded-random HTML/CSS support designs at both ratios (eligible family-showcase
templates are part of the same pool, not guaranteed inclusions). Pinterest
template pins are retired. Agent 27 no longer makes
factual specimen previews; Agent 13 renders the canonical factual specimens
during preparation. Its `visual-plan.json` also stores the
metadata- and specimen-grounded type label, thumbnail subtext, personality, and
product description, plus a verified product-facts bundle for the listing
stages. Agent 13 writes that description to the preparation
folder's `description.txt`; the orchestrator passes the same profile to the
three listing agents. Agent 13 does not install Pinterest pins. It copies all
four generated thumbnails and 24 support renders into `visuals/New-Images/`
for final processing; lettering references and other review assets stay in
`font-factory/`. Agent 30 runs after the listings when its readiness check
passes, preserves main and alternate thumbnail JPEGs in both final ratio folders,
targets 200 KB JPEGs with a default 300 KB preferred limit, and continues with
the smallest available JPEG if a file stays above 300 KB. It creates ten
approximately 1:2 PNG Pinterest panels by stacking three complete 3:2 source
images edge-to-edge at full width. Exact 3:2 rows produce 1000×2001; no crop,
stretch, or added side fill is used. It then writes their manifest.
`/pinterest-prepare` validates and uploads only those ten composites
to Blob, then writes every public link to `public-urls.md`. Pinterest upload
remains outside `/full-workflow`.

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
back every sibling. The pass is **search-first and source-complete**: for every family run three
separate Serper/Google searches (exact family name, `site:fonts2u.com` exact family, and
`site:findmyfonts.com` exact family), then search material leads across commercial places and
free-font directories (including DaFont, FontsGeek/FontGeek, FontFreak, FontSpace, 1001Fonts
and similar sources). Follow links to the credited author/foundry and named marketplace listings,
including Creative Market; inspect relevant pages for exact match, author/uploader, licence label,
date or a grant. Record the author/status, earliest date or age,
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

The Pinterest template catalogue is retired. Agent 30 now runs within
`/full-workflow` after listings and composes exactly ten approximately 1:2 panels
from the prepared 3:2 image pool: five lead with the main thumbnail and five
place it between two random 3:2 images. Each complete source spans the full
1000-pixel width and keeps its aspect ratio, producing three approximately
1000×667 rows and a 1000×2001 Pin with exact 3:2 inputs. No side fill or crop
is added. It writes `pinterest-set-manifest.json`
for those ten PNG composites. The
preparer validates and uploads only those manifested composites to Blob, then
writes every resulting link to `public-urls.md`.

- `/pinterest-prepare` (pinterest-font-preparer) runs after Agent 30 for each
  font, on its `outputs/font-preparation/{NUM}-{slug}/` folder. It validates
  ten composites from the pin-set manifest, then uploads every image to the
  `pinterest-pins-media` Vercel Blob store (one URL per image). It finds exact
  font product pages from Creative Fabrica and Creative Market seller catalogs.
  On Creative Market it checks PaperMoonStudioC first, then Timothy9 only when
  the font is absent from the first shop; it saves one exact product URL per
  marketplace in the registry and writes a
  `pinterest-profile.json` from product metadata plus inspected thumbnails and
  support art. That profile and its 30–60 evidence-backed keyword phrases feed
  the daily brief. It also records a separate Creative Fabrica source-font
  match with `set-source-match`; `urls.creative_fabrica` remains the prepared
  product listing. The local tracker displays both marketplace sheets. It
  classifies each font into one of the seven user-created
  boards and stores the canonical assignment in the registry; the daily agent
  uses that assignment unchanged. After upload, it fetches each public URL without credentials
  and checks HTTP 200, image content type, the 5 MB Buffer bulk-safe target, and
  exact manifest hash. It then writes all image URLs into `public-urls.md`
  (`pinterest-assets/` holds the linked project; auth lives in
  `~/.config/papermoon/blob.env` — never commit or print the token).
- `/pinterest-daily` (daily-pinterest-run) randomly picks 10 ready fonts per
  day by default (14-day re-pin exclusion; the user confirmed Buffer email is
  verified, so use five only if that account later becomes unverified), writes
  fresh title/description/alt/keywords
  per font using the preparer's saved board classification, and validates + assembles
  `outputs/pinterest/{YYYY-MM-DD}/buffer.csv`
  (Buffer free-plan import — carries Alt Text; staggered hourly from 09:00
  UTC) plus `pins.csv` as the Pinterest-native fallback. Per pin it takes ONE
  manifested image link and one product link; image indexes are balanced across
  the batch and both choices are stable for that date.
  Anti-cannibalization lives in `outputs/research/pinterest-tags.sqlite`:
  `prepared_pins` holds editable drafts; after a human confirms import,
  `tag_uses` (keyword counts), `pinned_runs` (re-pin window), and `pins` record
  accepted rows. Read confirmed copy with
  `python3 bin/pinterest_tag_ledger.py history --slug <slug> --full`; that
  history is included automatically in `brief.md`. Pinterest keyword rotation
  is separate from BOOTH's evidence-backed tag ledger; it prefers unused terms
  for that font, then lower-use phrases across Pinterest history.

Tools: `bin/process_final_font_images.py` (Agent 30 composites),
`bin/pinterest_registry.py`, `bin/papermoon-blob.py`,
`bin/pinterest_tag_ledger.py`, `bin/make_daily_pins.py`. Carousels are not
supported by the bulk CSV (one Media URL per row) — one image per pin.
Buffer is the primary human import. The user has already created these seven
Pinterest boards. The preparer assigns each font to one board and the daily run
copies that assignment exactly into Buffer's `Board Name`. Use the canonical
descriptions in
`agents/reference/pinterest-board-setup.md`:
`Display Fonts for Logos & Posters`, `Script & Handwriting Fonts`,
`Serif Fonts for Branding & Editorial`, `Retro & Vintage Fonts`,
`Gothic & Blackletter Fonts`, `Pixel, Gaming & Tech Fonts`, and
`Cricut & Craft Fonts` ([Buffer guide](https://support.buffer.com/articles/how-to-upload-posts-in-bulk-to-buffer-cTIhl4mv6H)).
The Pinterest-native CSV importer can create a missing board ([Pinterest guide](https://help.pinterest.com/en/business/article/bulk-upload-video-pins)).
After Buffer accepts/queues rows (or Pinterest accepts the native CSV), record
only those fonts with `python3 bin/pinterest_tag_ledger.py mark-imported --date D
--slugs slug-a slug-b`; this records import acceptance, not publication. Buffer's
free queue is limited to 10 waiting posts, so import within remaining slots.
The agents make no publication claim. Buffer's CSV `Tags` are internal labels,
not Pinterest SEO keywords; this workflow leaves them empty. Pinterest-native
keywords are written to `pins.csv`. Buffer Insights are not currently ingested
into the local ledger, so review saves/clicks in Buffer manually when refining
future batches. Buffer's current Pinterest guide lists daily limits of 25 Pins
for verified accounts and 5 for unverified accounts; use `--count 5` until the
email is verified ([Buffer Pinterest guide](https://support.buffer.com/articles/using-pinterest-with-buffer-PB6dp33lMG)).

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
│           ├── 1x1/                    ← thumbnail_main.png
│           ├── supporting/3x2/         ← 12 eligible HTML/CSS templates
│           ├── supporting/1x1/         ← the same 12 square adaptations
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
   - Set `NEXT_NUM = MAX_NUM + 1`, and pass that one number to every active listing stage (Creative Market, Creative Fabrica) — the orchestrator computes it once and supplies it.
   - Use this `{NEXT_NUM}` prefix for all platform output files created during the run (e.g., `33-my-font-booth.md`, `33-my-font-cm.md`, `33-my-font-cf.md`).

---

## 🏷️ CREATIVE FABRICA TAG STRATEGY

Relocated into `agents/agent-29-creative-fabrica-fonts-specialist.md` — read it if you are the
Creative Fabrica agent. The working target is about 30 relevant tags (up to 40), using exact route wording plus relevant comparable Designer Tags phrases; fewer are acceptable when the evidence supports a smaller set, without padding. `bin/validate_creative_fabrica_listing.py` enforces mechanical structure and source checks, not candidate-pool exhaustion or engagement judgments.

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
| `cm_fonts_specialist` | Agent 2 Creative Market listing |
| `creative_fabrica_fonts_specialist` | Agent 29 Creative Fabrica listing |
| `font_final_visual_processor` | Agent 30 final image processing |

Do not use `opencode.json`, OpenCode slash commands, or the hyphenated OpenCode
names for Codex delegation. The existing `agents/agent-28-full-workflow.md`
belongs to the OpenCode workflow and is not the Codex orchestrator; Codex uses
`.codex/agents/full-workflow.toml` instead.
