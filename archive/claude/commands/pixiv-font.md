---
description: "Run the Pixiv Font Discovery & BOOTH Funnel Specialist on a font product after the BOOTH listing."
argument-hint: "product facts or workspace path"
---

# /pixiv-font

Delegate the task below to the **`pixiv-fonts-specialist`** subagent defined in `.claude/agents/pixiv-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the pixiv-fonts-specialist agent to generate three paste-ready Pixiv Illustration post packages that funnel to the exact BOOTH item URL: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.