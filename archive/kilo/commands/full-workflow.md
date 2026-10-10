---
description: Run the active sequential font launch workflow through preparation, BOOTH, Pixiv, and Creative Fabrica. X, DLsite, and YellowImages are paused.
---

Dispatch the registered FontFairy task agent `full-workflow` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the full-workflow agent with the exact font workspace directory plus the old product description or a public product URL (exactly one of the two is required: product URL "product url: [url]", or description "description: [text]"), and any factual constraints supplied here. Do NOT supply a font name, a Supporting-image theme sentence, or per-image theme variants: Agent 27 decides them. Execute naming, provisional visual handoff, continuous font/package/video preparation, BOOTH, Pixiv, and Creative Fabrica strictly sequentially. Do not delegate X, DLsite, or YellowImages. Pixiv is a fast copy-only handoff using frozen local research. Copy Agent 27's four factual specimen PNGs unchanged, do not process creative marketing images, and do not invoke font-final-visual-processor. The public BOOTH item URL is optional during preparation; use LINK REQUIRED until available: $@
