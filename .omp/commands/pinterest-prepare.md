---
description: Register fonts for Pinterest — upload all four pin images to Vercel Blob, record both product-page URLs and the description.
---

Dispatch the registered FontFairy task agent `pinterest-font-preparer` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion lists registered fonts with their Blob image URLs, report them. Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the pinterest-font-preparer agent to register these fonts into the Pinterest registry: match each to its `outputs/font-preparation` folder, record both product-page URLs (`set-url`, `--market cm` and `--market cf`), decide a board suggestion (Handwritten / Display / Script / Decorative Fonts), upload all four images from `visuals/New-Images/pinterest/` to Vercel Blob, and write `public-urls.md` in the font folder. Make no Pinterest or publication claim. Fonts and URLs: $@
