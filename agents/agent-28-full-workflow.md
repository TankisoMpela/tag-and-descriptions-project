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

For a new launch, prefer an exact source folder or staged workspace supplied
by the user. If none is supplied, dispatch Agent 27 in auto-random source mode;
its first operation is `python3 bin/stage_saved_font.py --random`. That helper
randomly chooses one eligible folder directly inside `font-factory/Saved/`,
moves only its root-level original OTF/TTF files into a fresh
`font-factory/fonts/{input-slug}/`, records hashes, and returns the selected
folder and staged path. Do not ask the user to choose or stage multiple
families. If the user names an exact Saved folder, stage only that folder with
`python3 bin/stage_saved_font.py --source "<exact-folder>"`. Nested repairs and
output files are not source fonts. If the user asks to resume a family already
staged in `font-factory/fonts/`, use that exact folder without moving or
copying another source. For an unspecified new launch, require Agent 27's
`RANDOM_SOURCE_CLAIMED` result from its own `--random` invocation before it
continues. If it cannot claim a fresh source, stop that run; do not adopt a
workspace another concurrent run may be using.

Preserve any user-supplied final name, description, and factual constraints.
When the final name or product description is not supplied, Agent 27 derives
them from the source metadata, mapped-glyph specimen, and facts. Do not use
uniqueness research or the namemaker agent. Once a name is decided, preserve
its exact spelling and derive one shared slug.

Compute one new unified product number from the highest numeric prefix across
existing `outputs/*/*.md` listing files plus one, as specified in `AGENTS.md`.
Do not inspect font packages, source folders, or images to determine the number.
Pass the same number and slug to Creative Market and Creative Fabrica.

## Required sequence

Run each child through the current runtime's native agent mechanism, strictly
one at a time. Wait for the child's final result and verify its expected output
before dispatching the next stage:

1. Agent 27 — visual handoff and four generated thumbnails (`font-image-generator` / `font_image_generator`)
2. Agent 13 — package and preparation (`font-prep-specialist` / `font_preparer`)
3. Agent 2 — Creative Market (`cm-fonts-specialist` / `cm_fonts_specialist`)
4. Agent 29 — Creative Fabrica (`creative-fabrica-fonts-specialist` /
   `creative_fabrica_fonts_specialist`)
5. Agent 30 — final image processing (`font-final-visual-processor` /
   `font_final_visual_processor`), when the image readiness check passes.

Never launch later work concurrently, by shell orchestration, or before the
prior child's final response. If a child fails, is blocked, omits its required
path, or returns incomplete, stop and report the exact stage, status, first
blocker, and safe resume point.

Agent 27 generates the four final thumbnails from the matching `theme.txt`
prompts and lettering specimens during stage 1. Agent 13 installs those four
images and all 24 support renders into the preparation folder. After Agent 29
passes, run `bin/check_new_images.py` on that folder. If both named thumbnail
pairs, image ratios, and the minimum 3:2 pool are ready, dispatch Agent 30 as stage 6 and
wait for its `COMPLETE` manifest. If readiness fails, report the exact missing
or invalid image input and the safe resume point; do not ask the seller to
generate the already-authorized thumbnails manually.

## Stage handoffs

### 1. Agent 27 visual handoff

Read `agents/agent-27-font-image-generator.md` and
`agents/reference/AGENTS-annex-visual-handoff.md`. Pass any exact source path,
user-supplied final name and description, and only relevant facts. If the user
did not supply a source, explicitly tell Agent 27 to start in auto-random mode;
it chooses and stages one Saved family before running its metadata and specimen
review. Agent 27 records the font's vibe in `font_profile.personality` and its
factual description in `font_profile.product_description` after reviewing the
complete mapped-glyph atlas and verified metadata. Require the exact marker
`READY FOR FONT PREP HANDOFF`, the final name, the exact `prepared_visuals/`
path, selected source folder, exact staged workspace path, and a successful
visual handoff validation, including its source-name carry-through check.
Require `name_origin: "user_supplied"` only when the caller explicitly gave
the final name; otherwise require a distinct agent-selected name. Confirm that
the handoff path belongs to the staged
workspace and that its `final-thumbnails/` directory contains all four prompt-
paired outputs before continuing.

