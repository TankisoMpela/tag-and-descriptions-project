---
description: "Run the standalone MasterBundles General Product Specialist on any product."
argument-hint: "product facts or workspace path"
---

# /masterbundles-general

Delegate the task below to the **`masterbundles-general-specialist`** subagent defined in `.claude/agents/masterbundles-general-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the masterbundles-general-specialist agent to generate an optimized MasterBundles listing, live category path, properties, SEO, and upload checklist for this product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.