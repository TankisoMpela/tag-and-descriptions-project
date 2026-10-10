> **HISTORICAL ARCHIVE — DO NOT FOLLOW.** This is the pre-consolidation AGENTS.md,
> kept only so no rule text was lost. It describes the old two-pass font-prep visual
> handoff, which no longer exists: agent 27's `prepared_visuals/` are drafts that stay in
> `font-factory/`, agent 13 leaves an empty `visuals/New-Images/` drop directory, and the
> seller's own images are processed by `/font-final-images` (agent 30). Always follow
> `AGENTS.md` and the agent specs instead of this file.

# Tag & Description Project — Master Workspace & Agent Execution Guide

This document defines the unified workspace structure, product numbering convention, platform constraints, tag count tracking, and output file management for all registered marketplace and portfolio-marketing agents.

---
## 🚧 LISTING-AGENT SCOPE (NON-NEGOTIABLE)

This scope applies to marketplace listing and SEO agents (Agents 1–11, 15–17, and 20). It does not apply to the dedicated preparation, naming, visual-prep, portfolio-marketing, or workflow-orchestration agents.

Listing agents are copy-and-research specialists only. Their job is to research marketplace SEO language and produce the requested title, description, tags/keywords, and platform-required SEO meta fields.

- Use the user-supplied product description and facts as the primary source of truth. Listing agents may read relevant local product files, README/facts sheets, description documents, filenames, or existing listing text when that helps gather factual details for the copy. They should not systematically inspect the product or enumerate files for QA.
- Do not technically inspect, validate, or cross-check raw product files, ZIP/package contents, fonts, brush files, images, previews, metadata, dimensions, licenses, provenance, AI status, or upload requirements for completeness, correctness, packaging, or marketplace readiness. Reading relevant files for factual copy input is allowed.
- Do not run Fontspector, `validate_*` scripts, package/file/asset QA, image inspection, manifests, or any product-file validation. Do not reopen a generated listing to cross-validate the product.
- Do not produce category/taxonomy, attributes, materials, pricing, license, media/alt-text, AI-content, packaging, or upload guidance unless the user explicitly requests that field.
- Keep research focused on competitor titles/descriptions/tags, autocomplete/search language, and other SEO evidence. Validate only copy-level SEO constraints that are necessary for the requested title, description, and tags.
- If required product facts are missing from the supplied description, first read relevant local documentation or product files that may contain the fact. If it is still missing, ask one concise question or mark it as unknown; never invent it.

Preparation and visual agents remain responsible for technical/file/asset QA. Listing agents must not duplicate that work.

---
## ⚡ FAST REVENUE PIPELINE (PRO-ONLY DEFAULT MODE)

To maximize launch speed and conserve computational tokens/API resources during initial batch font releases:

- **Default Pipeline (Zero Listing Fees)**: User chooses the font name. Agent 27 first authors and validates the bespoke visual handoff, Agent 13 then runs the metadata/package pass followed by explicit visual-handoff processing, and the completed package proceeds to **strictly sequential marketplace delegation**: BOOTH paid listing (Agent 20) => Marketore (Agent 24) => YellowImages (Agent 23). Agent 13 does not create a dedicated YellowImages image set; YellowImages uses the approved 3:2 visuals. Creative Market Agent 2, MasterBundles Agents 8/17, Cubebrush Agent 9, Pixiv Agent 22, Behance Agent 21, and Pinterest Agent 10 remain explicit-request only. Never dispatch stages concurrently; wait for each active stage before starting the next. (Etsy Agent 6 is omitted to avoid listing fees; DaFont/FontSpace Agent 11 is omitted to save tokens).
- **Default Package Copies**: Agent 13 writes font binaries into a folder named after the font, never `pro/`, then creates `{Font-Name}-Commercial-Use.zip` and `{Font-Name}-Personal-Use.zip` (both clean; Personal-Use may add a like-request note) plus `{Font-Name}-Free-Trial-Demo.zip` (FontFairy demo stamp on digits + ASCII punctuation). All archives contain only the same font folder and OTF, TTF, WOFF, and WOFF2 files; `description.txt` remains at the preparation output root and is never packaged.
- **DaFont/FontSpace Activation**: Agent 11 and DaFont/FontSpace listing metadata remain explicit-request only. Creating the default Personal Use archive copy does not automatically run the freemium listing workflow.
- **BOOTH Scope**: Agent 20 creates paid BOOTH storefront listings only. It does not create Pixiv posts, free demos, freemium conversion experiments, or automatic BOOTH uploads.

## 🖼️ PIXIV FONT FUNNEL WORKFLOW (EXPLICIT ONLY)

