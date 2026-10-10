---
description: "Run the General Description & Tags Specialist on any Creative Market product."
argument-hint: "product facts or workspace path"
---

# /cm-general

Delegate the task below to the **`cm-general-specialist`** subagent defined in `.claude/agents/cm-general-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the cm-general-specialist agent to generate an optimized PDP for this product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.