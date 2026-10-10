---
description: Run the IvoryGlass marketplace sequence: BOOTH, Cubebrush, YellowImages, then DLsite, strictly one at a time.
---

Dispatch the registered FontFairy task agent `ivoryglass-marketplace-workflow` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the ivoryglass-marketplace-workflow agent for the font product IvoryGlass. Use OpenCode's native registered-agent delegation mechanism with the exact specialist IDs and run strictly one at a time: $@