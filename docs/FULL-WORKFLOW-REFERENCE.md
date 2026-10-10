# `/full-workflow` — Complete Reference

Everything the font launch workflow does: its agents, what each is handed, what
it does, the tools it runs, why those tools exist, and what each one costs in
time and tokens.

Measured 2026-09-22 on this machine (i5-1335U, 10 cores). Re-measure before
quoting any number as current.

---

## 1. The shape

Two phases. The workflow itself is **strictly sequential, one agent at a time**;
the final image processor is deliberately **outside** it.

```text
  /full-workflow  (agent-28 orchestrates; owns routing, not content)
        │
        ├─ 1  font-image-generator        (agent 27)  art direction + provisional visuals
        ├─ 2  font-prep-specialist        (agent 13)  package, metadata, specimens, drop dir
        ├─ 3  booth-fonts-specialist      (agent 20)  Japanese-first BOOTH listing
        ├─ 4  cm-fonts-specialist          (agent 2)   Creative Market corpus listing
        └─ 5  creative-fabrica-fonts-specialist (agent 29)  Creative Fabrica listing
                                      │
              ── workflow ends: READY FOR FINAL IMAGES ──
                                      │
        seller drops their own artwork into visuals/New-Images/
                                      │
        └─ /font-final-images  (agent 30)  delivery JPEGs + manifest
```

**Why this order.** Agent 27 must decide the final name before anything writes
it into metadata or copy. Agent 13 must produce the numbered output folder before
the three marketplace agents have a path and a product number to reference. The
three listing agents are independent of each other but all depend on 13, so they
run after it. Agent 30 cannot run inside the workflow because its input — the
seller's artwork — does not exist until the seller has seen Agent 27's drafts.

**Numbering.** Agent 28 scans `outputs/*/*.md` once for the highest numeric
prefix, adds one, and passes that single `{NUM}` to every stage. No child picks
its own number, so BOOTH/Creative Market/CF files for one product cannot collide.

---

## 2. The agents

### Agent 27 — `font-image-generator`

The visual art director. **Not** an image generator: it has no vision and no OCR,
and it never inspects a PNG it produced.

| | |
|---|---|
| **Provided** | font workspace, the final name when the user supplies one (otherwise it decides one under its Naming policy), the old product description, any factual constraints |
| **Produces** | `font-factory/fonts/{slug}/visual-direction/visual-plan.json` (the single source), `candidate-review.md`, and `prepared_visuals/` — 19 placeholder PNGs (9 at 3:2, 10 at 1:1) + 4 factual specimens, 23 PNGs total, plus derived `theme.txt`, `image-notes/`, `art-direction.md`, `visual-handoff-manifest.md`, `VISUAL-HANDOFF-READY.md` |
| **Tools** | `bin/font_fact_sheet.py`, `bin/generate_font_text_placeholders.py` |
| **Ends with** | `READY FOR FONT PREP HANDOFF` |

**Process.** Run the fact sheet once → build one phrase/concept ledger → write the
whole plan (per-image brief, copy, ratio layouts, placements) → run the renderer
once for the complete set. No per-image loop.

**The design decision that matters:** the agent authors **one** artifact. The
renderer derives `theme.txt`, `image-notes/` and `art-direction.md` from the
plan. Before this, the agent hand-wrote all four, which cost ~5,900 output tokens
per product and let them drift — one product's `theme.txt` and design note
described *different copy for the same promo*.

**Why no vision.** The provisional PNGs are typography-only placeholders for the
seller's later image-model pass. Judging them would need eyes this agent does not
have, so the contract is machine checks plus contrast maths, and the real artwork
is the seller's manual step.

---

### Agent 13 — `font-prep-specialist`

The mechanical packaging pass.

