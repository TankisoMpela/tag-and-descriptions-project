---
description: "Run the active font workflow sequentially: BOOTH, Marketore, then YellowImages. Creative Market, MasterBundles, Cubebrush, Pixiv, Behance, and Pinterest are paused."
argument-hint: "product facts or workspace path"
---

# /all-fonts

Delegate the task below to the **`all-fonts-workflow`** subagent defined in `.claude/agents/all-fonts-workflow.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the all-fonts-workflow agent for this font product. Use the registered in-session agent mechanism with the exact specialist IDs, strictly waiting for each active stage before starting the next; leave Creative Market, MasterBundles, Cubebrush, Pixiv, Behance, and Pinterest paused: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.