Agent 22 is paused from the default font workflow. When explicitly requested,
it is a discovery and view-oriented Pixiv Illustration package, not an upload
agent or a second storefront. It uses Japanese-first declarative presentation,
up to 10 Pixiv tags, approved image filenames, and the exact public BOOTH item
URL so Pixiv can attach its native BOOTH product widget. It prepares three
distinct angles—style showcase, lettering/typography showcase, and factual
use-case showcase—unless the user requests fewer.

## 🖼️ BEHANCE FONT PROJECT WORKFLOW (PAUSED)

Agent 21 is paused from the default workflow. It remains available through
the explicit `behance-font` command for a future user-requested run. It is not
a Pixiv-post agent and does not upload or publish on the user's behalf.

1. When explicitly requested, it runs after Agents 2, 8, 9, and 20 have completed for the same product number.
2. When explicitly requested, it researches Behance's current Popular Search Terms, Typography gallery, project-search language, and comparable font projects using Firecrawl for page retrieval, Serper/Exa for discovery, and one-time WebFetch fallback when Firecrawl rate-limits or fails.
3. It prepares a paste-ready project title, Creative Fields, up to 10 project tags, description, cover recommendation, individual image order, image tags, alt text, manual publishing steps, and a canonical Creative Market/BOOTH CTA.
4. It keeps the default sale mode as `EXTERNAL_LINK`. Native Behance asset-sale fields are prepared only when the user explicitly requests that mode and supplies the price/license decisions.
5. It does not inspect image pixels, validate dimensions, inspect packages, verify licenses, or claim that a Behance project was published. Those remain upstream or seller-side responsibilities.

## 🏷️ CREATIVE MARKET FONT CLASSIFICATION

Agent 2 must include the single primary Creative Market font category selected
from the current editor choices shown by the user:

`Blackletter` · `Handwritten` · `Sans Serif` · `Script` · `Serif` · `Slab Serif` · `Symbols`

This is a classification field, not a free-form tag. Do not select `Display` or
`Monospace` for this field unless the user supplies an updated editor taxonomy.
If the product facts do not support one of the seven choices, mark the field
`[CATEGORY NEEDS USER CONFIRMATION]` instead of inventing a category. Express
secondary qualities such as display, futuristic, or monospace through the
title, description, style filters, and tags only when supported.

## 🖼️ BESPOKE FONT IMAGE HANDOFF

Agent 27 (`font-image-generator`) runs before Agent 13. Its dedicated
thumbnail and supporting-image skills derive the visual concept, copy,
background, contrast, effects, and ratio-specific layouts from the specific
font. It authors a cohesive phrase/concept ledger, `theme.txt`,
`visual-plan.json`, and image notes, then creates a fast mechanical
text-placeholder handoff and the two factual specimen families. It reviews
the handoff with deterministic machine QA only (the agent has no vision or OCR
tool and never inspects rendered PNGs), and never claims placeholders are final
artwork. Final creative images are supplied later through the seller's manual
image-model workflow. It never modifies font binaries or claims an upload;
vision is never used and is never a dependency.

When the user does not supply a final font name, Agent 27 decides the best
evocative name from the description under its Naming policy; name-uniqueness
research and the namemaker agent are forbidden (uniqueness does not matter).

The required order is:
1. `/font-images` → phrase-led creative briefs, 4-8 supporting placeholders, four factual specimen PNGs, and `VISUAL-HANDOFF-READY.md`.
2. `/font-prep` → metadata/package pass only.
3. `/font-prep "continue visual handoff ... prepared visuals: ..."` → Agent 13 consumes and mechanically prepares Agent 27's completed handoff without inspecting image content.
4. Optional approved `thumbnail_pinterest.png` → `thumbnail_pinterest.png` (2:3, normally 1000x1500). If absent and Pinterest is explicitly requested, Agent 13 may mechanically compose Pinterest output from the completed 3:2 pool.

Run `/font-images` first with the raw font files, final name, description, and
font workspace. Wait for `READY FOR FONT PREP HANDOFF`. Then run `/font-prep` for
the metadata/package pass, followed by its explicit visual-handoff pass using
the exact `prepared_visuals/` path. Agent 13 consumes/copies the generated
3:2, 1:1, and specimen files, compresses creative images to `≤500 KB`,
mechanically composes a missing Pinterest image when requested, and never
creatively edits the source images.

For a single uninterrupted launch, use `/full-workflow` with the exact font
workspace directory, new name, and old description. It runs Agent 27, continuous
Agent 13, then BOOTH, Marketore, and YellowImages sequentially. Agent 13 does
not inspect image content in this mode and also creates the main `1920x1080`
showcase and Etsy `1920x960` 2:1 video plus its script.

