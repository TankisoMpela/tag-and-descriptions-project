---
description: "Run the YellowImages Creative Store Font Listing Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /yellowimages-font

Delegate the task below to the **`yellowimages-fonts-specialist`** subagent defined in `.claude/agents/yellowimages-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the yellowimages-fonts-specialist agent to generate an optimized YellowImages Creative Store font listing with exactly 30 canonical-first researched tags: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.