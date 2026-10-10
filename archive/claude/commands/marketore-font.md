---
description: "Run the Marketore Font Listing and SEO Research Specialist on a font product."
argument-hint: "product facts or workspace path"
---

# /marketore-font

Delegate the task below to the **`marketore-fonts-specialist`** subagent defined in `.claude/agents/marketore-fonts-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the marketore-fonts-specialist agent to generate a Marketore listing with exact Fonts taxonomy, exactly 10 canonical vocabulary tags, evidence-led weighting, a meta-safe first sentence, compatibility, and observed price tiers: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.