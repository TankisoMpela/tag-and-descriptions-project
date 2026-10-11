---
description: "FontFairy font preparation — package, audit and lay out the font, then hand off the specimen set."
argument-hint: "product facts or workspace path"
---

# /font-prep

Delegate the task below to the **`font-prep-specialist`** subagent defined in `.claude/agents/font-prep-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the font-prep-specialist agent with this exact instruction: $ARGUMENTS. Finish the font metadata, package/archive copies, technical audit, and the factual-specimen handoff. Treat Agent-27 prepared_visuals as deferred for creative artwork: do not copy, compress, rename, inspect, or compose any thumbnail, supporting promo, or video asset from them. Then run Step 2: write pins.brief.json with five fresh headlines in five colour worlds and render it with bin/render-pins. Copy only the four named factual specimen PNGs unchanged from prepared_visuals/specimens/3x2/ and prepared_visuals/specimens/1x1/ into the numbered output's specimens/ folders. Leave visuals/New-Images/ empty for the seller's own artwork, apart from the pinterest/ pins you rendered.
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.