| | |
|---|---|
| **Provided** | the font workspace, final name, product number, and Agent 27's `prepared_visuals/` (for the four specimen PNGs only) |
| **Produces** | `outputs/font-preparation/{NUM}-{slug}/` — the font-named folder with OTF/TTF/WOFF/WOFF2, `description.txt`, all three delivery archives, `specimens/`, an **empty** `visuals/New-Images/`, and three reports |
| **Tools** | `bin/prepare_font_package.py` (which runs `font_preflight_audit.py` and `font_package_audit.py` itself), `bin/validate_font_factory.py --strict` |
| **Ends with** | `READY FOR FINAL IMAGES` |

**Process — one command.** `prepare_font_package.py` performs the entire pass:
discover inputs → pre-flight audit → name table → OS/2 flags → OTF/TTF/WOFF/WOFF2
→ copy specimens → create the drop directory → write the reports → build both
archives → run the technical audit. The agent's only judgement work is
`description.txt`. This replaced 9 numbered steps and 13 command blocks.

**Two behaviours worth knowing**, both from bugs found while building it:

- **Name ID 10 is deliberately preserved.** It carries the original founder's
  credit. Every other ID is overwritten with the studio's.
- **Specimens are the only thing copied from Agent 27.** The 23 drafts stay in
  `font-factory/` forever; they must not reach `outputs/`.

---

### Agent 20 — `booth-fonts-specialist`

Japanese-first BOOTH listing with live tag evidence. The heaviest research agent.

| | |
|---|---|
| **Provided** | preparation output path, source description, final name, `{NUM}` |
| **Produces** | `outputs/booth/{NUM}-{slug}-booth.md` + rows appended to `booth-tag-ledger.md` |
| **Tools** | `booth_owned_registry.py`, `booth_tag_ledger.py`, `booth_tag_evidence.py`, `booth_evidence_table.py`, `search.js`, `validate_booth_listing.py` |
| **Gate** | `validate_booth_listing.py` must print `[PASS]` — fail-closed |

**Why those tools.** BOOTH tags need live public-page evidence (exact-tag route,
font-category route, page-life check), and the agent must not count the studio's
own products as competitor evidence. The four `booth_*` tools exist so it
**queries** that evidence instead of reading it:

| Tool | Why it exists | Effect |
|---|---|---|
| `booth_owned_registry.py` | own-product exclusion | 546,901 → **749 tokens** |
| `booth_tag_ledger.py` | decided/rejected tag memory | 63,417 → **411 tokens** |
| `booth_tag_evidence.py` | the evidence table itself | generates, not transcribes |
| `booth_evidence_table.py` | URL columns + coverage fill | strict no-op on correct files |

The contract is **18–25 validated tags, target 20**, and the compound form only:
a bare one-word BOOTH tag resolves to a broader *graphics* page, not a font page.

---

### Agent 2 — `cm-fonts-specialist`

Creative Market font listing generated from the complete local Creative Market
font corpus and its deterministic tag-pattern bank.

| | |
|---|---|
| **Provided** | preparation output path, source description, final name, `{NUM}` |
| **Produces** | `outputs/creativemarket/{NUM}-{slug}-cm.md` — one paste-ready PDP |
| **Tools** | `build_creative_market_font_tag_bank.py`, `validate_cm_listing.py` |
| **Gate** | `validate_cm_listing.py` must `[PASS]` |

The bank is a local corpus signal, not search volume or sales evidence. The
listing validator checks the PDP structure, title/metadata limits, one allowed
classification, exactly 30 unique tags, banned mechanical terms, and leading-
word repetition.

---

### Agent 29 — `creative-fabrica-fonts-specialist`

Creative Fabrica Fonts listing. **Exactly 40 tags**, every one evidenced.

| | |
|---|---|
| **Provided** | preparation output path, source description, final name, `{NUM}` |
| **Produces** | `outputs/creative-fabrica/{NUM}-{slug}-cf.md` + ledger rows |
| **Tools** | `creative_fabrica_tag_lookup.py`, `creative_fabrica_owned.py`, the `collect_*`/`build_*` research tools, `search.js`, `validate_creative_fabrica_listing.py` |
| **Gate** | `validate_creative_fabrica_listing.py` must `[PASS]` — fail-closed |

