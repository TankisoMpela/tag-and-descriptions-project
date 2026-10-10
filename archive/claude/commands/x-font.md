---
description: "Run the standalone X Font Promotion & BOOTH Funnel Specialist on a font product; full-workflow may also invoke this same copy/research stage."
argument-hint: "product facts or workspace path"
---

# /x-font

Delegate the task below to the **`x-font-promotion-specialist`** subagent defined in `.claude/agents/x-font-promotion-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the x-font-promotion-specialist agent using the BOOTH copy, Demo scope, approved image filenames, and product-level BOOTH URL when available. Generate ONE Japanese-first post within 280 weighted characters, with zero to two hashtags, the exact BOOTH link, the Free Trial Demo announcement, and a direct like request before download. Keep Commercial Use paid. Use frozen local research only; do not browse, crawl, call MCP tools, or publish: $ARGUMENTS
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.
