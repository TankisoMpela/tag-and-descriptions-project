---
description: Run the complete unified Procreate brush workflow: prepare visuals, then Creative Market, Cubebrush, and MasterBundles sequentially.
---

Dispatch the registered FontFairy task agent `all-brushes-workflow` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the all-brushes-workflow agent for this exact Brush-Factory product: $@