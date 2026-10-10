---
description: Run the active font workflow sequentially: BOOTH, DLsite, then YellowImages. Creative Market, MasterBundles, Cubebrush, Pixiv, Behance, and Pinterest are paused.
---

Dispatch the registered FontFairy task agent `all-fonts-workflow` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the all-fonts-workflow agent for this font product. Use the registered in-session agent mechanism with the exact specialist IDs, strictly waiting for each active stage before starting the next; leave Creative Market, MasterBundles, Cubebrush, Pixiv, Behance, and Pinterest paused: $@