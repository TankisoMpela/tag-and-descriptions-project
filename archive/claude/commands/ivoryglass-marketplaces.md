---
description: "Run the IvoryGlass marketplace sequence: BOOTH, Cubebrush, YellowImages, then Marketore, strictly one at a time."
argument-hint: "product facts or workspace path"
---

# /ivoryglass-marketplaces

Delegate the task below to the **`ivoryglass-marketplace-workflow`** subagent defined in `.claude/agents/ivoryglass-marketplace-workflow.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the ivoryglass-marketplace-workflow agent for the font product IvoryGlass. Use OpenCode's native registered-agent delegation mechanism with the exact specialist IDs and run strictly one at a time: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.