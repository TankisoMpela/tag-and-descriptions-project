---
description: Run the FontFairy font image generator before font preparation. Agent 27 authors the phrase-led theme.txt, visual-plan.json, image notes, provisional text-placeholder handoff, and four factual specimen families for 3:2 and 1:1. It decides the final font name only when the user supplied none, validates with deterministic machine QA only (no vision, no OCR), and leaves a strict mechanical Agent-13 handoff. The later manual image-model pass is the source of final creative artwork.
---

Dispatch the registered FontFairy task agent `font-image-generator` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved output file with `[PASS]`/success status, report its path.
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the registered font-image-generator agent before font preparation. Use the exact font workspace and product description. This agent has no vision/OCR, so do not request or depend on local reference images. When the user supplies a final font name, use it exactly and skip naming research; when not, decide the best evocative name under the agent's Naming policy. Derive a short phrase/concept ledger first: normally 1–4-word promo headlines, varied buyer jobs, phrase meaning, visual metaphor/world, verified font behavior, physical event, artwork, placement, and ratio-specific crop. Write theme.txt, notes, and visual-plan.json from that same ledger so they stay cohesive. Do not force templates or a fixed candidate set. Use scripts only for mechanical placeholder rasterization, specimens, and validation; do not invoke vision/OCR or font-prep automatically. Finish with READY FOR FONT PREP HANDOFF and the exact prepared_visuals path: $@
