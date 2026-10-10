---
description: "Run the FontFairy font image generator before font preparation. It creates a fast mechanical text-placeholder handoff, plans 3:2 and 1:1 outputs, and leaves a strict Agent-13 handoff. Final artwork replacement is a separate optional seller step."
argument-hint: "product facts or workspace path"
---

# /font-images

Delegate the task below to the **`font-image-generator`** subagent defined in `.claude/agents/font-image-generator.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the registered font-image-generator agent before font preparation. Use the exact font workspace, product description, and optional factual references supplied here. When the user supplies a final font name, use it exactly; when not, decide the best evocative name yourself under the agent's Naming policy and never run name-uniqueness research. Create the deterministic text-placeholder handoff with short, font-specific copy, canonical filenames, factual specimens, and mechanical validation. Do not use OpenPencil, image-generation tools, visual inspection, or OCR, and do not invoke font-prep automatically. Finish with READY FOR FONT PREP HANDOFF and the exact prepared_visuals path: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.