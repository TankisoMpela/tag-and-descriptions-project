---
name: agent-28-full-workflow
description: Runtime-neutral contract for the five-stage sequential font launch workflow.
---

# Full Font Launch Orchestrator

This file is the single source of truth for `/full-workflow` across the project
agent runtimes. Runtime registrations may translate agent IDs and delegation
syntax, but they must preserve this stage order, handoffs, stop conditions, and
scope. Read `AGENTS.md` and `font-factory/AGENTS.md` first, then this contract
and the active specialist specs it names. The orchestrator coordinates; it does
not perform a child agent's work.

## Source selection and shared product number

For a new launch, the source family must be selected from `font-factory/Saved/`.
If the user has not named one exact Saved folder, run
`python3 bin/stage_saved_font.py --list` and ask them to choose; do not guess,
stage every folder, or inspect unrelated font collections. After selection,
stage only that folder's original root-level OTF/TTF files with
`python3 bin/stage_saved_font.py --source "<exact-folder>"`. Pass the resulting
`font-factory/fonts/{input-slug}/` path to Agent 27. Nested repairs and output
files are not source fonts. If the user explicitly asks to resume a family
already staged in `font-factory/fonts/`, use that exact staged folder without
moving or copying another source.

Preserve any user-supplied final name, description, and factual constraints.
When the final name or product description is not supplied, Agent 27 derives
them from the source metadata, mapped-glyph specimen, and facts. Do not use
uniqueness research or the namemaker agent. Once a name is decided, preserve
its exact spelling and derive one shared slug.

Compute one new unified product number from the highest numeric prefix across
existing `outputs/*/*.md` listing files plus one, as specified in `AGENTS.md`.
Do not inspect font packages, source folders, or images to determine the number.
Pass the same number and slug to BOOTH, Creative Market, and Creative Fabrica.

## Required sequence

Run each child through the current runtime's native agent mechanism, strictly
one at a time. Wait for the child's final result and verify its expected output
before dispatching the next stage:

1. Agent 27 — visual handoff (`font-image-generator` / `font_image_generator`)
2. Agent 13 — package and preparation (`font-prep-specialist` / `font_preparer`)
3. Agent 20 — BOOTH (`booth-fonts-specialist` / `booth_fonts_specialist`)
4. Agent 2 — Creative Market (`cm-fonts-specialist` / `cm_fonts_specialist`)
5. Agent 29 — Creative Fabrica (`creative-fabrica-fonts-specialist` /
   `creative_fabrica_fonts_specialist`)

Never launch later work concurrently, by shell orchestration, or before the
prior child's final response. If a child fails, is blocked, omits its required
path, or returns incomplete, stop and report the exact stage, status, first
blocker, and safe resume point.

## Stage handoffs

### 1. Agent 27 visual handoff

Read `agents/agent-27-font-image-generator.md` and
`agents/reference/AGENTS-annex-visual-handoff.md`. Pass the exact staged source
folder, any user-supplied final name and description, and only relevant facts.
Agent 27 inspects the font metadata and complete mapped-glyph specimen before
deciding an unsupplied name or profile. Require the exact marker
`READY FOR FONT PREP HANDOFF`, the final name, the exact `prepared_visuals/`
path, and a successful visual handoff validation. Confirm that path belongs to
the selected source workspace before continuing.

Agent 27 writes its structured `visual-direction/visual-plan.json`, clean name
specimens and matching prompts, the required 3:2 and square support layouts,
four factual specimen previews, and the active Pinterest template renders.
Read `font_name`, `font_profile.type_label`, `font_profile.subtext`,
`font_profile.product_description`, and `verified_product_facts` from the
validated plan. These are the downstream handoff facts; do not ask another
agent to restate or infer them.

### 2. Agent 13 preparation

Read `agents/agent-13-font-prep-specialist.md`. Invoke it in
`FULL WORKFLOW CONTINUOUS MODE` with the exact source folder, final name,
product description, unified number, and Agent 27's validated handoff path and
profile. Agent 13 packages and audits the font, writes the exact product
description to `outputs/font-preparation/{NUM}-{slug}/description.txt`,
installs the verified 23 Agent-27 Pinterest template pins, and renders four
factual specimen sheets. It does not inspect or copy thumbnail/support-layout
drafts or process the seller's final images. Showcase video rendering is
archived and is not part of this stage.

Before continuing, confirm the preparation output path exists, the child
reported successful package validation, and `description.txt` matches the
plan's `product_description` exactly. Confirm the 23 template pins and four
specimen sheets through the preparation report/validator. Agent 13 leaves the
seller's final-art drop folder ready; Agent 30 is a separate post-workflow
stage.

### 3–5. Marketplace listings

Read each active listing agent's canonical spec and the listing-specific scope
annex in `agents/reference/AGENTS-annex-listing.md`. Pass the verified name,
slug, unified number, preparation output path, exact product description,
`verified_product_facts`, and only the technical facts reported by Agent 13.
Keep unknown product facts explicitly unknown. Do not ask listing agents to
inspect font binaries, image pixels, licenses, or package contents.

1. Agent 20 BOOTH: default campaign is `FREE_ACTIVE`; preserve any user-supplied
   campaign timing or scope. Freeze already-fetched tag evidence if a prior or
   interrupted run collected it, so evidence is not fetched twice.
2. Agent 2 Creative Market: one bounded per-font research pass and verified
   product facts; historical local listings are optional writing references.
3. Agent 29 Creative Fabrica Fonts: the current 40-tag evidence contract.

Each marketplace agent must return its validated output path and completion
status before the next is dispatched. Do not claim an upload or publication.

## Paused and post-workflow stages

Pixiv, X, Marketore, YellowImages, DLsite, Cubebrush, Etsy, Behance, Pinterest,
and all other marketplace agents are not part of `/full-workflow`. Agent 30
`font-final-visual-processor`, Agent 31 `font-rights-researcher`, the Pinterest
preparer, and the daily Pinterest runner remain standalone workflows.

## Runtime ID map

| Runtime | Agent 27 | Agent 13 | Agent 20 | Agent 2 | Agent 29 |
|---|---|---|---|---|---|
| Codex | `font_image_generator` | `font_preparer` | `booth_fonts_specialist` | `cm_fonts_specialist` | `creative_fabrica_fonts_specialist` |
| OpenCode / OMP / Qwen / Claude | `font-image-generator` | `font-prep-specialist` | `booth-fonts-specialist` | `cm-fonts-specialist` | `creative-fabrica-fonts-specialist` |

For Qwen, dispatch named agents in the foreground with
`run_in_background: false`. Every runtime's full-workflow registration must
read this contract and use only its native delegation mechanism.

## Completion report

Return a concise stage-by-stage report with each child's final status and exact
output path. Report paused agents as `PAUSED — not delegated`. Do not claim any
marketplace listing was uploaded or published. Agent 13's summary must confirm
the 23 checked template pins. Tell the user the final image artwork remains a
separate seller step and `/font-final-images` runs after those files are added.
