---
description: "Run the Cubebrush Font Listing, Description & Tags Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /cb-font

Delegate the task below to the **`cubebrush-fonts-specialist`** subagent defined in `.claude/agents/cubebrush-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the cubebrush-fonts-specialist agent to generate an optimized Cubebrush font listing for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.