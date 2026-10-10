# Legacy font-visual renderers (archived)

Retired on 2026-09-21. These six scripts formed the OpenPencil-era renderer
cluster for Agent 27's handoff:

| Script | Why retired |
|---|---|
| `render_openpencil_font_handoff.mjs` | Drives `@open-pencil/core`. OpenPencil is not installed in this environment (no binary, no npm global), so it cannot run. |
| `compile_openpencil_jsx.mjs` | OpenPencil source compiler; same dependency. |
| `openpencil_eval.sh` | Wrapper around the OpenPencil evaluator; same dependency. |
| `rasterize_font_visual_handoff.py` | OpenPencil-primary (`render_mode: openpencil`) rasterizer. |
| `generate_font_visual_handoff.py` | Documents itself as an older compatibility renderer; calls the rasterizer above. |
| `render_font_thumbnail_candidates.py` | Documents itself as superseded: "must not be used to choose a new font's creative direction". |

Agent 27's active path is the **text-placeholder** handoff rendered by
`bin/generate_font_text_placeholders.py`, validated by
`bin/validate_font_visual_handoff.py` (which still accepts the `openpencil` and
`svg` render modes for older handoffs, so restoring any of these files is safe).

Nothing in `agents/`, `.omp/`, or `AGENTS.md` referenced any of these scripts.
Restore with `git mv archive/bin-legacy-renderers/<file> bin/` if a legacy
handoff ever needs re-rendering.
