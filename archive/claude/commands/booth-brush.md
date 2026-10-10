---
description: "Run the standalone BOOTH Procreate brush preparation and SEO listing specialist."
argument-hint: "product facts or workspace path"
---

# /booth-brush

Delegate the task below to the **`booth-procreate-brushes-specialist`** subagent defined in `.claude/agents/booth-procreate-brushes-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the booth-procreate-brushes-specialist agent for this Brush-Factory product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.