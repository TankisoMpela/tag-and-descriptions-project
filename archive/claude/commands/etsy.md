---
description: "Run the Etsy Listing, Description & Tags Specialist on a product."
argument-hint: "product facts or workspace path"
---

# /etsy

Delegate the task below to the **`etsy-specialist`** subagent defined in `.claude/agents/etsy-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the etsy-specialist agent to generate an optimized Etsy listing for this product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.