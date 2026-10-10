---
description: "Run the PaperMoon font image generator before font preparation. It authors bespoke font-specific artwork rather than choosing a repository template, plans 3:2 and 1:1 independently, allows ambitious treatments when they serve the font, uses optional variants only for real uncertainty, checks contrast and purposeful copy, and leaves a strict Agent-13 handoff."
argument-hint: "product facts or workspace path"
---

# /font-images

Delegate the task below to the **`font-image-generator`** subagent defined in `.claude/agents/font-image-generator.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the registered font-image-generator agent before font preparation. Use the exact font workspace, product description, and optional visual references supplied here. When the user supplies a final font name, use it exactly; when not, decide the best evocative name yourself under the agent's Naming policy and never run name-uniqueness research. Author a bespoke visual direction from the actual font and buyer use; do not force templates, a fixed candidate set, or a fixed promo sequence. Create custom artwork directly for 3:2 and 1:1, use real glyph outlines for prominent lettering, make the colors work against each other, include purposeful typography, and include at least two concrete end-use contexts plus one believable functional result when the font's supported use cases make them appropriate. Use OpenPencil as the design source of truth and scripts only for mechanical rasterization/specimens/validation, do not invoke vision/OCR or font-prep automatically, and finish with READY FOR FONT PREP HANDOFF and the exact prepared_visuals path: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.