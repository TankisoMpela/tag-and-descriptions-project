---
description: "Run the Etsy PowerPoint & Presentation Template Listing, Description & Tags Specialist on a presentation product."
argument-hint: "product facts or workspace path"
---

# /etsy-powerpoint

Delegate the task below to the **`etsy-powerpoint-specialist`** subagent defined in `.claude/agents/etsy-powerpoint-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the etsy-powerpoint-specialist agent to generate an optimized Etsy listing for this PowerPoint/presentation template product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.