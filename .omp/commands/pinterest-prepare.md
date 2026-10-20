---
description: Validate and upload the complete manifested Pinterest image set, record product URLs, and write all public links.
---

Dispatch the registered FontFairy task agent `pinterest-font-preparer` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion lists registered fonts with their Blob image URLs, report them. Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the pinterest-font-preparer agent to register these fonts into the Pinterest registry: match each to its `outputs/font-preparation` folder, record supplied product-page URLs (`set-url`, `--market cm` and `--market cf`), choose a board suggestion, then validate and upload the complete manifested set from `visuals/New-Images/pinterest/` to Vercel Blob. The set contains every Agent-27 template pin followed by ten Agent-30 composites; use the manifest-driven count, not a fixed image count. Write all public links to `public-urls.md`. Report each board, uploaded image count and URLs, and which product URLs are set or missing. Do not claim that Pins were published. Fonts and URLs: $@