**Why the lookups.** The collected research is large; the agent queries it
(16,170 → **291 tokens** for a lookup, 84,404 → **421 tokens** for the owned
registry) instead of reading the banks.

**The rule that shaped this agent:** a Creative Fabrica font tag must be the
**compound** form `<modifier> Font(s)`. A bare one-word tag resolves to a broader
graphics tag — `/tag/kids/` shows SVGs, `/tag/kids-fonts/` is the font page. The
standalone one-word allowance is therefore **0**, and the validator fails closed
on any single-word tag.

---

### Agent 30 — `font-final-visual-processor` (outside the workflow)

The delivery pass for the seller's own artwork.

| | |
|---|---|
| **Provided** | the preparation output folder and the seller's `visuals/New-Images/` |
| **Produces** | `source/3x2/` + `source/1x1/` exact copies, `main/` + `squares/` bounded JPEGs, `final-image-manifest.md` |
| **Tools** | `bin/process_final_font_images.py` (which runs `encode_main_jpeg.py`) |
| **Gate** | the processor exits non-zero on any failure; no separate validator |

**Process.** Enumerate raw files mechanically → classify 3:2 and 1:1
independently → copy each exactly under canonical names → encode delivery JPEGs
→ write the manifest. **No vision, no contact sheet, no semantics** — the first
stable filename in each ratio becomes `thumbnail_main` and the rest become
`promo_N`. A square is never derived from a landscape.

**Why it is outside the workflow.** Its input is the seller's artwork, which only
exists after they have seen Agent 27's drafts and done their own image-model
pass. It also never runs inside `/full-workflow`, and it never uploads.

---

## 3. Timing

Measured end to end on a real 2-weight font.

| Stage | Tool | Time |
|---|---|---|
| Agent 27 | `font_fact_sheet.py` | **0.31 s** |
| Agent 27 | `generate_font_text_placeholders.py` (19 placeholders + 4 specimens = 23 PNGs, derived views, 2 validations) | **11.5–14.3 s** |
| Agent 13 | `prepare_font_package.py` (pre-flight audit, metadata, 8 font files, archives, package audit) | **2.95 s** |
| Agent 30 | `process_final_font_images.py` (5 raw → 3+2 JPEGs + manifest) | **1.92 s** |
| validator | `validate_font_visual_handoff.py --strict` | 1.39 s |
| validator | `validate_creative_fabrica_listing.py` | 0.22 s |
| validator | `validate_booth_listing.py` | 0.15 s |
| validator | `validate_pixiv_listing.py` | 0.12 s |
| | **Mechanical total** | **≈19 s** |

**The renderer dominates, and it is not Python.** `cProfile` attributes **8.7 s
of 14.5 s to `subprocess._communicate`** — i.e. the 23 `rsvg-convert` spawns. A
*trivial* SVG costs ~274 ms, so roughly half of each is process startup, not
rasterisation. Running librsvg in-process measures **1.9×** faster and removes 23
temp files, but it saves ~1.1% of a full run and adds a PyGObject dependency, so
it was deliberately not taken.

**Mechanical time is ~7–10% of a run.** The rest is model generation. See §5.

---

## 4. Tool reference

Every tool the workflow's agents name, why it exists, and its measured cost.

### Agent 27
| Tool | Why | Timing |
|---|---|---|
| `font_fact_sheet.py` | Gives the art director verified facts — metrics, character coverage (including whether Japanese exists at all), the OpenType feature inventory, and the exact glyph sequence for proposed display copy — without it writing fontTools/uharfbuzz inline. On eQuity, shaping `ffi` returns **one glyph from three characters**, so it warns that a headline's glyph count changes; an agent with no vision cannot eyeball that. | 0.31 s |
| `generate_font_text_placeholders.py` | The whole handoff in one command: renders the 19 placeholders, renders 4 specimens via `render_specimens.py`, derives the three documents from the plan, writes the manifest and marker, and runs the strict validator twice (pending, then PASS). Stages into a temp dir and swaps atomically; refuses a non-empty output. | 11.5–14.3 s |
| `validate_font_visual_handoff.py` | Deterministic machine QA — dimensions, promo counts, notes, contrast, handoff documents. The only evidence of record, since the agent cannot see. | 1.39 s |