## 🖌️ PROCREATE BRUSH LISTING WORKFLOW

Brushes use a unified paid-marketplace workflow. The user supplies the `.brushset`/`.brush` files, product facts, and approved images; the preparation agent only validates and mechanically derives marketplace assets and never rewrites brush files or creatively edits artwork.

1. Stage files in `brush-factory/brushes/{brush-slug}/source/`, `description.md`, and `prepared_visuals/`.
2. Run `/all-brushes brush-factory/brushes/{brush-slug}/`.
3. The workflow starts visual preparation and Creative Market (Agent 15) together, then delegates Cubebrush (Agent 16) and MasterBundles (Agent 17) sequentially.
4. Visual handoff files and mechanical derivatives land in `outputs/brush-preparation/{brush-slug}/`.
5. Listing outputs land in `outputs/brush-creativemarket/`, `outputs/brush-cubebrush/`, and `outputs/masterbundles/` with one shared product number.

There is no brush freemium, font preparation, Etsy, Pinterest marketing, or automatic marketplace upload stage in this workflow.

### Standalone BOOTH brush mode

When the user explicitly invokes `/booth-brush`, run the standalone
`booth-procreate-brushes-specialist` agent instead of the all-marketplace brush
workflow. It reads the user-supplied `description.md` and approved 3:2 images,
creates exact source copies plus compressed 3:2 JPEGs and padded square JPEGs
under `outputs/brush-preparation/{brush-slug}/`, then writes a Japanese-first
ordinary brush listing under `outputs/booth-brushes/`. It researches normal
brush sellers and buyer language, not Western-font positioning. It uses
exactly 30 live-evidence tags, frontloaded by strength, and creates a separate
BOOTH ZIP with a Japanese README pointing to
`https://papermoonstudio.booth.pm/`. It maintains a separate
`outputs/booth-brushes/booth-brush-tag-ledger.md`. It does not create Pinterest
assets, modify brush-file internals, upload to BOOTH, or claim publication.

## 🛒 MASTERBUNDLES GENERAL-PRODUCT WORKFLOW

Use the standalone `masterbundles-general-specialist` agent for any MasterBundles product that is not limited to the font workflow:

1. Run `/masterbundles-general` with the product facts, source folder, or existing package path.
2. The agent researches the live vendor form with Firecrawl plus the available search MCPs and, when authenticated, inspects the live category checkbox tree with `agent-browser` or Playwright.
3. It preserves the full parent-to-child category path across Add-ons, Crafters, Fonts, Freebies, Graphics, Stock Content, and Templates. The readable baseline is `agents/masterbundles-general-taxonomy.md`; live form data remains authoritative.
4. Output is written to `outputs/masterbundles/{NEXT_NUM}-{product-slug}-mb.md` with classification, properties, SEO, media requirements, and research notes. Credentials are never stored in the agent or listing files.


## 📁 WORKSPACE & OUTPUT DIRECTORY STRUCTURE

All generated marketplace listing copy and font preparation outputs live under `outputs/`:

