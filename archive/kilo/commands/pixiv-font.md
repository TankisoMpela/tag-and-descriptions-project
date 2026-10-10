---
description: Run the Pixiv Font Discovery & BOOTH Funnel Specialist on a font product after the BOOTH listing.
---

Dispatch the registered FontFairy task agent `pixiv-fonts-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the pixiv-fonts-specialist agent using the frozen Pixiv discovery bank to generate one paste-ready Japanese-first Illustration post package with exactly 10 consolidated tags and one declarative description that funnels to the exact BOOTH item URL. Use the permanent paid copy state (NORMAL_PAID) by default for this new font; switch to aggressive/front-loaded free-headline copy only when a free/trial campaign has been explicitly reactivated with real scope and dates/trigger: $@