### Agent 13
| Tool | Why | Timing |
|---|---|---|
| `prepare_font_package.py` | The entire mechanical pass as one command. Replaced 9 steps and 13 command blocks, cutting turn count (each turn is a full round-trip). | 2.95 s |
| `font_preflight_audit.py` | Read-only input audit — loads, required tables, UPM, fsType, glyph count, cmap coverage, name IDs, GSUB/GPOS. Called by the packager; aborts before modifying anything. | incl. |
| `font_package_audit.py` | Verifies fsType per format (0 Pro, 4 Freemium). **Caught a real defect**: `079-semilya-fontera`'s Demo shipped fsType 0 where Freemium needs 4. | incl. |
| OpenType Sanitizer | Run by the packager over all eight delivered files as an **independent** parser. It parses every table where the audit above reads only fsType/name IDs/glyph count through fontTools, which loads some malformed fonts without complaint until a broken table is touched. Skipped with a note when `ots-sanitize` is absent. | ≈0.3 s |
| `validate_font_factory.py --strict` | Staging hygiene — catches the pathologically space-joined slug and stray rasters in a font root. | ~0.1 s |

### Agents 2 / 20 / 29
| Tool | Why |
|---|---|
| `booth_owned_registry.py` | Own-product exclusion so the agent never counts its own work as competitor evidence |
| `booth_tag_ledger.py` | Persistent decided/rejected tag memory across products |
| `booth_tag_evidence.py` / `booth_evidence_table.py` | Generate the evidence table rather than have the model transcribe it |
| `creative_fabrica_tag_lookup.py` / `creative_fabrica_owned.py` | Query the research banks instead of reading them |
| `search.js` | Marketplace suggestion scoring and Japanese query-language seeding |
| `validate_cm_listing.py` / `validate_booth_listing.py` / `validate_creative_fabrica_listing.py` | Fail-closed structural gates |

### Agent 30
| Tool | Why | Timing |
|---|---|---|
| `process_final_font_images.py` | The delivery pass: exact source copies, bounded JPEGs, manifest. | 1.92 s |
| `encode_main_jpeg.py` | Size-bounded JPEG via a quality ladder, binary-searched so it finds the highest rung that fits in ~log2(n) encodes. Verified byte-identical to the previous linear walk across 7 images at three different caps. | incl. |

---

## 5. Token and cost model

Per full run. Input includes each agent's spec plus the injected `AGENTS.md` and,
for listing agents, the listing annex.

| Agent | Input | Output | Total |
|---|---:|---:|---:|
| agent 27 image generator | 18,959 | 6,045 | 25,004 |
| agent 13 font prep | 4,499 | 1,200 | 5,699 |
| agent 28 orchestrator | 3,226 | 600 | 3,826 |
| agent 20 BOOTH | 20,412 | 3,674 | 24,086 |
| agent 2 Creative Market | local corpus | local corpus | no live-research loop |
| agent 29 Creative Fabrica | 12,594 | 4,247 | 16,841 |
| **Total** | **69,304** | **19,491** | **88,795** |

**Cost is not the problem.** On the DeepSeek Flash card ($0.30/M uncached input,
$0.006/M cached, $1.20/M output) a run is **≈$0.044**, or ≈$0.028 with an 80%
input cache hit.

**Wall clock is the problem, and it is output.** Input is prefill and largely
cacheable; output is generated one token at a time and cannot be cached. At
60 tok/s the 19,491 output tokens are **≈5.4 minutes of pure serial generation**;
at 100 tok/s, ≈3.2 minutes.