```
tag-and-description-project/
├── font-factory/                       ← FONT INPUT, VISUAL-REFERENCE, PROMPT, AND PREPARATION WORKSPACE
│   ├── fonts/
│   │   └── {font-slug}/
│   │       ├── raw .otf/.ttf files
│   │       ├── visual-references/      ← original thumbnail/supporting images used to write prompt briefs
│   │       ├── visual-direction/       ← Agent 27 art direction, plan, and review
│   │       ├── visual-prompts/         ← supporting-image briefs and references
│   │       └── prepared_visuals/       ← Agent 27 creative and factual image handoff
│   │           ├── 3x2/                ← thumbnail_main.png and promo_N.png
│   │           ├── 1x1/                ← thumbnail_main.png, thumbnail_japanese.png, and promo_N.png
│   │           ├── specimens/          ← two factual specimen families per ratio
│   │           └── visual-handoff-manifest.md
│   ├── Style-References/               ← optional quality references for the Custom GPT
│   └── README.md
├── brush-factory/                     ← INPUT STAGING WORKSPACE (brush files + approved Custom GPT visuals)
│   └── brushes/{brush-slug}/           ← source/, description.md, prepared_visuals/, optional references/
├── outputs/                            ← ALL MARKETPLACE LISTING OUTPUTS
│   ├── font-preparation/               ← Agent 13 font-named packages, ZIP copies, and visual derivatives
│   ├── creativemarket/                 ← {NEXT_NUM}-{slug}-cm.md (30 tags, max 36 title, max 55 meta title, max 155 meta desc)
│   ├── etsy/                           ← {NEXT_NUM}-{slug}-etsy.md (13 tags, MAX 20 CHARS/TAG, max 140 title)
│   ├── masterbundles/                  ← {NEXT_NUM}-{slug}-mb.md (live taxonomy/property mapping, max 155 meta; paused by default)
│   ├── cubebrush/                      ← {NEXT_NUM}-{slug}-cb.md (20+10 tags, 300+ word desc, AI-content check)
│   ├── booth/                           ← {NEXT_NUM}-{slug}-booth.md (paid Japanese-first BOOTH listing, selective Japanese/English SEO terms, 10-18 validated live-evidence tags, JPY pricing, package/media/license checks)
│   ├── yellowimages/                    ← {NEXT_NUM}-{slug}-yellowimages.md (Creative Store font listing, exactly 30 canonical-first researched tags and category; uses approved 3:2 visuals)
│   ├── marketore/                       ← {NEXT_NUM}-{slug}-marketore.md (Marketore Fonts listing, exactly 10 captured-vocabulary tags, evidence, compatibility, and observed price tiers)
│   ├── pixiv/                            ← {NEXT_NUM}-{slug}-pixiv.md (three Japanese-first view-oriented posts, up to 10 tags each, BOOTH CTA, image order, research)
│   │   └── pixiv-tag-ledger.md           ← persistent Pixiv discovery-life evidence, rejected terms, and confidence tiers
│   ├── behance/                         ← {NEXT_NUM}-{slug}-behance.md (project title, fields, tags, description, image metadata, CTA, research)
│   ├── pinterest/                      ← {NEXT_NUM}-{slug}-pin.md (4 Pin packages, exact product URL, max 100 title, max 800 desc, max 500 alt)
│   ├── dafont-fontspace/               ← {NEXT_NUM}-{slug}-freemium.md (13-30 tags, commercial readme)
│   ├── font-names/                     ← {NEXT_NUM}-{slug}-name-report.md (user-supplied name lock)
│   ├── brush-creativemarket/           ← {NEXT_NUM}-{slug}-cm-brush.md (30 tags, max 36 title, max 55 meta, max 155 desc)
│   ├── brush-cubebrush/                ← {NEXT_NUM}-{slug}-cb-brush.md (20+10 terms, 300+ word desc, AI-content check)
│   ├── booth-brushes/                  ← {NEXT_NUM}-{slug}-booth-brush.md (ordinary Japanese-first brush copy, exactly 30 live-evidence tags)
│   │   └── booth-brush-tag-ledger.md   ← persistent BOOTH brush activity and rejection ledger
│   ├── brush-preparation/              ← mechanically prepared brush 3:2 JPEGs, padded square JPEGs, Japanese README, BOOTH ZIP, and manifests
│   └── ...                             ← additional listing outputs
├── agents/                             ← Specialized Agent Instruction Specs
├── bin/                                ← search.js validation CLI
└── opencode.json                       ← Agent registry & execution commands
```

---

## 🔢 UNIFIED PRODUCT NUMBERING ALGORITHM (`{NEXT_NUM}`)

Every product processed in the pipeline receives a **unified numeric ID** (`{NEXT_NUM}`) that is shared across all platform outputs for that product.

### How Agents Determine `{NEXT_NUM}`:

1. **Existing Product Lookup (Cross-Platform Alignment)**:
   - When an agent is called to generate a listing for an existing product (e.g. generating Etsy listing for product `#3`), the agent may use an explicitly supplied prior listing filename or product number to preserve alignment. Listing agents must not scan or open product packages, source folders, or assets to determine numbering.
   - Maintain the exact same number and slug across all platform output files!

2. **New Product Generation**:
   - If generating a new product from scratch, the agent scans the target `outputs/{platform}/` folder for existing numeric file prefixes (`[0-9]*.md`).
   - Extract the highest existing numeric prefix (`MAX_NUM`). If no files exist, set `MAX_NUM = 0`.
   - Set `NEXT_NUM = MAX_NUM + 1`.
   - Use this `{NEXT_NUM}` prefix for all platform output files created during the run (e.g., `1-vellum-cm.md`, `1-vellum-etsy.md`, `1-vellum-mb.md`, `1-vellum-cb.md`, `1-vellum-pin.md`).

---

## 📊 PLATFORM CONSTRAINT MATRIX (TAGS, CHARACTERS & VALIDATION)

Listing agents may enforce only the title, description, tag, and SEO-text constraints relevant to the copy they are producing. Product/file/asset, package, upload, license, media, and AI-content checks belong to preparation or visual agents and must not be duplicated here.

