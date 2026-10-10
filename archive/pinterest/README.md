# Pinterest image generation — ARCHIVED 2026-09-21

Archived because the workflow does not use Pinterest right now. Nothing here is
deleted: this is the complete, working capability, and the steps below put it
back exactly as it was.

## What is here

| File | Was at | Role |
|---|---|---|
| `compose_pinterest.py` | `bin/` | Composes 1000x1500 2:3 Pinterest panels by stacking 3:2 sources. Supports the multi-variant mode (`--variants`) and `--jpeg-companions`. |
| `validate_pinterest_listing.py` | `bin/` | Validates a Pinterest listing against the platform contract. |
| `process_final_font_images-pinterest-aware.py` | `bin/process_final_font_images.py` | The **full** Agent 30 processor as it existed with Pinterest support. This is the reinstatement reference: it contains the panel composition, the fingerprint cache, the format-aware delivery paths, the stale-format cleanup and the Pinterest manifest rows. |

## Why the snapshot exists

Pinterest was not a separable module. It was interleaved through
`process_final_font_images.py` — roughly 156 references across the constants,
seven helper functions, `main()` and `write_manifest()`. Rather than delete it
from the live processor and lose the shape of it, the live processor was reduced
to the delivery-only path (source copies, 3:2 / 1:1 separation, bounded JPEG
delivery, manifest) and this snapshot keeps the complete Pinterest-aware version.

## How to reinstate

1. **Restore the compositor and validator.**

   ```bash
   git mv archive/pinterest/compose_pinterest.py bin/compose_pinterest.py
   git mv archive/pinterest/validate_pinterest_listing.py bin/validate_pinterest_listing.py
   ```

2. **Restore the Pinterest-aware processor**, replacing the delivery-only one.

   ```bash
   git mv archive/pinterest/process_final_font_images-pinterest-aware.py \
          bin/process_final_font_images.py
   ```

   If the live processor has moved on since 2026-09-21 (new delivery rules, a
   changed manifest), do **not** overwrite it. Instead diff the two and port the
   Pinterest pieces across:

   ```bash
   diff -u bin/process_final_font_images.py \
           archive/pinterest/process_final_font_images-pinterest-aware.py
   ```

   The blocks to port are: the `PINTEREST_*` constants, the seven helpers
   (`encode_pinterest_jpeg`, `pinterest_output_paths`, `pinterest_delivery_paths`,
   `pinterest_outputs_status`, `pinterest_fingerprint`,
   `read_pinterest_fingerprint`, `pinterest_cache_hit`), the `--pinterest-*`
   arguments, the contiguous `main()` blocks, and the Pinterest section of
   `write_manifest()`.

3. **Restore the Agent 30 spec sections.** The live spec
   (`agents/agent-30-font-final-visual-processor.md`) had the Pinterest contract
   removed from its description, its compose step, its cache-validation step and
   its completion gate. Recover the original text with:

   ```bash
   git show <commit-before-2026-09-21>:agents/agent-30-font-final-visual-processor.md
   ```

4. **Add the command back** if you want a slash command for it. It was
   `.omp/commands/pinterest-compose.md` and an `opencode.json` entry
   `pinterest-compose`; the original opencode entry is preserved in
   `archive/opencode/opencode-full-31-agents.json`.

5. **Re-check the dependencies**: `pngquant` (lossy PNG fallback),
   `Pillow`, and the `compose_pinterest.select_variant_images` import that
   `process_final_font_images.py` makes at module level.

## Behaviour worth remembering

- Panels are photographic composites. Palette-quantised PNG at the 700 KB cap
  produced 667 KB at 256 colours; JPEG q95 produced 348 KB at full 24-bit
  colour, so **JPEG is the better deliverable** and became the default
  (`--pinterest-format jpeg`, with `png` keeping the old path).
- The cache is fingerprint-based and **format-aware**, so switching format is a
  cache miss rather than a false "already valid".
- Stale files in the other format are removed on every run, including on a cache
  hit — the cleanup must live outside the composition block or a cache hit
  leaves both formats behind.
