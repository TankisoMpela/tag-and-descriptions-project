---
description: "Run the DaFont & FontSpace Freemium Conversion Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /freemium-font

Delegate the task below to the **`freemium-fonts-specialist`** subagent defined in `.claude/agents/freemium-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the freemium-fonts-specialist agent to generate optimized DaFont/FontSpace submission metadata and commercial license zip readme for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.