| Platform | Code | Output File Pattern | Tag Count | Tag Length Limit | Title Limit | Meta Title Limit | Meta Desc Limit | Special Rules & Mandatory Constraints |
|---|---|---|---|---|---|---|---|---|
| **Creative Market** | `cm` | `outputs/creativemarket/{NUM}-{slug}-cm.md` | **Exactly 30** | None | **Max 36 chars** | **Max 55 chars** | **Max 155 chars** | Generate all three SEO fields plus one primary classification from the seven current editor choices; every tag 2+ words, no banned mechanical tags, ordered by weighted suggest score |
| **Etsy** | `etsy` | `outputs/etsy/{NUM}-{slug}-etsy.md` | **Exactly 13** | **MAX 20 CHARS** | Max 140 chars | N/A | Max 155 chars | **STRICT HARD LIMIT: Every tag $\le 20$ chars.** Title primary keyword in first 40 chars |
| **MasterBundles** | `mb` | `outputs/masterbundles/{NUM}-{slug}-mb.md` | Live category/property controls | None | Product-specific, minimum 5 letters | N/A | Max 160 chars | Use exact live nested category paths; do not invent free-form tags or flatten repeated labels. Include asset specs and format breakdown |
| **Cubebrush** | `cb` | `outputs/cubebrush/{NUM}-{slug}-cb.md` | **20 + 10** | None | Under 100 chars (60-80 ideal) | N/A | Max 155 chars | Public brush listings commonly use Tools; font listings may appear under Other. Use only current Basic/Commercial/Studio license choices exposed by the editor. **AI-CONTENT CHECK mandatory** (AI-labeled products may be hidden). Cover text centered in middle 60% (thumbnails center-crop). 300+ word description recommended. |
| **BOOTH** | `booth` | `outputs/booth/{NUM}-{slug}-booth.md` | **10-18 validated tags** (target 15; fail closed below 10 or above 18) | None publicly documented | Target approximately 80 chars; verify live editor | N/A | N/A | Paid Digital item under visible `Source Materials` (select a font child only when exposed), Japanese-first native title/description with selective English SEO terms, live tag evidence with numeric counts + provider + date, buy-intent hook description, JPY pricing, exact package/license facts, first image as thumbnail, attached Digital File, and recorded proxy/overseas setting. Tag set combines the font-clear family (pages dominated by fonts: フォント・書体・オリジナルフォント・タイポグラフィ・font-family styles) with the high-volume buyer-intent family (商用利用可能・テロップ・ロゴ・サムネイル・レトロ・ポップ), which substitutes for the lower-value font-clear filler. When requested, include named `Commercial Use` and `Personal Use` variants, explain both, and set Personal Use lower but not automatically free. No Pixiv posts or automatic upload. |
| **BOOTH Brushes** | `booth-brush` | `outputs/booth-brushes/{NUM}-{slug}-booth-brush.md` | **Exactly 30** | None publicly documented | Approximately 80 chars; verify live editor | N/A | N/A | Standalone ordinary Procreate-brush copy plus mechanical image handoff and separate Japanese-README BOOTH ZIP; Japanese-first title/plain-text description, normal brush-market tags, live exact-tag/category/page-life evidence, compressed 3:2 and padded square JPEGs, no upload claim. |
| **YellowImages** | `yellowimages` | `outputs/yellowimages/{NUM}-{slug}-yellowimages.md` | **Exactly 30 workflow tags** | No public author limit documented | Target approximately 45–80 chars; verify Creative Store editor | N/A | N/A | Creative Store > Fonts copy package. Frontload relevant exact terms from the public YellowImages Tags/category pages, then use researched supplemental terms. The 30-tag block is a workflow contract, not a claim that YellowImages accepts exactly 30. Image creation, derivatives, dimensions, and upload readiness remain with Font Prep/seller-side workflow; no upload claim. |
| **Marketore** | `marketore` | `outputs/marketore/{NUM}-{slug}-marketore.md` | **Exactly 10** | Exact strings from captured 4,353-tag vocabulary | Target approximately 45–90 chars; no stable live hard limit observed | N/A | N/A | First description sentence is meta/OG/Twitter/JSON-LD; main category must be `Fonts`, one observed subcategory, tags weighted by fit plus catalog coverage/saturation/opportunity, observed Personal/Commercial/Extended price ratios |
| **Pixiv** | `pixiv` | `outputs/pixiv/{NUM}-{slug}-pixiv.md` | Up to 10 per work | None documented | No stable documented cap | N/A | N/A | Illustration discovery/funnel package; three distinct post angles, Japanese-first declarative captions, comma-separated tags, exact public BOOTH item URL/widget CTA, approved image order, AI-setting recommendation, provider research notes; no upload claim. |
| **Behance** | `behance` | `outputs/behance/{NUM}-{slug}-behance.md` | Up to 10 project tags; up to 10 image tags per image | None documented beyond the count caps | No stable documented title cap | N/A | N/A | Post-marketplace project package: required Creative Field, readable description, individual image sequence, cover handoff, image tags/alt text, research notes, and external CTA by default. Native asset-sale fields are opt-in; no upload claim. |
| **Pinterest** | `pin` | `outputs/pinterest/{NUM}-{slug}-pin.md` | Up to 10 related topics per Pin | None | Max 100 chars | N/A | N/A | Exactly 4 intent-separated Pin packages using `pinterest_1.png`–`pinterest_4.png`; all links must be the exact Creative Market product page; description max 800 chars; alt text max 500 chars |
| **Personal Use** | `fm` | `outputs/dafont-fontspace/{NUM}-{slug}-personal-use.md` | **13–30** | None | N/A | N/A | N/A | Copy the main font files unchanged; include a Japanese TXT README in the ZIP explaining Personal Use, use cases, software installation, restrictions, and the Commercial Use path. No glyph subsetting or demo renaming. |
| **Font Prep** | `prep` | `outputs/font-preparation/{slug}/` | N/A | N/A | N/A | N/A | N/A | User-supplied name; font-named binary folder; clean Commercial Use ZIP + clean Personal Use ZIP + demo-stamped Free-Trial-Demo ZIP; root-level unbundled description; mechanical copies of Agent-27's prevalidated 3:2 and 1:1 sources including `thumbnail_japanese.png`; full-dimension JPEG copies targeting ≤500 KB in `visuals/main/` and `visuals/squares/`; approved 3:2 visuals are reused for YellowImages; four Pinterest derivatives in `visuals/pinterest/` only when requested; main 1920x1080 and Etsy 1920x960 videos plus Etsy script; metadata |
| **Creative Market Brushes** | `cm-brush` | `outputs/brush-creativemarket/{NUM}-{slug}-cm-brush.md` | **Exactly 30** | None | **Max 36 chars** | **Max 55 chars** | **Max 155 chars** | Listing-only agent; reads Brush-Factory source and approved visuals; content disclosure required |
| **Cubebrush Brushes** | `cb-brush` | `outputs/brush-cubebrush/{NUM}-{slug}-cb-brush.md` | **20 + 10** | None | Under 100 chars | N/A | N/A | Listing-only agent; current public brush listings use Tools/Software Brushes/Procreate labels; **description body must be plain text for direct Cubebrush paste** (internal output may remain `.md`); Basic/Commercial/Studio only when exposed; **AI-CONTENT CHECK mandatory**; cover text in middle 60% |

