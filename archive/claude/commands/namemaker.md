---
description: "Run the NameMaker Font Naming & Uniqueness Specialist on a font description/image."
argument-hint: "product facts or workspace path"
---

# /namemaker

Delegate the task below to the **`namemaker-specialist`** subagent defined in `.claude/agents/namemaker-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the namemaker-specialist agent to generate and verify a unique font name for this font product: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.