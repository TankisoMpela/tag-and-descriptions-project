---
description: Run the NameMaker Font Naming & Uniqueness Specialist on a font description/image.
---

Dispatch the registered FontFairy task agent `namemaker-specialist` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the namemaker-specialist agent to generate and verify a unique font name for this font product: $@