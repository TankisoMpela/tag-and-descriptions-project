---
description: Run the Behance Font Portfolio, Discovery & Asset Listing Specialist on a font product after the marketplace stages.
---

Dispatch the registered FontFairy task agent `behance-fonts-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the behance-fonts-specialist agent to generate a paste-ready Behance project package for this font product: $@