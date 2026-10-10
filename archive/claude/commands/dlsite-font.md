---
description: "Run the DLsite Font Listing and SEO Research Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /dlsite-font

Delegate the task below to the **`dlsite-fonts-specialist`** subagent defined in `.claude/agents/dlsite-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the dlsite-fonts-specialist agent to generate a Japanese-first DLsite listing with the confirmed ツール/アクセサリ work format, selected genres, keyword block with evidence, JPY pricing, and promotion plan: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.