---

## 🏷️ TAG TRACKING & COUNTING RULES

1. **Marketplace-specific discovery**:
   - For marketplaces with a documented or tested suggestion surface, run `node bin/search.js [--marketplace "marketplace"] --batch "tag1,tag2,..."` and apply that marketplace's evidence rules.
   - For BOOTH, Google Suggest is Japanese query-language seed discovery only. The `--marketplace "booth"` option prefixes the query; it is not BOOTH autocomplete and its count must not be called BOOTH search volume.
   - BOOTH tags require live public-page validation through the exact-tag route and the `フォント・書体` category route, followed by a page-life check for active relevant listings. Treat 0 relevant font-category listings as dead/no coverage, 1–16 as low activity to record and deprioritize, and 17+ as the basic activity threshold; if only visible cards are available, record the lower bound and do not infer a total. Record overall exact-tag count, font-category count, activity status, and rejected/dead/low-activity candidates in `outputs/booth/booth-tag-ledger.md` as coverage/activity signals, not demand volume.
   - Every selected BOOTH tag must also carry an evidence row with the exact-tag URL, font-category URL, paid-product count, distinct-seller count, activity/provider status, evidence tier, and product-fit reason. Do not count the current product, previous PaperMoon products, or the seller's own shop as independent competitor repetition.
   - Before live BOOTH research, the BOOTH agent must read existing `outputs/booth/*.md` listing files (excluding `booth-tag-ledger.md`) to build the PaperMoon-owned product registry. Filter those product names/slugs and the PaperMoon shop/seller pages before fetching; record owned results as skipped and never use them as competitor, repetition, paid-product, distinct-seller, or activity evidence.
   - Beyond the first five or six core tags, BOOTH requires a deliberate expansion pass across language-plus-object, style-plus-object, use-case-plus-object, commercial-rights, format/purchase-intent, English equivalents, and exact-tag intersection candidates. A low count is not automatically good or bad: select an expansion tag only when its exact route, font-category relevance, paid-product evidence, and product fit survive; otherwise keep it as a keyword phrase or ledger rejection. Test repeated `tags[]` intersections without treating an AND result as proof of a new compound tag. Do not use `フリーフォント` for a paid-only product without a confirmed free version.
   - Standalone BOOTH brush mode uses the same exact-tag, relevant-category, page-life, paid-product, and seller-diversity checks, but its category and candidates must come from normal brush listings rather than `フォント・書体`. It must give Japanese-only, English-only, and mixed candidates equal validation effort, including supported terms such as `brushset`, `brush set`, `stamps`, and `stamp brush`; language does not disqualify a tag. Record 0 as dead/no coverage, 1–16 as low activity, and 17+ as basic activity. Store rejected and low-activity brush terms in `outputs/booth-brushes/booth-brush-tag-ledger.md`; do not mix them with the font ledger.
   - Authenticated BOOTH editor observation (2026-08-19): the `add Tag` field provides autocomplete for some terms but also permits a typed custom tag through an explicit Enter action. Autocomplete presence is not marketplace activity evidence, and autocomplete absence is not rejection; both require the public exact-tag/category/page-life checks. No visible numeric tag counter or maximum was exposed on the inspected editor page.
   - Pinterest keyword discovery may use `node bin/search.js` and available search MCPs as language proxies, but returned suggestions/counts must never be labeled Pinterest search volume. Record the official Pinterest source URLs, the exact product-page destination, and the intent phrase assigned to each of the four Pins.
   - Pixiv discovery must use exact/current tag or search routes plus fetched relevant works. Record the candidate term, tag/use status, visible relevant-work lower bound, distinct creators, newest relevant date when exposed, provider/fallback, product fit, and Tier A/B/C or REJECT decision in `outputs/pixiv/pixiv-tag-ledger.md`; snippets and visible views are not Pixiv demand or sales evidence.
   - YellowImages discovery must use the live public Tags directory, Fonts category, relevant style collection, and comparable Creative Store font PDPs. The Tags directory is canonical vocabulary evidence and buyer-facing SEO infrastructure, not a documented closed author tag list. Frontload relevant exact YellowImages terms, fill the requested 30-tag block with evidence-backed supplemental terms, and record canonical/supplemental status for every tag. Do not call YellowImages tag presence search volume or sales evidence.
   - Marketore discovery must read `outputs/research/marketore-font-seo-research.md` and the complete `outputs/research/marketore-tags-vocabulary.json` capture first, then refresh the public Fonts browse page, at least three relevant PDPs, and exact style/use-case search pages. Treat vocabulary counts as product adoption and public search counts as catalog coverage/competition, never as demand or sales. Final tags must be exactly 10 unique strings from the captured vocabulary, with a row recording vocabulary count, search supply when available, comparable products/sellers, saturation band, fit, and decision for every selected tag. Use Firecrawl for all unique page URLs; use Serper/Exa for discovery and WebFetch once for a rate-limited or failed Firecrawl URL, recording the complement and limitation.
