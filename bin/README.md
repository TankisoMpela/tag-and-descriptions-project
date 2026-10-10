# `bin/` — helper scripts index

This directory holds the mechanical helpers behind the font / brush / listing
pipeline. They fall into three groups. Everything here is tooling; listing
agents never call these as QA gates (see `AGENTS.md` listing-agent scope).

## Active (current pipeline)

| Script | Purpose |
|---|---|
| `search.js` | Marketplace suggestion-scoring CLI (`node bin/search.js --marketplace ... --batch ...`). |
| `generate_font_text_placeholders.py` | Fast mechanical white 3:2 / 1:1 text-placeholder handoff from the phrase-led visual plan. The current Agent-27 preparation path. |
| `render_openpencil_font_handoff.mjs` | Archived (OpenPencil not installed) — `archive/bin-legacy-renderers/`. |
| `openpencil_eval.sh` | Archived (OpenPencil not installed) — `archive/bin-legacy-renderers/`. |
| `compile_openpencil_jsx.mjs` | Archived (OpenPencil not installed) — `archive/bin-legacy-renderers/`. |
| `rasterize_font_visual_handoff.py` | Archived (OpenPencil-primary) — `archive/bin-legacy-renderers/`. |
| `validate_font_visual_handoff.py` | Validates a visual handoff manifest/contract (`--strict`). |
| `validate_font_factory.py` | Font-factory staging hygiene check (pathological space-joined slug + stray raster in font root). |
| `render_font_specimens.py` | Generates the factual specimen families for a handoff. |
| `prepare_font_package.py` | **Agent 13's whole mechanical pass in one command**: pre-flight audit, name table, OS/2 flags, OTF/TTF/WOFF/WOFF2, specimens, image drop directory, reports, all three delivery archives, the technical audit, and an OpenType Sanitizer pass over every delivered format as an independent second parser. An OTF (CFF) source is the master and the TTF is derived with fontTools `cu2qu`; a glyf-only source (the usual shape of a marketplace demo) keeps its quadratic outlines and hinting as the delivered TTF and gets its OTF master derived with fontTools `qu2cu`. Commercial-Use and Personal-Use ZIPs both carry the clean fonts; the Free-Trial-Demo ZIP is rebuilt from a stamped temp copy (digits + ASCII punctuation = FontFairy demo badge; letters clean). Only `description.txt` needs a human. |
| `stamp_personal_use.py` | Free-trial-demo font watermark: `outline` converts `font-factory/stamps/fontfairy-demo.svg` (text nodes) into path outlines via rsvg+potrace; `stamp` replaces digit/punctuation glyph outlines in OTF/TTF (WOFF/WOFF2 regenerated) with that badge. Invoked automatically by `prepare_font_package.py` when building the Free-Trial-Demo archive. |
| `package_font_archives.py` | Standalone Commercial + Personal + stamped Free-Trial-Demo ZIP builder for an already-prepared package folder (prefer `prepare_font_package.py` for new runs). `--no-stamp` skips the stamped Free-Trial-Demo archive. |
| `font_fact_sheet.py` | Prints the factual font sheet Agent 27 uses for art direction: metrics, character coverage, OpenType feature inventory, and the exact glyph sequence for proposed display copy (flags ligature/substitution glyph-count changes). Replaces the inline fontTools/uharfbuzz inspection the spec used to ask for. |
| `font_preflight_audit.py` | Read-only pre-flight audit of raw fonts (tables, UPM, fsType, glyph count, cmap, name IDs, GSUB/GPOS). Exits 1 only if a font is missing or unloadable. Replaces the inline snippet that used to live in the Agent-13 spec. |
| `font_cleaner.py` | Dry-run-first cleanup helper. Audits a directory without decompiling outlines, identifies unloadable/incomplete fonts, and with explicit `--apply` moves only those confirmed failures into a sibling `Fonts-Trash/` folder with a reversible JSON manifest. |
| `font_package_audit.py` | Technical audit of Pro (fsType 0) and Freemium (fsType 4) packages; exits 1 on any mismatch. Replaces the inline snippet in Agent 13 Step 6b. |
| `campaign_mode.py` | Shared free/paid campaign contract for the listing tools: the mode set, which modes carry a free/limited-time offer, the free-offer vocabulary legitimate only in those modes, the limited-time and like-CTA markers, and the mode parser. Imported by both listing validators, `booth_tag_evidence.py`, and `booth_tag_ledger.py`; the human-readable contract is `agents/reference/AGENTS-annex-listing.md`. |
| `validate_booth_listing.py` | BOOTH 18-25 tag fail-closed validator (target 20; sibling-advisory with --booth-dir). Campaign-aware: a free mode requires a `## CAMPAIGN STATE` section, a first-line free + limited-time offer, a like CTA, and at least one free-offer tag; `NORMAL_PAID` forbids free-offer tags. |
| `validate_booth_brush_listing.py` | BOOTH brush 30-tag validator. |
| `validate_cm_listing.py` | Creative Market listing validator. |
| `validate_marketore_listing.py` | Marketore listing validator. |
| `validate_yellowimages_listing.py` | YellowImages listing validator. |
| `validate_behance_listing.py` | Behance project validator. |
| `pixiv_tag_ledger.py` | Query and append the Pixiv tag ledger without reading it whole (mirrors `booth_tag_ledger.py`). `--check` answers "was this tag used before, and for which products" in ~30 tokens where reading the 12 KB ledger costs ~3,000; `--append --listing` takes the evidence table straight from the listing so the rows are written once, instead of being reprinted inside the listing as an appendix. |
| `validate_pixiv_listing.py` | Pixiv listing validator (fail-closed gate). Campaign-aware: a free mode requires `## CAMPAIGN STATE`, a caption first line carrying the free + limited-time offer, a like CTA anywhere in the caption, and at least one free-offer tag; `NORMAL_PAID` forbids free-offer tags. |
| `booth_tag_evidence.py` | Per-tag BOOTH census evidence gate (young-paid cohort) with `--top-lanes` discovery and `--free-lanes` free-cohort discovery; `--campaign` lifts the free-promo ban in a free mode and reports a free-cohort verdict. |
| `booth_tag_ledger.py` | Query/append the BOOTH tag ledger without reading it whole; `--campaign` reclassifies a paid-only free-tag rejection as `MODE-CONDITIONAL` for a free campaign. |
| `check_listing_description_plaintext.py` | Ensures a description body is plain text for direct marketplace paste. |
| `encode_main_jpeg.py` | JPEG encode targeting ≤500 KB for prepared visuals. |
| `package_booth_brush.py` | Builds the BOOTH brush ZIP + Japanese README. |
| `prepare_booth_brush_visuals.py` | Mechanical 3:2 / padded-square JPEG prep for brush visuals. |
| `create_marketplace_thumbnail.py` | Mechanical thumbnail derivation. |
| `stress_test_marketore.py` | Marketore research / catalog stress test. |
| `crawl4ai_fetch.py` | Crawl4AI page fetch fallback (used by agents as a complement provider). |
| `sec-scan` | Security scan wrapper script. |
| `magick7` | ImageMagick 7 wrapper. |
| `make_booth_trial_pdf.py` | One-page Japanese BOOTH trial-insert PDF (`--booth-url --trial-url --font-dir …`). Embeds the product font + `visuals/New-Images/squares` thumbnail, clickable trial/BOOTH links, headless Chromium print-to-pdf. No like-CTA in the PDF. |

## Legacy (kept for compatibility, superseded by the active placeholder handoff)

Retained so older handoffs authored via the legacy SVG / template raster path
can still be consumed. New Agent-27 work uses the mechanical placeholder
handoff; final creative artwork is supplied later by the seller/custom image
workflow.

| Script | Note |
|---|---|
| `generate_font_visual_handoff.py` | Archived (superseded compatibility renderer) — `archive/bin-legacy-renderers/`. |
| `render_font_thumbnail_candidates.py` | Archived (superseded) — `archive/bin-legacy-renderers/`. |

## Archived

See [`bin/archive/2026-09-03/README.md`](archive/2026-09-03/README.md) for the
one-off, per-font scripts that were removed from the active pipeline on
2026-09-03. Nothing in the active pipeline references them.

