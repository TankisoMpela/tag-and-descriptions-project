---
description: FontFairy font preparation — package, audit and lay out the font, then hand off the specimen set.
---

Dispatch the registered FontFairy task agent `font-prep-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the font-prep-specialist agent with this exact instruction: $@. Finish the font metadata, package/archive copies, technical audit, and the factual-specimen handoff. Treat Agent-27 `prepared_visuals` as deferred for creative artwork: do not copy, compress, rename, inspect, or compose any thumbnail, supporting promo, video, or Pinterest asset. When the validated handoff is available, copy only the four named factual specimen PNGs unchanged from `prepared_visuals/specimens/3x2/` and `prepared_visuals/specimens/1x1/` into the numbered output's `specimens/` folders, record the source and destination paths, and never regenerate them. Leave an empty `visuals/New-Images/` drop directory for the seller. The separate `/font-final-images` command will process that folder after the workflow is finished.
