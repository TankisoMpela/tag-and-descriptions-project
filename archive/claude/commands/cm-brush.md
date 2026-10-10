---
description: "Run the Creative Market Procreate Brush Listing Specialist on a brush product."
argument-hint: "product facts or workspace path"
---

# /cm-brush

Delegate the task below to the **`cm-procreate-brushes-specialist`** subagent defined in `.claude/agents/cm-procreate-brushes-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the cm-procreate-brushes-specialist agent to generate an optimized Creative Market Procreate brush listing for this product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.