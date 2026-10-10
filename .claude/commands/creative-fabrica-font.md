---
description: "Run the Creative Fabrica Font Listing and SEO Research Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /creative-fabrica-font

Delegate the task below to the **`creative-fabrica-fonts-specialist`** subagent defined in `.claude/agents/creative-fabrica-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the creative-fabrica-fonts-specialist agent to generate a Creative Fabrica Fonts listing with a product title of no more than 30 characters, never adding the category word font/fonts, exactly 40 researched tags, live category/tag/PDP evidence, and clearly labelled engagement and purchase signals: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.