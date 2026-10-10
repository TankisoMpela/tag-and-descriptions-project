---
description: "Run the complete unified Procreate brush workflow: prepare visuals, then Creative Market, Cubebrush, and MasterBundles sequentially."
argument-hint: "product facts or workspace path"
---

# /all-brushes

Delegate the task below to the **`all-brushes-workflow`** subagent defined in `.claude/agents/all-brushes-workflow.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the all-brushes-workflow agent for this exact Brush-Factory product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.