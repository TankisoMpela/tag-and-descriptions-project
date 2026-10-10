---
description: "Run the PowerPoint/Presentation Description & Tags Specialist on a product."
argument-hint: "product facts or workspace path"
---

# /cm-powerpoint

Delegate the task below to the **`cm-powerpoint-specialist`** subagent defined in `.claude/agents/cm-powerpoint-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the cm-powerpoint-specialist agent to generate an optimized PDP for this presentation template product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.