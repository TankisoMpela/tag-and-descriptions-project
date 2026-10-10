---
description: Run the DaFont & FontSpace Freemium Conversion Specialist on a font product.
---

Dispatch the registered FontFairy task agent `freemium-fonts-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the freemium-fonts-specialist agent to generate optimized DaFont/FontSpace submission metadata and commercial license zip readme for this font product: $@