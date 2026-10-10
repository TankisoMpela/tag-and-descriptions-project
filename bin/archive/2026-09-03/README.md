# Archived scripts — 2026-09-03

These scripts had **zero references** anywhere in the repo (`AGENTS.md`,
`agents/*.md`, skills, opencode/codex configs) and no cross-imports from the
active pipeline. They are one-off, per-font or generic utilities that were
superseded by the OpenPencil render bridge
(`bin/render_openpencil_font_handoff.mjs`) and the dedicated validators.

They are archived (not deleted) so they can be restored if a specific font
needs to be re-produced with the original tooling.

| File | What it did |
|---|---|
| `prepare_cavero.py` | One-off font-prep packaging for the Cavero font. |
| `prepare_avelisse.py` | One-off font-prep packaging for the Avelisse font. |
| `prepare_vantrelle.py` | One-off font-prep packaging for the Vantrelle font. |
| `run_visual_handoff_cavero.py` | One-off visual-handoff runner for Cavero. |
| `run_visual_handoff_avelisse.py` | One-off visual-handoff runner for Avelisse. |
| `allocate_research_batch.py` | Generic Firecrawl-safe URL batching utility (≤6 in flight). |
| `optimize_png_lossless.py` | Generic lossless PNG re-encode helper. |

If you restore one, drop it back into `bin/` and remove its README row here.
