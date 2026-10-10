---
description: Run the standalone post-workflow final font image processor on a seller-created visuals/New-Images folder.
---

Dispatch the registered FontFairy task agent `font-final-visual-processor` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the font-final-visual-processor agent after all font preparation and requested marketplace work are complete. Use the exact font-preparation output directory and raw `visuals/New-Images` folder supplied here. Do not use vision or determine which image is semantically a thumbnail. Run `bin/process_final_font_images.py --auto-order` so direct filenames are sorted independently within 3:2 and 1:1; the first in each ratio becomes `thumbnail_main` and the rest become `promo_1` upward. Create exact source copies and `<=200 KB` main/square JPEG delivery files, and write `final-image-manifest.md` inside `New-Images`. Do not alter raw images, old `visuals/main` or `visuals/squares` folders, font files, or metadata; do not invoke full-workflow and make no upload claim: $@