2. **Tag Formatting**:
   - For marketplaces with valid suggestion scoring, order tags descending by the marketplace's suggest score. For BOOTH, order by product fit, live evidence tier, comparable paid-product repetition, and font-category coverage instead.
   - Remove duplicate root words (synonym clustering).
   - Cap leading-word repetitions at a maximum of 3 tags starting with the same word.
3. **Strict Verification Check**:
   - Before writing the file, count the final tags list. If count $\neq$ required count (e.g. not 30 for CM, not 20+10 for Cubebrush, not 13 for Etsy), fix the list before outputting.
   - BOOTH has no stable documented public tag cap, but this workflow targets **10-18 validated, non-redundant live-confirmed tags** (aim for 15); the listing fails closed (reports BLOCKED) if fewer than 10 or more than 18 can be defended, rather than padding. The set combines the **font-clear family** from the latest research — tags whose unfiltered result pages are dominated by fonts (フォント 3,078, 書体 1,263, フォント・書体 1,428, オリジナルフォント 1,076, タイポグラフィ 636, デザインフォント 311, 欧文フォント 143, and font-family styles such as サンセリフ/カリグラフィ which are >85% font-share) — with the **high-volume buyer-intent / use-case family** (商用利用可能, 商用可, テロップ, ロゴ, サムネイル, レトロ, ポップ, ヴィンテージ) that has broad, font-relevant coverage even when its page is Materials-mixed. The buyer-intent family substitutes for the lower-value font-clear filler (e.g. 明朝, 丸文字, 装飾フォント) that has tiny volume. Prefer font-clear tags as the anchor; also spend a tag slot on the higher-volume intent terms that are genuinely font-relevant, and keep leftover use-case words in the description (BOOTH indexes description text). Frontload by strength and treat English tags as equal candidates when exact BOOTH evidence, font-category relevance, and product fit support them. Record the live cap if exposed and provide an evidence row for every selected tag. Every final candidate must also pass a live page-life check through Firecrawl first; if Firecrawl rate-limits or fails, use WebFetch once and Serper/Exa to discover a current alternate URL, recording the actual provider and limitation. Do not pad with generic web phrases, near-synonym category words, or present them as confirmed BOOTH tags.
   - **Mandatory BOOTH validation gate**: after writing `outputs/booth/{NUM}-{slug}-booth.md`, the agent MUST run `python bin/validate_booth_listing.py outputs/booth/{NUM}-{slug}-booth.md` from the project root. The listing is NOT complete until the validator prints `[PASS]` (exit 0). Every `[FAIL]` must be resolved and the validator re-run until it passes. The validator is fail-closed (exit 1 on any failure) and enforces the 10-18 validated-tag contract (target 15), evidence-URL decoding, numeric counts, provider+date+activity status cells, the max-3 low-activity-exception cap, stale-evidence warnings, and sibling-advisory overlap checks when `--booth-dir` is supplied. Hand-checking is not a substitute. Copy-level only; it never inspects product files, packages, images, licenses, pricing, or upload readiness.
   - Pinterest is not a fixed tag-count marketplace: use up to 10 accurate related topics per Pin, keep hashtags optional and sparse, and validate exactly four distinct Pin sections with identical product-specific destination URLs.

