---
description: Run the active sequential font launch workflow through preparation, BOOTH, Pixiv, and Creative Fabrica. Marketore, YellowImages, and DLsite are paused.
---

Dispatch the registered FontFairy task agent `full-workflow` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path. 
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the full-workflow agent with the exact font workspace directory, old font description, and any factual constraints supplied here. If the user supplied a new font name, pass it through; if not, Agent 27 decides the final name itself under its Naming policy (name-uniqueness research is forbidden). Execute visual generation, continuous font preparation (packages, both videos), BOOTH, Pixiv, and Creative Fabrica strictly sequentially, one registered agent at a time, waiting for each final result. Do not invoke Marketore, YellowImages, DLsite, X, or font-final-visual-processor, and never claim any publication or upload: $@
