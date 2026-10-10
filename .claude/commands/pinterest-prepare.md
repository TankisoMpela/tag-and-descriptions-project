---
description: "Register fonts for Pinterest: record product URLs and descriptions, upload one pin image each to Vercel Blob."
argument-hint: "fonts with catalogue number/slug and their product URLs"
---

# /pinterest-prepare

Delegate the task below to the **`pinterest-font-preparer`** subagent defined in `.claude/agents/pinterest-font-preparer.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not attempt the specialist's work in the main session.

Task:

```
Please run the pinterest-font-preparer agent to register these fonts into the Pinterest registry: match each to its outputs/font-preparation folder, set the product URL, decide a board suggestion (Handwritten / Display / Script / Decorative Fonts), upload one deterministic-random pin image to Vercel Blob, record it in outputs/pinterest/registry.json, and write public-urls.md in the font folder. Report one line per font. Make no Pinterest or publication claim. Fonts and URLs: $ARGUMENTS
```

After the subagent returns, report the registered fonts and any font it could not match.
