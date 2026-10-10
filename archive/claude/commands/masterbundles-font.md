---
description: "Run the MasterBundles Font Listing, Description & Tags Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /masterbundles-font

Delegate the task below to the **`masterbundles-fonts-specialist`** subagent defined in `.claude/agents/masterbundles-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the masterbundles-fonts-specialist agent to generate an optimized MasterBundles font listing for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.