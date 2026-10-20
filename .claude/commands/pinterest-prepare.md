---
description: "Validate and upload the complete manifested Pinterest image set, record product URLs, and write all public links."
argument-hint: "fonts with catalogue number/slug and their product URLs"
---

# /pinterest-prepare

Delegate the task below to the **`pinterest-font-preparer`** subagent defined in `.claude/agents/pinterest-font-preparer.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not attempt the specialist's work in the main session.

Task:

```
Please run the pinterest-font-preparer agent to register these fonts into the Pinterest registry: match each to its outputs/font-preparation folder, record supplied product-page URLs (bin/pinterest_registry.py set-url, --market cm and --market cf), choose a board suggestion, then validate and upload the complete manifested set from visuals/New-Images/pinterest/ to Vercel Blob. The set contains every Agent-27 template pin followed by ten Agent-30 composites; use the manifest-driven count, not a fixed image count. Write all public links to public-urls.md. Report per font: board, live image count with URLs, and which product URLs are set or missing. Make no Pinterest publication claim. Fonts and URLs: $ARGUMENTS
```

After the subagent returns, report the registered fonts and any font it could not match.