**So the lever is output tokens.** That is why the agent authors one artifact and
the renderer derives the rest, and why the marketplace tag rules that a validator
already enforces were removed from the prose.

---

## 6. External dependencies

| Needed | For |
|---|---|
| `python3` | everything |
| `rsvg-convert` | rasterising the placeholder SVGs (the one external rasteriser; resvg measured 2× slower here — see `docs/PASTE5-FINDINGS.md`) |
| `ots-sanitize` | the independent font parser gate (optional: skipped with a note if absent) |
| `node` | `bin/search.js` for the three listing agents |
| Python: `Pillow`, `fontTools`, `uharfbuzz`, `PyYAML` | images, font parsing, shaping, frontmatter |

**No longer needed, because their features are archived:**

| Dropped | Was for |
|---|---|
| `ffmpeg` / `ffprobe` | showcase video rendering (archived → `archive/video/`) |
| `pngquant` | Pinterest PNG fallback (archived → `archive/pinterest/`) |
| `fontforge` | the OTF→TTF conversion, replaced by fontTools `cu2qu`, which also removed two defects: fontforge wrote OS/2 v5 with a v4-length table (fontTools then refused to load the file at all) and regenerated Name ID 6 from the CFF's internal name |

---

## 7. Guardrails, and why each exists

| Rule | Why |
|---|---|
| Agents run one at a time; no task arrays or concurrent delegation | a partial file or started child must never be mistaken for completion |
| Any stage fails → stop; never start a later stage | later stages consume earlier output paths |
| Listing agents never inspect packages, fonts, images or licenses | preparation owns technical QA; duplication caused wrong claims |
| Agent 27's `prepared_visuals/` are drafts and stay in `font-factory/` | they have not been through the seller's image-model pass |
| Agent 13 copies only the four factual specimens | the 23 creative PNGs must never reach `outputs/` |
| Every listing validator is fail-closed | a listing is not complete because it looks complete |
| No stage claims upload or publication | the workflow produces copy and research handoffs only |

---

## 8. Where things live

```text
font-factory/fonts/{slug}/
  visual-direction/     visual-plan.json (source), candidate-review.md,
                        theme.txt / image-notes/ / art-direction.md (derived)
  prepared_visuals/     DRAFTS — stay here, never copied to outputs/
outputs/font-preparation/{NUM}-{slug}/
  {Font-Name}/          OTF TTF WOFF WOFF2
  {Font-Name}-Commercial-Use.zip, {Font-Name}-Personal-Use.zip, {Font-Name}-Free-Trial-Demo.zip
  description.txt, specimens/, name-report.md, audit-report.md,
  specimen-source-manifest.md
  visuals/New-Images/   EMPTY — the seller's drop directory
outputs/booth/          {NUM}-{slug}-booth.md + booth-tag-ledger.md
outputs/pixiv/          {NUM}-{slug}-pixiv.md + pixiv-tag-ledger.md
outputs/creative-fabrica/ {NUM}-{slug}-cf.md
```

Post-workflow, inside `visuals/New-Images/`: `source/3x2`, `source/1x1`,
`main/`, `squares/`, `final-image-manifest.md`.

**Archived and reinstatable, with guides:** `archive/video/` (showcase videos),
`archive/pinterest/` (panel composition), `archive/skills-legacy/font-workflow/`
(superseded two-pass pipeline), `archive/opencode/` (the full 31-agent registry).

---

## 9. Commands

| Command | Runs |
|---|---|
| `/full-workflow` | agents 27 → 13 → 20 → 22 → 29 |
| `/font-images` | agent 27 alone |
| `/font-prep` | agent 13 alone |
| `/booth-font`, `/cm-font`, `/creative-fabrica-font` | one listing agent alone |
| `/font-final-images` | agent 30, outside the workflow |

Registered in both harnesses: `.omp/agents` + `.omp/commands` for oh-my-pi, and
`opencode.json` for opencode. Both carry the same seven agents and seven
commands.
