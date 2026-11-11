---
description: Run Agent 30 standalone for an older prepared font; new full-workflow products run it automatically after listings when image inputs pass readiness.
---

Dispatch the registered FontFairy task agent `font-final-visual-processor` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the font-final-visual-processor agent for the supplied older prepared product. Follow `agents/agent-30-font-final-visual-processor.md` and use its named thumbnail pair and exact input requirements; do not use vision to identify a thumbnail. Create exact source copies, optimized JPEG delivery files, transparent PNG Pinterest composites, and `final-image-manifest.md` inside `New-Images`. Do not alter raw images, font files, or metadata; do not invoke full-workflow and make no upload claim: $@
