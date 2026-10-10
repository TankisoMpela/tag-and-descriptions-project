---
description: "Register fonts for Pinterest: upload all four pin images to Vercel Blob, record both product-page URLs and the description."
argument-hint: "fonts with catalogue number/slug and their product URLs"
---

# /pinterest-prepare

Delegate the task below to the **`pinterest-font-preparer`** subagent defined in `.claude/agents/pinterest-font-preparer.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not attempt the specialist's work in the main session.

Task:

```
Please run the pinterest-font-preparer agent to register these fonts into the Pinterest registry: match each to its outputs/font-preparation folder, record both product-page URLs (bin/pinterest_registry.py set-url, --market cm and --market cf), decide a board suggestion (Handwritten / Display / Script / Decorative Fonts), upload all four images from visuals/New-Images/pinterest/ to Vercel Blob, record them in outputs/pinterest/registry.json, and write public-urls.md in the font folder. Report per font: board, live image count with URLs, which product URLs are set or missing. Make no Pinterest or publication claim. Fonts and URLs: $ARGUMENTS
```

After the subagent returns, report the registered fonts and any font it could not match.