Agent 27 writes its structured `visual-direction/visual-plan.json`, clean name
lettering references, matching prompts and four final thumbnails, plus 12
support layouts at both ratios.
Pinterest template pins are retired. Factual specimen previews are
retired from Agent 27; Agent 13 renders the canonical sheets from the font.
Read `font_name`, `font_profile.type_label`, `font_profile.subtext`,
`font_profile.product_description`, and `verified_product_facts` from the
validated plan. These are the downstream handoff facts; do not ask another
agent to restate or infer them. For Creative Market and Creative Fabrica, pass
the source description as factual grounding, not copy to paste: each specialist
writes two or three concise, natural prose paragraphs, followed by separate
What's Included, Features, and Software Compatibility bullets. The copy never
needs padding to hit a word target.

### 2. Agent 13 preparation

Read `agents/agent-13-font-prep-specialist.md`. Invoke it in
`FULL WORKFLOW CONTINUOUS MODE` with the exact source folder, final name,
product description, unified number, and Agent 27's validated handoff path and
profile. Agent 13 packages and audits the font, writes the exact product
description to `outputs/font-preparation/{NUM}-{slug}/description.txt`,
installs the 24 Agent-27 support images and four generated thumbnails for Agent
30, skips retired Pinterest template pins, and renders four factual specimen
sheets. It does not inspect, alter, or process the artwork. Showcase video
rendering is archived and is not part of this stage.

Before continuing, confirm the preparation output path exists, the child
reported successful package validation, and `description.txt` matches the
plan's `product_description` exactly. Confirm all 24 support images and four
specimen sheets through the preparation report/validator. Agent 13 leaves the
seller's final-art drop folder ready; Agent 30 is a separate post-workflow
stage.

### 3–4. Marketplace listings

Read each active listing agent's canonical spec and the listing-specific scope
annex in `agents/reference/AGENTS-annex-listing.md`. Pass the verified name,
slug, unified number, preparation output path, source product description as
factual grounding, `verified_product_facts`, and only the technical facts
reported by Agent 13.
Keep unknown product facts explicitly unknown. Do not ask listing agents to
inspect font binaries, image pixels, licenses, or package contents. Pass the
Agent-13 audit's exact OTF/TTF/WOFF files and per-format style counts, plus
verified family styles, tested features, character coverage, and software
compatibility evidence. Listing agents may state Canva's documented upload
support for OTF/TTF/WOFF on eligible plans as a platform capability, not as a
product-specific upload test.

2. Agent 2 Creative Market: one bounded per-font research pass and verified
   product facts; historical local listings are optional writing references.
3. Agent 29 Creative Fabrica Fonts: about 30 relevant tags (up to 40) using exact routes and comparable Designer Tags evidence.

Each marketplace agent must return its validated output path and completion
status before the next is dispatched. Stage 6's Agent-30 handoff is the exact
`outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/` folder. Both
thumbnail pairs and all 24 support images must be present and pass the readiness
check. Agent 30 retains both pairs by name in the final JPEG sets, then writes
ten Pinterest composites and `final-image-manifest.md`.
Confirm `COMPLETE` before reporting the workflow done. Do not claim an upload
or publication.

## Paused and post-workflow stages

Pixiv, X, Marketore, YellowImages, DLsite, Cubebrush, Etsy, Behance, Pinterest,
and all other marketplace agents are not part of `/full-workflow`. Agent 30 is
stage 6 and remains independently invocable for previously prepared products.
Agent 31 `font-rights-researcher`, the Pinterest preparer, and the daily
Pinterest runner remain standalone workflows.

## Runtime ID map

| Runtime | Agent 27 | Agent 13 | Agent 2 | Agent 29 | Agent 30 |
|---|---|---|---|---|---|---|
| Codex | `font_image_generator` | `font_preparer` | `cm_fonts_specialist` | `creative_fabrica_fonts_specialist` | `font_final_visual_processor` |
| OpenCode / OMP / Qwen | `font-image-generator` | `font-prep-specialist` | `cm-fonts-specialist` | `creative-fabrica-fonts-specialist` | `font-final-visual-processor` |

For Qwen, dispatch named agents in the foreground with
`run_in_background: false`. Every runtime's full-workflow registration must
read this contract and use only its native delegation mechanism.

## Completion report

Return a concise stage-by-stage report with each child's final status and exact
output path. Report paused agents as `PAUSED — not delegated`. Do not claim any
marketplace listing was uploaded or published. Agent 13's summary must confirm
the four copied thumbnails and 24 support images. Report Agent 30's JPEG
counts, size exceptions, ten Pinterest panels, manifest path, and completion
status. Do not describe thumbnail generation as a seller step.
