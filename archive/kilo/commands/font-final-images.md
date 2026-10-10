---
description: Run the standalone post-workflow final font image processor on a seller-created visuals/New-Images folder.
---

Dispatch the registered FontFairy task agent `font-final-visual-processor` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the font-final-visual-processor agent after all font preparation, videos, and requested marketplace work are complete. Use the exact font-preparation output directory and the raw visuals/New-Images folder supplied here. Identify the supplied 3:2 and 1:1 thumbnails, preserve the user's promo order, then run bin/process_final_font_images.py to create exact source copies, <=200 KB main/square JPEG delivery files, and four <=700 KB 1000x1500 Pinterest PNGs with the Pillow-only cached compositor. Before recomposition, reuse Pinterest outputs only when their dimensions, byte limits, and manifest source-hash/options fingerprint are unchanged; invoke pngquant only for over-limit PNGs and emit no Pinterest JPEG companions unless explicitly requested. Write final-image-manifest.md inside New-Images. Do not alter raw images, old visuals/main or visuals/squares folders, font files, metadata, or videos; do not invoke full-workflow and make no upload claim: $@