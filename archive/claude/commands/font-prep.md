---
description: "PaperMoon font preparation in two passes: first metadata/packages, then the explicit prevalidated Agent-27 visual handoff."
argument-hint: "product facts or workspace path"
---

# /font-prep

Delegate the task below to the **`font-prep-specialist`** subagent defined in `.claude/agents/font-prep-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the font-prep-specialist agent with this exact instruction: $ARGUMENTS. Agent 27 must already have produced the prepared_visuals handoff. On the first pass, finish metadata/packages and stop; only process images when the input explicitly says to continue/resume and provides the exact prepared_visuals directory.
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.