## 💰 RECOMMENDED PRICING IN LISTING FILES

Pricing is out of scope for listing agents by default. Do not read `outputs/pricing-reference.md` or add pricing, licensing, packaging, or upload sections unless the user explicitly requests them.

- **Reference Source**: Font agents read `outputs/pricing-reference.md` to pull recommended baseline and promotional prices for Desktop, Webfont, App, E-Pub, and Commercial licenses based on product type (Single Font, Font Duo, or Full Family).
- **Listing Markdown Inclusion**:
  - Creative Market: `## RECOMMENDED PRICING (from outputs/pricing-reference.md)` listing Desktop, Webfont (10k/100k), App, and E-Pub tiers.
  - Etsy: `## RECOMMENDED PRICING (from outputs/pricing-reference.md)` listing Digital Download Commercial Price ($4.99–$9.99).
  - MasterBundles: `## RECOMMENDED PRICING (from outputs/pricing-reference.md)` listing Commercial License & Promo prices.
  - Cubebrush: `## RECOMMENDED PRICING (from outputs/pricing-reference.md)` listing Single ($3-8), Duo/Family ($9-18), and Bundle ($15-29) prices.
  - BOOTH: `## RECOMMENDED PRICING (from outputs/pricing-reference.md)` listing the paid JPY tier, the current `5.6% + ¥45` fee formula, and approximate net before currency conversion.
---

## 🌐 WEB RESEARCH FETCH POLICY

For every batch of unique page URLs:

- Use `firecrawl_firecrawl_scrape` as the primary page-content provider for
  every de-duplicated URL. Never have more than **6 Firecrawl calls in flight
  at once**. Split larger URL sets into sequential batches of at most six,
  wait for each batch to finish, record its results, and only then start the
  next batch.
- Use `serper_serper_search` for high-recall discovery, URL replacement, and
  query-language expansion when Firecrawl rate-limits or when a page URL must
  be rediscovered. If Serper is unavailable, use Exa or another available
  search MCP and record that substitution.
- If Firecrawl rate-limits or fails for a URL, use the configured `webfetch`
  tool once for that URL. Do not repeatedly retry Firecrawl, and do not call
  Crawl4AI for current agent research.
- When a research set is larger than six URLs, use Serper/Exa alongside the
  Firecrawl batches for discovery and URL expansion; do not turn the larger
  set into one oversized Firecrawl burst.
- Search snippets discover URLs and wording; they do not prove page content,
  tag counts, activity, or sales. Record one row per URL in `RESEARCH NOTES`
  with Firecrawl status, complement provider, actual content provider, status,
  and fallback/limitation.

## 📓 OBSIDIAN VAULT INTEGRATION

When marketing listing packages or master font packages are completed, and only when the user explicitly requests this:
1. Save master copy to `~/Documents/Obsidian Vault/Product Listings/{FontName}-Master.md`.
2. Format with Wikilinks (`[[Creative Market Listing]]`, `[[MasterBundles Listing]]`, `[[Cubebrush Listing]]`, `[[BOOTH Listing]]`, `[[Behance Project]]`, `[[Pinterest Campaign]]`).
3. Optionally trigger Obsidian URI focus:
   `xdg-open "obsidian://open?vault=Obsidian%20Vault&file=Product%20Listings/{FontName}-Master"`
