---
description: "Run the active sequential font launch workflow through preparation, BOOTH, Pixiv, and Creative Fabrica. Marketore, YellowImages, and DLsite are paused."
argument-hint: "product facts or workspace path"
---

# /full-workflow

Delegate the task below to the **`full-workflow`** subagent defined in `.claude/agents/full-workflow.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the full-workflow agent with the exact font workspace directory, old font description, and any factual constraints supplied here. If the user supplied a new font name, pass it through; if not, Agent 27 decides the final name itself (name-uniqueness research is forbidden). Execute visual generation, continuous font preparation, BOOTH, Pixiv, and Creative Fabrica strictly sequentially. Do not delegate Marketore, YellowImages, or DLsite: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.
