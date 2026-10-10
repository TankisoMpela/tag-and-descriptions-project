---
description: "Run the standalone post-workflow final font image processor on a seller-created visuals/New-Images folder."
argument-hint: "product facts or workspace path"
---

# /font-final-images

Delegate the task below to the **`font-final-visual-processor`** subagent defined in `.claude/agents/font-final-visual-processor.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the font-final-visual-processor agent after all font preparation and requested marketplace work are complete. Use the exact font-preparation output directory and raw visuals/New-Images folder supplied here: $ARGUMENTS. Do not use vision or determine which image is semantically a thumbnail. Run bin/process_final_font_images.py --auto-order so direct filenames are sorted independently within 3:2 and 1:1; the first in each ratio becomes thumbnail_main and the rest become promo_1 upward. Create exact source copies and <=200 KB main/square JPEG delivery files, and write final-image-manifest.md inside New-Images. Do not alter raw images, old visuals/main or visuals/squares folders, font files, or metadata; do not invoke full-workflow and make no upload claim.
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.