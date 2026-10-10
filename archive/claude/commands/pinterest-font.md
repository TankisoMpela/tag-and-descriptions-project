---
description: "Run the Pinterest Font Traffic & SEO Specialist to generate a four-Pin package for a font product."
argument-hint: "product facts or workspace path"
---

# /pinterest-font

Delegate the task below to the **`pinterest-fonts-specialist`** subagent defined in `.claude/agents/pinterest-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the pinterest-fonts-specialist agent to generate a four-Pin Pinterest traffic package for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.