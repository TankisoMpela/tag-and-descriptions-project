---
description: Run the Etsy Listing, Description & Tags Specialist on a product.
---

Dispatch the registered FontFairy task agent `etsy-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the etsy-specialist agent to generate an optimized Etsy listing for this product: $@