---
description: "Run the Behance Font Portfolio, Discovery & Asset Listing Specialist on a font product after the marketplace stages."
argument-hint: "product facts or workspace path"
---

# /behance-font

Delegate the task below to the **`behance-fonts-specialist`** subagent defined in `.claude/agents/behance-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the behance-fonts-specialist agent to generate a paste-ready Behance project package for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.